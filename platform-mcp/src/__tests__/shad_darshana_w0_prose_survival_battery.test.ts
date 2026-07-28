/**
 * shad_darshana_w0_prose_survival_battery.test.ts — ṢAḌ-DARŚANA W0.6 CI skeleton, item 2
 * (SHAD_DARSHANA_BRIEF_v2_0.md §0.6.2 / §3 W0.6: "minimum-budget prose-survival battery").
 *
 * Asserts served prose survives response-budget trimming without going empty, using the
 * `hardFloor` mechanism (`response_budget.ts`) exactly as CLAUDE.md §N.6 describes it and
 * exactly as `kala_envelope.ts`'s own `kalaEvidenceTrimmableSection` helper wires it up for
 * the eight kala_* views. Precedent: `verbosity_hard_floor.test.ts` (W3 C-4 guard) proves
 * this mechanism for `judgment_query`'s `bearing_yogas`/`bearing_afflictions`; this file is
 * the SAME class of regression guard for the ṢAḌ-DARŚANA `ArgumentReading` shape.
 *
 * THE REGRESSION THIS GUARDS AGAINST (CLAUDE.md §N.6 point 2): a generic budget trim will,
 * left alone, zero out a section the instant it becomes genuinely populated — because a
 * newly-non-empty confirmed-finding section is, simply by no longer being empty, the
 * biggest remaining candidate for the hard-cap fallback pass. For a kala_* envelope, the
 * densest, most-actionable layer is `reading.evidence` (the cited drivers behind the
 * thesis/verdict) — `kalaEvidenceTrimmableSection` declares it `hardFloor: true, minKeep: 1`
 * specifically so it survives even the worst-case trim. This battery proves that survival
 * holds not just at the STRUCTURED-DATA level (the array itself) but at the SERVED-PROSE
 * level (`argument_composer.ts`'s `composeArgument().full_text`) — the actual bytes an LLM
 * caller reads never go empty, even under an extremely tight budget.
 *
 * This is a UNIT-level battery (no live MCP server needed) — it exercises the shared
 * `kala_envelope.ts` / `argument_composer.ts` / `response_budget.ts` libraries directly,
 * the same libraries every one of the eight kala_* tool facades is contracted to consume
 * ("ONE implementation, eight consumers" — kala_envelope.ts's own header). It is therefore
 * NOT blocked on the sibling facade lanes merging (unlike the live gate scripts under
 * `platform/scripts/census/shad_darshana_gates/`) and should be green from the moment this
 * PR lands.
 */
import { describe, it, expect } from 'vitest'
import { applyResponseBudget, type TrimmableSection } from '../lib/response_budget.js'
import { composeArgument } from '../lib/argument_composer.js'
import {
  kalaEvidenceTrimmableSection,
  type ArgumentReading,
  type ArgumentEvidence,
} from '../lib/kala_envelope.js'

/** A KalaEnvelope-shaped content object carrying a genuinely large evidence array (the
 *  exact "just became populated" condition the D-1.5a-class regression targets) plus a
 *  large amount of non-trimmable padding, so a tight budget is guaranteed to force real
 *  trimming rather than a no-op (`applyResponseBudget` returns unchanged when already
 *  under budget — this fixture is deliberately oversized to rule that out). */
function makeKalaEnvelopeShapedContent(evidenceCount: number): {
  padding: string
  reading: ArgumentReading
} {
  const evidence: ArgumentEvidence[] = Array.from({ length: evidenceCount }, (_, i) => ({
    claim: `Driver ${i}: Jupiter's dignity in the 10th supports authority during this period, corroborated by the daśā-lord's own placement (evidence row ${i} of ${evidenceCount}, padded to be realistically sized: ${'x'.repeat(80)})`,
    fact_ids: [`fact_${i}_a`, `fact_${i}_b`],
    strength: i % 3 === 0 ? 'strong' : i % 3 === 1 ? 'moderate' : 'weak',
  }))
  return {
    // Non-trimmable base content — pushes the response over budget on its own, matching
    // the real-world condition (chart_header, orientation prose, etc.) that makes the
    // hard-cap fallback fire in production (verbosity_hard_floor.test.ts uses the same
    // technique for the judgment_query analog).
    padding: 'x'.repeat(20_000),
    reading: {
      thesis: 'Saturn returning to its own sign this year anchors a multi-year authority-building arc for this native.',
      evidence,
      dissent: [
        { claim: 'The KP sub-lord clock reads this window as neutral, not activating.', fact_ids: ['fact_kp_1'], source: 'KP sub-lord clock' },
      ],
      verdict: { statement: 'This is a structurally favorable window for authority-linked undertakings.', tier: 'structural_prior' },
      falsifier: { statement: 'No visible career movement by the close of the daśā-sandhi', resolves_by: '2027-06-30' },
    },
  }
}

