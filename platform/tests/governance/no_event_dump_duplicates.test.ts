/**
 * no_event_dump_duplicates.test.ts
 *
 * lifeevents-audit F6 guard. The native's life-event text lives in ONE canonical home
 * (the Life Event Log + the `life_events` table). Generated / cached / rescued copies of
 * that text must not be re-committed. This test fails if any git-tracked .json / .jsonl
 * file contains a dump of event rows -- a list of >= 5 objects that each carry BOTH an
 * `event_id` and a `description` key -- outside the allow-lists below.
 *
 * Failure messages name paths and row counts only; they never print event text.
 *
 * To add a legitimate exception: put the path in KNOWN_EXCEPTIONS WITH a reason. A stale
 * exception (file gone, or no longer a dump) also fails, so exceptions cannot rot.
 */

import { describe, it, expect } from 'vitest'
import { execFileSync } from 'node:child_process'
import { mkdtempSync, mkdirSync, rmSync, writeFileSync, readFileSync, statSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'

const REPO_ROOT = resolve(__dirname, '../../../')

/** Canonical LEL homes (by design). None are JSON today; listed so a future structured export of the canonical LEL is the only thing that can be added here. */
const CANONICAL_LEL_PATTERNS: RegExp[] = [
  /^01_FACTS_LAYER\/(LIFE_EVENT_LOG|LEL_HELD_OUT_PARTITION)[^/]*$/,
  /^99_ARCHIVE\/01_FACTS_LAYER\/LIFE_EVENT_LOG[^/]*$/,
  /^00_ARCHITECTURE\/_archive\/[^/]+\/01_FACTS_LAYER\/(LIFE_EVENT_LOG|LEL_HELD_OUT_PARTITION)[^/]*$/,
]

/** Known non-canonical dumps that are NOT yet removable. Each needs a reason. */
const KNOWN_EXCEPTIONS: Record<string, string> = {
  'platform/python-sidecar/scripts/kala_admission/cache/lel_train_events.json':
    'Hard INPUT of the D-3 ADMIT harness (lel.py load_train_events -> run_admission, w41/w42/w44/w46 + ' +
    'test_split_guard). Populated once by a live lel_query call with a server-side date_to filter; no code ' +
    'path regenerates it. Remove only together with a DB-backed, split-guarded loader (follow-up).',
}

const MIN_ROWS = 5
const MAX_DEPTH = 6
const MAX_BYTES = 32 * 1024 * 1024

function isEventRow(o: unknown): boolean {
  return (
    typeof o === 'object' &&
    o !== null &&
    !Array.isArray(o) &&
    'event_id' in (o as Record<string, unknown>) &&
    'description' in (o as Record<string, unknown>)
  )
}

/** Largest number of event-shaped rows found in any single list inside `value`. */
function maxEventRows(value: unknown, depth = 0): number {
  if (depth > MAX_DEPTH) return 0
  if (Array.isArray(value)) {
    let best = value.filter(isEventRow).length
    for (const v of value) best = Math.max(best, maxEventRows(v, depth + 1))
    return best
  }
  if (typeof value === 'object' && value !== null) {
    let best = 0
    for (const v of Object.values(value)) best = Math.max(best, maxEventRows(v, depth + 1))
    return best
  }
  return 0
}

/** Event-row count of one file's text: JSONL = one row per line; JSON = nested lists. */
export function eventRowCount(path: string, text: string): number {
  try {
    if (path.endsWith('.jsonl')) {
      let n = 0
      for (const line of text.split('\n')) {
        if (!line.trim()) continue
        const obj = JSON.parse(line)
        if (isEventRow(obj)) n += 1
        else n = Math.max(n, maxEventRows(obj))
      }
      return n
    }
    return maxEventRows(JSON.parse(text))
  } catch {
    return 0 // not parseable JSON: cannot be a structured dump
  }
}

/** Every dump under `root` among `files` (repo-relative), minus canonical/known allow-lists. */
export function findEventDumps(
  root: string,
  files: string[],
  opts: { knownExceptions?: Record<string, string> } = {},
): { path: string; rows: number }[] {
  const known = opts.knownExceptions ?? KNOWN_EXCEPTIONS
  const out: { path: string; rows: number }[] = []
  for (const f of files) {
    if (!/\.jsonl?$/.test(f)) continue
    if (CANONICAL_LEL_PATTERNS.some((re) => re.test(f))) continue
    if (f in known) continue
    const abs = join(root, f)
    let size: number
    try {
      size = statSync(abs).size
    } catch {
      continue // listed but absent in the working tree (deleted, unstaged)
    }
    if (size > MAX_BYTES) continue
    const rows = eventRowCount(f, readFileSync(abs, 'utf-8'))
    if (rows >= MIN_ROWS) out.push({ path: f, rows })
  }
  return out
}

function trackedFiles(): string[] {
  return execFileSync('git', ['ls-files', '-z', '--', '*.json', '*.jsonl'], {
    cwd: REPO_ROOT,
    encoding: 'utf-8',
    maxBuffer: 64 * 1024 * 1024,
  })
    .split('\0')
    .filter(Boolean)
}

describe('F6: no committed duplicate of life-event text', () => {
  it('no tracked JSON/JSONL event dump outside the canonical LEL allow-list', () => {
    const dumps = findEventDumps(REPO_ROOT, trackedFiles())
    expect(
      dumps,
      `Event-text dump(s) committed (paths and row counts only): ${JSON.stringify(dumps)}. ` +
        'Life-event text has one canonical home (LEL + life_events table); regenerate such files ' +
        'on demand instead of committing them, or add a justified entry to KNOWN_EXCEPTIONS.',
    ).toEqual([])
  })

  it('every KNOWN_EXCEPTIONS entry still exists and is still a dump (no stale allow-list)', () => {
    const files = new Set(trackedFiles())
    for (const p of Object.keys(KNOWN_EXCEPTIONS)) {
      expect(files.has(p), `stale exception, file not tracked: ${p}`).toBe(true)
      const rows = eventRowCount(p, readFileSync(join(REPO_ROOT, p), 'utf-8'))
      expect(rows, `stale exception, no longer a dump: ${p}`).toBeGreaterThanOrEqual(MIN_ROWS)
    }
  })

  it('the regenerable duplicates removed by F6 stay removed', () => {
    const files = new Set(trackedFiles())
    for (const p of [
      'platform/python-sidecar/brahmagyan/mimamsa/bigquery_export_preview.jsonl',
      'artifacts/D-3/lel_events.json',
    ]) {
      expect(files.has(p), `re-added duplicate: ${p}`).toBe(false)
    }
  })

  // ── Mutation proof: the scanner goes red on a synthetic dump and green without it ──
  describe('scanner mutation proof (synthetic fixtures only)', () => {
    const synth = (n: number) =>
      Array.from({ length: n }, (_, i) => ({ event_id: `SYN.${i}`, description: `synthetic row ${i}` }))

    function withTree(fn: (root: string) => void) {
      const root = mkdtempSync(join(tmpdir(), 'f6-guard-'))
      try {
        mkdirSync(join(root, 'data'), { recursive: true })
        writeFileSync(join(root, 'data', 'clean.json'), JSON.stringify({ a: 1 }))
        fn(root)
      } finally {
        rmSync(root, { recursive: true, force: true })
      }
    }

    it('green on a clean tree', () => {
      withTree((root) => expect(findEventDumps(root, ['data/clean.json'], { knownExceptions: {} })).toEqual([]))
    })

    it('red on a top-level JSON list dump (>= 5 rows)', () => {
      withTree((root) => {
        writeFileSync(join(root, 'data', 'dump.json'), JSON.stringify(synth(5)))
        expect(findEventDumps(root, ['data/clean.json', 'data/dump.json'], { knownExceptions: {} })).toEqual([
          { path: 'data/dump.json', rows: 5 },
        ])
      })
    })

    it('red on a nested { events: [...] } dump and on JSONL', () => {
      withTree((root) => {
        writeFileSync(join(root, 'data', 'nested.json'), JSON.stringify({ meta: {}, events: synth(6) }))
        writeFileSync(join(root, 'data', 'rows.jsonl'), synth(7).map((r) => JSON.stringify(r)).join('\n'))
        const got = findEventDumps(root, ['data/nested.json', 'data/rows.jsonl'], { knownExceptions: {} })
        expect(got.map((g) => g.path).sort()).toEqual(['data/nested.json', 'data/rows.jsonl'])
      })
    })

    it('green below the threshold, and green again once the dump is removed (restore)', () => {
      withTree((root) => {
        writeFileSync(join(root, 'data', 'small.json'), JSON.stringify(synth(4)))
        expect(findEventDumps(root, ['data/small.json'], { knownExceptions: {} })).toEqual([])
        writeFileSync(join(root, 'data', 'dump.json'), JSON.stringify(synth(5)))
        expect(findEventDumps(root, ['data/dump.json'], { knownExceptions: {} })).toHaveLength(1)
        rmSync(join(root, 'data', 'dump.json'))
        expect(findEventDumps(root, ['data/dump.json'], { knownExceptions: {} })).toEqual([])
      })
    })

    it('allow-lists are honoured (canonical LEL pattern and explicit exception)', () => {
      withTree((root) => {
        mkdirSync(join(root, '01_FACTS_LAYER'), { recursive: true })
        writeFileSync(join(root, '01_FACTS_LAYER', 'LIFE_EVENT_LOG_v9.json'), JSON.stringify(synth(9)))
        writeFileSync(join(root, 'data', 'ok.json'), JSON.stringify(synth(9)))
        expect(
          findEventDumps(root, ['01_FACTS_LAYER/LIFE_EVENT_LOG_v9.json', 'data/ok.json'], {
            knownExceptions: { 'data/ok.json': 'test' },
          }),
        ).toEqual([])
      })
    })
  })
})
