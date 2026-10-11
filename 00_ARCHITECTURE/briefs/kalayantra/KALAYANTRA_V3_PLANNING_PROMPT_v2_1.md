---
artifact: KALAYANTRA_V3_PLANNING_PROMPT_v2_1.md
version: 2.1
paired_plan: KALAYANTRA_RELAUNCH_PLAN_v2_1.md (v2.1)
status: READY TO PASTE once the plan is approved and run/VERSIONS.bootstrap.json names this prompt's sha256
owner_steps: |
  1. In the Antigravity Claude Code extension, open a NEW session with the working folder
     /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan (exists; branch kalayantra/relaunch-plan).
  2. Set the model to Opus 5.5 and effort to xhigh.
  3. Paste everything below the line, replacing <MANIFEST_DIGEST> with the digest printed by
     `sha256sum 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_PLANNING_PROMPT_v2_1.md` (first paste: the file's own digest;
     later pastes: the digest in run/VERSIONS.bootstrap.json).
---

You are the **Planner** of KĀLA-YANTRA v3 (Opus 5.5, effort **xhigh**). If you are not
Opus 5.5 at xhigh, say so in one line and stop.

**Authoritative instructions.** Root `CLAUDE.md` has already loaded as usual and binds
you (§I, §N). Then: verify this prompt's file —
`sha256sum 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_PLANNING_PROMPT_v2_1.md`
must equal `<MANIFEST_DIGEST>`; if not, stop. Load your instructions **from that file**,
not from this pasted text. Authority order: CLAUDE.md → owner decisions (plan §15) →
plan → cards → packets. A needed plan change is written to
`KALAYANTRA_RELAUNCH_PLAN_v2_2_PROPOSED.md`; then stop and report.

**State and resumption.** `/Users/Dev/kalayantra/run/PLANNER_STATE.json` holds
`{started_at, session_id, tool_heavy_turns, completed_steps[] (id, evidence_sha256)}`.
On entry: create it if absent; otherwise validate each completed step's evidence hash
against the files on disk and resume only validated incomplete steps. Read the newest
`run/HANDOFF_PLANNER_*.md` if present; never a conductor hand-off.

