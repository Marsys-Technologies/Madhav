---
artifact: WP7_PACKET_T1
packet_id: T-1
version: "1.1"
status: DESIGN_ONLY_NOT_IMPLEMENTED
date: 2026-09-23
owner: "Owner of platform/python-sidecar/services/kala_trigger/trigger.py (+ scripts/kala_admission/currents.py)"
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §6.2 T-1; §6.1 F-25 rows; §10 ecosystem row
authority_note: "Owed to its owner. Call sites verified at this checkout: trigger.py:87 (duck-type contract), :96 (:_malefic_transit_over_mechanism), :150 (:_papa_kartari_sandwich), :199 (guru_shani_double_transit); currents.py:56-59 (live-engine requirement)."
---

# T-1 — kala_trigger: is `find_episodes` worth adopting for the per-window fan-out?

## The note to the owner

Your three suppressive/additive currents (`_malefic_transit_over_mechanism` at
`trigger.py:96`, `_papa_kartari_sandwich` at `:150`, `guru_shani_double_transit` at
`:199`) each fan `find_aspects` out **per malefic × per window** — the malefic loop at
`:94` runs Saturn, Mars, Rahu, Ketu separately per window, and `_papa_kartari_sandwich`
doubles that with a before/after target pair (`:143-148`), so one window costs up to
8+ separate ephemeris-search calls; packet S-1's `find_episodes(chart_id, targets,
horizon)` solves all (body × target × relation) contacts in **one batched call** over
prebuilt arcs and returns them with grain, coverage, and `contact_id`, which is
strictly less per-window fan-out. **The WP4 measured evidence is now in hand
(`WP4_DECOMPOSED_COMPARISON_v1_0.md`, workload WP4-SYNTH-1) — with an honest scope
limit, stated below:**

**What WP4 measured (kernel side, synthetic 2-body × 2-year workload):** one batched
solve covered the whole (body × target × relation) matrix — 4 search-matrix cells and
1 era window for the entire horizon — in 0.000619 s cold / 0.000617 s warm, with
end-to-end kernel cold at 0.002117 s. That is the batched side's shape and cost:
**one call per (chart, horizon)**, not per window.

**What WP4 did not measure:** the trigger-side `find_aspects` call count and
`compute_trigger_currents()` wall time were **not instrumented** — `trigger.py` is
outside this family's may_touch, and WP4's mandate was the decomposed legacy-vs-kernel
comparison, not trigger instrumentation. Rows (i) and (iii) of the measurement table
below therefore remain open.

**Recommendation on the evidence in hand:** the batched `find_episodes` shape is
measurably one-call-per-horizon and sub-millisecond at prototype scale, so adoption is
*likely* a strict win for your fan-out — but the decision stays evidence-gated: the
trigger-side numbers (i, iii) and the per-current score-equality gate must be produced
before adopting, per plan §6.2 ("either way the choice is recorded and §10's ecosystem
row proves both callers still run"). Until then the safe and correct default is: **do
nothing** — S-1 guarantees your duck-typed call sites keep working unchanged; adoption
is an optimization you make with evidence, not a migration you absorb blind.

## Measurement status (post-WP4, 2026-09-23)

| quantity | how to measure | status |
|---|---|---|
| find_aspects calls per window | instrument the `_MALEFICS` loop (`:94`) × before/after pair (`:143-148`) over the synthetic workload; report mean/max per window and per `compute_trigger_currents()` call | **open** — trigger.py outside may_touch; not instrumented |
| episode batching | one `find_episodes` call per (chart, horizon) covering all four malefics + both kartari targets | **measured** (kernel side): 4 search-matrix cells, 1 era window, one batched solve for the whole horizon — WP4 §3 |
| wall-time delta | `compute_trigger_currents()` end-to-end, cold and warm, both paths, same workload | **partial** — kernel side measured (search 0.00062 s, end-to-end cold 0.00212 s); trigger side open |
| correctness gate | per-current score equality within declared ε between the two paths on every fixture window — a number change is a defect, not a speedup | **open** — gate for the adoption decision |

## What this packet does NOT do

- It does not change `trigger.py` or `currents.py` (both are outside this family's
  may_touch; S-1 is designed so no change is *required*).
- It does not pre-commit the adoption decision — T-1 is evidence-gated on WP4 by design.
- It does not touch `find_aspects` semantics; the shape-compat guarantee is S-1's.
