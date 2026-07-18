"""
ka_avadhi — Period Dossiers (L3 Kāla)
========================================
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or closes ctx.db_conn — orchestrator owns the transaction.
NEVER writes to bodha_* tables.

For each chart, reads chart_dashas (MD + AD levels across all systems) and
produces a dossier row per period with:
  - lord_condition_fact_refs: refs (fact_ids only) to chart_facts describing
    the lord's sign, nakshatra, dispositor, D9 placement, karaka roles.
    Never restates computed values — refs only (BA trap-1 guard).
  - activated_pratijna_ids: bodha_pratijna IDs whose domain maps to the lord's
    natural significations and the period overlaps within the dossier window.
  - sublord_modulation: {graha, strength_factor, note} based on the AD lord.

BA-P5A Step 2. DAG: ka_yojaka → ka_avadhi.
"""
from __future__ import annotations

import json
import logging
from datetime import date

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

FORMULA_VERSION = "ka_avadhi_v1.0"

# Dasha systems available in chart_dashas
_DASHA_SYSTEMS = (
    "vimshottari", "yogini", "ashtottari",
    "chara", "naisargika", "mudda", "kalachakra",
)

# Classical graha → natural domain mapping (for pratijna linkage)
_GRAHA_DOMAINS: dict[str, list[str]] = {
    "Sun":     ["dharma", "career", "authority", "health"],
    "Moon":    ["mind", "relationship", "home", "health"],
    "Mars":    ["career", "property", "health", "disputes"],
    "Mercury": ["education", "commerce", "communication", "wealth"],
    "Jupiter": ["dharma", "wealth", "children", "education"],
    "Venus":   ["relationship", "wealth", "creativity", "luxury"],
    "Saturn":  ["karma", "career", "longevity", "health"],
    "Rahu":    ["karma", "foreign", "technology", "unusual"],
    "Ketu":    ["moksha", "spirituality", "loss", "liberation"],
}

# CR-110 fix (D-4a Lane A-0): kala_avadhi carries NO ayanamsha_id column at all —
# it is a single-ayanamsha table by design (same canonical scope as the
# pratijna/fact_refs queries below, which already pin 'lahiri_chitrapaksha').
# chart_dashas, however, pools ALL 5 ayanamsha computations (~9,200 MD/AD rows
# each per chart — see services/ka_temporal/date_resolver.py's own docstring).
# _FETCH_MD_SQL / _FETCH_AD_SQL previously carried NO ayanamsha_id filter, so
# every ayanamsha's variant of a given (system_id, level_n, lord_graha) period
# — each with a slightly different sidereal boundary (day-level drift, e.g.
# Mercury MD ending 2027-08-11 under true_chitra vs 2027-08-18 under lahiri) —
# was fetched and inserted as if it were the single canonical period. The
# INSERT's ON CONFLICT key (chart_id, system_id, level_n, period_start) could
# not de-duplicate these because their period_start values genuinely differ by
# a few days, so distinct ayanamsha variants landed as separate, silently
# conflicting rows in the SAME served spine — this is CR-110's double
# dasha-spine bug (confirmed live: two Mercury MD rows for chart 482012f1,
# ending 2027-08-11 and 2027-08-18, sourced from chart_dashas.ayanamsha_id
# 'true_chitra' vs the other four ayanamshas respectively). Fix: scope both
# fetches to the canonical ayanamsha, exactly like every other query in this
# writer already does.
_CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

_FETCH_MD_SQL = """
SELECT d.chart_id, d.system_id, d.lord_graha,
       d.start_date AS period_start,
       d.end_date   AS period_end,
       1 AS level_n
FROM chart_dashas d
WHERE d.chart_id = %s AND d.level_n = 1 AND d.system_id = ANY(%s)
  AND d.ayanamsha_id = %s
ORDER BY d.system_id, d.start_date
"""

_FETCH_AD_SQL = """
SELECT d.chart_id, d.system_id, d.lord_graha,
       d.start_date AS period_start,
       d.end_date   AS period_end,
       2 AS level_n,
       p.lord_graha AS parent_lord_graha
FROM chart_dashas d
JOIN chart_dashas p ON p.dasha_row_id = d.parent_row_id
WHERE d.chart_id = %s AND d.level_n = 2 AND d.system_id = ANY(%s)
  AND d.ayanamsha_id = %s AND p.ayanamsha_id = %s
ORDER BY d.system_id, d.start_date
"""

_FETCH_PRATIJNA_SQL = """
SELECT bp.pratijna_id, bp.event_class_id, bp.status, bp.grade,
       beo.domain
FROM bodha_pratijna bp
JOIN brahma_event_ontology beo USING (event_class_id)
WHERE bp.chart_id = %s AND bp.status IN ('promised', 'conditional')
  AND bp.ayanamsha_id = 'lahiri_chitrapaksha'
ORDER BY bp.grade DESC
"""

_FETCH_FACT_REFS_SQL = """
SELECT fact_id, fact_subject, fact_key, fact_value_text, fact_value_num
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = 'lahiri_chitrapaksha'
  AND fact_subject = %s
  AND fact_key IN ('sign', 'nakshatra', 'dispositor', 'D9_sign', 'karaka_role',
                   'longitude', 'dignity_score')
LIMIT 10
"""

