/**
 * INF7-S3: intent_classifier tests
 * [BUILD-ORCH-J-08]
 */

import { describe, it, expect } from 'vitest'
import { classifyIntent, filterAyanamshas } from '../intent_classifier'

describe('classifyIntent', () => {
  it('classifies dasha queries correctly', () => {
    const result = classifyIntent('Which vimshottari yogini dasha system is running now?')
    expect(result.intent).toBe('dasha_query')
    expect(result.confidence).toBeGreaterThan(0)
    expect(result.tool_priority[0]).toBe('query_dasha_periods')
  })

  it('classifies panchanga queries correctly', () => {
    const result = classifyIntent('What was the tithi paksha and panchang on my birth date?')
    expect(result.intent).toBe('panchanga_query')
    expect(result.prefetch_categories).toContain('panchang')
  })

  it('classifies remedial queries correctly', () => {
    const result = classifyIntent('What mantra and gemstone remedy should I use for Saturn?')
    expect(result.intent).toBe('remedial_query')
    expect(result.tool_priority).toContain('query_remedies_prescribed')
  })

  it('classifies comparison queries correctly', () => {
    const result = classifyIntent('How does Lahiri vs KP ayanamsha affect my chart?')
    expect(result.intent).toBe('comparison_query')
    expect(result.suggest_cross_ayanamsha).toBe(true)
    expect(result.recommended_ayanamshas).toHaveLength(5)
  })

  it('classifies transit queries correctly', () => {
    const result = classifyIntent('What transits are active for me now in gochara?')
    expect(result.intent).toBe('transit_query')
    expect(result.tool_priority).toContain('query_transits_over_natal')
  })

  it('classifies yoga queries correctly', () => {
    const result = classifyIntent('Do I have raj yoga or gajakesari yoga in my chart?')
    expect(result.intent).toBe('yoga_query')
    expect(result.prefetch_categories).toContain('yoga')
  })

  it('classifies prediction queries correctly', () => {
    const result = classifyIntent('When will I get married? Predict my career outcome.')
    expect(result.intent).toBe('prediction_query')
    expect(result.suggest_cross_ayanamsha).toBe(true)
  })

  it('defaults to chart_reading when no keywords match', () => {
    const result = classifyIntent('Hello there')
    expect(result.intent).toBe('chart_reading')
  })

  it('returns recommended_ayanamshas as non-empty array', () => {
    const result = classifyIntent('What is the lagna lord?')
    expect(result.recommended_ayanamshas.length).toBeGreaterThan(0)
  })

  it('returns tool_priority as non-empty array', () => {
    const result = classifyIntent('Some query')
    expect(result.tool_priority.length).toBeGreaterThan(0)
  })

  it('confidence is between 0 and 1', () => {
    const result = classifyIntent('Dasha and timing query for next period')
    expect(result.confidence).toBeGreaterThanOrEqual(0)
    expect(result.confidence).toBeLessThanOrEqual(1)
  })
})

describe('filterAyanamshas', () => {
  const ALL_5 = ['lahiri', 'true_chitra', 'kp', 'raman', 'surya_siddhanta']

  it('returns intersection of recommended and available for super_admin', () => {
    const result = filterAyanamshas(['lahiri', 'kp'], ALL_5, 'super_admin')
    expect(result).toEqual(['lahiri', 'kp'])
  })

  it('client tier: returns only lahiri by default', () => {
    const result = filterAyanamshas(['lahiri', 'true_chitra', 'kp'], ALL_5, 'client')
    expect(result).toContain('lahiri')
  })

  it('falls back to lahiri when recommended ayanamshas not in available', () => {
    const result = filterAyanamshas(['raman'], ['lahiri'], 'super_admin')
    expect(result).toEqual(['lahiri'])
  })

  it('returns empty list filtered to available only', () => {
    const result = filterAyanamshas(['lahiri', 'kp'], ['lahiri'], 'acharya_reviewer')
    expect(result).toEqual(['lahiri'])
  })
})
