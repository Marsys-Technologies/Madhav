"""ka_gochara_v3_century_materialize — W3.4 Century horizon + slice receipts.

GOCHARA-UTKARSA campaign, wave W3.4.

Gate: W0.3 PASS (generation schema + utkarsha_builder role in place) +
      W3.2 PASS (interval_solver root-solved threshold crossings).

PURPOSE
-------
Extends the W0.2/W2G materializer concept to a CENTURY-SCALE HEAVY writer
using the gochara_v3 engine (not v1's gochara_intensity grammar). The
unit of work is one (event_class × decade_era_slice) pair — 60 substeps
for 6 event classes × 10 decade slices spanning the native's century from
birth (1984-02-05 to 2084-02-05).

Key behaviours:
  1. plan_substeps — returns 60 SubStep objects, one per
     (event_class, decade_slice). substep_key = '{event_class}::{era_slice_key}'.
  2. run_substep — for each substep:
       a. Compute a delta fingerprint from (event_class, era_slice_key,
          ENGINE_VERSION, resonance_targets) via MD5.
       b. Check kala_gochara_v2_build_state for a matching stored fingerprint.
       c. If fingerprint unchanged AND rows exist: skip (honest no-op).
       d. Else: call find_threshold_crossings from gochara_v3.interval_solver
          over the decade JD range; DELETE-then-INSERT results into
          kala_gochara_windows_v2 with era_slice_key set.
       e. Upsert fingerprint to kala_gochara_v2_build_state.
       f. Log wall-clock time per substep at DEBUG level (AC5 / first SLO
          evidence point).
  3. I2 constraint: ZERO imports from gochara_grammar/*, gochara_intensity/*,
     or ka_gochara_sweep/*. All scoring comes from gochara_v3.interval_solver
     and gochara_v3.engine (AC6).
  4. I4 constraint: empty resonance targets → honest 0 rows for that substep,
     no fabrication (AC7).

TABLES
------
Write target:  kala_gochara_windows_v2  (own surface, never touches the
               protected kala_gochara_windows v1 table)
Build state:   kala_gochara_v2_build_state  (substep-keyed fingerprint)

FROZEN ORCHESTRATOR CONTRACT (§N.2)
------------------------------------
  * @register('ka_gochara_v3_century_materialize')  on a WriterBase subclass
  * HEAVY: plan_substeps(ctx) + run_substep(ctx, step)
  * ctx.db_conn — writer reads/writes on it, NEVER commits or closes it
  * Never writes asset_throughput

IDEMPOTENCY (§N.3)
------------------
Delete-then-INSERT scoped to (chart_id × event_class × generation='g3_utkarsha'
× era_slice_key) against kala_gochara_windows_v2 ONLY.

I2 STATIC CHECK (for test_w34_century_horizon.py)
---------------------------------------------------
The following import prefixes MUST NOT appear in this module's CODE
(they are named in the module docstring only for documentation):
  - services.gochara_grammar
  - services.gochara_intensity
  - services.ka_gochara_sweep
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)

# gochara_v3 imports only (I2: no gochara_grammar/*, gochara_intensity/*, ka_gochara_sweep/*)
from services.gochara_v3.interval_solver import find_threshold_crossings, IntervalBoundary
from services.gochara_v3.threshold import ThresholdConfig
from services.gochara_v3.context import ClassContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ASSET_ID = "ka_gochara_v3_century_materialize"

# Generation label for all rows this writer produces.
GENERATION_V3 = "g3_utkarsha"

# Engine version for fingerprinting.  Bumped whenever the scoring engine
# changes in a way that would move a stored window.  gochara_v3/__init__.py
# exports GRAMMAR_VERSION; we use our own constant so this writer's
# fingerprint is stable across internal gochara_v3 refactors that do NOT
# move window positions.
ENGINE_VERSION = "v3.0"

# The 6 event classes this writer handles (same as W0.2 materializer).
EVENT_CLASSES = [
    "career_advancement",
    "major_gain",
    "marriage",
    "illness_acute",
    "chronic_onset",
    "surgery",
]

# Julian Day for 1984-02-05 00:00 UTC (native birth date).
# JD = 2445736.5  (standard astronomical reference).
BIRTH_JD: float = 2445736.5

# Birth year for decade-slice labelling.
BIRTH_YEAR: int = 1984

# Number of decade slices in a century build.
DECADE_COUNT: int = 10

# Days per Julian year (standard astronomical).
DAYS_PER_YEAR: float = 365.25

# Table constants (this writer's own surface; v1 protected table is never named).
TABLE = "kala_gochara_windows_v2"
BUILD_STATE_TABLE = "kala_gochara_v2_build_state"

# INSERT template for kala_gochara_windows_v2.
INSERT_SQL = f"""
    INSERT INTO {TABLE}
      (chart_id, event_class, temporal_shape,
       window_start, window_end, peak_date,
       milestone_id, is_irreversibility_milestone,
       signed_intensity, raw_intensity, valence, is_adverse,
       active_sentences, contributing_systems, suppression_state,
       peak_basis, calibration_state, source, generation, era_slice_key)
    VALUES
      (%(chart_id)s, %(event_class)s, %(temporal_shape)s,
       %(window_start)s, %(window_end)s, %(peak_date)s,
       %(milestone_id)s, %(is_irreversibility_milestone)s,
       %(signed_intensity)s, %(raw_intensity)s, %(valence)s, %(is_adverse)s,
       %(active_sentences)s::jsonb, %(contributing_systems)s::jsonb,
       %(suppression_state)s::jsonb,
       %(peak_basis)s, %(calibration_state)s, %(source)s,
       %(generation)s, %(era_slice_key)s)
