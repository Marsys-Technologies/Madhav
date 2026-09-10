/**
 * V4 Bundle B — the calibration facade must serve its upstream aggregate when it
 * exists, and must not masquerade a failed read as empirical zero maturity.
 */
import { afterEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { fetchCalibrationMaturity } from './kala_envelope.js'

const PRINCIPAL = { user_uid: 'v4-user', key_id: 'v4-key' }

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('V4 Bundle B — calibration maturity authority', () => {
  it('serves the chart-level kala_field_skill aggregate when it exists', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () => ({ rows: [{
        n_events: 12,
        n_prospective: 7,
        event_class_coverage: 3,
        weights_version: 'weights-v4',
        skill_score: 0.81,
      }] }),
    })))

    await expect(fetchCalibrationMaturity('chart-v4', PRINCIPAL)).resolves.toEqual({
      n_events: 12,
      prospective_resolutions: 7,
      event_class_coverage: 3,
      weights_version: 'weights-v4',
      skill_score: 0.81,
    })
  })

  it('returns a typed, sanitized unknown state rather than an invented all-zero maturity when the authority is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, status: 503, text: async () => 'postgres: production connection refused' })))

    await expect(fetchCalibrationMaturity('chart-v4', PRINCIPAL)).resolves.toEqual({
      n_events: null,
      prospective_resolutions: null,
      event_class_coverage: null,
      weights_version: null,
      skill_score: null,
      state: 'unavailable',
      reason: 'calibration_maturity_authority_unavailable',
    })
  })

  it('uses the all-zero maturity only when the authority was reached and has no fitted row', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({ rows: [] }) })))

    await expect(fetchCalibrationMaturity('chart-v4', PRINCIPAL)).resolves.toEqual({
      n_events: 0,
      prospective_resolutions: 0,
      event_class_coverage: 0,
      weights_version: null,
      skill_score: null,
    })
  })
})

const ROOT = path.resolve(fileURLToPath(import.meta.url), '../../..')
const KALA_VIEWS = path.join(ROOT, 'src/tools/kala_views')

function source(file: string): string {
  return readFileSync(path.join(KALA_VIEWS, file), 'utf8')
}

describe('V4 Bundle B — remaining facade wiring and stale disclosure', () => {
  for (const file of ['now.ts', 'ritual.ts', 'story.ts']) {
    it(`${file} resolves calibration maturity from the shared authority`, () => {
      const contents = source(file)
      expect(contents).toContain('fetchCalibrationMaturity')
      expect(contents).not.toMatch(/calibrationMaturity:\s*noLelCalibrationMaturity\(\)/)
    })
  }

  it('removes the obsolete field-build-required state-delta fallback from kala_now_get', () => {
    expect(source('now.ts')).not.toContain('P-G1 field-build must complete first')
  })

  it('removes the false global claim that no calibration plane exists', () => {
    expect(source('priority.ts')).not.toContain('no calibration plane exists yet')
  })
})
