'use client'

/**
 * ConsumeChatV2 — assistant-ui shell for MARSYS chat.
 *
 * β2: conversation list sidebar + write-through restore on mount.
 * Flag gate: only rendered when MARSYS_FLAG_CHAT_V2_ENABLED=true.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { AssistantRuntimeProvider } from '@assistant-ui/react'
import { useChatRuntime } from '@assistant-ui/react-ai-sdk'
import { DefaultChatTransport } from 'ai'
import type { UIMessage } from 'ai'
import {
  ThreadPrimitive,
  MessagePrimitive,
  ComposerPrimitive,
  ActionBarPrimitive,
  BranchPickerPrimitive,
  useThreadRuntime,
} from '@assistant-ui/react'
import type { ConsumeChatProps } from './ConsumeChatLegacy'

// ─── Types ────────────────────────────────────────────────────────────────────

interface ConversationSummary {
  id: string
  title: string | null
  created_at: string
  updated_at: string | null
  archived_at: string | null
}

// ─── Conversation sidebar ─────────────────────────────────────────────────────

interface ConversationSidebarProps {
  chartId: string
  activeId: string | null
  onSelect: (id: string) => void
  onNew: () => void
  collapsed: boolean
  onToggle: () => void
}

function ConversationSidebar({
  chartId,
  activeId,
  onSelect,
  onNew,
  collapsed,
  onToggle,
}: ConversationSidebarProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loading, setLoading] = useState(false)

  const reload = useCallback(() => {
    setLoading(true)
    fetch(`/api/conversations?chartId=${encodeURIComponent(chartId)}&module=consume`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data?.conversations)) {
          setConversations(data.conversations as ConversationSummary[])
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [chartId])

  useEffect(() => {
    reload()
  }, [reload])

  if (collapsed) {
    return (
      <div className="flex flex-col items-center w-10 border-r border-zinc-800 bg-zinc-950 shrink-0">
        <button
          type="button"
          onClick={onToggle}
          title="Expand conversation list"
          className="mt-3 flex h-8 w-8 items-center justify-center rounded-md text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
          data-testid="v2-sidebar-expand"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4">
            <path d="M2 4h12M2 8h7M2 12h9" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    )
  }

  return (
    <aside
      className="flex flex-col w-56 shrink-0 border-r border-zinc-800 bg-zinc-950"
      data-testid="v2-conversation-sidebar"
    >
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800">
        <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">Conversations</span>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={onNew}
            title="New conversation"
            className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            data-testid="v2-new-conversation"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
              <path d="M8 2v12M2 8h12" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" />
            </svg>
          </button>
          <button
            type="button"
            onClick={onToggle}
            title="Collapse"
            className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            data-testid="v2-sidebar-collapse"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
              <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-1">
        {loading && conversations.length === 0 && (
          <p className="px-3 py-2 text-xs text-zinc-500">Loading…</p>
        )}
        {conversations.map((conv) => (
          <button
            key={conv.id}
            type="button"
            onClick={() => onSelect(conv.id)}
            className={`w-full text-left px-3 py-2 text-xs rounded-md transition-colors truncate ${
              conv.id === activeId
                ? 'bg-indigo-600/20 text-indigo-300'
                : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
            }`}
            data-testid={`v2-conversation-item-${conv.id}`}
          >
            {conv.title ?? 'Untitled'}
          </button>
        ))}
        {!loading && conversations.length === 0 && (
          <p className="px-3 py-4 text-xs text-zinc-600 text-center">No conversations yet</p>
        )}
      </div>
    </aside>
  )
}

// ─── Branch picker (inline navigation between alternates) ────────────────────

function V2BranchPicker() {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className="flex items-center gap-1 text-xs text-zinc-500"
      data-testid="v2-branch-picker"
    >
      <BranchPickerPrimitive.Previous asChild>
        <button
          type="button"
          className="h-5 w-5 flex items-center justify-center rounded hover:bg-zinc-800 hover:text-zinc-300 transition-colors disabled:opacity-30"
          title="Previous branch"
          data-testid="v2-branch-prev"
        >
          ‹
        </button>
      </BranchPickerPrimitive.Previous>
      <span>
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <button
          type="button"
          className="h-5 w-5 flex items-center justify-center rounded hover:bg-zinc-800 hover:text-zinc-300 transition-colors disabled:opacity-30"
          title="Next branch"
          data-testid="v2-branch-next"
        >
          ›
        </button>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  )
}

// ─── Message ─────────────────────────────────────────────────────────────────

function V2Message() {
  return (
    <MessagePrimitive.Root
      className="group flex w-full max-w-3xl mx-auto flex-col gap-1 px-4 py-3"
      data-testid="v2-message"
    >
      <MessagePrimitive.If user>
        <div className="flex flex-col items-end gap-1">
          <div
            className="rounded-2xl bg-indigo-600 px-4 py-2.5 text-sm text-white max-w-[70%]"
            data-testid="v2-user-message"
          >
            {/* F.2: flat props — renderer receives {text,...} directly, not a nested part object */}
            <MessagePrimitive.Parts components={{ Text: (props) => <span>{props.text}</span> }} />
          </div>

          {/* Edit action + branch picker for user messages */}
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <V2BranchPicker />
            <ActionBarPrimitive.Root
              hideWhenRunning
              autohide="not-last"
              className="flex gap-1"
              data-testid="v2-user-action-bar"
            >
              <ActionBarPrimitive.Edit asChild>
                <button
                  type="button"
                  className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                  title="Edit message"
                  data-testid="v2-edit-btn"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3 w-3">
                    <path d="M11.5 2.5a1.414 1.414 0 0 1 2 2L5 13H2v-3L11.5 2.5z" />
                  </svg>
                </button>
              </ActionBarPrimitive.Edit>
            </ActionBarPrimitive.Root>
          </div>
        </div>
      </MessagePrimitive.If>

      <MessagePrimitive.If assistant>
        <div className="flex flex-col gap-2 w-full" data-testid="v2-assistant-message">
          <MessagePrimitive.Parts
            components={{
              // F.2: props.text for reasoning (not props.reasoning)
              Reasoning: (props) => (
                <div className="rounded-lg border border-zinc-700 bg-zinc-900/60 px-4 py-2 text-xs font-mono text-zinc-400 whitespace-pre-wrap">
                  {props.text}
                </div>
              ),
              Text: (props) => (
                <p
                  className="whitespace-pre-wrap font-sans text-sm text-zinc-200 leading-relaxed"
                  data-testid="v2-message-text"
                >
                  {props.text}
                </p>
              ),
            }}
          />

          {/* Reload (regenerate) action + branch picker for assistant messages */}
          <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <V2BranchPicker />
            <ActionBarPrimitive.Root
              hideWhenRunning
              autohide="not-last"
              className="flex gap-1"
              data-testid="v2-assistant-action-bar"
            >
              <ActionBarPrimitive.Reload asChild>
                <button
                  type="button"
                  className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                  title="Regenerate response"
                  data-testid="v2-regenerate-btn"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-3 w-3">
                    <path d="M13.5 4A6 6 0 1 0 14 9" strokeLinecap="round" />
                    <path d="M11 1l2.5 3L11 7" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </ActionBarPrimitive.Reload>
              <ActionBarPrimitive.Copy asChild>
                <button
                  type="button"
                  className="flex h-6 w-6 items-center justify-center rounded text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                  title="Copy response"
                  data-testid="v2-copy-btn"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3 w-3">
                    <rect x="5" y="5" width="8" height="9" rx="1" />
                    <path d="M3 2h7a1 1 0 0 1 1 1v1H3V2z" />
                  </svg>
                </button>
              </ActionBarPrimitive.Copy>
            </ActionBarPrimitive.Root>
          </div>
        </div>
      </MessagePrimitive.If>
    </MessagePrimitive.Root>
  )
}

