/**
 * tools/dossier.ts — Elevation Campaign v2.1 · Stream γ (PŪRṆA) · Lane Ω5.
 * The gather-then-compose paging engine + structural synthesis gate.
 * ============================================================================
 *
 * `dossier(domain, chart_id, budget_kb?, cursor?)` serves a domain's ENTIRE TCI
 * slice (every concept the Ω1 inventory carries for the domain) in budget-capped
 * PAGES, and physically WITHHOLDS every interpretive surface until the accumulated
 * receipt reaches 100% accounting. It is EL-29's composition doctrine wired to
 * EL-02's completeness receipt as its gate — the mechanism that actually gets the
 * whole territory into the model before it speaks.
 *
 * WHAT A PAGE CARRIES (data + accounting ONLY, pre-gate):
 *   - `page_units`: coverage UNITS grouped from the slice. Each unit names its live
 *     `serving_tool` + `serving_args` (the drill handle — HOW to fetch the real rows)
 *     and its accounting `state` (Ω3's five states) and concept count. This is the
 *     densest honest representation of "here is everything that exists for this
 *     domain, its grounding, and how to reach it."
 *   - `coverage_so_far`: the running Ω3 tally (served / empty_for_this_chart /
 *     not_computed_globally / superseded_by_aggregate / excluded_by_named_rule),
 *     with `accounted` and `pct`.
 *   - `synthesis_gate`: 'BLOCKED' until `accounted == slice_size`, then 'OPEN'.
 *
 * THE GATE IS STRUCTURAL, NOT HORTATORY (charter Ω5, red-team finding #12): the
 * interpretive surfaces (`composition_scaffold`, verdicts, ranked prose) are
 * emitted by a code path that only runs when `synthesis_gate === 'OPEN'`. A page
 * served before OPEN is content-starved by construction — a premature composition
 * is visibly missing its scaffold rather than plausibly complete. `retrieval_receipts`
 * additionally records `composed_before_gate` whenever a caller asks for composition
 * (`compose: true`) while coverage is < 100% — this feeds Lane K2's grading.
 *
 * NO COMPUTATION IS REIMPLEMENTED (B.10, charter Ω5): the dossier does not compute
 * chart values. It pages a DETERMINISTIC join of already-produced artifacts (Ω3's
 * completeness accounting × Ω1's TCI serving handles), pre-compiled into compact
 * slice bundles under resources/vidhi/dossier_slices/. Every served unit carries the
 * exact `serving_tool` + `serving_args` a caller invokes to hydrate real rows — the
 * graha_portrait "call the already-built handlers" pattern, exposed as drill handles
 * rather than inlined (the density target — 13820 concepts in ≤6 pages @ a 25k-token
 * client — forbids inlining full handler outputs; densification, never truncation).
 *
 * DENSITY ACCEPTANCE (measured): the wealth slice of 482012f1 (13820 concepts, 100%
 * accounted) fits ≤6 pages at budget_kb=16 (a 25k-token client) and ≤2 pages at
 * budget_kb=64 (a 200k-token client). See `budgetKbForClientTokens`.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { remoteAuthorize } from '../lib/authz.js'
import type { Principal } from '../types.js'
// Slice bundles are embedded as a compiled TS module (not read from disk) so the
// engine's data ships in dist with zero runtime filesystem / Docker-copy dependency.
import { DOSSIER_SLICE_BUNDLES } from '../resources/vidhi/dossier_slices/dossier_slices.generated.js'

// C1: budget_kb is 1..64; the server ceiling is a hard cap, never exceedable.
const BUDGET_KB_MIN = 1
const BUDGET_KB_MAX = 64
const DEFAULT_BUDGET_KB = 24
// Bytes reserved on every page for the envelope (coverage tally, receipts, gate,
// reading_contract, provenance, cursor, and — on the final page — the composition
// scaffold). Sized to the measured worst-case envelope so a page's serialized size
// never exceeds budget_kb * 1024 (C1 hard-cap honesty). runDossier additionally
// re-measures the assembled page and flags page_exceeds_budget_kb if this is ever
// insufficient (belt-and-braces — never silently over-budget).
const ENVELOPE_RESERVE_BYTES = 4096

const STATE_KEYS = [
  'served',
  'empty_for_this_chart',
  'not_computed_globally',
  'superseded_by_aggregate',
  'excluded_by_named_rule',
] as const
type StateKey = (typeof STATE_KEYS)[number]
const CODE_TO_STATE: Record<string, StateKey> = {
  S: 'served',
  E: 'empty_for_this_chart',
  N: 'not_computed_globally',
  A: 'superseded_by_aggregate',
  X: 'excluded_by_named_rule',
}

// ── Slice bundle shape (produced by the Ω5 generator; see dossier_slices/*.json) ──

interface SliceBlock {
  t: string // serving_tool
  ak: string // serving-arg key ('' = no arg, '@' = multi packed into v)
  s: string // state code
  v: string[] // arg values — one coverage unit each
  n: number[] // concept count per unit
  ci?: number[] // indices in v that are chain/pattern units (Ω6 first-class)
}
interface SliceBundle {
  artifact: string
  version: string
  domain: string
  chart_id: string
  chart8: string
  slice_size: number
  state_totals: Record<string, number>
  chain_pattern_units: number
  blocks_fingerprint: string
  blocks: SliceBlock[]
  generated_from?: Record<string, string>
}

// ── One coverage unit, flattened from a block for paging ──────────────────────

interface CoverageUnit {
  serving_tool: string
  serving_args: Record<string, unknown>
  state: StateKey
  concept_count: number
  is_chain_or_pattern: boolean
}

const bundleCache = new Map<string, SliceBundle | null>()

function chart8Of(chart_id: string): string {
  return chart_id.slice(0, 8)
}

function loadBundle(domain: string, chart_id: string): SliceBundle | null {
  const key = `${domain}_${chart8Of(chart_id)}`
  if (bundleCache.has(key)) return bundleCache.get(key) ?? null
  const raw = DOSSIER_SLICE_BUNDLES[key]
  const bundle = (raw as unknown as SliceBundle | undefined) ?? null
  bundleCache.set(key, bundle)
  return bundle
}

/**
 * Reconstruct one coverage unit (block bi, value index vi) with its resolved
 * serving_args (chart_id folded back in — the bundle stores it factored out).
 */
