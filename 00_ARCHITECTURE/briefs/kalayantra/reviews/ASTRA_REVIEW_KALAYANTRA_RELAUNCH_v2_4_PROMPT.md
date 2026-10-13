# Confirmation review — KĀLA-YANTRA v3 relaunch plan v2.4 (autonomy model) at head {{HEAD}}

You are Astra. Your delta review of v2.3 (at a5c0bef2a: REWORK, KV-01…KV-06 blocking before B-1, KV-07/KV-08 high before the conductor) has been applied in full with your replacement text as plan **v2.4**, cockpit prompt **v2.4**, an updated surrogate agent definition, and amendments to the owner-decisions record (D-4 amended: the GitHub protected-environment approval is human and owner-only; D-6 revised: no merges to main during the certification hold; D-9: install from reviewed immutable branch heads). **Confirmation pass, read-only** (no builds, no tracker/fleet writes, no file writes); your review is your final message. The cockpit session continues B-0c in parallel; your findings are folded into B-0c before any B-1 launch.

## Givens (do not re-litigate)
Owner decisions 1–8, D-1…D-9 and Q1–Q4 in `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md`.

## Read (worktree /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan, head {{HEAD}})
1. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_4.md` — front matter (pairing rule), §4a, §6, §7, §10, §11, §13 (signals), §14 B-0c/B-1/B-2, §15, §16, §17.
2. `KALAYANTRA_V3_COCKPIT_PROMPT_v2_4.md`, `KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md`, `.claude/agents/kalayantra-owner-surrogate.md`.
3. Your `reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v2_3.md` and `_v2_2.md`.
4. Live state: `/Users/Dev/kalayantra/run/{PLANNER_STATE.json,JOURNAL_PLANNER.md (if present),HOLD_MERGES}`, `ls /Users/Dev/kalayantra/run/{actions,awaiting,commands,loops,QUALIFICATIONS} 2>/dev/null`; `git log --oneline -6 kalayantra/b0-model-reconcile`.
5. Mechanics as before: `/Users/Dev/kalayantra/tracker_live/pravaha_tracker/*.py` (esp. cli.py decision publication, state.py decision projection), `/Users/Dev/kalayantra/fleet_live/*`, root `CLAUDE.md` §I/§L/§N, `.github/workflows/deploy.yml`, `KALA_PROTECTED_WINDOW_v1_0.md`, `claude --help` (2.1.296), `/bin/launchctl`.

## Decide
**Part 1 — Closure of KV-01…KV-08** (`CLOSED` / `PARTLY` / `OPEN` / `REGRESSED`, section/line evidence, one sentence; exact replacement where not CLOSED), and whether KU-01…KU-03 and P-1/P-2 remain correctly carried.
**Part 2 — Walk the cockpit prompt steps 1–8 on a fresh session against the live run/ state** (including the one-time checkpoint migration), then the first `kyboot.py`-supervised B-1 launch, B-2 install from a reviewed head, B-3, B-5 activation record, the first `kyloop.py conductor` iteration (controller waits, batch launch), one veto-class decision through PENDING_VETO → EFFECTIVE via the `veto` controller, and one protected-window request reaching the external approval dependency. Name the first instruction that cannot be followed as written.
**Part 3 — Owner directions:** resume-anywhere / autonomy with surrogate / zero idle — ADDRESSED, PARTLY or WRONG REMEDY now?
**Part 4 — Token economy:** any remaining path to unbounded or repeated unproductive spend (loop restarts, surrogate ping-pong, cockpit + controller duplication, empty-inbox model turns)? Name the guard or the gap.
**Part 5 — Signal honesty:** any status in §13's signal table or elsewhere still without a detector.

## Answer format
Frontmatter: `artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH`, `version: "2.4"`, `verdict: PROCEED | PROCEED-WITH-FIXES | REWORK`, `blocking_count`, `reviewed_commit: {{HEAD}}`, `review_date`, `review_mode: read-only`. Then: (1) verdict ≤ 5 lines; (2) Part 1 table; (3) findings ≤ 6, `KW-01…`, severity (BLOCKING before B-1; HIGH before conductor activation; MEDIUM; LOW), location, defect in two sentences, failure, **exact replacement**; (4) Parts 2–5 ≤ 20 lines each; (5) what you could not verify. `PROCEED` only with no BLOCKING and a complete Part 2 walk; `PROCEED-WITH-FIXES` only when every fix is a written replacement the cockpit can apply in B-0c before any B-1 launch.
