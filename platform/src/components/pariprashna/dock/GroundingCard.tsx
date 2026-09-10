'use client'

import { useState } from 'react'
import type { Citation } from '../state/types'
import type { ConfidenceType } from '@/lib/pariprashna/confidence/types'

const GRADE_GLYPH: Record<Citation['grade'], string> = {
  confirmed: '●',
  supported: '◐',
  catalog: '○',
  honest_gap: '—',
}
const GRADE_LABEL: Record<Citation['grade'], string> = {
  confirmed: 'verified',
  supported: 'supported',
  catalog: 'catalog',
  honest_gap: 'honest gap',
}

/**
 * P2-close Lane K (PPR-03 typed confidence, G3-C). Reader-facing labels for
 * the 5-type enum in `confidence/types.ts` — plain-language, never the
 * internal type name verbatim (CLAUDE.md §L "no internal register in prose").
 */
const CONFIDENCE_TYPE_LABEL: Record<ConfidenceType, string> = {
  deterministic_fact: 'chart fact',
  structural_prior: 'structural signal',
  classical_prior: 'classical source',
  empirically_calibrated: 'calibrated',
  unresolved: 'untyped',
}

/**
 * One grounding row (§6.7 card / §N.6 density principle): confirmed and
 * catalog-only findings are never flattened together — shape + label
 * differentiate, never color alone. Click opens the mono audit detail
 * beneath (fact/citation ref), same affordance for every entitlement tier
 * (P4) — only whether it *resolves* to raw data differs, never whether the
 * affordance exists.
 *
 * `confidenceType` (Lane K): the PPR-03 typing for THIS citation's own `ref`,
 * looked up by `RightDock.tsx` from the turn's receipt
 * (`confidence_typing.entries[].ref`, the same token as `citation.ref` — see
 * `TypedConfidenceEntrySchema`'s own doc comment). `undefined` when the
 * receipt hasn't arrived yet, the flag was off this turn, or this specific
 * ref wasn't typed — renders nothing rather than a guessed type (§N.7 item 6).
 */
export function GroundingCard({
  citation,
  highlighted,
  registerRef,
  confidenceType,
}: {
  citation: Citation
  highlighted: boolean
  registerRef?: (el: HTMLDivElement | null) => void
  confidenceType?: ConfidenceType
}) {
  const [open, setOpen] = useState(false)
  return (
    <div>
      <div
        ref={registerRef}
        role="button"
        tabIndex={0}
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setOpen((v) => !v)
          }
        }}
        className="flex items-baseline gap-2.5 py-2 cursor-pointer"
        style={{
          borderBottom: '1px solid rgba(201,162,76,0.1)',
          background: highlighted ? 'var(--pp-tint)' : undefined,
          transition: 'background 0.3s var(--pp-ease)',
        }}
      >
        <span className="font-mono flex-none" style={{ fontSize: '10px', color: 'var(--pp-gold)', minWidth: '16px' }}>
          {citation.n}
        </span>
        <span className="flex-1 min-w-0">
          <span className="pp-prose block" style={{ fontSize: '14px', lineHeight: 1.35 }}>
            {citation.title}
          </span>
          <span className="block mt-0.5" style={{ fontSize: '9.5px', color: 'var(--pp-gold-tertiary)' }}>
            {citation.relevance}
          </span>
        </span>
        <span
          className="flex-none"
          style={{
            fontSize: '8.5px',
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: citation.grade === 'confirmed' ? 'var(--pp-gold)' : 'var(--pp-gold-tertiary)',
          }}
        >
          {GRADE_GLYPH[citation.grade]} {GRADE_LABEL[citation.grade]}
        </span>
      </div>
      {open && (
        <div
          className="font-mono"
          style={{
            margin: '4px 0 6px 26px',
            padding: '10px 12px',
            background: 'var(--pp-surface)',
            border: '1px solid var(--pp-rule)',
            borderRadius: '7px',
            fontSize: '10px',
            lineHeight: 1.7,
            color: 'var(--pp-gold-dim)',
          }}
        >
          {citation.ref}
          {confidenceType && (
            <>
              {'  ·  '}
              <span style={{ color: 'var(--pp-gold-tertiary)' }}>{CONFIDENCE_TYPE_LABEL[confidenceType]}</span>
            </>
          )}
        </div>
      )}
    </div>
  )
}
