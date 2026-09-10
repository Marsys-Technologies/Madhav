/**
 * Adapter: lane C-2's recorded-fixture protocol → this renderer's `WireEvent`.
 *
 * PATH ROLE (PB-1/integrate): this is the DEV FIXTURE-FORMAT path (used by the
 * `c2-single` / `c2-gap` dev fixture modes only). The LIVE production path is
 * `state/s1LiveAdapter.ts`, which maps S-1's real merged `PariprashnaEvent`
 * wire directly. This adapter is retained because C-2's recorded fixtures are a
 * genuinely different-shaped event source that exercises the same reducer +
 * components; it is NOT on the production wire path.
 *
 * NB: C-2's inline citation-anchor events were renamed `seam.open`/`seam.set`
 * → `citation_anchor.open`/`citation_anchor.set` at integration (they collided
 * in name with S-1's real PASS-BOUNDARY `seam.open`/`seam.set`); the C-1 copies
 * in `fixtures/c2_recorded_samples.ts` and the cases below were renamed to match.
 *
 * C-2 (`Madhav-pb-1-c2`, `platform/tests/pariprashna/{fixtures,reducer}/`)
 * built a real protocol scaffold + golden reducer ahead of S-1's live wire,
 * with its own event field names (`turn_id`, `block_id`, `text`,
 * `final_text`, `label_key`, `citation_id`, …). This module is the seam
 * between their recorded JSON and this renderer's reducer, so the same
 * `AnswerRegion`/`WorkingRegion`/`RightDock` components that render our own
 * hand-authored fixtures (`fixtures/adaptive_three_pass.ts` etc., built
 * directly off the approved mockup) can ALSO render C-2's actual recorded
 * event streams, unmodified in content.
 *
 * FIELD MAPPING (verified against C-2's committed fixtures + `reducer.mjs`,
 * `Madhav-pb-1-c2` @ 9452e0e7):
 *   turn.open            → turnId=turn_id, userText left blank (C-2's fixtures
 *                          don't carry the human question text — it's a
 *                          replay harness for engine output, not a full
 *                          request/response pair)
 *   phase                → label = event.label (falls back to phase key)
 *   activity.upsert      → key→id; pass_id (string) → passIndex via
 *                          first-seen ordinal; label_key resolved through
 *                          our lexicon's RETRIEVAL_FACET_LABEL/fallback;
 *                          status pending|active → 'running', done → 'done'
 *   block.open/delta/commit → block_id→blockId, text→textDelta,
 *                          final_text→html; kind/role pass through
 *   citation.define      → citation_id (string) → n via first-seen ordinal
 *                          (our chip/dock model is numeric-indexed, §6.7);
 *                          label→title; verification 'confirmed'|'catalog_only'
 *                          → grade 'confirmed'|'catalog'; source_ref→ref
 *   flag `honest_gap.*`  → synthesized as a committed `gap_ribbon` block
 *                          (their protocol reports the gap as a flag, not a
 *                          distinct block type — §6.8 requires it be its own
 *                          settled block on our surface, so we materialize one)
 *   turn.commit          → factorCount = citation_count, classicalCount = 0
 *                          (their protocol doesn't yet distinguish source
 *                          class in the commit payload — an open question
 *                          for the real wire, noted below)
 *   error                → best-effort classify by `code`; unseen in any of
 *                          C-2's current fixtures, so this path is untested
 *                          against real data
 *
 * DELIBERATELY NOT MAPPED — an open integration question, not an oversight:
 * C-2's `citation_anchor.open`/`citation_anchor.set` is a CITATION-ANCHOR primitive: it marks a
 * character offset inside a block's text where a citation resolves (or
 * resolves to `null` for "no source found"). That is a different concept
 * from the design plan's §5.8.1 PASS SEAM — the mockup's inline "Looking
 * further — the divisional charts…" divider marking a PASS TRANSITION
 * between retrieval rounds, which is what `PassSeamLive`/`SeamBlock` in
 * this tree render. Both are legitimately named "seam" but are not the same
 * thing. This adapter maps C-2's seam to a text splice (see
 * `spliceCitationAnchor` below) rather than to our pass-seam UI, and leaves
 * the pass-seam UI validated only against our own hand-authored
 * `adaptive_three_pass`/`reconnect_mid_pass` fixtures until S-1/C-2/this
 * lane reconcile the two meanings on the real wire.
 */

