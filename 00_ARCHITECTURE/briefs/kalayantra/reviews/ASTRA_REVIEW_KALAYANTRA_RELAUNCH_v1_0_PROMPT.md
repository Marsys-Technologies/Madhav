# Independent review — KĀLA-YANTRA v3 relaunch plan, strategy and paired prompts (head b16b4e24c)

You are Astra. You reviewed the KĀLA-YANTRA execution design three times before launch (v1.0: 27 findings; v1.1 REWORK KZ-01…KZ-13; v1.2 confirmation) and the K0a / K12 packets. That campaign ran 2026-10-06 → 10-10 and is now on hold. The owner has asked for your review of the **relaunch** before anything is kicked off. **Read-only:** run no build, open no database connection, start no fleet or tracker command that writes, write no file. Your review is your final message.

## Owner decisions — givens, do not re-litigate (flag risks only)
1. Everything runs in Claude (Claude Code CLI); no Codex in any campaign role; no local model.
2. Opus 5.5 high for conductor, ADHIKĀRIN, verifier and escalation builder; planner Opus 5.5 xhigh; builders Sonnet 5.5 high.
3. 3 builders + 2 verifiers standing, scaling up on demand when there is work.
4. Re-scope to the critical path ("Kāla serves chart 482012f1 end-to-end with certification mappings"); defer the rest; disposition inherited Pravāha material.
5. The five-part Suvarṇa exit signal is the launch gate.
6. No token caps or budgets; usage is measured and reported.
7. ADHIKĀRIN is an on-demand job, not a standing lane.
8. The campaign is started by the owner pasting a prompt into an interactive Claude Code session (Antigravity extension); workers are headless `claude -p` jobs.

