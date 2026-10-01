/**
 * canonical_formulas.ts — the ONE declaration of which `formula_id` is canonical for each
 * multi-formula `chart_facts` category (TS mirror).
 *
 * Why this exists (INVESTIGATION_L1_DUPLICATE_KEYS_v1_0.md, PR #2861; SS decision 2026-10-01).
 * `ga_sensitive` deliberately writes every classical variant of seven categories as separate
 * rows, one per `formula_id` (WP-1.8). `formula_id` is already part of the table's unique key, so
 * the 460 "duplicated" natural keys per chart are legitimate named variants, not defects. The
 * defect was on the READ side: readers that picked one row per (subject, key) without pinning the
 * formula served a physical-order-dependent winner. This table is what a reader pins to.
 *
 * MIRROR + PARITY. The Python mirror is `platform/python-sidecar/brahmagyan/canonical_formulas.py`
 * (a sibling module — brahmagyan/verification_vocab.py and l0_reference.py are frozen L0 digests
 * and are never edited for a constant). `platform/python-sidecar/tests/test_canonical_formulas_parity.py`
 * and `./__tests__/canonical_formulas.test.ts` each read BOTH files and assert equality
 * including the variants lists, so an edit to one side that is not made on the other fails CI.
 * The table below is deliberately written in a rigid one-entry-per-line shape those tests parse —
 * keep that shape when editing.
 *
 * STATUS: every canonical choice here is (R) PROVISIONAL until J1 (the acharya review) and is on
 * the J1 reviewers' list by name. `esoteric_point_mrityu` has NO canonical formula by design: the
 * three reckonings are all served with `formula_id` disclosed and no headline value, and any
 * reader that needs a single value returns an honest null with reason `no_canonical_formula`.
 *
 * The same table is read by the permanent guard
 * `platform/scripts/governance/check_fact_category_pinning.py` (it loads the Python mirror), which
 * REQUIRES every `chart_facts` SELECT on one of these categories to pin `formula_id` or carry an
 * explicit all-variants disclosure.
 */

export interface CategoryFormulas {
  /** The canonical `formula_id`, or null when the category has no canonical formula. */
  readonly canonical: string | null
  /**
   * Named variants, in disclosure order. When `canonical` is non-null this EXCLUDES it; when
   * `canonical` is null it lists every served formula.
   */
  readonly variants: readonly string[]
}

export const NO_CANONICAL_FORMULA_REASON = 'no_canonical_formula'

export const CANONICAL_FORMULA_STATUS = 'provisional_until_J1'

/**
 * A key that holds several formula rows in a category NOT declared in this table. There is no
 * canonical formula to prefer and none was ruled out, so the honest answer is a null headline with
 * THIS reason (never `no_canonical_formula`, which is a ruling about a declared category: Mrityu).
 */
export const UNDECLARED_MULTI_FORMULA_REASON = 'undeclared_multi_formula'

/** Served wherever variants are listed, so a reader cannot take list order for a ranking. */
export const FORMULA_ORDER_NOTE =
  'Order is the declared disclosure order, not a ranking: where a canonical formula exists it is listed first; ' +
  'where none does (esoteric_point_mrityu: bphs_ch39, saravali, tajik_aapamrityu) no formula is preferred over another.'

export const CANONICAL_FORMULAS: Readonly<Record<string, CategoryFormulas>> = {
  karaka_chara_position: { canonical: 'kn_rao_rahu_included', variants: ['parashari_rahu_excluded'] },
  esoteric_point_yogi: { canonical: 'bphs_93_20', variants: ['alt_96_40'] },
  esoteric_point_avayogi: { canonical: 'bphs_93_20', variants: ['alt_96_40'] },
  esoteric_point_brahma: { canonical: 'kn_rao_rahu_included', variants: ['parashari_rahu_excluded'] },
  esoteric_point_shiva: { canonical: 'kn_rao_rahu_included', variants: ['parashari_rahu_excluded'] },
  esoteric_point_vishnu: { canonical: 'kn_rao_rahu_included', variants: ['parashari_rahu_excluded'] },
  esoteric_point_mrityu: { canonical: null, variants: ['bphs_ch39', 'saravali', 'tajik_aapamrityu'] },
}

