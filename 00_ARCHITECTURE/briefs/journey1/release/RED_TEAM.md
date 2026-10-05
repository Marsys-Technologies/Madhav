---
artifact: JOURNEY1_RELEASE_ADVERSARIAL_REVIEW
version: 1.0
status: PASS_WITH_DISCLOSED_LIMITS
---

# Journey 1 release — in-session adversarial review

Performed by the implementation/release agent; this is not independent agent review or human acceptance.

1. Authentication: sign-in retains Firebase verification and active-profile/session enforcement; setup requires an active authenticated user. Disabled/pending profiles cannot acquire sessions. Existing profile auto-sync behavior was preserved. Auth/onboarding regression tests cover the refusals.
2. Ownership: username availability excludes only the caller UID; update targets only that verified UID/active status, validates normalized syntax and handles database uniqueness conflicts. Invalid JSON shapes reject. Existing chart layout/read/edit/build/admin guards remain; an overview link does not authorize its destination.
3. Recovery/privacy: active username/email resolve on the server, successful match and non-match share a generic response; unknown accounts never return email/existence. Rate limit, foreign-origin and provider-outage tests pass. No recovery email or production password/approval was triggered.
4. Read fidelity: chart divisional reader pins fact category/key, chart ID and canonical frame; D9/D10 have their own stored Lagna/positions and explicit empty states. Timing display only admits qualified/confirmed authoritative stored windows using the existing peak basis; context/prior data is not upgraded to predictive claims. No derived-data writer changed.
5. Navigation/accessibility: hooks execute consistently across detailed legacy routes, accessible collapsed rail labels remain, title preference changes headers only, mobile drawer traps focus/closes on Escape, native slider has labels/keyboard behavior. Scoped styles and fonts avoid changing deferred consultation pages.
6. Release isolation: reviewed payload excludes pre-existing audit files and the separate cleanup worktree. Current main's already-released migration1297 is inherited, not authored or reapplied manually. The three ancillary changes only type existing test fixtures; security assertions are retained. No quality bypass or cloud/IAM/credential changes.

Evidence: full lint zero errors (628 existing warnings), all types pass, 1,409 unit files / 15,655 tests pass with zero unexpected failures. Runtime public entry and fictional imported-component checks were completed in the implementation session. Protected CI Docker build and no-traffic candidate smoke/promotion remain before declaring deployment. Real approval/reset/username-save/CRUD acceptance requires deliberate account/data actions and is not manufactured by this read-only release verification.
