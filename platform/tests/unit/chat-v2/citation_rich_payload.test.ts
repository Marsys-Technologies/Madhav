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
  it('CitationContextValue.onPin accepts snippet and layer optional params', () => {
    expect(src).toContain("onPin: (n: number, signalId: string, snippet?: string, layer?: 'L1' | 'L2.5') => void")
  })

  it('handlePin uses snippet and layer params (not hardcoded empty string)', () => {
    const pinBlock = src.slice(
      src.indexOf('const handlePin = useCallback'),
      src.indexOf('const handlePin = useCallback') + 400,
    )
    expect(pinBlock).toContain('snippet = \'\'')
    expect(pinBlock).toContain('layer:')
    expect(pinBlock).not.toContain("snippet: ''")
  })

  it('V2AssistantText builds citationRichMap from data parts (via useDataParts hook)', () => {
    expect(src).toContain('citationRichMap')
    // R6.1: consolidated to hook — data-citation parts from both sources
    expect(src).toContain("'data-citation'")
    expect(src).toContain('data.signal_id')
  })

  it('V2AssistantText calls onPin with enriched snippet and layer', () => {
    expect(src).toContain('enrichedOnPin')
    expect(src).toContain('rich?.snippet')
    expect(src).toContain('rich?.layer')
  })

  it('renderWithCitations is called with enrichedOnPin (not bare onPin)', () => {
    const textFnBlock = src.slice(
      src.indexOf('function V2AssistantText'),
      src.indexOf('function V2AssistantText') + 2000,
    )
    expect(textFnBlock).toContain('renderWithCitations(text, enrichedOnPin)')
  })
})
