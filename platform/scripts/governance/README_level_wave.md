# Level-wave dispatcher (Suvarna E5.3)

`platform/scripts/governance/suvarna_level_wave.py`, section 2. Builds ONE frozen run manifest
(`nirmana-run-manifest/v1`) for an explicit list of assets, with waves derived from the registry's `depends_on`,
and dispatches it through the existing runner path. It replaces the single-asset
`platform/scripts/dispatch_frozen_rebuild.py` for multi-asset rebuilds; that script is untouched.

## Status: NEVER EXECUTED IN PRODUCTION above 17 assets / 1 wave

The largest run on record is 17 assets in one wave (L0, 2026-09-04). No multi-wave manifest and no 23-asset run has ever
executed; the only 2-wave manifest in history failed the image-skew check. The runner supports N assets and waves
structurally (read, not executed). Everything below is proven offline with fakes and fixtures only: no database, no
gcloud, no production contact. Exec Suvarna runs it. Read the dry-run receipt before `--commit`.

## Use

```
DATABASE_URL=... python3 platform/scripts/governance/suvarna_level_wave.py \
    --chart-id 482012f1-710e-4a25-994a-93821f5871aa \
    --assets bo_laksana,bo_bimba,...          # or @file, or repeated --assets; an explicit list, never a level
    --deployed-sha <sha of the running brahma-build-pipeline-job image>   # or --deployed-digests-file
    [--mode single-run|wave-by-wave] [--with-footprint]                   # dry run (default)
```

The dry run runs the whole transaction (advisory lock, active-run check, registry re-read, dependency check, both
INSERTs) and then ROLLBACKs. It prints the waves, the manifest digest, a per-wave manifest digest, the external
dependencies, a runtime bound, and the `--confirm` token. A real run adds `--commit --confirm <token> --mode ...`.

The token is the existing `<SUBJECT>_FROZEN_REBUILD` convention with the subject bound to the manifest:
`<N>ASSETS_<first 12 hex of the digest, upper>_FROZEN_REBUILD`. A registry change moves the digest and so the token:
a token from an old dry run cannot confirm a different manifest. `--commit` without `--mode`, or with a wrong token,
refuses before anything is written.

## What it builds

