---
artifact: DHARA_ENGINE_SPEC
version: 1.1
status: >
  REVIEWED — blind-drafted 2026-08-14 (commit 2737026b3); PARĪKṢAKA (opus, FM-26)
  issued FAIL on §3.1 (vectorized null algorithm incorrect: loop nesting inverted,
  ln_lambda wrongly claimed shared across replicates). Amended to v1.1 same date:
  §3.1 rewritten with correct C(t)+E((t−δ_r)modH) decomposition, REPLICATE-OUTSIDE
  BUCKET-INSIDE loop, periodic interpolation approach + equivalence-caveat. NullResult
  docstring fix (stale "256 by default") noted as P-B L-NULL task (non-blocking).
  PARĪKṢAKA re-review required before first P-B builder dispatches.
author: SAMPŪRTI-Δ1 conductor (R41, SM-R-10)
purpose: >
  Binding P-A DESIGN spec for P-B builders (L-ENGINE, L-NULL, L-TIER).
  Implements PURNA_KSHETRA_PLAN_v1_1.md §2 P1+P2+P3-a/b/d/e.
  Adversarial review: opus PARĪKṢAKA (FM-26) before any builder dispatched.
references:
  - PURNA_KSHETRA_PLAN_v1_1.md (SM-R-10, plan of record)
  - DHARA_DESIGN_v1_0.md (on main, PR #1276, commit 89bb6d74b)
  - SM-R-7 (suppression semantics: B, per-class filtered)
  - contracts.py NullResult (on main, PR #1275, commit d674d71e5)
  - PURNA_GROUNDING_REPORT_v1_0.md (G1–G12, ground-truth constraints)
changelog:
  v1.0: 2026-08-14 — blind draft (commit 2737026b3)
  v1.1: 2026-08-14 — §3.1 algorithm rewrite per PARĪKṢAKA FAIL (A6+B7)
---

# DHARA ENGINE SPEC v1.0 — P-B BUILD GUIDE

## 0. Scope

This document is the binding spec for P-B's three build lanes:

- **L-ENGINE (P1)**: Chart-level Layer 0 computation + per-class Layer 1 projection
- **L-NULL (P2)**: Vectorized null distribution (replaces dhara_compute_null's serial loop)
- **L-TIER (P3-a/b/d/e)**: Synthetic-baseline path for shape_only event classes

Scope NOT covered here (separate): P3-c (I-2 adversarial gate, runs post-P3-b census), P4
(priors research, parallel non-blocking lane), P5 (pin matrix), P6 (serving consistency).

## 1. LAYER 0 — Chart-Level Raw Matrix

### 1.1 Motivation (G1-G3 ground truth)

PURNA_GROUNDING_REPORT G1/G2/G3 confirmed that the following quantities are 100%
chart-level with zero class-dependence in their raw form:
- The lord stack per dasha system/level at each clock knot
- All 12 raw covariates x_j(t) at each knot
- Raw u_m(t) for every vighna instance in the chart

Today `writer.py`'s `_class_context()` rebuilds all three once per event class (27× rebuild
of identical structures). Layer 0 computes them ONCE per chart.

### 1.2 Data structure

```python
# Proposed (builder may refine naming but contract is binding):
@dataclass(frozen=True)
class Layer0:
    """Chart-level raw data, computed ONCE per chart, shared across all 27 classes."""
    # Knot set (combined clock + event knots, sorted, deduplicated)
    knots: np.ndarray  # shape (N_k,), float64, days from epoch
    # Lord stacks: for each dasha system + level, lord ID at each knot
    # Key: (system_id, level) → np.ndarray shape (N_k,) of lord IDs
    lord_stacks: dict[tuple[str, int], np.ndarray]
    # Raw covariates: 12 x_j values at each knot
    # Shape: (12, N_k), row i = covariate j=i
    covariates: np.ndarray  # shape (12, N_k)
    # Raw obstruction envelopes: u_m(t) at each knot
    # Key: vighna_key → np.ndarray shape (N_k,)
    obstructions: dict[str, np.ndarray]
```

**Decade-seam fix (G1/G2/G3, originally W1 in v1.0)**: Interior decade edges
`t = d * H/10` for `d = 1..9` MUST be added to the knot set in `assemble_knot_set`.
This is a zero-cost change (O(9) points) and eliminates the decade-seam artifact.

### 1.3 Computation order

1. Build K_c (clock knots: dasha boundaries at all active levels, per current `assemble_knot_set`) 
   PLUS the 9 interior decade knots.
2. Build K_e (event knots: from the evaluator's existing event-time set).
3. K = sorted(unique(K_c ∪ K_e)). Store as `Layer0.knots`.
4. For each (system_id, level) pair in the evaluator's dasha systems: evaluate lord at each knot.
   Store in `layer0.lord_stacks`.
5. For each of the 12 covariates: evaluate x_j(t) at each knot via `covariates_at`.
   Store in `layer0.covariates[j, :]`.
6. For each vighna instance in the chart: evaluate u_m(t) at each knot via `obstructions_at`.
   Store in `layer0.obstructions[vighna_key]`.

### 1.4 Thread-from-sweep optimization

Current `writer.py` calls `terms_at()` TWICE per knot (once in DHARA sweep at t_{i+1}, again
in row-materialization at seg.t_start). With Layer 0 pre-computed, the sweep indexes into
`layer0` arrays directly (O(1) per knot) instead of re-evaluating. The materialization step
also reads from `layer0` — no second evaluation.

This is the primary speedup: eliminates ~2× redundant evaluation across 60K+ knot points.

## 2. LAYER 1 — Per-Class Projection

### 2.1 What changes vs today

The existing `dhara_term_matrix.py` (`TermMatrixRow`/.npz schema) is **UNCHANGED**.
Layer 1 becomes a cheap projection: given Layer 0 and an event class `e`, produce the
same `TermMatrixRow` columns that stage 9/EXPLAIN already consume.

The projection is:
1. Retrieve routes for class `e` from `kala_field_routes WHERE event_class = e`.
2. **Lord relevance**: for each (system_id, level) in Layer 0, filter to routes that
   pass through lords in that layer. This is the "cheap step" G1 confirmed.
3. **Clock term C_e(t)**: sum over relevant lords, applying sign from `Route.suppressed_by`
   (existing behavior from `_best_route_for_lord` — no change).
4. **Covariate terms E_e(t)**: multiply Layer 0's shared x_j(t) by β_j for class e.
   β_j read from the term matrix's existing coefficient table (no change to coefficients).
5. **Suppression term S_e(t)** (SM-R-7, RULING B): filter `layer0.obstructions` to only
   keys appearing in any `Route.suppressed_by` tuple for class `e`. Pass filtered dict to
   `suppression_log_term`. A class with no suppressed routes gets S_e(t) = 1.0 identically.
   **This is the Layer 1 change SM-R-7 mandates** — currently the live code passes the
   UNFILTERED obstruction dict (the bug), Layer 1 projection adds the set-intersection.

### 2.2 API sketch

```python
def project_layer1(
    layer0: Layer0,
    event_class: str,
    routes: Sequence[Route],  # from kala_field_routes for this class
    beta: np.ndarray,         # shape (12,), from existing term matrix
) -> TermMatrixProjection:
    """Project Layer 0 to per-class Layer 1. Zero I/O; pure numpy."""
    # Step 5 suppression filter (SM-R-7):
    suppressed_keys = {
        key for r in routes for key in r.suppressed_by
    }
    filtered_obs = {k: v for k, v in layer0.obstructions.items() if k in suppressed_keys}
    # ... rest of projection
```

### 2.3 CI gate: Layer0→Layer1 equivalence (required for merge)

For the 6 already-working event classes (childbirth, marriage, foreign_settlement, career_change,
career_entry, death): at a random sample of 50 knots, `|Layer1.ln_lambda[t] - terms_at(t).ln_lambda|
< 1e-12`. This proves the refactor changed nothing observable for the calibrated classes.

Note: SM-R-7's suppression fix WILL produce a different value for classes where the live
obstruction dict was non-empty but none of the obstructions are in any Route.suppressed_by.
For those classes, the new value is CORRECT per the ruling (not a regression). The equivalence
test documents the expected differences.

## 3. VECTORIZED NULL (P2)

### 3.1 Design

The vectorized null replaces `dhara_compute_null`'s serial Python loop with numpy vectorized
operations. The mathematical result must be IDENTICAL to the current implementation at R=8 on
fixtures (acceptance criterion).

**Mathematical decomposition (plan §P2 notation, SM-R-10):**
```
ln λ_r(t) = C(t) + E((t − δ_r) mod H)
  C(t) = per-class clock/lord-relevance term, evaluated at t — FIXED across all replicates
  E(τ) = envelope term (covariates × beta + suppression log-term), at shifted time τ
  δ_r  = r · H / R  (cyclic shift for replicate r ∈ range(1, R))
  H    = chart horizon in days
```

`C(t)` depends only on which dasha lord is active at t (lord stacks from Layer 0, filtered
by per-class routes) — it is NOT shifted per-replicate. `E(τ)` uses covariate and obstruction
values at the shifted time τ = (t − δ_r) mod H, interpolated from Layer 0's pre-computed arrays.

**Algorithm — REPLICATE LOOP OUTSIDE, BUCKET LOOP INSIDE:**

```
1. Build K_null: coarse knot set restricted to _NULL_COARSE_LEVELS.
   (MD/AD/PD boundaries only — same coarse levels as today, L1g parity preserved.)
   Shape: (N_k,), float64.

2. Pre-compute ONCE (shared across all replicates):
   a. C_k = clock/lord-relevance component of Layer1.ln_lambda at each K_null knot.
      Use project_layer1(layer0, event_class, routes, beta) evaluated at K_null,
      taking only the lord-stack (C) contribution — NOT the envelope shift.
      Shape: (N_k,).
   b. cov_grid = Layer0.covariates restricted to K_null knots. Shape: (12, N_k).
   c. obs_grid = Layer0.obstructions (suppressed keys only, per SM-R-7) at K_null.
      Shape: (|S_e|, N_k).
   d. H = horizon_days.

3. For all R-1 replicates simultaneously (vectorized, no Python loop over r):
   a. delta = np.arange(1, R) * H / R          # shape (R-1,)
   b. tau_rk = np.mod(K_null[np.newaxis,:] - delta[:,np.newaxis], H)
                                                # shape (R-1, N_k)
   c. cov_rk  = interp_periodic(cov_grid, K_null, tau_rk)
                                                # shape (R-1, 12, N_k)
   d. obs_rk  = interp_periodic(obs_grid, K_null, tau_rk)
                                                # shape (R-1, |S_e|, N_k)
   e. E_rk    = beta @ cov_rk + suppression_log_term(obs_rk)
                                                # shape (R-1, N_k)
   f. ln_lambda_rk = C_k[np.newaxis, :] + E_rk # shape (R-1, N_k)
   g. lam_rk  = np.exp(ln_lambda_rk)
   h. dt_k    = np.diff(K_null, prepend=0)     # knot widths, shape (N_k,)
   i. cumul_rk = np.cumsum(lam_rk * dt_k[np.newaxis,:], axis=1)
                                                # shape (R-1, N_k)
   j. For each bucket b in DURATION_BUCKETS:   ← bucket loop INSIDE replicate block
      window_max_rb = vectorized_sliding_max(cumul_rk, width=b)  # shape (R-1,)
      all_stats[b].extend(window_max_rb.tolist())

4. q_threshold = np.percentile(lam_rk.ravel(), 95)

5. Return contracts.NullResult(
       replicates=R,
       max_stats=all_stats,
       q_threshold=q_threshold,
       shift_grid_step=H/R,
       shift_count=R-1,
       horizon_days=H,
       alpha=alpha,
   )
```

**Equivalence caveat (for builder — not negotiable):** The current `dhara_compute_null`
uses `integrator._refine` with adaptive midpoints between coarse knots (not just K_null).
This algorithm uses K_null knots + periodic interpolation. These are NOT identical by
construction. The R=8 equivalence test (§3.3, tol 1e-6) is the **sole binding gate**.
If the test fails: (a) densify K_null by adding midpoints at fraction ½ between adjacent
K_null knots, OR (b) compute the adaptive breakpoints for the unshifted evaluator and
interpolate at those + shifted versions. The builder chooses whichever approach passes
the gate. The gate is non-negotiable regardless of approach.

### 3.2 Key constants (non-negotiable)

- `DEFAULT_REPLICATES = 1024` (SM-R-8 mandate; OPT-N3 R=256 VOIDED)
- `SET LOCAL idle_in_transaction_session_timeout = '900000ms'` (FM-24: NEVER 0)
- `_RESUME_VERSION: int` in writer.py MUST be bumped 5→6 (invalidates all R=256 checkpoints)
- `_NULL_COARSE_LEVELS` unchanged (L1g parity preserved)
- Result type: `contracts.NullResult` (from P0.b, PR #1275) — NOT dhara_null.NullResult

### 3.3 Acceptance gates

- `test_dhara_null_vectorized.py`: equivalence at R=8, 5 random fixtures, absolute tolerance 1e-6
  on `q_threshold` and each `max_stats[b][r]` value
- FM-25 perf-gate: `dhara_compute_null(ev, R=1024)` ≤ 120s wall-clock for the Abhisek chart
  (run in CI on the Cloud Run 4vCPU/8Gi spec — the SM-R-4 machine)

## 4. TIERS SPEC (P3-a/b/d/e)

### 4.1 P3-a: Synthetic-baseline path

New constant in `contracts.py`:
```python
SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT: float = 1.0
# Pinned: never silently chosen per-build. This is the synthetic expected lifetime
# event count used for shape_only classes. Do NOT adjust without a native ruling
# (changing it causes cross-snapshot diffs in null_p comparisons).
```

`hazard.py`'s `baseline_rate()` and `stage4_field.py`'s `require_baseline()`:
- Current: raise `ClassSkipped` unconditionally when no calibrated baseline exists.
- New: when `shape_only=True` flag is passed (writer explicitly in shape_only mode for
  this class), return `SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT` (tagged, not silent).

`HazardTerms` dataclass gains: `baseline_is_synthetic: bool` field. Threaded through to
every row the writer produces. This IS the earned-signal fix (§N.8) — a queryable tag,
not an inferred one.

### 4.2 P3-b: Absolute-field census (pre-merge deliverable)

Before ANY shape_only row is written, the builder produces a census table (in the PR
description) of every consumer of:
- `kala_field_windows.expected_count`
- `kala_field_null.max_stats` / `q_threshold`
- `kala_ahead_get`, `kala_now_get`, `kala_windows_get`, `kala_priority_get`
- `stage65`'s `CONTRAST_MIN_DELTA_LN_LAMBDA` diff
- `stage8_spec.py`'s `expected_count` field

For each consumer: SUPPRESS (null when baseline_is_synthetic), RELABEL (ratio/rank, proven
invariant per G5), or CONFIRMED-SAFE-AS-IS (invariance proof required, not asserted).

### 4.3 P3-d: Tier-basis table

27 rows, one per event class, columns:
| class | basis | rationale |
|---|---|---|
| childbirth | calibrated | 6 ne_v01 rows in brahma_class_priors |
| ... | ... | ... |
| career_change | not_applicable | ADJUDICATION-2 Tier N-iii |
| ... | ... | ... |
| (others) | shape_only | no calibrated prior; G8: no single flag decides |

Drafted by conductor, ratified by PRATINIDHI with written rationale per class,
committed BEFORE any shape_only row is written (§N.8 earned-signal discipline).

### 4.4 P3-e: Writer + serving changes

Writer:
- Reads tier-basis table at build time.
- Calibrated path: unchanged (C-1 guard stays exactly as strict).
- Shape_only path: uses P3-a's synthetic constructor; tags every row `baseline_is_synthetic=True`.

Serving:
- P3-b's census decisions implemented: suppressed fields → null; relabeled fields → ratio/rank.
- `resolution_disclosure`-style facets (mirrors gochara surface Δ3 R2 work).

## 5. CI gates summary

| Gate | Where | Criterion |
|---|---|---|
| Layer0→Layer1 equivalence | test_layer0_projection.py | \|Δ ln_lambda\| < 1e-12 at 50 sampled knots, 6 calibrated classes |
| Knot contiguity | test_knot_set.py | gaps == 0 for full horizon; interior decade knots present |
| Vectorized NULL equivalence | test_dhara_null_vectorized.py | R=8 fixtures, tol 1e-6 |
| FM-25 perf | test_perf_null.py | ≤120s wall on 4vCPU/8Gi |
| Suppression filter | test_layer1_suppression.py | shape_only class with no suppressed routes → S_e=1.0 |
| baseline_is_synthetic tag | test_shape_only.py | every shape_only row has tag; calibrated rows have False |
| Census deliverable | PR description | P3-b table reviewed and approved by PARĪKṢAKA before P3-e ships |

## 6. What is explicitly OUT OF SCOPE for P-B

- Changing the `.npz` contract (TermMatrixRow schema)
- Changing stage 9 / EXPLAIN / the serving contract for calibrated classes
- Any modification to `orchestrator.py` or `WriterBase`
- P4 (priors research) — parallel, non-blocking
- P5 (pin matrix) — parallel
- P6 (serving consistency sweep) — starts immediately per plan, independent
- P3-c (I-2 adversarial gate) — runs after P3-b census exists

---
*DHARA_ENGINE_SPEC_v1_0.md — BLIND DRAFT, not yet committed. Commit before first P-B builder
dispatches. PARĪKṢAKA opus review required before builder dispatch.*
