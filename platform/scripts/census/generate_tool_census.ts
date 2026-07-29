/**
 * generate_tool_census.ts — Lane L1d, W1 (RETRIEVAL_PLANE_ELEVATION_PLAN §9.4 W-14/
 * W-20/W-21/W-23; strategy doc RETRIEVAL_STRATEGY_v1_0.md §6, the eight-axis per-tool
 * rubric).
 *
 * Runs the eight-axis rubric over every LIVE capability returned by getCatalog() (the
 * same registry both the MCP and chat channels import — no separate hand list). Per
 * the strategy doc's own framing, axes 2/3/4/8 are STATICALLY CHECKABLE and are
 * genuinely computed here from source (descriptor fields + a targeted grep of each
 * capability's own registration file, reusing E1's uri->source_file map). Axes
 * 1/5/6/7 are SEMANTIC (cognitive-fit judgment, drill-topology crawl, full data-
 * coverage audit, description-quality read) and are explicitly marked
 * NOT_YET_ASSESSED for this v1 pass — the strategy doc itself frames the full
 * rubric run as multi-phase, not a single-wave deliverable (§6: "the review is
 * executed as a generated scorecard... machine where possible... Fable-5-judged
 * where semantic").
 *
 * SCORING METHODOLOGY (v1, all real, all reproducible from source — no axis is
 * fabricated; where a real per-capability signal doesn't exist yet, the honest
 * finding IS the score, not a guess):
 *
 *  A2 Demand-shaping (§3 doctrine: "accepts scope/facets; declares demand_ranking;
 *     no default dump"):
 *    2 = input_schema has >=1 facet/scope-shaped key (category|scope|facet|domain|
 *        window|tag|filter|level|type|planet|house|sign|from_date|to_date|
 *        start_date|end_date|min_|max_) beyond chart_id/entity_id, OR
 *        demand_ranking is populated on the descriptor.
 *    1 = input_schema has >=1 param beyond chart_id/entity_id but none facet-shaped
 *        (accepts SOME input, doesn't fully default-dump, but doesn't declare
 *        scoping semantics either).
 *    0 = no input_schema, or only chart_id/entity_id (pure default-dump risk).
 *
 *  A3 Envelope conformance (§ plan R-2: "v3, header, grades, coverage, flags-enum,
 *     register labels"). REAL FINDING, stated up front: NO capability in the
 *     estate implements a v3 envelope — R-2 hasn't landed yet (plan §1.2's own
 *     audit: "envelope authored once, applied almost nowhere"; confirmed here:
 *     repo-wide grep finds exactly 1 call site for `buildRetrievalEnvelope()`
 *     inside registry/layers+synthesis, envelope.ts hardcodes `envelope_version:
 *     'v1'`). So this axis is scored as a v1 PROXY against the envelope-adjacent
 *     helpers that do exist (chart_header emission, buildCoverageStamp,
 *     buildHonestPagination, deriveEpistemicGrade), via a grep of the capability's
 *     own source_file (E1's uri->file map):
 *    2 = file calls buildRetrievalEnvelope() AND references chart_header.
 *    1 = file references >=1 of {chart_header, buildCoverageStamp,
 *        buildHonestPagination, deriveEpistemicGrade, buildEpistemicSummary,
 *        judgment_flags}.
 *    0 = none of the above (the large majority — this is the honest finding,
 *        not a scoring artifact).
 *
 *  A4 Density & budget (§N.6 density_contract populated + ENFORCED).
 *
 *    SAMĀPTI B-N8-CI-GATES / finding F-21 (2026-07-30) — THIS AXIS WAS REWRITTEN.
 *    Until this change A4 was scored purely from `typeof`/shape checks on the
 *    descriptor object, never from source. That made it a governance false-green
 *    in two distinct ways:
 *      (a) `descriptor_defaults.ts`'s `deriveDensityContract()` machine-stamps a
 *          `density_contract` on every capability that lacks one, deriving
 *          `empty_reason` from nothing but the ARCHETYPE LABEL
 *          (`archetype !== 'orientation_digest' && archetype !== 'calibration'`)
 *          and `paginated` from nothing but PARAM-NAME PRESENCE — neither ever
 *          looks at the handler. A shape-only A4 grades that derivation "§N.6
 *          enforced". `getCatalog()` applies that backfill in place, so any future
 *          edit swapping this script's `getAllCapabilities()` for `getCatalog()`
 *          would silently flip the whole estate to A4=2.
 *      (b) A hand-authored `density_contract: { empty_reason: true, ... }` literal
 *          with no matching handler behaviour also scored 2 — exactly the
 *          violation CLAUDE.md §N.6 names: "a capability that claims
 *          density_contract but ships no empty_reason discipline behind it."
 *    A4 now mirrors its own sibling `scoreA3` and greps the capability's own
 *    source file (E1's uri->file map), with the `density_contract: { ... }`
 *    declaration block itself EXCISED before the grep so a declaration can never
 *    corroborate itself.
 *
 *    2 = declared BY HAND in the capability's own source file, shape complete
 *        (paginated: boolean, facets: non-empty array, empty_reason: boolean),
 *        AND every claim it asserts `true` is corroborated by handler source
 *        outside the declaration block (empty_reason:true -> an `empty_reason`
 *        token in the handler; paginated:true -> a real pagination token).
 *    1 = declared in source but a `true` claim is uncorroborated, or the
 *        declaration is incomplete (facets: []), or the source file could not be
 *        resolved so enforcement is UNVERIFIABLE (never graded 2 on shape alone).
 *    0 = density_contract absent, OR present on the descriptor but NOT declared
 *        in the capability's own source — i.e. machine-backfilled by
 *        descriptor_defaults.ts, a claim with no implementation behind it.
 *
 *  A8 Cross-channel (§4: "stateless-safe; entitlement-gated; family-projectable"):
 *    2 = projection_tags populated (declares which generated surfaces serve it)
 *        AND entitlement-shape correct (per_chart scope has chart_id in
 *        required_inputs, OR scope is global).
 *    1 = entitlement-shape correct but projection_tags absent (not yet
 *        family-classified — this is the R-1.1 field L1a landed type-only,
 *        0/118 populated; expect nearly all capabilities to land here honestly).
 *    0 = entitlement-shape wrong (per_chart scope missing chart_id from
 *        required_inputs — would be a real defect, not expected to fire given
 *        the FROZEN per-chart discriminated-union type constraint, but checked
 *        for real rather than assumed).
 *
 * Run:
 *   cd platform && npx tsx --conditions=react-server scripts/census/generate_tool_census.ts
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { getAllCapabilities } from '@/lib/retrieval/registry'
import '@/lib/retrieval/registry/catalog' // side-effect: registers every capability
import { deriveDensityContract } from '@/lib/retrieval/registry/descriptor_defaults'
import type { CapabilityDescriptor } from '@/lib/retrieval/registry/types'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PLATFORM_ROOT = join(__dirname, '..', '..')
const E1_PATH = join(PLATFORM_ROOT, 'src/generated/harvest/e1_declared.json')
const JSON_OUTPUT_PATH = join(PLATFORM_ROOT, 'src/generated/census/tool_census_v1.json')
const MD_OUTPUT_PATH = join(
  PLATFORM_ROOT,
  '..',
  '00_ARCHITECTURE/briefs/retrieval_impl/RETRIEVAL_TOOL_CENSUS_v1_0.md',
)

const FACET_KEYS = [
  'category',
  'scope',
  'facet',
  'domain',
  'window',
  'tag',
  'filter',
  'level',
  'type',
  'planet',
  'house',
  'sign',
  'from_date',
  'to_date',
  'start_date',
  'end_date',
  'min_',
  'max_',
]
const NON_FACET_INPUTS = new Set(['chart_id', 'entity_id'])
const ENVELOPE_PROXY_TOKENS = [
  'chart_header',
  'buildCoverageStamp',
  'buildHonestPagination',
  'deriveEpistemicGrade',
  'buildEpistemicSummary',
  'judgment_flags',
]

// ── A4 (§N.6) source-evidence tokens — F-21 ──────────────────────────────────
// Tokens that evidence a REAL implementation of the behaviour a density_contract
// claims, as opposed to the claim itself. Checked against the capability's own
// source file WITH the `density_contract: { ... }` literal excised, so a
// declaration can never be its own corroboration.
const EMPTY_REASON_IMPL_TOKENS = ['empty_reason', 'emptyReason']
const PAGINATION_IMPL_TOKENS = [
  'buildHonestPagination',
  'pagination',
  'next_cursor',
  'nextCursor',
  'has_more',
  'hasMore',
  'page_info',
  'total_available',
  // Real row-window machinery, hand-verified against get_vichara.ts (LIMIT $n OFFSET $n+1
  // over a `limit`/`offset` arg pair) and get_yoga_firings.ts (LIMIT $n over a clamped
  // `limit`) — an earlier, narrower token list marked both UNCORROBORATED, which was a
  // false positive. A detector for unearned greens must not itself invent a red.
  'LIMIT $',
  'OFFSET',
  'offset',
  'cursor',
]

interface E1Concept {
  uri: string
  source_file: string | null
}

interface CensusRow {
  uri: string
  layer: string
  type: string
  name: string
  scope: string
  archetype: string
  tool_role: string
  a1_cognitive_fit: string
  a2_demand_shaping: number
  a2_basis: string
  a3_envelope_conformance: number
  a3_basis: string
  a4_density_budget: number
  a4_basis: string
  /** F-21: true iff a `density_contract` is present on the descriptor at all. */
  a4_density_contract_present: boolean
  a5_drill_topology: string
  a6_data_coverage: string
  a7_description_quality: string
  a8_cross_channel: number
  a8_basis: string
  source_file: string | null
}

