---
artifact: OBSERVATORY_METERING_DESIGN
version: 1.0
status: IMPLEMENTATION_AUTHORIZED
created: 2026-09-29
changelog: ["v1.0: isolated implementation under native go-ahead"]
---
# Observatory and consumption accounting

One immutable attempt ledger serves Pariprashna, MCP, backend tests and connection validation. Each physical provider call has a durable start, receipt, parent operation, turn, conversation, authenticated owner, purpose, payer and route identity. External MCP synthesis is unobserved; CLI totals are client-reported. Null means unavailable. Cache/reasoning subsets are never added twice.

Starts commit before provider invocation. Receipts persist before semantic finish; DB failure falls back to configured durable GCS recovery storage, replayed idempotently by an admin endpoint. Filesystem recovery is development/test only. Dangling starts expose uncertainty. No prompt, response, credential, arbitrary metadata or raw error text is stored.

Effective-dated immutable USD rate cards retain source evidence and observed/effective times. Receipts freeze their charge lines and card ID. Provider-reported charges stay distinct. Missing categories, rates, unsupported modifiers and non-token fees remain unpriced. OpenRouter supports official model pricing sync; other providers support validated source-attributed imports and existing rate-table compatibility. Reconciliation remains subject to each connector's actual reporting granularity.

Shared scoped APIs drive My Usage and the super-admin Metering view: known totals with completeness, leaf attempts, turns, conversations, channel/purpose/model/role/status breakdowns, trace details, pricing freshness, pagination and safe export. User scope is pinned server-side. Admin tests use owned routing and existing budgets, require charge acknowledgement, and retain test attribution.

Default-off MARSYS_FLAG_AI_METERING_ENABLED. Additive migration stays unapplied to production. Full local checks and independent code/migration/security review precede handoff. No deployment, protected merge, production DB operation, credentials, corpus or orchestrator changes.

Customer charging, paid balances, empirical quality scores, automatic production schedules, new billing credentials, multimodal fee calculators and external-client MCP receipt integrations remain separate work. Their unavailable evidence must be visible. Historical usage retains historical uncertainty.
