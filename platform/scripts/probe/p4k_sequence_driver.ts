#!/usr/bin/env npx tsx
/**
 * p4k_sequence_driver.ts — P4-K narration audit, driver half.
 *
 * Drives the six Kāla views (`p4k_views.ts`) as ONE real reader thread against a
 * target `/api/pariprashna` deployment, by shelling out to the repo's EXISTING probe
 * harness (`platform/scripts/probe/ask.ts`) six times, chaining `--conversation-id`
 * turn to turn. This is deliberately NOT a second auth path: `ask.ts` already owns
 * the credential seam (mint a fresh Firebase session cookie for
 * `probe-service-account`, see that file's own header) and this driver never touches
 * a credential directly — it only reads the JSON transcript `ask.ts` writes per turn.
 *
 * Per COMMON_BRIEF + the P4-K charter: synthetic chart ONLY
 * (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`, see p4k_views.ts), never the native's real
 * chart. `--chart-id` is intentionally NOT exposed on this driver's CLI for that
 * reason — pass it through `ask.ts` directly if a deliberate, explicit override is
 * ever needed (that script's own guard logs loudly if so).
 *
 * BUILD-TIME NOTE (P4-K is a FILLER(build)/post-flip(run) lane — see PLAN.yaml and
 * the P4-K charter §10.2/§10.5): this driver is built and committed now but is NOT
 * executed against any live default surface tonight. It is exercised only via
 * `--self-test`, which drives nothing over the network. The CONDUCTOR/VERIFIER runs
 * it for real, post-flip, via `p4k_narration_audit.sh` (see that file for the exact
 * one-line command).
 *
 * Usage:
 *   npx tsx p4k_sequence_driver.ts --service-url https://<tagged-or-default-url>
 *   npx tsx p4k_sequence_driver.ts --self-test        # offline structural self-check, no network
 *
 * Writes one manifest JSON to `platform/scripts/probe/out/p4k_sequences/<sequence_id>/
 * manifest.json` listing, in order, each view's question, the copied transcript path,
 * the conversation id the thread ran under, and whether that turn completed clean.
 * `p4k_narration_analyzer.ts` consumes exactly this manifest shape.
 */
import { spawnSync } from 'node:child_process'
import { mkdirSync, readFileSync, writeFileSync, copyFileSync, existsSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { randomUUID } from 'node:crypto'
import { SIX_VIEWS, type ViewSpec } from './p4k_views.js'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ASK_TS = join(__dirname, 'ask.ts')
const SEQUENCES_DIR = join(__dirname, 'out', 'p4k_sequences')

export interface ManifestTurn {
  view: ViewSpec['view']
  primitive_id: string
  live_tool: string
  question: string
  transcript_path: string
  conversation_id: string | null
  partial: boolean
  terminal_status: string | null
  ask_exit_ok: boolean
}

export interface Manifest {
  sequence_id: string
  service_url: string
  created_at: string
  turns: ManifestTurn[]
}

interface AskTranscript {
  turn_id: string
  conversation_id: string | null
  partial: boolean
  terminal_status: string | null
}

/** Runs one `ask.ts` turn via child_process, returns the transcript path it wrote
 *  (parsed from its own stderr "[ask] wrote <path> ..." line — the same contract
 *  `ask.sh` callers already rely on, not a new one this driver invents). */
function runAskTurn(question: string, serviceUrl: string, conversationId: string | null): { path: string; ok: boolean } {
  const args = ['tsx', ASK_TS, question, '--service-url', serviceUrl]
  if (conversationId) args.push('--conversation-id', conversationId)
  const result = spawnSync('npx', args, { encoding: 'utf8' })
  const stderr = result.stderr ?? ''
  // ask.ts exits non-zero on a partial/truncated turn but STILL writes its
  // transcript file first (see that script's writeResult() call before
  // process.exit(1)) — so a non-zero exit here is data, not a driver failure.
  const ok = result.status === 0
  const match = stderr.match(/\[ask\] wrote (\S+\.json)/)
  if (match) return { path: match[1], ok }
  throw new Error(
    `p4k_sequence_driver: could not locate ask.ts's transcript path in its stderr output ` +
      `(exit status=${result.status}, signal=${result.signal}). Raw stderr tail: ${stderr.slice(-800)}`,
  )
}

function parseArgs(argv: string[]): { serviceUrl: string; selfTest: boolean } {
  let serviceUrl = ''
  let selfTest = false
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--service-url') serviceUrl = argv[++i]
    else if (argv[i] === '--self-test') selfTest = true
  }
  return { serviceUrl, selfTest }
}

