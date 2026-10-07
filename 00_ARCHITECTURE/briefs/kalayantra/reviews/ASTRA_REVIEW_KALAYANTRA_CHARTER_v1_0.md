---
artifact: ASTRA_REVIEW_KALAYANTRA_CHARTER
version: "1.0"
verdict: REWORK
blocking_count: 11
reviewed_commit: dee68bae88dc7f4b35d30a9c40877768b377889c
review_date: 2026-10-06
review_mode: read-only
---

# 1. Verdict and the five things that matter most

**REWORK. Do not launch this fleet as written.** It can start processes, but it cannot reliably preserve ownership, enforce review, complete the Gochara transition, or prove the charter’s five completion conditions.

1. **The control plane does not provide the guarantees the fleet assumes.** Two K workers can claim the same item. A merged branch can complete an item regardless of its review, unfinished steps, or dependencies. A sufficiently long rejection report completes a packet-review item. These are correctness failures, not cosmetic tracker deficiencies. [CH:127–145; T/events.py:99–144; T/state.py:89–123; T/detectors.py:217–224]

2. **The credential boundary is absent.** `env "${envs[@]}"` preserves the supervisor’s exported environment, including both credential variables, in every lane. Unsandboxed agents sharing the operator’s Unix account can also read credential files and other worktrees. Prompts cannot make disclosure impossible. [FLEET:112–125; ENV:8–13; CH:99]

3. **The Gochara sequence contradicts its operational prerequisites.** J-1 queues changes that must remain unmerged through the small tests; retaining test rows prevents subsequent dispatch; the final-rules candidate and several inherited prerequisites have no explicit delivery path. [M:973–1024; SMALL:32–34,61,70; FINAL:219–236; DISPATCH:457–462]

4. **The flip is both incorrectly permitted and mechanically obstructed.** G6 admits `insufficient_evidence`, contrary to the evaluation protocol. J-5 tests a nonexistent `sealed` publication status. Migration 1236 rejects the authority switch to `'5.0'`; its replacement is missing. [OS:39; EVAL:178–222; M:1122,1164; MIG1236:46–51]

5. **The campaign can declare completion while substantial charter work remains unfinished.** C-3’s dependency closure excludes all K7 work, four certification mappings, Avadhi, relationship resolution, and other items. The four authoritative Kāla specifications are also absent from both supplied checkouts, so exact §9/R12/specification completeness cannot be certified. [M:380–488,835–932,1244–1375; CH:12–16,34–38]

The current model contains **81 items**, including B-3b. This review incorporates the modified `local_db.sh` present at final inspection. No builds, database connections, or file writes were performed.

## Evidence notation and limits

The following aliases make the citations readable. A citation such as `FLEET:123` means that exact file and line.

| Alias | File or directory |
|---|---|
| `KY` | `00_ARCHITECTURE/briefs/kalayantra/` |
| `CH` | `KY/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md` |
| `OS` | `KY/KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md` |
| `KICK` | `KY/KALAYANTRA_KICKOFF_PROMPT_v1_0.md` |
| `S`, `N`, `V`, `K` | `KY/prompts/SUTRADHARA.md`, `ADHIKARIN.md`, `PARIKSAKA.md`, `KARAKA.md` |
| `FLEET`, `INSTALL`, `PREFLIGHT`, `PRECHECK`, `LOCAL`, `ENV` | Corresponding files in `KY/fleet/` |
| `M` | `00_ARCHITECTURE/control/kalayantra/plan_model.json` |
| `P` | `/Users/Dev/madhav-l3/pravaha/` |
| `PB` | `P/00_ARCHITECTURE/briefs/pravaha/` |
| `PM` | `P/00_ARCHITECTURE/control/pravaha/plan_model.json` |
| `T` | `P/platform/scripts/governance/pravaha_tracker/` |
| `PP`, `PE` | `PB/PRAVAHA_CAMPAIGN_PLAN_v1_0.md`, `PRAVAHA_EXECUTION_ARCHITECTURE_v1_0.md` |
| `SMALL` | `PB/runbooks/SMALL_TEST_SITTING_CHECKLIST_v1_0.md` |
| `MEASURE`, `FINAL` | `PB/decisions/MEASURING_BUILD_CONTRACT_v1_0.md`, `FINAL_BUILD_SCOPE_v1_0.md` |
| `EVAL` | `PB/measurement/EVALUATION_PROTOCOL_v2_3.md` |
| `RULING10` | `P/00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_RULING_SHEET_v1_0.md` |
| `CI`, `DEPLOY`, `TAP` | `.github/workflows/ci.yml`, `deploy.yml`, `tap-ci.yml` |
| `SCHEMA`, `DRIFT`, `CLASSIFY` | `platform/scripts/governance/schema_validator.py`, `drift_detector.py`, `ci_changes.py` |
| `GIP`, `HYGIENE` | `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`, `ONGOING_HYGIENE_POLICIES_v1_0.md` |
| `COORD` | `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` |
| `MIG1081` | `platform/migrations/1081_nirmana_l3_gochara_ledger_coverage_publication.sql` |
| `MIG1236` | `platform/migrations/1236_gochara_authority_refuses_governed_generation.sql` |
| `AUTH527` | `platform/supabase/migrations/527_kala_gochara_generation_authority.sql` |
| `MIGRATE` | `platform/scripts/migrate.ts` |
| `DISPATCH` | `platform/scripts/dispatch_v5_small_test_job.py` |

The four requested Kāla specification files, both Nirmāṇa supervisor precedent files, and `00_ARCHITECTURE/autonomy/CHARTER.md` were absent from both allowed checkouts at final inspection. Their absence is filesystem evidence; there are no source lines to cite. References to them are present at `CH:12–16,97` and `OS:12`.

Consequently, the answers below distinguish **verified execution defects** from **comparisons that cannot be completed without the missing specifications**. I have not reconstructed or re-reviewed those specifications from their titles.

# 2. Findings table

| ID | Severity | File:line | What | Why it fails | Fix |
|---|---|---|---|---|---|
| KY-01 | BLOCKING | CH:12–16; K:12 | Authoritative implementation specifications are absent | Workers cannot read their governing contracts; exact scope/order cannot be audited | Package the reviewed documents and verify their hashes before bootstrap completion |
| KY-02 | BLOCKING | CH:127; T/events.py:99–144; T/cli.py:314–317 | Claims are neither exclusive nor tied to individual workers | Both K workers append valid `running` events; no state comparison or claim lease exists | Atomic claim transaction with worker identity, lease, dependency validation, and recovery |
| KY-03 | BLOCKING | CH:145; T/state.py:89–123; T/detectors.py:186–224 | Completion bypasses review, dependencies, and steps | Merge wins over rejection; file length accepts a rejecting review; an unchanged branch at main can appear merged | Composite completion predicate tied to reviewed head, required steps, dependencies, and accepted findings |
| KY-04 | BLOCKING | FLEET:112–125; ENV:8–13; OS:67 | Credentials and filesystem authority reach unsandboxed agents | Environment inheritance leaks both URLs to all lanes; same-user access defeats prose restrictions | Isolated execution identity/mounts and a fixed-operation credential broker; no database credentials in agent environments |
| KY-05 | BLOCKING | KICK:26–34; S:9–12; M:157–256 | Bootstrap launches before its prerequisites are established | Wrong tracker remains selected; detached preflight fails; K0a does not depend on B-1/B-4/B-3b | Reorder bootstrap, select the copied package explicitly, validate lane environments, and gate work on bootstrap acceptance |
| KY-06 | BLOCKING | M:973–1109; OS:40; SMALL:32–34,61,70 | Gochara PR landing and test sequence are invalid | G8/slice changes land too early; retained receipts prevent run 2; measuring build must precede final-rule changes | Explicit pre-small-test, measuring, protected-window, final-rules-candidate, final-build phases |
| KY-07 | BLOCKING | OS:39; EVAL:178–222 | G6 weakens flip eligibility | `insufficient_evidence`, rank-unproven, or unverifiable coverage can be treated as acceptable | Require every applicable protocol endpoint and A5.7 engineering gate to pass; no permissive fallback |
| KY-08 | BLOCKING | M:1122–1167; MIG1081:116; MIG1236:46–51 | Seal/flip detectors and migration path are wrong | No `sealed` status; J-5 can wait for publication that depends on J-5; authority CHECK rejects `'5.0'` | Use seal predicate, authority-pointer evidence, serving receipt, and an explicit reviewed replacement migration |
| KY-09 | BLOCKING | M:1244–1375; CH:34–38 | Final join does not join the promised work | C-3 can finish with K7, mappings, and other mandatory work incomplete | Explicit mandatory-item join, conditional dispositions, full coverage matrix, and post-stop receipt |
| KY-10 | BLOCKING | CH:209–211,285; M:489–580; COORD:28–50 | Automatic deploys lack compatibility and lease gates | Rewrites can reach production before replacement data/consumers; ordinary merges trigger deploy eligibility outside the lease protocol | Expand/contract delivery, pinned candidate readers, deploy-bound lease and readback gates |
| KY-11 | BLOCKING | N:12,26; M:1006–1125,1288–1305 | Production execution and completion have no complete autonomous path | N arms an unspecified next cycle; N is forbidden to mark manual items done; K owns verification/seal; missing credentials are declared optional despite mandatory production outcomes | Durable operation requests, separate executor/verifier/sealer identities, explicit lifecycle states, capability preflight |
| KY-12 | HIGH | FLEET:123–160,177–194 | Supervisor duplication and orphaning | Repeated `up` duplicates loops and loses PID records; `down` kills watchdog parents; timeout kills one PID, not descendants | Process locks, process-group termination, graceful stop followed by bounded forced stop |
| KY-13 | HIGH | FLEET:82–84,108,139–157; CH:269–272 | Budget and quota accounting are incorrect | Only K is capped; concurrent completions overshoot; fixed lanes remain unlimited; old log text can repeatedly trigger backoff | Atomic cycle-start reservations for all lanes; current-cycle logs; bounded idle scheduling |
| KY-14 | HIGH | INSTALL:12–20,35,69–71; T/events.py:32,81–85,122–123; T/cli.py:279–280 | “One generalisation” is insufficient | Changing CLI choices does not update reader validation or stream-to-stream policy; reinstall retains sibling package | Generalise all message paths, configure HOLD, validate model health, explicitly switch package |
| KY-15 | HIGH | LOCAL:29–44; MIGRATE:138–163; KICK:29 | Local database bootstrap is not a proven rehearsal environment | Fresh replay encounters protected migrations; role errors are swallowed; `set -e` skips intended diagnostics; wrong checkout may be replayed | Reviewed local fixture/replay recipe, exact lane head, production major version, fail-closed assertions |
| KY-16 | HIGH | PRECHECK:16–46; CI:137–139,2143–2185,2316–2364 | Precheck is neither equivalent nor reliably selective | False-red baseline handling; absent DB setup; omitted governance checks; basename test selection misses suites | Separate fast local checks from full CI, use explicit test manifests and correct CI baseline semantics |
| KY-17 | HIGH | M:596–727; RULING10:61 | Value checkpoint precedes the full G1 implementation it claims to test | Clock repair alone is not the later as-of/axis/suppression/breakpoint/null implementation | Build frozen G1 baseline before checkpoint; retain independent scorers and ruling-10 eligibility rules |
| KY-18 | HIGH | PM:561–592,773–875,1268–1280,1369–1440; M:973–1226 | Absorption does not cover every inherited obligation | Missing baseline, upstream release, second window, final-rules candidate, soak, retirement, Tier-2 and L5 closure paths | One disposition for every remaining Pravāha item, decision, PR, and operational hold |
| KY-19 | HIGH | T/runner.py:26–38,175–184; S:13; K:27 | Hand-over does not establish exclusive ownership | Old runners retain A/B authority; new worktrees fail original preflight; shared run state can be overwritten | Quiesce only absorbed runners, preserve state, record claimant transfer, update worktree registrations |
| KY-20 | HIGH | S:12,28; SCHEMA:475–570,715–750 | Handshake/scope instructions cannot truthfully satisfy governance | Missing required fields, unverified lease/profile, literal brace globs, incomplete allowed paths | One explicit campaign exception and complete validated handshake before state-changing work |
| KY-21 | HIGH | S:18–24; V:11–15; INSTALL:8; M:208–236,1213–1226,1337–1375 | Evidence paths and shutdown ownership are inconsistent | Relative `run/` points into lane worktrees; verdict directory is absent; close kills its author/verifier; campaign checkout may never receive evidence | Absolute runtime paths, committed evidence references, and an external finalizer |
| KY-22 | HIGH | CH:182–183; K:12–14,27; S:17 | Branch, PR, and review protocol contradicts itself | Rebase requires rewriting published branch history; shared GitHub author scope reaches other work; first step PR can finish whole item | Item-owned PR inventory, merge-main or replacement branches, per-slice items, review before queue |
| KY-23 | HIGH | CH:269; M:973–1024,1055–1109,1198–1210; V:11–14 | Units exceed the watchdog and verifier capacity | Multi-hour builds and multi-PR triage are placed inside 90-minute sessions; one verifier serialises the fleet | Dispatch/poll/readback as separate units; smaller implementation items; verifier concurrency within budget |
| KY-24 | MEDIUM | CH:176; T/state.py:214; FLEET:87–101 | Orientation is underspecified | Fresh sessions lack pinned contracts, ownership/resume records, exact tests, and compatibility boundaries | Generated item brief with immutable references and resume manifest |
| KY-25 | MEDIUM | M:58–90; T/state.py:143–174,251–261; FLEET:164–174 | Dashboard can look healthy without useful progress | Phases lack `lanes`; K heartbeat masks individual failures; status checks log timestamps; detector completions are absent from event-only throughput | Per-worker heartbeat, semantic completion counters, queue age and progress receipt |
| KY-26 | MEDIUM | PREFLIGHT:8–9,16–19,33–50; INSTALL:8–10 | Preflight is incomplete and brittle | Repairs only campaign dependencies, not lane dependencies; required production capabilities are warnings; fresh LaunchAgents directory may be absent | Separate bootstrap/launch preflight; argument-safe checks; provision every lane |
| KY-27 | LOW | CH:9,65,93,125,227; FLEET:170 | Stale descriptions and naming | Premature review claim; VC-3 absent; three fixed agent roles described as four; B-1/B-2 confused; port mismatch | Correct documentation and derive counts/ports from configuration; `date -r` itself is valid here |

