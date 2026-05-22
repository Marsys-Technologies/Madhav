'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import type { UIMessage } from 'ai'
import { motion, useReducedMotion } from 'framer-motion'
import TextareaAutosize from 'react-textarea-autosize'
import { FileText } from 'lucide-react'
import { MessageActions } from './MessageActions'
import { BranchPicker } from './BranchPicker'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface FilePart {
  type: 'file'
  filename?: string
  mediaType: string
  url: string
}

function getText(message: UIMessage): string {
  return message.parts
    .filter(p => p.type === 'text')
    .map(p => (p as { type: 'text'; text: string }).text)
    .join('')
}

function getFileParts(message: UIMessage): FilePart[] {
  return message.parts.filter(p => p.type === 'file') as unknown as FilePart[]
}

interface Props {
  message: UIMessage
  onEditSubmit?: (id: string, text: string) => void
  branchTotal?: number
  branchCurrent?: number
  onStepBranch?: (delta: -1 | 1) => void
}

export function UserMessage({
  message,
  onEditSubmit,
  branchTotal,
  branchCurrent,
  onStepBranch,
}: Props) {
  const text = getText(message)
  const files = getFileParts(message)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(text)
  const timestamp = useMemo(() => {
    const meta = (message.metadata ?? {}) as Record<string, unknown>
    const raw = meta.created_at ?? (message as unknown as { created_at?: unknown }).created_at
    return typeof raw === 'string' || typeof raw === 'number' ? new Date(raw) : null
  }, [message])
  const reduce = useReducedMotion()
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (editing) textareaRef.current?.focus()
  }, [editing])

  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
    } catch {}
  }

  if (editing) {
    return (
      <div className="mx-auto w-full max-w-4xl px-4">
        <div className="ml-auto w-full max-w-[85%]">
          <div className="rounded-2xl border border-border bg-background p-3 shadow-sm">
            <TextareaAutosize
              ref={textareaRef}
              value={draft}
              onChange={e => setDraft(e.target.value)}
              minRows={1}
              maxRows={12}
              className="w-full resize-none bg-transparent text-[15px] leading-relaxed text-foreground outline-none"
            />
            <div className="mt-2 flex items-center justify-end gap-1.5">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setDraft(text)
                  setEditing(false)
                }}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  const trimmed = draft.trim()
                  if (!trimmed || !onEditSubmit) return
                  onEditSubmit(message.id, trimmed)
                  setEditing(false)
                }}
                disabled={!draft.trim() || draft.trim() === text}
              >
                Send
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className="group/message mx-auto w-full max-w-4xl px-4"
    >
      <div className="flex items-start gap-4">
      <div className="min-w-0 flex-1">
      <div className="ml-auto flex w-full max-w-[85%] flex-col items-end gap-1.5">
        {files.length > 0 && (
          <div className="flex flex-wrap justify-end gap-1.5">
            {files.map((f, i) => (
              <AttachmentView key={i} file={f} />
            ))}
          </div>
        )}
        {text && (
          <div
            className={cn(
              // Base bubble — Marsys glassmorphic dark with gold speech-tail (v2-user-bubble).
              // v2-user-bubble--r11b-shape: shape variant activated by .consume-shell.r11b-active
              // (border-radius 1rem, max-width 80%, padding 12/14, right-aligned).
              // Speech-tail ::after + gold hairline border preserved in both states.
              'v2-user-bubble v2-user-bubble--r11b-shape',
              'rounded-2xl border border-border/80 bg-muted/50 px-4 py-2.5 text-[15px] leading-[1.6]',
              'text-foreground'
            )}
          >
            <p className="whitespace-pre-wrap break-words">{text}</p>
          </div>
        )}
        <div className="flex items-center gap-2 opacity-0 transition-opacity duration-150 group-hover/message:opacity-100 focus-within:opacity-100 has-[:focus]:opacity-100 data-[branch]:opacity-100" data-branch={branchTotal && branchTotal > 1 ? '' : undefined}>
          {branchTotal && branchTotal > 1 && typeof branchCurrent === 'number' && onStepBranch && (
            <BranchPicker
              currentBranch={branchCurrent + 1}
              totalBranches={branchTotal}
              onPrev={() => onStepBranch(-1)}
              onNext={() => onStepBranch(1)}
            />
          )}
          <MessageActions
            onCopy={text ? copy : undefined}
            onEdit={onEditSubmit && text ? () => setEditing(true) : undefined}
            timestamp={timestamp ?? undefined}
          />
        </div>
      </div>
      </div>
      <div className="w-8 shrink-0" aria-hidden />
      </div>
    </motion.div>
  )
}

function AttachmentView({ file }: { file: FilePart }) {
  const isImage = file.mediaType?.startsWith('image/')
  if (isImage) {
    return (
      <a
        href={file.url}
        target="_blank"
        rel="noreferrer"
        className="block overflow-hidden rounded-xl border border-border"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={file.url}
          alt={file.filename ?? 'attachment'}
          className="max-h-64 max-w-xs object-cover"
        />
      </a>
    )
  }
  return (
    <a
      href={file.url}
      target="_blank"
      rel="noreferrer"
      className="inline-flex max-w-xs items-center gap-2 rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs transition-colors hover:bg-muted"
    >
      <FileText className="size-4 shrink-0 text-muted-foreground" />
      <span className="truncate font-medium text-foreground">{file.filename ?? 'file'}</span>
    </a>
  )
}
