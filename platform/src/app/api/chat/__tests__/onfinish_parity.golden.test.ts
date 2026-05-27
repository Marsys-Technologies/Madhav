/**
 * onfinish_parity.golden.test.ts — unit 3.cutover (Stream A, sets G5b_onfinish).
 *
 * GOLDEN TEST: drives a fixed transcript through both pipelines' onFinish
 * write-through stage and asserts that the recorded I/O call lists are
 * deep-equal.
 *
 * Why this is the G5b setter: the cutover unit (3.cutover) flips the pipeline
 * selector default to the new (adapter) pipeline. For that to be safe the
 * adapter path must produce byte-identical write-throughs (persistence,
 * predictions, observatory cost, citation enrichment, marker parsing,
 * context-assembly bookkeeping, pending-stream cleanup, blind-mode ledger)
 * relative to the legacy synthesis-orchestrator path.
 *
 * Mechanism:
 *   • Both pipelines now route their onFinish stage through the shared
 *     `runOnFinishWriteThrough` helper at
 *     `platform/src/lib/pipelines/shared/onfinish_writethrough.ts`.
 *   • The test invokes that helper twice with identical inputs but the
 *     `pipelineKind` discriminator set to 'agentic' (adapter) and
 *     'single_pass' (legacy) respectively.
 *   • All dependencies (persistence, pricing, context-assembly-log writer,
 *     MSR snippet resolver, pending-stream writer, title client, prediction
 *     ledger appender) are recording mocks. The test asserts the recorded
 *     call lists deep-equal across the two invocations.
 *
 * If the two paths ever diverge in their write-through behaviour, this test
 * fails — G5b regresses, parent Conductor halts the queue.
 */

import { describe, it, expect, beforeEach } from 'vitest'

import type { UIMessage } from 'ai'

import {
  runOnFinishWriteThrough,
  type OnFinishWriteThroughOpts,
  type OnFinishWriteThroughDeps,
  type CitationGateOutcome,
} from '@/lib/pipelines/shared'

// ---------------------------------------------------------------------------
// Recording mocks — each captures the arguments it was called with so the
// test can deep-compare across the two pipeline invocations.
// ---------------------------------------------------------------------------

interface CapturedEvent {
  type: string
  data?: unknown
}

interface CapturedCall {
  fn: string
  args: unknown
}

function makeRecorder() {
  const events: CapturedEvent[] = []
  const calls: CapturedCall[] = []

  const writer = {
    write: (e: CapturedEvent) => {
      // Strip volatile fields so the comparison is stable.
      events.push({ type: e.type, data: e.data })
    },
  }

  const emit = (event: { event: string; query_id?: string; [k: string]: unknown }) => {
    calls.push({ fn: 'emit', args: event })
  }

  return { events, calls, writer, emit }
}

function makeDeps(rec: ReturnType<typeof makeRecorder>): OnFinishWriteThroughDeps {
  return {
    persistence: {
      writeMessages: async (args) => {
        rec.calls.push({ fn: 'persistence.writeMessages', args })
        // Synthesise deterministic message ids derived from the input length so
        // the assertion is stable across runs.
        const ids = args.messages.map((_, i) => `msg-${i}`)
        return { verified: true, messageIds: ids }
      },
    },
    pricing: {
      getPricing: (modelId: string) => {
        rec.calls.push({ fn: 'pricing.getPricing', args: { modelId } })
        return { input_per_million_tokens: 3, output_per_million_tokens: 15 }
      },
      computeUsd: (pricing, tokens) => {
        rec.calls.push({ fn: 'pricing.computeUsd', args: { pricing, tokens } })
        return 0.0042
      },
    },
    contextAssemblyLog: (entry) => {
      rec.calls.push({ fn: 'contextAssemblyLog', args: entry })
    },
    fetchMsrSnippets: async (signalIds) => {
      rec.calls.push({ fn: 'fetchMsrSnippets', args: { signalIds } })
      const m = new Map<string, string>()
      for (const sid of signalIds) m.set(sid, `snippet-for-${sid}`)
      return m
    },
    pendingStreamWriter: {
      clear: () => {
        rec.calls.push({ fn: 'pendingStreamWriter.clear', args: {} })
      },
    },
    title: {
      generate: async (msgs, ctx) => {
        rec.calls.push({
          fn: 'title.generate',
          args: { messageCount: msgs.length, ctx },
        })
        return 'Test conversation title'
      },
      update: async (cid, title) => {
        rec.calls.push({ fn: 'title.update', args: { conversationId: cid, title } })
      },
    },
    predictionLedger: (entry) => {
      // Strip volatile pred_id + emitted_at so the comparison is stable across
      // calls in different ms ticks.
      const { pred_id: _pid, emitted_at: _ea, ...stable } = entry
      rec.calls.push({ fn: 'predictionLedger', args: stable })
    },
  }
}

