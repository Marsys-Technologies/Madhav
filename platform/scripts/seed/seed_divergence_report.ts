/**
 * seed_divergence_report.ts — what a seed run would change, computed BEFORE it writes.
 *
 * Nirmāṇa WORK_QUEUE M0-T35. Implements ruling D-27 §2(b) and ruling D-28 §1.
 *
 * ─── WHY THIS FILE EXISTS ────────────────────────────────────────────────────
 *
 * `asset_registry_seed.ts`'s `ON CONFLICT (asset_id) DO UPDATE SET` assigns most of the
 * registry from `EXCLUDED` unconditionally. Whoever ran last therefore won, silently, with
 * exit 0 — which is not an answer to "which surface is right", it is the absence of one.
 *
 * D-27 split the registry's columns into three classes:
 *
 *   MEASURED               the campaign owns it; a declarative file structurally cannot hold a
 *                          measured value. `target_floor` is the case, and it has been removed
 *                          from the seeder's DO UPDATE SET entirely (see that file).
 *   DECLARED               the seed owns it outright; a divergence is the DB being stale.
 *   DECLARED-BUT-VERIFIABLE  legitimately authored in source AND checkable against reality —
 *                          `count_sql` and `depends_on`. Neither surface is unconditionally
 *                          right, so neither may quietly win. D-27 §2(b): "a seed run must
 *                          produce a divergence report for these columns before writing, and
 *                          the divergence is reconciled at the owning rung's Conform, on the
 *                          merits, per cell."
 *
 * D-28 §1 then added the category that matters most, and generalised it deliberately rather
 * than special-casing the asset that exposed it:
 *
 *   > D-27's mandatory seed divergence report MUST TREAT A NULL->VALUE TRANSITION AS A DISTINCT
 *   > CATEGORY FROM A VALUE->VALUE CHANGE. Filling a NULL is not the same operation as changing
 *   > a value; it is precisely where an undecided question gets silently answered by a default.
 *   > Any NULL->value transition in that report requires an explicit decision before the seed
 *   > runs, not after.
 *
 * The live instance is `lel_events`, whose `layer_index` / `layer_name` are held NULL because
 * the correct value is NULL-if-source but L5/Mīmāṃsā-if-data and D-23 reserved that question to
 * R5. That NULL is not absent data — it is the only place in the registry where the openness of
 * a reserved decision is written down, and a re-seed would answer it with one of the two
 * candidate answers, invisibly, producing a row indistinguishable from a correctly-derived one.
 * No value-drift measurement can flag that, because nothing was wrong before or after.
 *
 * NOTHING HERE NAMES `lel_events`, OR ANY OTHER ASSET. D-25 §2(c) refused special-casing two
 * asset ids on the ground that it "would fix the symptom and leave the mechanism, and would
 * silently miss the next" one, and D-28 §1 held to that explicitly. The gate below fires on the
 * SHAPE — live IS NULL, seed writes a value — so it catches the next deliberate NULL nobody has
 * thought of yet.
 *
 * ─── WHY THIS IS A SEPARATE MODULE ───────────────────────────────────────────
 *
 * Ruling D-13 standing-instructs every agent not to import from `asset_registry_seed.ts`: that
 * module exports `ASSETS` and its `main()` runs `INSERT INTO asset_registry … ON CONFLICT DO
 * UPDATE` against the control-plane table this campaign is auditing. Machinery that lives in
 * that file therefore cannot be unit-tested by import — only observed through a subprocess.
 *
 * So the machinery lives HERE instead: pure functions, no `pg`, no `main()`, no side effect of
 * any kind at import time. `asset_registry_seed.ts` imports from this file, never the reverse.
 * A test may import this module freely; D-13 is untouched because no execution path here can
 * reach a database.
 *
 * ─── NO SHADOW COPIES ────────────────────────────────────────────────────────
 *
 * Two disciplines, both from CLAUDE.md §N.7 item 3 (no wrapper-local constant may shadow the
 * value it claims to restate) and both structural rather than by convention:
 *
 *   1. `deriveSeedRow()` is the ONE place the seed's bound parameter values are computed. The
 *      seeder calls it to build the report AND to bind the upsert, from the same object. A
 *      report cannot describe a write that differs from the write.
 *   2. The set of columns the report covers is PARSED from the upsert SQL itself
 *      (`onConflictUpdatedColumns`), never re-typed. Adding a column to the SET clause adds it
 *      to the report automatically; removing one removes it. A hand-kept parallel list would be
 *      free to drift from the SQL, and drifting-parallel-declaration is the exact defect class
 *      this campaign keeps finding.
 */

