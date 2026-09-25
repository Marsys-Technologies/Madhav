import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { ASSETS } from '../seed/asset_registry_seed'
import { EXPLICIT_CLEAR_OPS } from '@/lib/cockpit/assetClearSpec'

/**
 * W-L0-1 (L0 Brahmagyan elevation, strategy v2.1 §4.2) — registry parity for the
 * 40 bg_* assets. Extends the L3 B1 pattern (gochara_seed_target_table_parity)
 * from one asset to the layer.
 *
 * What this guards, and why it is not cosmetic:
 *
 * `asset_registry.target_table` is seed-owned — the upsert's ON CONFLICT clause
 * sets `target_table = EXCLUDED.target_table` (asset_registry_seed.ts, the
 * DO UPDATE block), unlike count_sql/depends_on, which are migration-governed.
 * The seed literal is therefore the authoritative structural declaration of
 * which relation(s) a writer produces, and every consumer of that column must
 * read the same shape:
 *
 *   - the seed pre-flight (to_regclass per declared table),
 *   - the TCI bootstrap (generate_tci.ts TABLE_ASSETS),
 *   - the cockpit clear paths (deriveDeleteSqlFromCountSql → target_table
 *     fallback, gated by EXPLICIT_CLEAR_OPS for multi-table writers),
 *   - dag_edge_guard's producer mapping,
 *   - AtlasView's display.
 *
 * bg_prashna_rules is the anchor case: its writer (l0_prashna.seed_prashna_rules)
 * seeds FIVE peer tables, none of them primary, so the honest declaration is a
 * comma-separated multi-table set. Before W-L0-1 the row carried
 * target_table: null — which the pre-flight treats as the intentional
 * service/chart-partitioned shape, i.e. the registry actively mis-described a
 * postgres_table asset. The test reads the writer module's own INSERT targets
 * and requires the seed row, the count_sql and the clear spec all to agree with
 * them: a constant can drift from its source; a reference cannot (CLAUDE.md
 * §N.7 item 3).
 */

const PRASHNA_MODULE = path.resolve(
  __dirname,
  '../../python-sidecar/brahmagyan/l0_prashna.py'
)

const RELEASE_JSON = path.resolve(
  __dirname,
  '../../python-sidecar/brahmagyan/l0_semantic_release_v1.json'
)

const SLICE_JSON = path.resolve(
  __dirname,
  '../../python-sidecar/brahmagyan/l0_resource_config_slice_v1.json'
)

function readJson(p: string): Record<string, unknown> {
  return JSON.parse(readFileSync(p, 'utf8')) as Record<string, unknown>
}

const TABLE_NAME_RE = /^[a-z_][a-z0-9_]{0,62}$/

function declaredTables(targetTable: string | null): string[] {
  return (targetTable ?? '').split(',').map(t => t.trim()).filter(Boolean)
}

/** Relations the prashna writer module actually INSERTs into, from its own source. */
function prashnaWriterTargets(): string[] {
  const src = readFileSync(PRASHNA_MODULE, 'utf8')
  const targets = new Set<string>()
  for (const m of src.matchAll(/INSERT INTO (bg_prashna_\w+)/g)) targets.add(m[1])
  if (targets.size === 0) {
    throw new Error(`no INSERT INTO bg_prashna_* targets found in ${PRASHNA_MODULE}`)
  }
  return [...targets].sort()
}

const bgAssets = ASSETS.filter(a => a.asset_id.startsWith('bg_'))
const prashna = ASSETS.find(a => a.asset_id === 'bg_prashna_rules')

