export type Role = 'super_admin' | 'guest'
export type AccountStatus = 'pending' | 'active' | 'disabled'
export type PyramidStatus = 'not_started' | 'in_progress' | 'complete'
export type ConversationModule = 'build' | 'consume'
export type MessageRole = 'user' | 'assistant' | 'tool'

export interface Profile {
  id: string
  role: Role
  status: AccountStatus
  name: string | null
  username: string | null
  email: string | null
  approved_at: string | null
  approved_by: string | null
  created_at: string
}

export interface Chart {
  id: string
  client_id: string
  native_id: string
  name: string
  birth_date: string
  birth_time: string
  birth_place: string
  birth_lat: number | null
  birth_lng: number | null
  ayanamsa: string
  house_system: string
  created_at: string
}

export interface PyramidLayer {
  id: string
  chart_id: string
  native_id: string
  layer: string
  sublayer: string
  status: PyramidStatus
  version: string | null
  updated_at: string
}

export interface Document {
  id: string
  chart_id: string
  native_id: string
  layer: string
  name: string
  storage_path: string
  version: string
  created_at: string
  updated_at: string
}

export interface Conversation {
  id: string
  chart_id: string
  native_id: string
  user_id: string
  module: ConversationModule
  title: string | null
  created_at: string
}

export interface Message {
  id: string
  conversation_id: string
  native_id: string
  role: MessageRole
  content: string | null
  tool_calls: unknown | null
  panel_metadata: unknown | null
  created_at: string
}

export interface Report {
  id: string
  chart_id: string
  native_id: string
  domain: string
  title: string
  storage_path: string
  version: string
  created_at: string
  updated_at: string
}

export interface ChartFactsRow {
  id?: string
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
  source_section: string
  provenance?: Record<string, unknown>
  is_stale?: boolean
}

export interface MsrSignal {
  signal_id: string
  native_id: string
  domain: string
  planet: string | null
  house: number | null
  nakshatra: string | null
  dasha_lord: string | null
  confidence: number
  significance: number
  is_forward_looking: boolean
  claim_text: string
  classical_basis: string | null
  falsifier: string | null
  source_file: string
  source_version: string
  ingested_at: string
  // 8 new source fields added in migration 028 (KARN-W2-R1)
  signal_type?: string | null
  temporal_activation?: string | null
  valence?: string | null
  entities_involved?: unknown | null
  supporting_rules?: unknown | null
  rpt_deep_dive?: string | null
  v6_ids_consumed?: unknown | null
  prior_id?: string | null
}
