/**
 * Integration tests — data parts emitted via createUIMessageStream.
 *
 * Verifies that the stream-building pattern used in the consume route
 * (writer.write data-stage/data-tool, then writer.merge synthesis) emits
 * the expected UIMessageChunk sequence with correctly-shaped data parts.
 */
import { describe, it, expect } from 'vitest'
import { createUIMessageStream } from 'ai'
import type { UIMessageChunk } from 'ai'
import {
  DataPartSchema,
  stagePart,
  toolPart,
} from '@/lib/streams/data_parts'

async function collectChunks(stream: ReadableStream<UIMessageChunk>): Promise<UIMessageChunk[]> {
  const reader = stream.getReader()
  const chunks: UIMessageChunk[] = []
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    chunks.push(value)
  }
  return chunks
}

function dataPartsFrom(chunks: UIMessageChunk[]): unknown[] {
  return chunks
    .filter((c) => c.type === 'data-stage' || c.type === 'data-tool')
    .map((c) => (c as { data: unknown }).data)
}

// ── Test 1: stage sequence is emitted in correct order ────────────────────

describe('data parts stream — stage sequence', () => {
  it('emits classify → compose_bundle → tool_fetch → synthesis in order', async () => {
    const stream = createUIMessageStream({
      execute: ({ writer }) => {
        writer.write({ type: 'data-stage', data: stagePart('classify', 'done', 320) })
        writer.write({ type: 'data-stage', data: stagePart('compose_bundle', 'done', 45) })
        writer.write({ type: 'data-stage', data: stagePart('tool_fetch', 'done', 890) })
        writer.write({ type: 'data-stage', data: stagePart('synthesis', 'running') })
      },
    })

    const chunks = await collectChunks(stream as ReadableStream<UIMessageChunk>)
    const stageChunks = chunks.filter((c) => c.type === 'data-stage')
    expect(stageChunks).toHaveLength(4)

    const stages = stageChunks.map((c) => {
      const d = (c as { data: { stage: string; status: string } }).data
      return `${d.stage}:${d.status}`
    })
    expect(stages).toEqual([
      'classify:done',
      'compose_bundle:done',
      'tool_fetch:done',
      'synthesis:running',
    ])

    for (const p of dataPartsFrom(chunks)) {
      expect(DataPartSchema.safeParse(p).success).toBe(true)
    }
  })
})

// ── Test 2: tool parts carry ok_count / err_count ─────────────────────────

describe('data parts stream — tool parts', () => {
  it('emits done and error tool parts with correct fields', async () => {
    const stream = createUIMessageStream({
      execute: ({ writer }) => {
        writer.write({
          type: 'data-tool',
          data: { type: 'tool', name: 'msr_sql', status: 'done', ms: 312, ok_count: 8, err_count: 0 },
        })
        writer.write({
          type: 'data-tool',
          data: { type: 'tool', name: 'vector_search', status: 'error', ms: 5000, ok_count: 0, err_count: 1 },
        })
      },
    })

    const chunks = await collectChunks(stream as ReadableStream<UIMessageChunk>)
    const toolChunks = chunks.filter((c) => c.type === 'data-tool')
    expect(toolChunks).toHaveLength(2)

    const [t1, t2] = toolChunks.map((c) => (c as { data: Record<string, unknown> }).data)
    expect(t1.name).toBe('msr_sql')
    expect(t1.status).toBe('done')
    expect(t1.ok_count).toBe(8)
    expect(t1.err_count).toBe(0)

    expect(t2.name).toBe('vector_search')
    expect(t2.status).toBe('error')
    expect(t2.err_count).toBe(1)

    for (const p of dataPartsFrom(chunks)) {
      expect(DataPartSchema.safeParse(p).success).toBe(true)
    }
  })
})

// ── Test 3: all emitted data parts pass DataPartSchema ────────────────────

describe('data parts stream — schema validity', () => {
  it('every data chunk emitted by helper constructors passes DataPartSchema', async () => {
    const stream = createUIMessageStream({
      execute: ({ writer }) => {
        writer.write({ type: 'data-stage', data: stagePart('classify', 'running') })
        writer.write({ type: 'data-stage', data: stagePart('classify', 'done', 150) })
        writer.write({ type: 'data-stage', data: stagePart('compose_bundle', 'done', 30) })
        writer.write({ type: 'data-tool', data: toolPart('msr_sql', 'done', 200) })
        writer.write({ type: 'data-tool', data: toolPart('vector_search', 'error') })
        writer.write({ type: 'data-stage', data: stagePart('tool_fetch', 'done', 210) })
        writer.write({ type: 'data-stage', data: stagePart('synthesis', 'running') })
      },
    })

    const chunks = await collectChunks(stream as ReadableStream<UIMessageChunk>)
    const parts = dataPartsFrom(chunks)
    expect(parts.length).toBe(7)

    for (const p of parts) {
      const result = DataPartSchema.safeParse(p)
      expect(
        result.success,
        `DataPartSchema rejected: ${JSON.stringify(p)} — ${JSON.stringify((result as { error?: unknown }).error)}`
      ).toBe(true)
    }
  })
})
