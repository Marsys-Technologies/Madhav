/**
 * query_prospective_ledger — Standing Prospective Predictions (brahma_prospective_ledger)
 * ========================================================================================
 * The read side of the LIVE prospective prediction store (`brahma_prospective_ledger`,
 * migration 458 — D-4a Lane A-4). Serves the OPEN filed, falsifiable predictions for a
 * chart, each carrying its claim, event_class, temporal shape + window/milestones,
 * confidence, MANDATORY falsifier, generator_class, source_citation, and lifecycle_status.
 *
 * WHY THIS CAPABILITY EXISTS (SARVA-SIDDHI W-2 P-1, 2026-07-24):
 * The Vidhi E-2 primitive `standing_predictions_read` is DEFINED as a "prospective-ledger
 * read" but was wired (VIDHI-PŪRṆATĀ P-3b) to `phala_predictive_anchors_get` — an L4
 * *phala_anchors* surface (deterministic ph_nimitta rows), NOT the filed prospective
 * ledger. For a wealth plan `phala_anchors` returns empty, so the native's genuinely-filed
 * standing predictions (Sat–Jupiter Apr–Aug 2027, Ketu-MD shape, Venus-MD 2034 — all filed
 * 2026-07-19 in the D-4a Lane A-4 session, provenance intact in the ledger) never surfaced.
 * This is the exact PRE_DARPANA_READINESS B-2 FAIL. This capability repoints E-2 at the
 * table it was always meant to read.
 *
 * §11 governance (TEMPORAL_ENGINE_ARC_PLAN §11): predictions exist by EXPLICIT FILING only;
 * chat is never mined. This is a READ surface — confirmation/disclosure ONLY, never a
 * calibration or filing write. The §11 governance text is served on the surface itself.
 *
 * DOMAIN LAYERING (§N.6 Serving Density Principle): when a `domain` is given, predictions
 * whose event_class resolves (via brahma_event_ontology.domain) into that domain's material
 * cluster lead the response as `predictions`; every OTHER open prediction is STILL returned
 * (never silently dropped — B.10) under `other_domain_predictions`, with counts. An empty
 * result carries an explicit `empty_reason` (the B-1/A-6 silent-empty this lane must not
 * repeat), never a bare `{predictions:[]}`.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import {
  deriveWindowFields,
  PROSPECTIVE_LEDGER_GOVERNANCE_TEXT,
  type ProspectiveLedgerRow,
} from '@/lib/lel/prospective_ledger'

// ── Domain → event-class-domain cluster ──────────────────────────────────────────
//
// A Vidhi plan passes a single question `domain` (e.g. 'wealth'). Ledger rows are keyed by
// `event_class`, whose canonical life-domain lives on brahma_event_ontology.domain. Most
// domains map to themselves; the documented exception is the MATERIAL/ASSET cluster: a
// wealth reading legitimately owns property/residence acquisition (an asset event bearing
// directly on the native's wealth base), so `wealth` clusters {wealth, residence}. This is
// why the native's Venus-MD-2034 property_acquisition prediction (ontology domain
// 'residence') correctly surfaces on a wealth/timing plan alongside the two major_gain
// predictions (Sat–Jupiter 2027, Ketu-MD shape). Everything not in the cluster is still
// returned under other_domain_predictions — the cluster governs ORDER/LAYERING, not dropping.
const DOMAIN_CLUSTERS: Readonly<Record<string, readonly string[]>> = {
  wealth: ['wealth', 'residence'],
}

function clusterFor(domain: string | undefined): readonly string[] | null {
  if (!domain) return null
  const key = domain.trim().toLowerCase()
  if (!key) return null
  return DOMAIN_CLUSTERS[key] ?? [key]
}

type LedgerRowWithDomain = ProspectiveLedgerRow & { ontology_domain: string | null }

/** Shape one ledger row into a served prediction (adds human-facing window fields). */
function toServed(row: LedgerRowWithDomain) {
  const win = deriveWindowFields(row)
  return {
    prediction_id: row.prediction_id,
    claim: row.claim,
    event_class: row.event_class,
    ontology_domain: row.ontology_domain,
    claim_shape: row.claim_shape,
    point_date: win.point_date,
    window_start: win.window_start,
    window_end: win.window_end,
    milestone_set: row.milestone_set,
    confidence: row.confidence,
    falsifier: row.falsifier,
    generator_class: row.generator_class,
    lifecycle_status: row.lifecycle_status,
    model: row.model,
    formula_version: row.formula_version,
    configuration_signature: row.configuration_signature,
    as_of: row.as_of,
    filed_by: row.filed_by,
    source_citation: row.source_citation,
  }
}

