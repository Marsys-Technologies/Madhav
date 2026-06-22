---
artifact: CLAUDE_CODE_PROMPT_L4_DEPLOY_VERIFY.md
canonical_id: CLAUDE_CODE_PROMPT_L4_DEPLOY_VERIFY
version: 1.0
status: READY — paste-prompt for Claude Code in Antigravity. Trigger deploy, verify prod, diagnose the two 0-row assets. NO SEAL.
authored_by: Cowork 2026-06-22
context: P1–P5 + P7 done; prod DB has migs 330–341 + 9 lit ph_* assets; web container NOT redeployed (PROD_DATABASE_URL secret was missing). Native is setting the secret via gh/gcloud CLI IN PARALLEL with this prompt.
---

# Claude Code Prompt — L4 Deploy + Verify + 0-Row Diagnosis (NO SEAL)

> Paste §PROMPT to Claude Code in Antigravity. The native is setting the `PROD_DATABASE_URL` GitHub Actions
> secret via CLI in parallel — coordinate, don't duplicate that step. This prompt triggers/confirms the
> deploy, verifies the prod cockpit, and diagnoses the two 0-row assets. **DO NOT SEAL.**

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo Madhav). Context: the L4 merge is on `main`; the
prod DB already has migrations 330–341 and all 9 ph_* assets built + lit (verified via Cloud SQL proxy).
The blocker is that the `Deploy to Cloud Run` workflow fails at its migrate step because the
`PROD_DATABASE_URL` GitHub Actions secret was missing, so the WEB CONTAINER never redeployed with the
`ASSET_NAMES` cockpit fix. **The native is setting that secret via `gh`/`gcloud` CLI in parallel with you.**

Your job: trigger + confirm the deploy once the secret exists, verify the prod cockpit shows 9 lit, and
diagnose the two 0-row assets. **DO NOT perform the L4 seal** (no DRAFT→CURRENT, no L4_PHALA_CLOSE, no
CURRENT_STATE flip). Report back for the native's further changes.

**Rails:** N4 boundary; canonical chart `482012f1-710e-4a25-994a-93821f5871aa` never auto-mutated (B.10);
anti-drift; Gemini/DeepSeek only (Anthropic banned); data plane = prod via the Cloud SQL proxy. Verify
against the LIVE deployed revision, never the branch.

---

### STEP 0 — Coordinate on the secret (do NOT set it yourself unless asked)
The native is adding `PROD_DATABASE_URL` via CLI. Confirm it's present before triggering deploy:
```
gh secret list --repo amonty84/Madhav | grep PROD_DATABASE_URL    # should appear once the native sets it
```
If it's not there yet, WAIT / poll — do not proceed to Step 1. (If the native asks you to set it, use
`gh secret set PROD_DATABASE_URL` and paste the value they provide — never invent or log the value.)
**Sanity gate:** the secret's host/db MUST match the DB the proxy applied 330–341 to. If you can confirm
the proxy target (`echo $DATABASE_URL` host in the proxy env), eyeball that the secret points at the same
prod instance — a mismatch would migrate the WRONG database. Flag to native if you can't confirm.

### STEP 1 — Trigger the deploy
Once the secret is present, trigger the workflow (it also auto-triggers on the next push to main, but
dispatch is cleaner here):
```
gh workflow run "Deploy to Cloud Run" --repo amonty84/Madhav --ref main
gh run watch --repo amonty84/Madhav $(gh run list --repo amonty84/Madhav --workflow="Deploy to Cloud Run" --limit 1 --json databaseId -q '.[0].databaseId')
```
Watch the "Run database migrations" step PASS (it's idempotent — schema already applied via proxy, so it's
a no-op re-run) and the build + Cloud Run deploy succeed. If CI is red on the 31 KNOWN pre-existing
failures only, that's the baseline — confirm none are net-new; net-new blocks.

### STEP 2 — Confirm the prod revision == the deployed SHA
```
gcloud run services describe amjis-web --region=asia-south1 \
  --format='value(status.traffic[0].revisionName, status.latestReadyRevisionName)'
gcloud run services describe amjis-web --region=asia-south1 \
  --format='value(spec.template.metadata.annotations)' | tr ',' '\n' | grep -i sha   # confirm it matches main HEAD
```
Wait 30–60s for rollout + CDN. Check Cloud Run logs for zero startup errors:
`gcloud run services logs read amjis-web --region=asia-south1 --limit=50 | grep -iE "error|exception|fatal"` → empty.

