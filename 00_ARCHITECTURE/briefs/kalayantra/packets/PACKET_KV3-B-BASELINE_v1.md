```json
{"id":"KV3-B-BASELINE",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"Wave B bootstrap packet (plan §4 roster; §13 measurement source)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§2; §13; §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"scripts/token_economy/token_baseline.py",
"scripts/token_economy/tests/test_token_baseline.py"],
"acceptance":{
"command":"python3 -B -m pytest scripts/token_economy/tests/test_token_baseline.py -q -p no:cacheprovider",
"expected_result":"exit 0, nothing skipped; the committed script hashes to 28c1bb5b9df644a0a60a44a80b0a9a01c949db2838e03bf766631411b45c4176",
"negative_cases":[
"the scratch source hashes to anything else, or is missing: blocked, nothing committed",
"one byte of the committed script changed: the hash test fails",
"a call repeated on several lines or in a second transcript is counted once",
"a transcript cut mid-line (killed job) adds no call and raises nothing",
"a test that would read ~/.claude, ~/.codex or /Users/Dev/kalayantra/logs: the root guard fails it"]},
"packet_sha256":"c5f27a7ee27f2580dae260646699afde7bfed9ade657b775bdfd4049439cc714"}
```
# KV3-B-BASELINE: the token-baseline script, committed for independent review

P = `scripts/token_economy/token_baseline.py`; SRC = `/Users/Dev/scratch.noindex/claude/madhav/20261011-token-economy/token_baseline.py`; H = `28c1bb5b9df644a0a60a44a80b0a9a01c949db2838e03bf766631411b45c4176`.

**Pins.** Plan v2.7 at e709f60d7; base = the reviewed B-0c head in the job header. Ruling P14: the script's bytes are SRC, sha256 H (26,018 bytes).

**Owns.** Create P (git mode 100644) and `scripts/token_economy/tests/test_token_baseline.py`; nothing else. Prohibited: FROZEN paths (BS-05); every other file of SRC's directory (read that one file only).

**Spec** (verbatim).
```excerpt plan §13
- The baseline implementation must be independently reviewed, installed from a
  receipt-bound immutable source head and proven to cover the reported sessions **before**
  any v3 total is reported (a main merge is not a prerequisite). Missing source or coverage
  is reported as unknown, never zero.
- Accounting ownership is defined for every provider session and child session;
  repeated result events are de-duplicated; transcript usage is used only for uncovered
  calls; whether parent usage includes children is proven before child totals are added.
  Fixtures: normal completion, duplicate results, killed job, parent/child sessions,
  interactive planner/conductor sessions, bootstrap jobs, missing records.
```
```excerpt plan §2
Token audit + baseline script (scratch source recorded in the audit) | audit worktree | independently reviewed, installed from a receipt-bound immutable source head and proven to cover the reported sessions before any v3 total is reported (§13; no merge required)
```
```excerpt plan §14 B-1
`kyreport.py` + baseline import
```

