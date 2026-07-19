"""
gochara_grammar.resonance_map — read-side access to G-1's `gochara_resonance_map`.

G-1 (sibling lane) owns the table and its migration; this module only READS it,
defensively: `gochara_resonance_map` may not exist yet (G-1 not merged), or may
exist but be unpopulated for a given chart (G-1 merged, build not yet run for
this chart). Both are honest empty-set cases, not crashes -- per the task brief:
"read defensively, handle 'table not yet populated for this chart' as an honest
empty-set case, not a crash."

Also provides `build_fixture_targets()`, a hand-built set of ResonanceTarget rows
matching G-1's EXACT schema, for unit tests to run against when the live table is
unreachable/unpopulated. Fixture rows are clearly marked (`source_rule_id=None`,
`extra`-equivalent fixture marker carried by callers) -- never silently presented
as live data.
"""
from __future__ import annotations

import logging
from typing import Optional

from .models import ResonanceTarget
from . import citations as C

logger = logging.getLogger(__name__)

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def fetch_resonance_targets(
    conn, chart_id: str, event_class: Optional[str] = None
) -> list[ResonanceTarget]:
    """
    Read rows from `gochara_resonance_map` for `chart_id` (optionally filtered
    to one `event_class`). Returns [] on ANY of:
      - the table does not exist yet (G-1 not merged in this environment)
      - the table exists but has no rows for this chart/event_class
      - the query itself fails for a connectivity/permission reason

    Never raises for the "not populated yet" case -- that is explicitly an
    honest empty result, not an error, per this lane's task brief. Genuine
    programming errors (e.g. a malformed SQL string) still surface via the
    caught exception's log line, so a real regression is not silently eaten
    forever -- but the function contract is "empty list on any DB-shape
    surprise", so G-2 code that free-runs ahead of G-1's data never crashes.
    """
    sql = """
        SELECT chart_id, event_class, target_type, target_ref, weight,
               classical_citation, uncited_extension, source_rule_id
          FROM gochara_resonance_map
         WHERE chart_id = %s
    """
    params: list = [chart_id]
    if event_class is not None:
        sql += " AND event_class = %s"
        params.append(event_class)

    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: any DB-shape
        # surprise (UndefinedTable, connectivity error, etc.) degrades to an
        # honest empty result rather than propagating.
        logger.info(
            "[gochara_grammar.resonance_map] gochara_resonance_map read failed "
            "(table not yet populated, or G-1 not merged in this environment) "
            "chart_id=%s event_class=%s: %s",
            chart_id, event_class, exc,
        )
        return []

    targets: list[ResonanceTarget] = []
    for row in rows:
        # Support both tuple-cursor and dict-row cursor conventions used
        # elsewhere in this codebase (psycopg.rows.dict_row is common but not
        # universal -- handle both without assuming a specific row_factory).
        if isinstance(row, dict):
            d = row
        else:
            keys = [
                "chart_id", "event_class", "target_type", "target_ref", "weight",
                "classical_citation", "uncited_extension", "source_rule_id",
            ]
            d = dict(zip(keys, row))
        targets.append(
            ResonanceTarget(
                chart_id=str(d["chart_id"]),
                event_class=d["event_class"],
                target_type=d["target_type"],
                target_ref=d["target_ref"],
                weight=float(d["weight"]),
                classical_citation=d.get("classical_citation"),
                uncited_extension=bool(d.get("uncited_extension") or False),
                source_rule_id=d.get("source_rule_id"),
            )
        )
    return targets


def build_fixture_targets(chart_id: str) -> list[ResonanceTarget]:
    """
    Hand-built ResonanceTarget rows matching G-1's `gochara_resonance_map`
    schema exactly, for use when the live table is unreachable/unpopulated.

    `chart_id` is REQUIRED (no default) -- per this repo's contamination
    guard (tests/test_contamination_guard.py::test_no_raw_native_birth_fallback,
    Groups 1-8), a `chart_id` parameter must never default to
    CANONICAL_CHART_ID, since that hard-wires native-birth routing for any
    caller that forgets to pass one explicitly. Callers that want the
    canonical chart pass `resonance_map.CANONICAL_CHART_ID` explicitly (see
    tests/test_gochara_grammar.py for the pattern).

    NOT live data -- callers/tests must treat this as a synthetic fixture
    (this module's docstring + this function's name make that explicit).

    Anchors (target_longitude_deg/target_sign/target_nakshatra_id/natal_planet)
    are illustrative placeholders resolved by hand from well-known sidereal
    sign boundaries, NOT re-derived from a live chart_facts query for chart
    482012f1 -- exactly the "well-documented synthetic fixture" the task brief
    allows when DB access is unavailable in the sandbox.
    """
    return [
        ResonanceTarget(
            chart_id=chart_id,
            event_class="marriage",
            target_type="bhava",
            target_ref="7",
            weight=0.9,
            classical_citation=C.GOCHARA_PHALA_BPHS_29,
            target_longitude_deg=195.0,  # illustrative 7th-house cusp placeholder (mid-Libra)
            target_sign="Libra",
        ),
        ResonanceTarget(
            chart_id=chart_id,
            event_class="marriage",
            target_type="karaka",
            target_ref="Venus",
            weight=0.85,
            classical_citation=C.GRAHA_DRISHTI_BPHS_26,
            target_longitude_deg=142.0,  # illustrative natal Venus placeholder
            target_sign="Leo",
            natal_planet="Venus",
        ),
        ResonanceTarget(
            chart_id=chart_id,
            event_class="career_advancement",
            target_type="lord",
            target_ref="10",
            weight=0.8,
            classical_citation=C.GOCHARA_PHALA_BPHS_29,
            target_longitude_deg=280.0,  # illustrative 10th-lord placeholder (Capricorn)
            target_sign="Capricorn",
            natal_planet="Saturn",
        ),
        ResonanceTarget(
            chart_id=chart_id,
            event_class="major_gain",
            target_type="mechanism_node",
            target_ref="argala_11_to_2",
            weight=0.7,
            uncited_extension=True,  # composite mechanism-node scoring, not itself a single BPHS verse
            target_longitude_deg=305.0,
            target_sign="Aquarius",
        ),
        ResonanceTarget(
            chart_id=chart_id,
            event_class="major_gain",
            target_type="sensitive_degree",
            target_ref="moon_natal_297.5",
            weight=0.95,
            classical_citation=C.SADE_SATI_BPHS_71,
            target_longitude_deg=297.5,  # illustrative natal Moon degree placeholder (Purva Bhadrapada per FORENSIC anchors)
            target_sign="Aquarius",
            target_nakshatra_id=25,  # Purva Bhadrapada
            natal_planet="Moon",
        ),
    ]


__all__ = ["fetch_resonance_targets", "build_fixture_targets", "CANONICAL_CHART_ID"]
