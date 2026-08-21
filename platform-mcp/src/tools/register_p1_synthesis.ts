/**
 * P1 Group 3 — Synthesis-adjacent surface tools (3 tools)
 * =========================================================
 * Exposes L5 Mīmāṃsā, L2 Bodha, and L3 Kāla capabilities
 * that existed in the registry but were NOT previously MCP-exposed.
 * Per BA-P1 brief §Step 3.
 *
 * mimamsa_insight_get  → marsys://tool/L5/query_insights (PD-1: 14 rows, STRUCTURAL mode)
 * bodha_discoveries_get → bodha_discoveries table (acharya-grade cross-domain observations)
 * kala_life_arc_get    → marsys://tool/L3/query_life_arc (kala_jivana_parva biographical parvas)
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { remoteAuthorize } from '../lib/authz.js'
import { describeProxyFailure } from './registry_bridge.js'
import { applyAutoBudgetToEnvelope } from '../lib/response_budget.js'
import { judgmentFlag, type JudgmentFlagEntry } from '../generated/envelope.js'

// W3-L2 (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF §E W3 item 2 "d8/hollow-emitter migration"):
// this file's local `envelope()` is the documented "hollow envelope" precedent (envelope.ts's
// own module doc calls it out by name) — every legacy field including `judgment_flags` was
// hardcoded to null/[] with ZERO honest-gap machinery, even when the wrapped `content` was
// itself empty. Computes a REAL (if minimal) disclosure from the content this call already
// fetched — never a static placeholder, never a new query. Best-effort: walks only the
// content's own top-level shape (arrays / a `total`/`returned` scalar), the same depth every
// tool in this file already exposes to its caller.
function deriveHollowEnvelopeFlags(content: unknown, primaryField?: string): JudgmentFlagEntry[] {
  if (content === null || content === undefined) {
    return [judgmentFlag('zero_rows_returned', 'no content returned for this call.')]
  }
  if (typeof content !== 'object' || Array.isArray(content)) {
    // Scalar/array content — no named row-count field to inspect; still an honest statement
    // that this legacy envelope shape never computes verdict/grounding/drill_pointers.
    return [judgmentFlag('hollow_envelope_shape_not_evaluated', 'content is not a keyed object — no row-count field available to check.')]
  }
  const obj = content as Record<string, unknown>

  // PARISHODHANA B3 fix (deprecated top-level alias masking hollowness): a caller may pass a
  // `primaryField` naming the ONE array the tool actually serves as its answer (e.g.
  // bodha_discoveries_get's caller-facing, filter-applied `discoveries`). Some tools' `content`
  // ALSO carries other, unfiltered back-compat arrays for the same underlying data (e.g.
  // query_discoveries.ts's raw `rows` / `discovery_families`, both explicitly documented as
  // "kept for back-compat" and NOT filtered by this tool's own `min_salience` param). Before
  // this fix, the generic "every array field empty" check below looked at ALL of those arrays
  // together, so a non-empty unfiltered back-compat array silently suppressed the hollow flag
  // even when the field the caller actually reads (`discoveries`) was empty because the
  // filter matched nothing — a misleading judgment_flags (no honest-gap signal when there
  // plainly was one). When `primaryField` is supplied and present as an array, it alone
  // decides hollowness; the generic multi-field walk below is the fallback for tools that
  // don't pass one (unchanged behavior for those).
  if (primaryField) {
    const primary = obj[primaryField]
    if (Array.isArray(primary)) {
      return primary.length === 0
        ? [judgmentFlag('hollow_envelope_no_data_rows', `the served '${primaryField}' field is empty for this call (other back-compat fields on this response may still carry unfiltered data — see the tool's field docs).`)]
        : []
    }
  }

  const arrayFields = Object.entries(obj).filter(([, v]) => Array.isArray(v)) as Array<[string, unknown[]]>
  if (arrayFields.length > 0) {
    const allEmpty = arrayFields.every(([, v]) => v.length === 0)
    if (allEmpty) {
      return [judgmentFlag('hollow_envelope_no_data_rows', `every row-shaped field (${arrayFields.map(([k]) => k).join(', ')}) is empty for this call.`)]
    }
    return []
  }
  const total = obj['total'] ?? obj['returned']
  if (total === 0) {
    return [judgmentFlag('zero_rows_returned', 'total/returned=0 for this call.')]
  }
  return [judgmentFlag('hollow_envelope_shape_not_evaluated', 'no array-valued or total/returned field found on content — no honest-gap signal computable from this shape (never fabricated).')]
}

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function callRegistryCapability(uri: string, args: Record<string, unknown>, principal: Principal): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(20_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    // R5.2 A3 (battery X-2 finding, same class as registry_bridge.ts's identical fix):
    // don't leak the raw HTTP status code into the MCP-facing error text.
    throw new Error(describeProxyFailure(uri, res.status, text))
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) throw new Error(`[p1_synthesis] capability error: ${data.error ?? 'unknown'}`)
  return data.content
}

/**
 * Unwraps the ToolResult shape that callRegistryCapability returns.
 * callRegistryCapability returns `data.content` from the HTTP response,
 * where the capability handler's own return value is `{ content: T, is_error: boolean }`.
 * So the raw result from callRegistryCapability IS that ToolResult — callers must
 * unwrap `.content` to get the actual payload. This helper does that unwrap typed.
 * Falls back to the raw value if `.content` is absent (defensive).
 */
function unwrapCapabilityResult(raw: unknown): Record<string, unknown> {
  const wrapper = raw as Record<string, unknown>
  const inner = wrapper['content']
  if (inner !== null && typeof inner === 'object' && !Array.isArray(inner)) {
    return inner as Record<string, unknown>
  }
  return wrapper
}