function unitAt(block: SliceBlock, vi: number, chart_id: string): CoverageUnit {
  const args: Record<string, unknown> = { chart_id }
  if (block.ak === '@') {
    // multi-arg packed as "k=v;k2=v2"
    for (const pair of block.v[vi]!.split(';')) {
      const eq = pair.indexOf('=')
      if (eq > 0) args[pair.slice(0, eq)] = pair.slice(eq + 1)
    }
  } else if (block.ak !== '') {
    args[block.ak] = block.v[vi]
  }
  return {
    serving_tool: block.t,
    serving_args: args,
    state: CODE_TO_STATE[block.s] ?? 'served',
    concept_count: block.n[vi]!,
    is_chain_or_pattern: (block.ci ?? []).includes(vi),
  }
}

/** Empty per-state tally. */
function emptyTally(): Record<StateKey, number> {
  return Object.fromEntries(STATE_KEYS.map((k) => [k, 0])) as Record<StateKey, number>
}

// ── The pure pager ────────────────────────────────────────────────────────────
//
// A "position" is (blockIdx, valueIdx) into the ordered block stream. Paging is
// deterministic given (bundle, budget_kb): starting from a position, we greedily
// emit as many coverage units as fit under (budget_kb*1024 - ENVELOPE_RESERVE),
// re-emitting the shared block header (t/ak/s) whenever we cross a block boundary
// or split a block across pages. Coverage is derived by replay, never trusted from
// the caller — the cursor carries only a position + a fingerprint.

/**
 * A page's served block chunk. DENSE by design (the ≤6-page density target forbids
 * per-unit objects): coverage units are parallel arrays, not an array of objects.
 *   serving_tool + serving_arg_key + state  — the shared drill handle + accounting state
 *   values[i]          — the serving_args value for unit i (fed to serving_tool)
 *   concept_counts[i]  — how many TCI concepts unit i accounts for
 *   chain_pattern_idx  — indices into values[] that are Ω6 chain/pattern structures
 * To hydrate real rows for unit i: call `serving_tool` with
 * { chart_id, [serving_arg_key]: values[i] } (or split "k=v;k2=v2" when serving_arg_key === '@').
 */
interface PagedBlockChunk {
  serving_tool: string
  serving_arg_key: string
  state: StateKey
  values: string[]
  concept_counts: number[]
  chain_pattern_idx?: number[]
}

