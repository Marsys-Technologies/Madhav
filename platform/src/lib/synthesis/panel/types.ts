/**
 * MARSYS-JIS Phase 7 — Panel Mode shared types
 * schema_version: 1.0
 */

import type { Provider } from '@/lib/models/registry'

// ── Panel configuration ────────────────────────────────────────────────────────

export interface PanelMemberConfig {
  provider_family: Provider
  model_id: string
  temperature?: number
  prompt_variant_tag?: string
}

export interface AdjudicatorConfig {
  provider_family: Provider
  model_id: string
}

// ── Member output ──────────────────────────────────────────────────────────────

export interface PanelMemberOutput {
  member_index: number
  model_id: string
  provider_family: Provider
  status: 'success' | 'failed'
  answer?: string
  error?: string
  latency_ms: number
}

/** Anonymized view of a member output (model identity stripped for adjudicator). */
export interface AnonymizedMemberOutput {
  member_label: string
  answer: string
  latency_ms: number
}

// ── Divergence ─────────────────────────────────────────────────────────────────

export type DivergenceClass =
  | 'DIS.class.factual'
  | 'DIS.class.interpretive'
  | 'DIS.class.scope'
  | 'DIS.class.confidence'
  | 'DIS.class.extension'

export type MemberAlignment = 'aligned' | 'partial' | 'dissent'

// ── Adjudication ──────────────────────────────────────────────────────────────

export interface DivergenceSummary {
  // Null means the adjudicator response could not be evaluated.
  has_divergence: boolean | null
  divergence_count: number | null
  summary_text: string
}

export interface AdjudicationResult {
  final_answer: string
  divergence_summary: DivergenceSummary
  member_alignment: Record<string, MemberAlignment>
  adjudicator_model_id: string
  latency_ms: number
}

// ── Degrade ────────────────────────────────────────────────────────────────────

export interface DegradeNotice {
  failed_member_index: number
  reason: string
  surviving_members: number
}

// ── Panel result (full output of panel_strategy) ───────────────────────────────

export interface PanelResult {
  member_outputs: PanelMemberOutput[]
  adjudication: AdjudicationResult
  degrade_notice?: DegradeNotice
}