describe('L0 registry parity (W-L0-1)', () => {
  describe('the bg_* seed set itself', () => {
    it('contains exactly the 40 registered L0 assets', () => {
      // Measured against production asset_registry on 2026-09-25: 40 rows
      // (SELECT count(*) WHERE asset_id LIKE 'bg\_%'). The strategy's measured
      // inventory (§1.1) is the same 40.
      expect(bgAssets.map(a => a.asset_id).sort()).toHaveLength(40)
    })

    it('every non-service bg_* asset declares a non-null target_table', () => {
      // A null target_table is the intentional shape for service assets
      // (bg_panchanga, bg_ephemeris_engine — health_probe mechanism) and for
      // chart_facts-partitioned writers (none in L0). For a postgres_table
      // asset it is the prashna defect class: the registry claiming no output
      // relation for an asset whose writer demonstrably seeds tables.
      const dishonest = bgAssets.filter(
        a => a.storage_type !== 'service' && !a.target_table,
      )
      expect(dishonest.map(a => a.asset_id)).toEqual([])
    })

    it('every declared target table is a well-formed, unique relation name', () => {
      for (const asset of bgAssets) {
        const tables = declaredTables(asset.target_table)
        for (const t of tables) {
          expect(TABLE_NAME_RE.test(t), `${asset.asset_id}: '${t}'`).toBe(true)
        }
        expect(new Set(tables).size, `${asset.asset_id} duplicates a table`).toBe(tables.length)
      }
    })

    it('no bg_* seed row names the retired legacy reference_nakshatras table', () => {
      // reference_nakshatras (plural) is retired for superseded authority — the
      // live nakshatra reference is reference_nakshatra (singular, bg_nakshatra).
      // W-L0-1 drops the legacy table; nothing may keep declaring or counting it.
      for (const asset of bgAssets) {
        expect(declaredTables(asset.target_table), asset.asset_id).not.toContain('reference_nakshatras')
        expect(asset.count_sql ?? '', asset.asset_id).not.toMatch(/\breference_nakshatras\b/)
      }
    })
  })

  describe('multi-table-set consumers stay in step', () => {
    it('a comma-separated target_table always has an explicit clear spec covering the same set', () => {
      // The clear fallback builds `DELETE FROM <target_table>` verbatim and
      // rejects anything failing TABLE_NAME_RE with a 500 — so a multi-table
      // declaration without an EXPLICIT_CLEAR_OPS entry is not a gap, it is an
      // outage on the clear path. Require the entry, and require it to name
      // exactly the declared tables.
      for (const asset of ASSETS) {
        const tables = declaredTables(asset.target_table)
        if (tables.length <= 1) continue
        const ops = EXPLICIT_CLEAR_OPS[asset.asset_id]
        expect(ops, `${asset.asset_id} declares ${tables.length} tables but has no EXPLICIT_CLEAR_OPS entry`).toBeDefined()
        expect(ops, `${asset.asset_id} clear spec must not be a null skip`).not.toBeNull()
        const cleared = new Set<string>()
        for (const op of ops!) {
          const m = op.sql.match(/^DELETE FROM (\w+)/)
          expect(m, `${asset.asset_id}: unparseable clear op '${op.sql}'`).not.toBeNull()
          cleared.add(m![1])
        }
        expect([...cleared].sort(), asset.asset_id).toEqual([...tables].sort())
      }
    })
  })

  describe('bg_prashna_rules — the anchor case', () => {
    it('the writer module seeds exactly the five peer tables', () => {
      // Anchors every other assertion: if l0_prashna.py is ever repointed, this
      // fails first and the repoint is a deliberate, reviewed change rather
      // than a silent one that drags the registry along with it.
      expect(prashnaWriterTargets()).toEqual([
        'bg_prashna_fructification_rules',
        'bg_prashna_lagna_methods',
        'bg_prashna_significators',
        'bg_prashna_special_techniques',
        'bg_prashna_tajik_yogas',
      ])
    })

    it('the seed row target_table set equals the writer module\'s INSERT targets', () => {
      expect(prashna, 'bg_prashna_rules must have a seed row').toBeDefined()
      expect(declaredTables(prashna!.target_table).sort()).toEqual(prashnaWriterTargets())
    })

    it('the seed count_sql counts every table the writer seeds', () => {
      for (const t of prashnaWriterTargets()) {
        expect(prashna!.count_sql, `count_sql must count ${t}`).toContain(`FROM ${t}`)
      }
    })

    it('the seed row no longer carries the dishonest null target_table', () => {
      expect(prashna!.target_table).not.toBeNull()
      expect(prashna!.storage_type).toBe('postgres_table')
    })
  })

  describe('l0_resource_config_slice_v1.json — disposition: registered (C-5)', () => {
    // C-5 / strategy §4.2 W-L0-1: the Bhavat Bhavam resource-config slice is a
    // second release-shaped artifact beside l0_semantic_release_v1.json and was
    // "built and registered nowhere". The disposition is REGISTER — not as a
    // 41st asset_registry row (the measured inventory is 40), but bound to the
    // semantic release it extends, so the binding is detector-enforced rather
    // than conventional. Its own digest/contract validation lives with its
    // loader (python-sidecar tests/test_l0_resource_config_slice.py); what must
    // hold HERE is that the slice and the release cannot drift apart silently.
    const release = readJson(RELEASE_JSON)
    const slice = readJson(SLICE_JSON)

    it('the slice binds to the current semantic release by id and digest', () => {
      expect(slice.semantic_release_id).toBe(release.semantic_release_id)
      expect(slice.semantic_release_digest).toBe(release.content_sha256)
    })

    it('the slice tracks the release status — a release graduation forces a slice review', () => {
      expect(slice.delivery_state).toBe(release.release_status)
    })

    it('the slice declares the L0 reference boundary honestly', () => {
      // Same boundary as the "no subject column on any bg_* table" check: a
      // global-reference artifact must name the payload fields it refuses.
      const scope = slice.scope as { kind?: string; forbidden_payload_fields?: string[] }
      expect(scope.kind).toBe('global_reference')
      expect(scope.forbidden_payload_fields).toEqual(
        expect.arrayContaining(['subject_id', 'chart_id', 'birth_data', 'personal_observations']),
      )
    })
  })
})
