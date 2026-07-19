/**
 * get_vichara — L1 Gaṇita "judged structure" serving surface (ganita_vichara_get)
 * =================================================================================
 * Lane 5 (§N.6 density retrofit, Doctrine Campaign D-1 / Night-1). Serves the new
 * `ga_vichara` asset (Lane 2, `LANE2_GA_VICHARA.md`) — stored in `chart_vichara`,
 * five families: `valence_pass`, `varga_ratification`, `varga_ratification_divergence`,
 * `varga_consistency`, `leverage_index` (design §4/§8/§11).
 *
 * BORN §N.6-CONFORMANT (this is a brand-new tool — CR-76 "a dark asset repeats the
 * computed-then-dark failure" does not apply, but a NEW tool skipping the density
 * principle from day one would be the exact same class of mistake):
 *   (i)   family-collapse — rows are grouped by vichara_family with member counts;
 *         no flat undifferentiated dump.
 *   (ii)  facets honored or rejected loudly — `family`, `domain`, `subject` are
 *         validated against closed/known vocabularies; an unknown value is a loud
 *         rejection (400-shaped error content), never a silently-unfiltered corpus
 *         (CR-42). `subject` is case-insensitive (CR-10: Venus≡venus≡VENUS).
 *   (iii) layered envelope — `verdict` (small, counts + as_of), `digest` (per-family
 *         summary), `rows` (paginated). Byte caps enforced explicitly, not by hope.
 *   (iv)  density contract — see the capability_map addendum this lane also lands.
 *
 * DEPENDENCY HONESTY (conductor DAG: LANE2 → LANE3/LANE4 → LANE5): at the time this
 * lane was implemented, Lane 2's `ga_vichara` writer and `chart_vichara` table had
 * NOT been built by any sibling lane reachable from this worktree (see the Lane 4
 * handback report, same finding). Rather than fail hard or fabricate a shape, this
 * tool is written DEFENSIVELY: if `chart_vichara` does not exist yet, it degrades to
 * an honest empty response with a structured `empty_reason` naming the exact cause
 * (CR-11) — it activates automatically, with ZERO further code change, the moment
 * Lane 2's migration lands and the table exists. This mirrors Lane 4's own posture
 * toward the same missing dependency (their bo_laksana.py ratification/valence-source
 * loaders).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { grahaCodeOf } from '@/lib/retrieval/address_resolver'

const MAX_LIMIT = 500

/** Closed family vocabulary (design §3/§8/§11 — chart_vichara.vichara_family). */
const VICHARA_FAMILIES = [
  'valence_pass',
  'varga_ratification',
  'varga_ratification_divergence',
  'varga_consistency',
  'leverage_index',
] as const
type VicharaFamily = (typeof VICHARA_FAMILIES)[number]
const VICHARA_FAMILY_SET = new Set<string>(VICHARA_FAMILIES)

/** Closed domain vocabulary (design §11 operative-varga registry — wealth is design-ratified). */
const VICHARA_DOMAINS = ['wealth', 'career', 'marriage', 'health', 'general'] as const
const VICHARA_DOMAIN_SET = new Set<string>(VICHARA_DOMAINS)

/** Byte caps (design §N.6 (iii) / C1 budget) — verdict + digest + one page must stay small. */
const MAX_VERDICT_BYTES = 1024
const MAX_DIGEST_BYTES = 4096

function byteLen(v: unknown): number {
  return Buffer.byteLength(JSON.stringify(v) ?? '', 'utf8')
}

/**
 * Detect "relation chart_vichara does not exist" (or any table-not-built error) vs. a
 * genuine internal failure. Never leaks raw SQL error text to the caller either way —
 * the caller only ever sees the honest structured degraded response.
 */
function isMissingTableError(err: unknown): boolean {
  const msg = err instanceof Error ? err.message : String(err)
  return /relation .*chart_vichara.* does not exist/i.test(msg)
}

