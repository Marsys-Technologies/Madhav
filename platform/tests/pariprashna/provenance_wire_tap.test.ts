/**
 * Paripraśna Build — PB-2 (SMṚTI), Lane M-6: provenance-stamp wire-tap test.
 * ============================================================================
 * Enforces D-16 / PB-1 design plan ruling 8c: the provenance stamp (`build_id`,
 * `priors_version`, `formula_versions`, `ranking_config`) is DB-only. It must
 * NEVER appear on the SSE wire — not in any event field, not folded into a
 * `flag`/`grade` detail string, nowhere. `now_context_date` is the one
 * exception the brief carves out (may ride adjacent to daśā-year display data
 * for another lane) — this test does not forbid that field, only the other
 * four plus their container key names, which have no legitimate reason to
 * ever appear verbatim on the wire (the protocol's own field vocabulary,
 * `events.ts`, does not define any field named `build_id`, `priors_version`,
 * `formula_versions`, `ranking_config`, or `salience_formula_ver` — so a
 * clean stream can never contain these strings by coincidence).
 *
 * Why this test drives the REAL `PariprashnaEmitter` over a REPLAYED event
 * sequence rather than invoking the route's `POST` handler directly: the
 * route has ~40 live DB/LLM/auth dependencies, and the codebase's own prior
 * attempt at a full-route unit test (`tests/routes/adapter-branch-onfinish.
 * test.ts`) is `describe.skip`-quarantined for exactly this reason. Instead:
 *
 *   (A) a SOURCE-CONTRACT check greps the actual route.ts to prove the
 *       `provenanceStamp` variable this lane introduces is never passed as an
 *       argument to any `em.*(...)` call — the class of regression this test
 *       exists to catch;
 *   (B) a BEHAVIORAL check replays the EXACT em.* call sequence route.ts
 *       performs for a full turn (turn.open → phase × N → activity.upsert →
 *       block.open/delta/commit → the drift `flag` (reusing
 *       EDGE_STATE_LABELS.chart_rebuilt verbatim) → citation.define →
 *       turn.commit → turn.close) through the production `PariprashnaEmitter`
 *       + `serializeEvent`, and asserts the captured raw SSE bytes are
 *       stamp-field-free;
 *   (C) a RED proof: the same assertion helper, run against a deliberately
 *       leaky variant of the sequence, is shown to catch the leak (proving
 *       the detector is not vacuously passing).
 */
