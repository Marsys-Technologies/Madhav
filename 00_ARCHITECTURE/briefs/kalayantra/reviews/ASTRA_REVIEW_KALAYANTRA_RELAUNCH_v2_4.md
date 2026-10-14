---
artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH
version: "2.4"
verdict: PROCEED-WITH-FIXES
blocking_count: 3
reviewed_commit: fcbc06437
review_date: 2026-10-11
review_mode: read-only
---

**1. Verdict**

The autonomy design is substantially corrected, but several operative instructions still contradict it.  
Apply KW-01…KW-06 in B-0c before any B-1 launch; all six have written replacements below.  
This permits continued preparation, not launch acceptance: qualification receipts remain absent, `HOLD_MERGES` remains present, and 41 Claude/Madhav worktrees remain registered.  
Owner decisions, including amended D-4, revised D-6 and D-9, are accepted without reopening them.

References: **P** = [plan](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_4.md); **C** = [cockpit prompt](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_COCKPIT_PROMPT_v2_4.md); **A** = [surrogate definition](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/.claude/agents/kalayantra-owner-surrogate.md); **S** = [live planner state](/Users/Dev/kalayantra/run/PLANNER_STATE.json). CLOSED below means specification closure, not runtime acceptance.

**2. Part 1 — Closure**

| Finding | Status | Evidence and conclusion |
|---|---|---|
| KV-01 | **PARTLY** | P:13–26 establishes the single anchor and activation record, but P §16.3:723 still reserves bundle changes to the owner and C:20–32 cannot resume through an authorized successor bundle; apply KW-04. |
| KV-02 | **PARTLY** | P §4a.1:173–189 provides recovery records, but C:38–46 requests an absent `active` index and incorrectly converts external checkpoints into blobs, while P §11 conflicts with controller ownership; apply KW-01/KW-02. |
| KV-03 | **PARTLY** | P B-0c:655 and C:51–61 correctly separate `kyboot.py` from campaign dispatch, but P:648–649/657 retain mandatory owner-merge prerequisites; apply KW-03. |
| KV-04 | **CLOSED** | P §4a.2:190–209, §6:380–382 and §11:589–597 specify deterministic waiting, durable admission stops, meaningful progress and persistent breakers; the remaining controller/child integration defect is KW-02. |
| KV-05 | **PARTLY** | P:217–228 and A:29–54 correctly defer publication, but the SURROGATE dispatch row at P:346 still prescribes `ky decide` without the pending-state restriction; apply KW-05. |
| KV-06 | **CLOSED** | P §7:416–430 and B-0c:655 require configuration-bound passing qualifications, positive limits, launchd-context probes and refusal on unknown results. |
| KV-07 | **PARTLY** | P §15:694–707 correctly adopts D-6/D-9, but B-2 and the baseline-import requirement still demand merged source during the hold; apply KW-03. |
| KV-08 | **CLOSED** | P:229–238 and A:26–40 distinguish campaign authorization from human platform approval and retain inherited boundaries; approval-status verification needs the separate KW-06 correction. |

| Carry-forward | Assessment |
|---|---|
| KU-01 | **Correctly carried, not closed.** B-0c:655 requires the replacement; installed `audit.py:123–124,155–157` still demands post-deploy verdicts more broadly than `completion.py:81–96`. |
| KU-02 | **Correctly carried, not closed.** B-0c:655 retains the original storage/cleanup replacement, and P:206–208 adds crash cleanup; installed `local_db.sh:23,102` still lacks the required mount and keeps the stopped container. |
| KU-03 | **Correctly carried, not closed.** All three canonical/compatibility pairs currently have equal bytes; the required manifest binding and mismatch refusal remain acceptance obligations. |
| P-1/P-2 | **Correctly carried.** P:269–272/394–430 retains stored-sign-in-compatible launch flags and qualification; local Claude reports **2.1.296**, but actual model/tool execution remains unproved. |

**3. Findings**

**KW-01 — BLOCKING before B-1 — Legacy migration is not executable as written**

**Location:** P §4a.1:183–188; C step 2:38–46; S:7–20,90–100,137–143.

**Defect:** The live state has no `active` member, although step 2 requires reading it before migration. The three unhashed entries are a historical trust check, a coordination commit and a PR reference—not three file blobs at `e3b5294e2` that should all be superseded by launch changes.

**Failure:** A fresh session either stops immediately or manufactures replacement evidence and supersession claims.

**Exact replacement:**

