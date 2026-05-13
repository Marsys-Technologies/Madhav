import type { Provider, Capability, ModelRole } from '@/lib/models/registry'

export type CatalogFetchStatus = 'ok' | 'auth_fail' | 'timeout' | 'error' | 'unconfigured'

export interface CatalogEntry {
  model_id:      string
  provider:      Provider
  label:         string
  context_window: number | null    // null = unknown / METADATA_PENDING
  param_count:   number | null    // null = unknown / METADATA_PENDING
  capabilities:  Capability[]
  role:          ModelRole | null
  cost_input_per_1m:  number | null
  cost_output_per_1m: number | null
  metadata_pending:   boolean
  is_registry_entry:  boolean     // present in MODELS[]
  quirks?: {                      // Phase 2 adapter-layer reservation
    reasoning_via?: 'native' | 'markers' | 'none'
    system_block_required?: boolean
  }
}

export interface CatalogFetchResult {
  status:     CatalogFetchStatus
  models:     CatalogEntry[]
  raw:        unknown
  fetched_at: string
  stale?:     boolean
  last_successful_fetch?: string
}

/** Minimal shape of a provider model listing before augmentation. */
export interface RawModelEntry {
  id:       string
  label?:   string
  owned_by?: string
  [key: string]: unknown
}
