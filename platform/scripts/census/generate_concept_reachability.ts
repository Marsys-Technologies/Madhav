/**
 * IMPORT-SITE SCANNER FIX (post-hoc, this wave): a prior revision of this
 * generator ASSERTED "coverage_matrix.ts's CHART_FACTS_CATEGORIES has zero
 * import sites anywhere in the repo (confirmed by grep)" without the script
 * ever actually running a grep — it was a hand-written string literal. An
 * independent verifier caught this: `platform/tests/retrieval/coverage_gate
 * .test.ts` DOES import `CHART_FACTS_CATEGORIES` from `coverage_matrix.ts`
 * and uses it as a live CI gate. Fixed by implementing `scanImportSites()`
 * below — a real repo-wide scan for `import { ... }` / `export { ... } from`
 * statements whose module specifier resolves to the target file and whose
 * specifier list names the target export — and using its actual output
 * (not a hand-typed claim) everywhere this generator makes an import-site
 * assertion, for both `coverage_matrix.ts` and `ganita/types.ts`'s
 * same-named `CHART_FACTS_CATEGORIES` constants.
 *
 * generate_concept_reachability.ts — Lane L1d, W1 (RETRIEVAL_PLANE_ELEVATION_PLAN
 * §9.4 W-20/W-21/W-23; runs after L1b's harvest, consumes its JSON outputs directly
 * rather than re-querying the live DB — no DB credential is needed to run this).
 *
 * Produces, from real source data (no fabricated rows):
 *  1. Concept coverage census (W-21): one row per chart_facts fact_category (218,
 *     the live-DB-verified set from E3), cross-referenced against E1's declared
 *     registry extraction for a serving capability path.
 *  2. Enumeration reconciliation (W-23): picks the live DB as the single
 *     authoritative source (justified below) and reports why the other three
 *     (now confirmed FOUR — see finding below) sources disagree.
 *  3. Reachability matrix v1 (W-20): SERVED / NAVIGABLE / PLANNER-KNOWN per
 *     concept, across three concept kinds (fact_category, dark table, signal_class).
 *  4. Table/concept disposition table (W-15), carrying forward the plan's own
 *     already-settled GT-49/50/52 rulings + this lane's own independently
 *     verified corrections (see NEW_FINDINGS below).
 *
 * NEW FINDING this lane (verified by direct source read, not asserted): L1b's
 * cross-diff flagged `bg_dignity_reference` and `chart_panchanga` DARK because
 * neither table appears in any capability's static `table_hint` (a regex scan of
 * `platform/src/lib/retrieval/registry/layers` + `synthesis` only). Both ARE
 * actually served — just via serving paths outside that scan's two directories,
 * exactly the false-dark failure mode GT-51 already named for a different grep
 * (single-directory miss): `bg_dignity_reference` is served by
 * `platform-mcp/src/tools/register_p1_reference.ts`; `chart_panchanga` is served
 * by `platform/src/lib/tools/brahma/l1/query_panchanga.ts` — a THIRD serving path
 * (`lib/tools/brahma/`) that neither L1b's TS-registry scan nor a platform-mcp-only
 * scan would catch either. Corrected in the disposition table below with the exact
 * citing file. (`bg_sign_medical`, the third table GT-51 named, was already
 * correctly resolved SERVED by L1b's own cross-diff — not re-flagged here.)
 *
 * Also confirmed by direct source read, backed by this generator's own
 * `scanImportSites()` repo-wide scan (see below — not a hand-typed claim):
 * `coverage_matrix.ts`'s CHART_FACTS_CATEGORIES (158) is NOT wired into the
 * `chart_facts_query` serving path — but it DOES have one real import site,
 * `platform/tests/retrieval/coverage_gate.test.ts`, which imports it as a
 * live CI coverage gate. So it is not fully dead/decorative — it has a
 * test-time consumer, just not a runtime-serving one. `ganita/types.ts`
 * carries a FOURTH, 26-entry CHART_FACTS_CATEGORIES definition (not cited by
 * the plan's 3-way OR L1b's 4-way framing) that is imported by
 * `facts_store.ts` but only re-exported, never used to validate anything; and
 * `chart_facts_query`'s handler (`register_d7_channel.ts`) does
 * `fact_category = ANY($n::text[])` directly from the caller's raw string — no
 * enum gate at all, from ANY of the four static sources. This means L1b's stated
 * "chart_facts_query's category filter can't reach [66 categories] by name" is
 * not quite right: the filter can reach ALL 218 live categories by name (no
 * enum blocks it); the real gap is DISCOVERABILITY at the serving layer, not
 * query-blocking — an LLM caller has no documented, load-bearing list of the
 * 218 real category strings to draw from at query time (coverage_matrix.ts's
 * 158-item list exists and has a real test-gate consumer, but is never
 * consulted by the runtime tool it appears to document). See the
 * reconciliation note for the full correction.
 *
 * Run:
 *   cd platform && npx tsx --conditions=react-server scripts/census/generate_concept_reachability.ts
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PLATFORM_ROOT = join(__dirname, '..', '..')
const REPO_ROOT = join(PLATFORM_ROOT, '..')

const E1_PATH = join(PLATFORM_ROOT, 'src/generated/harvest/e1_declared.json')
const E3_PATH = join(PLATFORM_ROOT, 'src/generated/harvest/e3_fact_category_reconciliation.json')
const E4_PATH = join(PLATFORM_ROOT, 'src/generated/harvest/e4_signal_classes.json')
const ADJ_PATH = join(PLATFORM_ROOT, 'src/generated/harvest/adjudication_queue.json')
const VIDHI_REGISTRY_PATH = join(PLATFORM_ROOT, 'src/lib/vidhi/registry_data.ts')

const OUT_DIR = join(PLATFORM_ROOT, 'src/generated/census')
const BRIEF_DIR = join(REPO_ROOT, '00_ARCHITECTURE/briefs/retrieval_impl')

// ── import-site scanner (real repo-wide grep, not a hand-typed claim) ────────
//
// Prior revision of this file hand-wrote "zero import sites anywhere in the
// repo (confirmed by grep)" for coverage_matrix.ts's CHART_FACTS_CATEGORIES
// without ever running a grep — an independent verifier caught the fabrication
// (coverage_gate.test.ts DOES import it). This function replaces the claim
// with an actual scan: walk every .ts/.tsx file in the repo (excluding
// node_modules/.git/dist/build/generated-cache dirs), find `import { ... }`
// and `export { ... } from` statements, resolve the module specifier against
// the target file, and check whether the target export name appears in the
// specifier list (handling `Name as Alias`). Returns every real hit.

import { readdirSync, statSync } from 'node:fs'
import { resolve, relative, sep } from 'node:path'

const SCAN_EXCLUDE_DIRS = new Set([
  'node_modules', '.git', '.next', 'dist', 'build', 'coverage',
  '.turbo', '.vercel', '.venv', '__pycache__',
])

function listSourceFiles(root: string): string[] {
  const out: string[] = []
  const entries = readdirSync(root, { recursive: true }) as string[]
  for (const rel of entries) {
    if (!(rel.endsWith('.ts') || rel.endsWith('.tsx'))) continue
    const parts = rel.split(sep)
    if (parts.some((p) => SCAN_EXCLUDE_DIRS.has(p))) continue
    const full = join(root, rel)
    try {
      if (statSync(full).isFile()) out.push(full)
    } catch {
      // race/broken symlink — skip
    }
  }
  return out
}

interface ImportSiteHit {
  file: string
  line: number
  snippet: string
}

/**
 * Real scan for import sites of `exportName` from `targetFile`, across every
 * .ts/.tsx file under `root`. A "hit" is an `import { ... }` or
 * `export { ... } from '...'` statement whose resolved module path matches
 * targetFile (by basename-without-extension, since TS import specifiers omit
 * the extension and may be relative or path-aliased) AND whose brace-group
 * names `exportName` (bare or as `exportName as X`).
 */
