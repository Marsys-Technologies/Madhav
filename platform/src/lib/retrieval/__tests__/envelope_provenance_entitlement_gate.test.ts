/**
 * envelope_provenance_entitlement_gate.test.ts — finding: "provenance.tables / source_table
 * expose raw internal schema names regardless of entitlement" (judgment_query v3 envelope).
 *
 * Before this fix, any `provenance` block already present in a capability's `content`
 * (e.g. query_ucd.ts's `provenance: { tables: ['vw_chart_digest', 'bodha_msr_signals',
 * 'bodha_convergence'] }`, embedded into judgment_query's response as `orientation_context`)
 * rode through `buildRetrievalEnvelope` unconditionally — an ordinary end-user-facing call
 * received raw internal DB table names with no entitlement check at all.
 *
 * `redactProvenanceTables` + `buildRetrievalEnvelope`'s new `entitled` param close this:
 * passing `entitled: false` strips `tables`/`source_table` off every `provenance` block in
 * `content` (recursively), leaving every other provenance field untouched, while omitting
 * `entitled` (the default) keeps every existing call site byte-identical.
 */
import { describe, it, expect } from 'vitest'
import { buildRetrievalEnvelope, redactProvenanceTables } from '@/lib/retrieval/envelope'

describe('redactProvenanceTables', () => {
  it('entitled=true is a no-op and returns the SAME reference (cheap default path)', () => {
    const content = { provenance: { tables: ['chart_facts'], source: 'note' } }
    expect(redactProvenanceTables(content, true)).toBe(content)
  })

  it('entitled=false strips tables/source_table but keeps every other provenance field', () => {
    const content = {
      provenance: {
        tables: ['vw_chart_digest', 'bodha_msr_signals', 'bodha_convergence'],
        ranking_note: 'E-6 ranking pipeline note',
      },
    }
    const gated = redactProvenanceTables(content, false) as typeof content
    expect(gated.provenance).not.toHaveProperty('tables')
    expect(gated.provenance.ranking_note).toBe('E-6 ranking pipeline note')
    expect((gated.provenance as Record<string, unknown>)['schema_detail_gated']).toBe(true)
  })

  it('entitled=false strips a bare source_table field too', () => {
    const content = { provenance: { source_table: 'chart_divisionals', asset_id: 'ga_vichara' } }
    const gated = redactProvenanceTables(content, false) as typeof content
    expect(gated.provenance).not.toHaveProperty('source_table')
    expect(gated.provenance.asset_id).toBe('ga_vichara')
  })

  it('recurses into nested content (e.g. an embedded orientation_context-shaped object)', () => {
    const content = {
      chart_id: 'x',
      orientation_context: {
        content: { digest: {}, provenance: { tables: ['bodha_msr_signals'] } },
      },
    }
    const gated = redactProvenanceTables(content, false) as typeof content
    expect(gated.orientation_context.content.provenance).not.toHaveProperty('tables')
  })

  it('a content tree with no provenance block returns the SAME reference (no spurious copy)', () => {
    const content = { checklist: { bearing_yogas: [1, 2, 3] } }
    expect(redactProvenanceTables(content, false)).toBe(content)
  })

  it('does not touch a provenance-shaped block that carries neither tables nor source_table', () => {
    const content = { provenance: { source: 'panchang.py Swiss-Ephemeris' } }
    const gated = redactProvenanceTables(content, false) as typeof content
    expect(gated).toBe(content)
  })
})

describe('buildRetrievalEnvelope entitlement gate (params.entitled)', () => {
  const content = { provenance: { tables: ['chart_facts'], note: 'kept' } }

  it('omitting entitled preserves today\'s byte-identical content (additive-only, no silent break)', () => {
    const env = buildRetrievalEnvelope({ tool: 't', content }, 'legacy')
    expect(env.content).toBe(content)
  })

  it('entitled: true behaves identically to omitting it', () => {
    const env = buildRetrievalEnvelope({ tool: 't', content, entitled: true }, 'legacy')
    expect(env.content).toBe(content)
  })

  it('entitled: false strips provenance.tables from content on the legacy wire shape', () => {
    const env = buildRetrievalEnvelope({ tool: 't', content, entitled: false }, 'legacy')
    const gatedContent = env.content as typeof content
    expect(gatedContent.provenance).not.toHaveProperty('tables')
    expect(gatedContent.provenance.note).toBe('kept')
  })

  it('entitled: false also gates the v3 wire shape (the bug was not v3-only)', () => {
    const env = buildRetrievalEnvelope({ tool: 't', content, entitled: false }, 'v3')
    const gatedContent = env.content as typeof content
    expect(gatedContent.provenance).not.toHaveProperty('tables')
  })
})
