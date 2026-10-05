import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  nirmanaDetectorSqlHasBindPlaceholder,
  nirmanaReadOnlyDetectorSqlAcceptable,
} from '@/lib/nirmana-elevation/definitions'

/**
 * Migration 1254 -- ga_sensitive integrity_check_sql conjunct (a) vocabulary relaxation
 * ({two_pass_verified, floored} -> {two_pass_verified, floored, single, computed_extension}).
 *
 * Static shape test (the behaviour -- the real trigger staling ga_sensitive on every chart, the md5 guard, the
 * idempotent re-run, the window apply orders, the four-tier vocabulary against synthetic chart_facts and the
 * six guard mutations -- is proved against disposable PostgreSQL 15 and 17 by
 * python-sidecar/tests/test_migration_1254_ga_sensitive_tiers.py). Here: the migration is a routine, guarded,
 * asset_registry-only UPDATE of one column of one row, the new detector SQL still passes the REAL
 * elevation-pipeline validators (read-only, no bind placeholder, because the freeze-time integrity_verified
 * detector runs it standalone), it differs from migration 743's base text ONLY inside conjunct (a), and the
 * vocabulary is an explicit list of exactly four tiers. HELD: merges only in the S-L1 window W1, before the
 * ga_sensitive rebuild (see the file header).
 */
const migration = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/1254_nirmana_l1_ga_sensitive_integrity_tier_vocabulary.sql'),
  'utf8',
)
const base743 = fs.readFileSync(
  path.resolve(process.cwd(), 'migrations/743_nirmana_l1_ga_sensitive_integrity_contract.sql'),
  'utf8',
)

const BASE_MD5 = '77099c39ae07a2dfb18c8812d9345c2d'
const NEW_MD5 = 'd6dc29259125e4007c3506a42d983296'
const OLD_LIST = "AND verification_pass_status NOT IN ('two_pass_verified', 'floored')"
const NEW_LIST = "AND verification_pass_status NOT IN ('two_pass_verified', 'floored', 'single', 'computed_extension')"

function extractDetectorSql(source: string): string {
  const start = source.indexOf('$ck$')
  const end = source.lastIndexOf('$ck$')
  if (start === -1 || end === -1 || start === end) {
    throw new Error('could not locate the $ck$-delimited detector SQL')
  }
  return source.slice(start + 4, end)
}

