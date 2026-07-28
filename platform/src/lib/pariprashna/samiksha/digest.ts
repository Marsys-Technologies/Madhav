/**
 * SAMĪKṢĀ digest — PB-3 (SAMĪKṢĀ) lane L-4.
 *
 * The consolidated daily digest: its payload shape, its plain-text rendering, and the
 * transport seam through which it is delivered. Pure/isomorphic on purpose (no `pg`, no
 * `server-only`) so the render + transport can be unit-tested with zero DB dependency.
 *
 * TRANSPORT (wave-ruling W-5): this codebase has NO email transport — there is no mailer
 * dependency (no nodemailer/sendgrid/ses/resend in package.json) and no live
 * `/api/internal/send-email` route (only `alerts/dispatch.ts` *references* such a route, which
 * does not exist). Per W-5 the job + digest are still fully built and tested, and the actual
 * send is STUBBED to LOG-ONLY. `LogOnlyTransport` NEVER claims a real email was delivered
 * (`realDelivery: false`); it logs a clearly-marked stub block. When a real transport later
 * lands, implement `DigestTransport` against it and inject it — nothing else changes.
 */

import type { LedgerRow } from './schema'

// ── Digest item + payload ─────────────────────────────────────────────────────

/** One prediction line in the digest — a projection of the ledger row's public fields. */
export interface DigestItem {
  id: string
  chart_id: string
  claim_text: string
  domain: string | null
  /** Raw daterange literal, e.g. "[2026-01-01,2026-12-31)", or null. */
  window: string | null
  /** Raw numrange literal, e.g. "[0.6,0.8)", or null. */
  confidence: string | null
  direction: string | null
  /** ISO yyyy-mm-dd window end (exclusive upper of the daterange), or null. */
  window_end: string | null
}

export interface DigestPayload {
  /** The simulated/real "now" the run was computed against (ISO yyyy-mm-dd). */
  as_of: string
  /** Rows transitioned open → window_closed THIS run — now awaiting resolution (L-3 Resolve). */
  closed: DigestItem[]
  /** Rows still open whose window closes within `closing_soon_days` — a derived, non-persisted flag. */
  closing_soon: DigestItem[]
  /** The runway (days) used for the closing-soon detection. */
  closing_soon_days: number
  /** When this payload object was assembled (real wall-clock ISO timestamp). */
  generated_at: string
}

/** A digest is worth sending only when it carries at least one item in either section. */
export function digestIsEmpty(p: DigestPayload): boolean {
  return p.closed.length === 0 && p.closing_soon.length === 0
}

/** Project a ledger row down to the fields the digest surfaces. `window_end` is decoded here. */
export function toDigestItem(row: LedgerRow): DigestItem {
  return {
    id: row.id,
    chart_id: row.chart_id,
    claim_text: row.claim_text,
    domain: row.domain,
    window: row.window,
    confidence: row.confidence,
    direction: row.direction,
    window_end: upperDateOfRange(row.window),
  }
}

/**
 * Decode the exclusive upper bound (yyyy-mm-dd) from a Postgres daterange literal such as
 * "[2026-07-01,2027-01-01)" → "2027-01-01". Returns null for null/empty/unbounded ranges.
 */
export function upperDateOfRange(literal: string | null): string | null {
  if (!literal) return null
  // daterange literal: (lower_bracket)lower,upper(upper_bracket) — upper may be empty (unbounded).
  const m = literal.match(/^[[(]\s*[^,]*\s*,\s*([^)\]]*)\s*[)\]]$/)
  const upper = m?.[1]?.trim()
  return upper && upper.length > 0 ? upper : null
}

// ── Rendering ─────────────────────────────────────────────────────────────────

export interface RenderedDigest {
  subject: string
  text: string
}