interface PageResult {
  chunks: PagedBlockChunk[]
  page_tally: Record<StateKey, number>
  page_concepts: number
  chain_units_in_page: number
  endBi: number
  endVi: number
  done: boolean
  atomic_overflow: boolean // a single unit alone exceeded the cap (still emitted, flagged)
}

function chunkBytes(chunk: PagedBlockChunk): number {
  return Buffer.byteLength(JSON.stringify(chunk), 'utf8')
}

function packPage(
  bundle: SliceBundle,
  budgetKb: number,
  startBi: number,
  startVi: number,
): PageResult {
  const cap = budgetKb * 1024 - ENVELOPE_RESERVE_BYTES
  const chunks: PagedBlockChunk[] = []
  const tally = emptyTally()
  let pageBytes = 0
  let pageConcepts = 0
  let chainUnits = 0
  let atomicOverflow = false

  let bi = startBi
  let vi = startVi
  while (bi < bundle.blocks.length) {
    const block = bundle.blocks[bi]!
    const state = CODE_TO_STATE[block.s] ?? 'served'
    const chunk: PagedBlockChunk = {
      serving_tool: block.t,
      serving_arg_key: block.ak,
      state,
      values: [],
      concept_counts: [],
    }
    let chunkPushed = false
    while (vi < block.v.length) {
      const isChain = (block.ci ?? []).includes(vi)
      // Tentatively add unit vi to the current chunk.
      chunk.values.push(block.v[vi]!)
      chunk.concept_counts.push(block.n[vi]!)
      if (isChain) (chunk.chain_pattern_idx ??= []).push(chunk.values.length - 1)
      if (!chunkPushed) {
        chunks.push(chunk)
        chunkPushed = true
      }
      const prospective = chunks.reduce((s, c) => s + chunkBytes(c), 0)

      const pageHasContent = pageConcepts > 0
      if (prospective > cap && pageHasContent) {
        // Does not fit — roll the unit back and end the page at this position.
        chunk.values.pop()
        chunk.concept_counts.pop()
        if (isChain) chunk.chain_pattern_idx!.pop()
        if (chunk.values.length === 0) chunks.pop()
        return {
          chunks,
          page_tally: tally,
          page_concepts: pageConcepts,
          chain_units_in_page: chainUnits,
          endBi: bi,
          endVi: vi,
          done: false,
          atomic_overflow: atomicOverflow,
        }
      }
      if (prospective > cap && !pageHasContent) {
        // A single unit alone exceeds the whole cap — emit it anyway (never drop
        // coverage, B.10) and flag it, matching scan_fetch truncation honesty.
        atomicOverflow = true
      }
      // Commit.
      pageBytes = prospective
      tally[state] += block.n[vi]!
      pageConcepts += block.n[vi]!
      if (isChain) chainUnits += 1
      vi += 1
    }
    // block exhausted — advance to next block
    bi += 1
    vi = 0
  }
  return {
    chunks,
    page_tally: tally,
    page_concepts: pageConcepts,
    chain_units_in_page: chainUnits,
    endBi: bi,
    endVi: vi,
    done: true,
    atomic_overflow: atomicOverflow,
  }
}

/** Total pages for a bundle at a given budget (deterministic simulation). */
function countPages(bundle: SliceBundle, budgetKb: number): number {
  let pages = 0
  let bi = 0
  let vi = 0
  // safety bound: never more than one page per unit
  const maxPages = bundle.blocks.reduce((s, b) => s + b.v.length, 0) + 2
  while (true) {
    const r = packPage(bundle, budgetKb, bi, vi)
    pages += 1
    if (r.done || pages > maxPages) break
    bi = r.endBi
    vi = r.endVi
  }
  return pages
}

/** Coverage accumulated from position (0,0) up to (and excluding) position (bi,vi). */
function coverageBefore(
  bundle: SliceBundle,
  chart_id: string,
  bi: number,
  vi: number,
): { tally: Record<StateKey, number>; accounted: number; chain: number } {
  const tally = emptyTally()
  let accounted = 0
  let chain = 0
  for (let b = 0; b < bi && b < bundle.blocks.length; b += 1) {
    const block = bundle.blocks[b]!
    const state = CODE_TO_STATE[block.s] ?? 'served'
    for (let i = 0; i < block.v.length; i += 1) {
      tally[state] += block.n[i]!
      accounted += block.n[i]!
      if ((block.ci ?? []).includes(i)) chain += 1
    }
  }
  if (bi < bundle.blocks.length) {
    const block = bundle.blocks[bi]!
    const state = CODE_TO_STATE[block.s] ?? 'served'
    for (let i = 0; i < vi; i += 1) {
      tally[state] += block.n[i]!
      accounted += block.n[i]!
      if ((block.ci ?? []).includes(i)) chain += 1
    }
  }
  return { tally, accounted, chain }
}

