import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AssetRow } from '../AssetRow'
import { LayerPanel } from '../LayerPanel'
import type { AssetStats } from '@/app/api/cockpit/stats/route'

// Cockpit Polish R2 — service rendering + visual fixes.
// Covers brief issues 1 (service health), 5 (status dot), 7 (name size).

vi.mock('@/hooks/useUserRole', () => ({
  useUserRole: vi.fn(),
}))

import { useUserRole } from '@/hooks/useUserRole'
const mockUseUserRole = useUserRole as ReturnType<typeof vi.fn>

const DATA_ASSET = {
  asset_id: 'ga_positions',
  layer: 'ganita',
  sort_order: 1,
  sanskrit_name: 'Graha-sphuṭa',
  english_name: 'Planet positions',
  english_description: '',
  storage_type: 'table',
  target_table: 'ganita_positions',
  count_sql: 'SELECT count(*) FROM ganita_positions',
  size_sql: null,
  target_floor: 9,
  expected_volume_formula: null,
  expected_volume_inputs: null,
  volume_explanation: null,
  depends_on: [],
  scope: 'per_chart',
  is_active: true,
  estimated_seconds: null,
  created_at: '2026-01-01T00:00:00Z',
  asset_type: 'data' as const,
  layer_name: 'Gaṇita',
  layer_index: 'L1',
  provides_apis: null,
  health_probe: null,
  catalog_status: 'CURRENT' as const,
  // Migration 242 service/artifact kind fields
  asset_kind: 'data' as const,
  service_health: null,
  last_invoked_at: null,
  last_selftest_at: null,
  selftest_detail: null,
}

const SERVICE_ASSET = {
  ...DATA_ASSET,
  asset_id: 'bg_panchanga',
  layer: 'brahmagyan',
  sanskrit_name: 'Pañcāṅga Gaṇanā',
  english_name: 'Panchanga Engine',
  storage_type: 'service',
  target_table: null,
  count_sql: null,
  target_floor: null,
  scope: 'global',
  asset_type: 'service' as const,
  layer_name: 'Brahma Jñāna',
  layer_index: 'L0',
}

// L3 service assets use asset_type='data' + asset_kind='service' (migration 242 pattern).
// The ServiceHealthPill gate must check asset_kind, not just asset_type.
const L3_SERVICE_ASSET = {
  ...DATA_ASSET,
  asset_id: 'ka_dasha_kala',
  layer: 'kala',
  sanskrit_name: 'Daśā-kāla',
  english_name: 'Daśā Eligibility Service',
  storage_type: 'service',
  target_table: null,
  count_sql: null,
  target_floor: null,
  scope: 'global',
  asset_type: 'data' as const,
  asset_kind: 'service' as const,
  layer_name: 'Kāla',
  layer_index: 'L3',
}

function statOf(partial: Partial<AssetStats>): AssetStats {
  return {
    asset_id: 'x',
    actual_rows: null,
    volume: null,
    size_bytes: null,
    last_updated: '2026-01-01T00:00:00Z',
    error: null,
    state: 'dormant',
    last_built_at: null,
    build_state_stale: false,
    service_health: null,
    last_invoked_at: null,
    ...partial,
  }
}

