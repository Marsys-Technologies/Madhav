import { describe, expect, it } from 'vitest'
import { parseMarkers, hasAnyMarker } from '@/lib/consume/marker_parser'

describe('marker_parser', () => {
  it('strips ‹reasoning› spans and extracts text', () => {
    const out = parseMarkers(
      'The Lagna is strong. ‹reasoning›Weighing Saturn role in 10th from Moon‹/reasoning› Saturn in particular brings discipline.'
    )
    expect(out.visibleText).toBe('The Lagna is strong.  Saturn in particular brings discipline.')
    expect(out.reasoning).toHaveLength(1)
    expect(out.reasoning[0].text).toContain('Weighing Saturn')
    expect(out.reasoning[0].phase).toBe('synthesis')
  })

  it('extracts a correction block at the top of the answer', () => {
    const txt = `‹correction›
original: "my Jupiter is in the 7th"
corrected: "Jupiter is in the 5th"
source: "FORENSIC chart, F.JU.pos"
‹/correction›
Proceeding from the correct placement.`
    const out = parseMarkers(txt)
    expect(out.correction).not.toBeNull()
    expect(out.correction!.original_claim).toContain('Jupiter is in the 7th')
    expect(out.correction!.corrected_claim).toContain('5th')
    expect(out.correction!.classical_source).toContain('FORENSIC chart')
    expect(out.visibleText).toContain('Proceeding from the correct placement')
    expect(out.visibleText).not.toContain('‹correction›')
  })

  it('extracts out_of_domain reason', () => {
    const out = parseMarkers('‹out_of_domain reason="weather query"›‹/out_of_domain›Sunny, probably.')
    expect(out.outOfDomain).not.toBeNull()
    expect(out.outOfDomain!.reason).toBe('weather query')
    expect(out.visibleText).toBe('Sunny, probably.')
  })

  it('extracts Sanskrit spans and keeps display text', () => {
    const out = parseMarkers(
      'During the ‹sanskrit term="Vimshottari" def="120-year dasha system" translit="viṃśottarī"›Vimshottari‹/sanskrit› cycle, things shift.'
    )
    expect(out.sanskrit).toHaveLength(1)
    expect(out.sanskrit[0].term).toBe('Vimshottari')
    expect(out.sanskrit[0].transliteration).toBe('viṃśottarī')
    expect(out.visibleText).toContain('During the Vimshottari cycle')
  })

  it('deduplicates Sanskrit terms within one answer', () => {
    const txt =
      '‹sanskrit term="Karaka" def="Significator" translit="kāraka"›Karaka‹/sanskrit› and ' +
      '‹sanskrit term="Karaka" def="Significator" translit="kāraka"›Karaka‹/sanskrit›'
    const out = parseMarkers(txt)
    expect(out.sanskrit).toHaveLength(1)
  })

  it('hasAnyMarker detects open tokens', () => {
    expect(hasAnyMarker('plain text')).toBe(false)
    expect(hasAnyMarker('‹reasoning›x‹/reasoning›')).toBe(true)
  })
})
