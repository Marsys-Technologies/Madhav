/**
 * Source-reviewed aggregate over the strict scalar planet-transit capability.
 *
 * The Inquiry compiler needs a complete current transit state, not an
 * arbitrarily guessed significator. This descriptor keeps the scalar schema
 * unchanged and executes exactly one single-day lookup for each canonical
 * Jyotish graha. A partial fan-out is an honest failure, never a served result.
 */
import type { CapabilityContext, ToolCapability } from '../../types'
import { stableFingerprint } from '../../knowledge/stable'
import { queryPlanetTransitCapability } from './query_planet_transit'

export const CANONICAL_TRANSIT_PLANETS = [
  'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu',
] as const

function validTemporalAnchor(value: unknown): value is string {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const parsed = new Date(`${value}T00:00:00.000Z`)
  return !Number.isNaN(parsed.valueOf())
    && parsed.toISOString().slice(0, 10) === value
    && value >= '1900-01-01'
    && value <= '2150-12-31'
}

function validatesScalarIdentity(result: Record<string, unknown>, planet: string, asOfDate: string): boolean {
  if (result['ok'] !== true || result['planet'] !== planet) return false
  const window = result['window']
  if (!window || typeof window !== 'object') return false
  const windowRecord = window as Record<string, unknown>
  if (windowRecord['start'] !== asOfDate || windowRecord['end'] !== asOfDate) return false
  const rows = result['rows']
  if (!Array.isArray(rows) || rows.length === 0 || result['count'] !== rows.length) return false
  return rows.every((row) => row !== null
    && typeof row === 'object'
    && (row as Record<string, unknown>)['body'] === planet
    && (row as Record<string, unknown>)['date'] === asOfDate)
}

