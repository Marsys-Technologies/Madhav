/** KA-4b: ELECT reader of the scoped-parihāra evaluator (ALGO 3.17 step 3; PLAN §9 L0-M exit).
 * The producer is the sidecar `POST /api/compute/parihara_evaluate` (services/ka_muhurta_seva/
 * parihara_eval.py, contract `parihara_evaluate/1`). This file computes no astrology: it
 * validates the producer's typed envelope and projects each doṣa to `cancelled` (with the
 * citing rule's locator) or `cancellation_unassessed`. Nothing here ever reads "clear".
 *
 * (I) INTERPRETATION: the producer is the existing read-only evaluator route, so no stored
 * table (and no migration) is introduced; the caller names the doṣa targets because the
 * ALGO 3.17 step-2 doṣa ledger has no owning producer yet (B.10: never invent a target).
 */

/** Undertakings whose cancellation rules the classical source scopes (Muhūrta Cintāmaṇi,
 * vivāha chapter: marriage, and upanayana where the verse says so, plus the general clause
 * of PG26 v.34 ṭīkā; PG109 v.65 ṭīkā: the chapter's reckoning is not doṣa-producing elsewhere). */
export const IN_SCOPE_UNDERTAKINGS = ['marriage', 'upanayana', 'general'] as const
export type InScopeUndertaking = (typeof IN_SCOPE_UNDERTAKINGS)[number]

export const PARIHARA_CONTRACT_VERSION = 'parihara_evaluate/1'
/** Per-rule source metadata the producer must carry (parihara_eval.py `_METADATA`). */
export const RULE_METADATA_KEYS = ['dosha_canonical_id', 'scope', 'source_citation', 'source_chunk_id',
  'source_verse', 'conjunction_reading', 'tika_extension', 'priority_rank', 'net_standing', 'extraction_context'] as const

export type CancellationState = 'cancelled' | 'residual' | 'cancellation_unassessed'

export interface EvaluatedRule {
  rule_id: number | string
  dosha_canonical_id: string
  scope: string
  source_citation: string
  source_chunk_id: string
  source_verse: number
  extraction_context: string | null
  conjunction_reading: string | null
  tika_extension: boolean | null
  priority_rank: unknown
  net_standing: string | null
  result: 'applies' | 'does_not_apply' | 'unassessable'
  reason: string | null
}
export interface EvaluatedDosha {
  dosha_canonical_id: string
  state: CancellationState
  reason: string | null
  by_rules: (number | string)[]
}
export interface PariharaEvaluation {
  evaluator_version: string
  rules: EvaluatedRule[]
  dosas: EvaluatedDosha[]
  sky_coverage: { basis: string; complete: boolean }
  [extra: string]: unknown
}

export interface RuleCitation {
  rule_id: number | string
  scope: string
  source_citation: string
  source_chunk_id: string
  source_verse: number
  extraction_context: string | null
  result: EvaluatedRule['result']
}
export interface DoshaCancellation {
  dosha_canonical_id: string
  state: CancellationState
  reason: string | null
  /** Rules that applied for `cancelled`; every rule consulted otherwise. Never empty for `cancelled`. */
  citations: RuleCitation[]
}
export interface ScopedCancellation {
  undertaking: string
  in_scope: boolean
  producer: { contract: typeof PARIHARA_CONTRACT_VERSION; evaluator_version: string | null }
  dosas: DoshaCancellation[]
}

const isRecord = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v)
const text = (v: unknown): v is string => typeof v === 'string' && v.trim() !== ''
const RESULTS = new Set(['applies', 'does_not_apply', 'unassessable'])
const STATES = new Set(['cancelled', 'residual', 'cancellation_unassessed'])

export function isInScope(undertaking: string): undertaking is InScopeUndertaking {
  return (IN_SCOPE_UNDERTAKINGS as readonly string[]).includes(undertaking)
}
/** Rule scopes admissible for an undertaking (parihara_eval.py `scopes_for`, ALGO 3.17 step 3). */
export function scopesFor(undertaking: InScopeUndertaking): string[] {
  return undertaking === 'marriage' || undertaking === 'upanayana' ? [undertaking, 'general'] : ['general']
}

