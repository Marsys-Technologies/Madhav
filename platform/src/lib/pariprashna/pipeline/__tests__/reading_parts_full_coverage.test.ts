/**
 * Lane P3-C (SMṚTI completion) — §N.8 earned-signal coverage detector.
 *
 * `checkPartKindCoverage` is the detector this lane adds: given a turn that
 * DID produce thinking content and a tool dispatch, does the persisted
 * canonical `message_parts` set actually carry every kind that content
 * implies? Per CLAUDE.md §N.8, a status/PASS signal is null unless it is
 * demonstrated CAPABLE OF FAILING before its first green counts. The first
 * test below reproduces the exact pre-P3-C defect (a thinking block and a
 * tool dispatch happened, but `buildCanonicalParts` used to drop both kinds
 * silently) and asserts the detector correctly reports the gap RED; the
 * second test proves the SAME detector goes GREEN once P3-C's fix (this
 * lane) actually persists them.
 */
import { describe, it, expect } from 'vitest'

import { buildCanonicalParts, checkPartKindCoverage, type OpenBlock } from '../reading_parts'
import type { ToolBundle } from '@/lib/retrieval/shared_types'

// Synthetic chart ONLY — never the native's real chart (482012f1-…).
const SYNTHETIC_CHART_ID = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

const THINKING_BLOCK: OpenBlock = {
  id: 'blk-1-1',
  role: 'thinking',
  text: 'weigh Moon dignity before answering',
}
const PROSE_BLOCK: OpenBlock = {
  id: 'blk-1-2',
  role: 'prose',
  text: 'Your Moon sits in Purva Bhadrapada.',
}

const TOOL_BUNDLE: ToolBundle = {
  tool_bundle_id: 'tb-1',
  tool_name: 'ganita_nakshatra_get',
  tool_version: '1.0',
  invocation_params: { chart_id: SYNTHETIC_CHART_ID, planet: 'Moon' },
  results: [{ content: 'Purva Bhadrapada' }],
  served_from_cache: false,
  latency_ms: 12,
  result_hash: 'sha256:test',
  schema_version: '1.0',
}

const FULL_TURN_EXPECTED_KINDS = ['tool_call', 'tool_result', 'text', 'reasoning'] as const

describe('checkPartKindCoverage — §N.8 detector', () => {
  it('RED: withholding the thinking block + tool dispatch is correctly reported as missing coverage', () => {
    // Reproduces the pre-P3-C shape directly: only the prose block and no
    // tool dispatch make it into the builder, even though (per the fixture
    // below) the turn's real content included both.
    const truncated = buildCanonicalParts({
      committedBlocks: [PROSE_BLOCK], // thinking block withheld, on purpose
      accumulatedText: PROSE_BLOCK.text,
      snippets: new Map(),
      validToolResults: [], // tool dispatch withheld, on purpose
    })
    const coverage = checkPartKindCoverage(truncated.parts, FULL_TURN_EXPECTED_KINDS)
    expect(coverage.ok).toBe(false)
    expect([...coverage.missing].sort()).toEqual(['reasoning', 'tool_call', 'tool_result'])
  })

  it('GREEN: supplying the same turn\'s real thinking block + tool dispatch passes full coverage', () => {
    const full = buildCanonicalParts({
      committedBlocks: [THINKING_BLOCK, PROSE_BLOCK],
      accumulatedText: PROSE_BLOCK.text,
      snippets: new Map(),
      validToolResults: [TOOL_BUNDLE],
    })
    const coverage = checkPartKindCoverage(full.parts, FULL_TURN_EXPECTED_KINDS)
    expect(coverage.ok).toBe(true)
    expect(coverage.missing).toEqual([])
    // Chronology-honest ordering: evidence (tool_call/tool_result) precedes
    // synthesis (reasoning/text, in block order) — see reading_parts.ts's
    // buildCanonicalParts doc.
    expect(full.parts.map((p) => p.kind)).toEqual(['tool_call', 'tool_result', 'reasoning', 'text'])
    expect(full.toolArgsRedactedCount).toBe(0)
  })

  it('a leaking tool arg VALUE is redacted before persistence (keys — e.g. chart_id — are never touched)', () => {
    const leaking: ToolBundle = {
      ...TOOL_BUNDLE,
      invocation_params: {
        chart_id: SYNTHETIC_CHART_ID, // a benign key that LOOKS table-prefix-shaped
        note: 'see SIG.MSR.042 for context', // an actual leak, in a VALUE
      },
    }
    const result = buildCanonicalParts({
      committedBlocks: [PROSE_BLOCK],
      accumulatedText: PROSE_BLOCK.text,
      snippets: new Map(),
      validToolResults: [leaking],
    })
    expect(result.toolArgsRedactedCount).toBe(1)
    const toolCallPart = result.parts.find((p) => p.kind === 'tool_call')
    const args = (toolCallPart?.body as { args: Record<string, unknown> }).args
    // The benign key/value survives untouched...
    expect(args.chart_id).toBe(SYNTHETIC_CHART_ID)
    // ...but the leaking value does not carry the raw signal id through.
    expect(String(args.note)).not.toContain('SIG.MSR.042')
  })
})
