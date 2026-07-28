/**
 * SAMĪKṢĀ digest journal — PB-3 (SAMĪKṢĀ) lane L-4.
 *
 * Per-day idempotency for the consolidated digest: "has a digest already been sent for the
 * `as_of` date D?" The window-close TRANSITIONS are idempotent on their own (a re-run finds no
 * `open` row whose window has passed, because the first run already moved them to
 * `window_closed`). The DIGEST send is NOT self-idempotent — the closing-soon section is a
 * derived condition that re-detects the same rows every run — so it needs an explicit
 * sent-marker. This journal is that marker.
 *
 * WHY A FILE (not a DB table): lane L-4's `may_touch` grant deliberately excludes
 * `platform/supabase/migrations/**` (migrations are lane L-1's charge). A dedicated
 * `samiksha_job_runs` table would be the production-grade store, but adding it here would
 * breach the scope boundary. The file-based journal is the in-grant mechanism: real, testable,
 * and injectable. Its one honest limitation — a fresh ephemeral CI runner does not carry the
 * marker between separate invocations — is documented in the workflow and REPORT; it does not
 * affect the acceptance criterion (two runs of the same `--as-of` in a persistent environment
 * send exactly one digest), which the integration test proves against the real FileDigestJournal.
 */

import { promises as fs } from 'fs'
import path from 'path'

export interface DigestSentRecord {
  as_of: string
  sent_at: string
  closed_count: number
  closing_soon_count: number
  transport_mode: string
  real_delivery: boolean
}

export interface DigestJournal {
  /** True iff a digest has already been recorded as sent for this `as_of` date. */
  hasSent(asOf: string): Promise<boolean>
  /** Record that a digest was sent for this `as_of` date. Idempotent (overwrite is fine). */
  markSent(asOf: string, record: DigestSentRecord): Promise<void>
}

const AS_OF_RE = /^\d{4}-\d{2}-\d{2}$/

function assertAsOf(asOf: string): void {
  if (!AS_OF_RE.test(asOf)) {
    throw new Error(`DigestJournal: as_of must be ISO yyyy-mm-dd, got "${asOf}"`)
  }
}

/**
 * Default production journal: one JSON marker file per `as_of` date under a state directory.
 * The state dir defaults to `SAMIKSHA_STATE_DIR` env or `<cwd>/.samiksha-state` (gitignored).
 */
export class FileDigestJournal implements DigestJournal {
  private readonly dir: string
  constructor(stateDir?: string) {
    this.dir =
      stateDir ?? process.env['SAMIKSHA_STATE_DIR'] ?? path.join(process.cwd(), '.samiksha-state')
  }

  private file(asOf: string): string {
    return path.join(this.dir, `digest-${asOf}.json`)
  }

  async hasSent(asOf: string): Promise<boolean> {
    assertAsOf(asOf)
    try {
      await fs.access(this.file(asOf))
      return true
    } catch {
      return false
    }
  }

  async markSent(asOf: string, record: DigestSentRecord): Promise<void> {
    assertAsOf(asOf)
    await fs.mkdir(this.dir, { recursive: true })
    await fs.writeFile(this.file(asOf), JSON.stringify(record, null, 2), 'utf8')
  }
}

/** In-memory journal for unit tests (no filesystem). */
export class InMemoryDigestJournal implements DigestJournal {
  private readonly seen = new Map<string, DigestSentRecord>()
  async hasSent(asOf: string): Promise<boolean> {
    assertAsOf(asOf)
    return this.seen.has(asOf)
  }
  async markSent(asOf: string, record: DigestSentRecord): Promise<void> {
    assertAsOf(asOf)
    this.seen.set(asOf, record)
  }
}
