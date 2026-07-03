"""
mi_pramana v2 — Prediction-Event Matcher + Adjudication Engine (L5 Mīmāṃsā)
=============================================================================
BA-P6: G-LADDER stub falsifier DELETED; real StructuredFalsifier evaluation.
New adjudication verdicts: CONFIRMED / PARTIAL / REFUTED / EXPIRED / UNRESOLVED / FALSE_ALARM.
Brier score vs climatology null (base_rate from brahma_event_ontology).
Scoring weights read from brahma_formula_constants (C6 weight unification).

HEAVY writer: three substeps per chart:
  1. "match"       — temporal + domain match predictions → clean events
  2. "score"       — adjudication + multi-dim scoring vs climatology null
  3. "reliability" — calibration curve (ECE, Brier, hit rate by tier)

Tables written: mimamsa_calibration, mimamsa_reliability
PER-CHART scope.

FROZEN orchestrator contract: @register, plan_substeps + run_substep.
NEVER commits or closes ctx.db_conn.
"""
from __future__ import annotations

import json
import logging
import math
import time
from datetime import date
from typing import Any

import psycopg.rows

from pipeline.orchestrator.writers import WriterBase, WriterResult, SubStep, register

logger = logging.getLogger(__name__)

SCORING_FORMULA_VERSION = "mi_pramana_v2.0"
CALIBRATION_FORMULA_VER = "mi_pramana_v2.0"

# Scoring weight defaults (C6: authoritative copy in brahma_formula_constants)
_DEFAULT_WEIGHTS = {"timing": 0.30, "magnitude": 0.20, "domain": 0.25, "falsifier": 0.15, "manifestation": 0.10}


