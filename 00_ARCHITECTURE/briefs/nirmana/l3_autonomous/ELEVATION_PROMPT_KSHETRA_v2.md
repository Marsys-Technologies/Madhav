---
artifact: KALA_ELEVATION_PROMPT_KSHETRA
version: "2.0"
status: READY_TO_PASTE
date: 2026-09-22
instantiates: KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md for ka_kshetra (staged-internal-DAG shape)
scope: stages 0–2; terminal PROPOSED_FOR_NATIVE_RULING
---

You are elevating **`ka_kshetra`** — the continuous temporal field. It is the layer's *richest*
temporal object and its *least reachable*. Your scope is **stages 0–2** of
`KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md`, in the **staged-internal-DAG** shape: the frozen
stage plan is your packet boundary. Stop at `PROPOSED_FOR_NATIVE_RULING`. Base branch is
**`main`** — it carries P0 (`3f109869d`), the DHARA midpoint fix (`87cc8c9baf`) and
`DHARA_SWEEP_SEMANTIC_VERSION = '1.2'` (`services/ka_kshetra/dhara_sweep.py:52`) by content. Read
files not yet on `main` with `git show origin/l3/kala-elevation-readiness:<path>`.

## Read, in this order
1. `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_ELEVATION_PLAN_TEMPLATE_v2_0.md` (all); `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_BRIEF_INSTANTIATION_GUIDE_v1_0.md` §2–§12.
2. `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/W0_DELTA_KSHETRA.md`; `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md`.
3. `briefs/nirmana/MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md` §4.1, §5, §6 item 5, §8;
   `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_DHARA_NUMERICAL_CONTRACT_v1_0.md` (all); `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_DP019_KSHETRA_GATE_ACCEPTANCE_v1_0.md`.
