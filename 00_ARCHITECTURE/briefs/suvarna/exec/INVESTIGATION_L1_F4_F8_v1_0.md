---
artifact: INVESTIGATION_L1_F4_F8
version: "1.0"
status: DRAFT_FOR_REVIEW
date: 2026-10-02
lane: suvarna/land/TI-l1-f4-f8-001
base_commit: origin/main bf6fe712b
produced_by: exec-suvarna (read-only investigation)
execution: NONE against any real system. DB access was SELECT and catalog reads only, as `suvarna_reader`. No code, DB, build or migration change. The one computation (Part A.4) ran the shipping writer's pure row-builders offline against an in-memory dict with a fake connection; no database connection was opened by it.
questions: "F-4: why do the L1 build records say 38,620 rows for ga_vargas on charts 1c826d5a and cb73cd3d while chart_divisionals holds 23,542 each? F-8: why is ga_dashas `incomplete` on cb73cd3d, and why did the 2026-09-19 ga_positions run abort with no error text?"
changelog:
  - "1.0 (2026-10-02): first version."
---

# L1 investigation: F-4 (ga_vargas 38,620 vs 23,542) and F-8 (ga_dashas incomplete, ga_positions abort)

Charts: **A** = 1c826d5a-41cb-4450-b4dc-59d440e5f75a, **B** = cb73cd3d-9eba-4220-9902-0de91566e980, **C** (canonical) = 482012f1-710e-4a25-994a-93821f5871aa.

## Verdicts (short form)

