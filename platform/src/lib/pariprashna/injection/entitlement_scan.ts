/**
 * Paripraśna injection containment — THE ANSWER-SIDE ENTITLEMENT SCAN
 * (lane G1-G, PPR-13 / PPR-11).
 *
 * TA §14A.1: "Answer-side scan: an answer must not contain `chart_id`s or facts
 * from a chart the caller is not entitled to. The register lint (§13.5) already
 * walks the text; entitlement checking is a second pattern class in the same
 * pass."
 *
 * This module supplies the PATTERNS. The PASS is `safety/phrasing_scan.ts` —
 * these rules are handed to it as `extraRules` and share its sentence splitter,
 * its sentence-level redaction unit, its hash-not-content reporting, its
 * streaming holdback and carry, and above all its FAIL-CLOSED catch. Nothing
 * here re-implements a walk over text, and nothing here touches G1-A's
 * mortality rules.
 *
 * ── WHAT THIS DETECTS, STATED AT ITS ACTUAL WIDTH (§N.8) ────────────────────
 * The claim this scan makes is narrow and exact: **no chart identifier that is
 * not one of the caller's authorized charts reaches the reader.** Two forms:
 *
 *   1. `entitlement_foreign_chart_uuid` — a full RFC-4122-shaped UUID that is
 *      not in the authorized set. This is the zero-false-positive rule: a UUID
 *      does not occur in Jyotish prose by accident, and every chart id in this
 *      system is one.
 *   2. `entitlement_foreign_chart_id_prefix` — the ABBREVIATED form the project
 *      itself uses in prose ("Abhinandan Mohanty `1c826d5a`"): a run of 8–32
 *      hex characters sitting next to a chart-referential cue word, which is
 *      not a prefix of any authorized chart id. The cue word is required
 *      precisely to keep this rule from firing on arbitrary hex.
 *
 * A token that matches neither authorized-set test is treated as FOREIGN, which
 * means an id belonging to no chart at all (a hallucinated one, a stale one) is
 * also redacted. That is the fail-closed direction and it is deliberate: this
 * scan cannot enumerate every chart in the system, so "not provably mine" is
 * the only honest verdict available and the safe one to act on.
 *
 * ── WHAT THIS DOES NOT DETECT, SAID PLAINLY RATHER THAN IMPLIED ─────────────
 * The roadmap row reads "chart_ids/facts not belonging to the caller". The
 * chart_ids half is above. The FACTS half is only PARTIALLY reachable, and the
 * gap is structural rather than an omission:
 *
 *   · A bare fact/signal reference (`SIG.MSR.001`, `PLN.SUN`, `HSE.10`) carries
 *     NO chart identity — the same fact_key exists on every chart. There is no
 *     deterministic test that decides whose fact a bare id is, so this module
 *     does not pretend to one. Those tokens are already hard-redacted for a
 *     different reason by `citations/register_leak_lint.ts`'s `signal_id` /
 *     `fact_id_namespace` patterns, which run on the same prose in the same
 *     commit path — so they do not reach a reader regardless.
 *   · A fact stated in a sentence that ALSO carries a foreign chart reference
 *     IS caught, because the redaction unit is the whole sentence. That is the
 *     real overlap between the two halves and it is where the coverage comes
 *     from.
 *   · A foreign subject's NAME or birth data is out of reach here: names are
 *     not distinguishable from ordinary prose without a lookup this scan does
 *     not perform. Cross-tenant name leakage is prevented upstream, by the
 *     chart-scoping of retrieval itself (`tool_name_bridge.ts` overwrites
 *     `args.chart_id` with the authenticated chart for every `per_chart`
 *     capability) — not by this scan. Recorded so nobody reads a green run here
 *     as proof of something this never looked at.
 *
 * ── ONE KNOWN RESIDUAL, MEASURED RATHER THAN ROUNDED OFF ────────────────────
 * The redaction unit is a SENTENCE, and `splitSentences` treats a newline as a
 * sentence terminator. A UUID hard-wrapped across a line break therefore lands
 * in two different sentences and neither half is a complete UUID. What actually
 * happens in that case: the half carrying the chart-referential cue word IS
 * redacted by the prefix rule (so the claim goes), and the trailing fragment —
 * at most the UUID's final 12 hex characters, with no cue word and no claim
 * attached — survives. That is a partial identifier reaching the reader, not a
 * usable chart id, and it is the honest width of the residual.
 *
 * It is NOT closed by widening these rules to the cross-sentence window, which
 * is why that was not done: joining the two sentences leaves the newline INSIDE
 * the token, so the UUID pattern still does not match. Closing it properly
 * means normalizing whitespace across a sentence boundary, which would change
 * G1-A's splitter — out of scope for this lane and a deliberate hand-off rather
 * than an oversight. The whitespace-collapsed pass below closes the
 * SAME-sentence version of this evasion, which is the common one.
 */

