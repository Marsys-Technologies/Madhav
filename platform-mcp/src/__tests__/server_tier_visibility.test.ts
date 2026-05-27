/**
 * server_tier_visibility.test.ts — R1-T1
 * Assert all 40 tools register unconditionally.
 *
 * GISMCP Remediation R1 de-gating made tiers redundant; Stream A
 * 3.tier_excision (2026-05-28) removed `audience_tier` from Principal.
 * Test retained as the "tool-count parity" invariant — exercises every
 * register* call site once.
 */

import { describe, it, expect } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Register function imports (mirrors server.ts) ─────────────────────────────
import { registerChartSummaryTool } from '../tools/chart_summary.js'
import { registerHolisticBundle } from '../tools/holistic_bundle_tool.js'
import { registerMultiSchoolBundle } from '../tools/multi_school_bundle_tool.js'
import { registerQueryChartFacts } from '../tools/query_chart_facts.js'
import { registerQuerySignals } from '../tools/query_signals.js'
import { registerQueryDashaPeriods } from '../tools/query_dasha_periods.js'
import { registerQueryPanchanga } from '../tools/query_panchanga.js'
import { registerQueryEphemeris } from '../tools/query_ephemeris.js'
import { registerQueryTransitEvent } from '../tools/query_transit_event.js'
import { registerLelQuery } from '../tools/lel_query.js'
import { registerVectorSearch } from '../tools/vector_search.js'
import { registerGetCgmSubgraph } from '../tools/get_cgm_subgraph.js'
import { registerCrossSchoolLookup } from '../tools/cross_school_lookup.js'
import { registerQueryVarshphal } from '../tools/query_varshphal.js'
import { registerQueryDivisionalChart } from '../tools/query_divisional_chart.js'
import { registerQueryRemedialMantras } from '../tools/query_remedial_mantras.js'
import { registerMuhurtaFinder } from '../tools/muhurta_finder.js'
import { registerMsrSql } from '../tools/msr_sql.js'
import { registerTemporal } from '../tools/temporal.js'
import { registerKpQuery } from '../tools/kp_query.js'
import { registerQueryKpRulingPlanets } from '../tools/query_kp_ruling_planets.js'
import { registerPatternRegister } from '../tools/pattern_register.js'
import { registerResonanceRegister } from '../tools/resonance_register.js'
import { registerClusterAtlas } from '../tools/cluster_atlas.js'
import { registerContradictionRegister } from '../tools/contradiction_register.js'
import { registerQueryUcnWalk } from '../tools/query_ucn_walk.js'
import { registerQueryCdlmLookup } from '../tools/query_cdlm_lookup.js'
import { registerQueryRmWalk } from '../tools/query_rm_walk.js'
import { registerQueryJaiminiDrishti } from '../tools/query_jaimini_drishti.js'
import { registerTimelineQuery } from '../tools/timeline_query.js'
import { registerQuerySignalState } from '../tools/query_signal_state.js'
import { registerReadAsset } from '../tools/read_asset.js'
import { registerReadClassicalText } from '../tools/read_classical_text.js'
import { registerGetTrace } from '../tools/get_trace.js'
import { registerListRecentQueries } from '../tools/list_recent_queries.js'
import { registerLogPrediction } from '../tools/log_prediction.js'
import { registerRecordOutcome } from '../tools/record_outcome.js'
import { registerFlagDisagreement } from '../tools/flag_disagreement.js'
import { registerToolHealth } from '../tools/tool_health.js'
import { registerDataCoverage } from '../tools/data_coverage.js'

// ── Mock server ───────────────────────────────────────────────────────────────

function createMockServer() {
  const registeredNames: string[] = []
  return {
    _registeredNames: registeredNames,
    // Matches the McpServer.tool() call signature used by all register functions
    tool: (name: string, ..._rest: unknown[]) => { registeredNames.push(name) },
    resource: (..._args: unknown[]) => {},
  }
}

// ── Helper: register all 40 tools with a given principal ─────────────────────

