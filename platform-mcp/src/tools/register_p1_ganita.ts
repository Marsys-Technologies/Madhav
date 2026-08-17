/**
 * P1 Group 1 — Per-chart computed-chart tools (12 tools)
 * ======================================================
 * Exposes L1 Gaṇita capabilities that existed in the registry but were NOT previously
 * MCP-exposed. Per BA-P1 brief §Step 1 (RM §3.2 Group-1 table).
 *
 * All tools:
 *   - call callRegistryCapability() → platform /api/retrieval/capability
 *   - wrap response in RetrievalEnvelope v1 (verdict/ranking_basis null until P4/P2)
 *   - token cap: 25k default limit
 *   - scope: per_chart (chart_id required) — with 2 global exceptions, items 10-11 below
 *     (ganita_database_schema_get / ganita_concept_locate take an OPTIONAL chart_id,
 *     defaulting to the canonical chart — same as their underlying registry capabilities)
 *
 * Items 10-12 (ganita_database_schema_get, ganita_concept_locate, ganita_planet_get) were
 * added by the Elevation Campaign v2.1 STREAM α Lane-H follow-up (2026-07-25): the batch-1
 * registry capabilities get_database_schema / concept_locate / query_planet
 * (platform/src/lib/retrieval/registry/layers/L1_ganita/) were registered at the registry
 * layer but had no MCP-facing tool exposing them — the exact dark-asset gap this file exists
 * to close for the rest of L1. Same call-through mechanism, same dualOutput()/errorOutput()
 * envelope as items 1-9.
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import type { Principal } from '../types.js'
import { describeProxyFailure } from './registry_bridge.js'
import { resolveChartFactsAyanamsha } from '../lib/ayanamsha.js'
// R5 W0b-codegen (design §19): imports the GENERATED envelope module — the mirror that
// used to live at '../lib/envelope.js' was hand-written and has been deleted. See
// scripts/generate_envelope.ts for the generator; src/generated/envelope.ts is its output.
import {
  buildRetrievalEnvelope,
  resolveEnvelopeFormat,
  extractGroundingFromFactRows,
  buildEpistemicSummary,
  VERIFIED_PASS_STATUSES,
  judgmentFlag,
  type EnvelopeFormat,
  type ChartHeader,
  type DrillPointerType,
  type CoverageStamp,
  type JudgmentFlagEntry,
} from '../generated/envelope.js'
import { applyAutoBudgetToEnvelope } from '../lib/response_budget.js'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

function normalizeAyanamsha(id?: string): string {
  return resolveChartFactsAyanamsha(id)
}

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
    signal: AbortSignal.timeout(25_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    // R5.2 A3 (battery X-2 finding, same class as registry_bridge.ts's identical fix):
    // don't leak the raw HTTP status code into the MCP-facing error text.
    throw new Error(describeProxyFailure(uri, res.status, text))
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) throw new Error(`[p1_ganita] capability error: ${data.error ?? 'unknown'}`)
  // A4 (CR-93/94 root cause, live-verified 2026-07-15 against 482012f1): the platform route
  // /api/retrieval/capability does `NextResponse.json({ ok: true, content: await
  // capability.handler(safeArgs) })` — and every CapabilityDescriptor handler ITSELF returns
  // `{ content, is_error }` (registry/types.ts contract). So `data.content` here is really
  // `{ content: <realPayload>, is_error: boolean }`, one level deeper than every call site in
  // this file assumed (`data?.rows`, `data?.total`, etc. all read past the real payload into
  // `undefined`). Confirmed live: a `ganita_yogas_get` v3 call served
  // `content.content.{chart_id,rows,total}` with 32 genuine rows one level down, while every
  // read of `data.rows`/`data.total` in THIS file saw `undefined` → `rows=[]` → `coverage.served:
  // 0` + a false `zero_rows_returned` judgment_flag on a 32-row page (CR-94), AND starved the
  // Pancha Mahapurusha narrator's `get_positions` fetch the identical way, so `posByPlanet`
  // stayed empty and every PMP yoga fell through to the "position not available … not formed"
  // branch — wrongly denying a genuinely fired Śaśa Yoga even though its `yoga_label` row was
  // present in that same (mis-read) page (CR-93). Not a category mismatch (yoga_label vs
  // yoga_fires) and not a diacritics/name mismatch — chart_facts carries ZERO `yoga_fires`-
  // category rows for this chart; `yoga_label` rows ARE the fired entries per JL-004, and the
  // "Sasa Yoga" text matches the PANCHA_MAHAPURUSHA table exactly. The failure was purely this
  // unwrap depth. Unwrap it here, ONCE, so every caller in this file gets the real payload
  // directly rather than re-deriving the unwrap ad hoc per call site (the pattern
  // registry_bridge.ts had to hand-roll locally at its one call site that needed it — see its
  // `domainWrapper`/`inner` comment on the query_domain_reading call). Defensive: only unwraps
  // when the shape actually matches the handler-result contract (has an `is_error` key) — never
  // mis-unwraps a legitimately content-shaped payload that happens to lack that key.
  if (
    data.content && typeof data.content === 'object' && !Array.isArray(data.content) &&
    'is_error' in (data.content as Record<string, unknown>)
  ) {
    return (data.content as { content?: unknown }).content
  }
  return data.content
}

// R5 W0a punch-list (P3): envelope changes are additive-only (R5_AUTHORITY_DOSSIER §2) — every
// field below still ships, verbatim, on every call. The fix is that `pagination` is no longer
// unconditionally hollow: callers that already know their real offset/limit/total (the content
// they just fetched) may pass it through instead of it being silently dropped on the floor.
//
// R5 W0b (unified populated envelope, design §10/§19): `envelope()` now delegates to the
// shared buildRetrievalEnvelope() (canonical home: platform/src/lib/retrieval/envelope.ts;
// this process's mirror: ../lib/envelope.ts). Three-arg call sites are UNCHANGED — they still
// get the exact legacy shape (format defaults to 'legacy', v3Extras is undefined). Call sites
// that want the populated v3 envelope pass `format='v3'` + `v3Extras`; those extras are
// silently ignored under 'legacy' so existing consumers see a byte-identical response
// (brief §6.3 consumer format negotiation — default legacy until the W4 battery passes).
function envelope(
  content: unknown,
  toolName: string,
  pagination?: { offset: number; limit: number; total: number | null },
  format: EnvelopeFormat = 'legacy',
  v3Extras?: {
    chart_header?: ChartHeader | null
    verdict?: unknown
    ranking_basis?: Record<string, unknown> | null
    grounding?: { fact_ids: string[]; citations: string[]; grounding_score: number | null }
    drill_pointers?: { instrument: string; hint: string; pointer_type?: DrillPointerType }[]
    judgment_flags?: JudgmentFlagEntry[]
    as_of_date?: string
    epistemic?: ReturnType<typeof buildEpistemicSummary>
    coverage?: CoverageStamp | null
  },
) {
  return buildRetrievalEnvelope(
    {
      tool: toolName,
      content,
      pagination,
      chart_header: v3Extras?.chart_header,
      verdict: v3Extras?.verdict,
      ranking_basis: v3Extras?.ranking_basis,
      grounding: v3Extras?.grounding,
      drill_pointers: v3Extras?.drill_pointers,
      judgment_flags: v3Extras?.judgment_flags,
      as_of_date: v3Extras?.as_of_date,
      epistemic: v3Extras?.epistemic,
      coverage: v3Extras?.coverage,
    },
    format,
  )
}

const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000

// R5 W0a punch-list (P3, 174KB yogas overflow): dropped the `null, 2` pretty-print indent —
// pure serialization padding (~30-40% of wire bytes on large row sets), no information content.
// structuredContent + content dual-output is retained (provider-spec obligation, not padding).
// S3 fix (R5 W0a perf lane): text duplicate suppressed above threshold (structuredContent already
// carries the full payload) — see JL-003 for the 50KB threshold ruling.
function dualOutput(data: unknown) {
  // R6 3b-budgets (R-1/R-8): auto-detect + trim any oversized array section in `content`
  // BEFORE serializing — the shared generic mechanism (response_budget.ts) that covers this
  // whole file's tools (ganita_condition_get et al.) without per-tool hand-declared sections.
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

// Facet → L1 URI dispatch tables
// R-17 fix: parivartana and graha_yuddha were both routed to get_yoga_dosha, which has no
// backing category for either (its 6 categories are yoga_fires/yoga_label/dosha_fires/
// dosha_label/bhadra_flag/panchaka_flag) — both facets silently returned the identical
// unfiltered ~107-row yoga/dosha union. Their real data lives elsewhere: parivartana
// (mutual sign exchange) is fact_category parivartana_per_varga on get_dispositors;
// graha_yuddha (planetary war) has its own dedicated capability, get_graha_yuddha.
export const STRUCTURAL_FACET_URI: Record<string, string> = {
  aspects:          'marsys://tool/L1/get_aspects',
  // D-1.6 S-5 (PARK-A7 + R-17, the standing A7 PARK / S-4-sputa-drishti routed item):
  // `aspects` shared its declared category set with jaimini/tajik/matrix-summary rows, and
  // get_aspects.ts's underlying SQL orders `ORDER BY fact_category` GLOBALLY across every
  // requested category under ONE shared LIMIT — 'aspect_jaimini*' sorts alphabetically BEFORE
  // 'aspect_parashari_*', so a large aspect_jaimini_per_varga population (per graha × per
  // varga) could consume the entire row budget before a single Parashari (Graha Drishti) row
  // was ever reached — exactly the live symptom BIND_D-1.6 confirmed ("default page leads
  // with aspect_jaimini rasi-drishti boilerplate", 19 real aspect_parashari_given rows never
  // surfacing). Fix mirrors the D-1.5b kala_sarpa extraction (item 6): pull jaimini and tajik
  // aspects into their OWN focused facets sharing the same underlying URI/tool but a
  // DISJOINT declared category set (see FACET_CATEGORIES below), so neither can crowd out
  // the other under the shared-LIMIT tool. `aspects` now serves ONLY genuine Graha Drishti
  // (Parashari given/received/per-varga) — matching its own description text.
  aspects_jaimini:  'marsys://tool/L1/get_aspects',
  aspects_tajik:    'marsys://tool/L1/get_aspects',
  conjunctions: 'marsys://tool/L1/get_aspects',
  sambandha:    'marsys://tool/L1/get_aspects',
  argala:       'marsys://tool/L1/get_argala',
  dispositors:  'marsys://tool/L1/get_dispositors',
  functional:   'marsys://tool/L1/get_dispositors',
  parivartana:  'marsys://tool/L1/get_dispositors',
  yoga_fires:   'marsys://tool/L1/get_yoga_dosha',
  dosha_fires:  'marsys://tool/L1/get_yoga_dosha',
  graha_yuddha: 'marsys://tool/L1/get_graha_yuddha',
  // D-1.5b (item 6): a FOCUSED facet dedicated to kala_sarpa_per_varga — the full per-varga
  // (natal D1 + all 20 vargas) Kāla Sarpa map, computed by L1 but previously only reachable
  // by drawing down `dispositors`' shared row budget alongside 4 OTHER categories (where
  // kala_sarpa_per_varga sorts last alphabetically and can be truncated out of the page
  // entirely at the default limit) — "computed but buried". This facet guarantees the full
  // per-varga row set is served with zero competition from the other dispositor categories.
  kala_sarpa:   'marsys://tool/L1/get_dispositors',
}

// R-17 fix: each facet's DECLARED fact_category set. Used two ways: (1) narrows the
// underlying query via `categories` so facets sharing a URI (aspects/conjunctions/sambandha;
// dispositors/parivartana; yoga_fires/dosha_fires) actually return DIFFERENT row sets instead
// of the tool's full unfiltered union; (2) a serve-time assertion (below) verifies every
// returned row's fact_category is actually a member of this set — fails loudly instead of
// silently serving a mismatched category set if the map ever drifts from the underlying
// tool's real categories again.
//
// `functional` (functional benefic/malefic role) has NO dedicated L1 fact_category — that
// classification is derived logic living in graha_portrait.ts (R-6), not a stored chart_facts
// row. Declared as an empty/unbacked facet below: rejected outright rather than silently
// serving unrelated dispositor rows (canonical-or-floor: no backing category = no serve).
export const FACET_CATEGORIES: Record<string, string[]> = {
  // D-1.6 S-5 (PARK-A7 + R-17): narrowed to genuine Graha Drishti (Parashari) only — see
  // STRUCTURAL_FACET_URI comment above for the full root-cause writeup. aspect_matrix_summary
  // (a same-tool rollup ACROSS traditions) stays here too since it summarizes the Parashari
  // matrix this facet is now dedicated to, and is a small, bounded row (no crowding risk).
  aspects: [
    'aspect_parashari_given', 'aspect_parashari_received', 'aspect_parashari_per_varga',
    'aspect_matrix_summary',
  ],
  aspects_jaimini: ['aspect_jaimini', 'aspect_jaimini_per_varga'],
  aspects_tajik:   ['aspect_tajik'],
  conjunctions: ['conjunction_within_orb', 'conjunction_per_varga'],
  sambandha:    ['lord_aspects_lord_per_varga', 'lord_in_house_per_varga'],
  dispositors:  [
    'graha_dispositor_chain', 'dispositor_chain_per_varga', 'composite_dispositor_strength',
    'parivartana_per_varga', 'kala_sarpa_per_varga',
  ],
  parivartana:  ['parivartana_per_varga'],
  yoga_fires:   ['yoga_fires', 'yoga_label', 'bhadra_flag'],
  dosha_fires:  ['dosha_fires', 'dosha_label'],
  graha_yuddha: ['graha_yuddha'],
  kala_sarpa:   ['kala_sarpa_per_varga'],
  // argala intentionally omitted: get_argala is a single-purpose tool with no sibling facets
  // sharing its URI, so there is no cross-facet contamination risk to assert against.
}

// Facets with no valid backing category at all — rejected before dispatch (see comment above).
const NO_BACKING_FACETS = new Set(['functional'])

// EL-38 fix: the shared 25000 default below was sized for the OTHER facets on this tool
// (bounded row sets); argala is a per-varga × per-sign × per-offset matrix — live-verified
// 41,760 rows across 29 vargas for chart 482012f1 — and timed out at that default. Give
// argala its own sane default; every other facet keeps the existing 25000 default unchanged.
const FACET_DEFAULT_LIMIT: Record<string, number> = {
  argala: 500,
}
const STRUCTURAL_DEFAULT_LIMIT = 25000

// R5.3 B2 (Q9-N-3 ruling): Pancha Mahapurusha classical rule table (own-sign/exaltation +
// kendra). Static classical astrology (not chart data) — used only to LABEL already-fetched
// per-chart facts (yoga_label rows + graha_position sign/house_d1), never to compute a new
// chart value (B.10).
const KENDRA_HOUSES = new Set([1, 4, 7, 10])
const PANCHA_MAHAPURUSHA: {
  yoga: string; karaka: string; planet: string; ownSigns: string[]; exaltSign: string
}[] = [
  { yoga: 'Ruchaka', karaka: 'Mars',    planet: 'MAR', ownSigns: ['Aries', 'Scorpio'],       exaltSign: 'Capricorn' },
  { yoga: 'Bhadra',  karaka: 'Mercury', planet: 'MER', ownSigns: ['Gemini', 'Virgo'],        exaltSign: 'Virgo' },
  { yoga: 'Hamsa',   karaka: 'Jupiter', planet: 'JUP', ownSigns: ['Sagittarius', 'Pisces'],  exaltSign: 'Cancer' },
  { yoga: 'Malavya', karaka: 'Venus',   planet: 'VEN', ownSigns: ['Taurus', 'Libra'],        exaltSign: 'Pisces' },
  { yoga: 'Sasa',    karaka: 'Saturn',  planet: 'SAT', ownSigns: ['Capricorn', 'Aquarius'],  exaltSign: 'Libra' },
]

/** Builds per-yoga formed/not-formed sentences for the 5 Pancha Mahapurusha yogas from rows
 *  and planetary positions THIS RESPONSE ALREADY FETCHED (yoga_label presence = fired, per
 *  JL-004's ratified convention; graha_position sign/house_d1 = already-computed L1 facts,
 *  not a new derivation). Zero new computation.
 *
 *  Y-12 (D-1.6/S-3, CR-33/CR-43): `yogaDoshaRows` MUST be an UNPAGINATED yoga_label fetch, never
 *  the caller's own paginated page — the caller wires this via a dedicated get_yoga_dosha call
 *  (limit=500, offset=0) precisely so a small `limit` on ganita_yogas_get can never cause this
 *  function to assert "not formed" purely because pagination excluded a real yoga_label row from
 *  the page. A verdict must never fabricate absence from truncation (B.10).
 *
 *  A4 (CR-93 honesty hardening): `formed`/`not formed` is ALWAYS grounded in the yoga_label
 *  firing rows (a real signal, independent of position data). Position data is used only to
 *  ELABORATE the sign/kendra reason. Before this pass, when the position fetch came back empty
 *  (the CR-93 root cause — see callRegistryCapability's double-unwrap comment above), the
 *  reason text collapsed "positions unavailable" and "not formed" into one sentence ("...not
 *  formed per its absence from the yoga_label rows served") — reading as if the ABSENCE OF
 *  POSITION DATA were the reason for the verdict, which is never true (position data never
 *  drives `formed`) and is confusing/dishonest phrasing regardless of which fetch actually
 *  failed. `positionsAvailable` lets the reason text say plainly "positions unavailable —
 *  cannot state the sign/kendra reason" without implying that absence changed the verdict. */
