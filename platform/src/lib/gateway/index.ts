/**
 * Gateway — unit 3.gateway_pipeline_isolation public surface.
 *
 * The single chokepoint between every caller (portal pipeline, MCP server,
 * future agents) and the unified tool contract. Hosts:
 *   • search_tools(query|family|role)  — discoverability
 *   • invoke_tool(name, params, ctx)   — authz + B.11 floor + dispatch
 */

export { searchTools } from './search_tools'
export { invokeTool } from './invoke_tool'
export { B11_FLOOR_TOOL_NAMES, isFloorTool } from './b11_floor'
export {
  registerExecutor,
  getExecutor,
  hasExecutor,
  listRegisteredExecutors,
  __resetRegistryForTests,
} from './executor_registry'
export type {
  ToolSearchQuery,
  ToolSearchResult,
  InvokeContext,
  InvokeRequest,
  InvokeResult,
  InvokeErrorCode,
  ToolExecutor,
} from './types'
export { GatewayError } from './types'
