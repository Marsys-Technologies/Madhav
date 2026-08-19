/**
 * P0-C / RF-1 — the golden-stream scenario corpus for `/api/pariprashna`.
 *
 * WHAT THIS IS
 * ────────────
 * A pure, mock-free data module describing the INPUTS to one run of the real
 * `POST` handler: the request body, the auth/flag/DB world it runs against, the
 * planner outcome, the retrieval outcomes, and the exact adapter event sequence
 * the synthesis stream yields. `route_golden_stream.test.ts` mounts these
 * against the REAL route and records the resulting wire stream + boundary
 * side-effects as a committed golden.
 *
 * ── AN HONEST NOTE ON "THE 12-FIXTURE CORPUS" (read this before citing it) ───
 * RF-1 asks for equality "over the 12-fixture corpus + captured real streams".
 * `platform/tests/pariprashna/fixtures/*.json` IS that 12-fixture corpus — but
 * those fixtures are **client-side wire recordings**: arrays of already-emitted
 * `PariprashnaEvent`s with `delay_ms` pacing, built by
 * `scripts/replay/build_fixtures.ts` to drive the CLIENT reducer and the replay
 * server. They are OUTPUTS of a route, not INPUTS to one. Feeding them to
 * `POST` is not possible — the route consumes an HTTP request and an adapter
 * event stream, neither of which a fixture contains.
 *
 * So the bridge is explicit and named, never silent: each of the 12 fixtures
 * has a scenario below whose `derived_from` names it and whose `note` states
 * which behaviour of that fixture this scenario reproduces AT THE ROUTE. The
 * route-level scenarios (`derived_from: 'route-branch'`) cover the control-flow
 * branches the 12 fixtures cannot express at all (auth, flag-off, planner
 * clarification/fault, NO-LEAKAGE strip, abort, fatal). Anyone auditing the
 * equality claim should read `derived_from` as "modelled on", never as "the
 * fixture was replayed through the route".
 *
 * NO real deployed stream has been captured into this corpus — the
 * `PARIPRASHNA_STREAM_CAPTURE` path needs a deployed environment and a live
 * reading. That half of RF-1's sentence is UNMET here and is reported as such.
 */

export const HARNESS_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/** One step of the mocked adapter / agentic-loop event stream. */
export type AdapterStep =
  | { kind: 'text'; text: string }
  | { kind: 'thinking'; text: string }
  | { kind: 'tool_start'; id: string; name: string }
  | { kind: 'tool_complete'; id: string; name: string }
  | { kind: 'error'; error: string }
  /** The stream throws mid-flight (adapter fault after partial prose). */
  | { kind: 'throw'; message: string }
  /** The client disconnects: aborts the request signal before the next event. */
  | { kind: 'abort' }

export interface PlannerSpec {
  outcome: 'plan' | 'clarification_needed' | 'fault'
  /** clarification_needed */
  question?: string
  /** fault */
  reason?: string
  retryable?: boolean
  /** plan */
  toolCalls?: Array<{ tool_name: string; token_budget: number; priority: 1 | 2 | 3 }>
  queryClass?: string
  domains?: string[]
  withScopeTuple?: boolean
}

export interface RouteScenario {
  name: string
  /** A fixture name from tests/pariprashna/fixtures, or 'route-branch'. */
  derived_from: string
  note: string

  // ── Request ────────────────────────────────────────────────────────────────
  /** Raw body string; when set it REPLACES `body` (used for the malformed-JSON case). */
  rawBody?: string
  body?: Record<string, unknown>

  // ── World ──────────────────────────────────────────────────────────────────
  authenticated?: boolean
  flagEnabled?: boolean
  chartFound?: boolean
  permission?: 'view' | 'deny'
  /** Present + matching chart, present + mismatched chart, or absent. */
  existingConversation?: 'match' | 'chart-mismatch' | 'missing'
  /** Make the charts SELECT throw — drives the fatal in-stream catch. */
  throwOnChartQuery?: boolean
  insertConversationError?: 'duplicate' | 'fatal'

