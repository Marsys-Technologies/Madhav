import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const sql = readFileSync(join(process.cwd(), 'migrations/630_nirmana_evidence_server_writer_guard.sql'), 'utf8')

describe('migration 630: Nirmana server-reconstructed evidence writer guard', () => {
  it('rejects direct server-reconstructed inserts unless the transaction assumes the dedicated ingress role', () => {
    expect(sql).toContain("NEW.source_kind = 'server_reconstructed'")
    expect(sql).toContain('CREATE ROLE nirmana_evidence_ingress NOLOGIN NOINHERIT')
    expect(sql).toContain("current_user <> 'nirmana_evidence_ingress'")
    expect(sql).toContain('GRANT nirmana_evidence_ingress TO')
    expect(sql).toContain('BEFORE INSERT ON nirmana_elevation_campaign_events')
    expect(sql).toContain('validated evidence ingress')
  })
})