## Read — the documents under review (worktree /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan, head b16b4e24c)
1. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v1_0.md` — the plan (primary object of review).
2. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_PLANNING_PROMPT_v1_0.md` and `KALAYANTRA_V3_CONDUCTOR_PROMPT_v1_0.md` — the two paired prompts the owner will paste.
3. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_STRATEGY_v1_0.md` — the strategy the plan implements.

## Read — the evidence the plan rests on (test it; do not trust it)
4. `/Users/Dev/worktrees.noindex/madhav/claude/audit-token-economy/00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md` (§2 baseline, §4 findings F-1…F-10, §5 roster, §7 frontier globs) and `TOKEN_ECONOMY_PLAN_v1_0.md` (W1-1…W1-8) in the same folder, head 758e0dbb4.
5. Scratch notes from the audit sweeps, `/Users/Dev/scratch.noindex/claude/madhav/20261011-token-economy/`: `notes_ky_state.md` (campaign inventory, velocity, hurdles, waste, reusable vs stale), `notes_suvarna_state.md` (wrap-up checklist, dependencies), `notes_workflow.md` (fleet mechanics and idle analysis), `KY_MECHANICS_CATALOGUE.md` (exact `ky`/fleet syntax and the gaps for an event-driven dispatcher). Numbers in these notes are the audit's; verify the ones the plan relies on against the live sources below.

## Read — the live mechanics the plan must drive correctly (read-only)
6. `/Users/Dev/kalayantra/bin/ky`, `/Users/Dev/kalayantra/bin/kybrief`, `/Users/Dev/kalayantra/tracker_live/pravaha_tracker/cli.py` (and the modules it imports: claims, verdicts, state), `/Users/Dev/kalayantra/fleet_live/{kalayantra_fleet.sh,claude_cycle.py,local_db.sh,precheck.sh,preflight.sh,verify_specs.sh,finalize.sh}`, `/Users/Dev/kalayantra/conductor/{sweep.py,sweep_loop.sh,feed.py}`.
7. `/Users/Dev/kalayantra/run/`: `ls` only, plus `head -c 4000` of `DIGEST.md`, `HOLD_MERGES`, and the last 50 lines of `EVENTS.jsonl` (it is multi-MB; never read it whole; use grep/tail).
8. In the relaunch worktree: `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md` (by section: §0, §3, §5, §7, §11, §15), `KALAYANTRA_VELOCITY_AMENDMENT_v1_0.md`, `KALAYANTRA_INTERACTIVE_CONDUCTOR_PROMPT_v1_0.md` (the previous conductor prompt), `KALA_PROTECTED_WINDOW_v1_0.md`, `prompts/{KARAKA,PARIKSAKA,ADHIKARIN,SUTRADHARA}.md`, `fleet/README.md`, and `00_ARCHITECTURE/control/kalayantra/plan_model.json` (`control_plane`, `streams[].worktrees`, three sample items with `brief`).
9. `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan/CLAUDE.md` §I, §N.2, §N.8 (the project's build standards the plan must not violate), and `00_ARCHITECTURE/WORKTREE_ISOLATION_PROTOCOL_v1_0.md` plus the owner's worktree policy quoted in the plan §4.1.

Claude Code CLI facts you may rely on (verified on this machine, `claude --help`, version 2.1.239): flags `-p`, `--bare` ("minimal mode: skip hooks, LSP, plugin --settings, --agents, --plugin-dir"), `--effort <level>`, `--model`, `--max-turns`, `--disallowedTools`, `--permission-mode bypassPermissions`, `--output-format stream-json --verbose`, `--add-dir`, `--strict-mcp-config`, `--mcp-config`, `--setting-sources`, `--no-session-persistence`, `-w/--worktree`. Whether `--bare` also skips CLAUDE.md is **not verified** — treat it as unknown and say what the plan should do about it.

## Decide

**Part 1 — Does the plan address what actually went wrong?** For each measured hurdle in `notes_ky_state.md` §3 (idle/chatter cycling; the Suvarṇa hold; verifier rework and its classes; the migration-1320 lane-DB baseline; the 1330 outage → protected window; brief/scope friction and parks; census conflicts; Suvarṇa coupling; the LOCAL_ONLY incident) and each token finding the plan cites (F-1, F-3, F-5, F-6): `ADDRESSED`, `PARTLY`, `NOT ADDRESSED`, `WRONG REMEDY`, with the plan section and one sentence of reasoning. Then say which of the 102 remaining items you expect the re-scope to drop, if you can tell from the briefs.

**Part 2 — Walk the launch path in your head, command by command.** (a) The owner pastes the PLANNING prompt: step 1 → F. Name the first instruction that cannot be followed as written (missing file, wrong path, wrong `ky` syntax, a flag that does not exist, a worktree-policy breach, a read that would blow the context). (b) Wave B items B3-1 … B3-9 as specified in plan §7: which can an Opus headless job actually complete from that specification, and which lack an acceptance that can be tested? (c) The gate `kygate.sh` §2: are the five conditions machine-checkable with what exists; which one has no source of truth today? (d) The owner pastes the CONDUCTOR prompt: Setup → Start-up 1–5 → the wait call → the first dispatcher tick → the first BUILD job → its `ky claim`/`ky review` → the first VERIFY job → `ky verdict` → MERGE. Name the first command that fails or does the wrong thing. Include: `ky inbox --stream S --wait 1200 --json` semantics (exit 1 on empty; does `--wait` behave as the prompt assumes?), the claim lease and renewal by the dispatcher as a different process with `KY_LANE=<slot>`, verdict stream `V` identity rules when the verifier is a slot `v1..v4`, `ky done` guards (deploy containment) for code-only items, `HOLD_MERGES` and `$KY/HOLD` precedence, the per-branch worktree shared by builder and verifier jobs (one copy per branch) and the 15-worktree ceiling, slot DBs vs `local_db.sh db <lane>` expectations, `preflight.sh launch` expecting 13 worktrees and 11 lane DBs, and `streams[].worktrees[]` in the plan model (preflight checks cwd against them).

**Part 3 — Token economy, honestly.** Will this design cut tokens per accepted item, and where could it silently spend more (e.g. the planner session itself, re-pasting the packet on every turn of a job, Opus verifier reading beyond the diff, the conductor's wait call, worker transcripts left on, escalation ping-pong)? Give your estimate's basis or say it cannot be estimated.

**Part 4 — Quality and signal honesty.** Where does the plan risk a §N.8 violation (a status without a detector), a lowered verification bar, Sonnet building something that should be frontier-by-rule (test the globs in audit §7 against three real K items' `owns`), or a packet that could mislead a builder more than a pointer would?

**Part 5 — The two prompts as artifacts.** Are they self-sufficient for a fresh session that has read nothing else? Is the pairing rule enforceable? Is the hand-off rule executable by the model (it cannot read its own context size)? Is anything in them contradicted by the plan or by CLAUDE.md?

## Answer format
Frontmatter: `artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH`, `version: "1.0"`, `verdict: PROCEED | PROCEED-WITH-FIXES | REWORK`, `blocking_count`, `reviewed_commit: b16b4e24c`, `review_date`, `review_mode: read-only`.

Then only: (1) the verdict in at most five lines; (2) the Part 1 table; (3) findings — **at most twelve**, numbered `KR-01…`, each with severity (BLOCKING = must be fixed before the planning prompt is pasted; HIGH = before the conductor prompt is pasted; MEDIUM; LOW), file:line (or §), the defect in two sentences, the failure it would cause, and the **exact replacement text or command**; (4) Parts 2–5 in at most 30 lines each, pointing to findings rather than repeating them; (5) what you could not verify and why. A finding without a location and a replacement is not a finding. `PROCEED` only if nothing is BLOCKING and you have walked Part 2 end to end.
