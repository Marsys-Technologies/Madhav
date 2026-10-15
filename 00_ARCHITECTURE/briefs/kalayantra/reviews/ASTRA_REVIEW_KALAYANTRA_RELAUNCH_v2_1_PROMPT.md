# Confirmation review — KĀLA-YANTRA v3 relaunch plan v2.1 and paired prompts v2.1 (head {{HEAD}})

You are Astra. Your second review (ASTRA_REVIEW_KALAYANTRA_RELAUNCH v2.0 at 7f36181b5: REWORK, KS-01…KS-12) has been applied in full, using your replacement text, as plan **v2.1**, prompts **v2.1** and strategy **v1.2** (operative passages demoted to historical rationale). This is the **confirmation pass**: is it now safe for the owner to paste the planning prompt and begin Wave B, and — once Wave B is installed and the gate reads READY_TO_PASTE — to paste the conductor prompt? **Read-only:** no build, no DB connection, no tracker/fleet writes, no file writes; your review is your final message.

## Givens (do not re-litigate)
The owner's eight decisions and the three delegated calls D-1/D-2/D-3 (plan §15).

## Read — objects of review (worktree /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan, head {{HEAD}})
1. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_1.md` (primary; §17 maps KS-01…KS-12 to sections — test each claim).
2. `KALAYANTRA_V3_PLANNING_PROMPT_v2_1.md`, `KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_1.md`.
3. `KALAYANTRA_RELAUNCH_STRATEGY_v1_2.md` (confirm it no longer carries operative rules that conflict with the plan).
4. Your `reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v2_0.md` (your exact replacements) and `_v1_0.md`.

## Read — evidence and live mechanics (unchanged; read-only)
5. `/Users/Dev/worktrees.noindex/madhav/claude/audit-token-economy/00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md` at 758e0dbb4 (§4, §7).
6. `/Users/Dev/scratch.noindex/claude/madhav/20261011-token-economy/{notes_ky_state.md,notes_suvarna_state.md,KY_MECHANICS_CATALOGUE.md}`.
7. `/Users/Dev/kalayantra/bin/{ky,kybrief}`, `/Users/Dev/kalayantra/tracker_live/pravaha_tracker/*.py`, `/Users/Dev/kalayantra/fleet_live/{kalayantra_fleet.sh,claude_cycle.py,local_db.sh,precheck.sh,preflight.sh,finalize.sh,executor.py,executor_ops.json}`, `/Users/Dev/kalayantra/conductor/sweep.py`; repository `00_ARCHITECTURE/briefs/kalayantra/fleet/` where it differs.
8. `/Users/Dev/kalayantra/run/`: `ls`, `cat HOLD_MERGES`, `tail -n 60 EVENTS.jsonl`, `ls claims/`.
9. In the relaunch worktree: charter §0, `KALA_PROTECTED_WINDOW_v1_0.md`, `prompts/*.md`, `00_ARCHITECTURE/control/kalayantra/plan_model.json` (`control_plane`, `streams`, items J-0c/J-0d/J-0/J-0m/J-4p/K0-SV/K9-23/KA-1e/K1-2/K6-4 with `brief`), root `CLAUDE.md` §I/§N, `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §2, `.github/workflows/ci.yml` (job names), `00_ARCHITECTURE/WORKTREE_ISOLATION_PROTOCOL_v1_0.md`.
10. `git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree list --porcelain | grep -c 'worktrees.noindex/madhav/claude'`; `ls -l /Users/Dev/.local/bin/claude`.

Claude Code CLI facts (verified, 2.1.239): `-p`, `--bare`, `--effort`, `--model`, `--max-turns`, `--disallowedTools`, `--permission-mode bypassPermissions`, `--output-format stream-json --verbose`, `--add-dir`, `--strict-mcp-config`, `--mcp-config`. `--bare` + CLAUDE.md loading unverified (plan §7 treats it as unknown; B-3 tests it). Harness: one tool call ≤ 600 000 ms.

## Decide

**Part 1 — Closure of KS-01…KS-12** (`CLOSED` / `PARTLY` / `OPEN` / `REGRESSED`, with section/line evidence and one sentence; exact replacement where not CLOSED). Confirm also that KR-01…KR-12 remain closed.

**Part 2 — Launch walk, command by command, against v2.1:** (a) planning prompt: digest check → state file → read order → B-0a (inventory, STOP for owner, branch switch) → B-0b (roots, closure, two reconciliation tests, staged D-RETIRE, paths, schema receipt, joins) → B-0c → B-1 launch line (CLAUDE_BIN, cwd, bootstrap packet with release_pins not_applicable, independence from the dispatcher) → B-2 (install receipt, loaded tracker revision, old supervisor stopped, staged decisions published, legacy reconciliation) → B-3 (second tracker on a reserved port; override-preserving wrapper; fixture backend; acceptance) → B-4 → B-5. Name the first instruction that cannot be followed as written. (b) gate: `--pre-resume`/`READY_TO_PASTE`, receipt binding, resume after version validation and lock, hold ownership. (c) conductor prompt: digest → kyversion → kylock → state init → OWNER_RESUME → full gate → start-dispatcher → both inboxes with correct acks → wait/counters → first tick (precedence, freshness, admission checks) → first BUILD (claim, base contains prerequisite heads, allocator, test installation, admission classification) → `ky review` → VERIFY (no item claim, item lock, enforced boundary, controller-published verdict) → MERGE (registered head guard, squash) → COMPLETE (final PR head vs squash commit) → POST-READBACK path → finalisation (DRAIN_RECEIPT → C-3, FINAL_RECEIPT → C-4). Name the first command that fails or does the wrong thing.

**Part 3 — Essential governance and security:** anything still cut that a correct, honest campaign needs; anything kept that is ceremony without a detector; any conflict with CLAUDE.md §I/§N or the FROZEN contract.

**Part 4 — Token economy, honestly:** remaining silent-spend risks; confirm the plan makes no unearned savings claim.

**Part 5 — Quality and signal honesty:** remaining §N.8 risks; verifier bar; routing on KA-1e/K1-2/K6-4 and a `platform/src/lib/auth/**` diff; packet rules that could mislead.

**Part 6 — The prompts as artifacts:** self-sufficient; pairing enforceable as now stated; hand-off executable; contradictions; anything a Claude Code session cannot carry out.

## Answer format
Frontmatter: `artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH`, `version: "2.1"`, `verdict: PROCEED | PROCEED-WITH-FIXES | REWORK`, `blocking_count`, `reviewed_commit: {{HEAD}}`, `review_date`, `review_mode: read-only`.

Then only: (1) the verdict in ≤ 5 lines; (2) the Part 1 closure table (KS and a one-line KR confirmation); (3) findings — at most eight, `KT-01…`, severity (BLOCKING before the planning paste; HIGH before the conductor paste; MEDIUM; LOW), location, defect in two sentences, failure, **exact replacement**; (4) Parts 2–6 in ≤ 25 lines each; (5) what you could not verify and why. `PROCEED` only with no BLOCKING and a complete Part 2 walk; `PROCEED-WITH-FIXES` only when every fix is a written replacement the planner can apply in B-0c before any job runs.
