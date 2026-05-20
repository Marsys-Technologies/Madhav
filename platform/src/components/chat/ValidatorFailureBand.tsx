'use client'

import { useState } from 'react'
import type { GateVerdict } from '@/lib/streams/data_parts'

interface ValidatorFailureBandProps {
  issues: string[]
  isSuperAdmin: boolean
  onOpenDetails: () => void
  gates?: GateVerdict[]
}

const VERDICT_STYLES: Record<GateVerdict['verdict'], string> = {
  FAIL: 'bg-red-900/60 text-red-300',
  WARN: 'bg-yellow-900/60 text-yellow-300',
  PASS: 'bg-green-900/60 text-green-300',
}

export function ValidatorFailureBand({
  issues,
  isSuperAdmin,
  onOpenDetails,
  gates,
}: ValidatorFailureBandProps) {
  const [expanded, setExpanded] = useState(false)

  const flagEnabled = process.env.NEXT_PUBLIC_MARSYS_FLAG_R10_VALIDATOR_GATES === 'true'
  const showGates = flagEnabled && gates && gates.length > 0

  return (
    <div
      className="mb-2 rounded-md border border-red-500/40 bg-red-950/40 px-3 py-2 text-xs"
      role="alert"
      data-testid="v2-validator-failure-band"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2 min-w-0 flex-1">
          <span
            className="mt-0.5 shrink-0 text-red-400"
            aria-hidden="true"
          >
            ✕
          </span>
          <div className="min-w-0 flex-1">
            <button
              type="button"
              className="w-full text-left flex items-center gap-2"
              onClick={() => showGates && setExpanded(e => !e)}
              aria-expanded={showGates ? expanded : undefined}
              data-testid="v2-validator-failure-header"
            >
              <p className="font-semibold text-red-300">Citation validation failed</p>
              {showGates && (
                <span className="text-red-400/60 text-[10px]" aria-hidden="true">
                  {expanded ? '▲' : '▼'}
                </span>
              )}
            </button>

            {!expanded && (
              <>
                {isSuperAdmin && issues.length > 0 ? (
                  <ul className="mt-1 space-y-0.5 text-red-400/80">
                    {issues.map((issue, i) => (
                      <li key={i} className="truncate" title={issue}>
                        {issue}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-0.5 text-red-400/70">
                    One or more citations could not be verified.
                  </p>
                )}
              </>
            )}

            {showGates && expanded && (
              <ul className="mt-2 space-y-1" data-testid="v2-validator-gate-list">
                {gates!.map((gate, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span
                      className={`shrink-0 rounded px-1 py-0.5 text-[10px] font-bold uppercase ${VERDICT_STYLES[gate.verdict]}`}
                      data-testid={`v2-gate-verdict-${i}`}
                    >
                      {gate.verdict}
                    </span>
                    <span className="font-mono text-red-300/90">{gate.name}</span>
                    <span className="text-red-400/70 min-w-0 break-words">{gate.reason}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onOpenDetails}
          className="shrink-0 rounded px-2 py-0.5 text-[10px] font-medium text-red-300 hover:bg-red-900/60 transition-colors"
          data-testid="v2-validator-failure-details-btn"
        >
          Details
        </button>
      </div>
    </div>
  )
}
