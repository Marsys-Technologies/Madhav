/**
 * adapters/shared/result_clipper.ts
 *
 * Clips tool results to result_max_kb before returning to LLM.
 * Prevents context overflows from large retrieval results.
 *
 * L0FR Stream A — authored 2026-06-07
 */

export interface ClipOptions {
  /** Maximum result size in KB (default: 32KB) */
  max_kb: number
  /** Strategy: 'truncate_end' | 'truncate_middle' | 'summarize_stub' */
  strategy?: 'truncate_end' | 'truncate_middle' | 'summarize_stub'
}

const DEFAULT_MAX_KB = 32

/**
 * Clip a string result to max_kb.
 * Returns the clipped string, always valid UTF-8.
 */
export function clipString(
  text: string,
  opts: ClipOptions = { max_kb: DEFAULT_MAX_KB, strategy: 'truncate_end' }
): string {
  const maxBytes = (opts.max_kb ?? DEFAULT_MAX_KB) * 1024
  const encoder = new TextEncoder()
  const bytes = encoder.encode(text)

  if (bytes.length <= maxBytes) return text

  const strategy = opts.strategy ?? 'truncate_end'
  const marker = `\n\n[RESULT CLIPPED — exceeded ${opts.max_kb}KB limit]\n`
  const markerBytes = encoder.encode(marker).length
  const targetBytes = maxBytes - markerBytes

  if (strategy === 'truncate_end') {
    const clipped = bytes.slice(0, targetBytes)
    const decoder = new TextDecoder('utf-8', { fatal: false })
    return decoder.decode(clipped) + marker
  }

  if (strategy === 'truncate_middle') {
    const halfBytes = Math.floor(targetBytes / 2)
    const decoder = new TextDecoder('utf-8', { fatal: false })
    const head = decoder.decode(bytes.slice(0, halfBytes))
    const tail = decoder.decode(bytes.slice(bytes.length - halfBytes))
    return head + '\n\n[... MIDDLE CLIPPED ...]\n\n' + tail
  }

  // summarize_stub: return just the first 500 chars + metadata
  const decoder = new TextDecoder('utf-8', { fatal: false })
  const preview = decoder.decode(bytes.slice(0, Math.min(500, targetBytes)))
  return preview + marker
}

/**
 * Clip any result (object or string) to max_kb.
 * Objects are serialized to JSON first.
 */
export function clipResult(
  result: unknown,
  opts: ClipOptions = { max_kb: DEFAULT_MAX_KB }
): string {
  const serialized = typeof result === 'string' ? result : JSON.stringify(result, null, 2)
  return clipString(serialized, opts)
}

/**
 * Check if a result exceeds the max_kb limit without clipping it.
 */
export function exceedsLimit(result: unknown, max_kb: number = DEFAULT_MAX_KB): boolean {
  const serialized = typeof result === 'string' ? result : JSON.stringify(result)
  const bytes = new TextEncoder().encode(serialized).length
  return bytes > max_kb * 1024
}
