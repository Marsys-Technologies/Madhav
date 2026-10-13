---
artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH
version: "2.2"
verdict: PROCEED-WITH-FIXES
blocking_count: 0
reviewed_commit: 9c663da08
review_date: 2026-10-11
review_mode: read-only
---

**1. Verdict**

The owner may approve source commit `9c663da0814b8d6854210a3e82bee45d6132287b` and paste the planning prompt, provided KU-01…KU-03 enter the independently reviewed B-0c deliverables before any job runs.
All eight KT replacements are present; neither paste anchor needs changing.
The conductor paste remains conditional on measured final Wave B acceptance, all five release conditions and `READY_TO_PASTE`.
Those conditions are **not established today**: the final v3 manifest/receipts are absent and the certification hold remains.

**2. Part 1 — Closure**

References: **P** = [plan v2.2](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_2.md); **PP** = [planning prompt](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_PLANNING_PROMPT_v2_2.md); **CP** = [conductor prompt](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_2.md). Line numbers below refer to those files. CLOSED means the reviewed specification closes the finding; implementation acceptance remains Wave B’s responsibility.

| Finding | Status | Evidence and conclusion |
|---|---|---|
| KT-01 | CLOSED | P:11–29; PP:17–32; CP:23–39: source-commit and final-manifest anchors are non-circular, and conductor checkout mutation follows verification and locking. |
| KT-02 | CLOSED | P:320–329, 520–521; PP:83–102: staged MCP configuration, validated inputs and direct planner supervision remove dependency on unfinished launch machinery. |
| KT-03 | CLOSED | P:26–29, 434–451, 522–525; PP:104–127: bootstrap verification cannot authorize campaign admission, and final acceptance binds rehearsal, coverage and governance evidence. |
| KT-04 | CLOSED | P:193–200, 246: prerequisite containment recognizes verified squash mappings, while merge authorization is bound to the registered head. |
| KT-05 | CLOSED | P:251: operation readback exits through receipt/digest acceptance, while data-writing code requires the deployed merge-commit verdict. |
| KT-06 | CLOSED | P:461–467, 594; PP:34–42; CP:40–44: session rollover resets session counters while preserving validated campaign state and failure history. |
| KT-07 | CLOSED | P:263–272: terminal claim release follows process termination, checks the persisted claim identity and serializes against slot reuse. |
| KT-08 | CLOSED | P:172–179, 303–314; CP:53–54: job I/O and dispatcher logs use recorded scratch paths rather than durable control-state storage. |
| KS-02 | PARTLY | P:211–213, 521–522 omit the reused audit’s incompatible completion rule; apply KU-01’s exact B-0c replacement. |
| KS-06 | PARTLY | P:167–179, 206–210 do not specify acceptance for the reused helper’s physical DB storage and session cleanup; apply KU-02’s exact replacement. |
| KS-01, KS-03…05, KS-07…12 | CLOSED | P §0, §§3–14 and the paired prompts retain their adopted closure, isolation, gate, lifecycle, quality, security, finalisation and accounting requirements. |

The KS-02/KS-06 qualifications correct missed reuse defects in my earlier closure; they are not reversals introduced by the KT edits. No other KS regression was found.

**3. Findings**

**KU-01 — HIGH before conductor paste: audit disagrees with typed completion**

**Location:** P:211–213, 521–522; installed [preflight.sh:36](/Users/Dev/kalayantra/fleet_live/preflight.sh:36); [audit.py:114](/Users/Dev/kalayantra/tracker_live/pravaha_tracker/audit.py:114), particularly 123–124 and 155–157; [completion.py:81](/Users/Dev/kalayantra/tracker_live/pravaha_tracker/completion.py:81).

**Defect:** Audit unconditionally demands `post_deploy` acceptance for code completions carrying a merge commit, whereas guarded completion requires it for data-writing code and uses deployment containment for code-only work. Read-only evaluation found nine code-only completions flagged for missing `post_deploy`, and B-1 does not explicitly require repairing this disagreement.

