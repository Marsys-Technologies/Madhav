'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport, type FileUIPart, type UIMessage } from 'ai'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

interface Options {
  chartId: string
  conversationId?: string
  initialMessages?: UIMessage[]
  onConversationCreated?: (id: string) => void
  stack?: string
  style?: string
}

export function useChatSession({
  chartId,
  conversationId,
  initialMessages,
  onConversationCreated,
  stack,
  style,
}: Options) {
  const [persistedId, setPersistedId] = useState<string | undefined>(conversationId)
  // queryId for the most recent pipeline query (set as soon as start-part metadata arrives)
  const [currentQueryId, setCurrentQueryId] = useState<string | undefined>(undefined)
  const lastSeenQueryId = useRef<string | undefined>(undefined)

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPersistedId(conversationId)
  }, [conversationId])

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: '/api/chat/consume',
      }),
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
        if (process.env.NODE_ENV === 'development') {
          console.warn(
            '[useChatSession] conversationId transition:',
            persistedId ?? 'new', '→', newId,
            '| chat.status at transition:', chat.status
          )
        }
        setPersistedId(newId)
        onConversationCreated?.(newId)
      }
    },
  })

  // Watch messages in real-time: the 'start' stream part populates assistant message
  // metadata immediately, well before synthesis begins — so queryId is available
  // for TracePanel SSE subscription while the pipeline is still running.
  useEffect(() => {
    const lastAssistant = [...chat.messages].reverse().find(m => m.role === 'assistant')
    const meta = lastAssistant?.metadata as Record<string, unknown> | undefined
    const qid = meta?.queryId as string | undefined
    if (qid && qid !== lastSeenQueryId.current) {
      lastSeenQueryId.current = qid
      setCurrentQueryId(qid)
    }
  }, [chat.messages])

  const isStreaming = chat.status === 'streaming' || chat.status === 'submitted'
  const canSend = chat.status === 'ready' || chat.status === 'error'

  const send = useCallback(
    (text: string, files?: FileUIPart[], extraBody?: Record<string, unknown>) => {
      const trimmed = text.trim()
      const hasFiles = Boolean(files && files.length > 0)
      if ((!trimmed && !hasFiles) || isStreaming) return
      chat.sendMessage(
        hasFiles ? { text: trimmed, files } : { text: trimmed },
        { body: { chartId, conversationId: persistedId, stack, style, ...extraBody } }
      )
    },
    [chat, isStreaming, chartId, persistedId, stack, style]
  )

  const regenerate = useCallback(() => {
    lastSeenQueryId.current = undefined
    setCurrentQueryId(undefined)
    chat.regenerate({ body: { chartId, conversationId: persistedId, stack, style } })
  }, [chat, chartId, persistedId, stack, style])

  const editAndResubmit = useCallback(
    (id: string, newText: string) => {
      const idx = chat.messages.findIndex(m => m.id === id)
      if (idx === -1) return
      const truncated = chat.messages.slice(0, idx)
      chat.setMessages(truncated)
      // Reset queryId so TracePanel clears and waits for the new query's ID
      lastSeenQueryId.current = undefined
      setCurrentQueryId(undefined)
      chat.sendMessage(
        { text: newText },
        { body: { chartId, conversationId: persistedId, stack, style } }
      )
    },
    [chat, chartId, persistedId, stack, style]
  )

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
    editAndResubmit,
    conversationId: persistedId,
    currentQueryId,
  }
}
