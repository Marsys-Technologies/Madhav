"""ka_gochara_v3_century_materialize — W3.4/W5.4/MR-16/MR-11(b)/PK-R-8 Century
horizon + slice receipts.

GOCHARA-UTKARSA campaign, wave W3.4 (original) + W5.4 (writer repoint) +
PARIṢKĀRA MR-16 (dynamic event-class discovery + honest per-class coverage
notes) + PARIṢKĀRA MR-38 (fingerprint version fold) + PARIṢKĀRA MR-11(b) /
ADJUDICATOR ruling PK-R-8 (peak-anchored era⊃month⊃day hierarchy, resolution
facet, shape gate).

Gate: W0.3 PASS (generation schema + utkarsha_builder role in place) +
      W3.2 PASS (interval_solver root-solved threshold crossings) +
      UTK-R1 ADJUDICATOR ruling (W5.4 repoint to kala_gochara_windows generation='3.0') +
      W3.1 PASS (ka_gochara_resonance derives up to 27 canonical event classes;
      see services/ka_gochara_resonance/writer.py + its 92/92 test suite) +
      MR-38 gate (test_mr38_fingerprint_version_fold.py): a synthetic
      writer-version (row-schema) bump forces cache invalidation and a real
      rewrite; re-running with no version change and no input change
      correctly skips +
      PK-R-8 gate (test_w33_resolution_hierarchy.py R8.1-R8.7 detectors):
      peak-anchoring replaces fixed-step tiling for month/day production.

PARIṢKĀRA MR-11(b) / PK-R-8 — PEAK-ANCHORED HIERARCHY (era⊃month⊃day)
-----------------------------------------------------------------------
The W3.3 hierarchy producer (services/gochara_v3/resolution_hierarchy.py)
was originally merged as CODE but never wired into a materializer — this
writer is that wiring. ADJUDICATOR ruling PK-R-8 additionally REPLACED the
original W3.3 fixed-step TILING design (30-day/1-day subdivision, midpoint-
sampled "peak") with genuine PEAK-ANCHORING: a real local-maximum scan on the
REUSED coarse series find_threshold_crossings already computes, admission
gated on the era window's OWN P90 (never lambda_thresh), greedy retention
with a minimum separation and a hard cap, and 1-day-resolution refinement of
each retained peak to its TRUE argmax before that date is ever served as
`peak_date`. See resolution_hierarchy.py's module docstring for the full
R8.1-R8.6 account.

R8.12 SHAPE GATE: the hierarchy (era/month/day tiers, `resolution` column
populated) is produced ONLY for event classes whose brahma_event_ontology.
temporal_shape is 'interval' or 'chain'. Point-canonical classes (marriage,
career_advancement, illness_acute, surgery — confirmed live schema, 2026-08)
get NO hierarchy tiers: this writer falls back to the PRE-MR-11(b) flat
production (one row per find_threshold_crossings interval, `resolution`
column NULL) for those classes — "all tiers inherit the class's ontology
shape" (PK-R-7(iv)/BRIEF_D5 §3, both directions). See
`_fetch_event_class_temporal_shape`.

R8.8 PEAK_BASIS VOCABULARY: every row's `peak_basis` is now one of the three
named constants in `services/gochara_v3/peak_basis_vocab.py` — never the
retired bare literal `'gochara_lambda_v3'`. Era-tier (and shape-gated flat)
rows, whose peak comes from interval_solver's 50-sample coarse dense scan,
are stamped `LAMBDA_V3_COARSE_ARGMAX`; month/day-tier rows, whose peak is the
day-refined true argmax (R8.5), are stamped `LAMBDA_V3_ARGMAX` — the ONLY
basis that earns `is_timing_window=True` at serve time (register_gochara_
windows.ts, R8.9).

R8.13 PEAK ACCOUNTING: every substep's WriterResult.notes reports
era_windows/peaks_scanned/peaks_admitted/peaks_retained/month_rows/day_rows,
and a named zero_peaks_reason ('flat_lambda_curve'|'no_candidate_above_p90'|
'era_window_too_short'|'lost_to_pooled_retention') whenever peaks_retained==0
— never a bare/undated "0 rows" note. ROW-COUNT BOUND CORRECTION (MR-45,
register MASTER_REMEDIATION_REGISTER_v2_0.md): the PK-R-8/MR-11 disclosure
of "<=7 rows/substep (60-420/chart)" assumed exactly one era window per
substep (test_w33_resolution_hierarchy.py's R8.7 anti-explosion bound of 7
is a PER-ERA-WINDOW bound: 1 era + <=3 month + <=3 day). Production has
confirmed >=2 era windows CAN occur in a single substep (chart 482012f1,
career_setback::g3_2014_2024 — the real MR-44/MR-45 collision case). The
honest per-substep bound, accounting for N_era era windows in one decade
slice, is `N_era + 2*min(3*N_era, ceil(decade_days/90))` (each era window
contributes at most 3 peaks per MAX_PEAKS_PER_ERA_WINDOW, but the pooled
MIN_PEAK_SEPARATION_DAYS=90 retention (MR-44) additionally caps the total
retainable peaks across the whole decade at ceil(decade_days/90); each
retained peak contributes one month row + one day row, hence the factor of
2; the leading N_era term is the era-tier rows themselves).

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

ENGINE_VERSION COMPOSITION NOTE: MR-16 bumped ENGINE_VERSION "v3.0" ->
"v3.1" for its own scope/output-shape change (dynamic event-class discovery
+ coverage_quality note in suppression_state). PARIṢKĀRA MR-11(b)/PK-R-8's
hierarchy rewrite (this same lane, pre-production — no v3.1-tagged row has
ever been written to production under the OLD tiled-hierarchy shape) folds
into that SAME "v3.1" bump rather than requiring a second one: no
already-built corpus exists under a tiled-hierarchy v3.1 shape that a new
bump would need to invalidate. MR-38's row_schema_* fold is an independent,
composable input to the SAME hashed payload regardless.

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

R8.11 CLASS SCOPE (PK-R-8): the hierarchy producer runs for EVERY class
`_discover_event_classes` returns — there is no separate "LEL-represented
classes" allowlist (that phrase is not machine-resolvable against any live
table; ADJUDICATOR ruling confirms this). R8.12's shape gate (not a class
allowlist) is the only thing that varies behavior per class.

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
          ENGINE_VERSION, resonance_targets, row-schema) via MD5.
       c. Check kala_gochara_v2_build_state for a matching stored fingerprint.
       d. If fingerprint unchanged AND rows exist: skip (honest no-op).
       e. Else: fetch the class's ontology temporal_shape (R8.12 shape gate).
          - 'interval'/'chain': build_resolution_hierarchy (peak-anchored
            era⊃month⊃day, PK-R-8) over the decade JD range.
          - 'point' (or lookup failure, conservative default): flat
            find_threshold_crossings production, resolution=NULL (pre-
            MR-11(b) shape, unchanged for these classes).
          DELETE-then-INSERT results into BOTH:
            * kala_gochara_windows_v2 (calibration/staging surface, generation='g3_utkarsha')
            * kala_gochara_windows (production surface, generation='3.0') [W5.4 repoint]
       f. Upsert fingerprint to kala_gochara_v2_build_state.
       g. Log wall-clock time + peak accounting (R8.13) per substep at DEBUG.
  3. I2 constraint: ZERO imports from gochara_grammar/*, gochara_intensity/*,
     or ka_gochara_sweep/*. All scoring comes from gochara_v3.interval_solver,
     gochara_v3.resolution_hierarchy, and gochara_v3.engine (AC6). The
     dynamic event-class discovery query (MR-16) and the shape-gate query
     (R8.12) are plain SQL reads against gochara_resonance_map/brahma_event_
     ontology — the same tables `_fetch_resonance_targets`/`fetch_base_rate_
     for_class` already read — not an import of any forbidden module.
  4. I4 constraint: empty resonance targets → honest 0 rows for that substep,
     no fabrication (AC7). An empty resonance MAP (no event_class rows at
     all for this chart) → honest 0-substep plan (MR-16, same I4 discipline
     one level up). Zero retained peaks (R8.13) → honest 0 month/day rows,
     never a fallback fabrication.

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
import uuid
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
# PARIṢKĀRA MR-11(b) / PK-R-8: the peak-anchored hierarchy producer
# (era⊃month⊃day, parent_window_id, R8.1-R8.6) — see resolution_hierarchy.py
# module docstring for the full account. build_resolution_hierarchy itself
# calls find_threshold_crossings internally (era detection + reused coarse
# series) — already covered by the I2 static-import-check above
# (resolution_hierarchy.py is gochara_v3/*, not gochara_grammar/
# gochara_intensity/ka_gochara_sweep).
from services.gochara_v3.resolution_hierarchy import (
    build_resolution_hierarchy,
    WindowResolutionRecord,
)
# R8.8: named peak_basis vocabulary — writers use these constants, never a
# bare string literal (source-guarded, see test_peak_basis_vocab_used_not_
# literal in this module's test suite).
from services.gochara_v3 import peak_basis_vocab
# PARIṢKĀRA MR-47 (ADJUDICATOR ruling PK-R-10): named shape_conformance
# vocabulary — writers use these constants, never a bare string literal
# (source-guarded, see test_shape_conformance_vocab_used_not_literal in this
# module's test suite). See shape_conformance_vocab.py's own docstring for
# the full PK-R-10 account of the defect this closes.
from services.gochara_v3 import shape_conformance_vocab

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
# v3.0 -> v3.1 composes FOUR independent scope/shape changes landed together
# (concurrent lanes) in the same PARIṢKĀRA wave (Codex C2: any materializer
# output shape/scope change bumps ENGINE_VERSION):
#   (a) MR-16 — plan_substeps now discovers its event-class set dynamically
#       from gochara_resonance_map instead of a hardcoded 6-class list, and
#       every row carries a new coverage_quality note in suppression_state.
#   (b) MR-12 — chain-shaped rows (temporal_shape='chain') are now possible
#       for whatever event_class a substep is planned for; see
#       `_fetch_class_shape`/`_build_chain_row` and the 'chain' branch of
#       run_substep's shape gate.
#   (c) PARIṢKĀRA MR-11(b) / ADJUDICATOR ruling PK-R-8 — peak-anchored
#       era⊃month⊃day hierarchy (replacing the original W3.3 tiling design),
#       resolution facet, R8.12 shape gate, R8.8 peak_basis vocabulary. This
#       entire lane is pre-production (no v3.1-tagged row has ever been
#       written under the OLD tiled-hierarchy shape PK-R-8 replaced), so
#       there is no already-built corpus a second bump would need to
#       invalidate.
#   (d) MR-42 (PK-R-5/PK-R-9, 2026-08-11) — `suppression_state` is now a
#       structured {"mechanism":..., "value":...} object forwarding the
#       real quality_gates detail, never a bare {} placeholder -- see
#       `_build_suppression_state`.
# All four are delta-fingerprint-relevant per compute_substep_fingerprint's
# own "engine_version bumped when scoring logic OR output shape changes"
# contract, even though existing point-canonical classes' scoring is
# byte-for-byte unchanged. One bump, not four — there is only one
# ENGINE_VERSION value to compose into; every stored fingerprint must
# invalidate and re-materialize under the new shape rather than being
# silently skipped as "unchanged" by the fingerprint check in `run_substep`.
# Per Codex C2 convention: exactly this string, so concurrent lanes making
# the identical bump auto-merge cleanly.
ENGINE_VERSION = "v3.2"

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
# PARIṢKĀRA MR-11(b): +resolution, +parent_window_id (migration 567) and
# RETURNING id -- the writer must capture each inserted row's own bigint id
# so a subsequently-inserted CHILD row (month under era, day under month) can
# carry the correct parent_window_id. See run_substep's insert loop.
# PARIṢKĀRA MR-47 (PK-R-10): +shape_conformance (migration 570) -- the
# earned, explicit marker proving this row's temporal_shape was checked
# against brahma_event_ontology at WRITE time. See shape_conformance_vocab.py.
INSERT_SQL = f"""
    INSERT INTO {TABLE}
      (chart_id, event_class, temporal_shape,
       window_start, window_end, peak_date,
       milestone_id, is_irreversibility_milestone,
       signed_intensity, raw_intensity, valence, is_adverse,
       active_sentences, contributing_systems, suppression_state,
       peak_basis, calibration_state, source, generation, era_slice_key,
       term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source,
       resolution, parent_window_id, shape_conformance)
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
       %(ci_source)s,
       %(resolution)s, %(parent_window_id)s, %(shape_conformance)s)
    RETURNING id
