/**
 * Suvarna / migration 1271 (WAVE-1) - STATIC contract: bg_transit_engine honest attribution (citations only, no numeric
 * value), the re-seal of the two integrity digests that cover the citation column, the description fix and the comments.
 *
 * The live proof (disposable PostgreSQL 15 and 17 as a NOSUPERUSER NOINHERIT amjis_app with USAGE but no CREATE on
 * schema public, loaded with the audited production rows and the unmodified production integrity texts: apply, numbers
 * identical, exactly the audited registry cells, both re-sealed checks read true, the real deps_unsatisfied effect on the
 * six bg_transit_rules dependents, module == migration lockstep, idempotent re-run, 7 drift cases, empty table, swallowed
 * UPDATE and 19 mutants) is python-sidecar/tests/test_migration_1271_bg_transit_engine_honest_attribution.py.
 * This file pins the text.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const SIDECAR = path.resolve(__dirname, '../../../python-sidecar')
const FILE = '1271_bg_transit_engine_honest_attribution.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')
const MODULE = fs.readFileSync(path.join(SIDECAR, 'brahmagyan/l0_transit.py'), 'utf8')

const OLD = 'e2dafc84d7fef9b8a05ad01b98b036686e8ec0af9694a4d43ac4b2b8c425797b'
const NEW = 'e5c09a112502b241cbd4aecf5ae30cfb2a93423f928c84a94dee37e6818b8c3d'

describe('migration 1271 - static contract', () => {
  it('updates only the citation column of bg_transit_engine (no numeric column is ever SET)', () => {
    const sets = [...CODE.matchAll(/UPDATE bg_transit_engine\s+SET (\w+)/g)].map(m => m[1])
    expect(sets).toEqual(['classical_citation'])
    expect(CODE).not.toMatch(/avg_daily_motion_deg\s*=|zodiac_period_days\s*=|sign_residence_days\s*=/)
    expect(CODE).toContain("CASE WHEN graha = 'jupiter' THEN cit_jupiter ELSE cit_unsourced END")
    expect(CODE).toContain("'BPHS Ch.22 (Graha Gati ' || chr(8212) || ' Planetary Motion)'")
    expect(CODE).toContain('PARTLY SOURCED')
    expect(CODE).toContain('UNSOURCED - modern mean value')
    // the only classical support is Jupiter's round figure, with the corpus pointers
    for (const ref of ['yavana_jataka PG900:C1', 'PG662:C1', 'bphs PG933:C1']) expect(CODE).toContain(ref)
  })

  it('re-seals exactly the two checks by replacing the one digest literal, with the pinned old and new digests', () => {
    expect(CODE).toContain(`old_hash   constant text := '${OLD}'`)
    expect(CODE).toContain(`new_hash   constant text := '${NEW}'`)
    expect(CODE.match(/replace\(integrity_check_sql, old_hash, new_hash\)/g)).toHaveLength(2)
    expect(CODE).toContain("WHERE asset_id = 'bg_transit_engine' AND md5(integrity_check_sql) = engine_sql_md5")
    expect(CODE).toContain("WHERE asset_id = 'bg_transit_rules' AND md5(integrity_check_sql) = rules_sql_md5")
    for (const md5 of ['9c1b1f5b6792fc4643d689e5124fa554', 'a3ded694827457ffaf640d24ff1e4057', '3ffe36c1c59b3bfac653fd198ce3cf46']) expect(CODE).toContain(md5)
    // the rules' own digest and the moorti digest are never touched or named
    expect(CODE).not.toContain('1dbdd265cf0e04edd26aebde054f34d9034be38bfabc8102085b0127196a598d')
    expect(CODE).not.toContain('b411c02abb7fec89c971353190f1ebe117a31a85e1bba06aeadc6509d0256450')
  })

  it('is guarded and post-checked: audited pre-state or already-applied, 9 rows, recomputed digest, both checks executed', () => {
    expect(CODE).toContain('has drifted from the audited state')
    expect(CODE).toContain('is empty (fresh bootstrap')
    expect(CODE).toContain('already at the new state')
    expect(CODE).toContain('v_rows <> 9')
    expect(CODE).toContain('is not the pinned')
    expect(CODE).toContain('EXECUTE v_engine_sql INTO v_ok')
    expect(CODE).toContain('does not read true after the update')
    expect(CODE.match(/FOR UPDATE/g)!.length).toBeGreaterThanOrEqual(2)
  })

  it('only writes bg_transit_engine and the two registry rows; creates nothing; grants nothing', () => {
    expect(CODE).not.toMatch(/UPDATE bg_transit_rules|UPDATE bg_transit_moorti|INSERT INTO|DELETE FROM|TRUNCATE|DROP /i)
    expect(CODE).not.toMatch(/^\s*(CREATE|ALTER|GRANT|REVOKE)\b/im)
    expect(CODE).not.toMatch(/SECURITY DEFINER|\bCREATE\b/i)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
    expect(CODE.match(/^COMMENT ON TABLE bg_transit_engine IS/gm)).toHaveLength(1)
    expect(CODE.match(/^COMMENT ON COLUMN bg_transit_engine\./gm)).toHaveLength(4)
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('is in lockstep with the writer seed module: same strings, no refuted constant, numbers unmoved', () => {
    const uns = CODE.match(/cit_unsourced constant text := \$c\$([\s\S]*?)\$c\$;/)![1]
    const jup = CODE.match(/cit_jupiter   constant text := \$c\$([\s\S]*?)\$c\$;/)![1]
    // the python constants are implicit string concatenations; compare after joining
    const pyConst = (name: string): string => {
      const m = MODULE.match(new RegExp(`${name} = \\(([\\s\\S]*?)\\n\\)`))!
      return [...m[1].matchAll(/"((?:[^"\\\\]|\\\\.)*)"/g)].map(x => x[1]).join('')
    }
    expect(pyConst('TRANSIT_ENGINE_CITATION_UNSOURCED')).toBe(uns)
    expect(pyConst('TRANSIT_ENGINE_CITATION_JUPITER')).toBe(jup)
    expect(MODULE).not.toMatch(/^BPHS_CH22\s*=/m)
    expect(MODULE).not.toMatch(/"classical_citation":\s*BPHS_CH22/)
    expect(MODULE.match(/"classical_citation": TRANSIT_ENGINE_CITATION_UNSOURCED,/g)).toHaveLength(8)
    expect(MODULE.match(/"classical_citation": TRANSIT_ENGINE_CITATION_JUPITER,/g)).toHaveLength(1)
    for (const n of ['0.9856', '365.25', '30.44', '13.1764', '27.32', '2.28', '0.5240', '686.97', '45.0', '1.3833', '87.97', '14.0',
      '0.0831', '4332.59', '361.05', '1.2000', '224.70', '23.0', '0.0335', '10759.22', '913.37', '-0.0529', '6793.50', '548.00']) {
      expect(MODULE).toContain(n)
    }
  })

  it('states the header facts: refuted citation, why no value changed, lockstep + known-red inventory, staleness and its dependents, NOT done', () => {
    for (const needle of ['WAVE-1', 'is refuted', 'PG22:C1', 'WHY NO VALUE IS CHANGED', '1 deg 23 min', 'LOCKSTEP WITH THE WRITER',
      'KNOWN RED', 'nirmana-writer-digests.json', 'Assets that go stale: bg_transit_rules ONLY', 'ka_moorti_nirnaya', 'ka_gochara_resonance',
      'bg_transit_rules(receipt:stale)', 'PRIVILEGE', 'IDEMPOTENT', 'NOT DONE HERE', '[EXTERNAL_COMPUTATION_REQUIRED]',
      'asset_registry_seed.ts', 'query_transit_engine']) expect(SQL).toContain(needle)
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range, and its number is 1271', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    expect(Number(FILE.slice(0, 4))).toBe(1271)
    expect(fs.readdirSync(MIG).filter(f => /^1271_/.test(f) && f !== FILE)).toEqual([])
  })
})