/** The Jaimini chara-karaka school the L1 build already pins (ga_structural karaka-web, §N.5). */
export const CANONICAL_KARAKA_SCHOOL = CANONICAL_FORMULAS['karaka_chara_position']!.canonical as string

export function isMultiFormulaCategory(category: string): boolean {
  return Object.prototype.hasOwnProperty.call(CANONICAL_FORMULAS, category)
}

/** Declared categories, in table order. */
export function multiFormulaCategories(): string[] {
  return Object.keys(CANONICAL_FORMULAS)
}

/** The canonical formula for a category; null for an undeclared category OR a no-canonical one. */
export function canonicalFormulaOf(category: string): string | null {
  return isMultiFormulaCategory(category) ? CANONICAL_FORMULAS[category]!.canonical : null
}

/** Every formula a declared category can serve: canonical first (if any), then the variants. */
export function allFormulasOf(category: string): string[] {
  if (!isMultiFormulaCategory(category)) return []
  const spec = CANONICAL_FORMULAS[category]!
  return spec.canonical ? [spec.canonical, ...spec.variants] : [...spec.variants]
}

export type FormulaRole = 'canonical' | 'variant' | 'no_canonical_formula'

/**
 * The role a row's formula plays in its category. Undeclared categories / NULL formula_id have no
 * role (null): they are not multi-formula rows and are served exactly as before.
 */
export function formulaRoleOf(category: string, formulaId: string | null | undefined): FormulaRole | null {
  if (formulaId == null || !isMultiFormulaCategory(category)) return null
  const { canonical } = CANONICAL_FORMULAS[category]!
  if (canonical === null) return NO_CANONICAL_FORMULA_REASON
  return formulaId === canonical ? 'canonical' : 'variant'
}

/**
 * Total, canonical-first rank for a (category, formula) pair — 0 for the canonical formula, then
 * the declared variant position + 1; an undeclared formula/category sorts last (stable by formula
 * id downstream). Used to order JS-side arrays; the SQL twin is `canonicalFirstOrderSql`.
 */
export function formulaRank(category: string, formulaId: string | null | undefined): number {
  if (formulaId == null || !isMultiFormulaCategory(category)) return 1_000_000
  const order = allFormulasOf(category)
  const idx = order.indexOf(formulaId)
  return idx === -1 ? 1_000_000 : idx
}

/**
 * SQL twin of `formulaRank`: a CASE expression that sorts the canonical formula of each declared
 * category first, then each declared variant in disclosure order, then everything else. Built only
 * from the constant above (never from request input), so it is a static string safe to inline into
 * an ORDER BY. Rows with a NULL formula_id fall into the final `ELSE` bucket.
 *
 * Use as `ORDER BY ..., ${canonicalFirstOrderSql()}, formula_id, fact_id` — the trailing
 * `formula_id, fact_id` terms make the order TOTAL (fact_id is the primary key).
 */
export function canonicalFirstOrderSql(categoryCol = 'fact_category', formulaCol = 'formula_id'): string {
  const whens: string[] = []
  for (const category of multiFormulaCategories()) {
    allFormulasOf(category).forEach((formula, idx) => {
      whens.push(`WHEN ${categoryCol} = '${category}' AND ${formulaCol} = '${formula}' THEN ${idx}`)
    })
  }
  return `CASE ${whens.join(' ')} ELSE 1000000 END`
}

/** The categories as a SQL-safe text[] literal for `= ANY(...)` (static, from the constant). */
export function multiFormulaCategoriesSqlList(): string {
  return `ARRAY[${multiFormulaCategories().map(c => `'${c}'`).join(', ')}]::text[]`
}

export interface FormulaVariantDisclosure {
  formula_id: string
  /** `canonical` | `variant` | `no_canonical_formula` (the category declares no canonical). */
  role: FormulaRole | 'undeclared'
  value: unknown
  fact_id: string | null
}

