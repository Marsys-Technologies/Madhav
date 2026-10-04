/**
 * l2_lineage.test.ts — the N-91 between-state L2 lineage detector (provenance/l2_lineage.ts).
 *
 * Purity tests: the decision is a pure function of the receipt rows (no clock, env or constant),
 * proven by pairs of fixtures that differ ONLY in the pinned/current digest and flip the result.
 * The pin rule: a lineage pin held by an in-scope (proven, active-spec) L2 receipt is stale iff
 * the pinned output_digest differs from the CURRENT L1 receipt's digest (or the L1 asset has no
 * current receipt); observed_at is evidence, never the comparator.
 */
import { describe, it, expect, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import {
  evaluateL2Lineage,
  l2LineageFlag,
  resolveL2Lineage,
  resolveL2LineageFlag,
  L2_LINEAGE_SQL,
  L2_LINEAGE_DETAIL_MAX_BYTES,
  type L2LineageReceiptRow,
  type L2LineagePin,
} from '../l2_lineage'
import { JUDGMENT_FLAG_CODES, isJudgmentFlagCode } from '../../envelope'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const OTHER_CHART = '1c826d5a-0000-4000-8000-000000000000'
const T_OLD = '2026-09-07T08:37:20.895985Z'
const T_NEW = '2026-10-04T10:00:00.000000Z'

function l1(asset_id: string, output_digest: string | null, observed_at: string | Date = T_OLD, over: Partial<L2LineageReceiptRow> = {}): L2LineageReceiptRow {
  return {
    asset_id, chart_id: CHART, partition_key: '__whole_asset__', receipt_state: 'proven',
    observed_at, output_digest, spec_active: true, registry_current: true, l1_pins: null, ...over,
  }
}
function pin(asset_id: string, output_digest: string | null, observed_at: string | null = T_OLD): L2LineagePin {
  return { asset_id, output_digest, observed_at }
}
function l2(asset_id: string, pins: L2LineagePin[], over: Partial<L2LineageReceiptRow> = {}): L2LineageReceiptRow {
  return {
    asset_id, chart_id: CHART, partition_key: '__whole_asset__', receipt_state: 'proven',
    observed_at: '2026-09-08T18:22:33Z', output_digest: 'l2digest', spec_active: true, registry_current: true, l1_pins: pins, ...over,
  }
}

describe('evaluateL2Lineage — the pin rule', () => {
  it('(a) L2 pinned an L1 digest that has since changed -> stale, naming the L2 asset and the L1 asset that moved', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'Y', T_NEW),
      l2('bo_laksana', [pin('ga_structural', 'X', T_OLD)]),
    ], CHART)
    expect(r.state).toBe('stale')
    expect(r.stale).toEqual([{
      l2_asset_id: 'bo_laksana', l2_partition_key: '__whole_asset__', l1_asset_id: 'ga_structural',
      pinned_output_digest: 'X', current_output_digest: 'Y', pinned_observed_at: T_OLD, current_observed_at: T_NEW,
    }])
    expect(r.l1_pins_checked).toBe(1)
  })

  it('(b) current pin (pinned digest equals the current L1 digest) -> current, not stale', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'X'),
      l2('bo_laksana', [pin('ga_structural', 'X')]),
    ], CHART)
    expect(r.state).toBe('current')
    expect(r.stale).toEqual([])
    expect(r.l2_receipts_in_scope).toBe(1)
    expect(r.l1_pins_checked).toBe(1)
  })

  it('(c) equal digest with a NEWER L1 timestamp (a skip_no_delta re-receipt) -> NOT stale: observed_at is evidence, not the comparator', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'X', T_NEW), // L1 observed_at is now far newer than L2 — a literal timestamp rule would fire
      l2('bo_laksana', [pin('ga_structural', 'X', T_OLD)]),
    ], CHART)
    expect(r.state).toBe('current')
    expect(r.stale).toEqual([])
  })

  it('(d) the pinned L1 asset has no current receipt for this chart -> stale (current_output_digest null)', () => {
    const r = evaluateL2Lineage([
      l2('bo_laksana', [pin('ga_structural', 'X')]),
    ], CHART)
    expect(r.state).toBe('stale')
    expect(r.stale[0]).toMatchObject({ l1_asset_id: 'ga_structural', current_output_digest: null, current_observed_at: null })
  })

  it('(e1) legacy `unknown` L2 receipts are ignored even when their pins are stale', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'Y'),
      l2('bo_laksana', [pin('ga_structural', 'X')], { receipt_state: 'unknown' }),
    ], CHART)
    expect(r.state).toBe('not_applicable')
    expect(r.stale).toEqual([])
  })

  it('(e2) retired-spec L2 receipts are ignored even when their pins are stale', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'Y'),
      l2('bo_upaya', [pin('ga_structural', 'X')], { spec_active: false }),
    ], CHART)
    expect(r.state).toBe('not_applicable')
  })

  it('(e3) an ignored legacy receipt does not mask a real stale one, and a current in-scope one does not hide it', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'Y'),
      l2('bo_laksana', [pin('ga_structural', 'Y')]),
      l2('bo_arudha', [pin('ga_structural', 'X')]),
      l2('bo_legacy', [pin('ga_structural', 'Y')], { receipt_state: 'unknown' }),
    ], CHART)
    expect(r.state).toBe('stale')
    expect(r.stale.map(e => e.l2_asset_id)).toEqual(['bo_arudha'])
  })

  it('(g1) registry-superseded L2 receipts are ignored: a retired/renamed asset or a changed partition declaration cannot hold the flag TRUE', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'Y'),
      l2('bo_laksana', [pin('ga_structural', 'Y')]), // the live receipt, current
      l2('bo_laksana', [pin('ga_structural', 'X')], { partition_key: 'old partition text', registry_current: false }), // superseded partition
      l2('bo_retired', [pin('ga_structural', 'X')], { registry_current: false }), // retired / renamed asset
    ], CHART)
    expect(r.state).toBe('current')
    expect(r.stale).toEqual([])
    expect(r.l2_receipts_in_scope).toBe(1)
  })

  it('(g2) only superseded L2 receipts hold stale pins -> not_applicable, not stale', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'Y'),
      l2('bo_retired', [pin('ga_structural', 'X')], { registry_current: false }),
    ], CHART)
    expect(r.state).toBe('not_applicable')
  })

  it('(f1) no L2 receipts at all -> not_applicable (no L2 claim to disclose)', () => {
    expect(evaluateL2Lineage([l1('ga_structural', 'X')], CHART).state).toBe('not_applicable')
    expect(evaluateL2Lineage([], CHART).state).toBe('not_applicable')
  })

  it('(f2) L2 receipts that carry no L1 pin, or only another chart\'s receipts -> not_applicable', () => {
    expect(evaluateL2Lineage([l1('ga_structural', 'X'), l2('bo_laksana', [])], CHART).state).toBe('not_applicable')
    expect(evaluateL2Lineage([
      l1('ga_structural', 'Y'),
      l2('bo_laksana', [pin('ga_structural', 'X')], { chart_id: OTHER_CHART }),
    ], CHART).state).toBe('not_applicable')
  })

  it('pins on non-L1 assets are not lineage pins (only ga_* count)', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'X'),
      l2('bo_arudha', [pin('bo_laksana', 'ANYTHING'), pin('ga_structural', 'X')]),
    ], CHART)
    expect(r.state).toBe('current')
    expect(r.l1_pins_checked).toBe(1)
  })

  it('current L1 = the LATEST-observed receipt per asset (the orchestrator\'s pin rule): an older partition holding the pinned digest does not rescue a stale pin', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'X', T_OLD, { partition_key: 'p_old' }),
      l1('ga_structural', 'Y', T_NEW, { partition_key: 'p_new' }),
      l2('bo_laksana', [pin('ga_structural', 'X')]),
    ], CHART)
    expect(r.state).toBe('stale')
    expect(r.stale[0]).toMatchObject({ pinned_output_digest: 'X', current_output_digest: 'Y' })
  })

  it('a chart-scoped L1 receipt is preferred over a chart-less one even when the chart-less one is newer', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'X', T_OLD),
      l1('ga_structural', 'Z', T_NEW, { chart_id: null }),
      l2('bo_laksana', [pin('ga_structural', 'X')]),
    ], CHART)
    expect(r.state).toBe('current')
  })

  it('null digests compare as equal to each other (IS DISTINCT FROM semantics) and different from a value', () => {
    expect(evaluateL2Lineage([l1('ga_a', null), l2('bo_x', [pin('ga_a', null)])], CHART).state).toBe('current')
    expect(evaluateL2Lineage([l1('ga_a', 'V'), l2('bo_x', [pin('ga_a', null)])], CHART).state).toBe('stale')
    expect(evaluateL2Lineage([l1('ga_a', null), l2('bo_x', [pin('ga_a', 'V')])], CHART).state).toBe('stale')
  })

  it('is a pure function: it is NOT a constant (two fixtures differing only in a digest give opposite states) and is repeatable', () => {
    const rows = (current: string) => [l1('ga_structural', current), l2('bo_laksana', [pin('ga_structural', 'X')])]
    const stale = evaluateL2Lineage(rows('Y'), CHART)
    const fresh = evaluateL2Lineage(rows('X'), CHART)
    expect(stale.state).toBe('stale')
    expect(fresh.state).toBe('current')
    expect(evaluateL2Lineage(rows('Y'), CHART)).toEqual(stale)
    expect(evaluateL2Lineage(rows('X'), CHART)).toEqual(fresh)
  })

  it('the detector source reads no env/config switch (production receipts only)', () => {
    const src = readFileSync(join(__dirname, '..', 'l2_lineage.ts'), 'utf8')
    // strip comments so the header prose cannot satisfy or trip the check
    const code = src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '')
    expect(code).not.toMatch(/process\.env|import\.meta\.env|getenv/)
    expect(L2_LINEAGE_SQL).toContain('asset_provenance_receipts')
    expect(L2_LINEAGE_SQL).toContain('upstream_receipts')
    expect(L2_LINEAGE_SQL).toMatch(/retired_at IS NULL/)
  })
})

