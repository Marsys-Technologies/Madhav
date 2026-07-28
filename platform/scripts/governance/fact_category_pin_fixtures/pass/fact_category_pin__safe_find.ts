// Fixture: the corrected form — fact_category is scoped further by a
// fact_key check AND the array is sorted with a deterministic tiebreak
// immediately before the reduction to one element. Must NOT be flagged.
function pickShadbalaTotal(strengthRows: Record<string, unknown>[]) {
  const totalRow = strengthRows
    .sort((a, b) => String(a['verified_at']).localeCompare(String(b['verified_at'])))
    .find(r => r['fact_category'] === 'graha_shadbala_total' && r['fact_key'] === 'rupa')
  return totalRow
}
