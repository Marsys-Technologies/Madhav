# Confirmation review — KĀLA-YANTRA v3 relaunch plan v2.5 at head {{HEAD}}

You are Astra. Your confirmation review of v2.4 (at fcbc06437: PROCEED-WITH-FIXES, KW-01…KW-06) has been applied in full with your replacement text as plan **v2.5** and cockpit prompt **v2.5** (the owner-decisions record gained a clarifying line on bundle-change authorisation; the surrogate agent definition is unchanged from fcbc06437). **Confirmation pass, read-only** (no builds, no tracker/fleet writes, no file writes); your review is your final message. The cockpit session continues B-0c in parallel.

## Givens (do not re-litigate)
Owner decisions 1–8, D-1…D-9 and Q1–Q4 in `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md`.

## Read (worktree /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan, head {{HEAD}})
1. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_5.md` — pairing rule, §2, §4a, §6 (SURROGATE row), §11, §13, §14 (Wave B heading, B-2), §15, §16, §17.
2. `KALAYANTRA_V3_COCKPIT_PROMPT_v2_5.md` (steps 1–8), `KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md`, `.claude/agents/kalayantra-owner-surrogate.md`.
3. Your `reviews/ASTRA_REVIEW_KALAYANTRA_RELAUNCH_v2_4.md`.
4. Live state: `/Users/Dev/kalayantra/run/PLANNER_STATE.json`, `ls /Users/Dev/kalayantra/run/{actions,awaiting,commands,loops,locks,QUALIFICATIONS} 2>/dev/null`, `/Users/Dev/kalayantra/run/HOLD_MERGES`; `git log --oneline -5 kalayantra/b0-model-reconcile`; `git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree list --porcelain | grep -c 'worktrees.noindex/madhav/claude'`.
5. Mechanics as before where needed (`tracker_live/pravaha_tracker/*.py`, `fleet_live/*`, root `CLAUDE.md` §I/§L/§N, `deploy.yml`, `claude --help`).

## Decide
**Part 1 — Closure of KW-01…KW-06** (`CLOSED` / `PARTLY` / `OPEN` / `REGRESSED`, evidence, one sentence; exact replacement where not CLOSED); confirm KV-01…KV-08 remain closed or state regressions; KU-01…KU-03 and P-1/P-2 carried.
**Part 2 — Fresh-session walk of cockpit steps 1–8 against the live run/ state** (root-commit instruction load; successor-chain evaluation with no records present; the legacy migration under the planner fence; observer vs writer behaviour), then the first `kyboot.py`-supervised B-1 launch, B-2 receipt-bound install without a merge, B-5 activation record, a successor-bundle activation and the next fresh cockpit entry through the chain, the first conductor controller iteration with a child job, one veto-class decision end to end, and one `approve-window` report through readback. Name the first instruction that cannot be followed as written.
**Part 3 — Owner directions** (resume-anywhere / autonomy with surrogate / zero idle): ADDRESSED, PARTLY or WRONG REMEDY.
**Part 4 — Token economy:** any remaining path to repeated unproductive spend.
**Part 5 — Signal honesty:** any remaining status without a detector.

## Answer format
Frontmatter: `artifact: ASTRA_REVIEW_KALAYANTRA_RELAUNCH`, `version: "2.5"`, `verdict: PROCEED | PROCEED-WITH-FIXES | REWORK`, `blocking_count`, `reviewed_commit: {{HEAD}}`, `review_date`, `review_mode: read-only`. Then: (1) verdict ≤ 5 lines; (2) Part 1 table; (3) findings ≤ 5, `KX-01…`, severity (BLOCKING before B-1; HIGH before conductor activation; MEDIUM; LOW), location, defect in two sentences, failure, **exact replacement**; (4) Parts 2–5 ≤ 20 lines each; (5) what you could not verify. `PROCEED` only with no BLOCKING and a complete Part 2 walk.
