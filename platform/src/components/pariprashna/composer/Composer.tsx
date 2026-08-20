'use client'

import { useEffect, useRef, useState } from 'react'
import { PickerPopover, type PickerRow } from './PickerPopover'
import type { DepthOption, LengthOption } from '../state/types'
import type { FixtureMode } from '../fixtures'

const MODEL_ROWS: PickerRow<string>[] = [
  { value: 'Auto', label: 'Auto', detail: 'best available' },
  { value: 'Claude Opus', label: 'Claude Opus', meta: 'A · full loop' },
  { value: 'Gemini 2.5 Pro', label: 'Gemini 2.5 Pro', meta: 'A · full loop' },
  { value: 'GPT-4.1', label: 'GPT-4.1', meta: 'A · full loop' },
  { value: 'DeepSeek V4', label: 'DeepSeek V4', meta: 'B · compact' },
  { value: 'Kimi K2 · OpenRouter', label: 'Kimi K2 · OpenRouter', meta: 'C · bundle' },
]

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
  onSubmit: (text: string, mode: FixtureMode) => void
  onStop: () => void
  /** §5.3 `empty`: "focus is already in the composer." Only relevant on mount. */
  autoFocus?: boolean
}

/** Maps the composer's Depth choice to which fixture the stub plays (see the build report for why). */
function depthToFixtureMode(depth: DepthOption): FixtureMode {
  if (depth === 'Quick') return 'single'
  return 'adaptive'
}

export function Composer({ streaming, onSubmit, onStop, autoFocus }: ComposerProps) {
  const [text, setText] = useState('')
  const [model, setModel] = useState('Claude Opus')
  const [depth, setDepth] = useState<DepthOption>('Auto')
  const [length, setLength] = useState<LengthOption>('Auto')
  const [openPicker, setOpenPicker] = useState<'model' | 'depth' | 'length' | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  // Mount-only: the design plan is explicit that `autoFocus` re-triggering on
  // every re-render (e.g. after each submit) would steal focus mid-typing —
  // this only ever runs once, matching the plain `<textarea autofocus>`
  // semantics the empty state's copy describes.
  useEffect(() => {
    if (autoFocus) textareaRef.current?.focus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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
    onSubmit(trimmed, depthToFixtureMode(depth))
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
          valueLabel={model.replace(' · OpenRouter', '')}
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
        <span className="ml-auto font-mono" style={{ fontSize: 10, color: 'var(--pp-gold-tertiary)', letterSpacing: '0.03em' }}>
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
