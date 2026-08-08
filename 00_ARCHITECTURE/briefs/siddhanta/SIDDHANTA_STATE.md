# SIDDHANTA Campaign Ledger

**Campaign:** SIDDHANTA ("the established conclusion")
**Integration branch:** siddhanta/integration (cut from main 2026-08-08)
**Conductor:** Opus 4.6
**Status:** ACTIVE — arc-finishing run (2026-08-08). DB6 FIXED and live-verified;
DB7 falls with it; DB9 (3 KeyErrors) root-caused and fixed; DB12 found and fixed.
Awaiting PR #1100 merge + deploy + rebuild → MEASUREMENT #3.

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
| DB6 | bo_pratijna matched raw fact_id digests instead of fact_keys -> ALL 21 non-provisional classes matched nothing; every skill score epsilon-zero | **FIXED** 20121a154 — live-verified 21/21 classes match, 139,471 fact_ids resolved |
| DB7 | condition_grade always 0.000 | **FIXED** — falls with DB6; nonzero for 20/21 classes on live data |
| DB9 | 3 KeyError: 1 (ka_kota_chakra / ka_moorti_nirnaya / ka_tithi_pravesha) | **FIXED** 09fa25715 — one bug class: bare conn.cursor() inherited dict_row, then indexed positionally row[1]. Tables were 0 rows (fail precedes DELETE, so no partial writes) |
| DB8 | 1c826d5a + cb73cd3d full rebuilds | **OPEN** — DB9 fix now unblocks 'zero errors'; rebuild pending deploy of PR #1100 |
| DB10 | Bhava pattern `house_1` substring-matches `house_10`/`11`/`12` | **OPEN but currently INERT — verified 2026-08-08.** Exhaustive check over bhavas 1-12 vs real `house_N` fact_keys: **bhava 1 is the ONLY colliding pattern**. No non-provisional event class declares primary_bhava=1, so today the collision reaches nothing. It becomes live the moment any class adds bhava 1 (lagna). R13 forbids fixing it alongside the mechanical repair; fix before adding any lagna-primary class |
| DB11 | separation cond_sum=0.00 in 4,000-signal sample | **OPEN — R16 sample-scoped observation, NOT a defect claim.** Re-check against full post-rebuild data |
| DB12 | R6 gate detector grepped raw source and matched the comment DOCUMENTING the gate's removal; failed on correct code; invisible because it skipped without a DB | **FIXED** 7594107b7 — comment-stripped, mutation-proven still catches a real gate |
| DB13 | relation "bodha_graph" does not exist -> 3 test_bo22.py failures | **OPEN** — pre-existing schema/test drift, unrelated to this arc |
| DB14 | **Isolation rail is unenforced prose.** PARIKSHAKA verdict NO-GUARD-EXISTS: no hook, no CI check, no script can detect a builder writing to the main checkout. Structurally undetectable post-hoc — git commits carry no cwd provenance, so CI is blind by construction | **OPEN** — §N.8 UNEARNED. Recommended: versioned .githooks/pre-commit failing when git rev-parse --show-toplevel is the shared checkout |

---

## Self-Errors

| # | Error | Mitigation |
|---|---|---|
| 1 | Builder wrote to main checkout not worktree | Recovered from lane branches |
| 2 | Partial rebuild plans blocked by orchestrator | Used full DAG plan |
| 3 | ga_sensitive 45+ min on full rebuild | Future: targeted reset |
| 4 | UUID fact matching not caught pre-deploy | Recorded as DB6 |
| 5 | Arc-finishing run: ran `git checkout HEAD~1 -- bo_pratijna.py` to A/B a test, which silently reverted the DB6 fix in the working tree | Caught immediately by re-grepping for the fix; restored from HEAD (already committed+pushed, so nothing was lost). Lesson: never use checkout-from-another-commit to A/B; use a scratch worktree |
| 6 | Reported the predecessor's PARKED-FINAL 'no cloud-sql-proxy credentials' claim to the native as fact, twice, without testing it — the proxy had been running since 2026-08-05 | A later run disproved it by simply connecting. Lesson: verify a blocker before relaying it, especially an inherited one |

---

## Arc-finishing run — 2026-08-08

DB6 root cause was confirmed as stated, with one precision correction: the
constituent_facts_array entries are **16-hex fact_id digests**, not UUIDs.

Fixed and live-verified (read-only, chart 482012f1, 4,000-signal sample):
- 139,471 fact_ids resolve through chart_facts
- **21/21** non-provisional classes now match (was **0/21** — the entire karyatva
  engine was inert)
- condition weights nonzero for **20/21** classes -> DB7 falls with DB6

Also fixed this run: DB9 (3 KeyErrors, one bug class) and DB12 (a gate detector
that matched its own removal comment). Both mutation-proven, not asserted.

PR #1100 open (DB6 + DB12 + DB9). Merge -> deploy -> rebuild -> MEASUREMENT #3.
MEASUREMENT #2's row-level values were captured to
SKILL_MEASUREMENT_REGISTER_v1_0.md BEFORE the rebuild can overwrite them.

*Ledger created 2026-08-08 01:32 IST; arc-finishing run 2026-08-08 by CONDUCTOR (Opus 4.6)*