**Failure:** Retaining this check makes B-2’s `preflight.sh launch → ky audit --since kickoff` fail even after claim reconciliation; deleting the check would conceal real defects.

**Exact replacement — B-0c tracker/preflight implementation packet:**

> Audit and guarded completion shall share the same normalized, typed evidence requirements. Data-writing code requires ACCEPTED post_deploy evidence at the observed squash merge commit. Code-only completion requires verified successful deployment containment of its mapped merge commit, without inventing a post_deploy obligation. Artifact and operation completion retain their digest-bound acceptance requirements. Apply the shared reviewed-patch inheritance predicate wherever reviewed-head validity is evaluated.
>
> Acceptance fixtures shall prove: valid code-only completion without post_deploy passes; missing deployment containment fails; data-writing completion with missing or wrong-commit post_deploy evidence fails; invalid inheritance fails. Reconcile remaining legacy claim/verdict findings explicitly before B-2 preflight acceptance. Do not fabricate verdicts, rewrite historical events or suppress unresolved findings.

**KU-02 — HIGH before conductor paste: DB storage and cleanup lack executable acceptance**

**Location:** P:167–179, 206–210, 482; repository [local_db.sh:18](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/fleet/local_db.sh:18), especially 23 and 106; owner policy rules 5–6.

**Defect:** The reused helper starts Postgres without a scratch-root PGDATA bind mount and its `down` action explicitly keeps the container. The plan requires slot/seed changes and eventual cleanup, but does not require proof that physical database storage and session-close behavior satisfy the owner’s policy.

**Failure:** A successful slot test or cleanup receipt can coexist with database storage outside `scratch.noindex` or test databases surviving their originating session.

**Exact replacement — B-0c DB, lock/handoff and cleanup implementation packets:**

> Every v3 test database shall record its originating session and use PostgreSQL data storage explicitly bind-mounted beneath that session’s dated KY_SCRATCH realpath. Record container identity, mount source, database ownership and seed hashes in its receipt; reject an anonymous volume, an out-of-root mount or an ownership mismatch. Preserve incompatible pre-existing containers and report them; do not repurpose or delete them automatically.
>
> Before the originating planner or conductor session closes, including handoff, stop relevant admissions, drain or terminate its test processes while preserving work, remove its test databases and owned storage, and verify physical absence. Remove a container only when session ownership permits it and no foreign database remains. Enforce this through the session-close/lock-release path as well as finalisation. Test wrong mounts, stale READY receipts, ownership conflicts and stop-without-removal. A later session recreates required databases from an admitted seed.

**KU-03 — LOW: generated-file names disagree**

**Location:** P:49, 58, 518 versus PP:68, 75.

**Defect:** The plan names `_v2_1` disposition, acceptance-root and closure outputs, while the prompt names `_v2_2` outputs. Without an explicit binding, two independently edited files can appear to satisfy different halves of the same bootstrap.

**Failure:** Reviews or manifests can bind one set while reconciliation consumes the other.

**Exact replacement — B-0c generated-output binding template:**

> For WORKTREE_DISPOSITIONS, ACCEPTANCE_ROOTS and CLOSURE, use the plan’s named paths as canonical. Materialize the paired prompt’s differently named outputs as compatibility copies containing exactly the same reviewed bytes; retain content version 2.2. Record both absolute paths, the canonical role and their common SHA-256 in VERSIONS.bootstrap.json. Consumers use the canonical path; version checks verify both copies. Missing or unequal copies refuse bootstrap acceptance. Neither copy may be edited independently.

These replacements belong in generated B-0c templates/packets and their independent review. They require no modification of the approved plan, prompts or paste anchors.

**4. Part 2 — Launch walk**

