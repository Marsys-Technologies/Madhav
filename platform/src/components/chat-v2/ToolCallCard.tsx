'use client'

import type { ToolPart } from '@/lib/streams/data_parts'

interface ToolCallCardProps {
  tool: ToolPart
}

export function ToolCallCard({ tool }: ToolCallCardProps) {
  return (
    <div
      className={`flex items-center gap-2 rounded-lg border px-2.5 py-1.5 text-[11px] ${
        tool.status === 'running'
          ? 'border-indigo-500/30 bg-indigo-900/20 text-indigo-300'
          : tool.status === 'done'
            ? 'border-zinc-700/50 bg-zinc-800/40 text-zinc-400'
            : tool.status === 'error'
              ? 'border-red-500/30 bg-red-900/20 text-red-400'
              : 'border-zinc-700/30 bg-zinc-800/20 text-zinc-500'
      }`}
      data-testid={`v2-tool-card-${tool.name}`}
    >
      {tool.status === 'running' && (
        <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true">
          <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-indigo-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-500" />
        </span>
      )}
      {tool.status === 'done' && (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 12 12"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className="h-3 w-3 shrink-0 text-zinc-500"
          aria-hidden="true"
        >
          <path d="M2 6l3 3 5-5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
      {tool.status === 'error' && (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 12 12"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className="h-3 w-3 shrink-0 text-red-400"
          aria-hidden="true"
        >
          <path d="M2 2l8 8M10 2l-8 8" strokeLinecap="round" />
        </svg>
      )}
      {tool.status === 'pending' && (
        <span className="h-2 w-2 rounded-full border border-zinc-600 shrink-0" aria-hidden="true" />
      )}
      <span className="font-mono truncate max-w-[140px]">{tool.name}</span>
      {tool.ms !== undefined && tool.status === 'done' && (
        <span className="ml-auto text-[10px] opacity-50 shrink-0">{tool.ms}ms</span>
      )}
      {(tool.ok_count ?? 0) > 0 && (
        <span className="ml-auto text-[10px] text-green-500/70 shrink-0">{tool.ok_count} ok</span>
      )}
      {(tool.err_count ?? 0) > 0 && (
        <span className="ml-1 text-[10px] text-red-400/70 shrink-0">{tool.err_count} err</span>
      )}
    </div>
  )
}
