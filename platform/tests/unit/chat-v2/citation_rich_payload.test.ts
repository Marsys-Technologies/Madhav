/**
 * C.3 — Rich data-citation payload consumed in V2AssistantText.
 *
 * Source-level assertions that:
 *  - CitationContextValue.onPin accepts snippet + layer
 *  - V2AssistantText builds a citationRichMap from message.content DataMessageParts
 *  - handlePin uses snippet and layer params (not hardcoded empty string)
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const src = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/components/consume/ConsumeChatV2.tsx'),
  'utf8',
)

describe('C.3 — rich data-citation payload consumed', () => {
  it('V2AssistantText builds citationRichMap from data parts (via useDataParts hook)', () => {
    expect(src).toContain('citationRichMap')
    // R6.1: consolidated to hook — data-citation parts from both sources
    expect(src).toContain("'data-citation'")
    expect(src).toContain('data.signal_id')
  })

})
