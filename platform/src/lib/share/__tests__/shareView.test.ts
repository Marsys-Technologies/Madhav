/**
 * SS N-379 (ii) — a share viewer receives ONLY rendered conversation text.
 * buildShareViewMessages is an ALLOWLIST: it builds a NEW minimal object per
 * message and never spreads the loader's message.
 */
import { describe, expect, it } from 'vitest'
import { buildShareViewMessages } from '../shareView'

const TOOL_IN = 'RAW_RETRIEVAL_INPUT_secret'
const TOOL_OUT = 'RAW_RETRIEVAL_OUTPUT_secret'

function fixture() {
  return [
    {
      id: '11111111-aaaa-bbbb-cccc-000000000001',
      role: 'user',
      parts: [
        { type: 'text', text: 'What about Saturn?' },
        { type: 'file', mediaType: 'image/png', url: 'data:image/png;base64,FILEPAYLOAD' },
      ],
      metadata: { created_at: '2026-10-01T00:00:00Z', role: 'super_admin' },
    },
    {
      id: '11111111-aaaa-bbbb-cccc-000000000002',
      role: 'assistant',
      parts: [
        { type: 'step-start' },
        { type: 'tool-ganita_planet_get', toolCallId: 'call-1', state: 'output-available', input: { q: TOOL_IN }, output: { r: TOOL_OUT } },
        { type: 'dynamic-tool', toolName: 'x', toolCallId: 'call-2', state: 'output-available', input: TOOL_IN, output: TOOL_OUT },
        { type: 'data-trace', data: { secret: 'DATA_PART_secret' } },
        { type: 'source-url', sourceId: 's', url: 'https://example.invalid/src' },
        { type: 'reasoning', text: 'REASONING_visible_when_not_hidden' },
        { type: 'text', text: 'Saturn is exalted in Libra.', providerMetadata: { anthropic: { cacheControl: 'X' } } },
      ],
      metadata: { role: 'super_admin', model: 'MODEL_xyz', style: 'STYLE_xyz', query_id: 'QID_123', created_at: 't', truncated: false },
    },
    // A message carrying an admin-like RAW role: never rendered by MessageList, so never shipped.
    { id: 'x', role: 'super_admin', parts: [{ type: 'text', text: 'ADMIN_ROLE_MESSAGE_TEXT' }], metadata: {} },
    { id: 'y', role: 'system', parts: [{ type: 'text', text: 'SYSTEM_PROMPT_TEXT' }], metadata: {} },
    // Tool-only assistant turn: nothing renderable remains, so no empty bubble.
    { id: 'z', role: 'assistant', parts: [{ type: 'tool-foo', toolCallId: 'c', state: 'output-available', input: TOOL_IN, output: TOOL_OUT }], metadata: {} },
  ]
}

describe('buildShareViewMessages', () => {
  it('emits only id, display role and text/reasoning parts as NEW objects', () => {
    const out = buildShareViewMessages(fixture(), false, false)
    expect(out).toEqual([
      { id: 'm0', role: 'user', parts: [{ type: 'text', text: 'What about Saturn?' }] },
      {
        id: 'm1',
        role: 'assistant',
        parts: [
          { type: 'reasoning', text: 'REASONING_visible_when_not_hidden' },
          { type: 'text', text: 'Saturn is exalted in Libra.' },
        ],
      },
    ])
  })

  it('the serialized output carries no tool, data, metadata, model/style/query or raw-role strings', () => {
    const s = JSON.stringify(buildShareViewMessages(fixture(), false, false))
    for (const banned of [
      'tool-', 'dynamic-tool', 'toolCallId', 'data-', 'metadata', 'providerMetadata', 'step-start', 'source-url', 'file',
      TOOL_IN, TOOL_OUT, 'DATA_PART_secret', 'FILEPAYLOAD', 'MODEL_xyz', 'STYLE_xyz', 'QID_123', 'created_at',
      'super_admin', 'isAdmin', 'system', 'ADMIN_ROLE_MESSAGE_TEXT', 'SYSTEM_PROMPT_TEXT', '11111111-aaaa',
    ]) {
      expect(s, banned).not.toContain(banned)
    }
  })

  it('role is an opaque display value: only "user" or "assistant", never the raw string', () => {
    for (const m of buildShareViewMessages(fixture(), true, true)) {
      expect(['user', 'assistant']).toContain(m.role)
      expect(Object.keys(m).sort()).toEqual(['id', 'parts', 'role'])
    }
  })

  it('does not spread the loader message: unknown extra fields never survive', () => {
    const msgs = [{ id: 'a', role: 'assistant', parts: [{ type: 'text', text: 'hi' }], metadata: {}, evil: 'EXTRA_FIELD', content: 'LEGACY_CONTENT' }]
    const s = JSON.stringify(buildShareViewMessages(msgs, false, false))
    expect(s).not.toContain('EXTRA_FIELD')
    expect(s).not.toContain('LEGACY_CONTENT')
  })

  it('applies the hide filters first (reasoning part + methodology fence removed)', () => {
    const msgs = [
      {
        id: 'a',
        role: 'assistant',
        parts: [
          { type: 'reasoning', text: 'SECRET_REASONING' },
          { type: 'text', text: 'Answer.\n\n```marsys_methodology_block\nSECRET_METHOD\n```\n' },
        ],
        metadata: { methodology_block: 'SECRET_METHOD' },
      },
    ]
    const s = JSON.stringify(buildShareViewMessages(msgs, true, true))
    expect(s).toContain('Answer.')
    expect(s).not.toContain('SECRET_REASONING')
    expect(s).not.toContain('SECRET_METHOD')
  })

  it('does not mutate its input', () => {
    const f = fixture()
    const snapshot = JSON.stringify(f)
    buildShareViewMessages(f, true, true)
    expect(JSON.stringify(f)).toBe(snapshot)
  })

  it('tolerates junk input (non-array parts, null entries, non-string text)', () => {
    const junk = [null, 'str', { role: 'user' }, { role: 'user', parts: 'nope' }, { role: 'assistant', parts: [null, { type: 'text', text: 5 }] }]
    expect(buildShareViewMessages(junk as unknown[], false, false)).toEqual([])
  })
})
