#!/usr/bin/env tsx
/**
 * authority_basis_census_seed.ts — ṢAḌ-DARŚANA W0.6 CI skeleton, item 5
 * (SHAD_DARSHANA_BRIEF_v2_0.md §0.6.5 / §2 CI file-map / §3 W0.6: "authority-basis census
 * seed (item 44): seed of the census enumerating temporal-claim-bearing serving paths and
 * asserting authority_basis presence (real population is W2; this is the seed/skeleton)").
 *
 * DESIGN AUTHORITY: KALA_SUPREME_ELEVATION_v1_0.md §2 Consequence 1 + item 44 (§14): "every
 * served temporal claim carries `authority_basis` naming the field window-id it inherits,
 * and a CI authority-basis census enumerates every temporal-claim-bearing serving path and
 * asserts (a) each carries `authority_basis`, and (b) no path computes a window of its
 * own... census script is seeded at W0 alongside the completeness census so the inventory
 * grows with the build instead of being reconstructed at the end... HARD-gated at W6."
 *
 * WHAT THIS SEED HONESTLY IS (and is not) AT W0:
 *   - `authority_basis` does not exist ANYWHERE in this codebase yet (confirmed by source
 *     grep at authoring time — the field name appears only in `kala_envelope.ts`'s own
 *     "NOT implemented here" disclaimer comment). The real field, and the real field
 *     window-ids it names, do not exist until `ka_kshetra` (W2). So at W0 the honest
 *     scoreboard reads: paths_carrying_authority_basis = 0 for every enumerated path — that
 *     is correct, not a defect, and this script does NOT fail the build on it (item 44 is
 *     explicitly reported-not-gated at W2, HARD-gated only at W6, per brief §3 W2/W6).
 *   - What this seed DOES enforce now, with a real detector behind it (CLAUDE.md §N.7 —
 *     a check needs a real code path that could fail, or it is null): the enumeration
 *     mechanism itself is non-vacuous (finds ≥1 candidate temporal-claim-bearing tool by
 *     static source-text scan), and the `authority_basis` PRESENCE check is a genuine
 *     grep-based detector — it will correctly start reporting nonzero counts the moment a
 *     future wave's writer actually adds the literal field, and correctly reports zero now.
 *     This is a real (if simple) detector, not a decorative placeholder.
 *   - Clause (b) — "no path computes a window of its own" — is NOT automated at W0 (a
 *     reliable static detector for "this handler independently computes a temporal
 *     window" needs real per-tool semantics this seed does not have). The scoreboard
 *     carries an explicit `paths_computing_own_window: 'not_yet_assessed'` placeholder,
 *     named honestly as future work rather than silently assumed 0 — see the TODO below.
 *
 * PLAN/LIVE split does not apply (no MCP calls) — pure static source-text scan, runnable
 * anywhere, always. Exit 0 unless the enumeration mechanism itself is broken (0 candidates
 * found where the static scan of a non-empty tools directory should find some, or a
 * malformed/duplicate census-path entry).
 *
 * Run (from `platform/`):
 *   npx tsx scripts/census/shad_darshana_gates/authority_basis_census_seed.ts
 */
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs'
import path from 'node:path'
import { printGateReport, type GateResult } from './_report'

const REPO_ROOT = path.join(__dirname, '..', '..', '..', '..')
const MCP_TOOLS_ROOT = path.join(REPO_ROOT, 'platform-mcp/src/tools')
const REGISTRY_LAYERS_ROOT = path.join(REPO_ROOT, 'platform/src/lib/retrieval/registry/layers')

/**
 * Naive candidate-name pattern for "temporal-claim-bearing serving path" at seed stage:
 * any registered tool/capability whose name suggests it serves a time window, forecast,
 * dasha timing, transit window, prospective/standing prediction, or muhurta/election
 * timing. This is DELIBERATELY OVER-INCLUSIVE (a false positive here just means a path
 * gets tracked and later confirmed non-temporal or reclassified — cheap); the brief's own
 * item-44 census is explicitly described as growing over the campaign, not fixed at seed
 * time. Growing this pattern (or, better, replacing it with an explicit per-path opt-in
 * list once the eight kala_* facades + W2 field land) is future-wave work.
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

export interface AuthorityBasisCandidate {
  name: string
  source_file: string
  carries_authority_basis: boolean
}

/** Statically enumerates candidate temporal-claim-bearing tool registrations
 *  (server.tool('name', ...) / regAlias) whose name matches TEMPORAL_NAME_PATTERN, and
 *  greps the SAME source file for the literal `authority_basis` field name — a real,
 *  if simple, presence detector (see file header §N.7 note). */
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
    for (const name of names) {
      if (!TEMPORAL_NAME_PATTERN.test(name)) continue
      const key = `${name}@${f}`
      if (seen.has(key)) continue
      seen.add(key)
      candidates.push({
        name,
        source_file: path.relative(REPO_ROOT, f),
        carries_authority_basis: /authority_basis/.test(src),
      })
    }
  }
  return candidates.sort((a, b) => a.name.localeCompare(b.name))
}

function validate(): GateResult[] {
  const results: GateResult[] = []
  const registryLayersExist = existsSync(REGISTRY_LAYERS_ROOT)
  results.push({
    id: 'authbasis-census-scope-note',
    title: 'Scan scope',
    status: 'PASS',
    detail: `Scanned platform-mcp/src/tools for temporal-name-pattern tool registrations. platform/src/lib/retrieval/registry/layers (${registryLayersExist ? 'present' : 'MISSING'}) is a known second location for temporal capabilities (e.g. L3_kala/, L4_phala/ writers) NOT YET scanned by this seed — a real gap this seed names rather than silently missing (TODO before W2 population: extend enumerateAuthorityBasisCandidates to cover it too).`,
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

  const carrying = candidates.filter((c) => c.carries_authority_basis)
  results.push({
    id: 'authbasis-census-scoreboard',
    title: 'Authority-basis scoreboard (item 44) — reported, not gated, until W6 per brief §3',
    status: 'PASS',
    detail: `paths_enumerated=${candidates.length}, paths_carrying_authority_basis=${carrying.length}, paths_computing_own_window='not_yet_assessed' (clause (b) automation is future-wave work — see file header). At W0 this is EXPECTED to read 0/${candidates.length} — authority_basis does not exist anywhere pre-W2. A regression from a nonzero count established in a LATER wave would need this gate upgraded to compare-against-baseline (not yet — nothing has ever been nonzero).`,
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
