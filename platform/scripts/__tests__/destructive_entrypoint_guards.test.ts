/**
 * Entrypoint-guard tests for the five scripts repaired by Nirmāṇa WORK_QUEUE M0-T65
 * (ruling D-74 part 1 — wave 1 of finding F-4 tier 1, triaged in
 * `00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json`):
 *
 *   scripts/probe/ask.ts               execSync `gcloud secrets versions access`, `firebase apps:sdkconfig`
 *   scripts/dedupe_charts.ts           `DELETE FROM charts`
 *   scripts/_archived/seed-abhisek.ts  `ON CONFLICT (id) DO UPDATE SET role='super_admin'`
 *   scripts/dev/mint_session_cookie.ts mints a live super-admin `__session` cookie
 *   scripts/set-password.ts            `auth.updateUser(uid, { password })`
 *
 * Each called `main()` at module top level with NO guard, so IMPORTING any of them ran the
 * program. D-74's reason for taking these five first: "the gap between 'unguarded' and
 * 'catastrophic' is one incidental import."
 *
 * ── THE CONSTRAINT THAT SHAPES THIS FILE ────────────────────────────────────────────────────
 * D-74 parts 2 and 3 forbid EXECUTING any of the five — not to verify, not "just the import",
 * not with a stub env, not in a sandbox — and state that if verifying appears to require
 * executing, the task stops and parks rather than improvising a way to test it. So the proof is
 * deliberately split, and the split is stated rather than blurred:
 *
 *   STRUCTURAL, over the five real files' source text (§1). Proves the guard is present, that it
 *   is the exact `isDirectEntrypoint(import.meta.url, process.argv[1])` form, that the ONLY
 *   top-level `main()` invocation sits inside it, and — since M0-T66 (ruling D-67 part 3) — that
 *   the file defines NO private `isDirectEntrypoint` at all but imports and re-exports THE shared
 *   one in `scripts/lib/entrypoint.ts`. That replaces the original text-equality assertion
 *   against `scripts/seed/asset_registry_seed.ts`'s copy with an identity assertion, which is
 *   what finding F-2 asked for: eight copies that CAN diverge, versus one that cannot. Proven
 *   non-vacuous by paired fixtures in §3: an unguarded sample — including an INDENTED one — must
 *   be rejected by the same helpers that accept the repaired files.
 *
 *   BEHAVIOURAL, over a harmless stand-in that carries the identical idiom (§2), never over the
 *   five. `fixtures/entrypoint_guard_standin.fixture.ts` proves the idiom itself resolves
 *   correctly under this repo's `tsx` for a `platform/scripts/**` ESM `.ts` file, in both
 *   directions and under `NODE_ENV=test`.
 *
 *   NOT PROVEN, and not claimed anywhere: that any of the five behaves correctly when actually
 *   run. Nothing here executes them. A structural match plus a stand-in's behaviour is strictly
 *   weaker than running the real file, and that is the trade D-74 explicitly anticipated.
 *
 * ── WHY THE `isDirectEntrypoint` CONTRACT AND NOT `IMPORT_ONLY` ──────────────────────────────
 * `scripts/ci/dispatch_gate.ts` and `scripts/ci/verify_migrations_deployed.ts` were repaired the
 * other way (M0-T50 / ruling D-49, `scripts/audit/A3_env_matrix.md` Addendum A3.4) because a
 * GATE's hazard is FAILING to run, so its safe default is RUN. All five files here MUTATE or
 * ACQUIRE CREDENTIALS, so their hazard is RUNNING and their safe default is DO NOT RUN — A3.4
 * operator rule 5, and M0-T60's derivation.
 */
import { describe, it, expect } from 'vitest'
import { spawnSync, type SpawnSyncReturns } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'
import { pathToFileURL } from 'url'
// In-process import of the STAND-IN only. None of the five real files is ever imported here.
import {
  isDirectEntrypoint,
  STANDIN_MAIN_MARKER,
  STANDIN_MAIN_EXIT,
} from './fixtures/entrypoint_guard_standin.fixture'

const PLATFORM_DIR = path.resolve(__dirname, '../..')
const TSX = path.join(PLATFORM_DIR, 'node_modules', '.bin', 'tsx')

