/**
 * Lane G1-A — THE PRE-WIRE SCAN'S TWO HARDENING FINDINGS.
 *
 * ── H-3: `scan_failed` had no reachable true-state ──────────────────────────
 * The shipped suite's only test in the area was titled "the scan FAILS CLOSED,
 * unlike the register-leak lint" and asserted `scan_failed === false`. A
 * reviewer tried six malformed inputs (null/undefined/{}/[]/0/symbol) and every
 * one short-circuited before the `catch` block. Per §N.8 a flag whose true state
 * no code path can produce is not a clean signal — it is an unimplemented check
 * wearing a clean result's clothes, and this one guards whether a mortality date
 * reaches a reader.
 *
 * ── H-4: the 1200-char forced release leaked a complete mortality claim ──────
 * When `lastSafeCut()` released the whole buffer because MAX_HOLDBACK_CHARS was
 * exceeded with no sentence terminator, and the release point fell between a
 * mortality term and its paired date, both halves reached the reader —
 * deterministically, recurring every 1201 characters.
 */

import { describe, it, expect } from 'vitest'

import {
  scanMortalityPhrasing,
  StreamingMortalityScanner,
  MAX_HOLDBACK_CHARS,
  FORCED_RELEASE_OVERLAP_CHARS,
  type MortalityScanResult,
} from '../phrasing_scan'

// ═══════════════════════════════════════════════════════════════════════════
// H-3 — `scan_failed` can really become true, and fail-closed really fires.
// ═══════════════════════════════════════════════════════════════════════════

describe('H-3 — the failure path EXISTS and is demonstrated', () => {
  const unscannable: Array<[string, unknown]> = [
    ['a plain object', {}],
    ['an array', []],
    ['a number', 42],
    ['a boolean', true],
    ['a function', () => 'x'],
    ['a Map', new Map()],
  ]

  for (const [label, value] of unscannable) {
    it(`${label} → scan_failed TRUE and NOTHING is emitted`, () => {
      const r = scanMortalityPhrasing(value as string)
      // The signal reads true. Before the hardening round this returned
      // `{clean: '', scan_failed: false}` — "the scan ran and the output is
      // legitimately empty", which was a lie about a check that never ran.
      expect(r.scan_failed, `${label} did not register as a scan failure`).toBe(true)
      // And FAIL CLOSED: the text does not go out.
      expect(r.clean).toBe('')
      expect(r.hits).toEqual([])
    })
  }

  it('a real string still scans normally — the guard is not a blanket refusal', () => {
    const r = scanMortalityPhrasing('Jupiter transits the tenth house next year.')
    expect(r.scan_failed).toBe(false)
    expect(r.clean).toBe('Jupiter transits the tenth house next year.')
  })

  it('genuinely EMPTY input is not a failure — absence of text is not absence of a check', () => {
    // Kept distinct on purpose. '' and null mean "there was nothing to scan",
    // which is a different statement from "the scan could not run", and
    // conflating them would re-create the §N.8 defect in the other direction.
    for (const empty of ['', null, undefined]) {
      const r = scanMortalityPhrasing(empty as unknown as string)
      expect(r.scan_failed).toBe(false)
    }
  })

  it('a mortality-date sentence is STILL redacted (the scan does its day job)', () => {
    const r = scanMortalityPhrasing('The chart indicates death around 2047. Jupiter is strong.')
    expect(r.scan_failed).toBe(false)
    expect(r.clean).not.toContain('2047')
    expect(r.clean).toContain('Jupiter is strong.')
    expect(r.hits).toHaveLength(1)
  })
})

describe('H-3 — the STREAMING wrapper propagates the failure and emits nothing', () => {
  // The wrapper's own contract, driven through its injectable scanner. The
  // underlying failure is real and proven above; this proves the wrapper
  // reacts to it correctly, which is the part the reader depends on.
  const alwaysFails = (): MortalityScanResult => ({ clean: '', hits: [], scan_failed: true })

  it('scanFailed becomes true and push() returns nothing', () => {
    const s = new StreamingMortalityScanner(alwaysFails)
    const emitted = s.push('The native will die in 2047. ')
    expect(s.scanFailed).toBe(true)
    expect(emitted).toBe('')
  })

  it('flush() also emits nothing once the scan has failed', () => {
    const s = new StreamingMortalityScanner(alwaysFails)
    s.push('some prose without a terminator')
    expect(s.flush()).toBe('')
    expect(s.scanFailed).toBe(true)
  })

  it('a scanner that never fails leaves scanFailed false and emits the prose', () => {
    const s = new StreamingMortalityScanner()
    const out = s.push('Jupiter is strong this year. ')
    expect(s.scanFailed).toBe(false)
    expect(out).toContain('Jupiter is strong this year.')
  })

  it('ONE failed span poisons the flag for the whole block, permanently', () => {
    // A block that failed to scan even once must not report clean at commit.
    let calls = 0
    const failsOnce = (text: string): MortalityScanResult => {
      calls += 1
      return calls === 1 ? { clean: '', hits: [], scan_failed: true } : { clean: text, hits: [], scan_failed: false }
    }
    const s = new StreamingMortalityScanner(failsOnce)
    s.push('First sentence. ')
    expect(s.scanFailed).toBe(true)
    s.push('Second sentence. ')
    expect(s.scanFailed, 'a later success must not clear an earlier failure').toBe(true)
  })
})

// ═══════════════════════════════════════════════════════════════════════════
// H-4 — the forced-release boundary.
// ═══════════════════════════════════════════════════════════════════════════

