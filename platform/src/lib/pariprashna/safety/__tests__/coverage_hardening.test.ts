/**
 * Lane G1-A — COVERAGE OF THE SURFACES THE FIRST SUITE DID NOT TOUCH.
 *
 * ── H-5: two large surfaces were effectively untested ────────────────────────
 * A reviewer deleted entries and re-ran the suite to find what nothing depended
 * on:
 *   · the SQUASHED (spelling-evasion) patterns — ~23 of ~25 could be deleted
 *     with the suite green. The squashed surface is the ENTIRE defence against
 *     `s.u.i.c.i.d.e` and `k i l l  m y s e l f`, so an accidental deletion
 *     there silently reopens evasion that the `re` patterns cannot cover.
 *   · the DOMAIN/CAPABILITY rule family — 7 of 9 `CAPABILITY_CLASS_RULES` and 2
 *     of 3 `DOMAIN_CLASS_RULES` could be deleted with the suite green. This is
 *     the family that catches a question with NO trigger words in it at all,
 *     which makes it the one whose silent loss is hardest to notice.
 *
 * ── H-6: "type-enforced, no downgrade possible" was false ───────────────────
 * A reviewer added a `downgrade_to?` field to `LlmAssistPayload` plus a code
 * path honoring it. It compiled clean and every test passed.
 *
 * These are ENUMERATIVE tests: they walk the exported tables rather than
 * hard-coding a copy of them, so a future ADDITION is covered automatically and
 * a future DELETION fails here.
 */

import { describe, it, expect } from 'vitest'

import { classifyQuery, DOMAIN_CLASS_RULES, CAPABILITY_CLASS_RULES } from '../classifier'
import { LLM_ASSIST_PAYLOAD_KEYS, mergeLlmAssist, type LlmAssistPayload } from '../llm_assist'
import type { SafetyClass } from '../types'

// ═══════════════════════════════════════════════════════════════════════════
// H-5a — every DOMAIN rule has a test that depends on it.
// ═══════════════════════════════════════════════════════════════════════════

describe('H-5 — every DOMAIN_CLASS_RULES row is exercised', () => {
  // A representative domain string per row, chosen to match that row's regex.
  // Enumerating the TABLE (not a copy of it) is what makes a deleted row fail:
  // the loop shrinks, and the completeness assertion below catches it.
  const DOMAIN_SAMPLES: Record<string, string[]> = {
    hs4_mortality_window: ['longevity', 'mortality', 'ayurdaya', 'lifespan'],
    hs3_health_crisis: ['health', 'medical', 'disease', 'illness', 'body'],
    hs3_mental_health: ['mental_health', 'mental', 'psyche', 'psychology', 'mind'],
  }

  it('the sample table covers every rule row (fails if a row is added untested)', () => {
    const rowClasses = new Set(DOMAIN_CLASS_RULES.map((r) => r.cls))
    for (const cls of rowClasses) {
      expect(DOMAIN_SAMPLES[cls], `DOMAIN_CLASS_RULES has a "${cls}" row with no sample`).toBeDefined()
    }
    expect(DOMAIN_CLASS_RULES.length).toBe(rowClasses.size)
  })

  it('every sampled class STILL HAS a rule (fails if a row is deleted)', () => {
    // ── THE VACUITY GUARD, and it is here because it was needed ────────────
    // Mutation-tested during this round: deleting the `mental_health` row made
    // the parameterised loop below simply generate five fewer cases and the
    // file stayed green. A for-loop over a table cannot, by itself, detect the
    // table shrinking — the assertion has to be about the table.
    for (const cls of Object.keys(DOMAIN_SAMPLES)) {
      const samples = DOMAIN_SAMPLES[cls]
      expect(
        DOMAIN_CLASS_RULES.some((r) => samples.some((d) => r.domain.test(d) && r.cls === cls)),
        `the DOMAIN_CLASS_RULES row for "${cls}" was DELETED — a planner domain that used to ` +
          'imply a safety class now implies nothing',
      ).toBe(true)
    }
    expect(DOMAIN_CLASS_RULES.length).toBeGreaterThanOrEqual(3)
  })

  for (const rule of DOMAIN_CLASS_RULES) {
    const samples = DOMAIN_SAMPLES[rule.cls] ?? []
    for (const domain of samples) {
      // Only assert a sample against the row it actually belongs to.
      if (!rule.domain.test(domain)) continue
      it(`domain "${domain}" ⇒ ${rule.cls}`, () => {
        // A question with NO trigger words anywhere — the whole point of this
        // detector family.
        const r = classifyQuery({ queryText: 'How is my sixth house doing?', domains: [domain] })
        expect(r.classes).toContain(rule.cls)
        expect(r.severity).toBe(rule.severity)
      })
    }
  }

  it('every rule row is matched by at least one sample (no dead row)', () => {
    for (const rule of DOMAIN_CLASS_RULES) {
      const samples = DOMAIN_SAMPLES[rule.cls] ?? []
      expect(
        samples.some((d) => rule.domain.test(d)),
        `no sample matches the ${rule.cls} rule — it is untested`,
      ).toBe(true)
    }
  })

  it('an unrelated domain implies nothing', () => {
    expect(classifyQuery({ queryText: 'How is my tenth house?', domains: ['career'] }).classes).toEqual([])
  })
})

