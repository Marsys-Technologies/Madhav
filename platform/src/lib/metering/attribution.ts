import type { MeteringContext } from './types'

// The deployed Paripraśna canary authenticates as this fixed principal. Its
// requests exercise the public API, but are operational checks, not customer use.
export const PROBE_USER_ID = 'probe-service-account'

export function classifyMeteringContext(context: MeteringContext): MeteringContext {
  if (context.userId !== PROBE_USER_ID || context.purpose !== 'customer') return context
  return {
    ...context,
    channel: context.channel === 'web' ? 'api' : context.channel,
    purpose: 'validation',
  }
}
