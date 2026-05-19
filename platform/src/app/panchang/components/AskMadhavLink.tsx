'use client'

/**
 * AskMadhavLink — inline 💬 affordance for the /panchang page.
 *
 * Renders a small ghost-style icon button with a 💬 (MessageCircle) icon.
 * On click:
 *   1. Encodes prompt + optional panchang_context as URL params.
 *   2. Opens /clients/[chart_id]/consume?prompt=<encoded>&context=<encoded_json>
 *      in the same tab (router.push) — matching the project's existing pattern.
 *
 * Context-budget guard (AC.4C8.6):
 *   If the serialised panchang_context exceeds MAX_CONTEXT_BYTES (10 KB),
 *   it is trimmed to essentials and a "(truncated)" note is appended.
 *
 * Phase: 4C-8 (Item 1)
 */

import { useRouter } from 'next/navigation'
import { MessageCircle } from 'lucide-react'

// ── Constants ─────────────────────────────────────────────────────────────────

/** Default chart ID — the native's primary chart. Can be overridden per call-site. */
export const DEFAULT_CHART_ID = 'abhisek_mohanty_primary'

/** Maximum raw-JSON bytes for context injection. Above this we trim. */
const MAX_CONTEXT_BYTES = 10_240 // 10 KB

// ── Context budget guard ──────────────────────────────────────────────────────

/**
 * Serialise a Panchang context object for URL encoding.
 *
 * If the serialised JSON exceeds MAX_CONTEXT_BYTES the payload is reduced to
 * essential fields only and a note is appended so the synthesis layer knows
 * the context is partial.
 *
 * @param ctx  Any object (full PanchangDay or subset).
 * @returns    JSON string, guaranteed ≤ MAX_CONTEXT_BYTES when encoded.
 */
export function serialiseContext(ctx: object): string {
  const full = JSON.stringify(ctx)
  if (new TextEncoder().encode(full).length <= MAX_CONTEXT_BYTES) {
    return full
  }

  // Trim to essentials: angas, timings (sunrise/sunset), special_yogas summary
  // (This handles the 30-day range injection test from AC.4C8.6)
  const trimmed = {
    _truncated: true,
    _note: 'Context exceeded 10 KB. Call query_panchanga for full detail.',
    date: (ctx as Record<string, unknown>)['date'],
    lat: (ctx as Record<string, unknown>)['lat'],
    lon: (ctx as Record<string, unknown>)['lon'],
    angas: (ctx as Record<string, unknown>)['angas'],
    timings: (() => {
      const t = (ctx as Record<string, unknown>)['timings'] as Record<string, unknown> | null
      if (!t) return null
      return { sunrise_utc: t['sunrise_utc'], sunset_utc: t['sunset_utc'] }
    })(),
  }

  return JSON.stringify(trimmed)
}

// ── Component ─────────────────────────────────────────────────────────────────

interface AskMadhavLinkProps {
  /** The visible user question that will be pre-loaded in the chat input. */
  prompt: string
  /**
   * Optional Panchang JSON context to inject as a hidden block.
   * Will be size-guarded before encoding.
   */
  panchang_context?: object
  /**
   * Override the chart ID used in the deep-link URL.
   * Defaults to DEFAULT_CHART_ID.
   */
  chart_id?: string
  /**
   * Additional CSS class names for the wrapping button.
   * Useful for positioning (e.g. ml-2 inline, or absolute positioned).
   */
  className?: string
  /** Accessible label. Defaults to "Ask Madhav: <prompt>" */
  ariaLabel?: string
}

export function AskMadhavLink({
  prompt,
  panchang_context,
  chart_id = DEFAULT_CHART_ID,
  className = '',
  ariaLabel,
}: AskMadhavLinkProps) {
  const router = useRouter()

  function handleClick() {
    const params = new URLSearchParams()
    params.set('prompt', prompt)

    if (panchang_context) {
      params.set('context', serialiseContext(panchang_context))
    }

    router.push(`/clients/${chart_id}/consume?${params.toString()}`)
  }

  const tooltipText = `Ask Madhav: "${prompt.length > 60 ? prompt.slice(0, 57) + '…' : prompt}"`
  const label = ariaLabel ?? tooltipText

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={label}
      title={tooltipText}
      className={[
        // Ghost style — low visual weight, doesn't compete with primary content
        'inline-flex items-center justify-center',
        'h-6 w-6 rounded-full',
        'border border-transparent',
        'text-[rgba(212,175,55,0.45)]',
        'transition-all duration-150',
        'hover:border-[rgba(212,175,55,0.25)] hover:bg-[rgba(212,175,55,0.08)]',
        'hover:text-[rgba(212,175,55,0.80)]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-gold)]',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <MessageCircle className="h-3.5 w-3.5" aria-hidden="true" />
    </button>
  )
}
