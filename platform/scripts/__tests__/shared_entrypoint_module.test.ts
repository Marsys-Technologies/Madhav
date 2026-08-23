/**
 * `scripts/lib/entrypoint.ts` — the ONE shared `isDirectEntrypoint`, and its two load-bearing
 * properties.
 *
 * Nirmāṇa WORK_QUEUE **M0-T66**, ruling **D-67 part 3** (finding F-2, filed by M0-T60 at three
 * copies and re-filed by M0-T65 at eight): *"Three copies of a security-relevant predicate that
 * can silently diverge is a defect on its own terms."*
 *
 * Two things have to hold for the extraction to be an improvement rather than a rearrangement,
 * and each has its own section here:
 *
 *   §1 THE MODULE IS A LEAF. Ruling D-9's standing instruction is not "never import" — it is
 *      "never acquire a module graph you did not have". Importing `scripts/migrate.ts` used to
 *      apply migrations to production. This module must never become anything like that, so §1
 *      asserts, over its source, that it imports ONLY the three node builtins every caller
 *      already had and performs NO module-scope effect. Without §1, "import the shared one"
 *      would be advice that gets worse every time someone adds a convenience to it.
 *
 *   §2 NOBODY KEEPS A PRIVATE COPY. All eight former copy-holders must import and re-export the
 *      shared symbol and define no `isDirectEntrypoint` of their own. This is the assertion that
 *      replaces M0-T65's body-equality comparison: identity, not equality.
 *
 *   §3 THE PREDICATE STILL ANSWERS CORRECTLY, in both directions, including the wrongly-true
 *      direction that is this class's actual hazard.
 *
 *   §4 THE §1/§2 DETECTORS ARE NON-VACUOUS — each is run against a sample that must fail it.
 *
 * SAFE TO IMPORT IN-PROCESS: this module is the leaf §1 asserts it to be. None of the eight
 * consumers is imported by this file, and none is executed by it.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { pathToFileURL } from 'url'
import { isDirectEntrypoint } from '../lib/entrypoint'

const PLATFORM_DIR = path.resolve(__dirname, '../..')
const SHARED_REL = 'scripts/lib/entrypoint.ts'
const SHARED_TS = path.join(PLATFORM_DIR, SHARED_REL)

function read(rel: string): string {
  return fs.readFileSync(path.join(PLATFORM_DIR, rel), 'utf8')
}

/** Every tracked `.ts` under `platform/scripts`, platform-relative. */
function allScriptFiles(): string[] {
  const out: string[] = []
  const walk = (dir: string) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const abs = path.join(dir, e.name)
      if (e.isDirectory()) {
        if (e.name === 'node_modules' || e.name === 'out') continue
        walk(abs)
      } else if (e.name.endsWith('.ts')) {
        out.push(path.relative(PLATFORM_DIR, abs))
      }
    }
  }
  walk(path.join(PLATFORM_DIR, 'scripts'))
  return out.sort()
}

/**
 * ── `CONSUMERS` IS DERIVED, NEVER HAND-TYPED (M0-T66, finding F-O) ──────────────────────────
 *
 * Every production file under `platform/scripts` that uses `isDirectEntrypoint` at all — found
 * by scanning the tree, not by listing eight names. Today that is the eight former copy-holders;
 * when Wave 2 guards its 53, they enter this set with no edit here and §2 applies to all of them.
 * A hand-maintained literal is precisely what F-O was filed against.
 *
 * `scripts/__tests__/**` is excluded ON PURPOSE and it is the one exclusion: the stand-in fixture
 * (`fixtures/entrypoint_guard_standin.fixture.ts`) carries a DELIBERATE private copy, because its
 * whole job is to be a harmless module that behaves like the real ones without importing them.
 *
 * THE MATCH RUNS OVER COMMENT-BLANKED SOURCE, and that is load-bearing rather than tidy. Written
 * against raw text this derivation pulled in `scripts/ci/dispatch_gate.ts` and
 * `scripts/ci/verify_migrations_deployed.ts`, which mention `isDirectEntrypoint` only in a
 * COMMENT — explaining why a CI gate uses the opposite `IMPORT_ONLY` contract — and then failed
 * them for not importing a predicate they are right not to use. That is ADHIKĀRIN's D-72 caution
 * arriving inside this very file: a grep for a form cannot tell code that has it from prose that
 * documents it.
 */
