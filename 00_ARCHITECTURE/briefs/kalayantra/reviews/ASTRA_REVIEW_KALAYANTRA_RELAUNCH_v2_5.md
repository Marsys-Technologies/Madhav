---
artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH
version: "2.5"
verdict: PROCEED-WITH-FIXES
blocking_count: 3
reviewed_commit: 0a36f321e
review_date: 2026-10-11
review_mode: read-only
---

**1. Verdict**

Continue B-0c preparation; apply KX-01…KX-03 before B-1.  
KW-01, KW-02, KW-05 and KW-06 are closed at specification level; KW-03 and KW-04 remain partial.  
The literal walkthrough fails in cockpit step 1; installation and successor-bundle loading also retain contradictions.  
Owner decisions remain accepted without reopening them. Runtime launch acceptance is not established.

References: **P** = [plan v2.5](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_5.md); **C** = [cockpit v2.5](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_COCKPIT_PROMPT_v2_5.md); **A** = [surrogate definition](/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/.claude/agents/kalayantra-owner-surrogate.md); **S** = [planner state](/Users/Dev/kalayantra/run/PLANNER_STATE.json).

Live snapshot: **2026-10-11 17:08:38 UTC / 22:38:38 IST**. HEAD remained `0a36f321ede2937cd141adc8ea8c7429845c82fc`; all five anchor files matched its blobs. Concurrent untracked B-0c drafts were excluded.

**2. Part 1 — Closure**

CLOSED means specification closure, not implementation or runtime acceptance. Exact replacements for partial findings follow below.

| Finding | Status | Evidence and conclusion |
|---|---|---|
| KW-01 | **CLOSED** | P:207–220 and C:51–64 migrate legacy evidence by type before reading `active`; all 13 present file checkpoints match, and the retired proposal matches its recorded historical blob. |
| KW-02 | **CLOSED** | P:186–200, 609–633 and C:46–50,120–124 explicitly make the controller the sole lock holder/state writer and make observer exit queue-only. |
| KW-03 | **PARTLY** | P:117,653–656,692–694 correct the baseline and heading, but B-2:702 retains “owner-merged source” and a second merge-bound receipt description; apply KX-02. |
| KW-04 | **PARTLY** | P:26–38,768–771 establish authorization chaining, but C step 1 is not executable as written and active consumers retain version-specific paths; apply KX-01/KX-03. |
| KW-05 | **CLOSED** | P:379 explicitly excludes handled/pending proposals, defers veto publication to the deterministic handler and requires restart, notification-failure and target-change acceptance cases. |
| KW-06 | **CLOSED** | P:668–685 and C:84–110 distinguish legitimate controller waiting from missing children and require bound GitHub readback before verifying approval. |
| KV-01 | **PARTLY** | The single-root chain is specified, but entry fails under KX-01 and the v2.5 rename introduces the dangling surrogate reference in KX-03. |
| KV-02 | **CLOSED** | Typed migration, fenced ownership, action reconciliation and observer behavior now cover the prior recovery defects. |
| KV-03 | **PARTLY** | B-0c correctly separates qualified `kyboot.py` from campaign dispatch, but KX-02 still obstructs the later receipt-authorized installation transition. |
| KV-04 | **CLOSED** | P:223–242,625–633 preserve deterministic waiting, actionable admission and failure/no-progress history across restarts. |
| KV-05 | **CLOSED** | The operative SURROGATE row now agrees with the pending-veto state machine and agent publication restriction. |
| KV-06 | **CLOSED** | P:449–463 retains configuration-bound qualification, positive limits, launchd-context probes and refusal on unknown results. |
| KV-07 | **PARTLY** | D-6/D-9 and baseline accounting are consistent, but B-2’s surviving merge prerequisite remains unresolved. |
| KV-08 | **CLOSED** | P:262–271 and A:26–40 preserve human platform approval and inherited owner-only boundaries. |
| KU-01 | **CARRIED** | B-0c retains the obligation; installed `audit.py:123,155` still demands post-deploy verdicts more broadly than `completion.py:81–96`. |
| KU-02 | **CARRIED** | B-0c retains the obligation; installed `local_db.sh:23,102` still lacks the required storage mount and keeps the stopped container. |
| KU-03 | **CARRIED** | All three canonical/compatibility pairs currently have equal bytes, but manifest binding and mismatch-refusal acceptance remain outstanding. |
| P-1/P-2 | **CARRIED** | The launch flags and version pin remain; local Claude reports **2.1.296**, while recorded v2.3 probes do not constitute the required per-configuration qualifications. |