  planner: PlannerSpec
  /** tool name -> number of results, or 'error' to make dispatch throw. */
  toolOutcomes?: Record<string, number | 'error' | 'unknown-tool'>

  adapter: AdapterStep[]
  /** Informational: the scenario models a provider that re-enters retrieval. */
  agenticLoop?: boolean
  /**
   * Remove this provider's entry from LOOP_CONFIG_BY_PROVIDER so the route
   * takes the plain `adapter.chat(...)` branch instead of `runAgenticLoop`.
   */
  disableLoopConfig?: boolean

  citationGate?: {
    gateResult: 'PASS' | 'WARN' | 'ERROR'
    gateReason: string
    layer1Count: number
    layer2Verified: number
  }
  /** Make the citation validator throw (the swallowed-error branch). */
  citationGateThrows?: boolean

  /** Emit a provenance drift (chart_rebuilt flag). */
  provenanceDrift?: boolean
  /** MSR snippet rows the writer's fetchMsrSnippets resolves. */
  msrSnippets?: Record<string, { name: string; description: string }>
}

const PROSE_PLAIN =
  'Saturn occupies the tenth from the Ascendant with directional strength, and the ' +
  'current period lord aspects it from the fourth.'

/** Prose carrying real citation sentinels the citation extractor recognises. */
const PROSE_CITED =
  'The tenth-house pattern is corroborated across layers [1]. The dasha lord adds a ' +
  'second, independent confirmation [2], and the transit window closes the loop [3].'

/** Prose that trips the register-leak lint (internal identifiers in reader prose). */
const PROSE_LEAKY =
  'The MSR signal SIG.MSR.042 and the CDLM cross-domain matrix both point the same way.'

/** Prose the prediction detector scores at or above the 0.5 floor. */
const PROSE_PREDICTIVE =
  'Between March 2027 and September 2027 a decisive career elevation is likely, and ' +
  'the window will open around the Jupiter sub-period.'

function planSpec(over: Partial<PlannerSpec> = {}): PlannerSpec {
  return {
    outcome: 'plan',
    toolCalls: [
      { tool_name: 'msr_sql', token_budget: 600, priority: 1 },
      { tool_name: 'chart_facts_query', token_budget: 400, priority: 2 },
    ],
    queryClass: 'holistic',
    domains: ['career'],
    ...over,
  }
}

function baseBody(over: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    chartId: HARNESS_CHART_ID,
    stack: 'gemini',
    messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text: 'How does my career unfold?' }] }],
    ...over,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// A · The twelve fixture-derived scenarios
// ─────────────────────────────────────────────────────────────────────────────