# 3. Answers A1–G2

## A. Will the fleet actually run?

### A1. Bash walk-through

`bash -n` passes. The important distinctions are:

| Lines | Result |
|---|---|
| `14` | `set -u` is not `set -e`. Failed commands generally continue unless checked. Adding `set -e` indiscriminately would introduce new failures around intentional nonzero results. |
| `16–40` | Defaults and quoted paths are generally sound. Directory creation failures are not checked. `KY_REPO_MAIN` is used for fetch and worktree metadata mutations despite the “never written” comment. |
| `45–48,202` | Arbitrary nonempty lane names are accepted. Unknown names produce empty roles; `kanything` enters numeric logic. Validate the closed lane set. |
| `50–55` | Digit validation accepts `08`/`09`; Bash arithmetic interprets leading zero as octal and errors. Strip leading zeros or parse base 10 safely. |
| `58–66` | Worktree creation can fail permanently before the loop. Existing worktrees are accepted without checking repository, branch, or ownership. Detached creation conflicts with tracker branch validation. |
| `69–79` | Shared backoff reads/writes are unlocked; malformed content enters arithmetic, and concurrent expiry/write can remove a newer backoff. |
| `82–84` | **Not a zero-match bug.** `grep -c` emits `0` and exits 1 when there are no matches. Under `set -u` without `set -e`, assignment continues and outputs zero. Missing-file output falls back to zero. |
| `87–101` | The role prompt is expanded correctly. The charter is referenced by path, not embedded. Hard-coded CLI path ignores a changed `KY_ROOT`. A failed `cat` does not stop launch. |
| `108` | Same zero-match observation. Counting completed records gives sensible serial numbering, but duplicate supervisors can choose the same number and active/killed cycles are absent. |
| `109–110` | `mktemp`/prompt-generation failure is not checked. |
| `113,123` | `"${envs[@]}"` is **correct Bash array expansion**. The defect is inherited environment, not quoting. |
| `114–118` | Arming is consumed before proving credentials or identifying the operation. The log claims a credential is present even if both variables are empty. |
| `123–136` | **`wait "$pid"` is valid:** the background subshell is a child of the supervisor shell. There is no “wait from the wrong subshell” bug here. |
| `125,140` | Shared append-only lane logs and reused last-message files can mix old/current evidence and copy sensitive last-message text into another log. |
| `128–133` | Watchdog can exceed its nominal deadline by roughly the polling interval plus grace period. More seriously, it kills one PID, not necessarily tool subprocesses or nested reviewers. |
| `139` | Completion-only accounting is not a reservation system or reliable spend ceiling. |
| `141` | Scans the last 60 lines of the entire historical lane log. An old quota message can trigger another 30-minute pause after a subsequent short cycle. |
| `149` | Initial worktree failure exits the supervisor. Nothing restarts it. “A lane cannot die” is false. |
| `151–152` | HOLD takes precedence over STOP, so STOP is never processed while HOLD remains. |
| `154–157` | Cap applies only to K workers, despite a fleet-wide promise. The 600-second sleep delays responsiveness. |
| `164–174` | Status does not prove supervisor or worker liveness. Queue count is repository-wide. **macOS `date -r "$log"` works in this environment**; I checked it read-only. |
| `177–186` | `up` clears HOLD, truncates PID ownership, and starts duplicates. It is not idempotent. |
| `182` | `nohup "$0"` works for the normal executable-path invocation here. It is fragile when invoked with a nonexecutable script or unresolved relative/name-only `$0`; use absolute self-path plus `bash`. |
| `190–194` | `down` kills loop parents, potentially leaving Codex/tool children running without their watchdog. Its explanatory message is then false. |

**Stops execution:** detached-branch preflight, unavailable dependencies/specifications, invalid arithmetic inputs, initial worktree failure.

**Corrupts ownership/accounting:** duplicate `up`, non-atomic claims, completion-only budget, old-log quota detection, aggregate K heartbeat.

**Operationally dangerous:** inherited credentials, orphaned descendants, automatic queueing before review.

**Cosmetic or not bugs:** `grep -c` zero-match behaviour, quoted environment array, parent-shell `wait`, and observed macOS `date -r`. [FLEET:14–204; T/cli.py:158–184]

### A2. Fresh sessions versus resume

Fresh sessions are a reasonable default **after durable state is made sufficient**. They bound context accumulation and make the latest work order authoritative. Resume would preserve useful debugging context but would not repair missing claims, stale reviews, or absent specifications. [CH:95–101,176; K:9–14]

My estimate is **roughly 12,000–30,000 input tokens and 3–8 minutes of orientation per substantive cycle**, depending on the cited card and source inspection. This is an estimate, not a measurement. It makes 20-minute units relatively expensive.

The current orientation set is insufficient. Each item needs:

- exact specification sections and hashes;
- cross-cutting contracts, especially candidate identity, publication, numerical equivalence, and certification;
- owned files and shared-file exclusions;
- required tests, mutation oracles, and migration recipe;
- current branch/head, claim identity, unfinished step, and next action;
- inherited Pravāha decisions and deployment compatibility obligations.

`next` does not preserve an arbitrary rich plan specification as an execution brief; the snapshot’s item detail is operational state. The title alone cannot carry these contracts. [CH:176; T/state.py:214; M:238–319]

### A3. Isolation

No. The bypass flag removes the execution boundary that would enforce the prohibitions. A worktree isolates working files, not the Unix account, credentials, shared Git metadata, or executable authority. [FLEET:61–62,123; CH:51,99]

The smallest useful controls are:

1. **Dedicated campaign clone** under the fleet root, avoiding the main repository’s shared stash, local branch namespace, and worktree administration.
2. **Isolated worker identity or container/VM**, mounting only its checkout, necessary read-only specifications, and local database endpoint. Do not mount the operator’s home or other campaigns.
3. **Push broker or scoped credential** allowing only assigned campaign branches; deny direct main pushes, force updates, deletion, and unrelated refs.
4. **Fixed-operation production broker**, separate from model-controlled shell access.
5. **Process and claim locks**, with per-worker identity.

A pre-push hook and PATH shim are useful accident guards, but an unsandboxed agent can bypass both with another executable, `--no-verify`, or direct filesystem access. They cannot provide the requested guarantee.

### A4. Credential paths

The immediate leak is deterministic environment inheritance: every Codex child retains `KY_BUILDER_DATABASE_URL` and `KY_OWNER_DATABASE_URL` exported by `ENV`. Setting `DATABASE_URL` only for N does not remove those aliases elsewhere. [ENV:8–13; FLEET:113–125]

Further paths are:

- `env`, shell tracing, exception diagnostics, or connection objects in tool output;
- complete stdout/stderr capture;
- `-o` last-message output;
- supervisor copying the last line;
- free-text tracker notes/messages/evidence and their event-log persistence;
- sourced `pgenv.sh` and same-account access to its contents. [FLEET:125,140; T/cli.py:300–327; T/events.py:139–145; OS:67]

**No prompt can make leakage impossible while giving the model a general shell containing the secret.** Redaction is a secondary defence, not the boundary.

The supervisor must start agents with an allowlisted environment. Agents must submit only a typed operation request containing item, chart, generation, reviewed commit, image digest, lease, and expiry. A separate identity executes a closed command set and returns a credential-free receipt. Raw broker errors and environment dumps must not enter agent logs or tracker detail. Read-only database access should use the same approach if credential confidentiality is required.

## B. Will the control plane work?

### B1. Second-instance compatibility

**The HTTP tracker can largely run as a second instance; the proposed operational protocol cannot.**

