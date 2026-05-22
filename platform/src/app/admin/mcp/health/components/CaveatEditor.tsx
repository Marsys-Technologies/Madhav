/**
 * CaveatEditor — inline editable caveat list for a single MCP tool.
 *
 * Renders existing caveats and an "Add caveat" form. The `caveat_class`
 * dropdown distinguishes data_depth_gap, tool_reliability_gap, known_bug,
 * usage_hint per the tool_caveats table schema (migration 076).
 *
 * Mutations go to /api/admin/mcp/caveats (CRUD endpoint for tool_caveats).
 *
 * MCPT v3.1.0-S5
 */
'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

// ── Types ─────────────────────────────────────────────────────────────────────

export type CaveatClass = 'data_depth_gap' | 'tool_reliability_gap' | 'known_bug' | 'usage_hint'
export type CaveatSeverity = 'info' | 'warn' | 'critical'

export interface Caveat {
  id?: string
  text?: string
  caveat_text?: string
  class?: string
  caveat_class?: string
  severity?: string
  active?: boolean
}

interface Props {
  toolName: string
  initialCaveats: Caveat[]
}

const CLASS_OPTIONS: { value: CaveatClass; label: string; description: string }[] = [
  { value: 'data_depth_gap',       label: 'Data depth gap',       description: 'Missing rows / incomplete backfill' },
  { value: 'tool_reliability_gap', label: 'Tool reliability gap', description: 'Code bug or schema mismatch' },
  { value: 'known_bug',            label: 'Known bug',            description: 'Documented defect, fix scheduled' },
  { value: 'usage_hint',           label: 'Usage hint',           description: 'Recommended usage pattern' },
]

const SEVERITY_OPTIONS: { value: CaveatSeverity; label: string }[] = [
  { value: 'info',     label: 'Info' },
  { value: 'warn',     label: 'Warning' },
  { value: 'critical', label: 'Critical' },
]

// ── API helpers ───────────────────────────────────────────────────────────────

async function addCaveat(toolName: string, text: string, cls: CaveatClass, severity: CaveatSeverity) {
  const res = await fetch('/api/admin/mcp/caveats', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tool_name: toolName, caveat_text: text, caveat_class: cls, severity }),
  })
  if (!res.ok) throw new Error(`Failed to add caveat: ${res.status}`)
  return res.json()
}

async function deleteCaveat(id: string) {
  const res = await fetch(`/api/admin/mcp/caveats/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`Failed to delete caveat: ${res.status}`)
}

// ── Caveat class badge ────────────────────────────────────────────────────────

function ClassBadge({ cls }: { cls: string }) {
  const color =
    cls === 'data_depth_gap'       ? 'bg-blue-500/10 text-blue-400'
    : cls === 'tool_reliability_gap' ? 'bg-orange-500/10 text-orange-400'
    : cls === 'known_bug'            ? 'bg-red-500/10 text-red-400'
    : 'bg-muted text-muted-foreground'
  return (
    <span className={`inline-flex rounded px-1.5 py-0.5 text-xs font-medium ${color}`}>
      {cls.replace(/_/g, ' ')}
    </span>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────

export function CaveatEditor({ toolName, initialCaveats }: Props) {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [newText, setNewText] = useState('')
  const [newClass, setNewClass] = useState<CaveatClass>('data_depth_gap')
  const [newSeverity, setNewSeverity] = useState<CaveatSeverity>('warn')

  const addMutation = useMutation({
    mutationFn: () => addCaveat(toolName, newText, newClass, newSeverity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'mcp', 'tool-health'] })
      setNewText('')
      setShowForm(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCaveat(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'mcp', 'tool-health'] })
    },
  })

  const caveats = initialCaveats

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          Caveats — {toolName}
        </h4>
        <button
          onClick={() => setShowForm(v => !v)}
          className="text-xs text-brand-gold-cream hover:underline"
        >
          + Add caveat
        </button>
      </div>

      {/* Existing caveats */}
      {caveats.length > 0 ? (
        <div className="space-y-2">
          {caveats.map((c, i) => {
            const text = c.caveat_text ?? c.text ?? ''
            const cls = c.caveat_class ?? c.class ?? 'usage_hint'
            const severity = c.severity ?? 'info'
            return (
              <div key={c.id ?? i} className="flex items-start gap-2 rounded-md bg-muted/10 p-2.5">
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <ClassBadge cls={cls} />
                    <span className="text-xs text-muted-foreground">{severity}</span>
                  </div>
                  <p className="text-xs">{text}</p>
                </div>
                {c.id && (
                  <button
                    onClick={() => deleteMutation.mutate(c.id!)}
                    disabled={deleteMutation.isPending}
                    className="text-xs text-red-400/60 hover:text-red-400 disabled:opacity-40 shrink-0"
                    title="Delete caveat"
                  >
                    ✕
                  </button>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        <p className="text-xs text-muted-foreground italic">No caveats — tool is fully operational.</p>
      )}

      {/* Add caveat form */}
      {showForm && (
        <div className="rounded-md border border-border/50 p-3 space-y-3 bg-muted/10">
          <h5 className="text-xs font-medium">New caveat</h5>

          <div>
            <label className="block text-xs text-muted-foreground mb-1">Caveat class</label>
            <select
              value={newClass}
              onChange={e => setNewClass(e.target.value as CaveatClass)}
              className="w-full text-xs rounded border border-border/50 bg-background px-2 py-1.5"
            >
              {CLASS_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label} — {opt.description}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-muted-foreground mb-1">Severity</label>
            <select
              value={newSeverity}
              onChange={e => setNewSeverity(e.target.value as CaveatSeverity)}
              className="w-full text-xs rounded border border-border/50 bg-background px-2 py-1.5"
            >
              {SEVERITY_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-muted-foreground mb-1">Caveat text</label>
            <textarea
              value={newText}
              onChange={e => setNewText(e.target.value)}
              rows={3}
              placeholder="Describe the caveat. Be specific — this appears in tool_health() output and the capabilities resource."
              className="w-full text-xs rounded border border-border/50 bg-background px-2 py-1.5 resize-none"
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => addMutation.mutate()}
              disabled={!newText.trim() || addMutation.isPending}
              className="text-xs px-3 py-1.5 rounded bg-brand-gold-cream text-black font-medium disabled:opacity-40 hover:opacity-90"
            >
              {addMutation.isPending ? 'Saving…' : 'Save caveat'}
            </button>
            <button
              onClick={() => { setShowForm(false); setNewText('') }}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Cancel
            </button>
          </div>

          {addMutation.isError && (
            <p className="text-xs text-red-400">
              Failed to save caveat. Check that /api/admin/mcp/caveats is deployed.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
