---
canonical_id: STREAM_R11A_COMPLETE
status: COMPLETE
authored: 2026-05-22
---

# R11.A — Foundation Phase Complete

## Session Close-State Summary

| Session | Status | Commit | Key Deliverable |
|---|---|---|---|
| A-S0 | PASS | 426b7c86 | ProviderCapabilities interface, manifest-validator, R11V2 flags |
| A-S1 | PASS | (batch) | CapabilityAdapter interface, types.ts, CapabilityUnsupportedError |
| A-S2 | PASS | (batch) | AnthropicAdapter + ANTHROPIC_MANIFEST |
| A-S3 | PASS | (batch) | GoogleAdapter + GOOGLE_MANIFEST |
| A-S4 | PASS | (batch) | OpenAIAdapter + OPENAI_MANIFEST |
| A-S5 | PASS | (batch) | DeepSeekAdapter + DEEPSEEK_MANIFEST |
| A-S6 | PASS | (batch) | NVIDIAAdapter + NVIDIA_MANIFEST |
| A-S7 | PASS | 3ce14582 | Capability dispatcher — registry, routing, switch-stack hints |
| A-S8 | PASS | 76878966 | CapabilityHint UI, useProviderManifest, manifest-helpers, CSS |
| A-S9 | PASS | 76878966 | capability_telemetry.ts, data-capability-path SSE part |
| A-S10 | PASS | ded3ce7c | MigrationAdapter — all 5 adapters delegate chat() |
| A-S11 | PASS | 465d2424 | useMultiProviderParity, MultiProviderParityToggle, deploy.yml |
| A-S12 | PASS | c491dd98 | Foundation E2E: 340 tests, 5/5 stacks PASS |

## Test Report

```
R11.A foundation: 5/5 stacks PASS, capability manifests valid,
telemetry firing, hide-and-hint working.

Total tests: 340 across 16 test files
adapter-contract: 75/75 PASS (5 stacks × 15 assertions)
manifest-validation: 30/30 PASS (spot-checks + validateManifest on all 5)
foundation-smoke: 20/20 PASS (5 stacks × chat round-trip + report)
CapabilityHint.integration: 14/14 PASS (webSearch/thinking/computerUse/audio)
capability_telemetry.integration: 14/14 PASS (per-stack records + drain + SSE)
```

## Amendment 5 Coverage

NEXT_PUBLIC R11V2 flags in source:
- `NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` (only one)

In deploy.yml:
- `NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY=false` ✓

Coverage: PASS.

## Architecture Substrate Established

- 5 provider adapters with CapabilityAdapter interface
- Central capability dispatcher (getAdapter, getManifest, getAllManifests, dispatch, isCapabilityAvailable, getSwitchStackHint)
- MigrationAdapter bridge (all 5 adapters delegate chat() via stubChat)
- CapabilityHint UI component + useProviderManifest + manifest-helpers
- Capability-path telemetry pipeline (Observatory integration)
- Runtime user toggle (NEXT_PUBLIC env-var + localStorage per-browser pref)
- Full foundation E2E test suite
