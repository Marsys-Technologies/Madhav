/**
 * canonical_formulas.test.ts — parity with the Python mirror + the pure helpers every reader uses.
 *
 * PARITY: this test READS the Python mirror
 * (platform/python-sidecar/brahmagyan/canonical_formulas.py) and asserts it equals the TS table,
 * including every variants list and the scalar constants. The Python-side twin
 * (python-sidecar/tests/test_canonical_formulas_parity.py) reads both files too, so the mirror is
 * checked whichever CI job runs. The Python table is parsed by a strict one-entry-per-line regex; a
 * reformat it cannot read FAILS here rather than silently skipping.
 */
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  allFormulasOf,
  canonicalFirstOrderSql,
  CANONICAL_FORMULA_STATUS,
  CANONICAL_FORMULAS,
  CANONICAL_KARAKA_SCHOOL,
  canonicalFormulaOf,
  disclosePivotVariants,
  formulaPolicyFor,
  formulaRank,
  formulaRoleOf,
  isMultiFormulaCategory,
  labelFormulaRoles,
  multiFormulaCategories,
  NO_CANONICAL_FORMULA_REASON,
} from '../canonical_formulas'

function findRepoRoot(): string {
  let dir = __dirname
  for (let i = 0; i < 12; i++) {
    try {
      readFileSync(path.join(dir, 'platform/python-sidecar/brahmagyan/canonical_formulas.py'))
      return dir
    } catch {
      dir = path.dirname(dir)
    }
  }
  throw new Error('repo root not found from ' + __dirname)
}

