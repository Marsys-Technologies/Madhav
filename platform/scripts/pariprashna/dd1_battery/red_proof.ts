/**
 * dd1_battery/red_proof.ts — the §N.8 gate, encoded structurally.
 *
 * "A green from this battery does not count until the red exists."
 *
 * That sentence is not a promise in a report here; it is a code path. Every
 * check declares a `redProofKey` (metrics.ts). Before a check may report PASS,
 * a banked red-proof receipt must show, for that key:
 *
 *   red_fired  === true   — the check reported FAIL on a corpus deliberately
 *                           broken for exactly that rule; and
 *   green_clean === true  — the SAME check reported PASS on the clean
 *                           counterpart (a detector that fires on everything
 *                           is as useless as one that fires on nothing).
 *
 * …and the receipt's `detector_hash` must still match the current bytes of the
 * detector sources. Edit a detector and the banked proof goes stale, and every
 * PASS it was gating degrades to NOT_IMPLEMENTED until the proof is re-run.
 *
 * A FAIL is NEVER suppressed by this gate. The gate can only ever DOWNGRADE a
 * PASS — it exists to stop an unproven detector from minting a green, not to
 * hide a red.
 */
import { createHash } from 'node:crypto'
import { readFileSync, existsSync, writeFileSync, mkdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { BROKEN_CORPORA, CLEAN_CORPORA } from './broken_reading'
import { PROSE_CHECKS } from './prose_checks'
import type { MetricSpec, MetricStatus } from './metrics'

const __dirname = dirname(fileURLToPath(import.meta.url))

/**
 * Sources whose bytes the banked proof is valid FOR.
 *
 * FIX for the PR #1501 REFUTED finding: `instrumentation.ts` was missing.
 * `browser_lane.ts` only READS counters off `Dd1Recording` — the actual
 * detector logic (the rAF loop, `SETTLED_DRIFT_TOLERANCE_PX`, the caret
 * invariant, the committed-block mutation counter) lives in
 * `instrumentation.ts`'s `recorderSource()`. Without it in this list, editing
 * `instrumentation.ts` to neuter a detector left the banked receipt's hash
 * unchanged, so a detector demonstrated incapable of failing could still mint
 * a PASS off a stale receipt — the exact §N.8 defect this gate exists to
 * prevent. `index.ts` is included too: it owns the raw→gated status mapping
 * for all 13 checks (`applyRedProofGate` call sites, `record()`), so a defect
 * there would also silently mint PASSes the receipt never proved.
 */
const DETECTOR_SOURCES = [
  join(__dirname, 'prose_checks.ts'),
  join(__dirname, 'broken_reading.ts'),
  join(__dirname, 'browser_lane.ts'),
  join(__dirname, 'instrumentation.ts'),
  join(__dirname, 'metrics.ts'),
  join(__dirname, 'index.ts'),
]

export interface RedProofEntry {
  check: string
  red_fired: boolean
  /** Verbatim findings the check produced against the broken corpus. */
  red_findings: string[]
  green_clean: boolean
  green_findings: string[]
  note?: string
}

export interface RedProofReceipt {
  generated_at: string
  detector_hash: string
  target: string | null
  proofs: Record<string, RedProofEntry>
}

export function detectorHash(): string {
  const h = createHash('sha256')
  for (const f of DETECTOR_SOURCES) {
    h.update(f.split('/').pop() ?? f)
    h.update(existsSync(f) ? readFileSync(f) : Buffer.from('<absent>'))
  }
  return h.digest('hex')
}

export function receiptPath(outDir: string): string {
  return join(outDir, 'dd1_red_proof_receipt.json')
}

export function loadReceipt(outDir: string): RedProofReceipt | null {
  const p = receiptPath(outDir)
  if (!existsSync(p)) return null
  try {
    return JSON.parse(readFileSync(p, 'utf8')) as RedProofReceipt
  } catch {
    return null
  }
}

export function saveReceipt(outDir: string, receipt: RedProofReceipt): string {
  mkdirSync(outDir, { recursive: true })
  const p = receiptPath(outDir)
  writeFileSync(p, JSON.stringify(receipt, null, 2))
  return p
}

/**
 * Run the PROSE-lane red-then-green proof. Returns one entry per prose check,
 * keyed by the check's `redProofKey`.
 *
 * Browser-lane and fixture-lane proofs are produced by their own lanes and
 * merged into the same receipt — see `browser_lane.ts` (seeded live-DOM
 * violations) and `index.ts` (the fixture suite's own
 * `npm run pariprashna:selftest`, which IS the repo's automated red-then-green
 * runner for the edge-state gates).
 */
export function runProseRedProof(
  specs: readonly MetricSpec[],
  log: (s: string) => void,
): Record<string, RedProofEntry> {
  const out: Record<string, RedProofEntry> = {}
  for (const spec of specs) {
    if (spec.lane !== 'prose' || !spec.redProofKey) continue
    const check = PROSE_CHECKS[spec.id]
    if (!check) continue

    const broken = BROKEN_CORPORA[spec.id]
    const clean = CLEAN_CORPORA[spec.id]
    if (!broken || !clean) {
      out[spec.redProofKey] = {
        check: spec.id,
        red_fired: false,
        red_findings: [],
        green_clean: false,
        green_findings: [],
        note: 'no broken/clean corpus registered for this check',
      }
      continue
    }

    const red = check(broken)
    const green = check(clean)

    log('')
    log(`── RED PROOF · ${spec.id} (${spec.redProofKey}) ─────────────────────────`)
    log(`   fed:      deliberately broken corpus (${broken.map((b) => b.label).join(', ')})`)
    log(`   observed: ${red.ok ? 'PASS  ← DETECTOR DID NOT FIRE — this check cannot report false' : 'FAIL  ← detector fired, as required'}`)
    for (const f of red.findings) log(`     · ${f}`)
    log(`   then fed: clean counterpart (${clean.map((c) => c.label).join(', ')})`)
    log(`   observed: ${green.ok ? 'PASS  ← green counterpart clean, as required' : 'FAIL  ← detector fires on clean prose too'}`)
    for (const f of green.findings) log(`     · ${f}`)

    out[spec.redProofKey] = {
      check: spec.id,
      red_fired: !red.ok,
      red_findings: red.findings,
      green_clean: green.ok,
      green_findings: green.findings,
    }
  }
  return out
}

/**
 * The gate itself. Returns the status the battery may actually report, plus
 * the reason when it was downgraded.
 */
export function applyRedProofGate(
  raw: MetricStatus,
  spec: MetricSpec,
  receipt: RedProofReceipt | null,
): { status: MetricStatus; gateNote: string | null } {
  if (raw === 'FAIL') return { status: 'FAIL', gateNote: null } // never suppressed
  if (raw === 'NOT_IMPLEMENTED') return { status: 'NOT_IMPLEMENTED', gateNote: null }

  if (!spec.redProofKey) {
    return {
      status: 'NOT_IMPLEMENTED',
      gateNote: 'no red proof is possible for this metric as defined — see falsifier',
    }
  }
  if (!receipt) {
    return { status: 'NOT_IMPLEMENTED', gateNote: 'no red-proof receipt banked — run with --red-proof first' }
  }
  if (receipt.detector_hash !== detectorHash()) {
    return {
      status: 'NOT_IMPLEMENTED',
      gateNote: `red-proof receipt is STALE (banked for detector_hash ${receipt.detector_hash.slice(0, 12)}…, current ${detectorHash().slice(0, 12)}…) — re-run --red-proof`,
    }
  }
  const entry = receipt.proofs[spec.redProofKey]
  if (!entry) {
    return { status: 'NOT_IMPLEMENTED', gateNote: `no red-proof entry for key '${spec.redProofKey}'` }
  }
  if (!entry.red_fired) {
    return {
      status: 'NOT_IMPLEMENTED',
      gateNote: `detector never demonstrated capable of failing (red_fired=false${entry.note ? `; ${entry.note}` : ''}) — §N.8: this signal is null, not green`,
    }
  }
  if (!entry.green_clean) {
    return {
      status: 'NOT_IMPLEMENTED',
      gateNote: 'detector fires on the clean counterpart too — it does not discriminate, so its green means nothing',
    }
  }
  return { status: 'PASS', gateNote: null }
}
