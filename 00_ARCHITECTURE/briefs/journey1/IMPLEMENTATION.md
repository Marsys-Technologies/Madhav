---
artifact: JOURNEY1_IMPLEMENTATION
version: 1.0
status: LOCALLY_IMPLEMENTED_ACCEPTANCE_PENDING
base_sha: 40e9ede5ada47b1a155cfb4f14dae607a63f38d7
---

# Journey 1

Owner-authorized implementation of pages 03–09 from the reviewed Claude Design final v1.0 ZIP (sha256 4f9eb14b6822407dbd9d73ecbfe1cbf4a4d4e4929580eb51b6895e736b7ac790). Journey 2 remains deferred. All source stays uncommitted per GIP §P.4. Production is untouched.

1. Entry: shared 3C Nakṣatra Wheel, selected Signature 12, Alegreya 2A controls, restrained jet black and gold. Real Firebase sign-in retained; independent request/recovery routes, username/email recovery and generic response; reset only uses token and new password. No demo auth, no fictional accounts.
2. Approved account setup: authenticated username choice/availability with DB unique-index race handling. Request access has no username field. Existing approval/admin controls remain functional; approved reset links direct users through setup after sign-in.
3. Chart collection: shared shell, consistent dual titles and language preference, cards open overview without duplicate actions, filters preserved.
4. Create/edit: preserve real birth location/timezone, all five ayanāṃśa selection and API recompute confirmation; consistent headings and back links.
5. Overview: real read-only per-chart summaries; North Indian diamond D1/D9/D10 slider, desktop469/mobile300; no legend/recent conversations. Independent chart services, review/activation windows, readiness, transit, dasha/yoga; unavailable data explicit. Reports placeholder.
6. Retain sharing/access authorization; view grantees receive no edit/build authority.

Validation: targeted auth/access/data/component regression tests, lint, types, full unit suite, local entry runtime and desktop/mobile component-browser checks. Any fixtures are explicitly test data, never added to production pages. No paid model, chart rebuild, migration execution or deployment.

Existing portal-cleanup worktree changes stay separate. Detailed peer pages continue on their existing shell pending Journey 2 review.

## Local outcome

Implementation and source checks are recorded in [REVIEW.md](REVIEW.md). This is a local code delivery, not deployment or live acceptance. The previously approved Claude prototype remains the design reference; this session did not create another design set.