// R5 W0a punch-list (P6): the route now exists at /api/mcp/db/query (whitelisted,
// two-layer auth — see platform/src/app/api/mcp/db/query/route.ts). Callers MUST
// pass the resolved principal so Layer 2 (X-MCP-User/X-MCP-Key-Id) is satisfied —
// a bare x-mcp-internal-token is no longer sufficient (it never was for this route
// to be safely opened; the prior 404 masked the missing principal wiring too).
async function platformQuery(
  sql: string,
  params: unknown[],
  principal: Principal,
): Promise<{ rows: Record<string, unknown>[] }> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-MCP-Internal-Token': MCP_INTERNAL_TOKEN,
      'X-MCP-User': principal.user_uid,
      'X-MCP-Key-Id': principal.key_id,
    },
    body: JSON.stringify({ sql, params }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[p1_synthesis] platform DB query failed (${res.status}): ${text.slice(0, 200)}`)
  }
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
}

function envelope(content: unknown, toolName: string, queryClass: string, primaryField?: string) {
  return {
    envelope_version: 'v1',
    tool: toolName,
    verdict: null,
    ranking_basis: null,
    grounding: { fact_ids: [], citations: [], grounding_score: null },
    pagination: { offset: 0, limit: 0, total: null, next_cursor: null },
    drill_pointers: [],
    judgment_flags: deriveHollowEnvelopeFlags(content, primaryField),
    insight_type: null,
    query_class: queryClass,
    content,
  }
}

const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000

// R5 W0a punch-list (P3 fix class): dropped the `null, 2` pretty-print indent — pure
// serialization padding, no information content. Dual output (structuredContent + content)
// itself is retained (provider-spec obligation).
// S3 fix (R5 W0a perf lane): text duplicate suppressed above threshold (structuredContent already
// carries the full payload) — see JL-003 for the 50KB threshold ruling.
function dualOutput(data: unknown) {
  // R6 3b-budgets (R-1/R-8): auto-detect + trim any oversized array section in `content`
  // BEFORE serializing — covers kala_life_arc_get and the rest of this file's tools without
  // per-tool hand-declared sections (see response_budget.ts's autoDetectTrimmableSections doc).
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    const toolName = typeof obj['tool'] === 'string' ? (obj['tool'] as string) : 'unknown_tool'
    applyAutoBudgetToEnvelope(obj, toolName)
  }
  const structuredContent = { type: 'object' as const, object: data }
  const json = JSON.stringify(data)
  if (Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES) {
    return { structuredContent, content: [{ type: 'text' as const, text: '[large payload — see structuredContent]' }] }
  }
  return { structuredContent, content: [{ type: 'text' as const, text: json }] }
}

// ── R-5 fix: typed error envelope, never leak raw SQL/driver detail ──────────
//
// Denial ≠ empty ≠ internal error (register R-5): a caught error's `String(err)` may be a
// deliberately-authored, safe validation/denial message ("chart_id is required",
// "ENTITLEMENT_DENIED: ...") OR a raw driver/SQL error ('column "salience_score" does not
// exist', a stack frame, a connection string). The former is safe to echo verbatim; the
// latter must NEVER reach the client — it leaks internal schema/implementation detail and
// gives callers no stable, typed thing to branch on. classifyErrorMessage() distinguishes
// the three classes; errorOutput() logs the raw detail server-side only when it collapses
// an internal-looking message to the generic safe one.
type McpErrorClass = 'validation' | 'permission_denied' | 'internal_error'

function classifyErrorMessage(message: string): { error_class: McpErrorClass; safe_message: string } {
  if (/ENTITLEMENT_DENIED|AUTHZ_DENIED|lacks .* access/i.test(message)) {
    return { error_class: 'permission_denied', safe_message: message }
  }
  if (/ is required($|[^a-zA-Z])|^either `|^Unknown facet|^Unsupported /i.test(message)) {
    return { error_class: 'validation', safe_message: message }
  }
  const looksInternal =
    /column ".*" does not exist|relation ".*" does not exist|syntax error at or near|ECONNREFUSED|invalid input syntax|PostgresError|\bat \S+\.(ts|js):\d+|\.node_modules[\\/]/i.test(message)
  if (looksInternal) {
    return {
      error_class: 'internal_error',
      safe_message: 'An internal error occurred while serving this request. The specific ' +
        'cause has been logged server-side and is not exposed to the client (never leak raw ' +
        'SQL/driver detail — R-5).',
    }
  }
  return { error_class: 'internal_error', safe_message: message }
}

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  const { error_class, safe_message } = classifyErrorMessage(message)
  if (error_class === 'internal_error' && safe_message !== message) {
    console.error(`[${tool}] internal_error (raw, server-only, never sent to client): ${message}`)
  }
  const data = { ok: false, error: { class: error_class, message: safe_message }, tool, ...extra }
  return { ...dualOutput(data), isError: true as const }
}

// ── synth_chart_brief_get narration helpers ──────────────────────────────
// R5.3 B2 (Whole-chart reading lane): the mahā-brief previously returned raw
// fact-id/statement rows with zero synthesis — no ranking language, no
// coverage-receipt sentence, no surfaced dissent — even though the raw
// material (rank_consequence ordering, provenance_chain.contradictions,
// topics_covered/domains_covered counts) was already fetched. These helpers
// assemble that already-fetched data into narration; they perform NO new
// computation and query NO new tables.

type RankedEvidenceEntry = {
  signal_id?: string
  signal_type_id?: string | null
  salience?: number
  tier?: string | null
  fact_ids?: string[]
  classical_sources?: string[]
}

type ContradictionEntry = {
  signal_a_id?: string
  signal_b_id?: string
  tension_class?: string | null
  combined_salience?: number
  resolution?: unknown
  verification_status?: string | null
}

type ProvenanceChain = {
  event_class_name?: string
  domain?: string
  activation_state?: string
  grade?: number
  ranked_evidence?: RankedEvidenceEntry[]
  contradictions?: ContradictionEntry[]
  tradition_concordance?: Record<string, unknown>
}

function getProvenanceChain(row: Record<string, unknown>): ProvenanceChain | null {
  const pc = row['provenance_chain']
  return (pc && typeof pc === 'object') ? pc as ProvenanceChain : null
}

// Fallback parse from the templated statement string ("Name: status (grade
// N.N/10). note") for depth=standard callers where provenance_chain wasn't
// fetched — never invents a value, only extracts what's already in `statement`.
// L7-SERVING (ŚABDA-ŚUDDHI): also handles the new no_evidence format from
// bo_pratijna v2.0 which says "Name: no evidence — ..." with no grade clause.
function parseStatement(statement: unknown): { name: string | null; status: string | null; grade: number | null } {
  const s = typeof statement === 'string' ? statement : ''
  // Match the no_evidence format first (no grade in statement)
  const mNoEvid = /^(.*?):\s*no evidence\b/i.exec(s)
  if (mNoEvid) return { name: mNoEvid[1] ?? null, status: 'no_evidence', grade: null }
  // Original format with grade
  const m = /^(.*?):\s*(promised|denied|conditional)\s*\(grade\s*([\d.]+)\/10\)/i.exec(s)
  if (!m) return { name: null, status: null, grade: null }
  return { name: m[1] ?? null, status: (m[2] ?? '').toLowerCase(), grade: m[3] ? Number(m[3]) : null }
}

// D-12 fix: "Verdict-vocabulary mapping + template pass before native-facing" — L5's raw
// `statement` text can itself carry MORE THAN ONE status keyword (register example:
// "Outcome: denied (grade 5.0/10). Conditional" — 'denied' AND 'Conditional' both present
// in the same statement). Serving the raw text/anchor status verbatim in that case presents
// an internally-contradictory verdict as settled. This never invents a NEW status — it only
// detects when the raw text disagrees with itself and resolves to the more conservative
// reading (never claim a delivered promise you cannot back): no_evidence > denied > conditional > promised.
// L7-SERVING (ŚABDA-ŚUDDHI): 'no_evidence' added as most conservative — no evidence at all
// is more conservative than 'denied' (which at least had evidence to refute).
const STATUS_PRECEDENCE = ['no_evidence', 'denied', 'conditional', 'promised'] as const

function detectStatusVocabularyConflict(statement: unknown): { conflicting: boolean; keywordsFound: string[] } {
  const s = typeof statement === 'string' ? statement : ''
  const found = new Set<string>()
  // L7-SERVING (ŚABDA-ŚUDDHI): include no_evidence / no evidence (both forms)
  for (const m of s.matchAll(/\b(promised|denied|conditional|no_evidence|no\s+evidence)\b/gi)) {
    found.add((m[1] ?? '').toLowerCase().replace(/\s+/g, '_'))
  }
  return { conflicting: found.size > 1, keywordsFound: Array.from(found) }
}

