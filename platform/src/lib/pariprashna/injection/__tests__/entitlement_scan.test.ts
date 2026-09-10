/**
 * Lane G1-G · PPR-13 item 4 — THE ANSWER-SIDE ENTITLEMENT SCAN, ADVERSARIALLY.
 *
 * This is the lane's one genuine security boundary: a chart id belonging to
 * someone else reaching a reader is a cross-tenant confidentiality breach, not a
 * phrasing defect. Per §N.8 the control is only worth something if a detector
 * exists that returns FALSE when the claim is untrue — so this file is written
 * as an ATTACKER first and a maintainer second. Every `it` below is either an
 * attack that must be caught, or a legitimate reading that must NOT be damaged.
 *
 * The two charts used throughout:
 *   MINE    — the authenticated chart for the turn (the canonical native's id).
 *   THEIRS  — a different, real-shaped chart id the caller has no claim on.
 */
import { describe, it, expect } from 'vitest'

import {
  buildEntitlementScanRules,
  findForeignChartReferences,
  ENTITLEMENT_RULE_FOREIGN_UUID,
  ENTITLEMENT_RULE_FOREIGN_PREFIX,
} from '../entitlement_scan'
import { scanMortalityPhrasing, StreamingMortalityScanner } from '@/lib/pariprashna/safety/phrasing_scan'

const MINE = '482012f1-710e-4a25-994a-93821f5871aa'
const THEIRS = '1c826d5a-9f3b-4d21-8e77-0a5c4b2e91d0'
const CONFIG = { authorizedChartIds: [MINE] }
const RULES = buildEntitlementScanRules(CONFIG)

/** The exact composition the pipeline uses: entitlement rules, mortality OFF. */
function prewire(text: string) {
  return scanMortalityPhrasing(text, { extraRules: RULES, mortalityRulesEnabled: false })
}

describe('the primary claim — a foreign chart id never reaches the reader', () => {
  it('redacts the WHOLE sentence carrying a foreign chart UUID', () => {
    const leak =
      `Saturn favours consolidation this year. ` +
      `Comparing against chart ${THEIRS}, the same Saturn return lands eleven months later. ` +
      `Jupiter supports the professional axis throughout.`
    const r = prewire(leak)

    expect(r.clean).not.toContain(THEIRS)
    // Not just the id — the whole claim built on it goes, for the same reason
    // G1-A removes the whole mortality clause rather than the date.
    expect(r.clean).not.toContain('eleven months later')
    // …and the innocent neighbours survive. A scan that eats the reading is not
    // a working scan.
    expect(r.clean).toContain('Saturn favours consolidation this year.')
    expect(r.clean).toContain('Jupiter supports the professional axis throughout.')
    expect(r.extra_hits.map((h) => h.rule)).toContain(ENTITLEMENT_RULE_FOREIGN_UUID)
    expect(r.extra_hits.every((h) => h.caused_redaction)).toBe(true)
  })

  it("does NOT redact the caller's OWN chart id — the claim is cross-tenant, not no-ids", () => {
    const own = `This reading is scoped to chart ${MINE} throughout.`
    expect(prewire(own).clean).toBe(own)
    expect(prewire(own).extra_hits).toHaveLength(0)
  })

  it('an EMPTY authorized set makes every chart reference foreign (fail-closed)', () => {
    // "The caller's entitlements could not be resolved" must never read as
    // "everything is fine".
    const rules = buildEntitlementScanRules({ authorizedChartIds: [] })
    const r = scanMortalityPhrasing(`Scoped to chart ${MINE}.`, {
      extraRules: rules,
      mortalityRulesEnabled: false,
    })
    expect(r.clean).toBe('')
    expect(r.extra_hits).toHaveLength(1)
  })
})

