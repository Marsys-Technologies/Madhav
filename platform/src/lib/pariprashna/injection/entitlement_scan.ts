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
 * ── WHAT AN INDEPENDENT REVIEW FOUND, AND WHERE IT LEFT THINGS ──────────────
 * Five real bypasses were reproduced against the first version of this module.
 * Each is now closed and pinned by a test; they are listed because the SHAPE of
 * the mistakes is more useful to the next person than the fixes:
 *
 *   1. `\b` anchors on the UUID pattern. There is no word boundary between two
 *      hex characters, so `x<id>` and `<id>ff` matched nothing at all — one
 *      adjacent character disabled the module's only zero-false-positive rule.
 *      Anchors removed: hex adjacency should raise suspicion, not grant
 *      exemption.
 *   2. Literal-surface-only scanning. An id written with en-dashes or fullwidth
 *      digits read clean. Now scanned on the folded surface too, exactly as
 *      G1-A's `sentenceHit` does — and on `.literal`, never `.normalized`,
 *      because confusable folding rewrites digits into letters and would blind
 *      this scan to the very tokens it hunts.
 *   3. The hyphen-stripped 32-hex form had no rule at all.
 *   4. A token split across a sentence boundary — including the newline the
 *      streaming forced release lands on — was never rejoined, leaking a
 *      COMPLETE foreign id across a stream seam. Closed by sharing G1-A's
 *      cross-sentence window with these rules (the module used to argue that a
 *      window was unnecessary here; that argument was wrong, see
 *      `phrasing_scan.ts`).
 *   5. `[0-9a-fA-F]{8,64}` matched any 8+ digit DECIMAL number, so "Julian day
 *      24457355" near the word "chart" deleted the sentence and raised a
 *      cross-tenant alarm. The prefix rule now requires a hex letter.
 *
 * A SECOND independent re-verification then reproduced three more, all of the
 * same family — a bound that was supposed to describe a token and instead made
 * some tokens unmatchable:
 *
 *   6. A run of MORE than 64 hex characters near a cue word matched NOTHING.
 *      `{8,64}` plus the strict lookbehind/lookahead is unsatisfiable at every
 *      start offset inside a 66-character run, so raising the ceiling from 32
 *      to 64 had only moved the hole rather than closed it.
 *   7. A 33+ character run with NO cue word also matched nothing: `{32}` meant
 *      exactly 32, so one appended character (`<foreign-32-hex>f`) defeated the
 *      rule outright. Both are now gone the only way they can be — the ceiling
 *      is off the no-cue rule entirely (`{32,}`, the whole contiguous run is
 *      the token) and the cue rule takes the band strictly below it (8–31), so
 *      the two together cover every length from 8 up with no gap.
 *   8. `CROSS_SENTENCE_WINDOW = 2` closes a TWO-fragment split of a token and
 *      nothing wider. A foreign UUID broken at two of its own hyphens is THREE
 *      terminator-separated fragments, streamed out complete, zero hits. Closed
 *      by a token-continuity rejoin in `phrasing_scan.ts` that is unbounded in
 *      fragment count but only rejoins across boundaries where a token could
 *      actually continue — and, on this side, by the UUID pattern tolerating
 *      whitespace between any two of its hex characters rather than only around
 *      its hyphens (a break inside a hex group is not a break at a hyphen).
 *
 * ── THE RESIDUALS, NAMED ────────────────────────────────────────────────────
 *   · A chart referred to WITHOUT any identifier — by the subject's name, or as
 *     "the other reading" — is invisible to this scan. Stated under "what this
 *     does not detect" above; upstream retrieval's job, not this scan's.
 *   · The HYPHEN-STRIPPED 32-hex form fragmented by whitespace
 *     (`1c826d5a9f3b4d21` ⏎ `8e770a5c4b2e91d0`) is NOT reassembled, unlike the
 *     hyphenated form. This is a deliberate refusal rather than an oversight:
 *     the only pattern that could reassemble it is a whitespace-tolerant 32-run,
 *     and that pattern has a real false positive in ordinary English —
 *     `effaced defaced facade decade beaded` is exactly 32 characters all drawn
 *     from `[a-f]`, separated only by spaces. Deleting a sentence of legitimate
 *     prose AND raising a cross-tenant alarm on it is a worse outcome than the
 *     residual, so the residual is kept and written down. The hyphenated form —
 *     the one an id is actually written in, and the one whose 8-4-4-4-12
 *     structure makes the shape unambiguous — IS reassembled at any
 *     fragmentation, down to one character per line.
 */