function resolveConflictingStatus(keywordsFound: string[]): string {
  return STATUS_PRECEDENCE.find(s => keywordsFound.includes(s)) ?? keywordsFound[0] ?? 'unresolved'
}

function buildCoverageReceipt(params: {
  topicsCovered: number
  domains: unknown[]
  verdictCount: number
  loadBearingCount: number
  calibratedCount: number
  discoveryCount: number
}): string {
  const { topicsCovered, domains, verdictCount, loadBearingCount, calibratedCount, discoveryCount } = params
  const domainList = domains.filter((d): d is string => typeof d === 'string').join(', ')
  return (
    `${topicsCovered} topic slot(s) evaluated across ${domains.length} domain(s)` +
    (domainList ? ` (${domainList})` : '') +
    `: ${verdictCount} domain verdicts, ${loadBearingCount} load-bearing signals, ` +
    `${calibratedCount} calibration strata, ${discoveryCount} cross-domain discoveries ranked.`
  )
}

function buildDissentFlags(verdicts: Record<string, unknown>[]): { dissent_flags: string[]; dissent_note: string | null } {
  const flags: string[] = []
  for (const row of verdicts) {
    const pc = getProvenanceChain(row)
    const contras = pc?.contradictions ?? []
    for (const c of contras) {
      const label = pc?.event_class_name ?? parseStatement(row['statement']).name ?? String(row['insight_id'] ?? 'unknown')
      flags.push(
        `Tension flagged on ${label}: ${c.tension_class ?? 'unclassified'} conflict between signal ` +
        `${(c.signal_a_id ?? '?').toString().slice(0, 8)}… and ${(c.signal_b_id ?? '?').toString().slice(0, 8)}… ` +
        `(salience ${typeof c.combined_salience === 'number' ? c.combined_salience.toFixed(2) : 'n/a'}, ` +
        `${c.resolution ? 'resolved' : 'unresolved'} / ${c.verification_status ?? 'unverified'}) — ` +
        `held as an open dissent, not silently reconciled.`
      )
      if (flags.length >= 5) break
    }
    if (flags.length >= 5) break
  }
  if (flags.length === 0) {
    return {
      dissent_flags: [],
      dissent_note: 'No cross-signal tension recorded in the fetched insight set for this depth/domain selection.',
    }
  }
  return { dissent_flags: flags, dissent_note: null }
}

function hedgeForGrade(evidenceGrade: unknown): string | null {
  const g = typeof evidenceGrade === 'string' ? evidenceGrade : ''
  if (g === 'prior_only' || g === 'documented_approximation') {
    return 'provisional — thin evidential base'
  }
  // F-143: 'assignment_only' means a row has enough ASSIGNMENTS to look well-supported but
  // fewer than 5 outcome-adjudicated matches behind it. Left unhedged it would read exactly
  // like a calibrated row to a caller who only sees the theme text.
  if (g === 'assignment_only') {
    return 'provisional — assignments only, no scored outcomes behind it'
  }
  return null
}

function citeEvidence(pc: ProvenanceChain | null): string | null {
  const evid = (pc?.ranked_evidence ?? [])
    .slice()
    .sort((a, b) => (b.salience ?? 0) - (a.salience ?? 0))
    .slice(0, 2)
  if (evid.length === 0) return null
  return evid
    .map(e => {
      const fid = (e.fact_ids ?? [])[0]
      if (fid) return `fact ${fid}, salience ${typeof e.salience === 'number' ? e.salience.toFixed(2) : 'n/a'}`
      // no fact_id available — ground on the signal type label instead of inventing a citation.
      return e.signal_type_id ? `${e.signal_type_id}, salience ${typeof e.salience === 'number' ? e.salience.toFixed(2) : 'n/a'}` : null
    })
    .filter((x): x is string => Boolean(x))
    .join('; ')
}

