/**
 * F-06 (PARIŚEṢA-V4) — ref_remedies_chart_get scope honesty.
 *
 * Original defect: the tool description promised "Chart-specific remedy
 * suggestions", but neither the MCP-facing parameter schema nor the server-side
 * query scopes by chart_id. The underlying table (brahma_remedy_corpus) is a
 * global L0 reference corpus with no chart_id column, so per-chart filtering is
 * not merely unimplemented — it is not expressible against this data source.
 * The capability's own descriptor already says so ("No chart-scoped SQL — this
 * is a global corpus lookup"); only the MCP alias still claimed otherwise.
 *
 * Ruling: scope honesty, not new scoping. The description now states what the
 * tool does, chart_id is exposed as an explicitly provenance-only parameter (so
 * the schema mirrors the capability's real contract rather than hiding it), and
 * callers are pointed at bodha_remedies_get for genuinely chart-derived remedies.
 *
 * These tests are regression locks on the honesty claim itself.
 */
import { describe, it, expect, beforeAll } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { registerP1AliasTools } from '../tools/register_p1_aliases.js'
import type { Principal } from '../types.js'

interface CapturedTool {
  name: string
  description: string
  schema: Record<string, z.ZodTypeAny>
  handler: (...args: unknown[]) => unknown
}

const captured = new Map<string, CapturedTool>()

const fakeServer = {
  tool(name: string, description: string, schema: Record<string, z.ZodTypeAny>, handler: (...a: unknown[]) => unknown) {
    captured.set(name, { name, description, schema, handler })
  },
} as unknown as McpServer

const principal: Principal = {
  user_uid: 'test-user',
  role: 'client',
  key_id: 'test-key',
} as unknown as Principal

beforeAll(() => {
  registerP1AliasTools(fakeServer, principal)
})

describe('F-06 — ref_remedies_chart_get scope honesty', () => {
  it('is registered', () => {
    expect(captured.has('ref_remedies_chart_get')).toBe(true)
  })

  it('does NOT claim to be chart-specific / chart-scoped', () => {
    const desc = captured.get('ref_remedies_chart_get')!.description
    // The exact original false promise, and near neighbours of it.
    expect(desc).not.toMatch(/chart-specific remedy/i)
    expect(desc).not.toMatch(/remedies for (this|the|a) chart/i)
    expect(desc).not.toMatch(/based on (the |this )?chart/i)
  })

  it('states plainly that it is not chart-scoped', () => {
    const desc = captured.get('ref_remedies_chart_get')!.description
    expect(desc).toMatch(/NOT chart-scoped/i)
    expect(desc).toMatch(/brahma_remedy_corpus/)
  })

  it('points callers at the genuinely chart-scoped remedy surface', () => {
    const desc = captured.get('ref_remedies_chart_get')!.description
    expect(desc).toContain('bodha_remedies_get')
  })

  it('exposes chart_id in the schema (callers can pass it) and labels it provenance-only', () => {
    const tool = captured.get('ref_remedies_chart_get')!
    // The original defect was that chart_id could not even be passed.
    expect(Object.keys(tool.schema)).toContain('chart_id')

    const shape = z.object(tool.schema)
    // chart_id must be optional — it is not required, because it changes nothing.
    expect(shape.safeParse({ affliction: 'Saturn', top_k: 5 }).success).toBe(true)
    // and must still be validated when supplied (no arbitrary string smuggling).
    expect(shape.safeParse({ affliction: 'Saturn', chart_id: 'not-a-uuid' }).success).toBe(false)
    expect(
      shape.safeParse({ affliction: 'Saturn', chart_id: '482012f1-710e-4a25-994a-93821f5871aa' }).success,
    ).toBe(true)

    const chartIdDesc = (tool.schema['chart_id'] as z.ZodTypeAny).description ?? ''
    expect(chartIdDesc).toMatch(/provenance/i)
    expect(chartIdDesc).toMatch(/does NOT filter|not.*filter/i)
  })

  it('the original reproducer args still work unchanged (no breaking schema change)', () => {
    const tool = captured.get('ref_remedies_chart_get')!
    const shape = z.object(tool.schema)
    expect(shape.safeParse({ affliction: 'Saturn', top_k: 5 }).success).toBe(true)
  })
})
