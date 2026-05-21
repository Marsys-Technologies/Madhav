---
artifact: F2_CI_FINDINGS.md
packet: F.2
produced_at: 2026-05-21
status: COMPLETE
---

# Packet F.2 — CI Investigation Summary

## Source

Full investigation in:
`00_ARCHITECTURE/chat_v2_briefs/pr_111_remediation/CI_INVESTIGATION.md`
(authored by PR-111-REMEDIATION session; merged to main via PR #112, Packet A.1)

Raw check output:
`00_ARCHITECTURE/chat_v2_briefs/pr_111_remediation/_gh_checks_raw.txt`

---

## PR #111 context

PR #111 was on branch `fix/panchang-bootstrap-guard-target`. It was superseded by
PR #112 (`chat-v2/pr-111-remediation`) which addressed the 7 governance gaps cleanly
and was successfully merged (SHA `5554ba52`) in Packet A.1.

## Failing check 1 — Stage 3 E2E (Chromium)

**Run:** 26186224569 | **Classification: OUT-OF-SCOPE RESIDUAL**

3 failing tests in `mobile.spec.ts` and `axe.spec.ts`:
- Composer input `text-base` class assertion (iOS auto-zoom prevention)
- Action buttons `h-11 w-11` mobile sizing assertion
- Icon-only button `aria-label` WCAG assertion

Root cause: UI gap fixes committed in PR #111 adjusted CSS/ARIA but tests assert the
prior conventions. Fixing requires `platform/src/**` + `platform/tests/**` which were
`must_not_touch` for the PR-111-REMEDIATION session.

**Is this a regression from the governance work?** No. These tests were failing
specifically on the `fix/panchang-bootstrap-guard-target` branch due to UI changes
introduced in that branch, not in the governance remediation.

**Proposed next-step:** Separate focused session scoped to `platform/src/**` +
`platform/tests/**`. First check `KNOWN_PRE_EXISTING_FAILURES.md` — if the 3 tests
are already listed there, no action needed. Otherwise author a mobile/a11y fix session.

---

## Failing check 2 — smoke

**Run:** 26186224567 | **Classification: PRE-EXISTING INFRASTRUCTURE GAP**

9 failing tests in `round6-walkthrough.spec.ts` — all timeout at:
```
TimeoutError: page.waitForSelector('[data-testid="v2-chat-shell"]') timeout 10000ms
```

Root cause: `SMOKE_SESSION_COOKIE` + `SMOKE_CHART_ID` GitHub Actions secrets are not
configured for PR feature branches. The smoke suite requires live auth to render the
chat shell. This is a known infrastructure limitation, not a code regression.

**Is this a regression?** No. Pre-existing since the smoke spec was added (R6-SMOKE-PATCH
PR #75). Tracked in `KNOWN_PRE_EXISTING_FAILURES.md` (v1.1 baseline from R10 close-out).

**Proposed next-step:** Operator action — configure `SMOKE_SESSION_COOKIE` +
`SMOKE_CHART_ID` as GitHub Actions repository/environment secrets scoped to PR branches.

---

## Summary table

| Check | Run | Failing tests | Classification | PR #112 impact |
|---|---|---|---|---|
| Stage 3 — E2E (Chromium) | 26186224569 | 3 (mobile + a11y) | Out-of-scope residual (UI gap from #111 branch) | Not present — #112 has no UI changes |
| smoke | 26186224567 | 9 (auth timeout) | Pre-existing infra gap (secrets not configured) | Same pre-existing gap; not introduced by governance work |

**Conclusion:** Neither failure is a regression introduced by the governance work in
PR #112 or PR #113. Both are pre-existing residuals. The governance arc is clean.
