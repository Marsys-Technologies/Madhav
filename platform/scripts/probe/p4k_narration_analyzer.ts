#!/usr/bin/env npx tsx
/**
 * p4k_narration_analyzer.ts — P4-K narration audit, analyzer half.
 *
 * Reads a `p4k_sequence_driver.ts` manifest (six chained `ask.ts` transcripts, one
 * real reader thread) and asks the questions CLAUDE.md §N.6/§N.7/§N.8 name:
 * does the narration stay faithful within a turn, and does it stay CONSISTENT
 * across the six-view sequence a reader actually moves through?
 *
 * Every check below is one of two honestly-labeled kinds — never blurred:
 *
 *   DETERMINISTIC — a mechanical, re-runnable test against the transcript's own
 *   structured fields (SSE event types, regex over reader-visible text). A
 *   deterministic FAIL is a real defect, not a judgment call.
 *
 *   JUDGMENT — a question this harness can pose and hand evidence for, but
 *   cannot itself answer, because it requires semantic understanding of free
 *   text or comparison against the chart's true underlying facts. These are
 *   NEVER scored PASS/FAIL by this script — they are always emitted as open
 *   prompts for the CONDUCTOR/VERIFIER/an LLM judge to close. Dressing one of
 *   these as a deterministic PASS is exactly the defect class §N.6/§N.7 name.
 *
 * §N.8 (Earned-Signal Principle): every deterministic check here has a real
 * detector — see p4k_narration_analyzer.selftest fixtures under
 * `fixtures/p4k/{clean,broken}/` for a transcript this script is DEMONSTRATED
 * to fail before its first green counts. Run `--self-test` to reproduce.
 *
 * Usage:
 *   npx tsx p4k_narration_analyzer.ts --manifest <path/to/manifest.json>
 *   npx tsx p4k_narration_analyzer.ts --self-test
 *
 * Writes a JSON findings report next to the manifest (or, in --self-test mode,
 * under fixtures/p4k/<clean|broken>/report.json) and prints a human-readable
 * summary to stdout. Exit code 0 iff there are zero `fail`-severity
 * deterministic findings. `warn`/`info` findings and ALL judgment items never
 * affect the exit code — they are surfaced, not gated on.
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const FIXTURES_DIR = join(__dirname, 'fixtures', 'p4k')

// ── Transcript + manifest shapes (mirrors ask.ts's writeResult() / driver's Manifest) ──

/** The wire event's raw JSON payload. Fields are a union of everything the checks
 *  below read across the several SSE event types (`block.commit`, `flag`, `grade`,
 *  `citation.define`) — see `platform/src/lib/pariprashna/protocol/events.ts` for
 *  the full per-type schemas this is a reader-side subset of. All optional because
 *  which fields are present depends on `type`. */
interface AskEventRaw {
  role?: string
  text?: string
  code?: string
  level?: 'info' | 'warn' | 'error'
  detail?: string
  subject?: string
  grade?: string
  signal_id?: string
}

interface AskEvent {
  type: string
  raw: AskEventRaw
  receivedAtMs: number
}

interface AskBlock {
  blockId: string
  kind: string | null
  role: string | null
}

interface AskTranscript {
  turn_id: string
  question: string
  chart_id: string
  conversation_id: string | null
  partial: boolean
  terminal_status: string | null
  blocks: AskBlock[]
  prose: string
  events: AskEvent[]
}

interface ManifestTurn {
  view: string
  primitive_id: string
  live_tool: string
  question: string
  transcript_path: string
  conversation_id: string | null
  partial: boolean
  terminal_status: string | null
  ask_exit_ok: boolean
}

interface Manifest {
  sequence_id: string
  service_url: string
  created_at: string
  turns: ManifestTurn[]
}

// ── Findings ─────────────────────────────────────────────────────────────────

type Severity = 'fail' | 'warn' | 'info'

interface Finding {
  id: string
  check_id: string
  severity: Severity
  view: string | null
  message: string
  evidence: Record<string, unknown>
}

interface JudgmentItem {
  id: string
  prompt: string
  applies_to_views: string[]
}

interface Report {
  sequence_id: string | null
  generated_at: string
  deterministic_findings: Finding[]
  judgment_items: JudgmentItem[]
  result: 'PASS' | 'FAIL'
}

