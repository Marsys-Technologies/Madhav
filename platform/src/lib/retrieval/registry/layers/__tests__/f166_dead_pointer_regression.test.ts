/**
 * f166_dead_pointer_regression.test.ts — F-166b dead test-pointer regression guard.
 *
 * THE DEFECT: two comments in this directory named a `*.test.ts` file that does not exist
 * anywhere in the repo:
 *   - `register_d9_judgment.ts:143` claimed `shastra_map_signal_domain.test.ts` asserts
 *     SHASTRA_MAP's canonical-domain-only invariant. That file never existed; the real
 *     assertion lives in `register_d9_judgment.f57_domain_vocabulary.test.ts`.
 *   - `register_d8_assess_domain.ts:~176` claimed `register_d8_assess_domain.test.ts` covers
 *     the TEMPORAL_EMPTY_REASON regression protection. That file never existed either; the
 *     real siblings are `register_d8_assess_domain.gate.test.ts` /
 *     `register_d8_assess_domain.lane_e.test.ts`.
 *
 * Style precedent: `platform-mcp/src/tools/kala_views/f123_dead_pointer_regression.test.ts`
 * (CI-wired at `.github/workflows/ci.yml:1020`) — that suite exercises the real call sites to
 * prove a pointer resolves; this one is the simpler static-text sibling the F-166 finding
 * calls for: every `*.test.ts` filename literally referenced (in a comment or string) by
 * either touched file must resolve to a real file on disk, so a future edit that repoints a
 * comment at a typo'd or renamed test file fails CI instead of silently going stale again.
 *
 * Deliberately scoped to ONLY the two files this PR touches (F-166's own scope warning:
 * ~27 other dangling test-path strings exist repo-wide and are explicitly out of scope here).
 */
import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'

const LAYERS_DIR = path.resolve(__dirname, '..')
// __dirname = platform/src/lib/retrieval/registry/layers/__tests__
// -> platform/src is 5 levels up from LAYERS_DIR (layers -> registry -> retrieval -> lib -> src)
const PLATFORM_SRC = path.resolve(LAYERS_DIR, '../../../../')

const TOUCHED_FILES = [
  path.join(LAYERS_DIR, 'register_d9_judgment.ts'),
  path.join(LAYERS_DIR, 'register_d8_assess_domain.ts'),
]

const SKIP_DIRS = new Set(['node_modules', '.next', 'dist', 'build', '.git'])

/** Recursively collects every basename under `root`, mapping basename -> at least one
 *  absolute path that carries it. Bounded to `platform/src` — every filename this test
 *  checks is expected to live there (both touched files' own test siblings do). */
function collectBasenames(root: string): Map<string, string[]> {
  const out = new Map<string, string[]>()
  const stack = [root]
  while (stack.length > 0) {
    const dir = stack.pop()!
    let entries: fs.Dirent[]
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true })
    } catch {
      continue
    }
    for (const entry of entries) {
      if (SKIP_DIRS.has(entry.name)) continue
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) {
        stack.push(full)
      } else if (entry.isFile()) {
        const list = out.get(entry.name) ?? []
        list.push(full)
        out.set(entry.name, list)
      }
    }
  }
  return out
}

/** Every bare `*.test.ts` filename token literally present in `text` (basename only —
 *  these files reference siblings/self by name in comments, never by relative path). */
function extractTestFileReferences(text: string): string[] {
  // Filenames here are dot-segmented (e.g. `register_d9_judgment.f57_domain_vocabulary.test.ts`)
  // — the greedy `(?:\.[A-Za-z0-9_]+)*` backtracks to leave the trailing `.test.ts` for the
  // literal suffix, so the full multi-segment basename is captured, not just its last segment.
  const matches = text.match(/[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*\.test\.ts/g) ?? []
  return Array.from(new Set(matches))
}

describe('F-166b — no dangling *.test.ts pointer in the two touched files', () => {
  const basenames = collectBasenames(PLATFORM_SRC)

  for (const filePath of TOUCHED_FILES) {
    const fileLabel = path.basename(filePath)
    const text = fs.readFileSync(filePath, 'utf8')
    const referenced = extractTestFileReferences(text)

    it(`${fileLabel} references at least one *.test.ts filename (sanity — the extractor itself works)`, () => {
      expect(referenced.length).toBeGreaterThan(0)
    })

    it.each(referenced)(`${fileLabel} -> %s resolves to a real file on disk`, (name) => {
      const hits = basenames.get(name)
      expect(hits, `"${name}" (referenced in ${fileLabel}) does not exist anywhere under ${PLATFORM_SRC}`).toBeDefined()
      expect(hits!.length).toBeGreaterThan(0)
    })
  }

  // Pin the two specific dead pointers this PR fixed, so a revert is caught even if the
  // generic resolution check above were ever weakened.
  it('register_d9_judgment.ts no longer references the nonexistent shastra_map_signal_domain.test.ts', () => {
    const text = fs.readFileSync(path.join(LAYERS_DIR, 'register_d9_judgment.ts'), 'utf8')
    expect(text).not.toContain('shastra_map_signal_domain.test.ts')
    expect(text).toContain('register_d9_judgment.f57_domain_vocabulary.test.ts')
  })

  it('register_d8_assess_domain.ts no longer references the nonexistent register_d8_assess_domain.test.ts', () => {
    const text = fs.readFileSync(path.join(LAYERS_DIR, 'register_d8_assess_domain.ts'), 'utf8')
    expect(text).not.toContain('register_d8_assess_domain.test.ts')
    expect(text).toContain('register_d8_assess_domain.gate.test.ts')
  })
})