const FIXTURE_DERIVED: RouteScenario[] = [
  {
    name: 'single-pass',
    derived_from: 'single-pass',
    note: 'One retrieval pass, one committed prose block, clean turn.close — the fixture’s shape reproduced at the route.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
  },
  {
    name: 'adaptive-3-pass',
    derived_from: 'adaptive-3-pass',
    note: 'Engine re-enters retrieval twice after prose → pass 2 and pass 3 with seam.open/seam.set, exactly the route’s control-flow pass boundary.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    agenticLoop: true,
    adapter: [
      { kind: 'text', text: 'First pass reading. ' },
      { kind: 'tool_start', id: 't1', name: 'msr_sql' },
      { kind: 'tool_complete', id: 't1', name: 'msr_sql' },
      { kind: 'text', text: 'Second pass reading. ' },
      { kind: 'tool_start', id: 't2', name: 'chart_facts_query' },
      { kind: 'tool_complete', id: 't2', name: 'chart_facts_query' },
      { kind: 'text', text: 'Third pass reading.' },
    ],
  },
  {
    name: 'citation-dense',
    derived_from: 'citation-dense',
    note: 'Prose dense in citation sentinels → citation.define events + canonical citation parts + MSR snippet resolution.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 9, chart_facts_query: 4 },
    adapter: [{ kind: 'text', text: PROSE_CITED }],
    msrSnippets: {
      'SIG.MSR.042': { name: 'Moon–Purva Bhadrapada', description: 'Nakshatra placement anchor' },
      'SIG.MSR.117': { name: 'Saturn dig-bala', description: 'Tenth-house directional strength' },
    },
  },
  {
    name: 'honest-gap',
    derived_from: 'honest-gap',
    note: 'Every retrieval tool errors → zero evidence, citation gate WARN. The gap is reported (flag + grade), never silently absorbed.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 'error', chart_facts_query: 'error' },
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
    citationGate: { gateResult: 'WARN', gateReason: 'no layer-1 citations found', layer1Count: 0, layer2Verified: 0 },
  },
  {
    name: 'stop-mid-pass',
    derived_from: 'stop-mid-pass',
    note: 'Client stops the turn mid-block → request.signal aborts, the open block commits, turn.close status=aborted.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [
      { kind: 'text', text: 'Partial reading before the stop' },
      { kind: 'abort' },
      { kind: 'text', text: 'this text must never reach the wire' },
    ],
  },
  {
    name: 'disconnect-mid-block',
    derived_from: 'disconnect-mid-block',
    note: 'Adapter stream throws mid-block → synthesis_stream_error flag; the partial block still commits (no lost prose).',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [
      { kind: 'text', text: 'A reading interrupted by transport failure' },
      { kind: 'throw', message: 'ECONNRESET from provider' },
    ],
  },
  {
    name: 'unclosed-sentinel',
    derived_from: 'unclosed-sentinel',
    note: 'Prose containing an unterminated citation sentinel → citation gate ERROR path (grade + flag), turn still closes ok.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [{ kind: 'text', text: 'The pattern holds [1 and the window opens next spring.' }],
    citationGate: { gateResult: 'ERROR', gateReason: 'unterminated citation sentinel', layer1Count: 1, layer2Verified: 0 },
  },
  {
    name: 'malformed-sentinel-variants',
    derived_from: 'malformed-sentinel-variants',
    note: 'Malformed sentinels plus raw internal identifiers in reader prose → register_leak_scrubbed on the delta AND the block backstop.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [
      { kind: 'text', text: PROSE_LEAKY },
      { kind: 'text', text: ' Also [x] and [ ] and [99].' },
    ],
  },
  {
    name: 'giant-table',
    derived_from: 'giant-table',
    note: 'One very large prose block delivered as several big deltas — the block-accumulation path under volume.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 12, chart_facts_query: 8 },
    adapter: [
      { kind: 'text', text: '| House | Lord | Dignity |\n' },
      { kind: 'text', text: Array.from({ length: 12 }, (_, i) => `| ${i + 1} | lord-${i + 1} | own |`).join('\n') },
      { kind: 'text', text: '\nThe table above summarises the twelve houses.' },
    ],
  },
  {
    name: '1-byte-trickle',
    derived_from: '1-byte-trickle',
    note: 'One character per delta — maximal delta count, proving per-delta lint + accumulation are per-chunk correct.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: 'Saturn rises.'.split('').map((c) => ({ kind: 'text' as const, text: c })),
  },
  {
    name: 'gemini-slabs',
    derived_from: 'gemini-slabs',
    note: 'Two very large slabs rather than many small deltas — the Gemini delivery profile.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [
      { kind: 'text', text: PROSE_PLAIN.repeat(4) },
      { kind: 'text', text: PROSE_CITED.repeat(2) },
    ],
  },
  {
    name: '3s-stall',
    derived_from: '3s-stall',
    note: 'A thinking block precedes prose (the stall the fixture paces as dead air) → thinking block opens/commits then prose block opens.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [
      { kind: 'thinking', text: 'Weighing the tenth-house testimony against the dasha sequence.' },
      { kind: 'text', text: PROSE_PLAIN },
    ],
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// B · Route control-flow branches the fixture corpus cannot express
// ─────────────────────────────────────────────────────────────────────────────