function buildPanchaMahapurushaVerdict(
  yogaDoshaRows: Record<string, unknown>[],
  posByPlanet: Record<string, { sign?: string; house?: number; factId?: string }>,
) {
  const firedYogaNames = new Set(
    yogaDoshaRows
      .filter(r => r['fact_category'] === 'yoga_label')
      .map(r => String(r['fact_value_text'] ?? '')),
  )
  const positionsAvailable = Object.keys(posByPlanet).length > 0

  const perYoga = PANCHA_MAHAPURUSHA.map(entry => {
    const pos = posByPlanet[entry.planet]
    const matchingLabelNames = new Set([`${entry.yoga} Yoga`, `${entry.karaka} Yoga`])
    const formed = [...matchingLabelNames].some(label => firedYogaNames.has(label))
    const sourceRow = yogaDoshaRows.find(
      // The ga_structural writer's yoga catalog contract is
      // `fact_category=yoga_label, fact_key=yoga_name`.  Do not let another
      // yoga_label measurement with coincidentally matching display text donate
      // citations to this verdict (C.7 fact-category pinning).
      r => r['fact_category'] === 'yoga_label' && r['fact_key'] === 'yoga_name' &&
        matchingLabelNames.has(String(r['fact_value_text'] ?? '')),
    )
    const citations = (sourceRow?.['fact_value_jsonb'] as { classical_citations?: { text_id: string; chapter?: number }[] } | undefined)
      ?.classical_citations
    const citationText = citations?.length
      ? citations.map(c => c.chapter ? `${c.text_id} ch.${c.chapter}` : c.text_id).join(', ')
      : undefined

    let reason: string
    if (formed) {
      const dignity = pos?.sign === entry.exaltSign ? 'exalted' : entry.ownSigns.includes(pos?.sign ?? '') ? 'own sign' : 'condition satisfied'
      reason = `${entry.karaka} is in ${pos?.sign ?? 'unknown sign'} (${dignity})${typeof pos?.house === 'number' ? `, house ${pos.house}` : ''} — the own/exaltation-in-kendra condition is satisfied.` +
        (citationText ? ` Classical basis: ${citationText}.` : '')
    } else if (pos?.sign && !entry.ownSigns.includes(pos.sign) && pos.sign !== entry.exaltSign) {
      reason = `${entry.karaka} is in ${pos.sign} — neither own sign (${entry.ownSigns.join('/')}) nor exalted (${entry.exaltSign}); the condition fails on the sign leg.`
    } else if (pos?.sign && (entry.ownSigns.includes(pos.sign) || pos.sign === entry.exaltSign) && typeof pos.house === 'number' && !KENDRA_HOUSES.has(pos.house)) {
      reason = `${entry.karaka} is in ${pos.sign} (own/exalted sign) but house ${pos.house} is not a kendra (1st/4th/7th/10th); the condition fails on the kendra leg.`
    } else if (!positionsAvailable) {
      // A4 honesty fix: positions genuinely unavailable in this response — say so plainly,
      // and do NOT phrase the (still yoga_label-grounded) not-formed status as if it were
      // caused by the missing position data ("cannot rule" on the sign/kendra leg is a
      // DIFFERENT, weaker claim than "not formed", and the two must not be conflated).
      reason = `Positions unavailable in this response — cannot rule on ${entry.karaka}'s specific ` +
        `sign/kendra condition. The 'not formed' status above is independently grounded in the ` +
        `yoga_label firing rows served (JL-004: no ${entry.yoga} Yoga / ${entry.karaka} Yoga row present) ` +
        `— it is not derived from, or caused by, the missing position data.`
    } else {
      reason = `${entry.karaka}'s position was fetched but this response could not resolve a ` +
        `specific sign/house for it — cannot state the precise sign/kendra reason. The 'not formed' ` +
        `status above is independently grounded in the yoga_label firing rows served (JL-004: no ` +
        `${entry.yoga} Yoga / ${entry.karaka} Yoga row present).`
    }

    return {
      yoga: `${entry.yoga} (${entry.karaka} Mahapurusha Yoga)`,
      status: formed ? 'formed' : 'not formed',
      statement: `${entry.yoga} (${entry.karaka} Mahapurusha Yoga) is ${formed ? 'formed' : 'not formed'}. ${reason}`,
    }
  })

  const formedList = perYoga.filter(p => p.status === 'formed')
  const positionsCaveat = positionsAvailable
    ? ''
    : ' (NOTE: position data was unavailable in this response — per-yoga sign/kendra detail could ' +
      'not be confirmed for any entry; every formed/not-formed status above is still independently ' +
      'grounded in the yoga_label firing rows, not in position data.)'
  const summary = (formedList.length > 0
    ? `Yes, ${formedList.length} of 5 Pancha Mahapurusha yoga${formedList.length === 1 ? '' : 's'} — ${formedList.map(p => p.yoga).join(', ')} — ${formedList.length === 1 ? 'is' : 'are'} formed; the other ${5 - formedList.length} ${5 - formedList.length === 1 ? 'is' : 'are'} not formed.`
    : 'No Pancha Mahapurusha yoga is formed in this chart.') + positionsCaveat

  return { summary, per_yoga: perYoga, positions_available: positionsAvailable }
}