// ---------------------------------------------------------------------------
// Fixed transcript — exercises every write-through branch (cost, persistence,
// citation enrichment, marker parsing, prediction candidate, title, ledger).
// ---------------------------------------------------------------------------

const ASSISTANT_TEXT = [
  // SIG.MSR.NNN citations → exercises data-citation enrichment.
  'The Saturn–Mars opposition SIG.MSR.142 ripens through 2027.',
  'Cross-referenced with SIG.MSR.207 for school convergence.',
  // CORRECTION marker (‹correction› unicode-guillemet format per marker_parser.ts).
  '‹correction›original: "Moon in 7H"\ncorrected: "Moon in 8H"\nsource: "BPHS 7.42"‹/correction›',
  // Time-indexed prediction → exercises data-prediction-candidate.
  'In Q3 2027 the native will likely encounter a relocation event.',
].join(' ')

const FIXED_MESSAGES: UIMessage[] = [
  // History — one user, one assistant from prior turn.
  {
    id: 'u-prev',
    role: 'user',
    parts: [{ type: 'text', text: 'What is my career outlook?' }],
  } as unknown as UIMessage,
  {
    id: 'a-prev',
    role: 'assistant',
    parts: [{ type: 'text', text: 'Prior assistant turn.' }],
  } as unknown as UIMessage,
  // Current turn.
  {
    id: 'u-now',
    role: 'user',
    parts: [{ type: 'text', text: 'And the Saturn timing?' }],
  } as unknown as UIMessage,
  {
    id: 'a-now',
    role: 'assistant',
    parts: [{ type: 'text', text: ASSISTANT_TEXT }],
  } as unknown as UIMessage,
]

const FIXED_CITATION_GATE: CitationGateOutcome = {
  gateResult: 'PASS',
  layer1Count: 2,
  layer2Verified: 2,
}

function buildOpts(overrides: Partial<OnFinishWriteThroughOpts> = {}): OnFinishWriteThroughOpts {
  const rec = makeRecorder()
  return {
    pipelineKind: 'agentic',
    queryId: '00000000-0000-0000-0000-000000000001',
    conversationId: '00000000-0000-0000-0000-000000000002',
    chartId: '00000000-0000-0000-0000-000000000003',
    userUid: 'firebase-uid-test',
    isFirstTurn: true,
    lelContextEnabled: false, // exercises blind-mode prediction ledger
    finalMessages: FIXED_MESSAGES,
    assistantText: ASSISTANT_TEXT,
    lastUserQuery: 'And the Saturn timing?',
    lastAssistantMetadata: { custom: { model: 'claude-3-5-sonnet', queryId: '00000000-0000-0000-0000-000000000001' } },
    modelId: 'claude-3-5-sonnet',
    modelMaxContext: 200_000,
    synthUsage: {
      inputTokens: 8_000,
      outputTokens: 1_200,
      cacheReadInputTokens: 4_000,
      cacheCreationInputTokens: 0,
    },
    synthesisElapsedMs: 4_321,
    citationGate: FIXED_CITATION_GATE,
    contextAssembly: {
      l1_tokens: 1_500,
      l2_5_signal_tokens: 800,
      l2_5_pattern_tokens: 400,
      l4_tokens: 200,
      vector_tokens: 0,
      cgm_tokens: 100,
    },
    writer: rec.writer,
    emit: rec.emit,
    ...overrides,
  }
}

// ---------------------------------------------------------------------------
// Test surface
// ---------------------------------------------------------------------------

