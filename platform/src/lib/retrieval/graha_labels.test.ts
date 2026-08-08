/**
 * graha_labels.test.ts — Unit tests for the client-safe graha label/code vocabulary
 * extracted from address_resolver.ts (ADHIṢṬHĀNA build-break fix, 2026-08-08).
 *
 * No mocks required — unlike address_resolver.test.ts, this module has zero I/O
 * (no `@/lib/db/client` dependency), which is the entire point of the extraction:
 * it must be importable from a 'use client' component without pulling in
 * `server-only`. These tests both lock in grahaCodeOf()/GRAHA_CODE_TO_NAME's exact
 * prior behavior (unchanged by the move) and stand as a regression guard against
 * this module ever growing a `@/lib/db/client` import again.
 */

import { describe, it, expect } from 'vitest'
import { AddressResolutionError, GRAHA_CODE_TO_NAME, grahaCodeOf } from './graha_labels'
import * as fs from 'node:fs'
import * as path from 'node:path'

describe('GRAHA_CODE_TO_NAME', () => {
  it('maps every canonical fact_subject code to its classical graha name', () => {
    expect(GRAHA_CODE_TO_NAME.SUN).toBe('Sun')
    expect(GRAHA_CODE_TO_NAME.MOON).toBe('Moon')
    expect(GRAHA_CODE_TO_NAME.MAR).toBe('Mars')
    expect(GRAHA_CODE_TO_NAME.MER).toBe('Mercury')
    expect(GRAHA_CODE_TO_NAME.JUP).toBe('Jupiter')
    expect(GRAHA_CODE_TO_NAME.VEN).toBe('Venus')
    expect(GRAHA_CODE_TO_NAME.SAT).toBe('Saturn')
    expect(GRAHA_CODE_TO_NAME.RAH_MEAN).toBe('Rahu')
    expect(GRAHA_CODE_TO_NAME.KET_MEAN).toBe('Ketu')
  })
})

describe('grahaCodeOf', () => {
  it('normalizes canonical short codes (case-insensitive)', () => {
    expect(grahaCodeOf('SUN')).toBe('SUN')
    expect(grahaCodeOf('sun')).toBe('SUN')
    expect(grahaCodeOf('RAH_MEAN')).toBe('RAH_MEAN')
  })

  it('normalizes English long-form names', () => {
    expect(grahaCodeOf('Saturn')).toBe('SAT')
    expect(grahaCodeOf('Mars')).toBe('MAR')
    expect(grahaCodeOf('Rahu')).toBe('RAH_MEAN')
    expect(grahaCodeOf('Ketu')).toBe('KET_MEAN')
  })

  it('normalizes 2-letter shorthand aliases', () => {
    expect(grahaCodeOf('su')).toBe('SUN')
    expect(grahaCodeOf('ma')).toBe('MAR')
    expect(grahaCodeOf('ra')).toBe('RAH_MEAN')
    expect(grahaCodeOf('ke')).toBe('KET_MEAN')
  })

  it('normalizes bare "rah"/"ket" (Lane A2 cross-language parity aliases)', () => {
    expect(grahaCodeOf('rah')).toBe('RAH_MEAN')
    expect(grahaCodeOf('ket')).toBe('KET_MEAN')
  })

  it('normalizes classical Sanskrit names', () => {
    expect(grahaCodeOf('shani')).toBe('SAT')
    expect(grahaCodeOf('surya')).toBe('SUN')
    expect(grahaCodeOf('chandra')).toBe('MOON')
    expect(grahaCodeOf('guru')).toBe('JUP')
    expect(grahaCodeOf('brihaspati')).toBe('JUP')
    expect(grahaCodeOf('shukra')).toBe('VEN')
    expect(grahaCodeOf('mangala')).toBe('MAR')
    expect(grahaCodeOf('kuja')).toBe('MAR')
    expect(grahaCodeOf('budha')).toBe('MER')
  })

  it('round-trips grahaCodeOf -> GRAHA_CODE_TO_NAME for every canonical name', () => {
    for (const name of Object.values(GRAHA_CODE_TO_NAME)) {
      expect(GRAHA_CODE_TO_NAME[grahaCodeOf(name)]).toBe(name)
    }
  })

  it('throws AddressResolutionError on an unrecognized name (B.10 — no silent fallback)', () => {
    expect(() => grahaCodeOf('Pluto')).toThrow(AddressResolutionError)
    expect(() => grahaCodeOf('not-a-graha')).toThrow(AddressResolutionError)
  })
})

describe('module purity — no server-only / DB dependency', () => {
  it('the source file imports nothing from @/lib/db/client or the "server-only" package', () => {
    // Static-source guard: the whole reason this module exists is so a 'use client'
    // component can import graha labels without pulling in `server-only`. A future
    // edit that reintroduces a DB import here would silently resurrect the exact
    // build break this file was extracted to fix — catch it at test time, not at
    // `npm run build` time.
    const src = fs.readFileSync(path.join(__dirname, 'graha_labels.ts'), 'utf-8')
    // Match an actual `import ... from '@/lib/db/client'` (or bare `import 'server-only'`)
    // statement specifically, not the module's own doc-comment prose that documents
    // (and warns against) exactly this dependency.
    expect(src).not.toMatch(/^\s*import\b[^\n]*from\s+['"]@\/lib\/db\/client['"]/m)
    expect(src).not.toMatch(/^\s*import\s+['"]server-only['"]/m)
  })
})
