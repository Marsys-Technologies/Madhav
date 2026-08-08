/**
 * domain_vocabulary_census.test.ts — ADHIṢṬHĀNA Campaign A, Lane A7 census gate (TS side).
 * ================================================================================
 * Mirrors `platform/src/lib/retrieval/__tests__/graha_vocabulary_census.test.ts`'s pattern
 * (Lane A2) on the DOMAIN-classification vocabulary (career/wealth/relationship/health/…),
 * a completely different vocabulary from the graha-identifier work A1/A2 already closed.
 * R17 (Adoption over addition) requires acceptance by an actual, detector-cited removal
 * census, not an estimate — this file is that detector, committed and re-runnable.
 *
 * `platform/src/lib/domain_vocabulary.ts` (CANONICAL_DOMAINS / CanonicalDomain — the TS
 * mirror of the Python SSoT `brahmagyan/domain_vocabulary.py`) is the ONE permitted
 * independent domain-vocabulary declaration. Every other TS domain-vocabulary-shaped
 * literal found tree-wide is either:
 *   - migrated to import CanonicalDomain / CANONICAL_DOMAINS directly (or a type derived
 *     from it, e.g. `Exclude<CanonicalDomain, 'x'> | 'y'`, which this scanner cannot see as
 *     an independent literal — same "derivation, not a literal" pass signal the graha
 *     census uses for `Object.fromEntries([...].map(x => [x, grahaCodeOf(x)]))`), or
 *   - a documented, reasoned exclusion in INTENTIONAL_EXCLUSIONS below (a genuinely
 *     different vocabulary that happens to share tokens with the domain vocabulary).
 *
 * WHAT IS A VIOLATION: a TS source file (outside domain_vocabulary.ts and this file itself)
 * declaring EITHER
 *   (a) a string-literal type union (`type X = 'career' | 'wealth' | ...`), OR
 *   (b) a `const X = [...] as const` / plain array literal, OR
 *   (c) an inline tool-schema `enum: [...]` property
 * with >= DOMAIN_TOKEN_THRESHOLD (4) distinct string members drawn from the canonical
 * 13-domain vocabulary, its 19 known synonyms, or the two extra tokens this scanner
 * recognizes for detection purposes only ('other', 'litigation' — neither is a
 * domain_vocabulary.py synonym; 'other' is the pre-Lane-A7 ad hoc fallback several files
 * used, 'litigation' is scope_classifier.ts's own documented non-equivalent term).
 */
import { describe, it, expect } from 'vitest'
import * as fs from 'node:fs'
import * as path from 'node:path'
import * as ts from 'typescript'
import { CANONICAL_DOMAINS, DOMAIN_SYNONYMS } from '../../domain_vocabulary'

const REPO_SRC = path.resolve(__dirname, '../../../')
const SCAN_DIRS = ['lib', 'app', 'components'].map(d => path.join(REPO_SRC, d))

// Domain-token vocabulary this scanner recognizes as "members of a domain-vocabulary
// declaration": the 13 canonical domains + their 19 known synonyms (from the Python/TS SSoT
// itself) + two detection-only extras that are NOT SSoT synonyms but appeared as ad hoc
// fallback/adjacent terms across the pre-Lane-A7 codebase ('other', 'litigation' — see
// domain_vocabulary.py's own docstring, which explicitly calls out 'litigation' as a
// scope_classifier.ts-only concept with no canonical equivalent).
const DOMAIN_TOKENS = new Set<string>(
  [...CANONICAL_DOMAINS, ...Object.keys(DOMAIN_SYNONYMS), 'other', 'litigation'].map(s => s.toLowerCase()),
)

const DOMAIN_TOKEN_THRESHOLD = 4

const SSOT_FILE = 'domain_vocabulary.ts'

// ── Known-safe exclusions ──────────────────────────────────────────────────────
const EXCLUDED_PATH_SUBSTRINGS = ['__tests__', '.test.ts', '.gate.test.ts', 'node_modules', '/generated/']

