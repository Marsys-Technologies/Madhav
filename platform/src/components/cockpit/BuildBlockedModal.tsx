'use client'

import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { BlockerEntry } from '@/lib/build/plan'

interface BuildBlockedModalProps {
  blockers: BlockerEntry[]
  onDismiss: () => void
}

const STATE_BADGE_STYLE: Record<string, { label: string; background: string; color: string; border: string }> = {
  stale:        { label: 'stale',        background: 'rgba(212,166,72,0.15)',  color: 'rgba(212,166,72,0.9)',   border: '1px solid rgba(212,166,72,0.35)' },
  dormant:      { label: 'dormant',      background: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary, #888373)', border: '1px solid rgba(255,255,255,0.12)' },
  error:        { label: 'error',        background: 'rgba(220,60,60,0.15)',   color: 'rgba(220,100,100,0.9)',  border: '1px solid rgba(220,60,60,0.35)' },
  service_down: { label: 'service down', background: 'rgba(220,60,60,0.15)',   color: 'rgba(220,100,100,0.9)',  border: '1px solid rgba(220,60,60,0.35)' },
  building:     { label: 'building',     background: 'rgba(72,130,212,0.15)',  color: 'rgba(100,160,220,0.9)',  border: '1px solid rgba(72,130,212,0.35)' },
}

export function BuildBlockedModal({ blockers, onDismiss }: BuildBlockedModalProps) {
  // Portal mount guard (SSR-safe): mounting to <body> lifts the modal out of the
  // cockpit's nested stacking contexts so the constellation SVG can't overpaint it.
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  // Close on Escape
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onDismiss()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onDismiss])

  if (!mounted) return null

  return createPortal(
    <div
      role="presentation"
      onClick={onDismiss}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(8,7,10,0.82)',
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        data-testid="build-blocked-modal"
        onClick={e => e.stopPropagation()}
        style={{
          background: 'var(--obsidian-surface, #0f0d12)',
          border: '1px solid var(--obsidian-border, #1f1c17)',
          borderRadius: 8,
          padding: '24px 28px',
          minWidth: 400,
          maxWidth: 560,
          width: '90vw',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          fontFamily: 'var(--ui-stack, Inter, sans-serif)',
          boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
        }}
      >
        {/* Header */}
        <h2
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: 'var(--text-primary, #f5f0e8)',
            marginBottom: 4,
            lineHeight: 1.4,
          }}
        >
          Cannot build — dependencies not ready
        </h2>
        <p
          style={{
            fontSize: 12,
            color: 'rgba(212,166,72,0.75)',
            marginBottom: 0,
            lineHeight: 1.5,
          }}
        >
          Resolve the following before building.
        </p>

        {/* Blocker list */}
        <div
          style={{
            marginTop: 16,
            marginBottom: 20,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            overflowY: 'auto',
            minHeight: 0,
            flex: '1 1 auto',
            maxHeight: '60vh',
          }}
        >
          {blockers.map((b) => {
            const badge = STATE_BADGE_STYLE[b.dep_state] ?? {
              label: b.dep_state,
              background: 'rgba(255,255,255,0.06)',
              color: 'var(--text-secondary, #888373)',
              border: '1px solid rgba(255,255,255,0.12)',
            }
            return (
              <div
                key={b.dep_asset_id}
                style={{
                  border: '1px solid var(--obsidian-border, #1f1c17)',
                  borderRadius: 6,
                  padding: '10px 12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                }}
              >
                {/* Asset ID + state badge */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span
                    style={{
                      fontFamily: 'var(--mono-stack, monospace)',
                      fontSize: 12,
                      fontWeight: 600,
                      color: 'var(--text-primary, #f5f0e8)',
                    }}
                  >
                    {b.dep_asset_id}
                  </span>
                  <span
                    style={{
                      fontSize: 10,
                      padding: '1px 6px',
                      borderRadius: 3,
                      fontWeight: 500,
                      background: badge.background,
                      color: badge.color,
                      border: badge.border,
                    }}
                  >
                    {badge.label}
                  </span>
                </div>

                {/* Guidance (visually distinct hint) */}
                {b.guidance && (
                  <div
                    style={{
                      fontSize: 11,
                      color: 'rgba(212,166,72,0.85)',
                      borderLeft: '2px solid rgba(212,166,72,0.4)',
                      paddingLeft: 8,
                      fontStyle: 'italic',
                    }}
                  >
                    {b.guidance}
                  </div>
                )}

                {/* Required-by list */}
                <div
                  style={{
                    fontSize: 11,
                    color: 'var(--text-secondary, #888373)',
                  }}
                >
                  <span style={{ opacity: 0.6 }}>Required by: </span>
                  {b.required_by.join(', ')}
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={onDismiss}
            style={{
              padding: '6px 16px',
              fontSize: 13,
              color: 'var(--text-secondary, #888373)',
              background: 'transparent',
              border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: 4,
              cursor: 'pointer',
              fontFamily: 'var(--ui-stack, Inter, sans-serif)',
            }}
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