describe('3.cutover — onFinish write-through parity (G5b_onfinish setter)', () => {
  let recAgentic: ReturnType<typeof makeRecorder>
  let recSinglePass: ReturnType<typeof makeRecorder>

  beforeEach(async () => {
    // Drive the helper from BOTH pipelines with identical inputs.
    recAgentic = makeRecorder()
    const optsA = {
      ...buildOpts(),
      pipelineKind: 'agentic' as const,
      writer: recAgentic.writer,
      emit: recAgentic.emit,
    }
    await runOnFinishWriteThrough(optsA, makeDeps(recAgentic))

    recSinglePass = makeRecorder()
    const optsL = {
      ...buildOpts(),
      pipelineKind: 'single_pass' as const,
      writer: recSinglePass.writer,
      emit: recSinglePass.emit,
    }
    await runOnFinishWriteThrough(optsL, makeDeps(recSinglePass))
  })

  // -------------------------------------------------------------------------
  // GOLDEN: identical call lists across both pipeline shapes.
  // -------------------------------------------------------------------------
  it('GOLDEN: persistence calls are identical across both pipelines', () => {
    const filt = (calls: CapturedCall[]) =>
      calls.filter((c) => c.fn === 'persistence.writeMessages')
    expect(filt(recAgentic.calls)).toEqual(filt(recSinglePass.calls))
    // Both must persist exactly once.
    expect(filt(recAgentic.calls)).toHaveLength(1)
  })

  it('GOLDEN: context_assembly_log writes are identical across both pipelines', () => {
    const filt = (calls: CapturedCall[]) =>
      calls.filter((c) => c.fn === 'contextAssemblyLog')
    expect(filt(recAgentic.calls)).toEqual(filt(recSinglePass.calls))
    expect(filt(recAgentic.calls)).toHaveLength(1)
  })

  it('GOLDEN: pricing.computeUsd / getPricing calls are identical (Observatory cost)', () => {
    const filt = (calls: CapturedCall[]) =>
      calls.filter((c) => c.fn === 'pricing.getPricing' || c.fn === 'pricing.computeUsd')
    expect(filt(recAgentic.calls)).toEqual(filt(recSinglePass.calls))
    expect(filt(recAgentic.calls)).toHaveLength(2) // getPricing + computeUsd
  })

  it('GOLDEN: MSR snippet resolution + per-citation data parts are identical', () => {
    const filt = (calls: CapturedCall[]) =>
      calls.filter((c) => c.fn === 'fetchMsrSnippets')
    expect(filt(recAgentic.calls)).toEqual(filt(recSinglePass.calls))

    const citationEvents = (events: CapturedEvent[]) =>
      events.filter((e) => e.type === 'data-citation')
    expect(citationEvents(recAgentic.events)).toEqual(citationEvents(recSinglePass.events))
    expect(citationEvents(recAgentic.events)).toHaveLength(2) // SIG.MSR.142 + SIG.MSR.207
  })

  it('GOLDEN: prediction ledger appends are identical (blind-mode)', () => {
    const filt = (calls: CapturedCall[]) =>
      calls.filter((c) => c.fn === 'predictionLedger')
    expect(filt(recAgentic.calls)).toEqual(filt(recSinglePass.calls))
    expect(filt(recAgentic.calls)).toHaveLength(1)
  })

  it('GOLDEN: pendingStreamWriter.clear is invoked identically by both pipelines', () => {
    const filt = (calls: CapturedCall[]) =>
      calls.filter((c) => c.fn === 'pendingStreamWriter.clear')
    expect(filt(recAgentic.calls)).toEqual(filt(recSinglePass.calls))
    expect(filt(recAgentic.calls)).toHaveLength(1)
  })

  it('GOLDEN: title generation is requested identically by both pipelines (first turn)', () => {
    const filt = (calls: CapturedCall[]) =>
      calls.filter((c) => c.fn === 'title.generate')
    expect(filt(recAgentic.calls)).toEqual(filt(recSinglePass.calls))
    expect(filt(recAgentic.calls)).toHaveLength(1)
  })

  it('GOLDEN: full data-part event stream is identical across both pipelines', () => {
    // Compare the data-part stream excluding the data-cost monetary field
    // (deterministic via mock — included). All other parts must match.
    expect(recAgentic.events).toEqual(recSinglePass.events)
  })

  // -------------------------------------------------------------------------
  // SHAPE: assert each required write-through actually fires (catches the
  // pre-cutover gaps where the adapter path skipped these steps entirely).
  // -------------------------------------------------------------------------
  it('SHAPE: data-cost is emitted (closes adapter GAP-1)', () => {
    const costs = recAgentic.events.filter((e) => e.type === 'data-cost')
    expect(costs).toHaveLength(1)
    expect(costs[0].data).toMatchObject({ model: 'claude-3-5-sonnet', dollars: 0.0042 })
  })

  it('SHAPE: persistence carries lastAssistantMetadata (closes adapter GAP-2)', () => {
    const persist = recAgentic.calls.find((c) => c.fn === 'persistence.writeMessages')
    expect(persist).toBeDefined()
    const args = persist!.args as { lastAssistantMetadata?: Record<string, unknown> }
    expect(args.lastAssistantMetadata).toBeDefined()
    expect(args.lastAssistantMetadata).toMatchObject({ custom: { model: 'claude-3-5-sonnet' } })
  })

  it('SHAPE: per-citation data parts are emitted (closes adapter GAP-3)', () => {
    const cites = recAgentic.events.filter((e) => e.type === 'data-citation')
    expect(cites).toHaveLength(2)
    const ids = cites.map((c) => (c.data as { signal_id: string }).signal_id).sort()
    expect(ids).toEqual(['SIG.MSR.142', 'SIG.MSR.207'])
  })

  it('SHAPE: data-correction is emitted when synthesis marker present (closes adapter GAP-4)', () => {
    const corrections = recAgentic.events.filter((e) => e.type === 'data-correction')
    expect(corrections).toHaveLength(1)
    expect(corrections[0].data).toMatchObject({
      original_claim: 'Moon in 7H',
      corrected_claim: 'Moon in 8H',
    })
  })

  it('SHAPE: pendingStreamWriter.clear fires (closes adapter GAP-5)', () => {
    const clears = recAgentic.calls.filter((c) => c.fn === 'pendingStreamWriter.clear')
    expect(clears).toHaveLength(1)
  })

  it('SHAPE: blind-mode prediction ledger entry is appended (closes adapter GAP-6)', () => {
    const ledger = recAgentic.calls.filter((c) => c.fn === 'predictionLedger')
    expect(ledger).toHaveLength(1)
    expect(ledger[0].args).toMatchObject({
      mode: 'blind',
      chart_id: '00000000-0000-0000-0000-000000000003',
      conversation_id: '00000000-0000-0000-0000-000000000002',
      query: 'And the Saturn timing?',
    })
  })

  it('SHAPE: prediction candidate is emitted (>= 0.5 score)', () => {
    const preds = recAgentic.events.filter((e) => e.type === 'data-prediction-candidate')
    expect(preds.length).toBeGreaterThanOrEqual(1)
  })

  // -------------------------------------------------------------------------
  // GUARDS: blind-mode off → no ledger write; first-turn off → no title gen.
  // -------------------------------------------------------------------------
  it('GUARD: lelContextEnabled=true suppresses blind-mode ledger write', async () => {
    const rec = makeRecorder()
    const opts = {
      ...buildOpts({ lelContextEnabled: true }),
      writer: rec.writer,
      emit: rec.emit,
    }
    await runOnFinishWriteThrough(opts, makeDeps(rec))
    const ledger = rec.calls.filter((c) => c.fn === 'predictionLedger')
    expect(ledger).toHaveLength(0)
  })

  it('GUARD: isFirstTurn=false suppresses title generation', async () => {
    const rec = makeRecorder()
    const opts = {
      ...buildOpts({ isFirstTurn: false }),
      writer: rec.writer,
      emit: rec.emit,
    }
    await runOnFinishWriteThrough(opts, makeDeps(rec))
    const titleGen = rec.calls.filter((c) => c.fn === 'title.generate')
    expect(titleGen).toHaveLength(0)
    const titleEvents = rec.events.filter((e) => e.type === 'data-title')
    expect(titleEvents).toHaveLength(0)
  })

  it('GUARD: null synthUsage suppresses data-cost emit (adapter path with no usageHolder)', async () => {
    const rec = makeRecorder()
    const opts = {
      ...buildOpts({ synthUsage: null }),
      writer: rec.writer,
      emit: rec.emit,
    }
    await runOnFinishWriteThrough(opts, makeDeps(rec))
    const costs = rec.events.filter((e) => e.type === 'data-cost')
    expect(costs).toHaveLength(0)
    // Other write-throughs still fire.
    expect(rec.calls.filter((c) => c.fn === 'persistence.writeMessages')).toHaveLength(1)
    expect(rec.calls.filter((c) => c.fn === 'contextAssemblyLog')).toHaveLength(1)
  })
})
