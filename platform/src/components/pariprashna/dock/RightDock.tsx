'use client'

import { useEffect, useRef } from 'react'
import type { TurnState } from '../state/types'
import { GroundingCard } from './GroundingCard'
import { PredictionCard } from './PredictionCard'
import { useDockController } from './DockController'

/**
 * The collapsible right panel (§3.2, §5.8.0 ruling 2). Carries the
 * grounding ledger and the prediction-card placeholder — NOT inline in the
 * conversation column. Chips deep-link here (`⟦n⟧` → `openToCitation`);
 * clicking one opens the dock (if collapsed) and highlights + scrolls to
 * that row. No provenance anywhere — not the header, not this dock's
 * footer (§5.8.0 ruling 8c): the note at the bottom is a plain-language
 * caption, never a build id or priors dump.
 */
export function RightDock({ turns }: { turns: TurnState[] }) {
  const { open, setOpen, activeCitation } = useDockController()
  const cardRefs = useRef(new Map<string, HTMLDivElement | null>())

  useEffect(() => {
    if (!activeCitation) return
    const key = `${activeCitation.turnId}:${activeCitation.n}`
    const el = cardRefs.current.get(key)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [activeCitation])

  const turnsWithGrounding = turns.filter((t) => Object.keys(t.citations).length > 0 || t.blocks.some((b) => b.kind === 'prediction_card'))
  const orderedTurns = [...turnsWithGrounding].reverse()

  return (
    <div
      className="flex-none flex flex-col overflow-hidden rounded-[14px] transition-[width]"
      style={{
        width: open ? 312 : 46,
        background: 'var(--pp-panel)',
        border: '1px solid var(--pp-rule)',
        transitionDuration: '280ms',
        transitionTimingFunction: 'var(--pp-ease)',
      }}
    >
      <div
        className="flex items-center gap-2.5 px-3.5"
        style={{ paddingTop: 14, paddingBottom: 12, borderBottom: open ? '1px solid var(--pp-rule)' : 'none', justifyContent: open ? undefined : 'center' }}
      >
        <button
          type="button"
          className="font-mono"
          style={{ background: 'none', border: 'none', color: 'var(--pp-gold-tertiary)', fontSize: 13, cursor: 'pointer', padding: '2px 4px' }}
          onClick={() => setOpen(!open)}
          aria-label={open ? 'Collapse grounding dock' : 'Expand grounding dock'}
        >
          {open ? '»' : '«'}
        </button>
        {open && (
          <span style={{ fontFamily: 'var(--pp-font-sans)', fontSize: 11, letterSpacing: '0.28em', textTransform: 'uppercase', color: 'var(--pp-gold)', whiteSpace: 'nowrap' }}>
            Windows · Grounding
          </span>
        )}
      </div>

      {open && (
        <div className="flex-1 overflow-y-auto p-3.5">
          {orderedTurns.length === 0 && (
            <p className="pp-caveat" style={{ fontSize: 12.5 }}>
              Grounding will appear here once a reading settles.
            </p>
          )}
          {orderedTurns.map((turn) => {
            const predictionBlock = turn.blocks.find((b) => b.kind === 'prediction_card')
            const citations = Object.values(turn.citations).sort((a, b) => a.n - b.n)
            const classicalCount = citations.filter((c) => c.sourceClass === 'classical_source').length
            return (
              <div key={turn.id} className="mb-5">
                {predictionBlock?.prediction && <PredictionCard prediction={predictionBlock.prediction} />}
                {citations.length > 0 && (
                  <>
                    <div style={{ fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--pp-gold-dim)', margin: '2px 0 10px' }}>
                      <span style={{ color: 'var(--pp-ink)' }}>{citations.length}</span> CHART FACTORS
                      {classicalCount > 0 && (
                        <>
                          {' '}
                          · <span style={{ color: 'var(--pp-ink)' }}>{classicalCount}</span> CLASSICS
                        </>
                      )}
                    </div>
                    {citations.map((c) => (
                      <GroundingCard
                        key={c.n}
                        citation={c}
                        highlighted={activeCitation?.turnId === turn.id && activeCitation?.n === c.n}
                        registerRef={(el) => cardRefs.current.set(`${turn.id}:${c.n}`, el)}
                      />
                    ))}
                  </>
                )}
              </div>
            )
          })}
          <p className="pp-verse" style={{ fontSize: 12, borderLeft: 'none', paddingLeft: 0, color: 'var(--pp-gold-tertiary)', marginTop: 14 }}>
            Fills as the reading verifies, pass by pass. Cited in prose as ⟦n⟧ — a chip click opens its row here.
          </p>
        </div>
      )}
    </div>
  )
}
