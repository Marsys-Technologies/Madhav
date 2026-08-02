#!/usr/bin/env tsx
/**
 * authority_basis_census_seed.ts — ṢAḌ-DARŚANA item 5 (item 44 census) · W0 seed → W2 REAL
 * numbers (w2-envelope-real-snapshot lane, 2026-08-02).
 *
 * DESIGN AUTHORITY: KALA_SUPREME_ELEVATION_v1_0.md §2 Consequence 1 + item 44 (§14): "every
 * served temporal claim carries `authority_basis` naming the field window-id it inherits,
 * and a CI authority-basis census enumerates every temporal-claim-bearing serving path and
 * asserts (a) each carries `authority_basis`, and (b) no path computes a window of its
 * own... HARD-gated at W6." Item 44's W2 contract is REPORTED-not-gated: this script always
 * exits 0 on an honest scoreboard; only a broken enumeration mechanism fails it.
 *
 * WHAT CHANGED AT W2 (the seed's own header had gone stale):
 *   - The seed claimed "authority_basis does not exist ANYWHERE in this codebase yet."
 *     That is no longer true: elect.ts, ahead.ts, ritual.ts (+ kala_ritual_resonance.ts),
 *     upaya.ts (+ kala_upaya_diagnosis.ts) and kala_sky_pattern.ts all emit
 *     LOCALLY-CONSTRUCTED bases (e.g. `${factor_family}/${factor_key}@${start_utc}`,
 *     `pact_query:${status}`) — provenance tags naming the substrate atom a claim
 *     inherits, NOT field window-ids (`kfw_…`), which still do not exist as served data
 *     (`kala_field_windows` is written by ka_kshetra; production is empty until the first
 *     field build).
 *   - The scoreboard now CLASSIFIES each enumerated path's basis kind machine-readably:
 *       `field_window_id`     — a basis naming a real field window id (kfw_…). Detector:
 *                               line-level co-occurrence of `authority_basis` and `kfw_`
 *                               in the path's source (+ its one-hop relative lib imports).
 *                               HONESTLY 0 today — that 0 is the point of the scoreboard:
 *                               it flips upward only when serving paths actually inherit
 *                               field windows, and the Conductor tracks the number.
 *       `locally_constructed` — emits `authority_basis` but the basis is composed locally
 *                               from substrate row fields / provenance tags.
 *       `absent`              — no `authority_basis` emission at all.
 *   - `paths_computing_own_window: 'not_yet_assessed'` (a single global placeholder that
 *     read as coverage) is REPLACED by an explicit PER-PATH assessment: the eight kala_*
 *     view facades were hand-audited this lane (2026-08-02) and carry a grounded
 *     assessment + reason; every other enumerated path carries an explicit per-path
 *     `not_assessed` with an honest reason — never a global placeholder.
 *   - Enumeration bug fixed: `server.tool(TOOL_NAME, …)` registrations (now/ahead/
 *     priority/explain use a const identifier, not a string literal) were invisible to the
 *     seed's regex; the census now resolves single-identifier registrations against the
 *     same file's `const <IDENT> = '<name>'` declaration.
 *
 * SCOREBOARD FORM (stable, parseable — the Conductor records it at gate time):
 *   - stdout: the usual single-JSON gate report; the `authbasis-census-scoreboard`
 *     result's `detail` field IS the scoreboard JSON string (JSON.parse-able).
 *   - stderr: one `AUTHORITY_BASIS_SCOREBOARD_JSON=<json>` line (single line, greppable).
 *
 * CI compatibility (.github/workflows/shad-darshana-ci-skeletons.yml — owned by a sibling
 * lane, not edited here): invoked as
 *   npx tsx scripts/census/shad_darshana_gates/authority_basis_census_seed.ts  (cwd platform/)
 * and mutation-verified by repointing MCP_TOOLS_ROOT (declared below, this file's own copy)
 * at a nonexistent dir → the non-vacuous check FAILs → exit 1; restoring → exit 0. Both
 * properties are preserved.
 */
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs'
import path from 'node:path'
import { printGateReport, type GateResult } from './_report'

const REPO_ROOT = path.join(__dirname, '..', '..', '..', '..')
const MCP_TOOLS_ROOT = path.join(REPO_ROOT, 'platform-mcp/src/tools')
const REGISTRY_LAYERS_ROOT = path.join(REPO_ROOT, 'platform/src/lib/retrieval/registry/layers')

