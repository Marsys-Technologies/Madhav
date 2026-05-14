/**
 * Streaming marker buffer — parses an open/close tag pair from a chunked
 * text stream and routes content into two channels: reasoning (inside the
 * markers) and text (outside).
 *
 * Handles tags split across chunk boundaries by holding a lookahead buffer
 * equal to the length of the longest tag minus one character.
 *
 * Usage:
 *   const buf = new MarkerBuffer('<think>', '</think>')
 *   for (const chunk of chunks) {
 *     const { reasoning, text } = buf.feed(chunk)
 *     // emit reasoning_delta / text_delta as appropriate
 *   }
 *   const { reasoning, text, unclosed } = buf.flush()  // end-of-stream
 */
export class MarkerBuffer {
  private state: 'before' | 'inside' | 'after' = 'before'
  private buffer = ''
  private readonly openTag: string
  private readonly closeTag: string

  constructor(openTag = '<think>', closeTag = '</think>') {
    this.openTag = openTag
    this.closeTag = closeTag
  }

  feed(chunk: string): { reasoning?: string; text?: string } {
    this.buffer += chunk
    let reasoning = ''
    let text = ''

    while (this.buffer.length > 0) {
      if (this.state === 'before') {
        const idx = this.buffer.indexOf(this.openTag)
        if (idx !== -1) {
          text += this.buffer.slice(0, idx)
          this.buffer = this.buffer.slice(idx + this.openTag.length)
          this.state = 'inside'
          // continue to process remaining buffer in 'inside' state
        } else {
          const safeLen = longestTagPrefix(this.buffer, this.openTag)
          text += this.buffer.slice(0, this.buffer.length - safeLen)
          this.buffer = this.buffer.slice(this.buffer.length - safeLen)
          break
        }
      } else if (this.state === 'inside') {
        const idx = this.buffer.indexOf(this.closeTag)
        if (idx !== -1) {
          reasoning += this.buffer.slice(0, idx)
          this.buffer = this.buffer.slice(idx + this.closeTag.length)
          this.state = 'after'
          // continue to process remaining buffer in 'after' state
        } else {
          const safeLen = longestTagPrefix(this.buffer, this.closeTag)
          reasoning += this.buffer.slice(0, this.buffer.length - safeLen)
          this.buffer = this.buffer.slice(this.buffer.length - safeLen)
          break
        }
      } else {
        // 'after': all remaining content is plain text
        text += this.buffer
        this.buffer = ''
        break
      }
    }

    return {
      ...(reasoning ? { reasoning } : {}),
      ...(text ? { text } : {}),
    }
  }

  flush(): { reasoning?: string; text?: string; unclosed?: boolean } {
    if (this.buffer.length === 0) return {}
    const remaining = this.buffer
    this.buffer = ''
    if (this.state === 'inside') {
      return { reasoning: remaining, unclosed: true }
    }
    // 'before' or 'after': buffered content is a tag prefix or plain text
    return { text: remaining }
  }

  get currentState(): 'before' | 'inside' | 'after' {
    return this.state
  }
}

/**
 * Returns the length of the longest suffix of `str` that is a strict prefix
 * of `tag` (i.e., length < tag.length so a complete match is excluded).
 * This tells the caller how many chars to hold back to avoid splitting the tag.
 */
function longestTagPrefix(str: string, tag: string): number {
  const maxLen = Math.min(str.length, tag.length - 1)
  for (let len = maxLen; len > 0; len--) {
    if (str.endsWith(tag.slice(0, len))) return len
  }
  return 0
}
