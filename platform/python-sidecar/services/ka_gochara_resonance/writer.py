"""
writer.py — WriterBase subclass for ka_gochara_resonance (D-5 Lane G-1, L3 Kāla).

Registered as @register('ka_gochara_resonance') via the orchestrator adapter
at pipeline/orchestrator/writers/ka_gochara_resonance.py.

Populates `gochara_resonance_map`: for each of a small, deliberately-scoped
set of event_class values (from `brahma_event_ontology`'s 27-class ontology —
6 of them as of ṢAḌ-DARŚANA item 9; see GOCHARA_RESONANCE_MAP_SPEC.md §4 for
the original 3 and §4.2 for the health/adverse extension that closed DP-4),
emits target rows across the 11 target_type values the schema supports
(the original 8 plus the M-6 WP4 contract-extension 3 — see the M-6
section below):

  bhava / lord / karaka        — read straight off brahma_event_ontology's
                                  `signature_model` (BPHS-cited via that
                                  table's `citations` column, migration 388).
                                  uncited_extension=False — the citation
                                  covers exactly this signature claim.
  mechanism_node                — bg_transit_rules rows whose (graha, house)
                                  match the event class's karaka(s)/house(s).
                                  classical_citation copied verbatim from
                                  bg_transit_rules.classical_citation;
                                  source_rule_id set. uncited_extension=False.
  sensitive_degree / arudha /
  yoga_constituent /
  dasha_lord_portfolio          — this writer's OWN synthesis: it connects an
                                  event_class to a chart-specific L1 primitive
                                  (chart_facts sensitive-degree/arudha rows,
                                  ga_yoga_firings, chart_dashas MD lords) that
                                  is NOT itself keyed to that event_class in
                                  the source data. classical_citation is left
                                  NULL and uncited_extension=True for every
                                  row of these four target_types — B.10: never
                                  fabricate a citation string, and never dress
                                  an inferred linkage up as a classically-cited
                                  one just because the underlying PRIMITIVE
                                  happens to carry a real classical citation
                                  elsewhere (chart_facts.citation_human /
                                  ga_yoga_firings.citation_human are about the
                                  primitive itself, not about its relevance to
                                  THIS event_class).

Contract adherence (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - Uses ctx.db_conn (caller-owned) for all DB access
  - NEVER calls commit or rollback on ctx.db_conn
  - NEVER writes asset_throughput
  - Idempotency: per-chart delete-then-insert (§N.3) — DELETE FROM
    gochara_resonance_map WHERE chart_id = %s immediately before INSERT.

WP3c corrections (N-12 pre-approved honesty fixes, ruling sheet 2026-09-23;
GOCHARA_FAMILY_ELEVATION_PLAN_v2_1 §WP3c; implements the writer side of
WP1_CONTRACTS.md §2 / plan §5.3):

  R-1 sensitive_degree targets are kept ONLY for positive check results.
      chart_facts fact_value_text vocabulary (pinned from the sole producer,
      ga_writers/ga_sensitive_degree_writer.py:build_sensitive_degree_rows):
        mrityu_bhaga -> 'fired' | 'not_fired'
        gandanta     -> 'gandanta' | 'not_gandanta'
        kartari      -> 'papa_kartari' | 'shubha_kartari' | 'none'
        pushkara     -> 'pushkara' | 'not_pushkara'
      A negative-result row produces ZERO target rows (removed at the
      resonance layer, never carried as 'inapplicable' — F-19). Kept rows
      stay keyed by target_ref = the check fact_id (natural-key stability);
      the subject graha is recoverable downstream by joining chart_facts on
      that fact_id (fact_subject), and is additionally carried through the
      build report so the merge into the subject graha's own
      independence_group (plan §5.3 row 8) is auditable from WriterResult
      notes alone.
  R-2 arudha targets are sign-level INTERVALS. The fetch reads the
      fact_value_text of the stored fact_key='sign' row; the sibling
      longitude_sidereal is a cusp placeholder (every live value is exactly
      30*(sign-1) — F-20) and is NEVER read as a degree. target_ref stays
      the sign fact_id; the emitted row is typed sign-level via
      target_resolution_state + the build record (notes), and enrichment.py
      is deliberately untouched (it does not resolve arudha today — a
      documented gap, not something this packet may change).
  R-3 yoga_constituent targets are re-validated against live
      ga_yoga_firings (fired=true) at every build — the fetch already
      enforced fired=true; it now also selects constituent_fact_ids,
      constituent_planets and bhanga_active (§5.3 resolution inputs). The
      validated id set is pinned in WriterResult notes (the writer may not
      create tables; notes + log are its build record); run() additionally
      reads the prior build's yoga target_refs before DELETE so a yoga id
      that stopped firing (F-21, the ardhachandra/chatra case) surfaces as
      dropped_since_prior_build in the SAME build's notes — never silently.
  R-4 lord targets are resolved per WP1_CONTRACTS §2.2 item 3: whole-sign
      house-N sign from LAGNA (graha_sign_attributes.sign_num, 1-based),
      sign -> lord via the L0 reference_signs rulership table (missing or
      incomplete rulership -> 'unqualified'), lord -> its graha_position
      row (absent -> 'unavailable'; LAGNA fact absent -> 'unavailable').
      target_ref keeps the clean 'NL' form for natural-key stability; the
      resolution outcome lives in target_resolution_state (R-6) and the
      build notes.
  R-5 first source root retained, qualifier preserved. _build_lord_rows
      keeps the clean '10L' target_ref (the ontology's qualifier token is
      preserved in target_qualifier — 'afflicted' is the only qualifier in
      the seeded ontology today). Where a target resolves more than once
      (e.g. duplicate bg_transit_rules rows yielding the same
      mechanism_node ref), the table's UNIQUE key forces one row per
      (chart_id, event_class, target_type, target_ref): the FIRST root wins
      (setdefault) and every discard is counted — with kept-vs-discarded
      provenance — in the build notes (F-12: the retention was already
      first-wins; the honesty fix is that the discard is recorded, not
      silent).
  R-6 every emitted row stores target_resolution_state IN
      ('resolved','unavailable','unqualified') (WP1 §2.1 closed enum) —
      the honest null is stored, never inferred. Schema: migration
      platform/migrations/1080_nirmana_l3_gochara_resonance_target_resolution_state.sql
      (design artifact; NEVER applied to a real database from WP3c).

M-6 derived target rows (GOCHARA_RULING_SHEET_v2_0 §1 M-6; remainder brief
§4.4; WP1_CONTRACTS.md §2.2 items 9-11; Phaladīpikā Adh. XVII, translation
verified against corpus source OCR in.ernet.dli.2015.92117):

  gulika_mandi_distance         — PG220:C1 śl.26: N = sign distance from the
                                  8th-lord's occupied sign to Māndi's sign;
                                  the target is the rāśi N removed from
                                  Māndi; Saturn transit → death. Emitted ONLY
                                  for the classes the chapter names
                                  (bereavement, illness_acute — M6_EVENT_CLASSES),
                                  classically cited (uncited_extension=False),
                                  provisional weight 0.5 (WP8 owns values),
                                  target_qualifier carries the transit agent.
  yamakantaka_difference        — PG214:C1 śl.6-8 / PG217:C1 śl.14: whole-sign
                                  A−B differences over {lagna-lord, Sun,
                                  Yamakaṇṭaka, Māndi, 5th-star-lord} occupied
                                  signs; same class scoping, citation and
                                  qualifier discipline as above. Yamakaṇṭaka's
                                  own sign is the L1 sensitive_point_gulika_mandi
                                  [YAMAKANTAKA] fact (native-only persistence;
                                  no day-table fallback — see E-008).
  bhava_arudha                  — the ārūḍha of each house in the event
                                  class's signature_model, keyed by the clean
                                  symbolic ref BHAVA_ARUDHA_A{h} (natural-key
                                  stable, mirroring 'NL' for lords). Emitted
                                  for ALL classes with numeric houses; state
                                  'resolved' only when the arudha_pada sign
                                  fact for ARUDHA_A{h} exists and names a
                                  valid sign, else 'unavailable'.
                                  uncited_extension=True (own synthesis —
                                  the primitive is real but its linkage to
                                  THIS event_class is inferred), weight 0.6.

  Shared arithmetic lives in services.gochara_grammar.derived_points (single
  importable source for this writer AND the read-side resolver
  services.gochara_intensity.enrichment — no drift-guarded copies). The
  verses' navāṃśa refinement and trikona positions are named there and in
  WP1_CONTRACTS §2.2 but deliberately NOT emitted in v1: sign-grain operands
  cannot honestly anchor a 3°20′ span. The M-6 rows are stamped by their
  builder (operands in hand), following the arudha/yoga precedent; missing
  operand facts → 'unavailable', missing/incomplete reference_signs →
  'unqualified' (R-4 convention).
"""
from __future__ import annotations