/** Strict shape check. A malformed envelope is a contract violation, never an empty ledger. */
export function parsePariharaEvaluation(value: unknown): PariharaEvaluation | null {
  if (!isRecord(value) || !Array.isArray(value.rules) || !Array.isArray(value.dosas) || !isRecord(value.sky_coverage)) return null
  if (!text(value.evaluator_version)) return null
  for (const r of value.rules) {
    if (!isRecord(r) || !(typeof r.rule_id === 'number' || text(r.rule_id)) || !text(r.dosha_canonical_id)
      || !text(r.scope) || !RESULTS.has(r.result as string)) return null
  }
  for (const d of value.dosas) {
    if (!isRecord(d) || !text(d.dosha_canonical_id) || !STATES.has(d.state as string) || !Array.isArray(d.by_rules)) return null
  }
  return value as unknown as PariharaEvaluation
}

function citation(rule: EvaluatedRule): RuleCitation {
  return { rule_id: rule.rule_id, scope: rule.scope, source_citation: rule.source_citation,
    source_chunk_id: rule.source_chunk_id, source_verse: rule.source_verse,
    extraction_context: rule.extraction_context ?? null, result: rule.result }
}
/** A locator is citable only when display citation, chunk and a positive integer verse are all present. */
function citable(rule: EvaluatedRule): boolean {
  return text(rule.source_citation) && text(rule.source_chunk_id)
    && Number.isInteger(rule.source_verse) && rule.source_verse > 0
}

function unassessed(dosha: string, reason: string, citations: RuleCitation[] = []): DoshaCancellation {
  return { dosha_canonical_id: dosha, state: 'cancellation_unassessed', reason, citations }
}

/** Out-of-scope undertakings and failed producers read `cancellation_unassessed` for every named doṣa. */
export function unassessedFor(undertaking: string, dosasPresent: string[], reason: string, evaluatorVersion: string | null = null): ScopedCancellation {
  return { undertaking, in_scope: isInScope(undertaking),
    producer: { contract: PARIHARA_CONTRACT_VERSION, evaluator_version: evaluatorVersion },
    dosas: [...new Set(dosasPresent)].map(d => unassessed(d, reason)) }
}

/** Project a producer envelope. `cancelled` survives only when a rule of an admissible scope
 * applied and carries a full source locator (N.8: the claim is measured, not inherited). */
export function projectCancellation(undertaking: string, dosasPresent: string[], evaluation: unknown): ScopedCancellation {
  if (!isInScope(undertaking)) return unassessedFor(undertaking, dosasPresent, 'undertaking_out_of_scope')
  const parsed = parsePariharaEvaluation(evaluation)
  if (!parsed) return unassessedFor(undertaking, dosasPresent, 'producer_contract_violation')
  const allowed = new Set(scopesFor(undertaking))
  const byId = new Map(parsed.rules.map(r => [String(r.rule_id), r]))
  const dosas = [...new Set(dosasPresent)].map((target): DoshaCancellation => {
    const row = parsed.dosas.find(d => d.dosha_canonical_id === target)
    if (!row) return unassessed(target, 'dosha_missing_from_evaluation')
    const rules = row.by_rules.map(id => byId.get(String(id)))
    if (rules.some(r => !r || r.dosha_canonical_id !== target)) return unassessed(target, 'producer_contract_violation')
    const consulted = (rules as EvaluatedRule[]).map(citation)
    if (row.state !== 'cancelled') return { dosha_canonical_id: target, state: row.state, reason: row.reason ?? null, citations: consulted }
    const applied = (rules as EvaluatedRule[]).filter(r => r.result === 'applies')
    if (!applied.length) return unassessed(target, 'cancellation_not_supported_by_rule', consulted)
    if (applied.some(r => !allowed.has(r.scope))) return unassessed(target, 'rule_scope_not_admissible', consulted)
    if (!applied.every(citable)) return unassessed(target, 'uncited_cancellation', consulted)
    return { dosha_canonical_id: target, state: 'cancelled', reason: null, citations: applied.map(citation) }
  })
  return { undertaking, in_scope: true, producer: { contract: PARIHARA_CONTRACT_VERSION, evaluator_version: parsed.evaluator_version }, dosas }
}

