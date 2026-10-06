---
artifact: DESIGN_FINAL.md
version: 1.0
status: DESIGN_VERIFIED_APPLICATION_UNCHANGED
date: 2026-10-06
authority: CCD-024
---
# Journey 5 final prototype state correction

The four-block application delivery remains deployed and read-only verified through PR3197, source2c117ba1, deployment37415721436 and migration1310. PR3199 merged the release records as09fd39b4 at06:17:45 UTC. This follow-up corrects remaining illustrative preview states and updates their current archive; it changes no application source, SQL, provider setting, credential, grant or serving revision.

## Current design

[Journey05 board](https://claude.ai/design/p/acd0adbd-f395-43db-ab98-6df72a224e77?file=Journey+05.dc.html) and the existing Review Hub remain the review entry points. Revision08 exported at2026-10-06T06:35:19.136725+00:00,115 files, archive SHA256 `ed7e3f250e5bc880a81d8792ed93f81dc0bd68caca38c2b21a6a7802036479f7`. Private archive: `/Users/Dev/Documents/Codex/2026-10-06/journey5-reconciliation/design-revision-08/claude-design-project.zip`. `DESIGN_EXPORT.json` retains the full dated revision06 release snapshot and now identifies revision08 as current. Original archive06 and its earlier close are retained.

## Scoped corrections

- My Observatory failures use only the same API rows and denominator as the API outcome line. Normal7-day fixture:5,772 API calls,18 failures(0.31%);711 CLI summaries,4 failures,412 unattributed. Daily and tree failures are separate.
- Selected connection/model declarations determine measured, unreported and excluded populations. A recorded CLI zero is numeric0; an unreported CLI is unavailable; API/CLI source exclusions are explicit. Cockpit and Console activity summaries and Consumption use the same states.
- Explicit empty preview suppresses normal fixture costs, counts, conversations and question details. An unknown CLI scope stays unknown rather than becoming empty because the positive-row total is0. API receipts/estimates excluded from a CLI-only scope are labelled excluded; no per-call CLI price is invented.

## Independent verification

Actual refreshed browser: both pages show honest unknown CLI+c4 and explicit empty states; API/CLI scopes and normal fixture arithmetic checked. My Observatory and Consumption at320/390/1440 have no page-wide overflow (DOM title and actual frame width asserted). Scope persisted between the pages. Owner acceptance is still open.

Export06→08 differs only in `PgOps.dc.html`, `PgAccount.dc.html`, `portal-data.js` and generated`.thumbnail`. Shared ledger addition only returns derived `apiState`/`cliState`;45 combinations of7/30/today × source × connection compare all prior returned values byte-for-byte after excluding those two new fields. The system/admin Observatory branches, fixture rows, all other115-file project members, Journey05 board, Review Hub, Foundations and other journeys remain unchanged. Full scoped diffs and every file hash are retained privately.

Actual exported-component logic independently passes all/API/CLI/unreported/empty and an explicitly synthetic recorded-zero test for both pages. **The existing normal fixture has no measured CLI day with0 calls; the zero test is offline logic evidence, not a reachable browser or live-account observation.** See private revision08 `STATE_LOGIC_CHECKS.json` and `design-final-layouts.json`.

## Application and open limits

Fresh service check at this handoff: Ready=true, accepted2c revision at100% traffic, health200/ok. Protected source tests remain76 focused and15,774 full passing tests; types, lint0errors and builds pass. No source change warrants rerunning those local suites. Required hosted protection remains in force for publication of this metadata follow-up.

`RELEASE.md` remains the actual application release evidence. Human password/session-changing acceptance, paid-provider execution and owner design acceptance remain unperformed. Existing saved Claude Code default needs attention/execution qualification; inherited pre/post Consultation smoke HTTP400/6-of11 failures are not fixed or certified by Journey5. Shared-credential diagnostic disclosure remains a coordinated rotation follow-up; no secret is in this record/export and no credential was rotated. Original deployment/design leases stay released; the new design-only correction lease is released with its own remote receipt in the close.

Changelog: v1.0 records the final scoped prototype correction and independently qualified archive after the original application release and protected metadata handoff.
