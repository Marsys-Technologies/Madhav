/**
 * sensitive_capability_class.ts — the disclosure-sensitive capability class,
 * mirrored across the platform/platform-mcp process boundary (P1 lane G1-A).
 * ==============================================================================
 * PARIPRASHNA_ARCHITECTURE §2, the doors table, on the raw-MCP plane:
 * "**NONE — this is the retrieval/research plane.** … **Sensitive-class
 * capabilities MUST be excluded from the `consult` profile.**"
 * SAFETY_PRIVACY_TENANCY §3: "On raw MCP tools, where no prose crosses our
 * boundary, enforcement is capability-level: sensitive-class tools carry
 * disclosure-class requirements in the registry and are excluded from
 * `consult`-profile projections entirely." Abuse case A6 is the threat:
 * "Sensitive-class extraction from raw MCP tools (ayurdaya etc.)".
 *
 * ── WHY THIS FILE IS A MIRROR AND NOT AN IMPORT ───────────────────────────────
 * platform-mcp is a separate NodeNext ESM package with no import path back into
 * `platform/` — the same constraint `mcp_surface_profiles.generated.ts`,
 * `envelope.ts` and `registry_shims.ts` in this package all document. The
 * canonical list lives at
 * `platform/src/lib/pariprashna/safety/sensitive_capabilities.ts`; this is its
 * mirror, and `sensitive_capability_parity.test.ts` on the platform side READS
 * THIS FILE and asserts the two are identical. The mirror is therefore a
 * detector, not a promise (§N.8) — a drifting copy fails a test rather than
 * quietly widening the consult surface.
 *
 * ── WHY THE RUNTIME GATE AND NOT ONLY THE BUILDER ─────────────────────────────
 * The builder-side exclusion (platform/scripts/manifest/mcp_surface_profile_builder.ts)
 * keeps a sensitive tool out of a REGENERATED profile. But
 * `mcp_surface_profiles.generated.ts` is a checked-in artifact that is only
 * regenerated deliberately, so a builder-only fix would leave the currently
 * shipped profile unchanged and the claim would rest on a file nobody
 * re-ran. `subtractSensitiveClass()` is applied at request time, over whatever
 * the generated manifest happens to say, so the exclusion holds even against a
 * stale artifact.
 */

/** Mortality-domain capabilities (longevity computation). */
export const MORTALITY_CLASS_CAPABILITIES: readonly string[] = [
  'get_ayurdaya',
  'ganita_ayurdaya_get',
] as const

/** Health/medical capabilities. */
export const MEDICAL_CLASS_CAPABILITIES: readonly string[] = [
  'assess_health',
  'get_medical_indications',
  'ganita_medical_get',
  'query_medical_mappings',
  'query_nakshatra_medical',
  'query_sign_medical',
  'ref_sign_medical_get',
] as const

/** The union, sorted — the class the architecture's §2 door table names. */
export const SENSITIVE_CLASS_CAPABILITIES: readonly string[] = [
  ...MORTALITY_CLASS_CAPABILITIES,
  ...MEDICAL_CLASS_CAPABILITIES,
].sort()

export function isSensitiveClassCapability(toolName: string): boolean {
  return SENSITIVE_CLASS_CAPABILITIES.includes(toolName)
}

/**
 * Remove every sensitive-class tool name from a profile allowlist.
 *
 * Applied to `consult` ONLY. `full` and `compact` are scope-gated surfaces for
 * callers who explicitly asked for the wider projection; `consult` is the
 * SAFE-DEFAULT profile a plain guest gets without asking for anything, which is
 * precisely the population the exclusion is for.
 */
export function subtractSensitiveClass(allowed: Set<string>): {
  allowed: Set<string>
  removed: string[]
} {
  const removed: string[] = []
  for (const name of SENSITIVE_CLASS_CAPABILITIES) {
    if (allowed.delete(name)) removed.push(name)
  }
  return { allowed, removed }
}
