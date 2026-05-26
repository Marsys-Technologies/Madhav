/**
 * log_prediction.test.ts — Backward-compat alias tests for log_prediction MCP tool.
 *
 * MCP-REM-Session-A 2026-05-26: verifies that old-signature (float confidence,
 * no falsifier) and new-signature (enum confidence, required falsifier) both
 * pass validation and produce correct normalized shape.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

vi.mock('../client.js', () => ({
  callPlatformWrites: vi.fn(),
}))

import { callPlatformWrites } from '../client.js'
import { registerLogPrediction } from './log_prediction.js'

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
      trace_id: 'trace-lp-001',
      result: { prediction_id: 'PPL.MCP.TESTTEST' },
    },
  }
}

async function callLogPrediction(
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

  registerLogPrediction(stubServer, () => principal)

  if (!capturedHandler) throw new Error('log_prediction handler was not registered')

  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

const BASE_ARGS = {
  domain: 'career',
  horizon: '2026-Q3',
  prediction_text: 'Native transitions to a leadership role during Saturn Antardasha',
}

describe('log_prediction — backward-compat alias tests (MCP-REM-Session-A)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('A.7-OLD: accepts float confidence 0.8 (→ "high") and omitted falsifier (→ "")', async () => {
    const mockCallPlatformWrites = vi.mocked(callPlatformWrites)
    mockCallPlatformWrites.mockResolvedValue(buildOkEnvelope())

    const result = await callLogPrediction({
      ...BASE_ARGS,
      confidence: 0.8,
      // falsifier intentionally omitted — backward-compat default is ''
    })

    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
    expect(mockCallPlatformWrites).toHaveBeenCalledTimes(1)
    const callArg = mockCallPlatformWrites.mock.calls[0][1] as { entry: Record<string, unknown> }
    expect(callArg.entry['confidence']).toBe('high')
    expect(callArg.entry['falsifier']).toBe('')
  })

  it('A.7-NEW: accepts enum confidence "medium" and explicit falsifier string', async () => {
    const mockCallPlatformWrites = vi.mocked(callPlatformWrites)
    mockCallPlatformWrites.mockResolvedValue(buildOkEnvelope())

    const result = await callLogPrediction({
      ...BASE_ARGS,
      confidence: 'medium',
      falsifier: 'No promotion or role change by 2026-09-30',
    })

    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
    expect(mockCallPlatformWrites).toHaveBeenCalledTimes(1)
    const callArg = mockCallPlatformWrites.mock.calls[0][1] as { entry: Record<string, unknown> }
    expect(callArg.entry['confidence']).toBe('medium')
    expect(callArg.entry['falsifier']).toBe('No promotion or role change by 2026-09-30')
  })

  it('A.7-FLOAT: float 0.6 maps to "medium"', async () => {
    const mockCallPlatformWrites = vi.mocked(callPlatformWrites)
    mockCallPlatformWrites.mockResolvedValue(buildOkEnvelope())

    await callLogPrediction({ ...BASE_ARGS, confidence: 0.6 })

    const callArg = mockCallPlatformWrites.mock.calls[0][1] as { entry: Record<string, unknown> }
    expect(callArg.entry['confidence']).toBe('medium')
  })

  it('A.7-FLOAT: float 0.3 maps to "low"', async () => {
    const mockCallPlatformWrites = vi.mocked(callPlatformWrites)
    mockCallPlatformWrites.mockResolvedValue(buildOkEnvelope())

    await callLogPrediction({ ...BASE_ARGS, confidence: 0.3 })

    const callArg = mockCallPlatformWrites.mock.calls[0][1] as { entry: Record<string, unknown> }
    expect(callArg.entry['confidence']).toBe('low')
  })
})
