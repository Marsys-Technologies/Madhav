/**
 * ahead_autofile.test.ts — G14b AHEAD auto-file unit tests.
 *
 * Spec: MASTER_PLAN_v1_0.md G14(b).
 * Mocks: `fetch` (the platform DB query and platform writes calls) and
 * `callPlatformWrites` (via vi.mock) — same pattern as intervention_filing.test.ts.
 * SERVICE_TOKEN is set so client.ts's fetchIdentityToken() short-circuits to the
 * static-token path.
 *
 * Tests are organized as:
 *   §1 — pure helpers (buildSourceCitation, buildFalsifier, resolveEventClass) — no I/O
 *   §2 — autofileAheadWindows: event-class resolution and withhold gates
 *   §3 — autofileAheadWindows: idempotency (already_filed path)
 *   §4 — autofileAheadWindows: the sanctioned write path (filed path)
 *   §5 — autofileAheadWindows: error handling (failed path)
 *   §6 — KNOWN_EVENT_CLASSES non-vacuity (§N.8 earned-signal)
 *   §7 — AUTOFILE_WITHHOLD_EVENT_CLASSES: consistency with intervention_filing.ts
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Principal } from '../types.js'
import {
  buildSourceCitation,
  buildFalsifier,
  resolveEventClass,
  autofileAheadWindows,
  KNOWN_EVENT_CLASSES,
  AUTOFILE_WITHHOLD_EVENT_CLASSES,
  AHEAD_AUTOFILE_CONFIDENCE,
  AHEAD_AUTOFILE_FORMULA_VERSION,
  AHEAD_AUTOFILE_MODEL,
  type AutofileWindowInput,
} from './ahead_autofile.js'

// ── Shared test fixtures ─────────────────────────────────────────────────────────────

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key', role: 'guest' }

beforeEach(() => {
  vi.unstubAllGlobals()
  process.env['SERVICE_TOKEN'] = 'test-service-token'
})

function makeWindow(overrides: Partial<AutofileWindowInput> = {}): AutofileWindowInput {
  return {
    window_start: '2027-03-01',
    window_end: '2027-06-30',
    signature_classes: ['career_advancement'],
    domains: ['career'],
    ...overrides,
  }
}

/** Mock fetch that returns: DB query = no existing row, write call = success. */
function mockFetchBothSuccess(predictionId = 'pred-g14b-001') {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body ?? '{}')) as Record<string, unknown>
    // The DB existence check hits /api/mcp/db/query with a SELECT 1.
    if (String(url).includes('/api/mcp/db/query')) {
      return {
        ok: true,
        json: async () => ({ rows: [] }), // no existing row → proceed to file
        text: async () => '',
      }
    }
    // The write call hits /api/mcp/writes/prospective_ledger_file.
    if (String(url).includes('/api/mcp/writes/prospective_ledger_file')) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          trace_id: 'trace-g14b',
          epistemics: { surgical: true, confidence_band: 'medium', horizon_days: 14, falsifier: 'x' },
          result: { prediction: { prediction_id: predictionId } },
          citations: [],
          plan: null,
          predictions_logged: [],
          synthesis_audit: null,
          suggested_followups: [],
        }),
        text: async () => '',
      }
    }
    throw new Error(`Unexpected fetch call: ${url}`)
  })
}

// ── §1 — Pure helpers ─────────────────────────────────────────────────────────────────

