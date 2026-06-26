"""
mi_adhilepa — Calibration-Based Overlays + Load-Bearing Map (L5 Mīmāṃsā)
=========================================================================
Applies learned multipliers as overlay rows to signals, facts, convergences,
and anchors. Also identifies load-bearing signals for key conclusions.

Tables written:
  • mimamsa_signal_adjustment
  • mimamsa_fact_adjustment
  • mimamsa_convergence_adjustment
  • mimamsa_anchor_adjustment
  • mimamsa_load_bearing

PER-CHART scope: DELETE WHERE chart_id = %s, then re-insert.
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import json
import logging
import time

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

OVERLAY_FORMULA_VERSION = "mi_adhilepa_v1.0"

_MULTIPLIER_BOUND_MAX = 2.5
_MULTIPLIER_BOUND_MIN = 0.2


def _table_exists(conn, name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name=%s AND table_schema='public'",
            (name,),
        )
        return cur.fetchone() is not None


def _load_multipliers(conn, chart_id: str) -> dict[str, dict]:
    """Return {target_ref: multiplier_row} for promoted/earning weights."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            "SELECT target_ref, target_kind, applied_multiplier, raw_multiplier, "
            "       n_observations, kill_switch_state "
            "FROM mimamsa_multipliers WHERE chart_id = %s",
            (chart_id,),
        )
        return {r["target_ref"]: dict(r) for r in cur.fetchall()}


def _overlay_row(chart_id: str, origin_layer: str, origin_asset_id: str,
                 origin_id: str, mult: dict, n_pramana: int) -> tuple:
    applied = float(mult["applied_multiplier"])
    raw = float(mult["raw_multiplier"])
    bound = min(applied, _MULTIPLIER_BOUND_MAX)
    leakage = "clean"
    applies = mult.get("kill_switch_state", "active") == "active"
    return (
        chart_id,
        origin_layer,
        origin_asset_id,
        origin_id,
        f"LL1:{mult['target_ref']}",
        round(bound, 4),
        round(raw, 4),
        round(bound, 4),
        int(mult.get("n_observations") or 0),
        leakage,
        applies,
        json.dumps([]),   # derived_from_pramana_ids (full backfill in later version)
        OVERLAY_FORMULA_VERSION,
    )


