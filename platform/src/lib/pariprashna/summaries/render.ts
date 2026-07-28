/**
 * Paripraśna durable conversation summaries — PB-2 (SMṚTI) lane M-3 — rendering.
 *
 * Turns a run of canonical `message_parts` (M-1 schema) into the plain-text
 * input a `SummarizerWorker` folds into a summary, AND separately extracts the
 * citation lines that must survive VERBATIM regardless of what the LLM worker
 * does with them (see `appendCitationBlock`).
 *
 * Two hard rules enforced here, both named directly in the M-3 brief:
 *   1. `tool_call`/`tool_result` parts NEVER render as a raw internal tool
 *      name or a `'[multipart content]'`-style placeholder — they render as
 *      `"consulted ⟨reader label⟩ → ⟨result summary⟩"`, reusing PB-1 lane
 *      S-2's closed reader-facing lexicon (`resolveReaderLabel` /
 *      `FALLBACK_READER_LABEL`) exactly the way
 *      `src/app/api/pariprashna/route.ts`'s `resolveActivityLabel` already
 *      does for the live stream — this module mirrors that same resolution
 *      path rather than reinventing a second one.
 *   2. `citation` parts' `signal_id`/layer/snippet survive VERBATIM into the
 *      persisted summary text via a deterministic, LLM-independent append —
 *      see `appendCitationBlock`. Citation survival never depends on the LLM
 *      choosing to preserve them.
 */
import 'server-only'

import { getCapability } from '@/lib/retrieval/registry'
import { TOOL_NAME_TO_URI } from '@/lib/retrieval/registry/tool_name_bridge'
import { resolveReaderLabel, FALLBACK_READER_LABEL } from '@/lib/pariprashna/lexicon'
import type {
  CitationBody,
  TextBody,
  ToolCallBody,
  ToolResultBody,
} from '../store/schema'
import type { CanonicalTurn } from './types'

/** One citation line extracted from the summarized range, order-preserving. */
export interface CitationLine {
  index: number
  signal_id: string
  layer: string
  snippet: string
}

export interface RenderedTurns {
  /** Plain-text lines, joined, ready to hand to a `SummarizerWorker`. */
  text: string
  /** Every citation encountered in the summarized range, in original order. */
  citations: CitationLine[]
}

/**
 * Resolve a canonical `tool_call.body.tool_name` (already the reader-safe
 * name per M-1's schema.ts contract) to its reader-facing label — the SAME
 * resolution path `route.ts`'s `resolveActivityLabel` uses: legacy tool name
 * -> registry URI -> capability -> `resolveReaderLabel`. Never returns the raw
 * tool name; falls back to `FALLBACK_READER_LABEL` if unmapped, exactly like
 * the live stream does.
 */
export function resolveToolReaderLabel(toolName: string): string {
  const uri = toolName.startsWith('marsys://') ? toolName : TOOL_NAME_TO_URI[toolName]
  const capability = uri ? getCapability(uri) : undefined
  if (!capability) return FALLBACK_READER_LABEL
  return resolveReaderLabel(capability)
}

/**
 * Render a `tool_result` body's outcome as a short, reader-safe summary.
 * Never includes the raw `result` payload (which may carry internal shapes)
 * and never a `'[multipart content]'`-style placeholder — an honest, compact
 * phrase drawn only from status/detail/count/ms.
 */
function renderResultSummary(body: ToolResultBody): string {
  if (body.status === 'error') return body.detail ? `error — ${body.detail}` : 'error'
  if (body.detail) return body.detail
  if (typeof body.count === 'number') {
    const countPhrase = `${body.count} result${body.count === 1 ? '' : 's'}`
    return typeof body.ms === 'number' ? `${countPhrase} in ${body.ms}ms` : countPhrase
  }
  return 'done'
}

/**
 * Render a run of canonical turns into summarizer input text + the citation
 * lines that must survive verbatim. `priorSummarySeed` (an existing summary's
 * `summary_text`, when folding a new batch on top of an older one) is
 * prepended as an "[Earlier context]" block so the worker has continuity
 * without re-reading raw history.
 */
export function renderTurnsForSummary(
  turns: readonly CanonicalTurn[],
  priorSummarySeed?: string | null,
): RenderedTurns {
  const lines: string[] = []
  if (priorSummarySeed) lines.push(`[Earlier context]\n${priorSummarySeed}`)

  const citations: CitationLine[] = []

  for (const turn of turns) {
    const toolCallsById = new Map<string, ToolCallBody>()
    for (const part of turn.parts) {
      if (part.kind === 'tool_call') {
        const body = part.body as ToolCallBody
        toolCallsById.set(body.call_id, body)
      }
    }

    for (const part of turn.parts) {
      switch (part.kind) {
        case 'text': {
          const body = part.body as TextBody
          const trimmed = body.text.trim()
          if (trimmed) lines.push(trimmed)
          break
        }
        case 'tool_result': {
          const body = part.body as ToolResultBody
          const call = toolCallsById.get(body.call_id)
          const label = call ? resolveToolReaderLabel(call.tool_name) : FALLBACK_READER_LABEL
          lines.push(`consulted ${label} → ${renderResultSummary(body)}`)
          break
        }
        case 'citation': {
          const body = part.body as CitationBody
          citations.push({
            index: body.index,
            signal_id: body.signal_id,
            layer: body.layer,
            snippet: body.snippet,
          })
          break
        }
        // reasoning / tool_call / prediction_candidate / attachment are not
        // rendered as their own prose lines here — tool_call is consumed above
        // (paired with its tool_result), reasoning is model-internal, and
        // prediction_candidate/attachment have no summarizer-input contract
        // in this lane.
        default:
          break
      }
    }
  }

  return { text: lines.join('\n'), citations }
}

/**
 * Append a deterministic, LLM-independent citation block after the worker's
 * prose so every citation in the summarized range survives VERBATIM into
 * `summary_text` regardless of what the LLM chose to keep. This is the
 * citation-preservation guarantee: it never depends on the model.
 */
export function appendCitationBlock(summaryProse: string, citations: readonly CitationLine[]): string {
  const trimmedProse = summaryProse.trim()
  if (citations.length === 0) return trimmedProse
  const block = [...citations]
    .sort((a, b) => a.index - b.index)
    .map((c) => `[${c.index}] ${c.signal_id} (${c.layer}): ${c.snippet}`)
    .join('\n')
  return `${trimmedProse}\n\n[Citations carried forward — verbatim, resolvable]\n${block}`
}
