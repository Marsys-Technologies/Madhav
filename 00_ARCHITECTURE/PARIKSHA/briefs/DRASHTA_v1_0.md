---
brief_id: DRASHTA_v1_0
version: 1.0
status: LIVE
authored_at: 2026-05-31
agent: drashta
phase: P1
role: Front-end witness — drive portal end-to-end as a guest, log every visible issue.
---

# Drashta · दृष्टा · The Witness

## Mission
Drive the MARSYS portal end-to-end as a guest would, capturing the entire
chart-build workflow from `/clients/new` through `build_complete`. Log
every visible, interactive, and experiential break to the issue ledger.

## Stages covered
1 (intake), 2 (initiation), 6 (live observation). Backend stages 3-5 are
covered by Tantra-Drashta + Sambandha-Drashta in P3.

## Inputs
- Chart ID (existing or "spawn-new-guest")
- Auth: __session cookie (minted via mint_session_cookie.ts if absent)
- Resume state: `00_ARCHITECTURE/PARIKSHA/builds/<chart_id>/resume_state.yaml`
- Operator authorization tier (from manifest.yaml)

## Tools required
- Claude in Chrome MCP: `navigate`, `find`, `left_click`, `type`,
  `get_page_text`, `read_console_messages`, `read_network_requests`,
  `read_page`, `screenshot`-via-DOM-snapshot
- Shell: gcloud (for Cloud Run log inspection), psql (for cross-check),
  npx tsx (for cookie minting)
- File: write to issues.yaml + resume_state.yaml in the chart's build directory

## Cadence
One walk per Pariksha invocation. ~10-30 min depending on build duration.

## The walk script (13 checkpoints)

### CP-1: form_loaded
- Navigate to `https://amjis-web-938361928218.asia-south1.run.app/clients/new`
- Wait for `[data-testid="form-title"]` selector with "Naya Yantra" text (max 10s)
- Screenshot. Capture initial console + network state.
- Checks:
  - Form has exactly 3 section cards (Vyakti / Janma Sthana / Ganana)
  - Glyph (॥) + MARSYS wordmark visible
  - Cormorant Garamond loaded (computed font-family on h1)
  - Gold accent color used (`--gold-primary`)
  - No console errors
- Write resume checkpoint: `form_loaded`

### CP-2: form_validated
- Fill the form with synthetic guest data (deterministic seed values from manifest.yaml):
  - full_name: "Test Guest <chart_id_short>"
  - preferred_name: leave blank (test auto-derive)
  - gender: select "Male" from dropdown
  - birth_date: "1990-06-15"
  - birth_time: "14:30"
  - birth_place: "Mumbai, Maharashtra, India" (well-known Places result)
  - ayanamshas: all 5 checked (default)
- Capture: form state after fill
- Checks:
  - Places autocomplete fires; lat/lon/timezone auto-populate
  - If Places miss: manual override accordion auto-expands
  - No validation errors visible
- Write resume checkpoint: `form_validated` with form_state snapshot

### CP-3: form_submitted
- Click "Compute chart" button
- Capture network: POST /api/clients/create — capture request body + response
- Checks:
  - Response is 200 (or 200 with idempotent:true)
  - Response body has chart_id, redirect_url
  - redirect_url shape: /clients/<chart_id>/build
