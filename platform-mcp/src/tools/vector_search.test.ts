/**
 * vector_search.test.ts — Backward-compat alias tests for vector_search MCP tool.
 *
 * MCP-REM-Session-A 2026-05-26: verifies that old-signature (query param) and
 * new-signature (text param) both pass validation and produce correct normalized shape.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

vi.mock('../client.js', () => ({
  callPlatformPrimitive: vi.fn(),
}))

import { callPlatformPrimitive } from '../client.js'
import { registerVectorSearch, VectorSearchCompatSchema } from './vector_search.js'

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'super_admin',
  key_id: 'test-key',
}

function buildOkEnvelope() {
  return {
    status: 200,
    envelope: {
      ok: true,
      trace_id: 'trace-vs-001',
      result: { chunks: [] },
    },
  }
}

async function callVectorSearch(
  args: Record<string, unknown>,
  principal: Principal = mockPrincipal,
) {
  let capturedHandler: ((input: Record<string, unknown>) => Promise<unknown>) | null = null
  let capturedSchema: Record<string, unknown> | null = null

  const stubServer = {
    tool: (
      _name: string,
      _description: unknown,
      schema: Record<string, unknown>,
      handler: (input: Record<string, unknown>) => Promise<unknown>,
    ) => {
      capturedHandler = handler
      capturedSchema = schema
    },
  } as unknown as McpServer

  registerVectorSearch(stubServer, () => principal)

  if (!capturedHandler) throw new Error('vector_search handler was not registered')

  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

describe('vector_search — backward-compat alias tests (MCP-REM-Session-A)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('A.2-OLD: accepts old param name "query" and forwards it as text to primitive', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildOkEnvelope())

    const result = await callVectorSearch({ query: 'Saturn creates obstacles in career' })

    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['text']).toBe('Saturn creates obstacles in career')
  })

  it('A.2-NEW: accepts new param name "text" and forwards it correctly to primitive', async () => {
    const mockCallPlatformPrimitive = vi.mocked(callPlatformPrimitive)
    mockCallPlatformPrimitive.mockResolvedValue(buildOkEnvelope())

    const result = await callVectorSearch({ text: 'Saturn creates obstacles in career' })

    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
    expect(mockCallPlatformPrimitive).toHaveBeenCalledTimes(1)
    const params = mockCallPlatformPrimitive.mock.calls[0][1] as Record<string, unknown>
    expect(params['text']).toBe('Saturn creates obstacles in career')
  })

  it('A.2-COMPAT: VectorSearchCompatSchema transforms query → text correctly', () => {
    const result = VectorSearchCompatSchema.safeParse({ query: 'find signals about Saturn' })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.text).toBe('find signals about Saturn')
    }
  })

  it('A.2-COMPAT: VectorSearchCompatSchema accepts text directly without transform', () => {
    const result = VectorSearchCompatSchema.safeParse({ text: 'find signals about Saturn' })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.text).toBe('find signals about Saturn')
    }
  })

  it('A.2-COMPAT: VectorSearchCompatSchema rejects when neither text nor query is provided', () => {
    const result = VectorSearchCompatSchema.safeParse({ top_k: 5 })
    expect(result.success).toBe(false)
  })
})
