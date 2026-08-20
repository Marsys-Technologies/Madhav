#!/usr/bin/env npx tsx
/**
 * probe/ask.ts — standing, non-interactive access to the LIVE `/api/pariprashna`
 * route for a real authenticated turn, driven end-to-end (auth mint → POST →
 * consume the SSE stream to completion → write one immutable JSON file per turn).
 *
 * Built per the native's own conductor-continuation request (2026-08-20):
 * "Give Claude Code seamless, standing access to the live Pariprashna route."
 * Full account of the credential investigation this script's design rests on
 * is in `origin/campaign-coordination`'s corresponding entry — read that
 * before touching this file's auth section.
 *
 * ── STEP 1 — the credential seam (what this script authenticates as) ───────
 *
 * Investigated the MCP canary key (`mcp-canary-key` in Secret Manager) first,
 * per instruction. Found: it is a real, valid `mcp_api_keys` Bearer credential
 * (key_id `mcp_prod_tDO7obNw…`, `user_uid: 'probe-service-account'`,
 * `scopes: {read}`, never revoked) that already successfully authenticates —
 * confirmed live by calling `tools/call prashna_ask` with it directly, which
 * returned a real `job_id`, not an auth error. It "only ever exercises the
 * auth boundary" in the deploy pipeline purely because
 * `mcp_end_to_end_smoke.sh` deliberately only ever sends `initialize`
 * (a documented, disclosed choice — avoid a real LLM-costing call on every
 * deploy) — NOT because of any credential/scope limitation. No widening was
 * needed there.
 *
 * BUT the MCP door and `/api/pariprashna` (the web SSE route this script
 * targets, per spec) are two structurally different auth systems: the web
 * route's `getServerUser()` (`lib/firebase/server.ts`) reads ONLY a Firebase
 * `__session` cookie — no Bearer/API-key fallback exists in that code path.
 * The MCP canary key is therefore NOT reusable here by construction, not by
 * choice; widening its `mcp_api_keys.scopes` would do nothing for this route.
 *
 * Rather than mint a brand-new principal, this script reuses the SAME
 * identity the canary key already uses — `user_uid = 'probe-service-account'`
 * — via the platform's OWN existing service-account impersonation mechanism,
 * `scripts/dev/mint_session_cookie.ts` (already in this repo, built for
 * exactly this: `createCustomToken(uid)` → exchange for an ID token via the
 * Firebase Identity Toolkit → POST `/api/auth/session` → extract the
 * `__session` cookie). That script's `SUPER_ADMIN_UID` env var is just a
 * variable name — it works for ANY uid string; re-pointing it at
 * `probe-service-account` needed zero code changes there. This script
 * inlines the same three-step mint (rather than shelling out) so a single
 * `npx tsx ask.ts` call is self-contained.
 *
 * `probe-service-account` already holds real `chart_grants` rows
 * (`permission: 'view'`) on BOTH the synthetic test chart
 * (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`, Abhinandan Mohanty — confirmed via
 * a live DB read) and the real native's canonical chart
 * (`482012f1-710e-4a25-994a-93821f5871aa`) — the latter is a PRE-EXISTING
 * grant this script did not create and will never rely on: see the STEP 4
 * guard below, which refuses to let the real native's chart be anything but
 * an explicit, deliberate choice. `authorizeTurn` (`pipeline/safety_gate.ts`)
 * only requires `permission !== 'deny'` — a `view` grant clears it. The
 * subject-consent and safety-gate checks that run after are both flag-gated
 * off in production as of this script's authoring (`SUBJECT_CONSENT_ENFORCEMENT`,
 * `PARIPRASHNA_SAFETY_GATE_ENABLED`), so neither blocks a synthetic-chart turn.
 *
 * DURABILITY: the root credential is `FIREBASE_ADMIN_CREDENTIALS` (a GCP
 * service-account key — revocable, but not time-limited) plus the fixed
 * `probe-service-account` uid string. Firebase session cookies themselves
 * cannot exceed 14 days (a Firebase Admin SDK hard limit, not a choice this
 * app or this script made) — this script sidesteps that entirely by NEVER
 * caching a cookie: it mints a fresh one on every single invocation. There is
 * no "refresh" step because there is nothing to refresh — the durable secret
 * (`FIREBASE_ADMIN_CREDENTIALS`) never expires, and every run re-derives a
 * brand-new, single-use session cookie from it.
 *
 * ── ONE-TIME SETUP ───────────────────────────────────────────────────────
 * Two values, neither requiring anything new to be created:
 *   FIREBASE_ADMIN_CREDENTIALS   — Secret Manager (`firebase-admin-credentials`),
 *                                  the same service-account key production
 *                                  deploys already use. Fetched via `gcloud
 *                                  secrets versions access` if not already
 *                                  in the environment.
 *   NEXT_PUBLIC_FIREBASE_API_KEY — NOT in Secret Manager (it's a GitHub
 *                                  Actions repo secret there, consumed only
 *                                  as a Next.js build-arg) — and doesn't need
 *                                  to be: it's a PUBLIC value by Firebase's
 *                                  own design (embedded in every client
 *                                  bundle; confidentiality is enforced by
 *                                  Firebase's own API-key restrictions).
 *                                  Fetched via `firebase apps:sdkconfig WEB
 *                                  --project=madhav-astrology` if not already
 *                                  in the environment — confirmed working
 *                                  live during this script's own authoring.
 * Both fetches need only the same `gcloud`/`firebase` CLI auth this whole
 * session already has — in practice there is NO manual setup step; just run
 * the script.
 *
 * ── USAGE ────────────────────────────────────────────────────────────────
 *   npx tsx platform/scripts/probe/ask.ts "What does this period ask of my career?"
 *   npx tsx platform/scripts/probe/ask.ts "..." --conversation-id <uuid>   # continue a thread
 *   npx tsx platform/scripts/probe/ask.ts "..." --chart-id <uuid>          # explicit override (see guard below)
 *   npx tsx platform/scripts/probe/ask.ts "..." --service-url https://... # default: live prod
 *
 * Writes `platform/scripts/probe/out/<turnId>.json` (one immutable file per
 * turn — every SSE event in arrival order, the assembled prose, the block
 * list with each block's kind, and the harness tag applied to the created
 * conversation). On truncation/error mid-stream, still writes the file,
 * marks `"partial": true`, and exits non-zero.
 */

