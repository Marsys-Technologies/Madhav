# fleet/ — how the KĀLA-YANTRA fleet runs (operator notes)

Two processes, two shells, two environment files. Both run from a **snapshot** taken when they start, so nothing an agent edits in a working tree changes a running process.

| Process | Start | Environment file | Holds |
|---|---|---|---|
| executor | `source ~/.config/kalayantra/executor.env && bash fleet/executor.sh up` | `executor.env.example.sh` | the production credentials; nothing else does |
| fleet | `source ~/.config/kalayantra/fleet.env && bash fleet/kalayantra_fleet.sh up` | `fleet.env.example.sh` | no secrets (it refuses to start if one is present) |

- **Stop:** `bash fleet/kalayantra_fleet.sh down` (graceful) · `touch /Users/Dev/kalayantra/HOLD` (pause every lane at its next boundary) · `bash fleet/executor.sh down`.
- **Resume:** `rm /Users/Dev/kalayantra/HOLD` or `bash fleet/kalayantra_fleet.sh resume`. After a restart of the computer: start the executor, then `kalayantra_fleet.sh up` (the tracker restarts by itself).
- **Morning check:** `KY_STREAM=S /Users/Dev/kalayantra/bin/ky audit --since <ISO time>` (after bootstrap item B-2). It fails on duplicate claims, expired workers, rejected-but-done items, unmet dependencies, unbound production operations, or zero earned progress.
- **Pool size:** `/Users/Dev/kalayantra/run/KY_WORKERS` (absent or 0 = no implementation worker; the conductor writes 1 at launch acceptance and raises it to at most 6) and `run/KY_VERIFIERS` (1 until atomic claims land, then 2).
- **What the executor trusts:** only what is merged to `main` — its operations table (`executor_ops.json`) and every script are read from `origin/main`; a production operation runs in a private checkout of the reviewed, merged commit. After a merged change to `executor.py` itself: `executor.sh down`, then `up`.
- **What the tracker runs:** a snapshot of the selected package in `/Users/Dev/kalayantra/tracker_live`; `install_tracker.sh --gov <dir>` adopts a new one.

**Isolation hardening (optional; charter §15.1).** Agents run under the `madhav-parity` profile as your Unix user. To remove same-account access entirely: create a dedicated account, give it its own clone and Codex login, run the fleet there, and keep the executor and the read-only connection file in your account. The campaign runs without this and says so in its close report.
