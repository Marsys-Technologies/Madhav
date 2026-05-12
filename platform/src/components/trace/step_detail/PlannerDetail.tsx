'use client'

/**
 * PlannerDetail — Gate II W4 (2026-05-12).
 *
 * Renders the full QueryPlan for the planner stage per D3:
 *   query_class · plan_type · tools_selected · confidence · reasoning
 *
 * Per D2, the planner's own latency is shown in this metadata block (not on
 * the lifecycle node).
 */

import { useState } from 'react'
import type { PlannerStepMetadata } from '@/lib/trace/types'
import { Section } from './Section'
import { RawPayloadDialog } from '../RawPayloadDialog'

interface PlannerDetailProps {
  planner: PlannerStepMetadata | null
}

function fmtMs(ms: number | null | undefined): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

export function PlannerDetail({ planner }: PlannerDetailProps) {
  const [showRaw, setShowRaw] = useState(false)

  if (!planner) {
    return (
      <div data-testid="planner-detail">
        <p className="text-xs text-zinc-500">Planner did not run for this query.</p>
      </div>
    )
  }

  const plan = planner.query_plan
  const queryClass = plan?.query_class ?? '—'
  // plan_type is not a first-class field on TraceQueryPlan; derive from
  // expected_output_shape when present.
  const planType = plan?.expected_output_shape ?? '—'
  const confidence = plan?.router_confidence ?? null
  const reasoning = plan?.planning_rationale ?? null

  return (
    <div className="space-y-6" data-testid="planner-detail">
      <Section title="Plan summary">
        <div className="text-xs text-zinc-300 space-y-1">
          <p>
            <span className="text-zinc-500">query_class: </span>
            <span className="font-mono text-foreground" data-testid="planner-query-class">{queryClass}</span>
          </p>
          <p>
            <span className="text-zinc-500">plan_type: </span>
            <span className="font-mono text-foreground" data-testid="planner-plan-type">{planType}</span>
          </p>
          <p>
            <span className="text-zinc-500">confidence: </span>
            <span className="font-mono text-foreground" data-testid="planner-confidence">
              {confidence != null ? confidence.toFixed(2) : '—'}
            </span>
            {confidence != null && (
              <span className="ml-2 inline-block w-32 h-1.5 bg-zinc-800 rounded overflow-hidden align-middle">
                <span
                  className="block h-full bg-[var(--brand-gold)]"
                  style={{ width: `${Math.max(0, Math.min(1, confidence)) * 100}%` }}
                />
              </span>
            )}
          </p>
          <p>
            <span className="text-zinc-500">latency: </span>
            <span className="font-mono text-foreground">{fmtMs(planner.latency_ms)}</span>
          </p>
          {planner.bundle_summary && (
            <p>
              <span className="text-zinc-500">bundle: </span>
              <span className="text-foreground">{planner.bundle_summary}</span>
            </p>
          )}
        </div>
      </Section>

      <Section title="Tools selected">
        {planner.tool_calls.length === 0 ? (
          <p className="text-xs text-zinc-500">No tools planned.</p>
        ) : (
          <ul className="flex flex-wrap gap-1.5" data-testid="planner-tool-chips">
            {planner.tool_calls.map((tc, i) => (
              <li
                key={i}
                className="text-[11px] font-mono px-2 py-0.5 rounded bg-[rgba(212,175,55,0.10)] text-[#fce29a] border border-[rgba(212,175,55,0.20)]"
              >
                {tc.tool_name}
                <span className="ml-1 text-[10px] text-muted-foreground">·p{tc.priority}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      {reasoning && (
        <Section title="Reasoning">
          <details>
            <summary className="cursor-pointer text-xs text-zinc-400 hover:text-zinc-200">
              Show planner reasoning
            </summary>
            <p className="mt-2 text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed">
              {reasoning}
            </p>
          </details>
        </Section>
      )}

      <Section title="Raw plan">
        {plan ? (
          <div>
            <pre className="text-xs text-zinc-300 font-mono bg-[oklch(0.08_0.01_70)] rounded-lg p-3 max-h-[300px] overflow-y-auto whitespace-pre-wrap break-words">
              {JSON.stringify(plan, null, 2)}
            </pre>
            <button
              onClick={() => setShowRaw(true)}
              className="mt-2 text-xs text-zinc-500 hover:text-zinc-300"
            >
              View raw
            </button>
          </div>
        ) : (
          <p className="text-xs text-zinc-500">No raw plan available.</p>
        )}
      </Section>

      {showRaw && (
        <RawPayloadDialog
          title="QueryPlan"
          payload={plan}
          onClose={() => setShowRaw(false)}
        />
      )}
    </div>
  )
}