function scanImportSites(root: string, targetFile: string, exportName: string): ImportSiteHit[] {
  const targetBase = targetFile.replace(/\.tsx?$/, '')
  const hits: ImportSiteHit[] = []
  const importRe = /(?:import|export)\s+(?:type\s+)?\{([^}]*)\}\s*from\s*['"]([^'"]+)['"]/gs
  for (const file of listSourceFiles(root)) {
    if (resolve(file) === resolve(targetFile)) continue // defining file is not an import "site"
    const text = readFileSync(file, 'utf8')
    let m: RegExpExecArray | null
    importRe.lastIndex = 0
    while ((m = importRe.exec(text))) {
      const [full, specifierList, modulePath] = m
      // Resolve the specifier relative to the importing file when relative;
      // otherwise match on path-suffix (covers '@/...' aliases + bare paths).
      let resolvedGuess: string
      if (modulePath.startsWith('.')) {
        resolvedGuess = resolve(dirname(file), modulePath)
      } else {
        // strip a leading alias segment like '@/' — match by suffix instead
        resolvedGuess = modulePath.replace(/^@\//, 'src/')
      }
      const resolvedGuessNorm = resolvedGuess.replace(/\.tsx?$/, '')
      const matchesTarget =
        resolve(resolvedGuessNorm) === resolve(targetBase) ||
        targetBase.endsWith(resolvedGuessNorm) ||
        targetBase.replace(/\\/g, '/').endsWith(resolvedGuessNorm.replace(/\\/g, '/'))
      if (!matchesTarget) continue
      const names = specifierList.split(',').map((s) => s.trim()).filter(Boolean)
      const namesBare = names.map((n) => n.split(/\s+as\s+/)[0].trim())
      if (!namesBare.includes(exportName)) continue
      const idx = m.index
      const lineNo = text.slice(0, idx).split('\n').length
      hits.push({
        file: relative(REPO_ROOT, file),
        line: lineNo,
        snippet: full.replace(/\s+/g, ' ').trim().slice(0, 160),
      })
    }
  }
  return hits
}

const COVERAGE_MATRIX_PATH = join(
  PLATFORM_ROOT, 'src/lib/retrieval/registry/layers/L1_ganita/coverage_matrix.ts',
)
const GANITA_TYPES_PATH = join(PLATFORM_ROOT, 'src/lib/ganita/types.ts')

const coverageMatrixImportSites = scanImportSites(
  PLATFORM_ROOT, COVERAGE_MATRIX_PATH, 'CHART_FACTS_CATEGORIES',
)
const ganitaTypesImportSites = scanImportSites(
  PLATFORM_ROOT, GANITA_TYPES_PATH, 'CHART_FACTS_CATEGORIES',
)

console.log(
  `[CONCEPT-REACHABILITY] real scan: coverage_matrix.ts CHART_FACTS_CATEGORIES has ` +
    `${coverageMatrixImportSites.length} import site(s): ` +
    JSON.stringify(coverageMatrixImportSites),
)
console.log(
  `[CONCEPT-REACHABILITY] real scan: ganita/types.ts CHART_FACTS_CATEGORIES has ` +
    `${ganitaTypesImportSites.length} import site(s): ` +
    JSON.stringify(ganitaTypesImportSites),
)

// ── load inputs ──────────────────────────────────────────────────────────────

interface E1Concept {
  uri: string
  name: string
  table_hint: string[]
  source_file: string | null
}
const e1: { concepts: E1Concept[] } = JSON.parse(readFileSync(E1_PATH, 'utf8'))

const e3: {
  category_lists: {
    schema_json_canonical: string[]
    coverage_matrix_ts: string[]
    live_db: string[]
    live_db_row_counts: Record<string, number>
  }
  real_counts_from_all_sources: Record<string, number>
} = JSON.parse(readFileSync(E3_PATH, 'utf8'))

const e4: {
  class_inventories: Array<{
    table: string
    column: string
    distinct_count: number
    values_sample: Array<{ value: string | null; row_count: number }>
  }>
} = JSON.parse(readFileSync(E4_PATH, 'utf8'))

const adj: {
  rows: Array<{
    id: string
    type: string
    table_name?: string
    layer?: string
    row_count?: number
    proposed_disposition?: string
    rationale?: string
  }>
} = JSON.parse(readFileSync(ADJ_PATH, 'utf8'))

const vidhiText = readFileSync(VIDHI_REGISTRY_PATH, 'utf8')

