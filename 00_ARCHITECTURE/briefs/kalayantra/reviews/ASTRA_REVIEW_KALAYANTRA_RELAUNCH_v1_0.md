---
artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH
version: "1.0"
verdict: REWORK
blocking_count: 5
reviewed_commit: b16b4e24c
review_date: 2026-10-11
review_mode: read-only
---

**REWORK.** The direction addresses substantial waste, but neither pasted prompt is executable as written.  
Five findings must be corrected before planning; the remaining HIGH findings must become explicit bootstrap acceptance requirements before conducting.  
The principal gaps are incomplete scheduling, contradictory bootstrap instructions, packet correctness, and runtime migration.  
All five charter-pinned specification hashes match. The owner’s eight decisions remain accepted givens.

**1. Does the plan address what went wrong?**

| Measured hurdle / finding | Assessment | Plan location and reasoning |
|---|---|---|
| Idle/chatter cycling | ADDRESSED | §§3–4 replace speculative worker cycles and claim-renewal turns with deterministic scheduling, provided the missing lifecycle paths are supplied (KR-04). |
| Suvarṇa hold | PARTLY | §2 establishes the right release gate, but its evidence contract and treatment of the later N-467 stop are incomplete (KR-07). |
| Verifier rework overall | PARTLY | §§4.2, 5–6 reduce duplicate reviews, but suppress necessary evidence-only reconsideration and leave recovery cases unspecified (KR-09). |
| Rework: hash/pin/snapshot | WRONG REMEDY | §5.1 makes any movement of `main_sha` or `next_migration` a stop condition, recreating ordinary-progress rejection as packet failure (KR-08). |
| Rework: environment/baseline | PARTLY | §4.1/B3-5 renames and resets databases without requiring the authentic registry seed missing from the installed helper (KR-06). |
| Rework: deploy evidence | PARTLY | §4.2 schedules post-deploy verification, but omits a complete guarded-completion sweep and changed-evidence retry rule (KR-04, KR-09). |
| Rework: moved heads | PARTLY | §6 avoids duplicate verdicts, but inherited merge-only acceptance does not detect substantive conflict-resolution edits inside merge commits (KR-09). |
| Rework: scope/coordination | WRONG REMEDY | §5.2 reinstates blocking for necessary unlisted files despite the existing learned rule explicitly permitting them (KR-08). |
| Migration 1320 / lane-DB baseline | NOT ADDRESSED | B3-5 has no acceptance proving migration prerequisites survive seed, restore and reset; renaming the databases cannot establish that (KR-06). |
| Migration 1330 outage → protected window | PARTLY | §§5, 7 retain classification and batch grants, but need the manifest, predecessor, privilege and readback requirements carried into executable packets (KR-06, KR-08). |
| Brief/scope friction and parks | WRONG REMEDY | Planning B converts missing columns into deferral, including columns explicitly required by critical-path migrations (KR-03). |
| Census conflicts | PARTLY | B3-6 assigns regeneration to a script, but needs a pinned generator, resulting-tree verification and acceptance invalidation when regeneration changes reviewed content (KR-09). |
| Suvarṇa coupling beyond the hold | PARTLY | §2 publishes settled pins, but does not distinguish a stable build snapshot from mutable main/migration state or later seal-invalidating rebuilds (KR-07, KR-08). |
| LOCAL_ONLY incident | PARTLY | §§4.3, 5 forbid campaign workers from changing controls, but bootstrap inherits the same prohibition and its replacement launcher lacks explicit `no_wrappers` acceptance (KR-02, KR-05). |
| Unowned dependency stalls | NOT ADDRESSED | §§4.2, 7 leave J-0m, production operations and packet exits without schedulable job types, while putting prerequisites after their consumers (KR-03, KR-04). |
| F-1: long-lived coordinators | PARTLY | §4.4 bounds conductor lifetime, but planner restart, subagent scope and observable accounting need tightening (KR-12). |
| F-3: idle/polling cycles | ADDRESSED | §§3–4 remove the main structural cause; forced model “liveness jobs” and unsuccessful-job retries must not reintroduce it (KR-12). |
| F-5: pointer briefs and exploration | PARTLY | §5 supplies useful inline contracts, but unbounded packets, stale excerpts and unavailable test commits can make them worse than pointers (KR-08). |
| F-6: conflict recovery | PARTLY | B3-6 is the right mechanism, but only generator-owned conflicts are safely automatable and changed outputs still require appropriate verification (KR-09). |

