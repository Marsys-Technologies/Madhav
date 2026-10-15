```json
{"id":"KV3-B-PREFLIGHT",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"fleet/** control plane (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§5 CLAUDE_BIN, Preflight v3; §14 B-1, B-2","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/preflight.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_preflight.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_preflight.py -q -p no:cacheprovider",
"expected_result":"exit 0; hermetic: fakes only; all checks ok gives exit 0 and a receipt with \"mode\": \"launch\"",
"negative_cases":[
"an audit finding without a reconciliation entry, an entry without a finding, or a record not accepted at its current digest: FAIL",
"ky audit exit other than 0 or 1 (unavailable): FAIL",
"slots unknown; the disposable slot not READY, a seed hash unequal or its removal unproven: FAIL",
"qualification receipt missing or kyqualify check non-zero; claude below 2.1.296: FAIL",
"a credential variable name set: FAIL, its value never printed"]},
"packet_sha256":"c37e0589472f26ce1d0f6033b94307d96fa2b3df84f2c6453843a1f6a91fc3f2"}
```
F = `00_ARCHITECTURE/briefs/kalayantra/fleet`.

**Pins** Plan v2.7 at e709f60d7; base = the job header's reviewed B-0c head.

**Owns** `F/preflight.sh`, `F/tests/test_preflight.py` (new). Prohibited: `kalayantra_fleet.sh`; the tracker, ledger and any verdict; FROZEN paths.

**Spec** (verbatim)
```excerpt plan §5
**Preflight v3** derives expectations from configured slots, runs a Claude-only smoke,
  and is the install receipt's precondition.
```
KU-01 (label `preflight-v3`; block sha256 = ku_bindings.json `text_sha256`):
```text
Audit and guarded completion shall share the same normalized, typed evidence requirements. Data-writing code requires ACCEPTED post_deploy evidence at the observed squash merge commit. Code-only completion requires verified successful deployment containment of its mapped merge commit, without inventing a post_deploy obligation. Artifact and operation completion retain their digest-bound acceptance requirements. Apply the shared reviewed-patch inheritance predicate wherever reviewed-head validity is evaluated.

Acceptance fixtures shall prove: valid code-only completion without post_deploy passes; missing deployment containment fails; data-writing completion with missing or wrong-commit post_deploy evidence fails; invalid inheritance fails. Reconcile remaining legacy claim/verdict findings explicitly before B-2 preflight acceptance. Do not fabricate verdicts, rewrite historical events or suppress unresolved findings.
```

**Contract** `bash F/preflight.sh launch|bootstrap`. Exit 0 every check ok; 1 a check failed or is unknown; 64 usage. One line per check: `ok <name>` or `FAIL <name>: <reason>`.

`bootstrap`: today's repair of campaign-local dependencies (venv, node modules, ephemeris pins) against the campaign checkout; no Codex, no smoke, no receipt.

`launch`: repairs nothing; first removes `$KY_RUN/LAUNCH_RECEIPT.json`; then, in order:
1. `secrets` — none of DATABASE_URL, any `*_DATABASE_URL`, PGPASSWORD, ANTHROPIC_API_KEY is set. Names only.
2. `claude` — `$CLAUDE_BIN` (default `/Users/Dev/.local/bin/claude`) is executable and `--version` is ≥ 2.1.296.
3. `smoke` — Claude only: no Codex binary, profile or model, no `kalayantra_fleet.sh smoke`. For every `$KY_FLEET/templates/LAUNCH_CONFIG.<role>.json`: the receipt `$KY_RUN/QUALIFICATIONS/<role>-<model>.json` exists and `/opt/homebrew/bin/python3 -I -B $KY_FLEET/kyqualify.py check <receipt> --config <config> --require-context launchd` exits 0.
4. `dependencies` — the campaign checkout (`$KY_SOURCE_REPO`, default `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`) is a git work tree; `$KY_ROOT/venv/bin/python -c 'import pytest, psycopg, swisseph'`; `platform/node_modules` and `platform-mcp/node_modules` exist; the three ephemeris files match `ephemeris_pins.py`.
5. `tracker` — `GET $PRAVAHA_URL/api/health` (default `http://127.0.0.1:8767`) answers `ok: true` with no `model_error`.
6. `audit` (KU-01) — `KY_STREAM=S $KY_ROOT/bin/ky audit --since kickoff`. Exit 0: ok. Exit 1: every `FAIL <code> <ref>: …` line is echoed and must be reconciled explicitly — `$KY_RUN/AUDIT_RECONCILIATION.json` `{"schema":"ky.audit_reconciliation/1","entries":[{"code","ref","disposition","authority"}]}` must list exactly the findings' (code, ref) pairs (a finding without an entry, an entry without a finding, an empty `disposition` or `authority`: FAIL), and the count in `AUDIT FAIL: <n> findings` must equal the lines parsed. Any other exit: FAIL. Ruling P17: a planner job authors the record, an independent ARTIFACT review accepts it, preflight requires the accepted digest: `$KY_RUN/AUDIT_RECONCILIATION.review.json` {`verdict` "ACCEPTED", `inputs`: the record's sha256 as it is now, `reviewer_session_id` ≠ `author_session_id`}, else FAIL. Preflight never writes either file.
7. `slots` — `bash $KY_FLEET/local_db.sh slots` exits 0 with at least one `b` and one `v` slot (no lane list or count of its own). Ruling P16, slot PROVISIONABILITY, no standing pool required: for X = the first slot listed and its own session S = `PREFLIGHT-<UTC>-<pid>` (LOCALDB grammar `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`, no colon), `local_db.sh up --session S`, `db X --session S`, `check X` each exit 0; `$KY_RUN/local_db/X.json` is READY for S with `seed` hashes equal to the sha256 of the three `$KY_RUN/schema/` files; then `close --session S` exits 0 and the receipt is gone (KU-02). A failing step: FAIL naming it; `close` is still attempted.

