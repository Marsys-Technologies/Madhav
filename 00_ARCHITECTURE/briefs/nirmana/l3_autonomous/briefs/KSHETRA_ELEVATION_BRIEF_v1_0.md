---
artifact: KSHETRA_ELEVATION_BRIEF
canonical_id: KSHETRA_ELEVATION_BRIEF
version: "1.0"
status: DRAFT_FOR_NATIVE_RULING
date: 2026-09-22
asset: ka_kshetra (L3-A22)
packet_shape: MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md §6.4
governed_by:
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md
  - briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md
  - briefs/nirmana/MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
  - briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md
  - l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md
  - l3_autonomous/KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md §C5, §7
path_roots: >
  Bare code filenames in this brief (writer.py, layer1.py, hazard.py, contracts.py,
  stage3_clocks.py, stage4_field.py, stage5_null.py, dhara_null.py, uncertainty.py) resolve
  under platform/python-sidecar/services/ka_kshetra/ — NOT under a repo-root services/ path,
  which does not exist. Bare governance filenames resolve under 00_ARCHITECTURE/briefs/nirmana/.
  Every other path is written in full from the repository root.
evidence_base:
  - l3_autonomous/readiness/_work/LANE_C_HARD_ASSETS.md §B (F4, F5, F6, F12) — live DB figures inherited, NOT re-measured here
  - source read directly in worktree l3/kala-elevation-readiness @ d2c577d3d (every file:line in §2 verified in this session)
not_re_measured: >
  The database was unreachable from this session (ECONNREFUSED 127.0.0.1:5433). Every row count,
  class census and privilege result in this brief is Lane C's measurement, cited as such. Nothing
  live was independently re-confirmed. Source-level claims WERE independently verified and are
  marked VERIFIED HERE.