describe('migration 1254 -- ga_sensitive integrity_check_sql tier vocabulary', () => {
  it('is a guarded one-row UPDATE of asset_registry, with no transaction control and no DDL', () => {
    expect(migration).toMatch(/UPDATE asset_registry\s+SET integrity_check_sql = \$ck\$/)
    expect(migration).toMatch(
      /WHERE asset_id = 'ga_sensitive'\n {2}AND md5\(integrity_check_sql\) = '77099c39ae07a2dfb18c8812d9345c2d';/,
    )
    const executable = migration.split('\n').filter((l) => !l.trimStart().startsWith('--')).join('\n')
    expect(executable.match(/UPDATE asset_registry/g)).toHaveLength(1)
    expect(migration).toMatch(/SET LOCAL lock_timeout = '5s'/)
    expect(migration).toMatch(/\$pre\$/)
    expect(migration).toMatch(/\$post\$/)
    expect(migration).not.toMatch(/^\s*(BEGIN|COMMIT)\s*;/im)
    expect(migration.split('$ck$')).toHaveLength(3) // exactly two delimiters, never in a comment
    const outsideDetector = migration.slice(0, migration.indexOf('$ck$')) + migration.slice(migration.lastIndexOf('$ck$'))
    expect(outsideDetector.replace(/--[^\n]*/g, '')).not.toMatch(/\b(ALTER|CREATE|DROP|GRANT|REVOKE|TRUNCATE|DELETE|INSERT)\b/i)
  })

  it('starts with lock_timeout, accepts only the base or the target text, and states its serving effect', () => {
    const code = migration.split('\n').filter((l) => !l.trimStart().startsWith('--')).join('\n')
    expect(code.trim().startsWith("SET LOCAL lock_timeout = '5s';")).toBe(true)
    expect(code).toContain(`'${BASE_MD5}'`)
    expect(code).toContain(`'${NEW_MD5}'`)
    for (const needle of ['SERVING EFFECT AT APPLY', 'nirmana_registry_receipt_invalidation', 'ON EVERY CHART',
      'IDEMPOTENT SHAPE', 'VERIFICATION BY PRODUCTION STRUCTURE', 'HELD', 'ORDERING', 'FIVE assets',
      'NEVER EDIT THIS FILE AFTER IT HAS BEEN APPLIED', 'BEFORE the ga_sensitive rebuild in W4/W6']) {
      expect(migration.toUpperCase()).toContain(needle.toUpperCase())
    }
    expect(migration).toContain('{ga_structural (1221), ga_vargas (1222, 1223, 1226), ga_dashas (1226), ga_yoga (1226), ga_sensitive (1254)}')
  })

  it('the detector is read-only and carries no bind placeholder (the real elevation-pipeline validator)', () => {
    const detectorSql = extractDetectorSql(migration)
    expect(nirmanaReadOnlyDetectorSqlAcceptable(detectorSql)).toBe(true)
    expect(nirmanaDetectorSqlHasBindPlaceholder(detectorSql)).toBe(false)
    expect(detectorSql.trimEnd().endsWith('AS integrity_passed')).toBe(true)
  })

  it('differs from migration 743 only inside conjunct (a): (b) and (c) are byte-identical', () => {
    const base = extractDetectorSql(base743)
    const next = extractDetectorSql(migration)
    expect(base).toHaveLength(3069)
    expect(next).toHaveLength(3303)
    const tail = (s: string) => s.slice(s.indexOf("  -- (b) special_lagna's sign_lord"))
    const head = (s: string) => s.slice(0, s.indexOf('  -- (a) verification_pass_status vocabulary'))
    expect(tail(next)).toBe(tail(base))
    expect(head(next)).toBe(head(base))
    expect(base.split(OLD_LIST)).toHaveLength(2)
    expect(next.split(NEW_LIST)).toHaveLength(2)
    expect(next).not.toContain(OLD_LIST)
  })

  it('the vocabulary is an explicit list of exactly four tiers and nothing else is widened', () => {
    const next = extractDetectorSql(migration)
    const listed = /verification_pass_status NOT IN \(([^)]*)\)/.exec(next)![1]
    expect([...listed.matchAll(/'([a-z_]+)'/g)].map((m) => m[1])).toEqual([
      'two_pass_verified', 'floored', 'single', 'computed_extension',
    ])
    for (const refused of ['single_pass', 'classical_match', 'divergent_flagged', 'documented_approximation',
      'not_defined_for_nodes', 'pending_w3_verification']) {
      expect(listed).not.toContain(refused)
    }
    expect(next).toMatch(/-- \(b\) special_lagna's sign_lord/)
    expect(next).toMatch(/-- \(c\) bhava_arudha's classical Parashari 2-exception rule/)
  })

  it('keeps the 18 explicit categories and the esoteric_point_% / tajik_% / bhava_arudha scope', () => {
    const next = extractDetectorSql(migration)
    for (const cat of ['upagraha_position', 'saturn_derived_point', 'saham_position', 'karaka_chara_position',
      'karakamsa_position', 'swamsa_position', 'arudha_pada', 'midpoint', 'aprakasha_position',
      'lal_kitab_special_point', 'maharsi_specific_point', 'bhrigu_nadi_point', 'sensitive_point_gulika_mandi',
      'sun_derived_upagraha', 'special_lagna', 'nakshatra_pada_sensitive', 'kp_ruling_planets_natal',
      'kp_cuspal_significators']) {
      expect(next).toContain(`'${cat}'`)
    }
    expect(next).toContain("fact_category LIKE 'esoteric_point_%'")
    expect(next).toContain("fact_category LIKE 'tajik_%'")
    expect(next).toContain("fact_category = 'bhava_arudha'")
  })
})