// ── request + producer client ────────────────────────────────────────────────

export interface CancellationRequest {
  undertaking: string
  candidate: { start_utc: string; end_utc: string }
  location: { lat: number; lon: number; tz_offset_minutes: number }
  location_basis: 'caller' | 'lattice_reference_location'
  dosas_present: string[]
}
/** The producer call; resolves to the raw envelope or throws. Injected so tests never touch a network. */
export type PariharaEvaluator = (request: CancellationRequest) => Promise<unknown>

/** Explicit inputs only: no default place, undertaking, interval or wildcard target (B.10). */
export function parseCancellationRequest(value: unknown): CancellationRequest | string {
  if (!isRecord(value)) return 'scoped_cancellation must be an object'
  const { undertaking, candidate, location, dosas_present } = value
  if (!text(undertaking)) return 'scoped_cancellation.undertaking is required'
  if (!isRecord(candidate) || !text(candidate.start_utc) || !text(candidate.end_utc)) return 'scoped_cancellation.candidate needs start_utc and end_utc'
  if (!isRecord(location) || typeof location.lat !== 'number' || typeof location.lon !== 'number'
    || !Number.isInteger(location.tz_offset_minutes) || !Number.isFinite(location.lat) || !Number.isFinite(location.lon)) {
    return 'scoped_cancellation.location needs lat, lon and integer tz_offset_minutes'
  }
  if (!Array.isArray(dosas_present) || !dosas_present.length
    || dosas_present.some(d => !text(d) || d.includes('*'))) return 'scoped_cancellation.dosas_present must name explicit targets'
  const basis = value.location_basis ?? 'caller'
  if (basis !== 'caller' && basis !== 'lattice_reference_location') return 'scoped_cancellation.location_basis is invalid'
  return { undertaking, candidate: { start_utc: candidate.start_utc, end_utc: candidate.end_utc },
    location: { lat: location.lat, lon: location.lon, tz_offset_minutes: location.tz_offset_minutes as number },
    location_basis: basis, dosas_present: dosas_present as string[] }
}

/** Sidecar producer client. Any failure is a named unassessed reason, never "no cancellation needed". */
export const sidecarEvaluator: PariharaEvaluator = async request => {
  const base = process.env.PYTHON_SIDECAR_URL
  if (!base) throw new Error('producer_not_configured')
  const response = await fetch(`${base}/api/compute/parihara_evaluate`, {
    method: 'POST', signal: AbortSignal.timeout(20_000),
    headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.PYTHON_SIDECAR_API_KEY ?? '' },
    body: JSON.stringify(request),
  })
  if (!response.ok) throw new Error(response.status === 503 ? 'parihara_source_unavailable' : 'producer_unavailable')
  return response.json()
}

/** Out-of-scope undertakings never reach the producer; its `general` fallback must not read as an answer. */
export async function evaluateScopedCancellation(request: CancellationRequest, evaluate: PariharaEvaluator = sidecarEvaluator): Promise<ScopedCancellation> {
  if (!isInScope(request.undertaking)) return unassessedFor(request.undertaking, request.dosas_present, 'undertaking_out_of_scope')
  let envelope: unknown
  try { envelope = await evaluate(request) } catch (error) {
    const reason = error instanceof Error && /^[a-z_]+$/.test(error.message) ? error.message : 'producer_unavailable'
    return unassessedFor(request.undertaking, request.dosas_present, reason)
  }
  return projectCancellation(request.undertaking, request.dosas_present, envelope)
}
