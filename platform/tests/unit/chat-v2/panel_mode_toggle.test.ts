/**
 * Unit tests for B.6 — PanelModeToggle wired into V2 composer (audit finding O2).
 *
 * Source-shape tests verifying:
 * - PanelModeToggle component structure (4 tests)
 * - ConsumeChatV2 integration wiring (2 tests)
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const toggleSrc = readFileSync(
  join(__dirname, '../../../src/components/chat-v2/PanelModeToggle.tsx'),
  'utf-8',
)

const v2Src = readFileSync(
  join(__dirname, '../../../src/components/consume/ConsumeChatV2.tsx'),
  'utf-8',
)

// ── PanelModeToggle component tests ─────────────────────────────────────────

describe('B.6 — PanelModeToggle', () => {
  it('exports PanelOptInCtx for consumption in V2ChatRuntime', () => {
    expect(toggleSrc).toContain('export const PanelOptInCtx')
    expect(toggleSrc).toContain('PanelOptInContextValue')
  })

  it('renders with role="switch" + aria-checked for a11y', () => {
    expect(toggleSrc).toContain('role="switch"')
    expect(toggleSrc).toContain('aria-checked={panelOptIn}')
  })

  it('uses data-testid="v2-panel-mode-toggle" for E2E targeting', () => {
    expect(toggleSrc).toContain('data-testid="v2-panel-mode-toggle"')
  })

  it('includes tooltip explaining panel mode', () => {
    expect(toggleSrc).toContain('title=')
    expect(toggleSrc).toContain('multiple models')
  })
})

// ── ConsumeChatV2 integration wiring tests ────────────────────────────────────

describe('B.6 — ConsumeChatV2 wiring', () => {
  it('imports PanelModeToggle and PanelOptInCtx, provides PanelOptInCtx around runtime', () => {
    expect(v2Src).toContain("from '../chat-v2/PanelModeToggle'")
    expect(v2Src).toContain('PanelOptInCtx.Provider')
    expect(v2Src).toContain('panelOptInCtxValue')
  })

  it('injects panel_opt_in into transport body and renders PanelModeToggle in composer', () => {
    expect(v2Src).toContain('panel_opt_in')
    expect(v2Src).toContain('panelOptInRef.current')
    expect(v2Src).toContain('<PanelModeToggle')
    expect(v2Src).toContain('v2-composer-options')
  })
})
