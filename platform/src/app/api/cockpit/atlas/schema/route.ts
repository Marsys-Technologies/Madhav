import { NextRequest, NextResponse } from 'next/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

type ColumnRow = {
  column_name: string
  data_type: string
  is_nullable: string
  column_default: string | null
  ordinal_position: number
}

async function getWhitelistedTables(): Promise<Set<string>> {
  const result = await query<{ t: string }>(`
    SELECT DISTINCT unnest(
      CASE
        WHEN clear_tables IS NOT NULL AND cardinality(clear_tables) > 0 THEN clear_tables
        WHEN target_table IS NOT NULL THEN ARRAY[target_table]
        ELSE ARRAY[]::text[]
      END
    ) AS t
    FROM asset_registry
  `)
  return new Set(result.rows.map((r) => r.t).filter(Boolean))
}

export async function GET(req: NextRequest) {
  const table = req.nextUrl.searchParams.get('table')
  if (!table) {
    return NextResponse.json(
      { data: null, fetched_at: new Date().toISOString(), stale_after_seconds: 0, errors: ['table param required'] },
      { status: 400 }
    )
  }

  if (!/^[a-z_][a-z0-9_]{0,62}$/.test(table)) {
    return NextResponse.json(
      { data: null, fetched_at: new Date().toISOString(), stale_after_seconds: 0, errors: ['invalid table name format'] },
      { status: 400 }
    )
  }

  try {
    const allowed = await getWhitelistedTables()
    if (!allowed.has(table)) {
      return NextResponse.json(
        { data: null, fetched_at: new Date().toISOString(), stale_after_seconds: 0, errors: ['table not in asset registry'] },
        { status: 403 }
      )
    }

    const result = await query<ColumnRow>(
      `SELECT column_name, data_type, is_nullable, column_default, ordinal_position
       FROM information_schema.columns
       WHERE table_schema = 'public' AND table_name = $1
       ORDER BY ordinal_position`,
      [table]
    )

    const response = NextResponse.json({
      data: { table, columns: result.rows },
      fetched_at: new Date().toISOString(),
      stale_after_seconds: 60,
      errors: [],
    })
    response.headers.set('Cache-Control', 'public, s-maxage=60, stale-while-revalidate=30')
    return response
  } catch (err) {
    console.error('[cockpit/atlas/schema] db error', err)
    return NextResponse.json(
      {
        data: null,
        fetched_at: new Date().toISOString(),
        stale_after_seconds: 0,
        errors: [(err as Error).message ?? 'unknown error'],
      },
      { status: 500 }
    )
  }
}
