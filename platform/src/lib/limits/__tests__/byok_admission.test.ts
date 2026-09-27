import { beforeEach, describe, expect, it, vi } from 'vitest'

const checkRpm = vi.hoisted(() => vi.fn())
vi.mock('@/lib/mcp/rate_limiter_core', () => ({ checkRpm }))
import {
  admitByokTurn, isByokEvidencePayloadWithinLimit, isByokEvidenceWithinLimit,
  isMcpEvidenceEnvelopeWithinLimit, MCP_BYOK_EVIDENCE_ENVELOPE_MAX_BYTES, validateByokUiMessages,
} from '../byok_admission'

describe('admitByokTurn', () => {
  it('rejects oversized normalized assistant and tool history before turn preparation', async () => {
    const messages = [
      { id: 'system-1', role: 'system', parts: [{ type: 'text', text: 'system context' }] },
      { id: 'assistant-1', role: 'assistant', parts: [
        { type: 'reasoning', text: 'r'.repeat(1_100_000) },
        { type: 'dynamic-tool', toolName: 'fixture', toolCallId: 'call-1', state: 'output-available',
          input: { query: 'q'.repeat(500_000) }, output: { text: 'o'.repeat(500_000) } },
      ] },
      { id: 'user-1', role: 'user', parts: [{ type: 'text', text: 'short question' }] },
    ]

    await expect(validateByokUiMessages(messages)).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
  })

  it('returns only structurally valid normalized messages within the UTF-8 cap', async () => {
    await expect(validateByokUiMessages([
      { id: 'assistant-1', role: 'assistant', ignored: 'strip-me', parts: [
        { type: 'reasoning', text: 'careful' },
        { type: 'dynamic-tool', toolName: 'fixture', toolCallId: 'call-1', state: 'output-available',
          input: { query: 'hello' }, output: { answer: 'world' } },
      ] },
      { id: 'user-1', role: 'user', parts: [{ type: 'text', text: 'क्या?' }] },
    ])).resolves.toEqual([
      { id: 'assistant-1', role: 'assistant', parts: [
        { type: 'reasoning', text: 'careful' },
        { type: 'dynamic-tool', toolName: 'fixture', toolCallId: 'call-1', state: 'output-available',
          input: { query: 'hello' }, output: { answer: 'world' } },
      ] },
      { id: 'user-1', role: 'user', parts: [{ type: 'text', text: 'क्या?' }] },
    ])
  })

  it('rejects malformed message parts instead of silently ignoring them', async () => {
    await expect(validateByokUiMessages([
      { id: 'assistant-1', role: 'assistant', parts: [{ type: 'unknown-part', text: 'hidden' }] },
    ])).rejects.toMatchObject({ code: 'AI_EXECUTION_FAILED' })
  })

  it('enforces the same evidence ceiling after hydration without consuming admission', () => {
    expect(isByokEvidenceWithinLimit(2_000_000)).toBe(true)
    expect(isByokEvidenceWithinLimit(2_000_001)).toBe(false)
    expect(isByokEvidenceWithinLimit(-1)).toBe(false)
  })

  it('measures hydrated evidence as UTF-8 bytes rather than JavaScript characters', () => {
    expect(isByokEvidencePayloadWithinLimit({ text: 'a'.repeat(1_999_980) })).toBe(true)
    expect(isByokEvidencePayloadWithinLimit({ text: '🙏'.repeat(500_000) })).toBe(false)
  })

  it('caps the MCP evidence wire envelope independently of model context metadata', () => {
    const prefixBytes = Buffer.byteLength(JSON.stringify({ evidence: '' }), 'utf8')
    expect(isMcpEvidenceEnvelopeWithinLimit({
      evidence: 'a'.repeat(MCP_BYOK_EVIDENCE_ENVELOPE_MAX_BYTES - prefixBytes),
      model_context_tokens: 1,
    })).toBe(false)
    expect(isMcpEvidenceEnvelopeWithinLimit({ evidence: 'concise', model_context_tokens: 1 })).toBe(true)
  })
  beforeEach(() => checkRpm.mockReset().mockReturnValue({ allowed: true }))

  it('rejects hard-cap violations before consuming the rate counter', () => {
    expect(admitByokTurn({ userId: 'a', questionChars: 32_001 })).toEqual({
      allowed: false, code: 'AI_EXECUTION_FAILED',
    })
    expect(checkRpm).not.toHaveBeenCalled()
  })

  it('admits only two concurrent turns and release is idempotent', () => {
    const first = admitByokTurn({ userId: 'b', questionChars: 1 })
    const second = admitByokTurn({ userId: 'b', questionChars: 1 })
    expect(first.allowed).toBe(true)
    expect(second.allowed).toBe(true)
    expect(admitByokTurn({ userId: 'b', questionChars: 1 })).toMatchObject({ allowed: false, code: 'AI_RATE_LIMITED' })
    if (first.allowed) { first.release(); first.release() }
    const replacement = admitByokTurn({ userId: 'b', questionChars: 1 })
    expect(replacement.allowed).toBe(true)
    if (second.allowed) second.release()
    if (replacement.allowed) replacement.release()
  })
})
