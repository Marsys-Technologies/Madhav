/**
 * intent_scope_classifier.ts — D-2 Lane V-3, CR-28 (BIND_D-2.md §F1.7 ledger row 29).
 *
 * DETERMINISTIC scope-tuple classifier for the Vidhi Engine compiler, implementing
 * DISAGREEMENT_REGISTER DIS.021 / DR-8 (Opus engineering adjudication, 2026-07-16).
 *
 * The prior `intent_classify` / `util_intent_classify` returned a rendered classifier PROMPT
 * (prompt-delegation to the consuming LLM) — the server could not echo a tuple it never computed,
 * silently breaking V-2's already-briefed scope-tuple-echo promise. DR-8 REDESIGN ruling: the
 * common path is self-contained deterministic rule/pattern matching over the intent vocabulary
 * (CLAUDE.md §N.4 Deterministic-first — "Python over LLM for computation"; B.10 no-fabricated-
 * computation: zero inference cost/latency, no model-coupling, fully auditable via `matched_rules`).
 * The old rendered prompt is retained verbatim as `fallback_prompt`, disclosed and recommended
 * only when the deterministic pass is low-confidence / unmatched (`fallback_recommended`), so
 * genuinely ambiguous queries keep an LLM-delegation escape hatch.
 *
 * This module is the ONE shared classifier both faces (intent_classify in l0_brahmagyan.ts,
 * util_intent_classify in register_p1_aliases.ts) call, so the two twins never diverge.
 */

// ── Scope-tuple vocabulary (the compiler's contract) ──────────────────────────

/** The eight primary intents (superset of the pre-redesign INTENTS list). */
export const INTENTS = [
  'dasha_timing',
  'transit_analysis',
  'yoga_identification',
  'planet_strength',
  'house_analysis',
  'remedy_lookup',
  'panchanga',
  'classical_rule',
  'chart_overview',
  'prediction_calibration',
  'domain_assessment',
  'unknown',
] as const
export type Intent = (typeof INTENTS)[number]

export const DOMAINS = [
  'wealth', 'career', 'marriage', 'health', 'children', 'education',
  'spirituality', 'litigation', 'property', 'travel', 'general',
] as const
export type Domain = (typeof DOMAINS)[number]

export type Width = 'narrow' | 'standard' | 'broad'
export type Depth = 'shallow' | 'standard' | 'deep'
export type Horizon = 'past' | 'present' | 'near' | 'far' | 'atemporal'
export type Intervention = 'none' | 'remedy' | 'muhurta' | 'mitigation'
export type Entitlement = 'reference' | 'native' | 'restricted'

/**
 * Ω4 (Elevation Campaign v2.1) routing decision — the binary the depth-default flip governs.
 * `deep` = full comprehensive dossier (the DEFAULT posture); `narrow` = a pinpoint pointed-fact
 * lookup that had to be EARNED against the four narrow criteria below.
 */
export type Route = 'deep' | 'narrow'

/**
 * Pointer served on EVERY classification (Ω4: "even a narrow answer carries depth_available") —
 * the machine-readable way for a caller to escalate a narrow pinpoint answer to the full dossier.
 */
export type DepthAvailable = {
  /** true when a deeper reading exists that this classification did NOT deliver (i.e. narrow route). */
  available: boolean
  depth: Depth
  width: Width
  pointer: string
}

/**
 * The two native charts (§B / L1_GANITA_CLOSURE). A chart-specific query about either resolves
 * entitlement to `native` — NOT `restricted` (Ω4 defect fix: "restricted incorrectly applies to
 * native's own charts"). Any OTHER explicit chart_id is a third party → least-privilege `restricted`.
 */
export const NATIVE_CHART_IDS: ReadonlySet<string> = new Set([
  '482012f1-710e-4a25-994a-93821f5871aa', // Abhisek Mohanty (native)
  '1c826d5a-41cb-4450-b4dc-59d440e5f75a', // Abhinandan Mohanty (native family — operator E2E chart)
])

export type ScopeTuple = {
  intent: Intent
  domains: Domain[]
  width: Width
  depth: Depth
  horizon: Horizon
  intervention: Intervention
  entitlement: Entitlement
}

