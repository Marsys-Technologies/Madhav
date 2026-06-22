'use client'

import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { DUR, EASE } from '@/lib/components/cockpit/v2/motion'

export interface CascadePreviewModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  rootAssetId: string
  rootAssetLabel?: string
  plan: string[]           // asset IDs in topo order (root first)
  estimatedSeconds?: number | null
  isLoading?: boolean      // true while fetching plan
  isClearCascade?: boolean // true = "Clear & Rebuild" mode
}

function formatSeconds(s: number): string {
  if (s < 60) return `${Math.round(s)}s`
  const m = Math.floor(s / 60)
  const rem = Math.round(s % 60)
  return rem > 0 ? `${m}m ${rem}s` : `${m}m`
}

export function CascadePreviewModal({
  isOpen,
  onClose,
  onConfirm,
  rootAssetId,
  rootAssetLabel,
  plan,
  estimatedSeconds,
  isLoading,
  isClearCascade,
}: CascadePreviewModalProps) {
  // Close on Escape
  useEffect(() => {
    if (!isOpen) return
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [isOpen, onClose])

  const label = rootAssetLabel ?? rootAssetId
  const title = isClearCascade ? `Clear & Rebuild ${label}?` : `Rebuild ${label}?`
  const downstream = plan.slice(1) // everything after root

  const confirmDisabled = isLoading || plan.length === 0

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          key="cascade-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: DUR.modal, ease: EASE.out }}
          role="presentation"
          onClick={onClose}
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
          <motion.div
            key="cascade-modal"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: DUR.modal, ease: EASE.out }}
            role="dialog"
            aria-modal="true"
            data-testid="cascade-preview-modal"
            onClick={e => e.stopPropagation()}
            style={{
              background: 'var(--obsidian-surface, #0f0d12)',
              border: '1px solid var(--obsidian-border, #1f1c17)',
              borderRadius: 8,
              padding: '24px 28px',
              minWidth: 400,
              maxWidth: 560,
              width: '90vw',
              fontFamily: 'var(--ui-stack, Inter, sans-serif)',
              boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
            }}
          >
            {/* Title */}
            <h2
              style={{
                fontSize: 14,
                fontWeight: 600,
                color: 'var(--text-primary, #f5f0e8)',
                marginBottom: 4,
                lineHeight: 1.4,
              }}
            >
              {title}
            </h2>

            {/* Body */}
            {isLoading ? (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  marginTop: 16,
                  marginBottom: 20,
                  color: 'var(--text-secondary, #888373)',
                  fontSize: 12,
                }}
              >
                {/* Spinner */}
                <svg
                  width={14}
                  height={14}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={2.5}
                  strokeLinecap="round"
                  style={{ animation: 'spin 0.9s linear infinite', flexShrink: 0 }}
                >
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
                <style>{`@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}`}</style>
                Resolving plan…
              </div>
            ) : (
              <div
                style={{
                  marginTop: 14,
                  marginBottom: 20,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                {/* Root asset */}
                {plan.length > 0 && (
                  <div
                    style={{
                      fontSize: 12,
                      color: 'var(--text-primary, #f5f0e8)',
                      fontWeight: 600,
                      fontFamily: 'var(--mono-stack, monospace)',
                    }}
                  >
                    {plan[0]}
                  </div>
                )}

                {/* Downstream assets */}
                {downstream.map(id => (
                  <div
                    key={id}
                    style={{
                      fontSize: 12,
                      color: 'var(--text-secondary, #888373)',
                      fontFamily: 'var(--mono-stack, monospace)',
                      paddingLeft: 4,
                    }}
                  >
                    <span style={{ opacity: 0.5 }}>→ </span>
                    {id}
                  </div>
                ))}

                {/* Empty state */}
                {plan.length === 0 && (
                  <div style={{ fontSize: 12, color: 'var(--text-secondary, #888373)' }}>
                    No assets in plan.
                  </div>
                )}

                {/* Estimated time */}
                {estimatedSeconds != null && plan.length > 0 && (
                  <div
                    style={{
                      marginTop: 10,
                      fontSize: 11,
                      color: 'rgba(212,166,72,0.75)',
                      fontFamily: 'var(--mono-stack, monospace)',
                    }}
                  >
                    Estimated time: {formatSeconds(estimatedSeconds)}
                  </div>
                )}
              </div>
            )}

            {/* Buttons */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                onClick={onClose}
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
                disabled={confirmDisabled}
                style={{
                  padding: '6px 20px',
                  fontSize: 13,
                  fontWeight: 500,
                  color: confirmDisabled ? 'rgba(0,0,0,0.4)' : 'var(--obsidian-bg, #08070a)',
                  background: confirmDisabled ? 'rgba(212,166,72,0.35)' : 'var(--gold-primary, #d4a648)',
                  border: 'none',
                  borderRadius: 4,
                  cursor: confirmDisabled ? 'not-allowed' : 'pointer',
                  transition: 'background 0.15s, color 0.15s',
                  fontFamily: 'var(--ui-stack, Inter, sans-serif)',
                }}
              >
                {isClearCascade ? 'Clear & Rebuild' : 'Confirm rebuild'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
