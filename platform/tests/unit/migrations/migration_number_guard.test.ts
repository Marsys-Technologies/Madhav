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
  collectOwnerPathMigrations,
  OWNER_PATH_ROOT,
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

  it('still carries exactly the frozen legacy collisions PLUS disclosed additions — no more, no fewer', () => {
    // RULING 70: a collision found live on `main` after the freeze (484, ṢAḌ-DARŚANA, not owned
    // by SAMĀPTI) is not folded into the immutable `legacy_duplicate_groups` baseline — it is
    // recorded separately in `disclosed_additions`, itemized/dated/attributed. The real repo's
    // duplicate-number set must equal the UNION of both, not `legacy_duplicate_groups` alone.
    const baseline = loadBaseline(REPO_ROOT)
    const expectedKeys = [
      ...Object.keys(baseline.legacy_duplicate_groups),
      ...Object.keys(baseline.disclosed_additions ?? {}),
    ].sort()
    expect(Object.keys(result.duplicateGroups).sort()).toEqual(expectedKeys)
  })

  it('the 484 collision is present ONLY in disclosed_additions, never folded into the frozen legacy baseline', () => {
    // The whole point of RULING 70's third option: a post-freeze, not-owned collision must NOT
    // be smuggled into the immutable `legacy_duplicate_groups` list — that would be indistinguishable
    // from silently widening the baseline, exactly what the freeze exists to prevent.
    const baseline = loadBaseline(REPO_ROOT)
    expect(baseline.legacy_duplicate_groups['484']).toBeUndefined()
    expect(baseline.disclosed_additions?.['484']).toBeDefined()
  })

  it('the 484 disclosure is fully itemized — owner, date, and ruling are all named, not vague', () => {
    const baseline = loadBaseline(REPO_ROOT)
    const disclosed = baseline.disclosed_additions?.['484']
    expect(disclosed).toBeDefined()
    expect(disclosed?.owner).toBe('ṢAḌ-DARŚANA')
    expect(disclosed?.landed_at).toBe('2026-07-30')
    expect(disclosed?.disclosed_via).toContain('RULING 70')
    expect(disclosed?.fixed_by_samapti).toBe(false)
    expect(disclosed?.files.sort()).toEqual([
      'platform/supabase/migrations/484_bg_muhurta_lattice.sql',
      'platform/supabase/migrations/484_bg_synthetic_cohort_md.sql',
    ])
  })

  it('the disclosure is visible, not hidden — surfaces as a warning even though it does not fail CI', () => {
    // "disclosed not hidden" (Ruling 70's own phrase): the guard must still SAY something about
    // 484 even while passing, so a reader of CI output sees it without having to open the JSON.
    expect(result.warnings.some(w => w.includes('[disclosed-residual]') && w.includes('484'))).toBe(
      true
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
    // Computed, not hardcoded: the real repo's max climbs as new migrations land (485 as of
    // ṢAḌ-DARŚANA's 2026-07-30 batch — see RULING 70), so "the next free number" is whatever
    // computeNextMigrationNumber says TODAY, not whatever it said when this test was written.
    // A hardcoded literal here is exactly the kind of assertion that goes stale silently.
    const expectedNext = computeNextMigrationNumber(mutated)
    expect(out.errors.join('\n')).toContain(`Renumber the NEW file to ${expectedNext}`)
  })
})

