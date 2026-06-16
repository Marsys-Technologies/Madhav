#!/usr/bin/env tsx
/**
 * probe_11c_b — post-deploy verification for RETRIEVAL_11C_b.
 *
 * Steps:
 *   1. Firebase Admin: create a custom token for SUPER_ADMIN_EMAIL.
 *   2. Firebase REST API: signInWithCustomToken → idToken.
 *   3. POST deployed_url/api/auth/session → __session cookie.
 *   4. Send 5 test queries to deployed_url/api/chat/consume (streaming).
 *   5. Wait 30s.
 *   6. Query query_trace_steps for cgm_graph_walk rows.
 *   7. Print results.
 */

import { readFileSync, existsSync } from 'fs'
import { join } from 'path'
import { Pool } from 'pg'

function loadEnvFile(file: string): void {
  const p = join(process.cwd(), file)
  if (!existsSync(p)) return
  for (const line of readFileSync(p, 'utf8').split('\n')) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const eqIdx = trimmed.indexOf('=')
    if (eqIdx < 0) continue
    const key = trimmed.slice(0, eqIdx).trim()
    const val = trimmed.slice(eqIdx + 1).trim().replace(/^["']|["']$/g, '')
    if (!process.env[key]) process.env[key] = val
  }
}
loadEnvFile('.env.local')
loadEnvFile('.env.rag')

const DEPLOYED_URL = process.env.SMOKE_SERVER_URL ?? 'https://amjis-web-938361928218.asia-south1.run.app'
const FIREBASE_API_KEY = process.env.NEXT_PUBLIC_FIREBASE_API_KEY ?? ''
const SUPER_ADMIN_EMAIL = process.env.SUPER_ADMIN_EMAIL ?? ''
const CHART_ID = process.env.SMOKE_CHART_ID ?? '482012f1-710e-4a25-994a-93821f5871aa'
const DB_URL = process.env.DATABASE_URL ?? ''

const TEST_QUERIES = [
  'What does my Mercury support in my chart?',
  'How do my Mars and Saturn interact?',
  'What does my Saturn dasha bring next?',
  'Are there contradictions in my chart?',
  'Explain my chart in general terms.',
]

async function getCustomToken(): Promise<string> {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { initializeApp, getApps, cert } = require('firebase-admin/app')
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { getAuth } = require('firebase-admin/auth')
  const serviceAccount = JSON.parse(process.env.FIREBASE_ADMIN_CREDENTIALS ?? '{}')
  const app = getApps().length > 0 ? getApps()[0] : initializeApp({ credential: cert(serviceAccount) })
  const auth = getAuth(app)
  const user = await auth.getUserByEmail(SUPER_ADMIN_EMAIL)
  return auth.createCustomToken(user.uid)
}

async function signInWithCustomToken(customToken: string): Promise<string> {
  const res = await fetch(
    `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${FIREBASE_API_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: customToken, returnSecureToken: true }),
    }
  )
  const data = await res.json() as { idToken?: string; error?: { message: string } }
  if (!data.idToken) throw new Error(`signInWithCustomToken failed: ${JSON.stringify(data.error)}`)
  return data.idToken
}

async function createSessionCookie(idToken: string): Promise<string> {
  const res = await fetch(`${DEPLOYED_URL}/api/auth/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idToken }),
  })
  if (!res.ok) throw new Error(`session creation failed: ${res.status} ${await res.text()}`)
  const setCookie = res.headers.get('set-cookie') ?? ''
  const match = setCookie.match(/__session=([^;]+)/)
  if (!match) throw new Error(`no __session cookie in response: ${setCookie}`)
  return match[1]
}

async function sendQuery(query: string, sessionCookie: string): Promise<string> {
  const body = JSON.stringify({
    messages: [{ id: crypto.randomUUID(), role: 'user', content: query, parts: [{ type: 'text', text: query }] }],
    chartId: CHART_ID,
    model: 'claude-haiku-4-5',
    style: 'default',
  })
  const res = await fetch(`${DEPLOYED_URL}/api/chat/consume`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Cookie: `__session=${sessionCookie}`,
    },
    body,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`consume failed: ${res.status} ${text.slice(0, 200)}`)
  }
  // Drain the stream
  const reader = res.body?.getReader()
  if (!reader) return ''
  let queryId = ''
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value)
    // Look for query_id in trace event
    const idMatch = chunk.match(/"query_id"\s*:\s*"([0-9a-f-]{36})"/)
    if (idMatch) queryId = idMatch[1]
  }
  return queryId
}

