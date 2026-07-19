/**
 * generate_concept_projections.ts — concept_ledger → concept_census.json
 * ================================================================================
 * Retrieval Plane Elevation, W1 Lane L1a (W-24, RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-1,
 * "Concept Spine" doctrine): "inventory truth is EXTRACTED or GENERATED, never
 * hand-authored." This is the first (v1) projection generator over the single
 * writable concept_ledger table (migration 461) — it emits a build-time JSON
 * artifact summarizing concept counts by lifecycle_state and source_layer.
 *
 * v1 SCOPE: one projection (the census JSON). Later waves add further projections
 * (docs resource, CI census-drift gate, etc. per plan §3 R-1.2). concept_ledger is
 * EMPTY until the W-25 harvest pipeline lands (a later wave) — this generator is
 * required to run cleanly against zero rows today; that is the proof the
 * ledger → projection loop works end to end before any data exists.
 *
 * Usage: npx tsx scripts/manifest/generate_concept_projections.ts
 * Requires: DATABASE_URL env var (see platform/.env.local.example).
 */
import { writeFileSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import {
  countConcepts,
  getLifecycleLayerCounts,
  type LifecycleState,
  type SourceLayer,
} from '../../src/lib/retrieval/concept_ledger/ledger'

// Repo root is two levels up from platform/scripts/manifest/
// __dirname = .../platform/scripts/manifest
const OUTPUT_PATH = join(__dirname, '..', '..', 'src', 'generated', 'concept_census.json')

const ALL_LIFECYCLE_STATES: LifecycleState[] = [
  'DISCOVERED',
  'SERVED',
  'PLANNER_KNOWN',
  'INTERNAL_BY_DESIGN',
  'RETIRED',
  'DARK',
]

const ALL_SOURCE_LAYERS: SourceLayer[] = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5']

async function main(): Promise<void> {
  console.log('[generate_concept_projections] Reading concept_ledger...')

  const total = await countConcepts()
  const layerCounts = await getLifecycleLayerCounts()

  console.log(`[generate_concept_projections] concept_ledger has ${total} row(s)`)

  // Zero-fill so every declared state/layer key is present even when the ledger
  // is empty (or a state/layer has no rows yet) — the projection is honest about
  // what it does NOT yet know, never silently omits a key (§N.6 discipline).
  const counts_by_lifecycle_state: Record<LifecycleState, number> = Object.fromEntries(
    ALL_LIFECYCLE_STATES.map((s) => [s, 0]),
  ) as Record<LifecycleState, number>
  const counts_by_source_layer: Record<SourceLayer, number> = Object.fromEntries(
    ALL_SOURCE_LAYERS.map((l) => [l, 0]),
  ) as Record<SourceLayer, number>

  for (const row of layerCounts) {
    counts_by_lifecycle_state[row.lifecycle_state] =
      (counts_by_lifecycle_state[row.lifecycle_state] ?? 0) + row.concept_count
    counts_by_source_layer[row.source_layer] =
      (counts_by_source_layer[row.source_layer] ?? 0) + row.concept_count
  }

  const census = {
    generated_at: new Date().toISOString(),
    generator: 'generate_concept_projections.ts',
    generator_version: '1.0',
    source: 'concept_ledger (migration 461)',
    total_concepts: total,
    counts_by_lifecycle_state,
    counts_by_source_layer,
    counts_by_lifecycle_and_layer: layerCounts,
    note:
      total === 0
        ? 'concept_ledger is empty — population is the W-25 harvest pipeline (later wave). This census proves the ledger→projection loop runs end to end pre-population.'
        : undefined,
  }

  mkdirSync(dirname(OUTPUT_PATH), { recursive: true })
  writeFileSync(OUTPUT_PATH, JSON.stringify(census, null, 2) + '\n', 'utf-8')

  console.log(`[generate_concept_projections] Wrote ${OUTPUT_PATH}`)
}

main().catch((err) => {
  console.error('[generate_concept_projections] FAILED:', err)
  process.exit(1)
})
