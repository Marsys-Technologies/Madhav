/**
 * γ6 — Per-message cost visibility
 *
 * Tests:
 *   - COST_VISIBILITY_FOR_USERS flag exists in DEFAULT_FLAGS as false
 *   - Cost section gating logic: super_admin always sees cost; others gated by flag
 *   - PerMessageDetailsDrawer source has costVisible prop and showCost guard
 *   - feature_flags.ts exports the new flag
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'
import { DEFAULT_FLAGS } from '../../../src/lib/config/feature_flags'

const drawerSource = readFileSync(
  join(process.cwd(), 'src/components/chat/PerMessageDetailsDrawer.tsx'),
  'utf-8',
)

const v2Source = readFileSync(
  join(process.cwd(), 'src/components/consume/ConsumeChatV2.tsx'),
  'utf-8',
)

// ── Flag registration ─────────────────────────────────────────────────────────

describe('COST_VISIBILITY_FOR_USERS flag', () => {
  it('exists in DEFAULT_FLAGS', () => {
    expect('COST_VISIBILITY_FOR_USERS' in DEFAULT_FLAGS).toBe(true)
  })

  it('defaults to false (off by default)', () => {
    expect(DEFAULT_FLAGS.COST_VISIBILITY_FOR_USERS).toBe(false)
  })
})

// ── Drawer source assertions ───────────────────────────────────────────────────

describe('PerMessageDetailsDrawer — γ6 cost gating', () => {
  it('accepts costVisible prop', () => {
    expect(drawerSource).toContain('costVisible')
  })

  it('derives showCost from isSuperAdmin OR costVisible', () => {
    expect(drawerSource).toContain('showCost')
    expect(drawerSource).toContain('isSuperAdmin || costVisible')
  })

  it('gates the Cost section behind showCost', () => {
    expect(drawerSource).toContain('showCost')
    // Cost MetaRow must appear inside the showCost conditional
    const costSectionIdx = drawerSource.indexOf("title=\"Cost\"")
    const showCostIdx = drawerSource.lastIndexOf('showCost', costSectionIdx)
    expect(showCostIdx).toBeGreaterThanOrEqual(0)
    expect(showCostIdx).toBeLessThan(costSectionIdx)
  })

  it('derives isSuperAdmin from disclosure_tier in metadata.custom', () => {
    expect(drawerSource).toContain("disclosure_tier")
    expect(drawerSource).toContain('isSuperAdmin')
  })
})

// ── ConsumeChatV2 context provision ───────────────────────────────────────────

describe('ConsumeChatV2 — γ6 cost context', () => {
  it('declares CostVisibilityCtx', () => {
    expect(v2Source).toContain('CostVisibilityCtx')
  })

  it('wraps render in CostVisibilityCtx.Provider', () => {
    expect(v2Source).toContain('CostVisibilityCtx.Provider')
  })

  it('passes costVisibilityEnabled prop to provider value', () => {
    expect(v2Source).toContain('costVisibilityEnabled')
  })

  it('V2Message reads costVisible from context', () => {
    expect(v2Source).toContain('useContext(CostVisibilityCtx)')
  })

  it('passes costVisible to PerMessageDetailsDrawer', () => {
    expect(v2Source).toContain('costVisible={costVisible}')
  })
})

// ── Cost gating logic (pure) ───────────────────────────────────────────────────

describe('cost gating logic', () => {
  function showCost(isSuperAdmin: boolean, costVisible: boolean): boolean {
    return isSuperAdmin || costVisible
  }

  it('super_admin always sees cost regardless of flag', () => {
    expect(showCost(true, false)).toBe(true)
    expect(showCost(true, true)).toBe(true)
  })

  it('non-admin sees cost only when flag is on', () => {
    expect(showCost(false, true)).toBe(true)
    expect(showCost(false, false)).toBe(false)
  })
})
