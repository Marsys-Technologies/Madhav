"""ka_gochara_v3_century_materialize — W3.4/W5.4/MR-16 Century horizon + slice receipts.

GOCHARA-UTKARSA campaign, wave W3.4 (original) + W5.4 (writer repoint) +
PARIṢKĀRA MR-16 (dynamic event-class discovery + honest per-class coverage
notes) + PARIṢKĀRA MR-38 (fingerprint version fold).

Gate: W0.3 PASS (generation schema + utkarsha_builder role in place) +
      W3.2 PASS (interval_solver root-solved threshold crossings) +
      UTK-R1 ADJUDICATOR ruling (W5.4 repoint to kala_gochara_windows generation='3.0') +
      W3.1 PASS (ka_gochara_resonance derives up to 27 canonical event classes;
      see services/ka_gochara_resonance/writer.py + its 92/92 test suite) +
      MR-38 gate (test_mr38_fingerprint_version_fold.py): a synthetic
      writer-version (row-schema) bump forces cache invalidation and a real
      rewrite; re-running with no version change and no input change
      correctly skips.

MR-38 — FINGERPRINT VERSION FOLD (row-shape scope only)
----------------------------------------------------------
MR-13/14 changed the row shape this writer produces (added term_breakdown /
lambda_v3_ci_low / lambda_v3_ci_high / ci_source) without bumping
ENGINE_VERSION — the delta-skip (stored_fingerprint == recomputed_fingerprint
AND rows_exist) would have silently no-opped an authorized rebuild had this
not been caught in rehearsal. Fix: ROW_SCHEMA_COLUMNS (derived from
INSERT_PROD_SQL) and STAGING_ROW_SCHEMA_COLUMNS (derived from INSERT_SQL,
the calibration/staging INSERT executed every substep) — neither a
hand-maintained duplicate — are both folded into compute_substep_fingerprint's
hashed payload alongside engine_version, so any future ROW-SHAPE change to
EITHER INSERT template auto-invalidates every substep's fingerprint whether
or not ENGINE_VERSION is bumped.

SCOPE (PARĪKṢAKA F-3): this fold covers ROW SHAPE only — which columns get
written. It does NOT cover VALUE-COMPUTATION changes (e.g. MR-13's honest
valence derivation, which changed what a column's VALUE is without changing
the column LIST) — a fingerprint match after a value-computation-only change
still means "unchanged" even though the writer would now compute a different
value for the same inputs. The ENGINE_VERSION standing rule remains
load-bearing for exactly that class of change, post-MR-38 same as before:
any writer change that ALTERS COMPUTED VALUES without adding/removing/
renaming a column must still bump ENGINE_VERSION by hand. See the
"Row-schema signature" section below for the full account.

MR-16/MR-38 COMPOSITION NOTE: MR-16 bumped ENGINE_VERSION "v3.0" -> "v3.1"
for its own scope/output-shape change (dynamic event-class discovery +
coverage_quality note in suppression_state — see the MR-16 sections below).
MR-38's row_schema_* fold and MR-16's ENGINE_VERSION bump are independent,
composable inputs to the SAME hashed fingerprint payload — MR-16 does not
need MR-38's fold (it bumped ENGINE_VERSION by hand, the standing rule
MR-38's own SCOPE note above describes), and MR-38's fold does not need
MR-16's bump (a future row-shape-only change auto-invalidates via the fold
regardless of ENGINE_VERSION). ENGINE_VERSION remains "v3.1" post-merge.

PURPOSE
-------
Extends the W0.2/W2G materializer concept to a CENTURY-SCALE HEAVY writer
using the gochara_v3 engine (not v1's gochara_intensity grammar). The
unit of work is one (event_class × decade_era_slice) pair.

MR-16 FIX — DYNAMIC EVENT-CLASS DISCOVERY (kills the hardcoded 6)
-------------------------------------------------------------------
Before this fix, `plan_substeps` iterated a hardcoded 6-item `EVENT_CLASSES`
list, so this writer's production scope could never exceed 6 classes even
after `ka_gochara_resonance` (G-1) derived resonance targets for up to 27
canonical `brahma_event_ontology` classes (W3.1). The register's MR-16 gap:
"materializer hardcodes 6 classes; 27-class resonance map never rebuilt;
production scope identical to v1's."

FIX: `plan_substeps` now discovers its event-class set LIVE, per chart, via
`_discover_event_classes` — `SELECT DISTINCT event_class FROM
gochara_resonance_map WHERE chart_id = %s` — matching
`ka_gochara_sweep.KaGocharaSweepWriter._discover_event_classes`'s table and
query shape, so the two writers' substep plans always agree on which classes
a chart has coverage for. `ka_gochara_resonance` (G-1) is the single
upstream authority for which event classes a chart has targets for; as G-1's
coverage grows for a chart (today: 6 classes for the two canonical charts,
pending the R2-window resonance rebuild to reach up to 27), this writer's
substep plan grows with it on the NEXT build — no code change required. A
chart with a GENUINELY EMPTY resonance map (the query runs and finds 0 rows
— G-1 not yet built/run for it) honestly produces a ZERO-substep plan (I4)
— this writer never invents a class to plan for. `EVENT_CLASSES` is
retained as a documentation-only constant (the pre-MR-16 default/historical
scope, PARIṢKĀRA MR-12's `business_launch` folded in — see EVENT_CLASSES'
own comment) — it is NO LONGER read by `plan_substeps`.

PARĪKṢAKA F1 (§N.8, post-merge fix): `_discover_event_classes` deliberately
does NOT mirror ka_gochara_sweep's discovery method in one respect — it does
NOT catch and swallow DB errors into an empty list. See its own docstring
for the full rationale; in short, the orchestrator's SATYA-DĪPA no-op-
completion re-probe (`asset_runner.py`) treats an exception from
`plan_substeps` as "conservatively incomplete" and a `[]` return as
"genuinely done" — swallowing a query failure into `[]` here would make a
transient DB error indistinguishable from an honestly empty resonance map
and could promote a FAILED build to `state='lit'`.

The decade-slice dimension (`DECADE_SLICES`, 10 fixed slices spanning
birth→birth+100y) is unaffected — it is chart-agnostic and class-agnostic by
design (W3.4 spec), so it stays a module constant.

MR-16 FIX — HONEST PER-CLASS COVERAGE-QUALITY NOTES
-------------------------------------------------------
Per §N.6/§N.7 (never flatten confirmed and thin/sparse data into one
undifferentiated list; an honest null beats an invented judgment), every row
this writer emits now carries a LIVE-computed `coverage_quality` note inside
its `suppression_state` JSONB column — `{"tier": ..., "target_count": N,
"note": "..."}` — derived from the ACTUAL resonance-target count this
substep fetched (`_coverage_quality_note`), never a static/hand-authored
label. A class whose `gochara_resonance_map` targets are sparse (a "thin
map", per W3.1's design note: "classes with weak signature_model get honest
thin maps + a per-class quality note, never invented targets") is served
honestly as `tier="thin"`, not silently presented as equally strong as a
rich class. The same note is also folded into `WriterResult.notes` (the
per-substep build report) for build-time/SSE-log visibility.

MR-12 — CHAIN PRODUCTION (temporal_shape='chain')
-------------------------------------------------------
Wires `gochara_v3.interval_solver.score_chain_milestones` (existed, tested
in isolation since W3.2, never called by a real writer before MR-12) into
`run_substep`: for whatever event_class a substep is planned for, this
writer reads its `temporal_shape` live from `brahma_event_ontology`
(`_fetch_class_shape`) and, when it is `'chain'`, expands each detected
episode (`find_threshold_crossings`'s boundaries, reused here as episode
ANCHORS rather than final rows) into one row per `milestone_template` entry
via `score_chain_milestones` — `_build_chain_row` is the chain-shape sibling
of `_build_row`, carrying the SAME column set (including MR-16's
`coverage_quality` — see `_build_chain_row`'s own docstring), so no new DML
is introduced and the I1 mutation-guard needs no update for chain support.
`_normalize_milestone_template` adapts the ontology's
`{milestone_id, name_en, typical_offset_days_from_first}` per-entry shape
into `score_chain_milestones`'s expected
`{milestone_id, typical_offset_days, is_irreversibility_milestone}` shape —
the actual missing wire this MR closed.

HONEST FINDING: `marriage` is `temporal_shape='point'` in the live ontology
(migration 456), NOT `'chain'` — despite the originating register item's
"marriage first" framing. `business_launch` (chain, 3-milestone template,
`irreversibility_milestone='first_revenue'`) is the first GENUINELY
chain-canonical class this writer produces chain rows for. See
`_SHAPE_FALLBACK`'s docstring for the full account.

Key behaviours:
  1. plan_substeps — returns one SubStep per (event_class, decade_slice) pair,
     for whatever event_class values gochara_resonance_map holds for this
     chart (dynamic, MR-16). substep_key = '{event_class}::{era_slice_key}'.
  2. run_substep — for each substep:
       a. Fetch resonance targets + compute the live coverage_quality note.
       b. Compute a delta fingerprint from (event_class, era_slice_key,
          ENGINE_VERSION, resonance_targets) via MD5.
       c. Check kala_gochara_v2_build_state for a matching stored fingerprint.
       d. If fingerprint unchanged AND rows exist: skip (honest no-op).
       e. Else: call find_threshold_crossings from gochara_v3.interval_solver
          over the decade JD range; DELETE-then-INSERT results into BOTH:
            * kala_gochara_windows_v2 (calibration/staging surface, generation='g3_utkarsha')
            * kala_gochara_windows (production surface, generation='3.0') [W5.4 repoint]
       f. Upsert fingerprint to kala_gochara_v2_build_state.
       g. Log wall-clock time per substep at DEBUG level (AC5 / first SLO
          evidence point).
  3. I2 constraint: ZERO imports from gochara_grammar/*, gochara_intensity/*,
     or ka_gochara_sweep/*. All scoring comes from gochara_v3.interval_solver
     and gochara_v3.engine (AC6). The dynamic event-class discovery query
     (MR-16) is a plain SQL read against gochara_resonance_map — the same
     table `_fetch_resonance_targets` already reads — not an import of any
     forbidden module.
  4. I4 constraint: empty resonance targets → honest 0 rows for that substep,
     no fabrication (AC7). An empty resonance MAP (no event_class rows at
     all for this chart) → honest 0-substep plan (MR-16, same I4 discipline
     one level up).

TABLES
------
Write target 1: kala_gochara_windows_v2  (calibration/staging surface;
                generation='g3_utkarsha'; never touches v1 rows)
Write target 2: kala_gochara_windows  (production surface; generation='3.0';
                I1 rail: DB trigger protects generation='v1' rows for the two
                canonical charts — generation='3.0' writes pass through safely)
Build state:    kala_gochara_v2_build_state  (substep-keyed fingerprint)

W5.4 REPOINT (UTK-R1)
----------------------
Per ADJUDICATOR ruling UTK-R1, the production writer's FINAL target is
kala_gochara_windows with generation='3.0'. W5.4 adds this production write
while retaining the kala_gochara_windows_v2 calibration write.

I1 INVARIANT
------------
Every DML statement against kala_gochara_windows MUST carry the
generation='3.0' predicate. The mutation-guard test
(test_ka_gochara_v3_mutation_guard.py) enforces this invariant and is
mutation-tested to prove it is a real detector.

FROZEN ORCHESTRATOR CONTRACT (§N.2)
------------------------------------
  * @register('ka_gochara_v3_century_materialize')  on a WriterBase subclass
  * HEAVY: plan_substeps(ctx) + run_substep(ctx, step)
  * ctx.db_conn — writer reads/writes on it, NEVER commits or closes it
  * Never writes asset_throughput

IDEMPOTENCY (§N.3)
------------------
Delete-then-INSERT scoped to:
  kala_gochara_windows_v2: (chart_id × event_class × generation='g3_utkarsha' × era_slice_key)
  kala_gochara_windows:    (chart_id × event_class × generation='3.0' × era_slice_key)

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
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Optional

from pipeline.orchestrator.writers import (
    ContextSpec,
    SubStep,
    WriterBase,
    WriterResult,
    register,
)

# gochara_v3 imports only (I2: no gochara_grammar/*, gochara_intensity/*, ka_gochara_sweep/*)
from services.gochara_v3.interval_solver import (
    find_threshold_crossings, score_chain_milestones, IntervalBoundary, MilestoneScore,
)
from services.gochara_v3.threshold import ThresholdConfig, fetch_base_rate_for_class
from services.gochara_v3.context import ClassContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ASSET_ID = "ka_gochara_v3_century_materialize"

# Generation label for the calibration/staging surface (kala_gochara_windows_v2).
GENERATION_V3 = "g3_utkarsha"

# Generation label for the production surface (kala_gochara_windows).
# Per UTK-R1 ADJUDICATOR ruling (W5.4 repoint): every DML statement against
# kala_gochara_windows MUST carry this predicate — enforced by the mutation-guard
# test (test_ka_gochara_v3_mutation_guard.py).
GENERATION_PROD = "3.0"

# Engine version for fingerprinting.  Bumped whenever the scoring engine
# changes in a way that would move a stored window, OR (Codex C2) whenever
# the materializer's output shape/scope changes.  gochara_v3/__init__.py
# exports GRAMMAR_VERSION; we use our own constant so this writer's
# fingerprint is stable across internal gochara_v3 refactors that do NOT
# move window positions.
#
# v3.0 -> v3.1 composes THREE independent scope/shape changes landed
# together (concurrent lanes) in the same PARIṢKĀRA wave (Codex C2: any
# materializer output shape/scope change bumps ENGINE_VERSION):
#   (a) MR-16 — plan_substeps now discovers its event-class set dynamically
#       from gochara_resonance_map instead of a hardcoded 6-class list, and
#       every row carries a new coverage_quality note in suppression_state.
#   (b) MR-12 — chain-shaped rows (temporal_shape='chain') are now possible
#       for whatever event_class a substep is planned for; see the module
#       docstring's "MR-12 — CHAIN PRODUCTION" section.
#   (c) MR-42 (PK-R-5/PK-R-9, 2026-08-11) — `suppression_state` is now a
#       structured {"mechanism":..., "value":...} object forwarding the
#       real quality_gates detail, never a bare {} placeholder -- see
#       `_build_suppression_state`.
# All three are delta-fingerprint-relevant per compute_substep_fingerprint's
# own "engine_version bumped when scoring logic OR output shape changes"
# contract, even though existing point/interval classes' scoring is
# byte-for-byte unchanged. One bump, not three — there is only one
# ENGINE_VERSION value to compose into; every stored fingerprint must
# invalidate and re-materialize under the new shape rather than being
# silently skipped as "unchanged" by the fingerprint check in `run_substep`.
# Per Codex C2 convention: exactly this string, so concurrent lanes making
# the identical bump auto-merge cleanly.
ENGINE_VERSION = "v3.1"

# DOCUMENTATION-ONLY as of PARIṢKĀRA MR-16 — the pre-MR-16 hardcoded 6-class
# scope (3 legacy + 3 health/adverse; see event_class_scope.SWEEP_EVENT_CLASSES
# for the sibling ka_gochara_sweep copy of this same historical set), plus
# MR-12's business_launch addition (see _fetch_class_shape/_SHAPE_FALLBACK
# below for why business_launch, not marriage, is the first genuinely
# chain-canonical class this writer produces chain rows for). NO LONGER read
# by plan_substeps, which now discovers its event-class set live from
# gochara_resonance_map (see _discover_event_classes below) — this is the
# "kill the hardcoded 6" fix. Retained only as a documented historical
# reference / test fixture default, never as a fallback plan.
EVENT_CLASSES = [
    "career_advancement",
    "major_gain",
    "marriage",
    "illness_acute",
    "chronic_onset",
    "surgery",
    "business_launch",
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

# Table constants.
# Calibration/staging surface (W3.4 original target): kala_gochara_windows_v2.
TABLE = "kala_gochara_windows_v2"
# Production surface (W5.4 repoint, UTK-R1): kala_gochara_windows with generation='3.0'.
# I1 rail: the DB trigger on this table protects generation='v1' rows for the two
# canonical charts (482012f1-… and 1c826d5a-…). generation='3.0' writes are
# explicitly allowed by the generation-aware guard (migration 556).
PROD_TABLE = "kala_gochara_windows"
BUILD_STATE_TABLE = "kala_gochara_v2_build_state"

# INSERT template for kala_gochara_windows_v2 (calibration/staging).
# PARIṢKĀRA MR-14: the 4 W1.5 λ-decomposition columns (migration 559 on this
# table; migration 564 mirrored them onto the production table) are now
# populated from IntervalBoundary (see _build_row) instead of being silently
# omitted — the prior defect this fix closes (register PG-6/PG-7).
INSERT_SQL = f"""
    INSERT INTO {TABLE}
      (chart_id, event_class, temporal_shape,
       window_start, window_end, peak_date,
       milestone_id, is_irreversibility_milestone,
       signed_intensity, raw_intensity, valence, is_adverse,
       active_sentences, contributing_systems, suppression_state,
       peak_basis, calibration_state, source, generation, era_slice_key,
       term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source)
    VALUES
      (%(chart_id)s, %(event_class)s, %(temporal_shape)s,
       %(window_start)s, %(window_end)s, %(peak_date)s,
       %(milestone_id)s, %(is_irreversibility_milestone)s,
       %(signed_intensity)s, %(raw_intensity)s, %(valence)s, %(is_adverse)s,
       %(active_sentences)s::jsonb, %(contributing_systems)s::jsonb,
       %(suppression_state)s::jsonb,
       %(peak_basis)s, %(calibration_state)s, %(source)s,
       %(generation)s, %(era_slice_key)s,
       %(term_breakdown)s::jsonb, %(lambda_v3_ci_low)s, %(lambda_v3_ci_high)s,
       %(ci_source)s)