does_not_authorize: >
  No code, migration, grant, build, campaign change or asset retirement. This brief proposes; the
  native rules. It does not extend PURNA_KSHETRA_PLAN_v1_1 (Pūrṇa-owned), does not edit
  platform-mcp/src/tools/kala_views/* (Pūrṇa-owned), does not weaken the L2 cross-layer delete
  guard, and proposes no orchestrator contract change (§N.2).
independent_reviewer: UNASSIGNED — see §11.
---

# `ka_kshetra` elevation brief

## §0 — The recommendation, in one paragraph

Do **not** complete the 25-class generation, and do **not** park the asset. **Re-scope to the
calibrated 6-class configuration and take it to a published snapshot** — the configuration the
other chart has already completed end-to-end (F6), which requires no §N.8 waiver because all six
classes have a real `brahma_class_priors` baseline. Before that, three zero-cost P0 acts: **guard**
(not grant) the `phala_rectification` read, **preserve** the existing 8.57M rows against the delete
that the next pin-changing run will perform, and put a SAVEPOINT around the cohort read. The
25-class / 19-synthetic partial generation is then **preserved in place as substrate**, not
completed — it is Pūrṇa's P3 tier programme that makes it publishable, and publishing it today
would publish exactly what §N.8 forbids. The reason to do any of this at all is a single consumer
question the field uniquely serves — **L3-Q08, "is no window found a real negative?"** — and §1.3
gives the ablation that would falsify that claim. If the ablation fails, the honest disposition is
park-with-preservation and the P1 null programme is never paid for.

---

## §1 — What the continuous field is *for*

### 1.1 The qualified purpose, in the native's terms

Kshetra is not a window-finder. It models, for each life-event class, a continuous time-varying
hazard `λ_e(t)` over a 100-year horizon and stores it as a contiguous piecewise-segment table with
its **term decomposition preserved per segment** (`promise_term`, `clock_term_start`,
`modifier_term_start`, `suppression_term_start` — VERIFIED HERE in `_KALA_FIELD_INSERT_SQL`,
`writer.py:631-644`).

Two properties follow from that, and only from that:

1. **Totality.** λ is defined at *every* instant of the horizon, not only where something was
   found. Lane C measured the canonical chart at 342,803 segments per class spanning exactly
   0…36,525 days with no gaps.
2. **Attribution.** At every instant the model retains *why* λ is at its level, decomposed into
   the four terms — of which the clock term is the only genuinely classical operand (daśā lord
   stacks scored against stored causal `Route`s, `layer1.py:96-136`).

Every other L3 asset produces a *set of found things*. The field produces a *function over the
whole horizon*. That difference is the entire case for the asset, and it is the thing that must be
tested before P1 is paid for.

### 1.2 The question it uniquely serves

**L3-Q08 — "Is *no window found* a real negative?"** Required added distinction: *searched
horizon, resolution, method/target coverage, unavailable inputs and unknown intervals.* Named
proof: *a window just outside a searched partition must not become a universal denial.*

A discrete window ladder cannot answer this. Its silence is structurally ambiguous between
"searched and genuinely absent", "outside the searched partition", "truncated by a cap" and "the
method never ran" — which is precisely the ambiguity VA §10.2 and the layer's cap defects
(`LIMIT 750`, `max_windows=8`, top-500) are made of. The field converts absence into a *positive,
inspectable statement*: λ is defined here, it is this low, and here is the term that is missing.
That is the F06 completeness vocabulary expressed as data rather than as a label.

**Serves strongly but not uniquely:**

- **L3-Q04** — *why can activity coexist with strain?* The field stores `clock_term` and
  `suppression_term` **on the same segment at the same instant**, with SM-R-7 Option B guaranteeing
  that only obstructions a `Route` explicitly names in `suppressed_by` can suppress a class
  (`layer1.py:152-165`). Co-existing support and inhibition, continuously, both polarities retained.
  Vighnakara also addresses Q04 by a different route, so this is not unique.
- **L3-Q06** — *how does this chapter differ from the preceding one?* Two intervals at the same λ
  with different term composition is exactly "recurrence with changed participants/conditions/clocks".
  Jivana Parva also addresses Q06.

**Partially serves:** L3-Q01 (the "why" half, via decomposition; the "what is active now" half is
Darshana/Sangam's).
**Cannot serve:** L3-Q10 (election — not Kshetra's object), **L3-Q11** (observation fit — the
Circularity Guard forbids the field from consuming outcomes; `mi_bhara` owns that side and
`kala_insights.lel_derived = true` is not Kshetra's to write), **L3-Q13** (delivery — Pūrṇa's).
**L3-Q05** it actively complicates: the field's λ is on a scale that no other L3 asset shares, so
it must ship a comparability flag declaring itself non-comparable (context §1).

### 1.3 The ablation that would prove it — and the one that would kill it

**THE HONEST-NEGATIVE ABLATION (primary; decides whether the asset is worth its cost).**

Take one calibrated class and one horizon interval in which *no window was written*. Pose the
consumer question — *"is there no window here, or was this not searched?"* — twice:

- **Arm A (competent simpler baseline, per D10):** the window ladder plus its own declared search-
  coverage metadata, and nothing else.
- **Arm B:** the same, plus the field's λ over that interval and its four-term decomposition.

**If Arm A already distinguishes a real negative from an unsearched region, the field does not earn
L3-Q08, and with it the asset loses its unique claim.** Then the disposition is park-with-
preservation and P1 is never paid for. **If Arm A cannot and Arm B can, L3-Q08 is earned** and the
field's totality is load-bearing, not decorative.

This must be run against Arm A at its *best* — the window ladder with honest coverage metadata,
not a strawman ladder with silent caps.

**Supporting ablations (cheaper, run first):**

| # | Ablation | What a null result proves |
|---|---|---|
| A1 | **Within-class rank invariance.** For the 2 calibrated and 12 synthetic-baseline classes that have windows, compare window *rank order* within each class. λ⁰ is a constant multiplier, so within-class rank *should* be invariant to a synthetic baseline. | If invariant: the synthetic baseline affects only **cross-class** comparison and absolute counts. The native may serve within-class rank honestly today and defer the priors work. One aggregate query; highest information per unit cost on this asset. Lane C named it and did not run it. |
| A2 | **Decomposition ablation.** Take the top-10 windows by `lambda_peak`, generate a mechanism sentence from the four terms, then zero the clock term and regenerate. | If the sentence does not change, the only genuinely classical operand is not doing the work the model claims, and §1.1's attribution argument fails. |
| A3 | **Replicate ablation.** Re-run one class at R=128 against R=1024 and compare *window rank by* `null_p`. | If rank is unchanged, ~87% of S5 cost buys resolution nobody consumes — which is a P1 finding, but see §5.3: it is **not** an equivalence proof and cannot be used as one. |
| A4 | **Salience ablation** (only after a published snapshot exists). Answer one real timing question with `kala_priority_get`'s five-axis salience present vs absent. | If the top-5 ranking is identical either way, salience is decorative. |

---

## §2 — Findings that change the decision

Source-level findings below were **VERIFIED HERE** by reading the files in this worktree. They are
additional to Lane C's F4/F5/F6/F12, which this brief inherits without re-measurement.

### K-A — CORRECTION to Strategy §5's P0 row: the Kshetra planner-mutation hazard is already repaired

Strategy §5 P0 reads *"Kshetra planning deletes data before resume filtering."* That describes a
state the source no longer has. **VERIFIED HERE:** `plan_substeps` (`writer.py:277-488`) contains
no DML of any kind. `_delete_prior_rows` is called from `writer.py:563`, inside the executed
`prepare:replace` **substep**, under the orchestrator's per-substep savepoint and commit boundary,
with a `_dry_run` guard. The code carries its own marker for the repair — `writer.py:400-404`:
`# DP-SD-017 KSH-P0: replacement is executable work, not planning.` Resume filtering
(`_load_completed_substeps`, `writer.py:2449-2458`) runs in the planner and removes
`prepare:replace` from the emitted step list when its key is in the progress ledger.

**Two limits on this correction, stated rather than glossed:** (a) P0 has a second half —
Bhavishya's empty-input early return preceding its outcome-preservation guard — which this brief
does not examine and which is **not** covered by the above; (b) this is a claim about source on
this branch, not about the deployed revision (D9 is a separate question, not verified here).

**Consequence for §8's sequencing:** Kshetra's P0 half does not gate the disposition. What *does*
gate it is K-B.

### K-B — The 8.57M rows are deleted by the next pin-changing run. Preservation is an act, not a default.

**VERIFIED HERE.** `field_snapshot_id` is not a run id. It is a content hash of the pin vector
(`stage4_field.py:186-212`): `chart_id`, `corpus_pin`, `weights_version`, `x_schema_version`,
`cohort_version` and `config_pin` — where `config_pin` includes **`null_replicates` and
`segment_engine`** (`writer.py:324-341`). The build fingerprint includes the snapshot id
(`writer.py:2441-2445`), and a fingerprint mismatch makes `_load_completed_substeps` return `None`
(`writer.py:2456`), which routes to the fresh-build path and executes `prepare:replace` — a
`DELETE FROM` every one of the fifteen writer-owned tables (`_OWNED_TABLES`, `writer.py:2477-2520`).

This is correct, deliberate behaviour and the identity discipline is sound. But it has three
consequences that decide this brief:

1. **P1 and P2 change `config_pin` by construction.** Changing the replicate count or the segment
   engine mints a different `field_snapshot_id`. Therefore **"optimise, then complete the existing
   generation" is not an available option** — optimisation orphans the 8.57M rows and the next run
   deletes them. It is *complete under the current pins* or *rebuild from zero under new pins*.
2. **Park-with-preservation is not passive.** Leaving the asset alone does not preserve the rows;
   it merely defers the run that deletes them. If the native chooses to preserve, that requires an
   explicit act (§7.3) *before* any run with a changed pin vector.
3. **Resume to completion under unchanged pins is mechanically supported.** The dangling
   `kfs_1805…8e5f` is deterministic and re-derivable, so the existing rows are addressable. One
   real cost caveat: a class whose stage-5 blocks are partially complete re-runs *all* of them,
   because the quantile pool is in-memory (`_is_partial_null_class`, `writer.py:430-436`) — so
   `major_loss`, the class the run died inside, re-runs entirely.

### K-C — F5's mechanism, at source: the earned-signal tag is discarded with an underscore

Lane C established from `information_schema` that `kala_field` has no `baseline_is_synthetic`
column while `hazard.py:150-155` claims the tag is *"a queryable field on every downstream row."*
**VERIFIED HERE**, the mechanism is exact and is in two places:

- `layer1.py:89` — `lam0, _baseline_is_synthetic = baseline_rate(...)`. The tag is computed
  correctly by `hazard.baseline_rate` (`hazard.py:164-165`) and **thrown away at the point of
  computation**, by underscore convention, in the hot path that produces every field row.
- `_KALA_FIELD_INSERT_SQL` (`writer.py:631-638`) writes 21 columns; the tag is not among them.
  The W0 field contract register agrees — it holds exactly **21 rows for `kala_field`** and none is
  `baseline_is_synthetic`.

The tag that *does* reach `kala_field_windows` comes from a parallel class-level flag
(`cctx.baseline_is_synthetic`, `writer.py:793,922`), not from the hazard evaluation that produced
the row. So the window-level tag and the segment-level computation are two different objects that
happen to agree. This is §N.8 precisely: a signal whose claim ("every downstream row") no code path
could make false, because the row it claims to ride does not carry it.

**Boundary note:** this is Pūrṇa P3-a's deliverable ("`HazardTerms` gains a `baseline_is_synthetic`
field threaded through to every row it produces"). It is **theirs to land, not this brief's to
re-specify.** What this brief contributes is the measurement that P3-a is *partially* landed —
`HazardTerms` has the field (`hazard.py:425`), the windows carry it, `kala_field` does not — and
the ruling that **no 25-class generation may be published until it is** (§7.2).

### K-D — CORRECTION to Lane C's K-4: `confidence_tier` is binary by design, and `weakest_link` is the field to read

Lane C recorded `count(DISTINCT confidence_tier) = 1` over 17,528 windows as a "degenerate tier,
the same defect class as Sangam's `confidence_label`". **VERIFIED HERE, it is not the same defect
class.** `RobustnessVector.confidence_tier()` (`contracts.py:219-227`) returns `'concurrent'` iff
all five robustness dimensions are `True`, else `'structural_prior'`. It is a **two-valued** field,
and the higher tiers (`calibrated_provisional`, `calibrated`) are deliberately unreachable from
stage 5 — the Circularity Guard, so the field cannot promote its own confidence without outcome
data. That is honest design, not a degenerate label.

The companion field `weakest_link()` (`contracts.py:207-217`) names the **first non-`True`
dimension in a fixed order**, and each of the five detectors returns `None` — honest not-computed —
rather than passing when it has nothing to falsify with (`stage5_null.py:580-624` for
`birth_time_robust` and `ayanamsha_robust`; both are textbook §N.8). So a single tier value is not
the finding; **the finding is whichever dimension `weakest_link` names, and Lane C did not report
its distribution.**

**Hypothesis worth one aggregate query, named as a hypothesis and not a result:** `birth_time_robust`
returns `None` whenever σ_T is unknown, and σ_T for that dimension is read from
`kala_field_boundaries` (`writer.py:2231-2251`) — rows produced by the stage-3 path that cannot run
today (F12). If `weakest_link` is uniformly `birth_time_robust`, the single tier value has one
nameable cause, it is the same cause as F12, and §4's disposition fixes it. If it is uniformly
`ayanamsha_robust`, the cause is single-ayanāṃśa kinematics coverage and is a different repair.
**One query settles which; it has not been run.**

### K-E — The 221-row field register supplies no receiving operators and no falsifying tests

**VERIFIED HERE.** The W0 field contract register holds **221 rows across Kshetra's 15 tables**
(`kala_field_windows` 27, `kala_field_salience` 22, `kala_field` 21, `kala_field_kinematics` 20,
`kala_insights` 18, `kala_field_provenance` 16, `kala_field_boundaries` 15, `kala_field_primitives`
14, `kala_field_snapshots` 13, `kala_timeline_spec` 11, `kala_field_null` 11, `kala_field_clocks`
10, `kala_field_routes` 8, `kala_field_promise_nodes` 8, `kala_field_promise_edges` 7).

- **All 221** carry the byte-identical receiving-operator string: ``` `kala_views`
  story/explain/ritual, timeline widget, `mi_bhara`/field consumers ```.
- **All 221** carry a falsifying test prefixed `FUTURE `.

That string is also partly false: Lane C established `ritual.ts:783-789` reads *nothing* from the
field, and that **no retrieval capability exists over any `kala_field*` table** — independently
confirmed here by directory listing (`platform/src/lib/retrieval/registry/layers/L3_kala/` holds 16
capabilities, none over a field table; `grep -rl 'kala_field'` over the whole registry returns
nothing).

So the honest answer to *"which of the 699 registered fields are load-bearing?"* is: **for Kshetra,
none has yet been established.** The register is a correctly-shaped table whose two D1-decisive
columns are uniformly templated placeholders. The worklist is 221 rows and it has not been started.
(Minor: the register cites `writer.py:564` for `_KALA_FIELD_INSERT_SQL`, which is at `:631` on this
branch — the register was captured against an older revision.)

### K-F — The stale-prose defect sits on the exact quantity Q4 asks about

**VERIFIED HERE.** The implemented p-value is `(1 + exceed) / (len(stats) + 1)`
(`stage5_null.py:130-141`), where `len(stats)` is the number of replicate maxima — under the
F-01-corrected grid `range(1, R)`, that is **R−1 = 1023**, giving denominator **1024 = R**. That is
correct and agrees with `contracts.py:250-257` ("the p-value denominator is R (= 1 observation +
R−1 shifts)").

But `dhara_null.py:39`, in the module header whose whole purpose is to announce the F-01
correction, states `null_p = (1 + #{...}) / (R + 1)` — which under that module's own
`DEFAULT_REPLICATES: int = 1024` reads 1025. The symbol **R denotes 1024 in the constant and 1023
in the formula's denominator term**. The arithmetic is right; the documentation of the denominator
is ambiguous across three files, on the one quantity the native's Q4 asks to have settled. Cheap to
close, and §5 closes it.

Related and **not** a live defect: `S5.null_resolution()` still returns `1/(R+1)`
(`stage5_null.py:144-146`), which `contracts.py:257` explicitly calls wrong for this grid — but the
writer binds `null_result.resolution` (`writer.py:1001`), the corrected `1/R`. Pūrṇa P0.b's
fallback deletion landed. `S5.null_resolution` is dead for this path.

---

## §3 — Rulings proposed on PROMPT_2's seven questions

| # | Question | Proposed ruling | Rationale |
|---|---|---|---|
| **1** | Is the continuous-field model the right abstraction to preserve? | **Not yet established — and that is the honest answer, not a deferral.** Preserve the capital; make the §1.3 honest-negative ablation the gate. Do not pay for P1 before it returns. | The evidence is genuinely two-sided and Lane C is right that it is compatible with either answer. What rules out deciding today is that the decisive property (totality answering L3-Q08) has never been tested against a competent ladder baseline. Deciding "yes" on 8.57M rows is the presence-is-value error; deciding "no" on zero delivered value is the unknown-use error (context §7). |
| **2** | What is `kala_field` *for*? | **L3-Q08 uniquely; Q04 and Q06 strongly but not uniquely; Q01 partially. Not Q10/Q11/Q13. Must declare itself non-comparable.** | §1.2. Q11 is barred by the Circularity Guard, not merely unserved. |
| **3** | PARK-5 — is the served surface wrong, or the data unusable? | **Neither. The framing is the defect.** The data is a legitimate *incomplete, unpublished* partial product; two served surfaces carry stale prose; one surface (`kala_priority_get`) reads salience honestly and finds nothing because S6 never ran. **The load-bearing gap is that no retrieval capability exists over any `kala_field*` table.** Repairing the prose fixes nothing a user sees. | F4 + K-E. Under Strategy §7 the missing capability caps the asset below `CONSUMER_INTEGRATED` regardless of data quality. **PARK-5 is hereby re-scoped from a prose defect to an interface-packet obligation** (§6.2 / L3-U11). |
| **4** | The null programme — what do p/R mean, honest denominator, oracle? | **Settled in §5.** | §5. |
| **5** | Staged acceptance and `Accepted N/22` | **One terminal asset for counting; staged acceptance for work.** §10. | The snapshot manifest is all-or-nothing *by design* and is the asset's only publication identity. A stage-accepted, unpublished field has no meaning to a consumer. |
| **6** | Resume and publication semantics | **Confirmed correct as built; one gap.** Pin-hash identity + fingerprint gate already guarantee that a changed dependency invalidates and that a resume cannot mix generations (K-B). **The unconfirmed half is late-worker protection** — nothing verified here prevents an old worker publishing over a newer accepted generation. §9 names it as an open obligation, not a solved one. | K-B. |
| **7** | Which of the 699 fields are load-bearing? | **For Kshetra: none established. 221 register rows, 221 templated receiving operators, 221 `FUTURE` tests.** The worklist has not been started. | K-E. |

---

## §4 — The `phala_rectification` decision (F12) — ruling proposed: **GUARD, DO NOT GRANT**

The Phase 1 campaign is deliberately holding the four-table grant because it is L3 reading L4 — a
dependency pointing upward. This brief's job is to decide it. **Proposed ruling: refuse the grant
for `phala_rectification`, guard the read, and raise a bounded L1 amendment.** Three independent
grounds, any one of which is sufficient:

**1 — Doctrinal. The read is inadmissible, not merely awkward.** Strategy §6.2 states it directly:
*"Rectification and L5 weight inputs require separately admitted, purpose-compatible immutable
artifacts. An earlier timestamp does not make an event-derived rectification posterior admissible
under the event-free prospective contract."* `phala_rectification` is **event-derived**: the read
selects `lel_fit_score` (`uncertainty.py:189-193`), a fit against the Life Event Log. That σ_T sets
boundary uncertainty → window brackets → prospective forecasts. Granting SELECT would wire observed
outcomes into prospective predictions — the exact leak L3-U09's prospective firewall exists to
prevent. **Granting this would be a firewall breach dressed as a privilege fix.**

**2 — Architectural.** It points upward. L3 does not read L4.

**3 — Mechanical. Nothing needs it.** `compute_sigma_t_days` **already has a complete, honest,
named fallback**: fewer than two usable candidates returns `(DEFAULT_SIGMA_T_DAYS,
"default_120s_assumption")` (`uncertainty.py:170-173`, VERIFIED HERE). The read is an
*enrichment*, not a prerequisite — the function is fully defined without it. And the downstream
robustness dimension reads σ_T from a **different, already-guarded** path
(`kala_field_boundaries`, `writer.py:2231-2251`). Guarding the stage-3 read costs the build
nothing: boundaries are written with the instrumental default, honestly source-tagged, and
`birth_time_robust` computes against a real number instead of `None`.

**The fix (Kshetra-owned, no migration, no grant):** wrap `fetch_sigma_t_days`'s call site in
`stage3_clocks.py:1012` so an inaccessible or empty `phala_rectification` yields
`default_120s_assumption` with an explicit **F06 `unavailable`** state, never a silent pass. The
existing `sigma_t_source` string is already the right carrier.

### 4.1 — Is birth-time uncertainty an L1 fact? **Yes — and specifically a property of the birth *record*, not of any inference about it.**

The native's framing is right and the brief adopts it. Two arguments:

- **Symmetry with σ_A.** The sibling quantity, ayanāṃśa uncertainty, is *already* derived from L1:
  `compute_sigma_a_degrees` reads ≥2 ayanāṃśa longitudes from `chart_facts`
  (`uncertainty.py:110-137`), on the stated grounds that *"the five ayanamshas are a fixed,
  always-available L1 computation for any built chart."* σ_T is the same kind of quantity — input
  precision — and belongs to the same authority.
- **§N.7 item 3.** `DEFAULT_SIGMA_T_DAYS = 120.0/86400.0` (`uncertainty.py:57`) is a
  **wrapper-local constant standing in for a value L1 should supply.** A constant can drift from
  its source; a reference cannot. The recorded birth time (10:43 IST) has a declared precision; that
  precision is a fact about the record.

**The distinction that decides the grant:** L1 birth-time precision is *event-free* — it says how
precisely the time was recorded. `phala_rectification` is a *posterior fitted to observed life
events*. They are different quantities with different admissibility, and only the first may enter
an event-free prospective asset. Collapsing them is what the grant would do.

**Proposed target state** (a bounded upstream amendment returned to its owner per Strategy §3, **not
fabricated in L3, and not authorized by this brief**): L1 declares a birth-time precision fact;
Kshetra reads it; `DEFAULT_SIGMA_T_DAYS` demotes to fallback-of-last-resort carrying F06
`unavailable`. Until that lands, the guard in §4's fix is the correct interim, and it is honest
because it names its own assumption in `sigma_t_source`.

**Also required and separable:** K-6's missing SAVEPOINT around the cohort read
(`writer.py:1754-1770`). The `try/except` catches the privilege error but the ambient transaction is
already aborted, so the next statement fails with a less legible error. The codebase already has
the correct pattern at `ka_sangam.py:997,1028,1033`. **This is a real repair; the `bg_synthetic_cohort`
grant is a separate question this brief does not decide.**

---

## §5 — The null statistic: semantic contract and independent oracle

### 5.1 What `null_p` means — the exact null hypothesis, resolved

Lane C recorded COULD-NOT-VERIFY on whether the shift is circular, reflected or truncated. **Resolved
here from source** (`dhara_null.py:6-45, 90-166`):

> **Holding this chart's natal structure and daśā ladder FIXED, how often does a rigid circular
> re-phasing of the transit stream against that fixed ladder produce a window maximum at least as
> high as the observed one?**

Mechanically: `ln λ_r(t) = C(t) + E((t − δ_r) mod H)`. The shift is **circular** on a **1-day grid**
(n = 36,525) over the 100-year horizon. **Only the transit envelope E is shifted** —
`dhara_null.py:28` is explicit that the natal structure and the daśā ladder are *not*. The grid is
deterministic, **no RNG**: δ_r = r·H/R for r = 1…R−1. Default `coarse_mode=True` evaluates at
MD/AD/PD ladder boundaries only (~819 knots).

### 5.2 The honest denominator, and what the statistic is not

**Denominator: R = 1024 = 1 observation + 1023 circular shifts.** Implemented as
`(1 + exceed)/(len(stats) + 1)` with `len(stats) = R − 1 = 1023`. Resolution 1/R; a p of 1/1024 is
a floor, never zero. **Proposed doctrine fix (K-F):** correct `dhara_null.py:39`'s formula line and
pin one meaning for R across `dhara_null.py`, `contracts.py` and `stage5_null.py`.

**What it is NOT — each to be stamped on the served row, not left to the reader:**

- **Not** empirical event probability, and not a population statement of any kind.
- **Not** a test of the natal structure or of the daśā ladder. Both are held fixed and are therefore
  *untestable by this null*. A low `null_p` says nothing about whether the chart's promise is real.
- **Not** calibrated. Per context §1, it binds to F04 (computed fact, structural prior — not a
  calibrated claim) and must carry a comparability flag: it is **not comparable** with any other
  asset's quantity, in the `tier_basis = 'relative_uncalibrated'` discipline `ka_taranga` already
  applies.
- The ensemble includes physically impossible alignments — a 50-year shift maps age-90 transits onto
  age 40 against a fixed ladder. That is legitimate for a *phase* test and illegitimate as a claim
  about how unusual anything is in the world.

**A falsifiable consequence of this contract, offered as a test of the contract itself:** because
only E is shifted, a class whose λ variation is dominated by `C(t)` — baseline plus promise, both
constant in t — must get **no discriminating power** from this null. `null_p` should be
uninformative for such classes. If it is not, the stated semantics are wrong.

**Scale-invariance (bears directly on §7):** `null_p` compares the window's `expected_count`
against replicate maxima built from the *same* evaluator and the *same* λ⁰. Both sides scale with
λ⁰, so **`null_p` is invariant to a synthetic baseline** — it is honest for shape-only classes,
while `expected_count` in absolute terms is not. `stage8_spec.py:136` already applies exactly this
discipline (`"expected_count": None if window.get("baseline_is_synthetic") else ...`). That is the
existing precedent for Pūrṇa's P3-b census and should be cited to it as the pattern.

### 5.3 The independent oracle

Strategy §5 is explicit that where a method may have a defect, the old output is not the oracle, and
that *"fewer simulations, approximate quantiles or fewer years are not equivalent performance
repairs."* Two things follow, and the first is the useful one:

**The exact null is computable by exhaustive enumeration, and it is cheap.** On a 1-day grid the
full circular shift group has exactly **H = 36,525 elements**. The R=1024 grid is a regular
1023-point *subsample* of an exactly enumerable group. Therefore the oracle for the estimator is
**the exhaustive shift set on a reduced horizon** — compute the complete exceedance distribution
over all integer-day shifts for a short horizon and a synthetic process with known λ, and compare.
This is an independently specified reference calculation in Strategy §5's sense: it does not run
the estimator under test, it *enumerates the thing the estimator samples*. Add one closed-form case
(a pure sinusoidal E against constant C, whose sliding-window-max exceedance under rigid rotation is
analytic) as a second, implementation-independent check.

**A definitional point for the native to pin.** P1's equivalence contract requires the *"full shift
set."* Given the above, "full shift set" must mean **the full declared R-grid**, not the full
36,525-element group. Left unpinned, a P1 implementation could satisfy the phrase two
incompatible ways.

**And the boundary:** A3 (R=128 vs R=1024) is a **cost-sensitivity probe, not an equivalence proof**,
and may not be offered as one. Reducing replicates changes `config_pin` → changes
`field_snapshot_id` → is a different snapshot by the system's own identity rule (K-B).

---

## §6 — Per-family obligations (Strategy §6.2)

Structure that must survive, and the one obligation this brief adds per family. Families are
Strategy §6.2's; nothing here re-scopes them.

| Family | Must survive | Obligation this brief adds |
|---|---|---|
| `kala_field_kinematics` | Trajectories, longitude/velocity, orb/dwell/crossing, convention, resolution | Carry an ayanāṃśa-coverage marker. `ayanamsha_robust` returns `None` below 2 ayanāṃśas (`stage5_null.py:606-624`) — if that is the uniform `weakest_link` (K-D), this family is the cause. |
| `_promise_nodes`, `_promise_edges`, `_routes` | Signed mechanism graph, participants, conductance, source roots | Unchanged (L3-U01). SM-R-7 Option B's route-scoped suppression is the model's strongest structural guarantee — preserve it exactly. |
| `_clocks`, `_boundaries` | Applicability, parent hierarchy, lords, level, exact boundaries, timing uncertainty | **σ_T must carry its `sigma_t_source` to the row.** `default_120s_assumption` and `rectification_posterior_weighted_std` are different epistemic objects (§4) and a boundary may not be silent about which it used. |
| `kala_field` | Segment, alpha/gamma/lambda, integral, contributing term versions | **`baseline_is_synthetic` must land on the row** (K-C) before any 25-class publication. Pūrṇa P3-a owns the code. |
| `_null`, `_windows` | Null scope, duration buckets, p/R, intensity shape, interval, robustness | §5's contract stamped on the row: the fixed-ladder/shifted-transit scope, the R denominator, the non-comparability flag, and `coarse_mode`'s ~819-knot evaluation resolution as declared coverage. |
| `_provenance` | Target/term/weight, source table/row/fact/authority, generation | Unchanged. No first-root loss; all counterevidence recoverable. |
| `_salience`, `kala_insights` | Gain/rank/coverage/omissions, roots, robustness, `lel_derived` | The `lel_derived = FALSE` delete predicate (`_OWNED_TABLES`, `writer.py:2493-2496`) is the cross-layer guard **working**. Never widen it. |
| `kala_timeline_spec`, `_snapshots` | View/config/class coverage, skipped classes, substrate build IDs, complete digest | **Two identities must be distinguished in every statement about this asset:** the *pin* identity (`field_snapshot_id`, computed before any row is written) and the *content* hash (§7.4, recorded with `hashed_tables` in the manifest). The canonical chart has the first and not the second. **That is the precise definition of "unpublished."** A hash-replay comparison is meaningful only between snapshots whose `hashed_tables` agree. |

**Also, unchanged and stated for the record:** the four decomposed hazard terms (K-8) are stored on
every segment and read by no consumer. They are §1.1's entire attribution argument. They are either
the most valuable unexploited signal in L3 or four columns × 8.57M rows of dead weight, and
ablation A2 decides which.

---

## §7 — Disposition

### 7.1 — Recommended: re-scope to the calibrated 6-class configuration and publish it

**What.** Build `ka_kshetra` for the canonical chart over the **six calibrated classes only** —
`childbirth, foreign_settlement, marriage, relocation, separation, surgery`, the classes with a real
`brahma_class_priors` row — through S6 → S6.5 → S8 → **snapshot manifest**.

**Why this and not completion of the 25-class run:**

1. **It is a demonstrated path, not a hoped-for one.** Chart `1c826d5a` has already completed
   exactly this configuration: 6 classes, 2.41M segments, 7,650 salience rows, 415 insights, 6
   timeline specs, **1 manifest row** (F6). The configuration is known to terminate and publish.
2. **It needs no §N.8 waiver.** All six have real baselines. No `baseline_is_synthetic` propagation,
   no absolute-field census, no serve-time suppression — all of which are **Pūrṇa-owned and in
   flight** (P3-a/b), and none of which this brief may pre-empt.
3. **Completing the 25-class run today would publish what §N.8 forbids** — a manifest asserting a
   complete generation over a table where 85.7% of derived windows rest on a fabricated λ⁰ that the
   segment table cannot declare (K-C). Publication is the act that converts a partial artefact into
   an assertion; making that assertion before the tag lands is the defect, not a step toward fixing it.
4. **It reaches a real acceptance state.** A manifest makes `DATA_ACCEPTED` arguable and makes
   `kala_priority_get`'s five-axis salience stop returning `honest_empty` — the only existing
   serving path into the field.
5. **Four of the six are in the alphabetically-last 11** that never reached a window (`marriage`,
   `relocation`, `separation`, `surgery`). The calibrated set is *disproportionately* the part the
   crashed run never finished. Re-scoping does not discard completed work so much as target the work
   that was never done.

**Honest cost of this choice:** the chart is silent on 19 life domains until Pūrṇa's P3 lands. That
is a real loss and the native should weigh it. The brief's position is that **silence that says
"not computed" is worth more than coverage that cannot say whether its level is real** — and that
the silence is temporary by construction, because P3 is already the plan of record.

### 7.2 — The 25-class generation: preserved as substrate, not completed

Its disposition is **HELD**. It is legitimate partial product, it is deterministically addressable
(K-B), and it becomes publishable the moment P3-a threads the tag to `kala_field`. It must not be
completed and published before then. It is **not** parked in the sense of abandoned.

### 7.3 — The preservation act, which is urgent and is not optional under any disposition

Under **all three** dispositions — complete, re-scope, or park — the 8.57M rows are deleted by the
first run whose pin vector differs (K-B), and the §7.1 re-scope *is* such a run, because the class
set is discovered per-chart from `bodha_pratijna` (`writer.py:2395-2400`) and a 6-class build is a
different build. **Therefore preservation must be settled before anything is built.**

Three options, for the native to choose; this brief does not choose among them and none is
self-authorized:

- (a) Accept the loss — the rows are rebuildable projections and "data is disposable" applies
  (context §4). **This is defensible** and may well be right: nothing issued, no outcome and no
  observation rides on them.
- (b) Preserve out-of-band before the build.
- (c) Build the 6-class configuration on a disposable harness first, leaving production untouched.

**The brief's position: (a) is probably correct, but it must be *chosen*, not defaulted into.**
Losing 7.5 hours of compute by surprise is different from spending it deliberately.

### 7.4 — What is explicitly rejected

- **Completing the 25-class generation as-is** — publishes an untagged 85.7%-synthetic assertion.
- **Granting SELECT on `phala_rectification`** — §4.
- **Optimising first, then completing** — mechanically unavailable (K-B).
- **Adding classes, replicates or knots** — nothing reaches a consumer today; Lane C is right that
  this is the lowest-value elevation available.

---

## §8 — P0 / P1 / P2 / P6 sequencing

Strategy §5: *"Repair before any expensive rebuild trial."* Product §1.2: *"Processing speed is
subordinate to depth."*

| Order | Item | Position | Why here |
|---|---|---|---|
| **1** | **P0 (residual)** | **Do now. Zero compute.** | Kshetra's planner-mutation half is already repaired (K-A). What remains is Kshetra-owned and cheap: the §4 σ_T guard (unblocks the build while *refusing* the upward dependency), the K-6 SAVEPOINT, and the §7.3 preservation decision. Bhavishya's P0 half is outside this brief. |
| **2** | **P6 (publication)** | **Second, and before any optimisation.** | Publication is what converts rows into something a consumer can pin, and the pin-hash rule makes it the *only* order that preserves existing capital (K-B). Optimising an unpublishable artefact cannot pay back. Lane C reached this conclusion independently; the pin mechanism is the reason it is not merely a preference. |
| **3** | **The §1.3 ablation** | **Gate. Before P1 is funded.** | The largest cost in the layer is the null programme. Paying for exact-equivalence work on a statistic whose consumer question has never been tested is the error the native's Q1 is guarding against. |
| **4** | **P2 (shared context/sweep)** | After the gate, before P1. | Semantics-preserving and it does not touch the null's statistical contract. Its equivalence contract is checkable without settling §5's oracle. |
| **5** | **P1 (DHARA null)** | Last, and only if the gate passes. | ~4× the cost of everything else, and its equivalence proof depends on §5.3's oracle existing first. |

**One interface obligation runs in parallel and depends on none of the above** — §6.2's
capability packet (L3-U11). It is the item that actually caps the asset (Strategy §7), and it
is Pūrṇa's to implement.

---

## §9 — The §6.4 packet

| Packet field | Content |
|---|---|
| **Input generations** | Eight declared edges: `ka_dasha_kala`, `ka_gochara_resonance`, `ga_panchanga`, `bo_pratijna`, `bo_sangati`, `bo_upaya`, `bg_cohort`, `bg_class_lifetime_counts`. `bg_sky_calendar` deliberately not an edge (W3 staging); `mi_bhara` deliberately not an edge (acyclicity). **Under generation binding (context §3, native decision 1 open): bind one compatible transitive vector, no `public` fall-through.** Measured live 2026-09-22: zero L1/L2 generation heads exist, so **today the only available binding is the pin vector** — `corpus_pin` + `weights_version` + `x_schema_version` + `config_pin` (`stage4_field.py:186-212`). **If decision 1 goes the other way, the pin vector remains the identity and nothing in this brief changes;** if it goes for generations, the generation id joins `config_pin` and every existing snapshot id is superseded by construction. |
| **Field-level transformations** | `ln λ_e(t) = ln λ⁰_e + ln P̃_e + Σ w_s·A_s·r_{s,e}(t) + Σ β_j·x_j(t) + Σ ln(1 − ρ_m·u_m(t))` (`layer1.py:22-30`, impl. `:60-165`). Four terms persisted per segment. **One transformation changes: `baseline_is_synthetic` must survive from `hazard.baseline_rate` to the row (K-C) — Pūrṇa P3-a's code, this brief's precondition for 25-class publication.** |
| **Preserve / change / reuse** | **Preserve:** the term decomposition (§1.1); SM-R-7 route-scoped suppression; the exemplary `brahma_class_priors` selection (`stage4_field.py:1155-1168`, four coordinates pinned, total `ORDER BY`, `LIMIT 1` — §N.7 item 2 done right, and the pattern to cite to every other L3 writer); `temporal_shape` read-never-derived (`:1178-1188`); the `lel_derived = FALSE` delete predicate; the five §N.8 `None`-returning robustness detectors. **Change:** the σ_T read → guarded (§4); the cohort read → SAVEPOINT; `dhara_null.py:39`'s denominator prose (K-F). **Reuse:** the whole S0–S8 DAG and the resume machinery unchanged — **no orchestrator contract change is proposed or needed (§N.2).** |
| **Method qualification** | λ is a **structural prior, not a calibrated claim** (F04). λ⁰ is actuarial, not classical, and is calibrated for 6 of 25 classes only. The clock term is the classical operand; its graded, depth-discounted continuity is a declared departure from categorical daśā judgment. The noisy-OR promise combination is a declared departure. `null_p` per §5. **Comparability: NOT comparable with any other L3 asset's quantity.** |
| **Output keys / partitions** | `kala_field`: `(chart_id, event_class, segment_index)`, `t` in days-from-birth over 0…36,525. Fifteen writer-owned relations (`_OWNED_TABLES`). Publication identity `field_snapshot_id` (pin hash); content identity = §7.4 hash over the stage 0–8 row set excluding `lel_derived = TRUE`, recorded with `hashed_tables`. |
| **Source and data checks** | Manifest exists for the built pin vector; `hashed_tables` recorded; no segment references a snapshot id without a manifest row (the F4 invariant, currently violated); segment contiguity (gaps = 0 over the full horizon); `sigma_t_source` present on every boundary; `baseline_is_synthetic` present on every field row before any synthetic-class publication; `weakest_link` distribution non-degenerate **or** its single cause named (K-D). |
| **Consumer effects** | Today: `mi_bhara` (only substantive machine consumer); `kala_priority_get` (honest_empty, starved); `kala_explain_get` (window slice). **Zero retrieval capabilities over any `kala_field*` table** — the cap under Strategy §7. On the §7.1 disposition, `kala_priority_get` stops returning `honest_empty`. |
| **Benchmark target** | **None statable. Deliberately.** `asset_registry.estimated_seconds = 237` is **retired** (F28: no detector behind it → null); the measured ~7.5 h is a 114× divergence. The measured figure is **one unrepeated run**, reconstructed from `computed_at` spans, on a run that **crashed** (`worker_crash: OperationalError: the connection is lost`, 2026-09-11) as `amjis_app` under a 600 s idle-in-transaction killer, a week before the identity cutover — **a plausible but unreproduced cause, which must not be recorded as diagnosed.** It satisfies none of Strategy §5's benchmark contract (repeated matched runs, spread, hardware/ephemeris/version capture, cold/warm/resume/horizon-extension/upstream-correction workloads). **The benchmark target binds to `KALA_COST_PROFILE_v1_0.md`, which does not exist yet** (verified: absent from the tree and from git history). Until it lands, this asset states no cost target, and no P1/P2 saving may be claimed against one. |
| **History / rollback contract** | Kshetra owns only `kala_insights.lel_derived = false`; `mi_bhara` owns `true`. The cross-layer delete guard **must not be disabled** and its refusal is the protection working. `_delete_prior_rows` is scoped per-table with predicates. **Rollback gap:** nothing verified here prevents a late worker publishing over a newer accepted generation (§3 ruling 6) — an open obligation, not a solved one. Preservation of the 8.57M rows is §7.3's decision. |
| **Independent reviewer** | **UNASSIGNED.** §11. |

---

## §10 — Staged acceptance and `Accepted N/22`

**Proposed ruling: `Accepted N/22` counts `ka_kshetra` as ONE terminal asset. Stages are work
units, not acceptance units.**

- The snapshot manifest is all-or-nothing **by design** (§6.2's last row), and it is the asset's
  only publication identity. A "stage-accepted, unpublished" field has no meaning to a consumer —
  Strategy's own prerequisite line says *"a partially completed stage set cannot be selected as a
  complete snapshot."*
- Per-stage acceptance would let an asset accrue credit while remaining unconsumable, which is
  exactly the presence-is-value error the ladder exists to prevent.
- Internal staging is still real and is used for **work sequencing and resume** (the W2–W7 internal
  DAG), which the resume machinery already implements correctly.

**Consequence the native should accept explicitly:** on the §7.1 disposition, a published 6-class
snapshot makes Kshetra countable at `DATA_ACCEPTED` **for the 6-class configuration**, and the
asset's record must say so in those words — *not* "ka_kshetra accepted". The configuration is part
of the acceptance claim, because F6 establishes that configurations, not runs, are what differ here.

---

## §11 — What is not settled

1. **Q1 itself.** Whether the continuous-field model is worth preserving is **not** decided by this
   brief. §1.3's ablation decides it.
2. **The `weakest_link` distribution** (K-D). One aggregate query. Not run — no DB access this
   session.
3. **Ablation A1** (within-class rank invariance under a synthetic baseline). One aggregate query,
   the highest information-per-cost test on this asset. Named by Lane C, still not run.
4. **`refinement_depth` is 0 on all 8.57M rows** (K-5). Correct-and-dormant vs disabled-path is
   indistinguishable from the data, and the trigger was not read here.
5. **Late-worker publication protection.** Asserted as an obligation; no mechanism verified.
6. **The 25-vs-27 class question.** The class set is discovered per-chart from `bodha_pratijna`
   (`writer.py:2395-2400`), so 25 is this chart's promise coverage, not a configured constant —
   while Pūrṇa targets 27. Whether the gap is ontology coverage or promise coverage needs one query;
   **not asserted here.**
7. **The 2026-09-11 crash cause** — plausible, unreproduced, and recorded as unreproduced.
8. **Every live figure in this brief** is Lane C's. The DB was unreachable
   (`ECONNREFUSED 127.0.0.1:5433`). None was independently re-confirmed.
9. **The independent reviewer is unassigned.** The §6.4 packet is incomplete without one, and this
   brief cannot appoint its own reviewer.
10. **P0's Bhavishya half** — outside scope, examined by nobody in this brief.

## §12 — Live-path statement (context §7)

Hazards asserted here and whether a live path reaches them **today**:

- **F12 / §4 (σ_T unguarded read):** **live and blocking.** Stage 3 is on the mandatory substep
  path; the build hard-fails there.
- **K-B (delete on pin change):** **live**, and reached by the *first* build of any changed
  configuration — including the one §7.1 recommends.
- **K-C (tag discarded):** **live** on every field row written.
- **K-E (no receiving operator):** **live** — confirmed by directory listing; no capability exists.
- **K-6 (missing SAVEPOINT):** live only when the cohort read raises; `data_plane_builder` cannot
  SELECT those tables, so it raises.
- **K-F (denominator prose):** **documentation only.** The implemented arithmetic is correct. Not a
  data defect, and this brief does not inflate it into one.
- **`S5.null_resolution`'s 1/(R+1):** **no live caller found within scope** — `grep` over
  `services/ka_kshetra/*.py`; the writer binds the corrected `null_result.resolution`.