**3. Findings**

**KX-01 — BLOCKING before B-1 — Cockpit entry does not execute its trust-root procedure**

**Location:** C step 1:23–40.

**Defect:** The shell block redirects the trusted prompt to `$TMPDIR/cockpit.root.md` without loading it, and never assigns `C` before the comparison loop. Here `$TMPDIR` lies outside the owner’s required scratch root; independently, the fresh-shell comparison with empty `C` exits **128**, `fatal: bad revision ''`.

**Failure:** The first paste either violates scratch policy or stops despite all five files matching the approved commit; manually repairing shell state becomes an undocumented prerequisite.

**Exact replacement — replace the single step-1 shell block with sequential phases:**

> First execute only:
>
> ```bash
> C0=<APPROVED_SOURCE_COMMIT>
> C="$C0"
> D=00_ARCHITECTURE/briefs/kalayantra
> R=/Users/Dev/kalayantra/run
> git cat-file -e "$C0:$D/KALAYANTRA_V3_COCKPIT_PROMPT_v2_5.md" || exit 1
> git show "$C0:$D/KALAYANTRA_V3_COCKPIT_PROMPT_v2_5.md" || exit 1
> ```
>
> Read the displayed root-commit instructions before continuing. Do not redirect them to a temporary file.
>
> Next, inspect the activation records read-only. With no records, retain `C="$C0"`. Otherwise validate the complete predecessor chain, source commits, manifest digests, independent reviews and authorizing acts; explicitly assign `C` only to the terminal authorized source commit. Missing or invalid required evidence stops entry.
>
> Only after that evaluation run the active-bundle verification phase, using the role-to-path binding below. Keep the resolved values together across tool calls; never depend on an inherited shell variable.

**KX-02 — BLOCKING before B-1 — B-2 still requires the prohibited merge**

**Location:** P §14, B-2:702.

**Defect:** The new receipt-bound installation text was prepended without deleting the old instruction that `install.sh` installs “only reviewed, owner-merged source.” The same cell consequently describes both optional merge metadata and a second receipt containing a required merge commit.

**Failure:** B-2 cannot satisfy its literal instructions under `HOLD_MERGES`, or an implementer silently chooses which requirement to ignore.

**Exact replacement — B-2 work and acceptance cells:**

> **Work:** Independent review accepts the exact immutable source head or component heads assembled into the installation bundle. `install.sh` verifies those heads, review receipts and manifest hashes, then installs the fleet, tracker, wrappers, approved plan, prompts, cards and manifest. `run/INSTALL_RECEIPT.json` records source commits, tree/component hashes, review references, qualifications, `CLAUDE_BIN` and the running tracker’s loaded revision. A merge commit is optional historical metadata, never an installation prerequisite.
>
> Prove that old supervisors/sweeps cannot dispatch using `STOP_*` and process-absence evidence; create the campaign checkout within capacity; publish the staged D-RETIRE decisions; reconcile legacy claims, PRs and checkpoints. Mark the receipt `mode: bootstrap`. Under `HOLD_MERGES`, merge intentions remain durable local requests with no GitHub queue submission; the surrogate executes them after certification-done.
>
> **Acceptance:** Installed hashes match the reviewed component heads bound by the manifest; `preflight.sh launch` and `kyversion.sh --bootstrap` pass. Only the accepted bootstrap receipt permits isolated rehearsal activation; receipt-file existence alone grants no authority.

