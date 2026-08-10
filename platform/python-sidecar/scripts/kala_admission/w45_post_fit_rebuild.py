#!/usr/bin/env python3
"""
w45_post_fit_rebuild.py -- GOCHARA-UTKARSA W4.5: post-fit rebuild.

Gate: W4.4 PASS (gochara_v3_calibration table + fitted weights available).

PURPOSE
-------
After W4.4 has fitted per-mechanism weights via cross-chart partial pooling
and stored them in gochara_v3_calibration, this script:

  Stage A -- Loads fitted weights from gochara_v3_calibration (latest
             fitted_at per toggle_key). Missing toggle_key → honest 0.0 (I4).

  Stage B -- Calibration state stamper: UPDATE kala_gochara_windows_v2 SET
             calibration_state = 'empirically_calibrated' for rows belonging
             to either chart, era_slice_key LIKE 'g3_%', and currently at
             'structural_prior'. §N.8: only executes when real fit rows exist.

  Stage C -- Prospective ledger seeding: top 20 forward g3 windows per chart
             (window_end >= today, signed_intensity DESC) → brahma_prospective_ledger
             rows. Idempotent: skips rows already filed for the same
             (chart_id, event_class, observation_window).

  Stage D -- Build report JSON: harness, wave, fitted_weights,
             rows_stamped_empirically_calibrated, prospective_rows_seeded,
             fit_run_ids_used, dataset_hash_linked.

HONESTY CONSTRAINTS
-------------------
I2: ZERO imports from gochara_grammar/*, gochara_intensity/*, ka_gochara_sweep/*.
I4: Empty gochara_v3_calibration → weights all 0.0, no fabrication.
§N.4: Never edit applied migrations (migration 561 already exists — not touched).
§N.8: calibration_state stamping only when at least one fit row exists for the
      chart's era slice in gochara_v3_calibration.

MODEL POLICY: builder (sonnet). Never spawns opus.

Exit codes:
  0 -- report generated successfully
  1 -- computation error (non-DB)
  3 -- DB unavailable / missing DATABASE_URL / psycopg not installed

I2 STATIC CHECK (for test_w45_post_fit_rebuild.py)
---------------------------------------------------
The following import prefixes MUST NOT appear in this module's CODE:
  - services.gochara_grammar
  - services.gochara_intensity
  - services.ka_gochara_sweep
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date, datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Chart IDs ────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
ABHINANDAN_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"

CHART_IDS = (NATIVE_CHART_ID, ABHINANDAN_CHART_ID)

# ── Admitted mechanism toggle_keys (10 total) ─────────────────────────────────

ADMITTED_MECHANISM_IDS: frozenset[str] = frozenset([
    "w21_av_gating",
    "w22_moorti_nirnaya",
    "w23_tara_bala",
    "w24_sade_sati",
    "w25_kota_chakra",
    "w26_real_eclipses",
    "w27_annual_stack",
    "w27a_tajaka_year_lord",
    "w27b_tithi_pravesha",
    "w27c_sudarshana",
])

# ── Constants ─────────────────────────────────────────────────────────────────

GENERATION_V3 = "g3_utkarsha"
TABLE_WINDOWS = "kala_gochara_windows_v2"
TABLE_CALIBRATION = "gochara_v3_calibration"
TABLE_LEDGER = "brahma_prospective_ledger"

# Calibration state values (bridged from lel_calibration.py vocabulary)
STATE_STRUCTURAL_PRIOR = "structural_prior"
STATE_EMPIRICALLY_CALIBRATED = "empirically_calibrated"

# Prospective ledger seeding: top N forward windows per chart.
PROSPECTIVE_TOP_N = 20

# Formula version tag for ledger rows produced by this wave.
FORMULA_VERSION = "gochara_v3_w45"

# Filed by field (required NOT NULL) — identifies this automated seeder.
FILED_BY = "w45_post_fit_rebuild"

# Source citation (required NOT NULL).
SOURCE_CITATION = (
    "GOCHARA-UTKARSA W4.5 automated prospective seeding from "
    "kala_gochara_windows_v2 g3 corpus; weights from gochara_v3_calibration"
)

# Model tag (required NOT NULL on brahma_prospective_ledger).
MODEL_TAG = "gochara_v3_w45_builder"


# ═══════════════════════════════════════════════════════════════════════════
# Stage A — Load fitted weights
# ═══════════════════════════════════════════════════════════════════════════

def load_fitted_weights(conn: Any) -> tuple[dict[str, float], list[str], Optional[str]]:
    """Load fitted weights from gochara_v3_calibration.

    For each toggle_key in ADMITTED_MECHANISM_IDS, SELECT the row with the
    highest fitted_at. Missing toggle_key → honest 0.0 (I4).

    Returns:
        fitted_weights  dict[toggle_key, weight_value]  (all 10 keys present)
        fit_run_ids     list of distinct fit_run_id UUIDs used (as strings)
        dataset_hash    dataset_hash from the latest fit run, or None
    """
    fitted_weights: dict[str, float] = {tk: 0.0 for tk in ADMITTED_MECHANISM_IDS}
    fit_run_ids_seen: list[str] = []
    dataset_hash: Optional[str] = None

    for toggle_key in sorted(ADMITTED_MECHANISM_IDS):
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT weight_value, fit_run_id, fit_provenance
                      FROM {TABLE_CALIBRATION}
                     WHERE toggle_key = %s
                     ORDER BY fitted_at DESC
                     LIMIT 1
                    """,
                    (toggle_key,),
                )
                row = cur.fetchone()
        except Exception as exc:
            logger.warning(
                "[w45] could not query %s for toggle_key=%s: %s — honest 0.0 (I4)",
                TABLE_CALIBRATION, toggle_key, exc,
            )
            row = None

        if row is None:
            logger.debug("[w45] no fitted weight for toggle_key=%s — 0.0 (I4)", toggle_key)
            continue

        # Support both dict and tuple row factories.
        if isinstance(row, dict):
            weight_raw = row.get("weight_value", 0.0)
            fit_run_id = str(row.get("fit_run_id", ""))
            fit_prov = row.get("fit_provenance") or {}
        else:
            weight_raw, fit_run_id, fit_prov = row[0], str(row[1]), row[2] or {}

        # Coerce JSONB if it arrived as a string.
        if isinstance(fit_prov, str):
            try:
                fit_prov = json.loads(fit_prov)
            except (json.JSONDecodeError, TypeError):
                fit_prov = {}

        # I4: non-negative weight (max(0.0, value)).
        fitted_weights[toggle_key] = max(0.0, float(weight_raw) if weight_raw is not None else 0.0)

        if fit_run_id and fit_run_id not in fit_run_ids_seen:
            fit_run_ids_seen.append(fit_run_id)

        # Capture dataset_hash from the latest fit_provenance we encounter.
        if dataset_hash is None and isinstance(fit_prov, dict):
            dataset_hash = fit_prov.get("dataset_hash")

    logger.info(
        "[w45] Stage A: loaded %d fitted weights; fit_run_ids=%s",
        sum(1 for v in fitted_weights.values() if v > 0.0),
        fit_run_ids_seen,
    )
    return fitted_weights, fit_run_ids_seen, dataset_hash


