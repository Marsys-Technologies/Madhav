/**
 * V3-E-061 (CRITICAL, Pariprashna v3 closeout, Surrogate disposition
 * COMMISSION_FIX_THIS_CAMPAIGN, tracker event `d9fd0274-8c1d-49c9-9b10-
 * 382510438a1a`): the register-leak lint correctly DETECTS an attempted
 * internal-namespace leak inside a citation sentinel, but the citation
 * rewriter's timeout/malformed-sentinel flush path forwarded whatever
 * SURVIVED the lint straight into reader-visible prose — fail OPEN instead
 * of fail CLOSED. Reproduced live in production twice (`EDIR_V3_REGISTER_v1_0
 * .md` §V3-E-061, S2, 2026-08-28) as the literal malformed token `⟦cite: ⟧`
 * appearing mid-sentence in a real reading.
 *
 * Root cause (confirmed by code read, `citations/rewriter.ts`): a held
 * sentinel that times out (or hits the byte ceiling, or the stream ends
 * mid-sentinel) is flushed via `flushHold`, which ran the register-leak lint
 * over the held bytes and appended `lint.clean` to `out.text`. The lint only
 * strips KNOWN internal-id shapes (signal ids, table names, register
 * acronyms, fact-id namespaces) — it has NO pattern for the sentinel markup
 * itself (`⟦`, `cite:`, `⟧`), so the bracket syntax always survived the lint
 * and always reached the reader on any malformed flush. Confirmed exactly by
 * the production SSE capture: a `register_leak:redact` flag (pattern
 * `fact_id_namespace`) fired INSIDE the same hold, immediately followed by a
 * `malformed_sentinel:timeout` flag, immediately followed by the raw
 * `⟦cite: ⟧` delta — i.e. the internal id WAS correctly redacted, but the
 * bracket wrapper it lived inside was not, and rode along to the reader.
 *
 * This file has two jobs:
 *   1. Reproduce the OBSERVED defect exactly (same flag sequence, same
 *      malformed-token shape) and prove the fix closes it.
 *   2. Answer the deeper question the finding explicitly asks for: could a
 *      slower/larger redaction case leak GENUINE pre-redaction content
 *      (not just an empty bracket pair)? Answer: YES, structurally — the
 *      pre-fix path's safety depended entirely on the lint's pattern
 *      coverage, so ANY internal token shape the lint's pattern list does
 *      not yet recognize would have been forwarded verbatim, unredacted.
 *      The second describe block proves this with a token shape deliberately
 *      chosen to match NONE of `register_leak_lint.ts`'s HARD_PATTERNS.
 *
 * The fix (`rewriter.ts` `flushHold`/`dropSegment`) does not depend on lint
 * coverage at all: a malformed hold's bytes are DROPPED IN THEIR ENTIRETY,
 * never partially forwarded. Both scenarios below prove that structurally —
 * not merely "this specific pattern is now also covered".
 */

import { describe, it, expect } from 'vitest'
import { CitationStreamRewriter, TIMEOUT_MS } from '@/lib/pariprashna/citations/rewriter'
import { lintReaderProse } from '@/lib/pariprashna/citations/register_leak_lint'
import { makeFixtureResolver, runStream } from './fixtures'

describe('V3-E-061: known-pattern content — the exact production reproduction', () => {
  it('a fact_id_namespace token mid-sentinel that times out never reaches text as bracket markup', () => {
    const rw = new CitationStreamRewriter({ resolver: makeFixtureResolver(), modelId: 'm' })

    // Sanity check the mechanism this test depends on: the lint DOES redact
    // this token on its own — the bug is not "the lint fails to detect it",
    // it is "the flush forwards what's left after detection".
    const preflightLint = lintReaderProse('⟦cite: PLN.SUN', makeFixtureResolver())
    expect(preflightLint.leakCount).toBeGreaterThanOrEqual(1)
    expect(preflightLint.clean).not.toMatch(/PLN\.SUN/)
    expect(preflightLint.clean).toContain('⟦cite:') // ← the surviving markup

    // Reproduce the exact wire sequence from the production capture: prose,
    // then an internal fact-id-namespace token opens a sentinel that never
    // closes before TIMEOUT_MS elapses, then more prose arrives afterward.
    const opening = rw.write(
      'Because wealth-building is currently shadowed by the A6 Arudha of competitors ⟦cite: PLN.SUN',
      0,
    )
    expect(opening.text).toBe('Because wealth-building is currently shadowed by the A6 Arudha of competitors ')
    expect(rw.isHolding()).toBe(true)

    const flushed = rw.checkTimeout(TIMEOUT_MS + 1)
    // Flag order matches the production capture exactly: redact fires from
    // linting the held bytes, THEN the malformed_sentinel:timeout flag.
    expect(flushed.events.map((e) => (e.type === 'flag' ? e.flag : e.type))).toEqual([
      'register_leak',
      'malformed_sentinel',
    ])
    expect(flushed.events[0]).toMatchObject({
      flag: 'register_leak',
      verdict: 'redact',
      pattern: 'fact_id_namespace',
    })
    expect(flushed.events[1]).toMatchObject({ flag: 'malformed_sentinel', reason: 'timeout' })

    const rest = rw.write('⟧, sustainable career success right now depends entirely on...', TIMEOUT_MS + 2)
    const tail = rw.end() // release the held trailing partial word ("on...")

    const fullText = opening.text + flushed.text + rest.text + tail.text
    // Fail closed: no trace of the internal content or the OPENING sentinel
    // markup — the thing that actually identifies a citation attempt and
    // could carry internal content — anywhere in the output.
    expect(fullText).not.toContain('⟦')
    expect(fullText).not.toContain('cite:')
    expect(fullText).not.toContain('PLN.SUN')
    // In particular, the EXACT malformed string observed live in production
    // must never be constructable from this stream's output.
    expect(fullText).not.toContain('⟦cite: ⟧')
    // Documented residual (not a leak): once the sentinel's opener+content is
    // dropped, a lone trailing closer character arriving afterward is
    // ordinary pass-mode prose like any other character — findOpener only
    // recognizes `⟦`/`[[` as openers, so a bare `⟧` with no preceding
    // `⟦cite:` carries no internal id, register name, or protocol structure.
    // It is cosmetically odd, never a namespace/content leak, and out of
    // this finding's scope.
    expect(fullText).toContain('⟧')
    // The surrounding prose still flows on both sides of the dropped segment.
    expect(fullText).toContain('Because wealth-building is currently shadowed by the A6 Arudha of competitors')
    expect(fullText).toContain('sustainable career success right now depends entirely on')
  })
})

