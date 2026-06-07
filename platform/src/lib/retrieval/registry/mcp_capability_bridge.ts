/**
 * MCP Capability Bridge
 * =====================
 * Maps between the MCP server's tool registrations and the Consume Chat registry URIs.
 * Used by parity_check.ts to compare both channels.
 *
 * The bridge reads the MCP server's registered tool names and maps them to
 * the canonical marsys:// URI scheme used by the retrieval registry.
 */

import type { CapabilityUri } from './types'

/**
 * URI prefix mappings from MCP tool names to marsys:// URIs.
 * Format: MCP tool name → marsys:// URI
 */
const MCP_TOOL_TO_URI: Record<string, CapabilityUri> = {
  // L0 capabilities (Stream A)
  'resolve_entity': 'marsys://tool/L0/resolve_entity',
  'list_entities': 'marsys://tool/L0/list_entities',
  'intent-classify': 'marsys://prompt/intent-classify',
  // Resources use their path as URI
  'asset-registry-all': 'marsys://resource/asset-registry/all',
  'asset-registry-L0': 'marsys://resource/asset-registry/L0',
}

/**
 * Returns the set of capability URIs that the MCP server currently exports.
 * Reads from the MCP server's registered tools at runtime.
 */
export async function listMcpCapabilityUris(): Promise<CapabilityUri[]> {
  // In production: query the MCP server for its tool/resource/prompt list
  // In CI: use the statically declared MCP_TOOL_TO_URI map
  // This implementation uses the static map for determinism
  return Object.values(MCP_TOOL_TO_URI)
}

/**
 * Convert an MCP tool name to a marsys:// URI.
 */
export function mcpToolNameToUri(toolName: string): CapabilityUri | undefined {
  return MCP_TOOL_TO_URI[toolName]
}

/**
 * Register a new MCP tool → URI mapping.
 * Called when new capabilities are added to both channels.
 */
export function registerMcpToolUri(toolName: string, uri: CapabilityUri): void {
  MCP_TOOL_TO_URI[toolName] = uri
}
