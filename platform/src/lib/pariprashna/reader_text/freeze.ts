/**
 * pariprashna/reader_text/freeze.ts — lane P4-J freeze step.
 *
 * §10.5: "frozen artifact hashed and recorded." The freeze step is a single
 * serialized step (never parallelized, unlike generation) — `buildFrozenArtifact`
 * is a pure function of its (already-reviewed) inputs, and `computeArtifactHash`
 * is a pure function of the artifact's canonical serialization, so the
 * "single serialized step" property holds by construction: there is nothing
 * for two concurrent callers to race on.
 *
 * §N.8: this hash check needs a real detector, demonstrated capable of
 * failing — `freeze.test.ts` mutates one byte of a frozen artifact and shows
 * `verifyFreeze` catches it (RED), then shows the untampered artifact verifies
 * clean (GREEN). See that test for the verbatim mutate-and-catch proof.
 */
import { createHash } from 'node:crypto'

import type { FreezeRecord, FrozenArtifact, FrozenArtifactEntry, ReaderTextEntry, ReviewedEntry } from './types'
import type { RankedMsrEntry } from './types'

export const READER_TEXT_ARTIFACT_VERSION = '1.0.0'
export const RANKING_METHOD_DESCRIPTION =
  'top-cited-first: each MSR signal ranked by the sum of real message_parts ' +
  'citation counts (kind=citation, captured 2026-08-23) matched against its ' +
  'entities_involved codes, YGA.<->YOG. aliased, compound refs split on commas; ' +
  'ties broken by signal_id ascending; zero-citation signals sort last in ' +
  'signal_id order (honest fallback, not a real citation signal) — see ' +
  'citation_ranking.ts header comment for the full derivation and its one ' +
  'documented namespace-alias finding.'

/**
 * Assemble the frozen artifact from reviewed (passed-only) entries and their
 * rank/weight from the citation ranking. Entries that failed review MUST NOT
 * be passed in here — this function trusts its caller already filtered
 * (`generate_and_freeze.ts` is the one call site and does so explicitly).
 */
export function buildFrozenArtifact(
  reviewed: readonly ReviewedEntry[],
  ranked: readonly RankedMsrEntry[],
  authoredById: ReadonlyMap<string, ReaderTextEntry>,
  totalCatalogSignals: number,
): FrozenArtifact {
  const rankById = new Map(ranked.map((r, i) => [r.signal.signal_id, { rank: i + 1, weight: r.citation_weight }]))
  const entries: FrozenArtifactEntry[] = reviewed
    .filter((r) => r.passed)
    .map((r) => {
      // Both lookups THROW rather than defaulting. A reviewed entry with no
      // authored source, or with no rank, is a caller bug; the previous
      // `?? 'primary'` and `?? -1` fallbacks would have shipped an invented
      // grade and a nonsense rank into a hashed artifact under a green build
      // (SS N.7 item 6 / SS N.8 — a plausible-looking default standing in for
      // "I don't know" is the defect, not the guard against it).
      const authored = authoredById.get(r.signal_id)
      if (!authored) {
        throw new Error(`buildFrozenArtifact: reviewed entry ${r.signal_id} has no authored ReaderTextEntry`)
      }
      const rankInfo = rankById.get(r.signal_id)
      if (!rankInfo) {
        throw new Error(`buildFrozenArtifact: reviewed entry ${r.signal_id} has no rank in the citation ranking`)
      }
      return {
        signal_id: r.signal_id,
        rank: rankInfo.rank,
        citation_weight: rankInfo.weight,
        reader_text: r.clean_text,
        grade: authored.grade,
        grounding_note: authored.grounding_note,
        catalog_discrepancy_note: authored.catalog_discrepancy_note,
      }
    })
    .sort((a, b) => a.rank - b.rank)

  return {
    artifact: 'msr_reader_text_frozen',
    version: READER_TEXT_ARTIFACT_VERSION,
    generated_at: new Date().toISOString(),
    ranking_method: RANKING_METHOD_DESCRIPTION,
    total_catalog_signals: totalCatalogSignals,
    signals_covered: entries.length,
    entries,
  }
}

/** Canonical (stable-key-order) JSON serialization — the ONLY representation
 *  ever hashed. Re-serializing the same logical artifact must always produce
 *  byte-identical output regardless of object construction order. */
export function canonicalSerialize(artifact: FrozenArtifact): string {
  const sortedEntries = [...artifact.entries]
    .slice()
    .sort((a, b) => a.rank - b.rank)
    .map((e) => ({
      signal_id: e.signal_id,
      rank: e.rank,
      citation_weight: e.citation_weight,
      reader_text: e.reader_text,
      grade: e.grade,
      grounding_note: e.grounding_note,
      catalog_discrepancy_note: e.catalog_discrepancy_note,
    }))
  const canonical = {
    artifact: artifact.artifact,
    version: artifact.version,
    generated_at: artifact.generated_at,
    ranking_method: artifact.ranking_method,
    total_catalog_signals: artifact.total_catalog_signals,
    signals_covered: artifact.signals_covered,
    entries: sortedEntries,
  }
  return JSON.stringify(canonical, null, 2)
}

export function computeArtifactHash(artifact: FrozenArtifact): string {
  return createHash('sha256').update(canonicalSerialize(artifact), 'utf8').digest('hex')
}

export function buildFreezeRecord(artifact: FrozenArtifact, artifactPath: string): FreezeRecord {
  return {
    artifact_path: artifactPath,
    sha256: computeArtifactHash(artifact),
    frozen_at: artifact.generated_at,
    entry_count: artifact.entries.length,
  }
}

/**
 * Recompute the hash of a serialized artifact string and compare it against
 * a recorded `FreezeRecord`. Returns `{ intact: false, ... }` on ANY mismatch
 * — a single mutated byte anywhere in the serialized text changes the sha256
 * digest (see `freeze.test.ts`'s mutate-and-catch proof).
 */
export function verifyFreeze(
  serializedArtifact: string,
  record: FreezeRecord,
): { intact: boolean; recomputed_sha256: string; recorded_sha256: string } {
  const recomputed = createHash('sha256').update(serializedArtifact, 'utf8').digest('hex')
  return {
    intact: recomputed === record.sha256,
    recomputed_sha256: recomputed,
    recorded_sha256: record.sha256,
  }
}