// ── The asset shape this module needs ────────────────────────────────────────
// Structural, deliberately NOT imported from asset_registry_seed.ts (D-13). `AssetDef` there is
// assignable to this. If the two ever diverge, TypeScript says so at the seeder's call site.

export interface SeedAssetLike {
  asset_id: string
  layer: string
  sort_order: number
  sanskrit_name: string
  english_name: string
  english_description: string
  storage_type: string
  target_table: string | null
  count_sql: string | null
  size_sql: string | null
  target_floor: number | null
  expected_volume_formula: string | null
  expected_volume_inputs: Record<string, unknown> | null
  volume_explanation: string | null
  depends_on: string[]
  scope: string
  is_active: boolean
  estimated_seconds: null
  asset_type?: string
  layer_name?: string
  layer_index?: string
  provides_apis?: Record<string, unknown>[] | null
  health_probe?: Record<string, unknown> | null
  catalog_status?: string
  asset_kind?: string
}

export type SeedRow = Record<string, unknown>

/**
 * The layer→display-name and layer→index maps `main()` derives from when an entry omits the
 * key. Values are CLAUDE.md §N.1's LOCKED external lexicon — `Gaṇita` and `Kāla` carry their
 * diacritics; the ASCII-folded spellings are a §N.1 violation (recorded in ruling D-28 §6,
 * where a codepoint pin caught exactly that in production before a write).
 */
const LAYER_NAMES: Record<string, string> = {
  brahmagyan: 'Brahmagyan', ganita: 'Gaṇita', bodha: 'Bodha',
  kala: 'Kāla', phala: 'Phala', mimamsa: 'Mīmāṃsā',
}
const LAYER_INDICES: Record<string, string> = {
  brahmagyan: 'L0', ganita: 'L1', bodha: 'L2',
  kala: 'L3', phala: 'L4', mimamsa: 'L5',
}

/**
 * Every column value the seed's upsert binds, for one asset, with all defaults and derivations
 * applied — the same map the seeder uses to build its parameter array.
 *
 * The `??` defaults are the reason an ABSENT key is an ACTIVE WRITE rather than a no-op. Ruling
 * D-27 §3(a) calls that "the single most valuable thing" in the durability register and asks for
 * it stated plainly: modelling an omitted column as "unchanged" reports 0 changes and produces a
 * falsely reassuring answer. `asset_type` / `asset_kind` default to `'data'`, so an entry that
 * simply does not mention the key overwrites a live `'service'` with `'data'`.
 *
 * Values are LOGICAL, not transport-encoded: jsonb columns are objects here and are
 * `JSON.stringify`-ed at bind time by the caller, exactly as before.
 */
