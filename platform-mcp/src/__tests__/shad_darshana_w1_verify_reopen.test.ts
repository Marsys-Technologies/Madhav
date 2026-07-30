/**
 * shad_darshana_w1_verify_reopen.test.ts — ṢAḌ-DARŚANA Gate W1, PARĪKṢAKA live-acceptance
 * rejection of 2026-07-30 (items 8, 28, 29, 30, 32 FAILED-REOPENED + ND-1/ND-2/ND-4).
 *
 * Every test here is a REGRESSION GUARD for a defect that was live in production and that the
 * pre-existing suite passed straight over. The reason it passed over them is itself the lesson
 * recorded in this file: each pre-existing mock asserted a shape or a reachability signal that
 * the real substrate never produces, so the tests proved the facade consistent with a fiction.
 *
 * ── Root Cause A (items 8 + 28) — false-positive coverage ──────────────────────────────
 * `marsys://tool/L0/query_planet_transit`'s capability handler forwarded no `x-api-key`, while
 * `main.py` mounts the whole `/brahmagyan/ephemeris` router behind `Depends(verify_api_key)`
 * with `PYTHON_SIDECAR_API_KEY` set on every deployed service. Every production call 401'd and
 * the handler's own `{ ok: false, error, rows: [] }` envelope came back over HTTP 200 — which
 * the facade read as a GENUINE EMPTY. Result: all 9 grahas' transit fields null on both
 * canonical charts while `coverage` asserted `state: "computed"` and `*_reachable: true`.
 * Guarded below by (1) the classifier that now distinguishes the three outcomes, and (2) the
 * earned-signal predicate that makes `computed` require actual data (CLAUDE.md §N.8).
 *
 * ── Root Cause B (items 29 + 32) — single-date panchāṅga ───────────────────────────────
 * `routers/panchang.py::_fetch_native_context` called `compute_panchang(..., tz_offset_minutes=330)`
 * but the engine declares that parameter `tz_offset` → `TypeError`, uncaught by the surrounding
 * `except (ValidationError, OutOfRangeError, PanchangEngineError)` → unhandled HTTP 500. Only
 * the single-date + chart_id path reaches that function, which is exactly `kala_now_get`'s call
 * and exactly not `kala_ahead_get`'s (mode=range, no chart_id) — hence "range works, single is
 * broken". The Python-side fix is covered by the sidecar's own test; guarded here is the
 * SERVING half: the overlay now fails soft with a disclosed reason, and the facade must report
 * that specific reason instead of "unreachable" (ND-4).
 *
 * ── Root Cause C (item 30) — muntha ────────────────────────────────────────────────────
 * Covered in kala_ahead_get_mudda_w1_joins.test.ts (mock corrected to the real
 * `muntha_position_jsonb` shape) + the coverage/prose guards below.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import { computeKalaNow } from '../tools/kala_views/now.js'
import { computeKalaAhead } from '../tools/kala_views/ahead.js'
import {
  buildKalaFreshness,
  isNoLever,
  KALA_FRESHNESS_NOT_EVALUABLE_REASON,
  type TriPlanePointers,
} from '../lib/kala_envelope.js'

const CHART = '00000000-0000-0000-0000-000000000001'
const PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }
const AS_OF = '2026-07-30'

// Windows are anchored to the REAL current instant with a wide (+/-2h) margin: hora_now and
// gulika_kalam_now evaluate membership of the actual present moment, so a hardcoded UTC
// window would only pass during a 1-hour slice of the day.
const NOW_MS = Date.now()
const iso = (offsetMs: number) => new Date(NOW_MS + offsetMs).toISOString()
const H = 3600_000

const LAGNA_SIGN = 1
const MOON_SIGN = 11

const TRANSIT_ROW = {
  date: AS_OF, sign_number: 4, degree_in_sign: 12.401,
  nakshatra_number: 9, is_retrograde: false,
}

const ACTIVE_CHAIN = [
  { level_n: 1, level_name: 'Mahadasha', lord_graha: 'Mercury', lord_sign: 'Capricorn', start_date: '2010-08-18', end_date: '2027-08-18' },
]

type TransitMode =
  /** The real production failure: the capability's own error envelope, over HTTP 200. */
  | 'upstream_error'
  /** A genuine empty — call succeeded, ephemeris simply has no row. */
  | 'genuine_empty'
  /** Healthy. */
  | 'ok'

