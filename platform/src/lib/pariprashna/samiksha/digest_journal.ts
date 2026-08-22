/**
 * SAMĪKṢĀ digest journal — PB-3 (SAMĪKṢĀ) lane L-4, elevated to a real DB store by P4-I (DD-21,
 * `PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md` §10.2/§10.5).
 *
 * Per-day idempotency for the consolidated digest: "has a digest already been sent for the
 * `as_of` date D?" The window-close TRANSITIONS are idempotent on their own (a re-run finds no
 * `open` row whose window has passed, because the first run already moved them to
 * `window_closed`). The DIGEST send is NOT self-idempotent — the closing-soon section is a
 * derived condition that re-detects the same rows every run — so it needs an explicit
 * sent-marker. This journal is that marker, AND (since P4-I) the durable content record.
 *
 * HISTORY (why a file existed first): lane L-4's original `may_touch` grant deliberately
 * excluded `platform/supabase/migrations/**` (migrations were lane L-1's charge), so
 * `FileDigestJournal` (a per-`as_of` JSON marker file under `.samiksha-state/`, gitignored) was
 * the in-grant mechanism at the time — real, testable, and injectable, but storing COUNTS ONLY
 * (never the digest's actual subject/text/payload) and not queryable or joinable to a chart or a
 * prediction. P4-I's `may_touch` includes `platform/src/lib/**` and migration 588
 * (`588_samiksha_digest_journal.sql`) was reserved and authored for exactly this: `DbDigestJournal`
 * below is the production-grade store the file's own header said was owed. `FileDigestJournal`
 * and `InMemoryDigestJournal` are KEPT (offline/no-DB dev fallback and unit tests respectively) —
 * only the DEFAULT wired by `daily_job.ts` moves to `DbDigestJournal`.
 */

import { promises as fs } from 'fs'
import path from 'path'
import { query as sharedQuery } from '@/lib/db/client'
import type { LedgerExecutor } from './writer'
import type { DigestPayload } from './digest'

export interface DigestSentRecord {
  as_of: string
  sent_at: string
  closed_count: number
  closing_soon_count: number
  transport_mode: string
  real_delivery: boolean
  /** The rendered digest subject line (`renderDigest().subject`). Required since P4-I — a
   *  journal that cannot answer "what did the digest say" is a marker, not a record. */
  subject: string
  /** The rendered digest body (`renderDigest().text`). See `subject` above. */
  body_text: string
  /** The full structured payload the digest was rendered from — carries item-level `chart_id`
   *  and prediction-ledger `id`s, so a DB-backed journal row is joinable to a chart or a
   *  prediction, not just a text blob. */
  payload: DigestPayload
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
 * Offline/no-DB dev fallback journal (NOT the production default since P4-I — see
 * `DbDigestJournal` below, which `daily_job.ts` now wires by default): one JSON marker file per
 * `as_of` date under a state directory. The state dir defaults to `SAMIKSHA_STATE_DIR` env or
 * `<cwd>/.samiksha-state` (gitignored). Reachable in production only via the CLI's explicit
 * `--file-journal` opt-in (`scripts/samiksha/daily_job.ts`).
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

// ── DB-backed journal (P4-I, DD-21) ─────────────────────────────────────────────

/** Backs migration 588 (`588_samiksha_digest_journal.sql`). Table name is FIXED by that
 *  migration's own header — do not rename without a corrective migration. */
export const DIGEST_JOURNAL_TABLE = 'pariprashna_samiksha_digest_journal'

/** A durable digest journal row as read back from the DB — `DigestSentRecord` plus the
 *  identity/audit columns the table adds. */
export interface DigestJournalRow extends DigestSentRecord {
  id: number
  run_chart_id: string | null
  created_at: string
}

const defaultExecutor: LedgerExecutor = <T,>(sql: string, params?: unknown[]) =>
  sharedQuery(sql, params as unknown[]).then((r) => ({ rows: r.rows as T[], rowCount: r.rowCount }))

/**
 * Production journal (P4-I default): one row per `as_of` date in
 * `pariprashna_samiksha_digest_journal` (migration 588). Real, queryable, joinable to a chart or
 * a prediction via `payload`'s item-level ids — retires "the digest only ever lands in a log
 * line" (the defect DD-21 names).
 *
 * DB access goes through an injectable `LedgerExecutor` (same DI seam `writer.ts`/`daily_job.ts`
 * already use), defaulting to the shared pool, so this class can be driven against a real
 * throwaway Postgres with migration 588 actually applied in a test — not an in-memory mock of
 * the journal agreeing with itself (the same PB-2 false-confidence-gate lesson `writer.ts`
 * documents).
 *
 * `markSent` is an UPSERT keyed on `(as_of, run_chart_id)` (the table's own unique constraint,
 * `NULLS NOT DISTINCT` so the common all-charts row — `run_chart_id IS NULL` — still collides
 * with itself across re-runs) — a re-run for the same `(as_of, run_chart_id)` pair overwrites,
 * matching this interface's own documented contract ("Idempotent (overwrite is fine)"). Keying
 * on `as_of` ALONE was the original (pre-apply) design and was wrong: two `--chart`-scoped runs
 * on the same `as_of` would then collide with EACH OTHER — the first chart's row would make
 * `hasSent(asOf)` read true for every other chart too, silently swallowing their digests. See
 * migration 588's header for the reproduction. This class was fixed together with the migration
 * before either ever went live.
 */
export class DbDigestJournal implements DigestJournal {
  constructor(
    private readonly exec: LedgerExecutor = defaultExecutor,
    /** Optional chart scope, mirrors `runDailyJob`'s own `--chart` option. Stored in
     *  `run_chart_id`; NULL (the default) means "swept all charts". */
    private readonly chartId?: string,
  ) {}

