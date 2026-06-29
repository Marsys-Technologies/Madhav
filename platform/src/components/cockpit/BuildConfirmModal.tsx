'use client'

import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'

interface BuildConfirmModalProps {
  assetIds: string[]          // plan_waves.flat() — the assets that will be built
  estimatedSeconds: number | null
  onConfirm: () => void
  onCancel: () => void
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s > 0 ? `${m}m ${s}s` : `${m}m`
}

export function BuildConfirmModal({ assetIds, estimatedSeconds, onConfirm, onCancel }: BuildConfirmModalProps) {
  // Portal mount guard (SSR-safe): mounting to <body> lifts the modal out of the
  // cockpit's nested stacking contexts so the constellation SVG can't overpaint it.
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  // Close on Escape
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onCancel])

  if (!mounted) return null

  return createPortal(
    <div
      role="presentation"
      onClick={onCancel}
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
        data-testid="build-confirm-modal"
        onClick={e => e.stopPropagation()}
        style={{
          background: 'var(--obsidian-surface, #0f0d12)',
          border: '1px solid var(--obsidian-border, #1f1c17)',
          borderRadius: 8,
          minWidth: 400,
          maxWidth: 560,
          width: '90vw',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          fontFamily: 'var(--ui-stack, Inter, sans-serif)',
          boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            borderBottom: '1px solid var(--obsidian-border, #1f1c17)',
            padding: '16px 24px',
          }}
        >
          <h2
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: 'var(--text-primary, #f5f0e8)',
              margin: 0,
              lineHeight: 1.4,
            }}
          >
            Confirm build
          </h2>
          <p
            style={{
              fontSize: 12,
              color: 'var(--text-secondary, #888373)',
              margin: '4px 0 0',
            }}
          >
            {assetIds.length === 1
              ? `1 asset will be built.`
              : `${assetIds.length} assets will be built.`}
            {estimatedSeconds != null && ` Estimated time: ${formatDuration(estimatedSeconds)}.`}
          </p>
        </div>

        {/* Asset list */}
        <div
          style={{
            padding: '16px 24px',
            overflowY: 'auto',
            flex: '1 1 auto',
            minHeight: 0,
            maxHeight: 256,
          }}
        >
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
            {assetIds.map((id) => (
              <li
                key={id}
                style={{
                  fontSize: 12,
                  color: 'var(--text-primary, #f5f0e8)',
                  fontFamily: 'var(--mono-stack, monospace)',
                }}
              >
                {id}
              </li>
            ))}
          </ul>
        </div>

        {/* Footer */}
        <div
          style={{
            borderTop: '1px solid var(--obsidian-border, #1f1c17)',
            padding: '14px 24px',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 10,
          }}
        >
          <button
            onClick={onCancel}
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
            Cancel
          </button>
          <button
            onClick={onConfirm}
            style={{
              padding: '6px 20px',
              fontSize: 13,
              fontWeight: 500,
              color: 'var(--obsidian-bg, #08070a)',
              background: 'var(--gold-primary, #d4a648)',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              fontFamily: 'var(--ui-stack, Inter, sans-serif)',
            }}
          >
            Build
          </button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