The listed environment overrides correctly separate home, event log, model, repository, port and database environment. Separate launchd label and port are appropriate. [INSTALL:23–63; T/server.py:51–58]

Remaining assumptions:

| Assumption | Consequence |
|---|---|
| CLI `send --to A|B|C`, actor only steward/native | V-to-K syntax fails before generalisation. [T/cli.py:279–280] |
| `events.PARTIES` hard-coded | Changing only argparse still rejects S/N/V/K recipients; the event reader uses the same validator. [T/events.py:32,81–85,189] |
| Streams may message only steward | Even a model-derived `--as V` remains rejected without changing message policy. [T/events.py:117–125] |
| HOLD is `HOME/run/PRAVAHA_HOLD` | It does not observe `$KY_ROOT/HOLD`. [T/cli.py:182; T/server.py:58] |
| `runner.py` has original A/B/C configuration and absolute brief/worktree assumptions | It is not a reusable KY runner. The new fleet does not need it, but hand-over must stop its old writers. [T/runner.py:26–38] |
| Preflight requires registered worktree and branch regex | New detached lanes fail. [T/cli.py:173–181; M:15,26,37,53] |
| Health means recent engine tick | HTTP 200 is not proof of a valid model, correct package, or functioning detectors. [T/server.py:350–354] |
| Phase rendering expects `lanes` | Current phase objects do not populate the intended phase grouping. [T/state.py:251; M:58–90] |
| Installer retains `TRACKER_GOV` or sibling default | Re-running it without `--gov` does not switch to the copied code. [INSTALL:12–17,35; S:10] |

The one generalisation is **not sufficient**. Pool ownership and completion semantics require substantive additions beyond stream identifiers.

### B2. Pool semantics

- **Does `start` refuse RUNNING? No.** It appends a `running` event after structural ownership validation. There is no state comparison. I exercised the pure validator twice with the same K start event; both were accepted. [T/cli.py:314–317; T/events.py:99–144]
- **Does `next` return dependency-ready items? Its `ready` array does**, based on the current snapshot. It also returns separate running/review and blocked arrays. A stale snapshot can be used by CLI fallback, and `start` does not revalidate readiness. [T/server.py:355–362; T/state.py:187–205; T/cli.py:108–119]
- **Does `done` require the owner? Generally yes, but at stream level.** All six K workers share that owner. `steward` and `native` bypass item ownership. Evidence is required as text, not verified as a receipt. [T/events.py:67–69,106–116]
- **Can V send the proposed verdict now? No.** The current CLI rejects K recipients and V actors. After full generalisation, the message can exist, but messages are not an item-completion gate. [T/cli.py:279–304; T/state.py:40–68,89–123]
- **Two `next` calls in one second:** both can receive the same item and both starts succeed. Timestamp precision is incidental; the race exists at any interval before another observation changes the choice.

A claim needs a distinct `worker_id`, opaque claim token, expiry, renewal, and atomic compare-and-set. Stream K can remain the routing group.

### B3. Schema, detectors and DAG

The current **81-item** JSON passes the tracker’s `check_model()` validation. `steps` as strings, `done_by: decision`, decision IDs, and basic detector shapes are accepted. That validates structure, not the intended execution guarantees. [M:138–1492; T/server.py:269–298; T/state.py:82–85,119–132]

**SQL defects:**

- Publication status allows `candidate`, `published`, `superseded`, `rolled_back`; it has no `sealed`. [MIG1081:103–122]
- J-5 therefore recognises only its `published` alternative. Publication is downstream of J-5 through J-6a/D-FLIP: a semantic deadlock. [M:1112–1165]
- J-6 does not check `kala_gochara_authority`, seal validity, the expected manifest, or an actual served response. A publication row is insufficient. [M:1164; AUTH527:81–107]
- A `db_query` with `expect: nonempty` must return **no rows on false**. `SELECT false` would still pass. [T/detectors.py:236–245]

Most item branch refs correctly follow `kalayantra/<lowercase-id>`. B-1 intentionally uses `campaign/kalayantra`; inherited PRs use PR-number detectors. The branch detector already has a squash-merge fallback—squash itself is not broken. Its ancestor shortcut is too permissive for an unchanged branch created at main. [M:138–155,238–257,1027–1052; T/detectors.py:180–204]

There are no structural cycles or dangling dependencies. There are semantic deadlocks and omissions:

- K0a can start without B-1, B-4 or B-3b. [M:238–256]
- K3 does not wait for V-K12. [M:473–509]
- V-K3 excludes the real-generation K3-2 integration. [M:511–524,1229–1241]
- Full G1 follows the checkpoint that claims to evaluate it. [M:596–670]
- V-K5 excludes conditional K5-2/K5-3. [M:684–726]
- K8-REG excludes K8-K0a/K12/K3/K4. [M:835–932]
- K9 excludes all K7 work. [M:1244–1256]
- J-3 requires a `d_g9_ruled` step while D-G9 depends on J-3. [M:1055–1081]
- A refusal of D-G2 is still “decision done,” enabling K5-3. [M:672–710; T/state.py:119–123]
- Final review attempts to verify all five completion lines before close and shutdown happen. [M:1322–1375]

C-3’s ancestry excludes:

`B-1, B-3b, B-4, K2-2, K7-1, K7-2, K7-3, K1-2, V-K12, D-G2, K5-2, K5-3, K8-K0a, K8-K12, K8-K3, K8-K4, L0-M, D-R5, D-R6, D-R8, D-R9`.

That list was calculated from the current JSON. Some decisions are intended defaults or optional work, but the mandatory omissions alone invalidate the close join.

**Exact comparison with architecture plan §9 remains unverified because that file is absent.** The deviations above are established against the campaign’s own promises and available operational specifications.

### B4. Decisions

`decide` appends a decision event with state `decided`, or `delegated` when requested. Either state completes the decision item. `--as steward --delegated` works irrespective of stream N because the accepted actor is `steward`. [T/cli.py:286–312; T/events.py:126–131; T/state.py:119–123]

No new-model decision requires an authenticated human `native` actor. The `owner` descriptions in `decisions[]` do not enforce authority. The residual “awaiting the native” display is wording, not an actual gate. [M:1418–1490; T/state.py:125]

The real defect is **lack of structured outcomes and guarded transitions**. “Refused,” “approved,” and “insufficient evidence” all complete the decision identically.

## C. Is Gochara absorption complete and safe?

### C1. Remaining work and coverage

The snapshot read at **2026-10-06 12:22:45 UTC** reported 75/102 done, with these 27 incomplete items. This is tracker evidence, not a fresh database verification. [`/Users/Dev/pravaha/run/snapshot.json:1`]

| Group | Incomplete items |
|---|---|
| Decisions | N-FLIP, N-T2, N-G9 |
| 4.1 baseline | A2.5, A2.6, B4.4 |
| Builder and tests | A5.2, A5.3, A5.4, A5.5, A5.5h, A5.5i |
| Operational prerequisites | A5.5j, A5.5k, A5.5l, A5.5m |
| Full build and qualification | A5.6, A5.7, B5.4 |
| Flip/retirement/Tier 2 | A6.1, A6.2, A6.3, B6.1 |
| L5 and closure | B6.2, B6.3, J2, J3 |

The remote search returned **37 open `pravaha/*` PRs**, rather than the packet’s 35:

- Measuring/final rules: **3194, 3185, 3188, 3187, 3191**.
- Snapshot/serving/census/slice: **3193, 3165, 3192, 3141, 3140, 3145, 3144**.
- Operational and C-items: **3119, 3116, 3114, 3111, 3108, 3103, 3099, 3091, 3089, 3085, 3083, 3082, 3018, 2989, 2988**.
- Verification/seal/baseline/doctrine: **2976, 2975, 2953, 2952, 2949, 2923, 2914, 2907, 2903, 2817**.

