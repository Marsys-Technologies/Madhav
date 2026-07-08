---
canonical_id: R5_1_RUN_LEDGER
version: 1.0
status: LIVE
created: 2026-07-09
author: Claude Code (executing CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md)
program: successor run to R5 (SEALED — R5_RETRIEVAL_3_0_SEAL_v1_0.md). Governing law unchanged:
  RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN v1.6 + R5 seal report §3/§6 punch-list.
head_at_c0: 5c699c75 (docs(r5.1) brief commit; synced to origin via PR #484)
scope: C0 preflight through C5 wrap, per brief phase order (strict, no skipping).
---

# R5.1 RUN LEDGER — MCP-Consume

Append-only. Every phase's close appends here; this document never edits prior entries.

## JL-000 — Scope ruling recorded (native, 2026-07-09)

**Entry:** the native's message dispatching `CLAUDECODE_BRIEF_R5_1_MCP_CONSUME_v1_0.md` constitutes
the scope ruling and ratification-by-kickoff of this brief, per the brief's own frontmatter
`scope_ruling` field: PRIORITIZED = MCP interaction excellence on the two charts (482012f1 Abhisek +
1c826d5a Abhinandan) + acceptance battery. DEFERRED SHELF (explicitly out of scope, do not touch):
portal chat/UI productization, LEL/outcome web UI, Arunima/Kiran chart builds, rate limiting,
branch-graveyard cleanup, frontmatter CI debt, cross-chart pool opening, JL-022 Option B, tool-estate
legacy-name removal.

Execution mode: conductor + Pratinidhi-R grounded on `R5_AUTHORITY_DOSSIER_v1_0.md` (unchanged from
R5). Battery `R5_ANSWER_BATTERY_v1_0.md` remains FROZEN law — regression items only, never
edit/re-grade.

**Basis:** brief frontmatter `scope_ruling` field, v1.0, 2026-07-09.
**Reversibility:** all in-run judgment rulings carry native retrospective veto (brief inherits R5's
Pratinidhi-R protocol).

---

## C0 — PREFLIGHT (self-gating) — CLOSED, no HALT

### Deploy-truth
`amjis-web` latestReadyRevision `amjis-web-00889-9cz` (image `39f981cd…`, HEAD's parent — brief
commit `5c699c75` is docs-only, no redeploy required). `amjis-mcp` latestReadyRevision
`amjis-mcp-00403-c6v` (image `cf8e2186…`, PR #480) — confirmed zero `platform-mcp/**` commits landed
since that SHA. Live `initialize` handshake against the deployed MCP endpoint: HTTP 200, protocol
`2025-11-25`. **PASS.**

Finding: local `main` was 1 commit ahead of `origin/main` (`5c699c75`, docs-only, clean tree).
Direct push rejected by branch protection (4 required status checks). Resolved via PR #484
(`docs/r5-1-brief-sync`), set to auto-merge-squash.

### Migrations reconciliation
`_migrations_applied` = 310 rows; disk = 304 files; 0 on-disk-but-unledgered (no pending gap); 6
ledgered-but-retired-from-disk (pre-`173_drop_legacy_builds.sql` era, expected archival hygiene).
Latest ledgered = `426_build_runs_scope_asset_set.sql`, matches highest on-disk file. **PASS.**

### Canary battery state
Latest FULL battery on disk: `evals/r5-w4-full-battery/results_d5105222.json` (2026-07-08T20:42Z,
SHA `d5105222`, PR #478) — 14/38 pass, the known pre-C1 baseline (flagship instruments oversized —
exactly what C1 exists to fix). No scheduled canary job exists yet (`gcloud scheduler jobs list`
shows no canary-related job) — confirms brief item C5.2 is genuinely open, not silently skipped.
**Accepted as the honest W0 baseline for this run's before/after comparison (brief C4 requires a
token/latency/call-count table vs the W0 baseline — this is that baseline).**

### Test credential
`mcp_api_keys` row `key_id=mcp_prod_tDO7obNw`, `user_uid=probe-service-account`, scopes=['read'],
`revoked_at IS NULL`, `last_used_at=2026-07-08T21:21:42Z`. `chart_grants` confirms `view` permission
on both chart_ids. Live-fired `judgment_query` (career) against prod on both charts via this
credential — both HTTP 200 with full payload. **LIVE, confirmed usable.**

### Chart serving state
Queried `phala_rectification_best.judgment_flags` (authoritative source for
`query_phala_calibration.ts`):

| chart_id | calibration_state | lel_event_count | load_bearing |
|---|---|---|---|
| 482012f1 (native) | calibrated | 57 | true |
| 1c826d5a (Abhinandan) | structural | 0 | false |

Matches expected state exactly. **PASS.**

### C0 verdict
**No HALT condition triggered. Proceed to C1.** Two non-blocking notes carried forward: (1) PR #484
merge to be confirmed before relying on any CI-gated automation; (2) fresh canary run recommended
before C4 grading to timestamp a clean current-state baseline (the d5105222 result stands as the
pre-C1 baseline for the brief's required before/after table).
