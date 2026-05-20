/**
 * TimingsPanel unit tests
 * Phase: 4C-4-S2 (Item 6 / AC.4C4S2.6)
 */
import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { TimingsPanel } from '@/app/panchang/components/TimingsPanel'
import type { PanchangTimings } from '@/app/panchang/hooks/usePanchangDay'

// Bhubaneswar IST = UTC+5:30 = 330 min
const TZ = 330

/** Build a UTC ISO string offset by `offsetMinutes` from midnight UTC */
function utcAt(hour: number, minute: number): string {
  const d = new Date(Date.UTC(2026, 4, 19, hour, minute, 0))
  return d.toISOString().replace('.000', '')
}

const FULL_TIMINGS: PanchangTimings = {
  sunrise_utc: utcAt(0, 12),   // 05:42 IST
  sunset_utc: utcAt(13, 38),   // 19:08 IST
  moonrise_utc: utcAt(3, 44),  // 09:14 IST
  moonset_utc: utcAt(16, 31),  // 22:01 IST
  inauspicious: [
    { label: 'rahu_kalam', start_utc: utcAt(9, 54), end_utc: utcAt(11, 23) },
    { label: 'yamagandam', start_utc: utcAt(3, 40), end_utc: utcAt(5, 8) },
    { label: 'gulika_kalam', start_utc: utcAt(6, 55), end_utc: utcAt(8, 24) },
  ] as unknown as Record<string, unknown>,
  auspicious: [
    { label: 'abhijit', start_utc: utcAt(6, 25), end_utc: utcAt(7, 12) },
    { label: 'brahma_muhurta', start_utc: utcAt(23, 24), end_utc: utcAt(0, 12) },
    { label: 'amrit_kalam', start_utc: utcAt(1, 38), end_utc: utcAt(3, 3) },
  ] as unknown as Record<string, unknown>,
}

const MINIMAL_TIMINGS: PanchangTimings = {
  sunrise_utc: utcAt(0, 12),
  sunset_utc: utcAt(13, 38),
  moonrise_utc: null,   // no moonrise this day
  moonset_utc: null,    // no moonset this day
  inauspicious: null,
  auspicious: null,
}

describe('TimingsPanel', () => {
  it('renders all 4 sun/moon timing rows', () => {
    const { getByLabelText } = render(
      <TimingsPanel timings={FULL_TIMINGS} tzOffsetMinutes={TZ} />
    )
    // Section label
    expect(getByLabelText('Timings — Sun, Moon, Inauspicious and Auspicious Windows')).toBeTruthy()
    // Four rows
    expect(getByLabelText(/^Sunrise:/)).toBeTruthy()
    expect(getByLabelText(/^Sunset:/)).toBeTruthy()
    expect(getByLabelText(/^Moonrise:/)).toBeTruthy()
    expect(getByLabelText(/^Moonset:/)).toBeTruthy()
  })

  it('converts UTC times to local IST (HH:MM)', () => {
    const { getByLabelText } = render(
      <TimingsPanel timings={FULL_TIMINGS} tzOffsetMinutes={330} />
    )
    // sunrise 00:12 UTC + 330min = 05:42 IST
    const sunriseRow = getByLabelText(/^Sunrise:/)
    expect(sunriseRow.getAttribute('aria-label')).toContain('05:42')
    // sunset 13:38 UTC + 330min = 19:08 IST
    const sunsetRow = getByLabelText(/^Sunset:/)
    expect(sunsetRow.getAttribute('aria-label')).toContain('19:08')
  })

  it('shows — for missing moon transitions', () => {
    const { getByLabelText } = render(
      <TimingsPanel timings={MINIMAL_TIMINGS} tzOffsetMinutes={TZ} />
    )
    const moonriseRow = getByLabelText(/^Moonrise:/)
    expect(moonriseRow.getAttribute('aria-label')).toContain('—')
    const moonsetRow = getByLabelText(/^Moonset:/)
    expect(moonsetRow.getAttribute('aria-label')).toContain('—')
  })

  it('renders inauspicious windows with correct labels', () => {
    const { getByLabelText } = render(
      <TimingsPanel timings={FULL_TIMINGS} tzOffsetMinutes={TZ} />
    )
    expect(getByLabelText(/^Rahu Kalam:/)).toBeTruthy()
    expect(getByLabelText(/^Yamagandam:/)).toBeTruthy()
    expect(getByLabelText(/^Gulika Kalam:/)).toBeTruthy()
  })

  it('renders auspicious windows with correct labels', () => {
    const { getByLabelText } = render(
      <TimingsPanel timings={FULL_TIMINGS} tzOffsetMinutes={TZ} />
    )
    expect(getByLabelText(/^Abhijit Muhurta:/)).toBeTruthy()
    expect(getByLabelText(/^Brahma Muhurta:/)).toBeTruthy()
    expect(getByLabelText(/^Amrit Kalam:/)).toBeTruthy()
  })

  it('renders "None computed" when inauspicious is null', () => {
    const { getAllByText } = render(
      <TimingsPanel timings={MINIMAL_TIMINGS} tzOffsetMinutes={TZ} />
    )
    const noneTexts = getAllByText('None computed')
    // Two "None computed" — one for inauspicious, one for auspicious
    expect(noneTexts.length).toBe(2)
  })

  it('formats time windows as HH:MM – HH:MM', () => {
    const { getByLabelText } = render(
      <TimingsPanel timings={FULL_TIMINGS} tzOffsetMinutes={TZ} />
    )
    const rahuRow = getByLabelText(/^Rahu Kalam:/)
    // 09:54 UTC + 330 = 15:24 IST; 11:23 UTC + 330 = 16:53 IST
    const label = rahuRow.getAttribute('aria-label') ?? ''
    expect(label).toContain('15:24')
    expect(label).toContain('16:53')
  })
})