_INSERT_SQL = """
INSERT INTO kala_avadhi (
    chart_id, system_id, level_n, lord_graha,
    period_start, period_end, dossier, quality,
    citations, formula_version
) VALUES (
    %(chart_id)s, %(system_id)s, %(level_n)s, %(lord_graha)s,
    %(period_start)s, %(period_end)s, %(dossier)s::jsonb, %(quality)s::jsonb,
    %(citations)s, %(formula_version)s
)
ON CONFLICT (chart_id, system_id, level_n, period_start) DO UPDATE SET
    lord_graha     = EXCLUDED.lord_graha,
    period_end     = EXCLUDED.period_end,
    dossier        = EXCLUDED.dossier,
    quality        = EXCLUDED.quality,
    citations      = EXCLUDED.citations,
    formula_version = EXCLUDED.formula_version,
    computed_at    = NOW()
"""


def _table_exists(conn, name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name=%s AND table_schema='public'",
            (name,),
        )
        return cur.fetchone() is not None


@register("ka_avadhi")
class KaAvdhiWriter(WriterBase):
    """ka_avadhi — Period Dossiers (L3 Kāla). LIGHT writer."""

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config["chart_id"]

        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 0")

        # Idempotency: delete-then-insert per §N.3
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_avadhi WHERE chart_id = %s", (chart_id,))

        systems_list = list(_DASHA_SYSTEMS)

        # Load MD periods
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(_FETCH_MD_SQL, (chart_id, systems_list, _CANONICAL_AYANAMSHA))
            md_rows = cur.fetchall()

        # Load AD periods
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(_FETCH_AD_SQL, (chart_id, systems_list, _CANONICAL_AYANAMSHA, _CANONICAL_AYANAMSHA))
            ad_rows = cur.fetchall()

        if not md_rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes="no chart_dashas — run ka_dasha_kala first")

        # Load pratijna (SAVEPOINT-guarded soft dependency)
        pratijna_by_domain: dict[str, list[dict]] = {}
        with conn.cursor() as _sp:
            _sp.execute("SAVEPOINT sp_avadhi_pratijna")
        try:
            if _table_exists(conn, "bodha_pratijna"):
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    cur.execute(_FETCH_PRATIJNA_SQL, (chart_id,))
                    for pr in cur.fetchall():
                        d = str(pr.get("domain") or "unknown")
                        pratijna_by_domain.setdefault(d, []).append({
                            "pratijna_id": str(pr["pratijna_id"]),
                            "event_class_id": pr["event_class_id"],
                            "status": pr["status"],
                            "grade": float(pr["grade"] or 0),
                        })
            with conn.cursor() as _sp:
                _sp.execute("RELEASE SAVEPOINT sp_avadhi_pratijna")
        except Exception as exc:
            with conn.cursor() as _sp:
                _sp.execute("ROLLBACK TO SAVEPOINT sp_avadhi_pratijna")
            logger.debug("ka_avadhi: pratijna fetch skipped: %s", exc)

        # Cache fact_refs per graha (one query per unique lord)
        unique_lords = {r["lord_graha"] for r in md_rows} | {r["lord_graha"] for r in ad_rows}
        fact_refs_by_graha: dict[str, list[dict]] = {}
        for graha in unique_lords:
            with conn.cursor() as _sp:
                _sp.execute(f"SAVEPOINT sp_avadhi_facts_{graha[:6]}")
            try:
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    cur.execute(_FETCH_FACT_REFS_SQL, (chart_id, graha))
                    rows = cur.fetchall()
                fact_refs_by_graha[graha] = [
                    {
                        "fact_id": str(r["fact_id"]),
                        "fact_subject": r["fact_subject"],
                        "fact_key": r["fact_key"],
                        "role": r["fact_key"],
                    }
                    for r in rows
                ]
                with conn.cursor() as _sp:
                    _sp.execute(f"RELEASE SAVEPOINT sp_avadhi_facts_{graha[:6]}")
            except Exception as exc:
                with conn.cursor() as _sp:
                    _sp.execute(f"ROLLBACK TO SAVEPOINT sp_avadhi_facts_{graha[:6]}")
                logger.debug("ka_avadhi: fact_refs for %s skipped: %s", graha, exc)
                fact_refs_by_graha[graha] = []

        rows_inserted = 0

        def _build_row(dasha_row: dict, sublord: str | None = None) -> dict:
            lord = dasha_row["lord_graha"]
            domains = _GRAHA_DOMAINS.get(lord, [])
            activated_ids = []
            for d in domains:
                for pr in pratijna_by_domain.get(d, []):
                    activated_ids.append(pr["pratijna_id"])

            dossier = {
                "lord_condition_fact_refs": fact_refs_by_graha.get(lord, []),
                "activated_pratijna_ids": list(dict.fromkeys(activated_ids))[:10],
                "sublord_modulation": {
                    "graha": sublord,
                    "note": f"AD lord {sublord} modulates MD lord {lord}." if sublord else None,
                } if sublord else None,
            }
            return {
                "chart_id": chart_id,
                "system_id": dasha_row["system_id"],
                "level_n": dasha_row["level_n"],
                "lord_graha": lord,
                "period_start": dasha_row["period_start"],
                "period_end": dasha_row["period_end"],
                "dossier": json.dumps(dossier),
                "quality": json.dumps({"domains": domains}),
                "citations": [
                    "BPHS ch. Vimshottari-Dasha / Classical dasha lord tables",
                ],
                "formula_version": FORMULA_VERSION,
            }

        # Build all rows in memory then batch-insert — avoids N individual round-trips.
        all_rows = [_build_row(md) for md in md_rows] + [
            _build_row(ad, sublord=ad.get("parent_lord_graha")) for ad in ad_rows
        ]
        with conn.cursor() as cur:
            cur.executemany(_INSERT_SQL, all_rows)
        rows_inserted = len(all_rows)

        logger.info("[ka_avadhi] %d period dossier rows for chart %s", rows_inserted, chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=rows_inserted,
                            notes=f"systems={len(systems_list)};md={len(md_rows)};ad={len(ad_rows)}")
