---
artifact: PURNA_GROUNDING_REPORT_v1_0.md
version: 1.0
status: CLOSED — read-only grounding pass complete
date: 2026-08-14
authority: Claude Code, headless read-only grounding session (no DB writes, no file edits, no branch writes)
scope: PURNA_KSHETRA_PLAN_v1_0.md, all twelve G-items (G1-G12)
method: git show origin/main:<path> for all code citations (working tree was dirty and
  was NOT used as a source, except where explicitly noted for DHARA_DESIGN_v1_0.md,
  which does not exist on origin/main); read-only SELECTs against the production-shaped
  DB via cloud-sql-proxy on 127.0.0.1:5433, canonical chart_id
  482012f1-710e-4a25-994a-93821f5871aa.
---

# PŪRṆA-KṢETRA GROUNDING REPORT v1.0

Read-only grounding pass answering G1–G12 of `PURNA_KSHETRA_PLAN_v1_0.md`. Every
citation below is `file:line` with the decisive lines quoted verbatim from
`origin/main` (or the DB, for G8/G9/G11). Findings that contradict the plan's
stated assumptions are not softened — see also the closing "ASSUMPTIONS THAT
FAILED" section.

---

## G1 — CLOCK TERM DECOMPOSABILITY

**VERDICT:** Confirmed decomposable. The expensive part of the clock computation
(the lord stack per system at time t) is chart-level and is *already* loaded
chart-level — but the current architecture wastes that fact: `writer.py`'s
`_class_context()` reloads and rebuilds the ladder/clocks fresh for every event
class instead of sharing one instance across all 27.

**EVIDENCE:**

Clock loop, `platform/python-sidecar/services/ka_kshetra/hazard.py:492-509`:
```python
for clock in sorted(predictive_systems(clocks), key=lambda c: c.system_id):
    w_s = float(weights.get(f'w_s:{clock.system_id}', 0.0))
    stack = list(lord_stacks.get(clock.system_id, ()))
    r = relevance(stack, promise.routes, depth_weights)
    contribution = clock_log_factor(float(clock.quality or 0.0), r, w_s)
```

Per-input classification:
- `clocks` (`ClockApplicability` rows: `quality`, `applicability_state`,
  `is_predictive`) — `load_clocks(conn, chart_id)`,
  `stage4_field.py:900,907`: `"...FROM kala_field_clocks WHERE chart_id = %s..."`
  — **chart-level, no event_class**.
- `lord_stacks` (the expensive per-knot value) — `FieldEvaluator.lord_stacks_at(t)`
  (`stage4_field.py:579`) built from `self.ladder`, loaded by
  `load_ladder(conn, chart_id)` (`stage4_field.py:927,939`):
  `"...FROM kala_field_boundaries WHERE chart_id = %s AND precision_state <> 'precision_unsupported'..."`
  — **chart-level, no event_class**. This is the ~165K-period bisect walk.
- `weights` (`w_s`, `depth_weights`) — `resolve_weights_pin(conn)`
  (`stage4_field.py:723,738-751`) — **global, no chart_id, no event_class param
  at all**.
- `promise.routes` (fed into `relevance()`) — `load_promise_prior(conn,
  chart_id, event_class)` (`stage4_field.py:851,877`):
  `"...FROM kala_field_routes WHERE chart_id = %s AND event_class = %s..."` —
  **this is the one genuinely class-dependent input**.

`relevance()` (`hazard.py:208-243`) is exactly `r_{s,e}(t) = tanh(Σ_ℓ d_ℓ ·
sign_ℓ · g_ℓ)` — `d_ℓ` is a global depth weight, and `g_ℓ, sign_ℓ =
_best_route_for_lord(lord, routes)` (`hazard.py:247-271`) is a cheap
O(routes-for-this-lord) lookup against the small per-class `routes` list; it
never touches the ladder/bisect machinery.

The waste is concrete, not theoretical: `writer.py:1475-1503`
(`_class_context`) builds one fresh `FieldEvaluator` **per event_class**, each
with its own `S4.load_clocks(conn, self._chart_id)` and
`S4.load_ladder(conn, self._chart_id)` call (`writer.py:1486-1487`) — the same
chart-level query and ladder rebuilt from scratch once per class.

**IMPLICATION:** Clock raw value = `CHART-LEVEL matrix (lord stack per
system/level at t, quality per system)` × `PER-CLASS cheap lookup (route
gain/sign for the lords currently on the stack)`. Minimal chart-level columns
to precompute once: lord-at-each-level-at-each-ladder-breakpoint (per system),
plus the chart-level `ClockApplicability` rows. Both already have zero
event_class dependence; the redesign need only build them once and hand the
same objects to all 27 `FieldEvaluator`s.

---

## G2 — COVARIATES

**VERDICT:** Confirmed — all twelve covariate raw sources are chart-level,
including x3 (`dual_reference_agreement`), which is a pure derived function of
two other chart-level covariates computed inline for code-organization reasons,
not because of any class dependence.

**EVIDENCE:** `COVARIATE_KEYS` (`hazard.py:83-95`): `contact_moon_ref` (x1),
`contact_lagna_ref` (x2), `dual_reference_agreement` (x3, derived),
`av_kaksha_gate` (x4), `moorti_svarna`/`moorti_rajata`/`moorti_tamra`
(x5-x7), `station_band` (x8), `sandhi_band` (x9), `syzygy_band` (x10),
`eclipse_contact` (x11), `panchanga_affinity` (x12).

x1, x2, x4–x12 source: `FieldEvaluator.terms_at(t)`
(`stage4_field.py:603-614`) passes `covariates=self.envelopes.covariates_at(t)`;
`EnvelopeIndex.covariates_at(t)` (`stage4_field.py:349-378`) reads only
`self.supportive`, built in `__init__` from `load_primitives(conn, chart_id)`
(`stage4_field.py:964,970`): `"...FROM kala_field_primitives WHERE chart_id =
%s..."` — **chart-level, no event_class filter anywhere in the query**.

x3 derivation, verbatim (`hazard.py:291-299`):
```python
def derive_dual_reference_agreement(x: Mapping[str, float]) -> float:
    """x3 = min(x1, x2) — the gochara DUAL-REFERENCE agreement (§5.1 C-5 row 3)."""
    return min(float(x.get('contact_moon_ref', 0.0)), float(x.get('contact_lagna_ref', 0.0)))
```
invoked in `evaluate()` at `hazard.py:512-513`:
```python
x: dict[str, float] = {k: float(covariates.get(k, 0.0)) for k in COVARIATE_KEYS}
x['dual_reference_agreement'] = derive_dual_reference_agreement(x)
```
Both inputs come from the same chart-level `covariates` dict — no event_class
anywhere in this call chain.

**IMPLICATION:** The entire twelve-entry `x_j(t)` vector is computable once per
chart per instant from a single `EnvelopeIndex` and reused verbatim across all
27 classes. Only the twelve global `β_j` weights (class-independent) scale the
contribution.

