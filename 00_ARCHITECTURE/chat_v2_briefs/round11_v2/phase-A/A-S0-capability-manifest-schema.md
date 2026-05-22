---
canonical_id: R11A_A_S0
session_id: A-S0
title: Capability manifest schema + runtime validator
phase: R11.A — Foundation
depends_on: []
flag: FLAGLESS
client_side: "no — type definitions + runtime validator"
authored: 2026-05-22
---

# A-S0 — Capability Manifest Schema

## Context

The R11 v2 adapter substrate begins here. This session defines the **`ProviderCapabilities` TypeScript interface** — the structured manifest each of the 5 provider adapters declares at module load. The dispatcher (A-S7) and UI availability surface (A-S8) read this manifest to decide which capabilities are reachable on the active stack and which UI affordances to expose.

The manifest shape derives from `CAPABILITY_MATRIX.md §9`. This session is the canonical TypeScript codification of that matrix.

## Files in Scope

### Add

- `platform/src/lib/providers/capabilities.ts` — `ProviderCapabilities` interface (TypeScript). Fields per §9 of CAPABILITY_MATRIX. Each field is a string-union of supported variants (e.g., `extendedThinking: 'native_effort' | 'native_budget' | 'inline_blocks' | 'polyfill_cot' | null`) plus a few booleans.
- `platform/src/lib/providers/manifest-validator.ts` — runtime validator that asserts a provider's declared manifest conforms to the interface. Throws on validation failure at module load.
- `platform/tests/providers/capabilities.test.ts` — unit tests asserting interface shape + validator behavior (valid manifest passes; malformed manifest throws).

### Modify

- `platform/src/lib/config/feature_flags.ts` — placeholder registrations for the three new R11 v2 flags (`MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY`, `MARSYS_FLAG_R11V2_USE_ADAPTERS`, `MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY`). All three default to safe values (master = false, adapters/telemetry = true after subsequent sessions verify).

## Files MUST NOT Touch

- Any provider-specific code yet (A-S2..A-S6 own that)
- Existing model registry (`lib/models/registry.ts`)
- Phase 4C files

## Acceptance Criteria

1. `platform/src/lib/providers/capabilities.ts` exports `ProviderCapabilities` interface with all fields from CAPABILITY_MATRIX §9.
2. The interface is strictly typed — no `any`; every field is a string-union or boolean or numeric.
3. `manifest-validator.ts` exports `validateManifest(m: unknown): asserts m is ProviderCapabilities` — runtime assertion function.
4. Tests pass: valid manifest validates; manifests with missing fields, wrong types, or unknown values throw.
5. Three new flags registered in `feature_flags.ts` with safe defaults.
6. No regression: existing tests in `platform/tests/` still pass.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/providers/capabilities.ts && echo "PASS: capabilities.ts exists"
test -f src/lib/providers/manifest-validator.ts && echo "PASS: validator exists"
grep -n "MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY" src/lib/config/feature_flags.ts && echo "PASS: flag registered"
npx jest --testPathPattern="capabilities|manifest-validator|A-S0" --passWithNoTests
```

## Commit Template

```
feat(providers): capability manifest schema + runtime validator (A-S0)

ProviderCapabilities TypeScript interface codified from CAPABILITY_MATRIX §9.
Runtime validator throws on malformed manifests at module load. Three R11 v2
flags registered in feature_flags.ts with safe defaults. Foundation for
A-S1 adapter interface and A-S2..A-S6 per-provider adapter skeletons.

Flagless per §M.16 (type definitions + validator only).
```

## Decision Log

*(Executor: paste the final `ProviderCapabilities` interface shape; document any field-name diversions from CAPABILITY_MATRIX §9.)*
