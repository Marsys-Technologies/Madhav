```json
{"id":"KV3-B-KYREPORT",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"control-plane source (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§2; §13; §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyreport.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyreport.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyreport.py -q -p no:cacheprovider",
"expected_result":"all tests pass; unknown never reads as a number or as green",
"negative_cases":[
"no verified baseline: token totals read unknown, never 0",
"a duplicated result event counts once; a killed job makes the total unknown",
"a loaded launchd job with no verified controller identity is not HEALTHY",
"an owner's report without GitHub readback: approval_reported_unverified",
"baseline import from a work-tree file or with an unaccepted receipt: refused"]},
"packet_sha256":"37aec20c4e5c420db76f67adb47fd0e3b3a52b914af4de938d7cef8de4aa357d"}
```
# KV3-B-KYREPORT: `kyreport.py` + baseline import

F = `00_ARCHITECTURE/briefs/kalayantra/fleet`; R = `$KY_RUN`.

**Pins.** Plan v2.7 at e709f60d7; base = the job header's reviewed B-0c head.

**Owns.** Create `F/kyreport.py` and `F/tests/test_kyreport.py`. Prohibited: FROZEN paths.

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
- Reported separately: distinct guarded-completed item ids, decision completions, joins,
  accepted heads, weighted progress — each with its scope denominator and observation
  boundary (historical 46 = 39 guarded + 1 join + 6 decisions).
- Persistent failure fingerprints and attempt counts (§6); `no_progress_jobs`;
  escalations; rejection rate; CI-infra retries; lead time p50/p90; four-class tokens by
  role, kind and per guarded completion.
- **Signals and their detectors (Astra v2.3 Part 5):** *loop healthy* = verified controller identity, the authorised bundle and a timely
  successful control iteration; when a child is expected, additionally its matching process
  identity and liveness; when none is expected, a legitimate recorded waiting state and no
  unreconciled child; a stopped loop reports STOPPED; missing children during legitimate
  waiting never trigger model admission — a loaded plist is not health;
  *platform approval verified* = deterministic GitHub readback bound to the expected
  repository, workflow run/attempt, environment, source SHA and required owner approval;
  an owner's report alone is `approval_reported_unverified` and keeps the external
  dependency; approval, workflow completion and semantic operation acceptance are separate
  states; *loop making progress* =
  accepted work or changed external dependency (timestamps are a proxy, never the signal);
  *probe PASS* = exact configuration + observed result + negative control + evidence hash;
  *surrogate decision* = its state (proposed / pending-veto / effective / executed / vetoed /
  failed), not a journal line; *owner notified* = submission recorded + cockpit visibility
  (reading unknown); *veto expired* = the `veto` controller's check under the decision lock;
  *WAVE_B_DONE* = derived from accepted B-0…B-5 evidence and the final receipt, never a
  file's existence; *READY_TO_START* = the release/final-acceptance detector re-run against
  the bound inputs when D-7 activates.
```

**Contract.** `python3 -B F/kyreport.py [--today] [--events E] [--model M]` prints one JSON report; it launches, admits and writes nothing. Exit 0 report · 64 usage · 66 R missing.
- A figure is measured or `"unknown"` with `why`, never 0, false or green; each carries `denominator` and `observed` {events lines, prefix sha256, from, to}. Savings and throughput: `cannot_be_estimated` (§13).
- Ruling P15: no argument = the status report of the cockpit prompt's step 4. INTERPRETATION: `--today` is its alias.
- `completions`: E (default `R/EVENTS.jsonl`) and M via the tracker's `state.build_snapshot` (`KY_TRACKER_LIVE`, default `$KY_ROOT/tracker_live`).
- `jobs`: `R/jobs/*/state.json`; a missing field is `unknown`.
- `tokens`: classes = the four `usage` keys `F/kyprobe.py` reads from a stream `result` event; owners from `R/jobs/*/state.json` (`provider_session_id`, `result_event`) and the role-state session identities (none or two: `unknown`); duplicate = same session, identical payload; a session without a `result` event only via the verified baseline; children only if the receipt's `parent_includes_children` is exactly false; any uncovered session: total `unknown`, the rest `partial`.
- `signals`, each from the source named, else `unknown`:
  - `loop_healthy` (`kyloop.py admin show <loop>`, `admin child <loop>`): `STOPPED` if `R/STOP_<loop>` exists or `enabled` is false. `HEALTHY` needs: `controller` pid and `process_start` alive (R2 rule); `bundle.receipt_sha256` = sha256 of `R/INSTALL_RECEIPT.json` now; child `alive` when `expected_child` is set, else a recorded `waiting` state, child `none`, `last_iteration_at` ≤ 120 s old (INTERPRETATION: 4 × kyloop's longest poll). Else `UNHEALTHY`.
  - `platform_approval`: `kyreport.py approval --expect X` (X: repository, run_id, run_attempt, environment, source_sha, required_approver), read back with `KY_GH` (default `gh`); a report alone: `approval_reported_unverified`; completion and operation acceptance are separate fields; exit 0 only when `verified`.
  - `loop_progress`: `no_progress_count`. `probe_pass`: `kyqualify.py check … --require-context launchd --verify-evidence`. `surrogate_decision`, `veto_expired`: `kyveto.py status`. `owner_notified`: `notification.submitted` and the `[notify=submitted]` journal line. `WAVE_B_DONE`: the `R/WAVE_B_DONE` marker, its bound sha256 re-checked. `READY_TO_START`: `kygate.sh --pre-resume`.

Baseline import (INTERPRETATION): `kyreport.py baseline-import --repo G --commit C --path P --review-receipt V --dest D` takes blob `C:P` from the object store only; V = {`verdict` "ACCEPTED", `reviewer_session_id` ≠ `author_session_id`, `source_commit` C, `inputs[P]` = the blob's sha256}; under one kyaction record it writes D and `R/BASELINE_RECEIPT.json` {source_commit, path, sha256, review_receipt_sha256, installed_path, parent_includes_children: null}; else exit 1, reason, nothing written.
Ruling P14: P is KV3-B-BASELINE's `scripts/token_economy/token_baseline.py`, imported only from its independently reviewed head. Totals exist only while the receipt is present, `installed_path` hashes to `sha256` and every session is covered; else `unknown`. One adapter: `python3 -B <installed_path> [--since D] [--until D] --json OUT` (keys `sources`, `grand_total`, `by_role`, `top_sessions`). This job: fixtures only, no real import.

**Depends on.** Wave 2. B-0c `kyloop.py`, `kyveto.py`, `kyqualify.py`, `kyaction.py` (read-only); KV3-B-BASELINE (wave 1). Optional (`unknown` if absent): KV3-B-KYGATE (same wave); KV3-B-KYDJOBS' job state (wave 3), pinned keys `job_id item kind role phase provider_session_id result_event`.

**Acceptance.** Tests use a fake `gh` and a temp `KY_RUN`. The seven §13 fixtures. Each signal: one fixture where it holds, one where it is `unknown` or negative. A waiting loop without a child is `HEALTHY`; nothing is started.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16): commands, exit codes, pushed `head_sha`, `notes`.

**Branch and PR.** `kalayantra/kv3-b-kyreport`; one PR to `main`: `KĀLA-YANTRA v3 KV3-B-KYREPORT: kyreport.py + baseline import`; never merged by the job.

**Do not.** Edit outside `d1_paths`; let tests reach the network or a model; read `~/.claude` or credentials; rebase or force-push; touch production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time.
