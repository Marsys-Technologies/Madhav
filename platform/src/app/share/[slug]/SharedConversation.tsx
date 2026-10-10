'use client'

import type { UIMessage } from 'ai'
import { MessageList } from '@/components/chat/MessageList'

interface Props {
  /**
   * Already filtered by the server page (selective share, X-S8). This component
   * deliberately does NOT filter: it is a client component, so whatever it
   * receives has already been delivered to the browser in the RSC payload.
   */
  messages: UIMessage[]
}

// Read-only render of a shared conversation. MessageList already renders user +
// assistant messages; passing no handlers disables all interaction.
export function SharedConversation({ messages }: Props) {
  return <MessageList messages={messages} isStreaming={false} />
}