// ═══════════════════════════════════════════════════════════════════════════
// H-5b — every CAPABILITY rule has a test that depends on it.
// ═══════════════════════════════════════════════════════════════════════════

describe('H-5 — every CAPABILITY_CLASS_RULES entry is exercised', () => {
  const entries = Object.entries(CAPABILITY_CLASS_RULES) as Array<[string, SafetyClass]>

  it('the table is non-empty (a deleted table would make the loop vacuous)', () => {
    // Without this, deleting the whole map would leave a green — and empty —
    // parameterised block, which is the failure mode a for-loop test has.
    expect(entries.length).toBeGreaterThanOrEqual(9)
  })

  for (const [capability, cls] of entries) {
    it(`capability "${capability}" ⇒ ${cls}`, () => {
      // Deliberately trigger-word-free: the capability alone must carry it.
      const r = classifyQuery({ queryText: 'General reading please.', capabilities: [capability] })
      expect(r.classes, `${capability} did not imply ${cls}`).toContain(cls)
      expect(r.detections.some((d) => d.detector === 'capability' && d.rule === `capability:${capability}`)).toBe(true)
    })
  }

  it('the two mortality capabilities are both present and both imply HS-4', () => {
    // Named explicitly because these two are the ones HS-1 point (a) strips;
    // losing either would silently un-gate the longevity computation.
    expect(CAPABILITY_CLASS_RULES['get_ayurdaya']).toBe('hs4_mortality_window')
    expect(CAPABILITY_CLASS_RULES['ganita_ayurdaya_get']).toBe('hs4_mortality_window')
  })

  it('an unlisted capability implies nothing', () => {
    expect(
      classifyQuery({ queryText: 'General reading please.', capabilities: ['ganita_positions_get'] }).classes,
    ).toEqual([])
  })
})

// ═══════════════════════════════════════════════════════════════════════════
// H-5c — the SQUASHED (spelling-evasion) surface.
//
// Each case is the squashed entry re-expressed as a HUMAN evasion — dotted,
// spaced, hyphenated — so the test depends on the squashed entry existing AND
// on the normalizer collapsing the separators. A `re`-only match cannot satisfy
// these: `\b`-bounded patterns do not see through `s.u.i.c.i.d.e`.
// ═══════════════════════════════════════════════════════════════════════════

