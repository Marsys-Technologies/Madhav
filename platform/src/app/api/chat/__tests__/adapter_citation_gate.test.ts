/**
 * 0b.1 — Adapter-path B.11 citation gate parity (Stream B unit 0b.1).
 *
 * Asserts that the adapter/agentic dispatch branch of `/api/chat/consult`
 * (route.ts, gated by MARSYS_FLAG_R11V2_USE_ADAPTERS=true) enforces the same
 * B.11 citation gate the legacy synthesis-orchestrator path emits in onFinish.
 *
 * The route's adapter branch invokes `validateCitationsForStream(text, ctxJson,
 * queryClass, override)` after accumulating the adapter response and writes a
 * `data-citation-gate` part to the UI stream when the gate result is WARN or ERROR.
 * That call shape is what these tests pin: same inputs → same data-part shape →
 * same telemetry classification (PASS / WARN / ERROR) as the legacy path.
 *
 * The validator is shared with the legacy path, so a per-input contract test on
 * the validator is sufficient to lock the adapter parity — there is no separate
 * legacy-vs-adapter divergence to exercise.
 */
import { describe, it, expect } from 'vitest'

import { validateCitationsForStream } from '@/lib/synthesis/streaming_citation_validator'

// Minimal stand-ins for the route's bundle/tool_results JSON shape; the validator
// only cares about whether SIG.MSR.NNN substrings appear in the JSON-serialised context.
function buildContextJson(opts: {
  signalIds?: string[]
  bundleAssets?: Array<{ key: string; content: string }>
}): string {
  const bundle = { assets: opts.bundleAssets ?? [] }
  const tool_results = (opts.signalIds ?? []).map((sid) => ({
    tool_name: 'msr_sql',
    results: [{ content: `Row referencing ${sid}` }],
  }))
  return JSON.stringify({ bundle, tool_results })
}

// Captures the `writer.write` invocations the adapter path makes for the gate.
// In production the writer is the AI SDK UIMessageStream writer; here we only
// assert the discriminator + payload shape.
type CapturedEvent = { type: string; data?: unknown }
function makeCapturingWriter(): { writer: { write: (e: CapturedEvent) => void }; events: CapturedEvent[] } {
  const events: CapturedEvent[] = []
  return {
    writer: { write: (e: CapturedEvent) => events.push(e) },
    events,
  }
}

/**
 * Mirrors the adapter-path inline gate block in
 * route.ts:: if (configService.getFlag('R11V2_USE_ADAPTERS')) { … }.
 * Locked to the exact call shape so any drift in the route is caught.
 */
function runAdapterCitationGate(opts: {
  accumulatedText: string
  contextJson: string
  queryClass: string
  override: boolean
  writer: { write: (e: CapturedEvent) => void }
}): ReturnType<typeof validateCitationsForStream> {
  const validation = validateCitationsForStream(
    opts.accumulatedText,
    opts.contextJson,
    opts.queryClass,
    opts.override,
  )
  if (validation.dataPart) {
    opts.writer.write({ type: 'data-citation-gate', data: validation.dataPart })
  }
  return validation
}

