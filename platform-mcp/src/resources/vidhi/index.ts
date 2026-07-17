/**
 * Vidhi module — VENDORED MIRROR for the MCP delivery layer (D-2 Lane V-2).
 *
 * V-1 authored the canonical vidhi registry + compiler at `platform/src/lib/vidhi/`.
 * Because `platform-mcp/` is a separate TS package with `rootDir: src` + NodeNext
 * resolution, it cannot relative-import that module without breaking the MCP build
 * (the same constraint documented in `platform-mcp/src/contract_bridge.ts` and the
 * `src/generated/` codegen mirrors). This directory is therefore a 1:1 content mirror
 * of `platform/src/lib/vidhi/{types,cr_status,registry_data,compiler}.ts` — the ONLY
 * edit applied on copy is adding NodeNext-required `.js` import extensions.
 *
 * DRIFT GUARD: `src/__tests__/vidhi_registry_parity.test.ts` imports BOTH this mirror
 * and the platform canonical module and asserts the exported `VIDHI_PRIMITIVES` /
 * `VIDHI_INTENT_FLOORS` are deep-equal and the compilers produce byte-identical
 * contracts. A drift between the two fails that test loudly — this is what makes the
 * MCP-served rows provably "match V-1's registry" (BIND_D-2.md §F1.7 ledger row 14),
 * per the source-of-truth note in V-1's own registry_data.ts header.
 */
export * from './types.js';
export * from './registry_data.js';
export * from './compiler.js';
export * from './cr_status.js';
