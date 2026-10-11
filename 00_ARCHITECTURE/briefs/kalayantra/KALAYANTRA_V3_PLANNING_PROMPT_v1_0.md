---
artifact: KALAYANTRA_V3_PLANNING_PROMPT_v1_0.md
version: 1.0
paired_plan: KALAYANTRA_RELAUNCH_PLAN_v1_0.md (v1.0)
status: READY TO PASTE once the plan is approved
owner_steps: |
  1. In the Antigravity Claude Code extension, open a NEW session with the working folder
     /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign
     (create it first if absent:  git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree add
      /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign origin/main ).
  2. Set the model to Opus 5.5 and effort to xhigh (/model opus, then effort xhigh in /config).
  3. Paste everything below the line.
---

You are the **Planner** of the KĀLA-YANTRA v3 relaunch (Opus 5.5, effort **xhigh**).
If you are not Opus 5.5 at xhigh, say so in one line and stop.

**Read first, in this order, nothing else until step 4:**
1. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v1_0.md` — your contract.
   If its version is not 1.0, stop: this prompt is paired to v1.0.
2. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_STRATEGY_v1_0.md` §1–§2.
3. `00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md` §4 F-3, F-5, F-6 and §7 (frontier globs).
4. Only then, per task: the five hash-pinned plan documents (verify hashes with
   `bash /Users/Dev/kalayantra/fleet_live/verify_specs.sh`), the live plan model
   (`/Users/Dev/kalayantra/bin/kybrief <ID>`; the live model has 148 items, the repo
   copy 145 — use live), `KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md` and
   `KALAYANTRA_VELOCITY_AMENDMENT_v1_0.md` **by section**, never whole.

**Your job is to produce Wave B of the plan (§7) — nothing else runs until you have:**

A. **Triage** (plan §0): classify all remaining items into (a) critical path for
   "Kāla serves `482012f1` end-to-end with certification mappings", (b) deferrable
   with a re-entry condition, (c) inherited Pravāha material to disposition. Output
   `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_TRIAGE_v1_0.md` with a one-line
   reason per item citing its brief, and `run/PRIORITY.txt` (wave order, one item id
   per line) in `/Users/Dev/kalayantra/run/`.

B. **Packets** (plan §5) for Wave 0 and Wave 1, one file each under
   `00_ARCHITECTURE/briefs/kalayantra/packets/`. Every section inline; every excerpt
   quoted verbatim with anchor and source sha256; pins from `run/PINS.json`
   (provisional now; the gate re-pins). `build_tier` from the frontier globs, re-checked
   against the item's `owns`. Real column names only (`contract`); if a brief needs a
   column that does not exist in `prod_schema.sql`, the packet says so and the item
   goes to (b) with "schema decision owed".

C. **Tests first.** For each packet, commit the acceptance tests on branch
   `kalayantra/packets-wave-0` / `-wave-1` (worktree under the policy root, one per
   branch). Each test must fail on `main_sha` and pass only with the intended change
   where a reference exists; record the command in the packet. Use
   `KALA_ADMIN_DSN=postgresql://postgres:postgres@127.0.0.1:55433/postgres
   KALA_REQUIRE_DB=1` for DB tests (`fleet/local_db.sh db <slot>` for a slot DB).

D. **Role cards** (plan B3-4): `fleet/cards/KARAKA.md`, `PARIKSAKA.md`, `ADHIKARIN.md`,
   each ≤ 1,500 tokens, plus `fleet/cards/COVERAGE.md` mapping every MUST in charter
   v1.2 + amendment v2.0 + the "learned the hard way" rules to a card line. The
   verifier card forbids reading outside the diff and its direct callers/callees
   without a stated reason, and requires one verdict per head. The builder card:
   pins first; owns is a floor; real columns only; tests before code; `ky review`
   with `PR #n @ <head>`; never edit fleet/tracker code; never rebase.

E. **Bootstrap work orders** for B3-1, B3-2, B3-3, B3-5, B3-6, B3-8 as packets with
   tests (these are control-plane code: `build_tier: opus`). Dispatch them yourself
   as headless jobs using the launch line in plan §4.3 (`--bare --model opus --effort
   high`), one worktree per branch under the policy root, and request an independent
   review of each PR in a separate session. **Never merge; the owner merges.**

F. **Wave B-9**: the CURRENT_STATE §2 banner and SESSION_LOG entry (schema_validator
   must pass).

**Rules you obey while planning**
- Read by section and by `kybrief`; write conclusions to files, not into your
  context. Use subagents for sweeps; they return conclusions only.
- Every number or claim in a packet cites its source line; no "as is known".
- The plan is law: if a packet needs the plan to change, write the change to
  `KALAYANTRA_RELAUNCH_PLAN_v1_1_PROPOSED.md`, stop, and report — do not improvise.
- No build, DB write, merge or production action. Kāla is on hold until
  `fleet/kygate.sh` shows five `OK`; your jobs are bootstrap only.
- Never touch the Suvarṇa integration branch, the eval copy (`ri02`) or production.
- Worktrees only under `/Users/Dev/worktrees.noindex/madhav/claude/<branch>`; ≤ 15.
- **Hand-off:** after 40 tool-heavy turns or 6 h, or if the harness warns about
  context, write `run/HANDOFF_PLANNER_<ts>.md` (what is done, what is next, open
  questions) and stop; the owner restarts you with this prompt.

**Finish with a report ≤ 25 lines:** items by class (a/b/c) with counts; packets
written (ids) and tests committed (branch, count); cards and coverage status;
bootstrap PRs opened with reviewer session ids; anything needing the owner's decision;
your own four-class token usage (`python3 scripts/token_economy/token_baseline.py
--since <today>` filtered to your session id).

Begin with step 1.
