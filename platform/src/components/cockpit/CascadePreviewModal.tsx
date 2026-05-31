'use client'

/**
 * CascadePreviewModal — shows downstream nodes that will be invalidated
 * and recomputed when a single asset is rebuilt.
 *
 * [C-S7] scaffold — full cascade graph UI ships in a follow-on session.
 */

interface Props {
  open: boolean
  onClose: () => void
  assetId: string
  buildId: string
  chartId: string
  onConfirm: () => void
}

export function CascadePreviewModal({ open, onClose, assetId, onConfirm }: Props) {
  if (!open) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="cascade-preview-modal"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(8,7,10,0.8)',
      }}
    >
      <div
        style={{
          background: 'var(--obsidian-surface, #0f0d12)',
          border: '1px solid var(--obsidian-border, #1f1c17)',
          borderRadius: 8,
          padding: '24px 28px',
          minWidth: 400,
          maxWidth: 560,
          fontFamily: 'var(--font-sans, Inter, sans-serif)',
        }}
      >
        <h2
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: 'var(--text-primary, #f5f0e8)',
            marginBottom: 8,
          }}
        >
          Rebuild {assetId}?
        </h2>
        <p
          style={{
            fontSize: 12,
            color: 'var(--text-secondary, #888373)',
            marginBottom: 20,
          }}
        >
          Downstream assets that depend on this node will be queued for recomputation.
        </p>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          <button
            onClick={onClose}
            style={{
              padding: '6px 16px',
              fontSize: 13,
              color: 'var(--text-secondary, #888373)',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
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
            }}
          >
            Confirm rebuild
          </button>
        </div>
      </div>
    </div>
  )
}
