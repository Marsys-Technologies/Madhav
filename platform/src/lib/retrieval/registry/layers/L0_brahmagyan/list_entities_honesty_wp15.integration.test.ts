/**
 * list_entities_honesty_wp15.integration.test.ts — WP-1.5 (LCA-8/LCA-18).
 *
 * The audit lie: list_entities served ~100 of ~652 entities while reporting total=100 (the
 * served count), so 552 rows — whole entity classes — were silently invisible. This proves
 * `total` is now the TRUE ontology-family size, `served_count` is the slice, and
 * more_available/next_cursor honestly declare the trim. Real DB.
 *
 * Run: INTEGRATION=true DATABASE_URL=... vitest run \
 *   src/lib/retrieval/registry/layers/L0_brahmagyan/list_entities_honesty_wp15.integration.test.ts
 */
import { describe, it, expect } from 'vitest'
const D = process.env.INTEGRATION === 'true' ? describe : describe.skip
type H = (a: Record<string, unknown>, c?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>

D('WP-1.5 list_entities — total is the true family size, trim declared', () => {
  it('a small limit declares more_available with a working cursor and honest total', async () => {
    const { listEntitiesCapability } = await import('./list_entities')
    const h = listEntitiesCapability.handler as H
    const res = await h({ limit: 10 })
    const c = res.content
    const served = c['served_count'] as number
    const total = c['total'] as number
    expect(served).toBe((c['entities'] as unknown[]).length)
    expect(served).toBeLessThanOrEqual(10)
    // total is the whole ontology, strictly greater than the 10-row slice.
    expect(total).toBeGreaterThan(served)
    expect(c['more_available']).toBe(true)
    expect(c['next_cursor']).not.toBeNull()
  })

  it('the ~652-entity family exceeds the 500 max page — the trim is STILL declared, never masked', async () => {
    const { listEntitiesCapability } = await import('./list_entities')
    const h = listEntitiesCapability.handler as H
    const res = await h({ limit: 500 })
    const c = res.content
    const served = c['served_count'] as number
    const total = c['total'] as number
    // The exact audit lie was total==served (100 of 652 → total:100). Now total is the real
    // family size and the remaining ~152 are honestly disclosed, not silently dropped.
    expect(served).toBe(500)
    expect(total).toBeGreaterThan(served)
    expect(c['more_available']).toBe(true)
    expect(c['next_cursor']).not.toBeNull()
  })

  it('a narrow entity_class filter reports the honest per-class total (no whole-class masking)', async () => {
    const { listEntitiesCapability } = await import('./list_entities')
    const h = listEntitiesCapability.handler as H
    const res = await h({ entity_class: 'planet', limit: 5 })
    const c = res.content
    const total = c['total'] as number
    const served = c['served_count'] as number
    // total is the COUNT under the SAME entity_class filter, never the served slice.
    expect(total).toBeGreaterThanOrEqual(served)
    if (total > served) {
      expect(c['more_available']).toBe(true)
      expect(c['next_cursor']).not.toBeNull()
    }
  })
})
