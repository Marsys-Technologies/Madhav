"""
pipeline/orchestrator/writers/ga_transit_anchors.py
L1 Gaṇita heavy writer for ga_transit_anchors (Transit/Gochara Subsystem Gate-1).

Sub-step grain = one per ayanamsha (5 ayanamshas × 9 grahas = 45 rows per chart).
Each sub-step:
  1. DELETE WHERE (chart_id, ayanamsha_id) — L1 idempotency standard (replace, not accrete)
  2. INSERT natal position anchors from chart_facts

FORENSIC assertion (canonical chart only):
  Moon natal_sign must be 'aquarius' for chart_id 482012f1-710e-4a25-994a-93821f5871aa.

Conforms to the FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2).
"""
from __future__ import annotations

import logging

import psycopg.rows

from . import register, WriterBase, ContextSpec, WriterResult, SubStep
from brahmagyan.graha_vocabulary import to_title

logger = logging.getLogger(__name__)

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# 9 canonical grahas in UPPER_SNAKE fact_subject form
# lowercase long form, derived from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2 (found via the full-tree census; not one of the originally-
# enumerated retirement targets, but the same shape — this file's own
# established output convention happens to be lowercase, not Title-case).
_SUBJECT_TO_GRAHA: dict[str, str] = {
    code: to_title(code).lower()
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
}

# Ayanamshas matching CANONICAL_AYANAMSHAS in ga_positions_writer
_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "true_chitra",
    "krishnamurti",
    "raman",
    "surya_siddhanta_classical",
]

# Sign number → sign name (1-indexed)
_SIGN_NUM_TO_NAME: dict[int, str] = {
    1: "aries", 2: "taurus", 3: "gemini", 4: "cancer",
    5: "leo", 6: "virgo", 7: "libra", 8: "scorpio",
    9: "sagittarius", 10: "capricorn", 11: "aquarius", 12: "pisces",
}

_SIGN_NAME_TO_NUM: dict[str, int] = {v: k for k, v in _SIGN_NUM_TO_NAME.items()}


def _house_from_moon(moon_sign: str, planet_sign: str) -> int:
    """
    Compute Gochara house count — 1-based counting from Moon sign.
    Moon's own sign = house 1; next sign = house 2; etc.
    """
    moon_num = _SIGN_NAME_TO_NUM.get(moon_sign.lower(), 0)
    planet_num = _SIGN_NAME_TO_NUM.get(planet_sign.lower(), 0)
    if moon_num == 0 or planet_num == 0:
        return 1  # fallback: same sign
    return ((planet_num - moon_num) % 12) + 1


@register("ga_transit_anchors")
class GaTransitAnchorsWriter(WriterBase):
    """
    Heavy writer: one sub-step per ayanamsha.
    Builds natal transit anchor rows from chart_facts graha positions.
    """

    asset_id = "ga_transit_anchors"
    has_substeps = True
    source_paths = [
        "platform/python-sidecar/pipeline/orchestrator/writers/ga_transit_anchors.py"
    ]

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [
            SubStep(
                key=f"ayanamsha_{aya}",
                label=f"GA-transit-anchors — {aya}",
            )
            for aya in _AYANAMSHAS
        ]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"dry_run=True; skipped substep {step.key}",
            )

        chart_id = ctx.config["chart_id"]
        ayanamsha_id = step.key.removeprefix("ayanamsha_")

        # ── Load graha positions from chart_facts ─────────────────────────────
        positions: dict[str, dict] = {}
        with ctx.db_conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(
                """
                SELECT fact_subject, fact_key, fact_value_text, fact_value_num
                FROM chart_facts
                WHERE chart_id     = %s
                  AND ayanamsha_id = %s
                  AND fact_category IN ('graha_position', 'graha_sign_attributes')
                  AND fact_key IN ('sign', 'longitude_sidereal')
                """,
                (chart_id, ayanamsha_id),
            )
            for subject, key, val_text, val_num in cur.fetchall():
                graha = _SUBJECT_TO_GRAHA.get(subject)
                if graha is None:
                    continue
                if graha not in positions:
                    positions[graha] = {}
                if key == "sign" and val_text:
                    positions[graha]["natal_sign"] = val_text.lower()
                elif key == "longitude_sidereal" and val_num is not None:
                    positions[graha]["natal_degree_absolute"] = float(val_num)

        if not positions:
            logger.warning(
                "[ga_transit_anchors] No chart_facts found for chart_id=%s ayanamsha=%s",
                chart_id,
                ayanamsha_id,
            )
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes=f"no chart_facts for {ayanamsha_id}",
            )

        # ── FORENSIC assertion for canonical native chart ─────────────────────
        if chart_id == CANONICAL_CHART_ID:
            moon_sign = positions.get("moon", {}).get("natal_sign", "")
            if not moon_sign or moon_sign != "aquarius":
                raise AssertionError(
                    f"FORENSIC VIOLATION: Moon natal_sign={moon_sign!r} "
                    f"but expected 'aquarius' for chart_id={CANONICAL_CHART_ID} "
                    f"ayanamsha={ayanamsha_id}. "
                    "Moon absent or wrong sign — check ga_positions build for this chart."
                )

        # ── Resolve Moon sign for house-from-Moon computation ─────────────────
        moon_sign = positions.get("moon", {}).get("natal_sign", "")
        if not moon_sign:
            logger.error(
                "[ga_transit_anchors] Moon sign not found in chart_facts for "
                "chart_id=%s ayanamsha=%s — house_from_moon will be 1 for all grahas",
                chart_id,
                ayanamsha_id,
            )

        # ── L1 idempotency: delete then insert ───────────────────────────────
        with ctx.db_conn.cursor() as cur:
            cur.execute(
                "DELETE FROM ga_transit_anchors WHERE chart_id = %s AND ayanamsha_id = %s",
                (chart_id, ayanamsha_id),
            )

        # ── Build and insert anchor rows ──────────────────────────────────────
        rows_inserted = 0
        with ctx.db_conn.cursor() as cur:
            for graha, pos in positions.items():
                natal_sign = pos.get("natal_sign")
                natal_degree = pos.get("natal_degree_absolute")
                if natal_sign is None or natal_degree is None:
                    logger.warning(
                        "[ga_transit_anchors] Incomplete data for graha=%s chart_id=%s aya=%s; "
                        "skipping row",
                        graha, chart_id, ayanamsha_id,
                    )
                    continue

                house_from_moon = (
                    _house_from_moon(moon_sign, natal_sign) if moon_sign else 1
                )

                cur.execute(
                    """
                    INSERT INTO ga_transit_anchors
                        (chart_id, build_id, ayanamsha_id, graha,
                         natal_sign, natal_house_from_moon, natal_degree_absolute)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        chart_id,
                        ctx.build_id,
                        ayanamsha_id,
                        graha,
                        natal_sign,
                        house_from_moon,
                        natal_degree,
                    ),
                )
                rows_inserted += 1

        logger.info(
            "[ga_transit_anchors] Inserted %d anchor rows for chart_id=%s ayanamsha=%s",
            rows_inserted, chart_id, ayanamsha_id,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_inserted,
        )