const CONSUMERS = allScriptFiles().filter(
  (rel) =>
    rel !== SHARED_REL &&
    !rel.startsWith(path.join('scripts', '__tests__') + path.sep) &&
    /\bisDirectEntrypoint\b/.test(blankComments(read(rel))),
)

/** Coverage may be paid UP, never down. 8 = the copies that existed when M0-T66 ran. */
const CONSUMER_FLOOR = 8

/** Source with `//` and `/* *\/` comment bodies blanked, newlines preserved. */
function blankComments(src: string): string {
  return src
    .replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '))
    .replace(/(^|[^:])\/\/[^\n]*/g, (m, p1) => p1 + ' '.repeat(m.length - p1.length))
}

/** Module specifiers this file imports. */
function importSpecifiers(src: string): string[] {
  return [...blankComments(src).matchAll(/^\s*import\s[^'"]*['"]([^'"]+)['"]/gm)].map((m) => m[1])
}

function definesOwnPredicate(src: string): boolean {
  return /(?:^|\n)\s*(?:export\s+)?(?:async\s+)?function\s+isDirectEntrypoint\s*\(/.test(
    blankComments(src),
  )
}

function importsSharedPredicate(src: string): boolean {
  const s = blankComments(src)
  return (
    /import\s*\{[^}]*\bisDirectEntrypoint\b[^}]*\}\s*from\s*'[^']*lib\/entrypoint'/.test(s) &&
    /export\s*\{[^}]*\bisDirectEntrypoint\b[^}]*\}/.test(s)
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// §1 — the shared module is a LEAF (this is the D-9 property, asserted not assumed)
// ─────────────────────────────────────────────────────────────────────────────
const ALLOWED_SPECIFIERS = new Set(['node:fs', 'node:path', 'node:url'])

