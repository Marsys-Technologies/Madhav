---
canonical_id: R11A_FOUNDATION_PHASE_PLAN
project_name: Claude Takeover
version: 1.0
status: CURRENT
phase: R11.A — Foundation (project: Claude Takeover)
parent_arc: Claude Takeover — Multi-Provider Parity (R11 v2)
owner: Abhisek Mohanty
branch: chat-v2/round11-a-foundation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR11A
execution: sequential-single-stream-via-conductor
authored: 2026-05-22
companion_docs:
  - 00_ARCHITECTURE/CAPABILITY_MATRIX.md
  - 00_ARCHITECTURE/MULTI_PROVIDER_PARITY_ROADMAP.md
  - 00_ARCHITECTURE/chat_v2_briefs/round11_v2/R11V2_MASTER_PLAN_v1_0.md
  - 00_ARCHITECTURE/chat_v2_briefs/round11/NATIVE_RULINGS_v1_0.md (carry-forward)
---

# R11.A — Foundation Phase

## §1 — Mission

Stand up the **provider-agnostic capability adapter substrate** that every subsequent R11 v2 phase builds on. R11.A delivers no user-perceivable features; it delivers the infrastructure that lets future phases ship features once-across-all-five-providers instead of five times.

After R11.A merges:
- A `ProviderCapabilities` manifest is declared by each of the 5 provider adapters.
- A unified `CapabilityAdapter` interface exists; each provider implements it.
- A `dispatcher` routes capability calls from the chat surface to the active provider's adapter.
- The existing single-shot pipeline is wrapped in a `MigrationAdapter` so legacy behavior is preserved.
- A `CapabilityHint` UI component reads the active provider's manifest and surfaces "Switch to <stack>" hints when needed.
- A telemetry hook logs which capability path was taken per request.
- A runtime user toggle (master env-var AND localStorage user-pref) controls whether the new chat shell is engaged.

R11.A is **launch-ready** as of this plan's authoring (2026-05-22).

## §2 — Sessions (14 total, sequential)

| # | Session ID | Brief | Flag | Default | Client-side | Risk |
|---|-----------|-------|------|---------|-------------|------|
| 1 | A-S0 | capability-manifest-schema | FLAGLESS (type definitions) | — | n/a | low |
| 2 | A-S1 | provider-adapter-interface | FLAGLESS (type definitions) | — | n/a | low |
| 3 | A-S2 | anthropic-adapter-skeleton | FLAGLESS | — | no | low |
| 4 | A-S3 | google-adapter-skeleton | FLAGLESS | — | no | low |
| 5 | A-S4 | openai-adapter-skeleton | FLAGLESS | — | no | low |
| 6 | A-S5 | deepseek-adapter-skeleton | FLAGLESS | — | no | low |
| 7 | A-S6 | nvidia-adapter-skeleton | FLAGLESS | — | no | low |
| 8 | A-S7 | capability-dispatcher | MARSYS_FLAG_R11V2_USE_ADAPTERS | true | no (server-side) | medium |
| 9 | A-S8 | ui-availability-surface | FLAGLESS (additive component) | — | yes | low |
| 10 | A-S9 | telemetry-capability-paths | MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY | true | no (server-side) | low |
| 11 | A-S10 | migration-adapter | MARSYS_FLAG_R11V2_USE_ADAPTERS (same as A-S7) | true | no (server-side) | medium |
| 12 | A-S11 | runtime-user-toggle | MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY | **false** | yes (NEXT_PUBLIC) | medium |
| 13 | A-S12 | foundation-e2e-tests | FLAGLESS (test infrastructure) | — | n/a | low |
| 14 | **R11A-MERGE** | auto-pr-merge | — | — | — | terminal |

## §3 — Flag taxonomy introduced by R11.A

### Top-level master flag (R11 v2 wide)
- `MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` (NEXT_PUBLIC, default false) — master kill-switch. When false, the new chat shell + adapter layer are not engaged. When true, R11.A A-S11's user-pref toggle becomes the secondary gate.

### Adapter-layer flags (server-side, internal)
- `MARSYS_FLAG_R11V2_USE_ADAPTERS` (server-side, default **true** after A-S10 verifies migration adapter preserves existing behavior). When false, the chat surface bypasses the adapter and calls the legacy single-shot pipeline directly (rollback path).
- `MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY` (server-side, default true) — logs capability paths to Observatory.

### Per-provider feature manifest
Not a flag but a runtime-readable manifest exposed by each provider adapter. The UI reads `currentProvider.capabilities.<feature>` to decide affordance visibility.

## §4 — Carry-forward from R11 v1

