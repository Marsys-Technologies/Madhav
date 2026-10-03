/**
 * TI-l5-insight-prefix-label-001 — the pre-fix-generation detector and its served wiring.
 *
 * Fixtures mirror the stored rows on the canonical chart (read-only snapshot, 2026-10-03): v1.0 insight
 * units graded 'empirical' with leakage_status 'clean', v1.0 grammar rows, v2.0 retrodiction discoveries
 * without the F-148 markers, mi_pramana_v2.0 calibration rows with base_rate 0.1. The post-fix side is
 * built from the version constants the CURRENT writer sources stamp (parsed from the Python files), so
 * "a rebuild by a post-fix writer classifies post-fix" is tested, not asserted.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))

import * as G from '../prefix_generation'
import { queryInsightsCapability } from '../query_insights'
import { queryManifestationGrammarCapability } from '../query_manifestation_grammar'
import { queryMimamsaDiscoveriesCapability } from '../query_mimamsa_discoveries'
import { queryCalibrationCapability } from '../query_calibration'
import { queryLoadBearingCapability } from '../query_load_bearing'

type Rec = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
const HERE = path.dirname(fileURLToPath(import.meta.url))
const REPO = path.resolve(HERE, '../../../../../../../../')
const WRITERS = path.join(REPO, 'platform/python-sidecar/pipeline/orchestrator/writers')
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

function writerConst(file: string, name: string): string {
  const src = fs.readFileSync(path.join(WRITERS, file), 'utf8')
  const m = new RegExp(`^${name}\\s*=\\s*"([^"]+)"`, 'm').exec(src)
  if (!m) throw new Error(`${name} not found in ${file}`)
  return String(m[1])
}

// ---- stored (pre-fix) row shapes -------------------------------------------------------------
const PRE_UNIT_GRAMMAR = {
  insight_id: 'gram_transition_ch_transition_verbal_0', insight_type: 'manifestation_grammar', domain: 'transition',
  statement: "For transition events, the 'ch_transition_verbal' channel fires with 0% propensity (n=55, empirical learning).",
  rank_consequence: 0, confidence_band: null, n_support: 55, leakage_status: 'clean', evidence_grade: 'empirical',
  surface_formula_version: 'mi_darshana_v1.0', provenance_chain: { channel: 'ch_transition_verbal', propensity: 0, grade: null },
}
const PRE_UNIT_RETRO = {
  insight_id: 'disc_retro_x', insight_type: 'retrodiction', domain: 'career',
  statement: 'Blind retrodiction for 732a4119 (career) with T−90d cutoff 2026-01-08. Top-k anchors matched: 1.',
  rank_consequence: 0, n_support: 1, leakage_status: 'clean', evidence_grade: 'prior_only', surface_formula_version: 'mi_darshana_v1.0',
}
const PRE_UNIT_LB = {
  insight_id: 'lb_concl_fam_yoga', insight_type: 'load_bearing', domain: null,
  statement: "Signal 'fam_yoga' is load_bearing for conclusion 'concl_fam_yoga' (sensitivity=0.70). Removing this signal would materially alter the reading.",
  rank_consequence: 0.7, n_support: 1, leakage_status: 'clean', evidence_grade: 'structural', surface_formula_version: 'mi_darshana_v1.0',
}
const PRE_UNIT_EMPIRICAL_LAW = {
  insight_id: 'disc_law', insight_type: 'emergent_law', domain: 'career', statement: 'x (mean=0.31, n=7)',
  rank_consequence: 0.31, n_support: 7, leakage_status: 'clean', evidence_grade: 'empirical', surface_formula_version: 'mi_darshana_v1.0',
}
const PRE_GRAMMAR = { origin_ref: 'o', channel_id: 'c', evidence_grade: 'empirical', grammar_formula_version: 'mi_sambandha_v1.0', channel_propensity: 0, scored_count: 0 }
const PRE_RETRO = { discovery_id: 'retro_1', discovery_class: 'retrodiction', discovery_formula_ver: 'mi_pariksha_v2.0', evidence_refs: [], statement: PRE_UNIT_RETRO.statement }
const PRE_LAW = { discovery_id: 'law_1', discovery_class: 'emergent_law', discovery_formula_ver: 'mi_pariksha_v2.0', evidence_refs: { signal_id: 's' }, statement: 'x' }
const PRE_CAL_GROUPS = [{ scoring_formula_version: 'mi_pramana_v2.0', base_rate_is_null: false, n: 57 }]

// ---- post-fix row shapes, stamped with what the CURRENT writers stamp -------------------------
const V_DARSHANA = writerConst('mi_darshana.py', 'SURFACE_FORMULA_VERSION')
const V_SAMBANDHA = writerConst('mi_sambandha.py', 'GRAMMAR_FORMULA_VERSION')
const V_DISC = writerConst('mi_pariksha.py', 'DISCOVERY_FORMULA_VER')
const V_RETRO = writerConst('mi_pariksha.py', 'RETRODICTION_FORMULA_VER')
const V_PRAMANA = writerConst('mi_pramana.py', 'SCORING_FORMULA_VERSION')
const POST_UNIT = { ...PRE_UNIT_GRAMMAR, surface_formula_version: V_DARSHANA, leakage_status: 'not_assessed', statement: 'x' }
const POST_GRAMMAR = { ...PRE_GRAMMAR, grammar_formula_version: V_SAMBANDHA }
const POST_RETRO = { ...PRE_RETRO, discovery_formula_ver: V_RETRO, evidence_refs: { cutoff_enforced: false, window_containment_checked: false } }
const POST_LAW = { ...PRE_LAW, discovery_formula_ver: V_DISC, evidence_refs: { n_scored_matches: 6 } }

describe('detector: classifies the stored pre-fix generation as pre-fix', () => {
  it('insight units, grammar, discoveries and the calibration set from the live shapes are all pre-fix', () => {
    for (const u of [PRE_UNIT_GRAMMAR, PRE_UNIT_RETRO, PRE_UNIT_LB, PRE_UNIT_EMPIRICAL_LAW]) {
      expect(G.classifyInsightUnit(u)).toMatchObject({ pre_fix: true, reason: 'stamp_below_floor' })
    }
    expect(G.classifyGrammarRow(PRE_GRAMMAR)).toMatchObject({ pre_fix: true, reason: 'stamp_below_floor' })
    expect(G.classifyDiscovery(PRE_RETRO)).toMatchObject({ pre_fix: true, reason: 'stamp_below_floor' })
    expect(G.classifyDiscovery(PRE_LAW)).toMatchObject({ pre_fix: true, reason: 'stamp_below_floor' })
    expect(G.classifyCalibrationSet(PRE_CAL_GROUPS)).toMatchObject({ pre_fix: true, reason: 'fix_marker_absent' })
  })

  it('the floors sit strictly above what the pre-fix rows carry', () => {
    const f = G.GENERATION_FLOORS
    expect([f.insight_unit.major, f.insight_unit.minor]).not.toEqual([1, 0])
    expect(f.insight_unit.minor).toBeGreaterThan(0)
    expect(f.manifestation_grammar.minor).toBeGreaterThan(0)
    expect(f.discovery_emergent_law.minor).toBeGreaterThan(0)
    expect(f.discovery_retrodiction.minor).toBeGreaterThan(f.discovery_emergent_law.minor)
  })
})

describe('detector: rows from a rebuild by the CURRENT (post-fix) writers classify post-fix', () => {
  it('each floor is satisfied by the version the writer source stamps today', () => {
    expect(G.classifyInsightUnit(POST_UNIT).pre_fix).toBe(false)
    expect(G.classifyGrammarRow(POST_GRAMMAR).pre_fix).toBe(false)
    expect(G.classifyDiscovery(POST_RETRO).pre_fix).toBe(false)
    expect(G.classifyDiscovery(POST_LAW).pre_fix).toBe(false)
    // mi_pramana: label unchanged (v2.0) after the A-F-24 fix; the fix's own stamp (base_rate NULL) proves it.
    expect(V_PRAMANA).toBe('mi_pramana_v2.0')
    expect(G.classifyCalibrationSet([{ scoring_formula_version: V_PRAMANA, base_rate_is_null: true, n: 57 }]).pre_fix).toBe(false)
  })

  it('the pre-fix and post-fix stamps differ only because the writer sources moved (guards the floors against drift)', () => {
    const parse = (v: string) => /_v(\d+)\.(\d+)$/.exec(v)!.slice(1).map(Number) as [number, number]
    const ge = (a: [number, number], b: { major: number; minor: number }) => a[0] > b.major || (a[0] === b.major && a[1] >= b.minor)
    expect(ge(parse(V_DARSHANA), G.GENERATION_FLOORS.insight_unit)).toBe(true)
    expect(ge(parse(V_SAMBANDHA), G.GENERATION_FLOORS.manifestation_grammar)).toBe(true)
    expect(ge(parse(V_DISC), G.GENERATION_FLOORS.discovery_emergent_law)).toBe(true)
    expect(ge(parse(V_RETRO), G.GENERATION_FLOORS.discovery_retrodiction)).toBe(true)
  })

  it('the mi_pramana source still writes base_rate NULL when no rate exists (the marker the rule leans on)', () => {
    const src = fs.readFileSync(path.join(WRITERS, 'mi_pramana.py'), 'utf8')
    expect(src).toMatch(/round\(base_rate, 4\) if base_rate is not None else None/)
    expect(src).toMatch(/def _load_base_rates[\s\S]*?return \{\}/)
  })

  it('a post-fix row is served without a downgrade or rewrite', () => {
    const out = G.labelInsightUnit({ ...POST_UNIT, evidence_grade: 'empirical' })
    expect(out['generation_status']).toBe('post_fix')
    expect(out['evidence_grade']).toBe('empirical')
    expect(out['statement']).toBe('x')
    expect(out['generation_label']).toBeUndefined()
  })
})

describe('detector: fail-closed', () => {
  it.each([
    ['missing label', { ...POST_UNIT, surface_formula_version: undefined }, 'stamp_missing'],
    ['null label', { ...POST_UNIT, surface_formula_version: null }, 'stamp_missing'],
    ['blank label', { ...POST_UNIT, surface_formula_version: '  ' }, 'stamp_missing'],
    ['unparseable label', { ...POST_UNIT, surface_formula_version: 'v1.2' }, 'stamp_unparseable'],
    ['non-string label', { ...POST_UNIT, surface_formula_version: 12 }, 'stamp_unparseable'],
    ['foreign writer label', { ...POST_UNIT, surface_formula_version: 'mi_sambandha_v1.2' }, 'stamp_wrong_writer'],
    ['label below the floor', { ...POST_UNIT, surface_formula_version: 'mi_darshana_v1.1' }, 'stamp_below_floor'],
    ["post label but leakage 'clean'", { ...POST_UNIT, leakage_status: 'clean' }, 'fix_marker_absent'],
  ])('unit: %s -> pre-fix (%s)', (_n, row, reason) => {
    expect(G.classifyInsightUnit(row as Record<string, unknown>)).toMatchObject({ pre_fix: true, reason })
  })

  it('discoveries: post label without the fix marker, and an unknown class, are pre-fix', () => {
    expect(G.classifyDiscovery({ ...POST_RETRO, evidence_refs: {} })).toMatchObject({ pre_fix: true, reason: 'fix_marker_absent' })
    expect(G.classifyDiscovery({ ...POST_RETRO, evidence_refs: null })).toMatchObject({ pre_fix: true, reason: 'fix_marker_absent' })
    expect(G.classifyDiscovery({ ...POST_LAW, evidence_refs: { n_scored_matches: '6' } })).toMatchObject({ pre_fix: true, reason: 'fix_marker_absent' })
    expect(G.classifyDiscovery({ ...POST_LAW, discovery_class: 'novel_class' })).toMatchObject({ pre_fix: true, reason: 'unknown_row_class' })
  })

  it('calibration set: failed probe, empty set, any pre-fix group -> pre-fix', () => {
    expect(G.classifyCalibrationSet(null)).toMatchObject({ pre_fix: true, reason: 'generation_probe_unavailable' })
    expect(G.classifyCalibrationSet([])).toMatchObject({ pre_fix: true, reason: 'stamp_missing' })
    expect(G.classifyCalibrationSet([
      { scoring_formula_version: 'mi_pramana_v2.0', base_rate_is_null: true },
      { scoring_formula_version: 'mi_pramana_v2.0', base_rate_is_null: false },
    ]).pre_fix).toBe(true)
    expect(G.classifyCalibrationSet([{ scoring_formula_version: 'mi_pramana_v1.9', base_rate_is_null: true }]).pre_fix).toBe(true)
  })

  it('a future mi_pramana that derives real base rates must bump the label; v2.1+ is accepted with a non-null rate', () => {
    expect(G.classifyCalibrationSet([{ scoring_formula_version: 'mi_pramana_v2.1', base_rate_is_null: false }]).pre_fix).toBe(false)
  })

  it('summary treats a row with no generation_status as pre-fix', () => {
    const s = G.summarizeGeneration([{ a: 1 }, { generation_status: 'post_fix' }], ['insight_unit'])
    expect(s.pre_fix_rows).toBe(1)
    expect(s.flags).toEqual(['l5_rows_pre_fix_generation'])
  })
})

describe('relabelling is stricter-only', () => {
  it('pre-fix empirical -> unvalidated_prefix with the stored grade kept; nothing is ever raised to empirical', () => {
    const grades = ['empirical', 'assignment_only', 'prior_only', 'structural', 'unvalidated_prefix', undefined, 'weird']
    for (const g of grades) {
      for (const base of [PRE_UNIT_GRAMMAR, POST_UNIT]) {
        const out = G.labelInsightUnit({ ...base, evidence_grade: g })
        if (g === 'empirical' && out['generation_status'] === 'pre_fix_unvalidated') {
          expect(out['evidence_grade']).toBe('unvalidated_prefix')
          expect(out['evidence_grade_stored']).toBe('empirical')
        } else {
          expect(out['evidence_grade']).toBe(g)
        }
        if (g !== 'empirical') expect(out['evidence_grade']).not.toBe('empirical')
      }
    }
  })

  it("rewrites the 0%-propensity 'empirical learning' wording and the 'Blind retrodiction' wording, only for pre-fix rows", () => {
    const g = G.labelInsightUnit(PRE_UNIT_GRAMMAR)
    expect(String(g['statement'])).toContain('pre-fix generation, not validated')
    expect(String(g['statement'])).not.toMatch(/empirical learning/i)
    expect(String(g['generation_label'])).toContain('pre-fix generation, not validated')
    const r = G.labelInsightUnit(PRE_UNIT_RETRO)
    expect(String(r['statement'])).not.toContain('Blind retrodiction')
    expect(String(r['statement'])).toContain('declared-but-unenforced')
    const post = G.labelInsightUnit({ ...POST_UNIT, statement: 'Blind retrodiction stays as stored on a post-fix row' })
    expect(post['statement']).toBe('Blind retrodiction stays as stored on a post-fix row')
  })

  it('load_bearing is labelled in every generation (no validated generation exists)', () => {
    const post = G.labelInsightUnit({ ...PRE_UNIT_LB, surface_formula_version: V_DARSHANA, leakage_status: 'not_assessed' })
    expect(post).toMatchObject({ generation_status: 'pre_fix_unvalidated', generation_reason: 'no_validated_generation_exists' })
    expect(String(post['statement'])).not.toContain('Removing this signal would materially')
  })

  it('does not mutate its input', () => {
    const frozen = Object.freeze({ ...PRE_UNIT_GRAMMAR })
    expect(() => G.labelInsightUnit(frozen)).not.toThrow()
    expect(frozen.evidence_grade).toBe('empirical')
  })
})

describe('mirror in platform-mcp is byte-identical (platform-mcp cannot import platform sources)', () => {
  it('l5_prefix_generation.ts === prefix_generation.ts', () => {
    const a = fs.readFileSync(path.join(HERE, '../prefix_generation.ts'), 'utf8')
    const b = fs.readFileSync(path.join(REPO, 'platform-mcp/src/lib/l5_prefix_generation.ts'), 'utf8')
    expect(b).toBe(a)
  })
})

describe('only the intended L5 surfaces use the detector (no change for non-affected tools)', () => {
  it('importers of prefix_generation are exactly the six served L5 query files', () => {
    const dir = path.join(HERE, '..')
    const importers = fs.readdirSync(dir).filter(f => f.endsWith('.ts') && f !== 'prefix_generation.ts')
      .filter(f => /from '\.\/prefix_generation'/.test(fs.readFileSync(path.join(dir, f), 'utf8'))).sort()
    expect(importers).toEqual([
      'query_calibration.ts', 'query_insight_embeddings.ts', 'query_insights.ts',
      'query_load_bearing.ts', 'query_manifestation_grammar.ts', 'query_mimamsa_discoveries.ts',
    ])
  })
})

describe('served handlers', () => {
  beforeEach(() => { queryMock.mockReset(); queryMock.mockResolvedValue({ rows: [{ total: '1' }] }) })
  afterEach(() => vi.restoreAllMocks())

  it('query_insights: 31-style pre-fix empirical units are never served as empirical, flagged, relabelled, numerics suppressed', async () => {
    queryMock.mockResolvedValueOnce({ rows: [PRE_UNIT_GRAMMAR, PRE_UNIT_EMPIRICAL_LAW, PRE_UNIT_RETRO, PRE_UNIT_LB] })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const res = await queryInsightsCapability.handler({ chart_id: CHART }, undefined) as { content: Rec }
    const c = res.content
    expect(c.evidence_grade_counts).toEqual({ unvalidated_prefix: 2, prior_only: 1, structural: 1 })
    expect(c.evidence_grade_counts.empirical).toBeUndefined()
    expect(c.generation_flags).toEqual(['l5_rows_pre_fix_generation'])
    expect(c.generation_disclosure).toMatchObject({ pre_fix_rows: 4, post_fix_rows: 0, empirical_downgraded_rows: 2 })
    expect(c.evidence_grade_legend.unvalidated_prefix).toMatch(/pre-fix generation, not validated/)
    const g = c.insight_units[0]
    expect(g.evidence_grade).toBe('unvalidated_prefix')
    expect(g.rank_consequence).toBeNull()
    expect(g.statement).not.toMatch(/fires with 0% propensity/)
    expect(g.statement).toContain('pre-fix generation, not validated')
    expect(g.statement).not.toMatch(/empirical learning/i)
    expect(g.provenance_chain.propensity).toBeNull()
    expect(c.insight_units[2].statement).not.toContain('Blind retrodiction')
    expect(c.insight_units[3].statement).not.toContain('Removing this signal would materially')
    for (const u of c.insight_units) expect(u.generation_status).toBe('pre_fix_unvalidated')
  })

  it('query_insights: a post-fix empirical unit keeps its grade and numbers (no flag)', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ ...POST_UNIT, insight_type: 'emergent_law', evidence_grade: 'empirical', rank_consequence: 0.27, statement: 'mean credit=0.27' }] })
    queryMock.mockResolvedValueOnce({ rows: [{}] })
    const res = await queryInsightsCapability.handler({ chart_id: CHART }, undefined) as { content: Rec }
    expect(res.content.insight_units[0]).toMatchObject({ evidence_grade: 'empirical', rank_consequence: 0.27, generation_status: 'post_fix' })
    expect(res.content.generation_flags).toEqual([])
  })

  it('query_manifestation_grammar: pre-fix grammar rows lose the empirical grade; values untouched', async () => {
    queryMock.mockResolvedValueOnce({ rows: [PRE_GRAMMAR, POST_GRAMMAR] })
    const res = await queryManifestationGrammarCapability.handler({ chart_id: CHART }, undefined) as { content: Rec }
    expect(res.content.grammar_rows[0]).toMatchObject({ evidence_grade: 'unvalidated_prefix', evidence_grade_stored: 'empirical', channel_propensity: 0 })
    expect(res.content.grammar_rows[1]).toMatchObject({ evidence_grade: 'empirical', generation_status: 'post_fix' })
    expect(res.content.generation_flags).toEqual(['l5_rows_pre_fix_generation'])
  })

  it("query_mimamsa_discoveries: stored 'Blind retrodiction' wording is relabelled for pre-fix rows only", async () => {
    queryMock.mockResolvedValueOnce({ rows: [PRE_RETRO, { ...POST_RETRO, statement: 'Retrodiction (post-fix text)' }] })
    const res = await queryMimamsaDiscoveriesCapability.handler({ chart_id: CHART }, undefined) as { content: Rec }
    expect(res.content.rows[0].statement).not.toContain('Blind retrodiction')
    expect(res.content.rows[0].generation_status).toBe('pre_fix_unvalidated')
    expect(res.content.rows[1].generation_status).toBe('post_fix')
    expect(res.content.rows[1].statement).toBe('Retrodiction (post-fix text)')
  })

  it('query_calibration: bins derived from a pre-fix calibration set are downgraded; failed probe fails closed', async () => {
    const bins = [{ stratum_key: 'a', evidence_grade: 'empirical', held_out_validity: 'pass', n: 7 }, { stratum_key: 'b', evidence_grade: 'prior_only', held_out_validity: 'insufficient_n', n: 3 }]
    const plan = (gen: unknown) => {
      queryMock.mockReset()
      queryMock.mockResolvedValueOnce({ rows: [] })
      queryMock.mockResolvedValueOnce({ rows: bins })
      queryMock.mockResolvedValueOnce({ rows: [] })
      queryMock.mockResolvedValueOnce({ rows: [] })
      if (gen === 'fail') queryMock.mockRejectedValueOnce(new Error('probe down'))
      else queryMock.mockResolvedValueOnce({ rows: gen })
    }
    plan(PRE_CAL_GROUPS)
    let res = await queryCalibrationCapability.handler({ chart_id: CHART }, undefined) as { content: Rec }
    expect(res.content.reliability_curve[0]).toMatchObject({ evidence_grade: 'unvalidated_prefix', held_out_validity: 'unvalidated_prefix', evidence_grade_stored: 'empirical' })
    expect(res.content.reliability_curve[1]).toMatchObject({ evidence_grade: 'prior_only', held_out_validity: 'insufficient_n' })
    expect(res.content.generation_flags).toEqual(['l5_rows_pre_fix_generation'])
    expect(res.content.generation_disclosure.calibration_set).toMatchObject({ pre_fix: true, reason: 'fix_marker_absent' })
    plan('fail')
    res = await queryCalibrationCapability.handler({ chart_id: CHART }, undefined) as { content: Rec }
    expect(res.content.reliability_curve[0].evidence_grade).toBe('unvalidated_prefix')
    expect(res.content.generation_disclosure.calibration_set.reason).toBe('generation_probe_unavailable')
    plan([{ scoring_formula_version: 'mi_pramana_v2.0', base_rate_is_null: true, n: 57 }])
    res = await queryCalibrationCapability.handler({ chart_id: CHART }, undefined) as { content: Rec }
    expect(res.content.reliability_curve[0]).toMatchObject({ evidence_grade: 'empirical', held_out_validity: 'pass', generation_status: 'post_fix' })
    expect(res.content.generation_flags).toEqual([])
  })

  it('query_load_bearing: rows are labelled, values untouched', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ conclusion_id: 'c', signal_id: 'fam_yoga', sensitivity: 0.7, role: 'load_bearing', formula_version: 'mi_adhilepa_v1.0' }] })
    const res = await queryLoadBearingCapability.handler({ chart_id: CHART }, undefined) as { content: Rec }
    expect(res.content.rows[0]).toMatchObject({ sensitivity: 0.7, role: 'load_bearing', generation_reason: 'no_validated_generation_exists' })
    expect(res.content.generation_flags).toEqual(['l5_rows_pre_fix_generation'])
  })
})
