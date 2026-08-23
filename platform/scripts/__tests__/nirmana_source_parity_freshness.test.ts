import { describe, it, expect } from 'vitest'
import { spawnSync } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'

// ═══════════════════════════════════════════════════════════════════════════════════════
// REGRESSION COVERAGE FOR THE FOSSIL GATE — Nirmāṇa M0-T43 (Standing Queue SQ-04)
//
// WHAT DEFECT THIS PINS. Before M0-T42, `check_asset_source_parity.py` run with no
// `--registry` read a dated snapshot, printed six PASS rules, and EXITED 0 — a green
// produced from data hours out of date, with no `staleness` key anywhere in its `--json`.
// That is CLAUDE.md §N.8's defect class (a status with no detector behind the thing it
// claims) sitting inside the mechanism built to catch it.
//
// WHY THESE TESTS AND NOT THE SELF-TEST. The guard carries its own `--self-test` probes,
// and they are good ones. But they live INSIDE the file they test: a change that deletes
// the schema-behind case from `staleness_wiring_probe()` — or deletes the probe's call
// site in `self_test()` — leaves `--self-test` exiting 0 with the coverage gone. These
// tests drive the guard from OUTSIDE, as a subprocess, over snapshots this file builds,
// and assert on the process exit code. They therefore survive the probe being edited, and
// they run in the blocking `pnpm test` job rather than in
// `.github/workflows/nirmana-m0-guards.yml`, which is `continue-on-error: true` and does
// not fire on the campaign branch at all.
//
// WOULD THEY HAVE CAUGHT THE ORIGINAL BUG? Every case below except the two boundary cases
// (`exit 0` when genuinely clean, `exit 1` on an ordinary rule failure) returned 0 from the
// pre-M0-T42 guard and asserts a non-zero exit here. Case S2 and case J are the two that
// matter most and are called out where they appear.
//
// NO DATABASE. Every case is a JSON file in a temp dir plus the guard's own shipped
// `pass/clean` writer/seed fixture. `--live` is never invoked.
// ═══════════════════════════════════════════════════════════════════════════════════════

const REPO_ROOT = path.resolve(__dirname, '../../..')
const GUARD = path.join(REPO_ROOT, 'platform/scripts/governance/check_asset_source_parity.py')
const CLEAN = path.join(
  REPO_ROOT,
  'platform/scripts/governance/asset_source_parity_fixtures/pass/clean',
)
const MIGRATIONS = path.join(REPO_ROOT, 'platform/migrations')
const PY = process.env.PYTHON ?? 'python3'

/** Run the guard. No skip path: a missing interpreter is a red with a cause, never a green. */
function runGuard(args: string[]): { status: number; stdout: string; stderr: string } {
  const r = spawnSync(PY, [GUARD, ...args], {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    timeout: 180_000,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
  })
  if (r.error) {
    throw new Error(
      `could not run ${PY} ${GUARD}: ${r.error.message}. These tests deliberately do not ` +
        `skip on a missing interpreter — a skipped guard test is an unearned green (§N.8). ` +
        `Set PYTHON= to a python3 if the default is not on PATH.`,
    )
  }
  return { status: r.status ?? -1, stdout: r.stdout ?? '', stderr: r.stderr ?? '' }
}

/**
 * Columns this checkout's migrations add to asset_registry, re-derived HERE rather than
 * asked of the guard. An oracle that shares the code under test is not an oracle: if
 * `migration_declared_registry_columns()` were mutated to return nothing, every
 * schema-behind case built from its output would go vacuously green.
 */
function declaredColumnsIndependently(): string[] {
  const re =
    /alter\s+table\s+(?:only\s+)?(?:public\.)?asset_registry\s+add\s+column\s+(?:if\s+not\s+exists\s+)?([a-z_][a-z0-9_]*)/gi
  const out = new Set<string>()
  for (const f of fs.readdirSync(MIGRATIONS).filter((n) => n.endsWith('.sql')).sort()) {
    const flat = fs.readFileSync(path.join(MIGRATIONS, f), 'utf8').split(/\s+/).join(' ')
    for (const m of flat.matchAll(re)) out.add(m[1].toLowerCase())
  }
  return [...out].sort()
}

const DECLARED = declaredColumnsIndependently()

function tmpSnapshot(doc: unknown): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'm0t43-'))
  const p = path.join(dir, 'registry.json')
  fs.writeFileSync(p, JSON.stringify(doc), 'utf8')
  return p
}

/** Minutes/hours ago, as the ISO-8601 the guard parses out of `_meta.read_at`. */
const hoursAgo = (h: number) => new Date(Date.now() - h * 3_600_000).toISOString()

