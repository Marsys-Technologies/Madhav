/**
 * A counting in-memory `SafetyDb` double.
 *
 * It counts CALLS, not just rows, because "flag OFF touches no database" is a
 * claim about calls and the only honest way to assert it is to count them —
 * the same discipline G1-B's consent tests used for the same claim.
 */

import type { SafetyDb, SafetyQueryable } from '../types'

export interface FakeSafetyDb extends SafetyDb {
  calls: string[]
  rows: Record<string, Record<string, unknown>[]>
  /** Make the next N queries throw, to exercise the audit-failure path. */
  failNext: number
}

export function makeFakeSafetyDb(): FakeSafetyDb {
  const rows: Record<string, Record<string, unknown>[]> = {}
  const db: FakeSafetyDb = {
    calls: [],
    rows,
    failNext: 0,
    async query(sql: string, params?: unknown[]) {
      db.calls.push(sql.trim().split('\n')[0].trim())
      if (db.failNext > 0) {
        db.failNext -= 1
        throw new Error('FAKE_DB_FAILURE')
      }
      return runFake(rows, sql, params ?? [])
    },
    async withTransaction<T>(fn: (tx: SafetyQueryable) => Promise<T>): Promise<T> {
      db.calls.push('BEGIN')
      const tx: SafetyQueryable = {
        async query(sql: string, params?: unknown[]) {
          db.calls.push(sql.trim().split('\n')[0].trim())
          if (db.failNext > 0) {
            db.failNext -= 1
            throw new Error('FAKE_DB_FAILURE')
          }
          return runFake(rows, sql, params ?? [])
        },
      }
      const out = await fn(tx)
      db.calls.push('COMMIT')
      return out
    },
  }
  return db
}

/** A deliberately tiny SQL interpreter: only the shapes this lane issues. */
async function runFake<T>(
  rows: Record<string, Record<string, unknown>[]>,
  sql: string,
  params: unknown[],
): Promise<{ rows: T[] }> {
  const s = sql.replace(/\s+/g, ' ').trim()

  if (s.startsWith('SELECT pg_advisory_xact_lock')) return { rows: [] as T[] }

  if (s.startsWith('SELECT seq, entry_hash FROM pariprashna_safety_decisions')) {
    const chartId = params[0]
    const all = (rows.pariprashna_safety_decisions ?? []).filter((r) => r.chart_id === chartId)
    all.sort((a, b) => (b.seq as number) - (a.seq as number))
    return { rows: (all[0] ? [all[0]] : []) as T[] }
  }

  if (s.startsWith('INSERT INTO pariprashna_safety_decisions')) {
    const [
      decision_id, chart_id, turn_id, seq, enforced, classes_detected, severity, action,
      subject_kind, detections, evasion_markers, excluded_capabilities, llm_assist_ran,
      review_id, recorded_at, prev_hash, entry_hash,
    ] = params
    ;(rows.pariprashna_safety_decisions ??= []).push({
      decision_id, chart_id, turn_id, seq, enforced, classes_detected, severity, action,
      subject_kind,
      detections: JSON.parse(detections as string),
      evasion_markers: JSON.parse(evasion_markers as string),
      excluded_capabilities, llm_assist_ran, review_id, recorded_at, prev_hash, entry_hash,
    })
    return { rows: [] as T[] }
  }

  if (s.startsWith('INSERT INTO pariprashna_safety_reviews')) {
    const [review_id, chart_id, turn_id, state, classes, subject_kind, opened_at] = params
    ;(rows.pariprashna_safety_reviews ??= []).push({
      review_id, chart_id, turn_id, state, classes, subject_kind, opened_at,
      signed_off_by: null, signed_off_at: null, withheld_reason: null,
    })
    return { rows: [] as T[] }
  }

  if (s.startsWith('INSERT INTO pariprashna_safety_review_events')) {
    ;(rows.pariprashna_safety_review_events ??= []).push({ params })
    return { rows: [] as T[] }
  }

  if (s.startsWith('INSERT INTO pariprashna_safety_notifications')) {
    const [notification_id, chart_id, turn_id, decision_id, reason, recorded_at] = params
    ;(rows.pariprashna_safety_notifications ??= []).push({
      notification_id, chart_id, turn_id, decision_id, reason, state: 'pending', recorded_at,
    })
    return { rows: [] as T[] }
  }

  if (s.startsWith('INSERT INTO pariprashna_predictive_samples')) {
    const [sample_id, chart_id, turn_id, n, receipt_hash, safety_classes, sampled_at] = params
    ;(rows.pariprashna_predictive_samples ??= []).push({
      sample_id, chart_id, turn_id, prediction_candidate_count: n, receipt_hash,
      safety_classes, state: 'pending_review', sampled_at, reviewed_at: null,
      red_team_artifact_ref: null,
    })
    return { rows: [] as T[] }
  }

  if (s.startsWith('SELECT decision_id, chart_id, turn_id, seq')) {
    const chartId = params[0]
    const all = (rows.pariprashna_safety_decisions ?? []).filter((r) => r.chart_id === chartId)
    all.sort((a, b) => (a.seq as number) - (b.seq as number))
    return { rows: all as T[] }
  }

  throw new Error(`FAKE_DB: unhandled SQL shape: ${s.slice(0, 90)}`)
}
