/**
 * Paripraśna durable conversation summaries — PB-2 (SMṚTI) lane M-3 — context assembly.
 *
 * Pure, deterministic prefix assembly. `assembleSynthesisPrefix` is the
 * "prefix-stable splice" the brief asks for: the durable-summary block
 * occupies a FIXED structural slot (a fixed label, in a fixed position, ahead
 * of whatever else the caller passes) whether or not a summary exists yet — an
 * explicitly-labeled empty slot when null, never an omitted section — so the
 * assembled prefix's STRUCTURE depends only on `summaryText`'s own content,
 * never on anything else in the request varying turn to turn. Two calls with
 * the same `summaryText` (i.e. no new threshold crossing happened between
 * them) produce byte-identical output and therefore an identical hash — the
 * cache-relevant prefix a provider's prompt-caching layer sees is unchanged.
 *
 * This module has NO knowledge of the live route's actual system-prompt
 * builder (`buildConsultSystemContent`) — it is deliberately standalone and
 * pure so it can be unit-tested (see `__tests__/prefix_stability.test.ts`)
 * without needing the full route wired up. The route's splice point
 * (`src/app/api/pariprashna/route.ts`) calls this to build the block it
 * prepends ahead of the existing `systemContent` it already builds.
 */
import { createHash } from 'node:crypto'

export const SUMMARY_SLOT_LABEL = '[Conversation summary — earlier turns]'
export const SUMMARY_SLOT_EMPTY_BODY = '(none yet)'

/**
 * Build the fixed-slot durable-summary block. Always the same shape
 * (`SUMMARY_SLOT_LABEL` header + body), regardless of whether `summaryText`
 * is null — only the body content varies.
 */
export function buildDurableSummaryBlock(summaryText: string | null): string {
  return `${SUMMARY_SLOT_LABEL}\n${summaryText && summaryText.trim() ? summaryText.trim() : SUMMARY_SLOT_EMPTY_BODY}`
}

export interface AssembleSynthesisPrefixInput {
  /** Deterministic-per-chart content that precedes the summary slot (e.g. the
   *  chart-header / bundle system content). Caller-supplied so this module
   *  stays decoupled from the route's actual builder. */
  precedingBlock: string
  /** The durable summary text (or null — no summary yet / not applicable). */
  summaryText: string | null
  /** Content that follows the summary slot (e.g. synthesis guidance). Optional. */
  followingBlock?: string
}

/**
 * Assemble the full prefix: preceding block, then the FIXED summary slot,
 * then the optional following block, each separated by a stable delimiter.
 * Pure function — same input, same output, always.
 */
export function assembleSynthesisPrefix(input: AssembleSynthesisPrefixInput): string {
  const sections = [input.precedingBlock, buildDurableSummaryBlock(input.summaryText)]
  if (input.followingBlock) sections.push(input.followingBlock)
  return sections.join('\n\n---\n\n')
}

/** SHA-256 hex digest of a prefix string — used by the stability test to
 *  assert byte-for-byte equality without diffing giant strings inline. */
export function hashPrefix(prefix: string): string {
  return createHash('sha256').update(prefix).digest('hex')
}
