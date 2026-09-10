'use client'

import { useState } from 'react'
import type { InterpretationSetEntry, ReceiptInterpretationSets, SignificantJudgmentCategory } from '@/lib/pariprashna/interpretation/schema'

/**
 * The reader-facing "Read it another way" / "What would change my mind"
 * affordances (PPR-05, roadmap line 105 — G3-E). Depends on G3-B's
 * `interpretation_sets` (PPR-02, `@/lib/pariprashna/interpretation/schema`),
 * already assembled server-side; this component is pure presentation over
 * that already-assembled data (see `TurnState.interpretationSets`'s own doc
 * comment in `state/types.ts` for why there is no live wire threading it in
 * yet — out of this lane's scope).
 *
 * PPR-05 is explicit: these affordances "MUST be affordances, never forced
 * into the prose flow." This component therefore has exactly one caller —
 * `RightDock.tsx` — and is never rendered inside `FrozenBlock`/the prose
 * column. `FrozenBlock`'s prose renderer has no knowledge of this component
 * or of `interpretation_sets` at all, which is the structural (not just
 * visual) proof that the affordance cannot leak into the reading itself.
 *
 * Three honest states, mirroring `ReceiptInterpretationSets.status` /
 * `InterpretationSetEntry.status` exactly — never a fourth invented one, and
 * never a silent hide (§N.6/§N.7 item 6 — "an honest null beats an invented
 * judgment", "never present ... never silently drop"):
 *
 *  - receipt-level `status: 'unavailable'` — the whole check did not run
 *    this turn (flag off, or a semantic-blocks dependency gap). No
 *    per-judgment content exists to show, so this renders ONE disclosed
 *    line, not a stale/fake affordance.
 *  - receipt-level `status: 'measured'` with `sets: []` — the check ran and
 *    genuinely found no SIGNIFICANT judgments this turn. Distinct from
 *    `unavailable` (the check ran; there was simply nothing to check),
 *    disclosed as its own honest line.
 *  - per-entry `status: 'waived'` — the check ran for this judgment but
 *    could not produce 3 distinct candidates; `waiver_reason` is shown
 *    verbatim rather than fabricating alternates.
 *  - per-entry `status: 'generated'` — the real affordances: the
 *    non-selected candidates ("Read it another way") and the falsifier
 *    ("What would change my mind"), both click-to-expand, matching
 *    `GroundingCard.tsx`'s established disclosure interaction.
 */

const CATEGORY_LABEL: Record<SignificantJudgmentCategory, string> = {
  domain_verdict: 'Domain verdict',
  time_indexed: 'Time-indexed claim',
  remedial: 'Remedial guidance',
  prediction_detected: 'Prediction',
  rules_in_tension: 'Rules in tension',
}

