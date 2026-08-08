/**
 * synthesis/types.ts — Large-N Synthesis Instrument: shared contracts
 * ====================================================================
 * WP-1.4 (LCA-15 / R-48). The audit's root cause: NO serving path composes
 * N-hundred factors. Every existing surface either (a) dumps a flat top-K wall
 * (query_signals over 66,836 rows → the F-0949 flat-wall), (b) un-budgets the
 * payload, or (c) returns IDs-without-text. Meanwhile the L2 pre-aggregation
 * (bodha_chart_gestalt verdict map, bodha_cdlm_* linkage cells, bodha_cgm_paths
 * dispositor chains) exists PRECISELY to compose large evidence — and nothing
 * consumes it.
 *
 * This module defines the staged retrieval-with-aggregation contract:
 *   (1) P-10 intent decomposition   → EvidenceContract
 *   (2) plan against PRE-AGGREGATED  → PlanStep[] (gestalt/CDLM/CGM first)
 *   (3) map-reduce over families     → FamilyComposite[] with running budget
 *   (4) narrative + DERIVATION LEDGER → LargeNAnswer (every claim → ids)
 *
 * SKELETON SCOPE (W1): the stages RUN and COMPOSE today against existing served
 * surfaces. Depth deepens automatically when WP-2.2 populates the currently-thin
 * stages (native-chart contradictions=0, CDLM narrative seeds NULL) at W3 — the
 * instrument DISCLOSES thin stages, never fabricates them (B.10).
 */

// ── (1) intent decomposition — P-10 ───────────────────────────────────────────

import type { CanonicalDomain } from '@/lib/domain_vocabulary'

/**
 * The life-domains the L2 layer tags signals with (bodha_msr_signals.domains_affected_array).
 *
 * ADHIṢṬHĀNA Lane A7: previously a local literal (6 members + 'other'), one of 4 divergent
 * TS domain vocabularies. Now sourced from the canonical 13-domain SSoT
 * (`brahmagyan/domain_vocabulary.py` / `@/lib/domain_vocabulary`). The local 'other' fallback
 * is superseded by the SSoT's own unknown-domain term, 'general' — identical semantic role
 * (intent.ts's decompose() renames its 'other' literal to 'general' accordingly; no test
 * asserted the literal 'other' string, so this is a behavior-preserving rename, not a
 * semantic change). This type only widens the DECLARED domain space to 13; intent.ts's own
 * keyword-classifier content (DOMAIN_KEYWORDS/HEAVY_TEMPLATES) intentionally still covers
 * only the original 6 + general — inventing keyword lists for the 7 newly-representable
 * domains would be fabricated content, not a vocabulary fix (see intent.ts comment).
 */
export type Domain = CanonicalDomain

/**
 * One family of evidence the compound question needs. The evidence CONTRACT is the
 * set of these — the instrument's promise of WHAT it will go gather, made explicit
 * BEFORE any retrieval (so an un-served family is disclosed, not silently absent).
 */
export interface EvidenceFamilyRequest {
  /** Stable key, e.g. 'domain:relationship' or 'cross_link:relationship×career'. */
  family_key: string
  /** The primary domain this family draws from. */
  domain: Domain
  /** Why this family is in the contract (the decomposition rationale). */
  role: 'primary' | 'cross_domain' | 'karaka_chain' | 'tension' | 'orientation'
  /** Human rationale — the P-10 "why this evidence is needed" note. */
  rationale: string
}

/**
 * The evidence contract: the decomposed shape of a compound question. Produced by
 * intent decomposition (SKELETON: deterministic keyword→domain map; W3: LLM-planned).
 */
export interface EvidenceContract {
  question: string
  /** The primary domain the question centers on. */
  primary_domain: Domain
  /** All evidence families the answer must compose (primary + cross-domain + chains). */
  families: EvidenceFamilyRequest[]
  /** Which pre-computed heavy-question template matched, if any (for traceability). */
  matched_template: string | null
  /** How the decomposition was produced — SKELETON marker for W3 upgrade path. */
  decomposition_method: 'keyword_template' | 'keyword_generic'
}

// ── (2)/(3) map-reduce — bounded family composites ────────────────────────────

/**
 * The response-budget the map-reduce runs under. The ANTIDOTE to the flat top-K
 * wall + un-budgeted dump (E4 proportionality): the instrument NEVER serves more
 * than `total_signal_rows` atomic signal rows across ALL families combined, and
 * never more than `per_family_cap` from any single family. When the running budget
 * is exhausted, remaining families are DISCLOSED (served=0, total=N, more) — not dumped.
 */