/**
 * Reduce all rows sharing one (category, subject, key) to a served shape that NEVER lets a
 * physical-order accident pick the headline:
 *   - `headline`: the canonical formula's value; `null` when the category has no canonical
 *     formula (reason `no_canonical_formula`) or when none of the rows is the canonical one;
 *   - `variants`: EVERY row, canonical first, each labelled with its formula_id and role.
 *
 * `rows` may arrive in any order; the result is ordered by `formulaRank`, then formula_id, then
 * fact_id (a total order).
 */
export function disclosePivotVariants(
  category: string,
  rows: ReadonlyArray<{ formula_id: string; value: unknown; fact_id: string | null }>,
): {
  headline: unknown
  headline_fact_id: string | null
  headline_reason: typeof NO_CANONICAL_FORMULA_REASON | 'canonical_formula_absent' | typeof UNDECLARED_MULTI_FORMULA_REASON | null
  variants: FormulaVariantDisclosure[]
} {
  const ordered = [...rows].sort((a, b) => {
    const ra = formulaRank(category, a.formula_id)
    const rb = formulaRank(category, b.formula_id)
    if (ra !== rb) return ra - rb
    if (a.formula_id !== b.formula_id) return a.formula_id < b.formula_id ? -1 : 1
    return String(a.fact_id ?? '') < String(b.fact_id ?? '') ? -1 : String(a.fact_id ?? '') > String(b.fact_id ?? '') ? 1 : 0
  })
  const canonical = canonicalFormulaOf(category)
  const variants: FormulaVariantDisclosure[] = ordered.map(r => ({
    formula_id: r.formula_id,
    role: formulaRoleOf(category, r.formula_id) ?? 'undeclared',
    value: r.value,
    fact_id: r.fact_id,
  }))
  if (isMultiFormulaCategory(category) && canonical === null) {
    return { headline: null, headline_fact_id: null, headline_reason: NO_CANONICAL_FORMULA_REASON, variants }
  }
  const head = canonical === null ? undefined : ordered.find(r => r.formula_id === canonical)
  if (!head) {
    // Undeclared category with several formulas, or the declared canonical row is absent: the
    // honest answer is null with a reason, never "whichever row sorted first".
    return {
      headline: null,
      headline_fact_id: null,
      headline_reason: isMultiFormulaCategory(category) ? 'canonical_formula_absent' : UNDECLARED_MULTI_FORMULA_REASON,
      variants,
    }
  }
  return { headline: head.value, headline_fact_id: head.fact_id, headline_reason: null, variants }
}

/**
 * Label rows of a flat page: every row of a declared multi-formula category with a non-NULL
 * `formula_id` gains `formula_role` (`canonical` | `variant` | `no_canonical_formula`). Rows of any
 * other category, and rows without a formula_id, are returned unchanged. Never drops or merges a row.
 */
export function labelFormulaRoles<T extends Record<string, unknown>>(rows: readonly T[]): Array<T & { formula_role?: FormulaRole }> {
  return rows.map(r => {
    const role = formulaRoleOf(String(r['fact_category']), r['formula_id'] as string | null | undefined)
    return role ? { ...r, formula_role: role } : r
  })
}

type CategoryPolicy = { canonical_formula_id: string | null; variants: string[]; no_canonical_reason?: typeof NO_CANONICAL_FORMULA_REASON }

/**
 * The canonical-formula policy for the declared categories among `categories`, served so a reader
 * of a flat page can see WHICH formula is the headline and that the choice is provisional.
 * Returns `null` when none of `categories` is a declared multi-formula category.
 */
export function formulaPolicyFor(categories: readonly string[]): {
  status: typeof CANONICAL_FORMULA_STATUS
  order_note: typeof FORMULA_ORDER_NOTE
  categories: Record<string, CategoryPolicy>
} | null {
  const out: Record<string, CategoryPolicy> = {}
  for (const c of categories) {
    if (!isMultiFormulaCategory(c) || out[c]) continue
    const spec = CANONICAL_FORMULAS[c]!
    out[c] = {
      canonical_formula_id: spec.canonical,
      variants: [...spec.variants],
      ...(spec.canonical === null ? { no_canonical_reason: NO_CANONICAL_FORMULA_REASON } : {}),
    }
  }
  return Object.keys(out).length > 0 ? { status: CANONICAL_FORMULA_STATUS, order_note: FORMULA_ORDER_NOTE, categories: out } : null
}
