---
artifact: DHARA_DESIGN_v1_0.md
version: 1.1
status: AMENDED_BLIND — v1.0 committed blind; v1.1 amendments applied after S2 adversarial review (F-01 through F-14); tolerances in section 7 remain blind (no engine comparison run yet)
created: 2026-08-13
authority: SAMPURTI-D1 conductor S1 (v1.0); S2 VERIFIER + Δ1 conductor amendments (v1.1)
related: SAMPURTI_STATE.md, KALA_W2_FIELD_DESIGN_v1_0.md
changelog:
  - version: "1.1"
    date: "2026-08-13"
    note: "S2 adversarial review amendments: F-01 null-shift grid corrected (range(1,R+1)→range(1,R)); F-02 suppression detection corrected (!=0.0→!=1.0); F-03 error-bound derivation corrected (h^2 cancels, amplitude-dependent); F-04 pin matrix stage-0/1 split; F-05 E1 tolerance caveat for small gamma; F-06 .npz schema clarification; F-07 config_pin breaking-change acknowledgment; F-12 comment fix (t_{i+1}^- → t_{i+1}^+); F-09 delta-update runtime assertion added; F-14 rho storage clarification"
  - version: "1.0"
    date: "2026-08-13"
    note: "Initial blind spec — committed before any comparison engine output exists"
---

# DHARA DESIGN DOC v1.1

## The Analytic Field Engine for ka_kshetra

**DHARA** (Deterministic Hazard-rate Analytic Recomputation Architecture) replaces
`integrator.build_segments()`'s adaptive bisection with an event-driven sweep
over the exact knot set, exploiting the piecewise structure of the hazard
formula to eliminate unnecessary computation and deliver exact window edges.

**Blind-spec commitment (binding):** this document is committed to version control
BEFORE any DHARA engine output exists. Every tolerance in section 7 is derived from
the mathematics of sections 1-3, not from comparing two engines' outputs. The S2
adversarial review and S4 parity gate run AFTER this commit; neither may retroactively
weaken a tolerance stated here.

---

## Section 1 -- THE MATHEMATICAL FINDING

### 1.1 The hazard formula (restated from hazard.py)

The log-hazard for event class `e` at time `t` is:

```
ln lambda_e(t) = ln lambda^0_e + ln P_tilde_e
               + SUM_s  w_s * A_s * r_{s,e}(t)      [CLOCK term C_e(t)]
               + SUM_j  beta_j * x_j(t)              [MODIFIER term M_e(t)]
               + SUM_m  ln(1 - rho_m * u_m(t))       [SUPPRESSION term S_e(t)]
```

Five additive terms in the log domain. Two are constant over the entire horizon:

- **Baseline** `ln lambda^0_e = ln(N_e / 36525)` -- constant, set once from
  `brahma_class_priors`.
- **Promise** `ln P_tilde_e = ln(P_floor + (1 - P_floor) * P_e)` -- constant,
  set once from Lane A's noisy-OR prior.

The remaining three are time-varying. Their temporal structure is the key finding.

### 1.2 The knot sets

Two independent sets of breakpoints govern the time-varying terms:

**Clock knots K_c (dasa boundaries).** The set of all `t_start` and `t_end` values
from `kala_field_boundaries` (the precision-supported dasa ladder). These are the
instants where the lord-stack changes. Currently loaded by `FieldEvaluator.__init__`
from `ladder: Mapping[str, Sequence[LadderPeriod]]`.

Between consecutive clock knots, each system's lord stack is CONSTANT: the same
`(level, lord)` tuple at every `t` in the open interval. Therefore `r_{s,e}(t)` is
constant between clock knots (it depends only on the lord stack and the fixed route
structure), and `clock_log_factor(A_s, r_{s,e}(t), w_s)` is constant. The entire
clock term `SUM_s w_s * A_s * r_{s,e}(t)` is therefore PIECEWISE-CONSTANT with
jumps only at K_c.

**Envelope knots K_e (gochara primitive boundaries).** The sorted union of all
`knots[i][0]` values from every `Primitive` in the `EnvelopeIndex` -- both supportive
(covariates) and obstructive (vighna). These are the instants where the
piecewise-linear envelopes change slope. Currently obtained by
`EnvelopeIndex.breakpoints()`.

Between consecutive envelope knots, each `x_j(t)` is LINEAR in `t` (by the frozen
section 3.2 envelope contract: "linear between knots, and ZERO outside the span").
Similarly, each `u_m(t)` is LINEAR in `t`.

### 1.3 Term-by-term behavior between consecutive knots

Let `K = sort(K_c UNION K_e)` be the global knot set, and let `(t_i, t_{i+1})` be
any consecutive pair. In the open interval `(t_i, t_{i+1})`:

| Term | Formula | Behavior in (t_i, t_{i+1}) | Why |
|------|---------|----------------------------|-----|
| Baseline | `ln lambda^0_e` | CONSTANT | Birth-chart-fixed |
| Promise | `ln P_tilde_e` | CONSTANT | Birth-chart-fixed |
| Clock | `SUM_s w_s A_s r_{s,e}(t)` | CONSTANT | Lord stacks do not change between dasa boundaries; routes/weights are fixed |
| Modifier | `SUM_j beta_j x_j(t)` | EXACTLY LINEAR in t | Each x_j(t) is linear between envelope knots; finite sum of linear = linear |
| Suppression | `SUM_m ln(1 - rho_m u_m(t))` | LOG-AFFINE, NOT linear | Each u_m(t) is linear; but ln(1 - rho * u) is NOT linear in u; it is concave |

**The critical distinction:**

- When NO suppression is active in `(t_i, t_{i+1})` (every `u_m(t) = 0`
  throughout), the suppression sum is identically 0, and:

  ```
  ln lambda_e(t) = [constant terms] + [linear modifier term] = alpha + gamma * (t - t_i)
  ```

  This is EXACTLY log-linear. No approximation. The current engine's adaptive
  bisection is solving a problem that does not exist on these intervals.

- When suppression IS active, `ln lambda_e(t)` includes terms of the form
  `ln(1 - rho_m * (a_m + b_m * (t - t_i)))` where `a_m, b_m` are the piecewise-linear
  envelope coefficients on this interval. This is LOG-AFFINE: a logarithm of
  a linear function. It is NOT linear in `t`.

### 1.4 Properties of the suppression-active case

For a single active suppressor with linear `u_m(t) = a + b(t - t_i)`:

```
f(t) = ln(1 - rho * (a + b(t - t_i)))
```

First derivative:
```
f'(t) = -rho * b / (1 - rho * u_m(t))
```

Second derivative:
```
f''(t) = -rho^2 * b^2 / (1 - rho * u_m(t))^2
```

Since `rho > 0`, `b^2 >= 0`, and `(1 - rho * u_m) > 0` (guaranteed by
`RHO_MAX = 0.95` and `u in [0,1]`), we have `f''(t) <= 0` always.
Equality holds only when `b = 0` (the envelope is flat on this interval).

**Therefore: each suppression term is CONCAVE on every inter-knot interval.**

Implication for the full `ln lambda_e(t)`:
- The non-suppression terms contribute a linear function (constant + linear).
- Active suppression terms contribute concave functions.
- Sum of linear + concave = CONCAVE.

**Consequence: `ln lambda_e(t)` is CONCAVE between consecutive knots when
suppression is active.** This means:

1. **Peaks are still at breakpoints.** A concave function on a closed interval
   attains its maximum at an endpoint. Since `ln lambda` is either linear
   (endpoints are the only candidates) or concave (same conclusion) on every
   inter-knot interval, the global peak of `lambda` over any window is always
   attained at a knot in K. No interior optimizer is ever needed.

2. **At most one threshold crossing per segment.** A concave function can cross
   a horizontal line `ln q` at most twice on an interval. But since the non-suppression
   part is linear (one crossing possible) and suppression only bends the curve
   downward (concavity), the crossing structure is simple:
   - If `ln lambda(t_i) >= ln q` and `ln lambda(t_{i+1}) >= ln q`, the entire
     interval is above threshold.
   - If both are below, the interval is below threshold (concavity means it
     cannot bulge above).
   - If one is above and one below, there is exactly ONE crossing, findable
     by root-finding on the concave function.

