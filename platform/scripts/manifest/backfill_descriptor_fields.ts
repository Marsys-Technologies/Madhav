/**
 * backfill_descriptor_fields.ts — R-1.1 descriptor migration report
 * ================================================================================
 * Retrieval Plane Elevation W2 "One Catalog", plan R-1 item 1: bulk-populate the
 * nine W1-landed optional `CapabilityDescriptor` fields (display, annotations,
 * register, mutation, projection_tags, family_overrides, data_source,
 * demand_ranking, calibration_context_only) across the live ~118-capability
 * registry.
 *
 * THE ACTUAL APPLICATION happens in `descriptor_defaults.ts`'s
 * `applyDescriptorDefaults()`, wired into `catalog.ts`'s `getCatalog()` — the
 * one production consumption surface both the MCP and chat channels import.
 * Every call to `getCatalog()` (in production, in this script, in any test)
 * mutates the live registered descriptor objects in place, filling any of the
 * nine fields that are still `undefined` with a generator-derived default. See
 * `descriptor_defaults.ts`'s module doc comment for the full rationale — there
 * is no single static manifest of ~118 objects to rewrite instead; the
 * descriptors are inline object literals constructed across ~20
 * `registry/layers/**` files at module-import time.
 *
 * This script's job is narrower and honest about it: load the real, live
 * registry (which — by the time `getCatalog()` returns — has already had the
 * backfill applied), then report exactly what got set, per field, with the
 * classification tables' reasoning attached, so the counts in the wave log are
 * not hand-typed guesses.
 *
 * Usage: npx tsx --conditions=react-server scripts/manifest/backfill_descriptor_fields.ts
 *   (the --conditions=react-server flag is required because the registry
 *   import chain pulls in `lib/db/client.ts`, which is gated by the
 *   `server-only` package — same flag the existing tap: and sla: scripts use.)
 */
import { getCatalog } from '../../src/lib/retrieval/registry/catalog'
import { __backfillClassificationTables as CLASSIFICATION } from '../../src/lib/retrieval/registry/descriptor_defaults'
import type { CapabilityDescriptor } from '../../src/lib/retrieval/registry/types'

function isUniversal(cap: CapabilityDescriptor): boolean {
  return cap.annotations !== undefined && cap.mutation !== undefined && cap.data_source !== undefined
}

function main() {
  const caps = getCatalog() // getCatalog() itself runs applyDescriptorDefaults() on every entry

  const total = caps.length

  const counts = {
    annotations: caps.filter((c) => c.annotations !== undefined).length,
    mutation: caps.filter((c) => c.mutation !== undefined).length,
    data_source: caps.filter((c) => c.data_source !== undefined).length,
    projection_tags: caps.filter((c) => c.projection_tags !== undefined).length,
    display: caps.filter((c) => c.display !== undefined).length,
    calibration_context_only: caps.filter((c) => c.calibration_context_only !== undefined).length,
    demand_ranking: caps.filter((c) => c.demand_ranking !== undefined).length,
    register: caps.filter((c) => c.register !== undefined).length,
    family_overrides: caps.filter((c) => c.family_overrides !== undefined).length,
  }

  const dataSourceBreakdown = {
    stored: caps.filter((c) => c.data_source === 'stored').length,
    computed: caps.filter((c) => c.data_source === 'computed').length,
    hybrid: caps.filter((c) => c.data_source === 'hybrid').length,
  }

  const mutationTrueUris = caps.filter((c) => c.mutation === true).map((c) => c.uri)
  const computedUris = caps.filter((c) => c.data_source === 'computed').map((c) => c.uri).sort()
  const hybridUris = caps.filter((c) => c.data_source === 'hybrid').map((c) => c.uri).sort()
  const calibrationContextOnlyUris = caps
    .filter((c) => c.calibration_context_only === true)
    .map((c) => c.uri)
    .sort()
  const bearingFirstUris = caps
    .filter((c) => c.demand_ranking?.bearing_first === true)
    .map((c) => c.uri)
    .sort()
  const noProjectionTagsUris = caps.filter((c) => c.projection_tags === undefined).map((c) => c.uri).sort()

  const universalCount = caps.filter(isUniversal).length

  console.log('='.repeat(78))
  console.log('R-1.1 DESCRIPTOR MIGRATION — BACKFILL REPORT')
  console.log('='.repeat(78))
  console.log(`Live capability count (getCatalog()): ${total}`)
  console.log()
  console.log('Per-field population count (of the live total):')
  for (const [field, count] of Object.entries(counts)) {
    const pct = ((count / total) * 100).toFixed(1)
    console.log(`  ${field.padEnd(28)} ${String(count).padStart(4)} / ${total}  (${pct}%)`)
  }
  console.log()
  console.log(`Universal fields (annotations + mutation + data_source, all 3 set): ${universalCount} / ${total}`)
  console.log()
  console.log('data_source breakdown:')
  console.log(`  stored:   ${dataSourceBreakdown.stored}`)
  console.log(`  computed: ${dataSourceBreakdown.computed}  →  ${computedUris.join(', ')}`)
  console.log(`  hybrid:   ${dataSourceBreakdown.hybrid}  →  ${hybridUris.join(', ')}`)
  console.log()
  console.log(`mutation: true count: ${mutationTrueUris.length}  →  ${mutationTrueUris.join(', ') || '(none)'}`)
  console.log()
  console.log(
    `calibration_context_only: true count: ${calibrationContextOnlyUris.length}  →  ` +
      `${calibrationContextOnlyUris.join(', ') || '(none)'}`
  )
  console.log(`demand_ranking.bearing_first: true count: ${bearingFirstUris.length}  →  ${bearingFirstUris.join(', ')}`)
  console.log()
  console.log(
    `projection_tags left unset (deliberate — internal-only introspection tools): ` +
      `${noProjectionTagsUris.length}  →  ${noProjectionTagsUris.join(', ') || '(none)'}`
  )
  console.log()
  console.log('NOT populated this pass (genuine editorial work, not mechanical — see descriptor_defaults.ts):')
  console.log(`  register.glossary:  ${counts.register} / ${total}`)
  console.log(`  family_overrides:   ${counts.family_overrides} / ${total}`)
  console.log()
  console.log('Classification table sizes (evidence-derived, see descriptor_defaults.ts for file:line citations):')
  console.log(`  SIDECAR_BACKED_URIS:          ${CLASSIFICATION.SIDECAR_BACKED_URIS.size}`)
  console.log(`  HYBRID_URIS:                  ${CLASSIFICATION.HYBRID_URIS.size}`)
  console.log(`  INTERNAL_INTROSPECTION_URIS:  ${CLASSIFICATION.INTERNAL_INTROSPECTION_URIS.size}`)
  console.log(`  MUTATION_URIS:                ${CLASSIFICATION.MUTATION_URIS.size}`)
  console.log(`  CALIBRATION_CONTEXT_ONLY_URIS:${CLASSIFICATION.CALIBRATION_CONTEXT_ONLY_URIS.size}`)
  console.log(`  BEARING_FIRST_URIS:           ${CLASSIFICATION.BEARING_FIRST_URIS.size}`)
  console.log('='.repeat(78))

  if (universalCount !== total) {
    console.error(
      `[backfill] FAIL: ${total - universalCount} capabilities are missing a universal field ` +
        `after the backfill pass. This should be impossible — investigate.`
    )
    process.exitCode = 1
  }
}

main()
