'use client'

/**
 * SynthesisReceipt — TRACE-6 (W2-TRACE-B).
 *
 * Receipt-style summary of the synthesis call: model + temperature, input
 * and output tokens, cost, B.3 compliance status, and a citation breakdown
 * (verified vs. leaked-from-training-data). Surfaces a leak banner if any
 * Layer-2 leakage is detected.
 *
 * UI-only: hydrated by parent on `synthesis_done` SSE event.
 */

import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'

export interface CitationValidationSummary {
  gate_result: 'PASS' | 'WARN' | 'ERROR'
  layer1_count: number
  layer2_verified: number
  layer2_leaked: number
  gate_reason: string
}

interface SynthesisReceiptProps {
  synthesis_model_id: string
  synthesis_temperature: number
  input_tokens: number
  output_tokens: number
  cost_usd: number | null
  citation_validation: CitationValidationSummary | null
  b3_compliant: boolean
  isLoading: boolean
  /** P4 D.4.3 step C — populated from trace payload when available; row hidden if absent. */
  planning_model_id?: string | null
  planning_latency_ms?: number | null
  planning_cost_usd?: number | null
}

function fmtTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

function fmtCost(usd: number | null): string {
  if (usd == null) return '—'
  if (usd < 0.01) return `$${usd.toFixed(4)}`
  return `$${usd.toFixed(2)}`
}

function FieldSkeleton() {
  return (
    <div className="h-5 w-full rounded bg-[rgba(212,175,55,0.06)] animate-pulse" />
  )
}

function GateBadge({
  gateResult,
}: {
  gateResult: 'PASS' | 'WARN' | 'ERROR'
}) {
  if (gateResult === 'PASS') {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-bold bg-[rgba(140,210,170,0.10)] text-[rgba(140,210,170,0.95)] border-[rgba(120,190,150,0.4)]">
        <CheckCircle2 size={10} />
        B.3 PASS
      </span>
    )
  }
  if (gateResult === 'WARN') {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-bold bg-[rgba(220,140,60,0.12)] text-[rgba(240,170,100,0.95)] border-[rgba(230,150,80,0.4)]">
        <AlertTriangle size={10} />
        B.3 WARN
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-bold bg-[rgba(220,90,60,0.12)] text-[rgba(240,150,120,0.95)] border-[rgba(230,110,80,0.4)]">
      <XCircle size={10} />
      B.3 ERROR
    </span>
  )
}

