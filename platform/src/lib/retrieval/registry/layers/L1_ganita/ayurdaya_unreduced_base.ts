/**
 * ayurdaya_unreduced_base — display-side disclosure for served Āyurdāya (longevity) figures
 * ==========================================================================================
 * SS N-62 Q10 (display-side fix; no stored number, writer, or L1 row is touched).
 *
 * The ga_ayurdaya writer computes the Piṇḍāyu / Aṃśāyu / Naisargikāyu totals with
 * `apply_haranas=False` (ga_ayurdaya_writer.py) — they are UNREDUCED BASE FIGURES: the
 * classical reductive haranas are not applied. A bare "98.75 years" served with no caveat reads
 * as a lifespan figure, which the MACRO_PLAN Ethical Framework (probabilistic, calibrated, not
 * fortune-telling; health/longevity disclosure tiers) forbids. The one honest disclosure that
 * already existed (`harana_status`, buried in fact_value_jsonb and promoted to a top-level field
 * by get_ayurdaya) named the deferral but not the consequence for the figure itself.
 *
 * This module is the SINGLE source of the machine-readable fields + plain-language caveat, shared
 * by every served surface that can emit ayurdaya year figures (get_ayurdaya; chart_facts_query when
 * it serves fact_category='ayurdaya'), so the wording and the detector cannot drift apart.
 *
 * §N.7 item 4 / §N.8 (earned signal): `reductions_applied:false` is derived from the served rows'
 * own `harana_status`, never hardcoded. If a served total_years row carries a harana_status this
 * module does not recognise as "base only" (or none at all), the figure is NOT labelled
 * `unreduced_base`: it is `reduction_status_unverified` with `reductions_applied:null` — an honest
 * null beats an invented judgment (§N.7 item 6). Pages that carry only the per-graha contribution
 * rows / applicable_method row (no total_years row to read a status from) are labelled from the
 * writer's single computation mode (base-only), which is the only mode that has ever produced them.
 */
import { judgmentFlag, type JudgmentFlag } from '../../../envelope'

/** `figure_kind` for figures confirmed to be the unreduced base computation. */
export const AYURDAYA_FIGURE_KIND_UNREDUCED_BASE = 'unreduced_base' as const
/** `figure_kind` when a served total's harana (reduction) status could not be confirmed. */
export const AYURDAYA_FIGURE_KIND_STATUS_UNVERIFIED = 'reduction_status_unverified' as const

/** Plain-language caveat served with every unreduced base figure. */
export const AYURDAYA_UNREDUCED_BASE_CAVEAT =
  'Unreduced base figure from the classical pinda/amsa/nisarga computation; no reductions (harana) are applied; not a prediction of lifespan.'

/** Caveat when the reduction status of a served total could not be confirmed from its own row. */
export const AYURDAYA_STATUS_UNVERIFIED_CAVEAT =
  'Classical pinda/amsa/nisarga figure whose harana (reduction) status could not be confirmed from the served row; do not read it as a reduced or final figure; not a prediction of lifespan.'

/** harana_status values the writer emits for "base ayus only, reductive haranas not applied". */
const UNREDUCED_BASE_HARANA_STATUSES: ReadonlySet<string> = new Set(['base_only_haranas_deferred_to_w3'])

export interface AyurdayaFigureDisclosure {
  figure_kind: typeof AYURDAYA_FIGURE_KIND_UNREDUCED_BASE | typeof AYURDAYA_FIGURE_KIND_STATUS_UNVERIFIED
  /** false = confirmed unreduced base; null = could not be confirmed (never `true` here). */
  reductions_applied: false | null
  caveat: string
  judgment_flag: JudgmentFlag
}

type Row = Record<string, unknown>

/**
 * True iff `row` carries an Āyurdāya year figure: a method total (`total_years`), a per-graha
 * contribution (`<method>_contribution_years`), or the applicable_method row (whose jsonb carries
 * all three raw totals). When the row names its fact_category it must be 'ayurdaya' — `total_years`
 * exists under other categories (dashas etc.). get_ayurdaya's SELECT omits fact_category (its WHERE
 * already pins it), so an absent category is accepted.
 */