**F-4**
1. **38,620 is an attempted-row count, reproduced exactly**: 5 ayanamshas x 7,724 rows the writer built per ayanamsha, reported as `len(rows)` by the pre-F-A3 `_write_rows_batch`. It is recorded only in `asset_throughput.rows_written` (A and B, July 2026 builds).
2. **(a) Counting artefact: yes, for the number.** The rows were never all written; the count over-reported.
3. **(b) Real silent data loss: also yes, and it is not only the D30 collapse.** Of the 15,078-row gap (A and B), 850 rows are the F-A3 delete-grain loss (the D30 main-loop output, 170 per ayanamsha), 8 are sentinel churn, and **14,220 are rows dropped by natural-key collision** (2,844 per ayanamsha): 13,200 `varga_ashtakavarga` (11 of 12 sign rows per graha x varga lost; only Aries/S1 survives), 750 `varga_house_lord` (a lord that rules two houses keeps one), 250 `varga_d30_lord_per_amsa` (60 intended, 10 land: the F-A2 collapse), 20 `scope_cap` sentinels (the five floored bodies share one key).
4. **(c) The loss pattern repeats on canonical C.** C's recorded 24,400 is a landed count (post-F-A3, 09-07) and is within 8 of live 24,392 (the 8 = INVARIANT sentinels re-deleted per ayanamsha), so the *count* is honest. But the writer still attempts 38,620 and drops the same 14,220 key-collision rows on C: F-A2 (unique index lacks `fact_subject`) is unfixed in live. C only gained back the 850 delete-grain rows (24,392 = 23,542 + 850).
5. **Adjacent defect found on A and B (not asked): their `krishnamurti` and `surya_siddhanta_classical` varga positions are identical to `lahiri_chitrapaksha`** (PR #1053 ayanamsha-id fallback, fixed 2026-08-05, after the July builds; plus F-A1 birth-instant error, fixed 09-05). C was rebuilt 09-07 and differs correctly.

**F-8**
6. **ga_dashas `incomplete` on B is honest, not a false alarm.** B's `chart_dashas` holds two builds: 984e5eab (07-27, lahiri/true_chitra/raman) and 75ec8317 (08-05 20:33-20:35Z, krishnamurti/surya_siddhanta_classical only). The 08-05 pass never ran its 36th sub-step (concurrency post-pass), so those two ayanamshas have `convergence_count_at_start` NULL on all 202,552 rows (the other three have 192 per ayanamsha). The watchdog found the asset stuck in `building` and, since `has_substeps=true`, withheld `lit` (state `incomplete`, 505,348 rows, "0 substeps committed") at 08-05 20:55:06Z.
7. **`incomplete` has nothing to do with the ga_dashas `integrity_check_sql`**: that SQL is hard-scoped to chart C (`482012f1`) and never inspects B. It is a watchdog state (migration 474), not an integrity result.
8. **The 09-19 ga_positions abort was the orphan watchdog reaping a run that was never dispatched** (not a person, not the guardian, not a crash): the run (59232059, chart C, `l3-lane-frozen-manifest-rebuild`) sat `planned` with `started_at` NULL and was failed 11m28s later; `stop_requested_at` NULL. The asset row is `aborted` with no error because the watchdog version live on 09-19 aborted the asset without writing `error`/`ended_at`; the run row does carry `last_error = 'orphan-watchdog: run never dispatched'`. Fixed in code on 09-30 (#2782). Why Cloud Run never claimed the run is not visible from the reader.
9. **Repeat risk on C's S-L1 run:** the never-dispatched reaping can repeat (51 of 736 runs, 16 distinct days, none with a stop request; the code now writes error text to both rows). The B-style `incomplete` repeats only if ga_dashas is run as a partial, out-of-plan pass or its process dies mid-plan; C's current ga_dashas is a single complete build.
10. Unverified items are in section C.

---

## A. F-4 evidence

### A.1 Where the number lives
`asset_throughput.rows_written` (ga_vargas): A 38,620 (last_built_at 2026-07-26 06:36:58Z, run 7d8ee2b2), B 38,620 (07-27 08:39:32Z, run 984e5eab), C 24,400 (09-07 11:03:25Z, run 0663e31b). `built_against_writer_hash` is `unknown` for A and B (pre-receipt era). Nothing else records a count: `build_run_assets` has no row-count column; `build_substep_progress` has no ga_vargas rows; `asset_provenance_receipts` has a single ga_vargas receipt (C, `proven`) carrying digests, not a count; `asset_throughput.history` is empty `[]`; `expected_rows` is NULL. So "build records" for F-4 reduce to one column plus the F-A3 test header and PR #1766 text.

### A.2 Table key and writer (read at origin/main bf6fe712b)
`chart_divisionals_unique_idx` = UNIQUE (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key) NULLS NOT DISTINCT (catalog; migration 218 widened it from (chart_id, graha, ayanamsha_id, varga)). It does **not** include `fact_subject`, `sign`, `sign_number` or `house`.
`ga_vargas_writer.py:2610-2660`: both INSERTs end `ON CONFLICT (...) DO NOTHING`, so a colliding row is skipped silently. `_write_rows_batch` (:2676) runs `replace_prior_chart_divisionals` (delete grain = chart x varga-list x ayanamsha-list, `_idempotency.py:106`) before inserting. Pre-F-A3 it `return len(rows)` (attempted). #1766 (2026-09-05) changed it to the driver `rowcount` and added `cleared` scopes so later passes do not re-delete (docstring cites "38,620 written vs 23,542 live"). The orchestrator drives one ayanamsha per sub-step (`ayanamsha_subset=[aya]`).

### A.3 Build history (build_runs / build_run_assets)
A's live rows: build 7d8ee2b2 (rows created 2026-07-26 06:36:37-06:36:51Z), run `completed`, ga_vargas asset `complete`. B's: build 984e5eab (07-27 08:39:15-08:39:28Z), `completed`/`complete`. Both are `layer` runs by `xl2wYZRPwsVgPSAgtn9XJ80Xkub2`; neither was rebuilt since. C's live rows are build 0663e31b (09-07 11:03Z, nirmana L1 wave-1; an earlier attempt 10:57Z failed `post-write integrity check failed: integrity_check_sql -> False`, reason not visible to the reader). Live per chart: A and B 23,542 = 5 x 4,708 + 2 INVARIANT sentinels; C 24,392 = 5 x 4,878 + 2.

### A.4 Computation that closes the arithmetic
Method: import the shipping `ga_vargas_writer`, replace `_write_rows_batch` with an in-memory model of the unique index, `ON CONFLICT DO NOTHING` and the delete grain, run `build_ga_vargas` per ayanamsha with a fake connection (no DB), with the D60 deity reference (60 rows from `bg_shashtiamsha_deities`, read via the reader) seeded. Canonical birth parameters; collision structure does not depend on the longitudes.

| Mode | Reported per ayanamsha | x5 | Live per ayanamsha (model) | Matches |
|---|---|---|---|---|
| pre-F-A3 (`len(rows)`, delete per batch) | 7,724 | **38,620** | 4,708 + sentinels | A/B live 23,542 (4,708 x 5 + 2) |
| post-F-A3 (rowcount, scoped delete) | 4,880 | **24,400** | 4,878 + sentinels | C throughput 24,400; C live 24,392 |

Attempted 7,724 per ayanamsha decomposes as: main varga loop 7,628 + D30-lords 60 + cross-varga 30 + 6 sentinels. Distinct natural keys among them: 4,884. So **2,844 attempted rows per ayanamsha collide on the key even post-fix**:

| fact_category | attempted | distinct keys | dropped / aya | what is lost |
|---|---|---|---|---|
| varga_ashtakavarga | 2,880 | 240 | 2,640 | 12 sign-wise bindus per (graha, varga) collapse to 1 (live: only `*.S1` / Aries survives, e.g. `D1.SUN.S1 bindus=5`) |
| varga_house_lord | 360 | 210 | 150 | graha is the key and 'lord' the fact_key: a lord of two houses keeps the first (e.g. D1 Mars: H1 kept, H8 lost) |
| varga_d30_lord_per_amsa | 60 | 10 | 50 | the 6 odd and 6 even signs share five lord/degree keys each (live: 10 rows, subjects `D30.S1` and `D30.S2` only) |
| scope_cap | 6 | 2 | 4 | the five floored bodies (Uranus..MC) share one key; only URANUS lands (live INVARIANT rows: D81 and URANUS) |

Gap accounting for A and B (38,620 - 23,542 = 15,078): 5 x 2,844 = 14,220 key collisions; 5 x 170 = 850 D30 main-loop rows erased by the D30-lords pass (F-A3; live D30 = 10 rows on A/B vs 180 on C, and `D60`/`D7` differ only by where `varga_saptavargaja_bala_component` sits, a July-vs-August code change); 8 = sentinel rows counted five times but alive twice (`_delete_invariant_sentinels` runs per ayanamsha). 14,220 + 850 + 8 = 15,078. Exact.
Post-fix on C: recorded 24,400, live 24,392 (diff 8, same sentinel churn), 24,392 - 23,542 = 850 (the F-A3 recovery).

### A.5 Cause statement
Mechanism: the writer emits sign-/house-/region-granular facts under a unique key that omits the disambiguating column; `ON CONFLICT DO NOTHING` drops them silently; the pre-fix count (`len(rows)`) hid it; separately the delete grain erased the D30 pass. #1766 fixed the delete grain and the count; F-A2 (key widening by `fact_subject`, needs a migration) is named "not in this PR" in #1766 and is not in the live index.

### A.6 Adjacent defect on A and B (independent of the count)
Sum of D1 `degree_in_sign`: A krishnamurti = lahiri = surya_siddhanta_classical = 1269.6294 (true_chitra 1270.5636, raman 1356.4074); B likewise 927.0084 for all three. C: lahiri 1021.5906, krishnamurti 1027.4016, surya_siddhanta 1019.3136 (distinct). Cause: pre-#1053 `AYANAMSHA_MAP` fell back to Lahiri for the A3-canonical ids `krishnamurti` / `surya_siddhanta_classical` (commit message of 29d1aa935, merged 2026-08-05). A and B vargas predate it (and F-A1, 09-05).

## B. F-8 evidence

### B.1 ga_dashas `incomplete` on B
- `asset_throughput(B, ga_dashas)`: state `incomplete`, rows_written 505,348, last_built_at 2026-08-05 20:55:06.32Z, last_error = "orphan-watchdog: heartbeat went stale while a substep plan was in flight. 0 substep(s) committed and 505348 data row(s) are present, but this route cannot prove the plan finished, so the asset was NOT promoted to 'lit'. ..." That text is the SAMĀPTI B-WATCHDOG-LIT branch (`cockpit/watchdog/route.ts`, `has_substeps=true`, state `building`, last_built_at older than 15 min). A is `lit` (471,767) and C `lit` (483,870).
- Plan: `pipeline/orchestrator/writers/ga_dashas.py` plans 35 (system x ayanamsha) sub-steps plus a 36th concurrency post-pass (which also writes the scope_cap sentinel). Heartbeat threshold 15 min.
- Data: `chart_dashas` for B has two builds. 984e5eab (2026-07-27 08:39-08:58Z; run 984e5eab, asset `complete`): lahiri, true_chitra, raman, all with post-pass annotations (192 rows each with `convergence_count_at_start`). 75ec8317 (2026-08-05 20:33:17-20:35:22Z): krishnamurti, surya_siddhanta_classical, 101,239 and 101,313 rows, **0 annotated**. No `build_runs` row exists for 75ec8317 or for any B run on 08-05 (B's runs: 07-27 x3, 08-07 x2, 09-06 x1); the 08-05 state flip predates `asset_throughput_state_audit` (starts 2026-08-22).
- Totals by chart: B 505,348; A 471,767; C 483,870. The differences follow birth data (largest in `mudda`, `chara_karaka`, `narayana`), not duplication: each of the 5 ayanamshas is present exactly once in B at about 100-101k rows, and no (chart, ayanamsha, system) slice is split across the two builds. B's 07-27 timeline shows 3-minute gaps where krishnamurti (08:52-08:55) and surya (after 08:58) would sit, consistent with those two having been computed on 07-27 and replaced on 08-05.
- Likely trigger (inference from timing): PR #1053 (merged 2026-08-05 01:45 IST) fixed the Lahiri fallback for exactly `krishnamurti` and `surya_siddhanta_classical`; B got a targeted two-ayanamsha re-run (about 14 of the 35 system x ayanamsha sub-steps, resumable plan) that was never completed with the post-pass. The watchdog tick at 20:55:06 also failed A's run c7b99de6 at 20:55:06.06Z.
- `integrity_check_sql` for ga_dashas: all four conjuncts are literal-scoped to `chart_id = '482012f1-...'` (migration 882 scoping, per its own SQL comment). It cannot report on B; `incomplete` is not derived from it. A and B also lack the `scope_cap` KP sentinel row C has (pre-SD-DASHA-1 builds).

### B.2 The 2026-09-19 ga_positions abort
- `build_runs` 59232059-953c-4fbc-9ebc-b5600e73b8d7: chart C, scope `asset_set`, target ga_positions, action rebuild, triggered_by `l3-lane-frozen-manifest-rebuild`, created 2026-09-19 22:48:37.60Z, `started_at` NULL, ended 23:00:05.96Z, state `failed`, `last_error` = "orphan-watchdog: run never dispatched", `stop_requested_at` and `pause_requested_at` NULL. Plan manifest (nirmana-run-manifest/v1, one wave, ga_positions, digest 33c7d7f8...) was frozen at creation.
- Its `build_run_assets` row: `aborted`, position 0, `started_at`, `ended_at`, `error` and disposition all NULL. That exact shape is the pre-#2782 watchdog UPDATE (`SET state='aborted'` with no `error`/`ended_at`; verified in `git show ac3ef565e`, the version live on 09-19). The Python preflight terminalizer and the post-#2782 route both set `error` and `ended_at`, so neither made this row. "No error text" = the asset-level text was never written; the run-level text exists.
- Not a person: no stop request, state never `running`/`stopped`. Not the guardian or a crash: `started_at` NULL, no running phase to reap. C's ga_positions throughput is unchanged (lit, 1,205, last_built_at 2026-09-07 08:37Z; no audit transition after 09-07).
- Pattern: 51 of 736 `build_runs` carry this exact `last_error`, none with `stop_requested_at`, across 16 distinct days (5 on 07-10, 24 on 08-03/04 for relay runs, 5 on 08-10, one on 09-19). The route says the run stays `planned` until the orchestrator itself starts it, and only the watchdog covers a run Cloud Run never claimed (`cockpit/runs/route.ts:388-445`, `lib/build/runDispatch.ts`).

### B.3 Repeat risk on C's S-L1 run
- ga_positions: the failure is in dispatch/pickup, independent of chart, so it can repeat. Since #2782 (09-30) the reaper records error text on both rows. A 10-minute `planned` window is the only exposure; nothing here changes C's data.
- ga_dashas: C's data is a single complete build (1f89fd4c, 09-07, 168 annotated rows per ayanamsha, scope_cap row present, lit at 20:14Z). `incomplete` recurs on any has_substeps asset whose heartbeat stalls over 15 minutes while `building`, or whose plan is cut off (B's case), because the watchdog cannot prove plan completeness. On 09-07 C's per-ayanamsha slices took 2-9 minutes each, inside the window.
- Also visible but out of scope: both 2026-10-01 runs for `ka_gochara_resonance` ended `failed` (the second: `DEP-ASSERT ... bg_transit_rules(receipt:stale)`).

## C. Not verified
1. Whether the July writer's emission equals today's minus F-A3 exactly. The offline model used current code and reproduces 38,620 and 24,400 to the digit, which is strong but is not July's git state (F-61/F-167 changed D7/D60 saptavargaja placement on 08-21/22).
2. Who/what launched the 08-05 B ga_dashas pass (build 75ec8317, no `build_runs` row) and whether it was cut off or intentionally partial; the 08-05 flip to `building` is unaudited. The #1053 link is timing-based.
3. Why 984e5eab's ga_dashas asset was marked `complete` (the plan completeness predicate was fixed 07-29, SATYA-DĪPA, after that run) and whether B's other 07-27 assets share the pattern.
4. Why the 09-19 run was never claimed: Cloud Run job/execution logs and `invokeRunJob`'s return are not visible to `suvarna_reader`. Whether the dispatch call returned OK, threw, or the creating request died after commit is unknown.
5. Consumers of the collapsed ashtakavarga/house_lord/D30 rows (whether anything downstream needs the 11 missing sign bindus per graha-varga, or whether the same values live in another table); not traced.
6. Why C's first 09-07 ga_vargas attempt failed its integrity check.
