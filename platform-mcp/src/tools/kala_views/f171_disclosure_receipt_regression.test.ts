/**
 * f171_disclosure_receipt_regression.test.ts — F-171 regression guard.
 *
 * Defect: `kala_priority_get` (`priority.ts`) calls the SAME capability
 * (`marsys://tool/L3/call_priority_ranking`) that F-131 already fixed correctly — the
 * exclusion of internal computation-abstention marker rows genuinely happens upstream — but
 * this facade discarded F-131's disclosure receipt when forwarding the payload (only
 * `ranked_signals` / `signal_count` / `neutral_dignity_downranked_count` /
 * `neutral_dignity_note` were forwarded) and narrated from the raw `signal_headline_text`
 * template instead of the curated `signal_headline_label`.
 *
 * Drives the REAL registered `kala_priority_get` handler (mirrors
 * f123_dead_pointer_regression.test.ts's `captureRegisteredHandler` pattern) so a regression
 * that re-drops the forwarding at the seam makes THIS test fail for real, not a hand-derived
 * proxy of it.
 */
import { describe, expect, it, vi } from 'vitest'
import type { Principal } from '../../types.js'
import { registerKalaPriorityTool } from './priority.js'

const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'
const TEST_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

/** Minimal capturing fake McpServer — registers the real tool's handler and hands it back,
 *  same pattern as f123_dead_pointer_regression.test.ts's captureRegisteredHandler. */
function captureRegisteredHandler(
  registerFn: (server: { tool: (...args: unknown[]) => void }, principal: Principal) => void,
  principal: Principal,
): (params: Record<string, unknown>) => Promise<unknown> {
  let captured: ((params: Record<string, unknown>) => Promise<unknown>) | null = null
  const fakeServer = {
    tool: (..._args: unknown[]) => {
      const handler = _args[_args.length - 1] as (params: Record<string, unknown>) => Promise<unknown>
      captured = handler
    },
  }
  registerFn(fakeServer, principal)
  if (!captured) throw new Error('registerFn never called server.tool() — nothing captured')
  return captured
}

function extractContent(mcpResult: unknown): Record<string, unknown> {
  const asAny = mcpResult as { content?: Array<{ type: string; text?: string }> }
  const textBlock = asAny.content?.find((c) => c.type === 'text')
  if (!textBlock?.text) throw new Error('MCP tool result had no text content block')
  return JSON.parse(textBlock.text) as Record<string, unknown>
}

/** Builds a capability-side payload matching call_service_wrappers.ts's real
 *  `call_priority_ranking` response shape (F-131's landed pattern), so the mock fixture is
 *  faithful to what the real upstream capability actually returns. */
function capabilityPayload(overrides: Record<string, unknown>): Record<string, unknown> {
  return {
    chart_id: TEST_CHART_ID,
    ayanamsha_id: 'lahiri_chitrapaksha',
    date_from: '2026-08-01',
    date_to: '2026-11-01',
    domain_filter: null,
    ranked_signals: [
      {
        signal_id: 'sig-1',
        signal_headline_text: 'graha cheshta bala per varga: d9 = 0.62 [ga_structural]',
        signal_headline_label: 'Mars cheṣṭā bala (D9): 0.62',
        headline_label_mapped: true,
        headline_fact_category: 'ga_structural',
        catalog_only_unverified: false,
        computed_salience: 0.8,
        domains_affected_array: ['career'],
        signal_type_class: 'transit',
        activation_strength: 0.9,
        window_start: '2026-08-01',
        window_end: '2026-10-15',
        trigger_type: 'gochara',
        neutral_dignity_downranked: false,
        priority_score: 0.75,
      },
    ],
    signal_count: 1,
    signal_id_refs: ['sig-1'],
    neutral_dignity_downranked_count: 0,
    excluded_internal_marker_count: 0,
    excluded_internal_markers: [],
    unmapped_headline_count: 0,
    catalog_only_rows_in_page: 0,
    ...overrides,
  }
}

function mockPriorityFetch(capabilityContent: Record<string, unknown>) {
  return vi.fn(async (url: unknown, opts: unknown) => {
    const urlStr = String(url)
    if (urlStr.includes('/api/mcp/db/query')) {
      return { ok: true, json: async () => ({ rows: [] }), text: async () => '' } as unknown as Response
    }
    if (urlStr.includes('/api/retrieval/capability')) {
      const body = JSON.parse(String((opts as { body?: string })?.body ?? '{}')) as { uri?: string }
      if (body.uri === 'marsys://tool/L3/call_priority_ranking') {
        return {
          ok: true,
          json: async () => ({ ok: true, content: capabilityContent }),
        } as unknown as Response
      }
    }
    return { ok: false, status: 500, text: async () => 'unexpected' } as unknown as Response
  })
}

async function invokePriority(capabilityContent: Record<string, unknown>): Promise<Record<string, unknown>> {
  vi.stubGlobal('fetch', mockPriorityFetch(capabilityContent))
  try {
    const handler = captureRegisteredHandler(
      registerKalaPriorityTool as unknown as (server: { tool: (...args: unknown[]) => void }, principal: Principal) => void,
      TEST_PRINCIPAL,
    )
    const mcpResult = await handler({ chart_id: TEST_CHART_ID })
    return extractContent(mcpResult)
  } finally {
    vi.unstubAllGlobals()
  }
}

