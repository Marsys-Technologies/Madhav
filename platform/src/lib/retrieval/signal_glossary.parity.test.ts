/**
 * signal_glossary.parity.test.ts — cross-language drift gate for the generated glossary mirror.
 *
 * `signal_glossary.generated.ts` is codegen output from the Python single source of truth
 * `brahmagyan/signal_register_glossary.py`. This test is the mechanical guard that the two
 * have not drifted — it re-hashes the .py and compares against the sha256 the generator
 * pinned into the mirror. Deliberately python-free: it must fail on a CI runner that has no
 * Python interpreter at all, which is exactly where an un-regenerated edit would otherwise
 * slip through. Same mechanism as generate_vidhi_registry_mirror.ts's content-hash banner.
 */
import { describe, expect, it } from 'vitest'
import { createHash } from 'node:crypto'
import * as fs from 'node:fs'
import * as path from 'node:path'
import {
  FACT_CATEGORY_DISPLAY_LABEL,
  INTERNAL_MARKER_PATTERNS,
  SIGNAL_TYPE_GLOSSARY,
  SOURCE_PATH,
  SOURCE_SHA256,
} from './signal_glossary.generated'

// platform/src/lib/retrieval → repo root
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..', '..')

describe('signal glossary Python→TS mirror parity', () => {
  it('points at a Python source that actually exists', () => {
    expect(fs.existsSync(path.join(REPO_ROOT, SOURCE_PATH))).toBe(true)
  })

  it('matches the sha256 of the canonical Python source (regenerate on drift)', () => {
    const py = fs.readFileSync(path.join(REPO_ROOT, SOURCE_PATH), 'utf8')
    const actual = createHash('sha256').update(py, 'utf8').digest('hex')
    expect(
      actual,
      `${SOURCE_PATH} has changed since the mirror was generated. ` +
      'Run: npm run codegen:signal-glossary',
    ).toBe(SOURCE_SHA256)
  })

  it('carries non-empty tables (a hollow mirror would silently disable every label)', () => {
    expect(Object.keys(FACT_CATEGORY_DISPLAY_LABEL).length).toBeGreaterThan(40)
    expect(Object.keys(SIGNAL_TYPE_GLOSSARY).length).toBeGreaterThan(5)
    expect(INTERNAL_MARKER_PATTERNS.length).toBeGreaterThan(0)
  })

  it('carries the F-131 marker patterns the serving layer depends on', () => {
    expect(INTERNAL_MARKER_PATTERNS).toContain('floored: no_canonical_per_varga_method')
    expect(INTERNAL_MARKER_PATTERNS).toContain('floored:')
    // Order matters — classifySignalMarker reports the first match, and the most specific
    // pattern must precede the generic 'floored:' prefix.
    expect(INTERNAL_MARKER_PATTERNS.indexOf('floored: no_canonical_per_varga_method'))
      .toBeLessThan(INTERNAL_MARKER_PATTERNS.indexOf('floored:'))
  })

  it('the generated file is data-only — no imports, so it cannot poison a client bundle', () => {
    const gen = fs.readFileSync(
      path.join(REPO_ROOT, 'platform/src/lib/retrieval/signal_glossary.generated.ts'), 'utf8')
    expect(gen).not.toMatch(/^\s*import\s/m)
    expect(gen).toContain('DO NOT HAND-EDIT')
  })
})
