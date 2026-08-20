'use client'

import '../pariprashna/pariprashna.css'
// PB-6 (SAMĀPTI): samiksha.css was never imported anywhere, so the
// spec-conformant KalaRekha/PredictionCard pair's CSS classes (.pp-kala-rekha*,
// .pp-prediction-card*) had no effect wherever they were used — now mounted
// live in the right dock (dock/PredictionCard.tsx).
import './samiksha/samiksha.css'
import { useCallback, useMemo } from 'react'
import { ThreadHeader, type ChartPin } from './ThreadHeader'
import { Transcript } from './Transcript'
import { EmptyState } from './EmptyState'
import { Composer } from './composer/Composer'
import { RightDock } from './dock/RightDock'
import { OverlayLayer } from './overlay/OverlayLayer'
import { DockControllerProvider } from './dock/DockController'
import { useFixtureStream } from './state/useFixtureStream'
import { useLiveStream } from './hooks/useLiveStream'
import type { FixtureMode } from './fixtures'
import type { SubmitControls, ThreadState } from './state/types'

/**
 * The transport-agnostic stream contract the surface consumes. Both
 * `useFixtureStream` (dev replay) and `useLiveStream` (real SSE) satisfy it:
 * `submit(text, mode, controls?)` — the fixture host plays `mode` as a canned
 * fixture and ignores `controls`; the live host reads `controls` (lane P2-C —
 * `SubmitControls`, sent honestly by the composer's own picker state) to build
 * the real request, no longer re-deriving `reading_depth` from `mode`. Callers
 * with no real picker state (`EmptyState`'s example prompts, the dev fixture
 * picker) omit `controls`; the live host applies the same 'auto'/'standard'
 * defaults the request already had.
 */
export interface PariprashnaStream {
  state: ThreadState
  submit: (text: string, mode: FixtureMode, controls?: SubmitControls) => string | void
  stop: (turnId: string) => void
}

const EXAMPLE_PROMPTS = [
  'What does this period ask of my career?',
  'Is a career change on the cards over the next two years?',
  'When should I not initiate anything new?',
]

