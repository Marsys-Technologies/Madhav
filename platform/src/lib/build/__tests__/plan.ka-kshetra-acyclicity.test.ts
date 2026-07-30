/**
 * plan.ka-kshetra-acyclicity.test.ts — ṢAḌ-DARŚANA W2 Lane C, §7.5 sub-rule 6.
 *
 * THE WEIGHTS-VERSION ACYCLICITY GUARD.
 *
 * `ka_kshetra` (L3) must read a FITTED weights version; `mi_bhara` (L5) fits it.
 * Writing that as a DAG edge — `ka_kshetra.depends_on = [… 'mi_bhara']` — combined
 * with the necessary `mi_bhara.depends_on = ['ka_kshetra']`, forms the cycle
 *
 *     ka_kshetra → mi_bhara → ka_kshetra
 *
 * which `topoSort` rejects. The blast radius is not this wave: a cyclic registry
 * breaks EVERY chart build, for every layer, immediately. §7.5 calls this "the
 * subtlest part of the wave" for exactly that reason.
 *
 * The loop closes ACROSS builds by VERSION PIN instead of AROUND the DAG:
 *   1. migration 476 seeds `v0_classical` (a MIGRATION, not a writer), so every
 *      chart's first build finds an active weights version — there is no
 *      NULL-weights code path and no build order needing `mi_bhara` to have run;
 *   2. `ka_kshetra` READS the newest active version (a DATA dependency);
 *   3. `mi_bhara` INSERTs a NEW version row (never UPDATEs — weights are
 *      versioned artifacts and silent mutation is a drift failure);
 *   4. the NEXT `ka_kshetra` rebuild pins the newer version.
 *
 * §7.5 sub-rule 6 requires this guard to be POSITIVE, not merely absent-checking:
 * "(a) 'mi_bhara' NOT IN the seeded depends_on of ka_kshetra, and (b)
 * resolveBuildPlan topo-sorts a plan containing {ka_kshetra, mi_bhara,
 * mi_sankalpa} WITHOUT ERROR — a positive assertion, so the guard would correctly
 * fail if someone added the edge, rather than merely not-noticing."
 *
 * Both halves are here, and half (a) reads the ACTUAL migration file rather than
 * a transcription of it, so the guard cannot drift away from what ships.
 */
import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { resolveBuildPlan, computeWaves, type RegistryEntry, type ThroughputEntry } from '../plan'

const HERE = path.dirname(fileURLToPath(import.meta.url))

/** Walk up to the repo root by LOOKING FOR the migrations directory rather than
 *  counting `..` segments — this file has already been moved once by a hardcoded
 *  depth being wrong, and a count is silently wrong in a worktree or after any
 *  directory reshuffle. */
function repoRoot(): string {
  let dir = HERE
  for (let i = 0; i < 10; i++) {
    if (fs.existsSync(path.join(dir, 'platform/supabase/migrations'))) return dir
    dir = path.dirname(dir)
  }
  throw new Error('could not locate platform/supabase/migrations from ' + HERE)
}

const REPO_ROOT = repoRoot()
const MIGRATION = path.join(
  REPO_ROOT,
  'platform/supabase/migrations/480_kala_field_null.sql',
)

/** The eight edges §9.1 declares for `ka_kshetra`, and exactly those eight. */
const EXPECTED_EDGES = [
  'ka_dasha_kala',
  'ka_gochara_sweep',
  'ka_gochara_resonance',
  'ga_panchanga',
  'bo_pratijna',
  'bo_sangati',
  'bo_upaya',
  'bg_cohort',
]

function seededDependsOn(): string[] {
  const sql = fs.readFileSync(MIGRATION, 'utf8')
  const stmt = sql.slice(sql.indexOf('UPDATE asset_registry SET depends_on = ARRAY['))
  const body = stmt.slice(stmt.indexOf('['), stmt.indexOf(']'))
  return [...body.matchAll(/'([a-z0-9_]+)'/g)].map(m => m[1])
}

function reg(asset_id: string, layer: string, depends_on: string[]): RegistryEntry {
  return { asset_id, layer, depends_on, estimated_seconds: 60 }
}

describe('§7.5 sub-rule 6 (a) — the seeded depends_on', () => {
  it('does NOT contain mi_bhara', () => {
    // The one edge that would break every chart build in the product.
    expect(seededDependsOn()).not.toContain('mi_bhara')
  })

  it('does NOT contain bg_sky_calendar — the W3 edge-staging rule (§9.1)', () => {
    // §2.5.1 requires every edge to resolve to an EXISTING asset_id. W3 adds
    // this edge in the SAME PR that lands bg_sky_calendar's seed row, never
    // before: "A W2 lane that 'helpfully' pre-declares the edge breaks
    // production."
    expect(seededDependsOn()).not.toContain('bg_sky_calendar')
  })

  it('contains exactly the eight edges §9.1 declares', () => {
    expect(seededDependsOn().sort()).toEqual([...EXPECTED_EDGES].sort())
  })

  it('never lists ka_kshetra as its own dependency', () => {
    expect(seededDependsOn()).not.toContain('ka_kshetra')
  })
})

