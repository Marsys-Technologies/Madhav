/**
 * No mocks: every capability the shared envelope can ever authorize resolves in the REAL registry,
 * is read-only there, and survives the REAL no-leakage filter. If any target failed to resolve in
 * production the feature would be silently inert; this is the detector for that.
 */
import { describe, expect, it } from 'vitest'
import { getCatalog } from '@/lib/retrieval/registry/catalog'
import { isInquirySafeRegistryDescriptor } from './execution_policy'
import { EVIDENCE_FRONTIER_RULES } from './evidence_frontier'
import { buildAuthorizationEnvelope } from './authorization_envelope'
import { buildSuccessorAdmissionLive } from './successor_admission_live'
import { SCENARIO_CHART_ID, SCENARIO_SNAPSHOT } from './__fixtures__/successor_envelope_scenario'

describe('successor envelope targets resolve in the real registry', () => {
  it('every rule target on every transport is a registered, read-only, non-leaking, dispatchable capability', () => {
    getCatalog()
    for (const channel of ['platform_internal', 'mcp_full'] as const) {
      const envelope = buildAuthorizationEnvelope({
        snapshot: SCENARIO_SNAPSHOT, chart_id: SCENARIO_CHART_ID, execution_channel: channel,
        scope: { domains: ['general'], entitlement: 'native' }, planned_scu_ids: [], anchor_scu_ids: [],
      })
      expect(envelope.entries.length, channel).toBeGreaterThan(0)
      const live = buildSuccessorAdmissionLive({
        transport: channel === 'platform_internal' ? 'portal' : 'raw_mcp', chart_id: SCENARIO_CHART_ID,
        overlay: { overlay_version: null, build_id: null }, principal_subject: 'p', owner_principal_subject: 'p',
        chart_permission: 'all', cost_exhausted: false,
      })
      for (const entry of envelope.entries) {
        const descriptor = live.describe(entry.capability_uri)
        const binding = SCENARIO_SNAPSHOT.scus.find((scu) => scu.scu_id === entry.scu_id)!.bindings.find((candidate) => candidate.binding_id === entry.binding_id)!
        expect(descriptor, `${channel}: ${entry.capability_uri} must be registered`).toBeDefined()
        expect(isInquirySafeRegistryDescriptor(binding, descriptor), entry.capability_uri).toBe(true)
        expect(live.tool_exists(entry.capability_uri), entry.capability_uri).toBe(true)
        expect(live.is_capability_denied(entry.capability_uri), entry.capability_uri).toBe(false)
      }
    }
  })

  it('every declared rule target has at least one envelope-eligible binding on the internal channel', () => {
    const known = new Map(SCENARIO_SNAPSHOT.scus.map((scu) => [scu.scu_id, scu]))
    for (const rule of EVIDENCE_FRONTIER_RULES) for (const target of rule.target_scu_ids) {
      expect(known.get(target)?.bindings.some((binding) => binding.executable && binding.execution_channels?.includes('platform_internal')), `${rule.rule_id} -> ${target}`).toBe(true)
    }
  })
})
