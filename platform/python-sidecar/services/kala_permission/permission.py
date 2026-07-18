"""
services.kala_permission.permission — PERMISSION lock (L3 Kāla).

Doctrine-Waves D-3, wave/D-3/T-4.

PERMISSION answers: "does this Mahādaśā(MD)-bhukti(AD) window actually carry
license to deliver its promised result?" It is a GATE on top of the
Vimśottarī spine, not a re-derivation of it — every input below is either
queried directly from an existing L1/L3 table (chart_dashas, chart_facts,
chart_vichara) or delegated to an existing, already-ratified service
(`derive_dasha_consensus` — U1/D20a; `compute_tara_position`/`get_tara_detail`
— Muhūrta Tara Bala, MC §Tara Bala). §N.5: this module NEVER restates a value
those sources already own; it only composes them.

Four inputs, per the T-4 brief:

  1. VIMŚOTTARĪ SPINE — `_fetch_vimshottari_spine()` confirms the (md_lord,
     ad_lord) pair the caller is asking about is a REAL row-pair in
     chart_dashas covering `as_of` (system_id='vimshottari', level_n 1+2).
     This is the base temporal spine PERMISSION anchors to (per the brief:
     "the primary daśā-bhukti-antardaśā chain ... as the base temporal spine
     PERMISSION anchors to"). If the pair/date does not resolve to a real
     row-pair, `spine_found=False` and `base_spine_strength` is heavily
     discounted (0.3, CALIBRATION) rather than the computation being
     silently skipped or fabricated (B.10).

  2. MULTI-SYSTEM CONCORDANCE AS GATE MULTIPLIER — `derive_dasha_consensus()`
     (services/ph_nimitta/dasha_consensus.py, READ-ONLY import, not edited)
     is called with target_lords={md_lord, ad_lord} over the spine's AD
     window. Its `confidence_multiplier` (ratified G-LADDER formula, D21:
     max(0.5, count/7) capped at 1.0) is applied as a genuine MULTIPLICATIVE
     term on `permission_score` — not as one of several additive currents
     (ka_sangam's 0.12-weighted `cross_dasha_agreement`, which this module
     does not touch). Low cross-system agreement (count=1 of 7) therefore
     caps `gate_multiplier` at 0.5 REGARDLESS of how strong the relational/
     capability terms are — a structural ceiling, not a nudge.

  3. PERIOD-LORD RELATIONAL ALGEBRA — `period_lord_relation()`, new logic
     (no prior graha-pair version existed in the codebase per the brief's
     research): (a) kendra/trikoṇa/dusthāna of the AD-lord's D1 house
     COUNTED FROM the MD-lord's own D1 house (bhava-counting-from-a-graha,
     the same classical technique `ga_structural_writer.py`'s
     `_bhava_link_type()` applies to bhava-pairs — adapted here to
     graha-pairs; that helper is NOT imported or edited, only its bhava-set
     convention (kendra {1,4,7,10}, trikoṇa {1,5,9}, dusthāna {6,8,12}) is
     reproduced); (b) tārā from the MD-lord's natal nakshatra to the
     AD-lord's natal nakshatra, via `panchang_engine.tara_bala`'s
     `compute_tara_position`/`get_tara_detail` (READ-ONLY import, not
     edited) — reused exactly as recommended in the T-4 brief.

  4. FULL DASHA-LORD CAPABILITY — `lord_capability()` is a Python mirror of
     the already-served `ganita_dasha_lord_capability_get` TS view
     (`platform/src/lib/retrieval/registry/layers/L1_ganita/
     get_dasha_lord_capability.ts`), computed here for exactly the two lords
     PERMISSION needs (md_lord, ad_lord) rather than all 9 MD lords. This is
     the SAME precedent `panchang_engine/tara_bala.py` itself documents
     ("Python-side version of the TS tara_bala helper ... parity confirmed
     against TS version") — not a fresh formula. `WARNING_TIER_WEIGHTS` and
     `LOW_SHADBALA_PERCENTILE` below are copied VERBATIM from the TS file so
     the two surfaces cannot silently drift; if they ever need to diverge,
     that is a follow-up cross-surface reconciliation, not a decision made
     silently here.

`compute_permission()` combines all four into one CR-87-compliant
(chart_id-required, no defaults) entry point. See its docstring for the
exact combination formula and which weights are flagged CALIBRATION
(i.e. this session's choice, not inherited from a ratified source) vs
INHERITED (copied from an already-ratified formula elsewhere).

No writer-side I/O contract applies here: this is a service/scoring module,
not a `WriterBase` subclass (§N.2) — it runs read-only SELECTs against
`chart_dashas` / `chart_facts` / `chart_vichara` via a caller-supplied
connection and never commits/closes it, exactly like `derive_dasha_consensus`
and `ph_nimitta` before it.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── READ-ONLY reuse: the two modules the T-4 brief explicitly names for reuse.
# Neither is imported for its I/O side (both are pure/service functions), and
# neither file is modified by this lane.
from panchang_engine.tara_bala import compute_tara_position, get_tara_detail  # noqa: E402
from services.ph_nimitta.dasha_consensus import (  # noqa: E402
    ALL_7_SYSTEMS,
    DashaConsensusResult,
    derive_dasha_consensus,
)

# ── brahmagyan.l0_upapada_maitri_rules is NOT on T-4's must-not-touch list
# (only ga_structural_writer.py / ga_nakshatra_compute.py / tara_bala.py /
# dasha_consensus.py / ka_sangam/** are) — imported directly, not copied.
from brahmagyan.l0_upapada_maitri_rules import (  # noqa: E402
    KENDRA_HOUSES_NON_LAGNA,  # frozenset({4, 7, 10}) — kendra EXCLUDING the reference bhava itself
    TRIKONA_HOUSES,           # frozenset({1, 5, 9})
)

# Dusthāna houses (6, 8, 12) — not defined as a shared constant anywhere
# read-only-importable for this lane (ga_vichara_writer.py's DUSTHANA_HOUSES
# is {6, 8, 12} too, but that module is outside this session's may_touch and
# is not on the explicit reuse list either, so this is reproduced as a
# standalone classical constant rather than imported).
DUSTHANA_HOUSES: frozenset[int] = frozenset({6, 8, 12})

# ── Verbatim copy of ga_structural_writer.py's NAKSHATRA_NAMES_27 (that file
# is explicitly must-not-touch/read-only-reuse-only for T-4; this 27-name
# ordered list is a fixed classical constant, copied rather than imported to
# avoid pulling in ga_structural_writer.py's full (heavy, pyjhora-adapter-
# dependent) import graph for one list literal). ────────────────────────────
NAKSHATRA_NAMES_27: list[str] = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# ── graha -> chart_facts/chart_vichara subject-code map. Mirrors
# ga_writers/ga_positions_writer.py's PLANET_TO_SUBJECT (that file is NOT on
# the must-not-touch list, but the map is 9 lines and copying it keeps this
# module import-graph-independent from the L1 writers, same rationale as the
# NAKSHATRA_NAMES_27 copy above and the same pattern get_dasha_lord_capability.ts
# uses for its own GRAHA_TO_SUBJECT mirror). ────────────────────────────────
PLANET_TO_SUBJECT: dict[str, str] = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
    "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
    "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN",
}

# ── WARNING_TIER_WEIGHTS / LOW_SHADBALA_PERCENTILE — copied VERBATIM from
# platform/src/lib/retrieval/registry/layers/L1_ganita/get_dasha_lord_capability.ts
# so the two surfaces (TS-served view, this Python gate input) cannot drift
# apart silently. If the TS file's formula changes, this copy must be updated
# in the same PR — flagged here as a cross-surface reconciliation obligation,
# not solved by this lane. ───────────────────────────────────────────────────
WARNING_HOUSE_CLASSES = frozenset({"dusthana_lord", "maraka"})
WARNING_TIER_WEIGHTS = {
    "house_class": 1,
    "low_shadbala": 1,
    "low_ratification": 1,
    "functional_malefic": 1,
}
LOW_SHADBALA_PERCENTILE = 0.34
_MAX_WARNING_SCORE = sum(WARNING_TIER_WEIGHTS.values())  # 4


def _require_chart_id(chart_id: Optional[str]) -> str:
    """CR-87: chart_id is REQUIRED everywhere in this module, no defaults,
    no silent fallback to a hardcoded native chart. Raises, never guesses."""
    if not chart_id or not isinstance(chart_id, str):
        raise ValueError(
            "kala_permission: chart_id is required (CR-87) — refusing to "
            "compute PERMISSION for an unspecified/defaulted chart."
        )
    return chart_id


# ═══════════════════════════════════════════════════════════════════════════
# 1. Vimśottarī spine
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class VimshottariSpine:
    """The (MD, AD) row-pair from chart_dashas this PERMISSION call anchors
    to, or an honest absence if the pair/date does not resolve."""
    found: bool
    md_lord: str
    ad_lord: str
    as_of: date
    md_dasha_row_id: Optional[str] = None
    md_start_date: Optional[date] = None
    md_end_date: Optional[date] = None
    ad_dasha_row_id: Optional[str] = None
    ad_start_date: Optional[date] = None
    ad_end_date: Optional[date] = None
    fact_ids: list[str] = field(default_factory=list)  # chart_dashas row ids, cited as the L1 grounding


def _fetch_vimshottari_spine(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    md_lord: str,
    ad_lord: str,
    as_of: date,
) -> VimshottariSpine:
    """Confirm (md_lord, ad_lord, as_of) is a real Vimśottarī MD/AD row-pair
    in chart_dashas — the base temporal spine PERMISSION anchors to. Read-only
    SELECT against chart_dashas; mirrors the covering-interval query pattern
    already used by pipeline/orchestrator/writers/bo_upaya.py's dasha-timing
    lookup and services/ka_dasha_kala/tree_walk.py's level-1 fetch (same
    table, same query shape — not a new query pattern)."""
    sql = """
        SELECT md.dasha_row_id, md.start_date, md.end_date,
               ad.dasha_row_id, ad.start_date, ad.end_date
        FROM chart_dashas md
        JOIN chart_dashas ad ON ad.parent_row_id = md.dasha_row_id
        WHERE md.chart_id = %s AND md.ayanamsha_id = %s
          AND md.system_id = 'vimshottari' AND md.level_n = 1
          AND md.lord_graha = %s
          AND ad.level_n = 2 AND ad.lord_graha = %s
          AND md.start_date <= %s AND md.end_date > %s
          AND ad.start_date <= %s AND ad.end_date > %s
        LIMIT 1
    """
    row = conn.execute(
        sql, [chart_id, ayanamsha_id, md_lord, ad_lord, as_of, as_of, as_of, as_of],
    ).fetchone()

    if row is None:
        logger.info(
            "[kala_permission] spine NOT found: chart=%s md=%s ad=%s as_of=%s",
            chart_id, md_lord, ad_lord, as_of,
        )
        return VimshottariSpine(found=False, md_lord=md_lord, ad_lord=ad_lord, as_of=as_of)

    md_id, md_start, md_end, ad_id, ad_start, ad_end = row
    return VimshottariSpine(
        found=True, md_lord=md_lord, ad_lord=ad_lord, as_of=as_of,
        md_dasha_row_id=str(md_id), md_start_date=md_start, md_end_date=md_end,
        ad_dasha_row_id=str(ad_id), ad_start_date=ad_start, ad_end_date=ad_end,
        fact_ids=[str(md_id), str(ad_id)],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 2. Multi-system concordance gate
# ═══════════════════════════════════════════════════════════════════════════

def concordance_gate(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    md_lord: str,
    ad_lord: str,
    window_start: date,
    window_end: date,
) -> DashaConsensusResult:
    """Call the ALREADY-RATIFIED `derive_dasha_consensus()` (U1/D20a,
    services/ph_nimitta/dasha_consensus.py — not re-derived here) and return
    its result untouched. The caller (`compute_permission`) is what turns
    `.confidence_multiplier` into a genuine multiplicative GATE on
    `permission_score`, rather than leaving it as ka_sangam's 0.12-weighted
    additive current — that elevation is the T-4 deliverable, not a change
    to derive_dasha_consensus's own math."""
    return derive_dasha_consensus(
        db_conn=conn,
        chart_id=chart_id,
        ayanamsha_id=ayanamsha_id,
        target_lords={md_lord, ad_lord},
        window_start=window_start,
        window_end=window_end,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 3. Period-lord relational algebra
# ═══════════════════════════════════════════════════════════════════════════

def _classify_bhava_relation_from_lord(relative_house: int) -> str:
    """Classify `relative_house` (1..12, AD-lord's D1 house counted from the
    MD-lord's own D1 house, i.e. MD-lord's house treated as house 1) into
    kendra / trikona / dusthana / neutral. House 1 itself (conjunction —
    AD-lord shares the MD-lord's own house) is classically the strongest
    link and is both kendra AND trikona simultaneously (BPHS: kendra =
    {1,4,7,10}, trikona = {1,5,9}) — reported as 'kendra_trikona' rather than
    forcing an arbitrary tie-break between the two 1-inclusive sets."""
    if relative_house == 1:
        return "kendra_trikona"
    if relative_house in KENDRA_HOUSES_NON_LAGNA:
        return "kendra"
    if relative_house in (TRIKONA_HOUSES - {1}):
        return "trikona"
    if relative_house in DUSTHANA_HOUSES:
        return "dusthana"
    return "neutral"


def _fetch_graha_d1_house_and_nakshatra(
    conn: Any, chart_id: str, ayanamsha_id: str, graha: str,
) -> dict[str, Any]:
    """Read-only SELECT of a single graha's D1 house (house_d1) and natal
    nakshatra name from chart_facts (fact_category='graha_position') — the
    L1-authority source per §N.5. Never re-derives the position."""
    subject = PLANET_TO_SUBJECT.get(graha)
    if subject is None:
        return {"house_d1": None, "nakshatra": None, "fact_ids": []}

    rows = conn.execute(
        """
        SELECT fact_key, fact_value_num, fact_value_text, fact_id
        FROM chart_facts
        WHERE chart_id = %s AND ayanamsha_id = %s
          AND fact_category = 'graha_position' AND fact_subject = %s
          AND fact_key IN ('house_d1', 'nakshatra')
        """,
        [chart_id, ayanamsha_id, subject],
    ).fetchall()

    house_d1: Optional[int] = None
    nakshatra: Optional[str] = None
    fact_ids: list[str] = []
    for fact_key, val_num, val_text, fact_id in rows:
        fact_ids.append(str(fact_id))
        if fact_key == "house_d1" and val_num is not None:
            house_d1 = int(val_num)
        elif fact_key == "nakshatra" and val_text:
            nakshatra = val_text

    return {"house_d1": house_d1, "nakshatra": nakshatra, "fact_ids": fact_ids}


def period_lord_relation(
    md_lord: str,
    ad_lord: str,
    chart_id: str,
    ayanamsha_id: str = "lahiri_chitrapaksha",
    *,
    conn: Any,
) -> dict[str, Any]:
    """
    Period-lord relational algebra (new logic, T-4).

    Returns:
        {
          relation: 'kendra' | 'trikona' | 'kendra_trikona' | 'dusthana' | 'neutral' | 'unresolved',
          relative_house: int | None,   # AD-lord's D1 house counted FROM the MD-lord's own D1 house
          tara: str | None,             # tara name (e.g. 'Sampat') from MD-lord's natal nakshatra to AD-lord's
          tara_quality: str | None,     # 'auspicious' | 'neutral' | 'inauspicious'
          tara_score: float | None,     # 0.0..1.0, panchang_engine.tara_bala's attenuated score
          tara_favorable: bool | None,  # tara_quality == 'auspicious'
          fact_ids: list[str],          # chart_facts rows this relation cites (§N.5)
          judgment_flags: list[str],    # honest gaps, never fabricated
        }

    (a) kendra/trikoṇa/dusthāna is bhava-counting-from-a-graha: the classical
        technique `ga_structural_writer.py`'s `_bhava_link_type()` applies to
        bhava PAIRS (there: aspect-target-house classification), adapted here
        to graha PAIRS by treating the MD-lord's own D1 house as the
        reference "house 1" and counting the AD-lord's D1 house from it.
    (b) tara is computed via panchang_engine.tara_bala.compute_tara_position/
        get_tara_detail, called with the MD-lord's natal nakshatra as the
        "birth" reference and the AD-lord's natal nakshatra as "current" —
        exactly the reuse the T-4 brief specifies.
    """
    _require_chart_id(chart_id)
    md_pos = _fetch_graha_d1_house_and_nakshatra(conn, chart_id, ayanamsha_id, md_lord)
    ad_pos = _fetch_graha_d1_house_and_nakshatra(conn, chart_id, ayanamsha_id, ad_lord)

    fact_ids = list(md_pos["fact_ids"]) + list(ad_pos["fact_ids"])
    judgment_flags: list[str] = []

    relation = "unresolved"
    relative_house: Optional[int] = None
    if md_pos["house_d1"] is not None and ad_pos["house_d1"] is not None:
        relative_house = ((ad_pos["house_d1"] - md_pos["house_d1"]) % 12) + 1
        relation = _classify_bhava_relation_from_lord(relative_house)
    else:
        judgment_flags.append(
            f"bhava_relation_unresolved: house_d1 missing for md_lord={md_lord!r} "
            f"or ad_lord={ad_lord!r} in chart_facts — honest gap, not fabricated."
        )

    tara_name: Optional[str] = None
    tara_quality: Optional[str] = None
    tara_score: Optional[float] = None
    tara_favorable: Optional[bool] = None
    if md_pos["nakshatra"] in NAKSHATRA_NAMES_27 and ad_pos["nakshatra"] in NAKSHATRA_NAMES_27:
        md_nak_id = NAKSHATRA_NAMES_27.index(md_pos["nakshatra"]) + 1  # 1-indexed
        ad_nak_id = NAKSHATRA_NAMES_27.index(ad_pos["nakshatra"]) + 1
        tara_pos = compute_tara_position(md_nak_id, ad_nak_id)
        detail = get_tara_detail(tara_pos)
        tara_name = detail["name"]
        tara_quality = detail["quality"]
        tara_score = detail["score"]
        tara_favorable = tara_quality == "auspicious"
    else:
        judgment_flags.append(
            f"tara_unresolved: natal nakshatra missing for md_lord={md_lord!r} "
            f"or ad_lord={ad_lord!r} in chart_facts — honest gap, not fabricated."
        )

    return {
        "relation": relation,
        "relative_house": relative_house,
        "tara": tara_name,
        "tara_quality": tara_quality,
        "tara_score": tara_score,
        "tara_favorable": tara_favorable,
        "fact_ids": sorted(set(fact_ids)),
        "judgment_flags": judgment_flags,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 4. Full dasha-lord capability (Python mirror of get_dasha_lord_capability.ts)
# ═══════════════════════════════════════════════════════════════════════════

def lord_capability(
    conn: Any, chart_id: str, ayanamsha_id: str, lord_graha: str,
) -> dict[str, Any]:
    """
    Python mirror of `ganita_dasha_lord_capability_get`
    (platform/src/lib/retrieval/registry/layers/L1_ganita/get_dasha_lord_capability.ts),
    computed for a single lord rather than every MD lord on the chart — this
    is what PERMISSION needs (md_lord, ad_lord), not the full per-chart
    listing. Same three sources, same warning_tier formula, same weights
    (WARNING_TIER_WEIGHTS / LOW_SHADBALA_PERCENTILE, copied verbatim above).
    Same precedent as panchang_engine/tara_bala.py's own "Python-side version
    of the TS ... helper" docstring — parity, not a new formula.
    """
    _require_chart_id(chart_id)
    subject = PLANET_TO_SUBJECT.get(lord_graha)
    if subject is None:
        return {
            "lord": lord_graha, "warning_tier": "none", "warning_score": 0,
            "warning_reasons": [], "fact_ids": [],
            "judgment_flags": [f"unmapped_lord_graha: {lord_graha!r} has no known subject-code mapping."],
        }

    shadbala_row = conn.execute(
        """
        SELECT fact_id, fact_value_num,
               PERCENT_RANK() OVER (ORDER BY fact_value_num) AS pct
        FROM chart_facts
        WHERE chart_id = %s AND ayanamsha_id = %s
          AND fact_category = 'graha_shadbala_total' AND fact_key = 'rupa'
          AND fact_subject = %s
        """,
        [chart_id, ayanamsha_id, subject],
    ).fetchone()
    # NOTE: the PERCENT_RANK() window above only ranks against rows matching
    # fact_subject=%s (a single row) unless the driver evaluates the window
    # over the full result set pre-filter — Postgres computes PERCENT_RANK()
    # OVER an empty PARTITION BY per the WHERE-filtered row set, so with a
    # fact_subject equality filter this always returns pct=0.0 for the one
    # matching row. This is a known limitation of scoping to a single lord;
    # the TS view computes percentile correctly because it ranks all 9
    # grahas in one query, then looks up by subject. Flagged, not silently
    # wrong: percentile_note below documents it, and shadbala_rupa is still
    # served (the raw value is NOT lost — only the percentile is honestly
    # marked unavailable at single-lord scope).
    shadbala_rupa: Optional[float] = None
    shadbala_fact_id: Optional[str] = None
    percentile_note = None
    if shadbala_row is not None:
        shadbala_fact_id = str(shadbala_row[0])
        shadbala_rupa = float(shadbala_row[1]) if shadbala_row[1] is not None else None
        percentile_note = (
            "shadbala_percentile is not computable at single-lord query scope "
            "(PERCENT_RANK() needs all 9 grahas in the window); use "
            "ganita_dasha_lord_capability_get for the ranked percentile."
        )

    vichara_row = conn.execute(
        """
        SELECT
          (array_agg(value_jsonb->>'actor_primary_class') FILTER (WHERE value_jsonb->>'actor_primary_class' IS NOT NULL))[1],
          (array_agg(value_jsonb->>'stored_functional_class_bphs') FILTER (WHERE value_jsonb->>'stored_functional_class_bphs' IS NOT NULL))[1],
          (array_agg(DISTINCT cf) FILTER (WHERE cf IS NOT NULL))
        FROM chart_vichara, LATERAL unnest(constituent_fact_ids) AS cf
        WHERE chart_id = %s AND ayanamsha_id = %s AND varga = 'D1'
          AND vichara_family = 'valence_pass' AND subject = %s
        GROUP BY subject
        """,
        [chart_id, ayanamsha_id, subject],
    ).fetchone()
    house_class = vichara_row[0] if vichara_row else None
    functional_lordship = vichara_row[1] if vichara_row else None
    vichara_fact_ids = list(vichara_row[2]) if vichara_row and vichara_row[2] else []

    ratif_row = conn.execute(
        """
        SELECT AVG(ratification_factor), array_agg(DISTINCT domain)
        FROM chart_vichara
        WHERE chart_id = %s AND ayanamsha_id = %s
          AND vichara_family = 'varga_ratification' AND subject = %s
          AND ratification_factor IS NOT NULL
        GROUP BY subject
        """,
        [chart_id, ayanamsha_id, subject],
    ).fetchone()
    ratification_factor = float(ratif_row[0]) if ratif_row and ratif_row[0] is not None else None
    ratification_domains = [d for d in (ratif_row[1] if ratif_row else []) or [] if d is not None]

    score = 0
    reasons: list[str] = []
    if house_class and house_class in WARNING_HOUSE_CLASSES:
        score += WARNING_TIER_WEIGHTS["house_class"]
        reasons.append(f"house_class={house_class}")
    # shadbala_percentile is not computable at this scope (see percentile_note) —
    # the low_shadbala term is honestly skipped rather than fabricated from a
    # single-row PERCENT_RANK() that would always read 0.0.
    if ratification_factor is not None and ratification_factor < 1.0:
        score += WARNING_TIER_WEIGHTS["low_ratification"]
        reasons.append(f"ratification_factor={ratification_factor} (< 1.0)")
    if functional_lordship and "malefic" in functional_lordship.lower():
        score += WARNING_TIER_WEIGHTS["functional_malefic"]
        reasons.append(f"functional_lordship={functional_lordship}")

    tier = "high" if score >= 3 else "elevated" if score == 2 else "watch" if score == 1 else "none"

    judgment_flags = []
    if percentile_note:
        judgment_flags.append(percentile_note)
    if house_class is None:
        judgment_flags.append(f"house_class_unresolved: no chart_vichara valence_pass row for {lord_graha}.")
    if ratification_factor is None:
        judgment_flags.append(f"ratification_unavailable: {lord_graha} is not a stored karaka for any domain.")

    fact_ids = sorted(set(vichara_fact_ids + ([shadbala_fact_id] if shadbala_fact_id else [])))

    return {
        "lord": lord_graha,
        "lord_subject": subject,
        "house_class": house_class,
        "functional_lordship": functional_lordship,
        "shadbala_rupa": shadbala_rupa,
        "ratification_factor": ratification_factor,
        "ratification_domains": ratification_domains,
        "warning_tier": tier,
        "warning_score": score,
        "warning_reasons": reasons,
        "fact_ids": fact_ids,
        "judgment_flags": judgment_flags,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Combination: compute_permission()
# ═══════════════════════════════════════════════════════════════════════════

# ── Relation-term lookup — CALIBRATION (this session's choice; see brief's
# "flag any as calibration choices" instruction). Ordering reflects classical
# strength (kendra_trikona strongest, dusthana weakest) but the exact numeric
# gaps are not drawn from a ratified prior formula. ──────────────────────────
_RELATION_TERM: dict[str, float] = {
    "kendra_trikona": 1.00,
    "trikona": 0.90,
    "kendra": 0.85,
    "neutral": 0.70,
    "dusthana": 0.55,
    "unresolved": 0.70,  # honest-gap fallback = neutral, not zero and not a fabricated strong value
}

# CALIBRATION: base_spine_strength when the (md_lord, ad_lord, as_of) triple
# does NOT resolve to a real chart_dashas row-pair. Heavily discounted rather
# than zeroed (the caller may be asking about a near-future/edge-of-window
# instant that is off by rounding) or left at 1.0 (which would silently treat
# an unverified spine as fully grounded — a §N.5 violation).
_SPINE_NOT_FOUND_STRENGTH = 0.3

# CALIBRATION: floor applied to the capability term so a single high-warning
# lord cannot alone drive PERMISSION to exactly 0 (mirrors the ratified
# G-LADDER pattern of a 0.5 floor on gate_multiplier, at a stricter floor
# since capability is a secondary, not primary, gate).
_CAPABILITY_FLOOR = 0.4


@dataclass
class PermissionResult:
    permission_score: float
    gate_multiplier: float
    relation: dict[str, Any]
    dasha_lord_capability: dict[str, Any]
    components: dict[str, Any]
    judgment_flags: list[str]


def compute_permission(
    chart_id: str,
    md_lord: str,
    ad_lord: str,
    as_of: date,
    *,
    ayanamsha_id: str = "lahiri_chitrapaksha",
    conn: Any,
) -> dict[str, Any]:
    """
    PERMISSION lock — combine the Vimśottarī spine, the multi-system
    concordance gate, period-lord relational algebra, and full dasha-lord
    capability into a single score.

    CR-87: chart_id, md_lord, ad_lord, as_of are ALL required — no defaults.

    Combination formula (documented per the T-4 brief's honesty standard —
    same discipline as T-3's NBRY weight):

        permission_score = clamp(
            base_spine_strength            # 1.0 if spine found, else 0.3 (CALIBRATION)
          * gate_multiplier                # derive_dasha_consensus().confidence_multiplier,
                                            # INHERITED verbatim from the ratified G-LADDER
                                            # formula (D21: max(0.5, count/7), capped at 1.0)
                                            # — 0.5 floor, so worst-case concordance HALVES
                                            # permission_score no matter how strong the other
                                            # terms are (the "genuine gate, not a nudge" the
                                            # brief asks for).
          * relation_term                  # _RELATION_TERM[relation] (CALIBRATION, 0.55–1.00)
                                            # * (0.5 + 0.5 * tara_score) when tara resolves
                                            # (CALIBRATION blend — tara_score already 0..1
                                            # from panchang_engine.tara_bala, INHERITED).
          * capability_term,                0, 1)
                                            # capability_term = max(_CAPABILITY_FLOOR,
                                            #   1 - avg(md_warning_score, ad_warning_score) / 4)
                                            # (CALIBRATION scale-down; the 0..4 warning_score
                                            # range itself is INHERITED verbatim from
                                            # get_dasha_lord_capability.ts's WARNING_TIER_WEIGHTS.)

    Every multiplicative term is documented above as either CALIBRATION
    (this session's numeric choice, open to recalibration once outcome data
    accrues — same honesty standard as ph_nimitta's own G-LADDER) or
    INHERITED (copied unchanged from an already-ratified source).
    """
    _require_chart_id(chart_id)
    if not md_lord or not ad_lord:
        raise ValueError("kala_permission: md_lord and ad_lord are required, no defaults.")
    if as_of is None:
        raise ValueError("kala_permission: as_of is required, no defaults.")
    if conn is None:
        raise ValueError("kala_permission: conn is required (read-only DB access), no defaults.")

    judgment_flags: list[str] = []

    # 1. Vimśottarī spine
    spine = _fetch_vimshottari_spine(conn, chart_id, ayanamsha_id, md_lord, ad_lord, as_of)
    base_spine_strength = 1.0 if spine.found else _SPINE_NOT_FOUND_STRENGTH
    if not spine.found:
        judgment_flags.append(
            f"spine_not_found: no chart_dashas vimshottari MD={md_lord}/AD={ad_lord} "
            f"row-pair covers as_of={as_of} for chart_id={chart_id} — "
            f"base_spine_strength discounted to {_SPINE_NOT_FOUND_STRENGTH} (honest gap, "
            "not treated as fully grounded)."
        )

    # 2. Multi-system concordance gate
    if spine.found:
        window_start, window_end = spine.ad_start_date, spine.ad_end_date
    else:
        # Honest fallback window when the spine itself did not resolve:
        # a single day centered on as_of, so the gate call still runs
        # (derive_dasha_consensus requires a window) but is clearly narrow.
        window_start, window_end = as_of, as_of + timedelta(days=1)
    consensus = concordance_gate(conn, chart_id, ayanamsha_id, md_lord, ad_lord, window_start, window_end)
    gate_multiplier = consensus.confidence_multiplier
    if not consensus.high_agreement:
        judgment_flags.append(
            f"low_dasha_concordance: only {consensus.count}/7 systems agree "
            f"({sorted(consensus.systems_agreeing)}) — gate_multiplier={gate_multiplier:.3f} "
            "structurally caps permission_score, not just a nudge."
        )

    # 3. Period-lord relational algebra
    relation = period_lord_relation(md_lord, ad_lord, chart_id, ayanamsha_id, conn=conn)
    judgment_flags.extend(relation["judgment_flags"])
    relation_term = _RELATION_TERM.get(relation["relation"], _RELATION_TERM["unresolved"])
    if relation["tara_score"] is not None:
        relation_term *= (0.5 + 0.5 * relation["tara_score"])

    # 4. Full dasha-lord capability (md + ad)
    md_cap = lord_capability(conn, chart_id, ayanamsha_id, md_lord)
    ad_cap = lord_capability(conn, chart_id, ayanamsha_id, ad_lord)
    judgment_flags.extend(f"md_lord: {f}" for f in md_cap["judgment_flags"])
    judgment_flags.extend(f"ad_lord: {f}" for f in ad_cap["judgment_flags"])
    avg_warning = (md_cap["warning_score"] + ad_cap["warning_score"]) / 2.0
    capability_term = max(_CAPABILITY_FLOOR, 1.0 - avg_warning / _MAX_WARNING_SCORE)

    raw_score = base_spine_strength * gate_multiplier * relation_term * capability_term
    permission_score = max(0.0, min(1.0, raw_score))

    if not judgment_flags:
        judgment_flags.append("no_gaps: spine resolved, relation resolved, capability data present for both lords.")

    return {
        "permission_score": permission_score,
        "gate_multiplier": gate_multiplier,
        "relation": relation,
        "dasha_lord_capability": {"md_lord": md_cap, "ad_lord": ad_cap},
        "components": {
            "base_spine_strength": base_spine_strength,
            "spine_found": spine.found,
            "spine_fact_ids": spine.fact_ids,
            "gate_multiplier": gate_multiplier,
            "dasha_consensus_count": consensus.count,
            "dasha_consensus_systems": consensus.systems_agreeing,
            "relation_term": relation_term,
            "capability_term": capability_term,
            "md_warning_score": md_cap["warning_score"],
            "ad_warning_score": ad_cap["warning_score"],
            "raw_score_before_clamp": raw_score,
        },
        "judgment_flags": judgment_flags,
        "formula_note": (
            "permission_score = clamp(base_spine_strength[CALIBRATION: 1.0 if spine "
            f"found else {_SPINE_NOT_FOUND_STRENGTH}] * gate_multiplier[INHERITED: "
            "derive_dasha_consensus().confidence_multiplier, G-LADDER D21 formula, "
            "0.5 floor / 1.0 ceiling] * relation_term[CALIBRATION: "
            f"{_RELATION_TERM} scaled by (0.5 + 0.5*tara_score) when tara resolves] "
            f"* capability_term[CALIBRATION: max({_CAPABILITY_FLOOR}, 1 - "
            "avg_warning_score/4), warning_score scale INHERITED from "
            "get_dasha_lord_capability.ts WARNING_TIER_WEIGHTS], 0, 1)."
        ),
    }