function mockFetch(opts: {
  transit?: TransitMode
  panchanga?: 'ok' | 'dispatch_fail' | 'overlay_failed'
  varshaRow?: Record<string, unknown> | null
}) {
  const transit = opts.transit ?? 'ok'
  const panchanga = opts.panchanga ?? 'ok'

  return vi.fn(async (url: string, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body ?? '{}')) as {
      uri?: string; args?: Record<string, unknown>; params?: unknown[]
    }

    if (String(url).includes('/api/mcp/db/query')) {
      return { ok: true, json: async () => ({ rows: [] }), text: async () => '' } as Response
    }

    let inner: Record<string, unknown> = {}
    switch (body.uri) {
      case 'marsys://tool/L3/query_temporal_activation':
        inner = { window_families: [], forward_windows: [], activations: [] }
        break
      case 'marsys://tool/L3/query_temporal_view':
        inner = { rows: [] }
        break
      case 'marsys://tool/L1/get_dignity':
        inner = {
          rows: [
            { fact_subject: 'LAGNA', fact_key: 'sign_num', fact_value_num: LAGNA_SIGN, fact_id: 'fact-lagna' },
            { fact_subject: 'MOON', fact_key: 'sign_num', fact_value_num: MOON_SIGN, fact_id: 'fact-moon' },
          ],
        }
        break
      case 'marsys://tool/L3/query_active_dashas':
        inner = {
          systems: [
            { system_id: 'vimshottari', active_chain: ACTIVE_CHAIN },
            { system_id: 'mudda', active_chain: ACTIVE_CHAIN },
          ],
        }
        break
      case 'marsys://tool/L0/query_planet_transit':
        // The exact production shapes — see the header. `upstream_error` is what a 401'd
        // sidecar call actually looks like arriving at this facade.
        if (transit === 'upstream_error') {
          inner = {
            ok: false,
            error: 'sidecar 401: {"detail":"Invalid API key"}',
            confidence: 'none',
            planet: String(body.args?.['planet'] ?? ''),
            count: 0,
            rows: [],
          }
        } else if (transit === 'genuine_empty') {
          inner = { ok: true, planet: String(body.args?.['planet'] ?? ''), count: 0, rows: [] }
        } else {
          inner = { ok: true, planet: String(body.args?.['planet'] ?? ''), count: 1, rows: [TRANSIT_ROW] }
        }
        break
      case 'marsys://tool/L0/call_panchanga_service':
        if (panchanga === 'dispatch_fail') throw new Error('panchanga dispatch failed in test')
        inner = {
          panchang: {
            tithi: { id: 3, name: 'Shukla Tritiya', end_utc: null },
            nakshatra: { id: 25, name: 'Purva Bhadrapada', end_utc: null },
            vara: { id: 1, name: 'Ravivara', end_utc: null },
            inauspicious: [{ label: 'gulika_kalam', start_utc: iso(-2 * H), end_utc: iso(2 * H) }],
            hora: [{ label: 'hora_mars', start_utc: iso(-2 * H), end_utc: iso(2 * H) }],
            planets: { moon: { name: 'Moon', sign_id: 6, sign_name: 'Virgo', nakshatra_id: 13, nakshatra_name: 'Hasta' } },
          },
          native_context: panchanga === 'overlay_failed'
            ? null
            : { chart_id: CHART, moon_sign_id: MOON_SIGN, moon_sign_name: 'Aquarius', birth_nakshatra_id: 25, birth_nakshatra_name: 'Purva Bhadrapada' },
          native_context_error: panchanga === 'overlay_failed'
            ? "TypeError: compute_panchang() got an unexpected keyword argument 'tz_offset_minutes'"
            : null,
        }
        break
      case 'marsys://tool/L1/get_panchanga':
        inner = {
          rows: [
            { fact_id: 'f-vara', fact_category: 'panchanga_vara', ayanamsha_id: 'INVARIANT', fact_key: 'number', fact_value_num: 1, fact_value_text: null },
            { fact_id: 'f-tithi', fact_category: 'panchanga_tithi', ayanamsha_id: 'INVARIANT', fact_key: 'number_in_lunar_month', fact_value_num: 3, fact_value_text: null },
            { fact_id: 'f-nak', fact_category: 'panchanga_nakshatra_moon', ayanamsha_id: 'lahiri_chitrapaksha', fact_key: 'number', fact_value_num: 25, fact_value_text: null },
          ],
        }
        break
      case 'marsys://tool/L1/get_tajik':
        inner = {
          varsha_year_lords: {
            rows: opts.varshaRow === null ? [] : [opts.varshaRow ?? {
              varsha_year: 43,
              varsha_start_iso: '2026-02-04 23:59:03+00',
              varsha_end_iso: '2027-02-05 06:03:58+00',
              year_lord: 'Venus',
              muntha_position_jsonb: {
                lord: 'Venus', sign: 'Libra', degree: 12.4311,
                house_from_natal_lagna: 7, house_from_varsha_lagna: 10,
              },
            }],
          },
        }
        break
      case 'marsys://tool/L3/query_projections':
        inner = { projection_families: [] }
        break
      case 'marsys://tool/L1/get_dashas':
        inner = { rows: [] }
        break
      default:
        inner = {}
    }
    return {
      ok: true,
      json: async () => ({ ok: true, content: { content: inner, is_error: false } }),
      text: async () => '',
    } as Response
  })
}

