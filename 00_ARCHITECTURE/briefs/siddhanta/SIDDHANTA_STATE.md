# SIDDHANTA Campaign Ledger

**Campaign:** SIDDHANTA ("the established conclusion")
**Integration branch:** siddhanta/integration (cut from main 2026-08-08)
**Conductor:** Opus 4.6
**Status:** ACTIVE — Phase 1+2 MERGED (49/49 tests pass), Phase 3 NEXT

---

## Baselines (carried from PRATIJÑA-SATYA RUN-TERMINAL)

| Metric | Value | Scope |
|---|---|---|
| bodha_pratijna marriage grade (482012f1/lahiri) | 1.169 (= separation grade) | chart 482012f1 |
| bodha_pratijna status distribution | marriage=denied, separation=denied, childbirth=conditional(2.386) | chart 482012f1/lahiri |
| asset_throughput error rows (482012f1) | 3 (mi_adhilepa, mi_darshana, mi_seva) | chart 482012f1 |
| asset_throughput error rows (1c826d5a) | 13 | chart 1c826d5a |
| asset_throughput error rows (cb73cd3d) | 14 | chart cb73cd3d |
| asset_throughput error rows (GLOBAL) | 1 | global |
| total error rows across ALL charts+global | 31 across 16 assets | all 3 charts + global (R16) |
| kala_field rows (482012f1) | 60 | chart 482012f1 |
| kala_field_skill baseline | all classes underpowered(n), aggregate n=6 | chart 482012f1, R14 permanent |
| phala_anchors (482012f1) | 93 rows / 6 domains | chart 482012f1 |

---

## R15 Scoring Event Set (native ruling, 2026-08-08)

| Date | Event | Mapped class | Notes |
|---|---|---|---|
| 2007-06-15 | Right knee arthroscopy | surgery | n=1 |
| 2013-12-11 | Married childhood girlfriend | marriage | n=1 |
| 2019-05-15 | Moved to United States | relocation | n=2 (also 2023-05-15) |
| 2019-05-15 | US residence (4-year settlement) | foreign_settlement | n=1 (R15: counts as genuine settlement) |
| 2022-01-03 | Twin daughters born | childbirth | n=1 |
| 2023-05-15 | Returned to India | relocation | n=2 (also 2019-05-15) |
| 2026-04-17 | Separated from wife | separation | n=1 |

Total: 7 event-class pairings across 6 events. DB3 RESOLVED by R15.

---

## Phase 1 — Promise Engine v3: MERGED

### Lane P1+P2: bo_pratijna v3.0 build + tests — MERGED (cb5da546b)
- Migration 546: occurrence_grade + condition_grade columns on bodha_pratijna
- New: bo_pratijna_karyatva.py — 27 event class karyatva maps (22 classical + 5 DR-13 provisional)
- Modified: bo_pratijna.py — ENGINE_VERSION v3.0, per-class karyatva routing, domain fallback
- Tests: 35 passed (15 v3 property + 20 v2 regression), 2 skipped (DB-only)
- Property tests verified: marriage != separation, childbirth independence, R12, R13, registry

---

## Phase 2 — mi_adhilepa Repair: MERGED

- Commit: 62b322f8a (three-part fix)
- Migration 547: leakage_status DEFAULT 'not_assessed' for 4 overlay tables (backfill + NOT NULL restored)
- Writer: mi_adhilepa._overlay_row emits "not_assessed" (not None, not "clean")
- Consumer: mi_gunanaka excludes only 'leaked'; admits 'clean' + 'not_assessed'
- Tests: 14 passed (overlay row, source text, consumer filter, defect documentation)

---

## Phase 3 — Full Rebuild: NEXT

**NEXT-ACTION:** Create PR siddhanta/integration -> main, merge, deploy, rebuild all three charts.

## Phase 4 — Re-score: BLOCKED on Phase 3

## Phase 5 — Arc Close: BLOCKED on Phase 4

---

## Debt Register (inherited + new)

| ID | Description | Status |
|---|---|---|
| DB1 | L6 resolver (LEL event -> event_class automated mapping) | DEFERRED (native ruling) |
| DB3 | 2019-05-15 relocation/foreign_settlement ambiguity | RESOLVED by R15 |
| DB4 | Phase B2 build: bo_pratijna v3.0 | CLOSED (Phase 1 merged) |
| DB5 | mi_adhilepa NotNullViolation: leakage_status schema-writer drift | CLOSED (Phase 2 merged) |

---

## Self-Errors

(none yet)

---

*Ledger created 2026-08-08 01:32 IST by CONDUCTOR (Opus 4.6)*