let findingSeq = 0
function finding(check_id: string, severity: Severity, view: string | null, message: string, evidence: Record<string, unknown> = {}): Finding {
  findingSeq += 1
  return { id: `${check_id}-${String(findingSeq).padStart(3, '0')}`, check_id, severity, view, message, evidence }
}

// ── D1 — honest-verdict-non-empty (§N.6 item 3 / §N.7 item 6) ──────────────────
// A turn that completed ('ok', not partial) must carry at least one committed
// block with role === 'verdict' and non-empty text. A silently-empty verdict
// layer standing in for an honest "I don't know" is exactly the defect class
// these sections name.
function checkD1_verdictNonEmpty(view: string, t: AskTranscript): Finding[] {
  const out: Finding[] = []
  if (t.partial || t.terminal_status !== 'ok') return out // an honestly-partial turn is not this check's business
  const verdictBlocks = t.events.filter((e) => e.type === 'block.commit' && e.raw?.role === 'verdict')
  const nonEmpty = verdictBlocks.filter((e) => typeof e.raw?.text === 'string' && e.raw.text.trim().length > 0)
  if (verdictBlocks.length === 0) {
    out.push(finding('D1', 'fail', view, 'Turn completed ok but committed zero verdict-role blocks — an honest empty result must say so via a flag, not silently omit the verdict layer.', { terminal_status: t.terminal_status }))
  } else if (nonEmpty.length === 0) {
    out.push(finding('D1', 'fail', view, 'Turn committed verdict-role block(s) but every one is empty text.', { verdict_block_count: verdictBlocks.length }))
  }
  return out
}

// ── D2 — independent taxonomy-leak scan (§N.6 "no internal taxonomy reaching the reader") ──
// Deliberately does NOT reuse register_leak_lint.ts's own regex table — an
// independent detector, so a bug/regression in that lint's OWN implementation
// is not invisible to the one thing meant to catch it (§N.8: a check that only
// ever re-asks the system under test whether it is honest is not a check).
const LEAK_PATTERNS: Array<{ name: string; re: RegExp }> = [
  { name: 'asset_id_prefix', re: /\b(?:bo|ga|ka|ph|mi|bg)_[a-z][a-z_]{2,}\b/g },
  { name: 'table_prefix', re: /\b(?:bodha|mimamsa|kala|phala|ganita|brahma|chart|asset)_[a-z][a-z_]{2,}\b/g },
  { name: 'primitive_id', re: /\b(?:now_read|ahead_read|elect_read|story_read|priority_read|explain_read|upaya_read|ritual_read)\b/g },
  { name: 'live_tool_name', re: /\bkala_(?:now|ahead|elect|story|priority|explain|upaya|ritual)_get\b/g },
  { name: 'verdict_tier_literal', re: /\b(?:structural_prior|calibrated_provisional)\b/g },
  { name: 'register_acronym', re: /\b(?:MSR|UCN|CGM|CDLM)\b/g },
]

function checkD2_taxonomyLeak(view: string, t: AskTranscript): Finding[] {
  const out: Finding[] = []
  const readerText = t.prose + '\n' + t.events.filter((e) => e.type === 'block.commit' && typeof e.raw?.text === 'string').map((e) => e.raw.text).join('\n')
  for (const pat of LEAK_PATTERNS) {
    const matches = [...readerText.matchAll(pat.re)].map((m) => m[0])
    if (matches.length > 0) {
      out.push(finding('D2', 'fail', view, `Reader-visible text contains ${pat.name} token(s) that should never reach a reader.`, { pattern: pat.name, matches: [...new Set(matches)].slice(0, 10) }))
    }
  }
  return out
}

