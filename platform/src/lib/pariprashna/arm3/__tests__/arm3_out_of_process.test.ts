/**
 * P1 G1-C — the detector behind arm-3's central claim.
 *
 * §14.10 arm 3: "The ledger writer runs outside the synthesis process and holds
 * the only write role."
 *
 * "Runs outside the synthesis process" is a claim about the MODULE GRAPH, not a
 * comment. These tests make it falsifiable by walking the actual imports:
 *
 *   · nothing under `src/lib/pariprashna/pipeline/` (the synthesis path) may
 *     import `arm3/drain` — the module that performs ledger writes;
 *   · the worker entrypoint must not import the app's shared pool, or "out of
 *     process" would be one accidental `DATABASE_URL` away from being false;
 *   · the serving path may import `arm3/outbox` — enqueueing is exactly what it
 *     is supposed to do.
 *
 * Without this, "arm-3 is out-of-process" would be a status with no code path
 * that could make it read false (CLAUDE.md §N.8) — which is the defect class
 * this whole lane exists to close, and it would be poor form to reproduce it in
 * the lane's own deliverable.
 */

import { readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

const SRC = path.resolve(__dirname, '../../../..')
const PIPELINE_DIR = path.join(SRC, 'lib/pariprashna/pipeline')
const WORKER = path.resolve(
  __dirname,
  '../../../../../scripts/pariprashna/ledger_writer_worker.ts',
)
const CAPTURE = path.join(SRC, 'lib/pariprashna/samiksha/capture.ts')

function tsFilesUnder(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry)
    if (statSync(full).isDirectory()) {
      if (entry === '__tests__') continue
      out.push(...tsFilesUnder(full))
    } else if (entry.endsWith('.ts') || entry.endsWith('.tsx')) {
      out.push(full)
    }
  }
  return out
}

describe('arm-3 runs outside the synthesis process', () => {
  it('no file in the synthesis pipeline imports arm3/drain', () => {
    const offenders = tsFilesUnder(PIPELINE_DIR).filter((f) =>
      /from\s+['"][^'"]*arm3\/drain['"]/.test(readFileSync(f, 'utf8')),
    )
    expect(
      offenders.map((f) => path.relative(SRC, f)),
      'arm3/drain performs ledger writes; importing it from the synthesis pipeline would put ' +
        'the writer back in-process and defeat NO-LEAKAGE arm-3',
    ).toEqual([])
  })

  it('the worker entrypoint does not import the application pool', () => {
    // Import STATEMENTS only. The file's header prose names `@/lib/db/client`
    // while explaining why it does not import it, and a whole-file grep would
    // flag that explanation as the violation it is documenting.
    const specifiers = [...readFileSync(WORKER, 'utf8').matchAll(/^\s*import\s[^\n]*?from\s+['"]([^'"]+)['"]/gm)]
      .map((m) => m[1])
      .concat(
        [...readFileSync(WORKER, 'utf8').matchAll(/\bimport\(\s*['"]([^'"]+)['"]\s*\)/g)].map(
          (m) => m[1],
        ),
      )

    expect(specifiers.filter((s) => s.includes('lib/db'))).toEqual([])
    expect(specifiers.filter((s) => s.startsWith('@/'))).toEqual([])
  })

  it('the worker connects on its own credential variable, never DATABASE_URL', () => {
    const src = readFileSync(WORKER, 'utf8')
    expect(src).toContain('LEDGER_WRITER_DATABASE_URL')
    // `process.env.DATABASE_URL` must not appear as an actual read. The string
    // occurs inside LEDGER_WRITER_DATABASE_URL, so match the read form exactly.
    expect(src).not.toMatch(/process\.env\.DATABASE_URL/)
  })

  it('the capture path enqueues rather than writing, and does so behind one flag read', () => {
    const src = readFileSync(CAPTURE, 'utf8')
    expect(src).toContain('enqueueLedgerIntent')
    // Exactly one read site for the flag, so "off means unchanged" is enforced at
    // one line — the same discipline consent/flag.ts uses for G1-B.
    const reads = src.match(/configService\.getFlag\(/g) ?? []
    expect(reads).toHaveLength(1)
  })
})
