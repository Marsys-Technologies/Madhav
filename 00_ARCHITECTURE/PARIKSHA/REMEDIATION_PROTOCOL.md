---
artifact: REMEDIATION_PROTOCOL.md
version: 1.0
status: LIVE
authored_at: 2026-05-31
role: How Vaidya scopes + authors + ships fixes on the fly during a Pariksha walk.
---

# Remediation Protocol v1.0

Vaidya is the only Pariksha agent that writes code. This document defines
how Vaidya gets activated, scopes its work, opens PRs, and either waits
for human review or auto-merges under tight conditions.

## Activation triggers

Vaidya activates when ALL of the following are true:

1. Pratisamhita has assigned an issue or root cause cluster severity
   ≥ operator's auto-fix floor (default: workflow_blocking)
2. Issue is tagged `vaidya_eligible: true` in triage
3. Issue's `fix_attempts < 2` (retry budget)
4. No other Vaidya is currently active for this chart_id (mutex)
5. Operator authorization for this arc allows code writes (not observe-only)

When triggered, Vaidya writes a `vaidya_paused` block to the chart's
resume_state.yaml so Drashta knows to wait.

## Scoping rules (the hard ones)

Every Vaidya activation MUST declare:

```yaml
vaidya_scope:
  issue_id: I-001
  may_touch:
    - platform/src/components/clients/NewClientForm.tsx
  must_not_touch:
    - platform/src/app/api/clients/create/route.ts   # API is contract; FE adapts
    - Any file outside the issue's suspected_files set unless explicitly added
  branch: fix/pariksha/I-001-gender-enum
  estimated_loc_delta: ~5
  test_file_to_extend: platform/src/components/clients/__tests__/NewClientForm.test.tsx
```

If during the fix Vaidya discovers it needs to touch a file outside the
declared scope, it HALTS and writes a `scope_expansion_requested` entry
in the issue's history for operator review. No silent scope creep.

## The fix lifecycle

```
1. Pratisamhita ranks issue → notifies Vaidya
2. Vaidya reads issue evidence + suspected_files + existing tests
3. Vaidya creates branch `fix/pariksha/<issue_id>-<short-slug>`
4. Vaidya authors the patch within may_touch scope
5. Vaidya extends or adds a test that would have caught this issue
6. Vaidya commits with a structured message (see below)
7. Vaidya pushes; opens PR via gh
8. PR title: `fix(pariksha): <issue title>`
9. PR body includes:
     - Link to issue ID in the ledger
     - Evidence from the Drashta + correlating watcher signals
     - Patch summary
     - Test added/extended
     - Confidence statement
10. Vaidya waits for CI checks via `gh pr checks <N> --watch`
11. Outcomes:
    a. CI green + operator auth allows auto-merge + LOC ≤ 30 + single file
       → Vaidya `gh pr merge --squash`
    b. CI green + auto-merge not allowed → leave for human review
    c. CI red → auto-fix loop up to 3 attempts; if still red, mark
       `fix_failed`, increment fix_attempts, halt or retry per budget
12. If merged + auto-deploy succeeded → Naya-Pariksha re-runs the walk
    from the checkpoint; if the issue is resolved, mark closed
13. If re-run produces the SAME issue → mark `fix_did_not_resolve`,
    escalate to native review
14. If re-run produces a NEW issue caused by the fix → mark `regression`,
    revert the PR (via revert PR), escalate
```

## Structured commit message format

```
fix(pariksha): <issue title>

Issue ID:        I-001
Severity:        workflow_blocking
Root cause:      RC-001 (form-to-API field name drift)
Discovered by:   drashta, aapti_drashta (corroborating)
Surface:         /clients/new

Evidence (excerpted from issues.yaml):
  POST /api/clients/create returned 422 with errors[0].field='gender'.
  UI sent 'Male' (lowercase letter sequence) but API VALID_GENDERS expects 'M'.

Fix:
  In NewClientForm.tsx, change gender <option> values from
  'male' / 'female' / 'other' / 'not-specified' to
  'M' / 'F' / 'O' / 'unknown' matching the API contract.

Test:
  Added test in NewClientForm.test.tsx asserting that gender option values
  match the API's VALID_GENDERS set. Test fails on the pre-fix state.

Confidence:      high
Pariksha arc:    builds/362f9f17.../
```

