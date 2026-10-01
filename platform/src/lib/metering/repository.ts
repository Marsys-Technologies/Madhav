import 'server-only'
import { AttemptStartSchema, AttemptReceiptSchema } from './schema'
import { z } from 'zod'
import { getStorageClient } from '@/lib/storage'
import type { AttemptStart, AttemptReceipt } from './types'
import { priceUsage, type RateCard } from './pricing'

export interface MeteringDb {
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[]; rowCount?: number }>
}
export const meteringDb = (): MeteringDb => getStorageClient()
const Decimal = z.string().max(40).regex(/^\d{1,12}(\.\d{1,12})?$/)
export const RateCardSchema = z.object({
  id: z.string().uuid(), provider: z.string().min(1).max(64), model: z.string().min(1).max(256),
  effectiveFrom: z.string().datetime({ offset: true }), effectiveTo: z.string().datetime({ offset: true }).nullish(),
  observedAt: z.string().datetime({ offset: true }), sourceUrl: z.string().url().max(1024),
  inputPerMillion: Decimal, outputPerMillion: Decimal,
  cacheReadPerMillion: Decimal.nullable(), cacheWritePerMillion: Decimal.nullable(), reasoningPerMillion: Decimal.nullable(),
  tokenPricingOnly: z.boolean().default(true), outputIncludesReasoning: z.boolean(), maxInputTokens: z.number().int().nonnegative().nullable(),
}).strict()
const SOURCE_HOSTS = new Set(['openai.com','platform.openai.com','developers.openai.com','platform.claude.com',
  'docs.anthropic.com','ai.google.dev','cloud.google.com','openrouter.ai','api-docs.deepseek.com',
  'docs.x.ai','platform.moonshot.ai','docs.nvidia.com','build.nvidia.com'])

export function validateRateCard(input: unknown): RateCard {
  const card = RateCardSchema.parse(input)
  const source = new URL(card.sourceUrl)
  if (source.protocol !== 'https:' || source.username || source.password || source.port || source.search || source.hash
    || !SOURCE_HOSTS.has(source.hostname)) throw new Error('Use an official pricing source URL')
  if (card.effectiveTo || card.maxInputTokens !== null) {
    throw new Error('Context-tier and interval cards require a dedicated pricing adapter')
  }
  return card
}

export async function importRateCard(input: unknown, db: MeteringDb = meteringDb()): Promise<RateCard> {
  const card = validateRateCard(input)
  await db.query(`INSERT INTO ai_metering_rate_cards(id,provider,model,effective_from,observed_at,source_url,card)
    VALUES($1,$2,$3,$4,$5,$6,$7)`, [card.id,card.provider,card.model,card.effectiveFrom,card.observedAt,card.sourceUrl,JSON.stringify(card)])
  return card
}

/** Validate the entire catalog before one bounded, atomic append. */
export async function importRateCards(inputs: unknown[], db: MeteringDb = meteringDb()): Promise<number> {
  if (inputs.length > 5000) throw new Error('Too many rate cards')
  const cards = inputs.map(validateRateCard)
  if (!cards.length) return 0
  const { rows } = await db.query(`INSERT INTO ai_metering_rate_cards(id,provider,model,effective_from,observed_at,source_url,card)
    SELECT (card->>'id')::uuid,card->>'provider',card->>'model',(card->>'effectiveFrom')::timestamptz,
      (card->>'observedAt')::timestamptz,card->>'sourceUrl',card FROM jsonb_array_elements($1::jsonb) AS entry(card)
    ON CONFLICT(provider,model,effective_from) DO NOTHING RETURNING id`, [JSON.stringify(cards)])
  return rows.length
}

