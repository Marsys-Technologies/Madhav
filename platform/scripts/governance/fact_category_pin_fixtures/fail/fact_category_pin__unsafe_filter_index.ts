// Fixture: the .filter(...)[0] variant of the same defect class named
// explicitly in brief §5 C.7 — reduces to one element by fact_category alone.
function pickDignityRow(rows: Record<string, unknown>[]) {
  const row = rows.filter(r => r['fact_category'] === 'graha_dignity_per_varga')[0]
  return row
}