export type ScopeClassification = {
  scope_tuple: ScopeTuple
  confidence: number // 0.0–1.0
  method: 'deterministic_rules'
  matched_rules: string[]
  fallback_prompt: string
  fallback_recommended: boolean
  usage: string
  /** Ω4: the binary depth-default routing decision. `deep` unless narrow was positively EARNED. */
  route: Route
  /** Ω4: the narrow-classification confidence (distinct from the intent `confidence`). Below 0.5 → DEEP. */
  narrow_confidence: number
  /** Ω4: escalation pointer to the full dossier — present on every classification, narrow or deep. */
  depth_available: DepthAvailable
}

// ── Rendered prompt (retained verbatim as the fallback escape hatch) ───────────
// This is the EXACT template the pre-DR-8 tool returned. DR-8 mandates it be retained.

export const INTENT_CLASSIFY_TEMPLATE = `You are a Jyotish query classifier. Your job is to identify the PRIMARY intent of a query about a birth chart.

INTENTS (pick exactly ONE):
- dasha_timing: questions about planetary periods, sub-periods, Vimshottari or Jaimini dashas
- transit_analysis: current planetary transits, Gochar, upcoming transits
- yoga_identification: identifying chart yogas (Raj Yoga, Dhana Yoga, etc.)
- planet_strength: graha bala, Shadbala, dignity, debilitation, exaltation
- house_analysis: bhava analysis, house lords, house strength
- remedy_lookup: upayas, mantras, gemstones, rituals, remedies
- panchanga: tithi, vara, nakshatra, yoga, karana, muhurta
- classical_rule: looking up a specific classical text rule or sutra
- chart_overview: general chart reading, lagna analysis, overall summary
- prediction_calibration: evaluating or calibrating a specific prediction
- unknown: none of the above

QUERY:
{{query}}

Respond with ONLY valid JSON:
{"primary_intent": "<intent>", "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}`

export function renderFallbackPrompt(query: string): string {
  return INTENT_CLASSIFY_TEMPLATE.replace('{{query}}', query)
}

// ── Rule tables ───────────────────────────────────────────────────────────────
// Each rule is [label, regex]. A match appends its label to matched_rules (audit trail).

type Rule = readonly [string, RegExp]

const INTENT_RULES: ReadonlyArray<readonly [Intent, ReadonlyArray<Rule>]> = [
  ['remedy_lookup', [
    ['remedy:upaya', /\b(remed(y|ies|ial)|upaya|upāya|mantra|gemstone|gem stone|ratna|yantra|tantra|puja|pūjā|ritual|donation|dāna|daan|propitiat)/i],
    ['remedy:what-do', /\bwhat (should|can|do) i (do|wear|chant|perform)\b/i],
  ]],
  ['dasha_timing', [
    ['dasha:period', /\b(dasha|daśā|dasa|mahadasha|mahādaśā|antardasha|antardaśā|bhukti|pratyantar|vimshottari|viṃśottarī|jaimini dasha|chara dasha|narayana dasha|planetary period|sub-?period)\b/i],
    ['dasha:running', /\b(current|running|which|what) (dasha|daśā|period|mahadasha)\b/i],
  ]],
  ['transit_analysis', [
    ['transit:gochar', /\b(transit|gochar|gochara|sade sati|saḍe sati|sadesati|kantaka|ashtama shani|current planetary position|where is (saturn|jupiter|rahu|ketu|mars) (now|transiting))\b/i],
  ]],
  ['yoga_identification', [
    ['yoga:catalog', /\b(yoga|yogas|raja ?yoga|dhana ?yoga|gaja ?kesari|pancha ?mahapurusha|neecha ?bhanga|kemadruma|combinations?)\b/i],
  ]],
  ['planet_strength', [
    ['strength:bala', /\b(shadbala|ṣaḍbala|graha ?bala|bala|strength|dignity|exalt|debilit|neecha|uccha|combust|retrograde|vargottama|ashtakavarga|bindu)\b/i],
  ]],
  ['house_analysis', [
    ['house:bhava', /\b(house|bhava|bhāva|\b\d{1,2}(st|nd|rd|th) house\b|house lord|bhavesha|lord of the|cusp)\b/i],
  ]],
  ['panchanga', [
    ['panchanga:element', /\b(tithi|vara|vāra|nakshatra|nakṣatra|karana|karaṇa|panchanga|pañcāṅga|muhurta|muhūrta|choghadiya|hora)\b/i],
  ]],
  ['classical_rule', [
    ['classical:sutra', /\b(bphs|parashara|parāśara|jaimini sutra|brihat|sutra|sūtra|shloka|śloka|classical (rule|text|reference)|what does (the )?(text|scripture|shastra) say)\b/i],
  ]],
  ['prediction_calibration', [
    ['calibration:score', /\b(calibrat|prediction (was|is)?\s*(correct|accurate|accuracy|right|wrong)|(was|were) my.*prediction|did (it|the prediction) (come true|happen)|track record|hit rate|outcome (record|log)|falsif)\b/i],
  ]],
  ['domain_assessment', [
    ['assess:domain', /\b(assess|assessment|prospects?|outlook|analy[sz]e my|reading (for|on) (my )?(career|wealth|marriage|health|finance|money|job|relationship|business))\b/i],
  ]],
  ['chart_overview', [
    ['overview:general', /\b(overall|whole chart|entire chart|general reading|full reading|chart summary|read my chart|tell me about my (chart|horoscope|kundli)|lagna analysis|ascendant)\b/i],
  ]],
]

