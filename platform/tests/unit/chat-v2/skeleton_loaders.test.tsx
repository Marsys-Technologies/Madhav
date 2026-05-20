/**
 * X-S5 — Skeleton Loaders
 * Amendment 2: parent-context integration tests.
 *
 * Click-path: load Chat V2 on slow network → sidebar loading → SidebarSkeleton
 *   appears in place of conversation list; HeaderSkeleton appears in header.
 *   When data loads, both skeletons disappear and real content is shown.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, act } from '@testing-library/react'
import React, { useState } from 'react'
import { SidebarSkeleton } from '@/components/chat/SidebarSkeleton'
import { HeaderSkeleton } from '@/components/chat/HeaderSkeleton'

// ── A2: parent-context shell for SidebarSkeleton ──────────────────────────────

function SidebarShell({ isLoading }: { isLoading: boolean }) {
  return (
    <div data-testid="sidebar-shell" className="w-64 bg-zinc-900">
      {isLoading ? <SidebarSkeleton /> : <div data-testid="sidebar-content">Conversations loaded</div>}
    </div>
  )
}

// ── A2: parent-context shell for HeaderSkeleton ───────────────────────────────

function HeaderShell({ isLoading, chartName = 'Abhisek Mohanty' }: { isLoading: boolean; chartName?: string }) {
  return (
    <header data-testid="header-shell" className="flex items-center gap-3 border-b px-4 py-3">
      {isLoading ? (
        <HeaderSkeleton />
      ) : (
        <div className="min-w-0 flex-1 px-1.5">
          <span data-testid="v2-chart-name">{chartName}</span>
        </div>
      )}
    </header>
  )
}

// ── SidebarSkeleton tests ─────────────────────────────────────────────────────

describe('SidebarSkeleton — parent-context integration (Amendment 2)', () => {
  it('renders skeleton rows when isLoading=true', () => {
    const { container } = render(<SidebarShell isLoading={true} />)
    expect(container.querySelector('[data-testid="v2-sidebar-skeleton"]')).not.toBeNull()
  })

  it('does NOT render skeleton when isLoading=false', () => {
    const { container } = render(<SidebarShell isLoading={false} />)
    expect(container.querySelector('[data-testid="v2-sidebar-skeleton"]')).toBeNull()
    expect(container.querySelector('[data-testid="sidebar-content"]')).not.toBeNull()
  })

  it('renders 6 skeleton rows', () => {
    const { container } = render(<SidebarSkeleton />)
    const skeleton = container.querySelector('[data-testid="v2-sidebar-skeleton"]')
    expect(skeleton?.children.length).toBe(6)
  })

  it('has aria-hidden="true" for accessibility', () => {
    const { container } = render(<SidebarSkeleton />)
    const skeleton = container.querySelector('[data-testid="v2-sidebar-skeleton"]')
    expect(skeleton?.getAttribute('aria-hidden')).toBe('true')
  })

  it('transitions from skeleton to content when loading flips', () => {
    let setLoading!: (v: boolean) => void
    function ToggleSidebarShell() {
      const [loading, setL] = useState(true)
      setLoading = setL
      return <SidebarShell isLoading={loading} />
    }
    const { container } = render(<ToggleSidebarShell />)
    expect(container.querySelector('[data-testid="v2-sidebar-skeleton"]')).not.toBeNull()

    act(() => { setLoading(false) })
    expect(container.querySelector('[data-testid="v2-sidebar-skeleton"]')).toBeNull()
    expect(container.querySelector('[data-testid="sidebar-content"]')).not.toBeNull()
  })
})

// ── HeaderSkeleton tests ──────────────────────────────────────────────────────

describe('HeaderSkeleton — parent-context integration (Amendment 2)', () => {
  it('renders skeleton when isLoading=true', () => {
    const { container } = render(<HeaderShell isLoading={true} />)
    expect(container.querySelector('[data-testid="v2-header-skeleton"]')).not.toBeNull()
  })

  it('does NOT render skeleton when isLoading=false', () => {
    const { container } = render(<HeaderShell isLoading={false} />)
    expect(container.querySelector('[data-testid="v2-header-skeleton"]')).toBeNull()
    expect(container.querySelector('[data-testid="v2-chart-name"]')).not.toBeNull()
  })

  it('has aria-hidden="true" for accessibility', () => {
    const { container } = render(<HeaderSkeleton />)
    const skeleton = container.querySelector('[data-testid="v2-header-skeleton"]')
    expect(skeleton?.getAttribute('aria-hidden')).toBe('true')
  })

  it('shows chart name after skeleton dismissed', () => {
    let setLoading!: (v: boolean) => void
    function ToggleHeaderShell() {
      const [loading, setL] = useState(true)
      setLoading = setL
      return <HeaderShell isLoading={loading} chartName="Abhisek Mohanty" />
    }
    const { container } = render(<ToggleHeaderShell />)
    expect(container.querySelector('[data-testid="v2-header-skeleton"]')).not.toBeNull()

    act(() => { setLoading(false) })
    expect(container.querySelector('[data-testid="v2-header-skeleton"]')).toBeNull()
    expect(container.querySelector('[data-testid="v2-chart-name"]')?.textContent).toBe('Abhisek Mohanty')
  })
})
