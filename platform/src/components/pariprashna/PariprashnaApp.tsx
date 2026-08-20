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
import { useVisualViewport } from './hooks/useVisualViewport'
import type { FixtureMode } from './fixtures'
import type { ThreadState } from './state/types'

/**
 * The transport-agnostic stream contract the surface consumes. Both
 * `useFixtureStream` (dev replay) and `useLiveStream` (real SSE) satisfy it:
 * `submit(text, mode)` — the fixture host plays `mode` as a canned fixture; the
 * live host maps `mode` onto a `reading_depth` and calls the real route.
 */
export interface PariprashnaStream {
  state: ThreadState
  submit: (text: string, mode: FixtureMode) => string | void
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

/** Fixture-replay host (default): canned event streams, no backend. */
function PariprashnaAppFixture({ chartPin }: { chartPin: ChartPin }) {
  const stream = useFixtureStream()
  return <PariprashnaSurface chartPin={chartPin} stream={stream} showDevPicker />
}

/** Live host: real SSE via `/api/pariprashna`. Maps the composer's fixture
 *  `mode` onto a `reading_depth` (single → auto, everything else → deep_dive). */
function PariprashnaAppLive({ chartPin, chartId }: { chartPin: ChartPin; chartId: string }) {
  const live = useLiveStream(chartId)
  const stream = useMemo<PariprashnaStream>(
    () => ({
      state: live.state,
      submit: (text: string, mode: FixtureMode) =>
        live.submit(text, { reading_depth: mode === 'single' ? 'auto' : 'deep_dive' }),
      stop: live.stop,
    }),
    [live],
  )
  return <PariprashnaSurface chartPin={chartPin} stream={stream} showDevPicker={false} />
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
}: {
  chartPin: ChartPin
  stream: PariprashnaStream
  showDevPicker: boolean
}) {
  const { state, submit, stop } = stream
  const activeTurn = state.turns[state.turns.length - 1]
  const streaming = !!activeTurn && !['settled', 'interrupted', 'errored'].includes(activeTurn.status)

  // §9.2: composer pinned via `visualViewport`, never a `100vh` guess. The
  // shell is sized to (and, on viewports where the API is supported, pinned
  // to) the VISIBLE area — so when a mobile keyboard opens and shrinks the
  // visual viewport, the shell shrinks with it and the composer (its last
  // flex child) stays above the keyboard instead of being pushed underneath
  // it. `100dvh` is the fallback for engines without `visualViewport` (SSR
  // hydration, legacy browsers) — a dynamic-viewport unit, never the static
  // `100vh` that caused this defect.
  const vv = useVisualViewport()
  const shellHeight = vv.supported && vv.height != null ? `${vv.height}px` : '100dvh'

  const handleSubmit = useCallback(
    (text: string, mode: FixtureMode) => {
      submit(text, mode)
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
      <div
        className="pp-root flex flex-col"
        data-vh-source={vv.supported ? 'visual-viewport' : 'fallback'}
        style={{ position: 'fixed', inset: 0, height: shellHeight }}
      >
        <div className="flex-1 flex gap-3.5 p-4 items-stretch min-h-0" style={{ maxWidth: 1220, width: '100%', margin: '0 auto' }}>
          <div
            className="flex-1 min-w-0 flex flex-col rounded-[14px] overflow-hidden relative"
            style={{ background: 'var(--pp-surface)', border: '1px solid var(--pp-rule)', minHeight: '70vh' }}
          >
            <ThreadHeader chartPin={chartPin} />
            {state.turns.length === 0 ? (
              <EmptyState examplePrompts={EXAMPLE_PROMPTS} onPick={(text) => handleSubmit(text, 'adaptive')} />
            ) : (
              <Transcript turns={state.turns} />
            )}
            {showDevPicker && <DevFixturePicker onPick={handleDevPick} disabled={streaming} />}
            <Composer streaming={streaming} onSubmit={handleSubmit} onStop={handleStop} />
          </div>
          <RightDock turns={state.turns} />
        </div>
      </div>
      <OverlayLayer turns={state.turns} />
    </DockControllerProvider>
  )
}