// F-24: DOMAIN_RULES updated to match DEEP_DOMAIN_WORD's plural-safe vocabulary so that
// 'married'/'jobs'/'relationships' etc. resolve to the correct domain in scope_tuple.domains
// (they already triggered the deep-push path via DEEP_DOMAIN_WORD but were classified as
// 'general' because DOMAIN_RULES lacked plural/morphological coverage).
const DOMAIN_RULES: ReadonlyArray<readonly [Domain, RegExp]> = [
  ['wealth', /\b(wealth|moneys?|finances?|financial|riches|dhana|incomes?|savings|prosperity|affluen|net worth|gains?)\b/i],
  ['career', /\b(careers?|jobs?|professions?|professional|work|business(es)?|occupations?|employ|promotion|karma bhava|10th house|vocations?|livelihoods?)\b/i],
  ['marriage', /\b(marriages?|marry|married|marital|spouses?|wi(fe|ves)|husbands?|partners?|partnerships?|relationships?|love|romance|romantic|compatib|7th house|kalatra|divorces?|separations?|union)\b/i],
  ['health', /\b(health|diseases?|illness(es)?|body|medical|ailments?|roga|longevity|ayurdaya|vitality|sickness|chronic|acute|surg(ery|eries))\b/i],
  ['children', /\b(child(ren)?|progeny|santana|santāna|pregnan|conceive|5th house|putra|offspring|fertility)\b/i],
  ['education', /\b(education|study|studies|learning|degree|academic|vidya|knowledge|exam|scholar)\b/i],
  ['spirituality', /\b(spiritual|moksha|mokṣa|liberation|dharma|guru|sadhana|meditation|12th house|renunciation|sannyasa)\b/i],
  ['litigation', /\b(litigation|lawsuit|court|legal|dispute|enemy|enemies|6th house|conflict|debts?|loans?)\b/i],
  ['property', /\b(property|house|home|real estate|land|vehicle|4th house|assets?|conveyance)\b/i],
  ['travel', /\b(travel|foreign|abroad|relocation|journey|migration|overseas|pilgrimage)\b/i],
]

const WIDTH_BROAD = /\b(overall|whole|entire|complete|comprehensive|full|everything|all aspects|holistic|360|big picture|life reading)\b/i
const WIDTH_NARROW = /\b(just|only|specific|exactly|single|one thing|precisely|quick fact)\b/i

const DEPTH_DEEP = /\b(deep ?dive|detailed|in depth|in-depth|thorough|acharya|ācārya|exhaustive|granular|elaborate|comprehensive analysis)\b/i
const DEPTH_SHALLOW = /\b(quick|brief|summary|short|tldr|tl;dr|in a nutshell|one line|glance|snapshot)\b/i

const HORIZON_PAST = /\b(was|were|did|had|born|childhood|past|previously|history|already happened|last year|years ago)\b/i
const HORIZON_PRESENT = /\b(now|current|currently|present|today|at the moment|these days|right now|this (month|week|year))\b/i
const HORIZON_NEAR = /\b(next (month|year|week)|coming (months?|years?|weeks?)|soon|upcoming|near future|shortly|when will|this year)\b/i
const HORIZON_FAR = /\b(long term|long-term|eventually|later life|old age|far future|decades?|lifetime|by \d{4}|in \d+ years)\b/i