On success only, atomically: `$KY_RUN/LAUNCH_RECEIPT.json` = `{"schema":"ky.launch_receipt/3","mode":"launch","ts","checks":[…],"slots":[…],"slot_proof":{"slot","session","seed":{…},"closed":true},"claude":{"path","version","sha256"},"qualifications":[{"role","model","receipt_sha256","config_sha256"}],"audit":{"exit","findings":[{"code","ref"}],"reconciliation_sha256","review_sha256"},"campaign_head","model_sha256","preflight_sha256"}`, JSON indent 1 (the model's B-3 detector reads `"mode": "launch"`).

Environment: KY_ROOT, KY_RUN, KY_FLEET (default `$KY_ROOT/fleet_live`), KY_SCRATCH (for local_db.sh), KY_SOURCE_REPO, CLAUDE_BIN, PRAVAHA_URL, SE_EPHE_PATH; test override KY_CURL (absolute path).

INTERPRETATION: (1) the Claude-only smoke = the binary's version check plus the KV-06 launchd qualification check of every installed launch configuration; preflight starts no model job; (2) path and shape of the reconciliation record and of its review, and the exact-match rule; (3) every other check of today's preflight.sh is dropped: old topology (Codex, per-lane worktrees and databases) or file-existence proxies circular with the install receipt.

**Depends on** Wave 3; tests fake all. KV3-B-LOCALDB: `slots` (one per line; exit 1 when unknown), `up`, `db`, `check`, `close` as in 7; `close --session S`: exit 0 = S's databases gone and the container removed, handed over on record, absent, or incompatible and untouched (`container=removed|handed_over|absent|incompatible`); exit 1 = not proven. KV3-B-WRAPPERS: `<root>/bin/ky`, the CLI's exit status, 78 = refused override. KV3-B-TRACKER: `ky audit` lines, exits 0, 1, 2. kyqualify.py (B-0c). KV3-B-INSTALL (wave 4) runs `preflight.sh launch` from the installed fleet; exit 0 is its precondition for `INSTALL_RECEIPT.json`.

**Acceptance** A temp KY_ROOT, KY_RUN and KY_FLEET holding fake `bin/ky`, `local_db.sh`, `kyqualify.py`, `claude` and curl; no tracker, docker, model or network: all ok → exit 0 and the receipt; each check failing alone → exit 1, `FAIL <name>`, no receipt (an earlier one gone); the negative cases; the fake `local_db.sh` log is exactly `slots`, `up`, `db`, `check`, `close` for one slot and S, `close` also after a failed step; exact reconciliation passes with its findings in the receipt; `bootstrap` writes no receipt; no "codex" in preflight.sh. A check whose command cannot run is FAIL, never ok.

**Evidence** `result.json`: each command, exit code, summary; skips named; pushed `head_sha`.

**Branch and PR** `kalayantra/kv3-b-preflight`; one PR to main, "KĀLA-YANTRA v3 KV3-B-PREFLIGHT: preflight.sh v3"; never merged by the job.

**Do not** edit outside Owns; run the real `ky`, `claude`, `local_db.sh`, docker or the tracker; author reconciliation entries; rebase or force-push; read credentials; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
