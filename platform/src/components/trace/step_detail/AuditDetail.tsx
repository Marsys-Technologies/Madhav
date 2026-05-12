'use client'

/**
 * AuditDetail — Gate II W4 (2026-05-12).
 *
 * Renders audit_events JOIN + citation-gate trace-step signal per the
 * AuditStepMetadata schema. Validator verdict, disclosure tier, B.10/B.11
 * compliance flags, audit-event id.
 */

import type { AuditStepMetadata } from '@/lib/trace/types'
import { Section } from './Section'

interface Props {
  audit: AuditStepMetadata | null
}

function VerdictBadge({ verdict }: { verdict: AuditStepMetadata['validator_verdict'] }) {
  const map: Record<AuditStepMetadata['validator_verdict'], string> = {
    PASS: 'bg-emerald-400/10 text-emerald-400',
    WARN: 'bg-amber-400/10 text-amber-400',
    ERROR: 'bg-red-400/10 text-red-400',
    UNKNOWN: 'bg-zinc-700/30 text-zinc-400',
  }
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase tracking-wide ${map[verdict]}`}>
      {verdict}
    </span>
  )
}

function BoolFlag({ value }: { value: boolean | null }) {
  if (value === null) return <span className="text-muted-foreground">—</span>
  return (
    <span className={value ? 'text-emerald-400' : 'text-amber-400'}>
      {value ? 'compliant' : 'non-compliant'}
    </span>
  )
}

export function AuditDetail({ audit }: Props) {
  if (!audit) {
    return (
      <div data-testid="audit-detail">
        <p className="text-xs text-zinc-500">Audit data not available.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4" data-testid="audit-detail">
      <Section title="Validator verdict">
        <div className="flex items-center gap-2 text-[11px]">
          <VerdictBadge verdict={audit.validator_verdict} />
          <span className="text-muted-foreground">disclosure tier:</span>
          <span className="font-mono text-foreground">{audit.disclosure_tier ?? '—'}</span>
        </div>
      </Section>

      <Section title="Compliance">
        <dl className="grid grid-cols-2 gap-2 text-[11px]">
          <div>
            <dt className="text-muted-foreground">B.10 (no fabricated computation)</dt>
            <dd className="font-mono"><BoolFlag value={audit.b10_compliant} /></dd>
          </div>
          <div>
            <dt className="text-muted-foreground">B.11 (whole-chart-read)</dt>
            <dd className="font-mono"><BoolFlag value={audit.b11_compliant} /></dd>
          </div>
        </dl>
      </Section>

      <Section title="Audit event">
        <dl className="grid grid-cols-2 gap-2 text-[11px]">
          <div>
            <dt className="text-muted-foreground">audit_event_id</dt>
            <dd className="font-mono text-foreground" data-testid="audit-event-id">
              {audit.audit_event_id ?? '—'}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">version</dt>
            <dd className="font-mono text-foreground">{audit.audit_event_version ?? '—'}</dd>
          </div>
        </dl>
      </Section>

      {audit.citation_gate && (
        <Section title="Citation gate">
          <div className="text-[11px]">
            <p>
              <span className="text-muted-foreground">result: </span>
              <VerdictBadge verdict={audit.citation_gate.result} />
            </p>
            {audit.citation_gate.layer1_count != null && (
              <p className="mt-1">
                <span className="text-muted-foreground">layer1_count: </span>
                <span className="font-mono text-foreground">{audit.citation_gate.layer1_count}</span>
              </p>
            )}
            {audit.citation_gate.reason && (
              <p className="mt-1 text-muted-foreground">{audit.citation_gate.reason}</p>
            )}
          </div>
        </Section>
      )}

      {audit.placeholder_note && (
        <p className="text-[10px] text-muted-foreground italic" data-testid="audit-placeholder-note">
          {audit.placeholder_note}
        </p>
      )}
    </div>
  )
}