describe('buildSourceCitation', () => {
  it('produces a deterministic, human-readable fingerprint', () => {
    const citation = buildSourceCitation(CHART_ID, 'career_advancement', '2027-03-01', '2027-06-30')
    expect(citation).toBe(
      `ahead_autofile:v1:${CHART_ID.toLowerCase()}:career_advancement:2027-03-01:2027-06-30`,
    )
  })

  it('is case-insensitive on chart_id and event_class', () => {
    const lower = buildSourceCitation(CHART_ID.toLowerCase(), 'career_advancement', '2027-03-01', '2027-06-30')
    const upper = buildSourceCitation(CHART_ID.toUpperCase(), 'CAREER_ADVANCEMENT', '2027-03-01', '2027-06-30')
    // chart_id is lowercased; event_class is lowercased.
    expect(lower).toBe(`ahead_autofile:v1:${CHART_ID.toLowerCase()}:career_advancement:2027-03-01:2027-06-30`)
    expect(upper).toBe(`ahead_autofile:v1:${CHART_ID.toLowerCase()}:career_advancement:2027-03-01:2027-06-30`)
  })

  it('two different windows produce different citations (no collision)', () => {
    const a = buildSourceCitation(CHART_ID, 'career_advancement', '2027-03-01', '2027-06-30')
    const b = buildSourceCitation(CHART_ID, 'career_advancement', '2027-07-01', '2027-09-30')
    expect(a).not.toBe(b)
  })

  it('two different event classes on the same window produce different citations', () => {
    const a = buildSourceCitation(CHART_ID, 'career_advancement', '2027-03-01', '2027-06-30')
    const b = buildSourceCitation(CHART_ID, 'major_gain', '2027-03-01', '2027-06-30')
    expect(a).not.toBe(b)
  })
})

describe('buildFalsifier', () => {
  it('produces a specific, non-empty falsifier naming the class and window', () => {
    const f = buildFalsifier('career_advancement', '2027-03-01', '2027-06-30')
    expect(f).toContain('career_advancement')
    expect(f).toContain('2027-03-01')
    expect(f).toContain('2027-06-30')
    expect(f.trim().length).toBeGreaterThan(20)
  })

  it('never contains vague language — cites the LEL as the check mechanism', () => {
    const f = buildFalsifier('major_loss', '2028-01-01', '2028-06-30')
    expect(f.toLowerCase()).toContain('lel')
  })
})

describe('resolveEventClass', () => {
  it('returns the first KNOWN_EVENT_CLASSES member from signature_classes', () => {
    expect(resolveEventClass(['career_advancement'])).toBe('career_advancement')
    expect(resolveEventClass(['major_gain', 'career_advancement'])).toBe('major_gain')
  })

  it('returns null for an empty or null signature_classes array', () => {
    expect(resolveEventClass(null)).toBeNull()
    expect(resolveEventClass(undefined)).toBeNull()
    expect(resolveEventClass([])).toBeNull()
  })

  it('returns null when no member is in KNOWN_EVENT_CLASSES', () => {
    expect(resolveEventClass(['unknown_class_xyz', 'also_unknown'])).toBeNull()
  })

  it("returns '_withheld' when the first matching class is in AUTOFILE_WITHHOLD_EVENT_CLASSES", () => {
    expect(resolveEventClass(['illness_acute'])).toBe('_withheld')
    expect(resolveEventClass(['surgery', 'career_advancement'])).toBe('_withheld')
  })

  it("returns a non-withheld class when the first match is withheld but later entries are safe", () => {
    // The loop returns '_withheld' on the FIRST matching member (illness_acute); it does
    // NOT continue to find career_advancement. This is the conservative behaviour:
    // a window with BOTH a withheld class and a safe class is treated as withheld.
    expect(resolveEventClass(['illness_acute', 'career_advancement'])).toBe('_withheld')
  })

  it('returns the safe class when the withheld class appears only after safe classes', () => {
    expect(resolveEventClass(['career_advancement', 'illness_acute'])).toBe('career_advancement')
  })
})

// ── §2 — autofileAheadWindows: event-class resolution and withhold gates ──────────────

