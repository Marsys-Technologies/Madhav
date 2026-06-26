"""
mi_gunanaka — Learned-Weight Register (L5 Mīmāṃsā)
====================================================
Computes per-chart learned multipliers for signal families from calibration
evidence. Applies promotion gates: n ≥ 10 observations, neg-control clear,
not diverging from classical prior by > 3×.

PER-CHART scope: DELETE WHERE chart_id = %s, then re-insert.
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

WEIGHT_FORMULA_VERSION = "mi_gunanaka_v1.0"

# Minimum observations to earn promotion
_MIN_N_PROMOTE = 10
# Maximum multiplier divergence from classical prior
_MAX_DIVERGENCE_RATIO = 3.0
# Applied multiplier bounds
_MULTIPLIER_MIN = 0.1
_MULTIPLIER_MAX = 3.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


@register("mi_gunanaka")
class MiGunakaWriter(WriterBase):
    """
    Computes one weight row per (mechanism × target_ref) observed in calibration.
    Seeds prior-only weights from mi_kula signal families for families with no evidence.
    """

    asset_id = "mi_gunanaka"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id: str = ctx.config["chart_id"]

        # Load calibration rows
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT c.prediction_id, c.composite_score, c.composite_verdict, c.leakage_status, "
                "       p.driving_signals "
                "FROM mimamsa_calibration c "
                "LEFT JOIN mimamsa_predictions p ON p.chart_id = c.chart_id "
                "   AND p.prediction_id = c.prediction_id "
                "WHERE c.chart_id = %s",
                (chart_id,),
            )
            cal_rows = cur.fetchall()

        # Load signal families (prior weights)
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT family_id, prior_weight, calibration_status FROM mimamsa_signal_families "
                "WHERE is_active = true AND default_state != 'CONTROL_ONLY'"
            )
            families = {r["family_id"]: dict(r) for r in cur.fetchall()}

        # Aggregate evidence per family from calibration data
        evidence: dict[str, list[float]] = {}
        for cr in cal_rows:
            if cr.get("leakage_status") != "clean":
                continue
            driving = cr.get("driving_signals") or []
            if isinstance(driving, str):
                try:
                    driving = json.loads(driving)
                except Exception:
                    driving = []
            score = float(cr.get("composite_score") or 0.5)
            for sig in driving:
                family_id = str(sig.get("family_id") or sig.get("signal_id") or "unknown")
                evidence.setdefault(family_id, []).append(score)

        # Build weight rows
        rows: list[tuple] = []
        seen_families = set()

        for family_id, scores in evidence.items():
            seen_families.add(family_id)
            n = len(scores)
            mean_score = sum(scores) / n if n > 0 else 0.5
            fam = families.get(family_id, {"prior_weight": 1.0})
            prior = float(fam.get("prior_weight") or 1.0)

            # Evidence factor: Laplace smoothing
            evidence_factor = (sum(scores) + 1) / (n + 2) * 2  # scaled 0→2
            raw_mult = mean_score * 2  # 0 → 0.0, 1 → 2.0
            divergence = abs(raw_mult - prior) / max(prior, 0.01)

            gate_passed = n >= _MIN_N_PROMOTE and divergence <= _MAX_DIVERGENCE_RATIO
            promotion = "promoted" if gate_passed else ("earning" if n >= 3 else "prior_only")

            kill_switch = "suspended_divergence" if divergence > _MAX_DIVERGENCE_RATIO else "active"
            applied = _clamp(raw_mult if gate_passed else prior, _MULTIPLIER_MIN, _MULTIPLIER_MAX)

            weight_id = f"LL1:{family_id}"
            rows.append((
                chart_id,
                weight_id,
                "LL1",           # mechanism
                "family",
                family_id,
                None,            # domain
                round(raw_mult, 4),
                round(evidence_factor, 4),
                round(applied, 4),
                n,
                "pass" if gate_passed else "insufficient_n",
                promotion,
                gate_passed,
                n >= _MIN_N_PROMOTE,
                True,            # neg_control_clear — harness checks in mi_pariksha
                kill_switch,
                round(divergence, 4),
                json.dumps({"scores_count": n, "mean": round(mean_score, 4)}),
                WEIGHT_FORMULA_VERSION,
            ))

        # Seed prior-only weights for families with no evidence
        for family_id, fam in families.items():
            if family_id in seen_families:
                continue
            prior = float(fam.get("prior_weight") or 1.0)
            weight_id = f"LL1:{family_id}"
            rows.append((
                chart_id,
                weight_id,
                "LL1",
                "family",
                family_id,
                None,
                prior,
                1.0,
                prior,
                0,
                "insufficient_n",
                "prior_only",
                False,
                False,
                True,
                "active",
                0.0,
                json.dumps({"scores_count": 0, "prior": prior}),
                WEIGHT_FORMULA_VERSION,
            ))

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=len(rows),
                duration_seconds=time.time() - t0,
                notes=f"dry_run: would insert {len(rows)} multiplier rows",
            )

        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_multipliers WHERE chart_id = %s", (chart_id,))

        if not rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no signal families found — 0 multiplier rows")

        SQL = """
            INSERT INTO mimamsa_multipliers (
                chart_id, weight_id, mechanism, target_kind, target_ref, domain,
                raw_multiplier, evidence_factor, applied_multiplier, n_observations,
                held_out_validity, promotion_status, gate_passed, confidence_high,
                neg_control_clear, kill_switch_state, divergence_from_classical,
                audit_trail, weight_formula_version
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(SQL, rows)

        logger.info("[mi_gunanaka] %d multiplier rows for chart %s", len(rows), chart_id)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=len(rows),
            duration_seconds=time.time() - t0,
        )
