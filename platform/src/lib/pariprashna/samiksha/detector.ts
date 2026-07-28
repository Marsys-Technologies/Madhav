/**
 * SAMĪKṢĀ two-stage prediction detector — PB-3 (SAMĪKṢĀ) lane L-2.
 *
 * Design authority: PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §14.2.
 *
 * §14.2 keeps the existing two-stage design and EXTENDS it to emit a structured
 * candidate. The two stages, faithfully:
 *
 *   Stage 1 — synchronous regex pass (sub-millisecond). This is the EXISTING,
 *     shipped detector `detectPredictionCandidates` (src/lib/ppl/prediction_detector.ts),
 *     reused verbatim — this module does NOT re-implement sentence/horizon
 *     detection. It only ENRICHES each raw hit into the §14.2 structured shape.
 *
 *   Stage 2 — asynchronous classifier, post-stream. Modelled here as an
 *     INJECTABLE `CandidateClassifier` so a real (Haiku) classifier can be
 *     plugged in later, defaulting to a DETERMINISTIC enrichment (project rule
 *     "deterministic-first", CLAUDE.md §N.4). The default derives domain,
 *     direction, the window's ISO date bounds, any explicitly-stated
 *     probability, and technique/grounding references from the turn's citation
 *     parts. Nothing is fabricated — an unknown field is an honest `null`/`[]`
 *     (§N.7 rule 6), never a plausible-sounding default.
 *
 * ISOMORPHIC (pure TS, no `server-only`, no DB) so the enrichment + window/
 * date arithmetic are unit-testable with zero infrastructure.
 *
 * GROUNDING (§14.2): "the grounding refs come free once citations are parts."
 * This module takes the turn's already-detected `citation` message-part bodies
 * (PB-2 `CitationBody`: `{ index, signal_id, layer, ... }`) and maps their
 * `signal_id`s into `grounding_fact_ids` — it reuses PB-1's citation pipeline
 * rather than inventing a parallel citation concept.
 */

import {
  detectPredictionCandidates as detectStage1Raw,
  type PredictionCandidate as RawCandidate,
} from '@/lib/ppl/prediction_detector'

// ---------------------------------------------------------------------------
// The §14.2 structured candidate
// ---------------------------------------------------------------------------

/**
 * The structured candidate §14.2 mandates. Field names are verbatim from the
 * design doc's schema block. `window_start`/`window_end` are ISO `yyyy-mm-dd`
 * (inclusive lower / exclusive upper, matching the ledger daterange) or null
 * when the horizon text carries no resolvable window. `confidence_stated` is a
 * point probability in [0,1] present ONLY when the prose literally stated one.
 */
export interface StructuredPredictionCandidate {
  claim_text: string
  domain: string | null
  window_start: string | null
  window_end: string | null
  direction: string | null
  /** Present only when the prose stated a probability; never invented. */
  confidence_stated?: number
  technique_refs: string[]
  grounding_fact_ids: string[]
  /** Stage-1 heuristic score (0–1) — carried for the review surface's ordering. */
  score: number
  /** Raw horizon phrase Stage 1 matched (audit / UI hint). */
  horizon_text: string | null
}

/** A minimal projection of a PB-2 `citation` message-part body (schema.ts
 *  CitationBody) — only the fields the grounding map needs. */
export interface CitationRef {
  signal_id: string
  layer?: string
}

export interface DetectInput {
  /** The settled turn's full assistant prose. */
  text: string
  /** The turn's citation parts (PB-2 `citation` kind bodies). */
  citations?: CitationRef[]
  /** The reading's date (ISO yyyy-mm-dd) — the anchor relative-horizons resolve
   *  against ("in 2 years" from WHEN). Defaults to today (UTC). */
  nowDate?: string
  /** Minimum Stage-1 score to keep. Mirrors the route's live 0.5 filter. */
  minScore?: number
}

/**
 * Stage 2 classifier seam. A real post-stream classifier implements this to
 * refine/override the deterministic enrichment. Returns a (possibly) revised
 * candidate; returning `null` drops the candidate (false positive). The default
 * classifier is the deterministic enrichment itself.
 */
