/**
 * holistic_bundle_suberrors.test.ts — D-2 Lane V-3, CR-14/39 (ledger row 28).
 *
 * Anti-vacuous: the induced sub-error must actually be CAUGHT (§F1.7). Drives the pure
 * collectBundleSubErrors detector against a synthetic partial-ok bundle.
 */
import { describe, it, expect } from 'vitest'
import { collectBundleSubErrors } from './holistic_bundle.js'

describe('collectBundleSubErrors — CR-14/39', () => {
  it('catches an induced sub-error folded into an otherwise-ok bundle', () => {
    const result = {
      envelope: {
        ok: true,
        bundle_entries: [
          { subsystem: 'positions', ok: true, rows: 9 },
          { subsystem: 'signals', ok: false, error: 'query_signals timed out' },
          { subsystem: 'graph', status: 'ERROR' },
        ],
      },
    }
    const errs = collectBundleSubErrors(result)
    expect(errs).toHaveLength(2)
    expect(errs.map((e) => e.subsystem).sort()).toEqual(['graph', 'signals'])
    const sig = errs.find((e) => e.subsystem === 'signals')!
    expect(sig.error).toContain('timed out')
  })

  it('returns [] for a fully-healthy bundle (no false positives)', () => {
    const result = { bundle_entries: [{ subsystem: 'positions', ok: true }, { subsystem: 'signals', ok: true }] }
    expect(collectBundleSubErrors(result)).toEqual([])
  })

  it('detects error markers at the top-level bundle_entries location too', () => {
    const result = { bundle_entries: [{ name: 'resonance', is_error: true }] }
    const errs = collectBundleSubErrors(result)
    expect(errs).toHaveLength(1)
    expect(errs[0].subsystem).toBe('resonance')
  })

  it('handles a bundle with no entries array gracefully', () => {
    expect(collectBundleSubErrors({})).toEqual([])
  })

  // MC-002: holistic/multi_school bundle entries mark failure as `errored:true`
  // with `sub_tool` + `error_class` — previously undetected (the live 5-of-8 hole).
  it('catches errored:true entries (holistic/multi_school shape)', () => {
    const result = {
      envelope: {
        ok: false,
        status: 'degraded',
        bundle_entries: [
          { sub_tool: 'UCN', errored: false, rows_returned: 1 },
          { sub_tool: 'MSR', errored: true, error_class: 'tool_error' },
          { sub_tool: 'CGM', errored: true, error_class: 'tool_error' },
          { sub_tool: 'LEL', errored: true, error_class: 'timeout' },
        ],
      },
    }
    const errs = collectBundleSubErrors(result)
    expect(errs.map((e) => e.subsystem).sort()).toEqual(['CGM', 'LEL', 'MSR'])
    expect(errs.find((e) => e.subsystem === 'MSR')!.error).toContain('tool_error')
  })
})
