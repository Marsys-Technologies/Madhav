---
artifact: QUEUE_CANARY_SCRATCH.md
version: 1.0
status: THROWAWAY
produced_on: 2026-07-31
produced_during: org migration — merge-queue verification
authoritative_side: claude
role: >
  Throwaway payload proving the merge queue works after the transfer of this repository
  to the Marsys-Technologies organization. Deleted with its PR once the queue merge is
  confirmed.
implements: >
  Post-transfer verification: the four required checks must execute and report on a
  `gh-readonly-queue/main/...` ref, and this PR must merge via the queue.
changelog:
  - v1.0 (2026-07-31): merge-queue canary after org migration.
---

# Merge-queue canary (throwaway)

Inert by design: no code, no workflow, and under no workflow path filter, so a PR touching
only this file triggers exactly `ci.yml` — the four required checks and nothing else.

Merge queue became available only after this repository moved from the user account
`amonty84` to the `Marsys-Technologies` organization. GitHub's merge queue requires an
organization-owned repository; on the user account the Rulesets API rejected the rule
outright with `HTTP 422 Invalid rule 'merge_queue'`.

Delete this file and its branch once the queue merge is confirmed.
