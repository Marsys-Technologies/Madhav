/**
 * Certification migration 1363 — STATIC contract (ga_structural's integrity_check_sql, rewritten so chart_facts is read ONCE through one
 * leading `WITH gs_cf AS MATERIALIZED (...)` instead of ~330 times, with IDENTICAL semantics: NEW = OLD plus the inserted block plus the
 * rename chart_facts -> gs_cf at 299 uncorrelated references; the other 31 references stay on the base table).
 * The live proof (a disposable PostgreSQL cluster: OLD vs NEW on empty tables, a clean dataset, one injected violation per conjunct, a seeded
 * fuzz, negative controls, an EXPLAIN scan-node count, apply/guard/idempotency/serving effect) and the parse-tree identity proof are
 * python-sidecar/tests/test_migration_1363_ga_structural_integrity_speed.py. This file pins the text so a drive-by edit (a widened category
 * list, a renamed correlated reference, a dropped guard) is a deliberate, reviewed change.
 */
import { describe, it, expect } from 'vitest'
import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1363_ga_structural_integrity_single_scan_speed.sql'
const FIXTURE = path.resolve(
  __dirname,
  '../../../python-sidecar/tests/fixtures/ga_structural_1326/live_integrity_check_sql_pre1326_2026-10-07.sql',
)
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const HEADER = SQL.slice(0, SQL.indexOf("SET LOCAL lock_timeout")).replace(/^--/gm, ' ').replace(/\s+/g, ' ')
const md5 = (s: string): string => crypto.createHash('md5').update(s, 'utf8').digest('hex')

const PRE1326_MD5 = 'c56f9e12b2002269eb5f27a7abc42105'
const OLD_MD5 = 'fcd217e25127653ee28ad41c629946aa'
const NEW_MD5 = 'f49616e257f9a85de4f0cebf09fe2603'
const OLD_LEN = 208378
const NEW_LEN = 209602

// Migration 1326's single replacement, spelled independently of its migration/test: pre-1326 fixture + this = the live OLD text.
const L1326_OLD_LINE = "          WHEN re.retrograde_flag = 'retrograde' THEN 'weak'\n"
const L1326_NEW_BLOCK =
  '          -- Migration 1326 (node exclusion): the mean nodes Rahu/Ketu are always retrograde and ga_positions stores\n' +
  "          -- retrograde_flag 'retrograde' for them (N-185/N-187), but the retrograde composite downgrade does NOT apply to the\n" +
  "          -- nodes (their re_dignity is always 'neutral'); a node row therefore stays 'neutral'. Tara grahas are unchanged.\n" +
  "          WHEN re.retrograde_flag = 'retrograde' AND a.fact_subject NOT IN ('RAH_MEAN', 'KET_MEAN') THEN 'weak'\n"

const COLS = [
  'fact_id', 'chart_id', 'ayanamsha_id', 'build_id', 'fact_category', 'fact_subject', 'fact_key', 'fact_value_text', 'fact_value_num',
  'fact_value_jsonb', 'unit', 'verification_pass_status', 'computed_at',
]
const CATS = [
  'argala_natal_matrix', 'aspect_jaimini', 'aspect_jaimini_per_varga', 'aspect_matrix_summary', 'aspect_parashari_given',
  'aspect_parashari_per_varga', 'aspect_parashari_received', 'aspect_received_by_special_point', 'aspect_tajik', 'bhadra_flag',
  'bhava_bala_aspectual', 'bhava_bala_directional', 'bhava_bala_lord', 'bhava_bala_occupant', 'bhava_bala_positional',
  'bhava_bala_temporal', 'bhava_bala_total_extended', 'bhava_significance_link', 'chandra_bala_natal_baseline',
  'chart_center_of_gravity', 'chart_cluster', 'combustion_per_varga', 'composite_dispositor_strength', 'conjunction_per_varga',
  'conjunction_within_orb', 'contradiction_pair', 'convergence_count', 'dispositor_chain_per_varga', 'dispositor_tree',
  'graha_avastha_baladi', 'graha_avastha_deepta', 'graha_avastha_jagrad', 'graha_avastha_lifetime_exposure_summary',
  'graha_centrality', 'graha_composite_state_classification', 'graha_dignity_per_varga', 'graha_dispositor_chain',
  'graha_effective_dignity_modified_by_aspects', 'graha_functional_class_per_ascendant', 'graha_in_house_composite_strength',
  'graha_nakshatra_join', 'graha_position', 'graha_special_state_rollup', 'graha_tri_deva_role_strength',
  'graha_vargottama_amplification_factor', 'graha_yoga_karaka_flag', 'graha_yuddha_per_varga',
  'house_strength_classification_rollup', 'jaimini_tri_deva_role_per_graha', 'kala_sarpa_per_varga', 'karaka_bhava_concordance',
  'karaka_house_lord_overlap_flag', 'karakatva_strength_per_significance', 'lord_aspects_lord_per_varga', 'lord_in_house_per_varga',
  'nakshatra_dispositor_chain', 'net_argala_per_varga', 'nway_config_per_varga', 'panchaka_flag', 'panchanga_karana',
  'panchanga_nakshatra_moon', 'parivartana_per_varga', 'pranic_strength_per_graha', 'sambandha_grade',
  'tara_bala_natal_baseline', 'vargottama_per_varga', 'virodha_argala_natal_matrix',
]
// The 31 references that STAY on the base table (correlated EXISTS 25, correlated scalar sublinks 3, LATERAL subselects 4): 1-based line
// numbers in the OLD text. A CTE has no index, so renaming these would turn a per-outer-row index probe into a rescan.
const KEPT = [
  393, 625, 634, 816, 849, 1129, 1130, 1132, 1378, 1405, 1420, 1766, 1792, 1879, 2224, 2399, 2405, 2478, 2504, 2525, 2853, 3147, 3170,
  3253, 3328, 3343, 3471, 3490, 3554, 3643, 3710,
]
const ANCHOR = 'SELECT\n  -- (a) amplification_factor domain:'

