import { filterMessages } from './filterMessages'

/**
 * Share-viewer message shape (SS N-379 item ii).
 *
 * A share viewer receives ONLY the rendered conversation text. This is the whole
 * shape that crosses the server -> client boundary for a share page:
 *
 *  - `id`:   opaque positional key (`m0`, `m1`, ...), never the database id;
 *  - `role`: an opaque DISPLAY value, `'user' | 'assistant'`, derived on the
 *            server. It is never the raw stored role and never an admin flag, so
 *            no admin-only branch of the chat renderer can be reached from it;
 *  - `parts`: text parts (and reasoning text when the sharer chose to show it).
 *
 * Everything else the message loader returns is dropped on the SERVER, before any
 * client-component prop is built: tool-call parts (raw retrieval input/output),
 * `data-*` parts, file/source/step parts, provider metadata and the message
 * `metadata` object (model, style, query_id, `role`, ...).
 */
export type ShareDisplayRole = 'user' | 'assistant'

export interface ShareViewPart {
  type: 'text' | 'reasoning'
  text: string
}

export interface ShareViewMessage {
  id: string
  role: ShareDisplayRole
  parts: ShareViewPart[]
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return v !== null && typeof v === 'object' && !Array.isArray(v)
}

/**
 * Apply the stored hide options, then build a NEW minimal message per remaining
 * message from an allowlist. The loader's message object is never spread or
 * passed through. Messages with no renderable text left (tool-only turns,
 * system/unknown roles) are dropped rather than shipped as empty shells.
 */
export function buildShareViewMessages(
  messages: readonly unknown[],
  hideReasoning: boolean,
  hideMethodology: boolean,
): ShareViewMessage[] {
  const filtered = filterMessages(
    messages.filter(isRecord) as Record<string, unknown>[],
    hideReasoning,
    hideMethodology,
  )

  const out: ShareViewMessage[] = []
  for (const msg of filtered) {
    // Display role from the raw role, never forwarded. Anything that is not a
    // user/assistant turn was never rendered by the chat list, so it is not sent.
    const role: ShareDisplayRole | null =
      msg.role === 'user' ? 'user' : msg.role === 'assistant' ? 'assistant' : null
    if (!role || !Array.isArray(msg.parts)) continue

    const parts: ShareViewPart[] = []
    for (const part of msg.parts as unknown[]) {
      if (!isRecord(part) || typeof part.text !== 'string' || part.text === '') continue
      if (part.type === 'text') {
        parts.push({ type: 'text', text: part.text })
      } else if (part.type === 'reasoning' && role === 'assistant' && !hideReasoning) {
        parts.push({ type: 'reasoning', text: part.text })
      }
    }
    if (parts.length === 0) continue

    out.push({ id: `m${out.length}`, role, parts })
  }
  return out
}
