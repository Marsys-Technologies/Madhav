/**
 * Ayanamsha frame disclosure for the Kala views that join NATAL facts (read in the caller's
 * ayanamsha) with live TRANSIT positions (always sidereal Lahiri, from the L0 ephemeris sidecar).
 *
 * SS N-342: Lahiri is the primary reading. With the default id the two sides share one frame. When
 * a caller names another stored ayanamsha the natal side moves and the transit side does not, so
 * natal-vs-transit comparisons (gochara house counts, dasha-lord transit condition, ...) join two
 * different frames. That mix is DISCLOSED here as data, never silently reconciled.
 *
 * SS N-412 (2): some Kāla tables are written at ONE canonical ayanamsha (their writers pin
 * `CANONICAL_AYANAMSHA = lahiri_chitrapaksha`, their handlers take no ayanamsha filter). A section served from such a
 * table is Lahiri whatever `ayanamsha_id` the caller requested, so `natal_ayanamsha_id` (the requested id) must not be read as
 * its frame: the frame lists those sections with their REAL frame (`lahiri_only_sections`) and the label/note say so.
 */
import { PRIMARY_AYANAMSHA } from './ayanamsha.js'

/** A response section served from a Kāla table that exists at the Lahiri primary only. */
export interface LahiriOnlySection {
  /** The key of the section in the view's result. */
  section: string
  /** The table (or capability source) the section is served from. */
  table: string
  /** The frame the section is REALLY in, whatever ayanamsha_id was requested. */
  ayanamsha_id: typeof PRIMARY_AYANAMSHA
}

const lahiriOnly = (section: string, table: string): LahiriOnlySection => ({ section, table, ayanamsha_id: PRIMARY_AYANAMSHA })

/**
 * kala_now_get sections whose tables are single-ayanamsha: the writers (ka_kota_chakra, ka_sudarshana_varsha, ka_moorti_nirnaya,
 * ka_vedha_gochara, ka_tithi_pravesha) pin CANONICAL_AYANAMSHA = lahiri_chitrapaksha and the L3 handlers (query_kota_chakra,
 * query_sudarshana_varsha, query_moorti_nirnaya, query_vedha_gochara, query_tithi_pravesha) take no ayanamsha filter.
 */
export const KALA_NOW_LAHIRI_ONLY_SECTIONS: readonly LahiriOnlySection[] = [
  lahiriOnly('kota_chakra', 'kala_kota_chakra'),
  lahiriOnly('sudarshana_varsha', 'kala_sudarshana_varsha'),
  lahiriOnly('moorti_nirnaya', 'kala_moorti_nirnaya'),
  lahiriOnly('vedha_gochara', 'kala_vedha_gochara'),
  lahiriOnly('tithi_pravesha', 'kala_tithi_pravesha'),
]

/**
 * kala_ahead_get: `period_echo` takes its pre-birth cutoff (the birth-year floor, `fetchBirthYearFloor`) from the first chapter of
 * kala_jivana_parva, whose writer scopes the life-arc to the vimshottari spine at lahiri_chitrapaksha ("canonical ayanamsha").
 * Only that cutoff is Lahiri-only; the echo's own dasha reads follow `ayanamsha_id`, which the table text says.
 */
export const KALA_AHEAD_LAHIRI_ONLY_SECTIONS: readonly LahiriOnlySection[] = [
  lahiriOnly('period_echo', 'kala_jivana_parva (birth-year cutoff only; the echo\'s dasha reads follow ayanamsha_id)'),
]

export interface KalaAyanamshaFrame {
  /** The ayanamsha the PER-AYANAMSHA natal reads were requested/served at. It is NOT the frame of `lahiri_only_sections`. */
  natal_ayanamsha_id: string
  /** The L0 ephemeris sidecar serves sidereal Lahiri; the transit side never follows the caller's id. */
  transit_ayanamsha_id: string
  frame_mixed: boolean
  /** Sections served from Lahiri-only tables, each with its real frame (not the requested id). */
  lahiri_only_sections: LahiriOnlySection[]
  label: string
  note: string | null
}

export function buildKalaAyanamshaFrame(
  natalAyanamshaId: string,
  lahiriOnlySections: readonly LahiriOnlySection[] = [],
): KalaAyanamshaFrame {
  const mixed = natalAyanamshaId !== PRIMARY_AYANAMSHA
  const sections = lahiriOnlySections.map((s) => ({ ...s }))
  const names = sections.map((s) => s.section).join(', ')
  const lahiriOnlyLabel = mixed && sections.length > 0
    ? `; Lahiri-only tables (${names}) are stored at ${PRIMARY_AYANAMSHA} whatever ayanamsha_id was requested`
    : ''
  const lahiriOnlyNote = mixed && sections.length > 0
    ? ` The sections ${names} are served from Lahiri-only tables: they are ${PRIMARY_AYANAMSHA} readings, NOT ${natalAyanamshaId} ` +
      'readings, although natal_ayanamsha_id echoes the requested id.'
    : ''
  return {
    natal_ayanamsha_id: natalAyanamshaId,
    transit_ayanamsha_id: PRIMARY_AYANAMSHA,
    frame_mixed: mixed,
    lahiri_only_sections: sections,
    label: mixed
      ? `Mixed frame: natal facts read at ${natalAyanamshaId}, transit positions at ${PRIMARY_AYANAMSHA}${lahiriOnlyLabel}`
      : `Single frame: natal facts and transit positions both at ${PRIMARY_AYANAMSHA} (primary)`,
    note: mixed
      ? `Natal-vs-transit joins (gochara house counts, dasha-lord transit condition, ...) compare ${natalAyanamshaId} natal ` +
        `positions with ${PRIMARY_AYANAMSHA} transits.${lahiriOnlyNote} Omit ayanamsha_id for the primary single-frame reading.`
      : null,
  }
}
