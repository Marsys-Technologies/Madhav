/**
 * pariprashna/s3_live_corpus_run.ts — S3 stream driver script (not part of the
 * corpus library itself; a caller script per probe_output_adapter.ts's own
 * docblock: "Driving probe/ask.ts itself ... is left to a caller script").
 *
 * Runs a named subset of CORPUS_FIXTURES against the LIVE deployed web door,
 * adapts each captured turn via turnObservationFromProbeOutput, and scores
 * the batch through the existing runCorpus/scoreAllDimensions machinery.
 *
 * Chart scoping (V3-E-012 native ruling, decision_recorded event
 * 99421811-e13d-4b19-88f4-2cc16d7af220, 2026-08-29): --chart-id is passed to
 * probe/ask.ts ONLY when the FIXTURE ITSELF declares chartId ===
 * CANONICAL_CHART_ID (the native's real chart) — driven by the fixture's own
 * data, never a separate CLI flag, so an operator cannot accidentally widen
 * real-chart use by mistyping a flag. Every other fixture runs against
 * probe/ask.ts's synthetic default, unchanged. The ruling's own scope note:
 * "the quality corpus (fixtures.ts) only — this does NOT broaden real-chart
 * use to live probes or other streams" — this script IS that quality corpus,
 * so it is the one place the ruling actually applies.
 *
 * priorTurns seeding (2026-08-29): a fixture with `priorTurns` gets a REAL
 * two-call live conversation — first call seeds with priorTurns[0]'s user
 * text (a genuine live turn, not a scripted/fabricated assistant reply —
 * probe/ask.ts cannot inject history that didn't really happen), capturing
 * the real conversation_id; the second call asks the fixture's actual
 * queryText with --conversation-id continuing that same real thread. This is
 * MORE authentic than trying to force the scripted priorTurns[1] assistant
 * text into history (which no live door supports) — it tests the real
 * capability (reconciling a new question against real prior conversation
 * state), just not guaranteed to match the fixture's illustrative script
 * verbatim. Disclosed in each such observation's trace log.
 *
 * Usage: npx tsx scripts/pariprashna/s3_live_corpus_run.ts <fixtureId> [<fixtureId> ...]
 * Env: S3_SERVICE_URL overrides probe/ask.ts's default deployed host.
 * Writes a JSON report to scripts/pariprashna/out/s3_live_corpus_report_<ts>.json
 * (ts supplied via SNAPSHOT_TS env to keep the script pure re: Date.now()).
 */

import { execFileSync } from 'node:child_process'
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, statSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

import { CORPUS_FIXTURES } from '../../src/lib/pariprashna/corpus/fixtures'
import { CANONICAL_CHART_ID } from '../../src/lib/pariprashna/corpus/types'
import { turnObservationFromProbeOutput, type ProbeOutputRecord } from '../../src/lib/pariprashna/corpus/adapters/probe_output_adapter'
import { runCorpus } from '../../src/lib/pariprashna/corpus/runner'
import type { CorpusFixture, TurnObservation } from '../../src/lib/pariprashna/corpus/types'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT_DIR = join(__dirname, 'out')
const PROBE_OUT_DIR = join(__dirname, '..', 'probe', 'out')
const SERVICE_URL = process.env.S3_SERVICE_URL ?? 'https://amjis-web-938361928218.asia-south1.run.app'
const V3_E_012_RULING_EVENT_ID = '99421811-e13d-4b19-88f4-2cc16d7af220'

export const TRACE_LOG: Array<{ fixtureId: string; turnId: string | null; conversationId: string | null; seedConversationId: string | null; realChart: boolean }> = []

function newestProbeOutputFile(): string | null {
  const files = readdirSync(PROBE_OUT_DIR).filter((f) => f.endsWith('.json'))
  if (files.length === 0) return null
  const withMtime = files.map((f) => ({ f, mtime: statSync(join(PROBE_OUT_DIR, f)).mtimeMs }))
  withMtime.sort((a, b) => b.mtime - a.mtime)
  return join(PROBE_OUT_DIR, withMtime[0].f)
}