describe('Cockpit Polish R2 — AssetRow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  it('mounts a service row green with no missing_table / degraded text (issue 1)', () => {
    render(
      <AssetRow
        asset={SERVICE_ASSET}
        stat={statOf({ asset_id: 'bg_panchanga', state: 'service_ok', error: null })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    expect(screen.getByTitle('CURRENT · healthy')).toBeTruthy()
    expect(screen.queryByText(/missing_table/)).toBeNull()
    expect(screen.queryByText(/degraded/)).toBeNull()
  })

  it('renders a status dot instead of a literal CURRENT text chip (issue 5)', () => {
    const { container } = render(
      <AssetRow
        asset={DATA_ASSET}
        stat={statOf({ asset_id: 'ga_positions', state: 'lit', actual_rows: 9 })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    // No "CURRENT" rendered as visible text anywhere in the row
    expect(screen.queryByText('CURRENT')).toBeNull()
    // A status dot carries the words in its title tooltip
    expect(container.querySelector('[title="CURRENT · healthy"]')).toBeTruthy()
  })

  it('renders the sanskrit name at the bumped 18px medium weight (issue 7)', () => {
    render(
      <AssetRow
        asset={DATA_ASSET}
        stat={statOf({ asset_id: 'ga_positions', state: 'lit', actual_rows: 9 })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    const name = screen.getByText('Graha-sphuṭa')
    expect(name.className).toContain('text-[18px]')
    expect(name.className).toContain('font-medium')
  })
})

describe('Cockpit Polish R2 — parent context (LayerPanel renders a service row green)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  it('mounts a brahmagyan service inside LayerPanel without degraded state', () => {
    render(
      <LayerPanel
        layer="brahmagyan"
        assets={[SERVICE_ASSET]}
        stats={new Map([['bg_panchanga', statOf({ asset_id: 'bg_panchanga', state: 'service_ok' })]])}
        defaultExpanded
        chartId="chart-1"
        activeRun={null}
        onRunStarted={() => {}}
      />
    )
    expect(screen.getByTitle('CURRENT · healthy')).toBeTruthy()
    expect(screen.queryByText(/degraded/)).toBeNull()
  })
})