describe('M0-T66 §1 — scripts/lib/entrypoint.ts is a leaf module', () => {
  const src = read(SHARED_REL)

  it('imports ONLY node builtins every former copy-holder already imported', () => {
    const specs = importSpecifiers(src)
    expect(specs.length).toBeGreaterThan(0)
    for (const spec of specs) expect(ALLOWED_SPECIFIERS.has(spec)).toBe(true)
  })

  it('performs NO module-scope effect', () => {
    const code = blankComments(src)
    // No program: no main, no invocation of anything at top level, no exit.
    expect(code).not.toMatch(/(^|\n)\s*(void\s+|await\s+)?main\s*\(/)
    expect(code).not.toMatch(/process\.exit/)
    // No connection, credential, network or write primitive anywhere in the file.
    for (const forbidden of [
      /\bnew\s+Pool\b/,
      /\bnew\s+Client\b/,
      /\bgetPool\b/,
      /\bfetch\s*\(/,
      /\bexecSync\b/,
      /\bwriteFileSync\b/,
      /\bdotenv\b/,
      /\bprocess\.env\b/,
    ]) {
      expect(code).not.toMatch(forbidden)
    }
  })

  it('exports exactly one symbol', () => {
    const exported = [...blankComments(src).matchAll(/(?:^|\n)export\s+(?:function|const|let|class)\s+(\w+)/g)]
    expect(exported.map((m) => m[1])).toEqual(['isDirectEntrypoint'])
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// §2 — nobody keeps a private copy
// ─────────────────────────────────────────────────────────────────────────────
describe('M0-T66 §2 — all eight former copy-holders share the one implementation', () => {
  it('the derived list is non-vacuous and has not shrunk (F-O)', () => {
    // A broken derivation would empty CONSUMERS and the per-file blocks below would simply not
    // exist — a green suite asserting nothing. This is the floor that makes that impossible.
    expect(CONSUMERS.length).toBeGreaterThanOrEqual(CONSUMER_FLOOR)
    for (const rel of CONSUMERS) expect(fs.existsSync(path.join(PLATFORM_DIR, rel))).toBe(true)
    // The scan really does look at the whole tree, not at a stale subdirectory.
    expect(allScriptFiles().length).toBeGreaterThan(200)
  })

  for (const rel of CONSUMERS) {
    it(`${rel} imports and re-exports the shared predicate, and defines none of its own`, () => {
      const src = read(rel)
      expect(definesOwnPredicate(src)).toBe(false)
      expect(importsSharedPredicate(src)).toBe(true)
    })
  }
})

// ─────────────────────────────────────────────────────────────────────────────
// §3 — the predicate answers correctly, in BOTH directions
// ─────────────────────────────────────────────────────────────────────────────
describe('M0-T66 §3 — the shared predicate behaves', () => {
  it('true only when the module IS the entrypoint', () => {
    expect(isDirectEntrypoint(pathToFileURL(SHARED_TS).href, SHARED_TS)).toBe(true)
  })

  it('false on an import, which is the direction whose failure is catastrophic', () => {
    // Under vitest this module is loaded by the runner, never as argv[1].
    expect(process.argv[1] ?? '').not.toMatch(/lib\/entrypoint/)
    expect(isDirectEntrypoint(pathToFileURL(SHARED_TS).href, process.argv[1])).toBe(false)
  })

  it('false — not a throw — on unresolvable input', () => {
    expect(isDirectEntrypoint(pathToFileURL(SHARED_TS).href, undefined)).toBe(false)
    expect(isDirectEntrypoint('not-a-url', SHARED_TS)).toBe(false)
    expect(isDirectEntrypoint(pathToFileURL(SHARED_TS).href, '/nonexistent/path/xyz.ts')).toBe(false)
  })

  it('is not a constant function (both answers are reachable from real inputs)', () => {
    const answers = new Set([
      isDirectEntrypoint(pathToFileURL(SHARED_TS).href, SHARED_TS),
      isDirectEntrypoint(pathToFileURL(SHARED_TS).href, undefined),
    ])
    expect(answers).toEqual(new Set([true, false]))
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// §4 — the detectors above can fail
// ─────────────────────────────────────────────────────────────────────────────
const PRIVATE_COPY_SAMPLE = [
  "import { realpathSync } from 'node:fs'",
  'export function isDirectEntrypoint(a: string, b?: string) { return a === b }',
  'if (isDirectEntrypoint(import.meta.url, process.argv[1])) { main() }',
].join('\n')

const NO_GUARD_SAMPLE = "import x from 'y'\nmain()\n"

const COMMENTED_COPY_SAMPLE = [
  '// export function isDirectEntrypoint(a: string, b?: string) { return a === b }',
  "import { isDirectEntrypoint } from '../lib/entrypoint'",
  'export { isDirectEntrypoint }',
].join('\n')

describe('M0-T66 §4 — the §1/§2 detectors are non-vacuous', () => {
  it('definesOwnPredicate catches a private copy', () => {
    expect(definesOwnPredicate(PRIVATE_COPY_SAMPLE)).toBe(true)
    expect(definesOwnPredicate(NO_GUARD_SAMPLE)).toBe(false)
  })

  it('importsSharedPredicate rejects a private copy and an un-re-exported import', () => {
    expect(importsSharedPredicate(PRIVATE_COPY_SAMPLE)).toBe(false)
    expect(importsSharedPredicate(NO_GUARD_SAMPLE)).toBe(false)
    expect(importsSharedPredicate("import { isDirectEntrypoint } from './lib/entrypoint'")).toBe(false)
  })

  it('a COMMENTED-OUT copy is not mistaken for a real one (prose is not code)', () => {
    // The D-72 caution: a grep for a defective form cannot tell code that has the defect from
    // prose that documents it. Comment blanking is what makes that distinction.
    expect(definesOwnPredicate(COMMENTED_COPY_SAMPLE)).toBe(false)
    expect(importsSharedPredicate(COMMENTED_COPY_SAMPLE)).toBe(true)
  })

  it('a file that only MENTIONS the predicate in prose is not a consumer (D-72)', () => {
    // The live regression: the two CI gates document why they do NOT use this contract.
    const prose = "// see isDirectEntrypoint in scripts/lib/entrypoint.ts\nconst x = 1\n"
    expect(/\bisDirectEntrypoint\b/.test(prose)).toBe(true)
    expect(/\bisDirectEntrypoint\b/.test(blankComments(prose))).toBe(false)
    expect(CONSUMERS).not.toContain(path.join('scripts', 'ci', 'dispatch_gate.ts'))
    expect(CONSUMERS).not.toContain(path.join('scripts', 'ci', 'verify_migrations_deployed.ts'))
  })

  it('importSpecifiers rejects a non-builtin dependency', () => {
    expect(importSpecifiers("import { Pool } from 'pg'\n")).toEqual(['pg'])
    expect(ALLOWED_SPECIFIERS.has('pg')).toBe(false)
  })
})