describe('adversarial — evasion attempts on the UUID rule', () => {
  it('catches an UPPERCASE foreign UUID', () => {
    const r = prewire(`The other chart is ${THEIRS.toUpperCase()} and it differs.`)
    expect(r.clean).toBe('')
  })

  it('catches a foreign UUID with no surrounding chart vocabulary at all', () => {
    // The UUID rule deliberately does not require a cue word — an id is an id.
    const r = prewire(`Also relevant: ${THEIRS}.`)
    expect(r.clean).toBe('')
  })

  it('catches a foreign UUID inside markdown/backticks/parentheses', () => {
    for (const wrapped of [`\`${THEIRS}\``, `(${THEIRS})`, `[${THEIRS}]`, `**${THEIRS}**`]) {
      const r = prewire(`See ${wrapped} for the comparison.`)
      expect(r.clean, `wrapped as ${wrapped}`).toBe('')
    }
  })

  it('catches an id broken up by whitespace WITHIN one sentence', () => {
    const spaced = `${THEIRS.slice(0, 18)} ${THEIRS.slice(18)}`
    const r = prewire(`The other reading used ${spaced} as its source.`)
    expect(r.clean).toBe('')
    expect(r.extra_hits.map((h) => h.rule)).toContain(ENTITLEMENT_RULE_FOREIGN_UUID)
  })

  it('an id hard-wrapped across a NEWLINE is fully redacted, both halves', () => {
    // A newline is a sentence terminator, so this splits the token across two
    // sentences. The cross-sentence window rejoins them; before the window was
    // shared with the extra rules, the trailing 24 hex characters survived.
    const wrapped = `The comparison chart ${THEIRS.slice(0, 24)}\n${THEIRS.slice(24)} differs.`
    const r = prewire(wrapped)
    expect(r.clean.trim()).toBe('')
    expect(r.clean).not.toContain(THEIRS.slice(24))
  })

  it('a split id with NO cue word anywhere is still caught by the rejoin', () => {
    const r = prewire(`Also relevant: ${THEIRS.slice(0, 18)}\n${THEIRS.slice(18)} appears.`)
    expect(r.clean.trim()).toBe('')
  })

  it('an id split across THREE fragments is caught (P1-1, the 2-window gap)', () => {
    // `CROSS_SENTENCE_WINDOW = 2` closes the two-fragment seam and nothing more.
    // A UUID broken at two of its own hyphens is THREE terminator-separated
    // fragments and streamed out complete with ZERO hits — and since an
    // injected payload controls its own line breaks, that is inside the threat
    // model. The token-continuity rejoin is what closes it.
    const r = prewire(
      `The other record is ${THEIRS.slice(0, 13)}\n${THEIRS.slice(13, 23)}\n${THEIRS.slice(23)}\nand that is all.`,
    )
    expect(r.clean.replace(/\s+/g, '')).not.toContain(THEIRS)
    // …and the innocent fragment after the token survives: the rejoin marks the
    // SMALLEST run that reassembles the id, not the whole continuity chain.
    expect(r.clean).toContain('and that is all.')
    expect(r.extra_hits.map((h) => h.rule)).toContain(ENTITLEMENT_RULE_FOREIGN_UUID)
  })

  it('an id split at EVERY hyphen — five fragments — is still caught', () => {
    const groups = THEIRS.split('-')
    const text = `Record: ${groups[0]}\n-${groups[1]}\n-${groups[2]}\n-${groups[3]}\n-${groups[4]}\nend.`
    const r = prewire(text)
    expect(r.clean.replace(/\s+/g, '')).not.toContain(THEIRS)
  })

  it('an id split INSIDE a hex group is caught too', () => {
    // The break is not next to a hyphen, so tolerating whitespace only AROUND
    // the hyphens left this one open. The UUID pattern now tolerates whitespace
    // between any two of its hex characters — safe there, and only there,
    // because the 8-4-4-4-12 hyphen structure is what makes the shape
    // unambiguous.
    const r = prewire(`The other record is ${THEIRS.slice(0, 11)}\n${THEIRS.slice(11)} and more.`)
    expect(r.clean.replace(/\s+/g, '')).not.toContain(THEIRS)
  })

  it('one character per line — the maximal split — is caught', () => {
    const r = prewire(`Record: ${THEIRS.split('').join('\n')}\nend.`)
    expect(r.clean.replace(/\s+/g, '')).not.toContain(THEIRS)
  })

  it('the continuity rejoin does NOT fire on ordinary prose', () => {
    // Every sentence of real prose ends in a terminator that is not whitespace,
    // so no continuity boundary exists and this pass finds nothing. This is the
    // assertion that keeps the unbounded fragment count affordable and safe.
    const prose =
      'Saturn is steady. Mars is exalted. Jupiter aspects the seventh.\n' +
      'The tenth lord is strong.\nVenus is neutral. 2024 was a build year.'
    expect(prewire(prose).clean).toBe(prose)
  })

  it('the abbreviated form split from its cue across sentences is caught', () => {
    // The prefix rule IS a pair. "Consider the other chart. Its identifier is
    // 1c826d5a." split the pair and passed clean until the window was shared.
    const r = prewire('Consider the other chart. Its identifier is 1c826d5a and it matters.')
    expect(r.clean.trim()).toBe('')
  })

  it('an ADJACENT word character no longer hides a UUID', () => {
    // `\b` between two hex characters does not exist, so the original anchored
    // pattern was defeated by a single prefix/suffix character.
    for (const form of [`x${THEIRS}`, `${THEIRS}ff`, `ref-x${THEIRS}`, `[${THEIRS}]`]) {
      expect(prewire(`See record ${form} for details.`).clean, form).toBe('')
    }
  })

  it('catches an id written with en-dashes or fullwidth digits', () => {
    const enDash = THEIRS.replace(/-/g, '–')
    expect(prewire(`The other chart is ${enDash}.`).clean).toBe('')
    const fullwidth = THEIRS.replace(/1/g, '１')
    expect(prewire(`The other chart is ${fullwidth}.`).clean).toBe('')
  })

  it('catches the hyphen-stripped 32-hex form with no cue word', () => {
    const stripped = THEIRS.replace(/-/g, '')
    expect(prewire(`Cache key ${stripped} was used.`).clean).toBe('')
    // …and the caller's own id in that form is still fine.
    const mine = MINE.replace(/-/g, '')
    const own = `Cache key ${mine} was used.`
    expect(prewire(own).clean).toBe(own)
  })

  it('catches a UUID that is UNKNOWN to the system, not merely a known other chart', () => {
    // "Not provably mine" is the only honest verdict available to a scan that
    // cannot enumerate every chart, and it is the safe one to act on.
    const r = prewire(`Cross-referencing 00000000-0000-4000-8000-000000000000 gives a different arc.`)
    expect(r.clean).toBe('')
  })

  it('an EMPTY token is not authorized — the prefix test must not go vacuous', () => {
    // `'anything'.startsWith('')` is true, so a bare `''` would otherwise be
    // read as an abbreviation of every authorized id.
    expect(findForeignChartReferences('', CONFIG)).toEqual([])
    // …and the real check: the authorized set itself cannot be emptied into a
    // blanket allow by a falsy entry.
    const rules = buildEntitlementScanRules({ authorizedChartIds: ['', MINE] })
    const r = scanMortalityPhrasing(`Chart ${THEIRS} differs.`, {
      extraRules: rules,
      mortalityRulesEnabled: false,
    })
    expect(r.clean).toBe('')
  })

  it('a LONGER token that merely begins with the authorized id is NOT authorized', () => {
    const impostor = `${MINE.replace(/-/g, '')}ff`
    const found = findForeignChartReferences(`chart ${impostor} shows`, CONFIG)
    // 34 characters, so the no-cue run rule owns it (>= 32) rather than the
    // abbreviated-form rule (8–31). It is caught either way; the assertion pins
    // WHICH rule so the two bands cannot silently start overlapping again.
    expect(found).toHaveLength(1)
    expect(found[0].rule).toBe(ENTITLEMENT_RULE_FOREIGN_UUID)
    expect(found[0].token).toBe(impostor)
    // …and the same impostor shape inside the abbreviated band still reports as
    // the abbreviated rule, so the band split is proved in both directions.
    const shortImpostor = `${MINE.replace(/-/g, '').slice(0, 8)}ff`
    const shortFound = findForeignChartReferences(`chart ${shortImpostor} shows`, CONFIG)
    expect(shortFound.map((f) => f.rule)).toContain(ENTITLEMENT_RULE_FOREIGN_PREFIX)
  })

  it('a hex run of ANY length is judged — no length is unmatchable (P1-2)', () => {
    // Two holes were reproduced, in opposite directions: a >64-character run
    // near a cue matched nothing (`{8,64}` plus strict lookarounds is
    // unsatisfiable at every start offset inside a longer run), and a 33+
    // character run with NO cue matched nothing (`{32}` exactly). Both were the
    // same defect — a fixed-length quantifier pretending to judge a whole run.
    const hex = 'abcdef0123456789'
    const run = (n: number): string =>
      Array.from({ length: n }, (_, i) => hex[i % 16]).join('')

    for (const n of [30, 31, 32, 33, 34, 40, 64, 65, 80, 128]) {
      const withCue = findForeignChartReferences(`The chart is ${run(n)} here.`, CONFIG)
      expect(withCue.length, `cue, n=${n}`).toBeGreaterThan(0)
    }
    // Without a cue word the threshold is 32 BY DESIGN — below it a hex run is
    // not distinguishable from arbitrary hex — but above it there is no ceiling.
    for (const n of [32, 33, 34, 40, 64, 65, 80, 128]) {
      const noCue = findForeignChartReferences(`The reference is ${run(n)} here.`, CONFIG)
      expect(noCue.length, `no cue, n=${n}`).toBeGreaterThan(0)
      expect(noCue[0].token, `no cue token, n=${n}`).toBe(run(n))
    }
    // The exact form the re-verification used.
    const foreign32 = THEIRS.replace(/-/g, '')
    expect(
      findForeignChartReferences(`The reference key is ${foreign32}f.`, CONFIG),
    ).toHaveLength(1)
  })

  it('the decimal false-positive guard survives the widened bands', () => {
    // Widening the quantifier must not reopen the Julian-day/epoch/row-count
    // false positives the hex-letter gate closed.
    for (const prose of [
      'The chart uses Julian day 24457355 for the epoch.',
      'This chart was built at 20240115 in the pipeline.',
      'Chart totals: 100000000 divisional rows were written.',
      // 31 digits — the top of the abbreviated band, still gated by the
      // hex-letter requirement.
      'The chart counter reached 1234567890123456789012345678901 rows.',
    ]) {
      expect(prewire(prose).clean, prose).toBe(prose)
    }
    // At 32+ the no-cue run rule takes over and does NOT require a hex letter —
    // the same choice the exactly-32 rule always made, carried up to the
    // unbounded band. Asserted rather than left implicit: a 32-digit run is an
    // identifier shape, not a Julian day, a year or a row count, and treating it
    // as foreign is the fail-closed direction.
    expect(prewire('The run id is 12345678901234567890123456789012 here.').clean).toBe('')
  })
})

