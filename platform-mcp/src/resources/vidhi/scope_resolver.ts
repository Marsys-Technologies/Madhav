/**
 * scope_resolver.ts — D-2 Lane V-2, BIND_D-2.md §F1.7 ledger row 16 (scope-tuple echo).
 *
 * The AUTHORITATIVE question → scope_tuple classifier is V-3's `intent_classify` redesign
 * (DR-8 / DIS.021: returns `{scope_tuple, confidence, method, matched_rules, fallback_prompt,
 * fallback_recommended, usage}` via deterministic rule-matching). V-2 and V-3 ship in the
 * SAME cycle (cycle 2) in parallel, so at V-2's build time the DR-8 tool may not yet be
 * merged. Per this lane's task instruction ("code against the DR-8 contract shape; if V-3's
 * classifier isn't available at your build time, echo the tuple the server computes/receives
 * and note the dependency"), this module:
 *
 *   1. CONSUMES the DR-8 shape: if a caller passes a pre-classified `scope_tuple` (e.g. from
 *      `intent_classify`), `resolveScopeTuple` validates + uses it verbatim — the server
 *      echoes exactly what it received so the caller can correct it before execution.
 *   2. PROVIDES a deterministic FALLBACK resolver when only a question string is given, so
 *      `plan_retrieval` is self-contained and can always return a compiled plan for a wealth
 *      question (ledger row 15) without a hard dependency on V-3 being live. This fallback is
 *      a coarse keyword matcher — NOT a replacement for intent_classify; the response marks
 *      `method: 'v2_fallback_keyword'` and recommends the authoritative classifier.
 *
 * This is the SCOPE-TUPLE ECHO surface (ledger row 16): whatever tuple is resolved — received
 * or fallback-computed — is returned on the plan so a caller can correct it before execution.
 */
import type {
  ScopeTuple,
  IntentClass,
  ScopeWidth,
  ScopeDepth,
  ScopeHorizon,
  ScopeEntitlement,
} from './types.js';
// E-4 (VIDHI-PŪRṆATĀ P-3b): the domain→deepdive-intent map, imported from the compiler so the
// received-tuple promotion and the compiler union agree on one source of truth (no drift). No
// cycle: compiler.ts imports only ./types + ./registry_data, never this module.
import { DOMAIN_TO_INTENT } from './compiler.js';

const INTENT_CLASSES: readonly IntentClass[] = [
  'wealth_deepdive',
  'career_deepdive',
  'health_deepdive',
  'marriage_deepdive',
  // VIDHI-PŪRṆATĀ P-2 (F1): the three new life-domain deepdives. Presence here is the
  // received-tuple resolution path — a caller passing intent:'spirituality_deepdive' (etc.)
  // is now coerced to it instead of silently collapsing to general_synthesis.
  'spirituality_deepdive',
  'education_deepdive',
  'progeny_deepdive',
  'structure_read',
  'panoramic_breadth',
  'retrieval_only',
  'general_synthesis',
];
const WIDTHS: readonly ScopeWidth[] = ['narrow', 'standard', 'panoramic'];
const DEPTHS: readonly ScopeDepth[] = ['retrieval', 'structure', 'deepdive'];
const HORIZONS: readonly ScopeHorizon[] = ['natal', 'current', 'multi_year'];
const ENTITLEMENTS: readonly ScopeEntitlement[] = ['native', 'research', 'public_disclosed'];

