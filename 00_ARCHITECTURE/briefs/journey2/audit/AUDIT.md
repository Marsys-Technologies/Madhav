---
artifact: JOURNEY2_BACKEND_AUDIT
version: 1.2
status: LOCAL_VERIFIED_LIVE_ACCEPTANCE_OPEN
---

# Journey Two integration audit

Journey Two is Consultation and Prediction Review: screen 10 Ask/Paripraśna, screen 11 legacy Saved Reading forwarding, screen 12 Samīkṣā, screen 13 Shared/Print Reading. The reviewed prototype's Saved Reading library was removed; exact conversation/exchange forwarding is the intended outcome. This audit follows the owner's request to audit, identify gaps, brainstorm, fix and build the frontend/backend integration.

Worktree: `/Users/Dev/.codex/worktrees/journey-two-audit/Madhav`; branch `codex/journey-two-backend-audit`; base `f2a5c3abba1689620c1dbe43a7df97af5eef8594`. Journey One's separate dirty worktree remains untouched. Source is local and uncommitted under GIP §P4. No deployment, application-database migration, real chart/account modification, paid inference or external message was performed.

## Outcomes and evidence

| Outcome | Backend/frontend finding and repair | Local verification |
|---|---|---|
| Ask a real chart | Removed the extra browser live-transport flag that could render fixture answers on a real chart. Server supplies the current BYOK flag; no stale build-time mismatch. HTTP errors are validated and mapped to fixed safe recovery text and AI Console links. Retry callback is wired. Inactive profiles are refused by chart/page/turn guards. | Real-chart component test posts to the live endpoint using server-supplied BYOK; provider execution remains simulated in tests. |
| Continue a saved consultation | Browser submitted only its current question and the server forwarded only that question to the model. Server now loads authoritative canonical/legacy saved context, bounded to 40 messages / 60,000 characters, and persists only the newly submitted user question. Rejects malformed arrays and client-forged assistant history. | Disposable PostgreSQL context test; transport restoration and route golden tests; browser source-thread continuation. |
| Reopen exact source answer | `?thread=` was generated but never opened by the page. It now passes through server props and opens the owned consultation. Transcript emits ordinal anchors and retains persisted-answer anchors. `answer=`/hash target scrolls after restoration. | Component integration reopens the saved conversation and submits its exact ID. |
| Tagged conversation/answer history | Existing owner-scoped tags and canonical restoration remain in use. Tags need durable saved message IDs, recheck current chart entitlement, and refuse correction-history mutations. Legacy saved answers no longer require a newer reading receipt to enable tagging or sharing. | Existing Consultation10 suites plus real PostgreSQL archive/tag test and browser answer-scope PATCH. |
| Legacy Saved Reading forwarding | `/readings` and `/readings/:id` destinations were absent. Added authenticated forwarding for owned conversation IDs and persisted assistant-message IDs, preserving exact thread and answer. An unqualified `/readings` returns to dashboard; an unknown ID is 404. | Production build registers both routes; route/page guards inspected. Real authenticated legacy-link acceptance is a release check. |
| Share one answer or the conversation | No selected-answer storage/control existed; current share read lacked a private-ownership/current-access check. Added per-answer UI and additive migration 1312. Owner+active profile+current chart entitlement required. Parent-row transaction serializes identical creates and archive races; expiry/revocation are scoped correctly. Failed revoke keeps the active link visible. | 20 real PostgreSQL integration cases cover scoping, concurrent reuse, expiry, revocation, privilege boundaries, FK cascade and rollback. |
| Read a public share | Proxy redirected all anonymous share links to login; canonical assistant prose could be blank because the old reader looked only at legacy blobs. Narrow public share/print allowlist now reaches the dynamic public reader. It filters private/provider/tool metadata, selected exchanges, methodology and optional reasoning; preserved canonical citations become readable Sources. Owner's current access and account status are rechecked. | Anonymous Next production-route/browser checks on desktop/mobile, privacy and expired/missing-link tests. |
| Print / Save PDF, Markdown and JSON | Export reader lost canonical prose and used export-time timestamps. It now uses the same reader-safe canonical/legacy text, actual saved timestamps, optional selected exchange and actual source citations. Private authenticated print and public print routes added. Old optional PDF dependency/501 path replaced by redirect to native browser Print/Save PDF. | PostgreSQL canonical JSON/PDF redirect test; actual browser-generated PDF. This is browser Print/Save PDF, not server-generated PDF bytes. |
| Confirm a prediction | In-stream confirmation created another row after capture already created a detected row; both confirmation surfaces could copy the latest conversation stamp instead of the source answer's stamp. Stream now confirms the captured row, validates its source part/conversation/chart, applies only explicit human edits, copies exact source provenance, and is retry-idempotent. Review confirmation is transactional. | Real SQL capture/repeat confirmation, later-turn provenance, immutable-claim trigger and missing-stamp rollback. |
| Review/resolve predictions | Batch outcomes were committed one-by-one; edit could report success after a zero-row UPDATE. Batch now locks/validates all chart-scoped rows and commits atomically; stale edits fail. Read-only chart viewers see disabled mutations. UI awaits edits/single and batch resolution, preserves failures and supports retry. | Real DB batch rollback/cross-chart guards; component failure/recovery tests. |
| Close windows automatically | Existing daily lifecycle job and configured workflow remain the authority. Tested actual due-window closure and durable once-per-day digest journal. | Real PostgreSQL daily job test; production scheduler state has not been refreshed. |
| Learn from actual outcomes | Outcomes and confidence are durably saved and Brier computation works. Existing `mimamsa_calibration` sink is explicitly PARKED and `calibration_persisted` remains false. No phantom-schema insert or false learning-success claim was introduced. | Real DB outcome/Brier test confirms the truthful parked state. See decision proposal. |

