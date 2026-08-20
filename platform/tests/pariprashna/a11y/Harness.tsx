/**
 * Test-only re-composition of `PariprashnaApp.tsx`'s internal
 * `PariprashnaSurface` (not exported — it's a private implementation
 * detail of that module). This mounts the SAME real components in the SAME
 * arrangement — `Transcript` / `Composer` / `RightDock` / `OverlayLayer`
 * under one `DockControllerProvider` — so a11y assertions run against
 * production render output for an arbitrary `ThreadState`, not a
 * hand-rolled substitute markup.
 */
'use client'

import { Transcript } from '@/components/pariprashna/Transcript'
import { Composer } from '@/components/pariprashna/composer/Composer'
import { RightDock } from '@/components/pariprashna/dock/RightDock'
import { OverlayLayer } from '@/components/pariprashna/overlay/OverlayLayer'
import { DockControllerProvider } from '@/components/pariprashna/dock/DockController'
import type { TurnState } from '@/components/pariprashna/state/types'

export function Harness({ turns }: { turns: TurnState[] }) {
  const activeTurn = turns[turns.length - 1]
  const streaming = !!activeTurn && !['settled', 'interrupted', 'errored'].includes(activeTurn.status)
  return (
    <DockControllerProvider defaultOpen={true}>
      <div className="pp-root flex flex-col">
        <div className="flex-1 flex gap-3.5 p-4 items-stretch min-h-0">
          <div className="flex-1 min-w-0 flex flex-col rounded-[14px] overflow-hidden relative">
            <Transcript turns={turns} />
            <Composer streaming={streaming} onSubmit={() => {}} onStop={() => {}} />
          </div>
          <RightDock turns={turns} />
        </div>
      </div>
      <OverlayLayer turns={turns} />
    </DockControllerProvider>
  )
}