export function InterpretationSetsSection({ interpretationSets }: { interpretationSets: ReceiptInterpretationSets }) {
  if (interpretationSets.status === 'unavailable') {
    return (
      <div className="mb-5" data-testid="pp-interpretation-sets" data-interpretation-status="unavailable">
        <SectionEyebrow label="Alternate readings" />
        <p className="pp-caveat" style={{ fontSize: 12.5 }}>
          The alternate-reading check did not run this turn
          {interpretationSets.unavailable_reason ? ` — ${interpretationSets.unavailable_reason}.` : '.'}
        </p>
      </div>
    )
  }

  const sets = interpretationSets.sets ?? []
  if (sets.length === 0) {
    return (
      <div className="mb-5" data-testid="pp-interpretation-sets" data-interpretation-status="measured-empty">
        <SectionEyebrow label="Alternate readings" />
        <p className="pp-caveat" style={{ fontSize: 12.5 }}>
          No significant judgments this turn needed an alternate-reading check.
        </p>
      </div>
    )
  }

  return (
    <div className="mb-5" data-testid="pp-interpretation-sets" data-interpretation-status="measured">
      <div style={{ fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--pp-gold-dim)', margin: '2px 0 10px' }}>
        <span style={{ color: 'var(--pp-ink)' }}>{sets.length}</span> ALTERNATE-READING CHECK{sets.length === 1 ? '' : 'S'}
        {interpretationSets.waived_count ? (
          <>
            {' '}
            · <span style={{ color: 'var(--pp-ink)' }}>{interpretationSets.waived_count}</span> WAIVED
          </>
        ) : null}
      </div>
      {sets.map((entry) => (
        <InterpretationJudgmentCard key={entry.judgment_id} entry={entry} />
      ))}
    </div>
  )
}

function SectionEyebrow({ label }: { label: string }) {
  return (
    <div style={{ fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--pp-gold-dim)', margin: '2px 0 10px' }}>
      {label.toUpperCase()}
    </div>
  )
}

function InterpretationJudgmentCard({ entry }: { entry: InterpretationSetEntry }) {
  return (
    <div className="mb-3" style={{ borderBottom: '1px solid rgba(201,162,76,0.1)', paddingBottom: 10 }}>
      <span
        className="block"
        style={{ fontSize: 9.5, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--pp-gold-tertiary)', marginBottom: 6 }}
      >
        {CATEGORY_LABEL[entry.category]}
      </span>
      {entry.status === 'waived' ? (
        <p className="pp-prose" style={{ fontSize: 13, lineHeight: 1.4, color: 'var(--pp-ink-dim)' }}>
          No alternate readings available this turn{entry.waiver_reason ? ` — ${entry.waiver_reason}.` : '.'}
        </p>
      ) : (
        <>
          <ReadItAnotherWay entry={entry} />
          <WhatWouldChangeMyMind falsifier={entry.falsifier} />
        </>
      )}
    </div>
  )
}

/** "Read it another way" — the non-selected candidates, plain register, click-to-expand. */
function ReadItAnotherWay({ entry }: { entry: InterpretationSetEntry }) {
  const [open, setOpen] = useState(false)
  const candidates = entry.candidates ?? []
  const alternates = candidates.filter((_, i) => i !== entry.selected_index)

  return (
    <div className="mb-2">
      <DisclosureToggle open={open} onToggle={() => setOpen((v) => !v)} label="Read it another way" />
      {open && (
        <div style={{ margin: '4px 0 6px 4px' }}>
          {alternates.length === 0 ? (
            <p className="pp-prose" style={{ fontSize: 12.5, color: 'var(--pp-ink-dim)' }}>
              No alternate readings recorded for this judgment.
            </p>
          ) : (
            alternates.map((candidate, i) => (
              <div key={i} style={{ marginBottom: 8 }}>
                <p className="pp-prose" style={{ fontSize: 13, lineHeight: 1.4, margin: 0 }}>
                  {candidate.reading}
                </p>
                <p style={{ fontSize: 11, lineHeight: 1.4, color: 'var(--pp-gold-tertiary)', margin: '2px 0 0' }}>{candidate.rationale}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}

/** "What would change my mind" — the falsifier, click-to-expand, same discipline as above. */
function WhatWouldChangeMyMind({ falsifier }: { falsifier: string | null }) {
  const [open, setOpen] = useState(false)
  return (
    <div>
      <DisclosureToggle open={open} onToggle={() => setOpen((v) => !v)} label="What would change my mind" />
      {open && (
        <div style={{ margin: '4px 0 2px 4px' }}>
          <p className="pp-prose" style={{ fontSize: 13, lineHeight: 1.4, margin: 0 }}>
            {falsifier ?? 'No falsifier recorded for this judgment.'}
          </p>
        </div>
      )}
    </div>
  )
}

function DisclosureToggle({ open, onToggle, label }: { open: boolean; onToggle: () => void; label: string }) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onToggle}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onToggle()
        }
      }}
      aria-expanded={open}
      className="flex items-center gap-1.5 cursor-pointer"
      style={{ fontSize: 11.5, color: 'var(--pp-gold)', padding: '2px 0' }}
    >
      <span className="font-mono" style={{ fontSize: 9 }}>
        {open ? '▾' : '▸'}
      </span>
      <span>{label}</span>
    </div>
  )
}
