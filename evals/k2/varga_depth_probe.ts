#!/usr/bin/env tsx
/**
 * evals/k2/varga_depth_probe.ts — Lane K2 item 5 (EL-06).
 *
 * Checks whether a response actually engages the divisional-chart (varga) depth appropriate to
 * its domain — not just D1 — per `ELEVATION_REGISTER_v1_0.md` EL-06 ("varga-level depth
 * specifically absent from answers ... unless demanded"). D1-only answers on a domain whose
 * classical practice REQUIRES a specific varga (wealth needs D2/D11; career needs D10; marriage
 * needs D9; etc.) are the exact EL-01/EL-06 under-consumption pattern.
 *
 * Ground truth for "which vargas this domain requires" is sourced from, in priority order:
 *   1. Ω8's REGENERATED_FLOORS_v1_0.json (`floor_vargas` per domain) when present in the
 *      capability_map directory — this probe was built explicitly to be "reusable against Ω8's
 *      regenerated floors" (Lane K2 brief item 5) and reads that file with zero code changes
 *      once it lands in this branch (Ω8 merged into `elev/gamma` after this lane's branch
 *      point — see the fallback note below).
 *   2. A documented DEFAULT_DOMAIN_VARGAS fallback (mirroring the sealed evaluator harness's own
 *      required_concepts lists for wealth/career, cross-checked against Ω8's actual
 *      REGENERATED_FLOORS_v1_0.json content at authoring time so the fallback and the eventual
 *      live file agree) — so the probe is fully runnable today, before that merge lands.
 *
 * Usage:
 *   npx tsx evals/k2/varga_depth_probe.ts <transcript.json> <domain>
 */
import { existsSync, readFileSync } from 'fs'
import { join } from 'path'
import { CAPABILITY_MAP_DIR, loadTranscript } from './transcript_utils.js'

// ─────────────────────────────────────────────────────────────────────────────
// Ground truth
// ─────────────────────────────────────────────────────────────────────────────

/** Fallback floor_vargas per domain — mirrors SEALED_EVALUATOR_HARNESS_v1_0.md §3's
 * required_concepts (divisional_D2/D11 for wealth, divisional_D10/D9 for career) plus the
 * universal D1+D9 foundation, cross-checked against Ω8's REGENERATED_FLOORS_v1_0.json at
 * authoring time (wealth: D1,D2,D9,D11 · career: D1,D9,D10 — identical to what Ω8 computed
 * mechanically from the TCI, so this fallback is not a guess, it is a frozen snapshot of it). */
export const DEFAULT_DOMAIN_VARGAS: Record<string, string[]> = {
  wealth: ['D1', 'D2', 'D9', 'D11'],
  career: ['D1', 'D9', 'D10'],
  marriage: ['D1', 'D9'],
  health: ['D1', 'D6', 'D9', 'D30'],
  spirituality: ['D1', 'D9', 'D20'],
  education: ['D1', 'D9', 'D24'],
  progeny: ['D1', 'D7', 'D9'],
}

/** Classical names + common transliteration spellings a served answer might use instead of the
 * bare "D9" code — a probe that only greps for "D9" would under-count real varga engagement. */
export const VARGA_NAMES: Record<string, string[]> = {
  D1: ['rāśi', 'rasi', 'rashi', 'birth chart', 'natal chart', 'lagna chart'],
  D2: ['hora', 'horā'],
  D3: ['drekkana', 'drekana', 'drekkāṇa'],
  D4: ['chaturthamsa', 'chaturthāṁśa'],
  D6: ['shashthamsa', 'ṣaṣṭhāṁśa', 'sashtamsa'],
  D7: ['saptamsa', 'saptāṁśa'],
  D9: ['navamsa', 'navāṁśa', 'navamsha'],
  D10: ['dasamsa', 'daśāṁśa', 'dashamsa'],
  D11: ['rudramsa', 'rudrāṁśa', 'ekadasamsa'],
  D12: ['dvadasamsa', 'dvādaśāṁśa'],
  D16: ['shodasamsa', 'ṣoḍaśāṁśa'],
  D20: ['vimsamsa', 'viṁśāṁśa'],
  D24: ['siddhamsa', 'siddhāṁśa', 'chaturvimsamsa'],
  D27: ['bhamsa', 'nakshatramsa', 'nakṣatrāṁśa'],
  D30: ['trimsamsa', 'triṁśāṁśa', 'trimshamsa'],
  D40: ['khavedamsa'],
  D45: ['akshavedamsa'],
  D60: ['shashtiamsa', 'ṣaṣṭyaṁśa'],
}

