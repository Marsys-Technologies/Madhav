'use client'

import { MessageList } from '@/components/chat/MessageList'
import type { ShareViewMessage } from '@/lib/share/shareView'

interface Props {
  /**
   * Already reduced by the server page (SS N-379): text parts only, an opaque
   * display role (`user` | `assistant`), positional ids; the selective-share hide
   * options (X-S8) are already applied. This component deliberately does NOT
   * filter: it is a client component, so whatever it receives has already been
   * delivered to the browser in the RSC payload.
   */
  messages: ShareViewMessage[]
}

// Read-only render of a shared conversation. MessageList already renders user +
// assistant messages; passing no handlers disables all interaction. The messages
// carry no `metadata`, so the renderer's admin-only branches (trace flow) cannot
// be reached from a share page.
export function SharedConversation({ messages }: Props) {
  return <MessageList messages={messages} isStreaming={false} />
}