/**
 * DEPTH-DEFAULT DOCTRINE (BINDING — BRIEF_VIDHI_PURNATA_v1_0 §0; native-directed 2026-07-23).
 * DEEPDIVE IS THE DEFAULT STATE OF THE INSTRUMENT. Depth is driven by the resolved INTENT,
 * never gated behind a "deep/detailed/thorough" magic word (the pre-P-1 keyword gate). Every
 * full-read intent — the four domain deepdives, `panoramic_breadth`, and the `general_synthesis`
 * / E-0 foundational fallback for the unclassifiable question — defaults to `deepdive` (full
 * floor + machine band + intervention layer). A tuple drops BELOW deepdive ONLY for the two
 * intents that ARE, by definition, a reduced ask: `structure_read` (structural orientation) and
 * `retrieval_only` (a genuine RS-4 single-fact lookup, e.g. "where is my Moon?", "what dasha am
 * I in?"). This is LAW, not an implementation detail: ambiguity/generality resolves toward MORE
 * depth, never less. Closes F5 (naive-depth trap) + F6 (intervention trap) of
 * STATIC_VIDHI_AUDIT_v1_0. An explicitly-supplied valid depth on a received tuple is still
 * honored verbatim (the correction path); this governs only the DEFAULT when depth is omitted
 * or a question is keyword-resolved.
 */
const REDUCED_DEPTH_INTENTS: ReadonlySet<IntentClass> = new Set<IntentClass>([
  'structure_read',
  'retrieval_only',
]);

/** Intent-driven default depth (see DEPTH-DEFAULT DOCTRINE above). */
function defaultDepthForIntent(intent: IntentClass): ScopeDepth {
  switch (intent) {
    case 'retrieval_only':
      return 'retrieval';
    case 'structure_read':
      return 'structure';
    default:
      return 'deepdive'; // every full-read intent — incl. general_synthesis / E-0 fallback
  }
}

/**
 * Intent-driven default for the intervention/remedy layer (F6). A full-read (deepdive-class)
 * intent INCLUDES intervention by default — a complete reading carries its guidance layer; the
 * two reduced intents omit it unless the caller (received tuple) or a remedy keyword opts in.
 */
function defaultInterventionForIntent(intent: IntentClass): boolean {
  return !REDUCED_DEPTH_INTENTS.has(intent);
}

/** DR-8-shaped input a caller may pass through (from `intent_classify`). Partial-tolerant. */
export interface ScopeTupleInput {
  readonly intent?: string;
  readonly domains?: readonly string[];
  readonly width?: string;
  readonly depth?: string;
  readonly horizon?: string;
  readonly intervention?: boolean;
  readonly entitlement?: string;
}

export type ResolveMethod = 'received_scope_tuple' | 'v2_fallback_keyword';

export interface ResolvedScope {
  readonly scope_tuple: ScopeTuple;
  readonly method: ResolveMethod;
  readonly matched_rules: readonly string[];
  /** True when the resolution is the coarse fallback — the caller SHOULD prefer intent_classify. */
  readonly fallback_recommended: boolean;
  readonly note: string;
}

function coerce<T extends string>(value: string | undefined, allowed: readonly T[], fallback: T): T {
  return value !== undefined && (allowed as readonly string[]).includes(value) ? (value as T) : fallback;
}

/**
 * Domain → intent keyword map (fallback only). Ordered by specificity; first hit wins.
 * Deliberately small and total — a coarse matcher, not the authoritative DR-8 classifier.
 */
const KEYWORD_INTENTS: ReadonlyArray<{ re: RegExp; intent: IntentClass; domains: string[] }> = [
  { re: /\b(wealth|money|dhana|finance|financial|income|riches|prosperity)\b/i, intent: 'wealth_deepdive', domains: ['wealth'] },
  { re: /\b(career|profession|job|karma|10th|work|occupation|vocation)\b/i, intent: 'career_deepdive', domains: ['career'] },
  { re: /\b(health|disease|illness|roga|body|ayur|longevity)\b/i, intent: 'health_deepdive', domains: ['health'] },
  { re: /\b(marriage|spouse|partner|relationship|7th|dara|kalatra)\b/i, intent: 'marriage_deepdive', domains: ['marriage'] },
  // VIDHI-PŪRṆATĀ P-2 (F1): the three new life-domain deepdives, placed BEFORE the generic
  // structure/panoramic catch-alls so a specific-domain keyword wins the first-hit-wins scan.
  // 'progeny' is keyed off the children/progeny/putra vocabulary (the classifier's DOMAIN is
  // 'children'; the compiler IntentClass is 'progeny_deepdive' — P-0 (b) naming reconciliation).
  { re: /\b(spiritual|spirituality|moksha|mokṣa|liberation|dharma|sadhana|sādhana|renunciation|sannyas|sannyāsa|pravrajya|enlightenment|self.?realization|kundalini)\b/i, intent: 'spirituality_deepdive', domains: ['spirituality'] },
  { re: /\b(education|study|studies|academic|vidya|vidyā|degree|exam|scholar|schooling|learning|college|university)\b/i, intent: 'education_deepdive', domains: ['education'] },
  { re: /\b(progeny|children|child|santana|santāna|putra|offspring|conceive|conception|pregnan|fertility|kids?)\b/i, intent: 'progeny_deepdive', domains: ['children'] },
  { re: /\b(structure|orient|overview|snapshot|lagna|whole.?chart)\b/i, intent: 'structure_read', domains: ['general'] },
  { re: /\b(everything|panoram|all.?domains|comprehensive|full.?life|breadth)\b/i, intent: 'panoramic_breadth', domains: ['general'] },
];

