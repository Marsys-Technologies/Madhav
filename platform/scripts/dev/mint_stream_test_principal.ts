// Provision (idempotently) a per-stream test principal on the synthetic
// Pariprashna assurance chart, and mint it a __session cookie.
//
// WHY THIS EXISTS (Pariprashna V3 A4, campaign decision ledger_seq re: the
// S2 click-through block):
//
//   Every assurance stream (S1, S2, S5, ...) was minting sessions for the
//   SAME pre-existing Firebase UID `hunQRYVJ5Ec2mQnJnutK7AoQnsO2`
//   (`A2_CREDENTIAL_LANE_OUTCOME_v1_0.md`). `DELETE /api/auth/session`
//   (logout) and Firebase's `revokeRefreshTokens(uid)` are UID-scoped — see
//   `platform/src/app/api/auth/session/route.ts`'s `DELETE` handler and
//   `verifySessionCookie()`'s `checkRevoked: true` flag
//   (`platform/src/lib/firebase/server.ts`). Revoking one stream's session
//   (a logout/session-revocation drill, e.g. stream S5's security battery)
//   therefore invalidates EVERY other stream's still-active session cookie
//   for that same UID — S5's drill silently killed S2's mid-run
//   click-through session, because both streams were, without realizing it,
//   the same underlying principal.
//
//   The fix is NOT a change to production auth semantics (revocation being
//   UID-scoped is correct Firebase behavior, and it is not this lane's job
//   to relax it — see V3-E-017/S5). The fix is test-infrastructure
//   provisioning: give each stream its OWN Firebase UID, each with its own
//   `chart_grants` row scoped to the synthetic chart only. The existing
//   authorization brain (`authorizeChartAccess.ts`) already supports many
//   simultaneous guest grantees on one chart (three pre-existing test
//   principals already coexist on it) — this script simply mints another
//   one per stream instead of reusing a shared identity. Revoking stream
//   A's principal now only ever revokes stream A's principal.
//
// WHAT THIS SCRIPT TOUCHES:
//   - INSERTs at most one `chart_grants` row: (chart_id=<synthetic chart>,
//     principal_id=<derived per-stream UID>, permission='view'). Idempotent
//     (ON CONFLICT DO NOTHING on the table's existing UNIQUE(chart_id,
//     principal_id) constraint) — safe to re-run.
//   - Mints a Firebase custom token for that UID (creating the Firebase Auth
//     user on first use, exactly like the existing
//     `mint_session_cookie.ts` recipe) and exchanges it for a `__session`
//     cookie via the app's own `/api/auth/session` endpoint. That endpoint's
//     own profile-sync logic (`route.ts` POST handler) auto-inserts the
//     `profiles` row as `role='guest', status='active'` on first mint — no
//     manual profile provisioning needed here.
//   - Never touches production auth logic, `authorizeChartAccess.ts`,
//     `revokeRefreshTokens`, or any existing shared test principal's grants.
//     Strictly additive: a new capability (distinct principals), not a
//     loosened check.
//
// HARD SAFETY RAIL: refuses to run against the native's real chart
// (`482012f1-710e-4a25-994a-93821f5871aa`) even if explicitly passed via
// CHART_ID — this script is synthetic-chart-only, unconditionally.
//
// Required env vars:
//   FIREBASE_ADMIN_CREDENTIALS      JSON-stringified service-account credentials
//   NEXT_PUBLIC_FIREBASE_API_KEY    Firebase web API key
//   DATABASE_URL                    Postgres connection string (Cloud SQL Auth
//                                    Proxy or direct) — used ONLY for the
//                                    chart_grants provisioning step.
//   STREAM_ID                       Short stream label, e.g. "s2", "s5",
//                                    "smoke-test". Used to derive the UID
//                                    (`pariprashna-test-<stream_id>`) unless
//                                    TEST_PRINCIPAL_UID overrides it.
//
// Optional env vars:
//   TEST_PRINCIPAL_UID              Override the derived UID entirely.
//   CHART_ID                        Default: the synthetic assurance chart
//                                    `1c826d5a-41cb-4450-b4dc-59d440e5f75a`.
//   GRANTED_BY                      Text label for chart_grants.granted_by.
//                                    Default: 'pariprashna-v3-a4-provisioning'.
//   SERVICE_URL                     Target service base URL. Default:
//                                    http://localhost:3000.
//   COOKIE_OUTPUT_FILE              Write the cookie value directly to this
//                                    file instead of stdout (recommended —
//                                    see mint_session_cookie.ts's own note on
//                                    why: dotenvx's startup banner can share
//                                    stdout with a wrapped script).
//
// Usage:
//   STREAM_ID=s2 DATABASE_URL=... SERVICE_URL=... npx dotenvx run \
//     -f platform/.env.local -- npx tsx platform/scripts/dev/mint_stream_test_principal.ts
//
// Exit 0 on success, non-zero on any failure (with error written to stderr).

import { writeFileSync } from 'node:fs'
import { Pool } from 'pg'
import { initializeApp, getApps, cert } from 'firebase-admin/app'
import { getAuth } from 'firebase-admin/auth'

const SYNTHETIC_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function deriveUid(streamId: string): string {
  const slug = streamId.trim().toLowerCase().replace(/[^a-z0-9-]/g, '-')
  if (!slug) throw new Error('STREAM_ID produced an empty slug')
  return `pariprashna-test-${slug}`
}

