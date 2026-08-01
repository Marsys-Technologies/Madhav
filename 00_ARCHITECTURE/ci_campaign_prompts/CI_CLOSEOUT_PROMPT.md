# Claude Code task — close the CI campaign (Madhav)

Four passes are done. This closes the remainder. Same standing rules — they are in
`00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md §6` and now number six:

1. A job-level `conclusion` is `success` even when a `continue-on-error` step exited 1.
2. n=1 is not a measurement (variance 285–422s on the identical command).
3. "Doesn't fire today" ≠ "the mechanism doesn't exist."
4. A mutation proves nothing until you confirm it reached the code under test.
5. Impossible instructions get recorded, not silently reordered.
6. **A clean automatic merge is not a correct merge** — semantic conflicts leave no markers.

Assume this brief also contains something unexecutable. The last four each did. Report it.

---

## Item A — Build the queue canary (Abhisek flips the switch)

The previous canary (#968) auto-merged before the queue was enabled, so there is nothing to test
with. **Create a purpose-built throwaway PR** and leave it open and green:

- Branch `ci/queue-canary`. One trivial, reversible change — a comment line in a doc file. It must
  touch **nothing** that any path filter watches, and must not modify a workflow.
- Confirm it triggers all four required checks and is green.
- Do **not** arm auto-merge on it. It must sit still until the queue is on.

Then write the observation procedure into the PR description so whoever watches it knows the
criteria without re-reading this brief:

- **PASS** — the four required checks appear *and complete* on a `gh-readonly-queue/main/…` ref,
  and the PR merges.
- **ABORT** — checks don't appear within a few minutes, **or any check on a queue ref reports
  `cancelled`** (means the `cancel-in-progress` fix didn't take; PRs will be evicted). Untick
  "Require merge queue"; no code revert needed.
- Apply rule 1 when reading those checks: a queue check reporting success while its step exited
  non-zero is the same old trap in a new place.

Abhisek enables the queue himself (Settings → Branches → `main`; batch 1; squash; `strict: true`
stays ON). Do not create a ruleset. After the canary clears, he unticks `strict` — not before.

## Item B — #895

**Ask the author to move the Postgres service container onto its own `db-integration-tests` job**
rather than leaving it on `unit-tests`. Rationale for the review comment: `unit-tests` is a
required check, so a container that fails to start blocks every merge in the repo. On its own job
the same flake is diagnosable and contained. The container itself is approved — 31s for 7 genuine
DB-integration tests is good value; this is about *where* it hangs, not whether it lands.

State in the comment that the 224s vs 195/210s figure is **n=1 against n=2 and within known
variance** — it is not evidence of a slowdown, and shouldn't be cited as one.

If the split is awkward on another author's branch, merging as-is is acceptable — say so and note
the accepted risk. Either way #895 merges **after** the queue canary has cleared.

## Item C — Merge #970

Docs-only gate-teeth record. Merge it once green.

---

## Item D — The three gates left in limbo (this is the part that will otherwise rot)

Each is currently a signal asserting more than it measures. Resolve all three; one PR.

**`absence_lint_gate` — relabel now, arm later.** It cannot fail as wired, but
`ABSENCE_LINT_STRICT=true` produces exit 1 / FAIL=10 on the same mutation, so the detector is
sound and merely unarmed. Do **not** flip it on blind — that turns CI red on 10 pre-existing
findings with no triage. Instead: (a) dump the 10 current findings into the PR body so they exist
somewhere a human can read them, and (b) rename the job so it stops calling itself a gate —
`absence lint (report-only, non-blocking)` or similar. Arming it is a follow-up that requires
someone to look at those 10 first.

**`r18` — prove the ratchet or narrow the claim.** Exit 4 on a missing directory shows it isn't a
no-op, but that is not the same as catching a *new* violation. Inject one and see. If it catches
it, record that and leave it alone. If it doesn't, change its name and header to describe what it
actually verifies.

**`mcp_tool_smoke` / `s13` / `tap7` — retire to `workflow_dispatch`.** Their secrets
(`TAP_MCP_SERVER_URL`, `TAP_DATABASE_URL`, `TAP7_API_BASE_URL`) have never existed and nothing is
scheduled to create them. A job that has never been able to run is not a passing job, and burning
a runner per PR to print a skip is pure cost. Retire, don't delete; header states the real reason
and the exact secret that re-arms it.

**`tap5` stays as-is** — it is the pattern the others should copy: 5 laws honestly SKIPPED, Laws 4
and 7 genuinely executed. Say so in the header so the next reader knows it's deliberate.

---

## Guardrails

- Branch per item; never commit to `main`.
- Nothing deleted; every change one line to revert.
- Do not rename or remove any required check.
- Do not create a ruleset.
- Prefer honestly red — or honestly skipped — over silently green.

## Deliverable

Prose. What you verified and how; what changed and its revert; anything contradicting this brief.

End with a plain statement: **is the campaign closed?** If the only remaining item is Abhisek
flipping the queue switch, say exactly that. If something else remains, name it — do not round up
to "done".
