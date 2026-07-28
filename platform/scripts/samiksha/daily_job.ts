/**
 * SAMĪKṢĀ consolidated daily job — CLI entry — PB-3 (SAMĪKṢĀ) lane L-4.
 *
 * ONE scheduled run (T-3): closes passed windows, flags closing-soon predictions, and
 * dispatches ONE consolidated digest (only when non-empty, per-day idempotent). See
 * src/lib/pariprashna/samiksha/daily_job.ts for the logic; this file is just argv + wiring.
 *
 * RUN (imports the server-only DB client, so the react-server condition is required):
 *   npx tsx --conditions=react-server scripts/samiksha/daily_job.ts [--as-of YYYY-MM-DD]
 *
 * Flags:
 *   --as-of YYYY-MM-DD      simulated clock ("now"); default = today (UTC). ESSENTIAL for tests.
 *   --chart <uuid>          restrict the sweep to one chart; default = all charts.
 *   --closing-soon-days N   runway for the closing-soon flag; default 14.
 *   --state-dir <path>      DigestJournal marker dir; default SAMIKSHA_STATE_DIR or ./.samiksha-state.
 *   --json                  print the machine-readable DailyJobResult as JSON.
 *
 * Transport is the W-5 LOG-ONLY stub (no email transport exists in this codebase); a real
 * digest is logged, never emailed. Exit code 0 on success, 1 on failure.
 */

import { runDailyJob } from '@/lib/pariprashna/samiksha/daily_job'
import { FileDigestJournal } from '@/lib/pariprashna/samiksha/digest_journal'
import { LogOnlyTransport } from '@/lib/pariprashna/samiksha/digest'

function argValue(argv: string[], flag: string): string | undefined {
  const i = argv.indexOf(flag)
  if (i === -1) return undefined
  const v = argv[i + 1]
  if (v === undefined || v.startsWith('--')) {
    throw new Error(`${flag} requires a value`)
  }
  return v
}

function todayUtcIso(): string {
  return new Date().toISOString().slice(0, 10)
}

async function main(): Promise<void> {
  const argv = process.argv.slice(2)
  const asOf = argValue(argv, '--as-of') ?? todayUtcIso()
  const chartId = argValue(argv, '--chart')
  const closingSoonRaw = argValue(argv, '--closing-soon-days')
  const stateDir = argValue(argv, '--state-dir')
  const asJson = argv.includes('--json')

  const closingSoonDays = closingSoonRaw === undefined ? 14 : Number(closingSoonRaw)

  console.info(
    `[samiksha:daily_job] start — as_of=${asOf} chart=${chartId ?? '(all)'} ` +
      `closing_soon_days=${closingSoonDays}`,
  )

  const result = await runDailyJob({
    asOf,
    chartId,
    closingSoonDays,
    journal: new FileDigestJournal(stateDir),
    transport: new LogOnlyTransport(),
  })

  if (asJson) {
    // Drop the (potentially large) digest payload's item arrays' verbosity but keep structure.
    console.info(JSON.stringify(result, null, 2))
  } else {
    const digestLine =
      result.digest_dispatched
        ? `digest dispatched via ${result.transport_mode} (real_delivery=${result.real_delivery})`
        : `digest NOT dispatched (${result.digest_skipped_reason})`
    console.info(
      `[samiksha:daily_job] done — closed=${result.closed_row_ids.length} ` +
        `closing_soon=${result.closing_soon_row_ids.length} · ${digestLine}`,
    )
  }
}

main().catch((err) => {
  console.error('[samiksha:daily_job] FAILED:', err instanceof Error ? err.stack ?? err.message : err)
  process.exit(1)
})
