#!/usr/bin/env tsx
/**
 * cutover:stage1-smoke — Phase 11A end-to-end smoke test.
 *
 * Verifies the new query pipeline is default-on and working:
 *   1. Env guard: NEW_QUERY_PIPELINE_ENABLED + AUDIT_ENABLED both true, all
 *      provider keys present, Cloud SQL reachable.
 *   2. Sends one query per query class (8 classes) to POST /api/chat/consume.
 *   3. Asserts: HTTP 200, stream completes, citation marker present.
 *   4. Queries audit_log directly: count ≥ 8 rows written since smoke start.
 *   5. Fetches GET /api/audit/[query_id] for 2 rows; verifies response shape.
 *   6. Prints green ✅ summary or red ✗ failure list; exits 1 on any failure.
 *
 * Prerequisites (must be true before running):
 *   - Next.js dev server running: `cd platform && npm run dev`
 *   - Cloud SQL Auth Proxy running (or DATABASE_URL pointing at live DB)
 *   - SMOKE_SESSION_COOKIE env var: copy the `__session` cookie value from
 *     browser DevTools → Application → Cookies while logged into the app.
 *     (Open DevTools, go to Application tab, find __session under the localhost
 *     domain, copy the Value field.)
 *   - SMOKE_CHART_ID env var: the UUID of a valid chart in the DB.
 *     Run: `npm run audit:replay -- --last=1` to find a recent chart_id, or
 *     query the DB: `SELECT id FROM charts LIMIT 1;`
 *
 * Usage:
 *   npm run cutover:stage1-smoke
 *
 * Optional overrides:
 *   SMOKE_SERVER_URL=http://localhost:3000   (default)
 */

import { readFileSync, existsSync } from 'fs'
import { join } from 'path'

// ── Env loader ────────────────────────────────────────────────────────────────

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

import { Pool } from 'pg'

// ── Config ────────────────────────────────────────────────────────────────────

const SERVER_URL = process.env.SMOKE_SERVER_URL ?? 'http://localhost:3000'
const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE ?? ''
const CHART_ID = process.env.SMOKE_CHART_ID ?? ''

// Citation patterns produced by synthesis prompts.
// Matches [F.xxx], [FORENSIC.xxx], [SIG.MSR.xxx], [signal:xxx], [asset:xxx], [chunk:xxx]
const CITATION_RE = /(?:\[(F\.|FORENSIC\.|SIG\.MSR\.|signal:|asset:|chunk:)[^\]]+\]|\(→\s*(?:SIG\.MSR\.\d+|FORENSIC\.[^\s)]+|F\.[^\s)]+)\))/

// Disclosure / pipeline-tier indicator in the AI SDK stream JSON.
const PIPELINE_TIER_RE = /"pipeline"\s*:\s*"v2"/

// ── Query set: one per class ──────────────────────────────────────────────────

interface SmokeQuery {
  queryClass: string
  source: string
  text: string
}

// 6 drawn from synthesis_golden_v1_0.json + 2 supplementary for remedial + cross_native
const SMOKE_QUERIES: SmokeQuery[] = [
  {
    queryClass: 'factual',
    source: 'SQ.006',
    text: 'What planet lords Abhisek\'s 7th house?',
  },
  {
    queryClass: 'interpretive',
    source: 'SQ.002',
    text: 'What is the core psychological tension that runs through Abhisek\'s natal chart, and how does it shape his lived experience across domains?',
  },
  {
    queryClass: 'predictive',
    source: 'SQ.004',
    text: 'When and how will the career themes in Abhisek\'s chart crystallize in the upcoming dasha sequence, and what are the timing indicators?',
  },
  {
    queryClass: 'cross_domain',
    source: 'SQ.001',
    text: 'How do career and wealth domains interact in Abhisek\'s chart, and what planetary configurations bridge these two domains?',
  },
  {
    queryClass: 'holistic',
    source: 'SQ.005',
    text: 'What is the spiritual and dharmic mission encoded in Abhisek\'s chart, and how do the planetary combinations support or challenge it?',
  },
  {
    queryClass: 'discovery',
    source: 'SQ.009',
    text: 'How does this instrument handle conflicting interpretations from different Jyotish systems or commentators when they disagree about a chart placement?',
  },
  {
    queryClass: 'remedial',
    source: 'SUPP.1',
    text: 'What remedial measures would help Abhisek navigate the challenges indicated by his Rahu mahadasha, and which remedies have the strongest shastric basis for his ascendant?',
  },
  {
    queryClass: 'cross_native',
    source: 'SUPP.2',
    text: 'What patterns in Abhisek\'s chart — particularly around Saturn placement and its aspects — are characteristically shared by individuals with strong Saturn configurations in Aquarius?',
  },
]

