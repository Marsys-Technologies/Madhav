---
artifact: ISSUE_LEDGER_SCHEMA.md
version: 1.0
status: LIVE
authored_at: 2026-05-31
role: Schema all Pariksha agents use to write to the shared issue ledger.
---

# Issue Ledger Schema v1.0

Every agent writes issues to
`00_ARCHITECTURE/PARIKSHA/builds/<chart_id>/issues.yaml`.

## File-level structure

```yaml
schema: v1
chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
build_id: 9fd9b9dd-aba0-4ed5-8d26-2e3fe97cbe27   # null until Stage 2 fires
arc_started_at: "2026-05-31T22:00:00Z"
last_updated: "2026-05-31T22:14:32Z"
last_updated_by: "drashta"

# Pratisamhita aggregates open issues into root-cause clusters.
root_causes:
  - id: RC-001
    title: "Form-to-API field name drift"
    confidence: high
    issues: [I-001, I-007, I-015]
    suspected_layer: frontend_or_api

issues:
  - id: I-001
    discovered_by: drashta
    discovered_at: "2026-05-31T22:03:14Z"
    surface: "/clients/new"
    stage: 1
    severity: workflow_blocking
    title: "Form submit returns 422 on gender"
    description: |
      Filled form with gender='Male' from UI dropdown. POST /api/clients/create
      returned 422 with errors[0].field='gender' message='must be one of M, F, O, unknown'.
      UI sent 'Male' but API expects 'M'. Contract drift.
    evidence:
      screenshots: ["builds/<chart_id>/screenshots/I-001-form-422.png"]
      console:
        - "POST /api/clients/create 422 (Unprocessable Entity)"
      network:
        - method: POST
          url: /api/clients/create
          status: 422
          request_body_excerpt: '{"gender": "Male", ...}'
          response_body_excerpt: '{"errors":[{"field":"gender","message":"..."}]}'
      db_state: |
        SELECT COUNT(*) FROM charts WHERE created_at > NOW() - INTERVAL '1 minute';
        → 0
    suspected_root_cause: form_to_api_contract_drift
    suspected_files:
      - platform/src/components/clients/NewClientForm.tsx
      - platform/src/app/api/clients/create/route.ts
    related_root_cause: RC-001
    status: open
    severity_reason: "Guest cannot create a chart. Blocks entire workflow."
    triage:
      vaidya_eligible: true
      complexity: low
      estimated_loc_delta: ~5
      may_touch: [platform/src/components/clients/NewClientForm.tsx]
    history:
      - at: "2026-05-31T22:03:14Z"
        action: discovered
        by: drashta
      - at: "2026-05-31T22:04:02Z"
        action: triaged
        by: pratisamhita
        severity_set: workflow_blocking
    fix_pr: null
    fix_attempts: 0
    closed_at: null
```

## Required fields

Every issue MUST have:
- `id` (sequential `I-NNN`)
- `discovered_by` (one of: drashta, aapti_drashta, yantra_drashta, tantra_drashta, sambandha_drashta, pramana_drashta)
- `discovered_at` (ISO 8601)
- `surface` (URL path or system component)
- `stage` (1-6)
- `severity` (workflow_blocking | ux_degrading | cosmetic | data_integrity)
- `title` (short, ≤80 chars)
- `description` (long-form)
- `evidence` (at least one of: screenshots, console, network, db_state, logs)
- `status` (open | triaged | fix_in_flight | fix_landed | regression_check_pending | closed)

## Severity definitions

| Severity | Definition | Examples |
|---|---|---|
| `workflow_blocking` | Guest cannot complete the build flow from /clients/new to build_complete | Form submit fails; Build button does nothing; SSE never connects; build hangs >30 min |
| `data_integrity` | Build appears to complete but Pramana finds the chart_facts are internally inconsistent | Row count off >5% from spec; FK violations; layer ordering violated; nondeterminism |
| `ux_degrading` | Build completes but the user experience is visibly wrong | Progress bar lies; cockpit shows wrong asset count; Sanskrit names missing |
| `cosmetic` | Visible imperfection that doesn't impair function | Typo; color contrast; text wrap; minor layout shift |

## Severity → Vaidya eligibility

| Operator authorization | Auto-fix severities |
|---|---|
| observe-only | none |
| pr-only fixes (default) | workflow_blocking + data_integrity (PR opened, no merge) |
| auto-merge low-risk | workflow_blocking + data_integrity (PR auto-merged if ≤30 LOC + green CI), ux_degrading (PR-only) |

## Pratisamhita root-cause clustering

When ≥2 issues share a `suspected_root_cause` string or `suspected_files` pattern,
Pratisamhita creates an `RC-NNN` entry grouping them. Vaidya fixes the root cause,
not individual issues; closing the root cause closes all child issues.

## Status transitions

```
open → triaged → fix_in_flight → fix_landed → regression_check_pending → closed
                                ↓
                            fix_failed (retry counter +1)
                                ↓
                            escalated (after 2 retries)
```

`closed` can also be reached from `triaged` if Pratisamhita downgrades to
cosmetic-but-by-design or if native review marks as won't-fix.

## Concurrent writes

Multiple agents write to the same file. Same race-resolution as CLAIM_LEDGER
from build_e2e_arc:
1. `git pull --rebase` before write
2. Append your change (issues are append-only; updates use new `history[]` entries, never overwrite)
3. `git push`; on race, retry up to 3 times

Per-build issues.yaml is NOT pushed to main (it's in builds/ which is gitignored).
The atomic primitive is local file locking via filename touch + retry.
