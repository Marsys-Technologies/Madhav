/**
 * _report.ts — shared PASS/FAIL/QUARANTINED/SKIPPED/WARN result type + printer for the
 * ṢAḌ-DARŚANA W0.6 gate scripts in this directory. Mirrors the exit-code discipline
 * already established repo-wide (TAP-9: "an absent oracle must be declared, never
 * silently passed"; `platform/scripts/census/elev_gates/_report.ts` is the direct
 * precedent) — reimplemented locally for the same cross-manifest-isolation reason
 * documented in `_mcp_client.ts`'s header.
 *
 * Exit codes (CI-consumable):
 *   0 — every result PASS or SKIPPED/QUARANTINED/WARN (no live FAIL).
 *   1 — at least one FAIL.
 *   2 — the battery itself could not run at all (see individual scripts' `main()`).
 */

export type GateStatus = 'PASS' | 'FAIL' | 'QUARANTINED' | 'SKIPPED' | 'WARN'

export type GateResult = {
  id: string
  title: string
  status: GateStatus
  detail: string
}

export function printGateReport(battery: string, results: GateResult[], skipReason: string | null = null): number {
  const counts = { PASS: 0, FAIL: 0, QUARANTINED: 0, SKIPPED: 0, WARN: 0 }
  for (const r of results) counts[r.status]++
  const report = {
    battery,
    generated_at: new Date().toISOString(),
    skip_reason: skipReason,
    counts,
    results,
  }
  console.log(JSON.stringify(report, null, 2))
  console.error(
    `\n[${battery}] PASS=${counts.PASS} FAIL=${counts.FAIL} QUARANTINED=${counts.QUARANTINED} SKIPPED=${counts.SKIPPED} WARN=${counts.WARN}` +
      (skipReason ? ` — SKIP REASON: ${skipReason}` : ''),
  )
  return counts.FAIL > 0 ? 1 : 0
}