describe('adversarial — the ABBREVIATED id form the project itself uses in prose', () => {
  it("catches `chart 1c826d5a` — the shortened form, which a full-UUID rule would miss", () => {
    const r = prewire(`The comparison chart 1c826d5a shows a stronger tenth lord.`)
    expect(r.clean).toBe('')
    expect(r.extra_hits.map((h) => h.rule)).toContain(ENTITLEMENT_RULE_FOREIGN_PREFIX)
  })

  it('catches the REVERSE word order (`1c826d5a, the other chart`)', () => {
    const r = prewire(`Reading 1c826d5a, the other chart, gives a different Saturn story.`)
    expect(r.clean).toBe('')
  })

  it("catches `chart_id: <hex>` and `chartId <hex>` spellings", () => {
    for (const form of ['chart_id: 1c826d5a9f3b', 'chartId 1c826d5a9f3b', 'chart-id 1c826d5a9f3b']) {
      expect(prewire(`Source ${form} was consulted.`).clean, form).toBe('')
    }
  })

  it('catches an abbreviated id separated from its cue by a relative clause', () => {
    // One clause was enough to push the id past the original 24-char window.
    const r = prewire(
      'The other chart, which belongs to a different native entirely, is 1c826d5a today.',
    )
    expect(r.clean).toBe('')
  })

  it("does NOT fire on an ABBREVIATION of the caller's own id", () => {
    const own = `This is chart 482012f1, the one under reading.`
    expect(prewire(own).clean).toBe(own)
  })

  it('a full foreign UUID next to the word "chart" is reported ONCE, not twice', () => {
    // The UUID's own leading hex would otherwise also trip the prefix rule and
    // one leak would be counted as two.
    const found = findForeignChartReferences(`chart ${THEIRS} differs`, CONFIG)
    expect(found).toHaveLength(1)
    expect(found[0].rule).toBe(ENTITLEMENT_RULE_FOREIGN_UUID)
  })
})

