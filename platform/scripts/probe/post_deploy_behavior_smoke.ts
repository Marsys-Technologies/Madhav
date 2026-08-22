#!/usr/bin/env tsx
/**
 * probe/post_deploy_behavior_smoke.ts — P3-E: CI post-deploy smoke,
 * demonstrated-can-fail (PB-4 F-6).
 *
 * CONTEXT: `scripts/operator/end_to_end_smoke.sh` (run by deploy.yml after every
 * `amjis-web` deploy) says so itself, in its own header: "Honestly NOT covered,
 * and deliberately not claimed: no DB round-trip, no authenticated request, no
 * chart render. Those need a web canary credential that does not exist yet —
 * the same class of gap deploy.yml already documents for the MCP canary key."
 * That gap is PB-4 finding F-6. This script closes it: it drives a REAL
 * authenticated turn against the LIVE deployed `/api/pariprashna` route (via
 * `probe/ask.ts`, reused rather than reinvented — see that file's header for
 * the full credential-seam design) on the SYNTHETIC test chart
 * (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`, Abhinandan Mohanty — NEVER the
 * native's real chart `482012f1-…`) and asserts real engine behaviour, not
 * mere liveness.
 *
 * WHAT IS ASSERTED (each one is a real code path that must run correctly):
 *   - ask_script_exit_zero    — the whole SSE turn completed without a
 *                               network/HTTP/stream-truncation error.
 *   - turn_record_readable    — the probe's own JSON artifact parses.
 *   - terminal_status_ok      — the stream's `turn.close` event reported
 *                               status 'ok', not 'error'/'aborted'.
 *   - prose_non_trivial       — the assembled answer has real content
 *                               (catches an empty/truncated-response class
 *                               regression a bare HTTP-200 would miss).
 *   - receipt_define_present  — a `receipt.define` wire event was emitted
 *                               with a non-null `receipt` payload. This is
 *                               the KEY behavioural assertion: per
 *                               `pipeline/persistence_stage.ts`, this event
 *                               fires only AFTER `assembleAcharyaReadingReceipt`
 *                               + `validateAcharyaReadingReceipt` both
 *                               succeed — i.e. it proves the synthesis →
 *                               receipt-assembly → validation → persistence
 *                               chain ran end-to-end on the deployed
 *                               revision, not just that tokens streamed back.
 *                               If this pipeline regresses (assembly throws,
 *                               validation starts rejecting, or the stage is
 *                               ever short-circuited), this assertion goes
 *                               red while a naive HTTP-200 probe would stay
 *                               green.
 *   - no_stream_error_events  — no `type: 'error'` event anywhere on the wire.
 *   - blocks_committed        — at least one `block.commit` event landed
 *                               (the rendering pipeline actually produced
 *                               structured output, not just raw deltas).
 *
 * WHAT THIS DOES NOT ASSERT, AND WHY (say so plainly — no invented judgment
 * per CLAUDE.md §N.7 item 6):
 *   - Citation presence (`citation.define`) is NOT asserted as a hard gate:
 *     whether a given turn cites anything depends on the question's content
 *     and the synthetic chart's data density, so an empty citation set on a
 *     given probe question is not distinguishable from a real regression
 *     without a fixed, content-matched question bank this lane did not have
 *     time to build. Recorded in the smoke's own report as `citations_seen`
 *     (informational), not gated.
 *   - The safety gate (`PARIPRASHNA_SAFETY_GATE_ENABLED`) is NOT exercised:
 *     it is flag-gated off in production as of this writing (see
 *     `probe/ask.ts`'s own header), so a probe turn cannot observe it firing
 *     either way. Asserting on it would be asserting on a flag value, not on
 *     engine behaviour.
 *   - The harness-origin DB conversation tag is best-effort in `ask.ts`
 *     itself (needs a Cloud SQL Proxy tunnel this CI job does not open) and
 *     is never gated here — consistent with `ask.ts`'s own non-fatal design.
 *
 * §N.8 DEMONSTRATED-CAN-FAIL: mirrors the `ALWAYS_FAIL_MODE` precedent this
 * repo already uses in `scripts/gochara/smoke_probe.ts`. `INDUCE_FAILURE_MODE`
 * below was `true` for the one-time red-run proof commit (deliberately
 * requires an unreachable prose length AND treats `receipt.define` as always
 * absent, so BOTH the content-volume and the receipt-pipeline assertions are
 * proven capable of catching a real regression) — it is `false` in every
 * commit after that proof landed. See the lane's PR description for the CI
 * run URL of the red proof.
 *
 * USAGE (from platform/):
 *   npx tsx scripts/probe/post_deploy_behavior_smoke.ts
 *   SMOKE_WEB_URL=https://... npx tsx scripts/probe/post_deploy_behavior_smoke.ts
 *
 * ENVIRONMENT (all forwarded to the underlying `ask.ts` call):
 *   FIREBASE_ADMIN_CREDENTIALS, NEXT_PUBLIC_FIREBASE_API_KEY — required (the
 *     same two values `ask.ts` needs; both already provisioned as GitHub
 *     Actions repo secrets — see this lane's workflow).
 *   SMOKE_WEB_URL — target service URL. Default: the production `amjis-web`
 *     Cloud Run URL (same value `deploy.yml`'s `APP_URL` env var carries).
 *   SMOKE_MIN_PROSE_CHARS — override the content-volume floor (default 150).
 */

