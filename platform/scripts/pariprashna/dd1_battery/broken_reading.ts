/**
 * dd1_battery/broken_reading.ts — the DELIBERATELY REGISTER-BROKEN readings.
 *
 * The overnight charter §6.2 names this file's job with the battery's name on
 * it: *"the DD-1 feel-proxy battery fed a deliberately register-broken reading
 * and observed to fail it before its first real pass counts."*
 *
 * Two disciplines are encoded here, both from CLAUDE.md §N.8:
 *
 *  1. **Per-check, not just globally.** A battery that fails overall on one
 *     broken input tells you nothing about the checks that never fired. So
 *     there is one purpose-built broken corpus PER prose check, each breaking
 *     ONLY that check's rule, plus one composite reading that breaks all of
 *     them at once (the "one deliberately register-broken reading" the charter
 *     literally asks for).
 *
 *  2. **The clean counterpart must be genuinely clean.** Every broken corpus
 *     has a `clean` sibling built from the same shape. The red proof asserts
 *     BOTH directions: broken ⇒ the check reports FAIL, clean ⇒ the check
 *     reports PASS. A detector that fires on everything is as useless as one
 *     that fires on nothing.
 *
 * The prose below is synthetic and hand-written. It is not a model output and
 * is never sent anywhere — it only ever travels into `prose_checks.ts`'s pure
 * functions. The synthetic chart is not consulted to build it.
 */
import type { ReadingRecord } from './prose_checks'
import type { WireEvent, CommittedBlockRecord } from './live_turn'

function ev(type: string, raw: Record<string, unknown>, atMs = 0): WireEvent {
  return { type, raw: { type, ...raw }, atMs }
}

function blk(blockId: string, text: string, seqIndex: number, atMs = 0): CommittedBlockRecord {
  return { blockId, kind: 'paragraph', role: 'elaboration', text, atMs, seqIndex }
}

/**
 * A reading that is clean on every rule this battery checks. Deliberately
 * written IN the design plan's register: declarative about the chart, Sanskrit
 * glossed inline, verdict first, one calibrated phrase, no hedging stack, no
 * bare percentage leading a sentence, chips already defined on the wire.
 */
export function cleanReading(label = 'clean'): ReadingRecord {
  const prose = [
    'The chart is distinctly more likely than not to favour a change of role in this period.',
    '',
    'Śaśa Yoga (Saturn strongly placed in its own sign in an angle) is the structural reason ⟦1⟧. ' +
      'The tenth house is tenanted rather than merely aspected, and the period lord rules it ⟦2⟧. ' +
      'Calibrated at 68% for the window; treat the band, not the point.',
    '',
    'On the question of the specific employer, this chart is silent. The factors that would speak ' +
      'to it are unremarkable — and that is the finding, not a failure to look. What the period ' +
      'asks is preparation rather than a decision.',
  ].join('\n')

  const events: WireEvent[] = [
    ev('turn.open', { turn_id: 't', conversation_id: 'c', chart_id: 'x' }, 0),
    ev('citation.define', { n: 1, index: 1, reader_label: 'Saturn in Aquarius, 10th', grade: 'primary', ref: 'r1' }, 100),
    ev('citation.define', { n: 2, index: 2, reader_label: 'Daśā lord rules the 10th', grade: 'supporting', ref: 'r2' }, 120),
    ev('block.delta', { block_id: 'b1', delta: 'The chart is' }, 900),
    ev('block.commit', { block_id: 'b1', text: 'The chart is distinctly more likely than not to favour a change of role in this period.' }, 1200),
    ev('block.commit', { block_id: 'b2', text: 'Śaśa Yoga (Saturn strongly placed) is the structural reason ⟦1⟧ and the period lord rules the tenth ⟦2⟧.' }, 1800),
    ev('turn.commit', { conversation_id: 'c', message_id: 'm' }, 2000),
    ev('turn.close', { status: 'ok' }, 2010),
  ]

  return {
    label,
    question: 'What does this period ask of my work?',
    prose,
    events,
    blocks: [blk('b1', 'The chart is distinctly more likely than not to favour a change of role in this period.', 4, 1200), blk('b2', 'Śaśa Yoga (Saturn strongly placed) is the structural reason ⟦1⟧ and the period lord rules the tenth ⟦2⟧.', 5, 1800)],
    firstProseDeltaMs: 900,
  }
}

// ── Per-check broken corpora ───────────────────────────────────────────────

/** M5 — internal taxonomy reaching the reader. */
function brokenM5(): ReadingRecord {
  const base = cleanReading('BROKEN:M5')
  const prose =
    'The chart is distinctly more likely than not to favour a change of role. This is carried by ' +
    'SIG.MSR.413, which the bo_laksana writer emitted into bodha_signals from the fact PLN.SUN. ' +
    'The MSR concludes that the tenth house is the operative one, and the CGM agrees.'
  return { ...base, prose, blocks: [blk('b1', prose, 4, 1200)] }
}

/** REG — a second-person remedy imperative, and a severity claim with no uncertainty frame. */
function brokenREG(): ReadingRecord {
  const base = cleanReading('BROKEN:REG')
  const prose =
    'There is a serious risk to the health of the father in this window. ' +
    'You should wear a ruby set in gold on the ring finger, and you must chant the Aditya ' +
    'Hridayam daily. Wear it from the first Sunday of the month.'
  return { ...base, prose, blocks: [blk('b1', prose, 4, 1200)] }
}

