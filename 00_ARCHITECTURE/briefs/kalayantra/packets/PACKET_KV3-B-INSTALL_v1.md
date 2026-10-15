```json
{"id":"KV3-B-INSTALL",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§14 B-2; §15 D-9; §5; §0.4; §6; §7","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/install.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_install.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_install.py -q -p no:cacheprovider",
"expected_result":"exit 0; scratch-root installs only",
"negative_cases":[
"an area review REJECTED, missing, changed or double-signed while the manifest's review field says ACCEPTED: exit 1, nothing written",
"component bytes differ from the reviewed hash, or a legacy supervisor is alive or unobservable: exit 1",
"a staged action unpublished, a test-hook variable in a plist, a qualification not PASS: no receipt",
"an unbound or modified tracker file to install: exit 1"]},
"packet_sha256":"05b73c1802c4c76d990dcb2f74d3c2dfe69afa6f139693a291de21d57e342340"}
```
# KV3-B-INSTALL: `install.sh`

**Pins.** Plan v2.7 @ e709f60d7; base = the reviewed B-0c head (job header).

**Owns.** The two `d1_paths`. Prohibited: FROZEN paths; any other path → `blocked`. Tests install into a scratch root under `$JOB_SCRATCH`, every external program faked.

**Spec (verbatim).**
```excerpt plan §14 B-2
**Review and install (KX-02, D-9).** Independent review accepts the exact immutable source head or component heads assembled into the installation bundle. `install.sh` verifies those heads, review receipts and manifest hashes, then installs the fleet, tracker, wrappers, approved plan, prompts, cards and manifest. `run/INSTALL_RECEIPT.json` records source commits, tree/component hashes, review references, qualifications, `CLAUDE_BIN` and the running tracker's loaded revision; a merge commit is optional historical metadata, never an installation prerequisite. Prove that old supervisors/sweeps cannot dispatch (`STOP_*` + process-absence evidence); create the campaign checkout within capacity; publish the staged D-RETIRE decisions; reconcile legacy claims, PRs and checkpoints; mark the receipt `mode: bootstrap`.
```
```excerpt plan §14 B-2
installed hashes match the reviewed component heads bound by the manifest; `preflight.sh launch` and `kyversion.sh --bootstrap` pass; only the accepted bootstrap receipt permits isolated rehearsal activation — receipt-file existence alone grants no authority
```
```excerpt plan §15
**D-9** bootstrap and campaign installation use the independently
accepted branch head bound in the receipt, never an unreviewed or merged-by-assumption tree.
```
```excerpt plan §5
branch `kalayantra/campaign` (upstream `origin/main`) at
  `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`, created in B-2
```