import logging
import re as _re
from typing import Any, Iterable

from brahmagyan.graha_vocabulary import norm_graha
from services.gochara_grammar.derived_points import (
    M6_EVENT_CLASSES,
    MANDI_DISTANCE_AGENT,
    MANDI_DISTANCE_CITATION,
    MANDI_DISTANCE_REF,
    YAMAKANTAKA_FORMULAS,
    fifth_star_lord,
    sign_num_of,
)

logger = logging.getLogger(__name__)

# v2.1: M-6 derived target rows (gulika_mandi_distance, yamakantaka_difference,
# bhava_arudha) added per remainder brief §4.4 — emitted row set changes.
FORMULA_VERSION = "ka_gochara_resonance_v2.1"
_CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

# ── Event-class scope ────────────────────────────────────────────────────────
# W3.1: Extended to all 27 canonical event classes (2026-08-10).
#
# NOTE: We do NOT import SWEEP_EVENT_CLASSES for this — the gochara_grammar
# tuple covers only 6 (the SWEEP scope). The resonance writer's scope is now
# LARGER than the sweep scope by design: resonance map covers all 27 domains,
# while the sweep substep plan is gated by what's in the resonance map.
# I2: this file (ka_gochara_resonance/writer.py) is NOT in gochara_grammar/,
# so this change is legal and does not touch the frozen gochara_grammar module.
#
# The original 6-class scope (3 legacy + 3 health/adverse) is retained as the
# leading prefix so an existing chart's substep plan keeps its historical
# ordering. Order is stable and legacy-first.
_ALL_27_EVENT_CLASSES: tuple[str, ...] = (
    # Legacy 3 (richest bg_transit_rules coverage — GOCHARA_RESONANCE_MAP_SPEC.md §4)
    "marriage", "major_gain", "career_advancement",
    # Health/adverse extension (ṢAḌ-DARŚANA item 9, closes DP-4)
    "illness_acute", "chronic_onset", "surgery",
    # W3.1 extension — remaining 21 canonical classes
    "career_entry", "career_change", "career_setback", "business_launch",
    "education_milestone", "exam_outcome",
    "romantic_start", "separation",
    "childbirth", "parental_event", "bereavement",
    "major_loss", "property_acquisition",
    "relocation", "foreign_settlement",
    "spiritual_turn",
    "achievement_recognition", "financial_deception", "psychological_arc",
    "birth_anchor", "travel_event",
)
TARGET_EVENT_CLASSES: tuple[str, ...] = _ALL_27_EVENT_CLASSES

# ── Per-class coverage quality notes (I4 honest thin map documentation) ──────
# Documents the signature_model depth for each event class as seeded in
# brahma_event_ontology (migrations 388 + 456). Classes marked "provisional"
# inherited their signature_model from a sibling class; a dedicated Jyotish
# sourcing pass is an open item for those. This dict does NOT affect what rows
# get emitted — the writer always emits exactly what the ontology data supports,
# no more (I4). Sparse signature_models produce fewer rows, not fabricated ones.
COVERAGE_QUALITY_NOTES: dict[str, str] = {
    # ── Legacy 3 (non-provisional, dedicated citations) ──
    "marriage":
        "rich_model: houses 7,2 + lord 7L + karaka Venus; BPHS ch.7/Phaladeepika/Jaimini DK cited",
    "major_gain":
        "rich_model: houses 2,11 + lords 2L,11L + karakas Jupiter,Mercury; BPHS ch.2,11 cited",
    "career_advancement":
        "rich_model: houses 10,11 + lords 10L,11L + karaka Sun; BPHS ch.10/Phaladeepika cited",
    # ── Health/adverse extension (non-provisional, dedicated citations) ──
    "illness_acute":
        "rich_model: houses 6,8 + lords 6L,8L + karakas Mars,Saturn; BPHS ch.6/Phaladeepika cited",
    "chronic_onset":
        "rich_model: houses 6,8 + lords 6L,8L + karaka Saturn; BPHS ch.6,8/Sade-Sati rules cited",
    "surgery":
        "rich_model: houses 6,8 + lords 6L,8L + karaka Mars; BPHS ch.6/Phaladeepika cited",
    # ── W3.1 extension ──
    "career_entry":
        "rich_model: houses 10,6,1 + lords 10L,6L + karakas Sun,Saturn; BPHS ch.10/Phaladeepika cited",
    "career_change":
        "rich_model: houses 10,3,9 + lord 10L + karaka Rahu; BPHS ch.10/Rahu transit rules cited",
    "career_setback":
        "rich_model: houses 10,6,8,12 + lord 10L afflicted + karakas Saturn,Rahu; BPHS dusthana cited. "
        "Note: lords field contains 'afflicted' qualifier text — the qualifier is PRESERVED on the "
        "emitted row as target_qualifier='afflicted' (R-5/N-12, F-12); target_ref stays the clean '10L'",
    "business_launch":
        "rich_model: houses 7,10,11 + lords 7L,10L,11L + karakas Mercury,Jupiter; BPHS ch.7,10,11 cited",
    "education_milestone":
        "rich_model: houses 4,5,9 + lords 4L,5L,9L + karakas Mercury,Jupiter; "
        "BPHS ch.4,5,9/Jaimini Sutram cited",
    "exam_outcome":
        "moderate_model: houses 5,9 + lord 5L + karaka Mercury; BPHS ch.5 cited",
    "romantic_start":
        "moderate_model: houses 5,7 + lords 5L,7L + karaka Venus; BPHS ch.5,7 cited. "
        "self_report_non_discriminating=true (evidence_requirements); rows emitted honestly, "
        "calibration layer must weight accordingly",
    "separation":
        "rich_model: houses 6,8,12 + lord 7L afflicted + karakas Rahu,Saturn,Mars; "
        "BPHS ch.7 vivaha-vighna cited. Note: '7L afflicted' qualifier preserved as "
        "target_qualifier (R-5/N-12) same as career_setback",
    "childbirth":
        "moderate_model: houses 5,1 + lord 5L + karaka Jupiter; BPHS ch.5/Jaimini putra-karaka cited",
    "parental_event":
        "rich_model: houses 4,9 + lords 4L,9L + karakas Moon,Sun; BPHS ch.4,9 cited",
    "bereavement":
        "rich_model: houses 8,12,2 + lords 8L + maraka lords (2L/7L) + karakas Saturn,Ketu; "
        "BPHS ch.8,2 cited. Note: 'maraka lords (2L/7L)' is tokenized by _build_lord_rows "
        "using _LORD_TOKEN_RE — emits 8L, 2L, 7L as separate rows (B4 fix)",
    "major_loss":
        "rich_model: houses 2,11,12 + lords 2L/11L afflicted + 12L + karakas Saturn,Rahu; "
        "BPHS ch.12 cited. Note: compound lord tokens ('2L/11L afflicted') tokenize to 2L + 11L, "
        "each carrying target_qualifier='afflicted' (R-5/N-12)",
    "property_acquisition":
        "moderate_model: house 4 + lord 4L + karaka Mars; BPHS ch.4 cited",
    "relocation":
        "rich_model: houses 4,3,12 + lords 4L,3L + karakas Moon,Rahu; BPHS ch.4,12 cited",
    "foreign_settlement":
        "rich_model: houses 12,9,7 + lords 12L,9L + karaka Rahu; BPHS ch.12 cited",
    "spiritual_turn":
        "rich_model: houses 9,12,5 + lords 9L,12L + karakas Jupiter,Ketu; "
        "BPHS ch.9,12/Jaimini Sutram cited. "
        "self_report_non_discriminating=true (evidence_requirements); rows emitted honestly",
    # ── 5 provisional classes (migration 456, signature_model inherited from sibling) ──
    "achievement_recognition":
        "provisional_model (inherited from career_advancement): houses 10,11,5 + lords 10L,11L,5L "
        "+ karakas Sun,Mercury; BPHS ch.10/Phaladeepika inherited — pending dedicated Jyotish sourcing",
    "financial_deception":
        "provisional_model (inherited from major_loss): houses 2,11,12 + lords 2L/11L afflicted + "
        "12L active + karakas Rahu,Saturn; BPHS ch.12 inherited — pending dedicated sourcing. "
        "self_report_non_discriminating=true",
    "psychological_arc":
        "provisional_model (inherited from chronic_onset): houses 1,6,12 + lords 1L,6L "
        "+ karakas Moon,Mercury,Saturn; BPHS ch.1 inherited — pending dedicated sourcing. "
        "self_report_non_discriminating=true",
    "birth_anchor":
        "thin_model (provisional, no predecessor): house 1 + lord 1L + karaka Sun only; "
        "no dasha_rules or transit_triggers in ontology (birth is the chart epoch, not a "
        "predictable configuration). Emits bhava/lord/karaka rows only; mechanism/sensitive/"
        "arudha/yoga rows will be minimal. kill_switch epoch_tautology: excluded from lambda_e "
        "scoring — emitting resonance rows is honest documentation of natal significators, "
        "not a timing claim",
    "travel_event":
        "provisional_model (inherited from foreign_settlement): houses 3,9,12 + lords 3L,9L "
        "+ karaka Moon; BPHS ch.12 inherited — pending dedicated sourcing. Lighter-weight "
        "than foreign_settlement (single trip vs durable residency chain)",
}