/**
 * Naive candidate-name pattern for "temporal-claim-bearing serving path": any registered
 * tool whose name suggests it serves a time window, forecast, dasha timing, transit
 * window, prospective/standing prediction, or muhurta/election timing. DELIBERATELY
 * OVER-INCLUSIVE (a false positive just means a path gets tracked and later confirmed
 * non-temporal — cheap); the item-44 census grows over the campaign.
 */
const TEMPORAL_NAME_PATTERN = /(kala_|gochara_|dasha|dosha_timing|window|forecast|predictive_anchor|prospective|standing_predictions|muhurta|praveśa|praveśa|sandhi)/i

function walkTs(dir: string, out: string[]): void {
  let entries: string[]
  try {
    entries = readdirSync(dir)
  } catch {
    return
  }
  for (const entry of entries) {
    if (entry === 'node_modules' || entry === '.git') continue
    const full = path.join(dir, entry)
    let st
    try {
      st = statSync(full)
    } catch {
      continue
    }
    if (st.isDirectory()) walkTs(full, out)
    else if (entry.endsWith('.ts') && !entry.endsWith('.test.ts')) out.push(full)
  }
}

export type BasisKind = 'field_window_id' | 'locally_constructed' | 'absent'

export type OwnWindowAssessment =
  | 'inherits_substrate_window'
  | 'no_window_emission'
  | 'not_assessed'

export interface AuthorityBasisCandidate {
  name: string
  source_file: string
  carries_authority_basis: boolean
  basis_kind: BasisKind
  own_window: { assessment: OwnWindowAssessment; reason: string }
}

/**
 * Explicit per-path clause-(b) assessment ("no path computes a window of its own").
 * Hand-audited by the w2-envelope-real-snapshot lane, 2026-08-02, against the actual
 * emission sites (elect.ts:~500, ahead.ts:~1783, ritual.ts:~609 via
 * kala_ritual_resonance.ts, upaya.ts:~339 via kala_upaya_diagnosis.ts:~297,
 * kala_sky_pattern.ts:~908). Paths NOT in this map get an explicit per-path
 * `not_assessed` — an honest gap named per path, not a global placeholder.
 */
const OWN_WINDOW_ASSESSMENTS: Record<string, { assessment: OwnWindowAssessment; reason: string }> = {
  kala_elect_get: {
    assessment: 'inherits_substrate_window',
    reason:
      'Candidate windows + authority_basis atoms come from bg_muhurta_lattice substrate rows; the basis ' +
      '`${factor_family}/${factor_key}@${start_utc}` NAMES the inherited atom. No boundary invented at serve time.',
  },
  kala_ritual_get: {
    assessment: 'inherits_substrate_window',
    reason:
      'Same one-engine lattice substrate as ELECT (kala_ritual_resonance passthrough of factor-row spans); ' +
      'basis names the inherited lattice atom.',
  },
  kala_ahead_get: {
    assessment: 'inherits_substrate_window',
    reason:
      'Forward windows come from L3 substrate sweep rows (kala_bhavishya / lattice factors / panchanga-service ' +
      'ranges); its authority_basis names inherited lattice atoms. The query horizon (date_from/date_to) bounds ' +
      'the SEARCH, not a served claim window.',
  },
  kala_now_get: {
    assessment: 'inherits_substrate_window',
    reason:
      'Serves window families read from L3 registry capabilities (kala_activation/kala_darshana etc.) and ' +
      'panchanga-service rows; boundaries are substrate values, not serve-time computation. Emits no authority_basis yet.',
  },
  kala_story_get: {
    assessment: 'inherits_substrate_window',
    reason:
      'Chapter spans are ka_jivana_parva substrate rows (start_year/end_year), deduped but never re-derived. ' +
      'Emits no authority_basis yet.',
  },
  kala_priority_get: {
    assessment: 'inherits_substrate_window',
    reason:
      'Wraps the ka_tulana priority-ranking capability; any window content is the substrate\'s. Emits no ' +
      'authority_basis yet.',
  },
  kala_explain_get: {
    assessment: 'inherits_substrate_window',
    reason:
      'Explains an as-of state from substrate reads; serves no window of its own construction. Emits no ' +
      'authority_basis yet.',
  },
  kala_upaya_get: {
    assessment: 'no_window_emission',
    reason:
      'Its authority_basis is a pact-chain provenance tag (`pact_query:<status>`, kala_upaya_diagnosis.ts), not a ' +
      'temporal window claim; the facade serves intervention rows, no window bounds of its own.',
  },
}

