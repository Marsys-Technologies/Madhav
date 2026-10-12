// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyMessage = Record<string, any>

/**
 * Fenced methodology block the synthesis prompt appends to an assistant answer
 * (`METHODOLOGY_INSTRUCTION` in lib/prompts/templates/shared.ts). It is persisted
 * inside the assistant TEXT PART; the markdown renderer draws it as nothing, but
 * the raw text still ships to the browser, so hiding it means removing it from
 * the data, not from the DOM. An unterminated fence (truncated response) runs to
 * the end of the text.
 */
const METHODOLOGY_FENCE_RX = /```[ \t]*marsys_methodology_block[^\n]*\n[\s\S]*?(?:```|(?![\s\S]))/g

/**
 * Legacy "## Methodology" heading section, up to the next `## ` heading or the end
 * of the text. (The previous version ended the lookahead with `\Z`, which a
 * JavaScript RegExp treats as a literal "Z": a methodology section that was the
 * last section of the text was never stripped.)
 */
const METHODOLOGY_HEADING_RX = /^##\s+Methodology\b[\s\S]*?(?=^##\s|(?![\s\S]))/gim

/** Inline reasoning-narration markers (`REASONING_NARRATION_GATE`). */
const REASONING_MARKER_RX = /‹reasoning›[\s\S]*?(?:‹\/reasoning›|(?![\s\S]))/g

function stripText(text: string, hideReasoning: boolean, hideMethodology: boolean): string {
  let out = text
  if (hideMethodology) out = out.replace(METHODOLOGY_FENCE_RX, '').replace(METHODOLOGY_HEADING_RX, '')
  if (hideReasoning) out = out.replace(REASONING_MARKER_RX, '')
  return out === text ? text : out.trimEnd()
}

/**
 * X-S8: Filter assistant UIMessages based on selective share settings.
 *
 * MUST run on the SERVER, before the messages are handed to any client component:
 * a client component receives its props in the RSC payload, so filtering inside it
 * would still deliver the hidden sections to the viewer's browser.
 *
 * - hideReasoning: removes `reasoning` parts and inline ‹reasoning› markers
 * - hideMethodology: removes the `marsys_methodology_block` fence (and a legacy
 *   "## Methodology" section) from assistant text, plus `metadata.methodology_block`
 *
 * User messages are never altered. The input is not mutated.
 */
export function filterMessages(
  messages: AnyMessage[],
  hideReasoning: boolean,
  hideMethodology: boolean,
): AnyMessage[] {
  if (!hideReasoning && !hideMethodology) return messages
  return messages.map((msg) => {
    if (msg.role !== 'assistant') return msg
    const next: AnyMessage = { ...msg }

    if (Array.isArray(msg.parts)) {
      const parts: AnyMessage[] = []
      for (const part of msg.parts as AnyMessage[]) {
        if (hideReasoning && part.type === 'reasoning') continue
        if (part.type === 'text' && typeof part.text === 'string') {
          const text = stripText(part.text, hideReasoning, hideMethodology)
          if (text !== part.text) {
            if (text.trim() === '') continue
            parts.push({ ...part, text })
            continue
          }
        }
        parts.push(part)
      }
      next.parts = parts
    }

    if (typeof msg.content === 'string') {
      next.content = stripText(msg.content, hideReasoning, hideMethodology)
    }

    if (hideMethodology && msg.metadata && typeof msg.metadata === 'object' && 'methodology_block' in msg.metadata) {
      const { methodology_block: _dropped, ...rest } = msg.metadata as Record<string, unknown>
      void _dropped
      next.metadata = rest
    }
    return next
  })
}