1. **Planning anchor:** the full commit exists; all four reviewed files match its blobs byte-for-byte, and the specified `git cat-file -e`/`git diff --quiet` checks pass on this checkout.
2. **State/read order:** verify and reload instructions before state writes; preserve same-session counters and validate inherited checkpoints; root governance, plan, prior reviews and pinned audit precede implementation.
3. **B-0a:** inventory first; the observed count is **37**, not the historical 33. The mandatory owner-disposition stop is correct; no new copy until ≤14.
4. **B-0b:** preserve field semantics, compute acceptance-root closure, stage retirement decisions, reconcile J-0c→J-0d→J-0→J-0m and J-4p/K0-SV, and require both reconciliation tests.
5. **B-0c:** stage `mcp.none.json`, schemas, cards, validated launch-input template and source-commit-bearing bootstrap manifest; incorporate KU-01…03 before independent review.
6. **B-1:** launch directly using executable `CLAUDE_BIN`, absolute cwd/input/scratch paths, staged `--mcp-config`, declared environment/deadline and recorded process-group/start identity; no unfinished dispatcher or `kyjob.sh`.
7. **B-2:** independent review→owner merge→install merged source; reconcile legacy state, stop old dispatchers, record loaded tracker revision, then pass preflight and `kyversion.sh --bootstrap` with `mode: bootstrap`.
8. **B-3:** exercise real typed CLI paths against the isolated tracker/backend; prove live EVENTS unchanged, external requests absent, fixture cleanup complete and tested hashes recorded.
9. **B-4:** independently accept governance coverage and admit Wave 0/1 packets; retain coverage and packet hashes.
10. **B-5:** validate governance backfill, produce the final manifest and final receipt, pass normal version verification and print the final manifest digest for the owner.
11. **Gate:** final Wave B acceptance plus certification, rebuild pins, regeneration, exhaustive PR dispositions and SS coordinator closure must bind one release; missing evidence stays WAIT.
12. **Resume/holds:** pre-resume readiness supplies no campaign authority; owner paste binds N-467 to release and bundle digests; only the recorded certification-hold owner removes that hold.
13. **Conductor entry:** setup→manifest digest→prompt-entry digest→verified prompt→`kyversion.sh --expected-manifest-digest`→exclusive `kylock.sh acquire`; no checkout refresh before ownership.
14. **State/resume:** apply rollover rules, write matching `OWNER_RESUME`, record the note and pass the full gate before dispatcher start.
15. **Dispatcher/inboxes:** idempotent `start-dispatcher`; reconcile S and steward inboxes; durable deferrals are acknowledged using the correct inbox flag.
16. **Wait:** `--wait 540` fits the stated 600,000 ms harness limit; count every return, check thresholds before waiting again and inspect steward messages every tenth wake-up.
17. **First tick:** STOP/global HOLD, merge hold, gate, recovery/freshness and serialized checkout refresh precede admission.
18. **First BUILD:** claim/item lock→verified prerequisite head-or-squash containment→allocator→current slot receipt→install admitted tests→feature-red or independently justified already-green classification.
19. **Review/VERIFY:** `ky review` registers the actual head; an independent verifier tests the bound packet under the enforced write boundary; controller publication follows verifier exit and integrity checks.
20. **MERGE:** queue only the accepted registered head using `--match-head-commit`; the installed `gh` supports that flag, and head changes invalidate authorization and require queue cancellation.
21. **COMPLETE/POST-READBACK:** distinguish reviewed PR head from squash commit; data-writing code waits for merge-bound post-deploy acceptance; operations use the exact completed receipt, operation identity and artifact-digest verdict.
22. **Release/finalisation:** terminal process exit→identity-checked claim release; finalizer stops admission, proves drain, independently accepts C-3, cleans owned resources, independently checks final absence and completes C-4 while the tracker remains available.
23. **First problems:** B-0a contains the first naming disagreement; unchanged `local_db.sh up` is the first identified unsafe reused command when DB tests begin; B-2’s audit is the first identified incompatible launch acceptance. With KU-01…03 incorporated, no further command-order defect was found; this is a specification walk, not an executed v3 launch.

**Part 3 — Essential governance and security**

