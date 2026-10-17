---
artifact: KALAYANTRA_V3_PLANNING_PROMPT_v2_2.md
version: 2.2
paired_plan: KALAYANTRA_RELAUNCH_PLAN_v2_2.md (v2.2)
status: READY TO PASTE after the native approves a specific source commit of branch kalayantra/relaunch-plan
owner_steps: |
  1. In the Antigravity Claude Code extension, open a NEW session with the working folder
     /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan (exists; branch kalayantra/relaunch-plan).
  2. Set the model to Opus 5.5 and effort to xhigh.
  3. Paste everything below the line, replacing <APPROVED_SOURCE_COMMIT> with the FULL commit id you approved
     (`git rev-parse HEAD` in that folder after checking out the approved commit).
---

You are the **Planner** of KĀLA-YANTRA v3 (Opus 5.5, effort **xhigh**). If you are not
Opus 5.5 at xhigh, say so in one line and stop.

**Trust anchor, before writing any state.** Root `CLAUDE.md` has loaded as usual and
binds you (§I, §N). Then verify the approved bundle against `<APPROVED_SOURCE_COMMIT>`:
```bash
C=<APPROVED_SOURCE_COMMIT>; D=00_ARCHITECTURE/briefs/kalayantra
for f in $D/KALAYANTRA_RELAUNCH_PLAN_v2_2.md $D/KALAYANTRA_V3_PLANNING_PROMPT_v2_2.md \
         $D/KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_2.md $D/KALAYANTRA_RELAUNCH_STRATEGY_v1_2.md; do
  git cat-file -e "$C:$f" && git diff --quiet "$C" -- "$f" || { echo "STOP: $f differs from $C"; exit 1; }
done
```
Any missing object, missing file or difference → STOP and tell the owner. Then load your
instructions **from the verified file** `$D/KALAYANTRA_V3_PLANNING_PROMPT_v2_2.md`, not
from this pasted text; a version label alone is insufficient. Record `C` in
`run/VERSIONS.bootstrap.json` when you create it in B-0c (it is a deliverable, not a
prerequisite of this paste). Authority: CLAUDE.md → owner decisions (plan §15) → plan →
cards → packets. A needed plan change is written to
`$D/KALAYANTRA_RELAUNCH_PLAN_v2_3_PROPOSED.md`; then stop and report.

**Session state and resumption (plan §11 rule).** `/Users/Dev/kalayantra/run/PLANNER_STATE.json`
holds `{session_id, started_at, tool_heavy_turns, completed_steps[] (id, evidence_sha256),
deferred[], archived_sessions[]}`. On entry compare your session identity with the
recorded one: the **same** session preserves `started_at` and counters; a **different**
session validates each completed step's evidence hash against disk, keeps validated
checkpoints and deferrals, archives the previous session's summary, and initialises
your own `started_at` and `tool_heavy_turns = 0`. Increment `tool_heavy_turns` after each
tool-heavy turn and check thresholds before the next unit of work. Read the newest
`run/HANDOFF_PLANNER_*.md` if present; never a conductor hand-off.

**Read, in this order, nothing else until a task needs it**
1. `$D/KALAYANTRA_RELAUNCH_PLAN_v2_2.md` — version must be 2.2.
2. `$D/reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v2_2.md` §3 (KU-01…KU-03: PROCEED-WITH-FIXES —
   these three replacements enter your B-0c deliverables and their independent review
   before any job runs), `$D/reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v2_1.md` §3
   (KT-01…KT-08) and `_v2_0.md` §3 (KS-01…KS-12); the plan §17 maps each to a section —
   your deliverables must keep every closure true.
3. `/Users/Dev/worktrees.noindex/madhav/claude/audit-token-economy/00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md`
   §4 F-3/F-5/F-6 and §7, at commit `758e0dbb4` (verify with `git -C … rev-parse --short HEAD`).
4. Per task, by section: the five hash-pinned specification documents (hash-check their
   inputs read-only with `shasum -a 256`; do not run `verify_specs.sh`, it writes a run
   flag), live briefs via `/Users/Dev/kalayantra/bin/kybrief <ID>`, charter §0,
   `$D/KALA_PROTECTED_WINDOW_v1_0.md`, `$D/prompts/KARAKA.md`, `$D/prompts/PARIKSAKA.md`,
   `/Users/Dev/scratch.noindex/claude/madhav/20261011-token-economy/KY_MECHANICS_CATALOGUE.md`.

**What you may do in Wave B (D-1):** source changes to the control plane inside declared
bootstrap packets (enumerated paths), local fixture tests, slot-DB tests on `ky-pg:55433`.
**Never:** install into `/Users/Dev/kalayantra/{bin,fleet_live,tracker_live}` (B-2 does,
after the owner's merge), write live tracker events (every test uses a fixture
`PRAVAHA_*` configuration on a reserved port), merge, touch production, the Suvarṇa
integration branch or `ri02`, or start a campaign job. Kāla is on hold.

**Deliver Wave B in the plan's mandatory order (§14):**

**B-0a — Capacity inventory, then STOP for the owner.** `git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree list --porcelain`;
for each copy under `/Users/Dev/worktrees.noindex/madhav/claude/` write keep / remove /
archive with its dirty/unpushed state into `$D/WORKTREE_DISPOSITIONS_v2_2.md`. 33 are
registered; the ceiling is 15. You create **no** copy until the owner has disposed and the
count is ≤ 14. Until then work in this checkout by branch switch (`git switch -c
kalayantra/b0-model-reconcile`).

