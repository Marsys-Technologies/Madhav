/**
 * D5 Fan-Out — Roster Completeness Smoke Test
 * =============================================
 * Verifies that all D5 capability URIs declared in register_d5_fanout.ts
 * are importable and pass the chart_agnostic_gate.
 *
 * This is the "roster-completeness smoke" required by the parallel coordination
 * brief §4 (Fan-out 2: "run a roster-completeness smoke after D5 sub-waves merge").
 *
 * Coverage:
 *   1. All 28 D5 URIs are present in D5_CAPABILITY_URIS
 *   2. Each URI's capability is importable and has handler function
 *   3. chart_agnostic_gate passes for all D5 capabilities (0 violations)
 *   4. No duplicate URIs across D5 roster
 *   5. All per_chart tools have chart_id in required_inputs
 *   6. No NATIVE_CHART_ID in any capability descriptor
 *
 * [verify-against: prod] — DB connectivity checked in integration test suite.
 */

import { describe, it, expect } from 'vitest'
import { checkCapability } from '../../chart_agnostic_gate'

// D5 URI roster (mirrors register_d5_fanout.ts D5_CAPABILITY_URIS — kept in sync manually)
// We do NOT import register_d5_fanout directly to avoid pulling @/lib/db/client
// through traverse_chart_graph.ts → @/lib/db/client in the unit test environment.
const D5_CAPABILITY_URIS = [
  // L2 Bodha
  'marsys://tool/L2/query_domain_reading',
  'marsys://tool/L2/query_signals',
  'marsys://tool/L2/query_contradictions',
  'marsys://tool/L2/query_remedies',
  'marsys://tool/L2/query_quality_scorecard',
  // L3 Kāla — data
  'marsys://tool/L3/query_temporal_activation',
  'marsys://tool/L3/query_convergence_windows',
  'marsys://tool/L3/query_life_arc',
  'marsys://tool/L3/query_projections',
  'marsys://tool/L3/query_obstruction_periods',
  'marsys://tool/L3/query_temporal_view',
  // L3 Kāla — service wrappers
  'marsys://tool/L3/call_transit_search',
  'marsys://tool/L3/call_ephemeris_at_t',
  'marsys://tool/L3/call_dasha_eligibility',
  'marsys://tool/L3/call_muhurta_score',
  'marsys://tool/L3/call_priority_ranking',
  // L4 Phala
  'marsys://tool/L4/query_predictive_anchors',
  'marsys://tool/L4/query_domain_result',
  'marsys://tool/L4/query_auspicious_windows',
  'marsys://tool/L4/query_spillover_cascades',
  'marsys://tool/L4/query_falsifiers',
  'marsys://tool/L4/query_anomaly_flags',
  'marsys://tool/L4/query_remedy_program',
  'marsys://tool/L4/query_cleansed_anchors',
  'marsys://tool/L4/query_rectification',
  // L5 Mīmāṃsā
  'marsys://tool/L5/query_predictions',
  'marsys://tool/L5/query_signal_families',
  'marsys://tool/L5/query_manifestation_grammar',
] as const

// Import all D5 capabilities
import { queryDomainReadingCapability }    from '../L2_bodha/query_domain_reading'
import { querySignalsCapability }          from '../L2_bodha/query_signals'
import { queryContradictionsCapability }   from '../L2_bodha/query_contradictions'
import { queryRemediesCapability }         from '../L2_bodha/query_remedies'
import { queryQualityScorecardCapability } from '../L2_bodha/query_quality_scorecard'
import { queryTemporalActivationCapability }  from '../L3_kala/query_temporal_activation'
import { queryConvergenceWindowsCapability }  from '../L3_kala/query_convergence_windows'
import { queryLifeArcCapability }             from '../L3_kala/query_life_arc'
import { queryProjectionsCapability }         from '../L3_kala/query_projections'
import { queryObstructionPeriodsCapability }  from '../L3_kala/query_obstruction_periods'
import { queryTemporalViewCapability }        from '../L3_kala/query_temporal_view'
import {
  callTransitSearchCapability,
  callEphemerisAtTCapability,
  callDashaEligibilityCapability,
  callMuhurtaScoreCapability,
  callPriorityRankingCapability,
} from '../L3_kala/call_service_wrappers'
import { queryPredictiveAnchorsCapability } from '../L4_phala/query_predictive_anchors'
import { queryDomainResultCapability }      from '../L4_phala/query_domain_result'
import {
  queryAuspiciousWindowsCapability,
  querySpilloverCascadesCapability,
  queryFalsifiersCapability,
  queryAnomalyFlagsCapability,
  queryRemedyProgramCapability,
  queryCleasedAnchorsCapability,
  queryRectificationCapability,
} from '../L4_phala/query_phala_calibration'
import { queryPredictionsCapability }        from '../L5_mimamsa/query_predictions'
import { querySignalFamiliesCapability }     from '../L5_mimamsa/query_signal_families'
import { queryManifestationGrammarCapability } from '../L5_mimamsa/query_manifestation_grammar'
import type { CapabilityDescriptor } from '../../types'