// ─── Composer ─────────────────────────────────────────────────────────────────

function V2Composer() {
  // F.3: useThreadRuntime().subscribe() for run-state (deprecated primitive avoided)
  const runtime = useThreadRuntime()
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    const unsub = runtime.subscribe(() => {
      setIsRunning(runtime.getState().isRunning)
    })
    return unsub
  }, [runtime])

  return (
    <ComposerPrimitive.Root
      className="border-t border-zinc-800 bg-zinc-950 px-4 py-3"
      data-testid="v2-composer"
    >
      <div className="mx-auto max-w-3xl flex items-end gap-3">
        <ComposerPrimitive.Input
          className="flex-1 resize-none rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-colors"
          placeholder="Ask about the chart…"
          rows={3}
          data-testid="v2-composer-input"
        />
        <div className="flex flex-col gap-2 pb-0.5">
          {isRunning ? (
            <ComposerPrimitive.Cancel asChild>
              <button
                type="button"
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-700 text-zinc-300 hover:bg-zinc-600 transition-colors"
                title="Stop generation"
                data-testid="v2-abort-btn"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4">
                  <rect x="4" y="4" width="8" height="8" rx="1" />
                </svg>
              </button>
            </ComposerPrimitive.Cancel>
          ) : (
            <ComposerPrimitive.Send asChild>
              <button
                type="submit"
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-40 transition-colors"
                data-testid="v2-send-btn"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4">
                  <path d="M8 1L15 8L8 15M15 8H1" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </ComposerPrimitive.Send>
          )}
        </div>
      </div>
    </ComposerPrimitive.Root>
  )
}

// ─── Thread ───────────────────────────────────────────────────────────────────

