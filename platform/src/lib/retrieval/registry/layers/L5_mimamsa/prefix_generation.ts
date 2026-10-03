/**
 * prefix_generation — display-side "pre-fix generation" detector for L5 Mimamsa served rows
 * ==========================================================================================
 * TI-l5-insight-prefix-label-001. Until the L5 chain is rebuilt by writers that carry the already
 * merged honesty fixes (F-143 / F-147 / F-148 / A-F-24 / the leakage_status 'clean' -> 'not_assessed'
 * repair), the production rows on the canonical chart were written by the PRE-FIX writers and still
 * say things the fixed writers would no longer say ('empirical' from assignment counts, '0% propensity
 * ... empirical learning', 'Blind retrodiction ... T-90d cutoff', base_rate = 0.1 on every calibration
 * row). This module decides, per served row and at request time, whether a row is from that
 * generation, and relabels it. It can only LOWER a claim; it never raises one, never writes a
 * row, and never edits stored text (N-46 calibration record is untouched).
 *
 * THE DETECTOR (CLAUDE.md N.8: no constant verdict, no env flag, no hand-placed banner)
 * --------------------------------------------------------------------------------------
 * The verdict is computed from the stamps each writer puts on every row it writes:
 *   - the writer's version label  (surface_formula_version / grammar_formula_version /
 *     discovery_formula_ver / scoring_formula_version), compared to the first version that carries the
 *     fixes (GENERATION_FLOORS), and
 *   - a content marker the fixed writers stamp and the old ones provably could not:
 *       insight units      leakage_status = 'clean' (old: every unit; new: 'not_assessed')
 *       discoveries        evidence_refs.cutoff_enforced (retrodiction) / .n_scored_matches (emergent_law)
 *       calibration        base_rate IS NULL (old: 0.1 on every row; new: NULL until a real rate exists)
 * A row is POST-fix only if the label is parseable, belongs to the expected writer, is at or above the
 * floor AND the marker agrees. Anything missing, unparseable, foreign or older is PRE-fix
 * (fail-closed: unknown -> 'unvalidated', never 'empirical').
 *
 * Why not the alternatives (full account in the PR / report):
 *   - code digest vs src/generated/nirmana-writer-digests.json: the Node process cannot observe the
 *     deployed Python closure (see lib/build/staleness.ts), only 1 of 12 chart-scoped L5 assets has a
 *     receipt row at all, and any later unrelated writer edit would flip every correct row to 'pre-fix'
 *     forever. A digest answers "did the code change", not "does the row carry the fix".
 *   - row build date vs fix commit date: discoveries/load_bearing carry no timestamp, and the merge
 *     date is not the deploy date (a row built between the two would be mislabelled post-fix).
 *
 * KNOWN LIMITS (stated, not hidden):
 *   - the CF-L5-03 chronology defect (retrodiction scored as prediction) is NOT fixed on main. A rebuild
 *     by a floor-passing writer therefore clears the label but not that defect; the label means
 *     "written by a writer with the listed fixes", nothing more.
 *   - classification is per-row-stamp only; the SOURCE generation is not consulted. In a partial rebuild
 *     (e.g. mi_darshana rebuilt over still-v1.0 grammar rows) a floor-passing unit can keep a stored
 *     'empirical' grade that rests on a pre-fix source row. The label is exact for a whole-chain rebuild.
 *
 * SEPARATE CLAIM (not a generation): load_bearing rows rank classical prior weights in EVERY generation on
 * main (mi_adhilepa sensitivity = min(applied_multiplier / 2, 1), role = rank position; the only ablation in
 * mi_pariksha is `structural_proxy_only`). That is carried as `claim_status: 'structural_proxy_only'` and
 * never as 'pre-fix generation', and it does not raise the chart-level generation flag, so the flag can clear
 * after a rebuild.
 *
 * Pure module, no imports. A byte-identical copy lives at platform-mcp/src/lib/l5_prefix_generation.ts
 * (platform-mcp cannot import platform sources); a parity test enforces identity.
 */