# rule_type -> classical-prior weight (documented in GOCHARA_RESONANCE_MAP_SPEC.md §2)
_MECHANISM_WEIGHTS: dict[str, float] = {
    "favourable": 1.0,
    "unfavourable": -1.0,
    "vedha": 0.3,
    "double_transit": 0.75,
}

# karaka (Title Case planet name, as used in brahma_event_ontology.signature_model)
# -> the fact_subject code chart_facts uses for that graha (§0 confirmed live:
# Sun/Moon are spelled out, the rest are 3-letter PyJHora-inherited codes).
# Values sourced from the graha SSoT (brahmagyan/graha_vocabulary) rather
# than hardcoded literals — ADHIṢṬHĀNA Lane A2 (found via the full-tree
# census; not one of the originally-enumerated retirement targets).
_KARAKA_FACT_SUBJECT: dict[str, str] = {
    name: norm_graha(name)
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
}

_SENSITIVE_DEGREE_KEYS = ("mrityu_bhaga", "gandanta", "kartari", "pushkara")

# R-1 (N-12/F-19): positive-result vocabulary per fact_key, pinned from the
# sole producer of these rows (ga_sensitive_degree_writer.py
# build_sensitive_degree_rows:714-735). ONLY these (fact_key, value) pairs
# become sensitive_degree targets; every other value — the pinned negatives
# (not_fired, not_gandanta, not_pushkara, none) or anything unexpected —
# produces ZERO target rows and is counted in the build notes.
_POSITIVE_SENSITIVE_VALUES: dict[str, frozenset] = {
    "mrityu_bhaga": frozenset({"fired"}),
    "gandanta": frozenset({"gandanta"}),
    "kartari": frozenset({"papa_kartari", "shubha_kartari"}),
    "pushkara": frozenset({"pushkara"}),
}
_NEGATIVE_SENSITIVE_VALUES = frozenset({"not_fired", "not_gandanta", "not_pushkara", "none"})

# R-2/R-4: the 12 sign names, 1-based position in this tuple = sign_num.
_SIGNS: tuple[str, ...] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# R-4: fixed classical whole-sign rulership (BPHS Ch.1) — the build-time
# fallback IDENTICAL to brahmagyan/chart_reader_v4.py:109-112 SIGN_LORD
# (kept as a literal copy, not an import, mirroring that file's own
# drift-guarded copy of probe_p2_tracer.py; a test drift guard below keeps
# this copy honest). The PRIMARY source is the L0 reference_signs table —
# when it is unreachable or incomplete the writer does NOT silently fall
# back: every lord row is stamped 'unqualified' (rulership row missing),
# per WP1_CONTRACTS §2.2 item 3.
_CLASSICAL_SIGN_LORDS: dict[int, str] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

# R-5: lord qualifier detection. 'afflicted' is the only qualifier token in
# the seeded brahma_event_ontology signature_models (career_setback,
# separation, major_loss); unknown future qualifiers stay visible in the
# source ontology row and extend this pattern explicitly — no silent
# generality is claimed.
_LORD_QUALIFIER_RE: "_re.Pattern[str]" = _re.compile(r"\bafflicted\b", _re.IGNORECASE)

# R-6: closed enum (WP1_CONTRACTS §2.1).
_TARGET_RESOLUTION_STATES: tuple[str, ...] = ("resolved", "unavailable", "unqualified")

# B4: lord tokenizer — extracts clean NL refs (e.g. '10L') from compound
# or qualified strings (e.g. '10L afflicted', 'maraka lords (2L/7L)').
# See effect commit for _build_lord_rows usage.
_LORD_TOKEN_RE: "_re.Pattern[str]" = _re.compile(r'\d+L')


# ── Pure row-building helpers (DB-free, unit-testable) ───────────────────────

def _parse_house_ints(houses: Iterable[Any]) -> list[int]:
    """signature_model['houses'] entries that are plain numeric strings -> ints.
    Non-numeric entries (e.g. free-text lord glosses) are dropped, not guessed at."""
    out: list[int] = []
    for h in houses or []:
        s = str(h).strip()
        if s.isdigit():
            out.append(int(s))
    return sorted(set(out))


def _base_row(event_class: str, target_type: str, target_ref: str, weight: float,
              citation: str | None, uncited_extension: bool,
              source_rule_id: int | None = None,
              target_resolution_state: str = "resolved",
              target_qualifier: str | None = None) -> dict:
    assert target_resolution_state in _TARGET_RESOLUTION_STATES, target_resolution_state
    return {
        "event_class": event_class,
        "target_type": target_type,
        "target_ref": target_ref,
        "weight": weight,
        "classical_citation": citation,
        "uncited_extension": uncited_extension,
        "source_rule_id": source_rule_id,
        "target_resolution_state": target_resolution_state,
        "target_qualifier": target_qualifier,
    }


def _build_bhava_rows(event_class: str, houses: Iterable[Any], citation: str | None) -> list[dict]:
    return [
        _base_row(event_class, "bhava", str(h), 1.0, citation, False)
        for h in _parse_house_ints(houses)
    ]


def _build_lord_rows(event_class: str, lords: Iterable[Any], citation: str | None) -> list[dict]:
    seen: set[str] = set()
    rows = []
    for l in lords or []:
        ref = str(l).strip()
        if not ref:
            continue
        tokens = _LORD_TOKEN_RE.findall(ref)
        if not tokens:
            # No clean lord refs found (pure descriptive text) — skip
            continue
        # R-5 (N-12/F-12): preserve the qualifier instead of stripping it.
        # target_ref keeps the clean 'NL' form so the natural key
        # (chart_id, event_class, 'lord', 'NL') stays stable; the qualifier
        # rides the R-6-era target_qualifier column.
        qualifier = "afflicted" if _LORD_QUALIFIER_RE.search(ref) else None
        for token in tokens:
            if token in seen:
                continue
            seen.add(token)
            rows.append(_base_row(event_class, "lord", token, 1.0, citation, False,
                                  target_qualifier=qualifier))
    return rows


