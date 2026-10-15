---
artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH
version: "2.3"
verdict: REWORK
blocking_count: 6
reviewed_commit: a5c0bef2a
review_date: 2026-10-11
review_mode: read-only
---

**1. Verdict**

The autonomy direction is sound, but v2.3 is not yet a consistent, executable launch contract.  
Continue B-0c preparation; resolve KV-01…KV-06 before B-1 launches, and KV-07…KV-08 before conductor activation.  
The principal defects are premature decision publication, contradictory bootstrap ordering, incomplete restart discipline, and unbound approval transitions.  
Owner decisions 1–8, D-1…D-8 and Q1–Q4 remain accepted givens.

References: **P** = [plan](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_3.md); **C** = [cockpit prompt](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_COCKPIT_PROMPT_v2_3.md); **A** = [surrogate agent](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/.claude/agents/kalayantra-owner-surrogate.md).

**2. Part 1 — Owner directions**

| Direction | Assessment | Section evidence and conclusion |
|---|---|---|
| Owner-controlled session renewal; no automatic hand-off | **PARTLY** | P §4a.1, §11 and C steps 2/8 remove thresholds correctly. Headless job limits need not constitute owner hand-offs. However, checkpoint-after-completion cannot recover an interrupted side effect, the present state contains a deleted evidence file, and per-message locks do not serialize shared state. Checkpoints also do not bound an indefinitely growing interactive context. |
| Autonomous, multi-agent execution with persistent surrogate | **PARTLY** | P §4a.2–4, §6 SURROGATE and §10 establish the intended arrangement; persistence through records and on-demand jobs is sufficient in principle. FROZEN and credential hard stops are appropriate. Veto publication, bootstrap activation, D-6 merge admission and protected-environment approval remain inconsistent or unproved; inherited §I/§N and §L restrictions still bind. |
| Zero idle, high velocity, accuracy retained | **PARTLY** | P §4a.4, §6–§9 retain independent review, typed completion and verification boundaries. However, §11 puts timed inbox waiting inside model jobs, while unconditional `KeepAlive`, unspecified progress semantics and surrogate restart decisions can generate repeated paid work without useful progress. “Zero idle” must mean immediate useful admission, with idle waiting performed by scripts. |

**3. Findings**

**KV-01 — BLOCKING before B-1: the replacement prompt has no complete trust-chain transition**

**Location:** P front matter `pairing_rule`, §10–§11, §16.3; C step 1.

**Defect:** The pairing rule still requires PLANNING and CONDUCTOR pastes, although both have been deleted and the cockpit supplies only a source commit. D-4 permits veto-class bundle changes, while §16.3 reserves bundle approval to the owner, leaving the source of the conductor’s independently approved expected digest undefined.

**Failure:** A loop either cannot satisfy its first verification instruction or obtains its “expected” digest from the same mutable bundle it is supposed to verify.

**Exact replacement:**

> There is one owner paste. Its approved source commit binds the plan, cockpit prompt, owner decisions, strategy and surrogate agent definition. B-0c generates an independently reviewed bootstrap manifest binding all generated cards, schemas, launcher inputs and loop prompts to that source authority. Before every bootstrap launch, the supervisor verifies that manifest and its review receipt.
>
> Final bundle activation records an immutable manifest digest, source commit and authorizing owner act or effective D-4 surrogate decision. The launcher supplies that approved digest to the conductor independently of the installed manifest. Bundle changes follow the same reviewed activation procedure; changed inputs invalidate affected acceptance receipts. Remove all instructions requiring the retired two-paste workflow.

---

**KV-02 — BLOCKING before B-1: resumption lacks crash recovery and state ownership**

**Location:** P §4a.1/6, §11; C steps 2/8; live `PLANNER_STATE.json`.

**Defect:** Checkpointing only after a completed step leaves an interruption between an external action and its checkpoint, while different message locks permit simultaneous writes to the same role-state file. Current resumption also encounters three checkpoints without file hashes and `plan-change.proposal`, whose hashed file was deleted by the reviewed commit.

