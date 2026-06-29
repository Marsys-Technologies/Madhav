'use client'

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type ChangeEvent,
  type ClipboardEvent,
  type DragEvent,
  type KeyboardEvent,
} from 'react'
import { ArrowUp, Square, Paperclip, X, FileText, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Attachment } from '@/hooks/useAttachments'
import { useDraft } from '@/hooks/useChatPreferences'
import { useTokenCount } from '@/hooks/useTokenCount'
import { SlashCommandMenu } from './SlashCommandMenu'
import type { SlashCommand } from '@/lib/chat-commands'

export interface ComposerHandle {
  focus: () => void
  setValue: (value: string) => void
}

interface Props {
  onSubmit: (text: string, attachments: Attachment[]) => void
  onStop?: () => void
  isStreaming?: boolean
  placeholder?: string
  autoFocus?: boolean
  className?: string
  disabled?: boolean
  attachments: Attachment[]
  onAddFiles: (files: FileList | File[]) => void
  onRemoveAttachment: (id: string) => void
  attachmentsReady: boolean
  /** AC-2 (R7-S6): per-conversation draft key. null → __new__ key. */
  conversationId?: string | null
  tokensEnabled?: boolean
  slashEnabled?: boolean
  slashCommands?: SlashCommand[]
}

export const Composer = forwardRef<ComposerHandle, Props>(function Composer(
  {
    onSubmit,
    onStop,
    isStreaming = false,
    placeholder = 'Reply to Claude…',
    autoFocus = true,
    className,
    disabled = false,
    attachments,
    onAddFiles,
    onRemoveAttachment,
    attachmentsReady,
    conversationId = null,
    tokensEnabled = false,
    slashEnabled = false,
    slashCommands = [],
  },
  ref
) {
  const [draft, setDraft, clearDraft] = useDraft(conversationId)
  const [value, setValue] = useState(draft)
  const [isFocused, setIsFocused] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const [slashActiveIdx, setSlashActiveIdx] = useState(0)
  const [slashBlurTimer, setSlashBlurTimer] = useState<ReturnType<typeof setTimeout> | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { tokenCount, pctUsed } = useTokenCount(tokensEnabled ? value : '')

  // Slash command detection: find /query at start or after space
  const slashQuery = slashEnabled ? (() => {
    const m = value.match(/(?:^| )\/(\w*)$/)
    return m ? m[1] : null
  })() : null

  const slashFiltered = slashQuery !== null
    ? slashCommands.filter(c =>
        c.name.toLowerCase().startsWith(slashQuery.toLowerCase()) ||
        c.description.toLowerCase().includes(slashQuery.toLowerCase())
      ).slice(0, 6)
    : []

  const slashOpen = slashEnabled && slashQuery !== null

  useImperativeHandle(ref, () => ({
    focus: () => textareaRef.current?.focus(),
    setValue,
  }))

  // AC-3: restore draft when conversationId changes.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setValue(draft)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId])

  useEffect(() => {
    if (autoFocus) textareaRef.current?.focus()
  }, [autoFocus])

  // AC-4: clear debounce timer on unmount.
  useEffect(() => {
    return () => {
      if (debounceRef.current !== null) clearTimeout(debounceRef.current)
    }
  }, [])

  function handleChange(v: string) {
    setValue(v)
    if (debounceRef.current !== null) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setDraft(v)
    }, 400)
  }

  function send() {
    const trimmed = value.trim()
    const readyAttachments = attachments.filter(a => a.status === 'ready')
    const hasContent = trimmed.length > 0 || readyAttachments.length > 0
    if (!hasContent || isStreaming || disabled || !attachmentsReady) return
    // AC-5: clear draft before dispatch.
    clearDraft()
    if (debounceRef.current !== null) {
      clearTimeout(debounceRef.current)
      debounceRef.current = null
    }
    onSubmit(trimmed, readyAttachments)
    setValue('')
  }

  function selectSlashCommand(cmd: SlashCommand) {
    if (cmd.run) {
      cmd.run()
    } else {
      // Replace the /query fragment with the template
      const newValue = value.replace(/(?:^|( ))\/\w*$/, (_, space) => (space ?? '') + (cmd.template ?? ''))
      setValue(newValue)
      // Position cursor at end after state update
      requestAnimationFrame(() => {
        const el = textareaRef.current
        if (el) { el.selectionStart = el.selectionEnd = el.value.length }
      })
    }
    setSlashActiveIdx(0)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (slashOpen && slashFiltered.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSlashActiveIdx(i => Math.min(i + 1, slashFiltered.length - 1))
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSlashActiveIdx(i => Math.max(i - 1, 0))
        return
      }
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        const cmd = slashFiltered[slashActiveIdx]
        if (cmd) selectSlashCommand(cmd)
        return
      }
      if (e.key === 'Escape') {
        e.preventDefault()
        // Close slash menu without clearing input
        setValue(v => v + ' ')
        setTimeout(() => setValue(v => v.trimEnd()), 0)
        return
      }
    }
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      send()
      return
    }
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      send()
      return
    }
    if (e.key === 'Escape' && isStreaming && onStop) {
      e.preventDefault()
      onStop()
    }
  }

  function handleFileInput(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) onAddFiles(e.target.files)
    // Reset so the same file can be re-selected after removal.
    e.target.value = ''
  }

  function handlePaste(e: ClipboardEvent<HTMLTextAreaElement>) {
    const files: File[] = []
    for (const item of e.clipboardData.items) {
      if (item.kind === 'file') {
        const f = item.getAsFile()
        if (f) files.push(f)
      }
    }
    if (files.length > 0) {
      e.preventDefault()
      onAddFiles(files)
    }
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragOver(false)
    if (e.dataTransfer.files.length > 0) onAddFiles(e.dataTransfer.files)
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    if (e.dataTransfer.types.includes('Files')) {
      e.preventDefault()
      setIsDragOver(true)
    }
  }

  function handleDragLeave(e: DragEvent<HTMLDivElement>) {
    if (e.currentTarget.contains(e.relatedTarget as Node)) return
    setIsDragOver(false)
  }

  const trimmed = value.trim()
  const hasReadyAttachment = attachments.some(a => a.status === 'ready')
  const canSend = (trimmed.length > 0 || hasReadyAttachment) && attachmentsReady && !disabled
  const showStop = isStreaming && onStop

  return (
    <div className={cn('mx-auto w-full max-w-4xl px-4 pb-3 pt-1 relative', className)}>
      {slashOpen && (
        <SlashCommandMenu
          commands={slashFiltered}
          activeIndex={slashActiveIdx}
          onSelect={selectSlashCommand}
        />
      )}
      {/* consume-composer-card: base class for CSS targeting.
          R11.B B-S4: .consume-shell.r11b-active .consume-composer-card overrides in globals.css
          (1.5rem radius, no shadow, bg matches canvas, gold focus border). */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          'consume-composer-card relative flex flex-col rounded-3xl border border-[rgba(var(--brand-gold-rgb),0.35)] bg-background shadow-sm transition-all duration-200',
          isFocused && 'border-[rgba(var(--brand-gold-rgb),0.75)] shadow-[0_0_0_3px_rgba(var(--brand-gold-rgb),0.15)]',
          isDragOver && 'border-[rgba(var(--brand-gold-rgb),0.90)] ring-4 ring-[var(--brand-gold)]/20 shadow-lg',
          disabled && 'opacity-60'
        )}
      >
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 px-4 pt-3">
            {attachments.map(att => (
              <AttachmentChip
                key={att.id}
                attachment={att}
                onRemove={() => onRemoveAttachment(att.id)}
              />
            ))}
          </div>
        )}
        {/* LOCKED (2026-05-02): plain <textarea rows={3}> — fixed-size composer.
            Do not reintroduce TextareaAutosize / minRows / maxRows / field-sizing.
            Long prompts scroll inside the box. See platform/AGENTS.md "Locked UI design decisions". */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          onFocus={() => {
            setIsFocused(true)
            if (slashBlurTimer) { clearTimeout(slashBlurTimer); setSlashBlurTimer(null) }
          }}
          onBlur={() => {
            setIsFocused(false)
            // 150ms debounce so a menu-item mousedown can fire first
            const t = setTimeout(() => setValue(v => v), 150)
            setSlashBlurTimer(t)
          }}
          placeholder={placeholder}
          rows={3}
          disabled={disabled}
          className={cn(
            'w-full resize-none overflow-y-auto rounded-3xl bg-transparent px-5 py-4 text-[15px] leading-[1.55] text-foreground outline-none placeholder:text-muted-foreground/70 placeholder:transition-colors focus:placeholder:text-muted-foreground/50',
            'disabled:cursor-not-allowed'
          )}
          aria-label="Message composer"
        />
        {value === '/' && (
          <p className="px-5 pb-0.5 text-[11px] text-muted-foreground/70">
            Use{' '}
            <kbd className="rounded border border-border bg-muted px-1 font-mono text-[10px]">⌘K</kbd>
            {' '}for commands
          </p>
        )}
        {tokensEnabled && (
          <p
            className={cn(
              'px-5 pb-0.5 text-[10px] transition-colors',
              pctUsed === null || pctUsed < 75
                ? 'text-zinc-500'
                : pctUsed < 95
                ? 'text-amber-400'
                : 'text-red-400'
            )}
            title={
              pctUsed !== null && pctUsed >= 75
                ? 'Approaching context limit'
                : undefined
            }
          >
            {tokenCount === null
              ? '— tokens'
              : `${tokenCount} tokens · ${pctUsed}%`}
          </p>
        )}
        {tokensEnabled && pctUsed !== null && pctUsed >= 95 && (
          <p className="mx-5 mb-1 rounded-md bg-red-950/40 px-3 py-1.5 text-[11px] text-red-400">
            Context nearly full — consider starting a new conversation
          </p>
        )}
        <div className="flex items-center justify-between gap-2 px-3 pb-3 pt-0.5">
          <div className="flex items-center gap-1">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,application/pdf"
              multiple
              onChange={handleFileInput}
              className="sr-only"
              aria-hidden
              tabIndex={-1}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              aria-label="Attach file"
              title="Attach image or PDF"
              disabled={disabled}
              className="inline-flex size-8 items-center justify-center rounded-full text-muted-foreground transition-all duration-150 hover:bg-muted/80 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 disabled:opacity-50"
            >
              <Paperclip className="size-4" />
            </button>
            <span className="hidden md:inline pl-1 text-[10px] uppercase tracking-[0.18em] text-[var(--brand-cream)]/40">
              ↵ Send · ⇧ ↵ New line
            </span>
          </div>
          <div className="ml-auto flex items-center gap-1">
            {showStop ? (
              <button
                type="button"
                onClick={onStop}
                aria-label="Stop generating"
                className="inline-flex size-9 items-center justify-center rounded-full bg-foreground text-background transition-all duration-150 hover:opacity-80 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/30"
              >
                <Square className="size-3.5 fill-current" />
              </button>
            ) : (
              <button
                type="button"
                onClick={send}
                disabled={!canSend}
                aria-label="Send message"
                className={cn(
                  'inline-flex size-9 items-center justify-center rounded-full transition-all duration-200',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--brand-charcoal)]',
                  canSend
                    ? 'brand-cta active:scale-95'
                    : 'bg-muted text-muted-foreground/50 cursor-not-allowed'
                )}
              >
                <ArrowUp className="size-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
})