def _build_karaka_rows(event_class: str, karakas: Iterable[Any], citation: str | None) -> list[dict]:
    seen: set[str] = set()
    rows = []
    for k in karakas or []:
        ref = str(k).strip()
        if not ref or ref in seen:
            continue
        seen.add(ref)
        rows.append(_base_row(event_class, "karaka", ref, 1.0, citation, False))
    return rows


def _build_mechanism_rows(event_class: str, transit_rule_rows: Iterable[dict]) -> list[dict]:
    """transit_rule_rows: rows already fetched from bg_transit_rules
    (id, rule_type, graha, primary_house, classical_citation)."""
    rows = []
    for r in transit_rule_rows or []:
        graha = str(r["graha"]).strip().lower()
        rule_type = str(r["rule_type"])
        house = r["primary_house"]
        target_ref = f"{graha}:{rule_type}:h{house}"
        weight = _MECHANISM_WEIGHTS.get(rule_type, 0.5)
        rows.append(_base_row(
            event_class, "mechanism_node", target_ref, weight,
            r.get("classical_citation"), False, source_rule_id=r.get("id"),
        ))
    return rows


def _build_sensitive_degree_rows(
    event_class: str, fact_rows: Iterable[dict], report: dict | None = None,
) -> list[dict]:
    """fact_rows: chart_facts rows (fact_id, fact_subject, fact_key,
    fact_value_text) for sensitive_degree_check. Own extension —
    classical_citation NULL, uncited_extension=True (§ module docstring).

    R-1 (N-12/F-19): keep ONLY positive check results (see
    _POSITIVE_SENSITIVE_VALUES). A negative-result row — or a row whose
    value is anything outside the pinned positive vocabulary — produces
    ZERO target rows: the row is removed here, at the resonance layer,
    never carried as 'inapplicable'. Kept rows carry an internal
    `_fact_subject` key (the check row's fact_subject) so the build-time
    resolution pass can verify the subject graha's graha_position row
    exists; run() pops it before INSERT (it is not a table column). The
    subject graha is also recoverable downstream by joining chart_facts on
    target_ref (= fact_id) — the merge into the subject graha's own
    independence_group (plan §5.3 row 8) is realized downstream; this
    writer's duty is emitting the target keyed to the subject so the merge
    is possible, and recording the kept (fact_id, subject) pairs in the
    build notes."""
    kept: list[dict] = []
    for r in fact_rows or []:
        key = str(r.get("fact_key") or "")
        value = str(r.get("fact_value_text") or "").strip()
        if value not in _POSITIVE_SENSITIVE_VALUES.get(key, frozenset()):
            # Not a positive result — no target at all (F-19).
            if report is not None:
                if value in _NEGATIVE_SENSITIVE_VALUES:
                    report["dropped_negative"] += 1
                else:
                    report["dropped_unknown_value"] += 1
                    logger.warning(
                        "[ka_gochara_resonance] sensitive_degree_check row %s has "
                        "unexpected fact_value_text %r (fact_key=%s) — dropped, "
                        "not carried as a target",
                        r.get("fact_id"), value, key,
                    )
            continue
        row = _base_row(event_class, "sensitive_degree", str(r["fact_id"]), 0.5, None, True)
        row["_fact_subject"] = str(r.get("fact_subject") or "")
        kept.append(row)
        if report is not None:
            report["kept"] += 1
            report["kept_subjects"].add(row["_fact_subject"])
    return kept


def _build_arudha_rows(
    event_class: str, fact_rows: Iterable[dict], report: dict | None = None,
) -> list[dict]:
    """R-2 (N-12/F-20): arudha targets are sign-level INTERVALS. The stored
    sibling longitude_sidereal is a cusp placeholder (every live value is
    exactly 30*(sign-1)) and is never read as a degree. target_ref stays
    the fact_id of the stored fact_key='sign' row (natural-key stability);
    the sign VALUE the interval is derived from is fetched alongside
    (fact_value_text) and validated here: a row whose sign value is absent
    or not one of the 12 sign names cannot yield a sign span and is
    emitted with target_resolution_state='unavailable' (the honest null,
    stored by R-6), never silently resolved to the cusp placeholder."""
    rows = []
    for r in fact_rows or []:
        sign_value = str(r.get("fact_value_text") or "").strip()
        state = "resolved" if sign_value in _SIGNS else "unavailable"
        if report is not None:
            report["rows"] += 1
            if state != "resolved":
                report["invalid_sign_value"] += 1
                logger.warning(
                    "[ka_gochara_resonance] arudha sign fact %s has missing/unexpected "
                    "fact_value_text %r — row emitted as 'unavailable', never resolved "
                    "to the cusp placeholder longitude",
                    r.get("fact_id"), sign_value,
                )
        rows.append(_base_row(event_class, "arudha", str(r["fact_id"]), 0.6, None, True,
                              target_resolution_state=state))
    return rows


def _build_bhava_arudha_rows(
    event_class: str, house_ints: Iterable[int], arudha_fact_rows: Iterable[dict],
    report: dict | None = None,
) -> list[dict]:
    """M-6 (WP1_CONTRACTS §2.2 item 11): the ārūḍha of each house in the
    event class's signature_model, keyed by the clean symbolic ref
    BHAVA_ARUDHA_A{h} (natural-key stable — the ref survives a chart_facts
    rebuild, unlike a fact_id). The resolution operand is the SAME
    arudha_pada sign fact the R-2 `arudha` rows are built from (fetched once
    per event class and passed in here): state is 'resolved' only when that
    fact exists for ARUDHA_A{h} and names one of the 12 signs, else
    'unavailable' — the honest null, stored (R-6), never guessed from the
    cusp-placeholder longitude. Own synthesis: classical_citation NULL,
    uncited_extension=True; weight 0.6 mirrors the `arudha` rows."""
    sign_by_subject = {
        str(r.get("fact_subject") or ""): str(r.get("fact_value_text") or "").strip()
        for r in arudha_fact_rows or []
    }
    rows = []
    for h in house_ints or []:
        sign_value = sign_by_subject.get(f"ARUDHA_A{h}", "")
        state = "resolved" if sign_value in _SIGNS else "unavailable"
        if report is not None:
            report["rows"] += 1
            if state != "resolved":
                report["unavailable"] += 1
        rows.append(_base_row(event_class, "bhava_arudha", f"BHAVA_ARUDHA_A{h}",
                              0.6, None, True, target_resolution_state=state))
    return rows