  /** `hasSent` is scoped to THIS journal's own chart scope (`this.chartId`, NULL = all-charts),
   *  using NULL-safe equality (`IS NOT DISTINCT FROM`) so an all-charts journal instance
   *  (`chartId` undefined) only ever matches the all-charts row, never a `--chart`-scoped row
   *  for the same `as_of` and vice versa. Pre-fix this query ignored `run_chart_id` entirely — a
   *  chart-A run's row made `hasSent(asOf)` read true for chart B too, silently swallowing
   *  chart B's digest (the bug the migration 588 unique-key fix and this scoping fix close
   *  together; neither alone is sufficient). */
  async hasSent(asOf: string): Promise<boolean> {
    assertAsOf(asOf)
    const { rows } = await this.exec<{ exists: boolean }>(
      `SELECT EXISTS(
         SELECT 1 FROM ${DIGEST_JOURNAL_TABLE}
          WHERE as_of = $1::date AND run_chart_id IS NOT DISTINCT FROM $2::uuid
       ) AS exists`,
      [asOf, this.chartId ?? null],
    )
    return rows[0]?.exists === true
  }

  async markSent(asOf: string, record: DigestSentRecord): Promise<void> {
    assertAsOf(asOf)
    await this.exec(
      `INSERT INTO ${DIGEST_JOURNAL_TABLE}
         (as_of, run_chart_id, sent_at, closed_count, closing_soon_count, transport_mode,
          real_delivery, subject, body_text, payload)
       VALUES ($1::date, $2::uuid, $3::timestamptz, $4, $5, $6, $7, $8, $9, $10::jsonb)
       ON CONFLICT (as_of, run_chart_id) DO UPDATE SET
         sent_at            = EXCLUDED.sent_at,
         closed_count       = EXCLUDED.closed_count,
         closing_soon_count = EXCLUDED.closing_soon_count,
         transport_mode     = EXCLUDED.transport_mode,
         real_delivery      = EXCLUDED.real_delivery,
         subject            = EXCLUDED.subject,
         body_text          = EXCLUDED.body_text,
         payload            = EXCLUDED.payload`,
      [
        asOf,
        this.chartId ?? null,
        record.sent_at,
        record.closed_count,
        record.closing_soon_count,
        record.transport_mode,
        record.real_delivery,
        record.subject,
        record.body_text,
        JSON.stringify(record.payload),
      ],
    )
  }

  /** Read a journal row back, for tests, ops tooling, and the DD-21 written-and-read-back proof.
   *  Scoped to THIS journal's own chart scope, same NULL-safe rule as `hasSent`. Returns null
   *  when no digest has been journalled for `(asOf, this.chartId)`. */
  async readByAsOf(asOf: string): Promise<DigestJournalRow | null> {
    assertAsOf(asOf)
    const { rows } = await this.exec<DigestJournalRow>(
      `SELECT id, as_of::text AS as_of, run_chart_id, sent_at::text AS sent_at, closed_count,
              closing_soon_count, transport_mode, real_delivery, subject, body_text, payload,
              created_at::text AS created_at
         FROM ${DIGEST_JOURNAL_TABLE}
        WHERE as_of = $1::date AND run_chart_id IS NOT DISTINCT FROM $2::uuid`,
      [asOf, this.chartId ?? null],
    )
    return rows[0] ?? null
  }
}
