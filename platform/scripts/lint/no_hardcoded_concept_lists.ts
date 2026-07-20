/**
 * no_hardcoded_concept_lists.ts — hardcoded-list lint (W1 Lane L1a, RETRIEVAL_PLANE_ELEVATION_PLAN
 * §9.6 "Concept Spine" doctrine, W-24)
 * ================================================================================
 * Doctrine: "inventory truth is EXTRACTED or GENERATED, never hand-authored" (the
 * plan's Concept Spine principle). This scans the registry source tree for
 * hand-authored enumeration literals that duplicate what should instead be derived
 * from concept_ledger (migration 461) — the single writable inventory-truth source
 * — once the W-25 harvest pipeline populates it and downstream code migrates to
 * consume it (a LATER wave; this lint does not migrate anything, it only flags).
 *
 * v1 SCOPE (deliberately narrow, per the brief — "a few known patterns rather than
 * exhaustive"):
 *   Rule 1 — a top-level `const`/`export const` array literal of >= 15 string
 *            elements where >= 70% of the elements look like snake_case concept
 *            identifiers (e.g. fact_category or signal_class names: lowercase,
 *            digits, underscores only). This is exactly the shape of
 *            `CHART_FACTS_CATEGORIES` in coverage_matrix.ts (158 hand-typed
 *            fact_category strings — cited in the plan's W-16/W-20/W-23 findings
 *            as one of THREE inconsistent hand-maintained enumerations of the same
 *            underlying concept set).
 *
 * This is a regex/heuristic scan, not an AST analysis — deliberately simple for a
 * v1 lint. It will have false negatives (patterns it doesn't recognize) and
 * possibly rare false positives (a large, genuinely-not-concept string array); the
 * report below states exactly what it caught on THIS run, not a claim of
 * exhaustive coverage.
 *
 * Usage: npx tsx scripts/lint/no_hardcoded_concept_lists.ts
 * Exit code: 0 always in v1 (report-only — not yet wired as a CI hard gate; see
 * plan §9.6-4/W-26 for the future hard-gate wiring once concept_ledger is
 * populated and has something to diff against).
 */
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { extname, join } from 'node:path'

// Scan root: the registry source tree (task scope — "scans the registry source
// tree"). Narrower than the plan's full three-path W-16 census methodology
// (lib/retrieval/ + register_p1_* + brahma/*), which is a later-wave concern once
// this lint graduates from report-only.
const SCAN_ROOT = join(__dirname, '..', '..', 'src', 'lib', 'retrieval', 'registry')

const MIN_ARRAY_LENGTH = 15
const MIN_IDENTIFIER_RATIO = 0.7
const SNAKE_CASE_RE = /^[a-z][a-z0-9_]*$/

interface Finding {
  file: string
  line: number
  constName: string
  elementCount: number
  identifierRatio: number
  sample: string[]
  confidence: 'HIGH' | 'MEDIUM'
}

/**
 * HIGH confidence: the const name itself declares it's a category/class/concept
 * enumeration (e.g. CHART_FACTS_CATEGORIES, PANCHANGA_CATEGORIES) — these are the
 * plan's flagship examples (GT-56/W-16/W-20/W-23). MEDIUM: shape matches Rule 1
 * but the name suggests a column list or tool-id list (e.g. COMPACT_FIELDS,
 * SURGICAL_TOOLS) — still worth a human look (a column list can BE a concept
 * enumeration in disguise), but not the doctrine's named target.
 */
const HIGH_CONFIDENCE_NAME_RE = /CATEGOR|CONCEPT|SIGNAL_TYPE|_CLASS(ES)?$/i

function walk(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    const st = statSync(full)
    if (st.isDirectory()) {
      walk(full, out)
    } else if (extname(entry) === '.ts' && !entry.endsWith('.test.ts') && !entry.includes('__tests__')) {
      out.push(full)
    }
  }
  return out
}

