/**
 * NIRMĀṆA v2.1 · L4 · migration 680 — deterministic phala_anchors.anchor_id (D-CND-04, issue #1732).
 *
 * The migration carries its own live assertions (it refuses to install a red gate, and it
 * proves the detector goes red on an injected dangling reference before committing). This
 * suite guards the *contract* against future edits — the things a later change could quietly
 * break without any live assertion noticing.
 */
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/680_phala_anchor_deterministic_identity.sql'),
  'utf8',
)
const writer = fs.readFileSync(
  path.resolve(process.cwd(), 'python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py'),
  'utf8',
)

/** Every field that makes the anchor identity, in the order the function takes them. */
const IDENTITY_FIELDS = [
  'chart_id', 'anchor_source', 'event_type', 'direction', 'domain',
  'horizon_tier', 'window_start', 'peak_date', 'window_end', 'falsifier',
] as const

/**
 * Fields that must NEVER enter the identity. If a recalibration changes a prediction's
 * grade, the prediction must keep its identity — otherwise an outcome can never be
 * compared to the prediction it tests, which is precisely the P7 loop this key protects.
 */
const GRADE_FIELDS = ['magnitude', 'confidence_low', 'confidence_high', 'posterior'] as const

/**
 * Upstream surrogate keys that must NEVER enter the identity: convergence_id and
 * bhavishya_id are bigserial against delete-then-insert L3 writers, and signal_id is
 * uuid4-per-build (issue #1748). Including any of them re-mints L4 identities whenever
 * an upstream layer rebuilds — the exact failure D-CND-04 forbids.
 */
const UNSTABLE_UPSTREAM_KEYS = ['convergence_id', 'discovery_id', 'bhavishya_id', 'signal_id'] as const

function identityFunctionBody(): string {
  const start = migration.indexOf('CREATE OR REPLACE FUNCTION phala_anchor_identity(')
  expect(start).toBeGreaterThan(-1)
  const end = migration.indexOf('COMMENT ON FUNCTION phala_anchor_identity', start)
  expect(end).toBeGreaterThan(start)
  return migration.slice(start, end)
}

describe('migration 680 — the anchor identity namespace is permanent', () => {
  it('pins the namespace uuid literally', () => {
    // Changing this value re-mints every anchor id in existence and orphans every
    // stored reference. It is pinned here so such a change cannot pass review silently.
    expect(migration).toContain("SELECT 'a5f7c1e2-0b3d-5e88-9c41-6d2f8a7b4e10'::uuid")
  })

  it('derives the id with uuid v5, not a random generator', () => {
    expect(identityFunctionBody()).toContain('uuid_generate_v5')
    expect(identityFunctionBody()).not.toContain('gen_random_uuid')
    expect(identityFunctionBody()).not.toContain('uuid_generate_v4')
  })
})

describe('migration 680 — the identity tuple is grade-free and upstream-key-free', () => {
  it.each(IDENTITY_FIELDS)('includes %s', (field) => {
    expect(identityFunctionBody()).toContain(`p_${field}`)
  })

  it.each(GRADE_FIELDS)('excludes the grade field %s', (field) => {
    expect(identityFunctionBody()).not.toContain(field)
  })

  it.each(UNSTABLE_UPSTREAM_KEYS)('excludes the unstable upstream key %s', (field) => {
    expect(identityFunctionBody()).not.toContain(field)
  })

  it('encodes the tuple canonically and date-style-independently', () => {
    const body = identityFunctionBody()
    expect(body).toContain('jsonb_build_array')
    for (const dateField of ['p_window_start', 'p_peak_date', 'p_window_end']) {
      expect(body).toContain(`${dateField}::text`)
    }
  })
})