const INTERVENTION_MUHURTA = /\b(muhurta|muhūrta|auspicious (time|date|day)|best time|when (should|to) (start|begin|marry|launch|travel)|good time for|electional)\b/i
const INTERVENTION_MITIGATION = /\b(mitigat|reduce|lessen|protect against|ward off|counteract|neutrali[sz]e|shanti|śānti)\b/i
const INTERVENTION_REMEDY = /\b(remed(y|ies|ial)|upaya|upāya|mantra|gemstone|ratna|yantra|donation|puja|pūjā|what (should|can) i (do|wear|chant))\b/i

const REFERENCE_INTENTS: ReadonlySet<Intent> = new Set(['classical_rule', 'panchanga'])

// ── Ω4 depth-default routing (Elevation Campaign v2.1) ─────────────────────────
// DOCTRINE: `depth: deep, width: broad` (deepdive/comprehensive) is the DEFAULT posture. A
// `narrow` pinpoint route must be EARNED — it is granted ONLY when a query positively matches
// a single-entity / single-attribute pinpoint shape AND trips NONE of the deep-push signals
// below (evaluative/predictive verb, life-domain word, analytical topic, breadth, multi-entity).
// Uncertainty resolves toward depth: narrow_confidence < 0.5 → DEEP (mirrors Ω2 default-include).
//
// The classifier must not be weaker than plan_retrieval's keyword fallback (scope_resolver.ts),
// which routes EVERY life-domain-keyword question to `deepdive`. Every deep-push token below is a
// superset of that fallback's genuine life-domain vocabulary, so any question the fallback routes
// deep on a real domain word, this classifier also routes deep. (The fallback ALSO false-positives
// on bare house-ordinals — "10th"/"7th" — routing pinpoint "10th house lord" queries to a career/
// marriage deepdive; that is the exact over-routing Ω4 fixes, so house-ordinals are treated as
// STRUCTURAL here, never as a domain word.)

// (a)+(c) Evaluative / predictive / interpretive verbs & framings → DEEP. "How is my Moon" is deep
//          ('how' is evaluative); "What is my Moon sign" is not.
const DEEP_VERB =
  /\b(how|why|will|would|should|could|shall|can|when|analy[sz]e|assess|assessment|evaluate|describe|discuss|explain|indicate[ds]?|affect(s|ing|ed)?|suited|suit|suggest|recommend|compare|predict|forecast|interpret|read(ing)?|tell me|show(s|n)? about|say(s)? about|does my chart|do my|is this|are there|is there|more than one)\b/i

// (d) Life-domain words → DEEP. STRUCTURAL terms (house / bhava / Nth-house / planet names /
//     karakas / lagnas) are DELIBERATELY excluded — those are the pinpoint entities, not domains.
//     Nouns carry an optional plural suffix `s?` so "relationships"/"jobs"/"ailments" leak-proof
//     (F-Ω4-1 robustness fix — the \b...\b boundary previously let plural forms escape).
const DEEP_DOMAIN_WORD =
  /\b(wealth|moneys?|finances?|financial|incomes?|riches|prosperity|affluen|net worth|debts?|litigation|careers?|professions?|professional|jobs?|occupations?|employ|livelihoods?|vocations?|business(es)?|marriages?|marry|married|marital|spouses?|wi(fe|ves)|husbands?|partners?|partnerships?|relationships?|romance|romantic|compatib|separations?|divorces?|health|diseases?|illness(es)?|ailments?|medical|longevity|vitality|chronic|acute|surg(ery|eries)|child(ren)?|progeny|offspring|fertility|education|academic)\b/i

// Analytical topics & breadth framings → DEEP (a pinpoint fact never asks for these).
const DEEP_TOPIC =
  /\b(yoga|yogas|dosha|doshas|dasha|dashas|antardasha|bhukti|transit|transits|gochar|sade sati|remed(y|ies|ial)|mitigat|prospects?|outlook|trajectory|growth|risks?|obstacle|vulnerab|afflict|instabilit|fame|recognition|leadership|independent|independence|periods? (in|of|for)|best period|worst|good chart|better suited)\b/i

const DEEP_BREADTH =
  /\b(everything|comprehensive|entire|whole|overall|holistic|all aspects|big picture|life reading|full (life|reading|picture)|versus|\bvs\b)\b/i

// A conjunction that joins TWO topics/clauses → not a single pinpoint → DEEP.
const DEEP_MULTI = /\b(and|or)\b.*\b(and|or)\b/i
const CONJUNCTION = /\b(and|or)\b/i