describe('false positives — a real reading must survive intact', () => {
  const READING = [
    'Saturn in the tenth house from the Moon indicates a long consolidation.',
    'The Vimshottari sequence places Saturn Mahadasha from 2014 to 2033.',
    'Jupiter aspects the seventh, which the classics read as protective.',
    'Ashtakavarga gives the tenth house 31 bindus, above the 28 threshold.',
    'The D10 chart shows the tenth lord in its own sign.',
    'Effaced karma of the sixth house is a facade the ninth lord does not support.',
  ].join(' ')

  it('leaves ordinary Jyotish prose — dates, bindu counts, varga codes — untouched', () => {
    const r = prewire(READING)
    expect(r.clean).toBe(READING)
    expect(r.extra_hits).toHaveLength(0)
  })

  it('does not fire on hex-looking English words without a chart cue', () => {
    const prose = 'The effaced, defaced facade of that decade beaded together.'
    expect(prewire(prose).clean).toBe(prose)
  })

  it('does not fire on a four-digit year adjacent to the word chart', () => {
    const prose = 'The chart was rebuilt in 2024 after the ayanamsha correction.'
    expect(prewire(prose).clean).toBe(prose)
  })
})

describe('the fold into the pre-wire pass — composition, not duplication', () => {
  it('with mortality rules ON, BOTH classes redact in ONE pass', () => {
    const text =
      `Jupiter is strong. ` +
      `The native will meet death around 2047. ` +
      `The comparison chart ${THEIRS} differs. ` +
      `Mars is exalted.`
    const r = scanMortalityPhrasing(text, { extraRules: RULES, mortalityRulesEnabled: true })

    expect(r.clean).not.toContain('2047')
    expect(r.clean).not.toContain(THEIRS)
    expect(r.clean).toContain('Jupiter is strong.')
    expect(r.clean).toContain('Mars is exalted.')
    expect(r.hits.length).toBeGreaterThan(0)
    expect(r.extra_hits.length).toBeGreaterThan(0)
  })

  it('arming the entitlement class does NOT silently arm the mortality class', () => {
    // The two are gated by different feature flags. This is the line that keeps
    // flipping one from changing the other's behaviour.
    const mortal = 'The native will meet death around 2047.'
    const r = prewire(mortal)
    expect(r.clean).toBe(mortal)
    expect(r.hits).toHaveLength(0)
  })

  it('arming the mortality class alone leaves entitlement behaviour exactly as it was', () => {
    const leak = `The comparison chart ${THEIRS} differs.`
    const r = scanMortalityPhrasing(leak, { mortalityRulesEnabled: true })
    expect(r.clean).toBe(leak)
    expect(r.extra_hits).toHaveLength(0)
  })

  it('a sentence caught by BOTH is redacted once and reported as not-the-cause', () => {
    const both = `The native's death in 2047 is shown on chart ${THEIRS}.`
    const r = scanMortalityPhrasing(both, { extraRules: RULES, mortalityRulesEnabled: true })
    expect(r.clean).toBe('')
    expect(r.hits).toHaveLength(1)
    expect(r.extra_hits.every((h) => h.caused_redaction === false)).toBe(true)
  })

  it('FAILS CLOSED when an extra rule throws — the span is withheld, not passed', () => {
    const exploding = [{ rule: 'boom', test: (): boolean => { throw new Error('detector broke') } }]
    const r = scanMortalityPhrasing('A perfectly ordinary sentence.', {
      extraRules: exploding,
      mortalityRulesEnabled: false,
    })
    expect(r.scan_failed).toBe(true)
    expect(r.clean).toBe('')
    // §N.8: "the scan could not run" must not be reported as "nothing was found".
    expect(r.extra_hits).toHaveLength(0)
  })

  it('reports the span by HASH and LENGTH only — never the sentence itself', () => {
    const r = prewire(`The other chart is ${THEIRS}.`)
    const hit = r.extra_hits[0]
    expect(hit.redacted_span_hash).toMatch(/^[0-9a-f]{64}$/)
    expect(hit.redacted_span_hash).not.toContain(THEIRS)
    expect(hit.redacted_length).toBeGreaterThan(0)
    expect(JSON.stringify(hit)).not.toContain(THEIRS)
  })
})