> Under exclusive planner ownership, detect the legacy state schema before reading `active`. Preserve the original state and historical checkpoints; derive the compact active index from `in_progress`, `deferred` and the next step’s dependencies. Initialize absent action, awaiting, command and loop collections as empty without treating their absence as proof of process absence.
>
> Migrate evidence by type: retain the historical `trust-anchor` against its recorded source commit and perform a new trust check against the currently authorized source; retain `coordination.notice` as commit `b9fda0ccc8da51ec30ccf7e3622cddb57b48477f`; retain `B-0b.pr` as PR #3441 with its historical observed commit, refreshing external state when needed. Do not relabel these entries as file evidence or superseded launch proposals.
>
> Only `plan-change.proposal` is rebound to its verified file blob at `e3b5294e2`, retaining its existing SHA-256 and recording adoption by v2.3 §5/§7. Do not recreate its owner-wait. Record the migration idempotently through an action record, preserve failure history, and update session identity only while holding the planner fence.

**KW-02 — HIGH before conductor activation — Controller and child both own the role state**

**Location:** P §4a.1–2:174–193; §10:564–565; §11:574–595; C steps 2/8.

**Defect:** The controller holds the role lock, but §11 instructs the conductor job to acquire that same lock and write `CONDUCTOR_STATE.json`. Cockpit step 8 also orders a checkpoint even when the cockpit is only observing a controller-owned role.

**Failure:** The first child can fail duplicate-instance acquisition, or implementations can introduce multiple state writers to make it proceed.

**Exact replacement:**

> The deterministic controller is the sole role-lock holder and role-state writer across child jobs. It verifies the approved bundle, acquires ownership, reconciles actions and surviving children, validates resume/gates, and supplies each child an immutable state snapshot and a fenced job identity. Child jobs neither reacquire the role lock nor write the shared role-state file; they return results and checkpoint/action requests for the controller to validate and persist.
>
> Controller identity and child provider-session identity are separate fields. Child rollover never replaces controller ownership or resets campaign failure/no-progress history. Before a controller exists, the cockpit may perform these duties while exclusively holding the role lock.
>
> On cockpit exit, checkpoint and release ownership only if that cockpit holds it; an observing cockpit submits any requested handoff through the command queue. Add acceptance cases for a first child under a live controller, successive child sessions, observer exit and stale-child write refusal.

**KW-03 — BLOCKING before B-1 — D-9 has not replaced the old installation prerequisites**

**Location:** P §2:105; §13:617–619; §14:648–649/657.

**Defect:** The Wave B heading prohibits installation before the owner’s merge, and B-2 simultaneously requires an independently accepted branch head and “owner-merged source.” The accounting prerequisite also still requires a merged baseline implementation, making bootstrap measurement depend on the prohibited merge.

**Failure:** B-2 cannot satisfy its literal prerequisites during the hold, or the installer bypasses an instruction informally.

**Exact replacement:**

> **Wave B — bootstrap during the hold.** D-1 and D-9 apply. B-0c may activate its separately reviewed immutable bootstrap supervisor; B-2 installs the independently accepted immutable source bundle. Neither requires a main merge.
>
> **B-2 — Review and install.** Independent review accepts the exact source head or component heads assembled into the installation bundle. `install.sh` verifies those heads, review receipts and manifest hashes, then installs the fleet, tracker, wrappers and approved plan/prompts/cards. `INSTALL_RECEIPT.json` records source commits, tree/component hashes, review references, qualifications, `CLAUDE_BIN` and the running tracker’s loaded revision; a merge commit is optional historical metadata, never a prerequisite.
>
> Preserve the existing requirements to disable and prove absence of old dispatchers, create the campaign checkout within capacity, publish staged D-RETIRE decisions, reconcile legacy state, and pass preflight plus `kyversion.sh --bootstrap`. Only the accepted bootstrap receipt permits isolated rehearsal activation. Under `HOLD_MERGES`, merge intentions remain durable local requests; no GitHub queue submission occurs.
>
> In §2 and §13, replace the merged-baseline prerequisite with: “The baseline implementation must be independently reviewed, installed from a receipt-bound immutable source head and proven to cover the reported sessions before any v3 total is reported.”

**KW-04 — BLOCKING before B-1 — Authorized bundle changes break the next fresh cockpit entry**

**Location:** P pairing rule:13–26; §16.3:723; C step 1:20–32.

**Defect:** The pairing rule permits effective D-4 bundle activation, while §16.3 still makes every bundle change owner-approved. Even after a legitimate surrogate-authorized change, the unchanged owner paste compares the new files only against the original commit and must stop.

**Failure:** Resume-anywhere reintroduces a human approval relay, or a session weakens the source check to continue.

**Exact replacement:**