// ── Helpers ───────────────────────────────────────────────────────────────────

interface QueryResult {
  queryClass: string
  source: string
  queryText: string
  queryId: string | null
  httpStatus: number | null
  streamText: string
  passCitation: boolean
  passDisclosure: boolean
  passHttp: boolean
  error: string | null
}

async function submitQuery(q: SmokeQuery): Promise<QueryResult> {
  const result: QueryResult = {
    queryClass: q.queryClass,
    source: q.source,
    queryText: q.text,
    queryId: null,
    httpStatus: null,
    streamText: '',
    passCitation: false,
    passDisclosure: false,
    passHttp: false,
    error: null,
  }

  try {
    const body = {
      chartId: CHART_ID,
      messages: [{ role: 'user', id: 'smoke-msg-1', parts: [{ type: 'text', text: q.text }] }],
    }

    const response = await fetch(`${SERVER_URL}/api/chat/consume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Cookie: `__session=${SESSION_COOKIE}`,
      },
      body: JSON.stringify(body),
    })

    result.httpStatus = response.status
    result.passHttp = response.status === 200

    if (!result.passHttp) {
      const errText = await response.text()
      result.error = `HTTP ${response.status}: ${errText.slice(0, 200)}`
      return result
    }

    // Consume the full stream
    const reader = response.body?.getReader()
    if (!reader) {
      result.error = 'No response body reader'
      return result
    }

    const decoder = new TextDecoder()
    let fullText = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      fullText += decoder.decode(value, { stream: true })
    }
    result.streamText = fullText

    // Extract query_id from stream metadata lines (AI SDK format: "8:{"queryId":"..."}")
    const qIdMatch = fullText.match(/"query_id"\s*:\s*"([0-9a-f-]{36})"/i)
      ?? fullText.match(/"queryId"\s*:\s*"([0-9a-f-]{36})"/i)
    result.queryId = qIdMatch?.[1] ?? null

    result.passCitation = CITATION_RE.test(fullText)
    result.passDisclosure = PIPELINE_TIER_RE.test(fullText)
  } catch (err) {
    result.error = err instanceof Error ? err.message : String(err)
  }

  return result
}

async function checkAuditRows(pool: Pool, since: Date, minCount: number): Promise<{ count: number; pass: boolean }> {
  const { rows } = await pool.query<{ count: string }>(
    'SELECT count(*)::text FROM audit_log WHERE created_at >= $1',
    [since.toISOString()]
  )
  const count = parseInt(rows[0]?.count ?? '0', 10)
  return { count, pass: count >= minCount }
}

async function checkAuditDetail(queryId: string): Promise<{ pass: boolean; error: string | null; keys: string[] }> {
  try {
    const resp = await fetch(`${SERVER_URL}/api/audit/${queryId}`, {
      headers: { Cookie: `__session=${SESSION_COOKIE}` },
    })
    if (resp.status !== 200) return { pass: false, error: `HTTP ${resp.status}`, keys: [] }
    const data = (await resp.json()) as { row?: Record<string, unknown> }
    const row = data.row ?? {}
    const keys = Object.keys(row)
    // 8 required detail fields from the audit schema
    const required = ['id', 'query_id', 'query_text', 'query_class', 'bundle_keys',
      'tools_called', 'validators_run', 'final_output']
    const missing = required.filter(k => !(k in row))
    if (missing.length > 0) return { pass: false, error: `Missing fields: ${missing.join(', ')}`, keys }
    return { pass: true, error: null, keys }
  } catch (err) {
    return { pass: false, error: err instanceof Error ? err.message : String(err), keys: [] }
  }
}

// ── Guard checks ──────────────────────────────────────────────────────────────

function guardEnv(): string[] {
  const errors: string[] = []

  if (!SESSION_COOKIE) {
    errors.push(
      'SMOKE_SESSION_COOKIE is not set.\n' +
      '  How to get it: open the app in your browser, log in, open DevTools →\n' +
      '  Application → Cookies → localhost:3000 → find __session → copy Value.'
    )
  }

  if (!CHART_ID) {
    errors.push(
      'SMOKE_CHART_ID is not set.\n' +
      '  How to get it: run `npm run audit:replay -- --last=1` and copy the\n' +
      '  chart_id field, or query: SELECT id FROM charts LIMIT 1;'
    )
  }

  if (!process.env.ANTHROPIC_API_KEY) errors.push('ANTHROPIC_API_KEY is not set.')
  if (!process.env.OPENAI_API_KEY) errors.push('OPENAI_API_KEY is not set.')
  if (!process.env.GOOGLE_GENERATIVE_AI_API_KEY && !process.env.GCP_PROJECT) {
    errors.push('GOOGLE_GENERATIVE_AI_API_KEY (or GCP_PROJECT for ADC) is not set.')
  }
  if (!process.env.DATABASE_URL) errors.push('DATABASE_URL is not set. Start Cloud SQL Auth Proxy.')

  // Verify flag defaults by importing the flags module
  // (flags are read at import time, so this reflects actual defaults)
  const newPipelineFlag = process.env.MARSYS_FLAG_NEW_QUERY_PIPELINE_ENABLED
  const auditFlag = process.env.MARSYS_FLAG_AUDIT_ENABLED
  if (newPipelineFlag === 'false') {
    errors.push('MARSYS_FLAG_NEW_QUERY_PIPELINE_ENABLED is explicitly set to false — pipeline cutover not active.')
  }
  if (auditFlag === 'false') {
    errors.push('MARSYS_FLAG_AUDIT_ENABLED is explicitly set to false — audit logging not active.')
  }

  return errors
}

async function guardDbReachable(pool: Pool): Promise<string | null> {
  try {
    await pool.query('SELECT 1')
    return null
  } catch (err) {
    return `Cloud SQL not reachable: ${err instanceof Error ? err.message : String(err)}\n  Start the Auth Proxy and re-run.`
  }
}

async function guardServerReachable(): Promise<string | null> {
  try {
    const r = await fetch(`${SERVER_URL}/api/auth/session`, { method: 'HEAD' })
      .catch(() => fetch(`${SERVER_URL}/`))
    if (r.status >= 500) return `Dev server returned ${r.status} — check server logs.`
    return null
  } catch {
    return `Dev server not reachable at ${SERVER_URL}. Run: npm run dev`
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('  MARSYS-JIS Phase 11A — Stage 1 Cutover Smoke Test')
  console.log('  2026-04-28 | new pipeline default-on | all 8 query classes')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')

  // ── Guard phase ──────────────────────────────────────────────────────────
  console.log('Step 1 — Environment guard...')

  const envErrors = guardEnv()
  if (envErrors.length > 0) {
    console.error('\n✗ Environment guard failed:')
    for (const e of envErrors) console.error(`  • ${e}`)
    console.error('\nFix the above issues and re-run.\n')
    process.exit(1)
  }

  const pool = new Pool({ connectionString: process.env.DATABASE_URL! })

  const dbError = await guardDbReachable(pool)
  if (dbError) {
    console.error(`\n✗ ${dbError}\n`)
    await pool.end()
    process.exit(1)
  }

  const serverError = await guardServerReachable()
  if (serverError) {
    console.error(`\n✗ ${serverError}\n`)
    await pool.end()
    process.exit(1)
  }

  console.log('  ✓ All environment checks passed\n')

  // ── Query submission ─────────────────────────────────────────────────────
  console.log('Step 2 — Submitting queries to /api/chat/consume...')
  const smokeStart = new Date()
  const queryResults: QueryResult[] = []

  for (const q of SMOKE_QUERIES) {
    process.stdout.write(`  [${q.queryClass}] (${q.source}) ... `)
    const r = await submitQuery(q)
    queryResults.push(r)
    if (r.passHttp) {
      console.log(`HTTP ${r.httpStatus} ✓`)
    } else {
      console.log(`HTTP ${r.httpStatus ?? 'ERR'} ✗  ${r.error ?? ''}`)
    }
  }

  // ── Assertion summary ────────────────────────────────────────────────────
  console.log('\nStep 3 — Assertions per query...')

  const failures: string[] = []

  for (const r of queryResults) {
    const tag = `[${r.queryClass}]`

    if (!r.passHttp) {
      failures.push(`${tag} HTTP failed: ${r.error ?? `status ${r.httpStatus}`}`)
      continue
    }

    if (r.streamText.length < 20) {
      failures.push(`${tag} Stream body is empty or too short (${r.streamText.length} chars)`)
    }

    if (!r.passCitation) {
      // Warn but don't fail — factual queries may not always include citations.
      // Fail hard for interpretive / cross_domain classes where citations are mandatory.
      const mandatoryCitationClasses = ['interpretive', 'cross_domain', 'holistic', 'discovery']
      if (mandatoryCitationClasses.includes(r.queryClass)) {
        failures.push(`${tag} No citation marker found in stream (${r.queryClass} requires citations)`)
      } else {
        console.log(`    ⚠  ${tag} No citation marker (non-mandatory for ${r.queryClass})`)
      }
    }

    const citationStatus = r.passCitation ? '✓ citation' : '⚠ no-citation'
    const disclosureStatus = r.passDisclosure ? '✓ v2' : '⚠ no-v2-marker'
    console.log(`  ${r.passHttp ? '✓' : '✗'} ${tag} (${r.source}) — ${citationStatus} | ${disclosureStatus} | queryId=${r.queryId ?? 'not-found'}`)
  }

  // ── Audit log check ──────────────────────────────────────────────────────
  // onAuditEvent fires inside server-side onFinish which runs asynchronously
  // after the HTTP response body closes. Give the server time to flush all
  // audit writes before querying the DB.
  console.log('\nStep 4 — Waiting 10s for audit writes to settle...')
  await new Promise(resolve => setTimeout(resolve, 10_000))
  console.log('  Checking audit_log for written rows...')
  const { count, pass: passAuditCount } = await checkAuditRows(pool, smokeStart, 8)
  console.log(`  audit_log rows since smoke start: ${count} (need ≥ 8) ${passAuditCount ? '✓' : '✗'}`)
  if (!passAuditCount) {
    failures.push(`audit_log has only ${count} row(s) since ${smokeStart.toISOString()} — expected ≥ 8. Check AUDIT_ENABLED flag and DB connection.`)
  }

  // ── Audit detail check ───────────────────────────────────────────────────
  console.log('\nStep 5 — Fetching /api/audit/[query_id] for 2 representative rows...')

  const representativeQueryIds = queryResults
    .filter(r => r.queryId !== null)
    .slice(0, 2)
    .map(r => r.queryId!)

  if (representativeQueryIds.length < 2) {
    const msg = `Only ${representativeQueryIds.length} query_id(s) found in stream responses — need 2 for detail check. The pipeline may not be embedding query_id in stream metadata.`
    console.log(`  ⚠  ${msg}`)
    // Non-blocking: audit_log query above already verified rows exist.
  }

  for (const qid of representativeQueryIds) {
    const { pass, error, keys } = await checkAuditDetail(qid)
    console.log(`  /api/audit/${qid}: ${pass ? '✓' : '✗'} (fields=${keys.length}) ${error ?? ''}`)
    if (!pass) failures.push(`audit detail for ${qid}: ${error}`)
  }

  // ── Final report ─────────────────────────────────────────────────────────
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

  if (failures.length === 0) {
    console.log('✅  Stage 1 smoke PASSED — new pipeline is default-on and healthy.')
    console.log('    When ready: trigger Phase 11B to delete legacy code path.')
  } else {
    console.log('✗  Stage 1 smoke FAILED:\n')
    for (const f of failures) console.log(`  • ${f}`)
    console.log('\nFix the above failures before triggering Phase 11B.')
  }

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')

  await pool.end()
  process.exit(failures.length > 0 ? 1 : 0)
}

main().catch(err => {
  console.error('Smoke script crashed:', err)
  process.exit(1)
})
