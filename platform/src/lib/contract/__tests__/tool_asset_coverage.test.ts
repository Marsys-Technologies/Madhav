/**
 * tool_asset_coverage.test.ts — Unit 3.tool_asset_recon G6 gate (acceptance test).
 *
 * Asserts the tool ↔ asset reconciliation invariants post-2a:
 *
 *   AC.1  data_coverage reports 100% asset coverage + 0 orphaned tools +
 *         0 redundant duplicates.
 *   AC.2  Every ayanamsha-dependent tool declares its ayanamsha_role; none
 *         reads across roles disallowed by the asset's declared role set.
 *   AC.3  Every live retrieval/MCP tool name has an entry in TOOL_METADATA
 *         (no portal/MCP tool is missing from the reconciliation table).
 *   AC.4  Every per_chart tool's metadata flag matches the contract registry
 *         where the tool is registered (where applicable).
 *
 * The audit walks two surfaces:
 *   - portal RETRIEVAL_TOOLS (ALL_21_RETRIEVAL_TOOLS from lib/trace/types — D7 migration retired lib/retrieve)
 *   - MCP CATALOG (platform-mcp/src/tools/catalog.ts)
 */

import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'

import {
  TOOL_METADATA,
  TOOL_METADATA_BY_NAME,
  TOOL_METADATA_NAMES,
  EXPECTED_ASSETS,
  auditToolAssetReconciliation,
  isReconciliationGreen,
} from '../tool_metadata'

import { ALL_21_RETRIEVAL_TOOLS } from '../../trace/types'
import { TOOL_CONTRACTS } from '../registry'

/**
 * Read the live MCP CATALOG names by parsing the catalog source file. We
 * cannot import the MCP module directly: it pulls a separate TS package with
 * its own zod alias chain, and Vitest's import resolver would have to climb
 * out of the platform/ root. Reading the source file via fs is the same
 * verified-mirror discipline contract_bridge.ts uses.
 */
