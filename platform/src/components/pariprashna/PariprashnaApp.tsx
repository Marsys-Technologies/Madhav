'use client'

import '../pariprashna/pariprashna.css'
// PB-6 (SAMĀPTI): samiksha.css was never imported anywhere, so the
// spec-conformant KalaRekha/PredictionCard pair's CSS classes (.pp-kala-rekha*,
// .pp-prediction-card*) had no effect wherever they were used — now mounted
// live in the right dock (dock/PredictionCard.tsx).
import './samiksha/samiksha.css'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { ThreadHeader, type ChartPin } from './ThreadHeader'
import { Transcript } from './Transcript'
import { EmptyState } from './EmptyState'
import { ArrivalLine, type ArrivalLineData } from './ArrivalLine'
import { Composer } from './composer/Composer'
import { RightDock } from './dock/RightDock'
import { Sidebar } from './history/Sidebar'
import type { ThreadSummary } from './history/types'
import { OverlayLayer } from './overlay/OverlayLayer'
import { DockControllerProvider } from './dock/DockController'
import { useFixtureStream } from './state/useFixtureStream'
import { useLiveStream } from './hooks/useLiveStream'
import { FIXTURE_ARRIVAL_LINE } from './fixtures/arrival'
import { useVisualViewport } from './hooks/useVisualViewport'
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

/** Truncates a user question into a sidebar-row-length auto-generated title (§10.1). */
function autoTitle(userText: string): string {
  const trimmed = userText.trim()
  if (trimmed.length <= 46) return trimmed
  return `${trimmed.slice(0, 45)}…`
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
  return <PariprashnaSurface chartPin={chartPin} chartId="fixture-chart" stream={stream} showDevPicker isFixtureHost />
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
  return <PariprashnaSurface chartPin={chartPin} chartId={chartId} stream={stream} showDevPicker={false} isFixtureHost={false} />
}

/**
 * The presentational shell — transport-agnostic. Receives a `PariprashnaStream`
 * and renders header / transcript / composer / dock / overlay. Identical markup
 * for both hosts; only the dev fixture picker is fixture-host-only.
 */
