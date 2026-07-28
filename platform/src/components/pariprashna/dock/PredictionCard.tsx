import type { PredictionCardData } from '../state/types'

const LIFECYCLE_LABEL: Record<PredictionCardData['lifecycle'], string> = {
  window_open: 'TIME-INDEXED READING · WINDOW OPEN',
  window_closing: 'TIME-INDEXED READING · WINDOW CLOSING',
  awaiting_outcome: 'TIME-INDEXED READING · AWAITING OUTCOME',
  resolved_confirmed: 'TIME-INDEXED READING · RESOLVED — CONFIRMED',
  resolved_missed: 'TIME-INDEXED READING · RESOLVED — MISSED',
  resolved_mixed: 'TIME-INDEXED READING · RESOLVED — MIXED',
}

/**
 * The signature component (§6.9): the prediction card + kāla-rekhā (time
 * hairline). Lifecycle restyles only the eyebrow text (in place, fixed
 * height — the same discipline as the working band, P1 honored even by the
 * one living component) and advances the today-dot; nothing else changes
 * post-commit. Lives in the right dock per the 2026-07-27 native ruling,
 * not inline in the conversation column.
 */
export function PredictionCard({ prediction }: { prediction: PredictionCardData }) {
  return (
    <div
      className="rounded p-4 mb-4"
      style={{ border: '1px solid var(--pp-rule-strong)', borderRadius: '4px', background: 'var(--pp-surface)' }}
    >
      <div style={{ fontSize: '9px', letterSpacing: '0.24em', textTransform: 'uppercase', color: 'var(--pp-gold)', marginBottom: '8px' }}>
        {LIFECYCLE_LABEL[prediction.lifecycle]}
      </div>
      <div className="pp-prose" style={{ fontSize: '15px', lineHeight: 1.45, marginBottom: '12px' }}>
        {prediction.claim}
      </div>

      {/* kāla-rekhā — the time hairline; the one element on the surface that moves on the scale of months */}
      <div className="relative mb-1" style={{ height: '14px' }}>
        <span className="absolute" style={{ top: 6, left: 0, right: 0, height: 1, background: 'rgba(201,162,76,0.2)' }} />
        <span
          className="absolute"
          style={{
            top: 5.5,
            left: `${prediction.windowStartFraction * 100}%`,
            width: `${(prediction.windowEndFraction - prediction.windowStartFraction) * 100}%`,
            height: 2,
            background: 'var(--pp-gold)',
          }}
        />
        <span
          className="absolute rounded-full"
          style={{
            top: 3,
            left: `${prediction.todayFractionOfSpan * 100}%`,
            width: 7,
            height: 7,
            background: 'var(--pp-gold)',
          }}
          title="Today"
        />
      </div>
      <div className="flex justify-between font-mono" style={{ fontSize: '8px', color: 'var(--pp-gold-tertiary)', marginBottom: '10px' }}>
        <span>{prediction.windowStartLabel}</span>
        <span>{prediction.windowEndLabel}</span>
      </div>

      <div className="flex items-center gap-2.5">
        <span style={{ fontSize: '10.5px', color: 'var(--pp-ink-dim)' }}>{prediction.confidencePhrase}</span>
        <span className="font-mono ml-auto" style={{ fontSize: '9px', color: 'var(--pp-gold-tertiary)' }}>
          {prediction.ref}
        </span>
      </div>
    </div>
  )
}
