// Mint an authenticated __session cookie for a super-admin UID.
//
// Two-step flow:
//   1. Mint a Firebase custom token for SUPER_ADMIN_UID, exchange it for an
//      ID token via Firebase's signInWithCustomToken REST endpoint.
//   2. POST the ID token to ${SERVICE_URL}/api/auth/session; extract the
//      __session cookie value from the Set-Cookie response header.
//
// Required env vars:
//   FIREBASE_ADMIN_CREDENTIALS      JSON-stringified service-account credentials
//   NEXT_PUBLIC_FIREBASE_API_KEY    Firebase web API key
//   SUPER_ADMIN_UID                 UID of the super-admin to impersonate
//
// Optional env vars:
//   SERVICE_URL                     Target service base URL. Default: http://localhost:3000.
//                                   For prod: https://amjis-web-qm256lasva-el.a.run.app
//                                   (or fetch via `gcloud run services describe`).
//   COOKIE_OUTPUT_FILE              If set, the cookie value is written DIRECTLY to this
//                                   file (fs.writeFileSync, no trailing newline) instead of
//                                   stdout. This is the recommended invocation when running
//                                   under a wrapper like `dotenvx run` — PŪRṆATĀ 2026-08-01
//                                   found that `dotenvx run`'s own startup banner ("⟐ injected
//                                   env (N) from ...") shares stdout with any wrapped command,
//                                   so a shell redirect of the combined invocation
//                                   (`dotenvx run -- npx tsx this-script.ts > file`) captures
//                                   the banner as line 1 and the real cookie as line 2 — a
//                                   correctly-formed artifact that LOOKS corrupted if only its
//                                   first bytes are inspected. Writing straight to a file from
//                                   inside this process bypasses that entirely: no wrapper's
//                                   own stdout can ever reach this file, regardless of which
//                                   env-loader or log level it uses. Prefer this over the
//                                   wrapper's own `-q`/`--quiet` flag — silencing a symptom at
//                                   the wrapper regresses silently if its logging defaults ever
//                                   change; writing to a dedicated file does not depend on that.
//
// Usage:
//   SERVICE_URL=https://... SUPER_ADMIN_UID=<uid> npx tsx platform/scripts/dev/mint_session_cookie.ts
//   COOKIE_OUTPUT_FILE=/tmp/cookie.txt SERVICE_URL=... SUPER_ADMIN_UID=<uid> npx tsx platform/scripts/dev/mint_session_cookie.ts
//
// Without COOKIE_OUTPUT_FILE: prints the __session cookie VALUE (not the full Set-Cookie
// line) to stdout. Pipe directly into curl: COOKIE=$(... ); curl -H "Cookie: __session=$COOKIE" ...
// Exit 0 on success, non-zero on any failure (with error written to stderr).

import { writeFileSync } from 'node:fs'
import { initializeApp, getApps, cert } from 'firebase-admin/app'
import { getAuth } from 'firebase-admin/auth'
import { isDirectEntrypoint } from '../lib/entrypoint'

