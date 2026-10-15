---
artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH
version: "2.0"
verdict: REWORK
blocking_count: 3
reviewed_commit: 7f36181b5
review_date: 2026-10-11
review_mode: read-only
---

**(1) Verdict**

**REWORK.** The direction is substantially better, but §17 overstates closure.
Three blockers remain before the planning paste: closure semantics, bootstrap prerequisites, and fixture isolation.
KR-01 is closed; KR-02…KR-12 are partly closed.
The owner’s decisions stand. The replacements below repair execution and evidence contracts without reopening them.

**(2) Part 1 — Closure**

References below: **P** = [plan v2.0](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_0.md), **PP** = [planning prompt](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_PLANNING_PROMPT_v2_0.md), **CP** = [conductor prompt](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_0.md). **T/** denotes `/Users/Dev/kalayantra/tracker_live/pravaha_tracker/`; **F/** denotes `/Users/Dev/kalayantra/fleet_live/`. Replacement references identify the exact text in section 3.

| Finding | Closure | Evidence and conclusion | Exact replacement |
|---|---|---|---|
| KR-01 | **CLOSED** | PP:7–32 now starts in the existing checkout and resolves the audit at `758e0dbb4`; P §5 specifies a named campaign branch tracking `origin/main`. | — |
| KR-02 | **PARTLY** | P §15.D-1 grants authority, but PP:68–80 invokes packets, cards, installation and isolation whose prerequisites remain contradictory or incomplete. | KS-02, KS-03 |
| KR-03 | **PARTLY** | P §0 correctly preserves necessary schema work, but B-0 conflates graph changes with unchanged readiness; `J-4p` still follows unfinished `J-0m`. | KS-01 |
| KR-04 | **PARTLY** | P §6 adds job kinds and completion, but omits executable artifact-authoring, step completion and production pre-acceptance paths. | KS-05, KS-06 |
| KR-05 | **PARTLY** | P §§5/7 improves environment and path discipline, but its launcher cannot find this installation of Claude and its verifier can publish acceptance before its integrity check. | KS-02, KS-06, KS-08 |
| KR-06 | **PARTLY** | P §5 names the required migration, but installed helpers still reject the new topology; **33** Claude/Madhav registrations exceed the ceiling before any new copy. | KS-02, KS-06 |
| KR-07 | **PARTLY** | P §10 supplies an honest WAIT contract, but “five OK before paste” requires the resume record created by that paste. | KS-04 |
| KR-08 | **PARTLY** | P §8 supplies test installation and provenance, but universal release pins/control prohibitions break bootstrap, while universal red-on-current-base breaks legitimate continuation. | KS-02, KS-07 |
| KR-09 | **PARTLY** | P §6 adds evidence-aware review and patch comparison, but Wave 0 and installed `verdicts.py:5–32` still trust merge ancestry; changed heads also need a new review registration. | KS-08 |
| KR-10 | **PARTLY** | P §9 correctly routes the three named examples, but its security paths omit `platform/`, and the referenced FROZEN “list” is not a complete path manifest. | KS-10 |
| KR-11 | **PARTLY** | CP adds steward overrides and counters, but acknowledgment/locking remain defective; P §12 stops its review scheduler and submits the wrong C-3 artifact. | KS-09, KS-11 |
| KR-12 | **PARTLY** | P §13 fixes the accounting policy, but coverage/deduplication acceptance is unspecified, counters are incomplete, and strategy v1.1 retains conflicting operative rules. | KS-11, KS-12 |

**(3) Findings**

**KS-01 — BLOCKING — B-0 does not yet define a reproducible closure or reconciliation test.**

**Location:** P §0:31–43, §14:424,431–441; PP:49–65; `T/state.py:227–282`; model items `J-0`, `J-0m`, `J-4p`, `JOIN-ALL`.

**Defect:** The fields describe dependency and completion mechanics, but do not identify which items establish each retained acceptance; starting from the existing close chain simply pulls the old broad `JOIN-ALL` back into scope. The same-state test ignores detector observations and mixes preservation with deliberate graph changes, while cancelled executable items have no corresponding registered refusal decisions.

**Failure:** Different planners can compute different “critical paths,” a retirement command can be refused, or a valid re-scope can fail its own acceptance; `J-4p` cannot run first.

**Exact replacement — replace P §0’s closure procedure and B-0 acceptance:**

> First commit an acceptance-to-item mapping for goals (i)–(iii), citing each producing brief and detector. Compute prerequisites from those roots; regenerate the mechanical close chain afterwards, rather than using the old close chain as a scope root. `depends_on` supplies item edges; `steps` supplies intra-item obligations, not item IDs; joins use `done_by: join` consistently with `join`; `requires_outcome` supplies decision conditions, with explicit dependencies for unresolved decisions. Preserve `accepts_not_applicable_dependencies` and propagate skipped-input gaps; a skipped prerequisite cannot silently satisfy a retained acceptance.
>
> Split reconciliation into two tests. For path-only migration, compare identical item states using one hashed EVENTS prefix, one captured detector-result map and one fixed clock. For triage, compare against a reviewed expected delta covering dependencies, dispositions, readiness and close membership; preserve earned guarded completions and their evidence.
>
> Register `D-RETIRE-B-K-INBOX` and `D-RETIRE-B-CLAIM-RECOVERY`; map each unfinished item’s `requires_outcome` to `approved`, and stage the owner-authorized `refused` decision for the installation/model-migration action. Tests never publish it to live EVENTS. Use new namespaced IDs for any newly registered relaunch bootstrap work.
>
> Wave 0 first completes the necessary `J-0c → J-0d → J-0 → J-0m` chain, respecting already-earned completions, then `J-4p` after `K0-SV`; pin-consuming work follows `J-4p`.

**KS-02 — BLOCKING — Bootstrap requires artifacts that it produces later.**

**Location:** PP:68–94; P §7:228–238, §8:274–285,306, §14:425–429.

**Defect:** B-1 must use the normal packet and launcher contract before its cards/version manifest exist, with release pins unavailable during the hold and a packet prohibition against its authorized control-plane edits. `install.sh` has no implementation packet, and the displayed launch excludes the installed `/Users/Dev/.local/bin/claude` from PATH and never changes into the assigned worktree.

**Failure:** The first headless B-1 launch fails or operates in the planner’s checkout; an obedient bootstrap builder can also block itself on its own packet.

**Exact replacement — replace the B-1/B-2 prerequisite text:**

> Before creating any copy, complete the capacity inventory and authorized dispositions; the observed 33 registrations do not permit another copy under the ceiling of 15. Preserve dirty and unpushed work.
>
> Before B-1 launches, prepare and independently review the BOOTSTRAP card, fixture builder/verifier cards, bootstrap packet schema and bootstrap version manifest. A bootstrap packet uses source/specification pins, explicitly marks release pins `not_applicable: bootstrap`, and permits only its enumerated D-1 control-plane source paths. Its tests and review run independently of the not-yet-built dispatcher.
>
> Resolve and record an absolute `CLAUDE_BIN` before environment scrubbing, assert it is executable, and launch it with `cwd` set to the assigned bootstrap worktree. On this host the resolved binary is `/Users/Dev/.local/bin/claude`. The remaining scrubbed-environment and MCP restrictions still apply.
>
> Add implementation packets for `install.sh`, tracker semantic changes, allocation, and all modified runtime helpers. Each packet names its command, expected result and negative cases. B-2 installs only independently reviewed, owner-merged source, including the approved plan, prompts, required cards and version manifest. Record installed hashes and the running tracker’s loaded revision; prove the old supervisor/sweep cannot continue dispatching.
>
> B-3 uses that installed, version-checked fixture bundle. B-4 completes campaign packets and coverage; any subsequent card/script change requires a new reviewed installation receipt before launch.

**KS-03 — BLOCKING — `PRAVAHA_EVENTS` plus `--mock-merge` does not isolate B-3.**

**Location:** P §14:427; PP:43–44; `/Users/Dev/kalayantra/bin/ky:3–9`; `T/cli.py:57–81,215–245`; `T/server.py:51–77`.

**Defect:** The installed wrapper overwrites the supplied EVENTS setting, and even an override-preserving wrapper would still use live HOME-derived snapshots and the live HTTP tracker unless the other settings change. Mocking merge submission does not mock BUILD’s push/PR creation or isolate executor requests.

**Failure:** A supposedly isolated rehearsal can append live events, consume live readiness/detectors, or create a real PR.

**Exact replacement — replace B-3’s isolation contract:**

> `PRAVAHA_EVENTS` is a JSONL file path, not a directory. The fixture wrapper preserves validated overrides for `PRAVAHA_HOME`, `PRAVAHA_EVENTS`, `PRAVAHA_PLAN_MODEL`, `PRAVAHA_REPO`, `PRAVAHA_HOLD`, `PRAVAHA_URL` and `PRAVAHA_TRACKER_PORT`; the scrubbed launcher forwards that exact fixture configuration.
>
> Start a second tracker on a reserved unused loopback port, with its HOME, model, EVENTS, claims, snapshots and backups entirely below the dated scratch root. Do not reuse port 8767. Remove production DB configuration and admit only fixture-local detectors; disabling background detector polling alone is insufficient because `/api/verify` performs verification.
>
> Replace `--mock-merge` with a fixture backend covering Git pushes, PR creation/read/checks/merge, deploy observations and executor submission. Use local fixture remotes; deny production executor and credential access. Exercise the real CLI, claim, verdict and typed completion paths against the fixture tracker.
>
> Acceptance requires unchanged live EVENTS size/hash, no fixture connection to the live tracker, zero external PR/queue/production requests, expected fixture transitions, and cleanup of the fixture server, databases and worktrees.

**KS-04 — HIGH — The release/resume gate is circular and insufficiently bound.**

**Location:** P §10:344–359, §11:371–372, §16:476–478; CP:5,34–40.

**Defect:** The owner is told to wait for five OK before pasting, although condition 1 requires the resume file created by that paste; P §11 additionally places creation after the gate. File existence does not bind an old resume or mixed release evidence to the current launch.

**Failure:** A correct first launch is impossible, or a stale resume file makes a later launch appear authorized.

**Exact replacement — replace P §10’s admission preamble, §11’s resume ordering and both owner launch instructions:**

> `kygate.sh --pre-resume` validates the five release conditions and reports `READY_TO_PASTE` only when the sole missing launch authorization is the N-467 resume record. This mode authorizes no campaign job.
>
> The release receipt has one `release_id`, schema version and digest; every condition binds evidence to that release. Certification identifies its coordination commit/record; pins identify their rebuild producer/run; regeneration identifies main commit, generator version and output digest; PR dispositions come from an exhausted paginated API traversal; coordinator closure identifies SS’s enumerated handoffs. Missing or inconsistent evidence is WAIT.
>
> Paste the conductor after Wave B installation and `READY_TO_PASTE`. After version validation and exclusive instance acquisition, it writes `OWNER_RESUME.json` binding N-467, the release-receipt digest, approved bundle digest, session and timestamp, then runs the full gate. This is the D-3 owner act; no additional resume approval is required.
>
> The recorded certification-hold owner releases `HOLD_MERGES` when its documented certification condition is met. The conductor does not remove unrelated holds. STOP and global HOLD dominate bootstrap and campaign admission; HOLD_MERGES blocks every queue submission. Negative fixtures include stale resume, mixed release IDs and every surviving hold.

**KS-05 — HIGH — Job names still do not cover the actual lifecycle.**

**Location:** P §6:189–205; `T/completion.py:41–60`; `T/events.py:158–166`; `F/executor.py:237–276`; `executor_ops.json`; model `J-0c`, `J-0d`, `K9-23`.

**Defect:** K-owned artifact work is forced into a PR-only BUILD exit, required `steps` lack a completion producer, and OPERATION lacks request preparation and the executor’s required pre-acceptance producer. Protected-window dispatch is not an existing executor kind, while K9-23’s required table edit falls under the campaign control-plane prohibition.

**Failure:** Early artifacts and later production work stall despite all listed job kinds existing; a V-owned artifact may also be refused for lacking a recorded independent author.

**Exact replacement — add to P §6 and B-1:**

> Every retained executable item declares `completion_kind: code|artifact|packet|operation`, its producer, reviewer, detector and required step evidence. BUILD supports K-owned artifact production: register its path/digest through `ky review`, then schedule independent ARTIFACT review. Record each required `ky step` only after its named detector passes.
>
> Artifact authors claim only items owned by their stream and record author identity before review. Reviewers use separate job locks and a distinct identity; S-owned artifacts do not receive V item claims. COMPLETE uses K for K items, S for S items, and S for independently accepted N/V items.
>
> Add REQUEST-PREP for ready N-owned operations, PRE-ACCEPT by an independent V job, deterministic EXECUTE, and POST-READBACK/QUIESCENCE acceptance. Requests bind the reviewed merged script, request digest, lease, expiry and applicable backup/restore/dry-run evidence required by `executor.py`; requesters must match the approved operation table. GitHub protected-window dispatch remains a separate owner-approved workflow action.
>
> Move K9-23’s executor-table changes into a reviewed Wave B packet. Operations remain disabled until their merged implementation and exact qualification receipts satisfy that approved policy; campaign builders produce implementation and qualification evidence, never edit installed controls.
>
> On adoption, reconcile legacy claims, PRs and checkpoints into job state. Renew only jobs holding claims; serialize all author/reviewer access to an item worktree under one item lock.

**KS-06 — HIGH — Runtime admission still lacks a complete base, allocator and topology contract.**

**Location:** P §§5–8; `T/state.py:227–243`; `F/local_db.sh`, `preflight.sh`, `precheck.sh:90–116`, `executor.py:318–330`.

**Defect:** `base_sha` is unnamed provenance even though the tracker can mark dependants ready on accepted-but-unmerged prerequisites, and the allocator is referenced without an implementation or shared reservation contract. Existing helpers still encode old slots/paths, while the proposed scratch path lacks the owner-required date and job streams still go under `run/`.

**Failure:** A builder starts without its prerequisite code, migration numbers collide, or the first new slot/preflight/test invocation fails.

**Exact replacement — add to P §§5–7 and B-1 acceptance:**

> For each job record an absolute worktree, branch, `base_sha`, prerequisite heads and test digests. A BUILD is runnable only when its base contains the required accepted prerequisite heads; reuse a valid existing stack/checkpoint, otherwise wait for those heads to reach main. Tracker readiness alone does not prove code availability.
>
> Implement allocation as an atomic, persistent reservation keyed by item/branch against the repository-wide migration namespace and active reservations. All concurrent migration writers must observe the same reservation authority; until that is established, retain the existing reservation procedure. Test concurrent allocation, restart/reuse and a conflicting external reservation.
>
> Use `/Users/Dev/scratch.noindex/claude/madhav/<YYYYMMDD>-kalayantra-v3/` for new temporary files, logs and DB storage. Store their absolute paths in persistent job records. Adopt the registry-inclusive seed with mandatory schema/ledger/registry hashes; support b1–b6/v1–v4 throughout DB guards, preflight, model worktree and branch authorization, executor and cleanup.
>
> Launch with an explicit worktree cwd and absolute Claude executable; pass `--effort "$EFFORT"` with xhigh for PLAN and high for other specified roles. Make precheck fixture-aware through `KY_RUN`; write the manifest it actually consumes, or pass newline-delimited test paths in `TESTS`, not the manifest filename. Acceptance exercises every configured slot, reset isolation, missing-registry/1320 failure and cleanup.

**KS-07 — HIGH — Packet validity conflates original failure, current readiness and future schema.**

**Location:** P §8:268–305; PP:83–90; `T/completion.py:20–23`.

**Defect:** Requiring every test to fail on every job’s current base rejects valid REWORK, already-implemented inherited work and artifact checks. Requiring only currently real columns can also prevent the schema-prerequisite packet from describing the columns it must introduce.

**Failure:** Correct work is blocked as `test_not_red`, or builders receive an incomplete before/after contract and misleading production classification.

**Exact replacement — replace P §8’s schema/test admission rules:**

> A feature packet records the immutable original failing base, exact test digests and observed failing assertion. At job admission, install missing tests idempotently and classify the current result: expected-red permits new implementation; already-green triggers an independent already-satisfied assessment, not automatic rejection or completion. REWORK and inherited accepted heads retain their evidence history and run the relevant regression checks.
>
> Artifact and operational packets use explicit semantic acceptance and negative fixtures; they need not invent a red feature test. Schema-prerequisite packets declare both the admitted existing schema and the intended additive contract. Consumers wait for that prerequisite’s verified schema receipt.
>
> Populate `brief.migration` and `brief.op` consistently with the tracker’s `writes_data` classifier; `migration_class` alone is not its input. Normalize classification values rather than treating prose or the string `NONE` as truthy production metadata.
>
> Define `packet_sha256` over canonical packet content excluding that field. Validate test availability, source excerpts and the reconciliation claim against their pinned sources. Missing tests, stale contracts or unproven prerequisites fail admission with the specific reason.

**KS-08 — HIGH — Acceptance can escape its boundary or survive an unreviewed change.**

**Location:** P §6:191–194, §7:250–254, §14:432–433; `T/verdicts.py:5–60`; `T/completion.py:63–94`.

**Defect:** VERIFY publishes `ky verdict` before checking source integrity, but the CLI has no “void” operation and same-user chmod is not an enforced Bash write boundary. The installed inheritance function checks ancestry rather than merge-resolution content, and Wave 0 explicitly exempts merge-only head movement without applying the stronger patch proof.

**Failure:** MERGE can observe a premature acceptance, substantive conflict resolution can inherit acceptance, or `ky done` rejects a regenerated head absent from the latest review event.

**Exact replacement — replace VERIFY/inheritance publication rules:**

> The verifier writes a proposed result only. It independently runs the packet’s applicable tests, named mutations and compatibility checks; builder results are inputs, not substitutes. The launcher enforces a read-only source/Git-metadata boundary, with writes limited to declared evidence, caches, temporary files and the slot DB. Acceptance fixtures attempt Bash edits, chmod/replace, Git-index changes and shared-control writes.
>
> After the verifier exits, the controller checks exit status, reviewed HEAD, clean status, tracked hashes and boundary evidence; only then may it publish the V verdict. A boundary failure never publishes ACCEPTED. If previously published acceptance is invalidated, append an explicit rejection before any queue action.
>
> Use one inheritance predicate in dispatcher and tracker: bind old/new heads, their exact base commits and reviewed patch comparison; ancestry alone is insufficient. Any substantive resolution or unproven difference requires review of the new head. Apply this to all inherited Wave 0 heads.
>
> After every head change, register `ky review <ID> --detail "PR #<n> @ <new-head>"` under the owning stream. Queue only that checked head, using a head-match guard. Complete with the final PR head as `--reviewed-head`; use the squash merge commit for deployment containment and post-deploy verdicts. Retain required branch/ref evidence until guarded completion.

**KS-09 — HIGH — Finalization stops its reviewer and submits the wrong artifact.**

**Location:** P §12:390–398; model `C-3`/`C-4`; `T/cli.py:242–245`.

**Defect:** Stopping the dispatcher removes the producer of the subsequent ARTIFACT review jobs, and requiring every job to be absent before those jobs run makes the sequence circular. C-3’s detector requires `DRAIN_RECEIPT.json`, not `FINAL_REVIEW.json`, while session IDs are not reliably observable in a `pgrep "claude -p"` command line.

**Failure:** Close deadlocks or its first typed C-3 completion is refused.

**Exact replacement — replace P §12:**

> Finalization runs outside the ordinary dispatcher. Stop new admissions, drain or terminate recorded job groups within their deadlines, preserve dirty/unpushed work, and verify process identity using recorded PID/PGID plus process-start identity.
>
> Write `$KY_RUN/DRAIN_RECEIPT.json` from measured drain facts. A finalizer-owned, bounded independent reviewer accepts its exact digest; after that reviewer exits, the S finalizer executes `KY_STREAM=S ky done C-3 --artifact-path "$KY_RUN/DRAIN_RECEIPT.json"`.
>
> Remove eligible owned item worktrees and session DBs, then write `$KY_RUN/FINAL_RECEIPT.json`, binding the accepted drain digest, close-report evidence and physical-absence observations. Run one bounded independent close review outside ordinary dispatch, using a bound external review where the V-owned item requires it.
>
> After that reviewer exits, independently recheck process, worktree and DB absence. Publish its digest-bound verdict only if the receipt remains valid and unchanged, then execute `KY_STREAM=S ky done C-4 --artifact-path "$KY_RUN/FINAL_RECEIPT.json"`. Keep the tracker available through completion. Any survivor, changed receipt, missing close claim or failed cleanup prevents acceptance.

**KS-10 — HIGH — Essential checks are incompletely carried across the governance cut.**

**Location:** P §3:93–117, §9:323–328, B-4:428; `.github/workflows/ci.yml:299–302`; `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §§1–2.

**Defect:** The retained CI list omits the dedicated Kāla DB job, card coverage excludes §I, and repository-relative security rules still use component-relative paths. The claimed FROZEN path list is incomplete, while the periodic claim fixture is said to prove DB/worktree health that it does not inspect.

**Failure:** A green campaign can miss a material test or doctrine obligation; security changes can route incorrectly, and liveness can report unsupported health.

**Exact replacement — replace those retained rules and delete the LIVENESS row:**

> Keep applicable item tests, mutations and compatibility checks, required CI, and `Kāla DB Tests (throwaway Postgres)` for relevant code changes; absent, skipped or failed required DB evidence is not success. Preserve the semantic acceptance obligations of retained items, including Gochara endpoint completeness and actual teardown where required.
>
> COVERAGE maps every applicable MUST from root §I and §N, charter §0 and retained acceptance contracts to a card, packet clause or executable check. The 300-token summary cannot substitute for omitted binding rules.
>
> Replace the security globs with `platform/src/proxy.ts`, `platform/src/lib/{auth,security,share,limits,mcp}/**`, and `platform/src/app/api/{auth,admin,db}/**`; use `platform/scripts/governance/pravaha_tracker/**` for tracker source. Share one explicit frozen-path manifest with precheck, including the existing `asset_runner.py`, `runner.py`, `staleness.py` and `writers/__init__.py` prohibitions. New conforming writers remain permitted; frozen changes STOP for native authorization.
>
> Delete the every-two-hours LIVENESS job and its claimed DB/worktree proof. Check tracker freshness, assigned worktree and disposable DB at job admission; test claim renewal/recovery during bootstrap. Retain one independent card-coverage review; delete the additional “ADHIKĀRIN/native sign-off” wording from B-4.

**KS-11 — HIGH — Prompt pairing, locks and handoffs remain partly declarative.**

**Location:** PP:22–24,92–105; CP:29–53,66,84–90; P:11, §11; strategy v1.1:57,69,98–104,112–124,154–163.

**Defect:** File hashes cannot attest the pasted prompt’s bytes, check-then-write locks are racy, and counters are neither fully initialized nor incremented on every return. Generic `ky ack` does not acknowledge the steward inbox, while strategy v1.1 still prescribes rebasing, weaker verdict deduplication, frozen-file routing and obsolete budget/liveness language.

**Failure:** Duplicate conductors or repeated steward messages consume work, handoffs fail to bound sessions, or a fresh session follows conflicting instructions.

**Exact replacement — replace prompt startup/handoff mechanics and strategy authority:**

> Root bootstrap reading precedes the prompt’s restricted reading order. Each paste names the approved manifest digest and loads its authoritative instructions from the verified file; `kyversion.sh` verifies file pairing and installed hashes, not clipboard authenticity.
>
> Use an atomic instance-acquisition helper with session identity and process-start identity; do not use a transient tool-shell PID as the conductor identity. The same helper idempotently starts the dispatcher with detached stdin and managed logs; delete “ask the owner once,” because the approved conductor paste already authorizes startup.
>
> Initialize persistent planner/conductor state on first entry. Increment conductor wakeups after every wait return, including nonempty returns, and check both elapsed time and handoff thresholds before waiting again. Persist the planner’s completed-step IDs, evidence hashes, tool-heavy-turn counter and start time; resume validated incomplete steps only.
>
> Acknowledge S messages with `ky ack <id>` and steward messages with `ky ack <id> --steward`, after action or durable deferral. Record provider session IDs when observed; do not invent them before launch.
>
> Replace strategy §§2–4’s operative instructions with: “Historical rationale only. Execution, routing, review, regeneration, measurement and handoff rules are exclusively those of the approved relaunch plan and paired prompts.” Preserve the owner decisions and historical evidence.

**KS-12 — MEDIUM — Measurement policy needs acceptance tests before it earns its claims.**

**Location:** P §13:402–415, B-1:425; PP:110–111; `notes_ky_state.md:38,197`; audit §4/§7.

**Defect:** “One row per job” does not specify parent/subagent usage coverage, duplicate stream results, transcript fallback reconciliation or inherited/composite completion denominators. The referenced baseline script is absent from the pinned audit checkout, and failure counters can be reset by repacketization unless their identity is persistent.

**Failure:** The report can silently overcount savings, undercount coordinator work, or hide repeated paid attempts.

**Exact replacement — replace measurement acceptance and failure accounting:**

> Import the reviewed baseline implementation from its recorded scratch source into a merged repository path before reporting measured v3 totals. No missing source or coverage becomes zero.
>
> Define accounting ownership for every provider session and child session. Deduplicate repeated result events; use transcript usage only for uncovered calls; prove whether parent usage includes children before adding child totals. Fixtures cover normal completion, duplicate results, killed jobs, parent/child sessions, interactive planner/conductor sessions, bootstrap jobs and missing records.
>
> Report distinct guarded-completed item IDs separately from decision completions, joins, accepted heads and weighted progress, with an explicit scope denominator and observation boundary. The historical 46 includes 39 guarded completions, one join and six decisions; it is not 46 guarded completions.
>
> Persist failure-class fingerprints and attempt counts across retries, escalation, restart and repacketization. The third identical failure blocks further automatic attempts until a recorded changed condition permits retry. Parse structured quota errors as well as terminal log text. On frontier rerouting, preserve the existing diff for Opus assessment instead of discarding useful work.
>
> Savings and throughput remain “cannot be estimated” until comparable completed work and reconciled four-class usage exist.

**(4) Parts 2–6**

**Part 2 — Launch walkthrough**

1. **PP steps 1–4:** The checkout, review and pinned audit resolve. Root bootstrap must precede “nothing else”; handoff state must be checked against the approved bundle.
2. **PP step 5:** `kybrief` resolves the live model. `verify_specs.sh` writes `SPEC_HASHES_OK`; it is not a read-only verification command, so I inspected/hash-checked its inputs instead.
3. **First under-specified instruction:** B-0’s closure computation, PP:52–61; fields alone do not identify acceptance roots or define the intended semantic delta (**KS-01**).
4. **B-0 semantics:** `steps` are local obligations; `join` is not an edge; `requires_outcome` does not itself wait for an unresolved decision; skip acceptance changes terminal propagation.
5. **Fixed-boundary equivalence:** Testable with frozen EVENTS, detector observations and clock, separating path preservation from reviewed scope changes. EVENTS alone is insufficient.
6. **B-1:** Components are implementable, but not all have sufficient acceptance contracts; installer, allocator and tracker changes need explicit packets, while metering/version checks need negative fixtures.
7. **First definite shell failure:** P §7’s `env -i … claude …` cannot find the installed binary with its specified PATH; missing cwd is the next defect (**KS-02**).
8. **B-2:** A hash-bound installation receipt is achievable after reviewed implementation; file-copy hashes alone do not establish which tracker revision the running server loaded.
9. **B-3:** `PRAVAHA_EVENTS` alone does not isolate. The existing HTTP-based path needs a separate fixture tracker/port and full configuration; merge-only mocking is insufficient (**KS-03**).
10. **B-4/B-5:** Cards, semantic coverage, governance validation and version manifest are achievable, but prerequisites must be prepared before the jobs that consume them.
11. **Gate:** The receipt approach is sound after epoch/content binding and removal of the paste circularity; condition 5 still lacks its authoritative published handoff source (**KS-04**).
12. **Setup/startup 1–3:** Named tracking branch fixes `git pull`; approved bundle availability, installed-runtime verification and atomic locking remain required.
13. **Startup 4–6:** CP places resume before gate correctly, unlike P §11; owner instructions still demand the impossible pre-paste five OK.
14. **Startup 7–9:** Background startup is authorized by the paste; remove the extra approval question, detach stdin, reconcile both inboxes with the correct acknowledger (**KS-11**).
15. **Wait:** `--wait 540` fits the stated 600,000-ms tool limit. Nonempty returns currently bypass counter increments.
16. **First tick:** STOP/global HOLD precedence is right; freshness must be proved because `ky next` can fall back to a stale snapshot, and bounded tail reading alone cannot reconstruct all verdict identities.
17. **First BUILD:** `KY_STREAM=K KY_LANE=b1 ky claim … --worker b1 --lease 10800` is supported; actual worktree capacity, prerequisite-containing base, slot installation and allocation are not yet satisfied.
18. **First scheduled work:** `J-4p` cannot be first under its existing dependencies; J-0c/J-0d also need artifact-producing BUILD exits (**KS-01/05**).
19. **`ky review`:** Valid for a K actor; every changed PR head must be registered explicitly.
20. **VERIFY:** No K item claim is correct; a separate job lock is necessary, plus an item-wide lock preventing concurrent worktree mutation.
21. **`KY_STREAM=V KY_LANE=v1 ky verdict`:** Valid for a K-owned item, but must follow successful integrity checks; “void afterwards” is not a CLI operation (**KS-08**).
22. **MERGE:** **Squash is compatible.** Completion compares `--reviewed-head` with GitHub’s final PR head; deployment/post-deploy uses `mergeCommit.oid`, the squash commit.
23. **Inheritance:** Squash does not justify merge-only inheritance; substantive resolution can pass today’s ancestry test, and inherited acceptance does not refresh the latest `ky review` registration.
24. **COMPLETE:** Typed guards enforce strict dependencies, steps and detector success; code-only items also require a successful deployment containing the merge, not merely MERGED.
25. **POST-DEPLOY:** Writes-data items need the exact merge-SHA verdict after executor readback; pre-acceptance/request preparation is currently missing, so this path stalls (**KS-05**).
26. **Close:** The current first C-3 command supplies the wrong path; stopping the dispatcher also prevents its planned final review jobs (**KS-09**).

**Part 3 — Essential governance and security**

- Cutting idle model cycles, standing specialists, ledger PRs, repeated whole-document reads and per-cycle ceremony is justified.
- Removing reservation ceremony is safe only when migration allocation and shared-file ownership waits have working replacements; “typed block” does not reserve either resource (**KS-05/06**).
- Production request-bound pre-acceptance, backup/restore/dry-run requirements and quiescence are essential; “executor unchanged” preserves refusal but does not produce the evidence it requires.
- Retain applicable Kāla DB CI and the semantic acceptance obligations behind the Gochara seal; ordinary required checks cannot substitute for them (**KS-10**).
- The periodic claim-only LIVENESS job is retained ceremony with an overstated detector. Its exact deletion and replacement are in **KS-10**.
- Independent coverage review is useful; the additional unspecified ADHIKĀRIN/native card sign-off adds no distinct detector.
- P §3 does **not expressly authorize** violating root §I/§N or the FROZEN contract. The risk is incomplete transfer into cards, routing and checks—not the authorized retirement of old operating prose.
- Same-user chmod plus `bypassPermissions` is not a security boundary; acceptance must not rely on that claim (**KS-08**).

**Part 4 — Token economy**

| Regression | v2.0 judgment |
|---|---|
| Packet re-sent per turn | Bounded per job, not eliminated: packet/history remains model context, potentially charged as cache reads on later turns. |
| Opus verifier traversal | Diff-first intent and caps help; independent tests and bounded necessary exploration must replace broad rediscovery, not verification itself. |
| Planner sweeps | Wave/repacket triggers improve this; completed-step/hash checkpoints are still needed. |
| Repeating A–F after handoff | Own-role handoff helps; executable checkpoint validation is missing (**KS-11**). |
| Forced liveness | No longer an LLM job; its claimed detector remains wrong and unnecessary (**KS-10**). |
| Escalation ping-pong | Better bounded intent; counters must survive repacketization, and discarding Sonnet work wastes useful output (**KS-12**). |
| Transcript double counting | Correct policy, insufficient acceptance coverage for result/transcript/child overlap (**KS-12**). |

Additional spend can hide in bootstrap implementation, repeated invalid packet admission, missing prerequisite bases, stale-snapshot scheduling, repeated steward messages, quota failures outside “last lines,” and planner/conductor subagents.  
No defensible saving percentage follows from this design alone; the audit’s 64% remains an upper bound on addressable historical classes, not a v3 forecast.  
**Expected total cost and cost per guarded completion: cannot be estimated from current evidence.**

**Part 5 — Quality and signal honesty**

- **Gate lines:** Five plausible fields are insufficient without release identity, producer evidence and negative cases; missing condition 5 correctly remains WAIT (**KS-04**).
- **Dispositions:** A complete, independently accepted inventory is necessary; a disposition proposal does not itself merge, close or terminally retire an item (**KS-01/05**).
- **Progress:** `46/148 = 31.1%` is corrected, but 46 is not the guarded-completion count. Weighted progress and accepted heads remain separate measures (**KS-12**).
- **Report acceptance:** Result/transcript reconciliation, missing coverage, child attribution and denominator fixtures must precede savings claims.
- **Finalizer:** A matching `ACCEPTED` string or digest is insufficient without the reviewed close claims and fresh physical-absence evidence (**KS-09**).
- **Verifier bar:** Diff-first plus independent item tests, named mutations and compatibility checks is appropriate; the builder’s supplied results alone are inadequate.
- **Evidence-aware re-review:** Appropriate, but requires durable fingerprints, complete verdict history and one shared acceptance predicate (**KS-08**).
- **KA-1e:** Static application of §9 routes it to Opus through actual `platform/python-sidecar/services/kala_core/sky/...` ownership.
- **K1-2:** Routes to Opus through migration metadata/prose and migration-related owned paths.
- **K6-4:** Likewise routes to Opus; the unresolved additive-migration wording is conservatively sufficient.
- **Remaining routing defect:** Real `platform/src/...` security files miss the printed `src/...` rules.
- **Builder misinformation risks:** Unavailable release pins, stale schema excerpts, blanket control-plane prohibition, unconditional red-on-current-base, and migration-class metadata that does not populate the tracker’s classifier (**KS-02/07**).

**Part 6 — Prompts as artifacts**

- The planning entrypoint and audit pin are now usable by a fresh session.
- The pair is not yet self-sufficient: bootstrap artifacts arrive too late, runtime installation is underspecified, and plan/prompt gate ordering conflicts.
- `kyversion.sh` can enforce hashes of files and installed components; it cannot prove which bytes the owner pasted without a defined verified-loader contract (**KS-11**).
- Planning handoff lacks persisted counters/checkpoint identity; conductor handoff initializes neither state nor all-return counting.
- Check-then-write PID files do not enforce exclusive instances; a transient tool-shell PID is especially unsuitable.
- Steward inbox acknowledgment requires `--steward`; the generic acknowledgment can leave messages perpetually unread.
- `--wait 540` is within the supplied harness limit; no unsupported CLI fact is needed to reject it.
- Background dispatch is feasible, but survival across tool/session completion must be rehearsed with detached stdin and a managed process identity.
- Chat commands can be handled by the interactive session at its next wake; they do not automatically become tracker messages.
- Root authority remains binding before the restricted read order; cards must carry applicable §I as well as §N requirements.
- Strategy v1.1 still conflicts on rebasing, frozen-file routing, verdict deduplication, escalation and budget/liveness wording (**KS-11**).
- The headless PLAN launch currently hardcodes high despite the accepted xhigh decision; use role-specific effort (**KS-06**).

**(5) What I could not verify and why**

- I verified the exact review commit and a clean review worktree. The required capacity command returned **33** registrations.
- I ran no build, database connection, tracker mutation, fleet launch, installation or file write.
- Consequently, CLI authentication, `--bare` CLAUDE.md loading, detached-process survival, slot seeding, fixture isolation and shutdown remain acceptance work—not observed passes.
- I did not refresh remote PR/check/deployment state or establish production-schema freshness; historical receipts and bounded runtime messages are not current production proof.
- The requested EVENTS tail cannot prove the entire verdict/decision history. Conclusions about tracker behavior come from its source, not an unbounded log read.
- The v3 scripts and release/install/resume receipts do not yet exist locally; their absence is expected implementation work, while the contradictions above are defects in the instructions meant to produce them.
- No review-created resources require cleanup.