/**
 * Count total entity MENTIONS (not distinct classes). A single conjunction joining two same-class
 * entities ("… the Moon in and what sign is Mars in?") must trip the multi-clause gate even though
 * both dedupe to one class downstream (F-Ω4-1 robustness fix). Overlapping matches (a house-lord
 * also matching the bare house-ordinal) can over-count, but that only ever pushes toward DEEP and is
 * gated behind a conjunction — no conjunction-free narrow pinpoint is affected.
 */
function countEntityMentions(query: string): number {
  const g = (re: RegExp) => (query.match(new RegExp(re.source, 'gi')) ?? []).length
  return g(PLANET) + g(HOUSE_LORD) + g(POINT_ENTITY) + g(HOUSE_ORDINAL) + g(ASCENDANT)
}

// ── Positive pinpoint shape (the narrow criteria (a) single entity + (b) single attribute) ─────

// A specific single computed point that IS the answer on its own — "What is my X" is a pinpoint.
const POINT_ENTITY =
  /\b(indu lagna|hora lagna|bhava lagna|ghati(ka)? lagna|arudha( lagna| pada|)|sree lagna|shree lagna|shri lagna|pranapada|vighati lagna|(atma|amatya|bhratri|bhatru|matri|putra|gnati|dara|amatra)\s?karaka|karaka)\b/i

// Planets (incl. common Sanskrit) — an object you ask ONE attribute of.
const PLANET =
  /\b(sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu|s[uū]rya|chandra|budha|guru|b[rṛ]haspati|shukra|[śs]ukra|shani|[śs]ani|mangal|kuja|angaraka)\b/i

// A house-lord ("2nd house lord", "ascendant lord", "lagna lord", "lord of the 7th house").
const HOUSE_LORD =
  /\b(\d{1,2}(st|nd|rd|th)\s+(house\s+)?lord|(ascendant|lagna|rising)\s+lord|lord\s+of\s+the\s+\d{1,2}(st|nd|rd|th)\s+house|bhavesha|lagnesha)\b/i

// A bare house ("7th house") — pinpoint when paired with a "sign" attribute ("7th house sign").
const HOUSE_ORDINAL = /\b\d{1,2}(st|nd|rd|th)\s+house\b/i

// The ascendant/lagna itself as an entity.
const ASCENDANT = /\b(ascendant|lagna|rising sign|rising)\b/i

// The single attribute being asked of an object entity.
const PINPOINT_ATTR =
  /\b(sign|r[aā][śs]i|nak[śs]atra|nakshatra|house|placement|placed|dignity|degree[s]?|longitude|pada|dispositor|exalt|debilit|combust|retrograde|dig bala|status)\b/i

/**
 * Narrow-pointed detector (Ω4). Returns the earned-narrow decision plus a confidence and the audit
 * reasons. Narrow requires ALL of: (a) a single named entity, (b) a single named attribute,
 * (c) no evaluative/predictive verb, (d) no domain word — and narrow_confidence ≥ 0.5.
 */
