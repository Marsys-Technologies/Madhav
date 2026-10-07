// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyMessage = Record<string, any>

/**
 * X-S8: Filter assistant UIMessages based on selective share settings.
 * - hideReasoning: removes parts with type 'reasoning'
 * - hideMethodology: strips ## Methodology sections from text content
 */
export function stripMethodology(text: string): string {
  return text.replace(/^##[ \t]+Methodology\b[^\n]*(?:\n|$)[\s\S]*?(?=^#{1,2}[ \t]+|(?![\s\S]))/gim, '').trim()
}

export function filterMessages(
  messages: AnyMessage[],
  hideReasoning: boolean,
  hideMethodology: boolean,
): AnyMessage[] {
  if (!hideReasoning && !hideMethodology) return messages
  return messages.map((msg) => {
    if (msg.role !== 'assistant') return msg
    let parts = Array.isArray(msg.parts) ? [...msg.parts as AnyMessage[]] : msg.parts
    if (hideReasoning && Array.isArray(parts)) {
      parts = (parts as AnyMessage[]).filter((p) => p.type !== 'reasoning')
    }
    if (hideMethodology && Array.isArray(parts)) {
      parts = parts.map(p => p.type === 'text' && typeof p.text === 'string' ? { ...p, text: stripMethodology(p.text) } : p)
    }
    let content: string | undefined = typeof msg.content === 'string' ? msg.content : undefined
    if (hideMethodology && typeof content === 'string') {
      content = stripMethodology(content)
    }
    return { ...msg, ...(parts !== msg.parts ? { parts } : {}), ...(content !== msg.content ? { content } : {}) }
  })
}