function parsePythonTable(text: string): Record<string, { canonical: string | null; variants: string[] }> {
  const start = text.indexOf('CANONICAL_FORMULAS = {')
  const block = text.slice(start, text.indexOf('\n}\n', start))
  const out: Record<string, { canonical: string | null; variants: string[] }> = {}
  const re = /^\s{4}"([a-z_]+)":\s*\{"canonical":\s*(None|"[^"]*"),\s*"variants":\s*\[([^\]]*)\]\},?\s*$/gm
  let m: RegExpExecArray | null
  while ((m = re.exec(block)) !== null) {
    out[m[1]!] = {
      canonical: m[2] === 'None' ? null : m[2]!.slice(1, -1),
      variants: m[3]!.split(',').map(v => v.trim().replace(/^"|"$/g, '')).filter(Boolean),
    }
  }
  return out
}

describe('canonical_formulas — TS / Python parity', () => {
  const py = readFileSync(path.join(findRepoRoot(), 'platform/python-sidecar/brahmagyan/canonical_formulas.py'), 'utf8')
  const pyTable = parsePythonTable(py)

  it('parses all seven declared categories from the Python mirror', () => {
    expect(Object.keys(pyTable)).toHaveLength(7)
  })

  it('tables are equal: categories (in order), canonical formula, and every variants list in order', () => {
    expect(Object.keys(pyTable)).toEqual(multiFormulaCategories())
    for (const cat of multiFormulaCategories()) {
      expect(pyTable[cat]!.canonical, cat).toBe(CANONICAL_FORMULAS[cat]!.canonical)
      expect(pyTable[cat]!.variants, cat).toEqual([...CANONICAL_FORMULAS[cat]!.variants])
    }
  })

  it('scalar constants are equal', () => {
    expect(py).toContain(`NO_CANONICAL_FORMULA_REASON = "${NO_CANONICAL_FORMULA_REASON}"`)
    expect(py).toContain(`CANONICAL_FORMULA_STATUS = "${CANONICAL_FORMULA_STATUS}"`)
  })
})

describe('canonical_formulas — the SS-ruled values', () => {
  it('Yogi/Avayogi: bphs_93_20 canonical, alt_96_40 a named variant', () => {
    for (const c of ['esoteric_point_yogi', 'esoteric_point_avayogi']) {
      expect(canonicalFormulaOf(c)).toBe('bphs_93_20')
      expect(allFormulasOf(c)).toEqual(['bphs_93_20', 'alt_96_40'])
    }
  })
  it('chara karaka: kn_rao_rahu_included canonical (the L1 pin), parashari_rahu_excluded a named variant', () => {
    expect(canonicalFormulaOf('karaka_chara_position')).toBe('kn_rao_rahu_included')
    expect(CANONICAL_KARAKA_SCHOOL).toBe('kn_rao_rahu_included')
    expect(allFormulasOf('karaka_chara_position')).toEqual(['kn_rao_rahu_included', 'parashari_rahu_excluded'])
  })
  it('Mrityu: no canonical, all three served', () => {
    expect(canonicalFormulaOf('esoteric_point_mrityu')).toBeNull()
    expect(allFormulasOf('esoteric_point_mrityu')).toEqual(['bphs_ch39', 'saravali', 'tajik_aapamrityu'])
    expect(formulaRoleOf('esoteric_point_mrityu', 'saravali')).toBe(NO_CANONICAL_FORMULA_REASON)
  })
  it('undeclared categories are not multi-formula', () => {
    expect(isMultiFormulaCategory('graha_position')).toBe(false)
    expect(formulaRoleOf('graha_position', 'anything')).toBeNull()
    expect(allFormulasOf('graha_position')).toEqual([])
  })
})

describe('canonical_formulas — ranking, SQL twin, labelling', () => {
  it('formulaRank puts the canonical first, then variants, then everything else', () => {
    expect(formulaRank('esoteric_point_yogi', 'bphs_93_20')).toBe(0)
    expect(formulaRank('esoteric_point_yogi', 'alt_96_40')).toBe(1)
    expect(formulaRank('esoteric_point_yogi', 'surprise')).toBeGreaterThan(1)
    expect(formulaRank('esoteric_point_yogi', null)).toBeGreaterThan(1)
  })

  it('canonicalFirstOrderSql is a static CASE listing every declared (category, formula) pair', () => {
    const sql = canonicalFirstOrderSql()
    expect(sql.startsWith('CASE ')).toBe(true)
    expect(sql.endsWith(' ELSE 1000000 END')).toBe(true)
    expect(sql).toContain("WHEN fact_category = 'esoteric_point_yogi' AND formula_id = 'bphs_93_20' THEN 0")
    expect(sql).toContain("WHEN fact_category = 'esoteric_point_yogi' AND formula_id = 'alt_96_40' THEN 1")
    expect(sql).toContain("WHEN fact_category = 'karaka_chara_position' AND formula_id = 'kn_rao_rahu_included' THEN 0")
    // Mrityu has no canonical: every variant ranks by declared position, none is ranked "first canonical"
    expect(sql).toContain("WHEN fact_category = 'esoteric_point_mrityu' AND formula_id = 'bphs_ch39' THEN 0")
    // no user input can reach it: only identifier-safe tokens
    expect(sql).not.toMatch(/\$\d/)
  })

  it('labelFormulaRoles labels declared rows and leaves every other row untouched', () => {
    const rows = [
      { fact_category: 'esoteric_point_yogi', formula_id: 'bphs_93_20', v: 1 },
      { fact_category: 'esoteric_point_yogi', formula_id: 'alt_96_40', v: 2 },
      { fact_category: 'esoteric_point_mrityu', formula_id: 'saravali', v: 3 },
      { fact_category: 'graha_position', formula_id: null, v: 4 },
      { fact_category: 'arudha_pada', formula_id: 'wholesign_from_lagna:1indexed:v2', v: 5 },
    ]
    const out = labelFormulaRoles(rows)
    expect(out.map(r => (r as { formula_role?: string }).formula_role)).toEqual([
      'canonical', 'variant', 'no_canonical_formula', undefined, undefined,
    ])
    expect(out).toHaveLength(rows.length) // never drops a row
  })

  it('formulaPolicyFor names the canonical / variants / provisional status for declared categories only', () => {
    expect(formulaPolicyFor(['graha_position', 'arudha_pada'])).toBeNull()
    const p = formulaPolicyFor(['esoteric_point_mrityu', 'esoteric_point_yogi', 'graha_position'])!
    expect(p.status).toBe('provisional_until_J1')
    expect(p.categories['esoteric_point_yogi']).toEqual({ canonical_formula_id: 'bphs_93_20', variants: ['alt_96_40'] })
    expect(p.categories['esoteric_point_mrityu']).toMatchObject({ canonical_formula_id: null, no_canonical_reason: 'no_canonical_formula' })
    expect(p.categories['graha_position']).toBeUndefined()
  })
})

describe('disclosePivotVariants — arrival order can never pick the headline', () => {
  const yogi = [
    { formula_id: 'alt_96_40', value: 355.68, fact_id: 'f-alt' },
    { formula_id: 'bphs_93_20', value: 352.35, fact_id: 'f-bphs' },
  ]
  for (const order of [yogi, [...yogi].reverse()]) {
    it(`Yogi headline is bphs_93_20 and variants are canonical-first (${order[0]!.formula_id} arrives first)`, () => {
      const d = disclosePivotVariants('esoteric_point_yogi', order)
      expect(d.headline).toBe(352.35)
      expect(d.headline_fact_id).toBe('f-bphs')
      expect(d.headline_reason).toBeNull()
      expect(d.variants.map(v => [v.formula_id, v.role])).toEqual([['bphs_93_20', 'canonical'], ['alt_96_40', 'variant']])
    })
  }

  it('Mrityu has NO headline value: null with reason no_canonical_formula, all three disclosed', () => {
    const d = disclosePivotVariants('esoteric_point_mrityu', [
      { formula_id: 'tajik_aapamrityu', value: 247.8, fact_id: 'c' },
      { formula_id: 'bphs_ch39', value: 96.4, fact_id: 'a' },
      { formula_id: 'saravali', value: 8.0, fact_id: 'b' },
    ])
    expect(d.headline).toBeNull()
    expect(d.headline_fact_id).toBeNull()
    expect(d.headline_reason).toBe('no_canonical_formula')
    expect(d.variants.map(v => v.formula_id)).toEqual(['bphs_ch39', 'saravali', 'tajik_aapamrityu'])
    expect(d.variants.every(v => v.role === 'no_canonical_formula')).toBe(true)
  })

  it('a declared category whose canonical row is absent yields an honest null, never the variant as headline', () => {
    const d = disclosePivotVariants('karaka_chara_position', [{ formula_id: 'parashari_rahu_excluded', value: 'Mercury', fact_id: 'p' }])
    expect(d.headline).toBeNull()
    expect(d.headline_reason).toBe('canonical_formula_absent')
    expect(d.variants[0]).toMatchObject({ formula_id: 'parashari_rahu_excluded', role: 'variant' })
  })
})
