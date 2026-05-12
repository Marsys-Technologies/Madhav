'use client'

import * as React from 'react'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'

// W11: dynamic import insulates Gate I from Gate II's evolving TracePanel surface.
// If the import fails or the prop contract has shifted, the fallback path
// (link to /audit/[query_id]) is rendered — counts as wired per AC.8.
const TracePanel = dynamic<{ queryId: string | null }>(
  () =>
    import('@/components/trace/TracePanel')
      .then((m) => {
        const cmp =
          (m as Record<string, unknown>).TracePanel ??
          (m as { default?: unknown }).default
        return { default: cmp as React.ComponentType<{ queryId: string | null }> }
      })
      .catch(() => ({ default: (() => null) as React.ComponentType<{ queryId: string | null }> })),
  { ssr: false }
)

interface Props {
  open: boolean
  queryId: string | null
  onOpenChange: (open: boolean) => void
}

export function TracePanelLauncher({ open, queryId, onOpenChange }: Props) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-3xl">
        <SheetHeader>
          <SheetTitle className="text-sm">Trace — {queryId ?? '(none)'}</SheetTitle>
        </SheetHeader>
        <div className="mt-4 max-h-[calc(100vh-6rem)] overflow-auto">
          {queryId ? (
            <React.Suspense
              fallback={<div className="text-xs text-muted-foreground">Loading trace…</div>}
            >
              <TraceOrFallback queryId={queryId} />
            </React.Suspense>
          ) : (
            <div className="text-xs text-muted-foreground">Select a row to view its trace.</div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}

function TraceOrFallback({ queryId }: { queryId: string }) {
  const [failed, setFailed] = React.useState(false)
  if (failed) {
    return (
      <div className="text-xs text-muted-foreground">
        Trace unavailable in this view.{' '}
        <Link href={`/audit/${queryId}`} className="text-foreground underline">
          Open audit detail →
        </Link>
      </div>
    )
  }
  try {
    return (
      <ErrorBoundary onError={() => setFailed(true)}>
        <TracePanel queryId={queryId} />
      </ErrorBoundary>
    )
  } catch {
    return (
      <div className="text-xs text-muted-foreground">
        Trace unavailable —{' '}
        <Link href={`/audit/${queryId}`} className="text-foreground underline">
          see /audit/{queryId}
        </Link>
      </div>
    )
  }
}

class ErrorBoundary extends React.Component<
  { children: React.ReactNode; onError: () => void },
  { hasError: boolean }
> {
  state = { hasError: false }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  componentDidCatch() {
    this.props.onError()
  }
  render() {
    if (this.state.hasError) return null
    return this.props.children
  }
}
