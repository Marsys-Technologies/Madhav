# Orchestrator Blocker — 2026-06-01T07:16:00Z

**Blocker:** `platform/scripts/mint_session_cookie.ts` does not exist.  The
Drashta walk (§3) requires a minted `__session` cookie tied to the native's
Firebase UID (`mail.abhisek.mohanty@gmail.com`) so that the portal
authenticates the walk and the `/api/clients/create` dedupe path can return
the existing `362f9f17-95a5-490b-a5a7-027d3e0efda0` chart_id rather than
creating a duplicate.  Without the cookie, every navigation to a protected
route (including `/clients/new`) redirects to `/login`, blocking CP-1 through
CP-13 of the Drashta script.  Per REMEDIATION_PROTOCOL.md §safety, Pariksha
agents do not improvise alternative auth paths.

**To unblock:**
1. Author `platform/scripts/mint_session_cookie.ts` — it must accept
   `--uid`, `--email`, and `--chart-id` flags and emit a `__session` cookie
   string to stdout.  Consult the Firebase Admin SDK (`firebase-admin`)
   pattern used elsewhere in the platform (e.g., `platform/scripts/`).
2. Ensure the script is executable via `npx tsx scripts/mint_session_cookie.ts`.
3. Remove this file OR set `status: resolved` in the blocker YAML below, then
   re-invoke the Pariksha Orchestrator.  The resume_state.yaml checkpoint
   (`next_expected_action: drashta_cp1_form_loaded`) will cause Drashta to
   start at CP-1 without restarting the arc.

**Arc state preserved at:** `resume_state.yaml` — checkpoint `arc_initialized`,
`next_expected_action: drashta_cp1_form_loaded`.  No charts row was created,
no build was triggered, no DB was modified.

**Pramana status:** DB proxy (`start_db_proxy.sh`) exists.  If an existing
completed build for chart `362f9f17...` is present in the DB, the operator
may trigger Pramana independently (without Drashta) by running the Pramana
battery directly after starting the proxy.  The native oracle is fully seeded
at `native_oracles/362f9f17-95a5-490b-a5a7-027d3e0efda0.yaml` (82 assertions,
Lahiri only).
