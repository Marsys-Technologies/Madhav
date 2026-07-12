/**
 * resources/index.ts — MCP resource registration for MARSYS-JIS.
 *
 * Registers 5 MCP resources that Claude auto-loads at session attach (arch §4):
 *   - marsys://chart-snapshot    (~2.5k tokens, structured L1 facts, NEW in v3.1)
 *   - marsys://chart-overview    (~3k tokens, synthesis themes from L2.5)
 *   - marsys://house-rules       (universal operating manual)
 *   - marsys://capabilities      (tool + data coverage snapshot; S3=placeholder, S4=live)
 *   - marsys://school-conventions (~2.5k tokens, 4-school reference, static)
 *
 * MCPT v3.1.0-S3 (rewrites chart-overview + house-rules; adds 3 new resources)
 *
 * Prior: v1 registered chart-overview + house-rules as static markdown files
 * (2 resources). v3.1 registers 5 resources with dynamic generation; D0.5 removed tier conditioning.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { registerChartSnapshot } from './chart_snapshot.js'
import { registerChartOverview } from './chart_overview.js'
import { registerHouseRules } from './house_rules.js'
import { registerCapabilities } from './capabilities.js'
import { registerSchoolConventions } from './school_conventions.js'
import { registerChartBundleResource } from './chart_bundle_resource.js'
import { registerMultiAyanamshaResource } from './multi_ayanamsha_resource.js'
import { registerClassicalTextsResource } from './classical_texts_resource.js'
import { registerSutravaliResources } from './sutravali_resource.js'
import { registerChartCatalogResource } from './chart_catalog_resource.js'
import { registerConsumptionProtocol } from './consumption_protocol.js'

/**
 * Register all 5 MARSYS-JIS MCP resources on the given server.
 *
 * Call once per McpServer instance, alongside tool registrations, before
 * connecting the transport.
 *
 * @param server  The McpServer instance to register resources on.
 */
export function registerResources(server: McpServer, principal: Principal): void {
  // 1. chart-snapshot: structured L1 facts (~2.5k tokens, NEW in v3.1)
  //    Generated at attach time from chart_facts + dasha + panchang.
  //    M0: parametrized with {chart_id} + gated via remoteAuthorize.
  registerChartSnapshot(server, principal)

  // 2. chart-overview: L2.5 synthesis themes (~3k tokens for admin/acharya, ~800 for client)
  //    Top 5 MSR themes + top 2 CDLM contradictions + CGM anchor + LEL life-phase.
  //    Falls back to static markdown if dynamic generation fails.
  registerChartOverview(server)

  // 3. house-rules: universal operating manual
  //    Loaded from house_rules_variants/universal.md at server start.
  //    Single variant — no tier conditioning (D0.5 excision 2026-06-28).
  registerHouseRules(server)

  // 4. capabilities: tool + data coverage snapshot
  //    S3: PLACEHOLDER with hardcoded tool descriptions + "perf data pending S4" note.
  //    S4: replaces with live tool_health() + data_coverage() calls.
  registerCapabilities(server)

  // 5. school-conventions: 4-school static reference (~2.5k tokens)
  //    Uniform across all tiers. Covers Parashara/Jaimini/KP/Tajaka authoritative scope,
  //    output forms, known disagreements, and tool routing by school.
  registerSchoolConventions(server)

  // 6. chart-bundle: Layer-1 bundle per chart (planet positions, house cusps, dasha, yogas)
  //    Dynamic resource template marsys://chart-bundle/{chart_id}.
  //    INF11-S1 [BUILD-ORCH-J-03]
  registerChartBundleResource(server)

  // 7. multi-ayanamsha: cross-ayanamsha build status + guidance per chart.
  //    Dynamic resource template marsys://multi-ayanamsha/{chart_id}.
  //    INF11-S1 [BUILD-ORCH-J-03]
  registerMultiAyanamshaResource(server)

  // 8. classical-texts: verse-addressable corpus metadata per text_key
  //    Dynamic resource template marsys://classical-texts/{text_key}.
  //    brahmagyan.texts delta build 2026-06-03
  registerClassicalTextsResource(server)

  // 9. sutravali rules by planet + by house
  //    Dynamic resource templates:
  //      marsys://resource/sutravali/all-by-planet/{planet}
  //      marsys://resource/sutravali/all-by-house/{n}
  //    BRAHMA L0 Stream D (2026-06-07)
  registerSutravaliResources(server)

  // 10. chart catalog: entitled chart list + per-chart metadata resource
  //     marsys://chart/{chart_id} — list returns only the caller's entitled charts;
  //     read handler is M0-gated (remoteAuthorize). M2 chart selection (2026-07-01).
  registerChartCatalogResource(server, principal)

  // 11. consumption-protocol: the E3 demand-side chase protocol (WP-1.6 / P-12).
  //     Static teaching surface (no chart data) that makes the demand-side posture
  //     operative from W1 deploy — pairs with the capability map + acquisition tracker.
  //     marsys://consumption-protocol
  registerConsumptionProtocol(server)
}