const GUARD_LINE = 'if (isDirectEntrypoint(import.meta.url, process.argv[1])) {'

function read(rel: string): string {
  return fs.readFileSync(path.join(PLATFORM_DIR, rel), 'utf8')
}

/**
 * ── `TARGETS` IS DERIVED FROM THE MEASUREMENT, NEVER HAND-TYPED (M0-T66, finding F-O) ────────
 *
 * This used to be a five-element string literal — the files M0-T65 repaired. PARĪKṢAKA's
 * V-45..V-52 drain filed **F-O** against exactly that: *"If Wave 2 guards 53 files without
 * extending it, the repo ends with 58 files carrying a guard of which 5 are checked — coverage
 * silently drops from 100% of guarded files to 9%. Hand-extending a 53-entry literal is itself
 * an unverified step."*
 *
 * So the list is now computed, from the same artefact D-67 part 4 makes the ratchet's baseline:
 * `00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json`'s tier-1 records (58 files), FILTERED
 * to those that actually carry the guard today.
 *
 * The filter is what keeps this a pay-down list rather than a permanently-red one (D-39 part 2):
 * an unrepaired tier-1 file carries no guard, so it is not yet asserted about; the instant Wave 2
 * guards it, it enters this set and every assertion below applies to it with no edit here. The
 * set can therefore only GROW, and `COVERAGE_FLOOR` makes a shrink fail.
 */
const TRIAGE = JSON.parse(
  fs.readFileSync(
    path.resolve(PLATFORM_DIR, '..', '00_ARCHITECTURE/autonomy/reports/M0-T64-triage.json'),
    'utf8',
  ),
) as { records: Array<{ file: string; tier: number }> }

/** Repo-relative (`platform/scripts/...`) → platform-relative (`scripts/...`). */
const toPlatformRel = (repoRel: string): string => repoRel.replace(/^platform\//, '')

const TIER1 = TRIAGE.records.filter((r) => r.tier === 1).map((r) => toPlatformRel(r.file))

/** The exact guard form this contract mandates (M0-T60 / A3.4 operator rule 5). */
const carriesGuard = (rel: string): boolean => read(rel).includes(GUARD_LINE)

const TARGETS = TIER1.filter((rel) => fs.existsSync(path.join(PLATFORM_DIR, rel)) && carriesGuard(rel))

/**
 * Coverage may be paid UP, never down. 5 is M0-T65's wave 1; after wave 2 this is 58 and the
 * floor should be raised to match. A derivation that silently returned [] would make every
 * assertion below vacuous, which is the failure mode this constant exists to catch.
 */
const COVERAGE_FLOOR = 5

/**
 * THE one shared implementation (M0-T66, ruling D-67 part 3). Until M0-T66 this constant named
 * `scripts/seed/asset_registry_seed.ts` and the five carried textual COPIES of its predicate,
 * which this suite compared for equality. Finding F-2 was that eight copies of a
 * security-relevant predicate can silently diverge; the copies are gone, so the assertion is
 * now IDENTITY rather than equality — strictly stronger, and it cannot drift by construction.
 */
const REFERENCE = 'scripts/lib/entrypoint.ts'
/** The two files that carried the predicate before M0-T66; both now import it. */
const FORMER_COPIES = ['scripts/migrate.ts', 'scripts/seed/asset_registry_seed.ts'] as const

/**
 * The `isDirectEntrypoint` body, normalised so that a namespace-qualified copy
 * (`path.resolve`, `fs.realpathSync` — `scripts/migrate.ts`) and a named-import copy
 * (`resolve`, `realpathSync` — everywhere else) compare equal. Nothing else is normalised: a
 * changed comparison, a flipped return or a dropped `try` still shows up as a difference.
 */
function predicateBody(src: string): string | null {
  const start = src.indexOf('export function isDirectEntrypoint(')
  if (start === -1) return null
  const open = src.indexOf('{', start)
  let depth = 0
  for (let i = open; i < src.length; i++) {
    if (src[i] === '{') depth++
    else if (src[i] === '}') {
      depth--
      if (depth === 0) {
        return src
          .slice(start, i + 1)
          .replace(/\bfs\./g, '')
          .replace(/\bpath\./g, '')
          .replace(/\s+/g, ' ')
          .trim()
      }
    }
  }
  return null
}

/**
 * True when the file gets `isDirectEntrypoint` from THE shared module rather than defining its
 * own copy — an `import` of the symbol from a `lib/entrypoint` specifier, plus a re-export so
 * the module's public surface is unchanged. (M0-T66 / ruling D-67 part 3.)
 */
function importsSharedPredicate(src: string): boolean {
  const imports = /import\s*\{[^}]*\bisDirectEntrypoint\b[^}]*\}\s*from\s*'[^']*lib\/entrypoint'/.test(src)
  const reexports = /export\s*\{[^}]*\bisDirectEntrypoint\b[^}]*\}/.test(src)
  return imports && reexports
}

