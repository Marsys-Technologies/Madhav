# Second review — KĀLA-YANTRA v3 relaunch plan v2.0 and paired prompts v2.0 (head {{HEAD}})

You are Astra. Your first review (ASTRA_REVIEW_KALAYANTRA_RELAUNCH v1.0 at b16b4e24c: REWORK, KR-01…KR-12) led the owner to withdraw plan v1.0 and have it **rebuilt from scratch** as v2.0, with three decisions the owner delegated and the author took on the owner's behalf (plan §15: D-1 control-plane changes permitted in Wave B under review + install receipt; D-2 rework as v2.0; D-3 the N-467 stop is lifted by the owner's act of pasting the conductor prompt, recorded machine-checkably). **Read-only:** run no build, open no database connection, start no fleet/tracker command that writes, write no file. Your review is your final message.

## Givens (do not re-litigate; flag risks only)
The owner's eight decisions as listed in plan §15 (all Claude; roster; 3+2 scaling on demand; re-scope to the critical path; the five-part gate; no token caps; ADHIKĀRIN on demand; launch by paste), plus D-1, D-2, D-3.

## Read — the objects of review (worktree /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan, head {{HEAD}})
1. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_0.md` — primary.
2. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_PLANNING_PROMPT_v2_0.md` and `KALAYANTRA_V3_CONDUCTOR_PROMPT_v2_0.md`.
3. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_STRATEGY_v1_1.md` (operative passages corrected).
4. Your own `reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v1_0.md` and the plan's §17 closure map — test every closure claim; do not trust it.

## Read — evidence and live mechanics (same as your first review; read-only)
5. `/Users/Dev/worktrees.noindex/madhav/claude/audit-token-economy/00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md` at 758e0dbb4 (§4, §7).
6. `/Users/Dev/scratch.noindex/claude/madhav/20261011-token-economy/{notes_ky_state.md,notes_suvarna_state.md,notes_workflow.md,KY_MECHANICS_CATALOGUE.md}`.
7. `/Users/Dev/kalayantra/bin/{ky,kybrief}`, `/Users/Dev/kalayantra/tracker_live/pravaha_tracker/*.py` (cli, claims, verdicts, completion, state), `/Users/Dev/kalayantra/fleet_live/{kalayantra_fleet.sh,claude_cycle.py,local_db.sh,precheck.sh,preflight.sh,verify_specs.sh,finalize.sh,executor.py,executor_ops.json}`, `/Users/Dev/kalayantra/conductor/sweep.py`; the repository copies under `00_ARCHITECTURE/briefs/kalayantra/fleet/` where they differ.
8. `/Users/Dev/kalayantra/run/`: `ls`, `head -c 4000 DIGEST.md`, `cat HOLD_MERGES`, `tail -n 60 EVENTS.jsonl` (never the whole file), `ls claims/`.
9. In the relaunch worktree: charter §0/§3/§5/§7/§11, `KALAYANTRA_VELOCITY_AMENDMENT_v1_0.md`, `KALA_PROTECTED_WINDOW_v1_0.md`, `prompts/*.md`, `00_ARCHITECTURE/control/kalayantra/plan_model.json` (`control_plane`, `streams`, three items with `brief`, the `join`/`requires_outcome` fields), root `CLAUDE.md` §I/§N, `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §2 (the FROZEN list), `00_ARCHITECTURE/WORKTREE_ISOLATION_PROTOCOL_v1_0.md`.
10. `git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree list --porcelain | grep -c 'worktrees.noindex/madhav/claude'` (capacity reality).

Claude Code CLI facts (verified, version 2.1.239): `-p`, `--bare`, `--effort`, `--model`, `--max-turns`, `--disallowedTools`, `--permission-mode bypassPermissions`, `--output-format stream-json --verbose`, `--add-dir`, `--strict-mcp-config`, `--mcp-config`, `--setting-sources`, `--no-session-persistence`. Whether `--bare` skips CLAUDE.md is unverified (the plan §7 treats it as unknown and tests it in B-3). The interactive harness caps a single tool call at 600 000 ms (the conductor prompt uses `--wait 540`).

## Decide

**Part 1 — Closure of KR-01…KR-12.** For each: `CLOSED`, `PARTLY`, `OPEN`, or `REGRESSED`, with the plan/prompt section and file:line (or §) evidence, and one sentence. Where PARTLY/OPEN, the exact replacement text.

**Part 2 — Walk the launch path again, command by command,** against v2.0: (a) PLANNING prompt steps 1–5 and B-0…B-5 — the first instruction that cannot be followed as written; whether B-0's closure computation is specifiable from the model's fields (`depends_on`, `steps`, `join`, `requires_outcome`, `accepts_not_applicable_dependencies`) and whether "semantic equivalence at a fixed EVENTS boundary" is testable; whether B-1's packets can each be built and accepted by an Opus headless job from the detectors named; whether the B-2 install receipt and B-3 isolated dry run (fixture `PRAVAHA_EVENTS` root, `--mock-merge`) are achievable with the tracker as it exists (does `PRAVAHA_EVENTS` override suffice to isolate; does the tracker server need a second instance/port?). (b) The gate: is `run/RELEASE_RECEIPT.json` + `run/OWNER_RESUME.json` a sound evidence contract; which condition still lacks a producer; is the STOP/HOLD precedence right. (c) CONDUCTOR prompt Setup → Start-up 1–9 → wait → first dispatcher tick → first BUILD (claim as K slot, worktree creation, test installation, `base_sha`, allocator) → `ky review` → first VERIFY (no item claim; job lock; read-only boundary; `git status` check) → `ky verdict` as `KY_STREAM=V KY_LANE=v1` → MERGE (`gh pr merge --auto --squash` — is squash compatible with `ky done --reviewed-head` and merge-only inheritance? say exactly) → COMPLETE via typed `ky done` (deploy containment for code-only items) → POST-DEPLOY. Name the first command that fails or does the wrong thing.

**Part 3 — Essential governance and security.** The owner asked for "only essential governance and security; cut everything extraneous; single-pointed focus on accurate, high-velocity implementation". Judge plan §3: is anything **cut** that a correct, honest campaign needs (name it and why), and is anything **kept** that is ceremony without a detector (name it and the exact deletion)? Does any cut violate root CLAUDE.md §I/§N or the FROZEN contract?

**Part 4 — Token economy, honestly.** Does v2.0 address your Part 3 regressions (packet re-sent per turn, Opus verifier traversal, planner sweeps, repeated A–F after hand-off, forced liveness, escalation ping-pong, transcript double counting)? Where could it still silently spend more? Basis or "cannot be estimated".

**Part 5 — Quality and signal honesty.** §N.8 risks remaining (gate lines, dispositions, progress figures, report acceptance, finalizer), the verifier bar (diff-first with item tests/mutations/compat; evidence-aware re-review), routing on real `owns` (re-test KA-1e, K1-2, K6-4 against §9 as written), and whether any packet rule could still mislead a builder.

**Part 6 — The prompts as artifacts.** Self-sufficient for a fresh session? Pairing enforceable (`kyversion.sh` hashes)? Hand-off executable (persisted counters)? Any contradiction with the plan or CLAUDE.md? Any instruction a Claude Code session cannot carry out (tool timeouts, background processes, chat commands)?

## Answer format
Frontmatter: `artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH`, `version: "2.0"`, `verdict: PROCEED | PROCEED-WITH-FIXES | REWORK`, `blocking_count`, `reviewed_commit: {{HEAD}}`, `review_date`, `review_mode: read-only`.

Then only: (1) the verdict in at most five lines; (2) the Part 1 closure table; (3) findings — at most twelve, numbered `KS-01…`, each with severity (BLOCKING = before the planning prompt is pasted; HIGH = before the conductor prompt is pasted; MEDIUM; LOW), location, the defect in two sentences, the failure, and the **exact replacement**; (4) Parts 2–6 in at most 30 lines each, pointing to findings; (5) what you could not verify and why. `PROCEED` only if nothing is BLOCKING and you walked Part 2 end to end; `PROCEED-WITH-FIXES` only if every fix is a replacement you have written out.
