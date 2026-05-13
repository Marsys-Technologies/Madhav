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
//
// Usage:
//   SERVICE_URL=https://... SUPER_ADMIN_UID=<uid> npx tsx platform/scripts/dev/mint_session_cookie.ts
//
// Prints the __session cookie VALUE (not the full Set-Cookie line) to stdout.
// Pipe directly into curl: COOKIE=$(... ); curl -H "Cookie: __session=$COOKIE" ...
// Exit 0 on success, non-zero on any failure (with error written to stderr).

import { initializeApp, getApps, cert } from 'firebase-admin/app'
import { getAuth } from 'firebase-admin/auth'

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

  process.stdout.write(match[1])
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
