/**
 * MIGRATION NUMBER GUARD — regression suite.
 *
 * SAMĀPTI lane B-MIGGUARD · brief v2.0 §4.4 (MIG-1).
 *
 * Two things are proven here, and they are different things:
 *
 *  1. THE GUARD PASSES ON THE REAL REPO. If it did not, it would be un-mergeable and every later
 *     PR's CI signal would be poisoned — the exact failure mode A2-CI-POINTERS exists to repair.
 *
 *  2. THE GUARD CAN GO RED. Every hard-failure class (E1/E2/E3) is driven by a synthetic
 *     collision, including the case a naive single-directory check would miss: a number that is
 *     currently free in `platform/supabase/migrations/` but ALREADY TAKEN in
 *     `platform/migrations/` (474 today). A guard that cannot be made to fail proves nothing
 *     (CLAUDE.md §N.8).
 */

import { describe, it, expect } from 'vitest'
import fs from 'fs'
import os from 'os'
import path from 'path'
import {
  MIGRATION_DIRS,
  parseMigrationNumber,
  collectNumberedMigrations,
  computeNextMigrationNumber,
  checkMigrationNumbers,
  loadBaseline,
  repoRootFromHere,
  runGuard,
  type MigrationEntry,
} from '../../../scripts/ci/migration_number_guard'

const REPO_ROOT = repoRootFromHere()

function entry(relPath: string): MigrationEntry {
  const dir = path.dirname(relPath)
  const filename = path.basename(relPath)
  const number = parseMigrationNumber(filename)
  if (number === null) throw new Error(`unnumbered: ${relPath}`)
  return { relPath, dir, filename, number }
}

describe('parseMigrationNumber', () => {
  it('parses leading integers, tolerating zero-padding', () => {
    expect(parseMigrationNumber('473_bg_sky_calendar.sql')).toBe(473)
    expect(parseMigrationNumber('0001_brahma_baseline.sql')).toBe(1)
    expect(parseMigrationNumber('001_baseline.sql')).toBe(1)
  })

  it('scores the letter-suffix form as a claim on its base number (the 346a bypass)', () => {
    // Both forms exist on main. If `346a` parsed to null it would sit outside the sequence, and
    // `474a_anything.sql` would be a one-character way to walk past this guard.
    expect(parseMigrationNumber('346a_drop_legacy_mimamsa.sql')).toBe(346)
    expect(parseMigrationNumber('0000b_seed_legacy_v2.sql')).toBe(0)
  })

  it('returns null for the unnumbered legacy files so they cannot claim a number', () => {
    // 27 such files live in platform/migrations/ (brahma_*, ws2_*, v13_*).
    expect(parseMigrationNumber('brahma_kala_timeline.sql')).toBeNull()
    expect(parseMigrationNumber('ws2_l0_ontology.sql')).toBeNull()
    expect(parseMigrationNumber('v13_pyramid_layers.sql')).toBeNull()
  })
})

describe('computeNextMigrationNumber — the corrected max()-across-BOTH rule', () => {
  it('takes the max across both directories, not the max of either one alone', () => {
    const entries = [
      entry('platform/migrations/474_asset_throughput_incomplete_state.sql'),
      entry('platform/supabase/migrations/473_bg_sky_calendar.sql'),
    ]
    // Reading only platform/supabase/migrations/ would answer 474 — already taken. That single
    // arithmetic error is the whole 467-claimed-twice defect.
    expect(computeNextMigrationNumber(entries)).toBe(475)
    expect(
      computeNextMigrationNumber(entries.filter(e => e.dir === 'platform/supabase/migrations'))
    ).toBe(474)
  })
})

describe('collectNumberedMigrations', () => {
  it('reads both directories and ignores subdirectories and unnumbered files', () => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'migguard-'))
    for (const d of MIGRATION_DIRS) fs.mkdirSync(path.join(tmp, d), { recursive: true })
    fs.writeFileSync(path.join(tmp, 'platform/migrations/100_a.sql'), '')
    fs.writeFileSync(path.join(tmp, 'platform/migrations/brahma_unnumbered.sql'), '')
    fs.writeFileSync(path.join(tmp, 'platform/migrations/notes.md'), '')
    fs.mkdirSync(path.join(tmp, 'platform/supabase/migrations/_archive'), { recursive: true })
    fs.writeFileSync(path.join(tmp, 'platform/supabase/migrations/_archive/099_old.sql'), '')
    fs.writeFileSync(path.join(tmp, 'platform/supabase/migrations/101_b.sql'), '')

    const found = collectNumberedMigrations(tmp).map(e => e.relPath).sort()
    expect(found).toEqual([
      'platform/migrations/100_a.sql',
      'platform/supabase/migrations/101_b.sql',
    ])
    fs.rmSync(tmp, { recursive: true, force: true })
  })
})

describe('the real repository', () => {
  const result = runGuard(REPO_ROOT)

  it('has NO new migration-number collision (the guard must be green on main)', () => {
    expect(result.errors).toEqual([])
  })

  it('still carries exactly the frozen legacy collisions — no more, no fewer', () => {
    const baseline = loadBaseline(REPO_ROOT)
    expect(Object.keys(result.duplicateGroups).sort()).toEqual(
      Object.keys(baseline.legacy_duplicate_groups).sort()
    )
  })

  it('finds numbered migrations in BOTH directories (a one-directory scan would be a silent pass)', () => {
    for (const dir of MIGRATION_DIRS) {
      expect(result.entries.filter(e => e.dir === dir).length).toBeGreaterThan(0)
    }
  })
})

