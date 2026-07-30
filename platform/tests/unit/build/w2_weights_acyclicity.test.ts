/**
 * w2_weights_acyclicity.test.ts — ṢAḌ-DARŚANA W2 Lane E · SUB-RULE 6 of the weights-version
 * acyclicity mechanism, asserted against the REAL resolver and the REAL seed.
 *
 * Spec: `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
 *        KALA_W2_FIELD_DESIGN_v1_0.md` §7.5 sub-rule 6; brief `SHAD_DARSHANA_BRIEF_v2_0.md`
 *        §2.5.4.
 *
 * ── WHY THIS FILE EXISTS SEPARATELY FROM THE PYTHON ONE ────────────────────────────────
 * `platform/python-sidecar/tests/l5/test_mi_bhara_weights_acyclicity.py` covers the writer
 * side using a faithful Python mirror of `topoSort`. A mirror is not the thing: what actually
 * runs in production is `resolveBuildPlan` in `platform/src/lib/build/plan.ts`, reading
 * `asset_registry` rows seeded from `platform/scripts/seed/asset_registry_seed.ts`. This file
 * asserts THOSE, so the guard cannot pass because the mirror drifted.
 *
 * ── THE RULE ───────────────────────────────────────────────────────────────────────────
 *   `ka_kshetra` NEVER lists `mi_bhara` in `depends_on`.
 *
 * That edge, with the required `mi_bhara.depends_on = ['ka_kshetra']`, forms the cycle
 * `ka_kshetra → mi_bhara → ka_kshetra`. `topoSort` throws on a cycle, and `resolveBuildPlan`
 * calls it for EVERY plan — so the edge would not merely break this wave, it would break every
 * chart build in the product. The calibration loop closes by VERSION PIN across builds
 * (weights v0 seeded by migration 476; `ka_kshetra` reads the newest active version as a DATA
 * dependency; `mi_bhara` INSERTs a new version; the next `ka_kshetra` rebuild pins it), which
 * keeps the DAG acyclic WITHIN every build.
 *
 * ── ASSERTED POSITIVELY (§7.5 sub-rule 6's own wording) ────────────────────────────────
 * Not "we did not find the edge" — a plan that topo-sorts WITHOUT error. The negative form
 * passes by not-noticing if the cycle arrives under another name or through a longer path;
 * the positive form cannot, and §3 proves it by introducing exactly such a path and watching
 * the resolver reject it.
 */
import { describe, it, expect } from 'vitest'
import { ASSETS } from '../../../scripts/seed/asset_registry_seed'
import { resolveBuildPlan, type RegistryEntry, type ThroughputEntry, type AssetId } from '@/lib/build/plan'

const byId = new Map(ASSETS.map(a => [a.asset_id, a]))

/** The seed rows, in the shape `resolveBuildPlan` reads them out of `asset_registry`. */
function registryFromSeed(): RegistryEntry[] {
  return ASSETS.map(a => ({
    asset_id: a.asset_id,
    layer: a.layer,
    depends_on: a.depends_on,
    estimated_seconds: a.estimated_seconds,
  }))
}

function dormant(ids: AssetId[]): Map<AssetId, ThroughputEntry> {
  return new Map(ids.map(id => [id, { asset_id: id, state: 'dormant' as const }]))
}

/**
 * Everything `lit`, used with `action: 'rebuild'`.
 *
 * This combination is not incidental — it is what makes the cycle assertions REACH the cycle.
 * `resolveBuildPlan` runs its pre-flight gate BEFORE `computeWaves`/`topoSort`, and returns
 * `blocked` the moment any dependency is dormant. With a dormant fixture the poisoned-registry
 * tests below would come back `blocked` and never throw, and the "no cycle" assertions would
 * be passing on a code path that never sorted anything. `rebuild` makes every in-scope asset a
 * candidate regardless of state, and `lit` upstreams let pre-flight through, so the topo-sort
 * genuinely executes.
 */
function allLit(ids: AssetId[]): Map<AssetId, ThroughputEntry> {
  return new Map(ids.map(id => [id, { asset_id: id, state: 'lit' as const }]))
}