**KX-03 — BLOCKING before B-1 — Active bundle references do not survive version changes**

**Location:** A:11–15; C:32–40; P pairing rule:26–38 and roster:161–162.

**Defect:** The unchanged surrogate definition mandates reading `KALAYANTRA_RELAUNCH_PLAN_v2_4.md`, which is absent from both disk and reviewed head after its rename to v2.5. Cockpit verification also hard-codes v2.5 filenames for every successor commit, so another authorized rename breaks fresh entry; the roster additionally retains retired PLANNING/CONDUCTOR prompt references.

**Failure:** The required B-0c surrogate cannot complete its mandatory read, and a properly authorized successor bundle can fail entry solely because its plan/prompt filenames changed.

**Exact replacement:**

> **Bundle entrypoints:** The initial trust root uses its five explicitly named files. Every successor manifest includes a reviewed `entrypoints` mapping for `plan`, `cockpit_prompt`, `owner_decisions`, `strategy` and `surrogate_agent`, with repository-relative paths and blob hashes; the activation record binds that manifest’s digest.
>
> After validating the authorization chain, verify those mapped files against their tracked blobs at the authorized source commit `C`, then load the mapped cockpit prompt. Do not require a successor to retain the root bundle’s versioned filenames. A changed owner-decisions blob additionally requires owner authorization.
>
> **Surrogate authority loading:** The caller supplies the authorized source commit and verified entrypoint binding in the immutable job input. Read the mapped active plan (§4a and §15), mapped owner-decisions record and reviewed source-bound OWNER_SURROGATE card before ruling. Refuse missing or mismatched bindings; do not fall back to a retired plan or infer authority from installed filenames.
>
> **Roster mode replacements:** Planner: “COCKPIT while holding the planner fence; bounded headless PLAN jobs at xhigh.” SŪTRADHĀRA: “bounded headless conductor jobs supervised by the deterministic controller; observed and steered through COCKPIT.”

**4. Part 2 — Fresh-session and lifecycle walk**

1. **Step 1, first nonconforming instruction:** C:26 writes outside the prescribed scratch root; C:35 is the first reproduced command failure because `C` is unset.
2. **Root and empty chain:** After KX-01, read the root prompt, observe no activation records, retain `C=C0`; all five original files match `0a36f321e`.
3. **Step 2, ownership:** `loops/` and `locks/` are absent, which does not prove process absence; reconcile existing cockpit/controller ownership before acquiring the planner fence, otherwise remain an observer.
4. **Legacy migration:** The fenced writer preserves the original state, derives `active` from B-0c/deferred disposal/dependencies, initializes absent collections and retains typed trust, coordination and PR evidence; the proposal’s historical SHA-256 matches.
5. **Step 3:** The cockpit performs B-0c until a reviewed, qualified supervisor exists; the surrogate’s mandatory read currently fails under KX-03.
6. **Step 4:** Report legacy B-0c, unavailable v3 helpers/qualifications/receipts, **41** registered worktrees and the surviving certification merge hold; absent directories do not establish healthy or stopped processes.
7. **Step 5:** Complete and independently accept B-0c, including KU-01…03; execute approved disposals subject to their coordination conditions and satisfy **≤14 registrations before B-1**.
8. **Step 6:** Owner commands enter the durable queue; only the fenced role owner applies them, with veto and approval-report commands retaining their separate validation paths.
9. **Step 7:** Preserve hold ownership, prohibit main merges during the hold, and keep campaign launches behind the installed authorization machinery.
10. **Step 8:** A writer checkpoints/releases; an observer requests handoff through the queue and does not write role state.
11. **First B-1:** Qualified `kyboot.py` verifies its immutable staged bundle/review, configuration qualification, capacity, holds, bounded launch inputs and paths; it records and supervises the child process directly and obtains independent review.
12. **B-2:** As written, stop at the contradictory merge prerequisite; after KX-02, install accepted immutable heads without merging and earn the bootstrap receipt through readback and preflight.
13. **B-3/B-4:** Rehearse against the isolated tracker/backend, prove unchanged live EVENTS and cleanup, then independently accept card coverage and admitted packet hashes.
14. **B-5:** Bind final manifest, loaded tracker revision, rehearsal, coverage and validated governance evidence; create the immutable activation record bound to owner authorization or effective D-4.
15. **Successor activation:** Review the new immutable source and affected acceptance evidence, obtain owner/effective-D-4 authorization, and append a record linking predecessor, old/new commits and manifest digests; preserve earlier records.
16. **Next fresh cockpit:** Start from the same original root, validate the chain, resolve successor entrypoints under KX-03 and verify/load that bundle; a changed digest cannot reuse a stale `OWNER_RESUME`.
17. **First conductor iteration:** After matching D-7/resume and full gates, the controller alone locks/reconciles/writes state; an actionable batch launches a qualified child with a snapshot, which returns results/checkpoint requests without reacquiring ownership.
18. **Veto-class example:** Capacity above maxima produces one fingerprint-bound `PENDING_VETO`; successful notification plus visibility starts 30 minutes, after which the locked handler rechecks authority/target/evidence/holds and publishes/executes once—or refuses after veto, notification failure or changed inputs.
19. **`approve-window`:** Queue the owner report as unverified; deterministic readback must match repository, run/attempt, environment, SHA and required owner approval before clearing that dependency, while workflow completion and semantic operation acceptance remain separate.

