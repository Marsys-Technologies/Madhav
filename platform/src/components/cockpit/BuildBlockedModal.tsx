'use client'

import { BlockerEntry } from '@/lib/build/plan'

interface BuildBlockedModalProps {
  blockers: BlockerEntry[]
  onDismiss: () => void
}

const STATE_BADGE: Record<string, { label: string; className: string }> = {
  stale:        { label: 'stale',        className: 'bg-amber-100 text-amber-800 border border-amber-300' },
  dormant:      { label: 'dormant',      className: 'bg-gray-100 text-gray-700 border border-gray-300' },
  error:        { label: 'error',        className: 'bg-red-100 text-red-800 border border-red-300' },
  service_down: { label: 'service down', className: 'bg-red-100 text-red-800 border border-red-300' },
  building:     { label: 'building',     className: 'bg-blue-100 text-blue-800 border border-blue-300' },
}

export function BuildBlockedModal({ blockers, onDismiss }: BuildBlockedModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-amber-50 border-b border-amber-200 px-6 py-4">
          <h2 className="text-base font-semibold text-amber-900">
            Cannot build — dependencies not ready
          </h2>
          <p className="text-sm text-amber-700 mt-1">
            Resolve the following before building.
          </p>
        </div>

        {/* Blocker list */}
        <div className="px-6 py-4 space-y-3 max-h-80 overflow-y-auto">
          {blockers.map((b) => {
            const badge = STATE_BADGE[b.dep_state] ?? { label: b.dep_state, className: 'bg-gray-100 text-gray-700' }
            return (
              <div key={b.dep_asset_id} className="border border-gray-200 rounded-md p-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-medium text-gray-900">{b.dep_asset_id}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${badge.className}`}>
                    {badge.label}
                  </span>
                </div>
                {b.guidance && (
                  <p className="text-xs text-amber-700 mt-1">{b.guidance}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Required by: {b.required_by.join(', ')}
                </p>
              </div>
            )
          })}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 flex justify-end">
          <button
            onClick={onDismiss}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  )
}