### STEP 3 — Verify the PROD cockpit shows 9 lit (the live-deployment gate)
Prod is auth-walled (401 unauthenticated — that's correct, not down). Query with a valid session cookie
(`scripts/mint_session_cookie.ts` emits `__session`), or run the assertions server-side:
```
# registry must show 9 phala assets
curl -s -H "Cookie: __session=<minted>" https://madhav.marsys.in/api/cockpit/registry \
  | jq '[.data.assets[]|select(.layer=="phala")]|length'        # → 9
# stats must show all 9 lit
curl -s -H "Cookie: __session=<minted>" "https://madhav.marsys.in/api/cockpit/stats?chartId=482012f1-710e-4a25-994a-93821f5871aa" \
  | jq '[.data.assets[]|select(.asset_id|startswith("ph_"))|{id:.asset_id,rows:.actual_rows,state:.state}]'
```
Expected per the build report: nimitta 350, muhurta 100, sodhana 400, pramana 350, suddha_sodhana 350,
rectification 186, phaladesa 7, **pratikara 0, sankrama 0** (see Step 4). All `state:"lit"`.
Also confirm in the UI: Nirmāṇa panel Phala = "9 assets", progress bar reflects 7-of-9 populated, the DAG
shows 9 phala beads on the L4 ring wired to kala; `phala_rectification` candidates = **Aries**;
`phala_rectification_best.auto_action='stage_for_review'` (canonical chart UNCHANGED).

### STEP 4 — Diagnose the TWO 0-row assets SEPARATELY (they have DIFFERENT causes)
The build report lumped these together as "both depend on ka_vighnakara" — that is WRONG. Diagnose each:

**(a) ph_pratikara → phala_mitigation = 0 rows.** It reads `kala_vighnakara`/obstruction data (writer
`ph_pratikara.py` line 7, 136–161 — loads `ka_vighnakara` gracefully, returns [] if empty). `ka_vighnakara`
is REGISTERED (writer + migration 245) and its target is `kala_obstruction`. So the table EXISTS; the
cause is that **`kala_obstruction` is EMPTY for the native** (the L3 ka_vighnakara build never populated
482012f1). Confirm: `SELECT count(*) FROM kala_obstruction WHERE chart_id='482012f1-...'`. If 0 → the fix
is to RUN the L3 ka_vighnakara build for the native (a Kāla-layer build), after which ph_pratikara
repopulates. This is an L3 data gap, NOT an L4 bug. **Report it; do not hack ph_pratikara.**

**(b) ph_sankrama → phala_sankrama = 0 rows.** It reads **`phala_anchors` + `bodha_cdlm_cells`** (writer
`ph_sankrama.py` line 7) — NOT ka_vighnakara. `phala_anchors` has 350 rows and CDLM cells exist, so
**ph_sankrama returning 0 is SUSPICIOUS and likely a real bug** (a filter that's too strict, a join that
misses, a cascade-depth/linkage threshold that excludes everything, or a wrong column name). INVESTIGATE:
read `ph_sankrama.py` + `services/ph_sankrama/engine.py`, run the writer's query manually against the
native's `phala_anchors`/`bodha_cdlm_cells`, find why zero rows emit, and FIX it if it's a genuine defect.
If 0 is actually correct (e.g. no qualifying multi-hop spillover for this chart), document WHY with the
query evidence. Either way, resolve the ambiguity — don't leave it "0, probably fine".

### STEP 5 — Report back (NO SEAL)
Do NOT promote DRAFT→CURRENT, author L4_PHALA_CLOSE, set target_floors, or flip CURRENT_STATE. Report:
- The deploy run URL + result; the prod revision name + whether it matches main HEAD.
- The Step 3 prod assertion outputs (registry=9; per-asset rows + state).
- Step 4 findings: (a) ph_pratikara — confirmed L3 `kala_obstruction` empty? is the fix "run ka_vighnakara
  for the native"? (b) ph_sankrama — real bug (fixed, with diff) or genuinely-0 (with query evidence)?
- Any net-new CI failures; anything else needing the native.

**Report format:** status table (Step | done? | evidence) + an "open / needs-native" list. Then STOP.

---
*End. Confirm secret → deploy → verify prod revision + 9 lit → diagnose pratikara (L3 data gap) and
sankrama (likely real bug) SEPARATELY → report. NO SEAL.*
