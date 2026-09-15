'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport, type UIMessage } from 'ai'
import { useCallback, useMemo, useState } from 'react'

interface BuildChatOptions {
  chartId: string
  conversationId?: string
  initialMessages?: UIMessage[]
  onConversationCreated?: (id: string) => void
}

export function useBuildChat({
  chartId,
  conversationId,
  initialMessages,
  onConversationCreated,
}: BuildChatOptions) {
  const [generatedId, setGeneratedId] = useState<string | undefined>()
  const persistedId = conversationId ?? generatedId

  const transport = useMemo(
    () => new DefaultChatTransport({ api: '/api/chat/build' }),
    []
  )

  const chat = useChat({
    id: conversationId ?? 'new',
    messages: initialMessages,
    transport,
    onFinish: ({ message }) => {
      const metadata = message.metadata as { conversationId?: string } | undefined
      const newId = metadata?.conversationId
      if (newId && newId !== persistedId) {
        setGeneratedId(newId)
        onConversationCreated?.(newId)
      }
    },
  })

  const isStreaming = chat.status === 'streaming' || chat.status === 'submitted'
  const canSend = chat.status === 'ready' || chat.status === 'error'

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || isStreaming) return
      chat.sendMessage(
        { text: trimmed },
        { body: { chartId, conversationId: persistedId } }
      )
    },
    [chat, isStreaming, chartId, persistedId]
  )

  const regenerate = useCallback(() => {
    chat.regenerate({ body: { chartId, conversationId: persistedId } })
  }, [chat, chartId, persistedId])

  return {
    messages: chat.messages,
    status: chat.status,
    error: chat.error,
    isStreaming,
    canSend,
    send,
    stop: chat.stop,
    regenerate,
    setMessages: chat.setMessages,
    conversationId: persistedId,
  }
}
