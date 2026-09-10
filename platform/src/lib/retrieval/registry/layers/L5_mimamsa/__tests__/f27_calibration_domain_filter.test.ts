/**
 * F-27 — `query_calibration`'s `domain` parameter must be a REAL, derived filter.
 * ==============================================================================
 * Original finding: `mimamsa_calibration_get({chart_id})` and the same call with
 * `domain: 'career'` returned an identical `result_hash` — `domain` was a complete no-op.
 *
 * The first repair attempt deleted the parameter, on the reasoning that no honest
 * implementation existed. That reasoning was WRONG, and adversarial review caught it:
 * `mimamsa_calibration.prediction_id` (348_mimamsa_pramana.sql:9) resolves to
 * `mimamsa_predictions`, which declares `domain text NOT NULL`
 * (347_mimamsa_bhavisya.sql:10). The join is fully derived from L5's own schema — no
 * invented data — and the schema already ships the composite index for it,
 * `idx_mimamsa_calibration_prediction (chart_id, prediction_id)` (348:31).
 *
 * The fixture row counts below are the REAL live production distribution for the
 * canonical chart (re-verified 2026-08-21, not copied from an older snapshot):
 *   all domains  -> 57 rows: UNRESOLVED 25 / PARTIAL 23 / REFUTED 7 / CONFIRMED 2
 *   domain=career ->  9 rows: UNRESOLVED 9
 *   (relationship 41, transition 7; 0 calibration rows fail to join a prediction)
 *
 * So the finding's premise held all along: a real domain filter DOES narrow the 57 rows.
 * These tests assert the narrowing, not the deletion.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { queryCalibrationCapability } from '../query_calibration'
import { checkCapability } from '../../../chart_agnostic_gate'
import type { CapabilityDescriptor } from '../../../types'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn().mockResolvedValue({ rows: [] }),
}))

import { query as mockQuery } from '@/lib/db/client'

/** Live production verdict distribution for the canonical chart, all domains (57 rows). */
const ALL_DOMAIN_VERDICTS = [
  { composite_verdict: 'UNRESOLVED', n: 25 },
  { composite_verdict: 'PARTIAL', n: 23 },
  { composite_verdict: 'REFUTED', n: 7 },
  { composite_verdict: 'CONFIRMED', n: 2 },
]

/** Live production verdict distribution for the same chart, domain='career' (9 rows). */
const CAREER_VERDICTS = [{ composite_verdict: 'UNRESOLVED', n: 9 }]

/** Every call the handler made, in the order it made them. */
interface Call { sql: string; params: unknown[] }

/**
 * Stands in for the real DB. Routes on the table each of the handler's four queries
 * reads, and — critically — honours the domain join: the verdict query returns the
 * career slice only when the join predicate and its `$2` binding are actually present.
 * A handler that declared `domain` but dropped it would fall through to the all-domain
 * rows and fail the narrowing assertions below.
 */
function installFakeDb(calls: Call[]) {
  vi.mocked(mockQuery).mockReset()
  vi.mocked(mockQuery).mockImplementation((async (sql: string, params: unknown[] = []) => {
    calls.push({ sql, params })
    if (sql.includes('FROM mimamsa_calibration')) {
      const joined = sql.includes('JOIN mimamsa_predictions') && params.length > 1
      return { rows: joined && params[1] === 'career' ? CAREER_VERDICTS : joined ? [] : ALL_DOMAIN_VERDICTS }
    }
    if (sql.includes('FROM mimamsa_multipliers')) {
      // Real shape: this table HAS a domain column, but the writer leaves it NULL
      // (global scope) on this chart — which is why the handler reports multiplier
      // domain coverage as a measured count instead of silently emptying the section.
      return { rows: [{ weight_id: 'w1', domain: null }, { weight_id: 'w2', domain: null }] }
    }
    return { rows: [] }
  }) as never)
}

function verdictCall(calls: Call[]): Call {
  const found = calls.find(c => c.sql.includes('FROM mimamsa_calibration'))
  if (!found) throw new Error('handler never queried mimamsa_calibration')
  return found
}

type Content = Record<string, unknown>

describe('F-27 — query_calibration domain filter (descriptor)', () => {
  it('declares `domain` as an optional input', () => {
    const schema = queryCalibrationCapability.input_schema?.['domain'] as Record<string, unknown> | undefined
    expect(schema, 'domain must be advertised on the capability').toBeDefined()
    expect(schema?.['type']).toBe('string')
    expect(schema?.['required']).toBe(false)
    expect(queryCalibrationCapability.required_inputs).not.toContain('domain')
  })

  it('still passes the chart-agnostic gate with 0 violations', () => {
    const violations = checkCapability(queryCalibrationCapability as CapabilityDescriptor)
    expect(violations, JSON.stringify(violations)).toHaveLength(0)
  })
})

