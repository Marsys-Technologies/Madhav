/**
 * curve.ts — the T-0 retrodiction-gate harness's curve-construction + scoring
 * math (BRIEF_D3.md §F1 Lane T-0). Pure functions, no network — the whole
 * point is that this module is unit-testable offline against fixture dasha
 * periods (CONDUCTOR_PROTOCOL §3.1(b): "verifier runs the test suite
 * itself").
 *
 * WHAT CURVE THIS IS, AND WHY (documented per the brief's explicit
 * instruction: "document exactly what curve you built and why"):
 *
 * D-3's transit kernel (Lane T-2/T-3) has not shipped yet — this harness
 * builds FIRST, with no dependency on the rest of the wave. The brief
 * names "kala_activation proximity" as the fallback substrate. What is
 * actually servable TODAY on 482012f1 at day-scale resolution is the
 * Vimśottarī dasha-period table (`ganita_dasha_periods_get`), whose
 * nested levels have exactly the right natural granularity for a ±45-day
 * test: level-1 (Mahādaśā) spans years, level-2 (Antardaśā) spans roughly
 * MD/9, level-3 (Pratyantardaśā) spans roughly AD/9 — for this chart's
 * Mercury MD (~17y) that puts Pratyantar periods at ~roughly 2-3 months,
 * squarely inside a ±45-day window.
 *
 * DR-10 (DIS.023, ratified 2026-07-17) names pratyantar-lord decomposition
 * as the classical DEFAULT peak model (vs. the deprecated midpoint-triangle,
 * vs. the transit-kernel that supersedes both once it ships). This harness
 * approximates that default with what's servable today: a DASHA-LORD
 * CONFLUENCE score — at each date, sum a depth-weighted contribution for
 * every active nested dasha level (MD/AD/PD) whose running lord is one of
 * the mechanism's significator grahas, weighting deeper (more localized)
 * levels more heavily so a date where the significator runs concurrently
 * at MD+AD+PD scores far higher than one where it only runs at MD. This is
 * the T-0 INTERIM proxy, not the shipped kernel — every score this harness
 * emits is tagged `peak_basis: 'dasha_lord_confluence_v1'` (not
 * `pratyantar_lord | midpoint_triangle | transit_kernel`, DR-10's three
 * named models) so a future comparison (D-4 per DR-12) is honest about
 * what produced it.
 */

export type DashaPeriod = {
  level: number // 1=Mahadasha .. 4=Sookshma
  lord: string // e.g. "Jupiter"
  start: Date
  end: Date
}

export type CurvePoint = { date: Date; intensity: number }

// Deeper (more localized) dasha levels weight more heavily — a date where
// the significator lord is running concurrently at MD+AD+PD is a much
// stronger classical confluence than one where only the MD lord matches.
const DEPTH_WEIGHT: Record<number, number> = { 1: 1, 2: 2, 3: 4, 4: 8 }

/** Finds the period at a given level covering `date`, or undefined. Linear scan — periods lists here are in the hundreds, not worth indexing. */
function periodAt(periods: DashaPeriod[], level: number, date: Date): DashaPeriod | undefined {
  const t = date.getTime()
  return periods.find((p) => p.level === level && p.start.getTime() <= t && t < p.end.getTime())
}

/**
 * significators: graha name -> weight (typically the dasha-lord's
 * `ratification_factor` for the relevant domain, from
 * `ganita_dasha_lord_capability_get`, or 1.0 when no domain-ratification
 * exists — see mechanisms.ts DOMAIN_LORDS).
 */
export function intensityAt(periods: DashaPeriod[], significators: Record<string, number>, date: Date): number {
  let total = 0
  for (const level of [1, 2, 3, 4]) {
    const p = periodAt(periods, level, date)
    if (!p) continue
    const w = significators[p.lord]
    if (w) total += DEPTH_WEIGHT[level] * w
  }
  return total
}

