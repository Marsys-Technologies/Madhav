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

const INTENT_CLASSES: readonly IntentClass[] = [
  'wealth_deepdive',
  'career_deepdive',
  'health_deepdive',
  'marriage_deepdive',
  'structure_read',
  'panoramic_breadth',
  'retrieval_only',
  'general_synthesis',
];
const WIDTHS: readonly ScopeWidth[] = ['narrow', 'standard', 'panoramic'];
const DEPTHS: readonly ScopeDepth[] = ['retrieval', 'structure', 'deepdive'];
const HORIZONS: readonly ScopeHorizon[] = ['natal', 'current', 'multi_year'];
const ENTITLEMENTS: readonly ScopeEntitlement[] = ['native', 'research', 'public_disclosed'];

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
    const scope_tuple: ScopeTuple = {
      intent: coerce<IntentClass>(input.intent, INTENT_CLASSES, 'general_synthesis'),
      domains: input.domains && input.domains.length > 0 ? [...input.domains] : ['general'],
      width: coerce<ScopeWidth>(input.width, WIDTHS, 'standard'),
      depth: coerce<ScopeDepth>(input.depth, DEPTHS, 'deepdive'),
      horizon: coerce<ScopeHorizon>(input.horizon, HORIZONS, 'current'),
      intervention: input.intervention ?? false,
      entitlement: coerce<ScopeEntitlement>(input.entitlement, ENTITLEMENTS, 'native'),
    };
    return {
      scope_tuple,
      method: 'received_scope_tuple',
      matched_rules: ['received_scope_tuple'],
      fallback_recommended: false,
      note:
        'Scope tuple was supplied by the caller (DR-8 intent_classify shape) and is echoed ' +
        'verbatim for correction before execution.',
    };
  }

  // Path 2: coarse keyword fallback from the question text.
  const q = question ?? '';
  const matched_rules: string[] = [];
  let intent: IntentClass = 'general_synthesis';
  let domains: string[] = ['general'];
  for (const rule of KEYWORD_INTENTS) {
    if (rule.re.test(q)) {
      intent = rule.intent;
      domains = rule.domains;
      matched_rules.push(`keyword:${rule.intent}`);
      break;
    }
  }
  const intervention = /\b(remedy|remedies|upaya|remediation|mitigat|mantra|yantra)\b/i.test(q);
  if (intervention) matched_rules.push('keyword:intervention');
  const depth: ScopeDepth = /\b(deep|detailed|thorough|full|assessment|deep.?dive)\b/i.test(q)
    ? 'deepdive'
    : 'structure';
  matched_rules.push(`depth:${depth}`);

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
