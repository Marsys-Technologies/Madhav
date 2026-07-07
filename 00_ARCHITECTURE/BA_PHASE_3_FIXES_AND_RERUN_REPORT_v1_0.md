---
canonical_id: BA_PHASE_3_FIXES_AND_RERUN_REPORT
version: 1.0
status: CURRENT
date: 2026-07-06
author: Claude Code (BA Phase-3 fixes + re-run campaign)
supersedes: none
consumes: BA_PHASE_3_ABHINANDAN_REBUILD_REPORT_v1_0.md, CLAUDECODE_BRIEF_BA_PHASE_3_FIXES_AND_RERUN_v1_0.md
subject_chart: Abhinandan Mohanty (1c826d5a-41cb-4450-b4dc-59d440e5f75a) — NON-native
---

# BA Phase-3 Fixes + Re-run — Exit Report

## 0 — Verdict

**PHASE-3 NOT CLEAN.** 10 code/schema defects were root-caused, fixed, landed
(PRs #438–#445), and deployed. The L1→L5 build path now runs materially deeper
for a non-native chart than it ever had — a **serial** diagnostic reached
**65/66 assets `lit`** with the only non-completion being an intentional
(now-removed) contamination guard. **However, a fully-clean 66/66 has NOT been
achieved.** The final validation runs surfaced additional, deeper issues that
are **systemic** (scale/concurrency/verification), not a finite bug tail, and
that cross into data-model-ownership and orchestrator-policy decisions the
native should make. Autonomous fixing was **halted** at that threshold per the
systematic-debugging discipline (12 distinct root causes; fixes beginning to
interact). Remaining residuals are enumerated in §4.

The pre-existing rollback snapshot **`1783272757787` was never touched.** The
native chart **`482012f1…` was never built or contaminated.** All contamination
spot-checks passed (Abhinandan Sun = Aquarius ~318°, distinct from native
Capricorn ~292°).

## 1 — What was fixed (10 defects across 8 PRs)

| # | PR | merge SHA | Defect | Fix |
|---|----|-----------|--------|-----|
| 1 | #438 | 9aef418b | `mi_jivanaghatana` read the NATIVE LEL markdown for ANY chart (contamination vector) + hard `RuntimeError` on zero events | native-only markdown gate; graceful-empty for non-native; native-empty WARNING |
| 2 | #438 | 9aef418b | `ga_dashas` `executemany` silently upserted-away colliding rows; no completeness check | COPY bulk-load + completeness assertion (rows_written == computed) |
| 3 | #438 | 9aef418b | run-level state reported `completed` with 45/66 assets errored (NF-1 green over-report) | rollup marks run `failed` when any planned asset errors |
| 4 | #439 | 63e3407e | `ga_dashas` COPY `UniqueViolation` — `chart_dashas` unique key didn't discriminate KP sub-period rows from classical rows sharing `start_iso` (latent silent-overwrite bug pre-COPY) | **migration 414**: unique index incl. `COALESCE(kp_sublevel,'')` |
| 5 | #440 | ba725a99 | `ga_dashas` COPY hit the 30s `statement_timeout` on large systems | `SET LOCAL statement_timeout=0` for the per-substep COPY |
| 6 | #441 | 13f357e5 | `ga_sade_sati` `TypeError: Decimal not JSON serializable` (real upstream `Decimal` in `fact_value_jsonb`) | `json.dumps(..., default=str)` |
| 7 | #442 | 940c9ac9 | `bo_laksana` swallowed a `statement_timeout` WITHOUT rollback → `InFailedSqlTransaction` poisoned the txn + crashed the worker | SAVEPOINT-guard the best-effort salience/navamsha steps |
| 8 | #443 | 15ad2a1e | `bo_laksana` post-insert `PERCENT_RANK()` UPDATE ran 600s+ (full-row rewrite × 20 indexes) → watchdog kill | compute `salience_pctl_in_class` in memory; drop the UPDATE |
| 9 | #444 | 45b85f67 | `ga_condition` per-graha `chart_dashas` lookup did a ~20K-row heap scan (cost ~59,724) → 30s timeout under load; swallowed-without-rollback poisoned the txn | **migration 415**: partial index `(chart_id, lord_graha, start_iso) WHERE level_n=1` (→ 11-cost seek) + SAVEPOINT guards |
| 10 | #445 | 576ef7b3 | (A) `ph_rectification` hard-refused all non-native charts (native-only corpus); (B) `ga_condition`+`ga_structural` both write the same `chart_facts` avastha categories and ran concurrently → lock-contention timeout | (A) per-chart sourcing (own life_events/chart_dashas/chart_facts, never native); (B) **migration 416**: restore the `ga_structural → ga_condition` DAG edge (registry-drift fix) |

All fixes carry regression tests; the full `platform/python-sidecar` unit suite
(~2800+ tests) is green save pre-existing unrelated failures
(`test_l0_remedy_corpus.py`, one DB-integration CDLM test) untouched by this work.

## 2 — What is proven working (non-native, Abhinandan)

Confirmed via the SERIAL diagnostic rebuild (run `9dc9afe2`, HEAD_444+ph_fix era)
and the individual validations:
- **L1 Gaṇita** builds (chart_facts, chart_dashas=603,492 across 35 ayanamsha×system, chart_divisionals).
- **`ga_condition`** completes under BOTH serial and parallel (migration 415 + 416).
- **`ga_dashas`** completes (KP-collision + COPY-timeout fixes hold).
- **`ga_sade_sati`** completes (Decimal fix holds).
- **`bo_laksana`** completes (connection-poison + 600s-salience fixes hold; 67,116 MSR signals, 563 distinct salience percentiles — non-degenerate).
- **`bo_samskara`** completes serially (67,116 embeddings, ~8 min).
- **L2 Bodha 15/15, L3 Kāla 12/12, L5 Mīmāṃsā 10/10** all ran `lit` for a non-native chart for the first time (serial diagnostic).
- **`mi_jivanaghatana`** correctly builds 0-row (no native leakage).
- **run-state rollup** correctly reports `failed` on any asset error.
- **contamination firewall** holds throughout.

## 3 — Acceptance-criteria status

| AC (from brief §4) | Status |
|---|---|
| `mi_jivanaghatana` = rows_written=0, success, no native leakage | ✅ PASS |
| `ga_dashas` = full expected count, no timeout, no partial | ✅ PASS |
| run-level state reflects reality (completed vs failed) | ✅ PASS |
| Completeness/DAG: all L1–L5 built, none errored-where-upstream-has-rows | ⚠️ PARTIAL — reached under serial (65/66); not a clean 66/66 |
| Non-degeneracy (bo_upaya/cgm/pratijna/kala_convergence) | ✅ PASS where reached (serial) |
| Contamination spot-checks (Sun ≠ native; no leakage) | ✅ PASS |
| Integrity (fact_id resolution, count_sql vs throughput) | ✅ PASS on completed assets |
| `ph_rectification` scores each chart's own events, no native corpus | ⚠️ CODE LANDED; end-to-end unverified (cascade-blocked in final runs) |

## 4 — Open residuals (systemic; native decisions needed)

These are the reasons PHASE-3 is not clean. They are **not** simple bugs; they
are scale/concurrency/verification/data-model issues that surface only at
non-native scale and that interact with each other.

1. **`ga_structural` GA8 (argala) `TWO_PASS_FAILED: Duplicate fact_ids`**
   (surya_siddhanta_classical). ga_structural generates two argala rows with the
   same `(fact_category, fact_subject, fact_key)` → identical `fact_id` within
   one batch. Accompanied by a `VARGA_MISSING: D30` warning on every ayanamsha
   (GA6/ga_vargas did not produce D30 positions), which may drive an argala
   fallback that collides. Likely a **pre-existing data-dependent argala-key
   bug** (a fact_key that isn't unique across the argala house-pair matrix for
   certain ascendant configurations), NOT caused by migration 416's reorder
   (ga_structural's argala is a pure function of divisional/position data that
   ga_condition does not modify) — but the reorder/interaction is not fully
   ruled out and warrants investigation. **This is the current hard blocker to a
   clean serial build.**

2. **`ga_condition` ⇄ `ga_structural` shared-category ownership.** Both writers
   compute + delete-then-insert `graha_avastha_lajjitadi` and
   `graha_avastha_sayanadi`. Migration 416 serialized them (fixing the lock
   contention) but the underlying **ownership overlap** remains — a data-model
   decision (which writer owns those categories) that needs derivation-ledger
   review per §B.3.

3. **`ka_dasha_kala` self-test timeout (parallel only).** Its
   `confirm_systems_present(canonical_chart)` sanity probe hits `statement_timeout`
   under concurrent write load and FAILS the asset. A self-test on the canonical
   chart should never fail a client build — make it non-fatal / deferred /
   bounded.

4. **`bo_samskara` > 600s watchdog (parallel only).** Vertex-AI embeddings for
   ~67K signals take ~8 min serially but exceed the 600s per-asset watchdog under
   parallel contention. Needs either substep-chunking (per the FROZEN contract)
   or a permanent, documented `WRITER_TIMEOUT_SECONDS` raise for the heaviest
   writer.

5. **`ph_rectification` per-chart output unverified end-to-end.** The code
   (per-chart sourcing) is landed and unit-tested; it was cascade-blocked before
   executing in the final runs. Needs a clean run past L4 to confirm ~185
   per-chart candidate rows with zero native-event leakage.

6. **Systemic finding.** The 30s `statement_timeout` and 600s per-asset watchdog
   are too tight for a non-native-scale chart under wave-parallel contention.
   This build path had only ever run end-to-end for the NATIVE chart; Abhinandan
   is the first non-native full build, and each layer's latent scale/ordering/
   verification assumptions surfaced one at a time. A durable solution likely
   needs a coherent concurrency + timeout policy (advisory-lock the chart_facts
   critical section OR complete the DAG-edge ownership model; right-size the
   watchdog; make sanity self-tests non-fatal), decided holistically rather than
   one writer at a time.

## 5 — Current production config state (MUST be reconciled)

The pipeline job `brahma-build-pipeline-job` (region asia-south1, image on
HEAD_445 `576ef7b3`) currently carries two **diagnostic config overrides** that
should be reconciled to a deliberate steady state by the native:
- `ORCHESTRATOR_WORKER_LIMIT=1` (serial — avoids the wave-parallel contention).
- `WRITER_TIMEOUT_SECONDS=1200` (raised from the 600 default so bo_samskara fits).

Migration 416 (the DAG edge) is applied in prod. The Abhinandan chart is in a
**partial/failed** state (L1 incomplete due to residual #1; L2–L5 = 0). It can be
rebuilt once residual #1 is resolved, or restored from snapshot `1783272757787`.

## 6 — Recommendation

Pause autonomous per-writer fixing. Address the residuals as a **scoped
engineering + native-decision pass**: (a) fix the `ga_structural` argala
fact_id uniqueness (residual #1) — the hard blocker; (b) decide the
ga_condition/ga_structural category ownership (residual #2); (c) make
`ka_dasha_kala` self-test non-fatal and right-size the watchdog / chunk
`bo_samskara` (residuals #3–#4); then (d) one clean end-to-end run to confirm
66/66 and validate `ph_rectification` per-chart output (residual #5). Only then
is Phase-4 (native `482012f1` rebuild) cleared.

## 7 — Minor UI note (later hygiene)

The cockpit **Rebuild** button opens a "Clear all chart data?" DESTRUCTIVE modal
(confirm by typing the subject name → "Clear instrument", which then auto-chains
the rebuild). Intended behaviour, but the copy is confusing — flag for a later
UI hygiene pass.

---
*End BA_PHASE_3_FIXES_AND_RERUN_REPORT v1.0.*
