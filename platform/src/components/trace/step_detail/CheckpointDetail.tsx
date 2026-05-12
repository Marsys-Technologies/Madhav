'use client'

/**
 * CheckpointDetail — Gate II W4 (2026-05-12).
 *
 * Renders the per-checkpoint metadata for 4.5 / 5.5 / 8.5. Per D1: dimmed
 * treatment when the checkpoint did not run.
 */

import type { CheckpointStepMetadata } from '@/lib/trace/types'
import { Section } from './Section'

interface Props {
  checkpoint: CheckpointStepMetadata | null
}

function fmtMs(ms: number | null | undefined): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

const STAGE_LABEL: Record<CheckpointStepMetadata['stage'], string> = {
  checkpoint_4_5: 'Checkpoint 4.5',
  checkpoint_5_5: 'Checkpoint 5.5',
  checkpoint_8_5: 'Checkpoint 8.5',
}

export function CheckpointDetail({ checkpoint }: Props) {
  if (!checkpoint) {
    return (
      <div data-testid="checkpoint-detail">
        <p className="text-xs text-zinc-500">Checkpoint not found.</p>
      </div>
    )
  }

  return (
    <div
      className={`space-y-4 ${checkpoint.ran ? '' : 'opacity-70'}`}
      data-testid={`checkpoint-detail-${checkpoint.stage}`}
    >
      <Section title={STAGE_LABEL[checkpoint.stage]}>
        <dl className="grid grid-cols-2 gap-2 text-[11px]">
          <div>
            <dt className="text-muted-foreground">ran</dt>
            <dd className="font-mono text-foreground">{checkpoint.ran ? 'yes' : 'no'}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">enabled</dt>
            <dd className="font-mono text-foreground">
              {checkpoint.enabled == null ? '—' : checkpoint.enabled ? 'yes' : 'no'}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">verdict</dt>
            <dd className="font-mono text-foreground">{checkpoint.verdict ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">latency</dt>
            <dd className="font-mono text-foreground">{fmtMs(checkpoint.latency_ms)}</dd>
          </div>
        </dl>
      </Section>
      {checkpoint.notes && (
        <p className="text-[10px] text-muted-foreground italic">{checkpoint.notes}</p>
      )}
    </div>
  )
}
