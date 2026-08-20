/**
 * Lane P2-C (PPR-09/16) — the composer's honest request mapping.
 *
 * Depth/Length/Model pills previously either had no effect on the live
 * request at all (`model`/`length` were pure local state, never read by
 * `onSubmit`) or a misleading one (`Standard` silently forced `deep_dive` via
 * the dev-fixture `mode` bridge — see `PariprashnaApp.tsx`'s prior
 * `mode === 'single' ? 'auto' : 'deep_dive'`). These tests pin the new,
 * honest mapping functions directly.
 */

import { describe, it, expect } from 'vitest'

import { depthToReadingDepth, lengthToLengthTier, modelToModelId } from './Composer'

describe('depthToReadingDepth', () => {
  it('maps Deep dive to deep_dive — the only picker value that forces it', () => {
    expect(depthToReadingDepth('Deep dive')).toBe('deep_dive')
  })

  it('maps every other option to auto (ReadingDepthSchema has no finer tier)', () => {
    expect(depthToReadingDepth('Auto')).toBe('auto')
    expect(depthToReadingDepth('Quick')).toBe('auto')
    expect(depthToReadingDepth('Standard')).toBe('auto')
  })
})

describe('lengthToLengthTier', () => {
  it('maps Concise -> brief and Detailed -> exhaustive', () => {
    expect(lengthToLengthTier('Concise')).toBe('brief')
    expect(lengthToLengthTier('Detailed')).toBe('exhaustive')
  })

  it('maps Auto and Balanced to standard (the documented no-op tier)', () => {
    expect(lengthToLengthTier('Auto')).toBe('standard')
    expect(lengthToLengthTier('Balanced')).toBe('standard')
  })
})

describe('modelToModelId', () => {
  it('maps the "auto" sentinel to undefined (no model_id override sent)', () => {
    expect(modelToModelId('auto')).toBeUndefined()
  })

  it('passes any real registry id through unchanged', () => {
    expect(modelToModelId('claude-opus-4-7')).toBe('claude-opus-4-7')
  })
})
