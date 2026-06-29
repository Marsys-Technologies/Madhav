"""
mi_pramana — Prediction-Event Matcher + Calibration Scorecard (L5 Mīmāṃsā)
===========================================================================
HEAVY writer: three substeps per chart:
  1. "match"       — temporal + domain match predictions → clean events
  2. "score"       — multi-dim scoring (timing/magnitude/domain/falsifier/mfn)
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

SCORING_FORMULA_VERSION = "mi_pramana_v1.0"
CALIBRATION_FORMULA_VER = "mi_pramana_v1.0"

# Sentinel flags: True means the corresponding scoring function is a stub pending
# real LEL calibration / outcome data.  Set to False only when a real implementation
# replaces the stub.  These flags are checked by tests to ensure stubs remain
# visible and cannot be mistaken for production scoring logic.
_IS_STUB_FALSIFIER: bool = True        # _score_falsifier: awaiting falsifier JSON standardization
_IS_STUB_MANIFESTATION: bool = True    # _score_manifestation: awaiting outcome channel data

logger.debug(
    "mi_pramana: _score_falsifier + _score_manifestation are stubs "
    "(n=0 outcomes; _IS_STUB_FALSIFIER=%s, _IS_STUB_MANIFESTATION=%s)",
    _IS_STUB_FALSIFIER,
    _IS_STUB_MANIFESTATION,
)

# Scoring weights (must sum to 1.0)
_W_TIMING = 0.30
_W_MAGNITUDE = 0.20
_W_DOMAIN = 0.25
_W_FALSIFIER = 0.15
_W_MANIFESTATION = 0.10


def _score_timing(window_str: str, event_date: date) -> float:
    """Score timing: 1.0 if event falls in center 50%, decays toward edges."""
    try:
        # Parse psycopg DateRange — may be object or string
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
    scale = ["minor", "moderate", "major", "rupture"]
    if not actual:
        return 0.5  # unknown
    try:
        ei = scale.index(expected.lower())
        ai = scale.index(actual.lower())
        diff = abs(ei - ai)
        return max(0.0, 1.0 - diff * 0.5)
    except ValueError:
        return 0.5


def _score_domain(pred_domain: str, event_domain: str) -> float:
    return 1.0 if pred_domain == event_domain else 0.0


def _score_falsifier(falsifier_jsonb: Any, event: dict) -> float:
    """
    STUB (_IS_STUB_FALSIFIER = True): always returns 1.0.

    A real implementation would evaluate the structured falsifier_jsonb conditions
    against the event and return 0.0 if any falsifier condition is met (prediction
    denied), or 1.0 if all falsifier conditions pass.

    Pending: falsifier JSON structure not yet standardized across mimamsa_predictions.
    Replace this stub and set _IS_STUB_FALSIFIER = False once the schema is settled
    and LEL calibration data is available.
    """
    # STUB: always 1.0 until LEL calibration data + falsifier schema available
    return 1.0


def _score_manifestation(manifestation_channels: list[str], event: dict) -> tuple[float, str | None]:
    """
    STUB (_IS_STUB_MANIFESTATION = True): always returns (0.5, None).

    A real implementation would check which channel in manifestation_channels
    matches the event's observed channel and return a non-uniform propensity score.

    Pending: outcome channel data (mimamsa_manifestation_grammar) needed for
    empirical propensity; replace stub and set _IS_STUB_MANIFESTATION = False
    once n_support >= 5 for at least one channel.
    """
    # STUB: always 0.5 (unknown channel) until outcome data available
    return 0.5, None


def _composite(t: float, m: float, d: float, f: float, mfn: float) -> float:
    return (
        _W_TIMING * t
        + _W_MAGNITUDE * m
        + _W_DOMAIN * d
        + _W_FALSIFIER * f
        + _W_MANIFESTATION * mfn
    )


def _verdict(score: float, falsifier_score: float) -> str:
    if falsifier_score < 0.1:
        return "denied"
    if score >= 0.65:
        return "confirmed"
    if score >= 0.35:
        return "partial"
    return "denied"


def _table_exists(conn, name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name=%s AND table_schema='public'",
            (name,),
        )
        return cur.fetchone() is not None


@register("mi_pramana")
class MiPramanaWriter(WriterBase):
    """
    Matches predictions against clean life events and produces calibration scores.
    HEAVY: match → score → reliability (3 substeps).
    """

    asset_id = "mi_pramana"
    has_substeps = True

    def plan_substeps(self, ctx) -> list[SubStep]:
        self._chart_id = ctx.config["chart_id"]
        return [
            SubStep(key="match", label="match predictions to events"),
            SubStep(key="score", label="multi-dim scoring"),
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

        # Load predictions for this chart
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT * FROM mimamsa_predictions WHERE chart_id = %s "
                "AND lifecycle_status != 'pending'",
                (chart_id,),
            )
            # Note: on first run all are 'pending' — use all predictions
            preds = cur.fetchall()

        if not preds:
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

        # Store matches on self for score substep
        self._matches: list[dict] = []
        for pred in preds:
            window = pred["observation_window"]
            pred_domain = pred["domain"]
            for ev in events:
                ev_date = ev.get("event_date")
                if not ev_date:
                    continue
                # Check temporal overlap
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
                self._matches.append({
                    "pred": dict(pred),
                    "event": dict(ev),
                })

        logger.info("[mi_pramana:match] %d matches for chart %s", len(self._matches), chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                            duration_seconds=time.time() - t0)

    # ── substep: score ───────────────────────────────────────────────────────

    def _substep_score(self, conn, chart_id: str, t0: float) -> WriterResult:
        matches = getattr(self, "_matches", [])

        # Idempotency: delete prior calibration rows
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_calibration WHERE chart_id = %s", (chart_id,))

        if not matches:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no matches — 0 calibration rows")

        # Load manifestation channels for this chart
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
        for i, m in enumerate(matches):
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
            s_falsifier = _score_falsifier(pred.get("falsifier_jsonb"), ev)
            channels = mfn_channels.get(prediction_id, [])
            s_mfn, ch_fired = _score_manifestation(channels, ev)

            composite = _composite(s_timing, s_magnitude, s_domain, s_falsifier, s_mfn)
            verdict = _verdict(composite, s_falsifier)

            # Admissibility
            leakage = "clean" if ev.get("admissible_clean") and not ev.get("held_out") else "held_out"

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
                1,      # n_for_stratum placeholder
                leakage,
                SCORING_FORMULA_VERSION,
            ))

        CAL_SQL = """
            INSERT INTO mimamsa_calibration (
                chart_id, match_id, prediction_id, event_id,
                score_timing, score_magnitude, score_domain, score_falsifier, score_manifestation,
                manifestation_channel, composite_verdict, composite_score,
                base_rate_adjusted_skill, evidence_admissibility, n_for_stratum,
                leakage_status, scoring_formula_version
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        with conn.cursor() as cur:
            cur.executemany(CAL_SQL, rows)
            rows_inserted = len(rows)  # psycopg3 executemany rowcount is -1 (undefined)

        logger.info("[mi_pramana:score] %d calibration rows for chart %s", rows_inserted, chart_id)
        return WriterResult(asset_id=self.asset_id, rows_inserted=rows_inserted,
                            duration_seconds=time.time() - t0)

    # ── substep: reliability ─────────────────────────────────────────────────

    def _substep_reliability(self, conn, chart_id: str, t0: float) -> WriterResult:
        # Load all calibration rows for this chart
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT composite_score, composite_verdict FROM mimamsa_calibration WHERE chart_id = %s",
                (chart_id,),
            )
            cal_rows = cur.fetchall()

        # Idempotency: delete prior reliability rows
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mimamsa_reliability WHERE chart_id = %s", (chart_id,))

        if not cal_rows:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                duration_seconds=time.time() - t0,
                                notes="no calibration rows — 0 reliability rows")

        # Compute reliability by probability bin (10 bins: 0-0.1, 0.1-0.2, ...)
        bins: dict[str, list] = {}
        bin_size = 0.1
        for cr in cal_rows:
            score = float(cr["composite_score"])
            verdict = cr["composite_verdict"]
            lo = math.floor(score / bin_size) * bin_size
            hi = lo + bin_size
            key = f"[{round(lo,1)},{round(hi,1)})"
            bins.setdefault(key, []).append((score, verdict == "confirmed"))

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

            validity = "pass" if n >= 10 else "insufficient_n"
            grade = "empirical" if n >= 5 else "prior_only"

            rows.append((
                chart_id,
                f"domain_all|{stratum_key}",
                f"[{prob_lo},{prob_hi})",
                observed,
                n,
                None, None,   # ci_low, ci_high
                brier,
                None,         # log_loss
                None,         # ece
                observed,     # hit_rate_by_tier approximation
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
