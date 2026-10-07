'use client'

import { useCallback, useEffect, useState } from 'react'
import { Share2, Copy, Check, Trash2, Loader2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'

interface Props {
  conversationId?: string
}

export function ShareButton({ conversationId }: Props) {
  const [slug, setSlug] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [open, setOpen] = useState(false)
  const [confirmRevoke, setConfirmRevoke] = useState(false)
  // X-S8: selective share checkboxes — default true = "show" (hide_* = false)
  const [showReasoning, setShowReasoning] = useState(true)
  const [showMethodology, setShowMethodology] = useState(true)

  // Fetch existing share state when the dropdown is opened the first time.
  const refresh = useCallback(async () => {
    if (!conversationId) return
    try {
      const res = await fetch(`/api/conversations/${conversationId}/share`, { cache: 'no-store' })
      if (!res.ok) return
      const data = (await res.json()) as { share: { slug: string } | null }
      setSlug(data.share?.slug ?? null)
    } catch {}
  }, [conversationId])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (open) void refresh()
  }, [open, refresh])

  const shareUrl = slug ? `${window.location.origin}/share/${slug}` : null

  async function createShare() {
    if (!conversationId) return
    setLoading(true)
    try {
      const res = await fetch(`/api/conversations/${conversationId}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hide_reasoning: !showReasoning,
          hide_methodology: !showMethodology,
        }),
      })
      if (!res.ok) return
      const data = (await res.json()) as { slug: string }
      setSlug(data.slug)
    } finally {
      setLoading(false)
    }
  }

  async function copy() {
    if (!shareUrl) return
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {}
  }

  async function revoke() {
    if (!conversationId) return
    setConfirmRevoke(false)
    setLoading(true)
    try {
      await fetch(`/api/conversations/${conversationId}/share`, { method: 'DELETE' })
      setSlug(null)
    } finally {
      setLoading(false)
    }
  }

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
      <DropdownMenuContent align="end" className="w-80 p-3">
        <div className="space-y-2">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Share conversation</h3>
            <p className="text-[11px] text-muted-foreground">
              Anyone with the link will see a read-only copy of this chat.
            </p>
          </div>
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
                      onClick={revoke}
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
              {/* X-S8: selective share checkboxes */}
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
              <button
                type="button"
                onClick={createShare}
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
    </DropdownMenu>
  )
}
