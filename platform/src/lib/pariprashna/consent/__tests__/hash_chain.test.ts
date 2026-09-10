/**
 * P1 G1-B — the append-only hash chain (PPR-26) and the tombstone digest SQL.
 *
 * The point of these tests is the §N.8 question: "what code path would have to
 * run — and FAIL — for the integrity signal to correctly read false?" Every
 * tamper shape below is that code path, exercised.
 */

import { describe, expect, it } from 'vitest'

import {
  CONSENT_CHAIN_VERSION,
  assertSafeTableIdentifier,
  canonicalJson,
  consentEntryHash,
  tombstoneDigestSql,
  verifyConsentChain,
} from '../hash_chain'
import type { ConsentEventRow } from '../types'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function link(
  seq: number,
  kind: ConsentEventRow['event_kind'],
  prevHash: string | null,
  payload: Record<string, unknown> = {},
): ConsentEventRow {
  const recorded_at = `2026-08-19T10:0${seq}:00.000Z`
  return {
    chart_id: CHART,
    seq,
    event_kind: kind,
    actor_principal_id: 'uid-native',
    payload,
    recorded_at,
    prev_hash: prevHash,
    entry_hash: consentEntryHash({
      chart_id: CHART,
      seq,
      event_kind: kind,
      actor_principal_id: 'uid-native',
      payload,
      recorded_at,
      prev_hash: prevHash,
    }),
  }
}

function buildChain(): ConsentEventRow[] {
  const a = link(1, 'granted', null, { document_ref: 'consent/2026-08-19/native.pdf' })
  const b = link(2, 'anonymization_changed', a.entry_hash, { to: 'attributed' })
  const c = link(3, 'withdrawn', b.entry_hash, { note: null })
  return [a, b, c]
}

describe('canonicalJson', () => {
  it('sorts object keys at every depth so hashing is order-independent', () => {
    expect(canonicalJson({ b: 1, a: { d: 2, c: 3 } })).toBe('{"a":{"c":3,"d":2},"b":1}')
    expect(canonicalJson({ a: { c: 3, d: 2 }, b: 1 })).toBe(canonicalJson({ b: 1, a: { d: 2, c: 3 } }))
  })

  it('preserves array order (an array is data, not a set)', () => {
    expect(canonicalJson([2, 1])).toBe('[2,1]')
    expect(canonicalJson([2, 1])).not.toBe(canonicalJson([1, 2]))
  })

  it('renders null and undefined as null', () => {
    expect(canonicalJson(null)).toBe('null')
    expect(canonicalJson(undefined)).toBe('null')
  })
})

describe('consentEntryHash', () => {
  it('is a 64-hex sha256 and is deterministic', () => {
    const h1 = consentEntryHash({
      chart_id: CHART,
      seq: 1,
      event_kind: 'granted',
      actor_principal_id: null,
      payload: { a: 1, b: 2 },
      recorded_at: '2026-08-19T10:00:00.000Z',
      prev_hash: null,
    })
    const h2 = consentEntryHash({
      chart_id: CHART,
      seq: 1,
      event_kind: 'granted',
      actor_principal_id: null,
      payload: { b: 2, a: 1 }, // key order must not matter
      recorded_at: '2026-08-19T10:00:00.000Z',
      prev_hash: null,
    })
    expect(h1).toMatch(/^[0-9a-f]{64}$/)
    expect(h1).toBe(h2)
  })

  it('changes when ANY hashed field changes', () => {
    const base = {
      chart_id: CHART,
      seq: 1,
      event_kind: 'granted' as const,
      actor_principal_id: 'uid-a',
      payload: { x: 1 },
      recorded_at: '2026-08-19T10:00:00.000Z',
      prev_hash: null,
    }
    const h = consentEntryHash(base)
    expect(consentEntryHash({ ...base, seq: 2 })).not.toBe(h)
    expect(consentEntryHash({ ...base, event_kind: 'withdrawn' })).not.toBe(h)
    expect(consentEntryHash({ ...base, actor_principal_id: 'uid-b' })).not.toBe(h)
    expect(consentEntryHash({ ...base, payload: { x: 2 } })).not.toBe(h)
    expect(consentEntryHash({ ...base, recorded_at: '2026-08-19T10:00:00.001Z' })).not.toBe(h)
    expect(consentEntryHash({ ...base, prev_hash: 'a'.repeat(64) })).not.toBe(h)
  })

  it('the unit separator prevents field-boundary collisions', () => {
    // Without a separator, actor 'ab' + payload starting 'c' would hash the same
    // as actor 'a' + payload starting 'bc'. With 0x1F it cannot.
    const h1 = consentEntryHash({
      chart_id: 'ab',
      seq: 1,
      event_kind: 'granted',
      actor_principal_id: null,
      payload: {},
      recorded_at: 't',
      prev_hash: null,
    })
    const h2 = consentEntryHash({
      chart_id: 'a',
      seq: 1,
      event_kind: 'granted',
      actor_principal_id: null,
      payload: {},
      recorded_at: 'bt',
      prev_hash: null,
    })
    expect(h1).not.toBe(h2)
  })

  it('is versioned, so the convention can change without silently re-validating', () => {
    expect(CONSENT_CHAIN_VERSION).toBe('csc-v1')
  })
})