Per `00_ARCHITECTURE/chat_v2_briefs/round11/SUPERSESSION_NOTE.md §3`:

- **NATIVE_RULINGS §1 (preserve Marsys palette)** — applies to A-S8 (UI availability surface) and A-S11 (runtime toggle); both use Marsys gold/charcoal styling.
- **NATIVE_RULINGS §5 (sacred components)** — A-S10 (migration adapter) preserves PerMessageDetailsDrawer, Cost Visibility, PanelMember rendering verbatim.
- **NATIVE_RULINGS §6 (Conductor STRICT halt + auto-merge)** — R11.A's Conductor inherits this.
- **NATIVE_RULINGS §8 (runtime user toggle)** — re-implemented in A-S11 with R11 v2 naming.

## §5 — Acceptance — R11.A close

R11.A closes when:
1. All 13 implementation sessions PASS.
2. R11A-MERGE pushes, opens PR, auto-merges.
3. `CAPABILITY_MATRIX.md` updates: foundation rows flip from 🚧 to ✓.
4. `MULTI_PROVIDER_PARITY_ROADMAP.md §5` updates R11.A row with close date + merge SHA.
5. Provider manifests are runtime-readable: `curl https://<staging>/api/debug/provider-manifest?stack=anthropic` returns the manifest JSON for verification.

## §6 — Files in scope for R11.A

### New files (created across A-S0..A-S12)

- `platform/src/lib/providers/capabilities.ts` — `ProviderCapabilities` TypeScript interface (A-S0)
- `platform/src/lib/providers/manifest-validator.ts` — runtime validator (A-S0)
- `platform/src/lib/providers/adapter.ts` — `CapabilityAdapter` interface (A-S1)
- `platform/src/lib/providers/dispatcher.ts` — central registry + capability dispatch (A-S7)
- `platform/src/lib/providers/migration-adapter.ts` — legacy pipeline wrapper (A-S10)
- `platform/src/lib/providers/anthropic/adapter.ts` + `manifest.ts` (A-S2)
- `platform/src/lib/providers/google/adapter.ts` + `manifest.ts` (A-S3)
- `platform/src/lib/providers/openai/adapter.ts` + `manifest.ts` (A-S4)
- `platform/src/lib/providers/deepseek/adapter.ts` + `manifest.ts` (A-S5)
- `platform/src/lib/providers/nvidia/adapter.ts` + `manifest.ts` (A-S6)
- `platform/src/components/chat/CapabilityHint.tsx` (A-S8)
- `platform/src/lib/observatory/capability_telemetry.ts` (A-S9)
- `platform/src/lib/chat-v2/useMultiProviderParity.ts` (A-S11)
- `platform/src/components/consume/MultiProviderParityToggle.tsx` (A-S11)
- `platform/tests/providers/*` — adapter contract tests + foundation smoke (A-S12)

### Modified files

- `platform/src/lib/config/feature_flags.ts` — register the three new flags (A-S0/A-S9/A-S11)
- `.github/workflows/deploy.yml` — add `NEXT_PUBLIC_MARSYS_FLAG_R11V2_MULTI_PROVIDER_PARITY` build-arg (A-S11)
- `platform/src/app/api/chat/consume/route.ts` — emit `data-capability-path` SSE part (A-S9); integrate dispatcher (A-S7)
- `platform/src/components/consume/ConsumeChatV2.tsx` — mount `MultiProviderParityToggle` (A-S11)
- `platform/src/lib/models/resolver.ts` — bridge from existing model resolver into new adapter (A-S10)

## §7 — Files MUST NOT touch

- Any R11 v1 superseded brief file (audit trail only)
- Phase 4C files
- Observatory dashboard (we add to the telemetry pipeline, not the dashboard UI)
- PerMessageDetailsDrawer, PanelMember, Cost Visibility (sacred per `NATIVE_RULINGS §5`)
- `.consume-shell` styling block in globals.css (R11.B owns visual changes)
- Existing tool implementations in `lib/retrieve/` (preserved verbatim)

## §8 — Conductor + queue

- Conductor prompt: `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_R11A_v1_0.md`
- Queue: `00_ARCHITECTURE/CONDUCTOR/session_queue_R11A.yaml` (14 entries)
- Worktree: `/Users/Dev/Vibe-Coding/Apps/MadhavR11A`
- Branch: `chat-v2/round11-a-foundation`
- Setup + Kickoff prompts: `phase-A/CLAUDE_CODE_SETUP_PROMPT.md` + `CLAUDE_CODE_KICKOFF_PROMPT.md`

---

*End of R11A_PLAN_v1_0.md.*
