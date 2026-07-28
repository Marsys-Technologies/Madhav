# Feature Flag Status — MARSYS-JIS Platform

Managed in [platform/src/lib/config/feature_flags.ts](src/lib/config/feature_flags.ts).
Override any flag at runtime via env var `MARSYS_FLAG_<FLAG_NAME>=true|false`.

## Currently ON (backend active, UI hidden)

| Flag | Backend | UI | Notes | Flip when |
|------|---------|----|-------|-----------|
| `AUDIT_ENABLED` | ON | — | Logs every query to `audit_log` table + S3/GCS | Ready — already running |
| `AUDIT_VIEW_VISIBLE` | — | OFF | Shows audit log browser in the Consume UI | After native reviews 1–2 weeks of audit data |
| `PANEL_MODE_ENABLED` | ON | — | Panel synthesis runs server-side on every query | Ready — already running |
| `PANEL_CHECKBOX_VISIBLE` | — | OFF | Shows "Enable Panel Mode" checkbox in query UI | After native validates panel answer quality |
| `PARIPRASHNA_ENABLED` | OFF | OFF | Single flag gates BOTH the `/api/pariprashna` route (returns 404 when off) and the `/clients/[id]/pariprashna` page (redirects to `consult` when off) — there is no separate `_VISIBLE` companion flag; flipping it to `true` turns on backend + UI together | After PB-1 deploy verification, when the campaign's Q-1 lane is ready to run real readings against the deployed route |

## How to flip a flag

1. To enable UI for observation: set the `*_VISIBLE` flag to `true` in `feature_flags.ts` defaults, or set `MARSYS_FLAG_AUDIT_VIEW_VISIBLE=true` in Cloud Run env.
2. To disable backend processing: set the backend flag to `false` (stops API costs + DB writes).

## Removed

| Flag | Removed at | Notes |
|------|-----------|-------|
| `NEW_QUERY_PIPELINE_ENABLED` | Phase 11B (2026-05-11) | Legacy classify→compose→retrieve→synthesize→audit branch deleted; new pipeline is the only pipeline. Cloud Run env cleanup: `gcloud run services update amjis-web --region asia-south1 --project madhav-astrology --remove-env-vars "MARSYS_FLAG_NEW_QUERY_PIPELINE_ENABLED"` |
| `PORTAL_REDESIGN_R0_ENABLED` | R7 polish (2026-04-30) | AppShell is now the unconditional layout for all surfaces. Legacy code-path branches deleted from all layout.tsx files. Cloud Run env cleanup: `gcloud run services update amjis-web --region asia-south1 --project madhav-astrology --remove-env-vars "MARSYS_FLAG_PORTAL_REDESIGN_R0_ENABLED"` |
| `PORTAL_REDESIGN_R5_ENABLED` | R7 polish (2026-04-30) | Declaration-only flag; /clients/[id]/timeline is always enabled. No gated branches existed. |

## Advisory

While `AUDIT_ENABLED=true` and `AUDIT_VIEW_VISIBLE=false`, the audit is running and incurring DB writes + Anthropic API costs for every query, but the user cannot see the audit output. Flip `AUDIT_VIEW_VISIBLE` once you have enough data to validate it's useful.

Similarly, `PANEL_MODE_ENABLED=true` runs panel synthesis on every query (Anthropic API cost), but `PANEL_CHECKBOX_VISIBLE=false` means the user cannot activate panel display. Flip `PANEL_CHECKBOX_VISIBLE` once panel answer quality is validated.