function AttachmentChip({
  attachment,
  onRemove,
}: {
  attachment: Attachment
  onRemove: () => void
}) {
  const isImage = attachment.mime.startsWith('image/')
  const isError = attachment.status === 'error'
  const isUploading = attachment.status === 'uploading'

  return (
    <div
      className={cn(
        'group/chip relative flex items-center gap-2 rounded-lg border bg-muted/40 pr-2 transition-colors',
        isError ? 'border-destructive/50' : 'border-border'
      )}
    >
      {isImage && attachment.previewUrl ? (
        <div className="relative size-10 shrink-0 overflow-hidden rounded-l-lg bg-muted">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={attachment.previewUrl}
            alt={attachment.filename ?? 'attachment preview'}
            className={cn(
              'size-full object-cover',
              isUploading && 'opacity-60',
              isError && 'opacity-40'
            )}
          />
          {isUploading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="size-4 animate-spin text-foreground/80" />
            </div>
          )}
        </div>
      ) : (
        <div className="flex size-10 shrink-0 items-center justify-center rounded-l-lg bg-muted text-muted-foreground">
          {isError ? (
            <AlertCircle className="size-4 text-destructive" />
          ) : isUploading ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <FileText className="size-4" />
          )}
        </div>
      )}
      <div className="min-w-0 max-w-[180px] pr-1">
        <div className="truncate text-xs font-medium text-foreground">{attachment.filename}</div>
        <div className="truncate text-[10px] text-muted-foreground">
          {isError ? attachment.errorMsg : formatSize(attachment.size)}
        </div>
      </div>
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Remove ${attachment.filename}`}
        className="inline-flex size-5 shrink-0 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        <X className="size-3" />
      </button>
    </div>
  )
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