def _build_m6_derived_rows(
    event_class: str, m6_ctx: dict, report: dict | None = None,
) -> list[dict]:
    """M-6 (WP1_CONTRACTS §2.2 items 9-10): Gulika/Māndi sign-distance and
    Yamakaṇṭaka-difference targets, emitted ONLY for M6_EVENT_CLASSES
    (bereavement, illness_acute) — the classes Phaladīpikā Adh. XVII names.
    Sign-grain arithmetic is imported from services.gochara_grammar.
    derived_points (single source shared with enrichment; the verses' degree
    figures, navāṃśa refinement and trikona positions are documented there
    and deliberately NOT emitted — sign-grain operands cannot honestly
    anchor them). Rows are stamped here, where the operands are in hand
    (arudha/yoga precedent): missing operand fact → 'unavailable';
    missing/incomplete reference_signs rulership → 'unqualified' (R-4).

    m6_ctx keys: lagna_sign_num (int|None), sign_lords ({1..12: lord}|None),
    graha_sign_nums ({fact_subject: int}), gulika_mandi_signs
    ({GULIKA|MANDI|YAMAKANTAKA: sign name}), moon_nakshatra_id (int|None)."""
    rows: list[dict] = []
    if event_class not in M6_EVENT_CLASSES:
        return rows

    lagna_sign_num = m6_ctx.get("lagna_sign_num")
    sign_lords = m6_ctx.get("sign_lords")
    graha_sign_nums = m6_ctx.get("graha_sign_nums") or {}
    gm_signs = m6_ctx.get("gulika_mandi_signs") or {}
    moon_nakshatra_id = m6_ctx.get("moon_nakshatra_id")

    def _graha_sign_num(graha_name: str) -> int | None:
        subject = _KARAKA_FACT_SUBJECT.get(graha_name)
        value = graha_sign_nums.get(subject) if subject else None
        return int(value) if value is not None else None

    def _house_lord_occupied_sign_num(house_n: int) -> tuple[int | None, str]:
        """Lord of whole-sign house N → that graha's occupied sign.
        Returns (sign_num|None, state_when_missing)."""
        if lagna_sign_num is None:
            return None, "unavailable"
        house_sign_num = ((int(lagna_sign_num) - 1) + (house_n - 1)) % 12 + 1
        if not sign_lords or house_sign_num not in sign_lords:
            return None, "unqualified"
        sign_num = _graha_sign_num(sign_lords[house_sign_num])
        return sign_num, "unavailable"

    def _operand_sign_num(role: str) -> tuple[int | None, str]:
        if role == "lagna_lord":
            return _house_lord_occupied_sign_num(1)
        if role == "yamakantaka":
            return sign_num_of(gm_signs.get("YAMAKANTAKA", "")), "unavailable"
        if role == "mandi":
            return sign_num_of(gm_signs.get("MANDI", "")), "unavailable"
        if role == "fifth_star_lord":
            if moon_nakshatra_id is None:
                return None, "unavailable"
            return _graha_sign_num(fifth_star_lord(moon_nakshatra_id)), "unavailable"
        # 'Sun' and any other plain graha role
        return _graha_sign_num(role), "unavailable"

    def _state(*operand_states: tuple[int | None, str]) -> str:
        missing = [st for sign_num, st in operand_states if sign_num is None]
        if not missing:
            return "resolved"
        return "unqualified" if "unqualified" in missing else "unavailable"

    # ── PG220:C1 śl.26: Māndi sign-distance from the 8th lord ──
    eighth_lord = _house_lord_occupied_sign_num(8)
    mandi = _operand_sign_num("mandi")
    state = _state(eighth_lord, mandi)
    rows.append(_base_row(
        event_class, "gulika_mandi_distance", MANDI_DISTANCE_REF, 0.5,
        MANDI_DISTANCE_CITATION, False,
        target_resolution_state=state,
        target_qualifier=f"agent:{MANDI_DISTANCE_AGENT}",
    ))
    if report is not None:
        report["rows"] += 1
        report[state] += 1

    # ── PG214:C1 śl.6-8 / PG217:C1 śl.14: Yamakaṇṭaka differences ──
    for formula in YAMAKANTAKA_FORMULAS:
        minuend = _operand_sign_num(formula["minuend"])
        subtrahend = _operand_sign_num(formula["subtrahend"])
        state = _state(minuend, subtrahend)
        rows.append(_base_row(
            event_class, "yamakantaka_difference", formula["ref"], 0.5,
            formula["citation"], False,
            target_resolution_state=state,
            target_qualifier=f"agent:{formula['agent']}",
        ))
        if report is not None:
            report["rows"] += 1
            report[state] += 1
    return rows


def _build_yoga_rows(
    event_class: str, firing_rows: Iterable[dict], report: dict | None = None,
) -> list[dict]:
    """R-3 (N-12): every emitted row was validated against a LIVE
    ga_yoga_firings row (fired=true) at THIS build — the fetch enforces it.
    constituent_fact_ids / constituent_planets / bhanga_active are fetched
    alongside (plan §5.3 resolution inputs); bhanga_active=true is carried
    as a qualifier, not a weight (WP1 §2.2 item 7). The validated id set is
    pinned in the build report (→ WriterResult notes, the writer's build
    record)."""
    rows = []
    for r in firing_rows or []:
        yoga_id = str(r["yoga_canonical_id"])
        qualifier = "bhanga_active" if r.get("bhanga_active") is True else None
        rows.append(_base_row(event_class, "yoga_constituent", yoga_id, 0.7, None, True,
                              target_qualifier=qualifier))
        if report is not None:
            constituent_fact_ids = r.get("constituent_fact_ids") or []
            report["validated_ids"].add(yoga_id)
            report["constituents"][yoga_id] = len(list(constituent_fact_ids))
    return rows


def _build_dasha_portfolio_rows(event_class: str, dasha_rows: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    rows = []
    for r in dasha_rows or []:
        lord = str(r["lord_graha"])
        if lord in seen:
            continue
        seen.add(lord)
        rows.append(_base_row(event_class, "dasha_lord_portfolio", lord, 0.8, None, True))
    return rows


def build_resonance_rows(
    event_class: str,
    *,
    houses: Iterable[Any] = (),
    lords: Iterable[Any] = (),
    karakas: Iterable[Any] = (),
    ontology_citation: str | None = None,
    transit_rule_rows: Iterable[dict] = (),
    sensitive_fact_rows: Iterable[dict] = (),
    arudha_fact_rows: Iterable[dict] = (),
    yoga_firing_rows: Iterable[dict] = (),
    dasha_rows: Iterable[dict] = (),
    report: dict | None = None,
) -> list[dict]:
    """Pure assembly of all target-type rows for one event_class. DB-free —
    callers fetch the raw rows first, this function only shapes them.
    Dedup is scoped within each target_type (the table's UNIQUE key is
    (chart_id, event_class, target_type, target_ref)).

    `report` (optional, R-1/R-2/R-3/R-5): a dict this function records the
    honest build record into — sensitive-degree drop counts, arudha
    interval validation, validated yoga ids, and (R-5/F-12) every
    duplicate-root discard with kept-vs-discarded provenance. Callers that
    don't need the record (unit tests, mirrors) omit it; row output is
    identical either way.

    M-6: also emits bhava_arudha rows — one per numeric house in `houses`,
    resolved against the same `arudha_fact_rows` the R-2 `arudha` targets
    are built from. The M-6 gulika_mandi_distance / yamakantaka_difference
    rows are NOT built here: they need per-chart operands the caller
    (run()) assembles once per chart — see _build_m6_derived_rows."""
    if report is not None:
        report.setdefault("sensitive_degree", {"kept": 0, "dropped_negative": 0,
                                               "dropped_unknown_value": 0, "kept_subjects": set()})
        report.setdefault("arudha", {"rows": 0, "invalid_sign_value": 0})
        report.setdefault("bhava_arudha", {"rows": 0, "unavailable": 0})
        report.setdefault("yoga_constituent", {"validated_ids": set(), "constituents": {}})
        report.setdefault("roots", {"discarded": 0, "details": []})

    house_ints = _parse_house_ints(houses)

    rows: list[dict] = []
    rows += _build_bhava_rows(event_class, houses, ontology_citation)
    rows += _build_lord_rows(event_class, lords, ontology_citation)
    rows += _build_karaka_rows(event_class, karakas, ontology_citation)
    rows += _build_mechanism_rows(event_class, transit_rule_rows)
    rows += _build_sensitive_degree_rows(
        event_class, sensitive_fact_rows, report=report.get("sensitive_degree") if report else None)
    rows += _build_arudha_rows(
        event_class, arudha_fact_rows, report=report.get("arudha") if report else None)
    rows += _build_bhava_arudha_rows(
        event_class, house_ints, arudha_fact_rows,
        report=report.get("bhava_arudha") if report else None)
    rows += _build_yoga_rows(
        event_class, yoga_firing_rows, report=report.get("yoga_constituent") if report else None)
    rows += _build_dasha_portfolio_rows(event_class, dasha_rows)

    # Belt-and-braces de-dup on the actual UNIQUE key (target_type, target_ref)
    # within this event_class, in case two source queries yield the same key.
    # R-5 (F-12): the table's UNIQUE key physically admits one row per key,
    # so the FIRST root wins (setdefault) — but the discard is recorded in
    # the report (count + kept-vs-discarded provenance), never silent.
    deduped: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row["target_type"], row["target_ref"])
        prior = deduped.get(key)
        if prior is None:
            deduped[key] = row
            continue
        if report is not None:
            roots = report["roots"]
            roots["discarded"] += 1
            if len(roots["details"]) < 25:  # capped: notes stay compact
                roots["details"].append({
                    "target_type": key[0],
                    "target_ref": key[1],
                    "kept_source_rule_id": prior.get("source_rule_id"),
                    "discarded_source_rule_id": row.get("source_rule_id"),
                    "kept_weight": prior.get("weight"),
                    "discarded_weight": row.get("weight"),
                    "kept_qualifier": prior.get("target_qualifier"),
                    "discarded_qualifier": row.get("target_qualifier"),
                })
    return list(deduped.values())


