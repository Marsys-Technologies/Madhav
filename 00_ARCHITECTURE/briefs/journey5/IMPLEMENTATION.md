---
artifact: JOURNEY5_IMPLEMENTATION
version: 1.1
status: IMPLEMENTED_LOCALLY_RELEASE_PENDING
---

# Journey 5 — four connected account blocks

Owner requests plans, Claude Design, campaign update, frontend/backend and deployment. CCD-024 and lease L-PORTAL-JOURNEY5-DELIVERY-20261006 authorize this scope. This checkpoint records implementation and local source qualification; protected review/release and live acceptance remain pending.

- Identity/security: compact account index, username/name form with readonly email, fresh own Firebase reauthentication, password update and revoke-all/relogin, honest partial outcome and retry. Passwords never reach the application server. Real credential-changing browser acceptance is human-owned.
- Preferences: additive profiles.account_preferences JSON object, strict owned GET/PATCH, atomic partial merge and one shared provider for titles, independent pins, grounding, motion, reading size/depth. New owned readings start Deep; explicit choices survive late loads. Existing unowned Composer behavior remains compatible.
- AI setup/personas: four-destination cockpit, existing complete Console with owner-keyed query cache and one exact AI default; one transactional saved persona default consumed by new Consultation. Builtin Classical Parāśari fallback does not create records; legacy persona stack overrides remain preserved for the older reader.
- Activity/consumption: same authenticated-owner ledger and applied UTC dates/channel/purpose/provider/model/connection/source filters. API transport calls and CLI summaries stay separate. Provider receipts, calculated estimates and unknown cost stay separate. API outcome/latency charts expose units and gaps. Recorded connection/model attribution, conversation/question/call drilldown, separately paged CLI summaries and bounded exports retain unavailable evidence and retry failures. Tool-family telemetry is unavailable in the current backend; its future design and Sanskrit names remain provisional.

Claude Design updated the existing portal project and Journey05 board/Review Hub. Prototype fixtures and browser storage are separate from implementation. Independently found contract/chart mismatches were returned to Claude for correction. Versioned project archive is preserved with a SHA256 manifest under the private design-revision-03 folder. Full rendered inspection is still in progress at this checkpoint.

Local source checks:76 focused account tests with disposable PostgreSQL16, full suite15,774 passing tests across1,435 passing files,107 skipped files/1,060 skipped tests/2todo excluded from acceptance. TypeScript passes; full ESLint has zero errors and627 warnings (one new unused test parameter was subsequently removed). Next production build succeeds with fictional public Firebase configuration; final exact candidate/container qualification remains required. No Python/orchestrator changes.

Migration1310 is additive, runner-transactional and independently reviewed. Repeated application, JSON merge and concurrent persona-default semantics were exercised only in the named disposable localhost database. No application schema migration or deployment at this checkpoint.

Changelog: v1.0 — records local implementation, evidence and remaining release stages.

Final collision sweep covered all136 open PRs. Older Gochara PR3191 already contains1308; LEL reserves1309. Journey5 was renumbered before application to **1310_journey5_account_preferences.sql**. Only the unapplied filename/header changed; the reviewed DDL is unchanged. Earlier Journey5 reservation1308 is explicitly superseded in the coordination log, preserving the foreign1308 and1309 claims.