function trimmableSections<T extends { reading: { evidence: ArgumentEvidence[] } }>(): TrimmableSection<T>[] {
  return [kalaEvidenceTrimmableSection<T>({ instrument: 'kala_explain_get', hint: 'full evidence set' })]
}

describe('ṢAḌ-DARŚANA W0.6 item 2 — minimum-budget prose-survival battery', () => {
  it('sanity: the fixture with 50 evidence rows is genuinely over a 4KB budget (rules out a no-op trim)', () => {
    const content = makeKalaEnvelopeShapedContent(50)
    const before = Buffer.byteLength(JSON.stringify(content), 'utf8')
    expect(before).toBeGreaterThan(4 * 1024)
  })

  it('hardFloor holds at a GENEROUS budget: evidence array survives at/above minKeep(1)', () => {
    const content = makeKalaEnvelopeShapedContent(50)
    applyResponseBudget(content, 40, trimmableSections())
    expect(content.reading.evidence.length).toBeGreaterThanOrEqual(1)
  })

  it('hardFloor holds at an EXTREME budget (4KB — smaller than the padding alone): evidence array still survives at minKeep(1), never zero', () => {
    const content = makeKalaEnvelopeShapedContent(50)
    const result = applyResponseBudget(content, 4, trimmableSections())
    expect(content.reading.evidence.length).toBeGreaterThanOrEqual(1)
    // Honesty, not silence: an extreme budget this tight against 20KB of non-trimmable
    // padding legitimately cannot be met — that must be reported, never masked as a clean
    // trim (same discipline verbosity_hard_floor.test.ts's C-4 guard asserts). Compute the
    // over-budget condition directly (BudgetResult no longer surfaces a `still_over_budget`
    // field — GT-45 removed it as dead output — so this test derives the same fact from
    // approx_bytes_after, which the result DOES carry).
    const stillOverBudget = result.approx_bytes_after > 4 * 1024
    if (stillOverBudget) {
      expect(result.trim_report).not.toBeNull()
    }
  })

  it('THE PROSE-SURVIVAL ASSERTION: composeArgument(reading) on the POST-TRIM reading never goes empty, even under the extreme budget', () => {
    const content = makeKalaEnvelopeShapedContent(50)
    applyResponseBudget(content, 4, trimmableSections())

    const composed = composeArgument(content.reading)

    // The served text is non-empty...
    expect(composed.full_text.length).toBeGreaterThan(0)
    // ...and specifically carries the thesis, at least one evidence sentence (the hardFloor
    // guarantee made visible at the PROSE layer, not just the array-length layer), and the
    // verdict — the three clauses that must never silently vanish under trim pressure.
    expect(composed.thesis_sentence.length).toBeGreaterThan(0)
    expect(composed.evidence_sentences.length).toBeGreaterThanOrEqual(1)
    expect(composed.verdict_sentence.length).toBeGreaterThan(0)
    expect(composed.full_text).toContain(composed.thesis_sentence)
    expect(composed.full_text).toContain(composed.verdict_sentence)
  })

  it('a SMALL evidence array (already at minKeep) survives untouched even under the extreme budget — hardFloor never trims BELOW what is already minimal', () => {
    const content = makeKalaEnvelopeShapedContent(1)
    applyResponseBudget(content, 4, trimmableSections())
    expect(content.reading.evidence.length).toBe(1)
    const composed = composeArgument(content.reading)
    expect(composed.evidence_sentences.length).toBe(1)
    expect(composed.full_text.length).toBeGreaterThan(0)
  })

  it('regression guard: a non-hardFloor-declared trimmable section (if a facade adds one) is free to hit zero while reading.evidence (hardFloor) does not — proves the floor is doing real, differential work, not just "nothing got trimmed"', () => {
    type Content = { padding: string; reading: ArgumentReading; disposable_ids: string[] }
    const content: Content = {
      ...makeKalaEnvelopeShapedContent(3),
      disposable_ids: Array.from({ length: 500 }, (_, i) => `disposable_${i}`),
    }
    const sections: TrimmableSection<Content>[] = [
      kalaEvidenceTrimmableSection<Content>({ instrument: 'kala_explain_get', hint: 'full evidence set' }),
      {
        path: 'disposable_ids',
        label: 'disposable ids',
        minKeep: 0,
        getArray: (c) => c.disposable_ids,
        setArray: (c, kept) => { c.disposable_ids = kept as string[] },
        recover: { instrument: 'kala_explain_get', hint: 'full id list' },
        // no hardFloor — this is the disposable, catalog-shaped section §N.6 says should
        // absorb the cut first.
      },
    ]
    applyResponseBudget(content, 4, sections)
    expect(content.disposable_ids.length).toBeLessThan(500) // real cut happened
    expect(content.reading.evidence.length).toBeGreaterThanOrEqual(1) // hardFloor still held
  })
})
