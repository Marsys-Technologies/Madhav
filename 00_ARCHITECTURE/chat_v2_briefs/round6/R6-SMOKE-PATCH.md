---
name: R6-SMOKE-PATCH EXEC BRIEF — auth wall fix for round6 walkthrough spec
canonical_id: CHAT_V2_R6_SMOKE_PATCH_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored: 2026-05-18
governing_plan: 00_ARCHITECTURE/CHAT_V2_ROUND_6_PLAN_v1_0.md §5 R6-SMOKE
predecessor_brief: 00_ARCHITECTURE/chat_v2_briefs/round6/R6-SMOKE-and-R6-CI.md
defect_discovered_in: R6.1 post-merge verification (PR #74, commit 3d9a408)
branch: fix/chat-v2-r6/smoke-auth-wall-patch
base: main (POST R6.1 merge at 3d9a408)
pr_title: "fix(chat-v2/r6-smoke): auth-wall guard for round6 walkthrough spec"
estimated_loc: ~50
estimated_files: 3
may_touch:
  - platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts (add SMOKE_SESSION_COOKIE skip-guard + cookie injection)
  - .github/workflows/chat-v2-smoke.yml (mark step continue-on-error or update reporter expectation; document secret provisioning as R7 follow-up)
  - platform/tests/e2e/chat-v2/README.md (NEW — operator runbook for minting cookie locally)
must_not_touch:
  - platform/tests/e2e/chat-v2/fixtures/round6-mock-route.ts (works as-is; only the spec needs the auth guard)
  - platform/src/** (no source change — this is a test gate fix only)
  - platform/playwright.config.ts (no project-level config change needed)
  - any feature flag file
  - any of the in-flight R6.x brief files
depends_on: R6.1 must be on main (confirmed at 3d9a408)
blocks: R6.4, R6.5, R6.6, R6.2, R6.3 — none should fire until this patch lands and the smoke gate can actually verify them
---

# §1 Mission

The R6-SMOKE walkthrough spec landed at PR #73 / 78e44ef with the contract "asserts every F.3 finding against a mocked consume route, no live LLM credentials required, runs in CI." The contract held for the consume API. It did NOT hold for the page-load itself: `/clients/[id]/consume/page.tsx:16-17` calls `getServerUser()` and `redirect('/login')` if absent. The mock-route fixture intercepts `POST /api/chat/consume` but not the page's server-side auth check. Result: every spec run navigates to `/clients/test-client/consume`, hits the auth wall, gets redirected to `/login`, and times out on `waitForSelector('[data-testid="v2-chat-shell"]')` — which is correct (V2 never mounts because the page never renders).

Post-R6.1 (3d9a408), the smoke baseline confirms this: 9/9 RED with timeout failure mode unchanged. The auth wall is the active blocker, not any of the F.3 bugs. None of the R6.4–R6.6 fixes can be smoke-verified until this is resolved.

R6-SMOKE-PATCH adds the standard `SMOKE_SESSION_COOKIE` + `context.addCookies()` pattern (matching `tests/e2e/gate_ii_trace_smoke.spec.ts:19-30`) plus a SMOKE_CHART_ID env var (matching `tests/e2e/portal/build-mode.spec.ts:11-15`), plus an operator runbook for minting the cookie locally via existing `mint_session_cookie.ts`.

The patch is intentionally **operator-runnable today, CI-runnable later** — local smoke gating starts working immediately; CI workflow stays informational (no required-check enablement) until a follow-up brief provisions GitHub secrets in R7.

# §2 Scope

| File | Action | LoC | Notes |
|---|---|---|---|
| `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts` | Add SMOKE_SESSION_COOKIE + SMOKE_CHART_ID env-var guards; inject `__session` cookie in beforeEach | ~+30 | Pattern matches gate_ii_trace_smoke verbatim |
| `.github/workflows/chat-v2-smoke.yml` | No functional change required (test.skip suppresses on no-secret runs; workflow stays green vacuously). Add a comment block explaining the current "informational" status. Optionally swap `--reporter=github` for `--reporter=github --reporter=list` so skipped output is visible in CI logs. | ~+5 | Cosmetic |
| `platform/tests/e2e/chat-v2/README.md` | NEW operator runbook: how to mint a session cookie via `platform/scripts/mint_session_cookie.ts`, set env vars, run the spec locally | ~+50 | Net-new documentation |

# §3 Implementation specification

## §3.1 — `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts`

**Current** (verified at HEAD 3d9a408):

```ts
import { test, expect } from '@playwright/test';
import { applyRound6MockRoute } from './fixtures/round6-mock-route';

test.describe('Round 6 walkthrough — smoke assertions against F.3 findings', () => {
  test.beforeEach(async ({ page }) => {
    await applyRound6MockRoute(page);
    const clientId = process.env.PLAYWRIGHT_CHAT_CLIENT_ID ?? 'test-client';
    await page.goto(`/clients/${clientId}/consume?provider=mock`);
    await page.waitForSelector('[data-testid="v2-chat-shell"]', { timeout: 10_000 });
  });
  // ... 9 test() blocks
});
```

**Target:**

```ts
import { test, expect } from '@playwright/test';
import { applyRound6MockRoute } from './fixtures/round6-mock-route';

/**
 * Round 6 walkthrough smoke spec.
 *
 * Asserts every F.3 finding against a mocked consume route (no live LLM).
 * The spec navigates to `/clients/[id]/consume` which is auth-gated server-
 * side, so we inject a `__session` cookie that matches `getServerUser()`'s
 * reader in `platform/src/lib/firebase/server.ts`. Without the cookie the
 * spec is skipped — both locally and in CI — until secrets are provisioned.
 *
 * Run locally:
 *   1. Mint a session cookie:
 *      cd platform && npx tsx scripts/mint_session_cookie.ts \
 *        --uid <your-uid> --email <your-email>
 *      (See `platform/tests/e2e/chat-v2/README.md` for full runbook.)
 *   2. export SMOKE_SESSION_COOKIE='<cookie value from step 1>'
 *   3. export SMOKE_CHART_ID='<chart id you have access to>'
 *   4. cd platform && npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium
 *
 * Run in CI: requires SMOKE_SESSION_COOKIE + SMOKE_CHART_ID secrets in the
 * chat-v2-smoke workflow. Until those secrets land (R7 follow-up), this
 * spec skips in CI. The workflow remains as a path-trigger sentinel.
 */

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:3000';
const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE;
const CHART_ID = process.env.SMOKE_CHART_ID;
const SKIP = !SESSION_COOKIE || !CHART_ID;

test.describe('Round 6 walkthrough — smoke assertions against F.3 findings', () => {
  test.skip(SKIP, 'SMOKE_SESSION_COOKIE or SMOKE_CHART_ID not set; skipping authenticated smoke tests. See spec header for setup instructions.');

  test.beforeEach(async ({ context, page }) => {
    // Inject the Firebase session cookie that `getServerUser()` reads.
    // Cookie name MUST be `__session` to match
    // `platform/src/lib/firebase/server.ts:48`.
    await context.addCookies([
      {
        name: '__session',
        value: SESSION_COOKIE!,
        domain: new URL(BASE_URL).hostname,
        path: '/',
      },
    ]);

    // Intercept the consume API before navigation so the mock answers any
    // streaming request V2 fires after mount.
    await applyRound6MockRoute(page);

    // Navigate to the consume page. After auth passes the V2 component
    // mounts; we wait for its outermost testid before asserting.
    await page.goto(`/clients/${CHART_ID}/consume?provider=mock`);
    await page.waitForSelector('[data-testid="v2-chat-shell"]', { timeout: 10_000 });
  });

  // ... 9 test() blocks UNCHANGED
});
```

Notes:

- The `test.skip()` runs at describe level → applies to all 9 tests uniformly. Skipped tests show in the reporter so the operator can see the spec is dormant, not silently passing.
- `BASE_URL` env var lets the spec target a non-localhost server (staging smoke runs). Default stays `http://localhost:3000`.
- Drop `PLAYWRIGHT_CHAT_CLIENT_ID` in favor of `SMOKE_CHART_ID` for naming consistency with portal specs. (`PLAYWRIGHT_CHAT_CLIENT_ID` was a working name; `SMOKE_CHART_ID` aligns with the codebase pattern.)
- The 9 test blocks themselves are unchanged. Their assertions are correct; they just never reached past beforeEach.

## §3.2 — `.github/workflows/chat-v2-smoke.yml`

**Current** at HEAD 3d9a408 — last touched in PR #73:

```yaml
# (existing workflow per R6-SMOKE-and-R6-CI brief §3.3)
```

**Target — minimal change:** add a comment block at the top documenting the current "informational" status + the R7 secret-provisioning follow-up. No functional changes to the steps. The workflow already exits 0 when all tests skip (which is what happens without secrets), so the gate-state today is "fires + skips + passes vacuously."

Append at the top of the file, above the `name:` line:

```yaml
# chat-v2 smoke gate
#
# Today (post R6-SMOKE-PATCH): runs the round6-walkthrough spec under chromium.
# Without SMOKE_SESSION_COOKIE + SMOKE_CHART_ID secrets provisioned in this
# workflow's environment, all 9 tests skip — workflow exits 0 vacuously.
# Local operator runs (with cookies minted) exercise the gate normally.
#
# R7 follow-up: provision SMOKE_SESSION_COOKIE + SMOKE_CHART_ID as GitHub
# Actions secrets, inject via `env:` block on the playwright step, then
# enable `chat-v2 smoke / smoke` as a required check on main branch
# protection. Tracking: 00_ARCHITECTURE/CHAT_V2_ROUND_6_PLAN_v1_0.md §8.3.
```

If the executor wants to surface skip-state in CI logs (recommended), change the playwright invocation from:

```yaml
      - run: npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=github
```

to:

```yaml
      - run: npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=list
        env:
          SMOKE_SESSION_COOKIE: ${{ secrets.SMOKE_SESSION_COOKIE }}
          SMOKE_CHART_ID: ${{ secrets.SMOKE_CHART_ID }}
```

This is forward-compatible: when secrets land in R7 the spec runs; until then the env vars are empty strings → spec skips → workflow exits 0. The `--reporter=list` provides clearer skip messaging than `github` reporter.

DO NOT enable the required-check branch protection rule. That stays operator-manual after R7 secrets land.

## §3.3 — `platform/tests/e2e/chat-v2/README.md` (NEW)

Operator runbook. Content outline:

```markdown
# Chat V2 Round 6 — Smoke Spec Runbook

The `round6-walkthrough.spec.ts` is the automated gate for the Chat V2 Round 6 fix-wave. It asserts every finding from `00_ARCHITECTURE/CHAT_V2_F3_FORENSIC_v1_0.md §7` against a mocked `/api/chat/consume` route, without requiring live LLM credentials.

The page under test (`/clients/[id]/consume`) is auth-gated server-side, so the spec needs a valid Firebase `__session` cookie injected before navigation.

## One-time setup

1. Confirm you have an Auth-active super_admin (or member) account on local dev.
2. Have a chart ID handy that the account can access (use any chart from the dashboard).

## Run locally — three steps

### Step 1: mint a session cookie

The Madhav repo includes a helper script. From the repo root:

```bash
cd platform
npx tsx scripts/mint_session_cookie.ts --uid <your-firebase-uid> --email <your-email>
```

The script does a 2-step Firebase exchange (custom-token → id-token → session-cookie) and prints the `__session` cookie value. See `feedback_mint_session_cookie` memory note for the exact behavior shipped 2026-05-13.

Output looks like:

```
__session=eyJhbGc...<long blob>...XYZ123
```

Copy only the value after `__session=` (not the prefix).

### Step 2: export env vars

```bash
export SMOKE_SESSION_COOKIE='<paste cookie value here, no quotes inside>'
export SMOKE_CHART_ID='<a chart id your user can access>'
```

### Step 3: run the spec

```bash
cd platform
npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=list
```

Expected output after R6.1 has merged (3d9a408 or later):
- 2 passed (B1 stage stepper visible during streaming; O1 synthesis stage done state)
- 7 failed (L1, L2, L3, B2/B3, B4/B5, B6 — each with actual bug evidence; N1 passes if reports library copy is reachable, otherwise also fails)

As R6.4 → R6.6 → R6.2 → R6.3 land in sequence, additional tests flip green.

## CI status

The `chat-v2 smoke / smoke` workflow at `.github/workflows/chat-v2-smoke.yml` runs on PRs touching chat-v2 paths. Until `SMOKE_SESSION_COOKIE` and `SMOKE_CHART_ID` are provisioned as GitHub Actions secrets, the spec skips in CI and the workflow exits 0 vacuously. Local operator runs are the binding gate today.

R7 follow-up: provision secrets and flip the workflow to required-check.

## Troubleshooting

- **Test skip messages everywhere**: confirm `echo $SMOKE_SESSION_COOKIE` and `echo $SMOKE_CHART_ID` both return non-empty strings before running playwright.
- **All tests fail with `redirect to /login`**: the cookie is stale or invalid. Re-mint via Step 1. Cookies last ~14 days by default.
- **Test passes B1+O1 but B2/B3 says `SIG.MSR.NNN` still in body**: that bug fix is R6.2; expected.
- **Test fails on `v2-chat-shell` timeout post-R6.1**: confirm `git log --oneline -3 main` shows the R6.1 commit. If not, you're running on an older base.
```

This README is referenced from the spec header comment so future executors find it.

# §4 Acceptance criteria

- [ ] `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts` has the SMOKE_SESSION_COOKIE + SMOKE_CHART_ID guards + `__session` cookie injection.
- [ ] Spec header comment references the README runbook.
- [ ] `platform/tests/e2e/chat-v2/README.md` exists with the four-section runbook.
- [ ] `.github/workflows/chat-v2-smoke.yml` has the top comment block + `env:` injection for the secrets (still empty in CI; future-proofed).
- [ ] `cd platform && npx tsc --noEmit` exits 0.
- [ ] **Local smoke RUN-WITHOUT-COOKIE**: `cd platform && npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=list` reports 9 skipped, 0 passed, 0 failed, exit 0.
- [ ] **Local smoke RUN-WITH-COOKIE** (operator-driven): with SMOKE_SESSION_COOKIE + SMOKE_CHART_ID exported, same command reports 2 passed (B1, O1) + 7 failed (with actual bug evidence) + 0 skipped. Document the test names that pass and fail.
- [ ] No `platform/src/**` files touched.
- [ ] No fixture file changes (round6-mock-route.ts stays as-is).

# §5 Verification commands

```bash
# 1. Without cookie — spec should skip cleanly
cd platform
unset SMOKE_SESSION_COOKIE SMOKE_CHART_ID
npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=list 2>&1 | tail -20
# Expected: 9 skipped, exit 0

# 2. With cookie — operator runs after minting
#    (Skipped in executor session unless operator provides values inline)
#    export SMOKE_SESSION_COOKIE='...'
#    export SMOKE_CHART_ID='...'
#    npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=list

# 3. Compile + lint
npx tsc --noEmit
npx eslint tests/e2e/chat-v2/round6-walkthrough.spec.ts

# 4. README renders cleanly (markdown lint, if available)
test -f tests/e2e/chat-v2/README.md && echo "README present"

cd ..

# 5. Workflow YAML still parses
npx --yes js-yaml .github/workflows/chat-v2-smoke.yml > /dev/null && echo "YAML clean"
```

# §6 Hard constraints

- DO NOT modify `platform/tests/e2e/chat-v2/fixtures/round6-mock-route.ts`. The fixture intercepts the consume API correctly; only the page-load auth wall needs bridging.
- DO NOT modify any of the 9 `test()` blocks. The assertions are correct; they just need to reach past beforeEach to execute.
- DO NOT enable the required-check branch protection rule.
- DO NOT provision GitHub Actions secrets in this PR. That's R7 follow-up work.
- DO NOT touch `platform/src/**`. This is a test-gate fix only.
- DO NOT touch any of the R6.x in-flight brief files (R6.4 brief stays untouched).
- DO NOT regress the existing portal-spec auth pattern (which uses cookie name `session` in some places, `__session` in others — leave that codebase inconsistency alone; this brief uses `__session` because that's what `getServerUser()` reads).

# §7 Risks + mitigations

| Risk | Mitigation |
|---|---|
| `mint_session_cookie.ts` may have changed since the 2026-05-13 memory note describes it | Brief references the memory note but operator-runnable verification confirms behavior before this brief's runbook is trusted. If script behavior diverges from runbook, file a one-line README amendment in the same PR. |
| Existing `gate_ii_trace_smoke.spec.ts` uses `domain: 'localhost'` hardcoded; the brief uses `new URL(BASE_URL).hostname` (more portable) | Portable form is correct and matches `portal/build-mode.spec.ts:18`. Hardcoded localhost is a wart, not a pattern to replicate. |
| Skipping in CI means R6.4/R6.5/R6.6 PRs land without smoke verification | Operator runs the spec locally before approving each PR per Round 5 visual-review process discipline retained in Round 6 plan §4.4. Operator-driven smoke is the binding gate today. CI catches up in R7. |
| Provisioning secrets in R7 may face token-rotation lifecycle complications | Out of scope for this brief. R7 follow-up brief addresses cookie rotation strategy. |
| The spec's `--reporter=list` change makes CI logs slightly more verbose | Acceptable trade-off for clearer skip-state messaging. |

# §8 PR description template

```
## What this PR fixes

The R6-SMOKE round6-walkthrough spec couldn't run E2E against current main: `/clients/[id]/consume/page.tsx` is server-side auth-gated via `getServerUser()`, but the mock-route fixture only intercepts the consume API (after navigation). Result: every spec run got redirected to `/login` and timed out on `v2-chat-shell`. Diagnosed in PR #74 (R6.1) post-merge verification.

This patch adds the standard `SMOKE_SESSION_COOKIE` + `SMOKE_CHART_ID` env-var guard pattern (matching `gate_ii_trace_smoke.spec.ts` and `portal/build-mode.spec.ts`), injects a `__session` cookie matching `getServerUser()`'s reader (`platform/src/lib/firebase/server.ts:48`), and documents the operator runbook in a new `tests/e2e/chat-v2/README.md`.

## What this PR does NOT do

- DOES NOT provision GitHub Actions secrets. That's a separate R7 follow-up — until those land, the workflow skips vacuously in CI but operator-driven local runs work fully.
- DOES NOT touch source under `platform/src/**`.
- DOES NOT change any of the 9 test assertions.

## Files touched

- MOD `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts` (auth guard + cookie injection)
- MOD `.github/workflows/chat-v2-smoke.yml` (informational comment block + secret env injection scaffold)
- NEW `platform/tests/e2e/chat-v2/README.md` (operator runbook)

## Local verification

Without cookie:
```
9 skipped, 0 passed, 0 failed, exit 0
```

With cookie (operator-side):
```
2 passed (B1, O1) — R6.1 already merged at 3d9a408
7 failed (L1, L2, L3, B2/B3, B4/B5, B6, N1 — each with actual bug evidence)
0 skipped, exit 1 (failures expected; this is the gate doing its job)
```

## Refs

- `00_ARCHITECTURE/chat_v2_briefs/round6/R6-SMOKE-PATCH.md` (this PR's EXEC brief)
- `00_ARCHITECTURE/CHAT_V2_ROUND_6_PLAN_v1_0.md` §5 R6-SMOKE
- PR #74 (R6.1) — where the auth wall was first observed
```

# §9 Post-merge

After this lands on main, R6.4 fires per its existing brief. The operator runs the smoke locally with cookies before approving each R6.x PR.

R7 follow-up brief (separate, post-Round-6-close): provision GitHub Actions secrets + flip workflow to required-check.

# §10 Changelog

- **v1.0 (2026-05-18, READY_FOR_EXECUTION)** — Initial authoring. Auth-wall fix scoped to test gate. Three files: spec edit, workflow comment block + env injection, new README runbook. No source code changes.
