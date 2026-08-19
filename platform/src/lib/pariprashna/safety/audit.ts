/**
 * Paripraśna safety — THE AUDIT TRAIL (lane G1-A, PPR-26).
 *
 * PPR-26, verbatim: "Safety decisions, retractions, and consent transitions
 * MUST be written append-only (INSERT-only grant or hash chain). Audit rows
 * MUST reference C1 content by id/hash, never duplicate it."
 *
 * The §7 role migration (the INSERT-only grant) is lane G1-C's work, so this
 * lane takes the hash-chain option — the same choice, for the same reason, that
 * G1-B made for consent transitions. The chaining convention is NOT reinvented:
 * `canonicalJson` and `sha256Hex` are imported from `consent/hash_chain.ts`, so
 * there is one hashing convention in the Paripraśna surface rather than two
 * that can drift (§N.7 item 3 — a constant can drift from its source; a
 * reference cannot).
 *
 * ── WHAT THE CHAIN EARNS ─────────────────────────────────────────────────────
 * `verifySafetyChain` re-derives every link and names the first `seq` that
 * fails. That is the detector that makes "append-only" a measured claim rather
 * than a promise (§N.8): there is a real code path on which the integrity
 * signal reads false. An EMPTY chain reports `ok: true` with the explicit
 * reason `empty_chain_is_vacuously_intact` — it is not evidence of anything and
 * the reason field says so.
 *
 * ── WHAT NEVER ENTERS A ROW ──────────────────────────────────────────────────
 * The question text. Not truncated, not "just the matched bit". Detections
 * carry `matched_span_hash` and a rule id; that is enough to correlate and to
 * debug, and not enough to reconstruct a C1 body out of the audit table.
 */

import { canonicalJson, sha256Hex } from '../consent/hash_chain'
import type { SafetyDecision, SafetyDb, SafetyQueryable } from './types'

export const SAFETY_CHAIN_VERSION = 'psd-v1'

/** 0x1F UNIT SEPARATOR — the same guard the consent chain uses. */
const SEP = ''

export interface SafetyDecisionRow {
  decision_id: string
  chart_id: string
  turn_id: string
  seq: number
  enforced: boolean
  classes_detected: string[]
  severity: string
  action: string
  subject_kind: string | null
  detections: unknown
  evasion_markers: unknown
  excluded_capabilities: string[]
  llm_assist_ran: boolean
  review_id: string | null
  recorded_at: string
  prev_hash: string | null
  entry_hash: string
}

export interface SafetyEntryHashInput {
  chart_id: string
  turn_id: string
  seq: number
  action: string
  severity: string
  classes_detected: string[]
  detections: unknown
  recorded_at: string
  prev_hash: string | null
}

export function safetyEntryHash(input: SafetyEntryHashInput): string {
  const canonical = [
    SAFETY_CHAIN_VERSION,
    input.chart_id,
    input.turn_id,
    String(input.seq),
    input.action,
    input.severity,
    canonicalJson([...input.classes_detected].sort()),
    canonicalJson(input.detections ?? []),
    input.recorded_at,
    input.prev_hash ?? '',
  ].join(SEP)
  return sha256Hex(canonical)
}

export interface SafetyChainVerification {
  ok: boolean
  links_checked: number
  broken_at_seq: number | null
  reason:
    | null
    | 'empty_chain_is_vacuously_intact'
    | 'sequence_not_contiguous_from_1'
    | 'genesis_prev_hash_not_null'
    | 'prev_hash_does_not_match_parent'
    | 'entry_hash_does_not_match_content'
}

export function verifySafetyChain(rows: SafetyDecisionRow[]): SafetyChainVerification {
  const ordered = [...rows].sort((a, b) => a.seq - b.seq)
  if (ordered.length === 0) {
    return { ok: true, links_checked: 0, broken_at_seq: null, reason: 'empty_chain_is_vacuously_intact' }
  }
  let previousHash: string | null = null
  for (let i = 0; i < ordered.length; i++) {
    const r = ordered[i]
    const fail = (reason: SafetyChainVerification['reason']): SafetyChainVerification => ({
      ok: false,
      links_checked: i,
      broken_at_seq: r.seq,
      reason,
    })
    if (r.seq !== i + 1) return fail('sequence_not_contiguous_from_1')
    if (i === 0 && r.prev_hash !== null) return fail('genesis_prev_hash_not_null')
    if (i > 0 && r.prev_hash !== previousHash) return fail('prev_hash_does_not_match_parent')
    const recomputed = safetyEntryHash({
      chart_id: r.chart_id,
      turn_id: r.turn_id,
      seq: r.seq,
      action: r.action,
      severity: r.severity,
      classes_detected: r.classes_detected,
      detections: r.detections,
      recorded_at: r.recorded_at,
      prev_hash: r.prev_hash,
    })
    if (recomputed !== r.entry_hash) return fail('entry_hash_does_not_match_content')
    previousHash = r.entry_hash
  }
  return { ok: true, links_checked: ordered.length, broken_at_seq: null, reason: null }
}