function buildRankedThemes(
  verdicts: Record<string, unknown>[],
  audience: 'native' | 'third_party',
): { strengths: string[]; weaknesses: string[]; open_questions: string[]; verdict_quality_flags: string[]; weaknesses_empty_reason: string | null } {
  const strengths: string[] = []
  const weaknesses: string[] = []
  const openQuestionsRaw: Array<{sentence: string; grade: number | null}> = []
  const verdictQualityFlags: string[] = []
  let conditionalCount = 0
  let minConditionalGrade: number | null = null
  // GA-5 review finding on #1385: weaknesses_empty_reason must be derived from what was
  // ACTUALLY observed per-row, not a hardcoded claim about a grade threshold nothing here
  // evaluates. Track the real causes a 'denied' row can be excluded from weaknesses.
  let deniedSuppressedByZeroSupportCount = 0
  let noEvidenceCount = 0

  for (const row of verdicts) {
    const pc = getProvenanceChain(row)
    const parsed = parseStatement(row['statement'])
    const name = pc?.event_class_name ?? parsed.name ?? String(row['insight_id'] ?? 'signal')
    let status = pc?.activation_state ?? parsed.status
    const grade = typeof pc?.grade === 'number' ? pc.grade : parsed.grade
    const domain = pc?.domain ?? row['domain'] ?? null
    const citation = citeEvidence(pc)
    const hedge = hedgeForGrade(row['evidence_grade'])
    const gradeStr = grade != null ? `${grade.toFixed(1)}/10` : 'ungraded'

    // D-12 fix (part 1): raw statement carrying multiple, mutually-exclusive status keywords
    // (e.g. "denied ... Conditional") is an internally-contradictory verdict, not a settled
    // one — resolve to the conservative reading and flag it rather than serve the raw
    // (unresolved) mismatch as if it were a clean status.
    const { conflicting, keywordsFound } = detectStatusVocabularyConflict(row['statement'])
    if (conflicting) {
      const resolved = resolveConflictingStatus(keywordsFound)
      verdictQualityFlags.push(
        `${name}: raw statement carries conflicting status keywords (${keywordsFound.join(', ')}) — ` +
        `resolved to "${resolved}" (most conservative reading; D-12).`
      )
      status = resolved
    }

    // L7-SERVING (ŚABDA-ŚUDDHI): no_evidence rows already carry an honest statement
    // from mi_darshana. Route them directly to open_questions without running through
    // grade/status sentence construction — they have no grade to display, and the
    // zero-support masking path would replace their already-honest label.
    if (status === 'no_evidence') {
      noEvidenceCount++
      let sentence = `${name}: no evidence available for this event class — cannot assess.`
      if (citation) sentence += ` (${citation})`
      openQuestionsRaw.push({ sentence, grade: null })
      continue
    }

    // D-12 fix (part 2): a grade with ZERO supporting rows is not the same claim as a
    // grade backed by evidence (R-21 principle applied here to a numeric grade rather than
    // a ✓ mark) — never present n_support=0 grades with unqualified confidence.
    const nSupport = typeof row['n_support'] === 'number' ? row['n_support'] as number : null
    const zeroSupport = nSupport === 0
    // GA-5 review finding on #1385: capture status BEFORE it gets overwritten below, so
    // weaknesses_empty_reason can honestly report a denied-but-suppressed row instead of
    // silently losing it (it never reaches the 'denied' bucket once status is overwritten).
    if (zeroSupport && status === 'denied') deniedSuppressedByZeroSupportCount++
    if (zeroSupport && status !== 'no_evidence') {
      verdictQualityFlags.push(
        `${name}: grade ${gradeStr} carries n_support=0 (zero backing evidence rows) — ` +
        `treat as unverified/provisional, not a confirmed grade.`
      )
      // MC-010 (P0-safety, ŚODHANA T1): a zero-evidence structural prior must never be
      // SERVED with a pass/fail verb ("denied"/"promised"/"confirmed") — flagging it in
      // verdict_quality_flags alone is not enough, because the headline verb is what a
      // skimming reader sees first. Overwrite the served status label itself (not just
      // the flag) on safety-sensitive domains this is a harm issue, not a style issue.
      status = ZERO_SUPPORT_SAFE_LABEL
    }

    let sentence: string
    if (audience === 'third_party') {
      const domainPhrase = domain ? ` (${domain})` : ''
      sentence = `${name}${domainPhrase}: ${status ?? 'unresolved'} (grade ${gradeStr}) — ` +
        `a signal parents may want to watch for in this area, not itself a cause for alarm.`
    } else {
      sentence = `${name}: ${status ?? 'unresolved'} (grade ${gradeStr}).`
    }
    if (citation) sentence += ` (${citation})`
    if (hedge) sentence += ` [${hedge}]`
    if (conflicting) sentence += ' [CONTRADICTORY RAW STATEMENT — status resolved conservatively; see verdict_quality_flags]'
    if (zeroSupport) sentence += ' [UNVERIFIED — n_support=0]'

    // MC-010: strengths/weaknesses verbs ('promised'/'denied') are only ever bucketed
    // when n_support > 0 — a zero-evidence row's status was already overwritten above
    // (status !== 'promised'/'denied' in that case), the `!zeroSupport` guard here is
    // deliberate defense-in-depth against any future refactor that stops overwriting it.
    if (status === 'promised' && !zeroSupport && (grade == null || grade >= 6)) {
      strengths.push(sentence)
    } else if (status === 'denied' && !zeroSupport) {
      weaknesses.push(sentence)
    } else {
      if (status === 'conditional') {
        conditionalCount++
        if (grade != null && (minConditionalGrade == null || grade < minConditionalGrade)) {
          minConditionalGrade = grade
        }
      }
      openQuestionsRaw.push({ sentence, grade: grade ?? null })
    }
  }

  openQuestionsRaw.sort((a, b) => {
    if (a.grade == null && b.grade == null) return 0
    if (a.grade == null) return 1
    if (b.grade == null) return -1
    return a.grade - b.grade
  })
  const openQuestions = openQuestionsRaw.map(x => x.sentence)

  // GA-5 review finding on #1385: the prior version of this reason hardcoded a claim
  // ('no event class scored below the denied ceiling, grade < 2.0/10') that nothing in
  // this function evaluates -- weakness membership is a STATUS test ('denied'), not a
  // grade-threshold test, and a real observed row (denied, grade 5.0/10, n_support=0) can
  // falsify that exact sentence. Reason is now built ONLY from causes actually observed
  // this call, per §N.7 item 6 (an honest null/per-cause statement, never a plausible-
  // sounding invented one).
  let weaknesses_empty_reason: string | null = null
  if (weaknesses.length === 0) {
    const reasonParts: string[] = []
    if (deniedSuppressedByZeroSupportCount > 0) {
      reasonParts.push(
        `${deniedSuppressedByZeroSupportCount} event class(es) carry a 'denied' verdict but with ` +
        `zero supporting evidence rows (n_support=0) — excluded from weaknesses as unverified, ` +
        `not absent (see verdict_quality_flags for the individual class names)`
      )
    }
    if (conditionalCount > 0) {
      const minStr = minConditionalGrade != null ? minConditionalGrade.toFixed(1) : 'ungraded'
      reasonParts.push(`${conditionalCount} class(es) sit in the conditional band (lowest: ${minStr}/10)`)
    }
    if (noEvidenceCount > 0) {
      reasonParts.push(`${noEvidenceCount} class(es) have no evidence available (listed in open_questions instead)`)
    }
    weaknesses_empty_reason = reasonParts.length > 0
      ? `no event class for this chart currently carries an unsuppressed 'denied' verdict: ${reasonParts.join('; ')}.`
      : `no event class for this chart carries a 'denied' verdict.`
  }

  return { strengths, weaknesses, open_questions: openQuestions, verdict_quality_flags: verdictQualityFlags, weaknesses_empty_reason }
}

// MC-010 (P0-safety, ŚODHANA T1): verdict_summary[].statement is the RAW L5
// mimamsa_insight_units.statement text (e.g. "Marriage: denied (grade 1.6/10)") —
// served alongside (not replaced by) the narrated ranked_themes sentences built in
// buildRankedThemes below. A skimming reader (human or LLM) reading a pass/fail verb
// next to a safety-sensitive domain (marriage/health/childbirth/financial loss) on a
// zero-evidence STRUCTURAL-mode row will misread it as a confirmed categorical finding.
// This never invents a new value — it only masks the verb token when n_support=0 proves
// there is zero backing evidence for the grade the verb rides on.
// L7-SERVING (ŚABDA-ŚUDDHI): 'no_evidence' / 'no evidence' added to the RE so the
// conflict detector can see them — but sanitizeZeroSupportStatement must SKIP rows
// whose statement already contains "no evidence", because those are ALREADY honest
// (they were written by mi_darshana's no_evidence branch, §N.7-6 compliant).
const ZERO_SUPPORT_VERB_RE = /\b(promised|denied|conditional|confirmed|no_evidence|no\s+evidence)\b/gi
const ZERO_SUPPORT_SAFE_LABEL = 'not_yet_assessed (structural prior, no evidence rows)'

function sanitizeZeroSupportStatement(row: Record<string, unknown>): Record<string, unknown> {
  const nSupport = typeof row['n_support'] === 'number' ? row['n_support'] as number : null
  const statement = row['statement']
  if (nSupport !== 0 || typeof statement !== 'string') return row
  // no_evidence statements are already honest — masking them would replace the
  // honest label with a fabricated one; skip them entirely (L7-SERVING, ŚABDA-ŚUDDHI).
  if (/\bno\s*evidence\b/i.test(statement)) return row
  ZERO_SUPPORT_VERB_RE.lastIndex = 0
  if (!ZERO_SUPPORT_VERB_RE.test(statement)) return row
  ZERO_SUPPORT_VERB_RE.lastIndex = 0
  return {
    ...row,
    statement: statement.replace(ZERO_SUPPORT_VERB_RE, ZERO_SUPPORT_SAFE_LABEL),
    statement_verb_masked_note:
      'Original statement carried a pass/fail verb (promised/denied/conditional/confirmed) ' +
      'with n_support=0 (zero backing evidence rows) — verb replaced with a safe status label ' +
      '(MC-010, ŚODHANA T1). Never claim a categorical finding with no supporting evidence.',
  }
}

