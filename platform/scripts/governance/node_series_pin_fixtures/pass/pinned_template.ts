// PASS fixture: pinned template literal, and an exempt one.
export async function a(db: any, date: string) {
  return db.query(
    `SELECT body, tropical_longitude FROM ephemeris_daily WHERE date = $1 AND (body NOT IN ('Rahu','Ketu') OR node_mode = 'true')`,
    [date],
  )
}

export async function b(db: any, date: string) {
  // node-agnostic: non_node_bodies_literal: bodies are the five tara grahas by construction (TARA_GRAHA_SUBJECTS)
  return db.query(`SELECT body, latitude FROM ephemeris_daily WHERE date = $1 AND body = ANY($2)`, [date, ['Mars']])
}

export const C = 'SELECT date FROM ephemeris_daily ' +
  "WHERE body = 'Venus' AND date = $1"
// SELECT date FROM ephemeris_daily in a comment is not a read
