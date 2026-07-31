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

The script does a 2-step Firebase exchange (custom-token → id-token → session-cookie) and prints the `__session` cookie value.

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
- 7 failed (L1, L2, L3, B2/B3, B4/B5, B6 — each with actual bug evidence)

As R6.4 → R6.6 → R6.2 → R6.3 land in sequence, additional tests flip green.

## CI status

`round6-walkthrough.spec.ts` runs in CI as part of **Stage 3 — E2E (Chromium)** of
`.github/workflows/chat-v2-ci.yml`, which executes the whole `tests/e2e/chat-v2` directory
against `--config=tests/e2e/chat-v2/playwright.config.ts`.

> **Corrected 2026-07-31 (CI efficiency audit).** This section previously pointed at a
> separate `.github/workflows/chat-v2-smoke.yml` and said the spec "skips in CI and the
> workflow exits 0 vacuously" pending `SMOKE_SESSION_COOKIE` / `SMOKE_CHART_ID`. Both of
> those statements were wrong by the time they were read: the two secrets **are** provisioned
> in this repo, so the workflow was not skipping — it was running and **failing on every
> single run** since at least 2026-07-21, across four unrelated branches. The cause was that
> it invoked the spec *without* `--config=tests/e2e/chat-v2/playwright.config.ts`, so it
> loaded the repo-default Playwright config. That workflow has been deleted; Stage 3 already
> runs the same spec with the correct config, green, and the three path globs only
> chat-v2-smoke watched were folded into `chat-v2-ci.yml`.

## Troubleshooting

- **Test skip messages everywhere**: confirm `echo $SMOKE_SESSION_COOKIE` and `echo $SMOKE_CHART_ID` both return non-empty strings before running playwright.
- **All tests fail with redirect to /login**: the cookie is stale or invalid. Re-mint via Step 1. Cookies last ~14 days by default.
- **Test passes B1+O1 but B2/B3 says `SIG.MSR.NNN` still in body**: that bug fix is R6.2; expected.
- **Test fails on `v2-chat-shell` timeout post-R6.1**: confirm `git log --oneline -3 main` shows the R6.1 commit. If not, you're running on an older base.
