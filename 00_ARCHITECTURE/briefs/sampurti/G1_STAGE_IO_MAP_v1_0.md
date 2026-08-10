---
artifact: G1_STAGE_IO_MAP
version: 1.0
status: CURRENT
campaign: SAMPŪRTI
mandate: PA-0 (MASTER_PLAN_v1_0.md §REVIEW-PASS AMENDMENTS)
author: SAMPŪRTI-CONDUCTOR-2026-08-10-R4
date: 2026-08-10
---

# ka_kshetra Stage I/O Map — PA-0 Compliance Artifact

PA-0 mandated this map as a mandatory first step for G1:
> "a STAGE I/O MAP — which of stages 0–3 reads/writes which lead table
> (kinematics/envelopes/routes/clocks/boundaries) — wiring order derived from
> the map, never assumed."

This document records the verified I/O contract for each stage, the correct
dispatch order derived from those dependencies, and confirmation that
`ka_kshetra/writer.py` implements the correct order.

---

## Stage I/O Table

| Stage | Name | Reads (kala_field_*) | Also Reads | Writes (kala_field_*) |
|-------|------|----------------------|------------|----------------------|
| 0 | kinematics | — | contact dwell data, event schema | `kala_field_kinematics` |
| 2 | promise | — | `bodha_cgm_nodes/edges`, `bodha_pratijna`, `bodha_msr_signals` (L2) | `kala_field_promise_nodes`, `kala_field_promise_edges`, `kala_field_routes` |
| 3 | clocks | `kala_field_routes` (stage2), `kala_field_kinematics` (stage0) | `chart_facts`, `chart_dashas`, `brahma_dasha_systems`, `ephemeris` | `kala_field_clocks`, `kala_field_boundaries` |
| 1 | symbolization | `kala_field_kinematics` (stage0), `kala_field_boundaries` (stage3) | — | `kala_field_primitives` |
| 4 | field/windows | `kala_field_primitives` (stage1), `kala_field_routes` (stage2), `kala_field_clocks` (stage3), `kala_field_boundaries` (stage3) | `kala_field_weight_versions`, `kala_field_weights` | `kala_field_windows`, `kala_field_snapshots` |

---

## Dependency Graph

```
                  ┌─ bodha_cgm_*, bodha_pratijna, bodha_msr_signals (L2)
                  │
[stage2:promise] ─┘ → kala_field_routes
                              │
[stage0:kinematics] ──────────┤──→ kala_field_kinematics
                              │              │
                              ▼              │
                   [stage3:clocks] ──────────┘
                      (reads routes + kinematics)
                              │
                              ▼
                  kala_field_clocks, kala_field_boundaries
                              │
                              ▼
               [stage1:symbolization]  ← also reads kala_field_kinematics
                              │
                              ▼
                  kala_field_primitives
                              │
         ┌────────────────────┼──────────────────────────┐
         │                    │                          │
    (routes)            (clocks/boundaries)          (primitives)
         └────────────────────┴──────────────────────────┘
                              │
                              ▼
                   [stage4:field/windows]
                              │
                              ▼
              kala_field_windows, kala_field_snapshots
```

---

## Correct Dispatch Order

**Derived from the dependency graph:**

```
stage0 + stage2   (parallelizable — no mutual dependency)
    → stage3      (reads stage0's kinematics + stage2's routes)
    → stage1      (reads stage0's kinematics + stage3's boundaries)
    → stage4      (reads stage1/2/3 outputs)
```

Linear order: **0 → 2 → 3 → 1 → 4**

**NOTE:** The naive sequential order `0 → 1 → 2 → 3 → 4` is WRONG. Stage 1
reads `kala_field_boundaries` which stage 3 writes. Running stage 1 before
stage 3 would read empty or stale boundaries, causing silent data defects in
`kala_field_primitives` and corrupting the stage 4 hazard computation.

---

## Verification: writer.py Dispatch Order

**Source:** `platform/python-sidecar/services/ka_kshetra/writer.py` lines 333–336

```python
('services.ka_kshetra.stage0_kinematics', 'plan_substeps'),
('services.ka_kshetra.stage2_promise',    'plan_substeps'),
('services.ka_kshetra.stage3_clocks',     'plan_substeps'),
('services.ka_kshetra.stage1_symbolization', 'plan_substeps'),
```

The writer dispatches stages in order: **0 → 2 → 3 → 1**. Stage 4 substeps
are then the main per-event-class substep loop. This matches the dependency
graph exactly.

**CONFIRMED:** The G1 wiring fix (L1b/L1c/L1d, PRs #1150/#1153/#1158) implements
the correct stage dispatch order. Stage 1 runs AFTER stage 3 in the orchestrator.

---

## Key Cross-Dependency: Stage 1 reads Stage 3 Output

`stage1_symbolization.py` docstring confirms (line 600):
> "Reads kala_field_kinematics (stage0) and kala_field_boundaries (stage3)"

The cross-stage dependency is **intentional**: stage 1's envelope construction
for `kala_field_primitives` incorporates the precision-tier information from
`kala_field_boundaries` (the dasha boundary table produced by stage 3's clock
derivation). This is what makes the primitive's precision-tier labeling accurate.

---

## Stage-to-Lead-Table Summary

| Lead table | Written by | Read by |
|-----------|------------|---------|
| `kala_field_kinematics` | stage0 | stage1, stage3 |
| `kala_field_routes` | stage2 | stage3, stage4 |
| `kala_field_promise_nodes` | stage2 | (structural, for provenance) |
| `kala_field_promise_edges` | stage2 | (structural, for provenance) |
| `kala_field_clocks` | stage3 | stage4 |
| `kala_field_boundaries` | stage3 | stage1, stage4 |
| `kala_field_primitives` | stage1 | stage4 |
| `kala_field_windows` | stage4 | P-G1 proof queries |
| `kala_field_snapshots` | stage4 | P-G1 proof queries |

---

## P-G1 Proof Implication

For `kala_field_windows` to be non-empty:
1. `kala_field_kinematics` must have rows (stage0 ran)
2. `kala_field_routes` must have rows (stage2 ran)
3. `kala_field_clocks` + `kala_field_boundaries` must have rows (stage3 ran)
4. `kala_field_primitives` must have rows (stage1 ran, AFTER stage3)
5. Stage 4 must run to completion (no SIGTERM, no OOM)

The three documented P-G1 failure modes (SAMPURTI_STATE.md §WINDOWS-STAGE
FAILURE ROOT CAUSE) all prevented step 5 from completing. With L1e–L1j deployed,
step 5 should run to completion in Cloud Run (no coordination SIGTERM).

---

*End G1_STAGE_IO_MAP v1.0 — SAMPŪRTI-CONDUCTOR-2026-08-10-R4*
