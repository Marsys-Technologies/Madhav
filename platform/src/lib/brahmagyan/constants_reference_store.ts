import { query } from '@/lib/db/client'

export type FormulaConstantRow = {
  constant_id: string
  value_jsonb: unknown
  class: 'classical' | 'native_judgment' | 'engineering' | 'conflation_bug'
  consumer_assets: string[]
  citation_or_ratification: string
  calibratable: boolean
  bounds: unknown
  version: string
}

export type VicharaConstantRow = {
  constant_key: string
  value_jsonb: unknown
  citation: string | null
  version: string
  updated_at: Date | string | null
}

type ReferenceQueryResult<Row> = { rows: Row[] }

export async function queryFormulaConstantsReference(constantId: string | null, cls: string | null): Promise<ReferenceQueryResult<FormulaConstantRow>> {
  const filters: string[] = ['1=1']
  const params: unknown[] = []
  let p = 1
  if (constantId) { filters.push(`constant_id = $${p++}`); params.push(constantId) }
  if (cls)        { filters.push(`class = $${p++}`); params.push(cls) }
  const where = filters.join(' AND ')

  const sql = `
      SELECT constant_id, value_jsonb, class, consumer_assets, citation_or_ratification,
             calibratable, bounds, version
      FROM brahma_formula_constants
      WHERE ${where}
      ORDER BY constant_id`

  return query<FormulaConstantRow>(sql, params)
}

export async function queryVicharaConstantsReference(constantKey: string | null): Promise<ReferenceQueryResult<VicharaConstantRow>> {
  const filters: string[] = ['1=1']
  const params: unknown[] = []
  let p = 1
  if (constantKey) { filters.push(`constant_key = $${p++}`); params.push(constantKey) }
  const where = filters.join(' AND ')

  const sql = `
      SELECT constant_key, value_jsonb, citation, version, updated_at
      FROM brahma_vichara_constants
      WHERE ${where}
      ORDER BY constant_key`

  return query<VicharaConstantRow>(sql, params)
}
