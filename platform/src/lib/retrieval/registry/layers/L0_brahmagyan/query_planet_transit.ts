/**
 * retrieval/registry/layers/L0_brahmagyan/query_planet_transit.ts
 *
 * Tool: marsys://tool/L0/query_planet_transit
 * Query a planet's daily position series across a date range.
 * Optionally filtered by tropical sign number.
 *
 * L0FR Stream B — authored 2026-06-07
 */

import type { ToolCapability } from '../../types'

// ṢAḌ-DARŚANA W1 verify-reopen fix (items 8 + 28), 2026-07-30. This capability forwarded NO
// `x-api-key` to the sidecar. `main.py` mounts the whole `/brahmagyan/ephemeris` router behind
// `dependencies=[Depends(verify_api_key)]`, and `PYTHON_SIDECAR_API_KEY` IS set on every
// deployed service (deploy.yml wires it from Secret Manager) — so in production every call
// 401'd, this handler's `!res.ok` branch returned `{ ok: false, rows: [] }`, and every
// downstream consumer read that as a GENUINE EMPTY rather than a failure. `kala_now_get` /
// `kala_ahead_get` consequently served all-null transit fields for all 9 grahas while their
// own `coverage` asserted `state: "computed"` — a false-positive coverage claim (CLAUDE.md
// §N.8 Earned-Signal Principle).
//
// The identical defect was found and fixed for the SIBLING capability
// `query_planet_position.ts` under WP-1.7 (LCA-1, LCA-12) — including the `http://localhost:8001`
// → `:8000` default-port correction ("the prior 8001 default silently missed the bench and
// contributed to ephemeris 'returns nothing' symptoms locally"). That fix was never propagated
// to this file or its three siblings (`query_aspects_at_time`, `query_retrograde_periods`,
// `ephemeris_cache_*`). This pass propagates BOTH halves — the API key and the port default —
// plus query_planet_position.ts's honest `confidence: 'none'` transport-failure shape, so a
// sidecar outage is never again reported as a high-confidence empty.
const SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8000'
const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''

