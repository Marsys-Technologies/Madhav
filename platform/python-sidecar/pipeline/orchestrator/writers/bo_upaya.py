"""
bo_upaya — Remediation Map (L2 Bodha)
======================================
Reads bodha_msr_signals + L1 chart_facts + brahma_remedy_corpus →
writes:
  - bodha_rm_resonances          (one row per graha per ayanamsha: weakness + remedy priority)
  - bodha_rm_remedy_prescriptions (1-3 prescriptions per resonance, grounded to G27 corpus)

Resonance algorithm:
  For each of the 9 grahas:
    1. Fetch L1 shadbala_normalized + bhava_bala_normalized (chart_facts)
    2. Fetch combustion/debility/dignity from chart_facts (graha_special_state_rollup)
    3. Count dosha MSR signals touching this graha → contradiction_factor
    4. Compute resonance_score_v1 (formulas.py)
    5. Rank grahas by resonance_score DESC → weakest_rank_in_chart

Prescription grounding:
  For each resonance:
    1. Query brahma_remedy_corpus WHERE planet = graha.lower()
    2. Top 3 by confidence DESC
    3. Compute resonance_match_score_v1 (formulas.py)
    4. Write bodha_rm_remedy_prescriptions row

LIGHT writer.
"""
from __future__ import annotations

import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register
from brahmagyan.graha_vocabulary import to_title
from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT

logger = logging.getLogger(__name__)

ENGINE_VERSION   = "bo_upaya_v1.0"
SNAPSHOT_TYPE    = "static_natal"
CANONICAL_AYAS   = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

KNOWN_GRAHAS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
]

# Graha → Jaimini chara-karaka role (chart-specific; placeholder)
# In practice this comes from chart_facts karaka_chara_position
CHARA_ROLE_LOOKUP: dict[str, str] = {}   # populated from chart_facts at runtime

_RESONANCE_INSERT = """
INSERT INTO bodha_rm_resonances (
  resonance_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  graha, resonance_score, resonance_score_formula_version,
  weakness_score, contradiction_factor, domain_burden, motif_burden,
  is_yoga_karaka_flag, is_chara_karaka_role,
  weakest_rank_in_chart, remedy_priority_class,
  associated_doshas_array, associated_motifs_array, associated_cdlm_cells_array,
  ephemeris_audit_jsonb, verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(resonance_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(graha)s, %(resonance_score)s, %(resonance_score_formula_version)s,
  %(weakness_score)s, %(contradiction_factor)s, %(domain_burden)s, %(motif_burden)s,
  %(is_yoga_karaka_flag)s, %(is_chara_karaka_role)s,
  %(weakest_rank_in_chart)s, %(remedy_priority_class)s,
  %(associated_doshas_array)s, NULL, %(associated_cdlm_cells_array)s,
  %(ephemeris_audit_jsonb)s::jsonb, %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
"""

_PRESCRIPTION_INSERT = """
INSERT INTO bodha_rm_remedy_prescriptions (
  prescription_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  target_graha, target_resonance_id,
  tradition, sub_tradition,
  remedy_category, remedy_id_g27, remedy_label_human,
  prescription_detail_jsonb,
  classical_strength_rating, classical_sources_jsonb, classical_source_text_jsonb,
  targets_motif_id, targets_cell_id, targets_dosha_class,
  resonance_match_score, match_score_formula_version,
  counter_indications_array, incompatible_with_prescription_ids_array, prerequisite_prescription_ids_array,
  feasibility_score, estimated_cost_inr_range_jsonb, estimated_time_minutes_daily, ritual_complexity_class,
  requires_acharya_review_flag, acharya_review_reason_array,
  cross_tradition_corroboration_count, cross_tradition_corroborating_traditions_array,
  phase_sequence_class, phase_duration_days, count_prescription_jsonb,
  substitute_options_jsonb, yantra_geometry_jsonb, pranapratishtha_required_flag,
  pilgrimage_site_jsonb, pilgrimage_priority_rank,
  recommended_hora_lord_array, recommended_choghadiya_window_array,
  initiation_lunar_phase_recommendation_array, recommended_facing_direction,
  outcome_tracking_placeholder_jsonb, prescription_embedding_vec,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(prescription_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(target_graha)s, %(target_resonance_id)s,
  %(tradition)s, NULL,
  %(remedy_category)s, %(remedy_id_g27)s, %(remedy_label_human)s,
  %(prescription_detail_jsonb)s::jsonb,
  %(classical_strength_rating)s, %(classical_sources_jsonb)s::jsonb, NULL,
  NULL, NULL, %(targets_dosha_class)s,
  %(resonance_match_score)s, %(match_score_formula_version)s,
  %(counter_indications_array)s, NULL, NULL,
  %(feasibility_score)s, %(estimated_cost_inr_range_jsonb)s::jsonb, NULL, %(ritual_complexity_class)s,
  %(requires_acharya_review_flag)s, NULL,
  %(cross_tradition_corroboration_count)s, NULL,
  NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
  NULL, NULL, NULL, NULL, NULL, NULL,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
ON CONFLICT DO NOTHING
"""

# ── B-4 (BRIEF_D4B §1): bodha_rm_dasha_windowed_prescriptions ───────────────
# A13 Table 3 — designed 2026 in migration 226 but never populated (writer
# comment: "needs L3 dasha-window data unavailable at static-natal L2").
# B-4 populates it directly from L1 chart_dashas (no L3 dependency needed for
# a Mahadasha-level window) — the schedulable remedy-program surface.

_WINDOWED_INSERT = """
INSERT INTO bodha_rm_dasha_windowed_prescriptions (
  window_prescription_id, chart_id, ayanamsha_id, build_id, base_prescription_id,
  dasha_system, dasha_level, dasha_lord, window_start_iso, window_end_iso,
  window_intensity_multiplier, schedule_jsonb, phase_within_window,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(window_prescription_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(base_prescription_id)s,
  %(dasha_system)s, %(dasha_level)s, %(dasha_lord)s, %(window_start_iso)s, %(window_end_iso)s,
  %(window_intensity_multiplier)s, %(schedule_jsonb)s::jsonb, %(phase_within_window)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
"""

_BATCH_SIZE = 50

# ── WP-2.2 / LCA-5: RM sibling rollup tables (previously empty shells) ──────────
_RM_SUMMARY_INSERT = """
INSERT INTO bodha_rm_chart_summary (
  summary_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  top_3_resonance_targets_jsonb, top_10_priority_prescriptions_jsonb,
  recommended_intensity_class, total_active_dosha_count, primary_dosha_class,
  cross_tradition_convergence_jsonb, remedy_chart_typology,
  acharya_review_required_count, feasibility_assessment_jsonb,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(summary_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(top_3_resonance_targets_jsonb)s::jsonb, %(top_10_priority_prescriptions_jsonb)s::jsonb,
  %(recommended_intensity_class)s, %(total_active_dosha_count)s, %(primary_dosha_class)s,
  %(cross_tradition_convergence_jsonb)s::jsonb, %(remedy_chart_typology)s,
  %(acharya_review_required_count)s, %(feasibility_assessment_jsonb)s::jsonb,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
"""

_RM_BUNDLE_INSERT = """
INSERT INTO bodha_rm_dosha_remedy_bundles (
  bundle_id, chart_id, ayanamsha_id, build_id, dosha_class, active_flag,
  intensity_score, cancellation_count, prescription_ids_in_bundle_array,
  bundle_summary_jsonb, classical_sources_jsonb,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(bundle_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(dosha_class)s, %(active_flag)s,
  %(intensity_score)s, %(cancellation_count)s, %(prescription_ids_in_bundle_array)s,
  %(bundle_summary_jsonb)s::jsonb, %(classical_sources_jsonb)s::jsonb,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
ON CONFLICT (chart_id, ayanamsha_id, build_id, dosha_class) DO NOTHING
"""

_RM_PATTERN_INSERT = """
INSERT INTO bodha_rm_pattern_remedies (
  pattern_remedy_id, chart_id, ayanamsha_id, build_id,
  source_kind, source_id, remedy_theme, prescription_ids_array,
  theme_strength, cross_tradition_unanimity_score,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(pattern_remedy_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
  %(source_kind)s, %(source_id)s, %(remedy_theme)s, %(prescription_ids_array)s,
  %(theme_strength)s, %(cross_tradition_unanimity_score)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
"""


# ── L1 data fetchers ───────────────────────────────────────────────────────────

# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2. Kept as a local dict so `.get()` preserves None-on-miss.
_SUBJECT_TO_PLANET: dict[str, str] = {
    code: to_title(code)
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
}


