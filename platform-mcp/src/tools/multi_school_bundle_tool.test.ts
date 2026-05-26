/**
 * multi_school_bundle_tool.test.ts — Backward-compat alias tests for multi_school_bundle MCP tool.
 *
 * MCP-REM-Session-A 2026-05-26: verifies that old-signature (topic param) and
 * new-signature (claim param) both pass validation and produce correct normalized shape.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

vi.mock('../bundles/multi_school_bundle.js', () => ({
  executeMultiSchoolBundle: vi.fn(),
}))

import { executeMultiSchoolBundle } from '../bundles/multi_school_bundle.js'
import { registerMultiSchoolBundle, MultiSchoolBundleCompatSchema } from './multi_school_bundle_tool.js'

const mockPrincipal: Principal = {
  user_uid: 'test-user',
  audience_tier: 'acharya',
  key_id: 'test-key',
}

function buildOkEnvelope() {
  return {
    ok: true,
    bundle_name: 'multi_school_bundle',
    served_from_cache: false,
    bundle_entries: [],
    provenance: { signal_ids_available: [], sub_tools_fired: [], sub_tools_errored: [] },
  }
}

async function callMultiSchoolBundle(
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

  registerMultiSchoolBundle(stubServer, () => principal)

  if (!capturedHandler) throw new Error('multi_school_bundle handler was not registered')

  const schemaShape = capturedSchema as Record<string, z.ZodTypeAny>
  const zodSchema = z.object(schemaShape)
  const parseResult = zodSchema.safeParse(args)
  if (!parseResult.success) {
    return { zodError: parseResult.error, isZodError: true }
  }

  return capturedHandler(parseResult.data as Record<string, unknown>)
}

describe('multi_school_bundle — backward-compat alias tests (MCP-REM-Session-A)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('A.4-OLD: accepts old param name "topic" and passes it as claim to executor', async () => {
    const mockExecute = vi.mocked(executeMultiSchoolBundle)
    mockExecute.mockResolvedValue(buildOkEnvelope() as never)

    const result = await callMultiSchoolBundle({
      topic: 'Saturn in 10th house delays career until 36',
    })

    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
    expect(mockExecute).toHaveBeenCalledTimes(1)
    const callArg = mockExecute.mock.calls[0][0] as { claim: string }
    expect(callArg.claim).toBe('Saturn in 10th house delays career until 36')
  })

  it('A.4-NEW: accepts new param name "claim" and passes it correctly to executor', async () => {
    const mockExecute = vi.mocked(executeMultiSchoolBundle)
    mockExecute.mockResolvedValue(buildOkEnvelope() as never)

    const result = await callMultiSchoolBundle({
      claim: 'Moon-Ketu conjunction in 4th house indicates maternal separation theme',
    })

    expect((result as { isZodError?: boolean }).isZodError).toBeFalsy()
    expect(mockExecute).toHaveBeenCalledTimes(1)
    const callArg = mockExecute.mock.calls[0][0] as { claim: string }
    expect(callArg.claim).toBe('Moon-Ketu conjunction in 4th house indicates maternal separation theme')
  })

  it('A.4-COMPAT: MultiSchoolBundleCompatSchema transforms topic → claim and enforces min 10 chars', () => {
    const result = MultiSchoolBundleCompatSchema.safeParse({
      topic: 'Saturn in 10th house delays career until 36',
    })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.claim).toBe('Saturn in 10th house delays career until 36')
    }
  })

  it('A.4-COMPAT: MultiSchoolBundleCompatSchema rejects topic with fewer than 10 chars', () => {
    const result = MultiSchoolBundleCompatSchema.safeParse({ topic: 'short' })
    expect(result.success).toBe(false)
  })
})
