import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const sql = readFileSync(join(process.cwd(), 'migrations/632_nirmana_evidence_server_writer_guard.sql'), 'utf8')

describe('migration 632: Nirmana server-reconstructed evidence writer guard', () => {
  it('rejects direct shared-principal inserts and provisions only a distinct ingress login boundary', () => {
    expect(sql).toContain("NEW.source_kind = 'server_reconstructed'")
    expect(sql).toContain('CREATE ROLE nirmana_evidence_ingress_writer LOGIN NOINHERIT')
    expect(sql).toContain("session_user <> 'nirmana_evidence_ingress_writer'")
    expect(sql).toContain("current_user <> 'nirmana_evidence_ingress_writer'")
    expect(sql).toContain('GRANT INSERT ON TABLE')
    expect(sql).not.toContain('PASSWORD')
    expect(sql).toContain('BEFORE INSERT ON nirmana_elevation_campaign_events')
    expect(sql).toContain('dedicated evidence ingress login')
  })
})