export function buildCurve(
  periods: DashaPeriod[],
  significators: Record<string, number>,
  rangeStart: Date,
  rangeEnd: Date,
  stepDays: number
): CurvePoint[] {
  const out: CurvePoint[] = []
  for (let t = rangeStart.getTime(); t <= rangeEnd.getTime(); t += stepDays * 86_400_000) {
    const date = new Date(t)
    out.push({ date, intensity: intensityAt(periods, significators, date) })
  }
  return out
}

/** Value at the given percentile (0..1) of the curve's intensity distribution, nearest-rank. */
export function percentileThreshold(curve: CurvePoint[], p: number): number {
  if (curve.length === 0) return 0
  const sorted = [...curve.map((c) => c.intensity)].sort((a, b) => a - b)
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil(p * sorted.length) - 1))
  return sorted[idx]
}

export const topDecileThreshold = (curve: CurvePoint[]): number => percentileThreshold(curve, 0.9)
export const topTercileThreshold = (curve: CurvePoint[]): number => percentileThreshold(curve, 2 / 3)

/** Local max within ±windowDays of `center`. Returns undefined if the curve has no points in range. */
export function localMax(curve: CurvePoint[], center: Date, windowDays: number): CurvePoint | undefined {
  const lo = center.getTime() - windowDays * 86_400_000
  const hi = center.getTime() + windowDays * 86_400_000
  let best: CurvePoint | undefined
  for (const pt of curve) {
    const t = pt.date.getTime()
    if (t < lo || t > hi) continue
    if (!best || pt.intensity > best.intensity) best = pt
  }
  return best
}

/** Fraction of curve points at/above `threshold` — the anti-gaming "top-decile is <15% of days" check operates on this. */
export function fractionAtOrAbove(curve: CurvePoint[], threshold: number): number {
  if (curve.length === 0) return 0
  const n = curve.filter((c) => c.intensity >= threshold).length
  return n / curve.length
}

export function variance(curve: CurvePoint[]): number {
  if (curve.length === 0) return 0
  const mean = curve.reduce((s, c) => s + c.intensity, 0) / curve.length
  return curve.reduce((s, c) => s + (c.intensity - mean) ** 2, 0) / curve.length
}

/**
 * Anti-gaming negative control: a circular time-shift of the REAL dasha
 * timeline. B.10 forbids fabricating chart computation, so this does not
 * invent a new ephemeris/dasha run for a synthetic birth date (that would
 * require re-running the natal engine, which this harness has no mandate
 * to do) — instead it permutes the chart's OWN already-computed nested
 * dasha structure by a fixed offset, wrapping within [boundsStart,
 * boundsEnd), which approximates "this chart's mechanism structure as it
 * would fall on a differently-timed life" without inventing any new
 * astrological value. Each period's start/end is shifted independently and
 * wrapped; a period whose shifted end lands before its shifted start is
 * understood to wrap around the boundary (membership test in periodAt
 * handles only non-wrapping periods, so wrapping periods are split into
 * two on shift — see splitIfWrapped).
 */
export function circularShiftPeriods(periods: DashaPeriod[], shiftDays: number, boundsStart: Date, boundsEnd: Date): DashaPeriod[] {
  const totalMs = boundsEnd.getTime() - boundsStart.getTime()
  if (totalMs <= 0) return periods
  const wrap = (d: Date): number => {
    const offset = ((d.getTime() - boundsStart.getTime() + shiftDays * 86_400_000) % totalMs + totalMs) % totalMs
    return boundsStart.getTime() + offset
  }
  const out: DashaPeriod[] = []
  for (const p of periods) {
    const s = wrap(p.start)
    const e = wrap(p.end)
    if (e > s) {
      out.push({ ...p, start: new Date(s), end: new Date(e) })
    } else {
      // wrapped around the boundary — split into two non-wrapping pieces
      out.push({ ...p, start: new Date(s), end: new Date(boundsEnd) })
      out.push({ ...p, start: new Date(boundsStart), end: new Date(e) })
    }
  }
  return out
}