// ── Cursor codec (C1: opaque base64) ──────────────────────────────────────────

interface Cursor {
  bi: number
  vi: number
  pn: number // page number this cursor points AT (1-based)
  fp: string // slice bundle fingerprint — detects a regenerated slice
  bk: number // budget_kb the cursor was minted under
}
function encodeCursor(c: Cursor): string {
  return Buffer.from(JSON.stringify(c), 'utf8').toString('base64')
}
function decodeCursor(s: string): Cursor | null {
  try {
    const c = JSON.parse(Buffer.from(s, 'base64').toString('utf8')) as Cursor
    if (typeof c.bi === 'number' && typeof c.vi === 'number' && typeof c.fp === 'string') return c
    return null
  } catch {
    return null
  }
}

// ── token → budget_kb sizing (the density-target harness) ─────────────────────

/**
 * Map a client's usable-context size (tokens) to a dossier `budget_kb` (C1: 1..64).
 * A client devotes ~1KB of page per 1600 tokens of context to a single dossier page
 * (≈ an eighth of a per-message slice), clamped to C1's 64KB ceiling. Empirically:
 *   25k-token client → budget_kb 16  (wealth/482012f1 → 6 pages)
 *   200k-token client → budget_kb 64 (wealth/482012f1 → 2 pages)
 */
export function budgetKbForClientTokens(tokens: number): number {
  return Math.max(BUDGET_KB_MIN, Math.min(BUDGET_KB_MAX, Math.round(tokens / 1600)))
}

// ── Composition scaffold (post-gate ONLY; deterministic, non-generative) ──────
//
// This is the ONLY interpretive-facing surface, and it is emitted by a code path
// that runs only when synthesis_gate === 'OPEN'. It carries NO generated prose and
// NO verdict — it is a deterministic instruction + the prioritized drill order
// (chain/pattern units first, then served, per Ω6), computed from the accounting
// alone. The synthesis itself is the consumer's job, over the whole slice.

function buildCompositionScaffold(bundle: SliceBundle): Record<string, unknown> {
  return {
    instruction:
      'Coverage is 100% accounted for this domain slice. You now hold the whole ' +
      'territory. Compose the synthesis over the WHOLE — not a narration of the parts. ' +
      'Ground every claim in the L1 fact_ids reachable via each unit\'s serving_tool + ' +
      'serving_args (B.3 derivation-ledger). Prioritise the chain/pattern structures ' +
      '(Ω6 first-class) before atomic facts.',
    drill_order: [
      'chain_or_pattern units (structures: dispositor chains, yoga clusters, mutual ' +
        'reception, argala/virodha webs, CGM subgraphs) — read the structure, not just its atoms',
      'served atomic units (confirmed, chart-specific data)',
      'empty_for_this_chart units (honest negatives — the absence is itself a finding)',
      'not_computed_globally units (known gaps — never silently omitted)',
    ],
    chain_pattern_unit_count: bundle.chain_pattern_units,
    honesty:
      'empty_for_this_chart and not_computed_globally are reported as data, never ' +
      'suppressed. A correct negative is a finding (§N.6).',
  }
}

// ── dualOutput (mirrors register_vidhi_plan.ts) ───────────────────────────────

const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000
function dualOutput(data: unknown, isError = false) {
  const structuredContent = { type: 'object' as const, object: data }
  const json = JSON.stringify(data)
  const content =
    Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES
      ? [{ type: 'text' as const, text: '[large payload — see structuredContent]' }]
      : [{ type: 'text' as const, text: json }]
  return isError
    ? { structuredContent, content, isError: true as const }
    : { structuredContent, content }
}

// ── The core paging function (pure; exported for the density harness/tests) ───