async function main() {
  const credsRaw = process.env.FIREBASE_ADMIN_CREDENTIALS
  if (!credsRaw) throw new Error('FIREBASE_ADMIN_CREDENTIALS not set')
  const CREDS = JSON.parse(credsRaw)
  const app = getApps().length > 0 ? getApps()[0] : initializeApp({ credential: cert(CREDS) })
  const auth = getAuth(app)

  const UID = process.env.SUPER_ADMIN_UID
  if (!UID) throw new Error('SUPER_ADMIN_UID not set')

  const FIREBASE_API_KEY = process.env.NEXT_PUBLIC_FIREBASE_API_KEY
  if (!FIREBASE_API_KEY) throw new Error('NEXT_PUBLIC_FIREBASE_API_KEY not set')

  const SERVICE_URL = (process.env.SERVICE_URL ?? 'http://localhost:3000').replace(/\/$/, '')

  // Step 1: Firebase custom token → ID token
  const customToken = await auth.createCustomToken(UID)
  const fbResp = await fetch(
    `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${FIREBASE_API_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: customToken, returnSecureToken: true }),
    },
  )
  const fbData = (await fbResp.json()) as { idToken?: string; error?: unknown }
  if (fbData.error || !fbData.idToken) {
    console.error('Firebase signInWithCustomToken failed:', JSON.stringify(fbData.error ?? fbData))
    process.exit(1)
  }

  // Step 2: ID token → __session cookie via /api/auth/session
  const sessResp = await fetch(`${SERVICE_URL}/api/auth/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idToken: fbData.idToken }),
  })

  if (!sessResp.ok) {
    const body = await sessResp.text().catch(() => '<unreadable>')
    console.error(`/api/auth/session returned ${sessResp.status}: ${body}`)
    process.exit(1)
  }

  // Set-Cookie header may be a string or array depending on runtime; normalize.
  const rawSetCookie =
    (sessResp.headers as any).getSetCookie?.() ??
    sessResp.headers.get('set-cookie') ??
    ''
  const setCookieStr = Array.isArray(rawSetCookie) ? rawSetCookie.join('\n') : String(rawSetCookie)

  const match = setCookieStr.match(/__session=([^;]+)/)
  if (!match) {
    console.error(`__session cookie not found in Set-Cookie header. Got: ${setCookieStr.slice(0, 200)}`)
    process.exit(1)
  }

  const outputFile = process.env.COOKIE_OUTPUT_FILE
  if (outputFile) {
    writeFileSync(outputFile, match[1])
    console.error(`Cookie written to ${outputFile} (${match[1].length} bytes, no wrapper stdout can reach this file).`)
  } else {
    process.stdout.write(match[1])
  }
}

// ─────────────────────────────────────────────────────────────────────────────────────────────
// `isDirectEntrypoint` is THE ONE SHARED IMPLEMENTATION, in `scripts/lib/entrypoint.ts`.
//
// It used to be a private copy of that function in this file. Nirmāṇa finding F-2 (M0-T60,
// re-filed by M0-T65 at EIGHT copies) is that a security-relevant predicate duplicated N times
// with no detector asserting the bodies agree is a defect on its own terms; ruling D-67 part 3
// granted the shared implementation. Task M0-T66.
//
// Imported, not mirrored, and that is safe here for the reason ruling D-9 actually gives:
// `scripts/lib/entrypoint.ts` imports only the three node builtins this file already imported
// for its own copy, and has no module-scope effect at all. This module's graph gains nothing.
//
// Re-exported so this module's public surface is exactly what it was.
export { isDirectEntrypoint }
// ─────────────────────────────────────────────────────────────────────────────────────────────

// Guard: only execute when this module IS the entrypoint — never as an import side effect.
//
// THE HAZARD IS RUNNING. `main()` mints a Firebase custom token for `SUPER_ADMIN_UID`,
// exchanges it for an ID token over the network, POSTs that to `${SERVICE_URL}/api/auth/session`
// — which defaults to localhost but is routinely pointed at PRODUCTION — and writes the
// resulting `__session` cookie to stdout, or to `COOKIE_OUTPUT_FILE` if set. An incidental
// import therefore issued a live privileged-session grant and could overwrite an arbitrary path
// named by an environment variable; its four `process.exit(1)` paths killed the importer.
//
// This is the `isDirectEntrypoint` contract (Nirmāṇa M0-T60 / A3.4 operator rule 5), NOT the
// `IMPORT_ONLY !== '1'` contract the two CI gates use (M0-T50 / ruling D-49, documented at
// `scripts/audit/A3_env_matrix.md` Addendum A3.4). A gate's hazard is FAILING to run, so its safe
// default is RUN. This file's hazard is RUNNING, so its safe default is DO NOT RUN.
//
// Nirmāṇa WORK_QUEUE M0-T65, ruling D-74 part 1 (wave 1 of F-4 tier 1: the five scripts that were
// destructive or credential-touching on incidental import). Verified WITHOUT executing this file —
// D-74 parts 2 and 3 forbid running it — by structural assertion over this source plus behavioural
// tests of the identical idiom on a harmless stand-in module. See
// `scripts/__tests__/destructive_entrypoint_guards.test.ts`.
if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  main().catch((e) => {
    console.error(e)
    process.exit(1)
  })
}
