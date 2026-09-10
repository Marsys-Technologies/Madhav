# Paripraśna Swarm Tracker — human digest

Regenerated at wave boundaries from `SWARM_TRACKER.json`. For the live view, open
`tracker.html` in a browser (self-contained, no server; auto-refreshes every 30s).

## Current wave: P0-IGNITION

**Step 0 (retire prior attempt, land planning set):**

- 0a Lease announcement — DONE (`origin/campaign-coordination @ 0f4408ac4`)
- 0b Worktree + docs — DONE (`pariprashna/p0` from `origin/main @ a7136b467`)
- 0c PR land — PR open, CI running: https://github.com/Marsys-Technologies/Madhav/pull/1346
- 0d Retire old refs (`pariprashna/g0-close`, `pariprashna/p0-ignition`) — PENDING (after 0c merges)
- 0e Tracker — this file + `SWARM_TRACKER.json` + `tracker_data.js` + `tracker.html`, IN PROGRESS

**P0 lanes (not yet started):**

| Lane | Name | Stage |
|---|---|---|
| P0-B | Environment (worktree farm, cloud-sql-proxy, template test-DB, migration allocator, flag registry) | queued |
| P0-C | Ports refactor of `route.ts` (RF-1, gating lane) | queued |
| P0-D | Tracker scaffold | in_progress |
| P0-E | Design-plan grounding pass | queued |
| P0-F | DD-2 anthropic delist + DD-3 infra probes | queued |

**Prior-attempt findings carried forward (not re-probed):** see `prior_attempt` block in
`SWARM_TRACKER.json`. Summary: G0/PR #1341 merged clean; two governance-gate regressions
found+fixed there and pre-empted here; `gh`/`gcloud` auth both confirmed live.

**Still owed by P0-B:** `cloud-sql-proxy`, template test-DB, migration-number allocator, flag registry.