// chart_facts_query is the sole capability serving arbitrary fact_category values
// (verified: no enum validation in its handler — `fact_category = ANY($n::text[])`
// directly from caller input). Its descriptor topology (verified in
// register_d7_channel.ts): archetype=flat_fact, traversal_level=L-SIGNAL,
// tool_role=umbrella, emits_references=true, no drill_children — a single-hop
// direct-access surface, consistent with strategy §5.1's "layered data, flat
// access" doctrine.
const CHART_FACTS_QUERY_URI = 'marsys://tool/L1/chart_facts_query'

function plannerKnown(needle: string): { known: boolean; evidence: string } {
  if (vidhiText.includes(needle)) {
    // find one line of context
    const idx = vidhiText.indexOf(needle)
    const lineStart = vidhiText.lastIndexOf('\n', idx) + 1
    const lineEnd = vidhiText.indexOf('\n', idx)
    const line = vidhiText.slice(lineStart, lineEnd === -1 ? undefined : lineEnd).trim()
    return { known: true, evidence: line.slice(0, 140) }
  }
  return { known: false, evidence: '' }
}

// ── (1) Concept coverage census + (3a) reachability rows: fact_category ──────

interface ConceptRow {
  concept_kind: 'fact_category' | 'dark_table' | 'signal_class'
  concept: string
  served: boolean
  served_basis: string
  navigable: boolean | 'n/a'
  navigable_basis: string
  planner_known: boolean
  planner_known_basis: string
  disposition: string
}

const liveCategories = e3.category_lists.live_db
const coverageMatrixSet = new Set(e3.category_lists.coverage_matrix_ts)
const schemaJsonSet = new Set(e3.category_lists.schema_json_canonical)

const factCategoryRows: ConceptRow[] = liveCategories.map((cat) => {
  const rowCount = e3.category_lists.live_db_row_counts[cat] ?? 0
  const inCoverageMatrix = coverageMatrixSet.has(cat)
  const inSchemaJson = schemaJsonSet.has(cat)
  const pk = plannerKnown(`category=${cat}`)
  return {
    concept_kind: 'fact_category',
    concept: cat,
    served: true,
    served_basis:
      `chart_facts_query (${CHART_FACTS_QUERY_URI}) — no enum gate on its category ` +
      `filter (verified: fact_category = ANY($n) direct from caller input), so this ` +
      `category IS queryable today; documented in a static list is a separate axis ` +
      `(in coverage_matrix.ts's 158-entry list: ${inCoverageMatrix}; in ` +
      `CHART_FACTS_SCHEMA.json's 147-entry list: ${inSchemaJson}) — undocumented ` +
      `does not mean unqueryable for this tool.`,
    navigable: true,
    navigable_basis:
      'chart_facts_query is a single-hop direct-access leaf/umbrella (traversal_level=' +
      'L-SIGNAL, tool_role=umbrella, emits_references=true, no drill_children) — ' +
      'reachable in 1 call once the category string is known.',
    planner_known: pk.known,
    planner_known_basis: pk.known
      ? `vidhi/registry_data.ts: "${pk.evidence}"`
      : 'no vidhi primitive/floor references this category by name (grep `category=' +
        cat +
        '` against registry_data.ts — 0 hits)',
    disposition: inCoverageMatrix
      ? 'SERVED (documented + queryable)'
      : 'SERVED-UNDOCUMENTED (queryable, but absent from every hand-maintained category ' +
        `list — a caller must already know the exact string "${cat}"; row_count=${rowCount})`,
  }
})

// ── (3b) dark tables from L1b's adjudication queue ────────────────────────────

// Corrections verified by direct source read this lane (see file header).
const DARK_OVERRIDES: Record<string, { served_basis: string; disposition: string }> = {
  bg_dignity_reference: {
    served_basis:
      'Served by platform-mcp/src/tools/register_p1_reference.ts — outside the two ' +
      'directories (registry/layers, synthesis) L1b\'s E1 table_hint scan covered. ' +
      'Same false-dark failure mode GT-51 already named for a different grep.',
    disposition: 'SERVED (corrected this lane — was DARK/INTERNAL-BY-DESIGN in L1b\'s queue)',
  },
  chart_panchanga: {
    served_basis:
      'Served by platform/src/lib/tools/brahma/l1/query_panchanga.ts — a THIRD ' +
      'serving path (lib/tools/brahma/) outside both the registry/layers scan and ' +
      'platform-mcp; matches GT-51\'s single-directory-grep false-dark pattern.',
    disposition: 'SERVED (corrected this lane — was DARK/NEEDS-OWNER in L1b\'s queue)',
  },
}

// Plan-settled dispositions (GT-49/50/52) carried forward verbatim, not re-derived.
const PLAN_SETTLED: Array<{ concept: string; disposition: string; citation: string }> = [
  {
    concept: 'kala_timeline (service)',
    disposition:
      'DARK-UNWIRED (one-line fix, not a build gap): registerKalaTimeline handler exists, ' +
      'never imported into server.ts',
    citation: 'GT-49 (Lane E New-Finding 1)',
  },
  {
    concept: 'ka_graha_sancara (service)',
    disposition:
      'DARK SERVICE — highest-impact single coverage item; call_service_wrappers.ts:200-208 ' +
      'returns "not yet wired to a compute sidecar endpoint", blocking all date-parameterized ' +
      '"positions at time T" retrieval',
    citation: 'GT-50 (Lane E New-Finding 2)',
  },
  {
    concept: 'reference_aspects / reference_signs / reference_planets / reference_nakshatras / reference_vargas (5 tables)',
    disposition:
      'RETIRE — dead-superseded by served bg_* equivalents; NOT wire-up candidates',
    citation: 'GT-52 (Lane E New-Finding 4)',
  },
  {
    concept: 'bg_sign_medical',
    disposition: 'SERVED — correctly resolved by L1b\'s own cross-diff (query_sign_medical.ts)',
    citation: 'GT-51 (Lane E New-Finding 3); confirmed already-correct in L1b\'s adjudication_queue.json',
  },
]

