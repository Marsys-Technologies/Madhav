# SIDDHANTA Campaign Ledger

**Campaign:** SIDDHANTA ("the established conclusion")
**Integration branch:** siddhanta/integration (cut from main 2026-08-08)
**Conductor:** Opus 4.6
**Status:** RUN-TERMINAL: PARKED-FINAL (DB6 marriage/separation identity requires fact_key resolution)

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

## Phase 3 — Full Rebuild: 482012f1 COMPLETE, others PARKED

PR #1099 merged (2026-08-07 20:49 UTC), migrations 548+549 applied.

**482012f1 rebuilt:** 76 lit, 5 error (pre-existing), mi_adhilepa/mi_darshana/mi_seva ALL lit.
**Marriage: denied 1.169 → promised 6.231** (v3 working). marriage=separation identity NOT broken (DB6).
**1c826d5a + cb73cd3d:** PARKED (60+ min per chart; v3 code is deployed and will apply on next build trigger).

---

## Phase 4 — Re-score: COMPLETE

R15 event-class mappings applied (6 UPDATEs + 1 INSERT). mi_bhara re-scored (4.4s, 13 rows).
All classes underpowered (n<8). AGGREGATE n: 6->7 (foreign_settlement +1 per R15).
Skill scores invariant. R14 baseline preserved (same field_snapshot_id).

---

## Debt Register (inherited + new)

| ID | Description | Status |
|---|---|---|
| DB1 | L6 resolver (LEL event -> event_class automated mapping) | DEFERRED (native ruling) |
| DB3 | 2019-05-15 relocation/foreign_settlement ambiguity | RESOLVED by R15 |
| DB4 | Phase B2 build: bo_pratijna v3.0 | CLOSED (Phase 1 merged) |
| DB5 | mi_adhilepa NotNullViolation: leakage_status schema-writer drift | CLOSED (Phase 2 merged) |
| DB6 | marriage/separation identity: constituent_facts_array UUIDs need JOIN to chart_facts for fact_key matching | NEW — release: add fact_key lookup to _match_signal_to_class |
| DB7 | condition_grade always 0.000 (same root cause as DB6) | NEW — blocked on DB6 |
| DB8 | 1c826d5a + cb73cd3d full rebuilds | PARKED — v3 deployed, will apply on next build |
| DB9 | 3 pre-existing KeyError (ka_kota_chakra/ka_moorti_nirnaya/ka_tithi_pravesha) | PRE-EXISTING |

---

## Self-Errors

| # | Error | Mitigation |
|---|---|---|
| 1 | Builder wrote to main checkout not worktree | Recovered from lane branches |
| 2 | Partial rebuild plans blocked by orchestrator | Used full DAG plan |
| 3 | ga_sensitive 45+ min on full rebuild | Future: targeted reset |
| 4 | UUID fact matching not caught pre-deploy | Recorded as DB6 |

---

RUN-TERMINAL: PARKED-FINAL

Parked cause VERIFIED: DB6 (marriage/separation identity) root cause is constituent_facts_array
containing UUID strings. The karyatva signal matcher's bhava/karaka/divisional patterns match
against these UUIDs, which never matches. Release condition: add a JOIN to chart_facts in
_match_signal_to_class to resolve fact_ids -> fact_keys. The structural karyatva maps are correct.

*Ledger created 2026-08-08 01:32 IST, closed 2026-08-08 06:15 IST by CONDUCTOR (Opus 4.6)*