export type CandidateClassifier = (
  raw: RawCandidate,
  base: StructuredPredictionCandidate,
) => Promise<StructuredPredictionCandidate | null> | StructuredPredictionCandidate | null

// ---------------------------------------------------------------------------
// Stage 2 (deterministic) — domain, direction, confidence, techniques
// ---------------------------------------------------------------------------

/** Domain keyword buckets. First bucket with a hit wins; no hit → null (honest). */
const DOMAIN_KEYWORDS: ReadonlyArray<readonly [string, readonly string[]]> = [
  ['career', ['career', 'job', 'occupation', 'profession', 'promotion', 'work', 'business', 'employment', 'vocation', 'leadership role']],
  ['marriage', ['marriage', 'marry', 'wedding', 'spouse', 'partner', 'relationship', 'union', 'engagement']],
  ['health', ['health', 'illness', 'disease', 'surgery', 'recovery', 'ailment', 'injury', 'wellbeing']],
  ['wealth', ['wealth', 'money', 'finance', 'financial', 'income', 'gains', 'fortune', 'investment', 'property purchase', 'assets']],
  ['education', ['education', 'study', 'studies', 'degree', 'exam', 'academic', 'university', 'course']],
  ['property', ['property', 'house', 'home', 'land', 'real estate', 'residence', 'relocation', 'move abroad']],
  ['progeny', ['child', 'children', 'progeny', 'pregnancy', 'conception', 'offspring']],
  ['travel', ['travel', 'journey', 'abroad', 'foreign', 'overseas', 'voyage', 'trip']],
  ['spirituality', ['spiritual', 'moksha', 'renunciation', 'sadhana', 'pilgrimage', 'dharma']],
  ['litigation', ['litigation', 'lawsuit', 'court', 'legal', 'dispute', 'settlement']],
]

const POSITIVE_KEYWORDS = [
  'gain', 'gains', 'rise', 'rises', 'success', 'successful', 'promotion', 'promoted',
  'favorable', 'favourable', 'opportunity', 'growth', 'flourish', 'prosper', 'benefit',
  'elevation', 'achievement', 'advance', 'improve', 'improvement', 'auspicious', 'windfall',
]
const NEGATIVE_KEYWORDS = [
  'loss', 'losses', 'decline', 'illness', 'obstacle', 'obstacles', 'delay', 'delays',
  'setback', 'difficulty', 'difficulties', 'struggle', 'conflict', 'separation', 'accident',
  'downturn', 'reversal', 'hardship', 'adversity', 'inauspicious', 'crisis',
]

/** Map a citation layer / signal namespace onto a technique label, best-effort.
 *  Also inspects claim text for named techniques. Empty when nothing resolves. */
const TECHNIQUE_KEYWORDS: ReadonlyArray<readonly [string, readonly string[]]> = [
  ['vimshottari_dasha', ['dasha', 'daśā', 'mahadasha', 'antardasha', 'bhukti', 'vimshottari']],
  ['gochara_transit', ['transit', 'gochara', 'gocara', 'sade sati', 'saturn transit', 'jupiter transit']],
  ['tajaka_annual', ['tajaka', 'varshaphala', 'annual chart', 'muntha']],
  ['ashtakavarga', ['ashtakavarga', 'aṣṭakavarga', 'bindu', 'sav']],
  ['divisional_varga', ['navamsa', 'navāṃśa', 'dasamsa', 'daśāṃśa', 'varga', 'divisional']],
]

function inferDomain(text: string): string | null {
  const lower = text.toLowerCase()
  for (const [domain, kws] of DOMAIN_KEYWORDS) {
    if (kws.some((k) => lower.includes(k))) return domain
  }
  return null
}

/** positive / negative / null (honest — never a favourable-sounding default). */
function inferDirection(text: string): string | null {
  const lower = text.toLowerCase()
  const pos = POSITIVE_KEYWORDS.some((k) => new RegExp(`\\b${k}\\b`).test(lower))
  const neg = NEGATIVE_KEYWORDS.some((k) => new RegExp(`\\b${k}\\b`).test(lower))
  if (pos && !neg) return 'positive'
  if (neg && !pos) return 'negative'
  return null // mixed or absent → we do not know; §N.7 rule 6
}