export const UNVALIDATED_PREFIX_GRADE = 'unvalidated_prefix'
export const PREFIX_LABEL = 'pre-fix generation, not validated'
export const STRUCTURAL_PROXY_STATUS = 'structural_proxy_only'
export const STRUCTURAL_PROXY_LABEL =
  'structural proxy only: sensitivity is a rescaled classical prior weight and role is its rank position; ' +
  'not a validated signal-removal analysis'

/** Legend entry for the downgraded grade (query_insights merges it into evidence_grade_legend). */
export const PREFIX_GRADE_LEGEND: Record<string, string> = {
  [UNVALIDATED_PREFIX_GRADE]:
    `stored grade was "empirical" but the row was written by a pre-fix L5 writer (${PREFIX_LABEL}): ` +
    'its stamps show it predates the honesty fixes, so the grade is not served as evidence. ' +
    'Numerics suppressed. Cleared by an L5 rebuild from writers carrying the fixes.',
}

/** Closed vocabulary of machine-readable flags this module can raise (L5-local; not the envelope vocab). */
export const L5_GENERATION_FLAGS = ['l5_rows_pre_fix_generation'] as const
export type L5GenerationFlag = (typeof L5_GENERATION_FLAGS)[number]

export type PrefixReason =
  | 'stamp_missing'
  | 'stamp_unparseable'
  | 'stamp_wrong_writer'
  | 'stamp_below_floor'
  | 'fix_marker_absent'
  | 'unknown_row_class'
  | 'generation_probe_unavailable'

export interface GenerationVerdict {
  pre_fix: boolean
  reason: PrefixReason | null
  stamp: string | null
  /** first version that carries the fixes, e.g. 'mi_darshana_v1.2' */
  required: string | null
}

type Floor = { asset: string; major: number; minor: number }

/**
 * First writer version that carries the merged fixes, per served row class. A parity test
 * (prefix_generation.test.ts) asserts each floor is <= the version the current writer source
 * stamps, so a rebuild by main's writers always classifies post-fix, and > 1.0/2.0 (what the
 * pre-fix rows carry).
 */
export const GENERATION_FLOORS = {
  insight_unit: { asset: 'mi_darshana', major: 1, minor: 2 },
  manifestation_grammar: { asset: 'mi_sambandha', major: 1, minor: 2 },
  discovery_retrodiction: { asset: 'mi_pariksha', major: 2, minor: 2 },
  discovery_emergent_law: { asset: 'mi_pariksha', major: 2, minor: 1 },
  // mi_pramana never bumped its label when base_rate went NULL (still v2.0). The label alone cannot
  // prove the fix, so v2.0 additionally needs base_rate IS NULL; a future writer that derives real
  // base rates must bump to v2.1+ (the floor), which this rule then accepts.
  calibration: { asset: 'mi_pramana', major: 2, minor: 1 },
} as const satisfies Record<string, Floor>

const CALIBRATION_LEGACY_LABEL: Floor = { asset: 'mi_pramana', major: 2, minor: 0 }

function parseStamp(label: unknown): { asset: string; major: number; minor: number } | null | 'missing' {
  if (label == null || (typeof label === 'string' && label.trim() === '')) return 'missing'
  if (typeof label !== 'string') return null
  const m = /^([a-z][a-z0-9_]*)_v(\d+)\.(\d+)$/.exec(label) // anchored, no trim: padded / suffixed stamps are unparseable
  if (!m) return null
  return { asset: String(m[1]), major: Number(m[2]), minor: Number(m[3]) }
}

function atLeast(p: { major: number; minor: number }, f: { major: number; minor: number }): boolean {
  return p.major > f.major || (p.major === f.major && p.minor >= f.minor)
}

function fmt(f: Floor): string {
  return `${f.asset}_v${f.major}.${f.minor}`
}

function checkStamp(label: unknown, floor: Floor): GenerationVerdict {
  const required = fmt(floor)
  const stamp = typeof label === 'string' && label.trim() !== '' ? label : null
  const p = parseStamp(label)
  if (p === 'missing') return { pre_fix: true, reason: 'stamp_missing', stamp: null, required }
  if (p === null) return { pre_fix: true, reason: 'stamp_unparseable', stamp, required }
  if (p.asset !== floor.asset) return { pre_fix: true, reason: 'stamp_wrong_writer', stamp, required }
  if (!atLeast(p, floor)) return { pre_fix: true, reason: 'stamp_below_floor', stamp, required }
  return { pre_fix: false, reason: null, stamp, required }
}

