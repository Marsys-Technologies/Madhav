'use client'

import type { TurnState } from '../state/types'
import { useDockController } from '../dock/DockController'
import { CitationCard } from './CitationCard'

/**
 * The overlay layer (§8.1 component tree). Model/Depth/Length pickers are
 * NOT hosted here — they're small anchored popovers that are children of
 * their own pill (`composer/PickerPopover.tsx`), exactly as the approved
 * mockup builds them (position:absolute off the triggering button, not a
 * portal), so there is nothing to lift into a shared layer for them.
 * `AuditDrawer` (§8.1) is a Phase-2/entitlement-gated surface — out of
 * scope for this build; this layer currently hosts only the one overlay
 * Phase 1 actually needs: the mobile citation bottom sheet (§9.2), which
 * DOES need to be layered above everything since it's a scrim + sheet.
 */
export function OverlayLayer({ turns }: { turns: TurnState[] }) {
  const { mobileSheetCitation, closeMobileSheet } = useDockController()
  if (!mobileSheetCitation) return null
  const turn = turns.find((t) => t.id === mobileSheetCitation.turnId)
  const citation = turn?.citations[mobileSheetCitation.n]
  if (!citation) return null
  return <CitationCard citation={citation} onClose={closeMobileSheet} />
}
