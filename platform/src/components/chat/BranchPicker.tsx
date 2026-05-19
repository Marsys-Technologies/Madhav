'use client'

interface Props {
  currentBranch: number // 1-indexed
  totalBranches: number
  onPrev: () => void
  onNext: () => void
}

/**
 * Compact inline branch navigator rendered beneath edited user message bubbles.
 * Pure display — all state lives in useBranches.
 * Renders ‹ N/M › with disabled states on boundaries.
 */
export function BranchPicker({ currentBranch, totalBranches, onPrev, onNext }: Props) {
  return (
    <span className="inline-flex items-center gap-1">
      <button
        type="button"
        onClick={onPrev}
        disabled={currentBranch <= 1}
        aria-label="Previous branch"
        className="text-xs text-zinc-400 hover:text-zinc-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        ‹
      </button>
      <span className="text-xs text-zinc-400">
        {currentBranch}
        <span className="text-zinc-600">/</span>
        {totalBranches}
      </span>
      <button
        type="button"
        onClick={onNext}
        disabled={currentBranch >= totalBranches}
        aria-label="Next branch"
        className="text-xs text-zinc-400 hover:text-zinc-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        ›
      </button>
    </span>
  )
}