describe('F-27 — query_calibration domain filter (handler)', () => {
  beforeEach(() => {
    vi.mocked(mockQuery).mockReset()
  })

  it('domain=career narrows the verdict rows (57 -> 9) — the filter is NOT a no-op', async () => {
    const calls: Call[] = []
    installFakeDb(calls)

    const withoutDomain = await queryCalibrationCapability.handler({ chart_id: CHART_ID }, undefined)
    const allContent = withoutDomain.content as Content
    expect(withoutDomain.is_error).toBe(false)
    expect(allContent['verdict_row_count']).toBe(57)
    expect(allContent['verdict_distribution']).toHaveLength(4)

    calls.length = 0
    const withDomain = await queryCalibrationCapability.handler(
      { chart_id: CHART_ID, domain: 'career' },
      undefined,
    )
    const careerContent = withDomain.content as Content
    expect(withDomain.is_error).toBe(false)
    expect(careerContent['verdict_row_count']).toBe(9)
    expect(careerContent['verdict_distribution']).toHaveLength(1)

    // The whole point of the finding: the two responses must differ.
    expect(careerContent['verdict_row_count']).not.toBe(allContent['verdict_row_count'])
    expect(JSON.stringify(careerContent['verdict_distribution']))
      .not.toBe(JSON.stringify(allContent['verdict_distribution']))
  })

  it('joins mimamsa_predictions.domain and binds the value as $2', async () => {
    const calls: Call[] = []
    installFakeDb(calls)

    await queryCalibrationCapability.handler({ chart_id: CHART_ID, domain: 'career' }, undefined)

    const call = verdictCall(calls)
    expect(call.sql).toContain('JOIN mimamsa_predictions')
    expect(call.sql).toContain('p.prediction_id = c.prediction_id')
    expect(call.sql).toContain('p.domain')
    expect(call.sql).toContain('$2')
    // Parameterised, never interpolated — the value must arrive as a bind, not in the SQL.
    expect(call.sql).not.toContain("'career'")
    expect(call.params).toEqual([CHART_ID, 'career'])
  })

  it('omitting domain leaves the query unjoined and single-parameter', async () => {
    const calls: Call[] = []
    installFakeDb(calls)

    await queryCalibrationCapability.handler({ chart_id: CHART_ID }, undefined)

    const call = verdictCall(calls)
    // An unconditional join would silently drop any calibration row whose prediction
    // row is missing; "no domain requested" must still mean "every calibration row".
    expect(call.sql).not.toContain('JOIN mimamsa_predictions')
    expect(call.params).toEqual([CHART_ID])
  })

  it('an unmatched domain reports an honest empty, not the unfiltered set', async () => {
    const calls: Call[] = []
    installFakeDb(calls)

    const res = await queryCalibrationCapability.handler(
      { chart_id: CHART_ID, domain: 'no_such_domain' },
      undefined,
    )
    const content = res.content as Content
    expect(content['verdict_distribution']).toEqual([])
    expect(content['verdict_row_count']).toBe(0)
    expect((content['filters'] as Content)['domain']).toBe('no_such_domain')
  })

  it('blank/whitespace domain is treated as "no filter", not as an empty-string filter', async () => {
    for (const blank of ['', '   ']) {
      const calls: Call[] = []
      installFakeDb(calls)

      const res = await queryCalibrationCapability.handler(
        { chart_id: CHART_ID, domain: blank },
        undefined,
      )
      expect(verdictCall(calls).params).toEqual([CHART_ID])
      expect(((res.content as Content)['filters'] as Content)['domain']).toBeNull()
      expect((res.content as Content)['verdict_row_count']).toBe(57)
    }
  })

  it('reports which sections the domain filter did and did not scope (measured, not asserted)', async () => {
    const calls: Call[] = []
    installFakeDb(calls)

    const res = await queryCalibrationCapability.handler(
      { chart_id: CHART_ID, domain: 'career' },
      undefined,
    )
    const filters = (res.content as Content)['filters'] as Content

    expect(filters['domain']).toBe('career')
    expect(filters['domain_filtered_sections']).toEqual(['verdict_distribution'])
    expect(filters['domain_unfiltered_sections'])
      .toEqual(['reliability_curve', 'multipliers', 'qa_results'])
    // §N.8: the reason multipliers are not domain-scoped is a COUNT the handler measures,
    // not a sentence it asserts — a caller can see for itself that the column is unpopulated.
    expect(filters['multipliers_total']).toBe(2)
    expect(filters['multipliers_with_domain']).toBe(0)
  })

  it('the genuine include_held_out / promoted_only filters still work alongside domain', async () => {
    const calls: Call[] = []
    installFakeDb(calls)

    await queryCalibrationCapability.handler(
      { chart_id: CHART_ID, domain: 'career', include_held_out: true, promoted_only: true },
      undefined,
    )

    expect(verdictCall(calls).sql).not.toContain('held_out')
    const multCall = calls.find(c => c.sql.includes('FROM mimamsa_multipliers'))!
    expect(multCall.sql).toContain('gate_passed = true')
  })
})
