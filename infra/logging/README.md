# infra/logging — Cloud Logging exclusions

B-MCP-LOG-REDACT (DVA Ruling 64, `00_ARCHITECTURE/briefs/samapti/SAMAPTI_DVARAPALA_LEDGER.md`
INC-4, 2026-07-30).

## What this codifies

One Log Router exclusion, `amjis-mcp-url-token-credential-exclusion`: drops `amjis-mcp` Cloud
Run request-log entries whose `httpRequest.requestUrl` contains a live `api_key=` URL-token
credential, before durable storage.

## Why

Cloud Run's automatic HTTP request logging captures `httpRequest.requestUrl` (full path + query
string, exactly as received) for every request — independent of application code. `amjis-mcp`'s
`?api_key=<key>` URL-token fallback auth path (`platform-mcp/src/server.ts`) therefore wrote a
live, production-capable bearer credential into that field in plaintext on every request that
used it, including `scripts/operator/mcp_end_to_end_smoke.sh`'s old Probe 4, which exercised this
exact path with the real `mcp-canary-key` Secret Manager value on every single deploy. That smoke
script is fixed in the same PR as this module (see the script's own B-MCP-LOG-REDACT banner); this
Terraform module is the companion mitigation for the log-storage side, and for any OTHER caller
(a real MCP client) that uses the fallback path with a real key.

## Honesty note: exclusion, not redaction

Ruling 64 Decision B item 1 asked for a Cloud Logging "exclusion/redaction filter." Cloud
Logging's Log Router exclusion mechanism operates on whole log entries — a filter keeps or drops
an entry; there is no native field-level substring redaction for the automatic
`httpRequest.requestUrl` field on ingest. True field-level redaction would require a custom
Pub/Sub → DLP → bucket transformation pipeline; no such pipeline exists in this repo, and standing
one up is out of this lane's scope. What's implemented instead is an **exclusion**, scoped as
narrowly as the mechanism allows: it matches only `resource.type="cloud_run_revision" AND
resource.labels.service_name="amjis-mcp" AND httpRequest.requestUrl:"api_key="` — i.e. only the
exact leak pattern this ruling flagged, not general `amjis-mcp` traffic and not any other service.
After the smoke-script fix, this filter should rarely if ever fire in steady state.

Application-level defense-in-depth is also in place: `platform-mcp/src/lib/logger.ts`'s
`log()`/`logWarn()`/`logError()` now redact `api_key=` values from any string field before writing
to stdout/stderr (which Cloud Run also captures into Cloud Logging, as a separate jsonPayload/
textPayload entry from the automatic `httpRequest` field this module addresses). See
`platform-mcp/src/__tests__/logger_redaction.test.ts` for the before/after proof.

## Files

- `main.tf` — the `google_logging_project_exclusion` resource.
- `backend.tf` — GCS-backed terraform remote state (`infra/logging` state prefix).
- `apply.sh` — idempotent plan/apply wrapper, matching `infra/iam/apply.sh` and
  `infra/cloud_scheduler/apply.sh`'s conventions.

## Applying

Via the dispatch-only `IaC Apply` GitHub Actions workflow (`.github/workflows/iac-apply.yml`),
selecting module `logging`. Never applied automatically on deploy or PR — same posture as every
other `infra/*` module (PA-06). Plan is always shown before apply.

## Scope note

No credential rotation, no Secret Manager writes, no IAM changes are part of this module — the
`mcp-canary-key` value already written to logs by the historical smoke-script behavior remains the
native's rotation decision (Ruling 1), tracked in the SAMAPTI close report's INC-4 entry alongside
INC-1/2/3.