/** Find `const NAME = [ ... ]` (with optional `export`/type annotation) blocks via bracket matching. */
function findArrayLiterals(source: string): Array<{ name: string; startIndex: number; body: string }> {
  const results: Array<{ name: string; startIndex: number; body: string }> = []
  const declRe = /(?:export\s+)?const\s+(\w+)(?:\s*:\s*[^=]+)?\s*=\s*\[/g
  let m: RegExpExecArray | null
  while ((m = declRe.exec(source)) !== null) {
    const name = m[1]
    const bracketStart = m.index + m[0].length - 1 // index of the '['
    let depth = 0
    let i = bracketStart
    for (; i < source.length; i++) {
      if (source[i] === '[') depth++
      else if (source[i] === ']') {
        depth--
        if (depth === 0) break
      }
    }
    const body = source.slice(bracketStart + 1, i)
    results.push({ name, startIndex: m.index, body })
  }
  return results
}

function lineOf(source: string, index: number): number {
  return source.slice(0, index).split('\n').length
}

function analyzeFile(file: string): Finding[] {
  const source = readFileSync(file, 'utf-8')
  const findings: Finding[] = []

  for (const { name, startIndex, body } of findArrayLiterals(source)) {
    const stringLiteralRe = /'([^'\\]*(?:\\.[^'\\]*)*)'|"([^"\\]*(?:\\.[^"\\]*)*)"/g
    const elements: string[] = []
    let sm: RegExpExecArray | null
    while ((sm = stringLiteralRe.exec(body)) !== null) {
      elements.push(sm[1] ?? sm[2] ?? '')
    }
    if (elements.length < MIN_ARRAY_LENGTH) continue

    const identifierLike = elements.filter((e) => SNAKE_CASE_RE.test(e))
    const ratio = identifierLike.length / elements.length
    if (ratio < MIN_IDENTIFIER_RATIO) continue

    findings.push({
      file,
      line: lineOf(source, startIndex),
      constName: name,
      elementCount: elements.length,
      identifierRatio: Math.round(ratio * 100) / 100,
      sample: elements.slice(0, 5),
      confidence: HIGH_CONFIDENCE_NAME_RE.test(name) ? 'HIGH' : 'MEDIUM',
    })
  }
  return findings
}

function main(): void {
  const files = walk(SCAN_ROOT)
  const allFindings: Finding[] = []
  for (const file of files) {
    allFindings.push(...analyzeFile(file))
  }

  console.log(`[no_hardcoded_concept_lists] Scanned ${files.length} file(s) under ${SCAN_ROOT}`)
  console.log(`[no_hardcoded_concept_lists] Rule 1 threshold: >=${MIN_ARRAY_LENGTH} elements, >=${Math.round(MIN_IDENTIFIER_RATIO * 100)}% snake_case-identifier-shaped`)

  if (allFindings.length === 0) {
    console.log('[no_hardcoded_concept_lists] No hardcoded concept-list candidates found.')
    return
  }

  const high = allFindings.filter((f) => f.confidence === 'HIGH')
  const medium = allFindings.filter((f) => f.confidence === 'MEDIUM')
  console.log(`[no_hardcoded_concept_lists] ${allFindings.length} candidate(s) found (${high.length} HIGH confidence, ${medium.length} MEDIUM):\n`)
  for (const f of [...high, ...medium]) {
    console.log(`  [${f.confidence}] ${f.file}:${f.line}`)
    console.log(`    const ${f.constName} — ${f.elementCount} string elements, ${Math.round(f.identifierRatio * 100)}% identifier-shaped`)
    console.log(`    sample: ${JSON.stringify(f.sample)}`)
    console.log('')
  }
  console.log(
    '[no_hardcoded_concept_lists] These are candidates for eventual concept_ledger-derivation ' +
      '(plan §9.6 Concept Spine doctrine) once the W-25 harvest pipeline populates the ledger. ' +
      'v1: report-only, not a CI hard gate.',
  )
}

main()
