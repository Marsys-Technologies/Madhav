import 'server-only'
import type { QueryRequest, ModelInteraction } from './types'
import { streamAdapter } from './stream_adapter'
import { collectInteraction } from './event_collector'

export async function runAdapter(req: QueryRequest): Promise<ModelInteraction> {
  const stream = streamAdapter(req)
  return collectInteraction(stream)
}