* Manifest: byte-identical in shape to `dispatch_frozen_rebuild.build_manifest` (a one-asset input gives the same
  manifest and digest, golden-tested). `scope='asset_set'`, `scope_target` = the plan joined by commas (the campaign
  dispatcher's convention), `waves` = the derived levels, one `assets` entry per plan id in plan order with
  `scope`, `depends_on` (registry order), `natural_key_partition`, `has_cowriters`, and `expected_code_digest` from
  `platform/src/generated/nirmana-writer-digests.json`. The digest is the sha256 of the canonical JSON
  (sorted keys, `(",",":")`, ASCII), the same as `runner._canonical_manifest_digest`.
* Waves: wave(a) = 0 when a has no dependency inside the requested set, else 1 + the largest wave of its in-set
  dependencies (the longest path). Dependencies outside the set never move an asset. A cycle is an error. Ids inside a
  wave are sorted; the plan is the flattened waves.

## Refusals (exit 4, JSON on stdout, nothing inserted)

| code | when |
|---|---|
| `IMAGE_SKEW` / `CODE_DIGEST_UNAVAILABLE` | image skew: an asset's writer digest in the checkout differs from, or is absent in, the DEPLOYED image's inventory (the runner would refuse the whole run) |
| `DEPLOYED_DIGESTS_UNAVAILABLE` | no `--deployed-sha` / `--deployed-digests-file`, or it can not be read. Never skipped |
| `DEPENDENCY_NOT_READY` | a declared dependency OUTSIDE the set is not lit, or has no fresh receipt (service dependencies need only `service_ok`). Every asset's external dependencies are checked, not only wave 0 |
| `REGISTRY_ROW_CHANGED` | an asset's registry-row digest at the insert differs from the one the manifest was built from (re-read in the insert transaction) |
| `REGISTRY_ROW_INVALID` | missing, inactive, no writer, or a service asset |
| `ACTIVE_RUN` | a planned/running/paused run exists for the chart |
| `FAMILY_ASSET` | `ka_gochara*`, `gochara_*`, `kala_gochara_*` (always), or any member of `FAMILY_ASSETS.json` `family_set` |
| `SPLITS_FAMILY` | part of a declared family list without the rest |
| `FAMILY_FILE_UNREADABLE` | the file at `--family-ref` (default `origin/main`) exists but is unreadable, not JSON, missing a key, or `family_set` is not the union of the six lists. Never fails open |
| `FAMILY_FILE_MISSING` | the file is not on the ref and the run is a `--commit` (a dry run proceeds on name patterns only, and says so) |
| `CONFIRM_TOKEN_MISMATCH` | `--commit` without the exact token |

The family file is read with `git show <ref>:00_ARCHITECTURE/control/FAMILY_ASSETS.json`, the committed content, never the
working tree. It is lane 2's file and may not exist yet: while absent, only the name patterns protect a dry run, and
a real dispatch is refused.

## Stop hook between waves

The runner executes every wave of one manifest as one run and has **no hook between waves**: it schedules from each
asset's `depends_on`, and wave boundaries are informational. The frozen runner is not touched, so the hook lives here:

* `--mode single-run`: one manifest with all waves, one run. **No pause is possible.** A documented limitation.
* `--mode wave-by-wave`: one run per wave. Each wave's manifest holds only that wave; the earlier waves are ordinary
  out-of-set dependencies, so the dependency check (and the runner's own DEP-ASSERT) require them lit+fresh before the
  next wave can be inserted. Between waves the dispatcher stops and waits for the operator (`--pause-dir`): it writes
  `after-wave-<k>.pending.json` (what finished, the per-asset wall times, the next wave and its token) and continues only
  when `after-wave-<k>.continue` holds exactly `CONTINUE_WAVE_<k+1>_<12 hex>`; `after-wave-<k>.stop`, a wrong token or
  the hook timeout stop. A run that does not end `completed`, or an asset not `complete`/`skipped`, stops before the pause.
  `--commit --confirm` takes the full-plan token once; each wave's insert then uses its own computed token.

A wave-by-wave dry run exercises wave 0 only: later waves' dependencies are earlier waves, which are not built yet.

## Wall-time report

`asset_wall_time_report` / `read_wall_time_report(connect, run_id, waves)`: per-asset `wall_seconds` from
`build_run_assets.started_at/ended_at`, the asset's `asset_throughput` state, per-wave and whole-run spans. A missing or
inverted timestamp is `unmeasured` (None), never 0. In wave-by-wave mode it is read after every wave and shown in the
pause file. Runtime before a run: `runtime_estimate` gives upper bounds from `writer_timeout_seconds` (parallel inside a
wave, serial total) and `measured_seconds` only when every asset has a registry `estimated_seconds` (none do today).

## Offline proof and its limits

`__tests__/test_e5_3_level_wave.py`: fake connection that records every statement (INSERT then ROLLBACK, COMMIT only with the
token), fake git, fake dispatch and hook, mutation-checked refusals, golden digest equality with the existing dispatcher, the
manifest accepted by the real `runner.validate_frozen_run_manifest` (read-only import), and the 23 `bo_*` manifest.
The 23-asset dependency rows are indicative: the list is the registry seed / digest inventory, `depends_on` comes from the
seed overridden by the 16 rehearsal-registry rows that carry one (the rehearsal registry has 93 of ~128 rows). The live
registry decides; the dry run recomputes it.

NOT verified without production: that one run of 23 assets / 9 waves completes; the wall time of any L2 writer at
scale; the deployed image's real digests; the live `asset_freshness` state of every dependency; the SQL against the real
schema (the candidate, dependency and run-asset queries mirror `dispatch_frozen_rebuild.py` and `asset_runner.deps_unsatisfied`
by reading; they were not executed); the E5.9 footprint SQL (also unexecuted).
