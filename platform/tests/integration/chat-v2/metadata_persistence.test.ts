/**
 * Integration tests for B.7 — lastAssistantMetadata persistence (audit finding O9).
 *
 * O9: Reload after persistence showed empty details drawer because writeConversationMessages
 * was called without lastAssistantMetadata. The drawer reads from message.metadata.custom
 * after reload, so metadata must be persisted in conversation_messages.metadata_json.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const routeSrc = readFileSync(
  join(__dirname, '../../../src/app/api/chat/consume/route.ts'),
  'utf-8',
)

const writerSrc = readFileSync(
  join(__dirname, '../../../src/lib/persistence/conversation_writer.ts'),
  'utf-8',
)

describe('B.7 — lastAssistantMetadata persistence (O9)', () => {
  it('route passes lastAssistantMetadata to writeConversationMessages', () => {
    // Find the writeConversationMessages call in onFinish
    const callIdx = routeSrc.indexOf('const writeResult = await writeConversationMessages')
    const callBlock = routeSrc.slice(callIdx, callIdx + 400)
    expect(callBlock).toContain('lastAssistantMetadata')
  })

  it('lastAssistantMetadata is structured as { custom: {...} } to match PerMessageDetailsDrawer', () => {
    expect(routeSrc).toContain('lastAssistantMetadata: Record<string, unknown>')
    expect(routeSrc).toContain("custom: {")
    // Key fields the drawer reads
    const metaIdx = routeSrc.indexOf('const lastAssistantMetadata')
    const metaBlock = routeSrc.slice(metaIdx, metaIdx + 600)
    expect(metaBlock).toContain('model: modelId')
    expect(metaBlock).toContain('queryId')
    expect(metaBlock).toContain('planning_latency_ms')
    expect(metaBlock).toContain('disclosure_tier')
  })

  it('conversation_writer accepts lastAssistantMetadata and writes it to metadata_json', () => {
    expect(writerSrc).toContain('lastAssistantMetadata')
    expect(writerSrc).toContain('metadata_json')
    expect(writerSrc).toContain('isLastAssistant ? lastAssistantMetadata : {}')
  })
})