@register("mi_adhilepa")
class MiAdhilepaWriter(WriterBase):
    """
    Projects learned multipliers onto L2/L3/L4 artifacts as overlay rows.
    Also identifies load-bearing signals.
    """

    asset_id = "mi_adhilepa"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id: str = ctx.config["chart_id"]

        multipliers = _load_multipliers(conn, chart_id)
        total = 0

        # Idempotency: clear all overlay tables for this chart
        with conn.cursor() as cur:
            for tbl in [
                "mimamsa_load_bearing",
                "mimamsa_anchor_adjustment",
                "mimamsa_convergence_adjustment",
                "mimamsa_fact_adjustment",
                "mimamsa_signal_adjustment",
            ]:
                cur.execute(f"DELETE FROM {tbl} WHERE chart_id = %s", (chart_id,))

        if not multipliers:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no multipliers — overlays empty")

        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="dry_run: would apply overlays")

        OVERLAY_SQL = """
            INSERT INTO {table} (
                chart_id, origin_layer, origin_asset_id, origin_id,
                weight_id, multiplier, raw_multiplier, applied_bound, evidence_n,
                leakage_status, applies_to_reading, derived_from_pramana_ids,
                overlay_formula_version
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        # ── Signal overlays (bodha_msr_signals) ─────────────────────────────
        if _table_exists(conn, "bodha_msr_signals"):
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT signal_id, family_id FROM bodha_msr_signals WHERE chart_id = %s",
                    (chart_id,),
                )
                signals = cur.fetchall()

            sig_rows = []
            for sig in signals:
                family_id = sig.get("family_id") or sig.get("signal_id")
                mult = multipliers.get(str(family_id))
                if not mult:
                    continue
                sig_rows.append(_overlay_row(
                    chart_id, "L2", "bo_laksana", str(sig["signal_id"]), mult, 0
                ))

            if sig_rows:
                with conn.cursor() as cur:
                    cur.executemany(OVERLAY_SQL.format(table="mimamsa_signal_adjustment"), sig_rows)
                total += len(sig_rows)
                logger.info("[mi_adhilepa] %d signal overlays", len(sig_rows))

        # ── Fact overlays (chart_facts — high-impact facts only) ─────────────
        if _table_exists(conn, "chart_facts"):
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT fact_id, category FROM chart_facts WHERE chart_id = %s "
                    "AND category IN ('graha', 'yoga') LIMIT 200",
                    (chart_id,),
                )
                facts = cur.fetchall()

            fact_rows = []
            for fact in facts:
                mult = multipliers.get("fam_graha_natal" if fact["category"] == "graha" else "fam_yoga")
                if not mult:
                    continue
                fact_rows.append(_overlay_row(
                    chart_id, "L1", "ga_facts", str(fact["fact_id"]), mult, 0
                ))

            if fact_rows:
                with conn.cursor() as cur:
                    cur.executemany(OVERLAY_SQL.format(table="mimamsa_fact_adjustment"), fact_rows)
                total += len(fact_rows)
                logger.info("[mi_adhilepa] %d fact overlays", len(fact_rows))

        # ── Convergence overlays (kala_convergence) ──────────────────────────
        if _table_exists(conn, "kala_convergence"):
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT convergence_id FROM kala_convergence WHERE chart_id = %s LIMIT 500",
                    (chart_id,),
                )
                convergences = cur.fetchall()

            mult = multipliers.get("fam_convergence")
            if mult and convergences:
                conv_rows = [
                    _overlay_row(chart_id, "L3", "ka_sangam", str(c["convergence_id"]), mult, 0)
                    for c in convergences
                ]
                with conn.cursor() as cur:
                    cur.executemany(OVERLAY_SQL.format(table="mimamsa_convergence_adjustment"), conv_rows)
                total += len(conv_rows)
                logger.info("[mi_adhilepa] %d convergence overlays", len(conv_rows))

        # ── Anchor overlays (phala_anchors) ──────────────────────────────────
        if _table_exists(conn, "phala_anchors"):
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT anchor_id FROM phala_anchors WHERE chart_id = %s",
                    (chart_id,),
                )
                anchors = cur.fetchall()

            mult = multipliers.get("fam_anchor")
            if mult and anchors:
                anc_rows = [
                    _overlay_row(chart_id, "L4", "ph_nimitta", str(a["anchor_id"]), mult, 0)
                    for a in anchors
                ]
                with conn.cursor() as cur:
                    cur.executemany(OVERLAY_SQL.format(table="mimamsa_anchor_adjustment"), anc_rows)
                total += len(anc_rows)
                logger.info("[mi_adhilepa] %d anchor overlays", len(anc_rows))

        # ── Load-bearing map ─────────────────────────────────────────────────
        lb_rows = []
        # Top 3 promoted multipliers become load-bearing for their domain conclusions
        top_mults = sorted(
            [(ref, m) for ref, m in multipliers.items()
             if float(m.get("applied_multiplier") or 0) >= 1.0],
            key=lambda x: float(x[1]["applied_multiplier"]),
            reverse=True,
        )[:5]

        for i, (target_ref, mult) in enumerate(top_mults):
            conclusion_id = f"concl_{target_ref}"
            signal_id = target_ref
            sensitivity = min(float(mult["applied_multiplier"]) / 2.0, 1.0)
            role = "load_bearing" if i == 0 else ("supporting" if i < 3 else "redundant")
            lb_rows.append((chart_id, conclusion_id, signal_id,
                            round(sensitivity, 4), role, OVERLAY_FORMULA_VERSION))

        if lb_rows:
            LB_SQL = """
                INSERT INTO mimamsa_load_bearing (
                    chart_id, conclusion_id, signal_id, sensitivity, role, formula_version
                ) VALUES (%s,%s,%s,%s,%s,%s)
            """
            with conn.cursor() as cur:
                cur.executemany(LB_SQL, lb_rows)
            total += len(lb_rows)
            logger.info("[mi_adhilepa] %d load-bearing rows", len(lb_rows))

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            duration_seconds=time.time() - t0,
        )