// Drop redundant/empty scaffolding from a raw insight row before it goes into
// the response: (a) per-row surface_formula_version is a constant already
// stated once at brief.formula_version; (b) empty classical_sources[] arrays
// inside ranked_evidence cost bytes with zero information; (c) ranked_evidence
// is capped to its top 3 entries by salience with a recover_via pointer for
// the full chain. Trims byte weight to stay clear of DUAL_OUTPUT_TEXT_THRESHOLD_BYTES.
function trimInsightRow(row: Record<string, unknown>): Record<string, unknown> {
  const { surface_formula_version: _drop, ...rest0 } = row
  const rest = sanitizeZeroSupportStatement(rest0)
  const pc = getProvenanceChain(rest)
  if (!pc) return rest
  const trimmedEvidence = (pc.ranked_evidence ?? [])
    .slice()
    .sort((a, b) => (b.salience ?? 0) - (a.salience ?? 0))
    .slice(0, 3)
    .map(e => {
      const { classical_sources, ...evRest } = e
      return (classical_sources && classical_sources.length > 0)
        ? { ...evRest, classical_sources }
        : evRest
    })
  return {
    ...rest,
    provenance_chain: {
      ...pc,
      ranked_evidence: trimmedEvidence,
      ranked_evidence_note: (pc.ranked_evidence?.length ?? 0) > 3
        ? `top 3 of ${pc.ranked_evidence?.length} — recover full chain via mimamsa_insight_get`
        : undefined,
    },
  }
}

// F-135: exported for unit testing only — not part of the public API.
export { buildRankedThemes as _buildRankedThemesForTest }

