// AIOps schema row types — mirrors migration 046.
// llm_stack_routing_override, llm_param_override, llm_config_audit,
// llm_model_health, llm_catalog_snapshot dropped in WS-0; corresponding
// row types removed in WS-0C Sub-B.

export interface LlmStackConfigRow {
  scope:        string
  active_stack: string
  updated_at:   string
  updated_by:   string
}