// Documented, reasoned exclusions: (fileBasename, declaredName) pairs that remain
// independent by design, not by omission — each is a genuinely different vocabulary that
// happens to share string tokens with the domain vocabulary, verified by reading the file
// (not assumed from the name), same discipline as Lane A2's bo_laksana exclusion.
const INTENTIONAL_EXCLUSIONS = new Map<string, string>([
  [
    'scope_classifier.ts::DOMAINS',
    "Query-INTENT classification vocabulary (marriage/children/litigation/property, natural " +
    "user-facing terms), a faithful port of platform-mcp/src/tools/intent_scope_classifier.ts " +
    "(file's own docstring: 'do not diverge — this is a port, not a redesign', DR-8). Not the " +
    "domain-TAGGING vocabulary L2+ signals use. domain_vocabulary.py's own docstring already " +
    "carves this out: \"litigation is NOT a synonym — it's a scope_classifier.ts-only concept " +
    "with no canonical domain equivalent.\" Force-migrating would break DR-8 port-fidelity and " +
    "drop terms (litigation) with no canonical equivalent to migrate TO.",
  ],
  [
    'intent.ts::domains',
    "Not a vocabulary redefinition — the P-10 keyword classifier's own list of which of the " +
    "13 canonical domains it has real keyword content for (a subset selector). Every member " +
    "is already sourced from the imported CanonicalDomain type (see types.ts/intent.ts Lane " +
    "A7 comments); this array picks 6 of them for iteration, the same role bo_drishti.py's " +
    "keyword lists play in the Python census's safe-exclusion list.",
  ],
  [
    'get_vichara.ts::VICHARA_DOMAINS',
    "\"Closed domain vocabulary (design §11 operative-varga registry — wealth is design-" +
    "ratified)\" per the file's own comment — a deliberately narrow, closed vocabulary for one " +
    "specific chart_vichara feature, not the general domain-classification vocabulary. Only " +
    "'wealth' is design-ratified; migrating to the 13-domain SSoT would silently widen a " +
    "closed, ratified feature list.",
  ],
  [
    'query_muhurat.ts::VALID_ACTION_TYPES',
    "Muhurta ACTION types (marriage|travel|business|medical|education|property|general — " +
    "\"what activity are you timing\"), the backing Python engine's (brahmagyan/phala/" +
    "muhurta.py) action_types parameter. A different axis from life-domain classification of " +
    "chart signals, despite token overlap (marriage/travel/education/property/general).",
  ],
  [
    'TimelineView.tsx::CATEGORIES',
    "LEL (Life Event Log) UI category picker for logging discrete biographical events — " +
    "includes non-domain terms ('loss', 'all') the domain vocabulary has no equivalent for. " +
    "A related-but-distinct taxonomy from domain-tagging of chart signals (LEL event " +
    "categories vs. domain classification). Same exclusion applies to LogEventDialog.tsx and " +
    "PratikrutiClient.tsx below — all three are LEL intake/display pickers, independently " +
    "drifted from EACH OTHER (9/11/9 members) as their own, separate adoption-debt problem " +
    "flagged to the backlog, not fixed in this lane (LEL category unification is a different " +
    "vocabulary than domain classification).",
  ],
  [
    'LogEventDialog.tsx::CATEGORIES',
    "LEL UI category picker — see TimelineView.tsx::CATEGORIES exclusion above (same reasoning).",
  ],
  [
    'PratikrutiClient.tsx::EVENT_CLASSES',
    "LEL UI category picker (named EVENT_CLASSES but is the LEL intake form's category field, " +
    "not the L0 ghatana EVENT_CLASSES/event_classes.ts vocabulary Lane A4 fixed) — see " +
    "TimelineView.tsx::CATEGORIES exclusion above (same reasoning).",
  ],
  [
    'types.ts::Domain',
    "lib/schools/types.ts's `Domain` (uppercase CAREER/HEALTH/RELATIONSHIP/SPIRITUAL/" +
    "PSYCHOLOGICAL, 5 members) backs the M9 multi-school-triangulation subsystem (7 school " +
    "engines: parashari/jaimini/tajika/kp/nadi/bnn/yogini + school_runner.ts + the school-" +
    "consensus build route). NOT in this lane's declared scope (the brief named 4 files; this " +
    "is a 5th, previously-undocumented one this full-tree census surfaced, same as Lane A2 " +
    "finding 12 more graha maps than its own estimate). Flagged to the backlog rather than " +
    "force-migrated in-lane: fixing it correctly means rewriting the uppercase convention " +
    "across 9 files AND fixing what this census found to be a LIVE BUG — " +
    "app/api/build/school-consensus/route.ts inserts these UPPERCASE values directly into " +
    "school_analysis_runs.domain / convergence_scores.domain, both governed by migration 386's " +
    "LOWERCASE-only CHECK constraint (verified by reading 386_canonical_domain_normalization.sql " +
    "§8) — a runtime CHECK-violation risk that predates this lane and is out of its declared " +
    "scope to fix. See ADHISTHANA_STATE.md backlog for the carried-forward finding.",
  ],
  [
    'school_runner.ts::ALL_DOMAINS',
    "Same M9 schools subsystem as lib/schools/types.ts::Domain above (same reasoning).",
  ],
  [
    'route.ts::ALL_DOMAINS',
    "app/api/build/school-consensus/route.ts — same M9 schools subsystem as " +
    "lib/schools/types.ts::Domain above (this is the file where the live CHECK-violation risk " +
    "was found; see that exclusion's note).",
  ],
])