---

## G3 — SUPPRESSION

**VERDICT:** Confirmed chart-level for the raw curves — and further, **no
per-class vighna activation set exists anywhere in the code**: every active
obstruction in the chart suppresses every event class uniformly, which directly
contradicts the function's own docstring.

**EVIDENCE:** `EnvelopeIndex.obstructions_at(t)` (`stage4_field.py:394-416`)
reads `self.obstructive`, built from the same chart-scoped
`load_primitives(conn, chart_id)` query as G2 (`stage4_field.py:964-994`) —
**chart-level, no event_class**.

Docstring's claimed per-class scoping, `hazard.py:328-329`:
```
    `u` maps a vighna key (a stage-1 row with polarity='obstructive' that the
    class's routes list in `suppressed_by`) to its piecewise-linear envelope
```
But no code filters `u`/`obstructions` against a class's `Route.suppressed_by`
before it reaches `suppression_log_term`. `Route.suppressed_by` is consumed
only inside `relevance()`/`_best_route_for_lord()` (`hazard.py:266-271`) — a
completely separate mechanism (sign-flipping a clock lord's contribution), not
suppression filtering. `suppression_log_term(u, rhos, default_rho)`
(`hazard.py:321-353`) iterates `for key, u_val in sorted(u.items())` over the
**full, unfiltered chart-wide** obstruction dict for every event class.

**IMPLICATION:** Suppression is even more trivially shareable than clocks or
covariates — with zero per-class filtering, the same `EnvelopeIndex
.obstructions_at(t)` output can be shared verbatim across all 27
`FieldEvaluator`s. **Separate discrepancy worth flagging independent of the
chart/class-level question**: either the `hazard.py:328-329` docstring is
stale/aspirational and today's "every vighna thins every class uniformly"
behavior is intended (in which case the redesign should preserve that
uniformity), or this is an unlabeled bug (a vighna should only suppress classes
reachable through its own route, but currently suppresses all 27
indiscriminately). This needs a native/design-doc ruling
(`KALA_W2_FIELD_DESIGN_v1_0.md §5.1 C-6`) before the rebuild encodes either
behavior as intentional.

**G1-G3 summary against I-1:** the plan's claim ("the expensive per-knot work
is CHART-level, not class-level... only class identity enters as cheap
coefficients") is **verified true**, and understates how separable the system
already is. The actual defect is concretely located at
`writer.py:1475-1503`'s `_class_context()`, which rebuilds chart-level DB
round-trips and structures once per class instead of once per chart.

---

## G4 — FROZEN TERM-MATRIX SPEC

**VERDICT:** `DHARA_DESIGN_v1_0.md` **does not exist on `origin/main` at all**
— it lives only on a `sampurti/integration` feature-branch worktree, never
merged. `dhara_term_matrix.py` (which IS on `origin/main`) implements the §4
schema faithfully, but that schema is a **per-(chart_id, event_class) WEIGHTED
artifact**, not a chart-level shared raw layer — satisfying it and a
share-across-27-classes engine requires an explicit two-layer split that does
not exist yet.

**EVIDENCE — the doc is not merged:**
```
$ git log origin/main --oneline -- 00_ARCHITECTURE/briefs/sampurti/DHARA_DESIGN_v1_0.md
(no output — file has zero history on origin/main)

$ git log --oneline -- 00_ARCHITECTURE/briefs/sampurti/DHARA_DESIGN_v1_0.md
  (run inside .claude/worktrees/sampurti-conductor, branch sampurti/integration)
7ee9eef4a conductor(sampurti): S2 amendments DHARA_DESIGN v1.0→v1.1 — ...
2f0f93088 conductor(sampurti): S1 DHARA DESIGN DOC — analytic spec v1.0 committed blind
```
The file's own frontmatter (read at
`.claude/worktrees/sampurti-conductor/00_ARCHITECTURE/briefs/sampurti/DHARA_DESIGN_v1_0.md:1-14`)
confirms `status: AMENDED_BLIND`, `authority: SAMPURTI-D1 conductor S1 (v1.0);
S2 VERIFIER + Δ1 conductor amendments (v1.1)` — it is a working design artifact
on an integration branch, not a frozen, merged spec.

**§4 schema, quoted verbatim** (DHARA_DESIGN_v1_0.md §4.2, lines 662-680):
```
term_matrix[k, :] = [
  ln_lambda^0_e,                     # column 0: baseline (constant)
  ln_P_tilde_e,                      # column 1: promise (constant)
  w_1 * A_1 * r_{1,e}(t_k),         # column 2: clock system 1
  ...
  beta_1 * x_1(t_k),                # column 2+S: covariate x1
  ...
  ln(1 - rho_1 * u_1(t_k)),         # column 2+S+12: vighna 1
  ...
]
Column count: T = 2 + S + 12 + V
```
Note the explicit subscript `_e` on both `λ^0_e`/`P̃_e` (baseline/promise) and
`r_{s,e}(t)` (clock relevance) — the matrix schema as specified is defined
**per event class e**.

**`dhara_term_matrix.py` (full file read, `origin/main`) confirms this is
implemented exactly as a per-class artifact, weighted:**

`TermMatrixRow.clock_terms` docstring (`dhara_term_matrix.py:87-88`): *"One
entry per applicable predictive clock system. Value =
`w_s*A_s*r_{s,e}(t_k)`."* — already multiplied by the class-specific relevance
`r_{s,e}` and the global weight `w_s`; not a raw, unweighted, class-independent
value.