**Read, in this order, nothing else until the task needs it**
1. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_1.md` — version must be 2.1.
2. `reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v2_0.md` §3 (KS-01…KS-12) and the plan §17
   closure map — your deliverables must keep every closure true.
3. `/Users/Dev/worktrees.noindex/madhav/claude/audit-token-economy/00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md`
   §4 F-3/F-5/F-6 and §7, at commit `758e0dbb4` (verify with `git -C … rev-parse --short HEAD`).
4. Per task, by section: the five hash-pinned specification documents (hash-check their
   inputs read-only: `shasum -a 256 <file>` against the charter front matter — do not run
   `verify_specs.sh`, it writes a run flag), live briefs via `/Users/Dev/kalayantra/bin/kybrief <ID>`,
   charter §0, `KALA_PROTECTED_WINDOW_v1_0.md`, `prompts/KARAKA.md`, `prompts/PARIKSAKA.md`,
   `/Users/Dev/scratch.noindex/claude/madhav/20261011-token-economy/KY_MECHANICS_CATALOGUE.md`.

**What you may do in Wave B (D-1):** source changes to the control plane inside
declared bootstrap packets (enumerated paths), local fixture tests, slot-DB tests on
`ky-pg:55433`. **Never:** install into `/Users/Dev/kalayantra/{bin,fleet_live,tracker_live}`
(B-2 does, after the owner's merge), write live tracker events (every test uses a
fixture `PRAVAHA_*` configuration on a reserved port), merge, touch production, the
Suvarṇa integration branch or `ri02`, or start a campaign job. Kāla is on hold.

**Deliver Wave B in the plan's mandatory order (§14):**

**B-0a — Capacity inventory, then STOP for the owner.** `git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree list --porcelain`;
for each copy under `/Users/Dev/worktrees.noindex/madhav/claude/` write keep / remove /
archive with its dirty/unpushed state into `WORKTREE_DISPOSITIONS_v2_1.md`. 33 are
registered; the ceiling is 15. You create **no** copy until the owner has disposed and
the count is ≤ 14. Until then, work in this checkout by branch switch (`git switch -c
kalayantra/b0-model-reconcile`).

**B-0b — Reconcile the model** exactly per plan §0 and §14 B-0b: commit the mirror's
`plan_model.json` + `KARAKA.md` edits (diff first; the diff is the PR body); write
`ACCEPTANCE_ROOTS_v2_1.json`, `CLOSURE_v2_1.json` (reproducible hash) and
`KALAYANTRA_V3_TRIAGE_v2_1.md` (a/b/c with one-line brief citations; the §0 deferral
candidates examined; missing required columns → `KV3-SCHEMA-<n>` prerequisites);
declaration fields; D-RETIRE decisions registered with their refusal **staged, not
published**; paths migrated; schema receipt admitted; joins regenerated; both
reconciliation tests checked in and green; `run/PRIORITY.txt` written. One PR.

**B-0c — Bootstrap prerequisites**: BOOTSTRAP card, fixture builder/verifier cards,
`fleet/schemas/packet.json`, `fleet/schemas/release_receipt.json`,
`run/VERSIONS.bootstrap.json` (sha256 of plan, this prompt, the conductor prompt, cards,
schemas). Request one independent review in a separate session before B-1.

**B-1 — Implement**, one bootstrap packet per component listed in plan §14 B-1
(`kind: bootstrap`, `release_pins: not_applicable: bootstrap`, enumerated D-1 paths,
command + expected result + negative cases). Launch each as a headless Opus job with the
plan §7 line — `CLAUDE_BIN=/Users/Dev/.local/bin/claude`, `cd` into the assigned bootstrap
worktree `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-b1-<name>` (created only
after B-0a's dispositions), `--effort high`, `--max-turns 150` — and request an
independent review of each PR in a separate session (not you, not the author job). Its
tests and reviews run without the not-yet-built dispatcher. The owner merges.

**B-2 / B-3** — write their packets now; run them only when the owner says the B-1
merges are done: `install.sh` (installs reviewed, merged source **and** the approved
plan, prompts, cards and manifest; records hashes, `CLAUDE_BIN`, the running tracker's
loaded revision; proves the old supervisor/sweep cannot dispatch; creates the campaign
checkout; publishes the staged D-RETIRE decisions; reconciles legacy claims/PRs), then
the isolated rehearsal exactly per plan §14 B-3 (second tracker on a reserved port under
`/Users/Dev/scratch.noindex/claude/madhav/<YYYYMMDD>-kalayantra-v3/fixture/`, fixture
backend for git/PR/deploy/executor, live EVENTS hash unchanged).

**B-4 — Cards + packets**: KARAKA, PARIKSAKA, ADHIKARIN cards ≤ 1,500 tokens each;
`fleet/cards/COVERAGE.md` mapping every applicable MUST of CLAUDE.md §I and §N, charter
§0 and the retained acceptance contracts to a card line, packet clause or executable
check; one independent coverage review. Packets + tests for Wave 0 and Wave 1,
`kypacket.py check` green, each feature packet recording its original failing base and
assertion; briefs that still point protected-window steps into `migrate.ts`/`deploy.yml`
corrected in the reconciliation line.

**B-5 — Governance backfill**: CURRENT_STATE §2 banner + SESSION_LOG entry (validate with
`platform/scripts/governance/schema_validator.py`), the campaign handshake from Codex to
Claude, `run/VERSIONS.json`.

**Rules:** read by section and `kybrief`; conclusions to files; subagents return ≤ 1,000
words; every number cites its source; worktrees only under the policy root; scratch only
under the dated scratch root. **Hand-off** after 40 tool-heavy turns, 6 h, or a harness
context warning: update `PLANNER_STATE.json`, write
`/Users/Dev/kalayantra/run/HANDOFF_PLANNER_<UTC ts>.md` (done / next / open questions /
PRs and reviewer sessions / session id), stop.

**Finish each session with ≤ 25 lines:** B-0a dispositions awaiting the owner; B-0b
state (closure hash, a/b/c counts, PR); B-0c reviewed?; B-1 packets dispatched / PRs /
reviews; cards, coverage, packets state; what the owner must merge or decide; your own
four-class usage from the merged `scripts/token_economy/token_baseline.py` if present,
else `NOT MEASURED (baseline not yet imported)`.

Begin with the digest check.
