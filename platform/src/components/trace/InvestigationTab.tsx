'use client'

/**
 * InvestigationTab — TRACE-9 (W2-TRACE-B).
 *
 * Lazy-loading deep-dive over the four monitoring tables for a single
 * query_id. Fetches `/api/investigation/:query_id` only on first render
 * when `isVisible` flips to true, then renders four sub-tabs over the
 * payload (LLM Calls / Query Plan / Tool Executions / Context Assembly).
 * Each sub-tab provides a condensed table view + a JSON pretty-print with
 * a copy button. Top-level export buttons:
 *   - "Export JSON" — full InvestigationResponse via Blob download
 *   - "Export CSV"  — tool_executions only via Blob download
 * No server round-trip for either export — the data is already in memory.
 */

import { useEffect, useState } from 'react'
import { Copy, Download, ChevronRight } from 'lucide-react'
import type {
  ContextAssemblyLogRow,
  LlmCallLogRow,
  QueryPlanLogRow,
  ToolExecutionLogRow,
} from '@/lib/db/monitoring-types'

interface InvestigationResponse {
  query_id: string
  llm_calls: LlmCallLogRow[]
  query_plan: QueryPlanLogRow | null
  tool_executions: ToolExecutionLogRow[]
  context_assembly: ContextAssemblyLogRow | null
}

interface InvestigationTabProps {
  query_id: string | null
  isVisible: boolean
}

type SubTab = 'llm_calls' | 'query_plan' | 'tool_executions' | 'context_assembly'

const SUB_TABS: Array<{ id: SubTab; label: string }> = [
  { id: 'llm_calls', label: 'LLM Calls' },
  { id: 'query_plan', label: 'Query Plan' },
  { id: 'tool_executions', label: 'Tool Executions' },
  { id: 'context_assembly', label: 'Context Assembly' },
]

