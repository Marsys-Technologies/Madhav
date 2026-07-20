/**
 * load_harvest_to_ledger.ts — the harvest-pipeline → concept_ledger write step
 * (W1 Lane L1b, W-25, RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-2). This is the final
 * step the E1-E4 extractors + cross-diff were building toward: turning the
 * generated harvest JSON into real `concept_ledger` rows via the L1a-built
 * `ledger.ts` access layer (`upsertConcepts`).
 *
 * SCOPE / HONESTY NOTE (read before running against the live DB):
 * This script is WRITTEN and LIVE-TESTED against a disposable local Postgres 15
 * cluster (same pattern L1a used for migration 461 itself) — see
 * `00_ARCHITECTURE/briefs/retrieval_impl/STATE.md` W1 Lane L1b entry for the exact
 * commands. It has NOT been run against the live `amjis` database, for two
 * independent reasons, either of which alone would block it:
 *   1. This lane's only live-DB credential is `retrieval_census_ro`
 *      (SELECT-only, W0.5/W-18) — an INSERT against the live DB fails by design
 *      (`permission denied for table concept_ledger`), confirmed for `chart_facts`
 *      in W0.5 and true by the identical grant for any future table.
 *   2. Migration 461 (which CREATEs `concept_ledger`) has NOT been applied to the
 *      live DB as of this lane closing — confirmed via a live
 *      `information_schema.tables` query returning zero `concept_%` tables
 *      (see e2_db_truth_extractor.ts's own output). The table does not exist
 *      live yet; there is nothing to write to.
 * Applying migration 461 to the live DB and running this loader with a writer
 * credential is the conductor's call, same as L1a's migration itself.
 *
 * What THIS script populates (per concept_kind — see honesty notes inline for
 * what it deliberately does NOT populate):
 *   - fact_category  (source: E3 live DB categories; DARK if absent from the TS
 *     registry's coverage_matrix.ts enum, SERVED if present — see rationale below)
 *   - signal_class    (source: E4 bodha_msr_signals.signal_type_class values —
 *     the one confirmed real, populated signal-classification column found)
 *   - service_endpoint (source: E1 live getCatalog() capability URIs — every
 *     capability is, by definition, SERVED)
 *
 * Run against the disposable local DB (proves the write path end-to-end):
 *   DATABASE_URL=postgresql://postgres@127.0.0.1:5599/amjis_harvest_test \
 *     npx tsx --conditions=react-server scripts/harvest/load_harvest_to_ledger.ts
 */
import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  upsertConcepts,
  countConcepts,
  getLifecycleLayerCounts,
  type ConceptLedgerWriteInput,
} from '@/lib/retrieval/concept_ledger/ledger'

const __dirname = dirname(fileURLToPath(import.meta.url))
const GENERATED_DIR = join(__dirname, '..', '..', 'src', 'generated', 'harvest')

interface E1Doc { concepts: Array<{ uri: string; layer: string }> }
interface E3Doc {
  category_lists: {
    coverage_matrix_ts: string[]
    live_db_row_counts: Record<string, number>
  }
}
interface E4Doc {
  class_inventories: Array<{ table: string; column: string; values_sample: Array<{ value: string | null; row_count: number }> }>
}

function loadJson<T>(name: string): T {
  return JSON.parse(readFileSync(join(GENERATED_DIR, name), 'utf8')) as T
}

function buildFactCategoryConcepts(e3: E3Doc): ConceptLedgerWriteInput[] {
  const declared = new Set(e3.category_lists.coverage_matrix_ts)
  const out: ConceptLedgerWriteInput[] = []
  for (const [category, rowCount] of Object.entries(e3.category_lists.live_db_row_counts)) {
    const inRegistry = declared.has(category)
    out.push({
      concept_id: `fact_category::${category}`,
      concept_kind: 'fact_category',
      source_layer: 'L1',
      lifecycle_state: inRegistry ? 'SERVED' : 'DARK',
      disposition_rationale: inRegistry
        ? `Present in coverage_matrix.ts CHART_FACTS_CATEGORIES (queryable via ` +
          `chart_facts_query's category filter); ${rowCount} live row(s) on the ` +
          'canonical native chart.'
        : `Present live in chart_facts (${rowCount} row(s)) but ABSENT from ` +
          'coverage_matrix.ts CHART_FACTS_CATEGORIES — category-filtered retrieval ' +
          'cannot reach it by name (E3/FCAT-002 adjudication finding).',
      serving_capability_uri: inRegistry ? 'marsys://tool/L1/chart_facts_query' : null,
    })
  }
  return out
}

function buildSignalClassConcepts(e4: E4Doc): ConceptLedgerWriteInput[] {
  const msr = e4.class_inventories.find(
    (i) => i.table === 'bodha_msr_signals' && i.column === 'signal_type_class',
  )
  if (!msr) return []
  return msr.values_sample
    .filter((v) => v.value !== null)
    .map((v) => ({
      concept_id: `signal_class::bodha_msr_signals.signal_type_class::${v.value}`,
      concept_kind: 'signal_class' as const,
      source_layer: 'L2' as const,
      lifecycle_state: 'SERVED' as const,
      disposition_rationale:
        `Real, populated signal_type_class value on bodha_msr_signals (${v.row_count} ` +
        'row(s) on the canonical native chart); reachable via query_signals ' +
        '(marsys://tool/L2/query_signals family) — the closest thing this plane has ' +
        'to a signal-class registry (E4 finding).',
      serving_capability_uri: 'marsys://tool/L2/query_signals',
    }))
}

function buildServiceEndpointConcepts(e1: E1Doc): ConceptLedgerWriteInput[] {
  return e1.concepts.map((c) => ({
    concept_id: `service_endpoint::${c.uri}`,
    concept_kind: 'service_endpoint' as const,
    source_layer: c.layer as ConceptLedgerWriteInput['source_layer'],
    lifecycle_state: 'SERVED' as const,
    disposition_rationale: 'Live in getCatalog() as of this harvest run (E1).',
    serving_capability_uri: c.uri,
  }))
}

async function main(): Promise<void> {
  const e1 = loadJson<E1Doc>('e1_declared.json')
  const e3 = loadJson<E3Doc>('e3_fact_category_reconciliation.json')
  const e4 = loadJson<E4Doc>('e4_signal_classes.json')

  const factCategoryConcepts = buildFactCategoryConcepts(e3)
  const signalClassConcepts = buildSignalClassConcepts(e4)
  const serviceEndpointConcepts = buildServiceEndpointConcepts(e1)

  const all = [...factCategoryConcepts, ...signalClassConcepts, ...serviceEndpointConcepts]
  console.log(
    `[load] built ${all.length} concept rows: ${factCategoryConcepts.length} fact_category, ` +
      `${signalClassConcepts.length} signal_class, ${serviceEndpointConcepts.length} service_endpoint`,
  )

  const before = await countConcepts()
  const written = await upsertConcepts(all)
  const after = await countConcepts()
  const byLayerLifecycle = await getLifecycleLayerCounts()

  console.log(`[load] concept_ledger count before=${before} written=${written} after=${after}`)
  console.log('[load] lifecycle x layer breakdown:', byLayerLifecycle)
}

main().catch((err) => {
  console.error('[load] failed:', err)
  process.exit(1)
})
