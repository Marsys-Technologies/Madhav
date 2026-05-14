import type {
  ModelInteractionEvent,
  ModelInteraction,
  IntermediateEvent,
} from './types'

export async function collectInteraction(
  stream: ReadableStream<ModelInteractionEvent>,
): Promise<ModelInteraction> {
  const reader = stream.getReader()
  let reasoningText = ''
  const reasoningTokens = 0
  let finalText: string | undefined
  const finalStructured: unknown = undefined
  const intermediate: IntermediateEvent[] = []
  let finishedInteraction: ModelInteraction | undefined

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    switch (value.type) {
      case 'reasoning_delta':
        reasoningText += value.text
        break
      case 'text_delta':
        finalText = (finalText ?? '') + value.text
        break
      case 'tool_call':
      case 'tool_result':
      case 'status':
        intermediate.push({ type: value.type as IntermediateEvent['type'], ts: value.ts, payload: value })
        break
      case 'finish':
        finishedInteraction = value.interaction
        break
      case 'error':
        throw new Error(value.error.message)
    }
  }

  if (!finishedInteraction) {
    throw new Error('collectInteraction: stream ended without finish event')
  }

  // Merge collected text/reasoning with the finish event's interaction.
  // Adapters are expected to populate everything in the finish event;
  // we merge here for resilience in case delta events arrive without
  // being reflected in the finish event's snapshot.
  return {
    ...finishedInteraction,
    reasoning: reasoningText
      ? { text: reasoningText, tokens: reasoningTokens }
      : finishedInteraction.reasoning,
    intermediate,
    finalText: finalText ?? finishedInteraction.finalText,
    finalStructured: finalStructured ?? finishedInteraction.finalStructured,
  }
}