export function deriveSeedRow(asset: SeedAssetLike): SeedRow {
  return {
    asset_id: asset.asset_id,
    layer: asset.layer,
    sort_order: asset.sort_order,
    sanskrit_name: asset.sanskrit_name,
    english_name: asset.english_name,
    english_description: asset.english_description,
    storage_type: asset.storage_type,
    target_table: asset.target_table,
    count_sql: asset.count_sql,
    size_sql: asset.size_sql,
    // Modelled, but no longer WRITTEN by any path: `target_floor` is absent from both the
    // seeder's INSERT column list and its ON CONFLICT DO UPDATE SET (rulings D-27 §2(a),
    // D-35 §1). It stays here so a derived row remains a faithful model of the entry, and
    // deliberately takes NO `??` default — a default would write the column by a path with
    // no name in either SQL list, which is the shape D-27 §3(a) named.
    target_floor: asset.target_floor,
    expected_volume_formula: asset.expected_volume_formula,
    expected_volume_inputs: asset.expected_volume_inputs ?? null,
    volume_explanation: asset.volume_explanation,
    depends_on: asset.depends_on,
    scope: asset.scope,
    is_active: asset.is_active,
    estimated_seconds: asset.estimated_seconds,
    asset_type: asset.asset_type ?? 'data',
    layer_name: asset.layer_name ?? LAYER_NAMES[asset.layer] ?? asset.layer,
    layer_index: asset.layer_index ?? LAYER_INDICES[asset.layer] ?? null,
    provides_apis: asset.provides_apis ?? null,
    health_probe: asset.health_probe ?? null,
    catalog_status: asset.catalog_status ?? (asset.layer === 'brahmagyan' ? 'CURRENT' : 'DRAFT'),
    asset_kind: asset.asset_kind ?? 'data',
  }
}

// ── Parsing the SET clause: which columns does a re-run actually write? ──────

export interface UpdatedColumn {
  /** The column on the left of the `=`. */
  column: string
  /** True when the assignment is a `CASE … END` rather than a bare `EXCLUDED.x`. */
  guarded: boolean
}

/**
 * Extract the columns a statement's `ON CONFLICT … DO UPDATE SET` body assigns.
 *
 * Parsed from the SQL rather than declared alongside it, so the report's coverage cannot drift
 * from what the statement does. `--` comments are stripped first (the MR-06 guard's explanation
 * lives inside the SET body and contains both commas and `=` signs, so a naive split reads
 * garbage out of the prose).
 *
 * Assignments are separated by commas at paren-depth 0. A `CASE WHEN … THEN … ELSE … END`
 * contains no top-level comma, so it survives the split whole and is reported `guarded: true`.
 */
export function onConflictUpdatedColumns(sql: string): UpdatedColumn[] {
  const marker = /ON\s+CONFLICT\s*\([^)]*\)\s*DO\s+UPDATE\s+SET/i
  const m = marker.exec(sql)
  if (!m) throw new Error('onConflictUpdatedColumns: no "ON CONFLICT (…) DO UPDATE SET" found')

  // Strip line comments, then take everything after the marker.
  const body = sql
    .slice(m.index + m[0].length)
    .split('\n')
    .map(line => {
      const c = line.indexOf('--')
      return c < 0 ? line : line.slice(0, c)
    })
    .join('\n')

  const segments: string[] = []
  let depth = 0
  let start = 0
  for (let i = 0; i < body.length; i++) {
    const ch = body[i]
    if (ch === '(') depth++
    else if (ch === ')') depth--
    else if (ch === ',' && depth === 0) {
      segments.push(body.slice(start, i))
      start = i + 1
    }
  }
  segments.push(body.slice(start))

  const out: UpdatedColumn[] = []
  for (const seg of segments) {
    const eq = seg.indexOf('=')
    if (eq < 0) continue
    const column = seg.slice(0, eq).trim()
    if (!/^[a-z_][a-z0-9_]*$/i.test(column)) continue
    out.push({ column, guarded: /\bCASE\b/i.test(seg.slice(eq + 1)) })
  }
  return out
}

// ── Guards: what the SET clause actually produces for a guarded column ───────

