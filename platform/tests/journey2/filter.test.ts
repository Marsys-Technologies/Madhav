import { describe, it, expect } from 'vitest'
import { filterMessages } from '@/lib/share/filterMessages'
describe('Sharing disclosure follows real UIMessage text', () => {
  it('removes methodology through end of message and preserves the next peer section', () => {
    const messages = [{ role: 'assistant', parts: [{ type: 'text', text: 'Reading\n## Methodology\nprivate method\n### Details\nmore\n## Outcome\npublic outcome' }, { type: 'reasoning', text: 'private reasoning' }] }]
    expect(filterMessages(messages, true, true)[0].parts).toEqual([{ type: 'text', text: 'Reading\n## Outcome\npublic outcome' }])
    expect(filterMessages([{ role: 'assistant', parts: [{ type: 'text', text: 'Reading\n## Methodology\nprivate' }] }], false, true)[0].parts).toEqual([{ type: 'text', text: 'Reading' }])
    expect(messages[0].parts).toHaveLength(2)
  })
})