**Failure:** A fresh session can repeat an action, lose another actor’s checkpoint, or stop on intentionally superseded evidence.

**Exact replacement:**

> Each role-state file has one fenced writer; cockpit commands enter a durable command queue and do not overwrite a loop’s session identity. Before any side effect, persist an action id, inputs, target identity and intended transition; after it, persist the observed result atomically. Recovery reconciles unfinished actions against GitHub, tracker and process evidence before retrying. A message lock must be followed by a fresh handled-state check.
>
> Preserve historical checkpoints. Validate file evidence by hash and external evidence through typed commit/event references. Migrate the deleted proposal checkpoint to its verified blob at `e3b5294e2`, recording supersession by v2.3 §5/§7; do not recreate the obsolete owner-wait. Resume reads a compact active-state index and bounded journal tail, validating the dependency chain needed for the next action. Exit callbacks are best-effort; correctness must survive their absence.

---

**KV-03 — BLOCKING before B-1: B-0c activation depends on unfinished B-1/B-2 machinery**

**Location:** P §4a.2, §14 B-0c/B-1/B-2, §16.1; C steps 3–5.

**Defect:** C step 3 starts the dispatcher whenever `kyctl.sh` exists, although the dispatcher is implemented in B-1 and installed in B-2. Section 16 nevertheless says installation happens in B-0c, conflicting with §14’s installation boundary and the requirement that B-1 be supervised directly.

**Failure:** A partially assembled bootstrap can start missing, old or unreviewed machinery; first-run status and surrogate invocation also depend on not-yet-installed helpers.

**Exact replacement:**

> Distinguish bootstrap supervision from installed campaign operation. B-0c may activate a separately reviewed bootstrap supervisor from an immutable staged source bundle under D-1; it has its own proven instance lock and directly supervises B-1 jobs under §7. It must not start the campaign dispatcher or use `fleet_live` as an installation shortcut.
>
> Before that supervisor is qualified, the cockpit performs B-0c work and invokes the source-bound surrogate with its reviewed staged card. Status uses observed files and reports missing helpers as unavailable. B-2 installs the reviewed merged bundle; only its accepted bootstrap receipt permits dispatcher activation, initially for isolated rehearsal. File existence alone never authorizes activation. Campaign admission still requires final Wave B acceptance and the full release gate.

---

**KV-04 — BLOCKING before B-1: loop shutdown and useful-progress detection are incomplete**

**Location:** P §4a.2/6, §6, §11–§13; C steps 3/8.

**Defect:** Unconditional launchd `KeepAlive` restarts an exited supervisor, but the plan does not specify how STOP, completion or the three-run breaker disable further admission across that restart. The conductor performs timed waits inside model jobs, and “checkpoint progress” can include bookkeeping rather than completed useful work.

**Failure:** Stopped loops can reappear, empty inboxes consume repeated model turns, and a surrogate can repeatedly restart a loop whose underlying condition has not changed.

**Exact replacement:**

> launchd supervises a deterministic controller, not an unconditional chain of model invocations. The controller holds the role lock with supervisor and child PID/PGID/start identities, reconciles surviving children before replacement, and honors durable enabled, STOP, completion, quota and circuit-breaker state before every launch. Explicit stop and finalization disable model admission across controller restarts.
>
> Wait for inboxes, gate changes and deadlines outside model sessions. Launch a bounded job only for a deduplicated actionable event or eligible work item. Progress means an accepted step/result or changed external dependency, never a heartbeat, timestamp or journal append. Persist no-progress counts across restarts; reopening a breaker requires recorded changed evidence, including when the surrogate decides.
>
> Bind test databases to their actual originating session and enforce KU-02 cleanup on its termination, including crashes. Closing a cockpit neither adopts nor deletes another session’s databases. Probe duplicate start, orphan recovery, STOP, completion, shutdown and unchanged-condition restart refusal.

---

**KV-05 — BLOCKING before B-1: veto-class decisions become effective before the veto window**