async function main() {
  console.log('=== RETRIEVAL_11C_b Post-Deploy Verification ===')
  console.log(`Deployed URL: ${DEPLOYED_URL}`)
  console.log(`Chart ID: ${CHART_ID}`)
  console.log(`Super Admin: ${SUPER_ADMIN_EMAIL}`)
  console.log()

  // Step 1–3: Get session cookie
  console.log('Step 1: Getting Firebase custom token...')
  const customToken = await getCustomToken()
  console.log('  ✓ Custom token obtained')

  console.log('Step 2: Exchanging for ID token...')
  const idToken = await signInWithCustomToken(customToken)
  console.log('  ✓ ID token obtained')

  console.log('Step 3: Creating session cookie on deployed service...')
  const sessionCookie = await createSessionCookie(idToken)
  console.log('  ✓ Session cookie obtained')
  console.log()

  // Step 4: Send 5 queries
  const sentAt = new Date()
  console.log(`Step 4: Sending ${TEST_QUERIES.length} test queries at ${sentAt.toISOString()}...`)
  const queryIds: string[] = []
  for (const q of TEST_QUERIES) {
    console.log(`  → "${q}"`)
    try {
      const qid = await sendQuery(q, sessionCookie)
      queryIds.push(qid)
      console.log(`    query_id: ${qid || '(not captured in stream)'}`)
    } catch (err) {
      console.error(`    FAILED: ${err}`)
      queryIds.push('')
    }
  }
  console.log()

  // Step 5: Wait 30s
  console.log('Step 5: Waiting 30s for async trace writes...')
  await new Promise(resolve => setTimeout(resolve, 30_000))

  // Step 6: Query DB
  console.log('Step 6: Querying query_trace_steps for cgm_graph_walk results...')
  const pool = new Pool({ connectionString: DB_URL })
  try {
    const { rows } = await pool.query<{
      query_id: string
      step_seq: number
      step_name: string
      status: string
      item_count: number
    }>(
      `SELECT
        query_id,
        step_seq,
        step_name,
        status,
        COALESCE(jsonb_array_length(payload->'items'), 0) AS item_count
      FROM query_trace_steps
      WHERE created_at > $1
        AND step_name = 'cgm_graph_walk'
      ORDER BY query_id, step_seq`,
      [sentAt.toISOString()]
    )

    console.log()
    console.log('=== cgm_graph_walk trace rows (since queries were sent) ===')
    if (rows.length === 0) {
      console.log('  (none — cgm_graph_walk did not fire for any query)')
    } else {
      for (const row of rows) {
        console.log(`  query_id=${row.query_id} seq=${row.step_seq} status=${row.status} item_count=${row.item_count}`)
      }
    }

    const nonEmpty = rows.filter(r => r.item_count > 0).length
    console.log()
    console.log(`=== RESULT: cgm_graph_walk fired non-empty in ${nonEmpty} of ${TEST_QUERIES.length} queries ===`)
    console.log('  Baseline (PROBE 8, 2026-04-29): 1 of 17 queries (5.9%)')
    console.log(`  Post-fix: ${nonEmpty} of ${TEST_QUERIES.length} queries (${Math.round(nonEmpty / TEST_QUERIES.length * 100)}%)`)
    console.log(`  Target: ≥3 of 5 entity-named queries (60%)`)
    console.log()

    // Also capture graph_seed_hints from query_trace_steps classify step
    const { rows: seedRows } = await pool.query<{
      query_id: string
      seeds: string
    }>(
      `SELECT
        query_id,
        payload->'graph_seed_hints' AS seeds
      FROM query_trace_steps
      WHERE created_at > $1
        AND step_name = 'classify'
      ORDER BY created_at`,
      [sentAt.toISOString()]
    )
    if (seedRows.length > 0) {
      console.log('=== graph_seed_hints from classify steps ===')
      for (const row of seedRows) {
        console.log(`  query_id=${row.query_id}  seeds=${row.seeds}`)
      }
      console.log()
    }
  } finally {
    await pool.end()
  }
}

main().catch(err => {
  console.error('PROBE FAILED:', err)
  process.exit(1)
})