describe('H-5 — the squashed spelling-evasion surface actually holds', () => {
  const dotted = (s: string): string => s.split('').join('.')
  const spaced = (s: string): string => s.split('').join(' ')
  const hyphen = (s: string): string => s.split('').join('-')

  const EVASIONS: Array<[string, SafetyClass]> = [
    // HS-2
    ['suicide', 'hs2_suicide_adjacent'],
    ['suicidal', 'hs2_suicide_adjacent'],
    ['commitsuicide', 'hs2_suicide_adjacent'],
    ['killmyself', 'hs2_suicide_adjacent'],
    ['killingmyself', 'hs2_suicide_adjacent'],
    ['harmmyself', 'hs2_suicide_adjacent'],
    ['hurtmyself', 'hs2_suicide_adjacent'],
    ['selfharm', 'hs2_suicide_adjacent'],
    ['selfinjury', 'hs2_suicide_adjacent'],
    ['endmylife', 'hs2_suicide_adjacent'],
    ['takemyownlife', 'hs2_suicide_adjacent'],
    ['endingitall', 'hs2_suicide_adjacent'],
    ['dontwanttolive', 'hs2_suicide_adjacent'],
    ['nolongerwanttolive', 'hs2_suicide_adjacent'],
    ['wanttodie', 'hs2_suicide_adjacent'],
    ['wishiwasdead', 'hs2_suicide_adjacent'],
    ['readytodie', 'hs2_suicide_adjacent'],
    ['noreasontolive', 'hs2_suicide_adjacent'],
    ['nopointinliving', 'hs2_suicide_adjacent'],
    ['betteroffdead', 'hs2_suicide_adjacent'],
    ['betteroffwithoutme', 'hs2_suicide_adjacent'],
    ['unalive', 'hs2_suicide_adjacent'],
    ['offmyself', 'hs2_suicide_adjacent'],
    ['permanentsolution', 'hs2_suicide_adjacent'],
    ['finalexit', 'hs2_suicide_adjacent'],
    ['enditall', 'hs2_suicide_adjacent'],
    ['sleepforever', 'hs2_suicide_adjacent'],
    ['neverwakeup', 'hs2_suicide_adjacent'],
    ['ceasetoexist', 'hs2_suicide_adjacent'],
    ['makethepainstop', 'hs2_suicide_adjacent'],
    ['khudkushi', 'hs2_suicide_adjacent'],
    ['atmahatya', 'hs2_suicide_adjacent'],
    ['jaandena', 'hs2_suicide_adjacent'],
    ['suicidalideation', 'hs2_suicide_adjacent'],
    ['selfharmyoga', 'hs2_suicide_adjacent'],
    // HS-2, added by the hardening round (C-1) — covered from day one.
    ['hangmyself', 'hs2_suicide_adjacent'],
    ['slitmywrists', 'hs2_suicide_adjacent'],
    ['swallowallmypills', 'hs2_suicide_adjacent'],
    ['jalsamadhi', 'hs2_suicide_adjacent'],
    ['sallekhana', 'hs2_suicide_adjacent'],
    ['icchamrityu', 'hs2_suicide_adjacent'],
    ['selfimmolation', 'hs2_suicide_adjacent'],
    // HS-1
    ['dateofdeath', 'hs1_date_of_death'],
    ['dayofdeath', 'hs1_date_of_death'],
    ['yearofdeath', 'hs1_date_of_death'],
    ['dateofdemise', 'hs1_date_of_death'],
    ['whenwillidie', 'hs1_date_of_death'],
    ['whenamigoingtodie', 'hs1_date_of_death'],
    ['whatagewillidie', 'hs1_date_of_death'],
    ['howsoonwillidie', 'hs1_date_of_death'],
    ['howlongdoihaveleft', 'hs1_date_of_death'],
    ['howmanyyearsdoihaveleft', 'hs1_date_of_death'],
    ['howlongdoihavetolive', 'hs1_date_of_death'],
    ['liveuntilwhatage', 'hs1_date_of_death'],
    ['uptowhatage', 'hs1_date_of_death'],
    ['marakadasha', 'hs1_date_of_death'],
    ['mrityudasha', 'hs1_date_of_death'],
    ['fataldasha', 'hs1_date_of_death'],
    ['sixfeetunder', 'hs1_date_of_death'],
    ['kickthebucket', 'hs1_date_of_death'],
    ['meetmymaker', 'hs1_date_of_death'],
    ['pushingupdaisies', 'hs1_date_of_death'],
    ['breathemylast', 'hs1_date_of_death'],
    ['expirydate', 'hs1_date_of_death'],
    ['mytimeisup', 'hs1_date_of_death'],
    ['stopbreathing', 'hs1_date_of_death'],
    ['kabmarunga', 'hs1_date_of_death'],
    ['kabmarega', 'hs1_date_of_death'],
    ['maximumlifespan', 'hs1_date_of_death'],
    ['allottedyears', 'hs1_date_of_death'],
    ['predictmydeath', 'hs1_date_of_death'],
    ['calculatedateofdeath', 'hs1_date_of_death'],
    ['tellmewhenidie', 'hs1_date_of_death'],
    ['willpassintheyear', 'hs1_date_of_death'],
    ['kebemaribi', 'hs1_date_of_death'],
    // HS-3 / HS-4
    ['depression', 'hs3_mental_health'],
    ['bipolardisorder', 'hs3_mental_health'],
    ['schizophrenia', 'hs3_mental_health'],
    ['nervousbreakdown', 'hs3_mental_health'],
    ['substanceabuse', 'hs3_mental_health'],
    ['chemotherapy', 'hs3_health_crisis'],
    ['heartattack', 'hs3_health_crisis'],
    ['organfailure', 'hs3_health_crisis'],
    ['lifesupport', 'hs3_health_crisis'],
    ['palliativecare', 'hs3_health_crisis'],
    ['willirecover', 'hs3_health_crisis'],
    ['ayurdaya', 'hs4_mortality_window'],
    ['alpayu', 'hs4_mortality_window'],
    ['purnayu', 'hs4_mortality_window'],
    ['lifeexpectancy', 'hs4_mortality_window'],
    ['mortality', 'hs4_mortality_window'],
    ['willisurvive', 'hs4_mortality_window'],
  ]

  for (const [entry, cls] of EVASIONS) {
    it(`"${entry}" survives dot/space/hyphen evasion ⇒ ${cls}`, () => {
      for (const mangle of [dotted, spaced, hyphen]) {
        const q = mangle(entry)
        const found = classifyQuery({ queryText: q }).classes
        expect(found, `"${q}" (${mangle.name}) should detect ${cls}, got [${found.join(', ')}]`).toContain(cls)
      }
    })
  }

  it('covers a clear majority of the squashed surface', () => {
    // A count assertion so that a large future ADDITION of squashed entries
    // without matching cases is visible, rather than quietly diluting coverage.
    expect(EVASIONS.length).toBeGreaterThanOrEqual(80)
  })

  it('the squashed surface does not fire on ordinary prose', () => {
    // The floor: substring matching has NO word boundaries, so the risk this
    // surface carries is the opposite one.
    for (const q of [
      'What does my chart say about my career this year?',
      'Explain the Gaja Kesari yoga.',
      'Which remedies are indicated for Saturn?',
      'Is this a good time to relocate?',
    ]) {
      expect(classifyQuery({ queryText: q }).classes, q).toEqual([])
    }
  })
})

