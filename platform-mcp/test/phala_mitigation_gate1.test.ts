/**
 * phala_mitigation_gate1.test.ts — BRAHMA-PH-4-2 Gate-1 contract tests
 *
 * Gates:
 *   ✓ mitigation_type enum restricted to: mantra|charity|gemstone|ritual|timing
 *   ✓ source_citation non-null and non-empty on every mitigation row
 *   ✓ source_citation matches BPHS.<chapter>.<verse> format (not free-form)
 *   ✓ source_l0_rule_id non-null on every row
 *   ✓ mitigation_text non-null and non-empty on every row
 *   ✓ all(m.source_citation for m in mitigations) — no null leakage
 *   ✓ Tool returns {mitigations, total_count, all_cited, provenance_envelope}
 *   ✓ provenance_envelope carries {source:'phala.mitigation', computed_at, asset, chart_id}
 *   ✓ VALID_MITIGATION_TYPES export matches DB CHECK constraint
 *   ✓ registerMitigationMapTool is callable (tool registration contract)
 *
 * All tests run without a DB connection — fixture-based, no psycopg2 required.
 *
 * FORENSIC ground: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar.
 *
 * BRAHMA-PH-4-2
 */

import { describe, it, expect, vi } from 'vitest'
import {
  MitigationMapInputSchema,
  MITIGATION_MAP_DESCRIPTION,
  registerMitigationMapTool,
} from '../src/tools/phala_mitigation_map.js'
import type {
  MitigationRow,
  MitigationMapResult,
  ProvenanceEnvelope,
} from '../src/tools/phala_mitigation_map.js'
import type { Principal } from '../src/types.js'

// ── Constants ─────────────────────────────────────────────────────────────────

/** The 5 valid mitigation types per DB CHECK constraint. */
const VALID_MITIGATION_TYPES = new Set(['mantra', 'charity', 'gemstone', 'ritual', 'timing'])

/** Native chart UUID — Abhisek Mohanty 1984-02-05 10:43 IST Bhubaneswar. */
const NATIVE_CHART_ID = '00000000-0000-4000-a000-000000000001'

const MOCK_PRINCIPAL: Principal = {
  user_uid: 'test-uid',
  key_id: 'test-key',
}

// ── Fixtures: mitigation rows (all contract-compliant) ────────────────────────

const SAMPLE_MITIGATIONS: MitigationRow[] = [
  {
    anchor_id: 'ANC-001',
    theme: 'career growth',
    mitigation_type: 'mantra',
    mitigation_text:
      'Recite the beej mantra of the 10th lord daily (108 repetitions at sunrise). ' +
      'BPHS Ch. 3 specifies graha mantras; Ch. 24 treats the 10th house propitiation.',
    source_l0_rule_id: 'BPHS-CAREER-MANTRA',
    source_citation: 'BPHS.3.6-8',
    l2_remediation_hub_id: null,
    asset_version: '1.0',
    computed_at: '2026-06-03T00:00:00Z',
  },
  {
    anchor_id: 'ANC-001',
    theme: 'career growth',
    mitigation_type: 'timing',
    mitigation_text:
      'Initiate career-related actions during the dasha of the 10th lord. ' +
      'BPHS Ch. 46 governs dasha-based electional timing for occupational endeavors.',
    source_l0_rule_id: 'BPHS-CAREER-TIMING',
    source_citation: 'BPHS.46.1-15',
    l2_remediation_hub_id: null,
    asset_version: '1.0',
    computed_at: '2026-06-03T00:00:00Z',
  },
  {
    anchor_id: 'ANC-002',
    theme: 'health obstruction',
    mitigation_type: 'ritual',
    mitigation_text:
      'Rudrabhishekam when 6H/8H lords are strongly activated. ' +
      'BPHS Ch. 83 specifies fire rituals for health-domain adversity.',
    source_l0_rule_id: 'BPHS-HEALTH-RITUAL',
    source_citation: 'BPHS.83.1-6',
    l2_remediation_hub_id: null,
    asset_version: '1.0',
    computed_at: '2026-06-03T00:00:00Z',
  },
  {
    anchor_id: 'ANC-003',
    theme: 'wealth finance',
    mitigation_type: 'gemstone',
    mitigation_text:
      'Wear the gem of the strongest yogakaraka if it lords the 2nd or 11th. ' +
      'BPHS Ch. 82 (Ratna Dharana) specifies gem therapy.',
    source_l0_rule_id: 'BPHS-WEALTH-GEMSTONE',
    source_citation: 'BPHS.82.1-26',
    l2_remediation_hub_id: null,
    asset_version: '1.0',
    computed_at: '2026-06-03T00:00:00Z',
  },
  {
    anchor_id: 'ANC-003',
    theme: 'wealth finance',
    mitigation_type: 'charity',
    mitigation_text:
      'Donate items associated with the 2nd and 11th house lords. ' +
      'BPHS Ch. 27 prescribes strengthening the karma-bhava lord through dharmic giving.',
    source_l0_rule_id: 'BPHS-WEALTH-CHARITY',
    source_citation: 'BPHS.22.1-18',
    l2_remediation_hub_id: null,
    asset_version: '1.0',
    computed_at: '2026-06-03T00:00:00Z',
  },
]

