---
artifact: DATA_DEPENDENT_ASSERTIONS_S_L1
version: 1.0
status: DRAFT-FOR-REVIEW
produced_by: worker for exec-suvarna
date: 2026-10-02
scope: docs only (read-only investigation; no code, test, workflow, migration or database write; DB access was SELECT-only via suvarna_reader)
changelog:
  - "1.0 (2026-10-02): first version. CI location facts for chart_query.integration.test.ts; sweep of tests, scripts and workflows that read live data and could flip when the S-L1 rebuild lands, per lane; live-in-CI list; not-verified list."
---

# Data-dependent assertions that the S-L1 rebuild can flip

Lanes covered (all draft PRs): #2851 argala, #2892 Gandanta/X1, #2890 band table/X2, #2854 tier constants plus #2941 tier honesty (stacked on #2854; #2852 is docs only), karaka trio #2878 + #2886 + #2883, #2893 Sun required_rupa (this worktree, including the pending Rahu/Ketu composite honest-null change and the SHADBALA_REQUIRED default removal).

Baseline read from production on 2026-10-02 (SELECT-only): SUN `required_rupa` = 5 on the canonical chart (INVARIANT row); `karaka_chara_position` subjects on the canonical chart include STRIKARAKA (35 rows) and no PITRIKARAKA; `chart_facts.verification_pass_status = 'single_pass'` holds 10,937 rows. So none of the lane data has landed yet.

Headline: no test or job that runs automatically on pull_request, push to main, merge_group or inside deploy.yml reads production data and would turn red from these lanes. The assertions that flip are manual-run (INTEGRATION=true) tests or workflow_dispatch/scheduled jobs. Details in sections 1 and 3.

## 1. CI location facts for chart_query.integration.test.ts (exact)

File: `platform/src/lib/retrieval/registry/layers/__tests__/chart_query.integration.test.ts`

The assertion: line 132, `expect(sunPivot?.['required_rupa']).toBe(5)`, inside the test at lines 114-136, `[native] graha_shadbala_total serves BOTH ratio and required_rupa on the same graha row (Gate B)`, which calls the real handler against the real DB for chart 482012f1.

The gate (file lines 23, 28, 30):

```
const INTEGRATION = process.env.INTEGRATION === 'true'
const describeIf = INTEGRATION ? describe : describe.skip
describeIf('chart_query (marsys://tool/L1/chart_facts_query) — live DB', () => {
```

Where it is collected and run:

| item | location | evidence |
|---|---|---|
| package script | `platform/package.json:11` | `"test": "vitest run"` |
| vitest config | `platform/vitest.config.ts:176-180` (project `node`) | `name: 'node'`, `exclude: [...SHARED_EXCLUDE, ...DOM_TEST_GLOBS]`; no `include` override and the file is not in either list, so the file IS collected (and then skipped by its own `describe.skip`) |
| workflow | `.github/workflows/ci.yml` | name "CI - Ganga Quality Gate"; triggers push [main], pull_request, merge_group, workflow_dispatch |
| job | `unit-tests` (display name "Unit Tests"), ci.yml:130-131; a required check on main per the comments in ci.yml | |
| job env | ci.yml:140-141 | `env: NODE_ENV: test` only. No `INTEGRATION`, no `DATABASE_URL`/`DB_URL`. The job has a `postgres:15.18` service container (ci.yml:147-158) but no env var pointing the test process at it, and it is seeded only for the Nirmana evidence tests |
| step | ci.yml:221 | `- run: npm test -- --reporter=verbose` |

Classification: **(c) skipped in CI.** It is never run against production, and never against a throwaway DB, by any workflow.

