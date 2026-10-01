import 'server-only'
import { AsyncLocalStorage } from 'node:async_hooks'
import type { LanguageModelV3 } from '@ai-sdk/provider'
import { meteringEnabled, type MeteringChannel, type MeteringPurpose } from './types'
import { meterModel } from './model'
interface RequestAttribution { userId:string; conversationId:string|null; turnId:string; channel:MeteringChannel;
  purpose:MeteringPurpose; payer:'user'|'platform' }
const requestContext = new AsyncLocalStorage<{ attribution?:RequestAttribution }>()
export const meteringRequest = <T>(work:()=>T): T => requestContext.run({},work)
export function setMeteringAttribution(attribution:RequestAttribution) {
  const store = requestContext.getStore()
  if (store) store.attribution = Object.freeze({ ...attribution })
}
export const currentMeteringAttribution = () => requestContext.getStore()?.attribution
/** Explicit authenticated request attribution is mandatory when the ledger is enabled. */
export function meterSharedModel(model:LanguageModelV3, provider:string, modelId:string, role:string,
  explicit?: { userId?:string; traceId?:string }) {
  if (!meteringEnabled()) return model
  const attribution = currentMeteringAttribution() ?? (explicit?.userId ? { userId:explicit.userId,conversationId:null,
    turnId:explicit.traceId ?? crypto.randomUUID(),channel:'unknown' as const,purpose:'legacy' as const,payer:'platform' as const } : null)
  if (!attribution) throw new Error('Metering attribution required: route backend tests through the metered admin endpoint')
  return meterModel(model,{ ...attribution,operationId:crypto.randomUUID(),provider,model:modelId,role,aggregation:'transport' })
}
