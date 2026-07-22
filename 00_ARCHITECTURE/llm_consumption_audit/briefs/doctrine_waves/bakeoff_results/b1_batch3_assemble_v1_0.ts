#!/usr/bin/env -S npx tsx
/**
 * b1_batch3_assemble_v1_0.ts — one-shot assembly step for BATCH 3/3.
 *
 * Reads the scratch raw-results file b1_batch3_driver_v1_0.ts produced,
 * computes per-model summaries mirroring batch_batch1.json/batch_batch2.json's
 * own schema, and writes the final checkpointed batch artifact via the merged
 * writeBatchArtifact()/hashManifestFile() (b1_batch_artifact_io.ts, commit
 * fc6ead96, imported not reimplemented). This is a thin summarize-and-write
 * step, not a second scoring run — no model.curve(), no sidecar call, no CRPS
 * computation happens here; those all already happened in the driver and are
 * read back verbatim from b1_batch3_results_raw.json.
 *
 * Usage: npx tsx b1_batch3_assemble_v1_0.ts <ISO-timestamp-from-date--u>
 */
import { readFileSync } from 'node:fs'
import { hashManifestFile, writeBatchArtifact } from '../../../../../platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/b1_batch_artifact_io'

const SCRATCH = '/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/cb8619fb-b398-41cc-a7e7-6cc6c9eafb53/scratchpad'
const MANIFEST_PATH = `${__dirname}/B1_RUN_MANIFEST_v1_0.json`
const ARTIFACTS_DIR = `${__dirname}/b1_batches`
const WRITTEN_AT = process.argv[2]
if (!WRITTEN_AT) throw new Error('usage: b1_batch3_assemble_v1_0.ts <ISO-timestamp-from-date--u>')

type PerModelEventResult = {
  eventId: string
  category: string
  resolvedEventClass: string | null
  skipped?: string
  meanCrpsReal?: number
  meanCrpsControlShuffled?: number
  skillVsShuffled?: number | null
  hitRate?: { real: boolean; percentile: number }
  dr17?: { grade: string; weight: number }
  error?: string
}

const raw: Record<string, PerModelEventResult[]> = JSON.parse(readFileSync(`${SCRATCH}/b1_batch3_results_raw.json`, 'utf8'))
const ensembleExclusions: { modelId: string; reason: string }[] = JSON.parse(readFileSync(`${SCRATCH}/b1_batch3_ensemble_exclusions.json`, 'utf8'))
const CONTENDERS = ['guru_shani_double_transit', 'av_threshold', 'planetary_return', 'hierarchical_ensemble']

let totalNegative = 0
const summaries: Record<string, unknown> = {}
for (const modelId of CONTENDERS) {
  const rows = raw[modelId]
  const scored = rows.filter((r) => r.meanCrpsReal !== undefined)
  const skipped = rows.filter((r) => r.skipped)
  const errored = rows.filter((r) => r.error)
  const negCount = scored.filter((r) => (r.meanCrpsReal as number) < 0).length
  totalNegative += negCount
  const gradeCounts: Record<string, number> = {}
  let weightedTotal = 0
  for (const r of scored) {
    const g = r.dr17!.grade
    gradeCounts[g] = (gradeCounts[g] ?? 0) + 1
    weightedTotal += r.dr17!.weight
  }
  const meanCrpsReal = scored.length > 0 ? scored.reduce((s, r) => s + (r.meanCrpsReal as number), 0) / scored.length : NaN
  const meanSkillVsShuffled = scored.length > 0 ? scored.reduce((s, r) => s + ((r.skillVsShuffled as number) ?? 0), 0) / scored.length : NaN
  summaries[modelId] = {
    modelId,
    eventsTotal: rows.length,
    eventsScored: scored.length,
    eventsSkippedUnresolvedEventClass: skipped.length,
    eventsErrored: errored.length,
    negativeCrpsCount: negCount,
    dr17GradeCounts: gradeCounts,
    dr17WeightedTotal: weightedTotal,
    dr17WeightedMean: scored.length > 0 ? weightedTotal / scored.length : 0,
    meanCrpsReal,
    meanSkillVsShuffled,
    errors: errored.map((r) => ({ eventId: r.eventId, error: r.error })),
  }
}

const manifestHash = hashManifestFile(MANIFEST_PATH)