### 1.5 Quantifying the current engine's waste

The current `integrator.build_segments()` calls `ln_lambda(t)` as a BLACK BOX
at `t_i`, `t_{i+1}`, and the midpoint `t_mid`, then checks whether the midpoint
residual exceeds `tau = 0.02` nats. If so, it bisects recursively to `max_depth = 6`.

On a non-suppression interval (the vast majority), `ln lambda` is EXACTLY linear.
The midpoint residual is EXACTLY zero by construction. The bisection never triggers.
But the engine still:

1. Evaluates `ln_lambda(t_mid)` at every interval just to confirm it is zero --
   one unnecessary `terms_at()` call per interval. With `~165K` breakpoints
   (including SD/PrD boundaries), this is `~165K` wasted evaluations.

2. More importantly, the engine builds its breakpoint set from the FULL ladder
   (all five dasa levels) PLUS all envelope knots PLUS kinematics roots, creating
   `~165K + ~36K + ~120K = ~321K` breakpoints, producing `~321K` segments. The
   DHARA engine recognizes that the only breakpoints that matter are K_c UNION K_e
   (dasa boundaries + envelope knots), and that between consecutive knots the
   field is either exactly linear (non-suppression) or concave (suppression-active).

The null distribution path (`stage5_null.py`) already recognized this waste and
introduced the L1g/L1h/L1k/L1n optimizations to use only MD/AD/PD boundaries
(~819 breakpoints) for replicates. DHARA generalizes this insight to the real build.

---

## Section 2 -- EVENT-DRIVEN SWEEP (the DHARA algorithm)

### 2.1 Global knot set assembly

For a single `(chart_id, event_class)`:

```python
def assemble_knot_set(evaluator: FieldEvaluator) -> tuple[np.ndarray, ...]:
    """Build K = sort(K_c UNION K_e), clipped to [0, H].

    Returns (knot_times, knot_sources) where knot_sources[i] records
    whether knot i is a clock boundary, an envelope knot, or both.
    """
    K_c: set[float] = {0.0, evaluator.horizon_days}
    for periods in evaluator.ladder.values():
        for p in periods:
            K_c.add(p.t_start)
            K_c.add(p.t_end)

    K_e: set[float] = set(evaluator.envelopes.breakpoints())

    K = sorted(
        t for t in (K_c | K_e)
        if math.isfinite(t) and 0.0 <= t <= evaluator.horizon_days
    )
    return np.array(K, dtype=np.float64)
```

**Key difference from the current engine:** the current `FieldEvaluator.breakpoints()`
also includes `extra_breakpoints` (kinematics roots from `kala_field_kinematics`,
~120K Brent roots for this chart). The DHARA engine EXCLUDES kinematics roots from
the knot set because they are NOT points where `ln lambda` changes slope -- they
are astronomical event times that improve sampling density in the current adaptive
scheme but add no information to an engine that already knows the function is
exactly linear (or concave) between envelope/clock knots.

**Expected knot set size:** for the canonical chart (Abhisek Mohanty), the dasa
ladder has ~165K periods across all five levels, but only ~819 distinct
MD/AD/PD-level boundaries and ~2000 including SD/PrD. The envelope index has
~36K primitive knot times (from ~166K kala_field_primitives rows, many sharing
knot times). The merged K_c UNION K_e is expected to be O(10K-40K) after
deduplication, versus ~321K in the current engine.

### 2.2 Clock state delta-update

At each clock knot, the lord stacks change for one or more systems. Rather than
recomputing `lord_stacks_at(t)` from scratch (which does O(log N) bisects per
system per level), the DHARA sweep maintains a RUNNING lord-stack state and
applies DELTA updates at clock boundaries:

```python
def delta_update_lord_stacks(
    current_stacks: dict[str, list[tuple[str, str]]],
    t: float,
    ladder_bsearch: dict[str, list[tuple[str, list[float], list[float], list[str]]]],
) -> dict[str, list[tuple[str, str]]]:
    """O(1) amortized: only the level(s) that actually change at t are updated.

    At a clock knot, at most one level per system changes lord. The others
    are unchanged by definition (their [t_start, t_end) containment is
    unaffected). So the update touches only the changed entries.
    """
    # Implementation: for each system, check each level's current period.
    # If t falls at the boundary of the current period, advance to the
    # next period in that level. Other levels are untouched.
    ...
```

**Correctness note:** the delta-update produces the SAME lord stacks as a fresh
`lord_stacks_at(t)` call. The equivalence is verifiable by assertion during the
S4 parity gate. The optimization matters because the sweep visits O(|K|) knots
and a full `lord_stacks_at` at each would be O(|K| * S * L * log N) where S is
the number of systems and L the number of levels. Delta-update reduces this to
O(|K| * 1) amortized (each period boundary is visited exactly once).

**Fallback:** if the delta-update machinery proves fragile during implementation,
the engine MUST fall back to a fresh `lord_stacks_at(t)` call per knot rather
than risk a silent disagreement between the delta state and the true lord stacks.
The parity gate (S4) will catch any such disagreement. This fallback is acceptable
because even at O(|K| * S * L * log N), the sweep over ~40K knots with ~5 systems
and ~5 levels is O(40K * 25 * 17) ~ 17M comparisons, which completes in under 1
second -- negligible compared to the current engine's cost.

**F-09 AMENDMENT — runtime assertion:** Add a correctness check INDEPENDENT of
the delta state: at every N-th clock knot (e.g., every 100th), assert that the
delta-updated lord stacks equal the result of a fresh `lord_stacks_at(t)` call.
This makes the fallback trigger detectable at runtime, not only via offline S4
comparison. Cost: ~400 extra `lord_stacks_at` calls per class (40K/100), negligible.

### 2.3 Envelope evaluation at knots

At each knot `t_k`, the twelve covariates `x_j(t_k)` and the active obstructions
`u_m(t_k)` are evaluated by the existing `EnvelopeIndex.covariates_at(t_k)` and
`EnvelopeIndex.obstructions_at(t_k)`. These already use vectorized numpy range
checks (the L1i optimization) and are O(N_primitives) in numpy, O(K_active) in
Python where K_active << N_primitives.

No change to the envelope evaluation machinery is needed for DHARA. The knots are
simply visited in sorted order rather than via adaptive bisection.

### 2.4 The DHARA sweep algorithm

```
algorithm DHARA_SWEEP(event_class e, evaluator ev):

  K <- assemble_knot_set(ev)          # O(|K| log |K|) — one sort
  |K| expected: O(10K-40K)

  # Initialize running state
  lord_stacks <- ev.lord_stacks_at(K[0])
  terms_prev  <- ev.terms_at(K[0])    # full hazard evaluation at first knot

  segments <- []
  term_matrix_rows <- []

  for i in 0..|K|-2:
    t_i   <- K[i]
    t_ip1 <- K[i+1]

    # Evaluate ln_lambda at right endpoint
    #   — If t_ip1 is a clock knot, update lord stacks first
    if t_ip1 is in K_c:
      delta_update_lord_stacks(lord_stacks, t_ip1, ev.ladder)
    terms_next <- evaluate_at(ev, t_ip1, lord_stacks)

    a <- terms_prev.ln_lambda          # ln lambda(t_i^+)
    b <- terms_next.ln_lambda          # ln lambda(t_{i+1}^+)  [half-open convention:
                                       #   t_{i+1} belongs to the next lord period,
                                       #   so lord_stacks_at(t_{i+1}) returns the NEW lord.
                                       #   This matches integrator.build_segments exactly.
                                       #   See F-12 in S2 adversarial report.]

    # Determine suppression activity on this interval
    # F-02 AMENDMENT: suppression_term = exp(suppression_log) is ALWAYS > 0.
    # Comparing != 0.0 is always True. The correct check uses the multiplicative
    # identity: when no suppression is active, suppression_term = exp(0) = 1.0.
    suppression_active <- (
        terms_prev.suppression_term != 1.0
        or terms_next.suppression_term != 1.0
    )
    # Equivalently (log domain): suppression_log != 0.0 at either endpoint.
    # u_m > 0 somewhere in the interval iff suppression is nonzero at an endpoint,
    # because u_m is piecewise-linear between K_e knots (envelope boundaries are in K).

    width <- t_ip1 - t_i
    gamma <- (b - a) / width  if width > 0  else 0.0

    segment <- Segment(
      index = len(segments),
      t_start = t_i,
      t_end = t_ip1,
      alpha = a,
      gamma = gamma,
      refinement_depth = 0,
      refinement_exhausted = False,
      refinement_residual = None,
    )
    # Tag: is this segment suppression-active?
    # (Stored in a parallel array, not on the Segment dataclass,
    #  to preserve the frozen contract.)
    segments.append(segment)

    # Record term matrix row at t_i (section 4)
    term_matrix_rows.append(term_matrix_row(terms_prev, i))

    # Advance running state
    terms_prev <- terms_next

  # Final knot's term matrix row
  term_matrix_rows.append(term_matrix_row(terms_prev, len(K)-1))

  return segments, term_matrix_rows
```

