/**
 * query_muhurta_lattice — L0 Brahmagyan muhūrta boundary/factor lattice reader
 * =============================================================================
 * ṢAḌ-DARŚANA campaign item 36 (SHAD_DARSHANA_BRIEF_v2_0.md §1 row 36 · §3 W3):
 * the QUERY-TIME half of the contender lattice. The substrate — table
 * `bg_muhurta_lattice`, writer `bg_muhurta_lattice.py`, migration 484 — landed
 * with PR #930 (Night 2). This capability is the read path over it; it computes
 * NOTHING astrological of its own.
 *
 * WHAT IT SERVES: every lattice factor row whose [start_utc, end_utc) span
 * overlaps the requested interval, across four chart-independent factor families
 * (`agnivasa`, `combination_yoga`, `kalam`, `ghati_muhurta`).
 *
 * DENSITY DISCIPLINE (CLAUDE.md §N.6 part 1 — never present catalog/convention
 * rows as confirmed findings): the substrate stamps every row with
 * `corpus_status`, either `computed_cited` (the underlying panchang_engine table
 * carries a real inline classical citation) or `computed_uncited_convention` (a
 * live deterministic production convention whose source table carries NO
 * per-row classical citation — disclosed honestly by the writer rather than
 * given an invented one). Both are SERVED (B.10 forbids silently dropping
 * data), but they are COUNTED SEPARATELY here — `cited_row_count` vs
 * `convention_only_row_count`, plus a `convention_only_note` — so no caller can
 * read the raw row count as "N cited classical factors". The downstream
 * adjudication engine (platform-mcp `lib/kala_lattice_query.ts`) treats only
 * `computed_cited` rows as findings.
 *
 * REFERENCE-LOCATION HONESTY: the kālam/ghaṭī/sunrise-anchored families are
 * computed at ONE fixed IST reference location (an explicit, documented
 * substrate scope decision — see the writer's module docstring). The row's own
 * `reference_location_key` / `reference_lat` / `reference_lon` are returned as
 * DATA so a caller can never mistake these windows for querent-local ones; a
 * per-querent-location join does not exist and is not simulated here.
 *
 * Global chart-independent reference — no chart_id, by construction.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

/** The four factor families the substrate's CHECK constraint allows. */
const FACTOR_FAMILIES = ['agnivasa', 'combination_yoga', 'kalam', 'ghati_muhurta'] as const

const MAX_ROWS = 2000

function isIsoInstant(value: string): boolean {
  return !Number.isNaN(Date.parse(value))
}

export const queryMuhurtaLatticeCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_muhurta_lattice',
  type:  'tool',
  layer: 'L0',
  name:  'query_muhurta_lattice',

  description: [
    'Read the global muhūrta boundary/factor lattice (bg_muhurta_lattice) for a time interval.',
    'Four chart-independent factor families: agnivasa (Agni\'s tithi-keyed elemental residence),',
    'combination_yoga (Sarvārtha-siddhi, Amṛta-siddhi, Ravi/Guru-Puṣya, Tripuṣkara/Dvipuṣkara,',
    'Siddha, Bhadra, Pañchaka spans), kalam (rāhu-kālam, yamagaṇḍa, gulika, durmuhūrta,',
    'brāhma-muhūrta, abhijit, amṛta-kālam, varjyam and siblings) and ghati_muhurta (the 30-fold',
    'named day+night muhūrtas). Every row carries its own source_citation and a corpus_status of',
    'either computed_cited (a real inline classical citation exists for that table) or',
    'computed_uncited_convention (a live deterministic convention with no per-row classical',
    'citation in source — disclosed, not invented). The two are counted separately in the',
    'response; do not read the raw row count as a count of cited classical factors.',
    'Sunrise-anchored families are computed at one fixed IST reference location returned as data',
    'on every row — these are NOT querent-local windows. Global reference: no chart_id needed.',
  ].join(' '),

  input_schema: {
    start_utc: { type: 'string', description: 'Interval start, ISO-8601 UTC (e.g. 2026-08-05T00:00:00Z). Required.' },
    end_utc:   { type: 'string', description: 'Interval end, ISO-8601 UTC. Required. Rows overlapping [start_utc, end_utc) are returned.' },
    factor_family: { type: 'string', description: `Optional filter: one of ${FACTOR_FAMILIES.join(', ')}. Omit for all four.` },
    factor_key: { type: 'string', description: 'Optional exact factor_key filter (e.g. rahu_kalam, abhijit, bhadra).' },
    limit: { type: 'number', description: `Max rows (default ${MAX_ROWS}, hard cap ${MAX_ROWS}). Narrow the interval rather than raising this.` },
  },

  required_inputs: ['start_utc', 'end_utc'],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 20, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const startUtc = args['start_utc'] != null ? String(args['start_utc']) : ''
    const endUtc   = args['end_utc']   != null ? String(args['end_utc'])   : ''
    if (!startUtc || !endUtc || !isIsoInstant(startUtc) || !isIsoInstant(endUtc)) {
      return {
        content: { error: 'start_utc and end_utc are required and must be parseable ISO-8601 instants.' },
        is_error: true,
      }
    }
    if (Date.parse(endUtc) <= Date.parse(startUtc)) {
      return { content: { error: 'end_utc must be strictly after start_utc.' }, is_error: true }
    }

    const familyArg = args['factor_family'] != null ? String(args['factor_family']) : null
    if (familyArg && !(FACTOR_FAMILIES as readonly string[]).includes(familyArg)) {
      return {
        content: { error: `factor_family must be one of: ${FACTOR_FAMILIES.join(', ')}` },
        is_error: true,
      }
    }
    const factorKey = args['factor_key'] != null ? String(args['factor_key']) : null
    const requestedLimit = args['limit'] != null ? Number(args['limit']) : MAX_ROWS
    const limit = Number.isFinite(requestedLimit) && requestedLimit > 0
      ? Math.min(Math.floor(requestedLimit), MAX_ROWS)
      : MAX_ROWS

    // Half-open overlap: a row overlaps [start, end) iff row.start < end AND row.end > start.
    const filters: string[] = ['start_utc < $1', 'end_utc > $2']
    const params: unknown[] = [endUtc, startUtc]
    let p = 3
    if (familyArg) { filters.push(`factor_family = $${p++}`); params.push(familyArg) }
    if (factorKey) { filters.push(`factor_key = $${p++}`); params.push(factorKey) }
    params.push(limit)

    const sql = `
      SELECT factor_family, factor_key, start_utc, end_utc, detail,
             reference_lat, reference_lon, reference_tz_offset_minutes,
             reference_location_key, ayanamsha_key, sampling_method,
             source_citation, corpus_status
      FROM bg_muhurta_lattice
      WHERE ${filters.join(' AND ')}
      ORDER BY start_utc, factor_family, factor_key
      LIMIT $${p}`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows
      const citedRows = rows.filter((r) => r['corpus_status'] === 'computed_cited')
      const conventionRows = rows.filter((r) => r['corpus_status'] === 'computed_uncited_convention')

      const familyCounts: Record<string, number> = {}
      for (const r of rows) {
        const fam = String(r['factor_family'])
        familyCounts[fam] = (familyCounts[fam] ?? 0) + 1
      }

      return {
        content: {
          rows,
          count: rows.length,
          truncated: rows.length === limit,
          // §N.6 part 1: the two density layers are counted separately, never flattened.
          cited_row_count: citedRows.length,
          convention_only_row_count: conventionRows.length,
          convention_only_keys: Array.from(new Set(conventionRows.map((r) => String(r['factor_key'])))).sort(),
          convention_only_note:
            conventionRows.length > 0
              ? 'Rows with corpus_status=computed_uncited_convention are live deterministic ' +
                'conventions whose source table carries no per-row classical citation. They are ' +
                'served (never silently dropped) but are NOT cited classical findings — see ' +
                'bg_muhurta_factor_census via query_parihara_graph for the per-factor gap register.'
              : null,
          interval: { start_utc: startUtc, end_utc: endUtc },
          filters: { factor_family: familyArg, factor_key: factorKey, limit },
          family_counts: familyCounts,
          ...(rows.length === 0
            ? {
                empty_reason:
                  `No lattice rows overlap ${startUtc}..${endUtc}` +
                  (familyArg ? ` for factor_family=${familyArg}` : '') +
                  (factorKey ? ` / factor_key=${factorKey}` : '') +
                  '. The lattice carries a rolling forward horizon built by an explicit ' +
                  'super-admin L0 trigger — an interval outside that built horizon returns ' +
                  'honestly empty rather than a computed claim.',
              }
            : {}),
          disclaimer:
            'Chart-independent factor spans only — not a per-chart election verdict and not a ' +
            'querent-local window set. Sunrise-anchored families use the fixed reference ' +
            'location returned on each row.',
          provenance: { tables: ['bg_muhurta_lattice'], asset_id: 'bg_muhurta_lattice' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
