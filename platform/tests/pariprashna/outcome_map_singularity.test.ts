/**
 * outcome_map_singularity.test.ts — the G4 detector (SAMĀPTI §8.1 G4 / BRIEF_PB-3.1 G4).
 *
 * G4's finding: the live resolve action re-implemented the outcome→value map locally and
 * called the L-1 DAL directly, so L-5's `recordConversationalOutcome` — the function that
 * computes the Brier score and assembles the `CalibrationWriteIntent` — had ZERO non-test
 * callers. The brief's requirement is "one map, with a live caller — or a documented reason
 * for two. Do not leave two outcome maps with no stated relationship."
 *
 * This file is the DETECTOR that makes "one map with a live caller" a checkable property
 * instead of a claim, per CLAUDE.md §N.8 (a status/PASS field must have a detector behind it).
 * It asserts three independent things:
 *
 *   (1) SINGULARITY — exactly one source file in the SAMĪKṢĀ surface contains an
 *       outcome→NUMBER map, and it is `outcome_calibration.ts`.
 *   (2) LIVE CALLER — `recordConversationalOutcome` is called from at least one NON-TEST
 *       source file (the condition G4 says was violated).
 *   (3) NO BYPASS — the review-tab server actions do not call the L-1 writer's
 *       `recordOutcome` directly; they go through the L-5 recorder.
 *
 * ── Demonstrated-can-fail (the FOLLOWUP_PB-2 rule: a gate that can never go red "actively
 *    launders false confidence") ──────────────────────────────────────────────────────────
 * The map-shape detector is proven against fixtures below: it FLAGS both real map shapes (a
 * `case '<outcome>': return <number>` switch and a `{ happened: 1, ... }` record literal) and
 * does NOT flag the near-miss constructs that legitimately exist in this surface — a list of
 * outcome literals (`brier.ts`'s BRIER_SCORABLE_OUTCOMES), an outcome→STRING label map
 * (`lifecycle_label.ts`), and a Zod enum (`schema.ts`).
 *
 * ── Stated bounds (an honest scope, per the §N.8 discipline of not overclaiming) ──────────
 * This detects a re-declared outcome→number map written in one of the two idiomatic TS
 * shapes, inside the SAMĪKṢĀ file surface. It does NOT prove that no semantically-equivalent
 * arithmetic exists anywhere in the repo in some third shape; it proves the specific
 * regression G4 found cannot silently return.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve, join, relative, sep } from 'node:path'

// platform/ package root (platform/tests/pariprashna/<this> → up two dirs).
const PLATFORM_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')

/** The SAMĪKṢĀ file surface: the L-1..L-5 lib, the review-tab route, and its components. */
const SAMIKSHA_DIRS = [
  'src/lib/pariprashna/samiksha',
  'src/app/clients/[id]/samiksha',
  'src/components/pariprashna/samiksha',
]

/** The ONE file allowed to contain an outcome→number map. */
const CANONICAL_MAP_FILE = 'src/lib/pariprashna/samiksha/outcome_calibration.ts'

/** The L-5 recorder that must have a live (non-test) caller. */
const RECORDER_FILE = 'src/lib/pariprashna/samiksha/outcome_recorder.ts'
const RECORDER_FN = 'recordConversationalOutcome'

/** The live resolve surface that must not bypass the recorder. */
const ACTIONS_FILE = 'src/app/clients/[id]/samiksha/actions.ts'

/**
 * The two idiomatic TypeScript shapes of an outcome→NUMBER map. Deliberately requires a
 * NUMERIC (or explicit `null`) right-hand side, so an outcome→string label map, a list of
 * outcome literals, and an enum declaration are all correctly NOT matched.
 */
const OUTCOME_VALUE_MAP_SHAPES: readonly { id: string; pattern: RegExp }[] = [
  {
    id: 'switch-case-returns-number',
    pattern: /case\s+['"](?:happened|did_not_happen|partial|unverifiable)['"]\s*:[\s\S]{0,120}?return\s+(?:-?\d|null\b)/,
  },
  {
    id: 'record-literal-number-valued',
    pattern: /['"]?(?:happened|did_not_happen)['"]?\s*:\s*(?:-?\d|null\b)/,
  },
]

function listSourceFiles(relDir: string): string[] {
  const abs = resolve(PLATFORM_ROOT, relDir)
  if (!existsSync(abs)) return []
  const out: string[] = []
  const walk = (dir: string): void => {
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry)
      if (statSync(full).isDirectory()) {
        if (entry === '__tests__' || entry === 'node_modules') continue
        walk(full)
        continue
      }
      if (!/\.tsx?$/.test(entry)) continue
      if (/\.(test|spec)\.tsx?$/.test(entry)) continue
      out.push(relative(PLATFORM_ROOT, full).split(sep).join('/'))
    }
  }
  walk(abs)
  return out
}

/** Every non-test .ts/.tsx file under src/, for the live-caller scan. */
function listAllSrcFiles(): string[] {
  return listSourceFiles('src')
}

function filesContainingOutcomeValueMap(files: readonly string[]): { file: string; shape: string }[] {
  const hits: { file: string; shape: string }[] = []
  for (const rel of files) {
    const src = readFileSync(resolve(PLATFORM_ROOT, rel), 'utf8')
    for (const shape of OUTCOME_VALUE_MAP_SHAPES) {
      if (shape.pattern.test(src)) {
        hits.push({ file: rel, shape: shape.id })
        break
      }
    }
  }
  return hits
}

