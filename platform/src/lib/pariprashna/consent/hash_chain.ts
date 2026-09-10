/**
 * Paripraśna consent — HASH CHAIN + TOMBSTONE HASHING (PPR-26).
 *
 * "Safety decisions, retractions, and consent-state transitions are written
 * under an INSERT-only grant (part of the §7 role migration) or hash-chained — a
 * safety gate whose firing record is editable under the serving credential is
 * not 'never invisible.'" The §7 role migration is a different lane, so this
 * lane takes the hash-chain option.
 *
 * The hashing convention is the codebase's existing one, not a new invention:
 *   · version tag first, then an ordered field list, joined —
 *     `platform/src/lib/lel/prospective_ledger.ts`
 *   · a unit-separator (0x1F) between fields so "ab|c" and "a|bc" cannot
 *     collide — `platform/python-sidecar/services/w2g/fingerprint.py`
 *   · sha256 hex — `platform/supabase/migrations/492_kala_field_core.sql`
 *
 * `verifyConsentChain` is the DETECTOR that earns the append-only claim
 * (CLAUDE.md §N.8): it re-derives every link and names the first seq that fails,
 * so there is a real code path on which the integrity signal reads false.
 */

import { createHash } from 'node:crypto'

import type { ConsentEventKind, ConsentEventRow } from './types'

export const CONSENT_CHAIN_VERSION = 'csc-v1'

/** 0x1F UNIT SEPARATOR — a byte that cannot appear in the canonical JSON. */
const SEP = '\u001f'

/** Deterministic JSON: object keys sorted at every depth, arrays kept in order. */
export function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value ?? null)
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`
  const obj = value as Record<string, unknown>
  const keys = Object.keys(obj).sort()
  return `{${keys.map((k) => `${JSON.stringify(k)}:${canonicalJson(obj[k])}`).join(',')}}`
}

export function sha256Hex(input: string): string {
  return createHash('sha256').update(input, 'utf8').digest('hex')
}

export interface ConsentEntryHashInput {
  chart_id: string
  seq: number
  event_kind: ConsentEventKind
  actor_principal_id: string | null
  payload: Record<string, unknown>
  recorded_at: string
  prev_hash: string | null
}

/**
 * The entry hash of one consent-transition link.
 *
 * NOTE what is NOT in here: nothing that duplicates C1 content. `payload` is
 * caller-supplied and callers must keep it to ids/refs/enums — §5's safe-logging
 * rule ("audit logs reference content by hash/id, never duplicate C1 bodies").
 */
export function consentEntryHash(input: ConsentEntryHashInput): string {
  const canonical = [
    CONSENT_CHAIN_VERSION,
    input.chart_id,
    String(input.seq),
    input.event_kind,
    input.actor_principal_id ?? '',
    canonicalJson(input.payload ?? {}),
    input.recorded_at,
    input.prev_hash ?? '',
  ].join(SEP)
  return sha256Hex(canonical)
}

export interface ChainVerification {
  ok: boolean
  links_checked: number
  /** The first `seq` whose link does not verify; null when the chain is intact. */
  broken_at_seq: number | null
  reason:
    | null
    | 'empty_chain_is_vacuously_intact'
    | 'sequence_not_contiguous_from_1'
    | 'genesis_prev_hash_not_null'
    | 'prev_hash_does_not_match_parent'
    | 'entry_hash_does_not_match_content'
}

/**
 * Re-derive every link of a chart's consent chain.
 *
 * An EMPTY chain is reported `ok: true` with the explicit reason
 * `empty_chain_is_vacuously_intact` — it is not evidence of anything, and the
 * reason field says so rather than letting a bare `true` imply verification of
 * something that was never checked.
 */
export function verifyConsentChain(events: ConsentEventRow[]): ChainVerification {
  const ordered = [...events].sort((a, b) => a.seq - b.seq)
  if (ordered.length === 0) {
    return {
      ok: true,
      links_checked: 0,
      broken_at_seq: null,
      reason: 'empty_chain_is_vacuously_intact',
    }
  }

  let previousHash: string | null = null
  for (let i = 0; i < ordered.length; i++) {
    const e = ordered[i]
    const fail = (reason: ChainVerification['reason']): ChainVerification => ({
      ok: false,
      links_checked: i,
      broken_at_seq: e.seq,
      reason,
    })

    if (e.seq !== i + 1) return fail('sequence_not_contiguous_from_1')
    if (i === 0 && e.prev_hash !== null) return fail('genesis_prev_hash_not_null')
    if (i > 0 && e.prev_hash !== previousHash) return fail('prev_hash_does_not_match_parent')

    const recomputed = consentEntryHash({
      chart_id: e.chart_id,
      seq: e.seq,
      event_kind: e.event_kind,
      actor_principal_id: e.actor_principal_id,
      payload: e.payload,
      recorded_at: e.recorded_at,
      prev_hash: e.prev_hash,
    })
    if (recomputed !== e.entry_hash) return fail('entry_hash_does_not_match_content')

    previousHash = e.entry_hash
  }

  return { ok: true, links_checked: ordered.length, broken_at_seq: null, reason: null }
}

// ── Tombstone content hashing ────────────────────────────────────────────────

/**
 * SQL that measures a chart's rows in one table WITHOUT reading their content
 * back into the application: the per-row `md5(t.*::text)` digests are sorted and
 * folded into a single sha256. The application only ever sees a count and a
 * 64-hex digest, so the tombstone proves WHAT was deleted while retaining none
 * of it (§4 — "a tombstone hash so audit integrity survives content deletion";
 * §5 — "audit logs reference content by hash/id, never duplicate C1 bodies").
 *
 * `tableName` MUST already have passed `assertSafeTableIdentifier`; it is
 * interpolated, because a table name cannot be a bind parameter.
 */
export function tombstoneDigestSql(tableName: string): string {
  assertSafeTableIdentifier(tableName)
  return `
    SELECT count(*)::int AS row_count,
           encode(
             sha256(convert_to(coalesce(string_agg(d, '' ORDER BY d), ''), 'UTF8')),
             'hex'
           ) AS content_hash
      FROM (SELECT md5(t.*::text) AS d FROM "${tableName}" t WHERE t.chart_id::text = $1) s
  `
}

const SAFE_IDENTIFIER_RE = /^[a-z_][a-z0-9_]*$/

/**
 * Table names in the deletion sweep come from `information_schema`, not from a
 * request — but they are string-interpolated into DDL-shaped SQL, so they are
 * re-checked here anyway. Defense that only holds because of where the value
 * came from is not defense.
 */
export function assertSafeTableIdentifier(tableName: string): void {
  if (!SAFE_IDENTIFIER_RE.test(tableName) || tableName.length > 63) {
    throw new Error(`UNSAFE_TABLE_IDENTIFIER: ${JSON.stringify(tableName)}`)
  }
}