import type { PreWireSentenceRule } from '@/lib/pariprashna/safety/phrasing_scan'
import { normalizeForClassification } from '@/lib/pariprashna/safety/normalize'

/**
 * Full RFC-4122-shaped UUID, tolerating whitespace ANYWHERE inside it — around
 * its own hyphens AND between two hex characters of the same group — and
 * DELIBERATELY UNANCHORED.
 *
 * The first version used `\b` at both ends, and a review reproduced the
 * consequence: `\b` between two hex characters does not exist, so ONE adjacent
 * word character made the whole id invisible. `See record x<id> here` and
 * `<id>ff` both leaked with zero hits. An injected payload only had to ask for
 * the id to be cited with a prefix.
 *
 * The anchors are gone rather than inverted, and that is the right direction:
 * hex adjacency should make a token MORE suspicious, not exempt. A UUID-shaped
 * run inside a longer hex blob is still a UUID-shaped run, and there is no
 * legitimate Jyotish prose it appears in.
 *
 * The second version tolerated whitespace only around the four hyphens, and a
 * re-verification reproduced what that leaves open: a break INSIDE a hex group
 * (`1c826d5a-9f3` / newline / `b-4d21-…`) is not around a hyphen, so the
 * rejoined token matched nothing. Since the streaming forced release lands on a
 * character offset rather than a token boundary, and since an injected payload
 * controls its own line breaks, that is the ordinary case rather than the exotic
 * one. `(?:hex\s*)` per character closes it.
 *
 * Whitespace tolerance is safe HERE and nowhere else in this module because the
 * 8-4-4-4-12 hyphen structure is what makes the shape unambiguous: no run of
 * English words reproduces it. `BARE_HEX_RUN_RE` below has no such structure and
 * therefore stays strictly contiguous — see its own note for the counterexample.
 *
 * There is deliberately no separate strict (unspaced) pattern: `\s*` matches
 * empty, so this one sweep covers both and a second would only ever produce a
 * duplicate finding for `seen` to collapse. `[0-9a-fA-F]` and `\s` are disjoint
 * classes, so the nested quantifier cannot backtrack catastrophically.
 */
const SPACED_UUID_RE =
  /(?:[0-9a-fA-F]\s*){8}-\s*(?:[0-9a-fA-F]\s*){4}-\s*(?:[0-9a-fA-F]\s*){4}-\s*(?:[0-9a-fA-F]\s*){4}-\s*(?:[0-9a-fA-F]\s*){12}/g

/**
 * A chart id with its hyphens removed — the form `canonical()` produces and the
 * form a model echoing a DB key or a cache key emits. 32 hex characters in a
 * row is not something Jyotish prose contains, so this needs no cue word.
 *
 * Bounded on both sides by "not another hex character", and with NO UPPER BOUND,
 * so the whole contiguous run is the token. The previous `{32}` (exactly 32)
 * combined with those bounds meant a 33-character run matched NOTHING AT ALL —
 * one appended character defeated the rule outright, which a re-verification
 * reproduced with `The reference key is <foreign-32-hex>f.` The comment here
 * already claimed the intent ("that whole run is the token, and
 * `isAuthorizedReference` must judge it as one"); `{32,}` is what finally makes
 * that true instead of aspirational. `isAuthorizedReference` then judges the
 * WHOLE run — a 33-hex run is not any authorized id and is not a prefix of one,
 * so it is correctly foreign rather than invisible.
 *
 * Strictly CONTIGUOUS, unlike `SPACED_UUID_RE`, and this is the one place the
 * two forms must differ. A whitespace-tolerant 32-run has a real false positive
 * in ordinary English: `effaced defaced facade decade beaded` is exactly 32
 * characters all drawn from `[a-f]`, separated only by spaces. Redacting a
 * sentence of legitimate prose AND raising a cross-tenant alarm on it is the
 * worst possible trade, so the whitespace-fragmented hyphen-stripped form stays
 * a stated residual (module header) rather than a false-positive generator.
 */
const BARE_HEX_RUN_RE = /(?<![0-9a-fA-F])[0-9a-fA-F]{32,}(?![0-9a-fA-F])/g