# ── DB fetch helpers ──────────────────────────────────────────────────────────

_FETCH_ONTOLOGY_SQL = """
SELECT event_class_id, signature_model, citations
FROM brahma_event_ontology
WHERE event_class_id = %s
"""

_FETCH_TRANSIT_RULES_SQL = """
SELECT id, rule_type, graha, primary_house, classical_citation
FROM bg_transit_rules
WHERE lower(graha) = ANY(%s) AND primary_house = ANY(%s)
ORDER BY graha, rule_type, primary_house
"""

_FETCH_SENSITIVE_FACTS_SQL = """
SELECT fact_id, fact_subject, fact_key, fact_value_text
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'sensitive_degree_check'
  AND fact_subject = ANY(%s) AND fact_key = ANY(%s)
"""

_FETCH_ARUDHA_FACTS_SQL = """
SELECT fact_id, fact_subject, fact_value_text
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'arudha_pada'
  AND fact_subject = ANY(%s) AND fact_key = 'sign'
"""

_FETCH_YOGA_FIRINGS_SQL = """
SELECT DISTINCT yoga_canonical_id, constituent_fact_ids, constituent_planets, bhanga_active
FROM ga_yoga_firings
WHERE chart_id = %s AND ayanamsha_id = %s AND fired = true
  AND (
    EXISTS (
      SELECT 1 FROM jsonb_array_elements(constituent_houses) elem
      WHERE (elem::text)::int = ANY(%s::int[])
    )
    OR EXISTS (
      SELECT 1 FROM jsonb_array_elements_text(constituent_planets) elem
      WHERE elem = ANY(%s::text[])
    )
  )
"""

_FETCH_DASHA_ROWS_SQL = """
SELECT DISTINCT lord_graha
FROM chart_dashas
WHERE chart_id = %s AND ayanamsha_id = %s AND system_id = 'vimshottari' AND level_n = 1
  AND lower(lord_graha) = ANY(%s)
"""

# ── R-3/R-4 build-time validation fetches ─────────────────────────────────────
# R-4: LAGNA's whole-sign sign_num (1-based, per ga_positions_writer.py) —
# the anchor for lord and bhava resolution.
_FETCH_LAGNA_SIGN_SQL = """
SELECT fact_value_num
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_sign_attributes'
  AND fact_subject = 'LAGNA' AND fact_key = 'sign_num'
"""

# R-4: the L0 classical rulership table (WP1_CONTRACTS §2.2 item 3: "an L0
# reference row is cited by the writer"). Unreachable or incomplete -> the
# writer does NOT fall back silently: every lord row is 'unqualified'.
_FETCH_SIGN_LORDS_SQL = """
SELECT sign_id, lord FROM reference_signs ORDER BY sign_id
"""

# R-1/R-4: which graha_position longitude rows actually exist for this chart
# (karaka / dasha_lord_portfolio / sensitive-degree subject verification).
_FETCH_PRESENT_POSITIONS_SQL = """
SELECT DISTINCT fact_subject
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s
  AND fact_category = 'graha_position' AND fact_key = 'longitude_sidereal'
"""

# ── M-6 per-chart operand fetches (derived transit targets) ──────────────────
# Occupied sign (1-based sign_num) of every graha — the operand for the
# lagna-lord / 8th-lord / Sun / 5th-star-lord roles. LAGNA's own row is
# fetched separately by _FETCH_LAGNA_SIGN_SQL (R-4); this query does not
# exclude it, but only graha subjects are read from the result.
_FETCH_GRAHA_SIGN_NUMS_SQL = """
SELECT fact_subject, fact_value_num
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_sign_attributes'
  AND fact_key = 'sign_num'
"""

# Māndi / Gulika / Yamakaṇṭaka occupied signs (sign NAME text) — produced by
# ga_writers/ga_sensitive_writer.py's sensitive_point_gulika_mandi rows
# (Yamakaṇṭaka persisted native-only; no day-table fallback — E-008).
_FETCH_GULIKA_MANDI_SIGNS_SQL = """
SELECT fact_subject, fact_value_text
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'sensitive_point_gulika_mandi'
  AND fact_key = 'sign'
"""

# Natal Moon nakṣatra number (1..27) — operand for the 5th-star-lord role
# (PG214:C1 śl.8). ga_panchanga_writer._emit_nakshatra_moon writes this
# per-ayanamsha (it sits under the ayanamsha-dependent categories).
_FETCH_MOON_NAKSHATRA_SQL = """
SELECT fact_value_num
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'panchanga_nakshatra_moon'
  AND fact_subject = 'NAKSHATRA_MOON_BIRTH' AND fact_key = 'number'
"""

# R-3: the prior build's yoga target_refs, read BEFORE the DELETE so a yoga
# id that stopped firing (F-21) surfaces as dropped_since_prior_build in
# THIS build's notes — never silently.
_FETCH_PRIOR_YOGA_REFS_SQL = """
SELECT DISTINCT target_ref
FROM gochara_resonance_map
WHERE chart_id = %s AND target_type = 'yoga_constituent'
"""

_DELETE_SQL = "DELETE FROM gochara_resonance_map WHERE chart_id = %s"

_INSERT_SQL = """
INSERT INTO gochara_resonance_map (
    chart_id, event_class, target_type, target_ref, weight,
    classical_citation, uncited_extension, source_rule_id,
    target_resolution_state, target_qualifier
) VALUES (%(chart_id)s, %(event_class)s, %(target_type)s, %(target_ref)s, %(weight)s,
          %(classical_citation)s, %(uncited_extension)s, %(source_rule_id)s,
          %(target_resolution_state)s, %(target_qualifier)s)
ON CONFLICT (chart_id, event_class, target_type, target_ref) DO NOTHING
"""


def _fetch_event_class_rows(conn, chart_id: str, event_class: str,
                            report: dict | None = None) -> list[dict]:
    """Runs the full fetch sequence for one event_class and returns the
    shaped rows (chart_id + formula fields NOT yet attached — the caller adds
    those before INSERT). Isolated so the writer's run() stays thin."""
    import psycopg.rows

    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_ONTOLOGY_SQL, (event_class,))
        ontology = cur.fetchone()

    if not ontology:
        logger.warning("[ka_gochara_resonance] no brahma_event_ontology row for %s — skipping", event_class)
        return []

    sig = ontology["signature_model"] or {}
    houses = sig.get("houses") or []
    lords = sig.get("lords") or []
    karakas = sig.get("karakas") or []
    citations = ontology.get("citations") or []
    ontology_citation = "; ".join(citations) if citations else None

    house_ints = _parse_house_ints(houses)
    karakas_lower = sorted({str(k).strip().lower() for k in karakas if k})

    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_TRANSIT_RULES_SQL, (karakas_lower, house_ints))
        transit_rule_rows = cur.fetchall()

    fact_subjects = sorted({
        _KARAKA_FACT_SUBJECT[k] for k in karakas if k in _KARAKA_FACT_SUBJECT
    })
    sensitive_fact_rows: list[dict] = []
    if fact_subjects:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(_FETCH_SENSITIVE_FACTS_SQL,
                        (chart_id, _CANONICAL_AYANAMSHA, fact_subjects, list(_SENSITIVE_DEGREE_KEYS)))
            sensitive_fact_rows = cur.fetchall()

    arudha_fact_rows: list[dict] = []
    if house_ints:
        arudha_subjects = [f"ARUDHA_A{h}" for h in house_ints]
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(_FETCH_ARUDHA_FACTS_SQL, (chart_id, _CANONICAL_AYANAMSHA, arudha_subjects))
            arudha_fact_rows = cur.fetchall()

    yoga_firing_rows: list[dict] = []
    if house_ints or karakas_lower:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(_FETCH_YOGA_FIRINGS_SQL,
                        (chart_id, _CANONICAL_AYANAMSHA, house_ints, karakas_lower))
            yoga_firing_rows = cur.fetchall()

    dasha_rows: list[dict] = []
    if karakas_lower:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(_FETCH_DASHA_ROWS_SQL, (chart_id, _CANONICAL_AYANAMSHA, karakas_lower))
            dasha_rows = cur.fetchall()

    return build_resonance_rows(
        event_class,
        houses=houses, lords=lords, karakas=karakas,
        ontology_citation=ontology_citation,
        transit_rule_rows=transit_rule_rows,
        sensitive_fact_rows=sensitive_fact_rows,
        arudha_fact_rows=arudha_fact_rows,
        yoga_firing_rows=yoga_firing_rows,
        dasha_rows=dasha_rows,
        report=report,
    )


