import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { createConfigService, type FeatureFlag } from '@/lib/config/index'

describe('ConfigService', () => {
  it('pipeline feature flags default to false', () => {
    const svc = createConfigService()
    const flags: FeatureFlag[] = [
      'LLM_CHECKPOINTS_ENABLED',
    ]
    for (const flag of flags) {
      expect(svc.getFlag(flag)).toBe(false)
    }
  })

  // NEW_QUERY_PIPELINE_ENABLED retired Phase 11B (2026-05-11); legacy path deleted.
  // AUDIT_ENABLED retired BHISMA-B1 §6.2; replaced by always-on observability flags.
  // REASONING_MODEL_STREAMING retired BHISMA Wave 2; o-series models removed from registry.
  it('BHISMA-B1 observability flags default true', () => {
    const svc = createConfigService()
    const flags: FeatureFlag[] = [
      'TRACE_ANALYTICS_ENABLED',
      'COST_TRACKING_ENABLED',
      'CITATION_CHECK_ENABLED',
    ]
    for (const flag of flags) {
      expect(svc.getFlag(flag)).toBe(true)
    }
  })

  it('setFlag updates the value', () => {
    const svc = createConfigService()
    svc.setFlag('PANEL_MODE_ENABLED', true)
    expect(svc.getFlag('PANEL_MODE_ENABLED')).toBe(true)
  })

  it('subscribe callback fires on setFlag', () => {
    const svc = createConfigService()
    const calls: Array<[string, unknown]> = []
    const unsub = svc.subscribe((key, val) => calls.push([key, val]))
    svc.setFlag('AUDIT_VIEW_VISIBLE', true)
    expect(calls).toEqual([['AUDIT_VIEW_VISIBLE', true]])
    unsub()
  })

  it('unsubscribe stops notifications', () => {
    const svc = createConfigService()
    const calls: number[] = []
    const unsub = svc.subscribe(() => calls.push(1))
    unsub()
    svc.setFlag('AUDIT_VIEW_VISIBLE', true)
    expect(calls).toHaveLength(0)
  })

  it('getValue returns default when key not set', () => {
    const svc = createConfigService()
    expect(svc.getValue('nonexistent', 42)).toBe(42)
  })

  it('PANEL_MODE_ENABLED defaults true', () => {
    const svc = createConfigService()
    expect(svc.getFlag('PANEL_MODE_ENABLED')).toBe(true)
  })

  it('env var override: MARSYS_FLAG_PANEL_MODE_ENABLED=true enables the flag', () => {
    process.env.MARSYS_FLAG_PANEL_MODE_ENABLED = 'true'
    try {
      const svc = createConfigService()
      expect(svc.getFlag('PANEL_MODE_ENABLED')).toBe(true)
    } finally {
      delete process.env.MARSYS_FLAG_PANEL_MODE_ENABLED
    }
  })
})
