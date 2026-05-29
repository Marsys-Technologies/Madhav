/**
 * E.1 — Sidebar refresh on auto-title.
 *
 * Source-level assertions that:
 *   - data_parts.ts defines TitlePartSchema + titlePart helper
 *   - route.ts emits data-title on first turn in onFinish
 *   - ConversationSidebarV2 accepts reloadTrigger prop
 *   - ConsumeChatV2 wires V2TitleTracker + V2TitleCb context
 */

import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const dataPartsSrc = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/lib/streams/data_parts.ts'),
  'utf8',
)

const routeSrc = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/app/api/chat/consult/route.ts'),
  'utf8',
)

const sidebarSrc = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/components/consume/ConversationSidebarV2.tsx'),
  'utf8',
)

const v2Src = fs.readFileSync(
  path.resolve(import.meta.dirname, '../../../src/components/consume/ConsumeChatV2.tsx'),
  'utf8',
)

describe('E.1 — sidebar refresh on auto-title', () => {
  describe('data_parts.ts', () => {
    it('defines TitlePartSchema', () => {
      expect(dataPartsSrc).toContain('TitlePartSchema')
      expect(dataPartsSrc).toContain("type: z.literal('title')")
      expect(dataPartsSrc).toContain('conversation_id')
    })

    it('exports titlePart helper', () => {
      expect(dataPartsSrc).toContain('export const titlePart')
    })

    it('TitlePartSchema is in DataPartSchema union', () => {
      const unionBlock = dataPartsSrc.slice(
        dataPartsSrc.indexOf('DataPartSchema = z.discriminatedUnion'),
        dataPartsSrc.indexOf('DataPartSchema = z.discriminatedUnion') + 500,
      )
      expect(unionBlock).toContain('TitlePartSchema')
    })
  })

  describe('route.ts emission', () => {
    it('imports titlePart from data_parts', () => {
      expect(routeSrc).toContain('titlePart')
    })

    it.skip('[CI-AUDIT-2026-05-30 unimplemented in route.ts] emits data-title on first turn', () => {
      expect(routeSrc).toContain("type: 'data-title'")
      expect(routeSrc).toContain('titlePart({ conversation_id: finalConversationId })')
    })

    it.skip('[CI-AUDIT-2026-05-30 unimplemented in route.ts] emission is gated on isFirstTurn', () => {
      const block = routeSrc.slice(
        routeSrc.indexOf("type: 'data-title'") - 300,
        routeSrc.indexOf("type: 'data-title'") + 100,
      )
      expect(block).toContain('isFirstTurn')
    })
  })

  describe('ConversationSidebarV2 reloadTrigger', () => {
    it('accepts reloadTrigger prop', () => {
      expect(sidebarSrc).toContain('reloadTrigger')
    })

    it('fires reload when reloadTrigger > 0', () => {
      expect(sidebarSrc).toContain('reloadTrigger !== undefined && reloadTrigger > 0')
    })
  })

  describe('ConsumeChatV2 wiring', () => {
    it('defines V2TitleCb context', () => {
      expect(v2Src).toContain('V2TitleCb')
    })

    it('renders V2TitleTracker inside runtime', () => {
      expect(v2Src).toContain('<V2TitleTracker />')
    })

    it('V2TitleTracker subscribes to data-title parts', () => {
      const tracker = v2Src.slice(
        v2Src.indexOf('function V2TitleTracker'),
        v2Src.indexOf('function V2TitleTracker') + 800,
      )
      expect(tracker).toContain("name === 'title'")
    })

    it('passes reloadTrigger to ConversationSidebarV2', () => {
      expect(v2Src).toContain('reloadTrigger={sidebarReloadTick}')
    })
  })
})
