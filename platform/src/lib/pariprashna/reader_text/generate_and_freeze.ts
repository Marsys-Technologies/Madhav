/**
 * pariprashna/reader_text/generate_and_freeze.ts — lane P4-J entry point.
 *
 * Ties the whole pipeline together end to end:
 *
 *   1. GENERATE  — `entries.ts`'s hand-authored `READER_TEXT_ENTRIES` (this
 *      step is "parallelize generation freely" per §10.5; nothing here
 *      prevents authoring entries independently/concurrently — the pipeline
 *      only serializes at the freeze step below).
 *   2. RANK      — `citation_ranking.ts`'s `rankMsrSignals` over the
 *      reader-facing catalog (`catalog.ts`), so every entry's reported rank
 *      and citation_weight in the frozen artifact is the REAL derived value,
 *      not the array position in `entries.ts`.
 *   3. REVIEW    — `review.ts` runs every entry through the REAL register-leak
 *      lint, voice lint, and citation gate. An entry that fails is EXCLUDED
 *      from the frozen artifact — never silently "fixed" by weakening a gate
 *      (§9 hard-never) and never force-included with a flag suppressed.
 *   4. FREEZE    — `freeze.ts` builds the artifact from passed entries only,
 *      serializes it canonically, and hashes it. This step is the "single
 *      serialized step" §10.5 requires: it is a pure function of its inputs
 *      with no concurrent writers.
 *
 * Run with:
 *   npx tsx platform/src/lib/pariprashna/reader_text/generate_and_freeze.ts
 *
 * Writes `frozen/msr_reader_text_v1.json` (the artifact) and
 * `frozen/msr_reader_text_v1.freeze.json` (the hash record) — both committed,
 * so a later drift is detectable by re-running this script and diffing, or by
 * `freeze.test.ts`'s `verifyFreeze` check against the committed pair.
 */
import 'server-only'
import { writeFileSync } from 'node:fs'
import path from 'node:path'

import { loadReaderFacingCatalog } from './catalog'
import { rankMsrSignals } from './citation_ranking'
import { READER_TEXT_ENTRIES } from './entries'
import { reviewAll } from './review'
import { buildFrozenArtifact, buildFreezeRecord, canonicalSerialize } from './freeze'
import type { MsrSignal } from './types'

const FROZEN_DIR = path.join(__dirname, 'frozen')
const ARTIFACT_PATH = path.join(FROZEN_DIR, 'msr_reader_text_v1.json')
const FREEZE_RECORD_PATH = path.join(FROZEN_DIR, 'msr_reader_text_v1.freeze.json')

export function runPipeline(): {
  totalCatalogSignals: number
  reviewedCount: number
  passedCount: number
  failed: { signal_id: string; flags: unknown[] }[]
} {
  const catalog = loadReaderFacingCatalog()
  const ranked = rankMsrSignals(catalog)
  const gradeById = new Map(READER_TEXT_ENTRIES.map((e) => [e.signal_id, e.grade]))
  const signalsById = new Map<string, MsrSignal>(catalog.map((s) => [s.signal_id, s]))

  const reviewed = reviewAll(READER_TEXT_ENTRIES, signalsById)
  const failed = reviewed.filter((r) => !r.passed)

  const artifact = buildFrozenArtifact(reviewed, ranked, gradeById, catalog.length)
  const serialized = canonicalSerialize(artifact)
  const record = buildFreezeRecord(artifact, path.relative(process.cwd(), ARTIFACT_PATH))

  writeFileSync(ARTIFACT_PATH, serialized + '\n', 'utf8')
  writeFileSync(FREEZE_RECORD_PATH, JSON.stringify(record, null, 2) + '\n', 'utf8')

  return {
    totalCatalogSignals: catalog.length,
    reviewedCount: reviewed.length,
    passedCount: reviewed.length - failed.length,
    failed: failed.map((f) => ({ signal_id: f.signal_id, flags: f.flags as unknown[] })),
  }
}

if (require.main === module) {
  const result = runPipeline()
  console.log(JSON.stringify(result, null, 2))
  if (result.failed.length > 0) {
    console.error(`${result.failed.length} entr${result.failed.length === 1 ? 'y' : 'ies'} failed review — see above.`)
    process.exitCode = 1
  }
}
