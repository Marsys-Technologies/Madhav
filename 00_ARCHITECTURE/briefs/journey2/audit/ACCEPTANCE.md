---
artifact: JOURNEY2_LIVE_ACCEPTANCE_PLAN
version: 1.0
status: READY_FOR_OWNER_RELEASE_DECISION
---

# Journey Two release and outcome acceptance

The local patch is verified. Whole-system acceptance remains open until the exact integrated release and real-user flow below pass. This is a concrete release plan, not authorization to perform it.

1. Review the uncommitted candidate in `codex/journey-two-backend-audit`, reconcile Journey One's overlapping active-profile guard and common session pointers, and obtain publication authority under GIP §P4. Refresh main, migration reservations and current deployed schema. Migration 1307 is a prerequisite for owner-scoped tags; confirm its application rather than assume a prototype or earlier local test applied it. Publish through the repository's ordinary protected checks/review.
2. Authorize migration 1312 and deployment. Rehearse against production-like table size; the additive nullable FK/index is bounded by 5-second lock and 30-second statement timeouts. Use the existing migration runner transaction. A failed bounded migration must abort safely; no unrestricted retry/DDL shortcut. Apply once, verify actual column/FK/index, then release the matching code and verify serving SHA/traffic. Coordinate protected production authority separately from source leases.
3. Use an owner-approved chart and account with actual access, complete current source/build evidence and an already-qualified AI choice. Confirm active user and view/consume versus all permissions. Ask a question, record the returned provider/run and source evidence, then follow up. Verify that the follow-up references saved history and persists only its new user question. A model catalogue or local fixture is not successful inference.
4. Refresh the browser: verify restored canonical prose and receipt/source links, reopen the exact source answer, tag conversation and answer, and verify All / Tagged conversation / Tagged answer results. Test exact legacy conversation/message links while signed in, unauthorized links and archived correction-history behavior.
5. Share the conversation and one persisted exchange. In an anonymous browser verify only selected content, citations and authorized reasoning; no private methodology/provider/tool data or later exchanges. Verify revoked, expired, disabled-owner and access-removed links fail closed. Print/Save PDF at phone and desktop widths; verify legible text, readable sources, no action buttons/private reasoning in PDF. Verify private print still requires the owner session and matching chart. Download Markdown/JSON and compare saved timestamps/content to the selected exchange.
6. Capture a prediction and then produce a later consultation turn. Confirm the original captured row from both surfaces; verify exactly one row and original source provenance, immutable accepted claim, retry idempotency, and no automatic detected-to-open promotion. Edit/dismiss/review only authorized current rows. Resolve a selected batch and demonstrate all-or-nothing failure plus actionable browser recovery. Confirm confidence-band mapping and factual outcome/Brier values.
7. Verify the actual scheduled lifecycle job closes due windows once and journals its digest. Log-only transport is not external delivery. External email notifications need an explicit delivery contract, credentials and separately authorized delivery acceptance.
8. Obtain the separate native conversational learning schema ruling in `CALIBRATION_PROPOSAL.md`, implement its approved sink and versioned idempotent publication, and verify actual published records and feedback consumption. Until then report `calibration_persisted: false`; factual outcomes/Brier alone do not prove a learning loop.

Completion requires evidence for all applicable outcomes above, a matching deployed revision and owner acceptance. Learning publication and promised external notifications cannot be marked complete while their contracts remain parked/unimplemented. If those are deliberately excluded from a release, record that owner scope decision explicitly.

## Changelog

- 1.0: concrete protected release and real chart/provider acceptance plan.
