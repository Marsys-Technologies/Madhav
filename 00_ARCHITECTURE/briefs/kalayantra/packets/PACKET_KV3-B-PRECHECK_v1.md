```json
{"id":"KV3-B-PRECHECK",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"control-plane source (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§3; §7; §8.6; §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/precheck.sh","revision":"7ee8f2af278e9b09868968a593db25ac835457e1","section_range":"whole file","sha256":"a7b7f849de8475de71875dae463543691b6b0d8cfa7c08c37a9a3de302e94636"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/precheck.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_precheck.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_precheck.py -q -p no:cacheprovider",
"expected_result":"all tests pass; with KY_RUN set nothing under $KY_ROOT/run is read or written",
"negative_cases":[
"every path precheck refuses today is still refused (one case per alternative of the line-116 pattern)",
"a path listed in FROZEN_PATHS.txt is refused with freeze: <path>",
"a missing, unreadable or malformed FROZEN_PATHS.txt is RED",
"a KY_RUN that is set but not an absolute existing directory is RED",
"a code diff with neither TESTS nor a manifest under KY_RUN is RED"]},
"packet_sha256":"608f3496ef51ca14270dcf751031355c00cbbdf7ed1807b260b5756b82f2a82a"}
```
# KV3-B-PRECHECK: `precheck.sh` fixture-awareness

F = `00_ARCHITECTURE/briefs/kalayantra/fleet`.

**Pins.** Plan v2.7 at e709f60d7; front matter pins current precheck v2.1 at 7ee8f2af27. The delta/line numbers below describe historical v2.0 at e709f60d7, SHA256 fdda3dedad6107ed68ddab236f1ffccb4303188561301fe6929bad78e1bfdf3e (122 lines). Preserve that acceptance baseline; current admission is not redispatch of installed work. Release pins: not applicable.
Version 1.0; status: preparation; changelog: current source pin separated from historical baseline; scope unchanged.

**Owns.** Change `F/precheck.sh`; create `F/tests/test_precheck.py`; nothing else. `F/FROZEN_PATHS.txt` belongs to KV3-B-KYROUTE and `F/precheck_bg.sh` is out of scope: do not create or edit either. Prohibited: FROZEN paths (BS-05); the plan, cards, schemas, other packets.

**Spec** (verbatim).
```excerpt plan §7
- `precheck.sh` is fixture-aware through `KY_RUN`; the launcher writes the manifest
  precheck actually consumes **or** passes newline-delimited test paths in `TESTS`.
```
```excerpt plan §3 Kept
- The FROZEN contract: one explicit manifest `fleet/FROZEN_PATHS.txt` shared by
  `precheck.sh` and `kyroute.py`, seeded from ORCHESTRATOR_CONVERGENCE_CLOSE §2 and
  precheck's existing prohibitions (`asset_runner.py`, `runner.py`, `staleness.py`,
  `writers/__init__.py`, …). New conforming writers remain permitted; a frozen change is
  STOP for native authorisation.
```
```excerpt plan §8.6
Plus `KY_ITEM=<ID> bash $KY_FLEET/precheck.sh --item`.
```
```excerpt plan §7 launch line
TESTS="$TESTS_NEWLINE_LIST"
```
```excerpt plan §14 B-1
`precheck.sh` fixture-awareness
```

**Contract.** The command line, the nine steps, their order, the output lines and the exit status (0 `PRECHECK GREEN`, 1 `PRECHECK RED`) stay as they are. The change is this delta and nothing more; every line not named here stays byte for byte.
1. Run directory. After line 10 add `KY_RUN="${KY_RUN:-$KY_ROOT/run}"`. INTERPRETATION: when `KY_RUN` is set but is not an absolute path of an existing directory, print the reason and exit 1 before step 1; never fall back to the live directory.
2. Replace the three uses of `$KY_ROOT/run` by `$KY_RUN`:
   - lines 22–23, the heavy-step lock and its comment → `$KY_RUN/precheck_heavy.lock`;
   - line 92, the item's test manifest → `$KY_RUN/tests/$KY_ITEM.txt` (both occurrences);
   - line 110, the migration log → `$KY_RUN/precheck_migrate_${LANE}.log` (and the path its failure message prints).
   After the change the script reads and writes nothing under `$KY_ROOT/run` when `KY_RUN` points elsewhere.
