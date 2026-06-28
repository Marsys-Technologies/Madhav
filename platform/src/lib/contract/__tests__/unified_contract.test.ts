/**
 * unified_contract.test.ts — Unit 2b G3_contract gate (acceptance test).
 *
 * Asserts the contract module's invariants:
 *   1. Registry is non-empty.
 *   2. Every per_chart contract requires chart_id (Zod required).
 *   3. Every ayanamsha-dependent (per_chart) contract declares ayanamsha_role
 *      AND accepts an optional ayanamsha_id override.
 *   4. Zod schemas generate valid JSON-Schema for every contract.
 *   5. Dual-channel: portal index re-exports the contract names; MCP bridge
 *      mirrors the same set — both surfaces resolve from the one contract.
 *   6. Manifest query_schema is populated for every contract-known tool.
 */

import { describe, it, expect } from 'vitest'
import path from 'path'
import fs from 'fs'
import { z } from 'zod'

import {
  TOOL_CONTRACTS,
  CONTRACT_CATALOG,
  CONTRACT_TOOL_NAMES,
  checkContractInvariants,
  assertContractInvariants,
  zodToJsonSchema,
} from '../index'

// Portal channel: CONTRACT_TOOL_NAMES now lives directly in contract/catalog (D7 migration retired lib/retrieve).
import { CONTRACT_TOOL_NAMES as PORTAL_CONTRACT_TOOL_NAMES } from '../catalog'

// MCP channel bridge (verified mirror).
import { MCP_CONTRACT_TOOL_NAMES } from '../../../../../platform-mcp/src/contract_bridge'

describe('Unit 2b — unified tool contract (G3_contract gate)', () => {
  it('contract module exports a non-empty registry', () => {
    expect(TOOL_CONTRACTS.length).toBeGreaterThan(0)
    expect(CONTRACT_CATALOG.length).toBe(TOOL_CONTRACTS.length)
    expect(CONTRACT_TOOL_NAMES.length).toBe(TOOL_CONTRACTS.length)
    // No duplicate canonical_names.
    const set = new Set(CONTRACT_TOOL_NAMES)
    expect(set.size).toBe(CONTRACT_TOOL_NAMES.length)
  })

  it('every per_chart contract requires chart_id (Zod required, not optional)', () => {
    const perChart = TOOL_CONTRACTS.filter(c => c.per_chart)
    expect(perChart.length).toBeGreaterThan(0) // sanity: we have per-chart tools
    for (const c of perChart) {
      const json = z.toJSONSchema(c.input_schema as z.ZodType<unknown>) as {
        properties?: Record<string, unknown>
        required?: string[]
      }
      const required = Array.isArray(json.required) ? json.required : []
      expect(json.properties).toHaveProperty('chart_id')
      expect(required, `${c.canonical_name} must require chart_id`).toContain('chart_id')
    }
  })

  it('every ayanamsha-dependent contract declares ayanamsha_role + accepts optional ayanamsha_id', () => {
    const ayDep = TOOL_CONTRACTS.filter(c => c.ayanamsha_role !== null)
    expect(ayDep.length).toBeGreaterThan(0)
    for (const c of ayDep) {
      expect(['canonical', 'kp', 'reference']).toContain(c.ayanamsha_role)
      expect(c.ayanamsha_id, `${c.canonical_name} must default ayanamsha_id`).toBeTruthy()

      const json = z.toJSONSchema(c.input_schema as z.ZodType<unknown>) as {
        properties?: Record<string, unknown>
        required?: string[]
      }
      const required = Array.isArray(json.required) ? json.required : []
      expect(json.properties).toHaveProperty('ayanamsha_id')
      // ayanamsha_id must be OPTIONAL (not in required[]).
      expect(required).not.toContain('ayanamsha_id')
    }

    // The full invariant suite must also pass.
    expect(checkContractInvariants()).toEqual([])
    expect(() => assertContractInvariants()).not.toThrow()
  })

  it('Zod schemas generate valid JSON-Schema for every contract (sanity)', () => {
    for (const c of TOOL_CONTRACTS) {
      const schema = zodToJsonSchema(c.input_schema)
      expect(schema).toBeTypeOf('object')
      // Must look like an object schema (top-level type=object).
      expect(schema.type === 'object' || schema.$ref).toBeTruthy()
      // Must have a properties map (object schema invariant).
      expect(schema.properties, `${c.canonical_name} JSON-Schema missing properties`).toBeTypeOf('object')
    }
  })

  it('dual-channel resolution: portal and MCP catalogs expose the same canonical_name set', () => {
    // Portal channel — re-exports from contract index.
    expect(PORTAL_CONTRACT_TOOL_NAMES).toEqual(CONTRACT_TOOL_NAMES)

    // MCP channel — verified mirror.
    const portalSet = new Set(PORTAL_CONTRACT_TOOL_NAMES)
    const mcpSet = new Set(MCP_CONTRACT_TOOL_NAMES)
    const contractSet = new Set(CONTRACT_TOOL_NAMES)

    // Intersection of all three must equal each of them.
    const intersection = [...contractSet].filter(n => portalSet.has(n) && mcpSet.has(n))
    expect(new Set(intersection)).toEqual(contractSet)

    // No drift in either direction.
    expect(mcpSet.size).toBe(contractSet.size)
    expect(portalSet.size).toBe(contractSet.size)
  })

  it('manifest query_schema is populated for each tool in the contract registry', () => {
    const manifestPath = path.resolve(
      __dirname,
      '../../../../../00_ARCHITECTURE/CAPABILITY_MANIFEST.json'
    )
    expect(fs.existsSync(manifestPath), `manifest not found at ${manifestPath}`).toBe(true)

    const manifestRaw = fs.readFileSync(manifestPath, 'utf8')
    const manifest = JSON.parse(manifestRaw) as { entries: Array<Record<string, unknown>> }
    expect(Array.isArray(manifest.entries)).toBe(true)

    // Index manifest by tool_name (collect ALL entries — there can be multiple
    // per canonical name across channels; at least one must carry a
    // populated query_schema).
    const entriesByName = new Map<string, Array<Record<string, unknown>>>()
    for (const a of manifest.entries) {
      const name = (a['tool_name'] ?? a['retrieval_tool']) as string | undefined
      if (!name) continue
      const arr = entriesByName.get(name) ?? []
      arr.push(a)
      entriesByName.set(name, arr)
    }

    const missing: string[] = []
    for (const c of TOOL_CONTRACTS) {
      const entries = entriesByName.get(c.canonical_name) ?? []
      if (entries.length === 0) {
        missing.push(`${c.canonical_name}: no manifest entry`)
        continue
      }
      // At least one entry must carry a non-empty query_schema.
      const hasSchema = entries.some(e => {
        const qs = e['query_schema'] as { properties?: Record<string, unknown> } | undefined
        return (
          qs !== undefined &&
          qs !== null &&
          typeof qs === 'object' &&
          qs.properties !== undefined &&
          Object.keys(qs.properties).length > 0
        )
      })
      if (!hasSchema) {
        missing.push(`${c.canonical_name}: manifest entries lack populated query_schema`)
      }
    }

    expect(missing, `manifest gaps:\n${missing.join('\n')}`).toEqual([])
  })
})
