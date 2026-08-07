# PRATIJÑA-SATYA Campaign Ledger

**Campaign:** PRATIJÑA-SATYA ("truth of the promise")
**Integration branch:** pratijna-satya/integration (cut from main 2026-08-07)
**Conductor:** Opus 4.6
**Status:** ACTIVE

---

## Baselines (verified live 2026-08-07 22:32 IST)

| Metric | Value | Verification |
|---|---|---|
| brahma_event_ontology rows | 27 | `SELECT count(*) FROM brahma_event_ontology` |
| bg_transit_rules rows | 57 | `SELECT count(*) FROM bg_transit_rules` |
| gochara_resonance_map rows | 370 | `SELECT count(*) FROM gochara_resonance_map` |
| ka_gochara_resonance.depends_on | `{}` (empty) | `SELECT depends_on FROM asset_registry WHERE asset_id='ka_gochara_resonance'` |
| ontology version | 2.0 (all rows) | migration 456 applied |
| bg_ghatana asset state (482012f1) | error (since 2026-08-02) | predecessor campaign verified |
| bg_transit_rules asset state (482012f1) | error (since 2026-08-02) | predecessor campaign verified |
| Cloud SQL proxy | PID 58012, 74982 | pgrep verified |

---

## Phase A — L0 Repair

### Lane A1: bg_ghatana (NotNullViolation on temporal_shape)

| Field | Value |
|---|---|
| Status | DISPATCHED |
| Builder | Sonnet (worktree) |
| Branch | pratijna-satya/lane-a1-ghatana |
| Root cause | l0_ghatana.py INSERT omits temporal_shape (NOT NULL since migration 456); version hardcoded '1.1' not '2.0'; 22/27 classes (5 DR-13 classes missing) |
| Fix scope | Add temporal_shape/duration_prior/milestone_template/irreversibility_milestone to EVENT_CLASSES; add 5 missing classes; fix version; preflight assert |
| Dispatched | 2026-08-07 22:33 IST |
| Deadline | — |

### Lane A2: bg_transit_rules (ForeignKeyViolation)

| Field | Value |
|---|---|
| Status | DISPATCHED |
| Builder | Sonnet (worktree) |
| Branch | pratijna-satya/lane-a2-transit |
| Root cause | l0_transit.py DELETE FROM bg_transit_rules blocked by gochara_resonance_map FK (migration 459); ON CONFLICT upsert below is dead code |
| Fix scope | Remove 3 DELETE lines; update comment+log; the existing ON CONFLICT upserts become the sole idempotency mechanism |
| Dispatched | 2026-08-07 22:33 IST |
| Deadline | — |

### Lane A3: ka_gochara_resonance DAG edge

| Field | Value |
|---|---|
| Status | DISPATCHED |
| Builder | Sonnet (worktree) |
| Branch | pratijna-satya/lane-a3-dag-edge |
| Root cause | Migration 459 registered ka_gochara_resonance with depends_on=ARRAY[]::text[] despite consuming bg_transit_rules |
| Fix scope | Migration 546 to add 'bg_transit_rules' to depends_on |
| Dispatched | 2026-08-07 22:33 IST |
| Deadline | — |

---

## Phase B — Promise Engine v3

| Field | Value |
|---|---|
| Status | PENDING (parallel with A) |
| Spec | PRATIJNA_ENGINE_V3_SPEC_v1_0.md (to be written) |

---

## Phase C — Stage R Completion

| Field | Value |
|---|---|
| Status | BLOCKED on Phase A merge+deploy |

---

## Phase D — Stage S (First Skill Score)

| Field | Value |
|---|---|
| Status | BLOCKED on Phase C |

---

## Phase E — Re-score on v3

| Field | Value |
|---|---|
| Status | BLOCKED on Phase B + D |

---

## Debt Register

| ID | Description | Status |
|---|---|---|
| DB1 | L6 resolver (LEL event → event_class automated mapping) | DEFERRED (native ruling) |

---

## Self-Errors

(none yet)
