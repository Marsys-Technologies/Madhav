/**
 * Read a request body up to `maxBytes`, aborting the stream as soon as the cumulative byte
 * count exceeds it — never buffering an unbounded body in full and measuring it afterward
 * (R3 boundary, native ruling "actual certify-request byte limit"). `Content-Length` is only
 * an early-rejection optimization for an HONEST, oversized declaration: it can be omitted
 * entirely, understated, or simply not reflect what a chunked-transfer client actually sends
 * — the limit enforced here is the only one that cannot be bypassed by a malformed or absent
 * header.
 */
export type BoundedBodyResult =
  | { readonly ok: true; readonly text: string }
  | { readonly ok: false; readonly reason: 'too_large' }

export async function readBoundedRequestBody(request: Request, maxBytes: number): Promise<BoundedBodyResult> {
  const body = request.body
  if (!body) return { ok: true, text: '' }
  const reader = body.getReader()
  const chunks: Uint8Array[] = []
  let total = 0
  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      if (!value || value.byteLength === 0) continue
      total += value.byteLength
      if (total > maxBytes) {
        await reader.cancel('request body exceeds the configured limit').catch(() => {})
        return { ok: false, reason: 'too_large' }
      }
      chunks.push(value)
    }
  } finally {
    reader.releaseLock()
  }
  const merged = new Uint8Array(total)
  let offset = 0
  for (const chunk of chunks) {
    merged.set(chunk, offset)
    offset += chunk.byteLength
  }
  return { ok: true, text: new TextDecoder('utf-8').decode(merged) }
}
