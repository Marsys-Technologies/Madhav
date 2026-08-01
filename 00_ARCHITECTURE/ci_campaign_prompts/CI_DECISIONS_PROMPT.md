# Claude Code task — close out the three parked CI decisions (Madhav)

Abhisek has delegated these calls. The decisions below are made — your job is to **verify the
preconditions, then execute**, in the stated order. If verification contradicts a decision, **stop
and report instead of proceeding**: a delegated decision is not a licence to act on a false premise.

Same discipline as the last pass: state how you verified each claim; n=1 is not a measurement;
never trust a job-level `conclusion` for a `continue-on-error` step. Record any self-corrections in
`00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md §6`.

---

## Step 0 — Merge PR #964

Green at 19/0 with all four required checks passing. Abhisek has now reviewed and approved it.
Merge it. Delete the `ci-triggers` branch afterwards.

Before merging, add one line to the PR description if it isn't there: **`concurrency:` cannot
dedupe across event types**, which is why #963's concurrency groups did not cover the
push/pull_request double-fire. That's the obvious reviewer objection and the answer should be on
the record.

---

## Step 1 — Merge queue, and retire `strict: true`

**DECISION: adopt GitHub merge queue; drop `strict: true` once the queue is proven.**

Rationale, for the commit message and the audit doc: at 37 merges/day median (peak 104) against 30
open PRs and a ~9.5 min CI wall, `strict` demands a freshness property that is arithmetically
unachievable — it blocked #963 during the very session auditing it. The queue delivers what
`strict` was meant to guarantee (nothing lands untested against its true merge base) without
forcing every open PR to chase `main`. Safer *and* cheaper.

**This is staged, and the ordering is not optional.**

### 1a. Precondition — required checks MUST run on `merge_group`

A merge queue runs checks against a temporary `merge_group` ref. **Any required check whose
workflow does not declare a `merge_group:` trigger will never report, and every queued PR will hang
forever.** This is the single way this change can go badly wrong.

The four required checks — `TypeScript (src only)`, `Unit Tests`, `Secret Scan`,
`Governance Gates` — all live in `ci.yml`. Verify whether `ci.yml` currently declares
`merge_group:`. Based on the last audit it does **not**.

So: **first PR — add `merge_group:` to `ci.yml`'s triggers and nothing else.** Confirm the four
checks execute and report on a `merge_group` event before going near the queue setting. Note the
now-deleted `chat-v2-smoke.yml` did have a `merge_group` trigger, so there is prior art in this
repo — check git history for how it was written.

### 1b. Enable the queue

Enable merge queue on `main` with conservative settings: small batch size (start at 1–2 — batching
is where queues get confusing, and you can raise it later), and merge method matching current repo
practice.

### 1c. Prove it, then drop `strict`

Put **one real PR** through the queue end to end. Only after it merges cleanly, set
`required_linear_history`/`strict` off — i.e. uncheck "Require branches to be up to date before
merging". Keep all four required checks exactly as they are; **do not rename or remove any.**

**Rollback, one step:** re-enable `strict`, disable the queue. No code change is involved, so this
reverts from the GitHub UI in under a minute.

**Report before/after:** runner-hours/day, and how many re-runs the queue avoided over its first
day. If you only have hours of data, say so — do not annualise from one afternoon.

---

## Step 2 — Retire the ṢAḌ-DARŚANA W0.6 PLAN-mode gates

**DECISION: retire them. Do not arm them.**

Rationale: they cannot fail by construction, and their census is a false negative on 4 of 8 tools.
Arming a detector that is wrong half the time converts a meaningless pass into a **wrong** pass —
strictly worse. Fixing the census is a real piece of work on that lane, not a CI-cleanup task, and
it belongs to whoever next picks the lane up. Per CLAUDE.md §N.8, a gate that asserts more than it
measures must not stay green.

Execute:
- Move `specificity-gate-v0-plan`, `tri-plane-no-dead-end-gate-plan`, and
  `mode3-single-route-gate-plan` to **`workflow_dispatch`-only**. Do not delete the jobs or the
  scripts — one trigger line brings them back.
- Leave the two **census seeds** (`completeness-census-seed`, `authority-basis-census-seed`) and the
  **unit batteries** alone: their own header claims they are real gates needing no live server.
  **Verify that claim before relying on it** — check whether either has ever actually failed a
  build. If a "real gate" has never failed and cannot fail, it belongs in the retirement above;
  report it rather than deciding silently.
- In the workflow header, replace the stale "always exit 0 pending sibling lanes" note with the
  truth: retired 2026-07-31, cannot fail, census false-negative on 4/8 tools, re-arm requires
  fixing the detector first.

---

## Step 3 — `samiksha-daily` / `DATABASE_URL` — INVESTIGATE, do not guess

**DECISION: no blind rename.** Pointing it at `PROD_DATABASE_URL` looks obvious and would be a
guess about production data access — exactly the kind of assumption this campaign keeps catching.
Establish the facts first:

1. What has the job actually been doing? Pull its recent runs. Is it erroring, or silently
   succeeding as a no-op? A daily job that has "passed" for weeks while unable to reach a database
   is another earned-signal defect and the more important finding.
2. Does `DATABASE_URL` exist as an **environment**-scoped secret or variable rather than a repo
   secret? `gh secret list` alone will not show those. Check environment and variable scopes before
   concluding it is missing.
3. Read `platform/scripts/samiksha/daily_job.ts` — does it fall back, default, or fail closed?

Then:
- **If the secret genuinely does not exist:** do **not** silently repoint it. Add an explicit
  fail-fast so a missing DSN stops the job loudly instead of passing as a no-op, and report the
  finding with the run evidence. Repointing to `PROD_DATABASE_URL` is Abhisek's call, not yours —
  it changes which database a daily job writes to.
- **If it exists under another scope:** wire the scope correctly, and say which scope it was.

---

## Guardrails

- Branch per step. Never commit to `main`.
- Steps 1a, 2, and 3 are separate PRs — do not bundle.
- Every change revertible in one line or one UI toggle.
- Do not rename or remove any required check.
- Prefer honestly red over silently green, every time.

## Deliverable

Prose, not bullets. What you verified and how; what changed and its revert; what got faster with
sample counts (say "unproven" where it is); what is now honestly visible as broken; and anything
you found that contradicts a decision above — that last category is the most valuable thing you can
bring back.
