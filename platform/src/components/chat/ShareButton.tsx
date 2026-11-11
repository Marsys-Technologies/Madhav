'use client'

import { useEffect, useRef, useState } from 'react'
import { Share2, Copy, Check, Trash2, Loader2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { SHARE_DEFAULT_TTL_DAYS } from '@/lib/share/constants'

interface Props {
  conversationId?: string
}

export function ShareButton({ conversationId }: Props) {
  const [open, setOpen] = useState(false)
  if (!conversationId) return null

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger
        aria-label="Share conversation"
        className="inline-flex h-8 items-center gap-1.5 rounded-md px-2 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
      >
        <Share2 className="size-3.5" />
        <span className="hidden sm:inline">Share</span>
      </DropdownMenuTrigger>
      <ConversationShareMenu key={conversationId} conversationId={conversationId} open={open} />
    </DropdownMenu>
  )
}

function ConversationShareMenu({ conversationId, open }: { conversationId: string; open: boolean }) {
  const [slug, setSlug] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null)
  const [confirmRevoke, setConfirmRevoke] = useState(false)
  const [revokeError, setRevokeError] = useState(false)
  // X-S8: selective share checkboxes — default true = "show" (hide_* = false)
  const [showReasoning, setShowReasoning] = useState(true)
  const [showMethodology, setShowMethodology] = useState(true)
  // SS N-379: R10_SELECTIVE_SHARE only controls whether the options are OFFERED on
  // a NEW share. The GET below reports it; absent (older server) = offered.
  const [selectiveShareEnabled, setSelectiveShareEnabled] = useState(true)
  const readRequest = useRef<AbortController | null>(null)
  const writeRequest = useRef<AbortController | null>(null)
  const copyAttempt = useRef(0)
  const copyTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const endpoint = `/api/conversations/${conversationId}/share`

  useEffect(() => {
    if (!open || writeRequest.current) return
    const controller = new AbortController()
    readRequest.current = controller
    const { signal } = controller

    async function refresh() {
      try {
        const res = await fetch(endpoint, { cache: 'no-store', signal })
        if (!res.ok || signal.aborted) return
        const data = (await res.json()) as {
          share: { slug: string } | null
          selective_share_enabled?: boolean
        }
        if (signal.aborted) return
        setSlug(data.share?.slug ?? null)
        setSelectiveShareEnabled(data.selective_share_enabled !== false)
      } catch {}
    }

    void refresh()
    return () => {
      controller.abort()
      readRequest.current = null
    }
  }, [endpoint, open])

  useEffect(() => () => {
    writeRequest.current?.abort()
    writeRequest.current = null
    copyAttempt.current += 1
    if (copyTimer.current !== null) clearTimeout(copyTimer.current)
  }, [])

  const shareUrl = slug ? `${window.location.origin}/share/${slug}` : null
  const copied = shareUrl !== null && copiedUrl === shareUrl

  async function mutateShare(method: 'POST' | 'DELETE') {
    if (writeRequest.current) return
    const controller = new AbortController()
    writeRequest.current = controller
    readRequest.current?.abort()
    const { signal } = controller
    const revoking = method === 'DELETE'
    if (revoking) setRevokeError(false)
    setLoading(true)
    try {
      const response = await fetch(endpoint, revoking ? { method, signal } : {
        method,
        signal,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
          selectiveShareEnabled
            ? { hide_reasoning: !showReasoning, hide_methodology: !showMethodology }
            : {},
        ),
      })
      if (signal.aborted) return
      if (revoking) {
        if (response.ok) setSlug(null)
        else setRevokeError(true)
      } else if (response.ok) {
        const data = (await response.json()) as { slug: string }
        if (!signal.aborted) setSlug(data.slug)
      }
    } catch {
      if (!signal.aborted && revoking) setRevokeError(true)
    } finally {
      if (!signal.aborted) {
        writeRequest.current = null
        if (revoking) setConfirmRevoke(false)
        setLoading(false)
      }
    }
  }

  async function copy() {
    if (!shareUrl) return
    const attempt = ++copyAttempt.current
    try {
      await navigator.clipboard.writeText(shareUrl)
      if (copyAttempt.current !== attempt) return
      setCopiedUrl(shareUrl)
      if (copyTimer.current !== null) clearTimeout(copyTimer.current)
      copyTimer.current = setTimeout(() => setCopiedUrl(null), 1800)
    } catch {}
  }

  return (
    <DropdownMenuContent align="end" className="w-80 p-3">
      <div className="space-y-2">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Share conversation</h3>
          <p className="text-[11px] text-muted-foreground">
            Signed-in MARSYS-JIS users with the link will see a read-only copy of this chat.
            The link expires after {SHARE_DEFAULT_TTL_DAYS} days.
          </p>
        </div>
        {revokeError && slug && (
          <p role="alert" className="text-xs text-destructive">
            Could not revoke the link. Check its status or try again.
          </p>
        )}
        {slug && shareUrl ? (
          <>
            <div className="flex items-center gap-1 rounded-md border border-border bg-muted/30 px-2 py-1.5">
              <span className="flex-1 truncate font-mono text-[11px] text-foreground">
                {shareUrl}
              </span>
              <button
                type="button"
                onClick={copy}
                aria-label={copied ? 'Copied' : 'Copy link'}
                className={cn(
                  'inline-flex size-6 shrink-0 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-background hover:text-foreground',
                  copied && 'text-foreground'
                )}
              >
                {copied ? <Check className="size-3" /> : <Copy className="size-3" />}
              </button>
            </div>
            {confirmRevoke ? (
              <div className="space-y-1.5 rounded-md border border-destructive/40 bg-destructive/5 p-2">
                <p className="text-[11px] text-destructive">
                  Revoking removes access for anyone with this link. Continue?
                </p>
                <div className="flex gap-1.5">
                  <button
                    type="button"
                    onClick={() => setConfirmRevoke(false)}
                    className="flex-1 rounded-md border border-border px-2 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-muted"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => void mutateShare('DELETE')}
                    disabled={loading}
                    className="flex-1 inline-flex items-center justify-center gap-1 rounded-md border border-destructive/60 bg-destructive/10 px-2 py-1 text-[11px] text-destructive transition-colors hover:bg-destructive/20 disabled:opacity-50"
                  >
                    {loading ? <Loader2 className="size-3 animate-spin" /> : <Trash2 className="size-3" />}
                    Revoke
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setConfirmRevoke(true)}
                className="inline-flex w-full items-center justify-center gap-1.5 rounded-md border border-destructive/40 px-2 py-1.5 text-[11px] text-destructive transition-colors hover:bg-destructive/10"
              >
                <Trash2 className="size-3" />
                Revoke link
              </button>
            )}
          </>
        ) : (
          <div className="space-y-2">
            {/* X-S8: selective share checkboxes (offered only while R10_SELECTIVE_SHARE is on) */}
            {selectiveShareEnabled && (
            <div className="space-y-1 rounded-md border border-border bg-muted/20 px-3 py-2">
              <label className="flex cursor-pointer items-center gap-2 text-[11px] text-muted-foreground">
                <input
                  type="checkbox"
                  checked={showReasoning}
                  onChange={(e) => setShowReasoning(e.target.checked)}
                  data-testid="v2-share-show-reasoning"
                  className="rounded border-border"
                />
                Show reasoning
              </label>
              <label className="flex cursor-pointer items-center gap-2 text-[11px] text-muted-foreground">
                <input
                  type="checkbox"
                  checked={showMethodology}
                  onChange={(e) => setShowMethodology(e.target.checked)}
                  data-testid="v2-share-show-methodology"
                  className="rounded border-border"
                />
                Show methodology
              </label>
            </div>
            )}
            <button
              type="button"
              onClick={() => void mutateShare('POST')}
              disabled={loading}
              className="inline-flex w-full items-center justify-center gap-1.5 rounded-md bg-foreground px-2 py-1.5 text-[12px] font-medium text-background transition-opacity hover:opacity-90 disabled:opacity-50"
              data-testid="v2-share-create-btn"
            >
              {loading ? <Loader2 className="size-3.5 animate-spin" /> : <Share2 className="size-3.5" />}
              Create share link
            </button>
          </div>
        )}
      </div>
    </DropdownMenuContent>
  )
}
