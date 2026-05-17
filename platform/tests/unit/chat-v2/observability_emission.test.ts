/**
 * C.4 — data-observability emitted in route.ts onFinish.
 *
 * Source-level assertions verifying the route imports observabilityPart
 * and emits it with query_id + trace_url.
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const routeSrc = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/app/api/chat/consume/route.ts'),
  'utf8',
)

const drawerSrc = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/components/chat/PerMessageDetailsDrawer.tsx'),
  'utf8',
)

describe('C.4 — data-observability emission + trace deep-link', () => {
  it('route.ts imports observabilityPart from data_parts', () => {
    expect(routeSrc).toContain('observabilityPart')
  })

  it('route.ts emits data-observability with query_id and trace_url in onFinish', () => {
    expect(routeSrc).toContain("type: 'data-observability'")
    expect(routeSrc).toContain('observabilityPart({ query_id: queryId, trace_url:')
  })

  it('trace_url follows /observatory/trace/<query_id> pattern', () => {
    expect(routeSrc).toContain('/observatory/trace/${queryId}')
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