4. `briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §3 (**Interval/trajectory segment**,
   **Search coverage**), §5 rows **P0/P1/P2/P6** with their equivalence contracts, §6.1 row A22,
   §6.2 (the nine data families + the stage diagram + the rectification paragraph).
5. `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md` — Kshetra's 15 relations (13 Q1, 2 QX); fences 4, 6.
6. `l3_autonomous/readiness/_work/LANE_C_HARD_ASSETS.md` F4/F5/F6/F12.

## The asset's value proposition (stage 1) — answer this before anything else
VA §6.4: *"`ka_kshetra` should contribute its useful search/temporal-integration engineering as a
**mechanism-qualified candidate substrate**, not become a universal authority that all questions
accept without reconstructing its inputs."* The Strategy §3 object you own is the
**Interval/trajectory segment**: *onset/peak/decay/recurrence, boundaries, component witnesses,
null/missing states, evaluation resolution/error bounds, generation and horizon* — the only Kāla
producer that gives a consumer a *shape over time* rather than a window. Which of L3-Q01–Q13 does
that uniquely serve? (Q06 chapter-vs-chapter and Q07 domain interaction over time are the natural
homes; Q08's *"is no window a real negative"* is where your null model earns or loses its keep.)
Name the distinction, the simpler baseline (Sangam's windows), and the ablation.

## What is physically there — the richest object in the layer (register, measured)
`kala_field` (21 fields): per-segment `alpha`, `gamma`, `lambda_start/end`, `integral_days`, four
term multipliers (`promise`, `clock`, `modifier`, `suppression`), `signed_obstruction_start`
in [−1,0], `refinement_depth/exhausted/residual`. `kala_field_windows` (27): `t_peak`,
`lambda_peak`, `expected_count`, `duration_days`, `promise_state`, `temporal_shape`,
**`precision_regime`**, `null_p`, `null_r`, `null_resolution` (= 1/(R+1), honestly declared).
`kala_field_null` (11): `replicates`, `q_threshold`, `bucket_days`, `null_max_stats[]`,
`shift_grid_step`, `weights_version`. This is not an asset that needs *more*; it is an asset whose
richness is **unqualified and unreachable**.

## What is missing (lens 2.1 — four different fixes)
- **(d) Unqualified:** only 6 classes carry a real prior; **85.7% of windows are
  `baseline_is_synthetic`** — so `null_p` is meaningless for most classes — and `kala_field` has no
  such column despite `hazard.py:150-155` claiming the tag rides every row. The other chart holds a
  complete, calibrated 6-class run: **two configurations, not two runs.** Decide which is the
  product, and make the synthetic-vs-real baseline a first-class, honest field (F06 `unqualified`).
- **(a)/(unserved):** **no retrieval capability exists over any `kala_field*` table.** The layer's
  largest investment is unreadable by the product; under Strategy §7 that caps it below
  `CONSUMER_INTEGRATED` no matter what. The brief must include an L3-U11 interface packet (a
  capability + sentinel test), or state honestly that the asset is research-only.
- **(c) Incomplete generation:** every row references a `field_snapshot_id` with zero manifest
  rows; stage 5 died in alphabetical class order (25 classes have segments, 15 null stats, 14
  windows, 0 salience/insights/timeline). W0 already classes the 10.97M rows "not accepted useful
  coverage or a rebuild warrant."
- **Contrary to the Strategy:** `stage3_clocks.py:1012` reads `phala_rectification` live. §6.2:
  *"Rectification and L5 weight inputs require separately admitted, purpose-compatible immutable
  artifacts. An earlier timestamp does not make an event-derived rectification posterior
  admissible under the event-free prospective contract."* Replace the read with an admitted
  artifact (lens 2.6). This read is also absent from the W0 register — a register amendment.

## Efficiency with quality (lens 2.3) — the named candidates, with their contracts
Do **P0 before any trial** (accepted; do not re-prove). Then, in Strategy §5's study order:
- **P1 DHARA null** — *"~372M scalar sliding-window differences and 37M heap visits per class"* →
  *"existing exact numeric slice maximum plus an exact blocked order-statistic reducer."*
  Equivalence: *"same finite-value policy, float64/rank/ties, full shift set, duration buckets and
  statistical denominator."* Inherit DHARA 1.2 and the accepted midpoint fix as the reference.
- **P2 shared context and sweep** — full-century preparation repeated per class → *"immutable
  chart preparation, lightweight class projections, event/clock sweep, sparse obstruction
  support, direct segment-reader path."* Equivalence: *"same class/method meaning, numerical
  function, breakpoints, evidence roots and null scope; suppressed/empty classes remain explicit."*
- **P6 publication** — O(windows × legacy rows) cross-check → *"interval-indexed matching, bounded
  streaming publication, one timeline payload, optional exact complement for divergence."*
  Equivalence: *"every agreement/counterexample remains recoverable; no top-K deletion of contrary
  evidence."*
Measured cost ~7.5 h against a registry claim of 237 s — cite `KALA_COST_PROFILE_v1_0.md` and the
W0 baseline (null 0.31 s, prep 0.47 s, publication 6.99 s, small fixture). *Fewer simulations,
approximate quantiles or fewer years are not equivalent performance repairs.* S0 and S2 have
independent prerequisites; that *"does not authorize changing the frozen scheduler's present
serial behavior."*

## Synergy (lens 2.4)
**Receives:** L2 signed multidomain mechanisms through the promise graph (S2 — *"restore complete
signed mechanism/cancellation semantics rather than unsigned grade"*); L1 exact clocks (S3 —
hour grain and sandhi must survive); resonance targets from Gochara; legacy Gochara cross-checks
as *validation inputs, not contributors to λ*. **Owes:** `kala_timeline_spec` and
`kala_field_snapshots` to whatever serves the temporal landscape (Product §9 experience 4);
`kala_insights` (`lel_derived=false` only) to discovery. Name the seams where L2's signed structure
becomes an unsigned conductance, and where the exact clock becomes a day.

## Fences and holds
Frozen stage plan `S0 + S2 → S3 → S1 → S4 → S5 → S6 → S6.5 → S8 → snapshot` (direct S0 into S4);
**populated-chart replacement held until W7** — no rebuild trial on the canonical chart before
that infrastructure exists; you own only `kala_insights.lel_derived=false`; `kala_field_weight_
versions/weights` are inputs owned outside; `build_substep_progress` is the orchestrator's; Q2/Q4/
QX are closed gates.

## Decisions to put to the native
Product configuration: the 6-class calibrated run or the 25-class incomplete one · complete, re-scope
or park (with preservation) — recommend on the value proposition, not on sunk cost · the serving
capability's shape · the admitted-artifact source for rectification · which of P1/P2/P6 first.

## Deliver
`KSHETRA_ELEVATION_BRIEF_v1_0.md` in contract §1–§8 shape, packeted **by stage**, with the
latent-value register, the P1/P2/P6 equivalence contracts, the interface packet for retrieval, and
the A–J lenses. Propose; the native rules.