describe('G4 (1) — exactly ONE outcome→value map in the SAMĪKṢĀ surface', () => {
  it('the surface is non-empty (guards against a vacuous pass from a bad path)', () => {
    const files = SAMIKSHA_DIRS.flatMap(listSourceFiles)
    expect(files.length).toBeGreaterThan(10)
    expect(files).toContain(CANONICAL_MAP_FILE)
    expect(files).toContain(ACTIONS_FILE)
  })

  it('the ONLY file carrying an outcome→number map is outcome_calibration.ts', () => {
    const files = SAMIKSHA_DIRS.flatMap(listSourceFiles)
    const hits = filesContainingOutcomeValueMap(files)
    expect(
      hits.map((h) => h.file).sort(),
      `expected exactly one outcome→value map; found: ${JSON.stringify(hits)}`,
    ).toEqual([CANONICAL_MAP_FILE])
  })
})

describe('G4 (2) — the single map has a LIVE (non-test) caller', () => {
  it('recordConversationalOutcome is called from at least one non-test source file', () => {
    const callers = listAllSrcFiles().filter((rel) => {
      if (rel === RECORDER_FILE) return false
      const src = readFileSync(resolve(PLATFORM_ROOT, rel), 'utf8')
      return new RegExp(`\\b${RECORDER_FN}\\s*\\(`).test(src)
    })
    expect(
      callers,
      `${RECORDER_FN} has no non-test caller — this is exactly the G4 defect (the live ` +
        `resolve action bypassing L-5 and re-implementing the map locally).`,
    ).not.toEqual([])
    expect(callers).toContain(ACTIONS_FILE)
  })

  it('recordConversationalOutcome is the sole consumer of the canonical map for resolutions', () => {
    const recorder = readFileSync(resolve(PLATFORM_ROOT, RECORDER_FILE), 'utf8')
    // It reaches the map through computeBrier (which calls outcomeToValue internally) —
    // the map is never re-derived in the recorder itself.
    expect(recorder).toMatch(/from '\.\/outcome_calibration'/)
    expect(filesContainingOutcomeValueMap([RECORDER_FILE])).toEqual([])
  })
})

describe('G4 (3) — the live resolve surface does not bypass the recorder', () => {
  const actions = () => readFileSync(resolve(PLATFORM_ROOT, ACTIONS_FILE), 'utf8')

  it('imports recordConversationalOutcome', () => {
    expect(actions()).toMatch(new RegExp(`import\\s*\\{[^}]*${RECORDER_FN}[^}]*\\}`))
  })

  it('does NOT import or call the L-1 writer recordOutcome directly', () => {
    const src = actions()
    expect(src, 'actions.ts still calls the L-1 DAL recordOutcome directly (G4 bypass)').not.toMatch(
      /\brecordOutcome\s*\(/,
    )
    expect(src).not.toMatch(/import\s*\{[^}]*\brecordOutcome\b[^}]*\}\s*from\s*'@\/lib\/pariprashna\/samiksha\/writer'/)
  })
})

describe('G4 — the map detector is demonstrated-can-fail', () => {
  const detect = (src: string): string[] =>
    OUTCOME_VALUE_MAP_SHAPES.filter((s) => s.pattern.test(src)).map((s) => s.id)

  it('FLAGS a re-implemented switch map (the exact shape G4 removed from actions.ts)', () => {
    const fixture = [
      'function outcomeToValue(outcome: Outcome): number | null {',
      '  switch (outcome) {',
      "    case 'happened':",
      '      return 1',
      "    case 'unverifiable':",
      '      return null',
      '  }',
      '}',
    ].join('\n')
    expect(detect(fixture)).toContain('switch-case-returns-number')
  })

  it('FLAGS a re-implemented record-literal map', () => {
    expect(detect("const VALUES = { happened: 1, did_not_happen: 0, partial: 0.5 }")).toContain(
      'record-literal-number-valued',
    )
  })

  it('does NOT flag a list of outcome literals (brier.ts BRIER_SCORABLE_OUTCOMES)', () => {
    expect(detect("export const S: readonly Outcome[] = ['happened', 'did_not_happen', 'partial']")).toEqual([])
  })

  it('does NOT flag an outcome→STRING label map (lifecycle_label.ts shape)', () => {
    expect(detect("const LABELS = { happened: 'Happened', did_not_happen: 'Did not happen' }")).toEqual([])
  })

  it('does NOT flag a Zod enum of the outcome vocabulary (schema.ts shape)', () => {
    expect(detect("export const OutcomeSchema = z.enum(['happened', 'did_not_happen', 'partial', 'unverifiable'])")).toEqual([])
  })

  it('the real near-miss files in the surface are genuinely not flagged', () => {
    for (const rel of [
      'src/lib/pariprashna/samiksha/brier.ts',
      'src/lib/pariprashna/samiksha/lifecycle_label.ts',
      'src/lib/pariprashna/samiksha/schema.ts',
    ]) {
      expect(existsSync(resolve(PLATFORM_ROOT, rel)), `missing near-miss fixture file ${rel}`).toBe(true)
      expect(filesContainingOutcomeValueMap([rel]), `${rel} false-positived`).toEqual([])
    }
  })
})