import { writeFileSync, mkdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { execSync } from 'node:child_process'
import { randomUUID } from 'node:crypto'
import { Client } from 'pg'
import { initializeApp, getApps, cert } from 'firebase-admin/app'
import { getAuth } from 'firebase-admin/auth'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT_DIR = join(__dirname, 'out')

// ── STEP 4, guard 1 — the synthetic test chart is the ONLY default. ────────
// Abhinandan Mohanty, the pre-existing operator-E2E synthetic test chart
// (CLAUDE.md's L1 closure record: "operator E2E gated on Abhinandan Mohanty
// 1c826d5a"). NEVER the real native's canonical chart
// (482012f1-710e-4a25-994a-93821f5871aa, Abhisek Mohanty) unless a caller
// passes --chart-id explicitly — that is the ONLY path by which this script
// will ever touch the real native's chart.
const SYNTHETIC_TEST_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const REAL_NATIVE_CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const PROBE_UID = process.env.PROBE_UID ?? 'probe-service-account'
const DEFAULT_SERVICE_URL = 'https://amjis-web-qm256lasva-el.a.run.app'
const HARNESS_TITLE_MARKER = '[HARNESS PROBE]'

interface Args {
  question: string
  chartId: string
  chartIdExplicit: boolean
  conversationId: string | undefined
  serviceUrl: string
}

function parseArgs(argv: string[]): Args {
  const positional: string[] = []
  let chartId: string | undefined
  let conversationId: string | undefined
  let serviceUrl = DEFAULT_SERVICE_URL
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--chart-id') chartId = argv[++i]
    else if (a === '--conversation-id') conversationId = argv[++i]
    else if (a === '--service-url') serviceUrl = argv[++i]
    else positional.push(a)
  }
  const question = positional.join(' ').trim()
  if (!question) {
    console.error('Usage: npx tsx ask.ts "<question>" [--chart-id <uuid>] [--conversation-id <uuid>] [--service-url <url>]')
    process.exit(2)
  }
  const chartIdExplicit = chartId !== undefined
  return { question, chartId: chartId ?? SYNTHETIC_TEST_CHART_ID, chartIdExplicit, conversationId, serviceUrl }
}

