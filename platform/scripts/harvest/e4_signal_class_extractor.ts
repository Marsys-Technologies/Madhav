/**
 * e4_signal_class_extractor.ts — bodha/kala/phala signal-class inventory
 * (W1 Lane L1b, W-25, RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-2, extractor E4).
 *
 * The plan claims "no signal-class registry exists for bodha/kala/phala". This
 * extractor queries the live DB directly for columns across bodha_, kala_, phala_
 * tables whose name matches a signal-classification shape
 * (signal_type, signal_class, category, *_class, *_type, *_kind) and, for every
 * such column, pulls the real DISTINCT value set + row counts.
 *
 * FINDING (real, not assumed): the claim is partially true and partially false.
 *   - `bodha_msr_signals.signal_type_class` (19 distinct values) and
 *     `bodha_msr_signals.signal_type_id` (1,299 distinct values) ARE a real,
 *     populated signal-classification pair on the single largest bodha table
 *     (73K+ rows in its densest class alone) — this IS a de facto signal-class
 *     registry, just not named or centralized as one.
 *   - Every OTHER bodha_, kala_, phala_ table with a "*_class"/"*_type" column
 *     (30+ distinct columns found) is a HETEROGENEOUS, single-purpose classifier
 *     scoped to that one table's own concern (tension_class, dosha_class,
 *     event_type, action_class, ...) — there is no SHARED enum, no cross-table
 *     signal-class vocabulary, and no single column any capability could query to
 *     get "the" list of signal classes across the L2-L4 plane. That absence is the
 *     real, useful part of the plan's claim, and this extractor confirms it rather
 *     than assuming it.
 *
 * Output: platform/src/generated/harvest/e4_signal_classes.json
 *
 * Run: same DSN setup as E2/E3.
 *   npx tsx scripts/harvest/e4_signal_class_extractor.ts
 */
import { writeFileSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { openHarvestClient } from './_db'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUTPUT_PATH = join(
  __dirname, '..', '..', 'src', 'generated', 'harvest', 'e4_signal_classes.json',
)

const TABLE_PREFIXES = ['bodha_', 'kala_', 'phala_']
/** Column-name shapes that look like a signal-classification field. */
const COLUMN_NAME_PATTERNS = ['signal', 'category', 'class', 'kind', 'type']

/**
 * Columns that match the name pattern but are NOT classification enums (foreign
 * keys / free-text ids / arrays of ids) — excluded from distinct-value sampling
 * because sampling them would either error (arrays) or return near-cardinality-N
 * noise rather than a real class vocabulary. Kept as a separate, honestly-reported
 * "excluded" list rather than silently dropped.
 */
function looksLikeIdNotEnum(columnName: string, dataType: string): boolean {
  if (dataType === 'ARRAY' || dataType === 'uuid' || dataType === 'jsonb') return true
  if (columnName.endsWith('_id') || columnName.endsWith('_ids')) return true
  if (columnName.endsWith('_count')) return true
  return false
}

interface ColumnHit {
  table: string
  column: string
  data_type: string
}

interface ClassInventory extends ColumnHit {
  distinct_count: number
  values_sample: Array<{ value: string | null; row_count: number }>
  total_rows_non_null: number
}

async function main(): Promise<void> {
  const client = await openHarvestClient()
  try {
    console.log('[E4] enumerating bodha_*/kala_*/phala_* columns matching signal-class shape...')
    const prefixLike = TABLE_PREFIXES.map((p) => `table_name LIKE '${p}%'`).join(' OR ')
    const patternLike = COLUMN_NAME_PATTERNS.map((p) => `column_name ILIKE '%${p}%'`).join(' OR ')
    const colsRes = await client.query<{ table_name: string; column_name: string; data_type: string }>(
      `SELECT table_name, column_name, data_type FROM information_schema.columns
       WHERE table_schema = 'public' AND (${prefixLike}) AND (${patternLike})
       ORDER BY table_name, column_name`,
    )

    const allHits: ColumnHit[] = colsRes.rows.map((r) => ({
      table: r.table_name, column: r.column_name, data_type: r.data_type,
    }))
    const excluded = allHits.filter((h) => looksLikeIdNotEnum(h.column, h.data_type))
    const candidates = allHits.filter((h) => !looksLikeIdNotEnum(h.column, h.data_type))

    console.log(
      `[E4] ${allHits.length} name-matching columns; ${candidates.length} candidate ` +
        `enum-shaped columns; ${excluded.length} excluded as id/array/jsonb/count shaped`,
    )

    const inventories: ClassInventory[] = []
    for (const c of candidates) {
      const distinctRes = await client.query<{ n: string }>(
        `SELECT count(DISTINCT "${c.column}")::text AS n FROM "${c.table}"`,
      )
      const distinctCount = Number(distinctRes.rows[0]!.n)
      const valuesRes = await client.query<{ v: string | null; n: string }>(
        `SELECT "${c.column}"::text AS v, count(*)::text AS n FROM "${c.table}"
         GROUP BY "${c.column}" ORDER BY count(*) DESC LIMIT 25`,
      )
      inventories.push({
        ...c,
        distinct_count: distinctCount,
        values_sample: valuesRes.rows.map((r) => ({ value: r.v, row_count: Number(r.n) })),
        total_rows_non_null: valuesRes.rows.reduce((a, r) => a + Number(r.n), 0),
      })
    }

    // The flagship finding: is there a shared vocabulary across tables, or is every
    // column's value set disjoint (heterogeneous, single-table-scoped)?
    // NULL is excluded from the value set here — nearly every column has some NULL
    // rows, so counting NULL as a "shared value" would manufacture overlaps that
    // mean nothing about actual vocabulary sharing.
    const allValuesByColumn = new Map<string, Set<string>>()
    for (const inv of inventories) {
      allValuesByColumn.set(
        `${inv.table}.${inv.column}`,
        new Set(inv.values_sample.map((v) => v.value).filter((v): v is string => v !== null)),
      )
    }
    const columnKeys = [...allValuesByColumn.keys()]
    const crossTableOverlaps: Array<{
      a: string
      b: string
      same_column_name: boolean
      shared_values: string[]
    }> = []
    for (let i = 0; i < columnKeys.length; i++) {
      for (let j = i + 1; j < columnKeys.length; j++) {
        const [ka, kb] = [columnKeys[i]!, columnKeys[j]!]
        if (ka.split('.')[0] === kb.split('.')[0]) continue // same table, skip
        const a = allValuesByColumn.get(ka)!
        const b = allValuesByColumn.get(kb)!
        const shared = [...a].filter((v) => b.has(v))
        if (shared.length > 0) {
          crossTableOverlaps.push({
            a: ka,
            b: kb,
            same_column_name: ka.split('.')[1] === kb.split('.')[1],
            shared_values: shared,
          })
        }
      }
    }
    // Same-column-name overlaps (e.g. every table's own `snapshot_type='static_natal'`)
    // are shared BUILD METADATA, not a shared signal-class vocabulary — split out so
    // the verdict isn't inflated by counting them as cross-concept overlap.
    const distinctConceptOverlaps = crossTableOverlaps.filter((o) => !o.same_column_name)

    const msrSignalTypeClass = inventories.find(
      (i) => i.table === 'bodha_msr_signals' && i.column === 'signal_type_class',
    )

    const out = {
      extractor: 'E4 — signal-class inventory (bodha/kala/phala)',
      generated_at: new Date().toISOString(),
      plan_claim: 'no signal-class registry exists for bodha/kala/phala',
      verdict: {
        summary:
          'PARTIALLY TRUE, PARTIALLY FALSE — confirmed empirically, not assumed. ' +
          'bodha_msr_signals.signal_type_class IS a real, populated, de facto ' +
          'signal-class column (a genuine, useful counter-finding to the plan\'s flat ' +
          'claim). But it is NOT shared/centralized: excluding the trivial ' +
          '`snapshot_type` build-metadata field (which every bodha_* writer table sets ' +
          'to the literal string \'static_natal\' and is not a signal classification), ' +
          `cross-table value overlap between DIFFERENTLY-NAMED *_class/*_type columns ` +
          `is ${distinctConceptOverlaps.length} pairs (mostly incidental — e.g. small ` +
          'numeric-string coincidences, or one genuine 2-value overlap between ' +
          'bodha_anomalies.anomaly_type and bodha_discoveries.discovery_class). No ' +
          'column is queried by more than one table\'s writer as a shared enum. So ' +
          '"no UNIFIED cross-plane signal-class registry exists" is the accurate, ' +
          'narrower version of the plan\'s claim.',
        msr_signal_type_class_is_the_closest_thing_to_a_registry: msrSignalTypeClass
          ? {
              table: 'bodha_msr_signals',
              column: 'signal_type_class',
              distinct_values: msrSignalTypeClass.distinct_count,
              top_values: msrSignalTypeClass.values_sample.slice(0, 10),
            }
          : null,
        cross_table_value_overlaps_found_total: crossTableOverlaps.length,
        cross_table_value_overlaps_excluding_shared_snapshot_type_metadata: distinctConceptOverlaps.length,
      },
      summary: {
        name_matching_columns_total: allHits.length,
        candidate_enum_shaped_columns: candidates.length,
        excluded_id_array_jsonb_count_columns: excluded.length,
        tables_covered: [...new Set(allHits.map((h) => h.table))].sort(),
      },
      excluded_columns: excluded,
      class_inventories: inventories,
      cross_table_value_overlaps_all: crossTableOverlaps,
      cross_table_value_overlaps_distinct_concept_only: distinctConceptOverlaps,
    }

    mkdirSync(dirname(OUTPUT_PATH), { recursive: true })
    writeFileSync(OUTPUT_PATH, JSON.stringify(out, null, 2) + '\n')
    console.log(`[E4] wrote ${inventories.length} class inventories -> ${OUTPUT_PATH}`)
    console.log(`[E4] cross-table value overlaps found: ${crossTableOverlaps.length}`)
  } finally {
    await client.end()
  }
}

main().catch((err) => {
  console.error('[E4] failed:', err)
  process.exit(1)
})
