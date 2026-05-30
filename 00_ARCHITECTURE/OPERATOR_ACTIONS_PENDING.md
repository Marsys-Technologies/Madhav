## Smoke Gate Secrets — Pending Operator Action (added 2026-05-31)

The chat-v2-smoke workflow (.github/workflows/chat-v2-smoke.yml) exits 0 vacuously
because two required secrets are not provisioned. Until they are, the smoke gate
provides no protection.

**Required actions (human, GCP/GitHub console):**

1. Mint a long-lived session cookie for the smoke test user:
   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
   npx tsx scripts/mint_session_cookie.ts --uid <SMOKE_USER_UID> --chart-id 362f9f17-95a5-490b-a5a7-027d3e0efda0
   ```
   Copy the output `__session` cookie value.

2. In GitHub → repo Settings → Secrets → Actions, add:
   - `SMOKE_SESSION_COOKIE` = the __session cookie value from step 1
   - `SMOKE_CHART_ID` = 362f9f17-95a5-490b-a5a7-027d3e0efda0

3. In GitHub → repo Settings → Branches → main branch protection rule, add
   `chat-v2 smoke / smoke` as a required status check.

4. Rotate the session cookie every 90 days (it expires with Firebase session lifetime).
