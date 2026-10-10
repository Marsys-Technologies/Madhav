/**
 * Suvarna / migration 1268 (TI-L0-09) - STATIC contract: the attribution_state column on four L0 catalogues and the
 * token-exact backfill (unsourced / refuted). Never writes 'sourced', never changes a citation.
 *
 * The live proof (disposable PostgreSQL 15 and 17 as a NOSUPERUSER NOINHERIT amjis_app with USAGE but no CREATE on
 * schema public: apply, exact audited row sets, no other cell changed, CHECK enforced, trigger not fired, idempotent,
 * partial state, 7 drift cases, empty/missing tables, preset-state, silent-no-op and 16 mutants) is
 * python-sidecar/tests/test_migration_1268_l0_attribution_state_column.py. This file pins the text.
 */
import { describe, it, expect } from 'vitest'
import fs from 'fs'
import path from 'path'
import { PROTECTED_PUBLIC_SCHEMA_MIGRATIONS } from '../../../scripts/migrate'

const MIG = path.resolve(__dirname, '../../../migrations')
const FILE = '1268_l0_attribution_state_column.sql'
const SQL = fs.readFileSync(path.join(MIG, FILE), 'utf8')
const CODE = SQL.split('\n').filter(l => !l.trim().startsWith('--')).join('\n')

describe('migration 1268 - static contract', () => {
  it('adds one nullable column with a three-value CHECK to exactly the four audited tables', () => {
    expect(CODE).toContain("ARRAY['brahma_dosha_catalog', 'brahma_yoga_catalog', 'brahma_remedy_corpus', 'bg_transit_rules']")
    expect(CODE.match(/ADD COLUMN IF NOT EXISTS attribution_state text/g)).toHaveLength(1)
    expect(CODE.match(/\bADD COLUMN\b/g)).toHaveLength(1)
    expect(CODE).toContain("attribution_state IN (''sourced'', ''unsourced'', ''refuted'')")
    expect(CODE).toContain("attribution_state IS NULL OR")
    expect(CODE.match(/\bALTER TABLE\b/g)).toHaveLength(2) // ADD COLUMN, ADD CONSTRAINT (both dynamic, over the one list)
    expect(CODE).not.toMatch(/DROP COLUMN|DROP CONSTRAINT|RENAME|ALTER COLUMN|SET DATA TYPE/i)
  })

  it('classifies exactly the five audited token-exact classes with their audited counts and key hashes', () => {
    const rows = [...CODE.matchAll(/^\s*\('(\w+)',\s+'(\w+)',/gm)].map(m => m[1])
    expect(rows).toEqual(['dosha_placeholder', 'yoga_placeholder', 'remedy_placeholder', 'transit_refuted', 'transit_unsourced'])
    for (const h of ['358100cf4f432c341870c93c42a27c09', 'c59e915521bf783b2cf5b49ae8ce3df0', '018817ba07867f71b90461264e7b6a6d',
      'b71b9ac6de1c1eda2ae5d96ac6105037', '1656f780bb5ec60b40ad12a77444fd39']) expect(CODE).toContain(h)
    expect(CODE).toContain("classical_citations = '[{\"text_id\": \"classical_tradition\"}]'::jsonb")
    expect(CODE).toContain("source_citation = 'classical tradition (Jyotish)'")
    expect(CODE).toContain("classical_citation LIKE 'BPHS Ch.29 (Gochara Phala%'")
    expect(CODE).toContain("classical_citation LIKE 'UNSOURCED %'")
    // the states written are 'unsourced' and 'refuted' only
    const states = [...CODE.matchAll(/\b(\d+), '[0-9a-f]{32}', '(\w+)'\)/g)].map(m => `${m[1]}:${m[2]}`)
    expect(states).toEqual(['53:unsourced', '1:unsourced', '101:unsourced', '19:refuted', '6:unsourced'])
  })

  it("never writes 'sourced' and never changes a citation or any other column", () => {
    const stripped = CODE.replace("''sourced'', ''unsourced'', ''refuted''", '')
    expect(stripped).not.toMatch(/'sourced'/)
    expect(CODE).not.toMatch(/SET\s+(classical_citation|classical_citations|source_citation|source_chunk_ids)\b/i)
    const sets = [...CODE.matchAll(/UPDATE public\.%I SET (\w+) =/g)].map(m => m[1])
    expect(sets).toEqual(['attribution_state'])
    expect(CODE).toContain('AND attribution_state IS NULL') // a state set by anything else is never overwritten
    expect(CODE).not.toMatch(/\bINSERT INTO public\.|\bDELETE FROM\b|\bTRUNCATE\b|\bDROP TABLE\b/i)
  })

  it('is guarded and post-checked: drift raises, empty tables skip with a NOTICE, missing tables raise', () => {
    expect(CODE).toContain('has drifted from the audited rows')
    expect(CODE).toContain('fresh bootstrap')
    expect(CODE).toContain('does not exist')
    expect(CODE).toContain('is not %') // post-check: matching rows must carry exactly the audited state
    expect(CODE).toContain('GET DIAGNOSTICS v_rows = ROW_COUNT')
  })

  it('creates nothing in schema public (only a pg_temp table) and never touches the registry or grants', () => {
    const creates = [...CODE.matchAll(/\bCREATE\s+(\w+(?:\s+\w+)?)/gi)].map(m => m[1].toUpperCase())
    expect(creates).toEqual(['TEMP TABLE'])
    expect(CODE).toContain('ON COMMIT DROP')
    expect(CODE).not.toMatch(/\bGRANT\b|\bREVOKE\b|SECURITY DEFINER|\bCREATE (OR REPLACE )?(FUNCTION|TRIGGER|INDEX|VIEW|TABLE)\b/i)
    expect(CODE).not.toMatch(/asset_registry|asset_freshness/)
    expect(CODE).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/m)
  })

  it('starts with the transaction-local 5s lock_timeout', () => {
    expect(CODE.match(/\bSET LOCAL lock_timeout\b/g)).toHaveLength(1)
    expect(CODE.trimStart().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
  })

  it('states the header facts: NULL meaning, durability warning, writer half not done, no stale, privilege, NOT done', () => {
    expect(SQL).toContain('TI-L0-09')
    expect(SQL).toContain('WHAT \'NULL\' MEANS')
    expect(SQL).toContain('DURABILITY WARNING')
    expect(SQL).toContain('l0_doshas.py:1942-1944')
    expect(SQL).toContain('l0_yogas.py:2244-2249')
    expect(SQL).toContain('NO asset goes stale')
    expect(SQL).toContain('does NOT')
    expect(SQL).toContain('PRIVILEGE')
    expect(SQL).toContain('NOT DONE HERE')
    expect(SQL).toContain('TI-L0-10')
    expect(SQL).toContain('IDEMPOTENT')
  })

  it('is a ROUTINE migration (not protected), unique, in the 1200-1299 range, and its number is 1268', () => {
    expect(PROTECTED_PUBLIC_SCHEMA_MIGRATIONS.has(FILE)).toBe(false)
    expect(Number(FILE.slice(0, 4))).toBe(1268)
    expect(fs.readdirSync(MIG).filter(f => /^1268_/.test(f) && f !== FILE)).toEqual([])
  })
})