const CONDITION_FACET_URI: Record<string, string> = {
  dignity:  'marsys://tool/L1/get_dignity',
  avasthas: 'marsys://tool/L1/get_avasthas',
  karakas:  'marsys://tool/L1/get_karakas',
}

// R5 W0b-codegen parity gate (design §19 STRANGLER, brief §6.2): the three pilot instruments'
// input schemas are exported as named consts so the parity test can import the SAME zod
// schema objects the live handwritten shim registers — no re-typed duplicate schema in the
// test file. Compared against src/generated/registry_shims.ts's independently-generated
// schemas (derived from the registry CapabilityDescriptor) for byte-identical parse behavior.
export const ganitaStrengthGetInputSchema = {
  chart_id: z.string().uuid().describe('Chart UUID. Required.'),
  ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
  limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
  offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
  // ŚODHANA T3 (MC-014): default false — graha_in_house_composite_strength rows are filtered
  // to each graha's actual house (get_strength.ts's active-house filter) rather than every
  // planet x every house counterfactual placement.
  all: z.boolean().optional().describe(
    'Default false — graha_in_house_composite_strength (the one category with a row per graha ' +
    'PER HOUSE) is filtered to each graha\'s single ACTUAL house; every other strength category ' +
    'is already one row per graha and unaffected. Pass true for every counterfactual placement.'
  ),
}

export const ganitaSadeSatiGetInputSchema = {
  chart_id: z.string().uuid().describe('Chart UUID. Required.'),
  ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
  limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
  offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
  // ŚODHANA T3 (MC-014): default false — serves only the current+adjacent Saturn period(s),
  // not the full ~1950-2100 historical+future sweep (get_sade_sati.ts's WINDOW_YEARS filter).
  all: z.boolean().optional().describe(
    'Default false — serves only the CURRENT + adjacent Sade Sati/Saturn period(s), not every ' +
    'period this chart has ever had or will ever have across ~1950-2100. Pass true for the full ' +
    'historical+future sweep (useful for rectification / historical-events work).'
  ),
}

// CR-13/49 (D-1.5b item 2): the prior schema (max 25000, and the call site below forcing
// `limit ?? 25000`) silently overrode get_tajik.ts's own sane default (200, hard cap 1000 —
// see get_tajik.ts's `Math.min((args.limit as number) ?? 200, 1000)`) — the exact same
// "schema promises more than the server will ever return" class the R5 W0a punch-list
// already fixed for ganita_yogas_get. Bounds now tell the truth.
// MC-021/024 (ŚODHANA T4): `varsha_year`/`varsha_date`/`include_hadda` were silently accepted
// and dropped before this fix — the zod schema didn't declare them, so the MCP SDK stripped
// them before get_tajik.ts's handler (which DOES read varsha_year) ever saw them. The single
// most consultation-relevant row (the CURRENT solar year) was therefore unreachable through
// this tool. Now declared + threaded through to the registry capability (get_tajik.ts).
export const ganitaTajakaGetInputSchema = {
  chart_id: z.string().uuid().describe('Chart UUID. Required.'),
  ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
  varsha_year: z.number().int().optional().describe(
    'Filter varsha_year_lords to this EXACT solar-return year (1 = birth year). Preferred over ' +
    'paging when a single year (e.g. the current one) is wanted. Takes precedence over varsha_date.'),
  varsha_date: z.string().optional().describe(
    '"Current year" convenience: an ISO date (YYYY-MM-DD); resolved server-side to the solar-return ' +
    'varsha_year whose window contains this date, then applied as an exact-year filter. Ignored if ' +
    'varsha_year is also given. Omit both to get the default current-year-first ordering.'),
  include_hadda: z.boolean().optional().describe(
    'Include the 245 static hadda_lord/triraashipathi/vargottama chart_facts rows (do not vary by ' +
    'year). Default FALSE — pass true to fetch them; the true count is always reported either way.'),
  year_min: z.number().int().optional().describe('Filter varsha_year_lords to year >= this.'),
  year_max: z.number().int().optional().describe('Filter varsha_year_lords to year <= this.'),
  limit: z.number().int().min(1).max(1000).optional().describe('Max rows per section (default: 200, hard cap: 1000)'),
  offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
}

