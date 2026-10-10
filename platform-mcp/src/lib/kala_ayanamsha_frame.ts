/**
 * Ayanamsha frame disclosure for the Kala views that join NATAL facts (read in the caller's
 * ayanamsha) with live TRANSIT positions (always sidereal Lahiri, from the L0 ephemeris sidecar).
 *
 * SS N-342: Lahiri is the primary reading. With the default id the two sides share one frame. When
 * a caller names another stored ayanamsha the natal side moves and the transit side does not, so
 * natal-vs-transit comparisons (gochara house counts, dasha-lord transit condition, ...) join two
 * different frames. That mix is DISCLOSED here as data, never silently reconciled.
 */
import { PRIMARY_AYANAMSHA } from './ayanamsha.js'

export interface KalaAyanamshaFrame {
  natal_ayanamsha_id: string
  /** The L0 ephemeris sidecar serves sidereal Lahiri; the transit side never follows the caller's id. */
  transit_ayanamsha_id: string
  frame_mixed: boolean
  label: string
  note: string | null
}

export function buildKalaAyanamshaFrame(natalAyanamshaId: string): KalaAyanamshaFrame {
  const mixed = natalAyanamshaId !== PRIMARY_AYANAMSHA
  return {
    natal_ayanamsha_id: natalAyanamshaId,
    transit_ayanamsha_id: PRIMARY_AYANAMSHA,
    frame_mixed: mixed,
    label: mixed
      ? `Mixed frame: natal facts read at ${natalAyanamshaId}, transit positions at ${PRIMARY_AYANAMSHA}`
      : `Single frame: natal facts and transit positions both at ${PRIMARY_AYANAMSHA} (primary)`,
    note: mixed
      ? `Natal-vs-transit joins (gochara house counts, dasha-lord transit condition, ...) compare ${natalAyanamshaId} natal ` +
        `positions with ${PRIMARY_AYANAMSHA} transits. Omit ayanamsha_id for the primary single-frame reading.`
      : null,
  }
}
