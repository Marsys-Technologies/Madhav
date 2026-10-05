---
artifact: CONSULTATION10_RELEASE
version: 1.0
status: IN_PROGRESS
---

# Consultation review10 release

Owner-authorized protected release under CCD-022 and lease L-PORTAL-CONSULTATION10-RELEASE-20261006. Commit only reviewed consultation source/scoped evidence; preserve pre-existing untracked portal drafts and all foreign worktrees. Reconcile protected main before current quality gates and focused PR.

Routine migration1307 adds boolean owner tags to existing conversations and conversation_messages; no data rewrite, object creation or privilege change. Recheck numbering, take/reconfirm recoverable database backup, apply only via established migration runner and verify applied hash/columns through runner evidence and authenticated history endpoints. Application rollback: baseline web amjis-web-probe-091362f315a2-37346348777-1; additive columns may safely remain. Preserve all existing tagged revisions. Stop promotion on health/auth/isolation/migration failure. No emergency CI override.

Required gates: lint, TypeScript, full unit tests, fresh migration claims/guard, PR Build Check, protected queue/main CI, zero-traffic candidate smoke and signing/RLS canary. After promotion verify exact source/image/traffic, shared shell, closed/pinned panels, three tabs, placement, historical reader and tag authorization/API responses. Do not create readings, share links, modify existing chart/account data or fix the pre-existing engine400 residual. Other Journey2 and Journey3 implementations are separate.

Current state is IN_PROGRESS; no new deployment or production acceptance claimed.
