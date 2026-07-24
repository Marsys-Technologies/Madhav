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

const DOMAIN_RULES: ReadonlyArray<readonly [Domain, RegExp]> = [
  ['wealth', /\b(wealth|money|finance|financial|riches|dhana|income|savings|prosperity|affluen|net worth|gains?)\b/i],
  ['career', /\b(career|job|profession|work|business|occupation|employ|promotion|karma bhava|10th house|vocation|livelihood)\b/i],
  ['marriage', /\b(marriage|marry|spouse|wife|husband|partner|relationship|love|romance|7th house|kalatra|divorce|union)\b/i],
  ['health', /\b(health|disease|illness|body|medical|ailment|roga|longevity|ayurdaya|vitality|sickness|surgery)\b/i],
  ['children', /\b(child|children|progeny|santana|santāna|pregnan|conceive|5th house|putra|offspring)\b/i],
  ['education', /\b(education|study|studies|learning|degree|academic|vidya|knowledge|exam|scholar)\b/i],
  ['spirituality', /\b(spiritual|moksha|mokṣa|liberation|dharma|guru|sadhana|meditation|12th house|renunciation|sannyasa)\b/i],
  ['litigation', /\b(litigation|lawsuit|court|legal|dispute|enemy|enemies|6th house|conflict|debt|loan)\b/i],
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

/**
 * Deterministically classify a query into a scope tuple.
 * Pure function: identical input → identical output (compiler-safe per DR-8).
 */
export function classifyScope(rawQuery: string): ScopeClassification {
  const query = (rawQuery ?? '').trim()
  const matched: string[] = []
  const renderedFallbackPrompt = renderFallbackPrompt(query)

  if (!query) {
    const emptyQueryEntitlement: Entitlement = 'native'
    return {
      scope_tuple: {
        intent: 'unknown', domains: ['general'], width: 'standard', depth: 'standard',
        horizon: 'atemporal', intervention: 'none', entitlement: emptyQueryEntitlement,
      },
      confidence: 0,
      method: 'deterministic_rules',
      matched_rules: [],
      fallback_prompt: gateFallbackPrompt(renderedFallbackPrompt, emptyQueryEntitlement),
      fallback_recommended: true,
      usage: 'Empty query — no deterministic classification possible. Use fallback_prompt with an LLM.',
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

  // 3. Width
  let width: Width = 'standard'
  if (WIDTH_BROAD.test(query)) { width = 'broad'; matched.push('width:broad') }
  else if (WIDTH_NARROW.test(query)) { width = 'narrow'; matched.push('width:narrow') }
  else if (domains.length >= 3) { width = 'broad'; matched.push('width:broad<-multi_domain') }

  // 4. Depth
  let depth: Depth = 'standard'
  if (DEPTH_DEEP.test(query)) { depth = 'deep'; matched.push('depth:deep') }
  else if (DEPTH_SHALLOW.test(query)) { depth = 'shallow'; matched.push('depth:shallow') }

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

  // 7. Entitlement — best-effort disclosure tier. Reference/panchanga = public reference data;
  //    everything else defaults to the LEAST-PRIVILEGE tier ('restricted') — this classifier has
  //    no visibility into the calling principal's session, so it must never hint 'native' for a
  //    chart-specific query on the strength of a regex match alone. The compiler is the one that
  //    upgrades to 'native' when an explicit authenticated native-session signal is present in the
  //    caller's context; this function only ever offers a hint, never an authorization decision.
  const entitlement: Entitlement = REFERENCE_INTENTS.has(intent) ? 'reference' : 'restricted'
  matched.push(`entitlement:${entitlement}`)

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
  }
}