describe('L3 service asset dual-check (asset_kind fix)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  it('renders ServiceHealthPill (LIVE) for L3 asset with asset_type=data + asset_kind=service', () => {
    render(
      <AssetRow
        asset={L3_SERVICE_ASSET}
        stat={statOf({ asset_id: 'ka_dasha_kala', state: 'service_ok', error: null })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    // Must show LIVE (ServiceHealthPill green), never NOT BUILT (AssetProgressBar dormant fallback)
    expect(screen.getByText('LIVE')).toBeTruthy()
    expect(screen.queryByText('NOT BUILT')).toBeNull()
  })

  it('renders full bar (LIVE pill) for lit artifact with null target_floor and rows > 0', () => {
    render(
      <AssetRow
        asset={{ ...DATA_ASSET, target_floor: null }}
        stat={statOf({ asset_id: 'ga_positions', state: 'lit', actual_rows: 66738 })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    // Bar shows row count for lit data assets (milestone-segment design; no text pill)
    expect(screen.getByText('66,738')).toBeTruthy()
    expect(screen.queryByText('NOT BUILT')).toBeNull()
  })
})

describe('CF.L3.7 — RETIRED placeholder rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  const RETIRED_ASSET = {
    ...DATA_ASSET,
    asset_id: 'ka_test_retired_placeholder',
    layer: 'kala',
    sanskrit_name: 'Transit Almanac',
    english_name: 'Transit Almanac',
    is_active: false,
    catalog_status: 'RETIRED' as const,
    asset_kind: 'data' as const,
    target_floor: null,
  }

  it('renders RETIRED pill (grey) not NOT MIGRATED (red) for is_active=false + catalog_status=RETIRED', () => {
    render(
      <AssetRow
        asset={RETIRED_ASSET}
        stat={null}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    // RETIRED assets: milestone-segment bar (no text pill); confirm no NOT_MIGRATED fallback
    expect(document.querySelector('[data-asset-id="ka_test_retired_placeholder"]')).toBeTruthy()
    expect(screen.queryByText('NOT MIGRATED')).toBeNull()
  })

  it('status dot for RETIRED asset is neutral (not red — no isRed state)', () => {
    const { container } = render(
      <AssetRow
        asset={RETIRED_ASSET}
        stat={null}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    // Dot title shows 'retired' state — not 'not_migrated'
    const dot = container.querySelector('[title*="retired"]')
    expect(dot).toBeTruthy()
    // Color should NOT be the red error color
    const style = (dot as HTMLElement)?.style?.background ?? ''
    expect(style).not.toContain('220,80,80')
  })
})

// ── CF.L3.8 — DRAFT·healthy StatusDot must be GREEN, not red ────────────────
describe('CF.L3.8 — StatusDot: DRAFT catalog_status does not override healthy runtime state', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseUserRole.mockReturnValue({ role: 'super_admin', isSuperAdmin: true, loading: false })
  })

  it('DRAFT + lit state renders green dot (not red)', () => {
    const { container } = render(
      <AssetRow
        asset={{ ...DATA_ASSET, catalog_status: 'DRAFT' as const }}
        stat={statOf({ state: 'lit' })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    const dot = container.querySelector('[title*="healthy"]')
    expect(dot).toBeTruthy()
    const bg = (dot as HTMLElement)?.style?.background ?? ''
    expect(bg).not.toMatch(/220,?\s*80,?\s*80/)
    expect(bg).toMatch(/83,?\s*200,?\s*100/)
  })

  it('DRAFT + service_ok state renders green dot (not red)', () => {
    const { container } = render(
      <AssetRow
        asset={{ ...L3_SERVICE_ASSET, catalog_status: 'DRAFT' as const }}
        stat={statOf({ state: 'service_ok' })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    const dot = container.querySelector('[title*="healthy"]')
    expect(dot).toBeTruthy()
    const bg = (dot as HTMLElement)?.style?.background ?? ''
    expect(bg).not.toMatch(/220,?\s*80,?\s*80/)
  })

  it('DRAFT + dormant state renders red dot (not yet built)', () => {
    const { container } = render(
      <AssetRow
        asset={{ ...DATA_ASSET, catalog_status: 'DRAFT' as const }}
        stat={statOf({ state: 'dormant' })}
        chartId="chart-1"
        activeRunId={null}
        activeRunPaused={false}
        onRunStarted={() => {}}
      />
    )
    const dot = container.querySelector('[title*="DRAFT"]')
    expect(dot).toBeTruthy()
    const bg = (dot as HTMLElement)?.style?.background ?? ''
    expect(bg).toMatch(/220,?\s*80,?\s*80/)
  })
})

// ── Seed governance: Kāla layer count after hard-removal of ka_transit_almanac ──
describe('Asset seed governance — Kāla layer', () => {
  it('has exactly 17 kala assets in the seed (ka_transit_almanac removed; ka_avadhi + ka_taranga + ka_kshetra registered; ka_kota_chakra + ka_sudarshana_varsha added (SHAD-DARSHANA W3 items 16/17))', () => {
    const { readFileSync } = require('fs')
    const { resolve } = require('path')
    const seedContent: string = readFileSync(resolve(process.cwd(), 'scripts/seed/asset_registry_seed.ts'), 'utf8')
    const kalaMatches = seedContent.match(/layer:\s*'kala'/g) ?? []
    // BA Phase 2.5: ka_avadhi and ka_taranga are real, already-registered
    // (@register) writers with live populated tables that were never added to
    // this seed catalog — the same class of gap fixed for bo_pratijna/bg_ghatana
    // this same session. Raised the count from 12 to 14; did not reintroduce
    // ka_transit_almanac (see the next test).
    //
    // ṢAḌ-DARŚANA W2 (2026-07-30/31): a merge-train pass briefly removed Lane E's
    // `ka_kshetra` row, reasoning it was redundant with migration 494's own
    // `INSERT INTO asset_registry` — the same mechanism `ka_gochara_sweep`
    // (migration 460) / `ka_gochara_resonance` (migration 459) use without any
    // TS row. That reasoning missed that `catalog_reconciliation.test.ts`
    // resolves `depends_on` purely against THIS file's own `ASSETS` array, and
    // `mi_bhara.depends_on = ['ka_kshetra']` lives in this same file — so unlike
    // ka_gochara_sweep/resonance (which nothing in this file depends on),
    // `ka_kshetra` must have a row here too. Restored (14 → 15); same defect
    // class as the historical ga_vichara/bo_pratijna gaps.
    //
    // ṢAḌ-DARŚANA W3 (2026-08-01, Lane w3-kota-sudarshana): two brand-new Kāla
    // writers landed with their own Nirmāṇa asset_registry seed rows —
    // `ka_kota_chakra` (item 16, migration 520) and `ka_sudarshana_varsha`
    // (item 17, migration 521). 15 → 17.
    expect(kalaMatches).toHaveLength(17)
  })

  it('contains no ka_transit_almanac entry in the seed', () => {
    const { readFileSync } = require('fs')
    const { resolve } = require('path')
    const seedContent: string = readFileSync(resolve(process.cwd(), 'scripts/seed/asset_registry_seed.ts'), 'utf8')
    expect(seedContent).not.toContain("'ka_transit_almanac'")
  })
})