const POST: GenerationVerdict = { pre_fix: false, reason: null, stamp: null, required: null }

function isObject(x: unknown): x is Record<string, unknown> {
  return typeof x === 'object' && x !== null && !Array.isArray(x)
}

// ---------------------------------------------------------------------------------------------
// Classifiers (pure; one per served row class)
// ---------------------------------------------------------------------------------------------

/** mimamsa_insight_units row (mi_darshana). */
export function classifyInsightUnit(row: Record<string, unknown>): GenerationVerdict {
  const v = checkStamp(row['surface_formula_version'], GENERATION_FLOORS.insight_unit)
  if (v.pre_fix) return v
  // Old writers stamped leakage_status = 'clean' on every unit with no detector behind it.
  // Fixed writers write 'not_assessed'. A 'clean' under a post-fix label is a contradiction
  // (hand-edited label or mixed write): fail closed.
  // The marker must be PRESENT (a string) and not 'clean': a SELECT that omits the column, a null, or a
  // case/whitespace variant of 'clean' all fail closed.
  const ls = row['leakage_status']
  if (typeof ls !== 'string' || ls.trim().toLowerCase() === 'clean' || ls.trim() === '') {
    return { ...v, pre_fix: true, reason: 'fix_marker_absent' }
  }
  return v
}

/** mimamsa_manifestation_grammar row (mi_sambandha). */
export function classifyGrammarRow(row: Record<string, unknown>): GenerationVerdict {
  return checkStamp(row['grammar_formula_version'], GENERATION_FLOORS.manifestation_grammar)
}

/** mimamsa_discoveries row (mi_pariksha). Class decides floor and marker. */
export function classifyDiscovery(row: Record<string, unknown>): GenerationVerdict {
  const cls = row['discovery_class']
  const refs = isObject(row['evidence_refs']) ? row['evidence_refs'] : {}
  if (cls === 'retrodiction') {
    const v = checkStamp(row['discovery_formula_ver'], GENERATION_FLOORS.discovery_retrodiction)
    if (v.pre_fix) return v
    return typeof refs['cutoff_enforced'] === 'boolean' ? v : { ...v, pre_fix: true, reason: 'fix_marker_absent' }
  }
  if (cls === 'emergent_law') {
    const v = checkStamp(row['discovery_formula_ver'], GENERATION_FLOORS.discovery_emergent_law)
    if (v.pre_fix) return v
    const n = refs['n_scored_matches']
    return typeof n === 'number' && Number.isInteger(n)
      ? v
      : { ...v, pre_fix: true, reason: 'fix_marker_absent' }
  }
  return {
    pre_fix: true,
    reason: 'unknown_row_class',
    stamp: typeof row['discovery_formula_ver'] === 'string' ? (row['discovery_formula_ver'] as string) : null,
    required: null,
  }
}

/** One (label, base_rate-is-null) group of mimamsa_calibration rows (mi_pramana). */
export function classifyCalibrationRow(row: Record<string, unknown>): GenerationVerdict {
  const label = row['scoring_formula_version']
  const v = checkStamp(label, GENERATION_FLOORS.calibration)
  if (!v.pre_fix) return v
  // Below the floor only the legacy label (v2.0) may still be post-fix, and only when the fix's own
  // stamp (base_rate NULL) is present.
  if (v.reason === 'stamp_below_floor') {
    const p = parseStamp(label)
    if (p && p !== 'missing' && p.asset === CALIBRATION_LEGACY_LABEL.asset && atLeast(p, CALIBRATION_LEGACY_LABEL)) {
      if (row['base_rate'] === null) return { ...v, pre_fix: false, reason: null } // strict: undefined (column not read) is NOT null
      return { ...v, pre_fix: true, reason: 'fix_marker_absent' }
    }
  }
  return v
}