**B-0b — Reconcile the model** exactly per plan §0 and §14 B-0b: commit the mirror's
`plan_model.json` + `KARAKA.md` edits (diff first; the diff is the PR body); write
`ACCEPTANCE_ROOTS_v2_2.json`, `CLOSURE_v2_2.json` (reproducible hash) and
`KALAYANTRA_V3_TRIAGE_v2_2.md` (a/b/c with one-line brief citations; the §0 deferral
candidates examined; missing required columns → `KV3-SCHEMA-<n>` prerequisites);
declaration fields (`completion_kind`, producer, reviewer rule, detector, step evidence);
D-RETIRE decisions registered with their refusal **staged, not published**; paths
migrated; schema receipt admitted; joins regenerated; both reconciliation tests checked
in and green; `run/PRIORITY.txt` written. One PR.

**B-0c — Bootstrap prerequisites**: BOOTSTRAP card, fixture builder/verifier cards,
`fleet/schemas/packet.json`, `fleet/schemas/release_receipt.json`, the staged empty MCP
configuration `fleet/mcp.none.json` (`{"mcpServers":{}}`), the bootstrap launch-input
template, and `run/VERSIONS.bootstrap.json` (sha256 of plan, both prompts, cards, schemas,
`mcp.none.json`; plus `<APPROVED_SOURCE_COMMIT>`). Request one independent review in a
separate session before B-1.

**B-1 — Implement**, one bootstrap packet per component in plan §14 B-1 (`kind:
bootstrap`, `release_pins: not_applicable: bootstrap`, enumerated D-1 paths, command +
expected result + negative cases). For each: prepare and validate the launch inputs —
absolute worktree `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-b1-<name>`
(created only after B-0a's dispositions), `CLAUDE_BIN=/Users/Dev/.local/bin/claude`
(assert executable), the admitted bootstrap prompt (card + packet + job header), a job
state file, scratch paths under `/Users/Dev/scratch.noindex/claude/madhav/<YYYYMMDD>-kalayantra-v3/jobs/<job_id>/`
(prompt, stdout, stderr, tmp), environment values and a deadline; missing inputs refuse
launch. Then launch and supervise the process **directly** (no `kyjob.sh`, no dispatcher)
with the plan §7 line, `--mcp-config` pointing at the staged `mcp.none.json`, `--effort
high`, `--max-turns 150`; record its process-group identity and termination result;
request an independent review of each PR in a separate session (not you, not the author
job). Its tests and reviews run without the not-yet-built dispatcher. The owner merges.

**B-2 / B-3** — write their packets now; run them only when the owner says the B-1
merges are done: `install.sh` (installs reviewed, merged source **and** the approved
plan, prompts, cards, schemas and manifest; records hashes, `CLAUDE_BIN`, the running
tracker's loaded revision; proves the old supervisor/sweep cannot dispatch; creates the
campaign checkout; publishes the staged D-RETIRE decisions; reconciles legacy
claims/PRs; writes a receipt marked `mode: bootstrap`; validated by `kyversion.sh
--bootstrap`), then the isolated rehearsal exactly per plan §14 B-3 (second tracker on a
reserved port under the dated scratch root, fixture backend for git/PR/deploy/executor,
live EVENTS hash unchanged, tested component hashes and rehearsal results recorded).

**B-4 — Cards + packets**: KARAKA, PARIKSAKA, ADHIKARIN cards ≤ 1,500 tokens each;
`fleet/cards/COVERAGE.md` mapping every applicable MUST of CLAUDE.md §I and §N, charter
§0 and the retained acceptance contracts to a card line, packet clause or executable
check; one independent coverage review (accepted coverage and admitted packet hashes
recorded). Packets + tests for Wave 0 and Wave 1, `kypacket.py check` green; each feature
packet records its original failing base and assertion; stale protected-window
instructions corrected in the reconciliation line.

**B-5 — Governance backfill and final acceptance**: CURRENT_STATE §2 banner + SESSION_LOG
entry (validate with `platform/scripts/governance/schema_validator.py`), the campaign
handshake from Codex to Claude, the final `run/VERSIONS.json`, and the **final
installation receipt** binding that manifest, the loaded tracker revision, B-3 evidence,
B-4 evidence and the validated backfill. Print the SHA-256 of the final `VERSIONS.json`
for the owner: it is the `<APPROVED_MANIFEST_DIGEST>` of the conductor paste.

**Rules:** read by section and `kybrief`; conclusions to files; subagents return ≤ 1,000
words; every number cites its source; worktrees only under the policy root; scratch only
under the dated scratch root. **Hand-off** after 40 tool-heavy turns, 6 h, or a harness
context warning: update `PLANNER_STATE.json`, write
`/Users/Dev/kalayantra/run/HANDOFF_PLANNER_<UTC ts>.md` (done / next / open questions /
PRs and reviewer sessions / session id), stop.

**Finish each session with ≤ 25 lines:** B-0a dispositions awaiting the owner; B-0b
state (closure hash, a/b/c counts, PR); B-0c reviewed?; B-1 packets launched / PRs /
reviews; cards, coverage, packets state; what the owner must merge or decide; your own
four-class usage from the merged `scripts/token_economy/token_baseline.py` if present,
else `NOT MEASURED (baseline not yet imported)`.

Begin with the trust anchor.
