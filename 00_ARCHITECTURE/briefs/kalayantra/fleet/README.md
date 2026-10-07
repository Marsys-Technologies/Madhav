# fleet/ — how the KĀLA-YANTRA fleet runs (operator notes)

**Normal launch: paste the kickoff prompt into Codex** (`KALAYANTRA_KICKOFF_PROMPT_v1_0.md`, owner steps in its header); it starts both processes below. The commands here are for manual recovery.

Two processes, two environment files. Both run from a **snapshot** taken when they start, so nothing an agent edits in a working tree changes a running process.

| Process | Start | Environment file | Holds |
|---|---|---|---|
| executor | `source ~/.config/kalayantra/executor.env && bash fleet/executor.sh up` | `executor.env.example.sh` | the production credentials; nothing else does |
| fleet | `source ~/.config/kalayantra/fleet.env && bash fleet/kalayantra_fleet.sh up` | `fleet.env.example.sh` | no secrets (it refuses to start if one is present) |

- **Stop:** `bash fleet/kalayantra_fleet.sh down` (graceful) · `touch /Users/Dev/kalayantra/HOLD` (pause every lane at its next boundary) · `bash fleet/executor.sh down`.
- **Resume:** `rm /Users/Dev/kalayantra/HOLD` or `bash fleet/kalayantra_fleet.sh resume`. After a restart of the computer: start the executor, then `kalayantra_fleet.sh up` (the tracker restarts by itself).
- **Morning check:** `KY_STREAM=S /Users/Dev/kalayantra/bin/ky audit --since <ISO time>` (after bootstrap item B-2). It fails on duplicate claims, expired workers, rejected-but-done items, unmet dependencies, unbound production operations, or zero earned progress.
- **Pool size:** `/Users/Dev/kalayantra/run/KY_WORKERS` (absent or 0 = no implementation worker; the conductor writes 1 at launch acceptance and raises it to at most 6) and `run/KY_VERIFIERS` (1 until atomic claims land, then 2).
- **What the executor trusts:** only what is merged to `main` — `up` snapshots `executor.py` from `origin/main`, and the running executor re-hands-over only to compiled `origin/main` bytes when no work is active. Its operations table (`executor_ops.json`) and every script are likewise read from `origin/main`; a production operation runs in a private checkout of the reviewed, merged commit. A retained production fence is preserved and permits handover only with a verifier's request-bound quiescence receipt. The capabilities record exposes the active executor and main revisions; a refresh failure closes new-work admission.
- **What a lane can see:** `bash fleet/kalayantra_fleet.sh smoke` starts a real worker and a real reviewer under the exact lane environment and fails if the profile does not load, a model is refused, a tool is missing, or a credential-like variable reaches a command. The campaign's Codex profile (`~/.codex/kalayantra.config.toml`) is regenerated before every cycle from your base configuration with every personal MCP server and plugin switched off.
- **Rehearsal without spending anything:** `KY_DRY_RUN=1 bash fleet/kalayantra_fleet.sh up` runs the supervisor end to end (reservations, prompts, locks, spacing, stop) and calls no model; `down` afterwards, and make sure no `kalayantra_fleet.sh lane` process remains before a real `up` (a running dry-run loop would hold the lane's lock).
- **What the tracker runs:** a snapshot of the selected package in `/Users/Dev/kalayantra/tracker_live`; `install_tracker.sh --gov <dir>` adopts a new one.

**Isolation hardening (optional; charter §15.1).** Agents run with approvals off and full access (the `madhav-parity` posture, through the generated `kalayantra` profile) as your Unix user. To remove same-account access entirely: create a dedicated account, give it its own clone and Codex login, run the fleet there, and keep the executor and the read-only connection file in your account. The campaign runs without this and says so in its close report.