function downloadBlob(filename: string, mime: string, content: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function escapeCsv(value: unknown): string {
  if (value == null) return ''
  let str: string
  if (typeof value === 'string') {
    str = value
  } else if (typeof value === 'object') {
    str = JSON.stringify(value)
  } else {
    str = String(value)
  }
  if (/[",\n\r]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

function toolExecutionsToCsv(rows: ToolExecutionLogRow[]): string {
  const headers: Array<keyof ToolExecutionLogRow> = [
    'id',
    'query_id',
    'tool_name',
    'params_json',
    'status',
    'rows_returned',
    'latency_ms',
    'token_estimate',
    'data_asset_id',
    'error_code',
    'served_from_cache',
    'fallback_used',
    'created_at',
  ]
  const headerLine = headers.join(',')
  const dataLines = rows.map((row) =>
    headers.map((h) => escapeCsv(row[h])).join(','),
  )
  return [headerLine, ...dataLines].join('\n')
}

function CopyButton({ getText }: { getText: () => string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(getText())
          setCopied(true)
          setTimeout(() => setCopied(false), 1200)
        } catch {
          /* clipboard write failed; user can still select-all manually */
        }
      }}
      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded border border-[rgba(212,175,55,0.25)] bg-[rgba(212,175,55,0.06)] text-[rgba(244,209,96,0.85)] hover:bg-[rgba(212,175,55,0.12)] text-[10px]"
    >
      <Copy size={9} />
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function JsonBlock({ data }: { data: unknown }) {
  const text = JSON.stringify(data, null, 2)
  return (
    <div className="relative">
      <div className="absolute right-2 top-2">
        <CopyButton getText={() => text} />
      </div>
      <pre className="text-[10px] text-[rgba(252,226,154,0.8)] whitespace-pre-wrap break-all font-mono px-3 py-2 rounded border border-[rgba(212,175,55,0.10)] bg-[rgba(5,3,1,0.6)] max-h-[280px] overflow-y-auto">
        {text}
      </pre>
    </div>
  )
}

function CondensedTable({
  rows,
  fields,
}: {
  rows: Array<Record<string, unknown>>
  fields: string[]
}) {
  if (rows.length === 0) {
    return (
      <div className="px-3 py-2 text-[10px] italic text-[rgba(212,175,55,0.4)]">
        No rows.
      </div>
    )
  }
  return (
    <div className="rounded border border-[rgba(212,175,55,0.15)] bg-[rgba(13,10,5,0.5)] overflow-x-auto">
      <table className="w-full text-[10px]">
        <thead>
          <tr className="border-b border-[rgba(212,175,55,0.12)] text-[rgba(212,175,55,0.55)] uppercase tracking-[0.1em] text-[9px]">
            {fields.map((f) => (
              <th key={f} className="text-left px-2 py-1.5 font-semibold">
                {f}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[rgba(212,175,55,0.08)]">
          {rows.map((row, i) => (
            <tr key={i} className="text-[rgba(252,226,154,0.85)]">
              {fields.map((f) => {
                const v = row[f]
                let display: string
                if (v == null) {
                  display = '—'
                } else if (typeof v === 'object') {
                  display = JSON.stringify(v)
                } else {
                  display = String(v)
                }
                return (
                  <td
                    key={f}
                    className="px-2 py-1.5 font-mono truncate max-w-[180px]"
                    title={display}
                  >
                    {display}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function InvestigationTab({
  query_id,
  isVisible,
}: InvestigationTabProps) {
  return <InvestigationTabForQuery key={query_id ?? 'no-query'} query_id={query_id} isVisible={isVisible} />
}

function InvestigationTabForQuery({
  query_id,
  isVisible,
}: InvestigationTabProps) {
  const [expanded, setExpanded] = useState(false)
  const [data, setData] = useState<InvestigationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasFetched, setHasFetched] = useState(false)
  const [activeSub, setActiveSub] = useState<SubTab>('llm_calls')

  useEffect(() => {
    if (!isVisible || !expanded || !query_id || hasFetched) return
    let cancelled = false
    const initialFetch = setTimeout(() => {
      setLoading(true)
      setError(null)
      fetch(`/api/investigation/${encodeURIComponent(query_id)}`)
        .then(async (r) => {
          if (!r.ok) {
            if (r.status === 404) throw new Error('No records for this query.')
            throw new Error(`Investigation fetch failed (${r.status})`)
          }
          return (await r.json()) as InvestigationResponse
        })
        .then((payload) => {
          if (cancelled) return
          setData(payload)
          setHasFetched(true)
        })
        .catch((e: unknown) => {
          if (cancelled) return
          setError(e instanceof Error ? e.message : 'Investigation fetch failed.')
          setHasFetched(true)
        })
        .finally(() => {
          if (!cancelled) setLoading(false)
        })
    }, 0)
    return () => {
      cancelled = true
      clearTimeout(initialFetch)
    }
  }, [isVisible, expanded, query_id, hasFetched])

  if (!query_id) {
    return (
      <div className="px-4 py-3 text-[10px] italic text-[rgba(212,175,55,0.4)]">
        Run a query to enable investigation.
      </div>
    )
  }

  const headerLabel = expanded ? 'Investigation' : 'Investigation (click to load)'

  return (
    <div className="border border-[rgba(212,175,55,0.15)] rounded mx-2 my-2 overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-center gap-2 px-3 py-2 bg-[rgba(13,10,5,0.7)] hover:bg-[rgba(212,175,55,0.06)] transition-colors"
      >
        <ChevronRight
          size={11}
          className={`text-[rgba(212,175,55,0.6)] transition-transform ${
            expanded ? 'rotate-90' : ''
          }`}
        />
        <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(212,175,55,0.7)]">
          {headerLabel}
        </span>
        <span className="ml-auto text-[10px] text-[rgba(212,175,55,0.45)] font-mono truncate">
          {query_id}
        </span>
      </button>

      {expanded && (
        <div className="border-t border-[rgba(212,175,55,0.10)] bg-[rgba(8,5,2,0.5)]">
          {loading && (
            <div className="px-4 py-3 text-[10px] text-[rgba(212,175,55,0.55)]">
              Loading investigation data…
            </div>
          )}

          {error && !loading && (
            <div className="px-4 py-3 text-[10px] text-[rgba(240,150,120,0.95)]">
              {error}
            </div>
          )}

          {!loading && !error && data && (
            <div className="px-3 py-3 space-y-3">
              {/* Export buttons */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() =>
                    downloadBlob(
                      `investigation_${data.query_id}.json`,
                      'application/json',
                      JSON.stringify(data, null, 2),
                    )
                  }
                  className="inline-flex items-center gap-1 px-2 py-1 rounded border border-[rgba(212,175,55,0.25)] bg-[rgba(212,175,55,0.06)] text-[rgba(244,209,96,0.85)] hover:bg-[rgba(212,175,55,0.12)] text-[10px]"
                >
                  <Download size={10} />
                  Export JSON
                </button>
                <button
                  type="button"
                  onClick={() =>
                    downloadBlob(
                      `tool_executions_${data.query_id}.csv`,
                      'text/csv',
                      toolExecutionsToCsv(data.tool_executions),
                    )
                  }
                  className="inline-flex items-center gap-1 px-2 py-1 rounded border border-[rgba(212,175,55,0.25)] bg-[rgba(212,175,55,0.06)] text-[rgba(244,209,96,0.85)] hover:bg-[rgba(212,175,55,0.12)] text-[10px]"
                >
                  <Download size={10} />
                  Export CSV
                </button>
                <span className="ml-auto text-[10px] text-[rgba(212,175,55,0.45)]">
                  {data.llm_calls.length} llm · {data.tool_executions.length}{' '}
                  tools
                </span>
              </div>

              {/* Sub-tabs */}
              <div className="flex gap-px bg-[rgba(5,3,1,0.6)] rounded p-0.5 w-fit">
                {SUB_TABS.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setActiveSub(t.id)}
                    className={`px-2.5 py-1 rounded text-[10px] font-medium transition-colors ${
                      activeSub === t.id
                        ? 'bg-[rgba(212,175,55,0.12)] text-[rgba(252,226,154,0.95)]'
                        : 'text-[rgba(212,175,55,0.5)] hover:text-[rgba(252,226,154,0.85)]'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              {/* Sub-tab body */}
              {activeSub === 'llm_calls' && (
                <div className="space-y-2">
                  <CondensedTable
                    rows={
                      data.llm_calls as unknown as Array<
                        Record<string, unknown>
                      >
                    }
                    fields={[
                      'call_stage',
                      'model_id',
                      'provider',
                      'input_tokens',
                      'output_tokens',
                      'latency_ms',
                      'cost_usd',
                      'fallback_used',
                      'error_code',
                    ]}
                  />
                  <JsonBlock data={data.llm_calls} />
                </div>
              )}

              {activeSub === 'query_plan' && (
                <div className="space-y-2">
                  {data.query_plan ? (
                    <>
                      <CondensedTable
                        rows={[
                          data.query_plan as unknown as Record<string, unknown>,
                        ]}
                        fields={[
                          'planner_model_id',
                          'query_class',
                          'tool_count',
                          'parsing_success',
                          'parse_error',
                          'fallback_used',
                          'planner_latency_ms',
                        ]}
                      />
                      <JsonBlock data={data.query_plan} />
                    </>
                  ) : (
                    <div className="px-3 py-2 text-[10px] italic text-[rgba(212,175,55,0.4)]">
                      No query plan recorded.
                    </div>
                  )}
                </div>
              )}

              {activeSub === 'tool_executions' && (
                <div className="space-y-2">
                  <CondensedTable
                    rows={
                      data.tool_executions as unknown as Array<
                        Record<string, unknown>
                      >
                    }
                    fields={[
                      'tool_name',
                      'status',
                      'rows_returned',
                      'latency_ms',
                      'token_estimate',
                      'data_asset_id',
                      'served_from_cache',
                      'fallback_used',
                      'error_code',
                    ]}
                  />
                  <JsonBlock data={data.tool_executions} />
                </div>
              )}

              {activeSub === 'context_assembly' && (
                <div className="space-y-2">
                  {data.context_assembly ? (
                    <>
                      <CondensedTable
                        rows={[
                          data.context_assembly as unknown as Record<
                            string,
                            unknown
                          >,
                        ]}
                        fields={[
                          'l1_tokens',
                          'l2_5_signal_tokens',
                          'l2_5_pattern_tokens',
                          'l4_tokens',
                          'vector_tokens',
                          'cgm_tokens',
                          'total_tokens',
                          'synthesis_model_id',
                          'model_max_context',
                          'b3_compliant',
                          'citation_count',
                          'verified_citations',
                        ]}
                      />
                      <JsonBlock data={data.context_assembly} />
                    </>
                  ) : (
                    <div className="px-3 py-2 text-[10px] italic text-[rgba(212,175,55,0.4)]">
                      No context assembly recorded.
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