**Location:** A lines 33–41; P §4a.3, §6 SURROGATE, §10; live [CLI decision publication](/Users/Dev/kalayantra/tracker_live/pravaha_tracker/cli.py:561) and [decision projection](/Users/Dev/kalayantra/tracker_live/pravaha_tracker/state.py:145).

**Defect:** The agent instructs immediate `ky decide --delegated` publication and moves the awaiting item to `done` after recording a future effective time. The live tracker treats a delegated approved decision as effective immediately and has no veto-deadline check on that path.

**Failure:** Dependants can proceed before the owner’s veto opportunity; notifications and the cockpit can also lose the pending item.

**Exact replacement:**

> Veto-class decisions first enter `PENDING_VETO`, retaining the awaiting item and immutable target parameters, evidence digests, notification result and deadline. Do not publish an effective tracker decision or mark the awaiting item done at proposal time. A successfully submitted notification and durable cockpit entry establish the window; notification delivery is not evidence that the owner read it.
>
> One deterministic controller serializes veto, expiry and execution. At expiry it rechecks the unchanged target, authority, relevant holds and prerequisites, then publishes the effective decision and executes through an idempotent action record. Failed notification or changed evidence prevents activation.
>
> For D-7, bind the proposed release receipt and final bundle digests before the window; revalidate both gates at activation. An explicit owner pause cannot be automatically undone by the surrogate. Hard stops remain visible as unresolved; no delegated approval is published for them.

---

**KV-06 — BLOCKING before B-1: recorded probes are not a launch qualification**

**Location:** P §5 `CLAUDE_BIN`, §7, §14 B-0c acceptance.

**Defect:** B-0c acceptance says “probes recorded,” while §7 permits unknown results without specifying which unknowns refuse launch. The new SURROGATE and loop roles also lack a complete launch contract for permissions, turn limits and deadlines.

**Failure:** A recorded authentication failure, unresolved permission prompt or unproved isolation condition can coexist with bootstrap acceptance.

**Exact replacement:**

> A launch configuration is qualified only by a passing receipt bound to the resolved executable and hash, version, exact argv, model/effort, role permissions, working directory, environment policy and prompt/configuration hashes. Missing or nonpositive turn limits and wall-clock deadlines refuse launch for every role, including SURROGATE and both loops.
>
> B-0c probes the exact launchd user-agent context: correct user/domain, absolute executable/cwd/PATH, stored sign-in without credential copying, intended tools completing without a TTY or unanswered permission prompt, project CLAUDE.md visibility, excluded hooks/plugins/skills/MCP, observed model identity and measured input overhead. Use observable canaries/configuration evidence, not model self-report alone.
>
> Probe missing authentication, inaccessible keychain, denied tools, invalid settings, timeout, termination and restart. Required safety or operability results that are false or unknown refuse that configuration. Measure overhead in the real role worktree. Requalify changed binaries/configurations at installation; unsupported models produce a launch refusal, not repeated retries.

---

**KV-07 — HIGH before conductor loop starts: D-6 lacks an executable exception and assumes a false deployment property**

**Location:** P §6 hold precedence/MERGE, §10, §14 B-2, §15 D-6; [deploy workflow](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/.github/workflows/deploy.yml:1309).

**Defect:** Sections 6 and 10 prohibit every queue submission under `HOLD_MERGES`, while D-6 authorizes a narrow exception without specifying its admission path. The “no-op deploy” rationale is false for this workflow: successful main CI can run routine migrations and deploy-web without a changed-path condition on deploy-web.

**Failure:** B-2 either stalls or bypasses the hold informally; an allowed-path merge can still advance main, disturb integration qualification and cause production deployment.

**Exact replacement:**

