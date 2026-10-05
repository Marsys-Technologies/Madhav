---
artifact: CONSULTATION10_IMPLEMENTATION
version: 1.1
status: IMPLEMENTED_LOCALLY_VERIFIED
---

# Consultation review 10

The live Paripraśna route `/clients/<chart-id>/pariprashna` now uses the shared Madhav shell and reviewed consultation layout. Scope is review 10 only. Source is local and uncommitted in `codex/portal-experience`, based on `32a463c1a0071d735ab3b8cb640f4f0eba758762`. No application PR, push, protected merge, deployment or real user/chart mutation occurred.

## Delivered

- Shared signature/header, icon-only title-language switch, chart navigation with separate Samīkṣā, chart identity and back link. Jet-black surface, restrained dark gold, Alegreya controls, rounded workspace.
- History and evidence side panels initially closed; desktop hover/focus expansion, explicit pin/release remembered per user, accessible mobile dialogs with dismissal and focus return. Closing does not immediately reopen a panel under the pointer.
- Right pane contains exactly Grounding, Windows and History. Actual citation/receipt evidence is preserved. Grounding placement selector below the composer selects inline or right pane; no redundant Ask/Readings/Samīkṣā strip. Fixed composer uses Ask and preserves model/BYOK, depth, length and stop/retry behavior.
- Database-backed conversation and individual-answer tags with All / Tagged conversations / Tagged answers history filters and search. Selecting an answer opens its committed conversation and scrolls to that answer. Tags are saved only after a successful server write and remain independent of writer metadata and conversation timestamps.
- Reopen owned, chart-authorized stored consultations using the original server conversation identity and canonical reader parts, with legacy text fallback. Late responses from an abandoned stream cannot resurrect the previous conversation. Older history responses cannot replace newer tag results.
- Correction-archived conversations remain read-only historical links. Current chart access is rechecked; super-admin chart access does not grant another user's private conversation tags. Receipt schema and integrity are validated before a stored reading is presented as verified.
- Existing share/export controls reused for committed conversations; shared reader and prediction engine unchanged. Windows show actual available prediction data, otherwise an honest empty state. No synthetic windows or production data inserted.

## Verification

`CHECKS.json`: full lint (zero errors, 628 inherited warnings), TypeScript, 1,413 unit test files / 15,663 passing tests, zero unexpected failures, whitespace check. Skipped/expected-failure suites are explicitly excluded from acceptance.

`BROWSER_VERIFICATION.json`: actual application components with fictional test-only data in a local browser harness; desktop 1440×1000, mobile 390×844, compact 390×480. Verified Ask → settled rendering, composer visibility, no horizontal overflow, default closed panels, exact three tabs, inline grounding, title toggle, persistent pin/release and mobile Escape. Screenshots under `Assets/screenshots/consultation10/`. The harness substitutes navigation/transport; it is not authenticated production acceptance.

`DATABASE_VERIFICATION.json`: actual task-owned disposable PostgreSQL 17, migration applied twice, owner isolation, canonical/legacy history SQL, invalid stored-receipt refusal and a real parent-row-lock race with chart correction. No application database was connected or migrated.

`RED_TEAM.md`: independent migration/integration review and bounded implementation review; findings corrected and retested.

## Release boundary and remaining acceptance

Migration `1307_consultation_tags.sql` is authored and reserved, **not applied to an application database**. New history/tag endpoints require it before serving the new UI. Deployment must recheck numbering against main and open PRs, verify the exact migration applied, and exercise authenticated streaming, history/tag persistence, sharing and model selections against an approved environment. Use the established protected release workflow; source-only completion is not release acceptance.

The pre-existing production consultation HTTP 400/engine residual is not diagnosed or repaired by this UI task. Historical reader reconstruction shows persisted reader text, citations and validated receipt; it does not invent stream-only timing, coverage or prediction windows. History retains the existing 100-conversation list limit. No saved-readings page is added. Samīkṣā redesign, other Journey 2 pages, Nirmāṇa, account/preferences and global cleanup are outside this implementation.

Primary shared checkout and pre-existing untracked portal planning/screenshots are preserved.
