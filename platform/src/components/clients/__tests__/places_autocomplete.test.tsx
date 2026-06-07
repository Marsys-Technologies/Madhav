/**
 * Tests for Places API integration surface — [BUILD-ORCH-D-S3]
 *
 * D-S3 finding: Branch 3 — Places API was NOT wired at discovery time.
 * NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is absent from env.
 *
 * Acceptance criteria:
 *   - isGoogleMapsKeyConfigured() returns false when env var absent
 *   - buildPlacesHandler() returns keyAbsent=true when key absent
 *   - buildPlacesHandler() onPlaceSelected is a no-op when key absent
 *   - buildPlacesHandler() returns keyAbsent=false when key present
 *   - onPlaceSelected calls onResult with correct lat/lng/description
 *   - onPlaceSelected is a no-op (doesn't call onResult) when place.geometry absent
 *   - utcOffsetMinutes passes through correctly
 *   - utcOffsetMinutes is null when missing from place result
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  isGoogleMapsKeyConfigured,
  buildPlacesHandler,
  type PlacesResult,
} from '../usePlacesAutocomplete'

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makePlaceResult(overrides: Partial<google.maps.places.PlaceResult> = {}): google.maps.places.PlaceResult {
  return {
    geometry: {
      location: {
        lat: () => 20.2961,
        lng: () => 85.8245,
      } as google.maps.LatLng,
    } as google.maps.places.PlaceGeometry,
    formatted_address: 'Bhubaneswar, Odisha, India',
    name: 'Bhubaneswar',
    utc_offset_minutes: 330,
    ...overrides,
  }
}

// ─── isGoogleMapsKeyConfigured ────────────────────────────────────────────────

describe('isGoogleMapsKeyConfigured', () => {
  const originalEnv = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY

  afterEach(() => {
    if (originalEnv === undefined) {
      delete process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
    } else {
      process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = originalEnv
    }
  })

  it('returns false when env var is not set', () => {
    delete process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
    expect(isGoogleMapsKeyConfigured()).toBe(false)
  })

  it('returns false when env var is empty string', () => {
    process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = ''
    expect(isGoogleMapsKeyConfigured()).toBe(false)
  })

  it('returns true when env var is set to a non-empty value', () => {
    process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = 'AIzaSy_fake_key_for_tests'
    expect(isGoogleMapsKeyConfigured()).toBe(true)
  })
})

// ─── buildPlacesHandler — key absent ─────────────────────────────────────────

describe('buildPlacesHandler — key absent', () => {
  beforeEach(() => {
    delete process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
  })

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
  })

  it('returns keyAbsent=true when key is missing', () => {
    const { keyAbsent } = buildPlacesHandler(() => {})
    expect(keyAbsent).toBe(true)
  })

  it('onPlaceSelected is a no-op — does not call onResult', () => {
    const onResult = vi.fn()
    const { onPlaceSelected } = buildPlacesHandler(onResult)
    onPlaceSelected(makePlaceResult())
    expect(onResult).not.toHaveBeenCalled()
  })
})

// ─── buildPlacesHandler — key present ────────────────────────────────────────

describe('buildPlacesHandler — key present', () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY = 'AIzaSy_fake_key_for_tests'
  })

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
  })

  it('returns keyAbsent=false when key is present', () => {
    const { keyAbsent } = buildPlacesHandler(() => {})
    expect(keyAbsent).toBe(false)
  })

  it('calls onResult with correct lat + lng from place result', () => {
    const onResult = vi.fn<(r: PlacesResult) => void>()
    const { onPlaceSelected } = buildPlacesHandler(onResult)
    onPlaceSelected(makePlaceResult())
    expect(onResult).toHaveBeenCalledOnce()
    const result = onResult.mock.calls[0][0]
    expect(result.lat).toBe(20.2961)
    expect(result.lng).toBe(85.8245)
  })

  it('passes formatted_address as description', () => {
    const onResult = vi.fn<(r: PlacesResult) => void>()
    const { onPlaceSelected } = buildPlacesHandler(onResult)
    onPlaceSelected(makePlaceResult({ formatted_address: 'Bhubaneswar, Odisha, India' }))
    expect(onResult.mock.calls[0][0].description).toBe('Bhubaneswar, Odisha, India')
  })

  it('falls back to name when formatted_address is absent', () => {
    const onResult = vi.fn<(r: PlacesResult) => void>()
    const { onPlaceSelected } = buildPlacesHandler(onResult)
    onPlaceSelected(makePlaceResult({ formatted_address: undefined, name: 'Bhubaneswar' }))
    expect(onResult.mock.calls[0][0].description).toBe('Bhubaneswar')
  })

  it('passes utcOffsetMinutes correctly', () => {
    const onResult = vi.fn<(r: PlacesResult) => void>()
    const { onPlaceSelected } = buildPlacesHandler(onResult)
    onPlaceSelected(makePlaceResult({ utc_offset_minutes: 330 }))
    expect(onResult.mock.calls[0][0].utcOffsetMinutes).toBe(330)
  })

  it('sets utcOffsetMinutes to null when absent from place result', () => {
    const onResult = vi.fn<(r: PlacesResult) => void>()
    const { onPlaceSelected } = buildPlacesHandler(onResult)
    onPlaceSelected(makePlaceResult({ utc_offset_minutes: undefined }))
    expect(onResult.mock.calls[0][0].utcOffsetMinutes).toBeNull()
  })

  it('is a no-op (does not call onResult) when geometry is absent', () => {
    const onResult = vi.fn()
    const { onPlaceSelected } = buildPlacesHandler(onResult)
    onPlaceSelected({ ...makePlaceResult(), geometry: undefined })
    expect(onResult).not.toHaveBeenCalled()
  })
})