The clearest deferral candidate is **J-7**, the optional Tier-2 Sudarśana method explicitly outside sealed 5.0. **D-T2**, and possibly **L0-K**, can follow only if the revised acceptance confirms their corpus work is unnecessary for the retained goal; **J-7b** is another candidate because its brief says documentation-only with no runtime effect. Retire cancelled **B-K-INBOX/B-CLAIM-RECOVERY** obligations explicitly, and fold any still-needed **B-DB-BASELINE** repair into B3-5 rather than discarding it. I cannot justify dropping the remaining K engine, publication, verification or J sealing prerequisites from the briefs; nor can I give an honest reduced count before the dependency closure is rewritten.

**2. Findings**

**KR-01 — BLOCKING — The planning entrypoint cannot reach its contract.**  
Location: [Planning owner steps and steps 1–3](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_PLANNING_PROMPT_v1_0.md:6); conductor Setup, line 25.

The proposed campaign directory does not exist, and the locally available `origin/main` contains neither the relaunch plan nor the audit. Its creation command produces a detached checkout, so the conductor’s later `git pull --ff-only` also lacks the promised tracking branch.

Failure: planning stops at step 1; merely merging the relaunch documents still leaves step 3’s audit path unavailable.

**Replacement:**
> Begin planning in the existing `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan` checkout at the approved review commit. Read the audit from `/Users/Dev/worktrees.noindex/madhav/claude/audit-token-economy/00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md`, pinned to `758e0dbb4`. Do not create the campaign mirror before B3-5. B3-5 must create or reuse branch `kalayantra/campaign`, set its upstream to `origin/main`, and prove that the approved plan, prompts, cards and dependencies are present before conductor startup.

---

**KR-02 — BLOCKING — Bootstrap instructions prohibit their own work and lack an installation handoff.**  
Location: [Planning C–F and rules](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_PLANNING_PROMPT_v1_0.md:46); Plan §§5.9, 7/B3-1…B3-9.

The planner must run database tests and dispatch control-plane builders while its rules forbid builds/DB writes and its builder card forbids fleet/tracker edits. B3-8 additionally requires a registered synthetic item and installed new dispatcher, but neither installation nor its dependency on owner-merged bootstrap PRs is specified.

Failure: obedient jobs stop; improvising jobs invent authority, installation order or live test state.

**Replacement:**
> Wave B permits source changes and local fixture tests only within each bootstrap packet’s declared scope; its Opus bootstrap card explicitly permits those fleet/tracker source files. Campaign builders retain the control-plane prohibition. Sequence B3-1 reconciliation → B3-2/3/5/6 implementation → independent review and owner merge → hash-bound installation of tracker/fleet/wrappers → B3-8 isolated acceptance. Register B3-TEST in a separate fixture model/event root, mock merge submission, and assert no production request or live merge-queue entry. B3-4 and B3-7 remain planner work. B3-9 updates the campaign handshake to Claude and backfills truthful governance records. Root CLAUDE.md and owner decisions remain binding; retired Codex invocations are not copied into cards.

---

**KR-03 — BLOCKING — Re-scope can remove necessary schema work and cannot close the existing DAG.**  
Location: [Planning B, lines 41–44](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_PLANNING_PROMPT_v1_0.md:41); Plan §§0, 7/Waves 1–3.

“Column absent → deferrable” misclassifies required additive schema changes: K5-G1a and K6-4 explicitly need missing generation/shape columns. Meanwhile `parked` is not terminal, `JOIN-ALL` still includes deferred obligations, and Wave 1 depends on J-0m/J-5s assigned to Wave 2.

Failure: the retained goal becomes impossible, or the campaign cannot reach even an honest partial close.

**Replacement:**
> Compute the transitive prerequisites of the retained serving, publication and certification-mapping acceptances before assigning waves. A missing required column creates an Opus schema prerequisite or an explicit blocked contract decision; it is not evidence that the consumer is deferrable. Move J-0c/J-0d/J-0m and subsequent necessary J prerequisites ahead of their consumers. Commit the triage into the model and regenerate readiness/close joins. Record deferred items separately with re-entry conditions; use only supported decision-backed terminal dispositions where required, never an invented `ky not_applicable` command or a parked item counted as closed.

