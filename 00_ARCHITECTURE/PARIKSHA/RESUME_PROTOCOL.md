---
artifact: RESUME_PROTOCOL.md
version: 1.0
status: LIVE
authored_at: 2026-05-31
role: How Drashta + watchers resume from a break instead of restarting.
---

# Resume Protocol v1.0

When the Drashta walk breaks mid-flow (auth expired, browser crashed,
network drop, page navigation error, mid-build timeout, Vaidya mid-fix
interruption), the next Pariksha invocation must continue from the
checkpoint — not restart from /clients/new.

## Why this matters

A full walk takes 5-30 minutes depending on build duration. Restarting on
every break burns operator patience and creates duplicate charts. With
resume, breaks become recoverable.

## The checkpoint object

Every Drashta step writes to
`00_ARCHITECTURE/PARIKSHA/builds/<chart_id>/resume_state.yaml`:

```yaml
schema: v1
chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
build_id: 9fd9b9dd-aba0-4ed5-8d26-2e3fe97cbe27   # null until Stage 2
last_checkpoint_at: "2026-05-31T22:14:32Z"
last_checkpoint_by: "drashta"

# The 13 canonical checkpoints in the walk
checkpoints:
  form_loaded:                  { at: "...", url: "/clients/new" }
  form_validated:               { at: "...", form_state: {...} }
  form_submitted:               { at: "...", chart_id_response: "..." }
  redirected_to_cockpit:        { at: "...", url: "/clients/<id>/build" }
  cockpit_rendered:             { at: "...", screenshot: "..." }
  build_button_clicked:         { at: "..." }
  build_started:                { at: "...", build_id: "...", first_sse_event_at: "..." }
  l1_complete:                  { at: "..." }   # all 8 L1 writers done
  l2_5_complete:                { at: "..." }   # all 5 L2.5 writers done
  l3_complete:                  { at: "..." }   # all 8 L3 writers done
  build_complete_event:         { at: "..." }
  pramana_battery_run:          { at: "..." }
  final_report_written:         { at: "..." }

# Current state
current_stage: 2                # 1..6
current_checkpoint: cockpit_rendered
next_expected_action: click_build_button

# Recoverable state for the action
recovery_context:
  form_values_to_restore: null      # set if break occurred mid-form
  page_to_navigate_to: "/clients/362f9f17.../build"
  auth_status: valid_until_2026-05-31T23:00:00Z
  expected_dom_signatures:
    - { selector: "[data-testid='build-button']", expected_state: "enabled" }
    - { selector: ".cockpit-shell", expected_state: "mounted" }

# Break record (only present if break occurred)
break:
  occurred_at: "2026-05-31T22:14:32Z"
  reason: "auth_session_expired"   # or browser_crash, network_drop, vaidya_paused, manual_stop, timeout
  evidence:
    last_console_error: "401 Unauthorized"
    last_url: "/clients/362f9f17.../build"
  resume_strategy: "re_authenticate_then_navigate_to_url"

# Vaidya-paused state (only present if Vaidya activated mid-walk)
vaidya_paused:
  paused_at: "2026-05-31T22:14:32Z"
  paused_for_issue_id: "I-007"
  vaidya_session_id: "vaidya-<uuid>"
  expected_resume_after: "vaidya_pr_merged_and_deployed"
```

## Checkpoint cadence

Every Drashta step writes a checkpoint BEFORE attempting the action:

```
1. Read current resume_state.yaml
2. Write next_expected_action = <upcoming action>
3. Commit checkpoint (local file write, no git push needed)
4. Attempt the action
5. On success: write checkpoint as completed, advance to next
6. On failure: write break{} with reason + evidence; halt
```

This ensures the resume_state.yaml is always one step ahead of progress,
so a resume knows the intended action even if the current attempt failed.

## Resume algorithm

When a new Drashta session starts (operator paste, scheduled cron, or
auto-trigger after a Vaidya fix):

```
1. Read resume_state.yaml for the chart_id
2. If file absent: this is a fresh arc — start at form_loaded
3. If file present:
     a. Determine current_checkpoint + next_expected_action
     b. If break{} present:
          - Read break.reason
          - Execute resume_strategy from break record
          - On success: clear break{}, proceed
          - On failure: halt + escalate
     c. If vaidya_paused{} present:
          - Verify the Vaidya PR has merged + auto-deploy completed
          - If yes: clear vaidya_paused, proceed
          - If no: poll every 60s until done or timeout (1h)
     d. Navigate to recovery_context.page_to_navigate_to
     e. Verify recovery_context.expected_dom_signatures (auth still good,
        page loaded as expected)
     f. Restore recovery_context.form_values_to_restore if present
     g. Continue from next_expected_action
4. Walk forward from there, writing new checkpoints
```

## Recovery strategies by break reason

| Break reason | Strategy |
|---|---|
| `auth_session_expired` | Mint new __session cookie via mint_session_cookie.ts → reload page → re-verify expected DOM |
| `browser_crash` | Spawn fresh Chrome instance → re-auth → navigate to recovery URL |
| `network_drop` | Wait 60s for network → retry navigation → if still failing, halt |
| `vaidya_paused` | Poll Vaidya PR status; resume when fix landed and deployed |
| `manual_stop` | Operator wrote `STOP` file → halt all activity; resume requires removing STOP and re-paste of orchestrator |
| `timeout` | The build took longer than expected → re-poll for build_complete; if exceeds hard cap (1h), escalate |
| `page_navigation_error` | Navigate to recovery_context URL directly; if still fails, treat as new arc |

## In-cockpit "Resume Pariksha" banner (P3+ requirement)

Per the user's "kick off from same screen" requirement:

When `resume_state.yaml` shows an active break for the current chart_id +
the operator is viewing /clients/<id>/build:
- A gold-tinted banner appears at the top of the cockpit
- Banner shows: "Pariksha paused at: <next_expected_action> · Reason: <break.reason>"
- Action: "Resume Pariksha" button
- Click → POST /api/pariksha/resume → spawns a new Drashta session bound
  to this chart_id, which reads resume_state.yaml and continues

This becomes a new tiny API route + a small banner component (≤30 LOC each).
Specified in P3 brief.

## Vaidya-pause integration

When Vaidya activates mid-walk for a workflow_blocking issue:

```
1. Drashta encounters blocker → writes break{reason: vaidya_paused, ...}
2. Drashta exits (no need to keep Chrome session alive during fix)
3. Vaidya runs its remediation arc (open PR, wait for CI, wait for deploy)
4. Naya-Pariksha (or another Drashta invocation) checks resume_state every
   60s; when vaidya_paused.expected_resume_after condition is met, resumes
5. Resumed Drashta verifies the fix worked by retrying the failed action
6. If fix worked: clear vaidya_paused, continue
7. If fix did NOT work: record fix_failed in issue history, halt or retry
   (per Vaidya retry budget)
```

## Reset

To force a fresh start (discard resume state):
```
rm 00_ARCHITECTURE/PARIKSHA/builds/<chart_id>/resume_state.yaml
```
Or: in the cockpit banner, "Reset Pariksha (fresh start)" link.

## Safety

- Resume must verify chart_id, build_id, and auth state match the
  checkpoint. If any mismatched, treat as a stale checkpoint and either
  start fresh or escalate to operator.
- Checkpoint files do NOT get committed to main (gitignored).
- Resume timestamps are recorded in the resumed walk's history for audit.
