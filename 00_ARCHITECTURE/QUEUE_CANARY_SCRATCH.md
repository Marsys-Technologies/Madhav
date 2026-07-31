---
artifact: QUEUE_CANARY_SCRATCH.md
version: 1.0
status: THROWAWAY
produced_on: 2026-07-31
produced_during: CI campaign close-out — merge-queue adoption
authoritative_side: claude
role: >
  Throwaway payload for the merge-queue canary PR (branch ci/queue-canary). It exists only
  so a pull request can be opened whose diff touches NOTHING functional, and it is deleted
  together with that PR.
implements: >
  The queue-canary step of the CI close-out: observe the four required checks executing on
  a `gh-readonly-queue/main/...` ref before `strict: true` is switched off.
changelog:
  - v1.0 (2026-07-31): created as the queue canary payload.
---

# Merge-queue canary (throwaway)

Deliberately inert. No code, no workflow, and under **no workflow path filter** — so a pull
request touching only this file triggers exactly `ci.yml`, the one workflow with no
`pull_request` path filter and therefore the one carrying all four required checks:

- `TypeScript (src only)`
- `Unit Tests`
- `Secret Scan (unit 0b.2)`
- `Governance Gates (drift / schema / edge / native-literal / py-sidecar)`

That is precisely the surface the queue needs to be observed against: the required checks
and nothing else, with no advisory noise to read through.

It carries real frontmatter on purpose. A first draft without it added one
`schema_validator` violation (43 → 44). The exit code stays 3 either way, so CI would have
accepted it — which is exactly why it was worth fixing rather than shrugging at.

**Delete this file and its branch once the queue is proven.**