function V2Thread() {
  return (
    <ThreadPrimitive.Root
      className="flex h-full flex-col"
      data-testid="v2-thread-root"
    >
      <ThreadPrimitive.Viewport
        className="flex-1 overflow-y-auto scroll-smooth py-4"
        data-testid="v2-thread-viewport"
      >
        <ThreadPrimitive.Empty>
          <div
            className="flex h-full flex-col items-center justify-center gap-3 text-center px-4 py-16"
            data-testid="v2-thread-empty"
          >
            <p className="text-sm font-medium text-zinc-200">Ready</p>
            <p className="text-xs text-zinc-500">Chat V2 — assistant-ui</p>
          </div>
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages components={{ Message: V2Message }} />

        <ThreadPrimitive.ScrollToBottom asChild>
          <button
            type="button"
            className="fixed bottom-24 right-6 flex h-8 w-8 items-center justify-center rounded-full bg-zinc-700 text-zinc-300 shadow-lg hover:bg-zinc-600 transition-all opacity-80 hover:opacity-100"
            data-testid="v2-scroll-to-bottom"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-4 w-4">
              <path d="M8 12L2 6h12l-6 6z" />
            </svg>
          </button>
        </ThreadPrimitive.ScrollToBottom>
      </ThreadPrimitive.Viewport>

      <V2Composer />
    </ThreadPrimitive.Root>
  )
}

// ─── ConsumeChatV2 ────────────────────────────────────────────────────────────

/**
 * β2: Thread with conversation list sidebar + write-through restore on mount.
 * Accepts the same props as ConsumeChatLegacy for API compatibility.
 */
export function ConsumeChatV2({ chartId, chartName, chartMeta }: ConsumeChatProps) {
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [initialMessages, setInitialMessages] = useState<UIMessage[] | undefined>(undefined)
  const [restoredKey, setRestoredKey] = useState(0)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const chartIdRef = useRef(chartId)
  chartIdRef.current = chartId

  // Restore conversation messages on conversation switch.
  const handleSelectConversation = useCallback(async (id: string) => {
    setActiveConversationId(id)
    try {
      const r = await fetch(`/api/conversations/${id}/messages`)
      if (r.ok) {
        const data = await r.json() as { messages: UIMessage[] }
        setInitialMessages(data.messages ?? [])
      } else {
        setInitialMessages([])
      }
    } catch {
      setInitialMessages([])
    }
    // Increment key to remount the runtime with restored messages.
    setRestoredKey((k) => k + 1)
  }, [])

  const handleNewConversation = useCallback(() => {
    setActiveConversationId(null)
    setInitialMessages(undefined)
    setRestoredKey((k) => k + 1)
  }, [])

  return (
    <div
      className="flex h-screen bg-zinc-950 text-zinc-100"
      data-testid="consume-chat-v2-root"
    >
      <ConversationSidebar
        chartId={chartId}
        activeId={activeConversationId}
        onSelect={handleSelectConversation}
        onNew={handleNewConversation}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((c) => !c)}
      />

      <div className="flex flex-col flex-1 overflow-hidden">
        <header
          className="flex items-center gap-3 border-b border-zinc-800 px-6 py-3 shrink-0"
          data-testid="v2-header"
        >
          <span className="text-xs font-mono text-violet-400 bg-violet-400/10 px-2 py-0.5 rounded border border-violet-400/20">
            V2
          </span>
          <h1 className="text-sm font-semibold text-zinc-100" data-testid="v2-chart-name">
            {chartName}
          </h1>
          {chartMeta && (
            <span className="text-xs text-zinc-500" data-testid="v2-chart-meta">
              {chartMeta}
            </span>
          )}
        </header>

        <main className="flex-1 overflow-hidden">
          <V2ChatRuntime
            key={restoredKey}
            chartId={chartId}
            conversationId={activeConversationId}
            initialMessages={initialMessages}
          />
        </main>
      </div>
    </div>
  )
}

// ─── Runtime mount (isolated so key reset remounts cleanly) ──────────────────

interface V2ChatRuntimeProps {
  chartId: string
  conversationId: string | null
  initialMessages: UIMessage[] | undefined
}

function V2ChatRuntime({ chartId, conversationId, initialMessages }: V2ChatRuntimeProps) {
  const chartIdRef = useRef(chartId)
  chartIdRef.current = chartId
  const conversationIdRef = useRef(conversationId)
  conversationIdRef.current = conversationId

  const runtime = useChatRuntime({
    transport: new DefaultChatTransport({
      api: '/api/chat/consume',
      body: () => ({
        chartId: chartIdRef.current,
        ...(conversationIdRef.current ? { conversationId: conversationIdRef.current } : {}),
      }),
    }),
    messages: initialMessages,
  })

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <V2Thread />
    </AssistantRuntimeProvider>
  )
}