describe('verifyConsentChain — the detector', () => {
  it('verifies an intact chain and reports how many links it checked', () => {
    const v = verifyConsentChain(buildChain())
    expect(v).toEqual({ ok: true, links_checked: 3, broken_at_seq: null, reason: null })
  })

  it('verifies regardless of the order rows arrive in', () => {
    const chain = buildChain()
    expect(verifyConsentChain([chain[2], chain[0], chain[1]]).ok).toBe(true)
  })

  it('reports an EMPTY chain as vacuous, not as evidence', () => {
    const v = verifyConsentChain([])
    expect(v.ok).toBe(true)
    expect(v.links_checked).toBe(0)
    expect(v.reason).toBe('empty_chain_is_vacuously_intact')
  })

  it('DETECTS an edited payload (the tamper the chain exists to catch)', () => {
    const chain = buildChain()
    chain[1] = { ...chain[1], payload: { to: 'anonymous' } } // silently flipped
    const v = verifyConsentChain(chain)
    expect(v.ok).toBe(false)
    expect(v.broken_at_seq).toBe(2)
    expect(v.reason).toBe('entry_hash_does_not_match_content')
  })

  it('DETECTS an edited actor', () => {
    const chain = buildChain()
    chain[0] = { ...chain[0], actor_principal_id: 'uid-someone-else' }
    expect(verifyConsentChain(chain).reason).toBe('entry_hash_does_not_match_content')
  })

  it('DETECTS a re-hashed row whose parent link no longer matches', () => {
    // The sophisticated tamper: edit the row AND recompute its own hash. The
    // chain still breaks, because the NEXT link's prev_hash no longer matches.
    const chain = buildChain()
    const forged = link(2, 'anonymization_changed', chain[0].entry_hash, { to: 'anonymous' })
    chain[1] = forged
    const v = verifyConsentChain(chain)
    expect(v.ok).toBe(false)
    expect(v.broken_at_seq).toBe(3)
    expect(v.reason).toBe('prev_hash_does_not_match_parent')
  })

  it('DETECTS a deleted middle link', () => {
    const chain = buildChain()
    const v = verifyConsentChain([chain[0], chain[2]])
    expect(v.ok).toBe(false)
    expect(v.reason).toBe('sequence_not_contiguous_from_1')
  })

  it('DETECTS a genesis link that claims a parent', () => {
    const chain = buildChain()
    const bad = { ...chain[0], prev_hash: 'f'.repeat(64) }
    expect(verifyConsentChain([bad]).reason).toBe('genesis_prev_hash_not_null')
  })

  it('DETECTS a chain that does not start at seq 1', () => {
    const chain = buildChain()
    expect(verifyConsentChain([chain[1], chain[2]]).reason).toBe('sequence_not_contiguous_from_1')
  })
})

describe('assertSafeTableIdentifier', () => {
  it('accepts real table names', () => {
    expect(() => assertSafeTableIdentifier('bodha_msr_signals')).not.toThrow()
    expect(() => assertSafeTableIdentifier('_private')).not.toThrow()
  })

  it('rejects anything that could break out of the quoted identifier', () => {
    for (const bad of [
      'bodha"; DROP TABLE charts; --',
      'Bodha_Signals', // uppercase: not a real unquoted pg identifier here
      'public.bodha_signals',
      'bodha signals',
      '1_table',
      '',
      'x'.repeat(64),
    ]) {
      expect(() => assertSafeTableIdentifier(bad)).toThrow(/UNSAFE_TABLE_IDENTIFIER/)
    }
  })
})

describe('tombstoneDigestSql', () => {
  it('quotes the table, binds the chart id, and never selects row bodies', () => {
    const sql = tombstoneDigestSql('bodha_msr_signals')
    expect(sql).toContain('"bodha_msr_signals"')
    expect(sql).toContain('t.chart_id::text = $1')
    expect(sql).toContain('md5(t.*::text)')
    expect(sql).toContain('sha256')
    // The projected columns are only a count and a digest.
    expect(sql).toMatch(/SELECT count\(\*\)::int AS row_count/)
  })

  it('refuses to build SQL for an unsafe identifier', () => {
    expect(() => tombstoneDigestSql('x"; DROP TABLE charts; --')).toThrow(
      /UNSAFE_TABLE_IDENTIFIER/,
    )
  })
})
