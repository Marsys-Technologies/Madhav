---
artifact: OBSERVATORY_METERING_VERIFICATION_PLAN
version: 1.0
status: IMPLEMENTED_LOCAL_REVIEW
created: 2026-09-30
---
# Enabled-mode verification follow-up

Goal: make the new metering path testable under an explicit enabled-mode gate without spending provider tokens or weakening fail-closed attribution.

Scope: add synthetic tests for owned validation probes and request-scoped shared models, run the focused enabled-mode suite and disposable PostgreSQL checks, and record honest limits. Keep older adapter contract tests as unit tests; they intentionally invoke providers outside an authenticated request and are not an enabled-mode acceptance gate.

- [x] Prove an owned connection probe writes metering start and terminal evidence, and refuses a provider call when the start fails.
- [x] Prove shared SDK calls require admitted request attribution when enabled, and remain unchanged when disabled.
- [x] Run the focused enabled-mode suite, disposable PostgreSQL suite, full default-off suite, lint, TypeScript and build checks.
- [x] Record baseline static-audit delta, local CLI version compatibility and limits in the runbook/report.
- [x] Release the local verification lease; retain the isolated worktree uncommitted for review.
