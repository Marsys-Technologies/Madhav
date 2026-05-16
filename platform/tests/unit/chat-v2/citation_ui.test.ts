/**
 * β4 — Inline numbered citations unit tests.
 *
 * Covers: citation data part schema, extractCitations helper,
 * buildCitationIndex, and structural audit of the UI components.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'
import { extractCitations, buildCitationIndex } from '../../../src/lib/citations/citation_data_part'

// ── Source audit helpers ───────────────────────────────────────────────────────

const consumeSrc = readFileSync(
  resolve(__dirname, '../../../src/components/consume/ConsumeChatV2.tsx'),
  'utf8',
)
const routeSrc = readFileSync(
  resolve(__dirname, '../../../src/app/api/chat/consume/route.ts'),
  'utf8',
)
const dataPartsSrc = readFileSync(
  resolve(__dirname, '../../../src/lib/streams/data_parts.ts'),
  'utf8',
)

// ── extractCitations helper ────────────────────────────────────────────────────

describe('extractCitations', () => {
  it('extracts unique SIG.MSR.NNN in order of first appearance', () => {
    const text = 'Jupiter (→ SIG.MSR.042) and Saturn (→ SIG.MSR.117) combine here (→ SIG.MSR.042).'
    const citations = extractCitations(text)
    expect(citations).toHaveLength(2)
    expect(citations[0]!.signal_id).toBe('SIG.MSR.042')
    expect(citations[0]!.index).toBe(1)
    expect(citations[1]!.signal_id).toBe('SIG.MSR.117')
    expect(citations[1]!.index).toBe(2)
  })

  it('returns empty array for text with no citations', () => {
    expect(extractCitations('No signals mentioned here.')).toHaveLength(0)
  })

  it('does not match SIG.MSR.NNN with extra digits (4-digit sequences)', () => {
    const citations = extractCitations('SIG.MSR.0010 should not match')
    expect(citations).toHaveLength(0)
  })
})

// ── buildCitationIndex ─────────────────────────────────────────────────────────

describe('buildCitationIndex', () => {
  it('maps signal_id to its 1-based index', () => {
    const citations = extractCitations('SIG.MSR.001 and SIG.MSR.002')
    const index = buildCitationIndex(citations)
    expect(index.get('SIG.MSR.001')).toBe(1)
    expect(index.get('SIG.MSR.002')).toBe(2)
  })
})

// ── UI structural audits ───────────────────────────────────────────────────────

describe('ConsumeChatV2 β4 citation wiring', () => {
  it('imports NumberedCitation', () => {
    expect(consumeSrc).toContain('NumberedCitation')
  })

  it('imports CitationSidePanel', () => {
    expect(consumeSrc).toContain('CitationSidePanel')
  })

  it('uses CitationCtx (citation context)', () => {
    expect(consumeSrc).toContain('CitationCtx')
  })

  it('renders V2AssistantText as the Text part renderer', () => {
    expect(consumeSrc).toContain('V2AssistantText')
  })

  it('uses v2-citation-badge test ID (from NumberedCitation)', () => {
    expect(
      readFileSync(
        resolve(__dirname, '../../../src/components/chat/NumberedCitation.tsx'),
        'utf8',
      )
    ).toContain('v2-citation-badge')
  })

  it('uses v2-citation-panel test ID (from CitationSidePanel)', () => {
    expect(
      readFileSync(
        resolve(__dirname, '../../../src/components/chat/CitationSidePanel.tsx'),
        'utf8',
      )
    ).toContain('v2-citation-panel')
  })
})

// ── Route citation emission ───────────────────────────────────────────────────

describe('consume route β4 citation emission', () => {
  it('imports extractCitations', () => {
    expect(routeSrc).toContain('extractCitations')
  })

  it('emits data-citation parts in onFinish', () => {
    expect(routeSrc).toContain("type: 'data-citation'")
  })
})

// ── DataPart union ────────────────────────────────────────────────────────────

describe('data_parts CitationPart', () => {
  it('includes CitationPartSchema in the union', () => {
    expect(dataPartsSrc).toContain('CitationPartSchema')
  })

  it('exports citationPart helper', () => {
    expect(dataPartsSrc).toContain("export const citationPart")
  })
})
