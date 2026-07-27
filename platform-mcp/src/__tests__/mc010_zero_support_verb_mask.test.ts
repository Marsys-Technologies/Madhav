/**
 * mc010_zero_support_verb_mask.test.ts — ŚODHANA T1 self-verification for MC-010.
 *
 * MC-010 (P0-safety): synth_chart_brief_get's ranked_themes.weaknesses[]/open_questions[]
 * and verdict_summary[].statement must never render a pass/fail verb ("denied"/"promised"/
 * "confirmed") on a row where n_support=0 (zero backing evidence rows) — that reads as a
 * categorical finding to a skimming reader on safety-sensitive domains (marriage, health,
 * childbirth, financial loss).
 *
 * Fixture below reproduces the EXACT rows returned live by the deployed
 * synth_chart_brief_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, depth=standard)
 * call (captured 2026-07-27, catalog-1+t152+r653c2a1a98c8) — including the
 * n_support=0 "Childbirth: denied (grade 5.0/10)" / "Discrete Travel Event" /
 * "Major Financial Loss"-style rows the conductor's triage flagged, alongside
 * n_support=5 rows (e.g. "Marriage") that legitimately keep their verb because they
 * DO carry supporting evidence — proving the fix is evidence-conditioned, not a
 * blanket rename.
 *
 * All network calls are mocked — no real DB or platform server required.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { registerP1SynthesisTools } from '../tools/register_p1_synthesis.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

// Zero-support rows (n_support=0) — the MC-010 problem rows, verbatim statement text
// as served live in production today (pre-fix).
const ZERO_SUPPORT_ROWS = [
  {
    insight_id: 'verdict_childbirth', insight_type: 'verdict_object', domain: 'progeny',
    question_lens: 'childbirth',
    statement: "Childbirth: denied (grade 5.0/10). Conditional — context-dependent.",
    rank_consequence: 0.5, confidence_band: '[0.35,0.65)', n_support: 0,
    evidence_grade: 'structural', is_negative_knowledge: false,
  },
  {
    insight_id: 'verdict_travel_event', insight_type: 'verdict_object', domain: 'travel',
    question_lens: 'travel_event',
    statement: "Discrete Travel Event: denied (grade 5.0/10). Conditional — context-dependent.",
    rank_consequence: 0.5, confidence_band: '[0.35,0.65)', n_support: 0,
    evidence_grade: 'structural', is_negative_knowledge: false,
  },
]

// n_support=5 row (real evidence) — "Marriage" and "Major Financial Loss" both carry
// n_support=5 in live production data; the verb here is legitimate and must be preserved.
const SUPPORTED_ROWS = [
  {
    insight_id: 'verdict_marriage', insight_type: 'verdict_object', domain: 'relationship',
    question_lens: 'marriage',
    statement: "Marriage: denied (grade 1.6/10). Mixed or insufficient evidence.",
    rank_consequence: 0.1621, confidence_band: '[0.16,0.36)', n_support: 5,
    evidence_grade: 'structural', is_negative_knowledge: false,
  },
  {
    insight_id: 'verdict_major_loss', insight_type: 'verdict_object', domain: 'wealth',
    question_lens: 'major_loss',
    statement: "Major Financial Loss: denied (grade 1.4/10). Mixed or insufficient evidence.",
    rank_consequence: 0.137, confidence_band: '[0.14,0.34)', n_support: 5,
    evidence_grade: 'structural', is_negative_knowledge: false,
  },
]

const ALL_ROWS = [...ZERO_SUPPORT_ROWS, ...SUPPORTED_ROWS]

function jsonResponse(body: unknown) {
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
  })
}

describe('MC-010 (SODHANA T1) — zero-support verb masking in synth_chart_brief_get', () => {
  let handler: (args: { chart_id: string; depth?: 'standard' | 'deep' | 'complete'; audience?: 'native' | 'third_party' }) => Promise<{
    content: Array<{ type: string; text: string }>
    structuredContent?: { type: string; object: unknown }
    isError?: boolean
  }>

  beforeEach(() => {
    mockFetch.mockReset()
    mockFetch.mockImplementation((url: string, init?: { body?: string }) => {
      if (url.includes('/api/mcp/authz')) {
        return jsonResponse({ authorized: true })
      }
      if (url.includes('/api/mcp/db/query')) {
        const body = init?.body ? JSON.parse(init.body) as { sql: string } : { sql: '' }
        if (body.sql.includes('FROM mimamsa_insight_units')) {
          return jsonResponse({ rows: ALL_ROWS })
        }
        if (body.sql.includes('FROM bodha_discoveries')) {
          return jsonResponse({ rows: [] })
        }
      }
      return jsonResponse({})
    })

    const mockServer = {
      tool: (name: string, _desc: unknown, _schema: unknown, fn: typeof handler) => {
        if (name === 'synth_chart_brief_get') handler = fn
      },
    } as unknown as McpServer

    const principal: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'client' } as Principal
    registerP1SynthesisTools(mockServer, principal)
  })

  it('serves ZERO occurrences of denied/confirmed on n_support=0 rows, in both ranked_themes and verdict_summary', async () => {
    const result = await handler({ chart_id: CHART_ID, depth: 'standard' })
    expect(result.isError).toBeFalsy()
    const parsed = JSON.parse(result.content[0]!.text) as {
      content: {
        ranked_themes: { weaknesses: string[]; open_questions: string[]; strengths: string[] }
        verdict_summary: Array<{ insight_id: string; statement: string; n_support: number }>
      }
    }
    const { ranked_themes, verdict_summary } = parsed.content

    // 1. ranked_themes: no sentence for a zero-support insight_id may carry denied/confirmed.
    const allSentences = [...ranked_themes.weaknesses, ...ranked_themes.open_questions, ...ranked_themes.strengths]
    for (const zeroRow of ZERO_SUPPORT_ROWS) {
      const nameFragment = zeroRow.statement.split(':')[0]!
      const matching = allSentences.filter(s => s.includes(nameFragment))
      expect(matching.length).toBeGreaterThan(0)
      for (const sentence of matching) {
        expect(sentence).not.toMatch(/\bdenied\b/i)
        expect(sentence).not.toMatch(/\bconfirmed\b/i)
        expect(sentence).toContain('not_yet_assessed')
      }
    }

    // 2. verdict_summary[].statement: raw statement text must also be masked for n_support=0 rows.
    for (const row of verdict_summary) {
      if (row.n_support === 0) {
        expect(row.statement).not.toMatch(/\bdenied\b/i)
        expect(row.statement).not.toMatch(/\bconfirmed\b/i)
        expect(row.statement).toContain('not_yet_assessed')
      }
    }

    // 3. Evidence-conditioned, not a blanket rename: n_support=5 rows KEEP their verb —
    //    "Marriage"/"Major Financial Loss" both carry real supporting evidence in production.
    const supportedStatements = verdict_summary.filter(r => r.n_support > 0).map(r => r.statement)
    expect(supportedStatements.some(s => /\bdenied\b/i.test(s))).toBe(true)
    const marriageSentence = allSentences.find(s => s.startsWith('Marriage:'))
    expect(marriageSentence).toBeDefined()
    expect(marriageSentence).toMatch(/\bdenied\b/i)
  })
})