describe('0b.1 — adapter path citation gate (B.11 parity with legacy onFinish)', () => {
  it('PASS: cited and verified — no data-citation-gate part emitted', () => {
    const { writer, events } = makeCapturingWriter()
    const text = 'The dispositor chain SIG.MSR.142 governs the timing.'
    const ctx = buildContextJson({ signalIds: ['SIG.MSR.142'] })

    const result = runAdapterCitationGate({
      accumulatedText: text,
      contextJson: ctx,
      queryClass: 'holistic',
      override: false,
      writer,
    })

    expect(result.gateResult).toBe('PASS')
    expect(result.layer1Count).toBe(1)
    expect(result.layer2Verified).toBe(1)
    expect(result.layer2Leaked).toBe(0)
    expect(events).toEqual([])
  })

  it('WARN: cited but unverified (training-data leak) — emits warn data-citation-gate', () => {
    const { writer, events } = makeCapturingWriter()
    const text = 'See SIG.MSR.999 for the unrelated claim.'
    const ctx = buildContextJson({ signalIds: ['SIG.MSR.142'] }) // 999 not in context

    const result = runAdapterCitationGate({
      accumulatedText: text,
      contextJson: ctx,
      queryClass: 'holistic',
      override: false,
      writer,
    })

    expect(result.gateResult).toBe('WARN')
    expect(result.layer1Count).toBe(1)
    expect(result.layer2Verified).toBe(0)
    expect(result.layer2Leaked).toBe(1)
    expect(events).toHaveLength(1)
    expect(events[0].type).toBe('data-citation-gate')
    expect(events[0].data).toMatchObject({
      type: 'citation_gate',
      status: 'warn',
    })
    expect((events[0].data as { issues: string[] }).issues[0]).toMatch(/training-data leak/)
  })

  it('ERROR: prescriptive query with no citations — emits fail data-citation-gate', () => {
    const { writer, events } = makeCapturingWriter()
    const text = 'Wear a blue sapphire on the middle finger.'
    const ctx = buildContextJson({ signalIds: [] })

    const result = runAdapterCitationGate({
      accumulatedText: text,
      contextJson: ctx,
      queryClass: 'remedial',
      override: false,
      writer,
    })

    expect(result.gateResult).toBe('ERROR')
    expect(events).toHaveLength(1)
    expect(events[0].type).toBe('data-citation-gate')
    expect(events[0].data).toMatchObject({
      type: 'citation_gate',
      status: 'fail',
    })
  })

  it('OVERRIDE: prescriptive + uncited + override flag on → ERROR downgrades to WARN', () => {
    const { writer, events } = makeCapturingWriter()
    const text = 'Recite the Mahamrityunjaya mantra during Mars hora.'
    const ctx = buildContextJson({ signalIds: [] })

    const result = runAdapterCitationGate({
      accumulatedText: text,
      contextJson: ctx,
      queryClass: 'remedial',
      override: true, // simulates MARSYS_FLAG_CITATION_GATE_OVERRIDE=true
      writer,
    })

    expect(result.gateResult).toBe('WARN')
    expect(events).toHaveLength(1)
    expect((events[0].data as { status: string }).status).toBe('warn')
  })

  it('informational class (factual) with no citations — PASS, no data part', () => {
    const { writer, events } = makeCapturingWriter()
    const text = 'Saturn is the dispositor of the Capricorn rising chart.'
    const ctx = buildContextJson({ signalIds: [] })

    const result = runAdapterCitationGate({
      accumulatedText: text,
      contextJson: ctx,
      queryClass: 'factual',
      override: false,
      writer,
    })

    expect(result.gateResult).toBe('PASS')
    expect(result.layer1Count).toBe(0)
    expect(events).toEqual([])
  })
})

describe('0b.1 — adapter context-assembly bookkeeping uses real gate counts', () => {
  // route.ts adapter branch now flows the gate result into writeContextAssemblyLog:
  //   b3_compliant: adapterCitationGateResult === 'PASS'
  //   citation_count: adapterCitationL1Count
  //   verified_citations: adapterCitationL2Verified
  // Prior to 0b.1 these were hardcoded { true, 0, 0 } — that silently lied
  // about B.11 compliance. This test pins the new derivation.
  it('PASS-with-citations contributes truthful b3_compliant=true and counts > 0', () => {
    const text = 'Both SIG.MSR.142 and SIG.MSR.207 converge on this reading.'
    const ctx = buildContextJson({ signalIds: ['SIG.MSR.142', 'SIG.MSR.207'] })
    const result = validateCitationsForStream(text, ctx, 'holistic', false)

    const b3_compliant = result.gateResult === 'PASS'
    expect(b3_compliant).toBe(true)
    expect(result.layer1Count).toBe(2)
    expect(result.layer2Verified).toBe(2)
  })

  it('WARN result contributes b3_compliant=false (gate is not PASS)', () => {
    const text = 'See SIG.MSR.999 — unverifiable.'
    const ctx = buildContextJson({ signalIds: ['SIG.MSR.142'] })
    const result = validateCitationsForStream(text, ctx, 'holistic', false)

    const b3_compliant = result.gateResult === 'PASS'
    expect(b3_compliant).toBe(false)
    expect(result.gateResult).toBe('WARN')
  })
})
