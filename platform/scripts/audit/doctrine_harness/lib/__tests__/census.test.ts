/**
 * census.test.ts — D-2 Lane V-0 (BIND_D-2.md §F1.7 ledger row 5).
 *
 * Offline unit coverage for the census sweep's resumability, classification, and
 * transport-vs-tool separation — no live connector involved (per CONDUCTOR_PROTOCOL §6.3,
 * every lifecycle step must be independently testable; a live-only test would make this
 * lane's own CI un-runnable). The "interrupted-sweep resume test" the ledger names is the
 * second test below: it simulates a crash mid-sweep (checkpoint written, process ends) and
 * confirms a fresh `runCensusSweep` call against the SAME checkpoint path skips every
 * already-probed tool and only calls the remaining ones.
 */
import { describe, it, expect, afterEach } from 'vitest'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import {
  runCensusSweep,
  summarizeCensus,
  synthesizeCensusArgs,
  OVERSIZE_BYTES,
  type CensusToolResult,
} from '../census.js'
import { RateLimitedError, type McpClient, type McpToolDescriptor } from '../mcp_client.js'

function makeTools(n: number): McpToolDescriptor[] {
  return Array.from({ length: n }, (_, i) => ({
    name: `tool_${i}`,
    description: `test tool ${i}`,
    inputSchema: { type: 'object', properties: { chart_id: { type: 'string' } }, required: ['chart_id'] },
  }))
}

/** Fake McpClient — records call order, returns a scripted result per tool name. */
function fakeClient(
  behavior: (toolName: string, callIndex: number) => { content: unknown; isToolError: boolean; status?: number } | 'throw-transport' | 'throw-tool-error'
): { client: McpClient; calls: string[] } {
  const calls: string[] = []
  let i = 0
  const client = {
    callTool: async (name: string) => {
      calls.push(name)
      const outcome = behavior(name, i++)
      if (outcome === 'throw-transport') throw new RateLimitedError(name, 1)
      if (outcome === 'throw-tool-error') throw new Error(`TRANSPORT-ERROR 503 calling ${name}`)
      return { raw: { ok: true, status: outcome.status ?? 200, body: '' }, content: outcome.content, isToolError: outcome.isToolError }
    },
  } as unknown as McpClient
  return { client, calls }
}

let tmpDirs: string[] = []
afterEach(() => {
  for (const d of tmpDirs) rmSync(d, { recursive: true, force: true })
  tmpDirs = []
})

function tmpCheckpointPath(): string {
  const dir = mkdtempSync(join(tmpdir(), 'census-test-'))
  tmpDirs.push(dir)
  return join(dir, 'checkpoint.json')
}

describe('census — synthesizeCensusArgs', () => {
  it('fabricates chart_id for a chart_id-required tool', () => {
    const tool: McpToolDescriptor = {
      name: 't',
      inputSchema: { properties: { chart_id: { type: 'string' } }, required: ['chart_id'] },
    }
    expect(synthesizeCensusArgs(tool, 'CHART-1')).toEqual({ chart_id: 'CHART-1' })
  })

  it('returns null (SKIPPED, not a guess) for an unrecognized required string field', () => {
    const tool: McpToolDescriptor = {
      name: 't',
      inputSchema: { properties: { mystery_field: { type: 'string' } }, required: ['mystery_field'] },
    }
    expect(synthesizeCensusArgs(tool, 'CHART-1')).toBeNull()
  })
})

