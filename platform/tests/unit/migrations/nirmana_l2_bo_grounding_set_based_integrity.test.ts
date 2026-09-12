import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const sql = readFileSync(
  join(process.cwd(), 'migrations/1032_nirmana_l2_bo_grounding_set_based_integrity.sql'),
  'utf8',
)
const detector = sql.split('$ICHECK$')[1]

describe('migration 1032: bo_grounding set-based integrity detector', () => {
  it('materializes grounding and source identities once instead of running correlated counts', () => {
    expect(sql).toContain('grounding_identities AS MATERIALIZED')
    expect(sql).toContain('source_identities AS MATERIALIZED')
    expect(sql).toContain('count(*) AS match_count')
    expect(sql).toContain('true AS requires_grounding')
    expect(sql).toContain('f.fired AS requires_grounding')
    expect(detector.match(/\bEXCEPT\b/g)).toHaveLength(2)
    expect(detector).not.toMatch(/SELECT count\(\*\) FROM bodha_grounding_matches g/)
    expect(detector).not.toMatch(/WHERE s\.signal_id::text = g\.target_id/)
    expect(detector).not.toMatch(/LEFT JOIN/)
  })

  it('preserves all five original integrity invariants', () => {
    expect(sql).toContain("grounding_tier NOT IN ('sruti','yukti','pratyaksa')")
    expect(sql).toContain("grounding_tier = 'sruti'")
    expect(sql).toContain('matched_rule_id IS NULL')
    expect(sql).toContain("'msr_signal'::text AS target_kind")
    expect(sql).toContain("'yoga_dosha_firing'::text AS target_kind")
    expect(sql).toContain('WHERE requires_grounding')
    expect(sql).toContain('WHERE match_count = 1')
    expect(sql).not.toContain('WHERE f.fired')
  })

  it('changes only the bo_grounding detector and leaves its timeout untouched', () => {
    expect(sql).toMatch(/UPDATE asset_registry[\s\S]*WHERE asset_id = 'bo_grounding'/)
    expect(sql).not.toMatch(/writer_timeout_seconds\s*=/)
    expect(sql).toContain('EXECUTE new_sql INTO detector_ok')
    expect(sql).toContain('detector_ok IS DISTINCT FROM true')
  })

  it('fails closed on registry drift while permitting idempotent replay', () => {
    expect(sql).toContain('266ed3d30f63f601f1f5a8f515da147e272d0fcd7f9afe52f8861925d2b2800e')
    expect(sql).toContain("encode(sha256(convert_to(new_sql, 'UTF8')), 'hex')")
    expect(sql).toContain('refusing to overwrite unexpected bo_grounding detector fingerprint')
    expect(sql).toContain('GET DIAGNOSTICS updated_count = ROW_COUNT')
  })
})