interface FloorsFile {
  domains: Array<{ domain: string; floor_vargas: string[] }>
}

/** Attempts to read Ω8's REGENERATED_FLOORS_v1_0.json; returns null (not the fallback) if the
 * file isn't present in this branch yet, so the caller can report which source was actually
 * used rather than silently blending the two. */
function tryLoadOmega8Floors(): FloorsFile | null {
  const path = join(CAPABILITY_MAP_DIR, 'REGENERATED_FLOORS_v1_0.json')
  if (!existsSync(path)) return null
  try {
    return JSON.parse(readFileSync(path, 'utf-8')) as FloorsFile
  } catch {
    return null
  }
}

export interface RequiredVargasResult {
  domain: string
  required_vargas: string[]
  source: 'omega8_regenerated_floors' | 'fallback_default'
}

export function requiredVargasFor(domain: string): RequiredVargasResult {
  const omega8 = tryLoadOmega8Floors()
  const fromOmega8 = omega8?.domains.find((d) => d.domain === domain)
  if (fromOmega8) {
    return { domain, required_vargas: fromOmega8.floor_vargas, source: 'omega8_regenerated_floors' }
  }
  return { domain, required_vargas: DEFAULT_DOMAIN_VARGAS[domain] ?? ['D1', 'D9'], source: 'fallback_default' }
}

// ─────────────────────────────────────────────────────────────────────────────
// Probe
// ─────────────────────────────────────────────────────────────────────────────

export interface VargaDepthResult {
  domain: string
  source: 'omega8_regenerated_floors' | 'fallback_default'
  required_vargas: string[]
  vargas_mentioned: string[]
  vargas_missing: string[]
  depth_score: number // mentioned / required, 0..1
  d1_only: boolean // the specific EL-06 failure shape: only the base chart engaged, no divisional
}

function textMentionsVarga(text: string, code: string): boolean {
  const lower = text.toLowerCase()
  const codePattern = new RegExp(`\\b${code}\\b`, 'i') // "D9", not "D90" or "AD9"
  if (codePattern.test(text)) return true
  const names = VARGA_NAMES[code] ?? []
  return names.some((n) => lower.includes(n.toLowerCase()))
}

export function probeVargaDepth(finalAnswer: string, domain: string): VargaDepthResult {
  const { required_vargas, source } = requiredVargasFor(domain)
  // D1 (the base rāśi chart) is implicit in ANY chart reading — a real answer never needs to
  // spell out "D1" to have engaged it, so it is auto-satisfied for depth_score purposes rather
  // than penalizing an otherwise varga-rich answer for not literally typing "D1"/"rashi". What
  // this probe actually tests (per EL-06) is whether depth BEYOND D1 was engaged.
  const vargas_mentioned = required_vargas.filter((v) => v === 'D1' || textMentionsVarga(finalAnswer, v))
  const vargas_missing = required_vargas.filter((v) => !vargas_mentioned.includes(v))
  const nonD1Required = required_vargas.filter((v) => v !== 'D1')
  const nonD1Mentioned = vargas_mentioned.filter((v) => v !== 'D1')
  return {
    domain,
    source,
    required_vargas,
    vargas_mentioned,
    vargas_missing,
    depth_score: required_vargas.length > 0 ? vargas_mentioned.length / required_vargas.length : 0,
    d1_only: nonD1Required.length > 0 && nonD1Mentioned.length === 0,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────

function isMain(): boolean {
  return process.argv[1] != null && import.meta.url === `file://${process.argv[1]}`
}

if (isMain()) {
  const [transcriptPath, domain] = process.argv.slice(2)
  if (!transcriptPath || !domain) {
    console.error('Usage: npx tsx evals/k2/varga_depth_probe.ts <transcript.json> <domain>')
    process.exit(1)
  }
  const transcript = loadTranscript(transcriptPath)
  const result = probeVargaDepth(transcript.final_answer, domain)
  console.log(JSON.stringify(result, null, 2))
  if (result.d1_only) {
    console.warn(`\nEL-06 FLAG: ${domain} answer is D1-only — no divisional-chart depth engaged.`)
  }
}
