# Removing the program tracker at program close

The tracker is **ephemeral**. At Platform Modernization close, delete it with one filesystem call and (if deployed) one service delete. No other code depends on it.

## Local removal

```bash
rm -rf tools/program-tracker/
```

That's the entire footprint:
- `tools/program-tracker/` (this directory) — server, collector, UI, tests, state
- Nothing under `platform/`, `platform-mcp/`, `platform/migrations/`, or `00_ARCHITECTURE/` imports it.

Verify zero coupling:
```bash
grep -rIn "program-tracker" platform/ platform-mcp/   # expect no hits
```

## Optional Cloud Run service

If a tracker service was deployed alongside the program (per BRIEF_0t "Hosting"):
```bash
gcloud run services delete amjis-tracker --region=asia-south1 --quiet
```

That removes the Cloud Run revision + URL. No GCS bucket, no Secret Manager entry, no IAM role belongs to the tracker — it reads `program_status.json` from disk (or GCS) and writes nothing back to the program.

## Why this is safe

- The tracker is **read-only** w.r.t. the program (`session_queue.yaml`, `PROGRAM_STATE.md`, `gate_status.json`).
- It does not modify the build, the database, or any deployed app.
- Its only writes are to `tools/program-tracker/.state/` (gate status emitters, log mirrors).
- It exposes no mutation endpoints (`/status.json` and `/events` are read-only; `/healthz` is a string).

## Final hygiene

Update `00_ARCHITECTURE/CONDUCTOR/modernization/PROGRAM_STATE.md` with the close note, archive `CONDUCTOR_LOG.md` to `99_ARCHIVE/`, then run the `rm -rf` above. Done.
