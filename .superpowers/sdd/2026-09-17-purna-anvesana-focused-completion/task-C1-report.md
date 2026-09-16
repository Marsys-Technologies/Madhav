# Task C1 report — raw inquiry internal registry eligibility

## Delivered

- Added `platform/src/lib/vidhi/inquiry/execution_policy.ts`, which separates the inquiry presentation transport (`portal`, `managed_mcp`, `raw_mcp`) from server dispatch eligibility.
- The raw transport can compile a reviewed executable `registry_capability` whose existing dispatch eligibility includes `platform_internal`; this is explicitly server-side authority, not public MCP tool publication.
- Registry identity must be exact (`registry:${capability_uri}`); executable `mcp_native` aliases remain ineligible and cannot substitute for a registry handler.
- The compiler still checks exact overlay binding availability after policy selection, preserves existing required-argument resolution, and leaves blocked plan items as named dependencies rather than fabricating inputs.
- Added a committed-snapshot/frozen-corpus regression with a four-binding overlay. It grants only the exact dashas, divisionals, current-transit, and chart-gestalt registry bindings, while unrelated plan items stay dark.
- Updated the existing compiler channel assertion: raw inquiry now plans the internal divisional registry binding rather than rejecting it merely because it is not public MCP.

## Boundary retained by scope

`platform/src/app/api/mcp/inquiry/route.ts` already obtains registry handlers through `getToolByName(uri)`, whose URI path resolves and invokes a capability handler. Its execute branch nevertheless independently requires `binding.execution_channels.includes('mcp_full')`. C1 was explicitly prohibited from changing raw HTTP dispatch, so a platform-internal-only binding can now be compiler-ready but will still be rejected at that execution guard. No route, lifecycle, registration, handler, overlay-loader, generated snapshot, or public MCP surface was changed. A later explicitly authorized dispatcher integration must reuse `isInquiryServerDispatchEligible` (or an equivalent shared policy) at the route guard before such a compiled action can execute end-to-end.

## Verification

Passed:

- `npm test -- src/lib/vidhi/inquiry/raw_registry_binding_policy.test.ts src/lib/vidhi/inquiry/compiler.test.ts src/lib/vidhi/inquiry/door_parity.test.ts` — 33 tests passed.
- `npx tsc --noEmit` — passed.
- `npm test -- src/app/api/mcp/inquiry/__tests__/route.test.ts` — passed (32 tests).

Known pre-existing acceptance mismatch, not changed by C1:

- `src/lib/vidhi/inquiry/beyond_acarya_acceptance.test.ts` has two failing hash-pinning assertions. The current committed snapshot produces capability hash `sha256:85c02fe49904b7fd846839b246fe837a192d798e38d8f85e6f41de8245df8dd0` and report hash `sha256:1bc20aeb57d8e3e51c2dd00d7ae9838b1f46ed21930642493b89aa7c2eaa0503`; the governed acceptance artifact/test expect `sha256:55e17219c3e537a442cf02777d501a28874dd27c2e67a55422c0af47424f85a7` and `sha256:df21accf7b9c1ee72ef08ee05b07db4c36ae559e2019d5a175bfa842a536d30f`. C1 neither regenerated the snapshot nor altered the governed artifact, per scope.