> The initial owner-pasted source commit remains the trust root. Bundle changes require independently reviewed immutable source and either an owner authorization or an effective D-4 decision; changes to owner decisions remain owner-only.
>
> Retain immutable activation records linking the preceding authorization record, old/new source commits, old/new manifest digests, review receipts and authorizing act. A bootstrap activation authorizes only bootstrap sources, never campaign admission.
>
> On a subsequent cockpit entry, first load the trusted cockpit instructions from the original commit and verify the authorization chain to the active source. Then verify the active files against that authorized commit and load its prompt. If no valid successor chain exists, retain the original five-file comparison and stop on mismatch. Never accept a successor merely because the installed files or current activation pointer name it.
>
> Replace §16.3 with this authorization rule and remove the retired PLANNING/CONDUCTOR paste references from the audience and roster descriptions.

**KW-05 — HIGH before conductor activation — The dispatch table still describes premature publication**

**Location:** P §4a.3:210–228; §6 SURROGATE:346; A:29–54.

**Defect:** The corrected agent prohibits publishing veto proposals, but the dispatcher’s operative row still lists `ky decide` as the SURROGATE post-action. Its trigger also includes any non-hard-stop awaiting file without explicitly excluding already pending veto decisions.

**Failure:** An implementation following that row can publish approval early or repeatedly admit surrogate work during the same veto window.

**Exact replacement:**

> **SURROGATE trigger:** an unresolved awaiting item with no handled proposal for its current immutable target/evidence fingerprint. Under its lock, reread handled state before launch. `PENDING_VETO`, hard-stop and external-approval dependencies do not launch another SURROGATE job unless recorded material evidence changes.
>
> **Post-action:** routine decisions may publish immediately through an idempotent action record. Veto proposals persist `PENDING_VETO`, retain the awaiting item and publish no tracker decision. Successful notification submission plus durable cockpit visibility establish the start of the full 30-minute window; failed notification prevents effectiveness.
>
> Only the deterministic veto handler serializes veto, expiry, publication and execution. It rechecks authority, target, evidence, holds and prerequisites before becoming effective, then reconciles its action record before any retry. During bootstrap, the qualified staged supervisor may run this same handler without starting the campaign dispatcher.
>
> Acceptance must prove one proposal across repeated ticks/restarts, zero effective tracker publication before expiry, and refusal after veto, notification failure or target change.

The installed [decision publication path](/Users/Dev/kalayantra/tracker_live/pravaha_tracker/cli.py:561) still publishes immediately; [projection](/Users/Dev/kalayantra/tracker_live/pravaha_tracker/state.py:145) treats delegated final outcomes as effective. The controller boundary therefore remains essential.

**KW-06 — MEDIUM — Approval and idle-health signals need precise detectors**

**Location:** C:83; P §13:631–638.

**Defect:** `approve-window <id>` records GitHub approval “as done” without requiring platform readback. The health definition requires a live child even during legitimate controller waiting, when the design deliberately has no model child.

**Failure:** Status can claim an unobserved platform approval or classify a correctly idle controller as unhealthy.

**Exact replacement:**

> `approve-window <id>` records an owner report and requests deterministic GitHub readback. Mark platform approval verified only from evidence bound to the expected repository, workflow run/attempt, environment, source SHA and required owner approval; otherwise retain `approval_reported_unverified` and the external dependency. Approval, workflow completion and semantic operation acceptance remain separate states.
>
> Loop health requires verified controller identity, the authorized bundle and a timely successful control iteration. When a child is expected, additionally require its matching process identity and liveness; when none is expected, require a legitimate recorded waiting state and no unreconciled child. A stopped loop reports STOPPED. Missing model children during legitimate waiting never trigger model admission.

**4. Part 2 — Fresh-session and launch walk**