/** Fetch a secret from Secret Manager if the matching env var isn't already set. Seamless — no manual export needed. */
function envOrSecret(envVar: string, secretName: string): string {
  const fromEnv = process.env[envVar]
  if (fromEnv) return fromEnv
  console.error(`[ask] ${envVar} not set — fetching Secret Manager:${secretName} …`)
  const value = execSync(
    `gcloud secrets versions access latest --secret=${secretName} --project=madhav-astrology`,
    { encoding: 'utf8' },
  ).trim()
  if (!value) throw new Error(`Secret Manager:${secretName} returned empty value`)
  return value
}

/**
 * The Firebase web API key is NOT in Secret Manager — it's a GitHub Actions
 * repo secret consumed only as a Next.js build-arg (deploy.yml), because it's
 * a PUBLIC value by Firebase's own design (embedded in every client bundle;
 * confidentiality is enforced by Firebase's own API-key restrictions, not by
 * hiding the string). Fetched here via `firebase apps:sdkconfig`, the correct
 * source for this specific value — confirmed working live during this
 * script's own authoring.
 */
function envOrFirebaseSdkConfig(envVar: string): string {
  const fromEnv = process.env[envVar]
  if (fromEnv) return fromEnv
  console.error(`[ask] ${envVar} not set — fetching via \`firebase apps:sdkconfig WEB\` …`)
  const raw = execSync('firebase apps:sdkconfig WEB --project=madhav-astrology', { encoding: 'utf8' })
  const config = JSON.parse(raw)
  if (!config.apiKey) throw new Error('firebase apps:sdkconfig WEB returned no apiKey field')
  return config.apiKey
}

