# Claude Code task — drop `strict` on `main`, close out the CI campaign (Madhav)

The merge queue is unavailable on this repo (User-owned; GitHub merge queue requires an org — this
was proven four ways, ending in `POST /rulesets` → HTTP 422 `Invalid rule 'merge_queue'`). Abhisek
has chosen the alternative: **drop `strict` (require branches up to date) from classic branch
protection, keeping all four required checks.** This removes the livelock that blocked this
campaign's own PRs four times.

This is a one-field change to branch protection. Do it verified and reversible. Standing rule that
applies most here: **verify on the API, not from assumption** — read the config before and after,
and diff.

## Step 1 — Capture the exact current state

`gh api repos/amonty84/Madhav/branches/main/protection > /tmp/prot_before.json`

Confirm from it (stop and report if any differs — the change assumes this baseline):
- `required_status_checks.strict == true`
- `required_status_checks.contexts` (or `checks`) is exactly the four:
  `TypeScript (src only)`, `Unit Tests`, `Secret Scan (unit 0b.2)`,
  `Governance Gates (drift / schema / edge / native-literal / py-sidecar)`
- `enforce_admins == true`, `required_pull_request_reviews` absent (require-PR OFF)

## Step 2 — Flip only `strict`

Set `strict` to `false` and change **nothing else**. The clean way is the dedicated endpoint, which
touches only the status-checks object:

`gh api --method PATCH repos/amonty84/Madhav/branches/main/protection/required_status_checks \
  -f strict=false`

If that endpoint proves awkward, fall back to a full `PUT .../protection` — but only by taking
`/tmp/prot_before.json`, setting `strict:false`, and replaying **every other field unchanged**. A
partial `PUT` silently drops omitted protections; that is the failure mode to avoid. Prefer the
narrow PATCH above precisely because it cannot do that.

## Step 3 — Verify

`gh api repos/amonty84/Madhav/branches/main/protection > /tmp/prot_after.json`, then
`diff <(jq -S . /tmp/prot_before.json) <(jq -S . /tmp/prot_after.json)`.

The diff must show **exactly one change**: `strict` true → false. The four contexts, `enforce_admins`,
and the absence of required reviews must be identical. If anything else moved, restore from
`/tmp/prot_before.json` and report.

## Step 4 — Housekeeping

- Close **#972** (queue canary, now superseded) and delete its branch. Its description already says
  it's obsolete.
- Leave #967's `merge_group:` trigger in `ci.yml` in place — it's inert without a queue (fires only
  on a `merge_group` event, which can't occur here) and re-arms instantly if the repo ever moves to
  an org. One dead line is cheaper than a churn PR.
- Record the change in `00_ARCHITECTURE/CI_EFFICIENCY_AUDIT_v1_0.md §6` (new subsection): `strict`
  dropped, why (queue unavailable on a User-owned repo; livelock cost measured at 4 blocked PRs this
  campaign), and the one-line rollback.

## Rollback (one command)

`gh api --method PATCH repos/amonty84/Madhav/branches/main/protection/required_status_checks \
  -f strict=true` — restores the prior state exactly.

## Deliverable

Prose. The before/after diff (proving exactly one field moved); confirmation the four required checks
still gate `main`; that #972 is closed; and a plain final line: **is the CI campaign now closed?** If
yes, say so — this was the last open item.
