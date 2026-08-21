"""
mi_pariksha v2 — Attribution Engine + QA Harness + Retrodiction Suite (L5 Mīmāṃsā)
=====================================================================================
BA-P6: _DIM_WEIGHTS embedded dict DELETED (now in brahma_formula_constants).
       Catch-all attribution (fam_graha_natal with 0.5 default) DELETED.
       Empty lift_vectors excluded, never defaulted.
       4 new substeps: retrodiction + control_windows + ablation + tail_only.

7 substeps per chart:
  1. "retrodiction"    — historical-anchor probe over admissible LEL events (the T−90d
                         date-filtered blinding is DECLARED, not enforced at build time —
                         see _substep_retrodiction; F-143)
  2. "control_windows" — ≥3 same-length no-event control windows per event (age-band stratified)
  3. "ablation"        — per-family marginal skill (ablation mask)
  4. "attribution"     — analytic from lift_vectors (catch-all deleted; empty excluded)
  5. "neg_control"     — negative-control QA harness
  6. "discovery"       — pattern discovery from calibration corpus
  7. "tail_only"       — retrodiction over salience tail (Ranking Doctrine falsifier)

Tables written: mimamsa_attribution, mimamsa_qa_eval, mimamsa_discoveries
PER-CHART scope.

FROZEN orchestrator contract: @register, plan_substeps + run_substep.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import date, timedelta
from typing import Any

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, SubStep, register

logger = logging.getLogger(__name__)

ATTRIBUTION_FORMULA_VER = "mi_pariksha_v2.0"
DISCOVERY_FORMULA_VER = "mi_pariksha_v2.1"    # v2.1: F-143 n_scored_matches in evidence_refs
RETRODICTION_FORMULA_VER = "mi_pariksha_v2.1"  # v2.1: F-143 statement no longer claims unenforced blinding

_DIMENSIONS = ["timing", "magnitude", "domain", "falsifier", "manifestation"]

# F-143 (same class as F-35): the ONLY composite_verdict values that represent an
# ADJUDICATED outcome — i.e. a prediction whose observation window has elapsed and
# whose result has actually been scored against a real event. mi_pramana._verdict_v2
# emits these UPPERCASE. The other two verdicts it can emit are NOT evidence:
#   UNRESOLVED  — window not yet attested complete; the adjudication can still flip
#   FALSE_ALARM — control-window prediction, by construction not a real outcome
# A discovery's n_support counts ATTRIBUTION ASSIGNMENTS across all of these; only
# the adjudicated subset may ever support an 'empirical' evidence grade downstream.
_ADJUDICATED_VERDICTS = frozenset({"CONFIRMED", "PARTIAL", "REFUTED"})

# Default dim weights (C6: authoritative copy in brahma_formula_constants)
_DEFAULT_DIM_WEIGHTS = {
    "timing": 0.30, "magnitude": 0.20, "domain": 0.25,
    "falsifier": 0.15, "manifestation": 0.10,
}


def _load_dim_weights(conn) -> dict[str, float]:
    """Read attribution dimension weights from brahma_formula_constants; fall back to defaults."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(
                "SELECT value_jsonb FROM brahma_formula_constants "
                "WHERE constant_id = 'mi_pariksha_attribution_weights'"
            )
            row = cur.fetchone()
            if row and row[0]:
                return {k: float(v) for k, v in row[0].items()}
    except Exception:
        pass
    return dict(_DEFAULT_DIM_WEIGHTS)


def _table_exists(conn, name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name=%s AND table_schema='public'",
            (name,),
        )
        return cur.fetchone() is not None


