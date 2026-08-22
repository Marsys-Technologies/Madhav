/**
 * pariprashna/reader_text/review.ts — lane P4-J review step.
 *
 * Runs every `ReaderTextEntry` through the THREE real gates the charter names
 * (§10.5): the register-leak lint, the voice lint, and the citation gate
 * (`citation_gate.ts`, this lane's own structural grounding check — see its
 * header comment for why a live-turn `CitationResolver` does not apply here),
 * plus a fourth gate the lane's own false safety claim earned it: the
 * hedge-band check (`hedge_bands.ts`), which recomputes the confidence band
 * each entry's catalog `confidence` licenses and fails any entry whose
 * authored hedge does not match it. That claim used to live only in an
 * `entries.ts` comment and was false for 9 of 25 entries; it is now computed
 * at review time, so an overclaimed hedge cannot reach the frozen artifact.
 * The two lints are imported UNCHANGED from their existing modules — this
 * file adds zero new leak/voice detection logic and never loosens either
 * lint's behavior (§9 hard-never: never weaken a safety gate to make text
 * pass). An entry only reaches `freeze.ts` if `passed` here is true.
 *
 * `difficultFinding` is passed as `false` to the voice lint for every entry:
 * catalog reader-text is calm, structural narration (never conditioned on a
 * live turn's `SafetyDecision`), so the probability-framing / severity-
 * ordering checks (voice lint parts 2–3, difficult-finding-gated) do not
 * apply here — only the imperative detector (part 1, unconditional) is live.
 * If a future entry needs a probability claim, it should be phrased with an
 * inline qualitative frame directly (this module does not synthesize a fake
 * "difficult finding" context to force the rewrite path).
 */
import { lintReaderProse } from '../citations/register_leak_lint'
import { lintVoiceProse } from '../voice/voice_lint'
import { checkCitationGate } from './citation_gate'
import { checkHedgeBand } from './hedge_bands'
import type { MsrSignal, ReaderTextEntry, ReviewedEntry, ReviewFlag } from './types'

const ERROR_LEVELS = new Set(['error'])

export function reviewEntry(entry: ReaderTextEntry, signal: MsrSignal | null): ReviewedEntry {
  const flags: ReviewFlag[] = []

  const leak = lintReaderProse(entry.reader_text)
  for (const f of leak.flags) {
    flags.push({
      source: 'register_leak',
      code: f.pattern,
      level: f.verdict === 'telemetry' ? 'info' : 'error',
      detail: `${f.verdict}: ${f.original}${f.replacement ? ` -> ${f.replacement}` : ''}`,
    })
  }

  const voice = lintVoiceProse(leak.clean, { difficultFinding: false })
  for (const f of voice.flags) {
    flags.push({
      source: 'voice',
      code: f.code,
      level: f.level,
      detail: f.detail,
    })
  }

  const gate = checkCitationGate(entry, signal)
  flags.push(...gate.flags)

  const hedge = checkHedgeBand(entry, signal)
  flags.push(...hedge.flags)

  const hasHardLeak = leak.leakCount > 0
  const hasErrorFlag = flags.some((f) => ERROR_LEVELS.has(f.level))
  const passed = !hasHardLeak && !hasErrorFlag && gate.passed && hedge.passed

  return {
    signal_id: entry.signal_id,
    clean_text: voice.clean,
    passed,
    flags,
  }
}

export function reviewAll(
  entries: readonly ReaderTextEntry[],
  signalsById: ReadonlyMap<string, MsrSignal>,
): ReviewedEntry[] {
  return entries.map((e) => reviewEntry(e, signalsById.get(e.signal_id) ?? null))
}
