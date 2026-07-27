/**
 * get_yoga_firings — L1 Gaṇita Nābhasa yoga-firing detail serving surface
 * =========================================================================
 * WP-1.3(a) / F-L10-003 (LCA-19). Serves ga_yoga_firings — the rich Nābhasa
 * firing asset (per-yoga strength scoring, bhanga/cancellation, partial-formation
 * %, family tagging, dāśā-activation windows) that was computed (~50-56 rows/chart)
 * but had NO deployed serving path. This is DISTINCT from get_yoga_dosha, which
 * reads yoga rows out of chart_facts; this tool exposes the dedicated firing table
 * with its bhanga + activation detail. Read-only, bounded.
 *
 * §N.5 note: each row's constituent_fact_ids resolve back to chart_facts.fact_id;
 * this tool serves the stored firing rows verbatim — it does not re-derive them.
 *
 * MC-016 (ŚODHANA T8): the top-level `constituent_planets` field is ONE FLAT array
 * mixing structurally distinct planet roles (e.g. for neecha_bhanga_raja_yoga, the
 * DEBILITATED grahas and the RESCUER grahas that cancel the debility) — the split
 * is already present per-planet inside `grounds_jsonb` (each entry's `planet` +
 * `debilitation_sign` vs its fired grounds' `detail.supporting_planets`), but a
 * fast reader (LLM or human) sees the flat array first and can miscast a rescuer
 * as a debilitated subject (confirmed twice independently — e.g. Mars in Libra,
 * which is neutral, mis-read as "debilitated" because it sat in the flat array
 * alongside Venus/Saturn, which ARE debilitated in this firing). `deriveRoleSplit`
 * below derives labeled role fields server-side from `grounds_jsonb`:
 *   - neecha_bhanga_raja_yoga: `debilitated_planets` / `rescuer_planets`.
 *   - any other yoga family carrying the same per-planet grounds_jsonb shape:
 *     `principal_planets` (the planet each ground-block is keyed on) /
 *     `supporting_planets` (union of fired grounds' `detail.supporting_planets`).
 * `constituent_planets` is KEPT for back-compat but is now documented as
 * DEPRECATED for role-sensitive reads — see `constituent_planets_deprecated_note`
 * on each row and the tool description below.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

const CONSTITUENT_PLANETS_DEPRECATED_NOTE =
  'DEPRECATED for role-sensitive reads: constituent_planets is a flat, unordered union of ' +
  'every planet involved in this firing regardless of role (e.g. for neecha_bhanga_raja_yoga it ' +
  'mixes the debilitated grahas with the unrelated rescuer grahas). Prefer the labeled role ' +
  'fields (debilitated_planets/rescuer_planets, or principal_planets/supporting_planets) when ' +
  'present — see constituent_planets_role_split_available.'

interface GroundCheckDetail { supporting_planets?: string[] | null }
interface GroundCheck { fired?: boolean; detail?: GroundCheckDetail | null }
interface PlanetGroundBlock { planet?: string; grounds?: GroundCheck[]; debilitation_sign?: string }

/**
 * Derive a (principal, supporting) planet-role split from a firing row's
 * grounds_jsonb, generically — not hardcoded to NBRY's rule shape. Each entry in
 * grounds_jsonb is keyed on one "principal" planet (the subject of that ground
 * block — for NBRY, the debilitated planet) and carries a `grounds` array of
 * per-rule checks; a FIRED rule's `detail.supporting_planets` names the planet(s)
 * whose placement satisfies that rule (for NBRY, the rescuer). Returns null when
 * grounds_jsonb is absent/empty/malformed — callers must not assume a split
 * exists for every yoga family (most do not carry this Lane-3 data yet).
 */
function deriveRoleSplit(groundsJsonb: unknown): { principal_planets: string[]; supporting_planets: string[] } | null {
  if (!Array.isArray(groundsJsonb) || groundsJsonb.length === 0) return null
  const principals = new Set<string>()
  const supporters = new Set<string>()
  for (const entry of groundsJsonb as PlanetGroundBlock[]) {
    if (entry?.planet) principals.add(entry.planet)
    for (const g of entry?.grounds ?? []) {
      if (g?.fired && g.detail?.supporting_planets) {
        for (const sp of g.detail.supporting_planets) if (sp) supporters.add(sp)
      }
    }
  }
  if (principals.size === 0) return null
  // A planet cannot be its own rescuer/supporter — exclude self-references defensively.
  for (const p of principals) supporters.delete(p)
  return { principal_planets: [...principals], supporting_planets: [...supporters] }
}