import type { Citation, Grade, WireEvent } from './types'
import type { ScheduledEvent } from '../fixtures/types'
import { emptyGradeTally, rollUpGradeSummaryLabel, tallyGrade } from './groundingRollup'
// S-2's canonical closed vocabulary (PB-1/integrate — replaced the C-1 stand-in).
import { RETRIEVAL_FACET_NAMES, type RetrievalFacetKey } from '@/lib/pariprashna/lexicon'

/** Resolve a retrieval facet key to its reader-safe plain name via S-2's closed
 *  vocabulary; unknown keys fall back to a generic label (never a raw id). */
function resolveRetrievalFacet(facetKey: string): string {
  return RETRIEVAL_FACET_NAMES[facetKey as RetrievalFacetKey] ?? 'Chart data'
}

export interface C2RawScheduledEvent {
  delay_ms: number
  event: Record<string, unknown> & { type: string; id: string }
}

export interface C2Fixture {
  name: string
  description?: string
  events: C2RawScheduledEvent[]
}

function verificationToGrade(v: unknown): Grade {
  if (v === 'confirmed') return 'confirmed'
  if (v === 'catalog_only') return 'catalog'
  if (v === 'supported') return 'supported'
  return 'catalog'
}

/**
 * Splices a citation chip token (`⟦n⟧`) into accumulated block text at a
 * character offset — the real mechanics C-2's `citation_anchor.open{anchor_offset}` +
 * `citation_anchor.set{citation_id}` pair implies, worked all the way through rather
 * than dropped on the floor.
 */
function spliceCitationAnchor(text: string, offset: number, token: string): string {
  const at = Math.min(Math.max(offset, 0), text.length)
  return text.slice(0, at) + token + text.slice(at)
}