**Contract.**
1. Copy, never write. Before anything else compute sha256(SRC). Missing, unreadable or not H: stop, `blocked`, `source-drift: token_baseline.py` with the hash observed; nothing is committed. Equal: copy the bytes unchanged to P. The committed blob must hash to H (`git show HEAD:P | shasum -a 256`) and a test asserts it for the work-tree file. No byte of P is edited, formatted or "fixed": a defect you find goes to `notes`; this packet commits the candidate, the independent review judges it.
2. What P is (read from the bytes; do not change it). Read-only, standard library. `python3 -B P [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--json OUT] [--md OUT] [--waste] [--jobs N]`, exit 0; `main(argv=None)`. Three module-level roots: `CLAUDE_ROOT` (`~/.claude/projects`, `**/*.jsonl`), `CODEX_ROOT` (`~/.codex/sessions`, `**/rollout-*.jsonl`), `FLEET_LOGS` (`/Users/Dev/kalayantra/logs`, `*.log`). Four classes, `CLASSES` = `input`, `output`, `cache_creation`, `cache_read`. A call is keyed `(message.id, requestId)`; repeats keep the per-class maximum, within a file and across files. A line that is not JSON is skipped. Only paths that `is_madhav()` accepts are counted (the pytest base path may itself hold one of its tokens: assert that filter on the function, not on a directory name). JSON keys include `sources` (`claude_files`, `claude_files_with_usage`, `codex_madhav_sessions`, `fleet_logs`, `claude_api_calls_deduped`, `claude_cross_file_duplicate_keys_dropped`), `grand_total` (the four classes + `total`), `by_provider`, `by_role`, `by_model`, `by_workspace`, `top_sessions` (20 at most).
3. The tests are the work. Each imports P as the module `token_baseline` (its directory on `sys.path`, so that the script's own worker processes can import it too), points the three roots at fixture directories it writes under the pytest base, and calls `main(["--json", <out>, "--jobs", "1"])`. A root guard (autouse) fails any test in which one of the three names still has its default value. No test reads a real transcript, log or home directory, or the network.
4. One fixture per name in the excerpt, built by the test, with token figures chosen by you so that every expected sum is computed by hand in the test:
   - normal completion: one transcript, several calls: the four classes and `total`, `claude_api_calls_deduped`.
   - duplicate results: one call on several lines with growing usage, and the same key again in a second file: counted once, at the per-class maximum; `claude_cross_file_duplicate_keys_dropped`.
   - killed job: the last line cut mid-JSON: the earlier calls counted, no exception.
   - parent/child sessions: a parent transcript and a `/subagents/` file of the same session: what is summed, and which role and `subagent_files` value the child gets.
   - interactive planner/conductor sessions; bootstrap jobs: transcripts whose `cwd` is a relaunch-plan checkout, the campaign checkout and a bootstrap worktree: the workspace and role each receives.
   - missing records: empty roots, and a root that does not exist: exit status, `sources`, `grand_total`.
5. INTERPRETATION: these are characterisation tests of fixed bytes. Arithmetic and de-duplication are asserted against hand-computed values. A label (workspace, role) or an empty-input result is asserted as observed, and wherever the observed behaviour does not meet the excerpt (a zero where the plan wants unknown; no proof that parent usage excludes children; a session outside `top_sessions`) the test pins it and `notes` carries one line `gap: <fixture>: <what P does>`. Never `xfail`, `skip`, or an assertion weakened to pass. KV3-B-KYREPORT turns every gap into `unknown`.

**Depends on.** Wave 1; nothing. KV3-B-KYREPORT (wave 2) may assume: the path P; the call form `python3 -B <installed copy> [--since D] [--until D] --json OUT` and the keys of 2; that nothing is installed or reported from P until this packet's pushed head is independently reviewed and imported by `kyreport.py baseline-import` (receipt `$KY_RUN/BASELINE_RECEIPT.json`): until then every baseline-backed figure is `unknown`.

**Acceptance.** `acceptance.command`. Write the tests first: they fail while P is absent, pass once the verified bytes are copied. Shown: the hash test (and that it fails on a copy with one byte changed, made under the pytest base); the fixtures above, all seven names; the root guard. Every assertion is on a value P produced in that test run; a fixture P cannot read fails its test, it is never counted as passed.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16): sha256(SRC) as observed and the committed blob's sha256; each command with its exit code; pushed `head_sha`; `notes`: every `gap:` line and each pinned label.

**Branch and PR.** `kalayantra/kv3-b-baseline`; one PR to `main`: `KĀLA-YANTRA v3 KV3-B-BASELINE: token baseline script`; body: the two hashes, the fixtures, the gaps. Never merged by the job (hold).

**Do not.** Edit P's bytes; run P against the real roots; read `~/.claude`, `~/.codex`, `/Users/Dev/kalayantra/logs` or any other scratch file; install or import the baseline; rebase or force-push; touch credentials, production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
