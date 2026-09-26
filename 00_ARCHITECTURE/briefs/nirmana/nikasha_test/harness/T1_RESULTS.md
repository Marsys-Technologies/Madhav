---
artifact: NIKASHA_TEST_T1_RESULTS
version: "1.0"
status: FINAL
campaign_id: nikasha-test
phase: 2
test: T1 (planted-defect suite + mutation + differential)
date: 2026-09-26
target: sandbox only (db nikasha_sandbox, socket nikasha_test/.sandbox, port 54329, user sandbox)
---

# T1 — Planted-defect suite, mutation test, differential test

Inspector under test: `platform/scripts/governance/asset_census.py` (sha256(12) `1158bc8543ec`,
stdlib-only, shells to psql). Run pattern per plant:

```
PGHOST=NT/.sandbox PGPORT=54329 PGUSER=sandbox PGDATABASE=nikasha_sandbox PGOPTIONS= \
  /opt/homebrew/opt/python@3.13/bin/python3.13 platform/scripts/governance/asset_census.py \
  --layer L<n> --out census/plants/<plant>.json     # exit code 2 when failures exist
```

Harness: `harness/plant.py` (17 plants), `harness/mutation_test.py` + `harness/asset_census_mutant.py`,
`harness/differential.py`. Raw results: `harness/T1_RESULTS.json`, `harness/T1_MUTATION.json`,
`harness/T1_DIFFERENTIAL.md`; per-plant censuses: `census/plants/*.json`. Baselines:
`census/L0_sandbox2_20260926.json`, `census/L3_sandbox_20260926.json`,
`census/{L1,L2,L4,L5}_sandbox_20260926.json` (all against the clean sandbox).

## 1. Planted-defect suite — 17 plants, 17 detected, 0 cross-asset collateral

Every plant asserts the check changes verdict **for the planted asset and no other**
(`collateral=[]` on all 17). Every plant restored clean (`restore_ok=true` on all 17).

| # | plant | check | asset | defect planted | expected | observed | detected |
|---|---|---|---|---|---|---|---|
| 1 | vocab_identity | Vocab.identity | ph_sankrama (L4) | 2 rows duplicating the composite natural key; nullable members NULL (unique index admits them; `count(*)-count(DISTINCT)` = 1) | FAIL | PASS→FAIL ("1 duplicate(s)") | YES |
| 2 | count_floor | Count.floor | bg_vedha_malefic_scale | DELETE 1 row (live 5→4, floor=5) | FAIL | PASS→FAIL (delta=-1) | YES |
| 3 | build_completion_rw0 | Build.completion | bg_dignity_reference | rows_written=0 on the build record of a populated table | FAIL | PASS→FAIL | YES |
| 4 | build_completion_truncate | Build.completion | bg_muhurta_lattice | DELETE all 8 579 rows; build record says rows_written=8 579→0 after | **FAIL→PASS (inverted)** | FAIL→PASS ("live=0 and rows_written=0 — consistent") | **NO — see T1-FN1** |
| 5 | earn_cost_signal | Earn.build_record | bg_yogas | SENSITIVITY plant (reverse): rows_per_second=100 | PASS | FAIL→PASS (both Earn.build_record and Cost.baseline) | YES — see T1-FN4 |
| 6 | build_dag | Build.dag | bg_yogas | depends_on += phantom asset bg_t1_phantom | FAIL | PASS→FAIL (+ same-asset Build.dep_liveness co-fire, expected) | YES |
| 7 | build_target_null | Build.target | bg_transit_rules | target_table=NULL (has_writer=true) | N/A | PASS→N/A | YES(degraded) — see T1-FN2 |
| 8 | count_integrity | Build.count_integrity | bg_dignity_reference | integrity_check_sql=NULL (count_sql present) | PARTIAL | PASS→PARTIAL | YES |
| 9 | ldgr_source | Ldgr.source_presence | bg_dasha_systems | classical_citations=NULL on one row | PARTIAL | PASS→PARTIAL (19/20) | YES |
| 10 | vocab_alias | Vocab.alias | bg_ontology | synonyms='{}' on all 662 rows that had aliases | FAIL | FAIL→FAIL, measured worsens 79/741→741/741 empty | YES(verdict-invisible) — see T1-FN3 |
| 11 | build_history | Build.history | bg_class_priors | build_runs + build_run_assets row with status='error' | FAIL | PASS→FAIL | YES |
| 12 | build_exercised | Build.exercised | bg_dignity_reference | DELETE all 3 build_run_assets rows (has_writer=true, never run) | FAIL | PASS→FAIL (same-asset Build.history→N/A) | YES |
| 13 | dep_liveness | Build.dep_liveness | bg_class_lifetime_counts | state='error' on dependency bg_ghatana | FAIL | PASS→FAIL ("DEP-ASSERT") | YES |
| 14 | build_registered | Build.registered | bg_reference | has_writer=false while writer file still carries @register | FAIL | PASS→FAIL | YES |
| 15 | build_contract | Build.contract | bg_dignity_reference | CODE: real `ctx.db_conn.commit()` injected into writer run() | FAIL | PASS→FAIL | YES |
| 16 | idem_pattern | Idem.pattern | bg_cohort | CODE: 'ON CONFLICT' → 'ON  CONFLICT' (double space) in writer | PARTIAL | PASS→PARTIAL | YES |
| 17 | dens_served | Dens.served | bg_gochara_arcs | CODE: L0 capability file zz_t1_plant.ts referencing the table with no density_contract | FAIL | N/A→FAIL ("1 module(s): zz_t1_plant.ts; declaring density_contract: 0") | YES |