describe('V3-E-061 deeper risk: an UNRECOGNIZED internal token shape — genuine content, not just an empty token', () => {
  it('a token matching NONE of the lint HARD_PATTERNS would have leaked verbatim pre-fix, and must not leak post-fix', () => {
    // Deliberately not signal-id-shaped, not asset/table-prefixed, not a
    // register acronym/full name, not a fact_id-namespace-shaped token — a
    // token this lint's pattern list has never heard of. This stands in for
    // "the next internal identifier format nobody has written a pattern for
    // yet" — the exact gap the pre-fix code's safety silently depended on
    // never existing.
    const unrecognizedInternalToken = 'cache_slot_9f3a_row_42_customer_pii_row'
    const preflightLint = lintReaderProse(`⟦cite: ${unrecognizedInternalToken}`, makeFixtureResolver())
    // Proves the premise: this shape is invisible to the lint today.
    expect(preflightLint.leakCount).toBe(0)
    expect(preflightLint.clean).toBe(`⟦cite: ${unrecognizedInternalToken}`)

    const rw = new CitationStreamRewriter({ resolver: makeFixtureResolver(), modelId: 'm' })
    rw.write(`Something about `, 0)
    rw.write(`⟦cite: ${unrecognizedInternalToken}`, 1)
    expect(rw.isHolding()).toBe(true)
    const flushed = rw.checkTimeout(TIMEOUT_MS + 2)
    const ended = rw.end()
    const fullText = flushed.text + ended.text

    // The deeper, more serious variant the finding asked to be assessed:
    // genuine unredacted internal content — not just empty bracket markup —
    // must never reach the reader via this path.
    expect(fullText).not.toContain(unrecognizedInternalToken)
    expect(fullText).not.toContain('⟦')
    expect(fullText).not.toContain('cite:')
  })
})

describe('V3-E-061 sibling: a CLOSED-but-empty-ref canonical sentinel (no timeout involved)', () => {
  it('⟦cite: ⟧ — a well-formed close with an empty ref — is dropped, not emitted as prose', () => {
    // This reproduces the literal leaked string from a SECOND angle: even
    // with no timeout at all (closer arrives well within budget), a
    // canonical `⟦…⟧` sentinel that fails to PARSE as a citation (empty ref)
    // used to fall through to the generic non-citation-prose path — which,
    // like the timeout path, has no sentinel-markup-aware scrubbing. The
    // `[[…]]` tolerant form is deliberately UNCHANGED (still emitted as
    // prose — it is genuinely ambiguous with a real wiki-style link).
    const rw = new CitationStreamRewriter({ resolver: makeFixtureResolver(), modelId: 'm' })
    const { text, events } = runStream(rw, ['competitors ⟦cite: ⟧, sustainable career...'])
    expect(text).not.toContain('⟦')
    expect(text).not.toContain('⟧')
    expect(text).not.toContain('cite:')
    expect(text).toContain('competitors')
    expect(text).toContain('sustainable career')
    expect(events.some((e) => e.type === 'flag' && e.flag === 'malformed_sentinel' && e.reason === 'parse_failed')).toBe(
      true,
    )
  })

  it('a non-citation [[wiki]] link is still emitted as ordinary prose (unchanged, deliberately ambiguous)', () => {
    const rw = new CitationStreamRewriter({ resolver: makeFixtureResolver(), modelId: 'm' })
    const { text } = runStream(rw, ['see [[SomePage]] now'])
    expect(text).toBe('see [[SomePage]] now')
  })
})