describe('adversarial — the STREAMING path, where a leak arrives in pieces', () => {
  const streamRules = () =>
    new StreamingMortalityScanner(undefined, { extraRules: RULES, mortalityRulesEnabled: false })

  it('a UUID split across two deltas is still caught (the seam is the classic bypass)', () => {
    const s = streamRules()
    let out = ''
    // Split mid-UUID, which is exactly where a naive per-delta scan fails.
    out += s.push(`Saturn is steady. The other chart is ${THEIRS.slice(0, 12)}`)
    out += s.push(`${THEIRS.slice(12)}, which differs. Mars is exalted.`)
    out += s.flush()

    expect(out).not.toContain(THEIRS)
    expect(out).not.toContain(THEIRS.slice(12))
    expect(out).toContain('Saturn is steady.')
    expect(out).toContain('Mars is exalted.')
    expect(s.extraHits.length).toBeGreaterThan(0)
  })

  it('one character at a time still never emits the id', () => {
    const s = streamRules()
    const text = `Jupiter protects. The comparison chart is ${THEIRS}. Venus is neutral.`
    let out = ''
    for (const ch of text) out += s.push(ch)
    out += s.flush()

    expect(out).not.toContain(THEIRS)
    expect(out).toContain('Jupiter protects.')
    expect(out).toContain('Venus is neutral.')
  })

  it('a leak in the FINAL unterminated span is caught by flush(), not leaked', () => {
    const s = streamRules()
    let out = s.push('Saturn is steady. ')
    out += s.push(`and the other chart ${THEIRS} shows otherwise`)
    out += s.flush()
    expect(out).not.toContain(THEIRS)
  })

  it('FORCED RELEASE: an id straddling the no-terminator cut does not leak', () => {
    // The hard case a review reproduced. With no `.`/`!`/`?`/`\n` anywhere, the
    // scanner passes MAX_HOLDBACK_CHARS and force-releases at a fixed character
    // offset — mid-token by construction. The carried context and the new span
    // used to be scanned as separate sentence arrays, so the two halves could
    // never be rejoined and the COMPLETE id reached the reader.
    for (const offset of [-8, 0, 8]) {
      const s = new StreamingMortalityScanner(undefined, {
        extraRules: RULES,
        mortalityRulesEnabled: false,
      })
      const cut = 1200 + offset
      const filler = 'saturn steady jupiter strong venus neutral mars exalted '
      const head = filler.repeat(60).slice(0, cut)
      const text = `${head}${THEIRS} and more prose without any terminator at all`

      let out = ''
      for (let i = 0; i < text.length; i += 64) out += s.push(text.slice(i, i + 64))
      out += s.flush()

      expect(out, `offset ${offset}`).not.toContain(THEIRS)
      expect(s.extraHits.length, `offset ${offset}`).toBeGreaterThan(0)
    }
  })

  it('does not double-emit clean prose while the entitlement rules are armed', () => {
    const s = streamRules()
    const text = 'One. Two. Three. Four.'
    let out = ''
    for (const ch of text) out += s.push(ch)
    out += s.flush()
    expect(out).toBe(text)
  })
})
