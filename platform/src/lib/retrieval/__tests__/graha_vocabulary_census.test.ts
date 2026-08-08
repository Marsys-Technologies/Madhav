/**
 * graha_vocabulary_census.test.ts — ADHIṢṬHĀNA Campaign A, Lane A2 census gate (TS side).
 * ================================================================================
 * Mirrors platform/python-sidecar/tests/test_graha_vocabulary_census.py's pattern and
 * rationale (see that file's header for the full defect-class explanation) on the
 * TypeScript tree: R17 (Adoption over addition) requires acceptance by an actual,
 * detector-cited removal census, not an estimate.
 *
 * address_resolver.ts's GRAHA_CODE_TO_NAME / grahaCodeOf() (declared canonical per the
 * ADHIṢṬHĀNA Lane A2 brief) is the ONE permitted independent graha-alias object literal.
 * Every other TS graha map found tree-wide is retired to either:
 *   - an import of grahaCodeOf()/GRAHA_CODE_TO_NAME directly, or
 *   - a `Record<string,string>` built via `Object.fromEntries([...].map(x => [x, grahaCodeOf(x)]))`
 *     (a derivation, not a literal — this scanner cannot see it as an independent map,
 *     which is the pass signal, exactly as the Python scanner's comprehension-blindness is).
 *
 * WHAT IS A VIOLATION: a TS source file (outside address_resolver.ts and this file itself)
 * containing an object literal with >= GRAHA_KEY_THRESHOLD (4) distinct string-literal
 * PROPERTIES whose KEY and VALUE are BOTH graha-identifier tokens (short code, long English
 * name, or classical Sanskrit name/2-letter code) — i.e. an alias/subject NORMALIZATION map,
 * not a doctrinal lookup table that merely uses graha names as object keys with non-identifier
 * values (dignity states, sign names, weights, karaka roles).
 */
import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'
import * as ts from 'typescript'
import { GRAHA_CODE_TO_NAME } from '../graha_labels'

const REPO_SRC = path.resolve(__dirname, '../../../')

const SCAN_DIRS = ['lib', 'app', 'components'].map(d => path.join(REPO_SRC, d))

// The graha-identifier vocabulary this scanner recognizes as "keys/values of a
// graha map" — address_resolver's own exported canonical codes/names (short
// codes SUN/MOON/MAR/… and their Title-case long forms) plus the alias forms
// its (module-private) GRAHA_ALIASES table is documented to also accept: 2-char
// codes, lowercase long names, and classical Sanskrit variants. Kept in sync
// with graha_vocabulary.py's GRAHA_TOKENS for cross-language parity (this
// scanner intentionally does not import address_resolver's private
// GRAHA_ALIASES — it stays module-private by design).
const GRAHA_TOKENS = new Set<string>(
  [...Object.keys(GRAHA_CODE_TO_NAME), ...Object.values(GRAHA_CODE_TO_NAME)].map(s => s.toLowerCase()),
)
for (const extra of [
  'lagna', 'su', 'mo', 'ma', 'me', 'ju', 've', 'sa', 'ra', 'ke', 'rah', 'ket',
  'sol', 'luna', 'mangal', 'budh', 'brihaspati', 'sukra', 'sani', 'rahoo', 'kethu',
  'surya', 'chandra', 'mangala', 'kuja', 'budha', 'guru', 'shukra', 'shani',
]) {
  GRAHA_TOKENS.add(extra)
}

const GRAHA_KEY_THRESHOLD = 4

// The SSoT is now two files (ADHIṢṬHĀNA build-break fix, 2026-08-08): the graha
// code/name/alias vocabulary + grahaCodeOf() itself live in graha_labels.ts (the
// CLIENT-SAFE pure subset, extracted so a 'use client' component can import graha
// labels without pulling in address_resolver.ts's `@/lib/db/client` → `server-only`
// chain); address_resolver.ts re-exports the same names for its existing DB-touching
// call sites. Both are excluded from the scan — the object literal genuinely lives
// in graha_labels.ts now, address_resolver.ts carries only a re-export.
const SSOT_FILES = new Set(['address_resolver.ts', 'graha_labels.ts'])

// ── Known-safe exclusions ──────────────────────────────────────────────────────
const EXCLUDED_PATH_SUBSTRINGS = ['__tests__', '.test.ts', '.gate.test.ts', 'node_modules', '/generated/']

// Documented, reasoned exclusions: (fileBasename, declaredName) pairs that remain
// independent by design, not by omission. Empty for now — every genuine alias map
// found by this lane's audit was retired to a grahaCodeOf()-derived Record.
const INTENTIONAL_EXCLUSIONS = new Set<string>([
  // register_d7_channel.ts already wraps grahaCodeOf correctly (no independent
  // literal exists there) — nothing to exclude; listed for documentation parity
  // with the lane brief's explicit "leave as-is, already adopted" note.
])

interface Hit {
  file: string
  name: string
  line: number
  numKeys: number
}

function collectTsFiles(dir: string, out: string[]): void {
  if (!fs.existsSync(dir)) return
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue
      collectTsFiles(full, out)
    } else if (entry.isFile() && (entry.name.endsWith('.ts') || entry.name.endsWith('.tsx'))) {
      if (EXCLUDED_PATH_SUBSTRINGS.some(s => full.includes(s))) continue
      if (SSOT_FILES.has(entry.name)) continue
      out.push(full)
    }
  }
}

