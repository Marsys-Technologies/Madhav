import type { CallType, ModelStack } from '@/lib/models/registry'

export interface ProbeOptions {
  stack:          ModelStack
  callType:       CallType
  role:           'primary' | 'fallback'
  modelOverride?: string   // explicit model_id; overrides registry/DB routing
}

export interface ProbeResult {
  model_id:       string
  stack:          ModelStack
  call_type:      CallType
  role:           'primary' | 'fallback'
  status:         'pass' | 'fail' | 'timeout'
  latency_ms:     number
  input_tokens:   number | null
  output_tokens:  number | null
  output_text:    string      // truncated to 300 chars
  finish_reason:  string | null
  cost_usd:       number | null
  error?:         string
}