function snapshot(opts: {
  readAt?: string | null
  columns?: string[]
  assets?: string[]
}): unknown {
  const doc: Record<string, unknown> = {
    registry_columns: opts.columns ?? [...DECLARED, 'asset_id'],
    assets: (opts.assets ?? ['bg_one', 'bg_two']).map((a) => ({ asset_id: a })),
  }
  if (opts.readAt !== null) doc._meta = { read_at: opts.readAt ?? hoursAgo(0.08) }
  return doc
}

function overFixture(snapPath: string, extra: string[] = []) {
  return runGuard([
    '--registry',
    snapPath,
    '--writer-root',
    path.join(CLEAN, 'writers'),
    '--seed',
    path.join(CLEAN, 'seed.ts'),
    ...extra,
  ])
}

describe('the schema-behind and age detectors are two INDEPENDENT routes to stale', () => {
  it('the oracle is not vacuous — this checkout really does declare asset_registry columns', () => {
    // If this ever legitimately goes empty (every ADD COLUMN migration squashed away), the
    // schema-behind cases below become untestable and must be REMOVED, not left passing
    // over nothing. Failing here is the signal to do that deliberately.
    expect(DECLARED.length).toBeGreaterThan(0)
    // And the guard must agree it can see at least what this file can see. A mutation that
    // empties `migration_declared_registry_columns()` is caught right here, before any case
    // built on it could go quietly green.
    const j = JSON.parse(overFixture(tmpSnapshot(snapshot({})), ['--json']).stdout)
    for (const c of DECLARED) {
      expect(j.staleness.migration_declared_columns).toContain(c)
    }
  }, 180_000)

  it('S1 — AGE alone: schema-current but 100h old ⇒ refuses (exit 3)', () => {
    // The age route in isolation. Pre-M0-T42 this exited 0.
    const r = overFixture(tmpSnapshot(snapshot({ readAt: hoursAgo(100) })))
    expect(r.status).toBe(3)
    expect(r.stderr).toMatch(/REGISTRY SNAPSHOT STALE/)
    const j = JSON.parse(overFixture(tmpSnapshot(snapshot({ readAt: hoursAgo(100) })), ['--json']).stdout)
    expect(j.staleness.age_exceeded).toBe(true)
    // …and it got there by AGE, not by the other detector. Asserting only `stale` would let
    // a mutation that deletes the age branch pass on the schema branch's verdict.
    expect(j.staleness.schema_behind_columns).toEqual([])
  }, 180_000)

  it('S2 — SCHEMA-BEHIND alone: FIVE MINUTES old but missing a migration-declared column ⇒ refuses (exit 3)', () => {
    // ══ THE CASE THAT MATTERS MOST ══
    // M0-T42's own report names this hole: every case in its first probe reached the stale
    // verdict by the AGE route, so the schema-behind detector — the one that actually fires
    // on the real shipped baseline, which is only ~4h old and comfortably inside the 24h
    // threshold — was untested. A snapshot young enough to sail through the age check and
    // provably behind a migration sitting in the same checkout is the ONLY input that
    // isolates it. Delete the schema-behind proof and this is the test that goes red.
    const behind = [...DECLARED.slice(1), 'asset_id']
    const r = overFixture(tmpSnapshot(snapshot({ readAt: hoursAgo(0.08), columns: behind })))
    expect(r.status).toBe(3)
    const j = JSON.parse(
      overFixture(tmpSnapshot(snapshot({ readAt: hoursAgo(0.08), columns: behind })), ['--json']).stdout,
    )
    expect(j.staleness.age_exceeded).toBe(false)      // the age route did NOT fire
    expect(j.staleness.age_hours).toBeLessThan(1)
    expect(j.staleness.schema_behind_columns).toEqual([DECLARED[0]])
    expect(j.staleness.stale).toBe(true)
  }, 180_000)

  it('S3 — the gate is not stuck on: fresh AND schema-current ⇒ exit 0', () => {
    // The other boundary. A detector that reports everything as stale gates nothing, it
    // just stops being read. Without this case, S1/S2 are satisfied by `return 3`.
    const r = overFixture(tmpSnapshot(snapshot({})))
    expect(r.status).toBe(0)
    const j = JSON.parse(overFixture(tmpSnapshot(snapshot({})), ['--json']).stdout)
    expect(j.staleness.stale).toBe(false)
    // Never the word "fresh": neither detector can prove currency, only its absence.
    expect(JSON.stringify(j.staleness)).not.toMatch(/"fresh"/)
  }, 180_000)

  it('S4 — an unreadable registry leg is stale, and reports the RIGHT cause', () => {
    // The generic detector reaches `stale` here anyway, via the absent `read_at` — so
    // asserting only the verdict lets the branch be deleted (M0-T42 measured exactly that,
    // mutation M5). Reporting that there was NO SNAPSHOT, rather than a snapshot with no
    // timestamp, is this branch's entire contribution, so that is what is asserted.
    const missing = path.join(os.tmpdir(), 'm0t43-does-not-exist-' + Date.now() + '.json')
    const r = overFixture(missing)
    expect(r.status).toBe(3)
    const j = JSON.parse(overFixture(missing, ['--json']).stdout)
    expect(j.staleness.registry_unreadable).toBeTruthy()
    expect(j.staleness.reasons.join(' ')).toMatch(/could not be read at all/)
    // and "not measured" is not "agreed" — the rules over that leg go not_checkable.
    expect(j.rules['P-02'].status).toBe('not_checkable')
    expect(j.rules['P-03'].status).toBe('not_checkable')
  }, 180_000)
})