/**
 * The effective written value for a CASE-guarded column, given the live row.
 *
 * MR-06 (`asset_registry_seed.ts`, the RETIRED guard): a RETIRED asset must never be resurrected
 * by a re-seed, so `catalog_status` and `is_active` preserve the DB value when the LIVE row is
 * already RETIRED. Modelling this matters — without it the report would announce changes the SQL
 * will not make, and a report that cries wolf is one an operator learns to scroll past.
 *
 * Keyed by column name and cross-checked against the SQL by test: every column the parser
 * reports `guarded: true` must appear here, and every key here must be `guarded: true` in the
 * SQL. Neither list is allowed to be the sole authority.
 *
 * An honest note carried from ruling D-28 §4: this guard has never had to choose. Its only live
 * RETIRED row is declared RETIRED in the seed too, so both branches agree — "a guard that has
 * never had to choose is not yet a detector". The fixtures below are therefore the only place
 * its two branches have ever been separated.
 */
export const GUARDED_COLUMNS: Record<string, (live: SeedRow, seedValue: unknown) => unknown> = {
  catalog_status: (live, seedValue) =>
    live.catalog_status === 'RETIRED' ? live.catalog_status : seedValue,
  is_active: (live, seedValue) =>
    live.catalog_status === 'RETIRED' ? live.is_active : seedValue,
}

// ── Classification ───────────────────────────────────────────────────────────

export type CellCategory = 'unchanged' | 'null_to_value' | 'value_to_null' | 'value_change'

/** Recursive key-sorted canonical form, so jsonb key order is not mistaken for a change. */
function canonical(v: unknown): unknown {
  if (v === null || v === undefined) return null
  if (Array.isArray(v)) return v.map(canonical)
  if (v instanceof Date) return v.toISOString()
  if (typeof v === 'object') {
    const src = v as Record<string, unknown>
    const out: Record<string, unknown> = {}
    for (const k of Object.keys(src).sort()) out[k] = canonical(src[k])
    return out
  }
  return v
}

function isNullish(v: unknown): boolean {
  return v === null || v === undefined
}

/**
 * Which of the four things would this write do?
 *
 * `null_to_value` is deliberately NOT a sub-case of `value_change`. It is the whole point of
 * D-28 §1: a live NULL may be an undecided question written down, and filling it answers that
 * question with a default. A value→value change overwrites an answer that already existed;
 * a NULL fill manufactures one.
 *
 * Note what is NOT nullish here: `''`, `0`, `false` and `[]` are values. The DB default for
 * `depends_on` is `ARRAY[]::text[]`, so an empty dependency list is a declared "no dependencies",
 * not an absence, and must not trip the gate.
 */
export function classifyCell(live: unknown, seed: unknown): CellCategory {
  const liveNull = isNullish(live)
  const seedNull = isNullish(seed)
  if (liveNull && seedNull) return 'unchanged'
  if (liveNull) return 'null_to_value'
  if (seedNull) return 'value_to_null'
  return JSON.stringify(canonical(live)) === JSON.stringify(canonical(seed))
    ? 'unchanged'
    : 'value_change'
}

// ── The report ───────────────────────────────────────────────────────────────

/**
 * D-27 §2(b)'s class: legitimately authored in source AND checkable against reality. A DAG edge
 * SHOULD be declared where it is reviewable and diffable AND SHOULD be audited against what the
 * code actually reads, so neither surface is unconditionally right and the pair is surfaced
 * rather than resolved here. Reconciliation is the owning rung's Conform stage, on the merits,
 * per cell — and per D-27 §2(c) the repair must land in BOTH surfaces, or in the seed alone.
 */
export const DECLARED_BUT_VERIFIABLE_COLUMNS = ['count_sql', 'depends_on'] as const

export interface DivergentCell {
  assetId: string
  column: string
  category: Exclude<CellCategory, 'unchanged'>
  live: unknown
  seed: unknown
  /** True for the DECLARED-BUT-VERIFIABLE columns D-27 §2(b) names. */
  verifiable: boolean
  /** True when the seed entry never declared the key and a `??` default supplied the value. */
  fromDefault: boolean
}

