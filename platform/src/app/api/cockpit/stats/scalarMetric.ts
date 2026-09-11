type ScalarMetricOptions = {
  nullable?: boolean
}

/**
 * Read the one scalar returned by an asset_registry metric query.
 *
 * Registry SQL normally aliases its value as `count` or `size`, but PostgreSQL
 * names an unaliased compound expression `?column?`. A single-column result is
 * still unambiguous and must not be converted to a false zero merely because
 * its column label differs. Multi-column or malformed results fail closed.
 */
export function readSqlScalarMetric(
  row: Record<string, unknown> | undefined,
  preferredAlias: string,
  options: ScalarMetricOptions = {},
): number | null {
  if (!row) throw new Error(`Metric query for ${preferredAlias} returned no row.`)

  const keys = Object.keys(row)
  const hasPreferredAlias = Object.prototype.hasOwnProperty.call(row, preferredAlias)
  if (!hasPreferredAlias && keys.length !== 1) {
    throw new Error(`Metric query expected alias ${preferredAlias} or exactly one result column.`)
  }

  const raw = hasPreferredAlias ? row[preferredAlias] : row[keys[0]]
  if (raw == null) {
    if (options.nullable) return null
    throw new Error(`Metric query for ${preferredAlias} returned null.`)
  }

  const value = typeof raw === 'bigint'
    ? Number(raw)
    : typeof raw === 'number'
      ? raw
      : typeof raw === 'string' && /^\d+$/.test(raw.trim())
        ? Number(raw.trim())
        : Number.NaN

  if (!Number.isSafeInteger(value) || value < 0) {
    throw new Error(`Metric query for ${preferredAlias} must return a non-negative safe integer.`)
  }
  return value
}
