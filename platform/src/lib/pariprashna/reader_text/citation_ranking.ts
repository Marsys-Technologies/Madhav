/**
 * pariprashna/reader_text/citation_ranking.ts — lane P4-J, "top-cited-first".
 *
 * ── HOW THE RANKING WAS DERIVED (real data, not a guess) ─────────────────────
 * The live system does not (yet) emit a direct `SIG.MSR.NNN` citation onto the
 * wire — a resolved citation cites the underlying CHART FACT / yoga / dasha /
 * event it grounds a claim in (`PLN.SATURN`, `YOG.SASHA_MPY`, `EVT.2025.07…`,
 * …), the same entity-code vocabulary MSR's own `entities_involved` field uses
 * per signal (see `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` — every SIG.MSR.NNN
 * block lists the entity codes it draws on). So "how often has THIS SIGNAL
 * been cited" has no direct column to read; the honest, real-data proxy this
 * module uses instead is: for each MSR signal, SUM the real citation counts
 * of every entity code in its `entities_involved` list. A signal built from
 * heavily-cited planets/yogas ranks above one built from rarely-cited ones —
 * exactly what "top-cited-first" should mean once you go one level down to
 * what the system actually records citations against.
 *
 * `RAW_CITATION_SNAPSHOT` below is the VERBATIM, complete result of:
 *
 *   SELECT body->>'signal_id' AS ref, count(*) AS cite_count
 *   FROM message_parts
 *   WHERE kind = 'citation'
 *   GROUP BY 1
 *   ORDER BY cite_count DESC;
 *
 * run read-only against the live `message_parts` table on 2026-08-23 (119
 * total citation rows across every Paripraśna thread persisted so far, real
 * production + test-thread traffic — not synthetic/fixture data). It is
 * captured as a static snapshot (not queried live at generation time) so this
 * module has no DB dependency and the ranking is reproducibly frozen — a
 * fresh query tomorrow will return different, larger counts as more threads
 * accrue; that is expected and does not invalidate tonight's freeze, which is
 * scoped to this snapshot (`FrozenArtifact.ranking_method` records this).
 *
 * ── NORMALIZATION, DISCLOSED ─────────────────────────────────────────────────
 * One real drift was found while building this: the live citation ledger
 * writes yoga-entity codes with a `YGA.` prefix (`YGA.SASHA_MPY`,
 * `YGA.SATURN_QUADRUPLE`, …) while MSR_v5_0.md's own `entities_involved`
 * arrays use `YOG.` (`YOG.SASHA_MPY`, confirmed zero `YGA.` occurrences
 * anywhere in the 573-signal file). `normalizeEntityCode` treats these as the
 * same namespace (`YGA.` → `YOG.`) so the match is not silently lost — this
 * is a genuine naming drift between the MSR document's authored entity
 * namespace and the live system's citation namespace, worth a DD entry on its
 * own (see the P4-J report), fixed here only for the purpose of this
 * ranking, not "fixed" in either source.
 *
 * A citation row can name more than one entity in one string
 * (`"YGA.BUDH_ADITYA, HSE.10"`, `"PLN.SUN, HSE.10"`) — `splitCompoundRef`
 * splits these on commas so each named entity gets credited the row's full
 * count (the row records one message part citing multiple entities together,
 * not a fractional citation of each).
 *
 * Citation targets OUTSIDE the MSR namespace (`RM.*` — Resonance Map, `EVT.*`
 * — Life Event Log, `SEN.*` — ga_sensitive degrees, `UCN_v4_0.md…` — narrative
 * document section refs) never match any MSR `entities_involved` value (confirmed:
 * `RM.` and `SEN.` have zero occurrences in MSR_v5_0.md) and are correctly
 * excluded from this ranking — they belong to other registers.
 */
import type { MsrSignal, RankedMsrEntry, RawCitationCount } from './types'
import { entitiesInvolvedOf } from './catalog'

export const CITATION_SNAPSHOT_CAPTURED_AT = '2026-08-23T00:00:00Z'
export const CITATION_SNAPSHOT_QUERY =
  "SELECT body->>'signal_id' AS ref, count(*) AS cite_count FROM message_parts " +
  "WHERE kind = 'citation' GROUP BY 1 ORDER BY cite_count DESC;"
