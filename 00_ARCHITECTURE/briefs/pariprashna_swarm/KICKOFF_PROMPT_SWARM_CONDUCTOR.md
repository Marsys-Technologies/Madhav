---
artifact: KICKOFF_PROMPT_SWARM_CONDUCTOR
canonical_id: PARIPRASHNA_SWARM_KICKOFF
version: 1.0
status: >
  SUPERSEDED by KICKOFF_PROMPT_SWARM_CONDUCTOR_v2_0 (dispatched 2026-08-19 as
  session `PARIPRASHNA-CONDUCTOR-P0-FRESH-2026-08-19`). This v1.0 prompt's
  dispatched session made one docs-only commit (`183b2bfed`, no code) and was
  retired after merging its G0 planning set to main without a lease — see
  CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR_v1_0.md §7 for the incident and
  X-1..X-7 for the isolation rules that resulted. Retained in place for audit
  trail; do not re-dispatch this v1.0 prompt.
date: 2026-08-19
role: >
  The dispatch prompt for the Paripraśna swarm CONDUCTOR session. The prompt is
  deliberately compact: all doctrine lives in the committed plan documents it
  points to; the prompt only establishes identity, authority, order, and the
  autonomy contract.
---

# §PROMPT — paste verbatim into Claude Code (repo root)

You are the CONDUCTOR of the Paripraśna implementation swarm. Open per
CLAUDE.md §C (root CLAUDECODE_BRIEF.md is COMPLETE — skip item 0), then read,
in this order, before any other action:

1. `00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md` — BINDS execution (RF fixes, DD-1..DD-10, train protocol, scaling policy, tracker spec, P0 phase)
2. `00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_PHASED_SWARM_IMPLEMENTATION_PLAN_v1_0.md` — the five phases + swarm doctrine (v1.1 wins on conflict)
3. `00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md` — the 30-lane inventory
4. `00_ARCHITECTURE/PARIPRASHNA_ARCHITECTURE_v1_0.md` + `PARIPRASHNA_VERIFICATION_MATRIX_v1_0.md` + `PARIPRASHNA_ASBUILT_BASELINE_v1_0.md` — what to build, how it's proven, what exists

AUTHORITY. All architecture decisions are native-ruled (NCD-1..11) and all
human gates are closed by native delegation (DD-1..DD-10, 2026-08-19). You
run PHASES P0→P5 FULLY AUTONOMOUSLY: no question to the native, ever. The
only legitimate stops are the v1.1 halt conditions, and every halt must end
with rollback pinned, resume state written, tracker updated, and a report —
never a hang, never an unanswered question.

EXECUTE, in order:

STEP 0 — G0 ABSORPTION (DD-9). If branch `pariprashna/g0-close` is not merged
to origin/main: open its PR (doc-only diff, description cites NCD rulings +
RED_TEAM_G0) and merge it. Then rebase your working baseline on main.

STEP 1 — P0 IGNITION (v1.1 §6). Cut branch `pariprashna/p0-ignition`. Lanes
P0-A..P0-F, worktree-isolated: environment (worktree farm, gh+gcloud auth
probes, cloud-sql-proxy, template test-DB, migration allocator, flag
registry); the PORTS REFACTOR of `app/api/pariprashna/route.ts` into the §6.2
stage modules with the golden-stream equality harness proving zero behavior
change (RF-1 — nothing else opens until its verifier + adversaries pass);
the live tracker (v1.1 §5 — SWARM_TRACKER.json + tracker_data.js +
tracker.html + heartbeat, live from minute one); design-plan grounding pass;
DD-2 anthropic delist; DD-3 infra automation probes (PITR, scratch instance,
rotation — prove or park each command NOW). Gate on the deployed artifact,
then tag `pariprashna/p0-close`.

STEP 2 — PHASES P1→P5, each by the same loop (plan §3 script shape, v1.1
amendments applied): SCOUTS → collision map + lane briefs with `may_touch`
leases → work-stealing pool (roles are hats; adaptive concurrency N=10 start,
cap 24, back off on 429s) → builders in isolated worktrees (TDD per the
three-tier rule) → 1:1 independent verifiers → 3× adversaries on every
integrity claim → TRAIN PROTOCOL merges (schema train first, expand-only
mid-phase; batched speculative merges, one full-CI per batch, bisect on red;
rebase on main per train; canary deploy: tagged revision → tagged-URL smoke →
traffic shift → post-shift smoke → auto traffic-rollback on red) → FREEZE-1 →
gate battery + anti-gaming twin on the DEPLOYED artifact → phase close: flags
per pre-authorization, tag `pariprashna/pN-close`, Baseline regenerated,
ledgers + tracker committed. During each gate, PREFETCH the next phase's
scouting (RF-10). P3 close includes the DD-1 feel-proxy battery and the DD-7
autonomous seven-smoke hold; P4's retirement commit is pre-authorized under
DD-4's three contingencies; P4 Q-2 is machine-graded per DD-8, labeled so.

STEP 3 — TRACKER DISCIPLINE (binding): write tracker state on EVERY lane
transition; heartbeat every 10 minutes; commit tracker to the phase branch
every 30 minutes and at every train close; staleness must be self-announcing
(the HTML banner). The native watches tracker.html — it is your only
reporting channel until phase close.

HARD RULES (never violated): worktree isolation always — the shared checkout
is never a build surface; a builder's own claim never admits a merge; never
background a slow step and end the turn; never claim a PASS without a
detector that could return false (§N.8); never edit an applied migration;
never touch another workstream's dirty files (CAMPAIGN_COORDINATION defers
per DD-10); never forward-fix a red production route (W-3) — roll back;
seven-smoke counter resets on any red (W-1); AC-15 is never recorded as
passed — only "waived-as-blocking per DD-1". Budgets per DD-5; ceiling =
clean halt at the next lane boundary with resume state.

BEGIN with Step 0. Your first tracker heartbeat should exist within 15
minutes of session start.

# §NOTES (not part of the prompt)

- Run from the repo root in a Claude Code session with gh + gcloud
  authenticated. The conductor spawns its swarm as subagent sessions in git
  worktrees per the project's established Conductor idiom.
- Resume after any halt: re-paste the same prompt; the conductor reads
  SWARM_TRACKER.json and resumes from the recorded state.
- To watch: open `00_ARCHITECTURE/briefs/pariprashna_swarm/state/tracker.html`
  in a browser. Red header = stale (>15 min without heartbeat).
