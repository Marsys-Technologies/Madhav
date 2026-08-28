import { describe, expect, it } from 'vitest'

import { measureCitationDensity } from './citation_density'

describe('measureCitationDensity', () => {
  it('counts bracket-number markers and reports a density number', () => {
    // Verbatim prose from a live turn against the deployed web door (chart
    // 1c826d5a, 2026-08-28, this session — see EDIR V3-E-016 for the turn's
    // full context; the two markers below are the reader-facing citation
    // format that door actually renders).
    const prose =
      'The Moon in this chart is placed in the nakshatra of Purva Bhadrapada, specifically in ' +
      'Pada 3[1]. Its exact position is 27°02′48″ in the sign of Aquarius[2]. The planetary lord ' +
      'of Purva Bhadrapada is Jupiter[1].'
    const result = measureCitationDensity(prose)
    expect(result.status).toBe('measured')
    expect(result.citationMarkerCount).toBe(3)
    expect(result.distinctCitationIndices).toBe(2)
    expect(result.sentenceCount).toBe(3)
    expect(result.wordCount).toBeGreaterThan(0)
    expect(result.citationsPer100Words).toBeCloseTo((3 / (result.wordCount ?? 1)) * 100, 5)
    expect(result.citationsPerSentence).toBeCloseTo(1)
  })

  it('counts footnote-style [^n] markers (the MCP door observed format, 2026-08-28)', () => {
    const prose =
      'Based on the structural data for this chart, the placements are as follows: the Moon is ' +
      'placed in Ardra nakshatra[^1]. The Lagna is in the sign of Aries[^2].'
    const result = measureCitationDensity(prose)
    expect(result.status).toBe('measured')
    expect(result.citationMarkerCount).toBe(2)
    expect(result.distinctCitationIndices).toBe(2)
  })

  it('reports zero density honestly when a reading carries no citation markers at all', () => {
    const prose = 'This is a reading with no citations of any kind attached to its claims.'
    const result = measureCitationDensity(prose)
    expect(result.status).toBe('measured')
    expect(result.citationMarkerCount).toBe(0)
    expect(result.citationsPer100Words).toBe(0)
    expect(result.citationsPerSentence).toBe(0)
  })

  it('returns not_measurable, never a fabricated number, when proseText is null', () => {
    const result = measureCitationDensity(null)
    expect(result.status).toBe('not_measurable')
    expect(result.citationMarkerCount).toBeNull()
    expect(result.citationsPer100Words).toBeNull()
    expect(result.citationsPerSentence).toBeNull()
    expect(result.reason).toContain('no prose text')
  })

  it('returns not_measurable for empty-string prose rather than dividing by zero', () => {
    const result = measureCitationDensity('')
    expect(result.status).toBe('not_measurable')
    expect(result.reason).toContain('empty')
  })

  it('deduplicates repeated citation indices when counting distinct sources cited', () => {
    const prose = 'Claim one[1]. Claim two[1]. Claim three[2]. Claim four[1].'
    const result = measureCitationDensity(prose)
    expect(result.citationMarkerCount).toBe(4)
    expect(result.distinctCitationIndices).toBe(2)
  })
})