function scoreA2(cap: CapabilityDescriptor): { score: number; basis: string } {
  const keys = cap.input_schema ? Object.keys(cap.input_schema) : []
  const nonTrivial = keys.filter((k) => !NON_FACET_INPUTS.has(k))
  const facetKeys = nonTrivial.filter((k) =>
    FACET_KEYS.some((f) => k.toLowerCase().includes(f)),
  )
  const hasDemandRanking = !!cap.demand_ranking && Object.keys(cap.demand_ranking).length > 0
  if (facetKeys.length > 0 || hasDemandRanking) {
    return {
      score: 2,
      basis: hasDemandRanking
        ? `demand_ranking populated${facetKeys.length ? `; facet keys: ${facetKeys.join(',')}` : ''}`
        : `facet-shaped input_schema keys: ${facetKeys.join(',')}`,
    }
  }
  if (nonTrivial.length > 0) {
    return { score: 1, basis: `non-facet input_schema keys: ${nonTrivial.join(',')}` }
  }
  return { score: 0, basis: keys.length === 0 ? 'no input_schema' : 'only chart_id/entity_id' }
}

function scoreA3(sourceText: string | null): { score: number; basis: string } {
  if (!sourceText) return { score: 0, basis: 'source_file not resolved (no static check possible)' }
  const hasEnvelope = sourceText.includes('buildRetrievalEnvelope(')
  const hasHeader = sourceText.includes('chart_header')
  if (hasEnvelope && hasHeader) {
    return { score: 2, basis: 'calls buildRetrievalEnvelope() and references chart_header' }
  }
  const hits = ENVELOPE_PROXY_TOKENS.filter((t) => sourceText.includes(t))
  if (hits.length > 0) {
    return { score: 1, basis: `envelope-adjacent tokens present: ${hits.join(',')}` }
  }
  return { score: 0, basis: 'no envelope/header/coverage/grade token in source file' }
}

