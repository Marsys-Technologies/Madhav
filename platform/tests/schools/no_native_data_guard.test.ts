/**
 * Guard (SS N-362): NO birth or chart data of any native may live in platform/src/lib/schools.
 * The engines analyse only the live signals and ChartData passed in (CLAUDE.md §B / §N.7).
 *
 * Scans EVERY .ts/.tsx file under src/lib/schools (comments included). The allowlist is EMPTY
 * by default; adding a file to it is a deliberate, reviewed act.
 */
import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const SCHOOLS_DIR = path.join(__dirname, '../../src/lib/schools')

/** File-level allowlist (paths relative to src/lib/schools). EMPTY by default. */
const ALLOWLIST: string[] = []

const FORBIDDEN: string[] = ['Abhisek', 'Mohanty', '1984-02-05', 'FORENSIC']

function walk(dir: string): string[] {
  const out: string[] = []
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name)
    if (e.isDirectory()) out.push(...walk(full))
    else if (/\.(ts|tsx)$/.test(e.name)) out.push(full)
  }
  return out
}

describe('schools package carries no native data', () => {
  const files = walk(SCHOOLS_DIR)

  it('finds the schools sources (the scan is not vacuous)', () => {
    const names = files.map(f => path.relative(SCHOOLS_DIR, f))
    expect(names).toContain('kp_engine.ts')
    expect(names).toContain('types.ts')
    expect(names.some(n => n.startsWith('__fixtures__'))).toBe(true)
    expect(files.length).toBeGreaterThanOrEqual(12)
  })

  it('the allowlist is empty', () => {
    expect(ALLOWLIST).toEqual([])
  })

  for (const needle of FORBIDDEN) {
    it(`no file contains "${needle}" (case-sensitive; comments included)`, () => {
      const hits: string[] = []
      for (const f of files) {
        const rel = path.relative(SCHOOLS_DIR, f)
        if (ALLOWLIST.includes(rel)) continue
        const lines = fs.readFileSync(f, 'utf-8').split('\n')
        lines.forEach((line, i) => {
          if (line.includes(needle)) hits.push(`${rel}:${i + 1}`)
        })
      }
      expect(hits).toEqual([])
    })
  }

  it('no case-insensitive "abhisek" either', () => {
    const hits = files.filter(f => /abhisek/i.test(fs.readFileSync(f, 'utf-8'))).map(f => path.relative(SCHOOLS_DIR, f))
    expect(hits).toEqual([])
  })

  it('no ABHISEK_CHART export and no defaultSignals function remain', () => {
    const hits = files.filter(f => /ABHISEK_CHART|function defaultSignals|defaultSignals\(/.test(fs.readFileSync(f, 'utf-8')))
    expect(hits.map(f => path.relative(SCHOOLS_DIR, f))).toEqual([])
  })
})
