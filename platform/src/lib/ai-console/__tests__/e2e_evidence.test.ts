import { describe, expect, it } from 'vitest'
import {
  assertSafeRoutingEvidence,
  parseConsultTerminal,
  parsePariprashnaTerminal,
} from '../../../../scripts/ai-console/e2e_evidence'

const target = { kind: 'provider_model' as const, providerId: 'openai', connectionId: 'connection-1', modelId: 'model-1' }
const roles = { synthesizer: target, planner: target, deep_planner: target, worker: target }

describe('real local E2E evidence contract', () => {
  it('requires a successful Pariprashna turn.close and returns its exact turn id', () => {
    const text = [
      'event: turn.open\ndata: {"type":"turn.open","turn_id":"10000000-0000-4000-8000-000000000001"}\n',
      'event: turn.commit\ndata: {"type":"turn.commit","turn_id":"10000000-0000-4000-8000-000000000001","status":"ok"}\n',
      'event: turn.persisted\ndata: {"type":"turn.persisted","turn_id":"10000000-0000-4000-8000-000000000001","status":"durable"}\n',
      'event: turn.close\ndata: {"type":"turn.close","turn_id":"10000000-0000-4000-8000-000000000001","status":"ok"}\n',
    ].join('\n')
    expect(parsePariprashnaTerminal(text)).toBe('10000000-0000-4000-8000-000000000001')
    expect(() => parsePariprashnaTerminal(text.replace('"type":"turn.close","turn_id":"10000000-0000-4000-8000-000000000001","status":"ok"',
      '"type":"turn.close","turn_id":"10000000-0000-4000-8000-000000000001","status":"error"'))).toThrow('AIC_E2E_TURN_NOT_SUCCESSFUL')
    expect(() => parsePariprashnaTerminal(text.replace(/event: turn.persisted[\s\S]*?\n\n/, ''))).toThrow('AIC_E2E_TURN_NOT_SUCCESSFUL')
  })

  it('requires a semantic Consult finish event rather than accepting generic 2xx', () => {
    expect(parseConsultTerminal('data: {"type":"text-delta","delta":"hello"}\n\ndata: {"type":"finish","finishReason":"stop"}\n')).toBe(true)
    expect(() => parseConsultTerminal('data: {"type":"text-delta","delta":"hello"}\n')).toThrow('AIC_E2E_TERMINAL_EVENT_MISSING')
  })

  it('matches immutable selection and four role identities while rejecting fallback or failed receipts', () => {
    const evidence = {
      userId: 'owner-1', correlationId: '10000000-0000-4000-8000-000000000001',
      selection: { kind: 'explicit', choice: { kind: 'provider_model', connectionId: 'connection-1', modelId: 'model-1' } },
      resolvedChoice: { kind: 'provider_model', connectionId: 'connection-1', modelId: 'model-1' },
      roles,
      invocations: [
        { role: 'planner', status: 'succeeded' }, { role: 'synthesizer', status: 'succeeded' },
      ],
      observatory: [
        { role: 'planner', providerId: 'openai', modelId: 'model-1', fallbackUsed: false, status: 'success' },
        { role: 'synthesizer', providerId: 'openai', modelId: 'model-1', fallbackUsed: false, status: 'success' },
      ],
    } as const
    expect(assertSafeRoutingEvidence(evidence, {
      userId: 'owner-1', correlationId: evidence.correlationId, selection: evidence.selection,
      resolvedChoice: evidence.resolvedChoice, roles,
    })).toBe(true)
    expect(() => assertSafeRoutingEvidence({ ...evidence, observatory: [{ ...evidence.observatory[0], fallbackUsed: true }] }, {
      userId: 'owner-1', correlationId: evidence.correlationId, selection: evidence.selection,
      resolvedChoice: evidence.resolvedChoice, roles,
    })).toThrow('AIC_E2E_ROUTING_EVIDENCE_INVALID')
    expect(() => assertSafeRoutingEvidence(evidence, {
      userId: 'owner-1', correlationId: evidence.correlationId, selection: evidence.selection,
      resolvedChoice: { ...evidence.resolvedChoice, modelId: 'wrong' }, roles,
    })).toThrow('AIC_E2E_ROUTING_EVIDENCE_INVALID')
  })

  it('accepts the governed Google snapshot to Gemini Observatory normalization', () => {
    const googleTarget = { ...target, providerId: 'google' }
    const googleRoles = { synthesizer: googleTarget, planner: googleTarget, deep_planner: googleTarget, worker: googleTarget }
    const selection = { kind: 'explicit' as const, choice: { kind: 'provider_model' as const, connectionId: 'connection-1', modelId: 'model-1' } }
    const evidence = {
      userId: 'owner-1', correlationId: 'turn-1', selection, resolvedChoice: selection.choice, roles: googleRoles,
      invocations: [{ role: 'planner', status: 'succeeded' }, { role: 'synthesizer', status: 'succeeded' }],
      observatory: [
        { role: 'planner', providerId: 'gemini', modelId: 'model-1', fallbackUsed: false, status: 'success' },
        { role: 'synthesizer', providerId: 'gemini', modelId: 'model-1', fallbackUsed: false, status: 'success' },
      ],
    }
    expect(assertSafeRoutingEvidence(evidence, {
      userId: 'owner-1', correlationId: 'turn-1', selection, resolvedChoice: selection.choice, roles: googleRoles,
    })).toBe(true)
  })
})