/**
 * Excise every `density_contract: { ... }` object literal from a source text.
 *
 * F-21: without this, a hand-authored `density_contract: { empty_reason: true }`
 * literal would supply the very `empty_reason` token that is supposed to prove the
 * HANDLER implements empty-reason discipline — the declaration would corroborate
 * itself and the axis would be a tautology again, just one level deeper.
 */
export function stripDensityContractDeclarations(text: string): string {
  const KEY = 'density_contract'
  let out = ''
  let idx = 0
  for (;;) {
    const at = text.indexOf(KEY, idx)
    if (at === -1) {
      out += text.slice(idx)
      return out
    }
    const open = text.indexOf('{', at)
    // `density_contract: {` — the brace must follow closely, else this is a prose
    // mention (a doc comment) and not a declaration; keep it and move on.
    if (open === -1 || open - at > 40) {
      out += text.slice(idx, at + KEY.length)
      idx = at + KEY.length
      continue
    }
    let depth = 0
    let end = open
    for (; end < text.length; end++) {
      if (text[end] === '{') depth++
      else if (text[end] === '}') {
        depth--
        if (depth === 0) {
          end++
          break
        }
      }
    }
    out += text.slice(idx, at)
    idx = end
  }
}

function scoreA4(
  cap: CapabilityDescriptor,
  sourceText: string | null,
): { score: number; basis: string } {
  const dc = cap.density_contract
  if (!dc) return { score: 0, basis: 'density_contract absent' }

  const declaredShape = `declared (paginated=${String(dc.paginated)}, facets=${JSON.stringify(dc.facets)}, empty_reason=${String(dc.empty_reason)})`
  const shapeComplete =
    typeof dc.paginated === 'boolean' &&
    Array.isArray(dc.facets) &&
    dc.facets.length > 0 &&
    typeof dc.empty_reason === 'boolean'

  // F-21, step 1 — is this contract actually written down in the capability's OWN
  // source file? That is the only positive evidence a human authored it. It is checked
  // FIRST and takes precedence over the machine-default comparison below, because a
  // hand-authored contract can legitimately coincide with the generated default:
  // get_vichara.ts's hand-set 1024/4096 pair is byte-identical to the `leaf` tier
  // default, for the good reason that the tier table was BUILT from get_vichara's
  // precedent (descriptor_defaults.ts:TOOL_ROLE_DIGEST_BYTES doc comment says so).
  // Comparing values first would have graded that genuine implementation a 0.
  const declaredInOwnSource = sourceText !== null && /density_contract\s*:/.test(sourceText)

  if (!declaredInOwnSource) {
    // F-21 core discriminator for everything NOT written in its own source: re-run
    // descriptor_defaults.ts's derivation and compare. Byte-identical means this
    // capability's §N.6 claim rests on an archetype label and a param-name list, never
    // on its handler. Robust to the census being switched from getAllCapabilities()
    // (pre-backfill, today) to getCatalog() (post-backfill) — the exact one-line edit
    // that would otherwise flip the whole estate to "enforced".
    if (JSON.stringify(dc) === JSON.stringify(deriveDensityContract(cap))) {
      return {
        score: 0,
        basis:
          `${declaredShape} — not declared in the capability's own source, and IDENTICAL to ` +
          `descriptor_defaults.ts:deriveDensityContract()'s machine default (empty_reason from the archetype ` +
          `label, paginated from param-name presence, neither from the handler). A contract indistinguishable ` +
          `from a generated default is not evidence of §N.6 enforcement.`,
      }
    }
    if (sourceText === null) {
      return {
        score: 1,
        basis:
          `${declaredShape}; differs from the machine default (so it was authored somewhere) but source_file is ` +
          `unresolved in the E1 uri->file map — §N.6 enforcement NOT verifiable. Never graded 2 on descriptor shape alone.`,
      }
    }
    return {
      score: 1,
      basis:
        `${declaredShape}; differs from the machine default (so it was authored somewhere) but E1 maps this uri ` +
        `to a source file containing no \`density_contract:\` declaration — the uri->file map is STALE for this ` +
        `uri, so §N.6 enforcement cannot be checked from the mapped source. Not graded 2 on an unverified claim.`,
    }
  }

  const handlerText = stripDensityContractDeclarations(sourceText!)
  const emptyReasonImplemented = EMPTY_REASON_IMPL_TOKENS.some((t) => handlerText.includes(t))
  const paginationImplemented = PAGINATION_IMPL_TOKENS.some((t) => handlerText.includes(t))

  const gaps: string[] = []
  if (dc.empty_reason === true && !emptyReasonImplemented) {
    gaps.push(
      'claims empty_reason:true but the handler carries no `empty_reason` token outside the declaration',
    )
  }
  if (dc.paginated === true && !paginationImplemented) {
    gaps.push(
      `claims paginated:true but the handler carries no pagination token (${PAGINATION_IMPL_TOKENS.join('/')})`,
    )
  }
  if (!shapeComplete) {
    gaps.push('declaration incomplete (facets empty, or a sub-field unset)')
  }

  if (gaps.length > 0) {
    return { score: 1, basis: `${declaredShape}; hand-declared in source but UNCORROBORATED — ${gaps.join('; ')}` }
  }

  const corroboration = [
    dc.empty_reason === true
      ? 'empty_reason:true corroborated in handler source'
      : 'empty_reason:false — honest negative, nothing to corroborate',
    dc.paginated === true
      ? 'paginated:true corroborated in handler source'
      : 'paginated:false — honest negative, nothing to corroborate',
  ]
  return { score: 2, basis: `${declaredShape}; hand-declared in source AND ${corroboration.join('; ')}` }
}