function readMcpCatalogNames(): string[] {
  const catalogPath = path.resolve(
    __dirname,
    '../../../../../platform-mcp/src/tools/catalog.ts'
  )
  const src = fs.readFileSync(catalogPath, 'utf8')
  // Lines look like:   { name: 'query_chart_facts', description: ... },
  const names: string[] = []
  const re = /^\s*\{\s*name:\s*'([a-z_0-9]+)'\s*,/gm
  let m: RegExpExecArray | null
  while ((m = re.exec(src)) !== null) {
    names.push(m[1])
  }
  return names
}
const MCP_CATALOG_NAMES = readMcpCatalogNames()

describe('Unit 3.tool_asset_recon — tool ↔ asset reconciliation (G6 gate)', () => {
  it('AC.1 — data_coverage reports 100% asset coverage + 0 orphans + 0 redundancies', () => {
    const report = auditToolAssetReconciliation()

    // Print a tiny summary line for log readability (vitest --reporter=verbose surfaces this).
    // eslint-disable-next-line no-console
    console.log(
      `[G6] assets=${report.total_assets} tools=${report.total_tools} ` +
      `covered=${report.covered_assets.length} uncovered=${report.uncovered_assets.length} ` +
      `orphans=${report.orphaned_tools.length} redundancies=${report.redundancies.length} ` +
      `ayanamsha_mismatches=${report.ayanamsha_mismatches.length}`
    )

    expect(report.total_assets).toBe(EXPECTED_ASSETS.length)
    expect(report.total_tools).toBe(TOOL_METADATA.length)

    expect(
      report.uncovered_assets,
      `uncovered assets:\n${report.uncovered_assets.join('\n')}`
    ).toEqual([])

    expect(
      report.orphaned_tools,
      `orphaned tools (primary_asset not in EXPECTED_ASSETS):\n${report.orphaned_tools.join('\n')}`
    ).toEqual([])

    expect(
      report.redundancies,
      `redundancies (same (primary_asset, intent) on >1 non-alias tool):\n` +
      report.redundancies.map(r => `  ${r.primary_asset} / ${r.intent}: ${r.tools.join(', ')}`).join('\n')
    ).toEqual([])

    expect(isReconciliationGreen()).toBe(true)
  })

  it('AC.2 — every ayanamsha-dependent tool reads in an allowed role for its asset', () => {
    const report = auditToolAssetReconciliation()

    expect(
      report.ayanamsha_mismatches,
      `ayanamsha-role mismatches:\n` +
      report.ayanamsha_mismatches
        .map(m => `  ${m.tool} → ${m.primary_asset} reads as ${m.ayanamsha_role}, asset allows ${JSON.stringify(m.allowed_roles)}`)
        .join('\n')
    ).toEqual([])

    // Spot-check the engine-isolation contract: KP tools never read in canonical, vice versa.
    const kpTools = TOOL_METADATA.filter(t => t.ayanamsha_role === 'kp')
    expect(kpTools.length, 'must have ≥1 KP-bound tool').toBeGreaterThan(0)
    for (const t of kpTools) {
      // KP tools should be on a kp-allowed asset (chart_facts is shared canonical|kp).
      expect(t.primary_asset, `${t.canonical_name} reads chart_facts in kp role`).toBe('chart_facts')
    }

    const canonicalTools = TOOL_METADATA.filter(t => t.ayanamsha_role === 'canonical')
    expect(canonicalTools.length, 'must have ≥1 canonical-bound tool').toBeGreaterThan(0)
  })

  it('AC.3 — every live portal + MCP tool name has a TOOL_METADATA entry', () => {
    const portalNames = new Set(ALL_21_RETRIEVAL_TOOLS as readonly string[])
    const mcpNames = new Set(MCP_CATALOG_NAMES)
    const metadataNames = new Set(TOOL_METADATA_NAMES)

    // Portal coverage
    const portalMissing: string[] = []
    for (const n of portalNames) {
      if (!metadataNames.has(n)) portalMissing.push(n)
    }
    expect(
      portalMissing,
      `portal tools missing from TOOL_METADATA:\n${portalMissing.join('\n')}`
    ).toEqual([])

    // MCP coverage
    const mcpMissing: string[] = []
    for (const n of mcpNames) {
      if (!metadataNames.has(n)) mcpMissing.push(n)
    }
    expect(
      mcpMissing,
      `MCP tools missing from TOOL_METADATA:\n${mcpMissing.join('\n')}`
    ).toEqual([])

    // Reverse direction: every metadata entry must appear on at least one surface
    // (portal or MCP), per its declared `surface`.
    const stale: string[] = []
    for (const t of TOOL_METADATA) {
      const onPortal = portalNames.has(t.canonical_name)
      const onMcp = mcpNames.has(t.canonical_name)
      const expectPortal = t.surface === 'portal' || t.surface === 'both'
      const expectMcp = t.surface === 'mcp' || t.surface === 'both'
      if (expectPortal && !onPortal) stale.push(`${t.canonical_name}: declared surface=${t.surface} but missing on portal`)
      if (expectMcp && !onMcp) stale.push(`${t.canonical_name}: declared surface=${t.surface} but missing on MCP`)
    }
    expect(
      stale,
      `TOOL_METADATA entries whose declared surface disagrees with the live registry:\n${stale.join('\n')}`
    ).toEqual([])
  })

  it('AC.4 — per_chart flag agrees with contract registry where overlap exists', () => {
    // Cross-check against the unified contract registry (Unit 2b). Only tools
    // that appear in both surfaces need to agree.
    const mismatches: string[] = []
    for (const c of TOOL_CONTRACTS) {
      const meta = TOOL_METADATA_BY_NAME.get(c.canonical_name)
      if (!meta) {
        mismatches.push(`${c.canonical_name}: in contract registry but missing from TOOL_METADATA`)
        continue
      }
      if (meta.per_chart !== c.per_chart) {
        mismatches.push(
          `${c.canonical_name}: per_chart mismatch — contract=${c.per_chart}, metadata=${meta.per_chart}`
        )
      }
    }
    expect(mismatches, `per_chart mismatches:\n${mismatches.join('\n')}`).toEqual([])
  })

  it('AC.5 — every alias declares a valid alias_of target', () => {
    const names = new Set(TOOL_METADATA_NAMES)
    const bad: string[] = []
    for (const t of TOOL_METADATA) {
      if (!t.is_alias) continue
      if (!t.alias_of) {
        bad.push(`${t.canonical_name}: is_alias=true but no alias_of declared`)
        continue
      }
      if (!names.has(t.alias_of)) {
        bad.push(`${t.canonical_name}: alias_of=${t.alias_of} not found in TOOL_METADATA`)
      }
    }
    expect(bad, `alias issues:\n${bad.join('\n')}`).toEqual([])
  })
})