/** Attach labeled role-split fields (MC-016) to one served firing row, in place semantics (returns a new object). */
function withRoleSplit(row: Record<string, unknown>): Record<string, unknown> {
  const split = deriveRoleSplit(row['grounds_jsonb'])
  if (!split) {
    return { ...row, constituent_planets_role_split_available: false, constituent_planets_deprecated_note: CONSTITUENT_PLANETS_DEPRECATED_NOTE }
  }
  const isNbry = row['yoga_canonical_id'] === 'neecha_bhanga_raja_yoga'
  return {
    ...row,
    ...(isNbry
      ? { debilitated_planets: split.principal_planets, rescuer_planets: split.supporting_planets }
      : { principal_planets: split.principal_planets, supporting_planets: split.supporting_planets }),
    constituent_planets_role_split_available: true,
    constituent_planets_deprecated_note: CONSTITUENT_PLANETS_DEPRECATED_NOTE,
  }
}

export const getYogaFiringsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_yoga_firings',
  type:  'tool',
  layer: 'L1',
  name:  'get_yoga_firings',

  description: [
    'Retrieve detailed Nābhasa/yoga firing rows for a chart from ga_yoga_firings.',
    'Each row: yoga_canonical_id, fired (bool), strength + strength_label,',
    'partial_formation_pct + is_partial, bhanga_active + bhanga_rule_fired (cancellation),',
    'constituent_planets/houses/fact_ids, family_ids, activation_dasha_periods, derivation.',
    'MC-016: constituent_planets is a flat, role-blind union — DEPRECATED for role-sensitive',
    'reads (constituent_planets_deprecated_note explains why). When grounds_jsonb is present,',
    'each row also carries labeled role-split fields derived server-side: for',
    'neecha_bhanga_raja_yoga specifically, debilitated_planets (the debilitated grahas) vs',
    'rescuer_planets (the grahas whose placement cancels the debility); for any other yoga',
    'family carrying the same per-planet grounds_jsonb shape, principal_planets vs',
    'supporting_planets. constituent_planets_role_split_available (bool) discloses whether the',
    'split could be derived for that row. Filters: fired (default true), ayanamsha_id, bhanga_active, is_partial,',
    'yoga_canonical_id. Weak-tail and cancelled firings are included (strength is a column,',
    'not a gate). Includes grounds_jsonb (Lane 3 CR-59 grounds-checked-per-verdict ledger) when',
    'present. Default fired=true — a catalog-only (not-fired) row is NEVER served as a finding',
    'unless all=true or fired=false is explicit (CR-72/CR-43). Bounded to 50 rows with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:          { type: 'string',  description: 'Chart UUID. Required.', required: true },
    fired:             { type: 'boolean', description: 'Filter by fired status (default: true — only fired yogas). Pass false for non-firings, omit-as-null via all=true.' },
    all:               { type: 'boolean', description: 'If true, ignore the fired filter and return fired + non-fired rows.' },
    ayanamsha_id:      { type: 'string',  description: "Filter by ayanamsha. Omit for all." },
    bhanga_active:     { type: 'boolean', description: 'Filter to firings with an active bhanga (cancellation) rule.' },
    is_partial:        { type: 'boolean', description: 'Filter to partially-formed yogas.' },
    yoga_canonical_id: { type: 'string',  description: 'Filter to a specific yoga by canonical id.' },
    limit:             { type: 'number',  description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },
  // Lane 5 (§N.6 (iv), Doctrine Campaign D-1 Night-1): newly fronted as ganita_yoga_firings_get.
  density_contract: {
    paginated: true,
    facets: ['fired', 'all', 'bhanga_active', 'is_partial', 'yoga_canonical_id'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const all               = args['all'] === true
    const fired             = args['fired'] === undefined ? true : args['fired'] === true
    const ayanamsha_id      = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const bhanga_active     = typeof args['bhanga_active'] === 'boolean' ? (args['bhanga_active'] as boolean) : null
    const is_partial        = typeof args['is_partial'] === 'boolean' ? (args['is_partial'] as boolean) : null
    const yoga_canonical_id = args['yoga_canonical_id'] ? String(args['yoga_canonical_id']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (!all)                       { filters.push(`fired = $${p++}`);             params.push(fired) }
    if (ayanamsha_id)               { filters.push(`ayanamsha_id = $${p++}`);      params.push(ayanamsha_id) }
    if (bhanga_active !== null)     { filters.push(`bhanga_active = $${p++}`);     params.push(bhanga_active) }
    if (is_partial !== null)        { filters.push(`is_partial = $${p++}`);        params.push(is_partial) }
    if (yoga_canonical_id)          { filters.push(`yoga_canonical_id = $${p++}`); params.push(yoga_canonical_id) }
    const where = filters.join(' AND ')

    // Lane 5 (§N.6): grounds_jsonb (Lane 3's CR-59 grounds-checked-per-verdict ledger —
    // fired-and-not-fired reasoning) is included whenever present. Selected defensively:
    // if the column hasn't been migrated in yet in a given environment, fall back to the
    // pre-Lane-3 column set rather than hard-failing the whole tool.
    const baseCols = `id, yoga_canonical_id, ayanamsha_id, fired, strength, strength_label,
             partial_formation_pct, is_partial, bhanga_active, bhanga_rule_fired, bhanga_na_reason,
             constituent_planets, constituent_houses, constituent_fact_ids, family_ids,
             activation_dasha_periods, derivation, citation_ref, citation_human`

    async function runQueries(cols: string) {
      const sql = `
        SELECT ${cols}
        FROM ga_yoga_firings
        WHERE ${where}
        ORDER BY strength DESC NULLS LAST, yoga_canonical_id
        LIMIT $${p}`
      return Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM ga_yoga_firings WHERE ${where}`, params),
      ])
    }

    try {
      let groundsIncluded = true
      let rowsRes: Awaited<ReturnType<typeof query>>
      let countRes: Awaited<ReturnType<typeof query<{ total: string }>>>
      try {
        [rowsRes, countRes] = await runQueries(`${baseCols}, grounds_jsonb`)
      } catch (e) {
        // grounds_jsonb not migrated yet in this environment — fall back, never hard-fail
        // the whole tool over one additive column (Lane 3's migration may be unmerged here).
        if (/column .*grounds_jsonb.* does not exist/i.test(e instanceof Error ? e.message : String(e))) {
          groundsIncluded = false
          ;[rowsRes, countRes] = await runQueries(baseCols)
        } else {
          throw e
        }
      }
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      // MC-016: attach labeled role-split fields (debilitated_planets/rescuer_planets for
      // neecha_bhanga_raja_yoga; principal_planets/supporting_planets generically) derived
      // from grounds_jsonb, alongside the retained (now-deprecated-for-role-reads) flat
      // constituent_planets array. No-op when grounds_jsonb isn't in this environment/row.
      const rows = groundsIncluded
        ? (rowsRes.rows as Array<Record<string, unknown>>).map(withRoleSplit)
        : rowsRes.rows
      return {
        content: {
          chart_id,
          rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { fired: all ? null : fired, all, ayanamsha_id, bhanga_active, is_partial, yoga_canonical_id, limit },
          ...(total_matching === 0
            ? { empty_reason: `No ga_yoga_firings rows for chart ${chart_id} matching fired=${all ? 'any' : fired}${yoga_canonical_id ? ` yoga_canonical_id='${yoga_canonical_id}'` : ''}. Pass all=true to see catalog rows that have not fired.` }
            : {}),
          provenance: {
            tables: ['ga_yoga_firings'],
            note: 'constituent_fact_ids resolve back to chart_facts.fact_id (§N.5). Default fired=true — ' +
              'a non-fired catalog row is never served as a finding unless all=true or fired=false is explicit (CR-72/CR-43).',
            source: 'L1 Gaṇita yoga-firing detail; served chart-scoped.',
            grounds_jsonb_available: groundsIncluded,
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