"""

# INSERT template for kala_gochara_windows (production, W5.4 repoint, UTK-R1).
# Every DML on this table MUST carry generation='3.0' — enforced by the
# mutation-guard test (test_ka_gochara_v3_mutation_guard.py).
# I1 mutation-guard anchor: generation='3.0' (%(generation)s parameter always
# bound to GENERATION_PROD='3.0'; literal here for static-source guard coverage).
# PARIṢKĀRA MR-14: same 4 W1.5 columns as INSERT_SQL above (migration 564
# added them to this table, nullable, additive — see MASTER_REMEDIATION_
# REGISTER_v2_0.md MR-01/MR-14).
INSERT_PROD_SQL = f"""
    INSERT INTO {PROD_TABLE}
      (chart_id, event_class, temporal_shape,
       window_start, window_end, peak_date,
       milestone_id, is_irreversibility_milestone,
       signed_intensity, raw_intensity, valence, is_adverse,
       active_sentences, contributing_systems, suppression_state,
       peak_basis, calibration_state, source, generation, era_slice_key,
       term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source)
    VALUES
      (%(chart_id)s, %(event_class)s, %(temporal_shape)s,
       %(window_start)s, %(window_end)s, %(peak_date)s,
       %(milestone_id)s, %(is_irreversibility_milestone)s,
       %(signed_intensity)s, %(raw_intensity)s, %(valence)s, %(is_adverse)s,
       %(active_sentences)s::jsonb, %(contributing_systems)s::jsonb,
       %(suppression_state)s::jsonb,
       %(peak_basis)s, %(calibration_state)s, %(source)s,
       %(generation)s, %(era_slice_key)s,
       %(term_breakdown)s::jsonb, %(lambda_v3_ci_low)s, %(lambda_v3_ci_high)s,
       %(ci_source)s)
    -- W5.4 I1 invariant: generation='3.0' only; v1 rows are protected by DB trigger
