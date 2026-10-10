import { describe, expect, it } from 'vitest'
import snapshotJson from '../../../src/generated/capability_knowledge.snapshot.json'
import type { CapabilityKnowledgeSnapshot } from '../../../src/lib/retrieval/registry/knowledge/types'
import { buildCapabilityCoverage } from '../capability_coverage'
import { getCatalog } from '../../../src/lib/retrieval/registry/catalog'
import { compileCapabilityKnowledge } from '../../../src/lib/retrieval/registry/knowledge/compiler'
import { loadChartCapabilityOverlay } from '../../../src/lib/retrieval/registry/knowledge/overlay_loader'

const snapshot = snapshotJson as CapabilityKnowledgeSnapshot

describe('Purna capability coverage projection', () => {
  it('preserves the complete generated denominator and exposes the contract deficit', () => {
    const rows = buildCapabilityCoverage(snapshot)
    // R3 boundary (native strategic ruling packets 1-4): get_av_transit_gating and
    // synergy_pipeline each gained a genuine second, per-mode binding (kakshya_windows /
    // dry_run) — the coverage denominator is per-BINDING, so 186 -> 188 rows even though the
    // SCU count (182) is unchanged. SS N-373: ephemeris_cache_native_lifetime retired (one SCU, one
    // binding) — 188 -> 187 rows, 182 -> 181 SCUs.
    expect(rows).toHaveLength(187)
    expect(new Set(rows.map((row) => row.coverage_id)).size).toBe(187)
    expect(new Set(rows.map((row) => row.scu_id)).size).toBe(181)
    // synergy_pipeline is no longer missing: its executed mode is now contracted (derived,
    // 6 legs) and its dry_run mode is contracted (snapshot_resource, proof_kind 'plan') —
    // genuine per-mode proof typing closed the type-system gap the prior comment described.
    // query_sutravali_rules_for_planet is no longer missing: its sidecar route's real
    // parameter-binding bug (python-sidecar/routers/sutravali.py) is fixed and it is now
    // contracted like its siblings. Remaining missing (2): classical_attribution_lookup
    // (fails closed by design — the underlying tables were permanently retired in WS-0; an
    // empty result would falsely imply "classically silent") and query_muhurat (its sidecar
    // route has no matching registered nirmana-elevation health-probe asset; deferred to a
    // later phase of this same campaign, not fabricated here). Remaining deliberately_dark
    // (3 rows): call_transit_search (L3 Kāla campaign ownership boundary, untouched),
    // channel_chat_dispatch (legacy-route disposition, unchanged), and get_av_transit_gating's
    // kakshya_windows binding specifically (its sav_bav_gating default binding remains
    // separately, statically proven and counted under "authored" above).
    expect(rows.filter((row) => row.blocker === 'availability_contract_missing')).toHaveLength(2)
    expect(rows.filter((row) => row.availability_contract === 'authored')).toHaveLength(182)
    expect(rows.filter((row) => row.availability_contract === 'deliberately_dark')).toHaveLength(3)
  })

  it('keeps semantic outputs, bindings, and exact evidence dependencies together', () => {
    const mechanism = buildCapabilityCoverage(snapshot).find((row) => row.scu_id === 'scu.bodha.mechanism.network')
    expect(mechanism).toMatchObject({
      outputs: expect.arrayContaining(['mechanisms']),
      binding_id: 'registry:marsys://tool/L2/query_mechanisms',
      availability_contract: 'authored',
      source_dependencies: expect.arrayContaining(['producer:bo_yantra_mechanism']),
      blocker: 'overlay_not_measured',
    })
  })

  it('keeps every executable binding occurrence when one SCU exposes multiple routes', () => {
    const rows = buildCapabilityCoverage(snapshot)
    expect(rows.filter((row) => row.scu_id === 'scu.catalog.get_divisionals')).toHaveLength(2)
    expect(rows.filter((row) => row.scu_id === 'scu.catalog.query_planet_transit')).toHaveLength(2)
    expect(rows.filter((row) => row.scu_id === 'scu.finance.prosperity_assessment')).toHaveLength(2)
    expect(rows.filter((row) => row.scu_id === 'scu.yoga.firing_and_cancellation')).toHaveLength(2)

    const sharedBindingId = rows.filter((row) =>
      row.binding_id === 'registry:marsys://tool/L0/query_current_transit_snapshot')
    expect(sharedBindingId).toHaveLength(2)
    expect(new Set(sharedBindingId.map((row) => row.scu_id))).toEqual(new Set([
      'scu.catalog.query_current_transit_snapshot',
      'scu.catalog.query_planet_transit',
    ]))
  })

  it('reports plan/resource/discovery capabilities as resource_ok, never as dark answer routes (RC-7)', async () => {
    const compiled = compileCapabilityKnowledge(getCatalog(), '2026-09-27T00:00:00.000Z') as CapabilityKnowledgeSnapshot
    const overlay = await loadChartCapabilityOverlay(compiled, '482012f1-710e-4a25-994a-93821f5871aa', async () => ({ rows: [] }))
    const rows = buildCapabilityCoverage(compiled, overlay)
    const resources = rows.filter((row) => row.proof_kind !== 'answer')
    expect(resources.map((row) => row.scu_id).sort()).toEqual([
      'scu.catalog.channel_mcp_wiring', 'scu.catalog.intent_classify', 'scu.catalog.maro_mcp_surface',
      'scu.catalog.maro_orchestrate', 'scu.catalog.maro_profiles', 'scu.catalog.route', 'scu.catalog.tool_search',
    ])
    for (const row of resources) {
      expect(row).toMatchObject({ readiness: 'resource_ok', blocker: 'resource_not_answer', availability_contract: 'authored' })
      expect(row.source_dependencies[0]).toMatch(/^snapshot:/)
    }
  })
})
