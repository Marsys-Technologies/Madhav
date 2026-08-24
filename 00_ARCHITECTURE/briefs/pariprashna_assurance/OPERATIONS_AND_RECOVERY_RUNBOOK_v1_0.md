---
artifact: PARIPRASHNA_ASSURANCE_OPERATIONS_AND_RECOVERY_RUNBOOK
version: 1.0
status: CURRENT
date: 2026-08-24
---

# Operations and recovery runbook

Use an approved runtime path outside the repository; no generated database, snapshot, or
dashboard state is committed. For a local proof:

```sh
TRACKER_RUNTIME=/private/tmp/pariprashna-assurance-demo
python3 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/cli.py --runtime "$TRACKER_RUNTIME" provision-credentials
TRACKER_INTEGRATOR_TOKEN=$(jq -r '.tokens.integrator' "$TRACKER_RUNTIME/local-credentials.json")
python3 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/cli.py --runtime "$TRACKER_RUNTIME" init --token "$TRACKER_INTEGRATOR_TOKEN"
python3 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/server.py --runtime "$TRACKER_RUNTIME"
```

The server binds `127.0.0.1:8787` by default. `provision-credentials` creates random,
per-runtime actor tokens in a mode-0600 runtime file and refuses to overwrite it. The CLI
requires the matching provisioned token for bootstrap or event emission; HTTP writes require
the same token. Dashboard reads are deliberately unauthenticated only on the loopback proof
service. Production authentication, host exposure, backup policy, token issuance, and
release remain A3 decisions.

## Recovery

1. Stop the process; do not edit `events`.
2. Run `cli.py --runtime "$TRACKER_RUNTIME" verify`.
3. If the materialized projection is missing or mismatched, call `POST /api/rebuild` with
   an authorized integrator token, or restart the service; it replays the event log.
4. If replay fails, preserve the database read-only, export a filesystem copy, and open an
   integrity incident. Do not delete or rewrite rows.
5. Export an immutable snapshot only after a successful replay:
   `cli.py --runtime "$TRACKER_RUNTIME" snapshot --path /approved/path/snapshot.json`.

The rejected-event queue is an audit surface, not an error log to clear. Corrections are
new events referencing the original evidence.