function registerAll(server: ReturnType<typeof createMockServer>, principal: Principal) {
  const getPrincipal = () => principal

  registerChartSummaryTool(server as unknown as McpServer, getPrincipal)
  registerHolisticBundle(server as unknown as McpServer, getPrincipal, undefined)
  registerMultiSchoolBundle(server as unknown as McpServer, getPrincipal, undefined)
  registerQueryChartFacts(server as unknown as McpServer, getPrincipal)
  registerQuerySignals(server as unknown as McpServer, getPrincipal)
  registerQueryDashaPeriods(server as unknown as McpServer, getPrincipal)
  registerQueryPanchanga(server as unknown as McpServer, getPrincipal)
  registerQueryEphemeris(server as unknown as McpServer, getPrincipal)
  registerQueryTransitEvent(server as unknown as McpServer, getPrincipal)
  registerLelQuery(server as unknown as McpServer, getPrincipal)
  registerVectorSearch(server as unknown as McpServer, getPrincipal)
  registerGetCgmSubgraph(server as unknown as McpServer, getPrincipal)
  registerCrossSchoolLookup(server as unknown as McpServer, getPrincipal)
  registerQueryVarshphal(server as unknown as McpServer, getPrincipal)
  registerQueryDivisionalChart(server as unknown as McpServer, getPrincipal)
  registerQueryRemedialMantras(server as unknown as McpServer, getPrincipal)
  registerMuhurtaFinder(server as unknown as McpServer, getPrincipal)
  registerMsrSql(server as unknown as McpServer, getPrincipal)
  registerTemporal(server as unknown as McpServer, getPrincipal)
  registerKpQuery(server as unknown as McpServer, getPrincipal)
  registerQueryKpRulingPlanets(server as unknown as McpServer, getPrincipal)
  registerPatternRegister(server as unknown as McpServer, getPrincipal)
  registerResonanceRegister(server as unknown as McpServer, getPrincipal)
  registerClusterAtlas(server as unknown as McpServer, getPrincipal)
  registerContradictionRegister(server as unknown as McpServer, getPrincipal)
  registerQueryUcnWalk(server as unknown as McpServer, getPrincipal)
  registerQueryCdlmLookup(server as unknown as McpServer, getPrincipal)
  registerQueryRmWalk(server as unknown as McpServer, getPrincipal)
  registerQueryJaiminiDrishti(server as unknown as McpServer, getPrincipal)
  registerTimelineQuery(server as unknown as McpServer, getPrincipal)
  registerQuerySignalState(server as unknown as McpServer, getPrincipal)
  registerReadAsset(server as unknown as McpServer, getPrincipal)
  registerReadClassicalText(server as unknown as McpServer, getPrincipal)
  registerGetTrace(server as unknown as McpServer, getPrincipal)
  registerListRecentQueries(server as unknown as McpServer, getPrincipal)
  registerLogPrediction(server as unknown as McpServer, getPrincipal)
  registerRecordOutcome(server as unknown as McpServer, getPrincipal)
  registerFlagDisagreement(server as unknown as McpServer, getPrincipal)
  registerToolHealth(server as unknown as McpServer, getPrincipal)
  registerDataCoverage(server as unknown as McpServer, getPrincipal)
}

// ── Principals ────────────────────────────────────────────────────────────────

const OPS_TOOLS = ['tool_health', 'data_coverage', 'log_prediction', 'record_outcome', 'flag_disagreement']

// `tier` arg retained for label-only purposes (test description); Principal no
// longer carries audience_tier (Stream A 3.tier_excision 2026-05-28).
const makePrincipal = (tier: string): Principal => ({
  user_uid: `uid-${tier}`,
  key_id: `key-${tier}`,
})

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('server tool registration — tier visibility (R1 de-gating)', () => {

  it('registers all 40 tools for client tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('client'))
    expect(server._registeredNames).toHaveLength(40)
  })

  it('registers all 40 tools for acharya tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('acharya'))
    expect(server._registeredNames).toHaveLength(40)
  })

  it('registers all 40 tools for super_admin tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('super_admin'))
    expect(server._registeredNames).toHaveLength(40)
  })

  it('tool_health is present for client tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('client'))
    expect(server._registeredNames).toContain('tool_health')
  })

  it('data_coverage is present for client tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('client'))
    expect(server._registeredNames).toContain('data_coverage')
  })

  it('log_prediction is present for client tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('client'))
    expect(server._registeredNames).toContain('log_prediction')
  })

  it('record_outcome is present for client tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('client'))
    expect(server._registeredNames).toContain('record_outcome')
  })

  it('flag_disagreement is present for client tier', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('client'))
    expect(server._registeredNames).toContain('flag_disagreement')
  })

  it('all ops tools present for all tiers', () => {
    for (const tier of ['client', 'acharya', 'super_admin']) {
      const server = createMockServer()
      registerAll(server, makePrincipal(tier))
      for (const opsTool of OPS_TOOLS) {
        expect(server._registeredNames, `tier=${tier} must include ${opsTool}`).toContain(opsTool)
      }
    }
  })

  it('tool count is identical across all tiers (40 each)', () => {
    const counts = ['client', 'acharya', 'super_admin'].map(tier => {
      const server = createMockServer()
      registerAll(server, makePrincipal(tier))
      return server._registeredNames.length
    })
    expect(counts[0]).toBe(40)
    expect(counts[1]).toBe(40)
    expect(counts[2]).toBe(40)
  })

  it('no duplicate tool registrations', () => {
    const server = createMockServer()
    registerAll(server, makePrincipal('super_admin'))
    const unique = new Set(server._registeredNames)
    expect(unique.size).toBe(server._registeredNames.length)
  })
})