/**
 * A chart-referential cue word followed within a short window by a hex run, and
 * the mirror form (hex run followed by a cue). The window is intra-sentence by
 * construction — the caller only ever hands this one sentence.
 *
 * `[^\n]{0,80}?` is lazy and newline-free so "chart" on one line and a hex token
 * three lines later do not pair up. 80 rather than the original 24 because a
 * review reproduced the gap at 24 with an entirely natural sentence — "The
 * other chart, which belongs to a different native entirely, is 1c826d5a
 * today." — where one relative clause is enough to push the id out of range.
 * Widening is cheap now that `HAS_HEX_LETTER` (below) gates the token: a false
 * positive would have to be an 8+ character run of nothing but hex characters,
 * including at least one of a–f, sitting near the word "chart" — which is an
 * id, not prose.
 *
 * CASE-INSENSITIVE, and the reason is a real evasion the adversarial suite
 * found rather than a style choice: without `i`, `chartId` matches neither the
 * `chart` alternative (no word boundary between `t` and `I`) nor the
 * `chart[_\s-]?id` one (case), so the single most idiomatic camelCase spelling
 * of the key walked straight past this rule.
 *
 * ── THE LENGTH BAND, AND WHY IT IS 8–31 RATHER THAN 8–64 ────────────────────
 * The two versions before this one both had a length bound that made some runs
 * UNMATCHABLE rather than merely unmatched, and a re-verification reproduced
 * both directions:
 *
 *   · At `{8,32}` the appended-suffix form (`<authorized-32-hex>ff`) fell
 *     outside the quantifier and matched nothing.
 *   · At `{8,64}` a 65+ character run matched nothing EITHER: the strict
 *     lookbehind/lookahead mean no start offset inside a 66-character run can
 *     satisfy both bounds, so raising the ceiling only moved the hole.
 *
 * A fixed ceiling on a rule whose lookarounds demand the WHOLE run always has
 * that hole somewhere. So the ceiling is gone from the problem instead of moved:
 * `BARE_HEX_RUN_RE` above now claims every contiguous run of 32 OR MORE hex
 * characters with no cue word required, and this rule takes the band BELOW it —
 * 8 to 31 — which is exactly the abbreviated form that needs a cue word to be
 * distinguishable from arbitrary hex. Between them the two rules cover every
 * length from 8 upward with no gap and no double-report.
 */
const CUE_THEN_HEX_RE = /\bchart(?:[_\s-]?id)?\b[^\n]{0,80}?(?<![0-9a-fA-F])([0-9a-fA-F]{8,31})(?![0-9a-fA-F])/gi
const HEX_THEN_CUE_RE = /(?<![0-9a-fA-F])([0-9a-fA-F]{8,31})(?![0-9a-fA-F])[^\n]{0,80}?\bchart(?:[_\s-]?id)?\b/gi

/**
 * A prefix-rule token must contain at least one hex LETTER.
 *
 * Without this, `[0-9a-fA-F]{8,64}` matches any 8+ digit decimal number, and a
 * review reproduced the consequence: "The chart uses Julian day 24457355 for
 * the epoch", "This chart was built at 20240115", "Chart totals: 100000000
 * divisional rows" were all silently deleted from the reading AND raised an
 * error-level cross-tenant flag. That is a false positive that eats real
 * astrological content and cries wolf at the same time — the worst combination.
 *
 * A real chart id is a random 128-bit value; the probability its abbreviated
 * form is all-decimal is negligible, so this costs the detector essentially
 * nothing and buys back every Julian day, epoch, year and row count in the
 * corpus. The full-UUID rules do NOT apply it — their shape is already
 * unambiguous, hyphens and all.
 */
const HAS_HEX_LETTER = /[a-fA-F]/

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
  // An empty token would make the prefix test below vacuously TRUE for every
  // authorized id (`'x'.startsWith('') === true`) and turn this function into
  // "everything is authorized". The regexes cannot produce one, but this
  // function is exported and the failure direction here is unsafe, so it is
  // closed at the source rather than relied on from the caller.
  if (!c) return false
  if (authorized.full.has(c)) return true
  // An abbreviation is a PREFIX of an authorized id. The reverse direction is
  // not accepted: a longer token that merely starts with an authorized id is a
  // different identifier, not that one.
  return authorized.canonicalIds.some((id) => id.startsWith(c))
}