// ── D3 — cross-view current-dasha-lord consistency ─────────────────────────────
// The one concrete, mechanically-checkable instance of "does view N contradict
// view N-1?": NOW/AHEAD/PRIORITIZE/STORY all compile from the SAME current
// mahadasha state (registry_data.ts: now_read/ahead_read/priority_read are
// compiled together into every domain deepdive). If two of them name a
// DIFFERENT planet as the current mahadasha lord, that is a real, checkable
// contradiction. This is a TEMPLATE for one fact class — the general "any two
// views may disagree about any fact" question remains a judgment item (see J5)
// because it requires semantic fact extraction this regex approach cannot do.
const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
const CURRENT_DASHA_RE = new RegExp(
  `(?:currently|right now|at present)[^.]{0,80}?(?:Mah[āa]?da[śs]h?[āa]|Mahadasha|da[śs]h?[āa])\\s+of\\s+(${PLANETS.join('|')})` +
    `|(?:Mah[āa]?da[śs]h?[āa]|Mahadasha|da[śs]h?[āa])\\s+of\\s+(${PLANETS.join('|')})[^.]{0,80}?(?:currently|right now|at present)`,
  'gi',
)

function extractCurrentDashaLords(text: string): string[] {
  const out: string[] = []
  for (const m of text.matchAll(CURRENT_DASHA_RE)) {
    const lord = m[1] ?? m[2]
    if (lord) out.push(lord)
  }
  return out
}

function checkD3_crossViewDashaConsistency(turnsByView: Map<string, AskTranscript>): Finding[] {
  const relevant: Array<{ view: string; lords: string[] }> = []
  for (const view of ['NOW', 'AHEAD', 'PRIORITIZE', 'STORY']) {
    const t = turnsByView.get(view)
    if (!t) continue
    const lords = extractCurrentDashaLords(t.prose)
    if (lords.length > 0) relevant.push({ view, lords })
  }
  const allLords = new Set(relevant.flatMap((r) => r.lords))
  if (relevant.length < 2) {
    return [finding('D3', 'info', null, 'Insufficient signal to check cross-view current-dasha-lord consistency (fewer than two views made an extractable "current dasha lord" claim). Not a pass — deferred to judgment (see J5).', { views_with_signal: relevant.map((r) => r.view) })]
  }
  if (allLords.size > 1) {
    return [finding('D3', 'fail', null, 'Cross-view contradiction: views disagree about the current mahadasha lord.', { by_view: Object.fromEntries(relevant.map((r) => [r.view, r.lords])) })]
  }
  return [finding('D3', 'info', null, 'Cross-view current-dasha-lord mentions consistent across all views that made an extractable claim.', { lord: [...allLords][0], views_checked: relevant.map((r) => r.view) })]
}

// ── D4 — server self-reported flag surfacing (labeled: NOT independent) ────────
function checkD4_serverFlags(view: string, t: AskTranscript): Finding[] {
  const out: Finding[] = []
  for (const e of t.events.filter((e) => e.type === 'flag')) {
    const level: string = e.raw?.level ?? 'info'
    const sev: Severity = level === 'error' ? 'fail' : level === 'warn' ? 'warn' : 'info'
    out.push(finding('D4', sev, view, `Server self-reported flag (NOT an independent check — surfacing the system's own signal): code=${e.raw?.code}`, { code: e.raw?.code, level, detail: e.raw?.detail }))
  }
  return out
}

// ── D5 — server self-reported citation_gate grade presence (§N.8: absence of a
// detector is itself a finding, not a silent pass) ─────────────────────────────
function checkD5_citationGate(view: string, t: AskTranscript): Finding[] {
  if (t.partial || t.terminal_status !== 'ok') return []
  const gradeEvents = t.events.filter((e) => e.type === 'grade' && e.raw?.subject === 'citation_gate')
  if (gradeEvents.length === 0) {
    return [finding('D5', 'warn', view, 'No citation_gate grade event observed for a completed turn — either the gate did not run or this transcript does not carry its own detector output. Absence-of-detector is reported honestly, not silently passed.', {})]
  }
  const failing = gradeEvents.filter((e) => String(e.raw?.grade).toUpperCase() === 'FAIL')
  if (failing.length > 0) {
    return [finding('D5', 'fail', view, 'citation_gate reported FAIL (server self-report).', { grades: gradeEvents.map((e) => e.raw?.grade) })]
  }
  return [finding('D5', 'info', view, 'citation_gate reported non-failing (server self-report).', { grades: gradeEvents.map((e) => e.raw?.grade) })]
}

