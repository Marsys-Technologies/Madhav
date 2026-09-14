import { describe, expect, it } from 'vitest'
import { getCatalog } from '../catalog'
import { compileCapabilityKnowledge, inspectCapabilityKnowledge } from './compiler'
import { compileChartCapabilityOverlay, assertOverlayCompatibility } from './overlay'
import { inspectSemanticCapability, searchSemanticCapabilities } from './query'
import type { CapabilityKnowledgeSnapshot, SemanticCapabilityUnit } from './types'

describe('planner capability knowledge', () => {
  const catalog = getCatalog()
  const snapshot = compileCapabilityKnowledge(catalog, '2026-09-13T00:00:00.000Z')

  it('compiles a total, deterministic snapshot from the live catalog', () => {
    const second = compileCapabilityKnowledge(catalog, '2026-09-14T00:00:00.000Z')
    expect(snapshot.census.runtime_descriptors).toBe(catalog.length)
    expect(snapshot.census.addressable_descriptors + snapshot.census.excluded_descriptors).toBe(catalog.length)
    expect(snapshot.census.semantic_capabilities).toBe(snapshot.scus.length)
    expect(snapshot.content_hash).toMatch(/^sha256:[a-f0-9]{64}$/)
    expect(second.content_hash).toBe(snapshot.content_hash)
    expect(Object.isFrozen(snapshot)).toBe(true)
    const report = inspectCapabilityKnowledge(catalog, snapshot)
    expect(report.passed).toBe(true)
    expect(report.findings.every((finding) => finding.severity === 'warning')).toBe(true)
    expect(report.findings.map((finding) => finding.code)).toContain('BAD_PAGINATION_CONTRACT')
  })

  it('keeps SCUs distinct from tools with many-to-many executable bindings', () => {
    const finance = snapshot.scus.find((scu) => scu.scu_id === 'scu.finance.prosperity_assessment')
    const yoga = snapshot.scus.find((scu) => scu.scu_id === 'scu.yoga.firing_and_cancellation')
    expect(finance?.bindings).toHaveLength(2)
    expect(yoga?.bindings).toHaveLength(2)
    expect(finance?.bindings.every((binding) => binding.executable)).toBe(true)
    expect(yoga?.bindings.find((binding) => binding.relation === 'primary')?.public_tool_name).toBe('ganita_yoga_firings_get')
    expect(snapshot.census.publicly_named_bindings).toBeGreaterThan(0)
    expect(snapshot.census.reviewed_output_claims).toBe(7)
    expect(snapshot.scus.flatMap((scu) => scu.producer_output_claims ?? [])
      .filter((claim) => claim.disposition === 'reviewed_output')
      .every((claim) => /^[a-f0-9]{64}$/.test(claim.output_digest_spec_sha256 ?? ''))).toBe(true)
  })

  it('normalizes legacy flat and JSON Schema input dialects without losing required fields', () => {
    const transit = snapshot.scus.find((scu) => scu.scu_id === 'scu.catalog.query_planet_transit')
    expect(transit?.inputs).toEqual(expect.arrayContaining(['planet', 'start_date', 'end_date']))
    expect(transit?.bindings[0]?.input_contract).toMatchObject({
      planet: 'string:required', start_date: 'string:required', end_date: 'string:required',
    })
    expect(transit?.bindings[0]?.input_contract).not.toHaveProperty('properties')
  })

  it('provides staged discovery, graph inspection, and bounded depth', () => {
    expect(searchSemanticCapabilities(snapshot, 'finance prosperity mechanisms', 5)[0]?.scu_id).toBe('scu.finance.prosperity_assessment')
    const graph = inspectSemanticCapability(snapshot, 'scu.finance.prosperity_assessment', 2)
    expect(graph.root?.kind).toBe('assessment')
    expect(graph.nodes.map((node) => node.scu_id)).toContain('scu.bodha.mechanism.network')
    expect(graph.edges.every((edge) => snapshot.scus.some((scu) => scu.scu_id === edge.to_scu_id))).toBe(true)
  })

  it('fails CI-style integrity for duplicate SCUs, stale edges, and non-executable bindings', () => {
    const first = snapshot.scus[0] as SemanticCapabilityUnit
    const broken = {
      ...snapshot,
      scus: [
        ...snapshot.scus,
        { ...first, bindings: first.bindings.map((binding) => ({ ...binding, executable: false })) },
      ],
      edges: [...snapshot.edges, { from_scu_id: first.scu_id, relation: 'requires' as const, to_scu_id: 'scu.missing', rationale: 'fixture' }],
    } as CapabilityKnowledgeSnapshot
    const report = inspectCapabilityKnowledge(catalog, broken)
    expect(report.passed).toBe(false)
    expect(new Set(report.findings.map((finding) => finding.code))).toEqual(expect.objectContaining(new Set(['DUPLICATE_SCU', 'STALE_EDGE', 'NON_EXECUTABLE_BINDING'])))
  })

  it('rejects a reviewed producer-output claim without an exact specification hash', () => {
    const source = snapshot.scus.find((scu) => (scu.producer_output_claims?.length ?? 0) > 0)!
    const broken = {
      ...snapshot,
      scus: snapshot.scus.map((scu) => scu.scu_id === source.scu_id
        ? { ...scu, producer_output_claims: [{ ...scu.producer_output_claims![0]!, disposition: 'reviewed_output' as const, output_digest_spec_sha256: null }] }
        : scu),
    } as CapabilityKnowledgeSnapshot
    expect(inspectCapabilityKnowledge(catalog, broken).findings).toContainEqual(expect.objectContaining({ code: 'BAD_PRODUCER_OUTPUT_CLAIM', severity: 'error' }))
  })

  it('keeps chart availability separate and rejects a stale compatibility pair', () => {
    const overlay = compileChartCapabilityOverlay({ snapshot, chart_id: 'chart-fixture', build_id: 'build-fixture', evidence: [], generated_at: '2026-09-13T00:00:00.000Z' })
    expect(overlay.availability.every((item) => item.state === 'dark')).toBe(true)
    expect(() => assertOverlayCompatibility(snapshot, overlay)).not.toThrow()
    expect(() => assertOverlayCompatibility(snapshot, overlay, 'other-chart')).toThrow('CAPABILITY_OVERLAY_CHART_MISMATCH')
    expect(() => assertOverlayCompatibility(snapshot, { ...overlay, catalog_content_hash: 'sha256:stale' })).toThrow('CAPABILITY_OVERLAY_INCOMPATIBLE')
  })
})
