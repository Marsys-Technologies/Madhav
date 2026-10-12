```json
{"id":"KV3-B-WRAPPERS",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"plan §9: 00_ARCHITECTURE/briefs/kalayantra/fleet/** forces Opus",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§2; §5; §7; §14 B-1, B-3","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/bin/ky",
"00_ARCHITECTURE/briefs/kalayantra/fleet/bin/kybrief",
"00_ARCHITECTURE/briefs/kalayantra/fleet/install_tracker.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kywrappers.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kywrappers.py -q -p no:cacheprovider",
"expected_result":"exit 0; live defaults and a valid fixture set both reach the stub CLI unchanged",
"negative_cases":[
"any one of the seven fixture variables missing: exit 78, CLI not started",
"PRAVAHA_TRACKER_PORT=8767 or a URL on another host or port: exit 78",
"a fixture path outside $KY_SCRATCH/fixture/ (also through a symlink), or KY_SCRATCH unset: exit 78"]},
"packet_sha256":"fad33356a22b65a0a614b8654faccf1a2302fb5c58b33ec6bf94f5979db0cef1"}
```
F = `00_ARCHITECTURE/briefs/kalayantra/fleet`.

**Pins** Plan v2.7 at e709f60d7; base = the reviewed B-0c head in the job header.

**Owns** `F/bin/ky`, `F/bin/kybrief` (new; the only wrapper source), `F/tests/test_kywrappers.py` (new), and in `F/install_tracker.sh` ONLY the two heredocs that generate the wrappers (lines 26–48 today), replaced by installing those two files. Prohibited: `/Users/Dev/kalayantra/bin/{ky,kybrief}` and every installed tree (never written, never executed); the tracker package; the rest of install_tracker.sh; FROZEN paths.

**Spec** (verbatim)
```excerpt plan §2
the single ledger; wrappers re-pointed and made override-preserving (§5)
```
```excerpt plan §14 B-1
override-preserving `ky`/`kybrief` wrappers
```
```excerpt plan §14 B-3
fixture wrapper preserving validated `PRAVAHA_HOME/EVENTS/PLAN_MODEL/REPO/HOLD/URL/TRACKER_PORT`
```
```excerpt plan §7
For fixture runs it
  forwards the validated `PRAVAHA_*` fixture configuration (§14 B-3).
```
```excerpt plan §14 B-3 acceptance
live EVENTS size/hash unchanged; no fixture connection to port 8767
```

Defect today: both generated wrappers assign all seven values unconditionally, so a fixture job's `ky` reaches the live tracker and model.

**Contract**
`ky <tracker CLI arguments>` decides one of two modes before anything runs. ROOT = the real directory above the wrapper's own `bin/` (installed: `/Users/Dev/kalayantra`); `KY_ROOT` in the environment is not consulted. CAMPAIGN = `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign` (plan §5; replaces `$KY_ROOT/wt/campaign`; ruling P9: B-2 creates it at the accepted source head and it is not fast-forwarded to `origin/main` during the hold, so the reconciled model is there).
- LIVE — none of the seven names is set, or all seven equal these defaults: `PRAVAHA_HOME=ROOT`, `PRAVAHA_EVENTS=ROOT/run/EVENTS.jsonl`, `PRAVAHA_PLAN_MODEL=CAMPAIGN/00_ARCHITECTURE/control/kalayantra/plan_model.json`, `PRAVAHA_REPO=CAMPAIGN`, `PRAVAHA_HOLD=ROOT/HOLD`, `PRAVAHA_TRACKER_PORT=8767`, `PRAVAHA_URL=http://127.0.0.1:8767`.
- FIXTURE — any other case: all seven must be set and valid, and are passed on unchanged. Valid = port an integer 1024–65535 other than 8767; URL exactly `http://127.0.0.1:<port>`; HOME, EVENTS, PLAN_MODEL, REPO and HOLD absolute, their real paths (nearest existing ancestor) inside `realpath($KY_SCRATCH)/fixture/`; `KY_SCRATCH` set and absolute. This is the check the cards FIXTURE_BUILDER FB-02 and FIXTURE_VERIFIER FV-02 make.
- REFUSED — anything else: one stderr line `ky: REFUSED override: <NAME>: <reason>` (names and reasons, never a value), exit 78; the tracker CLI is not started and nothing is written. A partial or mixed set is never completed from defaults.