export function isAyurdayaYearsRow(row: Row): boolean {
  const category = row['fact_category']
  if (category !== undefined && category !== null && category !== 'ayurdaya') return false
  const key = String(row['fact_key'] ?? '')
  return key === 'total_years' || key === 'applicable_method' || key.endsWith('_contribution_years')
}

function haranaStatusOf(row: Row): string | null {
  const jsonb = row['fact_value_jsonb'] as { harana_status?: unknown } | null | undefined
  return typeof jsonb?.harana_status === 'string' ? jsonb.harana_status : null
}

/**
 * Derive the disclosure for a served page. Returns null when the page carries no Āyurdāya year
 * figure (nothing to caveat; never fabricated for a page that does not carry one).
 */
export function deriveAyurdayaFigureDisclosure(rows: readonly Row[]): AyurdayaFigureDisclosure | null {
  const yearRows = rows.filter(isAyurdayaYearsRow)
  if (yearRows.length === 0) return null

  const totalRows = yearRows.filter(r => r['fact_key'] === 'total_years')
  const unconfirmed = totalRows.some(r => {
    const status = haranaStatusOf(r)
    return status === null || !UNREDUCED_BASE_HARANA_STATUSES.has(status)
  })

  if (unconfirmed) {
    return {
      figure_kind: AYURDAYA_FIGURE_KIND_STATUS_UNVERIFIED,
      reductions_applied: null,
      caveat: AYURDAYA_STATUS_UNVERIFIED_CAVEAT,
      judgment_flag: judgmentFlag('ayurdaya_unreduced_base_figures', AYURDAYA_STATUS_UNVERIFIED_CAVEAT, 'warning'),
    }
  }
  return {
    figure_kind: AYURDAYA_FIGURE_KIND_UNREDUCED_BASE,
    reductions_applied: false,
    caveat: AYURDAYA_UNREDUCED_BASE_CAVEAT,
    judgment_flag: judgmentFlag('ayurdaya_unreduced_base_figures', AYURDAYA_UNREDUCED_BASE_CAVEAT, 'info'),
  }
}

/**
 * Annotate (non-mutating) every year-bearing row with `figure_kind` + `reductions_applied`.
 * Only adds keys — every stored value (fact_value_num, fact_value_text, fact_value_jsonb) is
 * passed through untouched. Rows with no year figure (e.g. maraka_grahas) are returned as-is.
 */
export function annotateAyurdayaYearRows(rows: readonly Row[], disclosure: AyurdayaFigureDisclosure | null): Row[] {
  if (!disclosure) return [...rows]
  return rows.map(r => (isAyurdayaYearsRow(r)
    ? { ...r, figure_kind: disclosure.figure_kind, reductions_applied: disclosure.reductions_applied }
    : r))
}

/**
 * chart_facts_query adapter: when the served rows carry Āyurdāya year figures, add a nested
 * `ayurdaya_figure_disclosure` object and a content-level `judgment_flags` entry. Returns the
 * result unchanged (same reference) otherwise, so every non-ayurdaya response is byte-identical.
 */
export function withAyurdayaFigureDisclosure<T extends { content: unknown; is_error: boolean }>(
  result: T,
  servedRows: readonly Row[],
): T {
  const disclosure = deriveAyurdayaFigureDisclosure(servedRows)
  if (!disclosure || !result.content || typeof result.content !== 'object' || Array.isArray(result.content)) return result
  const content = result.content as Record<string, unknown>
  const flags = Array.isArray(content['judgment_flags']) ? (content['judgment_flags'] as unknown[]) : []
  content['judgment_flags'] = [...flags, disclosure.judgment_flag]
  content['ayurdaya_figure_disclosure'] = {
    figure_kind: disclosure.figure_kind,
    reductions_applied: disclosure.reductions_applied,
    caveat: disclosure.caveat,
    applies_to: "rows with fact_category='ayurdaya' and fact_key total_years / *_contribution_years / applicable_method",
  }
  return result
}
