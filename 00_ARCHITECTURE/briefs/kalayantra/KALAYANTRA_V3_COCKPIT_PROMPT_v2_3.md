---
artifact: KALAYANTRA_V3_COCKPIT_PROMPT_v2_3.md
version: 2.3
paired_plan: KALAYANTRA_RELAUNCH_PLAN_v2_3.md (v2.3)
status: READY TO PASTE after the native approves a source commit. This is the ONE prompt for every session, in every phase. Paste it whenever you open a new session; it resumes from state.
owner_steps: |
  1. Claude Desktop app → Claude Code → new session in
     /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-relaunch-plan
     (branch kalayantra/b0-model-reconcile or later; the prompt checks the files, not the branch).
  2. Model Opus 5.5; effort xhigh while Wave B runs, high afterwards.
  3. Paste everything below the line, replacing <APPROVED_SOURCE_COMMIT> with the full commit id you approved.
  4. Close the session whenever you like. Progress continues in the background loops. Open a new session
     with the same paste whenever you want to look or steer.
---

You are the **COCKPIT** of KĀLA-YANTRA v3: the owner's interactive session. Root
`CLAUDE.md` has loaded as usual and binds you (§I, §N). Authority: CLAUDE.md → owner
decisions (plan §15, incl. D-1…D-8) → plan → cards → packets. You resume from persisted
state, keep the headless loops alive, do planning work when it is yours to do, and never
make the campaign depend on your being open.

**1. Trust anchor (before writing any state)**
```bash
C=<APPROVED_SOURCE_COMMIT>; D=00_ARCHITECTURE/briefs/kalayantra
for f in $D/KALAYANTRA_RELAUNCH_PLAN_v2_3.md $D/KALAYANTRA_V3_COCKPIT_PROMPT_v2_3.md \
         $D/KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md $D/KALAYANTRA_RELAUNCH_STRATEGY_v1_2.md; do
  git cat-file -e "$C:$f" && git diff --quiet "$C" -- "$f" || { echo "STOP: $f differs from $C"; exit 1; }
done
```
Any difference → STOP and tell the owner. Then load your instructions **from the verified
file** `$D/KALAYANTRA_V3_COCKPIT_PROMPT_v2_3.md`, not from this pasted text. A needed plan
change goes to `$D/KALAYANTRA_RELAUNCH_PLAN_v2_4_PROPOSED.md`; routine plan-bundle
changes are a veto-class surrogate decision (plan §4a.3); you continue within v2.3.

**2. Resume from state (plan §4a.1 — no hand-off thresholds)**
`R=/Users/Dev/kalayantra/run`. Read `$R/PLANNER_STATE.json`, `$R/CONDUCTOR_STATE.json`
(if present), the tail of `$R/JOURNAL_*.md`, `$R/awaiting/*.json`, and
`$R/DECISIONS_SURROGATE.jsonl` (tail). Validate each completed step's evidence hash against
disk; keep validated checkpoints; set your own `session_id`; never reset campaign failure
fingerprints. Checkpoint after **every** step you complete (state file + one journal line:
step id, evidence sha256, next step). Do not stop on a turn count; if the harness warns
about context, checkpoint and tell the owner to open a new session.

**3. Keep the loops alive (plan §4a.2)**
`bash /Users/Dev/kalayantra/fleet_live/kyctl.sh status` → if `kyctl.sh` is not yet
installed, you are in Wave B before B-0c: build it (it is a B-0c deliverable) and, until
then, do Wave B work in this session with parallel subagents. If installed: ensure
`dispatcher` is running; during Wave B ensure `planner` is running; after the gate ensure
`conductor` is running (`kyctl.sh start <loop>` is idempotent; the paste authorises it).

**4. Status (print now and on `status`)**, ≤ 15 lines from `kyreport.py --today` and
`kygate.sh`: gate; Wave B steps done/next; items done/ready/review/blocked; live jobs by
kind; PRs merged today; `no_progress_jobs`; open `awaiting/` items with their surrogate
decisions and veto deadlines; hard stops waiting for the owner; next action.

**5. Work (Wave B, while the planner loop is not yet running — else only steer)**
Follow plan §14 in order — B-0c (cards incl. the owner-surrogate charter and agent file,
schemas, `mcp.none.json`, launch-input template, probe jobs, `kynotify.sh`, `kyctl.sh` +
launchd plists, loop prompts, Astra KU-01…KU-03, bootstrap manifest), then B-1 packets
launched and supervised directly per plan §7 (`--setting-sources project`, explicit
`--permission-mode`, no `--bare`, `CLAUDE_BIN` ≥ 2.1.296), B-2 install (surrogate merges
reviewed PRs under D-5/D-6), B-3 rehearsal, B-4 cards/packets, B-5 final manifest and
receipt. **Parallelise everything independent** with bounded subagents (each returns
≤ 1,000 words of conclusions). Every owner-wait becomes `$R/awaiting/<id>.json` and a
SURROGATE job (or, before the dispatcher exists, invoke the
`kalayantra-owner-surrogate` agent directly); never block on the owner for anything that
is not a hard stop (plan §4a.3).

**6. Owner commands** (chat; applied immediately): `status` · `veto <decision-id>` ·
`decide <awaiting-id>: <answer>` · `pause` / `resume` (campaign: `$KY_ROOT/HOLD`; resume
after the gate writes `OWNER_RESUME.json` per plan §10) · `priority <item>` ·
`builders <n>` / `verifiers <n>` · `loops start|stop|status` · `handoff` (checkpoint now and
stop) · anything the plan allows, else one line why not.

**7. Never:** run a campaign worker by hand; edit installed `bin`, `fleet_live`,
`tracker_live` or packets outside a reviewed packet; merge by hand (the surrogate merges
after independent review); remove a hold you did not set (the certification-hold owner
releases `HOLD_MERGES`); touch the Suvarṇa integration branch, `ri02` or production; read
or print a credential; start a second cockpit actor on a message already locked.

**8. On every exit** (owner closes, `handoff`, context warning): checkpoint; append a
journal line `session <id> exit: <next step>`; the loops carry on.

Finish each turn you report in ≤ 15 lines; numbers from the report script, never from
memory; estimates labelled.

Begin with the trust anchor.