interface Hit { file: string; name: string; line: number; kind: string; tokens: string[] }

function collectTsFiles(dir: string, out: string[]): void {
  if (!fs.existsSync(dir)) return
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue
      collectTsFiles(full, out)
    } else if (entry.isFile() && (entry.name.endsWith('.ts') || entry.name.endsWith('.tsx'))) {
      if (EXCLUDED_PATH_SUBSTRINGS.some(s => full.includes(s))) continue
      if (entry.name === SSOT_FILE) continue
      out.push(full)
    }
  }
}

function domainTokensOfStringLiteralUnion(node: ts.TypeNode): string[] {
  if (!ts.isUnionTypeNode(node)) return []
  const toks: string[] = []
  for (const t of node.types) {
    if (ts.isLiteralTypeNode(t) && ts.isStringLiteral(t.literal)) {
      const v = t.literal.text.toLowerCase()
      if (DOMAIN_TOKENS.has(v)) toks.push(v)
    }
  }
  return toks
}

function domainTokensOfArrayLiteral(node: ts.ArrayLiteralExpression): string[] {
  const toks: string[] = []
  for (const el of node.elements) {
    if (ts.isStringLiteral(el)) {
      const v = el.text.toLowerCase()
      if (DOMAIN_TOKENS.has(v)) toks.push(v)
    }
  }
  return toks
}