export const queryCurrentTransitSnapshotCapability: ToolCapability = {
  // W-L0-4 served-surface contract: explicit declaration (detector:
  // __tests__/l0_density_contract.test.ts — do not remove; values follow the
  // deriveDensityContract evidence rules in ../../descriptor_defaults.ts).
  density_contract: {
    max_verdict_bytes: 3072,
    max_digest_bytes: 12288,
    paginated: false,
    facets: ['as_of_date'],
    empty_reason: true,
  },
  uri: 'marsys://tool/L0/query_current_transit_snapshot',
  primitive_type: 'tool',
  layer: 'L0',
  name: 'query_current_transit_snapshot',
  description:
    'Return the complete nine-graha transit state for one explicit date by invoking the strict ' +
    'scalar planet-transit capability once per canonical Jyotish body. Every component carries ' +
    'immutable argument and result hashes. The aggregate fails if any component is missing or fails.',
  input_schema: {
    type: 'object',
    properties: {
      as_of_date: {
        type: 'string',
        description: 'Explicit current-state anchor in YYYY-MM-DD format (1900-01-01 through 2150-12-31).',
      },
    },
    required: ['as_of_date'],
    additionalProperties: false,
  },
  output_schema: {
    type: 'object',
    properties: {
      ok: { type: 'boolean' },
      complete: { type: 'boolean' },
      as_of_date: { type: 'string' },
      expected_components: { type: 'number' },
      accounted_components: { type: 'number' },
      missing_planets: { type: 'array' },
      components: { type: 'array', description: 'Canonical planet results with scalar rows.' },
      component_receipts: { type: 'array', description: 'Per-planet immutable argument and result receipts.' },
      aggregate_hash: { type: 'string' },
    },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'temporal',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'temporal',
  emits_references: false,
  lel_capable: false,
  data_source: 'computed',
  // One aggregate dispatch fans out to exactly nine scalar sidecar calls. Brokers
  // must reserve this weight atomically before the handler can start any component.
  dispatch_units: CANONICAL_TRANSIT_PLANETS.length,
  llm_hints: {
    agentic: { cost_class: 'medium', always_prefetch: false, latency_ms_p50: 150 },
    bulk_context: { pre_fetch_priority: 75, always_include: false, result_size_kb_p50: 12 },
    result_max_kb: 80,
  },
  semantic_capabilities: [{
    scu_id: 'scu.catalog.query_current_transit_snapshot', version: 1, label: 'Complete current transit snapshot',
    description: 'Retrieve a complete receipted nine-graha snapshot by strictly composing the scalar transit binding.',
    kind: 'temporal', domains: ['timing'], concepts: ['transit', 'current_state'], intents: ['assess', 'verify'], horizons: ['current'], scope: 'global',
    inputs: ['as_of_date'], outputs: ['components', 'component_receipts', 'aggregate_hash', 'missing_planets'], primary_binding_uri: 'marsys://tool/L0/query_current_transit_snapshot',
    provenance_requirements: ['computed_at', 'engine_version', 'component_receipts'], freshness_policy: 'Availability is derived from the exact scalar transit binding; a missing child receipt keeps the aggregate unavailable.',
    entitlement: 'native', safety_notes: ['Every canonical component must succeed; partial snapshots are failures.'], known_gaps: [],
    availability_contracts: [{ binding_id: 'registry:marsys://tool/L0/query_current_transit_snapshot', requirements: [{
      kind: 'derived', scope: 'global', required_binding_ids: ['registry:marsys://tool/L0/query_planet_transit'],
      source_ref: 'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_current_transit_snapshot.ts#strict-nine-graha-fanout',
    }] }], editorial: false,
  }],
  async handler(args: Record<string, unknown>, ctx?: CapabilityContext) {
    const asOfDate = args['as_of_date']
    if (!validTemporalAnchor(asOfDate)) {
      return {
        ok: false,
        complete: false,
        error: 'INVALID_TEMPORAL_ANCHOR_DATE',
        as_of_date: typeof asOfDate === 'string' ? asOfDate : null,
        expected_components: CANONICAL_TRANSIT_PLANETS.length,
        accounted_components: 0,
        missing_planets: [...CANONICAL_TRANSIT_PLANETS],
        components: [],
        component_receipts: [],
      }
    }

    const components = await Promise.all(CANONICAL_TRANSIT_PLANETS.map(async (planet) => {
      const componentArgs = { planet, start_date: asOfDate, end_date: asOfDate }
      let raw: unknown
      try {
        raw = await queryPlanetTransitCapability.handler!(componentArgs, ctx)
      } catch (error) {
        raw = { ok: false, error: error instanceof Error ? error.message : 'SCALAR_TRANSIT_DISPATCH_FAILED', rows: [], count: 0 }
      }
      const result = raw && typeof raw === 'object' ? raw as Record<string, unknown> : { ok: false, error: 'INVALID_SCALAR_TRANSIT_RESULT' }
      const rows = Array.isArray(result['rows']) ? result['rows'] : []
      const served = validatesScalarIdentity(result, planet, asOfDate)
      return {
        planet,
        args: componentArgs,
        args_hash: stableFingerprint(componentArgs),
        status: served ? 'served' as const : 'failed' as const,
        rows,
        row_count: rows.length,
        result_hash: stableFingerprint(result),
        error: served
          ? null
          : typeof result['error'] === 'string'
            ? result['error']
            : rows.length === 0
              ? 'SCALAR_TRANSIT_COMPONENT_EMPTY'
              : 'SCALAR_TRANSIT_IDENTITY_MISMATCH',
      }
    }))
    const missingPlanets = components.filter((component) => component.status !== 'served').map((component) => component.planet)
    const receipts = components.map((component) => {
      const { rows, ...receipt } = component
      void rows
      return receipt
    })
    const normalized = {
      as_of_date: asOfDate,
      expected_components: CANONICAL_TRANSIT_PLANETS.length,
      accounted_components: components.length - missingPlanets.length,
      missing_planets: missingPlanets,
      components,
      component_receipts: receipts,
    }
    return {
      ok: missingPlanets.length === 0,
      complete: missingPlanets.length === 0,
      ...(missingPlanets.length ? { error: 'CURRENT_TRANSIT_SNAPSHOT_INCOMPLETE' } : {}),
      ...normalized,
      aggregate_hash: stableFingerprint(normalized),
    }
  },
}
