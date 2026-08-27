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
    expect(sql).toContain('Authoritative frozen-integrity detector read contract')
    expect(sql).toContain("'reference_planets'")
    expect(sql).toContain("'reference_aspects'")
    expect(sql).toContain("'reference_vargas'")
    expect(sql).toContain("'reference_glossary'")
    expect(sql).toContain("'classical_texts'")
    expect(sql).toContain("'classical_text_chunks'")
    expect(sql).toContain("'nirmana_bg_texts_integrity_baselines'")
    expect(sql).toContain("'vidhi_intent_floors'")
    expect(sql).toContain("'vidhi_floor_items'")
    expect(sql).toContain("'vidhi_primitives'")
    expect(sql).toContain("'bg_gochara_citation_resolution'")
    expect(sql).not.toContain('PASSWORD')
    expect(sql).toContain('BEFORE INSERT ON nirmana_elevation_campaign_events')
    expect(sql).toContain('dedicated evidence ingress login')
  })
})