export async function insertAttempt(start: AttemptStart, db: MeteringDb = meteringDb()): Promise<void> {
  start = AttemptStartSchema.parse(start)
  const inserted = await db.query(`INSERT INTO ai_metering_attempts(attempt_id,user_id,conversation_id,turn_id,operation_id,
    parent_operation_id,channel,purpose,payer,provider,model,role,connection_id,snapshot_id,test_run_id,
    requested_model,aggregation,started_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)
    ON CONFLICT(attempt_id) DO NOTHING`, [start.attemptId,start.userId,start.conversationId,start.turnId,start.operationId,
    start.parentOperationId ?? null,start.channel,start.purpose,start.payer,start.provider,start.model,start.role,
    start.connectionId ?? null,start.snapshotId ?? null,start.testRunId ?? null,start.requestedModel ?? null,
    start.aggregation,start.startedAt])
  if (inserted.rowCount === 0) {
    const { rows } = await db.query(`SELECT attempt_id FROM ai_metering_attempts WHERE attempt_id=$1
      AND user_id=$2 AND conversation_id IS NOT DISTINCT FROM $3 AND turn_id=$4 AND operation_id=$5
      AND parent_operation_id IS NOT DISTINCT FROM $6 AND channel=$7 AND purpose=$8 AND payer=$9
      AND provider=$10 AND model=$11 AND role=$12 AND connection_id IS NOT DISTINCT FROM $13
      AND snapshot_id IS NOT DISTINCT FROM $14 AND test_run_id IS NOT DISTINCT FROM $15
      AND requested_model IS NOT DISTINCT FROM $16 AND aggregation=$17 AND started_at=$18::timestamptz`,
      [start.attemptId,start.userId,start.conversationId,start.turnId,start.operationId,start.parentOperationId??null,
        start.channel,start.purpose,start.payer,start.provider,start.model,start.role,start.connectionId??null,
        start.snapshotId??null,start.testRunId??null,start.requestedModel??null,start.aggregation,start.startedAt])
    if (!rows.length) throw new Error('Conflicting attempt evidence')
  }
}

async function rateFor(start: AttemptStart, db: MeteringDb): Promise<RateCard | null> {
  const { rows } = await db.query<{ card: RateCard }>(`SELECT card FROM ai_metering_rate_cards
    WHERE provider=$1 AND model=$2 AND effective_from <= $3 ORDER BY effective_from DESC LIMIT 1`,
  [start.provider,start.model,start.startedAt])
  if (rows[0]) return RateCardSchema.parse(rows[0].card)
  // Existing versioned prices are retained as source evidence, never silently upgraded to fresh rates.
  const old = await db.query<{ pricing_version_id: string; token_class: string; price_per_million_usd: string; effective_from: string }>(
    `SELECT pricing_version_id,token_class,price_per_million_usd::text,effective_from
     FROM llm_pricing_versions WHERE provider=$1 AND model=$2 AND effective_from <= $3
     AND (effective_to IS NULL OR effective_to > $3)`, [start.provider === 'google' ? 'gemini' : start.provider,start.model,start.startedAt])
  const byClass = new Map(old.rows.map(row => [row.token_class,row]))
  if (old.rows.length !== byClass.size || !byClass.has('input') || !byClass.has('output')) return null
  const first = byClass.get('input')!
  return { id: first.pricing_version_id, provider: start.provider, model: start.model,
    effectiveFrom: new Date(first.effective_from).toISOString(), observedAt: new Date(first.effective_from).toISOString(),
    sourceUrl: 'legacy:llm_pricing_versions', inputPerMillion: first.price_per_million_usd,
    outputPerMillion: byClass.get('output')!.price_per_million_usd,
    cacheReadPerMillion: byClass.get('cache_read')?.price_per_million_usd ?? null,
    cacheWritePerMillion: byClass.get('cache_write')?.price_per_million_usd ?? null,
    reasoningPerMillion: byClass.get('reasoning')?.price_per_million_usd ?? null,
    outputIncludesReasoning: true, maxInputTokens: null }
}

export async function insertReceipt(start: AttemptStart, receipt: AttemptReceipt, db: MeteringDb = meteringDb()): Promise<void> {
  start = AttemptStartSchema.parse(start)
  receipt = AttemptReceiptSchema.parse(receipt)
  if (receipt.attemptId !== start.attemptId) throw new Error('Attempt identity mismatch')
  let card: RateCard | null = null
  // Unsupported pricing must never erase provider usage. Database failures still fail the INSERT below.
  if (start.payer !== 'subscription') {
    try { card = await rateFor(start, db) } catch { /* Retain unpriced evidence. */ }
  }
  const price = priceUsage(receipt.usage, card)
  await db.query(`INSERT INTO ai_metering_receipts(attempt_id,finished_at,status,usage,provider_request_id,
    finish_reason,first_token_at,provider_cost_usd,computed_cost_usd,pricing_status,pricing_snapshot)
    VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11) ON CONFLICT(attempt_id) DO NOTHING`,
  [receipt.attemptId,receipt.finishedAt,receipt.status,JSON.stringify(receipt.usage),receipt.providerRequestId,
    receipt.finishReason,receipt.firstTokenAt,receipt.providerCostUsd,price.costUsd,price.status,JSON.stringify({ card, ...price })])
}
