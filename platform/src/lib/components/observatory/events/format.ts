// Cell formatters for the event table. Pure; trivially testable.

import type { EventRow, EventColumnId } from './types'

export function formatCostUsd(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return value.toFixed(6)
}

export function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toISOString().replace('T', ' ').replace('Z', 'Z')
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return String(value)
}

export function getCellValue(row: EventRow, col: EventColumnId): string {
  switch (col) {
    case 'timestamp':
      return formatTimestamp(row.started_at)
    case 'conversation_name':
      return row.conversation_name ?? row.conversation_id ?? '—'
    case 'provider':
      return row.provider
    case 'model':
      return row.model
    case 'pipeline_stage':
      return row.pipeline_stage
    case 'input_tokens':
      return formatNumber(row.input_tokens)
    case 'output_tokens':
      return formatNumber(row.output_tokens)
    case 'cost_usd':
      return formatCostUsd(row.computed_cost_usd)
    case 'latency_ms':
      return formatNumber(row.latency_ms)
    case 'status':
      return row.status
    case 'prompt_id':
      return row.prompt_id
    case 'user_id':
      return row.user_id
    case 'cache_tokens':
      return formatNumber(
        (row.cache_read_tokens ?? 0) + (row.cache_write_tokens ?? 0),
      )
    case 'error_code':
      return row.error_code ?? '—'
  }
}