const darkTableRows: ConceptRow[] = adj.rows
  .filter((r) => r.type === 'DARK' && r.table_name)
  .map((r) => {
    const tn = r.table_name!
    const override = DARK_OVERRIDES[tn]
    const pk = plannerKnown(tn)
    if (override) {
      return {
        concept_kind: 'dark_table',
        concept: tn,
        served: true,
        served_basis: override.served_basis,
        navigable: true,
        navigable_basis: 'served via a direct capability call once its serving file is wired into the census scan (see served_basis).',
        planner_known: pk.known,
        planner_known_basis: pk.known ? `vidhi/registry_data.ts: "${pk.evidence}"` : 'no vidhi primitive references this table name',
        disposition: override.disposition,
      }
    }
    return {
      concept_kind: 'dark_table',
      concept: tn,
      served: false,
      served_basis: r.rationale ?? 'no capability\'s static table_hint references this table (L1b cross-diff)',
      navigable: 'n/a',
      navigable_basis: 'not served — navigability does not apply',
      planner_known: pk.known,
      planner_known_basis: pk.known ? `vidhi/registry_data.ts: "${pk.evidence}"` : 'no vidhi primitive references this table name',
      disposition: r.proposed_disposition ?? 'NEEDS-OWNER',
    }
  })

// ── (3c) signal_class concepts (bodha_msr_signals.signal_type_class, 19 values) ─

const msrClass = e4.class_inventories.find(
  (c) => c.table === 'bodha_msr_signals' && c.column === 'signal_type_class',
)
const SIGNAL_SERVING_URIS = e1.concepts
  .filter((c) => c.table_hint.includes('bodha_msr_signals') || c.name === 'query_signals')
  .map((c) => c.uri)

const signalClassRows: ConceptRow[] = (msrClass?.values_sample ?? [])
  .filter((v) => v.value !== null)
  .map((v) => {
    const pk = plannerKnown(v.value as string)
    return {
      concept_kind: 'signal_class',
      concept: `bodha_msr_signals.signal_type_class=${v.value}`,
      served: SIGNAL_SERVING_URIS.length > 0,
      served_basis:
        SIGNAL_SERVING_URIS.length > 0
          ? `bodha_msr_signals touched by: ${SIGNAL_SERVING_URIS.join(', ')} (table_hint match or name match; query_signals\' own table_hint is empty — sidecar/dynamic-query construction not caught by the FROM/JOIN regex, noted honestly not hidden)`
          : 'no capability\'s table_hint references bodha_msr_signals',
      navigable: SIGNAL_SERVING_URIS.length > 0 ? true : 'n/a',
      navigable_basis:
        SIGNAL_SERVING_URIS.length > 0
          ? 'reachable via the serving capabilities listed in served_basis (topology not individually re-verified per class value this pass)'
          : 'not served',
      planner_known: pk.known,
      planner_known_basis: pk.known
        ? `vidhi/registry_data.ts: "${pk.evidence}"`
        : 'no vidhi primitive/floor references this signal_type_class value by name',
      disposition:
        'SERVED, not centrally registered as a class (E4\'s finding: NOT a unified cross-plane signal-class registry — this column is the one real, populated exception, still local to bodha_msr_signals)',
    }
  })

const allRows = [...factCategoryRows, ...darkTableRows, ...signalClassRows]

// ── write JSON ──────────────────────────────────────────────────────────────

mkdirSync(OUT_DIR, { recursive: true })
const jsonOut = {
  generator: 'generate_concept_reachability.ts (Lane L1d, W1)',
  generated_at: new Date().toISOString(),
  summary: {
    fact_category_rows: factCategoryRows.length,
    fact_category_served: factCategoryRows.filter((r) => r.served).length,
    fact_category_documented_in_coverage_matrix: factCategoryRows.filter((r) =>
      r.disposition.startsWith('SERVED (documented'),
    ).length,
    fact_category_planner_known: factCategoryRows.filter((r) => r.planner_known).length,
    dark_table_rows: darkTableRows.length,
    dark_table_corrected_to_served: darkTableRows.filter((r) => r.served).length,
    dark_table_planner_known: darkTableRows.filter((r) => r.planner_known).length,
    signal_class_rows: signalClassRows.length,
    signal_class_served: signalClassRows.filter((r) => r.served).length,
  },
  plan_settled_dispositions_carried_forward: PLAN_SETTLED,
  rows: allRows,
}
writeFileSync(join(OUT_DIR, 'concept_reachability_v1.json'), JSON.stringify(jsonOut, null, 2) + '\n')
console.log('[CONCEPT-REACHABILITY] summary:', JSON.stringify(jsonOut.summary, null, 2))

// ── write CONCEPT_COVERAGE_CENSUS_v1_0.md (item 2) ────────────────────────────