---

**KR-04 — BLOCKING — The dispatcher specification cannot execute the campaign’s full lifecycle.**  
Location: [Plan §4.2](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v1_0.md:115); live `claims.py:101–181`, `completion.py:26–141`.

BUILD queries only K; VERIFY selects PR heads, leaving S-owned model/close work, V-owned artifact reviews and N-owned operations unscheduled. There is also no explicit COMPLETE action, and a V verifier cannot acquire the K item’s tracker claim even though the generic lifecycle says every live job has one.

Failure: jobs can produce accepted PRs while the campaign never advances through J-0m, packet exits, production dispatch or guarded completion.

**Replacement:**
> Add explicit MODEL/CLOSE jobs for S-owned work, ARTIFACT/PACKET jobs for V-owned work, and OPERATION/PRE-ACCEPT/READBACK jobs for N/V executor work; retain the executor’s authority boundary. Add deterministic COMPLETE actions using the existing typed `ky done` guards. Only the owning K/V stream acquires an item claim; PR review exclusivity uses a separate dispatcher job lock keyed by item, phase and head/digest. Use `ky claim "$ITEM" --worker "$SLOT" --lease 10800`; renew from the dispatcher with `KY_LANE="$SLOT" ky renew --lease 10800`. Persist claim/job identity, release successful jobs, recover interrupted work, and reap the process group before releasing a timed-out job’s ownership. Test each lifecycle and restart boundary.

---

**KR-05 — HIGH — Runtime paths and “lean/read-only” launch claims are not enforced.**  
Location: [Plan §§4.3–4.4](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v1_0.md:148); Planning C–D; conductor lines 34–55.

After `cd <worktree>`, `run/jobs/...`, `fleet/precheck.sh`, and `fleet/mcp.marsys-only.json` point to nonexistent repository-root locations; conductor control files similarly target the checkout’s `run/`. The displayed launch omits the promised environment scrub and default strict MCP configuration, while disabling Edit/Write leaves Bash capable of modifying source.

Failure: the first job can fail before Claude starts, controls can be written where the dispatcher never reads them, and tool access can exceed the claimed profile.

**Replacement:**
> Define `KY_ROOT=/Users/Dev/kalayantra`, `KY_RUN="$KY_ROOT/run"`, `KY_FLEET="$KY_ROOT/fleet_live"` and an absolute job worktree in every invocation. Read stdin from `"$KY_RUN/jobs/$JOB_ID.prompt.md"`; run precheck through `"$KY_FLEET/precheck.sh"`; use absolute paths for every control, receipt and configuration file. `kyjob.sh` must construct the scrubbed environment, reject credential variables with exit 78, preserve `no_wrappers`, and set TMPDIR beneath the approved scratch root. Always pass `--strict-mcp-config`, using an explicit empty MCP configuration unless a packet admits the Marsys-only configuration. Treat `--bare` loading of CLAUDE.md as unknown: include mandatory rules explicitly and verify effective startup behavior. Describe verifier access as source-read-only and test/enforce that boundary across Bash, while permitting declared tests and evidence writes.

---

**KR-06 — HIGH — B3-5 is a runtime migration, not a path substitution.**  
Location: [Plan §4.1 and B3-5](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v1_0.md:99); live `local_db.sh:16–17,27–53`, `preflight.sh:12,26,43–44`.

Installed `local_db.sh` rejects b1–b6/v4 and omits registry data that the repository helper now includes; launch preflight still starts Codex smoke and requires 13 lane worktrees plus 11 old databases. I found 31 registered worktree paths already under the Claude/Madhav policy root, while the model’s exact worktree lists, detector paths and executor paths still target the old root.

Failure: preflight cannot accept the proposed topology; resetting slots can reproduce the 1320 baseline failure; new copies breach the ceiling.