describe('resolveL2Lineage — one SELECT, fail closed', () => {
  const sqlRow = (over: Record<string, unknown>) => ({
    asset_id: 'ga_structural', chart_id: CHART, partition_key: '__whole_asset__', receipt_state: 'proven',
    observed_at: new Date(T_OLD), output_digest: 'X', spec_active: true, registry_current: true, l1_pins: null, ...over,
  })

  it('issues exactly one query, parameterised by the chart id, and reads the rows (Date observed_at, jsonb pins)', async () => {
    const calls: Array<[string, unknown[] | undefined]> = []
    const exec = async (sql: string, params?: unknown[]) => {
      calls.push([sql, params])
      return {
        rows: [
          sqlRow({ output_digest: 'Y', observed_at: new Date(T_NEW) }),
          sqlRow({
            asset_id: 'bo_laksana', observed_at: new Date('2026-09-08T18:22:33Z'),
            l1_pins: [{ asset_id: 'ga_structural', output_digest: 'X', observed_at: T_OLD }],
          }),
        ],
      }
    }
    const r = await resolveL2Lineage(CHART, exec)
    expect(calls).toHaveLength(1)
    expect(calls[0]![0]).toBe(L2_LINEAGE_SQL)
    expect(calls[0]![1]).toEqual([CHART])
    expect(r.state).toBe('stale')
    expect(r.stale[0]).toMatchObject({ l2_asset_id: 'bo_laksana', l1_asset_id: 'ga_structural', current_observed_at: new Date(T_NEW).toISOString() })
  })

  it('the same query path reads current when the pin matches (not a constant at the resolver level either)', async () => {
    const exec = async () => ({
      rows: [
        sqlRow({ output_digest: 'X' }),
        sqlRow({ asset_id: 'bo_laksana', l1_pins: [{ asset_id: 'ga_structural', output_digest: 'X', observed_at: T_OLD }] }),
      ],
    })
    expect((await resolveL2Lineage(CHART, exec)).state).toBe('current')
  })

  it('a query error -> state unknown (fail closed), never current/false, and never throws', async () => {
    const r = await resolveL2Lineage(CHART, async () => { throw new Error('permission denied for table asset_provenance_receipts') })
    expect(r.state).toBe('unknown')
    expect(r.error).toContain('permission denied')
    expect(r.state).not.toBe('current')
    expect(l2LineageFlag(r)).toMatchObject({ code: 'l2_lineage_check_failed' })
  })

  it('a malformed result (no row set) -> unknown', async () => {
    const r = await resolveL2Lineage(CHART, async () => ({}) as never)
    expect(r.state).toBe('unknown')
  })

  it('resolveL2LineageFlag returns the flag alongside the result', async () => {
    const stale = await resolveL2LineageFlag(CHART, async () => ({
      rows: [
        sqlRow({ output_digest: 'Y' }),
        sqlRow({ asset_id: 'bo_laksana', l1_pins: [{ asset_id: 'ga_structural', output_digest: 'X', observed_at: T_OLD }] }),
      ],
    }))
    expect(stale.flag).toMatchObject({ code: 'l2_receipts_predate_l1' })
    const fine = await resolveL2LineageFlag(CHART, async () => ({ rows: [] }))
    expect(fine.result.state).toBe('not_applicable')
    expect(fine.flag).toBeNull()
  })
})

