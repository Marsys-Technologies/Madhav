---
artifact: CLAUDECODE_BRIEF.md
canonical_id: CLAUDECODE_BRIEF
version: 3.0
status: ACTIVE_ORCHESTRATOR
authored_by: Cowork (Claude Opus 4.7) 2026-05-21
authored_for_session: CHATV2-WRAPUP-ORCHESTRATOR
purpose: >
  Autonomous orchestrator for the **Chat V2 wrap-up arc** — closes the loop on
  PR #112, PR #113, three governance-hygiene follow-up briefs, a new triage
  brief for drift_detector HIGH findings, CI investigation, and cleanup.
  Operates from inside a single dedicated worktree at
  `/Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap`. All packets execute inside that
  worktree by branch-switching — no external worktrees are created. State lives
  in the packet_status YAML below; the orchestrator updates it after every
  packet. Re-launching with the kickoff prompt resumes from
  last_completed_packet.

scope_note: >
  This is the **Chat V2 wrap-up arc only**. It does NOT touch the project's M5
  macro-phase campaign work (currently paused; lives on branches like
  `feature/m5-coverage-remediation`, `icr/s2-l1-truth-index`, etc., with their
  own worktrees). The wrap-up arc completes independently.

# ════════════════════════════════════════════════════════════════════════════
# WRAPUP STATE — orchestrator updates this YAML after every packet completes
# ════════════════════════════════════════════════════════════════════════════
packet_status:
  A.1:  DONE           # rebase + merge PR #112 (chat-v2/pr-111-remediation)
  A.2:  DONE           # rebase + merge PR #113 (governance-hygiene/drift-detector-fix)
  B:    INFO_EMITTED   # operator gate — emit HUMAN_GATE_B.md (non-blocking)
  C:    PR_OPEN        # Run 2 — GH_SESSION_LOG_STRUCTURE
  D:    PENDING        # Run 3 — GH_CORPUS_FRONTMATTER_BACKFILL
  E.1:  PENDING        # author GH_DRIFT_HIGH_TRIAGE_BRIEF_v1_0.md
  E.2:  PENDING        # launch Run 4 — drift HIGH triage (categorize phase only)
  F.2:  PENDING        # investigate 2 failing CI checks from PR #111
  F.3:  PENDING        # cleanup — convert this brief to FINAL_WRAPUP_SUMMARY.md
last_completed_packet: C
last_halt: null         # set to {packet, reason, next_action, halt_file_path} on halt
session_started_at: null
session_resumed_count: 1

execution_order:        # orchestrator walks this list in order, skipping DONE / HALTED
  - A.1
  - A.2
  - B
  - C
  - D
  - E.1
  - E.2
  - F.2
  - F.3

merge_policy:
  A.1: auto_merge      # existing reviewed PR — merge after mechanical rebase
  A.2: auto_merge      # same
  C:   open_pr_only    # new PR — stop at "PR opened" for human review
  D:   open_pr_only    # same
  E.2: open_pr_only    # same

worktree_model: single
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap
worktree_initial_branch: main
worktree_cleanup: manual_post_wrapup   # user removes this worktree manually after F.3 emits the final summary
---

# Chat V2 Wrap-Up Orchestrator Brief

## §1 — Mission

Execute Packets A through F sequentially to close out the Chat V2 R10 +
Phase 4C post-COMPLETE remediation arc. End state: drift_detector exits ≤ 3
with HIGH count actively triaged via a new brief, schema_validator exits ≤ 2
with documented residuals, mirror_enforcer exits 0, all open PRs merged or
opened-for-review, operator actions emitted as a single human gate, deferred
items parked.

## §2 — Operating principles

- **Single worktree.** Everything happens inside
  `/Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap`. The orchestrator is launched
  from this worktree's root. Branch switches inside this worktree handle the
  per-packet needs.
- **One Claude Code chat = one orchestrator session.** Sub-agents are
  dispatched via the Agent tool to keep the orchestrator's own context lean.
- **State lives in this file's frontmatter.** Read `packet_status` to pick the
  next eligible packet; write `packet_status` after every packet using `Edit`
  (atomic single-field changes), never `Write` (which overwrites the file).
