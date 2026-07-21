/**
 * cr118_uri_fastfail.test.ts — W5 L1: CR-118 fast-fail / msr_sql defect, before/after
 * ================================================================================
 * Real, live bug found while investigating the W5 "generated web-tool bridge"
 * task: `compiled_floor_adapter.ts`'s `ensureB11WholeChartReadFloor` (and its
 * `prashna_ask_spike.ts` twin) push literal registry URIs as `tool_name` —
 * e.g. `'marsys://tool/L2/query_signals'` (the exact capability `msr_sql`
 * already resolves correctly under its own name) and
 * `'marsys://tool/L2/traverse_chart_graph'`.
 *
 * BEFORE this lane: `tool_name_bridge.ts`'s `resolveToolUri()` only checked
 * `TOOL_NAME_TO_URI[toolName]` — a map whose KEYS are legacy names and whose
 * VALUES are URIs. A URI was never a valid KEY, so
 * `resolveToolUri('marsys://tool/L2/query_signals')` returned `undefined`,
 * `getToolByName(...)` returned `undefined`, and consult/route.ts's tool-fetch
 * loop (`if (!t) return null`) silently dropped the tool — no thrown error, no
 * step_error trace event, just a missing result. This is the msr_sql web-
 * channel defect named in the W5 brief and one instance of the CR-118
 * fast-fail class (a tool name present in the compiled/registry surface but
 * absent/misrouted in the web bridge).
 *
 * AFTER this lane: `resolveToolUri()` recognizes any `marsys://`-prefixed
 * `toolName` as an already-resolved URI and resolves it directly via
 * `getCapability()`, structurally (not by renaming the two call sites).
 */
import { describe, it, expect } from 'vitest'
import '../catalog'
import { getToolByName, hasToolByName, resolveToolUri } from '../tool_name_bridge'

const BROKEN_URIS_BEFORE_THIS_LANE = [
  'marsys://tool/L2/query_signals', // B.11 floor: MSR signals (msr_sql) — the msr_sql defect
  'marsys://tool/L2/traverse_chart_graph', // B.11 floor: CGM graph traversal
] as const

describe('CR-118 fast-fail fix — literal registry URIs are valid tool_name values', () => {
  it('resolveToolUri resolves a literal marsys:// URI to itself (was undefined before this lane)', () => {
    for (const uri of BROKEN_URIS_BEFORE_THIS_LANE) {
      expect(resolveToolUri(uri)).toBe(uri)
    }
  })

  it('hasToolByName is true for these URIs (was false before this lane)', () => {
    for (const uri of BROKEN_URIS_BEFORE_THIS_LANE) {
      expect(hasToolByName(uri), `${uri} must resolve after the CR-118 fix`).toBe(true)
    }
  })

  it('getToolByName returns a usable tool descriptor for these URIs (was undefined before this lane)', () => {
    for (const uri of BROKEN_URIS_BEFORE_THIS_LANE) {
      const t = getToolByName(uri)
      expect(t, `getToolByName(${uri}) must not be undefined after the CR-118 fix`).toBeDefined()
      expect(typeof t?.retrieve).toBe('function')
    }
  })

  it('the SAME capability is reachable both via its legacy name and its literal URI (msr_sql === marsys://tool/L2/query_signals)', () => {
    expect(resolveToolUri('msr_sql')).toBe(resolveToolUri('marsys://tool/L2/query_signals'))
  })

  it('a non-existent marsys:// URI (no such capability registered) still fails closed, not open', () => {
    const fake = 'marsys://tool/L99/does_not_exist'
    expect(resolveToolUri(fake)).toBe(fake) // resolves the URI syntactically...
    expect(hasToolByName(fake)).toBe(false) // ...but getCapability() correctly rejects it
    expect(getToolByName(fake)).toBeUndefined()
  })
})