> STOP and global HOLD dominate. Under HOLD_MERGES, permit only an exact-head bootstrap merge satisfying D-6: complete diff within its allowlist, independent review and required checks at that head, a bound batch notice to Strategic Suvarṇa at least 30 minutes earlier, no current objection, and fresh shared-lease/deployment coordination. All other merges remain refused; do not remove the hold.
>
> The surrogate authorizes the merge; the controller submits it through the existing protected path with head matching and cancellation on head change. Recheck eligibility immediately before submission. Treat every main merge as potentially deploying and invalidating integration evidence; record actual workflow outcomes. The no-op rationale is not acceptance evidence. B-2 installs independently reviewed, protected-merged source under D-5/D-6; replace stale “owner-merged” wording accordingly.

This needs implementation before the first B-2 merge, even though its severity deadline is conductor activation.

---

**KV-08 — HIGH before conductor loop starts: protected-window policy approval is confused with platform approval**

**Location:** P §3, §4a.3, §6 EXECUTE, §15 D-4; [protected-window operator note](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALA_PROTECTED_WINDOW_v1_0.md); workflow `jataka-protected-migrations`.

**Defect:** D-4 delegates the campaign decision, but the plan does not identify a permitted mechanism that satisfies the protected environment’s required reviewer approval. Calling that decision effective after 30 minutes neither supplies the GitHub approval nor establishes authority to alter the protection.

**Failure:** The campaign either waits unexpectedly for a human or attempts to bypass the control it promises to preserve.

**Exact replacement:**

> Distinguish campaign authorization, workflow dispatch, protected-environment approval and completed operation. An effective D-4 decision authorizes the bounded request; execution uses an already authorized identity and the unchanged protected workflow. Prove the permitted approval path before claiming autonomous protected-window execution.
>
> If the environment requires a human reviewer that the existing authorized automation cannot satisfy, record an external approval dependency and continue independent work. Never impersonate the owner, retrieve credentials, relax environment protection or substitute a veto deadline for the platform approval. Keep exact-source, migration-list, lease, backup, pre-acceptance, revocation and readback evidence.
>
> Root §I scope, §L architecture restrictions and §N.2 remain inherited hard boundaries; the surrogate’s listed hard stops are not an exhaustive replacement for them.

**4. Part 2 — Launch walks**

1. **Cockpit step 1:** the four named files match `a5c0bef2a`; the local check is executable, but the wider trust-chain mismatch remains KV-01.
2. **Step 2 — first instruction that cannot be completed literally:** validate every completed step’s evidence hash against disk. Three entries lack file hashes, and the proposal file is deleted; the other **12 hashed file checkpoints match**.
3. **Step 3:** the absent-helper fallback is appropriate, but installing `kyctl.sh` cannot by itself make the B-1 dispatcher available or authorize activation.
4. **Step 4:** `kyreport.py` and `kygate.sh` are absent; a specified bootstrap status fallback is needed.
5. **Step 5:** B-0c work can proceed after state migration; direct B-1 supervision is correct, subject to qualified inputs and the new bootstrap ownership rules.
6. **Step 6:** veto/resume commands require serialized pending-decision handling and explicit pause ownership.
7. **Step 7:** preserve the prohibitions; reconcile surrogate-authorized merges with controller execution and the D-6 exception.
8. **Step 8:** checkpointing on a graceful exit is useful; an owner closing the application or a killed process cannot guarantee that callback.
9. **First planner-loop run:** no loop prompt/plist exists at this head, as expected for B-0c deliverables. Even assuming generation, the first unresolved operation is trusted bootstrap activation before B-2; staged authority, locking and direct supervision must be specified.
10. **First conductor-loop run:** the first unresolved input is the independently approved manifest digest inherited from the deleted conductor paste. After fixing that: verify bundle → acquire role ownership → reconcile state → verify effective resume → full gate → admit work.
11. Neither loop was launched during this review; this is an instruction and dependency walk.

**5. Part 3 — KU-01…KU-03 and P-1/P-2**

