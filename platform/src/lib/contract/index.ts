/**
 * Unified Tool Contract — public entry point (Unit 2b, sets G3_contract).
 *
 * Re-exports for both portal and MCP channels. The contract is the single
 * source of truth for canonical_name, input_schema (Zod), description,
 * annotations, role, family, data_dependency, ayanamsha_role, ayanamsha_id.
 */

export type {
  ToolContract,
  ToolRole,
  ToolFamily,
  DataDependency,
  AyanamshaRole,
  ToolAnnotations,
} from './types'
export { DEFAULT_AYANAMSHA_BY_ROLE } from './types'
export { defineTool } from './defineTool'
export { zodToJsonSchema } from './json_schema'
export type { JsonSchemaObject } from './json_schema'
export {
  TOOL_CONTRACTS,
  getContract,
  getContractNames,
} from './registry'
export {
  checkContractInvariants,
  assertContractInvariants,
  type InvariantViolation,
} from './invariants'
export {
  CONTRACT_CATALOG,
  CONTRACT_CATALOG_BY_NAME,
  CONTRACT_TOOL_NAMES,
  type ContractCatalogEntry,
} from './catalog'
export {
  TOOL_METADATA,
  TOOL_METADATA_BY_NAME,
  TOOL_METADATA_NAMES,
  EXPECTED_ASSETS,
  getToolMetadata,
  auditToolAssetReconciliation,
  isReconciliationGreen,
  type ToolReconciliationEntry,
  type ToolSurface,
  type ToolIntent,
  type LiveAssetId,
  type CoverageReport,
} from './tool_metadata'
