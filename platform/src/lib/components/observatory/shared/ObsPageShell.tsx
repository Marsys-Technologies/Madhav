'use client'
import * as React from 'react'

interface ObsPageShellProps {
  title: string
  subtitle?: string
  headerRight?: React.ReactNode
  children: React.ReactNode
  testId?: string
}

export function ObsPageShell({ title, subtitle, headerRight, children, testId }: ObsPageShellProps) {
  return (
    <div
      data-testid={testId}
      className="min-h-full bg-[var(--brand-charcoal,oklch(0.10_0.012_70))]"
    >
      {/* Page header */}
      <div className="border-b border-[rgba(212,175,55,0.10)] px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="font-heading text-xl font-semibold text-[#fce29a] tracking-wide">
              {title}
            </h1>
            {subtitle && (
              <p className="mt-0.5 text-xs text-[rgba(212,175,55,0.45)]">{subtitle}</p>
            )}
          </div>
          {headerRight && <div>{headerRight}</div>}
        </div>
      </div>

      {/* Page content */}
      <div className="flex flex-col gap-8 p-6">
        {children}
      </div>
    </div>
  )
}