export const queryPlanetTransitCapability: ToolCapability = {
  // W-L0-4 served-surface contract: explicit declaration (detector:
  // __tests__/l0_density_contract.test.ts — do not remove; values follow the
  // deriveDensityContract evidence rules in ../../descriptor_defaults.ts).
  density_contract: {
    max_verdict_bytes: 3072,
    max_digest_bytes: 12288,
    paginated: false,
    facets: ['planet', 'start_date', 'end_date', 'sign_number'],
    empty_reason: true,
  },
  uri: 'marsys://tool/L0/query_planet_transit',
  primitive_type: 'tool',
  layer: 'L0',
  name: 'query_planet_transit',
  description:
    'Query a planet\'s transit series (daily longitude, sign, nakshatra) across a date window. ' +
    'Optionally filter by tropical sign number to find when a planet transits a specific sign. ' +
    'Use for transit windows, sign-entry/exit dates, and nakshatra progressions. ' +
    'Result set is capped and paginated. Data from ephemeris_daily (1900-2150).',
  input_schema: {
    type: 'object',
    properties: {
      planet: {
        type: 'string',
        description: 'Planet to query.',
        enum: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
      },
      start_date: {
        type: 'string',
        description: 'Start date in YYYY-MM-DD format.',
      },
      end_date: {
        type: 'string',
        description: 'End date in YYYY-MM-DD format.',
      },
      sign_number: {
        type: 'number',
        description: 'Optional: filter to rows where planet is in this sign (1=Aries through 12=Pisces, tropical).',
      },
    },
    required: ['planet', 'start_date', 'end_date'],
    additionalProperties: false,
  },
  output_schema: {
    type: 'object',
    properties: {
      ok: { type: 'boolean' },
      planet: { type: 'string' },
      rows: { type: 'array', description: 'Daily transit rows' },
      count: { type: 'number' },
    },
  },
  required_inputs: [],
  scope: 'global',
  archetype: 'temporal',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'temporal',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      always_prefetch: false,
      latency_ms_p50: 50,
    },
    bulk_context: {
      pre_fetch_priority: 70,
      always_include: false,
      result_size_kb_p50: 10,
    },
    result_max_kb: 50,
  },
  semantic_capabilities: [{
    scu_id: 'scu.catalog.query_planet_transit',
    version: 2,
    label: 'Planet transit evidence',
    description:
      'Dated planetary transit evidence. Explicit planet/window queries retain the strict scalar ' +
      'binding; current-state inquiry planning uses the reviewed complete nine-graha snapshot binding.',
    kind: 'temporal',
    domains: ['timing'],
    concepts: ['activation_timing', 'query_planet_transit', 'temporal_sequence', 'timing_window'],
    intents: ['sequence', 'time'],
    horizons: ['current', 'future', 'historical', 'multi_year'],
    scope: 'global',
    inputs: ['as_of_date', 'end_date', 'planet', 'sign_number', 'start_date'],
    outputs: ['accounted_components', 'component_receipts', 'components', 'count', 'missing_planets', 'ok', 'planet', 'rows'],
    primary_binding_uri: 'marsys://tool/L0/query_planet_transit',
    additional_bindings: [{
      binding_id: 'registry:marsys://tool/L0/query_current_transit_snapshot',
      kind: 'registry_capability',
      relation: 'provides',
      capability_uri: 'marsys://tool/L0/query_current_transit_snapshot',
      input_contract: { as_of_date: 'string:required' },
      output_contract: { structured_content: 'declared' },
      pagination: 'none',
      pagination_verified: null,
      result_collection_verified: true,
      pagination_contract: {
        result_collection_path: 'components',
        deterministic_order: ['canonical_graha_order'],
      },
      executable: true,
      execution_channels: ['platform_internal'],
      route_evidence: 'CapabilityDescriptor:marsys://tool/L0/query_current_transit_snapshot#complete-nine-graha-fanout',
    }],
    edges: [],
    provenance_requirements: ['computed_at', 'engine_version'],
    freshness_policy: 'Current-state planning requires an explicit receipted date and all nine canonical component outcomes.',
    // This scalar sidecar route is not backed by ka_gochara or a materialized
    // producer output.  Its only availability evidence is the independently
    // authenticated, exact-config ephemeris-engine probe.  Do not substitute
    // any transit materialization receipt: those prove a different path.
    availability_contracts: [{
      binding_id: 'registry:marsys://tool/L0/query_planet_transit',
      requirements: [{
        kind: 'service_probe',
        asset_id: 'bg_ephemeris_engine',
        probe_id: 'ephemeris_engine',
        endpoint_identity: 'nirmana-elevation:health-probe:bg_ephemeris_engine',
        probe_contract_sha256: 'd36262fa325fc2c29fe5ccf026d3da67120cad2280b1f7e1287bf4a327db5de1',
        max_age_seconds: 900,
        source_ref: 'platform/supabase/migrations/624_nirmana_l0_ephemeris_probe_contract.sql#bg_ephemeris_engine; platform/python-sidecar/routers/nirmana_probe.py#/internal/nirmana/probe',
      }],
    }, {
      binding_id: 'registry:marsys://tool/L0/query_current_transit_snapshot',
      requirements: [{
        kind: 'derived', scope: 'global', required_binding_ids: ['registry:marsys://tool/L0/query_planet_transit'],
        source_ref: 'platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_current_transit_snapshot.ts#strict-nine-graha-fanout',
      }],
    }],
    entitlement: 'native',
    safety_notes: ['Read-only computed evidence. Partial aggregate results are failures and cannot close a transit obligation.'],
    known_gaps: ['The scalar date-window binding is capped at 5,000 rows and is not exhaustion-proven.'],
    editorial: true,
  }],
  async handler(args: Record<string, unknown>) {
    const planet = args['planet'] as string
    const start_date = args['start_date'] as string
    const end_date = args['end_date'] as string
    const sign_number = args['sign_number'] as number | undefined

    const params = new URLSearchParams({ planet, start_date, end_date })
    if (sign_number !== undefined) params.set('sign_number', String(sign_number))

    // Forward the sidecar API key when configured (the sidecar's verify_api_key dependency
    // 401s on a missing/mismatched x-api-key when PYTHON_SIDECAR_API_KEY is set) — mirrors
    // query_planet_position.ts's WP-1.7 fix. See the header note: the absence of this header
    // is the root cause of the ṢAḌ-DARŚANA W1 items 8/28 all-null regression.
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (SIDECAR_API_KEY) headers['x-api-key'] = SIDECAR_API_KEY

    let res: Response
    try {
      res = await fetch(`${SIDECAR_URL}/brahmagyan/ephemeris/planet_transit?${params}`, { headers })
    } catch (err) {
      // Honest confidence (query_planet_position.ts WP-1.7): the sidecar being unreachable is
      // NOT a high-confidence empty. `confidence: 'none'` + a non-empty `error` is what lets a
      // consumer tell "no rows exist" from "the call failed" (CLAUDE.md §N.8).
      return {
        ok: false,
        error: `sidecar unreachable at ${SIDECAR_URL}: ${err instanceof Error ? err.message : String(err)}`,
        confidence: 'none',
        planet,
        count: 0,
        rows: [],
      }
    }
    if (!res.ok) {
      const msg = await res.text().catch(() => res.statusText)
      return {
        ok: false,
        error: `sidecar ${res.status}: ${msg}`,
        confidence: 'none',
        planet,
        count: 0,
        rows: [],
      }
    }
    return res.json()
  },
}