import { execFileSync } from 'node:child_process'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT_DIR = join(__dirname, 'out')
const ASK_SCRIPT = join(__dirname, 'ask.ts')
const PLATFORM_ROOT = join(__dirname, '..', '..')

const DEFAULT_QUESTION = 'What does the current daśā period emphasize for this chart?'
const SERVICE_URL = process.env['SMOKE_WEB_URL'] ?? 'https://amjis-web-938361928218.asia-south1.run.app'
const MIN_PROSE_CHARS = Number(process.env['SMOKE_MIN_PROSE_CHARS'] ?? '150')

// ── §N.8 demonstrated-can-fail toggle — see header. TRUE for this commit
// ONLY, to produce the one-time red-run proof; the very next commit on this
// branch flips it to false. Do not flip this back to true except to
// re-run that proof deliberately. ──────────────────────────────────────────
const INDUCE_FAILURE_MODE = true

interface Assertion {
  name: string
  pass: boolean
  detail: string
}

interface TurnEvent {
  type: string
  raw: Record<string, unknown>
  receivedAtMs: number
}

interface TurnRecord {
  turn_id: string
  chart_id: string
  terminal_status: string | null
  prose: string
  events: TurnEvent[]
  blocks: Array<{ blockId: string; kind: string | null; role: string | null }>
  partial: boolean
}

function newestJsonFile(dir: string): string {
  const files = readdirSync(dir).filter((f) => f.endsWith('.json'))
  if (files.length === 0) throw new Error(`no turn record file found in ${dir} — ask.ts likely never wrote one`)
  const withTimes = files.map((f) => ({ f, t: statSync(join(dir, f)).mtimeMs }))
  withTimes.sort((a, b) => b.t - a.t)
  return join(dir, withTimes[0]!.f)
}