This is a complete **conditional specification walk**, not a successful literal walk or an executed launch.

**5. Part 3 — Owner directions**

- **Resume-anywhere: PARTLY.** Migration and observer behavior are addressed; initial entry and successor filename resolution need KX-01/KX-03.
- **Autonomy with surrogate: PARTLY.** Authority and human-only boundaries are correct; the missing mandatory plan reference and installation contradiction obstruct execution.
- **Zero idle: ADDRESSED at specification level.** Deterministic waiting, actionable admission, pending-proposal deduplication and persistent breakers prevent intended idle model loops.
- **WRONG REMEDY:** None identified; the remaining defects are in applying the chosen design consistently.

**6. Part 4 — Token economy**

- KX-01/KX-03 leave a concrete path to repeated failed startup, reference hunting and unnecessary proposal/review cycles across fresh sessions.
- KX-02 can repeatedly consume planner/surrogate work reconciling incompatible installation prerequisites.
- Pending-veto ticks, unchanged awaiting items, empty inboxes and unchanged breaker conditions now have explicit non-admission rules.
- Interactive cockpit context remains owner-controlled; no automatic handoff or finite total-spend cap is promised.
- Accounting coverage and savings remain unproved until the reviewed baseline installation and session/child reconciliation are accepted.

**7. Part 5 — Signal honesty**

- KW-06 now supplies the right predicates for loop health and verified platform approval; no additional detector omission was found in those definitions.
- `PROBES.json` records v2.3 observations, including default permission mode; it is not a substitute for the missing configuration-bound `QUALIFICATIONS/` receipts.
- `WAVE_B_DONE`, campaign readiness and v3 loop health are **not earned** by the inspected state.
- Installed `ky decide` still publishes immediately and tracker projection treats delegated final outcomes as effective; the specified veto-controller boundary must therefore be implemented and tested before use.
- The §17 closure map cannot establish KW-03/KW-04 closure while the contradictory operative instructions remain.

**8. What I could not verify**

- Actual v3 launches, authentication/tool isolation, process fencing, crash recovery, DB cleanup, veto timing or approval readback: no builds, probes or runtime transitions were executed.
- Current GitHub reviews, environment approval configuration/events, workflow outcomes or SS’s complete release handoff.
- Process absence or exclusive ownership from missing control directories; no lock was acquired.
- Concurrent untracked B-0c implementation drafts were outside the pinned review.

No files, tracker/fleet state, worktrees or scratch resources were created or changed by this review.