// ── D6 — EXPLAIN-hop signal_id overlap (proxy, not proof — WARN not FAIL) ──────
function checkD6_explainHop(turnsByView: Map<string, AskTranscript>): Finding[] {
  const now = turnsByView.get('NOW')
  const explain = turnsByView.get('EXPLAIN')
  if (!now || !explain) return [finding('D6', 'info', null, 'NOW and/or EXPLAIN turn missing from this sequence — skipped.', {})]
  const sigIds = (t: AskTranscript) => new Set(t.events.filter((e) => e.type === 'citation.define').map((e) => String(e.raw?.signal_id)))
  const nowSigs = sigIds(now)
  const explainSigs = sigIds(explain)
  const overlap = [...nowSigs].filter((s) => explainSigs.has(s))
  if (nowSigs.size === 0 || explainSigs.size === 0) {
    return [finding('D6', 'info', 'EXPLAIN', 'NOW and/or EXPLAIN cited no signals via citation.define — cannot check hop overlap mechanically.', { now_signal_count: nowSigs.size, explain_signal_count: explainSigs.size })]
  }
  if (overlap.length === 0) {
    return [finding('D6', 'warn', 'EXPLAIN', 'EXPLAIN turn cites no signal_id in common with the NOW turn it was asked to explain. This is a PROXY, not proof of a wrong explanation — a legitimate EXPLAIN could draw on adjacent material — so this is WARN, not FAIL; see J1 for the substantive judgment call.', { now_signals: [...nowSigs], explain_signals: [...explainSigs] })]
  }
  return [finding('D6', 'info', 'EXPLAIN', 'EXPLAIN turn shares at least one cited signal_id with the NOW turn.', { overlap })]
}

// ── Judgment items — always emitted, never scored ───────────────────────────────
function judgmentItems(): JudgmentItem[] {
  return [
    { id: 'J1', prompt: "Does the EXPLAIN turn's causal chain (promise -> confirmation -> activation -> trigger) actually and correctly explain the NOW claim it was asked about, in substance — not just citation-id overlap (see D6)?", applies_to_views: ['EXPLAIN'] },
    { id: 'J2', prompt: "Does any turn's grade/label/verdict read as an invented plausible default (the 'elevated'-on-missing-direction / '5.0'-on-zero-grade defect class, §N.7 item 6) rather than a genuinely computed value? Requires cross-referencing the chart's true underlying facts.", applies_to_views: ['NOW', 'AHEAD', 'PRIORITIZE', 'STORY', 'ELECT', 'EXPLAIN'] },
    { id: 'J3', prompt: 'Tone/register/valence consistency across the six views: does the same underlying life period or fact get narrated with a different emotional valence depending on which view frames it (e.g. NOW hedges positively, STORY frames the same period negatively)?', applies_to_views: ['NOW', 'AHEAD', 'PRIORITIZE', 'STORY', 'ELECT', 'EXPLAIN'] },
    { id: 'J4', prompt: 'Catalog-only vs. confirmed-finding flattening (§N.6 item 1): are any citations presented as confirmed classical findings when the underlying signal is actually a single-pass/catalog-only match? Requires cross-reference to source signal metadata beyond what the wire transcript exposes.', applies_to_views: ['NOW', 'AHEAD', 'PRIORITIZE', 'STORY', 'ELECT', 'EXPLAIN'] },
    { id: 'J5', prompt: 'General cross-view fact contradiction beyond the one tracked class (D3 covers ONLY "current mahadasha lord"). Any other fact pair — a planet\'s dignity, a house lord, a yoga\'s presence/absence — could contradict across two views and this harness does not mechanically catch it. Read all six transcripts side by side for other contradictions.', applies_to_views: ['NOW', 'AHEAD', 'PRIORITIZE', 'STORY', 'ELECT', 'EXPLAIN'] },
  ]
}

// ── Runner ───────────────────────────────────────────────────────────────────

