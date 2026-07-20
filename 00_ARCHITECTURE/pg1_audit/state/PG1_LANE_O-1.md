---
lane: O-1
wave: PG-1
status: COMPLETE
date: 2026-07-19
---

# PG1 Lane O-1 — Ops Truth

## Scope

Read-only ops/infra verification for the PG-1 audit wave. Charge: (1) verify
Cloud SQL PITR status on the production instance; (2) verify backup location
and whether a restore has ever been tested; (3) verify the documented
deploy/rollback mechanism (CONDUCTOR_PROTOCOL §8.3/§8.4) against the live
`.github/workflows/deploy.yml`, and check for feature-flag infrastructure
supporting §19 P1'; (4) render verdicts on assumptions A27 (accessibility)
and A28 (cross-conversation memory) from `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`
§1.1.

No writes to any restricted path. No mutating gcloud calls were run — describe/
list only, per instructions.

## Headline finding

**Cloud SQL PITR is DISABLED on the production instance `amjis-postgres`**
(`pointInTimeRecoveryEnabled=False`). Daily automated backups ARE enabled
(STANDARD tier, 7 retained daily snapshots at 02:00, `transactionLogRetentionDays=7`)
but `replicationLogArchivingEnabled=False` and `transactionalLogStorageState`
is unspecified — consistent with PITR being off. This means: restorable to
any of the last 7 daily snapshots, but NOT to an arbitrary point-in-time
within a window (e.g. "5 minutes before the bad migration ran").

This resolves the open question `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`
§14A.3 flagged as unverified: *"Cloud SQL automated backups may be enabled at
the instance level; nothing in-repo verifies or documents that, which means
nobody knows."* Now verified — partially good news (backups exist, ran
successfully daily through 2026-07-18), partially bad news (no PITR, so
worst-case RPO is up to ~24h, not near-zero as the doc's own recommended
posture for the conversation store / prediction ledger calls for).

## Findings summary (6 total, all in pg1_findings_O-1.jsonl)

| id | assumption | class | severity |
|---|---|---|---|
| PG1-O1-0001 | A34 | confirmed | high — PITR disabled, contradicts doc's implied need for near-zero RPO on irreplaceable tables |
| PG1-O1-0002 | A34 | confirmed | high — no restore drill ever run against a scratch instance; only unfilled template slots / per-chart data-repair actions found in repo |
| PG1-O1-0003 | NEW | confirmed | informational — deploy.yml matches CONDUCTOR_PROTOCOL §8.3/§8.4 exactly (workflow_run gate, no-traffic→smoke→promote, update-traffic rollback) |
| PG1-O1-0004 | NEW | confirmed | informational — feature-flag infra exists and is already in production use (NEXT_PUBLIC_MARSYS_FLAG_* build-time flags + DB-backed gate_registry.ts runtime kill-switches); §19 P1' assumption is sound |
| PG1-O1-0005 | A27 | confirmed | informational — aria-live-while-streaming pattern is live and tested (MarkdownContent.tsx, ReasoningProgress.tsx, co6_behavioral.test.tsx) |
| PG1-O1-0006 | A28 | partial | informational — cross-conversation memory / prior_reading citation kind not yet implemented (zero repo hits); consistent with A-28 being an honest forward design conclusion, not a stale claim |

## Recommended actions (priority order)

1. Enable Cloud SQL PITR on `amjis-postgres` with a stated retention window; this is the doc's own "first action, costs an hour" ask and is still outstanding.
2. Run one real restore-to-scratch-instance drill from an existing daily backup and record the runbook + actual RTO in-repo.
3. State RPO/RTO explicitly in-repo per §14A.3's fourth bullet (doc's own suggested posture: "24h RPO on layer data, near-zero on ledger and conversations" — currently not true until action 1 lands).
4. No action needed on deploy/rollback mechanism (matches docs) or feature-flag infra (already exists, ready for P1' shim gating).

## Evidence artifacts

- `gcloud sql instances describe amjis-postgres --project=madhav-astrology --format="value(settings.backupConfiguration)"`
- `gcloud sql backups list --instance=amjis-postgres --project=madhav-astrology` (15 successful backups on record, most recent 2026-07-18)
- `.github/workflows/deploy.yml`
- `00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/CONDUCTOR_PROTOCOL.md` §8.3/§8.4 (read-only)
- `platform/src/lib/config/feature_flags.ts`, `platform/src/lib/gates/gate_registry.ts`
- `platform/src/components/chat/MarkdownContent.tsx`, `ReasoningProgress.tsx`, `platform/src/components/consume/__tests__/co6_behavioral.test.tsx`
- `00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §1.1 (A-27, A-28), §14A.3
