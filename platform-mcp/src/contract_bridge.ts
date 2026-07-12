/**
 * contract_bridge.ts — MCP-channel reader for the unified Tool Contract
 * (Unit 2b, sets G3_contract).
 *
 * The contract source of truth lives at platform/src/lib/contract/. Because
 * platform-mcp/ is a separate TS package with `rootDir: src`, we cannot
 * relative-import the contract module directly without breaking the MCP
 * build. Instead, this bridge advertises the SAME canonical_name set the
 * contract registry exports, and the cross-channel G3 test
 * (platform/src/lib/contract/__tests__/unified_contract.test.ts) asserts
 * the lists are equal — making this file a verified mirror.
 *
 * UPDATING THIS FILE: when a contract is added/removed in
 * platform/src/lib/contract/registry.ts, mirror the change here. The G3
 * test will fail loudly until the lists match.
 */

/**
 * Mirror of CONTRACT_TOOL_NAMES from platform/src/lib/contract/registry.ts.
 * Order is the canonical order (matches catalog generation).
 */
export const MCP_CONTRACT_TOOL_NAMES: string[] = [
  // Pre-existing contracts (Unit 2b)
  'query_chart_facts',
  'query_panchanga',
  'query_dasha_periods',
  'query_divisional_chart',
  // WP-1.3(h)/LCA-12 §7.3: query_kp_ruling_planets + kp_query PHANTOM DROPPED — no KP engine
  // backs them (migration 024_kp_sublords archived; no registry capability; removed from the
  // MCP surgical whitelist by WP-1.7). The MCP contract surface must not advertise a tool that
  // cannot resolve. Re-add only when a real KP engine is built + registered.
  'query_ephemeris',
  // L0FR Stream C — classical text corpus (2026-06-07)
  'read_classical_text',
  'read_chapter',
  'list_classical_texts',
  'find_verses_about',
  'search_classical_texts',
]

/**
 * Helper for MCP server registration — returns the names list the MCP server
 * SHOULD register from. (Wave-3 will collapse the legacy registration paths
 * onto this; Unit 2b adds the surface without flipping the dispatch.)
 */
export function getMcpContractToolNames(): string[] {
  return [...MCP_CONTRACT_TOOL_NAMES]
}