export const queryProspectiveLedgerCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L4/query_prospective_ledger',
  type:  'tool',
  layer: 'L4',
  name:  'query_prospective_ledger',

  description: [
    'Returns the OPEN filed, falsifiable standing predictions for a chart from the LIVE',
    'prospective ledger (brahma_prospective_ledger, migration 458 — D-4a Lane A-4).',
    'Each prediction carries: claim, event_class, temporal shape (point/interval/chain)',
    'with its window or milestone_set, confidence, a MANDATORY falsifier, generator_class',
    '(reading_synthesis | engine | native_intuition | anchor_engine), source_citation, and',
    'lifecycle_status. §11 governance: predictions exist by explicit filing only — this is a',
    'READ/confirmation surface, never a filing or calibration write.',
    'Filter by domain (question domain — wealth clusters {wealth, residence} as the material/',
    'asset cluster) and lifecycle_status. Non-domain-matching open predictions are still',
    'returned under other_domain_predictions (never silently dropped).',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'leaf',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    domain: {
      type: 'string',
      description:
        'Question domain (e.g. wealth, career, spirituality, residence). Predictions whose ' +
        'event_class resolves into this domain (wealth clusters {wealth, residence}) lead the ' +
        'response; all other open predictions are still returned under other_domain_predictions.',
    },
    status: {
      type: 'string',
      description: "Lifecycle filter (open | matched | confirmed | falsified | withdrawn). Default: open.",
    },
    limit: {
      type: 'number',
      description: 'Max predictions to scan (default 100).',
    },
  },

  density_contract: {
    paginated: false,
    facets: ['domain', 'status'],
    empty_reason: true,
  },

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 4,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const domain = args['domain'] as string | undefined
    const status = (args['status'] as string | undefined) ?? 'open'
    const limit  = Math.min(Number(args['limit'] ?? 100), 500)
    const cluster = clusterFor(domain)

    try {
      const sql = `
        SELECT p.prediction_id, p.chart_id, p.claim, p.event_class, p.claim_shape,
               p.observation_window::text AS observation_window, p.milestone_set,
               p.model, p.formula_version, p.confidence, p.falsifier,
               p.as_of, p.generator_class, p.configuration_signature,
               p.lifecycle_status, p.matched_event_id, p.matched_at, p.match_note,
               p.filed_by, p.filing_method, p.source_citation, p.created_at,
               o.domain AS ontology_domain
          FROM brahma_prospective_ledger p
          LEFT JOIN brahma_event_ontology o ON o.event_class_id = p.event_class
         WHERE p.chart_id = $1::uuid AND p.lifecycle_status = $2
         ORDER BY p.as_of DESC
         LIMIT $3
      `
      const result = await query<LedgerRowWithDomain>(sql, [chart_id, status, limit])
      const rows = result.rows

      const inCluster = (r: LedgerRowWithDomain): boolean =>
        cluster == null ? true : (r.ontology_domain != null && cluster.includes(r.ontology_domain))

      const matched = rows.filter(inCluster).map(toServed)
      const other   = cluster == null ? [] : rows.filter((r) => !inCluster(r)).map(toServed)

      // §N.6 / B.10 — never a bare silent empty. When nothing matches, say why explicitly.
      let empty_reason: string | null = null
      if (matched.length === 0) {
        if (rows.length === 0) {
          empty_reason =
            `No filed prospective predictions with lifecycle_status='${status}' exist for this ` +
            `chart in brahma_prospective_ledger. Predictions enter the ledger by EXPLICIT FILING ` +
            `only (§11) — an empty result means none has been filed, not that data was withheld.`
        } else if (cluster != null) {
          empty_reason =
            `${rows.length} open prediction(s) exist for this chart but none resolves into the ` +
            `'${domain}' domain cluster [${cluster.join(', ')}]; see other_domain_predictions ` +
            `for the full open set (nothing is dropped).`
        }
      }

      return {
        content: {
          chart_id,
          predictions: matched,
          prediction_count: matched.length,
          other_domain_predictions: other,
          other_domain_count: other.length,
          total_open_count: rows.length,
          empty_reason,
          filters: {
            domain: domain ?? null,
            domain_cluster: cluster ? Array.from(cluster) : null,
            status,
            limit,
          },
          governance: PROSPECTIVE_LEDGER_GOVERNANCE_TEXT,
          provenance: { tables: ['brahma_prospective_ledger', 'brahma_event_ontology'] },
        },
        is_error: false,
      }
    } catch {
      return {
        content: {
          error: 'Standing prospective predictions are currently unavailable.',
          chart_id,
        },
        is_error: true,
      }
    }
  },
}
