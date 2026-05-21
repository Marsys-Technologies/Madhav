'use client';

/**
 * ConflictPanel.tsx — ICR-S5 stub
 *
 * Renders the Conflict Resolution section on the /performance page.
 * Full panel (with per-patch confirm/reject/escalate UI) ships in PERF-S5.
 */

interface ConflictPanelProps {
  proposedCount: number;
}

export function ConflictPanel({ proposedCount }: ConflictPanelProps) {
  return (
    <section className="rounded-lg border border-border bg-card p-6">
      <h2 className="text-lg font-semibold mb-3">
        Conflict Resolution ({proposedCount} pending)
      </h2>
      {proposedCount === 0 ? (
        <p className="text-muted-foreground text-sm">No pending conflicts.</p>
      ) : (
        <p className="text-muted-foreground text-sm">
          {proposedCount} patch{proposedCount !== 1 ? 'es' : ''} awaiting native review.
          Full conflict panel ships in PERF-S5.
        </p>
      )}
    </section>
  );
}