"""

# INSERT template for kala_gochara_windows (production, W5.4 repoint, UTK-R1).
# Every DML on this table MUST carry generation='3.0' — enforced by the
# mutation-guard test (test_ka_gochara_v3_mutation_guard.py).
# I1 mutation-guard anchor: generation='3.0' (%(generation)s parameter always
# bound to GENERATION_PROD='3.0'; literal here for static-source guard coverage).
# PARIṢKĀRA MR-14: same 4 W1.5 columns as INSERT_SQL above (migration 564
# added them to this table, nullable, additive — see MASTER_REMEDIATION_
# REGISTER_v2_0.md MR-01/MR-14).
# PARIṢKĀRA MR-11(b): same +resolution/+parent_window_id/RETURNING id as
# INSERT_SQL above (migration 567 mirrors the columns onto both tables).
# PARIṢKĀRA MR-47 (PK-R-10): +shape_conformance (migration 570), same as
# INSERT_SQL above.
INSERT_PROD_SQL = f"""
    INSERT INTO {PROD_TABLE}
      (chart_id, event_class, temporal_shape,
       window_start, window_end, peak_date,
       milestone_id, is_irreversibility_milestone,
       signed_intensity, raw_intensity, valence, is_adverse,
       active_sentences, contributing_systems, suppression_state,
       peak_basis, calibration_state, source, generation, era_slice_key,
       term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source,
       resolution, parent_window_id, shape_conformance)
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
       %(ci_source)s,
       %(resolution)s, %(parent_window_id)s, %(shape_conformance)s)
    -- W5.4 I1 invariant: generation='3.0' only; v1 rows are protected by DB trigger
    RETURNING id
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
    peak_basis: str,
    generation: str,
    resolution: Optional[str] = None,
    parent_window_id: Optional[int] = None,
    coverage_quality: Optional[dict] = None,
    shape_conformance: str,
) -> dict[str, Any]:
    """Convert one MilestoneScore (gochara_v3.interval_solver) into a
    kala_gochara_windows(_v2) row dict — the chain-shape sibling of
    `_build_row`. Carries EXACTLY the same key set as `_build_row`'s
    returned dict (including the PARIṢKĀRA MR-11(b)/migration 567
    `resolution`/`parent_window_id` keys AND the MR-47/PK-R-10
    `shape_conformance` key — all required by INSERT_SQL/INSERT_PROD_SQL's
    parameter binding), so it binds against the SAME templates unchanged —
    no new DML statement is introduced, so the I1 mutation-guard's static
    source coverage (test_ka_gochara_v3_mutation_guard.py) needs no update
    for chain support.

    shape_conformance
        REQUIRED (PARIṢKĀRA MR-47, PK-R-10). A chain row is NEVER an
        envelope — whenever `run_substep` reaches this branch, the
        ontology's own `temporal_shape` is genuinely 'chain' (that is what
        routed this class here in the first place; see the R8.12 shape gate
        in `run_substep`), so this row's stamped `temporal_shape='chain'`
        always equals the ontology's declared shape. The caller therefore
        always passes `shape_conformance_vocab.SHAPE_CONFORMANCE_ONTOLOGY_
        MATCH` here — accepted as an explicit parameter (not hardcoded
        in-body) for the same "every value this function serves is an
        explicit parameter, never a re-derived assumption" discipline as
        every other field on this row.

    window_start = window_end = peak_date = this milestone's own JD (a
    chain-shaped row is one independently-dateable sub-window per milestone,
    per BRIEF_D5 §3 / migration 460's column comment).

    peak_basis
        REQUIRED. PK-R-8a (2026-08-11, ADJUDICATOR ruling, SUPERSEDES this
        lane's original R8.8 extension which stamped LAMBDA_V3_ARGMAX here):
        each milestone is evaluated at an EXACT, ontology-declared JD
        (episode_anchor_jd + typical_offset_days via score_chain_milestones)
        -- the date was DECLARED by brahma_event_ontology, not LOCATED by a
        peak search, so run_substep stamps peak_basis_vocab.
        ONTOLOGY_MILESTONE_OFFSET, never LAMBDA_V3_ARGMAX (that constant
        means "a located extremum", which no chain milestone ever is -- see
        peak_basis_vocab.py's own PK-R-8a docstring section). No default:
        every caller supplies a named peak_basis_vocab constant, never the
        retired bare literal.
    resolution, parent_window_id
        PK-R-8a (2026-08-11, SUPERSEDES this lane's original resolution=
        'day' stamp): run_substep now stamps resolution=None -- a chain row
        is not hierarchy-tier-classified at all (no era/month/day tier to
        assign it to; it earns is_timing_window through its OWN clause in
        the EARNED formula, keyed on peak_basis===ONTOLOGY_MILESTONE_OFFSET
        + a present milestone_id, never through the resolution-tier
        disjunct -- see register_gochara_windows.ts's
        deriveResolutionDisclosure). parent_window_id stays None (chain
        rows are independent per-milestone, no hierarchy parent to resolve
        regardless) -- both accepted here as explicit parameters (not
        derived in-body) matching `_build_row`'s own "every value this
        function serves is an explicit parameter" discipline.
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
        "peak_basis": peak_basis,
        "calibration_state": "structural_prior",
        "source": "live",
        "generation": generation,
        "era_slice_key": era_slice_key,
        "term_breakdown": json.dumps(term_breakdown) if term_breakdown is not None else None,
        "lambda_v3_ci_low": ci_low,
        "lambda_v3_ci_high": ci_high,
        "ci_source": ci_source,
        "resolution": resolution,
        "parent_window_id": parent_window_id,
        "shape_conformance": shape_conformance,
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

    R8.11 (PK-R-8): this IS the class scope for hierarchy production too —
    every class this function returns is eligible for the peak-anchored
    hierarchy (subject only to R8.12's shape gate, not a second allowlist).

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
# R8.12 SHAPE GATE — brahma_event_ontology.temporal_shape
# ---------------------------------------------------------------------------

def _fetch_event_class_temporal_shape(conn, event_class: str) -> str:
    """Return brahma_event_ontology.temporal_shape ('point'|'interval'|
    'chain') for `event_class` — the R8.12 SHAPE GATE input.

    The peak-anchored hierarchy (era/month/day tiers, `resolution` column
    populated) is produced ONLY for 'interval'/'chain' classes. Point-
    canonical classes (marriage, career_advancement, illness_acute, surgery
    — confirmed against live schema, 2026-08) get NO hierarchy tiers: this
    writer falls back to the flat (pre-MR-11(b)) production for them — "all
    tiers inherit the class's ontology shape" (PK-R-7(iv)/BRIEF_D5 §3, both
    directions; ADJUDICATOR ruling PK-R-8 R8.12).

    A lookup failure (DB error, or — should not happen, since gochara_
    resonance_map.event_class carries an FK into brahma_event_ontology.
    event_class_id, so any class _discover_event_classes returns already has
    a guaranteed ontology row — no row found) degrades to 'point': the
    CONSERVATIVE choice. Returning 'point' means "skip the hierarchy",
    which is always the SAFER default when the class's canonical shape could
    not be confirmed — it never risks stamping resolution tiers for a class
    that might not warrant them.

    Implemented as a thin wrapper over `_fetch_class_shape` (MR-12's own
    superset fetch — shape + milestone_template + irreversibility_milestone)
    so there is exactly ONE query implementation for
    brahma_event_ontology.temporal_shape, never two independently-drifting
    copies. `_fetch_class_shape`'s own fallback discipline (documented
    `_SHAPE_FALLBACK`, degrading to 'interval' for an unknown class) differs
    slightly from this function's 'point' conservative default for a
    genuine DB-error path; both are honest, documented choices for their own
    callers -- see each function's docstring for which applies when.
    """
    shape, _milestone_template, _irreversibility_milestone = _fetch_class_shape(conn, event_class)
    return shape


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
    peak_basis: str,
    generation: str = GENERATION_V3,
    term_breakdown: Optional[dict] = None,
    lambda_v3_ci_low: Optional[float] = None,
    lambda_v3_ci_high: Optional[float] = None,
    ci_source: Optional[str] = None,
    resolution: Optional[str] = None,
    parent_window_id: Optional[int] = None,
    coverage_quality: Optional[dict] = None,
    shape_conformance: str,
) -> dict[str, Any]:
    """Convert one IntervalBoundary/WindowResolutionRecord to a
    kala_gochara_windows(_v2) row dict.

    Parameters
    ----------
    shape_conformance
        REQUIRED (PARIṢKĀRA MR-47, ADJUDICATOR ruling PK-R-10) -- one of the
        named constants in `services.gochara_v3.shape_conformance_vocab`
        (SHAPE_CONFORMANCE_ONTOLOGY_MATCH for the real era⊃month⊃day
        hierarchy branch, where this row's stamped `temporal_shape`
        genuinely equals the class's ontology-declared shape;
        SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE for the R8.12 flat-production
        branch for point-canonical classes, where this row is honestly an
        envelope wearing 'interval' as a storage convenience). No default --
        every caller derives this from the SAME `class_shape` value
        `run_substep` already fetched via `_fetch_event_class_temporal_
        shape` for the R8.12 shape gate, never re-derived from a proxy (e.g.
        `resolution IS NULL`) and never a bare string literal. This closes
        the exact §N.7 item 3 defect PK-R-10 found: `temporal_shape` below
        was ALWAYS hardcoded `'interval'` regardless of which branch built
        this row, with nothing tracking whether that value was earned
        (a genuine hierarchy row) or borrowed (a point-canonical envelope).
        `temporal_shape` itself is UNCHANGED by this fix -- still stamped
        `'interval'` here in every case (see the module's R8.12 docstring
        section); `shape_conformance` is a NEW, additive field, not a
        replacement.
    valence
        REQUIRED -- the honest per-event_class valence
        ('gain'|'loss'|'neutral'|'mixed'), from `_fetch_class_valence`.
        No default: every caller must supply an honestly-derived value
        rather than a fixed literal (PARIṢKĀRA MR-13 fix -- this parameter
        used to be a hardcoded "favourable" string inside this function).
    is_adverse
        REQUIRED -- companion boolean from `_fetch_class_valence`.
    peak_basis
        REQUIRED (PK-R-8 R8.8) -- one of the named constants in
        `services.gochara_v3.peak_basis_vocab` (LAMBDA_V3_ARGMAX for a
        day-refined true peak on a month/day-tier row; LAMBDA_V3_COARSE_
        ARGMAX for an era-tier or shape-gated-flat row's coarse dense-scan
        peak). No default -- every caller must supply the correct basis for
        the tier it is building; the retired bare literal
        'gochara_lambda_v3' must never be passed here for a NEW row.
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
    resolution
        PARIṢKĀRA MR-11(b) (migration 567): the hierarchy tier this row was
        produced at -- 'era'|'month'|'day', from
        `WindowResolutionRecord.resolution_tier`. None for shape-gated flat
        rows (R8.12, point-canonical classes) and for any caller with no
        hierarchy classification for this row.
    parent_window_id
        PARIṢKĀRA MR-11(b) (migration 567): the DB-assigned bigint `id` of
        this row's widest containing coarser-tier window IN THE SAME TABLE
        (resolved by the caller via an id map keyed on the hierarchy's
        internal UUID `window_id`, populated as parent rows are inserted
        before their children — see run_substep). None for era-tier rows
        (no coarser parent) and for any row whose parent failed to resolve.
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
        "peak_basis": peak_basis,
        "calibration_state": "structural_prior",
        "source": "live",
        "generation": generation,
        "era_slice_key": era_slice_key,
        "term_breakdown": json.dumps(term_breakdown) if term_breakdown is not None else None,
        "lambda_v3_ci_low": lambda_v3_ci_low,
        "lambda_v3_ci_high": lambda_v3_ci_high,
        "ci_source": ci_source,
        "resolution": resolution,
        "parent_window_id": parent_window_id,
        "shape_conformance": shape_conformance,
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

        R8.11: every discovered class is in scope for hierarchy production
        (subject to R8.12's per-class shape gate at run_substep time) — there
        is no separate class allowlist here.

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
          4. Compute delta fingerprint (MR-38: row-schema-folded).
          5. Check stored fingerprint — if unchanged and rows exist: skip.
          6. Fetch the class's ontology temporal_shape (R8.12 shape gate);
             'interval'/'chain' -> build_resolution_hierarchy (peak-anchored,
             PK-R-8); 'point' (or lookup failure) -> flat find_threshold_
             crossings production, resolution=NULL (pre-MR-11(b) shape).
          7. DELETE-then-INSERT into kala_gochara_windows_v2 and
             kala_gochara_windows, every row carrying coverage_quality
             inside suppression_state and a named peak_basis (R8.8).
          8. Upsert fingerprint to kala_gochara_v2_build_state.
          9. Log wall-clock time + peak accounting (R8.13) at DEBUG.
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

        # 6. Structural-prior threshold: the v3 engine is bounded in [0,1],
        #    so we gate at 0.0 (emit all active intervals) as the honest
        #    structural prior before per-class calibration. This is a
        #    deliberate design choice for W3.4 — the full self-normalizing
        #    threshold (W1.4) is applied at serve time.
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

        # 6b. SHAPE GATE (PARIṢKĀRA MR-12 origin + PK-R-8 R8.12 generalization).
        #     BRIEF_D5 §3 (BINDING): a served row's shape must mirror
        #     brahma_event_ontology.temporal_shape.
        #       'interval' -> peak-anchored era⊃month⊃day hierarchy (PK-R-8).
        #       'chain'    -> one row per milestone_template entry
        #                     (score_chain_milestones, MR-12).
        #       'point' (or lookup failure, conservative default)
        #                  -> flat find_threshold_crossings production,
        #                     resolution='era' (R2 SEV-2: was NULL pre-R2,
        #                     causing buildNestedHierarchy to demote rows to
        #                     legacy_flat; now 'era' so rows land in roots).
        # class_shape drives the branch below; _fetch_event_class_temporal_
        # shape is the R8.12-named entry point (kept as a thin wrapper over
        # _fetch_class_shape -- see its own docstring) so existing shape-gate
        # tests that monkeypatch it by name keep working unchanged. Milestone
        # template data (needed only for the 'chain' branch) is fetched
        # separately via _fetch_class_shape below -- a second query only for
        # chain-shaped classes, never for the much more common point/interval
        # classes.
        class_shape = _fetch_event_class_temporal_shape(conn, event_class)
        is_chain = class_shape == "chain"

        # PARIṢKĀRA MR-47 (ADJUDICATOR ruling PK-R-10): derive shape_
        # conformance from the SAME class_shape value fetched above -- never
        # a proxy (e.g. resolution IS NULL), never a bare string literal.
        # class_shape is constant for this entire run_substep call (only ONE
        # of the interval/chain/flat-point branches below ever populates
        # insert_specs), so ONE derivation here correctly covers every row
        # this call builds:
        #   'interval' branch -> real era⊃month⊃day hierarchy: the stored
        #     temporal_shape genuinely equals the ontology's declared shape.
        #   'chain' branch (_build_chain_row) -> genuinely chain-shaped,
        #     never an envelope.
        #   R8.12 flat-production (else) branch -> a point-canonical (or
        #     lookup-failure-conservative-default) class's row: an honest
        #     flat context envelope, not a genuine interval production.
        if class_shape == "interval" or is_chain:
            row_shape_conformance = shape_conformance_vocab.SHAPE_CONFORMANCE_ONTOLOGY_MATCH
        else:
            row_shape_conformance = shape_conformance_vocab.SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE

        chain_milestone_template: list[dict] = []
        if is_chain:
            _, _raw_milestone_template, _irreversibility_milestone = _fetch_class_shape(
                conn, event_class,
            )
            if _raw_milestone_template:
                chain_milestone_template = _normalize_milestone_template(
                    _raw_milestone_template, _irreversibility_milestone,
                )

        if is_chain and not chain_milestone_template:
            # I4 honest gap: the ontology declares this class chain-shaped but
            # carries no usable milestone_template (or the live read failed
            # and no documented fallback template exists for this class).
            # Return BEFORE any DELETE/INSERT is issued, no fingerprint
            # upsert — never a fabricated row (I4).
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

        # Peak-accounting locals (R8.13) — populated by whichever branch runs.
        era_count = 0
        peaks_scanned = 0
        peaks_admitted = 0
        peaks_retained = 0
        month_count = 0
        day_count = 0
        zero_peaks_reason: Optional[str] = None
        chain_episode_count = 0

        # insert_specs: uniform list of
        #   (boundary_like, resolution_or_None, peak_basis, own_key, parent_key)
        # in PARENT-BEFORE-CHILD order — the insert loop below captures each
        # parent row's DB-assigned bigint id (RETURNING id) before any child
        # row that must reference it via parent_window_id is inserted. Used
        # by the 'interval' and 'point' branches; the 'chain' branch below
        # builds its rows directly (a MilestoneScore is not a boundary-like
        # object -- _build_chain_row has its own signature) but still shares
        # the SAME insert loop's DB-write/id-capture MECHANICS by degenerating
        # to (milestone, "day", LAMBDA_V3_ARGMAX, None, None) tuples paired
        # with a _build_chain_row-shaped closure -- see the chain branch.
        insert_specs: list[tuple[Any, Optional[str], str, Optional[str], Optional[str]]] = []

        if class_shape == "interval":
            # PARIṢKĀRA MR-11(b) / PK-R-8: build the full era⊃month⊃day
            # PEAK-ANCHORED hierarchy for this decade slice. build_resolution_
            # hierarchy calls find_threshold_crossings internally for era
            # detection (root-solved threshold crossings, unchanged
            # machinery) AND reuses that same coarse series for the peak scan
            # (R8.2) — no re-sweep, no fixed-step tiling (R8.1).
            hierarchy = build_resolution_hierarchy(
                swe=swe,
                context=context,
                start_jd=decade.start_jd,
                end_jd=decade.end_jd,
                threshold_config=threshold_config,
            )
            # Derived from the actual list length, not hierarchy.era_window_
            # count -- that field is a redundant summary set by build_
            # resolution_hierarchy itself; a HierarchyResult constructed by
            # hand (e.g. in a test fixture) without also setting it would
            # otherwise silently report a stale/wrong count here.
            era_count = len(hierarchy.era_windows)
            peaks_scanned = hierarchy.peaks_scanned
            peaks_admitted = hierarchy.peaks_admitted
            peaks_retained = hierarchy.peaks_retained
            month_count = len(hierarchy.month_windows)
            day_count = len(hierarchy.day_windows)
            zero_peaks_reason = hierarchy.zero_peaks_reason

            for record in hierarchy.era_windows:
                insert_specs.append((
                    record, "era", peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX,
                    record.window_id, record.parent_window_id,
                ))
            for record in hierarchy.month_windows:
                insert_specs.append((
                    record, "month", peak_basis_vocab.LAMBDA_V3_ARGMAX,
                    record.window_id, record.parent_window_id,
                ))
            for record in hierarchy.day_windows:
                insert_specs.append((
                    record, "day", peak_basis_vocab.LAMBDA_V3_ARGMAX,
                    record.window_id, record.parent_window_id,
                ))
        elif is_chain:
            # PARIṢKĀRA MR-12: chain production. Each detected episode
            # (IntervalBoundary from find_threshold_crossings, used here as
            # the episode ANCHOR only -- its enter_jd seeds score_chain_
            # milestones, the boundary itself is never served as a row) is
            # expanded into one row per milestone_template entry.
            #
            # PK-R-8a (2026-08-11, ADJUDICATOR ruling, SUPERSEDES this
            # lane's own prior R8.8/R8.9 extension of MR-12 below): a chain
            # milestone's date is DECLARED by brahma_event_ontology's
            # milestone_template (episode_anchor_jd + typical_offset_days),
            # not LOCATED by any peak search -- peak_basis=LAMBDA_V3_ARGMAX
            # was the wrong vocabulary entry for that (ARGMAX means "a
            # located extremum", which no chain milestone ever is). Chain
            # rows now carry peak_basis=ONTOLOGY_MILESTONE_OFFSET (its own
            # named basis, deliberately excluded from GENUINE_PEAK_BASES)
            # and resolution=NULL (chain rows are not hierarchy-tier-
            # classified at all -- no era/month/day tier, no parent_
            # window_id). A chain milestone still earns is_timing_window via
            # its OWN clause in the EARNED formula (temporal_shape==='chain'
            # AND peak_basis===ONTOLOGY_MILESTONE_OFFSET AND milestone_id
            # present), never by masquerading as a resolution-tier row --
            # see register_gochara_windows.ts's deriveResolutionDisclosure.
            chain_episodes = find_threshold_crossings(
                swe=swe, context=context,
                start_jd=decade.start_jd, end_jd=decade.end_jd,
                threshold_config=threshold_config, coarse_step_days=7.0,
            )
            chain_episode_count = len(chain_episodes)
            era_count = chain_episode_count
            for episode in chain_episodes:
                milestone_scores = score_chain_milestones(
                    swe, context, episode.enter_jd, chain_milestone_template,
                    threshold_config,
                )
                for ms in milestone_scores:
                    insert_specs.append((
                        ms, None, peak_basis_vocab.ONTOLOGY_MILESTONE_OFFSET, None, None,
                    ))
            day_count = len(insert_specs)
        else:
            # R8.12 shape gate: point-canonical class — NO hierarchy tiers.
            # Flat production: one row per detected interval,
            # resolution='era' (R2 SEV-2 fix: was NULL pre-R2, which caused
            # buildNestedHierarchy to route these rows to legacy_flat instead
            # of roots). The peak here is interval_solver's own 50-sample
            # coarse dense scan (IntervalBoundary.peak_lambda) —
            # LAMBDA_V3_COARSE_ARGMAX, never the day-refined ARGMAX basis
            # (R8.8). deriveResolutionDisclosure returns is_timing_window=true
            # for temporal_shape='point' regardless of resolution value (point-
            # clause short-circuits before the resolution check), so stamping
            # 'era' here preserves the timing claim while promoting these rows
            # from legacy_flat into roots in buildNestedHierarchy.
            flat_intervals = find_threshold_crossings(
                swe=swe, context=context,
                start_jd=decade.start_jd, end_jd=decade.end_jd,
                threshold_config=threshold_config, coarse_step_days=7.0,
            )
            era_count = len(flat_intervals)
            for interval in flat_intervals:
                # Stamp resolution='era' for decade-envelope point rows so
                # buildNestedHierarchy places them in roots (not legacy_flat).
                # deriveResolutionDisclosure returns is_timing_window=true for
                # temporal_shape='point' regardless of resolution value (point-
                # clause short-circuits), so timing claim is preserved.
                insert_specs.append((
                    interval, 'era', peak_basis_vocab.LAMBDA_V3_COARSE_ARGMAX,
                    None, None,
                ))

        shape_gate_note = f"shape={class_shape}"

        if ctx.dry_run:
            elapsed = time.time() - t0
            total_would_insert = len(insert_specs)
            logger.debug(
                "[%s] DRY RUN substep=%r chart=%s: %s, %d rows "
                "(era=%d month=%d day=%d) would be served. wall_clock_s=%.3f",
                ASSET_ID, substep_key, chart_id, shape_gate_note, total_would_insert,
                era_count, month_count, day_count, elapsed,
            )
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                rows_skipped=total_would_insert,
                duration_seconds=elapsed,
                notes=(
                    f"{av_gate_note}DRY RUN {substep_key}: {shape_gate_note}, "
                    f"{total_would_insert} rows found (era={era_count} month={month_count} "
                    f"day={day_count}) in {decade.year_start}–{decade.year_end} — nothing written"
                ),
            )

        # 7. DELETE-then-INSERT (§N.3 replace-not-accrete).
        #    Scoped to (chart_id, event_class, generation, era_slice_key) so
        #    a resubmit of this decade slice does not touch other slices.
        #    This scope covers ALL resolution tiers / chain rows for the
        #    substep — a resubmit cleanly replaces era+month+day (or the
        #    flat/chain rows) together, never leaving orphaned children from
        #    a prior run.
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
        # event_class) and passed to every _build_row/_build_chain_row call
        # below -- never a hardcoded "favourable" literal.
        class_valence, class_is_adverse = _fetch_class_valence(conn, event_class)

        # PARIṢKĀRA MR-11(b): id maps from the hierarchy's own internal UUID
        # window_id -> the DB-assigned bigint id this row received on INSERT,
        # kept SEPARATELY per table (kala_gochara_windows_v2 and
        # kala_gochara_windows have independent id sequences). A child
        # record's parent key (a UUID) is looked up in the map for the table
        # it is about to be inserted into; parent-before-child ordering
        # (insert_specs above) guarantees the parent's id is already present
        # by the time a child looks it up. A parent whose own INSERT failed
        # (or whose fetchone() returned nothing, e.g. a stubbed responder in
        # tests) simply leaves no entry — its children then honestly get
        # parent_window_id=None rather than a fabricated id. (Chain rows
        # never have a parent_key, so this map is unused for them.)
        v2_id_map: dict[str, int] = {}
        prod_id_map: dict[str, int] = {}

        inserted = 0
        for boundary, resolution, peak_basis, own_key, parent_key in insert_specs:
            is_chain_row = is_chain and isinstance(boundary, MilestoneScore)

            if is_chain_row:
                row_v2 = _build_chain_row(
                    chart_id, event_class, boundary, era_slice_key,
                    valence=class_valence, is_adverse=class_is_adverse,
                    generation=GENERATION_V3,
                    peak_basis=peak_basis,
                    resolution=resolution,
                    parent_window_id=None,
                    coverage_quality=quality_note,
                    shape_conformance=row_shape_conformance,
                )
            else:
                row_v2 = _build_row(
                    chart_id, event_class, boundary, era_slice_key,
                    valence=class_valence, is_adverse=class_is_adverse,
                    peak_basis=peak_basis,
                    generation=GENERATION_V3,
                    term_breakdown=boundary.term_breakdown,
                    lambda_v3_ci_low=boundary.lambda_v3_ci_low,
                    lambda_v3_ci_high=boundary.lambda_v3_ci_high,
                    ci_source=boundary.ci_source,
                    resolution=resolution,
                    parent_window_id=v2_id_map.get(parent_key) if parent_key else None,
                    coverage_quality=quality_note,
                    shape_conformance=row_shape_conformance,
                )
            try:
                cur = conn.execute(INSERT_SQL, row_v2)
                returned = cur.fetchone()
                if returned is not None:
                    new_id = returned["id"] if isinstance(returned, dict) else returned[0]
                    if own_key is not None:
                        v2_id_map[own_key] = new_id
                inserted += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[%s] substep=%r v2 row insert failed (resolution=%s): %s",
                    ASSET_ID, substep_key, resolution, exc,
                )

            # (b) Insert into production table (generation='3.0').
            #     I1 mutation-guard invariant: row carries generation='3.0'.
            if is_chain_row:
                row_prod = _build_chain_row(
                    chart_id, event_class, boundary, era_slice_key,
                    valence=class_valence, is_adverse=class_is_adverse,
                    generation=GENERATION_PROD,
                    peak_basis=peak_basis,
                    resolution=resolution,
                    parent_window_id=None,
                    coverage_quality=quality_note,
                    shape_conformance=row_shape_conformance,
                )
            else:
                row_prod = _build_row(
                    chart_id, event_class, boundary, era_slice_key,
                    valence=class_valence, is_adverse=class_is_adverse,
                    peak_basis=peak_basis,
                    generation=GENERATION_PROD,
                    term_breakdown=boundary.term_breakdown,
                    lambda_v3_ci_low=boundary.lambda_v3_ci_low,
                    lambda_v3_ci_high=boundary.lambda_v3_ci_high,
                    ci_source=boundary.ci_source,
                    resolution=resolution,
                    parent_window_id=prod_id_map.get(parent_key) if parent_key else None,
                    coverage_quality=quality_note,
                    shape_conformance=row_shape_conformance,
                )
            try:
                cur = conn.execute(INSERT_PROD_SQL, row_prod)
                returned = cur.fetchone()
                if returned is not None:
                    new_id = returned["id"] if isinstance(returned, dict) else returned[0]
                    if own_key is not None:
                        prod_id_map[own_key] = new_id
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[%s] substep=%r prod row insert failed (resolution=%s): %s",
                    ASSET_ID, substep_key, resolution, exc,
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

        # 9. Log wall-clock time + peak accounting at DEBUG (AC5 / R8.13).
        elapsed = time.time() - t0
        logger.debug(
            "[%s] substep=%r chart=%s: %s, %d rows inserted "
            "(era=%d peaks_scanned=%d peaks_admitted=%d peaks_retained=%d "
            "month=%d day=%d). wall_clock_s=%.3f",
            ASSET_ID, substep_key, chart_id, shape_gate_note, inserted,
            era_count, peaks_scanned, peaks_admitted, peaks_retained,
            month_count, day_count, elapsed,
        )

        # R8.13: WriterResult.notes carries the full peak-accounting report,
        # and a NAMED zero_peaks_reason whenever peaks_retained==0 for a
        # hierarchy-eligible class — never a bare/undifferentiated "0 rows".
        zero_peaks_part = (
            f", zero_peaks_reason={zero_peaks_reason}"
            if class_shape == "interval" and peaks_retained == 0 and zero_peaks_reason
            else ""
        )

        if is_chain:
            notes = (
                f"{av_gate_note}{substep_key}: {shape_gate_note}, "
                f"{chain_episode_count} chain episode(s) x "
                f"{len(chain_milestone_template)} milestone(s) = {inserted} rows "
                f"inserted into {TABLE} (generation={GENERATION_V3}) "
                f"and {PROD_TABLE} (generation={GENERATION_PROD}), "
                f"era_slice_key={era_slice_key}, "
                f"fingerprint={fingerprint}, "
                f"coverage_quality={quality_note['tier']} "
                f"({quality_note['target_count']} target(s))"
            )
        else:
            notes = (
                f"{av_gate_note}{substep_key}: {shape_gate_note}, "
                f"era_windows={era_count}, peaks_scanned={peaks_scanned}, "
                f"peaks_admitted={peaks_admitted}, peaks_retained={peaks_retained}, "
                f"month_rows={month_count}, day_rows={day_count}{zero_peaks_part}, "
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
    "_fetch_event_class_temporal_shape",
]