describe('CAN-FAIL — every hard-failure class goes red on a synthetic collision', () => {
  const baseline = loadBaseline(REPO_ROOT)
  const real = collectNumberedMigrations(REPO_ROOT)

  it('E2 — a number free in supabase/ but TAKEN in platform/migrations/ (the cross-dir blind spot)', () => {
    // 474 exists today ONLY in platform/migrations/. A check that scanned just
    // platform/supabase/migrations/ — the "active" directory the README points authors at —
    // would wave this straight through.
    const supabaseNumbers = new Set(
      real.filter(e => e.dir === 'platform/supabase/migrations').map(e => e.number)
    )
    const platformNumbers = new Set(
      real.filter(e => e.dir === 'platform/migrations').map(e => e.number)
    )
    expect(platformNumbers.has(474)).toBe(true)
    expect(supabaseNumbers.has(474)).toBe(false)

    const mutated = [...real, entry('platform/supabase/migrations/474_synthetic_collision.sql')]
    const out = checkMigrationNumbers(mutated, baseline)
    expect(out.errors.some(e => e.startsWith('[E2 NEW-COLLISION]') && e.includes('474'))).toBe(true)
  })

  it('E2 — the mirror case: a number free in platform/migrations/ but taken in supabase/', () => {
    const mutated = [...real, entry('platform/migrations/473_synthetic_collision.sql')]
    const out = checkMigrationNumbers(mutated, baseline)
    expect(out.errors.some(e => e.startsWith('[E2 NEW-COLLISION]') && e.includes('473'))).toBe(true)
  })

  it('E2 — a duplicate WITHIN one directory also fails', () => {
    const mutated = [...real, entry('platform/supabase/migrations/470_second_claim.sql')]
    const out = checkMigrationNumbers(mutated, baseline)
    expect(out.errors.some(e => e.startsWith('[E2 NEW-COLLISION]') && e.includes('470'))).toBe(true)
  })

  it('E1 — an identical filename in both directories fails (migrate.ts would silently skip one)', () => {
    const mutated = [
      ...real,
      entry('platform/migrations/473_bg_sky_calendar.sql'), // same basename as the supabase file
    ]
    const out = checkMigrationNumbers(mutated, baseline)
    expect(out.errors.some(e => e.startsWith('[E1 SILENT-SKIP]'))).toBe(true)
  })

  it('E3 — the letter-suffix form cannot be used to dodge a taken number', () => {
    const mutated = [...real, entry('platform/migrations/474a_sneaky.sql')]
    const out = checkMigrationNumbers(mutated, baseline)
    expect(out.errors.some(e => e.includes('474') && e.includes('474a_sneaky.sql'))).toBe(true)
  })

  it('E3 — a legacy collision is not cover for a new one', () => {
    // 466 is a baselined legacy group of two. Adding a third file to it must still fail.
    expect(baseline.legacy_duplicate_groups['466']).toHaveLength(2)
    const mutated = [...real, entry('platform/supabase/migrations/466_third_claim.sql')]
    const out = checkMigrationNumbers(mutated, baseline)
    expect(out.errors.some(e => e.startsWith('[E3 WIDENED-LEGACY-GROUP]') && e.includes('466'))).toBe(
      true
    )
  })

  it('the failure message names the correct replacement number', () => {
    const mutated = [...real, entry('platform/supabase/migrations/474_synthetic_collision.sql')]
    const out = checkMigrationNumbers(mutated, baseline)
    expect(out.errors.join('\n')).toContain('Renumber the NEW file to 475')
  })
})

describe('advisory band — reported, never fatal (Dvārapāla RULING 44)', () => {
  const result = runGuard(REPO_ROOT)
  const headerWarnings = result.warnings.filter(w => w.includes('header-mismatch'))

  it('header/filename mismatches NEVER contribute to errors', () => {
    // RULING 44: 17 mismatches predate this campaign. A blocking check would turn main red on
    // merge and read as a regression this PR introduced. This assertion is the enforcement.
    expect(headerWarnings.length).toBeGreaterThan(0)
    expect(result.errors).toEqual([])
    // Deliberately NOT asserting a specific filename: lane B-MIG474-COMMENT is fixing
    // 474_asset_throughput_incomplete_state.sql, and this suite must not go red when it lands.
  })

  it('scans whole files, not a prefix — 227 (line 24) and 237 (line 10) declare late', () => {
    // A 5-line window found 15 of 17. An advisory that under-counts invites the reader to treat
    // the list as complete, so the scan window is the whole file.
    const joined = headerWarnings.join('\n')
    for (const late of ['227_ga_structural_floor_update.sql', '237_drop_signal_type_registry.sql']) {
      expect(joined).toContain(late)
    }
  })

  it('does not score a PROSE reference to another migration as a mismatch', () => {
    // 183_bg_texts_and_text_dependent_floors.sql contains "never set by migration 174 or 179" in
    // running text and has no `-- Migration N` declaration. A looser grep reports it as a
    // mismatch; it is not one.
    expect(headerWarnings.join('\n')).not.toContain('183_bg_texts_and_text_dependent_floors.sql')
  })
})