const PRE = fs.readFileSync(FIXTURE, 'utf8')
const OLD = PRE.replace(L1326_OLD_LINE, () => L1326_NEW_BLOCK)
const NEW = /\$nt\$([\s\S]*?)\$nt\$/.exec(SQL)?.[1] ?? ''
const CF = /\bchart_facts\b/
const OLD_LINES = OLD.split('\n')
const K = OLD.indexOf(ANCHOR)
const BLOCK = NEW.slice(K, NEW.indexOf(ANCHOR))
const BODY = NEW.slice(0, K) + NEW.slice(K + BLOCK.length)

describe('migration 1363 — static contract', () => {
  it('pins the live OLD text (pre-1326 fixture md5, then + migration 1326 = md5 and length of the text 1326 left)', () => {
    expect(md5(PRE)).toBe(PRE1326_MD5)
    expect(md5(OLD)).toBe(OLD_MD5)
    expect(OLD).toHaveLength(OLD_LEN)
  })

  it('NEW (the $nt$ literal) hashes to the md5 and length the migration names', () => {
    expect(md5(NEW)).toBe(NEW_MD5)
    expect(NEW).toHaveLength(NEW_LEN)
    expect(SQL.split('$nt$')).toHaveLength(3)
    expect(NEW).not.toContain('$m1363$')
  })

  it('NEW is OLD with the one block inserted at the anchor and the rename applied: dropping the block and renaming back is OLD byte for byte', () => {
    expect(OLD.split(ANCHOR)).toHaveLength(2)
    expect(NEW.split(ANCHOR)).toHaveLength(2)
    expect(BODY.split('gs_cf')).toHaveLength(300) // 299 renamed references
    expect(OLD).not.toContain('gs_cf')
    expect(BODY.replace(/gs_cf/g, 'chart_facts')).toBe(OLD)
  })

  it('the inserted block is comment lines then ONE materialized CTE over exactly the 13 columns and the 67 categories', () => {
    const lines = BLOCK.split('\n')
    const w = lines.findIndex(l => l.startsWith('WITH gs_cf AS MATERIALIZED ('))
    expect(w).toBeGreaterThanOrEqual(1)
    expect(lines.slice(0, w).every(l => l.startsWith('-- '))).toBe(true)
    const expected =
      'WITH gs_cf AS MATERIALIZED ( SELECT ' + COLS.join(', ') + ' FROM chart_facts WHERE fact_category IN ( ' +
      CATS.map(c => `'${c}'`).join(', ') + ' ) ) '
    expect(lines.slice(w).join('\n').replace(/\s+/g, ' ')).toBe(expected)
    expect(COLS).toHaveLength(13)
    expect(new Set(CATS).size).toBe(67)
    expect([...CATS].sort()).toEqual(CATS)
  })

  it('the 67 categories are re-derived from the text: every fact_category literal except the two chart_divisionals-only ones', () => {
    const code = OLD.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
    expect((code.match(/fact_category/g) ?? []).length).toBe((code.match(/fact_category\s*(?:=\s*'|IN\s*\()/g) ?? []).length)
    const seen = new Set<string>()
    for (const m of code.matchAll(/fact_category\s*(?:=\s*'([A-Za-z0-9_]+)'|IN\s*\(([^)]*)\))/g)) {
      if (m[1]) seen.add(m[1])
      else for (const x of (m[2] ?? '').matchAll(/'([A-Za-z0-9_]+)'/g)) seen.add(x[1])
    }
    const divisionalsOnly = ['varga_position', 'varga_vargottama_flag']
    expect([...seen].filter(c => !divisionalsOnly.includes(c)).sort()).toEqual(CATS)
    expect(divisionalsOnly.every(c => seen.has(c))).toBe(true)
  })

  it('exactly 330 chart_facts code references, one per line: 299 renamed, the 31 pinned lines untouched', () => {
    const codeLines = OLD_LINES.map((l, i) => [i + 1, l] as const).filter(([, l]) => CF.test(l) && !l.trim().startsWith('--'))
    expect(codeLines).toHaveLength(330)
    expect(codeLines.every(([, l]) => (l.match(/\bchart_facts\b/g) ?? []).length === 1)).toBe(true)
    expect(KEPT).toHaveLength(31)
    expect(KEPT.every(n => codeLines.some(([m]) => m === n))).toBe(true)
    const bodyLines = BODY.split('\n')
    expect(bodyLines).toHaveLength(OLD_LINES.length)
    const changed = bodyLines.map((l, i) => (l !== OLD_LINES[i] ? i + 1 : 0)).filter(Boolean)
    expect(changed).toEqual(codeLines.map(([n]) => n).filter(n => !KEPT.includes(n)))
    expect(changed).toHaveLength(299)
    for (const n of KEPT) expect(bodyLines[n - 1]).toBe(OLD_LINES[n - 1])
  })

  it('the arbitrary-choice sublinks read the base table: the one ORDER BY...LIMIT (uu2 p) and the one bare LIMIT (conjunction_within_orb cwo)', () => {
    const limits = OLD_LINES.map((l, i) => (/^\s*LIMIT\b/.test(l) ? i + 1 : 0)).filter(Boolean)
    expect(limits).toEqual([853, 3501])
    expect(KEPT).toContain(849)
    expect(KEPT).toContain(3490)
  })

  it('the migration carries both md5s', () => {
    expect(CODE).toContain(`c_old_md5  constant text := '${OLD_MD5}'`)
    expect(CODE).toContain(`c_new_md5  constant text := '${NEW_MD5}'`)
  })

  it('is ONE md5-guarded UPDATE of one column of the ga_structural row; no DDL, no transaction control, no index', () => {
    expect(CODE.match(/\bUPDATE asset_registry\b/g)).toHaveLength(1)
    expect(CODE).toContain("WHERE asset_id = 'ga_structural'\n     AND md5(integrity_check_sql) = c_old_md5;")
    expect(CODE.match(/\bSET (?:LOCAL )?[a-z_]+ =/g)).toEqual(['SET LOCAL lock_timeout =', 'SET integrity_check_sql ='])
    expect(CODE).toContain('SET integrity_check_sql = c_new_text')
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT|ROLLBACK)\s*;/m)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|INSERT|DELETE)\b/im)
  })

  it('starts with lock_timeout, NOTICEs (never raises) on a foreign or already-new text, raises only when the update did not take', () => {
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE).toContain('is not the text this migration was written against')
    expect(CODE).toContain('NO-OP')
    expect(CODE).toContain('already carries the single-scan rewrite')
    expect(CODE.match(/RAISE EXCEPTION/g)).toHaveLength(1)
    expect(CODE.match(/RAISE NOTICE/g)).toHaveLength(3)
    expect(CODE).toContain('update did not take')
    expect(CODE.indexOf('v_md5 = c_new_md5')).toBeLessThan(CODE.indexOf('UPDATE asset_registry'))
    expect(CODE.indexOf('v_md5 IS DISTINCT FROM c_old_md5')).toBeLessThan(CODE.indexOf('UPDATE asset_registry'))
    expect(CODE.indexOf('UPDATE asset_registry')).toBeLessThan(CODE.indexOf('RAISE EXCEPTION'))
  })

  it('states the header facts: problem, scan analysis, rewrite, equivalence, no index, no timing claim, trigger effect, verification, rollback', () => {
    for (const n of ['THE PROBLEM', 'THE DOMINANT SCAN', 'THE REWRITE', 'IDENTICAL SEMANTICS', 'WHY NO INDEX', 'EXPECTED EFFECT',
      'NOT a measurement', 'GUARD AND WHAT HAPPENS WHEN IT DOES NOT MATCH', 'SERVING EFFECT AT APPLY', 'nirmana_registry_receipt_invalidation',
      "STALES ga_structural's freshness rows", 'VERIFICATION BY PRODUCTION STRUCTURE', 'ROLLBACK', OLD_MD5, NEW_MD5, String(NEW_LEN)]) {
      expect(HEADER).toContain(n)
    }
  })

  it('is a ROUTINE migration (not protected) with a unique number', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    expect(fs.readdirSync(MIG).filter(f => /^1363_/.test(f) && f !== FILE)).toEqual([])
  })
})