export interface DossierPage {
  ok: boolean
  tool: 'dossier'
  domain: string
  chart_id: string
  page_n: number
  pages_total: number
  cursor: string | null
  more_available: boolean
  budget_kb_applied: number
  budget_kb_requested?: number
  slice_size: number
  page_units: PagedBlockChunk[]
  page_concepts_accounted: number
  chain_units_in_page: number
  coverage_so_far: Record<StateKey, number> & {
    accounted: number
    slice_size: number
    pct: number
    chain_pattern_units_seen: number
  }
  synthesis_gate: 'BLOCKED' | 'OPEN'
  gate_reason: string
  reading_contract: string
  composition_scaffold?: Record<string, unknown>
  retrieval_receipts: Record<string, unknown>
  judgment_flags: string[]
  provenance: Record<string, unknown>
  page_bytes?: number
  error?: { class: string; message: string }
}

export interface DossierArgs {
  domain: string
  chart_id: string
  budget_kb?: number
  cursor?: string
  compose?: boolean
}

export function runDossier(args: DossierArgs): DossierPage {
  const { domain, chart_id } = args
  const requestedBudget = args.budget_kb
  // C1: clamp to [1,64]. A caller-supplied value above the ceiling is hard-capped.
  const budgetKb = Math.max(
    BUDGET_KB_MIN,
    Math.min(BUDGET_KB_MAX, requestedBudget ?? DEFAULT_BUDGET_KB),
  )

  const errBase = {
    ok: false as const,
    tool: 'dossier' as const,
    domain,
    chart_id,
    page_n: 0,
    pages_total: 0,
    cursor: null,
    more_available: false,
    budget_kb_applied: budgetKb,
    ...(requestedBudget !== undefined ? { budget_kb_requested: requestedBudget } : {}),
    slice_size: 0,
    page_units: [],
    page_concepts_accounted: 0,
    chain_units_in_page: 0,
    coverage_so_far: {
      ...emptyTally(),
      accounted: 0,
      slice_size: 0,
      pct: 0,
      chain_pattern_units_seen: 0,
    },
    synthesis_gate: 'BLOCKED' as const,
    gate_reason: '',
    reading_contract: '',
    judgment_flags: [] as string[],
    retrieval_receipts: {},
    provenance: {},
  }

  const bundle = loadBundle(domain, chart_id)
  if (!bundle) {
    return {
      ...errBase,
      gate_reason: 'slice_not_precomputed',
      error: {
        class: 'slice_not_available',
        message:
          `No pre-compiled dossier slice for (domain=${domain}, chart=${chart8Of(chart_id)}). ` +
          'The Ω5 engine pages the committed slice bundles under resources/vidhi/dossier_slices/. ' +
          'Flagship coverage: {wealth, career} × {482012f1, 1c826d5a}. Generating a slice for an ' +
          'arbitrary (domain, chart) requires the Ω3 completeness-accounting census (cross-lane).',
      },
    }
  }

  // Resolve start position from cursor (or page 1).
  let startBi = 0
  let startVi = 0
  let pageN = 1
  const flags: string[] = []
  if (args.cursor) {
    const c = decodeCursor(args.cursor)
    if (!c) {
      return { ...errBase, slice_size: bundle.slice_size, gate_reason: 'bad_cursor', error: { class: 'bad_cursor', message: 'cursor did not decode' } }
    }
    if (c.fp !== bundle.blocks_fingerprint) {
      // Slice regenerated under this cursor — restart honestly rather than mis-page.
      flags.push('cursor_slice_changed_restarted')
      startBi = 0
      startVi = 0
      pageN = 1
    } else {
      startBi = c.bi
      startVi = c.vi
      pageN = c.pn
    }
    if (c.bk !== budgetKb && c.fp === bundle.blocks_fingerprint) {
      flags.push('budget_kb_changed_mid_page')
    }
  }

  const pagesTotal = countPages(bundle, budgetKb)
  const page = packPage(bundle, budgetKb, startBi, startVi)

  const before = coverageBefore(bundle, chart_id, startBi, startVi)
  const accounted = before.accounted + page.page_concepts
  const tally = emptyTally()
  for (const k of STATE_KEYS) tally[k] = before.tally[k] + page.page_tally[k]
  const chainSeen = before.chain + page.chain_units_in_page

  const gateOpen = page.done && accounted === bundle.slice_size
  const nextCursor = page.done
    ? null
    : encodeCursor({ bi: page.endBi, vi: page.endVi, pn: pageN + 1, fp: bundle.blocks_fingerprint, bk: budgetKb })

  if (page.atomic_overflow) flags.push('atomic_unit_exceeds_budget_kb')
  if (!gateOpen && args.compose) flags.push('composed_before_gate')

  // retrieval_receipts (charter Ω5): the consumption record. Persisting it to the
  // server-side retrieval_receipts table needs the shared receipts writer (α / lib) —
  // not in this lane's manifest — so it is emitted IN the response and flagged
  // in_response_only. composed_before_gate is recorded whenever a caller signals a
  // compose intent while the gate is still BLOCKED (feeds Lane K2 grading).
  const receipt = {
    receipt_id: `${domain}:${bundle.chart8}:p${pageN}:bk${budgetKb}`,
    domain,
    chart_id,
    page_n: pageN,
    pages_total: pagesTotal,
    budget_kb_applied: budgetKb,
    accounted_so_far: accounted,
    slice_size: bundle.slice_size,
    gate: gateOpen ? 'OPEN' : 'BLOCKED',
    served_units_this_page: page.chunks.reduce((s, c) => s + c.values.length, 0),
    composed_before_gate: Boolean(!gateOpen && args.compose),
    persistence: 'in_response_only',
    persistence_note:
      'Server-side persistence to retrieval_receipts requires the shared receipts ' +
      'writer (cross-lane, blocked-on-α); this receipt is authoritative but transient.',
  }

  const readingContract = gateOpen
    ? 'synthesis_gate: OPEN — 100% of this domain slice is accounted. Compose the ' +
      'synthesis over the WHOLE slice now (see composition_scaffold). The deliverable is ' +
      'the synthesis, not a narration of the parts.'
    : `synthesis_gate: BLOCKED — ${accounted}/${bundle.slice_size} concepts accounted ` +
      `(${((accounted / bundle.slice_size) * 100).toFixed(1)}%). Do NOT compose yet. Page ` +
      'through the remaining units (follow `cursor`) until the gate reads OPEN. This page ' +
      'carries data + accounting ONLY — the interpretive surfaces are withheld by construction.'

  const out: DossierPage = {
    ok: true,
    tool: 'dossier',
    domain,
    chart_id,
    page_n: pageN,
    pages_total: pagesTotal,
    cursor: nextCursor,
    more_available: !page.done,
    budget_kb_applied: budgetKb,
    ...(requestedBudget !== undefined ? { budget_kb_requested: requestedBudget } : {}),
    slice_size: bundle.slice_size,
    page_units: page.chunks,
    page_concepts_accounted: page.page_concepts,
    chain_units_in_page: page.chain_units_in_page,
    coverage_so_far: {
      ...tally,
      accounted,
      slice_size: bundle.slice_size,
      pct: Number(((accounted / bundle.slice_size) * 100).toFixed(2)),
      chain_pattern_units_seen: chainSeen,
    },
    synthesis_gate: gateOpen ? 'OPEN' : 'BLOCKED',
    gate_reason: gateOpen
      ? 'coverage_100pct'
      : `coverage_${((accounted / bundle.slice_size) * 100).toFixed(1)}pct_incomplete`,
    reading_contract: readingContract,
    // STRUCTURAL GATE: composition_scaffold exists on the object ONLY when OPEN.
    ...(gateOpen ? { composition_scaffold: buildCompositionScaffold(bundle) } : {}),
    retrieval_receipts: receipt,
    judgment_flags: flags,
    provenance: {
      slice_bundle: `${domain}_${bundle.chart8}.json`,
      blocks_fingerprint: bundle.blocks_fingerprint,
      generated_from: bundle.generated_from ?? {},
      density_note:
        'Units carry serving_tool + serving_args as live drill handles (call them to ' +
        'hydrate real rows — no computation reimplemented here, B.10). Auto-hydration over ' +
        'HTTP needs the tool-name→capability-URI resolver (cross-lane, blocked-on-α).',
      contract_refs: ['C1 (budget_kb + paging)', 'C7 (completeness accounting)', 'C8 (honesty fields)'],
    },
  }

  // C1 hard-cap honesty: re-measure the ASSEMBLED page. If the reserve was ever
  // insufficient, flag it truthfully (never silently over-budget) rather than
  // dropping coverage to fit.
  const pageBytes = Buffer.byteLength(JSON.stringify(out), 'utf8')
  out.page_bytes = pageBytes
  if (pageBytes > budgetKb * 1024) {
    out.judgment_flags = [...out.judgment_flags, 'page_exceeds_budget_kb']
  }
  return out
}