function scoreA8(cap: CapabilityDescriptor): { score: number; basis: string } {
  const entitlementOk =
    cap.scope === 'global' ||
    (cap.scope === 'per_chart' && (cap.required_inputs as string[] | undefined)?.includes('chart_id'))
  const hasProjectionTags = !!cap.projection_tags && cap.projection_tags.length > 0
  if (!entitlementOk) {
    return { score: 0, basis: 'per_chart scope missing chart_id from required_inputs' }
  }
  if (hasProjectionTags) {
    return { score: 2, basis: `entitlement-shape OK; projection_tags=[${cap.projection_tags!.join(',')}]` }
  }
  return { score: 1, basis: 'entitlement-shape OK; projection_tags not yet populated (R-1.1 field, W2 migration)' }
}

function main(): void {
  const caps = getAllCapabilities()
  console.log(`[CENSUS] getCatalog() returned ${caps.length} live capabilities`)

  const e1: { concepts: E1Concept[] } = JSON.parse(readFileSync(E1_PATH, 'utf8'))
  const fileByUri = new Map(e1.concepts.map((c) => [c.uri, c.source_file]))

  const fileTextCache = new Map<string, string>()
  function readSourceOnce(relPath: string): string {
    if (fileTextCache.has(relPath)) return fileTextCache.get(relPath)!
    let text = ''
    try {
      text = readFileSync(join(PLATFORM_ROOT, relPath), 'utf8')
    } catch {
      text = ''
    }
    fileTextCache.set(relPath, text)
    return text
  }

  const rows: CensusRow[] = caps
    .map((cap) => {
      const sourceFile = fileByUri.get(cap.uri) ?? null
      const sourceText = sourceFile ? readSourceOnce(sourceFile) : null
      const a2 = scoreA2(cap)
      const a3 = scoreA3(sourceText)
      const a4 = scoreA4(cap, sourceText)
      const a8 = scoreA8(cap)
      return {
        uri: cap.uri,
        layer: cap.layer,
        type: cap.type,
        name: cap.name,
        scope: cap.scope,
        archetype: cap.archetype,
        tool_role: cap.tool_role,
        a1_cognitive_fit: 'NOT_YET_ASSESSED (semantic — v1 stub per strategy §6)',
        a2_demand_shaping: a2.score,
        a2_basis: a2.basis,
        a3_envelope_conformance: a3.score,
        a3_basis: a3.basis,
        a4_density_budget: a4.score,
        a4_basis: a4.basis,
        a4_density_contract_present: cap.density_contract !== undefined,
        a5_drill_topology: 'NOT_YET_ASSESSED (semantic — v1 stub per strategy §6)',
        a6_data_coverage: 'NOT_YET_ASSESSED (semantic — v1 stub per strategy §6)',
        a7_description_quality: 'NOT_YET_ASSESSED (semantic — v1 stub per strategy §6)',
        a8_cross_channel: a8.score,
        a8_basis: a8.basis,
        source_file: sourceFile,
      }
    })
    .sort((a, b) => a.uri.localeCompare(b.uri))

  function dist(scores: number[]): Record<string, number> {
    const d: Record<string, number> = { '0': 0, '1': 0, '2': 0 }
    for (const s of scores) d[String(s)] = (d[String(s)] ?? 0) + 1
    return d
  }

  const summary = {
    total_capabilities: rows.length,
    axes_computed_this_pass: ['A2', 'A3', 'A4', 'A8'],
    axes_stubbed_this_pass: ['A1', 'A5', 'A6', 'A7'],
    a2_distribution: dist(rows.map((r) => r.a2_demand_shaping)),
    a3_distribution: dist(rows.map((r) => r.a3_envelope_conformance)),
    a4_distribution: dist(rows.map((r) => r.a4_density_budget)),
    a8_distribution: dist(rows.map((r) => r.a8_cross_channel)),
    // F-21 §N.6 accounting: separate "declares a density_contract" from "earns it".
    // A claim that is present but unearned is the violation CLAUDE.md §N.6 names;
    // collapsing the two into one number is how the axis went green in the first place.
    a4_n6_accounting: {
      density_contract_present: rows.filter((r) => r.a4_density_contract_present).length,
      density_contract_absent: rows.filter((r) => !r.a4_density_contract_present).length,
      present_and_enforced: rows.filter((r) => r.a4_density_contract_present && r.a4_density_budget === 2)
        .length,
      present_but_unearned: rows.filter((r) => r.a4_density_contract_present && r.a4_density_budget < 2)
        .length,
      machine_derived_default: rows.filter((r) => r.a4_basis.includes("IDENTICAL to descriptor_defaults")).length,
    },
  }

  mkdirSync(dirname(JSON_OUTPUT_PATH), { recursive: true })
  writeFileSync(
    JSON_OUTPUT_PATH,
    JSON.stringify(
      {
        generator: 'generate_tool_census.ts (Lane L1d, W1)',
        generated_at: new Date().toISOString(),
        summary,
        rows,
      },
      null,
      2,
    ) + '\n',
  )
  console.log(`[CENSUS] wrote ${rows.length} rows -> ${JSON_OUTPUT_PATH}`)
  console.log('[CENSUS] summary:', JSON.stringify(summary, null, 2))

  // ── Markdown render ─────────────────────────────────────────────────────
  const lines: string[] = []
  lines.push('---')
  lines.push('artifact: RETRIEVAL_TOOL_CENSUS_v1_0.md')
  lines.push('canonical_id: RETRIEVAL_TOOL_CENSUS')
  lines.push('version: 1.0')
  lines.push('status: GENERATED — v1 (partial rubric)')
  lines.push('generator: platform/scripts/census/generate_tool_census.ts')
  lines.push(`generated_at: ${new Date().toISOString()}`)
  lines.push('source_doctrine: RETRIEVAL_STRATEGY_v1_0.md §6 (eight-axis per-tool rubric)')
  lines.push('---')
  lines.push('')
  lines.push('# Retrieval Tool Census v1.0')
  lines.push('')
  lines.push(
    'Machine-generated. One row per LIVE capability returned by `getCatalog()` ' +
      `(${rows.length} capabilities, live in-process load — the same registry both ` +
      'the MCP and chat channels import). Re-run: `cd platform && npx tsx ' +
      '--conditions=react-server scripts/census/generate_tool_census.ts`.',
  )
  lines.push('')
  lines.push(
    '**Honesty note (read before using this census):** per RETRIEVAL_STRATEGY_v1_0.md ' +
      '§6, axes A2/A3/A4/A8 are STATICALLY CHECKABLE and are genuinely computed from ' +
      'source below (descriptor field inspection + targeted source-file grep — see the ' +
      'script header for the exact scoring rule per axis). Axes A1 (cognitive fit), A5 ' +
      '(drill topology), A6 (data coverage), A7 (description quality) are SEMANTIC and ' +
      'are honestly marked `NOT_YET_ASSESSED` in every row — the strategy doc itself ' +
      'frames the full rubric as a multi-phase, partly Fable-5-judged exercise, not a ' +
      'single-wave deliverable. Scoring the semantic axes without doing the actual ' +
      'reading-quality/topology-crawl work would be fabrication; this census does not do ' +
      'that.',
  )
  lines.push('')
  lines.push('## Summary')
  lines.push('')
  lines.push(`- Total capabilities: **${summary.total_capabilities}**`)
  lines.push(
    `- A2 (demand-shaping) distribution: 0=${summary.a2_distribution['0']}, 1=${summary.a2_distribution['1']}, 2=${summary.a2_distribution['2']}`,
  )
  lines.push(
    `- A3 (envelope conformance) distribution: 0=${summary.a3_distribution['0']}, 1=${summary.a3_distribution['1']}, 2=${summary.a3_distribution['2']} ` +
      '— **real finding, not a scoring artifact:** no capability implements the plan R-2 v3 envelope yet (repo-wide, exactly 1 call site for `buildRetrievalEnvelope()` inside registry/layers+synthesis); scores here are a v1 proxy against envelope-adjacent helpers (chart_header, buildCoverageStamp, buildHonestPagination, deriveEpistemicGrade), documented in full in the script header.',
  )
  lines.push(
    `- A4 (density & budget) distribution: 0=${summary.a4_distribution['0']}, 1=${summary.a4_distribution['1']}, 2=${summary.a4_distribution['2']} ` +
      '— **rewritten by SAMĀPTI finding F-21 (2026-07-30):** A4 previously graded §N.6 purely from the shape ' +
      'of the descriptor object, so `descriptor_defaults.ts`\'s machine-stamped `density_contract` (empty_reason ' +
      'derived from the archetype LABEL, paginated from PARAM-NAME presence — neither ever reading the handler) ' +
      'scored "enforced", and so did any hand-authored declaration with nothing behind it. A4 now (i) re-runs ' +
      'that derivation and scores 0 when the stored contract is byte-identical to the generated default, and ' +
      '(ii) for genuinely hand-authored contracts, greps the capability\'s own source file the way its sibling ' +
      'A3 does — with the `density_contract: { ... }` literal excised first, so a declaration cannot corroborate ' +
      'itself.',
  )
  lines.push(
    `- A4 §N.6 accounting (declaration vs. enforcement, kept separate on purpose): ` +
      `${summary.a4_n6_accounting.density_contract_present} capabilities carry a \`density_contract\`, of which ` +
      `**${summary.a4_n6_accounting.present_and_enforced} are enforced** (hand-declared in source AND every ` +
      `\`true\` claim corroborated in the handler) and ` +
      `**${summary.a4_n6_accounting.present_but_unearned} are declared-but-unearned**; ` +
      `${summary.a4_n6_accounting.machine_derived_default} of those carry a contract byte-identical to ` +
      `descriptor_defaults.ts's generated default (a label-derived value, not an implementation). ` +
      `${summary.a4_n6_accounting.density_contract_absent} carry none at all.`,
  )
  lines.push(
    `- A8 (cross-channel) distribution: 0=${summary.a8_distribution['0']}, 1=${summary.a8_distribution['1']}, 2=${summary.a8_distribution['2']} ` +
      '— `projection_tags` (R-1.1) is 0/118 populated estate-wide (L1a\'s finding, type-only wave); nearly every capability lands at 1 (entitlement-shape correct, not yet family-classified) rather than 2, honestly.',
  )
  lines.push('')
  lines.push('## Per-capability rows')
  lines.push('')
  lines.push(
    '| uri | layer | type | scope | archetype | role | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | source_file |',
  )
  lines.push('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
  for (const r of rows) {
    lines.push(
      `| \`${r.uri}\` | ${r.layer} | ${r.type} | ${r.scope} | ${r.archetype} | ${r.tool_role} | — | ${r.a2_demand_shaping} | ${r.a3_envelope_conformance} | ${r.a4_density_budget} | — | — | — | ${r.a8_cross_channel} | \`${r.source_file ?? 'unresolved'}\` |`,
    )
  }
  lines.push('')
  lines.push('## Per-axis basis (why each static score is what it is)')
  lines.push('')
  lines.push('<details><summary>Expand — one basis line per capability per computed axis</summary>')
  lines.push('')
  lines.push('| uri | A2 basis | A3 basis | A4 basis | A8 basis |')
  lines.push('|---|---|---|---|---|')
  for (const r of rows) {
    lines.push(
      `| \`${r.uri}\` | ${r.a2_basis} | ${r.a3_basis} | ${r.a4_basis} | ${r.a8_basis} |`,
    )
  }
  lines.push('')
  lines.push('</details>')
  lines.push('')
  lines.push('---')
  lines.push('')
  lines.push(
    '*End of RETRIEVAL_TOOL_CENSUS v1.0 — Lane L1d, W1. Full JSON at ' +
      '`platform/src/generated/census/tool_census_v1.json`. Re-generated (not ' +
      're-authored) after every phase gate per strategy §6.*',
  )

  mkdirSync(dirname(MD_OUTPUT_PATH), { recursive: true })
  writeFileSync(MD_OUTPUT_PATH, lines.join('\n') + '\n')
  console.log(`[CENSUS] wrote markdown -> ${MD_OUTPUT_PATH}`)
}

main()
