// Observatory pricing seed v1 — populates llm_pricing_versions with the
// published rates as of 2026-05-03 across the five providers in scope per
// OBSERVATORY_PLAN_v1_0.md §4. Idempotent: relies on the
// uq_llm_pricing_versions_natural_key index (provider, model, token_class,
// effective_from) created by migration 038.
//
// Run:
//   npx tsx platform/src/lib/db/seed/observatory_pricing/seed_v1.ts
//
// Re-runs are safe — INSERT ... ON CONFLICT DO NOTHING — and produce no new
// rows once the v1 set has landed.

import 'server-only'
import { query } from '../../client'

const EFFECTIVE_FROM = '2026-05-03T00:00:00Z'

interface PricingSeedRow {
  provider: string
  model: string
  token_class: string
  price_per_million_usd: number
  source_url: string
}

const PRICING_V1: PricingSeedRow[] = [
  // ---------------------------------------------------------------------------
  // Anthropic — https://www.anthropic.com/pricing
  // Cache-write billed at 1.25× input; cache-read at 0.1× input (per
  // OBSERVATORY_PLAN §4.1).
  // ---------------------------------------------------------------------------
  { provider: 'anthropic', model: 'claude-opus-4-6',   token_class: 'input',        price_per_million_usd: 15.00, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-opus-4-6',   token_class: 'output',       price_per_million_usd: 75.00, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-opus-4-6',   token_class: 'cache_write',  price_per_million_usd: 18.75, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-opus-4-6',   token_class: 'cache_read',   price_per_million_usd:  1.50, source_url: 'https://www.anthropic.com/pricing' },

  { provider: 'anthropic', model: 'claude-sonnet-4-6', token_class: 'input',        price_per_million_usd:  3.00, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-sonnet-4-6', token_class: 'output',       price_per_million_usd: 15.00, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-sonnet-4-6', token_class: 'cache_write',  price_per_million_usd:  3.75, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-sonnet-4-6', token_class: 'cache_read',   price_per_million_usd:  0.30, source_url: 'https://www.anthropic.com/pricing' },

  { provider: 'anthropic', model: 'claude-haiku-4-5',  token_class: 'input',        price_per_million_usd:  1.00, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-haiku-4-5',  token_class: 'output',       price_per_million_usd:  5.00, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-haiku-4-5',  token_class: 'cache_write',  price_per_million_usd:  1.25, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-haiku-4-5',  token_class: 'cache_read',   price_per_million_usd:  0.10, source_url: 'https://www.anthropic.com/pricing' },

  // ---------------------------------------------------------------------------
  // OpenAI — https://openai.com/api/pricing/
  // `cached_input` from the brief maps to `cache_read` token_class (the schema's
  // canonical name; OpenAI's published label preserved in source_url citation).
  // o-series: reasoning_tokens billed as output per OBSERVATORY_PLAN §4.2 — no
  // separate `reasoning` row is required because the multiplier is 1× output.
  // ---------------------------------------------------------------------------
  { provider: 'openai', model: 'gpt-4.1',      token_class: 'input',      price_per_million_usd:  2.00,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'gpt-4.1',      token_class: 'output',     price_per_million_usd:  8.00,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'gpt-4.1',      token_class: 'cache_read', price_per_million_usd:  0.50,  source_url: 'https://openai.com/api/pricing/' },

  { provider: 'openai', model: 'gpt-4.1-mini', token_class: 'input',      price_per_million_usd:  0.40,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'gpt-4.1-mini', token_class: 'output',     price_per_million_usd:  1.60,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'gpt-4.1-mini', token_class: 'cache_read', price_per_million_usd:  0.10,  source_url: 'https://openai.com/api/pricing/' },

  { provider: 'openai', model: 'gpt-4.1-nano', token_class: 'input',      price_per_million_usd:  0.10,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'gpt-4.1-nano', token_class: 'output',     price_per_million_usd:  0.40,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'gpt-4.1-nano', token_class: 'cache_read', price_per_million_usd:  0.025, source_url: 'https://openai.com/api/pricing/' },

  { provider: 'openai', model: 'o3',           token_class: 'input',      price_per_million_usd:  2.00,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'o3',           token_class: 'output',     price_per_million_usd:  8.00,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'o3',           token_class: 'cache_read', price_per_million_usd:  0.50,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'o3',           token_class: 'reasoning',  price_per_million_usd:  8.00,  source_url: 'https://openai.com/api/pricing/' },

  { provider: 'openai', model: 'o4-mini',      token_class: 'input',      price_per_million_usd:  1.10,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'o4-mini',      token_class: 'output',     price_per_million_usd:  4.40,  source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'o4-mini',      token_class: 'cache_read', price_per_million_usd:  0.275, source_url: 'https://openai.com/api/pricing/' },
  { provider: 'openai', model: 'o4-mini',      token_class: 'reasoning',  price_per_million_usd:  4.40,  source_url: 'https://openai.com/api/pricing/' },

  // ---------------------------------------------------------------------------
  // Gemini — https://ai.google.dev/gemini-api/docs/pricing
  // Standard-tier rates (≤200K context window for 2.5 Pro). Long-context tier
  // is a v2 enhancement per OBSERVATORY_PLAN §4.3; not seeded here.
  // ---------------------------------------------------------------------------
  { provider: 'gemini', model: 'gemini-2.5-pro',   token_class: 'input',  price_per_million_usd: 1.25, source_url: 'https://ai.google.dev/gemini-api/docs/pricing' },
  { provider: 'gemini', model: 'gemini-2.5-pro',   token_class: 'output', price_per_million_usd: 10.00, source_url: 'https://ai.google.dev/gemini-api/docs/pricing' },

  { provider: 'gemini', model: 'gemini-2.5-flash', token_class: 'input',  price_per_million_usd: 0.30, source_url: 'https://ai.google.dev/gemini-api/docs/pricing' },
  { provider: 'gemini', model: 'gemini-2.5-flash', token_class: 'output', price_per_million_usd: 2.50, source_url: 'https://ai.google.dev/gemini-api/docs/pricing' },

  { provider: 'gemini', model: 'gemini-2.5-flash-lite', token_class: 'input',  price_per_million_usd: 0.015, source_url: 'https://ai.google.dev/gemini-api/docs/pricing' },
  { provider: 'gemini', model: 'gemini-2.5-flash-lite', token_class: 'output', price_per_million_usd: 0.060, source_url: 'https://ai.google.dev/gemini-api/docs/pricing' },

  // ---------------------------------------------------------------------------
  // DeepSeek — https://api-docs.deepseek.com/quick_start/pricing
  // V3 chat: cache-miss input $0.27, output $1.10, cache-hit input $0.07.
  // R1 reasoner: cache-miss input $0.55, output $2.19, cache-hit input $0.14.
  // R1 reasoning tokens fold into completion_tokens (no separate field per §4.4).
  // ---------------------------------------------------------------------------
  { provider: 'deepseek', model: 'deepseek-chat',     token_class: 'input',      price_per_million_usd: 0.27, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-chat',     token_class: 'output',     price_per_million_usd: 1.10, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-chat',     token_class: 'cache_read', price_per_million_usd: 0.07, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },

  { provider: 'deepseek', model: 'deepseek-reasoner', token_class: 'input',      price_per_million_usd: 0.55, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-reasoner', token_class: 'output',     price_per_million_usd: 2.19, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-reasoner', token_class: 'cache_read', price_per_million_usd: 0.14, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },

  // ---------------------------------------------------------------------------
  // NIM (managed catalog at build.nvidia.com) — https://build.nvidia.com
  // Self-hosted NIM is a v2 deferral per OBSERVATORY_PLAN §4.5; only managed
  // catalog is seeded here.
  // ---------------------------------------------------------------------------
  { provider: 'nim', model: 'meta/llama-3.1-405b-instruct', token_class: 'input',  price_per_million_usd: 3.00, source_url: 'https://build.nvidia.com' },
  { provider: 'nim', model: 'meta/llama-3.1-405b-instruct', token_class: 'output', price_per_million_usd: 3.00, source_url: 'https://build.nvidia.com' },

  { provider: 'nim', model: 'meta/llama-3.3-70b-instruct',  token_class: 'input',  price_per_million_usd: 0.90, source_url: 'https://build.nvidia.com' },
  { provider: 'nim', model: 'meta/llama-3.3-70b-instruct',  token_class: 'output', price_per_million_usd: 0.90, source_url: 'https://build.nvidia.com' },

  // ---------------------------------------------------------------------------
  // Additional model aliases — real model IDs observed in llm_usage_events that
  // differ from the canonical names above. Rates mirror the closest canonical.
  // ---------------------------------------------------------------------------

  // claude-opus-4-7: same price tier as claude-opus-4-6 until Anthropic publishes
  // separate pricing. Update when official rates are available.
  { provider: 'anthropic', model: 'claude-opus-4-7',   token_class: 'input',       price_per_million_usd: 15.00, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-opus-4-7',   token_class: 'output',      price_per_million_usd: 75.00, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-opus-4-7',   token_class: 'cache_write', price_per_million_usd: 18.75, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-opus-4-7',   token_class: 'cache_read',  price_per_million_usd:  1.50, source_url: 'https://www.anthropic.com/pricing' },

  // deepseek-v4-pro: mirrors deepseek-chat rates until DeepSeek publishes V4 pricing.
  { provider: 'deepseek', model: 'deepseek-v4-pro', token_class: 'input',      price_per_million_usd: 0.27, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-v4-pro', token_class: 'output',     price_per_million_usd: 1.10, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-v4-pro', token_class: 'cache_read', price_per_million_usd: 0.07, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },

  // nvidia/nemotron-3-super-120b-a12b: mirrors llama-405b managed catalog tier.
  { provider: 'nim', model: 'nvidia/nemotron-3-super-120b-a12b', token_class: 'input',  price_per_million_usd: 3.00, source_url: 'https://build.nvidia.com' },
  { provider: 'nim', model: 'nvidia/nemotron-3-super-120b-a12b', token_class: 'output', price_per_million_usd: 3.00, source_url: 'https://build.nvidia.com' },
]

export async function seedObservatoryPricingV1(): Promise<{
  attempted: number
  inserted: number
}> {
  const attempted = PRICING_V1.length
  let inserted = 0

  for (const row of PRICING_V1) {
    const result = await query(
      `INSERT INTO llm_pricing_versions
         (provider, model, token_class, price_per_million_usd,
          effective_from, effective_to, source_url)
       VALUES ($1, $2, $3, $4, $5, NULL, $6)
       ON CONFLICT (provider, model, token_class, effective_from)
       DO NOTHING
       RETURNING pricing_version_id`,
      [
        row.provider,
        row.model,
        row.token_class,
        row.price_per_million_usd,
        EFFECTIVE_FROM,
        row.source_url,
      ],
    )
    inserted += result.rowCount ?? 0
  }

  return { attempted, inserted }
}

export const PRICING_V1_ROW_COUNT = PRICING_V1.length
export { PRICING_V1 }

if (require.main === module) {
  seedObservatoryPricingV1()
    .then(({ attempted, inserted }) => {
      // eslint-disable-next-line no-console
      console.log(
        `[observatory_pricing/seed_v1] attempted=${attempted} inserted=${inserted} skipped=${attempted - inserted}`,
      )
      process.exit(0)
    })
    .catch((err: unknown) => {
      // eslint-disable-next-line no-console
      console.error('[observatory_pricing/seed_v1] failed:', err)
      process.exit(1)
    })
}