export function SynthesisReceipt({
  synthesis_model_id,
  synthesis_temperature,
  input_tokens,
  output_tokens,
  cost_usd,
  citation_validation,
  b3_compliant,
  isLoading,
  planning_model_id,
  planning_latency_ms,
  planning_cost_usd,
}: SynthesisReceiptProps) {
  if (isLoading) {
    return (
      <div className="px-4 py-3 space-y-2">
        <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(212,175,55,0.6)]">
          Synthesis Receipt
        </div>
        <FieldSkeleton />
        <FieldSkeleton />
        <FieldSkeleton />
      </div>
    )
  }

  const cv = citation_validation
  const showLeakBanner = cv != null && cv.layer2_leaked > 0
  // Derive a gate badge: prefer the explicit citation_validation gate; fall
  // back to the b3_compliant flag for synthesis runs that ran before
  // citation validation completed.
  const gateForBadge: 'PASS' | 'WARN' | 'ERROR' = cv
    ? cv.gate_result
    : b3_compliant
      ? 'PASS'
      : 'ERROR'

  return (
    <div className="px-4 py-3 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(212,175,55,0.6)]">
          Synthesis Receipt
        </span>
        <GateBadge gateResult={gateForBadge} />
      </div>

      <div className="rounded border border-[rgba(212,175,55,0.15)] bg-[rgba(13,10,5,0.5)] divide-y divide-[rgba(212,175,55,0.08)]">
        {/* Planner row — P4 D.4.3 step C; rendered only when planner data present */}
        {planning_model_id && (
          <div className="flex items-center gap-2 px-3 py-2">
            <span className="text-[10px] font-semibold text-[rgba(212,175,55,0.55)] uppercase tracking-[0.12em] w-20">
              Planner
            </span>
            <span className="text-[11px] text-[rgba(252,226,154,0.85)] font-mono">
              {planning_model_id}
            </span>
            <span className="ml-auto text-[10px] text-[rgba(244,209,96,0.7)]">
              {planning_latency_ms != null ? `${(planning_latency_ms / 1000).toFixed(1)}s` : ''}
              {planning_cost_usd != null ? `  ${fmtCost(planning_cost_usd)}` : ''}
            </span>
          </div>
        )}
        {/* Model + temperature */}
        <div className="flex items-center gap-2 px-3 py-2">
          <span className="text-[10px] font-semibold text-[rgba(212,175,55,0.55)] uppercase tracking-[0.12em] w-20">
            Model
          </span>
          <span className="text-[11px] text-[rgba(252,226,154,0.95)] font-mono">
            {synthesis_model_id}
          </span>
          <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded border border-[rgba(212,175,55,0.25)] bg-[rgba(212,175,55,0.06)] text-[rgba(244,209,96,0.85)]">
            T={synthesis_temperature.toFixed(2)}
          </span>
        </div>

        {/* Tokens */}
        <div className="flex items-center gap-3 px-3 py-2 text-[10px]">
          <span className="font-semibold text-[rgba(212,175,55,0.55)] uppercase tracking-[0.12em] w-20">
            Tokens
          </span>
          <span className="text-[rgba(212,175,55,0.7)]">
            in{' '}
            <span className="text-[rgba(252,226,154,0.95)] font-semibold">
              {fmtTokens(input_tokens)}
            </span>
          </span>
          <span className="text-[rgba(212,175,55,0.7)]">
            out{' '}
            <span className="text-[rgba(252,226,154,0.95)] font-semibold">
              {fmtTokens(output_tokens)}
            </span>
          </span>
          <span className="ml-auto text-[rgba(244,209,96,0.85)] font-semibold">
            {fmtCost(cost_usd)}
          </span>
        </div>

        {/* Citations */}
        <div className="flex items-center gap-3 px-3 py-2 text-[10px]">
          <span className="font-semibold text-[rgba(212,175,55,0.55)] uppercase tracking-[0.12em] w-20">
            Citations
          </span>
          {cv ? (
            <>
              <span className="text-[rgba(212,175,55,0.7)]">
                total{' '}
                <span className="text-[rgba(252,226,154,0.95)] font-semibold">
                  {cv.layer1_count}
                </span>
              </span>
              <span className="text-[rgba(140,210,170,0.85)]">
                verified{' '}
                <span className="font-semibold">{cv.layer2_verified}</span>
              </span>
              <span
                className={
                  cv.layer2_leaked > 0
                    ? 'text-[rgba(240,150,120,0.95)] font-semibold'
                    : 'text-[rgba(212,175,55,0.55)]'
                }
              >
                leaked{' '}
                <span className="font-semibold">{cv.layer2_leaked}</span>
              </span>
            </>
          ) : (
            <span className="italic text-[rgba(212,175,55,0.45)]">
              not validated
            </span>
          )}
        </div>

        {/* Gate reason */}
        {cv?.gate_reason && (
          <div className="px-3 py-2 text-[10px] text-[rgba(212,175,55,0.6)] italic">
            {cv.gate_reason}
          </div>
        )}
      </div>

      {/* Leak banner */}
      {showLeakBanner && (
        <div className="flex items-start gap-2 px-3 py-2 rounded border bg-[rgba(220,140,60,0.10)] text-[rgba(240,170,100,0.95)] border-[rgba(220,140,60,0.4)]">
          <AlertTriangle size={12} className="mt-0.5 flex-shrink-0" />
          <div className="text-[10px] leading-relaxed">
            <div className="font-semibold">Training data leak detected</div>
            <div className="opacity-80">
              {cv!.layer2_leaked} citation{cv!.layer2_leaked === 1 ? '' : 's'}{' '}
              traced to model training data rather than the curated corpus.
              Review before relying on the answer.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
