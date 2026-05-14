import type { Provider } from '@/lib/models/registry'
import type { Adapter } from './providers/base'
import { adapterAnthropic } from './providers/adapter_anthropic'
import { adapterDeepseek } from './providers/adapter_deepseek'
import { adapterGemini } from './providers/adapter_gemini'
import { adapterOpenai } from './providers/adapter_openai'
import { adapterNim } from './providers/adapter_nim'

export function adapterFor(provider: Provider): Adapter {
  switch (provider) {
    case 'anthropic': return adapterAnthropic
    case 'deepseek':  return adapterDeepseek
    case 'google':    return adapterGemini
    case 'openai':    return adapterOpenai
    case 'nvidia':    return adapterNim
    default: {
      const _exhaustive: never = provider
      throw new Error(`Unknown provider: ${String(_exhaustive)}`)
    }
  }
}