# ── R-3/R-4 build-time target-resolution validation ───────────────────────────

def _fetch_chart_resolution_context(conn, chart_id: str) -> dict:
    """Per-chart inputs the target-resolution pass verifies against
    (WP1_CONTRACTS §2.2). All reads are best-effort: any absence is carried
    as an honest state on the affected rows, never an exception.
    Returns {lagna_sign_num (1-based int|None), sign_lords ({1..12: lord}
    or None when the L0 table is unreachable/incomplete), present_subjects
    (set of chart_facts graha_position fact_subjects with a longitude)}."""
    import psycopg.rows

    lagna_sign_num: int | None = None
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_LAGNA_SIGN_SQL, (chart_id, _CANONICAL_AYANAMSHA))
        row = cur.fetchone()
    if row is not None and row.get("fact_value_num") is not None:
        lagna_sign_num = int(row["fact_value_num"])

    sign_lords: dict[int, str] | None = None
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(_FETCH_SIGN_LORDS_SQL)
            rows = cur.fetchall()
        lords = {int(r["sign_id"]): str(r["lord"]) for r in rows
                 if r.get("sign_id") is not None and r.get("lord")}
        if len(lords) == 12:
            sign_lords = lords
    except Exception as exc:  # noqa: BLE001 — absence is data, not a crash
        logger.warning("[ka_gochara_resonance] reference_signs unreadable (%s) — "
                       "lord rows will be stamped 'unqualified'", exc)

    present_subjects: set[str] = set()
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_PRESENT_POSITIONS_SQL, (chart_id, _CANONICAL_AYANAMSHA))
        present_subjects = {str(r["fact_subject"]) for r in cur.fetchall()
                            if r.get("fact_subject")}

    return {
        "lagna_sign_num": lagna_sign_num,
        "sign_lords": sign_lords,
        "present_subjects": present_subjects,
    }


def _fetch_m6_context(conn, chart_id: str) -> dict:
    """M-6 per-chart operands for the derived transit targets (WP1_CONTRACTS
    §2.2 items 9-10). Same best-effort discipline as
    _fetch_chart_resolution_context: every absence is carried as an honest
    state on the affected rows by _build_m6_derived_rows, never an
    exception. Returns {graha_sign_nums {fact_subject: int},
    gulika_mandi_signs {subject: sign name}, moon_nakshatra_id (int|None)}."""
    import psycopg.rows

    graha_sign_nums: dict[str, int] = {}
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_GRAHA_SIGN_NUMS_SQL, (chart_id, _CANONICAL_AYANAMSHA))
        for r in cur.fetchall():
            if r.get("fact_subject") and r.get("fact_value_num") is not None:
                graha_sign_nums[str(r["fact_subject"])] = int(r["fact_value_num"])

    gulika_mandi_signs: dict[str, str] = {}
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_GULIKA_MANDI_SIGNS_SQL, (chart_id, _CANONICAL_AYANAMSHA))
        for r in cur.fetchall():
            if r.get("fact_subject") and r.get("fact_value_text"):
                gulika_mandi_signs[str(r["fact_subject"])] = str(r["fact_value_text"]).strip()

    moon_nakshatra_id: int | None = None
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(_FETCH_MOON_NAKSHATRA_SQL, (chart_id, _CANONICAL_AYANAMSHA))
        row = cur.fetchone()
    if row is not None and row.get("fact_value_num") is not None:
        moon_nakshatra_id = int(row["fact_value_num"])

    return {
        "graha_sign_nums": graha_sign_nums,
        "gulika_mandi_signs": gulika_mandi_signs,
        "moon_nakshatra_id": moon_nakshatra_id,
    }


def _resolve_lord_ref(ref: str, ctx: dict) -> tuple[str, str | None]:
    """R-4 (WP1_CONTRACTS §2.2 item 3): resolve a clean 'NL' lord ref.
    Returns (target_resolution_state, resolved_lord_graha|None).
      lagna sign fact absent                    -> 'unavailable'
      rulership row missing (L0 table gap)      -> 'unqualified'
      lord graha_position row absent            -> 'unavailable'
      chain complete                            -> 'resolved'"""
    match = _re.fullmatch(r"(\d+)L", ref)
    if not match or ctx["lagna_sign_num"] is None:
        return "unavailable", None
    house_n = int(match.group(1))
    if not 1 <= house_n <= 12:
        return "unavailable", None
    # whole-sign house-N sign: LAGNA is 1-based; offset adds N-1 signs.
    sign_num = ((int(ctx["lagna_sign_num"]) - 1) + (house_n - 1)) % 12 + 1
    sign_lords = ctx.get("sign_lords")
    if not sign_lords or sign_num not in sign_lords:
        return "unqualified", None
    lord = sign_lords[sign_num]
    subject = _KARAKA_FACT_SUBJECT.get(lord)
    if subject is None or subject not in ctx["present_subjects"]:
        return "unavailable", None
    return "resolved", lord


def _stamp_target_resolution(all_rows: list[dict], ctx: dict,
                             lord_report: dict | None = None) -> None:
    """R-1/R-4/R-6: verify resolvability at build time and stamp every row's
    target_resolution_state. Rows are never dropped here — an unresolvable
    target is stored WITH its honest state (the honest null is stored, never
    inferred), except R-1 negative sensitive rows which were already removed
    at the row-building layer (there is nothing to store a state on)."""
    for row in all_rows:
        tt = row["target_type"]
        if tt == "lord":
            state, lord = _resolve_lord_ref(row["target_ref"], ctx)
            row["target_resolution_state"] = state
            if lord_report is not None:
                lord_report[state] += 1
                if state != "resolved":
                    lord_report[state + "_refs"].append(row["target_ref"])
                else:
                    lord_report["resolved_map"][row["target_ref"]] = lord
        elif tt == "bhava":
            # A bhava interval needs the LAGNA anchor; the interval span is
            # realized downstream (M-5: whole-sign, never a cusp point).
            if ctx["lagna_sign_num"] is None:
                row["target_resolution_state"] = "unavailable"
        elif tt in ("karaka", "dasha_lord_portfolio"):
            subject = _KARAKA_FACT_SUBJECT.get(str(row["target_ref"]))
            if subject is None or subject not in ctx["present_subjects"]:
                row["target_resolution_state"] = "unavailable"
        elif tt == "sensitive_degree":
            # R-1 kept only positive checks; the target resolves to the
            # subject graha's OWN graha_position degree (plan §5.3 row 8) —
            # honest only if that row exists.
            subject = row.pop("_fact_subject", "")
            if not subject or subject not in ctx["present_subjects"]:
                row["target_resolution_state"] = "unavailable"
        # arudha (R-2) and yoga_constituent (R-3) were stamped by their
        # builders, where the cited input was in hand; mechanism_node rows
        # name a live bg_transit_rules row (the operand wiring itself) and
        # stay 'resolved' — the M-4 operand audit is a later packet.
        # bhava_arudha / gulika_mandi_distance / yamakantaka_difference
        # (M-6) were likewise stamped by their builders, where the chart's
        # arudha/sensitive/graha-sign operands were in hand.


