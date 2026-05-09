'use client'
import * as React from 'react'
import { ObsHero } from './ObsHero'

interface ObsPageShellProps {
  title: string
  subtitle?: string
  headerRight?: React.ReactNode
  /** Optional bottom slot under the hero (advanced filters, secondary tabs). */
  headerBottom?: React.ReactNode
  /** Render the Devanagari accent on the title. */
  devanagari?: boolean
  /** Tone-tinted radial backdrop behind the hero. */
  tone?: 'neutral' | 'good' | 'warn' | 'bad'
  /** Show the live-data dot. */
  live?: boolean
  liveLabel?: string
  children: React.ReactNode
  testId?: string
}

export function ObsPageShell({
  title,
  subtitle,
  headerRight,
  headerBottom,
  devanagari,
  tone,
  live,
  liveLabel,
  children,
  testId,
}: ObsPageShellProps) {
  return (
    <div data-testid={testId} className="obs-shell page-ascend min-h-full">
      <ObsHero
        title={title}
        subtitle={subtitle}
        devanagari={devanagari}
        tone={tone}
        live={live}
        liveLabel={liveLabel}
        right={headerRight}
        bottom={headerBottom}
      />
      <div className="flex flex-col gap-8 p-6">{children}</div>
    </div>
  )
}