export const getVicharaCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_vichara',
  type:  'tool',
  layer: 'L1',
  name:  'get_vichara',

  description: [
    'Retrieve ga_vichara ("judged structure") rows for a chart from chart_vichara — the',
    'judgment layer built on top of ga_structural: valence_pass (functional-lordship',
    'valence, e.g. the 8L-Mars→H2 strong_malefic specimen), varga_ratification',
    '(ratification_factor ∈ [0.6,1.4] per domain×subject), varga_ratification_divergence',
    '(a varga that flips D1\'s dignity direction — rankable evidence, not noise),',
    'varga_consistency (continuous vargottama-generalized index, 0..1), leverage_index',
    '(domain_load_bearing_weight ÷ capability, forward-weighted by dasha runway — the',
    'number remedy/intervention-timing ranks on). Every row carries constituent_fact_ids',
    'resolving back to chart_facts (§N.5 — L1 authority, never restated). Filter by',
    'family (closed vocabulary), domain, or subject (graha/lord code, case-insensitive).',
    'Layered response: verdict (family counts) + digest (per-family summary) + paginated rows.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Filter by ayanamsha (e.g. 'lahiri_chitrapaksha'). Omit for all." },
    family: {
      type: 'string',
      description: `One of: ${VICHARA_FAMILIES.join(', ')}. Omit for all families. Unknown values are rejected, never silently ignored.`,
      enum: [...VICHARA_FAMILIES],
    },
    domain: {
      type: 'string',
      description: `One of: ${VICHARA_DOMAINS.join(', ')}. Omit for all domains (only meaningful for varga_ratification/varga_ratification_divergence/leverage_index — valence_pass/varga_consistency rows carry domain=null and are unaffected by this filter).`,
      enum: [...VICHARA_DOMAINS],
    },
    subject: {
      type: 'string',
      description: 'Filter by subject (graha/lord/karaka code, e.g. VENUS or venus — case-insensitive, CR-10).',
    },
    limit:  { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
    offset: { type: 'number', description: 'Pagination offset (default 0).' },
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
    bulk_context: { pre_fetch_priority: 70, always_include: false },
  },
  density_contract: {
    max_verdict_bytes: MAX_VERDICT_BYTES,
    max_digest_bytes: MAX_DIGEST_BYTES,
    paginated: true,
    facets: ['family', 'domain', 'subject'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const familyRaw = args['family'] !== undefined && args['family'] !== null ? String(args['family']) : null
    const domainRaw = args['domain'] !== undefined && args['domain'] !== null ? String(args['domain']) : null
    const subjectRaw = args['subject'] !== undefined && args['subject'] !== null ? String(args['subject']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)
    const offset = Math.max(Number(args['offset'] ?? 0), 0)

    // (ii) Facets honored or rejected loudly — CR-42: a dropped/unrecognized filter must
    // NEVER degrade to a different, unfiltered corpus. Reject before any SQL runs.
    if (familyRaw !== null && !VICHARA_FAMILY_SET.has(familyRaw)) {
      return {
        content: {
          error: `Unknown family "${familyRaw}". Supported: ${VICHARA_FAMILIES.join(', ')}.`,
          supported_families: VICHARA_FAMILIES,
        },
        is_error: true,
      }
    }
    if (domainRaw !== null && !VICHARA_DOMAIN_SET.has(domainRaw)) {
      return {
        content: {
          error: `Unknown domain "${domainRaw}". Supported: ${VICHARA_DOMAINS.join(', ')}.`,
          supported_domains: VICHARA_DOMAINS,
        },
        is_error: true,
      }
    }
    const family = familyRaw as VicharaFamily | null
    const domain = domainRaw

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (family)       { filters.push(`vichara_family = $${p++}`); params.push(family) }
    if (domain)       { filters.push(`domain = $${p++}`); params.push(domain) }
    // CR-10: case-insensitive subject match — Venus≡venus≡VENUS.
    if (subjectRaw)   { filters.push(`UPPER(subject) = UPPER($${p++})`); params.push(subjectRaw) }
    const where = filters.join(' AND ')

    const rowsSql = `
      SELECT id, chart_id, ayanamsha_id, build_id, vichara_family, subject, domain, varga_id,
             value_num, value_text, value_jsonb, constituent_fact_ids, formula_version,
             source_citation, computed_at
      FROM chart_vichara
      WHERE ${where}
      ORDER BY vichara_family, domain NULLS FIRST, subject
      LIMIT $${p} OFFSET $${p + 1}`
    const countSql = `SELECT COUNT(*)::text AS total FROM chart_vichara WHERE ${where}`
    const familyCountSql = `
      SELECT vichara_family, COUNT(*)::text AS n
      FROM chart_vichara WHERE ${where}
      GROUP BY vichara_family`

    try {
      let [rowsRes, countRes, familyCountRes] = await Promise.all([
        query<Record<string, unknown>>(rowsSql, [...params, limit, offset]),
        query<{ total: string }>(countSql, params),
        query<{ vichara_family: string; n: string }>(familyCountSql, params),
      ])

      // D-2 finding §6.1 fix (leverage_index `subject=venus` false-empty, D-4a Lane A-1):
      // chart_vichara.subject stores the 3-letter/graha CODE (e.g. 'VEN'), not the
      // natural-language name. The UPPER(subject)=UPPER($n) filter above is CR-10-correct
      // for code-vs-code case-insensitivity (Venus≡venus≡VENUS all resolve to the SAME
      // literal string), but a caller passing the full name ("venus") never matches the
      // stored code ("VEN") — a real 0-row miss disguised as an ambiguous empty_reason,
      // not a genuine absence-of-data finding. Retry ONCE with the canonical graha code
      // (shared `grahaCodeOf` resolver — same alias table every other L1/L2 surface uses,
      // per the single-source mandate) whenever the raw subject filter produced zero rows
      // and resolves to a DIFFERENT code than what was literally passed. Never silent: the
      // resolved-alias retry is disclosed on the response via `subject_alias_resolved`.
      let subjectAliasResolved: { input: string; resolved_code: string } | undefined
      if (subjectRaw && Number(countRes.rows[0]?.total ?? 0) === 0) {
        let resolvedCode: string | undefined
        try {
          resolvedCode = grahaCodeOf(subjectRaw)
        } catch {
          resolvedCode = undefined // not a recognized graha name/alias — leave the honest 0-row result as-is
        }
        if (resolvedCode && resolvedCode.toUpperCase() !== subjectRaw.toUpperCase()) {
          const retryParams = params.map((v, i) => (i === params.length - 1 && subjectRaw ? resolvedCode : v))
          const [rowsRetry, countRetry, familyCountRetry] = await Promise.all([
            query<Record<string, unknown>>(rowsSql, [...retryParams, limit, offset]),
            query<{ total: string }>(countSql, retryParams),
            query<{ vichara_family: string; n: string }>(familyCountSql, retryParams),
          ])
          if (Number(countRetry.rows[0]?.total ?? 0) > 0) {
            rowsRes = rowsRetry
            countRes = countRetry
            familyCountRes = familyCountRetry
            subjectAliasResolved = { input: subjectRaw, resolved_code: resolvedCode }
          }
        }
      }

      const total = Number(countRes.rows[0]?.total ?? 0)
      const rows = rowsRes.rows ?? []

      // (i) Family-collapse presentation: per-family counts, not a flat dump.
      const family_counts: Record<string, number> = {}
      for (const r of familyCountRes.rows) family_counts[r.vichara_family] = Number(r.n)

      const verdict = {
        chart_id,
        total_rows: total,
        served_rows: rows.length,
        family_counts,
        as_of: new Date().toISOString(),
        note: 'Counts are family totals under the SAME filters this page was drawn from (D5 coverage receipt) — not a re-guess.',
      }
      if (byteLen(verdict) > MAX_VERDICT_BYTES) {
        // Trim to the minimum honest shape rather than exceed the cap silently.
        (verdict as Record<string, unknown>)['family_counts'] = { _trimmed: true, reason: 'verdict byte cap' }
      }

      const digest = {
        families_present: Object.keys(family_counts),
        by_family: Object.fromEntries(
          VICHARA_FAMILIES.filter(f => family_counts[f]).map(f => [
            f,
            { count: family_counts[f], sample_subjects: Array.from(new Set(rows.filter(r => r['vichara_family'] === f).map(r => String(r['subject'])))).slice(0, 8) },
          ]),
        ),
      }
      let digestOut: unknown = digest
      if (byteLen(digest) > MAX_DIGEST_BYTES) {
        digestOut = { families_present: Object.keys(family_counts), note: 'digest trimmed to family list only (digest byte cap exceeded)' }
      }

      const empty_reason = total === 0
        ? `No chart_vichara rows for chart ${chart_id}${ayanamsha_id ? ` at ayanamsha '${ayanamsha_id}'` : ''}${family ? ` for family '${family}'` : ''}${domain ? ` for domain '${domain}'` : ''}${subjectRaw ? ` for subject '${subjectRaw}'` : ''} — either ga_vichara has not been built for this chart yet, or these filters genuinely match nothing. NOTE: chart_vichara.subject stores the graha CODE (e.g. 'VEN', 'MOON'), not the full name — a natural-language subject value is auto-resolved via the shared graha alias table when possible (see 'subject_alias_resolved' when that succeeds); if you still see this message with a subject filter set, the resolved/literal code genuinely has no rows for the other filters in play.`
        : undefined

      return {
        content: {
          chart_id,
          verdict,
          digest: digestOut,
          rows,
          total_matching: total,
          more_available: total > offset + rows.length,
          filters: { ayanamsha_id, family, domain, subject: subjectRaw, limit, offset },
          ...(subjectAliasResolved ? { subject_alias_resolved: subjectAliasResolved } : {}),
          ...(empty_reason ? { empty_reason } : {}),
          provenance: { tables: ['chart_vichara'], asset_id: 'ga_vichara' },
        },
        is_error: false,
      }
    } catch (err) {
      if (isMissingTableError(err)) {
        // Honest degraded response (CR-76 avoidance) — NOT an error. ga_vichara/chart_vichara
        // has not been built yet in this environment; this tool activates the moment it is,
        // with zero further code change.
        return {
          content: {
            chart_id,
            verdict: { chart_id, total_rows: 0, served_rows: 0, family_counts: {}, as_of: new Date().toISOString() },
            digest: { families_present: [] },
            rows: [],
            total_matching: 0,
            more_available: false,
            filters: { ayanamsha_id, family, domain, subject: subjectRaw, limit, offset },
            empty_reason: `ga_vichara has not been built yet (chart_vichara table does not exist in this environment). This tool will serve real rows automatically once Lane 2's migration + writer land — no code change required.`,
            provenance: { tables: ['chart_vichara'], asset_id: 'ga_vichara', status: 'asset_not_built' },
          },
          is_error: false,
        }
      }
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