function inferTechniques(text: string, citations: CitationRef[]): string[] {
  const lower = text.toLowerCase()
  const found = new Set<string>()
  for (const [technique, kws] of TECHNIQUE_KEYWORDS) {
    if (kws.some((k) => lower.includes(k))) found.add(technique)
  }
  // Citation signal namespaces can also name a technique (e.g. a dasha signal id).
  for (const c of citations) {
    const id = c.signal_id.toLowerCase()
    for (const [technique, kws] of TECHNIQUE_KEYWORDS) {
      if (kws.some((k) => id.includes(k.replace(/\s+/g, '_')))) found.add(technique)
    }
  }
  return [...found]
}

/**
 * Parse an explicitly-stated probability from prose. Returns a point in [0,1],
 * or null when none is stated. Only literal numbers count — verbal hedges
 * ("highly likely") are deliberately NOT mapped to a number (that would be
 * inventing precision — T-8 / §14.6 "n=7 is precision theater" discipline).
 */
export function parseStatedConfidence(text: string): number | null {
  // "70% chance", "an 80 % probability", "70 percent likely"
  const pct = text.match(/(\d{1,3})\s*%/) ?? text.match(/(\d{1,3})\s*percent\b/i)
  if (pct) {
    const n = Number(pct[1])
    if (n >= 0 && n <= 100) return n / 100
  }
  // "0.7 probability", "probability of 0.65", "confidence 0.8"
  const dec = text.match(/(?:probability|confidence|likelihood|odds)\D{0,12}(0?\.\d+)/i)
    ?? text.match(/(0?\.\d+)\s+(?:probability|confidence|likelihood)/i)
  if (dec) {
    const n = Number(dec[1])
    if (n >= 0 && n <= 1) return n
  }
  return null
}

// ---------------------------------------------------------------------------
// Window parsing — horizon text → { start, end } ISO daterange bounds
// ---------------------------------------------------------------------------

function iso(y: number, m: number, d: number): string {
  const mm = String(m).padStart(2, '0')
  const dd = String(d).padStart(2, '0')
  return `${y}-${mm}-${dd}`
}

/** Add whole months to an ISO date, clamping day to the 1st (window bounds are
 *  month-granular; day precision would be false precision from vague prose). */
function addMonths(isoDate: string, months: number): string {
  const [y, m] = isoDate.split('-').map(Number)
  const total = (y * 12 + (m - 1)) + months
  const ny = Math.floor(total / 12)
  const nm = (total % 12) + 1
  return iso(ny, nm, 1)
}

/**
 * Resolve a Stage-1 horizon phrase into a `[start, end)` ISO daterange, anchored
 * at `nowDate` for relative phrases. Returns null when the phrase carries no
 * resolvable calendar window. Month-granular by design (vague astrological
 * windows do not carry day precision — inventing it would violate B.10's spirit).
 */
export function parseWindow(
  horizon: string | null,
  nowDate: string,
): { start: string; end: string } | null {
  if (!horizon) return null
  const h = horizon.toLowerCase().trim()
  const nowY = Number(nowDate.slice(0, 4))

  // "mid-2027" / "early 2027" / "late-2027"
  const seasonal = h.match(/\b(early|mid|late)[-\s](\d{4})\b/)
  if (seasonal) {
    const y = Number(seasonal[2])
    if (seasonal[1] === 'early') return { start: iso(y, 1, 1), end: iso(y, 5, 1) }
    if (seasonal[1] === 'mid') return { start: iso(y, 5, 1), end: iso(y, 9, 1) }
    return { start: iso(y, 9, 1), end: iso(y + 1, 1, 1) } // late
  }

  // "Q3 2027"
  const quarter = h.match(/\bq([1-4])\s*(\d{4})\b/)
  if (quarter) {
    const q = Number(quarter[1])
    const y = Number(quarter[2])
    const startM = (q - 1) * 3 + 1
    return { start: iso(y, startM, 1), end: addMonths(iso(y, startM, 1), 3) }
  }

  // "in/within/over the next N days|weeks|months|years" (relative to now)
  const relative = h.match(/\b(?:in|within|over|during)\s+(?:the\s+next\s+)?(\d+)\s+(day|week|month|year)s?\b/)
    ?? h.match(/\b(?:the\s+)?next\s+(\d+)\s+(day|week|month|year)s?\b/)
  if (relative) {
    const n = Number(relative[1])
    const unit = relative[2]
    const months = unit === 'year' ? n * 12 : unit === 'month' ? n : unit === 'week' ? Math.max(1, Math.round((n * 7) / 30)) : Math.max(1, Math.round(n / 30))
    return { start: nowDate, end: addMonths(nowDate, months) }
  }

  // "this year" / "next year"
  if (/\bthis\s+year\b/.test(h)) return { start: iso(nowY, 1, 1), end: iso(nowY + 1, 1, 1) }
  if (/\bnext\s+year\b/.test(h)) return { start: iso(nowY + 1, 1, 1), end: iso(nowY + 2, 1, 1) }

  // "by 2027" / "before 2027" → from now to the end of that year
  const byYear = h.match(/\b(?:by|before)\s+(\d{4})\b/)
  if (byYear) {
    const y = Number(byYear[1])
    return { start: nowDate, end: iso(y + 1, 1, 1) }
  }

  // "around 2027" / "in 2027" / bare "2027" → the whole calendar year
  const bareYear = h.match(/\b(\d{4})\b/)
  if (bareYear) {
    const y = Number(bareYear[1])
    return { start: iso(y, 1, 1), end: iso(y + 1, 1, 1) }
  }

  return null
}