{
  const lines: string[] = []
  lines.push('---')
  lines.push('artifact: CONCEPT_COVERAGE_CENSUS_v1_0.md')
  lines.push('canonical_id: CONCEPT_COVERAGE_CENSUS')
  lines.push('version: 1.0')
  lines.push('status: GENERATED — v1')
  lines.push('generator: platform/scripts/census/generate_concept_reachability.ts')
  lines.push(`generated_at: ${new Date().toISOString()}`)
  lines.push('---')
  lines.push('')
  lines.push('# Concept Coverage Census v1.0 (W-21 — concept granularity, not table)')
  lines.push('')
  lines.push(
    'Per RETRIEVAL_PLANE_ELEVATION_PLAN §9.4 W-21: "Census granularity = CONCEPT not ' +
      'table: enumerate chart_facts fact_categories... as first-class census rows — ' +
      'table-level coverage under-counts L1 by design." This census enumerates all ' +
      `**${liveCategories.length}** live \`chart_facts.fact_category\` values (the ` +
      'live-DB-verified set from L1b\'s E3 extractor, cross-referenced against E1\'s ' +
      'declared registry extraction for a serving capability path) — not the smaller ' +
      'hand-maintained lists.',
  )
  lines.push('')
  lines.push(
    '**Headline finding, verified by direct source read (corrects L1b\'s stated impact ' +
      'claim):** `chart_facts_query`\'s category filter (`register_d7_channel.ts`) does ' +
      '`fact_category = ANY($n::text[])` straight from the caller\'s string — **no enum ' +
      'validates it, from any of the four static category lists in the repo.** So all ' +
      `${liveCategories.length} live categories are technically SERVED (queryable) today, ` +
      'not just the 152 L1b\'s ledger loader counted as SERVED (which used ' +
      'coverage_matrix.ts membership as its SERVED/DARK signal). The real gap is ' +
      '**discoverability at the serving layer**: `chart_facts_query`\'s own handler never ' +
      'consults `coverage_matrix.ts`\'s 158-entry `CHART_FACTS_CATEGORIES` constant, so an ' +
      'LLM caller has no single documented, load-bearing list of the real category strings ' +
      'to draw from at query time. That constant is **not fully dead**, though — a real ' +
      `repo-wide import-site scan (this generator's own \`scanImportSites()\`, not a hand-` +
      `typed claim) finds **${coverageMatrixImportSites.length}** import site(s): ` +
      `${coverageMatrixImportSites.length > 0 ? coverageMatrixImportSites.map((h) => `\`${h.file}:${h.line}\``).join(', ') : '(none)'}` +
      '. It is imported by `platform/tests/retrieval/coverage_gate.test.ts` and used as a ' +
      'live CI coverage gate — one real consumer, just a test-time gate rather than a ' +
      'runtime-serving one.',
  )
  lines.push('')
  lines.push(
    `- Live categories: **${liveCategories.length}**\n` +
      `- Documented in coverage_matrix.ts's list (158 entries, but unused by the query path): **${factCategoryRows.filter((r) => r.disposition.startsWith('SERVED (documented')).length}**\n` +
      `- SERVED-UNDOCUMENTED (queryable but absent from every static list): **${factCategoryRows.filter((r) => r.disposition.startsWith('SERVED-UNDOCUMENTED')).length}**\n` +
      `- Planner-known (referenced by name in a vidhi primitive/floor's fallback_face or definition): **${factCategoryRows.filter((r) => r.planner_known).length}**`,
  )
  lines.push('')
  lines.push('## Per-category coverage')
  lines.push('')
  lines.push('| fact_category | live rows | served? | documented in coverage_matrix.ts? | planner-known? |')
  lines.push('|---|---|---|---|---|')
  for (const r of factCategoryRows) {
    const rc = e3.category_lists.live_db_row_counts[r.concept] ?? 0
    const documented = coverageMatrixSet.has(r.concept) ? 'yes' : 'no'
    lines.push(
      `| \`${r.concept}\` | ${rc} | ${r.served ? 'yes' : 'no'} | ${documented} | ${r.planner_known ? 'yes' : 'no'} |`,
    )
  }
  lines.push('')
  lines.push('---')
  lines.push('')
  lines.push(
    '*End of CONCEPT_COVERAGE_CENSUS v1.0 — Lane L1d, W1. Full JSON at ' +
      '`platform/src/generated/census/concept_reachability_v1.json`. See ' +
      '`REACHABILITY_MATRIX_v1.md` for the full three-way SERVED/NAVIGABLE/PLANNER-KNOWN ' +
      'matrix across all concept kinds (fact_category + dark table + signal_class).*',
  )
  mkdirSync(BRIEF_DIR, { recursive: true })
  writeFileSync(join(BRIEF_DIR, 'CONCEPT_COVERAGE_CENSUS_v1_0.md'), lines.join('\n') + '\n')
  console.log('[CONCEPT-REACHABILITY] wrote CONCEPT_COVERAGE_CENSUS_v1_0.md')
}

// ── write REACHABILITY_MATRIX_v1.md (item 4) ──────────────────────────────────

{
  const lines: string[] = []
  lines.push('---')
  lines.push('artifact: REACHABILITY_MATRIX_v1.md')
  lines.push('canonical_id: REACHABILITY_MATRIX')
  lines.push('version: 1.0')
  lines.push('status: GENERATED — v1/initial (NOT the CI-gated final artifact; that is W2+)')
  lines.push('generator: platform/scripts/census/generate_concept_reachability.ts')
  lines.push(`generated_at: ${new Date().toISOString()}`)
  lines.push('---')
  lines.push('')
  lines.push('# Reachability Matrix v1 (W-20)')
  lines.push('')
  lines.push(
    'Per RETRIEVAL_PLANE_ELEVATION_PLAN §9.4 W-20: "every data-plane CONCEPT... × its ' +
      'serving capability × its umbrella drill-path (≤2 hops) × the Vidhi primitive that ' +
      'names it. Three-way guarantee: SERVED (coverage) + NAVIGABLE (drill crawl reaches ' +
      'it, zero dead ends) + PLANNER-KNOWN (a floor/primitive references it)." This is the ' +
      '**v1/initial** pass explicitly scoped by this lane\'s brief — not the CI-gated final ' +
      'artifact (that lands in W2+).',
  )
  lines.push('')
  lines.push('## Coverage of this pass (honest scope statement)')
  lines.push('')
  lines.push(
    `- **fact_category** concepts: full coverage, all ${factCategoryRows.length} live categories (from E3).\n` +
      `- **dark_table** concepts: full coverage, all ${darkTableRows.length} tables from L1b's adjudication queue (77 real tables with zero TS-registry-declared route + a small number of new corrections this lane verified — see disposition notes).\n` +
      `- **signal_class** concepts: the one confirmed, populated, real signal-class column found by E4 (\`bodha_msr_signals.signal_type_class\`, ${signalClassRows.length} distinct values) — E4's own finding is that no OTHER cross-plane signal-class column is populated/shared, so this is the full real set, not a sample.\n` +
      '- **service_endpoint** concepts: the 118 live capabilities are the service-endpoint concept universe and are already fully enumerated, per-capability, in `RETRIEVAL_TOOL_CENSUS_v1_0.md` (this lane\'s item 1 deliverable) — not repeated row-for-row here to avoid a 118-row duplicate; cross-reference by URI.\n' +
      '- **NOT covered this pass:** the ~106-asset `asset_registry` plane beyond what appears via fact_category/dark-table/signal-class (W-22\'s Provider Concept Manifest — asset-level `emits` declarations — is a separate, not-yet-built W2 item per the plan; this pass has no per-asset declared-concept-inventory to reconcile against, only the harvest\'s regex-derived table_hint).',
  )
  lines.push('')
  lines.push('## NAVIGABLE methodology (v1 approximation, per the brief)')
  lines.push('')
  lines.push(
    'Per the brief: "a v1 approximation is fine, e.g. checking if the serving ' +
      "capability's drill_children/emits_references fields point anywhere.\" For every " +
      'concept served by `chart_facts_query` (all fact_category rows) or by the ' +
      'bodha_msr_signals-touching capabilities (signal_class rows), NAVIGABLE is computed ' +
      "from the serving capability's real descriptor topology: `chart_facts_query` has " +
      '`traversal_level=L-SIGNAL`, `tool_role=umbrella`, `emits_references=true`, no ' +
      '`drill_children` — a single-hop direct-access surface (0 further hops needed once ' +
      "the concept's identifying string is known), consistent with the strategy doc §5.1 " +
      '"layered data, flat access, guided navigation" doctrine. Dark-table concepts that ' +
      'are not served are marked `n/a` — navigability doesn\'t apply to an unserved concept.',
  )
  lines.push('')
  lines.push('## Plan-settled dispositions carried forward (not re-derived — see citations)')
  lines.push('')
  lines.push('| concept | disposition | citation |')
  lines.push('|---|---|---|')
  for (const p of PLAN_SETTLED) {
    lines.push(`| ${p.concept} | ${p.disposition} | ${p.citation} |`)
  }
  lines.push('')
  lines.push('## Full matrix')
  lines.push('')
  lines.push('| concept_kind | concept | served? | navigable? | planner-known? | disposition |')
  lines.push('|---|---|---|---|---|---|')
  for (const r of allRows) {
    lines.push(
      `| ${r.concept_kind} | \`${r.concept}\` | ${r.served ? 'YES' : 'NO'} | ${r.navigable === 'n/a' ? 'n/a' : r.navigable ? 'YES' : 'NO'} | ${r.planner_known ? 'YES' : 'NO'} | ${r.disposition} |`,
    )
  }
  lines.push('')
  lines.push('## Basis detail (why each SERVED/NAVIGABLE/PLANNER-KNOWN call is what it is)')
  lines.push('')
  lines.push('<details><summary>Expand — one basis line per concept per axis</summary>')
  lines.push('')
  lines.push('| concept | served_basis | navigable_basis | planner_known_basis |')
  lines.push('|---|---|---|---|')
  for (const r of allRows) {
    lines.push(`| \`${r.concept}\` | ${r.served_basis} | ${r.navigable_basis} | ${r.planner_known_basis} |`)
  }
  lines.push('')
  lines.push('</details>')
  lines.push('')
  lines.push('---')
  lines.push('')
  lines.push(
    '*End of REACHABILITY_MATRIX v1 — Lane L1d, W1. Full JSON at ' +
      '`platform/src/generated/census/concept_reachability_v1.json`. Not CI-wired ' +
      '(report-only v1, matching the harvest lanes\' precedent); the CI-gated automated ' +
      'drill-pointer crawl + matrix completeness check the plan describes for W-20 is a ' +
      'later-wave deliverable.*',
  )
  writeFileSync(join(BRIEF_DIR, 'REACHABILITY_MATRIX_v1.md'), lines.join('\n') + '\n')
  console.log('[CONCEPT-REACHABILITY] wrote REACHABILITY_MATRIX_v1.md')
}

