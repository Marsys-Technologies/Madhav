/**
 * whitelist_resolution_invariant.test.ts — WP-1.7 (LCA-1 / LCA-13) permanent guard.
 *
 * DURABLE DELIVERABLE. Prevents recurrence of the local-bench-vs-deployed divergence
 * whose root cause was: MCP_TO_RETRIEVAL_TOOL whitelisted retrieval-tool names whose
 * targets were ABSENT from TOOL_NAME_TO_URI → getToolByName() returned undefined → the
 * /api/mcp/primitives/[tool] route 500'd on every such call ("Retrieval tool not found
 * in registry"). ~45% of the surgical surface was dead locally.
 *
 * INVARIANT: every value in MCP_TO_RETRIEVAL_TOOL MUST resolve, end to end:
 *   1. isAllowedSurgicalTool(mcpName) === true                    (whitelist accepts it)
 *   2. SURGICAL_TOOLS contains the retrieval name                 (type-level integrity)
 *   3. resolveToolUri(retrievalName) is defined                   (TOOL_NAME_TO_URI entry exists)
 *   4. getCapability(uri) is registered                           (a real handler backs it)
 *   5. getToolByName(retrievalName) is defined                    (the primitives route's own call)
 *
 * If ANY of these fails, CI fails. To prove the guard works, temporarily delete or
 * mutate a TOOL_NAME_TO_URI entry (or point it at a bogus URI) and re-run: step 3/4/5
 * for the dependent tool(s) must fail. See the WP-1.7 report for the recorded mutation.
 *
 * The primitives route makes the same `import '@/lib/retrieval/registry/catalog'` at
 * module load; we replicate it here so getCapability()/getToolByName() reflect the real,
 * fully-populated registry (L0–L5), not a partial one.
 */
import { describe, it, expect } from 'vitest'
import './catalog'
import { getCapability } from './index'
import {
  MCP_TO_RETRIEVAL_TOOL,
  SURGICAL_TOOLS,
  TOOL_NAME_TO_URI,
  isAllowedSurgicalTool,
  resolveToolUri,
  getToolByName,
  hasToolByName,
} from './tool_name_bridge'

const surgicalSet = new Set<string>(SURGICAL_TOOLS)

describe('WP-1.7 — MCP surgical whitelist resolution invariant', () => {
  const entries = Object.entries(MCP_TO_RETRIEVAL_TOOL)

  it('the whitelist is non-empty (sanity)', () => {
    expect(entries.length).toBeGreaterThan(0)
  })

  it.each(entries)(
    'MCP tool "%s" → retrieval "%s" resolves end to end (whitelist → SURGICAL_TOOLS → URI → capability → getToolByName)',
    (mcpName, retrievalName) => {
      // 1. whitelist accepts the MCP-facing name
      expect(isAllowedSurgicalTool(mcpName), `isAllowedSurgicalTool("${mcpName}") should be true`).toBe(true)

      // 2. retrieval name is a declared SurgicalToolName
      expect(surgicalSet.has(retrievalName), `SURGICAL_TOOLS should contain "${retrievalName}" (for MCP name "${mcpName}")`).toBe(true)

      // 3. TOOL_NAME_TO_URI has an entry
      const uri = resolveToolUri(retrievalName)
      expect(uri, `TOOL_NAME_TO_URI is missing "${retrievalName}" (MCP name "${mcpName}") — the exact WP-1.7 root cause`).toBeDefined()

      // 4. a real capability is registered for that URI
      expect(getCapability(uri as string), `no capability registered for ${uri} (retrieval "${retrievalName}")`).toBeDefined()

      // 5. the primitives route's own resolution path returns a live tool (not undefined → not a 500)
      expect(getToolByName(retrievalName), `getToolByName("${retrievalName}") returned undefined → the primitives route would 500`).toBeDefined()
      expect(hasToolByName(retrievalName)).toBe(true)
    },
  )

  it('aggregate: ZERO MCP_TO_RETRIEVAL_TOOL values fail to resolve via getToolByName', () => {
    const unresolved = Object.entries(MCP_TO_RETRIEVAL_TOOL)
      .filter(([, retrievalName]) => getToolByName(retrievalName) === undefined)
      .map(([mcpName, retrievalName]) => `${mcpName} → ${retrievalName}`)
    expect(unresolved, `these whitelist entries do not resolve (would 500): ${unresolved.join(', ')}`).toEqual([])
  })

  it('every SURGICAL_TOOLS retrieval name that is referenced by the whitelist has a TOOL_NAME_TO_URI entry', () => {
    const referenced = new Set(Object.values(MCP_TO_RETRIEVAL_TOOL))
    const missing = [...referenced].filter((name) => !(name in TOOL_NAME_TO_URI))
    expect(missing, `whitelisted retrieval names with no URI mapping: ${missing.join(', ')}`).toEqual([])
  })
})