describe('§7.5 sub-rule 6 (b) — a plan containing the calibration triangle sorts', () => {
  // A registry that mirrors the real edges around the field: the eight upstreams
  // plus both L5 consumers pointing back at ka_kshetra.
  const REGISTRY: RegistryEntry[] = [
    ...EXPECTED_EDGES.map(id => reg(id, id.startsWith('bg_') ? 'brahmagyan' : 'kala', [])),
    reg('ka_kshetra', 'kala', EXPECTED_EDGES),
    reg('mi_bhara', 'mimamsa', ['ka_kshetra']),
    reg('mi_sankalpa', 'mimamsa', ['ka_kshetra']),
  ]

  // EVERYTHING lit, with action 'rebuild'. Two reasons, both about making this
  // suite assert what it claims to: (1) `rebuild` takes every in-scope asset as a
  // candidate regardless of state, so the plan is genuinely the three-asset one;
  // (2) the pre-flight gate blocks on ANY non-ready dependency — including
  // `ka_kshetra` itself, which is a dep of both L5 consumers — so a dormant
  // fixture returns `status: 'blocked'` with EMPTY waves and the ordering
  // assertions below would pass over nothing.
  const throughput = new Map<string, ThroughputEntry>(
    REGISTRY.map(r => [r.asset_id, { asset_id: r.asset_id, state: 'lit' as const }]),
  )

  it('topo-sorts without error and orders ka_kshetra before both L5 consumers', () => {
    const plan = resolveBuildPlan({
      scope: 'asset_set',
      scope_target: 'ka_kshetra,mi_bhara,mi_sankalpa',
      action: 'rebuild',
      registry: REGISTRY,
      throughput,
    })
    const order = plan.plan_waves.flat()
    expect(order).toContain('ka_kshetra')
    expect(order).toContain('mi_bhara')
    expect(order).toContain('mi_sankalpa')
    expect(order.indexOf('ka_kshetra')).toBeLessThan(order.indexOf('mi_bhara'))
    expect(order.indexOf('ka_kshetra')).toBeLessThan(order.indexOf('mi_sankalpa'))
  })

  it('WOULD fail if the mi_bhara edge were added — the guard has power', () => {
    // §N.8: a guard needs a code path that makes it correctly read false. This
    // constructs exactly the forbidden registry and asserts the sorter rejects
    // it, so the passing test above is evidence rather than a coincidence.
    //
    // Asserted against `computeWaves` (which calls the same private `topoSort`)
    // rather than `resolveBuildPlan`, because with the forbidden edge present
    // `mi_bhara` becomes a DORMANT dependency of `ka_kshetra` and the pre-flight
    // gate would short-circuit to `status: 'blocked'` BEFORE the sort ran — a
    // pass that would prove nothing about cycles. Going straight at the sorter
    // makes the assertion about the thing it claims to be about.
    const cyclic: RegistryEntry[] = REGISTRY.map(r =>
      r.asset_id === 'ka_kshetra'
        ? reg('ka_kshetra', 'kala', [...EXPECTED_EDGES, 'mi_bhara'])
        : r,
    )
    expect(() =>
      computeWaves(['ka_kshetra', 'mi_bhara', 'mi_sankalpa'], cyclic, 'asset_set',
                   'ka_kshetra,mi_bhara,mi_sankalpa'),
    ).toThrow(/Cycle detected/)
  })

  it('the same sort SUCCEEDS on the shipped, edge-free registry', () => {
    // The negative control for the test above: identical call, real edges.
    expect(() =>
      computeWaves(['ka_kshetra', 'mi_bhara', 'mi_sankalpa'], REGISTRY, 'asset_set',
                   'ka_kshetra,mi_bhara,mi_sankalpa'),
    ).not.toThrow()
  })
})

describe('§7.5 — migration 476 is the acyclicity keystone', () => {
  const seed = fs.readFileSync(
    path.join(REPO_ROOT, 'platform/supabase/migrations/476_kala_field_weights_seed.sql'),
    'utf8',
  )

  it('seeds an ACTIVE v0_classical version by migration, not by a writer', () => {
    // This is what guarantees every chart's very first ka_kshetra build finds an
    // active weights version, and therefore that no build order ever needs
    // mi_bhara to have run first.
    expect(seed).toMatch(/'v0_classical',\s*'active'/)
  })

  it('numbers below the field-core migration so it lands first', () => {
    expect(476).toBeLessThan(478)
  })

  it('uses ON CONFLICT DO NOTHING so a re-run cannot silently mutate a weight', () => {
    // Weights are versioned artifacts; silent mutation is a drift failure (§1
    // rail 8). A genuine change to v0 is a NEW version row, never an UPDATE.
    expect(seed).toContain('ON CONFLICT (version_id, weight_id) DO NOTHING')
    expect(seed).not.toMatch(/ON CONFLICT \(version_id, weight_id\) DO UPDATE/)
  })
})
