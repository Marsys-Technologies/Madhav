---
artifact: CONSULTATION10_RED_TEAM
version: 1.0
status: PASS_WITH_FIXES
---

# Bounded review

Independent `migration-guard` agent reviewed additive migration 1307 and its application ownership/read-only integration. Verdict: MIGRATION SAFE after the parent-row-lock correction; no production access. This is an independent migration/integration review, not an independent whole-product UI audit.

Implementation review and actual local browser verification covered stream identity, stored-reader trust, default/pinned panels, keyboard/mobile behavior and tag failures. The following findings were corrected:

1. **Concurrent chart correction / answer tag:** a message UPDATE joined to conversations did not lock the parent. Use a transaction and lock the owned, unarchived parent with `FOR UPDATE` before updating the assistant message. Real PostgreSQL lock-wait evidence proves refusal after a racing correction commits.
2. **Untrusted stored receipt:** validate receipt schema and integrity on the server before surfacing verified evidence; malformed stored receipt is omitted.
3. **Stale stream identity:** restored/reset stream generation invalidates late responses from aborted prior requests. Regression verifies no prior identity or turns reappear.
4. **Duplicate React keys:** transcript and composer had the same conversation key, causing duplicate turn DOM after real Ask submission. They now use distinct keys; actual component browser check passes.
5. **Explicit close reopened under hover:** suppress pointer expansion after a close until the pointer leaves; skip programmatic focus re-expansion. Desktop close and mobile Escape verified.
6. **Canonical-only history preview:** canonical message_parts text is preferred with legacy parts_json fallback; actual database assertions cover both.
7. **Out-of-order history refresh:** request generation prevents a stale refresh from overwriting newer results after tagging.

No engine/provider qualification, production acceptance, or other review pages are certified by this report. Remaining release gates are in IMPLEMENTATION.md.