// ---------------------------------------------------------------------------
// Enrichment (Stage 1 hit → structured candidate)
// ---------------------------------------------------------------------------

function todayUTC(): string {
  return new Date().toISOString().slice(0, 10)
}

/** Deterministic Stage-2 enrichment of one Stage-1 hit. Pure. */
export function enrichCandidate(
  raw: RawCandidate,
  ctx: { citations: CitationRef[]; nowDate: string },
): StructuredPredictionCandidate {
  const window = parseWindow(raw.horizon, ctx.nowDate)
  const stated = parseStatedConfidence(raw.text)
  const grounding_fact_ids = ctx.citations.map((c) => c.signal_id)
  return {
    claim_text: raw.text,
    domain: inferDomain(raw.text),
    window_start: window?.start ?? null,
    window_end: window?.end ?? null,
    direction: inferDirection(raw.text),
    ...(stated !== null ? { confidence_stated: stated } : {}),
    technique_refs: inferTechniques(raw.text, ctx.citations),
    grounding_fact_ids,
    score: raw.score,
    horizon_text: raw.horizon,
  }
}

/**
 * Full two-stage detection (deterministic default classifier). Runs Stage 1
 * (the shipped regex detector), enriches each hit to the §14.2 structured shape,
 * then applies the injectable Stage-2 classifier (default: identity over the
 * deterministic enrichment). Candidates the classifier returns null for are
 * dropped. Sorted by Stage-1 score descending.
 */
export async function detectStructuredCandidates(
  input: DetectInput,
  classifier?: CandidateClassifier,
): Promise<StructuredPredictionCandidate[]> {
  const nowDate = input.nowDate ?? todayUTC()
  const minScore = input.minScore ?? 0.5
  const citations = input.citations ?? []
  const raws = detectStage1Raw(input.text).filter((c) => c.score >= minScore)

  const out: StructuredPredictionCandidate[] = []
  for (const raw of raws) {
    const base = enrichCandidate(raw, { citations, nowDate })
    const refined = classifier ? await classifier(raw, base) : base
    if (refined) out.push(refined)
  }
  return out.sort((a, b) => b.score - a.score)
}

/**
 * Synchronous variant — Stage 1 + deterministic Stage-2 enrichment, no async
 * classifier. This is the path the settled-turn persistence seam and the tests
 * use; it is sub-millisecond and DB-free.
 */
export function detectStructuredCandidatesSync(input: DetectInput): StructuredPredictionCandidate[] {
  const nowDate = input.nowDate ?? todayUTC()
  const minScore = input.minScore ?? 0.5
  const citations = input.citations ?? []
  return detectStage1Raw(input.text)
    .filter((c) => c.score >= minScore)
    .map((raw) => enrichCandidate(raw, { citations, nowDate }))
    .sort((a, b) => b.score - a.score)
}