# ═══════════════════════════════════════════════════════════════════════════
# Stage B — Calibration state stamper
# ═══════════════════════════════════════════════════════════════════════════

def stamp_empirically_calibrated(conn: Any, fit_run_ids: list[str]) -> int:
    """UPDATE kala_gochara_windows_v2 SET calibration_state = 'empirically_calibrated'.

    Scoped to:
      chart_id IN (native, abhinandan)
      AND era_slice_key LIKE 'g3_%'
      AND calibration_state = 'structural_prior'

    §N.8 gate: only executes when at least one fit row exists (fit_run_ids is
    non-empty). If no fitted weights were found, returns 0 with a warning —
    never stamps 'empirically_calibrated' for rows whose weights have not been
    computed.

    Returns count of rows updated.
    """
    if not fit_run_ids:
        logger.warning(
            "[w45] Stage B: NO fit_run_ids found in %s — "
            "calibration_state stamping skipped (§N.8: no earned signal).",
            TABLE_CALIBRATION,
        )
        return 0

    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {TABLE_WINDOWS}
                   SET calibration_state = %s
                 WHERE chart_id = ANY(%s)
                   AND era_slice_key LIKE 'g3_%%'
                   AND calibration_state = %s
                """,
                (
                    STATE_EMPIRICALLY_CALIBRATED,
                    list(CHART_IDS),
                    STATE_STRUCTURAL_PRIOR,
                ),
            )
            count = cur.rowcount if hasattr(cur, "rowcount") else 0
    except Exception as exc:
        logger.error("[w45] Stage B: UPDATE failed: %s", exc)
        raise

    logger.info("[w45] Stage B: %d rows stamped '%s'.", count, STATE_EMPIRICALLY_CALIBRATED)
    return count


# ═══════════════════════════════════════════════════════════════════════════
# Stage C — Prospective ledger seeding
# ═══════════════════════════════════════════════════════════════════════════

def _build_confidence(signed_intensity: float) -> float:
    """Compute initial confidence from signed_intensity.

    confidence = min(0.9, max(0.5, 0.5 + signed_intensity * 0.3))
    Clamped to (0.0, 1.0) exclusive per brahma_prospective_ledger CHECK.
    """
    raw = 0.5 + float(signed_intensity) * 0.3
    return min(0.9, max(0.5, raw))


def _build_claim(event_class: str, window_start: date, window_end: date, signed_intensity: float) -> str:
    """Build the claim text for a prospective ledger row."""
    return (
        f"Gochara lambda_v3 elevation forecast: {event_class} window "
        f"{window_start}–{window_end}, signed_intensity={signed_intensity:.3f}"
    )


def _build_falsifier(event_class: str) -> str:
    """Build the falsifier for a prospective ledger row."""
    return (
        f"Window end passes without elevated life event in the tracked event class "
        f"({event_class})"
    )


def _window_already_filed(conn: Any, chart_id: str, event_class: str, window_start: date, window_end: date) -> bool:
    """Check whether a brahma_prospective_ledger row already exists for this window."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT 1 FROM {TABLE_LEDGER}
                 WHERE chart_id = %s
                   AND event_class = %s
                   AND observation_window = daterange(%s, %s)
                 LIMIT 1
                """,
                (chart_id, event_class, window_start, window_end),
            )
            row = cur.fetchone()
        return row is not None
    except Exception as exc:
        # On error, treat as not filed — the INSERT will either succeed or
        # raise a constraint error we can observe, not silently skip.
        logger.debug("[w45] _window_already_filed check failed: %s — assuming not filed", exc)
        return False


def seed_prospective_ledger(conn: Any, today: Optional[date] = None) -> int:
    """Select top forward g3 windows per chart and seed brahma_prospective_ledger.

    AC4: forward windows only (window_end >= today).
    AC5: filing_method = 'explicit_filing_tool' in every INSERT.
    Idempotent: skips rows already filed for (chart_id, event_class, observation_window).

    Returns count of new rows inserted.
    """
    if today is None:
        today = date.today()

    total_seeded = 0

    for chart_id in CHART_IDS:
        # Fetch top PROSPECTIVE_TOP_N forward g3 windows by signed_intensity DESC.
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT event_class,
                           window_start,
                           window_end,
                           signed_intensity
                      FROM {TABLE_WINDOWS}
                     WHERE chart_id = %s
                       AND era_slice_key LIKE 'g3_%%'
                       AND window_end >= %s
                     ORDER BY signed_intensity DESC
                     LIMIT %s
                    """,
                    (chart_id, today, PROSPECTIVE_TOP_N),
                )
                rows = cur.fetchall()
        except Exception as exc:
            logger.error("[w45] Stage C: SELECT windows failed for chart=%s: %s", chart_id, exc)
            raise

        for row in rows:
            if isinstance(row, dict):
                event_class = row["event_class"]
                window_start = row["window_start"]
                window_end = row["window_end"]
                signed_intensity = float(row["signed_intensity"] or 0.0)
            else:
                event_class, window_start, window_end, signed_intensity = (
                    row[0], row[1], row[2], float(row[3] or 0.0)
                )

            # Coerce dates.
            if isinstance(window_start, str):
                window_start = date.fromisoformat(window_start)
            if isinstance(window_end, str):
                window_end = date.fromisoformat(window_end)

            # AC4: paranoid forward-only guard (the WHERE clause already does this,
            # but double-check here for the §N.8 "earned signal" discipline).
            if window_end < today:
                continue

            # Idempotency: skip if already filed.
            if _window_already_filed(conn, chart_id, event_class, window_start, window_end):
                logger.debug(
                    "[w45] Stage C: already filed chart=%s event_class=%s window=%s–%s — skip",
                    chart_id, event_class, window_start, window_end,
                )
                continue

            claim = _build_claim(event_class, window_start, window_end, signed_intensity)
            falsifier = _build_falsifier(event_class)
            confidence = _build_confidence(signed_intensity)

            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {TABLE_LEDGER} (
                            chart_id,
                            claim,
                            event_class,
                            claim_shape,
                            observation_window,
                            model,
                            formula_version,
                            confidence,
                            falsifier,
                            as_of,
                            generator_class,
                            filed_by,
                            filing_method,
                            source_citation
                        ) VALUES (
                            %s, %s, %s, %s,
                            daterange(%s, %s),
                            %s, %s, %s, %s,
                            NOW(),
                            'engine',
                            %s,
                            'explicit_filing_tool',
                            %s
                        )
                        """,
                        (
                            chart_id,
                            claim,
                            event_class,
                            "interval",
                            window_start,
                            window_end,
                            MODEL_TAG,
                            FORMULA_VERSION,
                            confidence,
                            falsifier,
                            FILED_BY,
                            SOURCE_CITATION,
                        ),
                    )
                total_seeded += 1
                logger.debug(
                    "[w45] Stage C: seeded chart=%s event_class=%s window=%s–%s confidence=%.3f",
                    chart_id, event_class, window_start, window_end, confidence,
                )
            except Exception as exc:
                logger.warning(
                    "[w45] Stage C: INSERT failed for chart=%s event_class=%s window=%s–%s: %s",
                    chart_id, event_class, window_start, window_end, exc,
                )

    logger.info("[w45] Stage C: %d prospective rows seeded.", total_seeded)
    return total_seeded


# ═══════════════════════════════════════════════════════════════════════════
# Stage D — Build report
# ═══════════════════════════════════════════════════════════════════════════

def build_post_fit_report(conn: Any) -> dict:
    """Run all four stages and return the W4.5 report dict.

    Caller is responsible for commit/rollback; this function never commits.

    Returns dict with keys:
      harness, wave, fitted_weights, rows_stamped_empirically_calibrated,
      prospective_rows_seeded, fit_run_ids_used, dataset_hash_linked
    """
    # Stage A: load fitted weights.
    fitted_weights, fit_run_ids, dataset_hash = load_fitted_weights(conn)

    # Stage B: stamp empirically_calibrated (§N.8 gate inside the function).
    rows_stamped = stamp_empirically_calibrated(conn, fit_run_ids)

    # Stage C: seed prospective ledger.
    rows_seeded = seed_prospective_ledger(conn)

    # Stage D: report.
    report = {
        "harness": "w45_post_fit_rebuild",
        "wave": "W4.5",
        "fitted_weights": fitted_weights,
        "rows_stamped_empirically_calibrated": rows_stamped,
        "prospective_rows_seeded": rows_seeded,
        "fit_run_ids_used": fit_run_ids,
        "dataset_hash_linked": dataset_hash,
    }
    return report


# ═══════════════════════════════════════════════════════════════════════════
# DB helpers
# ═══════════════════════════════════════════════════════════════════════════

def _require_psycopg():
    """Import psycopg or exit(3)."""
    try:
        import psycopg
        import psycopg.rows
        return psycopg
    except ImportError as exc:
        print(f"ERROR: psycopg unavailable: {exc}", file=sys.stderr)
        sys.exit(3)


def _require_database_url() -> str:
    """Get DATABASE_URL or exit(3)."""
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print(
            "ERROR: DATABASE_URL environment variable is required. "
            "Set it to a valid PostgreSQL connection string.",
            file=sys.stderr,
        )
        sys.exit(3)
    return dsn


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    dsn = _require_database_url()
    psycopg = _require_psycopg()

    try:
        with psycopg.connect(dsn, row_factory=psycopg.rows.dict_row) as conn:
            report = build_post_fit_report(conn)
            conn.commit()
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: w45 post-fit rebuild failed: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()


__all__ = [
    "ADMITTED_MECHANISM_IDS",
    "CHART_IDS",
    "FORMULA_VERSION",
    "GENERATION_V3",
    "NATIVE_CHART_ID",
    "ABHINANDAN_CHART_ID",
    "STATE_EMPIRICALLY_CALIBRATED",
    "STATE_STRUCTURAL_PRIOR",
    "build_post_fit_report",
    "load_fitted_weights",
    "seed_prospective_ledger",
    "stamp_empirically_calibrated",
]
