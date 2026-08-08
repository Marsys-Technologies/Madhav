'use client'

/**
 * QueryDNAPanel — BHISMA-B3 §5.2
 *
 * Displays the "DNA" of the current query — what the planner decided about
 * intent, classification, tool authorization, and temporal context. Reads
 * from the planning step's data_summary + payload.query_plan.
 *
 * Graceful degradation: when the planner step is absent (waiting for query)
 * the panel shows a placeholder. When payload.query_plan is missing
 * (pre-BHISMA-B2 traces), the panel falls back to data_summary fields and
 * suppresses the rich sections (intent summary, planning rationale).
 */

import { useState } from 'react'
import { ChevronDown, ChevronUp, ChevronRight, Sparkles, AlertTriangle } from 'lucide-react'
import type { TraceStep, TraceQueryPlan, TraceToolCallSpec } from '@/lib/trace/types'
// CLIENT-SAFE import — this file is 'use client', so it must import graha
// labels from graha_labels.ts, never from address_resolver.ts (which pulls
// in @/lib/db/client → `server-only` and poisons the client bundle; see
// graha_labels.ts's own header for the full defect-class explanation).
import { grahaCodeOf, GRAHA_CODE_TO_NAME } from '@/lib/retrieval/graha_labels'

interface Props {
  steps: TraceStep[]
}

// ── Query class colour map (warm tonal palette, per §5.1 design system) ──────

const QUERY_CLASS_STYLE: Record<string, { bg: string; text: string; border: string; label: string }> = {
  factual:       { bg: 'bg-[rgba(var(--trace-blue-rgb),0.12)]',   text: 'text-[rgba(var(--trace-blue-rgb),0.9)]',   border: 'border-[rgba(var(--trace-blue-rgb),0.3)]',   label: 'FACTUAL' },
  interpretive:  { bg: 'bg-[rgba(var(--trace-gold-rgb),0.12)]',   text: 'text-[rgba(var(--trace-gold-rgb),0.9)]',   border: 'border-[rgba(var(--trace-gold-rgb),0.35)]',   label: 'INTERPRETIVE' },
  predictive:    { bg: 'bg-[rgba(var(--trace-red-rgb),0.12)]',    text: 'text-[rgba(var(--trace-red-rgb),0.9)]',    border: 'border-[rgba(var(--trace-red-rgb),0.3)]',    label: 'PREDICTIVE' },
  cross_domain:  { bg: 'bg-[rgba(var(--trace-violet-rgb),0.12)]', text: 'text-[rgba(var(--trace-violet-rgb),0.9)]', border: 'border-[rgba(var(--trace-violet-rgb),0.3)]', label: 'CROSS-DOMAIN' },
  discovery:     { bg: 'bg-[rgba(var(--trace-green-rgb),0.12)]',  text: 'text-[rgba(var(--trace-green-rgb),0.9)]',  border: 'border-[rgba(var(--trace-green-rgb),0.3)]',  label: 'DISCOVERY' },
  holistic:      { bg: 'bg-[rgba(var(--trace-gold-rgb),0.16)]',   text: 'text-[rgba(var(--trace-gold-rgb),0.95)]',   border: 'border-[rgba(var(--trace-gold-rgb),0.45)]',   label: 'HOLISTIC' },
  remedial:      { bg: 'bg-[rgba(var(--trace-red-rgb),0.12)]',    text: 'text-[rgba(var(--trace-red-rgb),0.85)]',    border: 'border-[rgba(var(--trace-red-rgb),0.3)]',    label: 'REMEDIAL' },
  cross_native:  { bg: 'bg-[rgba(var(--trace-blue-rgb),0.12)]',   text: 'text-[rgba(var(--trace-blue-rgb),0.85)]',   border: 'border-[rgba(var(--trace-blue-rgb),0.3)]',   label: 'CROSS-NATIVE' },
}

const UNKNOWN_CLASS_STYLE = {
  bg: 'bg-[rgba(var(--trace-gold-rgb),0.06)]',
  text: 'text-[rgba(var(--trace-gold-rgb),0.6)]',
  border: 'border-[rgba(var(--trace-gold-rgb),0.2)]',
  label: 'UNCLASSIFIED',
}

