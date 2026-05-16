'use client'

/**
 * Minimal Thread implementation using assistant-ui primitives.
 * Used exclusively in the α0 spike to verify rendering behavior.
 *
 * Spike verification checklist (checked in Playwright spike.spec.ts):
 * - Scroll anchoring: viewport stays at bottom during streaming (no jump per token)
 * - Reasoning drawer: expands/collapses correctly
 * - Code blocks: render with syntax highlighting
 * - KaTeX math: renders inline ($...$) and block ($$...$$)
 * - Message edit/regenerate UI: affordances present
 * - Abort button: present during streaming
 */

import React, { useState } from 'react'
import {
  ThreadPrimitive,
  MessagePrimitive,
  ComposerPrimitive,
  useThreadRuntime,
} from '@assistant-ui/react'

// ─── Message component ────────────────────────────────────────────────────────

function ReasoningBlock({ content }: { content: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div
      className="mb-3 rounded-lg border border-zinc-700 bg-zinc-900/60"
      data-testid="reasoning-drawer"
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
        aria-expanded={open}
        data-testid="reasoning-toggle"
      >
        <span className="font-mono text-violet-400">⟨think⟩</span>
        <span className="flex-1 truncate">
          {open ? 'Hide reasoning' : 'Show reasoning'}&nbsp;·&nbsp;
          {content.split(/\s+/).length} tokens
        </span>
        <span className="font-mono text-zinc-500">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div
          className="border-t border-zinc-700 px-4 py-3 text-xs font-mono text-zinc-400 whitespace-pre-wrap"
          data-testid="reasoning-content"
        >
          {content}
        </div>
      )}
    </div>
  )
}

function SpikeMessage() {
  return (
    <MessagePrimitive.Root className="group flex w-full max-w-3xl mx-auto flex-col gap-1 px-4 py-3">
      <MessagePrimitive.If user>
        <div className="flex justify-end">
          <div
            className="rounded-2xl bg-indigo-600 px-4 py-2.5 text-sm text-white max-w-[70%]"
            data-testid="user-message"
          >
            <MessagePrimitive.Parts components={{ Text: (props) => <span>{props.text}</span> }} />
          </div>
        </div>
      </MessagePrimitive.If>

      <MessagePrimitive.If assistant>
        <div className="flex flex-col gap-2 w-full" data-testid="assistant-message">
          {/* Reasoning section — rendered from message parts */}
          <MessagePrimitive.Parts
            components={{
              Reasoning: (props) => <ReasoningBlock content={props.text} />,
              Text: (props) => (
                <div
                  className="prose prose-invert prose-sm max-w-none text-zinc-200 leading-relaxed"
                  data-testid="message-text"
                >
                  <pre className="whitespace-pre-wrap font-sans text-sm">{props.text}</pre>
                </div>
              ),
            }}
          />

          {/* Action row */}
          <div
            className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity mt-1"
            data-testid="message-actions"
          >
            <button
              type="button"
              className="text-xs text-zinc-500 hover:text-zinc-300 px-2 py-1 rounded hover:bg-zinc-800 transition-colors"
              data-testid="copy-btn"
            >
              Copy
            </button>
            <button
              type="button"
              className="text-xs text-zinc-500 hover:text-zinc-300 px-2 py-1 rounded hover:bg-zinc-800 transition-colors"
              data-testid="regenerate-btn"
            >
              Regenerate
            </button>
          </div>
        </div>
      </MessagePrimitive.If>
    </MessagePrimitive.Root>
  )
}

// ─── Composer component ───────────────────────────────────────────────────────

function SpikeComposer() {
  const runtime = useThreadRuntime()
  const [isRunning, setIsRunning] = React.useState(false)

  React.useEffect(() => {
    const unsubscribe = runtime.subscribe(() => {
      setIsRunning(runtime.getState().isRunning)
    })
    return unsubscribe
  }, [runtime])

  return (
    <ComposerPrimitive.Root className="border-t border-zinc-800 bg-zinc-950 px-4 py-3">
      <div className="mx-auto max-w-3xl flex items-end gap-3">
        <ComposerPrimitive.Input
          className="flex-1 resize-none rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-colors"
          placeholder="Ask about the chart… (spike mode)"
          rows={3}
          autoFocus
          data-testid="composer-input"
        />
        <div className="flex flex-col gap-2 pb-0.5">
          {isRunning ? (
            <ComposerPrimitive.Cancel asChild>
              <button
                type="button"
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-700 text-zinc-300 hover:bg-zinc-600 transition-colors"
                title="Stop generation"
                data-testid="abort-btn"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-4 w-4"
                >
                  <rect x="4" y="4" width="8" height="8" rx="1" />
                </svg>
              </button>
            </ComposerPrimitive.Cancel>
          ) : (
            <ComposerPrimitive.Send asChild>
              <button
                type="submit"
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                data-testid="send-btn"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  className="h-4 w-4"
                >
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

// ─── Thread root ──────────────────────────────────────────────────────────────

export function ChatSpikeThread() {
  return (
    <ThreadPrimitive.Root
      className="flex h-full flex-col"
      data-testid="thread-root"
    >
      <ThreadPrimitive.Viewport
        className="flex-1 overflow-y-auto scroll-smooth py-4"
        data-testid="thread-viewport"
      >
        <ThreadPrimitive.Empty>
          <div
            className="flex h-full flex-col items-center justify-center gap-4 text-center px-4"
            data-testid="thread-empty"
          >
            <div className="rounded-full bg-indigo-500/10 p-4 border border-indigo-500/20">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                className="h-8 w-8 text-indigo-400"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-200">α0 Spike Ready</p>
              <p className="text-xs text-zinc-500 mt-1">
                Ask anything to stream a fixture response and verify assistant-ui behavior.
              </p>
            </div>
          </div>
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages
          components={{ Message: SpikeMessage }}
        />

        <ThreadPrimitive.ScrollToBottom asChild>
          <button
            type="button"
            className="fixed bottom-24 right-6 flex h-8 w-8 items-center justify-center rounded-full bg-zinc-700 text-zinc-300 shadow-lg hover:bg-zinc-600 transition-all opacity-80 hover:opacity-100"
            data-testid="scroll-to-bottom"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="currentColor"
              className="h-4 w-4"
            >
              <path d="M8 12L2 6h12l-6 6z" />
            </svg>
          </button>
        </ThreadPrimitive.ScrollToBottom>
      </ThreadPrimitive.Viewport>

      <SpikeComposer />
    </ThreadPrimitive.Root>
  )
}
