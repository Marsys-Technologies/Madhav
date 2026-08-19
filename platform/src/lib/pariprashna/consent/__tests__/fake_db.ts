/**
 * A tiny in-memory `ConsentDb` for the flag/decision unit tests.
 *
 * It answers only the handful of statement SHAPES `resolve.ts` issues, matched
 * by distinctive substrings, and RECORDS every statement it was asked to run.
 * That recording is what makes "the flag-OFF path never touches the database" a
 * measured claim rather than an assertion: the test reads `calls.length === 0`.
 *
 * Anything the fake does not recognize throws, so a future query added to the
 * resolution path fails loudly here instead of silently returning `{rows: []}`
 * and being read as "no consent row" — which would look like a passing
 * fail-closed test while actually testing nothing.
 */

import type { ChartSubjectRow, ConsentDb, ConsentQueryable, ConsentRow, ExclusionRow } from '../types'

export interface FakeDbSeed {
  chart?: Partial<ChartSubjectRow> | null
  consent?: Partial<ConsentRow> | null
  /** Make the exclusion-register INSERT fail, to exercise `registered: false`. */
  failRegisterWrite?: boolean
}

export interface FakeDb extends ConsentDb {
  calls: string[]
  exclusions: ExclusionRow[]
  cleared: Array<{ chart_id: string; reason: string; cleared_reason: string }>
}

const CHART_DEFAULTS: ChartSubjectRow = {
  id: '482012f1-710e-4a25-994a-93821f5871aa',
  owner_id: 'uid-native',
  role: 'native',
  birth_date: '1984-02-05',
  name: 'Test Subject',
  subject_name: 'Test Subject',
  birth_place: 'Bhubaneswar, Odisha, India',
}

const CONSENT_DEFAULTS: ConsentRow = {
  chart_id: CHART_DEFAULTS.id,
  subject_kind: 'native_self',
  subject_principal_id: 'uid-native',
  guardian_principal_id: null,
  consent_document_ref: null,
  consent_state: 'granted',
  granted_at: '2026-08-19T00:00:00.000Z',
  withdrawn_at: null,
  anonymization_choice: 'anonymous',
  redaction_requests: [],
  vulnerable_exclusion_flag: false,
  verified_deletion_at: null,
  recorded_by_principal_id: 'uid-native',
  created_at: '2026-08-19T00:00:00.000Z',
  updated_at: '2026-08-19T00:00:00.000Z',
}

export function makeFakeDb(seed: FakeDbSeed = {}): FakeDb {
  const chart: ChartSubjectRow | null =
    seed.chart === null ? null : { ...CHART_DEFAULTS, ...(seed.chart ?? {}) }
  const consent: ConsentRow | null =
    seed.consent === null ? null : { ...CONSENT_DEFAULTS, ...(seed.consent ?? {}) }

  const calls: string[] = []
  const exclusions: ExclusionRow[] = []
  const cleared: FakeDb['cleared'] = []

  const query: ConsentQueryable['query'] = async (sql, params = []) => {
    calls.push(sql.replace(/\s+/g, ' ').trim())

    if (sql.includes('FROM charts WHERE id')) {
      return { rows: (chart ? [chart] : []) as never[] }
    }
    if (sql.includes('FROM chart_subject_consent WHERE chart_id')) {
      return { rows: (consent ? [consent] : []) as never[] }
    }
    if (sql.includes('INSERT INTO chart_subject_exclusions')) {
      if (seed.failRegisterWrite) throw new Error('simulated register write failure')
      const row: ExclusionRow = {
        exclusion_id: exclusions.length + 1,
        chart_id: String(params[0]),
        exclusion_reason: params[1] as ExclusionRow['exclusion_reason'],
        detector: String(params[2]),
        subject_age_years: (params[3] ?? null) as number | null,
        evidence: JSON.parse(String(params[4] ?? '{}')),
        detected_at: new Date().toISOString(),
        cleared_at: null,
        cleared_reason: null,
      }
      exclusions.push(row)
      return { rows: [row] as never[] }
    }
    if (sql.includes('UPDATE chart_subject_exclusions')) {
      cleared.push({
        chart_id: String(params[0]),
        reason: String(params[1]),
        cleared_reason: String(params[2]),
      })
      return { rows: [] as never[] }
    }

    throw new Error(`FakeDb: unrecognized statement — ${sql.replace(/\s+/g, ' ').trim()}`)
  }

  return {
    calls,
    exclusions,
    cleared,
    query,
    async withTransaction(fn) {
      return fn({ query })
    },
  }
}
