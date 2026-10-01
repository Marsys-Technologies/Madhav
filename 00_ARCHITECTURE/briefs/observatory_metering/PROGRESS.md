# Observatory implementation progress

Base: cbded8e54908aa258277d6a47c6988bca8fbbdbb
Worktree: /Users/Dev/.codex/worktrees/observatory-metering/Madhav
Branch: codex/observatory-metering
Lease: L-OBSERVATORY-METERING-20260929; remotely verified 05a67cb18.
Session-open schema: PASS, 0 violations.

Status: local implementation and independent reviews complete; default-off, unapplied outside disposable PostgreSQL, retained uncommitted for review. No hosted/product acceptance is claimed.

Delivered: immutable per-invocation attempt/receipt ledger, nested token normalization, exact-decimal rate snapshots, durable recovery, BYOK and shared-model instrumentation across Pariprashna/Consult/Build/MCP doors, separate CLI aggregates and historical evidence, owner/admin scoped analysis APIs, conversation/turn drill-down, CSV export, user/admin dashboards, bounded official OpenRouter rate refresh, source-attributed manual rate imports, and explicitly acknowledged metered administrator tests. The runbook documents operation and coverage.

Local evidence in `verification/`: 1,298 Vitest files passed (14,401 tests; 82 files skipped, 761 tests skipped, 2 todo); TypeScript passed; lint 0 errors and 583 warnings; disposable PostgreSQL migration and ledger suite 11/11 passed; tracker-focused suite 2/2 passed. Red/green evidence covers incomplete token partitions and microsecond pagination. `REVIEW_v1_0.md` records independent migration and whole-change review, fixes, and limits.

Unverified boundaries: configured private recovery bucket permissions, live provider and CLI behavior, authenticated hosted UI, provider invoice reconciliation, deployment and production migration. Other provider rate cards require reviewed manual imports; external calls that bypass Madhav and external MCP client synthesis cannot be measured by this server. No customer billing or automatic cross-provider tariff collection is included.

Lease release: remotely verified on `origin/campaign-coordination` at commit `3464c4df827ecdd283a2b301d8811f523ef5450d`. The isolated worktree remains available for review.

2026-09-30 verification follow-up: a new scoped coordination lease covers a
synthetic enabled-mode acceptance gate, now green. See `TEST_REPORT_v1_0.md`
and `verification/2026-09-30/results.json`. This does not advance hosted
acceptance or erase the separately observed legacy global-flag fixture
failures, static AI Console baseline or local CLI version mismatches.
Verification lease `L-OBSERVATORY-METERING-VERIFY-20260930` was remotely
released at `4e7f7989025ccc5192208b037d669678d7a9a844` on
`origin/campaign-coordination`.

Ruling: native implementation instruction supersedes skill artifact review pauses; execute inline and preserve uncommitted review state.
Ruling: customer charging and empirical quality scoring remain separate scope; unavailable evidence stays visible.
Ruling: local verification makes no external provider calls or production connections.
