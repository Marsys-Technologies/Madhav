import 'server-only'
import type { QueryRequest, ModelInteraction } from './types'
import { streamAdapter } from './stream_adapter'
import { collectInteraction } from './event_collector'
import { runAdapterLegacy } from './legacy_runAdapter'
import { getFlag } from '@/lib/config/index'

export async function runAdapter(req: QueryRequest): Promise<ModelInteraction> {
  if (getFlag('ADAPTERS_ENABLED')) {
    const stream = streamAdapter(req)
    return collectInteraction(stream)
  }
  return runAdapterLegacy(req)
}
