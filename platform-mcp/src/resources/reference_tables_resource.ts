/**
 * reference_tables_resource.ts — MCP resource: marsys://reference-tables
 *
 * brahmagyan.reference asset MCP resource. Auto-loaded at session attach.
 * Exposes a concise catalogue of all 10 reference_* tables: row counts,
 * key range, and the classical text authorities each table is grounded in.
 *
 * This is metadata-only — no row data. Use the reference_lookup tool to
 * fetch specific rows. The resource lets the host LLM know which tables
 * exist and which classical texts back them, without a tool round-trip.
 *
 * URI: marsys://reference-tables
 * MimeType: text/markdown
 * Layer: L0 Brahmagyan (brahmagyan.reference)
 * Surgical: true — no LLM, no synthesis, static content.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js'

const REFERENCE_TABLES_CONTENT = `# Brahmagyan Reference Tables — Classical Lookup Catalogue

Layer: L0 Brahmagyan (brahmagyan.reference)
Tool: reference_lookup(table, key) — direct DB read, no LLM, no synthesis.

## Available tables

| table | rows | key column | key range | authority |
|---|---|---|---|---|
| nakshatra_attrs | 27 | nakshatra_id | 1–27 | BS §2; MC §3; Parasara Hora Shastra |
| tithi_attrs | 30 | tithi_id | 1–30 | MC §1; BS §2 |
| yoga_attrs | 27 | yoga_id | 1–27 | MC §4; BS §2 |
| karana_attrs | 11 | karana_id | 1–11 | MC §2; BS §2 |
| vara_attrs | 7 | vara_id | 1–7 | VS; MC §1; DP |
| sign_attrs | 12 | sign_id | 1–12 | BS §1; Parasara Hora Shastra |
| hora_cycle | 7 | vara_id | 1–7 | VS; Hora Sara (Prithuyashas) |
| combustion_orbs | 8 | planet (string) | — | MC §6; Phaladeepika §4; DP |
| event_quality | ≥18 | event_type + factor_type + factor_id | — | MC 3.2–8.1; BS; DP |
| inauspicious_periods | 7 | vara_id | 1–7 | DP published tables |

## Authority abbreviations

- **BS** — Brihat Samhita (Varahamihira)
- **MC** — Muhurta Chintamani (Rama Daivagna)
- **VS** — Vishnu Smriti (hora / vara authority)
- **DP** — Drik Panchang published tables
- **PHS** — Parasara Hora Shastra (Vimshottari Dasha chapter)
- **Phaladeepika** — Mantresvara, §4 (combustion orbs)
- **Hora Sara** — Prithuyashas (Chaldean hora cycle)

## Tool usage

\`\`\`
reference_lookup({ table: "nakshatra_attrs", key: 25 })
  → nakshatra_id=25: Purva Bhadrapada, lord=Jupiter, deity=Aja Ekapad
  → FORENSIC: native Moon nakshatra (1984-02-05 Bhubaneswar)

reference_lookup({ table: "vara_attrs", key: 1 })
  → vara_id=1: Ravivara (Sunday), lord=Sun
  → FORENSIC: native birth weekday (1984-02-05 = Sunday)

reference_lookup({ table: "combustion_orbs", planet: "Saturn" })
reference_lookup({ table: "event_quality", event_type: "vivah", factor_type: "tithi" })
reference_lookup({ table: "nakshatra_attrs" })  ← all 27 rows
\`\`\`

Every row carries source_citation (non-null, classical text with section reference).
provenance_envelope is included in every tool response.
`.trim()

export function registerReferenceTablesResource(server: McpServer): void {
  server.resource(
    'reference-tables',
    new ResourceTemplate('marsys://reference-tables', { list: undefined }),
    async (_uri) => ({
      contents: [
        {
          uri: 'marsys://reference-tables',
          mimeType: 'text/markdown',
          text: REFERENCE_TABLES_CONTENT,
        },
      ],
    })
  )
}
