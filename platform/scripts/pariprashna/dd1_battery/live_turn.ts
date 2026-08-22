/**
 * dd1_battery/live_turn.ts — drive ONE real turn against a live
 * `/api/pariprashna` target and return the full ordered wire transcript.
 *
 * The auth seam (mint a fresh, single-use Firebase `__session` cookie for
 * `probe-service-account` on every invocation) is the same one designed and
 * documented at length in `platform/scripts/probe/ask.ts` — read that file's
 * STEP 1 header for the credential investigation this rests on. It is
 * re-expressed here rather than imported because `ask.ts` is a top-level
 * script that runs `main()` on import and has no exported surface; extracting
 * it into a shared module would mean editing `ask.ts` itself, which several
 * other lanes depend on unchanged tonight. FOLLOW-UP (filed as a finding, not
 * done here): fold `ask.ts` onto this module so one auth implementation exists.
 *
 * SAFETY: the synthetic chart is the ONLY default and the real native's
 * canonical chart is REFUSED outright — unlike `ask.ts`, which permits it
 * behind an explicit flag. The battery has no legitimate reason to ever touch
 * the native's chart, so the escape hatch does not exist (COMMON_BRIEF
 * hard-never; charter §9).
 *
 * PRIMARY GATE LOCATION (fixed post-#1501 refutation): the refusal below in
 * `driveTurn()` is defense-in-depth ONLY. The primary, binding gate is
 * `refuseRealNativeChart()` in `index.ts`'s `parseArgs()` — it runs before
 * ANY lane (prose/browser/fixture) is dispatched, for every flag combination.
 * The original version of this module claimed "the escape hatch simply does
 * not exist here" as if that were true of the whole battery; it was true only
 * of this one function — `browser_lane.ts` built its target URL from the raw
 * `--chart-id` argument with no guard at all, so `--no-live --chart-id
 * <native>` (which never calls `driveTurn()`) drove a real turn on the
 * native's real chart. Do not reason about battery-wide safety from this
 * module alone; the binding gate is in `index.ts`.
 */
import { execSync } from 'node:child_process'
import { randomUUID } from 'node:crypto'
import { initializeApp, getApps, cert } from 'firebase-admin/app'
import { getAuth } from 'firebase-admin/auth'

export const SYNTHETIC_TEST_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
export const REAL_NATIVE_CANONICAL_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const PROBE_UID = process.env.PROBE_UID ?? 'probe-service-account'

export interface WireEvent {
  type: string
  raw: Record<string, unknown>
  /** ms since the POST was dispatched. */
  atMs: number
}

export interface CommittedBlockRecord {
  blockId: string
  kind: string | null
  role: string | null
  text: string
  atMs: number
  /** index into `events` */
  seqIndex: number
}

export interface DrivenTurn {
  turnId: string
  question: string
  chartId: string
  conversationId: string | null
  assistantMessageId: string | null
  partial: boolean
  terminalStatus: string | null
  error: string | null
  totalMs: number
  /** ms from POST to the first block.delta carrying prose — the M4 quantity. */
  firstProseDeltaMs: number | null
  events: WireEvent[]
  blocks: CommittedBlockRecord[]
  /** Concatenated delivered reader prose (committed blocks only). */
  prose: string
}

function envOrSecret(envVar: string, secretName: string): string {
  const fromEnv = process.env[envVar]
  if (fromEnv) return fromEnv
  const value = execSync(
    `gcloud secrets versions access latest --secret=${secretName} --project=madhav-astrology`,
    { encoding: 'utf8' },
  ).trim()
  if (!value) throw new Error(`Secret Manager:${secretName} returned empty value`)
  return value
}

function envOrFirebaseSdkConfig(envVar: string): string {
  const fromEnv = process.env[envVar]
  if (fromEnv) return fromEnv
  const raw = execSync('firebase apps:sdkconfig WEB --project=madhav-astrology', { encoding: 'utf8' })
  const config = JSON.parse(raw) as { apiKey?: string }
  if (!config.apiKey) throw new Error('firebase apps:sdkconfig WEB returned no apiKey field')
  return config.apiKey
}

