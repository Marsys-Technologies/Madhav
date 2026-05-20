'use client'

import type { UIMessage } from 'ai'
import { MessageList } from '@/components/chat/MessageList'
import { filterMessages } from '@/lib/share/filterMessages'

interface Props {
  messages: UIMessage[]
  /** X-S8: when true, filter reasoning/thinking parts from assistant messages */
  hideReasoning?: boolean
  /** X-S8: when true, strip methodology sections from assistant text content */
  hideMethodology?: boolean
}

// Read-only render of a shared conversation. MessageList already renders user +
// assistant messages; passing no handlers disables all interaction.
export function SharedConversation({ messages, hideReasoning = false, hideMethodology = false }: Props) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const filtered = filterMessages(messages as any[], hideReasoning, hideMethodology) as UIMessage[]
  return <MessageList messages={filtered} isStreaming={false} />
}