export interface DivergenceReport {
  liveRowCount: number
  seedRowCount: number
  columns: UpdatedColumn[]
  cells: DivergentCell[]
  /** Assets the seed would INSERT because no live row exists. Not a divergence — a creation. */
  newAssetIds: string[]
  counts: Record<Exclude<CellCategory, 'unchanged'>, number>
}

export interface BuildReportInput {
  /** Live `asset_registry` rows, keyed by asset_id. */
  liveRows: Map<string, SeedRow>
  /** `deriveSeedRow()` output, keyed by asset_id, in seed order. */
  seedRows: Map<string, SeedRow>
  /** From `onConflictUpdatedColumns(<the upsert SQL>)`. */
  columns: UpdatedColumn[]
  /**
   * Which (assetId, column) pairs had no explicit key in the seed entry, so a `??` default
   * supplied the value. Reporting-only; it does not change any category. Ruling D-27 §3(a).
   */
  defaultedKeys?: Set<string>
}

export function cellToken(assetId: string, column: string): string {
  return `${assetId}.${column}`
}

export function buildDivergenceReport(input: BuildReportInput): DivergenceReport {
  const { liveRows, seedRows, columns, defaultedKeys } = input
  const verifiable = new Set<string>(DECLARED_BUT_VERIFIABLE_COLUMNS)
  const cells: DivergentCell[] = []
  const newAssetIds: string[] = []

  for (const [assetId, seedRow] of seedRows) {
    const live = liveRows.get(assetId)
    if (!live) {
      newAssetIds.push(assetId)
      continue
    }
    for (const { column, guarded } of columns) {
      const guard = guarded ? GUARDED_COLUMNS[column] : undefined
      if (guarded && !guard) {
        throw new Error(
          `buildDivergenceReport: column "${column}" is CASE-guarded in the SQL but has no ` +
          'model in GUARDED_COLUMNS. Refusing to report a guarded column as if it were ' +
          'unconditional — the report would describe a write the statement will not make.',
        )
      }
      const seedValue = guard ? guard(live, seedRow[column]) : seedRow[column]
      const category = classifyCell(live[column], seedValue)
      if (category === 'unchanged') continue
      cells.push({
        assetId,
        column,
        category,
        live: live[column],
        seed: seedValue,
        verifiable: verifiable.has(column),
        fromDefault: defaultedKeys?.has(cellToken(assetId, column)) ?? false,
      })
    }
  }

  const counts = { null_to_value: 0, value_to_null: 0, value_change: 0 } as Record<
    Exclude<CellCategory, 'unchanged'>,
    number
  >
  for (const c of cells) counts[c.category]++

  return {
    liveRowCount: liveRows.size,
    seedRowCount: seedRows.size,
    columns,
    cells,
    newAssetIds,
    counts,
  }
}

export function nullFillCells(report: DivergenceReport): DivergentCell[] {
  return report.cells.filter(c => c.category === 'null_to_value')
}

// ── Rendering ────────────────────────────────────────────────────────────────

function preview(v: unknown, max = 90): string {
  if (v === null || v === undefined) return '(null)'
  const s = typeof v === 'string' ? v : JSON.stringify(v)
  const flat = s.replace(/\s+/g, ' ').trim()
  return flat.length <= max ? flat : `${flat.slice(0, max)}…[+${flat.length - max}]`
}

