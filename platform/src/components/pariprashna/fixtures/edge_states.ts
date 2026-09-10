import { FixtureBuilder } from './builder'
import { classifyPariprashnaError } from '@/lib/pariprashna/errors/classify'
import type { Fixture } from './types'

/**
 * P2-G (Edge-state lexicon) — one fixture per §7.8 edge state that has a real
 * wire/reducer path today. Every fixture drives the SAME `threadReducer` +
 * `WorkingBand` a live turn would, through the SAME `classifyPariprashnaError`
 * call production code uses (`state/s1LiveAdapter.ts`,
 * `hooks/useLiveStream.ts`) — so a fixture and the live surface cannot drift
 * apart the way the three former hand-authored `ClassifiedError` literals
 * could (and had).
 *
 * ── Which §7.8 rows are (and are not) fixture-able here ─────────────────────
 * §7.8's ten edge-state rows split into two groups:
 *
 *  REAL WIRE/REDUCER PATH TODAY (fixtured below):
 *   - "Network drop mid-turn" (→ RECONNECTING… → RESUMED — NOTHING LOST):
 *     `edge_network_drop_and_resume`.
 *   - "User presses Stop" (→ STOPPED — KEPT WHAT ARRIVED): `edge_user_stopped`.
 *   - "Provider overloaded / rate-limited", "Timeout" — via §7.5's error
 *     taxonomy, which `error.bandLabel` renders directly:
 *     `edge_error_rate_limit`, `edge_error_model_overload`, `edge_error_timeout`,
 *     `edge_error_network`, `edge_error_auth`, `edge_error_unknown`.
 *
 *  NOT YET WIRED (no `TurnStatus`, `WireEvent`, or reducer case exists for
 *  these — building one is a real feature per state, not a copy fix, and is
 *  each its own later-gate lane: J8/G8-C for the open-window counter-question,
 *  G1-D for the cost/coverage cap ribbon, G3-G/model-picker for the queued
 *  model switch, a busy-instrument queue mechanism, and a chart-rebuild
 *  detector). Their EXACT §7.8 copy is still pinned — as literal strings in
 *  `lib/pariprashna/lexicon.ts`'s `EDGE_STATE_LABELS` / render functions,
 *  asserted byte-exact in `tests/pariprashna/edge_state_lexicon.test.ts` — but
 *  there is honestly no fixture that exercises them end to end yet:
 *   - "Engine asks back (clarification)" — `A QUESTION FIRST`
 *   - "Open window relevant (J8)" — `BEFORE I ANSWER —`
 *   - "Chart rebuilt since last turn" — `THE CHART HAS BEEN REBUILT — RE-READING`
 *   - "Cost/coverage cap trips (partial)" — `SERVED WITHIN LIMITS — ⟨n⟩ OF ⟨m⟩ STEPS`
 *   - "Mid-turn model switch requested" — `WILL SWITCH TO ⟨model⟩ NEXT TURN`
 *   - "Queue wait (busy instrument)" — `IN LINE — STARTS IN A MOMENT`
 * Per §N.8 (Earned-Signal Principle): a fixture with no real detector/wire
 * path behind it would be a green light with nothing measuring the claim —
 * so these are left as honest lexicon-only pins, not faked fixtures.
 */

const USER_TEXT = 'Is a career change on the cards over the next two years?'

/** §7.8: "Network drop mid-turn | RECONNECTING… (band stays; content untouched) → RESUMED — NOTHING LOST". */
export function buildEdgeNetworkDropAndResumeFixture(turnId = 'edge-network-drop'): Fixture {
  const b = new FixtureBuilder(turnId)
  b.turnOpen(USER_TEXT)
  b.phase('Reading the whole chart')
  b.activity({ id: 'a1', passIndex: 0, label: 'Retrieved — timing cycles', detail: '536 periods', kind: 'tool', durationMs: 300, ms: '0.3s' })
  b.advance(100)
  b.reconnecting()
  b.advance(900)
  b.reconnected()
  return { id: 'edge_network_drop_and_resume', label: 'Edge state — network drop & resume', userText: USER_TEXT, events: b.build() }
}

/** §7.8: "User presses Stop | STOPPED — KEPT WHAT ARRIVED; turn settles as interrupted". */
export function buildEdgeUserStoppedFixture(turnId = 'edge-user-stopped'): Fixture {
  const b = new FixtureBuilder(turnId)
  b.turnOpen(USER_TEXT)
  b.phase('Composing the reading')
  b.streamedBlock({ blockId: 'b1', role: 'verdict', text: 'Yes — a genuine occupational shift is indicated.' })
  b.advance(100)
  b.interrupted()
  return { id: 'edge_user_stopped', label: 'Edge state — user stopped', userText: USER_TEXT, events: b.build() }
}

/** One fixture per §7.5 error kind, each carrying the EXACT classifier output a live turn would receive. */
function buildEdgeErrorFixture(id: string, label: string, code: string, turnId: string): Fixture {
  const b = new FixtureBuilder(turnId)
  b.turnOpen(USER_TEXT)
  b.phase('Consulting the chart')
  b.advance(100)
  b.error(classifyPariprashnaError(code))
  return { id, label, userText: USER_TEXT, events: b.build() }
}

export function buildEdgeErrorRateLimitFixture(turnId = 'edge-error-rate-limit'): Fixture {
  return buildEdgeErrorFixture('edge_error_rate_limit', 'Edge state — error: rate limit', 'RATE_LIMIT_429', turnId)
}

export function buildEdgeErrorModelOverloadFixture(turnId = 'edge-error-model-overload'): Fixture {
  return buildEdgeErrorFixture('edge_error_model_overload', 'Edge state — error: model overloaded', 'MODEL_OVERLOADED_503', turnId)
}

export function buildEdgeErrorTimeoutFixture(turnId = 'edge-error-timeout'): Fixture {
  return buildEdgeErrorFixture('edge_error_timeout', 'Edge state — error: timeout', 'DEADLINE_EXCEEDED', turnId)
}

export function buildEdgeErrorNetworkFixture(turnId = 'edge-error-network'): Fixture {
  return buildEdgeErrorFixture('edge_error_network', 'Edge state — error: network (terminal)', 'NETWORK_RESUME_EXHAUSTED', turnId)
}

export function buildEdgeErrorAuthFixture(turnId = 'edge-error-auth'): Fixture {
  return buildEdgeErrorFixture('edge_error_auth', 'Edge state — error: auth', 'AUTH_401', turnId)
}

export function buildEdgeErrorUnknownFixture(turnId = 'edge-error-unknown'): Fixture {
  return buildEdgeErrorFixture('edge_error_unknown', 'Edge state — error: unknown', 'SOME_UNMAPPED_CODE', turnId)
}
