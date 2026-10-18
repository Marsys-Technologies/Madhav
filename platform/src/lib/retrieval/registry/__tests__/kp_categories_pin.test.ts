/**
 * kp_categories_pin.test.ts — SS N-358: the KP category set (`KP_FRAME_CATEGORIES`) is pinned.
 *
 * "A KP category is served in the KP frame": the set is the one list of chart_facts categories
 * that get_karakas / get_nakshatra read at krishnamurti on default pages and explicit lists.
 * Changing it must be a deliberate edit of this test. It is also checked against the two
 * category censuses (a KP-looking category that is not in the set fails here).
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import {
  INVARIANT_STORED_FACT_CATEGORIES,
  INVARIANT_STORED_FACT_CATEGORY_PREFIXES,
} from '../constants'
import { KP_FRAME_CATEGORIES, isKpFrameCategory, partitionKpCategories } from '../kp_categories'
import { CHART_FACTS_CATEGORIES } from '../layers/L1_ganita/coverage_matrix'

describe('KP_FRAME_CATEGORIES', () => {
  it('pins the exact members', () => {
    expect([...KP_FRAME_CATEGORIES].sort()).toEqual([
      'cusp_kp_lords',
      'graha_kp_lords',
      'kp_cuspal_significators',
      'kp_house_significators',
      'kp_planet_significations',
      'kp_ruling_planets_natal',
    ])
  })

  it('every member is a plain [a-z_]+ identifier (the mixed-page SQL inlines them as literals)', () => {
    for (const c of KP_FRAME_CATEGORIES) expect(c, c).toMatch(/^[a-z_]+$/)
  })

  it('has no duplicates', () => {
    expect(new Set(KP_FRAME_CATEGORIES).size).toBe(KP_FRAME_CATEGORIES.length)
  })

  it('no member is also an INVARIANT-stored category (a KP chain is per ayanamsha, never INVARIANT)', () => {
    for (const c of KP_FRAME_CATEGORIES) {
      expect(INVARIANT_STORED_FACT_CATEGORIES.has(c), c).toBe(false)
      expect(INVARIANT_STORED_FACT_CATEGORY_PREFIXES.some((p) => c.startsWith(p)), c).toBe(false)
    }
  })

  it('contains every KP-looking category of the authoritative census and the coverage matrix', () => {
    const census = JSON.parse(
      readFileSync(join(__dirname, '../../../../generated/census/chart_facts_categories_authoritative_v1.json'), 'utf8'),
    ) as { categories: string[] }
    const kpLooking = (c: string) => /(^kp_|_kp_)/.test(c)
    const seen = [...census.categories, ...(CHART_FACTS_CATEGORIES as readonly string[])].filter(kpLooking)
    expect(seen.length).toBeGreaterThanOrEqual(4)
    for (const c of seen) expect(isKpFrameCategory(c), `${c} looks like a KP category but is not in KP_FRAME_CATEGORIES`).toBe(true)
  })

  it('does not swallow general house-frame / structural categories', () => {
    for (const c of ['bhava_cusps', 'significator_path', 'bhava_significance_link', 'graha_nakshatra_join', 'karaka_chara_position']) {
      expect(isKpFrameCategory(c), c).toBe(false)
    }
  })
})

describe('isKpFrameCategory / partitionKpCategories', () => {
  it('is exact-membership (no prefix guessing) and total on non-strings', () => {
    expect(isKpFrameCategory('kp_cuspal_significators')).toBe(true)
    expect(isKpFrameCategory('kp_unknown_future')).toBe(false)
    expect(isKpFrameCategory(undefined)).toBe(false)
    expect(isKpFrameCategory(null)).toBe(false)
    expect(isKpFrameCategory(7)).toBe(false)
  })

  it('splits a list preserving order', () => {
    expect(partitionKpCategories(['arudha_pada', 'cusp_kp_lords', 'swamsa_position', 'graha_kp_lords'])).toEqual({
      kp: ['cusp_kp_lords', 'graha_kp_lords'],
      other: ['arudha_pada', 'swamsa_position'],
    })
    expect(partitionKpCategories([])).toEqual({ kp: [], other: [] })
  })
})