**Replacement:**
> B3-5 acceptance requires: a policy-compliant capacity/disposition inventory before creating any copy; one reusable worktree per branch with serialized builder/verifier access; model preflight authorization for those exact assignments; migration of all wrapper, detector, installer, executor and finalizer paths; Claude-only smoke; and preflight derived from configured slots rather than old lane counts. Install the reviewed registry-inclusive seed helper and bind schema, ledger and registry fixture hashes to each slot receipt. Prove authentic 1320 prerequisites and negative cases, reset isolation and cleanup. Test DB storage, temporary files and new logs use the approved scratch root. Preserve existing work until pushed or archived, then use `git worktree remove` and `prune`.

---

**KR-07 — HIGH — The five-part gate lacks a complete evidence contract and stop precedence.**  
Location: [Plan §2 and §4.2.1–2](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v1_0.md:55); runtime tail, N-467 messages at `2026-10-10T21:25:36Z`.

Condition 5 has no authoritative session/role-closure source today, and conditions 2–4 specify outputs without binding them to one release epoch and declared producers. The runtime tail supersedes the summarized branch-only state with N-467’s stop-until-owner-resumes direction, but v3 does not specify its reconciliation or distinguish global HOLD from the bootstrap gate exemption.

Failure: a gate can print five plausible green lines without proving release, or launch despite a surviving owner stop.

**Replacement:**
> Publish one versioned release receipt containing the certification notice’s coordination commit, post-rebuild pin provenance, regeneration commit/output, exhaustive PR dispositions with owner/re-entry condition, and SS’s enumerated session handoff/role-closure records. Condition 5 remains WAIT until that source exists; report attested handover separately from process-observed shutdown. Each condition needs a negative fixture. Require an explicit owner resume record covering N-467. STOP/global HOLD dominate every launch and merge, including bootstrap; HOLD_MERGES prohibits queue submission. Bootstrap exemption applies only to the Suvarṇa release gate. Gate condition 2 admits the producer’s settled pins; J-4p then runs before its consumers, avoiding a gate that waits for work it forbids.

---

**KR-08 — BLOCKING — Packets can be stale, unavailable or internally contradictory at job start.**  
Location: [Plan §5](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v1_0.md:183); Planning B–C.

Tests live on separate packet branches, but no operation places their exact commits into item branches or the precheck manifest. Pinning mutable main/migration values and calling `owns` a floor while blocking every unlisted side-file recreates two measured failure classes; source hashes alone do not prove that an excerpt or schema contract is semantically applicable.

Failure: missing tests, repeated repacketization, unnecessary parks, or confidently implementing an obsolete contract.

**Replacement:**
> Each packet records source path, revision, section boundaries and hash; the admitted schema receipt; exact test commits/digests; and the expected failing assertion on the designated base. The dispatcher installs those tests into the item branch and supplies `TESTS` or the item manifest before launch. Distinguish immutable specification/build pins from the job’s checkout base and the migration allocator’s current state; unrelated main advances do not invalidate a packet. Revalidate relevant contracts and later L1 rebuilds explicitly. Permit necessary generated files, tests, exports and direct consumers with PR disclosure while preserving frozen/cross-campaign prohibitions. Missing required schema becomes a prerequisite per KR-03. Tests for unfinished features must not claim an observed pass until implementation supplies it.

---

**KR-09 — HIGH — Verdict deduplication can suppress valid recovery and preserve invalid acceptance.**  
Location: [Plan §§4.2.3, 6](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v1_0.md:120); live `verdicts.py:5–32`.

“One verdict ever per head” prevents reconsideration when deployment/readback evidence changes without a source change, and red CI is routed to builder rework without distinguishing infrastructure failures. Conversely, `merge_only_between()` checks commit ancestry/types, not whether conflict resolution changed reviewed semantics.

Failure: unnecessary code churn and escalation, permanently rejected deployed work, or queueing materially changed code under inherited acceptance.

**Replacement:**
> Deduplicate active jobs by `(item, phase, head-or-digest)` and evidence fingerprint. Re-review the same identity only after named evidence changes or an explicit reversal request; retain the full verdict history. Classify CI failures before assigning code rework. Inherit pre-merge acceptance only when the reviewed patch is unchanged and conflict resolution introduced no substantive change; otherwise review the resulting head. REGEN merges the target base, regenerates only declared generated outputs with the pinned generator, runs the applicable tests, and records resulting hashes before pushing. Include same-head post-deploy recovery, concurrent scheduling, and substantive merge-resolution fixtures.

---