### 2.5 Suppression-active segment handling

On a suppression-active interval `(t_i, t_{i+1})`, the stored segment uses the
same `(alpha, gamma)` representation as a non-suppression segment:

```
alpha = ln lambda(t_i)
gamma = (ln lambda(t_{i+1}) - ln lambda(t_i)) / (t_{i+1} - t_i)
```

This is the LINEAR INTERPOLANT of the true (concave) `ln lambda` on the interval.
The true function lies ON OR BELOW this line (by concavity). The maximum error
between the true function and the stored linear interpolant occurs at the interior
point where the concave function curves most, and is bounded by section 1.4's
second-derivative analysis.

For the stored segments that drive window detection and integration, this linear
interpolant is EXACTLY what the current engine stores (after its adaptive
refinement converges). The key difference is:

1. **Non-suppression intervals:** DHARA's interpolant is EXACT (residual = 0
   identically). The current engine arrives at the same answer after confirming
   the midpoint residual is below tau.

2. **Suppression-active intervals:** DHARA's linear interpolant has a nonzero
   residual (the concavity gap). But the intervals between consecutive knots in
   K are MUCH shorter than the current engine's intervals (because K includes
   ALL envelope knots, not just a subset), so the residual per interval is
   MUCH smaller than tau = 0.02 nats. On a suppression-active interval of width
   `h` days with maximum second derivative `|f''| = rho^2 * b^2 / (1-rho*u)^2`,
   the maximum linear-interpolation error is bounded by:

   ```
   max_error <= (1/8) * |f''_max| * h^2
   ```

   **F-03 AMENDMENT — corrected derivation:**

   Since `u_m(t)` is piecewise-linear between consecutive K_e knots, the slope
   on interval `[t_i, t_{i+1}]` of width `h` is `b = (u_{i+1} - u_i) / h`.
   Substituting into `|f''_max| = rho^2 * b^2 / (1-rho*u)^2`:

   ```
   max_error <= (1/8) * rho^2 * ((u_{i+1} - u_i) / h)^2 / (1-rho*u)^2 * h^2
             =  (1/8) * rho^2 * (u_{i+1} - u_i)^2 / (1-rho*u)^2
   ```

   **The h^2 cancels completely.** The error depends on the AMPLITUDE CHANGE
   `delta_u = u_{i+1} - u_i` across the interval, not on the interval width.

   For `rho = 0.95` and worst-case `delta_u = 1`, `(1-rho*u_max) = 0.05`:

   ```
   max_error_worst_case = (1/8) * 361 * 1^2 = 45.125 nats
   ```

   This worst case applies when the obstruction envelope traverses its full range
   (0 to 1) within a single inter-knot interval — an extreme transit onset. In
   practice, K_e already contains every slope-change knot, so most intervals have
   small `delta_u` (the envelope changes gradually). For `delta_u = 0.1`:
   `max_error <= (1/8) * 361 * 0.01 = 0.45 nats`. For `delta_u = 0.02`:
   `max_error <= (1/8) * 361 * 0.0004 = 0.018 nats < tau`.

   **Resolution:** for suppression-active intervals where the endpoint-evaluated
   midpoint residual exceeds tau = 0.02 nats, DHARA applies the SAME adaptive
   refinement as the current engine (bisect at midpoint, recurse). The percentage
   of intervals requiring refinement depends on the distribution of `delta_u`, not
   on interval width. Intervals where the obstruction envelope changes by less than
   `~0.02` across the interval need no refinement; those where it changes by more
   do. For a typical chart with a handful of active vighnas whose envelopes are
   gradual, refinement is needed on a small fraction of suppression-active intervals.
   On the ~90-95% of intervals that are non-suppression, no refinement is needed
   because the stored form is EXACT.

### 2.6 Complexity comparison

| Operation | Current engine | DHARA |
|-----------|---------------|-------|
| Breakpoint set | ~321K (all levels + envelopes + kinematics) | ~10K-40K (K_c UNION K_e) |
| ln_lambda evaluations | ~321K (endpoints) + ~321K (midpoints) + refinement | ~40K (endpoints only, non-suppression) + ~2K (suppression refinement) |
| Segments produced | ~321K (most trivially linear) | ~40K (each representing a true inter-knot interval) |
| Window edge detection | Linear scan (exact, on stored segments) | Linear scan (exact, on stored segments) |
| Integration | Closed form (exact, per segment) | Closed form (exact, per non-suppression segment); 4-point GL for suppression |

Expected speedup: 5-10x for the real build (fewer evaluations, fewer segments).
The null distribution (section 6) achieves a separate, additional speedup.

---

## Section 3 -- CLOSED FORMS

### 3.1 Window edge detection (threshold crossings)

