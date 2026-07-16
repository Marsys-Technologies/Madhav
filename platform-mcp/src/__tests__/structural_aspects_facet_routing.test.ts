/**
 * D-1.6 Lane S-5 — PARK-A7 + R-17 regression test (also closes the routed S-4-sputa-drishti
 * item, same root cause).
 *
 * ganita_structural_get's `aspects` facet previously declared BOTH Parashari (Graha Drishti)
 * AND Jaimini/Tajik categories in one shared set. get_aspects.ts's underlying SQL orders
 * `ORDER BY fact_category` globally across every requested category under ONE shared LIMIT —
 * 'aspect_jaimini*' sorts alphabetically before 'aspect_parashari_*', so a large
 * aspect_jaimini_per_varga population could consume the row budget before any Parashari row
 * was ever reached (BIND_D-1.6 S-7 probe: "default page leads with aspect_jaimini rasi-drishti
 * boilerplate", 19 real aspect_parashari_given rows never surfacing).
 *
 * Fix: split into disjoint facets — `aspects` (Parashari + matrix_summary only),
 * `aspects_jaimini`, `aspects_tajik` — each with its own declared category set, so none can
 * crowd another out under the shared-LIMIT tool.
 */
import { describe, it, expect } from 'vitest'
import { FACET_CATEGORIES, STRUCTURAL_FACET_URI } from '../tools/register_p1_ganita.js'

describe('ganita_structural_get aspects facet routing (PARK-A7 / R-17)', () => {
  it('aspects facet declares ONLY Parashari + matrix_summary categories — never jaimini/tajik', () => {
    const categories = FACET_CATEGORIES['aspects']
    expect(categories).toBeDefined()
    expect(categories).toContain('aspect_parashari_given')
    expect(categories).toContain('aspect_parashari_received')
    expect(categories).toContain('aspect_parashari_per_varga')
    expect(categories).not.toContain('aspect_jaimini')
    expect(categories).not.toContain('aspect_jaimini_per_varga')
    expect(categories).not.toContain('aspect_tajik')
  })

  it('aspects_jaimini facet exists and is disjoint from aspects', () => {
    const jaimini = FACET_CATEGORIES['aspects_jaimini']
    expect(jaimini).toEqual(['aspect_jaimini', 'aspect_jaimini_per_varga'])
    const aspects = FACET_CATEGORIES['aspects'] ?? []
    for (const c of jaimini ?? []) expect(aspects).not.toContain(c)
  })

  it('aspects_tajik facet exists and is disjoint from aspects', () => {
    const tajik = FACET_CATEGORIES['aspects_tajik']
    expect(tajik).toEqual(['aspect_tajik'])
    const aspects = FACET_CATEGORIES['aspects'] ?? []
    for (const c of tajik ?? []) expect(aspects).not.toContain(c)
  })

  it('all three aspect-family facets route to the same underlying get_aspects tool', () => {
    expect(STRUCTURAL_FACET_URI['aspects']).toBe('marsys://tool/L1/get_aspects')
    expect(STRUCTURAL_FACET_URI['aspects_jaimini']).toBe('marsys://tool/L1/get_aspects')
    expect(STRUCTURAL_FACET_URI['aspects_tajik']).toBe('marsys://tool/L1/get_aspects')
  })

  it('graha_yuddha and parivartana still return their OWN row sets (pre-existing R-17 fix, ' +
     'guarded here so a future edit cannot silently re-collapse them)', () => {
    expect(FACET_CATEGORIES['graha_yuddha']).toEqual(['graha_yuddha'])
    expect(FACET_CATEGORIES['parivartana']).toEqual(['parivartana_per_varga'])
    expect(STRUCTURAL_FACET_URI['graha_yuddha']).toBe('marsys://tool/L1/get_graha_yuddha')
    expect(STRUCTURAL_FACET_URI['parivartana']).toBe('marsys://tool/L1/get_dispositors')
  })

  it('no two facets sharing the get_aspects URI declare an overlapping category (the exact ' +
     'crowding-out bug class this fix closes)', () => {
    const aspectFamilyFacets = Object.entries(STRUCTURAL_FACET_URI)
      .filter(([, uri]) => uri === 'marsys://tool/L1/get_aspects')
      .map(([facet]) => facet)
    const seen = new Map<string, string>()
    for (const facet of aspectFamilyFacets) {
      for (const category of FACET_CATEGORIES[facet] ?? []) {
        const owner = seen.get(category)
        expect(owner, `category "${category}" claimed by both "${owner}" and "${facet}"`).toBeUndefined()
        seen.set(category, facet)
      }
    }
  })
})