/**
 * Resolve a scope tuple from either a passed-in (DR-8) tuple or a question string.
 *
 * Precedence:
 *   - if `input` carries an `intent`, treat it as a received DR-8 tuple (validate enums,
 *     fill defaults, echo it back) — `method: 'received_scope_tuple'`.
 *   - else keyword-resolve from `question` — `method: 'v2_fallback_keyword'`,
 *     `fallback_recommended: true`.
 *
 * Always total: an unmatched question resolves to `general_synthesis`/`structure` depth.
 */
export function resolveScopeTuple(question: string | undefined, input?: ScopeTupleInput): ResolvedScope {
  // Path 1: a caller supplied a classified tuple (from intent_classify or by hand).
  if (input && input.intent !== undefined) {
    const domains = input.domains && input.domains.length > 0 ? [...input.domains] : ['general'];
    let intent = coerce<IntentClass>(input.intent, INTENT_CLASSES, 'general_synthesis');
    const matched_rules: string[] = ['received_scope_tuple'];
    // E-4 domain→deepdive promotion (VIDHI-PŪRṆATĀ P-3b). intent_classify (DR-8) emits a
    // CLASSIFIER-vocab intent (domain_assessment / chart_overview / dasha_timing / …) that is
    // NOT a compiler IntentClass, so `coerce` lands it on general_synthesis — which would send a
    // clearly-classifiable domain question to the E-0 foundation instead of its dedicated
    // deepdive, AND would stop the E-4 union from ever firing on the authoritative path. When the
    // coercion fell back to general_synthesis AND the caller named ≥1 deepdive domain, promote the
    // primary intent to the FIRST mapped deepdive (the compiler then UNIONS the remaining domains'
    // floors). A caller who genuinely wants the foundation names domains ['general'] (or none) → no
    // promotion. Closes the P-0(b) MCP received-tuple bridge gap; consistent with the depth-default
    // doctrine (a classifiable domain question resolves toward MORE depth, never the thin fallback).
    if (intent === 'general_synthesis') {
      const promoted = domains.map((d) => DOMAIN_TO_INTENT[d]).find((i): i is IntentClass => i !== undefined);
      if (promoted) {
        intent = promoted;
        matched_rules.push(`domain_promotion:${promoted}`);
      }
    }
    // Depth: an explicitly-supplied VALID depth is honored verbatim (the correction path).
    // When depth is OMITTED, default from the resolved INTENT per the DEPTH-DEFAULT DOCTRINE
    // (F5) — NOT a flat 'deepdive', which would wrongly deepen a structure_read / retrieval_only
    // received tuple that merely left depth unset.
    const depth: ScopeDepth =
      input.depth !== undefined && (DEPTHS as readonly string[]).includes(input.depth)
        ? (input.depth as ScopeDepth)
        : defaultDepthForIntent(intent);
    // Intervention (F6): an explicit boolean is honored; when OMITTED, default from the INTENT —
    // a full-read intent carries its intervention/remedy layer by default, not behind a keyword.
    const intervention = input.intervention ?? defaultInterventionForIntent(intent);
    const scope_tuple: ScopeTuple = {
      intent,
      domains,
      width: coerce<ScopeWidth>(input.width, WIDTHS, 'standard'),
      depth,
      horizon: coerce<ScopeHorizon>(input.horizon, HORIZONS, 'current'),
      intervention,
      entitlement: coerce<ScopeEntitlement>(input.entitlement, ENTITLEMENTS, 'native'),
    };
    return {
      scope_tuple,
      method: 'received_scope_tuple',
      matched_rules,
      fallback_recommended: false,
      note:
        'Scope tuple was supplied by the caller (DR-8 intent_classify shape) and is echoed ' +
        'verbatim for correction before execution.' +
        (matched_rules.length > 1
          ? ' The primary intent was promoted from a classifier-vocab/general intent to a domain ' +
            'deepdive (E-4 multi-domain); correct it if that domain is not the focus.'
          : ''),
    };
  }

  // Path 2: coarse keyword fallback from the question text.
  const q = question ?? '';
  const matched_rules: string[] = [];
  let intent: IntentClass = 'general_synthesis';
  // E-4 multi-domain (VIDHI-PŪRṆATĀ P-3b): collect ALL matched domains, NOT first-hit-wins. The
  // FIRST matching rule (KEYWORD_INTENTS is ordered by specificity — the domain deepdives lead)
  // sets the PRIMARY intent; every subsequent matching DOMAIN rule contributes its domain to the
  // union set, and the compiler UNIONS the matched deepdive floors. The generic structure_read /
  // panoramic_breadth catch-alls carry the 'general' pseudo-domain, which is skipped here — it is
  // not a union domain (a domain question that also trips 'overview' must not have its focus diluted).
  const domainSet: string[] = [];
  for (const rule of KEYWORD_INTENTS) {
    if (!rule.re.test(q)) continue;
    if (intent === 'general_synthesis') {
      intent = rule.intent;
      matched_rules.push(`keyword:${rule.intent}`);
    } else {
      matched_rules.push(`keyword:${rule.intent}<-multi_domain`);
    }
    for (const d of rule.domains) {
      if (d !== 'general' && !domainSet.includes(d)) domainSet.push(d);
    }
  }
  const domains: string[] = domainSet.length > 0 ? domainSet : ['general'];
  // Intervention (F6): intent-driven by default — a full-read intent INCLUDES its remedy/
  // intervention layer WITHOUT a "remedy/mantra" magic word (the pre-P-1 keyword gate). A remedy
  // keyword can still opt a REDUCED intent (structure_read / retrieval_only) into that layer.
  const remedyKeyword = /\b(remedy|remedies|upaya|remediation|mitigat|mantra|yantra)\b/i.test(q);
  const intervention = defaultInterventionForIntent(intent) || remedyKeyword;
  if (remedyKeyword) matched_rules.push('keyword:intervention');
  // Depth (F5): intent-driven default — the "deep/detailed/thorough" keyword gate is RETIRED.
  // Deepdive is the default state of the instrument; only the two reduced intents resolve below
  // it, and an unmatched question (general_synthesis) stays deepdive-equivalent, never trimmed.
  // See the DEPTH-DEFAULT DOCTRINE on defaultDepthForIntent above.
  const depth: ScopeDepth = defaultDepthForIntent(intent);
  matched_rules.push(`depth:${depth}<-intent`);

  const scope_tuple: ScopeTuple = {
    intent,
    domains,
    width: 'standard',
    depth,
    horizon: 'current',
    intervention,
    entitlement: 'native',
  };
  return {
    scope_tuple,
    method: 'v2_fallback_keyword',
    matched_rules,
    fallback_recommended: true,
    note:
      'Resolved by the V-2 coarse keyword fallback — NOT the authoritative classifier. Prefer ' +
      "V-3's intent_classify (DR-8) and pass its scope_tuple to plan_retrieval. Tuple echoed for " +
      'correction before execution.',
  };
}