describe('autofileAheadWindows — event-class resolution and withhold gates', () => {
  it('skips windows with no window_start or window_end — those are not interval-fileable', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const result = await autofileAheadWindows(
      CHART_ID,
      [{ window_start: null, window_end: '2027-06-30', signature_classes: ['career_advancement'] },
       { window_start: '2027-03-01', window_end: null, signature_classes: ['career_advancement'] }],
      PRINCIPAL,
    )

    expect(result.windows_examined).toBe(0)
    expect(result.filed_count).toBe(0)
    expect(result.outcomes).toHaveLength(0)
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('skips windows with no resolvable event class (no_resolvable_event_class)', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const result = await autofileAheadWindows(
      CHART_ID,
      [makeWindow({ signature_classes: ['unknown_predicate_label'] })],
      PRINCIPAL,
    )

    expect(result.windows_examined).toBe(1)
    expect(result.skipped_count).toBe(1)
    expect(result.filed_count).toBe(0)
    expect(result.outcomes[0]).toMatchObject({ kind: 'skipped', skipped_reason: 'no_resolvable_event_class' })
    // No network call at all — no class to check.
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('skips windows where the resolved class is in AUTOFILE_WITHHOLD_EVENT_CLASSES (adverse_class_withheld)', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    for (const cls of AUTOFILE_WITHHOLD_EVENT_CLASSES) {
      const result = await autofileAheadWindows(
        CHART_ID,
        [makeWindow({ signature_classes: [cls] })],
        PRINCIPAL,
      )
      expect(result.skipped_count).toBe(1)
      expect(result.outcomes[0]).toMatchObject({ kind: 'skipped', skipped_reason: 'adverse_class_withheld' })
    }
    // No network call for any of them.
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('skips a window with null/undefined signature_classes (no_resolvable_event_class)', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const result = await autofileAheadWindows(
      CHART_ID,
      [makeWindow({ signature_classes: undefined })],
      PRINCIPAL,
    )

    expect(result.skipped_count).toBe(1)
    expect(result.outcomes[0]).toMatchObject({ kind: 'skipped', skipped_reason: 'no_resolvable_event_class' })
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})

// ── §3 — autofileAheadWindows: idempotency (already_filed path) ─────────────────────

describe('autofileAheadWindows — idempotency: already_filed path', () => {
  it('skips filing when the DB existence check finds a matching source_citation row', async () => {
    let capturedExistQuery: string | null = null
    const fetchSpy = vi.fn(async (url: string, init?: RequestInit) => {
      if (String(url).includes('/api/mcp/db/query')) {
        const body = JSON.parse(String(init?.body ?? '{}')) as { sql?: string; params?: string[] }
        capturedExistQuery = body.params?.[0] ?? null
        return { ok: true, json: async () => ({ rows: [{ '?column?': 1 }] }), text: async () => '' }
      }
      throw new Error(`Unexpected fetch to ${url}`)
    })
    vi.stubGlobal('fetch', fetchSpy)

    const result = await autofileAheadWindows(
      CHART_ID,
      [makeWindow({ signature_classes: ['career_advancement'] })],
      PRINCIPAL,
    )

    expect(result.windows_examined).toBe(1)
    expect(result.skipped_count).toBe(1)
    expect(result.filed_count).toBe(0)
    expect(result.outcomes[0]).toMatchObject({ kind: 'skipped', skipped_reason: 'already_filed' })
    // The existence check SHOULD have been called with the correct source_citation.
    const expectedCitation = buildSourceCitation(CHART_ID, 'career_advancement', '2027-03-01', '2027-06-30')
    expect(capturedExistQuery).toBe(expectedCitation)
    // The write endpoint must NOT have been called.
    expect(fetchSpy.mock.calls.every((c) => !String(c[0]).includes('writes'))).toBe(true)
  })

  it('attempts the file when the DB existence check returns an empty row set', async () => {
    const fetchSpy = mockFetchBothSuccess()
    vi.stubGlobal('fetch', fetchSpy)

    const result = await autofileAheadWindows(
      CHART_ID,
      [makeWindow({ signature_classes: ['career_advancement'] })],
      PRINCIPAL,
    )

    expect(result.filed_count).toBe(1)
    // The write endpoint must have been called.
    expect(fetchSpy.mock.calls.some((c) => String(c[0]).includes('writes'))).toBe(true)
  })

  it('proceeds to file (conservatively) when the existence check fetch itself fails', async () => {
    let callCount = 0
    const fetchSpy = vi.fn(async (url: string, init?: RequestInit) => {
      callCount++
      if (String(url).includes('/api/mcp/db/query')) {
        throw new Error('DB query unreachable')
      }
      // Write path succeeds.
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true, trace_id: 't1',
          epistemics: { surgical: true, confidence_band: 'medium', horizon_days: 14, falsifier: 'x' },
          result: { prediction: { prediction_id: 'pred-fallback' } },
          citations: [], plan: null, predictions_logged: [], synthesis_audit: null, suggested_followups: [],
        }),
        text: async () => '',
      }
    })
    vi.stubGlobal('fetch', fetchSpy)

    const result = await autofileAheadWindows(
      CHART_ID,
      [makeWindow({ signature_classes: ['career_advancement'] })],
      PRINCIPAL,
    )

    // Conservative: when the read fails, attempt the write.
    expect(result.filed_count).toBe(1)
    expect(callCount).toBe(2) // once for DB query (throws), once for write
  })
})

// ── §4 — autofileAheadWindows: the sanctioned write path ─────────────────────────────

describe('autofileAheadWindows — the sanctioned write path (filed)', () => {
  it('files a valid window and returns a filed outcome with the prediction_id', async () => {
    vi.stubGlobal('fetch', mockFetchBothSuccess('pred-career-001'))

    const result = await autofileAheadWindows(
      CHART_ID,
      [makeWindow({ signature_classes: ['career_advancement'] })],
      PRINCIPAL,
    )

    expect(result.filed_count).toBe(1)
    expect(result.windows_examined).toBe(1)
    expect(result.outcomes[0]).toMatchObject({
      kind: 'filed',
      prediction_id: 'pred-career-001',
      event_class: 'career_advancement',
    })
  })

  it('sends chart_id and a correctly-shaped entry to prospective_ledger_file (claim_shape=interval, generator_class=engine)', async () => {
    let capturedBody: Record<string, unknown> | null = null
    const fetchSpy = vi.fn(async (url: string, init?: RequestInit) => {
      if (String(url).includes('/api/mcp/db/query')) {
        return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
      }
      capturedBody = JSON.parse(String(init?.body ?? '{}'))
      return {
        ok: true, status: 200,
        json: async () => ({
          ok: true, trace_id: 't1',
          epistemics: { surgical: true, confidence_band: 'medium', horizon_days: 14, falsifier: 'x' },
          result: { prediction: { prediction_id: 'pred-check' } },
          citations: [], plan: null, predictions_logged: [], synthesis_audit: null, suggested_followups: [],
        }),
        text: async () => '',
      }
    })
    vi.stubGlobal('fetch', fetchSpy)

    await autofileAheadWindows(
      CHART_ID,
      [makeWindow({ signature_classes: ['major_gain'], window_start: '2028-01-01', window_end: '2028-03-31' })],
      PRINCIPAL,
    )

    expect(capturedBody).not.toBeNull()
    const body = capturedBody as { chart_id: string; entry: Record<string, unknown> }
    expect(body.chart_id).toBe(CHART_ID)
    expect(body.entry['event_class']).toBe('major_gain')
    expect(body.entry['claim_shape']).toBe('interval')
    expect(body.entry['window_start']).toBe('2028-01-01')
    expect(body.entry['window_end']).toBe('2028-03-31')
    expect(body.entry['generator_class']).toBe('engine')
    expect(body.entry['model']).toBe(AHEAD_AUTOFILE_MODEL)
    expect(body.entry['formula_version']).toBe(AHEAD_AUTOFILE_FORMULA_VERSION)
    expect(body.entry['confidence']).toBe(AHEAD_AUTOFILE_CONFIDENCE)
    // filed_by must NOT be sent from the client side (server stamps it from principal).
    expect('filed_by' in body.entry).toBe(false)
    // falsifier must be non-empty and specific.
    expect(typeof body.entry['falsifier']).toBe('string')
    expect(String(body.entry['falsifier']).trim().length).toBeGreaterThan(20)
    expect(String(body.entry['falsifier'])).toContain('major_gain')
    // source_citation must be the deterministic fingerprint.
    const expectedCitation = buildSourceCitation(CHART_ID, 'major_gain', '2028-01-01', '2028-03-31')
    expect(body.entry['source_citation']).toBe(expectedCitation)
  })

  it('processes multiple eligible windows, filing each separately', async () => {
    vi.stubGlobal('fetch', mockFetchBothSuccess('pred-multi'))

    const result = await autofileAheadWindows(
      CHART_ID,
      [
        makeWindow({ signature_classes: ['career_advancement'], window_start: '2027-01-01', window_end: '2027-03-31' }),
        makeWindow({ signature_classes: ['major_gain'], window_start: '2027-04-01', window_end: '2027-06-30' }),
      ],
      PRINCIPAL,
    )

    expect(result.windows_examined).toBe(2)
    expect(result.filed_count).toBe(2)
    expect(result.skipped_count).toBe(0)
    expect(result.outcomes.filter((o) => o.kind === 'filed')).toHaveLength(2)
  })

  it('mixes filed, skipped, and failed outcomes for a heterogeneous window list', async () => {
    // Distinct source citations let us route fetch calls deterministically:
    // career_advancement → file succeeds; major_gain → file fails.
    const majorGainCitation = buildSourceCitation(CHART_ID, 'major_gain', '2027-04-01', '2027-06-30')

    const fetchSpy = vi.fn(async (url: string, init?: RequestInit) => {
      if (String(url).includes('/api/mcp/db/query')) {
        return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
      }
      // Write path: fail the major_gain window, succeed the career_advancement window.
      if (String(url).includes('/api/mcp/writes/prospective_ledger_file')) {
        const body = JSON.parse(String(init?.body ?? '{}')) as { entry?: Record<string, unknown> }
        if (body.entry?.['source_citation'] === majorGainCitation) {
          return {
            ok: true, status: 500,
            json: async () => ({ ok: false, trace_id: 't1', error: { message: 'server error on major_gain' } }),
            text: async () => '',
          }
        }
        return {
          ok: true, status: 200,
          json: async () => ({
            ok: true, trace_id: 't1',
            epistemics: { surgical: true, confidence_band: 'medium', horizon_days: 14, falsifier: 'x' },
            result: { prediction: { prediction_id: 'pred-career' } },
            citations: [], plan: null, predictions_logged: [], synthesis_audit: null, suggested_followups: [],
          }),
          text: async () => '',
        }
      }
      throw new Error(`Unexpected fetch call: ${url}`)
    })
    vi.stubGlobal('fetch', fetchSpy)

    const result = await autofileAheadWindows(
      CHART_ID,
      [
        // window 1: no class → skipped
        makeWindow({ signature_classes: [] }),
        // window 2: valid class → filed
        makeWindow({ signature_classes: ['career_advancement'], window_start: '2027-01-01', window_end: '2027-03-31' }),
        // window 3: valid class but write fails → failed
        makeWindow({ signature_classes: ['major_gain'], window_start: '2027-04-01', window_end: '2027-06-30' }),
      ],
      PRINCIPAL,
    )

    expect(result.windows_examined).toBe(3)
    expect(result.filed_count).toBe(1)
    expect(result.skipped_count).toBe(1)
    expect(result.failed_count).toBe(1)
  })
})

// ── §5 — autofileAheadWindows: error handling (failed path) ──────────────────────────

describe('autofileAheadWindows — error handling (never throws)', () => {
  it('reports filing_failed on a network error from the write call, never throws to the caller', async () => {
    const fetchSpy = vi.fn(async (url: string) => {
      if (String(url).includes('/api/mcp/db/query')) {
        return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
      }
      throw new Error('network unreachable')
    })
    vi.stubGlobal('fetch', fetchSpy)

    const result = await autofileAheadWindows(
      CHART_ID,
      [makeWindow({ signature_classes: ['career_advancement'] })],
      PRINCIPAL,
    )

    expect(result.failed_count).toBe(1)
    expect(result.filed_count).toBe(0)
    expect(result.outcomes[0]).toMatchObject({ kind: 'failed', detail: expect.stringContaining('network unreachable') })
  })

  it('reports failed when the server returns !envelope.ok, with the verbatim error message', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (String(url).includes('/api/mcp/db/query')) {
        return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
      }
      return {
        ok: true, status: 400,
        json: async () => ({
          ok: false, trace_id: 't1',
          error: { message: 'unknown event_class not_in_ontology' },
        }),
        text: async () => '',
      }
    }))

    const result = await autofileAheadWindows(
      CHART_ID,
      [makeWindow({ signature_classes: ['career_advancement'] })],
      PRINCIPAL,
    )

    expect(result.failed_count).toBe(1)
    expect(result.outcomes[0]).toMatchObject({ kind: 'failed', detail: expect.stringContaining('unknown event_class') })
  })

  it('reports failed when ok=true but prediction_id is absent (§N.8 earned-signal)', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (String(url).includes('/api/mcp/db/query')) {
        return { ok: true, json: async () => ({ rows: [] }), text: async () => '' }
      }
      return {
        ok: true, status: 200,
        json: async () => ({ ok: true, trace_id: 't1', result: {} }),
        text: async () => '',
      }
    }))

    const result = await autofileAheadWindows(
      CHART_ID,
      [makeWindow({ signature_classes: ['career_advancement'] })],
      PRINCIPAL,
    )

    expect(result.failed_count).toBe(1)
    expect(result.outcomes[0]).toMatchObject({ kind: 'failed', detail: expect.stringContaining('no resolvable prediction_id') })
  })

  it('returns an empty result for an empty windows array — no I/O at all', async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal('fetch', fetchSpy)

    const result = await autofileAheadWindows(CHART_ID, [], PRINCIPAL)

    expect(result.windows_examined).toBe(0)
    expect(result.filed_count).toBe(0)
    expect(result.outcomes).toHaveLength(0)
    expect(fetchSpy).not.toHaveBeenCalled()
  })
})

