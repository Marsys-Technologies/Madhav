/**
 * NIRMĀṆA v2.1 · L4 · migration 682 — the identity trigger that completes D-CND-04 (#1732).
 *
 * 680 made the identity deterministic and remapped the existing rows, but left
 * `phala_anchors.anchor_id` defaulting to `gen_random_uuid()` — so the guarantee lived in one
 * writer rather than in the table. This suite guards the contract of the fix; the migration
 * itself proves its behaviour live at deploy time (it inserts without `anchor_id`, asserts the
 * derived identity came back, asserts a re-insert of the same event tuple collapses, and rolls
 * both probes back).
 */
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/682_phala_anchor_identity_trigger.sql'),
  'utf8',
)

describe('migration 682 — the invariant moves from the writer to the table', () => {
  it('installs a BEFORE INSERT trigger on phala_anchors', () => {
    expect(migration).toMatch(/CREATE TRIGGER phala_anchors_identity_biu[\s\S]*BEFORE INSERT ON phala_anchors/)
  })

  it('does NOT fire on UPDATE', () => {
    // Recomputing on UPDATE would let an ordinary column edit silently change an anchor's
    // identity and orphan every reference to it — converting a safe operation into the exact
    // failure D-CND-04 exists to prevent.
    const createTrigger = migration.slice(migration.indexOf('CREATE TRIGGER phala_anchors_identity_biu'))
    const stmt = createTrigger.slice(0, createTrigger.indexOf(';'))
    expect(stmt).not.toMatch(/\bUPDATE\b/)
    expect(stmt).not.toMatch(/\bDELETE\b/)
  })

  it('retires the random default rather than leaving it to read as live', () => {
    expect(migration).toContain('ALTER TABLE phala_anchors ALTER COLUMN anchor_id DROP DEFAULT')
  })

  it('derives the identity from the row itself, via 680\'s single source of truth', () => {
    expect(migration).toContain('NEW.anchor_id := phala_anchor_identity(')
    for (const field of [
      'NEW.chart_id', 'NEW.anchor_source', 'NEW.event_type', 'NEW.direction', 'NEW.domain',
      'NEW.horizon_tier', 'NEW.window_start', 'NEW.peak_date', 'NEW.window_end', 'NEW.falsifier',
    ]) {
      expect(migration).toContain(field)
    }
  })

  it('excludes every graded quantity from the identity (D-CND-11)', () => {
    const fn = migration.slice(
      migration.indexOf('CREATE OR REPLACE FUNCTION phala_anchors_set_identity'),
      migration.indexOf('COMMENT ON FUNCTION phala_anchors_set_identity'),
    )
    for (const graded of ['magnitude', 'confidence_low', 'confidence_high', 'posterior']) {
      expect(fn).not.toContain(graded)
    }
  })

  it('overwrites rather than filling only when NULL', () => {
    // anchor_id was NOT NULL WITH a default, so a caller omitting it never presented NULL —
    // it presented a freshly minted random uuid. Fill-if-null would never have fired on the
    // one case the trigger exists to catch.
    const fn = migration.slice(
      migration.indexOf('CREATE OR REPLACE FUNCTION phala_anchors_set_identity'),
      migration.indexOf('COMMENT ON FUNCTION phala_anchors_set_identity'),
    )
    expect(fn).not.toMatch(/IF\s+NEW\.anchor_id\s+IS\s+NULL/i)
  })
})

describe('migration 682 — it fails closed and proves itself', () => {
  it('refuses to run without 680\'s identity function', () => {
    expect(migration).toContain('migration 682 requires phala_anchor_identity() from migration 680')
  })

  it('proves an anchor_id-omitting insert now yields the derived identity', () => {
    expect(migration).toContain('an anchor_id-omitting insert produced % but the derived identity is %')
  })

  it('proves the same event tuple cannot mint a second identity', () => {
    // The property the entire campaign-wide hold is about.
    expect(migration).toContain('the same event tuple minted a second identity')
    expect(migration).toContain('ON CONFLICT (anchor_id) DO NOTHING')
  })

  it('rolls its probe rows back rather than leaving test data in the table', () => {
    expect(migration).toContain("RAISE EXCEPTION 'rollback_probe'")
  })

  it('asserts its own post-conditions', () => {
    expect(migration).toContain('still carries a column default')
    expect(migration).toContain('the identity trigger is not installed')
  })
})