export function formatDivergenceReport(report: DivergenceReport): string {
  const L: string[] = []
  L.push('── SEED DIVERGENCE REPORT (computed BEFORE any write — rulings D-27 §2(b), D-28 §1) ──')
  L.push('')
  L.push(`Live asset_registry rows: ${report.liveRowCount}   Seed entries: ${report.seedRowCount}`)
  L.push(`Columns a re-run writes on conflict: ${report.columns.length} ` +
         `(${report.columns.filter(c => c.guarded).length} CASE-guarded)`)
  L.push('')
  L.push(`  NULL → value  : ${report.counts.null_to_value}   ` +
         '← a default answering a question nobody decided. GATED.')
  L.push(`  value → NULL  : ${report.counts.value_to_null}`)
  L.push(`  value → value : ${report.counts.value_change}`)
  L.push(`  new rows      : ${report.newAssetIds.length} (INSERT — no live row to diverge from)`)
  L.push('')

  const fills = nullFillCells(report)
  if (fills.length > 0) {
    L.push('NULL → value transitions — each needs an explicit decision BEFORE this run:')
    for (const c of fills) {
      L.push(`  ${cellToken(c.assetId, c.column)}`)
      L.push(`      live: (null)   seed would write: ${preview(c.seed)}` +
             `${c.fromDefault ? '   [from a ?? default — the key is not declared]' : ''}`)
    }
    L.push('')
  }

  const verifiableCells = report.cells.filter(c => c.verifiable)
  L.push(`DECLARED-BUT-VERIFIABLE columns (${DECLARED_BUT_VERIFIABLE_COLUMNS.join(', ')}) — ` +
         `${verifiableCells.length} divergent cell(s).`)
  L.push('  Neither surface is unconditionally right (D-27 §2(b)). These are SURFACED, not')
  L.push('  resolved: reconcile each at the owning rung\'s Conform stage, on the merits, per')
  L.push('  cell — and land the repair in BOTH surfaces, or in the seed alone (D-27 §2(c)).')
  for (const c of verifiableCells) {
    L.push(`  ${cellToken(c.assetId, c.column)}  [${c.category}]`)
    L.push(`      live: ${preview(c.live)}`)
    L.push(`      seed: ${preview(c.seed)}`)
  }
  L.push('')

  const others = report.cells.filter(c => !c.verifiable && c.category !== 'null_to_value')
  if (others.length > 0) {
    L.push(`Other divergent cells (${others.length}):`)
    for (const c of others) {
      L.push(`  ${cellToken(c.assetId, c.column)}  [${c.category}]` +
             `${c.fromDefault ? ' [from a ?? default]' : ''}`)
      L.push(`      live: ${preview(c.live, 60)}   →   seed: ${preview(c.seed, 60)}`)
    }
    L.push('')
  }

  if (report.newAssetIds.length > 0) {
    L.push(`New rows this run would INSERT (${report.newAssetIds.length}): ` +
           report.newAssetIds.join(', '))
    L.push('')
  }
  L.push('── end of divergence report ─────────────────────────────────────────────────────')
  return L.join('\n')
}

// ── The gate ─────────────────────────────────────────────────────────────────

/**
 * The environment variable that carries the operator's explicit decision.
 *
 * WHY A GATE AND NOT A WARNING. D-28 §1 requires "a real gate, not a printed warning that a
 * hurried operator scrolls past", and left open whether it BLOCKS or requires an ACKNOWLEDGEMENT
 * FLAG. It does both, in the only combination that is actually a decision:
 *
 *   - It BLOCKS by default. A NULL fill is not recoverable by re-running anything: once the
 *     default is written, the row is indistinguishable from a correctly-derived one, so no later
 *     detector can find it. A signal that only warns about damage nothing can subsequently
 *     detect is the §N.8 shape — a mechanism with no consequence — and D-17 already recorded, in
 *     this same file's neighbourhood, that a safety mechanism which does not actually stop
 *     anything harms the careful operator rather than the careless one.
 *
 *   - The escape is PER CELL, not a blanket flag. `SEED_ACK_NULL_FILL` takes an explicit list of
 *     `asset_id.column` tokens. A blanket `--yes-i-know` would be the scrolled-past warning
 *     wearing a flag's costume: it can be typed once, pasted into a runbook, and thereafter
 *     acknowledges NULL fills nobody has ever looked at, including the next one. Naming the cell
 *     cannot be done before reading the report, and it goes stale by itself — a new deliberate
 *     NULL appears under a token no existing acknowledgement covers, and the run blocks again.
 *
 *   - A token that matches NOTHING in the current report is an ERROR, not a shrug. That is the
 *     stale-runbook case, and it is the exact mechanism by which an acknowledgement written for
 *     last month's report would authorise this month's unexamined fill. Failing loudly forces
 *     the list to be re-derived from a report that was actually generated.
 *
 * The value is whitespace/comma separated, e.g.
 *   SEED_ACK_NULL_FILL='lel_events.layer_index lel_events.layer_name'
 */