def _fetch_shadbala(conn: Any, chart_id: str, aya: str) -> dict[str, float]:
    """graha → normalized shadbala strength (achieved/required ratio, CR-18).

    fact_subject holds the planet code (SUN/MOON/MAR/…); fact_key = 'ratio' is
    the L1-authoritative achieved/required shadbala ratio (ga_strength_writer,
    CR-18), already dividing each graha's OWN classical Parashara minimum
    (SHADBALA_REQUIRED: Sun/Mars/Saturn=5.0, Moon=6.0, Mercury=7.0, Jupiter=6.5,
    Venus=5.5 rupas) — read here, never recomputed (§N.5). Rahu/Ketu carry no
    classical shadbala requirement (ga_strength_writer's classical_grahas list
    excludes them) and so have no 'ratio' row; the caller falls back honestly.

    PRIOR BUG (MC-025a root cause): this fetcher divided the raw 'rupa' total
    by a flat 390.0 constant for EVERY graha. Real chart_facts 'rupa' totals
    are on the classical scale of ~0.4-8.5 rupas (NOT the ~390-virupa scale
    390 implies), so val/390 collapsed every graha to ~0.001-0.02, making
    (1 - shadbala_normalized) an effective CONSTANT ~0.98-1.0 across all 9
    grahas. That term alone carries 30% of resonance_score_v1's weakness_score
    weight — the single largest component — so this one bug was the dominant
    contributor to the observed flat 0.49-0.53 resonance band chart-wide.
    Verified by hand against chart 482012f1/lahiri_chitrapaksha: real ratios
    range 0.844 (Venus) to 1.694 (Sun), vs. the old val/390 output of
    ~0.012-0.022 for the same grahas.
    """
    rows = conn.execute(
        """SELECT fact_subject, fact_value_num FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'graha_shadbala_total'
             AND fact_key = 'ratio'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, float] = {}
    for r in rows:
        subject = str(r[0] if isinstance(r, tuple) else r.get("fact_subject", ""))
        planet  = _SUBJECT_TO_PLANET.get(subject)
        if planet is None:
            continue
        val = r[1] if isinstance(r, tuple) else r.get("fact_value_num")
        if val is None:
            continue
        out[planet] = max(0.0, float(val))
    return out


def _weakest_graha_by_shadbala(shadbala: dict[str, float]) -> str | None:
    """§N.5 single-authority weakest graha (MC-025b reconciliation).

    The ONE authoritative "weakest graha" is the graha with the MINIMUM L1
    graha_shadbala_total (rupa) — read straight from L1, never recomputed from a
    composite. bo_upaya's `weakest_rank_in_chart` is a COMPOSITE remedy-priority
    rank (resonance_score DESC: shadbala + bhava_bala + dispositor + cdlm + cgm +
    dasha), a DIFFERENT question, and must not be conflated with this shadbala
    minimum. Before this fix bo_upaya's rank-1 (Mercury, composite) and
    bodha_chart_digest (Venus, shadbala) disagreed on "the single most
    remedy-relevant fact". Both must now read THIS function's answer for the
    shadbala-weakest designation. For chart 482012f1 → Venus (VEN, 4.64 rupa).

    NB: `shadbala` here is the normalized dict from `_fetch_shadbala` (total/390);
    the argmin is invariant under that monotonic normalization, so the minimum
    graha is identical to the minimum of the raw rupa totals.
    """
    if not shadbala:
        return None
    return min(shadbala.items(), key=lambda kv: kv[1])[0]


def _fetch_bhava_bala(conn: Any, chart_id: str, aya: str) -> dict[int, float]:
    """house → normalized bhava bala strength (achieved/required ratio).

    fact_subject = 'HOUSE_1' … 'HOUSE_12'; fact_category = 'house_bhava_bala_ratio',
    fact_key = 'strength_ratio' is the L1-precomputed strength ratio
    (ga_strength_writer._build_bhava_bala_rows) — read here, never recomputed.

    PRIOR BUG (MC-025a contributor): read fact_category='house_bhava_bala_total'
    / fact_key='total' (the raw rupa total) and divided by a flat 300.0. Real
    house totals for this chart run ~5.3-9.0 rupas, so val/300 collapsed every
    house to ~0.018-0.03 — again an effective CONSTANT (1 - bh_norm) ~0.97-0.98,
    contributing another 15%-weight flat term. Fixed by reading the
    already-computed L1 strength_ratio directly (§N.5), matching the same
    achieved/required-ratio pattern CR-18 established for shadbala.
    """
    rows = conn.execute(
        """SELECT fact_subject, fact_value_num FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'house_bhava_bala_ratio'
             AND fact_key = 'strength_ratio'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[int, float] = {}
    for r in rows:
        subject = str(r[0] if isinstance(r, tuple) else r.get("fact_subject", ""))
        try:
            house = int(subject.replace("HOUSE_", ""))
        except (ValueError, AttributeError):
            continue
        val = r[1] if isinstance(r, tuple) else r.get("fact_value_num")
        if val is None:
            continue
        out[house] = max(0.0, float(val))
    return out


# fact_key → special-state label, for the graha_special_state_rollup rows
# (one boolean flag per row: fact_value_text ∈ {'true','false'}).
_SPECIAL_STATE_LABELS: dict[str, str] = {
    "is_combust": "combust",
    "is_retrograde": "retrograde",
    "is_vargottama": "vargottama",
    "is_debilitated": "debilitated",
    "is_exalted": "exalted",
}


def _fetch_special_states(conn: Any, chart_id: str, aya: str) -> dict[str, set[str]]:
    """graha → set of TRUE special-state labels (combust/debilitated/exalted/
    retrograde/vargottama) from graha_special_state_rollup.

    A graha present in the returned dict (even with an empty set) means the
    rollup HAS data for it (all-false is a real, known-neutral state); a
    graha absent means no rollup row exists at all (genuinely unknown).

    PRIOR BUG (MC-025a contributor): selected only fact_key (never
    fact_subject) and derived "graha" via key.split(':')[0] — but the real
    schema stores the graha in fact_subject and plain keys like 'is_combust'/
    'is_debilitated'/'is_exalted' (fact_value_text='true'/'false'), not a
    colon-prefixed compound key. Every row's derived "graha" was therefore
    the literal fact_key string itself, so this function's output never had
    a real graha as a key: special_states.get(graha, set()) always hit the
    empty-set default. That zeroed combustion_score for every graha AND made
    debility_score's "graha not in special_states" branch permanently true
    (debility=0.0 chart-wide, regardless of actual debility/exaltation) —
    e.g. Saturn's real is_exalted=true was never read.
    """
    rows = conn.execute(
        """SELECT fact_subject, fact_key, fact_value_text FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'graha_special_state_rollup'
             AND fact_key = ANY(%s)""",
        [chart_id, aya, list(_SPECIAL_STATE_LABELS.keys())],
    ).fetchall()
    out: dict[str, set[str]] = {}
    for r in rows:
        subject = str(r[0] if isinstance(r, tuple) else r.get("fact_subject", ""))
        key     = str(r[1] if isinstance(r, tuple) else r.get("fact_key", ""))
        val     = str(r[2] if isinstance(r, tuple) else r.get("fact_value_text") or "").strip().lower()
        planet  = _SUBJECT_TO_PLANET.get(subject)
        if planet is None:
            continue
        out.setdefault(planet, set())  # a row exists -> this graha is "known"
        if val == "true":
            label = _SPECIAL_STATE_LABELS.get(key)
            if label:
                out[planet].add(label)
    return out


def _fetch_graha_house_placements(conn: Any, chart_id: str, aya: str) -> dict[str, int]:
    """graha → bhava number (D1 placement).

    fact_subject holds the planet code; fact_category='graha_position',
    fact_key='house_d1' is the plain D1 house-placement fact.

    PRIOR BUG (MC-025a contributor): queried
    fact_key LIKE '%:D1%:bhava%' and derived the graha via
    key.split(':')[0] — but the real schema's graha_position fact_key is the
    plain string 'house_d1' (no compound GRAHA:D1:bhava key exists, and the
    graha lives in fact_subject, never selected). The LIKE filter matched
    ZERO rows chart-wide, so every graha silently fell back to house=1 in the
    caller — meaning all nine grahas read the SAME house's bhava_bala value,
    collapsing 15% of resonance_score_v1's weakness weight to one identical
    constant across the whole chart (compounding the _fetch_bhava_bala bug
    above).
    """
    rows = conn.execute(
        """SELECT fact_subject, fact_value_num FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_position'
             AND fact_key = 'house_d1'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, int] = {}
    for r in rows:
        subject = str(r[0] if isinstance(r, tuple) else r.get("fact_subject", ""))
        planet  = _SUBJECT_TO_PLANET.get(subject)
        if planet is None:
            continue
        try:
            val = int(r[1] if isinstance(r, tuple) else r.get("fact_value_num") or 1)
            out[planet] = val
        except (TypeError, ValueError):
            pass
    return out


def _fetch_yoga_karaka_flags(conn: Any, chart_id: str, aya: str) -> set[str]:
    """Returns set of grahas that are yoga-karakas."""
    rows = conn.execute(
        """SELECT fact_key FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'graha_yoga_karaka_flag'
             AND fact_value_text IN ('true', '1', 'yes', 'yoga_karaka')""",
        [chart_id, aya],
    ).fetchall()
    result: set[str] = set()
    for r in rows:
        key = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        graha = key.split(":")[0]
        if graha in KNOWN_GRAHAS:
            result.add(graha)
    return result


def _fetch_chara_roles(conn: Any, chart_id: str, aya: str) -> dict[str, str]:
    """graha → chara karaka role (AK/AmK/BK/etc.)."""
    rows = conn.execute(
        """SELECT fact_key, fact_value_text FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'karaka_chara_position'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, str] = {}
    for r in rows:
        key = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        val = str(r[1] if isinstance(r, tuple) else r.get("fact_value_text") or "")
        graha = key.split(":")[0]
        if graha in KNOWN_GRAHAS and val:
            out[graha] = val
    return out


def _fetch_dispositor_terminal_strength(conn: Any, chart_id: str, aya: str) -> dict[str, float]:
    """graha → dispositor-chain terminal strength (0..1; 1.0 = chain terminates in
    an exalted sign-lord, 0.25 = terminates in a debilitated one).

    BA-P2.5 #4: real L1 fact (§N.5 — L1 is the authority over L2+ derivations).
    Written by ga_structural_writer.py (fact_category='composite_dispositor_strength',
    fact_key='terminal_strength'); NEVER recomputed here — only referenced.
    dispositor_chain_weakness = 1.0 - terminal_strength (weak terminal dispositor
    means the graha's authority chain bottoms out in a weak sign-lord).
    """
    rows = conn.execute(
        """SELECT fact_subject, fact_value_num FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'composite_dispositor_strength'
             AND fact_key = 'terminal_strength'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, float] = {}
    for r in rows:
        subject = str(r[0] if isinstance(r, tuple) else r.get("fact_subject", ""))
        planet  = _SUBJECT_TO_PLANET.get(subject)
        if planet is None:
            continue
        val = float(r[1] if isinstance(r, tuple) else r.get("fact_value_num") or 0.5)
        out[planet] = max(0.0, min(val, 1.0))
    return out


def _fetch_dasha_proximity(conn: Any, chart_id: str, aya: str, at_dt: datetime) -> dict[str, float]:
    """graha → dasha-timing proximity/activation score (0..1) as of ``at_dt``.

    BA-P2.5 #4: real GA7 chart_dashas data (written by ga_dashas), not a fabricated
    number. Reuses the same "which lord covers this instant" lookup pattern as
    ga_sade_sati_writer.py's _lookup_dasha_lord_at() — a covering-interval query on
    chart_dashas.start_iso/end_iso for the vimshottari system.

    Scoring (mirrors this file's own 3-tier debility_score precedent):
      - graha is BOTH the current mahadasha (level_n=1) AND antardasha (level_n=2)
        lord  -> 1.0  (its own dasha-within-its-own-dasha: maximal classical activation)
      - graha is the current mahadasha OR antardasha lord (not both) -> 0.6
      - graha holds neither running period                            -> 0.0
    """
    rows = conn.execute(
        """SELECT level_n, lord_graha FROM chart_dashas
           WHERE chart_id = %s AND ayanamsha_id = %s AND system_id = 'vimshottari'
             AND level_n IN (1, 2) AND start_iso <= %s AND end_iso > %s""",
        [chart_id, aya, at_dt, at_dt],
    ).fetchall()
    active_by_level: dict[int, str] = {}
    for r in rows:
        level = int(r[0] if isinstance(r, tuple) else r.get("level_n"))
        lord  = str(r[1] if isinstance(r, tuple) else r.get("lord_graha") or "")
        active_by_level[level] = lord

    md_lord = active_by_level.get(1)
    ad_lord = active_by_level.get(2)

    out: dict[str, float] = {}
    for graha in KNOWN_GRAHAS:
        is_md = graha == md_lord
        is_ad = graha == ad_lord
        if is_md and is_ad:
            out[graha] = 1.0
        elif is_md or is_ad:
            out[graha] = 0.6
        else:
            out[graha] = 0.0
    return out


def _fetch_cgm_motif_weakness(conn: Any, chart_id: str, aya: str) -> dict[str, float]:
    """graha → weakness burden (0..1) contributed by CGM structural motifs it
    participates in (mutual_reception / stellium / parivartana_chain).

    BA-P2.5 #4: real value from bodha_cgm_motifs.motif_strength (written by
    bo_cgm_motifs), joined to bodha_cgm_nodes.node_subject to resolve graha
    identity. Uses MIN(motif_strength) across a graha's motifs (a chain/pattern
    is only as strong as its weakest constituent — same product/min-over-parts
    philosophy already established for bo_cgm_paths.path_strength, JL-013).
    weakness = 1.0 - min(motif_strength); grahas with no motif membership get
    0.0 (honest "no burden observed", not a fabricated value).

    NOTE: bo_cgm_motifs' stellium/parivartana_chain detectors are Tier-3-blocked
    on missing bo_karanajala dispositor edges (see bo_cgm_motifs.py); only
    mutual_reception motifs reliably populate today. That is a bo_cgm_motifs-side
    gap, not something this reader should paper over.
    """
    rows = conn.execute(
        """SELECT n.node_subject, MIN(m.motif_strength) AS weakest_strength
           FROM bodha_cgm_motifs m
           JOIN bodha_cgm_nodes n
             ON n.node_id = ANY(m.involved_node_ids_array)
            AND n.chart_id = m.chart_id AND n.ayanamsha_id = m.ayanamsha_id
           WHERE m.chart_id = %s AND m.ayanamsha_id = %s
           GROUP BY n.node_subject""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, float] = {}
    for r in rows:
        # bo_bimba writes node_subject as the title-case graha name directly
        # (e.g. "Sun", "Mars") — already KNOWN_GRAHAS-shaped, no code translation.
        subject = str(r[0] if isinstance(r, tuple) else r.get("node_subject", ""))
        if subject not in KNOWN_GRAHAS:
            continue
        strength = r[1] if isinstance(r, tuple) else r.get("weakest_strength")
        if strength is None:
            continue
        out[subject] = max(0.0, min(1.0 - float(strength), 1.0))
    return out


