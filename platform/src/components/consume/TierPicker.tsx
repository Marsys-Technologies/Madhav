'use client'

import { Layers, BookOpen, Zap, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AudienceTier } from '@/lib/prompts/types'

const TIERS: { value: AudienceTier; label: string; icon: LucideIcon; tooltip: string }[] = [
  {
    value: 'super_admin',
    label: 'Deep',
    icon: Layers,
    tooltip: 'Full acharya-grade depth: all layers, full citations, technical Jyotish.',
  },
  {
    value: 'acharya_reviewer',
    label: 'Study',
    icon: BookOpen,
    tooltip: 'Peer-level discussion: explanatory, moderately technical.',
  },
  {
    value: 'client',
    label: 'Brief',
    icon: Zap,
    tooltip: 'Concise, accessible, key insights only.',
  },
]

interface Props {
  tier: AudienceTier
  onChange: (tier: AudienceTier) => void
}

export function TierPicker({ tier, onChange }: Props) {
  return (
    <div
      role="group"
      aria-label="Audience tier"
      className="flex gap-px rounded-md border border-border bg-muted/30 p-0.5"
    >
      {TIERS.map(({ value, label, icon: Icon, tooltip }) => {
        const active = tier === value
        return (
          <button
            key={value}
            type="button"
            onClick={() => onChange(value)}
            title={tooltip}
            aria-pressed={active}
            aria-label={`${label} — ${tooltip}`}
            className={cn(
              'inline-flex items-center gap-1.5 rounded px-2.5 py-1 text-[11px] font-medium transition-colors',
              active
                ? 'bg-[var(--brand-charcoal)] text-[var(--brand-gold)] ring-1 ring-[var(--brand-gold)]'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/30'
            )}
          >
            <Icon size={12} />
            {label}
          </button>
        )
      })}
    </div>
  )
}

export const TIER_LABELS: Record<AudienceTier, string> = {
  super_admin: 'Deep',
  acharya_reviewer: 'Study',
  client: 'Brief',
  public_redacted: 'Public',
}
