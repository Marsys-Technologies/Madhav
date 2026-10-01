import 'server-only'
import { z } from 'zod'
import { usdUnits,formatUsd, type RateCard } from './pricing'
import { importRateCards,meteringDb,type MeteringDb } from './repository'
const Price = z.string().max(30).regex(/^\d{1,12}(\.\d{1,12})?$/)
const CatalogModel = z.object({ id:z.string().min(1).max(256),
  pricing:z.object({ prompt:Price,completion:Price,input_cache_read:Price.optional(),input_cache_write:Price.optional() }).catchall(z.unknown())
}).passthrough()
const Catalog = z.object({ data:z.array(z.unknown()).max(5000) }).passthrough()
const URL = 'https://openrouter.ai/api/v1/models'
const tokenRate = (value:string) => formatUsd(usdUnits(value)*BigInt(1_000_000))
export function catalogCards(input:unknown,now=new Date()): { cards:RateCard[];skipped:number } {
  const catalog = Catalog.parse(input); const cards:RateCard[]=[]; let skipped=0
  for (const item of catalog.data) {
    // A catalog may contain routers with sentinel prices or rates beyond our
    // exact decimal precision. Keep usable models without inventing a price.
    const parsed=CatalogModel.safeParse(item)
    if (!parsed.success) { skipped++;continue }
    const model=parsed.data
    const p=model.pricing
    const known=new Set(['prompt','completion','input_cache_read','input_cache_write'])
    // Never pretend token-only pricing covers paid requests, tools, modalities or tier modifiers.
    const extraFee=Object.entries(p).some(([key,value])=>!known.has(key) && (typeof value!=='string' || !/^0(\.0+)?$/.test(value)))
    const tokenPricingOnly = !extraFee && !model.id.startsWith('openrouter/')
    if (!tokenPricingOnly) skipped++
    cards.push({ id:crypto.randomUUID(),provider:'openrouter',model:model.id,effectiveFrom:now.toISOString(),observedAt:now.toISOString(),
      sourceUrl:URL,inputPerMillion:tokenRate(p.prompt),outputPerMillion:tokenRate(p.completion),
      cacheReadPerMillion:p.input_cache_read===undefined?null:tokenRate(p.input_cache_read),
      cacheWritePerMillion:p.input_cache_write===undefined?null:tokenRate(p.input_cache_write),
      reasoningPerMillion:null,outputIncludesReasoning:true,maxInputTokens:null,tokenPricingOnly })
  }
  return { cards,skipped }
}
export async function syncOpenRouterCatalog(db:MeteringDb=meteringDb(),fetcher:typeof fetch=fetch) {
  const response=await fetcher(URL,{ signal:AbortSignal.timeout(15000),cache:'no-store',redirect:'error' })
  if (!response.ok || Number(response.headers.get('content-length'))>4_000_000) throw new Error('Catalog unavailable')
  const reader=response.body?.getReader(); if (!reader) throw new Error('Catalog unavailable')
  const parts:Uint8Array[]=[];let bytes=0
  try { while (true) { const chunk=await reader.read();if(chunk.done)break;bytes+=chunk.value.byteLength
    if(bytes>4_000_000)throw new Error('Catalog too large');parts.push(chunk.value) } }
  finally { await reader.cancel() }
  const { cards,skipped }=catalogCards(JSON.parse(Buffer.concat(parts).toString()))
  const { rows }=await db.query<{card:RateCard}>(`SELECT DISTINCT ON(model) card FROM ai_metering_rate_cards
    WHERE provider=$1 AND effective_from<=$2 ORDER BY model,effective_from DESC`,['openrouter',cards[0]?.observedAt??new Date().toISOString()])
  const previousByModel=new Map(rows.map(row=>[row.card.model,row.card]))
  let unchanged=0
  const changed=cards.filter(card=>{
    const previous=previousByModel.get(card.model)
    const fields=['inputPerMillion','outputPerMillion','cacheReadPerMillion','cacheWritePerMillion','reasoningPerMillion','outputIncludesReasoning','maxInputTokens'] as const
    if(previous && fields.every(key=>previous[key]===card[key]) && (previous.tokenPricingOnly??true)===card.tokenPricingOnly) { unchanged++;return false }
    return true
  })
  const imported=await importRateCards(changed,db)
  return { imported,unchanged,skipped,observedAt:cards[0]?.observedAt??new Date().toISOString(),sourceUrl:URL }
}
