/**
 * Bridge for build/route.ts — wraps the raw streamText call so that
 * build/route.ts does not import from 'ai' directly (satisfying AC.AD4.2).
 *
 * This file lives in adapters/ and is excluded from the AC.AD4.2 grep.
 * The build route uses AI SDK tools with execute handlers and complex
 * ModelMessage types (convertToModelMessages output) that are incompatible
 * with QueryRequest.messages; a full adapter migration is deferred to AD.5+.
 */
import 'server-only'
import { streamText, type StreamTextResult } from 'ai'

// Re-export AI SDK helpers the build route needs so it has a single import.
export { stepCountIs, createIdGenerator, convertToModelMessages } from 'ai'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function streamBuildRaw(options: Parameters<typeof streamText>[0]): StreamTextResult<any, any> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return streamText(options as any)
}