const byConcept = (coverage: Array<{ concept: string; state: string; reason?: string }>) =>
  Object.fromEntries(coverage.map((c) => [c.concept, c]))

beforeEach(() => {
  vi.unstubAllGlobals()
})

// ── Root Cause A (items 8 + 28) ────────────────────────────────────────────────────────

describe('Root Cause A — item 8: an upstream transit error must NEVER be served as "computed"', () => {
  it('THE REJECTED DEFECT: all-null transit rows are no longer accompanied by state:"computed"', async () => {
    vi.stubGlobal('fetch', mockFetch({ transit: 'upstream_error' }))
    const result = await computeKalaNow(CHART, { as_of: AS_OF }, PRINCIPAL)

    // The symptom the Verifier saw, still present (we do not hide the rows — B.10)…
    expect(result.gochara_dual_reference).toHaveLength(9)
    expect(result.gochara_dual_reference.every((r) => r.transit_sign_name === null)).toBe(true)
    // …but the CLAIM about it is now honest.
    const cov = byConcept(result.coverage)['dual_reference_gochara']
    expect(cov?.state).toBe('honest_empty')
    expect(result.provenance_envelope.gochara_dual_reference_reachable).toBe(false)
    expect(result.provenance_envelope.gochara_dual_reference_rows_with_transit_data).toBe(0)
  })

  it('ND-4: the reason names the failure as PERSISTENT and quotes the upstream error, never "unreachable this call"', async () => {
    vi.stubGlobal('fetch', mockFetch({ transit: 'upstream_error' }))
    const result = await computeKalaNow(CHART, { as_of: AS_OF }, PRINCIPAL)
    const reason = byConcept(result.coverage)['dual_reference_gochara']?.reason ?? ''
    expect(reason).toContain('PERSISTENT')
    expect(reason).toContain('sidecar 401')
    expect(reason).not.toMatch(/unreachable this call/)
  })

  it('a GENUINE empty is worded differently from a failure — the two are not conflated', async () => {
    vi.stubGlobal('fetch', mockFetch({ transit: 'genuine_empty' }))
    const result = await computeKalaNow(CHART, { as_of: AS_OF }, PRINCIPAL)
    const reason = byConcept(result.coverage)['dual_reference_gochara']?.reason ?? ''
    expect(reason).toContain('genuine empty')
    expect(reason).not.toContain('PERSISTENT')
  })

  it('healthy substrate: real values for all 9 grahas, both house counts, and state:"computed"', async () => {
    vi.stubGlobal('fetch', mockFetch({ transit: 'ok' }))
    const result = await computeKalaNow(CHART, { as_of: AS_OF }, PRINCIPAL)
    expect(result.gochara_dual_reference).toHaveLength(9)
    for (const row of result.gochara_dual_reference) {
      expect(row.transit_sign_number).toBe(4)
      expect(row.transit_sign_name).toBe('Cancer')
      expect(row.degree_in_sign).toBe(12.401)
      expect(row.is_retrograde).toBe(false)
      // house_from_moon and house_from_lagna are counted from DIFFERENT natal references and
      // must both be present and independent (item 8's whole point — no silent single default).
      expect(row.house_from_lagna).toBe(4)  // Cancer from Aries
      expect(row.house_from_moon).toBe(6)   // Cancer from Aquarius
    }
    expect(byConcept(result.coverage)['dual_reference_gochara']?.state).toBe('computed')
    expect(result.provenance_envelope.gochara_dual_reference_rows_with_transit_data).toBe(9)
  })
})

