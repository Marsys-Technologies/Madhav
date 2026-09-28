import { describe, expect, it, vi } from 'vitest'
import {
  logSafeByokToolFailure,
  MCP_BYOK_TOOL_FAILURE_CODES,
} from '@/lib/mcp/prashna_ask/logging'

describe('MCP BYOK safe failure logging', () => {
  it.each(MCP_BYOK_TOOL_FAILURE_CODES)('logs %s with only the stable trace and allowlisted tool fields', code => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    try {
      logSafeByokToolFailure(code, '11111111-1111-4111-8111-111111111111', 'safe_tool')
      expect(spy).toHaveBeenCalledExactlyOnceWith(
        `[mcp:prashna_ask] ${code} trace=11111111-1111-4111-8111-111111111111 tool=safe_tool`,
      )
    } finally {
      spy.mockRestore()
    }
  })

  it('replaces a non-allowlisted tool label instead of logging it', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    try {
      logSafeByokToolFailure('MCP_TOOL_DISPATCH_FAILED', 'trace-1', 'unsafe\ntool provider-secret')
      const rendered = spy.mock.calls.flat().map(String).join(' ')
      expect(rendered).toContain('tool=unresolved')
      expect(rendered).not.toContain('provider-secret')
    } finally {
      spy.mockRestore()
    }
  })
})
