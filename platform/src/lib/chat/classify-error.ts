export type ChatErrorKind =
  | 'network'
  | 'timeout'
  | 'rate_limit'
  | 'auth'
  | 'model_overload'
  | 'insufficient_credits'
  | 'unknown'

export interface ClassifiedChatError {
  kind: ChatErrorKind
  title: string
  hint: string
  detail?: string
}

/**
 * Classify an AI SDK / fetch error into a user-facing shape. The AI SDK surfaces
 * errors as plain `Error`s; we pattern-match on the message text since the SDK
 * does not expose a typed error hierarchy here.
 */
export function classifyChatError(err: Error | null | undefined): ClassifiedChatError | null {
  if (!err) return null
  const msg = (err.message ?? '').toLowerCase()

  if (
    msg.includes('credit balance is too low') ||
    msg.includes('insufficient credit') ||
    msg.includes('billing') ||
    msg.includes('insufficient_quota') ||
    msg.includes('quota exceeded')
  ) {
    return {
      kind: 'insufficient_credits',
      title: 'Provider account out of credits',
      hint:
        'The selected provider (Anthropic / Google / DeepSeek) has exhausted its balance. ' +
        'Top up the account, or switch to a different provider in the model picker.',
      detail: err.message,
    }
  }
  if (msg.includes('429') || msg.includes('rate limit') || msg.includes('rate_limit')) {
    return {
      kind: 'rate_limit',
      title: 'Rate limit reached',
      hint: 'You are sending messages faster than the model can respond. Wait a moment and try again.',
      detail: err.message,
    }
  }
  if (msg.includes('401') || msg.includes('unauthorized') || msg.includes('forbidden') || msg.includes('403')) {
    return {
      kind: 'auth',
      title: 'Not authorised',
      hint: 'Your session may have expired. Sign in again to continue.',
      detail: err.message,
    }
  }
  if (msg.includes('529') || msg.includes('overloaded') || msg.includes('model_overloaded')) {
    return {
      kind: 'model_overload',
      title: 'Model is overloaded',
      hint: 'The upstream model is temporarily busy. Retrying usually works within a few seconds.',
      detail: err.message,
    }
  }
  if (msg.includes('timeout') || msg.includes('aborted due to timeout')) {
    return {
      kind: 'timeout',
      title: 'Model response timed out',
      hint: 'The NIM model queue was too busy to respond in time. Try again, or switch to a different stack (Anthropic, Gemini, or GPT).',
      detail: err.message,
    }
  }
  if (
    msg.includes('failed to fetch') ||
    msg.includes('network') ||
    msg.includes('econnreset') ||
    msg.includes('enotfound')
  ) {
    return {
      kind: 'network',
      title: 'Network error',
      hint: 'Check your connection and retry.',
      detail: err.message,
    }
  }
  if (msg.includes('api key is missing') || msg.includes('api key must be') || msg.includes('environment variable')) {
    return {
      kind: 'auth',
      title: 'Model API key not configured',
      hint: 'The selected model\'s API key is missing from the server environment. Switch to a different model in the picker.',
      detail: err.message,
    }
  }
  return {
    kind: 'unknown',
    title: 'Something went wrong',
    hint: 'Retry the request. If it keeps happening, try a different model.',
    detail: err.message,
  }
}