**KR-10 — HIGH — Frontier routing is not a machine-usable rule yet.**  
Location: [Plan §3, frontier-by-rule](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v1_0.md:92); audit §7; Planning B.

The imported globs mix repository-relative and component-relative roots, while real `owns` entries include prose such as “one additive migration” and multiple annotated paths. Opus selection for frozen files also needs an explicit distinction between review routing and permission to change the frozen contract.

Failure: migration-bearing K1-2/K6-4 can initially route to Sonnet, or escalation can be mistaken for authorization.

**Replacement:**
> Normalize all owned files and globs to repository-relative paths before routing; prose ownership entries must be resolved or conservatively routed to Opus. Use `platform/python-sidecar/services/{kala_core/sky,gochara_kernel}/**`, `platform/python-sidecar/pipeline/orchestrator/...`, `platform/scripts/migrate.ts`, and correctly rooted security paths. Any migration metadata, protected/missing migration class, unresolved migration ownership, frontier import, control-plane change or matching diff content forces Opus. Freeze violations STOP for native authorization under CLAUDE.md §N.2; selecting Opus grants none. Add routing fixtures for KA-1e, K1-2 and K6-4 and rerun routing before accepting the actual diff.

---

**KR-11 — HIGH — Conductor control and final shutdown are not executable under the new topology.**  
Location: [Conductor message handling](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_CONDUCTOR_PROMPT_v1_0.md:45); Plan Wave 3; live `finalize.sh:13–25,53,68–77`.

An S actor cannot ordinarily unblock/park K-owned items, and the prompt omits the steward override used by existing coordination. The finalizer still uses old lane paths, counts `codex exec`, and calls guarded completion with `--evidence` alone, which supplies none of the required typed evidence sources.

Failure: conductor interventions are refused; finalization either stalls or reports process absence using the wrong detector.

**Replacement:**
```bash
ky unblock "$ITEM" --as steward --detail "$REASON"
ky park "$ITEM" --as steward --detail "$REASON; re-entry: $CONDITION"
```
> Give the conductor and dispatcher exclusive instance locks; reconcile both S and steward inboxes at startup and acknowledge only handled messages. Owner chat commands are handled directly, not presumed to appear in ky. The finalizer must stop the dispatcher, prove every recorded Claude job/process group has exited, clean its owned branch worktrees and session DBs, and verify absence independently. Complete C-3/C-4 through accepted, digest-bound typed artifacts using `--artifact-path`, with the required independent reviews. Test that a surviving Claude process or unremoved assigned worktree prevents ACCEPTED.

---

**KR-12 — MEDIUM — Token and progress reporting can mismeasure the claimed improvement.**  
Location: [Plan §§4.3, 8–9](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v1_0.md:161); strategy §1; Planning handoff/report.

The available baseline script separately adds transcript usage and fleet result usage, assuming fleet transcripts do not exist, whereas v3 enables both; killed jobs can also lack the authoritative result event. “Idle ≈0 by construction” is not measured, and the strategy mislabels weighted progress as `46/148 = 37.6%` and expands “~4 defects among 27 early rejections” into “~4 of 74.”

Failure: apparent savings or quality improvements can be accounting artifacts.

**Replacement:**
> Report each job once using a job-id/session-id join: result usage is primary, transcript usage reconciles missing results, and incomplete coverage is unknown rather than zero. Include planner, conductor, subagents, failed jobs and escalations in campaign totals; report guarded completions separately from accepted heads and weighted progress. Correct 46/148 to 31.1% completed and retain 37.6% only as weighted progress. Preserve the original ~4/27 scope. Measure no-progress jobs and bound repeated identical failures; liveness probes are deterministic. Planner startup reads only its latest planner handoff; conductor reads only its conductor handoff. Persist turn/wakeup counters and elapsed time externally, and validate plan/prompt/card versions and source hashes before launch.

**3. Part 2 — Command-by-command launch walk**

