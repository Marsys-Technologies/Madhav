import { buildAdaptiveThreePassFixture } from './adaptive_three_pass'
import { buildSinglePassFixture } from './single_pass'
import { buildHonestGapFixture } from './honest_gap'
import { buildReconnectMidPassFixture } from './reconnect_mid_pass'
import { buildC2SinglePassFixture, buildC2HonestGapFixture } from './c2_recorded_samples'
import type { Fixture } from './types'

export type FixtureMode = 'adaptive' | 'single' | 'gap' | 'reconnect' | 'c2-single' | 'c2-gap'

/**
 * STUB — recorded-fixture registry standing in for lane S-1's live wire.
 * `adaptive` | `single` | `gap` | `reconnect` are hand-authored directly off
 * the approved mockup script (`adaptive_three_pass.ts` etc.); `c2-single` |
 * `c2-gap` replay lane C-2's own committed protocol-scaffold fixtures
 * through `state/c2ProtocolAdapter.ts` — a second, independently-shaped
 * source of events proving this renderer isn't just special-cased to its
 * own invented wire shape. See this build's final report for what's real
 * vs stubbed. Swap for a real submit → SSE-stream wiring once S-1 lands;
 * the reducer and every renderer component are unaffected either way.
 */
export function buildFixtureForMode(mode: FixtureMode, turnId: string, userTextOverride?: string): Fixture {
  const fixture = ((): Fixture => {
    switch (mode) {
      case 'single':
        return buildSinglePassFixture(turnId)
      case 'gap':
        return buildHonestGapFixture(turnId)
      case 'reconnect':
        return buildReconnectMidPassFixture(turnId)
      case 'c2-single':
        return buildC2SinglePassFixture(turnId)
      case 'c2-gap':
        return buildC2HonestGapFixture(turnId)
      case 'adaptive':
      default:
        return buildAdaptiveThreePassFixture(turnId)
    }
  })()
  if (!userTextOverride) return fixture
  return {
    ...fixture,
    userText: userTextOverride,
    events: fixture.events.map((se) =>
      se.event.type === 'turn.open' ? { ...se, event: { ...se.event, userText: userTextOverride } } : se,
    ),
  }
}

export type { Fixture, ScheduledEvent } from './types'
