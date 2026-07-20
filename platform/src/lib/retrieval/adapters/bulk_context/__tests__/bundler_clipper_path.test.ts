/**
 * bundler_clipper_path.test.ts — W3-L5 (budget unification, R-2 item 5 / W-8).
 *
 * The retrieval-plane budget unification migrated every MCP tool registration onto
 * `finalizeMcpBudget` (platform-mcp/src/lib/response_budget.ts) and evicted the byte-
 * truncating `result_clipper.ts` from that path. This test asserts the ONE thing that
 * migration must never touch: `result_clipper.ts`'s live caller on the bulk-context/
 * hybrid path (`adapters/bulk_context/bundler.ts`) still clips oversized sections via
 * `clipResult`, unchanged — GT-17 (`result_clipper.ts` is NOT orphaned; it is a
 * narrower-purpose LLM-context clipper for THIS path, not dead code to delete).
 */
import { describe, it, expect } from 'vitest'
import { buildBundle, formatBundleForPrompt } from '../bundler'
import type { PrefetchResult } from '../prefetcher'
import type { CapabilityUri } from '@/lib/retrieval/registry/types'

function makeResult(uri: string, content: unknown): PrefetchResult {
  return { uri: uri as CapabilityUri, content, tokens_estimate: 0 }
}

describe('bundler.ts — result_clipper.ts live caller (GT-17, untouched by W3-L5)', () => {
  it('clips a section whose serialized content exceeds SECTION_MAX_KB (16KB) and marks clipped:true', () => {
    // 20,000 chars of payload — comfortably over the 16KB section ceiling once JSON-serialized.
    const bigPayload = { rows: Array.from({ length: 2000 }, (_, i) => ({ id: i, note: 'x'.repeat(50) })) }
    const results = [makeResult('marsys://tool/L2/big_payload', bigPayload)]

    const bundle = buildBundle(results)

    expect(bundle.sections).toHaveLength(1)
    const section = bundle.sections[0]!
    expect(section.clipped).toBe(true)
    // clipResult's truncate_end strategy appends this exact marker (result_clipper.ts) —
    // asserting on it proves the CLIPPER ran, not some other mechanism.
    expect(section.content).toContain('[RESULT CLIPPED')
    const contentBytes = new TextEncoder().encode(section.content).length
    expect(contentBytes).toBeLessThanOrEqual(16 * 1024)
  })

  it('does NOT clip a small section — content passes through as plain serialized JSON', () => {
    const smallPayload = { ok: true, count: 3 }
    const results = [makeResult('marsys://tool/L2/small_payload', smallPayload)]

    const bundle = buildBundle(results)

    expect(bundle.sections).toHaveLength(1)
    const section = bundle.sections[0]!
    expect(section.clipped).toBe(false)
    expect(section.content).not.toContain('[RESULT CLIPPED')
    expect(section.content).toBe(JSON.stringify(smallPayload, null, 2))
  })

  it('formatBundleForPrompt annotates clipped sections with the clip note', () => {
    const bigPayload = { blob: 'y'.repeat(40_000) }
    const bundle = buildBundle([makeResult('marsys://tool/L2/blob', bigPayload)])
    const formatted = formatBundleForPrompt(bundle)
    expect(formatted).toContain('[result clipped to fit context window]')
  })
})
