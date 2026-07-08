/**
 * R5 W0b — Single-source contract codegen manifest.
 * ===================================================
 * Design mandate: RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md §19
 * ("SINGLE-SOURCE CONTRACT GENERATION" — the facet schema for each instrument
 * is declared ONCE, in the registry's CapabilityDescriptor; MCP-side Zod shims
 * are GENERATED from it, never hand-edited).
 *
 * STRANGLER DISCIPLINE (brief §6.2): instruments are added to this manifest
 * ONE AT A TIME, behind a parity gate (see src/__tests__/r5_codegen_parity.test.ts).
 * Adding an entry here is the act of "migrating" an instrument to the generated
 * path. The corresponding handwritten shim in src/tools/*.ts is NOT deleted —
 * that is a later-wave decision gated on its own green parity run in prod.
 *
 * Each entry points at the registry CapabilityDescriptor that is the single
 * source of truth for that instrument's facet schema (platform/src/lib/retrieval/
 * registry/layers/**). The codegen script (generate_from_registry.ts) parses
 * that descriptor's `input_schema` + `required_inputs` STATICALLY (TypeScript
 * AST only, no import/execution of the descriptor module — the descriptor
 * pulls in platform-only runtime deps like `@/lib/db/client` that platform-mcp,
 * a separate deployable process/package with its own node_modules, cannot and
 * must not resolve at build time; see design §19's "two-process contract seam"
 * finding this codegen exists to close).
 *
 * PILOT SELECTION (W0b, this wave): 3 low-risk, well-understood, already-verified
 * L1 Gaṇita "flat_fact / leaf" instruments from the P1 family the W0a punch-list
 * lane already touched (register_p1_ganita.ts) — simple single-facet handlers,
 * uniform {chart_id, ayanamsha_id, limit, offset} shape, no facet-dispatch
 * branching. Good proof-of-concept surface before harder cases (structural/
 * condition facet-dispatch tools, corpus hybrid search, graph traversal).
 */

export interface RegistryManifestEntry {
  /** The MCP-facing tool name this instrument is served as (matches the handwritten shim's name). */
  mcpToolName: string
  /**
   * Path to the registry CapabilityDescriptor source file, relative to this
   * manifest file (platform-mcp/scripts/). Crosses into the sibling `platform`
   * package's source tree — READ-ONLY, parsed as text, never executed or
   * imported at runtime by platform-mcp.
   */
  descriptorPath: string
  /** The exported const name of the CapabilityDescriptor object literal in that file. */
  exportName: string
  /** The capability URI (redundant with the descriptor's own `uri` field; used for a fast sanity check post-parse). */
  uri: string
  /** Human note: which handwritten shim file currently serves this tool (for parity-test wiring). */
  handwrittenShimFile: string
  handwrittenShimExportedRegisterFn: string
}

export const REGISTRY_MANIFEST: RegistryManifestEntry[] = [
  {
    mcpToolName: 'ganita_strength_get',
    descriptorPath: '../../platform/src/lib/retrieval/registry/layers/L1_ganita/get_strength.ts',
    exportName: 'getStrengthCapability',
    uri: 'marsys://tool/L1/get_strength',
    handwrittenShimFile: '../src/tools/register_p1_ganita.ts',
    handwrittenShimExportedRegisterFn: 'registerP1GanitaTools',
  },
  {
    mcpToolName: 'ganita_sade_sati_get',
    descriptorPath: '../../platform/src/lib/retrieval/registry/layers/L1_ganita/get_sade_sati.ts',
    exportName: 'getSadeSatiCapability',
    uri: 'marsys://tool/L1/get_sade_sati',
    handwrittenShimFile: '../src/tools/register_p1_ganita.ts',
    handwrittenShimExportedRegisterFn: 'registerP1GanitaTools',
  },
  {
    mcpToolName: 'ganita_tajaka_get',
    descriptorPath: '../../platform/src/lib/retrieval/registry/layers/L1_ganita/get_tajik.ts',
    exportName: 'getTajikCapability',
    uri: 'marsys://tool/L1/get_tajik',
    handwrittenShimFile: '../src/tools/register_p1_ganita.ts',
    handwrittenShimExportedRegisterFn: 'registerP1GanitaTools',
  },
]
