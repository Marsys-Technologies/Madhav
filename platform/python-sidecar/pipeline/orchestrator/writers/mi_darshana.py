"""
mi_darshana — Insight Retrieval Surface (L5 Mīmāṃsā)
=====================================================
HEAVY writer: three substeps per chart:
  1. "insight_units"  — synthesize calibrated + discovery + grammar data into
                         retrievable insight_unit rows with full provenance
  2. "embeddings"     — mark rows for embedding (actual vectors require external
                         embedding model call — [EXTERNAL_COMPUTATION_REQUIRED])
  3. "views_verify"   — count-check against views and log gaps

Tables written: mimamsa_insight_units (+ embedding stubs if model available)
PER-CHART scope.

B.10 note: embedding vectors require an external embedding model. The writer
inserts insight_units in full; mimamsa_insight_embeddings rows are NOT inserted
here — that requires an external embedding service call tagged
[EXTERNAL_COMPUTATION_REQUIRED].

FROZEN orchestrator contract: @register, plan_substeps + run_substep.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, SubStep, register

logger = logging.getLogger(__name__)

SURFACE_FORMULA_VERSION = "mi_darshana_v1.0"
LEL_VERSION = "v1.7"

_INSIGHT_TYPES = {
    "calibrated_outlook": "Calibrated confidence from prediction-event matching",
    "manifestation_grammar": "Learned channel propensity for this native",
    "emergent_law": "Pattern candidate from discovery mining",
    "load_bearing": "Load-bearing conclusion from signal sensitivity map",
    "negative_knowledge": "What definitively does NOT hold for this native",
}


def _table_exists(conn, name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name=%s AND table_schema='public'",
            (name,),
        )
        return cur.fetchone() is not None


@register("mi_darshana")
class MiDarshanaWriter(WriterBase):
    """
    Synthesizes L5 data into retrievable insight units.
    HEAVY: insight_units → embeddings → views_verify (3 substeps).
    """

    asset_id = "mi_darshana"
    has_substeps = True

    def plan_substeps(self, ctx) -> list[SubStep]:
        self._chart_id = ctx.config["chart_id"]
        return [
            SubStep(key="insight_units", label="synthesize insight units"),
            SubStep(key="embeddings", label="mark embedding stubs"),
            SubStep(key="views_verify", label="verify views"),
        ]

    def run_substep(self, ctx, step: SubStep) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id = self._chart_id

        if step.key == "insight_units":
            return self._substep_insight_units(conn, chart_id, t0)
        if step.key == "embeddings":
            return self._substep_embeddings(conn, chart_id, t0)
        if step.key == "views_verify":
            return self._substep_views_verify(conn, chart_id, t0)
        raise ValueError(f"unknown substep: {step.key}")

    # ── insight_units ────────────────────────────────────────────────────────

    def _substep_insight_units(self, conn, chart_id: str, t0: float) -> WriterResult:
        rows: list[tuple] = []
        now = datetime.utcnow()

        # ── 1. Calibrated-outlook insights from reliability strata ────────────
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT stratum_key, predicted_prob_bin, observed_rate, n, "
                "       brier_score, evidence_grade, held_out_validity "
                "FROM mimamsa_reliability WHERE chart_id = %s",
                (chart_id,),
            )
            rel_rows = cur.fetchall()

        for i, r in enumerate(rel_rows):
            n = r.get("n") or 0
            if n < 2:
                continue
            observed = r.get("observed_rate")
            grade = r.get("evidence_grade", "prior_only")
            statement = (
                f"In predictions scored {r['predicted_prob_bin']}, "
                f"the observed outcome rate is {observed:.1%} across {n} events "
                f"(evidence: {grade})."
            ) if observed is not None else (
                f"Stratum {r['stratum_key']}: {n} predictions, insufficient events to compute rate."
            )
            insight_id = f"cal_{r['stratum_key'].replace('|','_')[:50]}_{i}"
            conf_lo = max(0.0, (observed or 0.5) - 0.1)
            conf_hi = min(1.0, (observed or 0.5) + 0.1)
            rows.append((
                chart_id, insight_id, "calibrated_outlook",
                None, None, None,   # domain, horizon, question_lens
                statement,
                float(observed or 0.5),
                f"[{round(conf_lo,2)},{round(conf_hi,2)})",
                n,
                "clean",
                grade,
                LEL_VERSION,
                None,   # last_calibrated_at
                json.dumps({"stratum": r["stratum_key"], "brier": r.get("brier_score")}),
                False,
                SURFACE_FORMULA_VERSION,
            ))

        # ── 2. Manifestation-grammar insights ────────────────────────────────
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT channel_id, domain, channel_propensity, prior_propensity, "
                "       n_support, evidence_grade "
                "FROM mimamsa_manifestation_grammar WHERE chart_id = %s "
                "AND evidence_grade = 'empirical' ORDER BY n_support DESC LIMIT 20",
                (chart_id,),
            )
            gram_rows = cur.fetchall()

        for i, r in enumerate(gram_rows):
            ch = r["channel_id"]
            dom = r.get("domain", "unknown")
            prop = float(r.get("channel_propensity") or r.get("prior_propensity") or 0.5)
            n = r.get("n_support") or 0
            statement = (
                f"For {dom} events, the '{ch}' channel fires with {prop:.0%} propensity "
                f"(n={n}, empirical learning)."
            )
            insight_id = f"gram_{dom}_{ch[:20]}_{i}"
            rows.append((
                chart_id, insight_id, "manifestation_grammar",
                dom, None, None,
                statement,
                prop,
                None,   # confidence_band
                n,
                "clean",
                "empirical",
                LEL_VERSION,
                now,
                json.dumps({"channel": ch, "domain": dom, "propensity": prop}),
                False,
                SURFACE_FORMULA_VERSION,
            ))

        # ── 3. Emergent-law insights from discoveries ─────────────────────────
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT discovery_id, discovery_class, statement, strength, n_support, "
                "       confidence_band, activation_status "
                "FROM mimamsa_discoveries WHERE chart_id = %s ORDER BY strength DESC NULLS LAST",
                (chart_id,),
            )
            disc_rows = cur.fetchall()

        for r in disc_rows:
            insight_id = f"disc_{r['discovery_id'][:50]}"
            strength = float(r.get("strength") or 0.5)
            n = r.get("n_support") or 0
            is_neg = False
            rows.append((
                chart_id, insight_id, r.get("discovery_class", "emergent_law"),
                None, None, None,
                r["statement"],
                strength,
                r.get("confidence_band"),
                n,
                "clean",
                "empirical" if n >= 5 else "prior_only",
                LEL_VERSION,
                now,
                json.dumps({"discovery_id": r["discovery_id"], "status": r.get("activation_status")}),
                is_neg,
                SURFACE_FORMULA_VERSION,
            ))

        # ── 4. Load-bearing signal insights ──────────────────────────────────
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT conclusion_id, signal_id, sensitivity, role "
                "FROM mimamsa_load_bearing WHERE chart_id = %s ORDER BY sensitivity DESC",
                (chart_id,),
            )
            lb_rows = cur.fetchall()

        for r in lb_rows:
            insight_id = f"lb_{r['conclusion_id'][:50]}"
            sens = float(r["sensitivity"])
            statement = (
                f"Signal '{r['signal_id']}' is {r['role']} for conclusion '{r['conclusion_id']}' "
                f"(sensitivity={sens:.2f}). Removing this signal would materially alter the reading."
            )
            rows.append((
                chart_id, insight_id, "load_bearing",
                None, None, None,
                statement,
                sens,
                None,
                1,
                "clean",
                "structural",
                LEL_VERSION,
                None,
                json.dumps({"signal_id": r["signal_id"], "role": r["role"]}),
                False,
                SURFACE_FORMULA_VERSION,
            ))

        # Idempotency: delete prior insight units
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_insight_units WHERE chart_id = %s", (chart_id,))

        if not rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no source data — 0 insight units")

        SQL = """
            INSERT INTO mimamsa_insight_units (
                chart_id, insight_id, insight_type, domain, horizon, question_lens,
                statement, rank_consequence, confidence_band, n_support,
                leakage_status, evidence_grade, freshness_lel_version,
                last_calibrated_at, provenance_chain, is_negative_knowledge,
                surface_formula_version
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,
                %s::numrange,
                %s,%s,%s,%s,%s,%s,%s,%s
            )
        """
        BATCH = 500
        with conn.cursor() as cur:
            for i in range(0, len(rows), BATCH):
                cur.executemany(SQL, rows[i:i+BATCH])

        logger.info("[mi_darshana:insight_units] %d insight units for chart %s",
                    len(rows), chart_id)
        self._insight_count = len(rows)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)

    # ── embeddings ───────────────────────────────────────────────────────────

    def _substep_embeddings(self, conn, chart_id: str, t0: float) -> WriterResult:
        # Per B.10: generating vector embeddings requires an external embedding model.
        # This substep logs the requirement but does NOT insert fake vectors.
        # [EXTERNAL_COMPUTATION_REQUIRED]: call embedding model (e.g. text-embedding-3-small)
        # on each mimamsa_insight_units.statement and INSERT into mimamsa_insight_embeddings.
        insight_count = getattr(self, "_insight_count", 0)
        logger.warning(
            "[mi_darshana:embeddings] %d insight units require external embedding calls "
            "[EXTERNAL_COMPUTATION_REQUIRED]. "
            "Run the embedding service against mimamsa_insight_units WHERE chart_id = '%s' "
            "to populate mimamsa_insight_embeddings.",
            insight_count, chart_id,
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=0,
            duration_seconds=time.time() - t0,
            notes=(
                f"[EXTERNAL_COMPUTATION_REQUIRED] {insight_count} insight units need embedding. "
                "INSERT into mimamsa_insight_embeddings via external model call."
            ),
        )

    # ── views_verify ─────────────────────────────────────────────────────────

    def _substep_views_verify(self, conn, chart_id: str, t0: float) -> WriterResult:
        counts = {}
        for view in [
            "vw_mimamsa_insight_by_domain",
            "vw_mimamsa_insight_by_horizon",
            "vw_mimamsa_insight_by_lens",
            "vw_mimamsa_negative_knowledge",
        ]:
            try:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM {view} WHERE chart_id = %s", (chart_id,))
                    r = cur.fetchone()
                    counts[view] = r[0] if r else 0
            except Exception as exc:
                counts[view] = f"ERROR: {exc}"

        logger.info("[mi_darshana:views_verify] chart %s view counts: %s", chart_id, counts)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=0,
            duration_seconds=time.time() - t0,
            notes=f"view counts: {counts}",
        )