/**
 * Append one `safety_decision` row.
 *
 * Called on EVERY turn the gate runs — proceed included. A safety table that
 * only carries the turns that fired cannot answer "how many readings went out
 * unflagged", which is the denominator every rate in this domain needs.
 *
 * Returns whether the write landed. The caller reports that boolean on the
 * decision (`audit_written`) rather than assuming success — the same honesty
 * the consent lane's `registered` field carries.
 */
export async function appendSafetyDecision(
  db: SafetyDb,
  decision: SafetyDecision,
): Promise<boolean> {
  try {
    await db.withTransaction(async (tx: SafetyQueryable) => {
      // Serialize the chain per chart: the advisory lock makes two concurrent
      // turns on one chart take seq 1 and 2, never both take 1.
      await tx.query(`SELECT pg_advisory_xact_lock(hashtextextended($1, 0))`, [
        `pariprashna_safety:${decision.chart_id}`,
      ])
      const { rows } = await tx.query<{ seq: number; entry_hash: string }>(
        `SELECT seq, entry_hash FROM pariprashna_safety_decisions
          WHERE chart_id = $1 ORDER BY seq DESC LIMIT 1`,
        [decision.chart_id],
      )
      const prev = rows[0] ?? null
      const seq = (prev?.seq ?? 0) + 1
      const prevHash = prev?.entry_hash ?? null
      const recordedAt = decision.decided_at
      const entryHash = safetyEntryHash({
        chart_id: decision.chart_id,
        turn_id: decision.turn_id,
        seq,
        action: decision.action,
        severity: decision.severity,
        classes_detected: decision.classes_detected,
        detections: decision.detections,
        recorded_at: recordedAt,
        prev_hash: prevHash,
      })
      await tx.query(
        `INSERT INTO pariprashna_safety_decisions (
           decision_id, chart_id, turn_id, seq, enforced, classes_detected, severity,
           action, subject_kind, detections, evasion_markers, excluded_capabilities,
           llm_assist_ran, review_id, recorded_at, prev_hash, entry_hash
         ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11::jsonb,$12,$13,$14,$15,$16,$17)`,
        [
          decision.decision_id,
          decision.chart_id,
          decision.turn_id,
          seq,
          decision.enforced,
          decision.classes_detected,
          decision.severity,
          decision.action,
          decision.subject_kind,
          JSON.stringify(decision.detections),
          JSON.stringify(decision.evasion_markers),
          decision.excluded_capabilities,
          decision.llm_assist_ran,
          decision.review_id,
          recordedAt,
          prevHash,
          entryHash,
        ],
      )
    })
    return true
  } catch (err) {
    // The decision STANDS whether or not the row landed — a gate that opened
    // because its logger was down would be the worst possible failure mode.
    // The honest signal is `audit_written: false`, not a swallowed success.
    console.error('[pariprashna/safety] safety_decision audit write failed:', err)
    return false
  }
}

/**
 * Read a chart's chain back in a form `verifySafetyChain` can re-derive.
 *
 * `recorded_at` is rendered with an explicit UTC `to_char` mask rather than
 * `::text`, because the hash was taken over a JavaScript `toISOString()` string
 * and Postgres's default timestamptz text output is NOT that format. Reading it
 * back the lazy way would make every link fail verification and the chain would
 * look tampered-with when nothing had been touched.
 */
export const RECORDED_AT_ISO_SQL = `to_char(recorded_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')`

export async function loadSafetyChain(db: SafetyDb, chartId: string): Promise<SafetyDecisionRow[]> {
  const { rows } = await db.query<SafetyDecisionRow>(
    `SELECT decision_id, chart_id, turn_id, seq, enforced, classes_detected, severity,
            action, subject_kind, detections, evasion_markers, excluded_capabilities,
            llm_assist_ran, review_id, ${RECORDED_AT_ISO_SQL} AS recorded_at, prev_hash, entry_hash
       FROM pariprashna_safety_decisions WHERE chart_id = $1 ORDER BY seq ASC`,
    [chartId],
  )
  return rows
}
