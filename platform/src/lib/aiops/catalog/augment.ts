import { MODELS, getModelMeta, type Provider } from '@/lib/models/registry'
import type { CatalogEntry, RawModelEntry } from './types'

// Build index of curated metadata per provider
const METADATA_INDEX: Partial<Record<Provider, Record<string, CatalogEntry>>> = {}

function getMetadataIndex(provider: Provider): Record<string, CatalogEntry> {
  if (METADATA_INDEX[provider]) return METADATA_INDEX[provider]!
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const data = require(`./metadata/${provider}.json`) as CatalogEntry[]
    const idx: Record<string, CatalogEntry> = {}
    for (const entry of data) {
      idx[entry.model_id] = entry
    }
    METADATA_INDEX[provider] = idx
    return idx
  } catch {
    METADATA_INDEX[provider] = {}
    return {}
  }
}

/** Registry-based index for fast lookup */
const REGISTRY_INDEX: Record<string, (typeof MODELS)[0]> = Object.fromEntries(
  MODELS.map(m => [m.id, m])
)

/**
 * Augments raw catalog entries from a provider with registry + curated metadata.
 * Priority: registry entry → curated metadata file → METADATA_PENDING.
 */
export function augmentEntries(rawEntries: RawModelEntry[], provider: Provider): CatalogEntry[] {
  const metaIdx = getMetadataIndex(provider)
  return rawEntries.map(raw => {
    const id = raw.id

    // 1. Registry source of truth
    const reg = REGISTRY_INDEX[id]
    if (reg) {
      return {
        model_id:           id,
        provider:           reg.provider,
        label:              reg.label,
        context_window:     reg.maxInputTokens ?? null,
        param_count:        null,
        capabilities:       [...reg.capabilities],
        role:               reg.role,
        cost_input_per_1m:  reg.costPer1MInput,
        cost_output_per_1m: reg.costPer1MOutput,
        metadata_pending:   false,
        is_registry_entry:  true,
      } satisfies CatalogEntry
    }

    // 2. Curated metadata file
    const curated = metaIdx[id]
    if (curated) {
      return { ...curated, model_id: id, provider, is_registry_entry: false, metadata_pending: false } satisfies CatalogEntry
    }

    // 3. METADATA_PENDING — newly discovered model
    return {
      model_id:           id,
      provider,
      label:              (raw.label as string | undefined) ?? id,
      context_window:     null,
      param_count:        null,
      capabilities:       [],
      role:               null,
      cost_input_per_1m:  null,
      cost_output_per_1m: null,
      metadata_pending:   true,
      is_registry_entry:  false,
    } satisfies CatalogEntry
  })
}
