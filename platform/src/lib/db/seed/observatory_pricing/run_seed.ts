#!/usr/bin/env npx tsx
// Standalone seed runner — bypasses the server-only guard so this can be run
// directly via `npx tsx`. Functionally identical to seed_v1.ts.
// Run from platform/ dir:
//   DATABASE_URL="postgresql://..." npx tsx src/lib/db/seed/observatory_pricing/run_seed.ts

import { Pool } from 'pg'

// Pricing data inlined here so this runner has zero transitive imports
// that touch server-only. Keep in sync with seed_v1.ts PRICING_V1.
const PRICING_V1 = [
  // Anthropic
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
  { provider: 'anthropic', model: 'claude-opus-4-7',   token_class: 'input',        price_per_million_usd: 15.00, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-opus-4-7',   token_class: 'output',       price_per_million_usd: 75.00, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-opus-4-7',   token_class: 'cache_write',  price_per_million_usd: 18.75, source_url: 'https://www.anthropic.com/pricing' },
  { provider: 'anthropic', model: 'claude-opus-4-7',   token_class: 'cache_read',   price_per_million_usd:  1.50, source_url: 'https://www.anthropic.com/pricing' },
  // OpenAI
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
  // Gemini
  { provider: 'gemini', model: 'gemini-2.5-pro',   token_class: 'input',  price_per_million_usd:  1.25, source_url: 'https://ai.google.dev/gemini-api/docs/pricing' },
  { provider: 'gemini', model: 'gemini-2.5-pro',   token_class: 'output', price_per_million_usd: 10.00, source_url: 'https://ai.google.dev/gemini-api/docs/pricing' },
  { provider: 'gemini', model: 'gemini-2.5-flash', token_class: 'input',  price_per_million_usd:  0.30, source_url: 'https://ai.google.dev/gemini-api/docs/pricing' },
  { provider: 'gemini', model: 'gemini-2.5-flash', token_class: 'output', price_per_million_usd:  2.50, source_url: 'https://ai.google.dev/gemini-api/docs/pricing' },
  // DeepSeek
  { provider: 'deepseek', model: 'deepseek-chat',     token_class: 'input',      price_per_million_usd: 0.27, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-chat',     token_class: 'output',     price_per_million_usd: 1.10, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-chat',     token_class: 'cache_read', price_per_million_usd: 0.07, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-reasoner', token_class: 'input',      price_per_million_usd: 0.55, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-reasoner', token_class: 'output',     price_per_million_usd: 2.19, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-reasoner', token_class: 'cache_read', price_per_million_usd: 0.14, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-v4-pro',   token_class: 'input',      price_per_million_usd: 0.27, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-v4-pro',   token_class: 'output',     price_per_million_usd: 1.10, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  { provider: 'deepseek', model: 'deepseek-v4-pro',   token_class: 'cache_read', price_per_million_usd: 0.07, source_url: 'https://api-docs.deepseek.com/quick_start/pricing' },
  // NIM
  { provider: 'nim', model: 'meta/llama-3.1-405b-instruct',       token_class: 'input',  price_per_million_usd: 3.00, source_url: 'https://build.nvidia.com' },
  { provider: 'nim', model: 'meta/llama-3.1-405b-instruct',       token_class: 'output', price_per_million_usd: 3.00, source_url: 'https://build.nvidia.com' },
  { provider: 'nim', model: 'meta/llama-3.3-70b-instruct',        token_class: 'input',  price_per_million_usd: 0.90, source_url: 'https://build.nvidia.com' },
  { provider: 'nim', model: 'meta/llama-3.3-70b-instruct',        token_class: 'output', price_per_million_usd: 0.90, source_url: 'https://build.nvidia.com' },
  { provider: 'nim', model: 'nvidia/nemotron-3-super-120b-a12b',  token_class: 'input',  price_per_million_usd: 3.00, source_url: 'https://build.nvidia.com' },
  { provider: 'nim', model: 'nvidia/nemotron-3-super-120b-a12b',  token_class: 'output', price_per_million_usd: 3.00, source_url: 'https://build.nvidia.com' },
]

const DATABASE_URL = process.env.DATABASE_URL ?? process.env.NEXT_PUBLIC_DATABASE_URL
if (!DATABASE_URL) {
  throw new Error(
    'DATABASE_URL (or NEXT_PUBLIC_DATABASE_URL) env var required — see header comment for usage. ' +
      'No hard-coded fallback: SAMAPTI security incident INC-3 found a live `postgres` ' +
      'superuser credential hard-coded here, mislabelled as amjis_app.'
  )
}

const EFFECTIVE_FROM = '2026-05-03T00:00:00Z'

async function main() {
  const pool = new Pool({ connectionString: DATABASE_URL })
  const client = await pool.connect()
  let inserted = 0
  const attempted = PRICING_V1.length

  try {
    for (const row of PRICING_V1) {
      const result = await client.query(
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
    console.log(
      `[observatory_pricing/seed_v1] attempted=${attempted} inserted=${inserted} skipped=${attempted - inserted}`,
    )
  } finally {
    client.release()
    await pool.end()
  }
}

main().catch((err) => {
  console.error('[observatory_pricing/seed_v1] failed:', err)
  process.exit(1)
})