- **Halt protocol.** If a packet can't complete autonomously, write
  `00_ARCHITECTURE/CONDUCTOR/wrapup/HUMAN_GATE_<packet>.md` with reason +
  next-action, set `last_halt:` in the frontmatter, and STOP.
- **No interactive prompts.** Never wait for user input mid-session. If
  uncertain, halt with a gate file.
- **HEAD discipline.** After every packet that switches branches, return to
  `main` via `git checkout main` before continuing. Each packet starts on
  `main` and ends on `main` (with the exception of HALTED packets, where the
  branch is preserved for human inspection).

## §3 — Packet ledger

| Packet | Title | Branch operations inside worktree | Outcome | Halt-on-doubt? |
|---|---|---|---|---|
| A.1 | Merge PR #112 | checkout `chat-v2/pr-111-remediation`, rebase main, push, merge via gh, return to main | PR #112 merged | yes — any non-mechanical conflict |
| A.2 | Merge PR #113 | checkout `governance-hygiene/drift-detector-fix`, rebase main, push, merge via gh, return to main | PR #113 merged | yes |
| B   | Operator gate | none (orchestrator-side file write) | HUMAN_GATE_B.md emitted; orchestrator continues | no — non-blocking |
| C   | Run 2 — SESSION_LOG structure | create branch `governance-hygiene/session-log-structure` from origin/main, do brief work, push, open PR, return to main | new PR opened (NOT merged) | yes |
| D   | Run 3 — corpus frontmatter | create branch `governance-hygiene/corpus-frontmatter` from origin/main, do brief work, push, open PR, return to main | new PR opened (NOT merged) | yes |
| E.1 | Author Run 4 brief | none — file write on current branch (main) | GH_DRIFT_HIGH_TRIAGE_BRIEF_v1_0.md authored | no |
| E.2 | Run 4 — drift HIGH triage | create branch `governance-hygiene/drift-high-triage` from origin/main, run categorize-only session, push, open PR, return to main | categorization PR opened; per-class fix PRs deferred | yes |
| F.2 | CI investigation | orchestrator-side (or short sub-agent) | findings logged to F2_CI_FINDINGS.md | no |
| F.3 | Brief self-cleanup + summary | orchestrator-side | this brief flipped to COMPLETE; FINAL_WRAPUP_SUMMARY.md emitted | no |

## §4 — Per-packet execution recipes

### Packet A.1 — Merge PR #112

**Goal:** Rebase `chat-v2/pr-111-remediation` onto current `origin/main` from
within this worktree, resolve mechanical conflicts, push, merge via
`gh pr merge 112 --squash --delete-branch`.

**Sub-agent dispatch.** Spawn a `general-purpose` agent with description
"Rebase + merge PR #112" and this prompt:

