import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const sql = readFileSync(join(process.cwd(), 'migrations/627_nirmana_elevation_asset_labels.sql'), 'utf8')

describe('migration 627: Nirmana elevation asset labels', () => {
  it('creates a definition-scoped append-only label catalogue', () => {
    expect(sql).toContain('CREATE TABLE IF NOT EXISTS nirmana_elevation_asset_labels')
    expect(sql).toContain('PRIMARY KEY (campaign_id, definition_revision, catalogue_revision, asset_id)')
    expect(sql).toContain('REFERENCES nirmana_elevation_campaign_definitions')
    expect(sql).toContain('CHECK (label_digest ~')
    expect(sql).toContain("jsonb_typeof(legacy_aliases) = 'array'")
    expect(sql).toContain('BEFORE UPDATE OR DELETE OR TRUNCATE ON nirmana_elevation_asset_labels')
    expect(sql).toContain('nirmana_elevation_asset_labels is append-only')
  })
})
