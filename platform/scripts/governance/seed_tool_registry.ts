/**
 * seed_tool_registry.ts — Upsert capability_tool_registry + capability_asset_tool_bindings
 * from CAPABILITY_MANIFEST.json and manifest_overrides.yaml.
 *
 * Run:
 *   cd platform && npx tsx scripts/governance/seed_tool_registry.ts
 *
 * Requires DATABASE_URL in .env.local.
 * Idempotent: running twice produces the same table state (upsert semantics).
 *
 * Exit codes:
 *   0 — seed completed; ≥ 30 rows in capability_tool_registry
 *   1 — seed failed or row count < 30
 */

import * as fs from 'node:fs'
import * as path from 'node:path'
import * as dotenv from 'dotenv'
import { Pool } from 'pg'

dotenv.config({ path: path.join(process.cwd(), '.env.local') })

const REPO_ROOT = path.resolve(__dirname, '..', '..', '..')
const MANIFEST_PATH = path.join(REPO_ROOT, '00_ARCHITECTURE', 'CAPABILITY_MANIFEST.json')
const OVERRIDES_PATH = path.join(REPO_ROOT, '00_ARCHITECTURE', 'manifest_overrides.yaml')

// ── Types ─────────────────────────────────────────────────────────────────────

interface ToolSeedRow {
  tool_name: string
  expose_to_planner: boolean
  description: string
  query_schema: Record<string, unknown> | null
  output_schema: Record<string, unknown> | null
  cost_weight: number | null
  linked_data_asset_ids: string[]
  binding_source: 'manifest' | 'override' | 'inferred'
}

// ── Manifest parser ───────────────────────────────────────────────────────────

function loadManifestTools(): ToolSeedRow[] {
  const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf-8')) as {
    entries: Array<Record<string, unknown>>
  }
  const rows: ToolSeedRow[] = []
  for (const entry of manifest.entries) {
    const toolName = entry['tool_name']
    if (typeof toolName !== 'string' || toolName.length === 0) continue
    const linked: string[] = []
    if (typeof entry['linked_data_asset_id'] === 'string') {
      linked.push(entry['linked_data_asset_id'] as string)
    }
    if (Array.isArray(entry['linked_data_asset_ids'])) {
      for (const id of entry['linked_data_asset_ids'] as string[]) {
        if (!linked.includes(id)) linked.push(id)
      }
    }
    rows.push({
      tool_name: toolName,
      expose_to_planner: Boolean(entry['expose_to_planner'] ?? entry['expose_to_chat'] ?? true),
      description: String(entry['tool_description'] ?? entry['description'] ?? ''),
      query_schema: (entry['query_schema'] as Record<string, unknown>) ?? null,
      output_schema: (entry['output_schema'] as Record<string, unknown>) ?? null,
      cost_weight: entry['cost_weight'] != null ? Number(entry['cost_weight']) : null,
      linked_data_asset_ids: linked,
      binding_source: 'manifest',
    })
  }
  return rows
}