const NOT_ASSESSED_REASON =
  'Not hand-audited by the 2026-08-02 per-path assessment (which covered the eight kala_* view facades). ' +
  'Explicit per-path honest gap — assess when this path is next touched, or when clause-(b) automation lands (pre-W6).'

/** One-hop relative-import resolution: returns the concatenated source text of `file`
 *  plus every `./`/`../` module it imports (as `.ts`, if it exists). Basis strings are
 *  often composed in a lib the facade imports (kala_upaya_diagnosis.ts, kala_sky_pattern
 *  .ts, kala_ritual_resonance.ts) — classifying on the file alone would under-count. */
function sourceWithOneHopImports(file: string): string {
  const src = readFileSync(file, 'utf-8')
  const chunks = [src]
  for (const m of src.matchAll(/from\s+['"](\.{1,2}\/[^'"]+)['"]/g)) {
    const spec = m[1]!
    const resolved = path.resolve(path.dirname(file), spec.replace(/\.js$/, '.ts'))
    const tryPaths = resolved.endsWith('.ts') ? [resolved] : [`${resolved}.ts`, path.join(resolved, 'index.ts')]
    for (const p of tryPaths) {
      if (existsSync(p)) {
        try {
          chunks.push(readFileSync(p, 'utf-8'))
        } catch {
          /* unreadable import — skip, the file-local text still classifies */
        }
        break
      }
    }
  }
  return chunks.join('\n')
}

/** Strips block + line comments so a docstring MENTIONING `authority_basis` (e.g.
 *  kala_envelope.ts's own "NOT implemented here" disclaimer, a one-hop import of every
 *  kala facade) cannot false-positive as an emission. Heuristic: does not tokenize
 *  strings, so a `//` inside a string literal loses that line's tail — acceptable for a
 *  presence detector (verified against the known emission sites, all of which survive). */
export function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '')
}

/** Classifies the basis kind for a path from its comment-stripped source + one-hop
 *  imports. `field_window_id` detector: a LINE mentioning both `authority_basis` and
 *  `kfw_` (the field-window id prefix, KALA_W2_FIELD_DESIGN_v1_0.md §7.4 family) —
 *  line-level co-occurrence, so prose elsewhere in the file that merely names the
 *  kala_field_windows table does not false-positive. Honest count today: 0. */
export function classifyBasisKind(combinedSource: string): BasisKind {
  const code = stripComments(combinedSource)
  if (!/authority_basis/.test(code)) return 'absent'
  for (const line of code.split('\n')) {
    if (/authority_basis/.test(line) && /kfw_/.test(line)) return 'field_window_id'
  }
  return 'locally_constructed'
}

/** Statically enumerates candidate temporal-claim-bearing tool registrations:
 *  `server.tool('name', …)` string literals, `regAlias/globalAlias(server, 'name', …)`,
 *  AND `server.tool(IDENT, …)` where the same file declares `const IDENT = 'name'`
 *  (the kala_now/ahead/priority/explain registration shape the W0 seed missed). */
