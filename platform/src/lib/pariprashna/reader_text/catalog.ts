/**
 * pariprashna/reader_text/catalog.ts — lane P4-J.
 *
 * Loads the MSR catalog via the existing, tested `parseMsrSignals`
 * (`platform/src/scripts/etl/msr_parser.ts` — 573/573, see that module's own
 * test suite) and excludes the registry's own §16 internal "Statistics" audit
 * entries (SIG.MSR.416–420, `claim_text` starting with "Statistics — ") from
 * the reader-facing pool: those five are the catalog auditing ITSELF (signal
 * counts by section), not chart findings a reader would ever ask about, and
 * they carry `entities_involved: []` by design — including them in citation
 * ranking would silently sink them to the bottom as if they were real,
 * uncited astrological signals rather than correctly excluding them as
 * out-of-scope for this lane.
 */
import 'server-only'
import { readFileSync } from 'node:fs'
import path from 'node:path'

import { parseMsrSignals } from '../../../scripts/etl/msr_parser'
import type { MsrSignal } from './types'

const REPO_ROOT = path.resolve(__dirname, '..', '..', '..', '..', '..')
const MSR_PATH = path.join(REPO_ROOT, '025_HOLISTIC_SYNTHESIS', 'MSR_v5_0.md')

/** True for the registry's own §16 internal audit entries — never real chart
 *  findings (see module header comment). */
export function isMetaStatisticsEntry(signal: Pick<MsrSignal, 'claim_text'>): boolean {
  return signal.claim_text.startsWith('Statistics — ')
}

let cached: MsrSignal[] | null = null

/** All 573 parsed catalog entries, unfiltered — the raw parser output. */
export function loadFullMsrCatalog(): MsrSignal[] {
  if (cached) return cached
  const content = readFileSync(MSR_PATH, 'utf-8')
  cached = parseMsrSignals(content)
  return cached
}

/** The reader-facing subset: full catalog minus the §16 meta-statistics
 *  entries. This is the pool `citation_ranking.ts` ranks over. */
export function loadReaderFacingCatalog(): MsrSignal[] {
  return loadFullMsrCatalog().filter((s) => !isMetaStatisticsEntry(s))
}

/** Read `entities_involved` off a parsed `MsrSignal` as a string array.
 *  The field is typed `unknown | null` on `MsrSignal` (shared with the DB
 *  ingest shape); `parseMsrSignals` always sets it to a `string[]` or `null`
 *  at runtime, so this narrows defensively rather than casting blindly. */
export function entitiesInvolvedOf(signal: MsrSignal): string[] {
  const raw = signal.entities_involved
  if (!Array.isArray(raw)) return []
  return raw.filter((x): x is string => typeof x === 'string')
}
