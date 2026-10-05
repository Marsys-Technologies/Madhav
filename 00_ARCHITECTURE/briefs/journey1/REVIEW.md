---
artifact: JOURNEY1_REVIEW
version: 1.0
status: LOCALLY_IMPLEMENTED_ACCEPTANCE_PENDING
---

# Journey 1 — implemented locally

The seven reviewed pages are implemented in the actual Madhav application, with the supporting approved-user username setup. This is a local, uncommitted delivery for review; production is unchanged. Journey 2 remains deferred.

| Review number | Page | Application route | Result |
| --- | --- | --- | --- |
| 03 | Sign In | `/login` | Username or email modes; existing Firebase sign-in/session; shared identity and nine-graha entry animation. |
| 04 | Request Access | `/login/request-access` | Existing request submission; name/email/reason; username chosen after approval. |
| 05 | Recovery / Reset | `/login/recovery`, `/reset-password` | Username or email recovery with a generic response; existing Firebase token/password reset. |
| 06 | Birth Charts | `/dashboard` | Shared navigation and title treatment; existing filters, authorization and readiness; one overview link per card. |
| 07 | New Chart | `/clients/new` | Existing authorized chart creation and all five ayanāṃśa choices; responsive form and back link. |
| 08 | Selected Chart Overview | `/clients/<id>` | Smaller North Indian chart; D1/D9/D10 slider; identity beside chart; full-width qualified summaries and chart service links. |
| 09 | Chart Details & Access | `/clients/<id>/edit` | Existing birth details, timezone/ayanāṃśa changes and recompute confirmation; authorized sharing controls at `#sharing`. |
| Supporting flow | Approved account username setup | `/setup-account` | Active authenticated users choose an available username; validation, retry and unique-index conflict handling. |

## Feedback incorporated

Marsys deep jet black, restrained darker gold, rounded controls, selected Signature 12 with peacock feather, Alegreya 2A for everyday text and Cormorant headings. Fonts are self-hosted with their licenses. A single translate icon switches the two page-title languages and persists the preference; the page body is unchanged. The navigation rail expands on hover/focus, can be pinned, and becomes a keyboard-accessible mobile drawer.

The entry design uses the approved 3C Nakṣatra Wheel: the unchanged Marsys medallion serves as the central Sun, surrounded by eight moving grahas, zodiac/nakṣatra rings and restrained stars. Reduced-motion preferences are respected.

The overview has the North Indian diamond chart, no legend and no recent-chat or latest-event panels. Desktop chart width is about 469 CSS pixels; mobile is about 300. D9 and D10 use their stored divisional data, never a reused D1. Chart-specific frame identifiers use the existing canonical ayanāṃśa mapping. Qualified stored activation/transit windows appear as a timeline; prior/context-only windows do not become timing claims. Missing data is shown honestly. Separate Samīkṣā, Nirmāṇa, Personal Almanac, Life Events and Reports links are retained. Reports is a protected placeholder only. No new report engine or almanac computation was built.

Access controls live on Chart Details & Access. The overview action menu links there. Existing owner/grantee/admin boundaries remain: viewing a chart does not grant editing or building rights. Security audit remains an administration destination. Retired global Cockpit/general Pañcāṅga/audit/performance links are absent from the new Journey 1 rail. The separate legacy cleanup worktree was not changed.

The full Account/AI Cockpit and detailed Journey 2 services are deferred. The new account affordance currently leads to the real username setup screen; detailed peer pages retain the existing shell until their review is completed.

## Design provenance

Source: approved Claude Design `review-revision-02/html/` and `claude-journey1-final-v1.0.zip`, SHA256 `4f9eb14b6822407dbd9d73ecbfe1cbf4a4d4e4929580eb51b6895e736b7ac790`. Signature 12 comes from the approved `madhav-shared.js`, not the stale wordmark SVG. This session implemented the reviewed design; it did not create another design set.

## Verification

- Full unit suite: **1,408 files passed; 15,648 tests passed; zero unexpected failures**. Existing skips: 107 files, 1,060 tests; three expected failures and two todo tests.
- Type checking: **passed**.
- Lint on every changed application/test file: **zero errors**, three existing warnings in `NewClientForm.tsx`.
- Repository-wide lint: **nine existing errors and 628 warnings**. The errors are in three untouched unrelated tests: data-plane secret isolation and the Gochara provisioning/seal workflow static tests. These were not silently fixed or treated as a green release gate.
- Actual local application: sign-in, recovery and request screens loaded; username/email mode, title toggle persistence and entry rendering checked. Public Firebase configuration was fictional; no real account/password/recovery request was submitted.
- Actual imported chart/form/shell components were exercised separately with explicitly fictional fixtures and all API submissions blocked: desktop/mobile layouts, D1/D9/D10 keyboard switching, missing divisional data, pin persistence, mobile drawer/Escape and all five ayanāṃśa choices. This is component verification, not authenticated application acceptance.
- Governance validation: zero session-open violations; drift has two LOW findings because the local database at port 5433 lacks credentials. No production connection was substituted.

Machine-readable results: [CHECKS.json](CHECKS.json). The session-close inventory records changed-file hashes and scope. A production build and real signed-in end-to-end acceptance have not been performed.

## Screenshots

[Implemented sign-in in Chrome](../../../Assets/screenshots/journey1/sign-in-desktop.jpg). Other IAB captures show the visible portion of the review pane and may be clipped; responsive measurements above come from the rendered viewport. [Chart desktop component fixture](../../../Assets/screenshots/journey1/chart-desktop-fixture.jpg), [chart mobile component fixture](../../../Assets/screenshots/journey1/chart-mobile-fixture.jpg), [chart details mobile component fixture](../../../Assets/screenshots/journey1/chart-details-mobile-fixture.jpg). Chart screenshots use test data; they are not production records.

## Remaining release checks

Before publishing, run approved non-production signed-in acceptance with real Firebase/database configuration: username and email sign-in/session/logout; recovery email delivery and token reset; request approval → password setup → available username selection including conflicts; owner/view-grantee/admin chart permissions; create/edit and rebuild confirmation; correct chart frame/divisional data and Maps/Places behavior. Resolve or disposition the repository-wide lint errors through their owning workstream. These checks do not require reviewing Journey 2 first.

No source commit, PR, merge, deployment, migration, production record/permission mutation, chart rebuild or paid AI call was performed. The app preview is at `http://127.0.0.1:3187/login` and is left running only for local review.
