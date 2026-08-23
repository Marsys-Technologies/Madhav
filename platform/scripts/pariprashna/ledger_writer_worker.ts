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
import { realpathSync } from 'fs'
import { resolve } from 'path'
import { fileURLToPath } from 'url'

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

/**
 * Is THIS module the process entrypoint, or was it merely imported by something else?
 *
 * Exported so the question has a real, directly-testable detector behind it rather than an
 * inline expression nothing can exercise (CLAUDE.md §N.8). It is also this module's FIRST
 * export — the old guard's comment invited a test to import this file while the file exported
 * nothing at all, so the invitation could only ever be taken up as a side-effect import.
 *
 * Compares the module's own URL against `process.argv[1]`, the path the runtime was told to
 * execute. Both sides are normalised through `realpathSync` where possible, so a symlinked
 * checkout, a `./`-prefixed spelling, or a `/tmp` → `/private/tmp` style realpath difference
 * does not make a direct run look like an import. Any failure to resolve either side answers
 * `false`: the safe direction is "assume imported", because a wrongly-false answer makes the
 * documented `npx tsx platform/scripts/pariprashna/ledger_writer_worker.ts --once` exit having
 * drained nothing — recoverable, and visible in `pariprashna_ledger_outbox`'s depth — while a
 * wrongly-true answer drains the outbox and writes `brahma_mimamsa_prediction_ledger` as an
 * import side effect, holding the only `role_ledger_write` credential while it does so.
 *
 * MIRRORED, NOT IMPORTED, from `scripts/migrate.ts` and `scripts/seed/asset_registry_seed.ts`,
 * which carry the same function. Deliberately a copy: Nirmāṇa ruling D-9 standing-instructs
 * agents not to import from `scripts/migrate.ts`, and this worker's whole design premise is that
 * it stays OUT of other module graphs (see the header — it does not import `@/lib/db/client`
 * either). Behaviour is intended to stay identical to those copies; each has its own tests.
 */
export function isDirectEntrypoint(moduleUrl: string, argv1: string | undefined): boolean {
  if (!argv1) return false
  let modulePath: string
  try {
    modulePath = fileURLToPath(moduleUrl)
  } catch {
    return false
  }
  const entryPath = resolve(argv1)
  if (modulePath === entryPath) return true
  try {
    return realpathSync(modulePath) === realpathSync(entryPath)
  } catch {
    return false
  }
}

// Guard: only execute when this module IS the entrypoint — never as an import side effect.
//
// This used to read `if (process.env.NODE_ENV !== 'test')` (Nirmāṇa WORK_QUEUE M0-T60,
// Standing Queue SQ-24; same defect class as ruling D-9 / finding F-2 in `scripts/migrate.ts`
// and M0-T15 in `scripts/seed/asset_registry_seed.ts`). An environment sentinel says nothing
// about how the module was loaded, and it was wrong in BOTH directions here:
//
//   · it RAN on import in any shell with NODE_ENV unset — every ordinary developer and agent
//     shell. `main()` opens a pool on the sole `role_ledger_write` credential, drains
//     `pariprashna_ledger_outbox` into `brahma_mimamsa_prediction_ledger`, and calls
//     `process.exit()`, so the import both mutated the ledger and killed its importer;
//   · it DID NOT RUN on the documented direct invocation whenever the surrounding environment
//     happened to export NODE_ENV=test — exiting 0 having printed nothing, so a scheduler would
//     have recorded a success over a drain that never happened.
//
// Note this is NOT the `IMPORT_ONLY !== '1'` contract the two CI gates use (M0-T50 / D-49,
// documented at `platform/scripts/audit/A3_env_matrix.md` Addendum A3.4). A gate's hazard is
// FAILING to run, so its safe default is RUN. A mutating worker's hazard is RUNNING, so its safe
// default is DO NOT RUN — A3.4 operator rule 5, applied here.
//
// Both directions are covered by
// `scripts/__tests__/ledger_writer_worker_entrypoint_guard.test.ts`.
if (isDirectEntrypoint(import.meta.url, process.argv[1])) {
  void main()
}