Schema traps encountered and solved while building the suite (recorded for Phase 3 reuse):

- `bg_muhurta_lattice.id` is GENERATED ALWAYS identity → restore needs `INSERT ... OVERRIDING SYSTEM VALUE`.
- `bg_sky_calendar.secondary_body_key` is a GENERATED column coalescing NULL→'' (30 449 rows) —
  physically blocks the Vocab.identity NULL-key plant → plant moved to L4 `phala_sankrama`.
- `asset_registry.asset_kind` CHECK = data|service|artifact, NOT NULL → see T1-FN2.
- `build_runs` NOT NULL columns: chart_id, scope, action, plan, triggered_by; state CHECK:
  planned|running|paused|completed|stopped|failed. `asset_throughput.state` CHECK:
  dormant|building|lit|stale|error|incomplete.

## 2. False-negative / degraded-detection findings (T1 register candidates)

- **T1-FN1 — Build.completion inverted (confirms and sharpens R42).** Emptying a table whose
  build record agrees with the emptiness flips the check FAIL→**PASS**: destroying data makes the
  asset look healthy. The check is a rows_written-vs-live *consistency* test, not a non-emptiness
  test; combined with R42 (rows_written present breaks the comparison) the check is unreliable in
  both directions.
- **T1-FN2 — Build.target FAIL branch is dead code.** The only FAIL path requires a data-kind
  asset with a NULL target_table, but `asset_registry.asset_kind` is NOT NULL with CHECK
  (data|service|artifact) and the NULL-target plant is expressible → the check degrades to N/A
  ("no target_table; asset_kind='data', has_writer=True"). Detected-but-degraded: a target-table
  loss can never raise FAIL.
- **T1-FN3 — Vocab.alias severity is verdict-invisible.** Emptying all 662 synonym sets moved the
  measured value 79/741→741/741 empty but the verdict stayed FAIL→FAIL (no synonyms-bearing asset
  is PASS anywhere in the sandbox, so the check saturates). New alias defects are invisible once
  the asset is already FAIL; only the `measured` string carries the signal.
- **T1-FN4 — Earn.build_record ≡ Cost.baseline is one detector, and it is constant-FAIL in the
  sandbox.** Both checks read the same `asset_throughput.rows_per_second` column; the sandbox has
  ZERO assets with rows_per_second set, so both verdicts are FAIL at baseline everywhere. The
  "plant" could only run in the sensitivity direction (set rps → both flip to PASS). Any verdict
  movement on one must move the other; they provide no independent signal.
- **T1-F1 — Count.floor / Build.completion silently absent on parameterized or multi-table
  count_sql (differential, §4).** 57 assets on L1/L2/L4/L5 emit NO Count.floor verdict at all
  because the inspector cannot execute their count_sql per-asset (e.g. `WHERE chart_id = $1`).
  The independent reimplementation (plain `count(*)` of target_table) finds real floor breaches
  the inspector never reports, e.g. `ga_condition` 135 < floor 2 880, `ga_vargas` 0 < 22 092,
  `bo_laksana` 7 409 < 60 000, `bo_samskara` 7 537 < 60 000, `ph_sankrama` 630 < 2 510.