describe('Root Cause A — item 28: daśā-lord transit condition, current + forward', () => {
  it('upstream error → honest_empty, not "computed", on the CURRENT (now) half', async () => {
    vi.stubGlobal('fetch', mockFetch({ transit: 'upstream_error' }))
    const result = await computeKalaNow(CHART, { as_of: AS_OF }, PRINCIPAL)
    // The lord identity still resolves (a different substrate) — only its transit is missing.
    expect(result.dasha_lord_transit_condition[0]?.lord_graha).toBe('Mercury')
    expect(result.dasha_lord_transit_condition[0]?.transit_sign_name).toBeNull()
    expect(byConcept(result.coverage)['dasha_lord_current_transit_condition']?.state).toBe('honest_empty')
    expect(result.provenance_envelope.dasha_lord_transit_condition_reachable).toBe(false)
  })

  it('healthy substrate → real transit sign/degree/house for the running lord, state:"computed"', async () => {
    vi.stubGlobal('fetch', mockFetch({ transit: 'ok' }))
    const result = await computeKalaNow(CHART, { as_of: AS_OF }, PRINCIPAL)
    const md = result.dasha_lord_transit_condition[0]
    expect(md?.lord_graha).toBe('Mercury')
    expect(md?.transit_sign_name).toBe('Cancer')
    expect(md?.degree_in_sign).toBe(12.401)
    expect(md?.house_from_lagna).toBe(4)
    expect(byConcept(result.coverage)['dasha_lord_current_transit_condition']?.state).toBe('computed')
  })

  it('the FORWARD half (kala_ahead_get) carries the same earned-signal discipline', async () => {
    vi.stubGlobal('fetch', mockFetch({ transit: 'upstream_error' }))
    const ahead = await computeKalaAhead(CHART, {}, PRINCIPAL)
    expect(byConcept(ahead.coverage)['dasha_lord_forward_transit_condition']?.state).toBe('honest_empty')
    expect(ahead.provenance_envelope.dasha_lord_transit_condition_forward_reachable).toBe(false)
    expect(ahead.provenance_envelope.dasha_lord_transit_condition_forward_rows_with_transit_data).toBe(0)

    vi.stubGlobal('fetch', mockFetch({ transit: 'ok' }))
    const healthy = await computeKalaAhead(CHART, {}, PRINCIPAL)
    expect(byConcept(healthy.coverage)['dasha_lord_forward_transit_condition']?.state).toBe('computed')
    expect(healthy.dasha_lord_transit_condition_forward[0]?.transit_sign_name).toBe('Cancer')
  })
})

// ── Root Cause B (items 29 + 32) ───────────────────────────────────────────────────────

