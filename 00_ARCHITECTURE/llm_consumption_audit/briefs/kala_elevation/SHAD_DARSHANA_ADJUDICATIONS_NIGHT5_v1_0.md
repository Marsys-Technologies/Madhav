---
artifact: SHAD_DARSHANA_ADJUDICATIONS_NIGHT5
version: 1.0
status: LIVE — ANTARYĀMIN rulings, Night 5 (2026-08-02); native may overrule any ruling at
  morning review; reversibility noted per ruling
campaign: ṢAḌ-DARŚANA
adjudicator: ANTARYĀMIN (Opus), per SHAD_DARSHANA_NIGHT_RUN_v1_0.md §A
predecessor: SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md (rulings -2 … -13 + §NATIVE CONFIRMATIONS)
---

# ṢAḌ-DARŚANA — Night-5 adjudications

Both rulings below were issued at session open (session-open protocol step (c)) to unblock
the W2G writer lane before any builder could stall on them. ANTARYĀMIN read the design doc
(`GOCHARA_SWEEP_2_0_DESIGN_v1_0.md`), the V1–V6 validation source, the Night-3 precedent, and
migration 527, and took its own read-only measurements against live production — the numbers
below are measured, not restated.

---

## ADJUDICATION-14 — V4: the §2.3 design-band re-scope (eager/lazy tiering)

**QUESTION.** V4 measured ~7.8×10⁵ chart-specific contact events over 1984–2084 × 9 bodies
against design §2.3's asserted 10k–100k band; even the "everything except Moon" split
(~1.9×10⁵) exceeds the band. What does the 2.0 writer eagerly materialize, and what does the
band become?

**MEASUREMENTS** (live prod, read-only, 2026-08-02; V4's own formula
`n_targets × Σ crossings_per_fixed_degree × 3`, crossings derived from measured total angular
variation ÷ 360 in `ephemeris_daily`, `ayanamsha_id='tropical'`, 1984-01-01→2084-12-31):

| body | crossings/fixed° | body | crossings/fixed° |
|---|---|---|---|
| Moon | 1350.22 | Mars | 57.88 |
| Mercury | 124.71 | Jupiter | 13.65 |
| Venus | 106.68 | Saturn | 7.06 |
| Sun | 101.00 | Rahu / Ketu | 6.08 each |

All nine = **1773.36**. `gochara_resonance_map` targets: native `482012f1` = 148, Abhinandan
`1c826d5a` = 145, Kiran `cb73cd3d` = 77. Native all-nine = 787,372 events (V4 recorded
779,595 — small epoch-boundary difference, same order). Moon share = 76.1%, reproducing V4's
recorded 76%. `kala_gochara_windows` today: 19,073 rows / 59 MB incl. indexes = **3,235
B/row measured**; native's v1 century = 8,345 rows. The decisive fact V4 did not surface:
the residual "eager" mass is NOT the slow bodies — Sun+Mercury+Venus = 332.39 of the 423.14
non-Moon crossings (**78.6% of the eager layer**); the genuinely slow set (Jupiter, Saturn,
Rahu, Ketu) is 32.87, i.e. **1.85% of the total**.

**OPTIONS.** (a) amend the band upward to ~8×10⁵ — REJECTED: 262,457 window rows × 3,235 B ≈
849 MB/chart (32× v1), materializing ~16 Moon contact events per chart-day that nothing
downstream reads at that resolution (day-grade-first rail) — an honesty argument, not merely
storage. (b) restructure the eager/lazy split — **TAKEN**. (c) reduce bodies/classes for v1
of 2.0 — REJECTED as unnecessary: nothing is dropped under (b), only re-tiered (reversible),
whereas dropping is a doctrine amputation §5 forbids.

**RULING — (b), as a THREE-TIER split, which is what design §2.5 actually says and V4's
implementation collapsed into two** (`v4_transition_sizing.py`'s
`LAZY_LAYER_BODIES = {"Moon"}` merged tiers A and B):

- **TIER A — EAGER, full-span, materialized: Saturn, Jupiter, Rahu, Ketu, Mars.** Σ = 90.75.
  Native = 40,293 contact events / 13,431 window rows; Abhinandan 39,476; Kiran 20,963 —
  every v1-corpus chart lands INSIDE the existing 10k–100k band, unamended. **Mars is ruled
  INTO Tier A explicitly**: §2.5's "Jupiter…Ketu" leaves Mars unassigned (a real design gap);
  Mars gochara is load-bearing classically; at 57.88 it costs 1.8× the whole slow set while
  keeping the tier in band.
- **TIER B — CONDITIONALLY MATERIALIZED: Sun, Mercury, Venus.** Σ = 332.39 (147,581 events
  full-span — the thing that broke the band). Solved and persisted only inside intervals
  Tier A already elevates, plus unconditionally at their own station/retro-loop boundaries.
  Doctrinal cover: the Sun's sankrānti/nakshatra ingresses are already in the
  chart-independent global calendar (§2.2) at zero per-chart cost — Tier B defers only
  chart-specific degree contacts.
- **TIER C — LAZY, on demand only: Moon (+ lagna-scale).** 599,498 events full-span; never
  materialized across the horizon. Election/drill-down solves it inside a bounded request
  window and caches.

