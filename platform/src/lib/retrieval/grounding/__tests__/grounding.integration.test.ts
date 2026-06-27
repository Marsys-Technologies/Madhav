/**
 * D3 Grounding Spine — Integration Tests (live DB proxy)
 * ================================================================
 * Verifies grounding works against the live DB (localhost:5433).
 * Uses the native chart_id (482012f1-…) as a test fixture — not as a default.
 *
 * These tests use makeLiveDbProxy() and require a running DB.
 * Run with:
 *   INTEGRATION=true DATABASE_URL=... vitest run src/lib/retrieval/grounding/__tests__/grounding.integration.test.ts
 *
 * chart-agnostic: the native chart_id appears only as an explicit fixture argument.
 * All queries are parameterized; no native default fallback anywhere in the spine.
 *
 * Test matrix:
 *   I1 — resolveSignals: signals with resolvable facts resolve correctly to L1 facts
 *   I2 — resolveSignals: §N.5 detection works — orphan fact_ids are surfaced, not hidden
 *   I3 — resolveMetric: computed_salience resolves from a real signal
 *   I4 — resolveMetric: fact_value_num resolves from a real fact
 *   I5 — resolveSignals: empty-on-missing — non-existent signal_id → not_found_signal_ids
 *   I6 — resolveMetric: out-of-vocab metric still rejects even against live DB
 */

import { describe, it, expect, beforeAll } from 'vitest'
import { makeLiveDbProxy } from '../db_proxy'
import { resolveSignals, resolveMetric, assertNoN5Violations } from '../resolver'

// Only run if integration mode is enabled
const INTEGRATION = process.env.INTEGRATION === 'true'

// Native chart used as fixture — parameterized, never a default
const NATIVE_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

// ── Probe the DB to obtain real signal_ids ────────────────────────────────────
//
// We need two sets:
//   - groundableSignalIds: signals whose constituent_facts_array facts exist in chart_facts
//   - orphanSignalIds:     signals whose constituent_facts_array contains orphan fact_ids
//
// This is queried in beforeAll rather than hardcoded, so tests remain correct
// across rebuilds that may change signal_ids.

let groundableSignalIds: string[] = []
let groundableAyanamsha: string = 'lahiri_chitrapaksha'
let orphanSignalIds: string[] = []
let orphanAyanamsha: string = 'lahiri_chitrapaksha'
let firstResolvableFactId: string | null = null
let firstGroundableSignalId: string | null = null

beforeAll(async () => {
  if (!INTEGRATION) return

  const db = makeLiveDbProxy()

  // Find signals that have at least one fact resolvable in chart_facts.
  // Use a JOIN to guarantee the fact actually exists.
  const groundableRows = await db.query<{
    signal_id: string
    ayanamsha_id: string
    fact_id: string
  }>(
    `SELECT DISTINCT s.signal_id, s.ayanamsha_id, f.fact_id
     FROM bodha_msr_signals s
     JOIN chart_facts f ON f.fact_id = ANY(s.constituent_facts_array)
     WHERE s.chart_id = $1
       AND f.chart_id = $1
     ORDER BY s.signal_id
     LIMIT 5`,
    [NATIVE_CHART_ID]
  )

  groundableSignalIds = [...new Set(groundableRows.map(r => r.signal_id))]
  if (groundableRows.length > 0) {
    groundableAyanamsha = groundableRows[0].ayanamsha_id
    firstResolvableFactId = groundableRows[0].fact_id
    firstGroundableSignalId = groundableRows[0].signal_id
  }

  // Find signals that have orphan fact_ids (constituent_facts_array refs not in chart_facts).
  // These are the §N.5 violation cases the spine must detect.
  const orphanRows = await db.query<{
    signal_id: string
    ayanamsha_id: string
    orphan_fact: string
  }>(
    `SELECT s.signal_id, s.ayanamsha_id,
            unnest(s.constituent_facts_array) AS orphan_fact
     FROM bodha_msr_signals s
     WHERE s.chart_id = $1
       AND NOT EXISTS (
         SELECT 1 FROM chart_facts f
         WHERE f.chart_id = $1
           AND f.fact_id = ANY(s.constituent_facts_array)
       )
     LIMIT 3`,
    [NATIVE_CHART_ID]
  )

  orphanSignalIds = [...new Set(orphanRows.map(r => r.signal_id))]
  if (orphanRows.length > 0) {
    orphanAyanamsha = orphanRows[0].ayanamsha_id
  }
})

