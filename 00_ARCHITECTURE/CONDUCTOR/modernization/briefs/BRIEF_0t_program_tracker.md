---
unit: 0t
wave: 0 (program-support — build FIRST so it can track everything)
title: Program Tracker — live, real-time progress dashboard (ephemeral, removable)
stream: any free stream (standalone; no app-code deps)
worktree: any
blockedBy: []
on_red: rollback
lifecycle: EPHEMERAL — delete the whole `tools/program-tracker/` dir + its Cloud Run service at program close.
---

## Context (self-contained)
With zero human approval gates, the native's visibility IS the safety surface. Build a real-time dashboard
that shows, at a glance: what is done, what is running, what is left, what is blocked, and what was MISSED
(failed gates / rollbacks / stale / halts). It must be live (auto-updating), hostable on localhost AND
Cloud Run, and **fully self-contained so it can be deleted at program end with one `rm -rf` + one service
delete** (it must NOT wire into the main app — clean removability).

## System architecture (decoupled: emitters → one status file → UI)
```
Conductor + gate check_commands + a git-poller  ──write──▶  program_status.json  ──read──▶  tracker server ──▶ dashboard (SSE/poll)
```
- **`tools/program-tracker/`** — a standalone tiny Node service (single `server.mjs` + `public/index.html`).
  No import from `platform/` or `platform-mcp/`. Its own minimal `package.json`.
- **Status contract = `program_status.json`** (the single source the UI reads). It is ASSEMBLED, not
  hand-kept, by a `collect.mjs` that derives state from the canonical sources:
  - `00_ARCHITECTURE/CONDUCTOR/modernization/session_queue.yaml` (units, deps, gates, fences),
  - `00_ARCHITECTURE/CONDUCTOR/modernization/PROGRAM_STATE.md` (current batch, last-green, halts),
  - `git` (per-stream branch HEADs, commits, main cherry-picks),
  - a `gate_status.json` each gate `check_command` writes its exit-code + timestamp to,
  - `CONDUCTOR_LOG.md` + `CONDUCTOR_HALT_LOG.md` (activity + halts),
  - (optional) `gcloud run services describe` for prod revision + error rate.
- **Real-time:** `collect.mjs` runs on a 5s interval (and on a file-watch of the sources) and writes
  `program_status.json`; the server pushes it to the browser via **SSE** (`GET /events`) with a **client
  poll fallback** (`GET /status.json` every 5s). Header shows "updated Ns ago" + a live/stale dot
  (stale = no update in 30s → amber).

## `program_status.json` schema
```json
{
  "program":"PLATFORM_MODERNIZATION","updated_at":"ISO",
  "current_batch":1,"percent_complete":8,
  "streams":[{"id":"A","branch":"prog/stream-a","state":"running|idle|halted","current_unit":"0a.1","last_green":"0a.0","head_sha":"a1b2c3d"}],
  "gates":[{"id":"naming_ci","status":"green|red|pending","last_run":"ISO"}],
  "units":[{"id":"0a.0","wave":"0a","title":"...","stream":"A","status":"pending|blocked|eligible|running|green|red|rolled_back|halted","blockedBy":["..."],"gate_result":"pass|fail|na","commit_sha":"...","merged_to_main":true,"updated_at":"ISO"}],
  "halts":[{"type":"halt_queue|kill_switch","unit":"...","reason":"...","opened_at":"ISO","resolved":false}],
  "attention":[{"unit":"1.2","reason":"jh_oracle input required","severity":"blocker"}],
  "activity":[{"ts":"ISO","kind":"commit|cherrypick|gate_flip|rollback|rekick|deploy","detail":"..."}],
  "health":{"tests_pass":true,"coverage":0.0,"smoke":"pass|fail|na","prod_revision":"...","error_rate":0.0}
}
```

## Dashboard sections (build to the previewed design)
1. **Header** — program, current batch/wave, live dot + "updated Ns ago".
2. **Metric tiles** — % complete · units done/total · gates green/total · active halts · prod revision.
3. **Wave progress** — segmented 0a·0b·1·2·3·4 (done/active/pending).
3b. **Completion matrix (ALL units)** — every unit rendered as a color-coded cell, grouped by wave:
    **green = done & merged · orange = in progress · gray = not started · lock badge = blocked by a gate.**
    This is the headline "what is NOT done yet" surface — driven by `units[].status` from the status
    contract, so cells flip green as units merge and orange while running, with zero manual upkeep. Count of
    cells must equal the live unit total; a legend states the color mapping. Render it as a **vertical,
    sequential ledger** (logical execution order, top to bottom), and each unit shows a one-line
    **plain-language description of what it delivers** — not just its id (ids alone are confusing).
4. **Streams** — A/B/C: state badge · current unit · last green · head SHA.
5. **Gate board** — naming_ci, jh_oracle_pinned, G1–G5b chips (green/red/pending + last-run).
6. **Attention & blocking** (danger-bordered) — `attention[]` + active `halts[]` with reasons. THE "what we
   missed / what's stuck" view: failed gates, rollbacks, stale units (>N min no update), unexpected blocks.
7. **Unit board** — grouped Done&merged / Running / Eligible / Blocked / Pending, each card = id+title+stream
   (+gate result + SHA + merged flag). This is "completed vs left" at a glance.
8. **Activity feed** — reverse-chron `activity[]` with icons + relative time.
9. **Health strip** — tests/coverage/smoke/prod-revision/error-rate (error-rate proximity = kill-switch risk).
Theme-adaptive (light/dark), no secrets ever rendered, read-only (no controls that mutate the program).

## Hosting
- **Local:** `node tools/program-tracker/server.mjs` → `http://localhost:8787/` (port env-configurable).
- **Prod (optional):** a `Dockerfile` + standalone Cloud Run service `amjis-tracker` (its OWN service, NOT
  the main app), behind IAM or a shared token; reads `program_status.json` from GCS if run off-box.
  Deleted at program close (`gcloud run services delete amjis-tracker`).

## Acceptance criteria (all automated)
1. `node tools/program-tracker/server.mjs` serves the dashboard on localhost and `GET /status.json` returns
   schema-valid JSON assembled from the real sources (test against the current `session_queue.yaml`).
2. SSE pushes an update within 5s of `program_status.json` changing (test: touch a source, assert push).
3. **Click-through:** an integration test loads the page and asserts all 9 sections render from a fixture
   `program_status.json` (mount, not prop-inject).
4. Stale detection: if no update in 30s, the header dot goes amber and labels "stale".
5. **Removability:** a `REMOVE.md` documents the exact `rm -rf tools/program-tracker/` + service-delete; a
   grep proves zero imports of program-tracker from `platform/` or `platform-mcp/`.
6. Renders no secret/credential values (scan the assembled JSON).

## must_not_touch
`platform/src/**`, `platform-mcp/src/**`, `platform/migrations/**` (standalone tool only).

## Commit cadence / rollback
Commits: (1) server + status schema + collector, (2) dashboard UI, (3) SSE + stale + tests, (4) Dockerfile +
REMOVE.md. Cleanly cherry-pickable (only `tools/program-tracker/**`). Rollback = revert; nothing else depends on it.
