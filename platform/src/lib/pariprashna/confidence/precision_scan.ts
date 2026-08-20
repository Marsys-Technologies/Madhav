/**
 * pariprashna/confidence/precision_scan.ts — the T-8 precision scan (lane
 * G3-C, PPR-03).
 *
 * PPR-03 (line 148): "a quantity MUST NOT be served with more precision than
 * its sample supports (T-8)." e.g. "73.4% confident" from a sample of 3
 * outcomes overstates precision the sample cannot support; the honest thing
 * is fewer significant figures or a qualitative band.
 *
 * SCOPE (deliberately narrow, not a blanket numeric-value scanner): this scan
 * applies to a numeric confidence value ONLY when it is paired with a REAL
 * backing sample size — the same `sampleSize` shape
 * `activation_gate.ts#extractCalibrationSampleSize` already extracts from a
 * calibration-bearing tool's own result payload
 * (`calibration_summary.total_matches` / `verdict_distribution[].n`). A
 * numeric score with no determinable backing sample (an embedding-similarity
 * score, a structural weight, anything NOT drawn from
 * `mimamsa_calibration`/`mimamsa_reliability`) is out of scope for THIS
 * detector — scanning it here would be exactly the "checks a proxy rather
 * than the claim" failure mode CLAUDE.md §N.8 names; a value with no
 * determinable sample size is reported `sample_size: null` and the scan
 * conservatively treats it as unsupported-for-any-decimal-precision (see
 * `scanPrecision` below), never silently skipped.
 *
 * THE PRECISION BANDS ARE AN HONEST, DISCLOSED PLACEHOLDER (same disclosure
 * discipline as `activation_gate.ts`'s threshold — no such band table exists
 * anywhere in this codebase; grepped alongside the activation-gate search
 * with zero hits). The bands below are a conservative, named convention:
 * roughly, the number of decimal places a percentage figure can honestly
 * carry given how wide a binomial-proportion confidence interval a sample of
 * that size implies. A real L5 calibration owner should replace this with a
 * data-driven standard-error-based rule once real volume exists.
 */

/** Honest, disclosed placeholder bands — see module docblock. */
export const PRECISION_SCAN_BANDS_ARE_PLACEHOLDER = true as const

export interface PrecisionBand {
  /** Inclusive lower bound of sample size for this band. */
  minSampleSize: number
  /** Maximum decimal places a served percentage/probability may carry at this sample size. */
  maxDecimalPlaces: number
  /** Human-readable qualitative band name used when maxDecimalPlaces is 0 and a numeric % is still not warranted. */
  label: string
}

/**
 * Ordered ascending by `minSampleSize`; `scanPrecision` picks the last band
 * whose `minSampleSize` the real sample size clears.
 */
export const PRECISION_BANDS: readonly PrecisionBand[] = [
  { minSampleSize: 0, maxDecimalPlaces: 0, label: 'insufficient_sample' },
  { minSampleSize: 5, maxDecimalPlaces: 0, label: 'integer_percent_only' },
  { minSampleSize: 30, maxDecimalPlaces: 1, label: 'one_decimal_supported' },
  { minSampleSize: 100, maxDecimalPlaces: 2, label: 'two_decimal_supported' },
]

export interface PrecisionScanInput {
  /** The numeric value as actually served (e.g. 0.734 for "73.4%"). */
  value: number
  /** Decimal places the served representation actually carries (e.g. 1 for "73.4"). */
  servedDecimalPlaces: number
  /**
   * The real backing sample size, from the SAME calibration-bearing tool
   * result the value itself came from (see module docblock scope note).
   * `null` when no real sample size could be determined this turn.
   */
  sampleSize: number | null
}

export interface PrecisionScanResult {
  overstated: boolean
  max_supported_decimal_places: number
  served_decimal_places: number
  sample_size: number | null
  band_label: string
  /** `value` rounded down to `max_supported_decimal_places`; the honest replacement for an overstated figure. */
  demoted_value: number
  bands_are_placeholder: boolean
}

function bandFor(sampleSize: number | null): PrecisionBand {
  if (sampleSize === null || sampleSize < 0) return PRECISION_BANDS[0]
  let selected = PRECISION_BANDS[0]
  for (const band of PRECISION_BANDS) {
    if (sampleSize >= band.minSampleSize) selected = band
  }
  return selected
}

function roundToDecimalPlaces(value: number, places: number): number {
  const factor = 10 ** places
  return Math.round(value * factor) / factor
}

/**
 * Scan one served numeric value for T-8 overstated precision. Never throws;
 * a genuinely unsupportable sample (`null` or 0) demotes to the coarsest
 * band rather than being skipped — an honest null-sample input is exactly
 * the case this scan exists to catch, not an edge case to special-case away.
 */
export function scanPrecision(input: PrecisionScanInput): PrecisionScanResult {
  const band = bandFor(input.sampleSize)
  const overstated = input.servedDecimalPlaces > band.maxDecimalPlaces
  return {
    overstated,
    max_supported_decimal_places: band.maxDecimalPlaces,
    served_decimal_places: input.servedDecimalPlaces,
    sample_size: input.sampleSize,
    band_label: band.label,
    demoted_value: roundToDecimalPlaces(input.value, band.maxDecimalPlaces),
    bands_are_placeholder: PRECISION_SCAN_BANDS_ARE_PLACEHOLDER,
  }
}

/** Count the decimal places a number literally carries (e.g. 0.734 → 3, 73 → 0). Defensive against floating-point noise up to 12 places. */
export function countDecimalPlaces(value: number): number {
  if (!Number.isFinite(value)) return 0
  const s = value.toString()
  if (s.includes('e-')) {
    // Scientific notation for very small numbers (e.g. 1e-7) — treat as
    // carrying at least that many decimal places.
    const [, exp] = s.split('e-')
    return Number(exp)
  }
  const dot = s.indexOf('.')
  return dot === -1 ? 0 : s.length - dot - 1
}
