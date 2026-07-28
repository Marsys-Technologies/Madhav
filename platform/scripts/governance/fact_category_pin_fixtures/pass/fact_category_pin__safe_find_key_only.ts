// Fixture: fact_key checked in the same predicate WITHOUT a preceding
// .sort(...) — fact_key alone already disambiguates which row can match, so
// this must NOT be flagged (mirrors the Python key-only-safe fixture).
function pickShadbalaRatio(strengthRows: Record<string, unknown>[]) {
  const row = strengthRows.find(
    r => r['fact_category'] === 'graha_shadbala_total' && r['fact_key'] === 'ratio',
  )
  return row
}
