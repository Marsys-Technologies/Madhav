'use client'

import { getSuggestedQuestions } from '@/lib/consume/question_templates'

interface Props {
  readyAssets: string[]
  onSelect: (q: string) => void
}

export function QuestionSuggester({ readyAssets, onSelect }: Props) {
  const suggestions = getSuggestedQuestions(readyAssets)
  if (!suggestions.length) return null

  return (
    <div className="mb-4">
      <p className="mb-2 text-xs text-brand-text-3 uppercase tracking-wider">Suggested questions</p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((q, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onSelect(q)}
            className="rounded-full border border-brand-gold-4/40 px-3 py-1 text-sm text-brand-gold-2 hover:border-brand-gold-1 hover:bg-brand-gold-1/10 transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