/** Mint a FRESH single-use __session cookie for PROBE_UID. Never cached — see header. */
async function mintSessionCookie(serviceUrl: string): Promise<string> {
  const credsRaw = envOrSecret('FIREBASE_ADMIN_CREDENTIALS', 'firebase-admin-credentials')
  const apiKey = envOrFirebaseSdkConfig('NEXT_PUBLIC_FIREBASE_API_KEY')
  const creds = JSON.parse(credsRaw)
  const app = getApps().length > 0 ? getApps()[0] : initializeApp({ credential: cert(creds) })
  const auth = getAuth(app)

  const customToken = await auth.createCustomToken(PROBE_UID)
  const fbResp = await fetch(
    `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${apiKey}`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token: customToken, returnSecureToken: true }) },
  )
  const fbData = (await fbResp.json()) as { idToken?: string; error?: unknown }
  if (fbData.error || !fbData.idToken) {
    throw new Error(`Firebase signInWithCustomToken failed: ${JSON.stringify(fbData.error ?? fbData)}`)
  }

  const sessResp = await fetch(`${serviceUrl}/api/auth/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idToken: fbData.idToken }),
  })
  if (!sessResp.ok) {
    throw new Error(`/api/auth/session returned ${sessResp.status}: ${await sessResp.text().catch(() => '<unreadable>')}`)
  }
  const rawSetCookie = (sessResp.headers as any).getSetCookie?.() ?? sessResp.headers.get('set-cookie') ?? ''
  const setCookieStr = Array.isArray(rawSetCookie) ? rawSetCookie.join('\n') : String(rawSetCookie)
  const match = setCookieStr.match(/__session=([^;]+)/)
  if (!match) throw new Error(`__session cookie not found in Set-Cookie header. Got: ${setCookieStr.slice(0, 200)}`)
  return match[1]
}

/** Tag the conversation this turn created with the harness-origin marker (STEP 4, guard 2). Best-effort — never fails the turn. */
async function tagConversationAsHarness(conversationId: string): Promise<{ tagged: boolean; error?: string }> {
  const dbPassword = process.env.DB_PASSWORD ?? envOrSecret('DB_PASSWORD', 'amjis-db-password')
  const client = new Client({
    host: '127.0.0.1',
    port: Number(process.env.PGPORT ?? 5433),
    user: 'amjis_app',
    password: dbPassword,
    database: 'amjis',
  })
  try {
    await client.connect()
    const { rows } = await client.query('SELECT title FROM conversations WHERE id = $1', [conversationId])
    const currentTitle: string | null = rows[0]?.title ?? null
    if (currentTitle?.startsWith(HARNESS_TITLE_MARKER)) return { tagged: true }
    await client.query(
      'UPDATE conversations SET title = $2 WHERE id = $1',
      [conversationId, `${HARNESS_TITLE_MARKER} ${currentTitle ?? '(untitled)'}`],
    )
    return { tagged: true }
  } catch (err) {
    return { tagged: false, error: String(err) }
  } finally {
    await client.end().catch(() => {})
  }
}

interface ParsedSseEvent {
  type: string
  raw: unknown
  receivedAtMs: number
}

async function main() {
  const args = parseArgs(process.argv.slice(2))

  if (args.chartId === REAL_NATIVE_CANONICAL_CHART_ID && !args.chartIdExplicit) {
    // Structurally unreachable (the default is always the synthetic chart),
    // kept as a defense-in-depth assertion in case the default constant above
    // is ever edited carelessly.
    throw new Error('Refusing to default to the real native\'s canonical chart. This should be unreachable.')
  }
  if (args.chartId === REAL_NATIVE_CANONICAL_CHART_ID && args.chartIdExplicit) {
    console.error(`[ask] WARNING: --chart-id explicitly set to the REAL NATIVE's canonical chart (${REAL_NATIVE_CANONICAL_CHART_ID}). Proceeding because this was an explicit, deliberate choice, not a default.`)
  }

  mkdirSync(OUT_DIR, { recursive: true })

  console.error(`[ask] minting fresh session cookie for uid=${PROBE_UID} …`)
  const cookie = await mintSessionCookie(args.serviceUrl)

  const turnId = randomUUID()
  const events: ParsedSseEvent[] = []
  const startedAtMs = Date.now()
  let partial = true
  let terminalStatus: string | null = null
  let conversationId: string | null = args.conversationId ?? null
  let assistantMessageId: string | null = null
  const blocks: Array<{ blockId: string; kind: string | null; role: string | null }> = []
  let prose = ''

  console.error(`[ask] POST ${args.serviceUrl}/api/pariprashna — chart=${args.chartId}${args.chartIdExplicit ? ' (explicit)' : ' (synthetic default)'}`)

  let resp: Response
  try {
    resp = await fetch(`${args.serviceUrl}/api/pariprashna`, {
      method: 'POST',
      headers: { 'content-type': 'application/json', cookie: `__session=${cookie}` },
      body: JSON.stringify({
        chartId: args.chartId,
        conversationId: args.conversationId,
        reading_depth: 'auto',
        length_tier: 'standard',
        messages: [{ id: `${turnId}-user`, role: 'user', parts: [{ type: 'text', text: args.question }] }],
      }),
    })
  } catch (err) {
    writeResult({ turnId, args, events, partial: true, terminalStatus: 'network_error', conversationId, assistantMessageId, blocks, prose, startedAtMs, error: String(err) })
    console.error(`[ask] network error: ${err}`)
    process.exit(1)
  }

  if (!resp.ok || !resp.body) {
    const bodyText = await resp.text().catch(() => '<unreadable>')
    writeResult({ turnId, args, events, partial: true, terminalStatus: `http_${resp.status}`, conversationId, assistantMessageId, blocks, prose, startedAtMs, error: `HTTP ${resp.status}: ${bodyText}` })
    console.error(`[ask] HTTP ${resp.status}: ${bodyText}`)
    process.exit(1)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const frames = buffer.split('\n\n')
      buffer = frames.pop() ?? ''
      for (const frame of frames) {
        const dataLine = frame.split('\n').find((l) => l.startsWith('data: '))
        if (!dataLine) continue
        let parsed: any
        try {
          parsed = JSON.parse(dataLine.slice('data: '.length))
        } catch {
          continue
        }
        events.push({ type: parsed.type, raw: parsed, receivedAtMs: Date.now() - startedAtMs })

        if (parsed.type === 'block.commit') {
          // Wire field names are snake_case (block_id/text), NOT the client
          // reducer's transformed camelCase (blockId/html) — confirmed by
          // inspecting a real captured event, not assumed from the reducer type.
          blocks.push({ blockId: parsed.block_id, kind: parsed.kind ?? null, role: parsed.role ?? null })
          if (typeof parsed.text === 'string') prose += (prose ? '\n\n' : '') + parsed.text
        }
        if (parsed.type === 'turn.commit') {
          conversationId = parsed.conversation_id ?? conversationId
          assistantMessageId = parsed.message_id ?? assistantMessageId
        }
        if (parsed.type === 'turn.close') {
          terminalStatus = parsed.status
          partial = parsed.status !== 'ok'
        }
        if (parsed.type === 'error') {
          terminalStatus = terminalStatus ?? 'stream_error'
        }
      }
    }
  } catch (err) {
    console.error(`[ask] stream read error: ${err}`)
  }

  if (terminalStatus === null) {
    // Stream ended without a turn.close — genuinely partial/truncated.
    terminalStatus = 'truncated_no_close'
    partial = true
  }

  let harnessTag: { tagged: boolean; error?: string } | null = null
  if (conversationId) {
    console.error(`[ask] tagging conversation ${conversationId} as harness-origin …`)
    harnessTag = await tagConversationAsHarness(conversationId)
    if (!harnessTag.tagged) console.error(`[ask] WARNING: harness tag failed (non-fatal): ${harnessTag.error}`)
  }

  const outPath = writeResult({ turnId, args, events, partial, terminalStatus, conversationId, assistantMessageId, blocks, prose, startedAtMs, harnessTag })
  console.error(`[ask] wrote ${outPath} (partial=${partial}, status=${terminalStatus}, ${events.length} events, ${blocks.length} blocks)`)
  if (partial) process.exit(1)
}

