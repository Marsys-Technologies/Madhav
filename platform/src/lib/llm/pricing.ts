/**
 * Pricing helper — synchronous lookup against the in-code MODEL_REGISTRY.
 *
 * Adapted from CLAUDECODE_BRIEF GANGA-OVERNIGHT-S1 P2 D.2.1: brief assumed a
 * SQL `model_pricing` table; pricing in this codebase actually lives in
 * `src/lib/models/registry.ts`. So this helper reads from the registry
 * synchronously — no DB call, no TTL needed. The async signature in the brief
 * is preserved for forward compatibility (the tests pin the contract).
 */
import { MODELS, type ModelMeta } from '../models/registry'

export interface ModelPricing {
  model_id: string
  input_per_1m_usd: number
  output_per_1m_usd: number
  cache_read_per_1m_usd?: number | null
  cache_write_per_1m_usd?: number | null
}

const REGISTRY_BY_ID: Map<string, ModelMeta> = new Map(MODELS.map((m) => [m.id, m]))

export function getModelPricingSync(model_id: string): ModelPricing | null {
  const meta = REGISTRY_BY_ID.get(model_id)
  if (!meta) return null
  return {
    model_id: meta.id,
    input_per_1m_usd: meta.costPer1MInput,
    output_per_1m_usd: meta.costPer1MOutput,
    cache_read_per_1m_usd: null,
    cache_write_per_1m_usd: null,
  }
}

/** Async wrapper preserved for brief contract; synchronous under the hood. */
export async function getModelPricing(model_id: string): Promise<ModelPricing | null> {
  return getModelPricingSync(model_id)
}

export interface UsageTokens {
  input_tokens?: number | null
  output_tokens?: number | null
  cache_read_tokens?: number | null
  cache_write_tokens?: number | null
}

export function computeCostUsd(
  pricing: ModelPricing | null,
  usage: UsageTokens
): number | null {
  if (!pricing) return null
  const input = usage.input_tokens ?? 0
  const output = usage.output_tokens ?? 0
  const cacheRead = usage.cache_read_tokens ?? 0
  const cacheWrite = usage.cache_write_tokens ?? 0
  // If both input and output are null (not just zero), nothing to bill.
  if (
    (usage.input_tokens === null || usage.input_tokens === undefined) &&
    (usage.output_tokens === null || usage.output_tokens === undefined)
  ) {
    return null
  }
  const cost =
    (input / 1e6) * pricing.input_per_1m_usd +
    (output / 1e6) * pricing.output_per_1m_usd +
    (cacheRead / 1e6) * (pricing.cache_read_per_1m_usd ?? 0) +
    (cacheWrite / 1e6) * (pricing.cache_write_per_1m_usd ?? 0)
  return Math.round(cost * 1_000_000) / 1_000_000
}
