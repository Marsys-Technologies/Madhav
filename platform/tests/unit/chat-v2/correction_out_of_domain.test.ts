/**
 * D.3 — CorrectionNotice + OutOfDomainBanner emission paths.
 *
 * Source-level assertions that:
 *   - data_parts.ts has CorrectionPartSchema + OutOfDomainPartSchema
 *   - the shared finish pipeline parses markers and emits correction/out-of-domain parts
 *   - ConsumeChatV2.tsx imports the components and subscribes to the data parts
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const dataPartsSrc = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/lib/streams/data_parts.ts'),
  'utf8',
)

const pipelineSrc = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/lib/pipelines/shared/onfinish_writethrough.ts'),
  'utf8',
)

const v2Src = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/components/consume/ConsumeChatV2.tsx'),
  'utf8',
)

describe('D.3 — CorrectionNotice + OutOfDomainBanner emission', () => {
  describe('data_parts.ts schemas', () => {
    it('defines CorrectionPartSchema', () => {
      expect(dataPartsSrc).toContain('CorrectionPartSchema')
      expect(dataPartsSrc).toContain("type: z.literal('correction')")
      expect(dataPartsSrc).toContain('corrected_claim')
    })

    it('defines OutOfDomainPartSchema', () => {
      expect(dataPartsSrc).toContain('OutOfDomainPartSchema')
      expect(dataPartsSrc).toContain("type: z.literal('out_of_domain')")
    })

    it('exports correctionPart and outOfDomainPart helpers', () => {
      expect(dataPartsSrc).toContain('export const correctionPart')
      expect(dataPartsSrc).toContain('export const outOfDomainPart')
    })

    it('includes both schemas in DataPartSchema union', () => {
      expect(dataPartsSrc).toContain('CorrectionPartSchema')
      expect(dataPartsSrc).toContain('OutOfDomainPartSchema')
    })
  })

  it('parses assistant markers and emits corrections and out-of-domain notices on finish', () => {
    expect(pipelineSrc).toContain('parseMarkers(opts.assistantText)')
    expect(pipelineSrc).toContain("type: 'data-correction'")
    expect(pipelineSrc).toContain('data: correctionPart({')
    expect(pipelineSrc).toContain("type: 'data-out-of-domain'")
    expect(pipelineSrc).toContain('data: outOfDomainPart({ reason: outOfDomain.reason })')
  })

  describe('ConsumeChatV2.tsx wiring', () => {
    it('imports CorrectionNotice', () => {
      expect(v2Src).toContain("from './CorrectionNotice'")
    })

    it('imports OutOfDomainBanner', () => {
      expect(v2Src).toContain("from './OutOfDomainBanner'")
    })

    it('subscribes to correction data part (via useDataParts hook)', () => {
      // R6.1: consolidated to hook — matches data-correction from both sources
      expect(v2Src).toContain("'data-correction'")
    })

    it('subscribes to out_of_domain data part (via useDataParts hook)', () => {
      // R6.1: consolidated to hook — matches data-out-of-domain from both sources
      expect(v2Src).toContain("'data-out-of-domain'")
    })

    it('renders CorrectionNotice when correction present', () => {
      expect(v2Src).toContain('<CorrectionNotice')
    })

    it('renders OutOfDomainBanner when out-of-domain present', () => {
      expect(v2Src).toContain('<OutOfDomainBanner')
    })
  })
})