function writeResult(r: {
  turnId: string
  args: Args
  events: ParsedSseEvent[]
  partial: boolean
  terminalStatus: string | null
  conversationId: string | null
  assistantMessageId: string | null
  blocks: Array<{ blockId: string; kind: string | null; role: string | null }>
  prose: string
  startedAtMs: number
  error?: string
  harnessTag?: { tagged: boolean; error?: string } | null
}): string {
  const outPath = join(OUT_DIR, `${r.turnId}.json`)
  const record = {
    turn_id: r.turnId,
    question: r.args.question,
    chart_id: r.args.chartId,
    chart_id_explicit: r.args.chartIdExplicit,
    conversation_id: r.conversationId,
    assistant_message_id: r.assistantMessageId,
    partial: r.partial,
    terminal_status: r.terminalStatus,
    error: r.error ?? null,
    harness_tag: r.harnessTag ?? null,
    total_ms: Date.now() - r.startedAtMs,
    event_count: r.events.length,
    blocks: r.blocks,
    prose: r.prose,
    events: r.events,
    written_at: new Date().toISOString(),
  }
  writeFileSync(outPath, JSON.stringify(record, null, 2))
  return outPath
}

main().catch((err) => {
  console.error('[ask] fatal:', err)
  process.exit(1)
})
