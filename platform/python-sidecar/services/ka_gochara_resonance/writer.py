"""
writer.py — WriterBase subclass for ka_gochara_resonance (D-5 Lane G-1, L3 Kāla).

Registered as @register('ka_gochara_resonance') via the orchestrator adapter
at pipeline/orchestrator/writers/ka_gochara_resonance.py.

Populates `gochara_resonance_map`: for each of a small, deliberately-scoped
set of event_class values (from `brahma_event_ontology`'s 27-class ontology —
6 of them as of ṢAḌ-DARŚANA item 9; see GOCHARA_RESONANCE_MAP_SPEC.md §4 for
the original 3 and §4.2 for the health/adverse extension that closed DP-4),
emits target rows across all 8 target_type values the schema supports:

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
"""
from __future__ import annotations

import logging
from typing import Any, Iterable

from brahmagyan.graha_vocabulary import norm_graha

logger = logging.getLogger(__name__)

FORMULA_VERSION = "ka_gochara_resonance_v2.0"
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
        "Note: lords field contains 'afflicted' qualifier text — qualifier tokens are dropped by "
        "_build_lord_rows (non-numeric tokens stripped), only clean lord refs emit rows.",
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
        "BPHS ch.7 vivaha-vighna cited. Note: '7L afflicted' qualifier dropped same as career_setback",
    "childbirth":
        "moderate_model: houses 5,1 + lord 5L + karaka Jupiter; BPHS ch.5/Jaimini putra-karaka cited",
    "parental_event":
        "rich_model: houses 4,9 + lords 4L,9L + karakas Moon,Sun; BPHS ch.4,9 cited",
    "bereavement":
        "rich_model: houses 8,12,2 + lords 8L + maraka lords (2L/7L) + karakas Saturn,Ketu; "
        "BPHS ch.8,2 cited. Note: 'maraka lords (2L/7L)' is a compound gloss — "
        "_build_lord_rows emits '8L' and 'maraka lords (2L/7L)' as-is (non-empty strings); "
        "the latter is a descriptive token, not a clean lord ref",
    "major_loss":
        "rich_model: houses 2,11,12 + lords 2L/11L afflicted + 12L + karakas Saturn,Rahu; "
        "BPHS ch.12 cited. Note: compound lord tokens ('2L/11L afflicted') passed through as-is",
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
              source_rule_id: int | None = None) -> dict:
    return {
        "event_class": event_class,
        "target_type": target_type,
        "target_ref": target_ref,
        "weight": weight,
        "classical_citation": citation,
        "uncited_extension": uncited_extension,
        "source_rule_id": source_rule_id,
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
        if not ref or ref in seen:
            continue
        seen.add(ref)
        rows.append(_base_row(event_class, "lord", ref, 1.0, citation, False))
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


def _build_sensitive_degree_rows(event_class: str, fact_rows: Iterable[dict]) -> list[dict]:
    """fact_rows: chart_facts rows (fact_id, fact_subject, fact_key) for
    sensitive_degree_check. Own extension — classical_citation NULL,
    uncited_extension=True (§ module docstring)."""
    return [
        _base_row(event_class, "sensitive_degree", str(r["fact_id"]), 0.5, None, True)
        for r in fact_rows or []
    ]


def _build_arudha_rows(event_class: str, fact_rows: Iterable[dict]) -> list[dict]:
    return [
        _base_row(event_class, "arudha", str(r["fact_id"]), 0.6, None, True)
        for r in fact_rows or []
    ]


def _build_yoga_rows(event_class: str, firing_rows: Iterable[dict]) -> list[dict]:
    return [
        _base_row(event_class, "yoga_constituent", str(r["yoga_canonical_id"]), 0.7, None, True)
        for r in firing_rows or []
    ]


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
) -> list[dict]:
    """Pure assembly of all target-type rows for one event_class. DB-free —
    callers fetch the raw rows first, this function only shapes them.
    Dedup is scoped within each target_type (the table's UNIQUE key is
    (chart_id, event_class, target_type, target_ref))."""
    rows: list[dict] = []
    rows += _build_bhava_rows(event_class, houses, ontology_citation)
    rows += _build_lord_rows(event_class, lords, ontology_citation)
    rows += _build_karaka_rows(event_class, karakas, ontology_citation)
    rows += _build_mechanism_rows(event_class, transit_rule_rows)
    rows += _build_sensitive_degree_rows(event_class, sensitive_fact_rows)
    rows += _build_arudha_rows(event_class, arudha_fact_rows)
    rows += _build_yoga_rows(event_class, yoga_firing_rows)
    rows += _build_dasha_portfolio_rows(event_class, dasha_rows)

    # Belt-and-braces de-dup on the actual UNIQUE key (target_type, target_ref)
    # within this event_class, in case two source queries yield the same key.
    deduped: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row["target_type"], row["target_ref"])
        deduped.setdefault(key, row)
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
SELECT fact_id, fact_subject, fact_key
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'sensitive_degree_check'
  AND fact_subject = ANY(%s) AND fact_key = ANY(%s)
"""

_FETCH_ARUDHA_FACTS_SQL = """
SELECT fact_id, fact_subject
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'arudha_pada'
  AND fact_subject = ANY(%s) AND fact_key = 'sign'
"""

_FETCH_YOGA_FIRINGS_SQL = """
SELECT DISTINCT yoga_canonical_id
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

_DELETE_SQL = "DELETE FROM gochara_resonance_map WHERE chart_id = %s"

_INSERT_SQL = """
INSERT INTO gochara_resonance_map (
    chart_id, event_class, target_type, target_ref, weight,
    classical_citation, uncited_extension, source_rule_id
) VALUES (%(chart_id)s, %(event_class)s, %(target_type)s, %(target_ref)s, %(weight)s,
          %(classical_citation)s, %(uncited_extension)s, %(source_rule_id)s)
ON CONFLICT (chart_id, event_class, target_type, target_ref) DO NOTHING
"""


def _fetch_event_class_rows(conn, chart_id: str, event_class: str) -> list[dict]:
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
    )


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

            # Idempotency: per-chart delete-then-insert (§N.3)
            with conn.cursor() as cur:
                cur.execute(_DELETE_SQL, (chart_id,))

            all_rows: list[dict] = []
            for event_class in TARGET_EVENT_CLASSES:
                class_rows = _fetch_event_class_rows(conn, chart_id, event_class)
                for row in class_rows:
                    row["chart_id"] = chart_id
                all_rows.extend(class_rows)

            if not all_rows:
                return WriterResult(
                    asset_id=self.asset_id, rows_inserted=0,
                    notes="No rows built — check brahma_event_ontology/bg_transit_rules coverage",
                )

            with conn.cursor() as cur:
                cur.executemany(_INSERT_SQL, all_rows)

            logger.info("[ka_gochara_resonance] %d resonance-map rows for chart %s across %d event classes",
                        len(all_rows), chart_id, len(TARGET_EVENT_CLASSES))
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=len(all_rows),
                notes=f"event_classes={list(TARGET_EVENT_CLASSES)}",
            )

    return KaGocharaResonanceWriter


KaGocharaResonanceWriter = _build_writer_class()
