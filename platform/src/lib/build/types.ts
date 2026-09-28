// TypeScript types mirroring the GCS build_state JSON schemas (schema_version 0.3.0)

export interface Milestone {
  id: string
  title: string
  status: 'completed' | 'active' | 'pending' | string
  session_count_actual?: number
  session_count_estimated?: number | null
}

export interface MacroPhaseEntry {
  id: string
  title: string
  status: 'completed' | 'active' | 'pending'
  milestones: Milestone[]
}

export interface MacroPhase {
  id: string
  title: string
  status: 'completed' | 'active' | 'pending'
  macro_arc: MacroPhaseEntry[]
}

export interface SubPhase {
  phase_id: string
  title: string
  status: 'completed' | 'in_progress' | 'pending' | string
  session_count_actual: number
  session_count_estimated?: number | null
}

export interface PhasePlan {
  path: string
  version: string
  sub_phase: string
  status: string
  sub_phases: SubPhase[]
}

export interface TrendEntry {
  report_file: string
  session_id: string
  run_at: string
  exit_code: number
  finding_count: number
}

export interface ScriptsTrend {
  drift_detector: TrendEntry[]
  schema_validator: TrendEntry[]
  mirror_enforcer: TrendEntry[]
}

export interface RedTeamGauge {
  counter: number
  next_fires_at_counter: number
  last_fired_session: string | null
  sessions_until_next: number
}

export interface Governance {
  rebuild_status: string
  baseline_artifact_path: string | null
  baseline_closed_on: string | null
  active_step: string
  active_step_status: string
  next_step: string | null
  next_quarterly_pass: string
  red_team: RedTeamGauge
  scripts_trend: ScriptsTrend
}

export interface LastSession {
  id: string
  closed_at: string
  agent: string
  cowork_thread_name: string | null
  close_state: string
  drift_verdict: string | null
  deliverable_summary: string | null
}

export interface NextSession {
  objective: string
  proposed_cowork_thread_name: string | null
}

export interface NDEntry {
  nd_id: string
  title: string
  status: string
  issued_on: string | null
  addressed_on: string | null
}

export interface NativeDirectives {
  open: string[]
  addressed: string[]
  note: string
  entries: NDEntry[]
}

export interface DREntry {
  dr_id: string
  class: string
  status: string
  opened_on: string
  description: string
}

export interface DisagreementRegister {
  open_count: number
  resolved_count: number
  entries: DREntry[]
}

export interface CanonicalArtifact {
  canonical_id: string
  path: string
  version: string
  status: string
  fingerprint_sha256: string | null
  last_verified_session: string | null
  last_verified_on: string | null
  mirror_pair_id: string | null
}

export interface MirrorPair {
  pair_id: string
  claude_side: string
  gemini_side: string
  authoritative_side: string
  mirror_mode: string
  last_verified_session: string | null
  days_since_verified: number | null
}

export interface RedTeamPass {
  session_id: string | null
  report_path: string
  verdict: string
  finding_count: number
  residuals: string[]
  performed_on: string
}

export interface StalenessEntry {
  path: string
  since: string
  reason: string
}

export interface CurrentBrief {
  session_id: string
  status: string
  ac_total: number
  ac_passed_known: number
  may_touch: string[]
  must_not_touch: string[]
}

export interface SessionIndex {
  session_id: string
  title: string | null
  date: string | null
  class: string
  phase_id: string | null
  drift_exit: number | null
  schema_exit: number | null
  mirror_exit: number | null
  deliverable_one_liner: string | null
  detail_shard: string
}

export interface PhaseIndex {
  phase_id: string
  detail_shard: string
  status: string
  session_count?: number
}

export interface CoworkEntry {
  thread_name: string
  opened_on: string
  closed_on: string | null
  purpose: string
  outcomes: string[]
  spawned_sessions: string[]
}

export interface WorkstreamEntry {
  id: string
  title: string
  status: string
  last_activity?: string
}

export interface TodayProgress {
  date_key: string
  session_ids: string[]
  session_count: number
  files_touched_count: number
  deliverables: string[]
}

// v0.3.0: corpus density metrics
export interface ChunksByDocType {
  doc_type: string
  count: number
}

export interface EdgeClass {
  class: string
  count: number
}

export interface L3CoverageEntry {
  domain_id: string
  status: 'current' | 'stale' | 'missing' | string
}

export interface CorpusState {
  rag_chunks: number
  rag_graph_nodes: number
  rag_graph_edges: number
  msr_signals: number
  cgm_nodes: number
  cgm_reconciled_edges: number
  l3_reports_current: number
  chunks_by_doc_type: ChunksByDocType[]
  edge_classes: EdgeClass[]
  l3_coverage: L3CoverageEntry[]
}

export interface BuildState {
  schema_version: string
  generated_at: string
  generated_by_session: string
  generator_version: string
  source_fingerprints: Record<string, string>
  macro_phase: MacroPhase
  phase_plan: PhasePlan
  governance: Governance
  last_session: LastSession | null
  next_session: NextSession | null
  native_directives: NativeDirectives
  disagreement_register: DisagreementRegister
  canonical_artifacts: CanonicalArtifact[]
  mirror_pairs: MirrorPair[]
  red_team_passes: RedTeamPass[]
  staleness_register: StalenessEntry[]
  current_brief: CurrentBrief | null
  staleness_seconds_since_last_close: number
  sessions_index: SessionIndex[]
  today_progress?: TodayProgress
  phases_index?: PhaseIndex[]
  cowork_ledger?: CoworkEntry[]
  workstreams?: WorkstreamEntry[]
  recent_sessions?: SessionIndex[]
  // v0.3.0
  corpus_state?: CorpusState
  serializer_warnings?: string[]
}

// Insight card type for InsightCards component
export interface InsightCard {
  id: string
  severity: 'info' | 'positive' | 'concern'
  text: string
}
