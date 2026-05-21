import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { RETRIEVAL_TOOLS } from '@/lib/retrieve/index'

const NEW_TOOLS = ['query_muhurat', 'query_jaimini_drishti', 'query_v7_additions']
const EXPECTED_MIN_TOTAL = 33

describe('sla_probe_new_tools — COV-S4 sidecar wrappers surface in registry', () => {
  it(`RETRIEVAL_TOOLS contains at least ${EXPECTED_MIN_TOTAL} tools (30 existing + 3 new)`, () => {
    expect(RETRIEVAL_TOOLS.length).toBeGreaterThanOrEqual(EXPECTED_MIN_TOTAL)
  })

  it.each(NEW_TOOLS)('RETRIEVAL_TOOLS contains %s', (toolName) => {
    const found = RETRIEVAL_TOOLS.find(t => t.name === toolName)
    expect(found, `${toolName} not found in RETRIEVAL_TOOLS`).toBeDefined()
  })

  it.each(NEW_TOOLS)('%s has name, version and retrieve function', (toolName) => {
    const t = RETRIEVAL_TOOLS.find(t => t.name === toolName)!
    expect(typeof t.name).toBe('string')
    expect(typeof t.version).toBe('string')
    expect(typeof t.retrieve).toBe('function')
    expect(typeof t.description).toBe('string')
    expect((t.description ?? '').length).toBeGreaterThan(20)
  })

  it('manifest_overrides.yaml has entries for all 3 new tools', () => {
    const overridesPath = resolve(__dirname, '../../../00_ARCHITECTURE/manifest_overrides.yaml')
    const content = readFileSync(overridesPath, 'utf-8')
    for (const toolName of NEW_TOOLS) {
      expect(content).toContain(`tool_name: "${toolName}"`)
    }
  })

  it('query_muhurat is marked expose_to_planner: true in manifest_overrides', () => {
    const overridesPath = resolve(__dirname, '../../../00_ARCHITECTURE/manifest_overrides.yaml')
    const content = readFileSync(overridesPath, 'utf-8')
    // Find the query_muhurat block and confirm expose_to_planner: true follows within 20 lines
    const idx = content.indexOf('tool_name: "query_muhurat"')
    expect(idx).toBeGreaterThan(-1)
    const slice = content.slice(idx, idx + 2000)
    expect(slice).toContain('expose_to_planner: true')
  })
})
