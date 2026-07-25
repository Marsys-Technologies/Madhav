#!/usr/bin/env tsx
/**
 * receipt_gate.ts — Elevation Campaign, Stream α (SATYA), Lane K1, Task 3 (batch 2).
 *
 * Targets the class of MCP tool that accepts a caller-supplied `categories[]` (or other
 * fixed-catalog multi-select) param and is expected to answer HONESTLY per-category — no
 * category silently vanishing from the response, and no category's status/count claim
 * disagreeing with what was actually served. Runs the two existing structural walkers from
 * `_structural_checks.ts` (`findEmptyOverConfirmedViolations`, `findCountArrayMismatches`)
 * over each such tool's response.
 *
 * ── Static discovery (mechanical, not hand-maintained) ──────────────────────────────────
 * `scanForMultiCategoryParams()` greps `platform-mcp/src/tools/**` source for
 * `<param>: z.array(z.enum(...))` param declarations (the shape every real multi-category
 * selector in this codebase uses) and best-effort-associates each hit with the tool it
 * belongs to via nearest-preceding (falling back to nearest-following) `server.tool(<name>`
 * / `regAlias(server, <name>` registration in the same file — the same registration-site
 * regex vocabulary `_tool_enumeration.ts`'s `collectRegisteredTools()` already uses.
 *
 * A batch-1 investigation (documented in the K1 task brief) manually confirmed three real
 * hits: `ganita_positions_get.categories`, `ganita_special_lagnas_get.categories`, and
 * `prashna_ask.scope_tuple.domains`. This run's static re-scan (see PLAN-mode output below)
 * reconfirms all three are still live AND surfaces a fourth the manual pass did not call
 * out: `graha_portrait.include` — a `z.array(z.enum([...]))` param selecting report
 * sections (position/dignity/functional_nature/strength/avasthas/special_states/yogas/
 * dashas/cgm_neighborhood). It does not build a `category_receipts`-shaped field the way
 * the EL-41/B-1 pair does, but it is a genuine fixed-catalog multi-select whose response can
 * still exhibit an empty-over-confirmed or count/array mismatch, so it is included as a
 * fourth live target. Two more `z.array(...)` hits were found and DELIBERATELY EXCLUDED —
 * `register_vidhi_plan.ts`'s `domains: z.array(z.string()).optional()` and
 * `graha_portrait`'s own `operative_vargas: z.array(z.string()).optional()` — both are
 * free-form string arrays with no fixed enum catalog behind them, so there is no
 * "which of my known categories are missing" question to ask of their response; they are
 * still reported as SKIPPED-WITH-REASON rows below rather than silently dropped (B.10).
 *
 * ── C7 include-point ─────────────────────────────────────────────────────────────────────
 * See `runC7AccountingInvariant()` below — a deliberate no-op. Checked
 * `~/elev-v2-shared/contracts/CONTRACT_STATUS.md` at write time (2026-07-25): **C7's
 * contract TEXT is now FROZEN** (`C7_ACCOUNTING_INVARIANT_v1_0.md`, γ-owned, landed ~T0+4h,
 * PROXY-RULED-002) — a change from the K1 brief's "still DRAFT" assumption. However the
 * contract's OWN freeze condition for actually turning the gate on
 * (`contracts/C7.frozen`, a sentinel file written only once γ's TCI generator has produced a
 * real DB-derived Total Concept Inventory for a canonical chart AND the accounting-row
 * generator has passed for `wealth` end-to-end AND the independent Verifier's Ω1 sanity gate
 * has passed — see the contract's "Freeze condition" section) has NOT been met: neither
 * `contracts/C7.frozen` nor any of `TOTAL_CONCEPT_INVENTORY_v1_0.json` /
 * `DOMAIN_RELEVANCE_MAP_v1_0.json` / `ledgers/contracts/C7_ENFORCED_SCOPE.json` exist yet in
 * `~/elev-v2-shared` as of this check. Per the contract's own text, "The gate as a whole is
 * warn-only in its entirety until contracts/C7.frozen exists" — so there is nothing correct
 * to assert yet regardless of the contract-text freeze. This file therefore still leaves the
 * hook as a no-op per the K1 task instruction, but the hook body now documents exactly what
 * unblocks it, for whoever picks this up next.
 *
 * Two modes: PLAN (no MCP_SERVER_URL — static scan + call-plan only, exit 0) / LIVE.
 *
 * Run (plan mode, from `platform/`):
 *   npx tsx scripts/census/elev_gates/receipt_gate.ts
 * Run (live mode, from `platform/`):
 *   MCP_SERVER_URL=https://<mcp-host>/mcp MCP_BEARER=<token> \
 *     npx tsx scripts/census/elev_gates/receipt_gate.ts
 */
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { listToolSourceFiles } from './_tool_enumeration'
import { ElevMcpClient, resolveMcpTarget, unwrapToolPayload, CANONICAL_CHART_ID, envOrDefault, DEFAULT_TOOL_TIMEOUT_MS } from './_mcp_client'
import { findEmptyOverConfirmedViolations, findCountArrayMismatches, type StructuralViolation } from './_structural_checks'
import { printGateReport, type GateResult } from './_report'

