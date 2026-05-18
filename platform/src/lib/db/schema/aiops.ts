// AIOps schema row types — mirrors migrations 046–052.
// 1:1 by column name and nullability. Consumed by runtime_config.ts,
// the AIOps API routes, and the Control Panel UI.

export type AiopsAction =
  | 'set_stack'
  | 'set_routing'
  | 'set_param'
  | 'reset_param'
  | 'probe'
  | 'revert'
  | 'reset_routing'    // emitted when routing override is deleted

export type AiopsModelHealthStatus =
  | 'pass'
  | 'fail'
  | 'timeout'
  | 'stale'
  | 'never_probed'

export interface LlmStackConfigRow {
  scope:        string
  active_stack: string
  updated_at:   string
  updated_by:   string
}

export interface LlmStackRoutingOverrideRow {
  scope:          string
  stack:          string
  call_type:      string
  primary_model:  string
  fallback_model: string
  updated_at:     string
  updated_by:     string
  /** NULL = permanent override; ISO string = auto-expire at this time (Phase 3C). */
  expires_at:     string | null
}

export interface LlmParamOverrideRow {
  scope:       string
  stack:       string
  call_type:   string
  param_name:  string
  param_value: unknown   // jsonb — decoded by pg client
  updated_at:  string
  updated_by:  string
}

export interface LlmModelHealthRow {
  model_id:       string
  status:         AiopsModelHealthStatus
  latency_ms:     number | null
  last_probe_at:  string | null
  last_error:     string | null
  last_probed_by: string | null
}

export interface LlmConfigAuditRow {
  id:            number
  occurred_at:   string
  actor_user_id: string
  action:        AiopsAction
  scope:         string | null
  stack:         string | null
  call_type:     string | null
  param_name:    string | null
  before_value:  unknown | null
  after_value:   unknown | null
  notes:         string | null
}

export interface LlmCatalogSnapshotRow {
  provider:    string
  model_id:    string
  fetched_at:  string
  raw_payload: unknown
  augmented:   unknown
}