function selfTest(): number {
  // Offline structural check: no network, no ask.ts invocation. Verifies this
  // driver's OWN contract — six distinct views in the documented order, each with
  // a non-empty probe_question — so a future edit to p4k_views.ts that silently
  // drops a view or empties a question is caught here, not discovered post-flip.
  const expected: ViewSpec['view'][] = ['NOW', 'AHEAD', 'PRIORITIZE', 'STORY', 'ELECT', 'EXPLAIN']
  const actual = SIX_VIEWS.map((v) => v.view)
  let ok = true
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    console.error(`[p4k_sequence_driver --self-test] FAIL: view order/set drifted. expected=${JSON.stringify(expected)} actual=${JSON.stringify(actual)}`)
    ok = false
  }
  for (const v of SIX_VIEWS) {
    if (!v.probe_question || v.probe_question.trim().length === 0) {
      console.error(`[p4k_sequence_driver --self-test] FAIL: view ${v.view} has an empty probe_question.`)
      ok = false
    }
    if (!v.primitive_id || !v.live_tool) {
      console.error(`[p4k_sequence_driver --self-test] FAIL: view ${v.view} missing primitive_id/live_tool.`)
      ok = false
    }
  }
  console.log(ok ? '[p4k_sequence_driver --self-test] PASS: six views intact, in order, all fields populated.' : '[p4k_sequence_driver --self-test] FAIL — see above.')
  return ok ? 0 : 1
}

function main(): number {
  const args = parseArgs(process.argv.slice(2))
  if (args.selfTest) return selfTest()
  if (!args.serviceUrl) {
    console.error('Usage: npx tsx p4k_sequence_driver.ts --service-url <url>   (or --self-test for an offline structural check)')
    return 2
  }

  const sequenceId = randomUUID()
  const seqDir = join(SEQUENCES_DIR, sequenceId)
  mkdirSync(seqDir, { recursive: true })

  console.error(`[p4k_sequence_driver] sequence ${sequenceId} against ${args.serviceUrl}`)
  console.error('[p4k_sequence_driver] WARNING: this drives REAL turns against the target surface, using the synthetic test chart only (ask.ts default). Never point --service-url at anything the real native could be routed through unknowingly outside the sanctioned canary/default flow.')

  let conversationId: string | null = null
  const turns: ManifestTurn[] = []

  for (let i = 0; i < SIX_VIEWS.length; i++) {
    const v = SIX_VIEWS[i]
    console.error(`[p4k_sequence_driver] turn ${i + 1}/6 — VIEW ${v.view} (${v.primitive_id} -> ${v.live_tool})`)
    const { path, ok } = runAskTurn(v.probe_question, args.serviceUrl, conversationId)
    if (!existsSync(path)) {
      throw new Error(`p4k_sequence_driver: ask.ts reported writing ${path} but the file does not exist.`)
    }
    const transcript = JSON.parse(readFileSync(path, 'utf8')) as AskTranscript
    const destName = `${String(i + 1).padStart(2, '0')}_${v.view.toLowerCase()}.json`
    const destPath = join(seqDir, destName)
    copyFileSync(path, destPath)

    turns.push({
      view: v.view,
      primitive_id: v.primitive_id,
      live_tool: v.live_tool,
      question: v.probe_question,
      transcript_path: destPath,
      conversation_id: transcript.conversation_id,
      partial: transcript.partial,
      terminal_status: transcript.terminal_status,
      ask_exit_ok: ok,
    })

    // Chain the thread: every subsequent turn continues the SAME conversation so
    // EXPLAIN (turn 6) can actually reach back into turn 1's claim, and so the
    // analyzer's cross-view checks are checking one real thread, not six
    // independent, unrelated conversations.
    if (transcript.conversation_id) conversationId = transcript.conversation_id
    else if (!ok) {
      console.error(`[p4k_sequence_driver] WARNING: turn ${i + 1} (${v.view}) produced no conversation_id and was not ok — subsequent turns will open a NEW thread, breaking the cross-turn EXPLAIN-hop check. Continuing (never silently retrying/looping).`)
    }
  }

  const manifest: Manifest = {
    sequence_id: sequenceId,
    service_url: args.serviceUrl,
    created_at: new Date().toISOString(),
    turns,
  }
  const manifestPath = join(seqDir, 'manifest.json')
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2))
  console.error(`[p4k_sequence_driver] wrote manifest: ${manifestPath}`)
  console.log(manifestPath)
  return 0
}

process.exit(main())
