---
artifact: WP7_PACKET_T1
packet_id: T-1
version: "1.0"
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
strictly less per-window fan-out. **However, the measured comparison that would let you
decide — calls per window today vs batched episodes under your real trigger workload —
is produced by this family's WP4 and is not yet in hand:**

> **[WP4 NUMBERS PENDING — parent run fills this after WP4 with the measured fan-out comparison]**

When the parent run lands the WP4 numbers, this paragraph is replaced by: (i) measured
`find_aspects` calls per trigger window on the pre-declared synthetic workload (count
the `:94` and `:143-148` loops instrumented); (ii) measured `find_episodes` batch
count for the same workload (one call per window, or one per chart-horizon if you hoist
it); (iii) wall-time delta per `compute_trigger_currents()` invocation, cold and warm;
(iv) the recommendation — adopt `find_episodes`, or stay on the shape-compatible
`find_aspects` — with the numbers as evidence, per plan §6.2 ("either way the choice is
recorded and §10's ecosystem row proves both callers still run"). Until then the safe
and correct default is: **do nothing** — S-1 guarantees your duck-typed call sites keep
working unchanged; adoption is an optimization you make with evidence, not a migration
you absorb blind.

## What to measure (structure, so the WP4 numbers slot in)

| quantity | how to measure | where it lands |
|---|---|---|
| find_aspects calls per window | instrument the `_MALEFICS` loop (`:94`) × before/after pair (`:143-148`) over the synthetic workload; report mean/max per window and per `compute_trigger_currents()` call | row (i) |
| episode batching | one `find_episodes` call per (chart, horizon) covering all four malefics + both kartari targets; report calls per chart-run | row (ii) |
| wall-time delta | `compute_trigger_currents()` end-to-end, cold and warm, both paths, same workload | row (iii) |
| correctness gate | per-current score equality within declared ε between the two paths on every fixture window — a number change is a defect, not a speedup | gate for (iv) |

## What this packet does NOT do

- It does not change `trigger.py` or `currents.py` (both are outside this family's
  may_touch; S-1 is designed so no change is *required*).
- It does not pre-commit the adoption decision — T-1 is evidence-gated on WP4 by design.
- It does not touch `find_aspects` semantics; the shape-compat guarantee is S-1's.
