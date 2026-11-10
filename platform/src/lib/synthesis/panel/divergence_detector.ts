/**
 * MARSYS-JIS Phase 7 — Divergence Detector
 * schema_version: 1.0
 *
 * Classifies each pairwise disagreement between panel members into one of
 * five classes from the DIS.class.panel_divergence taxonomy. The classification
 * attaches to the audit event at payload.panel.divergence_classification.
 *
 * Classification is heuristic + keyword-based (no additional LLM call).
 * The adjudication result's divergence_summary.summary_text is the source.
 */

import type { PanelMemberOutput, AdjudicationResult, DivergenceClass, MemberAlignment } from './types'

// ── Classification output ──────────────────────────────────────────────────────

export interface DivergenceInstance {
  class: DivergenceClass
  description: string
  member_indices: number[]
}

export interface DivergenceClassification {
  has_divergence: boolean | null
  instances: DivergenceInstance[]
  member_alignment_summary: Record<string, MemberAlignment>
}

// ── Classification keywords ────────────────────────────────────────────────────

const CLASS_SIGNALS: Array<{ class: DivergenceClass; keywords: string[] }> = [
  {
    class: 'DIS.class.factual',
    keywords: ['house', 'lord', 'planet', 'degree', 'dasha', 'period', 'year', 'date', 'position', 'sign'],
  },
  {
    class: 'DIS.class.interpretive',
    keywords: ['interpret', 'mean', 'signif', 'suggest', 'indicate', 'imply', 'understand'],
  },
  {
    class: 'DIS.class.scope',
    keywords: ['framing', 'focus', 'approach', 'perspective', 'scope', 'question', 'aspect'],
  },
  {
    class: 'DIS.class.confidence',
    keywords: ['confident', 'certainty', 'probable', 'likely', 'unlikely', 'strong', 'weak', 'high', 'low'],
  },
  {
    class: 'DIS.class.extension',
    keywords: ['remedy', 'remedial', 'additional', 'extended', 'extra', 'beyond', 'added', 'recommendation'],
  },
]

// ── Main entry ─────────────────────────────────────────────────────────────────

export function classifyDivergence(
  memberOutputs: PanelMemberOutput[],
  adjudication: AdjudicationResult,
): DivergenceClassification {
  const { has_divergence, summary_text, divergence_count } = adjudication.divergence_summary

  if (has_divergence === null || divergence_count === null) {
    return { has_divergence: null, instances: [], member_alignment_summary: adjudication.member_alignment }
  }

  if (!has_divergence || divergence_count === 0) {
    return {
      has_divergence: false,
      instances: [],
      member_alignment_summary: adjudication.member_alignment,
    }
  }

  const summaryLower = summary_text.toLowerCase()

  // Collect all class signals that fire on the summary text.
  const instances: DivergenceInstance[] = []
  for (const { class: cls, keywords } of CLASS_SIGNALS) {
    const hit = keywords.some(kw => summaryLower.includes(kw))
    if (hit) {
      const dissentingIndices = memberOutputs
        .filter((_, i) => {
          const key = `member_${i + 1}`
          const alignment = adjudication.member_alignment[key]
          return alignment === 'dissent' || alignment === 'partial'
        })
        .map(o => o.member_index)

      instances.push({
        class: cls,
        description: `Detected via summary text keyword match: "${cls}"`,
        member_indices: dissentingIndices,
      })
    }
  }

  // If no specific class fired, fall back to interpretive (generic disagreement).
  if (instances.length === 0) {
    instances.push({
      class: 'DIS.class.interpretive',
      description: 'Generic disagreement detected; no specific class keywords matched',
      member_indices: [],
    })
  }

  return {
    has_divergence: true,
    instances,
    member_alignment_summary: adjudication.member_alignment,
  }
}
