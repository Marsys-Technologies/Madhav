/**
 * marker_parser.ts — Gate III.
 *
 * Parses inline ‹marker› tokens out of streamed synthesis prose:
 *   ‹reasoning›…‹/reasoning›
 *   ‹correction›YAML‹/correction›
 *   ‹sanskrit term="…" def="…" translit="…"›display‹/sanskrit›
 *   ‹out_of_domain reason="…"›‹/out_of_domain›
 *
 * The parser is incremental — given the accumulated text so far, it returns
 * (a) the visible prose (markers removed; Sanskrit markers replaced by their
 * display text), and (b) the structured payload events extracted so far.
 *
 * Idempotent: passing the same text twice yields the same outputs. The caller
 * re-parses on every text delta.
 */

import type {
  ReasoningStepEvent,
  CorrectionEvent,
  OutOfDomainEvent,
  SanskritTerm,
} from '@/types/sse_events'

// Use both unicode single guillemets (‹›) and the lookalikes (<<, >>) as
// safe fallbacks for models that emit ASCII approximations.
const OPEN = /[‹<]{1,2}/
const CLOSE = /[›>]{1,2}/

const REASONING_RX = /‹reasoning›([\s\S]*?)‹\/reasoning›/g
const CORRECTION_RX = /‹correction›([\s\S]*?)‹\/correction›/g
// Match both the full self-closing form (‹out_of_domain ...›‹/out_of_domain›)
// and the open-only form (‹out_of_domain ...›) — models often skip the closing tag.
const OUT_OF_DOMAIN_RX = /‹out_of_domain\s+reason="([^"]*)"\s*›(?:\s*‹\/out_of_domain›)?/g
const SANSKRIT_RX = /‹sanskrit\s+([^›]+)›([\s\S]*?)‹\/sanskrit›/g
const SANSKRIT_ATTR_RX = /(\w+)="([^"]*)"/g

export interface ParsedMarkers {
  /** Prose with all markers removed; Sanskrit spans replaced by display text. */
  visibleText: string
  reasoning: ReasoningStepEvent[]
  correction: CorrectionEvent | null
  sanskrit: SanskritTerm[]
  outOfDomain: OutOfDomainEvent | null
}

function parseYamlLikeCorrection(body: string): CorrectionEvent {
  // Minimal YAML-ish parsing — match `key: "value"` and `key: value` lines.
  const lines = body.split('\n')
  const out: Record<string, string> = {}
  for (const raw of lines) {
    const m = raw.match(/^\s*(\w+)\s*:\s*"?([^"]*)"?\s*$/)
    if (m) out[m[1]] = m[2].trim()
  }
  return {
    type: 'correction',
    original_claim: out.original ?? '',
    corrected_claim: out.corrected ?? '',
    classical_source: out.source || undefined,
  }
}

export function parseMarkers(text: string): ParsedMarkers {
  const reasoning: ReasoningStepEvent[] = []
  let correction: CorrectionEvent | null = null
  let outOfDomain: OutOfDomainEvent | null = null
  const sanskrit: SanskritTerm[] = []
  const seenTerms = new Set<string>()

  let visible = text

  // Reasoning — collect text, strip markers.
  visible = visible.replace(REASONING_RX, (_full, inner) => {
    const t = String(inner).trim()
    if (t) {
      reasoning.push({
        type: 'reasoning_step',
        phase: 'synthesis',
        text: t,
        timestamp: Date.now(),
      })
    }
    return ''
  })

  // Correction — keep only the first, strip all.
  visible = visible.replace(CORRECTION_RX, (_full, inner) => {
    if (!correction) correction = parseYamlLikeCorrection(String(inner))
    return ''
  })

  // Out-of-domain — keep only the first, strip all.
  visible = visible.replace(OUT_OF_DOMAIN_RX, (_full, reason) => {
    if (!outOfDomain) outOfDomain = { type: 'out_of_domain', reason: String(reason) }
    return ''
  })

  // Sanskrit — collect terms; replace span with display text in visible prose.
  visible = visible.replace(SANSKRIT_RX, (_full, attrs, display) => {
    const attrMap: Record<string, string> = {}
    let m: RegExpExecArray | null
    const rx = new RegExp(SANSKRIT_ATTR_RX)
    while ((m = rx.exec(String(attrs))) !== null) {
      attrMap[m[1]] = m[2]
    }
    const term = (attrMap.term ?? String(display)).trim()
    if (term && !seenTerms.has(term.toLowerCase())) {
      seenTerms.add(term.toLowerCase())
      sanskrit.push({
        term,
        definition: attrMap.def ?? '',
        transliteration: attrMap.translit || undefined,
      })
    }
    return String(display)
  })

  return {
    visibleText: visible,
    reasoning,
    correction,
    sanskrit,
    outOfDomain,
  }
}

/** True if the streamed text contains any open marker — useful for guards. */
export function hasAnyMarker(text: string): boolean {
  return (
    text.indexOf('‹reasoning›') >= 0 ||
    text.indexOf('‹correction›') >= 0 ||
    text.indexOf('‹sanskrit') >= 0 ||
    text.indexOf('‹out_of_domain') >= 0
  )
}

// Suppress eslint unused-export warnings from the regex sentinels above.
void OPEN
void CLOSE