**Contract.** ROOT = `--root`, default `$KY_ROOT`; R = `ROOT/run`; F = `ROOT/fleet_live`; (I) = INTERPRETATION.
- `bash install.sh --manifest M --source S [--root ROOT] [--action ID]`, absolute paths. M: a `ky.versions_bootstrap/1` manifest; S: a clean checkout at M's `components_commit`. Exit 0 installed + receipt · 1 refused, nothing written · 3 failed after writing began (trees restored, no receipt) · 64 usage.
- B-2 only (I): ROOT = `/Users/Dev/kalayantra` needs `--action ID`, an INTENDED kyaction record of kind `install` binding M's sha256 and S's commit; it completes or fails it. Fail closed (ruling P29): any other ROOT → exit 1 unless `KY_LAUNCHAGENTS_DIR`, `KY_LAUNCHCTL`, `KY_CAMPAIGN_CHECKOUT` (step 5's path) and `PRAVAHA_URL` are each given explicitly, none equal to its real default. Ruling P39: both are decided FIRST, before M, S or any path under ROOT (STOP files included) is read or written, each with its stderr code `E_ACTION`, `E_UNSET <VAR>` or `E_REAL <VAR>`; its test passes an M and S that cannot verify, HOME = the pytest base, and asserts the code.
- Verify (failure → exit 1):
  a. `python3 -I -B <S fleet>/kymanifest.py check M --repo S --run R` exits 0.
  b. Provenance, by its own code, never M's `review` field: the record at `review.path` has `review.sha256`, verdict ACCEPTED, M's approved commit; each `area_reviews[].record` has its `record_sha256` and `review.verdict` ACCEPTED; no session signs twice; the areas equal the bound `# area:` names of `BOOTSTRAP_COMPONENTS.txt`; each component in S equals its blob at `components_commit`, M's `components[].sha256` and an ACCEPTED record's `inputs`. Ruling P40: only M's components and entrypoints so verified are installed (fleet, tracker package, wrappers, MCP configurations); an unbound file to install → exit 1.
  c. `deferred_components` are never installed.
  d. `CLAUDE_BIN` executable, version ≥ 2.1.296, sha256 taken.
  e. Old supervisors/sweeps: `R/STOP_<lane>` for sutradhara adhikarin v1–v3 k1–k8 (absent: created as the first write, never in a refusal); no process matching `kalayantra_fleet.sh`, `claude_cycle.py`, `conductor/sweep.py`, or `codex exec` under `ROOT/wt/`; an unanswerable listing refuses; kill nothing.
- Then write exactly these, in order (failure → exit 3); trees swap by rename, old kept as `.old`.
  1. `F/**`: M's fleet components, cards and prompts included; `fleet_live/bundle/<repository path>`: the five entrypoints (I).
  2. `ROOT/tracker_live/pravaha_tracker/**`.
  3. `ROOT/bin/ky`, `ROOT/bin/kybrief`: byte copies of `fleet/bin/*`, 0755; nothing else in `bin`.
  4. `R/VERSIONS.bootstrap.json` = M.
  5. The campaign checkout (`git worktree add`, spec path and branch) at `components_commit` (ruling P9: the accepted source head, never fast-forwarded to `origin/main` in the hold), while the Claude/Madhav worktree count is ≤ 14.
  6. Tracker: write `${KY_LAUNCHAGENTS_DIR:-~/Library/LaunchAgents}/com.madhav.kalayantra.tracker.plist` (install_tracker.sh's block + `F` on PYTHONPATH, step 5's checkout); restart it (`${KY_LAUNCHCTL:-/bin/launchctl}`): `/api/health` ok, no `model_error`, process started after the swap (I). Then, before any receipt: publish `STAGED_MODEL_ACTIONS_v2_2.json` with the installed `ky` — `decide <D> --outcome refused --as steward --delegated --detail …`, `park <item> --as steward --detail …`, `block KV3-SCHEMA-1 --as steward --detail …`; once each (an existing event is skipped, reported).
  7. Legacy (I): list each `R/claims/*.json`, each open `kalayantra/*` PR with its tracker-registered head, each legacy checkpoint; `KY_LANE=<lane> ky release` only after (e); one `R/jobs/legacy-<n>/state.json` per adopted PR; fabricate nothing; the rest → `legacy.unresolved[]`.
  8. `bash F/kyctl.sh install` renders the four loop plists into the same directory; each lacks `KY_LOOP_SLEEP_SCALE` and `KY_LOOP_TEST_CONTEXT`; record its `KY_SCRATCH`. Starts nothing.
  9. Requalify each `F/templates/LAUNCH_CONFIG.*.json` and `python3 F/kyloop.py admin launch-config planner|conductor`: unless `kyqualify.py check <receipt> --config <cfg> --require-context launchd --verify-evidence` exits 0, run `kyqualify.py qualify --config <cfg> --context launchd --evidence-dir <scratch> --out R/QUALIFICATIONS/<role>-<model>.json`; PASS required (I).
  10. `bash F/preflight.sh launch` exits 0; write `R/INSTALL_RECEIPT.json` (atomic); `bash F/kyversion.sh --bootstrap` exits 0, else rename it `.refused`.
- Receipt keys (ruling P6): `schema`, `mode: "bootstrap"`, `source` (both commits; `merge_commit` optional), `manifest{path, sha256, manifest_sha256}`, `components[{path, installed_path, sha256}]` (one per installed file, MCP configurations too; read by kyversion.sh), `trees`, `reviews`, `qualifications`, `claude_bin`, `tracker_revision` (package hash; pid, process start), `plists`, `old_supervisors`, `campaign_checkout`, `model_actions`, `legacy` — each measured in this run; an unknown value → no receipt.

**Depends on.** Wave 4. KV3-B-KYVERSION, KV3-B-PREFLIGHT (step 10): exit 0 = pass. KV3-B-WRAPPERS `fleet/bin/*`; KV3-B-TRACKER, KV3-B-KYVERDICTS (imported from `F`); KV3-B-KYROUTE's `FROZEN_PATHS.txt` installs with the fleet.

**Acceptance.** The front-matter cases; a second run changes and republishes nothing; a crash after step 6 resumes with no second `ky decide`.

**Evidence.** `result.json`: each command, exit code; the pushed 40-hex head.

**Branch and PR.** `kalayantra/kv3-b-install`; one PR to main "KĀLA-YANTRA v3 KV3-B-INSTALL: install.sh"; never merged by the job.

**Do not.** Rebase or force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