/**
 * Generation of a chart's calibration SET (for reliability bins / multipliers, which are derived
 * from it in the same build and carry no stamp of their own). Pre-fix if ANY calibration row is
 * pre-fix, or the set is empty/unreadable (the bins then cannot be tied to a generation).
 */
export function classifyCalibrationSet(
  groups: ReadonlyArray<{ scoring_formula_version: unknown; base_rate_is_null: unknown; n?: unknown }> | null,
): GenerationVerdict {
  if (groups == null) return { pre_fix: true, reason: 'generation_probe_unavailable', stamp: null, required: fmt(GENERATION_FLOORS.calibration) }
  if (groups.length === 0) return { pre_fix: true, reason: 'stamp_missing', stamp: null, required: fmt(GENERATION_FLOORS.calibration) }
  for (const g of groups) {
    const v = classifyCalibrationRow({
      scoring_formula_version: g.scoring_formula_version,
      // Only an explicit boolean true / 't' is NULL; undefined, 'yes', 1, null (a malformed probe value) are not.
      base_rate: g.base_rate_is_null === true || g.base_rate_is_null === 't' ? null : 'not-null',
    })
    if (v.pre_fix) return v
  }
  return { ...POST, stamp: String(groups[0]?.scoring_formula_version ?? '') }
}

// ---------------------------------------------------------------------------------------------
// Relabelling (display-side; stricter-only)
// ---------------------------------------------------------------------------------------------

const EMPIRICAL = 'empirical'

/** Statement rewrites that remove claims the pre-fix text made and the data never earned. */
export function relabelPrefixStatement(statement: string, insightType: unknown): string {
  let s = statement
  // v1.0 form 'fires with 0% propensity (n=55, empirical learning)': n there is the assignment count
  // (mi_sambandha n = opportunity count; scored_count was 0). The later 'outcome-scored predictions' form
  // (v1.1) does carry a scored n, so that sentence is NOT rewritten to call n an assignment count.
  s = s.replace(
    /\(n=(\d+), empirical learning\)/gi,
    `(${PREFIX_LABEL}; stored n=$1 is an assignment count, not scored outcomes)`,
  )
  s = s.replace(
    /\(n=(\d+) outcome-scored predictions, empirical learning\)/gi,
    `(n=$1 outcome-scored predictions; ${PREFIX_LABEL})`,
  )
  // calibrated_outlook: '... the observed outcome rate is 28.6% across 7 events (evidence: empirical).'
  // The rate comes from the pre-fix calibration set (circular, chronology-unclean bins), and the grade
  // word is the stored one; neither is served as measured evidence.
  s = s.replace(/the observed outcome rate is [\d.]+%/gi, 'the observed outcome rate is [suppressed: unvalidated pre-fix value]')
  s = s.replace(/\(evidence: empirical\)/gi, `(evidence: ${UNVALIDATED_PREFIX_GRADE}; ${PREFIX_LABEL})`)
  s = s.replace(/empirical learning/gi, PREFIX_LABEL)
  // The v1.0 grammar template prints the propensity as 'fires with N% propensity' (a literal 0% on the
  // canonical chart's 7 rows with 0 scored outcomes); the number was never a measurement.
  s = s.replace(/fires with [\d.]+% propensity/gi, 'has a propensity [suppressed: unvalidated pre-fix value]')
  // 'Blind retrodiction ... with T-90d cutoff <date>': the cutoff was declared, never applied.
  s = s.replace(/Blind retrodiction/g, `Retrodiction probe (${PREFIX_LABEL})`)
  s = s.replace(/with T[−-]90d cutoff \d{4}-\d{2}-\d{2}/g, 'with a declared-but-unenforced T−90d cutoff')
  if (insightType === 'load_bearing') s = relabelLoadBearingStatement(s)
  return s
}

/** load_bearing text claims an ablation nobody ran; the numbers are rescaled classical prior weights. */
export function relabelLoadBearingStatement(statement: string): string {
  return statement.replace(
    /Removing this signal would materially alter the reading\./g,
    'This ranks a classical prior weight (structural proxy only); it is not a validated signal-removal analysis.',
  )
}

