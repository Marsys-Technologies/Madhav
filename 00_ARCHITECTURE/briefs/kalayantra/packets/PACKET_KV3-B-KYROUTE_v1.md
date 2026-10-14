```json
{"id":"KV3-B-KYROUTE",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"control-plane source (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§3; §8.2; §9; §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/control/kalayantra/plan_model.json","revision":"7ee8f2af278e9b09868968a593db25ac835457e1","section_range":"KA-1e, K1-2, K6-4","sha256":"64c6b291670cea2226e322d804fbf238980ae2864d19f34e6a1a05229f231edf"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyroute.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/FROZEN_PATHS.txt",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyroute.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/fixtures/kyroute/items.json"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyroute.py -q -p no:cacheprovider",
"expected_result":"all tests pass; KA-1e, K1-2, K6-4 route to opus; a frozen path exits 3",
"negative_cases":[
"a path in FROZEN_PATHS.txt is not routed: STOP, exit 3",
"a Sonnet-built platform/src/lib/auth/ diff: exit 1, re-queued for Opus, head untouched",
"a missing, empty or malformed manifest: exit 66",
"an item owning only platform/src/components/ paths stays sonnet",
"a prose owns entry routes to opus"]},
"packet_sha256":"f9211eb9e973c785ed1b5a070199871f8ee8571566cb579a6514ff07dd83d05e"}
```
# KV3-B-KYROUTE: `kyroute.py`, `FROZEN_PATHS.txt`

F = `00_ARCHITECTURE/briefs/kalayantra/fleet`; O = `platform/python-sidecar/pipeline/orchestrator`.

**Pins.** Plan at e709f60d7; model at 7ee8f2af27; historical base = B-0c job head.
Version 1.0; status: preparation; changelog: refreshed model pin.

