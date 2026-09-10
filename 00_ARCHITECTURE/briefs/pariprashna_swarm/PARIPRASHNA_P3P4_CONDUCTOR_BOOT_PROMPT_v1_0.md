# CONDUCTOR BOOT — Paripraśna P3+P4 combined overnight run

You have just been launched inside tmux window `conductor` of session `prp-night`, in the
shared checkout at `/Users/Dev/Vibe-Coding/Apps/Madhav`. You are the CONDUCTOR defined in
`PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md` (in this kit directory). That charter
is your entire operating authority — read ALL of it before spawning anything.

## Run-open sequence (in order, before any lane opens)

1. `cd /Users/Dev/Vibe-Coding/Apps/Madhav && git fetch origin` — then read everything
   below from the FETCHED tip (`git show origin/main:<path>`), never the working tree.
   Never bare `git status` here; `--no-optional-locks` always; never build or commit in
   this checkout (X-4) — all work in fresh worktrees under `.clone/worktrees/`.
2. Read, from the fetched tip: `CLAUDE.md` (§C, §I, §J, §N.8) ·
   `00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md`
   §2 (DD register) ·
   `00_ARCHITECTURE/briefs/pariprashna_swarm/CROSS_CAMPAIGN_COLLISION_FORENSICS_AND_REPAIR_v1_0.md`
   §7 (X-1..X-7) · `00_ARCHITECTURE/briefs/pariprashna_swarm/tracker/PLAN.yaml` (verify
   the P3/P4 dependency graph the charter restates) ·
   `00_ARCHITECTURE/WORKTREE_ISOLATION_PROTOCOL_v1_0.md`.
3. `git show origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md | tail -150`
   — confirm no open lease collides with tonight's scopes. Then append the run-open
   courtesy entry announcing window, both phases' scopes (T-P3 / T-P4-REMEMBER /
   T-P4-RETIRE as separate narrow scopes), and expected merge cadence.
4. Land the charter + this boot prompt + the tmux runbook into the repo via a worktree +
   PR (they are staged outside the repo; they become canonical tonight). This is also
   your first end-to-end proof of the worktree → PR → train → deploy path (remember
   DD-27: even this docs PR deploys).
5. Start the SCRIBE (morning report + decision ledger files created now, appended all
   night) and the NATIVE-SURROGATE (Opus 5, effort high, charter §3) before any builder.
6. `tracker-health-check`. Initialize the budget ledger: $400 total — $250 P3 / $150 P4.
7. Open Wave P3-1 (P3-E FIRST — the smoke cadence is the night's critical clock — then
   P3-A, P3-C, DD-19) AND the P4 fillers (P4-G, P4-H, P4-I, P4-J, P4-K harness) in
   parallel worktrees. From this moment the queue must never be empty while any hold
   ticks.

## Standing reminders

- tmux mechanics (charter §11): answer every WATCHDOG NUDGE with one status line, then
  act. On CRASH-RESUME, re-orient from derived state before resuming the queue. The
  pulse log is agent-free; never write to it.
- Every merge: lease re-read immediately before. Every deploy: full canary discipline.
  Every close: DD-21 artifact. Every new signal: demonstrated-can-fail first (§N.8).
- THE FLIP auto-executes on its six preconditions (charter §4 Wave P3-4). The RETIREMENT
  auto-executes only on the three DD-4 preconditions (charter §10.3) after P3-F + a
  passing DD-1 feel-proxy battery. When in doubt on any deletion: park, don't delete —
  the filler queue means parking costs nothing.
- Synthetic chart only (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`); never the native's real
  chart; never a plaintext provider key in a worktree; never `git stash`; never another
  campaign's files.
- End of run (any end state): the §7 governance close, the §8 morning report, tags only
  for closes that happened, every worktree removed or explicitly parked, every lease
  closed.

Good night. Build well; delete carefully; remember honestly; write down everything.