function findDomainVocabsInFile(filePath: string): Hit[] {
  const source = fs.readFileSync(filePath, 'utf-8')
  const sf = ts.createSourceFile(filePath, source, ts.ScriptTarget.Latest, true)
  const found: Hit[] = []

  function visit(node: ts.Node) {
    if (ts.isTypeAliasDeclaration(node)) {
      const toks = domainTokensOfStringLiteralUnion(node.type)
      if (new Set(toks).size >= DOMAIN_TOKEN_THRESHOLD) {
        const { line } = sf.getLineAndCharacterOfPosition(node.getStart())
        found.push({ file: filePath, name: node.name.text, line: line + 1, kind: 'type_union', tokens: [...new Set(toks)] })
      }
    }
    if (ts.isVariableDeclaration(node) && node.initializer) {
      let arrExpr: ts.ArrayLiteralExpression | null = null
      if (ts.isArrayLiteralExpression(node.initializer)) arrExpr = node.initializer
      else if (ts.isAsExpression(node.initializer) && ts.isArrayLiteralExpression(node.initializer.expression)) arrExpr = node.initializer.expression
      if (arrExpr) {
        const toks = domainTokensOfArrayLiteral(arrExpr)
        if (new Set(toks).size >= DOMAIN_TOKEN_THRESHOLD) {
          const { line } = sf.getLineAndCharacterOfPosition(node.getStart())
          const name = ts.isIdentifier(node.name) ? node.name.text : '<destructured>'
          found.push({ file: filePath, name, line: line + 1, kind: 'array_literal', tokens: [...new Set(toks)] })
        }
      }
    }
    // Inline tool-schema `enum: [...]` properties (MCP CapabilityDescriptor input_schema).
    if (ts.isPropertyAssignment(node) && ts.isIdentifier(node.name) && node.name.text === 'enum' && ts.isArrayLiteralExpression(node.initializer)) {
      const toks = domainTokensOfArrayLiteral(node.initializer)
      if (new Set(toks).size >= DOMAIN_TOKEN_THRESHOLD) {
        const { line } = sf.getLineAndCharacterOfPosition(node.getStart())
        found.push({ file: filePath, name: 'enum:<inline>', line: line + 1, kind: 'schema_enum', tokens: [...new Set(toks)] })
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
    for (const hit of findDomainVocabsInFile(f)) {
      const key = `${path.basename(hit.file)}::${hit.name}`
      if (INTENTIONAL_EXCLUSIONS.has(key)) continue
      allHits.push(hit)
    }
  }
  return allHits
}

describe('domain vocabulary census (TS)', () => {
  it('scanner reaches known lane-touched files', () => {
    const files: string[] = []
    for (const dir of SCAN_DIRS) collectTsFiles(dir, files)
    const rels = files.map(f => path.relative(REPO_SRC, f))
    expect(rels).toContain(path.join('lib', 'retrieval', 'synthesis', 'types.ts'))
    expect(rels).toContain(path.join('lib', 'retrieval', 'spine', 'constants.ts'))
    expect(rels).toContain(path.join('lib', 'retrieval', 'ranking', 'priors_config.ts'))
    expect(rels).toContain(path.join('lib', 'vidhi', 'scope_classifier.ts'))
  })

  it('SSoT file (domain_vocabulary.ts) is excluded from the scan', () => {
    const files: string[] = []
    for (const dir of SCAN_DIRS) collectTsFiles(dir, files)
    expect(files.map(f => path.basename(f))).not.toContain(SSOT_FILE)
  })

  it('every documented INTENTIONAL_EXCLUSIONS entry is still actually found by the raw scanner', () => {
    // Guards against a stale exclusion: if a file is later migrated (or deleted) and its
    // entry is left in INTENTIONAL_EXCLUSIONS, that's silently hiding a should-be-caught
    // regression path. This test fails loudly instead — mirrors the graha census's spirit
    // of "the exclusion list is audited, not just trusted."
    const files: string[] = []
    for (const dir of SCAN_DIRS) collectTsFiles(dir, files)
    const rawHitKeys = new Set<string>()
    for (const f of files) {
      for (const hit of findDomainVocabsInFile(f)) {
        rawHitKeys.add(`${path.basename(hit.file)}::${hit.name}`)
      }
    }
    for (const key of INTENTIONAL_EXCLUSIONS.keys()) {
      expect(rawHitKeys, `stale exclusion entry (no longer found by scanner): ${key}`).toContain(key)
    }
  })

  it('THE GATE (R17): 0 unexplained independent TS domain vocabularies survive tree-wide', () => {
    // BEFORE Lane A7 (measured by this exact scanner shape, re-run directly against the
    // pre-lane git tree): 16 independent domain-vocabulary-shaped literals found tree-wide
    // across 14 files. 4 matched the lane brief's own named set exactly:
    //   retrieval/synthesis/types.ts::Domain (7: 6 + 'other')
    //   retrieval/spine/constants.ts::SPINE_DOMAINS (7: 6 + 'other')
    //   retrieval/ranking/priors_config.ts::Domain (12: 11 canonical + 'moksha')
    //   vidhi/scope_classifier.ts::DOMAINS (11, incl. 'litigation'/'marriage'/'children'/'property')
    // The other 12 were surfaced by this full-tree census (the brief's "4" was an estimate,
    // same pattern as Lane A2's graha census finding 18 instead of an estimated 6):
    //   L2_bodha/query_domain_reading.ts (an inline schema enum + a VALID_DOMAINS array,
    //     2 hits) and L4_phala/query_domain_result.ts (a schema enum) — both MIGRATED to
    //     import CANONICAL_DOMAINS; query_domain_result.ts's fix also corrected a real stale-
    //     count bug (its "7 rows"/'6+other' enum was left behind when ph_phaladesa.py was
    //     already extended to write all 13 canonical domains per chart, SHABDA-SHUDDHI Lane
    //     L5 Fix 5 — the enum just never caught up).
    //   retrieval/synthesis/intent.ts::domains, vidhi/scope_classifier.ts (already counted
    //     above), L1_ganita/get_vichara.ts::VICHARA_DOMAINS, L4_phala/query_muhurat.ts::
    //     VALID_ACTION_TYPES, 3 LEL UI category pickers (TimelineView/LogEventDialog/
    //     PratikrutiClient), and lib/schools/types.ts::Domain + school_runner.ts::ALL_DOMAINS
    //     + school-consensus/route.ts::ALL_DOMAINS (3 hits, one subsystem) — all DOCUMENTED,
    //     REASONED EXCLUSIONS in INTENTIONAL_EXCLUSIONS above (verified by reading each file,
    //     not assumed from the name), not silently dropped.
    // AFTER: 0 outside the SSoT and the documented exclusions — domain_vocabulary.ts is the
    // one permitted canonical file (excluded from the scan by file name).
    const hits = runCensus()
    if (hits.length > 0) {
      const lines = ['Independent TS domain vocabularies found outside the SSoT (R17 violation):']
      for (const h of hits) {
        lines.push(`  ${path.relative(REPO_SRC, h.file)}:${h.line}: '${h.name}' [${h.kind}] (${h.tokens.length} tokens: ${h.tokens.join(',')})`)
      }
      throw new Error(lines.join('\n'))
    }
    expect(hits).toHaveLength(0)
  })
})