## Auto-merge conditions (tight)

Auto-merge is OFF by default. When operator opts in, Vaidya may auto-merge
ONLY when ALL true:
1. Severity is `workflow_blocking` or `data_integrity`
2. Total diff is single file
3. LOC delta ≤ 30
4. Test was added or extended
5. CI is fully green (no flaky-test bypass)
6. The fix did NOT touch any file in a "high-risk" allowlist:
   - `infra/**`
   - `.github/workflows/**`
   - `platform/migrations/**`
   - `platform/src/app/api/build/**` (build orchestration is too central)
   - `platform/src/middleware.ts`, `platform/src/proxy.ts`

If any condition fails, PR stays open for human review.

## Conflict resolution

When Vaidya's PR cherry-pick conflicts with main (because another agent
just merged):
- Attempt 1: clean rebase
- Attempt 2: `git pull --rebase` + retry
- Attempt 3: declare conflict unresolvable; tag issue `merge_conflict`;
  halt; escalate

## What Vaidya never does

- Never push directly to main
- Never modify or delete a file outside `may_touch`
- Never disable a failing CI gate to make CI green
- Never weaken a test assertion to make it pass
- Never run a destructive prod operation (DB writes, deploys, IAM changes)
- Never modify Pariksha's own files (`00_ARCHITECTURE/PARIKSHA/**`)
- Never use Anthropic models

## Retry budget

| Fix attempt | What happens |
|---|---|
| 1 | First Vaidya tries the fix per scope |
| 2 | If 1 failed (CI red after auto-fix loop OR re-run did not close), spawn a second Vaidya with reset scope + the failure record from attempt 1 as additional context |
| 3+ | Halt. Mark issue `escalated`. Native review required. |

## Operator-side override

Operator can at any time:
- `touch 00_ARCHITECTURE/PARIKSHA/STOP` — halts all Pariksha agents within 60s
- Mark an issue `wont_fix` in issues.yaml — Vaidya skips it
- Close a Vaidya PR manually — Vaidya logs the manual close and moves on
- Reset an arc — `rm -rf 00_ARCHITECTURE/PARIKSHA/builds/<chart_id>/`

## Integration with Drashta resume

When Vaidya activates:
1. Vaidya writes `vaidya_paused{}` block to chart's resume_state.yaml
2. Drashta sees this on next checkpoint write → exits gracefully
3. Vaidya proceeds independently
4. On Vaidya success → fixes resume_state.yaml: clears vaidya_paused,
   appends a `fix_applied` history entry
5. Naya-Pariksha picks up the resume → re-runs the walk from the checkpoint
6. Naya-Pariksha verifies the issue is closed (the failing assertion now passes)

## Confidence model

Vaidya scores its own confidence before committing:

| Confidence | Conditions | What happens |
|---|---|---|
| high | Single file diff, ≤30 LOC, existing test pattern covers the fix, no other agents flagged uncertainty | Auto-merge eligible |
| medium | Single file but >30 LOC, OR cross-file but each diff ≤20 LOC, no flaky tests touched | PR-only |
| low | Cross-file with risky paths, OR no test coverage for the fix, OR Pratisamhita flagged "complex" | PR-only with `review_strongly_advised` label |

Vaidya may also score itself low when it's unsure of a root cause:
"I patched the symptom but I'm not confident this is the root cause." That
sentence in the PR body triggers PR-only + human review.

## Logging

Every Vaidya action writes to `00_ARCHITECTURE/PARIKSHA/builds/<chart_id>/vaidya.log`:
```
2026-05-31T22:14:32Z vaidya activated for I-001
2026-05-31T22:14:50Z scope declared: may_touch=[NewClientForm.tsx]
2026-05-31T22:15:14Z patch authored (4 LOC delta)
2026-05-31T22:15:18Z test extended (NewClientForm.test.tsx)
2026-05-31T22:15:32Z PR #182 opened
2026-05-31T22:18:14Z CI green
2026-05-31T22:18:18Z PR merged (auto, conditions met)
2026-05-31T22:23:00Z deploy.yml run 26720001234 success
2026-05-31T22:23:10Z naya-pariksha notified to resume
```

This log is the audit trail of every autonomous fix and is the basis of
operator trust in the system.
