---
artifact: PRE_FAN_OUT_MANIFEST_v1_0.md
conductor: Sūtradhāra
layer: L3 Kāla
created: 2026-06-21
purpose: Record the pre-fan-out gate verdicts before any agent is spawned.
---

# L3 Kāla — Pre-Fan-Out Manifest

## PRE-1 — PART-A Closeout Gate ✅ GREEN

Source: L3_KALA_OPERATOR_RUNBOOK_v1_0.md v1.1 (ALL_GATES_GREEN, executed S1892 2026-06-21 ~04:24 IST)

| Gate | Status | Evidence |
|---|---|---|
| OP1 — Branch reconciliation | ✅ | 4 stale branches deleted local+remote (S1892) |
| OP2 — Inputs committed to clean branch | ✅ | commit 6fa47a59, 167 files on chore/l3-kala-planning-inputs |
| OP3 — prod==main verify | ✅ | L2 migrations 325-327 applied; cockpit stats live |
| OP4 — prod residual checks | ✅ | 66,738 embeddings @768-dim; 4 L3-fill hooks = NULL |
| D7 — Templates/weights RATIFIED | ✅ | L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md RATIFIED |
| D-Q4 — embeddings known-gap | ✅ | bo_samskara uses real Vertex AI (confirmed) |
| D-Q7 — coarse-to-fine ratified | ✅ | ka_gochara brief §3.5 spec confirmed |
| DR3 — TRUE_NODE | ✅ | l0_ephemeris.py + compute_transits.py both TRUE_NODE |
| CS3 — DAG contradiction fixed | ✅ | ka_kala_darshana parallel_safe_with=[] |
| CS4 — service-asset-type id | ✅ | normalized to k0_service_asset_type |

**VERDICT: PRE-1 GREEN — all OP and decision gates clear.**

---

## PRE-2 — Migration Pre-Allocation ✅ ASSIGNED

See MIGRATION_PRE_ALLOCATION.md for the full block (328–335).

- Last on-disk migration: 327 (platform/migrations/327_l2_bodha_cockpit_is_active.sql)
- Next free number: 328
- Block 328–335 assigned in DAG order (K0→K6)
- Migration dir for new L3 migrations: platform/migrations/

**VERDICT: PRE-2 ASSIGNED — 8 numbers locked; no agent resolves `<next>` itself.**

---

## PRE-3 — RATIFIED Templates/Weights Pinned ✅ GREEN

Source: L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md status=RATIFIED 2026-06-21

- I-7 weights: RATIFIED (read-only for the swarm)
- I-15 activation templates: RATIFIED (read-only for the swarm)
- I-16 convergence form + weights: RATIFIED (read-only for the swarm)
- Any "re-pick weight" impulse = Tier-2 STUB+log; NEVER a native halt

**VERDICT: PRE-3 GREEN — templates pinned read-only.**

---

## ALL PRE-FAN-OUT GATES: ✅ GREEN

**Build is authorized to begin. K0 agent spawning next.**

Timestamp: 2026-06-21 ~04:35 IST
</content>
