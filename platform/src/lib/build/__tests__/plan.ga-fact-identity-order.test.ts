/**
 * plan.ga-fact-identity-order.test.ts — migration 1333's DAG edges, read from the ACTUAL migration file, put the Fact Identity Index AFTER every
 * ga_* asset that writes chart_facts and BEFORE its reader bo_pratijna, in every plan scope.
 *
 * Why this matters: chart_fact_identity.fact_id is ON DELETE CASCADE from chart_facts, so any chart_facts writer that runs AFTER the index
 * empties it again. The only guarantee is the DAG order; this test is the positive proof that the planner honours it (a regression that
 * dropped an edge, or added one that formed a cycle, fails here, not in production).
 *
 * The registry is the production-shaped snapshot of 2026-10-05 (after migration 1262) with exactly migration 1333's two edits applied:
 * ga_fact_identity.has_writer = true and depends_on = the migration's v_deps; bo_pratijna.depends_on += ga_fact_identity.
 */
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import { computeWaves, type RegistryEntry } from '../plan'

const ROOT = (() => {
  let dir = __dirname
  for (let i = 0; i < 10; i++) {
    if (fs.existsSync(path.join(dir, 'platform/migrations'))) return dir
    dir = path.dirname(dir)
  }
  throw new Error('repo root not found')
})()
const MIGRATION = fs.readFileSync(path.join(ROOT, 'platform/migrations/1333_ga_fact_identity_writer_registration.sql'), 'utf8')
const ID = 'ga_fact_identity'
const CONSUMER = 'bo_pratijna'

const migrationEdges = (): string[] => {
  const block = /v_deps\s+constant text\[\] := ARRAY\[([\s\S]*?)\];/.exec(MIGRATION)
  if (!block) throw new Error('v_deps not found in migration 1333')
  return [...block[1].matchAll(/'(ga_[a-z_]+)'/g)].map((m) => m[1])
}

type Row = { asset_id: string; layer: string; depends_on: string[] | null; is_active: boolean; has_writer: boolean; asset_kind: 'data' | 'artifact' | 'service' }
const snapshot = JSON.parse(
  fs.readFileSync(path.join(ROOT, 'platform/src/lib/nirmana-elevation/__tests__/fixtures/production_asset_registry_2026_10_05.json'), 'utf8'),
) as { rows: Row[] }

const registryAfter1333 = (): RegistryEntry[] => {
  const edges = migrationEdges()
  return snapshot.rows
    .filter((r) => r.is_active && r.has_writer || r.asset_id === ID)
    .map((r) => ({
      asset_id: r.asset_id,
      layer: r.layer,
      asset_kind: r.asset_kind,
      has_writer: r.asset_id === ID ? true : r.has_writer,
      estimated_seconds: null,
      depends_on:
        r.asset_id === ID ? [...edges]
        : r.asset_id === CONSUMER ? [...(r.depends_on ?? []), ID]
        : [...(r.depends_on ?? [])],
    }))
}

describe('migration 1333 — the DAG puts ga_fact_identity after every chart_facts writer and before bo_pratijna', () => {
  it('the edge list is the 11 ga_* chart_facts writers, all present, active, with a writer in the registry', () => {
    const edges = migrationEdges()
    expect(edges).toHaveLength(11)
    expect([...edges].sort()).toEqual(edges) // stored sorted
    const byId = new Map(snapshot.rows.map((r) => [r.asset_id, r]))
    for (const e of edges) expect(byId.get(e), e).toMatchObject({ is_active: true, has_writer: true, layer: 'ganita' })
  })

  it('global scope: every chart_facts writer is in an earlier wave than ga_fact_identity, and bo_pratijna in a later one', () => {
    const registry = registryAfter1333()
    const waves = computeWaves(registry.map((r) => r.asset_id), registry, 'global', null)
    const waveOf = new Map<string, number>()
    waves.forEach((w, i) => w.forEach((id) => waveOf.set(id, i)))
    for (const e of migrationEdges()) expect(waveOf.get(e)!, e).toBeLessThan(waveOf.get(ID)!)
    expect(waveOf.get(ID)!).toBeLessThan(waveOf.get(CONSUMER)!)
  })

  it('layer scope (ganita): ga_fact_identity lands in a wave strictly after all 11 writers', () => {
    const registry = registryAfter1333()
    const candidates = registry.filter((r) => r.layer === 'ganita').map((r) => r.asset_id)
    const waves = computeWaves(candidates, registry, 'layer', 'ganita')
    const waveOf = new Map<string, number>()
    waves.forEach((w, i) => w.forEach((id) => waveOf.set(id, i)))
    for (const e of migrationEdges()) expect(waveOf.get(e)!, e).toBeLessThan(waveOf.get(ID)!)
  })

  it('the post-1333 graph is acyclic (the topological sort inside computeWaves throws on a cycle)', () => {
    const registry = registryAfter1333()
    expect(() => computeWaves(registry.map((r) => r.asset_id), registry, 'global', null)).not.toThrow()
  })
})