import type { PreWireSentenceRule } from '@/lib/pariprashna/safety/phrasing_scan'

/** Full RFC-4122-shaped UUID. Global: reused per call via a `lastIndex` reset. */
const UUID_RE = /\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b/g

/**
 * The same UUID, tolerating whitespace around its own hyphens — the shape a
 * wrapped or deliberately spaced-out id takes. See `findForeignChartReferences`
 * for why this is a separate pattern and not a collapsed copy of the sentence.
 */
const SPACED_UUID_RE =
  /\b[0-9a-fA-F]{8}\s*-\s*[0-9a-fA-F]{4}\s*-\s*[0-9a-fA-F]{4}\s*-\s*[0-9a-fA-F]{4}\s*-\s*[0-9a-fA-F]{12}\b/g

/**
 * A chart-referential cue word followed within a short window by a hex run, and
 * the mirror form (hex run followed by a cue). The window is intra-sentence by
 * construction — the caller only ever hands this one sentence.
 *
 * `[^\n]{0,24}?` is lazy and newline-free so "chart" on one line and a hex token
 * three lines later do not pair up.
 *
 * CASE-INSENSITIVE, and the reason is a real evasion the adversarial suite
 * found rather than a style choice: without `i`, `chartId` matches neither the
 * `chart` alternative (no word boundary between `t` and `I`) nor the
 * `chart[_\s-]?id` one (case), so the single most idiomatic camelCase spelling
 * of the key walked straight past this rule.
 *
 * Upper bound 64, not 32, for the same reason: a token that merely BEGINS with
 * an authorized id is a different identifier, and at 32 the appended-suffix
 * form (`<authorized-32-hex>ff`) fell outside the quantifier and matched
 * nothing at all. 64 covers a hyphen-stripped UUID (32), a sha256 (64), and
 * every suffixed variant in between.
 */
const CUE_THEN_HEX_RE = /\bchart(?:[_\s-]?id)?\b[^\n]{0,24}?\b([0-9a-fA-F]{8,64})\b/gi
const HEX_THEN_CUE_RE = /\b([0-9a-fA-F]{8,64})\b[^\n]{0,24}?\bchart(?:[_\s-]?id)?\b/gi

export interface EntitlementScanConfig {
  /**
   * Every chart id the CALLER is authorized for — at minimum the turn's own
   * `chart_id`, which comes from the authenticated call and never from question
   * text (PPR-11). An empty array is legal and means "nothing is authorized",
   * so every chart reference in the answer is foreign. That is the correct
   * fail-closed reading of "the caller's entitlements could not be resolved".
   */
  readonly authorizedChartIds: readonly string[]
}

/** Rule ids. Stable, reported on the wire, never derived from content. */
export const ENTITLEMENT_RULE_FOREIGN_UUID = 'entitlement_foreign_chart_uuid'
export const ENTITLEMENT_RULE_FOREIGN_PREFIX = 'entitlement_foreign_chart_id_prefix'

/** Canonical comparison form: lowercase, hyphens removed. */
function canonical(id: string): string {
  return id.toLowerCase().replace(/-/g, '')
}

interface AuthorizedSet {
  /** Canonical full ids, for the exact-UUID test. */
  full: ReadonlySet<string>
  /** The same ids, for the prefix test. */
  canonicalIds: readonly string[]
}

function buildAuthorizedSet(config: EntitlementScanConfig): AuthorizedSet {
  const canonicalIds = (config.authorizedChartIds ?? [])
    .filter((id): id is string => typeof id === 'string' && id.length > 0)
    .map(canonical)
  return { full: new Set(canonicalIds), canonicalIds }
}

/** True when `token` is (or abbreviates) an authorized chart id. */
function isAuthorizedReference(token: string, authorized: AuthorizedSet): boolean {
  const c = canonical(token)
  if (authorized.full.has(c)) return true
  // An abbreviation is a PREFIX of an authorized id. The reverse direction is
  // not accepted: a longer token that merely starts with an authorized id is a
  // different identifier, not that one.
  return authorized.canonicalIds.some((id) => id.startsWith(c))
}