function loadOverrideTools(): ToolSeedRow[] {
  const yaml = fs.readFileSync(OVERRIDES_PATH, 'utf-8')
  const rows: ToolSeedRow[] = []

  // Parse additional_entries blocks that have tool_name fields.
  // Strategy: find each "- canonical_id:" block after "additional_entries:"
  // and extract fields via regex (avoids adding a YAML dep).
  const afterAdditional = yaml.split(/^additional_entries:/m)[1]
  if (!afterAdditional) return rows

  // Split on entry boundaries: "  - canonical_id:"
  const entries = afterAdditional.split(/\n  - canonical_id:/g)

  for (const block of entries.slice(1)) {
    const toolNameMatch = block.match(/\n\s+tool_name:\s*["']?([a-z_]+)["']?/)
    if (!toolNameMatch) continue
    const toolName = toolNameMatch[1]

    const descMatch = block.match(/\n\s+tool_description:\s*["']?([^\n"']+)["']?/)
    const description = descMatch ? descMatch[1].trim() : ''

    const exposeMatch = block.match(/\n\s+expose_to_planner:\s*(true|false)/)
    const expose_to_planner = exposeMatch ? exposeMatch[1] === 'true' : true

    const costMatch = block.match(/\n\s+token_cost_hint:\s*["']?([a-z]+)["']?/)
    const costHint = costMatch ? costMatch[1] : null
    const cost_weight = costHint === 'low' ? 0.3 : costHint === 'high' ? 1.0 : costHint === 'med' ? 0.6 : null

    // linked_data_asset_ids: ["X", "Y"]
    const linkedMatch = block.match(/\n\s+linked_data_asset_ids:\s*\[([^\]]*)\]/)
    const linked: string[] = []
    if (linkedMatch) {
      const raw = linkedMatch[1]
      const ids = raw.match(/"([^"]+)"|'([^']+)'|([A-Z0-9_]+)/g) ?? []
      for (const id of ids) {
        const clean = id.replace(/['"]/g, '').trim()
        if (clean.length > 0) linked.push(clean)
      }
    }

    // query_schema: parse the nested YAML block minimally
    // For the seed we store null — full JSON Schema extraction from YAML is out of scope
    // (the schema is documented in manifest_overrides.yaml for human readers)
    const query_schema: Record<string, unknown> | null = null

    rows.push({
      tool_name: toolName,
      expose_to_planner,
      description,
      query_schema,
      output_schema: null,
      cost_weight,
      linked_data_asset_ids: linked,
      binding_source: 'override',
    })
  }
  return rows
}

// ── DB operations ─────────────────────────────────────────────────────────────

const pool = new Pool({ connectionString: process.env.DATABASE_URL })

async function upsertToolRegistry(rows: ToolSeedRow[]): Promise<void> {
  for (const row of rows) {
    await pool.query(
      `INSERT INTO capability_tool_registry
         (tool_name, expose_to_planner, description, query_schema, output_schema, cost_weight, linked_data_asset_ids)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       ON CONFLICT (tool_name) DO UPDATE SET
         expose_to_planner    = EXCLUDED.expose_to_planner,
         description          = EXCLUDED.description,
         query_schema         = EXCLUDED.query_schema,
         output_schema        = EXCLUDED.output_schema,
         cost_weight          = EXCLUDED.cost_weight,
         linked_data_asset_ids = EXCLUDED.linked_data_asset_ids,
         updated_at           = now()`,
      [
        row.tool_name,
        row.expose_to_planner,
        row.description,
        row.query_schema ? JSON.stringify(row.query_schema) : null,
        row.output_schema ? JSON.stringify(row.output_schema) : null,
        row.cost_weight,
        row.linked_data_asset_ids,
      ],
    )
  }
}

async function upsertAssetBindings(rows: ToolSeedRow[]): Promise<void> {
  for (const row of rows) {
    for (const assetId of row.linked_data_asset_ids) {
      await pool.query(
        `INSERT INTO capability_asset_tool_bindings
           (asset_canonical_id, tool_name, binding_source)
         VALUES ($1, $2, $3)
         ON CONFLICT (asset_canonical_id, tool_name) DO UPDATE SET
           binding_source = EXCLUDED.binding_source`,
        [assetId, row.tool_name, row.binding_source],
      )
    }
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const manifestRows = loadManifestTools()
  const overrideRows = loadOverrideTools()

  // Merge: overrides take precedence if same tool_name exists in both
  const mergedMap = new Map<string, ToolSeedRow>()
  for (const row of manifestRows) mergedMap.set(row.tool_name, row)
  for (const row of overrideRows) mergedMap.set(row.tool_name, row) // overrides win

  const merged = [...mergedMap.values()]
  console.log(`Seeding ${merged.length} tools (${manifestRows.length} from manifest, ${overrideRows.length} from overrides)`)

  await upsertToolRegistry(merged)
  await upsertAssetBindings(merged)

  const { rows: countRows } = await pool.query<{ count: string }>(
    'SELECT COUNT(*)::text AS count FROM capability_tool_registry',
  )
  const count = parseInt(countRows[0].count, 10)
  console.log(`capability_tool_registry row count: ${count}`)

  const { rows: bindingRows } = await pool.query<{ count: string }>(
    'SELECT COUNT(*)::text AS count FROM capability_asset_tool_bindings',
  )
  const bindingCount = parseInt(bindingRows[0].count, 10)
  console.log(`capability_asset_tool_bindings row count: ${bindingCount}`)

  await pool.end()

  if (count < 30) {
    console.error(`ERROR: expected ≥ 30 rows in capability_tool_registry, got ${count}`)
    process.exit(1)
  }
  console.log('Seed complete ✓')
  process.exit(0)
}

main().catch((err) => {
  console.error('Seed failed:', err)
  process.exit(1)
})
