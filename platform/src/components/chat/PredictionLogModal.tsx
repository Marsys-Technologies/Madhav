'use client'

/**
 * PredictionLogModal — γ3
 *
 * End-of-message modal for logging a detected prediction candidate.
 * Pre-fills fields from the detected candidate; user reviews + submits.
 * Learning Layer rule #4: outcome is never captured here.
 */

import { useEffect, useRef, useState } from 'react'
import { writePrediction } from '@/lib/ppl/prediction_writer'

interface PredictionLogModalProps {
  open: boolean
  onClose: () => void
  queryId: string
  conversationId: string | null
  /** Pre-filled from prediction_candidate data part. */
  predictionText: string
  horizon: string | null
}

export function PredictionLogModal({
  open,
  onClose,
  queryId,
  conversationId,
  predictionText,
  horizon,
}: PredictionLogModalProps) {
  const [text, setText] = useState(predictionText)
  const [conf, setConf] = useState<string>('')
  const [hor, setHor] = useState(horizon ?? '')
  const [falsifier, setFalsifier] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Reset state when modal opens for a new prediction
  useEffect(() => {
    if (open) {
      setText(predictionText)
      setHor(horizon ?? '')
      setConf('')
      setFalsifier('')
      setSaved(false)
      setError(null)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open, predictionText, horizon])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!text.trim()) return
    setSaving(true)
    setError(null)
    try {
      const confidenceNum = conf ? parseFloat(conf) : null
      if (confidenceNum !== null && (confidenceNum < 0 || confidenceNum > 1)) {
        setError('Confidence must be 0–1')
        setSaving(false)
        return
      }
      await writePrediction({
        query_id: queryId,
        conversation_id: conversationId,
        prediction_text: text.trim(),
        confidence: confidenceNum,
        horizon: hor.trim() || null,
        falsifier: falsifier.trim() || null,
      })
      setSaved(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save prediction')
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60"
        onClick={onClose}
        aria-hidden="true"
        data-testid="prediction-modal-backdrop"
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-label="Log prediction"
        aria-modal="true"
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        data-testid="prediction-modal"
      >
        <div className="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-950 shadow-2xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-zinc-800">
            <h2 className="text-sm font-semibold text-zinc-100">Log as prediction</h2>
            <button
              type="button"
              onClick={onClose}
              className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
              aria-label="Close"
              data-testid="prediction-modal-close"
            >
              ×
            </button>
          </div>

          {saved ? (
            <div className="px-5 py-6 text-center">
              <p className="text-sm text-emerald-400 font-medium">Prediction logged.</p>
              <p className="mt-1 text-xs text-zinc-600">Outcome will be recorded at observation time.</p>
              <button
                type="button"
                onClick={onClose}
                className="mt-4 px-4 py-1.5 rounded-lg bg-zinc-800 text-xs text-zinc-300 hover:bg-zinc-700 transition-colors"
                data-testid="prediction-modal-done"
              >
                Done
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="px-5 py-4 flex flex-col gap-3">
              {/* Prediction text */}
              <div>
                <label htmlFor="pred-text" className="block text-[10px] font-semibold uppercase tracking-widest text-zinc-500 mb-1">
                  Prediction
                </label>
                <textarea
                  id="pred-text"
                  ref={inputRef}
                  value={text}
                  onChange={e => setText(e.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/60 resize-none"
                  rows={3}
                  required
                  data-testid="prediction-text-input"
                />
              </div>

              {/* Horizon */}
              <div>
                <label htmlFor="pred-horizon" className="block text-[10px] font-semibold uppercase tracking-widest text-zinc-500 mb-1">
                  Horizon <span className="text-zinc-600 normal-case font-normal">(e.g. "6 months", "by 2027")</span>
                </label>
                <input
                  id="pred-horizon"
                  type="text"
                  value={hor}
                  onChange={e => setHor(e.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/60"
                  placeholder="optional"
                  data-testid="prediction-horizon-input"
                />
              </div>

              {/* Falsifier */}
              <div>
                <label htmlFor="pred-falsifier" className="block text-[10px] font-semibold uppercase tracking-widest text-zinc-500 mb-1">
                  Falsifier <span className="text-zinc-600 normal-case font-normal">(what would prove it wrong?)</span>
                </label>
                <input
                  id="pred-falsifier"
                  type="text"
                  value={falsifier}
                  onChange={e => setFalsifier(e.target.value)}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/60"
                  placeholder="optional"
                  data-testid="prediction-falsifier-input"
                />
              </div>

              {/* Confidence */}
              <div>
                <label htmlFor="pred-confidence" className="block text-[10px] font-semibold uppercase tracking-widest text-zinc-500 mb-1">
                  Confidence <span className="text-zinc-600 normal-case font-normal">(0–1, optional)</span>
                </label>
                <input
                  id="pred-confidence"
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  value={conf}
                  onChange={e => setConf(e.target.value)}
                  className="w-32 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-indigo-500/60"
                  placeholder="e.g. 0.75"
                  data-testid="prediction-confidence-input"
                />
              </div>

              {error && (
                <p className="text-xs text-red-400" role="alert" data-testid="prediction-error">
                  {error}
                </p>
              )}

              <div className="flex justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-1.5 rounded-lg text-xs text-zinc-400 hover:bg-zinc-800 transition-colors"
                  data-testid="prediction-modal-cancel"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving || !text.trim()}
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 text-xs text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
                  data-testid="prediction-modal-submit"
                >
                  {saving ? 'Saving…' : 'Log prediction'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </>
  )
}