/** Mint a FRESH single-use `__session` cookie. Never cached. */
export async function mintSessionCookie(serviceUrl: string): Promise<string> {
  const credsRaw = envOrSecret('FIREBASE_ADMIN_CREDENTIALS', 'firebase-admin-credentials')
  const apiKey = envOrFirebaseSdkConfig('NEXT_PUBLIC_FIREBASE_API_KEY')
  const creds = JSON.parse(credsRaw) as Record<string, unknown>
  const app = getApps().length > 0 ? getApps()[0] : initializeApp({ credential: cert(creds as never) })
  const auth = getAuth(app)

  const customToken = await auth.createCustomToken(PROBE_UID)
  const fbResp = await fetch(
    `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${apiKey}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: customToken, returnSecureToken: true }),
    },
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
    throw new Error(
      `/api/auth/session returned ${sessResp.status}: ${await sessResp.text().catch(() => '<unreadable>')}`,
    )
  }
  const rawSetCookie =
    (sessResp.headers as unknown as { getSetCookie?: () => string[] }).getSetCookie?.() ??
    sessResp.headers.get('set-cookie') ??
    ''
  const setCookieStr = Array.isArray(rawSetCookie) ? rawSetCookie.join('\n') : String(rawSetCookie)
  const match = setCookieStr.match(/__session=([^;]+)/)
  if (!match) throw new Error(`__session cookie not found in Set-Cookie. Got: ${setCookieStr.slice(0, 200)}`)
  return match[1]
}

export interface DriveTurnOptions {
  serviceUrl: string
  cookie: string
  question: string
  chartId?: string
  conversationId?: string
  readingDepth?: string
  lengthTier?: string
}

/** Drive one real turn end-to-end and return the ordered wire transcript. */
export async function driveTurn(opts: DriveTurnOptions): Promise<DrivenTurn> {
  const chartId = opts.chartId ?? SYNTHETIC_TEST_CHART_ID
  if (chartId === REAL_NATIVE_CANONICAL_CHART_ID) {
    throw new Error(
      'dd1_battery refuses to run against the real native\'s canonical chart. ' +
        'The battery probes the synthetic chart only (COMMON_BRIEF hard-never).',
    )
  }

  const turnId = randomUUID()
  const events: WireEvent[] = []
  const blocks: CommittedBlockRecord[] = []
  const startedAtMs = Date.now()
  let firstProseDeltaMs: number | null = null
  let partial = true
  let terminalStatus: string | null = null
  let conversationId: string | null = opts.conversationId ?? null
  let assistantMessageId: string | null = null
  let prose = ''

  const base = {
    turnId,
    question: opts.question,
    chartId,
    conversationId,
    assistantMessageId,
    events,
    blocks,
    prose,
    firstProseDeltaMs,
  }

  let resp: Response
  try {
    resp = await fetch(`${opts.serviceUrl}/api/pariprashna`, {
      method: 'POST',
      headers: { 'content-type': 'application/json', cookie: `__session=${opts.cookie}` },
      body: JSON.stringify({
        chartId,
        conversationId: opts.conversationId,
        reading_depth: opts.readingDepth ?? 'auto',
        length_tier: opts.lengthTier ?? 'standard',
        messages: [{ id: `${turnId}-user`, role: 'user', parts: [{ type: 'text', text: opts.question }] }],
      }),
    })
  } catch (err) {
    return { ...base, partial: true, terminalStatus: 'network_error', error: String(err), totalMs: Date.now() - startedAtMs }
  }

  if (!resp.ok || !resp.body) {
    const bodyText = await resp.text().catch(() => '<unreadable>')
    return {
      ...base,
      partial: true,
      terminalStatus: `http_${resp.status}`,
      error: `HTTP ${resp.status}: ${bodyText.slice(0, 500)}`,
      totalMs: Date.now() - startedAtMs,
    }
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let streamError: string | null = null

  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const frames = buffer.split('\n\n')
      buffer = frames.pop() ?? ''
      for (const frame of frames) {
        const dataLine = frame.split('\n').find((l) => l.startsWith('data: '))
        if (!dataLine) continue
        let parsed: Record<string, unknown>
        try {
          parsed = JSON.parse(dataLine.slice('data: '.length)) as Record<string, unknown>
        } catch {
          continue
        }
        const atMs = Date.now() - startedAtMs
        events.push({ type: String(parsed.type), raw: parsed, atMs })

        if (parsed.type === 'block.delta' && typeof parsed.delta === 'string' && parsed.delta.length > 0) {
          if (firstProseDeltaMs === null) firstProseDeltaMs = atMs
        }
        if (parsed.type === 'block.commit') {
          const text = typeof parsed.text === 'string' ? parsed.text : ''
          blocks.push({
            blockId: String(parsed.block_id),
            kind: (parsed.kind as string) ?? null,
            role: (parsed.role as string) ?? null,
            text,
            atMs,
            seqIndex: events.length - 1,
          })
          if (text) prose += (prose ? '\n\n' : '') + text
        }
        if (parsed.type === 'turn.commit') {
          conversationId = (parsed.conversation_id as string) ?? conversationId
          assistantMessageId = (parsed.message_id as string) ?? assistantMessageId
        }
        if (parsed.type === 'turn.close') {
          terminalStatus = (parsed.status as string) ?? null
          partial = terminalStatus !== 'ok'
        }
        if (parsed.type === 'error' && terminalStatus === null) terminalStatus = 'stream_error'
      }
    }
  } catch (err) {
    streamError = String(err)
  }

  if (terminalStatus === null) {
    terminalStatus = 'truncated_no_close'
    partial = true
  }

  return {
    turnId,
    question: opts.question,
    chartId,
    conversationId,
    assistantMessageId,
    partial,
    terminalStatus,
    error: streamError,
    totalMs: Date.now() - startedAtMs,
    firstProseDeltaMs,
    events,
    blocks,
    prose,
  }
}
