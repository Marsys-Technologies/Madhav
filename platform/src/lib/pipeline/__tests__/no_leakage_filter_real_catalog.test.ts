import { describe, expect, it } from 'vitest'
// Bootstrap the full L0–L5 registry (side-effect import) so this test exercises
// filterLeakedCapabilities against the REAL production catalog, not fixtures —
// same import consult/route.ts's path makes. Kept in its own file (rather than
// alongside no_leakage_filter.test.ts's fixture suite) so no `clearRegistry()`
// call anywhere in the process can empty the catalog out from under it.
import '@/lib/retrieval/registry/catalog'
import { filterLeakedCapabilities } from '@/lib/pipeline/no_leakage_filter'

describe('filterLeakedCapabilities — against the real production catalog', () => {
  it('strips the real F-R7-flagged lel_query / query_predictions capabilities', () => {
    const toolNames = [
      'marsys://tool/L5/lel_query',
      'marsys://tool/L5/query_predictions',
      'chart_facts_query',
    ]
    const result = filterLeakedCapabilities(toolNames)
    expect(result).not.toContain('marsys://tool/L5/lel_query')
    expect(result).not.toContain('marsys://tool/L5/query_predictions')
    expect(result).toContain('chart_facts_query')
  })
})
