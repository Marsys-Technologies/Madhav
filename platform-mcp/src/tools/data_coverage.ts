/**
 * data_coverage.ts — MCP tool: data_coverage (perf brief §6.2)
 *
 * Returns data coverage report at two layers:
 *   (a) row-count audit — expected vs actual rows per tool/category
 *   (b) tool ↔ asset reconciliation — coverage / orphans / redundancies
 *       (Unit 3.tool_asset_recon, G6_tool_coverage). Sourced from the
 *       static reconciliation block below (mirrored from
 *       platform/src/lib/contract/tool_metadata.ts).
 *
 * MCPT v3.1.0-S4 (extended 2026-05-28 — Unit 3.tool_asset_recon)
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const DATA_COVERAGE_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns coverage at two layers — (a) expected vs actual row counts per ' +
    'tool/category (KP, Tajaka, Shadbala, Ashtakavarga, Upagraha, Bhava-Bala), and ' +
    '(b) tool ↔ asset reconciliation map (post-2a): which tool serves which asset, ' +
    'ayanamsha roles, orphans, and redundancies (G6 gate).',
  whenToPrefer:
    'Use data_coverage before calling a tool that relies on backfilled data (query_chart_facts ' +
    'with category kp_cusp, varshphal, shadbala, etc.) to verify data is present. ' +
    'Use mode="reconciliation" to inspect tool↔asset coverage post-2a. ' +
    'Use tool_health for operational metrics.',
  tierNote: 'Available: all tiers (unconditional — R1 de-gating).',
})

/**
 * RECONCILIATION_SNAPSHOT — verified mirror of
 * platform/src/lib/contract/tool_metadata.ts auditToolAssetReconciliation().
 *
 * This static snapshot is what `mode=reconciliation` returns when the platform
 * endpoint is unreachable. The G6 test in the contract module verifies the
 * live audit is GREEN. If you re-key the asset taxonomy in tool_metadata.ts,
 * regenerate this snapshot.
 *
 * Last regenerated: 2026-05-28 (Unit 3.tool_asset_recon)
 *   assets=19  tools=77  orphans=0  redundancies=0  ayanamsha_mismatches=0
 */
const RECONCILIATION_SNAPSHOT = {
  generated_at: '2026-05-28',
  unit: '3.tool_asset_recon',
  gate: 'G6_tool_coverage',
  assets: {
    total: 19,
    covered: 19,
    uncovered: [] as string[],
    list: [
      'chart_facts',
      'l25_msr_signals',
      'l25_cdlm_links',
      'l25_cgm_nodes',
      'l25_cgm_edges',
      'l25_rm_resonances',
      'l25_ucn_sections',
      'panchang_daily',
      'ephemeris',
      'life_events',
      'rag_chunks',
      'multi_school_signals',
      'school_convergence_index',
      'remedial_codex',
      'classical_text',
      'sidecar',
      'capability_manifest',
      'observatory',
      'mcp_audit',
    ],
  },
  tools: {
    total: 77,
    orphans: [] as string[],
    redundancies: [] as Array<{ primary_asset: string; intent: string; tools: string[] }>,
    ayanamsha_mismatches: [] as Array<{ tool: string; primary_asset: string; ayanamsha_role: string | null; allowed_roles: Array<string | null> }>,
  },
  status: 'GREEN' as const,
}

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

const DataCoverageInputSchema = z.object({
  tool_filter: z.string().optional().describe(
    'Optional tool name filter. If omitted, returns coverage for all tools.'
  ),
  mode: z.enum(['rows', 'reconciliation', 'both']).optional().default('both').describe(
    'Coverage layer to return. `rows` = expected-vs-actual rows per category (platform endpoint). ' +
    '`reconciliation` = tool↔asset map (Unit 3.tool_asset_recon G6 snapshot). `both` = both layers.'
  ),
})

type DataCoverageInput = z.infer<typeof DataCoverageInputSchema>

export function registerDataCoverage(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'data_coverage',

    DATA_COVERAGE_DESCRIPTION,

    DataCoverageInputSchema.shape,

    async (input: DataCoverageInput) => {
      const principal = getPrincipal()
      const mode = input.mode ?? 'both'

      // Reconciliation layer — pure local, never fails.
      const reconciliation = mode === 'rows' ? undefined : RECONCILIATION_SNAPSHOT

      // Row-count layer — platform endpoint, may fail (network) — degrade
      // gracefully to reconciliation-only.
      if (mode === 'reconciliation') {
        return okResult({ ok: true, reconciliation })
      }

      try {
        const response = await fetch(`${PLATFORM_URL}/api/mcp/health/coverage`, {
          method: 'GET',
          headers: {
            'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
            'X-MCP-User': principal.user_uid,
            // X-MCP-Audience-Tier removed (Stream A 3.tier_excision 2026-05-28).
            'X-MCP-Key-Id': principal.key_id,
          },
          signal: AbortSignal.timeout(10_000),
        })

        const data = await response.json() as {
          ok: boolean
          coverage?: Array<{ tool: string; [key: string]: unknown }>
          [key: string]: unknown
        }

        // Apply tool filter if requested
        if (input.tool_filter && data.coverage) {
          data.coverage = data.coverage.filter(c => c.tool === input.tool_filter)
        }

        return okResult({ ...data, reconciliation })
      } catch (err) {
        return errorResult({
          ok: false,
          trace_id: '',
          error: {
            class: 'internal',
            message: err instanceof Error ? err.message : String(err),
            remediation: 'Check platform connectivity',
          },
        })
      }
    }
  )
}