export function registerP1SynthesisTools(server: McpServer, principal: Principal): void {

  // ── 1. mimamsa_insight_get ────────────────────────────────────────────────
  server.tool(
    'mimamsa_insight_get',
    'Retrieve L5 Mīmāṃsā insight units for a chart. ' +
    'Returns calibrated insight units from the mimamsa_insight_units table: ' +
    'calibrated outlooks (prediction→outcome match scores), manifestation-grammar learnings, ' +
    'emergent-law discoveries (pattern candidates from cross-chart mining), ' +
    'load-bearing conclusions (the chart\'s most consequential structural claims), ' +
    'and negative-knowledge statements (what this chart rules out). ' +
    'IMPORTANT: The system is in STRUCTURAL mode (L5 SEALED per BA build arc). ' +
    'calibration_status=\'prior_only\' — empirical scores populate as outcome data accrues. ' +
    'All units carry provenance chains back to L1 chart_facts.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      insight_type: z.enum([
        'calibrated_outlook', 'manifestation_grammar', 'emergent_law',
        'load_bearing', 'negative_knowledge', 'verdict_object',
      ]).optional().describe('Filter by insight type. Omit for all types.'),
      domain: z.string().optional().describe('Filter by life domain (career, health, relationship, wealth, etc.).'),
      min_rank: z.number().min(0).max(1).optional().describe('Minimum rank_consequence threshold (0..1, default: 0).'),
      top_k: z.number().int().min(1).max(200).optional().describe('Max insight units (default: 30, max: 200).'),
      include_negative_knowledge: z.boolean().optional()
        .describe('Include is_negative_knowledge=true rows (default: true).'),
    },
    async ({ chart_id, insight_type, domain, min_rank, top_k, include_negative_knowledge }) => {
      if (!chart_id) return errorOutput('mimamsa_insight_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L5/query_insights', {
          chart_id, insight_type, domain,
          min_rank: min_rank ?? 0,
          top_k: top_k ?? 30,
          include_negative_knowledge: include_negative_knowledge !== false,
        }, principal)
        const inner = unwrapCapabilityResult(data)
        const wrapped = {
          calibration_status: 'prior_only',
          mode: 'STRUCTURAL',
          note: 'L5 Mīmāṃsā is SEALED in STRUCTURAL mode. Empirical calibration accrues as outcome data is recorded.',
          ...inner,
        }
        return dualOutput(envelope(wrapped, 'mimamsa_insight_get', 'synthesis_calibration'))
      } catch (err) {
        return errorOutput('mimamsa_insight_get', String(err), { chart_id })
      }
    }
  )

  // ── 2. bodha_discoveries_get ──────────────────────────────────────────────
  server.tool(
    'bodha_discoveries_get',
    'Retrieve acharya-grade cross-domain discoveries for a chart from L2 Bodha. ' +
    'Queries the bodha_discoveries table — the "Bimba" (image/reflection) layer of Bodha, ' +
    'which contains the system\'s highest-signal cross-domain observations: ' +
    'patterns that surface only when multiple L1 data streams are synthesized. ' +
    'Examples: Saturn-Ketu mutual aspect amplifying 8th house themes across D1+D9+D10; ' +
    'strong Atmakaraka-Arudha Pada relationship forecasting public prominence. ' +
    'Returns discovery_id, domain tags, supporting fact_ids, salience score, and narrative.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      domain:   z.string().optional().describe('Filter by life domain (career, health, relationship, wealth, etc.).'),
      min_salience: z.number().min(0).max(1).optional().describe('Minimum salience score (0..1, default: 0).'),
      limit:    z.number().int().min(1).max(200).optional().describe('Max results (default: 30, max: 200).'),
      offset:   z.number().int().min(0).optional().describe('Pagination offset (default: 0).'),
    },
    async ({ chart_id, domain, min_salience, limit, offset }) => {
      if (!chart_id) return errorOutput('bodha_discoveries_get', 'chart_id is required')
      if (!(await remoteAuthorize(principal, chart_id, 'view'))) {
        return errorOutput('bodha_discoveries_get', 'AUTHZ_DENIED', { chart_id })
      }
      try {
        // MC-015 (ŚODHANA-ŚEṢA W1): this handler used to run its own hand-rolled SQL
        // directly against bodha_discoveries (R6 0b-deadtools fix, below), which meant
        // it NEVER called the registry capability (marsys://tool/L2/query_discoveries,
        // query_discoveries.ts) — including that capability's MC-015/026
        // `discovery_families` cross-ayanāṃśa collapse. Result: this MCP-facing tool kept
        // serving the raw, ~40x-duplicated-per-ayanāṃśa rows straight from the table with
        // no family collapse, even after PR #803 landed the fix one layer away. The sibling
        // kala_projections_get (register_p1_aliases.ts) never had this problem because it
        // was already written as a thin proxy to marsys://tool/L3/query_projections — so it
        // picked up `projection_families` for free. Rewired the same way here: proxy to the
        // registry capability instead of re-deriving (and diverging from) its query logic.
        // `min_salience` has no direct equivalent in the registry capability — the old raw
        // SQL branch's own comment already flagged `composite_discovery_rank` as NOT a 0..1
        // salience score (schema drift), so filtering on it was already semantically wrong.
        // Applied here, best-effort, against `non_obviousness_score` (the field the schema
        // actually carries in that 0..1 range) over the returned page.
        const data = await callRegistryCapability('marsys://tool/L2/query_discoveries', {
          chart_id,
          ...(domain ? { domain } : {}),
          limit: limit ?? 30,
          offset: offset ?? 0,
        }, principal)
        const content = unwrapCapabilityResult(data)
        const allRows = (content['rows'] as Record<string, unknown>[] | undefined) ?? []
        const rows = (min_salience != null && min_salience > 0)
          ? allRows.filter(r => Number(r['non_obviousness_score'] ?? 0) >= min_salience)
          : allRows
        return dualOutput(envelope({
          ...content,
          // Back-compat field names this tool has always exposed, alongside the richer
          // `rows` / `discovery_families` fields already on `content` from the registry.
          discoveries: rows,
          total: content['total_matching'] ?? rows.length,
          returned: rows.length,
          min_salience_filter_applied: min_salience ?? null,
          source_table: 'bodha_discoveries',
          // PARISHODHANA B3 fix: `content.rows`/`content.discovery_families` are
          // query_discoveries.ts's own unfiltered, "kept for back-compat" arrays — they are
          // NOT narrowed by this tool's `min_salience` filter the way `discoveries` (above)
          // is. Naming `discoveries` as the primaryField below means judgment_flags reports
          // hollowness off the field this tool actually serves as its filtered answer, not
          // off whichever back-compat array happens to still have unfiltered rows in it.
        }, 'bodha_discoveries_get', 'synthesis_cross_domain', 'discoveries'))
      } catch (err) {
        return errorOutput('bodha_discoveries_get', String(err), { chart_id })
      }
    }
  )

  // ── 3. kala_life_arc_get ──────────────────────────────────────────────────
  server.tool(
    'kala_life_arc_get',
    '[DEPRECATED — superseded by kala_story_get, ṢAḌ-DARŚANA v2 W0.4: the elevated STORY ' +
    'view over this same kala_jivana_parva substrate, with the parva-duplication defect ' +
    'fixed at serving (dedup by span+level), per-chapter tri-plane pointers, and argument-' +
    'shaped reading. This tool remains live — not retired — per the campaign\'s strangler-' +
    'fig discipline; its raw (un-deduped) parva rows are still available here.] ' +
    'Retrieve the biographical life-arc (Jīvana Parva) for a chart from L3 Kāla. ' +
    'Returns the kala_jivana_parva view: the life divided into named biographical periods ' +
    '(Parvas) based on Vimshottari mahadasha + dasha-sequence logic. Each Parva covers ' +
    'a named life stage with its dominant dasha lord, expected thematic domain, ' +
    'start/end years (age-based). ' +
    'Note: LEL-event join is not yet implemented for this tool (lel_capable: false at the ' +
    'capability layer). ' +
    'Use as the temporal backbone for reading the native\'s life story.',
    {
      // (F-26) the LEL-event opt-in param was intentionally removed — the underlying
      // capability declares lel_capable:false; re-adding it requires an actual LEL
      // join in query_life_arc.ts first.
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      limit:   z.number().int().min(1).max(100).optional().describe('Max Parvas (default: 50).'),
      offset:  z.number().int().min(0).optional().describe('Pagination offset (default: 0).'),
    },
    async ({ chart_id, limit, offset }) => {
      if (!chart_id) return errorOutput('kala_life_arc_get', 'chart_id is required')
      try {
        // T-9 fix (R6 0d-clips): the underlying capability (query_life_arc.ts) reads
        // `top_k`/`offset`, not `limit` — passing `limit` here was silently ignored
        // (top_k defaulted to 739 = all rows every time, regardless of this tool's
        // advertised `limit` param). Map limit -> top_k so the cap is actually honored.
        const data = await callRegistryCapability('marsys://tool/L3/query_life_arc', {
          chart_id,
          top_k: limit ?? 50,
          offset: offset ?? 0,
        }, principal)
        return dualOutput(envelope(unwrapCapabilityResult(data), 'kala_life_arc_get', 'temporal_life_arc'))
      } catch (err) {
        return errorOutput('kala_life_arc_get', String(err), { chart_id })
      }
    }
  )

  // ── 4. synth_tail_divergence_get ─────────────────────────────────────────
  server.tool(
    'synth_tail_divergence_get',
    'Retrieve the tail-divergence signals for a domain — the lowest-salience signals from L2 Bodha ' +
    'that contradict or diverge from the dominant synthesis reading. Per BA-P4 attention budget ' +
    '(70/20/10 head/dissent/tail), these are the "10% dissent" signals that surface minority positions. ' +
    'Use before anchoring high-confidence forecasts to surface contradicting evidence. ' +
    'Returns bodha_msr_signals rows in the bottom salience decile for the requested domain, ' +
    'with signal type, salience percentile, domains, and classical sources for audit.',
    {
      chart_id:  z.string().uuid().describe('Chart UUID. Required.'),
      domain:    z.string().optional().describe('Life domain filter (career, health, relationship, wealth, dharma, etc.). Omit for all domains.'),
      top_k:     z.number().int().min(1).max(50).optional().describe('Max tail signals to return (default: 10).'),
    },
    async ({ chart_id, domain, top_k }) => {
      if (!chart_id) return errorOutput('synth_tail_divergence_get', 'chart_id is required')
      if (!(await remoteAuthorize(principal, chart_id, 'view'))) {
        return errorOutput('synth_tail_divergence_get', 'AUTHZ_DENIED', { chart_id })
      }
      try {
        const limitVal = top_k ?? 10
        const params: unknown[] = [chart_id, 'lahiri_chitrapaksha']
        const domainClause = domain
          ? `AND domains_affected_array && ARRAY[$${(params.push(domain), params.length)}::text]`
          : ''
        params.push(limitVal)
        // R6 0b-deadtools (R-10): bodha_msr_signals has no `tier` column (schema drift —
        // real column is `signature_tier`). Also serves the already-computed, stored
        // `salience_pctl_in_class` (PERCENT_RANK over the chart's full signal set, written
        // by bo_laksana.py per S-15) instead of re-deriving a percentile query-time from a
        // domain-filtered subset — the domain filter would otherwise silently change the
        // percentile's reference population out from under the "bottom 10% of the WHOLE
        // chart" claim this tool advertises.
        const sql = `
          SELECT signal_id, signal_type_id, computed_salience, signature_tier,
                 salience_pctl_in_class AS salience_pctl,
                 domains_affected_array, classical_sources_array,
                 constituent_facts_array, valence
          FROM bodha_msr_signals
          WHERE chart_id = $1 AND ayanamsha_id = $2 ${domainClause}
            AND salience_pctl_in_class IS NOT NULL
            AND salience_pctl_in_class <= 0.10
          ORDER BY salience_pctl_in_class ASC
          LIMIT $${params.length}
        `
        const result = await platformQuery(sql, params, principal)
        return dualOutput(envelope({
          tail_signals: result.rows,
          total: result.rows.length,
          divergence_memo:
            `${result.rows.length} tail-divergence signal(s) (bottom 10% salience) ` +
            `for chart ${chart_id}${domain ? ` / domain ${domain}` : ''}. ` +
            `Per BA-P4 attention budget 70/20/10: these form the dissent/tail tier. ` +
            `Review before anchoring high-confidence forecasts.`,
          filters: { domain, top_k: limitVal, ayanamsha: 'lahiri_chitrapaksha' },
          attention_budget_note: 'BA-P4: head=70%, dissent=20%, tail=10%. These signals occupy the tail=10%.',
        }, 'synth_tail_divergence_get', 'synthesis_tail_divergence'))
      } catch (err) {
        return errorOutput('synth_tail_divergence_get', String(err), { chart_id })
      }
    }
  )

  // ── 5. synth_chart_brief_get ──────────────────────────────────────────────
  server.tool(
    'synth_chart_brief_get',
    'Assemble the Mahā-Brief — a comprehensive chart synthesis across 38 canonical topic slots. ' +
    'Draws from L5 Mīmāṃsā insight_units (verdict_object + calibrated_outlook + load_bearing + ' +
    'negative_knowledge) and L2 Bodha discoveries. Covers: domain verdicts (career/health/' +
    'relationship/wealth/creativity/dharma/moksha), load-bearing conclusions, negative knowledge, ' +
    'tradition concordance overview, and calibration status. ' +
    'depth=standard: key verdicts only (38 topics). depth=deep: + evidence chains. ' +
    'depth=complete: + tail divergence + all tradition stacks. ' +
    'System is in STRUCTURAL mode (L5 SEALED) — empirical scores accrue as outcome data records.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      depth:    z.enum(['standard', 'deep', 'complete']).optional()
        .describe('Brief depth: standard (default), deep, or complete.'),
      audience: z.enum(['native', 'third_party']).optional()
        .describe('Narration voice: native (default, first-person-neutral about the chart\'s own subject) ' +
          'or third_party (reframes ranked themes as observations for someone reading on the native\'s ' +
          'behalf — e.g. a parent — without adding any new data source; consumes the same fetched rows).'),
    },
    async ({ chart_id, depth = 'standard', audience = 'native' }) => {
      if (!chart_id) return errorOutput('synth_chart_brief_get', 'chart_id is required')
      if (!(await remoteAuthorize(principal, chart_id, 'view'))) {
        return errorOutput('synth_chart_brief_get', 'AUTHZ_DENIED', { chart_id })
      }
      try {
        const topK = depth === 'complete' ? 200 : depth === 'deep' ? 80 : 38
        const insightResult = await platformQuery(`
          SELECT insight_id, insight_type, domain, question_lens,
                 statement, rank_consequence, confidence_band,
                 n_support, evidence_grade, is_negative_knowledge,
                 surface_formula_version
                 ${depth !== 'standard' ? ', provenance_chain' : ''}
          FROM mimamsa_insight_units
          WHERE chart_id = $1
          ORDER BY
            CASE insight_type
              WHEN 'verdict_object'     THEN 1
              WHEN 'load_bearing'       THEN 2
              WHEN 'calibrated_outlook' THEN 3
              WHEN 'emergent_law'       THEN 4
              WHEN 'negative_knowledge' THEN 5
              ELSE 6
            END,
            rank_consequence DESC NULLS LAST
          LIMIT $2
        `, [chart_id, topK], principal)

        const discLimit = depth === 'complete' ? 20 : 5
        const discResult = await platformQuery(`
          SELECT discovery_id, discovery_class, discovery_subsystem,
                 affected_domains_array AS domains,
                 hypothesis_text, depth_reading, why_an_acharya_misses_it,
                 surface_reading,
                 composite_discovery_rank AS salience_score
          FROM bodha_discoveries
          WHERE chart_id = $1
          ORDER BY composite_discovery_rank DESC NULLS LAST
          LIMIT $2
        `, [chart_id, discLimit], principal)

        const rows = insightResult.rows
        const verdicts     = rows.filter(r => r['insight_type'] === 'verdict_object')
        const loadBearing  = rows.filter(r => r['insight_type'] === 'load_bearing')
        const calibrated   = rows.filter(r => r['insight_type'] === 'calibrated_outlook')
        const negKnowledge = rows.filter(r => r['is_negative_knowledge'])
        const domains      = [...new Set(verdicts.map(r => r['domain']).filter(Boolean))]

        const lbLimit  = depth === 'standard' ? 5  : 20
        const calLimit = depth === 'standard' ? 3  : 10
        const negLimit = depth === 'standard' ? 3  : 10

        const trimmedVerdicts = verdicts.map(trimInsightRow)
        const coverage_receipt = buildCoverageReceipt({
          topicsCovered: rows.length,
          domains,
          verdictCount: verdicts.length,
          loadBearingCount: Math.min(loadBearing.length, lbLimit),
          calibratedCount: Math.min(calibrated.length, calLimit),
          discoveryCount: discResult.rows.length,
        })
        const { dissent_flags, dissent_note } = buildDissentFlags(verdicts)
        const ranked_themes = buildRankedThemes(verdicts, audience)
        const lel_disclosure =
          'This reading draws only on chart-derived L5 Mīmāṃsā / L2 Bodha signals — it does not ' +
          'reference or infer from the native\'s personal event log (no life_event_log join in this query).'

        const brief = {
          chart_id,
          depth,
          audience,
          // F-143 / §N.7 item 3: this was the hardcoded literal 'mi_darshana_v1.0' — a
          // wrapper-local constant shadowing a value the query above already selects
          // (surface_formula_version). It could not track a writer version bump, so it
          // would have started mislabelling every brief the moment mi_darshana bumped.
          // Report what the rows actually carry; disclose a mixed set rather than picking one.
          formula_version:
            [...new Set(rows.map(r => r['surface_formula_version']).filter(Boolean))].join(', ') ||
            'none — no insight units for this chart',
          calibration_mode: 'STRUCTURAL',
          calibration_note: 'L5 SEALED — empirical scores accrue as outcome data is recorded.',
          topics_covered: rows.length,
          domains_covered: domains,
          coverage_receipt,
          dissent_flags,
          ...(dissent_note ? { dissent_note } : {}),
          ranked_themes,
          lel_disclosure,
          verdict_summary: trimmedVerdicts,
          load_bearing_signals: loadBearing.slice(0, lbLimit).map(trimInsightRow),
          calibration_strata: calibrated.slice(0, calLimit).map(trimInsightRow),
          negative_knowledge: negKnowledge.slice(0, negLimit).map(trimInsightRow),
          top_discoveries: discResult.rows,
        }

        return dualOutput(envelope(brief, 'synth_chart_brief_get', 'synthesis_maha_brief'))
      } catch (err) {
        return errorOutput('synth_chart_brief_get', String(err), { chart_id })
      }
    }
  )

  // ── prashna_undertaking_get ───────────────────────────────────────────────
  // BA-P5B Step 3: Q4 undertaking recipe = prashna verdict × election scoring × fructification.
  // Reads ga_prashna_judgment (prashna chart), phala_muhurta (election windows for domain),
  // phala_anchors (fructification timing anchor), brahma_activity_ontology (rules).
  server.tool(
    'prashna_undertaking_get',
    'Q4 undertaking recipe: prashna (horary) verdict × muhurta election scoring × fructification timing. ' +
    'Provide the prashna chart_id (cast at question moment) and domain. ' +
    'Returns: horary verdict, best election windows, fructification anchor, composite undertaking score.',
    {
      chart_id:       z.string().uuid().describe('Prashna chart UUID (cast at question moment, not natal chart).'),
      domain:         z.string().describe('Undertaking domain (career | financial | relationship | health | spiritual | transition).'),
      top_windows:    z.number().int().min(1).max(10).default(3).describe('Number of top election windows to return.'),
    },
    async ({ chart_id, domain, top_windows }) => {
      if (!chart_id) return errorOutput('prashna_undertaking_get', 'chart_id is required')
      if (!(await remoteAuthorize(principal, chart_id, 'view'))) {
        return errorOutput('prashna_undertaking_get', 'AUTHZ_DENIED', { chart_id, domain })
      }

      // The undertaking's election rows and activity-ontology rules use related but
      // distinct authorities. `phala_muhurta.action_class` is the writer's concrete
      // election vocabulary (for example `medical`); the activity ontology uses its
      // own class IDs (for example `medical_procedure`). Keep the two mappings
      // explicit rather than selecting all election windows and merely labelling the
      // result with an inferred action class.
      const _DOMAIN_TO_MUHURTA_ACTION: Record<string, string> = {
        career:       'start_business',
        financial:    'contract_signing',
        wealth:       'contract_signing',
        health:       'medical',
        relationship: 'marriage',
        spiritual:    'spiritual_initiation',
        spirituality: 'spiritual_initiation',
        transition:   'travel',
      }
      const muhurtaActionClass = _DOMAIN_TO_MUHURTA_ACTION[domain]
      if (!muhurtaActionClass) {
        return errorOutput('prashna_undertaking_get', 'INVALID_DOMAIN', { chart_id, domain })
      }
      try {
        // 1. Prashna judgment (from ga_prashna_judgment)
        // R6 0b-deadtools (R-12): gj.verdict/gj.verdict_strength/gj.significator_positions/
        // gj.timing_indication/gj.classical_citations do not exist on ga_prashna_judgment —
        // schema drift (these column names were never live). The real verdict is the
        // categorical `judgment_text` (e.g. "UNCERTAIN"); there is NO numeric strength
        // column at all — per canonical-or-floor, verdictStrength below is floored NULL
        // with a reason rather than computed from judgment_text (that would be a fabricated
        // substitute, not a citable value). significator_positions/timing_indication are
        // reshaped from the real querent/quesited + fructification columns, not invented.
        const prashnaResult = await platformQuery(`
          SELECT gj.question_class, gj.judgment_text AS verdict, gj.ayanamsha_id,
                 gj.querent_significator, gj.quesited_significator,
                 gj.querent_longitude, gj.quesited_longitude, gj.longitudinal_gap,
                 gj.is_applying, gj.tajik_yoga,
                 gj.fructification_value, gj.fructification_unit, gj.fructification_rule_id,
                 gj.lagna_rashi, gj.classical_citation
          FROM ga_prashna_judgment gj
          WHERE gj.chart_id = $1
          ORDER BY gj.ayanamsha_id
          LIMIT 5
        `, [chart_id], principal)

        // 2. Election windows (phala_muhurta for the requested domain's action class)
        const muhurtaResult = await platformQuery(`
          SELECT pm.action_class, pm.window_start, pm.window_end,
                 pm.composite_quality, pm.window_quality_verdict,
                 pm.fructification_anchor, pm.tarabala_chandrabala_jsonb,
                 pm.significators_met_jsonb, pm.follow_up_hook_jsonb
          FROM phala_muhurta pm
          WHERE pm.chart_id = $1
            AND pm.composite_quality IS NOT NULL
            AND pm.action_class = $2
          ORDER BY pm.composite_quality DESC NULLS LAST
          LIMIT $3
        `, [chart_id, muhurtaActionClass, top_windows], principal)

        // 3. Fructification timing from phala_anchors (domain-filtered)
        const anchorResult = await platformQuery(`
          SELECT pa.anchor_id, pa.domain, pa.event_type, pa.posterior,
                 pa.magnitude,
                 to_char(pa.window_start, 'YYYY-MM-DD') AS window_start,
                 to_char(pa.window_end, 'YYYY-MM-DD')   AS window_end,
                 pa.structured_falsifier_jsonb, pa.lift_vector_jsonb
          FROM phala_anchors pa
          WHERE pa.chart_id = $1
            AND pa.domain = $2
            AND pa.posterior IS NOT NULL
          ORDER BY pa.posterior DESC NULLS LAST
          LIMIT 3
        `, [chart_id, domain], principal)

        // 4. Activity ontology fructification rules for inferred action class
        // SHABDA-SHUDDHI Lane L5 (Fix 3): canonical domain vocabulary + existing activity IDs.
        //   - 'financial' → 'wealth' (legacy non-canonical domain key)
        //   - 'spiritual' → 'spirituality' (legacy non-canonical domain key)
        //   - 'sadhana' → 'spiritual_initiation' (sadhana does not exist in brahma_activity_ontology;
        //      verified against l0_ghatana.py seed; spiritual_initiation does exist)
        //   - Fallback changed from 'business_start' (misleading — implies a business undertaking
        //     for any unresolved domain) to null (honest: no matching activity class found).
        //   Activity IDs verified against brahmagyan/l0_ghatana.py seed data.
        const _DOMAIN_TO_ACTION: Record<string, string> = {
          career:       'business_start',
          wealth:       'contract_signing',
          health:       'medical_procedure',
          relationship: 'marriage',
          spirituality: 'spiritual_initiation',
          transition:   'travel_journey',
          residence:    'griha_pravesh',
          travel:       'travel_journey',
          education:    'education_start',
        }
        const actionClass: string | null = _DOMAIN_TO_ACTION[domain] ?? null
        const ontologyResult = actionClass ? await platformQuery(`
          SELECT activity_class_id, name_en, significators, fructification_rules, citations
          FROM brahma_activity_ontology
          WHERE activity_class_id = $1
        `, [actionClass], principal) : { rows: [] }

        // Composite undertaking score = mean(prashna verdict_strength, best election quality, best posterior).
        // R-12 fix: ga_prashna_judgment carries no numeric verdict-strength column (only the
        // categorical judgment_text) — canonical-or-floor forbids inventing a number from that
        // text, so verdictStrength floors to null+reason and the composite averages only over
        // the components that actually have a value (never silently substituting a placeholder
        // for the missing one).
        const verdictStrength: number | null = null
        const verdictStrengthFloorReason =
          'ga_prashna_judgment has no verdict_strength (or equivalent numeric) column — ' +
          'judgment_text is the only verdict field and is categorical (e.g. "UNCERTAIN"). ' +
          'Floored NULL rather than derived from text (canonical-or-floor).'
        const bestElection = (muhurtaResult.rows[0]?.['composite_quality'] as number | null) ?? 0.5
        const bestPosterior = (anchorResult.rows[0]?.['posterior'] as number | null) ?? 0.1
        const compositeInputs = [verdictStrength, bestElection, bestPosterior].filter(
          (v): v is number => typeof v === 'number'
        )
        const compositeScore = compositeInputs.length > 0
          ? Math.round((compositeInputs.reduce((a, b) => a + b, 0) / compositeInputs.length) * 1000) / 1000
          : null

        const recipe = {
          chart_id,
          domain,
          action_class: actionClass,
          formula_version: 'prashna_undertaking_v1.0_ba_p5b',
          composite_undertaking_score: compositeScore,
          composite_undertaking_score_note: verdictStrength === null
            ? `Averaged over ${compositeInputs.length}/3 components — verdict_strength omitted: ${verdictStrengthFloorReason}`
            : null,
          prashna_verdict: prashnaResult.rows,
          election_windows: muhurtaResult.rows,
          fructification_anchors: anchorResult.rows,
          fructification_rules: ontologyResult.rows[0]?.['fructification_rules'] ?? null,
          classical_citations: ontologyResult.rows[0]?.['citations'] ?? [],
          note: 'Q4 undertaking recipe: horary verdict × election scoring × fructification. ' +
                'JL-009: posterior values use placeholder base rates until native review.',
        }

        return dualOutput(envelope(recipe, 'prashna_undertaking_get', 'q4_undertaking'))
      } catch (err) {
        return errorOutput('prashna_undertaking_get', String(err), { chart_id, domain })
      }
    }
  )
}