/** PLAIN — one instance of each §7.1/§7.3/§7.4 rule this battery checks. */
function brokenPLAIN(): ReadingRecord {
  const base = cleanReading('BROKEN:PLAIN')
  const prose = [
    'Unfortunately, no data was available for this question.',
    "I couldn't find anything on the marriage question, and the system was unable to complete the lookup.",
    'It is not for us to know what the ninth house intends here.',
    'You will change employers before the end of the year.',
    '68% is the figure for this window.',
    'Perhaps it may be that possibly the transit could matter.',
  ].join(' ')
  return { ...base, prose, blocks: [blk('b1', prose, 4, 1200)] }
}

/** CITE — raw sentinel residue, a malformed_sentinel flag, an illegal grade, an undefined chip. */
function brokenCITE(): ReadingRecord {
  const base = cleanReading('BROKEN:CITE')
  const prose =
    'The tenth house is the operative one ⟦cite: PLN.SUN⟧ and the period lord rules it [[cite: HSE.10]]. ' +
    'A third strand ⟦7⟧ supports the same reading.'
  const events: WireEvent[] = [
    ev('citation.define', { n: 1, index: 1, reader_label: 'x', grade: 'fabricated_grade', ref: 'r1' }, 100),
    ev('flag', { flag: 'malformed_sentinel', reason: 'eof_unclosed', raw: '⟦cite: PLN.SU' }, 150),
    ev('block.commit', { block_id: 'b1', text: prose }, 1200),
    ev('turn.close', { status: 'ok' }, 1300),
  ]
  return { ...base, prose, events, blocks: [blk('b1', prose, 2, 1200)] }
}

/** M6-wire — a define arriving AFTER the block that references it, and a changed re-commit. */
function brokenM6Wire(): ReadingRecord {
  const base = cleanReading('BROKEN:M6-wire')
  const text1 = 'The tenth house is the operative one ⟦3⟧.'
  const text2 = 'The tenth house is the operative one, decisively ⟦3⟧.'
  const events: WireEvent[] = [
    ev('block.commit', { block_id: 'b1', text: text1 }, 1000),
    // The define arrives LATE — the chip was already committed as plain text.
    ev('citation.define', { n: 3, index: 3, reader_label: 'Saturn in the 10th', grade: 'primary', ref: 'r3' }, 1100),
    // …and the same block is re-committed with DIFFERENT text.
    ev('block.commit', { block_id: 'b1', text: text2 }, 1200),
    ev('turn.close', { status: 'ok' }, 1300),
  ]
  return {
    ...base,
    prose: text2,
    events,
    blocks: [blk('b1', text1, 0, 1000), blk('b1', text2, 2, 1200)],
  }
}

/** M4 — a turn whose first prose delta lands far past the p50/p90 thresholds. */
function brokenM4(): ReadingRecord[] {
  return [
    { ...cleanReading('BROKEN:M4/a'), firstProseDeltaMs: 21_000 },
    { ...cleanReading('BROKEN:M4/b'), firstProseDeltaMs: 22_000 },
    { ...cleanReading('BROKEN:M4/c'), firstProseDeltaMs: 23_000 },
  ]
}

/**
 * THE composite deliberately-register-broken reading — the single artifact the
 * charter asks for by name. It leaks internal taxonomy, commands the reader,
 * invents certainty where a null belongs, and carries protocol residue, all in
 * one reading. Every prose check must fail on it.
 */
export function compositeBrokenReading(): ReadingRecord {
  const prose = [
    'You will be promoted before September.',
    '',
    'SIG.MSR.413 is close to unequivocal here — the bo_laksana signal in bodha_signals, ' +
      'derived from PLN.SUN, settles it. The MSR, CGM, and CDLM all agree ⟦cite: HSE.10⟧.',
    '',
    '92% is the figure. Unfortunately, no data was available on the timing, and the system was ' +
      'unable to resolve it; perhaps it may be that possibly the transit matters.',
    '',
    'You should wear a ruby set in gold, and you must chant the Aditya Hridayam daily.',
  ].join('\n')

  const events: WireEvent[] = [
    ev('block.commit', { block_id: 'b1', text: prose }, 1000),
    ev('citation.define', { n: 9, index: 9, reader_label: 'x', grade: 'not_a_grade', ref: 'r9' }, 1100),
    ev('flag', { flag: 'malformed_sentinel', reason: 'byte_limit', raw: '⟦cite: HSE.10' }, 1150),
    ev('turn.close', { status: 'ok' }, 1200),
  ]

  return {
    label: 'BROKEN:composite',
    question: 'Will I be promoted this year?',
    prose,
    events,
    blocks: [blk('b1', prose + ' ⟦9⟧', 0, 1000)],
    firstProseDeltaMs: 30_000,
  }
}

/** checkId → the corpus that must make THAT check report FAIL. */
export const BROKEN_CORPORA: Record<string, ReadingRecord[]> = {
  M5: [brokenM5()],
  REG: [brokenREG()],
  PLAIN: [brokenPLAIN()],
  CITE: [brokenCITE()],
  'M6-wire': [brokenM6Wire()],
  M4: brokenM4(),
}

/** checkId → a corpus that must make THAT check report PASS (the green counterpart). */
export const CLEAN_CORPORA: Record<string, ReadingRecord[]> = {
  M5: [cleanReading('clean:M5')],
  REG: [cleanReading('clean:REG')],
  PLAIN: [cleanReading('clean:PLAIN')],
  CITE: [cleanReading('clean:CITE')],
  'M6-wire': [cleanReading('clean:M6-wire')],
  M4: [cleanReading('clean:M4')],
}
