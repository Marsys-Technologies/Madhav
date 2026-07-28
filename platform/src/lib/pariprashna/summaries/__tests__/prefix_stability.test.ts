/**
 * PB-2 (SMṚTI) lane M-3 — prefix-stable splice.
 *
 * The brief's requirement, verbatim: "write a test asserting this: build the
 * context-assembly output twice (once for turn N, once for N+1 with no new
 * summary), hash the prefix, assert equality when no new threshold-crossing
 * occurs."
 */
import { describe, it, expect } from 'vitest'
import { assembleSynthesisPrefix, buildDurableSummaryBlock, hashPrefix, SUMMARY_SLOT_LABEL } from '../assemble'

const CHART_HEADER_BLOCK = 'Chart header: Aries lagna, Sun in Capricorn.'
const SYNTHESIS_GUIDANCE = 'Focus on career timing this reading.'

describe('assembleSynthesisPrefix — fixed structural slot', () => {
  it('the summary slot occupies the SAME position whether summaryText is present or null', () => {
    const withSummary = assembleSynthesisPrefix({
      precedingBlock: CHART_HEADER_BLOCK,
      summaryText: 'Earlier turns covered X and Y.',
    })
    const withoutSummary = assembleSynthesisPrefix({
      precedingBlock: CHART_HEADER_BLOCK,
      summaryText: null,
    })
    // Both carry the SAME label at the SAME structural position — only the
    // body after it differs.
    expect(withSummary).toContain(`${CHART_HEADER_BLOCK}\n\n---\n\n${SUMMARY_SLOT_LABEL}`)
    expect(withoutSummary).toContain(`${CHART_HEADER_BLOCK}\n\n---\n\n${SUMMARY_SLOT_LABEL}`)
  })

  it('buildDurableSummaryBlock never omits the label, even with no summary yet', () => {
    expect(buildDurableSummaryBlock(null)).toBe(`${SUMMARY_SLOT_LABEL}\n(none yet)`)
    expect(buildDurableSummaryBlock('')).toBe(`${SUMMARY_SLOT_LABEL}\n(none yet)`)
    expect(buildDurableSummaryBlock('real summary')).toBe(`${SUMMARY_SLOT_LABEL}\nreal summary`)
  })
})

describe('prefix-hash stability — turn N vs. turn N+1', () => {
  it('IDENTICAL prefix hash across two assembly calls when no new threshold-crossing occurred ' +
    '(summaryText unchanged between turn N and turn N+1)', () => {
    const buildForTurn = () =>
      assembleSynthesisPrefix({
        precedingBlock: CHART_HEADER_BLOCK,
        summaryText: 'Summary v1 — covers turns 0-5.',
        followingBlock: SYNTHESIS_GUIDANCE,
      })

    // Turn N's assembly.
    const turnNPrefix = buildForTurn()
    // Turn N+1's assembly — no new summarization threshold crossed, so the
    // caller passes the SAME summaryText again (this is exactly what
    // service.ts's cache-hit path returns: the same existing row).
    const turnNPlus1Prefix = buildForTurn()

    expect(turnNPrefix).toBe(turnNPlus1Prefix)
    expect(hashPrefix(turnNPrefix)).toBe(hashPrefix(turnNPlus1Prefix))
  })

  it('the hash CHANGES once a new summary is actually written (a real threshold crossing)', () => {
    const turnNPrefix = assembleSynthesisPrefix({
      precedingBlock: CHART_HEADER_BLOCK,
      summaryText: 'Summary v1 — covers turns 0-5.',
    })
    const turnNPlus1Prefix = assembleSynthesisPrefix({
      precedingBlock: CHART_HEADER_BLOCK,
      summaryText: 'Summary v2 — covers turns 0-11.',
    })
    expect(hashPrefix(turnNPrefix)).not.toBe(hashPrefix(turnNPlus1Prefix))
  })

  it('the hash is UNAFFECTED by unrelated later sections changing, as long as the summary slot ' +
    'itself did not change — the slot is a stable prefix independent of trailing content', () => {
    const prefixA = assembleSynthesisPrefix({
      precedingBlock: CHART_HEADER_BLOCK,
      summaryText: 'Summary v1.',
      followingBlock: 'Guidance variant A',
    })
    const prefixB = assembleSynthesisPrefix({
      precedingBlock: CHART_HEADER_BLOCK,
      summaryText: 'Summary v1.',
      followingBlock: 'Guidance variant B',
    })
    // The full strings differ (trailing content differs)...
    expect(prefixA).not.toBe(prefixB)
    // ...but the STABLE PREFIX up to and including the summary slot is identical.
    const stablePrefixA = prefixA.split('\n\n---\n\n').slice(0, 2).join('\n\n---\n\n')
    const stablePrefixB = prefixB.split('\n\n---\n\n').slice(0, 2).join('\n\n---\n\n')
    expect(hashPrefix(stablePrefixA)).toBe(hashPrefix(stablePrefixB))
  })
})