describe('F-171: kala_priority_get forwards the F-131 disclosure receipt and narrates from curated labels', () => {
  it('MUST-FAIL-TODAY: a capability payload carrying excluded_internal_marker_count:3 is reflected in the served content', async () => {
    const excludedMarkers = [
      { signal_id: 'sig-abstain-1', signal_headline_text: 'graha cheshta bala per varga: D14 = floored: no_canonical_per_varga_method [ga_structural]', matched_pattern: 'floored: no_canonical', priority_score: 0.9, pre_exclusion_rank: 1, exclusion_reason: 'internal_computation_abstention_marker' },
      { signal_id: 'sig-abstain-2', signal_headline_text: 'graha cheshta bala per varga: D10 = floored: no_canonical_per_varga_method [ga_structural]', matched_pattern: 'floored: no_canonical', priority_score: 0.85, pre_exclusion_rank: 2, exclusion_reason: 'internal_computation_abstention_marker' },
      { signal_id: 'sig-abstain-3', signal_headline_text: 'graha cheshta bala per varga: D7 = floored: no_canonical_per_varga_method [ga_structural]', matched_pattern: 'floored: no_canonical', priority_score: 0.81, pre_exclusion_rank: 5, exclusion_reason: 'internal_computation_abstention_marker' },
    ]
    const content = await invokePriority(capabilityPayload({
      excluded_internal_marker_count: 3,
      excluded_internal_markers: excludedMarkers,
      excluded_internal_marker_note: '3 row(s) that would otherwise have ranked within the top N were EXCLUDED from ranked_signals.',
    }))

    // The load-bearing assertion: today (before the fix) these keys are absent entirely.
    expect(content['excluded_internal_marker_count']).toBe(3)
    expect(content['excluded_internal_markers']).toEqual(excludedMarkers)
    expect(content['excluded_internal_marker_note']).toContain('3 row(s)')
  })

  it('zero-exclusion case: excluded_internal_marker_count is present and 0, not absent (§N.8: "never evaluated" must be distinguishable from "nothing excluded")', async () => {
    const content = await invokePriority(capabilityPayload({}))

    expect(content).toHaveProperty('excluded_internal_marker_count')
    expect(content['excluded_internal_marker_count']).toBe(0)
    expect(content).toHaveProperty('excluded_internal_markers')
    expect(content['excluded_internal_markers']).toEqual([])
    // _note is only present when non-zero — mirrors F-131's shape exactly.
    expect(content).not.toHaveProperty('excluded_internal_marker_note')

    expect(content).toHaveProperty('unmapped_headline_count')
    expect(content['unmapped_headline_count']).toBe(0)
    expect(content).not.toHaveProperty('unmapped_headline_note')

    expect(content).toHaveProperty('catalog_only_rows_in_page')
    expect(content['catalog_only_rows_in_page']).toBe(0)
    expect(content).not.toHaveProperty('catalog_only_note')
  })

  it('unmapped_headline_count/_note and catalog_only_rows_in_page/_note forward when non-zero', async () => {
    const content = await invokePriority(capabilityPayload({
      unmapped_headline_count: 2,
      unmapped_headline_note: '2 of 1 row(s) have no entry in the signal-register glossary.',
      catalog_only_rows_in_page: 1,
      catalog_only_note: '1 row(s) are catalog-only matches awaiting cross-verification.',
    }))

    expect(content['unmapped_headline_count']).toBe(2)
    expect(content['unmapped_headline_note']).toContain('no entry in the signal-register glossary')
    expect(content['catalog_only_rows_in_page']).toBe(1)
    expect(content['catalog_only_note']).toContain('catalog-only matches')
  })

  it('label case: reading narrates from signal_headline_label, not the raw signal_headline_text template', async () => {
    const content = await invokePriority(capabilityPayload({}))
    const reading = content['reading'] as { thesis: string; evidence: Array<{ claim: string }> }

    expect(reading.thesis).toContain('Mars cheṣṭā bala (D9): 0.62')
    expect(reading.thesis).not.toContain('graha cheshta bala per varga: d9 = 0.62 [ga_structural]')
    expect(reading.evidence[0]?.claim).toContain('Mars cheṣṭā bala (D9): 0.62')
    expect(reading.evidence[0]?.claim).not.toContain('[ga_structural]')
  })

  it('label fallback: when headline_label_mapped is false, the raw signal_headline_text is used (nothing invented)', async () => {
    const content = await invokePriority(capabilityPayload({
      ranked_signals: [
        {
          signal_id: 'sig-2',
          signal_headline_text: 'some raw unmapped template string',
          signal_headline_label: 'some raw unmapped template string',
          headline_label_mapped: false,
          headline_fact_category: null,
          catalog_only_unverified: false,
          priority_score: 0.5,
        },
      ],
      unmapped_headline_count: 1,
      unmapped_headline_note: '1 of 1 row(s) have no entry in the signal-register glossary.',
    }))
    const reading = content['reading'] as { thesis: string }
    expect(reading.thesis).toContain('some raw unmapped template string')
  })

  it('catalog_only_unverified rows are flagged in the evidence claim (§N.6 item 1)', async () => {
    const content = await invokePriority(capabilityPayload({
      ranked_signals: [
        {
          signal_id: 'sig-3',
          signal_headline_text: 'candidate yoga match: raja yoga [requires_pass]',
          signal_headline_label: 'Candidate Rāja Yoga (label match)',
          headline_label_mapped: true,
          headline_fact_category: 'ga_yoga_catalog',
          catalog_only_unverified: true,
          priority_score: 0.6,
        },
      ],
      catalog_only_rows_in_page: 1,
      catalog_only_note: '1 row(s) are catalog-only matches awaiting cross-verification.',
    }))
    const reading = content['reading'] as { evidence: Array<{ claim: string }> }
    expect(reading.evidence[0]?.claim).toContain('CATALOG-ONLY')
  })
})
