/**
 * alias_check.test.ts — D-2 Lane V-0 (BIND_D-2.md §F1.7 ledger row 4).
 *
 * V-3's canonical_faces.json does not exist yet in this repo snapshot (V-3 is a cycle-2 lane;
 * this test runs against cycle-1 reality) — this test suite is itself the "self-test evidence
 * showing the stub" the task instructions require: it asserts the mechanical-fallback branch
 * activates, is clearly labeled, and never silently reports as if it were V-3's authored list.
 */
import { describe, it, expect } from 'vitest'
import { checkAliasCount, loadCanonicalFacesFile } from '../alias_check.js'
import type { McpToolDescriptor } from '../mcp_client.js'

describe('alias_check — stub-until-V-3 behavior (self-test evidence)', () => {
  it('canonical_faces.json does not exist yet in this repo snapshot (confirms the stub condition is real, not assumed)', () => {
    expect(loadCanonicalFacesFile()).toBeNull()
  })

  it('falls back to mechanical [Phase-1 alias] discovery and labels the result explicitly as a stub', () => {
    const tools: McpToolDescriptor[] = [
      { name: 'bodha_signals_get', description: 'Primary signal reader.' },
      { name: 'get_signals', description: '[Phase-1 alias] Legacy name (same as bodha_signals_get).' },
      { name: 'ganita_natal_positions_compute', description: 'Primary positions reader.' },
      { name: 'compute_natal_positions', description: '[Phase-1 alias] Legacy name (same as ganita_natal_positions_compute).' },
    ]
    const result = checkAliasCount(tools)
    expect(result.source).toBe('mechanical_fallback_pending_v3')
    expect(result.detail).toMatch(/STUB/)
    expect(result.live_tool_count).toBe(4)
    expect(result.deprecated_alias_count).toBe(2) // get_signals, compute_natal_positions
    expect(result.canonical_face_count).toBe(2) // bodha_signals_get, ganita_natal_positions_compute
    expect(result.reconciles).toBe(true)
  })

  it('flags an orphan twin: an alias whose declared primitive does not exist live', () => {
    const tools: McpToolDescriptor[] = [
      { name: 'get_signals', description: '[Phase-1 alias] Legacy name (same as bodha_signals_get_RENAMED).' },
    ]
    const result = checkAliasCount(tools)
    expect(result.orphan_twins).toContain('get_signals')
    expect(result.reconciles).toBe(false)
  })

  it('under-counts unmarked twins by design — documented, not silently wrong (BIND_D-2.md §B.5 example)', () => {
    // get_signals/bodha_signals_get IS the real BIND_D-2.md §B.5-cited pair — this fixture omits
    // the [Phase-1 alias] marker to model an unmarked twin, which the mechanical fallback cannot
    // catch (only V-3's authored list can). Both tools are counted as independently "canonical".
    const tools: McpToolDescriptor[] = [
      { name: 'bodha_signals_get', description: 'Primary signal reader.' },
      { name: 'get_signals', description: 'Legacy signal reader (no Phase-1 alias marker).' },
    ]
    const result = checkAliasCount(tools)
    expect(result.canonical_face_count).toBe(2) // both counted canonical — the documented under-count
    expect(result.detail).toMatch(/under-counts true aliasing/)
  })
})