describe('census — probe classification', () => {
  it('classifies a healthy small payload as PASS', async () => {
    const tools = makeTools(1)
    const { client } = fakeClient(() => ({ content: { content: { rows: [{ a: 1 }, { a: 2 }] } }, isToolError: false }))
    const checkpointPath = tmpCheckpointPath()
    const { results } = await runCensusSweep(client, tools, { checkpointPath, chartId: 'C1', target: 't', interBatchMs: 0 })
    expect(results[0].status).toBe('PASS')
  })

  it('classifies a >64KB payload as DEGRADED, never FAIL', async () => {
    const tools = makeTools(1)
    const bigRows = Array.from({ length: 5000 }, (_, i) => ({ id: i, text: 'x'.repeat(20) }))
    const { client } = fakeClient(() => ({ content: { content: { rows: bigRows } }, isToolError: false }))
    const checkpointPath = tmpCheckpointPath()
    const { results } = await runCensusSweep(client, tools, { checkpointPath, chartId: 'C1', target: 't', interBatchMs: 0 })
    expect(results[0].status).toBe('DEGRADED')
    expect(results[0].bytes).toBeGreaterThan(OVERSIZE_BYTES)
  })

  it('classifies zero rows WITH empty_reason as EMPTY (honest), never FAIL', async () => {
    const tools = makeTools(1)
    const { client } = fakeClient(() => ({ content: { content: { rows: [] }, empty_reason: 'no wealth yogas in stored vocabulary' }, isToolError: false }))
    const checkpointPath = tmpCheckpointPath()
    const { results } = await runCensusSweep(client, tools, { checkpointPath, chartId: 'C1', target: 't', interBatchMs: 0 })
    expect(results[0].status).toBe('EMPTY')
    expect(results[0].empty_reason).toContain('vocabulary')
  })

  it('classifies an explicit tool-level error as FAIL', async () => {
    const tools = makeTools(1)
    const { client } = fakeClient(() => ({ content: { error: 'boom' }, isToolError: true }))
    const checkpointPath = tmpCheckpointPath()
    const { results } = await runCensusSweep(client, tools, { checkpointPath, chartId: 'C1', target: 't', interBatchMs: 0 })
    expect(results[0].status).toBe('FAIL')
  })

  it('TRANSPORT-vs-TOOL separation: a rate-limit/transport exception is TRANSPORT_ERROR, never FAIL', async () => {
    const tools = makeTools(1)
    const { client } = fakeClient(() => 'throw-transport')
    const checkpointPath = tmpCheckpointPath()
    const { results } = await runCensusSweep(client, tools, { checkpointPath, chartId: 'C1', target: 't', interBatchMs: 0 })
    expect(results[0].status).toBe('TRANSPORT_ERROR')
    const summary = summarizeCensus(results)
    expect(summary.FAIL).toBe(0)
    expect(summary.TRANSPORT_ERROR).toBe(1)
  })

  it('a required-arg field it cannot synthesize is SKIPPED, not FAIL and not silently dropped', async () => {
    const tools: McpToolDescriptor[] = [
      { name: 'weird_tool', inputSchema: { properties: { mystery: { type: 'string' } }, required: ['mystery'] } },
    ]
    const { client, calls } = fakeClient(() => ({ content: {}, isToolError: false }))
    const checkpointPath = tmpCheckpointPath()
    const { results } = await runCensusSweep(client, tools, { checkpointPath, chartId: 'C1', target: 't', interBatchMs: 0 })
    expect(results[0].status).toBe('SKIPPED')
    expect(calls.length).toBe(0) // never called the tool with a guessed arg
  })
})

describe('census — interrupted-sweep resume (BIND_D-2.md §F1.7 ledger row 5)', () => {
  it('resumes from a checkpoint: already-probed tools are never re-called', async () => {
    const tools = makeTools(5)
    const checkpointPath = tmpCheckpointPath()

    // First "run": only probes 3 of 5 tools, simulating a crash after batch write (batchSize=3
    // forces exactly one checkpoint write covering tools 0-2, then we stop before the 2nd batch
    // by using batchSize=3 with only tools[0..2] passed in — this models the exact on-disk state
    // an interrupted real sweep would leave behind).
    const { client: client1 } = fakeClient(() => ({ content: { content: { rows: [{ a: 1 }] } }, isToolError: false }))
    await runCensusSweep(client1, tools.slice(0, 3), { checkpointPath, chartId: 'C1', target: 'https://x/mcp', interBatchMs: 0, batchSize: 3 })

    // Second "run" (the resume): full 5-tool list, SAME checkpoint path + target + chartId.
    const { client: client2, calls: calls2 } = fakeClient(() => ({ content: { content: { rows: [{ a: 1 }] } }, isToolError: false }))
    const { results, resumed } = await runCensusSweep(client2, tools, {
      checkpointPath,
      chartId: 'C1',
      target: 'https://x/mcp',
      interBatchMs: 0,
      batchSize: 3,
    })

    expect(resumed).toBe(true)
    // Only the 2 NEW tools (tool_3, tool_4) should have been called on the resume — tool_0..2
    // came from the checkpoint, never re-probed.
    expect(calls2.sort()).toEqual(['tool_3', 'tool_4'])
    expect(results).toHaveLength(5)
    expect(results.every((r: CensusToolResult) => r.status === 'PASS')).toBe(true)
  })

  it('does NOT resume across a different target (avoids mixing two connectors under one checkpoint)', async () => {
    const tools = makeTools(2)
    const checkpointPath = tmpCheckpointPath()
    const { client: client1 } = fakeClient(() => ({ content: { content: { rows: [{ a: 1 }] } }, isToolError: false }))
    await runCensusSweep(client1, tools, { checkpointPath, chartId: 'C1', target: 'https://a/mcp', interBatchMs: 0 })

    const { client: client2, calls: calls2 } = fakeClient(() => ({ content: { content: { rows: [{ a: 1 }] } }, isToolError: false }))
    const { resumed } = await runCensusSweep(client2, tools, { checkpointPath, chartId: 'C1', target: 'https://b/mcp', interBatchMs: 0 })

    expect(resumed).toBe(false)
    expect(calls2.sort()).toEqual(['tool_0', 'tool_1']) // full re-probe against the new target
  })
})
