/**
 * Tool 27: multi_school_signal_lookup
 * Full implementation M9-D-S1 (2026-05-14). Replaces M9-A stub.
 *
 * Queries school_signal_coverage to report what all 7 Jyotish schools say about a topic.
 * Used by synthesis stage when query involves multi-school comparison.
 */

import 'server-only'
import { query } from '@/lib/db/client'

export interface MultiSchoolSignalLookupInput {
  topic: string
  domains?: string[]  // filter to specific domains: CAREER|HEALTH|RELATIONSHIP|SPIRITUAL|PSYCHOLOGICAL
  schools?: string[]  // filter to specific schools; defaults to all 7
}

export interface PerSchoolSignalResult {
  school: 'parashari' | 'jaimini' | 'tajika' | 'kp' | 'nadi' | 'bnn' | 'yogini'
  coverage_type: 'primary' | 'secondary' | 'silent'
  confidence: number | null
  matching_signals: Array<{
    signal_id: string
    signal_name: string
    domain: string
    attribution_ref?: string
  }>
}

export interface MultiSchoolSignalLookupOutput {
  topic: string
  results_by_school: PerSchoolSignalResult[]
  total_signals_found: number
  schools_with_primary_coverage: string[]
  schools_silent: string[]
}

const ALL_SCHOOLS = ['parashari', 'jaimini', 'tajika', 'kp', 'nadi', 'bnn', 'yogini'] as const
type School = typeof ALL_SCHOOLS[number]

interface SchoolSignalRow {
  school: string
  coverage_type: string
  confidence: string | null
  signal_id: string
  signal_name: string
  domain: string
  attribution_ref: string | null
}

export async function multi_school_signal_lookup(
  input: MultiSchoolSignalLookupInput
): Promise<MultiSchoolSignalLookupOutput> {
  const { topic, domains, schools } = input

  const effectiveSchools: string[] = schools ?? [...ALL_SCHOOLS]
  const params: unknown[] = [`%${topic}%`, effectiveSchools]
  let idx = 3
  const domainCondition = domains && domains.length > 0
    ? `AND msr.domains_affected && $${idx++}::text[]`
    : ''
  if (domains && domains.length > 0) params.push(domains)

  const sql = `
    SELECT
      ssc.school,
      ssc.coverage_type,
      ssc.confidence,
      msr.signal_id,
      msr.name AS signal_name,
      msr.domains_affected[1] AS domain,
      cc.attribution_ref
    FROM school_signal_coverage ssc
    JOIN l25_msr_signals msr ON msr.signal_id = ssc.signal_id
    LEFT JOIN (
      SELECT ssc2.signal_id, ct.text_key || ' §' || cc2.chapter AS attribution_ref
      FROM school_signal_coverage ssc2
      JOIN classical_chunks cc2 ON cc2.id = ssc2.attribution_chunk_id
      JOIN classical_texts ct ON ct.id = cc2.text_id
      WHERE ssc2.attribution_chunk_id IS NOT NULL
    ) cc ON cc.signal_id = ssc.signal_id
    WHERE (
      msr.name ILIKE $1
      OR msr.description ILIKE $1
      OR msr.domains_affected::text ILIKE $1
    )
    AND ssc.school = ANY($2::text[])
    ${domainCondition}
    ORDER BY ssc.school, ssc.coverage_type, ssc.confidence DESC NULLS LAST
  `

  const { rows } = await query<SchoolSignalRow>(sql, params)

  // Group by school
  const bySchool = new Map<School, PerSchoolSignalResult>()

  for (const school of effectiveSchools as School[]) {
    bySchool.set(school, {
      school,
      coverage_type: 'silent',
      confidence: null,
      matching_signals: [],
    })
  }

  for (const row of rows) {
    const school = row.school as School
    const existing = bySchool.get(school)
    if (!existing) continue

    const signal = {
      signal_id: row.signal_id,
      signal_name: row.signal_name,
      domain: row.domain,
      attribution_ref: row.attribution_ref ?? undefined,
    }
    existing.matching_signals.push(signal)

    // Upgrade coverage_type: primary > secondary > silent
    const current = existing.coverage_type
    const incoming = row.coverage_type as 'primary' | 'secondary' | 'silent'
    if (current === 'silent' || (current === 'secondary' && incoming === 'primary')) {
      existing.coverage_type = incoming
      existing.confidence = row.confidence !== null ? Number(row.confidence) : null
    }
  }

  const results_by_school = Array.from(bySchool.values())
  const schools_with_primary_coverage = results_by_school
    .filter(r => r.coverage_type === 'primary')
    .map(r => r.school)
  const schools_silent = results_by_school
    .filter(r => r.coverage_type === 'silent')
    .map(r => r.school)

  return {
    topic,
    results_by_school,
    total_signals_found: rows.length,
    schools_with_primary_coverage,
    schools_silent,
  }
}