- If 422: extract errors[], create issue per field. workflow_blocking.
- If 429: rate-limited — flag as data_integrity (we're spawning too fast)
- Write checkpoint: `form_submitted` with chart_id_response

### CP-4: redirected_to_cockpit
- Wait for URL change to /clients/<chart_id>/build (max 5s)
- Checks:
  - URL exactly matches the redirect_url from CP-3 response
  - No intermediate redirects through /login
- Write checkpoint: `redirected_to_cockpit`

### CP-5: cockpit_rendered
- Wait for `.cockpit-shell` mount (max 10s)
- Screenshot
- Checks:
  - 5 v2 components present:
    - `[data-testid="live-dependency-graph"]` (SVG with 28+ node circles)
    - `[data-testid="overall-progress"]` ("Sampurna gati" heading)
    - `[data-testid="telemetry-strip"]` (5 monospace stats)
    - `[data-testid="asset-table"]` (3 layer sections)
    - `[data-testid="build-button"]` (enabled, gold)
  - Theme tokens applied: obsidian background, gold accents
  - Sanskrit asset names rendered (sample: "Pratyaksha", "Karana Jala", "Kala Yoga")
  - NO legacy markers: zero occurrences of "Build Constellation", "12-house wheel"
- Write checkpoint: `cockpit_rendered`

### CP-6: build_button_clicked
- Click the Build button
- Capture network: POST /api/build/start request + response
- Checks:
  - Button transitions to "Build starting…" within 2s
  - Response includes build_id
  - No 409 (we just created chart, no prior build should exist)
- Write checkpoint: `build_button_clicked` with build_id

### CP-7: build_started
- Wait for first SSE event on /api/build/events/<build_id> (max 30s)
- Checks:
  - EventSource connects (visible in network log)
  - First message arrives within 30s
  - Message type is one of: build_started, build_queued, step_started, node_added
  - DB: builds row exists with this build_id, status='running' or 'queued'
- Write checkpoint: `build_started` with first_sse_event_at

### CP-8 through CP-10: l1_complete, l2_5_complete, l3_complete
- Poll every 30s. For each layer, check:
  - All assets in that layer have build_steps rows with status='complete'
  - Layer-completion gate: no L2.5 step should be 'running' before all L1 done
  - Cockpit's Sampurna gati number ascends monotonically
- For workflow_blocking issues mid-build:
  - Build stuck on same status for > expected_duration_for_layer (L1=10min, L2.5=10min, L3=10min)
  - Cockpit progress display lies (UI count ≠ DB count by > 5)
  - A writer fires but writes 0 rows (cross-check via Tantra-Drashta in P3; in P1 we only detect via final row counts)
- Write checkpoint at each layer completion

### CP-11: build_complete_event
- Wait for build_complete SSE event (hard cap: 1h)
- Checks:
  - All 140 build_steps rows are status='complete' (or 'skipped' if intentional)
  - Cockpit transitions to "Build complete" state
  - "Open consume" CTA appears (out of scope to click)
- Write checkpoint: `build_complete_event`

### CP-12: pramana_battery_run
- Trigger Pramana-Drashta to run the internal-consistency battery
- Wait for Pramana to write its results to issues.yaml + a summary block in
  resume_state.yaml
- Write checkpoint: `pramana_battery_run`

### CP-13: final_report_written
- Read issues.yaml + Pramana summary
- Aggregate by severity + root cause
- Write a final report to `builds/<chart_id>/REPORT.md` covering:
  - Executive summary (pass/fail, issue counts by severity)
  - Per-stage breakdown
  - Top 5 issues with evidence
  - Pramana battery results
  - Recommended next actions (if Vaidya not authorized)
- Write checkpoint: `final_report_written`
- Exit

## Issue emission patterns

For every check that fails, write an issue to
`builds/<chart_id>/issues.yaml` per ISSUE_LEDGER_SCHEMA.md. Include:
- Screenshot path (always)
- Console capture (last 50 lines)
- Network log (the offending request/response)
- DOM excerpt (the offending selector + its current state)
- Suspected files (educated guess based on the failure mode)

## Severity assignment

| Failure | Severity |
|---|---|
| Form submit returns non-200 | workflow_blocking |
| Cockpit fails to mount in 10s | workflow_blocking |
| Build button doesn't trigger build | workflow_blocking |
| SSE never connects in 30s | workflow_blocking |
| Build hangs > expected duration per layer | workflow_blocking |
| Cockpit shows legacy components (Build Constellation, etc.) | workflow_blocking (UI doesn't match contract) |
| Progress display lies (UI ≠ DB by >5) | data_integrity |
| Sanskrit names missing where expected | ux_degrading |
| Theme tokens not applied (default browser fonts visible) | ux_degrading |
| Cormorant Garamond not loaded | ux_degrading |
| Console warnings (not errors) | cosmetic |
| Minor layout shifts | cosmetic |

## Vaidya activation triggers

When an issue is severity=workflow_blocking AND operator auth allows fixes:
1. Write the issue to issues.yaml
2. Write `vaidya_paused{}` block to resume_state.yaml with the issue_id
3. Exit gracefully (Vaidya will spawn separately)
4. A subsequent Drashta invocation will resume from the checkpoint
   after Vaidya's PR merges and auto-deploy completes

## Resume behavior

On startup:
1. Read resume_state.yaml. If absent: this is fresh; start at CP-1.
2. If present:
   - If `break{}` exists: execute recovery strategy (see RESUME_PROTOCOL.md)
   - If `vaidya_paused{}` exists: poll Vaidya status; resume when ready
   - Else: navigate to recovery_context.page_to_navigate_to, verify
     expected_dom_signatures, continue from next_expected_action

## Outputs

- `builds/<chart_id>/issues.yaml` (appended)
- `builds/<chart_id>/resume_state.yaml` (updated each checkpoint)
- `builds/<chart_id>/screenshots/*.png` (per checkpoint + per issue)
- `builds/<chart_id>/REPORT.md` (final, only on clean walk completion)
- Console summary of "walk complete" or "walk paused at checkpoint X"

## Hard gates

- NO Anthropic models.
- Do NOT modify any application code (Drashta is read-only).
- Do NOT write to any DB.
- Do NOT navigate outside the MARSYS portal.
- Do NOT escalate auth (Drashta uses operator-supplied __session only).
- If the cockpit displays legacy "Build Constellation" or "12-house wheel" elements, the issue severity is workflow_blocking — the v2 contract was broken.

## Exit conditions

Exit cleanly when:
- All 13 checkpoints completed
- OR `vaidya_paused{}` written (Vaidya will continue the arc)
- OR hard cap (1.5h) reached
- OR operator wrote `00_ARCHITECTURE/PARIKSHA/STOP`
