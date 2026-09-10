import { describe, expect, it } from 'vitest'

import { queryYogaCatalogCapability } from '../query_yoga_catalog'

describe('queryYogaCatalogCapability description', () => {
  it('documents the current 233-row catalog, not the legacy snapshot', () => {
    expect(queryYogaCatalogCapability.description).toContain('233 canonical yogas')
  })
})