export const NULL_FILL_ACK_ENV = 'SEED_ACK_NULL_FILL'

export function parseNullFillAcknowledgement(env: NodeJS.ProcessEnv): Set<string> {
  const raw = env[NULL_FILL_ACK_ENV]
  if (!raw) return new Set()
  return new Set(raw.split(/[\s,]+/).map(s => s.trim()).filter(Boolean))
}

export class NullFillGateError extends Error {
  readonly unacknowledged: string[]
  readonly stale: string[]
  constructor(message: string, unacknowledged: string[], stale: string[]) {
    super(message)
    this.name = 'NullFillGateError'
    this.unacknowledged = unacknowledged
    this.stale = stale
  }
}

/**
 * Throws unless every NULL→value transition in `report` is named in `ack`, and every token in
 * `ack` names one. Returns the acknowledged tokens so the caller can log what was decided.
 */
export function enforceNullFillGate(report: DivergenceReport, ack: Set<string>): string[] {
  const fills = nullFillCells(report).map(c => cellToken(c.assetId, c.column))
  const fillSet = new Set(fills)
  const unacknowledged = fills.filter(t => !ack.has(t))
  const stale = [...ack].filter(t => !fillSet.has(t))

  if (unacknowledged.length === 0 && stale.length === 0) return fills

  const L: string[] = []
  L.push('REFUSING TO SEED — a NULL→value transition needs an explicit decision first.')
  L.push('')
  L.push('Rulings D-27 §2(b) and D-28 §1. Filling a NULL is not the same operation as changing a')
  L.push('value: a live NULL can be an UNDECIDED QUESTION written down, and a `??` default answers')
  L.push('it invisibly. The resulting row is indistinguishable from a correctly-derived one, so')
  L.push('nothing downstream can ever detect that the question was answered by accident.')
  L.push('')
  L.push('NOTHING HAS BEEN WRITTEN. The upsert loop had not started.')
  L.push('')
  if (unacknowledged.length > 0) {
    L.push(`${unacknowledged.length} NULL→value transition(s) not acknowledged:`)
    for (const t of unacknowledged) {
      const cell = nullFillCells(report).find(c => cellToken(c.assetId, c.column) === t)!
      L.push(`  ${t}  →  seed would write: ${preview(cell.seed)}`)
    }
    L.push('')
  }
  if (stale.length > 0) {
    L.push(`${stale.length} acknowledgement token(s) match NOTHING in this report:`)
    for (const t of stale) L.push(`  ${t}`)
    L.push('')
    L.push('A stale acknowledgement is how a decision made about one report authorises a fill in')
    L.push('a later one that nobody read. Re-derive the list from the report printed above.')
    L.push('')
  }
  L.push('Decide each cell — is that NULL absent data, or a reserved decision held open? — then')
  L.push(`name every one of them, and only them, in ${NULL_FILL_ACK_ENV}:`)
  L.push('')
  L.push(`  ${NULL_FILL_ACK_ENV}='${fills.join(' ')}' \\`)
  L.push('    DATABASE_URL=… npx tsx scripts/seed/asset_registry_seed.ts')
  L.push('')
  L.push('There is deliberately no blanket "acknowledge everything" flag: it would be typed once,')
  L.push('pasted into a runbook, and thereafter acknowledge fills nobody has looked at.')

  throw new NullFillGateError(L.join('\n'), unacknowledged, stale)
}