/**
 * Every hex/UUID token in `sentence` that is not provably the caller's.
 *
 * Runs over TWO surfaces, exactly as G1-A's `sentenceHit` does and for the same
 * reason: the literal text, and `normalizeForClassification(...).literal` — a
 * NFKD-normalized, diacritic-stripped, punctuation-folded, whitespace-collapsed
 * view. That second surface is what catches an id written with en-dashes or
 * fullwidth digits, both of which a review reproduced as clean leaks against
 * the literal-only version.
 *
 * `.literal` and NOT `.normalized`: the confusable folding that lets the safety
 * classifier read `d1e` as `die` also rewrites digits into letters, which would
 * turn a real chart id into a different, harmless-looking token and blind this
 * scan to precisely what it exists to catch. Same trap G1-A documents at
 * `sentenceHit`, same resolution.
 */
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

  const surfaces = [sentence]
  const folded = normalizeForClassification(sentence).literal
  if (folded && folded !== sentence) surfaces.push(folded)

  for (const surface of surfaces) {
    // Full UUIDs first, and record which spans they occupied — a UUID's own
    // leading 8 hex digits would otherwise ALSO trip the prefix rule next to
    // the word "chart", double-reporting one leak as two.
    const uuidSpans: [number, number][] = []

    // The SPACED pattern SUBSUMES the strict one (`\s*` matches empty), so this
    // one sweep covers both a plain RFC-4122 UUID and one pulled apart at its
    // own hyphens ("1c826d5a-9f3b-4d21 -8e77-0a5c4b2e91d0" — a wrap, or
    // deliberate spacing). Done as a segment-aware pattern rather than by
    // scanning a whitespace-collapsed copy of the sentence, because collapsing
    // glues the id to the word in front of it and — since a-f are hex letters —
    // an ordinary English word ending in one ("used") would then swallow it.
    SPACED_UUID_RE.lastIndex = 0
    for (let m = SPACED_UUID_RE.exec(surface); m !== null; m = SPACED_UUID_RE.exec(surface)) {
      uuidSpans.push([m.index, m.index + m[0].length])
      push(ENTITLEMENT_RULE_FOREIGN_UUID, m[0].replace(/\s+/g, ''))
    }

    // The hyphen-stripped form, at 32 characters OR LONGER. No cue word
    // required — 32 hex characters in a row is not a thing Jyotish prose
    // contains, and the whole run is judged as one token.
    BARE_HEX_RUN_RE.lastIndex = 0
    for (let m = BARE_HEX_RUN_RE.exec(surface); m !== null; m = BARE_HEX_RUN_RE.exec(surface)) {
      uuidSpans.push([m.index, m.index + m[0].length])
      push(ENTITLEMENT_RULE_FOREIGN_UUID, m[0])
    }

    const insideUuid = (start: number, end: number): boolean =>
      uuidSpans.some(([s, e]) => start >= s && end <= e)

    for (const re of [CUE_THEN_HEX_RE, HEX_THEN_CUE_RE]) {
      re.lastIndex = 0
      for (let m = re.exec(surface); m !== null; m = re.exec(surface)) {
        const token = m[1]
        // An all-decimal run is a Julian day, a year, a row count — not an id.
        if (!HAS_HEX_LETTER.test(token)) continue
        const at = m[0].indexOf(token) + m.index
        if (insideUuid(at, at + token.length)) continue
        push(ENTITLEMENT_RULE_FOREIGN_PREFIX, token)
      }
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
  // The two rules are asked about the SAME sentence back-to-back by the pre-wire
  // pass, and in the streaming path that pass runs on every released span. A
  // one-entry memo turns four regex sweeps per span into two, with no
  // behavioural difference: `findForeignChartReferences` is pure, and the memo
  // is keyed on the exact text.
  //
  // ONE ENTRY, NOT A MAP, and the reason is confidentiality rather than
  // efficiency: an unbounded cache here would retain reader prose (C1 content)
  // for the life of the turn, which is the opposite of what this module is for.
  // The access pattern it was originally sized for — "same sentence twice, then
  // move on" — is no longer the only one, since the windowed and continuity
  // passes ask about joined spans in between; the memo simply hits less often
  // there. That is a deliberate trade of a few short regex sweeps for not
  // holding the reading in memory, not an oversight.
  let lastSentence: string | null = null
  let lastFindings: { rule: string; token: string }[] = []
  const findingsFor = (sentence: string): { rule: string; token: string }[] => {
    if (sentence !== lastSentence) {
      lastFindings = findForeignChartReferences(sentence, config)
      lastSentence = sentence
    }
    return lastFindings
  }

  return [
    {
      rule: ENTITLEMENT_RULE_FOREIGN_UUID,
      test: (sentence) => findingsFor(sentence).some((f) => f.rule === ENTITLEMENT_RULE_FOREIGN_UUID),
    },
    {
      rule: ENTITLEMENT_RULE_FOREIGN_PREFIX,
      test: (sentence) => findingsFor(sentence).some((f) => f.rule === ENTITLEMENT_RULE_FOREIGN_PREFIX),
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
