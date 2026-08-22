/**
 * dd1_battery/prose_checks.ts — the wire/prose lane of the DD-1 feel-proxy
 * battery.
 *
 * MACHINE PROXY — NOT AC-15 (see metrics.ts PROXY_LABEL).
 *
 * Every detector here is a PURE function over a `ReadingRecord[]` corpus. That
 * purity is not stylistic: it is what lets `red_proof.ts` feed the SAME code
 * path a deliberately register-broken corpus and observe it fail, per §N.8 and
 * the overnight charter §6.2 ("the DD-1 feel-proxy battery fed a deliberately
 * register-broken reading and observed to fail it before its first real pass
 * counts"). If a detector ever reaches outside its corpus argument, the red
 * proof stops proving anything about the real run.
 *
 * Detectors REUSE the project's own gates wherever one exists:
 *   M5   → src/lib/pariprashna/citations/register_leak_lint.ts (lintReaderProse)
 *   REG  → src/lib/pariprashna/voice/voice_lint.ts (lintVoiceProse)
 *   CITE → src/lib/pariprashna/citations/grammar.ts (sentinel grammar) +
 *          citations/types.ts (CitationGrade vocabulary)
 * Nothing below reimplements a lint the repo already ships.
 */
import { lintReaderProse } from '../../../src/lib/pariprashna/citations/register_leak_lint'
import { lintVoiceProse } from '../../../src/lib/pariprashna/voice/voice_lint'
import type { WireEvent, CommittedBlockRecord } from './live_turn'

export interface ReadingRecord {
  /** Probe label — used in findings so a failure names the reading. */
  label: string
  question: string
  /** The prose actually DELIVERED to the reader (committed blocks, joined). */
  prose: string
  events: WireEvent[]
  blocks: CommittedBlockRecord[]
  firstProseDeltaMs: number | null
}

export interface CheckOutcome {
  ok: boolean
  /** Every individual violation, verbatim enough to act on. */
  findings: string[]
  /** Structured counters the report prints. */
  detail: Record<string, unknown>
}

/** The chip token the server rewrites sentinels into pre-wire (§8.4.1). */
const CHIP_TOKEN = /⟦(\d+)⟧/g

/** `citations/types.ts` CitationGradeSchema — the legal grade vocabulary. */
const LEGAL_GRADES = new Set(['primary', 'supporting', 'contextual', 'unverified', 'prior_reading'])

// ── M5 · internal-ID leakage in reader prose ────────────────────────────────
export function checkM5(corpus: ReadingRecord[]): CheckOutcome {
  const findings: string[] = []
  let totalLeaks = 0
  for (const r of corpus) {
    const lint = lintReaderProse(r.prose)
    totalLeaks += lint.leakCount
    if (lint.leakCount > 0) {
      for (const f of lint.flags) {
        if (f.verdict === 'telemetry') continue
        findings.push(
          `[${r.label}] M5 leak (${f.pattern}, verdict=${f.verdict}): ${JSON.stringify(f.original)}`,
        )
      }
    }
    if (lint.clean !== r.prose) {
      findings.push(
        `[${r.label}] M5: the pre-wire lint would have altered the DELIVERED prose — ` +
          'something the server-side lint should have caught reached the reader.',
      )
    }
  }
  return { ok: findings.length === 0, findings, detail: { readings: corpus.length, hard_leak_matches: totalLeaks } }
}