@register("mi_pariksha")
class MiParikshaWriter(WriterBase):
    """
    Attribution, retrodiction, QA harness, and discovery miner for L5 calibration data.
    HEAVY: 7 substeps (retrodiction/control_windows/ablation/attribution/neg_control/discovery/tail_only).
    """

    asset_id = "mi_pariksha"
    has_substeps = True

    def plan_substeps(self, ctx) -> list[SubStep]:
        self._chart_id = str(ctx.config["chart_id"])
        return [
            SubStep(key="retrodiction",    label="historical-anchor probe (T−90d cutoff declared, not enforced)"),
            SubStep(key="control_windows", label="≥3 no-event control windows per event"),
            SubStep(key="ablation",        label="per-family marginal skill ablation"),
            SubStep(key="attribution",     label="analytic attribution from lift_vectors"),
            SubStep(key="neg_control",     label="negative-control QA harness"),
            SubStep(key="discovery",       label="pattern discovery mining"),
            SubStep(key="tail_only",       label="tail-only retrodiction (Ranking Doctrine)"),
        ]

    def run_substep(self, ctx, step: SubStep) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id = self._chart_id

        if step.key == "retrodiction":
            return self._substep_retrodiction(conn, chart_id, t0)
        if step.key == "control_windows":
            return self._substep_control_windows(conn, chart_id, t0)
        if step.key == "ablation":
            return self._substep_ablation(conn, chart_id, t0)
        if step.key == "attribution":
            return self._substep_attribution(conn, chart_id, t0)
        if step.key == "neg_control":
            return self._substep_neg_control(conn, chart_id, t0)
        if step.key == "discovery":
            return self._substep_discovery(conn, chart_id, t0)
        if step.key == "tail_only":
            return self._substep_tail_only(conn, chart_id, t0)
        raise ValueError(f"unknown substep: {step.key}")

    # ── retrodiction (BA-P6 Step 2) ──────────────────────────────────────────

    def _substep_retrodiction(self, conn, chart_id: str, t0: float) -> WriterResult:
        """
        Historical-anchor probe. TARGET design (not what runs at build time): for each
        admissible LEL event at date T, apply DATE-FILTERED VIEWS (cutoff T−90d) over
        chart_facts/chart_dashas and run the R-pipeline (promise→activation→anchor v2),
        emitting top-k (event_class, window, posterior).

        WHAT ACTUALLY RUNS at build time (F-143 — stated plainly so no downstream grader
        can mistake it for a backtest): the cutoff is computed but never applied; the query
        below selects up to 3 phala_anchors in the event's domain whose window_start is on
        or before the event date. It does NOT check that the anchor window CONTAINS the
        event, nor that the anchor's event type matches what happened, nor that the anchor
        was derivable from pre-cutoff data only. A row here is therefore a deterministic
        structural probe, not adjudicated evidence — mi_darshana grades this class
        'structural' and can never grade it 'empirical' (see _discovery_evidence_grade).
        """
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT event_id, event_date, domain_primary, event_class_id, event_magnitude "
                "FROM mimamsa_event_provenance "
                "WHERE chart_id = %s AND admissible_clean = true AND held_out = false "
                "  AND event_date IS NOT NULL "
                "ORDER BY event_date",
                (chart_id,),
            )
            events = cur.fetchall()

        if not events:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no admissible events — 0 retrodiction rows")

        # Retrodiction rows go into mimamsa_discoveries with discovery_class='retrodiction'
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mimamsa_discoveries WHERE chart_id = %s "
                "AND discovery_class = 'retrodiction'",
                (chart_id,),
            )

        rows: list[tuple] = []
        for ev in events:
            event_id = ev["event_id"]
            event_date = ev["event_date"]
            cutoff = event_date - timedelta(days=90)

            # Load anchor predictions that were computable with cutoff T−90d
            # (phala_anchors: window_start < event_date AND anchor created before cutoff)
            top_k_anchors: list[dict] = []
            if _table_exists(conn, "phala_anchors"):
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                    cur.execute(
                        "SELECT anchor_id, domain, event_type, posterior, magnitude, "
                        "       window_start, window_end, lift_vector_jsonb "
                        "FROM phala_anchors "
                        "WHERE chart_id = %s "
                        "  AND domain = %s "
                        "  AND window_start <= %s "
                        "  AND posterior IS NOT NULL "
                        "ORDER BY posterior DESC NULLS LAST "
                        "LIMIT 3",
                        (chart_id, ev["domain_primary"], event_date),
                    )
                    top_k_anchors = cur.fetchall()

            retro_id = f"retro_{event_id}"
            top_k_json = json.dumps([
                {
                    "anchor_id": str(a["anchor_id"]),
                    "domain": a["domain"],
                    "posterior": float(a["posterior"]) if a["posterior"] else None,
                    "window_start": str(a["window_start"]),
                    "rank": i + 1,
                    "rank_credit": round(1.0 / math.log2(i + 2), 4),
                }
                for i, a in enumerate(top_k_anchors)
            ])

            has_match = len(top_k_anchors) > 0
            strength = float(top_k_anchors[0]["posterior"]) if has_match and top_k_anchors[0]["posterior"] else 0.0

            rows.append((
                chart_id,
                retro_id,
                "retrodiction",
                # F-143 / §N.7: the old statement read "Blind retrodiction ... with T−90d
                # cutoff {cutoff}", asserting a blinding this code path never performs —
                # `cutoff` is computed and printed but never applied as a filter (the anchor
                # query below filters on domain + window_start only; there are no
                # date-filtered views at build time, as this method's own docstring says).
                # The statement now says what actually ran. A row that claims blinding it
                # did not perform is the same unearned-signal defect one layer up.
                f"Retrodiction probe for {event_id} ({ev['domain_primary']}): "
                f"{len(top_k_anchors)} pre-existing {ev['domain_primary']} anchor(s) had "
                f"opened on or before the event date. "
                f"NOT a blind backtest — the declared T−90d cutoff ({cutoff}) is not applied "
                f"as a filter and an anchor match is not an adjudicated hit.",
                top_k_json,
                round(strength, 4),
                len(top_k_anchors),
                None,   # confidence_band
                "candidate",
                False,
                None,
                RETRODICTION_FORMULA_VER,
            ))

        if not rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no retrodiction rows generated")

        DISC_SQL = """
            INSERT INTO mimamsa_discoveries (
                chart_id, discovery_id, discovery_class, statement, evidence_refs,
                strength, n_support, confidence_band, activation_status,
                citation_required, citation_ref, discovery_formula_ver
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s::numrange,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(DISC_SQL, rows)

        logger.info("[mi_pariksha:retrodiction] %d retrodiction rows for chart %s", len(rows), chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)

    # ── control_windows (BA-P6 Step 2) ───────────────────────────────────────

    def _substep_control_windows(self, conn, chart_id: str, t0: float) -> WriterResult:
        """
        ≥3 same-length no-event windows per event, age-band stratified.
        Emits control window records into mimamsa_qa_eval with check_type='control_window'.
        """
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT event_id, event_date, domain_primary "
                "FROM mimamsa_event_provenance "
                "WHERE chart_id = %s AND admissible_clean = true AND held_out = false "
                "  AND event_date IS NOT NULL "
                "ORDER BY event_date",
                (chart_id,),
            )
            events = cur.fetchall()

        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mimamsa_qa_eval WHERE chart_id = %s AND check_type = 'control_window'",
                (chart_id,),
            )

        if not events:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no events — 0 control windows")

        rows: list[tuple] = []
        known_event_dates = {ev["event_date"] for ev in events}

        for ev in events:
            event_date = ev["event_date"]
            # Offsets for 3 control windows (±365d, ±730d, ±1095d age bands)
            offsets = [365, -365, 730]
            for i, offset_days in enumerate(offsets):
                ctrl_date = event_date + timedelta(days=offset_days)
                # Verify it is a no-event window (no known event within 90 days)
                is_no_event = all(
                    abs((ctrl_date - ed).days) > 90
                    for ed in known_event_dates
                )
                ctrl_id = f"ctrl_{ev['event_id']}_w{i+1}"
                rows.append((
                    chart_id,
                    ctrl_id,
                    "control_window",
                    f"ctrl_{ev['event_id']}",
                    0.5,
                    "control_baseline" if is_no_event else "FAIL_event_too_close",
                    json.dumps({
                        "source_event_id": ev["event_id"],
                        "event_date": str(event_date),
                        "control_date": str(ctrl_date),
                        "offset_days": offset_days,
                        "is_no_event_window": is_no_event,
                        "domain": ev["domain_primary"],
                    }),
                ))

        QA_SQL = """
            INSERT INTO mimamsa_qa_eval (
                chart_id, check_id, check_type, target, result_score, status, detail
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(QA_SQL, rows)

        logger.info("[mi_pariksha:control_windows] %d control window rows for chart %s",
                    len(rows), chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)

    # ── ablation (BA-P6 Step 2) ───────────────────────────────────────────────

    def _substep_ablation(self, conn, chart_id: str, t0: float) -> WriterResult:
        """
        Per-family marginal skill: rerun scoring with each technique family masked.
        Emits ablation result rows into mimamsa_qa_eval with check_type='ablation'.
        """
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT family_id, prior_weight FROM mimamsa_signal_families "
                "WHERE is_active = true AND default_state != 'CONTROL_ONLY'"
            )
            families = cur.fetchall()

        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT composite_score, composite_verdict, score_timing, score_magnitude, "
                "       score_domain, score_falsifier, score_manifestation "
                "FROM mimamsa_calibration WHERE chart_id = %s",
                (chart_id,),
            )
            cal_rows = cur.fetchall()

        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mimamsa_qa_eval WHERE chart_id = %s AND check_type = 'ablation'",
                (chart_id,),
            )

        if not cal_rows or not families:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no calibration rows or families — 0 ablation rows")

        baseline_mean = sum(float(r["composite_score"]) for r in cal_rows) / len(cal_rows)

        rows: list[tuple] = []
        for fam in families:
            family_id = fam["family_id"]
            # Masked mean: exclude the family's contribution (proxy: remove dimension scoring)
            # True ablation requires rerunning the full R-pipeline with family masked.
            # At build time: structural ablation via composite score without family weight.
            masked_scores = []
            for cr in cal_rows:
                score = float(cr.get("composite_score") or 0.5)
                masked_scores.append(score)
            masked_mean = sum(masked_scores) / len(masked_scores) if masked_scores else 0.5
            marginal_skill = round(baseline_mean - masked_mean, 4)

            check_id = f"ablation_{family_id}_{chart_id[:8]}"
            rows.append((
                chart_id,
                check_id,
                "ablation",
                family_id,
                round(masked_mean, 4),
                # masked_scores is a verbatim copy of composite_score (no family is
                # actually masked — true ablation requires a serve-time R-pipeline
                # rerun), so marginal_skill is always exactly 0.0. "pass" here would
                # be indistinguishable from a genuinely-executed ablation check;
                # use a distinct status so mimamsa_qa_eval consumers can't mistake
                # this structural placeholder for a real completed validation.
                "structural_proxy",
                json.dumps({
                    "family_id": family_id,
                    "baseline_mean": round(baseline_mean, 4),
                    "masked_mean": round(masked_mean, 4),
                    "marginal_skill": marginal_skill,
                    "note": "structural_proxy_only; full ablation requires serve-time R-pipeline rerun",
                }),
            ))

        QA_SQL = """
            INSERT INTO mimamsa_qa_eval (
                chart_id, check_id, check_type, target, result_score, status, detail
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(QA_SQL, rows)

        logger.info("[mi_pariksha:ablation] %d ablation rows for chart %s", len(rows), chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)

    # ── attribution ──────────────────────────────────────────────────────────

    def _substep_attribution(self, conn, chart_id: str, t0: float) -> WriterResult:
        """
        Analytic attribution from lift_vectors (BA-P6: catch-all DELETED).
        Empty lift_vectors are excluded, never defaulted to fam_graha_natal.
        """
        dim_weights = _load_dim_weights(conn)

        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT c.match_id, c.prediction_id, "
                "       c.score_timing, c.score_magnitude, c.score_domain, "
                "       c.score_falsifier, c.score_manifestation, "
                "       c.manifestation_channel, c.composite_score, "
                "       p.driving_signals "
                "FROM mimamsa_calibration c "
                "LEFT JOIN mimamsa_predictions p "
                "   ON p.chart_id = c.chart_id AND p.prediction_id = c.prediction_id "
                "WHERE c.chart_id = %s",
                (chart_id,),
            )
            cal_rows = cur.fetchall()

        # Also load lift_vector_jsonb from phala_anchors for each prediction
        anchor_lift: dict[str, dict] = {}
        if _table_exists(conn, "phala_anchors"):
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT anchor_id, lift_vector_jsonb "
                    "FROM phala_anchors WHERE chart_id = %s AND lift_vector_jsonb IS NOT NULL",
                    (chart_id,),
                )
                for r in cur.fetchall():
                    anchor_lift[str(r["anchor_id"])] = r["lift_vector_jsonb"] or {}

        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_attribution WHERE chart_id = %s", (chart_id,))

        if not cal_rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no calibration rows — 0 attribution rows")

        score_cols = {
            "timing": "score_timing",
            "magnitude": "score_magnitude",
            "domain": "score_domain",
            "falsifier": "score_falsifier",
            "manifestation": "score_manifestation",
        }

        rows: list[tuple] = []
        skipped_empty = 0

        for cr in cal_rows:
            match_id = cr["match_id"]
            driving = cr.get("driving_signals") or []
            if isinstance(driving, str):
                try:
                    driving = json.loads(driving)
                except Exception:
                    driving = []

            # BA-P6: catch-all DELETED — exclude empty driving signals (never default)
            if not driving:
                skipped_empty += 1
                continue

            for sig in driving[:10]:
                signal_id = str(sig.get("signal_id") or "unknown")
                family_id = str(sig.get("family_id") or sig.get("signal_id") or "unknown")
                signal_strength = float(sig.get("strength") or 0.0)

                # Lift vector contribution (analytic from posterior model)
                lv = anchor_lift.get(signal_id) or {}
                lv_promise = float(lv.get("promise_lift", 1.0))
                lv_activation = float(lv.get("activation_lift", 1.0))

                for dim in _DIMENSIONS:
                    dim_score = float(cr.get(score_cols[dim]) or 0.0)
                    weight = dim_weights.get(dim, 0.0)
                    # Analytic credit: signal_strength × dim_score × weight × lift_factor
                    lift_factor = (lv_promise * lv_activation) ** 0.5 if lv else 1.0
                    credit = signal_strength * dim_score * weight * lift_factor

                    rows.append((
                        chart_id,
                        match_id,
                        signal_id,
                        family_id,
                        dim,
                        round(credit, 4),
                        cr.get("manifestation_channel") if dim == "manifestation" else None,
                        ATTRIBUTION_FORMULA_VER,
                    ))

        if skipped_empty > 0:
            logger.info("[mi_pariksha:attribution] skipped %d empty driving_signals (no catch-all)",
                        skipped_empty)

        ATT_SQL = """
            INSERT INTO mimamsa_attribution (
                chart_id, match_id, signal_id, family_id, dimension,
                credit_blame, channel_fired, attribution_formula_ver
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """
        BATCH = 1000
        with conn.cursor() as cur:
            for i in range(0, len(rows), BATCH):
                cur.executemany(ATT_SQL, rows[i:i+BATCH])

        logger.info("[mi_pariksha:attribution] %d attribution rows (skipped_empty=%d) for chart %s",
                    len(rows), skipped_empty, chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)

    # ── neg_control ──────────────────────────────────────────────────────────

    def _substep_neg_control(self, conn, chart_id: str, t0: float) -> WriterResult:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT control_id, expected_score, tolerance FROM mimamsa_negative_controls"
            )
            controls = cur.fetchall()

        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mimamsa_qa_eval WHERE chart_id = %s "
                "AND check_type NOT IN ('control_window', 'ablation')",
                (chart_id,),
            )

        if not controls:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no negative controls defined — 0 QA rows")

        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(
                "SELECT AVG(composite_score) FROM mimamsa_calibration WHERE chart_id = %s",
                (chart_id,),
            )
            r = cur.fetchone()
            baseline = float(r[0]) if r and r[0] is not None else 0.5

        # JL-019: this substep does not actually inject a synthetic null input through the
        # scoring engine and compare the result to `expected` — it derives a `null_score`
        # directly from `expected` itself, so the comparison is a tautology that can never
        # fail. Until a real synthetic-injection harness exists, every row is reported
        # `not_implemented` rather than a misleading "pass".
        rows: list[tuple] = []
        for ctrl in controls:
            control_id = ctrl["control_id"]
            expected = ctrl["expected_score"]
            tolerance = float(ctrl["tolerance"])

            check_id = f"neg_{control_id}_{chart_id[:8]}"
            rows.append((
                chart_id,
                check_id,
                "negative_control",
                control_id,
                None,
                "not_implemented",
                json.dumps({"expected": expected, "tolerance": tolerance,
                            "baseline": round(baseline, 4),
                            "reason": "no synthetic-injection harness exists yet — "
                                      "prior status derived null_score from expected "
                                      "itself and could never fail (JL-019)"}),
            ))

        if baseline > 0.0:
            all_same = baseline >= 0.95 or baseline <= 0.05
            rows.append((
                chart_id,
                f"degen_dist_{chart_id[:8]}",
                "degenerate_distribution",
                "composite_score_distribution",
                round(baseline, 4),
                "FAIL" if all_same else "pass",
                json.dumps({"mean_score": round(baseline, 4), "is_degenerate": all_same}),
            ))

        QA_SQL = """
            INSERT INTO mimamsa_qa_eval (
                chart_id, check_id, check_type, target, result_score, status, detail
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(QA_SQL, rows)

        logger.info("[mi_pariksha:neg_control] %d QA rows for chart %s", len(rows), chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)

    # ── discovery ────────────────────────────────────────────────────────────

    def _substep_discovery(self, conn, chart_id: str, t0: float) -> WriterResult:
        # F-143: join the attribution rows to the calibration verdict they came from.
        # An attribution row is an ASSIGNMENT of analytic credit to a signal for one
        # prediction↔event match; it is NOT evidence that an outcome was scored. Only
        # matches with an adjudicated verdict (_ADJUDICATED_VERDICTS) carry that.
        # ORDER BY: the 20-row cap below previously kept whichever groups the unordered
        # scan happened to yield first, so a rebuild could silently swap which discoveries
        # survive. Total ordering makes the cap deterministic.
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT a.signal_id, a.family_id, a.dimension, a.credit_blame, "
                "       a.match_id, c.composite_verdict "
                "FROM mimamsa_attribution a "
                "LEFT JOIN mimamsa_calibration c "
                "  ON c.chart_id = a.chart_id AND c.match_id = a.match_id "
                "WHERE a.chart_id = %s "
                "ORDER BY a.signal_id, a.dimension, a.match_id",
                (chart_id,),
            )
            att_rows = cur.fetchall()

        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mimamsa_discoveries WHERE chart_id = %s "
                "AND discovery_class = 'emergent_law'",
                (chart_id,),
            )

        if not att_rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no attribution data — 0 discoveries")

        sig_dim: dict[tuple, dict] = {}
        for row in att_rows:
            key = (str(row["signal_id"]), row["dimension"])
            agg = sig_dim.setdefault(
                key, {"credits": [], "matches": set(), "scored_matches": set()}
            )
            agg["credits"].append(float(row.get("credit_blame") or 0.0))
            match_id = row.get("match_id")
            if match_id is not None:
                agg["matches"].add(str(match_id))
                verdict = str(row.get("composite_verdict") or "").upper()
                if verdict in _ADJUDICATED_VERDICTS:
                    agg["scored_matches"].add(str(match_id))

        rows: list[tuple] = []
        for (signal_id, dimension), agg in sig_dim.items():
            credits = agg["credits"]
            n = len(credits)
            if n < 3:
                continue
            mean_credit = sum(credits) / n
            if mean_credit < 0.15:
                continue

            # F-143: the two counts mean different things and must never be conflated.
            # n                 — attribution ASSIGNMENTS (this is what n_support stores)
            # n_scored_matches  — distinct prediction↔event matches with an adjudicated
            #                     verdict; the only count that can earn 'empirical'.
            n_matches = len(agg["matches"])
            n_scored = len(agg["scored_matches"])

            discovery_id = f"disc_{signal_id[:20]}_{dimension}"
            statement = (
                f"Signal '{signal_id}' shows consistent {dimension}-dimension credit "
                f"(mean credit={mean_credit:.2f} across {n} attribution assignments "
                f"over {n_matches} prediction-event matches, {n_scored} of them "
                f"outcome-adjudicated). Candidate emergent calibration law."
            )
            conf_lo = max(0.0, mean_credit - 0.15)
            conf_hi = min(1.0, mean_credit + 0.15)

            rows.append((
                chart_id,
                discovery_id,
                "emergent_law",
                statement,
                json.dumps({
                    "signal_id": signal_id,
                    "dimension": dimension,
                    "n": n,
                    "n_support_semantics": (
                        "attribution-assignment rows, NOT independently scored outcomes "
                        "(F-143) — read n_scored_matches for evidence strength"
                    ),
                    "n_distinct_matches": n_matches,
                    "n_scored_matches": n_scored,
                    "adjudicated_verdicts": sorted(_ADJUDICATED_VERDICTS),
                }),
                round(mean_credit, 4),
                n,
                f"[{round(conf_lo,2)},{round(conf_hi,2)})",
                "candidate",
                False,
                None,
                DISCOVERY_FORMULA_VER,
            ))
            if len(rows) >= 20:
                break

        if not rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no patterns above threshold — 0 discoveries")

        DISC_SQL = """
            INSERT INTO mimamsa_discoveries (
                chart_id, discovery_id, discovery_class, statement, evidence_refs,
                strength, n_support, confidence_band, activation_status,
                citation_required, citation_ref, discovery_formula_ver
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s::numrange,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(DISC_SQL, rows)

        logger.info("[mi_pariksha:discovery] %d discovery candidates for chart %s",
                    len(rows), chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)

    # ── tail_only (BA-P6 Step 2 — Ranking Doctrine falsifier) ────────────────

    def _substep_tail_only(self, conn, chart_id: str, t0: float) -> WriterResult:
        """
        Retrodiction over the salience tail alone (MSR signals with salience rank > 70th percentile).
        Tests the Ranking Doctrine: if low-salience signals carry independent skill,
        the attention-budget model needs revision.
        """
        tail_rows: list[dict] = []
        if _table_exists(conn, "bodha_msr_signals"):
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT signal_id, computed_salience "
                    "FROM bodha_msr_signals WHERE chart_id = %s AND computed_salience IS NOT NULL "
                    "ORDER BY computed_salience ASC",
                    (chart_id,),
                )
                all_signals = cur.fetchall()
            # Tail = bottom 30% by salience
            n_tail = max(1, len(all_signals) * 30 // 100)
            tail_rows = all_signals[:n_tail]

        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT composite_score, composite_verdict "
                "FROM mimamsa_calibration WHERE chart_id = %s",
                (chart_id,),
            )
            all_cal = cur.fetchall()

        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mimamsa_qa_eval WHERE chart_id = %s "
                "AND check_type = 'tail_only'",
                (chart_id,),
            )

        tail_signal_ids = {str(r["signal_id"]) for r in tail_rows}
        tail_mean = (
            sum(float(r["composite_score"]) for r in all_cal) / len(all_cal)
            if all_cal else 0.5
        )
        full_mean = tail_mean  # structural proxy at build time

        check_id = f"tail_only_{chart_id[:8]}"
        rows = [(
            chart_id,
            check_id,
            "tail_only",
            f"salience_tail_n={len(tail_signal_ids)}",
            round(tail_mean, 4),
            # full_mean is set verbatim equal to tail_mean (no real tail-vs-full
            # comparison runs at build time), so marginal_skill is always exactly
            # 0.0 — same placeholder shape as _substep_ablation above. "pass"
            # would be indistinguishable from a genuinely-executed comparison.
            "structural_proxy",
            json.dumps({
                "tail_signal_count": len(tail_signal_ids),
                "tail_mean_score": round(tail_mean, 4),
                "full_mean_score": round(full_mean, 4),
                "marginal_skill": round(tail_mean - full_mean, 4),
                "note": "structural_proxy; serve-time enrichment runs R-pipeline on tail signals only",
            }),
        )]

        QA_SQL = """
            INSERT INTO mimamsa_qa_eval (
                chart_id, check_id, check_type, target, result_score, status, detail
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(QA_SQL, rows)

        logger.info("[mi_pariksha:tail_only] %d tail_only rows for chart %s", len(rows), chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)


import math  # noqa: E402 — used by retrodiction
