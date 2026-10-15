/**
 * intent_classifier_nakshatra.test.ts -- the entity_lookup pattern recognises every nakshatra spelling the
 * platform can now meet: the canonical L0-lexicon names (Mrigasira, Moola, Dhanishtha) AND the old L1
 * spellings still stored until the rebuild (Mrigashira, Mula, Dhanishta). SS N-471.
 */
import { describe, it, expect } from 'vitest'
import { classifyIntentSync } from '../intent_classifier'
import { CANONICAL_NAKSHATRA_NAMES } from '@/lib/nakshatra_spelling'

describe('classifyIntentSync -- nakshatra names are entity lookups', () => {
  it.each([
    'Mrigasira', 'Mrigashira', 'Moola', 'Mula', 'Dhanishtha', 'Dhanishta',
  ])('"%s" alone classifies as entity_lookup', (name) => {
    expect(classifyIntentSync(name).tags).toContain('entity_lookup')
    expect(classifyIntentSync(`what does ${name.toUpperCase()} mean`).tags).toContain('entity_lookup')
  })

  it('every canonical nakshatra name is recognised', () => {
    for (const name of CANONICAL_NAKSHATRA_NAMES) {
      expect(classifyIntentSync(name).tags, name).toContain('entity_lookup')
    }
  })

  it('moolatrikona (a dignity term) is not mistaken for the nakshatra Moola', () => {
    expect(classifyIntentSync('moolatrikona').tags).not.toContain('entity_lookup')
  })
})