/** Every hex/UUID token in `sentence` that is not provably the caller's. */
export function findForeignChartReferences(
  sentence: string,
  config: EntitlementScanConfig,
): { rule: string; token: string }[] {
  const authorized = buildAuthorizedSet(config)
  const found: { rule: string; token: string }[] = []
  const seen = new Set<string>()

  const push = (rule: string, token: string): void => {
    if (isAuthorizedReference(token, authorized)) return
    const key = `${rule}:${canonical(token)}`
    if (seen.has(key)) return
    seen.add(key)
    found.push({ rule, token })
  }

  // Full UUIDs first, and record which spans they occupied — a UUID's own
  // leading 8 hex digits would otherwise ALSO trip the prefix rule next to the
  // word "chart", double-reporting one leak as two.
  const uuidSpans: [number, number][] = []
  UUID_RE.lastIndex = 0
  for (let m = UUID_RE.exec(sentence); m !== null; m = UUID_RE.exec(sentence)) {
    uuidSpans.push([m.index, m.index + m[0].length])
    push(ENTITLEMENT_RULE_FOREIGN_UUID, m[0])
  }

  // …then the SPACED form, which catches an id pulled apart at its own hyphens
  // ("1c826d5a-9f3b-4d21 -8e77-0a5c4b2e91d0" — a wrap, or deliberate spacing).
  //
  // Done as a segment-aware pattern rather than by scanning a
  // whitespace-collapsed copy of the sentence, and the reason is a real bug the
  // adversarial suite caught: collapsing glues the id to the word in front of
  // it, and since `a`–`f` are hex letters, an ordinary English word ending in
  // one ("used", "café") destroys the leading `\b` and the UUID stops matching
  // altogether. Tolerating whitespace only WHERE THE HYPHENS ALREADY ARE keeps
  // both anchors intact.
  SPACED_UUID_RE.lastIndex = 0
  for (let m = SPACED_UUID_RE.exec(sentence); m !== null; m = SPACED_UUID_RE.exec(sentence)) {
    uuidSpans.push([m.index, m.index + m[0].length])
    push(ENTITLEMENT_RULE_FOREIGN_UUID, m[0].replace(/\s+/g, ''))
  }
  const insideUuid = (start: number, end: number): boolean =>
    uuidSpans.some(([s, e]) => start >= s && end <= e)

  for (const re of [CUE_THEN_HEX_RE, HEX_THEN_CUE_RE]) {
    re.lastIndex = 0
    for (let m = re.exec(sentence); m !== null; m = re.exec(sentence)) {
      const token = m[1]
      const at = m[0].indexOf(token) + m.index
      if (insideUuid(at, at + token.length)) continue
      push(ENTITLEMENT_RULE_FOREIGN_PREFIX, token)
    }
  }

  return found
}

/**
 * The two rules, ready to hand to `scanMortalityPhrasing`/
 * `StreamingMortalityScanner` as `extraRules`.
 *
 * Two rules rather than one so the hit's `rule` field distinguishes the
 * zero-false-positive UUID form from the heuristic abbreviation form without
 * anyone having to re-derive which fired from a count.
 */
export function buildEntitlementScanRules(config: EntitlementScanConfig): PreWireSentenceRule[] {
  return [
    {
      rule: ENTITLEMENT_RULE_FOREIGN_UUID,
      test: (sentence) =>
        findForeignChartReferences(sentence, config).some(
          (f) => f.rule === ENTITLEMENT_RULE_FOREIGN_UUID,
        ),
    },
    {
      rule: ENTITLEMENT_RULE_FOREIGN_PREFIX,
      test: (sentence) =>
        findForeignChartReferences(sentence, config).some(
          (f) => f.rule === ENTITLEMENT_RULE_FOREIGN_PREFIX,
        ),
    },
  ]
}

/**
 * The reader-facing notice, emitted ONCE when the entitlement scan removed
 * anything — the same discipline as `PREWIRE_REDACTION_NOTICE`: a withholding
 * is never silent.
 *
 * It deliberately does not say WHICH chart or HOW MANY sentences. Telling the
 * reader "a reference to chart X was removed" would leak the very identifier
 * the removal exists to protect.
 */
export const ENTITLEMENT_REDACTION_NOTICE =
  'Part of this reading was withheld at the output stage: it referenced a chart outside the ones this session is authorized to read.'
