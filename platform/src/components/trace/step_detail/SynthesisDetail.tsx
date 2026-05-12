'use client'

/**
 * SynthesisDetail — Gate II W4 (2026-05-12).
 *
 * Discriminated render per D6:
 *   single_model → one LLM-call row with model / token counts / latency / finish-reason
 *   panel        → N panelist rows + an aggregator row
 *
 * Per-step latency shown in the metadata block (D2).
 */

import type { SynthesisStepMetadata } from '@/lib/trace/types'
import { Section } from './Section'

interface SynthesisDetailProps {
  synthesis: SynthesisStepMetadata | null
}

function fmtMs(ms: number | null | undefined): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

function fmtCount(n: number | null | undefined): string {
  if (n == null) return '—'
  return n.toLocaleString()
}

function LlmCallRow({
  label,
  model,
  inputTokens,
  outputTokens,
  latencyMs,
  testid,
}: {
  label: string
  model: string | null
  inputTokens: number | null
  outputTokens: number | null
  latencyMs: number | null
  testid?: string
}) {
  return (
    <div
      data-testid={testid}
      className="rounded border border-[rgba(212,175,55,0.10)] bg-[oklch(0.10_0.005_70)] p-3"
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[11px] font-semibold text-[#fce29a]">{label}</span>
        <span className="ml-auto text-[10px] text-muted-foreground">{fmtMs(latencyMs)}</span>
      </div>
      <dl className="grid grid-cols-3 gap-2 text-[11px]">
        <div>
          <dt className="text-muted-foreground">model</dt>
          <dd className="font-mono text-foreground">{model ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">tokens in</dt>
          <dd className="font-mono text-foreground">{fmtCount(inputTokens)}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">tokens out</dt>
          <dd className="font-mono text-foreground">{fmtCount(outputTokens)}</dd>
        </div>
      </dl>
    </div>
  )
}

export function SynthesisDetail({ synthesis }: SynthesisDetailProps) {
  if (!synthesis) {
    return (
      <div data-testid="synthesis-detail">
        <p className="text-xs text-zinc-500">Synthesis did not run for this query.</p>
      </div>
    )
  }

  if (synthesis.mode === 'panel') {
    return (
      <div className="space-y-4" data-testid="synthesis-detail" data-mode="panel">
        <Section title="Panel synthesis">
          {synthesis.panel_trace_pending && (
            <p className="text-[11px] text-amber-400/80 mb-3" data-testid="panel-pending-note">
              Panel-mode trace shape pending follow-up gate; per-panelist rows not yet emitted.
            </p>
          )}
          {synthesis.panelists.length > 0 && (
            <div className="space-y-2 mb-3" data-testid="panel-panelists">
              {synthesis.panelists.map((p, i) => (
                <LlmCallRow
                  key={i}
                  testid={`panel-panelist-${p.panelist_id}`}
                  label={`Panelist · ${p.panelist_id}`}
                  model={p.model}
                  inputTokens={p.input_tokens}
                  outputTokens={p.output_tokens}
                  latencyMs={p.latency_ms}
                />
              ))}
            </div>
          )}
          {synthesis.aggregator ? (
            <LlmCallRow
              testid="panel-aggregator"
              label="Aggregator"
              model={synthesis.aggregator.model}
              inputTokens={synthesis.aggregator.input_tokens}
              outputTokens={synthesis.aggregator.output_tokens}
              latencyMs={synthesis.aggregator.latency_ms}
            />
          ) : (
            <LlmCallRow
              testid="panel-aggregator"
              label="Aggregator (combined)"
              model={null}
              inputTokens={null}
              outputTokens={null}
              latencyMs={synthesis.latency_ms}
            />
          )}
        </Section>
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="synthesis-detail" data-mode="single_model">
      <Section title="Synthesis (single model)">
        <LlmCallRow
          testid="synthesis-llm-call"
          label="LLM call"
          model={synthesis.model}
          inputTokens={synthesis.input_tokens}
          outputTokens={synthesis.output_tokens}
          latencyMs={synthesis.latency_ms}
        />
      </Section>

      <Section title="Quality signals">
        <dl className="grid grid-cols-2 gap-2 text-[11px]">
          <div>
            <dt className="text-muted-foreground">citations</dt>
            <dd className="font-mono text-foreground">{fmtCount(synthesis.citation_count)}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">output_shape_compliant</dt>
            <dd className="font-mono text-foreground">
              {synthesis.output_shape_compliant == null
                ? '—'
                : synthesis.output_shape_compliant ? 'yes' : 'no'}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">provider</dt>
            <dd className="font-mono text-foreground">{synthesis.provider ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">temperature</dt>
            <dd className="font-mono text-foreground">
              {synthesis.temperature != null ? synthesis.temperature.toFixed(2) : '—'}
            </dd>
          </div>
        </dl>
      </Section>

      {synthesis.context_assembly_short_circuit?.short_circuited && (
        <Section title="Context assembly (short-circuit)">
          <div className="text-[11px] text-muted-foreground">
            Skipped synthesis context-assembly LLM: bundle size{' '}
            <span className="font-mono text-foreground">
              {synthesis.context_assembly_short_circuit.total_token_estimate}
            </span>{' '}
            below threshold{' '}
            <span className="font-mono text-foreground">
              {synthesis.context_assembly_short_circuit.threshold}
            </span>
            {synthesis.context_assembly_short_circuit.reason
              ? ` (${synthesis.context_assembly_short_circuit.reason})`
              : ''}
          </div>
        </Section>
      )}

      {synthesis.reasoning_trace && (
        <Section title="Reasoning trace">
          <details>
            <summary className="cursor-pointer text-xs text-zinc-400 hover:text-zinc-200">
              Show DeepSeek R1 think block
            </summary>
            <pre className="mt-2 text-[11px] text-zinc-300 whitespace-pre-wrap leading-relaxed">
              {synthesis.reasoning_trace}
            </pre>
          </details>
        </Section>
      )}

      {synthesis.prompt_preview && (
        <Section title="Prompt preview">
          <pre className="text-[11px] text-zinc-300 font-mono bg-[oklch(0.08_0.01_70)] rounded-lg p-3 max-h-[300px] overflow-y-auto whitespace-pre-wrap break-words">
            {synthesis.prompt_preview}
          </pre>
        </Section>
      )}
    </div>
  )
}
