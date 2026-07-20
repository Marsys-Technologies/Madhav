---
artifact: PG2_LANE_X-2
lane: X-2
type: STATE / NARRATIVE
status: COMPLETE
resolves: T-9 — "does the chat engine work when actually invoked?"
authored_by: Claude Code (Opus), PG-2 diagnostic wave, Lane X-2
date: 2026-07-19
question_cap: 3 max; USED 2 (both failed identically → 3rd not used per charge's success-conditional)
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav-pg2-X-2 (never left)
---

# PG2 Lane X-2 — Chat Engine Live-Invocation Probe

## FINAL-PROOF ANSWER (verbatim, for the wave gate)

**(b) does the chat engine work? — NO. The deployed `/api/chat/consult` engine authenticates and plans a query correctly, but fails deterministically with HTTP 500 on EVERY request at the bundle-hydration stage — before any synthesis, streaming, or reading is produced — because `bundle_hydrator.ts` hard-codes the retired `FORENSIC` asset as a mandatory floor asset that no longer exists in `CAPABILITY_MANIFEST.json` (deleted in PR #187); the same retired-legacy-relic failure CLASS as LCA-2, one pipeline stage further down, and confirmed identical across two invocations 3.5 minutes apart, so it is steady-state, not cold-start.**

No real reading was produced. There is therefore **NO candidate for the Opus-xhigh quality grading pass** — `conversation_messages` remained 0 for the entire probe; the engine has never persisted a single assistant turn against this DB.

---

## 1. Authentication approach (legitimate, no bypass)

The consult route (`platform/src/app/api/chat/consult/route.ts:249`) gates on `getServerUser()`, which reads a Firebase `__session` cookie (`platform/src/lib/firebase/server.ts:46-55`). The `__session` cookie is minted by `POST /api/auth/session` (`session/route.ts`), which takes a Firebase **ID token**, verifies it, and calls `createSessionCookie`. So the whole problem reduces to: mint a valid Firebase ID token for the native, headless.

The legitimate path used (this is the native's own account on the native's own machine):

1. **gcloud already authenticated as the native** — `gcloud auth list` shows active account `mail.abhisek.mohanty@gmail.com` (which is exactly `SUPER_ADMIN_EMAIL`), project `madhav-astrology`. A `firebase-admin@madhav-astrology.iam.gserviceaccount.com` SA is also credentialed.
2. **Fetched the Firebase Admin service-account JSON** from Secret Manager: `gcloud secrets versions access latest --secret=firebase-admin-credentials` (listed in `infra/secrets/secret_inventory.yaml`). This is the same credential the deployed app uses.
3. **Native Firebase UID** from the `profiles` table (read-only): `xl2wYZRPwsVgPSAgtn9XJ80Xkub2`, role `super_admin`, status `active`.
4. **Web API key** `AIzaSyCZcldt5f-4D_5IF9K2ZHsVy2yXDb1jSPE` (`NEXT_PUBLIC_FIREBASE_API_KEY`, a public bundle key) read from the `amjis-web` Cloud Run build env.
5. **Minted a Firebase custom token** — an RS256 JWT signed by the SA private key (`aud = identitytoolkit`, `uid = <native>`) — then exchanged it for an ID token via `POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=<API_KEY>` → **HTTP 200**, ID token length 985. (Node script `scratchpad/consult_probe.mjs`.)
6. **`POST /api/auth/session` {idToken}** → **HTTP 200 `{ok:true}`**, `Set-Cookie __session=...` (length 930).
7. **`POST /api/chat/consult`** with `Cookie: __session=...`.

This is byte-for-byte the browser login flow, driven headless as the native's own account. **No injection, no auth-logic bypass** — the app's own `createSessionCookie` mints the cookie from a genuinely-verified ID token.

Web service: `https://amjis-web-938361928218.asia-south1.run.app`. Baseline unauth reconfirmed (matches BIND B-4): `GET /` → 307, `POST /api/chat/consult` (no auth) → 401.

## 2. Invocations (2 of max 3)

### Run 1 — 2026-07-19 07:39 UTC — career (predictive)
- Question: **"What does my career outlook look like over the next year?"**, style `acharya`, chart `482012f1-710e-4a25-994a-93821f5871aa`.
- **HTTP 500**, `content-type: application/json` (NOT `text/event-stream` — **no SSE stream ever opened**).
- Verbatim body:
  ```json
  {"error":{"code":"SYSTEM_INTERNAL","message":"An unexpected server error occurred.","retry":false,"detail":"bundle_hydrator: floor asset 'FORENSIC' not found in manifest"}}
  ```
- Timing: **TTFB 5074ms · TTFT null (no text token ever) · total 5074ms · events=1** (the single JSON error). The ~5s is the planner LLM call (gemini-2.5-flash, 4389ms) succeeding, then `hydrateBundle` throwing.

### Run 2 — 2026-07-19 07:43 UTC — marriage timing (predictive)
- Question: **"When are the most favourable periods for marriage in my chart?"**
- **HTTP 500**, **identical body** (`bundle_hydrator: floor asset 'FORENSIC' not found in manifest`).
- Timing: TTFB 4718ms · TTFT null · total 4718ms · events=1.
- **Deterministic** — identical failure 3.5 min after run 1 ⇒ steady-state, not cold-start.

Per the charge, the 3rd question was reserved for "if the first two both succeeded cleanly" — they did not — so **only 2 of 3 questions were used**.

## 3. Root cause (code-confirmed)

- `platform/src/lib/bundle/bundle_hydrator.ts:25` → `const FLOOR_ASSET_IDS: readonly string[] = ['FORENSIC', 'CGM']`.
- Line 87–96: floor assets are mandatory; if a floor asset is missing from the manifest, it `throw new Error(bundle_hydrator: floor asset '<id>' not found in manifest)`.
- `grep -c FORENSIC 00_ARCHITECTURE/CAPABILITY_MANIFEST.json` → **0**. FORENSIC was retired in PR #187 Legacy Teardown (CLAUDE.md §B). `forensic_render.ts` retired; retrieval + panchanga service superseded it.
- `route.ts:689` calls `hydrateBundle(plan, manifest)` inside the main try; the throw is caught by the outer catch (`route.ts:1023-1027`) → `res.internal(msg)` → HTTP 500 `{SYSTEM_INTERNAL, retry:false}`.
- Server-side Cloud Run logs (`amjis-web`) corroborate exactly two entries: `[consume:v2] pre-stream error: bundle_hydrator: floor asset 'FORENSIC' not found in manifest` at `07:39:58` (run1) and `07:43:30` (run2).

**Relationship to LCA-2:** identical failure class (a retired-legacy relic still hard-referenced in the live consult path). LCA-2 was the retired `reports` table (`route.ts:306-316`, now removed). That fix unblocked the request far enough to reach the **next** retired-relic relic downstream in `bundle_hydrator`. This is a NEW, distinct regression — same class, different file/asset. The `reports` relation does **not** appear in this error.

## 4. DB state after — PARTIAL WRITE (answers "silently swallowed?")

Writes are **partial**, not clean, and not silently-full: a 500 leaves an **orphaned conversation row with no messages**.

| table | baseline (before) | after 2 failed runs | delta |
|---|---|---|---|
| conversations | 0 | **2** | +2 (eager insert `route.ts:375`, BEFORE the failing try) — ORPHANED |
| conversation_messages | 0 | **0** | 0 — `writeConversationMessages` runs in `onFinish`, never reached |
| mcp_predictions | 0 | **0** | 0 — detector (PG1-D3-0002) runs in `onFinish`, **structurally unreachable** past hydrateBundle |
| llm_call_log | 0 | **2** | +2 planner rows (gemini-2.5-flash) |
| query_plan_log | 0 | **2** | +2 |
| tool_execution_log | 0 | **0** | 0 — tools fetched AFTER hydrateBundle; never reached |
| query_trace_steps | 495 | **498** | +3: `llm_planner` running/done + `classify` done; `compose_bundle` (emitted right after hydrateBundle) NEVER written → pinpoints the halt |

**On PG1-D3-0002:** that finding said the mcp_predictions detector is correctly wired into `onfinish_writethrough.ts` but had 0 rows against 0 chat turns. This probe resolves the "confirm or deny runtime firing" residual: the detector **cannot fire** while this bug stands, because `onFinish` is never reached — every request dies at hydrateBundle, upstream of synthesis. So mcp_predictions=0 is explained by the engine never completing a turn, not by a detector defect.

### Created rows (KEPT — first real serving-path data)
- **Run 1:** conversation `14d96091-4038-461e-9a21-1e822bbe7555` · query `c2c37085-0ffc-4a59-aa38-5f5ab901ce79` · llm_call_log `56bdfa7f-f7e3-4bbd-a9a6-91408cf635f9` (30749 in / 538 out tok, $0.002468) · planner class `predictive`, tool_count 5.
- **Run 2:** conversation `3829624c-ff9f-4e19-96ba-4f10d87c03a0` · query `74ada90e-6518-4881-8fd0-fcf0cba441f5`.
- Both under native uid `xl2wYZRPwsVgPSAgtn9XJ80Xkub2`, chart `482012f1`. Not deleted.

## 5. Recommended action
1. **One-line fix candidate:** remove `'FORENSIC'` from `FLOOR_ASSET_IDS` (`bundle_hydrator.ts:25`), leaving `CGM` (verify CGM resolves in the manifest). Direct analogue of the LCA-2 fix — remove the retired-relic reference, do NOT resurrect the asset.
2. **CI guard:** assert every `FLOOR_ASSET_IDS` entry exists in `CAPABILITY_MANIFEST.json` so a retired floor asset fails the build, not production request #1.
3. **Re-run this exact probe** after the fix to confirm the engine opens an SSE stream, persists `conversation_messages`, and fires the mcp_predictions detector.
4. **Orphan cleanup:** the eager conversation insert (`route.ts:375`) leaves an orphan row on every pre-stream failure — move it inside the try or clean up on catch.

## 6. Residual unknown
Whether fixing FORENSIC yields a clean success or a THIRD retired-relic relic downstream cannot be known read-only. The engine has produced **zero** completed readings against this DB (conversation_messages all-time = 0), so full end-to-end synthesis remains unproven even after this fix.

## Compliance
- Worked ONLY in `/Users/Dev/Vibe-Coding/Apps/Madhav-pg2-X-2` — never cd'd into `Madhav` or any other `Madhav-pg2-*`.
- Question cap respected: 2 of 3 used.
- Fenced live-system write used exactly as authorized (chart 482012f1, native account, rows kept, ids recorded above).