Evidence from a real run: main CI run 34594715170 (2026-09-11), job "Unit Tests", log line `↓ node src/lib/retrieval/registry/layers/__tests__/chart_query.integration.test.ts > chart_query (...) — live DB > [native] graha_shadbala_total serves BOTH ratio and required_rupa on the same graha row (Gate B)` (the down-arrow is vitest's skipped mark); job totals `Test Files 1082 passed | 70 skipped (1152)`, `Tests 11546 passed | 658 skipped | 2 todo`.

Who sets INTEGRATION=true: `grep -rn INTEGRATION .github/` finds exactly one setter, `.github/workflows/judgment-integration-nightly.yml:121` (`INTEGRATION: 'true'`, with `DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}` through the Cloud SQL Auth Proxy), job `d9-judgment-integration` (line 49), step at line 123: `npx vitest run src/lib/retrieval/registry/layers/__tests__/register_d9_judgment.integration.test.ts ...`. That workflow's header (lines 14-22) states the scoping is deliberate: INTEGRATION=true would light about 20 other `*.integration.test.ts` files, including this one, so it is applied to a single file path only. It is schedule (05:41 UTC) plus workflow_dispatch, not a required check. It does not run chart_query.integration.test.ts.

Post-merge / deploy: `deploy.yml` contains zero `vitest` invocations. It triggers on `workflow_run` of the CI workflow concluding success (deploy.yml:7-8, 219, 434) and its smoke steps are: `scripts/operator/end_to_end_smoke.sh` and `mcp_end_to_end_smoke.sh` (auth/HTTP probes only), and the "Puṛṇa inquiry signing and RLS candidate canary" (deploy.yml:1480-1527: HTTP 200 plus signing/RLS signals for `SMOKE_CHART_ID`; no L1 value is asserted). Therefore a production rebuild that makes `chart_query.integration.test.ts:132` red cannot block a deploy, and cannot block a PR. It only fails for someone running `INTEGRATION=true vitest run ...` by hand with a production `DATABASE_URL`.

Recommended fix (owner #2893): change line 132 to 6.5. Because the file is skipped in CI, editing it inside #2893 is CI-safe; the intent doc left it at 5 only so that a manual pre-rebuild run stays green. Update the comment at lines 110-113 and the stale "SUN required_rupa=5" comment in `platform/scripts/audit/doctrine_harness/lib/assertions.ts:1234` at the same time.

## 2. Sweep, per lane

Method: enumerated every test or script that can read live data (list below), then searched each for the lane's categories, keys, subjects, tiers and numbers. Rows marked "no flip" are listed so the coordinator can see they were checked.

Universe of live-capable assertions and where each runs:

| class | files | gate | CI status (evidence) |
|---|---|---|---|
| A. INTEGRATION=true TS tests (33 files; list from `grep -l "process.env.INTEGRATION"` over `platform`, `platform-mcp`) | e.g. chart_query, get_sensitive_degrees, get_nakshatra, get_dashas, get_structural_signals, get_yoga_firings, register_d9_judgment, wp18, L2/L3 suites | `describe.skip` unless INTEGRATION=true | skipped in `unit-tests` (run 34594715170 shows 658 skipped); only register_d9_judgment runs nightly (section 1) |
| B. TS tests gated on `DB_URL \|\| DATABASE_URL` | `address_resolver.integration.test.ts`, `L2_bodha/__tests__/graha_portrait.gate.integration.test.ts`, `traverse_chart_graph.gate.integration.test.ts`, `build.integration.test.ts`, `sessions.provenance_stamp.integration.test.ts` | `describe.skip`/`skipIf` | skipped: `unit-tests` job env has no DATABASE_URL/DB_URL (ci.yml:140-141) |
| C. TS tests gated on a live MCP URL | `mcp_visibility.integration.test.ts`, `m8_e2e_proof.test.ts` (INTEGRATION block), `mcp_stub_engines.integration.test.ts` | `MCP_BASE_URL` + `MCP_API_KEY_CLIENT` | skipped; `gh secret list` shows no such secret; platform-mcp's full suite is not run in CI at all (ci.yml:1562 comment; only named test files in `density-census`) |
| D. Python live tests | `tests/l2/conftest.py db_conn` (skips without DATABASE_URL), `ga_writers/__tests__/test_vimshottari_independent_verifier.py` smoke (`skipif(_live_conn() is None)`), `tests/test_chart_reader_v4.py` (`DBURL`), `-m integration` tests | env var / marker | ci.yml:1529-1535 runs `pytest tests/ ... -m "not integration"` in `governance-gates` with no DATABASE_URL, so all skip. `shad-darshana-circularity-guard.yml` runs one `-m integration` file live (LEL invariance, not lane data) |
| E. Live scripts in workflows | doctrine_harness (ci.yml `census-battery`, `if: workflow_dispatch`, needs `MARSYS_MCP_KEY`), `elev-serving-gates.yml serving-gates-live` (dispatch, needs `MARSYS_MCP_URL`), `tap-ci.yml tap-db-gates` S-13 and TAP-7 (dispatch-only steps, `PROD_DATABASE_URL`), `verification-invariant.yml` (nightly, PROD), `judgment-integration-nightly.yml` (nightly, PROD), `samiksha-daily.yml` (nightly, PROD; ledger sweep), `gochara-smoke-probe.yml` (every 6 h; needs MARSYS_MCP_URL, absent), `pariprashna-post-deploy-smoke.yml` (after deploy; one real chat turn on 1c826d5a) | triggers as listed | `gh secret list` (repo level) shows PROD_DATABASE_URL, SMOKE_CHART_ID, SMOKE_SESSION_COOKIE and no MARSYS_MCP_URL / MARSYS_MCP_KEY, so the live-MCP jobs self-skip |
| F. Throwaway / seeded DB | `db-integration-tests` job, the Nirmana steps in `unit-tests`, `PRATIJÑĀ v4 Fixture Property Tests` (restores a committed export of chart 482012f1, `python-sidecar/tests/fixtures/pratijna_v4_snapshot`), `fresh_chart_smoke.yml` (weekly; schema + reference tables dumped from prod into a local Postgres, then builds a fixture chart with branch writers; asserts every asset reaches lit, no row counts) | local DB URLs | not production; unaffected by a production rebuild |

### 2.1 #2893 Sun required_rupa (5 -> 6.5; Rahu/Ketu composite honest nulls; SHADBALA_REQUIRED default removal)

| # | file:line | asserts | flips? | runs in CI against live? | fix / note |
|---|---|---|---|---|---|
| S1 | `platform/src/lib/retrieval/registry/layers/__tests__/chart_query.integration.test.ts:132` | live SUN `required_rupa` toBe(5) | **YES, 5 -> 6.5** | No: class A, skipped (section 1) | set 6.5 in #2893 (CI-safe) |
| S2 | same file `:118-128` | at least 7 rows carry ratio and required_rupa; each ratio row has required_rupa and a fact_id | no (nodes carry neither; unchanged) | no | none |
| S3 | `platform/scripts/audit/doctrine_harness/lib/assertions.ts:1244-1253` (B_shadbala_ratio) | ratio rows > 0 and required_rupa rows > 0 on the live MCP | no (presence only); comment at :1234 says SUN=5 (stale) | no: `ci.yml census-battery`, dispatch only, secret absent | refresh comment |
| S4 | `platform/src/lib/retrieval/registry/layers/__tests__/get_dasha_lord_capability.integration.test.ts:77` | `shadbala_percentile` not null (rupa-based) | no | no (class A) | none |
| S5 | `platform/src/lib/pariprashna/corpus/fixtures.ts:567-585` (`remedial-005-rahu-weak-composite-lagna`) | fixture premise: Rahu has very low composite strength, RAH_MEAN_IN_HOUSE_1 bphs_weighted 0.0518, cites fact ids 6399aab3bb099fa8 etc. on 1c826d5a | **premise flips**: node composite rows become one floored null row per (node, house, ayanamsha); delete-then-insert also replaces the cited fact ids | no: used only by manual `platform/scripts/pariprashna/s3_live_corpus_run.ts` (not referenced by any workflow) | bump `CORPUS_FIXTURE_SET_VERSION` and re-ground after the rebuild; owner Pariprashna corpus |
| S6 | `platform/src/lib/retrieval/registry/layers/chart_facts_query_wp13f.test.ts:160-196`, `platform-mcp/src/__tests__/registry_bridge_r5w3_judgment_and_portrait.test.ts:429-498` | `required_rupa` = 5 / 5.0 | no: mock fixtures of the reading mechanism, not live | runs in CI, but on mocks | none required |
| S7 | `evals/omega7/harness_runs/DC-C-17.json` | recorded output containing SUN required_rupa | no: static recorded artifact, no test reads it | no | stale record only |
| S8 | `platform-mcp/src/resources/vidhi/dossier_slices/*_482012f1.json` | contain the string `required_rupa` as a tool argument handle, not a value | no | no | none |
| S9 | any test on `RAH_MEAN_IN_HOUSE_*` / `graha_in_house_composite_strength` values on live data | searched `_IN_HOUSE`, `bphs_weighted`, `cross_formula_divergence` across tests, scripts, platform-mcp, evals | none found besides S5 and the lane's own fixture tests | n/a | none |

### 2.2 #2851 argala (156 new `argala_graha_natal` rows canonical; `argala_natal_matrix` value 1.0 -> NULL on 3,444 unoccupied-source cells; count_sql edits in migration 1219)

| # | file:line | asserts | flips? | CI against live? | fix / note |
|---|---|---|---|---|---|
| A1 | `platform/scripts/audit/tap/s13_coverage_matrix_live.ts:50-70` against `platform/src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts` (`CHART_FACTS_CATEGORIES`, :110 argala_natal_matrix, :260 net_argala_per_varga, :327 virodha_argala_natal_matrix) | FAIL if live `SELECT DISTINCT fact_category` for 482012f1 has categories absent from the static list | **gets worse**: `argala_graha_natal` is absent from the static list and neither #2851 nor #2870 adds it. Already FAIL today: measured 219 live vs 225 static, missing `combustion_per_varga`, `convergence_count` (same result on origin/main 96549f943) | `tap-ci.yml` job `tap-db-gates`, step "S-13 live coverage matrix [dispatch-only]" with `PROD_DATABASE_URL`; workflow_dispatch only (not PR, push, merge_group) | add `argala_graha_natal` to the list and to the category-to-tool map near coverage_matrix.ts:452 (get_argala); owner #2851 (or the L1 coverage owner). Not verified whether other tests constrain additions |
| A2 | `L1_ganita/__tests__/get_structural_signals.integration.test.ts:25-45` | per-domain category presence (net_argala_per_varga etc.) | no (net_argala_per_varga unchanged; the new category is not in get_structural's list, `get_structural_signals.ts:67,77`) | no (class A) | none |
| A3 | `platform/scripts/census/elev_gates/w1_bare_empty_census_gate.ts:103` | keyword "argala" returns non-empty | no (presence) | no: live mode is dispatch-only and secret absent; the PLAN-mode half runs in CI without live data | none |
| A4 | tests on argala_natal_matrix counts or the 1.0 value | searched `argala` across all test, script, eval and platform-mcp trees | none live. `get_argala.ts:7` carries a comment with 41,760 rows (stale after rebuild; comment only) | n/a | none |

### 2.3 #2892 Gandanta / X1 (graha_gandanta: 3 deg 20 min canonical; `strict_0_48` variant rows; 50 variant is_gandanta rows per chart; Abhinandan 6 readings flip false -> true)

| # | file:line | asserts | flips? | CI against live? | fix / note |
|---|---|---|---|---|---|
| G1 | `L1_ganita/__tests__/get_nakshatra.integration.test.ts:27` | identity domain (limit 2000) includes graha_nakshatra_join, graha_pada_join, graha_gandanta | no. Measured canonical identity rows today: 700 + 200 + 50 = 950; +50 variant rows stays far under the 2000 cap | no (class A) | none |
| G2 | tests counting `is_gandanta` rows, asserting `formula_id`, or asserting `strict_0_48` | searched `is_gandanta`, `graha_gandanta`, `strict_0_48` | none live | n/a | none |
| G3 | readers returning two rows per (subject,key) | `get_nakshatra` serves both variants unpinned | not a test; reader determinism is the formula-pins work in #2866/#2870 (held) | n/a | coordinate with #2866 |

### 2.4 #2890 band table / X2 (ga_medical `indication_strength` 15 canonical rows mild -> moderate; ga_vastu `direction_impact` 0 canonical rows change; ga_condition D1-fallback guard)

| # | file:line | asserts | flips? | CI against live? | fix / note |
|---|---|---|---|---|---|
| B1 | `platform/scripts/census/elev_gates/w1_bare_empty_census_gate.ts:116` (medical) | `ganita_medical_get` returns rows | no (row count unchanged) | live mode dispatch-only, secret absent | none |
| B2 | tests on `indication_strength`, `mild`, `moderate`, `direction_impact`, `condition_score` over live data | searched TS (platform, platform-mcp), scripts, evals, Python tests | none live; the Python ga_medical/ga_vastu/ga_condition tests are fixture or golden based (`tests/_ga_condition_canonical_inputs.py`) | n/a | none |
| B3 | ga_condition build guard (writer, not a test) | raises if a D1 fallback would be used on a chart that has divisional rows | build-time risk on 1c826d5a and cb73cd3d (90 rows ran on the fallback) if ga_vargas rows exist at ga_condition time | n/a | confirm ga_vargas precedes ga_condition in the rebuild order (DAG already has ga_condition depending on ga_vargas) |

### 2.5 #2854 tier constants and #2941 tier honesty (single_pass -> single; classical_match, documented_approximation, computed_extension, floored, single replace two_pass_verified where nothing double-checked; canonical after-rebuild: two_pass_verified 265, classical_match 1,650, documented_approximation 7,800, computed_extension 35, floored 85, single 10,335)

| # | file:line | asserts | flips? | CI against live? | fix / note |
|---|---|---|---|---|---|
| T1 | `L1_ganita/__tests__/get_sensitive_degrees.integration.test.ts:80` | live `sensitive_point_yogi` rows are exactly `{two_pass_verified}` | **YES (#2941)**: 60 canonical rows two_pass_verified -> classical_match (ga_sensitive_degree, per tiers_evidence) | no (class A) | expect `classical_match`; owner #2941 |
| T2 | same file `:98` | subject YOGI page has `unverified_rows_in_page` toBe(0) | **YES (#2941)**: the tool counts `tier !== 'two_pass_verified'` as unverified (`get_sensitive_degrees.ts:128`), so it becomes 60 and an `unverified_note` appears | no | change expectation or the tool's notion of unverified; owner #2941 |
| T3 | same file `:56-57,:81-83` | unverified > 0; `sensitive_degree_check` tiers are `{pending_w3_verification, single}` | no (sensitive_degree_check is not in the transition list) | no | none |
| T4 | `platform/scripts/audit/verification_invariant.py:143-167` (`check_vocabulary_conformance`), `:98-133` (`check_claim_vs_evidence`) | no row holds a deprecated alias such as `single_pass`; verified-tier rows must fall inside a declared examined predicate | **flips to a better state**: chart_facts `single_pass` 10,937 rows -> 0 after #2854 + #2941 on all charts; `l1_tajik_varsha_year_lords` 475 two_pass_verified -> classical_match removes that claim | **YES, live-in-CI**: `verification-invariant.yml`, schedule 04:17 UTC, PROD_DATABASE_URL; non-blocking | see section 3 |
| T5 | `get_dashas.integration.test.ts` (:75 name only), `get_sensitive_points.integration.test.ts`, `get_sade_sati`, `get_panchanga`, `get_positions_upagraha_sandhi`, `get_tara_chandra_bala` | pagination, ties, row counts (e.g. 221 panchanga rows, 195 tara rows, 70 and 25 esoteric rows) | no: tier changes only, row sets unchanged (expected_row_count_changes 0) | no (class A) | none |
| T6 | live tests asserting a `single_pass` value | searched; only `tests/l2/test_n8_earned_signal_detectors.py` (throwaway DB it creates itself) | no | n/a | none |
| T7 | write-side CHECK constraints | chart_dashas/chart_divisionals CHECK admits `{two_pass_verified, classical_match, divergent_flagged, single}` (`verification_vocab.py:187-193`); chart_facts has no CHECK | no write failure expected (documented in the vocab file) | n/a | none |

### 2.6 Karaka trio #2878 (ga_sensitive/ga_vargas relabel), #2886 (chart_dashas roles), #2883 (karaka_web_per_varga order-independent, +1,074 canonical rows across 5 ayanamshas)

kn_rao ranks 5-8 become PITRIKARAKA / PUTRAKARAKA / GNATIKARAKA / DARAKARAKA (was PUTRA / GNATI / DARA / STRI); STRIKARAKA subject disappears; `strikaraka_alias` key appears on DARAKARAKA; ranks 1-4 (ATMA, AMATYA, BHRATRI, MATRI) and the parashari 7-scheme labels are unchanged. Dasha role columns change on 185,883 canonical rows.

| # | file:line | asserts | flips? | CI against live? | fix / note |
|---|---|---|---|---|---|
| K1 | `platform/src/lib/retrieval/address_resolver.integration.test.ts:44-49, :80-85` | `karaka('AK')` = Moon house 11 (native), Mercury house 11 (Abhinandan) | no (AK is rank 1) | no: class B | none |
| K1b | `platform/src/lib/retrieval/address_resolver.ts:146-154` (reader, not a test) | `KARAKA_CODE_TO_SUBJECT`: SK -> STRIKARAKA, PK -> PUTRAKARAKA, DK -> DARAKARAKA | semantics shift after the relabel (SK resolves nothing; PK is one rank later in the 8-scheme); none of the three karaka PRs edits this file; #2870 does (held) | n/a | confirm #2870 covers the new labels; owner #2878 / #2870 |
| K2 | `platform/python-sidecar/tests/test_chart_reader_v4.py:208-216` | DARAKARAKA `karaka_school` values equal both schools | no (DARAKARAKA still exists in both schools) | no: needs env `DBURL`, not set anywhere in `.github` | none |
| K3 | `platform/python-sidecar/ga_writers/__tests__/test_vimshottari_independent_verifier.py` live smoke (`skipif(_live_conn() is None)`, around line 528+) | independent Vimshottari derivation agrees with stored chart_dashas, zero divergent | no, provided #2886 is merged before the rebuild: #2886 removes the transcribed role table and moves the two role columns to NOT_INDEPENDENTLY_CHECKABLE. Without #2886 against rebuilt data the role columns would diverge | no (DATABASE_URL gate) | order: merge #2886 before the dasha rebuild |
| K4 | `platform/scripts/audit/doctrine_harness/lib/assertions.ts:1175-1214` (B_karakamsha), `w1_bare_empty_census_gate.ts:87` (keyword karaka) | karakamsa_position / karaka rows resolvable | no (presence; AK unchanged) | no (dispatch, secret absent) | none |
| K5 | `platform/src/lib/pariprashna/corpus/fixtures.ts:460-480` (`cross-domain-005`, Mercury Atmakaraka on 1c826d5a) | premise Atmakaraka = Mercury | no (rank 1) | manual live corpus run only | none |
| K6 | `get_dashas.integration.test.ts:45-71` byte budget 1024 on the current-dasha row | payload size | no: `COMPACT_FIELDS` (`get_dashas.ts:125-130`) excludes both role columns and `citation_human` | no (class A) | none |
| K7 | tests pinning STRIKARAKA, PUTRAKARAKA, PITRIKARAKA, `karaka_role_at_period`, `karakas_active_during_period`, or `karaka_web_per_varga` counts on live data | searched whole repo | none live (hits are DDL in `roles_rls_b002_gaps.db.test.ts:192`, fixture tests the lanes edit, and `formula_pins_order.integration.test.ts` in held #2866/#2870 which asserts only "both schools served, canonical first, paging stable" and survives the relabel) | n/a | none |

### 2.7 Counts, floors and golden snapshots (cross-lane)

| item | finding |
|---|---|
| `asset_registry.target_floor` / `count_sql` vs live counts | no automated test compares live per-asset counts to floors (searched `target_floor` in tests and scripts: migration-text tests, `asset_runner` fixtures, and L2 `test_b6_eval_harness.py` which is `-m integration`). #2851 leaves floors untouched (re-declared after S-L1 in one registry migration); it narrows ga_strength and ga_condition `count_sql` (migration 1219) |
| `platform-mcp/test/accuracy/fixtures/abhisek-mohanty-golden.json` | generated from live by `regenerate_golden.ts`; `run.test.ts` self-checks offline (`expected_min_rows`); categories do not include any lane category; platform-mcp full suite is not in CI |
| `platform-mcp/src/resources/vidhi/dossier_slices/*.json`, `platform/src/generated/*`, `evals/omega7/harness_runs/*` | static snapshots or code-derived; no test compares them with live data |
| PRATIJÑĀ v4 snapshot fixture (`ci.yml:833-889`) | committed export of 482012f1 restored into a throwaway DB; unaffected until someone regenerates it |

## 3. Live-in-CI list (owner lane and fix)

Automatic triggers (nightly or scheduled, production DB through Cloud SQL Auth Proxy; none is a required check, none gates a PR or deploy):

| job | trigger | assertion (file:line) | lane | effect of the rebuild | action |
|---|---|---|---|---|---|
| `verification-invariant.yml` | schedule 04:17 UTC + dispatch | `platform/scripts/audit/verification_invariant.py:143-167` vocabulary conformance; `:98-133` claim vs evidence | #2854, #2941 | currently 7 FAIL / 11 (run 36852037689, 2026-10-01): chart_facts 10,937 `single_pass`, bodha_cgm_edges 1,115, bodha_cgm_nodes 951, bodha_msr_signals 3,262 `single_pass`, plus unpredicated claims on bodha_msr_signals (14,663), kala_tithi_pravesha (240), l1_tajik_varsha_year_lords (475). After S-L1 on all charts the chart_facts and l1_tajik lines clear (up to 7 -> 5 FAIL); the bodha and kala lines remain (S-L2 and out of scope). No new red is introduced | none needed; note expected improvement so a partial clear is not misread |
| `judgment-integration-nightly.yml` | schedule 05:41 UTC + dispatch | `register_d9_judgment.integration.test.ts` | none of the 8 lanes | already red (20 of 22 failing, run 36857641103): `Could not resolve frame "lagna" for chart 1c826d5a ...: no graha_position/LAGNA sign fact found`. Its assertions are structural (key presence, types, domain karaka map); no lane value is pinned. May turn green when Abhinandan's positions are rebuilt | none for the lanes |
| `shad-darshana-circularity-guard.yml` | nightly + push to main on ka_* paths | `tests/l3/test_ka_jivana_parva_circularity_guard.py` (-m integration) | none | LEL invariance, not an L1 value | none |
| `samiksha-daily.yml` | nightly | prediction-ledger sweep | none | not L1 data | none |

Manual dispatch only (live prod, hosted in CI):

| job | assertion | lane | effect | action |
|---|---|---|---|---|
| `tap-ci.yml tap-db-gates`, S-13 step | `platform/scripts/audit/tap/s13_coverage_matrix_live.ts:50-70` | #2851 | already FAIL (2 missing categories); gains `argala_graha_natal` as a third | add the category to `coverage_matrix.ts` (owner #2851) |
| `tap-ci.yml`, TAP-7 step | `tap7_distribution_gates.ts` (graha_shadbala_cheshta distinct values, ishta/kashta, sade_sati_cycle duplicates) | none | not affected (cheshta, ishta, kashta values and tiers-only changes) | none |
| `ci.yml census-battery`; `elev-serving-gates.yml serving-gates-live` | doctrine_harness, K1/W1 gates | #2893, karaka (presence checks only) | no flip; also self-skips (MARSYS secrets absent) | none |

Not in CI but WILL flip when run by hand against rebuilt production (INTEGRATION=true):

| file:line | lane | fix |
|---|---|---|
| `platform/src/lib/retrieval/registry/layers/__tests__/chart_query.integration.test.ts:132` | #2893 | 5 -> 6.5 in #2893 |
| `platform/src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_sensitive_degrees.integration.test.ts:80` and `:98` | #2941 | expect classical_match; adjust unverified count |

Bottom line for the coordinator: no assertion found that is both live and automatic and that goes newly red from these lanes. Required checks (`Unit Tests`, `Governance Gates`, etc.), merge queue and deploy.yml are unaffected by the data change itself.

## 4. Not verified

1. Repo-level secrets only were listed (`gh secret list`); organization-level or environment-scoped secrets (for example MARSYS_MCP_URL, MARSYS_MCP_KEY, MCP_BASE_URL) were not checked. If any exists, the live-MCP jobs in section 3 would actually run.
2. The 33 INTEGRATION files were searched by lane terms and numeric assertions, not each read end to end. L2/L3 suites (wp12a, wp12b, coverage_receipt, date_tz_sweep, temporal_activation, query_life_arc_dedup) and instrument/grounding/mcp_primitives were only grepped for lane terms (none found).
3. Python tests were selected by DB-access patterns (362 files with DATABASE_URL/psycopg connect; 109 test files) and grepped for lane terms; fixture-based Python tests that the lane PRs edit were not re-run.
4. Tests in other held PRs (#2866 formula pins, #2870 tool-text vehicle, #2908 condition served) were read only where named (`formula_pins_order.integration.test.ts`); the 2,293-test governance suite and the TAP-6 static `two_pass_verified_literal` rule (a required, code-level check that tier honesty touches) were not analysed for data effects.
5. The weekly `fresh_chart_smoke.yml` and the post-deploy `pariprashna-post-deploy-smoke.yml` (a real chat turn on 1c826d5a) were read for assertions: neither asserts a lane value, but a mid-rebuild data gap on Abhinandan could make the latter fail for reasons unrelated to values; not tested.
6. The S-13 comparison replicates the script's logic in Python against a read-only `SELECT DISTINCT` and origin/main's `coverage_matrix.ts`; the script itself was not run.
7. The ga_condition fallback guard (B3) and the ordering of ga_vargas relative to ga_condition in a rebuild were not exercised.
8. Production was read only to establish the baseline in the header, section 2.3 (identity row counts) and section 2.5/3 (tier counts, S-13 categories). Counts for post-rebuild states come from the lanes' own hooks and evidence files (`tiers_evidence_v1_0.json`, `sun_required_rupa.json`, `gandanta.json`, `band_table.json`, `karaka_*.json`, `argala.json`), not from measurement.
9. Adjacent, not a data flip: each lane regenerates `platform/src/generated/nirmana-writer-digests.json` and `capability_estate_census.json`, so merging the lanes one after another will make the later PRs' committed digests stale (`provenance_inventory --check` runs in `governance-gates`); expect rebases and regenerations in the merge order.