// ── I1 — Signals with resolvable facts resolve correctly ──────────────────────

describe('I1: resolveSignals — signals with resolvable facts resolve to L1 rows [verify-against: prod]', () => {
  it('resolves signals whose constituent facts exist in chart_facts', async () => {
    if (!INTEGRATION) {
      console.log('[SKIP] Set INTEGRATION=true to run DB integration tests')
      return
    }

    if (groundableSignalIds.length === 0) {
      console.warn('[I1] No groundable signals found in DB — data may need rebuild')
      return
    }

    const db = makeLiveDbProxy()
    const outcome = await resolveSignals(db, NATIVE_CHART_ID, groundableSignalIds)

    expect(outcome.ok).toBe(true)
    if (!outcome.ok) {
      console.error('[I1] grounding failed:', outcome.error)
      return
    }

    const { result } = outcome
    expect(result.signals.length).toBeGreaterThan(0)

    // At least one signal must have resolved facts
    const signalsWithFacts = result.signals.filter(s => s.resolved_facts.length > 0)
    expect(signalsWithFacts.length).toBeGreaterThan(0)

    for (const sig of signalsWithFacts) {
      // Every resolved fact must belong to the same chart — chart isolation enforced
      for (const fact of sig.resolved_facts) {
        expect(fact.chart_id).toBe(NATIVE_CHART_ID)
        expect(fact.fact_id).toBeTruthy()
        expect(fact.citation_ref).toBeTruthy()
        expect(fact.citation_human).toBeTruthy()
        expect(fact.fact_category).toBeTruthy()
      }
    }

    console.log(`[I1] Resolved ${signalsWithFacts.length}/${result.signals.length} signals with L1 facts`)
  })
})

// ── I2 — §N.5 detection: orphan fact_ids are surfaced correctly ───────────────

describe('I2: resolveSignals — §N.5 violation detection works correctly [verify-against: prod]', () => {
  it('detects orphan fact_ids and surfaces them (spine functioning correctly)', async () => {
    if (!INTEGRATION) return

    if (orphanSignalIds.length === 0) {
      console.log('[I2] No orphan-bearing signals found — §N.5 violations may have been resolved in the data')
      return
    }

    const db = makeLiveDbProxy()
    const outcome = await resolveSignals(db, NATIVE_CHART_ID, orphanSignalIds)

    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    // The spine must report the orphans — this is the detector working correctly
    expect(outcome.result.has_n5_violations).toBe(true)
    expect(outcome.result.orphan_fact_count).toBeGreaterThan(0)

    // assertNoN5Violations must surface them as N5_VIOLATION errors
    const violations = assertNoN5Violations(outcome.result)
    expect(violations.length).toBeGreaterThan(0)
    expect(violations.every(v => v.error_code === 'N5_VIOLATION')).toBe(true)

    // Each violation must name the offending signal and fact
    for (const v of violations) {
      expect(v.signal_id).toBeTruthy()
      expect(v.fact_id).toBeTruthy()
      expect(v.message).toContain('§N.5')
    }

    console.log(`[I2] §N.5 detector found ${violations.length} violations (data integrity bugs in DB, spine working correctly)`)
    for (const v of violations) {
      console.log(`  signal=${v.signal_id} orphan_fact=${v.fact_id}`)
    }
  })
})

// ── I3 — computed_salience resolves from a real signal ────────────────────────