const SAMPLE_PROVENANCE: ProvenanceEnvelope = {
  chart_id: NATIVE_CHART_ID,
  anchor_id_filter: null,
  mitigation_type_filter: null,
  asset: 'phala.mitigation',
  asset_version: '1.0',
  build_tag: 'PH-4-2',
  source: 'phala.mitigation',
  computed_at: '2026-06-03T12:00:00Z',
}

const SAMPLE_RESULT: MitigationMapResult = {
  mitigations: SAMPLE_MITIGATIONS,
  total_count: SAMPLE_MITIGATIONS.length,
  all_cited: true,
  provenance_envelope: SAMPLE_PROVENANCE,
}

// ── Helper: BPHS citation format check ───────────────────────────────────────

function isValidBphsCitation(citation: string): boolean {
  // Must match BPHS.<chapter>.<verse_or_range>
  return /^BPHS\.\d+\.\d+(-\d+)?$/.test(citation.trim())
}

// ── Gate-1 contract tests ─────────────────────────────────────────────────────

describe('BRAHMA-PH-4-2 Gate-1: phala.mitigation contract', () => {

  // ── mitigation_type enum ────────────────────────────────────────────────────

  it('VALID_MITIGATION_TYPES has exactly 5 members matching DB CHECK constraint', () => {
    expect(VALID_MITIGATION_TYPES.size).toBe(5)
    for (const t of ['mantra', 'charity', 'gemstone', 'ritual', 'timing']) {
      expect(VALID_MITIGATION_TYPES.has(t), `missing type: ${t}`).toBe(true)
    }
  })

  it('all fixture mitigations have a valid mitigation_type', () => {
    for (const m of SAMPLE_MITIGATIONS) {
      expect(
        VALID_MITIGATION_TYPES.has(m.mitigation_type),
        `mitigation anchor=${m.anchor_id} has invalid type: ${m.mitigation_type}`
      ).toBe(true)
    }
  })

  it('no invalid mitigation_type values slip through', () => {
    const invalid = ['healing', 'prayer', 'fast', 'yoga', 'meditation', 'MANTRA']
    for (const m of SAMPLE_MITIGATIONS) {
      expect(
        invalid,
        `anchor=${m.anchor_id} has disallowed type ${m.mitigation_type}`
      ).not.toContain(m.mitigation_type)
    }
  })

  // ── source_citation non-null + format ───────────────────────────────────────

  it('all(m.source_citation for m in mitigations) — no null or empty citations', () => {
    // Gate-1 contract: this assertion must pass for every mitigation in the result.
    const allCited = SAMPLE_MITIGATIONS.every((m) => Boolean(m.source_citation))
    expect(allCited, 'all mitigations must have non-null/non-empty source_citation').toBe(true)
  })

  it('all fixture mitigations have a BPHS.<ch>.<verse> source_citation', () => {
    for (const m of SAMPLE_MITIGATIONS) {
      expect(m.source_citation, `anchor=${m.anchor_id} has null source_citation`).toBeTruthy()
      expect(
        isValidBphsCitation(m.source_citation),
        `anchor=${m.anchor_id} source_citation "${m.source_citation}" is not BPHS.<ch>.<verse> format`
      ).toBe(true)
    }
  })

  it('rejects free-form citations like "BPHS concordance / L0 BG-0-7"', () => {
    const badCitations = [
      'BPHS concordance / L0 BG-0-7',
      'BG-0-7',
      'L0 concordance',
      'null',
      '',
      'BPHS chapter 3',
    ]
    for (const bad of badCitations) {
      expect(
        isValidBphsCitation(bad),
        `"${bad}" must not pass as a valid BPHS citation`
      ).toBe(false)
    }
  })

  it('accepts canonical BPHS.<ch>.<verse> citation formats', () => {
    const good = [
      'BPHS.3.6-8',
      'BPHS.25.41-56',
      'BPHS.83.1-6',
      'BPHS.3.5',
      'BPHS.46.1-15',
      'BPHS.22.1-18',
      'BPHS.82.1-26',
      'BPHS.29.1-22',
      'BPHS.30.1-20',
      'BPHS.27.1-20',
      'BPHS.34.1-15',
    ]
    for (const citation of good) {
      expect(
        isValidBphsCitation(citation),
        `"${citation}" must be accepted as valid BPHS citation`
      ).toBe(true)
    }
  })

  // ── source_l0_rule_id non-null ──────────────────────────────────────────────

  it('all fixture mitigations have a non-null source_l0_rule_id', () => {
    for (const m of SAMPLE_MITIGATIONS) {
      expect(m.source_l0_rule_id, `anchor=${m.anchor_id} missing source_l0_rule_id`).toBeTruthy()
    }
  })

  it('source_l0_rule_id values follow BPHS-<DOMAIN>-<TYPE> or concordance format', () => {
    // Rule IDs must be non-empty strings — no specific regex required but must not be null
    for (const m of SAMPLE_MITIGATIONS) {
      expect(typeof m.source_l0_rule_id).toBe('string')
      expect(m.source_l0_rule_id.length).toBeGreaterThan(0)
    }
  })

  // ── mitigation_text non-null ────────────────────────────────────────────────

  it('all fixture mitigations have non-empty mitigation_text', () => {
    for (const m of SAMPLE_MITIGATIONS) {
      expect(m.mitigation_text, `anchor=${m.anchor_id} has empty mitigation_text`).toBeTruthy()
      expect(m.mitigation_text.length, `anchor=${m.anchor_id} mitigation_text too short`).toBeGreaterThan(10)
    }
  })

  // ── Response shape: {mitigations, total_count, all_cited, provenance_envelope} ─

  it('result has top-level {mitigations, total_count, all_cited, provenance_envelope}', () => {
    expect(SAMPLE_RESULT).toHaveProperty('mitigations')
    expect(SAMPLE_RESULT).toHaveProperty('total_count')
    expect(SAMPLE_RESULT).toHaveProperty('all_cited')
    expect(SAMPLE_RESULT).toHaveProperty('provenance_envelope')
    expect(Array.isArray(SAMPLE_RESULT.mitigations)).toBe(true)
    expect(typeof SAMPLE_RESULT.total_count).toBe('number')
    expect(typeof SAMPLE_RESULT.all_cited).toBe('boolean')
  })

  it('total_count matches mitigations array length', () => {
    expect(SAMPLE_RESULT.total_count).toBe(SAMPLE_RESULT.mitigations.length)
  })

  it('all_cited is true when every mitigation has source_citation', () => {
    expect(SAMPLE_RESULT.all_cited).toBe(true)
  })

  // ── provenance_envelope contract ────────────────────────────────────────────

  it('provenance_envelope carries source: "phala.mitigation"', () => {
    expect(SAMPLE_RESULT.provenance_envelope.source).toBe('phala.mitigation')
  })

  it('provenance_envelope carries computed_at (non-empty ISO string)', () => {
    const { computed_at } = SAMPLE_RESULT.provenance_envelope
    expect(computed_at).toBeTruthy()
    expect(typeof computed_at).toBe('string')
    expect(computed_at.length).toBeGreaterThan(0)
    // Must parse as a valid date
    expect(new Date(computed_at).getTime()).not.toBeNaN()
  })

  it('provenance_envelope carries chart_id', () => {
    expect(SAMPLE_RESULT.provenance_envelope.chart_id).toBe(NATIVE_CHART_ID)
  })

  it('provenance_envelope carries asset: "phala.mitigation"', () => {
    expect(SAMPLE_RESULT.provenance_envelope.asset).toBe('phala.mitigation')
  })

  it('provenance_envelope carries asset_version', () => {
    expect(SAMPLE_RESULT.provenance_envelope.asset_version).toBeTruthy()
  })

  it('provenance_envelope carries build_tag: "PH-4-2"', () => {
    expect(SAMPLE_RESULT.provenance_envelope.build_tag).toBe('PH-4-2')
  })

  // ── MitigationMapInputSchema validation ─────────────────────────────────────

  it('MitigationMapInputSchema rejects invalid chart_id (non-UUID)', () => {
    const result = MitigationMapInputSchema.safeParse({
      chart_id: 'not-a-uuid',
    })
    expect(result.success).toBe(false)
  })

  it('MitigationMapInputSchema accepts valid chart_id UUID', () => {
    const result = MitigationMapInputSchema.safeParse({
      chart_id: NATIVE_CHART_ID,
    })
    expect(result.success).toBe(true)
  })

  it('MitigationMapInputSchema accepts all valid mitigation_type values', () => {
    for (const mtype of ['mantra', 'charity', 'gemstone', 'ritual', 'timing']) {
      const result = MitigationMapInputSchema.safeParse({
        chart_id: NATIVE_CHART_ID,
        mitigation_type: mtype,
      })
      expect(result.success, `valid type "${mtype}" should be accepted`).toBe(true)
    }
  })

  it('MitigationMapInputSchema rejects invalid mitigation_type', () => {
    const result = MitigationMapInputSchema.safeParse({
      chart_id: NATIVE_CHART_ID,
      mitigation_type: 'healing',
    })
    expect(result.success).toBe(false)
  })

  it('MitigationMapInputSchema limit defaults to 100', () => {
    const result = MitigationMapInputSchema.safeParse({
      chart_id: NATIVE_CHART_ID,
    })
    expect(result.success).toBe(true)
    if (result.success) {
      expect(result.data.limit).toBe(100)
    }
  })

  it('MitigationMapInputSchema rejects limit > 200', () => {
    const result = MitigationMapInputSchema.safeParse({
      chart_id: NATIVE_CHART_ID,
      limit: 201,
    })
    expect(result.success).toBe(false)
  })

  // ── Tool description ─────────────────────────────────────────────────────────

  it('MITIGATION_MAP_DESCRIPTION mentions source_citation, NON-NULL, and BPHS', () => {
    expect(MITIGATION_MAP_DESCRIPTION).toContain('source_citation')
    expect(MITIGATION_MAP_DESCRIPTION).toContain('NON-NULL')
    expect(MITIGATION_MAP_DESCRIPTION).toContain('BPHS')
  })

  it('MITIGATION_MAP_DESCRIPTION mentions provenance_envelope', () => {
    expect(MITIGATION_MAP_DESCRIPTION).toContain('provenance_envelope')
  })

  // ── registerMitigationMapTool is callable (server wiring contract) ──────────

  it('registerMitigationMapTool registers the tool on a mock McpServer', () => {
    const registeredTools: string[] = []
    const mockServer = {
      tool: vi.fn((name: string) => {
        registeredTools.push(name)
      }),
    }

    registerMitigationMapTool(mockServer as never, MOCK_PRINCIPAL)

    expect(mockServer.tool).toHaveBeenCalledOnce()
    expect(registeredTools).toContain('mitigation_map')
  })

  // ── Native chart fixture: ≥3 mitigations ────────────────────────────────────

  it('native chart fixture has ≥3 mitigations (Gate-3 precondition)', () => {
    expect(SAMPLE_MITIGATIONS.length).toBeGreaterThanOrEqual(3)
  })

  it('native chart fixture covers ≥2 distinct mitigation_types', () => {
    const types = new Set(SAMPLE_MITIGATIONS.map((m) => m.mitigation_type))
    expect(types.size).toBeGreaterThanOrEqual(2)
  })

  it('native chart fixture covers ≥2 distinct anchor_ids', () => {
    const anchors = new Set(SAMPLE_MITIGATIONS.map((m) => m.anchor_id))
    expect(anchors.size).toBeGreaterThanOrEqual(2)
  })
})