function renderItemLine(it: DigestItem): string {
  const bits: string[] = []
  if (it.domain) bits.push(it.domain)
  if (it.window) bits.push(`window ${it.window}`)
  if (it.confidence) bits.push(`p=${it.confidence}`)
  if (it.direction) bits.push(it.direction)
  const meta = bits.length ? `  [${bits.join(' · ')}]` : ''
  return `  • ${it.claim_text}${meta}\n    (id ${it.id})`
}

/**
 * Render the digest to a plain-text subject + body. Deterministic given the payload (item
 * order is the caller's; this function does not re-sort), so a golden test can assert on it.
 */
export function renderDigest(p: DigestPayload): RenderedDigest {
  const subject =
    `[Samīkṣā] ${p.closed.length} window(s) closed, ${p.closing_soon.length} closing soon — as of ${p.as_of}`

  const lines: string[] = []
  lines.push(`SAMĪKṢĀ prediction digest — as of ${p.as_of}`)
  lines.push(`Generated ${p.generated_at}`)
  lines.push('')

  lines.push(`── Windows closed today (${p.closed.length}) — awaiting resolution ──`)
  if (p.closed.length === 0) {
    lines.push('  (none)')
  } else {
    for (const it of p.closed) lines.push(renderItemLine(it))
  }
  lines.push('')

  lines.push(`── Closing soon within ${p.closing_soon_days}d (${p.closing_soon.length}) ──`)
  if (p.closing_soon.length === 0) {
    lines.push('  (none)')
  } else {
    for (const it of p.closing_soon) lines.push(renderItemLine(it))
  }
  lines.push('')
  lines.push('Resolve closed predictions on the Samīkṣā review tab (Resolve section).')

  return { subject, text: lines.join('\n') }
}

// ── Transport seam ─────────────────────────────────────────────────────────────

export interface DigestMessage {
  subject: string
  text: string
  /** Structured payload carried alongside the rendered text (for a future real transport). */
  payload: DigestPayload
}

export interface TransportResult {
  ok: boolean
  /** Transport identity, e.g. 'log-only-stub' or (future) 'smtp' / 'sendgrid'. */
  mode: string
  /**
   * Whether a real external delivery (an actual email) occurred. FALSE for the W-5 stub — it
   * is NEVER set true unless a message genuinely left the system.
   */
  realDelivery: boolean
  /** Human-readable note (e.g. the W-5 stub disclosure). */
  note?: string
}

export interface DigestTransport {
  send(msg: DigestMessage): Promise<TransportResult>
}

/**
 * W-5 stub transport: logs the digest, clearly marked as a stub, and returns
 * `realDelivery: false`. It does NOT fake a send. This is the default until a real email
 * transport exists in the codebase.
 */
export class LogOnlyTransport implements DigestTransport {
  constructor(private readonly logger: Pick<Console, 'info'> = console) {}

  async send(msg: DigestMessage): Promise<TransportResult> {
    const banner =
      '════════════════════════════════════════════════════════════════════\n' +
      '[samiksha:digest] STUB TRANSPORT (W-5) — LOG-ONLY, NOT EMAILED.\n' +
      'No email transport is configured in this codebase; this digest was\n' +
      'logged, not delivered. Wire a real DigestTransport to actually send.\n' +
      '════════════════════════════════════════════════════════════════════'
    this.logger.info(`${banner}\nSubject: ${msg.subject}\n\n${msg.text}\n`)
    return {
      ok: true,
      mode: 'log-only-stub',
      realDelivery: false,
      note: 'W-5: no email transport present; digest logged only, not emailed.',
    }
  }
}

/** A transport that records what it was asked to send — for tests to assert send-count. */
export class RecordingTransport implements DigestTransport {
  readonly sent: DigestMessage[] = []
  constructor(private readonly delegate?: DigestTransport) {}
  async send(msg: DigestMessage): Promise<TransportResult> {
    this.sent.push(msg)
    return (
      (await this.delegate?.send(msg)) ?? {
        ok: true,
        mode: 'recording',
        realDelivery: false,
        note: 'test recording transport',
      }
    )
  }
}