function PariprashnaSurface({
  chartPin,
  chartId,
  stream,
  showDevPicker,
  isFixtureHost,
}: {
  chartPin: ChartPin
  /** Real chart id (live host only) — threaded down to `AnswerRegion` so it
   *  can mount `LogToSamiksha` with a genuine chart scope (lane P2-A / G2-A). */
  chartId: string
  stream: PariprashnaStream
  showDevPicker: boolean
  isFixtureHost: boolean
}) {
  const { state, submit, stop } = stream
  const activeTurn = state.turns[state.turns.length - 1]
  const streaming = !!activeTurn && !['settled', 'interrupted', 'errored'].includes(activeTurn.status)

  // History sidebar (Lane F-1, §10.1). V3-E-012a: the live session's own
  // thread (below) is now MERGED with real persisted history fetched once
  // per chart via GET /api/conversations?readingsOnly=true — the receipt
  // discriminator (lib/conversations.ts docblock) keeps legacy consume/
  // consult rows out. Fetched ONCE at mount/chart-change, BEFORE any turn
  // this session can possibly have written — so the live thread (added
  // separately below, always first) can never collide with a fetched row
  // for the same conversation; no id-matching dedup is needed or attempted.
  // What this does NOT do (Native Surrogate ruling, decision event
  // f3b88219-432f-4096-999c-07f6700f6406, referred to S2 as V3-E-012b):
  // selecting a FETCHED historical row does not load its messages into the
  // reading pane — that needs the real backend `conversation_id` threaded
  // through `useLiveStream`'s wire decoder/reducer (S2 territory; today's
  // `WireEvent` shape for `turn.open` drops the field the SSE payload
  // already carries), which this shell may not touch.
  const [titleOverride, setTitleOverride] = useState<string | null>(null)
  const [pastReadings, setPastReadings] = useState<ThreadSummary[]>([])
  const [unavailableNotice, setUnavailableNotice] = useState(false)
  const threadId = useMemo(() => `session-${chartId}`, [chartId])

  useEffect(() => {
    if (isFixtureHost) return
    let cancelled = false
    fetch(`/api/conversations?chartId=${encodeURIComponent(chartId)}&module=consume&readingsOnly=true`)
      .then((r) => (r.ok ? r.json() : null))
      .then(
        (data: {
          conversations: {
            id: string
            chart_id: string
            title: string | null
            first_message_snippet: string | null
            updated_at: string
            created_at: string
          }[]
        } | null) => {
          if (cancelled || !data?.conversations) return
          setPastReadings(
            data.conversations.map((c) => ({
              id: c.id,
              chartId: c.chart_id,
              chartName: chartPin.name,
              title: c.title ?? c.first_message_snippet ?? 'Untitled reading',
              updatedAtMs: new Date(c.updated_at ?? c.created_at).getTime(),
              active: false,
              streaming: false,
            })),
          )
        },
      )
      .catch(() => {
        // Honest absence, not a thrown error into the shell: the sidebar
        // simply shows only the live session's own thread, same as before
        // this fetch existed.
      })
    return () => {
      cancelled = true
    }
  }, [chartId, isFixtureHost, chartPin.name])

  const threads = useMemo<ThreadSummary[]>(() => {
    const live: ThreadSummary[] =
      state.turns.length === 0
        ? []
        : (() => {
            const firstTurn = state.turns[0]
            const lastTurn = state.turns[state.turns.length - 1]
            return [
              {
                id: threadId,
                chartId,
                chartName: chartPin.name,
                title: titleOverride ?? autoTitle(firstTurn.userText),
                updatedAtMs: lastTurn.openedAtMs,
                active: true,
                streaming,
              },
            ]
          })()
    return [...live, ...pastReadings]
  }, [state.turns, threadId, chartId, chartPin.name, titleOverride, streaming, pastReadings])

  const handleSidebarSelect = useCallback(
    (id: string) => {
      if (id === threadId) return // already the live thread — no-op, as before
      // V3-E-012a/b (surrogate ruling B4): a historical row is real and
      // visible now, but opening its content is not yet wired (S2's,
      // V3-E-012b) — an honest, dismissable notice, never a silent dead
      // click implying content loaded.
      setUnavailableNotice(true)
    },
    [threadId],
  )

  useEffect(() => {
    if (!unavailableNotice) return
    const timer = setTimeout(() => setUnavailableNotice(false), 3200)
    return () => clearTimeout(timer)
  }, [unavailableNotice])

  const handleSidebarRename = useCallback(
    (id: string, title: string) => {
      // V3-E-012a follow-up: `titleOverride` only ever feeds the LIVE
      // thread's title (see the `threads` useMemo). Before pastReadings
      // existed there was only ever one row, so `id` was always the live
      // thread's — now that fetched historical rows share the same
      // rename affordance, a rename on one of THEM must not silently
      // relabel the unrelated live thread instead. Same honest-notice
      // treatment as selecting a historical row (surrogate ruling B4);
      // renaming a past reading isn't wired yet either (it was never
      // persisted server-side even for the live thread — local-only
      // today — so a fetched row's rename has nowhere real to go).
      if (id !== threadId) {
        setUnavailableNotice(true)
        return
      }
      setTitleOverride(title)
    },
    [threadId],
  )

  // Arrival line (§3.2, J2, AC-16) — fixture-only sample data on the fixture
  // host; the live host renders nothing until the real L1/Kāla wiring lands
  // (P4-F). See `ArrivalLine.tsx`'s header note.
  const arrival: ArrivalLineData | null = isFixtureHost && state.turns.length > 0 ? FIXTURE_ARRIVAL_LINE : null

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
      <div
        className="pp-root flex flex-col"
        data-vh-source={vv.supported ? 'visual-viewport' : 'fallback'}
        style={{ position: 'fixed', inset: 0, height: shellHeight }}
      >
        <div className="flex-1 flex gap-3.5 p-4 items-stretch min-h-0" style={{ maxWidth: 1220, width: '100%', margin: '0 auto' }}>
          <div style={{ position: 'relative', display: 'flex', flex: 'none' }}>
            <Sidebar threads={threads} onSelect={handleSidebarSelect} onRename={handleSidebarRename} />
            {unavailableNotice && (
              // V3-E-012b interim affordance (surrogate ruling B4): honest,
              // not a silent dead click — opening a past reading's content
              // is not wired yet (referred to S2).
              <div
                role="status"
                data-testid="pp-sidebar-select-unavailable"
                style={{
                  position: 'absolute',
                  bottom: 8,
                  left: 8,
                  right: 8,
                  padding: '8px 10px',
                  borderRadius: 8,
                  background: 'var(--pp-panel)',
                  border: '1px solid var(--pp-rule-strong)',
                  color: 'var(--pp-ink-dim)',
                  fontSize: 11.5,
                  lineHeight: 1.35,
                  zIndex: 5,
                }}
              >
                Opening a past reading isn&apos;t available yet — it&apos;s saved, just not openable in this build.
              </div>
            )}
          </div>
          <div
            data-testid="pp-main-column"
            className="flex-1 min-w-0 flex flex-col rounded-[14px] overflow-hidden relative"
            style={{ background: 'var(--pp-surface)', border: '1px solid var(--pp-rule)', minHeight: '70vh' }}
          >
            <ThreadHeader chartPin={chartPin} />
            <ArrivalLine arrival={arrival} />
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
              autoFocus={state.turns.length === 0}
            />
          </div>
          <RightDock turns={state.turns} />
        </div>
      </div>
      <OverlayLayer turns={state.turns} />
    </DockControllerProvider>
  )
}
