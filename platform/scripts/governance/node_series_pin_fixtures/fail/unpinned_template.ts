// FAIL fixture: a TypeScript template-literal read of ephemeris_daily with no node-series pin.
export async function latByBody(db: any, date: string, bodies: string[]) {
  const ephResult = await db.query(
    `SELECT body, latitude FROM ephemeris_daily WHERE date = $1 AND ayanamsha_id = 'tropical' AND body = ANY($2)`,
    [date, bodies],
  )
  return ephResult.rows
}
