'use client'

import '../pariprashna/pariprashna.css'
import { useCallback } from 'react'
import { ThreadHeader, type ChartPin } from './ThreadHeader'
import { Transcript } from './Transcript'
import { EmptyState } from './EmptyState'
import { Composer } from './composer/Composer'
import { RightDock } from './dock/RightDock'
import { OverlayLayer } from './overlay/OverlayLayer'
import { DockControllerProvider } from './dock/DockController'
import { useFixtureStream } from './state/useFixtureStream'
import type { FixtureMode } from './fixtures'

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

export function PariprashnaApp({ chartPin }: { chartPin: ChartPin }) {
  const { state, submit, stop } = useFixtureStream()
  const activeTurn = state.turns[state.turns.length - 1]
  const streaming = !!activeTurn && !['settled', 'interrupted', 'errored'].includes(activeTurn.status)

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
              <Transcript turns={state.turns} />
            )}
            <DevFixturePicker onPick={handleDevPick} disabled={streaming} />
            <Composer streaming={streaming} onSubmit={handleSubmit} onStop={handleStop} />
          </div>
          <RightDock turns={state.turns} />
        </div>
      </div>
      <OverlayLayer turns={state.turns} />
    </DockControllerProvider>
  )
}