// ── CGM seed-node humanizer ──────────────────────────────────────────────────

// Values sourced from the graha SSoT (graha_labels.grahaCodeOf +
// GRAHA_CODE_TO_NAME) rather than hardcoded literals — ADHIṢṬHĀNA Lane A2.
const PLANET_LABELS: Record<string, string> = Object.fromEntries(
  ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN', 'RAHU', 'KETU']
    .map(p => [p, GRAHA_CODE_TO_NAME[grahaCodeOf(p)]]),
)

function humanizeSeedNode(seed: string): string {
  if (seed.startsWith('PLN.')) {
    const key = seed.slice(4).toUpperCase()
    return `${PLANET_LABELS[key] ?? key} (planet)`
  }
  if (seed.startsWith('HSE.')) {
    const n = seed.slice(4)
    const ord = n === '1' ? '1st' : n === '2' ? '2nd' : n === '3' ? '3rd' : `${n}th`
    return `${ord} house`
  }
  if (seed.startsWith('YOG.')) {
    return `Yoga: ${seed.slice(4)}`
  }
  if (seed.startsWith('SGN.')) {
    return `${seed.slice(4)} (sign)`
  }
  if (seed.startsWith('NAK.')) {
    return `Nakshatra: ${seed.slice(4)}`
  }
  return seed
}

// ── Tool-name → step_type-style badge inference ──────────────────────────────

function inferToolKind(toolName: string): 'sql' | 'vector' | 'gcs' | 'graph' | 'other' {
  if (toolName.includes('vector')) return 'vector'
  if (toolName.includes('graph') || toolName.includes('cgm')) return 'graph'
  if (toolName.includes('sql') || toolName.includes('register')) return 'sql'
  if (toolName.includes('gcs') || toolName.includes('bundle') || toolName.includes('section')) return 'gcs'
  return 'other'
}

