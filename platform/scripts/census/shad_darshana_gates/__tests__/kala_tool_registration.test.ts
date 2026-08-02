/**
 * kala_tool_registration.test.ts — ṢAḌ-DARŚANA W2 (lane w2-specificity-hard).
 *
 * Proves the registration detector fix: `server.tool(TOOL_NAME, …)` — an identifier whose
 * value is a same-file `const TOOL_NAME = 'kala_now_get'` — must resolve, not false-negative.
 * This was the documented defect that retired CI items 1/3/6 to workflow_dispatch
 * (.github/workflows/shad-darshana-ci-skeletons.yml header, CI_EFFICIENCY_AUDIT_v1_0.md §4.8):
 * 4 of the 8 kala_* views (now, ahead, priority, explain) register via a TOOL_NAME constant
 * and were reported unregistered while being live in production.
 *
 * Two layers:
 *   1. Unit — `extractRegisteredToolNames()` on synthetic sources covering every observed
 *      registration shape in platform-mcp/src/tools/kala_views (literal single-line, literal
 *      multi-line, const-identifier single-line, const-identifier multi-line, regAlias both
 *      forms), plus the honest-negative case (an identifier that resolves to nothing must
 *      NOT fabricate a detection).
 *   2. Integration — `collectShadDarshanaRegistration()` against the real platform-mcp tree
 *      must detect ALL EIGHT kala_* views. This is the self-check the workflow header named
 *      as the re-arming precondition.
 */
import { describe, it, expect } from 'vitest'
import {
  extractRegisteredToolNames,
  collectShadDarshanaRegistration,
  SHAD_DARSHANA_EIGHT_TOOLS,
} from '../_kala_tool_registration'

describe('extractRegisteredToolNames (unit, synthetic sources)', () => {
  it('detects a single-line string literal registration', () => {
    expect(extractRegisteredToolNames(`server.tool('kala_story_get', DESC, shape, handler)`)).toContain('kala_story_get')
  })

  it('detects a multi-line string literal registration (elect/story/ritual/upaya shape)', () => {
    const src = `  server.tool(\n    'kala_elect_get',\n    'ELECT — "When should I act?"',\n    InputSchema.shape,\n  )`
    expect(extractRegisteredToolNames(src)).toContain('kala_elect_get')
  })

  it('resolves a same-file const identifier, single-line call (now/ahead shape) — the fixed defect', () => {
    const src = `const TOOL_NAME = 'kala_now_get'\nserver.tool(TOOL_NAME, TOOL_DESCRIPTION, InputSchema.shape, async (params) => {})`
    expect(extractRegisteredToolNames(src)).toContain('kala_now_get')
  })

  it('resolves a same-file const identifier, multi-line call (priority/explain shape) — the fixed defect', () => {
    const src = `const TOOL_NAME = 'kala_priority_get'\n  server.tool(\n    TOOL_NAME,\n    'VIEW 5 — PRIORITIZE',\n    InputSchema.shape,\n  )`
    expect(extractRegisteredToolNames(src)).toContain('kala_priority_get')
  })

  it('detects regAlias/globalAlias with a literal', () => {
    const src = `regAlias(server, 'kala_upaya_get', handler)\nglobalAlias(server, 'kala_ritual_get', handler)`
    const names = extractRegisteredToolNames(src)
    expect(names).toContain('kala_upaya_get')
    expect(names).toContain('kala_ritual_get')
  })

  it('resolves regAlias with a same-file const identifier', () => {
    const src = `const ALIAS_NAME = 'kala_ahead_get'\nregAlias(server, ALIAS_NAME, handler)`
    expect(extractRegisteredToolNames(src)).toContain('kala_ahead_get')
  })

  it('does NOT fabricate a detection for an identifier with no same-file const value', () => {
    const src = `import { TOOL_NAME } from './names'\nserver.tool(TOOL_NAME, DESC, shape, handler)`
    expect(extractRegisteredToolNames(src)).toEqual([])
  })

  it('does NOT detect a const declaration alone (no registration call site)', () => {
    expect(extractRegisteredToolNames(`const TOOL_NAME = 'kala_now_get'`)).toEqual([])
  })
})

describe('collectShadDarshanaRegistration (integration, real platform-mcp tree)', () => {
  it('detects ALL EIGHT kala_* views as registered — the re-arming precondition', () => {
    const registration = collectShadDarshanaRegistration()
    const missing = SHAD_DARSHANA_EIGHT_TOOLS.filter((t) => (registration[t]?.length ?? 0) === 0)
    expect(missing, `undetected tools: ${missing.join(', ')} — registration census is false-negative`).toEqual([])
  })
})