/** Lines that INVOKE `main()` (not the declaration) at column 0 — i.e. unguarded top level. */
function unguardedTopLevelMainCalls(src: string): string[] {
  return src
    .split('\n')
    .filter((l) => /^(void\s+|await\s+)?main\s*\(\s*\)/.test(l))
}

/** Lines that invoke `main()` at ANY indentation. */
function allMainCalls(src: string): string[] {
  return src
    .split('\n')
    .filter((l) => /^\s*(void\s+|await\s+)?main\s*\(\s*\)/.test(l))
}

/** True when every `main()` invocation in the source appears after the guard line. */
function everyMainCallIsAfterGuard(src: string): boolean {
  const lines = src.split('\n')
  const guardIdx = lines.findIndex((l) => l.trim() === GUARD_LINE)
  if (guardIdx === -1) return false
  return lines.every(
    (l, i) => !/^\s*(void\s+|await\s+)?main\s*\(\s*\)/.test(l) || i > guardIdx,
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// §1 — STRUCTURAL: the five real files. Read as text; never imported, never executed.
// ─────────────────────────────────────────────────────────────────────────────
describe('M0-T65 §1 — structural: the five destructive scripts carry the guard', () => {
  const referenceBody = predicateBody(read(REFERENCE))

  it('the derived TARGETS list is non-vacuous and has not shrunk (F-O)', () => {
    // Without this, a broken derivation would empty the list and every per-file block below
    // would simply not exist — a green suite asserting nothing, which is the exact shape
    // §N.8 calls an unearned signal.
    expect(TIER1.length).toBe(58) // M0-T64's measured tier-1 population
    expect(TARGETS.length).toBeGreaterThanOrEqual(COVERAGE_FLOOR)
    // Every guarded tier-1 file is covered: coverage is 100% of guarded files by construction,
    // not a list somebody remembered to extend.
    expect(TIER1.filter((rel) => fs.existsSync(path.join(PLATFORM_DIR, rel)) && carriesGuard(rel)))
      .toEqual(TARGETS)
  })

  it('the shared predicate is readable, and NOBODY else defines one', () => {
    // Anchors the whole section: if this fails, every per-file comparison below is vacuous.
    // (This test is the one that caught M0-T66's own rewire: when the predicate moved out of
    // `asset_registry_seed.ts`, `referenceBody` went null and every per-file `toBe(null)`
    // would have passed vacuously. Keep it first and keep it truthy-asserting.)
    expect(referenceBody).toBeTruthy()
    for (const rel of FORMER_COPIES) {
      expect(predicateBody(read(rel))).toBeNull()
      expect(importsSharedPredicate(read(rel))).toBe(true)
    }
  })

  for (const rel of TARGETS) {
    describe(rel, () => {
      const src = read(rel)

      it('has NO unguarded top-level main() call', () => {
        expect(unguardedTopLevelMainCalls(src)).toEqual([])
      })

      it('calls main() exactly once, and only after the guard line', () => {
        expect(allMainCalls(src)).toHaveLength(1)
        expect(everyMainCallIsAfterGuard(src)).toBe(true)
      })

      it('uses the exact isDirectEntrypoint guard form, exactly once', () => {
        const occurrences = src.split(GUARD_LINE).length - 1
        expect(occurrences).toBe(1)
        // Not the CI-gate contract — opposite hazard, opposite default (A3.4 rule 5).
        expect(src).not.toMatch(/process\.env\.IMPORT_ONLY/)
        // Not the retired environment-sentinel form either (ruling D-9 / M0-T60).
        expect(src).not.toMatch(/^\s*if \(process\.env\.NODE_ENV/m)
      })

      it('defines NO private predicate — it imports and re-exports the shared one', () => {
        // M0-T66 / D-67 part 3. Was "body identical to the certified copy"; identity of
        // implementation replaces equality of text, so divergence is now impossible rather
        // than merely detected.
        expect(predicateBody(src)).toBeNull()
        expect(importsSharedPredicate(src)).toBe(true)
      })

      it('the guard block closes at end of file (nothing runs after it)', () => {
        const lines = src.split('\n').filter((l) => l.trim() !== '')
        expect(lines[lines.length - 1].trim()).toBe('}')
      })
    })
  }
})

// ─────────────────────────────────────────────────────────────────────────────
// §2 — BEHAVIOURAL: the identical idiom, on a harmless stand-in. Never on the five.
// ─────────────────────────────────────────────────────────────────────────────
const STANDIN_REL = path.join('scripts', '__tests__', 'fixtures', 'entrypoint_guard_standin.fixture.ts')
const STANDIN_TS = path.join(PLATFORM_DIR, STANDIN_REL)
const tsxPresent = fs.existsSync(TSX)

function runTsx(args: string[], extraEnv: NodeJS.ProcessEnv = {}): SpawnSyncReturns<string> {
  // Constructed from scratch, NOT spread from process.env: nothing this suite spawns may inherit
  // a real credential. The stand-in needs none, and this keeps that true by construction.
  const env: NodeJS.ProcessEnv = {
    PATH: process.env.PATH ?? '',
    HOME: process.env.HOME ?? '',
    ...extraEnv,
  }
  return spawnSync(TSX, args, { cwd: PLATFORM_DIR, env, encoding: 'utf8', timeout: 180_000 })
}

function output(r: SpawnSyncReturns<string>): string {
  return `${r.stdout ?? ''}${r.stderr ?? ''}`
}

/** A throwaway module whose only content is a side-effect import of the stand-in. */
function withImportHarness(fn: (harnessPath: string) => void): void {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nirmana-m0t65-'))
  try {
    const harness = path.join(dir, 'harness.ts')
    fs.writeFileSync(
      harness,
      `import ${JSON.stringify(STANDIN_TS)}\nconsole.log('IMPORT_RETURNED_OK')\n`,
      'utf8',
    )
    fn(harness)
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
}

describe.skipIf(!tsxPresent)('M0-T65 §2 — behavioural: the idiom, proven on a stand-in', () => {
  it('A — importing a module guarded this way does NOT run its main()', () => {
    withImportHarness((harness) => {
      const r = runTsx([harness])
      expect(output(r)).toMatch(/IMPORT_RETURNED_OK/)
      expect(output(r)).not.toMatch(STANDIN_MAIN_MARKER)
      // A clean 0 proves the import's exit was not hijacked by main()'s process.exit.
      expect(r.status).toBe(0)
    })
  }, 180_000)

  it('B — importing it with NODE_ENV=test also does NOT run its main()', () => {
    withImportHarness((harness) => {
      const r = runTsx([harness], { NODE_ENV: 'test' })
      expect(output(r)).toMatch(/IMPORT_RETURNED_OK/)
      expect(output(r)).not.toMatch(STANDIN_MAIN_MARKER)
      expect(r.status).toBe(0)
    })
  }, 180_000)

  it('C — CAN-FAIL: a direct run still enters main()', () => {
    const r = runTsx([STANDIN_REL])
    expect(output(r)).toMatch(STANDIN_MAIN_MARKER)
    expect(r.status).toBe(STANDIN_MAIN_EXIT)
  }, 180_000)

  it('D — a direct run under NODE_ENV=test still enters main()', () => {
    // The cell the retired NODE_ENV sentinel got wrong: it exited 0 having done nothing.
    const r = runTsx([STANDIN_REL], { NODE_ENV: 'test' })
    expect(output(r)).toMatch(STANDIN_MAIN_MARKER)
    expect(r.status).toBe(STANDIN_MAIN_EXIT)
  }, 180_000)

  it('E — a `./`-prefixed direct run is still a direct run', () => {
    const r = runTsx([`./${STANDIN_REL}`])
    expect(output(r)).toMatch(STANDIN_MAIN_MARKER)
    expect(r.status).toBe(STANDIN_MAIN_EXIT)
  }, 180_000)
})

// ─────────────────────────────────────────────────────────────────────────────
// §3 — THE DETECTORS THEMSELVES. Needs no subprocess; runs everywhere.
// ─────────────────────────────────────────────────────────────────────────────
const UNGUARDED_SAMPLE = `import x from 'y'\nasync function main() { return x }\nmain().catch(() => process.exit(1))\n`
const INDENTED_UNGUARDED_SAMPLE = `import x from 'y'\nasync function main() { return x }\nif (true) {\n  main()\n}\n`
const GUARDED_SAMPLE = `import x from 'y'\nasync function main() { return x }\nexport function isDirectEntrypoint(a: string, b?: string) { return a === b }\n${GUARD_LINE}\n  main()\n}\n`

describe('M0-T65 §3 — the structural detectors are non-vacuous', () => {
  it('rejects an unguarded top-level main() call', () => {
    expect(unguardedTopLevelMainCalls(UNGUARDED_SAMPLE)).toHaveLength(1)
    expect(everyMainCallIsAfterGuard(UNGUARDED_SAMPLE)).toBe(false)
  })

  it('rejects an INDENTED main() that is not behind the guard', () => {
    // The failure mode a naive column-0 grep misses, and the one D-74 part 7 names for the
    // ratchet: indentation is not a guard.
    expect(unguardedTopLevelMainCalls(INDENTED_UNGUARDED_SAMPLE)).toHaveLength(0)
    expect(everyMainCallIsAfterGuard(INDENTED_UNGUARDED_SAMPLE)).toBe(false)
  })

  it('accepts the guarded shape', () => {
    expect(unguardedTopLevelMainCalls(GUARDED_SAMPLE)).toEqual([])
    expect(everyMainCallIsAfterGuard(GUARDED_SAMPLE)).toBe(true)
  })

  it('predicateBody returns null when there is no predicate, and differs when a body differs', () => {
    expect(predicateBody(UNGUARDED_SAMPLE)).toBeNull()
    expect(predicateBody(GUARDED_SAMPLE)).not.toBe(predicateBody(read(REFERENCE)))
  })

  it('importsSharedPredicate rejects a private copy and a bare import (M0-T66)', () => {
    // Without these, "defines NO private predicate" could pass on a file that has neither the
    // predicate NOR the import — i.e. on a file with no guard at all.
    expect(importsSharedPredicate(GUARDED_SAMPLE)).toBe(false)
    expect(importsSharedPredicate(UNGUARDED_SAMPLE)).toBe(false)
    expect(
      importsSharedPredicate("import { isDirectEntrypoint } from './lib/entrypoint'\n"),
    ).toBe(false) // imported but NOT re-exported: public surface would have changed
    expect(
      importsSharedPredicate(
        "import { isDirectEntrypoint } from '../lib/entrypoint'\nexport { isDirectEntrypoint }\n",
      ),
    ).toBe(true)
  })

  it('F — under vitest the stand-in module is never the entrypoint', () => {
    expect(process.argv[1] ?? '').not.toMatch(/entrypoint_guard_standin/)
    expect(isDirectEntrypoint(pathToFileURL(STANDIN_TS).href, process.argv[1])).toBe(false)
  })

  it('G — the predicate answers true for a genuine direct run, and false on bad input', () => {
    // Guards against an implementation that just returns false, which would make every file
    // repaired this way unrunnable while every negative assertion above still passed.
    expect(isDirectEntrypoint(pathToFileURL(STANDIN_TS).href, STANDIN_TS)).toBe(true)
    expect(isDirectEntrypoint(pathToFileURL(STANDIN_TS).href, undefined)).toBe(false)
    expect(isDirectEntrypoint('not-a-url', STANDIN_TS)).toBe(false)
  })
})