const TOOL_KIND_STYLE = {
  sql:    'bg-[rgba(20,100,180,0.12)] text-[rgba(140,190,240,0.85)] border-[rgba(60,130,210,0.25)]',
  vector: 'bg-[rgba(20,160,100,0.12)] text-[rgba(120,210,160,0.85)] border-[rgba(40,180,120,0.25)]',
  gcs:    'bg-[rgba(200,80,40,0.12)]  text-[rgba(240,140,100,0.85)] border-[rgba(220,100,60,0.25)]',
  graph:  'bg-[rgba(160,110,220,0.12)] text-[rgba(200,160,240,0.85)] border-[rgba(170,120,225,0.25)]',
  other:  'bg-[rgba(212,175,55,0.08)]  text-[rgba(212,175,55,0.65)]  border-[rgba(212,175,55,0.2)]',
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmtMs(ms: number | undefined | null): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

function priorityDot(priority: 1 | 2 | 3 | undefined): string {
  if (priority === 1) return '●●●'
  if (priority === 2) return '●●○'
  if (priority === 3) return '●○○'
  return ''
}

// ── Component ────────────────────────────────────────────────────────────────

// ── Per-tool params collapse state ───────────────────────────────────────────

function ToolParamsTable({ params }: { params: Record<string, unknown> }) {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null)
  if (entries.length === 0) return null
  const compact = entries.length <= 4
  return (
    <div className="mt-1 ml-1 border-l border-[rgba(212,175,55,0.15)] pl-2">
      <table className="w-full text-[9px] font-mono">
        <tbody>
          {entries.slice(0, compact ? entries.length : 4).map(([k, v]) => (
            <tr key={k}>
              <td className="text-[rgba(212,175,55,0.55)] pr-2 align-top whitespace-nowrap">{k}</td>
              <td className="text-[rgba(252,226,154,0.75)] break-all">{String(v)}</td>
            </tr>
          ))}
          {!compact && entries.length > 4 && (
            <tr>
              <td colSpan={2} className="text-[rgba(212,175,55,0.35)] pt-0.5">
                +{entries.length - 4} more params
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export function QueryDNAPanel({ steps }: Props) {
  const [collapsed, setCollapsed] = useState(false)
  const [expandedToolParams, setExpandedToolParams] = useState<Set<string>>(new Set())

  // Realigned for new pipeline 2026-05-12 (Gate II W6).
  // The emitter writes step_name='classify' for the planner LLM call (route.ts:393
  // comment preserves the legacy literal for trace UI compat). The 'plan' branch
  // was dead — kept here as a transitional alias for any old trace rows.
  const planStep = steps.find(s => s.step_name === 'classify' || s.step_name === 'plan')

  if (!planStep) {
    return (
      <div className="border-b border-[rgba(212,175,55,0.10)] px-4 py-2.5 bg-[rgba(13,10,5,0.4)]">
        <div className="flex items-center gap-2">
          <Sparkles size={11} className="text-[rgba(212,175,55,0.4)]" />
          <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(212,175,55,0.4)]">Query DNA</span>
          <span className="text-[10px] text-[rgba(212,175,55,0.3)] italic ml-auto">awaiting planner…</span>
        </div>
      </div>
    )
  }

  const ds = planStep.data_summary
  const plan: TraceQueryPlan | undefined = planStep.payload.query_plan
  const toolCalls: TraceToolCallSpec[] | undefined = planStep.payload.tool_calls ?? plan?.tool_calls

  const queryClass = (plan?.query_class ?? ds.query_class ?? '').toLowerCase()
  const classStyle = QUERY_CLASS_STYLE[queryClass] ?? UNKNOWN_CLASS_STYLE

  const confidence = plan?.router_confidence ?? ds.planning_confidence ?? ds.confidence
  const isFallback = confidence === 0 || confidence == null

  const intentSummary = plan?.query_intent_summary
  const planningRationale = plan?.planning_rationale
  const synthesisGuidance = plan?.synthesis_guidance

  const tools = toolCalls && toolCalls.length > 0
    ? toolCalls.map(tc => ({ name: tc.tool_name, priority: tc.priority, reason: tc.reason, params: tc.params }))
    : (plan?.tools_authorized ?? []).map(name => ({ name, priority: undefined, reason: undefined, params: undefined }))

  const domains = plan?.domains ?? []
  const seeds = plan?.graph_seed_hints ?? []
  const planets = plan?.planets ?? []
  const houses = plan?.houses ?? []

  const planningModel = plan?.planning_model_id ?? ds.model
  const planningLatency = plan?.planning_latency_ms ?? planStep.latency_ms

  const forwardLooking = plan?.forward_looking
  const dashaRequired = plan?.dasha_context_required
  const timeWindow = plan?.time_window

  return (
    <div className="border-b border-[rgba(212,175,55,0.10)] bg-[rgba(13,10,5,0.5)] flex-shrink-0">
      {/* Header */}
      <button
        type="button"
        onClick={() => setCollapsed(c => !c)}
        className="w-full flex items-center gap-2 px-4 py-2 hover:bg-[rgba(212,175,55,0.04)] transition-colors"
      >
        <Sparkles size={11} className="text-[rgba(212,175,55,0.6)]" />
        <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(212,175,55,0.65)]">Query DNA</span>

        {/* Class badge always visible (even when collapsed) */}
        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${classStyle.bg} ${classStyle.text} ${classStyle.border}`}>
          {classStyle.label}
        </span>

        {isFallback && (
          <span className="flex items-center gap-1 text-[9px] font-bold px-1.5 py-0.5 rounded border bg-[rgba(220,90,60,0.12)] text-[rgba(240,150,120,0.95)] border-[rgba(230,110,80,0.4)]">
            <AlertTriangle size={9} /> FALLBACK
          </span>
        )}

        {!collapsed && tools.length > 0 && (
          <span className="text-[10px] text-[rgba(212,175,55,0.5)] ml-auto">{tools.length} tools · {fmtMs(planningLatency)}</span>
        )}

        {collapsed && intentSummary && (
          <span className="flex-1 text-[10px] text-[rgba(252,226,154,0.7)] italic truncate ml-2 text-left">
            {intentSummary}
          </span>
        )}

        <span className="ml-auto flex-shrink-0">
          {collapsed
            ? <ChevronDown size={12} className="text-[rgba(212,175,55,0.4)]" />
            : <ChevronUp size={12} className="text-[rgba(212,175,55,0.4)]" />}
        </span>
      </button>

      {/* Body */}
      {!collapsed && (
        <div className="px-4 pb-3 space-y-2">
          {/* Intent summary (B2-only) */}
          {intentSummary && (
            <div className="border-l-2 border-[rgba(212,175,55,0.4)] pl-2.5 py-0.5">
              <div className="text-[9px] font-bold uppercase tracking-[0.12em] text-[rgba(212,175,55,0.4)] mb-0.5">Intent</div>
              <div className="text-[11px] text-[rgba(252,226,154,0.85)] leading-snug">{intentSummary}</div>
            </div>
          )}

          {/* Tools row — I.1: each tool badge has a chevron when params exist */}
          {tools.length > 0 && (
            <div>
              <div className="text-[9px] font-bold uppercase tracking-[0.12em] text-[rgba(212,175,55,0.4)] mb-1">Tools authorized</div>
              <div className="flex flex-col gap-1">
                {tools.map((tool, i) => {
                  const kind = inferToolKind(tool.name)
                  const titleParts: string[] = [tool.name]
                  if (tool.priority) titleParts.push(`priority ${tool.priority}`)
                  if (tool.reason) titleParts.push(tool.reason)
                  const hasParams = tool.params && Object.keys(tool.params).length > 0
                  const paramsExpanded = expandedToolParams.has(`${tool.name}-${i}`)
                  const toggleParams = () => {
                    setExpandedToolParams(prev => {
                      const next = new Set(prev)
                      if (next.has(`${tool.name}-${i}`)) next.delete(`${tool.name}-${i}`)
                      else next.add(`${tool.name}-${i}`)
                      return next
                    })
                  }
                  return (
                    <div key={`${tool.name}-${i}`}>
                      <div className="flex items-center gap-1 flex-wrap">
                        <span
                          title={titleParts.join(' — ')}
                          className={`inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded border ${TOOL_KIND_STYLE[kind]}`}
                        >
                          <span className="font-mono">{tool.name}</span>
                          {tool.priority && (
                            <span className="text-[8px] opacity-60 font-mono" aria-label={`priority ${tool.priority}`}>
                              {priorityDot(tool.priority)}
                            </span>
                          )}
                        </span>
                        {hasParams && (
                          <button
                            type="button"
                            onClick={toggleParams}
                            className="inline-flex items-center gap-0.5 text-[9px] text-[rgba(212,175,55,0.45)] hover:text-[rgba(212,175,55,0.75)] transition-colors"
                            title="Toggle planner params"
                          >
                            {paramsExpanded
                              ? <ChevronDown size={9} />
                              : <ChevronRight size={9} />}
                            <span>params</span>
                          </button>
                        )}
                        {tool.reason && (
                          <span className="text-[9px] text-[rgba(212,175,55,0.4)] italic truncate max-w-[200px]">{tool.reason}</span>
                        )}
                      </div>
                      {hasParams && paramsExpanded && (
                        <ToolParamsTable params={tool.params as Record<string, unknown>} />
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Domains + Graph seeds row */}
          {(domains.length > 0 || seeds.length > 0 || planets.length > 0 || houses.length > 0) && (
            <div className="grid grid-cols-2 gap-3">
              {domains.length > 0 && (
                <div>
                  <div className="text-[9px] font-bold uppercase tracking-[0.12em] text-[rgba(212,175,55,0.4)] mb-1">Domains</div>
                  <div className="flex flex-wrap gap-1">
                    {domains.map(d => (
                      <span key={d} className="text-[10px] px-1.5 py-0.5 rounded bg-[rgba(212,175,55,0.06)] text-[rgba(252,226,154,0.75)] border border-[rgba(212,175,55,0.18)]">
                        {d}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {(seeds.length > 0 || planets.length > 0 || houses.length > 0) && (
                <div>
                  <div className="text-[9px] font-bold uppercase tracking-[0.12em] text-[rgba(212,175,55,0.4)] mb-1">Chart seeds</div>
                  <div className="flex flex-wrap gap-1">
                    {seeds.map(s => (
                      <span key={s} className="text-[10px] px-1.5 py-0.5 rounded bg-[rgba(160,110,220,0.08)] text-[rgba(200,160,240,0.85)] border border-[rgba(170,120,225,0.22)]">
                        {humanizeSeedNode(s)}
                      </span>
                    ))}
                    {planets.filter(p => !seeds.some(s => s.includes(p.toUpperCase()))).map(p => (
                      <span key={`pln-${p}`} className="text-[10px] px-1.5 py-0.5 rounded bg-[rgba(160,110,220,0.06)] text-[rgba(200,160,240,0.7)] border border-[rgba(170,120,225,0.18)]">
                        {p}
                      </span>
                    ))}
                    {houses.filter(h => !seeds.some(s => s === `HSE.${h}`)).map(h => (
                      <span key={`hse-${h}`} className="text-[10px] px-1.5 py-0.5 rounded bg-[rgba(160,110,220,0.06)] text-[rgba(200,160,240,0.7)] border border-[rgba(170,120,225,0.18)]">
                        H{h}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Temporal flags + planning model row */}
          <div className="flex items-center flex-wrap gap-x-3 gap-y-1 text-[10px] pt-1 border-t border-[rgba(212,175,55,0.08)]">
            {forwardLooking && (
              <span className="inline-flex items-center gap-1 text-[rgba(240,170,100,0.8)]">
                <span className="w-1 h-1 rounded-full bg-[rgba(240,170,100,0.6)]" />
                forward-looking
              </span>
            )}
            {dashaRequired && (
              <span className="inline-flex items-center gap-1 text-[rgba(190,150,240,0.8)]">
                <span className="w-1 h-1 rounded-full bg-[rgba(190,150,240,0.6)]" />
                dasha context
              </span>
            )}
            {timeWindow?.start && timeWindow?.end && (
              <span className="text-[rgba(212,175,55,0.5)] font-mono">
                {timeWindow.start} → {timeWindow.end}
              </span>
            )}
            {plan?.expected_output_shape && (
              <span className="text-[rgba(212,175,55,0.5)]">
                shape: <span className="text-[rgba(252,226,154,0.7)]">{plan.expected_output_shape.replace(/_/g, ' ')}</span>
              </span>
            )}
            <span className="ml-auto flex items-center gap-2">
              {confidence != null && (
                <span className={isFallback ? 'text-[rgba(240,150,120,0.85)] font-semibold' : 'text-[rgba(212,175,55,0.55)]'}>
                  confidence {confidence.toFixed(2)}
                </span>
              )}
              {planningModel && (
                <span className="text-[rgba(212,175,55,0.45)] font-mono">
                  {planningModel.replace(/^claude-|^gpt-|^gemini-|^deepseek-/, '')} · {fmtMs(planningLatency)}
                </span>
              )}
            </span>
          </div>

          {/* Rationale + synthesis guidance (B2-only, dimmer) */}
          {(planningRationale || synthesisGuidance) && (
            <div className="space-y-1 pt-1 border-t border-[rgba(212,175,55,0.08)]">
              {planningRationale && (
                <div>
                  <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-[rgba(212,175,55,0.4)] mr-2">Rationale</span>
                  <span className="text-[10px] text-[rgba(252,226,154,0.65)] italic">{planningRationale}</span>
                </div>
              )}
              {synthesisGuidance && (
                <div>
                  <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-[rgba(212,175,55,0.4)] mr-2">Synthesis</span>
                  <span className="text-[10px] text-[rgba(252,226,154,0.65)] italic">{synthesisGuidance}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
