/**
 * MARSYS-JIS Retrieval tool registry — CLEAN SLATE STUB
 *
 * All tools removed as part of legacy-teardown (feature/legacy-teardown).
 * RETRIEVAL_TOOLS is empty. Rebuild per layer during the Layer-0 → Layer-3 arc.
 *
 * Types and CONTRACT_CATALOG re-exports are preserved so the serve shell
 * (route.ts, tool_catalogue.ts, agentic loop) compiles and boots tool-less.
 */

export * from './types'
import type { RetrievalTool } from './types'

export const RETRIEVAL_TOOLS: RetrievalTool[] = []

export function getTool(name: string): RetrievalTool | undefined {
  return RETRIEVAL_TOOLS.find(t => t.name === name)
}

// CONTRACT_CATALOG re-exports — registry is also empty after teardown.
export {
  CONTRACT_CATALOG,
  CONTRACT_CATALOG_BY_NAME,
  CONTRACT_TOOL_NAMES,
} from '../contract'