function detectNarrow(query: string): { narrow: boolean; confidence: number; reasons: string[] } {
  const reasons: string[] = []

  // (c)+(d) + topic/breadth/multi deep-push gate — ANY hit disqualifies narrow.
  const deepHits: string[] = []
  if (DEEP_VERB.test(query)) deepHits.push('deep_push:eval_verb')
  if (DEEP_DOMAIN_WORD.test(query)) deepHits.push('deep_push:domain_word')
  if (DEEP_TOPIC.test(query)) deepHits.push('deep_push:analytical_topic')
  if (DEEP_BREADTH.test(query)) deepHits.push('deep_push:breadth')
  if (DEEP_MULTI.test(query)) deepHits.push('deep_push:multi_clause')
  // F-Ω4-1: a conjunction joining ≥2 entity mentions (even same-class) is a compound query → DEEP.
  if (CONJUNCTION.test(query) && countEntityMentions(query) >= 2) deepHits.push('deep_push:multi_entity_conjunction')
  if (deepHits.length > 0) {
    return { narrow: false, confidence: 0, reasons: deepHits }
  }

  // (a) single entity — count the distinct entity CLASSES referenced (most-specific first, so a
  //     "2nd house lord" counts once as a house-lord, not also as a bare house).
  let entityClass: string | null = null
  let entityCount = 0
  const seen = new Set<string>()
  const noteEntity = (cls: string) => { if (!seen.has(cls)) { seen.add(cls); entityCount += 1; entityClass = cls } }
  if (HOUSE_LORD.test(query)) noteEntity('house_lord')
  else if (POINT_ENTITY.test(query)) noteEntity('point_entity')
  else {
    if (PLANET.test(query)) noteEntity('planet')
    if (HOUSE_ORDINAL.test(query)) noteEntity('house')
    if (ASCENDANT.test(query) && !HOUSE_ORDINAL.test(query)) noteEntity('ascendant')
    if (POINT_ENTITY.test(query)) noteEntity('point_entity')
  }

  if (entityClass === null) {
    return { narrow: false, confidence: 0, reasons: ['narrow:no_pinpoint_entity'] }
  }
  if (entityCount > 1) {
    return { narrow: false, confidence: 0, reasons: [`narrow:multi_entity(${entityCount})`] }
  }
  reasons.push(`narrow:entity=${entityClass}`)

  // (b) single attribute. Point-entities (karaka / special lagna) are self-contained — the entity
  //     IS the queried value, so an explicit attribute word is not required.
  const attrMatched = PINPOINT_ATTR.test(query)
  const selfContained = entityClass === 'point_entity'
  if (!attrMatched && !selfContained) {
    return { narrow: false, confidence: 0, reasons: [...reasons, 'narrow:no_pinpoint_attribute'] }
  }
  if (attrMatched) reasons.push('narrow:attribute')
  else reasons.push('narrow:self_contained_point')

  // Confidence: entity (0.5) + attribute-or-self-contained (0.4). Both present ≥ 0.9 ≥ 0.5.
  let confidence = 0.5 + (attrMatched || selfContained ? 0.4 : 0)
  confidence = Math.round(confidence * 100) / 100
  reasons.push(`narrow_confidence:${confidence}`)

  // Ω4 uncertainty rule: below 0.5 routes DEEP, never narrow.
  if (confidence < 0.5) {
    return { narrow: false, confidence, reasons: [...reasons, 'narrow:below_confidence_floor->deep'] }
  }
  return { narrow: true, confidence, reasons }
}

// ── Entitlement-gated fallback_prompt disclosure ───────────────────────────────
// The rendered fallback_prompt is the ENTIRE internal classifier system-prompt, verbatim
// (dev-facing prompt-engineering text). It must not reach every caller unconditionally —
// only entitlement:'native' (internal/native-facing) callers get the full text; reference/
// restricted callers get a redaction stub instead. See finding: "fallback_prompt inlines
// the full internal classifier system-prompt unconditionally".

const FALLBACK_PROMPT_REDACTED =
  '[fallback_prompt withheld: the internal classifier system-prompt is disclosed only to ' +
  'entitlement="native" callers. This query classified at a non-native entitlement tier; ' +
  'escalate via the native-facing path if the full LLM-delegation prompt is required.]'

function gateFallbackPrompt(rendered: string, entitlement: Entitlement): string {
  return entitlement === 'native' ? rendered : FALLBACK_PROMPT_REDACTED
}

// ── Classifier ────────────────────────────────────────────────────────────────

function firstMatch<T>(query: string, rules: ReadonlyArray<readonly [T, RegExp]>, matched: string[], kind: string): T | null {
  for (const [value, re] of rules) {
    if (re.test(query)) {
      matched.push(`${kind}:${String(value)}`)
      return value
    }
  }
  return null
}

/** Optional caller context — the ONLY authorization signal this deterministic classifier honors. */
export type ClassifyContext = {
  /** The chart the query is about, when the caller knows it. A native chart_id → entitlement `native`. */
  chartId?: string
}

/**
 * Resolve the entitlement tier (Ω4 defect fix). Reference intents stay `reference`. For a
 * chart-specific query: an explicit NATIVE chart_id → `native`; an explicit THIRD-PARTY chart_id →
 * least-privilege `restricted`; NO chart_id supplied → `native` (this is the native's own
 * single-native instrument — §B — so an un-qualified "my …" query is about the native's own chart;
 * the prior blanket `restricted` default was the documented defect that mis-tagged native charts).
 */