3. Test manifest, the interface the launcher (KV3-B-KYJOB, wave 3; plan §7) may assume, unchanged in form: `TESTS`, when non-empty, is the manifest (newline-delimited paths relative to the repository root); otherwise the file `$KY_RUN/tests/$KY_ITEM.txt`, one path per line. With neither, a diff that changes code stays RED (line 102).
4. Frozen manifest (step 9). Read `FROZEN_PATHS.txt` beside the script (`$(dirname "${BASH_SOURCE[0]}")`), in the format KV3-B-KYROUTE fixes: UTF-8, LF; lines starting `#` and blank lines ignored; every other line one exact repository-relative file path (no glob, no leading `/`, no `.` or `..` segment, no white space, no duplicate). Each path of `$CHANGED` that equals an entry → `fail "freeze: <path>"`. A manifest that is missing, unreadable, without entries or holding any other line → `fail` with that reason. No environment variable may relocate or disable it.
5. Existing prohibitions. The step-9 pattern of line 116, the `K0a-0` workflow exception of line 115, the credential-file check of line 118 and the writer-digest check of line 119 are not edited: the four orchestrator alternatives stay inline as well, so a short manifest can never relax them. The result is the union of the inline pattern and the manifest.
6. Header: `v2.0` → `v2.1` with one changelog comment line naming this packet (BS-11).
Not changed (plan silent): the database addresses of lines 91 and 109, `KY_PRECHECK_MODE`, the step list.

Call forms in use: `KY_ITEM=<ID> fleet/precheck.sh` (`TESTING.md`), `bash "$2"` from `F/precheck_bg.sh` with `KY_ITEM` and `KY_LANE` set, and the plan §8.6 form above. `F/kyboot.py` allows `TESTS` and `KY_RUN` in a job's environment. No B-0c controller calls precheck.

**Depends on.** Wave 1; nothing built first. KV3-B-KYROUTE (same wave): only the path and the format of `F/FROZEN_PATHS.txt` in item 4; its seed is the four orchestrator files already in line 116. The tests write their own manifest, so the two packets build in parallel.

**Acceptance.** The front matter's `acceptance.command`. Each test copies the script next to a manifest it writes, into a throwaway git repository under the pytest base (an `origin/main` ref, stub `npm`, `npx`, `gitleaks` first on `PATH`, a stub `platform/scripts/governance/secret_scan.sh`, `KY_PY` = the test interpreter, `--item` mode), with `KY_ROOT` and `KY_RUN` in separate temporary directories; no network, no database, no real `/Users/Dev/kalayantra` path. The tests show:
- manifests naming different tests under `$KY_ROOT/run/tests/` and `$KY_RUN/tests/`: only the `KY_RUN` one runs, and the listing and hashes under `$KY_ROOT/run` are identical before and after;
- `TESTS` wins over both; with `KY_RUN` unset the `$KY_ROOT/run/tests/` manifest is used as before;
- one RED case for every alternative of the line-116 pattern (`CLAUDECODE_BRIEF.md`, root `CLAUDE.md`, `.codex/`, a workflow file and its `K0a-0` exception, the two `platform/src/lib` trees, each of the four other campaigns' brief folders, each of the four orchestrator files), for a staged credential-like file, for a `ka_` writer changed without its digest file, for an unknown test path type and for a migration with `KY_LANE` unset;
- the five negative cases; a manifest entry outside the inline pattern is refused with `freeze: <path>`; a clean diff with a passing test is GREEN (a script that always fails does not pass).
GREEN is printed only when every step ran: no new branch may skip a step or turn a missing input into success.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16): `tests[]` with the acceptance command and each negative case and exit code; `head_sha` = the pushed head; `notes` gives the `git diff --stat` of `precheck.sh` and the interpretation applied.

**Branch and PR.** Branch `kalayantra/kv3-b-precheck`. One PR to `main`, title `KĀLA-YANTRA v3 KV3-B-PRECHECK: precheck.sh fixture-awareness`; body: delta and test exits. Fleet merges under KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A1_FULL_AUTONOMY.md:26–33; job never merges.

**Do not.** No control-plane edit outside `d1_paths`; no removed or weakened prohibition; no rebase or force-push; no credentials; no production; no database; no edits to the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
