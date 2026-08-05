---
artifact: SHAD_DARSHANA_ADJUDICATION_18_SWEEP_OPTIMIZER_ENGINE_BOUNDARY
canonical_id: SHAD_DARSHANA_ADJUDICATION_18_SWEEP_OPTIMIZER_ENGINE_BOUNDARY
version: 1.0
status: RULED — native ruling, relayed and recorded verbatim by the Conductor (SESSION-B-BUILD)
created: 2026-08-04
author: Native ruling; transcribed by the Conductor
governing: BRIEF_D5.md §7 (superseded scope, see below) · SHAD_DARSHANA_STATE.md SESSION-B-BUILD
  lane (a)
---

# ADJUDICATION-18 — the D-5 §7 boundary, and the sweep-optimizer's true scope

## The question

`ka_gochara_sweep` (G-4, D-5 wave) is the writer lane (a) SESSION-B-BUILD directive asks to be
optimized. Investigation (Conductor, foreground, 2026-08-04) traced the actual per-day hot loop:

- `writer.py`'s `run_substep` → `sweep.sweep_event_class_chunk` → `engine.compute_lambda_e_series`
  (`services/gochara_intensity/engine.py:182-218`) — the real `while t <= t_end_jd:` loop,
  calling `compute_lambda_e` (same file, `:95-179`) once per grid day.
- `compute_lambda_e` calls `compute_permission` (`permission.py`) and
  `gather_configuration_sentences` (`configuration_activity.py:54-95`) per day. The latter's own
  docstring records a LIVE-PROFILED finding: all 9 contact primitives cost ~110-120ms per
  (target, 10-day-window) call regardless of DB touch — real, measured, pre-existing evidence for
  the redundancy this lane targets.
- Those primitives (`gochara_grammar/primitives.py`, G-2) delegate ALL ephemeris scanning to
  `pipeline.transit_search` (per that file's own docstring, line ~8-12) — a SHARED,
  non-G-lane-owned platform utility, not part of any G-1..G-5 package.

None of this redundant work lives inside `ka_gochara_sweep` (G-4) itself. It lives in G-3
(`gochara_intensity/`) and G-2 (`gochara_grammar/primitives.py`), both of which
`BRIEF_D5.md §7`'s **must_not_touch** clause named explicitly: *"prior gate surfaces... G-lanes
CONSUME these, never modify them; if a lane finds a bug in prior-wave code, it reports to the
Binder, it does not patch across the boundary."*

## The ruling

**The RULE-AS-MACHINERY (scope-warden enforcement, report-to-Binder) was D-5 wave-coordination
hygiene and expired with D-5's close** (the Binder it names no longer exists; L3 Kāla is sealed).

**What SURVIVES is the narrower durable principle underneath it: a downstream consumer must
never change an upstream engine's SEMANTICS or AUTHORITY.** Performance-transparent change is a
different category — the test is not "which file" but "is the output provably unchanged."

**Approved, exactly as shaped:**
- `compute_lambda_e_series`/`compute_lambda_e` gain an OPTIONAL precomputed-kinematics-cache
  parameter. Default = absent = current behavior, byte-for-byte, for every existing caller.
  `ka_gochara_sweep` builds the cache once per year and passes it; no other caller changes.
- The cache carries ONLY chart-independent, class-independent kinematics (per-day positions,
  velocities, aspect geometry). Nothing event-class-specific ever enters it — that separation IS
  the boundary principle, now enforced by a type signature instead of a wave rule.
- ZERO formula changes inside `compute_lambda_e` beyond consuming the cache: no constants, no
  branch-logic edits, no reordering that alters float accumulation.

**Scoping note the ruling's literal text names only `engine.py`'s two functions; the investigation
above found the actual expensive calls one and two layers deeper** (`primitives.py`'s
delegation to `pipeline.transit_search`). For the cache to have real effect, it must be threaded
(or the equivalent memoization achieved) all the way down to wherever `transit_search`'s
ephemeris calls happen — the SAME "is the output provably unchanged" test extends by direct
analogy to that deeper plumbing; this adjudication treats that extension as already covered by
the ruling's own stated principle, not a separate open question requiring a second ruling. If the
builder's own investigation finds a materially different shape at that layer, it should still
stop and report rather than assume — same discipline as everywhere else in this campaign.

**Guards, mandatory, in this order:**
1. Internal A/B first, cheap: engine WITH cache vs. engine WITHOUT cache, identical outputs on
   sampled (event_class, year) slices, BOTH canonical charts. Proves the parameter is truly
   transparent before any corpus comparison.
2. The standing acceptance, unchanged: optimized writer vs. the ~600 completed production
   substeps, byte-equivalence per the lane's original spec. 100% or no switch.

DB-round-trip batching (the primitive-call-overhead half, `configuration_activity.py`'s own
documented ~110-120ms/call finding) is permitted under the SAME regime, as a SECOND phase,
proven by the same two guards independently — a failure isolates cleanly to one change.

## Reversibility

Total. The new parameter is optional and additive; removing it (or never wiring the cache) costs
nothing — every existing call site is unaffected by construction, per guard 1.

## Does this touch a FROZEN contract / untouchable / rail?

No. `WriterBase`/orchestrator contract untouched. This is a signature-additive change to two
G-3 functions and (by extension, per this ruling) whatever G-2/shared-utility plumbing the
kinematics cache needs to reach — not the orchestrator, not `plan_substeps`/`run_substep`'s own
shape, not any migration/schema.

## The echo, recorded per the native's instruction

"The hot loop lives in a shared engine another wave owns" is precisely the architectural smell
W2G's global-tables design (lane (b), this session) exists to eliminate — chart-independent
kinematics computed once, shared, rather than re-derived per consumer. This optimization is the
bridge; W2G remains the destination.