function resolveEntitlement(intent: Intent, chartId: string | undefined): { entitlement: Entitlement; reason: string } {
  if (REFERENCE_INTENTS.has(intent)) return { entitlement: 'reference', reason: 'entitlement:reference<-reference_intent' }
  if (chartId !== undefined) {
    return NATIVE_CHART_IDS.has(chartId)
      ? { entitlement: 'native', reason: 'entitlement:native<-native_chart_id' }
      : { entitlement: 'restricted', reason: 'entitlement:restricted<-third_party_chart_id' }
  }
  return { entitlement: 'native', reason: 'entitlement:native<-default_native_instrument' }
}

/** The escalation pointer served on every classification (Ω4 depth_available). */
function makeDepthAvailable(route: Route): DepthAvailable {
  return route === 'narrow'
    ? {
        available: true,
        depth: 'deep',
        width: 'broad',
        pointer:
          'A full comprehensive dossier is available. To escalate this pinpoint answer, re-invoke ' +
          'with an explicit deepdive scope_tuple (depth:"deep", width:"broad") or call the domain ' +
          'dossier / plan_retrieval for the whole-domain read.',
      }
    : {
        available: false,
        depth: 'deep',
        width: 'broad',
        pointer: 'Already routed to the full comprehensive (deepdive) reading — no deeper tier to escalate to.',
      }
}

/**
 * Deterministically classify a query into a scope tuple.
 * Pure function: identical input → identical output (compiler-safe per DR-8).
 *
 * Ω4 (Elevation Campaign v2.1): the DEFAULT posture is `depth: deep, width: broad` (deepdive /
 * comprehensive). A `narrow`/`shallow` route is EARNED only via {@link detectNarrow}. `context.chartId`
 * feeds the entitlement fix ({@link resolveEntitlement}).
 */