"""


# ---------------------------------------------------------------------------
# Decade-slice helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DecadeSlice:
    """One 10-year era slice in the century build.

    Fields
    ------
    era_slice_key   'g3_{year_start}_{year_end}', e.g. 'g3_1984_1994'.
    start_jd        Julian Day for the start of the decade (birth anniversary).
    end_jd          Julian Day for the end of the decade (next decade's start).
    year_start      Calendar year label for the slice start.
    year_end        Calendar year label for the slice end.
    """
    era_slice_key: str
    start_jd: float
    end_jd: float
    year_start: int
    year_end: int


def build_decade_slices() -> list[DecadeSlice]:
    """Return 10 DecadeSlice objects covering the century from BIRTH_JD.

    Slice boundaries are exact Julian Days computed as:
        start_jd = BIRTH_JD + decade_index × 10 × DAYS_PER_YEAR
        end_jd   = BIRTH_JD + (decade_index + 1) × 10 × DAYS_PER_YEAR

    Labels use calendar years: 'g3_{BIRTH_YEAR + 0}_{BIRTH_YEAR + 10}',
    'g3_{BIRTH_YEAR + 10}_{BIRTH_YEAR + 20}', …

    Returns exactly DECADE_COUNT = 10 slices.
    """
    slices: list[DecadeSlice] = []
    for i in range(DECADE_COUNT):
        year_start = BIRTH_YEAR + i * 10
        year_end = BIRTH_YEAR + (i + 1) * 10
        start_jd = BIRTH_JD + i * 10 * DAYS_PER_YEAR
        end_jd = BIRTH_JD + (i + 1) * 10 * DAYS_PER_YEAR
        era_slice_key = f"g3_{year_start}_{year_end}"
        slices.append(DecadeSlice(
            era_slice_key=era_slice_key,
            start_jd=start_jd,
            end_jd=end_jd,
            year_start=year_start,
            year_end=year_end,
        ))
    return slices


# Module-level constant: the 10 decade slices (built once at import time).
DECADE_SLICES: list[DecadeSlice] = build_decade_slices()


# ---------------------------------------------------------------------------
# Fingerprint computation
# ---------------------------------------------------------------------------

def compute_substep_fingerprint(
    event_class: str,
    era_slice_key: str,
    engine_version: str,
    resonance_targets: list[str],
) -> str:
    """Compute a delta fingerprint for one (event_class, era_slice) substep.

    The fingerprint is an MD5 hex digest of a canonicalized JSON payload
    covering the four inputs that, if changed, would require a rebuild:
      * event_class      — the class being scored.
      * era_slice_key    — the decade window.
      * engine_version   — bumped when scoring logic changes.
      * resonance_targets — sorted list of target_ref strings for this chart×class.

    Inputs are sorted so the fingerprint is stable across row-order changes.

    Returns
    -------
    str — 32-character MD5 hex digest.
    """
    payload = json.dumps(
        {
            "event_class": event_class,
            "era_slice_key": era_slice_key,
            "engine_version": engine_version,
            "resonance_targets": sorted(resonance_targets),
        },
        sort_keys=True,
    )
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _query_fn(conn):
    """Return a callable that executes SQL and returns list[dict]."""
    def query(sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        cur = conn.execute(sql, params or [])
        rows = cur.fetchall()
        return [dict(r) if not isinstance(r, dict) else r for r in rows]
    return query


def _fetch_resonance_targets(conn, chart_id: str, event_class: str) -> list[str]:
    """Fetch resonance target_refs for this (chart_id, event_class) pair.

    Returns a sorted list of target_ref strings.
    Returns [] when the chart has no resonance targets for this class (I4).
    """
    try:
        cur = conn.execute(
            "SELECT DISTINCT target_ref FROM gochara_resonance_map "
            "WHERE chart_id = %s AND event_class = %s ORDER BY target_ref",
            [chart_id, event_class],
        )
        rows = cur.fetchall()
        return [
            (r["target_ref"] if isinstance(r, dict) else r[0])
            for r in rows
            if (r["target_ref"] if isinstance(r, dict) else r[0]) is not None
        ]
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[%s] could not fetch resonance targets for chart=%s event_class=%s: %s "
            "— honest empty (I4).",
            ASSET_ID, chart_id, event_class, exc,
        )
        return []


def _stored_fingerprint(query, chart_id: str, substep_key: str) -> str | None:
    """Return the stored fingerprint for this substep, or None if absent."""
    rows = query(
        f"SELECT class_fingerprint FROM {BUILD_STATE_TABLE} "
        f"WHERE chart_id = %s AND event_class = %s AND generation = %s",
        [chart_id, substep_key, GENERATION_V3],
    )
    if rows and rows[0].get("class_fingerprint"):
        return rows[0]["class_fingerprint"]
    return None


def _stored_rows_exist(query, chart_id: str, substep_key: str, era_slice_key: str) -> bool:
    """Return True if rows already exist in kala_gochara_windows_v2 for this substep."""
    # substep_key = '{event_class}::{era_slice_key}'; split to get event_class.
    event_class = substep_key.split("::", 1)[0]
    rows = query(
        f"SELECT 1 FROM {TABLE} "
        f"WHERE chart_id = %s AND event_class = %s AND generation = %s AND era_slice_key = %s "
        f"LIMIT 1",
        [chart_id, event_class, GENERATION_V3, era_slice_key],
    )
    return len(rows) > 0


def _upsert_build_state(
    conn,
    chart_id: str,
    substep_key: str,
    fingerprint: str,
    rows_written: int,
    skipped: bool,
    build_id: str,
) -> None:
    """Upsert a fingerprint record into kala_gochara_v2_build_state.

    Uses the existing table schema:
      PRIMARY KEY (chart_id, event_class, generation)
    with:
      event_class = substep_key  (e.g. 'marriage::g3_1984_1994')
      generation  = GENERATION_V3

    Required NOT NULL columns that we fill with honest sentinels:
      grammar_version, arc_engine_version, bodies_scope,
      horizon_start_date, horizon_end_date, horizon_status.
    """
    # Extract event_class and era_slice_key from substep_key for horizon dates.
    parts = substep_key.split("::", 1)
    era_slice_key = parts[1] if len(parts) == 2 else substep_key

    # Derive approximate horizon dates from the era_slice_key label.
    # Format: 'g3_{year_start}_{year_end}'.
    try:
        _, year_start_s, year_end_s = era_slice_key.split("_", 2)
        horizon_start = date(int(year_start_s), 2, 5)
        horizon_end = date(int(year_end_s), 2, 5)
    except Exception:  # noqa: BLE001
        horizon_start = date(1984, 2, 5)
        horizon_end = date(2084, 2, 5)

    skipped_reason = "fingerprint_unchanged" if skipped else None

    conn.execute(
        f"""
        INSERT INTO {BUILD_STATE_TABLE}
          (chart_id, event_class, generation, class_fingerprint,
           grammar_version, arc_engine_version, bodies_scope,
           horizon_start_date, horizon_end_date, horizon_status,
           contacts_evaluated, rows_written, skipped_reason, build_id, computed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
        ON CONFLICT (chart_id, event_class, generation) DO UPDATE SET
          class_fingerprint  = EXCLUDED.class_fingerprint,
          grammar_version    = EXCLUDED.grammar_version,
          arc_engine_version = EXCLUDED.arc_engine_version,
          bodies_scope       = EXCLUDED.bodies_scope,
          horizon_start_date = EXCLUDED.horizon_start_date,
          horizon_end_date   = EXCLUDED.horizon_end_date,
          horizon_status     = EXCLUDED.horizon_status,
          contacts_evaluated = EXCLUDED.contacts_evaluated,
          rows_written       = EXCLUDED.rows_written,
          skipped_reason     = EXCLUDED.skipped_reason,
          build_id           = EXCLUDED.build_id,
          computed_at        = now()
        """,
        [
            chart_id,
            substep_key,         # stored in event_class column
            GENERATION_V3,
            fingerprint,
            ENGINE_VERSION,      # grammar_version sentinel
            ENGINE_VERSION,      # arc_engine_version sentinel
            [],                  # bodies_scope (empty array; interval_solver handles bodies)
            horizon_start,
            horizon_end,
            "full_backfill",     # century build covers the full declared slice
            0,                   # contacts_evaluated (interval_solver doesn't expose this count)
            rows_written,
            skipped_reason,
            build_id,
        ],
    )


def _jd_to_date(jd: float) -> date:
    """Convert Julian Day number to a Python date.

    Uses a simple algorithm: JD 2440588.0 = 1970-01-01.
    Accurate to within 1 day across the 1984–2084 range we care about.
    """
    EPOCH_JD = 2440588.0  # JD for Unix epoch 1970-01-01
    days_since_epoch = int(jd - EPOCH_JD)
    return date(1970, 1, 1) + timedelta(days=days_since_epoch)


def _build_row(
    chart_id: str,
    event_class: str,
    boundary: IntervalBoundary,
    era_slice_key: str,
) -> dict[str, Any]:
    """Convert one IntervalBoundary to a kala_gochara_windows_v2 row dict."""
    window_start = _jd_to_date(boundary.enter_jd)
    window_end = _jd_to_date(boundary.exit_jd)
    peak_date = _jd_to_date(boundary.peak_jd)
    return {
        "chart_id": chart_id,
        "event_class": event_class,
        "temporal_shape": "interval",
        "window_start": window_start,
        "window_end": window_end,
        "peak_date": peak_date,
        "milestone_id": None,
        "is_irreversibility_milestone": False,
        "signed_intensity": round(float(boundary.peak_lambda), 6),
        "raw_intensity": round(float(boundary.peak_lambda), 6),
        "valence": "favourable",        # structural prior; v3 engine refines at serving time
        "is_adverse": False,
        "active_sentences": json.dumps([]),
        "contributing_systems": json.dumps([]),
        "suppression_state": json.dumps({}),
        "peak_basis": "gochara_lambda_v3",
        "calibration_state": "structural_prior",
        "source": "live",
        "generation": GENERATION_V3,
        "era_slice_key": era_slice_key,
    }


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

@register(ASSET_ID)
class GocharaV3CenturyMaterializeWriter(WriterBase):
    """W3.4 Century-horizon writer using gochara_v3 engine + decade-slice substeps.

    See module docstring for the full spec contract.
    """

    asset_id = ASSET_ID
    has_substeps = True

    # ------------------------------------------------------------------
    # FROZEN CONTRACT: plan_substeps
    # ------------------------------------------------------------------

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        """Return 60 SubStep objects: 6 event_classes × 10 decade slices.

        Each SubStep has:
          key   = '{event_class}::{era_slice_key}'  e.g. 'marriage::g3_1984_1994'
          label = human-readable description

        The plan is STATIC — it does not query the DB. The 6 event classes
        and 10 decade slices are fixed by the campaign spec. An empty
        resonance-target set for a given substep is handled honestly in
        run_substep (I4: 0 rows, not a plan failure).
        """
        steps: list[SubStep] = []
        for event_class in EVENT_CLASSES:
            for decade in DECADE_SLICES:
                key = f"{event_class}::{decade.era_slice_key}"
                label = (
                    f"W3.4 century: {event_class} "
                    f"{decade.year_start}–{decade.year_end}"
                )
                steps.append(SubStep(key=key, label=label))
        return steps

    # ------------------------------------------------------------------
    # FROZEN CONTRACT: run_substep
    # ------------------------------------------------------------------

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        """Materialize one (event_class, decade_slice) pair.

        Steps:
          1. Parse substep_key → (event_class, era_slice_key, decade).
          2. Fetch resonance targets for this chart×class.
          3. If no targets: honest 0-row result (I4).
          4. Compute delta fingerprint.
          5. Check stored fingerprint — if unchanged and rows exist: skip.
          6. call find_threshold_crossings over the decade JD range.
          7. DELETE-then-INSERT into kala_gochara_windows_v2.
          8. Upsert fingerprint to kala_gochara_v2_build_state.
          9. Log wall-clock time at DEBUG.
        """
        t0 = time.time()
        chart_id = ctx.config["chart_id"]
        substep_key = step.key
        conn = ctx.db_conn
        query = _query_fn(conn)

        # 1. Parse substep_key.
        parts = substep_key.split("::", 1)
        if len(parts) != 2:
            logger.error(
                "[%s] malformed substep_key=%r — expected 'event_class::era_slice_key'",
                ASSET_ID, substep_key,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=f"malformed substep_key={substep_key!r}",
            )
        event_class, era_slice_key = parts

        # Find the matching DecadeSlice.
        decade = next(
            (d for d in DECADE_SLICES if d.era_slice_key == era_slice_key), None
        )
        if decade is None:
            logger.error(
                "[%s] unknown era_slice_key=%r in substep_key=%r",
                ASSET_ID, era_slice_key, substep_key,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=f"unknown era_slice_key={era_slice_key!r}",
            )

        # 2. Fetch resonance targets.
        target_refs = _fetch_resonance_targets(conn, chart_id, event_class)

        # 3. I4: empty resonance targets → honest 0 rows.
        if not target_refs:
            elapsed = time.time() - t0
            logger.debug(
                "[%s] substep=%r chart=%s: no resonance targets — honest 0 rows (I4). "
                "wall_clock_s=%.3f",
                ASSET_ID, substep_key, chart_id, elapsed,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                duration_seconds=elapsed,
                notes=(
                    f"{substep_key}: honest empty — no resonance targets for "
                    f"chart={chart_id} event_class={event_class} (I4)"
                ),
            )

        # 4. Compute delta fingerprint.
        fingerprint = compute_substep_fingerprint(
            event_class, era_slice_key, ENGINE_VERSION, target_refs,
        )

        # 5. Delta skip: if fingerprint unchanged AND rows exist → no-op.
        stored_fp = _stored_fingerprint(query, chart_id, substep_key)
        rows_exist = _stored_rows_exist(query, chart_id, substep_key, era_slice_key)
        if stored_fp is not None and stored_fp == fingerprint and rows_exist and not ctx.dry_run:
            elapsed = time.time() - t0
            logger.debug(
                "[%s] substep=%r chart=%s: fingerprint unchanged (%s) — skip. "
                "wall_clock_s=%.3f",
                ASSET_ID, substep_key, chart_id, fingerprint, elapsed,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                duration_seconds=elapsed,
                notes=(
                    f"{substep_key}: skipping — fingerprint unchanged ({fingerprint}), "
                    f"rows already present"
                ),
            )

        # 6. Find threshold crossings over the decade JD range.
        #    We need a ThresholdConfig to gate window emission.  For the
        #    century build we use a structural-prior threshold: the v3 engine
        #    is bounded in [0,1], so we gate at 0.0 (emit all active intervals)
        #    as the honest structural prior before per-class calibration.
        #    This is a deliberate design choice for W3.4 — the full
        #    self-normalizing threshold (W1.4) is applied at serve time.
        threshold_config = ThresholdConfig(
            percentile_used=0.0,
            lambda_thresh=0.0,
            implied_density=0.0,
            base_rate_cited=0.0,
            age_band_used="band_41_60",
            density_flag="no_base_rate",
            fallback_used=True,
            sample_count=0,
        )

        # Import swisseph lazily (matches pattern in existing writers).
        try:
            import swisseph as swe  # type: ignore[import]
        except Exception as exc:
            elapsed = time.time() - t0
            logger.error("[%s] swisseph unavailable: %s", ASSET_ID, exc)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                duration_seconds=elapsed,
                notes=f"swisseph unavailable: {exc}",
            )

        # Build a ClassContext: the one-shot DB fetch that makes batched
        # lambda_v3 evaluation possible (zero per-JD DB access after fetch).
        # ClassContext is imported at module level so tests can monkeypatch it.
        try:
            context = ClassContext.fetch(
                conn=conn,
                chart_id=chart_id,
                event_class=event_class,
            )
        except Exception as exc:  # noqa: BLE001
            elapsed = time.time() - t0
            logger.warning(
                "[%s] substep=%r chart=%s: ClassContext.fetch failed: %s — 0 rows.",
                ASSET_ID, substep_key, chart_id, exc,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                duration_seconds=elapsed,
                notes=(
                    f"{substep_key}: ClassContext unavailable ({exc}) — honest 0 rows"
                ),
            )

        intervals: list[IntervalBoundary] = find_threshold_crossings(
            swe=swe,
            context=context,
            start_jd=decade.start_jd,
            end_jd=decade.end_jd,
            threshold_config=threshold_config,
            coarse_step_days=7.0,
        )

        if ctx.dry_run:
            elapsed = time.time() - t0
            logger.debug(
                "[%s] DRY RUN substep=%r chart=%s: %d intervals would be served. "
                "wall_clock_s=%.3f",
                ASSET_ID, substep_key, chart_id, len(intervals), elapsed,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                rows_skipped=len(intervals),
                duration_seconds=elapsed,
                notes=(
                    f"DRY RUN {substep_key}: {len(intervals)} intervals found "
                    f"in {decade.year_start}–{decade.year_end} — nothing written"
                ),
            )

        # 7. DELETE-then-INSERT (§N.3 replace-not-accrete).
        #    Scoped to (chart_id, event_class, generation, era_slice_key) so
        #    a resubmit of this decade slice does not touch other slices.
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {TABLE} "
                f"WHERE chart_id = %s AND event_class = %s "
                f"AND generation = %s AND era_slice_key = %s",
                [chart_id, event_class, GENERATION_V3, era_slice_key],
            )

        inserted = 0
        for boundary in intervals:
            row = _build_row(chart_id, event_class, boundary, era_slice_key)
            try:
                conn.execute(INSERT_SQL, row)
                inserted += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[%s] substep=%r row insert failed (peak_date=%s): %s",
                    ASSET_ID, substep_key,
                    _jd_to_date(boundary.peak_jd), exc,
                )

        # 8. Upsert fingerprint.
        _upsert_build_state(
            conn=conn,
            chart_id=chart_id,
            substep_key=substep_key,
            fingerprint=fingerprint,
            rows_written=inserted,
            skipped=False,
            build_id=ctx.build_id,
        )

        # 9. Log wall-clock time at DEBUG (AC5 — first SLO evidence point).
        elapsed = time.time() - t0
        logger.debug(
            "[%s] substep=%r chart=%s: %d intervals inserted. wall_clock_s=%.3f",
            ASSET_ID, substep_key, chart_id, inserted, elapsed,
        )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            duration_seconds=elapsed,
            notes=(
                f"{substep_key}: {len(intervals)} intervals found, "
                f"{inserted} rows inserted into {TABLE}, "
                f"era_slice_key={era_slice_key}, "
                f"fingerprint={fingerprint}"
            ),
        )

    # ------------------------------------------------------------------
    # CLI / direct-use fallback (drives own substeps; no orchestrator heartbeat)
    # ------------------------------------------------------------------

    def run(self, ctx: ContextSpec) -> WriterResult:
        """CLI path: drive all 60 substeps sequentially."""
        t0 = time.time()
        total_inserted = 0
        notes: list[str] = []
        for step in self.plan_substeps(ctx):
            result = self.run_substep(ctx, step)
            total_inserted += result.rows_inserted
            if result.notes:
                notes.append(result.notes)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_inserted,
            duration_seconds=time.time() - t0,
            notes=" | ".join(notes),
        )


__all__ = [
    "ASSET_ID",
    "DECADE_SLICES",
    "ENGINE_VERSION",
    "EVENT_CLASSES",
    "GENERATION_V3",
    "TABLE",
    "GocharaV3CenturyMaterializeWriter",
    "build_decade_slices",
    "compute_substep_fingerprint",
]