## 3. Mutation test — the suite notices a broken detector

`harness/asset_census_mutant.py` = inspector with the Vocab.identity PASS/FAIL comparison
inverted. Re-ran the vocab_identity plant (`census/plants/mutant_control.json`,
`mutant_vocab_identity.json`):

- control inspector on the planted duplicate: **FAIL** ("1 duplicate(s)")
- mutant inspector on the same data: **PASS** (same measured string)
- `suite_notices=true`, `restore_ok=true`

The planted-defect suite can fail — it distinguishes a working detector from an inverted one.

## 4. Differential test — independent reimplementation, all 6 layers

`harness/differential.py` reimplements three checks with deliberately different logic
(Vocab.identity: duplicate GROUPS over non-NULL key members vs count-DISTINCT; Build.registered:
literal grep of `@register('<id>')` vs AST walk; Count.floor: plain count(*) of target_table vs
the asset's own count_sql) and diffs verdicts against the inspector's sandbox censuses.

**Totals: 265 agreements; 99 disagreements, ALL classed; 0 unclassified.**

| class | rows | reading |
|---|---|---|
| known defect R46 (view/stub count_sql ≠ table count) | 9 | inspector's live counts disagree with the tables on L0 (e.g. bg_nakshatra inspector 2 857 vs table 28) — the inspector is wrong, ours matches the table |
| known defect R48 (Count.floor absent on L3) | 19 | inspector emits no Count.floor anywhere on L3; ours measures all 19 (6 are real FAILs: ka_kalasutra, ka_kshetra, ka_taranga, ka_yojaka et al.) |
| known defect R43 (literal-grep vs AST read of @register) | 13 | two readings of writer registration disagree; the three-source rule (§Phase 2) applies — code + registry + run history recorded in the diff |
| finding T1-F1 (parameterized/multi-table count_sql → inspector silent) | 57 | see §2 |
| methodology (bg_prashna_rules: multi-table asset counted via count_sql, no target_table) | 1 | not a defect — ours cannot run without a target_table |

One tooling note: the first differential run used a single-quote-only grep for `@register` and
produced 64 bogus R43 rows; double-quoted decorators are real in this codebase. Fixed to
`@register\(['"]` — the row count collapsed to the 13 genuine disagreements.

## 5. Checks NOT measurable by planting (and why)

- **Complete.width, Carr.detector, Reach.fields** — constant verdicts with no per-asset input to
  mutate; there is nothing to plant against. Recorded as NOT_MEASURED.
- **Earn.build_record / Cost.baseline defect direction** — constant-FAIL at sandbox baseline
  (rows_per_second never set), so only the sensitivity direction is plantable (T1-FN4).

Coverage: 15 of the 18 inspector checks have at least one real plant; the remaining 3 are
structurally unplantable, not skipped.

## 6. Restore verification and sandbox cleanliness (final state)

- All 17 plants: `restore_ok=true`, `collateral=[]`.
- `bg_muhurta_lattice` count = 8 579 (= baseline; the mid-session failed restore was repaired
  with `INSERT ... OVERRIDING SYSTEM VALUE` and re-verified).
- `phala_sankrama`: 0 rows matching the 't1' plant marker; count = 630 (= baseline).
- `nt_t1` scratch schema: exists, 0 tables.
- Code plants reverted: `git status --porcelain platform/` clean; no `zz_t1_plant.ts` under
  `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/`.
- `/tmp/nikasha_prod` never touched; all mutation ran against the sandbox only.

## 7. Headline answer

Per-cell, the inspector's verdicts are trustworthy: 17/17 planted defects moved exactly the
planted asset's verdict with zero cross-asset collateral, and the suite provably notices a broken
detector. The false-negative risk is concentrated in known classes, not random noise: R42's
inverted consistency test (T1-FN1), one dead FAIL branch (T1-FN2), verdict-saturated severity
(T1-FN3), one duplicated constant-FAIL detector (T1-FN4), and a 57-asset silent-coverage gap on
parameterized count_sql (T1-F1) that hides real floor breaches.
