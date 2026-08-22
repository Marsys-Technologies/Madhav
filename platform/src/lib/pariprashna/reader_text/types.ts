/**
 * pariprashna/reader_text/types.ts — lane P4-J (FILLER, "Signal reader text").
 *
 * Shared types for the MSR (Master Signal Register, `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md`)
 * reader-text pipeline: parse the catalog → rank top-cited-first → generate reader
 * text → review (voice lint + citation gate) → freeze. See `generate_and_freeze.ts`'s
 * header comment for the end-to-end account and the charter this lane implements
 * (`00_ARCHITECTURE/briefs/pariprashna_swarm/tracker/PLAN.yaml` P4-J,
 * `PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md` §10.5).
 *
 * Catalog PARSING is deliberately NOT re-implemented here — `platform/src/scripts/
 * etl/msr_parser.ts`'s `parseMsrSignals` already parses the full MSR_v5_0.md into
 * a tested `MsrSignal` shape (573/573, `msr_parser.test.ts`); re-parsing here would
 * be a second, drift-prone reading of the same source (exactly what an earlier
 * draft of this lane did — it silently dropped 4 blocks to 569 via a narrower
 * regex — before this lane was pointed at the existing, tested parser instead).
 */

import type { MsrSignal } from '../../db/types'

export type { MsrSignal }

/** A real, verbatim-captured grouping of citation rows from `message_parts`
 *  (`kind = 'citation'`), keyed by the RAW `body->>'signal_id'` value exactly
 *  as it was written to the wire (before any normalization). See
 *  `citation_ranking.ts`'s header comment for the exact query and capture
 *  timestamp. */
export interface RawCitationCount {
  readonly ref: string
  readonly cite_count: number
}

/** A ranked catalog entry — `MsrSignal` plus the derived citation weight and
 *  which of its `entities_involved` codes actually matched a real citation. */
export interface RankedMsrEntry {
  readonly signal: MsrSignal
  readonly citation_weight: number
  readonly matched_entities: readonly string[]
}

/** Verification grade for a reader-text entry's grounding — deliberately the
 *  SAME vocabulary `citations/types.ts`'s `CitationGrade` uses for live-turn
 *  citations, reused here (not re-invented) because the semantics are
 *  identical: `primary` = directly grounded in the signal's own classical
 *  source + falsifier/derivation note; `supporting` = grounded but via a
 *  secondary/derived reading. There is no live-turn `unverified`/
 *  `prior_reading` case here since every entry is authored against the
 *  catalog directly, never against a live turn's tool calls. */
export type ReaderTextGrade = 'primary' | 'supporting'

/** One hand-authored reader-text entry for one MSR catalog signal. */
export interface ReaderTextEntry {
  readonly signal_id: string
  /** The reader-facing prose. Must pass BOTH `lintReaderProse` (register-leak)
   *  and `lintVoiceProse` (voice) with zero leaks / zero error-level flags,
   *  and the citation gate (see `citation_gate.ts`) before it may freeze. */
  readonly reader_text: string
  readonly grade: ReaderTextGrade
  /** Short, human-auditable note on what grounds this text — e.g. the
   *  classical source name + the specific claim it licenses. NOT shown to
   *  the reader; audit-channel only, same discipline as `ResolvedCitation
   *  .audit_detail`. */
  readonly grounding_note: string
  /** Non-empty when authoring this entry required deliberately DECLINING to
   *  restate part of the catalog signal's own headline because the signal's
   *  own `falsifier` field contradicted it (an honest-null-over-invented-
   *  judgment call, §N.7 item 6). Empty string when not applicable. */
  readonly catalog_discrepancy_note: string
}

export interface ReviewFlag {
  readonly source: 'register_leak' | 'voice' | 'citation_gate' | 'hedge_band'
  readonly code: string
  readonly level: 'info' | 'warn' | 'error'
  readonly detail: string
}

export interface ReviewedEntry {
  readonly signal_id: string
  readonly clean_text: string
  readonly passed: boolean
  readonly flags: readonly ReviewFlag[]
}

export interface FrozenArtifactEntry {
  readonly signal_id: string
  readonly rank: number
  readonly citation_weight: number
  readonly reader_text: string
  readonly grade: ReaderTextGrade
}

export interface FrozenArtifact {
  readonly artifact: 'msr_reader_text_frozen'
  readonly version: string
  readonly generated_at: string
  readonly ranking_method: string
  readonly total_catalog_signals: number
  readonly signals_covered: number
  readonly entries: readonly FrozenArtifactEntry[]
}

export interface FreezeRecord {
  readonly artifact_path: string
  readonly sha256: string
  readonly frozen_at: string
  readonly entry_count: number
}
