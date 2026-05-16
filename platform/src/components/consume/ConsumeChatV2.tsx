'use client'

/**
 * ConsumeChatV2 — assistant-ui shell for MARSYS chat.
 *
 * α7 scaffold: minimal Thread mount against /api/chat/consume.
 * All MARSYS chrome (reasoning, citations, panel, metadata, etc.) is wired in β phase.
 *
 * Flag gate: only rendered when MARSYS_FLAG_CHAT_V2_ENABLED=true.
 * Flag-off preserves ConsumeChatLegacy byte-for-byte.
 */

import { useEffect, useRef, useState } from 'react'
import { AssistantRuntimeProvider } from '@assistant-ui/react'
import { useChatRuntime } from '@assistant-ui/react-ai-sdk'
import { DefaultChatTransport } from 'ai'
import {
  ThreadPrimitive,
  MessagePrimitive,
  ComposerPrimitive,
  useThreadRuntime,
} from '@assistant-ui/react'
import type { ConsumeChatProps } from './ConsumeChatLegacy'

// ─── Message ─────────────────────────────────────────────────────────────────

function V2Message() {
  return (
    <MessagePrimitive.Root
      className="group flex w-full max-w-3xl mx-auto flex-col gap-1 px-4 py-3"
      data-testid="v2-message"
    >
      <MessagePrimitive.If user>
        <div className="flex justify-end">
          <div
            className="rounded-2xl bg-indigo-600 px-4 py-2.5 text-sm text-white max-w-[70%]"
            data-testid="v2-user-message"
          >
            {/* F.2: flat props — renderer receives {text,...} directly, not a nested part object */}
            <MessagePrimitive.Parts components={{ Text: (props) => <span>{props.text}</span> }} />
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
        </div>
      </MessagePrimitive.If>
    </MessagePrimitive.Root>
  )
}

// ─── Composer ─────────────────────────────────────────────────────────────────

function V2Composer() {
  // F.3: useThreadRuntime().subscribe() for run-state (F.3 — deprecated primitive avoided)
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
 * α7 scaffold: minimal Thread against /api/chat/consume.
 * Accepts the same props as ConsumeChatLegacy for API compatibility.
 * MARSYS chrome (sidebar, reasoning drawer, citations, etc.) wired in β phase.
 */
export function ConsumeChatV2({ chartId, chartName, chartMeta }: ConsumeChatProps) {
  // Stable body factory: F.1 — DefaultChatTransport with api: not shorthand
  const chartIdRef = useRef(chartId)
  chartIdRef.current = chartId

  const runtime = useChatRuntime({
    transport: new DefaultChatTransport({
      api: '/api/chat/consume',
      body: () => ({ chartId: chartIdRef.current }),
    }),
  })

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div
        className="flex h-screen flex-col bg-zinc-950 text-zinc-100"
        data-testid="consume-chat-v2-root"
      >
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
          <V2Thread />
        </main>
      </div>
    </AssistantRuntimeProvider>
  )
}
