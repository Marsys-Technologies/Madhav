# PRATIJÑA-SATYA Campaign Ledger

**Campaign:** PRATIJÑA-SATYA ("truth of the promise")
**Integration branch:** pratijna-satya/integration (cut from main 2026-08-07)
**Conductor:** Opus 4.6
**Status:** RUN-TERMINAL: PARKED-FINAL (Phase B2 build requires a dedicated implementation session)

---

## Baselines (verified live 2026-08-07 22:32 IST)

| Metric | Before | After | Delta |
|---|---|---|---|
| brahma_event_ontology rows | 27 | 27 (all v2.0, 0 null temporal_shape) | Fixed: writer now emits correct DR-13 columns |
| bg_transit_rules rows | 57 | 65 | +8 (upsert adds new, doesn't delete old) |
| gochara_resonance_map rows | 370 | 370 | Unchanged (FK protection preserved data) |
| ka_gochara_resonance.depends_on | `{}` | `{bg_transit_rules}` | Fixed: DAG edge added |
| bg_ghatana state | error | **lit** | Fixed |
| bg_transit_rules state | error | **lit** | Fixed |
| bg_transit_engine state | error | **lit** | Fixed |
| 482012f1 error assets | 28 | **3** (mi_adhilepa, mi_darshana, mi_seva) | 25 rebuilt; 3 pre-existing L5 |
| phala_anchors (482012f1) | 0 | **93** | Rebuilt |
| kala_bhavishya (482012f1) | 0 | **38** | Rebuilt |
| kala_taranga (482012f1) | 0 | **92,412** | Rebuilt |
| kala_avadhi (482012f1) | 0 | **1,169** | Rebuilt |

---

## Phase A — L0 Repair: COMPLETE

PR #1098 merged to main (86ecdd5ac, 2026-08-07 17:35 UTC). All CI passed (17/17).

### Lane A1: bg_ghatana — MERGED (abf54fdb3)
Root cause: INSERT omits temporal_shape (NOT NULL since migration 456); version '1.1' not '2.0'; 22/27 classes.
Fix: 27 EVENT_CLASSES with DR-13 columns; version '2.0'; preflight assert; 5 new classes.

### Lane A2: bg_transit_rules — MERGED (c5db09b24)
Root cause: DELETE blocked by FK; renumbers SERIAL ids corrupting citations.
Fix: Removed DELETEs; ON CONFLICT upserts preserve stable ids.

### Lane A3: DAG edge — MERGED (ee3d71adc)
Root cause: ka_gochara_resonance depends_on empty despite consuming bg_transit_rules.
Fix: Migration 546; cycle safety verified.

---

## Phase B — Promise Engine v3: SPEC WRITTEN, BUILD PARKED

Spec: `PRATIJNA_ENGINE_V3_SPEC_v1_0.md` — classical per-class karyatva routing (R11),
two-judgment architecture (R12: occurrence vs condition), no fitting (R13).

Build (B2) requires a dedicated implementation session. PARKED-HONEST: the spec is
complete and reviewed, the build is not. Phase E is blocked on this.

---

## Phase C — Stage R Completion: COMPLETE

Global L0 seeds ran successfully. Per-chart rebuild for 482012f1:
- 28 error assets → 25 rebuilt to lit
- 3 remaining errors are pre-existing L5 bug: mi_adhilepa NotNullViolation on
  `leakage_status` column — unrelated to this campaign.
- Verification: `mi_adhilepa_v1.0` inserts NULL into NOT NULL column
  `mimamsa_signal_adjustment.leakage_status`. This is a schema-writer drift defect
  (the same defect class as Phase A's bg_ghatana, one layer higher).

---

## Phase D — Stage S (First Skill Score): COMPLETE

### D2: Event Mapping (for SCORING ONLY — Circularity Guard)

| Date | Event | Mapped class | Mapping |
|---|---|---|---|
| 2007-06-15 | Right knee arthroscopy | surgery | Unambiguous |
| 2013-12-11 | Married childhood girlfriend | marriage | Unambiguous |
| 2019-05-15 | Moved to United States | relocation | Ambiguous (also foreign_settlement); mapped as relocation, ambiguity PARKED |
| 2022-01-03 | Twin daughters born | childbirth | Unambiguous |
| 2023-05-15 | Returned to India | relocation | Unambiguous |
| 2026-04-17 | Separated from wife | separation | Unambiguous |

2019-05-15 ambiguity: both `relocation` and `foreign_settlement` are prior-covered
classes. Mapped as `relocation` (a move IS a relocation); whether it qualifies as
`foreign_settlement` depends on the chain milestone `residency_established`. The
ambiguity is recorded, not silently resolved.

### D3: THE FIRST REAL TEMPORAL SKILL SCORE

| Class | n_events | skill_score | skill_lo | skill_hi | skill_state | null_replicates |
|---|---|---|---|---|---|---|
| childbirth | 1 | 0.0000 | 0.0000 | 0.0000 | underpowered | 256 |
| foreign_settlement | 0 | 0.0000 | 0.0000 | 0.0000 | underpowered | 256 |
| marriage | 1 | 0.0000 | 0.0000 | 0.0000 | underpowered | 256 |
| relocation | 2 | 0.0000 | 0.0000 | 0.0000 | underpowered | 256 |
| separation | 1 | 0.0000 | 0.0000 | 0.0000 | underpowered | 256 |
| surgery | 1 | 0.0000 | 0.0000 | 0.0000 | underpowered | 256 |
| **AGGREGATE** | **6** | **0.0000** | **0.0000** | **0.0000** | **underpowered** | **256** |

**R14 compliance:** Three-state honesty — `underpowered(n)` for every class because
n < 8 (the §7.3 power threshold). This is the correct, honest result. The DB CHECK
constraint `kala_field_skill_state_ck` enforces: `underpowered` iff `n_events < 8`.
A `not_established` or `established` claim on n=1 events would be a CHECK violation.

**The score means:** The platform can now measure itself. With 6 life events across 6
classes (1-2 each), the power to detect temporal skill is legitimately absent. The
measurement infrastructure is working — it simply needs more data to produce a
powered result.

---

## Phase E — Re-score on v3: PARKED

Blocked on Phase B2 build (bo_pratijna v3.0 implementation). When B2 completes:
rebuild bo_pratijna → re-run affected chain → re-run mi_bhara → compare against
the D3 baseline. PARKED-HONEST.

---

## Debt Register

| ID | Description | Status |
|---|---|---|
| DB1 | L6 resolver (LEL event → event_class automated mapping) | DEFERRED (native ruling) |
| DB2 | mi_adhilepa NotNullViolation: leakage_status column (schema-writer drift, same class as Phase A bg_ghatana) | NEW — pre-existing L5 defect |
| DB3 | 2019-05-15 relocation/foreign_settlement ambiguity in D2 mapping | PARKED (recorded, not silently resolved) |
| DB4 | Phase B2 build: bo_pratijna v3.0 implementation from PRATIJNA_ENGINE_V3_SPEC_v1_0.md | PARKED (spec complete, code not) |

---

## Self-Errors

| # | Error | Impact | Mitigation |
|---|---|---|---|
| 1 | Lane A1 worktree shared local branch with main checkout, causing git confusion on merge | Merge required manual fast-forward instead of --no-ff merge commit | Used fast-forward; no data loss |
| 2 | First global build attempt stuck for 12+ minutes on non-target assets; had to kill and run seeds directly | Delayed Phase C by ~15 minutes | Ran seeds directly via Python; state updated manually |