export function registerP1GanitaTools(server: McpServer, principal: Principal): void {

  // ── 1. ganita_strength_get ────────────────────────────────────────────────
  server.tool(
    'ganita_strength_get',
    'Retrieve Shadbala and allied strength metrics for a chart (L1 Gaṇita). Returns planet-by-planet ' +
    'strength scores: Sthana Bala (positional), Dig Bala (directional), Kaala Bala (temporal), ' +
    'Cheshta Bala (motional), Naisargika Bala (natural), Drig Bala (aspectual) — plus Ishta-Kashta, ' +
    'Vimsopaka, and Bhava Bala. Use to determine which planets are capable of delivering significations.',
    ganitaStrengthGetInputSchema,
    async ({ chart_id, ayanamsha_id, limit, offset, all }) => {
      if (!chart_id) return errorOutput('ganita_strength_get', 'chart_id is required')
      try {
        // MC-014 fix: `limit` no longer force-inflated to 25000 — the capability's own
        // default (500) now actually applies. `all` threads through to the capability's
        // actual-placement-only default filter (get_strength.ts).
        const data = await callRegistryCapability('marsys://tool/L1/get_strength', {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), limit, offset: offset ?? 0,
          ...(all != null ? { all } : {}),
        }, principal)
        return dualOutput(envelope(data, 'ganita_strength_get'))
      } catch (err) {
        return errorOutput('ganita_strength_get', String(err), { chart_id })
      }
    }
  )

  // ── 2. ganita_structural_get ──────────────────────────────────────────────
  server.tool(
    'ganita_structural_get',
    'Retrieve structural chart relationships via a single facet-parameterized tool (L1 Gaṇita). ' +
    'ONE tool covers all inter-planetary structural layers: ' +
    'aspects (Graha Drishti — Parashari planetary aspects given/received/per-varga ONLY; D-1.6 ' +
    'PARK-A7/R-17 fix: jaimini rashi-drishti and tajik aspects moved to their own dedicated ' +
    'facets below so they can never crowd Parashari rows out of the shared row budget), ' +
    'aspects_jaimini (Jaimini rashi drishti, natal + per-varga), ' +
    'aspects_tajik (Tajaka aspects: Itthasala/Ishrafa/Nakta/Yamaya/Manahoo/Khallasara), ' +
    'argala (planetary intervention), dispositors (sign-ruler chain), ' +
    'parivartana (exchange), yoga_fires (classical yoga patterns), dosha_fires (affliction patterns), ' +
    'conjunctions (same-sign occupancy), sambandha (relational bonds), ' +
    'functional (functional benefic/malefic roles), graha_yuddha (planetary war), ' +
    'kala_sarpa (the FULL per-varga — natal D1 + every divisional chart — Kāla Sarpa map, a ' +
    'focused facet so this row set is never truncated out by the 4 other dispositors categories). ' +
    'Specify exactly one facet per call. ' +
    'response_format=\'v3\' (opt-in; default \'legacy\') returns the R5 unified §N.6-density envelope ' +
    '(verdict/ranking_basis/grounding/drill_pointers/judgment_flags/epistemic/coverage/chart_header); ' +
    'for facet=dosha_fires it additionally states an explicit Kala Sarpa Dosha natal verdict ' +
    '(fired/not-fired, Rahu/Ketu house axis) sourced from the genuinely computed ' +
    'kala_sarpa_per_varga L1 fact rather than the unrelated dosha_label catalog row. ' +
    'B9 dosha gate (D-1.5b): for facet=dosha_fires, shared-stub dosha_label rows (fire_reason=' +
    'requires_pass) are excluded from the default page — pass all=true to include them. ' +
    'EL-38 (facet=argala only): a per-varga × per-sign × per-offset matrix — pass `varga` ' +
    '(e.g. "D1", "D9") to scope to one divisional chart instead of all ~29 at once (default ' +
    'limit is 500 for this facet specifically, not the shared 25000, to avoid timing out on ' +
    'the full matrix); `shape` controls whether rows carry a resolved `argala_on_house` ' +
    '(default) or the raw sign-indexed matrix (shape="matrix", backward compat).',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      facet: z.enum([
        'aspects', 'aspects_jaimini', 'aspects_tajik', 'argala', 'dispositors', 'parivartana',
        'yoga_fires', 'dosha_fires', 'conjunctions', 'sambandha',
        'functional', 'graha_yuddha', 'kala_sarpa',
      ]).describe('Which structural relationship layer to retrieve.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional()
        .describe('Max rows (default: 25000; facet=argala defaults to 500 instead — see facet description).'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
      response_format: z.enum(['legacy', 'v3']).optional()
        .describe("Envelope shape: 'legacy' (default, unchanged) or 'v3' (populated verdict/grounding/" +
          'drill_pointers/chart_header — for facet=dosha_fires includes an explicit Kala Sarpa verdict).'),
      all: z.boolean().optional().describe(
        'B9 dosha gate: for facet=dosha_fires, if true, includes catalog-only dosha_label rows ' +
        '(fire_reason=requires_pass) that are excluded by default. Ignored for other facets.'),
      varga: z.string().optional().describe(
        'facet=argala only: scope to one divisional chart (e.g. "D1", "D9"). Ignored for other facets.'),
      shape: z.enum(['resolved', 'matrix']).optional().describe(
        'facet=argala only: "resolved" (default) adds argala_on_house per row; "matrix" returns ' +
        'the raw sign-indexed rows (backward compat). Ignored for other facets.'),
    },
    async ({ chart_id, facet, ayanamsha_id, limit, offset, response_format, all, varga, shape }) => {
      if (!chart_id) return errorOutput('ganita_structural_get', 'chart_id is required')
      // R-17 fix: reject facets with no backing category outright, rather than silently
      // serving whatever unrelated rows the routed-to tool happens to return.
      if (NO_BACKING_FACETS.has(facet)) {
        return errorOutput(
          'ganita_structural_get',
          `facet="${facet}" has no dedicated L1 fact_category — this classification is derived ` +
          'logic (see graha_portrait.ts functional_nature), not a stored chart_facts row. ' +
          'Use graha_portrait with include=["functional_nature"] instead.',
          { chart_id, facet },
        )
      }
      const uri = STRUCTURAL_FACET_URI[facet]
      if (!uri) return errorOutput('ganita_structural_get', `Unknown facet: ${facet}`)
      try {
        const resolvedOffset = offset ?? 0
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        const format = resolveEnvelopeFormat(response_format)
        const declaredCategories = FACET_CATEGORIES[facet]
        // EL-38: per-facet default (argala=500) instead of the shared 25000 — see
        // FACET_DEFAULT_LIMIT comment above.
        const resolvedLimit = limit ?? FACET_DEFAULT_LIMIT[facet] ?? STRUCTURAL_DEFAULT_LIMIT
        const data = await callRegistryCapability(uri, {
          chart_id, ayanamsha_id: resolvedAyanamsha,
          limit: resolvedLimit, offset: resolvedOffset, facet,
          ...(facet === 'dosha_fires' ? { all: all === true } : {}),
          // EL-38: argala's own varga scope + house-resolution shape param, forwarded only
          // for facet=argala (get_argala.ts ignores unknown args for every other facet, but
          // being explicit here matches the existing dosha_fires `all` pattern).
          ...(facet === 'argala' && varga ? { varga } : {}),
          ...(facet === 'argala' && shape ? { shape } : {}),
          ...(declaredCategories ? { categories: declaredCategories } : {}),
        }, principal) as Record<string, unknown> | undefined
        const merged: Record<string, unknown> = { facet, ...(typeof data === 'object' && data ? data : { rows: data }) }

        // R-17 serve-time assertion: verify every returned row's fact_category is actually a
        // member of this facet's declared set. Fails loudly (rather than silently serving a
        // mismatched category set) if the map ever drifts from the underlying tool's real
        // categories again — this is the exact failure mode that caused the graha_yuddha/
        // parivartana bug in the first place.
        if (declaredCategories) {
          const mergedRows = Array.isArray(merged['rows']) ? merged['rows'] as Record<string, unknown>[] : []
          const declaredSet = new Set(declaredCategories)
          const offendingCategories = [...new Set(
            mergedRows
              .map(r => r['fact_category'] as string | undefined)
              .filter((c): c is string => Boolean(c) && !declaredSet.has(c as string))
          )]
          if (offendingCategories.length > 0) {
            return errorOutput(
              'ganita_structural_get',
              `facet="${facet}" routing assertion failed: returned rows include ` +
              `fact_category(s) [${offendingCategories.join(', ')}] outside the facet's declared ` +
              `set [${declaredCategories.join(', ')}]. This is a facet→category map bug, not a ` +
              'data problem — the map must be corrected, not the assertion widened.',
              { chart_id, facet },
            )
          }
        }

        if (format !== 'v3') {
          return dualOutput(envelope(merged, 'ganita_structural_get'))
        }

        // ── v3 population (R5.3 B2, Q9-N-1: dosha_fires had NO narration of any kind — always
        // legacy format; see the FACET_TO_TYPE + kala_sarpa_per_varga fixes in get_yoga_dosha.ts
        // for the wiring + data-availability half of this fix) ──
        const rows = Array.isArray(merged['rows']) ? merged['rows'] as Record<string, unknown>[] : []
        const grounding = extractGroundingFromFactRows(rows)
        const judgment_flags: JudgmentFlagEntry[] = []
        if (rows.length === 0) judgment_flags.push(judgmentFlag('zero_rows_returned'))

        const drill_pointers: { instrument: string; hint: string; pointer_type: DrillPointerType }[] = [
          { instrument: 'bodha_signals_get', hint: 'signal_type_class=yoga|dosha for salience-ranked cross-validation against L2 Bodha (SC-18: was previously mis-pointed at the non-existent MCP tool name "query_signals").', pointer_type: 'opposing_yoga' },
        ]

        let verdict: unknown = {
          facet,
          rows_served: rows.length,
          note: 'Row-count receipt; a facet-specific narrated verdict is added for facet=dosha_fires.',
        }

        if (facet === 'dosha_fires') {
          const ks = merged['kala_sarpa_per_varga'] as
            | { natal?: Record<string, unknown>[]; divisional_fired?: Record<string, unknown>[] }
            | undefined
          const natalRow = ks?.natal?.[0]
          const natalDetail = natalRow?.['fact_value_jsonb'] as
            | { fires?: boolean; rahu_house?: number; ketu_house?: number }
            | undefined
          // `dosha_label` is a category, not the semantic identity of the
          // catalog label.  ga_structural writes the named label under
          // `fact_key=dosha_name`; pin it before reducing to one row (C.7).
          const catalogRow = rows.find(
            r => r['fact_category'] === 'dosha_label' && r['fact_key'] === 'dosha_name' &&
              r['fact_value_text'] === 'Kala Sarpa Dosha',
          )

          if (natalDetail && typeof natalDetail.fires === 'boolean') {
            const fires = natalDetail.fires === true
            const divisionalFiredList = (ks?.divisional_fired ?? [])
              .map(r => (r['fact_value_jsonb'] as { varga?: string } | undefined)?.varga)
              .filter((v): v is string => Boolean(v))
            verdict = {
              facet,
              kala_sarpa_dosha: {
                natal_verdict: fires ? 'formed' : 'not_formed',
                statement: fires
                  ? `Kala Sarpa Dosha IS formed in the natal (D1/Rasi) chart — Rahu occupies house ${natalDetail.rahu_house}, Ketu house ${natalDetail.ketu_house}, with all seven non-nodal grahas confined to the arc between them on one side.`
                  : `Kala Sarpa Dosha is NOT formed in the natal (D1/Rasi) chart. The Rahu-Ketu axis is present — Rahu occupies house ${natalDetail.rahu_house}, Ketu house ${natalDetail.ketu_house} — but the classical condition requires ALL SEVEN non-nodal grahas confined within the arc between Rahu and Ketu on one side; this D1 detection returning not-fired means at least one graha falls outside that arc.`,
                rahu_house: natalDetail.rahu_house,
                ketu_house: natalDetail.ketu_house,
                source_fact_id: natalRow?.['fact_id'],
                reconciliation_note: catalogRow
                  ? `A generic "Kala Sarpa Dosha" catalog row does appear among this chart's dosha_label rows (fact_id ${String(catalogRow['fact_id'])}), but its cited constituent fact is a generic placeholder unrelated to Rahu/Ketu placement, shared by dozens of unrelated catalog rows — it is NOT the verified per-chart computation. The kala_sarpa_per_varga fact above (fact_category=kala_sarpa_per_varga, fact_key=ks_detection, varga=D1) is the authoritative, genuinely per-chart-computed Rahu/Ketu detection.`
                  : 'No competing "Kala Sarpa Dosha" catalog row was present in this page.',
                divisional_charts_with_fires_true: divisionalFiredList,
                divisional_note: divisionalFiredList.length > 0
                  ? `Several divisional (varga) charts DO show Kala Sarpa formation (fires=true): ${divisionalFiredList.join(', ')}. These are DIVISIONAL findings, not natal — they do not contradict the D1 natal verdict above.`
                  : 'No divisional (varga) chart in this response showed fires=true.',
              },
            }
            drill_pointers.push({ instrument: 'ganita_structural_get', hint: 'facet=kala_sarpa surfaces the FULL kala_sarpa_per_varga row set (natal D1 + every divisional chart) directly — a focused facet, never truncated by the other dispositors categories (item 6, D-1.5b).', pointer_type: 'other' })
          }
        }

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability('marsys://tool/L1/get_chart_header', {
            chart_id, ayanamsha_id: resolvedAyanamsha,
          }, principal) as ChartHeader
        } catch {
          chart_header = null // frame-safety header is best-effort; never fails the instrument
        }

        const total = typeof merged['total'] === 'number' ? merged['total'] as number : null

        // §N.6 Serving Density Principle retrofit (D-1.5b Lane B-6, item 4 — pending B-7's
        // formal §N.6 text landing in CLAUDE.md; applied here per the existing V3-envelope
        // pattern already established by ganita_yogas_get in this same file, the reference
        // "layered verdict/grounding/drill_pointers density contract" instrument): this v3
        // branch previously stopped at {chart_header, verdict, grounding, drill_pointers,
        // judgment_flags} — missing ranking_basis (the actual serve order, so a caller never
        // has to guess it) and the epistemic/coverage receipts every other §N.6-retrofitted
        // instrument in this file (ganita_yogas_get) already carries. Added here, zero new
        // computation (B.10) — derived from rows THIS response already fetched.
        const ranking_basis = {
          mode: 'catalog_order',
          fields: ['fact_category', 'ayanamsha_id', 'fact_key'],
          note: `The underlying ${uri.split('/').pop()} tool orders alphabetically by category/` +
            'ayanamsha/key, not by strength or salience — for salience-ranked cross-validation use ' +
            'get_signals(signal_type_class=yoga|dosha).',
        }
        const epistemic = buildEpistemicSummary({
          verifiedFraction: grounding.grounding_score,
          note: 'verified_fraction = share of this page\'s rows whose verification_pass_status is in '
            + VERIFIED_PASS_STATUSES.join('|')
            + ' — the one settled definition of verified (envelope.ts VERIFICATION_PASS_STATUS_VOCAB). '
            + 'Previously this note said "two_pass_verified" while the number beside it was computed '
            + 'from a wider two-value check including a bare "pass"; SAMĀPTI Ruling 13 collapsed the two.',
        })
        const coverage: CoverageStamp = {
          family: `${facet}_rows[categories=${declaredCategories?.join(',') ?? 'all'}]`,
          served: rows.length,
          total,
        }

        return dualOutput(envelope(merged, 'ganita_structural_get', {
          offset: resolvedOffset,
          limit: limit ?? 25000,
          total,
        }, 'v3', { chart_header, verdict, ranking_basis, grounding, drill_pointers, judgment_flags, epistemic, coverage }))
      } catch (err) {
        return errorOutput('ganita_structural_get', String(err), { chart_id, facet })
      }
    }
  )

  // ── 3. ganita_condition_get ───────────────────────────────────────────────
  server.tool(
    'ganita_condition_get',
    'Retrieve planetary condition data for a chart (L1 Gaṇita). ' +
    'Three facets: dignity (exaltation/debilitation/own-sign/friend/enemy + vargottama; NOTE: ' +
    'neecha-bhanga/debility-cancellation is NOT computed anywhere in this build — see ' +
    'MARSYS_DEFECT_GAP_REGISTER Y-3 — this facet does not detect or report it despite the ' +
    'classical name appearing in dignity theory), ' +
    'avasthas (Baladi/Jagradadi/Deeptadi state classifications), ' +
    'karakas (Chara Karakas AK→DK via Jaimini degree + Sthira Karakas). ' +
    'Default facet: dignity. Use to assess the intrinsic capability and vitality of each planet.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      facet: z.enum(['dignity', 'avasthas', 'karakas']).optional()
        .describe("Which condition layer: 'dignity' | 'avasthas' | 'karakas'. Default: 'dignity'"),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, facet, ayanamsha_id, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_condition_get', 'chart_id is required')
      const resolvedFacet = facet ?? 'dignity'
      const uri = CONDITION_FACET_URI[resolvedFacet]
      if (!uri) return errorOutput('ganita_condition_get', `Unknown facet: ${resolvedFacet}`)
      try {
        const data = await callRegistryCapability(uri, {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id),
          limit: limit ?? 25000, offset: offset ?? 0,
        }, principal)
        return dualOutput(envelope({ facet: resolvedFacet, ...( typeof data === 'object' && data ? data : { rows: data }) }, 'ganita_condition_get'))
      } catch (err) {
        return errorOutput('ganita_condition_get', String(err), { chart_id, facet: resolvedFacet })
      }
    }
  )

  // ── 3b. ganita_kp_cusps_get (SARVA-SIDDHI W-4 D-4, CR-30) ─────────────────
  // Dedicated first-class KP (Krishnamurti Paddhati) cusp/sub-lord face. SERVING ONLY —
  // no new computation (B.10); every value is an already-stored L1 fact. Closes the CR-30
  // known-gap on the vidhi primitive kp_cusp_sublord_read (previously reachable only via the
  // Jaimini+KP omnibus get_karakas or the raw chart_facts category route). This is NOT a
  // resurrection of the dropped kp_query / query_kp_ruling_planets phantoms — those were
  // whitelist names with no backing engine (removed by WP-1.7 for exactly that reason); this
  // is a real capability backed by real, stored data.
  server.tool(
    'ganita_kp_cusps_get',
    'Retrieve the dedicated KP (Krishnamurti Paddhati) cuspal picture for a chart (L1 Gaṇita). ' +
    'For each of the 12 bhava cusps: cusp sidereal longitude, sign (rashi), and the full KP lord ' +
    'chain — sign_lord (rashi lord) / star_lord (nakshatra lord) / sub_lord / sub_sub_lord / ' +
    'prana_lord — plus the cuspal significators list and the cusp degrees (Placidus and Sripati ' +
    'start/madhya/end). Also returns the KP ruling planets for the natal moment (Ascendant lord, ' +
    'Ascendant sub-lord, Moon sign/star lord, Day lord). SERVING ONLY — no new computation; every ' +
    'value is an already-stored L1 fact (chart_facts categories cusp_kp_lords, ' +
    'kp_cuspal_significators, bhava_cusps, kp_ruling_planets_natal). Defaults to the KP-canonical ' +
    "Krishnamurti ayanamsha; pass ayanamsha_id for any of the 5 stored ayanamshas. Pass " +
    'include_graha_kp_lords=true to also get each graha’s own KP chain (graha_kp_lords). ' +
    'Each cusp carries its source fact_ids for grounding back-reference.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional()
        .describe("Ayanamsha (default: 'krishnamurti', the KP-canonical one). Also: " +
          'lahiri_chitrapaksha, raman, true_chitra, surya_siddhanta_classical.'),
      include_graha_kp_lords: z.boolean().optional()
        .describe('If true, also return the per-graha KP star/sub/sub_sub/prana chain. Default false.'),
    },
    async ({ chart_id, ayanamsha_id, include_graha_kp_lords }) => {
      if (!chart_id) return errorOutput('ganita_kp_cusps_get', 'chart_id is required')
      // KP defaults to Krishnamurti — do NOT route through normalizeAyanamsha (it defaults to
      // lahiri and folds true_chitra→lahiri, both wrong for a KP surface). Pass through, with a
      // minimal lahiri-alias convenience only.
      const aya = !ayanamsha_id
        ? undefined
        : (ayanamsha_id === 'lahiri' || ayanamsha_id === 'LAHIRI' ? 'lahiri_chitrapaksha' : ayanamsha_id)
      try {
        const data = await callRegistryCapability('marsys://tool/L1/get_kp_cusps', {
          chart_id,
          ...(aya ? { ayanamsha_id: aya } : {}),
          ...(include_graha_kp_lords ? { include_graha_kp_lords: true } : {}),
        }, principal)
        return dualOutput(envelope(data, 'ganita_kp_cusps_get'))
      } catch (err) {
        return errorOutput('ganita_kp_cusps_get', String(err), { chart_id })
      }
    }
  )

  // ── 4. ganita_sade_sati_get ───────────────────────────────────────────────
  server.tool(
    'ganita_sade_sati_get',
    'Retrieve Sade Sati and the full Saturn transit period family for a chart (L1 Gaṇita). ' +
    'Covers all 15 classical Saturn period categories: Sade Sati cycles (with peak/rising/setting phases), ' +
    'Janma Shani, Ashtama Shani, Ardhashtama Shani, Dhaiya (Kantaka/2.5 year), and compound markers. ' +
    'Use to assess Saturn\'s current influence and upcoming heavy-transit windows.',
    ganitaSadeSatiGetInputSchema,
    async ({ chart_id, ayanamsha_id, limit, offset, all }) => {
      if (!chart_id) return errorOutput('ganita_sade_sati_get', 'chart_id is required')
      try {
        // MC-014 fix: `limit` no longer force-inflated to 25000 when omitted — the
        // capability's own default (500, current+adjacent-window-filtered unless
        // all:true) now actually applies, instead of every unpaginated call silently
        // requesting the maximum page before the window filter even runs.
        const data = await callRegistryCapability('marsys://tool/L1/get_sade_sati', {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), limit, offset: offset ?? 0,
          ...(all != null ? { all } : {}),
        }, principal)
        return dualOutput(envelope(data, 'ganita_sade_sati_get'))
      } catch (err) {
        return errorOutput('ganita_sade_sati_get', String(err), { chart_id })
      }
    }
  )

  // ── 5. ganita_tajaka_get ──────────────────────────────────────────────────
  server.tool(
    'ganita_tajaka_get',
    'Retrieve Tajaka (Varshaphal / annual horoscopy) data for a chart (L1 Gaṇita). ' +
    'Tajaka is the Perso-Arabic annual chart system used for year-by-year prediction: ' +
    'returns the current-year annual chart planetary positions, Muntha lord, year lord (Varshesha), ' +
    'Harsha Bala scores, and Tajaka aspects (Ithasala, Ishrafa, Nakta, Yamaya, Manahoo, Khallasara). ' +
    'Use for yearly-window predictions layered over the natal Vimshottari frame. ' +
    'CR-13/49: default limit is 200 rows per section (hadda_lord_facts / varsha_year_lords are ' +
    'paginated independently — see get_tajik.ts), hard cap 1000 — pass limit explicitly for a wider page.',
    ganitaTajakaGetInputSchema,
    async ({ chart_id, ayanamsha_id, varsha_year, varsha_date, include_hadda, year_min, year_max, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_tajaka_get', 'chart_id is required')
      try {
        // CR-13/49 fix: `limit` now passes through UNFORCED — omitting it lets get_tajik.ts's
        // own sane default (200, hard cap 1000) apply, instead of this call site silently
        // inflating every unpaginated request to 25000 rows.
        // MC-021/024 fix: varsha_year/varsha_date/include_hadda/year_min/year_max now actually
        // reach get_tajik.ts's handler instead of being silently stripped at the zod boundary.
        const data = await callRegistryCapability('marsys://tool/L1/get_tajik', {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), limit, offset: offset ?? 0,
          ...(varsha_year != null ? { varsha_year } : {}),
          ...(varsha_date != null ? { varsha_date } : {}),
          ...(include_hadda != null ? { include_hadda } : {}),
          ...(year_min != null ? { year_min } : {}),
          ...(year_max != null ? { year_max } : {}),
        }, principal)
        return dualOutput(envelope(data, 'ganita_tajaka_get'))
      } catch (err) {
        return errorOutput('ganita_tajaka_get', String(err), { chart_id })
      }
    }
  )

  // ── 6. ganita_nakshatra_get ───────────────────────────────────────────────
  server.tool(
    'ganita_nakshatra_get',
    'Retrieve Nakshatra-based strength data for a chart (L1 Gaṇita). ' +
    'Returns Tara Bala (the 9-fold Tara classification of each of the 27 nakshatras relative to ' +
    'the natal Moon nakshatra: Janma/Sampat/Vipat/Kshema/Pratyak/Sadhaka/Vadha/Mitra/Ati-Mitra) ' +
    'and Chandra Bala (12-sign Moon transit strength rating). ' +
    'Essential for Muhurta and transit timing quality assessment.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, ayanamsha_id, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_nakshatra_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L1/get_tara_chandra_bala', {
          chart_id, ayanamsha_id: normalizeAyanamsha(ayanamsha_id), limit: limit ?? 25000, offset: offset ?? 0,
        }, principal)
        return dualOutput(envelope(data, 'ganita_nakshatra_get'))
      } catch (err) {
        return errorOutput('ganita_nakshatra_get', String(err), { chart_id })
      }
    }
  )

  // ── 7. ganita_yogas_get ───────────────────────────────────────────────────
  server.tool(
    'ganita_yogas_get',
    'Retrieve Yoga and Dosha CATALOG/LABEL detections for a chart from chart_facts (L1 Gaṇita) — ' +
    'Pancha Mahapurusha (Ruchaka/Bhadra/Hamsa/Malavya/Shasha), Nabhasa yogas, and Parivartana; ' +
    'plus doshas: Mangal Dosha, Kemadruma, Grahan Yoga, Shrapit, Shakata, Kala Sarpa, and others. ' +
    'A4/CR-93/CR-94 CORRECTION (2026-07-15; supersedes the prior "will never fire from this tool" ' +
    'claim, which was itself stale and had become misleading): Dhana Yoga, Raja Yoga (kendra-' +
    'trikona + house-lord families), and Viparita Raja Yoga ARE now evaluated and DO fire on live ' +
    'charts (482012f1 fires 13 yogas including dhana_yoga_2_5_9_11 at strength 1.0218) — but ' +
    'THIS tool (chart_facts yoga_label rows, single-pass catalog matches per JL-004) is NOT their ' +
    'authoritative source and may still under-report them here. **`ganita_yoga_firings_get` (backed ' +
    'by the dedicated ga_yoga_firings table) is the firings-authoritative surface** for per-yoga ' +
    'strength scoring, bhaṅga/cancellation state, partial-formation %, and dāśā-activation — use it ' +
    'for any fired/not-fired judgment; treat this tool\'s rows as catalog labels to cross-check ' +
    'against, never as the sole word on whether a yoga fired. Neecha Bhanga (debility-cancellation) ' +
    'IS evaluated and served — but by `ganita_yoga_firings_get`, NOT by this tool: it fires ' +
    'neecha_bhanga_raja_yoga with bhanga_active + a per-varga grounds_jsonb ledger (BPHS Ch.39, ' +
    'rule-by-rule) since D-1.6 S-3 (D-2 gate-verified 2026-07-17). For any debility-cancellation ' +
    'read, call ganita_yoga_firings_get (optionally bhanga_active=true) — this catalog tool does not carry it. ' +
    'Returns yoga_name, constituent planets, house conditions, and activation_flag. ' +
    'response_format=\'v3\' (opt-in; default \'legacy\') returns the R5 unified envelope: ' +
    'a populated verdict (fired-yoga/dosha/flag counts — catalog-only/requires_pass rows are ' +
    'flagged, not presented as confirmed findings; see judgment_flags), grounding (fact_ids + ' +
    'citations from this response\'s own rows), ranking_basis (the actual serve order), ' +
    'drill_pointers (ganita_yoga_firings_get for cross-validated firing detail, mimamsa_insight_get ' +
    'for calibrated outlooks), judgment_flags (e.g. zero-row / truncated-page honesty markers), ' +
    'and chart_header. ' +
    'B9 dosha gate (D-1.5b): shared-stub dosha_label rows (fire_reason=requires_pass — a catalog/ ' +
    'label match, not a cross-verified per-chart finding) are EXCLUDED from the default page — see ' +
    'dosha_label_gate in the response. Pass all=true to include them.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha (default: 'lahiri_chitrapaksha')"),
      // R5 W0a punch-list (P3): the prior default (25000, echoing an unbounded schema promise)
      // silently overrode get_yoga_dosha's own sane default (500) and inflated the response
      // to 174KB. The handler's hard cap is 2000 rows (get_yoga_dosha.ts Math.min(...,2000)) —
      // schema bounds now tell the truth about what the server will actually return.
      limit: z.number().int().min(1).max(2000).optional().describe('Max rows (default: 500, hard cap: 2000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
      // R5 W0b consumer format negotiation (brief §6.3): default 'legacy' — byte-identical to
      // the pre-W0b response. 'v3' opts in to the populated unified envelope (closes P3).
      response_format: z.enum(['legacy', 'v3']).optional()
        .describe("Envelope shape: 'legacy' (default, unchanged) or 'v3' (populated verdict/grounding/ranking_basis/drill_pointers/chart_header — opt-in until the R5 W4 battery flips the default)."),
      all: z.boolean().optional().describe(
        'B9 dosha gate: if true, includes catalog-only dosha_label rows (fire_reason=requires_pass) ' +
        'that are excluded by default. Default false.'),
    },
    async ({ chart_id, ayanamsha_id, limit, offset, response_format, all }) => {
      if (!chart_id) return errorOutput('ganita_yogas_get', 'chart_id is required')
      try {
        const resolvedOffset = offset ?? 0
        const resolvedAyanamsha = normalizeAyanamsha(ayanamsha_id)
        const format = resolveEnvelopeFormat(response_format)
        const data = await callRegistryCapability('marsys://tool/L1/get_yoga_dosha', {
          chart_id, ayanamsha_id: resolvedAyanamsha, limit, offset: resolvedOffset, all: all === true,
        }, principal) as { total?: number; rows?: Record<string, unknown>[] } | undefined
        const total = typeof data?.total === 'number' ? data.total : null

        if (format !== 'v3') {
          return dualOutput(envelope(data, 'ganita_yogas_get', {
            offset: resolvedOffset,
            limit: limit ?? 500,
            total,
          }))
        }

        // ── v3 population (design §10; closes P3's hollow-envelope defect for this instrument) ──
        const rows = data?.rows ?? []

        // verdict: honest aggregation of the CATEGORIES ALREADY SERVED IN THIS RESPONSE (no new
        // computation — B.10). yoga_label/dosha_label rows ARE the fired entries (this chart's
        // engine writes fired items directly; there is no separate boolean yoga_fires/dosha_fires
        // row for the served categories — see JL-004).
        const categoryCounts: Record<string, number> = {}
        for (const r of rows) {
          const cat = String(r['fact_category'] ?? 'unknown')
          categoryCounts[cat] = (categoryCounts[cat] ?? 0) + 1
        }
        // R5.3 B2 (Q9-N-3 ruling): the row-count receipt above is a receipt, not narration.
        // Fetch graha positions (already-computed L1 fact_category, zero new computation) to
        // label the 5 named Pancha Mahapurusha yogas formed/not-formed with a citable reason —
        // best-effort: if the fetch fails, verdict still ships with the receipt fields above.
        //
        // Y-12 (D-1.6/S-3, CR-33/CR-43 fix): buildPanchaMahapurushaVerdict MUST NOT be grounded
        // in `rows` (the CALLER-PAGINATED page — e.g. limit=3 can return zero yoga_label rows
        // at all) — doing so fabricated "Sasa is not formed" purely because pagination excluded
        // Sasa's yoga_label row from THIS page, while the row genuinely exists (and Sasa
        // genuinely fires in ga_yoga_firings). Live-confirmed defect: ganita_yogas_get(limit=3,
        // response_format=v3) on 482012f1 asserted all 5 Pancha Mahapurusha yogas "not formed"
        // with zero yoga_label rows even present in the page. Fix: fetch a SEPARATE, unpaginated,
        // yoga_label-only slice (bounded to 500 — the tool's own sane default, well above the 5
        // named Mahapurusha rows that could ever match) so the verdict is grounded in the full
        // yoga_label population regardless of what the caller's own pagination window served.
        let panchaMahapurusha: ReturnType<typeof buildPanchaMahapurushaVerdict> | undefined
        try {
          const [positionsData, panchaMahapurushaRowsData] = await Promise.all([
            callRegistryCapability('marsys://tool/L1/get_positions', {
              chart_id, ayanamsha_id: resolvedAyanamsha, categories: ['graha_position'], limit: 200,
            }, principal) as Promise<{ rows?: Record<string, unknown>[] } | undefined>,
            callRegistryCapability('marsys://tool/L1/get_yoga_dosha', {
              chart_id, ayanamsha_id: resolvedAyanamsha, limit: 500, offset: 0, all: false,
            }, principal) as Promise<{ rows?: Record<string, unknown>[] } | undefined>,
          ])
          const posByPlanet: Record<string, { sign?: string; house?: number; factId?: string }> = {}
          for (const r of positionsData?.rows ?? []) {
            const subj = String(r['fact_subject'] ?? '')
            if (!subj) continue
            const slot = (posByPlanet[subj] ??= {})
            if (r['fact_key'] === 'sign') slot.sign = String(r['fact_value_text'] ?? '')
            if (r['fact_key'] === 'house_d1' && r['fact_value_num'] != null) slot.house = Number(r['fact_value_num'])
          }
          // Fall back to the page's own rows only if the dedicated unpaginated fetch failed
          // (never silently swap to a KNOWN-truncated source when the honest one is reachable).
          const groundingRows = panchaMahapurushaRowsData?.rows ?? rows
          panchaMahapurusha = buildPanchaMahapurushaVerdict(groundingRows, posByPlanet)
        } catch {
          panchaMahapurusha = undefined // best-effort narration enrichment; never fails the instrument
        }

        // A3 (CR-92 residue, R-3): get_yoga_dosha.ts now returns a `firings_pointer` (a genuine
        // ga_yoga_firings fired-count) and `catalog_only_rows_in_page` (B9-preview guard) — surface
        // both here so the v3 verdict never again reads as "yogas_fired: 0" while ga_yoga_firings
        // shows real fired yogas underneath it (the exact CR-33/CR-56/CR-92 defect class).
        const dataObj = data as {
          firings_pointer?: unknown
          catalog_only_rows_in_page?: number
          catalog_only_note?: string
          dosha_label_gate?: { applied: boolean; all: boolean; excluded_total: number; note: string }
        } | undefined
        const catalogOnlyRows = dataObj?.catalog_only_rows_in_page ?? 0

        const verdict = {
          yogas_fired: categoryCounts['yoga_label'] ?? 0,
          doshas_fired: categoryCounts['dosha_label'] ?? 0,
          bhadra_flag_rows: categoryCounts['bhadra_flag'] ?? 0,
          panchaka_flag_rows: categoryCounts['panchaka_flag'] ?? 0,
          category_counts: categoryCounts,
          note: 'Counts are of ROWS SERVED IN THIS PAGE only — see pagination.total for the full count.',
          // B9-preview: catalog_only/requires_pass rows are counted separately from
          // `yogas_fired`/`doshas_fired` above and MUST NOT be read as confirmed findings — they
          // still serve (never silently dropped), just flagged. Full gating is D-1.5b's job.
          catalog_only_rows_in_page: catalogOnlyRows,
          // B9 dosha gate (D-1.5b, closes the "full gating" TODO above for dosha_label
          // specifically): shared-stub dosha_label rows are excluded from `rows`/`doshas_fired`
          // above by default — this receipt states how many, and how to reach them (all=true).
          ...(dataObj?.dosha_label_gate ? { dosha_label_gate: dataObj.dosha_label_gate } : {}),
          ...(dataObj?.firings_pointer ? { firings_pointer: dataObj.firings_pointer } : {}),
          ...(panchaMahapurusha ? { pancha_mahapurusha: panchaMahapurusha } : {}),
        }

        const grounding = extractGroundingFromFactRows(rows)

        const judgment_flags: JudgmentFlagEntry[] = []
        if (rows.length === 0) judgment_flags.push(judgmentFlag('zero_rows_returned'))
        if (total !== null && resolvedOffset + rows.length < total) judgment_flags.push(judgmentFlag('partial_page_more_available'))
        if (catalogOnlyRows > 0) {
          judgment_flags.push(judgmentFlag(
            'catalog_only_rows_present',
            `${catalogOnlyRows} row(s) in this page are catalog_only/` +
            'requires_pass label matches (JL-004), not cross-verified confirmed firings — see ' +
            'verdict.catalog_only_rows_in_page and ganita_yoga_firings_get for confirmed detail.',
          ))
        }

        const ranking_basis = {
          mode: 'catalog_order',
          fields: ['fact_category', 'ayanamsha_id', 'fact_key'],
          note: 'get_yoga_dosha orders alphabetically by category/key, not by strength or salience — ' +
            'for salience-ranked cross-validation use query_signals(signal_type_class=yoga|dosha).',
        }

        // Typed per design §28.4 (R5 W3 Phase B) — additive `pointer_type` alongside the
        // pre-existing {instrument, hint} shape.
        const drill_pointers: { instrument: string; hint: string; pointer_type: DrillPointerType }[] = [
          { instrument: 'ganita_yoga_firings_get', hint: 'firings-authoritative source (ga_yoga_firings): per-yoga strength, bhaṅga/cancellation state, partial-formation %, dāśā-activation windows — cross-check before asserting fired/not-fired (A3/CR-92, R-3).', pointer_type: 'opposing_yoga' },
          { instrument: 'bodha_signals_get', hint: 'signal_type_class=yoga|dosha for salience-ranked cross-validation against L2 Bodha (SC-18: was previously mis-pointed at the non-existent MCP tool name "query_signals").', pointer_type: 'opposing_yoga' },
          { instrument: 'mimamsa_insight_get', hint: 'calibrated_outlook / load_bearing insight units built on top of these firings.', pointer_type: 'other' },
        ]

        let chart_header: ChartHeader | null = null
        try {
          chart_header = await callRegistryCapability('marsys://tool/L1/get_chart_header', {
            chart_id, ayanamsha_id: resolvedAyanamsha,
          }, principal) as ChartHeader
        } catch {
          chart_header = null // frame-safety header is best-effort; never fails the instrument
        }

        const epistemic = buildEpistemicSummary({
          verifiedFraction: grounding.grounding_score,
          note: 'verified_fraction = share of this page\'s rows whose verification_pass_status is in '
            + VERIFIED_PASS_STATUSES.join('|')
            + ' — the one settled definition of verified (envelope.ts VERIFICATION_PASS_STATUS_VOCAB). '
            + 'Previously this note said "two_pass_verified" while the number beside it was computed '
            + 'from a wider two-value check including a bare "pass"; SAMĀPTI Ruling 13 collapsed the two.',
        })

        // D5 coverage receipt (design §10.5): `total` above is a genuine COUNT(*) against
        // the SAME chart_id/category/ayanamsha filters this page was drawn from (get_yoga_dosha.ts) —
        // not a re-guess. family names the filtered set this page is a slice of.
        const coverage: CoverageStamp = {
          family: `yoga_dosha_rows[categories=${(data as { categories?: string[] } | undefined)?.categories?.join(',') ?? 'all'}]`,
          served: rows.length,
          total,
        }

        return dualOutput(envelope(data, 'ganita_yogas_get', {
          offset: resolvedOffset,
          limit: limit ?? 500,
          total,
        }, 'v3', { chart_header, verdict, ranking_basis, grounding, drill_pointers, judgment_flags, epistemic, coverage }))
      } catch (err) {
        return errorOutput('ganita_yogas_get', String(err), { chart_id })
      }
    }
  )

  // ── 8. phala_rectification_get ────────────────────────────────────────────
  server.tool(
    'phala_rectification_get',
    'Retrieve birth-time rectification analysis for a chart (L4 Phala). ' +
    'Returns candidate birth times with plausibility scores, the rectification methodology applied ' +
    '(event-based Tattva Shodhana, Nadi-style rising sign confirmation, Shadbala consistency check), ' +
    'and which Life Event Log entries anchor each candidate time. ' +
    'Use when birth time accuracy is in question before committing to chart interpretation.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe(
        "OPTIONAL ayanamsha filter — short code (lahiri | kp | raman | surya_siddhanta | true_chitra). Omit for ALL ayanamshas."
      ),
      top_k: z.number().int().min(1).max(50).optional().describe('Max candidates (default: 50, max: 50)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, ayanamsha_id, top_k, offset }) => {
      if (!chart_id) return errorOutput('phala_rectification_get', 'chart_id is required')
      try {
        // WP-1.3j serving-bug fix (F-L10-025): phala_rectification stores SHORT ayanamsha codes,
        // NOT the L1 long form. Do NOT run normalizeAyanamsha() here (it maps everything to
        // 'lahiri_chitrapaksha', which matched ZERO rows). Pass ayanamsha_id through as-is; the
        // capability accepts the long form as an alias and omitting it returns all ayanamshas.
        const data = await callRegistryCapability('marsys://tool/L4/query_rectification', {
          chart_id,
          ...(ayanamsha_id ? { ayanamsha_id } : {}),
          top_k: top_k ?? 50, offset: offset ?? 0,
        }, principal)
        return dualOutput(envelope(data, 'phala_rectification_get'))
      } catch (err) {
        return errorOutput('phala_rectification_get', String(err), { chart_id })
      }
    }
  )

  // ── 9. ganita_transit_anchors_get ─────────────────────────────────────────
  server.tool(
    'ganita_transit_anchors_get',
    'Retrieve natal transit anchor data for a chart (L1 Gaṇita — ga_transit_anchors table). ' +
    'Returns the natal sign, house-from-Moon count, and absolute sidereal degree for each of the ' +
    '9 grahas (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu) across all 5 ayanamshas. ' +
    '45 rows per chart. These anchors are the substrate for all Gochara (transit) computations: ' +
    'sign-ingress triggers, degree-exact conjunctions, Vedha/obstruction rules, ' +
    'and Ashtakavarga bindu scoring per transit sign.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha filter (e.g. 'lahiri_chitrapaksha'). Omit for all 5."),
      graha: z.string().optional().describe('Filter to one graha: sun/moon/mars/mercury/jupiter/venus/saturn/rahu/ketu.'),
      limit: z.number().int().min(1).max(25000).optional().describe('Max rows (default: 50, max: 25000)'),
      offset: z.number().int().min(0).optional().describe('Pagination offset (default: 0)'),
    },
    async ({ chart_id, ayanamsha_id, graha, limit, offset }) => {
      if (!chart_id) return errorOutput('ganita_transit_anchors_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L1/get_transit_anchors', {
          chart_id, ayanamsha_id: ayanamsha_id ? normalizeAyanamsha(ayanamsha_id) : undefined,
          graha, limit: limit ?? 50, offset: offset ?? 0,
        }, principal)
        return dualOutput(envelope(data, 'ganita_transit_anchors_get'))
      } catch (err) {
        return errorOutput('ganita_transit_anchors_get', String(err), { chart_id })
      }
    }
  )

  // ── 10. ganita_database_schema_get (Elevation Campaign v2.1 STREAM α Lane-H Task 1) ──────
  // Fronts get_database_schema (registry URI marsys://tool/L1/get_database_schema) — the C3
  // SchemaMap discovery substrate — which was registered in the L1_ganita registry index but
  // had NO MCP-facing tool (the exact dark-asset gap this file exists to close; see the file
  // header comment for the pattern this batch follows). Faithful pass-through: the capability
  // itself already implements pagination (offset/limit/cursor) and declares its own budget_kb
  // param; this tool's dualOutput() wrapper applies the file's standard auto-budget trim on
  // top as a backstop, matching every other tool in this function.
  server.tool(
    'ganita_database_schema_get',
    'Discovery substrate (L1 Gaṇita): every fact_category x fact_subject combination that ' +
    'actually exists in the live chart_facts data model, mechanically enumerated (never ' +
    'hand-authored), each with its observed fact_keys, row_count, and up to 3 sample fact_ids ' +
    'for spot-checking. PAGINATED (offset/limit/cursor, budget_kb) — never an unbounded dump. ' +
    'Also returns concept_aliases: a seeded table mapping common alternate names (e.g. ' +
    '"Gulika"/"Maandi", "sphuta", "panchanga", "mangal") to the real fact_category value(s) ' +
    'they resolve through. Use ganita_concept_locate to resolve a single free-text term ' +
    'instead of scanning this whole substrate. Conforms to the C3 SchemaMap contract.',
    {
      chart_id: z.string().uuid().optional().describe(
        'Chart UUID to enumerate against. Defaults to the canonical chart if omitted — the ' +
        'schema SHAPE is deterministic across charts built by the same writers.'),
      limit: z.number().int().min(1).max(200).optional().describe('Entries per page (default 50, max 200).'),
      cursor: z.string().optional().describe("Opaque pagination cursor from a previous response's next_cursor."),
      budget_kb: z.number().min(1).max(64).optional().describe(
        'Optional response-size ceiling override, 1-64 KB (C1). Tighter than the tool default ' +
        'is honored; wider is clamped to the default.'),
    },
    async ({ chart_id, limit, cursor, budget_kb }) => {
      try {
        const data = await callRegistryCapability('marsys://tool/L1/get_database_schema', {
          ...(chart_id ? { chart_id } : {}),
          ...(limit != null ? { limit } : {}),
          ...(cursor ? { cursor } : {}),
          ...(budget_kb != null ? { budget_kb } : {}),
        }, principal)
        return dualOutput(envelope(data, 'ganita_database_schema_get'))
      } catch (err) {
        return errorOutput('ganita_database_schema_get', String(err), { chart_id })
      }
    }
  )

  // ── 11. ganita_concept_locate (Elevation Campaign v2.1 STREAM α Lane-H Task 1) ───────────
  // Fronts concept_locate (registry URI marsys://tool/L1/concept_locate). Naming: kept the
  // source verb as the type suffix rather than forcing `_get` — mirrors the existing
  // `resolve_entity` → `ref_entity_resolve` precedent in MCP_TOOL_NAMING_STANDARD_v1_0.md §3
  // row 1 (a lookup-by-free-text resolver is not the same shape as a bounded/keyed `_get`).
  server.tool(
    'ganita_concept_locate',
    'Resolve a free-text concept name (English or Sanskrit, e.g. "Gulika", "sphuta", ' +
    '"panchanga", "mangal shadbala") to the real fact_category value(s) it serves through and ' +
    'the MCP tool that serves them (L1 Gaṇita). Tries the seeded alias table first, then ' +
    'falls back to a direct substring match against the live fact_category list. Returns an ' +
    'HONEST MISS (resolved:false, empty_reason naming exactly what was checked) when nothing ' +
    'matches — never a silent empty result. Use this before phrasing any answer as "not in ' +
    'the data" / "doesn\'t exist" (Absence Protocol, EL-07).',
    {
      query: z.string().describe('Free-text concept name to resolve. Required.'),
      chart_id: z.string().uuid().optional().describe(
        'Chart UUID for the live-category fallback pass. Defaults to the canonical chart.'),
    },
    async ({ query, chart_id }) => {
      if (!query) return errorOutput('ganita_concept_locate', 'query is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L1/concept_locate', {
          query, ...(chart_id ? { chart_id } : {}),
        }, principal)
        return dualOutput(envelope(data, 'ganita_concept_locate'))
      } catch (err) {
        return errorOutput('ganita_concept_locate', String(err), { query })
      }
    }
  )

  // ── 12. ganita_planet_get (Elevation Campaign v2.1 STREAM α Lane-H Task 3) ───────────────
  // Fronts query_planet (registry URI marsys://tool/L1/query_planet) — the assembled
  // per-graha entity face (B.10: zero new computation, assembles rows from already-served L1
  // capabilities). ayanamsha_id follows the same optional-only-normalize pattern as
  // ganita_transit_anchors_get above (item 9): forcing a default here would change the
  // capability's own documented omitted-means-unfiltered behavior across the 8 handlers it
  // fans out to.
  server.tool(
    'ganita_planet_get',
    'Canonical assembled-entity face for ONE graha (L1 Gaṇita): sign, house (D1), ' +
    'nakshatra+pada, degree, retrograde/combustion state, dignity chain (exalted/own/friend/' +
    'neutral/enemy/debilitated + functional class), shadbala, avasthas, aspects given/' +
    'received (best-effort matched), yogas this graha participates in (firings-authoritative ' +
    '+ catalog-label, both flagged separately), and its dispositor chain. Gathers ALL of this ' +
    'from already-served L1 capabilities in one call (get_positions/get_dignity/get_strength/' +
    'get_avasthas/get_aspects/get_yoga_dosha/get_yoga_firings/get_dispositors) — no new ' +
    'computation. Use this instead of chaining 7+ individual EAV tool calls for an ' +
    'entity-shaped ("tell me about Saturn") question.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      planet: z.string().describe(
        'Graha name (English, Sanskrit, or 2-3 letter code), e.g. "Saturn", "shani", "SAT". Required.'),
      ayanamsha_id: z.string().optional().describe("Ayanamsha filter (e.g. 'lahiri_chitrapaksha'). Omit for unfiltered."),
    },
    async ({ chart_id, planet, ayanamsha_id }) => {
      if (!chart_id) return errorOutput('ganita_planet_get', 'chart_id is required')
      if (!planet) return errorOutput('ganita_planet_get', 'planet is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L1/query_planet', {
          chart_id, planet,
          ayanamsha_id: ayanamsha_id ? normalizeAyanamsha(ayanamsha_id) : undefined,
        }, principal)
        return dualOutput(envelope(data, 'ganita_planet_get'))
      } catch (err) {
        return errorOutput('ganita_planet_get', String(err), { chart_id, planet })
      }
    }
  )
}
