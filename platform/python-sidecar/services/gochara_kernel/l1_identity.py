"""The L1 identity component of the overlay writers' upstream fingerprints (step 3 §4).

The §12.9 fingerprint answered "built from what the reference tables say now?" from L0
tables only — `ephemeris_daily` was deliberately not fingerprinted and the consumed L1
(natal) operands were not fingerprinted either, so rows built from an OLD L1 build read
`fresh` (spec §4, the defect). Both overlay writers read exactly one L1 fact — the natal
`graha_position / MOON / longitude_sidereal` for the chart — and each declares its operand
tuple as a module constant next to its own SQL (`L1_OPERANDS`). The writer, the freshness
check and the '4.1' manifest all call THIS one helper (the existing "same fetch path as the
writer" principle, `ka_vedha_gochara/freshness.py`), so the stamped identity and the
recomputed identity cannot drift apart.

A missing operand means the identity cannot be computed: `L1OperandAbsentError` — the
freshness check turns that into `stale` (reason `l1_operand_absent`), never `fresh`; the
writers never reach it (their own janma fetch fails first).
"""
from __future__ import annotations

from typing import Any

import psycopg.rows

from services.gochara_kernel.fingerprint import canonical_digest

# The same WHERE shape the writers' own _FETCH_JANMA_MOON_SQL uses, plus the
# identity columns (build_id, and fact_value_num AS STORED TEXT — the value the
# row carries, not a float reformat).
_FETCH_OPERAND_SQL = """
SELECT fact_id, build_id, fact_value_num::text AS value
FROM chart_facts
WHERE chart_id = %s AND ayanamsha_id = %s
  AND fact_category = %s AND fact_subject = %s AND fact_key = %s
"""


class L1OperandAbsentError(RuntimeError):
    """A declared L1 operand has no chart_facts row — the identity cannot be computed."""


def l1_operand_identity(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    operands: tuple[tuple[str, str, str], ...],
) -> dict:
    """{"operands": [{category, subject, key, fact_id, build_id, value}], "digest": sha256}
    for the (category, subject, key) tuples `operands` declares, read from live
    chart_facts. Order follows the declared tuple. Raises L1OperandAbsentError when any
    operand is absent, and RuntimeError when an operand is ambiguous (more than one row —
    the writers' own fetch could not say which it read either).
    """
    out = []
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        for category, subject, key in operands:
            cur.execute(_FETCH_OPERAND_SQL, (chart_id, ayanamsha_id, category, subject, key))
            rows = cur.fetchall()
            if not rows:
                raise L1OperandAbsentError(
                    f"l1 operand absent: {category}/{subject}/{key} for chart "
                    f"{chart_id} ({ayanamsha_id}) — the L1 identity cannot be computed"
                )
            if len(rows) > 1:
                raise RuntimeError(
                    f"l1 operand ambiguous: {len(rows)} chart_facts rows for "
                    f"{category}/{subject}/{key} chart {chart_id} ({ayanamsha_id})"
                )
            row = rows[0]
            out.append({
                "category": category,
                "subject": subject,
                "key": key,
                "fact_id": str(row["fact_id"]),
                "build_id": None if row["build_id"] is None else str(row["build_id"]),
                "value": row["value"],
            })
    return {"operands": out, "digest": canonical_digest(out)}