describe('disclosed_additions — RULING 70: exit-clean iff itemized, never a blanket pass', () => {
  const baseline = loadBaseline(REPO_ROOT)
  const real = collectNumberedMigrations(REPO_ROOT)

  it('the 484 disclosure alone is enough for the real repo to pass (sanity check: mechanism does not over-fire)', () => {
    const out = checkMigrationNumbers(real, baseline)
    expect(out.errors).toEqual([])
  })

  it('SANITY CHECK — a SECOND, undisclosed collision still fails even with 484 disclosed', () => {
    // Proves the disclosed_additions mechanism is scoped to exactly the number it names — adding
    // 484 to the baseline must not act as a blanket amnesty for some other, unrelated collision.
    const mutated = [...real, entry('platform/supabase/migrations/470_undisclosed_synthetic.sql')]
    const out = checkMigrationNumbers(mutated, baseline)
    expect(out.errors.some(e => e.startsWith('[E2 NEW-COLLISION]') && e.includes('470'))).toBe(true)
    // ...and the legitimately-disclosed 484 is still not re-flagged alongside it.
    expect(out.errors.some(e => e.includes('484'))).toBe(false)
  })

  it('a THIRD file added to the disclosed 484 group fails (E3, same as a legacy group)', () => {
    const mutated = [...real, entry('platform/supabase/migrations/484_sneaky_third_claim.sql')]
    const out = checkMigrationNumbers(mutated, baseline)
    expect(
      out.errors.some(e => e.startsWith('[E3 WIDENED-DISCLOSED-GROUP]') && e.includes('484'))
    ).toBe(true)
  })

  it('E4 — a disclosed_additions entry missing a required field is treated as UNDISCLOSED, not a partial pass', () => {
    for (const missingField of ['owner', 'landed_at', 'disclosed_via', 'fixed_by_samapti', 'files'] as const) {
      const incomplete = JSON.parse(JSON.stringify(baseline)) as typeof baseline
      const entry484 = incomplete.disclosed_additions!['484']
      delete (entry484 as unknown as Record<string, unknown>)[missingField]
      const out = checkMigrationNumbers(real, incomplete)
      expect(
        out.errors.some(e => e.startsWith('[E4 INCOMPLETE-DISCLOSURE]') && e.includes('484')),
        `expected E4 when "${missingField}" is missing`
      ).toBe(true)
    }
  })

  it('E4 — an empty files array also counts as incomplete (itemization means non-empty, named files)', () => {
    const incomplete = JSON.parse(JSON.stringify(baseline)) as typeof baseline
    incomplete.disclosed_additions!['484'].files = []
    const out = checkMigrationNumbers(real, incomplete)
    expect(out.errors.some(e => e.startsWith('[E4 INCOMPLETE-DISCLOSURE]') && e.includes('484'))).toBe(
      true
    )
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

// ── OWNER-PATH SCAN (N-95) ─────────────────────────────────────────────────────
// Owner-path SQL lives OUTSIDE platform/migrations and platform/supabase/migrations (migrate.ts
// never reads it), under 00_ARCHITECTURE/briefs/suvarna/exec/<package>/. Its numbers (1265, 1272,
// 1273, 1274 ...) are still drawn from the SAME sequence, so they must never equal a routine number
// nor each other. Convention-driven: ANY `NNNN_*.sql` (exactly four digits) under OWNER_PATH_ROOT.
describe('OWNER-PATH SCAN — owner-path numbers cannot collide with routine or each other', () => {
  const baseline = loadBaseline(REPO_ROOT)
  const real = collectNumberedMigrations(REPO_ROOT)

  function makeTree(files: string[]): string {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'migguard-owner-'))
    for (const f of files) {
      fs.mkdirSync(path.dirname(path.join(tmp, f)), { recursive: true })
      fs.writeFileSync(path.join(tmp, f), '')
    }
    return tmp
  }
  const O = OWNER_PATH_ROOT

  it('convention: the owner-path root is the suvarna exec package folder', () => {
    expect(OWNER_PATH_ROOT).toBe('00_ARCHITECTURE/briefs/suvarna/exec')
  })

  it('collect: finds NNNN_*.sql at any depth, ignores unnumbered / 2-digit / non-sql files', () => {
    const tmp = makeTree([
      `${O}/dp_builder_privileges/1272_bind_x.sql`,
      `${O}/l5_frozen_guard_1265/sql/1265_l5_guards.sql`,
      `${O}/l5_frozen_guard_1265/sql/verify_before_apply.sql`,
      `${O}/mig_1274_life_events_view/tests/schema/00_roles.sql`,
      `${O}/mig_1274_life_events_view/mig_1274_exec.py`,
      `${O}/ifl2/ti_l2_06_queries.sql`,
      `${O}/dp_builder_privileges/live_defs/bind.LIVE.sql`,
    ])
    try {
      const found = collectOwnerPathMigrations(tmp).map(e => `${e.number}:${e.relPath}`).sort()
      expect(found).toEqual([
        `1265:${O}/l5_frozen_guard_1265/sql/1265_l5_guards.sql`,
        `1272:${O}/dp_builder_privileges/1272_bind_x.sql`,
      ])
    } finally {
      fs.rmSync(tmp, { recursive: true, force: true })
    }
  })

  it('collect: a missing owner-path root yields an empty set (main today has no numbered owner SQL)', () => {
    const tmp = makeTree(['platform/migrations/100_a.sql'])
    try {
      expect(collectOwnerPathMigrations(tmp)).toEqual([])
    } finally {
      fs.rmSync(tmp, { recursive: true, force: true })
    }
  })

  it('PASS — the numbers that exist today (1265, 1272, 1273, 1274, rollback companions included) are accepted', () => {
    const tmp = makeTree([
      `${O}/l5_frozen_guard_1265/sql/1265_l5_frozen_row_guards.sql`,
      `${O}/l5_frozen_guard_1265/sql/1265_l5_frozen_row_guards.ROLLBACK.sql`,
      `${O}/dp_builder_privileges/1272_bind_l2_exact_inputs_builder_reads_shadows.sql`,
      `${O}/dp_builder_privileges/1273_builder_execute_bodha_identity_functions.sql`,
      `${O}/mig_1274_life_events_view/1274_life_events_chart_scoped_view.sql`,
      `${O}/mig_1274_life_events_view/1274_life_events_chart_scoped_view_ROLLBACK.sql`,
    ])
    try {
      const owner = collectOwnerPathMigrations(tmp)
      expect([...new Set(owner.map(e => e.number))].sort()).toEqual([1265, 1272, 1273, 1274])
      const out = checkMigrationNumbers(real, baseline, { ownerEntries: owner })
      expect(out.errors).toEqual([])
    } finally {
      fs.rmSync(tmp, { recursive: true, force: true })
    }
  })

  it('E5 — an owner-path number equal to a ROUTINE number fails (both directories)', () => {
    const routineHighest = Math.max(...real.map(e => e.number))
    const routineNumbers = new Set(real.map(e => e.number))
    const taken = real.find(e => e.dir === 'platform/supabase/migrations')!.number
    expect(routineNumbers.has(taken)).toBe(true)
    for (const n of [taken, routineHighest]) {
      const owner = [entry(`${O}/pkg_a/${String(n).padStart(4, '0')}_owner_claim.sql`)]
      const out = checkMigrationNumbers(real, baseline, { ownerEntries: owner })
      expect(
        out.errors.some(e => e.startsWith('[E5 OWNER-VS-ROUTINE]') && e.includes(String(n))),
        `owner ${n} vs routine`
      ).toBe(true)
    }
  })

  it('E5 — a routine migration landing on an owner-path number fails (the 1272 scenario)', () => {
    const owner = [entry(`${O}/dp_builder_privileges/1272_bind_x.sql`)]
    const routine = [...real, entry('platform/supabase/migrations/1272_routine_took_it.sql')]
    const out = checkMigrationNumbers(routine, baseline, { ownerEntries: owner })
    expect(out.errors.some(e => e.startsWith('[E5 OWNER-VS-ROUTINE]') && e.includes('1272'))).toBe(true)
  })

  it('E6 — two owner-path files claiming the same number in DIFFERENT packages fail', () => {
    const owner = [
      entry(`${O}/pkg_a/9975_first.sql`),
      entry(`${O}/pkg_b/9975_second.sql`),
    ]
    const out = checkMigrationNumbers(real, baseline, { ownerEntries: owner })
    expect(out.errors.some(e => e.startsWith('[E6 OWNER-DUPLICATE]') && e.includes('9975'))).toBe(true)
  })

  it('E6 — two distinct forward files with one number inside ONE package also fail', () => {
    const owner = [
      entry(`${O}/pkg_a/9975_first.sql`),
      entry(`${O}/pkg_a/9975_second.sql`),
    ]
    const out = checkMigrationNumbers(real, baseline, { ownerEntries: owner })
    expect(out.errors.some(e => e.startsWith('[E6 OWNER-DUPLICATE]') && e.includes('9975'))).toBe(true)
  })

  it('a ROLLBACK companion of a forward file is NOT a second claim, but an ORPHAN rollback still claims its number', () => {
    const paired = [
      entry(`${O}/pkg_a/9975_x.sql`),
      entry(`${O}/pkg_a/9975_x_ROLLBACK.sql`),
      entry(`${O}/pkg_b/sql/9976_y.sql`),
      entry(`${O}/pkg_b/sql/9976_y.ROLLBACK.sql`),
    ]
    expect(checkMigrationNumbers(real, baseline, { ownerEntries: paired }).errors).toEqual([])

    // Orphan rollback (no forward sibling in its folder) colliding with a routine number fails.
    const taken = real.find(e => e.dir === 'platform/migrations')!.number
    const orphan = [entry(`${O}/pkg_c/${String(taken).padStart(4, '0')}_z_ROLLBACK.sql`)]
    const out = checkMigrationNumbers(real, baseline, { ownerEntries: orphan })
    expect(out.errors.some(e => e.startsWith('[E5 OWNER-VS-ROUTINE]'))).toBe(true)
  })

  it('owner-path numbers feed the allocator: next free number skips every claimed owner number', () => {
    const owner = [entry(`${O}/pkg_a/9000_far_ahead.sql`)]
    const out = checkMigrationNumbers(real, baseline, { ownerEntries: owner })
    expect(out.nextNumber).toBe(9001)
    expect(out.errors).toEqual([])
  })

  // ── REVIEW_3067 follow-ups (MED-1, LOW-1, NIT-2) ────────────────────────────
  it('MED-1 — numbered LIVE captures and verify scripts are NOT claims (collect excludes them)', () => {
    const tmp = makeTree([
      `${O}/pkg_a/1272_x.sql`,
      `${O}/pkg_a/1272_x.LIVE.sql`,
      `${O}/pkg_a/1272_x.live.sql`,
      `${O}/pkg_a/1272_verify_after_apply.sql`,
      `${O}/pkg_a/1272_verify_before_apply.sql`,
      `${O}/pkg_a/1272.verify-before-apply.sql`,
    ])
    try {
      const owner = collectOwnerPathMigrations(tmp)
      expect(owner.map(e => e.filename)).toEqual(['1272_x.sql'])
      expect(checkMigrationNumbers(real, baseline, { ownerEntries: owner }).errors).toEqual([])
    } finally {
      fs.rmSync(tmp, { recursive: true, force: true })
    }
  })

  it('MED-1 — the exclusion is NARROW (the real conventions only): other verify/live-ish names stay claims', () => {
    // A broad "verify"/"live" exclusion would let a genuine migration such as
    // 1273_verify_grants.sql or 1274_go_live.sql walk past the guard.
    const tmp = makeTree([
      `${O}/pkg_a/1272_verifier_grants.sql`,
      `${O}/pkg_a/1273_verify_grants.sql`,
      `${O}/pkg_a/1274_go_live.sql`,
      `${O}/pkg_a/1275_deliver_live_rows.sql`,
    ])
    try {
      expect(collectOwnerPathMigrations(tmp).map(e => e.number).sort()).toEqual([1272, 1273, 1274, 1275])
    } finally {
      fs.rmSync(tmp, { recursive: true, force: true })
    }
  })

  it('NIT-2 — a numbered file directly in the exec root (depth 0) is a claim', () => {
    const tmp = makeTree([`${O}/1272_root_level.sql`])
    try {
      expect(collectOwnerPathMigrations(tmp).map(e => e.relPath)).toEqual([`${O}/1272_root_level.sql`])
    } finally {
      fs.rmSync(tmp, { recursive: true, force: true })
    }
  })

  it('NIT-2 — lowercase / mixed-case rollback suffixes are companions too', () => {
    const owner = [
      entry(`${O}/pkg_a/9975_x.sql`),
      entry(`${O}/pkg_a/9975_x.rollback.sql`),
      entry(`${O}/pkg_b/9976_y.sql`),
      entry(`${O}/pkg_b/9976_y_Rollback.sql`),
    ]
    expect(checkMigrationNumbers(real, baseline, { ownerEntries: owner }).errors).toEqual([])
  })

  it('LOW-1 — a FORWARD file merely named "rollback_*" is a real claim: two forwards on one number fail', () => {
    const owner = [entry(`${O}/pkg_a/1272_a.sql`), entry(`${O}/pkg_a/1272_rollback_guard.sql`)]
    const out = checkMigrationNumbers(real, baseline, { ownerEntries: owner })
    expect(out.errors.some(e => e.startsWith('[E6 OWNER-DUPLICATE]') && e.includes('1272'))).toBe(true)
  })

  it('LOW-1 — such a forward file plus its true rollback is still ONE claim', () => {
    const owner = [
      entry(`${O}/pkg_a/1272_rollback_guard.sql`),
      entry(`${O}/pkg_a/1272_rollback_guard_ROLLBACK.sql`),
    ]
    expect(checkMigrationNumbers(real, baseline, { ownerEntries: owner }).errors).toEqual([])
  })

  it('LOW-1 — only the _ROLLBACK / .ROLLBACK suffix convention pairs: _undo / _down names are separate claims', () => {
    for (const undo of ['1272_a_undo.sql', '1272_a_down.sql', '1272_a.revert.sql']) {
      const owner = [entry(`${O}/pkg_a/1272_a.sql`), entry(`${O}/pkg_a/${undo}`)]
      const out = checkMigrationNumbers(real, baseline, { ownerEntries: owner })
      expect(out.errors.some(e => e.startsWith('[E6 OWNER-DUPLICATE]')), undo).toBe(true)
    }
  })

  it('LOW-1 — a rollback needs a forward file with the MATCHING STEM in the SAME folder, else it is an orphan claim', () => {
    // different folder
    let owner = [entry(`${O}/pkg_a/1265_x.sql`), entry(`${O}/pkg_a/rollback/1265_x.ROLLBACK.sql`)]
    expect(
      checkMigrationNumbers(real, baseline, { ownerEntries: owner }).errors.some(e =>
        e.startsWith('[E6 OWNER-DUPLICATE]')
      )
    ).toBe(true)
    // same folder, different stem
    owner = [entry(`${O}/pkg_a/1265_x.sql`), entry(`${O}/pkg_a/1265_other_ROLLBACK.sql`)]
    expect(
      checkMigrationNumbers(real, baseline, { ownerEntries: owner }).errors.some(e =>
        e.startsWith('[E6 OWNER-DUPLICATE]')
      )
    ).toBe(true)
  })

  it('runGuard WIRING — an end-to-end tree with an owner/routine clash goes red; a clean one stays green', () => {
    const baselineRel = 'platform/scripts/ci/migration_number_legacy_duplicates.json'
    const bad = makeTree([
      'platform/migrations/100_a.sql',
      'platform/supabase/migrations/1272_routine_took_it.sql',
      `${O}/dp_builder_privileges/1272_bind_x.sql`,
    ])
    const good = makeTree([
      'platform/migrations/100_a.sql',
      `${O}/dp_builder_privileges/1272_bind_x.sql`,
    ])
    try {
      for (const t of [bad, good]) {
        fs.mkdirSync(path.join(t, path.dirname(baselineRel)), { recursive: true })
        fs.copyFileSync(path.join(REPO_ROOT, baselineRel), path.join(t, baselineRel))
      }
      expect(runGuard(bad).errors.some(e => e.startsWith('[E5 OWNER-VS-ROUTINE]'))).toBe(true)
      expect(runGuard(good).errors).toEqual([])
      expect(runGuard(good).nextNumber).toBe(1273)
    } finally {
      fs.rmSync(bad, { recursive: true, force: true })
      fs.rmSync(good, { recursive: true, force: true })
    }
  })

  it('the real repo (owner-path folders absent or collision-free) passes with the owner scan on', () => {
    const out = runGuard(REPO_ROOT)
    expect(out.errors).toEqual([])
    expect(out.ownerEntries).toEqual(collectOwnerPathMigrations(REPO_ROOT))
  })
})
