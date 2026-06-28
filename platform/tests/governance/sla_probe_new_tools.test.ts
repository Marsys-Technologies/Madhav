import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
// D7 Step 4: RETRIEVAL_TOOLS from lib/retrieve retired — check bridge + spec instead
import { TOOL_NAME_TO_URI } from '@/lib/retrieval/registry/tool_name_bridge'
import { RETRIEVAL_CAPABILITY_SPEC, getCapability } from '@/lib/router/retrieval_capability_spec'

const NEW_TOOLS = ['query_muhurat', 'query_jaimini_drishti', 'query_v7_additions']
const EXPECTED_MIN_TOTAL = 33

describe('sla_probe_new_tools — COV-S4 sidecar wrappers surface in registry', () => {
  it(`RETRIEVAL_CAPABILITY_SPEC contains at least ${EXPECTED_MIN_TOTAL} entries`, () => {
    expect(RETRIEVAL_CAPABILITY_SPEC.length).toBeGreaterThanOrEqual(EXPECTED_MIN_TOTAL)
  })

  it.each(NEW_TOOLS)('RETRIEVAL_CAPABILITY_SPEC contains %s', (toolName) => {
    const found = getCapability(toolName)
    expect(found, `${toolName} not found in RETRIEVAL_CAPABILITY_SPEC`).toBeDefined()
  })

  it.each(NEW_TOOLS)('%s has description and required fields in spec', (toolName) => {
    const entry = getCapability(toolName)!
    expect(typeof entry.tool_name).toBe('string')
    expect(typeof entry.description).toBe('string')
    expect(entry.description.length).toBeGreaterThan(20)
    expect(typeof entry.data_surface).toBe('string')
    expect(typeof entry.supported_params).toBe('string')
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
    const idx = content.indexOf('tool_name: "query_muhurat"')
    expect(idx).toBeGreaterThan(-1)
    const slice = content.slice(idx, idx + 2000)
    expect(slice).toContain('expose_to_planner: true')
  })
})