def _build_wp3c_notes(report: dict, all_rows: list[dict],
                      prior_yoga_refs: list[str]) -> str:
    """The writer's build record (the writer may not create tables; the
    WriterResult notes + log ARE its honest record — R-3). JSON, key-sorted,
    deterministic, compact."""
    import json

    yoga_ids = sorted({r["target_ref"] for r in all_rows
                       if r["target_type"] == "yoga_constituent"})
    states: dict[str, int] = {s: 0 for s in _TARGET_RESOLUTION_STATES}
    for r in all_rows:
        states[r["target_resolution_state"]] += 1

    sensitive = report["sensitive_degree"]
    lord = report["lord"]
    # Tests that build a hand-made report omit the M-6 sections; default
    # them honestly rather than KeyError (run() always passes them).
    bhava_arudha = report.get("bhava_arudha", {"rows": 0, "unavailable": 0})
    m6_derived = report.get("m6_derived",
                            {"rows": 0, "resolved": 0, "unavailable": 0, "unqualified": 0})
    notes = {
        "wp3c": "N-12 R-1..R-6",
        "event_classes": len(TARGET_EVENT_CLASSES),
        "rows": len(all_rows),
        "target_resolution_state_counts": states,
        "sensitive_degree": {
            "positive_kept": sensitive["kept"],
            "negative_dropped_zero_rows": sensitive["dropped_negative"],
            "unknown_value_dropped_zero_rows": sensitive["dropped_unknown_value"],
            "kept_subjects": sorted(sensitive["kept_subjects"]),
        },
        "arudha": {
            "rows": report["arudha"]["rows"],
            "sign_level_interval": True,
            "cusp_placeholder_longitude_never_read": True,
            "invalid_sign_value_unavailable": report["arudha"]["invalid_sign_value"],
        },
        "bhava_arudha": {
            "rows": bhava_arudha["rows"],
            "unavailable": bhava_arudha["unavailable"],
            "symbolic_ref": "BHAVA_ARUDHA_A{h}",
            "uncited_extension": True,
        },
        "m6_derived": {
            "event_classes": list(M6_EVENT_CLASSES),
            "rows": m6_derived["rows"],
            "resolved": m6_derived["resolved"],
            "unavailable": m6_derived["unavailable"],
            "unqualified": m6_derived["unqualified"],
            "sign_grain_only": True,
            "navamsa_refinement_not_emitted": True,
            "trikona_positions_not_emitted": True,
            "weight_provisional_pending_wp8": True,
        },
        "yoga_constituent": {
            "validated_ids": yoga_ids,
            "constituent_fact_counts": {k: report["yoga_constituent"]["constituents"][k]
                                        for k in sorted(report["yoga_constituent"]["constituents"])},
            "dropped_since_prior_build": sorted(set(prior_yoga_refs) - set(yoga_ids)),
        },
        "lord": {
            "rulership_source": "reference_signs" if lord.get("rulership_available")
                                else "unavailable_unqualified",
            "resolved": lord["resolved"],
            "unavailable": lord["unavailable"],
            "unqualified": lord["unqualified"],
            "unavailable_refs": sorted(lord["unavailable_refs"]),
            "unqualified_refs": sorted(lord["unqualified_refs"]),
            "resolved_lords": {k: lord["resolved_map"][k] for k in sorted(lord["resolved_map"])},
        },
        "roots": {
            "discarded_duplicates": report["roots"]["discarded"],
            "first_root_retained": True,
            "details": report["roots"]["details"],
        },
    }
    return json.dumps(notes, sort_keys=True)


def _build_writer_class():
    from pipeline.orchestrator.writers import WriterBase, ContextSpec, WriterResult, register

    @register("ka_gochara_resonance")
    class KaGocharaResonanceWriter(WriterBase):
        """Per-chart resonance-map writer. Rows: target sets across 8
        target_types for TARGET_EVENT_CLASSES. NEVER commits ctx.db_conn."""

        asset_id = "ka_gochara_resonance"

        def run(self, ctx: ContextSpec) -> WriterResult:
            conn = ctx.db_conn
            chart_id = ctx.config["chart_id"]

            if ctx.dry_run:
                logger.info("[ka_gochara_resonance] dry_run=True — skipping")
                return WriterResult(asset_id=self.asset_id, rows_inserted=0, notes="dry_run=True")

            # R-3: capture the prior build's yoga target set BEFORE any
            # DELETE, so an id that no longer fires surfaces in THIS build's
            # notes (dropped_since_prior_build) — never silently.
            import psycopg.rows
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(_FETCH_PRIOR_YOGA_REFS_SQL, (chart_id,))
                prior_yoga_refs = [str(r["target_ref"]) for r in cur.fetchall()]

            # R-4/R-6: per-chart resolution inputs verified at build time.
            resolution_ctx = _fetch_chart_resolution_context(conn, chart_id)

            report: dict = {
                "lord": {
                    "resolved": 0, "unavailable": 0, "unqualified": 0,
                    "unavailable_refs": [], "unqualified_refs": [],
                    "resolved_map": {},
                    "rulership_available": resolution_ctx["sign_lords"] is not None,
                },
                "m6_derived": {"rows": 0, "resolved": 0, "unavailable": 0, "unqualified": 0},
            }

            all_rows: list[dict] = []
            missing_event_classes: list[str] = []
            for event_class in TARGET_EVENT_CLASSES:
                class_rows = _fetch_event_class_rows(conn, chart_id, event_class, report=report)
                if not class_rows:
                    missing_event_classes.append(event_class)
                    continue
                for row in class_rows:
                    row["chart_id"] = chart_id
                all_rows.extend(class_rows)

            if missing_event_classes:
                return WriterResult(
                    asset_id=self.asset_id, rows_inserted=0,
                    notes=(
                        "incomplete event-class coverage for "
                        + ",".join(missing_event_classes)
                        + "; prior partition preserved"
                    ),
                )

            # M-6: derived transit targets (Gulika/Māndi sign-distance,
            # Yamakaṇṭaka difference) — per-chart operands fetched once,
            # rows built only for the classes Phaladīpikā Adh. XVII names.
            # Stamped by the builder (operands in hand); placed AFTER the
            # coverage gate so an aborted build never writes partial data.
            m6_ctx = dict(resolution_ctx)
            m6_ctx.update(_fetch_m6_context(conn, chart_id))
            for event_class in M6_EVENT_CLASSES:
                derived_rows = _build_m6_derived_rows(
                    event_class, m6_ctx, report=report["m6_derived"])
                for row in derived_rows:
                    row["chart_id"] = chart_id
                all_rows.extend(derived_rows)

            # R-1/R-4/R-6: verify resolvability and stamp the honest state on
            # every row (also pops the internal _fact_subject helper key).
            _stamp_target_resolution(all_rows, resolution_ctx, report["lord"])

            notes = _build_wp3c_notes(report, all_rows, prior_yoga_refs)

            # Build and validate the complete candidate before replacement.
            # An honest-empty upstream result must not erase the prior servable
            # chart partition.  The orchestrator still owns atomic rollback for
            # any later INSERT failure.
            with conn.cursor() as cur:
                cur.execute(_DELETE_SQL, (chart_id,))

            with conn.cursor() as cur:
                cur.executemany(_INSERT_SQL, all_rows)

            logger.info("[ka_gochara_resonance] %d resonance-map rows for chart %s across %d event classes",
                        len(all_rows), chart_id, len(TARGET_EVENT_CLASSES))
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=len(all_rows),
                notes=notes,
            )

    return KaGocharaResonanceWriter


KaGocharaResonanceWriter = _build_writer_class()