- Owner decisions and D-1/D-2/D-3 remain intact; strategy v1.2 is historical and supplies no operative override.
- Coverage retains applicable CLAUDE.md §I/§N, charter §0 and retained acceptance contracts; the five pinned specification hashes matched.
- FROZEN remains a stop boundary, including single-writer/base, connection ownership and deterministic fact/prose contracts; routing to Opus grants no exception.
- KU-02 is the remaining concrete owner-policy conflict; worktree inventory, archive-before-removal and capacity requirements otherwise remain explicit.
- Coverage approval, cleanup assertions and version labels must be backed by the required measured evidence; they are not substitute detectors.
- The verifier’s write boundary must survive shell/chmod/replacement attacks; same-user permissions or `--disallowedTools` alone do not establish that boundary.

**Part 4 — Token economy**

- No unearned savings claim remains: P:507–509 explicitly says savings and throughput cannot yet be estimated; 64% is a historical addressable-class ceiling.
- Silent-spend risks remain in bootstrap/rehearsal, repeated fixed context, failed launches, broad verifier exploration and subscription/backoff loops.
- `--bare` instruction visibility remains a B-3 measurement, not an assumed saving.
- Parent/child accounting, duplicate result events, killed jobs and interactive sessions require the stated reconciliation; missing usage stays unknown.
- Persistent failure fingerprints must survive rollover; no LLM liveness ceremony or repeated known-failing gate should generate unbounded retries.

**Part 5 — Quality and signal honesty**

- §N.8 remains exposed wherever a receipt proves a command ran rather than that the claimed behavior holds; KU-01 is a concrete example.
- VERIFY must independently assess behavior, negative cases, compatibility and relevant mutations; author tests plus green CI are insufficient.
- Routing correctly escalates KA-1e’s sky/ephemeris work, K1-2/K6-4 migration prose/metadata and `platform/src/lib/auth/**`; FROZEN changes still stop.
- Original failing-base evidence and admission classification are distinct: already-green work needs independent assessment, not manufactured red tests.
- Schema prerequisites need actual required columns and registry evidence; absence cannot justify silently dropping their consumers.
- The throwaway-Postgres Kāla DB CI job remains required; accepted heads, merges, decisions, joins and guarded completions retain separate measures and denominators.

**Part 6 — Prompts as artifacts**

- The planning prompt is self-sufficient as a governed entry point with its required local readings; it no longer requires a manifest that it must itself create.
- The conductor prompt becomes executable only after B-5 installation and readiness; its manifest digest is a final-bundle anchor, not a prompt-file digest.
- Pairing is enforceable through source/blob verification, manifest entries and installed-hash checks; KU-03 removes ambiguous generated-output identities.
- Session rollover and both inbox acknowledgment paths are specified; implementation tests must demonstrate consecutive handoffs, same-session re-entry and rejected stale checkpoints.
- KU-02 supplies the missing connection between handoff and the owner’s database cleanup rule.
- Supplied Claude CLI flags present no remaining syntax contradiction; actual authentication, model availability, process identity and sandbox enforcement require Wave B execution.
- Owner worktree dispositions, PR merges and the external SS closure remain explicit dependencies; a Claude session cannot honestly manufacture them.

**5. What I could not verify and why**

- **No v3 execution acceptance:** `kyversion.sh`, `kylock.sh`, the dispatcher, campaign checkout and final v3 manifests/receipts are not installed/present for this launch.
- **No live release readiness:** the certification hold remains; the required final release evidence and matching resume binding were not established.
- **No operational proof:** Claude authentication/model execution, `--bare` loading, verifier isolation, DB mounts/cleanup, queue behavior and consecutive handoffs were not exercised in this read-only review.
- The audit evaluation also returned six reviewed-verdict findings and 25 expired-worker findings; I have **not** classified those as false positives. B-2 must reconcile them with evidence.
- No files, worktrees, databases, tracker events or external state were changed; no session-created scratch or copies require cleanup.