function analyze(manifest: Manifest): Report {
  const turnsByView = new Map<string, AskTranscript>()
  const perViewTranscript: Array<{ view: string; t: AskTranscript }> = []
  for (const turn of manifest.turns) {
    const t = JSON.parse(readFileSync(turn.transcript_path, 'utf8')) as AskTranscript
    turnsByView.set(turn.view, t)
    perViewTranscript.push({ view: turn.view, t })
  }

  const findings: Finding[] = []
  for (const { view, t } of perViewTranscript) {
    findings.push(...checkD1_verdictNonEmpty(view, t))
    findings.push(...checkD2_taxonomyLeak(view, t))
    findings.push(...checkD4_serverFlags(view, t))
    findings.push(...checkD5_citationGate(view, t))
  }
  findings.push(...checkD3_crossViewDashaConsistency(turnsByView))
  findings.push(...checkD6_explainHop(turnsByView))

  const hasFail = findings.some((f) => f.severity === 'fail')
  return {
    sequence_id: manifest.sequence_id,
    generated_at: new Date().toISOString(),
    deterministic_findings: findings,
    judgment_items: judgmentItems(),
    result: hasFail ? 'FAIL' : 'PASS',
  }
}

function printReport(report: Report) {
  console.log('='.repeat(78))
  console.log(`P4-K NARRATION AUDIT — sequence ${report.sequence_id ?? '(fixture)'}`)
  console.log('='.repeat(78))
  console.log(`\nDETERMINISTIC FINDINGS (${report.deterministic_findings.length}):`)
  for (const f of report.deterministic_findings) {
    console.log(`  [${f.severity.toUpperCase()}] ${f.id} (${f.check_id}${f.view ? `, view=${f.view}` : ''}): ${f.message}`)
    if (Object.keys(f.evidence).length > 0) console.log(`      evidence: ${JSON.stringify(f.evidence)}`)
  }
  console.log(`\nJUDGMENT ITEMS (${report.judgment_items.length}) — NEVER auto-scored, hand to CONDUCTOR/VERIFIER/LLM judge:`)
  for (const j of report.judgment_items) {
    console.log(`  [${j.id}] (${j.applies_to_views.join(', ')}) ${j.prompt}`)
  }
  console.log(`\nRESULT: ${report.result}`)
  console.log('='.repeat(78))
}

function runSelfTest(): number {
  let overallOk = true
  for (const kind of ['broken', 'clean'] as const) {
    const dir = join(FIXTURES_DIR, kind)
    const manifestPath = join(dir, 'manifest.json')
    const manifest = JSON.parse(readFileSync(manifestPath, 'utf8')) as Manifest
    // Fixture manifests use paths relative to the fixture dir — resolve them.
    manifest.turns = manifest.turns.map((t) => ({ ...t, transcript_path: join(dir, t.transcript_path) }))
    const report = analyze(manifest)
    printReport(report)
    writeFileSync(join(dir, 'report.json'), JSON.stringify(report, null, 2))

    const expected = kind === 'broken' ? 'FAIL' : 'PASS'
    const gotIt = report.result === expected
    console.log(`\n[self-test] fixture=${kind} expected=${expected} got=${report.result} -> ${gotIt ? 'OK' : 'MISMATCH'}`)
    if (!gotIt) overallOk = false
  }
  console.log(overallOk ? '\n[p4k_narration_analyzer --self-test] PASS — analyzer demonstrated capable of both failing (broken fixture) and passing (clean fixture).' : '\n[p4k_narration_analyzer --self-test] FAIL — see MISMATCH above.')
  return overallOk ? 0 : 1
}

function parseArgs(argv: string[]): { manifest: string | null; selfTest: boolean } {
  let manifest: string | null = null
  let selfTest = false
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--manifest') manifest = argv[++i]
    else if (argv[i] === '--self-test') selfTest = true
  }
  return { manifest, selfTest }
}

function main(): number {
  const args = parseArgs(process.argv.slice(2))
  if (args.selfTest) return runSelfTest()
  if (!args.manifest) {
    console.error('Usage: npx tsx p4k_narration_analyzer.ts --manifest <path> | --self-test')
    return 2
  }
  const manifest = JSON.parse(readFileSync(args.manifest, 'utf8')) as Manifest
  const report = analyze(manifest)
  printReport(report)
  const outPath = join(dirname(args.manifest), 'report.json')
  writeFileSync(outPath, JSON.stringify(report, null, 2))
  console.error(`\n[p4k_narration_analyzer] wrote ${outPath}`)
  return report.result === 'PASS' ? 0 : 1
}

process.exit(main())