const AYANAMSHA_ID = 'lahiri_chitrapaksha'
const TOOL_TIMEOUT_MS = Number(envOrDefault('RECEIPT_TOOL_TIMEOUT_MS', String(DEFAULT_TOOL_TIMEOUT_MS)))
const MIN_GAP_MS = Number(envOrDefault('RECEIPT_MIN_GAP_MS', '300'))
// prashna_ask is job-handle-first (register_prashna_ask.ts header) — the synchronous
// tools/call response is only {job_id, status:'pending'}, never the receipt payload itself.
// This gate polls prashna_status for the real answer within a bounded budget rather than
// structurally-checking the meaningless job-handle shape.
const PRASHNA_POLL_ATTEMPTS = Number(envOrDefault('RECEIPT_PRASHNA_POLL_ATTEMPTS', '5'))
const PRASHNA_POLL_GAP_MS = Number(envOrDefault('RECEIPT_PRASHNA_POLL_GAP_MS', '2000'))

async function sleep(ms: number): Promise<void> {
  await new Promise((r) => setTimeout(r, ms))
}

// ─────────────────────────────────────────────────────────────────────────────
// Static discovery
// ─────────────────────────────────────────────────────────────────────────────

export type MultiCategoryHit = {
  tool_name: string | null
  param_name: string
  enum_values: string[] | 'free_form_string_array' | 'unresolved_identifier'
  source_file: string
  association: 'preceding_registration' | 'following_registration' | 'file_single_tool' | 'unresolved'
}

