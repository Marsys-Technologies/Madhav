/**
 * pariprashna/confidence/activation_gate.ts — the `empirically_calibrated`
 * activation gate (lane G3-C, PPR-03).
 *
 * PPR-03: "`empirically_calibrated` language MUST NOT be used below a passing
 * activation gate." CLAUDE.md §E: L5 Mīmāṃsā is sealed in STRUCTURAL mode —
 * "empirical calibration values fill in as prediction→outcome data accrues"
 * — meaning the honest answer for essentially every claim TODAY is that this
 * tier is NOT yet earned. This module is that gate, built for the first time
 * in this lane (no prior activation-gate concept exists anywhere in the
 * codebase — grepped `MIN_SAMPLE`, `min_sample_size`, `sample_size_threshold`,
 * `activation_gate` across `src/lib` and `platform-mcp` before writing this;
 * zero hits).
 *
 * GROUNDED IN THE REAL CALIBRATION TABLE SHAPE, not invented column names:
 *   - `mimamsa_calibration.n_for_stratum` (migrations/348_mimamsa_pramana.sql
 *     line 21) — the per-match stratum sample size the scoring formula itself
 *     already carries.
 *   - `mimamsa_reliability.n` (same migration, line 42) — the per
 *     probability-bin sample size behind a reliability-curve point.
 *   - `query_insights.ts`'s own `calibration_summary.total_matches`
 *     (`registry/layers/L5_mimamsa/query_insights.ts` — `calSql`'s
 *     `COUNT(*)::int AS total_matches`) — the aggregate match count the
 *     SAME calibration-bearing tool `receipt/assemble.ts`'s
 *     `CALIBRATION_BEARING_TOOL_NAMES` already audits for consultation.
 *   - `query_calibration.ts`'s `verdict_distribution[].n` (`COUNT(*)::int AS
 *     n ... GROUP BY composite_verdict`) — the other calibration-bearing
 *     tool's own per-verdict sample size.
 *
 * THE THRESHOLD IS AN HONEST, DISCLOSED PLACEHOLDER, not a value sourced
 * from this codebase (none exists — see the grep above) or from any cited
 * MSR/CGM/RM doctrine. `MIN_SAMPLE_SIZE_FOR_EMPIRICAL_CALIBRATION = 30` is
 * the conventional statistical rule-of-thumb minimum for a normal-approximation
 * confidence interval on a proportion to start being informative (not a
 * MARSYS-JIS-specific derivation). It is deliberately conservative — a real
 * L5 calibration-owner decision should replace it once real prediction→
 * outcome volume exists to justify a data-driven threshold. Every caller of
 * `evaluateEmpiricalCalibrationGate` receives this disclosure back in
 * `gate_note` so no downstream surface can present the number as anything
 * other than what it is.
 */

/**
 * Conservative, HONESTLY-DISCLOSED placeholder — see module docblock. Not
 * sourced from MARSYS-JIS doctrine; replace once real calibration volume
 * justifies a data-driven threshold.
 */
export const MIN_SAMPLE_SIZE_FOR_EMPIRICAL_CALIBRATION = 30 as const

export const ACTIVATION_GATE_THRESHOLD_IS_PLACEHOLDER = true as const

export interface CalibrationSampleInput {
  /**
   * The real, already-computed aggregate sample size behind this turn's
   * calibration claim — e.g. `calibration_summary.total_matches`
   * (query_insights) or the sum of `verdict_distribution[].n`
   * (query_calibration). `null` when no real sample-size figure could be
   * determined this turn (the honest default — the gate NEVER assumes a
   * sample exists it cannot see).
   */
  sampleSize: number | null
  /** Override for testing / a future data-driven revision. Defaults to the placeholder above. */
  minSampleSize?: number
}

export interface CalibrationGateResult {
  /** True only when a real, non-null sample size meets or exceeds the minimum. */
  gate_open: boolean
  sample_size: number | null
  min_sample_size_required: number
  threshold_is_placeholder: boolean
  gate_note: string
}

const STRUCTURAL_MODE_GATE_NOTE =
  'Gate CLOSED: no real calibration sample size was available this turn, or L5 Mīmāṃsā ' +
  'is still in STRUCTURAL mode (CLAUDE.md §E) with too few prediction→outcome matches to ' +
  'clear the minimum sample size. empirically_calibrated language is not earned.'

const GATE_OPEN_NOTE_PREFIX = 'Gate OPEN: real calibration sample size'

/**
 * The activation gate. NEVER returns `gate_open: true` on a null or
 * sub-threshold sample size — see `__tests__/activation_gate.test.ts` for
 * the proof this returns false under today's real STRUCTURAL-mode
 * conditions (sample size null/zero/low).
 */
export function evaluateEmpiricalCalibrationGate(input: CalibrationSampleInput): CalibrationGateResult {
  const minSampleSize = input.minSampleSize ?? MIN_SAMPLE_SIZE_FOR_EMPIRICAL_CALIBRATION
  const { sampleSize } = input
  const gateOpen = sampleSize !== null && sampleSize >= minSampleSize

  return {
    gate_open: gateOpen,
    sample_size: sampleSize,
    min_sample_size_required: minSampleSize,
    threshold_is_placeholder: ACTIVATION_GATE_THRESHOLD_IS_PLACEHOLDER,
    gate_note: gateOpen
      ? `${GATE_OPEN_NOTE_PREFIX} (n=${sampleSize}) meets the minimum (${minSampleSize}). ` +
        'This clears the PPR-03 activation gate for THIS turn\'s calibration claim only — ' +
        'it does not certify every predictive claim in the reading as calibrated.'
      : STRUCTURAL_MODE_GATE_NOTE,
  }
}

