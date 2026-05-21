/**
 * COV-S5 — Unit tests for query_ucn_walk, query_cdlm_lookup, query_rm_walk
 *
 * Gate: ucn_cdlm_rm_parametric_smoke
 *   - Full-dump mode returns non-empty results for each tool
 *   - Seeded mode returns non-empty results for known entries
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

vi.mock('@/lib/db/monitoring-write', () => ({
  writeToolExecutionLog: vi.fn().mockResolvedValue(undefined),
}))

// ---------------------------------------------------------------------------
// Minimal UCN fixture: contains MSR.413, MSR.391, MSR.190 references
// ---------------------------------------------------------------------------
const UCN_FIXTURE = `---
artifact: UCN_v4_0.md
version: 4.1
---

## PART I — BASE NARRATIVE

### I.1 — The Five Foundation Signatures

**Foundation Signature 1: The Mercury Seven-System Convergence**

Seven independent classical systems designate Mercury as primary (MSR.413, confidence 0.98).

**Foundation Signature 2: The Authority-Through-Tension Pattern**

Saturn and Mars share the 7th house. See MSR.391 for the seven-layer 7H significance.

### I.2 — How the Five Signatures Interact

Mercury (FS1) MSR.190 intelligence, analysis, communication.

## Part II — The Soul-Trajectory

Mercury governs the Karakamsa. MSR.413 again referenced here.

## Part V — Career Domain

Career and wealth are linked. MSR.264 wealth mechanism.
`

// ---------------------------------------------------------------------------
// Minimal CDLM fixture: contains CDLM.D1.D1 and CDLM.D1.D2 cells
// ---------------------------------------------------------------------------
const CDLM_FIXTURE = `---
version: 1.3
---

### ROW D1: CAREER → [All Domains]

CDLM.D1.D1:
  row_domain: Career
  col_domain: Career (self-reference)
  linkage_type: mirrors
  primary_mechanism: "10H Capricorn = AL + Saturn AmK"
  msr_anchors: [MSR.390, MSR.413, MSR.339, MSR.349, MSR.117]
  strength: 1.00
  direction: bidirectional
  valence: benefic
  key_finding: "Career is this chart's primary domain."

CDLM.D1.D2:
  row_domain: Career
  col_domain: Wealth
  linkage_type: feeds
  primary_mechanism: "Mercury (10H) career delivers gains; Venus as 2L in 9H"
  msr_anchors: [MSR.413, MSR.264, MSR.311]
  strength: 0.92
  direction: row→col
  valence: benefic
  key_finding: "Career directly feeds wealth."

### ROW D2: WEALTH → [All Domains]

CDLM.D2.D1:
  row_domain: Wealth
  col_domain: Career
  linkage_type: feeds
  primary_mechanism: "Wealth reputation enables career opportunities"
  msr_anchors: [MSR.413, MSR.264]
  strength: 0.88
  direction: row→col
  valence: benefic
  key_finding: "Wealth reputation feeds career leverage."
`

// ---------------------------------------------------------------------------
// Minimal RM fixture: contains RM.01 and RM.02 entries
// ---------------------------------------------------------------------------
const RM_FIXTURE = `---
version: 2.2
---

## §1 — ELEMENT BLOCKS

### RM.01 — Mercury 10H Capricorn (Primary Instrument)

\`\`\`yaml
element: "Mercury Eight-System Convergence"
domains_primary: [D1, D2, D3, D8, D9]
msr_anchors: [MSR.413, MSR.190]
net_resonance: "STRONGLY AMPLIFIED during Mercury MD; protect 6L boundary"
\`\`\`

### RM.02 — Saturn 7H Libra Exalted (Career Lord)

\`\`\`yaml
element: "Saturn exalted 7H + AmK + Sasha Mahapurusha"
domains_primary: [D1, D3]
msr_anchors: [MSR.391, MSR.052]
net_resonance: "STRONGLY AMPLIFIED — quintessential authority architecture (ATT)"
\`\`\`

### RM.03 — Jupiter 9H Sagittarius Own Sign (Dharma Lord)

\`\`\`yaml
element: "Jupiter 9L own sign + 12L + GK Chara Karaka"
domains_primary: [D6, D1, D2, D7]
msr_anchors: [MSR.089, MSR.407]
net_resonance: "STRONGLY AMPLIFIED by dignity; Uccha-Bala weakness requires active dharmic engagement"
\`\`\`
`

// Mock fs to return fixtures
vi.mock('fs', () => ({
  default: {
    readFileSync: (filePath: string, _encoding: string) => {
      if (String(filePath).includes('UCN')) return UCN_FIXTURE
      if (String(filePath).includes('CDLM')) return CDLM_FIXTURE
      if (String(filePath).includes('RM_v2_0')) return RM_FIXTURE
      throw new Error(`Unexpected file read: ${filePath}`)
    },
  },
  readFileSync: (filePath: string, _encoding: string) => {
    if (String(filePath).includes('UCN')) return UCN_FIXTURE
    if (String(filePath).includes('CDLM')) return CDLM_FIXTURE
    if (String(filePath).includes('RM_v2_0')) return RM_FIXTURE
    throw new Error(`Unexpected file read: ${filePath}`)
  },
}))

import { tool as ucnWalkTool } from '@/lib/retrieve/query_ucn_walk'
import { tool as cdlmLookupTool } from '@/lib/retrieve/query_cdlm_lookup'
import { tool as rmWalkTool } from '@/lib/retrieve/query_rm_walk'

// ---------------------------------------------------------------------------
// Shared minimal QueryPlan factory
// ---------------------------------------------------------------------------
function makePlan(overrides: Partial<{ query_text: string }> = {}): import('@/lib/retrieve/types').QueryPlan {
  return {
    query_plan_id: 'test-plan-cov-s5',
    query_text: overrides.query_text ?? 'test query',
    query_class: 'holistic',
    domains: ['career'],
    forward_looking: false,
    audience_tier: 'super_admin',
    tools_authorized: ['query_ucn_walk', 'query_cdlm_lookup', 'query_rm_walk'],
    history_mode: 'research',
    panel_mode: false,
    expected_output_shape: 'structured_data',
    manifest_fingerprint: 'test-fp',
    schema_version: '1.0',
  }
}

// ---------------------------------------------------------------------------
// query_ucn_walk tests
// ---------------------------------------------------------------------------

describe('query_ucn_walk', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('full-dump mode returns non-empty results', async () => {
    const bundle = await ucnWalkTool.retrieve(makePlan(), {})
    expect(bundle.tool_name).toBe('query_ucn_walk')
    expect(bundle.results.length).toBeGreaterThan(0)
  })

  it('full-dump mode extracts MSR signal IDs', async () => {
    const bundle = await ucnWalkTool.retrieve(makePlan(), {})
    const signalIds = bundle.results.map(r => r.signal_id)
    expect(signalIds).toContain('MSR.413')
  })

  it('[ucn_cdlm_rm_parametric_smoke] seeded mode MSR.413 returns non-empty results', async () => {
    const bundle = await ucnWalkTool.retrieve(makePlan(), { seed_signal_id: 'MSR.413' })
    expect(bundle.results.length).toBeGreaterThan(0)
    // Every returned entry should reference MSR.413
    for (const r of bundle.results) {
      expect(r.signal_id).toBe('MSR.413')
    }
  })

  it('[ucn_cdlm_rm_parametric_smoke] seeded mode MSR.391 returns non-empty results', async () => {
    const bundle = await ucnWalkTool.retrieve(makePlan(), { seed_signal_id: 'MSR.391' })
    expect(bundle.results.length).toBeGreaterThan(0)
  })

  it('seeded mode for non-existent signal returns empty results', async () => {
    const bundle = await ucnWalkTool.retrieve(makePlan(), { seed_signal_id: 'MSR.999' })
    expect(bundle.results.length).toBe(0)
  })

  it('bundle has correct structure fields', async () => {
    const bundle = await ucnWalkTool.retrieve(makePlan(), {})
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(typeof bundle.tool_bundle_id).toBe('string')
    expect(typeof bundle.result_hash).toBe('string')
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })

  it('each result carries source_canonical_id = UCN', async () => {
    const bundle = await ucnWalkTool.retrieve(makePlan(), {})
    for (const r of bundle.results) {
      expect(r.source_canonical_id).toBe('UCN')
    }
  })

  it('depth param is accepted without error', async () => {
    await expect(
      ucnWalkTool.retrieve(makePlan(), { seed_signal_id: 'MSR.413', depth: 2 })
    ).resolves.toBeDefined()
  })
})

// ---------------------------------------------------------------------------
// query_cdlm_lookup tests
// ---------------------------------------------------------------------------

describe('query_cdlm_lookup', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('full-dump mode returns non-empty results', async () => {
    const bundle = await cdlmLookupTool.retrieve(makePlan(), {})
    expect(bundle.tool_name).toBe('query_cdlm_lookup')
    expect(bundle.results.length).toBeGreaterThan(0)
  })

  it('[ucn_cdlm_rm_parametric_smoke] domain_a=Career returns non-empty results', async () => {
    const bundle = await cdlmLookupTool.retrieve(makePlan(), { domain_a: 'Career' })
    expect(bundle.results.length).toBeGreaterThan(0)
    for (const r of bundle.results) {
      const entry = JSON.parse(r.content)
      expect(entry.row_domain.toLowerCase()).toContain('career')
    }
  })

  it('[ucn_cdlm_rm_parametric_smoke] signal_id=MSR.413 returns non-empty results', async () => {
    const bundle = await cdlmLookupTool.retrieve(makePlan(), { signal_id: 'MSR.413' })
    expect(bundle.results.length).toBeGreaterThan(0)
    for (const r of bundle.results) {
      const entry = JSON.parse(r.content)
      expect(entry.signal_ids).toContain('MSR.413')
    }
  })

  it('domain_a=Career domain_b=Wealth returns D1.D2 cell', async () => {
    const bundle = await cdlmLookupTool.retrieve(makePlan(), { domain_a: 'Career', domain_b: 'Wealth' })
    expect(bundle.results.length).toBeGreaterThan(0)
    const entry = JSON.parse(bundle.results[0].content)
    expect(entry.domain_pair).toBe('Career→Wealth')
    expect(entry.linkage_type).toBe('feeds')
    expect(entry.strength).toBe('0.92')
  })

  it('parses key_finding correctly', async () => {
    const bundle = await cdlmLookupTool.retrieve(makePlan(), { domain_a: 'Career', domain_b: 'Wealth' })
    const entry = JSON.parse(bundle.results[0].content)
    expect(entry.key_finding).toContain('Career directly feeds wealth')
  })

  it('non-matching filter returns empty results', async () => {
    const bundle = await cdlmLookupTool.retrieve(makePlan(), { domain_a: 'Nonexistent' })
    expect(bundle.results.length).toBe(0)
  })

  it('each result carries source_canonical_id = CDLM', async () => {
    const bundle = await cdlmLookupTool.retrieve(makePlan(), {})
    for (const r of bundle.results) {
      expect(r.source_canonical_id).toBe('CDLM')
    }
  })

  it('bundle has correct structure fields', async () => {
    const bundle = await cdlmLookupTool.retrieve(makePlan(), {})
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })
})

// ---------------------------------------------------------------------------
// query_rm_walk tests
// ---------------------------------------------------------------------------

describe('query_rm_walk', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('full-dump mode returns non-empty results', async () => {
    const bundle = await rmWalkTool.retrieve(makePlan(), {})
    expect(bundle.tool_name).toBe('query_rm_walk')
    expect(bundle.results.length).toBeGreaterThan(0)
  })

  it('full-dump mode returns all 3 RM entries from fixture', async () => {
    const bundle = await rmWalkTool.retrieve(makePlan(), {})
    expect(bundle.results.length).toBe(3)
  })

  it('[ucn_cdlm_rm_parametric_smoke] seeded mode MSR.413 returns RM.01', async () => {
    const bundle = await rmWalkTool.retrieve(makePlan(), { seed_signal_id: 'MSR.413' })
    expect(bundle.results.length).toBeGreaterThan(0)
    const rmIds = bundle.results.map(r => JSON.parse(r.content).rm_id)
    expect(rmIds).toContain('RM.01')
  })

  it('[ucn_cdlm_rm_parametric_smoke] seeded mode MSR.391 returns RM.02', async () => {
    const bundle = await rmWalkTool.retrieve(makePlan(), { seed_signal_id: 'MSR.391' })
    expect(bundle.results.length).toBeGreaterThan(0)
    const rmIds = bundle.results.map(r => JSON.parse(r.content).rm_id)
    expect(rmIds).toContain('RM.02')
  })

  it('seeded mode RM.01 direct ID returns RM.01', async () => {
    const bundle = await rmWalkTool.retrieve(makePlan(), { seed_signal_id: 'RM.01' })
    expect(bundle.results.length).toBeGreaterThan(0)
    const entry = JSON.parse(bundle.results[0].content)
    expect(entry.rm_id).toBe('RM.01')
  })

  it('non-existent seed returns empty results', async () => {
    const bundle = await rmWalkTool.retrieve(makePlan(), { seed_signal_id: 'MSR.999' })
    expect(bundle.results.length).toBe(0)
  })

  it('each result carries source_canonical_id = RM', async () => {
    const bundle = await rmWalkTool.retrieve(makePlan(), {})
    for (const r of bundle.results) {
      expect(r.source_canonical_id).toBe('RM')
    }
  })

  it('strength field is classified correctly for STRONGLY AMPLIFIED', async () => {
    const bundle = await rmWalkTool.retrieve(makePlan(), { seed_signal_id: 'RM.01' })
    const entry = JSON.parse(bundle.results[0].content)
    expect(entry.strength).toBe('STRONGLY_AMPLIFIED')
  })

  it('domains array is parsed for RM.01', async () => {
    const bundle = await rmWalkTool.retrieve(makePlan(), { seed_signal_id: 'RM.01' })
    const entry = JSON.parse(bundle.results[0].content)
    expect(entry.domains).toContain('D1')
    expect(entry.domains).toContain('D2')
  })

  it('bundle has correct structure fields', async () => {
    const bundle = await rmWalkTool.retrieve(makePlan(), {})
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.tool_version).toBe('1.0.0')
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })

  it('depth param is accepted without error', async () => {
    await expect(
      rmWalkTool.retrieve(makePlan(), { seed_signal_id: 'MSR.413', depth: 2 })
    ).resolves.toBeDefined()
  })
})
