'use client'

import { useRef, useState } from 'react'
import { PickerPopover, type PickerRow } from './PickerPopover'
import { getSynthesisModelRows } from './model_options'
import type { DepthOption, LengthOption, SubmitControls } from '../state/types'
import type { FixtureMode } from '../fixtures'

/** Real registry ids (`@/lib/models/registry`) — see `model_options.ts`. The
 *  previous hardcoded list ('Claude Opus', 'Kimi K2 · OpenRouter', …) named no
 *  model the registry actually has; selecting one would have silently fallen
 *  back to the stack default even if the selection had been wired through
 *  (it previously was not — see the P2-C build report). */
const MODEL_ROWS: PickerRow<string>[] = getSynthesisModelRows()

const DEPTH_ROWS: PickerRow<DepthOption>[] = [
  { value: 'Auto', label: 'Auto', detail: 'from the question' },
  { value: 'Quick', label: 'Quick', detail: 'pinpoint lookup' },
  { value: 'Standard', label: 'Standard', detail: 'whole-chart read' },
  { value: 'Deep dive', label: 'Deep dive', detail: '100% coverage' },
]

const LENGTH_ROWS: PickerRow<LengthOption>[] = [
  { value: 'Auto', label: 'Auto', detail: 'matched to weight' },
  { value: 'Concise', label: 'Concise', detail: 'verdict + essentials' },
  { value: 'Balanced', label: 'Balanced', detail: 'standard' },
  { value: 'Detailed', label: 'Detailed', detail: 'every nuance' },
]

const LINE_HEIGHT_PX = 22.5 // Inter 15/22 with a little breathing room
const MIN_LINES = 3
const MAX_LINES = 8

export interface ComposerProps {
  streaming: boolean
  onSubmit: (text: string, mode: FixtureMode, controls: SubmitControls) => void
  onStop: () => void
  /**
   * Lane P2-C — the ACTUAL depth the last turn's `scope_tuple` resolved to
   * (server-derived; `null` when unknown — flag-OFF deploy, no turn yet, or a
   * turn the planner never scored). Rendered as an honest disclosure distinct
   * from whatever `depth` below is currently selected for the NEXT turn.
   */
  depthReceived?: string | null
}

/** Maps the composer's Depth choice to which fixture the stub plays (see the build report for why). */
function depthToFixtureMode(depth: DepthOption): FixtureMode {
  if (depth === 'Quick') return 'single'
  return 'adaptive'
}

/**
 * Lane P2-C — honest request mapping. `ReadingDepthSchema` only has two real
 * values (`auto` | `deep_dive`; see `protocol/events.ts`), so `Quick`,
 * `Standard`, and `Auto` are mapped to the SAME wire value: none of them are
 * separately real on the backend today, and pretending otherwise would just
 * move the lying pill from the picker into this function. Exported for the
 * colocated unit test — pure, no component needed to exercise it.
 */
export function depthToReadingDepth(depth: DepthOption): SubmitControls['readingDepth'] {
  return depth === 'Deep dive' ? 'deep_dive' : 'auto'
}

/** Lane P2-C — honest request mapping onto the real `LengthTierSchema` values. */
export function lengthToLengthTier(length: LengthOption): SubmitControls['lengthTier'] {
  if (length === 'Concise') return 'brief'
  if (length === 'Detailed') return 'exhaustive'
  return 'standard' // Auto | Balanced — both mean "no override" today
}

/** Lane P2-C — 'auto' sentinel → no `model_id` override (stack default binds). */
export function modelToModelId(model: string): string | undefined {
  return model === 'auto' ? undefined : model
}