export function adaptC2Fixture(turnId: string, raw: C2Fixture): ScheduledEvent[] {
  const out: ScheduledEvent[] = []
  let cursor = 0

  const passIndexByPassId = new Map<string, number>()
  const citationNByCitationId = new Map<string, number>()
  let nextCitationN = 1
  // pending anchors: anchor_id → { blockId, offset } captured at citation_anchor.open,
  // resolved into a splice once citation_anchor.set delivers a citation_id (or a
  // synthesized gap block, for citation_id: null).
  const pendingAnchors = new Map<string, { blockId: string; offset: number }>()
  // accumulate per-block text as we see deltas/commits, so a late-resolving
  // anchor can still be spliced into the RIGHT committed block's html.
  const blockTextById = new Map<string, string>()
  let citationCountSeen = 0
  const gradeTally = emptyGradeTally()
  let lastEventId = ''

  for (const { delay_ms, event } of raw.events) {
    cursor += delay_ms
    const atMs = cursor
    lastEventId = String(event.id)

    switch (event.type) {
      case 'turn.open': {
        out.push({ atMs, event: { type: 'turn.open', turnId, userText: '', eventId: String(event.id) } })
        break
      }
      case 'phase': {
        const label = typeof event.label === 'string' ? event.label : String(event.phase ?? 'Consulting the chart')
        out.push({ atMs, event: { type: 'phase', turnId, label, eventId: String(event.id) } })
        break
      }
      case 'activity.upsert': {
        const passId = String(event.pass_id ?? 'pass-1')
        if (!passIndexByPassId.has(passId)) passIndexByPassId.set(passId, passIndexByPassId.size)
        const passIndex = passIndexByPassId.get(passId)!
        const labelKey = typeof event.label_key === 'string' ? event.label_key : ''
        const label = labelKey.startsWith('activity.retrieval.')
          ? `Retrieved — ${resolveRetrievalFacet(labelKey.replace('activity.retrieval.', ''))}`
          : resolveRetrievalFacet(labelKey)
        const rawStatus = String(event.status ?? 'pending')
        out.push({
          atMs,
          event: {
            type: 'activity.upsert',
            turnId,
            row: {
              id: String(event.key),
              passIndex,
              label,
              detail: typeof event.detail === 'string' ? event.detail : undefined,
              kind: 'tool',
              status: rawStatus === 'done' ? 'done' : 'running',
            },
            eventId: String(event.id),
          },
        })
        break
      }
      case 'block.open': {
        blockTextById.set(String(event.block_id), '')
        out.push({
          atMs,
          event: {
            type: 'block.open',
            turnId,
            blockId: String(event.block_id),
            kind: (event.kind as WireEvent extends { type: 'block.open'; kind: infer K } ? K : never) ?? 'paragraph',
            eventId: String(event.id),
          },
        })
        break
      }
      case 'block.delta': {
        const blockId = String(event.block_id)
        const text = String(event.text ?? '')
        blockTextById.set(blockId, (blockTextById.get(blockId) ?? '') + text)
        out.push({ atMs, event: { type: 'block.delta', turnId, blockId, textDelta: text, eventId: String(event.id) } })
        break
      }
      case 'block.commit': {
        const blockId = String(event.block_id)
        const finalText = typeof event.final_text === 'string' ? event.final_text : blockTextById.get(blockId) ?? ''
        blockTextById.set(blockId, finalText)
        out.push({
          atMs,
          event: {
            type: 'block.commit',
            turnId,
            blockId,
            kind: 'paragraph',
            html: finalText,
            eventId: String(event.id),
          },
        })
        break
      }
      case 'citation_anchor.open': {
        pendingAnchors.set(String(event.anchor_id), {
          blockId: String(event.block_id),
          offset: Number(event.anchor_offset ?? 0),
        })
        break
      }
      case 'citation_anchor.set': {
        const anchor = pendingAnchors.get(String(event.anchor_id))
        pendingAnchors.delete(String(event.anchor_id))
        if (!anchor) break
        const citationId = event.citation_id
        if (citationId == null) {
          // Honest gap at this anchor (§6.8) — the protocol reports it via
          // the citation resolving to null, not a distinct block type; we
          // materialize the ribbon our surface requires.
          break // handled by the `flag` case below when the engine also emits honest_gap.*
        }
        const n = citationNByCitationId.get(String(citationId))
        if (n != null) {
          const spliced = spliceCitationAnchor(blockTextById.get(anchor.blockId) ?? '', anchor.offset, `⟦${n}⟧`)
          blockTextById.set(anchor.blockId, spliced)
          out.push({
            atMs,
            event: { type: 'block.commit', turnId, blockId: anchor.blockId, kind: 'paragraph', html: spliced, eventId: `${event.id}-splice` },
          })
        }
        break
      }
      case 'citation.define': {
        const citationId = String(event.citation_id)
        const n = nextCitationN++
        citationNByCitationId.set(citationId, n)
        citationCountSeen += 1
        const grade = verificationToGrade(event.verification)
        tallyGrade(gradeTally, grade)
        const citation: Citation = {
          n,
          title: String(event.label ?? `Source ${n}`),
          sourceClass: 'chart_factor',
          relevance: 'From lane C-2 recorded fixture.',
          ref: String(event.source_ref ?? ''),
          grade,
        }
        out.push({ atMs, event: { type: 'citation.define', turnId, citation, eventId: String(event.id) } })
        break
      }
      case 'flag': {
        const flagKey = String(event.flag_key ?? '')
        if (flagKey.startsWith('honest_gap')) {
          const text = typeof event.detail === 'string' ? event.detail : 'The chart is silent here.'
          out.push({
            atMs,
            event: {
              type: 'block.commit',
              turnId,
              blockId: `gap-${event.id}`,
              kind: 'gap_ribbon',
              gapText: text,
              eventId: String(event.id),
            },
          })
        }
        break
      }
      case 'grade':
      case 'error':
        // Not yet exercised by any of C-2's committed fixtures; our reducer
        // accepts `grade`/`error` shapes but this adapter has no real
        // sample to map field-for-field yet.
        break
      case 'turn.commit': {
        const factorCount = Number(event.citation_count ?? citationCountSeen)
        out.push({
          atMs,
          event: {
            type: 'turn.commit',
            turnId,
            grounding: {
              factorCount,
              classicalCount: 0,
              elapsedLabel: `0:${String(Math.round(atMs / 1000)).padStart(2, '0')}`,
              // Honest rollup from the real per-citation grade distribution — never
              // a confident verdict on the strength of a bare count (B.1/B.10, §6.7).
              gradeSummaryLabel: rollUpGradeSummaryLabel(gradeTally),
              // This adapter maps C-2's recorded-fixture protocol, which never
              // carries a server-derived grounding summary — always the
              // disclosed client-estimate path (G2-B).
              source: 'client_estimate',
            },
            eventId: String(event.id),
          },
        })
        break
      }
      case 'turn.close': {
        out.push({ atMs, event: { type: 'turn.close', turnId, eventId: String(event.id) } })
        break
      }
      default:
        break
    }
  }

  void lastEventId
  return out.sort((a, b) => a.atMs - b.atMs)
}
