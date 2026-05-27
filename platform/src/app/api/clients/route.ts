import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'

async function requireSuperAdmin() {
  const user = await getServerUser()
  if (!user) return null
  const { rows } = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [user.uid])
  if (rows[0]?.role !== 'super_admin') return null
  return user
}

export async function GET() {
  const user = await requireSuperAdmin()
  if (!user) return res.forbidden()

  try {
    const { rows } = await query(
      'SELECT charts.*, profiles.name AS client_name FROM charts LEFT JOIN profiles ON charts.client_id=profiles.id ORDER BY charts.created_at DESC'
    )
    return NextResponse.json(rows)
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Query failed.'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}

export async function POST(request: Request) {
  const user = await requireSuperAdmin()
  if (!user) return res.forbidden()

  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid request body')
  }
  const { name, birth_date, birth_time, birth_place, birth_lat, birth_lng, subject_name } = body as {
    name?: string; birth_date?: string; birth_time?: string; birth_place?: string;
    birth_lat?: string; birth_lng?: string; subject_name?: string
  }

  if (!name || !birth_date || !birth_time || !birth_place) {
    return res.badRequest('Missing required fields')
  }

  // Unit 2c (Stream B): owner/subject split.
  //   - owner_id = the super_admin creating the chart (the guest who owns it).
  //   - subject_name = the chart subject's name (the person whose birth data this is).
  // No Firebase user minted per chart — clients are birth-data, not logins.
  // client_id is retained during the cutover window and seeded from owner_id so
  // any reads still using the legacy column resolve to the same Firebase UID.
  const owner_id = user.uid
  const client_id = user.uid // legacy column; identical to owner_id this cutover window.
  const subjectName = subject_name ?? name

  let chart: Record<string, unknown>
  try {
    const { rows } = await query(
      'INSERT INTO charts (client_id, owner_id, name, subject_name, birth_date, birth_time, birth_place, birth_lat, birth_lng) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING *',
      [
        client_id,
        owner_id,
        name,
        subjectName,
        birth_date,
        birth_time,
        birth_place,
        birth_lat ? parseFloat(birth_lat) : null,
        birth_lng ? parseFloat(birth_lng) : null,
      ]
    )
    chart = rows[0]
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Chart insert failed.'
    return res.internal(message)
  }

  const layers = [
    { layer: 'L1', sublayer: 'facts' },
    { layer: 'L2', sublayer: 'analysis_mode_a' },
    { layer: 'L2', sublayer: 'analysis_mode_b' },
    { layer: 'L2.5', sublayer: 'synthesis' },
    { layer: 'L3', sublayer: 'domain_reports' },
    { layer: 'L4', sublayer: 'query_interface' },
  ]

  try {
    for (const l of layers) {
      await query(
        'INSERT INTO pyramid_layers (chart_id, layer, sublayer, status) VALUES ($1,$2,$3,\'not_started\') ON CONFLICT DO NOTHING',
        [chart.id, l.layer, l.sublayer]
      )
    }
  } catch (err) {
    await query('DELETE FROM charts WHERE id=$1', [chart.id]).catch(() => {})
    const message = err instanceof Error ? err.message : 'Layer insert failed.'
    return res.internal(message)
  }

  // No invite link — chart subjects are not logins.
  return NextResponse.json(chart)
}
