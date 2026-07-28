/**
 * Paripraśna durable conversation summaries — PB-2 (SMṚTI) lane M-3 public API.
 *
 *   Types (isomorphic):        types.ts
 *   Threshold decision (pure,
 *     isomorphic):             threshold.ts
 *   Context assembly (pure,
 *     isomorphic):             assemble.ts
 *
 *   Rendering (server-only —
 *     reads the registry):     render.ts     -> import directly, not re-exported
 *   Orchestration (server-only
 *     transitively, via
 *     render.ts):               service.ts    -> import directly, not re-exported
 *   Postgres store
 *     (server-only):           store.ts       -> import directly, not re-exported
 *   LLM worker
 *     (server-only):           worker.ts      -> import directly, not re-exported
 *   Route splice
 *     (server-only):           splice.ts      -> import directly, not re-exported
 *
 * Same discipline as M-1's `store/index.ts`: server-only modules (anything
 * pulling in `pg`, the retrieval registry, or the LLM adapter stack) are left
 * out of this barrel so importing it never drags server-only code into a
 * client bundle.
 */
export * from './types'
export * from './threshold'
export * from './assemble'