// ── REG · register / voice lint ─────────────────────────────────────────────
//
// FATAL-LEVEL NOTE (§N.8 — read before "simplifying" this):
// `voice_lint.ts` emits NO `level: 'error'` flag today. Its two real
// violations — `voice_imperative_detected` (a second-person remedy command to
// the reader, violating design-plan P7 "The instrument answers; the tradition
// prescribes") and `voice_pacing_order_violation` (§7.2's uncertainty-before-
// severity ordering) — are deliberately `warn` THERE, because the pipeline
// must never kill a turn over prose it cannot safely rewrite. A battery has
// the opposite job: it reports, it does not serve. So this check treats those
// two codes as FAILING and says so out loud. Had it instead kept the obvious-
// looking "fail on level === 'error'" rule, REG could never have reported
// false at all — an unimplemented check wearing a clean result's clothes,
// which is the exact defect CLAUDE.md §N.8 names.
const REG_FATAL_CODES = new Set([
  'voice_imperative_detected',
  'voice_pacing_order_violation',
  'voice_lint_internal_error',
])

export function checkREG(corpus: ReadingRecord[]): CheckOutcome {
  const findings: string[] = []
  const census: Record<string, number> = {}
  for (const r of corpus) {
    // Run BOTH modes: `difficultFinding` is a turn-scoped proxy the battery
    // cannot observe from the wire, so checking both is the honest superset
    // rather than guessing which applied. Flags are de-duplicated by code so a
    // finding present in both modes is reported once.
    const seenCodes = new Set<string>()
    for (const difficultFinding of [false, true]) {
      const res = lintVoiceProse(r.prose, { difficultFinding })
      for (const f of res.flags) {
        census[f.code] = (census[f.code] ?? 0) + 1
        if (!REG_FATAL_CODES.has(f.code)) continue
        if (seenCodes.has(f.code)) continue
        seenCodes.add(f.code)
        findings.push(`[${r.label}] REG ${f.code} (level=${f.level} in voice_lint; FATAL in this battery): ${f.detail}`)
      }
    }
  }
  return { ok: findings.length === 0, findings, detail: { readings: corpus.length, flag_census: census } }
}

// ── PLAIN · §7.1 / §7.3 reader-register plainness ───────────────────────────
//
// PROVENANCE, stated where it can't be lost: the charter calls these "the §J
// plainness checks". CLAUDE.md §J is the acharya-grade quality standard and
// enumerates NO plainness checks; no artifact in this repo defines a "§J
// plainness" rubric. These rules are therefore taken from the design plan's
// own enumerated, machine-checkable register rules, quoted in each entry.
interface PlainRule {
  id: string
  /** Verbatim source sentence from the design plan. */
  rule: string
  re: RegExp
}