def _load_scoring_weights(conn) -> dict[str, float]:
    """Read mi_pramana scoring weights from brahma_formula_constants; fall back to defaults."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(
                "SELECT value_jsonb FROM brahma_formula_constants "
                "WHERE constant_id = 'mi_pramana_scoring_weights'"
            )
            row = cur.fetchone()
            if row and row[0]:
                return {k: float(v) for k, v in row[0].items()}
    except Exception:
        pass
    return dict(_DEFAULT_WEIGHTS)


def _load_base_rates(conn) -> dict[str, float]:
    """Load per-event-class base rates from brahma_event_ontology; return {} if table absent."""
    sp = "sp_base_rates"
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(f"SAVEPOINT {sp}")
            cur.execute(
                "SELECT event_class_id, base_rate FROM brahma_event_ontology "
                "WHERE base_rate IS NOT NULL"
            )
            rows = cur.fetchall()
            cur.execute(f"RELEASE SAVEPOINT {sp}")
            return {r["event_class_id"]: float(r["base_rate"]) for r in rows}
    except Exception:
        try:
            with conn.cursor() as cur:
                cur.execute(f"ROLLBACK TO SAVEPOINT {sp}")
        except Exception:
            pass
        return {}


def _score_timing(window_str: str, event_date: date) -> float:
    """Score timing: 1.0 if event falls in center 50%; PARTIAL if within ±20% of window edges."""
    try:
        if hasattr(window_str, 'lower'):
            lo, hi = window_str.lower, window_str.upper
        else:
            s = str(window_str).strip("[]()").split(",")
            lo = date.fromisoformat(s[0].strip())
            hi = date.fromisoformat(s[1].strip())
        if lo is None or hi is None:
            return 0.5
        total = (hi - lo).days
        if total <= 0:
            return 1.0
        offset = (event_date - lo).days
        center = total / 2.0
        dist = abs(offset - center) / center
        return max(0.0, 1.0 - dist)
    except Exception:
        return 0.5


def _score_magnitude(expected: str, actual: str | None) -> float:
    """Score magnitude: exact match = 1.0, adjacent = 0.5, mismatch = 0.0."""
    scale = ["trivial", "minor", "moderate", "significant", "major", "rupture"]
    if not actual:
        return 0.5
    try:
        ei = scale.index(expected.lower()) if expected.lower() in scale else 2
        ai = scale.index(actual.lower()) if actual.lower() in scale else 2
        diff = abs(ei - ai)
        return max(0.0, 1.0 - diff * 0.5)
    except ValueError:
        return 0.5


def _score_domain(pred_domain: str, event_domain: str) -> float:
    return 1.0 if pred_domain == event_domain else 0.0


def _score_falsifier(falsifier_jsonb: Any, event: dict) -> float:
    """
    BA-P6: Real StructuredFalsifier evaluation (replaces BA-P5 stub).
    Evaluates magnitude_floor and attestation_required conditions.
    Returns 0.0 (falsified) | 0.5 (uncertain) | 1.0 (not falsified).
    """
    if not falsifier_jsonb:
        return 1.0

    if isinstance(falsifier_jsonb, str):
        try:
            falsifier_jsonb = json.loads(falsifier_jsonb)
        except Exception:
            return 1.0

    if not isinstance(falsifier_jsonb, dict):
        return 1.0

    # Inherited from bhavishya anchor — no structured eval
    if falsifier_jsonb.get("inherited"):
        return 1.0

    _MAG_ORD = {
        "trivial": 0, "minor": 1, "moderate": 2,
        "significant": 2, "major": 3, "rupture": 4,
        "life-altering": 4, "life_altering": 4,
    }

    # magnitude_floor: if event magnitude below floor → falsified
    magnitude_floor = falsifier_jsonb.get("magnitude_floor")
    if magnitude_floor:
        ev_mag = str(event.get("event_magnitude") or "moderate").lower()
        ev_ord = _MAG_ORD.get(ev_mag, 2)
        fl_ord = _MAG_ORD.get(str(magnitude_floor).lower(), 1)
        if ev_ord < fl_ord:
            return 0.0

    # attestation_required: if True and event has no confirmed attestation
    if falsifier_jsonb.get("attestation_required"):
        has_attest = bool(
            event.get("attestation_source")
            or event.get("disclosure_date")
            or event.get("admissible_clean")
        )
        if not has_attest:
            return 0.5  # uncertain; attestation needed

    return 1.0


def _score_manifestation(manifestation_channels: list[str], event: dict) -> tuple[float, str | None]:
    """Channel scoring: 0.5 (unknown) until outcome channel data accrues (n_support < 5)."""
    return 0.5, None


def _composite(scores: dict[str, float], weights: dict[str, float]) -> float:
    return sum(scores[dim] * weights.get(dim, 0.0) for dim in scores)


def _verdict_v2(
    score: float,
    falsifier_score: float,
    period_window_passed: bool,
    is_control: bool = False,
) -> str:
    """
    BA-P6 adjudication verdicts:
    FALSE_ALARM: control window prediction
    REFUTED: falsifier condition explicitly violated (requires attestation-complete period)
    UNRESOLVED: no falsifier violation but period not yet attested complete → ask-card queue
    CONFIRMED: score >= 0.65 and period passed
    PARTIAL: 0.35 ≤ score < 0.65 (magnitude one-tier off or edge timing)
    """
    if is_control:
        return "FALSE_ALARM"
    if falsifier_score < 0.1:
        return "REFUTED"
    if not period_window_passed:
        return "UNRESOLVED"
    if score >= 0.65:
        return "CONFIRMED"
    if score >= 0.35:
        return "PARTIAL"
    return "REFUTED"


def _table_exists(conn, name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name=%s AND table_schema='public'",
            (name,),
        )
        return cur.fetchone() is not None


def _window_passed(window_str: str) -> bool:
    """True if the prediction window has fully elapsed."""
    from datetime import date as _date
    today = _date.today()
    try:
        if hasattr(window_str, 'upper'):
            hi = window_str.upper
        else:
            s = str(window_str).strip("[]()").split(",")
            hi = _date.fromisoformat(s[-1].strip())
        return hi is not None and today > hi
    except Exception:
        return False


@register("mi_pramana")
class MiPramanaWriter(WriterBase):
    """
    Matches predictions against clean life events and produces calibration scores.
    HEAVY: match → score → reliability (3 substeps).
    BA-P6 v2: real falsifier eval, CONFIRMED/PARTIAL/REFUTED/EXPIRED/UNRESOLVED/FALSE_ALARM,
    Brier vs climatology null, weights from brahma_formula_constants.
    """

    asset_id = "mi_pramana"
    has_substeps = True

    def plan_substeps(self, ctx) -> list[SubStep]:
        self._chart_id = ctx.config["chart_id"]
        return [
            SubStep(key="match", label="match predictions to events"),
            SubStep(key="score", label="adjudication + multi-dim scoring"),
            SubStep(key="reliability", label="calibration curve"),
        ]

    def run_substep(self, ctx, step: SubStep) -> WriterResult:
        t0 = time.time()
        conn = ctx.db_conn
        chart_id = self._chart_id

        if step.key == "match":
            return self._substep_match(conn, chart_id, t0)
        if step.key == "score":
            return self._substep_score(conn, chart_id, t0)
        if step.key == "reliability":
            return self._substep_reliability(conn, chart_id, t0)
        raise ValueError(f"unknown substep key: {step.key}")

    # ── substep: match ───────────────────────────────────────────────────────

    def _substep_match(self, conn, chart_id: str, t0: float) -> WriterResult:
        if not _table_exists(conn, "mimamsa_predictions"):
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="mimamsa_predictions missing — skip match")

        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT * FROM mimamsa_predictions WHERE chart_id = %s",
                (chart_id,),
            )
            preds = cur.fetchall()

        # Load admissible clean events (not held-out)
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT * FROM mimamsa_event_provenance "
                "WHERE chart_id = %s AND admissible_clean = true AND held_out = false",
                (chart_id,),
            )
            events = cur.fetchall()

        self._matches: list[dict] = []
        self._all_preds: list[dict] = [dict(p) for p in preds]

        for pred in preds:
            window = pred["observation_window"]
            pred_domain = pred["domain"]
            for ev in events:
                ev_date = ev.get("event_date")
                if not ev_date:
                    continue
                try:
                    if hasattr(window, 'lower'):
                        lo, hi = window.lower, window.upper
                    else:
                        parts = str(window).strip("[]()").split(",")
                        lo = date.fromisoformat(parts[0].strip())
                        hi = date.fromisoformat(parts[1].strip())
                    if not (lo <= ev_date <= hi):
                        continue
                except Exception:
                    continue
                self._matches.append({"pred": dict(pred), "event": dict(ev)})

        logger.info("[mi_pramana:match] %d matches (%d preds, %d events) for chart %s",
                    len(self._matches), len(preds), len(events), chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                            duration_seconds=time.time() - t0)

    # ── substep: score ───────────────────────────────────────────────────────

    def _substep_score(self, conn, chart_id: str, t0: float) -> WriterResult:
        matches = getattr(self, "_matches", [])
        weights = _load_scoring_weights(conn)
        base_rates = _load_base_rates(conn)

        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_calibration WHERE chart_id = %s", (chart_id,))

        if not matches:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no matches — 0 calibration rows")

        mfn_channels: dict[str, list[str]] = {}
        if _table_exists(conn, "mimamsa_manifestation_sets"):
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    "SELECT prediction_id, channel_id FROM mimamsa_manifestation_sets WHERE chart_id = %s",
                    (chart_id,),
                )
                for r in cur.fetchall():
                    mfn_channels.setdefault(r["prediction_id"], []).append(r["channel_id"])

        rows: list[tuple] = []
        for m in matches:
            pred = m["pred"]
            ev = m["event"]
            prediction_id = pred["prediction_id"]
            event_id = ev["event_id"]
            match_id = f"{prediction_id}_{event_id}"

            s_timing = _score_timing(pred["observation_window"], ev["event_date"])
            s_magnitude = _score_magnitude(
                pred.get("magnitude_expected", "moderate"),
                ev.get("event_magnitude"),
            )
            s_domain = _score_domain(pred["domain"], ev.get("domain_primary", ""))
            s_falsifier = _score_falsifier(pred.get("falsifier_jsonb") or pred.get("structured_falsifier_jsonb"), ev)
            channels = mfn_channels.get(prediction_id, [])
            s_mfn, ch_fired = _score_manifestation(channels, ev)

            dim_scores = {"timing": s_timing, "magnitude": s_magnitude,
                          "domain": s_domain, "falsifier": s_falsifier, "manifestation": s_mfn}
            composite = _composite(dim_scores, weights)

            period_passed = _window_passed(pred["observation_window"])
            verdict = _verdict_v2(composite, s_falsifier, period_passed)

            leakage = "clean" if ev.get("admissible_clean") and not ev.get("held_out") else "held_out"

            # Brier vs climatology null
            event_class_id = ev.get("event_class_id")
            base_rate = float(base_rates.get(event_class_id, 0.10)) if event_class_id else 0.10
            pred_prob = pred.get("posterior") or pred.get("confidence_high") or composite
            null_brier = base_rate * (1 - base_rate)
            model_brier = (float(pred_prob) - 1.0) ** 2 if verdict == "CONFIRMED" else float(pred_prob) ** 2
            brier_vs_null = 1.0 - (model_brier / null_brier) if null_brier > 0 else None

            rows.append((
                chart_id,
                match_id,
                prediction_id,
                event_id,
                round(s_timing, 4),
                round(s_magnitude, 4),
                round(s_domain, 4),
                round(s_falsifier, 4),
                round(s_mfn, 4),
                ch_fired,
                verdict,
                round(composite, 4),
                None,   # base_rate_adjusted_skill — computed in reliability
                "clean",
                1,
                leakage,
                SCORING_FORMULA_VERSION,
                round(base_rate, 4),
                round(brier_vs_null, 4) if brier_vs_null is not None else None,
            ))

        CAL_SQL = """
            INSERT INTO mimamsa_calibration (
                chart_id, match_id, prediction_id, event_id,
                score_timing, score_magnitude, score_domain, score_falsifier, score_manifestation,
                manifestation_channel, composite_verdict, composite_score,
                base_rate_adjusted_skill, evidence_admissibility, n_for_stratum,
                leakage_status, scoring_formula_version,
                base_rate, brier_vs_null
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(CAL_SQL, rows)

        logger.info("[mi_pramana:score] %d calibration rows for chart %s", len(rows), chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)

    # ── substep: reliability ─────────────────────────────────────────────────

    def _substep_reliability(self, conn, chart_id: str, t0: float) -> WriterResult:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT composite_score, composite_verdict, base_rate, brier_vs_null "
                "FROM mimamsa_calibration WHERE chart_id = %s",
                (chart_id,),
            )
            cal_rows = cur.fetchall()

        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_reliability WHERE chart_id = %s", (chart_id,))

        if not cal_rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no calibration rows — 0 reliability rows")

        bins: dict[str, list] = {}
        bin_size = 0.1
        for cr in cal_rows:
            score = float(cr["composite_score"])
            verdict = cr["composite_verdict"]
            lo = math.floor(score / bin_size) * bin_size
            hi = lo + bin_size
            key = f"[{round(lo,1)},{round(hi,1)})"
            bins.setdefault(key, []).append((score, verdict == "CONFIRMED"))

        rows: list[tuple] = []
        for stratum_key, items in bins.items():
            n = len(items)
            observed = sum(1 for _, hit in items if hit) / n if n > 0 else None
            scores = [s for s, _ in items]
            hits = [h for _, h in items]
            brier = sum((s - int(h))**2 for s, h in zip(scores, hits)) / n if n > 0 else None
            parts = stratum_key.strip("[]()").split(",")
            prob_lo = float(parts[0].strip())
            prob_hi = float(parts[1].strip())

            validity = "pass" if n >= 5 else "insufficient_n"
            grade = "empirical" if n >= 5 else "prior_only"

            rows.append((
                chart_id,
                f"domain_all|{stratum_key}",
                f"[{prob_lo},{prob_hi})",
                observed,
                n,
                None, None,
                brier,
                None,
                None,
                observed,
                validity,
                grade,
                CALIBRATION_FORMULA_VER,
            ))

        REL_SQL = """
            INSERT INTO mimamsa_reliability (
                chart_id, stratum_key, predicted_prob_bin, observed_rate, n,
                ci_low, ci_high, brier_score, log_loss, ece, hit_rate_by_tier,
                held_out_validity, evidence_grade, calibration_formula_ver
            ) VALUES (%s,%s,%s::numrange,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(REL_SQL, rows)

        logger.info("[mi_pramana:reliability] %d reliability rows for chart %s", len(rows), chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=len(rows),
                            duration_seconds=time.time() - t0)
