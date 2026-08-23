/**
 * pariprashna/reader_text/hedge_bands.ts — lane P4-J, the hedge-band detector.
 *
 * WHY THIS MODULE EXISTS. `entries.ts` used to assert, in prose and nowhere
 * else: "No entry below claims a stronger hedge than its own catalog
 * confidence licenses (§N.7 item 6)." Adversarial review machine-checked that
 * assertion against the catalog and found it FALSE — 9 of 25 entries carried a
 * hedge phrase that did not match the band their own catalog `confidence`
 * licenses, 4 of them overclaims (SIG.MSR.513 at confidence 0.68 read
 * "reasonably supported" where the published band requires "genuinely
 * provisional"). A documented status claim with no detector behind it, asserted
 * green and false for 4 of 25, is §N.8's defect class exactly, inside the
 * lane's own stated safety property.
 *
 * So the claim is now computed rather than asserted. `checkHedgeBand` is wired
 * into `review.ts` as a real gate — an entry whose hedge outruns its catalog
 * confidence FAILS review and therefore never reaches the frozen artifact —
 * and `__tests__/hedge_band.test.ts` demonstrates the detector RED (a
 * deliberately overclaimed entry) before its first GREEN counts.
 *
 * WHAT THIS DETECTOR DOES AND DOES NOT CLAIM. It checks ONE mechanical
 * property: that the canonical band marker appearing in `reader_text` is
 * exactly the one the signal's catalog `confidence` licenses. It does NOT
 * check that the surrounding sentence means what the marker says, that the
 * catalog's `confidence` is itself well-calibrated, or that the prose is
 * otherwise honest. Those are not detectable here and are not claimed.
 */
import type { MsrSignal, ReaderTextEntry, ReviewFlag } from './types'

export type HedgeBand = 'well_established' | 'solidly_supported' | 'reasonably_supported' | 'provisional'

/**
 * The canonical marker phrase for each band. These are the exact substrings the
 * detector matches on (case-insensitively); the fuller convention phrasing each
 * one belongs to is in `HEDGE_BAND_CONVENTION` below and in `entries.ts`'s
 * header. Marker phrases are deliberately disjoint — no marker is a substring
 * of another — so "exactly one band claimed" is a decidable property.
 */
export const HEDGE_BAND_MARKERS: Readonly<Record<HedgeBand, string>> = {
  well_established: 'well-established',
  solidly_supported: 'solidly supported',
  reasonably_supported: 'reasonably supported',
  provisional: 'genuinely provisional',
}

/** Human-readable, for error messages and for `entries.ts`'s header. */
export const HEDGE_BAND_CONVENTION: Readonly<Record<HedgeBand, string>> = {
  well_established: 'confidence >= 0.90 — "well-established in the chart"',
  solidly_supported:
    'confidence 0.80-0.89 — "solidly supported, though not the chart\'s single strongest point"',
  reasonably_supported: 'confidence 0.70-0.79 — "reasonably supported, with an open question or two"',
  provisional: 'confidence < 0.70 — "worth naming, but genuinely provisional"',
}

/** Strongest-first, so a mismatch can be reported as overclaim vs underclaim. */
export const HEDGE_BANDS_STRONGEST_FIRST: readonly HedgeBand[] = [
  'well_established',
  'solidly_supported',
  'reasonably_supported',
  'provisional',
]

/**
 * The band a signal's own catalog `confidence` licenses, or `null` when the
 * catalog records no usable confidence for it.
 *
 * The `null` case is load-bearing, not defensive padding: `msr_parser.ts`
 * defaults a MISSING `confidence:` field to the number 0, which is
 * indistinguishable from a genuine 0.00. Mapping that to the weakest band
 * would be a proxy quietly standing in for a claim the catalog never made, so
 * a non-positive confidence licenses NO band at all — and the gate below then
 * requires such an entry to carry no hedge marker rather than a plausible-
 * looking weak one (§N.7 item 6, §N.8).
 */
export function licensedHedgeBand(confidence: number | null | undefined): HedgeBand | null {
  if (typeof confidence !== 'number' || !Number.isFinite(confidence) || confidence <= 0) return null
  if (confidence >= 0.9) return 'well_established'
  if (confidence >= 0.8) return 'solidly_supported'
  if (confidence >= 0.7) return 'reasonably_supported'
  return 'provisional'
}

/** Every distinct band whose canonical marker appears in the text. */
export function detectHedgeBands(readerText: string): HedgeBand[] {
  const haystack = readerText.toLowerCase()
  return HEDGE_BANDS_STRONGEST_FIRST.filter((band) => haystack.includes(HEDGE_BAND_MARKERS[band]))
}

export interface HedgeBandResult {
  readonly passed: boolean
  readonly licensed: HedgeBand | null
  readonly claimed: readonly HedgeBand[]
  readonly flags: readonly ReviewFlag[]
}

/**
 * The gate. An entry passes when it claims exactly one band and that band is
 * the one its catalog confidence licenses — or, when the catalog licenses no
 * band, when it claims none.
 */
export function checkHedgeBand(entry: ReaderTextEntry, signal: MsrSignal | null): HedgeBandResult {
  const licensed = signal ? licensedHedgeBand(signal.confidence) : null
  const claimed = detectHedgeBands(entry.reader_text)
  const flags: ReviewFlag[] = []

  const fail = (code: string, detail: string): HedgeBandResult => {
    flags.push({ source: 'hedge_band', code, level: 'error', detail })
    return { passed: false, licensed, claimed, flags }
  }

  if (!signal) {
    return fail(
      'hedge_band_unknown_signal',
      `${entry.signal_id} has no catalog signal, so no confidence licenses any hedge`,
    )
  }

  if (claimed.length === 0) {
    return licensed === null
      ? { passed: true, licensed, claimed, flags }
      : fail(
          'hedge_band_absent',
          `${entry.signal_id} states no confidence hedge; catalog confidence ${signal.confidence} licenses "${HEDGE_BAND_MARKERS[licensed]}" (${HEDGE_BAND_CONVENTION[licensed]})`,
        )
  }

  if (claimed.length > 1) {
    return fail(
      'hedge_band_ambiguous',
      `${entry.signal_id} claims ${claimed.length} different hedge bands (${claimed.join(', ')}); exactly one is required`,
    )
  }

  if (licensed === null) {
    return fail(
      'hedge_band_unlicensed',
      `${entry.signal_id} claims "${HEDGE_BAND_MARKERS[claimed[0]]}" but its catalog entry records no usable confidence (${signal.confidence}) — no band is licensed`,
    )
  }

  if (claimed[0] !== licensed) {
    const claimedRank = HEDGE_BANDS_STRONGEST_FIRST.indexOf(claimed[0])
    const licensedRank = HEDGE_BANDS_STRONGEST_FIRST.indexOf(licensed)
    const direction = claimedRank < licensedRank ? 'OVERCLAIM' : 'underclaim'
    return fail(
      'hedge_band_mismatch',
      `${entry.signal_id} ${direction}: text claims "${HEDGE_BAND_MARKERS[claimed[0]]}" but catalog confidence ${signal.confidence} licenses "${HEDGE_BAND_MARKERS[licensed]}" (${HEDGE_BAND_CONVENTION[licensed]})`,
    )
  }

  return { passed: true, licensed, claimed, flags }
}