export function Composer({ streaming, onSubmit, onStop, depthReceived }: ComposerProps) {
  const [text, setText] = useState('')
  const [model, setModel] = useState('auto')
  const [depth, setDepth] = useState<DepthOption>('Auto')
  const [length, setLength] = useState<LengthOption>('Auto')
  const [openPicker, setOpenPicker] = useState<'model' | 'depth' | 'length' | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  const modelLabel = MODEL_ROWS.find((r) => r.value === model)?.label ?? model

  const footNote =
    depth === 'Auto' && length === 'Auto'
      ? 'acharya-grade · one register'
      : `acharya-grade · ${depth !== 'Auto' ? depth.toLowerCase() + ' ' : ''}${length !== 'Auto' ? length.toLowerCase() + ' ' : ''}override`.replace(/\s+/g, ' ').trim()

  function autogrow() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    const maxPx = LINE_HEIGHT_PX * MAX_LINES
    el.style.height = `${Math.min(el.scrollHeight, maxPx)}px`
  }

  function submit() {
    const trimmed = text.trim()
    if (!trimmed || streaming) return
    onSubmit(trimmed, depthToFixtureMode(depth), {
      modelId: modelToModelId(model),
      readingDepth: depthToReadingDepth(depth),
      lengthTier: lengthToLengthTier(length),
    })
    setText('')
    requestAnimationFrame(() => {
      const el = textareaRef.current
      if (el) el.style.height = `${LINE_HEIGHT_PX * MIN_LINES}px`
    })
  }

  return (
    <div className="px-5 pb-[18px] pt-3.5" style={{ borderTop: '1px solid var(--pp-rule)', background: 'var(--pp-panel)' }}>
      <div className="flex items-center gap-2 flex-wrap mb-2.5 px-0.5">
        <PickerPopover
          valueLabel={modelLabel}
          rows={MODEL_ROWS}
          selected={model}
          open={openPicker === 'model'}
          onOpenChange={(o) => setOpenPicker(o ? 'model' : null)}
          onSelect={setModel}
        />
        <PickerPopover
          eyebrow="Depth"
          valueLabel={depth}
          rows={DEPTH_ROWS}
          selected={depth}
          open={openPicker === 'depth'}
          onOpenChange={(o) => setOpenPicker(o ? 'depth' : null)}
          onSelect={setDepth}
        />
        <PickerPopover
          eyebrow="Length"
          valueLabel={length}
          rows={LENGTH_ROWS}
          selected={length}
          open={openPicker === 'length'}
          onOpenChange={(o) => setOpenPicker(o ? 'length' : null)}
          onSelect={setLength}
        />
        <span className="ml-auto font-mono flex items-center gap-2" style={{ fontSize: 10, color: 'var(--pp-gold-tertiary)', letterSpacing: '0.03em' }}>
          {/* Lane P2-C: honest disclosure of what the LAST turn actually got,
              never a guess and never the same field as the picker above (which
              is the request for the NEXT turn). Renders nothing when unknown. */}
          {depthReceived && <span title="Depth the last reading actually received">depth received: {depthReceived}</span>}
          {footNote}
        </span>
      </div>

      <div
        className="flex items-end gap-3 rounded-xl px-3.5 py-3"
        style={{ border: '1px solid var(--pp-rule)', background: 'var(--pp-surface)', transition: 'border-color 0.2s var(--pp-ease)' }}
      >
        <textarea
          ref={textareaRef}
          className="pp-composer-field flex-1 bg-transparent outline-none border-none"
          style={{ color: 'var(--pp-ink)', height: LINE_HEIGHT_PX * MIN_LINES }}
          placeholder="Ask the chart…"
          value={text}
          rows={MIN_LINES}
          disabled={streaming}
          onChange={(e) => {
            setText(e.target.value)
            autogrow()
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault()
              submit()
            }
          }}
        />
        {streaming ? (
          <button
            type="button"
            onClick={onStop}
            title="Stop"
            aria-label="Stop"
            className="flex-none w-[34px] h-[34px] rounded-[9px] flex items-center justify-center"
            style={{ border: '1px solid var(--pp-rule)', background: 'var(--pp-tint)', color: 'var(--pp-gold)' }}
          >
            <span aria-hidden style={{ width: 11, height: 11, background: 'var(--pp-gold)', borderRadius: 2 }} />
          </button>
        ) : (
          <button
            type="button"
            onClick={submit}
            title="Send"
            aria-label="Send"
            disabled={!text.trim()}
            className="flex-none w-[34px] h-[34px] rounded-[9px] flex items-center justify-center font-mono"
            style={{
              border: '1px solid var(--pp-rule)',
              background: 'var(--pp-tint)',
              color: text.trim() ? 'var(--pp-gold)' : 'var(--pp-gold-tertiary)',
            }}
          >
            ↑
          </button>
        )}
      </div>
    </div>
  )
}