describe('migration 680 — the remap is total, guarded, and self-proving', () => {
  it('remaps only identities that are unique, never silently collapsing rows', () => {
    expect(migration).toContain('HAVING count(*) = 1')
  })

  it('fails closed if a computed identity collides with a different existing anchor', () => {
    expect(migration).toContain('computed identities collide with a different existing anchor')
  })

  it('asserts zero dangling references after the remap', () => {
    expect(migration).toContain('dangling reference(s) across the 8 referencing columns')
  })

  it('re-checks the deferred foreign keys inside the migration, not at commit', () => {
    expect(migration).toMatch(/SET CONSTRAINTS[\s\S]*IMMEDIATE;/)
  })

  it('restores every deferred constraint to NOT DEFERRABLE', () => {
    const madeDeferrable = migration.match(/ALTER CONSTRAINT \w+\s+DEFERRABLE INITIALLY IMMEDIATE/g) ?? []
    const restored = migration.match(/ALTER CONSTRAINT \w+\s+NOT DEFERRABLE/g) ?? []
    expect(madeDeferrable).toHaveLength(6)
    expect(restored).toHaveLength(6)
  })

  it('does not rewrite the two L5 columns that were verified NOT to hold anchor ids', () => {
    expect(migration).not.toMatch(/UPDATE mimamsa_attribution/)
    expect(migration).not.toMatch(/UPDATE mimamsa_manifestation_sets/)
  })

  it('does rewrite the one L5 column that was verified to hold them', () => {
    expect(migration).toMatch(/UPDATE mimamsa_predictions p SET source_pramana_id/)
  })
})

describe('migration 680 — the detector is a gate, not a proposal (C12 rewrite floor test)', () => {
  it('refuses to install a detector that is already red', () => {
    expect(migration).toContain('refusing to install a red gate')
  })

  it('proves the detector can fail on real corruption before committing to it', () => {
    expect(migration).toContain('FAILED the rewrite floor test')
    expect(migration).toContain("RAISE EXCEPTION 'rollback_probe'")
  })

  it('bounds the known identity exception explicitly rather than skipping it silently', () => {
    // The 4 rows are 2 content-identical pairs whose merge re-points L5 rows (issue #1748).
    // The allowance must be an explicit counted ceiling that can only shrink.
    expect(migration).toMatch(/a\.window_end, a\.falsifier\)\) <= 4/)
  })

  it('checks referential integrity across all eight verified referencing columns', () => {
    for (const table of [
      'phala_suddha_sodhana', 'phala_sodhana', 'phala_pramana', 'phala_sankrama',
      'phala_muhurta', 'phala_mitigation', 'phala_phaladesa', 'mimamsa_predictions',
    ]) {
      expect(migration).toContain(table)
    }
  })
})

describe('ph_nimitta writer — one implementation of the identity, and no silent drops', () => {
  it('calls the SQL function rather than reimplementing uuid5 in Python', () => {
    expect(writer).toContain('phala_anchor_identity(')
    expect(writer).not.toMatch(/uuid\.uuid5\s*\(/)
  })

  it('targets the anchor_id conflict explicitly instead of a bare ON CONFLICT', () => {
    // Assert on the executable INSERT, not on prose: the phrase "ON CONFLICT DO NOTHING"
    // legitimately appears in two explanatory comments (CR-46's history, and the §N.8
    // note on rowcount), and a naive whole-file match would fail on those.
    const insertSql = writer.slice(
      writer.indexOf('INSERT INTO phala_anchors ('),
      writer.indexOf('rows_inserted += 1'),
    )
    expect(insertSql).toContain('ON CONFLICT (anchor_id) DO NOTHING')
    expect(insertSql).not.toMatch(/ON CONFLICT\s+DO NOTHING/)
  })

  it('counts what the database accepted rather than assuming the insert landed', () => {
    // §N.8: an unconditional `rows_inserted += 1` beside ON CONFLICT DO NOTHING is a
    // claimed count with no measurement behind it.
    expect(writer).toContain('if cur.rowcount == 1:')
    expect(writer).toContain('identity_collapsed += 1')
  })

  it('reports a collapse loudly instead of hiding it', () => {
    expect(writer).toMatch(/logger\.warning\([\s\S]*identity_collapsed/)
  })
})
