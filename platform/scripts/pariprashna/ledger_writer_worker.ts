/**
 * NO-LEAKAGE arm-3 — THE out-of-process ledger writer.
 * Lane G1-C · PPR-31 arm 3 · TA §14.10 arm 3.
 *
 *   "The ledger writer runs outside the synthesis process and holds the only
 *    write role."
 *
 * This process is that writer. It is the ONLY thing that should ever connect as
 * `role_ledger_write`, and after the role cutover it is the only thing in the
 * system that CAN write `brahma_mimamsa_prediction_ledger` — migration 576
 * revokes INSERT/UPDATE/DELETE on it from `role_web_serve`, `role_orchestrator`
 * and `role_jobs` alike.
 *
 * ── HOW IT CONNECTS ──────────────────────────────────────────────────────────
 * `LEDGER_WRITER_DATABASE_URL`, and nothing else. Deliberately NOT
 * `DATABASE_URL`, and deliberately not `@/lib/db/client`:
 *   · a separate variable means this process cannot accidentally inherit the
 *     serving credential from an ambient env — the wall would be undone by a
 *     convenience default;
 *   · not importing the app's pool keeps this out of the Next.js module graph,
 *     which is what "out of process" has to mean concretely.
 *
 * ── RUNNING IT ───────────────────────────────────────────────────────────────
 *   LEDGER_WRITER_DATABASE_URL="postgres://<user granted role_ledger_write>@host/db" \
 *     npx tsx platform/scripts/pariprashna/ledger_writer_worker.ts --once
 *
 *   --once           drain once and exit (the scheduled-task shape, matching
 *                    how samiksha-daily.yml already runs its sweeper)
 *   --interval <ms>  poll continuously (the long-running-worker shape)
 *   --limit <n>      max intents per drain (default 100)
 *
 * No deployment manifest is added by this lane. Wiring it into a schedule is part
 * of the cutover, not part of shipping it dark:
 * 00_ARCHITECTURE/briefs/pariprashna_swarm/G1_C_ROLES_RLS_CUTOVER_RUNBOOK_v1_0.md
 *
 * ── EXIT CODES ───────────────────────────────────────────────────────────────
 *   0  drained cleanly (including "nothing to do")
 *   1  could not start (no credential, cannot connect)
 *   2  drained, but at least one intent failed to apply — a real, visible signal
 *      rather than a green exit over a failure count nobody reads.
 */

import { Pool } from 'pg'

import { drainOutbox } from '../../src/lib/pariprashna/arm3/drain'
import { outboxDepth, type OutboxDb } from '../../src/lib/pariprashna/arm3/outbox'

interface Args {
  once: boolean
  intervalMs: number
  limit: number
}

function parseArgs(argv: string[]): Args {
  const intervalIdx = argv.indexOf('--interval')
  const limitIdx = argv.indexOf('--limit')
  return {
    once: argv.includes('--once') || intervalIdx === -1,
    intervalMs: intervalIdx === -1 ? 30_000 : Number(argv[intervalIdx + 1]),
    limit: limitIdx === -1 ? 100 : Number(argv[limitIdx + 1]),
  }
}

function log(msg: string, extra?: Record<string, unknown>): void {
  const stamp = new Date().toISOString()
  console.log(`[arm3-ledger-writer ${stamp}] ${msg}${extra ? ' ' + JSON.stringify(extra) : ''}`)
}

async function drainOnce(db: OutboxDb, limit: number): Promise<number> {
  const before = await outboxDepth(db)
  const result = await drainOutbox(db, limit)

  if (result.claimed === 0) {
    log('nothing pending', { pending: before.pending, failed: before.failed })
    return 0
  }

  log('drain complete', {
    claimed: result.claimed,
    applied: result.applied,
    failed: result.failed,
  })

  // Every failure printed individually. A count alone would let a persistent
  // poison message hide behind a shrinking-looking number.
  for (const e of result.errors) {
    console.error(
      `[arm3-ledger-writer] intent ${e.outbox_id} (${e.op}) FAILED: ${e.message}`,
    )
  }

  return result.failed
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2))

  const url = process.env.LEDGER_WRITER_DATABASE_URL
  if (!url) {
    console.error(
      'ARM3_NO_CREDENTIAL: LEDGER_WRITER_DATABASE_URL is not set. This worker connects on its ' +
        'own variable on purpose — it must NOT inherit DATABASE_URL, because the whole point of ' +
        'arm-3 is that the serving credential and the ledger-write credential are different ' +
        'things. Provision a login user granted role_ledger_write and point this at it.',
    )
    process.exit(1)
  }

  const pool = new Pool({ connectionString: url, max: 2 })
  const db: OutboxDb = {
    query: (sql, params) =>
      pool.query(sql, params as unknown[]).then((r) => ({
        rows: r.rows as never[],
        rowCount: r.rowCount,
      })),
  }

  // Report which role we actually hold. If this says `amjis_app`, the wall is not
  // in place regardless of what any flag claims — so it is printed every run
  // rather than assumed.
  try {
    const { rows } = await pool.query<{ role: string }>('SELECT current_user AS role')
    log('connected', { current_user: rows[0]?.role })
  } catch (err) {
    console.error('ARM3_CONNECT_FAILED:', err)
    await pool.end()
    process.exit(1)
  }

  let failures = 0
  if (args.once) {
    failures = await drainOnce(db, args.limit)
    await pool.end()
    process.exit(failures > 0 ? 2 : 0)
  }

  log('polling', { intervalMs: args.intervalMs, limit: args.limit })
  let stopping = false
  const stop = () => {
    stopping = true
  }
  process.on('SIGINT', stop)
  process.on('SIGTERM', stop)

  while (!stopping) {
    try {
      await drainOnce(db, args.limit)
    } catch (err) {
      console.error('[arm3-ledger-writer] drain cycle failed', err)
    }
    await new Promise((r) => setTimeout(r, args.intervalMs))
  }

  log('shutting down')
  await pool.end()
}

// Guard: only run when invoked directly, so a test may import this file.
if (process.env.NODE_ENV !== 'test') {
  void main()
}