// ── MCP registration ──────────────────────────────────────────────────────────

export function registerDossierTool(server: McpServer, principal: Principal): void {
  server.tool(
    'dossier',
    // Elevation α: the description leads with the naive-caller intent ("how is my wealth", a
    // COMPLETE reading) so an uninstructed agent browsing the raw MCP tool catalog — the surface
    // through which it found assess_wealth — sees dossier as the obvious tool for a full-domain
    // question, not an unfamiliar specialist. This is the discoverability half (option (a)) of the
    // flagship completeness fix; assess_wealth/assess_career also now carry dossier's accounting
    // inline (domain_completeness) so the routing works even if this tool is never chosen.
    'COMPLETE domain reading — the tool for "how is my wealth?", "assess my career fully", or any ' +
      'question wanting the WHOLE picture of a life domain, not a headline. Where assess_wealth / ' +
      'assess_career give a reconciled summary, `dossier` serves the ENTIRE domain concept slice ' +
      '(every wealth/career concept the chart carries — thousands of them) with 100% completeness ' +
      'accounting. Ω5 gather-then-compose paging engine (Elevation Campaign v2.1). Serves a ' +
      'domain\'s ENTIRE concept slice for a chart in budget-capped PAGES, and structurally WITHHOLDS ' +
      'every interpretive surface until coverage reaches 100% accounting. Each page carries ' +
      'data + accounting only: coverage UNITS (each naming its live serving_tool + ' +
      'serving_args drill handle and its accounting state), a running coverage_so_far tally ' +
      'over the five accounting states, and synthesis_gate (BLOCKED until 100%, then OPEN). ' +
      'The composition_scaffold — the only interpretive-facing surface — appears ONLY once ' +
      'the gate is OPEN. Follow `cursor` to page through the whole slice before composing. ' +
      'Flagship slices: {wealth, career} × the two canonical charts. `domain` is REQUIRED — ' +
      'enum "wealth" | "career" (MC-011: the only two domains with pre-compiled slices). ' +
      'budget_kb (1..64, C1) sizes the page to the client; 16 ≈ a 25k-token client, ' +
      '64 ≈ a 200k-token client.',
    {
      // MC-011 (ŚODHANA T8): domain was z.string() with no enum, so an omitted domain
      // surfaced only a raw zod message ("Required, received undefined") with no guidance
      // on what a valid value looks like. z.enum() both documents the two currently
      // pre-compiled slice domains up front AND gives a self-describing validation error
      // ("Invalid enum value. Expected 'wealth' | 'career' ...") if an unsupported domain is
      // passed. Schema-only change — does not touch runDossier's gate/receipt logic.
      domain: z
        .enum(['wealth', 'career'])
        .describe('REQUIRED. Domain slice to page. Valid values: "wealth", "career" (the only ' +
          'domains with pre-compiled dossier slices today — flagship coverage).'),
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      budget_kb: z
        .number()
        .min(BUDGET_KB_MIN)
        .max(BUDGET_KB_MAX)
        .optional()
        .describe('Per-page byte budget in KB (C1: 1..64). Omit for the default. A value above ' +
          'the ceiling is hard-capped. ~16 ≈ a 25k-token client (≤6 pages for wealth); 64 ≈ a ' +
          '200k-token client (≤2 pages).'),
      cursor: z.string().optional().describe('Opaque cursor from the previous page. Omit for page 1.'),
      compose: z
        .boolean()
        .optional()
        .describe('Signal that you intend to compose now. If coverage is < 100%, this is ' +
          'recorded as composed_before_gate in retrieval_receipts (and interpretive surfaces ' +
          'remain withheld). Leave false until synthesis_gate reads OPEN.'),
    },
    async (args) => {
      const authorized = await remoteAuthorize(principal, args.chart_id)
      if (!authorized) {
        return dualOutput(
          {
            ok: false,
            tool: 'dossier',
            error: {
              class: 'entitlement_denied',
              message: 'AUTHZ_DENIED: not authorized to access this chart',
            },
            chart_id: args.chart_id,
          },
          true,
        )
      }
      try {
        const page = runDossier({
          domain: args.domain,
          chart_id: args.chart_id,
          budget_kb: args.budget_kb,
          cursor: args.cursor,
          compose: args.compose,
        })
        return dualOutput(page, !page.ok)
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err)
        return dualOutput(
          { ok: false, tool: 'dossier', error: { class: 'paging_error', message } },
          true,
        )
      }
    },
  )
}