## Remaining operational gates

1. Owner review/publication and protected deployment of this exact patch, applying 1312 through the existing migration runner. It was applied twice only to the task-owned disposable PostgreSQL. Check actual production table size/lock duration before the bounded migration.
2. Authenticated live acceptance on an owner-approved chart, using an already-qualified AI choice and real engine/source data: first question, follow-up, persisted answer, reopen, tag, prediction confirmation/resolution, selected/whole share, revoke, export and print. Local tests/build do not certify production inference or engine completeness. Earlier engine/CLI failure evidence is a historical baseline, not a fresh live diagnosis here.
3. Conversational learning publication requires the separate Pratinidhi schema decision recorded in `PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE.md`; see `CALIBRATION_PROPOSAL.md`. This decision is not silently supplied by a frontend/backend audit.
4. Existing digest transport is honestly log-only. No real email-delivery adapter exists. Scheduled window closure and internal journal work locally; external notification delivery is not certified or added without a chosen delivery contract.

## Verification limits

The full unit suite passed 15,843 tests (1,088 skipped and 2 TODO); these skipped tests are not acceptance. All 20 separately enabled disposable PostgreSQL integration tests passed. Production build, TypeScript and ESLint have no errors. Browser evidence distinguishes the real anonymous Next server and disposable DB from the actual consultation component running against synthetic HTTP fixtures; no live Firebase/provider session was used. Screenshots and browser-generated PDFs were inspected. No full-system or production completion is claimed.

## Changelog

- 1.2: final local verification, legacy receipt-independent tags/shares and readable shared/print styling recorded; publication, live engine/provider acceptance, learning schema and external digest delivery remain open.

- 1.1: traced screens 10–13 and repaired consultation context, source links, public boundary, canonical exports/citations, exchange shares, privacy/expiry/revoke, prediction duplicate/provenance/transactions and recoverable UI errors. Local verification and release gates recorded.
- 1.0: audit opened.