const results = {
  batch: 'batch3',
  contenders: CONTENDERS,
  chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
  preregistration_packet_blob_sha: '9b6713db8c2551a937ff2070e498da1f12526966',
  events_scored_count: 54,
  events_excluded: [
    { eventId: 'EVT.1984.02.05.01', reason: 'structural_anchor_not_scored (packet §0)' },
    { eventId: 'EVT.1995.XX.XX.02', reason: 'congenital_onset_not_independently_scoreable (packet §0)' },
  ],
  grading: {
    framework: 'DR-17 (dr17_grading.ts, PR #704, imported not reimplemented)',
    weights_ruling: 'NP-D4B-001',
    tie_bands_ruling: 'NP-D4B-003 (adopted table)',
    tie_band_set_used: 'adopted',
  },
  controls: {
    design: 'DR-15(c) coverage-matched shuffled-birth',
    n: 1000,
    mirrored_via: 'harness.ts runMirroredScoringHarness (structural control-mirroring)',
  },
  negative_crps_check: {
    total_negative_crps_found: totalNegative,
    verified_zero: totalNegative === 0,
  },
  event_class_resolution_note:
    "Same 3-of-54 resolved events as batch1/batch2 (EVT.2010.XX.XX.01/EVT.2013.12.11.01/EVT.2025.07.XX.01), reusing batch1's own live-verified resolution (gochara_resonance_map career_advancement=22/major_gain=35/marriage=23 for this chart) rather than re-querying a third time this batch. All 3 batch3 PERMISSION contenders (guru_shani_double_transit/av_threshold/planetary_return, resolved live via the sidecar /api/compute/permission_curve route, confirmed reachable with a live PYTHON_SIDECAR_API_KEY pulled from Secret Manager this batch) are honestly SKIPPED for the other 51 unresolved events, matching F-1/batch1/batch2's established design. hierarchical_ensemble is necessarily scored on the SAME 3-event slice only (see J-ENSEMBLE-1 in b1_batch3_driver_v1_0.ts's module header) -- it is likewise SKIPPED (not fallback-scored) for the other 51.",
  ensemble_note:
    'hierarchical_ensemble built LAST, over all 13 non-ensemble contenders (pratyantar_lord [batch1] + all 12 PERMISSION_SYSTEM_IDS [4 batch1 + 5 batch2 + 3 batch3]) -- every one of which recorded eventsErrored=0 in its own batch artifact (batch_batch1.json/batch_batch2.json, cross-checked this batch) or in this batch\'s own Part A run, so all 13 were fed into the ensemble unfiltered. ensembleExclusions=0 this run (recorded live in b1_batch3_ensemble_exclusions.json; would have been non-empty and disclosed here had any constituent failed to bind/curve for a given event). J-ENSEMBLE-1 (b1_batch3_driver_v1_0.ts module header) discloses the one new judgment call this batch made: an eventClassSignificators key-alias extension (zero new significator weights, only two new keys pointing at batch1\'s own pre-existing DOMAIN_LORDS.wealth/DOMAIN_LORDS.marriage entries) so pratyantar_lord could be called with the SAME eventClass argument (major_gain/marriage) the ensemble hands its PERMISSION constituents, since ensemble_model.ts\'s curve() calls every constituent with one shared eventClass value.',
  disclosed_observation:
    'guru_shani_double_transit and planetary_return both grade peak/elevated on 1 of their 3 scored events (av_threshold peaks on a DIFFERENT event of the 3 -- EVT.2010.XX.XX.01 -- while guru_shani_double_transit/planetary_return peak/elevate on EVT.2025.07.XX.01), real differentiation consistent with batch2\'s own finding that this 3-event slice is NOT uniformly degenerate-flat across contenders. hierarchical_ensemble grades peak on 2 of 3 (EVT.2010.XX.XX.01, EVT.2013.12.11.01) and elevated on the third (EVT.2025.07.XX.01) -- its unweighted-sum construction means it inherits a peak whenever ANY constituent grades strongly on that event (e.g. av_threshold peaks on EVT.2010.XX.XX.01 even though guru_shani_double_transit/planetary_return grade neutral there), which is the expected behavior of an unweighted superposition per ensemble_model.ts\'s own documented design, not an anomaly. Disclosed, not investigated further -- outside this batch\'s scope (per-system weight learning is B-3\'s job, per BRIEF_D4B §1 and ensemble_model.ts\'s own header).',
  summaries,
  per_event_detail: raw,
  ensemble_exclusions: ensembleExclusions,
}

const path = writeBatchArtifact(ARTIFACTS_DIR, 'batch3', manifestHash, results, WRITTEN_AT)
console.error('[assemble] manifestHash=', manifestHash)
console.error('[assemble] wrote', path)
