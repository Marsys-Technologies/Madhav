/**
 * C.1 — ConsumeReportLibraryV2 wired into ConsumeChatV2.
 *
 * Source-level assertions verifying the reports prop is destructured
 * and ConsumeReportLibraryV2 is imported and rendered in the header.
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const CONSUME_DIR = path.resolve(
  import.meta.dirname,
  '../../../src/components/consume'
)

const src = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeChatV2.tsx'), 'utf8')

describe('C.1 — ConsumeReportLibraryV2 wired into ConsumeChatV2', () => {
  it('imports ConsumeReportLibraryV2', () => {
    expect(src).toContain("from '@/components/consume/ConsumeReportLibraryV2'")
  })

  it('destructures reports from props with default empty array', () => {
    expect(src).toContain('reports = []')
  })

  it('renders ConsumeReportLibraryV2 with reports prop in header-actions', () => {
    const headerActionsBlock = src.slice(
      src.indexOf('v2-header-actions'),
      src.indexOf('v2-header-actions') + 800,
    )
    expect(headerActionsBlock).toContain('<ConsumeReportLibraryV2')
    expect(headerActionsBlock).toContain('reports={reports}')
  })

  it('ConsumeReportLibraryV2 component has v2-report-library-trigger testid', () => {
    const libSrc = fs.readFileSync(path.join(CONSUME_DIR, 'ConsumeReportLibraryV2.tsx'), 'utf8')
    expect(libSrc).toContain('v2-report-library-trigger')
  })
})