const ROUTE_BRANCHES: RouteScenario[] = [
  {
    name: 'branch-unauthenticated',
    derived_from: 'route-branch',
    note: 'No user → pre-stream HTTP 401, no stream opened.',
    body: baseBody(),
    authenticated: false,
    planner: planSpec(),
    adapter: [],
  },
  {
    name: 'branch-flag-off',
    derived_from: 'route-branch',
    note: 'PARIPRASHNA_ENABLED off → deliberate 404, the wave’s rollback design.',
    body: baseBody(),
    flagEnabled: false,
    planner: planSpec(),
    adapter: [],
  },
  {
    name: 'branch-malformed-json',
    derived_from: 'route-branch',
    note: 'Unparseable body → HTTP 400 before any stream byte.',
    rawBody: '{not json',
    planner: planSpec(),
    adapter: [],
  },
  {
    name: 'branch-missing-fields',
    derived_from: 'route-branch',
    note: 'chartId/messages absent → HTTP 400.',
    body: { stack: 'gemini' },
    planner: planSpec(),
    adapter: [],
  },
  {
    name: 'branch-invalid-chart-id',
    derived_from: 'route-branch',
    note: 'Non-UUID chartId → HTTP 400 INVALID_CHART_ID.',
    body: baseBody({ chartId: 'not-a-uuid' }),
    planner: planSpec(),
    adapter: [],
  },
  {
    name: 'branch-chart-not-found',
    derived_from: 'route-branch',
    note: 'Chart row absent → in-stream CHART_NOT_FOUND error event (never an HTTP status).',
    body: baseBody(),
    chartFound: false,
    planner: planSpec(),
    adapter: [],
  },
  {
    name: 'branch-forbidden',
    derived_from: 'route-branch',
    note: 'authorizeChartAccess denies → in-stream FORBIDDEN error event.',
    body: baseBody(),
    permission: 'deny',
    planner: planSpec(),
    adapter: [],
  },
  {
    name: 'branch-conversation-not-found',
    derived_from: 'route-branch',
    note: 'Client supplied a conversationId that does not resolve → in-stream CONVERSATION_NOT_FOUND.',
    body: baseBody({ conversationId: '11111111-2222-3333-4444-555555555555' }),
    existingConversation: 'missing',
    planner: planSpec(),
    adapter: [],
  },
  {
    name: 'branch-existing-conversation',
    derived_from: 'route-branch',
    note: 'Second turn on an existing conversation → no eager insert, isFirstTurn false.',
    body: baseBody({ conversationId: '11111111-2222-3333-4444-555555555555' }),
    existingConversation: 'match',
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
  },
  {
    name: 'branch-planner-clarification',
    derived_from: 'route-branch',
    note: 'Planner asks for clarification → flag + a single clar-0 block + phase end, turn.close ok, no synthesis.',
    body: baseBody(),
    planner: { outcome: 'clarification_needed', question: 'Which career decision do you mean?' },
    adapter: [],
  },
  {
    name: 'branch-planner-fault-retryable',
    derived_from: 'route-branch',
    note: 'Transient planner fault → PLANNER_TRANSIENT in-stream error, retryable true.',
    body: baseBody(),
    planner: { outcome: 'fault', reason: 'upstream 503', retryable: true },
    adapter: [],
  },
  {
    name: 'branch-planner-fault-permanent',
    derived_from: 'route-branch',
    note: 'Invalid plan → PLANNER_INVALID_PLAN in-stream error, retryable false.',
    body: baseBody(),
    planner: { outcome: 'fault', reason: 'schema violation', retryable: false },
    adapter: [],
  },
  {
    name: 'branch-no-leakage-strip',
    derived_from: 'route-branch',
    note: 'Planner authorises a real calibration_context_only capability → NO-LEAKAGE strip flag with a COUNT only, tool never dispatched.',
    body: baseBody(),
    planner: planSpec({
      toolCalls: [
        { tool_name: 'msr_sql', token_budget: 600, priority: 1 },
        { tool_name: 'lel_query', token_budget: 400, priority: 2 },
      ],
    }),
    toolOutcomes: { msr_sql: 3 },
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
  },
  {
    name: 'branch-empty-synthesis',
    derived_from: 'route-branch',
    note: 'Adapter yields nothing → empty_synthesis flag, persistence skipped, honest gap surfaced.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [],
  },
  {
    name: 'branch-deep-dive',
    derived_from: 'route-branch',
    note: 'reading_depth=deep_dive → dasha_context_required forced, wider loop cap, echoed on turn.open.',
    body: baseBody({ reading_depth: 'deep_dive', length_tier: 'exhaustive' }),
    planner: planSpec({ withScopeTuple: true }),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    agenticLoop: true,
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
  },
  {
    name: 'branch-completeness-receipt',
    derived_from: 'route-branch',
    note: 'Plan carries a scope_tuple → completeness receipt built and reported as served/total (never "[object Object]").',
    body: baseBody(),
    planner: planSpec({ withScopeTuple: true }),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
  },
  {
    name: 'branch-prediction-candidates',
    derived_from: 'route-branch',
    note: 'Predictive prose → prediction_candidate flags, canonical prediction_candidate parts, SAMĪKṢĀ detected-row capture.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [{ kind: 'text', text: PROSE_PREDICTIVE }],
  },
  {
    name: 'branch-provenance-drift',
    derived_from: 'route-branch',
    note: 'Chart rebuilt since the previous turn → chart_rebuilt info flag carrying only the closed-lexicon label.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
    provenanceDrift: true,
  },
  {
    name: 'branch-adapter-error-event',
    derived_from: 'route-branch',
    note: 'Adapter emits an in-band error event → adapter_error warn flag, stream continues.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [
      { kind: 'text', text: 'Opening statement. ' },
      { kind: 'error', error: 'provider soft error' },
      { kind: 'text', text: 'Continued after the soft error.' },
    ],
  },
  {
    name: 'branch-unknown-tool',
    derived_from: 'route-branch',
    note: 'An authorised tool the registry cannot resolve → activity error, no dispatch, turn unaffected.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 'unknown-tool' },
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
  },
  {
    name: 'branch-citation-gate-throws',
    derived_from: 'route-branch',
    note: 'Citation validator throws → swallowed, no grade emitted, turn still closes ok (the documented catch).',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
    citationGateThrows: true,
  },
  {
    name: 'branch-fatal-in-stream',
    derived_from: 'route-branch',
    note: 'The charts SELECT throws → INTERNAL in-stream error via the fatal catch, turn.close status=error.',
    body: baseBody(),
    throwOnChartQuery: true,
    planner: planSpec(),
    adapter: [],
  },
  {
    name: 'branch-non-agentic-adapter',
    derived_from: 'route-branch',
    note: 'No loop config for the provider → the route takes the plain adapter.chat(...) branch instead of runAgenticLoop.',
    body: baseBody(),
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    disableLoopConfig: true,
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
  },
  {
    name: 'branch-conversation-insert-duplicate',
    derived_from: 'route-branch',
    note: 'Eager insert hits a duplicate-key race → tolerated, the turn proceeds (the documented benign path).',
    body: baseBody(),
    insertConversationError: 'duplicate',
    planner: planSpec(),
    toolOutcomes: { msr_sql: 3, chart_facts_query: 2 },
    adapter: [{ kind: 'text', text: PROSE_PLAIN }],
  },
  {
    name: 'branch-conversation-insert-fatal',
    derived_from: 'route-branch',
    note: 'Eager insert fails for a non-duplicate reason → CONVERSATION_INIT_FAILED in-stream error, retryable.',
    body: baseBody(),
    insertConversationError: 'fatal',
    planner: planSpec(),
    adapter: [],
  },
]

export const ROUTE_SCENARIOS: RouteScenario[] = [...FIXTURE_DERIVED, ...ROUTE_BRANCHES]

/** The 12 fixture names this corpus claims coverage of (asserted by the test). */
export const FIXTURE_CORPUS_NAMES = FIXTURE_DERIVED.map((s) => s.derived_from)

export function scenarioByName(name: string): RouteScenario {
  const s = ROUTE_SCENARIOS.find((x) => x.name === name)
  if (!s) throw new Error(`unknown scenario: ${name}`)
  return s
}

/** The scope tuple attached when `withScopeTuple` is set. */
export const HARNESS_SCOPE_TUPLE = {
  intent: 'domain_assessment',
  domains: ['career'],
  width: 'standard',
  depth: 'standard',
  horizon: 'near',
  intervention: 'none',
  entitlement: 'native',
} as const