> You are the Chat V2 wrap-up orchestrator's Packet A.1 sub-agent. You operate
> inside the worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap`. Your
> task is to rebase the branch `chat-v2/pr-111-remediation` onto current
> `origin/main` and merge PR #112.
>
> Steps:
> 1. `cd /Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap && git fetch origin`.
> 2. `git checkout chat-v2/pr-111-remediation`. If this fails because the branch is checked out in another worktree (e.g., MadhavPR111), HALT immediately with a gate file telling the user to remove that worktree first — do NOT try to force.
> 3. `git rebase origin/main`.
> 4. **Expected conflicts (resolve mechanically):**
>    - `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`: branch authored a `v5.28` entry; main has `v5.28` for the panchang seal. Resolution — read main's highest version, renumber the branch's entry to the next (likely `v5.29`). Update version string + any cross-references in the entry body.
>    - `00_ARCHITECTURE/SESSION_LOG.md`: append-point shift — move the branch's `PR-111-REMEDIATION` session entry to the new end of the file, after main's most recent panchang entries.
>    - `CLAUDE.md` §E: branch appended a paragraph to the Chat V2 R10 entry; main may have touched §E for Phase 4C. Preserve both — the chat-v2 paragraph goes after the panchang updates.
>    - `.gemini/project_state.md`: adapted parity merge — preserve both sides meaningfully.
> 5. **HALT condition:** If any conflict is in `platform/src/**`, `platform/migrations/**`, or any file not in the four expected paths above, run `git rebase --abort`, write `00_ARCHITECTURE/CONDUCTOR/wrapup/HUMAN_GATE_A1.md` with the conflict file list + recommendation, and report HALTED. Do NOT proceed.
> 6. After successful rebase: `git push --force-with-lease origin chat-v2/pr-111-remediation`.
> 7. `gh pr checks 112`. If checks pending, wait up to 10 min. If checks fail unexpectedly, HALT.
> 8. `gh pr merge 112 --squash --delete-branch --auto`.
> 9. Return worktree HEAD to main: `git checkout main && git pull --ff-only origin main`.
> 10. Report: (a) final merge SHA on main, (b) CURRENT_STATE version assigned, (c) any conflict files touched, (d) HALTED status if applicable. Under 250 words.

**On sub-agent success:** flip `packet_status.A.1` to `DONE`, set
`last_completed_packet: A.1`, append a log entry to
`00_ARCHITECTURE/CONDUCTOR/wrapup/EXECUTION_LOG.md`.

**On sub-agent halt:** flip `packet_status.A.1` to `HALTED`, set `last_halt`,
stop orchestrator.

### Packet A.2 — Merge PR #113

Same recipe as A.1 with substitutions:
- branch: `governance-hygiene/drift-detector-fix`
- PR number: 113
- CURRENT_STATE renumber: branch authored `v5.29` from `v5.27` base. Main now has up to `v5.29` (after A.1). Renumber to `v5.30`.
- Additional expected conflict file: `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` §F (branch appended).
- Halt clause: any conflict outside the 5 expected files (CURRENT_STATE, SESSION_LOG, CLAUDE.md, .gemini/project_state.md, ONGOING_HYGIENE_POLICIES) → HALT.
- Step 2 might fail if branch is checked out in MadhavGH1 worktree — same HALT protocol as A.1 step 2.

### Packet B — Operator gate (non-blocking)

**Action — orchestrator-side, no sub-agent:**
1. Write `00_ARCHITECTURE/CONDUCTOR/wrapup/HUMAN_GATE_B.md` covering:
   - **B.1** R8 Cloud Run env-vars (`gcloud run services update amjis-web --region asia-south1 --update-env-vars MARSYS_FLAG_R8_SLASH_ENABLED=true,MARSYS_FLAG_R8_EXPORT_ENABLED=true,MARSYS_FLAG_R8_TOKENS_ENABLED=true`)
   - **B.2** browser smoke for slash / export / tokens
   - **B.3** fresh Cloud Build (`gcloud builds submit --config=platform/cloudbuild.yaml platform/`)
   - **B.4** browser smoke for scroll discipline + validator failure bands
   - **B.5** panchang bootstrap rebuild (migration 069 + bootstrap_panchanga.py + staging swap)
2. Flip `packet_status.B` to `INFO_EMITTED`.
3. Continue immediately to Packet C.

### Packet C — Run 2 (SESSION_LOG structure)

**Pre-flight check.** Confirm A.1 and A.2 are DONE in packet_status. If not, HALT.

**Sub-agent dispatch:**

> You are the Chat V2 wrap-up orchestrator's Packet C sub-agent. You operate
> inside the worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap`. Read
> CLAUDE.md (§C mandatory reading) in full. Then read
> `00_ARCHITECTURE/governance_hygiene_briefs/GH_SESSION_LOG_STRUCTURE_BRIEF_v1_0.md`
> (in this worktree) and execute it autonomously per its §4 step-by-step.
> Emit the SESSION_OPEN handshake before any substantive tool call.
>
> **Worktree override:** The hygiene brief's Step 1 prescribes a separate
> worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavGH2`. **Ignore that.** You
> are already inside the wrap-up worktree. Instead:
> 1. `cd /Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap && git fetch origin`.
> 2. `git checkout -b governance-hygiene/session-log-structure origin/main`
>    (creates the brief's prescribed branch directly inside this worktree).
> 3. Execute the brief's substantive steps (AC.1 through AC.10) here.
> 4. Push: `git push -u origin governance-hygiene/session-log-structure`.
> 5. Open the PR via `gh pr create`. Do NOT merge.
> 6. Return worktree HEAD to main: `git checkout main && git pull --ff-only origin main`. The new branch stays alive on the remote for human review.
>
> Halt conditions: per the brief's §5. On halt, write
> `00_ARCHITECTURE/CONDUCTOR/wrapup/HUMAN_GATE_C.md` (in this worktree) in
> addition to the brief's own SESSION_HALT.md.
>
> Report: (a) branch name, (b) PR URL, (c) AC.1–AC.10 statuses, (d) any
> SESSION_HALT.md content if halted, (e) final validator exit codes. Under 400 words.

**State protocol:** on success flip `packet_status.C` to `PR_OPEN`. Continue to D.

### Packet D — Run 3 (corpus frontmatter)

Same recipe as C with substitutions:
- brief path: `00_ARCHITECTURE/governance_hygiene_briefs/GH_CORPUS_FRONTMATTER_BACKFILL_BRIEF_v1_0.md`
- branch: `governance-hygiene/corpus-frontmatter`
- halt gate file: `HUMAN_GATE_D.md`
- **Special caution:** brief touches `01_FACTS_LAYER/**` and `025_HOLISTIC_SYNTHESIS/**`. Brief's own halt clause is "halt rather than guess." Sub-agent must respect.

### Packet E.1 — Author GH_DRIFT_HIGH_TRIAGE_BRIEF

**Sub-agent dispatch:**

> You are the Chat V2 wrap-up orchestrator's Packet E.1 sub-agent. Author
> `/Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap/00_ARCHITECTURE/governance_hygiene_briefs/GH_DRIFT_HIGH_TRIAGE_BRIEF_v1_0.md`
> following the structure of the existing GH briefs in the same folder. Scope:
> categorize-only session over the 86+ HIGH drift_detector findings. Single AC:
> triage report at `00_ARCHITECTURE/governance_hygiene_briefs/drift_high_triage/REPORT.md`
> classifying every HIGH finding by H.3.N check (H.3.1 path-table parity,
> H.3.2 fingerprint match, H.3.3 MACRO_PLAN/PHASE_B_PLAN alignment, H.3.5
> FILE_REGISTRY, H.3.6 GOVERNANCE_STACK, H.3.7 phantom refs, H.3.8 unreferenced
> artifacts) with suggested fix per finding. No fixes applied in this session.
> Use the same frontmatter conventions as the other GH briefs (status: STORED;
> may_touch narrow to the triage folder + governance trail).
>
> When done, report: (a) path to new brief, (b) summary of scope, (c) any
> structural concerns. Under 200 words.

**On success:** flip `packet_status.E.1` to `DONE`. Continue to E.2.

### Packet E.2 — Launch Run 4 (categorize phase)

Same recipe as C with substitutions:
- brief path: the file just authored in E.1
- branch: `governance-hygiene/drift-high-triage`
- halt gate file: `HUMAN_GATE_E2.md`

### Packet F.2 — CI investigation

**Action — orchestrator-side or short sub-agent.** Use `gh pr checks 111` and
`gh run view <run-id> --log-failed` for the 2 failing checks. Classify each as
"real regression" vs. "flake" vs. "pre-existing." Write findings to
`00_ARCHITECTURE/CONDUCTOR/wrapup/F2_CI_FINDINGS.md`. Cross-reference with
`00_ARCHITECTURE/chat_v2_briefs/pr_111_remediation/CI_INVESTIGATION.md` (now on
main after A.1).

**On completion:** flip `packet_status.F.2` to `DONE`.

### Packet F.3 — Brief self-cleanup + final summary

**Goal:** Write the final wrap-up summary, flip this brief to COMPLETE, and
emit a final message instructing the user how to clean up the wrap-up worktree.

**Action — orchestrator-side:**
1. Run the validator triple, capture exit codes:
   ```bash
   python3 platform/scripts/governance/schema_validator.py; echo "schema exit: $?"
   python3 platform/scripts/governance/drift_detector.py; echo "drift exit: $?"
   python3 platform/scripts/governance/mirror_enforcer.py; echo "mirror exit: $?"
   ```
2. Write `00_ARCHITECTURE/CONDUCTOR/wrapup/FINAL_WRAPUP_SUMMARY.md` with:
   - Each packet's final status (DONE | INFO_EMITTED | PR_OPEN | HALTED | DEFERRED).
   - Final validator triple exit codes.
   - PR URLs for any PRs still open (C, D, E.2).
   - Operator gate status (B.1–B.5).
   - Deferred items list.
   - **Manual cleanup instructions for the user:**
     ```
     # From the main checkout (not from inside this worktree):
     cd /Users/Dev/Vibe-Coding/Apps/Madhav
     git worktree remove /Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap
     git worktree prune
     ```
3. Flip this brief's `status:` from `ACTIVE_ORCHESTRATOR` to `COMPLETE`. Set
   `last_completed_packet: FINAL`.
4. Append a one-line note to `CLAUDE.md` §E (Chat V2 R10 entry) pointing to
   `FINAL_WRAPUP_SUMMARY.md`'s path on main.
5. `git add -A && git commit -m "docs(chatv2-wrapup): final summary + brief status COMPLETE" && git push origin main` — yes, this commits to main from inside the worktree. The commits include just the wrap-up summary + the CLAUDE.md note + the brief's COMPLETE status.

**Note on F.4:** I removed the original F.4 worktree-cleanup-as-orchestrator-action. The orchestrator cannot remove the worktree it's currently running inside. Instead, F.3's summary tells the user how to remove the worktree manually after the orchestrator exits.

## §5 — Final wrap-up procedure

After F.3 completes:

1. Emit a final chat message:
   - "Chat V2 wrap-up orchestrator complete."
   - Each packet's status.
   - Open PRs awaiting human review (with URLs).
   - Operator gate status.
   - Deferred items.
   - The "from main checkout, remove this worktree" instructions.
2. Stop. Do NOT take further actions.

## §6 — Resumability protocol

On launch (initial OR resume), the orchestrator:

1. Reads this file's `packet_status`.
2. Increments `session_resumed_count`.
3. If `last_halt` is non-null:
   - Decide retry vs. skip per the halt's `next_action`. Transient failures
     (e.g., `gh pr checks` network timeout) auto-retry. Anything else: halt
     again immediately with a message pointing the user at the existing
     `HUMAN_GATE_<packet>.md`.
4. Walks `execution_order`, finds the first packet not in {DONE,
   INFO_EMITTED, PR_OPEN, DEFERRED, FINAL}, executes it.
5. Updates state after the packet completes.
6. Continues until all packets terminal or a halt.

## §7 — Halt-on-doubt clauses (sticky)

Orchestrator MUST halt rather than guess when:
- A merge conflict touches a file not in the per-packet expected-conflicts list.
- A sub-agent reports HALTED with reasoning the orchestrator can't disambiguate.
- A pre-flight check fails (e.g., A.1 not yet DONE before C is attempted).
- `gh pr merge` reports an unexpected error.
- A sub-agent claims success but verification (file diff, validator exit code,
  PR existence) contradicts the claim — trust the verification, halt.
- Validator suite regresses between packets without an obvious cause.
- `git checkout <branch>` fails because the branch is checked out in another
  worktree — halt with instructions to remove that worktree.

Halts always: write `HUMAN_GATE_<packet>.md`, set `last_halt`, stop without
claiming the packet DONE.

## §8 — Files the orchestrator MAY touch

Inside `/Users/Dev/Vibe-Coding/Apps/MadhavCV2Wrap`:

- `CLAUDECODE_BRIEF.md` (this file — frontmatter state updates only)
- `00_ARCHITECTURE/CONDUCTOR/wrapup/**` (working folder)
- `00_ARCHITECTURE/governance_hygiene_briefs/GH_DRIFT_HIGH_TRIAGE_BRIEF_v1_0.md` (authored in E.1)
- `CLAUDE.md` (one-line §E note in F.3 only)

Sub-agents operate in this same worktree on per-packet branches and may touch
a broader scope per their respective briefs.

## §9 — Files the orchestrator MUST NOT touch

- `platform/src/**`
- `01_FACTS_LAYER/**`
- `025_HOLISTIC_SYNTHESIS/**`
- `06_LEARNING_LAYER/**`
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
- `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md`
- `00_ARCHITECTURE/CONDUCTOR/session_queue.yaml`
- `00_ARCHITECTURE/CONDUCTOR/SESSION_QUEUE_M5_COVERAGE.yaml`
- Any path that the active per-packet sub-agent's brief lists in its own must_not_touch.
- ANY M5-campaign-related files or branches (`feature/m5-*`, `icr/s2-*`, etc.).

The orchestrator MAY READ any file. It just can't WRITE outside §8.