**Amended §2.3 band text (for the W2G lane's PR):** replace the single "tens of thousands"
claim with a per-tier budget plus stated ceiling — Tier A eager budget: 10,000–100,000
contact events per chart per century (the original band, which HOLDS as measured: 40,293 /
39,476 / 20,963). Tier B on-demand ceiling ≈1.5×10⁵; Tier C ceiling ≈6×10⁵; full nine-body
enumeration ≈7.9×10⁵ / ~849 MB per chart — recorded as a measured ceiling, explicitly NOT a
materialization target. The "1–3× per cycle" multiplier is WITHDRAWN: retrograde
re-crossings are counted by measured total angular variation, per V4.

**Projections a builder can use:** Tier A ≈ 13,431 rows × 3,235 B ≈ 43 MB/chart (1.61× v1's
8,345 rows); peak during dual-generation ≈ 70 MB/chart (2.0 writes beside v1, ADJ-6 /
migration 527). Build time is NOT the binding constraint (at §2.3's own millisecond
root-find assumption, Tier A ≈ 40 s/chart; V3's measured 0.314″ worst spline error with 1.0″
tolerance bounds iterations). Binding constraints: storage, serving density (§N.6), and the
day-grade-first rail.

**Honesty requirement carried by this ruling (§N.8):** a Tier-B/C row's absence must be
machine-distinguishable from "no event occurred" — 2.0 rows carry `generation` plus a
tier/materialization marker, and an empty read returns an explicit reason (e.g.
`tier_b_not_materialized`), never a silently-thin envelope.

**RATIONALE.** Design §2.5 (three rates, verbatim) · §2.3 (sizing claim under amendment) ·
§2.2 (global calendar carries Sun ingresses free) · §5 (no doctrine dropped — re-tiering is
not amputation) · §3.1–3.2 (Tier A vs v1's daily grid is exactly where the equivalence
corpus is comparable; Tier C is where class-(b) Moon-undersampling divergences appear, so
deferring it localizes rather than weakens the finding). Rails: day-grade-first;
`kala_gochara_windows` untouchable; strangler.

**REVERSIBILITY: HIGH.** Promoting Tier B (or C) to eager is a config change plus a backfill
run under the same `generation`, gated by the same ADJ-6 pointer; no schema change, no v1
row touched, no orchestrator change. Nothing is deleted by tiering — no evidence is
destroyed by getting a tier wrong.

---

## ADJUDICATION-15 — V1: the minimal per-phase instrumentation contract

**QUESTION.** V1 is INDETERMINATE because no table carries per-phase timing for the sweep —
"what fraction of cost does 2.0 eliminate" is unmeasurable. What must the 2.0 writer ship?

**OPTIONS.** (a) new orchestrator telemetry surface / `_telemetry` — forbidden outright by
FROZEN contract §N.2, not adjudicable. (b) new standalone profiling table — rejected: a
second build-state ledger to keep consistent, for a descriptive number. (c) logging only —
rejected: unqueryable across runs, V1 stays INDETERMINATE forever. (d) logging + an additive
nullable column on the ledger the writer already upserts — **TAKEN**.

**RULING — (d).** Structured log line + one additive nullable `jsonb` column named
`phase_profile` on `build_substep_progress`, written by the 2.0 writer inside its own
existing upsert. Verified this needs NO contract change: heavy writers already upsert
`build_substep_progress` themselves on `ctx.db_conn` inside the orchestrator-owned
transaction (`services/ka_gochara_sweep/writer.py:656`, `services/ka_kshetra/writer.py:825`,
`writers/ka_sangam.py:510`) — the 2.0 writer adds columns to a statement it already issues.
No orchestrator surface, no `asset_throughput` write, no `_telemetry`, no commit.

**What is measured — a FIXED phase enum, every key present in every row:** `spline_eval` ·
`event_solve` · `interval_assembly` · `lambda_integration` · `row_write` · `other`. Per
phase: `seconds` (monotonic clock) and one item count (`n_spline_evals`, `n_root_finds`,
`n_intervals`, `n_lambda_segments`, `n_rows`). Plus `substep_wall_seconds` and `tier`
(A/B/C, per ADJ-14) so the profile answers the tiering question directly.
`sum(phase seconds) + other ≈ substep_wall_seconds` is an invariant the lane asserts in test.

**Earned-signal discipline (§N.8, non-negotiable):** a phase that did not run records `0.0`
explicitly — a MISSING key always means instrumentation is broken, never "that phase was
fast"; the two must never be confusable. The profile is descriptive, never a gate (§N.4):
no build fails on a timing number.

**Deliberate bonus:** `_PHASE_TIMING_COLUMN_HINTS` in `v1_profile_split.py` already contains
`"phase_profile"` — naming the column makes V1's existing, unmodified detector fire (the
detector predates the column, so this is not moving goalposts). V1 converts from
INDETERMINATE to a real measurement with zero edits to the validation.

**Scope note:** instruments the 2.0 writer ONLY. Retro-instrumenting v1 is explicitly NOT
ordered — v1 is a strangler-retired artifact; V1's intent (what fraction 2.0 eliminates) is
answerable from 2.0's own phase split against v1's already-available aggregate
inter-commit wall-clock, with the aggregate's caveats (`DISPATCH_GAP_SECONDS`, orchestrator
overhead) carried forward, not hidden.

**RATIONALE.** CLAUDE.md §N.2 (FROZEN) · migration 436 comment (the ledger is
writer-upserted inside the orchestrator-owned per-substep transaction — the enabling fact) ·
design §6 V1 · §N.8 · §N.4.

**REVERSIBILITY: TOTAL.** One nullable additive column; `DROP COLUMN` restores the prior
state exactly; every existing reader ignores it.

---

*Neither ruling alters a FROZEN contract, an untouchable, or a campaign rail. Transcribed by
the Conductor from ANTARYĀMIN's session-open ruling pass, Night 5 (2026-08-02). The §2.3/§2.5
design-doc amendment is the W2G writer lane's PR to make, wording supplied in ADJ-14.*