export interface StageBudget {
  /** Hard ceiling on atomic signal exemplar rows across the whole composed answer. */
  total_signal_rows: number
  /** Per-family exemplar ceiling — no single family can monopolize the budget. */
  per_family_cap: number
  /** Ceiling on pre-aggregated dispositor paths surfaced. */
  dispositor_cap: number
}

export const DEFAULT_BUDGET: StageBudget = {
  total_signal_rows: 60,
  per_family_cap: 10,
  dispositor_cap: 8,
}

/** One atomic exemplar surfaced for a family — reference + text (never an ID-without-text). */
export interface SignalExemplar {
  signal_id: string
  headline: string | null
  summary: string | null
  salience: number | null
  /** L1 fact_ids this signal grounds to (§N.5 — MUST resolve). */
  constituent_fact_ids: string[]
}

/**
 * The REDUCE output for one evidence family: a bounded composite. Carries the
 * DISCLOSED true family size, the bounded exemplars actually served, and the honest
 * "was I trimmed?" bit — so a 12,364-signal family becomes one composite with 10
 * exemplars + `total=12364, more_available=true`, never a 12,364-row wall.
 */
export interface FamilyComposite {
  family_key: string
  domain: Domain
  role: EvidenceFamilyRequest['role']
  /** True family size under this family's filter (disclosed; from the served surface's own count). */
  total_in_family: number
  /** How many exemplars this composite actually served (≤ per_family_cap, ≤ remaining budget). */
  served: number
  /** TRUE iff total_in_family > served — honest trim bit (WP-1.5 receipt honesty). */
  more_available: boolean
  /** The bounded exemplars, each with resolvable references + text. */
  exemplars: SignalExemplar[]
  /** Pre-aggregated cross-domain linkage cells bearing on this family (from CDLM). */
  linkages: LinkageCell[]
  /** Honest disposition when a family could not be fully served (budget or thin stage). */
  disposition: 'served' | 'budget_exhausted' | 'thin_stage_disclosed'
  note: string
}

/** A pre-aggregated CDLM cross-domain linkage cell (bodha_cdlm_cells) — one cell, not N signals. */
export interface LinkageCell {
  domain_row: string
  domain_col: string
  shared_signal_count: number
  linkage_strength: number | null
  contradiction_flag: boolean
}

// ── (4) narrative + derivation ledger ─────────────────────────────────────────

/**
 * One DERIVATION LEDGER entry (§N.5 / B.3). Every narrative claim the instrument
 * makes carries one — naming the exact signal_ids / fact_ids / surface it rests on,
 * so the whole answer is auditable back to L1. Resolvability is a HARD test: every
 * id here must resolve against the DB (or the injected surface, in unit tests).
 */
export interface DerivationLedgerEntry {
  /** The claim this entry backs (a sentence from the narrative). */
  claim: string
  /** Signal ids backing the claim (resolve to bodha_msr_signals.signal_id). */
  signal_ids: string[]
  /** L1 fact ids backing the claim (resolve to chart_facts.fact_id). */
  fact_ids: string[]
  /** Which served surface produced the evidence (provenance). */
  source_surface: string
}

/** One narrative section of the composed answer. */
export interface NarrativeSection {
  heading: string
  body: string
  /** Ledger entries scoped to this section's claims. */
  ledger: DerivationLedgerEntry[]
}

/** The composed large-N answer. */
export interface LargeNAnswer {
  chart_id: string
  ayanamsha_id: string
  question: string
  /** (1) the decomposed evidence contract. */
  contract: EvidenceContract
  /** (2) the plan — which pre-aggregated surface each stage consulted, in order. */
  plan: PlanStep[]
  /** (3) the reduced family composites (bounded). */
  families: FamilyComposite[]
  /** (4) the narrative, each section carrying its own derivation ledger. */
  narrative: NarrativeSection[]
  /** Flattened whole-answer derivation ledger (union of section ledgers). */
  derivation_ledger: DerivationLedgerEntry[]
  /** Budget accounting — proof the composition stayed bounded. */
  budget: {
    total_signal_rows_cap: number
    total_signal_rows_served: number
    families_fully_served: number
    families_disclosed_not_dumped: number
  }
  /** Honest disclosure of every stage that was thin/degraded (never silently dropped). */
  disclosures: string[]
}

/** One planned stage — names the pre-aggregated surface consulted and its result size. */
export interface PlanStep {
  stage: 'orient' | 'plan_cross_domain' | 'map_reduce_families' | 'dispositor' | 'tension'
  surface: string
  /** 'pre_aggregated' (gestalt/CDLM/CGM composites) vs 'atomic_drill' (bounded signals). */
  kind: 'pre_aggregated' | 'atomic_drill'
  note: string
}
