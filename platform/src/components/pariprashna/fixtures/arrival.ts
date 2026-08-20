import type { ArrivalLineData } from '../ArrivalLine'

/**
 * DEV/QA-ONLY sample arrival-line text — NOT wired to any real L1/Kāla
 * capability. Exists so the fixture host (`PariprashnaAppFixture`) can
 * demonstrate the chrome's placement/typography without fabricating a real
 * value on the live path (see `ArrivalLine.tsx`'s header for the full scope
 * note). Never imported by `hooks/useLiveStream.ts` or any live host.
 */
export const FIXTURE_ARRIVAL_LINE: ArrivalLineData = {
  text: 'Śani daśā, fourth year · one prediction window open — mid-2027. (fixture sample — not L1/Kāla-sourced)',
}
