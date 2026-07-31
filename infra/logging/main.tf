// MARSYS-JIS Platform Modernization — B-MCP-LOG-REDACT
// (DVA Ruling 64 / SAMAPTI_DVARAPALA_LEDGER.md INC-4, 2026-07-30)
//
// WHAT THIS CODIFIES
//
// Cloud Run's automatic HTTP request logging populates `httpRequest.requestUrl`
// (full path + query string, exactly as received) for EVERY request to a Cloud Run
// service — independent of anything the application logs itself. platform-mcp's own
// structured logger (platform-mcp/src/lib/logger.ts) was audited as part of this fix
// and never logs the raw request URL; the leak is entirely Cloud Run's own automatic
// request-log field. `amjis-mcp`'s `?api_key=<key>` URL-token fallback auth path (see
// platform-mcp/src/server.ts) therefore wrote a live, production-capable bearer
// credential into that field, in plaintext, on every request that used it — including
// `scripts/operator/mcp_end_to_end_smoke.sh`'s old Probe 4, which exercised this path
// with the real `mcp-canary-key` on every single deploy (fixed separately, same PR;
// see the script's B-MCP-LOG-REDACT banner).
//
// HONESTY NOTE ON "REDACTION" (Ruling 64 Decision B item 1 asked for an
// "exclusion/redaction filter"): Cloud Logging's Log Router exclusion mechanism
// operates on WHOLE log entries — a filter either keeps or drops an entry; there is
// no native field-level substring redaction for the automatic `httpRequest.requestUrl`
// field on ingest (that would require a custom Pub/Sub → DLP → bucket pipeline, out of
// scope for this fix — no such pipeline exists in this repo and this lane's authority
// does not extend to standing up new data-processing infra). What follows is
// therefore an EXCLUSION, scoped as narrowly as the mechanism allows: it drops (never
// durably stores) only `amjis-mcp` request-log entries whose `requestUrl` contains the
// literal `api_key=` credential-in-URL pattern this ruling flagged — not general
// `amjis-mcp` traffic, and not any other service. After the smoke-script fix in this
// same PR, this filter should rarely if ever fire in steady state; it exists as
// defense-in-depth against any OTHER caller (a real MCP client) using the fallback
// path with a real key.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

variable "gcp_project" {
  type    = string
  default = "madhav-astrology"
}

variable "gcp_region" {
  type    = string
  default = "asia-south1"
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

// Project-level Log Router exclusion. Applies to the project's routing (the _Default
// sink and any other project-level sink) — matching entries are dropped before they
// are durably stored anywhere; they still transiently exist for real-time Logs
// Explorer streaming/alerting during the request itself, per standard Cloud Logging
// behavior, but are never written to a log bucket.
resource "google_logging_project_exclusion" "amjis_mcp_url_token_credential" {
  name        = "amjis-mcp-url-token-credential-exclusion"
  description = <<-EOT
    B-MCP-LOG-REDACT (DVA Ruling 64, INC-4): drops amjis-mcp Cloud Run request-log
    entries whose requestUrl carries a live api_key= URL-token credential, before
    durable storage. Narrowly scoped to this exact leak pattern — does not exclude
    general amjis-mcp request logs. See infra/logging/main.tf header for the full
    rationale and the honesty note on why this is an exclusion, not a partial-field
    redaction (Cloud Logging has no native mechanism for the latter on this field).
  EOT

  filter = <<-EOT
    resource.type="cloud_run_revision"
    resource.labels.service_name="amjis-mcp"
    httpRequest.requestUrl:"api_key="
  EOT
}
