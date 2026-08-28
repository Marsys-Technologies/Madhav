/**
 * pariprashna/s3_live_corpus_run.ts — S3 stream driver script (not part of the
 * corpus library itself; a caller script per probe_output_adapter.ts's own
 * docblock: "Driving probe/ask.ts itself ... is left to a caller script").
 *
 * Runs a named subset of CORPUS_FIXTURES against the LIVE deployed web door
 * (scripts/probe/ask.ts, synthetic chart default — never passes --chart-id,
 * so it is structurally incapable of touching the real native's chart),
 * adapts each captured turn via turnObservationFromProbeOutput, and scores
 * the batch through the existing runCorpus/scoreAllDimensions machinery.
 *
 * Usage: npx tsx scripts/pariprashna/s3_live_corpus_run.ts <fixtureId> [<fixtureId> ...]
 * Writes a JSON report to scripts/pariprashna/out/s3_live_corpus_report_<ts>.json
 * (ts supplied via SNAPSHOT_TS env to keep the script pure re: Date.now()).
 */

import { execSync } from 'node:child_process'
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, statSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

import { CORPUS_FIXTURES } from '../../src/lib/pariprashna/corpus/fixtures'
import { turnObservationFromProbeOutput, type ProbeOutputRecord } from '../../src/lib/pariprashna/corpus/adapters/probe_output_adapter'
import { runCorpus } from '../../src/lib/pariprashna/corpus/runner'
import type { CorpusFixture, TurnObservation } from '../../src/lib/pariprashna/corpus/types'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT_DIR = join(__dirname, 'out')
const PROBE_OUT_DIR = join(__dirname, '..', 'probe', 'out')

function newestProbeOutputFile(): string | null {
  const files = readdirSync(PROBE_OUT_DIR).filter((f) => f.endsWith('.json'))
  if (files.length === 0) return null
  const withMtime = files.map((f) => ({ f, mtime: statSync(join(PROBE_OUT_DIR, f)).mtimeMs }))
  withMtime.sort((a, b) => b.mtime - a.mtime)
  return join(PROBE_OUT_DIR, withMtime[0].f)
}

function runProbe(fixture: CorpusFixture): TurnObservation {
  const escaped = fixture.queryText.replace(/"/g, '\\"')
  const cmd = `npx tsx scripts/probe/ask.ts "${escaped}"`
  console.error(`[s3-live] running ${fixture.fixtureId} ...`)
  const before = newestProbeOutputFile()
  try {
    execSync(cmd, { cwd: join(__dirname, '..', '..'), stdio: 'inherit', maxBuffer: 1024 * 1024 * 32 })
  } catch (err) {
    const e = err as { message?: string }
    console.error(`[s3-live] ${fixture.fixtureId} probe exited non-zero: ${e.message}`)
  }
  const outPath = newestProbeOutputFile()
  if (!outPath || outPath === before) {
    console.error(`[s3-live] ${fixture.fixtureId}: no new probe output file detected`)
    return { fixture, receipt: null, turnMetrics: null, proseText: null }
  }
  const record: ProbeOutputRecord = JSON.parse(readFileSync(outPath, 'utf8'))
  console.error(`[s3-live] ${fixture.fixtureId}: read ${outPath}`)
  return turnObservationFromProbeOutput(record, fixture)
}

async function main() {
  const ids = process.argv.slice(2)
  if (ids.length === 0) {
    console.error('usage: s3_live_corpus_run.ts <fixtureId> [<fixtureId> ...]')
    process.exit(1)
  }
  const byId = new Map(CORPUS_FIXTURES.map((f) => [f.fixtureId, f]))
  const fixtures: CorpusFixture[] = []
  for (const id of ids) {
    const f = byId.get(id)
    if (!f) {
      console.error(`[s3-live] unknown fixtureId: ${id}`)
      process.exit(1)
    }
    fixtures.push(f)
  }

  const observations = new Map<string, TurnObservation>()
  for (const f of fixtures) {
    observations.set(f.fixtureId, runProbe(f))
  }

  const report = await runCorpus({
    fixtures,
    runTurn: async (f) => observations.get(f.fixtureId)!,
    target: { kind: 'web_route', description: 'https://amjis-web-qm256lasva-el.a.run.app/api/pariprashna (live deployed default model, probe/ask.ts)' },
  })

  if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true })
  const ts = process.env.SNAPSHOT_TS ?? String(Date.now())
  const outFile = join(OUT_DIR, `s3_live_corpus_report_${ts}.json`)
  writeFileSync(outFile, JSON.stringify(report, null, 2))
  console.error(`[s3-live] wrote ${outFile}`)
  console.log(JSON.stringify(report.summary, null, 2))
}

main()