1. **Planning owner setup:** the prescribed new copy already breaches the 15-copy ceiling unless capacity is resolved; 31 paths are registered under the policy root (KR-06).
2. **Planning step 1:** first body instruction fails: the plan is absent from the proposed `origin/main` checkout; step 3’s audit is also absent (KR-01).
3. **Step 4:** `kybrief <ID>` is valid; the live model has 148 items versus 145 here, and all five specification hashes match by read-only hashing.
4. **A:** triage can be researched, but priority text alone cannot alter model dependencies or terminal states (KR-03).
5. **B/C:** packets cannot yet obtain `PINS.json`; tests need admitted schema, reachable commits and a resolved local-test exception (KR-02, KR-08).
6. **D/E/F:** cards and bootstrap orders need explicit authority precedence; implementation, owner merge, installation and B3-8 must be sequenced (KR-02).
7. **B3-1:** source reconciliation is doable; “status identical” must compare semantic state at a fixed event boundary, not timestamps/version text.
8. **B3-2:** implementation is doable; “expected jobs” lacks a checked-in expected result and omits lifecycle cases identified in KR-04.
9. **B3-3:** usage round-trip/report rendering are testable; they do not test missing results, transcript deduplication or attribution (KR-12).
10. **B3-4:** checklist production is doable; native/independent sign-off cannot be completed by the authoring job itself.
11. **B3-5:** not acceptable against existing preflight: Codex smoke, 13 worktrees and 11 old DBs must be replaced, not satisfied accidentally (KR-06).
12. **B3-6:** fixture regeneration is testable; five printed lines are not acceptance tests for the five claims (KR-07, KR-09).
13. **B3-7:** red-base tests are testable; an observed positive reference does not exist for every unbuilt feature (KR-08).
14. **B3-8:** lacks model registration, fixture isolation, installed-dispatcher provenance and a defined mock queue boundary (KR-02).
15. **B3-9:** mechanically checkable once the exact session artifacts and validator invocation are supplied; historical execution must not be invented.
16. **Gate 1:** coordination notice plus absent HOLD_MERGES is checkable, but needs release identity and N-467 resume reconciliation.
17. **Gate 2:** producer evidence is potentially checkable; no current PINS source exists, and J-4p cannot be both gated work and a prelaunch completion requirement.
18. **Gate 3:** a clean pinned regeneration is checkable in an isolated checkout at the release commit.
19. **Gate 4:** exhaustive paginated PR metadata plus disposition records is checkable; absence of a label alone does not prove owner/re-entry details.
20. **Gate 5:** **no authoritative source exists today for enumerated coordinator handoff and cessation of the conductor role** (KR-07).
21. **Conductor Setup:** absent directory fails first today; if created exactly as instructed, detached HEAD makes `git pull --ff-only` fail (KR-01).
22. **Startup 1–5:** after those fixes, require the installed bootstrap receipt and instance lock; use absolute runtime paths and a conductor-only handoff.
23. **Wait:** `--wait 1200` polls every three seconds, returns immediately on any unacked message, and returns `[]`/exit 1 only after an empty timeout; it is not a “new messages since this call” subscription.
24. **First tick:** honor STOP/HOLD before launch, distinguish release gating from merge holds, recover existing jobs, and refuse stale-snapshot admission (KR-04, KR-07).
25. **First BUILD:** relative prompt redirection currently fails; after KR-05, bind the item’s actual branch, tests, pins and slot before launching.
26. **Claim/review:** `KY_STREAM=K KY_LANE=b1 ky claim "$ITEM" --worker b1 --lease 10800`; renew from another process is valid because ownership uses worker/claim identity, not PID; review must name the PR and full head.
27. **First VERIFY:** share that branch worktree sequentially under a job lock; reset the verifier’s own slot DB; do not claim the K-owned item as stream V.
28. **Verdict:** `KY_STREAM=V KY_LANE=v1 ky verdict …` is valid; V-owned artifacts require a different author/reviewer identity or a bound external review.
29. **MERGE:** require current acceptance, actual required-check success, correct PR base and no applicable hold; retain protected-window checks.
30. **DONE:** code-only items still need successful `workflow_run` deploy containment; data items need post-deploy acceptance, and both retain strict dependencies/steps/detectors—merge alone is insufficient (KR-04).

**4. Part 3 — Token economy, honestly**