# ── CR-67 (SARVA-SIDDHI W-3): resonance → CDLM cell join ────────────────────
# bodha_rm_resonances.associated_cdlm_cells_array was 100% NULL DB-wide across
# every built chart: the writer had no code path that populated it. This is the
# missing L2 derivation that joins each graha's remedy resonance to the CDLM
# cross-domain-linkage cells the graha is a load-bearing constituent of.
#
# GROUNDING (§N.5 — L1 is the authority; no fabricated cell assignments):
#   1. Each MSR signal resolves to its graha(s) via its constituent_facts_array
#      → chart_facts.fact_subject (the canonical L1 fact ids the signal already
#      cites). fact_subject ∈ {SUN,MOON,MAR,MER,JUP,VEN,SAT,RAH_MEAN,KET_MEAN}
#      maps to the KNOWN_GRAHAS name. A signal may resolve to >1 graha (e.g. an
#      aspect Mars→Saturn), in which case it contributes to each.
#   2. A CDLM cell (bo_sangati) bridges two life domains via its
#      shared_signal_ids_array. For each cell, sum computed_salience of the
#      shared signals resolving to each graha.
#   3. A graha is a MATERIAL CONSTITUENT of a cell iff its salience-share of the
#      cell is ≥ the equal-share baseline (cell_salience ÷ number-of-distinct-
#      grahas-present-in-cell) — i.e. an above-average bridging contributor.
#      This deterministic threshold distinguishes load-bearing bridging grahas
#      from incidental single-signal touches (without it, the dense shared-signal
#      sets would associate ~every graha with ~every cell — true but useless).
#   associated_cdlm_cells_array[graha] = cell_ids where graha is material.
#
# The whole join runs as one SQL per (chart, ayanamsha) — the array-membership
# and salience aggregation are far cheaper server-side than materialising ~10k
# signals into Python.

def _fetch_graha_cdlm_cells(conn: Any, chart_id: str, aya: str) -> dict[str, list[str]]:
    """graha → list of CDLM cell_id (uuid str) the graha is a material
    constituent of. See the CR-67 block comment above for the derivation."""
    rows = conn.execute(
        """
        WITH sig_graha AS (
          SELECT s.signal_id, s.computed_salience,
            CASE cf.fact_subject
              WHEN 'SUN' THEN 'Sun'  WHEN 'MOON' THEN 'Moon' WHEN 'MAR' THEN 'Mars'
              WHEN 'MER' THEN 'Mercury' WHEN 'JUP' THEN 'Jupiter' WHEN 'VEN' THEN 'Venus'
              WHEN 'SAT' THEN 'Saturn' WHEN 'RAH_MEAN' THEN 'Rahu' WHEN 'KET_MEAN' THEN 'Ketu'
            END AS graha
          FROM bodha_msr_signals s
          JOIN LATERAL (
            SELECT DISTINCT cf.fact_subject FROM chart_facts cf
            WHERE cf.fact_id = ANY(s.constituent_facts_array)
              AND cf.fact_subject IN
                ('SUN','MOON','MAR','MER','JUP','VEN','SAT','RAH_MEAN','KET_MEAN')
          ) cf ON TRUE
          WHERE s.chart_id = %(chart_id)s AND s.ayanamsha_id = %(aya)s
        ),
        cell_sig AS (
          SELECT c.cell_id, sg.graha, sg.computed_salience
          FROM bodha_cdlm_cells c
          JOIN sig_graha sg ON sg.signal_id = ANY(c.shared_signal_ids_array)
          WHERE c.chart_id = %(chart_id)s AND c.ayanamsha_id = %(aya)s
        ),
        per AS (
          SELECT cell_id, graha,
                 SUM(computed_salience) AS graha_sal,
                 SUM(SUM(computed_salience)) OVER (PARTITION BY cell_id) AS cell_sal,
                 COUNT(*) OVER (PARTITION BY cell_id) AS n_graha
          FROM cell_sig
          GROUP BY cell_id, graha
        )
        SELECT graha, cell_id::text AS cell_id
        FROM per
        WHERE n_graha > 0 AND graha_sal >= cell_sal / n_graha
        """,
        {"chart_id": chart_id, "aya": aya},
    ).fetchall()
    out: dict[str, list[str]] = {}
    for r in rows:
        graha = str(r[0] if isinstance(r, tuple) else r.get("graha") or "")
        cell  = str(r[1] if isinstance(r, tuple) else r.get("cell_id") or "")
        if graha and cell:
            out.setdefault(graha, []).append(cell)
    return out


def _fetch_chart_typology(conn: Any, chart_id: str, aya: str) -> str:
    """
    Derive chart typology from element distribution of graha sign placements.
    Queries chart_facts for graha_sign_attributes element facts and returns
    the dominant element mapped to a typology label.

    Maps:
      Fire dominant   → "pitta"
      Earth dominant  → "kapha_stable"
      Air dominant    → "vata"
      Water dominant  → "kapha_fluid"
      No clear majority (tie) → "balanced"
    """
    rows = conn.execute(
        """SELECT fact_value_text, COUNT(*) AS cnt
           FROM chart_facts
           WHERE chart_id = %s
             AND ayanamsha_id = %s
             AND fact_category = 'graha_sign_attributes'
             AND fact_key = 'element'
           GROUP BY fact_value_text
           ORDER BY cnt DESC""",
        [chart_id, aya],
    ).fetchall()

    if not rows:
        return "balanced"

    counts: dict[str, int] = {}
    for r in rows:
        elem = str(r[0] if isinstance(r, tuple) else r.get("fact_value_text") or "")
        cnt  = int(r[1] if isinstance(r, tuple) else r.get("cnt") or 0)
        if elem:
            counts[elem] = cnt

    if not counts:
        return "balanced"

    max_cnt = max(counts.values())
    # Tie check: more than one element shares the maximum count → balanced
    leaders = [e for e, c in counts.items() if c == max_cnt]
    if len(leaders) != 1:
        return "balanced"

    dominant = leaders[0].lower()
    _ELEMENT_MAP: dict[str, str] = {
        "fire": "pitta",
        "earth": "kapha_stable",
        "air": "vata",
        "water": "kapha_fluid",
    }
    return _ELEMENT_MAP.get(dominant, "balanced")


