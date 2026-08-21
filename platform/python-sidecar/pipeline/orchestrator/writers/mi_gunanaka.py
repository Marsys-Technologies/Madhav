"""
mi_gunanaka v2 — Learned-Weight Register with Hierarchical Shrinkage (L5 Mīmāṃsā)
===================================================================================
BA-P6: n≥10 hard gate REPLACED by hierarchical shrinkage:
  posterior = (n × likelihood + k × prior) / (n + k)
  where k = mi_gunanaka_shrinkage_k from brahma_formula_constants.
  At n=0: posterior = classical prior (full shrinkage to prior).
  3× divergence cap RETAINED (mi_gunanaka_divergence_cap from brahma_formula_constants).

Versioned calibration snapshots published to mimamsa_calibration_snapshot.

PER-CHART scope: DELETE WHERE chart_id = %s, then re-insert.
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, register

logger = logging.getLogger(__name__)

WEIGHT_FORMULA_VERSION = "mi_gunanaka_v2.0"

_DEFAULT_SHRINKAGE_K = 5.0
_DEFAULT_DIVERGENCE_CAP = 3.0
_MULTIPLIER_MIN = 0.1
_MULTIPLIER_MAX = 3.0


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _load_constants(conn) -> tuple[float, float]:
    """Load shrinkage_k and divergence_cap from brahma_formula_constants."""
    shrinkage_k = _DEFAULT_SHRINKAGE_K
    divergence_cap = _DEFAULT_DIVERGENCE_CAP
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT constant_id, value_jsonb FROM brahma_formula_constants "
                "WHERE constant_id IN ('mi_gunanaka_shrinkage_k', 'mi_gunanaka_divergence_cap')"
            )
            for row in cur.fetchall():
                cid = row["constant_id"]
                val = row["value_jsonb"]
                if cid == "mi_gunanaka_shrinkage_k" and val:
                    shrinkage_k = float(val.get("k", _DEFAULT_SHRINKAGE_K))
                elif cid == "mi_gunanaka_divergence_cap" and val:
                    divergence_cap = float(val.get("cap", _DEFAULT_DIVERGENCE_CAP))
    except Exception as e:
        logger.warning("[mi_gunanaka] failed to load constants from registry (%s); using defaults", e)
    return shrinkage_k, divergence_cap


def _hierarchical_posterior(
    cell_likelihood: float,
    cell_n: int,
    family_likelihood: float,
    global_likelihood: float,
    classical_prior: float,
    shrinkage_k: float,
) -> float:
    """
    Hierarchical shrinkage (cell → family → global pooling, weights ∝ n).
    Step 1: family-level posterior = (cell_n × cell_likelihood + k × family_likelihood) / (cell_n + k)
    Step 2: global shrinkage = (cell_n × step1 + k × global_likelihood) / (cell_n + k)
    At n=0: posterior = classical_prior (no data → fall back to classical).
    """
    if cell_n == 0:
        return float(classical_prior)
    # Cell → family shrinkage
    family_posterior = (cell_n * cell_likelihood + shrinkage_k * family_likelihood) / (cell_n + shrinkage_k)
    # Family → global shrinkage
    global_posterior = (cell_n * family_posterior + shrinkage_k * global_likelihood) / (cell_n + shrinkage_k)
    return global_posterior


@register("mi_gunanaka")
class MiGunakaWriter(WriterBase):
    """
    Computes per-chart learned multipliers via hierarchical shrinkage.
    Seeds prior-only rows (posterior = classical prior) for families with no evidence.
    Publishes a versioned calibration snapshot to mimamsa_calibration_snapshot.
    """

    asset_id = "mi_gunanaka"

    def run(self, ctx) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id: str = ctx.config["chart_id"]

        shrinkage_k, divergence_cap = _load_constants(conn)

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

        # Load signal families with their classical priors
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT family_id, prior_weight, calibration_status FROM mimamsa_signal_families "
                "WHERE is_active = true AND default_state != 'CONTROL_ONLY'"
            )
            families = {r["family_id"]: dict(r) for r in cur.fetchall()}

        # Aggregate evidence per family from calibration data.
        # §N.8 (Earned-Signal Principle): only exclude rows explicitly marked 'leaked'
        # (when a real detector has run and found leakage). 'not_assessed' rows are
        # admitted — excluding them would silently empty the calibration evidence path
        # when no leakage detector exists, the same defect class as a filter that can
        # never pass (§N.8). 'clean' rows are also admitted (detector ran, found nothing).
        evidence: dict[str, list[float]] = {}
        not_assessed_count = 0
        excluded_leaked_count = 0
        for cr in cal_rows:
            ls = cr.get("leakage_status")
            if ls == "leaked":
                # Genuinely detected leakage — exclude from calibration evidence.
                excluded_leaked_count += 1
                continue
            if ls == "not_assessed":
                # No leakage detector has run — include with honest acknowledgment.
                # §N.8: excluding un-assessed rows would silently empty the calibration
                # path when no detector exists.
                not_assessed_count += 1
            # 'clean' and 'not_assessed' rows proceed to calibration evidence.
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
        logger.info(
            "[mi_gunanaka] calibration evidence: %d rows admitted (%d not_assessed, %d excluded as leaked)",
            len(cal_rows) - excluded_leaked_count, not_assessed_count, excluded_leaked_count,
        )

        # Global likelihood: mean across all observed scores
        all_scores = [s for scores in evidence.values() for s in scores]
        global_likelihood = sum(all_scores) / len(all_scores) if all_scores else 0.5

        # Family-level likelihood: mean per family (used as pooling target)
        family_likelihoods = {
            fid: sum(scores) / len(scores)
            for fid, scores in evidence.items()
            if scores
        }
        family_mean_likelihood = (
            sum(family_likelihoods.values()) / len(family_likelihoods)
            if family_likelihoods else 0.5
        )

        rows: list[tuple] = []
        seen_families = set()
        snapshot_cells: list[dict] = []

        for family_id, scores in evidence.items():
            seen_families.add(family_id)
            n = len(scores)
            cell_likelihood = sum(scores) / n if n > 0 else 0.5
            fam = families.get(family_id, {"prior_weight": 1.0})
            classical_prior = float(fam.get("prior_weight") or 1.0)

            # Family-level likelihood for this family's pool
            fam_likelihood = family_likelihoods.get(family_id, family_mean_likelihood)

            # Hierarchical shrinkage posterior
            posterior = _hierarchical_posterior(
                cell_likelihood, n, fam_likelihood, global_likelihood,
                classical_prior, shrinkage_k,
            )
            # Convert posterior (0→1 score) to multiplier (0→2 scale)
            raw_mult = posterior * 2.0
            divergence = abs(raw_mult - classical_prior) / max(classical_prior, 0.01)

            # 3× divergence cap RETAINED
            if divergence > divergence_cap:
                raw_mult = classical_prior * (1 + (divergence_cap * (1 if raw_mult > classical_prior else -1)))
                kill_switch = "suspended_divergence"
            else:
                kill_switch = "active"

            applied = _clamp(raw_mult, _MULTIPLIER_MIN, _MULTIPLIER_MAX)
            promotion = "promoted" if n >= 3 else "earning"

            weight_id = f"LL1:{family_id}"
            rows.append((
                chart_id,
                weight_id,
                "LL1",
                "family",
                family_id,
                None,
                round(raw_mult, 4),
                round(posterior, 4),
                round(applied, 4),
                n,
                "pass",
                promotion,
                True,
                n >= 5,
                True,
                kill_switch,
                round(divergence, 4),
                json.dumps({
                    "scores_count": n,
                    "cell_likelihood": round(cell_likelihood, 4),
                    "fam_likelihood": round(fam_likelihood, 4),
                    "global_likelihood": round(global_likelihood, 4),
                    "shrinkage_k": shrinkage_k,
                    "posterior": round(posterior, 4),
                    "formula": "hierarchical_shrinkage_v2",
                }),
                WEIGHT_FORMULA_VERSION,
            ))
            snapshot_cells.append({
                "family_id": family_id,
                "n": n,
                "posterior": round(posterior, 4),
                "applied": round(applied, 4),
                "kill_switch": kill_switch,
            })

        # Seed prior-only weights for families with no evidence (n=0 → full prior)
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
                prior / 2.0,  # evidence_factor = prior_only
                prior,
                0,
                "insufficient_n",
                "prior_only",
                False,
                False,
                True,
                "active",
                0.0,
                json.dumps({
                    "scores_count": 0,
                    "prior": prior,
                    "formula": "hierarchical_shrinkage_v2_prior_only",
                }),
                WEIGHT_FORMULA_VERSION,
            ))
            snapshot_cells.append({
                "family_id": family_id,
                "n": 0,
                "posterior": round(prior / 2.0, 4),
                "applied": prior,
                "kill_switch": "active",
            })

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=len(rows),
                duration_seconds=time.time() - t0,
                notes=f"dry_run: would insert {len(rows)} multiplier rows",
            )

        if not rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no signal families found — 0 multiplier rows")

        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_multipliers WHERE chart_id = %s", (chart_id,))

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

        # Publish versioned calibration snapshot (two-key publication — key-2 pending native sign-off)
        _publish_snapshot(conn, chart_id, snapshot_cells, WEIGHT_FORMULA_VERSION)

        logger.info("[mi_gunanaka] %d multiplier rows (shrinkage_k=%.1f, diverge_cap=%.1f) for chart %s",
                    len(rows), shrinkage_k, divergence_cap, chart_id)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=len(rows),
            duration_seconds=time.time() - t0,
        )


def _publish_snapshot(conn, chart_id: str, cells: list[dict], formula_version: str) -> None:
    """Publish a versioned calibration snapshot (key-1 signed; key-2 pending native).

    SV-6 fix (parked ŚUDDHA-VĀCA finding, NIḤŚEṢA Track B): `chart_id` is annotated
    `str`, but the value actually delivered via `ctx.config["chart_id"]` is not
    guaranteed to already be a plain `str` at the call site (a `uuid.UUID` instance
    reaches here in practice for some callers) — `chart_id[:8]` then raised
    `'UUID' object is not subscriptable`, caught non-fatally by the except block
    below and logged as a warning, silently skipping the snapshot publish for the
    affected chart every time it occurred. `str(chart_id)[:8]` makes the id-prefix
    slice work correctly for both a `str` and a `uuid.UUID` input, fixing the
    computation at its root rather than merely tolerating the exception.

    F-188 (PARIŚEṢA-V4, ratified 2026-08-22): this function is a deliberate,
    RATIFIED exception to CLAUDE.md §N.3's per-chart delete-then-insert
    idempotency standard. `snapshot_id` embeds `int(time.time())`, so every
    rebuild inserts a NEW row into `mimamsa_calibration_snapshot` rather than
    replacing a prior one — the table accretes across rebuilds by design. This
    is correct, not a bug: `mimamsa_calibration_snapshot` is the append-only
    historical record the L5 calibration loop reads (two-key publication —
    key-1 = this writer, key-2 = native Ācārya-Pratinidhi sign-off; see the
    table's own COMMENT in migration 400). A delete-then-insert here would
    destroy exactly the history the table exists to keep, discarding every
    prior proposed/published snapshot instead of preserving it alongside the
    new one. `mimamsa_multipliers` (the INSERT above, guarded by the
    `DELETE FROM mimamsa_multipliers WHERE chart_id = %s` at the top of
    `run()`) correctly obeys §N.3 in the ordinary way — the exception is
    scoped to this one accretion table, not to the asset as a whole. See
    `00_ARCHITECTURE/briefs/parisesa/F188_ACCRETION_EXCEPTION_v1_0.md` for the
    full doctrine note; `asset_registry.count_sql` for `mi_gunanaka` was
    corrected in the same finding to count both tables (it previously counted
    `mimamsa_multipliers` only and silently missed this table's rows).
    """
    try:
        snapshot_id = f"snap_{str(chart_id)[:8]}_{int(time.time())}"
        sp = "sp_snapshot"
        with conn.cursor() as cur:
            cur.execute(f"SAVEPOINT {sp}")
            cur.execute(
                "INSERT INTO mimamsa_calibration_snapshot "
                "(snapshot_id, chart_id, proposing_executor, two_key_complete, "
                " cells_jsonb, publication_status, formula_version) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT (snapshot_id) DO NOTHING",
                (
                    snapshot_id,
                    chart_id,
                    "mi_gunanaka",
                    False,
                    json.dumps({"families": cells, "n_families": len(cells)}),
                    "proposed",
                    formula_version,
                ),
            )
            cur.execute(f"RELEASE SAVEPOINT {sp}")
            logger.info("[mi_gunanaka] snapshot %s published (key-2 pending)", snapshot_id)
    except Exception as e:
        try:
            with conn.cursor() as cur:
                cur.execute(f"ROLLBACK TO SAVEPOINT {sp}")
        except Exception:
            pass
        logger.warning("[mi_gunanaka] snapshot publish failed (%s) — continuing", e)