- **Likely improvement:** replacing idle and renewal-only model cycles should materially reduce worker tokens.
- The audit’s addressable scenario is `(1.25B + 0.766B) / 3.13B ≈ 64%` of its historical fleet gross; that is an upper-bound opportunity, not a forecast.
- The cited 197M conflict total overlaps that fleet baseline and cannot simply be added as another independent saving.
- Tokens per **accepted item cannot be estimated credibly** before comparable jobs run: model mix, scope, acceptance denominator and planner investment all change.
- A packet is submitted once per job, but its contents remain in context and are processed on subsequent model calls; an oversized packet can increase every turn’s cost.
- Planner sweeps, repeated A–F after handoff, and Opus reviews opening transitive dependencies can offset smaller worker startup context.
- The wait command itself spends no model tokens while its process blocks; unacked backlog, timeout wakeups or harness background polling can still create model turns.
- Persistent transcripts chiefly add disk retention; the immediate accounting risk is counting both transcripts and result events (KR-12).
- Repeated red CI, same-head evidence rejection, forced liveness jobs and escalation/repacket ping-pong are the largest silent regressions.
- Compare four-class campaign totals—including planning and failed attempts—against unique guarded completions and their retained acceptance scope.

**5. Part 4 — Quality and signal honesty**

- §N.8 risks include five printed gate lines, label-only dispositions, “idle≈0,” render-only report acceptance, and the obsolete shutdown detector (KR-07, KR-11, KR-12).
- The gate and report need failing cases for the precise claims they emit; missing observation must remain WAIT/unknown.
- Literal expanded audit-glob checks against real `owns` produced: **KA-1e matches only through `**/*ephemeris*`; K1-2 matches none; K6-4 matches none**.
- KA-1e’s other sky paths expose the missing repository prefix; K1-2/K6-4 express migrations and workflow edits in prose, so metadata-aware normalization is essential (KR-10).
- Diff-first review is appropriate only while retaining independent item tests, named mutations, compatibility checks, and justified traversal to data producers/consumers.
- Builder-supplied gate output alone is not independent verification, and permanent same-head suppression is not a substitute for evidence-aware deduplication (KR-09).
- Existing briefs already contain stale protected-window instructions pointing into `migrate.ts`/`deploy.yml`; the current mechanism uses `kala_protected_migrations.txt`, demonstrating why hashed excerpts still need contract reconciliation.
- Frozen-contract work remains STOP-and-native under §N.2; frontier routing must never convert that restriction into ordinary Opus implementation.

**6. Part 5 — The prompts as artifacts**

- **Neither is self-sufficient today:** their starting checkout, audit, provisional pins, runtime paths and installed bootstrap artifacts are not consistently reachable.
- Their “read nothing else” wording needs to preserve root CLAUDE.md and the campaign’s valid orientation exception, including its build standards.
- Pairing currently checks only a manually maintained version string; same-version content drift passes, and no card/source hash validator is specified (KR-12).
- Strategy’s 250K-context threshold is not executable by a model without harness telemetry; the plan’s elapsed-time/wakeup alternatives are workable with persisted counters.
- Planner restart omits reading its own handoff; conductor’s broad `HANDOFF_*.md` can select a planner handoff (KR-12).
- Bootstrap “no build/DB write,” blanket control-plane prohibitions and the required test/implementation work contradict one another (KR-02).
- Owner decisions override stale strategy text saying 2+1 capacity, optional xhigh and budget language; the approved version should remove those contradictory operative passages.
- The conductor must explicitly handle tool timeout/background behavior and owner chat interruption; the CLI’s valid wait flag alone proves neither.

**7. What I could not verify, and why**

- I did not independently recompute full-cycle/token totals, historical rejection classes, 29 duplicate verdicts or lead-time distributions: the permitted runtime inspection was bounded, and the historical transcript/log corpus was not reprocessed.
- I verified local model counts, source mechanics, worktree registrations, specification hashes and the permitted digest/hold/event tail. The tail includes N-467 and K-NAK correspondence absent from the earlier summary; K-NAK is not in the 148-item model.
- Current GitHub PR states, coordination-branch release notices, actual deployment/traffic containment, production migration state and Suvarṇa session closure were not freshly established.
- No new dispatcher, gate, launcher or report exists in the inspected installed fleet, so their behavior remains a specification to implement and test.
- I did not verify whether `--bare` skips CLAUDE.md, the interactive harness’s 20-minute wait behavior, or effective model/effort selection.
- No build, database connection, fleet/tracker mutation or file write was performed. No session worktree or scratch artifact was created.

