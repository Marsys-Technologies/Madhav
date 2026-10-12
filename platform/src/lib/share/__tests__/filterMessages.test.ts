// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { filterMessages } from '../filterMessages'

const FENCE = (body: string) => '```marsys_methodology_block\n' + body + '\n```'

describe('filterMessages — what hide_methodology / hide_reasoning really remove (SS N-376 item 5)', () => {
  it('strips the marsys_methodology_block fence from assistant TEXT PARTS (the persisted shape)', () => {
    const msgs = [
      { id: 'a', role: 'assistant', parts: [{ type: 'text', text: `Answer.\n\n${FENCE('SECRET')}\n` }], metadata: {} },
    ]
    const out = filterMessages(msgs, false, true)
    expect(JSON.stringify(out)).not.toContain('SECRET')
    expect(JSON.stringify(out)).not.toContain('marsys_methodology_block')
    expect((out[0].parts[0] as { text: string }).text).toContain('Answer.')
  })

  it('strips an UNTERMINATED methodology fence (truncated response) to the end of the text', () => {
    const msgs = [
      { id: 'a', role: 'assistant', parts: [{ type: 'text', text: 'Answer.\n```marsys_methodology_block\nSECRET never closed' }] },
    ]
    expect(JSON.stringify(filterMessages(msgs, false, true))).not.toContain('SECRET')
  })

  it('strips a "## Methodology" section even when it is the LAST section (the old regex used \\Z, which JS reads as a literal Z)', () => {
    const msgs = [
      { id: 'a', role: 'assistant', parts: [{ type: 'text', text: 'Answer.\n\n## Methodology\nSECRET steps here' }] },
    ]
    expect(JSON.stringify(filterMessages(msgs, false, true))).not.toContain('SECRET')
  })

  it('stops the "## Methodology" strip at the next heading', () => {
    const msgs = [
      { id: 'a', role: 'assistant', parts: [{ type: 'text', text: '## Methodology\nSECRET\n## Remedies\nKEEP_ME' }] },
    ]
    const s = JSON.stringify(filterMessages(msgs, false, true))
    expect(s).not.toContain('SECRET')
    expect(s).toContain('KEEP_ME')
  })

  it('removes metadata.methodology_block when hiding methodology', () => {
    const msgs = [
      { id: 'a', role: 'assistant', parts: [{ type: 'text', text: 'x' }], metadata: { methodology_block: 'SECRET', model: 'm' } },
    ]
    const out = filterMessages(msgs, false, true)
    expect(JSON.stringify(out)).not.toContain('SECRET')
    expect((out[0].metadata as Record<string, unknown>).model).toBe('m')
  })

  it('drops reasoning parts AND inline reasoning markers from text', () => {
    const msgs = [
      {
        id: 'a',
        role: 'assistant',
        parts: [
          { type: 'reasoning', text: 'SECRET_A' },
          { type: 'text', text: 'Before ‹reasoning›SECRET_B‹/reasoning› after.' },
        ],
      },
    ]
    const out = filterMessages(msgs, true, false)
    const s = JSON.stringify(out)
    expect(s).not.toContain('SECRET_A')
    expect(s).not.toContain('SECRET_B')
    expect(s).toContain('Before')
    expect(s).toContain('after.')
  })

  it('drops a text part that is empty after stripping, never leaving an empty shell', () => {
    const msgs = [{ id: 'a', role: 'assistant', parts: [{ type: 'text', text: FENCE('SECRET') }] }]
    expect(filterMessages(msgs, false, true)[0].parts).toHaveLength(0)
  })

  it('leaves user messages alone and does not mutate its input', () => {
    const msgs = [
      { id: 'u', role: 'user', parts: [{ type: 'text', text: FENCE('USER_OWN') }] },
      { id: 'a', role: 'assistant', parts: [{ type: 'text', text: FENCE('SECRET') }] },
    ]
    const snapshot = JSON.stringify(msgs)
    const out = filterMessages(msgs, true, true)
    expect(JSON.stringify(out[0])).toContain('USER_OWN')
    expect(JSON.stringify(msgs)).toBe(snapshot)
  })

  it('both flags false returns the input untouched', () => {
    const msgs = [{ id: 'a', role: 'assistant', parts: [{ type: 'reasoning', text: 'R' }] }]
    expect(filterMessages(msgs, false, false)).toBe(msgs)
  })
})