function main(): void {
  console.log(`[post_deploy_behavior_smoke] target=${SERVICE_URL}`)
  console.log(`[post_deploy_behavior_smoke] question=${JSON.stringify(DEFAULT_QUESTION)}`)
  console.log(`[post_deploy_behavior_smoke] INDUCE_FAILURE_MODE=${INDUCE_FAILURE_MODE}`)

  let askExitCode = 0
  try {
    execFileSync('npx', ['tsx', ASK_SCRIPT, DEFAULT_QUESTION, '--service-url', SERVICE_URL], {
      stdio: 'inherit',
      cwd: PLATFORM_ROOT,
    })
  } catch (err: unknown) {
    const status = (err as { status?: number } | null)?.status
    askExitCode = typeof status === 'number' ? status : 1
    console.error(`[post_deploy_behavior_smoke] ask.ts exited ${askExitCode} — continuing to inspect whatever it wrote`)
  }

  let record: TurnRecord | undefined
  let readError: string | null = null
  try {
    const path = newestJsonFile(OUT_DIR)
    console.log(`[post_deploy_behavior_smoke] inspecting ${path}`)
    record = JSON.parse(readFileSync(path, 'utf8')) as TurnRecord
  } catch (err) {
    readError = String(err)
  }

  const assertions: Assertion[] = []

  assertions.push({
    name: 'ask_script_exit_zero',
    pass: askExitCode === 0,
    detail: `ask.ts exit code = ${askExitCode}`,
  })

  assertions.push({
    name: 'turn_record_readable',
    pass: readError === null,
    detail: readError ?? 'turn record parsed OK',
  })

  let citationsSeen = 0

  if (record) {
    assertions.push({
      name: 'terminal_status_ok',
      pass: record.terminal_status === 'ok',
      detail: `terminal_status=${record.terminal_status}`,
    })

    const proseLen = typeof record.prose === 'string' ? record.prose.length : 0
    // Induced mode: an unreachable floor proves this assertion is capable of failing.
    const proseThreshold = INDUCE_FAILURE_MODE ? 999_999_999 : MIN_PROSE_CHARS
    assertions.push({
      name: 'prose_non_trivial',
      pass: proseLen >= proseThreshold,
      detail: `prose.length=${proseLen}, threshold=${proseThreshold}`,
    })

    const events: TurnEvent[] = Array.isArray(record.events) ? record.events : []
    citationsSeen = events.filter((e) => e.type === 'citation.define').length

    // Induced mode: pretend the event was never seen, proving this assertion
    // is capable of failing independently of the prose-length one above.
    const receiptEvent = INDUCE_FAILURE_MODE ? undefined : events.find((e) => e.type === 'receipt.define')
    const receiptPresent = Boolean(receiptEvent) && receiptEvent!.raw?.['receipt'] != null
    assertions.push({
      name: 'receipt_define_present',
      pass: receiptPresent,
      detail: receiptEvent
        ? `receipt.define seen; receipt payload is ${receiptEvent.raw?.['receipt'] != null ? 'non-null' : 'NULL'}`
        : 'no receipt.define event on the wire — the synthesis→receipt-assembly→validation→persistence chain did not complete visibly',
    })

    const errorEvents = events.filter((e) => e.type === 'error')
    assertions.push({
      name: 'no_stream_error_events',
      pass: errorEvents.length === 0,
      detail: `error events on wire = ${errorEvents.length}`,
    })

    const blockCount = Array.isArray(record.blocks) ? record.blocks.length : 0
    assertions.push({
      name: 'blocks_committed',
      pass: blockCount > 0,
      detail: `block.commit count = ${blockCount}`,
    })
  }

  const failed = assertions.filter((a) => !a.pass)
  const report = {
    battery: 'post_deploy_behavior_smoke (P3-E / PB-4 F-6)',
    service_url: SERVICE_URL,
    chart_id: record?.chart_id ?? null,
    turn_id: record?.turn_id ?? null,
    induce_failure_mode: INDUCE_FAILURE_MODE,
    citations_seen_informational_not_gated: citationsSeen,
    assertions,
    summary: { pass: assertions.length - failed.length, fail: failed.length, total: assertions.length },
    generated_at: new Date().toISOString(),
  }
  console.log(JSON.stringify(report, null, 2))

  if (failed.length > 0) {
    console.error(`[post_deploy_behavior_smoke] FAIL — ${failed.length}/${assertions.length} assertions failed:`)
    for (const a of failed) console.error(`  FAIL  ${a.name}: ${a.detail}`)
    process.exit(1)
  }
  console.error(`[post_deploy_behavior_smoke] PASS — ${assertions.length}/${assertions.length} assertions passed.`)
}

main()
