# Journey 6 reconciliation — evidence index

6 October 2026. Read-only source and prototype inspection; this is not a Journey 6 runtime qualification.

## Snapshots

- Planning checkout: `/Users/Dev/.codex/worktrees/journey-five/Madhav`, branch `codex/journey-five-design-final`, HEAD `0c438284e2eb9f40d9fa1d72ff6275df8f619f8f`.
- Refreshed main: `b1fe14efad5fe0d34d458322c6b7c0d7ef640149`. Application trees `platform`, `platform-mcp`, `python-sidecar` and `.github` match the planning checkout.
- Current Claude Design project: [Madhav — Current Portal · 04 Oct 2026 / Review Hub](https://claude.ai/design/p/acd0adbd-f395-43db-ab98-6df72a224e77?file=Review%20Hub.dc.html).
- All 15 Journey 6 pages were loaded individually, with each page's heading checked before recording its body. An initial asynchronous capture containing repeated prior-page content was discarded. Valid observations: `/Users/Dev/Documents/Codex/2026-10-06/journey6-reconciliation/design-page-observations.json`.
- Current source export reference: `/Users/Dev/Documents/Codex/2026-10-06/journey5-reconciliation/design-revision-08/project/`. Archive SHA256 `ed7e3f250e5bc880a81d8792ed93f81dc0bd68caca38c2b21a6a7802036479f7`, 115 files. No export or design was modified in this planning session.
- Owner feedback: `/Users/Dev/Documents/Codex/2026-10-04/claude-design-current/FEEDBACK_REGISTER_v1.0.md`; content includes later revisions. Relevant feedback F16, F19–22, F60–68 and F82–87.
- Journey 5 delivery boundaries: `../journey5/RELEASE.md`, `../journey5/RECONCILIATION.md`, `../journey5/DESIGN_FINAL.md`, CCD-024. Journey 5 source was implemented and deployed previously; owner design acceptance is a distinct open milestone.

## Grounded source references

Paths below are relative to the verified application snapshot. Consult their actual guards and action contracts during implementation; this index is not a substitute for fresh reads.

| Concern | Primary source | Finding used in the plan |
|---|---|---|
| Operator authority | `platform/src/lib/auth/access-control.ts`; `platform/src/app/admin/layout.tsx`; `platform/src/app/cockpit/layout.tsx` | Existing active `super_admin` guard; no new role needed. |
| Administration | `platform/src/components/admin/AdminClient.tsx`; `platform/src/components/admin/AiAccessTab.tsx` | Existing tabbed user/admission/chart/audit functions; per-product CLI grants already implemented. |
| Chart grants | `platform/src/app/api/admin/users/[id]/chart-grants/route.ts`; `platform/src/lib/auth/requireChartPermission.ts` | Reuse canonical chart permissions and grant mutation endpoints. |
| AI grant authority | `platform/src/app/api/admin/users/[id]/ai-cli-grants/route.ts`; `platform/src/lib/ai-console/repository.ts` | Active target/execution guards and audit; host availability differs from grant state. |
| Console availability | `platform/src/app/api/ai-console/_shared.ts`; `platform/src/app/account/ai-cockpit/console/page.tsx` | Feature gate and authenticated active account; no additional Console allowlist established by these guards. |
| Keys | `platform/src/app/api/mcp/keys/route.ts`; `platform/src/app/api/mcp/keys/[key_id]/route.ts`; `platform/src/app/admin/mcp/keys/page.tsx` | Admin creation, one-time generated secret, own/admin revoke; active-profile checks need normalization for list/revoke. |
| Shared ledger | `platform/src/lib/metering/queries.ts`; `platform/src/lib/metering/http.ts`; `platform/src/app/api/usage/route.ts`; `platform/src/app/api/admin/observatory/metering/route.ts` | Same normalized attempts/receipts plus deduplicated legacy data, separate populations and personal/operator guards. |
| Personal filters | `platform/src/lib/account/activity-filters.ts`; `platform/src/components/account/PersonalActivity.tsx` | Reuse semantics; strip privileged parameters when linking to personal scope. |
| Legacy operator analytics | `platform/src/lib/observatory/queries.ts`; `platform/src/app/api/admin/observatory/_parse.ts`; `platform/src/app/api/admin/observatory/analytics/cost-per-quality/route.ts` | Older usage-only queries and differing filters; quality probe explicitly unwired. |
| Current scope UI | `platform/src/app/(super-admin)/observatory/layout.tsx`; `platform/src/components/observatory/ObservatoryScope.tsx` | Current personal/operator mixed route needs compatibility and explicit scope, not blanket privilege assumptions. |
| Audit coverage | `platform/src/app/api/admin/audit-log/route.ts`; `platform/src/lib/admin/audit.ts`; `platform/src/lib/ai-console/audit.ts` | Separate source histories and limited read view; universal immutability/coverage not established. |
| Foundation | `platform/src/app/admin/foundation/page.tsx` | Table/environment presence and empty fallbacks cannot prove migrations or health. |
| MCP wiring | `platform/src/app/admin/mcp/health/page.tsx`; `platform/src/app/admin/mcp/health/McpHealthClient.tsx`; `platform/src/app/admin/mcp/health/McpHealthDashboard.tsx` | Route uses partial client; complete-looking alternative is not wired. Component paths should be rediscovered if moved before implementation. |
| Internal health APIs | `platform/src/app/api/mcp/health/tools/route.ts`; `platform/src/app/api/mcp/health/coverage/route.ts` | Internal-token endpoints and 24-hour snapshots; need guarded server/browser adapter and honest history. |
| Trace | `platform/src/app/admin/trace/[query_id]/page.tsx`; `platform/src/app/api/admin/trace/[query_id]/route.ts`; `platform/src/app/api/trace/history/route.ts` | Full operator trace exists separately from personal owned usage detail. |
| Asset evidence | `platform/src/app/admin/tracker/page.tsx`; `platform/src/app/cockpit/page.tsx` | Existing build evidence and operational root; incomplete projections/query failures need explicit states. |
| Hidden operational controls | `platform/src/app/cockpit/command-center/page.tsx`; `platform/src/app/admin/nirmana-elevation/page.tsx` | Preserve capability coverage and deep links; do not restart superseded programme work. |
| Programme evidence | `platform/src/lib/nirmana-elevation/programme.ts`; `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` | Historical programme projection and governed current/superseded state must be distinguished. |
| Learning authority | `platform/src/app/api/clients/[id]/learning/route.ts` | Chart-level actions and quarantine exist; observed publication/co-sign handler does not establish independent second-actor authority. |

## Evidence limits

The prototype uses illustrative records, counts, amounts and programme names. Those are design observations, not production facts. Source inspection establishes implementation gaps and current contracts; it does not prove every operational path works live. Learning authority concerns require review of the governed protocol before any publication redesign. No provider calls, real-account mutations, credential operations or deployment were performed for this reconciliation.

The plan recommends verification work rather than certifying absent wiring, statistical validity, historical measurements or receipt completeness. Current Hub review labels remain unchanged.