describe('I3: resolveMetric — computed_salience from a real signal [verify-against: prod]', () => {
  it('resolves computed_salience for a signal with known data', async () => {
    if (!INTEGRATION) return

    if (!firstGroundableSignalId) {
      console.warn('[I3] No groundable signal_id found — skip')
      return
    }

    const db = makeLiveDbProxy()
    const outcome = await resolveMetric(
      db,
      NATIVE_CHART_ID,
      'computed_salience',
      firstGroundableSignalId
    )

    expect(outcome.ok).toBe(true)
    if (!outcome.ok) {
      console.error('[I3] metric resolution failed:', outcome.error)
      return
    }

    expect(outcome.metric.metric).toBe('computed_salience')
    // Value may be null (computed_salience IS nullable in the schema)
    expect(['number', 'object'].includes(typeof outcome.metric.value) || outcome.metric.value === null).toBe(true)
    expect(outcome.metric.source_table).toBe('bodha_msr_signals')
    expect(outcome.metric.source_id).toBe(firstGroundableSignalId)

    console.log(`[I3] computed_salience = ${outcome.metric.value}`)
  })
})

// ── I4 — fact_value_num resolves from a real chart_fact ──────────────────────

describe('I4: resolveMetric — fact_value_num from a real chart_fact [verify-against: prod]', () => {
  it('resolves fact_value_num for a resolvable fact_id', async () => {
    if (!INTEGRATION) return

    if (!firstResolvableFactId) {
      console.log('[I4] No resolvable fact_id found — skip')
      return
    }

    const db = makeLiveDbProxy()
    const outcome = await resolveMetric(
      db,
      NATIVE_CHART_ID,
      'fact_value_num',
      firstResolvableFactId
    )

    // Resolution must succeed (fact was found via JOIN in beforeAll)
    expect(outcome.ok).toBe(true)
    if (!outcome.ok) {
      console.error('[I4] fact metric resolution failed:', outcome.error)
      return
    }

    expect(outcome.metric.source_table).toBe('chart_facts')
    expect(outcome.metric.source_id).toBe(firstResolvableFactId)
    console.log(`[I4] fact_value_num = ${outcome.metric.value} for fact ${firstResolvableFactId}`)
  })
})

// ── I5 — empty-on-missing: non-existent signal_id ────────────────────────────

describe('I5: resolveSignals — empty-on-missing for non-existent signal [verify-against: prod]', () => {
  it('populates not_found_signal_ids for a signal not in the DB', async () => {
    if (!INTEGRATION) return

    const db = makeLiveDbProxy()
    const nonExistentId = '00000000-0000-0000-0000-000000000000'
    const outcome = await resolveSignals(db, NATIVE_CHART_ID, [nonExistentId])

    expect(outcome.ok).toBe(true)
    if (!outcome.ok) return

    expect(outcome.result.signals).toHaveLength(0)
    expect(outcome.result.not_found_signal_ids).toContain(nonExistentId)
    // No fabricated data — empty, not invented
    expect(outcome.result.has_n5_violations).toBe(false)
    expect(outcome.result.orphan_fact_count).toBe(0)
  })
})

// ── I6 — out-of-vocab metric still rejects against live DB ───────────────────

describe('I6: resolveMetric — out-of-vocab still rejected against live DB [verify-against: prod]', () => {
  it('rejects an out-of-vocabulary metric even with a real signal_id', async () => {
    if (!INTEGRATION) return

    if (!firstGroundableSignalId) {
      console.warn('[I6] No groundable signal_id found — skip')
      return
    }

    const db = makeLiveDbProxy()
    // The vocab check fires before the DB query, so no DB hit needed for this test
    const outcome = await resolveMetric(
      db,
      NATIVE_CHART_ID,
      'invented_metric_xyz',
      firstGroundableSignalId
    )

    expect(outcome.ok).toBe(false)
    if (outcome.ok) return
    expect(outcome.error.error_code).toBe('OUT_OF_VOCAB')
    expect(outcome.error.requested_metric).toBe('invented_metric_xyz')
    expect(outcome.error.message).toContain('governed metric vocabulary')
  })
})