// Same three registration-site shapes _tool_enumeration.ts's collectRegisteredTools() greps
// for, but here we need each match's POSITION (index) in the file too, to associate it with
// the nearest array-param declaration — collectRegisteredTools() only returns names.
function findRegistrationSites(src: string): Array<{ name: string; index: number }> {
  const sites: Array<{ name: string; index: number }> = []
  for (const m of src.matchAll(/server\.tool\(\s*['"]([a-zA-Z0-9_]+)['"]/g)) sites.push({ name: m[1]!, index: m.index! })
  for (const m of src.matchAll(/\b(?:regAlias|globalAlias)\(\s*server,\s*['"]([a-zA-Z0-9_]+)['"]/g)) sites.push({ name: m[1]!, index: m.index! })
  if (/server\.tool\(\s*TOOL_NAME\s*,/.test(src)) {
    const nameMatch = src.match(/const TOOL_NAME\s*=\s*['"]([a-zA-Z0-9_]+)['"]/)
    const callMatch = src.match(/server\.tool\(\s*TOOL_NAME\s*,/)
    if (nameMatch && callMatch) sites.push({ name: nameMatch[1]!, index: callMatch.index! })
  }
  sites.sort((a, b) => a.index - b.index)
  return sites
}

function parseArrayLiteral(literalBody: string): string[] {
  return literalBody
    .split(',')
    .map((s) => s.trim().replace(/^['"]|['"]$/g, ''))
    .filter((s) => s.length > 0)
}

function findConstArrayDecl(src: string, id: string): string[] | null {
  const declRe = new RegExp(`const\\s+${id}\\s*=\\s*\\[([^\\]]*)\\]`)
  const m = src.match(declRe)
  return m ? parseArrayLiteral(m[1]!) : null
}

/** Resolves an z.enum(...) argument to its literal string values. Handles three shapes:
 *  (1) an inline array literal `[...]`; (2) a same-file `const ID = [...] as const`;
 *  (3) an identifier imported from a sibling file (`import { ID } from './other.js'`) —
 *  followed one hop, mirroring how register_prashna_ask.ts actually sources DOMAINS from
 *  intent_scope_classifier.ts. Two hops or a non-relative import are reported unresolved
 *  rather than guessed at. */
function resolveEnumValues(src: string, enumArg: string, filePath: string): string[] | 'unresolved_identifier' {
  const literal = enumArg.match(/^\[([^\]]*)\]$/)
  if (literal) return parseArrayLiteral(literal[1]!)
  const idMatch = enumArg.trim().match(/^([a-zA-Z0-9_]+)$/)
  if (!idMatch) return 'unresolved_identifier'
  const id = idMatch[1]!
  const sameFile = findConstArrayDecl(src, id)
  if (sameFile) return sameFile
  const importRe = new RegExp(`import\\s*\\{[^}]*\\b${id}\\b[^}]*\\}\\s*from\\s*['"](\\.[^'"]+)['"]`)
  const importMatch = src.match(importRe)
  if (!importMatch) return 'unresolved_identifier'
  const importPath = importMatch[1]!.replace(/\.js$/, '.ts')
  const resolved = path.join(path.dirname(filePath), importPath)
  try {
    const importedSrc = readFileSync(resolved, 'utf-8')
    const found = findConstArrayDecl(importedSrc, id)
    return found ?? 'unresolved_identifier'
  } catch {
    return 'unresolved_identifier'
  }
}

function associate(sites: Array<{ name: string; index: number }>, matchIndex: number): { name: string | null; association: MultiCategoryHit['association'] } {
  const preceding = [...sites].reverse().find((s) => s.index <= matchIndex)
  if (preceding) return { name: preceding.name, association: 'preceding_registration' }
  const following = sites.find((s) => s.index > matchIndex)
  if (following) return { name: following.name, association: 'following_registration' }
  if (sites.length === 1) return { name: sites[0]!.name, association: 'file_single_tool' }
  return { name: null, association: 'unresolved' }
}

/** Mechanical re-scan of platform-mcp/src/tools/** for every multi-select array param
 *  (`z.array(z.enum(...))` — fixed catalog, receipt-testable) and, separately, every
 *  free-form `z.array(z.string())` param named `categories`/`domains` (excluded from live
 *  checks but reported so a caller can see they were considered, not missed). */
export function scanForMultiCategoryParams(): MultiCategoryHit[] {
  const hits: MultiCategoryHit[] = []
  for (const file of listToolSourceFiles()) {
    const src = readFileSync(file, 'utf-8')
    const sites = findRegistrationSites(src)
    for (const m of src.matchAll(/\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*z\.array\(\s*z\.enum\(\s*(\[[^\]]*\]|[a-zA-Z0-9_]+)\s*\)/g)) {
      const paramName = m[1]!
      const enumArg = m[2]!
      const { name, association } = associate(sites, m.index!)
      hits.push({ tool_name: name, param_name: paramName, enum_values: resolveEnumValues(src, enumArg, file), source_file: file, association })
    }
    for (const m of src.matchAll(/\b(categories|domains)\s*:\s*z\.array\(\s*z\.string\(\)\s*\)/g)) {
      const { name, association } = associate(sites, m.index!)
      hits.push({ tool_name: name, param_name: m[1]!, enum_values: 'free_form_string_array', source_file: file, association })
    }
  }
  // Dedupe: the same (tool, param, source_file) can appear twice when a schema is declared
  // once as a shared const (e.g. ScopeTupleSchema) and again inline in a second tool's schema
  // literal in the same file — real, distinct source locations, but not worth two report rows
  // when they resolve to the same tool/param/value-set.
  const seen = new Set<string>()
  return hits.filter((h) => {
    const key = `${h.tool_name}::${h.param_name}::${h.source_file}::${JSON.stringify(h.enum_values)}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

// ─────────────────────────────────────────────────────────────────────────────
// LIVE call plan — per-tool arg shaping for the confirmed fixed-catalog hits.
// Generic fallback (flat {chart_id, ayanamsha_id, [param]: enum_values}) covers any NEW
// fixed-catalog hit the scan above finds that isn't one of these four known shapes.
// ─────────────────────────────────────────────────────────────────────────────

type CallPlan = { args: Record<string, unknown>; note: string }

function buildCallPlan(hit: MultiCategoryHit): CallPlan | null {
  if (hit.enum_values === 'free_form_string_array' || hit.enum_values === 'unresolved_identifier') return null
  const values = hit.enum_values
  if (hit.tool_name === 'graha_portrait') {
    return {
      args: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, graha: 'Saturn', [hit.param_name]: values },
      note: 'graha_portrait requires graha — using Saturn as a representative body.',
    }
  }
  if (hit.tool_name === 'prashna_ask') {
    // Handled specially by runPrashnaAskCheck() below (job-handle + poll) — never dispatched
    // through the generic flat-arg path because `domains` is nested under `scope_tuple`.
    return null
  }
  return {
    args: { chart_id: CANONICAL_CHART_ID, ayanamsha_id: AYANAMSHA_ID, [hit.param_name]: values },
    note: 'generic flat-arg call plan (chart_id + ayanamsha_id + the multi-category param).',
  }
}

function violationsToDetail(violations: StructuralViolation[]): string {
  return violations.map((v) => `${v.path}: ${v.reason}`).join(' | ')
}

async function runStructuralChecksLive(client: ElevMcpClient, toolName: string, args: Record<string, unknown>, idPrefix: string, results: GateResult[]): Promise<void> {
  const outcome = await client.callTool(toolName, args)
  if (outcome.timed_out || outcome.status >= 500 || outcome.status === 0) {
    results.push({
      id: `${idPrefix}:${toolName}`,
      title: `${toolName} — could not measure (call failed)`,
      status: 'QUARANTINED',
      detail: `status=${outcome.status}, timed_out=${outcome.timed_out}, error=${outcome.error ?? 'n/a'} — a smoke-gate-class failure, not a receipt violation; see smoke_gate.ts.`,
    })
    return
  }
  const { payload, isToolError } = unwrapToolPayload(outcome)
  if (isToolError) {
    results.push({
      id: `${idPrefix}:${toolName}`,
      title: `${toolName} — tool-level error, receipt not meaningful`,
      status: 'QUARANTINED',
      detail: `Tool returned an in-band error for this call plan: ${JSON.stringify(payload).slice(0, 300)}`,
    })
    return
  }
  const emptyOverConfirmed = findEmptyOverConfirmedViolations(payload)
  const countMismatches = findCountArrayMismatches(payload)
  const allViolations = [...emptyOverConfirmed, ...countMismatches]
  results.push({
    id: `${idPrefix}:${toolName}`,
    title: `${toolName} — ${allViolations.length} structural violation(s) (${emptyOverConfirmed.length} empty-over-confirmed, ${countMismatches.length} count/array mismatch)`,
    status: allViolations.length === 0 ? 'PASS' : 'FAIL',
    detail: allViolations.length === 0 ? 'No empty-over-confirmed or count/array-mismatch violations found in this response.' : violationsToDetail(allViolations),
  })
}

/** prashna_ask: dispatch → poll prashna_status → structural-check the resolved payload. */
async function runPrashnaAskCheck(client: ElevMcpClient, domainsValues: string[], results: GateResult[]): Promise<void> {
  const askArgs = {
    chart_id: CANONICAL_CHART_ID,
    question: 'What does my chart say about these domains?',
    scope_tuple: {
      intent: 'domain_assessment',
      domains: domainsValues,
      width: 'standard',
      depth: 'standard',
      horizon: 'present',
      intervention: 'none',
      entitlement: 'native',
    },
    response_format: 'v3',
  }
  const askOutcome = await client.callTool('prashna_ask', askArgs)
  if (askOutcome.timed_out || askOutcome.status >= 500 || askOutcome.status === 0) {
    results.push({
      id: 'receipt:prashna_ask',
      title: 'prashna_ask — dispatch call failed',
      status: 'QUARANTINED',
      detail: `status=${askOutcome.status}, timed_out=${askOutcome.timed_out}, error=${askOutcome.error ?? 'n/a'} — smoke-gate-class failure, not a receipt violation.`,
    })
    return
  }
  const { payload: askPayload, isToolError: askIsError } = unwrapToolPayload(askOutcome)
  if (askIsError) {
    results.push({
      id: 'receipt:prashna_ask',
      title: 'prashna_ask — dispatch returned in-band error',
      status: 'QUARANTINED',
      detail: `${JSON.stringify(askPayload).slice(0, 300)}`,
    })
    return
  }
  const jobId = (askPayload as Record<string, unknown> | null)?.['job_id']
  if (typeof jobId !== 'string' || jobId.length === 0) {
    results.push({
      id: 'receipt:prashna_ask',
      title: 'prashna_ask — no job_id in dispatch response',
      status: 'FAIL',
      detail: `Expected {job_id, status:'pending'} per register_prashna_ask.ts's own contract; got: ${JSON.stringify(askPayload).slice(0, 300)}`,
    })
    return
  }
  for (let attempt = 1; attempt <= PRASHNA_POLL_ATTEMPTS; attempt++) {
    await sleep(PRASHNA_POLL_GAP_MS)
    const statusOutcome = await client.callTool('prashna_status', { job_id: jobId })
    if (statusOutcome.timed_out || statusOutcome.status >= 500 || statusOutcome.status === 0) continue
    const { payload: statusPayload, isToolError: statusIsError } = unwrapToolPayload(statusOutcome)
    if (statusIsError) continue
    const status = (statusPayload as Record<string, unknown> | null)?.['status']
    if (status === 'complete') {
      const violations = [...findEmptyOverConfirmedViolations(statusPayload), ...findCountArrayMismatches(statusPayload)]
      results.push({
        id: 'receipt:prashna_ask',
        title: `prashna_ask (via job ${jobId}, resolved after ${attempt} poll(s)) — ${violations.length} structural violation(s)`,
        status: violations.length === 0 ? 'PASS' : 'FAIL',
        detail: violations.length === 0 ? 'No violations found in the resolved v3-enveloped reading.' : violationsToDetail(violations),
      })
      return
    }
    if (status === 'failed') {
      results.push({
        id: 'receipt:prashna_ask',
        title: `prashna_ask (via job ${jobId}) — job reported status='failed'`,
        status: 'QUARANTINED',
        detail: `${JSON.stringify(statusPayload).slice(0, 300)} — an engine-side failure, not a receipt-structure violation.`,
      })
      return
    }
    // still pending/running — keep polling.
  }
  results.push({
    id: 'receipt:prashna_ask',
    title: `prashna_ask (via job ${jobId}) — did not resolve within poll budget`,
    status: 'QUARANTINED',
    detail: `Job still not complete/failed after ${PRASHNA_POLL_ATTEMPTS} polls at ${PRASHNA_POLL_GAP_MS}ms — async job-handle design (register_prashna_ask.ts header) makes this an expected slow-path outcome under CI time pressure, not a structural violation. Raise RECEIPT_PRASHNA_POLL_ATTEMPTS/RECEIPT_PRASHNA_POLL_GAP_MS to widen the budget.`,
  })
}

// ─────────────────────────────────────────────────────────────────────────────
// C7 include-point (deliberate no-op — see header comment for why)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * NO-OP HOOK. When `~/elev-v2-shared/contracts/C7.frozen` exists (see this file's header
 * comment for the exact freeze condition, per `C7_ACCOUNTING_INVARIANT_v1_0.md`'s own
 * "Freeze condition" section) AND `ledgers/contracts/C7_ENFORCED_SCOPE.json` lists at least
 * one `{tool, domain}` pair, this function is where the 100%-accounting assertion goes:
 * build a `ConceptAccountingRow[]` for `(CANONICAL_CHART_ID, domain)` from the TCI × domain
 * relevance map, assert `rows.length === slice_size` and `unaccounted.length === 0` per the
 * contract's frozen `PASS(...)` definition, and push a PASS/FAIL GateResult gated by whether
 * `(tool, domain)` is inside C7_ENFORCED_SCOPE.json (report-only outside the allowlist, per
 * the contract's Scope section). Left unimplemented deliberately — see header.
 */
function runC7AccountingInvariant(results: GateResult[]): void {
  results.push({
    id: 'receipt:c7-include-point',
    title: 'C7 accounting invariant — NO-OP (include-point only)',
    status: 'SKIPPED',
    detail:
      "Contract TEXT is FROZEN (C7_ACCOUNTING_INVARIANT_v1_0.md, checked at write time) but the contract's OWN gating sentinel " +
      "(contracts/C7.frozen) and its inputs (TOTAL_CONCEPT_INVENTORY_v1_0.json, DOMAIN_RELEVANCE_MAP_v1_0.json, " +
      "ledgers/contracts/C7_ENFORCED_SCOPE.json) do not exist yet in ~/elev-v2-shared — per the contract's own text this keeps the " +
      'whole gate warn-only campaign-wide. See runC7AccountingInvariant()\'s doc-comment for exactly what unblocks this.',
  })
}

// ─────────────────────────────────────────────────────────────────────────────
// main
// ─────────────────────────────────────────────────────────────────────────────

const KNOWN_CATEGORY_TOOLS = ['ganita_positions_get', 'ganita_special_lagnas_get', 'prashna_ask'] as const

async function main(): Promise<void> {
  const hits = scanForMultiCategoryParams()
  const results: GateResult[] = []

  // Drift check: every previously-confirmed hit must still be found by this run's re-scan.
  for (const known of KNOWN_CATEGORY_TOOLS) {
    const found = hits.some((h) => h.tool_name === known)
    results.push({
      id: `receipt:known-hit:${known}`,
      title: `Known multi-category tool '${known}' — ${found ? 'still found' : 'NO LONGER FOUND'} by static re-scan`,
      status: found ? 'PASS' : 'FAIL',
      detail: found
        ? `Static scan confirms ${known} still declares a categories[]/domains[] fixed-catalog param.`
        : `${known} was manually confirmed in the batch-1 pass but this run's re-scan of platform-mcp/src/tools/** no longer finds it — either the param was renamed/removed, or the association heuristic failed (check source_files below for manual investigation).`,
    })
  }

  const fixedCatalogHits = hits.filter((h) => h.enum_values !== 'free_form_string_array' && h.enum_values !== 'unresolved_identifier')
  const excludedHits = hits.filter((h) => h.enum_values === 'free_form_string_array' || h.enum_values === 'unresolved_identifier')

  for (const hit of excludedHits) {
    results.push({
      id: `receipt-scan:excluded:${hit.tool_name ?? 'unresolved'}:${hit.param_name}`,
      title: `${hit.tool_name ?? '(unresolved tool)'}.${hit.param_name} — excluded (${hit.enum_values})`,
      status: 'SKIPPED',
      detail: `${hit.source_file.split('/platform-mcp/')[1]} — ${hit.enum_values === 'free_form_string_array' ? 'free-form string array, no fixed catalog to check receipts against' : 'z.enum() identifier reference could not be resolved to a literal value list by this static scanner'}.`,
    })
  }

  const target = resolveMcpTarget()
  if (!target) {
    for (const hit of fixedCatalogHits) {
      const plan = hit.tool_name === 'prashna_ask' ? { args: 'special-cased poll flow, see runPrashnaAskCheck()', note: '' } : buildCallPlan(hit)
      results.push({
        id: `receipt-plan:${hit.tool_name ?? 'unresolved'}:${hit.param_name}`,
        title: `Call plan: ${hit.tool_name ?? '(unresolved — ' + hit.association + ')'}.${hit.param_name} = ${JSON.stringify(hit.enum_values)}`,
        status: 'SKIPPED',
        detail: `PLAN mode — no MCP_SERVER_URL set, no live call executed. Source: ${hit.source_file.split('/platform-mcp/')[1]}. ${plan ? JSON.stringify(plan) : 'no call plan (see notes)'}`,
      })
    }
    runC7AccountingInvariant(results)
    const reason = 'MCP_SERVER_URL not set — running in PLAN mode only (static scan + drift check verified, no live receipt measurement).'
    process.exit(printGateReport('receipt_gate (PLAN mode)', results, reason))
    return
  }

  const client = new ElevMcpClient(target.baseUrl, target.bearer, TOOL_TIMEOUT_MS)
  await client.init()

  for (const hit of fixedCatalogHits) {
    if (hit.tool_name === 'prashna_ask') {
      await runPrashnaAskCheck(client, (hit.enum_values as string[]) ?? ['career', 'wealth'], results)
      await sleep(MIN_GAP_MS)
      continue
    }
    const plan = buildCallPlan(hit)
    if (!plan || !hit.tool_name) {
      results.push({
        id: `receipt:${hit.tool_name ?? 'unresolved'}:${hit.param_name}`,
        title: `${hit.tool_name ?? '(unresolved tool)'}.${hit.param_name} — no call plan`,
        status: 'QUARANTINED',
        detail: `Association=${hit.association}; this gate could not confidently build a live-call arg set for this hit. Source: ${hit.source_file.split('/platform-mcp/')[1]}.`,
      })
      continue
    }
    await runStructuralChecksLive(client, hit.tool_name, plan.args, 'receipt', results)
    await sleep(MIN_GAP_MS)
  }

  runC7AccountingInvariant(results)
  process.exit(printGateReport('receipt_gate (LIVE)', results))
}

main().catch((err) => {
  console.error('receipt_gate FATAL:', err)
  process.exit(2)
})