describe('exit-code precedence: a PASS over a fossil is not a weaker pass', () => {
  it('J — stale AND a real rule failure ⇒ 3, not 1', () => {
    // Order is the claim. If the rule verdict outranked staleness, this would be 1 — and a
    // reader would act on a diff computed against the wrong data believing it was merely a
    // known failure. `bg_orphan` is in the registry leg and in neither the writers nor the
    // seed, which is P-03.
    const doc = snapshot({ readAt: hoursAgo(100), assets: ['bg_one', 'bg_two', 'bg_orphan'] })
    const r = overFixture(tmpSnapshot(doc))
    expect(r.status).toBe(3)
    const j = JSON.parse(overFixture(tmpSnapshot(doc), ['--json']).stdout)
    expect(j.rules['P-03'].status).toBe('fail')       // the failure is still REPORTED…
    expect(j.rules['P-03'].violation_count).toBe(1)   // …in full, not suppressed by the gate
  }, 180_000)

  it('K — an ordinary rule failure on a FRESH snapshot ⇒ 1', () => {
    // Proves 3 is not the universal answer and that the six parity rules still work at all.
    // Without this, `exit_code` could be `return 3 if rules_failed else 0` and J still pass.
    const doc = snapshot({ assets: ['bg_one', 'bg_two', 'bg_orphan'] })
    const r = overFixture(tmpSnapshot(doc))
    expect(r.status).toBe(1)
  }, 180_000)
})

describe('the DEFAULT invocation — what CI actually runs — measures freshness at all', () => {
  it('L — a bare `--json` run carries a populated staleness measurement', () => {
    // F-T40-1 in its purest form: CI passes no `--registry`, so CI reads the dated baseline,
    // and the pre-fix guard emitted NO staleness key anywhere in this output while
    // `_meta.registry.read_at` was already being carried into the report unread.
    //
    // Deliberately NOT asserting the baseline's current verdict. It is stale today (missing
    // migration 590's four columns) and regenerating it is an operator sequencing decision;
    // a test that pinned `exit 3` here would turn a correct operator action into a red. What
    // is asserted is the durable property: the default path MEASURES, and reports what it
    // measured.
    const r = runGuard(['--json'])
    const j = JSON.parse(r.stdout)
    expect(j.staleness).toBeTruthy()
    expect(j.staleness.mode).toBe('snapshot')
    expect(j.staleness.enforced).toBe(true)          // snapshot mode is enforced; --live is not
    expect(j.staleness).toHaveProperty('age_hours')
    expect(j.staleness).toHaveProperty('schema_behind_columns')
    expect(j.staleness).toHaveProperty('max_age_hours')
    expect(Array.isArray(j.staleness.reasons)).toBe(true)
    // And whatever it measured, the exit must agree with it — the one invariant that ties
    // the detector to the verdict for the input CI actually uses.
    if (j.staleness.stale) expect(r.status).toBe(3)
    else expect(r.status).not.toBe(3)
  }, 180_000)

  it('M — loosening --max-age-hours does not silence the schema-behind proof', () => {
    // The documented asymmetry: age is a threshold an operator may set, schema-behind is a
    // proof and is not negotiable. A "fix" that routed both through one tunable would pass
    // every other test in this file.
    const behind = [...DECLARED.slice(1), 'asset_id']
    const p = tmpSnapshot(snapshot({ readAt: hoursAgo(0.08), columns: behind }))
    const r = overFixture(p, ['--max-age-hours', '999999'])
    expect(r.status).toBe(3)
  }, 180_000)
})

describe('the guard\'s own probes still pass, from the blocking test job', () => {
  it('N — `--self-test` exits 0', () => {
    // The self-test is a real, mutation-tested probe set, but its only CI caller is
    // nirmana-m0-guards.yml, which is `continue-on-error: true` and does not run on the
    // campaign branch. This line is what makes those ~20 hand-built expectations actually
    // gate something. It does NOT replace the cases above: it cannot notice its own
    // deletion, which is precisely why they exist separately.
    const r = runGuard(['--self-test'])
    expect(r.stdout + r.stderr).toMatch(/self-test OK/)
    expect(r.status).toBe(0)
  }, 180_000)
})