These are an inventory, **not a recommendation to merge all 37**. For example, [PR 2952](https://github.com/Marsys-Technologies/Madhav/pull/2952) explicitly describes an integration exhibit that must not merge, and [PR 3193](https://github.com/Marsys-Technologies/Madhav/pull/3193) supersedes 3165.

The J lane does not explicitly deliver:

- the 4.1 geometric baseline and comparison;
- A5.5k’s upstream Suvarṇa release;
- A5.5j/m’s grants, principal/job provisioning and second protected window;
- full A5.7 engineering evidence and B5.4 comparative evaluation;
- the final-rules candidate between measuring and sealed builds;
- authority migration, rollback and legacy-reader cutover;
- A6.1 soak and A6.2 retirement;
- the original Tier-2 scope, including Jaimini, transit-to-transit and other deferred methods;
- B6.2’s L5 prediction/outcome hand-off. [PM:561–592,773–875,1268–1280,1369–1440; FINAL:228–236,258,282]

J-1 must become **triage and ordered disposition**, not “land everything before J-2.” [M:973–1024]

There is substantial potential file overlap. Examples from remote PR file inventories:

- [3194](https://github.com/Marsys-Technologies/Madhav/pull/3194) and [3193](https://github.com/Marsys-Technologies/Madhav/pull/3193): `ka_gochara_v5.py`, kernel manifests, generated writer digests, CI.
- [2953](https://github.com/Marsys-Technologies/Madhav/pull/2953): mūrti/vedha writers and shared generated inventories.
- [3188](https://github.com/Marsys-Technologies/Madhav/pull/3188): evaluation/registry/kernel modules and generated inventories.
- [3082](https://github.com/Marsys-Technologies/Madhav/pull/3082): chart context, substrate and window sweep.

CH’s broad promise that K “consumes” Gochara does not mechanically reserve these files. Use an explicit shared-file ownership map and land inherited implementation changes before K modifies their adapters. [CH:80; M:919–932]

### C2. G6 preconditions

Seal validity, independently verified grains, live reader, test-slice refusal, previous-head retention and lease are appropriate. **The evaluation alternative is not.** [OS:39]

The protocol requires all co-primary endpoints, including:

- coverage ≥32/47;
- timing median ≤45 days;
- rank validity floor of 17 eligible events and required rank result;
- adverse/gain false-positive criteria;
- verifiable computation coverage;
- A5.7 engineering gates. [EVAL:168–222]

`rank-unproven`, `VOID`, `UNVERIFIABLE`, and generic `insufficient_evidence` cannot be converted into flip permission.

A surrogate can verify objective gates without a human if there are pinned machine-readable results and independent readbacks. Replace human attestations with:

- evaluation receipt bound to registry, extract, implementation and protocol hashes;
- exact generation/manifest/seal receipt;
- deployed image and migration receipt;
- end-to-end reader probes, including out-of-range, test-slice and rollback cases;
- lease and exclusive-operation receipt;
- required grants/jobs/capabilities verified through existing identities.

The surrogate cannot manufacture an unavailable credential, third-party entitlement, consenting dataset, or upstream completed build. Those must be satisfied before a promise of unattended completion is made. [OS:50; SMALL:63–71; FINAL:256–258]

### C3. Steward hand-over

Writing A/B events from a KY lane can pass item ownership checks, but it is **not a complete hand-over**. Original preflight rejects an unregistered KY worktree/branch, and the old runner configuration still belongs to the original A/B/C layout. [T/events.py:108–116; T/cli.py:173–181; T/runner.py:26–38]

B-5 must preserve:

- `EVENTS.jsonl`, current model and decision history;
- unacknowledged messages and existing item owners;
- runner HOLD/STOP semantics and quota state;
- dirty worktrees and unmerged branches;
- running external jobs and their run IDs.

A stale `RUNNER_STOP_*` file is not sufficient: the runner compares its timestamp to process start. Quiescence must be verified, and relaunch paths disabled for the absorbed writers. [`T/runner.py:175–184`]

The observed run directory contained quota/configuration state; absence of a HOLD/STOP file is not proof that no writer is active. The corrected hand-over must positively establish one writer per inherited item.

## D. Throughput, CI/CD and isolation

### D1. Landing rate and pacing

Using the supplied 9–13-minute duration, a strictly serial one-PR validation/merge cycle gives a theoretical **4.6–6.7 PRs/hour**. A practical planning allowance is **3–5/hour** after rebases, failures, dependency ordering and deploy verification.

That is a planning estimate: a five-entry queue is a capacity limit, not proof that all validation is serial or that five PRs land per run. At 3–5/hour, 35 inherited PRs alone require roughly **7–12 hours of landing capacity**, before K work and failures.

The verifier is likely the earlier bottleneck. One V repeats local checks and all item oracles and spends 30–60 minutes on packet reviews. Six producers can outpace it even when the merge queue is healthy. [V:11–14; CH:263–269]

Recommended pacing:

- Queue only independently verified, dependency-ready, deploy-compatible heads.
- Keep no more than **two verified PRs waiting per verifier slot**.
- Reserve queue capacity for the next J/critical-path dependency.
- Stop new implementation claims when review backlog exceeds that bound; use workers for permitted fixes and evidence completion.
- Reserve shared migration numbers and generated-file ownership centrally.
- Bind lease acquisition to the actual deploy window, not just build readiness.

An integration branch could help **coherent batches of tightly coupled K changes**, reducing deploy churn. It is not a one-line change: both CI and TAP branch admission, required-check equivalence, batch acceptance, and final-main validation need treatment. `ci.yml` and `tap-ci.yml` have different PR allowlists. [CI:18–62; TAP:106–129]

Direct-to-main is reasonable for independently compatible slices. It is unsafe as a blanket rule for partially converted writers/readers. The author is right to reject an **unvalidated** integration branch, but wrong to treat direct-to-main as inherently sufficient. [CH:203–211]

### D2. Precheck

No, it is not a faithful proxy, and there is no evidence it finishes under ten minutes on this laptop—especially with multiple lanes running it concurrently.

It **over-runs or falsely rejects**:

- full TypeScript checking rather than CI’s src-only error treatment;
- platform-mcp checking beyond the named six checks;
- drift/schema exit 3 even when within CI’s accepted ceilings;
- repeated full governance pytest execution for each item and again in V. [PRECHECK:16–37; CI:137–139,2143–2185]

It **misses or inadequately reproduces**:

- CI’s database provisioning and unit-test environment;
- explicit governance test shard selection and environment scrubbing;
- referential, schema-pin, DAG-edge and derivation checks;
- writer provenance inventory;
- sidecar suites outside `tests/`;
- package-specific tests when filenames do not match a basename;
- test-only and script-only changes;
- migration application: it only prints an instruction;
- migrations in `platform/migrations`;
- the complete frozen-file and declaration boundary. [PRECHECK:38–51; CI:162–270,2029–2036,2195–2246,2316–2364]

Governance tests should not inherit a production DSN. CI deliberately sets `DATABASE_URL` and `PGHOST` empty. [CI:2029–2031]

Use a fast local precheck plus explicit item tests; let the actual required CI checks remain the merge gate. Do not label a reduced script “equivalent.”

### D3. Deploy safety

Automatic deployment follows successful CI on main; merge completion alone does not establish deployed image or migration completion. [DEPLOY:3–24,95; CH:210]

Items needing explicit compatibility staging include:

- **K0a-1/3/4:** candidate/publication tables, generation resolution and initial read models;
- **K1/K2/K3:** reshaped clocks, graph/resolver and obstruction storage;
- **K4-2:** removal of existing Saṅgam modes and fields;
- **K5-1:** replacement forecaster semantics;
- **K6:** read models and the L5 registrar/reference-protection transition;
- **K7:** registry/alias/bridge and served-output changes;
- **K8-REG:** registry dependencies/counts/digests currently deferred until later. [M:238–319,337–509,546–565,652–670,728–833,398–456,919–932]

Candidate/published separation is the right intended foundation. But additive DDL alone does not protect live readers from changed writer semantics, deleted code paths, changed registry resolution, or absent replacement rows.

**K4-2 is not demonstrated deploy-safe as sequenced:** it explicitly deletes old modes before the final layer rebuild, without an item requiring old-head compatibility. Similar proof is missing for K5/K6/K7 cutovers. [M:546–565,652–670,742–814]

Writer-digest regeneration cannot wait for K8-REG when CI checks provenance on earlier writer PRs. [CI:2316; M:919–932]

Protected migrations have an additional stop: the routine migration runner deliberately refuses them outside the protected window. A blanket merge queue sweep can therefore interrupt normal deployments. [MIGRATE:128–163]

### D4. Cross-campaign effects

Yes, despite separate paths:

- Worktrees share Git refs, configuration, stash and administrative metadata.
- `git -C "$KY_REPO_MAIN" fetch` mutates shared repository metadata.
- Same-account agents can access every supplied checkout.
- “PRs you author” is not campaign isolation when all lanes use the same GitHub account.
- Broad Pravāha sweeping touches held drafts before their inherited conditions.
- Coordination-branch updates contend with other campaigns.
- Fixed Docker name `ky-pg` can reuse/remove an unrelated container with that name.
- Installer labels/ports are distinct, but do not protect filesystem or credential access. [FLEET:61–62,173; CH:182; S:17; LOCAL:16–23,51; INSTALL:9,45]

Do not touch Nirmāṇa’s HOLD, Suvarṇa’s held branches, or Pūrṇa’s brief. The current intent says that correctly; enforcement is missing. [CH:76,284]

## E. Governance minimum

### E1. Are seven rules sufficient?

They are a useful summary, not a sufficient executable policy.

Necessary retained obligations include:

- frozen WriterBase transaction/throughput ownership;
- L1 authority direction and no restated values;
- additive, unapplied-only migration edits;
- registry `count_sql`, dependency and integrity truth;
- density, narration and earned-signal declarations;
- generated writer digests and capability census;
- canonical artifact fingerprints and complete touched-file accounting;
- migration-number collision checks;
- coordination and cross-tool decision registration. [CLAUDE.md:265–308,344; CI:2316,2474–2615; HYGIENE:174–190; DRIFT:299–353]

A docs-only shortcut is not available merely because a file sits under `00_ARCHITECTURE`: control/autonomy paths are excluded, and shell/JSON files are not eligible documentation. Queue/push events do not receive the PR-only docs shortcut. [CLASSIFY:30–66,125–131]

The fleet should automate the retained obligations once per coherent change. It should not ask a human to perform them.

### E2. One campaign handshake and exact B-4 requirements

Under the base protocol, a fresh session normally opens and closes with its own records. A single campaign record is defensible as an **explicit native-directed exception**, provided it is recorded once in the shared governance state and child execution remains auditable. It does not become valid merely because the charter says it “discharges” the requirement. [CLAUDE.md:204–212; GIP:1054–1115; CH:240]

`schema_validator.py --handshake` parses the **entire input as YAML**. B-4 must contain a top-level `session_open:` mapping, not a Markdown document containing a fenced block. [SCHEMA:475–486]

Required fields:

```yaml
session_open:
  session_id: ...
  cowork_thread_name: ...
  agent_name: ...
  agent_version: ...
  tool: Codex
  tool_profile: ... # an actually selected supported profile
  worktree_path: ...
  step_number_or_layer: ...
  coordination:
    lease_id: ...
    lease_status_verified: true
  cross_tool_state_read:
    cross_cutting_decision_register: true
  predecessor_session: ...
  mandatory_reading_confirmation: ...
  canonical_artifact_fingerprint_check: ...
  declared_scope:
    may_touch: [...]
    must_not_touch: [...]
  mirror_pair_freshness_check: ...
  native_directive_obligations: ...
  red_team_due: false
```

All ellipses must be replaced with truthful values. The currently accepted Codex profile names are `madhav-safe` and `madhav-parity`; do not record one while launching a different configuration. A false fingerprint match is rejected. `must_not_touch` must be nonempty. [SCHEMA:492–570]

The validator only checks presence of `red_team_due`; the prompt’s descriptive string is not rejected by that particular function. Nevertheless, use the template’s boolean and record the exemption separately. [S:12; SCHEMA:492–526]

Brace globs such as `{kala_core,ka_*,gochara_*}` are not expanded by `fnmatch`. Enumerate them separately. Include tests, both migration directories, permitted L5 code, generated inventories, close metadata and the coordination decision. A global `must_not_touch: "**"` would override every allowed path and must not be used. [S:12; SCHEMA:715–750]

### E3. Delegated powers

The native plainly delegated routine domain, architecture, sequencing, review, protected delivery and acceptance decisions needed for this campaign. Delegating D-FLIP/D-T2/D-G9/D-CLOUD **subject to unchanged evidence gates** is consistent with that directive. The accepted Pūrṇa form similarly delegates operational decisions without allowing missing proof to become acceptance. [CH:44–52; OS:21,34–44; Pūrṇa charter:18–45]

The questionable grants are not “too much autonomy”; they are **relaxations disguised as judgment**:

- permitting insufficient evaluation evidence for flip;
- treating retained test rows as an equivalent teardown path;
- allowing completion to outrun independent verification. [OS:39–40; CH:145]

Conversely, blanket P5 and “only the native may amend this charter” recreate a human gate for ordinary execution defects. Authorise the surrogate to repair execution mechanics within the fixed mission, evidence gates, scope and budget. Keep scope expansion, frozen-contract relaxation and unavailable credentials outside that power. [OS:50–54,94–96]

The two named L0 demands also need a precise exception to the blanket prohibition on protected-corpus writes, routed through the existing ingestion/migration mechanism. Otherwise L0-K is authorised and prohibited simultaneously. [OS:60; CH:69,76; M:954–970]

## F. The plan model

### F1. Grain

The number is currently **81**, not 80. Count is less important than whether each item represents one independently claimable, resumable and verifiable result.

Too large for one 90-minute execution unit:

- J-1’s 37-PR disposition;
- J-2’s two runs and two teardowns;
- J-3/J-4 if the agent waits for multi-hour jobs;
- J-7’s multiple Tier-2 methods;
- K1-1, K2-1, K4-2 and K5-1 as broad algorithm/schema/facade/test rewrites;
- K7-1’s seven composites, aliases, bridge and floor tests;
- K9-1/3/4 end-to-end rehearsal, drills and production rebuild;
- full packet review plus nested reviewer startup and report processing. [M:337–378,398–416,546–565,652–670,973–1109,1198–1210,1244–1305; V:11–14]

Split into sub-items or PR-sized slices **before** claim. `steps[]` are progress annotations, not a sound substitute while the first merged branch marks the parent done. [K:13–14; T/state.py:82–103]

Potentially too small: the five pre-ruled decisions as separate expensive model cycles, and isolated documentation-only certification mappings. Keep their evidence separately addressable, but batch execution where ownership and acceptance are coherent. [M:784–792,835–932,1378–1415]

### F2. Value checkpoint

It does not currently establish that the evaluated G1 model equals the intended G1 implementation. VC depends on K0a-2’s clock repair; full breakpoints, pinned as-of/axis, suppression inputs and forecaster null arrive later in K5-1. [M:259–277,596–670]

Ruling 10 requires the three arms, ordinary-period controls, frozen distinction rubric, independent scoring, censored/ambiguous handling, and real consenting outcome evidence; its per-stratum censoring ceiling cannot be replaced by a generic local fixture run. [RULING10:61]

OS’s acceptance of `insufficient_evidence` for **the value checkpoint** may be legitimate; that does not make it legitimate for **Gochara flip**. [OS:36,39]

There is no `VC-3` item despite the charter’s label. D-VC appears to occupy the adjudication role, but that must be named consistently. [CH:65; M:596–650]

**NR-KALA-R12 comparison remains unverified because the ruling file is absent.**

### F3. Missing deliverables

At minimum, explicit producers/acceptance items are needed for:

- specification delivery and hash verification;
- atomic claims, guarded completion, structured decisions and shutdown finalisation;
- completion of the K0a verification-dispatch **stub**;
- full inherited Pravāha disposition and final-rules-candidate path;
- authority CHECK replacement, legacy reader cutover and rollback;
- evaluation/A5.7 qualification;
- independent verifier/sealer operational capability;
- upstream release and protected-window prerequisites;
- backup/restore evidence production, not just checking that a record exists;
- all-seven-view/K7 acceptance and certification coverage;
- `kala_now_get`’s negative-space sentinel and arrival-line acceptance;
- a close join over every mandatory result;
- post-shutdown proof that fleet processes and lane worktrees are gone. [CH:34–38,76; M:279–298,398–456,973–1375]

The absent algorithm plan prevents a complete asset-by-asset omission list. An explicit card→item→oracle→migration→deployment→live-detector matrix is required before launch.

## G. Kickoff

### G1. Execution order and first failures

On a fresh operator setup, the earliest conditional failure is `cp` before creating `~/.config/kalayantra`. [KICK:7–9]

After that:

1. The prompt can start from any directory but uses relative commands before an explicit `cd`. [KICK:4,16,26]
2. Required specification reads fail because the files are absent. [CH:12–16; K:12]
3. Preflight may install the campaign venv/dependencies, but does not establish all lane environments or production completion capability. [PREFLIGHT:16–19,34–43]
4. Installer starts the original sibling package. S/N/V/K messaging is not supported. [INSTALL:12–17; T/cli.py:279–280]
5. B-1 precheck can reject existing accepted governance residuals. The permitted write-set also omits files needed for some bootstrap/governance corrections. [PRECHECK:29–30; CI:2143–2185; KICK:37]
6. `ky` is used without adding its bin directory to PATH. `KY_STREAM=S` applies only to the command it prefixes, not later commands. [KICK:28]
7. PR creation is not idempotent. A repeat must inspect an existing head PR before creating another. No open bootstrap PR was returned by the remote search at review time; this is a repeat-run defect, not a claim that one already existed.
8. Worktrees are detached and fail branch preflight. Local database instructions reference obsolete failure/skip files and do not establish a complete fixture. [KICK:29; T/cli.py:179–181; LOCAL:39–44]
9. B-4 happens after state-changing bootstrap work and requires fields/lease/profile evidence the prompt does not establish. [KICK:31; SCHEMA:492–570]
10. Launch does not await B-1 merge/deployment, does not explicitly switch tracker package, and allows workers before B-3b/B-4. [KICK:34; M:238–256]
11. Even after those repairs, duplicate claims and premature completion remain.

The corrected kickoff below replaces this sequence.

### G2. Successful kickoff and next-morning check

A successful kickoff should show:

- exact reviewed package/model/specification hashes;
- one supervisor per enabled lane, individual worker identities and fresh heartbeats;
- valid tracker health with no model error;
- one exclusive claim per running item;
- lane dependencies and local fixtures verified;
- B-1 merged and the copied package selected explicitly;
- no database secrets in agent environments;
- inherited Pravāha writers quiesced and ownership transferred;
- the first real work item progressing through claim → review → accepted head → merge;
- a working HOLD/STOP test.

The current `status` cannot prove this: it reports log timestamps and aggregate tracker state. [FLEET:164–174; T/state.py:143–174]

The single morning check should be a machine-generated **progress receipt**, exposed by a command such as:

```text
ky audit --since kickoff --require-live-workers --require-earned-progress
```

This command **does not exist today**. B-1 should implement it. It should fail on duplicate claims, expired workers, rejected-but-done items, missing dependencies, unbound production operations, or zero earned progress during a nonblocked interval. A heartbeat alone must never count as productivity.

# 4. Corrected artefacts

These are replacement **design and script blocks**, not applied changes. The control-plane and isolation work explicitly assigned below must be implemented and verified before launch; the patches are not a claim that those missing capabilities already exist.

## 4.1 Replace the common item/merge protocol

Replace `CH §4.2`, the automatic-queue instructions in `CH §5–§6`, and the corresponding K/S instructions with:

```markdown
### Item ownership, review and completion

A stream routes work; a worker owns a claim. Every worker has a stable worker_id
and every claim has an opaque claim_id, expiry and renewal record.

The tracker atomically claims a READY item only when all required dependencies
are complete. A stale snapshot cannot authorise a claim. A second worker cannot
claim or mutate an active claim. Recovery requires an expired claim and a
recorded hand-over preserving its branch, head and unfinished work.

Workers push a PR and request review; workers do not enable auto-merge.
SŪTRADHĀRA alone queues an assigned campaign PR after:
1. PARĪKṢAKA accepted its exact current head;
2. required CI checks passed;
3. all dependency and deployment-compatibility predicates passed; and
4. any required production coordination lease covers the deployment.

A later push invalidates the accepted verdict. REJECTED cannot become complete
through a merge detector, a note, a long review file or a decision description.

An item is complete only when its required dependencies and steps are complete,
its exact reviewed head has landed, and its required runtime/readback evidence
is accepted. Detector observations are evidence inputs, not unconditional state
overrides.

A large item is split into independently claimable child items before execution.
Each child has its own branch, PR and acceptance receipt. The parent is a join.
A first child merge never completes the parent.

Decisions have a structured outcome: approved, refused, deferred, or
insufficient_evidence. Dependants name the outcomes they require.
Optional work closes as not_applicable only under its explicit decision rule;
it is never reported as implemented.

A rejected packet blocks its outgoing dependency edges until every blocking
finding is fixed and re-reviewed or explicitly dispositioned under an unchanged
acceptance contract.

PR ownership is the claim's registered PR number and head branch, never merely
the authenticated GitHub author.
```

This addresses KY-02/03/09/22 and removes the dangerous conflict between “verifier required” and “detector closes itself.”

## 4.2 Replace SŪTRADHĀRA’s bootstrap section

```markdown
## Bootstrap — finish before enabling implementation workers

B-1 is a control-plane acceptance work package, not a stream-name-only patch.

1. Restore the reviewed Kāla specifications to this campaign, verify the charter's
   pinned hashes, and record the exact versions of the native rulings and
   reconciliation. Do not infer missing specification text.

2. Copy pravaha_tracker without changing the running Pravāha installation.
   Preserve compatibility with its existing model and event history.

3. Implement and verify:
   - model-derived message recipients and actors in CLI, writer and event reader;
   - authorised verifier-to-owner messaging, linked visibly to the referenced item;
   - configurable HOLD path;
   - atomic READY-to-claimed transition with worker_id, claim_id, lease and recovery;
   - dependency and claim validation on every item mutation;
   - structured decision outcomes and guarded conditional dependencies;
   - exact-head independent verdicts;
   - completion as the conjunction of dependencies, steps, accepted verdict and
     detector/runtime evidence;
   - packet blocking-findings gates;
   - per-worker heartbeat and earned-progress audit;
   - explicit reopen/unblock operations;
   - a finalizer that can complete C-3 after agents stop.

4. Acceptance must demonstrate, using temporary local fixtures:
   two simultaneous claims produce exactly one winner; stale state cannot claim;
   a rejected or changed head cannot queue or complete; a refused decision cannot
   enable approved-only work; a rejecting review file cannot unlock a packet;
   a stopped worker's claim recovers without losing its branch; Pravāha's original
   behaviour and historical messages remain readable.

5. Complete B-3b before worker release. Establish the reviewed local database
   recipe and lane dependencies. Record the exact CI job/script revisions and
   which checks are local versus CI-only.

6. Create and validate the campaign SESSION_OPEN before other campaign mutations.
   Record the native-authorised campaign-level handshake exception in the shared
   decision register. Use the actual execution profile and live lease evidence.

7. Open or update the existing campaign/kalayantra PR. Never create a duplicate.
   Obtain independent acceptance, pass CI, queue it, and wait for its merge.
   Fetch the merged head and explicitly install the copied tracker package:
   install_tracker.sh --gov "$KY_ROOT/wt/campaign/platform/scripts/governance"

8. Verify the running tracker reports the expected code/model hashes and passes
   the control-plane acceptance audit. Only then enable K workers.
```

Replace S’s standing duties concerning paths, PRs and close with:

```markdown
Use "$KY_ROOT/run" and "$KY_ROOT/logs" for every runtime path.
Committed digests and review packets live under
00_ARCHITECTURE/briefs/kalayantra/ in the owning worktree.

Queue only PR numbers registered to an active campaign claim and accepted at
their current head. Respect inherited hold conditions and deployment leases.
Do not sweep all PRs by GitHub author or all pravaha/* drafts indiscriminately.

For model changes, use one designated model writer. Publish a validated model
revision atomically after its review; do not fast-forward the campaign branch
arbitrarily onto unrelated ledger branches.

For a blocked item, record a ruling and invoke the tracker's explicit
owner-authorised unblock/reopen transition. A note does not change state.

C-3 is executed by the external finalizer from "$KY_ROOT", after the close PR
has merged and V has accepted all pre-stop evidence. The finalizer stops the
fleet, verifies no campaign descendants remain, removes only clean campaign
lane worktrees, preserves branches and evidence, freezes absorbed event writers,
and records the post-stop receipt. S must not remove its own active worktree.
```

Addresses KY-05/09/14/18–23/26.

## 4.3 Replace the worker’s cycle

```markdown
## Each cycle

1. Check HOLD/STOP. Read your durable claim/resume record. If a claim exists,
   resume that exact branch and unfinished step; do not create a fresh branch.

2. Fetch main. Inspect only your registered PRs. Never operate on a PR merely
   because the shared GitHub account authored it. Merge origin/main into an
   existing published branch when needed; do not rebase and force-push it.
   If replacement is necessary, preserve the old branch and create a new
   reviewed replacement PR with an explicit supersession record.

3. Ask the tracker to atomically claim one dependency-ready item for your
   worker_id. If another worker wins, request another item. Never infer ownership
   from a shared stream-K RUNNING status.

4. Read the generated item brief: pinned specification sections, cross-cutting
   contracts, file ownership, exact tests, migration recipe and deployment
   compatibility requirements. If any required source is absent, block the item.

5. Work on one resumable slice. Use your existing local database or explicitly
   request a reset; obtaining a database URL must never drop the database.
   Run the fast precheck and the item's explicit tests and mutation oracles.
   Regenerate required writer/capability inventories in the same PR.

6. Push an explicit-path commit, create or update the registered PR, and request
   independent review at its exact head. Do not enable auto-merge.

7. Renew the claim while working. Before exit, persist branch, head, changed
   files, tests, unfinished step and next action. Completion is performed only
   through the guarded tracker transition.

J work uses an inherited-item mapping and an explicit hand-over claim.
Triage does not mean merge: obey the small-test, measuring-build, protected-window
and final-rules ordering. Preserve superseded PR content before closing it.
```

Addresses KY-01/02/03/05/15/18/19/22/23/24.

## 4.4 Replace ADHIKĀRIN’s production and unblock instructions

```markdown
For a blocked or parked item, record a structured ruling with its evidence and
invoke the explicit authorised transition. A note or message alone never unblocks.

For a production operation, create a durable operation request containing:
operation_id, item_id, chart_id, generation, reviewed_commit, image_digest,
manifest/input hashes, lease_id, expiry, idempotency key, permitted operation,
and the independent pre-operation acceptance receipt.

Submit this request to the fixed-operation executor. No database URL, password,
credential-file content or arbitrary shell command may enter the request.

Dispatch, observation, verification, sealing, publication and rollback are
separate resumable states. Re-entering a cycle reads the existing operation_id;
it never arms or dispatches another operation merely because the item remains READY.

Long jobs run outside the Codex cycle. A cycle may submit or inspect one operation
and exit; it does not wait for the job to finish.

After independent acceptance, the owner may invoke the guarded completion
transition for its manual item. ADHIKĀRIN may not verify its own execution.

Missing execution, teardown, verifier, sealer or migration capability blocks the
dependent operation before the first production write. There is no retention
substitute for a required teardown and no evaluation-evidence substitute for PASS.
```

Addresses KY-04/06/07/11/23.

## 4.5 Replace PARĪKṢAKA’s review protocol

```markdown
Create "$KY_ROOT/run/verdicts" and "$KY_ROOT/run/reviews" before writing evidence.

For an item, review the exact registered PR head. Produce a structured verdict
bound to item_id, claim_id, head_sha, specification hashes, tests and mutations.
A changed head invalidates the verdict. Separate pre-merge compatibility review
from post-deploy migration/runtime acceptance.

For a packet, obtain the output path directly from the plan model; do not derive
it from a differently capitalised packet name. Store the input packet at an
absolute path and pass that same path to the nested reviewer.

A packet is accepted only after its structured verdict is ACCEPTED and every
blocking finding is resolved or validly dispositioned. File existence and byte
length are not acceptance.

File new findings through report with their item reference; the designated model
writer creates the required items and dependency edges before any successor starts.

Production prechecks contain only predicates that can be true before dispatch.
Postconditions are checked after the recorded operation completes. Use the exact
run, generation, manifest and image identities; process exit zero is not proof.

Do not block or complete another stream's item through an ordinary owner command.
Submit the independent verdict; the guarded control plane performs the authorised
state transition.
```

Addresses KY-03/08/11/21/23.

## 4.6 Fleet script corrections

The following replacements address the shell defects. They must accompany the control-plane and isolation work above.

**After directory setup, validate names/numbers and normalise the script path:**

```bash
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
PY=/opt/homebrew/bin/python3

valid_lane() {
  case "$1" in
    sutradhara|adhikarin|pariksaka|k1|k2|k3|k4|k5|k6) return 0 ;;
    *) echo "invalid lane" >&2; return 2 ;;
  esac
}

workers_wanted() {
  "$PY" -c '
import pathlib,sys
p=pathlib.Path(sys.argv[1])
try:
    raw=p.read_text().strip() if p.exists() else sys.argv[2]
    n=int(raw,10)
except (OSError,ValueError):
    n=4
print(max(1,min(6,n)))
' "$RUN/KY_WORKERS" "${KY_WORKERS:-4}"
}
```

**Replace the credential injection block.** Production credentials belong to the separate executor, not this process tree:

```bash
for secret_name in KY_BUILDER_DATABASE_URL KY_OWNER_DATABASE_URL DATABASE_URL; do
  if [ -n "${!secret_name:-}" ]; then
    echo "Refusing agent launch: production credential variable is set." >&2
    return 78
  fi
done

local -a envs=(
  "HOME=$HOME"
  "PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
  "KY_STREAM=$stream"
  "KY_LANE=$lane"
  "KY_ROOT=$KY_ROOT"
  "KY_PY=$KY_ROOT/venv/bin/python"
  "SE_EPHE_PATH=$SE_EPHE_PATH"
  "SWE_EPHE_PATH=$SE_EPHE_PATH"
)
```

`HOME` here must be the **isolated execution account’s home**, not the operator’s home. This patch eliminates inherited environment leakage; OS isolation eliminates file-based access. Do not claim the former supplies the latter.

**Replace the background Codex invocation/watchdog/wait block with a process-group controller:**

```bash
local cycle_log="$LOGD/$lane.$n.log"
local last_file="$LOGD/$lane.$n.last.md"

env -i "${envs[@]}" "$PY" -c '
import os,signal,subprocess,sys
limit=int(sys.argv[1])
p=subprocess.Popen(sys.argv[2:], start_new_session=True)

def terminate(*_):
    try: os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    try: p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try: os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        p.wait()

def interrupted(signum, frame):
    terminate()
    raise SystemExit(128+signum)

signal.signal(signal.SIGTERM, interrupted)
signal.signal(signal.SIGINT, interrupted)
try:
    result=p.wait(timeout=limit)
except subprocess.TimeoutExpired:
    terminate()
    result=124
finally:
    # Reap tool descendants that outlive the main Codex process.
    try: os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError: pass
    try: os.killpg(p.pid, signal.SIGKILL)
    except ProcessLookupError: pass
raise SystemExit(result)
' "$MAX_CYCLE_SECS" \
  codex exec -C "$wt" --dangerously-bypass-approvals-and-sandbox \
  -m "$model" -c "model_reasoning_effort=\"$effort\"" \
  -o "$last_file" - < "$prompt_file" > "$cycle_log" 2>&1 &
local pid=$!

trap 'kill -TERM "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null; exit 143' TERM INT
wait "$pid"; rc=$?
trap - TERM INT

# Examine this cycle only. Do not copy model output into supervisor.log.
if grep -qiE '(^|[^0-9])429([^0-9]|$)|usage limit|rate limit|quota (will reset|exceeded)|too many requests' "$cycle_log"; then
  mark_quota_backoff "$lane"
fi
log "$lane" "cycle $n end rc=$rc"
```

**Replace cycle numbering/cap checks with an atomic start reservation**, called before producing a prompt:

```bash
reserve_cycle() {
  "$PY" -c '
import datetime,fcntl,json,pathlib,sys
root=pathlib.Path(sys.argv[1]); lane=sys.argv[2]; cap=int(sys.argv[3])
root.mkdir(parents=True,exist_ok=True)
with (root/"CYCLE_STARTS.lock").open("a+") as lock:
    fcntl.flock(lock,fcntl.LOCK_EX)
    p=root/"CYCLE_STARTS.jsonl"
    rows=[json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    if sum(r["ts"][:10]==now[:10] for r in rows) >= cap:
        raise SystemExit(75)
    n=1+sum(r["lane"]==lane for r in rows)
    with p.open("a") as out:
        out.write(json.dumps({"ts":now,"lane":lane,"cycle":n})+"\n")
        out.flush()
        import os; os.fsync(out.fileno())
    print(n)
' "$RUN" "$1" "$KY_MAX_CYCLES_PER_DAY"
}
```

Use:

```bash
n="$(reserve_cycle "$lane")" || return "$?"
```

Apply this to **all lanes**. Remove the K-only cap at line 157. Count reserved starts in budget/status; keep completion records separately.

**Add a process lock around every lane invocation:**

```bash
locked_lane() {
  valid_lane "$1" || return "$?"
  "$PY" -c '
import fcntl,os,subprocess,sys
lock=open(sys.argv[1],"a+")
try:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit(0)
raise SystemExit(subprocess.call(
    ["bash",sys.argv[2],"lane-locked",sys.argv[3]],
    pass_fds=(lock.fileno(),)))
' "$RUN/$1.lock" "$SELF" "$1"
}
```

Replace `up`, `down`, and command routing:

```bash
up() {
  [ ! -f "$HOLD" ] || {
    echo "HOLD exists; use resume to release it."
    return 1
  }
  for lane in "${ALL_LANES[@]}"; do
    rm -f "$RUN/STOP_$lane"
    nohup bash "$SELF" lane "$lane" \
      >> "$LOGD/supervisor.$lane.out" 2>&1 &
  done
  status
}

down() {
  touch "$HOLD"
  for lane in "${ALL_LANES[@]}"; do
    touch "$RUN/STOP_$lane"
  done
  echo "Stop requested. Active cycles retain their watchdog and finish within the cap."
}

case "${1:-status}" in
  up) up ;;
  down) down ;;
  resume)
    rm -f "$HOLD"
    up
    ;;
  status) status ;;
  lane) locked_lane "${2:?lane required}" ;;
  lane-locked)
    valid_lane "${2:?lane required}" || exit "$?"
    supervise_lane "$2"
    ;;
  *) echo "usage: $0 up|down|resume|status|lane <name>"; exit 2 ;;
esac
```

Within `supervise_lane`, test STOP **before** HOLD and cap sleeps at 60 seconds. The external finalizer must wait for lane locks to release before removing worktrees. These changes fix duplicate active lane loops and preserve watchdogs during graceful shutdown; they do not replace the required isolated execution boundary.

Addresses KY-04/12/13/25. Backoff updates must additionally be serialised under a lock, retaining the maximum unexpired deadline; malformed state must fail closed.

## 4.7 Installer and preflight replacements

In `install_tracker.sh`, replace initial directory creation with:

```bash
umask 077
mkdir -p "$RUN" "$KY_ROOT/bin" "$RUN/reviews" "$RUN/verdicts" \
  "$HOME/Library/LaunchAgents"
```

Replace implicit package selection with explicit selection:

```bash
if [ "${1:-}" = "--gov" ]; then
  [ "$#" -eq 2 ] || { echo "usage: --gov <package-parent>"; exit 2; }
  GOV="$2"
  printf '%s\n' "$GOV" > "$RUN/TRACKER_GOV"
elif [ -s "$RUN/TRACKER_GOV" ]; then
  GOV="$(cat "$RUN/TRACKER_GOV")"
else
  echo "Select a reviewed tracker package explicitly with --gov."
  exit 1
fi
```

Add to both wrapper and launchd environment, after implementing the configurable HOLD option:

```text
PRAVAHA_HOLD=/Users/Dev/kalayantra/HOLD
```

Replace HTTP-200-only acceptance with:

```markdown
Installation succeeds only when the tracker reports:
- the expected campaign and plan-model hash;
- the explicitly selected package revision;
- no model validation error;
- a fresh engine tick;
- all required local acceptance checks passed.

Database detector unavailability is reported separately and cannot complete a
production-dependent item. Installing a server is not completing B-2 by itself.
```

Replace preflight’s credential “optional” policy with:

```markdown
There are two preflight modes.

bootstrap: may repair only campaign-local dependencies and establish the control
plane. It does not write PREFLIGHT_OK or authorise implementation workers.

launch: requires all specification files and hashes, copied tracker acceptance,
all lane worktrees and dependencies, reviewed local database fixtures, exclusive
claims, isolated agent environment, absorbed-runner hand-over, and the fixed
production executor capabilities needed by the mandatory campaign path.

Launch preflight writes a structured receipt bound to code/model/specification
hashes. A timestamp-only file is not a launch detector.
```

Addresses KY-05/11/14/21/26.

## 4.8 Local database corrections

The current runner-based revision is an improvement. Replace `mkdb()` with this fail-closed form; B-3b must supply the reviewed fixture recipe rather than inventing skip exceptions:

```bash
mkdb() {
  local lane="$1"
  case "$lane" in
    k1|k2|k3|k4|k5|k6|sutradhara|adhikarin|pariksaka) ;;
    *) echo "invalid lane"; return 2 ;;
  esac

  local lane_repo="$KY_ROOT/wt/$lane"
  local recipe="$lane_repo/00_ARCHITECTURE/briefs/kalayantra/fleet/rehearsal_db.sh"
  local db="ky_$lane"
  local url="postgresql://postgres:$PW@127.0.0.1:$PORT/$db"
  local logfile="$KY_ROOT/run/local_db_${lane}_runner.log"

  [ -f "$recipe" ] || {
    echo "B-3b incomplete: reviewed rehearsal database recipe is missing."
    return 1
  }

  # The recipe owns reset, extensions, roles, protected local migration ordering,
  # both migration directories, and schema/grant assertions.
  # It accepts only the fixed localhost database supplied here.
  local rc=0
  KY_REPO="$lane_repo" DATABASE_URL="$url" \
    bash "$recipe" "$lane" > "$logfile" 2>&1 || rc=$?

  if [ "$rc" -ne 0 ]; then
    echo "ky_$lane INCOMPLETE; see $logfile"
    return "$rc"
  fi

  echo "ky_$lane ready: reviewed recipe and assertions passed"
}
```

The new recipe is an explicit B-3b deliverable, not an existing file. Require production-major-version compatibility, serial cluster-role setup, both migration directories, and named schema/grant assertions. Do not use `local_db.skip` as a substitute for objects an oracle needs.

Keep `url` read-only. Rename reset behaviour to `reset` or require an explicit reset argument so ordinary worker setup does not destroy retained evidence. Validate an existing container’s image, label and port before reuse/removal. [LOCAL:21–23,29–51]

Addresses KY-15.

## 4.9 Precheck replacements

Replace its introductory promise with:

```bash
# Fast local precheck plus explicitly selected item tests.
# This is not equivalent to the six required GitHub checks.
# Required CI and independent exact-head acceptance remain mandatory before queueing.
```

Replace strict-zero drift/schema calls with CI-equivalent ceiling handling:

```bash
baseline_gate() {
  local name="$1" ceiling="$2" pattern="$3" output rc=0 count
  output="$(python3 "platform/scripts/governance/$name.py")" || rc=$?
  printf '%s\n' "$output"
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 3 ]; then
    fail "$name exit=$rc"
    return
  fi
  count="$(printf '%s\n' "$output" | sed -n "$pattern" | tail -1)"
  if [[ ! "$count" =~ ^[0-9]+$ ]] || [ "$count" -gt "$ceiling" ]; then
    fail "$name baseline exceeded or unreadable"
  else
    ok "$name within CI baseline"
  fi
}

baseline_gate drift_detector 79 's/^drift_detector: \([0-9]*\) findings.*/\1/p'
baseline_gate schema_validator 43 's/^schema_validator: \([0-9]*\) violations.*/\1/p'
```

Replace governance pytest invocation with a scrubbed environment:

```bash
(
  cd platform &&
  env -u KY_BUILDER_DATABASE_URL -u KY_OWNER_DATABASE_URL \
    DATABASE_URL='' PGHOST='' \
    "${KY_PY:-/Users/Dev/kalayantra/venv/bin/python}" \
    -m pytest -q scripts/governance
) && ok "governance pytest" || fail "governance pytest"
```

Replace basename-based sidecar discovery and migration echo with:

```markdown
Each code item supplies an explicit reviewed test manifest containing test paths,
database fixture requirements and mutation commands. The precheck executes those
paths; no "-k package-basename" inference is allowed.

A migration item requires a successful rehearsal receipt for its exact head and
migration set. Both platform/migrations and platform/supabase/migrations are
included. A printed reminder is not a successful migration check.

Writer changes regenerate and check provenance inventory in the same PR.
Generated capability/bridge changes run their corresponding freshness checks.

The full required GitHub checks remain mandatory. Report local checks and CI-only
checks separately; never print "six required checks reproduced" unless the
commands, environments and acceptance semantics are actually identical.
```

The test-manifest executor is a B-3b deliverable. This avoids claiming an unimplemented selector is already available. Addresses KY-16.

## 4.10 Correct G6/G7 and the J graph

Replace OS G6/G7 and KYD-7 with:

```markdown
G6 — D-FLIP:
Approve only for the exact generation and manifest independently verified and
sealed, with every applicable EVALUATION_PROTOCOL v2.3 co-primary endpoint and
A5.7 engineering gate passing. Rank-unproven, VOID, UNVERIFIABLE, fail and
insufficient_evidence do not authorise the flip.

Require the deployed serving path, replacement authority constraint migration,
test-slice refusal, scope/range behaviour, rollback rehearsal, previous-head
retention and live coordination lease. Readbacks must identify the deployed
image and migration set.

G7 — D-TEARDOWN:
The two small tests require the checklist's intervening and final teardown.
No first test is dispatched until the complete teardown capability is verified.
Missing teardown capability blocks that production sequence; retaining its rows
does not complete the sequence or permit a second dispatch.

KYD-7:
No retention alternative. Use the existing authorised teardown mechanism through
the fixed-operation executor, dry-run first, and independently verify the required
absence of rows/receipts before the next dispatch.
```

Replace J-1’s “land all” instruction with:

```markdown
J-1 inventories every inherited item, decision, PR, hold and active writer.
For each, record: keep/merge/supersede/salvage/not-applicable, exact evidence,
owner, dependencies and permitted landing phase. Triage completion does not
mean every PR has merged.

Landing phases:
1. Small-test prerequisites only.
2. Run 1, readback, teardown, absence proof.
3. Run 2, readback, teardown, absence proof.
4. Measuring builder/verifier prerequisites on the measuring rules.
5. Measuring dispatch, readback, golden capture, report and teardown.
6. Resolve final-build decisions and upstream release prerequisites.
7. Protected-window changes and independent readbacks.
8. Final-rule builder/verifier changes and equality/noninterference proof.
9. Final-rules candidate, density/residual decisions and cap qualification.
10. Final build, engineering/evaluation qualification, independent verification
    and sealing.
11. Serving migration, end-to-end reader/rollback acceptance and D-FLIP.
12. Flip, live readback, soak, retirement, admitted Tier-2/L5 work and original
    Pravāha closure.
```

For the database observations, replace the two SQL strings with:

```sql
-- J-5: seal observation; acceptance also binds the expected manifest and job.
SELECT p.generation
FROM public.kala_gochara_publication AS p
WHERE p.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND p.generation = '5.0'
  AND public.ka_gochara_generation_is_sealed(p.chart_id, p.generation);
```

```sql
-- J-6: authority/publication observation; live serving receipt remains required.
SELECT p.generation
FROM public.kala_gochara_publication AS p
JOIN public.kala_gochara_authority AS a
  ON a.chart_id = p.chart_id
 AND a.authoritative_generation = p.generation
WHERE p.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND p.generation = '5.0'
  AND p.status = 'published'
  AND public.ka_gochara_generation_is_sealed(p.chart_id, p.generation);
```

Do not treat either SQL result alone as complete acceptance. Addresses KY-06/07/08/11/18.

## 4.11 Correct the model’s closure and checkpoint rules

Apply these exact design requirements before regenerating the JSON:

```markdown
- B-1, B-2, B-3, B-3b and B-4 all precede implementation release.
- V-K12 gates work that requires completed K1/K2 contracts.
- K3-2 receives independent review before final K3 acceptance.
- The full frozen G1 baseline precedes VC-1/VC-2.
- D-G2 approved enables K5-3; refused makes it explicitly not_applicable.
- K5-2 records implemented-and-proven or not_applicable-with-dense-path-retained.
- V-K5 covers every applicable K5 child.
- K8-REG depends on every required mapping, including serving/adapters.
- K9-1 requires completed K7 and all required mappings.
- J-3 does not contain d_g9_ruled as a completion step; D-G9 follows its readback.
- Long production operations are dispatch, observe and accept children.
- A mandatory-results join covers every charter-required item.
- C-1 depends on that join and complete absorbed Pravāha disposition.
- C-2 requires a merged close PR plus successful close validation.
- C-3 belongs to the external finalizer.
- The final five-line acceptance follows C-3's post-stop receipt.
```

This is deliberately not a speculative reconstruction of missing architecture §9. Reconcile it against that specification once restored. Addresses KY-09/17/23.

## 4.12 Replacement kickoff

```markdown
You are bootstrapping KĀLA-YANTRA. Work only in the campaign's authorised isolated
checkout. Do not launch implementation agents until bootstrap acceptance passes.

1. Set and enter the working root explicitly:
   export KY_ROOT=/Users/Dev/kalayantra
   cd "$KY_ROOT/wt/campaign"
   export PATH="$KY_ROOT/bin:$PATH"
   export KY_STREAM=S

2. Read the campaign and surrogate charters, this corrected execution protocol,
   and the pinned Kāla specifications. Verify their hashes. Missing or mismatched
   specifications block launch.

3. Establish the campaign SESSION_OPEN and native-authorised campaign-level
   governance exception with truthful profile, lease, fingerprint and scope data.
   Validate before state-changing campaign work.

4. Complete B-1 control-plane changes and their acceptance cases. Use the local
   copied package explicitly; do not modify the running Pravāha package.

5. Complete B-3/B-3b: isolated lane environments, reviewed local database fixtures,
   explicit test manifests, supervisor lifecycle tests, secret-free agent
   environments, production executor capabilities and per-worker identity.

6. Prepare the inherited Pravāha inventory and ordered disposition. Quiesce only
   the absorbed writers, preserve run state and branches, and record exclusive
   ownership transfer. Do not queue all inherited drafts.

7. Create or update the bootstrap PR:
   inspect an existing open PR for head campaign/kalayantra first;
   create only if absent. Review the exact head, pass CI, queue through main,
   and wait for MERGED. Do not force-push.

8. Fetch the merged code. Explicitly install:
   bash 00_ARCHITECTURE/briefs/kalayantra/fleet/install_tracker.sh \
     --gov "$KY_ROOT/wt/campaign/platform/scripts/governance"

9. Run launch acceptance. It must verify code/model/specification hashes,
   exclusive claims, review-before-completion, configured HOLD, lane environments,
   inherited ownership and all mandatory production capabilities.

10. Launch one implementation worker plus S/N/V. Observe a genuine exclusive
    claim and durable progress receipt. Raise the pool only after that succeeds.
    Do not wait inside one Codex session for a multi-hour production job.

11. Report the bootstrap PR/merge SHA, tracker URL, enabled lanes, first claim,
    launch-acceptance receipt and HOLD command. The fleet continues autonomously.

If bootstrap acceptance fails, record the exact defect and continue authorised
bootstrap repairs. Never replace a failed prerequisite with a timestamp, note,
unreviewed default or a request for the human to approve missing evidence.
```

Operator configuration must create its directory before copying a nonsecret configuration file. Remove database URLs from `env.example.sh`; production secret provisioning belongs to the isolated executor. Addresses KY-01/04/05/11/20/26.

# 5. What to cut and what is missing

**Cut:**

- Repeated full-charter/whole-check-suite work for trivial idle cycles.
- Minute-by-minute paid model polling when no eligible work exists.
- Automatic queue sweeps by shared GitHub author.
- The claim that a byte-count review detector proves acceptance.
- Repeated rebase/force-push pressure on inherited drafts.
- A separate expensive cycle for each already-fixed default decision.
- Logs copied into multiple free-text surfaces.
- “Never wait” wording applied to asynchronous jobs: record state, exit, and resume on an event instead.
- Unnecessary new governance ceremonies. Preserve only the checks that enforce scope, truth, compatibility, ownership and recovery.

**Add:**

- Pinned specification delivery.
- Atomic ownership and structured completion.
- One complete inherited-work disposition.
- A real credential/execution boundary.
- Deployment compatibility and lease enforcement.
- Complete Gochara test→measure→final-candidate→qualify→seal→serve ordering.
- Exact-head review and machine-readable production receipts.
- A coverage matrix for all five charter lines.
- A finalizer outside the agents it stops.
- A single earned-progress audit suitable for the next morning.

The goal should be **autonomous execution with honest failure states and automatic recovery**, not a promise that empirical evaluation will pass. No execution design can guarantee that the model meets its predeclared scientific thresholds; it can guarantee that failure is detected and never relabelled success.

# 6. Hashes

Computed with `shasum -a 256`. Paths below use the aliases defined above.

## Design under review

```text
44326f3d7ba815521b2051b822cf090a266781b3350210d1c6adc0031a290832  CH
ee08931e425eaa4fa1a72d73408b90bb1a2cd24208031f19682d2fba2f9a9eb5  OS
9531d01db5babf245aa45e7c1e308003361fb0b33b205aac249907f0608a68c3  KICK
2125a2df0554ab4ab61b5d92d3d9e6ff63295b56e32f8c5036a2d5c7caf118c2  S
e1e088ea399478d3840fe8c9b7fff00e7300f07a79f370573a8fdbfac9621626  N
959ef6c7e115b6741d9d8b644862c662c51a069af6abfe7b8890de04bf22d7a6  V
411804b7ab54df901656a063df3c4181d0ea1e216b454ba8ef96bddce87509be  K
13d792ea875b08ccca59b0a2597d727dbfb900757bd7c8b261202eda432f88fc  FLEET
16dfcf793572d241ce90372e71eedf1e400fac354749487502ae3f21a50b8c7a  INSTALL
a9a515353340b47168a0af496b97727b717fda079c58a53402fa22be224794b3  PREFLIGHT
4212842d837cd29ec46ec6b872d0399c9726de3b84c3f4d9f0b3cd0514073aa2  PRECHECK
d1df1351dab081f205012bb13434f07c9ddb3026999668ebcd886d51541fc46c  LOCAL
08d89b85f08574d7e8e2f611d690a8fe3cfb4ff118734472c118287930e00090  ENV
9b22601e80ad3613f8355f26f9f535235c3c66613c1470eb1840146454bffac5  M
```

`LOCAL` was modified in the working tree during the review. Its final hash above, and the final model hash, were rechecked before reporting.

## Requested precedents and implementation references

```text
a364863fc3efcf416ca16773093dda72ea7b632d6d63cd1c13a387889121e12e  CLAUDE.md
11d1349983f021f765ba5a9c678039809c667b1ebe78b43abbae166c573130a6  CLAUDECODE_BRIEF.md
8fb6a302355cd5e729a45a86b25f8258226d0f1ba5647e72de2329b9b67323d7  COORD
a78f67309611dd483555f52221e2894c65ef87d5c94a36958e1777ee73962533  GIP
ca9b37a754ac61896215e22bd2d2199916d9783c74238ecf4dce3049b67674b3  HYGIENE
4c70a050e7beda5149917d0277c1cd4d5b6d80896110886d68c143e969677f62  00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PURNA_OWNER_SURROGATE_CHARTER_v1_0.md

54ecf3f2ffb20d229a042867818976ac6e0b53b862cee73f59a60ca45429d3a7  PP
52bc810e178daa24b516ad24d0d6be656a7b89bf91388547dedad4ed8aca756d  PE
37d6cc9bafdf815a96a0311fdec448094705a055f95cbd691492c4b8fb72290b  SMALL
7bf117613c2e5c9220ab6aac8c20a2d46032fdf3d24088d977de220e2feea52d  MEASURE
3c750948f8d0fb5d2e9cb60fb4c688b7438f728b5621e9e172b25e81c933b076  PB/decisions/NATIVE_RULINGS_BY_DELEGATE_v1_0.md
24b5826262bf5bd4738f873fe12c2b3fc0b0cdf1dc0182f80c2b4a6f6cd4d21f  PM
f5c95638da3cfdc0ae5161ae38e2d988577d422990abd87aa9e28e473267df86  T/cli.py
cb8e15bf8c615d9c0e4feb3e8fc90c20d7fee505b33faea19b5c7b008a4d2fd7  T/server.py
e3ce074e8d5ecf868a35cd07dfc57128680a31269b1817cde949e00d6eac36c5  T/state.py
423c1f12b04611f36a0b64c543a7976580fc52d879ab93d73e18a37608fe7434  T/detectors.py
0c5933b75c28bd52285a6e97718b0a4582ef797b789ab02334f4d5462de89d1d  T/runner.py
b41889fbe88812ca3184ddf048745596ccbb6a3383af000cf421061d54a2dafe  T/events.py

221f32b084d2a81a3c027b3a08dba0b0a6942a7e086fd9fb0d0a98edd9c77d41  CI
aeeff19247c7016302696576b6c577e63de94b8356e1ebf6caf928cbb06504a5  DEPLOY
1323bee4a06c4ff7fd07a598b050456868f1cd1bcac8929178043180714084ff  TAP
e2dd44d374487a19e5cf3d442a04c7de625abae1b4aff15d914fe4beab52d06e  platform/scripts/governance/secret_scan.sh
0f37efd64dfc7742050980694effbb1bdb21fe62da04c7248505b32b7f67e74c  DRIFT
c5e194f693cba706eac32b079cb6e22397c14efdb4dbb0fa6f435ef25807f9fc  SCHEMA
58c14a8482d9b251f34026e0609092bb8fa545e56050fe8f38324c8ccbbd9f08  CLASSIFY

a572046eae4c10d2204bbbf03767f008bf97cad0dc4e216751b63246ee14222a  platform/python-sidecar/pipeline/orchestrator/asset_runner.py
50528d42137f99e81b805066440b20f21140f65857313533b8e6e5f2243c451d  platform/python-sidecar/pipeline/orchestrator/main.py
7bdd87cd1b78c4907666480d95dd0a1fb8ad1425bcfca4742153b051546cdd21  platform/python-sidecar/pipeline/orchestrator/writers/__init__.py
9419471ff84f40e4a80f5134116f2b09fe4caad1d97992734beea22ebae16081  DISPATCH
6a2ac92668fc674620cae62a8636dc37758fbd89c0f494fe0929594d03f679e1  platform/python-sidecar/services/gochara_kernel/ephemeris_pins.py

2e9f8724e43c9e347024150c47a4d5e2e3809fff28ffe20e98923c28e4595a96  MIG1081
74bf0f157b10cad7c22d803a4765b9e607646e860a05e4a088f35b1750ca6d40  AUTH527
3729f957b2a589828256748372a9cc732039ee84eaaeed5283edd89290e3f71a  MIG1236
05a8f897a0b8ae6b955915eced717ad30c98af485d490185333a88355707bc6b  platform/migrations/1240_gochara_window_verification_gate.sql
a187660afd52081198f0951d25856aaff8f09a59811f51d2117519b1b28f0406  MIGRATE
e51a94ac048fc2e3b1688b512aab4a3d152293d0c137131e23059cd876b62a80  platform/python-sidecar/services/gochara_kernel/verification_job.py

a8353dc48563e08710f1fc6815ace2f15b7e9db5eec5d4ebea1e6dde1120514e  EVAL
2eae6a1b3eef4b465a185fb878d88a477e7576d4e8f76d842b022e54c68cda3a  FINAL
5e031a628d2aa826f5e8544c1e2566e02986186dd13c2f2f158a1f143b871c76  RULING10
```

## Missing requested files — no hash available

```text
MISSING  00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md
MISSING  00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md
MISSING  00_ARCHITECTURE/briefs/l3_families/decisions/KALA_LAYER_NATIVE_RULINGS_v1_0.md
MISSING  00_ARCHITECTURE/briefs/l3_families/reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md
MISSING  00_ARCHITECTURE/briefs/nirmana/sessions/supervisor/CYCLE_CONTRACT_C8_V23.md
MISSING  00_ARCHITECTURE/briefs/nirmana/sessions/supervisor/run_fleet.sh
MISSING  00_ARCHITECTURE/autonomy/CHARTER.md
```