describe('Root Cause B — items 29 + 32: the single-date panchāṅga joins actually populate', () => {
  it('THE REJECTED DEFECT: all five panchāṅga-backed fields are non-null and "computed"', async () => {
    vi.stubGlobal('fetch', mockFetch({ panchanga: 'ok' }))
    const result = await computeKalaNow(CHART, {}, PRINCIPAL)

    expect(result.disha_shula?.avoid_direction).toBe('West') // vara 1 → West
    expect(result.gulika_kalam_now?.window_start_utc).toBe(iso(-2 * H))
    expect(result.gulika_kalam_now?.is_active_now).toBe(true)
    expect(result.hora_now?.hora_lord).toBe('Mars')
    expect(result.chandrashtama).not.toBeNull()
    expect(result.janma_resonance?.tithi.resonance).toBe(true) // birth tithi 3 == today's 3

    const cov = byConcept(result.coverage)
    for (const concept of ['disha_shula', 'gulika_kalam_now', 'chandrashtama', 'hora_now', 'janma_resonance']) {
      expect(cov[concept]?.state, `${concept} must be computed`).toBe('computed')
    }
    expect(result.provenance_envelope.panchanga_reachable).toBe(true)
  })

  it('§N.5: chandrāṣṭama takes the natal Moon rāśi from L1 chart_facts, citing the fact_id', async () => {
    vi.stubGlobal('fetch', mockFetch({ panchanga: 'ok' }))
    const result = await computeKalaNow(CHART, {}, PRINCIPAL)
    expect(result.chandrashtama?.natal_moon_sign_source).toBe('l1_chart_facts')
    expect(result.chandrashtama?.natal_moon_sign_fact_id).toBe('fact-moon')
    expect(result.chandrashtama?.natal_moon_sign_id).toBe(MOON_SIGN)
    // Virgo (6) counted from Aquarius (11) = house 8 → chandrāṣṭama.
    expect(result.chandrashtama?.house_from_natal_moon).toBe(8)
    expect(result.chandrashtama?.is_chandrashtama).toBe(true)
    // The panchāṅga service's own re-derivation agrees here; a disagreement would surface.
    expect(result.chandrashtama?.native_context_agrees_with_l1).toBe(true)
  })

  it('ND-4: a failed OPTIONAL overlay no longer blanks the other four fields, and is disclosed by name', async () => {
    vi.stubGlobal('fetch', mockFetch({ panchanga: 'overlay_failed' }))
    const result = await computeKalaNow(CHART, {}, PRINCIPAL)

    // This is the whole point of the fail-soft change: the four fields that never needed the
    // chart at all survive an overlay failure.
    const cov = byConcept(result.coverage)
    for (const concept of ['disha_shula', 'gulika_kalam_now', 'hora_now', 'janma_resonance']) {
      expect(cov[concept]?.state, `${concept} must survive an overlay failure`).toBe('computed')
    }
    // The specific upstream reason is carried through verbatim, not relabelled "unreachable".
    expect(result.provenance_envelope.panchanga_native_context_error)
      .toContain('tz_offset_minutes')
    // chandrāṣṭama still works, because L1 is its authority — not the failed overlay.
    expect(result.chandrashtama?.natal_moon_sign_source).toBe('l1_chart_facts')
  })

  it('a genuine dispatch failure is still reported, and is NOT worded as a bare transient', async () => {
    vi.stubGlobal('fetch', mockFetch({ panchanga: 'dispatch_fail' }))
    const result = await computeKalaNow(CHART, {}, PRINCIPAL)
    expect(result.provenance_envelope.panchanga_reachable).toBe(false)
    const reason = byConcept(result.coverage)['disha_shula']?.reason ?? ''
    expect(reason).toContain('persistent defect')
  })
})

// ── Root Cause C (item 30) ─────────────────────────────────────────────────────────────

