#!/usr/bin/env -S npx tsx
/**
 * run.ts — density/census harness (doctrine-waves D-1.5b Lane B-7, CLAUDE.md §N.6).
 *
 * PURPOSE: verify the Serving Density Principle (§N.6) mechanically on the surfaces that
 * already implement it — judgment_query and ganita_yogas_get — WITHOUT a live MCP connector
 * or a database. Modeled in spirit on `platform/scripts/audit/doctrine_harness/run.ts`
 * (same CLI contract: exit 0 all-green / 1 any-red, JSON receipt to stdout, an assertion
 * that cannot be evaluated reports red with a diagnosis, never a silent skip) but scoped to
 * density/layering rather than doctrine correctness, and OFFLINE by design: doctrine_harness
 * hits the deployed connector; this harness runs entirely against the checked-out source
 * tree + the real, pure `response_budget.ts` functions, so it is cheap enough to run on
 * every PR that touches the density-relevant files (see the CI wiring in ci.yml).
 *
 * Two assertion classes:
 *   - BEHAVIORAL: imports and calls the actual production `applyResponseBudget` /
 *     `finalizeMcpBudget` functions (platform-mcp/src/lib/response_budget.ts) with fixture
 *     data shaped like real responses — genuine code execution, not a source-text check.
 *   - CENSUS: structural/static checks against the source of the two capabilities
 *     (register_d9_judgment.ts, get_yoga_dosha.ts, register_p1_ganita.ts, registry_bridge.ts)
 *     confirming the specific §N.6 invariants those files are documented to uphold are still
 *     present. Same discipline class as this repo's existing drift_detector.py / naming-lint
 *     static gates — a regression here (someone silently deleting the hardFloor wiring, or
 *     merging catalog_only rows into the confirmed count) is caught without a live rebuild.
 *
 * Run: npx tsx platform/scripts/audit/density_harness/run.ts [--assertions <ids|all>]
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import {
  applyResponseBudget,
  type TrimmableSection,
} from '../../../../platform-mcp/src/lib/response_budget'

const REPO_ROOT = join(__dirname, '../../../..')

type Status = 'green' | 'red'
interface AssertionResult {
  id: string
  status: Status
  evidence: string
}

function readSource(relPath: string): string {
  return readFileSync(join(REPO_ROOT, relPath), 'utf8')
}

// ── DENSITY-1 (CENSUS): registry_bridge.ts wires hardFloor:true on judgment_query's ──
// bearing_yogas section — the confirmed/firings-authoritative layer that must survive a
// forced hard-cap trim (§N.6 principle #2; the D-1.5a wave gate finding this wiring fixed).
function densityOneJudgmentHardFloorWired(): AssertionResult {
  const id = 'DENSITY-1'
  try {
    const src = readSource('platform-mcp/src/tools/registry_bridge.ts')
    const pathIdx = src.indexOf("path: 'content.checklist.bearing_yogas'")
    if (pathIdx === -1) {
      return { id, status: 'red', evidence: 'content.checklist.bearing_yogas TrimmableSection not found in registry_bridge.ts' }
    }
    // hardFloor: true must appear before the next section's `path:` declaration (i.e.
    // inside THIS section's object literal), not merely somewhere later in the file.
    const nextPathIdx = src.indexOf('path:', pathIdx + 1)
    const sectionText = src.slice(pathIdx, nextPathIdx === -1 ? undefined : nextPathIdx)
    if (!/hardFloor:\s*true/.test(sectionText)) {
      return { id, status: 'red', evidence: 'bearing_yogas TrimmableSection found but hardFloor:true is not set on it' }
    }
    const minKeepMatch = sectionText.match(/minKeep:\s*(\d+)/)
    const minKeep = minKeepMatch ? Number(minKeepMatch[1]) : null
    if (minKeep === null || minKeep < 1) {
      return { id, status: 'red', evidence: `bearing_yogas minKeep is ${minKeep} — a hardFloor section must protect at least 1 confirmed row` }
    }
    return { id, status: 'green', evidence: `bearing_yogas TrimmableSection: hardFloor:true, minKeep:${minKeep}` }
  } catch (e) {
    return { id, status: 'red', evidence: `could not evaluate: ${String(e)}` }
  }
}

// ── DENSITY-2 (BEHAVIORAL): applyResponseBudget genuinely respects hardFloor under the ──
// PASS-2 hard-cap fallback — a section declaring hardFloor:true keeps its minKeep even when
// every other section has been floored to zero; a sibling section without hardFloor is
// floored to zero first. Real production code, fixture data only.
function densityTwoHardFloorBehavioral(): AssertionResult {
  const id = 'DENSITY-2'
  try {
    type Content = { confirmed: { id: number }[]; catalog_only: { id: number }[] }
    const makeContent = (): Content => ({
      confirmed: Array.from({ length: 20 }, (_, i) => ({ id: i })),
      catalog_only: Array.from({ length: 20 }, (_, i) => ({ id: i })),
    })

    const confirmedSection: TrimmableSection<Content> = {
      path: 'confirmed',
      label: 'confirmed (firings-authoritative)',
      minKeep: 3,
      hardFloor: true,
      getArray: (c) => c.confirmed,
      setArray: (c, kept) => { c.confirmed = kept as { id: number }[] },
      recover: { instrument: 'ganita_yoga_firings_get', hint: 'full confirmed detail' },
    }
    const catalogOnlySection: TrimmableSection<Content> = {
      path: 'catalog_only',
      label: 'catalog_only (single-pass label matches)',
      minKeep: 3,
      // no hardFloor — must be floorable to 0 under the hard-cap fallback.
      getArray: (c) => c.catalog_only,
      setArray: (c, kept) => { c.catalog_only = kept as { id: number }[] },
      recover: { instrument: 'ganita_yogas_get', hint: 'full catalog' },
    }

    // A tiny maxKb forces PASS 2 (the hard-cap fallback) for both sections.
    const content = makeContent()
    const result = applyResponseBudget(content, 0.05, [confirmedSection, catalogOnlySection])

    if (result.content.confirmed.length < confirmedSection.minKeep) {
      return {
        id, status: 'red',
        evidence: `hardFloor section 'confirmed' was cut below its declared minKeep=${confirmedSection.minKeep} ` +
          `(kept ${result.content.confirmed.length}) — the exact D-1.5a regression this section guards against`,
      }
    }
    if (result.content.catalog_only.length !== 0) {
      return {
        id, status: 'red',
        evidence: `non-hardFloor section 'catalog_only' was NOT floored to 0 under the hard-cap pass ` +
          `(kept ${result.content.catalog_only.length}) — fixture does not exercise PASS 2 as intended`,
      }
    }
    return {
      id, status: 'green',
      evidence: `hard-cap PASS 2: confirmed kept ${result.content.confirmed.length} (>= minKeep ${confirmedSection.minKeep}), ` +
        `catalog_only floored to 0 — hardFloor genuinely protects the denser layer`,
    }
  } catch (e) {
    return { id, status: 'red', evidence: `could not evaluate: ${String(e)}` }
  }
}

// ── DENSITY-3 (CENSUS): ganita_yogas_get's v3 verdict keeps catalog_only_rows_in_page ──
// separate from yogas_fired/doshas_fired (never merged into the confirmed count), and
// flags the caller honestly via judgment_flags when catalog-only rows are present.
function densityThreeYogasGetCatalogSeparation(): AssertionResult {
  const id = 'DENSITY-3'
  try {
    const src = readSource('platform-mcp/src/tools/register_p1_ganita.ts')
    const verdictIdx = src.indexOf('const verdict = {')
    const yogasFiredIdx = src.indexOf("yogas_fired:", verdictIdx)
    if (verdictIdx === -1 || yogasFiredIdx === -1) {
      return { id, status: 'red', evidence: 'ganita_yogas_get v3 verdict object (yogas_fired) not found' }
    }
    const verdictBlockEnd = src.indexOf('\n        }', verdictIdx)
    const verdictBlock = src.slice(verdictIdx, verdictBlockEnd === -1 ? undefined : verdictBlockEnd)
    if (!/catalog_only_rows_in_page:/.test(verdictBlock)) {
      return { id, status: 'red', evidence: 'verdict object no longer carries catalog_only_rows_in_page as a distinct field' }
    }
    // The confirmed count must NOT be computed by adding catalog-only rows into it —
    // guard against a regression that folds catalogOnlyRows into yogas_fired/doshas_fired.
    const yogasFiredLine = verdictBlock.match(/yogas_fired:.*$/m)?.[0] ?? ''
    if (/catalogOnlyRows|catalog_only/i.test(yogasFiredLine)) {
      return { id, status: 'red', evidence: `yogas_fired computation appears to reference catalog-only rows: "${yogasFiredLine}"` }
    }
    if (!src.includes("catalog_only_rows_present")) {
      return { id, status: 'red', evidence: 'no judgment_flags entry (catalog_only_rows_present) found — caller not honestly flagged when catalog-only rows are served' }
    }
    return { id, status: 'green', evidence: 'verdict.catalog_only_rows_in_page is distinct from yogas_fired/doshas_fired; judgment_flags carries catalog_only_rows_present' }
  } catch (e) {
    return { id, status: 'red', evidence: `could not evaluate: ${String(e)}` }
  }
}

// ── DENSITY-4 (CENSUS): get_yoga_dosha.ts never silently drops catalog-only rows from ──
// the served `rows` array (B.10 — weak-tail/requires_pass rows still serve) while
// computing catalogOnlyCount as a SEPARATE tally, not a filter applied to `rows` itself.
function densityFourYogaDoshaRowsNeverDropped(): AssertionResult {
  const id = 'DENSITY-4'
  try {
    const src = readSource('platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_dosha.ts')
    if (!/rows:\s*result\.rows\s*\?\?\s*\[\]/.test(src)) {
      return { id, status: 'red', evidence: 'served rows field no longer maps 1:1 from the unfiltered query result — cannot confirm rows are never dropped' }
    }
    if (!/catalogOnlyCount\s*=\s*\(result\.rows\s*\?\?\s*\[\]\)\.filter/.test(src)) {
      return { id, status: 'red', evidence: 'catalogOnlyCount is not computed as a separate filter/count over result.rows — density-count wiring may have changed' }
    }
    if (!src.includes('catalog_only_rows_in_page')) {
      return { id, status: 'red', evidence: 'catalog_only_rows_in_page not present in the served content — the count is not surfaced to the caller' }
    }
    return { id, status: 'green', evidence: 'rows served unfiltered (fire_reason=requires_pass rows are NOT dropped); catalogOnlyCount is a separate, additive tally, not a filter on rows' }
  } catch (e) {
    return { id, status: 'red', evidence: `could not evaluate: ${String(e)}` }
  }
}

const ALL_ASSERTIONS: Record<string, () => AssertionResult> = {
  'DENSITY-1': densityOneJudgmentHardFloorWired,
  'DENSITY-2': densityTwoHardFloorBehavioral,
  'DENSITY-3': densityThreeYogasGetCatalogSeparation,
  'DENSITY-4': densityFourYogaDoshaRowsNeverDropped,
}

function parseArgs(argv: string[]): string[] | 'all' {
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--assertions') {
      const val = argv[++i]
      return val === 'all' ? 'all' : val.split(',').map((s) => s.trim())
    }
  }
  return 'all'
}

function main(): void {
  const requested = parseArgs(process.argv.slice(2))
  const ids = requested === 'all' ? Object.keys(ALL_ASSERTIONS) : requested

  const unknown = ids.filter((id) => !ALL_ASSERTIONS[id])
  if (unknown.length > 0) {
    console.error(JSON.stringify({ error: 'UNKNOWN_ASSERTION_IDS', unknown, known: Object.keys(ALL_ASSERTIONS) }))
    process.exit(2)
  }

  const results = ids.map((id) => ALL_ASSERTIONS[id]())
  const green = results.filter((r) => r.status === 'green').map((r) => r.id)
  const red = results.filter((r) => r.status === 'red').map((r) => r.id)

  const receipt = {
    harness: 'density_harness',
    principle: 'CLAUDE.md §N.6 — Serving Density Principle',
    run_at: new Date().toISOString(),
    requested,
    summary: { total: results.length, green: green.length, red: red.length, green_ids: green, red_ids: red },
    results,
  }

  console.log(JSON.stringify(receipt, null, 2))
  process.exit(red.length > 0 ? 1 : 0)
}

main()
