// Mint a Firebase ID token for a super-admin UID, suitable for use as
// the __session cookie in authenticated API calls during dev, acceptance,
// and smoke runs.
//
// Required env vars:
//   FIREBASE_ADMIN_CREDENTIALS      JSON-stringified service-account credentials
//   NEXT_PUBLIC_FIREBASE_API_KEY    Firebase web API key
//   SUPER_ADMIN_UID                 UID of the super-admin to impersonate
//
// Usage:
//   SUPER_ADMIN_UID=<uid> npx tsx platform/scripts/dev/mint_session_cookie.ts
//
// Prints the ID token to stdout. Pipe into curl or capture into $COOKIE.

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
  const FIREBASE_API_KEY = process.env.NEXT_PUBLIC_FIREBASE_API_KEY!
  if (!FIREBASE_API_KEY) throw new Error('NEXT_PUBLIC_FIREBASE_API_KEY not set')
  
  const customToken = await auth.createCustomToken(UID)
  
  const response = await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${FIREBASE_API_KEY}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: customToken, returnSecureToken: true })
  })
  
  const data = await response.json() as any
  if (data.error) {
    console.error('Firebase error:', JSON.stringify(data.error))
    process.exit(1)
  }
  
  process.stdout.write(data.idToken)
}

main().catch(e => { console.error(e); process.exit(1) })
