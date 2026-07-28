// Fixture: reproduces the exact D1-class defect (brief §5 C.7 / the
// registry_bridge.ts P0-1 bug, parked separately) — a fact array reduced to
// one element via .find() keyed only on fact_category, with no fact_key
// check and no deterministic sort/tiebreak beforehand.
function pickShadbalaTotal(strengthRows: Record<string, unknown>[]) {
  const totalRow = strengthRows.find(r => r['fact_category'] === 'graha_shadbala_total')
  return totalRow
}
