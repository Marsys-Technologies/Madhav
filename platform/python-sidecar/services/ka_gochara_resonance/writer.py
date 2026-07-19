"""
writer.py — WriterBase subclass for ka_gochara_resonance (D-5 Lane G-1, L3 Kāla).

Registered as @register('ka_gochara_resonance') via the orchestrator adapter
at pipeline/orchestrator/writers/ka_gochara_resonance.py.

Populates `gochara_resonance_map`: for each of a small, deliberately-scoped
set of event_class values (from `brahma_event_ontology`'s 27-class ontology —
see GOCHARA_RESONANCE_MAP_SPEC.md §4 for why THESE 3 classes), emits target
rows across all 8 target_type values the schema supports:

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

logger = logging.getLogger(__name__)

FORMULA_VERSION = "ka_gochara_resonance_v1.0"
_CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

# ── Event-class scope (§ GOCHARA_RESONANCE_MAP_SPEC.md §4 documents why) ──────
# Chosen for richest bg_transit_rules (graha x house) coverage among the 27-
# class ontology: each karaka below has multiple favourable/unfavourable/
# double_transit bg_transit_rules rows whose primary_house lands inside the
# event class's own signature_model houses.
TARGET_EVENT_CLASSES: tuple[str, ...] = ("marriage", "major_gain", "career_advancement")

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
_KARAKA_FACT_SUBJECT: dict[str, str] = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
    "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
    "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN",
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