const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const ALL_D5_CAPS: CapabilityDescriptor[] = [
  queryDomainReadingCapability,
  querySignalsCapability,
  queryContradictionsCapability,
  queryRemediesCapability,
  queryQualityScorecardCapability,
  queryTemporalActivationCapability,
  queryConvergenceWindowsCapability,
  queryLifeArcCapability,
  queryProjectionsCapability,
  queryObstructionPeriodsCapability,
  queryTemporalViewCapability,
  callTransitSearchCapability,
  callEphemerisAtTCapability,
  callDashaEligibilityCapability,
  callMuhurtaScoreCapability,
  callPriorityRankingCapability,
  queryPredictiveAnchorsCapability,
  queryDomainResultCapability,
  queryAuspiciousWindowsCapability,
  querySpilloverCascadesCapability,
  queryFalsifiersCapability,
  queryAnomalyFlagsCapability,
  queryRemedyProgramCapability,
  queryCleasedAnchorsCapability,
  queryRectificationCapability,
  queryPredictionsCapability,
  querySignalFamiliesCapability,
  queryManifestationGrammarCapability,
]

describe('D5 Roster Completeness Smoke', () => {
  it('D5_CAPABILITY_URIS has exactly 28 entries', () => {
    expect(D5_CAPABILITY_URIS).toHaveLength(28)
  })

  it('ALL_D5_CAPS array has exactly 28 capabilities', () => {
    expect(ALL_D5_CAPS).toHaveLength(28)
  })

  it('No duplicate URIs in D5 roster', () => {
    const uris = ALL_D5_CAPS.map(c => c.uri)
    const unique = new Set(uris)
    expect(unique.size).toBe(uris.length)
  })

  it('All D5 URIs declared in register_d5_fanout match actual capability URIs', () => {
    const actualUris = new Set(ALL_D5_CAPS.map(c => c.uri))
    for (const uri of D5_CAPABILITY_URIS) {
      expect(actualUris.has(uri), `URI not found in capabilities: ${uri}`).toBe(true)
    }
  })

  it('All D5 capabilities have handler function', () => {
    for (const cap of ALL_D5_CAPS) {
      expect(typeof cap.handler, `${cap.name}: missing handler`).toBe('function')
    }
  })

  it('No native chart UUID in any D5 capability descriptor', () => {
    for (const cap of ALL_D5_CAPS) {
      expect(cap.description, `${cap.name}: native UUID in description`).not.toContain(NATIVE_CHART_ID)
      expect(cap.uri, `${cap.name}: native UUID in URI`).not.toContain(NATIVE_CHART_ID)
    }
  })

  it('All per_chart D5 capabilities have chart_id in required_inputs', () => {
    for (const cap of ALL_D5_CAPS) {
      if (cap.scope === 'per_chart') {
        expect(cap.required_inputs, `${cap.name}: missing chart_id in required_inputs`).toContain('chart_id')
      }
    }
  })

  it('All D5 capabilities pass chart_agnostic_gate with 0 violations', () => {
    for (const cap of ALL_D5_CAPS) {
      const violations = checkCapability(cap)
      expect(violations, `${cap.name}: ${JSON.stringify(violations)}`).toHaveLength(0)
    }
  })

  it('All per_chart D5 handlers return is_error=true when chart_id missing', async () => {
    const perChartCaps = ALL_D5_CAPS.filter(c => c.scope === 'per_chart')
    // Skip stubbed tools (they return is_error=true for missing chart_id too, but verify)
    for (const cap of perChartCaps) {
      const result = await cap.handler({}, undefined)
      expect(result.is_error, `${cap.name}: should error without chart_id`).toBe(true)
    }
  })

  // WP-1.3(a) / F-L10-012,018 (LCA-19): formerly-STUBBED obstruction & temporal_view
  // tools now serve real rows from populated tables — they no longer advertise stubbing.
  it('formerly-stubbed tools no longer advertise STUBBED-PENDING-DATA', () => {
    const unstubbed = [queryObstructionPeriodsCapability, queryTemporalViewCapability]
    for (const cap of unstubbed) {
      expect(cap.description, `${cap.name}: should no longer be stubbed`).not.toContain('STUBBED-PENDING-DATA')
    }
  })
})