export function enumerateAuthorityBasisCandidates(): AuthorityBasisCandidate[] {
  const candidates: AuthorityBasisCandidate[] = []
  const seen = new Set<string>()
  if (!existsSync(MCP_TOOLS_ROOT)) return candidates
  const files: string[] = []
  walkTs(MCP_TOOLS_ROOT, files)
  for (const f of files) {
    const src = readFileSync(f, 'utf-8')
    const names = new Set<string>()
    for (const m of src.matchAll(/server\.tool\(\s*['"]([a-zA-Z0-9_]+)['"]/g)) names.add(m[1]!)
    for (const m of src.matchAll(/\b(?:regAlias|globalAlias)\(\s*server,\s*['"]([a-zA-Z0-9_]+)['"]/g)) names.add(m[1]!)
    // const-identifier registrations: server.tool(TOOL_NAME, …) + const TOOL_NAME = '…'
    for (const m of src.matchAll(/server\.tool\(\s*([A-Z][A-Z0-9_]*)\s*,/g)) {
      const ident = m[1]!
      const decl = src.match(new RegExp(`const\\s+${ident}\\s*=\\s*['"]([a-zA-Z0-9_]+)['"]`))
      if (decl) names.add(decl[1]!)
    }
    if (names.size === 0) continue
    let combined: string | null = null
    for (const name of names) {
      if (!TEMPORAL_NAME_PATTERN.test(name)) continue
      const key = `${name}@${f}`
      if (seen.has(key)) continue
      seen.add(key)
      combined ??= sourceWithOneHopImports(f)
      const basisKind = classifyBasisKind(combined)
      candidates.push({
        name,
        source_file: path.relative(REPO_ROOT, f),
        carries_authority_basis: basisKind !== 'absent',
        basis_kind: basisKind,
        own_window: OWN_WINDOW_ASSESSMENTS[name] ?? { assessment: 'not_assessed', reason: NOT_ASSESSED_REASON },
      })
    }
  }
  return candidates.sort((a, b) => a.name.localeCompare(b.name))
}

export interface AuthorityBasisScoreboard {
  measured_at: string
  paths_enumerated: number
  paths_emitting_authority_basis: number
  basis_kind_counts: Record<BasisKind, number>
  own_window_assessment_counts: Record<OwnWindowAssessment, number>
  paths: AuthorityBasisCandidate[]
}

export function buildScoreboard(candidates: AuthorityBasisCandidate[]): AuthorityBasisScoreboard {
  const basisKindCounts: Record<BasisKind, number> = { field_window_id: 0, locally_constructed: 0, absent: 0 }
  const ownWindowCounts: Record<OwnWindowAssessment, number> = {
    inherits_substrate_window: 0,
    no_window_emission: 0,
    not_assessed: 0,
  }
  for (const c of candidates) {
    basisKindCounts[c.basis_kind]++
    ownWindowCounts[c.own_window.assessment]++
  }
  return {
    measured_at: new Date().toISOString(),
    paths_enumerated: candidates.length,
    paths_emitting_authority_basis: candidates.filter((c) => c.carries_authority_basis).length,
    basis_kind_counts: basisKindCounts,
    own_window_assessment_counts: ownWindowCounts,
    paths: candidates,
  }
}

function validate(): GateResult[] {
  const results: GateResult[] = []
  const registryLayersExist = existsSync(REGISTRY_LAYERS_ROOT)
  results.push({
    id: 'authbasis-census-scope-note',
    title: 'Scan scope',
    status: 'PASS',
    detail: `Scanned platform-mcp/src/tools for temporal-name-pattern tool registrations (string-literal, regAlias/globalAlias, and const-identifier server.tool forms). platform/src/lib/retrieval/registry/layers (${registryLayersExist ? 'present' : 'MISSING'}) is a known second location for temporal capabilities (e.g. L3_kala/, L4_phala/ writers) NOT YET scanned — a real gap this census names rather than silently missing (TODO: extend enumerateAuthorityBasisCandidates to cover it too).`,
  })

  const candidates = enumerateAuthorityBasisCandidates()
  results.push({
    id: 'authbasis-census-nonvacuous',
    title: 'Enumeration mechanism is non-vacuous (finds ≥1 candidate)',
    status: candidates.length > 0 ? 'PASS' : 'FAIL',
    detail: candidates.length > 0
      ? `Found ${candidates.length} candidate temporal-claim-bearing tool(s): ${candidates.map((c) => c.name).join(', ')}`
      : 'FAIL: zero candidates found — either the temporal-name pattern is broken, or platform-mcp/src/tools is unreachable from this script (path/CWD bug), not a real "nothing is temporal" finding.',
  })

  const scoreboard = buildScoreboard(candidates)
  // Stable single-line marker on stderr for the Conductor's ledger extraction.
  console.error(`AUTHORITY_BASIS_SCOREBOARD_JSON=${JSON.stringify(scoreboard)}`)
  results.push({
    id: 'authbasis-census-scoreboard',
    title:
      'Authority-basis scoreboard (item 44) — REAL numbers, reported-not-gated until W6 per brief §3. ' +
      'field_window_id=0 is the honest current state (kala_field_windows unpopulated pre-first-field-build); ' +
      'detail is the machine-readable scoreboard JSON.',
    status: 'PASS',
    detail: JSON.stringify(scoreboard),
  })

  const dupeCheck = new Set<string>()
  const dupes: string[] = []
  for (const c of candidates) {
    if (dupeCheck.has(c.name)) dupes.push(c.name)
    dupeCheck.add(c.name)
  }
  results.push({
    id: 'authbasis-census-no-dupe-names',
    title: 'No duplicate candidate names across distinct source files (would indicate a census bookkeeping bug)',
    status: dupes.length === 0 ? 'PASS' : 'WARN',
    detail: dupes.length === 0 ? 'clean' : `duplicate names: ${[...new Set(dupes)].join(', ')}`,
  })

  return results
}

function main(): void {
  process.exit(printGateReport('authority_basis_census_seed', validate()))
}

main()