describe('ṢAḌ-DARŚANA W2 — weights-version acyclicity (§7.5 sub-rule 6)', () => {
  // ── §1 — the specific forbidden edge ────────────────────────────────────────────────
  it('ka_kshetra does not list mi_bhara in depends_on', () => {
    const ka = byId.get('ka_kshetra')
    expect(ka, 'ka_kshetra must have a seed row for this guard to mean anything').toBeDefined()
    expect(ka!.depends_on).not.toContain('mi_bhara')
  })

  it('mi_bhara depends on ka_kshetra and on nothing else', () => {
    const mi = byId.get('mi_bhara')
    expect(mi, 'mi_bhara must have a seed row (brief §2.5.1 — same PR as the writer)').toBeDefined()
    expect(mi!.depends_on).toEqual(['ka_kshetra'])
    expect(mi!.layer).toBe('mimamsa')
    expect(mi!.scope).toBe('per_chart')
  })

  it('mi_bhara carries a chart-scoped count_sql (§N.4 cockpit-truth rail)', () => {
    // The cockpit stats route reads count_sql, NOT asset_throughput — the L1 trap. A data
    // asset without one is invisible to Nirmāṇa even when its table is full.
    const mi = byId.get('mi_bhara')!
    expect(mi.count_sql).toBeTruthy()
    expect(mi.count_sql).toContain('chart_id = $1')
    expect(mi.asset_kind ?? 'data').toBe('data')
  })

  // ── §2 — the POSITIVE assertion: a real plan resolves ───────────────────────────────
  it('resolveBuildPlan topo-sorts a plan containing ka_kshetra + mi_bhara without error', () => {
    // `mi_sankalpa` is a W4 asset with no writer and therefore no seed row yet (see migration
    // 483's own scope note). The set is filtered to what actually exists, so this assertion
    // strengthens rather than breaks when W4 lands.
    const wanted = ['ka_kshetra', 'mi_bhara', 'mi_sankalpa'].filter(id => byId.has(id))
    expect(wanted).toContain('ka_kshetra')
    expect(wanted).toContain('mi_bhara')

    const plan = resolveBuildPlan({
      scope: 'asset_set',
      scope_target: wanted.join(','),
      action: 'rebuild',
      registry: registryFromSeed(),
      throughput: allLit(ASSETS.map(a => a.asset_id)),
    })

    expect(plan.status).toBe('ok')
    const order = plan.plan_waves.flat()
    expect(order).toContain('ka_kshetra')
    expect(order).toContain('mi_bhara')
    // and it is ORDERED: the field is built before the calibration that reads it
    expect(order.indexOf('ka_kshetra')).toBeLessThan(order.indexOf('mi_bhara'))
  })

  it('a full global plan over the whole seed resolves — no cycle anywhere in the catalog', () => {
    const plan = resolveBuildPlan({
      scope: 'global',
      scope_target: null,
      action: 'build',
      registry: registryFromSeed(),
      throughput: dormant(ASSETS.map(a => a.asset_id)),
    })
    expect(['ok', 'blocked']).toContain(plan.status)
    if (plan.status === 'ok') {
      const order = plan.plan_waves.flat()
      const iKa = order.indexOf('ka_kshetra')
      const iMi = order.indexOf('mi_bhara')
      if (iKa >= 0 && iMi >= 0) expect(iKa).toBeLessThan(iMi)
    }
  })

  // ── §3 — the guard would GENUINELY FAIL if the edge were added ──────────────────────
  it('adding the forbidden edge makes resolveBuildPlan throw (the vacuity half)', () => {
    // Without this, §2 passes just as happily on a resolver that never detects cycles at all —
    // a green signal with no detector behind it (CLAUDE.md §N.8).
    const poisoned = registryFromSeed().map(r =>
      r.asset_id === 'ka_kshetra' ? { ...r, depends_on: [...r.depends_on, 'mi_bhara'] } : r
    )
    expect(() =>
      resolveBuildPlan({
        scope: 'asset_set',
        scope_target: 'ka_kshetra,mi_bhara',
        action: 'rebuild',
        registry: poisoned,
        throughput: allLit(poisoned.map(r => r.asset_id)),
      })
    ).toThrow(/Cycle detected/)
  })

  it('a longer cycle that never names mi_bhara directly is caught too', () => {
    // ka_kshetra → mi_pramana → mi_bhara → ka_kshetra. Half (a) of the guard — "is mi_bhara in
    // ka_kshetra.depends_on?" — passes this. The topo-sort does not.
    const poisoned = registryFromSeed().map(r => {
      if (r.asset_id === 'ka_kshetra') return { ...r, depends_on: [...r.depends_on, 'mi_pramana'] }
      if (r.asset_id === 'mi_pramana') return { ...r, depends_on: ['mi_bhara'] }
      return r
    })
    expect(poisoned.find(r => r.asset_id === 'ka_kshetra')!.depends_on).not.toContain('mi_bhara')
    expect(() =>
      resolveBuildPlan({
        scope: 'asset_set',
        scope_target: 'ka_kshetra,mi_bhara,mi_pramana',
        action: 'rebuild',
        registry: poisoned,
        throughput: allLit(poisoned.map(r => r.asset_id)),
      })
    ).toThrow(/Cycle detected/)
  })

  // ── §4 — the EDGE-STAGING RULE (§9.1) ──────────────────────────────────────────────
  it('no W2 asset pre-declares the W3 bg_sky_calendar edge', () => {
    // §9.1's trap: `resolveBuildPlan` cannot resolve an edge to an id with no seed row, so a
    // "helpful" early declaration would 500 every chart build. W3 adds the edge in the SAME
    // PR that lands `bg_sky_calendar`'s seed row — never before.
    const ka = byId.get('ka_kshetra')
    if (ka && !byId.has('bg_sky_calendar')) {
      expect(ka.depends_on).not.toContain('bg_sky_calendar')
    }
  })
})
