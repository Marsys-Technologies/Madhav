'use client';

/**
 * ConflictPanel.tsx — PERF-S5 full implementation
 *
 * Renders the Conflict Resolution section on the /performance page.
 * Fetches proposed/resolved/rejected patches from GET /api/icr/patches,
 * and exposes Confirm / Reject / Escalate actions via POST /api/icr/confirm.
 */

import * as React from 'react';

interface PatchSummary {
  filename: string;
  conflict_id: string;
  signal_ids_affected: string[];
  patch_description: string;
  authored_on: string;
  before: string;
  after: string;
  status: string;
}

interface PatchesResponse {
  proposed: PatchSummary[];
  resolved: PatchSummary[];
  rejected: PatchSummary[];
}

export function ConflictPanel() {
  const [pending, setPending] = React.useState<PatchSummary[]>([]);
  const [history, setHistory] = React.useState<PatchSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  async function fetchPatches() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/icr/patches');
      if (!res.ok) {
        setError(`Failed to load patches: ${res.statusText}`);
        return;
      }
      const data: PatchesResponse = await res.json();
      setPending(data.proposed ?? []);
      setHistory([...(data.resolved ?? []), ...(data.rejected ?? [])]);
    } catch (e) {
      setError(`Network error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    void fetchPatches();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleAction(
    filename: string,
    action: 'confirm' | 'reject' | 'escalate',
  ) {
    let reason: string | undefined;
    if (action === 'reject' || action === 'escalate') {
      reason = window.prompt(`Reason for ${action} (optional):`) ?? undefined;
    }
    try {
      const res = await fetch('/api/icr/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patch_file: filename, action, reason }),
      });
      if (res.ok) {
        await fetchPatches(); // refresh both tables
      } else {
        setError(`Failed to ${action}: ${res.statusText}`);
      }
    } catch (e) {
      setError(`Network error on ${action}: ${e instanceof Error ? e.message : String(e)}`);
    }
  }

  return (
    <section className="rounded-lg border border-border bg-card p-6 space-y-6">
      <h2 className="text-lg font-semibold">
        Conflict Resolution — Pending ({pending.length})
      </h2>

      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      {/* ── Pending table ──────────────────────────────────────────────────── */}
      {loading ? (
        <p className="text-muted-foreground text-sm">Loading…</p>
      ) : pending.length === 0 ? (
        <p className="text-muted-foreground text-sm">No pending conflicts.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="pb-2 pr-4 font-medium">Conflict ID</th>
                <th className="pb-2 pr-4 font-medium">Signals Affected</th>
                <th className="pb-2 pr-4 font-medium">Description</th>
                <th className="pb-2 pr-4 font-medium">Authored</th>
                <th className="pb-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pending.map((patch) => (
                <tr
                  key={patch.filename}
                  className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                >
                  <td className="py-3 pr-4 font-mono text-xs">{patch.conflict_id}</td>
                  <td className="py-3 pr-4 font-mono text-xs">
                    {patch.signal_ids_affected.join(', ')}
                  </td>
                  <td className="py-3 pr-4 max-w-xs">{patch.patch_description}</td>
                  <td className="py-3 pr-4 text-muted-foreground">{patch.authored_on}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => void handleAction(patch.filename, 'confirm')}
                        className="rounded border px-2 py-1 text-xs font-medium transition-colors border-emerald-500/40 text-emerald-600 hover:bg-emerald-500/10"
                      >
                        Confirm
                      </button>
                      <button
                        onClick={() => void handleAction(patch.filename, 'reject')}
                        className="rounded border px-2 py-1 text-xs font-medium transition-colors border-red-500/40 text-red-600 hover:bg-red-500/10"
                      >
                        Reject
                      </button>
                      <button
                        onClick={() => void handleAction(patch.filename, 'escalate')}
                        className="rounded border px-2 py-1 text-xs font-medium transition-colors border-amber-500/40 text-amber-600 hover:bg-amber-500/10"
                      >
                        Escalate
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── History table ─────────────────────────────────────────────────── */}
      <div>
        <h2 className="text-base font-semibold mb-3">History</h2>
        {!loading && history.length === 0 ? (
          <p className="text-muted-foreground text-sm">No history.</p>
        ) : !loading ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium">Conflict ID</th>
                  <th className="pb-2 pr-4 font-medium">Signals</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map((patch) => (
                  <tr
                    key={patch.filename}
                    className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                  >
                    <td className="py-3 pr-4 font-mono text-xs">{patch.conflict_id}</td>
                    <td className="py-3 pr-4 font-mono text-xs">
                      {patch.signal_ids_affected.join(', ')}
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${
                          patch.status === 'RESOLVED'
                            ? 'bg-emerald-500/15 text-emerald-600'
                            : patch.status === 'REJECTED'
                              ? 'bg-red-500/15 text-red-600'
                              : 'bg-amber-500/15 text-amber-600'
                        }`}
                      >
                        {patch.status.toLowerCase()}
                      </span>
                    </td>
                    <td className="py-3 text-muted-foreground">{patch.authored_on}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </section>
  );
}