**Owns.** Create `F/kyroute.py`, `F/FROZEN_PATHS.txt`, `F/tests/test_kyroute.py`, `F/tests/fixtures/kyroute/items.json`; nothing else (`F/precheck.sh` is KV3-B-PRECHECK's). Manifest files prohibited.

**Spec** (verbatim).
```excerpt plan §9
`kyroute.py` normalises `owns`/`shared`/diff paths to repository-relative; prose entries
are resolved by the planner or routed to Opus. Opus is forced by: a migration file or
non-NONE migration metadata; any path under
`platform/python-sidecar/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**`,
`platform/python-sidecar/services/{kala_core/sky,gochara_kernel}/**`,
`platform/python-sidecar/pipeline/orchestrator/writers/ga_*.py`, `**/*ephemeris*`,
`platform/scripts/temporal/**`, `platform/scripts/migrate.ts`, `platform/migrations/**`,
`platform/src/proxy.ts`, `platform/src/lib/{auth,security,share,limits,mcp}/**`,
`platform/src/app/api/{auth,admin,db}/**`, `.github/workflows/**`, `infra/**`,
`platform/scripts/governance/**` (including `platform/scripts/governance/pravaha_tracker/**`),
`00_ARCHITECTURE/briefs/kalayantra/fleet/**`; any diff line touching `'lit'` state or
writing `verification_pass_status`; an import of `swisseph`/`jhora`. Paths in
`FROZEN_PATHS.txt` are not routed: STOP for native authorisation. Routing runs on the
packet and again on the actual diff before VERIFY: a Sonnet diff that hits an Opus rule
is **preserved** and re-queued as an Opus REWORK that assesses it (not discarded).
Fixtures: KA-1e, K1-2, K6-4 → Opus; a `platform/src/lib/auth/**` diff → Opus.

Escalation: Sonnet red after `max_loops` → Opus REWORK; one REJECTED on a Sonnet head →
Opus REWORK; Opus REJECTED twice → `ky block` → conductor → RULING or PLAN.
```
```excerpt plan §3 Kept
- The FROZEN contract: one explicit manifest `fleet/FROZEN_PATHS.txt` shared by
  `precheck.sh` and `kyroute.py`, seeded from ORCHESTRATOR_CONVERGENCE_CLOSE §2 and
  precheck's existing prohibitions (`asset_runner.py`, `runner.py`, `staleness.py`,
  `writers/__init__.py`, …). New conforming writers remain permitted; a frozen change is
  STOP for native authorisation.
```

**Contract A: `F/FROZEN_PATHS.txt`**, the one manifest; `F/precheck.sh` reads the same file. UTF-8, LF. `#` lines and blank lines are ignored; every other line is one exact repository-relative file path: no glob, no leading `/`, no `.` or `..` segment, no white space, no duplicate. A reader that finds it missing, unreadable, without entries or with any other line refuses: never "nothing is frozen". Seed, exactly four lines: `O/asset_runner.py`, `O/runner.py`, `O/staleness.py`, `O/writers/__init__.py`.
INTERPRETATION: only these, the list the plan names (the orchestrator part of `F/precheck.sh` line 116). Precheck's other step-9 prohibitions stay inline there, not frozen: §9 routes `.github/workflows/**` to Opus and §8.2 names cross-campaign files as a separate class.

**Contract B: `F/kyroute.py`**, read-only (no checkout, reset, stash, delete or write); stdout is one JSON `{"mode","decision","tier","packet_tier","computed_tier","reasons":[{"rule","path","detail"}],"frozen":[],"head"}`.
```
kyroute.py packet   --packet <abs PACKET.md> --model <abs plan_model.json> --repo <abs>
kyroute.py diff     --repo <abs> --base <40-hex> --head <40-hex> --built-tier sonnet|opus
kyroute.py escalate --tier sonnet|opus --red-loops N --max-loops M --rejected K
```
- `packet` and `diff` take `--frozen <abs>` (default: the one beside the script).
- `packet` reads the front matter (the first fenced json block, as KV3-B-KYPACKET defines): `id`, `build_tier`, `d1_paths`; and, from the model item with that id, `brief.owns`, `brief.shared`, `brief.migration`, `brief.op`. INTERPRETATION: the packet schema has no owns field and the body is not parsed. No such item and no `d1_paths`: exit 66.
- Normalisation: drop a leading `./`; make an absolute path under `--repo` relative. An entry that then holds white space, a `..` segment or an absolute path elsewhere is prose: Opus (`prose_entry`).
- Rule table = the excerpt's list, one row per glob. INTERPRETATION, each erring to Opus: `**/*ephemeris*` matches any segment containing `ephemeris`, case-insensitively; an owns glob that can overlap a rule matches it; a migration file matches `precheck.sh`'s `^platform/(supabase/)?migrations/.*\.sql$`; non-NONE migration metadata is any `migration` or `op` other than absent, null, `""`, `NONE`.
- `diff`: paths from `git diff --name-only --no-renames <base> <head>`; content rules, by substring on added and removed lines (INTERPRETATION): a line containing `'lit'` or `"lit"`; one containing `verification_pass_status`; an `import` or `from` of `swisseph` or `jhora`.
- Decisions. `STOP`, tier null, exit 3: an entry or changed path is in the manifest (`rule` `freeze`). `REQUEUE_OPUS_REWORK`, exit 1: `diff` with `--built-tier sonnet` hits an Opus rule; `head` is preserved for the dispatcher to re-queue. Else `ROUTE`, exit 0: `tier` is opus when `packet_tier` or `computed_tier` is opus, else sonnet (a packet may raise the tier, never lower it).
- `escalate` prints `{"decision": "CONTINUE" | "OPUS_REWORK" | "BLOCK"}`, exit 0: sonnet with `rejected` ≥ 1 or `red-loops` ≥ `max-loops`: `OPUS_REWORK`; opus with `rejected` ≥ 2: `BLOCK`; INTERPRETATION: opus with `red-loops` ≥ `max-loops`: `BLOCK`; else `CONTINUE`. The dispatcher acts on it; escalation grants no authority (plan §3).
- Exit 0 · 1 re-queue · 3 STOP · 64 usage · 66 an input (the manifest included) is missing, unreadable or invalid; no tier is printed on 3, 64, 66. Environment: `KY_GIT` (default `/usr/bin/git`).

**Depends on.** Wave 1; none. KV3-B-PRECHECK (same wave) may assume A; the dispatcher packets (KV3-B-KYD*) B: routing recomputed at admission (plan §6), the diff run before VERIFY.

**Acceptance.** `acceptance.command`. `items.json` = the `brief` of KA-1e, K1-2, K6-4 copied by script from the pinned plan model at the base, with that file's sha256; never retyped. Shown: those three route to opus, each with the rule that forced it; a Sonnet-built `platform/src/lib/auth/` diff exits 1, with refs, `HEAD` and work tree unchanged; every rule row has a path that matches and one that does not; each seeded path, in `owns` and in a diff, exits 3; the escalation table row by row. A tier comes only from a rule that ran: an unreadable input never yields sonnet.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16): commands, exit codes, pushed `head_sha`, interpretations in `notes`.

**Branch and PR.** `kalayantra/kv3-b-kyroute`; one PR to main. Fleet merges under KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A1_FULL_AUTONOMY.md:26–33; job never merges.

**Do not.** Edit outside `d1_paths` or any frozen file; rebase or force-push; touch credentials, production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