/** Attach the (generation-independent) structural-proxy claim label to a load_bearing row. */
function withProxyClaim(out: Record<string, unknown>): Record<string, unknown> {
  const res: Record<string, unknown> = {
    ...out,
    claim_status: STRUCTURAL_PROXY_STATUS,
    claim_label: STRUCTURAL_PROXY_LABEL,
  }
  if (typeof out['statement'] === 'string') res['statement'] = relabelLoadBearingStatement(out['statement'])
  return res
}

export interface LabelOptions {
  /** also rewrite statement text (default true) */
  rewriteText?: boolean
}

/**
 * Apply the generation verdict to an insight-unit row. Adds `generation_status` (always, so an
 * absent field never has to be read as "fine"), and for pre-fix rows: downgrades 'empirical' to
 * 'unvalidated_prefix' (original kept in `evidence_grade_stored`), rewrites the affected statement text
 * and adds a human-readable `generation_label`. load_bearing units additionally carry the
 * generation-independent `claim_status: 'structural_proxy_only'` (see module header); that claim does not
 * make a post-fix unit "pre-fix".
 */
export function labelInsightUnit(row: Record<string, unknown>, opts: LabelOptions = {}): Record<string, unknown> {
  const verdict = classifyInsightUnit(row)
  const isLoadBearing = row['insight_type'] === 'load_bearing'
  if (!verdict.pre_fix) {
    const post = { ...row, generation_status: 'post_fix' }
    return isLoadBearing ? withProxyClaim(post) : post
  }
  const out: Record<string, unknown> = {
    ...row,
    generation_status: 'pre_fix_unvalidated',
    generation_reason: verdict.reason,
    generation_stamp: verdict.stamp,
    generation_required: verdict.required,
  }
  const labelParts: string[] = []
  if (row['evidence_grade'] === EMPIRICAL) {
    out['evidence_grade'] = UNVALIDATED_PREFIX_GRADE
    out['evidence_grade_stored'] = EMPIRICAL
    labelParts.push(`stored grade "empirical" is not served`)
  }
  if (opts.rewriteText !== false && typeof row['statement'] === 'string') {
    const rewritten = relabelPrefixStatement(row['statement'], row['insight_type'])
    if (rewritten !== row['statement']) {
      out['statement'] = rewritten
      labelParts.push('stored statement wording relabelled')
    }
  }
  out['generation_label'] = labelParts.length > 0
    ? `${PREFIX_LABEL} (${labelParts.join('; ')})`
    : PREFIX_LABEL
  return isLoadBearing ? withProxyClaim(out) : out
}

/** manifestation_grammar row: downgrade 'empirical' for pre-fix rows; values stay (raw reader). */
export function labelGrammarRow(row: Record<string, unknown>): Record<string, unknown> {
  const v = classifyGrammarRow(row)
  if (!v.pre_fix) return { ...row, generation_status: 'post_fix' }
  const out: Record<string, unknown> = {
    ...row,
    generation_status: 'pre_fix_unvalidated',
    generation_reason: v.reason,
    generation_stamp: v.stamp,
    generation_required: v.required,
  }
  if (row['evidence_grade'] === EMPIRICAL) {
    out['evidence_grade'] = UNVALIDATED_PREFIX_GRADE
    out['evidence_grade_stored'] = EMPIRICAL
  }
  out['generation_label'] =
    `${PREFIX_LABEL}: channel_propensity / n_support come from the pre-fix writer` +
    (row['evidence_grade'] === EMPIRICAL ? '; stored grade "empirical" is not served' : '')
  return out
}

/** discovery row: flag; relabel the retrodiction wording for pre-fix rows. */
export function labelDiscoveryRow(row: Record<string, unknown>): Record<string, unknown> {
  const v = classifyDiscovery(row)
  if (!v.pre_fix) return { ...row, generation_status: 'post_fix' }
  const out: Record<string, unknown> = {
    ...row,
    generation_status: 'pre_fix_unvalidated',
    generation_reason: v.reason,
    generation_stamp: v.stamp,
    generation_required: v.required,
    generation_label: `${PREFIX_LABEL}`,
  }
  if (typeof row['statement'] === 'string') {
    const rewritten = relabelPrefixStatement(row['statement'], row['discovery_class'])
    if (rewritten !== row['statement']) out['statement'] = rewritten
  }
  return out
}