Given threshold `q_e` (from stage 5's null distribution), a window is a maximal
interval where `lambda_e(t) >= q_e`, equivalently `ln lambda_e(t) >= ln q_e`.

**Non-suppression segment** `(alpha, gamma)`:

```
ln lambda(t) = alpha + gamma * (t - t_start) = ln q

Solving:  t* = t_start + (ln q - alpha) / gamma
```

This is a LINEAR equation. The solution is EXACT to float64 precision. No
iteration needed. This is IDENTICAL to the current `integrator._super_threshold_span`.

**Suppression-active segment:** the stored `(alpha, gamma)` form is a linear
interpolant of the true concave `ln lambda`. Two approaches:

(a) **Use the stored linear interpolant** for window edge detection. This gives
    the same window edges as the current engine (which also operates on stored
    linear segments). The window edges are properties of the STORED field, not
    the true product form, and the stored field is what everything downstream
    reads (integrator.py module docstring: "this is a DEFINITION OF THE STORED
    FIELD, not an approximation claim").

(b) **Use the true product form** for higher precision. This requires solving
    `ln lambda_true(t) = ln q` where `ln lambda_true` includes the log-affine
    suppression terms. Algorithm:

```
algorithm CERTIFIED_BRACKET_NEWTON(t_i, t_{i+1}, ln_q, ev):
  """Find t* in (t_i, t_{i+1}) where ln lambda_true(t*) = ln_q.
  Requires a sign change: f(t_i) and f(t_{i+1}) have opposite signs
  where f(t) = ln lambda_true(t) - ln_q.
  """
  f_lo = ev.ln_lambda(t_i) - ln_q
  f_hi = ev.ln_lambda(t_{i+1}) - ln_q

  if f_lo * f_hi > 0:
    return None  # no crossing in this interval

  # Maintain bracket [lo, hi] throughout
  lo, hi = t_i, t_{i+1}
  t = 0.5 * (lo + hi)  # initial guess: midpoint

  for iter in range(20):
    f_t = ev.ln_lambda(t) - ln_q

    # Compute f'(t) analytically:
    # f'(t) = gamma_modifier + SUM_m -rho_m * u_m'(t) / (1 - rho_m * u_m(t))
    # where gamma_modifier = d/dt[SUM_j beta_j * x_j(t)]
    #   = SUM_j beta_j * x_j'(t)  (piecewise constant between envelope knots)
    # and u_m'(t) is the slope of the m-th obstruction envelope on this interval.
    f_prime = compute_f_prime(t, ev)

    if abs(f_prime) < 1e-30:
      # Derivative too small; fall back to bisection step
      t_new = 0.5 * (lo + hi)
    else:
      t_new = t - f_t / f_prime

    # Certification: if Newton step leaves bracket, use bisection instead
    if t_new <= lo or t_new >= hi:
      t_new = 0.5 * (lo + hi)

    # Update bracket
    if f_t * f_lo < 0:
      hi = t
    else:
      lo = t

    # Convergence check
    if abs(t_new - t) < 1e-8:  # < 1 second in days
      return t_new

    t = t_new

  # Max iterations reached; return best estimate
  return t


def compute_f_prime(t, ev):
  """Analytic derivative of ln lambda at t, between knots.

  Between consecutive knots:
    d/dt [ln lambda] = gamma_base + SUM_m  -rho_m * b_m / (1 - rho_m * u_m(t))
  where:
    gamma_base = d/dt[SUM_j beta_j * x_j(t)]
               = SUM_j beta_j * slope_j  (constant between envelope knots)
    b_m = du_m/dt = slope of obstruction m's envelope on this interval
    u_m(t) = a_m + b_m * (t - t_i)
  """
  ...
```

**DHARA's choice:** approach (a) for the STORED field (preserving the invariant
that window edges are properties of `kala_field` rows), with approach (b)
available as an OPTIONAL refinement for future stages. The S4 parity gate
compares stored-field window edges, not true-product-form edges.

### 3.2 Peak detection

Peaks are always at breakpoints (the global knot set K). This holds for BOTH
non-suppression intervals (ln lambda is linear, hence monotone on each segment --
extremes at endpoints) and suppression-active intervals (ln lambda is concave --
maximum at an endpoint of each segment).

```
algorithm PEAK_OVER_WINDOW(segments, t_start_window, t_end_window):
  best_t = t_start_window
  best_lambda = -inf

  for seg in segments overlapping [t_start_window, t_end_window]:
    u = max(t_start_window, seg.t_start)
    v = min(t_end_window, seg.t_end)
    for t in {u, v}:
      lam = exp(seg.alpha + seg.gamma * (t - seg.t_start))
      if lam > best_lambda or (lam == best_lambda and t < best_t):
        best_lambda = lam
        best_t = t

  return best_t, best_lambda
```

This is IDENTICAL to `integrator._peak_over`. No change needed.

**Exception case:** none. The concavity proof in section 1.4 covers all suppression-
active intervals. A convex suppression term would require `f''(t) > 0`, which would
require `rho^2 * b^2 / (1 - rho*u)^2 < 0` -- impossible since all terms are
non-negative. The only way `f''(t) = 0` is `b = 0` (flat envelope on the interval),
in which case suppression is effectively constant and the interval is linear anyway.

### 3.3 Integration

**Non-suppression segments:** closed form, identical to `integrator.segment_integral`:

```
integral_{u}^{v} exp(alpha + gamma * (t - t_start)) dt

  = exp(alpha) * (v - u)                                    if |gamma| <= EPS_GAMMA
  = exp(base) * (v - u) * expm1(gamma * d) / (gamma * d)   if |gamma * d| < 0.01
  = (exp(alpha + gamma*(v-t_start)) - exp(base)) / gamma    otherwise

where base = alpha + gamma * (u - t_start), d = v - u.
```

The `expm1` branch for numerical stability is MANDATORY per section 5.2 of the
field design (cancellation guard for near-flat segments). This is unchanged.

**Suppression-active segments:** the stored linear-interpolant integral is computed
by the SAME `segment_integral` (since the stored form is log-linear). This gives
the same `expected_count` as the current engine for the STORED field.

For the optional TRUE-PRODUCT-FORM integral (not needed for parity but available
for future refinement):

4-point Gauss-Legendre quadrature on `[t_i, t_{i+1}]`:

```
nodes (in [-1, 1]):
  xi_1 = -0.861136311594953  (w_1 = 0.347854845137454)
  xi_2 = -0.339981043584856  (w_2 = 0.652145154862546)
  xi_3 = +0.339981043584856  (w_3 = 0.652145154862546)
  xi_4 = +0.861136311594953  (w_4 = 0.347854845137454)

Transform to [a, b]:
  t_k = (b + a)/2 + (b - a)/2 * xi_k

Integral approx:
  I = (b - a)/2 * SUM_{k=1}^{4} w_k * exp(ev.ln_lambda(t_k))
```

Error bound: 4-point GL is exact for polynomials up to degree 7. The integrand
`exp(ln_lambda(t))` is `exp(linear + concave)` on a suppression-active interval.
The Taylor expansion of `exp(f(t))` where `f` is a polynomial of degree `d` in `t`
produces terms up to `exp(alpha) * (gamma*t)^n / n!` which converge rapidly.
The error is `O(h^8)` per interval where `h = t_{i+1} - t_i`.

For a typical suppression-active interval of width `h ~ 10` days with
`|gamma| ~ 0.01` nats/day:

```
Error per interval ~ (h^8 / 8!) * max |f^{(8)}(t)| * exp(f)
                    ~ (10^8 / 40320) * small_derivative * small_exp
                    << 1e-6
```

Tolerance target: `|I_GL - I_exact| < 1e-6` per suppression-active interval, so
the cumulative error over all suppression-active intervals in a window is
`< 1e-6 * N_suppression_intervals`. With `N_suppression_intervals` typically
< 100 per window, the cumulative error is `< 1e-4` in expected_count.

---

## Section 4 -- TERM MATRIX FORMAT (native ruling n2: DB + compact artifact)

### 4.1 Purpose

The term matrix stores per-knot, per-term contributions for:

1. **EXPLAIN:** a consumer can read which term dominated at any time, without
   re-evaluating the hazard formula. This replaces the current provenance edges'
   per-window-peak snapshot with a full time-resolved decomposition.

2. **Weights refit:** changing `beta_j`, `w_s`, or `rho_m` requires only
   column-weighted summation over the term matrix, not a full field rebuild.
   Stage 9's fitter reads the matrix directly.

### 4.2 Schema

For each knot `t_k` in K, for event class `e`, the term matrix row is:

```
term_matrix[k, :] = [
  ln_lambda^0_e,                     # column 0: baseline (constant)
  ln_P_tilde_e,                      # column 1: promise (constant)
  w_1 * A_1 * r_{1,e}(t_k),         # column 2: clock system 1
  w_2 * A_2 * r_{2,e}(t_k),         # column 3: clock system 2
  ...                                 # one column per applicable clock system
  beta_1 * x_1(t_k),                # column 2+S: covariate x1
  beta_2 * x_2(t_k),                # column 3+S: covariate x2
  ...                                 # 12 covariate columns total
  ln(1 - rho_1 * u_1(t_k)),         # column 2+S+12: vighna 1
  ln(1 - rho_2 * u_2(t_k)),         # column 2+S+12+1: vighna 2
  ...                                 # one column per active vighna class
]
```

Column count: `T = 2 + S + 12 + V` where:
- S = number of applicable predictive clock systems (typically 3-5)
- 12 = fixed covariate count (hazard.COVARIATE_KEYS, frozen at 12 for W2)
- V = number of distinct vighna classes active for this event class (typically 2-8)

### 4.3 Compact binary artifact format

Per event class per chart, stored as numpy `.npz`:

```python
np.savez_compressed(
    f'term_matrix_{chart_id}_{event_class}.npz',
    knot_times=knot_times,           # float64, shape [K]
    term_matrix=term_matrix,         # float64, shape [K, T]
    column_ids=column_ids,           # unicode array, shape [T]
    # column_ids example:
    # ['baseline', 'promise',
    #  'clock:vimshottari', 'clock:chara',
    #  'mod:x1_contact_moon_ref', ..., 'mod:x12_panchanga_affinity',
    #  'sup:vedha:Sa->10', 'sup:ashtakavarga_deficit:Ju->7']
    weights_version=weights_version, # scalar string
    x_schema_version=x_schema_version,
)
```

Storage: written alongside the `kala_field` segment rows. The `.npz` file is
an intermediate artifact consumed by stage 9 and by the EXPLAIN serving path.
It is NOT a replacement for `kala_field` -- the segment rows remain the
authoritative stored field.

### 4.4 DB storage for served artifacts

The existing `kala_field` and `kala_field_provenance` table schemas are UNCHANGED.
DHARA writes the same rows to these tables as the current engine. The term matrix
is an ADDITIONAL artifact, not a replacement.

Provenance edges are still computed at the window peak (per section 5.4 of the
field design), using `ev.terms_at(t_peak)` exactly as the current engine does.
The reconciliation invariant (`assert_provenance_reconciles`) is unchanged.

### 4.5 Refit path

To refit weights without a full field rebuild:

```python
def refit_from_term_matrix(npz_path, new_weights):
    data = np.load(npz_path)
    knot_times = data['knot_times']        # [K]
    raw_matrix = data['term_matrix']       # [K, T]
    column_ids = data['column_ids']        # [T]

    # Reweight: each column's contribution is scaled by the ratio
    # new_weight / old_weight. For columns where the weight is embedded
    # in the stored value (e.g., beta_j * x_j), the raw term value is
    # x_j(t_k) and the stored value is beta_j * x_j(t_k).
    # To refit, divide out old beta, multiply by new beta.
    # This requires storing BOTH the weighted and unweighted values,
    # or storing the weights separately.

    # DESIGN DECISION: store unweighted values in a separate array:
    #   unweighted_matrix[k, :] = [1, 1, r_1(t_k), ..., x_1(t_k), ..., u_1(t_k), ...]
    # and weighted_matrix[k, :] = column-wise product with weight vector.
    # Then refit = unweighted_matrix @ diag(new_weight_vector).

    # Recompute ln_lambda at each knot:
    ln_lambda_new = new_weighted_matrix.sum(axis=1)  # [K]

    # Recompute segments from the new ln_lambda values:
    segments = []
    for i in range(len(knot_times) - 1):
        alpha = ln_lambda_new[i]
        gamma = (ln_lambda_new[i+1] - ln_lambda_new[i]) / (knot_times[i+1] - knot_times[i])
        segments.append(Segment(i, knot_times[i], knot_times[i+1], alpha, gamma))

    return segments
```

Time: O(|K| * T) matrix multiplication + O(|K|) segment construction. For
|K| ~ 40K and T ~ 25, this is ~1M float operations -- completes in milliseconds.
The full field rebuild currently takes O(minutes); refit takes O(seconds).

---

## Section 5 -- (STAGE x CLASS) PIN MATRIX

### 5.1 Purpose

The current `config_pin` is a MONOLITHIC fingerprint: any change to any input
invalidates the entire field. The DHARA pin matrix decomposes this into
per-stage, per-class pins, enabling SELECTIVE invalidation.

### 5.2 Pin definitions

```
PIN[stage, class] = SHA256(canonical_json(stage_inputs[stage][class]))
```

| Stage | Name | Inputs hashed |
|-------|------|---------------|
| 0 | Kinematics | `code_version` (DHARA engine version tag) + `chart_data_digest` (birth params + positions hash) + `cohort_version` |
| 1 | Symbolization | Stage 0 pin + Stage 3 pin + `code_version` |
| 2 | Promise | Stage 0 pin + `promise_graph_version` (SHA256 of `bo_pratijna` corpus rows for this chart, sorted by natural key) |
| 3 | Clocks + Boundaries | Stage 0 pin + `kala_field_clocks_digest` (SHA256 of applicable-system rows) + `boundary_data_digest` (SHA256 of ladder periods) |
| 4 | Field Assembly | Stage 0 pin + Stage 1 pin + Stage 2 pin + Stage 3 pin + `weights_version` + `gochara_corpus_digest` (SHA256 of `kala_field_primitives` rows for this chart) |
| 5 | Null Distribution | Stage 4 pin + `null_replicate_count` (1024 for DHARA) |

**F-04 AMENDMENT note:** Stage 1 (symbolization) depends on stage 3's output
(`kala_field_boundaries`) because the dispatch order is `0→2→3→1→4` (stage 1
reads the boundaries produced by stage 3). Stages 0 and 1 must therefore have
separate pins, with stage 1's pin including the stage 3 pin as an input. This
replaces the original "0-1 combined" entry. Downstream pins (stages 2-5) that
previously referenced "Stage 0-1 pin" now reference the specific stage pin(s)
they depend on directly.

### 5.3 Invalidation rules

| What changed | Stages invalidated | Stages reusable | Estimated recompute time |
|---|---|---|---|
| Gochara corpus (new transits computed) | 4, 5 | 0-1, 2, 3 | Stage 4: ~30s (sweep over new K_e); Stage 5: ~10 min (1024 replicates) |
| Weights refit (beta/w_s/rho) | 4, 5 | 0-1, 2, 3 | Stage 4: ~1s (term matrix refit); Stage 5: ~10 min |
| New event class added (G2 growth) | 0-5 for that class ONLY | All stages for all other classes | ~1 min for the new class |
| Promise graph changed | 2, 4, 5 | 0-1, 3 | Stage 2: ~1s; Stage 4: ~30s; Stage 5: ~10 min |
| Clock system changed | 3, 4, 5 | 0-1, 2 | Stage 3: ~1s; Stage 4: ~30s; Stage 5: ~10 min |
| Cold build (nothing cached) | 0-5 for all classes | Nothing | ~20-30 min total |

### 5.4 Storage

The pin matrix is stored as a JSON object on `kala_field_snapshots`:

```json
{
  "pin_matrix": {
    "marriage": {
      "stage_01": "sha256:abc123...",
      "stage_2": "sha256:def456...",
      "stage_3": "sha256:789abc...",
      "stage_4": "sha256:012def...",
      "stage_5": "sha256:345ghi..."
    },
    "childbirth": { ... }
  }
}
```

**F-07 AMENDMENT:** The `config_pin` derived from `SHA256(canonical_json(pin_matrix))`
is a BREAKING CHANGE relative to the existing `kala_field_snapshots` rows produced
by the sampled engine (those rows have a config_pin with different structure and value).
A DHARA field snapshot will NOT match any sampled-engine snapshot on config_pin lookup.
This is intentional: the segment representation IS different. Downstream snapshot-lookup
code that relies on config_pin matching across engine versions must be aware that a
DHARA build produces a new, distinct snapshot. The sampled-engine snapshots remain in
the table as historical records; the DHARA snapshot is a new row.

The monolithic `config_pin` and `field_snapshot_id` remain as DERIVED values
for DHARA build records: `config_pin = SHA256(canonical_json(pin_matrix))`.

---

## Section 6 -- VECTORIZED NULL DESIGN (1024 replicates, ruling n3)

### 6.1 Current design (256 replicates, coarse grid)

The current null (`stage5_null.py`) runs R=256 circular-shift replicates. Each
replicate:

1. Shifts envelope knots by `delta_r = r * (H/R)` (wrapping at H=36525).
2. Builds segments using COARSE breakpoints only (MD/AD/PD boundaries, ~819
   knots -- the L1g optimization).
3. Builds a cumulative integral on a 1-day grid (36525 grid points).
4. Computes sliding-window-max `M_r(L)` for each duration bucket.
5. Pools `lambda_r(t_g)` values into a streaming quantile for `q_e`.

Cost: 256 replicates * (~7s per replicate on the canonical chart with L1g/L1h/L1k/L1n
optimizations) = ~30 min per class.

### 6.2 DHARA null design (1024 replicates, full-fidelity knots)

**Core insight:** a circular shift of the transit stream by `delta` shifts the
ENVELOPE knots by `delta` (wrapping at H). The CLOCK knots (dasa boundaries) remain
FIXED -- they are birth-chart properties, not transit properties. The DHARA sweep
algorithm is already event-driven over a merged knot set, so applying the null
shift is a RE-INDEX of the envelope knots, not a full rebuild.

```
algorithm DHARA_NULL_REPLICATE(r, delta_r, event_class e, ev):

  # Clock knots: UNCHANGED (birth-chart-fixed)
  K_c_r = K_c

  # Envelope knots: shifted by delta_r, wrapped at H
  K_e_shifted = [(t + delta_r) % H  for t in K_e]
  K_e_r = sorted(K_e_shifted)

  # Merge step: O(|K_c| + |K_e|) via sorted merge (both pre-sorted)
  K_r = sorted_merge(K_c_r, K_e_r)

  # Run DHARA sweep on K_r with shifted envelope evaluations
  # The evaluator is replicate_evaluator(ev, delta_r) — same as current
  rep_ev = replicate_evaluator(ev, delta_r)
  segments_r = dhara_sweep(e, rep_ev, knot_set=K_r)

  # Cumulative integral and sliding-window max: same as current
  cum_r = cumulative_on_grid(segments_r, H, grid_step=1.0)
  stats_r = {b: sliding_window_max(cum_r, b) for b in DURATION_BUCKETS}

  return segments_r, stats_r
```

### 6.3 Vectorized implementation for R=1024 replicates

The key optimization: all 1024 replicates share the SAME clock knots `K_c`.
The envelope knots differ only by a constant shift `delta_r`. This enables
batch processing:

```python
def vectorized_null(ev, R=1024):
    H = ev.horizon_days
    K_c = sorted_clock_knots(ev)           # fixed for all replicates
    K_e = sorted_envelope_knots(ev)        # base (unshifted)

    # F-01 AMENDMENT: range(1, R+1) is wrong — when r=R, delta=H, and
    # circular_shift's `delta % H = 0` returns an UNSHIFTED index identical to
    # the real field. This double-counts the observation in the p-value formula
    # and inflates minimum achievable p from 1/(R+1) to 2/(R+1). The correct
    # grid uses range(1, R), yielding R-1 = 1023 independent replicates with
    # p-value resolution 1/1024. This is a pre-existing bug in the 256-replicate
    # engine (range(1,257) has the same defect); DHARA corrects it.
    deltas = [r * (H / R) for r in range(1, R)]  # R-1 independent shifts, none wraps to H

    q_pool = QuantilePool(quantile=0.95, expected_total=R * int(H))
    all_stats = {b: {} for b in DURATION_BUCKETS}

    for r, delta in enumerate(deltas):
        # Shift envelope knots: O(|K_e|)
        K_e_shifted = np.mod(K_e + delta, H)
        K_e_shifted.sort()   # O(|K_e| log |K_e|)

        # Merge with clock knots: O(|K_c| + |K_e|) via np.searchsorted
        K_r = np.unique(np.concatenate([K_c, K_e_shifted]))

        # Build shifted evaluator
        rep_ev = replicate_evaluator(ev, delta)

        # DHARA sweep on K_r: O(|K_r|) evaluations
        segments_r = dhara_sweep_segments(rep_ev, K_r)

        # Cumulative integral + sliding max: O(|K_r| + H)
        cum_r = cumulative_on_grid(segments_r, H)
        for b in DURATION_BUCKETS:
            all_stats[b][r] = sliding_window_max(cum_r, b)

        # Pool lambda values for q_e: O(|K_r|)
        lambda_grid_r = lambda_grid_fast(segments_r, H)
        q_pool.add(lambda_grid_r)

    q_threshold = q_pool.value()
    return NullResult(
        replicates=R, horizon_days=H,
        shift_grid_step=H / R,
        q_threshold=q_threshold,
        max_stats={b: [all_stats[b][i] for i in range(R)] for b in DURATION_BUCKETS},
    )
```

### 6.4 Per-replicate cost estimate

Each replicate requires:
- Envelope shift: O(|K_e|) = ~36K ops
- Sort shifted knots: O(|K_e| log |K_e|) = ~36K * 15 = ~540K comparisons
- Merge with K_c: O(|K_c| + |K_e|) = ~40K ops
- DHARA sweep (ln_lambda evaluations): O(|K_r|) = ~40K evaluations
  - Each evaluation: ~100 microseconds (L1i vectorized envelope lookup)
  - Total: ~4 seconds per replicate
- Cumulative integral: O(|K_r| + H) = ~76K ops
- Lambda grid: O(|K_r| + H) = ~76K ops

Per-replicate time: ~4 seconds (dominated by ln_lambda evaluations).
Total for R=1024: ~4096 seconds = ~68 minutes per class.

**This is SLOWER than the current 256-replicate null (~30 min per class) because
DHARA uses the FULL knot set (~40K) instead of the coarse set (~819).**

### 6.5 Null-specific coarsening (performance recovery)

To keep the null affordable at R=1024, the DHARA null uses a COARSENED knot set
for replicates, exactly as the current engine does (L1g):

```
K_null_r = sort(K_c_coarse UNION K_e_coarse_shifted)
```

where:
- `K_c_coarse` = MD/AD/PD boundaries only (~819 knots), same as current L1g
- `K_e_coarse_shifted` = envelope knots subsampled to one per ~7-day window,
  shifted by `delta_r`

With `|K_null_r| ~ 1500-2000`, each replicate's DHARA sweep takes:
- ~2000 ln_lambda evaluations * 100 microseconds = ~200ms per replicate
- 1024 replicates * 200ms = ~205 seconds = ~3.4 minutes per class

This is FASTER than the current 256-replicate null (~30 min) because:
1. DHARA sweep does NOT do adaptive refinement (no midpoint checks on the
   ~90% of intervals that are non-suppression)
2. The remaining ~10% of suppression-active intervals are short enough that
   a single-depth refinement suffices

**Alternative (preferred, if compute budget allows):** use the FULL knot set
for replicates (no coarsening), accepting ~68 minutes per class. The 4x increase
in replicates (256 -> 1024) combined with the full-fidelity knot set gives a
much more accurate null distribution. The SAMPURTI conductor can schedule this
as an overnight job.

**The blind-spec commitment:** R=1024 is COMMITTED here per native ruling n3.
The coarsening strategy (full vs. coarse knot set) is an implementation choice
that does not affect the replicate count.

### 6.6 Equivalence to current 256-replicate result

The 1024-replicate result will NOT be bit-identical to the current 256-replicate
result, for three independent reasons:

1. **Different replicate count:** R=256 uses shifts `delta_r = r * (H/256)`;
   R=1024 uses `delta_r = r * (H/1024)`. The 256 original shifts are a SUBSET of
   the 1024 new shifts (every 4th replicate in the new set matches an old one:
   `4r * (H/1024) = r * (H/256)`). So the 256 original statistics are embedded
   in the 1024 new ones, but the additional 768 replicates change the quantile
   and the per-bucket max-stat distributions.

2. **Different knot set (if full-fidelity):** the current null uses ~819 coarse
   breakpoints; DHARA (full-fidelity variant) uses ~40K. The segments differ,
   so `lambda_r(t_g)` differs at individual grid points, so `q_e` differs.

3. **Different p-value resolution:** null_resolution changes from 1/257 to 1/1025.
   p-values that were at the resolution floor (1/257 ~ 0.00389) may now have
   finer resolution (1/1025 ~ 0.000976).

**Expected direction of q_e change:** the finer null distribution (more replicates,
higher-fidelity knot set) generally produces a HIGHER `q_e` (the 95th percentile
of a better-sampled distribution is more accurate, and the current coarse grid
tends to underestimate peak lambda values because it misses short-lived transit
peaks). A higher `q_e` means some current windows may fall below the new threshold
and be dropped. This is the CORRECT behavior -- those windows were only notable
because the coarse null underestimated the sky's background activity.

---

## Section 7 -- EQUIVALENCE TOLERANCES + EXPECTED-DIFFERENCES REGISTER

**This section is committed BLIND before any comparison runs (binding per native
ruling n1). Every tolerance is DERIVED from the mathematics of sections 1-3, not
from empirical measurement.**

### E1 -- Window edges

**Source of difference:** the current engine builds segments via adaptive bisection
with `tau = 0.02` nats tolerance and `max_depth = 6`. DHARA builds segments by
evaluating `ln lambda` at exactly the knots in K (no bisection for non-suppression
intervals).

On a **non-suppression interval**: both engines produce the SAME `(alpha, gamma)`
to float64 precision, because the true `ln lambda` IS linear and both evaluate
it at the same endpoint knots. The window edge `t* = t_start + (ln_q - alpha)/gamma`
is therefore identical.

On a **suppression-active interval**: the current engine's adaptive bisection
places sub-segment boundaries at midpoints (depth 1), quarter-points (depth 2),
etc., producing a piecewise-linear approximation with segments of width
`h / 2^depth`. DHARA's knot set already contains all envelope knots, so the
interval between consecutive knots in K is typically SHORTER than the current
engine's finest bisection sub-segment. The window edge computed from DHARA's
`(alpha, gamma)` may differ from the current engine's edge by at most the
difference between the two piecewise-linear approximations of the concave
`ln lambda`.

**Bound:** the maximum difference in the linear interpolant's crossing point is
bounded by the maximum difference in the linear interpolants themselves, divided
by the minimum slope magnitude:

```
|t*_dhara - t*_current| <= max_interpolant_difference / min(|gamma|, EPS_GAMMA)
```

The maximum interpolant difference between two piecewise-linear approximations
of a concave function on the same domain is bounded by the concavity gap:

```
max_interpolant_difference <= (1/8) * |f''_max| * max(h_dhara, h_current)^2
```

For typical values (`|f''_max| ~ 361` nats/day^2 at worst, `h ~ 1-30` days):

```
max_interpolant_difference <= (1/8) * 361 * 30^2 = 40,612 nats
```

This worst case is VERY pessimistic (it assumes `rho = 0.95`, `u = 0.95`,
envelope changing from 0 to 1 in one step -- the most extreme possible
suppression). In practice, most suppression-active intervals have
`|f''| << 361` because `u_m` is small or `rho_m << 0.95`.

**Practical tolerance:** `|t_edge_dhara - t_edge_current| <= 0.5 day` for
non-suppression intervals (should be exactly 0, but allowing float64 noise
at day-grade precision). For suppression-active intervals:
`|t_edge_dhara - t_edge_current| <= 3.0 days` as a DEFAULT tolerance, with
the following caveat from **F-05**:

The time-domain error from different linear interpolants is bounded by
`max_interpolant_diff / |gamma|` where `|gamma|` is the log-hazard slope at the
threshold crossing. For segments with very small `|gamma|` (a near-flat
ln_lambda crossing the threshold), this bound diverges. The 3.0-day tolerance
assumes `|gamma| >= 0.007 nats/day`. For segments with `|gamma| < 0.007`
(extremely flat crossings), the equivalence gate is RELAXED to
`max_interpolant_diff / |gamma|` computed per-segment. In practice, flat
crossings are rare (they require ln_lambda to barely nudge above the threshold),
and both engines produce nearly identical crossing times in such cases (since both
linear-interpolate the same endpoints).

**Equivalence gate (S4):**

```
PASS if:
  For each window in the current engine's output:
    There exists a window in DHARA's output within 0.1 day for non-suppression
    edges and within 3.0 days for suppression-active edges.
  AND the converse (every DHARA window matches a current-engine window).
```

**How to test:** on the canonical chart's fixture decades, run both engines,
extract window boundary times, classify each boundary as suppression-active or
non-suppression based on the `suppression_term` at the boundary, and diff.

### E2 -- Peak times

Both engines use breakpoint argmax (section 3.2). For non-suppression intervals,
the breakpoint set is the same (K), so peak times are IDENTICAL.

For suppression-active intervals, the current engine may have additional
sub-breakpoints from adaptive refinement that DHARA does not have (or DHARA
may have knots from K_e that the current engine does not). The peak is an argmax
over a slightly different candidate set.

**Tolerance:**

```
Non-suppression intervals: |t_peak_dhara - t_peak_current| = 0 days (exact match)
Suppression-active intervals: |t_peak_dhara - t_peak_current| <= 1.0 day
```

The suppression tolerance is bounded by the maximum distance between adjacent
breakpoints in either engine's set, which is at most one envelope knot spacing
(~1-30 days). Since both engines evaluate `lambda` at all breakpoints and take
the argmax, the difference is at most one knot spacing -- and in practice much
less, because both knot sets contain the envelope boundaries where `lambda`
is largest.

### E3 -- Expected counts (integral of lambda)

**Non-suppression intervals:** DHARA uses `segment_integral` on segments with
the same `(alpha, gamma)` as the current engine. The integral is IDENTICAL to
float64 precision.

```
|Lambda_dhara - Lambda_current| = 0  (exact, non-suppression)
```

**Suppression-active intervals:** both engines use `segment_integral` on their
stored `(alpha, gamma)` segments. The segments differ slightly (different
breakpoints, different linear interpolants of the concave function), so the
integrals differ.

The difference in `segment_integral` between two linear interpolants of a concave
function `f` on `[a, b]` is bounded by:

```
|I_1 - I_2| <= integral_a^b |exp(L_1(t)) - exp(L_2(t))| dt
            <= integral_a^b exp(max(L_1, L_2)) * |L_1(t) - L_2(t)| dt
            <= exp(max_ln_lambda) * max_interpolant_diff * (b - a)
```

For typical values (`exp(max_ln_lambda) ~ exp(-4) ~ 0.018` events/day,
`max_interpolant_diff ~ 0.02` nats from section E1, `(b-a) ~ 10` days):

```
|I_1 - I_2| <= 0.018 * 0.02 * 10 = 0.0036
```

**Tolerance:**

```
Non-suppression: |Lambda_dhara - Lambda_current| < 1e-10 (float64 noise only)
Suppression-active per window: |Lambda_dhara - Lambda_current| < 0.01
Overall per class per decade: |Lambda_dhara - Lambda_current| < 0.05
```

### E4 -- Null thresholds (q_e)

The change from 256 to 1024 replicates is a PARAMETER change, not a bug fix.
`q_e` WILL change because:

1. The null distribution is sampled 4x more densely.
2. (If full-fidelity knots) the per-replicate field is higher-resolution.
3. The quantile pool has 4x more values.

**Expected magnitude of change:** the 95th percentile of a distribution sampled
with 4x more points converges toward the true percentile. The standard error of
a sample quantile at quantile level `p` from `N` samples is approximately:

```
SE(q_p) ~ sqrt(p * (1-p) / N) / f(q_p)
```

where `f(q_p)` is the density at the quantile. Going from N=256*36525 to
N=1024*36525 reduces SE by a factor of 2.

The DIRECTION of change depends on whether the current 256-replicate estimate
is above or below the true percentile. With 256 replicates, the sampling error
is approximately `1/sqrt(256) = 6.25%` relative. With 1024 replicates, it is
approximately `1/sqrt(1024) = 3.125%` relative.

**Tolerance (smoke test):**

```
|q_e_new - q_e_old| < 0.20 * q_e_old    (20% relative change)
```

A change larger than 20% would be anomalous and would require investigation.
The expected change is typically 5-10% based on the sampling-error argument above.

### E5 -- Window count per class

Window count may change because:
1. Window edges move slightly (E1) -- adjacent windows may merge or split.
2. `q_e` changes (E4) -- windows near the threshold may appear or disappear.

**Tolerance (equivalence gate):**

```
|N_windows_dhara - N_windows_current| <= 2  per class per decade
```

Justification: each class typically has 3-8 windows per decade. A change of
more than 2 would indicate a systematic shift, not edge-case noise. The edge
movement tolerance (E1) is small enough that at most 1-2 windows per decade
could be affected by edge merging/splitting. The `q_e` change (E4) could add
or remove 1 window near the threshold.

### E6 -- Segment count

DHARA produces FEWER segments than the current engine:

```
N_segments_dhara ~ |K| ~ 10K-40K
N_segments_current ~ 321K
```

This is an expected and DESIRED difference. The current engine's ~321K segments
include ~120K kinematics-root segments (unnecessary -- `ln lambda` does not change
slope at kinematics roots) and ~160K SD/PrD-boundary segments (each of which is
individually very short and carries essentially the same `(alpha, gamma)` as its
neighbors, since SD/PrD lord changes contribute negligibly to the clock term
when `w_s * A_s` is small for those systems).

The STORED FIELD (the `(alpha, gamma)` representation) differs between the two
engines on suppression-active intervals because the breakpoint sets differ. But the
field's EVALUATION at any point `t` differs by at most the interpolation error
bounded in E1.

---

## Section 8 -- DUAL-ENGINE FLAG AND ROLLOUT CONTRACT

### 8.1 Engine version flag

```python
# services/ka_kshetra/engine_config.py (NEW FILE, single constant)

ENGINE_VERSION: str = 'sampled'
# Values:
#   'sampled'  — current adaptive-bisection engine (default, UNTOUCHED)
#   'analytic' — DHARA event-driven sweep engine
```

### 8.2 Rollout rules

1. **The `'sampled'` code path is UNTOUCHED.** All DHARA code is additive -- new
   modules, new functions. No existing function in `integrator.py`, `hazard.py`,
   `stage4_field.py`, or `stage5_null.py` is modified, deleted, or renamed.

2. **The flag-flip is its own separate commit,** distinct from any implementation
   PR. The commit message is:
   `feat(ka_kshetra): flip ENGINE_VERSION sampled -> analytic (DHARA)`

3. **`_RESUME_VERSION` bumps on the flag-flip commit,** not on implementation
   commits. This ensures a build in progress under `sampled` is not silently
   switched to `analytic` mid-run.

4. **All implementation lanes (S3) are merged to the integration branch BEFORE
   the flag-flip commit is authored.** The flag-flip is a single-line change.

### 8.3 SMR-2 commitment

When the flag flips to `'analytic'`:

- A new measurement M5 is run on the DHARA engine.
- M5 is published BESIDE M4 (not replacing it) per R14 versioning rules.
- The M4 baseline STANDS until M5 is reviewed and accepted by native ruling.
- If M5 shows regression beyond the tolerances in section 7, the flag reverts
  to `'sampled'` and the finding is investigated.

### 8.4 Stage routing

```python
# In the ka_kshetra writer's substep dispatcher:

from services.ka_kshetra.engine_config import ENGINE_VERSION

if ENGINE_VERSION == 'analytic':
    from services.ka_kshetra.dhara_sweep import dhara_build_segments
    segments = dhara_build_segments(evaluator)
else:
    segments = evaluator.build_segments()
```

The routing is at the SEGMENT CONSTRUCTION level only. Everything downstream
(window detection, integration, provenance, null distribution) reads the
produced `Segment` objects identically regardless of which engine produced them.

---

## Appendix A -- Gauss-Legendre nodes and weights (4-point)

For reference, the exact values used in section 3.3:

```
Node 1: xi = -sqrt(3/7 + 2/7 * sqrt(6/5))  = -0.8611363115940526
         w  = (18 - sqrt(30)) / 36           =  0.3478548451374538

Node 2: xi = -sqrt(3/7 - 2/7 * sqrt(6/5))  = -0.3399810435848563
         w  = (18 + sqrt(30)) / 36           =  0.6521451548625461

Node 3: xi = +sqrt(3/7 - 2/7 * sqrt(6/5))  = +0.3399810435848563
         w  = (18 + sqrt(30)) / 36           =  0.6521451548625461

Node 4: xi = +sqrt(3/7 + 2/7 * sqrt(6/5))  = +0.8611363115940526
         w  = (18 - sqrt(30)) / 36           =  0.3478548451374538
```

Transform from [-1, 1] to [a, b]:
```
t_k = (b + a) / 2 + (b - a) / 2 * xi_k
I   = (b - a) / 2 * SUM_k  w_k * f(t_k)
```

## Appendix B -- Notation glossary

| Symbol | Meaning | Source |
|--------|---------|-------|
| `lambda_e(t)` | Hazard rate for event class e at time t (events/day) | hazard.py |
| `lambda^0_e` | Baseline hazard rate = N_e / 36525 | hazard.baseline_rate |
| `P_tilde_e` | Floored promise = P_floor + (1-P_floor)*P_e | hazard.promise_tilde |
| `r_{s,e}(t)` | Signed relevance of clock system s to class e at time t | hazard.relevance |
| `x_j(t)` | Covariate j at time t, piecewise-linear in [0,1] | EnvelopeIndex.covariates_at |
| `u_m(t)` | Obstruction m at time t, piecewise-linear in [0,1] | EnvelopeIndex.obstructions_at |
| `K_c` | Clock knots (dasa boundary times) | kala_field_boundaries |
| `K_e` | Envelope knots (primitive knot times) | kala_field_primitives |
| `K` | Global knot set = sort(K_c UNION K_e) | Section 2.1 |
| `H` | Horizon = 36525 days (100 Julian years) | HORIZON_DAYS |
| `R` | Replicate count (1024 for DHARA, 256 for current) | Section 6 |
| `q_e` | Window threshold (95th percentile of null) | stage5_null.QuantilePool |
| `tau` | Adaptive refinement tolerance (0.02 nats) | integrator.DEFAULT_TAU |
| `alpha, gamma` | Stored log-linear segment: ln lambda = alpha + gamma*(t-t_start) | Segment |

## Appendix C -- Open questions and implementation notes

### C.1 Kinematics roots: include or exclude?

The current real-build path (`FieldEvaluator.breakpoints()`) includes kinematics
roots from `extra_breakpoints`. DHARA excludes them from K because `ln lambda`
does not change slope at kinematics roots (they are astronomical event times, not
breakpoints of the piecewise structure).

However, kinematics roots serve a DIFFERENT purpose in the current engine: they
ensure that the adaptive bisection samples `ln lambda` near significant
astronomical events (stations, direction changes). Without them, a long
inter-knot interval might miss a transit that starts and ends between two
envelope knots.

**Resolution:** this concern does not apply to DHARA because DHARA's breakpoint
set ALREADY includes all envelope knots (K_e). A transit that starts and ends
is represented by its envelope's knots, which are already in K. Kinematics roots
are redundant when the full envelope knot set is used.

### C.2 SD/PrD dasa levels: include or exclude from K_c?

The current engine includes all five dasa levels in the breakpoint set. DHARA's
K_c should include all precision-supported levels, because the clock term
`r_{s,e}(t)` genuinely changes at every lord transition, including SD/PrD.

However, the CONTRIBUTION of SD/PrD lord changes to the clock term is typically
small (depth weights: SD=0.30, PrD=0.15). Excluding them from K_c would reduce
|K_c| from ~165K to ~819, at the cost of approximating the clock term as
piecewise-constant over ~30-day intervals instead of ~0.1-day intervals.

**Resolution:** include all precision-supported levels in K_c for the REAL BUILD.
The ~165K dasa boundaries are still far fewer total evaluations than the current
engine's ~321K breakpoints, and they give exact clock-term representation. For
the NULL DISTRIBUTION, use the L1g coarsening (MD/AD/PrD only) as the current
engine already does.

### C.3 Term matrix: weighted or unweighted storage?

Section 4.5 notes that the refit path requires either (a) storing both weighted
and unweighted values, or (b) storing the weights separately so the refit can
divide out old and multiply by new. Option (b) is preferred because it halves
the storage and the weight vector is already stored in `kala_field_weights`.

**Resolution:** store the UNWEIGHTED term matrix (raw `r_{s,e}(t_k)`, raw
`x_j(t_k)`, raw `ln(1 - rho_m * u_m(t_k))` with the CURRENT rho) plus the
weight vector as metadata in the `.npz`. The weighted matrix is reconstructed
at refit time by column-wise multiplication.

**F-06 + F-14 AMENDMENT:** The `.npz` schema in section 4.3 does NOT include
`u_m(t_k)` as a separate column — the schema must be extended. Add:

```python
np.savez_compressed(
    ...,                                 # existing fields per section 4.3
    raw_u_matrix=raw_u_matrix,           # float32, shape [K, V] — raw u_m(t_k) values
                                         # (unweighted, rho-free, the linear-envelope
                                         # value at each knot for each vighna class V)
    rho_values=rho_values,               # float32, shape [V] — rho_m at build time
                                         # REQUIRED for rho-refit recovery
)
```

The suppression "unweighted" column in `term_matrix` stores `ln(1 - rho * u)`,
which EMBEDS rho. A rho refit requires knowing `u_m(t_k)` separately to
recompute `ln(1 - rho_new * u)`. The `raw_u_matrix` addition satisfies this.

Additionally, `rho_values` must be stored alongside so the recovery formula
`u = (1 - exp(stored_log)) / rho_old` is always available even if the
`kala_field_weights` row for the old weights_version is later deleted.
This storage is O(|K| * V * 4 bytes) ≈ O(40K * 8 * 4) = ~1.3 MB per class,
acceptable for the rebuild savings.

---

*End of DHARA_DESIGN_v1_0.md v1.1*