interface RawProbeRecord extends ProbeOutputRecord {
  turn_id?: string
  conversation_id?: string
  __path: string
}

function callAsk(question: string, opts: { chartId?: string; conversationId?: string }): RawProbeRecord {
  const args = ['tsx', 'scripts/probe/ask.ts', question, '--service-url', SERVICE_URL]
  if (opts.chartId) args.push('--chart-id', opts.chartId)
  if (opts.conversationId) args.push('--conversation-id', opts.conversationId)
  const before = newestProbeOutputFile()
  try {
    execFileSync('npx', args, { cwd: join(__dirname, '..', '..'), stdio: 'inherit', maxBuffer: 1024 * 1024 * 32 })
  } catch (err) {
    const e = err as { message?: string }
    console.error(`[s3-live] ask.ts exited non-zero: ${e.message}`)
  }
  const outPath = newestProbeOutputFile()
  if (!outPath || outPath === before) {
    throw new Error('no new probe output file detected')
  }
  const record: RawProbeRecord = JSON.parse(readFileSync(outPath, 'utf8'))
  return { ...record, __path: outPath }
}

function runProbe(fixture: CorpusFixture): TurnObservation {
  const realChart = fixture.chartId === CANONICAL_CHART_ID
  console.error(
    `[s3-live] running ${fixture.fixtureId} ${realChart ? `[REAL CHART -- V3-E-012 ruling ${V3_E_012_RULING_EVENT_ID}]` : '[synthetic]'} ...`,
  )
  try {
    let seedConversationId: string | null = null
    if (fixture.priorTurns && fixture.priorTurns.length > 0) {
      const seedText = fixture.priorTurns.find((t) => t.role === 'user')?.text
      if (seedText) {
        console.error(`[s3-live] ${fixture.fixtureId}: seeding real prior turn -- "${seedText.slice(0, 80)}..."`)
        const seedRecord = callAsk(seedText, { chartId: realChart ? CANONICAL_CHART_ID : undefined })
        seedConversationId = seedRecord.conversation_id ?? null
        console.error(`[s3-live] ${fixture.fixtureId}: seed conversation_id=${seedConversationId}`)
      }
    }
    const record = callAsk(fixture.queryText, {
      chartId: realChart ? CANONICAL_CHART_ID : undefined,
      conversationId: seedConversationId ?? undefined,
    })
    const turnId = record.turn_id ?? null
    const conversationId = record.conversation_id ?? null
    TRACE_LOG.push({ fixtureId: fixture.fixtureId, turnId, conversationId, seedConversationId, realChart })
    console.error(`[s3-live] ${fixture.fixtureId}: turn_id=${turnId} conversation_id=${conversationId} (${record.__path})`)
    return turnObservationFromProbeOutput(record, fixture)
  } catch (err) {
    console.error(`[s3-live] ${fixture.fixtureId}: FAILED — ${(err as Error).message}`)
    TRACE_LOG.push({ fixtureId: fixture.fixtureId, turnId: null, conversationId: null, seedConversationId: null, realChart })
    return { fixture, receipt: null, turnMetrics: null, proseText: null }
  }
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
    target: { kind: 'web_route', description: `${SERVICE_URL}/api/pariprashna (live deployed default model, probe/ask.ts)` },
  })

  if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true })
  const ts = process.env.SNAPSHOT_TS ?? String(Date.now())
  const outFile = join(OUT_DIR, `s3_live_corpus_report_${ts}.json`)
  writeFileSync(outFile, JSON.stringify(report, null, 2))
  const traceFile = join(OUT_DIR, `s3_live_corpus_trace_${ts}.json`)
  writeFileSync(traceFile, JSON.stringify(TRACE_LOG, null, 2))
  console.error(`[s3-live] wrote ${outFile}`)
  console.error(`[s3-live] wrote ${traceFile}`)
  console.log(JSON.stringify(report.summary, null, 2))
}

main()