export function classifyScope(rawQuery: string, context?: ClassifyContext): ScopeClassification {
  const query = (rawQuery ?? '').trim()
  const matched: string[] = []
  const renderedFallbackPrompt = renderFallbackPrompt(query)
  const chartId = context?.chartId

  if (!query) {
    const emptyQueryEntitlement: Entitlement = resolveEntitlement('unknown', chartId).entitlement
    // Ω4: even an unclassifiable query defaults to the DEEP posture (uncertainty → depth).
    const emptyRoute: Route = 'deep'
    return {
      scope_tuple: {
        intent: 'unknown', domains: ['general'], width: 'broad', depth: 'deep',
        horizon: 'atemporal', intervention: 'none', entitlement: emptyQueryEntitlement,
      },
      confidence: 0,
      method: 'deterministic_rules',
      matched_rules: ['route:deep<-empty_query_default', `entitlement:${emptyQueryEntitlement}`],
      fallback_prompt: gateFallbackPrompt(renderedFallbackPrompt, emptyQueryEntitlement),
      fallback_recommended: true,
      usage: 'Empty query — no deterministic classification possible. Defaulted to the deep (comprehensive) ' +
        'posture per Ω4 (uncertainty resolves toward depth). Use fallback_prompt with an LLM for a real classification.',
      route: emptyRoute,
      narrow_confidence: 0,
      depth_available: makeDepthAvailable(emptyRoute),
    }
  }

  // 1. Intent — first intent-family whose any rule fires (ordered by specificity above).
  let intent: Intent = 'unknown'
  for (const [candidate, rules] of INTENT_RULES) {
    const hit = rules.find(([, re]) => re.test(query))
    if (hit) {
      intent = candidate
      matched.push(`intent:${candidate}<-${hit[0]}`)
      break
    }
  }

  // 2. Domains — ALL matching (multi-value). Empty → ['general'].
  const domains: Domain[] = []
  for (const [dom, re] of DOMAIN_RULES) {
    if (re.test(query)) {
      domains.push(dom)
      matched.push(`domain:${dom}`)
    }
  }
  if (domains.length === 0) domains.push('general')

  // ── Ω4 narrow-detection: does this query EARN the narrow pinpoint route? ──────
  const narrowResult = detectNarrow(query)
  matched.push(...narrowResult.reasons)
  const narrowEarned = narrowResult.narrow
  const route: Route = narrowEarned ? 'narrow' : 'deep'
  matched.push(`route:${route}`)

  // 3. Width — Ω4 DEFAULT is `broad` (comprehensive); `narrow` must be EARNED. An explicit broad
  //    keyword stays broad; an explicit narrow keyword only narrows when the pinpoint shape was
  //    also earned (a bare "just/only" without single-entity/attribute does not qualify).
  let width: Width
  if (narrowEarned) { width = 'narrow'; matched.push('width:narrow<-earned_pinpoint') }
  else if (WIDTH_BROAD.test(query)) { width = 'broad'; matched.push('width:broad') }
  else if (domains.length >= 3) { width = 'broad'; matched.push('width:broad<-multi_domain') }
  else { width = 'broad'; matched.push('width:broad<-default_comprehensive') }

  // 4. Depth — Ω4 DEFAULT is `deep` (deepdive). An explicit brevity keyword ("quick/summary") is
  //    honored as a caller-stated preference; an earned pinpoint drops to `shallow`; everything
  //    else stays `deep`. `standard` is no longer a default — it must be explicitly requested.
  let depth: Depth
  if (DEPTH_SHALLOW.test(query)) { depth = 'shallow'; matched.push('depth:shallow<-explicit_brevity') }
  else if (DEPTH_DEEP.test(query)) { depth = 'deep'; matched.push('depth:deep<-explicit') }
  else if (narrowEarned) { depth = 'shallow'; matched.push('depth:shallow<-earned_pinpoint') }
  else { depth = 'deep'; matched.push('depth:deep<-default_deepdive') }

  // 5. Horizon (present/near/far/past/atemporal). Precedence: explicit future > present > past.
  let horizon: Horizon = 'atemporal'
  if (HORIZON_NEAR.test(query)) { horizon = 'near'; matched.push('horizon:near') }
  else if (HORIZON_FAR.test(query)) { horizon = 'far'; matched.push('horizon:far') }
  else if (HORIZON_PRESENT.test(query)) { horizon = 'present'; matched.push('horizon:present') }
  else if (HORIZON_PAST.test(query)) { horizon = 'past'; matched.push('horizon:past') }
  else if (intent === 'dasha_timing' || intent === 'transit_analysis' || intent === 'prediction_calibration') {
    horizon = 'present'; matched.push('horizon:present<-timing_intent')
  }

  // 6. Intervention
  let intervention: Intervention = 'none'
  if (INTERVENTION_MUHURTA.test(query)) { intervention = 'muhurta'; matched.push('intervention:muhurta') }
  else if (INTERVENTION_REMEDY.test(query)) { intervention = 'remedy'; matched.push('intervention:remedy') }
  else if (INTERVENTION_MITIGATION.test(query)) { intervention = 'mitigation'; matched.push('intervention:mitigation') }

  // 7. Entitlement (Ω4 defect fix). Reference/panchanga = public reference data. For a chart-
  //    specific query the tier follows the caller's chart context: a native chart_id → 'native';
  //    an explicit third-party chart_id → least-privilege 'restricted'; NO chart context → 'native'
  //    (single-native instrument, §B — the prior blanket 'restricted' default mis-tagged the
  //    native's own charts, the exact defect this lane resolves). See resolveEntitlement.
  const entResolved = resolveEntitlement(intent, chartId)
  const entitlement: Entitlement = entResolved.entitlement
  matched.push(entResolved.reason)

  // Confidence: intent match is the dominant term; corroborating dimensions add smaller weight.
  const intentMatched = intent !== 'unknown'
  const domainMatched = !(domains.length === 1 && domains[0] === 'general')
  let confidence = 0
  if (intentMatched) confidence += 0.6
  if (domainMatched) confidence += 0.2
  if (intervention !== 'none') confidence += 0.1
  if (horizon !== 'atemporal') confidence += 0.1
  confidence = Math.min(1, Math.round(confidence * 100) / 100)

  const fallback_recommended = !intentMatched || confidence < 0.5

  return {
    scope_tuple: { intent, domains, width, depth, horizon, intervention, entitlement },
    confidence,
    method: 'deterministic_rules',
    matched_rules: matched,
    fallback_prompt: gateFallbackPrompt(renderedFallbackPrompt, entitlement),
    fallback_recommended,
    usage: fallback_recommended
      ? 'Low-confidence / unmatched intent — the scope_tuple is a best-effort default. ' +
        'Pass fallback_prompt to an LLM for a stronger classification, then correct the scope_tuple.'
      : 'Deterministic classification. V-2 echoes scope_tuple verbatim for user correction before execution. ' +
        'fallback_prompt is retained but not recommended for this query.',
    route,
    narrow_confidence: narrowResult.confidence,
    depth_available: makeDepthAvailable(route),
  }
}