describe('l2LineageFlag — the closed-vocabulary flags', () => {
  it('both codes are members of the closed judgment-flag vocabulary', () => {
    expect(isJudgmentFlagCode('l2_receipts_predate_l1')).toBe(true)
    expect(isJudgmentFlagCode('l2_lineage_check_failed')).toBe(true)
    expect(JUDGMENT_FLAG_CODES).toContain('l2_receipts_predate_l1')
    expect(JUDGMENT_FLAG_CODES).toContain('l2_lineage_check_failed')
  })

  it('stale -> l2_receipts_predate_l1 with a SHORT detail: counts and the first three L2 asset names', () => {
    const r = evaluateL2Lineage([
      l1('ga_structural', 'Y', T_NEW),
      l2('bo_laksana', [pin('ga_structural', 'X', T_OLD)]),
      l2('bo_arudha', [pin('ga_structural', 'X', T_OLD)]),
    ], CHART)
    const flag = l2LineageFlag(r)!
    expect(flag.code).toBe('l2_receipts_predate_l1')
    expect(flag.severity).toBe('warning')
    expect(flag.detail).toContain('2 L2 asset(s) (bo_arudha, bo_laksana)')
    expect(flag.detail).toContain('1 L1 asset(s)')
  })

  it('WORST CASE (the S-L1 case: all 8 L2 assets stale, every L1 asset moved): detail stays within the cap and names only three assets', () => {
    const l2Names = ['bo_arudha', 'bo_grounding', 'bo_karanajala', 'bo_laksana', 'bo_nakshatra_semantic', 'bo_special_lagna', 'bo_sudarshana', 'bo_vargottama_dhana']
    const l1Names = ['ga_positions', 'ga_structural', 'ga_vichara', 'ga_vargas', 'ga_yoga', 'ga_strength', 'ga_dashas', 'ga_condition', 'ga_nakshatra', 'ga_panchanga', 'ga_sade_sati', 'ga_sensitive', 'ga_sensitive_degree', 'ga_tajaka', 'ga_ayurdaya', 'ga_medical', 'ga_vastu', 'ga_transit_anchors']
    const rows = [
      ...l1Names.map(n => l1(n, 'NEW', T_NEW)),
      ...l2Names.map(n => l2(n, l1Names.map(m => pin(m, 'OLD', T_OLD)))),
    ]
    const r = evaluateL2Lineage(rows, CHART)
    expect(r.state).toBe('stale')
    expect(r.stale.length).toBe(8 * 18) // evidence is complete in the result; only the SERVED detail is short
    const flag = l2LineageFlag(r)!
    expect(Buffer.byteLength(JSON.stringify(flag), 'utf8')).toBeLessThanOrEqual(L2_LINEAGE_DETAIL_MAX_BYTES + 60) // + code/severity envelope
    expect(Buffer.byteLength(flag.detail!, 'utf8')).toBeLessThanOrEqual(L2_LINEAGE_DETAIL_MAX_BYTES)
    expect(flag.detail).toContain('8 L2 asset(s) (bo_arudha, bo_grounding, bo_karanajala +5 more)')
    expect(flag.detail).toContain('18 L1 asset(s)')
    expect(flag.detail).not.toContain('bo_vargottama_dhana')
    expect(flag.detail).not.toContain(T_OLD)
  })

  it('current and not_applicable -> no flag', () => {
    expect(l2LineageFlag({ state: 'current', stale: [], l2_receipts_in_scope: 1, l1_pins_checked: 1 })).toBeNull()
    expect(l2LineageFlag({ state: 'not_applicable', stale: [], l2_receipts_in_scope: 0, l1_pins_checked: 0 })).toBeNull()
  })

  it('unknown -> l2_lineage_check_failed (fail closed), fixed detail says unknown, not confirmed', () => {
    const flag = l2LineageFlag({ state: 'unknown', stale: [], l2_receipts_in_scope: 0, l1_pins_checked: 0, error: 'boom' })!
    expect(flag.code).toBe('l2_lineage_check_failed')
    expect(flag.detail).toMatch(/UNKNOWN/)
    expect(flag.detail).not.toContain('boom')
  })

  it('the served failure detail never carries the raw driver error; the real error goes to the server log', async () => {
    const raw = 'password authentication failed for user "amjis_app" at 10.0.0.7:5432'
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    try {
      const { result, flag } = await resolveL2LineageFlag(CHART, async () => { throw new Error(raw) })
      expect(result.state).toBe('unknown')
      expect(flag!.code).toBe('l2_lineage_check_failed')
      const served = JSON.stringify(flag)
      expect(served).not.toContain('amjis_app')
      expect(served).not.toContain('10.0.0.7')
      expect(served).not.toContain('password')
      expect(spy).toHaveBeenCalledTimes(1)
      expect(String(spy.mock.calls[0]![0])).toContain('[l2_lineage]')
      expect(spy.mock.calls[0]![1]).toBeInstanceOf(Error)
      expect((spy.mock.calls[0]![1] as Error).message).toBe(raw)
    } finally {
      spy.mockRestore()
    }
  })
})
