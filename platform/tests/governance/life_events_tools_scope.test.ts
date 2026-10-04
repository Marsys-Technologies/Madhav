/**
 * life_events_tools_scope.test.ts
 *
 * SS N-109 / lifeevents-audit F3: `life_events` is PEOPLE-ENTERED, PRIVATE,
 * chart-scoped data. The AI-SDK tool `tools/structured/query_life_events.ts`
 * read it with no chart_id predicate (any chart, LIMIT 50, free-text
 * `description`). It was an orphan with no importer and was deleted. This
 * source-scan test keeps it deleted and keeps any other module under
 * `src/lib/tools/` from reading `life_events` without a chart_id predicate.
 *
 * The maintained, chart-scoped reader is the retrieval-registry capability
 * `src/lib/retrieval/registry/layers/L5_mimamsa/query_life_events.ts`
 * (same tool name, different file); this test does NOT touch it.
 *
 * Pure source scan: no DB, no network.
 */

import { describe, it, expect } from 'vitest'
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'

const PLATFORM_ROOT = resolve(__dirname, '../../')
const TOOLS_DIR = join(PLATFORM_ROOT, 'src/lib/tools')

/** String / template literals in `src` that mention the life_events table. */
export function lifeEventsLiteralsMissingChartId(src: string): string[] {
  const literals = src.match(/`[^`]*`|'(?:\\.|[^'\\\n])*'|"(?:\\.|[^"\\\n])*"/g) ?? []
  return literals.filter((lit) => /\blife_events\b/i.test(lit) && !/\bchart_id\b/i.test(lit))
}

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    if (statSync(full).isDirectory()) {
      if (name === '__tests__' || name === 'node_modules') continue
      walk(full, out)
    } else if (/\.(ts|tsx|mts|js|mjs)$/.test(name) && !/\.(test|spec)\./.test(name)) {
      out.push(full)
    }
  }
  return out
}

describe('life_events tool scope (lifeevents-audit F3)', () => {
  it('the unscoped tools/structured/query_life_events.ts reader stays deleted', () => {
    expect(existsSync(join(TOOLS_DIR, 'structured/query_life_events.ts'))).toBe(false)
  })

  it('no file named query_life_events.* exists anywhere under src/lib/tools/', () => {
    const offenders = walk(TOOLS_DIR)
      .filter((f) => /query_life_events\./.test(f))
      .map((f) => relative(PLATFORM_ROOT, f))
    expect(offenders).toEqual([])
  })

  it('no module under src/lib/tools/ reads life_events without a chart_id predicate', () => {
    const offenders: string[] = []
    for (const file of walk(TOOLS_DIR)) {
      const missing = lifeEventsLiteralsMissingChartId(readFileSync(file, 'utf8'))
      if (missing.length > 0) offenders.push(relative(PLATFORM_ROOT, file))
    }
    expect(offenders).toEqual([])
  })

  it('the retrieval-registry capability (the scoped reader) is still present', () => {
    expect(
      existsSync(join(PLATFORM_ROOT, 'src/lib/retrieval/registry/layers/L5_mimamsa/query_life_events.ts')),
    ).toBe(true)
  })

  describe('scanner self-check (synthetic SQL only)', () => {
    it('flags an unscoped life_events SELECT (the deleted tool shape)', () => {
      const unscoped = 'const sql = `SELECT event_id, description FROM life_events ${where} LIMIT 50`'
      expect(lifeEventsLiteralsMissingChartId(unscoped)).toHaveLength(1)
    })

    it('flags a plain-quoted unscoped query', () => {
      expect(lifeEventsLiteralsMissingChartId(`q("SELECT * FROM life_events")`)).toHaveLength(1)
    })

    it('accepts a chart-scoped life_events SELECT', () => {
      const scoped = 'const sql = `SELECT event_id FROM life_events WHERE chart_id = $1 LIMIT 50`'
      expect(lifeEventsLiteralsMissingChartId(scoped)).toHaveLength(0)
    })

    it('ignores literals that do not mention life_events', () => {
      expect(lifeEventsLiteralsMissingChartId('const a = `SELECT 1 FROM chart_facts`')).toHaveLength(0)
    })
  })
})