`TermMatrixRow.suppression_log_terms` docstring (`dhara_term_matrix.py:99-100`):
*"One entry per **active vighna class**. Value = `ln(1 - ρ_m * u_m(t_k))`."* —
the column SET itself (`V`, which vighnas appear as columns at all) varies per
class (contradicting G3's finding that suppression is applied uniformly in the
current `hazard.py`/`stage4_field.py` production path — the §4 spec assumes a
per-class vighna filter that G3 shows doesn't exist in the live evaluator).

`build_term_matrix_row()` (`dhara_term_matrix.py:114-146`) extracts these
already-weighted, already-class-scoped values straight from a `HazardTerms`
snapshot's `edges` — i.e., from a call to `hazard.evaluate()` for one specific
event class e. There is no unweighted/chart-level variant produced anywhere in
this file: `save_term_matrix()` (`dhara_term_matrix.py:337-372`) writes one
`.npz` per `(chart_id, event_class)` pair (per the module docstring's own
naming convention, `dhara_term_matrix.py` header comment: `term_matrix_{chart_id}_{event_class}.npz`).

Even the modifier (covariate) columns, which G2 showed are chart-level raw
data, are stored WEIGHTED (`β_j * x_j(t_k)`, `dhara_term_matrix.py:93-94`) —
if `β_j` were ever made class-specific (it currently isn't, per G2), the
schema as-is could not distinguish "same raw x_j, different β" from "different
raw x_j" without the refit machinery in §4.5.

**IMPLICATION — the two-layer structure required:** the frozen §4 artifact (as
specified AND as implemented) is a *per-class* weighted projection, and cannot
by itself serve as I-1's proposed chart-level shared raw layer. Satisfying
both the §4 contract (unchanged schema, unchanged `.npz` naming/consumption by
stage 9 and EXPLAIN) and P1's "sweep once, combine per class" goal requires:

- **Layer 0 (NEW, chart-level, computed once per chart):** raw, unweighted,
  class-independent columns — lord stack per system/level at each clock knot
  (G1), all 12 raw covariates `x_j(t)` at each knot (G2), and raw `u_m(t)` for
  every vighna instance in the chart regardless of which class will reference
  it (G3, since no class-vighna filter currently exists to narrow this set
  even if one were later added).
- **Layer 1 (the EXISTING §4 `TermMatrixRow`/.npz, unchanged schema):**
  becomes a cheap per-class PROJECTION of Layer 0 — select the class's routes
  to compute `r_{s,e}(t_k)` from the shared lord stack (G1's cheap lookup),
  multiply the shared `x_j(t_k)` by the class's/global `β_j`, and (if/when a
  per-class vighna filter is ever built per G3's flagged discrepancy) select
  the class's active vighna subset from the shared raw `u_m(t)` set.

This satisfies §4's binding artifact contract (the per-class `.npz` file,
consumed by stage 9/EXPLAIN, does not change shape) while making the sweep
itself chart-level — exactly the "engine's working set" P1 describes, but the
plan should be explicit that P1 is adding a NEW unweighted chart-level layer
underneath an UNCHANGED per-class §4 layer, not replacing §4.

---

## G5 — SCALE-INVARIANCE END-TO-END (⚠ redesign-required finding)

**VERDICT:** The window/peak-detection MATH itself is genuinely scale-invariant
(window boundaries, `q_threshold`, `null_p`, robustness flags, the
`stage6_salience` ranking scalar, and even the `adrishta_residual` ratio all
cancel a uniform λ→c·λ rescale) — **but the claim is currently unreachable for
any shape_only-eligible class**, because `hazard.baseline_rate()` /
`stage4_field.require_baseline()` hard-gate and **skip the class entirely**
before any of that scale-invariant math ever runs. Separately, one served,
**non-invariant absolute number** (`expected_count`) leaks through to the
served timeline spec with zero shape_only-aware suppression anywhere in the
read path. **This is the single most plan-critical finding in this report —
reported loudly per the task's own instruction.**

**EVIDENCE — the math that IS scale-invariant:**

1. Window boundaries: `integrator.py:263-305` (`find_windows`) compares `α +
   γ(t−t_i) ≥ ln q`, where `q_threshold` is the 0.95 quantile of same-chart,
   same-scale null replicates (`replicate_evaluator`, `hazard.py:211-231`,
   passes `baseline_source`/`lifetime_count` through unchanged) — a uniform
   rescale multiplies both sides identically. SCALE-INVARIANT.
2. `null_p`, `stage5_null.py:130-141`:
   ```python
   threshold = lambda_obs * (1.0 - _EXCEEDANCE_REL_TOL)
   exceed = sum(1 for m in stats if m >= threshold)
   ```
   Ratio-based against replicate stats computed at the same scale;
   `_EXCEEDANCE_REL_TOL = 1e-12` (`stage5_null.py:93`) is *relative*.
   SCALE-INVARIANT.
3. `adrishta_residual` — the *ratio* is scale-invariant as a formula
   (`stage5_null.py:635-658`, `share = fsum(window_integrals) / expectation`
   where both numerator and denominator carry the same λ⁰ factor) — but it is
   called as `S5.adrishta_residual(totals, hazard.baseline_rate(ev
   .lifetime_count), HORIZON_DAYS)` (`writer.py:592-593,681-682`), and
   `baseline_rate()` **raises** on missing/non-positive `lifetime_count` — see
   next point.

**EVIDENCE — the hard gate that blocks reaching any of the above:**

`stage4_field.py:688-705` (`require_baseline`):
```python
def require_baseline(lifetime_count: Optional[float], event_class: str) -> float:
    ...
    if lifetime_count is None:
        raise ClassSkipped(event_class, 'no_class_prior_row',
                           'no bg_class_priors lifetime-count row for this event class')
    if not math.isfinite(lifetime_count) or lifetime_count <= 0.0:
        raise ClassSkipped(event_class, 'class_prior_not_positive',
                           f'lifetime_count={lifetime_count!r}')
    return float(lifetime_count)
```
`hazard.py:133-150` (`baseline_rate`) independently re-raises `ValueError` on
the same condition, with its own docstring stating: *"a class with no prior
row is `not_computed` and is SKIPPED ENTIRELY (no field rows written for it) —
never given a made-up baseline."* Every stage4/5/5dhara/finalize entry point in
`writer.py` (e.g. `writer.py:455-461,519-525,539-546,629-635`) catches
`S4.ClassSkipped` and returns `WriterResult(rows_inserted=0, ...)` — **today,
live, zero `kala_field` segments → zero windows → zero salience/insight/
timeline rows for that class.** This is current production behavior, not a
hypothetical failure mode.

**EVIDENCE — the leaking absolute number:**

`writer.py:590-591,679-680`: `windows = integrator.find_windows(...)`;
`totals = [w.expected_count for w in windows]`. `expected_count`
(`integrator.py:302`, the integral of λ over the window) is Λ_e(w) — an
absolute quantity linearly proportional to whatever baseline was used. Written
to `kala_field_windows.expected_count` (`writer.py:761,869-870`) and re-served
**verbatim** by `stage8_spec.py:136`:
```python
"expected_count": float(window["expected_count"]),
```
No tier/`shape_only` flag anywhere in `interval_from_window()`
(`stage8_spec.py:111-153`) suppresses, relabels, or contextualizes this field.
A shape_only window would present a numerically meaningless "expected count"
identically to a real calibrated one.

**IMPLICATION (loud, per task instruction):** Section 0's I-2 claim ("window
detection... is SCALE-INVARIANT... prior-less classes can ship honest
`shape_only` timing output") is TRUE of the underlying math but FALSE as a
description of what the current codebase would do if pointed at a class
without a prior — it would not ship "honest shape_only output," it would ship
**nothing at all** (`ClassSkipped`, zero rows), because the gate that raises
`ClassSkipped` sits upstream of every downstream consumer, inside
`hazard.evaluate()` itself (`hazard.py:472-473` calls `baseline_rate`
unconditionally). Implementing shape_only is NOT "relax a downstream check" —
it requires:
1. A new code path that injects an explicit, versioned, PINNED synthetic
   placeholder `lifetime_count` (the plan proposes none currently) to get past
   `require_baseline`/`baseline_rate`, tagged as synthetic end-to-end.
2. An audit and suppression of every absolute-value consumer downstream —
   `expected_count` (confirmed leaking, `stage8_spec.py:136`) is only the one
   found in this pass; a full P3 implementation must sweep every other served
   absolute field (e.g. anything under `kala_field_windows`/
   `kala_field_null` reached by `kala_now_get`/`kala_ahead_get`/etc. — not
   exhaustively checked here) for the same leak pattern.
3. Per §N.8 (Earned-Signal Principle), the `shape_only` tier flag itself must
   be a real detector distinguishing "this window's absolute fields are
   synthetic-baseline-derived" from "this window's absolute fields are real"
   — not a label applied after the fact.

This is a genuine redesign requirement for P3, exactly as the plan's own I-2
adversarial gate anticipated ("If refuted → fallback: shape tier canceled").
This grounding pass surfaces the refutation the gate was designed to catch:
the invariance is real, but the current architecture makes it unreachable and
leaks one absolute field where it is reachable.

*(Secondary, non-fatal: `stage65_insights.py:50,360-382,603-674`'s
`CONTRAST_MIN_DELTA_LN_LAMBDA = 0.5` cross-snapshot diff is scale-invariant
only within one consistently-scaled snapshot; if a shape_only class's
synthetic placeholder baseline is not pinned identically across snapshots
being diffed, `compute_field_diff`/`detect_contrast` could mix a real field
change with a spurious rescale artifact. Not yet exercised in production —
`contrast_inputs=None` at `writer.py:1136` — but a forward-looking constraint:
the synthetic constant must be versioned and pinned, never freely re-chosen
per build.)*

---

## G6 — STAGE 6/6.5/8 AT 27 CLASSES

**VERDICT:** No hardcoded 6-class (or any fixed small-N) assumption exists in
stage6/6.5/8; event-class discovery is fully dynamic. No cross-class
comparison uses a raw/absolute λ or `expected_count` — cross-class ranking uses
only the renormalized `[0,1]` salience scalar, which (modulo G5's
`expected_count` leak, which is served but not used for ranking) is a point in
the plan's favor. Cost scales roughly linearly with total window count
(≈classes × windows/class); nothing found is O(classes²).

**EVIDENCE — no hardcoded class list:** `writer.py:2049-2075`
(`_discover_event_classes`):
```python
cur.execute(
    'SELECT DISTINCT event_class_id FROM bodha_pratijna '
    'WHERE chart_id = %s '
    'ORDER BY event_class_id', (chart_id,))
```
Docstring: *"LIVE discovery from Lane A's promise register — never a
hardcoded list."* `stage8_spec.py:54`'s `VIEWS = ("now", "ahead", "elect",
"story", "priority", "explain")` is a fixed 6-tuple of **timeline VIEWS**
(unrelated to event-class count) — confirmed not a class-count assumption via
`writer.py:306-307`, which iterates views independently of
`self._event_classes`.

**EVIDENCE — no absolute-λ cross-class comparison:** `writer.py:929-989`
(`_run_stage6`) builds one `SM.SubmodularCandidate` per window with
`salience=vectors[w['window_id']].salience` — the renormalized `[0,1]` scalar
from `compute_salience_vector` (`stage6_salience.py:227-278`), never the raw
`expected_count`/`lambda_peak`. `submodular.py`'s `select_submodular` ranks
only on this scalar plus per-candidate marginal gain — never raw magnitude
across classes.

**EVIDENCE — cost scaling 6→27:**
- Stage 4/5/5dhara: already O(classes), one substep-group per class
  (`writer.py:285-300`) — unaffected by 6/6.5/8, linear.
- Stage 6 (`_run_stage6`, `writer.py:929-1043`): ONE substep for the whole
  chart; `_load_committed_windows` loads all windows in one query
  (`writer.py:1256-1268`), then loops per-window calling
  `_cohort_rate_for_window` (`writer.py:1435-1476` — DB query, memoized per
  `(lagna_sign, md_lord, ref_age)` key) and `_lord_stack_at_peak`
  (`writer.py:1344-1358` — in-memory, no new DB call). Net: O(total_windows)
  in-memory + a bounded, deduped number of DB round-trips.
- Stage 6.5 (`_run_stage65`, `writer.py:1047-1176`): one substep for the whole
  chart, but `_reversal_inputs` (`writer.py:1383-1414`) loops `by_class.items()`
  and re-loads that class's full committed segment list
  (`self._load_segments(conn, event_class)`) per class — O(classes) DB
  queries + O(total_windows·avg_segments_per_window) in-memory filtering.
- Stage 8 (`_run_stage8`, `writer.py:1180-1208+`): runs once per VIEW (6 fixed
  substeps, not per class), each independently reloading the full chart's
  committed windows/boundaries/ontology — total cost `6 × O(total_windows +
  total_boundaries)`, a fixed 6× view multiplier unrelated to class count.

**IMPLICATION:** 6→27 classes (~4.5× if windows/class holds roughly constant)
scales close to linearly overall; nothing here is quadratic. The one scaling
risk flagged: stage6/6.5's per-window/per-class DB round-trips
(`_cohort_rate_for_window`, stage65's per-class `_load_segments`) are **not**
batched the way stage5's writes were fixed to be (`writer.py:791-799`'s L1o
comment cites a prior "hundreds of thousands of round-trips... 30+ min finalize
→ idle_in_transaction timeout" regression, fixed via `_write_windows_batch`
executemany). At 4.5× the classes/windows, this is the most likely place a
similar timeout regression reappears — a scaling risk to watch, not a
confirmed defect today.

---

## G7 — EXACT CURRENT NULL DEFINITION

**VERDICT:** The current null is a deterministic circular-shift permutation
test where the **transit envelope knot-set is shifted** (natal structure +
daśā ladder fixed), run on a **1-day cumulative grid derived from coarse
(MD/AD/PD-only) daśā breakpoints**, producing a **sliding-window-max statistic
per duration bucket**, thresholded at the **95th percentile pooled across all
replicates via an exact `QuantilePool`** — but **two live, non-identical
implementations exist** (`stage5_null.py`, R+1-denominator; `dhara_null.py`,
R-denominator after an OPT-N3 rollback from 1024 to 256 replicates), and
`dhara_null.py`'s own docstring calls `stage5_null.py`'s denominator a bug, not
a spec to preserve. The plan must pin parity against whichever engine is
actually wired — currently DHARA (`_run_stage5dhara`).

**EVIDENCE — what's shifted / fixed**, `stage5_null.py:189-207`
(`replicate_evaluator`):
```python
def replicate_evaluator(ev: FieldEvaluator, delta: float) -> FieldEvaluator:
    """Build replicate r's evaluator: the SAME field with the transit stream
    circularly shifted by δ. Everything else is passed through by reference —
    the promise prior, the clock applicabilities, the daśā ladder, the
    weights, the baseline."""
    return FieldEvaluator(..., envelopes=ev.envelopes.circular_shift(delta), ...)
```
Only `ev.envelopes` shifts; `promise`, `clocks`, `ladder`, `weights`,
`baseline_source`, `extra_breakpoints` pass through unchanged.

**Grid/resolution:** `δ_r = r·(H/R) for r = 1…R` (`shift_grid`,
`stage5_null.py:96-103`). Segment breakpoints are coarse (`_null_breakpoints`,
`stage5_null.py:293-313`): only MD/AD/PD ladder levels; envelope knots and
kinematics roots are intentionally excluded (~819 breakpoints). Cumulative Λ
on a **1-day grid**: `cumulative_on_grid(segments, horizon_days, grid_step:
float = 1.0)` (`stage5_null.py:353`).

**Statistic per bucket**, `sliding_window_max` (`stage5_null.py:405-415`):
```python
def sliding_window_max(cum: Sequence[float], bucket_days: int) -> float:
    """M(L) = max over t on the grid of Λ(t, t+L)."""
    n = len(cum) - 1
    if bucket_days >= n:
        return cum[-1] - cum[0]
    return max(cum[k + bucket_days] - cum[k] for k in range(n - bucket_days + 1))
```

**Quantile/pool:** `Q_QUANTILE: float = 0.95` (`stage5_null.py:80`);
`QuantilePool` (`stage5_null.py:157-186`) is an exact top-k min-heap quantile
("No sketching, no t-digest, no approximation") pooled over R×N values.
`NullAccumulator.finalize()` → `q_threshold=self._pool.value()`
(`stage5_null.py:543`).

**Replicate count / denominator:** `DEFAULT_REPLICATES: int = 256`
(`stage5_null.py:69`); `null_resolution(replicates) -> 1.0/(replicates+1)`
(`stage5_null.py:150-152`) — this engine's p-value denominator is **R+1=257**.

**The DHARA variant is a second, already-diverged engine, not a
straightforward vectorization target.** `dhara_null.py` header:
> "F-01 CORRECTION — shift grid uses `range(1, R)`, not `range(1, R+1)`...
> This corrects a pre-existing bug in stage5_null.py's 256-replicate engine
> (`range(1, 257)` has the same defect)."

`dhara_null.py:56-64` (OPT-N3 comment): replicate count was **1024 by native
ruling n3**, then **rolled back to 256** on 2026-08-14 because
`dhara_compute_null` is sequential-Python (not vectorized), making 1024
replicates take ~34min/class and exceeding
`idle_in_transaction_session_timeout=30min`. `DEFAULT_REPLICATES: int = 256` in
`dhara_null.py:64` — numerically matching `stage5_null.py`'s R, but the
**denominators still differ** (DHARA's `resolution` property,
`dhara_null.py:117-119`, uses `1/R`; `stage5_null.py`'s `null_resolution` uses
`1/(R+1)`). DHARA **imports and reuses** `QuantilePool`,
`cumulative_on_grid`, `sliding_window_max`, `replicate_evaluator`,
`_NULL_COARSE_LEVELS`, `_null_build_segments` from `stage5_null.py`
(`dhara_null.py:56-64`) rather than reimplementing them — DHARA only adds its
own knot-set/replicate-loop logic (`dhara_null.py:190-260`).

**Which engine is wired:** `writer.py:610-696` (`_run_stage5dhara`) calls
`DN.dhara_compute_null(ev, replicates=DN.DEFAULT_REPLICATES)`
(`writer.py:648`), dispatched when `step.key` starts with `stage5dhara`
(`writer.py:400-403`), firing under `ENGINE_VERSION=='analytic'`. The older
`stage5_null.py` path (`_run_stage5_block`/`_run_stage5_finalize`,
`writer.py:517-606`) still exists for `ENGINE_VERSION=='sampled'` — both paths
are live, neither superseded.

**IMPLICATION:** Pinning "the current definition" against `stage5_null.py`
alone (as the plan's phrasing implies) would reproduce a formula DHARA's own
commit history has already declared a bug and replaced. The parity contract
must explicitly choose: `stage5_null.py`'s R+1 grid (legacy/`sampled`, still
live) vs. `dhara_null.py`'s F-01-corrected R grid (currently production,
`_run_stage5dhara`) — and must record that DHARA's replicate count has already
moved twice in one day (1024 native-ruled → 256 OPT-N3 rollback), so "the
current definition" needs a pinned commit/date, not just a file name.

---

## G10 — NULLRESULT ADAPTER SURFACE

**VERDICT:** `contracts.py` — the project's own frozen cross-lane boundary
file — contains **no `NullResult` definition at all**, contradicting the
task's premise. Two separate `NullResult` dataclasses exist instead
(`stage5_null.py`, `dhara_null.py`) with different field sets, and
`_run_stage5dhara` papers over the mismatch with a `getattr(...,'resolution',
None)` fallback.

**EVIDENCE — `_run_stage5dhara`** (`writer.py:610-696`), key consumption
points:
- `null_result = DN.dhara_compute_null(ev, replicates=DN.DEFAULT_REPLICATES)`
  (`writer.py:648`).
- `for bucket, stats in null_result.max_stats.items(): ... INSERT ...
  (self._chart_id, event_class, null_result.replicates, HORIZON_DAYS,
  null_result.q_threshold, bucket, stats, null_result.shift_grid_step, ...)`
  (`writer.py:653-668`) — note `HORIZON_DAYS` is the module constant, **not**
  `null_result.horizon_days`.
- `windows = integrator.find_windows(segments, null_result.q_threshold or
  math.inf)` (`writer.py:679`).
- `_write_windows_batch(conn, ev, event_class, segments, windows, null_result,
  adrishta, ...)` (`writer.py:687-688`) — the whole `NullResult` passed down.
- Inside `_write_windows_batch`/`_write_window` (`writer.py:791,697`):
  `bucket = S5.select_bucket(w.duration_days); p = S5.null_p(null_result
  .max_stats.get(bucket, []), w.expected_count)` (`writer.py:723,830`);
  `birth_time_robust=S5.birth_time_robust(segments, w.t_peak, null_result
  .q_threshold or 0.0, sigma_t)` (`writer.py:726-727,833-834`); row insert uses
  `p, null_result.replicates, getattr(null_result, 'resolution', None) or
  S5.null_resolution(null_result.replicates)` (`writer.py:764-765,873-874`).

**`contracts.py`**: read in full — defines `Route`, `PromisePrior`,
`ClockApplicability`, etc.; `git grep -n "class NullResult" origin/main --
platform/python-sidecar/` finds it **only** in `stage5_null.py:436` and
`dhara_null.py:88`.

`stage5_null.py:436-441`:
```python
@dataclass
class NullResult:
    """Everything stage 5 needs to persist and to threshold windows with."""
    replicates: int
    horizon_days: float
    shift_grid_step: float
    q_threshold: Optional[float]
    max_stats: dict[int, list[float]] = field(default_factory=dict)
```

`dhara_null.py:87-117`:
```python
@dataclass
class NullResult:
    replicates: int
    shift_count: int
    horizon_days: float
    shift_grid_step: float
    q_threshold: Optional[float]
    max_stats: dict = field(default_factory=dict)
    alpha: float = DEFAULT_ALPHA

    @property
    def resolution(self) -> float:
        """p-value resolution = 1/R (F-01: denominator = R, not R+1)."""
        return 1.0 / self.replicates
```

**Field-by-field consumption at the writer.py boundary:**

| Field | stage5_null | dhara_null | Consumed how |
|---|---|---|---|
| `replicates` | yes | yes | → `kala_field_null.replicates`, `kala_field_windows.null_R`, fallback arg to `null_resolution()` |
| `horizon_days` | yes | yes | **Unused** — writer uses its own `HORIZON_DAYS` constant instead |
| `shift_grid_step` | yes | yes | → `kala_field_null.shift_grid_step` |
| `q_threshold` | yes | yes | → `kala_field_null.q_threshold`; `find_windows(...)`; `birth_time_robust(...)` |
| `max_stats` | yes | yes | Iterated for per-bucket row insert; `.get(bucket, [])` feeds `null_p()` |
| `shift_count` | — | yes | **Unused** at the consumption boundary |
| `alpha` | — | yes | **Unused** at the consumption boundary |
| `resolution` (property) | — | yes | Read via `getattr(...,'resolution', None)`, falling back to `S5.null_resolution()` (the R+1 formula) when absent |

**IMPLICATION:** The object the vectorized rewrite must reproduce is not a
stable, singular contract — it is two dataclasses that already disagree
(`shift_count`, `alpha`, `resolution` exist only on one side), reconciled at
the call site by a fallback that assumes `stage5_null`'s R+1 formula whenever
the object handed to it doesn't declare its own resolution. **This is a
currently-latent correctness trap**: a vectorized replacement that returns a
`stage5_null.NullResult`-shaped object (no `.resolution`) would silently fall
through to the wrong (R+1) formula for what's meant to be an R-denominator
result. The plan should make an explicit acceptance criterion: the new
engine's result type must carry its own `.resolution` matching its own
denominator convention, or the `getattr` fallback must be removed entirely —
and `NullResult` should probably move into `contracts.py` as a real frozen
cross-lane type, not stay duplicated.

---

## G8 — ONTOLOGY

**VERDICT:** `brahma_event_ontology` exists with exactly 27 rows as expected.
`birth_anchor` IS confirmed non-predictive, but via a `kill_switch_criteria`
entry (`epoch_tautology`), not a dedicated boolean column — no such generic
"countability"/"predictiveness" column exists for the other 26 rows.

**EVIDENCE:** Schema (19 columns): `event_class_id, name_en, domain,
lel_category, signature_model(jsonb), magnitude_floor, adjacency(jsonb),
base_rate_by_age(jsonb), matching_rules(jsonb), citations(array), version,
created_at, temporal_shape, duration_prior(jsonb), milestone_template(jsonb),
irreversibility_milestone, evidence_requirements(jsonb),
self_report_non_discriminating(bool), kill_switch_criteria(jsonb)`.

`SELECT count(*) FROM brahma_event_ontology;` → **27**. All 27 rows
(event_class_id / domain / lel_category / temporal_shape / magnitude_floor /
self_report_non_discriminating):

| event_class_id | domain | lel_category | temporal_shape | magnitude_floor | self_report_non_discriminating |
|---|---|---|---|---|---|
| achievement_recognition | general | creative | point | moderate | f |
| bereavement | transition | loss | point | significant | f |
| **birth_anchor** | transition | other | point | **life_altering** | f |
| business_launch | career | career | chain | significant | f |
| career_advancement | career | career | point | moderate | f |
| career_change | career | career | chain | moderate | f |
| career_entry | career | career | point | moderate | f |
| career_setback | career | career | interval | significant | f |
| childbirth | progeny | family | point | significant | f |
| chronic_onset | health | health | interval | significant | f |
| education_milestone | education | education | chain | moderate | f |
| exam_outcome | education | education | point | trivial | f |
| financial_deception | wealth | loss | interval | significant | **t** |
| foreign_settlement | travel | travel | chain | significant | f |
| illness_acute | health | health | point | moderate | f |
| major_gain | wealth | finance | interval | moderate | f |
| major_loss | wealth | loss | interval | significant | f |
| marriage | relationship | relationship | point | significant | f |
| parental_event | family | family | interval | moderate | f |
| property_acquisition | residence | finance | point | moderate | f |
| psychological_arc | character | psychological | interval | moderate | **t** |
| relocation | residence | residential | interval | moderate | f |
| romantic_start | relationship | relationship | point | moderate | **t** |
| separation | relationship | relationship | chain | significant | f |
| spiritual_turn | spirituality | spiritual | interval | moderate | **t** |
| surgery | health | health | point | significant | f |
| travel_event | travel | travel | point | trivial | f |

Full `birth_anchor` row:
```
base_rate_by_age = {"band_0_12": 1.0, "band_13_25": 0.0, "band_26_40": 0.0,
                     "band_41_60": 0.0, "band_60_plus": 0.0}
citations = {"n/a — defines the natal epoch, not a classically-timed event"}
kill_switch_criteria = [{"description": "The chart's own birth event is the
  zero-lag definitional anchor of the natal chart, not a predictable
  configuration. ALWAYS excluded from lambda_e scoring, the retrodiction
  harness, and every model contender — scoring it would be tautological, not
  a measurement.", "criterion_id": "epoch_tautology"}]
```

**IMPLICATION:** Confirmed, but more precisely than "flagged non-predictive"
suggests: there is no schema-level predictiveness/countability column any of
the 27 classes could be uniformly queried against. `birth_anchor` alone
carries a `kill_switch_criteria` entry hard-excluding it from λ_e scoring, and
its `base_rate_by_age` is degenerate (1.0 in infancy, 0.0 forever after — not
a rate). Whether any other class needs its own kill-switch is a per-row
judgment call, not something P3's tier-basis table can read off a flag column.

---

## G9 — PRIORS TEMPLATE

**VERDICT:** `bg_class_priors` (the name in the plan) **does not exist**. The
real table is **`brahma_class_priors`** (177 rows), and it is keyed by
`signal_type_class` — a Jyotish signal/rule-type taxonomy (yoga, dasha_period,
varga, tradition weight, etc., 33 distinct values) — **not** by
`event_class_id`. It is a signal-type/tradition prior registry, only
incidentally overlapping the 27 event classes for 6 of them.

**EVIDENCE:** `information_schema.tables` search for `%class_prior%` /
`%event_prior%` finds only `brahma_class_priors`. Columns (13):
`prior_version, signal_type_class, fact_kind, source_subsystem,
signal_tradition, class_prior(numeric), varga_weights(jsonb), contested(bool),
citation, ratified_by, created_at, prior_basis, source_ref`.

`SELECT count(*) FROM brahma_class_priors;` → **177**, all `contested = f`.
Breakdown by `ratified_by`: 171 rows `W1_SEED_PACKAGE_v1_0` (prior_version
1.0, wildcard `signal_type_class`/`fact_kind` rows, mostly empty
`prior_basis`); 6 rows `SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0
§ADJUDICATION-2` (prior_version `ne_v01`) — the only fully-cited cohort:

| signal_type_class | fact_kind | class_prior | prior_basis | citation (truncated) |
|---|---|---|---|---|
| childbirth | lifetime_count_per_100y | 3.09 | demographic_structural | NFHS-5 India Report Vol.1, Table 4.5 |
| foreign_settlement | lifetime_count_per_100y | 0.0129 | demographic_structural | UN DESA Int'l Migrant Stock 2020, Table 1 |
| marriage | lifetime_count_per_100y | 0.984 | demographic_structural | Census of India 2011, Table C-2 |
| relocation | lifetime_count_per_100y | 0.376 | demographic_structural | Census of India 2011, Table D-2 |
| separation | lifetime_count_per_100y | 0.00806 | demographic_structural | Census of India 2011, Table C-2 |
| surgery | lifetime_count_per_100y | 0.356 | demographic_structural | Zadey S. et al., Int J Surg 2024, DOI 10.1097/JS9.0000000000001024 |

**IMPLICATION:** `bg_class_priors` naming drift is itself a finding — a plan
reader searching for that exact table name will not find it. More
importantly, the 6 `ne_v01` rows are the only ones structurally matching what
P4 needs to ratify (`class_prior`/`prior_basis`/`citation`/`source_ref` all
populated, `demographic_structural`), and they cover only 6 of the 27 event
classes — none of `bereavement`, `career_*`, `chronic_onset`, etc. Any new P4
ratification should match the 6 `ne_v01` rows' shape, not the 171 sparse
`W1_SEED` rows.

---

## G11 — KNOT-SET COMPOSITION

**VERDICT:** The plan's 343,973-segments-per-class figure is confirmed live in
production for the canonical chart — but it is per-CLASS for only the **6
currently-wired classes** (the same 6 with `ne_v01` priors from G9), not per
knot-set as such, and it comes from the OUTPUT table `kala_field`, not the
INPUT tables (`kala_field_boundaries`/`kala_field_primitives`) the plan's own
search hints point at. Memory footprint for a chart-level raw matrix
comfortably fits an 8Gi budget — not tightly, by roughly 30-40×.

**EVIDENCE:** Per-source counts for canonical chart_id
`482012f1-710e-4a25-994a-93821f5871aa`:
- `kala_field_boundaries` (dasa ladder): **262,730** total (AD/MD/PD/SD across
  6 systems: chara_karaka, kalachakra, mudda, naisargika, vimshottari,
  yogini).
- `kala_field_kinematics` (motion events): **120,377** total.
- `kala_field_primitives` (derived envelope primitives): **166,205** total.

None of these individually or combined equals 343,973. The actual source,
confirmed via `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md:1623` (SM-R-6
desk ruling: "2,063,838 exact segment rows (343,973/class = the true knot
count K)") and traced to the writer's INSERT target: the **`kala_field`**
table (the log-linear hazard segment table itself, 23 columns).

Live query:
```sql
SELECT count(*) FROM kala_field WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
→ 2063838

SELECT event_class, count(*) FROM kala_field WHERE chart_id=... GROUP BY 1 ORDER BY 1;
    childbirth          343973
    foreign_settlement  343973
    marriage            343973
    relocation          343973
    separation          343973
    surgery             343973
```
Exact match: 343,973 × 6 = 2,063,838 — and this is the **same 6-class set**
that carries `ne_v01` demographic priors in G9. Not a coincidence: these are
DHARA's currently-wired 6 hazard-model classes, a strict subset of the 27 in
`brahma_event_ontology`.

**Memory footprint estimate** (K=343,973 knots per class, float32):
- Single class, 20 cols: 343,973 × 20 × 4B ≈ **26.2 MB**; 30 cols ≈ **39.4 MB**.
- All 6 wired classes, 20 cols: **≈157.5 MB**; 30 cols: **≈236.2 MB**.

Against an 8Gi budget (≈8.59 GB): even the largest estimate is ≈236 MB, **≈2.9%
of budget**. Doubling to float64 or doubling column count again would still
stay under 6%.

**IMPLICATION:** Memory is not the constraint on this build path — the plan's
own §4 time budget table already locates the bottleneck correctly elsewhere
(I/O-bound COPY writes, sequential null replicates), and this DB-grounded
measurement confirms it: even a generously-sized chart-level raw matrix for
all 27 classes would fit an 8Gi job with wide margin. One caveat for the plan
document itself: its own search hints (`kala_field_boundaries`/
`kala_field_primitives`) point at INPUTS, not the OUTPUT table (`kala_field`)
that actually carries the 343,973/class figure — a reader following only the
named tables would not find where that number lives.

---

## G12 — SERVING CLASS-UNIVERSE QUICK SCAN

**VERDICT:** Three hardcoded event-class-list sites found in `kala_*` MCP code
paths — none is a 6-class default; all three are static compile-time
duplicates of the ontology universe (drift risk, not silent undercounting).
The correct dynamic-read pattern is already used in several other serving
surfaces, confirming this is a small, targeted P6 fix, not a broad rewrite.

**EVIDENCE — hardcoded event-class lists in `kala_*` code paths:**

1. `platform-mcp/src/lib/ahead_autofile.ts:124-165` —
   `KNOWN_EVENT_CLASSES`, a 27-entry hardcoded `ReadonlySet<string>` literal,
   imported by `platform-mcp/src/tools/kala_views/ahead.ts:96`
   (`kala_ahead_get`). Comment (lines 116-123): *"the committed set from
   brahma_event_ontology (migrations 388 + 456 + 421 + 551 + 555)... When the
   ontology gains a new event class, this set gains it too; CI tests in
   ahead_autofile.test.ts catch omissions."* A manually-maintained mirror, not
   a dynamic read — currently 27 by coincidence of current state, not
   architecture.
2. `platform-mcp/src/lib/ahead_autofile.ts:108-114` —
   `AUTOFILE_WITHHOLD_EVENT_CLASSES`, a hardcoded 5-item `Set`
   (`illness_acute, chronic_onset, surgery, psychological_arc, bereavement`).
   Comment: *"mirrored from intervention_filing.ts §5.3 / ADJUDICATION-13 ...
   both places must stay in sync."*
3. `platform-mcp/src/lib/kala_upaya_diagnosis.ts:774-779` —
   `ADVERSE_WITHHOLD_EVENT_CLASSES`, an independently-declared hardcoded
   5-item array (same 5 values), imported by
   `platform-mcp/src/tools/kala_views/upaya.ts:74` (`kala_upaya_get`). Own
   docstring (lines 762-773): *"platform-mcp has no direct DB connection and
   no MCP-exposed primitive for querying brahma_event_ontology by
   domain/lel_category... this is a VERIFIED SNAPSHOT constant, not a live
   query... flagged here for the Conductor, not silently worked around."* — a
   self-documented, previously-escalated architectural gap, not an oversight.

**Not in scope** (different taxonomy, noted for completeness):
`register_p1_aliases.ts:788` and `L1_ganita/get_vichara.ts:51` hardcode a
5-item **domain** enum (`wealth, career, marriage, health, general`) — an L1
Gaṇita tool, not `kala_*`, and a different/smaller taxonomy than
`event_class`. `muhurta_finder.ts:85,1007` / `query_muhurat.ts:30` hardcode a
7-item **muhurta purpose** enum, same caveat. Test fixture only:
`s4_05_health_coverage.test.ts:36-45`'s `DOMAIN_UNIVERSE`/`DOMAIN_OF` — mock
data, not a serving defect.

**Counter-evidence (dynamic reads already in place elsewhere):**
`register_gochara_windows.ts:1007` (`SELECT DISTINCT domain FROM
brahma_event_ontology WHERE domain IS NOT NULL ORDER BY 1`),
`lel_intake_checklist.ts:237`, `prediction_lifecycle_sweep.ts:267,370`,
`query_prospective_ledger.ts:180`, `query_predictive_anchors.ts:177-201` all
query the ontology live.

**IMPLICATION for P6:** the sweep is small and targeted, not a blanket audit
— the codebase is already overwhelmingly dynamic where it matters. Concrete
P6 work: (1) `ahead_autofile.ts`'s `KNOWN_EVENT_CLASSES` needs to become a
dynamic/cached read or get a CI drift-guard against a live query; (2) the two
duplicated 5-item withhold lists (`ahead_autofile.ts` +
`kala_upaya_diagnosis.ts`) should consolidate to one shared source or get the
new `query_event_ontology_class`-style primitive `kala_upaya_diagnosis.ts`
already flagged as missing — P6 should first check whether that
previously-escalated flag was ever picked up. No `kala_*` surface was found
silently hardcoding a *smaller* display universe (e.g. 6 classes) for
end-user-facing "here is the universe" presentation.

---

## ASSUMPTIONS THAT FAILED

1. **I-2's shape_only claim ("prior-less classes can ship honest shape_only
   timing output") is not implementable as stated today** — see G5. The
   scale-invariant math is real, but `hazard.baseline_rate()`/
   `stage4_field.require_baseline()` hard-gate and skip any class without a
   real lifetime-count prior *before* any window/null/salience math runs, and
   `expected_count` leaks to the served timeline spec unconditionally where
   the gate is bypassed. P3 needs an explicit synthetic-baseline injection
   design, not a downstream relax.
2. **`DHARA_DESIGN_v1_0.md`, cited throughout the plan as a "frozen §4
   artifact," is not merged to `origin/main`** — see G4. It exists only on an
   unmerged `sampurti/integration` worktree branch with `status:
   AMENDED_BLIND`. Any claim that treats it as settled, shipped doctrine is
   currently unsupported by what's actually in production.
3. **The §4 term matrix is a per-class weighted artifact, not the chart-level
   shared raw layer I-1 implies it already is** — see G4. P1 needs to add a
   genuinely new Layer 0 (chart-level, unweighted, class-independent) beneath
   the existing per-class §4 Layer 1, which stays unchanged.
4. **`bg_class_priors` (named in the plan/task) does not exist** — see G9. The
   real table, `brahma_class_priors`, is keyed by `signal_type_class`
   (a 33-value signal/tradition taxonomy), not `event_class_id`, and only 6 of
   its 177 rows are structurally complete demographic priors for event
   classes — covering 6 of 27 classes, not a general per-class template.
5. **The plan's search hints for the 343,973-segment figure
   (`kala_field_boundaries`/`kala_field_primitives`) point at the wrong
   tables** — see G11. The figure lives in the OUTPUT table `kala_field`, and
   is per-class for only the 6 currently-wired classes, not a knot-set size in
   itself.
6. **The suppression term's own docstring claim of per-class vighna filtering
   is false in the live evaluator** — see G3. Every active obstruction
   currently suppresses all 27 classes uniformly; either the docstring is
   stale or this is an unlabeled bug — needs a native ruling before the
   rebuild encodes either behavior as intentional. (Separately, `dhara_term_
   matrix.py`'s §4 implementation, per G4, *does* assume per-class vighna
   columns — meaning the frozen artifact and the live evaluator already
   disagree with each other on this point, independent of the plan.)
7. **"The current null" is not a single definition** — see G7/G10. Two live,
   diverging engines exist (`stage5_null.py` R+1-denominator,
   `dhara_null.py` R-denominator, itself already amended once from 1024→256
   replicates same-day), reconciled downstream by a `getattr` fallback that
   silently picks the wrong resolution formula if a result object doesn't
   declare its own `.resolution`. `contracts.py` — the designated frozen
   cross-lane boundary — holds neither definition.

## OPEN UNKNOWNS

- **Whether any event class besides `birth_anchor` needs its own
  `kill_switch_criteria` entry** (G8) — not systematically checked across all
  27 rows' full JSON; the tier-basis table (P3) will need a per-row read, not
  a flag-column query.
- **Whether the `expected_count` leak (G5) is the only absolute-value leak** —
  only `stage8_spec.py`'s `interval_from_window()` was audited; other kala_*
  serving surfaces (`kala_now_get`, `kala_windows_get`, `kala_priority_get`,
  etc.) reading `kala_field_windows`/`kala_field_null` were not individually
  swept for the same pattern in this pass.
- **Whether `_run_stage5_block`/`stage5_null.py`'s "sampled" engine path is
  still exercised in any live build**, or whether it is effectively dead code
  now that `ENGINE_VERSION` defaults to `analytic` — not determined; would
  need a DB/config check of the live `ENGINE_VERSION` setting and a build-log
  audit, out of scope for this pass.
- **Whether `kala_upaya_diagnosis.ts`'s self-flagged missing primitive
  (`query_event_ontology_class`-style) was ever picked up by a subsequent PR**
  (G12) — the escalation comment exists in the current file; whether it was
  actioned since was not traced through PR history.
- **The full 177-row verbatim dump of `brahma_class_priors`** (G9) was
  captured during the DB agent's session but not reproduced in full in this
  report — only the 6 fully-cited rows and a representative sample of the 171
  sparse rows are shown. If a complete per-row audit of the W1_SEED cohort is
  needed for P4 scoping, re-run `SELECT * FROM brahma_class_priors WHERE
  ratified_by = 'W1_SEED_PACKAGE_v1_0';`.
- **Whether stage6/6.5's unbatched per-window/per-class DB round-trips
  (G6) will actually regress at 27 classes**, or stay within budget — flagged
  as a scaling risk by code-shape analysis only; no load test was run in this
  read-only pass.