Then, as today: `PRAVAHA_STREAM=${KY_STREAM:-${PRAVAHA_STREAM:-}}`, `KY_WORKER=${KY_LANE:-}`, `PYTHONPATH=ROOT/tracker_live:ROOT/fleet_live`, `exec /opt/homebrew/bin/python3 -m pravaha_tracker.cli "$@"`. The second PYTHONPATH entry lets the tracker import the top-level module `kyverdicts` (ruling P4; `F/kyverdicts.py`, KV3-B-KYVERDICTS). Arguments, stdout, stderr and exit status are the CLI's own: 0 ok, 1 none or findings (`inbox`, `audit`), 2 refused, 3 event log unwritable, 4 preflight failed.

`kybrief <ID>`: resolves the plan model by the same two modes and the same refusal (exit 78); prints the item as JSON (indent 1), exit 0; unknown id prints `no such item: <ID>`, exit 1; no argument prints usage, exit 64.

Both files are static: no install-time substitution; installation is a byte copy into `<root>/bin/`, mode 0755.

Existing callers, to keep working unchanged:
- kyloop.py `poll_inboxes`: `[<root>/bin/ky, "inbox", "--stream", "S", "--json"]` and `[<root>/bin/ky, "inbox", "--steward", "--json"]`, its own environment plus `KY_STREAM=S`; exit 0 = a JSON list on stdout, 1 = none, anything else = unreadable. kyloop.py also requires `os.access(<root>/bin/ky, os.X_OK)`.
- kyveto.py `run_ky`: `[<root>/bin/ky, "decide", <D-id>, "--outcome", <o>, "--as", "steward", "--delegated", "--detail", <text>]`, stdin `/dev/null`, environment ONLY `HOME USER LANG TERM PATH TMPDIR KY_ROOT KY_RUN KY_FLEET` — LIVE mode must need no other variable.
- KV3-B-PREFLIGHT: `KY_STREAM=S <root>/bin/ky audit --since kickoff`; KV3-B-KYREGEN, KV3-B-KYVERDICTS, KV3-B-FINALIZE, KV3-B-INSTALL: `ky review`, `ky verdict`, `ky claim|release|done`, `ky decide|park|block`, each with `KY_STREAM`/`KY_LANE` set by the caller.
- Plan §6 forms: `ky claim|renew|release|review|block|step|verdict|done|next --json|decide|ack|request|park`.

INTERPRETATION: (a) "validated" = the FB-02/FV-02 rule, all or nothing; (b) exit 78 for a refused override — 0, 1 and 2 already mean something to the callers above; (c) ROOT from the wrapper's own location, so one file serves the installed tree and a test tree; (d) static files under `F/bin/` instead of heredocs, so the installed bytes equal reviewed bytes (D-9).

**Depends on** Wave 1; nothing to build. KV3-B-INSTALL (wave 4) may assume: sources `F/bin/ky` and `F/bin/kybrief`, byte copy, 0755, no other wrapper generator (install_tracker.sh installs the same two files). The tracker service's own launch environment (the plist block of install_tracker.sh, which must also put `<root>/fleet_live` on PYTHONPATH and name CAMPAIGN) is that packet's, not this one's.

**Acceptance** Tests first; command above. Tests copy the wrappers into a temp ROOT whose `tracker_live/pravaha_tracker/cli.py` is a stub recording its arguments and the seven values; they never touch `/Users/Dev/kalayantra`. Must show: LIVE defaults exactly as listed, with an empty environment and with kyveto's nine-name environment; a complete valid fixture set passed through unchanged; arguments containing spaces and exit statuses 0, 1, 2, 3 passed through; `kybrief` reading the fixture model in FIXTURE mode and, in LIVE mode, opening exactly the default path (shown from its output whether or not the campaign checkout exists). Negative: the three cases above for `ky` and for `kybrief`, each of the seven names in turn; in every refusal the stub did not run and no file changed. A source test fails if install_tracker.sh still assigns a `PRAVAHA_` value outside its launchd plist block. No output ever contains an environment value. A mode the wrapper cannot decide is REFUSED, never LIVE.

**Evidence** `result.json` (BS-16): each command, exit code, summary; skips named; `head_sha` = pushed head.

**Branch and PR** `kalayantra/kv3-b-wrappers`; one PR to main, "KĀLA-YANTRA v3 KV3-B-WRAPPERS: override-preserving ky and kybrief wrappers"; never merged by the job; under the hold nothing merges.

**Do not** edit outside Owns (plan, cards, schemas, other packets, tracker); run or write an installed wrapper; run `install_tracker.sh` or the tracker; rebase or force-push; read credentials; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