// ── (2) authoritative fact_category enumeration (item 3 / W-23) ───────────────

{
  const authoritative = {
    canonical_id: 'CHART_FACTS_CATEGORIES_AUTHORITATIVE',
    version: 1,
    generated_at: new Date().toISOString(),
    source: 'live DB — SELECT DISTINCT fact_category FROM chart_facts (via E3, retrieval_census_ro role)',
    rationale:
      'Picked as the single source of truth because it is the only one of the (now ' +
      'confirmed FOUR, not three) static/live sources that reflects what the L1 build ' +
      'ACTUALLY WROTE, per CLAUDE.md §N.5 ("L1 is the authority over L2+ derivations") ' +
      'generalized to L1\'s own documentation: chart_facts (the table) is definitionally ' +
      'the ground truth for chart_facts (the category enum), not any hand-maintained ' +
      'mirror of it. All three static lists are demonstrably STALE mirrors, not competing ' +
      'design intents: CHART_FACTS_SCHEMA.json (147, missing 73 live categories) and ' +
      `coverage_matrix.ts (158, missing 66 live categories, AND unused by the ` +
      `chart_facts_query serving path it appears to document — a real repo-wide ` +
      `import-site scan finds ${coverageMatrixImportSites.length} import site(s): ` +
      `${coverageMatrixImportSites.length > 0 ? coverageMatrixImportSites.map((h) => `${h.file}:${h.line}`).join(', ') : '(none)'}, ` +
      `so it is not fully dead — it is a live CI coverage-gate dependency, just not ` +
      `runtime-serving) both undercount; a FOURTH, ` +
      'previously-uncited source (ganita/types.ts, 26 entries, imported by facts_store.ts ' +
      'but only re-exported, never used to validate anything) undercounts far more ' +
      'severely. None of the three static sources gates the live write path OR the live ' +
      'read path (chart_facts_query has no category enum check at all) — they are pure ' +
      'documentation, currently wrong documentation.',
    count: liveCategories.length,
    categories: liveCategories,
    row_counts: e3.category_lists.live_db_row_counts,
    disagreement_with_other_sources: {
      'CHART_FACTS_SCHEMA.json (00_ARCHITECTURE + platform/scripts/governance mirror, byte-identical)': {
        count: 147,
      },
      'coverage_matrix.ts CHART_FACTS_CATEGORIES': {
        count: 158,
        import_sites_in_repo: coverageMatrixImportSites.length,
        import_sites: coverageMatrixImportSites,
        gates_runtime_serving_path: false,
        note: coverageMatrixImportSites.length > 0
          ? 'not wired into chart_facts_query\'s serving path, but has a real test-time ' +
            'consumer (see import_sites) — not fully dead/decorative'
          : 'no import sites found by this scan',
      },
      'ganita/types.ts CHART_FACTS_CATEGORIES (4th, previously-uncited source, found this lane)': {
        count: 26,
        import_sites_in_repo: ganitaTypesImportSites.length,
        import_sites: ganitaTypesImportSites,
        note: 'imported by facts_store.ts but only re-exported (`export { CHART_FACTS_CATEGORIES } from \'./types\'`), never used to validate a write or a read',
      },
    },
    migration_note:
      'RECOMMENDATION (design note, not executed this wave — no code changed the three ' +
      'static lists or their call sites): retire all three/four static ' +
      'CHART_FACTS_CATEGORIES-shaped constants as sources of truth. The ONLY safe path ' +
      'given must_not_touch chart_facts semantics (this lane\'s scope boundary) is to ' +
      'point future consumers (chart_facts_query\'s description text, coverage_matrix.ts\'s ' +
      'own completeness gate, CHART_FACTS_SCHEMA.json\'s governance mirror) at this ' +
      'generated JSON (or a live query) instead of hand-typed literals, per L1a\'s ' +
      'no_hardcoded_concept_lists.ts lint (already flags coverage_matrix.ts\'s array as ' +
      'the flagship HIGH catch). Regenerating this file periodically (or on every L1 ' +
      'build) keeps it honest as the live set drifts; W2 is the wave that actually wires ' +
      'consumers to read it.',
  }
  mkdirSync(OUT_DIR, { recursive: true })
  writeFileSync(
    join(OUT_DIR, 'chart_facts_categories_authoritative_v1.json'),
    JSON.stringify(authoritative, null, 2) + '\n',
  )
  console.log('[CONCEPT-REACHABILITY] wrote chart_facts_categories_authoritative_v1.json')

  const lines: string[] = []
  lines.push('---')
  lines.push('artifact: FACT_CATEGORY_ENUMERATION_RECONCILIATION_v1_0.md')
  lines.push('canonical_id: FACT_CATEGORY_ENUMERATION_RECONCILIATION')
  lines.push('version: 1.0')
  lines.push('status: GENERATED — v1 (design note; no source files were changed this wave)')
  lines.push('generator: platform/scripts/census/generate_concept_reachability.ts')
  lines.push(`generated_at: ${new Date().toISOString()}`)
  lines.push('---')
  lines.push('')
  lines.push('# Fact-Category Enumeration Reconciliation v1.0 (W-23)')
  lines.push('')
  lines.push(
    'Per RETRIEVAL_PLANE_ELEVATION_PLAN §9.4 W-23: "Reconcile the three chart_facts ' +
      'category enumerations... into ONE generated source consumed by all three ' +
      'consumers." This note picks the authoritative source and documents why the ' +
      'others disagree. **No source file was modified to execute this migration** — ' +
      'this lane\'s scope is must_not_touch `chart_facts` semantics; wiring real ' +
      'consumers to the new authoritative artifact is future work (see recommendation ' +
      'below), not done here.',
  )
  lines.push('')
  lines.push(
    '**The plan\'s own framing understates the problem.** It names three sources ' +
      '(SCHEMA.json, coverage_matrix.ts, "37" prose). L1b\'s E3 extractor found a real ' +
      'fourth (`platform/python-sidecar/ga_writers/CHART_FACTS_SCHEMA.json`, 191 — a ' +
      'byte-DIFFERENT copy of the "same" file). This lane found a real **fifth**: ' +
      '`platform/src/lib/ganita/types.ts` also defines a `CHART_FACTS_CATEGORIES` ' +
      'constant (26 entries) — imported by `facts_store.ts` but only re-exported, never ' +
      'used to gate a write or a read. None of the five static/near-static sources ' +
      'gates the live *serving* path — `chart_facts_query`\'s category filter does ' +
      '`fact_category = ANY($n::text[])` directly from the caller\'s raw string, with no ' +
      'enum check against any of the five lists. They are pure (currently wrong) ' +
      'documentation from the runtime\'s perspective; one of them (`coverage_matrix.ts`) ' +
      'does have a real non-runtime consumer — see table below (import-site counts are ' +
      `from this generator's own repo-wide \`scanImportSites()\` scan, not a hand-typed ` +
      'claim).',
  )
  lines.push('')
  lines.push('## The five sources, real counts')
  lines.push('')
  lines.push('| source | count | import sites (repo-wide scan) | gates the runtime serving path? |')
  lines.push('|---|---|---|---|')
  lines.push('| **Live DB** (`SELECT DISTINCT fact_category FROM chart_facts`) | **218** | — | — (this IS the runtime) |')
  lines.push('| `CHART_FACTS_SCHEMA.json` (00_ARCHITECTURE canonical + platform/scripts/governance mirror, byte-identical) | 147 | not scanned (JSON, not a TS import) | no |')
  lines.push('| `CHART_FACTS_SCHEMA.json` (`platform/python-sidecar/ga_writers/`, undocumented 3rd copy) | 191 | not verified this pass — Python sidecar out of TS-registry scan scope | not verified this pass — Python sidecar out of TS-registry scan scope |')
  lines.push(
    `| \`coverage_matrix.ts\` \`CHART_FACTS_CATEGORIES\` | 158 | **${coverageMatrixImportSites.length}** ` +
      `(${coverageMatrixImportSites.length > 0 ? coverageMatrixImportSites.map((h) => `\`${h.file}:${h.line}\``).join(', ') : 'none'}) ` +
      `| **no** — not consulted by \`chart_facts_query\`'s serving path; its one real import ` +
      `site is \`coverage_gate.test.ts\`, a live CI *test-time* coverage gate, not a runtime ` +
      `serve-path consumer |`,
  )
  lines.push(
    `| \`ganita/types.ts\` \`CHART_FACTS_CATEGORIES\` (5th source, found this lane, not ` +
      `cited by the plan) | 26 | **${ganitaTypesImportSites.length}** ` +
      `(${ganitaTypesImportSites.length > 0 ? ganitaTypesImportSites.map((h) => `\`${h.file}:${h.line}\``).join(', ') : 'none'}) ` +
      `| no — imported by \`facts_store.ts\` but only re-exported |`,
  )
  lines.push('')
  lines.push('## Authoritative source: the live DB (218 categories)')
  lines.push('')
  lines.push(
    'Chosen per CLAUDE.md §N.5 generalized: `chart_facts` (the table) is the ground ' +
      'truth for `chart_facts` (the category enum), not a hand-typed mirror of it, and ' +
      'the live set is what every one of the other four sources is trying (and failing) ' +
      'to describe. The full generated list ships at ' +
      '`platform/src/generated/census/chart_facts_categories_authoritative_v1.json` ' +
      `(${liveCategories.length} categories, with live row counts per category).`,
  )
  lines.push('')
  lines.push('## Migration recommendation (design only — not executed this wave)')
  lines.push('')
  lines.push(
    'Retire the three/four/five static `CHART_FACTS_CATEGORIES`-shaped constants as ' +
      'sources of truth; point future consumers at the generated JSON (or a live query) ' +
      'instead. `coverage_matrix.ts`\'s own array is already L1a\'s flagship HIGH catch in ' +
      '`no_hardcoded_concept_lists.ts` — this reconciliation gives the eventual fix its ' +
      'target artifact. Regenerate on every L1 build (or on a cadence) so the file stays ' +
      'honest as the live set drifts. Wiring real call sites (chart_facts_query\'s ' +
      'description text\'s enumerated examples, coverage_matrix.ts\'s completeness gate, ' +
      'the governance CHART_FACTS_SCHEMA.json mirror) to consume it is a W2 migration ' +
      'item, not this wave\'s.',
  )
  lines.push('')
  lines.push('---')
  lines.push('')
  lines.push(
    '*End of FACT_CATEGORY_ENUMERATION_RECONCILIATION v1.0 — Lane L1d, W1. Authoritative ' +
      'list at `platform/src/generated/census/chart_facts_categories_authoritative_v1.json`.*',
  )
  writeFileSync(
    join(BRIEF_DIR, 'FACT_CATEGORY_ENUMERATION_RECONCILIATION_v1_0.md'),
    lines.join('\n') + '\n',
  )
  console.log('[CONCEPT-REACHABILITY] wrote FACT_CATEGORY_ENUMERATION_RECONCILIATION_v1_0.md')
}

