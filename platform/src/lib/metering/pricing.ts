import type { UsageEvidence } from './types'

export interface RateCard {
  id: string
  provider: string
  model: string
  effectiveFrom: string
  effectiveTo?: string | null
  observedAt: string
  sourceUrl: string
  inputPerMillion: string
  outputPerMillion: string
  cacheReadPerMillion: string | null
  cacheWritePerMillion: string | null
  reasoningPerMillion: string | null
  outputIncludesReasoning: boolean
  maxInputTokens: number | null
  tokenPricingOnly?: boolean
}
export interface ChargeLine { kind: string; quantity: number; ratePerMillion: string; costUsd: string }
export interface PriceResult {
  costUsd: string | null
  rateCardId: string | null
  status: 'priced' | 'usage_unavailable' | 'usage_inconsistent' | 'rate_unavailable' | 'rate_inapplicable' | 'partial_rate'
  lines: ChargeLine[]
}
const SCALE = BigInt(1_000_000_000_000)
export function usdUnits(value: string): bigint {
  if (!/^\d+(\.\d{1,12})?$/.test(value) || value.length > 40) throw new Error('Invalid USD decimal')
  const [whole, fraction = ''] = value.split('.')
  return BigInt(whole) * SCALE + BigInt(fraction.padEnd(12, '0'))
}
export function formatUsd(value: bigint): string {
  return `${value / SCALE}.${(value % SCALE).toString().padStart(12, '0')}`
}

export function priceUsage(usage: UsageEvidence, card: RateCard | null): PriceResult {
  const result: PriceResult = { costUsd: null, rateCardId: card?.id ?? null, status: 'rate_unavailable', lines: [] }
  if (usage.issues.length) return { ...result, status: 'usage_inconsistent' }
  if (usage.input === null || usage.output === null) return { ...result, status: 'usage_unavailable' }
  if (!card) return result
  if (card.tokenPricingOnly === false) return { ...result, status:'rate_inapplicable' }
  if (usage.uncachedInput === null) return { ...result, status:'partial_rate' }
  const inputParts = (usage.uncachedInput ?? 0) + (usage.cacheRead ?? 0) + (usage.cacheWrite ?? 0)
  if (usage.uncachedInput === null || inputParts !== usage.input || (usage.reasoning ?? 0) > usage.output) {
    return { ...result, status: 'usage_inconsistent' }
  }
  if (card.maxInputTokens !== null && usage.input > card.maxInputTokens) return { ...result, status: 'rate_inapplicable' }
  let total = BigInt(0), missing = usage.input > 0 && ((card.cacheReadPerMillion !== null && usage.cacheRead === null)
    || (card.cacheWritePerMillion !== null && usage.cacheWrite === null))
  const line = (kind: string, quantity: number | null, rate: string | null) => {
    if (quantity === 0) return
    if (quantity === null || rate === null) { missing = true; return }
    const units = (BigInt(quantity) * usdUnits(rate) + BigInt(500_000)) / BigInt(1_000_000)
    total += units; result.lines.push({ kind, quantity, ratePerMillion: rate, costUsd: formatUsd(units) })
  }
  line('input', usage.uncachedInput, card.inputPerMillion)
  line('cache_read', usage.cacheRead ?? 0, card.cacheReadPerMillion)
  line('cache_write', usage.cacheWrite ?? 0, card.cacheWritePerMillion)
  if (card.outputIncludesReasoning) line('output', usage.output, card.outputPerMillion)
  else {
    line('output', usage.reasoning === null ? null : usage.output - usage.reasoning, card.outputPerMillion)
    line('reasoning', usage.reasoning, card.reasoningPerMillion)
  }
  if (total >= BigInt('1000000000000000000000000000000')) return { ...result, status:'rate_inapplicable' }
  return { ...result, costUsd: missing ? null : formatUsd(total), status: missing ? 'partial_rate' : 'priced' }
}