describe('H-4 — a term/date pair straddling the forced release is caught', () => {
  /**
   * Build unpunctuated filler of exactly `n` characters. No `.`/`!`/`?`/`\n`,
   * so `lastSafeCut` cannot find a sentence boundary and the FORCED release is
   * the only thing that can move the buffer.
   */
  //
  // NOTE the leading space every payload below is prefixed with. `slice(0, n)`
  // truncates mid-word, and gluing the filler's tail directly onto `death`
  // produces `bendeath`, which the WORD-BOUNDED mortality lexicon correctly
  // does not match — so the fixture would have been testing nothing while
  // appearing to reproduce the leak. Found while debugging this very block.
  const filler = (n: number): string => 'the chart shows a strong benefic influence here '.repeat(200).slice(0, n)

  /**
   * Run the scanner over a delta sequence and return everything it emitted.
   *
   * ── WHY DELTAS, AND NOT ONE `push` (learned the hard way) ─────────────────
   * The first version of this block fed the whole span in a single `push` and
   * PASSED against the un-fixed code — because a single push puts the term and
   * the date in the same scan span, where they were always caught. The leak
   * needs them in DIFFERENT spans, which is what a real stream produces: the
   * term rides out on the delta that trips the forced release, and the date
   * arrives on the next one. Every case below is therefore driven as a delta
   * sequence, and the mutation check that motivated this rewrite is in the
   * report.
   */
  const runDeltas = (deltas: string[]): { emitted: string; scanner: StreamingMortalityScanner } => {
    const scanner = new StreamingMortalityScanner()
    let emitted = ''
    for (const d of deltas) emitted += scanner.push(d)
    emitted += scanner.flush()
    return { emitted, scanner }
  }

  it('the mortality term and its date do NOT both reach the reader', () => {
    // The term sits at the very end of the delta that trips the forced release;
    // the date arrives on the next one. Against the un-fixed code the term goes
    // out with the release and the date goes out at flush, and the reader has
    // the whole claim.
    const { emitted, scanner } = runDeltas([
      `${filler(MAX_HOLDBACK_CHARS - 2)} death`,
      ' around 2047 and then more prose',
    ])
    expect(emitted, 'the date half leaked past the forced release').not.toContain('2047')
    expect(scanner.hits.length, 'no redaction was recorded at the boundary').toBeGreaterThan(0)
  })

  it('the pair is caught across a whole sweep of alignments around the boundary', () => {
    // The reviewer measured ~2.4% of alignments leaking. Sweeping the offset is
    // the only honest way to assert the WINDOW is closed rather than that one
    // lucky alignment happens to work.
    const leaked: number[] = []
    for (let offset = -40; offset <= 40; offset += 2) {
      const { emitted } = runDeltas([
        `${filler(MAX_HOLDBACK_CHARS + offset)} death`,
        ' around 2047 and then more prose follows',
      ])
      if (emitted.includes('2047')) leaked.push(offset)
    }
    expect(leaked, `alignments still leaking the date: ${leaked.join(', ')}`).toEqual([])
  })

  it('holds when the prose is fed in small uniform deltas', () => {
    // The realistic shape: a model emitting token-sized chunks across the bound.
    const text = `${filler(MAX_HOLDBACK_CHARS - 15)} death around 2047 and then more prose`
    for (const size of [7, 13, 37, 64]) {
      const deltas: string[] = []
      for (let i = 0; i < text.length; i += size) deltas.push(text.slice(i, i + size))
      const { emitted } = runDeltas(deltas)
      expect(emitted, `leaked with delta size ${size}`).not.toContain('2047')
    }
  })

  it('the term/date pair is caught even with the date several deltas later', () => {
    const { emitted } = runDeltas([
      `${filler(MAX_HOLDBACK_CHARS - 2)} death`,
      ' around',
      ' the',
      ' year',
      ' 2047 and then more prose',
    ])
    expect(emitted).not.toContain('2047')
  })

  it('the forced release still MAKES PROGRESS — the stream cannot stall', () => {
    // The bound exists so one enormous unpunctuated span cannot buffer forever.
    // Retaining a tail must not have traded a leak for a hang.
    expect(FORCED_RELEASE_OVERLAP_CHARS).toBeLessThan(MAX_HOLDBACK_CHARS)
    const s = new StreamingMortalityScanner()
    const out = s.push(filler(MAX_HOLDBACK_CHARS + 500))
    expect(out.length).toBeGreaterThan(0)
    expect(out.length).toBe(MAX_HOLDBACK_CHARS + 500 - FORCED_RELEASE_OVERLAP_CHARS)
  })

  it('the retained tail is HELD, never emitted twice', () => {
    // Double-emission would be a different bug wearing the same fix.
    const s = new StreamingMortalityScanner()
    const text = filler(MAX_HOLDBACK_CHARS + 300)
    const emitted = s.push(text) + s.flush()
    expect(emitted).toBe(text)
  })

  it('ordinary punctuated prose is unaffected by the overlap logic', () => {
    const s = new StreamingMortalityScanner()
    const out = s.push('Jupiter is strong. Saturn is weak. ') + s.flush()
    expect(out).toBe('Jupiter is strong. Saturn is weak. ')
    expect(s.hits).toEqual([])
  })

  it('a benign long span with a NUMBER but no mortality term is not redacted', () => {
    // The floor in the other direction: the overlap must not turn the scan into
    // a blanket digit filter.
    const s = new StreamingMortalityScanner()
    const text = `${filler(MAX_HOLDBACK_CHARS - 20)} a strong Jupiter return in 2047 brings gains`
    const emitted = s.push(text) + s.flush()
    expect(emitted).toContain('2047')
    expect(s.hits).toEqual([])
  })
})
