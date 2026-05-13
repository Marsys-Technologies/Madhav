export function EmptyRightRail() {
  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold text-foreground">Recent Changes</h3>
        <p className="mt-2 text-xs text-muted-foreground">
          No edits yet — write side lands in CP.2.
        </p>
      </div>
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold text-foreground">Health Status</h3>
        <p className="mt-2 text-xs text-muted-foreground">
          Health probes start in CP.4.
        </p>
      </div>
    </div>
  )
}
