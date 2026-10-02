# Level-wave dispatcher (Suvarna E5.3)

`platform/scripts/governance/suvarna_level_wave.py`, section 2. Builds ONE frozen run manifest
(`nirmana-run-manifest/v1`) for an explicit list of assets, with waves derived from the registry's `depends_on`,
and dispatches it through the existing runner path. It replaces the single-asset
`platform/scripts/dispatch_frozen_rebuild.py` for multi-asset rebuilds; that script is untouched.

## Status: NEVER EXECUTED IN PRODUCTION above 17 assets / 1 wave

The largest run on record is 17 assets in one wave (L0, 2026-09-04). No multi-wave manifest and no 23-asset run has ever
executed; the only 2-wave manifest in history failed the image-skew check. The runner supports N assets and waves
structurally (read, not executed). The logic is proven offline with fakes and fixtures. The SQL the script mirrors
(candidate, closure, dependency, run-asset, E5.9 catalog) was exercised once against a real schema, the local rehearsal
cluster, in dry-run form (see "Rehearsal exercise"). Nothing has touched production. Exec Suvarna runs it.

## MANDATORY before the first --commit: the LIVE dry run

The LIVE dry run (INSERT then ROLLBACK against the real database, run by the operator session) is MANDATORY before the
first --commit. It prints the live wave list, the live manifest digest, the outside dependencies and the confirm token. Any
wave list in this README is indicative only (it is computed from fixture rows), never a plan to copy.

Indicative `bo_*` list (23 assets, 9 waves; from the registry seed and the 16 rehearsal-registry rows that carry a
`depends_on`; the live registry decides): w0 bo_arudha bo_laksana bo_nakshatra_semantic bo_special_lagna bo_sudarshana
bo_vargottama_dhana; w1 bo_bimba bo_grounding bo_samskara; w2 bo_karanajala; w3 bo_cgm_motifs bo_cgm_paths
bo_laksana_rerank; w4 bo_sangati bo_yantra_mechanism; w5 bo_cdlm_summary bo_drishti bo_pratijna bo_upaya; w6 bo_anveshana;
w7 bo_chart_gestalt bo_pramana_mapa; w8 bo_samvada.

## Manual step before every campaign: the deployed job sha

