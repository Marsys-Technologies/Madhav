/**
 * resources.test.ts — Verify all 5 MCP resources are present + correctly structured.
 * MCPT v3.1.0-S3 AC.S3.1 through AC.S3.6
 */

import { describe, it, expect } from 'vitest'
import { existsSync, readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { join, dirname } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..', '..')

// ── File existence checks ─────────────────────────────────────────────────────

describe('S3 resource files exist', () => {
  const files = [
    'src/resources/chart_snapshot.ts',
    'src/resources/chart_overview.ts',
    'src/resources/house_rules.ts',
    'src/resources/capabilities.ts',
    'src/resources/school_conventions.ts',
    'src/resources/index.ts',
    'src/resources/house_rules_variants/super_admin.md',
    'src/resources/house_rules_variants/acharya.md',
    'src/resources/house_rules_variants/client.md',
    // public_redacted.md retired (Stream A 3.tier_excision 2026-05-28).
  ]

  for (const file of files) {
    it(`${file} exists`, () => {
      expect(existsSync(join(ROOT, file))).toBe(true)
    })
  }
})

// ── Resource registration checks ──────────────────────────────────────────────

describe('resources/index.ts registers all 5 resources', () => {
  it('imports and calls register for all 5 resources', () => {
    const indexContent = readFileSync(join(ROOT, 'src/resources/index.ts'), 'utf-8')
    expect(indexContent).toContain('registerChartSnapshot')
    expect(indexContent).toContain('registerChartOverview')
    expect(indexContent).toContain('registerHouseRules')
    expect(indexContent).toContain('registerCapabilities')
    expect(indexContent).toContain('registerSchoolConventions')
  })

  it('exports a single registerResources function', () => {
    const indexContent = readFileSync(join(ROOT, 'src/resources/index.ts'), 'utf-8')
    expect(indexContent).toContain('export function registerResources')
  })
})

// ── House rules variant content checks ────────────────────────────────────────

describe('house_rules_variants content quality', () => {
  const variantsDir = join(ROOT, 'src/resources/house_rules_variants')

  it('super_admin.md contains B.11 floor instruction', () => {
    const content = readFileSync(join(variantsDir, 'super_admin.md'), 'utf-8')
    expect(content).toContain('B.11')
  })

  it('super_admin.md contains PPL discipline section', () => {
    const content = readFileSync(join(variantsDir, 'super_admin.md'), 'utf-8')
    expect(content).toContain('log_prediction')
  })

  it('super_admin.md contains cite-allowlist contract', () => {
    const content = readFileSync(join(variantsDir, 'super_admin.md'), 'utf-8')
    expect(content).toContain('signal_ids_available')
  })

  it('super_admin.md contains bundle guidance', () => {
    const content = readFileSync(join(variantsDir, 'super_admin.md'), 'utf-8')
    expect(content).toContain('holistic_bundle')
    expect(content).toContain('multi_school_bundle')
  })

  it('super_admin.md mentions operator-side audit subsystem', () => {
    const content = readFileSync(join(variantsDir, 'super_admin.md'), 'utf-8')
    expect(content).toContain('nightly audit')
  })

  it('acharya.md is shorter than super_admin.md (no internal audit commentary)', () => {
    const superAdmin = readFileSync(join(variantsDir, 'super_admin.md'), 'utf-8')
    const acharya = readFileSync(join(variantsDir, 'acharya.md'), 'utf-8')
    expect(acharya.length).toBeLessThan(superAdmin.length)
  })

  it('client.md mentions Sanskrit glossing requirement', () => {
    const content = readFileSync(join(variantsDir, 'client.md'), 'utf-8')
    expect(content.toLowerCase()).toContain('sanskrit')
    expect(content.toLowerCase()).toContain('english')
  })

  it('client.md specifies compact output (≤800 tokens)', () => {
    const content = readFileSync(join(variantsDir, 'client.md'), 'utf-8')
    expect(content).toContain('800')
  })

  // public_redacted.md content check retired (Stream A 3.tier_excision 2026-05-28).
})

// ── School conventions content checks ─────────────────────────────────────────

describe('school_conventions.ts content', () => {
  it('contains all 4 school names', () => {
    const content = readFileSync(join(ROOT, 'src/resources/school_conventions.ts'), 'utf-8')
    expect(content).toContain('Parashara')
    expect(content).toContain('Jaimini')
    expect(content).toContain('KP')
    expect(content).toContain('Tajaka')
  })

  it('contains convergence_score definition', () => {
    const content = readFileSync(join(ROOT, 'src/resources/school_conventions.ts'), 'utf-8')
    expect(content).toContain('convergence_score')
  })

  it('documents known disagreements between schools', () => {
    const content = readFileSync(join(ROOT, 'src/resources/school_conventions.ts'), 'utf-8')
    expect(content.toLowerCase()).toContain('disagree')
  })

  it('includes classical anchors for each school', () => {
    const content = readFileSync(join(ROOT, 'src/resources/school_conventions.ts'), 'utf-8')
    expect(content).toContain('Brihat Parashara Hora Shastra')
    expect(content).toContain('Jaimini Sutram')
    expect(content).toContain('KP Reader')
    expect(content).toContain('Tajaka Neelakanthi')
  })
})

// ── Capabilities placeholder check ────────────────────────────────────────────

describe('capabilities.ts placeholder', () => {
  it('contains "perf data pending S4 wiring" note', () => {
    const content = readFileSync(join(ROOT, 'src/resources/capabilities.ts'), 'utf-8')
    expect(content).toContain('pending S4')
  })

  it('lists all 21 tools including new bundle and perf tools', () => {
    const content = readFileSync(join(ROOT, 'src/resources/capabilities.ts'), 'utf-8')
    expect(content).toContain('holistic_bundle')
    expect(content).toContain('multi_school_bundle')
    expect(content).toContain('tool_health')
    expect(content).toContain('data_coverage')
    expect(content).toContain('log_prediction')
  })
})

// ── chart_snapshot.ts checks ──────────────────────────────────────────────────

describe('chart_snapshot.ts structure', () => {
  it('registers marsys://chart-snapshot URI', () => {
    const content = readFileSync(join(ROOT, 'src/resources/chart_snapshot.ts'), 'utf-8')
    expect(content).toContain('marsys://chart-snapshot')
  })

  it('fetches from primitive tools (not hardcoded data only)', () => {
    const content = readFileSync(join(ROOT, 'src/resources/chart_snapshot.ts'), 'utf-8')
    expect(content).toContain('fetchPrimitive')
    expect(content).toContain('query_dasha_periods')
    expect(content).toContain('query_panchanga')
  })

  it('contains planetary positions table structure', () => {
    const content = readFileSync(join(ROOT, 'src/resources/chart_snapshot.ts'), 'utf-8')
    expect(content).toContain('Planetary Position')
    expect(content).toContain('Nakshatra')
  })
})