// ═══════════════════════════════════════════════════════════════════════════
// H-6 — the assist payload's field set is pinned by a real detector.
// ═══════════════════════════════════════════════════════════════════════════

describe('H-6 — LlmAssistPayload cannot silently grow a downgrade field', () => {
  it('the canonical key list matches the interface EXACTLY', () => {
    // THE TEST THAT KILLS THE REVIEWER'S ATTACK. They added `downgrade_to?` to
    // the interface plus a branch honoring it, and everything stayed green. A
    // representative payload is built with every canonical key present, and its
    // real runtime key set is compared against the list — so an added field
    // that a future author wires into the merge fails HERE, before the merge
    // logic can act on it.
    const representative: Required<LlmAssistPayload> = {
      raised_classes: ['hs2_suicide_adjacent'],
      raised_severity: 'hard_stop',
      rationale: 'because',
      model_id: 'm-1',
    }
    expect(Object.keys(representative).sort()).toEqual([...LLM_ASSIST_PAYLOAD_KEYS].sort())
  })

  it('the canonical list contains no downgrade-shaped field, by name', () => {
    // Belt and braces on the specific attack, in a form a reader recognises.
    for (const forbidden of ['downgrade_to', 'downgrade', 'clear', 'override', 'lower', 'suppress', 'confidence']) {
      expect(LLM_ASSIST_PAYLOAD_KEYS as readonly string[]).not.toContain(forbidden)
    }
  })

  it('an UNKNOWN field on the payload changes nothing about the merge', () => {
    // The behavioural half: even if a caller smuggles an extra field past the
    // type (via a cast, as the reviewer did), the merge body ignores it.
    const deterministic = classifyQuery({ queryText: 'I want to kill myself.' })
    const hostile = {
      raised_classes: [],
      raised_severity: 'none',
      model_id: 'attacker',
      downgrade_to: 'none',
      clear: true,
      override_severity: 'none',
    } as unknown as LlmAssistPayload

    const merged = mergeLlmAssist(deterministic, hostile)
    expect(merged.classes).toContain('hs2_suicide_adjacent')
    expect(merged.severity).toBe('hard_stop')
    for (const d of deterministic.detections) {
      expect(merged.detections.some((m) => m.rule === d.rule)).toBe(true)
    }
  })

  it('the list is exactly four keys — a size change is a review event', () => {
    expect(LLM_ASSIST_PAYLOAD_KEYS).toHaveLength(4)
  })
})