Compare the committed inventory's job sha with the deployed job image sha before every campaign. The inventory the digests
come from is read at `--deployed-sha`; `--deployed-job-sha` is the LIVE deployed job image sha, read by the operator at
launch (Exec's LC-1 gate). Use the image / `DEPLOY_SHA`, never a deploy run's `head_sha`: Trap 103, the deploy run's
`head_sha` metadata can disagree with the real `DEPLOY_SHA`. The script resolves both to full commits and refuses
(`JOB_SHA_MISMATCH`) unless they are the same commit, and prints the sha on every receipt. For wave-by-wave it re-reads
`--job-sha-file` (a file the operator's gate keeps holding exactly one 40-hex sha; validated at launch, in every mode, and at every re-read; the script never calls gcloud) before every wave
and refuses (`JOB_SHA_CHANGED`) if the deployed image changed mid-campaign. A `--deployed-digests-file` has no provenance to
check, so it works for a dry run only.

## Use

```
DATABASE_URL=... python3 platform/scripts/governance/suvarna_level_wave.py \
    --chart-id 482012f1-710e-4a25-994a-93821f5871aa \
    --assets bo_laksana,bo_bimba,...          # or @file, or repeated --assets; an explicit list, never a level
    --deployed-sha <commit whose inventory = the deployed image's> --deployed-job-sha <live job image sha>
    [--mode single-run|wave-by-wave] [--with-footprint]                   # dry run (default)
```

The dry run runs the whole transaction (advisory lock, active-run check, registry re-read, dependency check, both
INSERTs) and then ROLLBACKs. A real run adds `--commit --confirm <token> --mode ...` (and `--pause-dir` + `--job-sha-file`
for wave-by-wave). The token is the existing `<SUBJECT>_FROZEN_REBUILD` convention with the subject bound to the manifest:
`<N>ASSETS_<first 12 hex of the digest, upper>_FROZEN_REBUILD`; a registry change moves the digest and so the token.

Output is JSON lines, flushed per event: `run_committed` (with the run_id, the moment the COMMIT succeeds),
`run_dispatched`, `wave_dispatched`, `wave_ended`, `hook_*`, `dispatch_failed`, then a final `summary` / `refused` / `error`
line that also lists every run committed so far. A database error or any exception ends in that JSON line, never a
traceback, so the operator can always find a running run by its run_id.

## Exit codes

| code | meaning |
|---|---|
| 0 | dry run done, or every wave completed |
| 1 | `DATABASE_URL` missing |
| 2 | bad input, or an internal inconsistency (nothing dispatched) |
| 3 | dispatch failed after the run was committed (it is terminalised, or the summary carries a chart-blocking warning); in wave-by-wave too (`DISPATCH_FAILED`) |
| 4 | a gate refused (JSON `refusals`) |
| 5 | wave-by-wave campaign stopped (refusal, operator stop, run or asset not complete) |
| 6 | unexpected exception or database error (`committed_runs` lists every run committed so far). A connection that dropped during COMMIT is reported as `COMMIT outcome unknown` with the run id: run the `ACTIVE_RUN` check before relaunching (never read as "no run was committed") |
| 7 | interrupted (SIGINT / SIGTERM): the summary lists the runs committed so far and the chart-blocking warning: one not yet dispatched is `planned` and BLOCKS the chart until dispatched or terminalised |

## What it builds

* Manifest: byte-identical in shape to `dispatch_frozen_rebuild.build_manifest` (a one-asset input gives the same
  manifest and digest, golden-tested). `scope='asset_set'`, `scope_target` = the plan joined by commas, `waves` = the
  derived levels, one `assets` entry per plan id in plan order, `expected_code_digest` from
  `platform/src/generated/nirmana-writer-digests.json`. Digest = sha256 of the canonical JSON, the runner's own.
* Waves: wave(a) = 0 when a has no ordering dependency inside the requested set, else 1 + the largest wave of its in-set
  ordering dependencies (the longest path). An in-set ancestor reached THROUGH an out-of-set asset also orders (A depends
  on E outside the set, E depends on B inside it: A comes after B); the upstream closure is read from the registry for
  that. A cycle, through outside assets too, is an error. Ids inside a wave are sorted.
* Only `per_chart` assets: a global asset is refused (`NON_PER_CHART_SCOPE`).

## Refusals (exit 4, JSON, nothing inserted)

| code | when |
|---|---|
| `IMAGE_SKEW` / `CODE_DIGEST_UNAVAILABLE` | image skew: an asset's writer digest in the checkout differs from, or is absent in, the deployed image's inventory |
| `DEPLOYED_DIGESTS_UNAVAILABLE` | no `--deployed-sha` / `--deployed-digests-file`, or it can not be read |
| `DEPLOYED_JOB_SHA_REQUIRED` / `JOB_SHA_MISMATCH` / `JOB_SHA_UNRESOLVABLE` | the live job sha is missing, unresolvable, or not the commit the inventory comes from |
| `JOB_SHA_FILE_UNREADABLE` / `JOB_SHA_CHANGED` | the job-sha file is unreadable, or names another commit than the pinned one (checked at start and before every wave) |
| `DEPLOYED_BINDING_UNVERIFIED` | `--commit` with a digests file instead of `--deployed-sha` |
| `DEPENDENCY_NOT_READY` | a declared dependency OUTSIDE the set is not lit, or has no fresh receipt (services need only `service_ok`). The outside dependencies of every wave are checked, in the dry run too and before wave 0 is inserted in wave-by-wave mode |
| `REGISTRY_ROW_CHANGED` | a registry-row digest at the insert differs from the one the manifest was built from (re-read in the insert transaction) |
| `REGISTRY_ROW_INVALID` / `NON_PER_CHART_SCOPE` | missing, inactive, no writer, service, or not per_chart |
| `ACTIVE_RUN` | a planned/running/paused run exists for the chart |
| `FAMILY_ASSET` | `ka_gochara*`, `ka_vedha_gochara*`, `gochara_*`, `bg_gochara_*`, `kala_gochara_*` (always), or any member of `FAMILY_ASSETS.json` `family_set` |
| `SPLITS_FAMILY` | part of a declared family list without the rest |
| `FAMILY_FILE_UNREADABLE` | the file at `--family-ref` exists but is unreadable or malformed. Never fails open |
| `FAMILY_FILE_MISSING` | the file is not on the ref and the run is a `--commit` (stays refused until `FAMILY_ASSETS.json` is on origin/main) |
| `FAMILY_REF_STALE` / `FAMILY_REF_UNVERIFIED` | the local `origin/main` is not the remote tip (`git ls-remote`, read-only); for a commit the ref must be verified fresh. The ref sha used is printed |
| `STALE_HOOK_FILES` | the pause directory already holds `after-wave-*` files; nothing is deleted |
| `CONFIRM_TOKEN_MISMATCH` | `--commit` without the exact token |

### What the family set means, and who is in it (strategist rulings, 2026-10-02)

The family set is what the WAVE tool refuses. Family assets and their readers are rebuilt and certified ONE AT A TIME by the
production session with the single-asset dispatcher, each under a stage the strategist approves (Pravaha's own assets only by
Pravaha). The wave tool is for level waves of non-family assets (first use: the 23 bo_* assets).

`FAMILY_ASSETS.json` (draft `0.1-draft`, branch `suvarna/engine-E6.3-family`, 21 members) now includes, beyond the five R8 names
and the 13 other readers: `ka_yojaka` (Sangam's stale prerequisite), `ka_gochara_v3_century_materialize` (Gochara's century
writer) and `ka_moorti_nirnaya` (Pravaha's gochara writer, not covered by any name pattern). `ka_kota_chakra` is deliberately not
in the set (that reader is ours by agreement). None of the 23 bo_* assets is a member; a test pins that.

## Stop hook between waves

The runner executes every wave of one manifest as one run and has **no hook between waves**: it schedules from each
asset's `depends_on`, and wave boundaries are informational. The frozen runner is not touched, so the hook lives here:

* `--mode single-run`: one manifest with all waves, one run. **No pause is possible.** A documented limitation.
* `--mode wave-by-wave`: one run per wave, each manifest holding only that wave (earlier waves are ordinary outside
  dependencies, required lit+fresh by the dependency check and the runner's DEP-ASSERT). After each wave the dispatcher
  writes `after-wave-<k>.pending.json` (what finished, the wall times, the next wave) and continues only when
  `after-wave-<k>.continue` holds exactly the token in that file. The token is bound to the finished run: its run_id and
  its assets' end times, which exist only once the wave has ended, so no token in the dry-run output, the manifest or a
  file written beforehand can release a wave. The pause directory is created 0700 and `pending.json` 0600. A `.continue` that exists but does not yet hold the token (empty, half-written) is re-read a few times before it counts as a wrong token. A `.continue` or `.stop` that already exists when the wave is reported
  finished, or any `after-wave-*` file in the pause directory at launch, is REFUSED (never deleted: remove it and
  relaunch). `.stop`, a wrong token or the timeout stop. A run that does not end `completed` stops the campaign before the pause. An asset counts as built only when
  `build_run_assets.state` is `complete` AND `asset_throughput.state` is in `GOOD_THROUGHPUT_STATES` (`lit`, `mature`,
  `dormant`, `service_ok`: the runner's own success allowlist; the runner writes `complete` even for an `incomplete`
  build, so it proves nothing alone) AND `disposition` is `build`. This holds for the LAST wave too, which no dependency
  check ever re-reads. A no-delta skip (`disposition = skip_no_delta`, state `complete`) is not success unless the asset is
  named in `--declared-skips`; skipped assets are always reported. Any other disposition stops the campaign.

## --force-execute (OFF by default)

The delta-skip: an unchanged writer re-dispatched without force no-op-completes and emits no new receipt
(asset_runner.py ~1141-1160); L0_STATE.md D-L0-B documents it. Force bypasses it for every asset of that run. The runner reads
`NIRMANA_FORCE_EXECUTE` (`1`/`true`/`yes`) inside the job container, per run (`runner.py` `execute_run`); there is no manifest
field. `--force-execute` therefore sets it for ONE execution with the Cloud Run override
`gcloud run jobs execute ... --update-env-vars=NIRMANA_FORCE_EXECUTE=1` (verified against the local gcloud 576.0.0: the flag is
accepted next to `--args`, and a malformed value is rejected by the same parser). Rules: exactly one asset in the plan
(`FORCE_MULTI_ASSET`), never a family asset, name pattern or `family_set`, even alone (`FORCE_FAMILY_ASSET`); a real dispatch
needs `--commit` and the force-bound confirm token (`<N>ASSETS_<digest12>_FORCE_FROZEN_REBUILD`, different from the normal
token, so neither confirms the other); a dry run with the flag previews the force token and dispatches nothing. `force_execute`
is in the dry-run summary and every receipt and event.

### Force: image check, and what is verified afterwards

* At launch (dry run included) the pinned job sha's `runner.py` must read `NIRMANA_FORCE_EXECUTE` and its `asset_runner.py` must
  gate the delta-skip on `not force`; otherwise `FORCE_NOT_SUPPORTED_BY_IMAGE`. An image built before the O-wave WP-2 commit
  (ef9ee729e) accepts the gcloud override and silently delta-skips; `force_execute: true` in a receipt records the operator's
  INTENT, not that force took effect.
* single-run reads nothing back: the disposition (`build` vs `skip_no_delta`) is NOT verified afterwards unless you pass
  `--verify-forced`, which waits for the run to end and reports `forced_effective: true|false` from `build_run_assets`
  (a warning when a forced run ended `skip_no_delta`). wave-by-wave verifies every wave: a `skip_no_delta` stops the campaign.
* `--force-execute` together with `--declared-skips` naming the same asset is refused (`FORCE_WITH_DECLARED_SKIP`): a forced run
  that skipped means force failed, never success.
* Operator check: a `NIRMANA_FORCE_EXECUTE` already set on the Cloud Run job itself would force EVERY run of that job. Before a
  campaign, `gcloud run jobs describe <job>` must show no such variable in its env.

## Out-of-set intermediates

The dry-run summary lists `out_of_set_intermediates_at_risk`: outside assets E that a requested asset depends on and that
themselves depend on a requested asset. Rebuilding that asset can make E's receipt stale, and the dependent's wave would then
refuse with `DEPENDENCY_NOT_READY`: read the list before the live run.

## Time limits

Every `git` call (including `git ls-remote`, every output line parsed) and the `gcloud` dispatch run with a timeout, no stdin
and no prompts. A gcloud timeout means the dispatch outcome is unknown: the planned run is terminalised (the runner refuses a
run that is not planned/running).

## Wall-time report

`asset_wall_time_report` / `read_wall_time_report(connect, run_id, waves)`: per-asset `wall_seconds` from
`build_run_assets.started_at/ended_at`, the asset's `asset_throughput` state, per-wave and whole-run spans. A missing or
inverted timestamp is `unmeasured` (None), never 0. Runtime before a run: `runtime_estimate` gives upper bounds from
`writer_timeout_seconds` and `measured_seconds` only when every asset has a registry `estimated_seconds` (none do today).

## Rehearsal exercise (real schema, local only)

A dry run of a four-asset `bo_*` subset against the rehearsal cluster (127.0.0.1:55432/rehearsal, through the E5.6 guard):
the candidate, closure, dependency, advisory-lock, active-run SELECTs and both INSERTs executed, the E5.9 catalog SELECTs
read 192 FK edges, and the transaction rolled back (0 charts, 0 build_runs left). The rehearsal cluster has no `charts`
row, so the harness inserted one inside the rolled-back transaction. Output and harness:
`scratchpad/e5_3/rehearsal_harness.py`, `rehearsal_harness_output.txt`.

## Offline proof and its limits

`__tests__/test_e5_3_level_wave.py`: fake connection that records every statement, fake git, fake dispatch and hook,
mutation-checked refusals, golden digest equality with the existing dispatcher, the manifest accepted by the real
`runner.validate_frozen_run_manifest` (read-only import), the 23 `bo_*` manifest from fixture rows.

NOT verified without production: that one run of 23 assets / 9 waves completes; the wall time of any L2 writer at scale;
the deployed image's real digests; the live `asset_freshness` state of every dependency; the live `depends_on` of the
seven `bo_*` assets the rehearsal registry lacks; Cloud Run dispatch (`gcloud`) itself.
