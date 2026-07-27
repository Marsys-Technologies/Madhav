/**
 * dump_vidhi_registry.ts — PARIŚODHANA B2 (Ω8 floor-wiring, anti-drift gate).
 * ================================================================================
 * Emits the canonical Vidhi registry (platform/src/lib/vidhi/registry_data.ts) as a
 * NORMALIZED JSON document — the single TS-side reference the vidhi-registry parity gate
 * (check_vidhi_registry_parity.mjs) compares the Python DB-seed writers against.
 *
 * "Normalized" = every optional field is materialized to its explicit default so the three
 * process-boundary copies (canonical TS, the two Python seed writers, and — informationally —
 * the SQL migration) compare on the SAME shape:
 *   - floor_items[].args_override → {} when absent
 *   - floor_items[].hard_floor    → false when absent
 *   - floors[].notes              → null when absent
 * Floors are emitted in registry order; floor_items are emitted sorted by `order` (the order the
 * compiler consumes them within a band). Object-key order is NOT normalized here — the gate
 * deep-compares parsed JSON with recursive key-sorting, so key order is irrelevant.
 *
 * USAGE: npx tsx scripts/census/dump_vidhi_registry.ts   (run from platform/) → prints JSON to stdout.
 */
import { VIDHI_PRIMITIVES, VIDHI_INTENT_FLOORS } from '../../src/lib/vidhi/registry_data'

interface NormalizedPrimitive {
  primitive_id: string
  version: number
  definition: string
  category: string
  live_tool: string
  tool_args: Record<string, unknown>
  fallback_face: string | null
  known_gap: string | null
  mandatory_tags: string[]
  cr27_prevents: string[]
}

interface NormalizedFloorItem {
  primitive_id: string
  order: number
  band: string
  args_override: Record<string, unknown>
  hard_floor: boolean
}

interface NormalizedFloor {
  intent: string
  version: number
  cr27_coverage: string[]
  notes: string | null
  floor_items: NormalizedFloorItem[]
}

const primitives: NormalizedPrimitive[] = [...VIDHI_PRIMITIVES]
  .map((p) => ({
    primitive_id: p.primitive_id,
    version: p.version,
    definition: p.definition,
    category: p.category,
    live_tool: p.live_tool,
    tool_args: { ...p.tool_args },
    fallback_face: p.fallback_face,
    known_gap: p.known_gap,
    mandatory_tags: [...p.mandatory_tags],
    cr27_prevents: [...p.cr27_prevents],
  }))
  .sort((a, b) => a.primitive_id.localeCompare(b.primitive_id))

const floors: NormalizedFloor[] = VIDHI_INTENT_FLOORS.map((f) => ({
  intent: f.intent,
  version: f.version,
  cr27_coverage: [...f.cr27_coverage],
  notes: f.notes ?? null,
  floor_items: [...f.floor_items]
    .sort((a, b) => a.order - b.order)
    .map((i) => ({
      primitive_id: i.primitive_id,
      order: i.order,
      band: i.band,
      args_override: { ...(i.args_override ?? {}) },
      hard_floor: i.hard_floor ?? false,
    })),
}))

process.stdout.write(JSON.stringify({ primitives, floors }, null, 2) + '\n')