async function ensureChartGrant(chartId: string, uid: string, grantedBy: string) {
  const databaseUrl = process.env.DATABASE_URL
  if (!databaseUrl) throw new Error('DATABASE_URL not set')

  const pool = new Pool({ connectionString: databaseUrl })
  try {
    const chartRes = await pool.query('SELECT id FROM charts WHERE id=$1', [chartId])
    if (chartRes.rows.length === 0) {
      throw new Error(`chart ${chartId} does not exist — refusing to grant against a phantom chart_id`)
    }

    const insertRes = await pool.query(
      `INSERT INTO chart_grants (chart_id, principal_id, permission, granted_by)
       VALUES ($1, $2, 'view', $3)
       ON CONFLICT (chart_id, principal_id) DO NOTHING
       RETURNING id`,
      [chartId, uid, grantedBy]
    )
    const created = insertRes.rows.length > 0

    const existing = await pool.query(
      'SELECT chart_id FROM chart_grants WHERE principal_id=$1',
      [uid]
    )
    const otherCharts = existing.rows.map((r) => r.chart_id).filter((id: string) => id !== chartId)
    if (otherCharts.length > 0) {
      // Should be unreachable for a freshly-derived per-stream UID, but if an
      // operator reused TEST_PRINCIPAL_UID for something broader, surface it
      // loudly rather than silently minting a session with wider scope than
      // the caller expects.
      console.error(
        `WARNING: principal ${uid} also holds chart_grants on: ${otherCharts.join(', ')}. ` +
          `This script only asserts the grant on ${chartId}; it does not narrow existing scope.`
      )
    }

    return { created }
  } finally {
    await pool.end()
  }
}

async function mintCookie(uid: string): Promise<string> {
  const credsRaw = process.env.FIREBASE_ADMIN_CREDENTIALS
  if (!credsRaw) throw new Error('FIREBASE_ADMIN_CREDENTIALS not set')
  const CREDS = JSON.parse(credsRaw)
  const app = getApps().length > 0 ? getApps()[0] : initializeApp({ credential: cert(CREDS) })
  const auth = getAuth(app)

  const FIREBASE_API_KEY = process.env.NEXT_PUBLIC_FIREBASE_API_KEY
  if (!FIREBASE_API_KEY) throw new Error('NEXT_PUBLIC_FIREBASE_API_KEY not set')

  const SERVICE_URL = (process.env.SERVICE_URL ?? 'http://localhost:3000').replace(/\/$/, '')

  const customToken = await auth.createCustomToken(uid)
  const fbResp = await fetch(
    `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${FIREBASE_API_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: customToken, returnSecureToken: true }),
    }
  )
  const fbData = (await fbResp.json()) as { idToken?: string; error?: unknown }
  if (fbData.error || !fbData.idToken) {
    throw new Error(`Firebase signInWithCustomToken failed: ${JSON.stringify(fbData.error ?? fbData)}`)
  }

  const sessResp = await fetch(`${SERVICE_URL}/api/auth/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idToken: fbData.idToken }),
  })
  if (!sessResp.ok) {
    const body = await sessResp.text().catch(() => '<unreadable>')
    throw new Error(`/api/auth/session returned ${sessResp.status}: ${body}`)
  }

  const headersWithGetSetCookie = sessResp.headers as Headers & { getSetCookie?: () => string[] }
  const rawSetCookie = headersWithGetSetCookie.getSetCookie?.() ?? sessResp.headers.get('set-cookie') ?? ''
  const setCookieStr = Array.isArray(rawSetCookie) ? rawSetCookie.join('\n') : String(rawSetCookie)
  const match = setCookieStr.match(/__session=([^;]+)/)
  if (!match) {
    throw new Error(`__session cookie not found in Set-Cookie header. Got: ${setCookieStr.slice(0, 200)}`)
  }
  return match[1]
}

async function main() {
  const chartId = process.env.CHART_ID ?? SYNTHETIC_CHART_ID
  if (chartId === NATIVE_CHART_ID) {
    throw new Error(
      `Refusing: CHART_ID resolved to the native's real chart (${NATIVE_CHART_ID}). ` +
        'This script provisions synthetic-chart test principals only.'
    )
  }

  const streamId = process.env.STREAM_ID
  const uid = process.env.TEST_PRINCIPAL_UID ?? (streamId ? deriveUid(streamId) : undefined)
  if (!uid) throw new Error('Set STREAM_ID (or TEST_PRINCIPAL_UID directly)')

  const grantedBy = process.env.GRANTED_BY ?? 'pariprashna-v3-a4-provisioning'

  const { created } = await ensureChartGrant(chartId, uid, grantedBy)
  console.error(
    `[mint_stream_test_principal] uid=${uid} chart_id=${chartId} grant=${created ? 'created' : 'already present'}`
  )

  const cookie = await mintCookie(uid)

  const outputFile = process.env.COOKIE_OUTPUT_FILE
  if (outputFile) {
    writeFileSync(outputFile, cookie)
    console.error(
      `[mint_stream_test_principal] uid=${uid}: cookie written to ${outputFile} (${cookie.length} bytes).`
    )
  } else {
    process.stdout.write(cookie)
  }
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
