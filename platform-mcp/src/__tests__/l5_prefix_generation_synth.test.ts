/**
 * TI-l5-insight-prefix-label-001 — platform-mcp edge of the pre-fix-generation label.
 *
 * synth_chart_brief_get reads mimamsa_insight_units directly (it does not go through
 * marsys://tool/L5/query_insights), so the same detector (byte-identical mirror of the platform module,
 * parity-tested in platform) is applied to its rows: a stored 'empirical' grade from the pre-fix
 * generation is never served as empirical, and the 'empirical learning' / 'Blind retrodiction' /
 * 'Removing this signal ...' wording is relabelled. mimamsa_insight_get keeps its (stricter) layer
 * constants and states that the unit-level grade governs.
 * Network is mocked; no DB or platform server.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { registerP1SynthesisTools } from '../tools/register_p1_synthesis.js'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

const PRE = { surface_formula_version: 'mi_darshana_v1.0', leakage_status: 'clean' }
const POST = { surface_formula_version: 'mi_darshana_v1.2', leakage_status: 'not_assessed' }
const base = { domain: 'career', question_lens: null, rank_consequence: 0.4, confidence_band: null, is_negative_knowledge: false }
const ROWS = [
  { ...base, ...PRE, insight_id: 'v1', insight_type: 'verdict_object', statement: 'Career: promised (grade 8.8/10). Strong evidence.', n_support: 5, evidence_grade: 'structural' },
  { ...base, ...PRE, insight_id: 'co_pre', insight_type: 'calibrated_outlook', statement: 'In predictions scored [0.6, 0.7), the observed outcome rate is 28.6% across 7 events (evidence: empirical).', n_support: 9, evidence_grade: 'empirical' },
  { ...base, ...POST, insight_id: 'co_post', insight_type: 'calibrated_outlook', statement: 'In predictions scored [0.6, 0.7), the observed outcome rate is 28.6% across 7 events (evidence: empirical).', n_support: 9, evidence_grade: 'empirical' },
  { ...base, ...PRE, insight_id: 'v_emp', insight_type: 'verdict_object', question_lens: 'wealth', statement: 'Wealth: promised (grade 7.5/10). Strong evidence.', n_support: 5, evidence_grade: 'empirical' },
  { ...base, ...PRE, insight_id: 'lb', insight_type: 'load_bearing', statement: "Signal 'fam_yoga' is load_bearing for conclusion 'c' (sensitivity=0.70). Removing this signal would materially alter the reading.", n_support: 1, evidence_grade: 'structural' },
]

function jsonResponse(body: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) })
}
type Handler = (args: Record<string, unknown>) => Promise<{ content: Array<{ type: string; text: string }>; isError?: boolean }>

describe('platform-mcp: pre-fix generation label', () => {
  const handlers: Record<string, Handler> = {}
  beforeEach(() => {
    mockFetch.mockReset()
    mockFetch.mockImplementation((url: string, init?: { body?: string }) => {
      if (url.includes('/api/mcp/authz')) return jsonResponse({ authorized: true })
      if (url.includes('/api/retrieval/capability')) {
        return jsonResponse({ ok: true, content: { content: {
          chart_id: CHART_ID, insight_units: [], generation_flags: ['l5_rows_pre_fix_generation'],
          generation_disclosure: { pre_fix_rows: 4 },
        } } })
      }
      if (url.includes('/api/mcp/db/query')) {
        const body = init?.body ? JSON.parse(init.body) as { sql: string } : { sql: '' }
        if (body.sql.includes('FROM mimamsa_insight_units')) {
          // fail-closed probe: the detector's second marker column must be selected
          expect(body.sql).toContain('leakage_status')
          expect(body.sql).toContain('surface_formula_version')
          return jsonResponse({ rows: ROWS })
        }
        if (body.sql.includes('FROM bodha_discoveries')) return jsonResponse({ rows: [] })
      }
      return jsonResponse({})
    })
    const server = { tool: (name: string, _d: unknown, _s: unknown, fn: Handler) => { handlers[name] = fn } } as unknown as McpServer
    registerP1SynthesisTools(server, { user_uid: 'u', key_id: 'k', role: 'client' } as Principal)
  })

  it('synth_chart_brief_get: pre-fix empirical row is downgraded, post-fix empirical row is not; flags + disclosure present', async () => {
    const r = await handlers['synth_chart_brief_get']!({ chart_id: CHART_ID, depth: 'standard' })
    expect(r.isError).toBeFalsy()
    const c = (JSON.parse(r.content[0]!.text) as { content: Record<string, any> }).content
    const strata = c.calibration_strata as Array<Record<string, any>>
    const pre = strata.find(s => s.insight_id === 'co_pre')!
    const post = strata.find(s => s.insight_id === 'co_post')!
    expect(pre.evidence_grade).toBe('unvalidated_prefix')
    expect(pre.evidence_grade_stored).toBe('empirical')
    expect(pre.generation_status).toBe('pre_fix_unvalidated')
    expect(post.evidence_grade).toBe('empirical')
    expect(post.generation_status).toBe('post_fix')
    // MED-2: the pre-fix outlook neither serves the rate nor keeps the stored 'evidence: empirical' wording
    expect(String(pre.statement)).not.toMatch(/28\.6|evidence: empirical/)
    expect(String(pre.statement)).toContain('pre-fix generation, not validated')
    expect(String(post.statement)).toContain('28.6% across 7 events (evidence: empirical)')
    expect(c.generation_flags).toEqual(['l5_rows_pre_fix_generation'])
    expect(c.generation_disclosure).toMatchObject({ pre_fix_rows: 4, post_fix_rows: 1, empirical_downgraded_rows: 2, structural_proxy_rows: 1 })
    const lb = (c.load_bearing_signals as Array<Record<string, any>>)[0]!
    expect(lb.statement).not.toContain('Removing this signal would materially alter the reading.')
    expect(lb.statement).toContain('structural proxy only')
    expect(lb.claim_status).toBe('structural_proxy_only')
    // verdict rows are not rewritten (only labelled); layer constants stay (stricter)
    const v = (c.verdict_summary as Array<Record<string, any>>)[0]!
    expect(v.statement).toContain('promised (grade 8.8/10)')
    expect(c.calibration_mode).toBe('STRUCTURAL')
    // a pre-fix verdict row whose stored grade was 'empirical' is hedged in the narrated themes
    const themes = c.ranked_themes as { strengths: string[]; weaknesses: string[]; open_questions: string[] }
    const sentence = [...themes.strengths, ...themes.weaknesses, ...themes.open_questions].find(t => t.startsWith('Wealth'))
    expect(sentence).toContain('pre-fix generation, not validated')
  })

  it('mimamsa_insight_get: layer constants stay prior_only/STRUCTURAL, note defers to unit-level grade, inner disclosure passes through', async () => {
    const r = await handlers['mimamsa_insight_get']!({ chart_id: CHART_ID })
    const c = (JSON.parse(r.content[0]!.text) as { content: Record<string, any> }).content
    expect(c.calibration_status).toBe('prior_only')
    expect(c.mode).toBe('STRUCTURAL')
    expect(c.note).toContain('unvalidated_prefix')
    expect(c.generation_flags).toEqual(['l5_rows_pre_fix_generation'])
    expect(c.generation_disclosure).toEqual({ pre_fix_rows: 4 })
  })
})