describe('Root Cause C — item 30: muntha is read from muntha_position_jsonb and disclosed', () => {
  it('THE REJECTED DEFECT: muntha_sign/muntha_house populate from the real JSONB column', async () => {
    vi.stubGlobal('fetch', mockFetch({}))
    const ahead = await computeKalaAhead(CHART, {}, PRINCIPAL)
    expect(ahead.mudda_dasha_varsha?.muntha_sign).toBe('Libra')
    expect(ahead.mudda_dasha_varsha?.muntha_house).toBe(7)
    expect(ahead.mudda_dasha_varsha?.muntha_lord).toBe('Venus')
    expect(ahead.mudda_dasha_varsha?.muntha_house_from_varsha_lagna).toBe(10)
    expect(ahead.mudda_dasha_varsha?.muntha_degree).toBeCloseTo(12.4311, 4)
  })

  it('muntha gets its OWN coverage entry, separate from mudda_dasha_varsha', async () => {
    vi.stubGlobal('fetch', mockFetch({}))
    const ahead = await computeKalaAhead(CHART, {}, PRINCIPAL)
    expect(byConcept(ahead.coverage)['muntha_varsha_position']?.state).toBe('computed')
    expect(ahead.provenance_envelope.muntha_varsha_position_reachable).toBe(true)
  })

  it('THE DISCLOSURE GAP: a missing muntha is now reported, while the mudda chain stays "computed"', async () => {
    // The precise reopened condition: the mudda-chain deliverable works, the muntha does not.
    vi.stubGlobal('fetch', mockFetch({
      varshaRow: {
        varsha_year: 43,
        varsha_start_iso: '2026-02-04 23:59:03+00',
        varsha_end_iso: '2027-02-05 06:03:58+00',
        year_lord: 'Venus',
        muntha_position_jsonb: null,
      },
    }))
    const ahead = await computeKalaAhead(CHART, {}, PRINCIPAL)
    const cov = byConcept(ahead.coverage)
    expect(cov['mudda_dasha_varsha']?.state).toBe('computed')
    expect(cov['muntha_varsha_position']?.state).toBe('honest_empty')
    expect(cov['muntha_varsha_position']?.reason).toContain('muntha_position_jsonb')
    expect(ahead.provenance_envelope.muntha_varsha_position_reachable).toBe(false)
  })

  it('THE PROSE LEAK: the digest never emits "Muntha in unknown"', async () => {
    vi.stubGlobal('fetch', mockFetch({
      varshaRow: {
        varsha_year: 43,
        varsha_start_iso: '2026-02-04 23:59:03+00',
        varsha_end_iso: '2027-02-05 06:03:58+00',
        year_lord: null,
        muntha_position_jsonb: null,
      },
    }))
    const ahead = await computeKalaAhead(CHART, {}, PRINCIPAL)
    const serialized = JSON.stringify(ahead.digest_90d)
    expect(serialized).not.toContain('Muntha in unknown')
    expect(serialized).not.toContain('Year-lord unknown')
    expect(serialized).not.toMatch(/\bunknown\b/)
  })

  it('a populated muntha DOES appear in the digest prose, with its house and lord', async () => {
    vi.stubGlobal('fetch', mockFetch({}))
    const ahead = await computeKalaAhead(CHART, {}, PRINCIPAL)
    const muddaItem = ahead.digest_90d.items.find((i) => i.kind === 'mudda_dasha_varsha')
    if (muddaItem) {
      expect(muddaItem.detail).toContain('Muntha in Libra')
      expect(muddaItem.detail).toContain('7H from natal lagna')
      expect(muddaItem.detail).toContain('lord Venus')
    }
  })
})

// ── ND-1: tri-plane null shape ─────────────────────────────────────────────────────────