1. **Step 1:** All five named files match `fcbc0643766b85c8cf3b407ff71400b871b224fd`; initial entry works assuming that is the owner-approved anchor. Successor entry needs KW-04.
2. **Step 2 — first instruction that cannot be followed literally:** read `PLANNER_STATE.json → active`; that member does not exist.
3. **Migration:** KW-01 supplies the missing transition: 12 present file checkpoints match; the retired proposal matches its historical blob; the three external/trust entries retain typed evidence.
4. **Step 3:** Cockpit performs B-0c; qualified `kyboot.py` later owns direct bootstrap supervision. Missing helpers do not authorize campaign activation.
5. **Step 4:** Report observed B-0c state, absent qualification/manifests, 41 registered worktrees and the surviving merge hold; report unavailable helpers explicitly.
6. **Step 5:** Complete and independently accept B-0c, including these replacements and KU-01…03; satisfy B-0a’s capacity prerequisite before B-1.
7. **Step 6:** Commands enter the durable queue; one fenced owner applies them, with KW-05 governing veto and KW-06 governing approval reports.
8. **Step 7:** No campaign worker by hand, no main merge under the hold, and no removal of another actor’s hold.
9. **Step 8:** Only the role owner checkpoints/releases; observer exit leaves controller ownership intact, and crash recovery uses action records.
10. **First B-1 launch:** `kyboot.py` verifies the immutable staged bundle/review, qualification, limits, paths and holds; records the action/process identity; directly supervises §7 execution and obtains independent review.
11. **B-2:** KW-03 installs reviewed heads without merging, reconciles legacy state and proves the loaded revision; its accepted bootstrap receipt authorizes rehearsal only.
12. **B-3:** Exercise isolated real CLI/typed transitions and negative fixtures; require unchanged live EVENTS, no external mutations, cleanup and measured tested hashes.
13. **B-4:** Independently accept coverage and admit the initial packet set.
14. **B-5:** Bind final manifest, loaded revision, rehearsal, coverage and governance evidence; record the owner/effective-D-4 authorization in the activation record.
15. **Start:** Only matching final acceptance, all five release conditions, required hold clearance and effective D-7 produce `OWNER_RESUME`; file presence alone does not start the conductor.
16. **First conductor iteration:** Controller validates/locks/reconciles, then waits without a model; the first actionable batch launches one bounded child under KW-02, and accepted results/checkpoints return through the controller.
17. **Veto example:** A capacity-above-maxima proposal remains `PENDING_VETO`, visible and unpublished; at expiry the veto controller rechecks unchanged inputs, publishes EFFECTIVE once, applies the action and records EXECUTED.
18. **Protected window:** Bound request → independent pre-acceptance → effective campaign authorization → protected workflow dispatch → external owner-approval dependency; independent work continues until verified approval and subsequent execution/readback.
19. This completes the **conditional instruction walk**; none of these launches or transitions was executed in this review.

**5. Part 3 — Owner directions**

- **Resume-anywhere: PARTLY.** Durable recovery is the correct remedy; legacy migration, role ownership and successor trust still need KW-01/KW-02/KW-04.
- **Autonomy with surrogate: PARTLY.** Delegation and human-only boundaries are correct; contradictory installation/publication instructions still require correction.
- **Zero idle: ADDRESSED at specification level.** Waiting is deterministic, model admission is event-driven, and progress excludes bookkeeping; implementation acceptance and KW-02/KW-05 remain necessary.
- None of the three directions now has a **WRONG REMEDY**.

**6. Part 4 — Token economy**

- **Loop restarts:** durable enabled/STOP/completion/backoff/breaker state guards admission; three no-progress runs persist across restarts.
- **Surrogate ping-pong:** stable awaiting identities, evidence fingerprints and changed-evidence reopening provide the guard; KW-05 makes pending-state exclusion explicit.
- **Cockpit/controller duplication:** the queue and handled-state records are sound; KW-02 removes the conflicting second state writer.
- **Empty inboxes:** §11 now forbids model waits and requires an actionable batch; no empty-inbox model-turn path is intended.
- **Failed launches:** configuration-bound qualification and unsupported-model refusal prevent repeated speculative launch attempts.
- **Interactive context:** remains owner-controlled and can grow while a cockpit stays open; compact fresh-session input does not cap an existing conversation.
- **Total spend:** intentionally has no finite cap under the owner decision; no savings or actual v3 consumption can yet be claimed.
- **Measurement:** KW-03 removes the unnecessary main-merge dependency without weakening review or accounting coverage.

**7. Part 5 — Signal honesty**

- **Remaining unsupported claim:** cockpit `approve-window` can currently label platform approval done without a detector; KW-06 repairs it.
- **Incorrect predicate:** “loop healthy” currently requires a child during idle waiting; KW-06 makes it conditional.
- **Adequately specified:** useful progress, qualification PASS, notification submission/visibility, veto effectiveness, `WAVE_B_DONE` and `READY_TO_START` have defined evidence requirements.
- **Not yet earned:** those v3 signals remain unknown/unqualified until their implementations and negative fixtures pass; the observed run directory contains no qualification or final activation receipts.
- A surrogate journal entry proves recording only; EFFECTIVE requires the veto/authority checks, and EXECUTED requires reconciled action evidence.

**8. What I could not verify**

- Runtime authentication, model availability, permission isolation, launchd recovery, process fencing, DB cleanup and actual veto execution: no probes, builds or tests were run.
- GitHub’s current reviewer configuration, PR review state, approval events or protected execution outcomes; the checked-in workflow names `data-plane-production-cutover`, and its operator note requires reviewer approval.
- Complete release readiness or SS’s five-part handoff; no release receipt was present in the inspected snapshot.
- Concurrent B-0c drafts: untracked cards/probe files appeared during review and were excluded from the `fcbc06437` assessment.

No files, tracker/fleet state, worktrees or scratch resources were created or changed by this review.