export const CITATION_SNAPSHOT_TOTAL_ROWS = 119

/** Verbatim query result — see the module header comment. Do not hand-edit;
 *  regenerate by re-running `CITATION_SNAPSHOT_QUERY` and replacing this
 *  array wholesale (a fresh snapshot is a new, separate freeze). */
export const RAW_CITATION_SNAPSHOT: readonly RawCitationCount[] = [
  { ref: 'PLN.SATURN', cite_count: 8 },
  { ref: 'YGA.SASHA_MPY', cite_count: 6 },
  { ref: 'PLN.JUPITER', cite_count: 5 },
  { ref: 'PLN.RAHU', cite_count: 5 },
  { ref: 'KRK.C8.AMATYA', cite_count: 4 },
  { ref: 'YGA.SATURN_QUADRUPLE', cite_count: 3 },
  { ref: 'PLN.SUN', cite_count: 3 },
  { ref: 'EVT.2025.07.XX.01', cite_count: 3 },
  { ref: 'DSH.VM.AD.MERC_SATURN', cite_count: 3 },
  { ref: 'PLN.MARS', cite_count: 3 },
  { ref: 'YGA.ARIES_LIBRA_AXIS', cite_count: 3 },
  { ref: 'DVS.D9.MOON', cite_count: 3 },
  { ref: 'SEN.ARD.AL', cite_count: 3 },
  { ref: 'YGA.MERCURY_OPERATIONAL_SPINE', cite_count: 3 },
  { ref: 'EVT.2023.05.XX.01', cite_count: 2 },
  { ref: 'KRK.C8.ATMA', cite_count: 2 },
  { ref: 'EVT.2026.04.08.01', cite_count: 2 },
  { ref: 'EVT.2023.07.XX.01', cite_count: 2 },
  { ref: 'DSH.VM.MD.KETU', cite_count: 2 },
  { ref: 'EVT.CURRENT.01', cite_count: 2 },
  { ref: 'SGN.CAPRICORN', cite_count: 2 },
  { ref: 'YGA.D9_12H_STELLIUM', cite_count: 2 },
  { ref: 'RM.05', cite_count: 2 },
  { ref: 'HSE.7', cite_count: 1 },
  { ref: 'SEN.ARD.A6', cite_count: 1 },
  { ref: 'YGA.JUPITER_9H_NEAR_MPY', cite_count: 1 },
  { ref: 'UCN_v1_0.md', cite_count: 1 },
  { ref: 'YGA.BUDH_ADITYA, HSE.10', cite_count: 1 },
  { ref: 'NAK.ASHWINI', cite_count: 1 },
  { ref: 'UCN_v4_0.md', cite_count: 1 },
  { ref: 'DSH.VM.AD.MERC_JUPITER', cite_count: 1 },
  { ref: 'UCN_v4_0.md, Part VII.1', cite_count: 1 },
  { ref: 'UCN_v4_0.md Part IV § IV.4', cite_count: 1 },
  { ref: 'DVS.D10.RAHU', cite_count: 1 },
  { ref: 'FORENSIC_v8_0 §3.3', cite_count: 1 },
  { ref: 'UCN_v4_0.md Part XXIII § XXIII.2', cite_count: 1 },
  { ref: 'UCN_v4_0.md, Part VII.4', cite_count: 1 },
  { ref: 'EVT.2024.02.16.01', cite_count: 1 },
  { ref: 'DVS.D10.SATURN', cite_count: 1 },
  { ref: 'UCN_v4_0.md Part XXIII § XXIII.3', cite_count: 1 },
  { ref: 'YGA.LAKSHMI, YGA.SARASWATI', cite_count: 1 },
  { ref: 'EVT.2007.06.10.01', cite_count: 1 },
  { ref: 'YGA.NBRY_SATURN', cite_count: 1 },
  { ref: 'PLN.SUN, HSE.10', cite_count: 1 },
  { ref: 'YGA.TRIPLE_EXALTED_NODAL', cite_count: 1 },
  { ref: 'PLN.KETU', cite_count: 1 },
  { ref: 'PLN.MERCURY', cite_count: 1 },
  { ref: 'EVT.2026.03.20.01', cite_count: 1 },
  { ref: 'YGA.10H_CAREER_DENSITY', cite_count: 1 },
  { ref: 'UCN_v4_0.md, Part XXIII.1', cite_count: 1 },
  { ref: 'EVT.2022.01.03.01', cite_count: 1 },
  { ref: 'RM.07', cite_count: 1 },
  { ref: 'UCN_v4_0.md §XXIII.2', cite_count: 1 },
  { ref: 'YGA.JUPITER_9L_DHARMA_WEALTH', cite_count: 1 },
  { ref: 'RM.34', cite_count: 1 },
  { ref: 'UCN_v4_0.md Part III § I.1', cite_count: 1 },
  { ref: 'LIFE_EVENT_LOG_v1_2 EVT.2010.XX.XX.01', cite_count: 1 },
  { ref: 'HSE.10', cite_count: 1 },
  { ref: 'RM.03', cite_count: 1 },
  { ref: 'PLN.MOON', cite_count: 1 },
  { ref: 'UCN_v4_0', cite_count: 1 },
  { ref: 'UCN_v4_0.md §XXIII.1', cite_count: 1 },
  { ref: 'YGA.BUDH_ADITYA', cite_count: 1 },
  { ref: 'UCN_v4_0.md, Part XXIII.2', cite_count: 1 },
  { ref: 'DSH.VM.AD.MERC_KETU', cite_count: 1 },
  { ref: 'LIFE_EVENT_LOG_v1_2 EVT.2023.05.XX.01', cite_count: 1 },
  { ref: 'DSH.VM.MD.MERCURY', cite_count: 1 },
  { ref: 'EVT.2025.05.XX.01', cite_count: 1 },
  { ref: 'SGN.PISCES', cite_count: 1 },
]