"""


# ---------------------------------------------------------------------------
# Row-schema signature (PARIṢKĀRA MR-38)
# ---------------------------------------------------------------------------
#
# PRIOR DEFECT: MR-13/14 added the term_breakdown / lambda_v3_ci_low /
# lambda_v3_ci_high / ci_source columns to INSERT_SQL, INSERT_PROD_SQL, and
# _build_row -- a real change to the writer's OUTPUT CONTRACT -- WITHOUT
# bumping ENGINE_VERSION (whose documented purpose is narrower: "bumped
# whenever the scoring engine changes in a way that would move a stored
# window", not "bumped whenever the row shape changes"). Because
# compute_substep_fingerprint's only inputs were (event_class, era_slice_key,
# engine_version, resonance_targets), a chart already built under the OLD row
# shape recomputed the IDENTICAL fingerprint after the MR-13/14 code change --
# the delta-skip fired and an authorized rebuild would have silently no-opped
# (caught in rehearsal, not by any test).
#
# FIX: derive a row-schema signature directly from BOTH INSERT templates --
# the ACTUAL SQL executed, not a hand-maintained duplicate list that could
# itself drift -- and fold both into compute_substep_fingerprint's payload
# alongside engine_version. Any future column addition/removal/rename in
# EITHER template automatically changes every substep's fingerprint -- no
# human has to remember to bump ENGINE_VERSION for a row-SHAPE change again.
# This is orthogonal to (and composes cleanly with) any future ENGINE_VERSION
# bump: all three are independent inputs folded into the same hashed payload.
#
# SCOPE (PARĪKṢAKA F-3, corrects an earlier overstated summary in this
# module's top docstring): a fingerprint match means "the inputs AND the
# writer's column LIST are unchanged" -- it does NOT mean "the writer's
# value-computation logic is unchanged". A change that alters what VALUE a
# column gets (e.g. MR-13's honest valence derivation) without adding,
# removing, or renaming any column evades this fold entirely -- the
# ENGINE_VERSION standing rule remains load-bearing for exactly that class of
# change, same as before MR-38. MR-38 closes the row-shape gap only.
#
# Both INSERT_SQL (staging/calibration surface, kala_gochara_windows_v2 --
# written every substep) and INSERT_PROD_SQL (production surface,
# kala_gochara_windows -- W5.4 repoint) are covered: a staging-only column
# change (INSERT_SQL edited without touching INSERT_PROD_SQL, or vice versa)
# must also invalidate the fingerprint, since either template's row shape is
# part of what this writer's "output contract" means.
def _extract_insert_columns(insert_sql: str) -> tuple[str, ...]:
    """Parse the column list out of an ``INSERT INTO table (col1, col2, ...)``
    SQL template.

    Self-describing on purpose: sourced from the SQL actually executed, so
    this signature cannot silently drift from the writer's real output
    contract the way a hand-maintained duplicate list could.
    """
    match = re.search(r"INSERT INTO\s+\S+\s*\(([^)]*)\)", insert_sql)
    if not match:
        return ()
    cols = [c.strip() for c in match.group(1).split(",")]
    return tuple(c for c in cols if c)


# The writer's OUTPUT CONTRACT signature: the column lists actually written
# by INSERT_SQL (staging) and INSERT_PROD_SQL (production), derived from the
# SQL templates themselves. Both folded into every substep's fingerprint by
# compute_substep_fingerprint (see the "Row-schema signature" note above).
STAGING_ROW_SCHEMA_COLUMNS: tuple[str, ...] = _extract_insert_columns(INSERT_SQL)
ROW_SCHEMA_COLUMNS: tuple[str, ...] = _extract_insert_columns(INSERT_PROD_SQL)


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
    covering the six inputs that, if changed, would require a rebuild:
      * event_class      — the class being scored.
      * era_slice_key    — the decade window.
      * engine_version   — bumped when scoring logic OR VALUE-COMPUTATION
                            changes (the standing rule for anything that is
                            NOT a row-shape change — see SCOPE below).
      * resonance_targets — sorted list of target_ref strings for this chart×class.
      * row_schema_staging — PARIṢKĀRA MR-38: the module's CURRENT
      * row_schema_prod     STAGING_ROW_SCHEMA_COLUMNS / ROW_SCHEMA_COLUMNS,
                            read live from module scope (not accepted as
                            parameters — this is the fold: it is structurally
                            impossible to compute a fingerprint that does not
                            reflect the writer's CURRENT column lists for
                            BOTH the staging INSERT_SQL and the production
                            INSERT_PROD_SQL). A row-SHAPE change to either
                            template (e.g. the MR-13/14 column additions that
                            landed without an ENGINE_VERSION bump) therefore
                            automatically invalidates every previously-stored
                            fingerprint, without depending on a human
                            remembering to bump ENGINE_VERSION for it. See
                            the "Row-schema signature" note near
                            ROW_SCHEMA_COLUMNS' definition for the full
                            defect this closes.

    SCOPE (PARĪKṢAKA F-3): the row_schema_* fold covers ROW SHAPE (which
    columns exist) only. It does NOT cover VALUE-COMPUTATION changes — a
    writer edit that changes what value a column gets, without adding,
    removing, or renaming any column, still evades this fold and remains
    covered ONLY by the ENGINE_VERSION standing rule, unchanged from before
    MR-38. A fingerprint match means "the inputs and the writer's column
    list are unchanged" — not "the writer's computed values are unchanged".

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
            "row_schema_staging": list(STAGING_ROW_SCHEMA_COLUMNS),
            "row_schema_prod": list(ROW_SCHEMA_COLUMNS),
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



# ---------------------------------------------------------------------------
# Valence — honest per-event_class derivation (PARIṢKĀRA MR-13, F#1 fix)
# ---------------------------------------------------------------------------
#
# PRIOR DEFECT: _build_row() hardcoded "valence": "favourable" for every
# event_class it serves, including the adverse-natured health classes
# (illness_acute, chronic_onset — canonical valence 'loss' per
# brahma_event_ontology) and surgery (canonical valence 'neutral'). A
# hardcoded favourable default standing in for a real per-class judgment is
# exactly the dishonest-default pattern §N.7/§N.8 exist to close.
#
# FIX: read the canonical valence live from
# brahma_event_ontology.evidence_requirements->>'valence' (migration 456) --
# the SAME field services/gochara_intensity/valence.py::VALENCE_MAP and
# services/gochara_grammar/event_class_scope.py transcribe, but read here via
# a direct SQL query (never an import of those modules -- I2/AC6 forbids
# importing gochara_intensity/gochara_grammar in this writer's code, not a
# read of the shared ontology table this module already reads elsewhere via
# fetch_base_rate_for_class/_fetch_resonance_targets).
#
# Fallback (live read fails / no row / ontology unreachable): a small,
# explicitly documented map covering ONLY the 6 EVENT_CLASSES this writer
# handles, transcribed from the same migration 456 values -- "live-preferred,
# documented fallback, never silently invented" (identical discipline to
# every sibling fetch_* in this codebase). An event_class this writer does
# not know about at all degrades to 'neutral' (the codebase's own
# established unknown-class convention, e.g.
# gochara_intensity.valence.fetch_valence's own default) -- NEVER
# 'favourable'/'gain', which would repeat the exact defect this fix removes.
_VALENCE_FALLBACK: dict[str, str] = {
    "career_advancement": "gain",
    "major_gain": "gain",
    "marriage": "neutral",
    "illness_acute": "loss",
    "chronic_onset": "loss",
    "surgery": "neutral",
}


def _fetch_class_valence(conn, event_class: str) -> tuple[str, bool]:
    """Return (valence, is_adverse) for `event_class`.

    valence is one of the kala_gochara_windows schema's own vocabulary
    values -- 'gain'|'loss'|'neutral'|'mixed' (migration 460) -- read
    directly from brahma_event_ontology, no engine-vocab translation needed
    (unlike ka_gochara.py's v1-engine _VALENCE_MAP, which translates a
    DIFFERENT vocabulary). is_adverse is True iff valence == 'loss' --
    matching gochara_intensity.valence.is_adverse's own sign rule for the
    classes this writer serves (none of EVENT_CLASSES carry the
    psychological_arc 'mixed'-override case).
    """
    try:
        cur = conn.execute(
            "SELECT evidence_requirements->>'valence' AS valence "
            "FROM brahma_event_ontology WHERE event_class_id = %s",
            [event_class],
        )
        row = cur.fetchone()
        if row is not None:
            v = row["valence"] if isinstance(row, dict) else row[0]
            if v:
                v = str(v)
                return v, (v == "loss")
    except Exception as exc:  # noqa: BLE001
        logger.info(
            "[%s] brahma_event_ontology valence read failed for "
            "event_class=%s, falling back to documented fixture: %s",
            ASSET_ID, event_class, exc,
        )
    v = _VALENCE_FALLBACK.get(event_class, "neutral")
    return v, (v == "loss")


# ---------------------------------------------------------------------------
# Temporal shape + milestone_template (PARIṢKĀRA MR-12: chain production
# wiring) — honest per-event_class derivation, same "live-preferred,
# documented fallback" discipline as _fetch_class_valence above.
# ---------------------------------------------------------------------------
#
# BRIEF_D5 §3 (migration 460, BINDING): a served row's shape MUST mirror its
# event_class's brahma_event_ontology.temporal_shape -- point/interval/chain,
# never more temporal precision than the ontology declares. This writer was
# already shape-aware for point/interval (both stamped "interval" pre-MR-12,
# unchanged by this fix -- point-row production is a separate, already-closed
# lane, MR-10/MR-11); MR-12 is the first time this writer reads the ontology's
# 'chain' branch and produces milestone_template-shaped output.
#
# HONEST FINDING (MR-12, 2026-08-11 session): the register item's "marriage
# first" framing does NOT match the live ontology. brahma_event_ontology
# (migration 456) declares marriage temporal_shape='point' explicitly, with
# its own note: "a future v2 could split into a chain (engagement -> ceremony
# -> registration) if per-milestone dates become available." It is not a
# chain today, and brahma_event_ontology's own CHECK constraint (migration
# 456, brahma_event_ontology_shape_data_consistency_check) forbids storing a
# chain-shaped row without a real milestone_template of >=2 entries -- so
# marriage cannot honestly produce chain rows without either fabricating an
# ontology override (B.10 violation) or a native-ruled ontology amendment
# (out of this CODE-ONLY session's authority). See PARISHKARA_LEDGER.md
# "MR-12" entry (parishkara/campaign branch) for the full account.
#
# 'business_launch' is the first GENUINELY chain-canonical class this writer
# is wired to produce rows for: temporal_shape='chain', 3-milestone template
# (decision -> registration -> first_revenue), irreversibility_milestone=
# 'first_revenue' -- BRIEF_D4A Lane A-2's own worked example (migration 456).
_SHAPE_FALLBACK: dict[str, dict[str, Any]] = {
    "career_advancement": {
        "temporal_shape": "point", "milestone_template": None, "irreversibility_milestone": None,
    },
    "major_gain": {
        "temporal_shape": "interval", "milestone_template": None, "irreversibility_milestone": None,
    },
    "marriage": {
        # Matches live brahma_event_ontology (migration 456) — NOT 'chain'.
        "temporal_shape": "point", "milestone_template": None, "irreversibility_milestone": None,
    },
    "illness_acute": {
        "temporal_shape": "point", "milestone_template": None, "irreversibility_milestone": None,
    },
    "chronic_onset": {
        "temporal_shape": "interval", "milestone_template": None, "irreversibility_milestone": None,
    },
    "surgery": {
        "temporal_shape": "point", "milestone_template": None, "irreversibility_milestone": None,
    },
    "business_launch": {
        "temporal_shape": "chain",
        "milestone_template": [
            {"milestone_id": "decision", "name_en": "Decision to found/launch",
             "typical_offset_days_from_first": 0},
            {"milestone_id": "registration", "name_en": "Legal/business registration",
             "typical_offset_days_from_first": 45},
            {"milestone_id": "first_revenue", "name_en": "First revenue booked",
             "typical_offset_days_from_first": 120},
        ],
        "irreversibility_milestone": "first_revenue",
    },
}


def _fetch_class_shape(
    conn, event_class: str,
) -> tuple[str, Optional[list[dict]], Optional[str]]:
    """Return (temporal_shape, milestone_template, irreversibility_milestone)
    for `event_class`.

    Live-reads brahma_event_ontology; falls back to `_SHAPE_FALLBACK` (honest,
    documented fixture) on any DB-shape surprise, identical discipline to
    `_fetch_class_valence`. An event_class absent from BOTH the live table and
    the fallback degrades to temporal_shape='interval' (this writer's
    pre-MR-12 universal behavior) with no milestone_template -- NEVER
    invented as 'chain' (I4: a shape this writer cannot honestly support is
    never guessed into existence).

    milestone_template is returned in the RAW ontology shape
    ({milestone_id, name_en, typical_offset_days_from_first}) — see
    `_normalize_milestone_template` for the adapter into
    `score_chain_milestones`'s expected per-entry shape.
    """
    try:
        cur = conn.execute(
            "SELECT temporal_shape, milestone_template, irreversibility_milestone "
            "FROM brahma_event_ontology WHERE event_class_id = %s",
            [event_class],
        )
        row = cur.fetchone()
        if row is not None:
            d = row if isinstance(row, dict) else dict(
                zip(["temporal_shape", "milestone_template", "irreversibility_milestone"], row)
            )
            shape = d.get("temporal_shape")
            if shape:
                template = d.get("milestone_template")
                if isinstance(template, str):
                    try:
                        template = json.loads(template)
                    except Exception:  # noqa: BLE001
                        template = None
                return str(shape), template, d.get("irreversibility_milestone")
    except Exception as exc:  # noqa: BLE001
        logger.info(
            "[%s] brahma_event_ontology shape read failed for event_class=%s, "
            "falling back to documented fixture: %s",
            ASSET_ID, event_class, exc,
        )
    fallback = _SHAPE_FALLBACK.get(event_class)
    if fallback is None:
        return "interval", None, None
    return fallback["temporal_shape"], fallback["milestone_template"], fallback["irreversibility_milestone"]


def _normalize_milestone_template(
    raw_template: list[dict], irreversibility_milestone: Optional[str],
) -> list[dict]:
    """Adapt brahma_event_ontology's milestone_template entry shape
    ({milestone_id, name_en, typical_offset_days_from_first}) into
    `gochara_v3.interval_solver.score_chain_milestones`'s expected per-entry
    shape ({milestone_id, typical_offset_days, is_irreversibility_milestone}).

    The ontology does NOT carry an is_irreversibility_milestone flag per
    milestone-entry — it names the ONE irreversibility milestone_id (if any)
    at the ontology-row level (the `irreversibility_milestone` column). This
    adapter is the exact wiring gap MR-12 was scoped to find and close:
    score_chain_milestones has existed, tested in isolation
    (test_w32_interval_solver.py), since W3.2 — nothing ever translated real
    ontology JSON into the shape it expects before this fix.
    """
    return [
        {
            "milestone_id": entry.get("milestone_id"),
            "typical_offset_days": entry.get("typical_offset_days_from_first", 0.0),
            "is_irreversibility_milestone": (
                entry.get("milestone_id") is not None
                and entry.get("milestone_id") == irreversibility_milestone
            ),
        }
        for entry in raw_template
    ]


def _build_chain_row(
    chart_id: str,
    event_class: str,
    milestone: MilestoneScore,
    era_slice_key: str,
    *,
    valence: str,
    is_adverse: bool,
    generation: str,
    coverage_quality: Optional[dict] = None,
) -> dict[str, Any]:
    """Convert one MilestoneScore (gochara_v3.interval_solver) into a
    kala_gochara_windows(_v2) row dict — the chain-shape sibling of
    `_build_row`. Carries EXACTLY the same key set (verified by
    test_mr12_chain_production.py::test_build_chain_row_same_key_set_as_
    interval_row), so it binds against the SAME INSERT_SQL/INSERT_PROD_SQL
    templates unchanged — no new DML statement is introduced, so the I1
    mutation-guard's static source coverage (test_ka_gochara_v3_mutation_
    guard.py) needs no update for chain support.

    window_start = window_end = peak_date = this milestone's own JD (a
    chain-shaped row is one independently-dateable sub-window per milestone,
    per BRIEF_D5 §3 / migration 460's column comment).

    coverage_quality
        PARIṢKĀRA MR-16/MR-12 parity: the SAME honest, LIVE-computed
        per-event_class coverage-quality note `_build_row` now embeds under
        `suppression_state["coverage_quality"]` (see `_build_row`'s own
        docstring). A chain row is scored from the identical resonance-target
        fetch as its sibling interval/point rows for the same substep, so it
        must carry the same coverage signal — a caller reading a chain row's
        suppression_state must not see a silent gap just because the row
        happened to come from the chain branch of run_substep. Default None
        (I4 degrade) only for callers/tests that predate this fix;
        run_substep always supplies it.

    PARĪKṢAKA F-2 fix (2026-08-11): `suppression_state` is now built via
    `_build_suppression_state(term_breakdown, coverage_quality)` -- the SAME
    function `_build_row` uses -- instead of a standalone
    `{"coverage_quality": ...} if ... else {}` dict. Before this fix, a
    chain row's `suppression_state` (a) could be a bare `{}` (whenever
    `coverage_quality` was omitted) and (b) NEVER carried the real
    `quality_gates` mechanism/value MR-42 requires, even though that same
    value is already sitting in `term_breakdown['quality_gates']` two lines
    below (`milestone.intensity_result.term_breakdown`) -- the exact
    §N.7-item-4 "flag/field with no real detector behind it" defect class
    MR-42 was written to kill on the interval-row path, silently still
    reachable via the chain-row path alone.
    """
    milestone_date = _jd_to_date(milestone.milestone_jd)
    ir = milestone.intensity_result
    term_breakdown = ir.term_breakdown if ir is not None else None
    ci_low = ir.lambda_v3_ci_low if ir is not None else None
    ci_high = ir.lambda_v3_ci_high if ir is not None else None
    ci_source = ir.ci_source if ir is not None else None
    return {
        "chart_id": chart_id,
        "event_class": event_class,
        "temporal_shape": "chain",
        "window_start": milestone_date,
        "window_end": milestone_date,
        "peak_date": milestone_date,
        "milestone_id": milestone.milestone_id,
        "is_irreversibility_milestone": milestone.is_irreversibility_milestone,
        "signed_intensity": round(float(milestone.lambda_v3), 6),
        "raw_intensity": round(float(milestone.lambda_v3), 6),
        "valence": valence,
        "is_adverse": is_adverse,
        "active_sentences": json.dumps([]),
        "contributing_systems": json.dumps([]),
        "suppression_state": json.dumps(_build_suppression_state(term_breakdown, coverage_quality)),
        "peak_basis": "gochara_lambda_v3",
        "calibration_state": "structural_prior",
        "source": "live",
        "generation": generation,
        "era_slice_key": era_slice_key,
        "term_breakdown": json.dumps(term_breakdown) if term_breakdown is not None else None,
        "lambda_v3_ci_low": ci_low,
        "lambda_v3_ci_high": ci_high,
        "ci_source": ci_source,
    }


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


# ---------------------------------------------------------------------------
# Dynamic event-class discovery (PARIṢKĀRA MR-16 — kills the hardcoded 6)
# ---------------------------------------------------------------------------

def _discover_event_classes(conn, chart_id: str) -> list[str]:
    """DISTINCT event_class values gochara_resonance_map holds for this
    chart, ascending.

    Mirrors ka_gochara_sweep.KaGocharaSweepWriter._discover_event_classes in
    table + query shape, so the two writers' substep plans always agree on
    which classes a chart has coverage for. NEVER a hardcoded fallback list
    (MR-16 fix): a chart with genuinely zero gochara_resonance_map rows
    returns [] here, which plan_substeps below turns into an honest
    0-substep plan (I4) — never a silent revert to EVENT_CLASSES.

    PARĪKṢAKA F1 (§N.8): DB errors PROPAGATE — this function does NOT catch
    and swallow exceptions the way ka_gochara_sweep's sibling does. The
    orchestrator's no-op-completion re-probe (asset_runner.py, the
    SATYA-DĪPA fix) calls `writer.plan_substeps(ctx)` inside a
    SAVEPOINT + try/except that conservatively sets `plan_complete=False`
    on ANY exception — a deliberate fail-closed design. A `_discover_event_
    classes` that swallowed its own query failure and returned [] would be
    INDISTINGUISHABLE, from that re-probe's point of view, from "this chart
    genuinely has an empty resonance map" — `remaining_count=0` ->
    `plan_complete=True` -> the asset gets promoted to 'lit' on top of a
    FAILED query, exactly the D-1.6/SATYA-DĪPA defect class one level
    deeper. Letting the exception propagate here means the orchestrator's
    own except-clause does its job (fails closed); catching it here would
    blind that mechanism. Only a QUERY THAT RUNS AND FINDS ZERO ROWS
    produces the honest empty list — a query that never ran to completion
    is not that, and must not be reported as if it were.

    I2: this is a plain SQL read against gochara_resonance_map — the exact
    same table _fetch_resonance_targets above already reads — not an import
    of gochara_grammar/gochara_intensity/ka_gochara_sweep.
    """
    rows = _query_fn(conn)(
        "SELECT DISTINCT event_class FROM gochara_resonance_map "
        "WHERE chart_id = %s ORDER BY event_class",
        [chart_id],
    )
    return [r["event_class"] for r in rows if r.get("event_class")]


# ---------------------------------------------------------------------------
# Honest per-class coverage-quality note (PARIṢKĀRA MR-16)
# ---------------------------------------------------------------------------

# Tier boundaries for the LIVE target-count signal. Deliberately coarse and
# documented here (not hidden inside the function) — these are a serving
# convenience label, never a claim of statistical significance. The honest
# quantity is target_count itself; tier is a human-readable bucket over it.
_COVERAGE_QUALITY_THIN_MAX = 2
_COVERAGE_QUALITY_MODERATE_MAX = 5


def _coverage_quality_note(event_class: str, target_refs: list[str]) -> dict[str, Any]:
    """Honest, LIVE-computed per-event_class coverage-quality note.

    §N.7 item 4 / §N.8: a quality label needs a real detector behind it, or
    it is null, not green. Rather than importing/duplicating a static,
    hand-authored "rich_model"/"thin_model" narrative string maintained
    elsewhere (services/ka_gochara_resonance/writer.py's
    COVERAGE_QUALITY_NOTES — itself documentation, not live data), this note
    is derived from the ACTUAL resonance-target count `run_substep` just
    fetched for (chart_id, event_class) via `_fetch_resonance_targets` — the
    real detector for "how much resonance-map coverage does THIS chart have
    for THIS class, right now." A class with a genuinely thin
    `signature_model` mechanically produces few targets and is honestly
    labeled 'thin' here; a class this writer has never seen before (a new
    W3.1 class with no resonance rows yet) is honestly 'empty', never
    silently promoted to look as strong as a rich class (I4 / §N.6).

    Returns a dict suitable for embedding under suppression_state's
    "coverage_quality" key: {"tier", "target_count", "note"}.
    """
    n = len(target_refs)
    if n == 0:
        tier = "empty"
    elif n <= _COVERAGE_QUALITY_THIN_MAX:
        tier = "thin"
    elif n <= _COVERAGE_QUALITY_MODERATE_MAX:
        tier = "moderate"
    else:
        tier = "rich"
    return {
        "tier": tier,
        "target_count": n,
        "note": (
            f"{event_class}: {n} resonance target(s) in gochara_resonance_map "
            f"backed this window ({tier} coverage). Never an invented target — "
            f"a thin/empty tier honestly reports sparse classical-prior "
            f"coverage for this class, not an error."
        ),
    }


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


def _build_suppression_state(
    term_breakdown: Optional[dict], coverage_quality: Optional[dict] = None,
) -> dict[str, Any]:
    """MR-42 (PK-R-5, 2026-08-11): the row's `suppression_state` column used
    to be an unconditional `json.dumps({})` regardless of whether anything
    was actually computed -- a reader could not tell "nothing fired" from
    "nothing was asked" (the whole computation's own suppression detail was
    silently dropped, even though it was already computed and buried in
    `term_breakdown['quality_gates']` a few lines away).

    `quality_gates` is the v3-native suppression mechanism (see engine.py's
    MR-41(c) wiring-decision comment) -- 1.0 in (0,1] when no
    `kala_vedha_gochara` vedha rows overlapped the evaluation window,
    <1.0 when one or more did. This function ALWAYS returns a structured
    object naming that mechanism, so `suppression_state={}` never appears on
    a row this writer actually computed a peak for:

      * `term_breakdown` present (the normal computed-row case): forwards
        the real `quality_gates` scalar this same `term_breakdown` already
        carries (no new computation, no new DB read -- W1.5's own value).
      * `term_breakdown` is None (I4 honest degrade: peak evaluation
        failed at this boundary's peak_jd): still names the mechanism, with
        `value: None` and an explicit `note` -- distinguishable from a
        computed `quality_gates == 1.0` ("checked, nothing fired") by a
        reader inspecting `value`, never collapsed to the same bare `{}`
        either case used to produce.

    `coverage_quality` (MR-16, folded in here at REBASE MERGE time so the
    two concurrent lanes' additions to this SAME field compose rather than
    one silently overwriting the other): when supplied, embedded under the
    `coverage_quality` key alongside `mechanism`/`value`/`note` above --
    the same shape `_build_row`'s own (pre-MR-42) `coverage_quality` branch
    used to build standalone, now folded into the always-structured object
    this function returns.
    """
    if term_breakdown is None:
        state = {
            "mechanism": "quality_gates",
            "value": None,
            "note": "peak evaluation failed at this boundary's peak_jd (I4 honest degrade) "
                    "-- quality_gates was never computed for this row, not evaluated to a "
                    "value of 0/1.",
        }
    else:
        state = {
            "mechanism": "quality_gates",
            "value": term_breakdown.get("quality_gates"),
            "note": "v3-native suppression mechanism (see gochara_v3/engine.py's MR-41(c) "
                    "wiring-decision comment); the v1 vedha_cancellation/sarvatobhadra_vedha/"
                    "kartari_pincer mechanisms remain v1-parity-mode-only and are not consulted "
                    "on this (v3 production) path.",
        }
    if coverage_quality is not None:
        state["coverage_quality"] = coverage_quality
    return state


def _build_row(
    chart_id: str,
    event_class: str,
    boundary: IntervalBoundary,
    era_slice_key: str,
    *,
    valence: str,
    is_adverse: bool,
    generation: str = GENERATION_V3,
    term_breakdown: Optional[dict] = None,
    lambda_v3_ci_low: Optional[float] = None,
    lambda_v3_ci_high: Optional[float] = None,
    ci_source: Optional[str] = None,
    coverage_quality: Optional[dict] = None,
) -> dict[str, Any]:
    """Convert one IntervalBoundary to a kala_gochara_windows(_v2) row dict.

    Parameters
    ----------
    valence
        REQUIRED -- the honest per-event_class valence
        ('gain'|'loss'|'neutral'|'mixed'), from `_fetch_class_valence`.
        No default: every caller must supply an honestly-derived value
        rather than a fixed literal (PARIṢKĀRA MR-13 fix -- this parameter
        used to be a hardcoded "favourable" string inside this function).
    is_adverse
        REQUIRED -- companion boolean from `_fetch_class_valence`.
    generation
        The generation label to stamp on the row.
        * GENERATION_V3 ('g3_utkarsha') → calibration row for kala_gochara_windows_v2
        * GENERATION_PROD ('3.0')       → production row for kala_gochara_windows
    term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source
        PARIṢKĀRA MR-14 fix (register PG-6/PG-7): the W1.5 λ decomposition +
        structural-prior credible interval, sourced from
        `IntervalBoundary.term_breakdown`/`.lambda_v3_ci_low`/`.lambda_v3_ci_high`/
        `.ci_source` (populated by `interval_solver.find_threshold_crossings`
        at the window's peak_jd). Callers pass `boundary.term_breakdown` etc.
        explicitly rather than this function reaching into `boundary` itself,
        matching the existing valence/is_adverse pattern of "every value this
        function serves is an explicit parameter, not silently derived
        in-body." All default None (I4 honest degrade: a boundary whose peak
        evaluation failed carries None here, never a fabricated breakdown).
    coverage_quality
        PARIṢKĀRA MR-16 fix (deliverable 2): the honest, LIVE-computed
        per-event_class coverage-quality note from `_coverage_quality_note`
        (`{"tier", "target_count", "note"}`), embedded under
        `suppression_state["coverage_quality"]` so a consumer reading the
        served row (register_gochara_windows.ts passes `suppression_state`
        through opaquely) can see how thin/rich this chart's resonance-map
        coverage was for this class, at build time -- never invented, never
        silently omitted for a thin class. Default None (I4 degrade) only
        for callers/tests that predate this fix; `run_substep` always
        supplies it. REBASE MERGE NOTE (PK-R-9, 2026-08-11): folded into
        `_build_suppression_state` below (see that function's own
        `coverage_quality` parameter) rather than built standalone here, so
        this concurrent MR-16 addition and MR-42's structured
        {"mechanism":...} object compose in the SAME `suppression_state`
        field instead of one silently overwriting the other.
        `term_breakdown` is ALSO now the source for `suppression_state`
        (MR-42, PK-R-5/PK-R-9 -- see `_build_suppression_state`) -- no new
        parameter added for that half, the same value this docstring
        already documents just gets used a second time.
    """
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
        "valence": valence,
        "is_adverse": is_adverse,
        "active_sentences": json.dumps([]),
        "contributing_systems": json.dumps([]),
        "suppression_state": json.dumps(_build_suppression_state(term_breakdown, coverage_quality)),
        "peak_basis": "gochara_lambda_v3",
        "calibration_state": "structural_prior",
        "source": "live",
        "generation": generation,
        "era_slice_key": era_slice_key,
        "term_breakdown": json.dumps(term_breakdown) if term_breakdown is not None else None,
        "lambda_v3_ci_low": lambda_v3_ci_low,
        "lambda_v3_ci_high": lambda_v3_ci_high,
        "ci_source": ci_source,
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
        """Return one SubStep per (event_class, decade_slice) pair.

        Each SubStep has:
          key   = '{event_class}::{era_slice_key}'  e.g. 'marriage::g3_1984_1994'
          label = human-readable description

        PARIṢKĀRA MR-16: event_class now ranges DYNAMICALLY over whatever
        `gochara_resonance_map` holds for this chart (`_discover_event_classes`)
        — NEVER the hardcoded `EVENT_CLASSES` list (that constant is
        documentation-only as of this fix; see module docstring). The plan is
        no longer static: it issues one DISTINCT-event_class read against
        gochara_resonance_map, the same table `_fetch_resonance_targets`
        already reads per-substep. decade_slice stays the fixed 10-slice
        century grid (DECADE_SLICES) — chart-agnostic and class-agnostic by
        design (W3.4 spec). Whether a given discovered event_class turns out
        to be chain-shaped (PARIṢKĀRA MR-12) is decided per-substep, inside
        run_substep — plan_substeps itself is shape-agnostic.

        A chart with a GENUINELY EMPTY resonance map (the query runs and
        finds 0 rows — G-1 not yet run for it) honestly produces a
        ZERO-substep plan here (I4 at the plan level, mirroring
        ka_gochara_sweep's own no-targets-no-substeps discipline) — this
        writer never invents a class to plan for. A per-substep empty
        resonance-TARGET set (a discovered class with rows for OTHER classes
        but somehow none for itself — not expected, but handled the same way
        as always) remains a run_substep-level I4 0-row result, not a plan
        failure.

        A DB error during discovery is NOT caught here — `_discover_event_
        classes` lets it propagate (PARĪKṢAKA F1), and this method does not
        add its own try/except around that call. The orchestrator's
        no-op-completion re-probe relies on exactly this: it wraps its own
        `plan_substeps(ctx)` call in a try/except and treats any exception
        as "conservatively incomplete," which only works if this method
        does not swallow the error first.
        """
        chart_id = ctx.config["chart_id"]
        conn = ctx.db_conn
        event_classes = _discover_event_classes(conn, chart_id)

        if not event_classes:
            logger.info(
                "[%s] no populated gochara_resonance_map event_classes for "
                "chart=%s — honest empty plan, zero substeps (MR-16 I4).",
                ASSET_ID, chart_id,
            )
            return []

        steps: list[SubStep] = []
        for event_class in event_classes:
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
          2. Fetch resonance targets for this chart×class; compute the
             honest, LIVE coverage_quality note from that same fetch
             (MR-16 deliverable 2).
          3. If no targets: honest 0-row result (I4).
          4. Compute delta fingerprint.
          5. Check stored fingerprint — if unchanged and rows exist: skip.
          6. call find_threshold_crossings over the decade JD range.
          7. DELETE-then-INSERT into kala_gochara_windows_v2 and
             kala_gochara_windows, every row carrying coverage_quality
             inside suppression_state.
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

        # 2b. PARIṢKĀRA MR-16 deliverable 2: the honest, LIVE per-class
        #     coverage-quality note, computed from the SAME target_refs
        #     fetch above (never a static/hand-authored label). Computed
        #     unconditionally (including the I4 empty-targets branch below,
        #     where it is honestly tier='empty') so every WriterResult.notes
        #     carries a real coverage signal, not just the row-level ones.
        quality_note = _coverage_quality_note(event_class, target_refs)

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
                    f"chart={chart_id} event_class={event_class} (I4) "
                    f"[coverage_quality={quality_note['tier']}]"
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
        #
        #    §N.8: fallback_used must be derived from a real DB lookup, not
        #    bound to a literal — the lookup result (True iff the class has no
        #    base_rate row in brahma_event_ontology) is the earned signal.
        #    base_rate_cited and age_band_used are also populated from the
        #    lookup; lambda_thresh stays 0.0 per the structural-prior design.
        try:
            _base_rate_cited, _age_band_used, _fallback_used = fetch_base_rate_for_class(
                conn, event_class,
            )
        except Exception:  # noqa: BLE001
            _base_rate_cited, _age_band_used, _fallback_used = 0.0, "band_41_60", True

        threshold_config = ThresholdConfig(
            percentile_used=0.0,
            lambda_thresh=0.0,
            implied_density=0.0,
            base_rate_cited=_base_rate_cited,
            age_band_used=_age_band_used,
            density_flag="no_base_rate" if _fallback_used else "ok",
            fallback_used=_fallback_used,
            sample_count=0,
        )

        # PARIṢKĀRA MR-12: shape-aware dispatch. BRIEF_D5 §3 (BINDING) requires
        # a served row's shape to mirror brahma_event_ontology.temporal_shape.
        # is_chain gates the milestone-scoring path below; a chain-shaped
        # class with no usable milestone_template degrades to an honest
        # skip (I4), never a fabricated row.
        _shape, _raw_milestone_template, _irreversibility_milestone = _fetch_class_shape(
            conn, event_class,
        )
        is_chain = _shape == "chain"
        chain_milestone_template: list[dict] = []
        if is_chain and _raw_milestone_template:
            chain_milestone_template = _normalize_milestone_template(
                _raw_milestone_template, _irreversibility_milestone,
            )

        if is_chain and not chain_milestone_template:
            # I4 honest gap: the ontology declares this class chain-shaped but
            # carries no usable milestone_template (or the live read failed
            # and no documented fallback template exists for this class).
            # Mirrors the "no resonance targets" early-return above: return
            # BEFORE any DELETE/INSERT is issued, no fingerprint upsert —
            # never a fabricated row (I4).
            elapsed = time.time() - t0
            note = (
                f"{substep_key}: skipped — event_class={event_class} is "
                f"chain-shaped (brahma_event_ontology.temporal_shape='chain') "
                f"but milestone_template is empty/unavailable — honest gap "
                f"(I4), no rows fabricated"
            )
            logger.warning("[%s] %s", ASSET_ID, note)
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                duration_seconds=elapsed,
                notes=note,
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

        # PARIṢKĀRA MR-15: AV (Ashtakavarga) gating is a flagship gochara_v3
        # mechanism. A degraded av_gate_rows fetch inside ClassContext.fetch
        # used to be indistinguishable from "this chart genuinely has no AV
        # data" — swallowed at INFO with zero build-report visibility (the
        # exact defect the only production build to date silently shipped
        # with). getattr(..., None) is deliberate: existing tests stub
        # ClassContext.fetch to return a bare object() with no attributes at
        # all, and that must keep degrading gracefully, not raise.
        av_gate_fetch_error = getattr(context, "av_gate_fetch_error", None)
        av_gate_note = ""
        if av_gate_fetch_error:
            logger.error(
                "[%s] substep=%r chart=%s: AV (Ashtakavarga) gating degraded "
                "this substep — %s",
                ASSET_ID, substep_key, chart_id, av_gate_fetch_error,
            )
            av_gate_note = f"AV_GATE_DEGRADED: {av_gate_fetch_error}; "

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
            if is_chain:
                would_produce = len(intervals) * len(chain_milestone_template)
                logger.debug(
                    "[%s] DRY RUN substep=%r chart=%s: %d chain episodes x %d "
                    "milestones = %d rows would be served. wall_clock_s=%.3f",
                    ASSET_ID, substep_key, chart_id, len(intervals),
                    len(chain_milestone_template), would_produce, elapsed,
                )
                return WriterResult(
                    asset_id=self.asset_id, rows_inserted=0,
                    rows_skipped=would_produce,
                    duration_seconds=elapsed,
                    notes=(
                        f"{av_gate_note}DRY RUN {substep_key}: chain-shaped, "
                        f"{len(intervals)} episodes x {len(chain_milestone_template)} "
                        f"milestones = {would_produce} rows would be served "
                        f"in {decade.year_start}–{decade.year_end} — nothing written"
                    ),
                )
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
                    f"{av_gate_note}DRY RUN {substep_key}: {len(intervals)} intervals found "
                    f"in {decade.year_start}–{decade.year_end} — nothing written"
                ),
            )

        # 7. DELETE-then-INSERT (§N.3 replace-not-accrete).
        #    Scoped to (chart_id, event_class, generation, era_slice_key) so
        #    a resubmit of this decade slice does not touch other slices.
        #
        #    W5.4 repoint (UTK-R1): write to BOTH tables.
        #      (a) kala_gochara_windows_v2 — calibration/staging (generation='g3_utkarsha')
        #      (b) kala_gochara_windows    — production           (generation='3.0')
        #    Every DML on kala_gochara_windows MUST carry generation='3.0'.
        #    The I1 rail (DB trigger) allows generation='3.0'; it only blocks 'v1'.

        # (a) Calibration/staging table: kala_gochara_windows_v2
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {TABLE} "
                f"WHERE chart_id = %s AND event_class = %s "
                f"AND generation = %s AND era_slice_key = %s",
                [chart_id, event_class, GENERATION_V3, era_slice_key],
            )

        # (b) Production table: kala_gochara_windows with generation='3.0'
        #     I1 mutation-guard invariant: this DELETE carries generation='3.0'.
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {PROD_TABLE} "
                f"WHERE chart_id = %s AND event_class = %s "
                f"AND generation = '3.0' AND era_slice_key = %s",
                [chart_id, event_class, era_slice_key],
            )

        # Honest per-event_class valence (PARIṢKĀRA MR-13, F#1 fix): computed
        # ONCE per substep (all boundaries in this substep share the same
        # event_class) and passed to every _build_row call below -- never a
        # hardcoded "favourable" literal.
        class_valence, class_is_adverse = _fetch_class_valence(conn, event_class)

        inserted = 0
        if is_chain:
            # PARIṢKĀRA MR-12: chain production. Each detected episode
            # (IntervalBoundary from find_threshold_crossings, reused here as
            # the episode ANCHOR, not the final row) is expanded into one row
            # per milestone_template entry via score_chain_milestones — the
            # W3.2 machinery that has existed, tested in isolation, since
            # before this fix but was never wired to a real caller.
            #
            # MR-16 parity: coverage_quality (the same quality_note every
            # non-chain row on this substep carries) is passed to
            # _build_chain_row too — a chain row is scored from the identical
            # resonance-target fetch as its sibling rows for this substep, so
            # it must carry the same honest coverage signal.
            for boundary in intervals:
                milestone_scores = score_chain_milestones(
                    swe, context, boundary.enter_jd, chain_milestone_template,
                    threshold_config,
                )
                for ms in milestone_scores:
                    # (a) Insert into calibration/staging table.
                    row_v2 = _build_chain_row(
                        chart_id, event_class, ms, era_slice_key,
                        valence=class_valence, is_adverse=class_is_adverse,
                        generation=GENERATION_V3,
                        coverage_quality=quality_note,
                    )
                    try:
                        conn.execute(INSERT_SQL, row_v2)
                        inserted += 1
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "[%s] substep=%r v2 chain row insert failed "
                            "(milestone_id=%s, peak_date=%s): %s",
                            ASSET_ID, substep_key, ms.milestone_id,
                            _jd_to_date(ms.milestone_jd), exc,
                        )

                    # (b) Insert into production table (generation='3.0').
                    #     I1 mutation-guard invariant: row carries generation='3.0'.
                    row_prod = _build_chain_row(
                        chart_id, event_class, ms, era_slice_key,
                        valence=class_valence, is_adverse=class_is_adverse,
                        generation=GENERATION_PROD,
                        coverage_quality=quality_note,
                    )
                    try:
                        conn.execute(INSERT_PROD_SQL, row_prod)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "[%s] substep=%r prod chain row insert failed "
                            "(milestone_id=%s, peak_date=%s): %s",
                            ASSET_ID, substep_key, ms.milestone_id,
                            _jd_to_date(ms.milestone_jd), exc,
                        )
        else:
            for boundary in intervals:
                # (a) Insert into calibration/staging table.
                row_v2 = _build_row(
                    chart_id, event_class, boundary, era_slice_key,
                    valence=class_valence, is_adverse=class_is_adverse,
                    generation=GENERATION_V3,
                    term_breakdown=boundary.term_breakdown,
                    lambda_v3_ci_low=boundary.lambda_v3_ci_low,
                    lambda_v3_ci_high=boundary.lambda_v3_ci_high,
                    ci_source=boundary.ci_source,
                    coverage_quality=quality_note,
                )
                try:
                    conn.execute(INSERT_SQL, row_v2)
                    inserted += 1
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "[%s] substep=%r v2 row insert failed (peak_date=%s): %s",
                        ASSET_ID, substep_key,
                        _jd_to_date(boundary.peak_jd), exc,
                    )

                # (b) Insert into production table (generation='3.0').
                #     I1 mutation-guard invariant: row carries generation='3.0'.
                row_prod = _build_row(
                    chart_id, event_class, boundary, era_slice_key,
                    valence=class_valence, is_adverse=class_is_adverse,
                    generation=GENERATION_PROD,
                    term_breakdown=boundary.term_breakdown,
                    lambda_v3_ci_low=boundary.lambda_v3_ci_low,
                    lambda_v3_ci_high=boundary.lambda_v3_ci_high,
                    ci_source=boundary.ci_source,
                    coverage_quality=quality_note,
                )
                try:
                    conn.execute(INSERT_PROD_SQL, row_prod)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "[%s] substep=%r prod row insert failed (peak_date=%s): %s",
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

        if is_chain:
            notes = (
                f"{av_gate_note}{substep_key}: {len(intervals)} chain episodes found "
                f"({len(chain_milestone_template)} milestones/episode, temporal_shape=chain), "
                f"{inserted} rows inserted into {TABLE} (generation={GENERATION_V3}) "
                f"and {PROD_TABLE} (generation={GENERATION_PROD}), "
                f"era_slice_key={era_slice_key}, "
                f"fingerprint={fingerprint}, "
                f"coverage_quality={quality_note['tier']} "
                f"({quality_note['target_count']} target(s))"
            )
        else:
            notes = (
                f"{av_gate_note}{substep_key}: {len(intervals)} intervals found, "
                f"{inserted} rows inserted into {TABLE} (generation={GENERATION_V3}) "
                f"and {PROD_TABLE} (generation={GENERATION_PROD}), "
                f"era_slice_key={era_slice_key}, "
                f"fingerprint={fingerprint}, "
                f"coverage_quality={quality_note['tier']} "
                f"({quality_note['target_count']} target(s))"
            )

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=inserted,
            duration_seconds=elapsed,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # CLI / direct-use fallback (drives own substeps; no orchestrator heartbeat)
    # ------------------------------------------------------------------

    def run(self, ctx: ContextSpec) -> WriterResult:
        """CLI path: drive all substeps sequentially (count depends on the
        chart's live gochara_resonance_map coverage — MR-16 dynamic plan;
        any chain-shaped classes among them are dispatched per MR-12 inside
        run_substep)."""
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
    "GENERATION_PROD",
    "PROD_TABLE",
    "TABLE",
    "ROW_SCHEMA_COLUMNS",
    "STAGING_ROW_SCHEMA_COLUMNS",
    "GocharaV3CenturyMaterializeWriter",
    "build_decade_slices",
    "compute_substep_fingerprint",
    "_fetch_class_valence",
    "_fetch_class_shape",
    "_normalize_milestone_template",
    "_build_chain_row",
    "_discover_event_classes",
    "_coverage_quality_note",
]
