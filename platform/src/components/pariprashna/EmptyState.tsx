'use client'

import { useReducedMotion } from './hooks/useReducedMotion'

/**
 * `empty` state (§5.3, J1 step 1): the ecliptic line — a single 1px gold
 * hairline drawn across the field at ~38% height — is the surface's entire
 * astronomy (no star field, wheel, or zodiac figure). It shares its stroke
 * language with the turn separator and the prediction card's kāla-rekhā
 * (§6.4: "one line, three duties").
 */
export function EmptyState({ examplePrompts, onPick }: { examplePrompts: string[]; onPick: (text: string) => void }) {
  const reducedMotion = useReducedMotion()
  return (
    <div className="flex-1 min-h-0 flex flex-col items-center justify-center px-6 gap-6">
      <div className="w-full max-w-md relative" style={{ height: 1 }}>
        <div
          className="pp-hairline-draw"
          style={{ animation: reducedMotion ? 'none' : undefined, transform: reducedMotion ? 'scaleX(1)' : undefined }}
        />
      </div>
      <p className="pp-prose" style={{ fontSize: 28, fontWeight: 600 }}>
        Ask the chart.
      </p>
      <div className="flex flex-wrap justify-center gap-2.5">
        {examplePrompts.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => onPick(p)}
            className="rounded-full"
            style={{
              fontSize: 12.5,
              color: 'var(--pp-ink-dim)',
              border: '1px solid var(--pp-rule)',
              background: 'var(--pp-tint)',
              padding: '8px 16px',
            }}
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  )
}