/** Split a compound citation ref ("YGA.BUDH_ADITYA, HSE.10") into its
 *  individually-named entity codes. A lone ref is a "split" of length 1. */
export function splitCompoundRef(ref: string): string[] {
  return ref
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

/** Normalize one entity code to MSR's own namespace spelling. Currently the
 *  one documented alias: live citations use `YGA.`, MSR uses `YOG.` — see the
 *  module header comment. Everything else passes through unchanged. */
export function normalizeEntityCode(code: string): string {
  if (code.startsWith('YGA.')) return `YOG.${code.slice(4)}`
  return code
}

/** Build a normalized entity-code → total-citation-count map from the raw
 *  snapshot, applying `splitCompoundRef` + `normalizeEntityCode`. */
export function buildCitationFrequencyMap(
  snapshot: readonly RawCitationCount[] = RAW_CITATION_SNAPSHOT,
): Map<string, number> {
  const freq = new Map<string, number>()
  for (const { ref, cite_count } of snapshot) {
    for (const part of splitCompoundRef(ref)) {
      const norm = normalizeEntityCode(part)
      freq.set(norm, (freq.get(norm) ?? 0) + cite_count)
    }
  }
  return freq
}

/**
 * Rank a set of MSR catalog signals top-cited-first: `citation_weight` is the
 * sum of the real citation counts of every entity in the signal's
 * `entities_involved` that matched the (normalized) frequency map. Ties break
 * on `signal_id` ascending (deterministic — no hidden randomness in the
 * freeze). Signals with `citation_weight === 0` sort last, in `signal_id`
 * order — this is the honest fallback ordering for the portion of the
 * catalog the real citation corpus has not touched yet (see the P4-J report
 * for exactly how many that is).
 */
export function rankMsrSignals(
  signals: readonly MsrSignal[],
  freq: Map<string, number> = buildCitationFrequencyMap(),
): RankedMsrEntry[] {
  const ranked = signals.map((signal) => {
    let weight = 0
    const matched: string[] = []
    for (const entity of entitiesInvolvedOf(signal)) {
      const norm = normalizeEntityCode(entity)
      const hit = freq.get(norm)
      if (hit) {
        weight += hit
        matched.push(entity)
      }
    }
    return { signal, citation_weight: weight, matched_entities: matched }
  })
  ranked.sort((a, b) => {
    if (b.citation_weight !== a.citation_weight) return b.citation_weight - a.citation_weight
    return a.signal.signal_id.localeCompare(b.signal.signal_id)
  })
  return ranked
}
