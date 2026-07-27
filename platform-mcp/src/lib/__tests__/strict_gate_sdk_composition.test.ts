/**
 * strict_gate_sdk_composition.test.ts — P0 REGRESSION (2026-07-27)
 * ================================================================
 * The test that would have caught the production crash-loop:
 *   `Tool prashna_ask expected a Zod schema or ToolAnnotations, but received an unrecognized
 *    object` (McpServer.tool @modelcontextprotocol/sdk ≥1.29.0)
 *
 * Exercises the gate machinery against the REAL SDK `McpServer` (not a mock), with BOTH gates
 * applied in PRODUCTION order (strict first, then deprecated — server.ts), then registers a
 * tool whose shape carries a nested `.optional(z.object({...}))` field mirroring
 * `register_prashna_ask.ts`'s `scope_tuple`. The original T4 implementation crashed here
 * because it handed a constructed ZodObject to the positional `.tool()` overload; the fix
 * re-issues via `registerTool`. See strict_tool_schema_gate.ts banner ("P0 CRASH FIX").
 */
import { describe, it, expect } from 'vitest'
import { z } from 'zod'
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js'
import { applyStrictSchemaGate, type StrictSchemaGateServer } from '../strict_tool_schema_gate.js'
import { applyDeprecatedToolGate } from '../deprecated_tool_gate.js'
import type { ToolRegisteringServer } from '../mcp_profile.js'

function makeGatedServer() {
  const server = new McpServer({ name: 'test', version: '0.0.0' })
  // PRODUCTION ORDER (server.ts): strict schema gate first, deprecated gate second.
  applyStrictSchemaGate(server as unknown as StrictSchemaGateServer)
  applyDeprecatedToolGate(server as unknown as ToolRegisteringServer)
  return server
}

const okHandler = async () => ({ content: [{ type: 'text' as const, text: 'ok' }] })

describe('strict + deprecated gate composition against the real SDK', () => {
  it('registers a tool with a nested .optional(z.object) field WITHOUT throwing (the prashna_ask shape)', () => {
    const server = makeGatedServer()
    expect(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(server as any).tool(
        'prashna_ask',
        'Full-loop question answering.',
        {
          chart_id: z.string().uuid().describe('Chart UUID'),
          question: z.string().min(1).describe('Question'),
          scope_tuple: z
            .object({
              intent: z.string(),
              domains: z.array(z.string()),
              width: z.enum(['narrow', 'standard', 'broad']),
              depth: z.enum(['shallow', 'standard', 'deep']),
            })
            .optional()
            .describe('Optional pre-classified scope tuple.'),
          response_format: z.string().describe('Format hint.'),
        },
        okHandler,
      )
    }).not.toThrow()
  })

  it('registers a FLAT-shape tool without throwing (bug was general, not nested-specific)', () => {
    const server = makeGatedServer()
    expect(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(server as any).tool('flat_tool_get', 'desc', { a: z.string(), b: z.number() }, okHandler)
    }).not.toThrow()
  })

  it('end-to-end: strict schema is advertised and unknown params are rejected, known params pass', async () => {
    const server = makeGatedServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(server as any).tool(
      'prashna_ask',
      'desc',
      {
        chart_id: z.string().uuid(),
        question: z.string().min(1),
        scope_tuple: z.object({ intent: z.string() }).optional(),
        response_format: z.string(),
      },
      okHandler,
    )

    const [clientT, serverT] = InMemoryTransport.createLinkedPair()
    const client = new Client({ name: 'c', version: '0' })
    await Promise.all([server.connect(serverT), client.connect(clientT)])
    try {
      const list = await client.listTools()
      const prashna = list.tools.find(t => t.name === 'prashna_ask')
      expect(prashna).toBeDefined()
      // .strict() surfaces as additionalProperties:false in the advertised JSON schema.
      expect((prashna!.inputSchema as { additionalProperties?: unknown }).additionalProperties).toBe(false)

      const valid = await client.callTool({
        name: 'prashna_ask',
        arguments: {
          chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
          question: 'q',
          response_format: 'brief',
        },
      })
      expect(valid.isError).not.toBe(true)

      const unknownKey = await client.callTool({
        name: 'prashna_ask',
        arguments: {
          chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
          question: 'q',
          response_format: 'brief',
          bogus_param: 1,
        },
      })
      expect(unknownKey.isError).toBe(true)
    } finally {
      await client.close()
      await server.close()
    }
  })
})
