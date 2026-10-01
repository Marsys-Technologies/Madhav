---
artifact: NIRMANA_ENGINE_HANDOFF_FROM_NIKASHA
version: "1.0"
status: OPEN — two register rows owned by this campaign, relayed from Nikaṣa
produced_on: 2026-09-27
from: campaign nikasha-test (/Users/Dev/madhav-nikasha, campaign/nikasha-test @ 8b90c8d7d, PR #2736)
per: NIKASHA_CHANGE_REGISTER_v2_0.md v2.1 §2.9 (R216, R217); D1 ruling 2026-09-27 (nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md v2.1)
---

# Hand-off from Nikaṣa — read at session open (R215 discipline)

Two rows in the Nikaṣa register are engine-surface work and are owned here. Nikaṣa did not write into this worktree beyond this file.

| row | what | evidence | where it lands |
|---|---|---|---|
| **R217** | `build_runs.last_error` is never written by `mark_run_state` (`runner.py:408–425`: `UPDATE build_runs SET state = %s[, ended_at = NOW()] WHERE id = %s`) on the failed-assets path (:1450), the exception path (:1456) or the writer-gap path (:1240). Only `_terminalize_preflight_failure` (:327) and the TypeScript `terminalizeFailedRun` / watchdog CTEs write it. This is the residual behind the **288 of 419** failed runs with empty `last_error` — A2 fixed the asset grain (`build_run_assets.error`), not the run grain. | GPT-6 Astra review D1.1, verified by Fable reconciliation (`mark_run_state` executed against an in-memory cursor: no error assignment on any failed path) | an A2c packet, or B2 if you prefer — your call; Nikaṣa's P1 acceptance query (`state='failed' AND last_error empty → 0 for post-build runs`) is the proof |
| **R216** | `platform/scripts/governance/asset_census.py` is changed by B1 (`17e5a1257`, +75 lines: blocked-dependency classification + tests) and will be changed again by Nikaṣa P4/P6. Nikaṣa's P4 rebases on B1's census diff **first** and keeps B1's census tests green. | `git show --stat 17e5a1257` | nothing for you to do unless B1's census hunk changes again — if it does, note it in EVENTS so Nikaṣa re-rebases |

**Also for your awareness:** engine D-1 (b) and D-2 (a) were confirmed as the adopted options in the Nikaṣa D1 ruling — consistent with your `73385d72f`. And the Nikaṣa D5 revision (2.1) measured the build DAG: `build_dependencies` is a dead pre-rename table (ids `A1`/`A10`, layer `L25`, zero overlap with `asset_registry.depends_on`) — if any engine surface reads it, that is R219.