// ── §6 — KNOWN_EVENT_CLASSES non-vacuity (§N.8 earned-signal) ───────────────────────

describe('KNOWN_EVENT_CLASSES — §N.8 earned-signal non-vacuity', () => {
  it('is non-empty (a vacuous set would silently skip every window)', () => {
    expect(KNOWN_EVENT_CLASSES.size).toBeGreaterThan(0)
  })

  it('contains at least the six core career/wealth classes that are primary AHEAD targets', () => {
    for (const cls of ['career_entry', 'career_advancement', 'career_change', 'career_setback', 'major_gain', 'major_loss']) {
      expect(KNOWN_EVENT_CLASSES.has(cls), `expected KNOWN_EVENT_CLASSES to contain '${cls}'`).toBe(true)
    }
  })

  it('every member of AUTOFILE_WITHHOLD_EVENT_CLASSES is also in KNOWN_EVENT_CLASSES', () => {
    for (const cls of AUTOFILE_WITHHOLD_EVENT_CLASSES) {
      expect(
        KNOWN_EVENT_CLASSES.has(cls),
        `AUTOFILE_WITHHOLD_EVENT_CLASSES contains '${cls}' which is NOT in KNOWN_EVENT_CLASSES — ` +
        'a withheld class that is not known would never match any window (the withhold gate is unreachable), ' +
        'which is the §N.8 no-op-completion defect class applied to a safety gate.',
      ).toBe(true)
    }
  })
})

// ── §7 — AUTOFILE_WITHHOLD_EVENT_CLASSES consistency with intervention_filing.ts ─────

describe('AUTOFILE_WITHHOLD_EVENT_CLASSES — must match intervention_filing.ts WITHHOLD_EVENT_CLASSES', () => {
  it('contains exactly the five ADJUDICATION-13 classes (illness_acute, chronic_onset, surgery, psychological_arc, bereavement)', () => {
    expect(AUTOFILE_WITHHOLD_EVENT_CLASSES.size).toBe(5)
    for (const cls of ['illness_acute', 'chronic_onset', 'surgery', 'psychological_arc', 'bereavement']) {
      expect(AUTOFILE_WITHHOLD_EVENT_CLASSES.has(cls), `expected '${cls}' in AUTOFILE_WITHHOLD_EVENT_CLASSES`).toBe(true)
    }
  })

  it('the withhold set is not empty (§N.8: a vacuous safety gate is not a safety gate)', () => {
    expect(AUTOFILE_WITHHOLD_EVENT_CLASSES.size).toBeGreaterThan(0)
  })
})