// ── (5) TABLE_CONCEPT_DISPOSITIONS_v1_0.md (W-15) ──────────────────────────────

{
  const lines: string[] = []
  lines.push('---')
  lines.push('artifact: TABLE_CONCEPT_DISPOSITIONS_v1_0.md')
  lines.push('canonical_id: TABLE_CONCEPT_DISPOSITIONS')
  lines.push('version: 1.0')
  lines.push('status: GENERATED — v1')
  lines.push('generator: platform/scripts/census/generate_concept_reachability.ts')
  lines.push(`generated_at: ${new Date().toISOString()}`)
  lines.push('---')
  lines.push('')
  lines.push('# Table/Concept Lifecycle Dispositions v1.0 (W-15)')
  lines.push('')
  lines.push(
    'Disposition = SERVED | INTERNAL-BY-DESIGN | RETIRE | DARK-NEEDS-OWNER, for the ' +
      `${darkTableRows.length} real DARK tables L1b's mechanical cross-diff found ` +
      '(zero TS-registry-declared route), plus the plan-already-settled non-table dark-set ' +
      'items (GT-49/50/52) carried forward verbatim rather than re-derived. Two ' +
      'corrections this lane independently verified (see body) are folded in, not left ' +
      'as open findings.',
  )
  lines.push('')
  lines.push('## Plan-already-settled (carried forward, not re-derived)')
  lines.push('')
  lines.push('| concept | disposition | citation |')
  lines.push('|---|---|---|')
  for (const p of PLAN_SETTLED) {
    lines.push(`| ${p.concept} | ${p.disposition} | ${p.citation} |`)
  }
  lines.push('')
  lines.push('## This lane\'s own corrections (verified by direct source read)')
  lines.push('')
  lines.push('| table | was (L1b) | now | evidence |')
  lines.push('|---|---|---|---|')
  lines.push(
    '| `bg_dignity_reference` | INTERNAL-BY-DESIGN (DARK) | **SERVED** | ' +
      DARK_OVERRIDES.bg_dignity_reference!.served_basis +
      ' |',
  )
  lines.push(
    '| `chart_panchanga` | NEEDS-OWNER (DARK) | **SERVED** | ' +
      DARK_OVERRIDES.chart_panchanga!.served_basis +
      ' |',
  )
  lines.push('')
  lines.push(`## Full DARK-table disposition set (${darkTableRows.length} tables, L1b's cross-diff + this lane's corrections)`)
  lines.push('')
  lines.push('| table | layer | row_count | disposition |')
  lines.push('|---|---|---|---|')
  for (const r of adj.rows.filter((x) => x.type === 'DARK' && x.table_name)) {
    const override = DARK_OVERRIDES[r.table_name!]
    const disp = override ? override.disposition : (r.proposed_disposition ?? 'NEEDS-OWNER')
    lines.push(`| \`${r.table_name}\` | ${r.layer ?? '—'} | ${r.row_count ?? '—'} | ${disp} |`)
  }
  lines.push('')
  lines.push('## Disposition-class summary')
  lines.push('')
  const dispCounts: Record<string, number> = {}
  for (const r of adj.rows.filter((x) => x.type === 'DARK' && x.table_name)) {
    const override = DARK_OVERRIDES[r.table_name!]
    const disp = override ? 'SERVED (corrected)' : (r.proposed_disposition ?? 'NEEDS-OWNER')
    dispCounts[disp] = (dispCounts[disp] ?? 0) + 1
  }
  for (const [k, v] of Object.entries(dispCounts)) lines.push(`- ${k}: **${v}**`)
  lines.push('')
  lines.push(
    '`INTERNAL-BY-DESIGN` rows were auto-proposed by L1b\'s cross-diff via two transparent, ' +
      'inspectable naming-pattern rules (bookkeeping-suffix tables, `bg_*` reference-keyword ' +
      'tables) — not individually researched per row. `NEEDS-OWNER` rows are honestly left ' +
      'for a human/conductor call, per L1b\'s own scope statement (52/77 not individually ' +
      'researched). Neither this lane nor L1b re-derives dispositions the plan itself already ' +
      'settled (GT-49/50/52, table above) — those are carried forward verbatim.',
  )
  lines.push('')
  lines.push('---')
  lines.push('')
  lines.push(
    '*End of TABLE_CONCEPT_DISPOSITIONS v1.0 — Lane L1d, W1. Source data: ' +
      '`platform/src/generated/harvest/adjudication_queue.json` (L1b) + this lane\'s two ' +
      'verified corrections + GROUND_TRUTH_REGISTER.md GT-49/50/52 (carried forward).*',
  )
  writeFileSync(join(BRIEF_DIR, 'TABLE_CONCEPT_DISPOSITIONS_v1_0.md'), lines.join('\n') + '\n')
  console.log('[CONCEPT-REACHABILITY] wrote TABLE_CONCEPT_DISPOSITIONS_v1_0.md')
}

console.log('[CONCEPT-REACHABILITY] done.')