def _fetch_msr_dosha_sigs_by_graha(conn: Any, chart_id: str, aya: str) -> dict[str, list[str]]:
    """graha → list of dosha signal_type_ids (from MSR signals of class dosha)."""
    rows = conn.execute(
        """SELECT configuration_jsonb, signal_type_id, computed_salience
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s AND signal_type_class = 'dosha'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, list[str]] = {}
    for r in rows:
        cfg_raw = r[0] if isinstance(r, tuple) else r.get("configuration_jsonb") or {}
        type_id = str(r[1] if isinstance(r, tuple) else r.get("signal_type_id") or "")
        if isinstance(cfg_raw, str):
            try:
                cfg = json.loads(cfg_raw)
            except Exception:
                cfg = {}
        else:
            cfg = cfg_raw if isinstance(cfg_raw, dict) else {}
        graha = (cfg.get("graha") or cfg.get("primary_graha") or cfg.get("lord") or "").split(":")[0]
        if graha in KNOWN_GRAHAS:
            if graha not in out:
                out[graha] = []
            if type_id and type_id not in out[graha]:
                out[graha].append(type_id)
    return out


# ── β.G / EL-51 — maraka-lordship gemstone contraindication verdict ────────────
# Grounded in BPHS Chapter 44 "Maraka (Killer) Planets" (corpus chunks bphs_pg0439_c01
# through bphs_pg0443_c01, [HIGH] confidence, Trans. R. Santhanam, Ranjan Publications —
# verified live via ref_rules_search(keyword="maraka") 2026-07-25) and corroborated by
# BPHS Ch.47 (corpus row sweep_venus_japa_1b8a46b9, PG581 — the exact passage EL-52 names
# as its OCR-garbled example, cleaned separately in this same lane's pass): "the 2nd and
# 7th [houses from lagna] are Maraka houses... The lords of the 2nd and the 7th ... are
# known as Marakas." v1 scope: the unambiguous 2nd/7th-lordship rule only (BPHS's fuller
# rule additionally covers malefic occupants of/conjunct-with 2nd/7th and Rahu/Ketu — not
# implemented here; disclosed as a named follow-up in BETA_G.md, not silently generalized).
MARAKA_CITATION = (
    "BPHS Ch.44 \"Maraka (Killer) Planets\" (2-5, 3): \"the 2nd and 7th are Maraka houses... "
    "The lords of the 2nd and the 7th ... are known as Marakas.\" Trans. R. Santhanam, "
    "Ranjan Publications. Corroborated by BPHS Ch.47 (Venus sub-periods): \"If Venus be lord "
    "of the 2nd or the 7th (two maraka houses) there will be during his Dasa, physical pains "
    "and troubles.\""
)


def _fetch_maraka_facts(conn: Any, chart_id: str, aya: str) -> dict[str, Any] | None:
    """L1 maraka significators — READ from chart_facts, never recomputed (§N.5).
    Written by ga_ayurdaya_writer.py (fact_category='ayurdaya', fact_subject='CHART',
    fact_key='maraka_grahas'): second_lord, seventh_lord, occupants_2_7, natural_maraka,
    maraka_grahas. This IS the L1-authoritative source for the 2nd/7th-lordship rule —
    bo_upaya references it, never restates the lordship computation itself."""
    rows = conn.execute(
        """SELECT fact_value_jsonb, fact_id
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'ayurdaya' AND fact_subject = 'CHART'
             AND fact_key = 'maraka_grahas'""",
        [chart_id, aya],
    ).fetchall()
    if not rows:
        return None
    r0 = rows[0]
    val = r0[0] if isinstance(r0, (tuple, list)) else r0.get("fact_value_jsonb")
    fact_id = r0[1] if isinstance(r0, (tuple, list)) else r0.get("fact_id")
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except Exception:
            val = {}
    val = dict(val or {})
    val["_source_fact_id"] = fact_id
    return val


def _compute_gemstone_maraka_verdict(graha: str, maraka_facts: dict[str, Any] | None) -> dict[str, Any]:
    """Deterministic per-gemstone maraka-contraindication verdict for `graha`.

    Rule (v1, see MARAKA_CITATION): a graha is contraindicated for gemstone-wearing on
    maraka-lordship grounds if it is the 2nd-house lord or the 7th-house lord from lagna
    (BPHS Ch.44's core, unambiguous rule). Never fabricated — if the L1 maraka fact is
    absent for this chart/ayanamsha, the verdict is explicitly `unavailable`, not a
    silent False."""
    if not maraka_facts:
        return {
            "verdict": "unavailable",
            "is_maraka_lord": None,
            "reason": "L1 ayurdaya.maraka_grahas fact not found for this chart/ayanamsha — "
                      "cannot compute a maraka verdict without it (never guessed).",
            "citation": MARAKA_CITATION,
            "rule_scope": "v1: 2nd/7th house lordship only (occupancy + Rahu/Ketu extensions "
                          "not yet implemented — see BETA_G.md follow-up)",
        }
    second_lord = maraka_facts.get("second_lord")
    seventh_lord = maraka_facts.get("seventh_lord")
    is_second = graha == second_lord
    is_seventh = graha == seventh_lord
    is_maraka_lord = bool(is_second or is_seventh)
    if is_second and is_seventh:
        which = "both the 2nd and 7th houses (maximal maraka lordship)"
    elif is_second:
        which = "the 2nd house (BPHS: \"the 2nd is a powerful Maraka house\")"
    elif is_seventh:
        which = "the 7th house"
    else:
        which = None
    reason = (
        f"{graha} rules {which} from lagna — a maraka lord. Per BPHS Ch.44/47, wearing "
        f"{graha}'s gemstone is classically contraindicated for this chart unless a "
        f"qualified acharya review finds a redeeming yoga; gemstones strengthen the planet "
        f"they represent, and strengthening a maraka is the opposite of the intended effect."
        if is_maraka_lord else
        f"{graha} is neither the 2nd-house lord ({second_lord}) nor the 7th-house lord "
        f"({seventh_lord}) from lagna in this chart — no maraka-lordship contraindication "
        f"under the v1 rule."
    )
    return {
        "verdict": "contraindicated" if is_maraka_lord else "no_contraindication_found",
        "is_maraka_lord": is_maraka_lord,
        "second_lord": second_lord,
        "seventh_lord": seventh_lord,
        "reason": reason,
        "citation": MARAKA_CITATION,
        "rule_scope": "v1: 2nd/7th house lordship only (occupancy + Rahu/Ketu extensions "
                      "not yet implemented — see BETA_G.md follow-up)",
        "source_fact_id": maraka_facts.get("_source_fact_id"),
    }


# ── β.G / EL-51 — associated_doshas_array backfill (chart-wide 100% NULL, live-confirmed) ──
# The existing MSR path (_fetch_msr_dosha_sigs_by_graha above) is wired but structurally dead:
# bodha_msr_signals.configuration_jsonb for signal_type_class='dosha' rows never carries a
# graha/primary_graha/lord key (confirmed live, 2026-07-25) — every lookup returns empty.
# This fetcher backfills via a traceable path instead: L1 chart_facts dosha_label rows
# (fires=true only — never a catalog-only/unevaluated formation-shape match) carry a
# constituent_facts_array of the OTHER chart_facts rows the dosha computation consumed;
# if one of those constituent facts' fact_subject IS a graha name, that association is
# real and traced back to a specific fact_id — never inferred from the dosha's name/label.
def _fetch_active_doshas_by_graha(conn: Any, chart_id: str, aya: str) -> dict[str, list[str]]:
    rows = conn.execute(
        """SELECT fact_subject, fact_value_text, fact_value_jsonb
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'dosha_label'
             AND fact_value_jsonb->>'fires' = 'true'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, list[str]] = {}
    for r in rows:
        dosha_id = r[0] if isinstance(r, (tuple, list)) else r.get("fact_subject")
        dosha_name = r[1] if isinstance(r, (tuple, list)) else r.get("fact_value_text")
        val = r[2] if isinstance(r, (tuple, list)) else r.get("fact_value_jsonb")
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except Exception:
                val = {}
        val = val or {}
        constituent_ids = val.get("constituent_facts_array") or []
        if not constituent_ids:
            continue
        placeholders = ",".join(["%s"] * len(constituent_ids))
        crows = conn.execute(
            f"""SELECT DISTINCT fact_subject FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s AND fact_id IN ({placeholders})""",
            [chart_id, aya, *constituent_ids],
        ).fetchall()
        for cr in crows:
            subj_raw = str((cr[0] if isinstance(cr, (tuple, list)) else cr.get("fact_subject")) or "")
            graha = to_title(subj_raw)
            if graha in KNOWN_GRAHAS:
                label = dosha_name or dosha_id
                out.setdefault(graha, [])
                if label not in out[graha]:
                    out[graha].append(label)
    return out


def _fetch_leverage_weights(conn: Any) -> dict[str, Any]:
    """brahma_vichara_constants.leverage_weights — the SAME registry ga_vichara
    reads (design §11: "registry data, not literals"). Read here so B-4's
    fresh dasha-runway re-derivation (below) uses the identical runway_base/
    scale/duration_norm/start_horizon/lookforward curve, not new invented
    constants."""
    rows = conn.execute(
        "SELECT value_jsonb FROM brahma_vichara_constants WHERE constant_key = %s",
        ["leverage_weights"],
    ).fetchall()
    if not rows:
        return {}
    r0 = rows[0]
    val = r0[0] if isinstance(r0, (tuple, list)) else r0.get("value_jsonb")
    if isinstance(val, str):
        val = json.loads(val)
    return val or {}


def _fetch_wealth_leverage_index(conn: Any, chart_id: str, aya: str) -> list[dict]:
    """L1 ga_vichara leverage_index, domain='wealth' — READ from chart_vichara,
    never recomputed (§N.5). Ranked DESC: highest leverage_index = the graha
    most structurally on the hook for wealth (lordship/karakatva/occupancy/
    yoga participation) relative to its own capability — i.e. the "weakest
    load-bearing graha" BRIEF_D4B §1 B-4 names."""
    rows = conn.execute(
        """SELECT id AS vichara_row_id, subject, value_num, constituent_fact_ids
           FROM chart_vichara
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND vichara_family = 'leverage_index' AND domain = 'wealth'
             AND value_num IS NOT NULL AND value_num > 0
           ORDER BY value_num DESC""",
        [chart_id, aya],
    ).fetchall()
    keys = ["vichara_row_id", "subject", "value_num", "constituent_fact_ids"]
    return [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]


# LEL sealed test split (ESCALATION_POLICY_v1_0.md §4): gate-runner/anti-gaming
# territory ONLY may read events on/after this date. This literal must never be
# parameterized or widened by a caller.
_SADHANA_EMBARGO_DATE = "2020-01-01"


def _fetch_sadhana_milestones(conn: Any, chart_id: str) -> list[dict]:
    """LEL sadhana / spiritual-arc milestones strictly BEFORE the sealed test
    split. Read-only against life_events (calibration corpus; append-only,
    never written here — §3 must_not_touch: raw LEL event data). Not
    ayanamsha-scoped (life events are sidereal-system-independent)."""
    rows = conn.execute(
        """SELECT event_id, event_date, domain, source_citation
           FROM life_events
           WHERE chart_id = %s AND event_type = 'spiritual'
             AND event_date < %s::date
           ORDER BY event_date""",
        [chart_id, _SADHANA_EMBARGO_DATE],
    ).fetchall()
    keys = ["event_id", "event_date", "domain", "source_citation"]
    return [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]


def _fetch_dasha_runway_fresh(conn: Any, chart_id: str, aya: str, planet: str,
                               now: datetime, weights: dict[str, Any]) -> dict | None:
    """Fresh, correct dasha-runway re-derivation for `planet`'s next-or-current
    Vimshottari Mahadasha, read directly from L1 chart_dashas.

    Mirrors ga_vichara_writer.py's own `_dasha_runway()` curve exactly, using
    the SAME brahma_vichara_constants.leverage_weights registry values (no
    new constants invented) — but does NOT reuse chart_vichara.leverage_index's
    own embedded runway sub-field for `planet`.

    WHY: a live cross-check during B-4 authoring (2026-07-22) found that
    field, for chart 482012f1/VEN/wealth (leverage_index=3.9375, same build
    b84c3797), reads years_to_start=0 / md_duration_years=20 — implying
    Venus's Mahadasha is already running. The SAME build's own chart_dashas
    (level_n=1, lord_graha='Venus') instead shows the next/only Venus MD
    starting 2034-08-18 — ~8.08 years out from that build's computed_at, not
    0. This is a genuine discrepancy inside ga_vichara's own leverage_index
    dasha-runway sub-computation (root cause not diagnosed here — not a B-4
    may_touch file per BRIEF_D4B §3; flagged to the Binder as its own named
    finding). B-4's own join therefore re-derives this factor independently
    and correctly rather than propagate a value already shown to be wrong.
    """
    rows = conn.execute(
        """SELECT dasha_row_id, start_iso, end_iso, duration_days
           FROM chart_dashas
           WHERE chart_id = %s AND ayanamsha_id = %s AND system_id = 'vimshottari'
             AND level_n = 1 AND lord_graha = %s
           ORDER BY start_iso""",
        [chart_id, aya, planet],
    ).fetchall()
    keys = ["dasha_row_id", "start_iso", "end_iso", "duration_days"]
    md_rows = [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]

    lookforward_years = float(weights.get("runway_lookforward_years", 30))
    base = float(weights.get("runway_base", 1.0))
    scale = float(weights.get("runway_scale", 0.5))
    dur_norm = float(weights.get("runway_duration_norm_years", 20))
    start_horizon = float(weights.get("runway_start_horizon_years", 15))

    best: dict[str, Any] | None = None
    for r in md_rows:
        start, end = r.get("start_iso"), r.get("end_iso")
        if start is None or end is None:
            continue
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if end < now:
            continue  # already elapsed
        s_years = max(0.0, (start - now).days / 365.25)
        if s_years > lookforward_years:
            continue
        if best is None or s_years < best["years_to_start"]:
            duration_days = r.get("duration_days")
            y_years = (float(duration_days) / 365.25 if duration_days is not None
                       else (end - start).days / 365.25)
            best = {
                "dasha_row_id": r.get("dasha_row_id"),
                "years_to_start": round(s_years, 3),
                "md_duration_years": round(y_years, 3),
                "start_iso": start,
                "end_iso": end,
                "currently_running": start <= now,
            }

    if best is None:
        return None
    weight = base + scale * (best["md_duration_years"] / dur_norm) * max(
        0.0, 1 - best["years_to_start"] / start_horizon)
    best["runway_weight"] = round(weight, 6)
    return best


import re as _re
_CONDITIONAL_PREAMBLE_RE = _re.compile(r'^For\s[^:]{5,200}:\s*', _re.IGNORECASE)


def _strip_conditional_preamble(text: str) -> tuple[str, bool]:
    """Strip 'For <affliction clause>: ' preamble from prescription_text.
    Returns (cleaned_text, preamble_was_stripped).
    The preamble states a condition never tested against chart state (F-116)."""
    m = _CONDITIONAL_PREAMBLE_RE.match(text)
    if m:
        remainder = text[m.end():]
        return (remainder[:1].upper() + remainder[1:] if remainder else ""), True
    return text, False


def _fetch_remedies_for_graha(conn: Any, planet: str, limit: int = 5) -> list[dict]:
    """Fetch top remedies from brahma_remedy_corpus for this planet."""
    rows = conn.execute(
        """SELECT remedy_id, remedy_type, prescription_text, confidence,
                  source_canonical_id, source_citation, classical_ref,
                  contraindications, cost_tier
           FROM brahma_remedy_corpus
           WHERE lower(planet) = %s AND scaffold_status = 'live'
           ORDER BY confidence DESC NULLS LAST
           LIMIT %s""",
        [planet.lower(), limit],
    ).fetchall()
    keys = [
        "remedy_id", "remedy_type", "prescription_text", "confidence",
        "source_canonical_id", "source_citation", "classical_ref",
        "contraindications", "cost_tier",
    ]
    return [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]


# ── Priority class ─────────────────────────────────────────────────────────────

def _priority_class(rank: int, total: int) -> str:
    """Chart-relative remedy priority class (rank-in-chart thirds).

    MC-025a: the prior absolute-threshold cutoffs (critical>=0.70, high>=0.45,
    medium>=0.25) were calibrated against the broken formula whose baseline
    resonance_score sat near ~0.5 for every graha (see the _fetch_shadbala /
    _fetch_bhava_bala fixes above) — that made "high" trivially true for all
    nine grahas. Against the CORRECTED formula, weakness_score rarely
    approaches those absolute thresholds at all for a chart without severe,
    simultaneous affliction (combust + debilitated + heavily-afflicted), so
    keeping fixed thresholds would only have swapped "everyone high" for
    "everyone low" — the same degenerate flatness, inverted, and one that
    would also make the classing depend on how afflicted a chart happens to
    be overall rather than on which of ITS OWN grahas most needs remedial
    attention. `weakest_rank_in_chart` already names the right frame:
    upaya priority is inherently a comparison across THIS native's own nine
    grahas (classical practice remedies the relatively weakest, not grahas
    that fail a universal absolute bar). Reclassified as rank-relative thirds
    of the chart's own N grahas: robust to any chart's overall affliction
    severity, and guaranteed >1 distinct class whenever N>1.
    """
    if total <= 0:
        return "low"
    if rank <= 1:
        return "critical"
    if rank <= max(1, -(-total // 3)):        # ceil(total/3)
        return "high"
    if rank <= max(1, -(-2 * total // 3)):    # ceil(2*total/3)
        return "medium"
    return "low"


def _feasibility(remedy: dict) -> float:
    """Simple feasibility: mantra/charity → high, gem → low."""
    rt = str(remedy.get("remedy_type") or "mantra").lower()
    if rt in ("mantra", "japa", "vrata", "behavioral"):
        return 0.90
    if rt in ("charity", "puja", "homa"):
        return 0.75
    if rt in ("yantra",):
        return 0.60
    if rt in ("gemstone",):
        return 0.45
    return 0.70


def _complexity(remedy: dict) -> str:
    rt = str(remedy.get("remedy_type") or "mantra").lower()
    if rt in ("mantra", "japa", "behavioral"):
        return "simple"
    if rt in ("charity", "puja", "vrata"):
        return "moderate"
    return "complex"


# ── Main per-ayanamsha build ───────────────────────────────────────────────────

def _build_resonances_and_prescriptions(
    chart_id: str, aya: str, build_id: str, conn: Any, now: str
) -> tuple[list[dict], list[dict]]:
    from bodha_writers.formulas import (
        ResonanceInputs, resonance_score_v1,
        ResonanceMatchInputs, resonance_match_score_v1,
    )

    shadbala      = _fetch_shadbala(conn, chart_id, aya)
    # MC-025b (§N.5): the single L1-authoritative weakest graha by shadbala.
    # Both bo_upaya and bo_chart_digest must read this — never recompute their own.
    weakest_graha_shadbala = _weakest_graha_by_shadbala(shadbala)
    bhava_bala    = _fetch_bhava_bala(conn, chart_id, aya)
    special_states = _fetch_special_states(conn, chart_id, aya)
    placements    = _fetch_graha_house_placements(conn, chart_id, aya)
    yoga_karakas  = _fetch_yoga_karaka_flags(conn, chart_id, aya)
    chara_roles   = _fetch_chara_roles(conn, chart_id, aya)
    dosha_by_graha = _fetch_msr_dosha_sigs_by_graha(conn, chart_id, aya)
    # β.G / EL-51: real backfill (the MSR path above is structurally dead — see comment on
    # _fetch_active_doshas_by_graha). Union rather than replace: if the MSR path is ever
    # repaired upstream, both sources merge honestly instead of one silently overwriting.
    doshas_from_facts = _fetch_active_doshas_by_graha(conn, chart_id, aya)
    for graha, names in doshas_from_facts.items():
        existing = dosha_by_graha.setdefault(graha, [])
        for name in names:
            if name not in existing:
                existing.append(name)
    # β.G / EL-51: L1 maraka significators (2nd/7th house lords) — fetched once per
    # ayanamsha, referenced (never recomputed) for the gemstone contraindication verdict.
    maraka_facts = _fetch_maraka_facts(conn, chart_id, aya)
    chart_typology = _fetch_chart_typology(conn, chart_id, aya)
    # BA-P2.5 #4: real wired inputs (see the 3 new fetchers above _fetch_chart_typology).
    dispositor_strength = _fetch_dispositor_terminal_strength(conn, chart_id, aya)
    try:
        _now_dt = datetime.fromisoformat(now)
    except (TypeError, ValueError):
        _now_dt = datetime.now(timezone.utc)
    dasha_proximity = _fetch_dasha_proximity(conn, chart_id, aya, _now_dt)
    cgm_motif_weakness = _fetch_cgm_motif_weakness(conn, chart_id, aya)
    # CR-67 (SARVA-SIDDHI W-3): graha → CDLM cells the graha is a material
    # constituent of (was 100% NULL DB-wide — the missing L2 derivation).
    graha_cdlm_cells = _fetch_graha_cdlm_cells(conn, chart_id, aya)

    resonances: list[dict] = []

    for graha in KNOWN_GRAHAS:
        states       = special_states.get(graha, set())
        combustion   = 1.0 if "combust" in states else 0.0
        # Debility: only apply the 0.3 neutral penalty when states are KNOWN for
        # this graha (key present in special_states) but lack exalted/moolatrikona.
        # If the graha is absent from special_states entirely, default to 0.0.
        if graha not in special_states:
            debility = 0.0
        elif "debilitated" in states:
            debility = 1.0
        elif "exalted" in states or "moolatrikona" in states:
            debility = 0.0
        else:
            debility = 0.3
        afflictions  = min(len(dosha_by_graha.get(graha, [])) / 3.0, 1.0)
        house        = placements.get(graha, 1)
        # BA-P3B: track which inputs fell back to silent defaults (F-007 guard)
        inputs_complete = True
        missing_inputs: list[str] = []
        sha_norm = shadbala.get(graha, None)
        if sha_norm is None:
            # MC-025a: the fallback for "no L1 shadbala ratio row" (structurally
            # true for Rahu/Ketu — classical shadbala has no defined requirement
            # for the nodes) must be the formula's NEUTRAL/no-penalty value for
            # this (1 - shadbala_normalized) term, i.e. 1.0, not the generic
            # dataclass default of 0.5. 0.5 reads as "half of required" on the
            # corrected ratio scale — an unearned weakness penalty for missing
            # data, exactly the B.10 "absence of evidence is not evidence of
            # weakness" principle this same file already applies to
            # cancellation_burden/cdlm_weakest_constituent_count below.
            sha_norm = 1.0
            inputs_complete = False
            missing_inputs.append("shadbala")
        bh_norm = bhava_bala.get(house, None)
        if bh_norm is None:
            bh_norm = 1.0  # same neutral-default reasoning as shadbala above
            inputs_complete = False
            missing_inputs.append("bhava_bala")
        is_yk        = graha in yoga_karakas
        chara_role   = chara_roles.get(graha)
        # MC-025a: vargottama_absence_score wired from the now-fixed
        # graha_special_state_rollup (was a hardcoded 0.5 placeholder for
        # every graha regardless of the real is_vargottama fact).
        is_vargottama = "vargottama" in states
        vargottama_absence = 0.0 if is_vargottama else 1.0

        r_inputs = ResonanceInputs(
            shadbala_normalized=min(sha_norm, 1.0),
            bhava_bala_normalized=min(bh_norm, 1.0),
            combustion_score=combustion,
            debility_score=debility,
            affliction_count_normalized=afflictions,
            # BA-P2.5 #4 — honest placeholder: no already-computed per-graha
            # cancellation aggregate exists. ga_structural's yoga_fires rows carry
            # a per-YOGA cancellation_flag inside value_jsonb, keyed by yoga name,
            # not by graha; deriving a per-graha ratio would require assembling a
            # brand-new join across constituent_facts_array (fabricating a formula
            # that doesn't already exist elsewhere) — left at 0.0 per B.10.
            cancellation_burden=0.0,
            # BA-P2.5 #4 — WIRED: real L1 fact (ga_structural composite_dispositor_strength).
            dispositor_chain_weakness=round(1.0 - dispositor_strength.get(graha, 0.5), 6),
            vargottama_absence_score=vargottama_absence,
            # BA-P2.5 #4 — WIRED: real GA7 chart_dashas coverage as of computed_at.
            dasha_proximity_activation_score=dasha_proximity.get(graha, 0.0),
            msr_signals_in_conflict=min(len(dosha_by_graha.get(graha, [])) * 0.1, 1.0),
            # BA-P2.5 #4 — honest placeholder: bodha_cdlm_cells.weakest_constituent_graha_jsonb
            # exists as a column but is never populated by bo_sangati (dead column) — no real
            # per-graha CDLM value exists yet to reference. Left at 0.0 per B.10.
            cdlm_weakest_constituent_count=0.0,
            # BA-P2.5 #4 — WIRED: real bodha_cgm_motifs.motif_strength (min over the graha's
            # motif memberships). Often 0.0 in practice while bo_cgm_motifs' stellium /
            # parivartana_chain detectors remain Tier-3-blocked on missing bo_karanajala
            # dispositor edges — that is a bo_cgm_motifs-side gap, not fabricated here.
            cgm_motifs_weakest_node=cgm_motif_weakness.get(graha, 0.0),
            is_yoga_karaka=is_yk,
            chara_role=chara_role,
        )
        r_result = resonance_score_v1(r_inputs)

        resonance_id = str(uuid.uuid4())
        resonances.append({
            "_graha": graha,
            "_resonance_id": resonance_id,
            "_resonance_score": float(r_result["resonance_score"]),
            "_is_yoga_karaka": is_yk,
            "_chara_role": chara_role,
            "resonance_id": resonance_id,
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "graha": graha,
            "resonance_score": round(float(r_result["resonance_score"]), 6),
            "resonance_score_formula_version": r_result["resonance_score_formula_version"],
            "weakness_score": round(float(r_result["weakness_score"]), 6),
            "contradiction_factor": round(float(r_result["contradiction_factor"]), 6),
            "domain_burden": round(float(r_result["domain_burden"]), 6),
            "motif_burden": round(float(r_result["motif_burden"]), 6),
            "is_yoga_karaka_flag": is_yk,
            "is_chara_karaka_role": chara_role,
            "weakest_rank_in_chart": None,  # set after ranking
            "remedy_priority_class": None,  # set after ranking
            "associated_doshas_array": dosha_by_graha.get(graha),
            # CR-67: real, L1-grounded CDLM cells this graha is a material
            # constituent of (None when the graha bridges no cell above the
            # equal-share salience baseline — an honest empty, not a NULL gap).
            "associated_cdlm_cells_array": (graha_cdlm_cells.get(graha) or None),
            "ephemeris_audit_jsonb": json.dumps({
                "inputs_complete": inputs_complete,
                "missing_inputs": missing_inputs,
                "sha_norm_used": round(sha_norm, 4),
                "bh_norm_used": round(bh_norm, 4),
                "dispositor_chain_weakness_used": round(1.0 - dispositor_strength.get(graha, 0.5), 4),
                "dasha_proximity_activation_score_used": round(dasha_proximity.get(graha, 0.0), 4),
                "cgm_motifs_weakest_node_used": round(cgm_motif_weakness.get(graha, 0.0), 4),
                # MC-025b (§N.5): L1-authoritative weakest-graha designation, distinct from
                # the COMPOSITE weakest_rank_in_chart. Both bo_upaya and bo_chart_digest read
                # this single L1 source (min graha_shadbala_total.rupa) — for 482012f1 → VEN.
                "weakest_graha_by_shadbala_l1": weakest_graha_shadbala,
                "is_weakest_by_shadbala_l1": (graha == weakest_graha_shadbala),
                "weakest_graha_authority_note": (
                    "weakest_graha_by_shadbala_l1 = min(L1 graha_shadbala_total.rupa) — the §N.5 "
                    "single source of truth for 'weakest graha'. weakest_rank_in_chart is a SEPARATE "
                    "composite remedy-priority rank; do not read it as the shadbala-weakest graha."
                ),
                # T7 (UPĀYA-ŚODHANA, PR #809): vargottama_absence_score is now wired from the
                # fixed special-state fetch (was hardcoded 0.5 for everyone). Preserved as-is —
                # independent of the weakest-graha fields above (different source: is_vargottama).
                "vargottama_absence_score": vargottama_absence,
                "cancellation_burden": 0.0,
                "cdlm_weakest_constituent_count": 0.0,
                # CR-67: count of CDLM cross-domain-linkage cells this graha is a
                # material constituent of (salience-share ≥ equal-share baseline),
                # resolved via constituent_facts_array → chart_facts.fact_subject.
                "associated_cdlm_cell_count": len(graha_cdlm_cells.get(graha) or []),
                "note": (
                    "cancellation_burden, cdlm_weakest_constituent_count remain honest 0.0 "
                    "placeholders (no already-computed source exists yet, B.10); "
                    "shadbala_normalized, bhava_bala_normalized, vargottama_absence_score, "
                    "dispositor_chain_weakness, dasha_proximity_activation_score, "
                    "cgm_motifs_weakest_node are all wired to real L1/L2 data "
                    "(MC-025a fixed shadbala/bhava_bala/vargottama; BA-P2.5 #4 wired the rest). "
                    "shadbala/bhava_bala missing-data fallback is 1.0 (neutral/no-penalty for "
                    "this term), not 0.5 — see _fetch_shadbala's docstring."
                ),
            }),
            "verification_pass_status": "documented_approximation",
            "citation_ref": f"bo_upaya/resonance/{graha}",
            "citation_human": f"Resonance: {graha} | sha={sha_norm:.2f} dosha_count={len(dosha_by_graha.get(graha, []))}",
            "computed_at": now,
        })

    # Rank by resonance_score DESC
    # NOTE (T2 convergence): weakest_rank_in_chart is the chart's single
    # weakest-graha authority pending T2's shared cross-writer helper (SETU-
    # BANDHA / MC-025b) landing. Until then this ranking is sourced directly
    # from the now-corrected L1 shadbala (_fetch_shadbala reads
    # graha_shadbala_total/ratio) + bhava_bala + special-state inputs above —
    # never an independently-invented weakness metric — so it already
    # converges with L1 ṣaḍbala's own minimum (verified for 482012f1: Venus,
    # the lowest shadbala ratio among the 7 classical grahas, ranks #1 here).
    # Once T2's shared authority lands, swap this sort key for its output
    # directly rather than resonance_score, per the brief's single-authority
    # rule (§N.5).
    resonances.sort(key=lambda x: x["_resonance_score"], reverse=True)
    _n_resonances = len(resonances)
    for rank, row in enumerate(resonances, start=1):
        row["weakest_rank_in_chart"] = rank
        row["remedy_priority_class"] = _priority_class(rank, _n_resonances)

    # Distribution guard: warn if all resonance_score values are degenerate
    if len(resonances) > 2:
        scores = [r["_resonance_score"] for r in resonances]
        score_range = max(scores) - min(scores)
        if score_range < 0.001:
            logger.warning(
                "[bo_upaya] DEGENERATE DISTRIBUTION: all resonance_score values are ~%.4f; "
                "shadbala or bhava_bala inputs may be missing for chart %s/%s",
                scores[0], chart_id, aya,
            )

    # Prescriptions (top 3 remedies per graha from corpus)
    prescriptions: list[dict] = []
    for res in resonances:
        graha         = res["_graha"]
        resonance_id  = res["_resonance_id"]
        remedies_from_corpus = _fetch_remedies_for_graha(conn, graha, limit=3)

        for corpus_row in remedies_from_corpus:
            rm_inputs = ResonanceMatchInputs(
                classical_strength_for_graha=float(corpus_row.get("confidence") or 0.85),
                chart_typology=chart_typology,
                remedy_category=str(corpus_row.get("remedy_type") or "mantra"),
                cross_tradition_corroboration_count=1,
                has_active_counter_indication=False,
            )
            rm_result = resonance_match_score_v1(rm_inputs)

            remedy_category = str(corpus_row.get("remedy_type") or "mantra")
            counter_indications: list[str] = []
            if corpus_row.get("contraindications"):
                counter_indications.append(corpus_row["contraindications"])

            # β.G / EL-51 — deterministic maraka verdict, gemstone rows only, cited.
            maraka_verdict: dict[str, Any] | None = None
            if remedy_category == "gemstone":
                maraka_verdict = _compute_gemstone_maraka_verdict(graha, maraka_facts)
                if maraka_verdict.get("verdict") == "contraindicated":
                    counter_indications.append(
                        f"MARAKA CONTRAINDICATION (computed, {MARAKA_CITATION.split('(')[0].strip()}): "
                        f"{maraka_verdict['reason']}"
                    )

            # β.G / EL-51 — estimated_cost_inr_range_jsonb: real INR market pricing is not
            # classical/deterministic data (no corpus source computes it) — B.10 forbids
            # inventing a number here. Disclose the gap explicitly instead of leaving a bare
            # NULL a consumer would misread as "not applicable" rather than "not computable
            # from this corpus." cost_tier (qualitative, already real) is carried alongside.
            cost_gap_disclosure = json.dumps({
                "available": False,
                "reason": "INR market pricing requires an external, time-varying market-price "
                          "source not present in the classical-text corpus this system computes "
                          "from — B.10 forbids inventing a figure. See cost_tier for the "
                          "qualitative (free/low/medium/high) classification, which IS "
                          "corpus-derived.",
                "cost_tier": corpus_row.get("cost_tier"),
                "external_computation_required": "market gemstone/ritual-goods pricing lookup",
            })

            _raw_pt = str(corpus_row.get("prescription_text") or "")
            _label_human, _preamble_stripped = _strip_conditional_preamble(_raw_pt)
            prescriptions.append({
                "prescription_id": str(uuid.uuid4()),
                "chart_id": chart_id,
                "ayanamsha_id": aya,
                "build_id": build_id,
                "snapshot_type": SNAPSHOT_TYPE,
                "target_graha": graha,
                "target_resonance_id": resonance_id,
                "tradition": "parashari",
                "remedy_category": str(corpus_row.get("remedy_type") or "mantra"),
                "remedy_id_g27": str(corpus_row.get("remedy_id") or ""),
                "remedy_label_human": _label_human[:200],
                "prescription_detail_jsonb": json.dumps({
                    "prescription_text": corpus_row.get("prescription_text"),
                    "mantra_text": corpus_row.get("mantra_text"),
                    "gemstone": corpus_row.get("gemstone"),
                    "charity_action": corpus_row.get("charity_action"),
                    "deity": corpus_row.get("deity"),
                    # β.G / EL-51: structured, cited, deterministic verdict (gemstone rows
                    # only; None for every other category — never fabricated for non-gemstone
                    # remedies where the maraka rule doesn't apply).
                    "maraka_contraindication_verdict": maraka_verdict,
                    "preamble_stripped": _preamble_stripped,  # True = conditional clause removed; False = none present
                }),
                "classical_strength_rating": str(corpus_row.get("confidence") or ""),
                "classical_sources_jsonb": json.dumps({"source_id": str(corpus_row.get("source_canonical_id") or "BPHS"), "citation": str(corpus_row.get("classical_ref") or "")}),
                "targets_dosha_class": (dosha_by_graha.get(graha) or [None])[0],
                "resonance_match_score": round(float(rm_result["resonance_match_score"]), 6),
                "match_score_formula_version": rm_result["match_score_formula_version"],
                "counter_indications_array": (counter_indications or None),
                "feasibility_score": round(_feasibility(corpus_row), 4),
                "ritual_complexity_class": _complexity(corpus_row),
                "requires_acharya_review_flag": (
                    str(corpus_row.get("remedy_type") or "").lower() in ("gemstone", "homa")
                    or bool(maraka_verdict and maraka_verdict.get("verdict") == "contraindicated")
                ),
                "cross_tradition_corroboration_count": 1,
                "verification_pass_status": "documented_approximation",
                "citation_ref": f"brahma_remedy_corpus/{corpus_row.get('remedy_id')}",
                "citation_human": f"G27 remedy {corpus_row.get('remedy_id')} for {graha}",
                "computed_at": now,
                # β.G / EL-51: honest INR-cost-gap disclosure — see comment above this loop.
                # Wired into _PRESCRIPTION_INSERT (was a hardcoded NULL; now bound).
                "estimated_cost_inr_range_jsonb": cost_gap_disclosure,
            })

    return resonances, prescriptions


def _batch_insert(conn: Any, rows: list[dict], sql: str) -> int:
    inserted = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), _BATCH_SIZE):
            batch = rows[i:i + _BATCH_SIZE]
            cur.executemany(sql, batch)
            inserted += len(batch)
    return inserted


def _strip_private_keys(rows: list[dict]) -> list[dict]:
    """Remove _-prefixed helper keys before INSERT."""
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]


# ── WP-2.2 / LCA-5 RM sibling rollups (deterministic aggregation of the
#     resonances + prescriptions this same writer just built) ──────────────────

def _build_rm_summary(chart_id: str, aya: str, build_id: str,
                      resonances: list[dict], prescriptions: list[dict],
                      chart_typology: str, now: str) -> dict:
    """One rm_chart_summary row: the chart's remedy priorities distilled."""
    ranked_res = sorted(resonances, key=lambda r: r.get("resonance_score") or 0.0, reverse=True)
    top3 = [{"graha": r["graha"], "resonance_score": r.get("resonance_score"),
             "priority_class": r.get("remedy_priority_class")} for r in ranked_res[:3]]

    ranked_presc = sorted(prescriptions, key=lambda p: p.get("resonance_match_score") or 0.0, reverse=True)
    top10 = [{"prescription_id": p["prescription_id"], "target_graha": p["target_graha"],
              "remedy_category": p["remedy_category"], "match_score": p.get("resonance_match_score")}
             for p in ranked_presc[:10]]

    dosha_classes = [p["targets_dosha_class"] for p in prescriptions if p.get("targets_dosha_class")]
    dosha_counts: dict[str, int] = defaultdict(int)
    for dc in dosha_classes:
        dosha_counts[dc] += 1
    primary_dosha = max(dosha_counts, key=dosha_counts.get) if dosha_counts else None

    acharya_ct = sum(1 for p in prescriptions if p.get("requires_acharya_review_flag"))
    feasibilities = [float(p.get("feasibility_score") or 0.0) for p in prescriptions]
    mean_feas = round(sum(feasibilities) / len(feasibilities), 4) if feasibilities else 0.0

    # SHABDA-SHUDDHI Lane L5 (Fix 7a): when there are no resonances/prescriptions the
    # intensity is None — there is no assessment to make (emitting "light" was a false
    # clean-bill: it implied a real evaluation ran on actual data).
    if not ranked_res:
        intensity = None
    else:
        top_class = ranked_res[0].get("remedy_priority_class") or "low"
        intensity = {"critical": "intensive", "high": "sustained",
                     "moderate": "moderate", "low": "light"}.get(str(top_class), "moderate")

    trad_counts: dict[str, int] = defaultdict(int)
    for p in prescriptions:
        trad_counts[str(p.get("tradition") or "parashari")] += 1

    return {
        "summary_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": build_id,
        "snapshot_type": SNAPSHOT_TYPE,
        "top_3_resonance_targets_jsonb": json.dumps(top3),
        "top_10_priority_prescriptions_jsonb": json.dumps(top10),
        "recommended_intensity_class": intensity,
        "total_active_dosha_count": len(set(dosha_classes)),
        "primary_dosha_class": primary_dosha,
        "cross_tradition_convergence_jsonb": json.dumps(dict(trad_counts)),
        "remedy_chart_typology": chart_typology,
        "acharya_review_required_count": acharya_ct,
        "feasibility_assessment_jsonb": json.dumps(
            {"mean_feasibility": mean_feas, "prescription_count": len(prescriptions)}),
        # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
        # "pass" — an unconditional stamp with no verification logic behind it, and a
        # live false-green the serve layer counted as verified. Audited: nothing here
        # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
        "verification_pass_status": UNVERIFIED_DEFAULT,
        "citation_ref": "bo_upaya:rm_chart_summary_v1:bodha_rm_resonances+prescriptions",
        "citation_human": f"RM chart summary — {len(resonances)} resonances, {len(prescriptions)} prescriptions",
        "computed_at": now,
    }


def _build_dosha_bundles(chart_id: str, aya: str, build_id: str,
                         prescriptions: list[dict], now: str) -> list[dict]:
    """Group prescriptions by the dosha class they remediate."""
    by_dosha: dict[str, list[dict]] = defaultdict(list)
    for p in prescriptions:
        dc = p.get("targets_dosha_class")
        if dc:
            by_dosha[dc].append(p)

    rows: list[dict] = []
    for dosha_class, presc in sorted(by_dosha.items()):
        pids = [p["prescription_id"] for p in presc]
        sources = sorted({str((json.loads(p["classical_sources_jsonb"])
                               if isinstance(p.get("classical_sources_jsonb"), str)
                               else (p.get("classical_sources_jsonb") or {})).get("source_id", "BPHS"))
                          for p in presc})
        grahas = sorted({p["target_graha"] for p in presc})
        rows.append({
            "bundle_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "dosha_class": dosha_class,
            "active_flag": True,
            "intensity_score": round(min(len(presc) / 3.0, 1.0), 4),
            "cancellation_count": 0,
            "prescription_ids_in_bundle_array": pids,
            "bundle_summary_jsonb": json.dumps(
                {"prescription_count": len(presc), "target_grahas": grahas}),
            "classical_sources_jsonb": json.dumps({"source_ids": sources}),
            # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
            # "pass" — an unconditional stamp with no verification logic behind it, and a
            # live false-green the serve layer counted as verified. Audited: nothing here
            # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "citation_ref": f"bo_upaya:dosha_bundle_v1:{dosha_class}",
            "citation_human": f"Dosha remedy bundle for {dosha_class} — {len(presc)} prescriptions",
            "computed_at": now,
        })
    return rows


def _build_pattern_remedies(chart_id: str, aya: str, build_id: str,
                            resonances: list[dict], prescriptions: list[dict],
                            now: str) -> list[dict]:
    """Per-resonance-target remedy theme: the prescriptions grouped by target graha,
    keyed to the resonance (pattern source) that motivated them."""
    presc_by_res: dict[str, list[dict]] = defaultdict(list)
    for p in prescriptions:
        rid = p.get("target_resonance_id")
        if rid:
            presc_by_res[str(rid)].append(p)

    rows: list[dict] = []
    for res in resonances:
        rid = str(res.get("resonance_id"))
        presc = presc_by_res.get(rid, [])
        if not presc:
            continue
        rows.append({
            "pattern_remedy_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "source_kind": "resonance",
            "source_id": rid,
            "remedy_theme": f"strengthen_{res['graha']}",
            "prescription_ids_array": [p["prescription_id"] for p in presc],
            "theme_strength": round(float(res.get("resonance_score") or 0.0), 6),
            "cross_tradition_unanimity_score": round(
                len({str(p.get("tradition")) for p in presc}) / 4.0, 4),
            # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
            # "pass" — an unconditional stamp with no verification logic behind it, and a
            # live false-green the serve layer counted as verified. Audited: nothing here
            # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "citation_ref": f"bo_upaya:pattern_remedy_v1:resonance/{rid}",
            "citation_human": f"Pattern remedy theme strengthen_{res['graha']} — {len(presc)} prescriptions",
            "computed_at": now,
        })
    return rows


# ── B-4 (BRIEF_D4B §1) remedy-leverage join builder ─────────────────────────

_MAX_LEVERAGE_TARGETS = 3  # top-N wealth-leverage grahas per ayanamsha


def _build_remedy_leverage_windows(
    chart_id: str, aya: str, build_id: str, conn: Any, now: datetime,
    prescriptions: list[dict], sadhana_events: list[dict],
    leverage_weights: dict[str, Any], compute_now: str,
) -> list[dict]:
    """B-4: leverage_index (weakest load-bearing graha, wealth domain) x
    sadhana history (LEL spiritual arc, pre-embargo) x dasha runway
    (intervention window = years BEFORE the weak lord's MD opens).

    Writes one bodha_rm_dasha_windowed_prescriptions row per top wealth-
    leverage graha that has both (a) an existing prescription this same
    writer just built (base_prescription_id FK) and (b) a resolvable next/
    current Mahadasha in chart_dashas. Honestly skips (logs, does not
    fabricate) a graha missing either.
    """
    from bodha_writers.formulas import RemedyLeverageJoinInputs, remedy_leverage_join_v1

    leverage_rows = _fetch_wealth_leverage_index(conn, chart_id, aya)[:_MAX_LEVERAGE_TARGETS]
    if not leverage_rows:
        logger.info("[bo_upaya B-4] no positive wealth leverage_index rows for %s/%s "
                    "— no schedulable remedy window built this ayanamsha", chart_id, aya)
        return []

    sadhana_count = len(sadhana_events)
    sadhana_event_ids = [str(e["event_id"]) for e in sadhana_events]

    prescriptions_by_graha: dict[str, list[dict]] = defaultdict(list)
    for p in prescriptions:
        prescriptions_by_graha[p["target_graha"]].append(p)

    windows: list[dict] = []
    for lev in leverage_rows:
        subj = str(lev["subject"])
        planet = _SUBJECT_TO_PLANET.get(subj)
        if planet is None:
            logger.warning("[bo_upaya B-4] leverage_index subject '%s' has no known "
                           "graha mapping — skipped", subj)
            continue

        candidate_prescs = prescriptions_by_graha.get(planet, [])
        if not candidate_prescs:
            logger.warning("[bo_upaya B-4] no bodha_rm_remedy_prescriptions row for "
                           "%s (wealth leverage_index=%.4f) — no base_prescription_id "
                           "available, schedulable window skipped honestly (not fabricated)",
                           planet, float(lev["value_num"]))
            continue
        base_presc = max(candidate_prescs, key=lambda p: p.get("resonance_match_score") or 0.0)

        runway = _fetch_dasha_runway_fresh(conn, chart_id, aya, planet, now, leverage_weights)
        if runway is None:
            logger.warning("[bo_upaya B-4] no resolvable next/current Mahadasha for %s "
                           "within the runway_lookforward_years window — schedulable "
                           "window skipped honestly (not fabricated)", planet)
            continue

        join_result = remedy_leverage_join_v1(RemedyLeverageJoinInputs(
            leverage_index_value=float(lev["value_num"]),
            sadhana_milestone_count=sadhana_count,
            dasha_runway_weight=runway["runway_weight"],
        ))

        if runway["currently_running"]:
            window_start, window_end = now, runway["end_iso"]
            phase = "active_md_direct_intervention"
        else:
            window_start, window_end = now, runway["start_iso"]
            phase = "pre_md_preparation_window"

        windows.append({
            "window_prescription_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "base_prescription_id": base_presc["prescription_id"],
            "dasha_system": "vimshottari",
            "dasha_level": "maha",
            "dasha_lord": planet,
            "window_start_iso": window_start,
            "window_end_iso": window_end,
            "window_intensity_multiplier": join_result["remedy_leverage_score"],
            "schedule_jsonb": json.dumps({
                "join_formula_version": join_result["remedy_leverage_join_formula_version"],
                "weakest_load_bearing_graha": planet,
                "leverage_index": {
                    "value": float(lev["value_num"]),
                    "domain": "wealth",
                    "vichara_row_id": lev["vichara_row_id"],
                    "constituent_fact_ids": lev.get("constituent_fact_ids") or [],
                    "source": "chart_vichara (ga_vichara L1 leverage_index, referenced not recomputed, §N.5)",
                },
                "sadhana_history": {
                    "factor": join_result["sadhana_history_factor"],
                    "pre_embargo_milestone_count": sadhana_count,
                    "milestone_event_ids": sadhana_event_ids,
                    "embargo_date": _SADHANA_EMBARGO_DATE,
                    "source": "life_events (LEL calibration corpus, event_type='spiritual', strictly pre-embargo)",
                },
                "dasha_runway": {
                    "years_before_md_open": runway["years_to_start"],
                    "md_duration_years": runway["md_duration_years"],
                    "runway_weight": runway["runway_weight"],
                    "currently_running": runway["currently_running"],
                    "dasha_row_id": str(runway["dasha_row_id"]),
                    "source": "chart_dashas (L1, fresh live re-derivation)",
                    "note": ("chart_vichara.leverage_index's own embedded runway sub-field "
                             "for this graha/domain is NOT reused here — see "
                             "_fetch_dasha_runway_fresh docstring for the live discrepancy "
                             "found during B-4 authoring (2026-07-22)."),
                },
                "remedy_leverage_score": join_result["remedy_leverage_score"],
            }),
            "phase_within_window": phase,
            "verification_pass_status": "documented_approximation",
            "citation_ref": f"bo_upaya/remedy_leverage_join/{planet}/wealth",
            "citation_human": (f"B-4 remedy-leverage join: {planet} wealth leverage_index="
                               f"{float(lev['value_num']):.4f} x sadhana_history_factor="
                               f"{join_result['sadhana_history_factor']:.4f} x dasha_runway_weight="
                               f"{runway['runway_weight']:.4f} = {join_result['remedy_leverage_score']:.4f}"),
            "computed_at": compute_now,
        })

    return windows


@register("bo_upaya")
class BoUpayaWriter(WriterBase):
    """bo_upaya: Remediation Map — resonances + prescriptions grounded to G27 corpus."""
    asset_id = "bo_upaya"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import (
            replace_prior_rm_resonances, replace_prior_rm_prescriptions,
            replace_prior_rm_dasha_windowed,
        )

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now_dt   = datetime.now(timezone.utc)
        now      = now_dt.isoformat()
        total_res = 0
        total_presc = 0
        total_summary = 0
        total_bundles = 0
        total_patterns = 0
        total_windowed = 0

        # WP-2.2 / LCA-5 idempotency for the sibling rollup tables (chart-scoped
        # delete-then-insert per §N.3).
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bodha_rm_chart_summary WHERE chart_id = %s", [chart_id])
            cur.execute("DELETE FROM bodha_rm_dosha_remedy_bundles WHERE chart_id = %s", [chart_id])
            cur.execute("DELETE FROM bodha_rm_pattern_remedies WHERE chart_id = %s", [chart_id])

        # B-4 (BRIEF_D4B §1): registry weights + sadhana history are chart-scoped,
        # not per-ayanamsha — fetch once, reuse across the CANONICAL_AYAS loop.
        leverage_weights = _fetch_leverage_weights(conn)
        sadhana_events = _fetch_sadhana_milestones(conn, chart_id)
        logger.info("[bo_upaya B-4] %d pre-embargo (< %s) LEL sadhana milestones for chart=%s",
                    len(sadhana_events), _SADHANA_EMBARGO_DATE, chart_id)

        for aya in CANONICAL_AYAS:
            if ctx.dry_run:
                logger.info("[bo_upaya dry_run] %s", aya)
                continue

            resonances, prescriptions = _build_resonances_and_prescriptions(
                chart_id, aya, build_id, conn, now
            )

            # B-4's windowed rows FK-reference bodha_rm_remedy_prescriptions —
            # delete them BEFORE the prescriptions they reference are replaced.
            replace_prior_rm_dasha_windowed(conn, chart_id, aya)
            replace_prior_rm_prescriptions(conn, chart_id, aya, SNAPSHOT_TYPE)
            replace_prior_rm_resonances(conn, chart_id, aya, SNAPSHOT_TYPE)

            clean_res = _strip_private_keys(resonances)
            logger.info("[bo_upaya] %s — %d resonances, %d prescriptions",
                        aya, len(resonances), len(prescriptions))
            total_res   += _batch_insert(conn, clean_res, _RESONANCE_INSERT)
            total_presc += _batch_insert(conn, prescriptions, _PRESCRIPTION_INSERT)

            # ── B-4: remedy-leverage join (needs the just-built prescriptions'
            # in-memory prescription_id values, same pattern as the RM rollups
            # below) ──────────────────────────────────────────────────────────
            windows = _build_remedy_leverage_windows(
                chart_id, aya, build_id, conn, now_dt, prescriptions,
                sadhana_events, leverage_weights, now,
            )
            if windows:
                with conn.cursor() as cur:
                    for w in windows:
                        cur.execute(_WINDOWED_INSERT, w)
                total_windowed += len(windows)

            # ── RM sibling rollups (deterministic aggregation of the above) ──────
            if prescriptions:
                chart_typology = _fetch_chart_typology(conn, chart_id, aya)
                summary = _build_rm_summary(chart_id, aya, build_id, clean_res,
                                            prescriptions, chart_typology, now)
                bundles = _build_dosha_bundles(chart_id, aya, build_id, prescriptions, now)
                patterns = _build_pattern_remedies(chart_id, aya, build_id, clean_res,
                                                   prescriptions, now)
                with conn.cursor() as cur:
                    cur.execute(_RM_SUMMARY_INSERT, summary)
                    for b in bundles:
                        cur.execute(_RM_BUNDLE_INSERT, b)
                    for p in patterns:
                        cur.execute(_RM_PATTERN_INSERT, p)
                total_summary += 1
                total_bundles += len(bundles)
                total_patterns += len(patterns)

        if not ctx.dry_run and total_presc == 0:
            raise RuntimeError(
                f"[bo_upaya] G3: chart_id={chart_id} — 0 remedy prescriptions written; "
                "brahma_remedy_corpus may be empty (L0 Brahmagyan corpus must be seeded)"
            )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=(total_res + total_presc + total_summary + total_bundles
                           + total_patterns + total_windowed),
            notes=(f"resonances={total_res} prescriptions={total_presc} "
                   f"rm_chart_summary={total_summary} dosha_bundles={total_bundles} "
                   f"pattern_remedies={total_patterns} "
                   f"dasha_windowed_prescriptions={total_windowed} "
                   f"(B-4 remedy-leverage join: wealth leverage_index x sadhana history "
                   f"[{len(sadhana_events)} pre-embargo milestones] x fresh dasha runway)"),
        )