- **KU-01: carried, not closed.** B-0c explicitly names it; the installed audit still unconditionally requires post-deploy acceptance where typed completion distinguishes code-only work.
- **KU-02: carried, but needs the new lifecycle adapter.** The installed DB helper still lacks a scratch-root PGDATA mount and keeps its container on `down`; successive headless sessions need explicit originating-session cleanup.
- **KU-03: substantially carried.** Canonical/compatibility outputs remain; the bootstrap manifest must still bind both copies and reject unequal bytes.
- **P-1: correctly incorporated** in §7: no `--bare`, explicit settings source and permission mode, probes and measured overhead. Local help confirms `--bare` excludes OAuth/keychain reads.
- **P-2: version remedy incorporated; qualification only partly carried.** Local `claude` is **2.1.296**; retain the proposal’s exact-launch model success requirement and refusal behavior through KV-06.
- I read the deleted proposal from `e3b5294e2`; its operative launch changes are present in §7/§5.
- `--setting-sources`, `--permission-mode`, `--disable-slash-commands` and `-p` appear in local help. `--max-turns` is hidden from that help but defined in the installed executable for print mode; enforcement remains a probe obligation.
- `launchctl` exists at `/bin/launchctl`.

**6. Part 4 — Token economy**

- **Useful guards retained:** packet/card limits, per-job limits, persistent failure fingerprints, quota backoff, accounting deduplication and independent review.
- **No finite total-spend bound exists**, consistently with the owner’s no-budget decision; the required control is refusal of repeated unproductive work.
- **Idle conductor gap:** `ky inbox --wait 540` inside model execution generates repeated model continuations after empty returns.
- **Restart gap:** unconditional KeepAlive plus a non-durable or self-resetting breaker can repeat startup context indefinitely.
- **Surrogate gap:** unchanged awaiting conditions need stable identities and evidence-based reopening, preventing surrogate/restart ping-pong.
- **Double-action gap:** locks prevent simultaneous access only; durable handled-state and external-action reconciliation prevent sequential duplication.
- **Context gap:** checkpoints preserve work but do not bound interactive context; compact resume input and bounded headless jobs preserve the owner’s discretion without reintroducing hand-off thresholds.
- **Measurement:** the historical approximately 31K empty-job input is not a qualified cost for the actual planner, conductor or surrogate worktree.

**7. Part 5 — Signal honesty**

| Signal | Required detector or present gap |
|---|---|
| Loop healthy | Loaded plist is insufficient: verify supervisor identity, child identity, bound bundle, last successful control iteration and legitimate waiting state. |
| Loop making progress | Measure accepted work or changed external dependencies; checkpoint timestamps alone are a proxy. |
| Probe PASS | Exact configuration, observed result, negative control and evidence hash; “recorded” is insufficient. |
| Surrogate decision | Separate proposed, pending veto, effective, executed, vetoed and failed; an appended JSON line proves recording only. |
| Owner notified | Record notification submission and cockpit visibility; human reading remains unknown. |
| Veto expired | A controller checks time, veto state and unchanged targets under the decision lock. |
| `WAVE_B_DONE` | Derive from accepted B-0…B-5 evidence and final receipt; file existence alone is insufficient. |
| `READY_TO_START` | Existing release/final-acceptance detector design is sound; repeat it against the same bound inputs when D-7 becomes effective. |

**8. What I could not verify**

- Runtime authentication, keychain access, permissions, shutdown, restart, resource cleanup and veto behavior under launchd: no probes or processes were started.
- B-0c implementation acceptance: loop prompts, new helpers, surrogate card, `PROBES.json` and bootstrap/final manifests were absent when inspected.
- GitHub environment reviewer configuration and an authorized automated approval path.
- Final release readiness: `HOLD_MERGES` remains present; the current coordination record reports the single rebuild finished and evaluation next, not the complete five-part release.
- `gh pr view` failed because shell network access was unavailable. The GitHub connector confirmed [PR #3441](https://github.com/Marsys-Technologies/Madhav/pull/3441) is open at the reviewed head and returned all 32 filenames, each within D-6’s path allowlist; that establishes path eligibility only.

No builds, tracker/fleet changes, files or scratch resources were created.