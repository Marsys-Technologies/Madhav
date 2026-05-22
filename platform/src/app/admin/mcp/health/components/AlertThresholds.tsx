/**
 * AlertThresholds — threshold configuration per metric, inline in ToolHealth tab.
 *
 * Reads from /api/admin/mcp/alert-configs (backed by mcp_alerts_config table,
 * migration 077). Allows the operator to edit threshold values, window_hours,
 * and channel toggles. Saves via PUT /api/admin/mcp/alert-configs/:id.
 *
 * MCPT v3.1.0-S5
 */
'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// ── Types ─────────────────────────────────────────────────────────────────────

interface AlertConfig {
  id: string
  metric_name: string
  scope: 'global' | 'per_tool'
  tool_name: string | null
  threshold_value: number
  comparison: 'gte' | 'lte' | 'gt' | 'lt'
  window_hours: number
  channels: string[]
  enabled: boolean
  slack_webhook_url: string | null
  email_recipients: string[] | null
}

// ── Fetch / mutate ────────────────────────────────────────────────────────────

async function fetchAlertConfigs(): Promise<AlertConfig[]> {
  const res = await fetch('/api/admin/mcp/alert-configs')
  if (!res.ok) {
    if (res.status === 404) return [] // endpoint may be added in a later deploy
    throw new Error(`Failed to fetch alert configs: ${res.status}`)
  }
  const data = await res.json() as { configs?: AlertConfig[] }
  return data.configs ?? []
}

async function updateAlertConfig(id: string, patch: Partial<AlertConfig>): Promise<void> {
  const res = await fetch(`/api/admin/mcp/alert-configs/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
  if (!res.ok) throw new Error(`Failed to update alert config: ${res.status}`)
}

// ── Comparison label ──────────────────────────────────────────────────────────

function cmpLabel(cmp: string): string {
  return cmp === 'gte' ? '≥' : cmp === 'lte' ? '≤' : cmp === 'gt' ? '>' : '<'
}

// ── Row editor ────────────────────────────────────────────────────────────────

function AlertRow({ config }: { config: AlertConfig }) {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [threshold, setThreshold] = useState(String(config.threshold_value))
  const [window, setWindow] = useState(String(config.window_hours))
  const [slack, setSlack] = useState(config.channels.includes('slack'))
  const [email, setEmail] = useState(config.channels.includes('email'))
  const [enabled, setEnabled] = useState(config.enabled)

  const mutation = useMutation({
    mutationFn: () => updateAlertConfig(config.id, {
      threshold_value: parseFloat(threshold),
      window_hours: parseInt(window),
      channels: [slack && 'slack', email && 'email'].filter(Boolean) as string[],
      enabled,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'mcp', 'alert-configs'] })
      setEditing(false)
    },
  })

  const toolLabel = config.tool_name ? ` [${config.tool_name}]` : ''
  const displayName = `${config.metric_name}${toolLabel}`

  if (!editing) {
    return (
      <tr className="hover:bg-muted/10">
        <td className="px-4 py-2.5 font-mono text-xs">{displayName}</td>
        <td className="px-4 py-2.5 text-xs text-muted-foreground">
          {cmpLabel(config.comparison)} {config.threshold_value}
        </td>
        <td className="px-4 py-2.5 text-xs text-muted-foreground">{config.window_hours}h</td>
        <td className="px-4 py-2.5 text-xs text-muted-foreground">{config.channels.join(', ') || '—'}</td>
        <td className="px-4 py-2.5">
          <span className={`text-xs ${config.enabled ? 'text-green-400' : 'text-muted-foreground'}`}>
            {config.enabled ? 'On' : 'Off'}
          </span>
        </td>
        <td className="px-4 py-2.5">
          <button
            onClick={() => setEditing(true)}
            className="text-xs text-brand-gold-cream hover:underline"
          >
            Edit
          </button>
        </td>
      </tr>
    )
  }

  return (
    <tr className="bg-muted/10">
      <td className="px-4 py-2.5 font-mono text-xs">{displayName}</td>
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-1">
          <span className="text-xs text-muted-foreground">{cmpLabel(config.comparison)}</span>
          <input
            type="number"
            value={threshold}
            onChange={e => setThreshold(e.target.value)}
            step="0.01"
            className="w-20 text-xs rounded border border-border/50 bg-background px-2 py-1"
          />
        </div>
      </td>
      <td className="px-4 py-2.5">
        <input
          type="number"
          value={window}
          onChange={e => setWindow(e.target.value)}
          min="1"
          max="168"
          className="w-16 text-xs rounded border border-border/50 bg-background px-2 py-1"
        />
        <span className="ml-1 text-xs text-muted-foreground">h</span>
      </td>
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1 text-xs cursor-pointer">
            <input type="checkbox" checked={slack} onChange={e => setSlack(e.target.checked)} />
            Slack
          </label>
          <label className="flex items-center gap-1 text-xs cursor-pointer">
            <input type="checkbox" checked={email} onChange={e => setEmail(e.target.checked)} />
            Email
          </label>
        </div>
      </td>
      <td className="px-4 py-2.5">
        <label className="flex items-center gap-1 text-xs cursor-pointer">
          <input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)} />
          Enabled
        </label>
      </td>
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-2">
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="text-xs px-2 py-1 rounded bg-brand-gold-cream text-black font-medium disabled:opacity-40"
          >
            {mutation.isPending ? '…' : 'Save'}
          </button>
          <button
            onClick={() => setEditing(false)}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Cancel
          </button>
        </div>
      </td>
    </tr>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export function AlertThresholds() {
  const configsQuery = useQuery({
    queryKey: ['admin', 'mcp', 'alert-configs'],
    queryFn: fetchAlertConfigs,
    staleTime: 60_000,
  })

  const configs = configsQuery.data ?? []

  if (configsQuery.isError) {
    return <p className="text-xs text-red-400">Failed to load alert configurations.</p>
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Alert Thresholds</h3>
        <p className="text-xs text-muted-foreground">
          Dispatched by <code>dispatch.ts</code> from the nightly audit job.
          Configure <code>ALERT_SLACK_WEBHOOK_URL</code> and <code>ALERT_EMAIL_RECIPIENTS</code> env vars.
        </p>
      </div>

      {configsQuery.isLoading ? (
        <p className="text-xs text-muted-foreground animate-pulse">Loading alert configs…</p>
      ) : configs.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          No alert configs found. Apply migration 077 to seed defaults, or the endpoint may not be deployed yet.
        </p>
      ) : (
        <div className="overflow-x-auto rounded border border-border/30">
          <table className="w-full text-sm">
            <thead className="border-b border-border/30 bg-muted/20">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Metric</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Threshold</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Window</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Channels</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/20">
              {configs.map(config => (
                <AlertRow key={config.id} config={config} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