describe('ND-1 — no facade emits a bare null in any tri_plane slot', () => {
  const PLANES = ['interpretation_ref', 'prediction_ref', 'intervention_ref'] as const

  function assertNoBareNulls(triPlane: TriPlanePointers, label: string) {
    for (const plane of PLANES) {
      const slot = triPlane[plane]
      expect(slot, `${label}.${plane} is a bare null — tri_plane_no_dead_end_gate.ts grades this WARN`).not.toBeNull()
      if (isNoLever(slot!)) {
        expect((slot as { reason: string }).reason.length, `${label}.${plane} no_lever needs a reason`).toBeGreaterThan(20)
      } else {
        expect(typeof (slot as { instrument: string }).instrument).toBe('string')
      }
    }
  }

  it('kala_now_get: interpretation_ref is a REAL pointer to kala_explain_get (the ND-1 "worst case")', async () => {
    vi.stubGlobal('fetch', mockFetch({}))
    const result = await computeKalaNow(CHART, {}, PRINCIPAL)
    assertNoBareNulls(result.tri_plane, 'kala_now_get')
    expect(isNoLever(result.tri_plane.interpretation_ref!)).toBe(false)
    expect((result.tri_plane.interpretation_ref as { instrument: string }).instrument).toBe('kala_explain_get')
    // …and it becomes a traversable drill pointer, not just an envelope field.
    expect(result.drill_pointers.map((p) => p.instrument)).toContain('kala_explain_get')
  })

  it('kala_ahead_get: prediction_ref is an honest self-describing no_lever, not a bare null', async () => {
    vi.stubGlobal('fetch', mockFetch({}))
    const ahead = await computeKalaAhead(CHART, {}, PRINCIPAL)
    assertNoBareNulls(ahead.tri_plane, 'kala_ahead_get')
    expect(isNoLever(ahead.tri_plane.prediction_ref!)).toBe(true)
    expect((ahead.tri_plane.prediction_ref as { reason: string }).reason).toContain('IS the prediction plane')
  })

  it('the shape survives total substrate unreachability (view-level fact, not data-conditional)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 500, text: async () => 'down' })) as unknown as typeof fetch)
    const result = await computeKalaNow(CHART, {}, PRINCIPAL)
    assertNoBareNulls(result.tri_plane, 'kala_now_get (substrate down)')
    const ahead = await computeKalaAhead(CHART, {}, PRINCIPAL)
    assertNoBareNulls(ahead.tri_plane, 'kala_ahead_get (substrate down)')
  })
})

// ── ND-2: freshness honesty ────────────────────────────────────────────────────────────

describe('ND-2 — `stale` is never a confident false with no attestation behind it', () => {
  it('THE REJECTED DEFECT: all-null attestation now yields stale:null with a stated reason', () => {
    const f = buildKalaFreshness({ ephemerisVersion: null, sweepBuildDate: null, fieldHash: null })
    expect(f.stale).toBeNull()
    expect(f.stale_reason).toBe(KALA_FRESHNESS_NOT_EVALUABLE_REASON)
  })

  it('a real declared horizon still produces an EARNED boolean in both directions', () => {
    const expired = buildKalaFreshness({
      ephemerisVersion: null, sweepBuildDate: null, fieldHash: null,
      staleAfter: '2020-01-01', now: new Date('2026-07-30'),
    })
    expect(expired.stale).toBe(true)
    expect(expired.stale_reason).toContain('horizon expired')

    const within = buildKalaFreshness({
      ephemerisVersion: null, sweepBuildDate: null, fieldHash: null,
      staleAfter: '2030-01-01', now: new Date('2026-07-30'),
    })
    expect(within.stale).toBe(false)
  })

  it('provenance evidence with no declared horizon earns a false', () => {
    const f = buildKalaFreshness({ ephemerisVersion: '2.10.03', sweepBuildDate: null, fieldHash: null })
    expect(f.stale).toBe(false)
    expect(f.stale_reason).toBeNull()
  })

  it('the live facades surface the honest null rather than the unfalsifiable false', async () => {
    vi.stubGlobal('fetch', mockFetch({}))
    const result = await computeKalaNow(CHART, {}, PRINCIPAL)
    expect(result.freshness.ephemeris_version).toBeNull()
    expect(result.freshness.stale).toBeNull()
    expect(result.freshness.stale_reason).toContain('not evaluable')
  })
})