/** Distinct graha-token property keys (lowercased) in an object literal where
 *  BOTH the property key AND its value are graha-identifier tokens — mirrors
 *  the Python census's `_dict_literal_graha_key_hits`. */
function objectLiteralGrahaKeyHits(node: ts.ObjectLiteralExpression): Set<string> {
  const hits = new Set<string>()
  for (const prop of node.properties) {
    if (!ts.isPropertyAssignment(prop)) continue
    let keyText: string | null = null
    if (ts.isIdentifier(prop.name) || ts.isStringLiteral(prop.name)) {
      keyText = prop.name.text
    }
    if (keyText === null) continue
    const lowKey = keyText.trim().toLowerCase()
    if (!GRAHA_TOKENS.has(lowKey)) continue
    if (!ts.isStringLiteral(prop.initializer)) continue
    const lowVal = prop.initializer.text.trim().toLowerCase()
    if (!GRAHA_TOKENS.has(lowVal)) continue
    hits.add(lowKey)
  }
  return hits
}

function findGrahaMapsInFile(filePath: string): Hit[] {
  const source = fs.readFileSync(filePath, 'utf-8')
  const sf = ts.createSourceFile(filePath, source, ts.ScriptTarget.Latest, true)
  const found: Hit[] = []

  function visit(node: ts.Node) {
    if (ts.isVariableDeclaration(node) && node.initializer && ts.isObjectLiteralExpression(node.initializer)) {
      const hits = objectLiteralGrahaKeyHits(node.initializer)
      if (hits.size >= GRAHA_KEY_THRESHOLD) {
        const name = ts.isIdentifier(node.name) ? node.name.text : '<destructured>'
        const { line } = sf.getLineAndCharacterOfPosition(node.getStart())
        found.push({ file: filePath, name, line: line + 1, numKeys: hits.size })
      }
    }
    ts.forEachChild(node, visit)
  }
  visit(sf)
  return found
}

function runCensus(): Hit[] {
  const files: string[] = []
  for (const dir of SCAN_DIRS) collectTsFiles(dir, files)
  const allHits: Hit[] = []
  for (const f of files.sort()) {
    for (const hit of findGrahaMapsInFile(f)) {
      const key = `${path.basename(hit.file)}::${hit.name}`
      if (INTENTIONAL_EXCLUSIONS.has(key)) continue
      allHits.push(hit)
    }
  }
  return allHits
}

describe('graha vocabulary census (TS)', () => {
  it('scanner reaches known lane-touched directories', () => {
    const files: string[] = []
    for (const dir of SCAN_DIRS) collectTsFiles(dir, files)
    const names = files.map(f => path.basename(f))
    expect(names).toContain('identifier_format.ts')
    expect(names).toContain('composite_ranker.ts')
    expect(names).toContain('priors_config.ts')
  })

  it('SSoT files (address_resolver.ts, graha_labels.ts) are excluded from the scan', () => {
    const files: string[] = []
    for (const dir of SCAN_DIRS) collectTsFiles(dir, files)
    const names = files.map(f => path.basename(f))
    for (const ssot of SSOT_FILES) expect(names).not.toContain(ssot)
  })

  it('THE GATE (R17): exactly ONE independent TS graha map survives tree-wide', () => {
    // Before ADHIṢṬHĀNA Lane A2: 18 independent literal graha-alias object
    // literals found by this exact scanner shape tree-wide across 15 files,
    // re-run directly against the pre-lane git tree (`git stash` to the base
    // commit, scanner re-run, `git stash pop`) as a detector-cited
    // measurement, not an estimate. Only ~6 were in the lane brief's own
    // enumeration (identifier_format.ts x2, composite_ranker.ts x2,
    // priors_config.ts, get_dasha_lord_capability.ts); the other 12 were
    // surfaced by this full-tree census: facts_store.ts, l1_context_fetcher.ts
    // (x1), reading_checklist.ts, query_remedies.ts, forensic/snapshot.ts,
    // RasiChartSVG.tsx, QueryDNAPanel.tsx, rank_vocabulary.ts,
    // get_chart_snapshot.ts, get_dashas.ts, get_graha_yuddha.ts,
    // register_d10_pact.ts. graha_portrait.ts was already adopted (imports
    // grahaCodeOf/GRAHA_CODE_TO_NAME directly, no independent literal) —
    // the brief's own "~line 82" pointer for it was stale.
    // After: 0 outside the SSoT (this test) — address_resolver.ts was the one
    // permitted canonical file (excluded from the scan by file name); it also
    // gained 2-letter code aliases (rah/ket) for cross-language parity with
    // the Python SSoT and to cover identifier_format.ts's prior coverage.
    // 2026-08-08 (ADHIṢṬHĀNA build-break fix): the literal itself (and
    // grahaCodeOf()) moved to graha_labels.ts — the client-safe pure subset
    // extracted so a 'use client' component (QueryDNAPanel.tsx) can import
    // graha labels without pulling in address_resolver.ts's `@/lib/db/client`
    // → `server-only` chain. address_resolver.ts re-exports the same names
    // (still zero independent literals there); both files are now the SSoT
    // pair excluded from the scan (SSOT_FILES above).
    const hits = runCensus()
    if (hits.length > 0) {
      const lines = ['Independent TS graha maps found outside the SSoT (R17 violation):']
      for (const h of hits) {
        lines.push(`  ${path.relative(REPO_SRC, h.file)}:${h.line}: '${h.name}' (${h.numKeys} graha-token keys)`)
      }
      throw new Error(lines.join('\n'))
    }
    expect(hits).toHaveLength(0)
  })
})