import { describe, it, expect } from 'vitest'
import { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'
import { readRouteSurface } from './route_surface'
import { EDGE_STATE_LABELS } from '@/lib/pariprashna/lexicon'
import type { TurnProvenanceStamp } from '@/lib/pariprashna/provenance/stamp'

// ─────────────────────────────────────────────────────────────────────────────
// (A) Source-contract check — route.ts never threads the stamp into em.*(...)
// ─────────────────────────────────────────────────────────────────────────────

// P0-C / RF-1: the pipeline moved into typed stage modules; the surface is the
// route shell plus every stage module it composes (tests/pariprashna/route_surface.ts).
const routeSrc = readRouteSurface()

describe('source contract: the live route surface never passes provenanceStamp into an em.* call', () => {
  it('computes the stamp exactly once and only threads it into persistence metadata', () => {
    // The stamp variable must exist (the write path this lane added).
    expect(routeSrc).toContain('computeTurnProvenanceStamp')
    expect(routeSrc).toContain('provenanceStamp')

    // Every `em.<method>(` call site — none of their argument blocks may
    // reference the raw `provenanceStamp` identifier. We scan call-by-call
    // (from `em.` to the matching top-level close) rather than a single
    // regex over the whole file, since a whole-file substring match would
    // also match the (legitimate) `withProvenanceStamp(..., provenanceStamp)`
    // persistence call.
    const emCallRegex = /\bem\.[a-zA-Z]+\(/g
    let match: RegExpExecArray | null
    const offendingCalls: string[] = []
    while ((match = emCallRegex.exec(routeSrc))) {
      const start = match.index + match[0].length
      let depth = 1
      let i = start
      while (i < routeSrc.length && depth > 0) {
        if (routeSrc[i] === '(') depth++
        else if (routeSrc[i] === ')') depth--
        i++
      }
      const callBody = routeSrc.slice(start, i - 1)
      if (/\bprovenanceStamp\b/.test(callBody)) {
        offendingCalls.push(`${match[0]}${callBody}`)
      }
    }
    expect(offendingCalls).toEqual([])
  })

  it('the drift flag reuses EDGE_STATE_LABELS.chart_rebuilt via the drift-result field, never a raw stamp field', () => {
    const flagIdx = routeSrc.indexOf("code: 'chart_rebuilt'")
    expect(flagIdx).toBeGreaterThan(-1)
    const nearby = routeSrc.slice(flagIdx - 200, flagIdx + 200)
    expect(nearby).toContain('provenanceDrift.edge_state_label')
    expect(nearby).not.toMatch(/provenanceStamp\.(build_id|priors_version|formula_versions|ranking_config)/)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// (B) + (C) Behavioral wire-tap over the replayed full-turn event sequence
// ─────────────────────────────────────────────────────────────────────────────

/** Minimal capturing stand-in for ReadableStreamDefaultController. */
function makeCapturingController() {
  const decoder = new TextDecoder()
  let text = ''
  const controller = {
    enqueue: (chunk: Uint8Array) => {
      text += decoder.decode(chunk, { stream: true })
    },
    close: () => {},
    error: () => {},
  } as unknown as ReadableStreamDefaultController<Uint8Array>
  return { controller, getText: () => text }
}

const STAMP: TurnProvenanceStamp = {
  build_id: 'build-9f3c1a2b-leak-canary',
  priors_version: '1.2',
  formula_versions: { salience_formula_ver: null },
  ranking_config: { mode: 'composite_v1' },
  now_context_date: '2026-07-28',
  computed_at: '2026-07-28T10:00:00.000Z',
}

/** Field/key names that must NEVER appear verbatim on the wire (D-16 / 8c). */
const FORBIDDEN_STRINGS = [
  'build_id',
  STAMP.build_id!,
  'priors_version',
  'formula_versions',
  'salience_formula_ver',
  'ranking_config',
  'composite_v1',
]

function findLeaks(streamText: string): string[] {
  return FORBIDDEN_STRINGS.filter((needle) => streamText.includes(needle))
}

/**
 * Replays the real em.* call sequence for a full Paripraśna turn, mirroring
 * route.ts's actual invocations (turn.open through turn.close). `leak: true`
 * simulates the exact regression class this test guards against — a future
 * edit that folds the raw stamp into a flag/grade detail instead of using the
 * closed-lexicon edge-state string — to prove the detector actually fires.
 */
function emitFullTurn(em: PariprashnaEmitter, opts: { withDrift: boolean; leak: boolean }): void {
  em.turnOpen({
    turn_id: 't-1',
    conversation_id: 'c-1',
    chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
    model_id: 'claude-opus-4-5',
    reading_depth: 'auto',
    length_tier: 'standard',
  })
  em.phase({ phase: 'plan', status: 'start' })
  em.phase({ phase: 'plan', status: 'end', ms: 120 })
  em.grade({ subject: 'query_class', grade: 'interpretive', detail: '3 planned tools' })

  em.phase({ phase: 'retrieve', status: 'start', pass_id: 1 })
  em.activity({ key: 'retrieve:dasha', label_key: 'Consulting the chart — Daśā structure', pass_id: 1, status: 'done', count: 5, ms: 80 })
  em.phase({ phase: 'retrieve', status: 'end', pass_id: 1, ms: 200 })

  em.phase({ phase: 'synthesize', status: 'start', pass_id: 1 })
  em.blockOpen({ block_id: 'blk-1-1', pass_id: 1, role: 'prose' })
  em.blockDelta({ block_id: 'blk-1-1', delta: 'Saturn transits the natal Moon this year.' })
  em.blockCommit({ block_id: 'blk-1-1', text: 'Saturn transits the natal Moon this year.' })
  em.phase({ phase: 'synthesize', status: 'end', pass_id: 1, ms: 900 })

  em.grade({ subject: 'citation_gate', grade: 'PASS', detail: '2/2 verified' })
  em.citationDefine({ index: 0, signal_id: 'SIG.MSR.413', layer: 'L2.5', snippet: 'Mercury eight-system convergence' })

  if (opts.withDrift) {
    if (opts.leak) {
      // ── Deliberately leaky variant (what the source-contract regression
      // would look like) — a regression that stringifies the raw stamp into
      // a flag detail instead of using the closed-lexicon edge-state string.
      em.flag({ code: 'chart_rebuilt', level: 'info', detail: JSON.stringify(STAMP) })
    } else {
      // ── The real, correct emission (mirrors route.ts exactly).
      em.flag({ code: 'chart_rebuilt', level: 'info', detail: EDGE_STATE_LABELS.chart_rebuilt })
    }
  }

  em.turnCommit({ turn_id: 't-1', conversation_id: 'c-1', message_id: 'm-1', status: 'ok', assistant_chars: 42 })
  em.grade({ subject: 'completeness', grade: '5/6', detail: 'served/floor' })
  em.phase({ phase: 'finalize', status: 'end' })
  em.turnClose({ turn_id: 't-1', status: 'ok', ms: 1500 })
}

describe('wire-tap: the provenance stamp never reaches the SSE wire', () => {
  it('GREEN — a full turn (with build_id drift) emits zero stamp fields on the wire', () => {
    const { controller, getText } = makeCapturingController()
    const em = new PariprashnaEmitter(controller)
    emitFullTurn(em, { withDrift: true, leak: false })
    em.close()

    const streamText = getText()
    // Sanity: the stream is non-trivial and really contains the drift flag.
    expect(streamText).toContain('turn.open')
    expect(streamText).toContain('turn.close')
    expect(streamText).toContain(EDGE_STATE_LABELS.chart_rebuilt)

    const leaks = findLeaks(streamText)
    expect(leaks).toEqual([])
  })

  it('GREEN — a full turn with NO drift also emits zero stamp fields', () => {
    const { controller, getText } = makeCapturingController()
    const em = new PariprashnaEmitter(controller)
    emitFullTurn(em, { withDrift: false, leak: false })
    em.close()
    expect(findLeaks(getText())).toEqual([])
  })

  it('RED — a deliberately leaky emission IS caught by the same assertion (proves the detector is live, not vacuous)', () => {
    const { controller, getText } = makeCapturingController()
    const em = new PariprashnaEmitter(controller)
    emitFullTurn(em, { withDrift: true, leak: true })
    em.close()

    const streamText = getText()
    const leaks = findLeaks(streamText)
    // The leak canary build_id AND the container key names must be caught.
    expect(leaks.length).toBeGreaterThan(0)
    expect(leaks).toContain(STAMP.build_id)
    expect(leaks).toContain('build_id')
    expect(leaks).toContain('formula_versions')
    expect(leaks).toContain('ranking_config')

    // Demonstrates the fail-mode a CI gate built on `findLeaks` would produce:
    // asserting the wire is clean on the leaky stream throws exactly like a
    // real CI failure would.
    expect(() => expect(leaks).toEqual([])).toThrowError()
  })
})
