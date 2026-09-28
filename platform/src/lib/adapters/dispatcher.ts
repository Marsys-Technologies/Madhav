import type { Provider } from '@/lib/models/registry'
import type { ProviderId } from '@/lib/ai-console/types'
import type { Adapter } from './providers/base'
import { adapterAnthropic } from './providers/adapter_anthropic'
import { adapterDeepseek } from './providers/adapter_deepseek'
import { adapterGemini } from './providers/adapter_gemini'
import { adapterOpenai } from './providers/adapter_openai'
import { adapterNim } from './providers/adapter_nim'

export function adapterFor(provider: Provider | ProviderId): Adapter {
  switch (provider) {
    case 'anthropic': return adapterAnthropic
    case 'deepseek':  return adapterDeepseek
    case 'google':    return adapterGemini
    case 'openai':    return adapterOpenai
    case 'xai':
    case 'kimi':
    case 'openrouter': return adapterOpenai
    case 'nvidia':    return adapterNim
    default: {
      const _exhaustive: never = provider
      throw new Error(`Unknown provider: ${String(_exhaustive)}`)
    }
  }
}