/**
 * mimamsa_load_bearing row (mi_adhilepa). The table has no per-row writer stamp that separates generations
 * (formula_version is a constant that never moved), so generation_status is 'not_assessed' rather than a
 * claimed verdict; the claim label (structural proxy only) is true of every generation on main.
 */
export function labelLoadBearingRow(row: Record<string, unknown>): Record<string, unknown> {
  return {
    ...row,
    generation_status: 'not_assessed',
    claim_status: STRUCTURAL_PROXY_STATUS,
    claim_label: STRUCTURAL_PROXY_LABEL,
  }
}

/** Row derived from a chart's calibration set (reliability bin / multiplier): same generation as the set. */
export function labelCalibrationDerivedRow(
  row: Record<string, unknown>,
  setVerdict: GenerationVerdict,
  downgrade: ReadonlyArray<string>,
): Record<string, unknown> {
  if (!setVerdict.pre_fix) return { ...row, generation_status: 'post_fix' }
  const out: Record<string, unknown> = {
    ...row,
    generation_status: 'pre_fix_unvalidated',
    generation_reason: setVerdict.reason,
  }
  for (const col of downgrade) {
    const cur = row[col]
    if (cur === EMPIRICAL || cur === 'pass') {
      out[col] = UNVALIDATED_PREFIX_GRADE
      out[`${col}_stored`] = cur
    }
  }
  return out
}

export interface GenerationSummary {
  classifier: 'l5_prefix_generation/v1'
  flags: L5GenerationFlag[]
  pre_fix_rows: number
  post_fix_rows: number
  /** rows whose generation cannot be assessed from a stamp (mimamsa_load_bearing); never counted pre/post */
  generation_not_assessed_rows: number
  /** rows carrying the generation-independent structural-proxy claim (load_bearing); does not raise the flag */
  structural_proxy_rows: number
  empirical_downgraded_rows: number
  floors: Record<string, string>
  note: string
}

/** Roll-up over labelled rows (any row class). Flags is empty iff no row is pre-fix. */
export function summarizeGeneration(rows: ReadonlyArray<Record<string, unknown>>, floorKeys: ReadonlyArray<keyof typeof GENERATION_FLOORS>): GenerationSummary {
  let pre = 0
  let post = 0
  let down = 0
  let na = 0
  let proxy = 0
  for (const r of rows) {
    if (r['generation_status'] === 'post_fix') post++
    else if (r['generation_status'] === 'not_assessed' && r['claim_status'] === STRUCTURAL_PROXY_STATUS) na++
    else pre++ // fail-closed: anything not explicitly post_fix / assessed-as-not-assessable counts as pre-fix
    if (r['claim_status'] === STRUCTURAL_PROXY_STATUS) proxy++
    if (r['evidence_grade_stored'] === EMPIRICAL) down++
  }
  const floors: Record<string, string> = {}
  for (const k of floorKeys) floors[k] = fmt(GENERATION_FLOORS[k])
  return {
    classifier: 'l5_prefix_generation/v1',
    flags: pre > 0 ? ['l5_rows_pre_fix_generation'] : [],
    pre_fix_rows: pre,
    post_fix_rows: post,
    generation_not_assessed_rows: na,
    structural_proxy_rows: proxy,
    empirical_downgraded_rows: down,
    floors,
    note:
      `Rows classified from the writer stamps stored on each row (version label + fix marker), at request time. ` +
      `"pre_fix_unvalidated" rows were written before the honesty fixes the floors name and are served as ${PREFIX_LABEL}; ` +
      `their stored "empirical" grade is not served. Stored rows are unchanged. The flag is cleared by a rebuild from writers ` +
      `at or above the floors. structural_proxy_rows (load_bearing) carry a separate, generation-independent claim label ` +
      `and never raise the flag.`,
  }
}
