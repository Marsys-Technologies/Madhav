/**
 * Lane P2-C (PPR-09/16) — the composer's Model pill, made honest.
 *
 * Before this lane, `Composer.tsx`'s `MODEL_ROWS` was a hand-written mockup
 * list ('Claude Opus', 'GPT-4.1', 'Kimi K2 · OpenRouter', …) whose `value`
 * strings did not correspond to any real `@/lib/models/registry` id. Even had
 * the composer wired the selection through to the request body (it did not —
 * `model` was local state the submit handler never read), `isValidModelId`
 * would have rejected every one of those labels and silently fallen back to
 * the stack's synthesis primary — a second, independent way the pill lied.
 *
 * This module derives the picker rows from the SAME registry the server binds
 * `model_id` against (`bindTurnParams` in `pipeline/safety_gate.ts`), so a
 * selection here is always a valid id there. No wrapper-local constant
 * duplicates the registry's data (§N.7 item 3) — a model added, renamed, or
 * retired in the registry changes this list on the next render, not on the
 * next edit to this file.
 */

import { MODELS, type ModelTier } from '@/lib/models/registry'
import type { PickerRow } from './PickerPopover'

/** Registry `label` substrings that mark a row as not meant for a user picker
 *  (deprecated, unavailable, an internal-only alias, EOL, or degraded). */
const NOT_USER_FACING = /\[(unavailable|deprecated|internal label only|eol|degraded)\]/i

const TIER_META: Record<ModelTier, string> = {
  premium: 'A · deepest',
  mid: 'B · balanced',
  worker: 'C · fast',
}

/**
 * Synthesis-capable, user-facing models, in registry order. `role` filters to
 * 'synthesis' | 'both' — a 'planner'/'worker'-only routing entry is never
 * something a reader should pick as their reading's synthesis model.
 */
export function getSynthesisModelRows(): PickerRow<string>[] {
  const rows: PickerRow<string>[] = [{ value: 'auto', label: 'Auto', detail: 'best available' }]
  for (const m of MODELS) {
    if (m.role !== 'synthesis' && m.role !== 'both') continue
    if (NOT_USER_FACING.test(m.label)) continue
    rows.push({ value: m.id, label: m.label, meta: TIER_META[m.tier] })
  }
  return rows
}