/** Dev/QA only — exercises fixture modes the Depth control doesn't reach (gap, reconnect, the two lane-C-2-recorded replays). Not part of the mockup's production chrome. */
function DevFixturePicker({ onPick, disabled }: { onPick: (mode: FixtureMode) => void; disabled: boolean }) {
  if (process.env.NODE_ENV === 'production') return null
  const modes: { mode: FixtureMode; label: string }[] = [
    { mode: 'adaptive', label: 'Adaptive · 3 passes' },
    { mode: 'single', label: 'Single pass' },
    { mode: 'gap', label: 'Honest gap' },
    { mode: 'reconnect', label: 'Reconnect mid-pass' },
    { mode: 'c2-single', label: 'C-2 recorded: single' },
    { mode: 'c2-gap', label: 'C-2 recorded: gap' },
  ]
  return (
    <div className="flex flex-wrap gap-1.5 px-6 py-2" style={{ borderTop: '1px solid var(--pp-rule)' }}>
      <span style={{ fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--pp-gold-tertiary)', marginRight: 4, alignSelf: 'center' }}>
        Dev · fixture
      </span>
      {modes.map((m) => (
        <button
          key={m.mode}
          type="button"
          disabled={disabled}
          onClick={() => onPick(m.mode)}
          className="rounded"
          style={{ fontSize: 11, color: 'var(--pp-ink-dim)', border: '1px solid var(--pp-rule)', background: 'none', padding: '4px 9px', opacity: disabled ? 0.4 : 1 }}
        >
          {m.label}
        </button>
      ))}
    </div>
  )
}

/**
 * Paripraśna app entry. Chooses the transport HOST at mount:
 *   • live SSE against `/api/pariprashna` when a chartId is present AND the
 *     `NEXT_PUBLIC_PARIPRASHNA_LIVE` flag is on (the deploy-behind-a-flag path);
 *   • otherwise the fixture-replay host (dev / component work / no chartId).
 * The two hosts are distinct components so each calls exactly one transport
 * hook (React hook rules) and both render the same `<PariprashnaSurface>`.
 */
export function PariprashnaApp({ chartPin, chartId }: { chartPin: ChartPin; chartId?: string }) {
  const liveEnabled = process.env.NEXT_PUBLIC_PARIPRASHNA_LIVE === '1' && !!chartId
  if (liveEnabled && chartId) {
    return <PariprashnaAppLive chartPin={chartPin} chartId={chartId} />
  }
  return <PariprashnaAppFixture chartPin={chartPin} />
}

/** Fixture-replay host (default): canned event streams, no backend — no real
 *  chart id, so `chartId` is left undefined (see `AnswerRegion`'s guard). */
function PariprashnaAppFixture({ chartPin }: { chartPin: ChartPin }) {
  const stream = useFixtureStream()
  return <PariprashnaSurface chartPin={chartPin} stream={stream} showDevPicker />
}

/**
 * Live host: real SSE via `/api/pariprashna`. Lane P2-C: `reading_depth`,
 * `model_id`, and `length_tier` now come from the composer's OWN picker state
 * (`controls`) rather than being re-derived from the dev-fixture `mode`
 * (which used to force `deep_dive` for every Depth selection except "Quick" —
 * see the P2-C build report for how that mapping was discovered). `mode` is
 * ignored here entirely; it exists only for the fixture host.
 */
function PariprashnaAppLive({ chartPin, chartId }: { chartPin: ChartPin; chartId: string }) {
  const live = useLiveStream(chartId)
  const stream = useMemo<PariprashnaStream>(
    () => ({
      state: live.state,
      submit: (text: string, _mode: FixtureMode, controls?: SubmitControls) =>
        live.submit(text, {
          reading_depth: controls?.readingDepth ?? 'auto',
          model_id: controls?.modelId,
          length_tier: controls?.lengthTier ?? 'standard',
        }),
      stop: live.stop,
    }),
    [live],
  )
  return <PariprashnaSurface chartPin={chartPin} stream={stream} showDevPicker={false} chartId={chartId} />
}

/**
 * The presentational shell — transport-agnostic. Receives a `PariprashnaStream`
 * and renders header / transcript / composer / dock / overlay. Identical markup
 * for both hosts; only the dev fixture picker is fixture-host-only.
 */
function PariprashnaSurface({
  chartPin,
  stream,
  showDevPicker,
  chartId,
}: {
  chartPin: ChartPin
  stream: PariprashnaStream
  showDevPicker: boolean
  /** Real chart id (live host only) — threaded down to `AnswerRegion` so it
   *  can mount `LogToSamiksha` with a genuine chart scope (lane P2-A / G2-A). */
  chartId?: string
}) {
  const { state, submit, stop } = stream
  const activeTurn = state.turns[state.turns.length - 1]
  const streaming = !!activeTurn && !['settled', 'interrupted', 'errored'].includes(activeTurn.status)

  const handleSubmit = useCallback(
    (text: string, mode: FixtureMode, controls?: SubmitControls) => {
      submit(text, mode, controls)
    },
    [submit],
  )

  const handleStop = useCallback(() => {
    if (activeTurn) stop(activeTurn.id)
  }, [activeTurn, stop])

  const handleDevPick = useCallback(
    (mode: FixtureMode) => {
      const fallbackText =
        mode === 'gap'
          ? 'Should I take the Dubai offer or the Singapore one?'
          : mode === 'single'
            ? 'And within that, when specifically should I not initiate anything new?'
            : 'Is a career change on the cards over the next two years?'
      submit(fallbackText, mode)
    },
    [submit],
  )

  return (
    <DockControllerProvider defaultOpen={true}>
      <div className="pp-root flex flex-col" style={{ minHeight: '100vh' }}>
        <div className="flex-1 flex gap-3.5 p-4 items-stretch min-h-0" style={{ maxWidth: 1220, width: '100%', margin: '0 auto' }}>
          <div
            className="flex-1 min-w-0 flex flex-col rounded-[14px] overflow-hidden relative"
            style={{ background: 'var(--pp-surface)', border: '1px solid var(--pp-rule)', minHeight: '70vh' }}
          >
            <ThreadHeader chartPin={chartPin} />
            {state.turns.length === 0 ? (
              <EmptyState examplePrompts={EXAMPLE_PROMPTS} onPick={(text) => handleSubmit(text, 'adaptive')} />
            ) : (
              <Transcript turns={state.turns} chartId={chartId} />
            )}
            {showDevPicker && <DevFixturePicker onPick={handleDevPick} disabled={streaming} />}
            <Composer
              streaming={streaming}
              onSubmit={handleSubmit}
              onStop={handleStop}
              depthReceived={activeTurn?.readingDepthReceived}
            />
          </div>
          <RightDock turns={state.turns} />
        </div>
      </div>
      <OverlayLayer turns={state.turns} />
    </DockControllerProvider>
  )
}
