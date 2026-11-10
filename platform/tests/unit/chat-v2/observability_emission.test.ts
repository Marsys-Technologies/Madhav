/**
 * C.4 — The shared adapter dispatcher emits data-observability with a query ID and trace URL.
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const pipelineSrc = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/lib/pipelines/shared/run_adapter_dispatch.ts'),
  'utf8',
)

const drawerSrc = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/components/chat/PerMessageDetailsDrawer.tsx'),
  'utf8',
)

describe('C.4 — data-observability emission + trace deep-link', () => {
  it('emits observability with the query ID and its trace URL', () => {
    expect(pipelineSrc).toContain("type: 'data-observability'")
    expect(pipelineSrc).toContain('observabilityPart({ query_id: queryId, trace_url: `/observatory/trace/${queryId}` })')
  })

  it('PerMessageDetailsDrawer reads observability data part (primary source)', () => {
    expect(drawerSrc).toContain("name === 'observability'")
    expect(drawerSrc).toContain('obsQueryId')
  })

  it('PerMessageDetailsDrawer View trace link uses the queryId', () => {
    expect(drawerSrc).toContain('/observatory/trace/${queryId}')
    expect(drawerSrc).toContain('v2-details-trace-link')
  })
})
