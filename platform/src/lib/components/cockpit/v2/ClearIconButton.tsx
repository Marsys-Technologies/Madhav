'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { ClearConfirmModal, type ClearPreview } from './ClearConfirmModal'
import { CascadePreviewModal } from '@/components/cockpit/CascadePreviewModal'

interface Props {
  chartId: string
  scope: 'global' | 'layer' | 'asset'
  scopeTarget?: string | null
  size?: number
  onSuccess?: () => void
}

export function ClearIconButton({ chartId, scope, scopeTarget, size = 28, onSuccess }: Props) {
  // Modal is opened immediately on click; preview fetched async inside.
  const [modalOpen, setModalOpen] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [preview, setPreview] = useState<ClearPreview | null>(null)

  // Post-clear cascade offer
  const [cascadeAssets, setCascadeAssets] = useState<string[] | null>(null)
  const [cascadeLoading, setCascadeLoading] = useState(false)
  const [cascadePlan, setCascadePlan] = useState<string[]>([])
  const [showCascade, setShowCascade] = useState(false)

  async function handleClick(e: React.MouseEvent) {
    e.stopPropagation()
    if (modalOpen || previewLoading) return

    // Open modal immediately — user sees it right away with loading skeleton
    setModalOpen(true)
    setPreview(null)
    setPreviewLoading(true)
    try {
      const r = await fetch('/api/cockpit/clear', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId, scope, scope_target: scopeTarget ?? null }),
      })
      const txt = await r.text()
      let body: Record<string, unknown>
      try { body = JSON.parse(txt) }
      catch { throw new Error(`Server error (${r.status}): ${txt.substring(0, 200) || 'no body'}`) }
      if (!r.ok) throw new Error((body.error as string | undefined) ?? 'Preview failed')
      setPreview(body.preview as ClearPreview)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load clear preview')
      setModalOpen(false)
    } finally {
      setPreviewLoading(false)
    }
  }

  function handleModalClose() {
    setModalOpen(false)
    setPreview(null)
  }

  // Called by ClearConfirmModal after a successful clear
  async function handleSuccess() {
    const downstream = preview?.downstream_stale_assets ?? []
    setModalOpen(false)
    setPreview(null)
    onSuccess?.()

    if (downstream.length === 0) return

    // Offer cascade rebuild
    setCascadeAssets(downstream)
    setCascadeLoading(true)
    setShowCascade(true)
    setCascadePlan([])
    try {
      const r = await fetch('/api/cockpit/plan', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId, scope, scope_target: scopeTarget ?? null, action: 'cascade' }),
      })
      const body = await r.json().catch(() => null)
      if (r.ok && Array.isArray(body?.data?.plan) && body.data.plan.length > 0) {
        setCascadePlan(body.data.plan as string[])
      } else {
        setCascadePlan(downstream)
      }
    } catch {
      setCascadePlan(downstream)
    } finally {
      setCascadeLoading(false)
    }
  }

  async function handleCascadeConfirm() {
    setShowCascade(false)
    try {
      const r = await fetch('/api/cockpit/runs', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: chartId, scope, scope_target: scopeTarget ?? null, action: 'cascade' }),
      })
      const body = await r.json().catch(() => null)
      if (!r.ok) {
        toast.error(body?.error ?? 'Failed to start cascade rebuild')
        return
      }
      toast.success('Cascade rebuild started')
      onSuccess?.()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to start cascade rebuild')
    } finally {
      setCascadeAssets(null)
      setCascadePlan([])
    }
  }

  return (
    <>
      <button
        onClick={handleClick}
        title={`Clear ${scope === 'asset' ? (scopeTarget ?? 'asset') : scope}`}
        disabled={modalOpen}
        data-icon-btn
        style={{
          width: size,
          height: size,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'transparent',
          border: 'none',
          borderRadius: '4px',
          cursor: modalOpen ? 'default' : 'pointer',
          color: 'var(--on-dark-faint)',
          padding: 0,
          transition: 'color 0.15s, background 0.15s',
        }}
        onMouseEnter={e => {
          if (!modalOpen) {
            e.currentTarget.style.color = 'var(--marsys-error)'
            e.currentTarget.style.background = 'rgba(181,71,76,0.10)'
          }
        }}
        onMouseLeave={e => {
          e.currentTarget.style.color = 'var(--on-dark-faint)'
          e.currentTarget.style.background = 'transparent'
        }}
      >
        {/* Trash2 icon */}
        <svg
          width={Math.round(size * 0.54)}
          height={Math.round(size * 0.54)}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
          <path d="M10 11v6" />
          <path d="M14 11v6" />
          <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
        </svg>
      </button>

      {/* Confirm modal — opens immediately with isLoading skeleton until preview arrives */}
      {modalOpen && (
        <ClearConfirmModal
          chartId={chartId}
          scope={scope}
          scopeTarget={scopeTarget}
          preview={preview}
          isLoading={previewLoading}
          onClose={handleModalClose}
          onSuccess={handleSuccess}
        />
      )}

      {/* Post-clear cascade rebuild offer */}
      <CascadePreviewModal
        isOpen={showCascade}
        isLoading={cascadeLoading}
        onClose={() => {
          setShowCascade(false)
          setCascadeAssets(null)
          setCascadePlan([])
        }}
        onConfirm={handleCascadeConfirm}
        rootAssetId={scopeTarget ?? scope}
        rootAssetLabel={
          cascadeAssets
            ? `${cascadeAssets.length} stale downstream asset${cascadeAssets.length !== 1 ? 's' : ''}`
            : undefined
        }
        plan={cascadePlan}
        isClearCascade
      />
    </>
  )
}