/**
 * Best-effort extraction of a real aggregate calibration sample size from a
 * calibration-bearing tool's already-fetched result payload. Defensive by
 * construction (§N.7 item 6 — an honest null beats an invented judgment):
 * any shape mismatch, parse failure, or absent field returns `null` rather
 * than guessing, which mechanically keeps `evaluateEmpiricalCalibrationGate`
 * closed rather than risking a false-open gate on malformed input.
 *
 * Recognizes exactly the two real shapes documented in the module docblock:
 *   - `{ calibration_summary: { total_matches: number } }` (query_insights)
 *   - `{ verdict_distribution: Array<{ n: number }> }` (query_calibration)
 */
export function extractCalibrationSampleSize(payload: unknown): number | null {
  if (payload === null || typeof payload !== 'object') return null
  const obj = payload as Record<string, unknown>

  const calSummary = obj.calibration_summary
  if (calSummary !== null && typeof calSummary === 'object') {
    const totalMatches = (calSummary as Record<string, unknown>).total_matches
    if (typeof totalMatches === 'number' && Number.isFinite(totalMatches)) return totalMatches
    // query_insights' raw SQL COUNT(*) can arrive as a numeric-looking string
    // via some pg drivers' bigint handling — accept only a clean integer string.
    if (typeof totalMatches === 'string' && /^\d+$/.test(totalMatches)) return Number(totalMatches)
  }

  const verdicts = obj.verdict_distribution
  if (Array.isArray(verdicts)) {
    let sum = 0
    let sawAny = false
    for (const row of verdicts) {
      if (row === null || typeof row !== 'object') continue
      const n = (row as Record<string, unknown>).n
      if (typeof n === 'number' && Number.isFinite(n)) {
        sum += n
        sawAny = true
      }
    }
    if (sawAny) return sum
  }

  return null
}

/** A candidate numeric field to which the T-8 precision scan may apply, plus
 *  the real backing sample size for that specific field (never a different
 *  field's sample size). */
export interface CalibrationPrecisionCandidate {
  value: number
  sampleSize: number | null
}

function coerceFiniteNumber(raw: unknown): number | null {
  if (typeof raw === 'number' && Number.isFinite(raw)) return raw
  // Postgres numeric(...) columns can arrive as strings via some pg driver
  // paths (bigint/numeric handling) — accept a clean numeric string, same
  // defensive convention `extractCalibrationSampleSize` already uses above.
  if (typeof raw === 'string' && raw.trim() !== '' && Number.isFinite(Number(raw))) return Number(raw)
  return null
}

/**
 * G3BC hardening defect 2. `receipt/assemble.ts`'s T-8 precision scan used
 * to read `ToolBundleResult.confidence` — a top-level field NEITHER
 * `query_calibration.ts` NOR `query_insights.ts` ever populates (both return
 * their real data as a JSON-stringified `content` field — see
 * `tool_name_bridge.ts#toToolBundleResults`'s `'content' in content`
 * branch). This function is the fix: it reads precision-bearing numeric
 * values from the SAME PARSED payload shape `extractCalibrationSampleSize`
 * above already successfully parses from (never a second, independently-
 * invented parsing path), grounded in the real column names those two
 * handlers actually return:
 *
 *   - `calibration_summary.mean_composite_score` (query_insights,
 *     `numeric(4,3)`) — paired with `calibration_summary.total_matches`, the
 *     SAME aggregate sample size `extractCalibrationSampleSize` extracts for
 *     this shape.
 *   - `verdict_distribution[].mean_score` / `.mean_timing` / `.mean_domain` /
 *     `.mean_magnitude` (query_calibration, each `numeric(4,3)`) — each
 *     PAIRED WITH THAT SAME ROW'S OWN `n`, never the turn-wide/summed sample
 *     size — a per-verdict-group mean is only as precise as that group's own
 *     count supports, not the whole turn's.
 *
 * Defensive by construction (§N.7 item 6): an unrecognized shape or
 * non-numeric field returns no candidates for that field rather than
 * guessing.
 */
export function extractCalibrationPrecisionCandidates(payload: unknown): CalibrationPrecisionCandidate[] {
  if (payload === null || typeof payload !== 'object') return []
  const obj = payload as Record<string, unknown>
  const out: CalibrationPrecisionCandidate[] = []

  const calSummary = obj.calibration_summary
  if (calSummary !== null && typeof calSummary === 'object') {
    const summary = calSummary as Record<string, unknown>
    const value = coerceFiniteNumber(summary.mean_composite_score)
    if (value !== null) {
      out.push({ value, sampleSize: coerceFiniteNumber(summary.total_matches) })
    }
  }

  const verdicts = obj.verdict_distribution
  if (Array.isArray(verdicts)) {
    for (const row of verdicts) {
      if (row === null || typeof row !== 'object') continue
      const r = row as Record<string, unknown>
      const rowSampleSize = coerceFiniteNumber(r.n)
      for (const field of ['mean_score', 'mean_timing', 'mean_domain', 'mean_magnitude'] as const) {
        const value = coerceFiniteNumber(r[field])
        if (value !== null) out.push({ value, sampleSize: rowSampleSize })
      }
    }
  }

  return out
}
