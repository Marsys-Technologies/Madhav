/**
 * tool_name_bridge_r6_0b_deadtools.test.ts — R6 lane 0b-deadtools regression pins.
 *
 * R-14: mimamsa_calibration_get 400'd outright — the MCP primitives dispatcher
 * (/api/mcp/primitives/[tool]/route.ts) rejects any tool name not in
 * MCP_TO_RETRIEVAL_TOOL via isAllowedSurgicalTool(). `query_calibration` (the retrieval
 * tool register_p1_aliases.ts's mimamsa_calibration_get alias calls through
 * callPlatformPrim) had no entry at all. Fixed by wiring it into SURGICAL_TOOLS +
 * MCP_TO_RETRIEVAL_TOOL + TOOL_NAME_TO_URI (pointing at the correct, schema-current L5
 * capability — distinct from the legacy Python-sidecar `query_calibration` MCP tool
 * registered in mimamsa_outcome.ts, which is fixed separately for its own schema drift).
 */
import { describe, it, expect } from 'vitest'
// Triggers capability registration for all layers (same import the primitives route makes
// at module load — see platform/src/app/api/mcp/primitives/[tool]/route.ts) so
// hasToolByName() below reflects the real, fully-populated registry.
import './catalog'
import { isAllowedSurgicalTool, resolveToolUri, hasToolByName } from './tool_name_bridge'

describe('R6 0b-deadtools (R-14) — query_calibration surgical-whitelist fix', () => {
  it('isAllowedSurgicalTool("query_calibration") is now true (was previously absent -> 400 "not in surgical whitelist")', () => {
    expect(isAllowedSurgicalTool('query_calibration')).toBe(true)
  })

  it('resolves to the correct, schema-current L5 capability URI', () => {
    expect(resolveToolUri('query_calibration')).toBe('marsys://tool/L5/query_calibration')
  })

  it('the capability is actually registered in the registry (not just URI-mapped)', () => {
    expect(hasToolByName('query_calibration')).toBe(true)
  })
})
