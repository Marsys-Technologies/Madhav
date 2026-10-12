/** Serving-only F-L2 qualification. A stored figure cannot outlive its source.
 * The boolean is measured in the reader's own chart-scoped SQL snapshot.
 * A nonempty source is only availability evidence, not a rebuild/freshness claim. */
export function qualifyStoryConvergence(row: Record<string, unknown>): Record<string, unknown> {
  if (row.convergence_source_available === true) return row
  const reason = row.convergence_source_available === false
    ? 'source_table_empty_for_chart' : 'source_availability_unverified'
  const narrative = row.narrative && typeof row.narrative === 'object' && !Array.isArray(row.narrative)
    ? row.narrative as Record<string, unknown> : {}
  return { ...row, high_convergence_count: null, avg_effective_score: null,
    convergence_null_reason: reason,
    // The writer embeds the count in summary as well as structured fields.
    // Null the unsourced prose; keep chapter identity, themes and citation.
    narrative: { ...narrative, summary: null, high_convergence_count: null,
      avg_effective_score: null, convergence_null_reason: reason },
  }
}