const PLAIN_RULES: PlainRule[] = [
  {
    id: 'banned_no_data',
    rule: '§7.3 Banned: "Unfortunately, no data…" (machine failure register)',
    re: /\bunfortunately,?\s+(?:there\s+is\s+)?no\s+data\b/i,
  },
  {
    id: 'banned_couldnt_find',
    rule: '§7.3 Banned: "I couldn\'t find…" (machine failure register)',
    re: /\bi\s+(?:couldn'?t|could\s+not|was\s+unable\s+to)\s+find\b/i,
  },
  {
    id: 'banned_system_unable',
    rule: '§7.3 Banned: "The system was unable…" (machine failure register)',
    re: /\bthe\s+system\s+(?:was\s+unable|could\s+not|failed)\b/i,
  },
  {
    id: 'banned_mystification',
    rule: '§7.3 Banned: "It is not for us to know…" (mystification)',
    re: /\bit\s+is\s+not\s+for\s+us\s+to\s+know\b/i,
  },
  {
    id: 'oracular_second_person',
    rule:
      '§7.1 rule 3: "Declarative about the chart, never oracular about the person. ' +
      '\\"The chart shows a period that…\\" not \\"You will…\\"."',
    re: /\byou\s+will\s+[a-z]/i,
  },
  {
    id: 'bare_percentage_leads_sentence',
    rule: '§7.4: "A bare percentage never leads a sentence (P6)."',
    re: /(?:^|[.!?]\s+|\n)\s*\d{1,3}\s?%/,
  },
]

/** §7.1 rule 5: "No hedging theater." Two or more hedges inside ONE sentence. */
const HEDGES = /\b(?:perhaps|possibly|maybe|it\s+may\s+be|conceivably|arguably)\b/gi

export function checkPLAIN(corpus: ReadingRecord[]): CheckOutcome {
  const findings: string[] = []
  const hits: Record<string, number> = {}
  for (const r of corpus) {
    for (const rule of PLAIN_RULES) {
      const re = new RegExp(rule.re.source, rule.re.flags.includes('g') ? rule.re.flags : rule.re.flags + 'g')
      let m: RegExpExecArray | null
      while ((m = re.exec(r.prose)) !== null) {
        hits[rule.id] = (hits[rule.id] ?? 0) + 1
        findings.push(`[${r.label}] PLAIN ${rule.id} — ${rule.rule} — matched: ${JSON.stringify(m[0].trim())}`)
        if (m.index === re.lastIndex) re.lastIndex += 1
      }
    }
    // Hedging stack, per sentence.
    for (const sentence of r.prose.split(/(?<=[.!?])\s+/)) {
      const found = sentence.match(HEDGES)
      if (found && found.length >= 2) {
        hits.hedging_theater = (hits.hedging_theater ?? 0) + 1
        findings.push(
          `[${r.label}] PLAIN hedging_theater — §7.1 rule 5: "No hedging theater." — ` +
            `${found.length} hedges in one sentence (${found.join(', ')}): ${JSON.stringify(sentence.slice(0, 160))}`,
        )
      }
    }
  }
  return { ok: findings.length === 0, findings, detail: { readings: corpus.length, hits } }
}

// ── CITE · citation integrity ───────────────────────────────────────────────
export function checkCITE(corpus: ReadingRecord[]): CheckOutcome {
  const findings: string[] = []
  let residues = 0
  let malformed = 0
  let illegalGrades = 0
  let undefinedChips = 0

  for (const r of corpus) {
    // (a) raw sentinel residue in DELIVERED prose. The grammar module accepts
    //     `⟦cite: ref⟧` and `[[cite: ref]]` (and mixed brackets); ANY of those
    //     shapes reaching the reader is a leak of the wire protocol.
    const residueRe = /(?:\[\[|⟦)\s*cite\s*:/gi
    let m: RegExpExecArray | null
    while ((m = residueRe.exec(r.prose)) !== null) {
      residues += 1
      findings.push(
        `[${r.label}] CITE unresolved sentinel residue at offset ${m.index}: ` +
          JSON.stringify(r.prose.slice(m.index, m.index + 60)),
      )
    }

    // (b) malformed_sentinel flags on the wire.
    for (const e of r.events) {
      if (e.type !== 'flag') continue
      const flagName = String(e.raw.flag ?? e.raw.code ?? '')
      if (flagName.includes('malformed_sentinel')) {
        malformed += 1
        findings.push(`[${r.label}] CITE malformed_sentinel flag: ${JSON.stringify(e.raw)}`)
      }
    }

    // (c) every citation.define carries a legal grade (when it carries one at
    //     all — the S-1 wire form is {index, signal_id, layer, snippet} and
    //     grade is optional there, so absence is not a violation).
    const definedIndexes = new Set<number>()
    for (const e of r.events) {
      if (e.type !== 'citation.define') continue
      const n = Number(e.raw.n ?? e.raw.index)
      if (Number.isFinite(n)) definedIndexes.add(n)
      const grade = e.raw.grade
      if (grade !== undefined && !LEGAL_GRADES.has(String(grade))) {
        illegalGrades += 1
        findings.push(`[${r.label}] CITE illegal citation grade ${JSON.stringify(grade)} on define n=${n}`)
      }
    }

    // (d) every chip token rendered to the reader has a define behind it.
    for (const b of r.blocks) {
      const re = new RegExp(CHIP_TOKEN.source, 'g')
      let cm: RegExpExecArray | null
      while ((cm = re.exec(b.text)) !== null) {
        const n = Number(cm[1])
        if (!definedIndexes.has(n)) {
          undefinedChips += 1
          findings.push(`[${r.label}] CITE chip ⟦${n}⟧ rendered in block ${b.blockId} with no citation.define`)
        }
      }
    }
  }

  return {
    ok: findings.length === 0,
    findings,
    detail: { readings: corpus.length, residues, malformed_sentinel_flags: malformed, illegal_grades: illegalGrades, undefined_chips: undefinedChips },
  }
}

// ── M6-wire · define-then-reference + committed-block immutability ──────────
export function checkM6Wire(corpus: ReadingRecord[]): CheckOutcome {
  const findings: string[] = []
  let lateDefines = 0
  let recommits = 0

  for (const r of corpus) {
    // define position by citation number (first define wins).
    const definePos = new Map<number, number>()
    r.events.forEach((e, i) => {
      if (e.type !== 'citation.define') return
      const n = Number(e.raw.n ?? e.raw.index)
      if (Number.isFinite(n) && !definePos.has(n)) definePos.set(n, i)
    })

    for (const b of r.blocks) {
      const re = new RegExp(CHIP_TOKEN.source, 'g')
      let cm: RegExpExecArray | null
      while ((cm = re.exec(b.text)) !== null) {
        const n = Number(cm[1])
        const pos = definePos.get(n)
        if (pos === undefined || pos > b.seqIndex) {
          lateDefines += 1
          findings.push(
            `[${r.label}] M6-wire define-then-reference violated: chip ⟦${n}⟧ committed in block ` +
              `${b.blockId} at wire index ${b.seqIndex}, but its citation.define is at ` +
              `${pos === undefined ? 'NEVER' : String(pos)} — the chip cannot render at final ` +
              'geometry on first paint.',
          )
        }
      }
    }

    // Committed blocks are append-only and parse-final: a block_id committing
    // twice with different text IS transmutation on the wire.
    const seen = new Map<string, string>()
    for (const b of r.blocks) {
      const prev = seen.get(b.blockId)
      if (prev !== undefined && prev !== b.text) {
        recommits += 1
        findings.push(
          `[${r.label}] M6-wire committed block ${b.blockId} re-committed with DIFFERENT text ` +
            `(${JSON.stringify(prev.slice(0, 60))} → ${JSON.stringify(b.text.slice(0, 60))}).`,
        )
      }
      seen.set(b.blockId, b.text)
    }
  }

  return { ok: findings.length === 0, findings, detail: { readings: corpus.length, late_defines: lateDefines, changed_recommits: recommits } }
}

// ── M4 · time-to-first-token ────────────────────────────────────────────────
function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return NaN
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1))
  return sorted[idx]
}

export function checkM4(corpus: ReadingRecord[]): CheckOutcome {
  const findings: string[] = []
  const samples = corpus
    .map((r) => r.firstProseDeltaMs)
    .filter((v): v is number => typeof v === 'number')
    .sort((a, b) => a - b)

  if (samples.length === 0) {
    return {
      ok: false,
      findings: ['M4: no turn produced a prose delta — nothing to measure.'],
      detail: { samples: 0 },
    }
  }
  const p50 = percentile(samples, 50)
  const p90 = percentile(samples, 90)
  if (p50 >= 4000) findings.push(`M4: p50 TTFT ${p50}ms exceeds the 4000ms threshold.`)
  if (p90 >= 12000) findings.push(`M4: p90 TTFT ${p90}ms exceeds the 12000ms threshold.`)
  return { ok: findings.length === 0, findings, detail: { samples: samples.length, p50_ms: p50, p90_ms: p90, all_ms: samples } }
}

export const PROSE_CHECKS: Record<string, (corpus: ReadingRecord[]) => CheckOutcome> = {
  M5: checkM5,
  REG: checkREG,
  PLAIN: checkPLAIN,
  CITE: checkCITE,
  'M6-wire': checkM6Wire,
  M4: checkM4,
}
