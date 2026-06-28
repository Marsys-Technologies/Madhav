---
artifact: MCP_CHANNEL_AUDIT_D0_v1_0.md
canonical_id: MCP_CHANNEL_AUDIT_D0
version: 1.0
status: CURRENT — current-state map of the MCP channel; gates the production-hardening plan
created: 2026-06-28
author: Cowork (planning) — D0-style audit for the MCP-channel workstream, native Abhisek Mohanty
classification: audit / current-state map (mirrors the retrieval D0 pattern)
parent: MCP_CHANNEL_CONVERSATION_HANDOFF_v1_0 (the workstream this opens)
verification_basis: code (main HEAD 13c141a9) + git + deploy.yml. LIVE-PROD verification of the
  deployed Cloud Run revision is PENDING (sandbox has no gcloud/GCP creds; amjis-mcp is IAM-gated
  --no-allow-unauthenticated). The exact native-run probe steps are in §7.
hard_constraints_inherited:
  - chart-agnostic, zero native contamination (principle #14)
  - no audience tier
  - reference-don't-restate (§N.5 / F3)
  - reverse-citation gate before ANY deletion
  - prod-only data plane (verify against prod after merge, not worktree)
  - single-source-of-query-logic invariant (the registry is the one query source)
changelog:
  - v1.0 (2026-06-28): First D0 current-state map. Headline finding — the live wired MCP surface
    does NOT match the seal narrative. It is 26 hand-wired tools that bypass the sealed lib/retrieval
    registry (24 of 26), have zero outputSchema/structuredContent coverage, and carry 2 live native
    contamination defects the ISSUE-7 gate did not catch (it scans for native UUIDs/names, not
    native-data fallbacks or native-hardcoded tools). Per-area rebuild/update/fix decisions in §6.
---

# MCP CHANNEL — D0 CURRENT-STATE AUDIT (v1.0)

> The MCP-channel workstream inherited a "sealed, clean, gate-protected" foundation per the handoff.
> This audit reads the live code, git, and deploy config to establish ground truth before any
> hardening plan. **Headline: the wired MCP surface and the seal narrative diverge materially.**
> The retrieval *registry* is sealed and clean; the *MCP server that is supposed to project it is not
> projecting it.* This is not cleanup the handoff missed — it is a genuine architectural gap the seal's
> "20/20 drift parity" did not cover, because that parity was measured at the registry layer, not at
> the wired MCP server. The good news: the fix is well-scoped and the inherited registry is sound.

---

## §1 — What's genuinely sealed and sound (inherited, verified)

| Component | State | Verified by |
|---|---|---|
| `lib/retrieval` registry (D1 contract, 3 primitive types, 4 adapters, URI scheme) | ✅ sound, clean | code validation §H.1 (one LOW only) |
| Chart-agnostic CI gate incl. `scanMcpToolFileContent()` over `platform-mcp/src/tools/` | ✅ present, 3 tests | `chart_agnostic_gate.ts` on disk |
| Zero native **UUIDs/names** in `platform-mcp/src/tools/` | ✅ clean | grep `482012f1|NATIVE_CHART_ID|Abhisek` → 0 files |
| Transport = Streamable HTTP, POST-only, stateless (`sessionIdGenerator: undefined`); GET /mcp → 405 | ✅ correct (Gemini-safe) | `server.ts:139-160` |
| OAuth 2.0 endpoints (authorize/token/refresh + discovery + openid-config) for ChatGPT connector | ✅ wired | `server.ts:54-67` |
| Bearer key auth (header or `?api_key=`) | ✅ wired | `server.ts:77-101` |
| amjis-mcp in CI deploy (GH Actions WIF, Artifact Registry, IAM-gated, runtime SA) | ✅ wired | `deploy.yml:392-445` |
| Tool naming — zero `-` in any of the 26 tool names | ✅ Gemini-compatible on naming | per-file scan |

**Bottom line on the inheritance:** the registry and the gate are real and good. The transport choice
is correct for the cross-provider intersection. Auth scaffolding exists. Naming is clean. ISSUE-7 (native
UUIDs in unwired files) IS genuinely closed. The problems are all in the *wired tool surface* and in
*what the seal did not measure*.

---

## §2 — Headline findings (the ground truth that contradicts the narrative)

### F-1 — The wired MCP surface bypasses the sealed registry (single-source invariant BROKEN at MCP)
The handoff says "12 consolidated workflow-shaped tools over the registry … both channels share one
query source." **Live reality:** `server.ts` wires **26 distinct tools** from hand-written files under
`platform-mcp/src/tools/`. **24 of 26 do NOT consume `lib/retrieval`** — they hit the Python sidecar by
raw REST or open a direct Postgres `Pool` and run SQL. Only **2** (`mitigation_map`, `muhurta_finder`)
reach the registry, and only *indirectly* via the platform route `/api/mcp/primitives/[tool]`. **No MCP
tool file imports `lib/retrieval` at all** (grep: 0 hits). The single-source-of-query-logic invariant —
"what the whole campaign bought" — does not hold on the MCP channel. The "20/20 drift parity" was a
registry-layer measurement; it did not exercise the wired MCP server.

### F-2 — Tool count is wrong everywhere it's stated
Claimed "12 consolidated"; health endpoint hardcodes `tools: 13` (`server.ts:165`, a stale literal that
counts registration *calls*, not tools); **actual wired tool count = 26**. No artifact currently states
the true number.

### F-3 — Zero provider-obligation output compliance
**0 of 26** tools declare an `outputSchema`, return `structuredContent`, implement cursor pagination
(`nextCursor`), or expose a `response_format`/verbosity enum. Every tool returns
`content:[{type:'text', text: JSON.stringify(...)}]` — text fallback only, no machine-readable channel.
The two registry-routed tools return the *raw platform envelope object* instead of MCP `content`, which
is worse for MCP-client compatibility. This fails the core provider-spec obligations checklist outright.

### F-4 — Two LIVE native-contamination defects the ISSUE-7 gate cannot catch
The gate scans for native **UUIDs/names**. These two defects encode the native as **data/behavior**, so
they passed:
- **`ephemeris_cache_native_lifetime`** (`l0_ephemeris.ts:243-265`) — a tool **hardcoded to the native**:
  name, LLM-visible description ("native's lifetime window 1984-2070"), and endpoint
  `/native_lifetime_meta`. No `chart_id` at all. A native-specific tool shipped on a chart-agnostic surface.
- **`kala_temporal_bundle`** (`kala_temporal.ts`) — takes a generic `chart_id`, BUT ships a large
  native-specific FORENSIC fallback (dasha periods 1984-2028, Sade Sati, `DEFAULT_SNAPSHOT_DATE='2026-06-05'`,
  native MD/AD/PD) returned for **any** chart_id when the sidecar is down (`:156-341, :436`). On sidecar
  failure it returns *the native's life arc for a stranger's chart*. This is a principle-#14 violation
  (native-as-fallback) that the UUID-only gate does not detect. Also embeds native dasha specifics in the
  live `description:` string (LLM-visible native leak).

### F-5 — Per-chart input hygiene is otherwise good
Setting aside F-4: every genuinely per-chart tool (`holistic_bundle`, `holistic_bundle_chart_facts`,
`event_anchors`, `phala_outlook`, `mitigation_map`, `muhurta_finder`, `lel_query`) takes `chart_id` as a
**required** `.uuid()` with no native default and errors if missing. No `?? NATIVE`, no `.default(<uuid>)`,
no hardcoded canonical/phantom id in any input schema. The contamination is concentrated in F-4, not spread.

### F-6 — Declared-profile mechanism (MARO) is unbuilt on MCP
Design says declared→profiled / undeclared→universal-best per connecting model family. The DECLARATION
MECHANISM (config / OAuth scope / per-key / client hint) was left to this workstream and **is not wired**.
MARO does not shape the MCP surface today; the surface is a flat 26-tool list for every client.

### F-7 — `audience_tier` residue persists in MCP resources
Code validation flagged `house_rules_variants/{client,acharya,super_admin}.md` + an active
`server_tier_visibility.test.ts` despite the no-tier doctrine. To re-verify post-seal and strip.

---

## §3 — The 26 wired tools (inventory)

| Layer | Tool(s) | Source path | Query source | Per-chart hygiene |
|---|---|---|---|---|
| L0 | `resolve_entity`, `list_entities`, `asset_registry_all`, `asset_registry_l0`, `intent_classify` | `tools/l0_brahmagyan.ts` | platform REST (not registry) | n/a |
| L0 | `query_planet_position`, `query_planet_transit`, `query_aspects_at_time`, `query_retrograde_periods`, `ephemeris_cache_year`, `ephemeris_cache_native_lifetime` | `tools/l0_ephemeris.ts` | sidecar REST | **F-4: last tool native-hardcoded** |
| L1 | `compute_natal_positions`, `query_dasha_periods`, `query_special_lagnas` | `tools/retrieval/pyhora_natal.ts` | sidecar REST | birth-params, clean |
| L2 | `holistic_bundle` | `tools/bo_2-8.ts` | sidecar REST | clean (req chart_id) |
| L2 | `holistic_bundle_chart_facts` | `tools/retrieval/holistic_bundle.ts` | **direct PG Pool** | clean (req chart_id) |
| L3 | `kala_temporal_bundle` | `tools/retrieval/kala_temporal.ts` | sidecar REST + **native fallback** | **F-4: native life-arc fallback** |
| L0 | `query_remedies`, `query_remedies_for_chart`, `list_remedies_by_category`, `read_remedy`, `query_tantric_remedies`, `query_remedies_by_planet`, `query_mantras` | `tools/retrieval/remedy_tools.ts` | **direct PG Pool** | corpus (chart-agnostic), clean |
| L4 | `event_anchors` | `tools/phala_event_anchors.ts` | sidecar REST | clean (req chart_id) |
| L4 | `mitigation_map` | `tools/phala_mitigation_map.ts` | **REGISTRY (indirect)** | clean (req chart_id) |
| L4 | `muhurta_finder` | `tools/muhurta_finder.ts` | **REGISTRY (indirect)** | clean (req chart_id) |
| L4 | `phala_outlook` | `tools/phala_outlook.ts` | sidecar REST | clean (req chart_id) |
| L5 | `lel_query` | `tools/mimamsa_lel_intake.ts` | sidecar REST | clean (req chart_id) |
| L5 | `record_outcome`, `query_calibration` | `tools/mimamsa_outcome.ts` | sidecar REST | chart_id optional (calibration-scoped) |

Total = **26**. Registry-backed = **2**. outputSchema/structuredContent = **0**.

---

## §4 — Provider-obligations gap matrix

Checklist from `RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md` Part 3. **PASS** = satisfied across the
surface; **GAP** = not satisfied; **PARTIAL** = some tools.

| # | Obligation | Status | Note |
|---|---|---|---|
| 1 | Tool names valid charset, unique, 1–128 | ✅ PASS | all snake_case |
| 2 | Avoid `-` in names (Gemini) | ✅ PASS | 0 hyphens |
| 3 | `inputSchema` always valid object, never null | ✅ PASS | zod schemas present |
| 4 | Intent-rich `description` | ⚠️ PARTIAL | present, but some embed native specifics (F-4) |
| 5 | Human-readable `title` | ❓ VERIFY | not confirmed per-tool |
| 6 | `outputSchema` declared | ❌ GAP | 0/26 |
| 7 | `structuredContent` returned | ❌ GAP | 0/26 |
| 8 | Serialized JSON in `text` block (fallback) | ✅ PASS | all return text JSON (the only channel) |
| 9 | Input-validation failures as tool errors (`isError:true`) | ❓ VERIFY | per-tool error shape unconfirmed |
| 10 | Honest `annotations` (readOnly/destructive/idempotent/openWorld) | ❌ GAP | not set |
| 11 | Token-bounded responses (pagination/filter/truncate) | ❌ GAP | no pagination/caps |
| 12 | `response_format`/verbosity enum | ❌ GAP | 0/26 |
| 13 | Default response cap (~25k tokens, Anthropic) | ❌ GAP | none |
| 14 | UUIDs → human-meaningful names | ⚠️ PARTIAL | some tools resolve names; not systematic |
| 15 | Consolidated workflow tools, set small (<~20) | ❌ GAP | 26 granular tools, not consolidated |
| 16 | Resources for read-only context; prompts for slash-commands | ❓ VERIFY | resources exist; tier residue (F-7) |
| 17 | Cursor pagination on every list op, opaque cursors | ❌ GAP | none |
| 18 | HTTPS Streamable HTTP | ✅ PASS | correct |
| 19 | Input validation / access-control / rate-limit / output sanitize | ⚠️ PARTIAL | auth yes; **rate-limit GAP** |
| 20 | Human-in-the-loop deny | ✅ via client | OAuth `require_approval` defaults on (OpenAI) |
| 21 | Treat tool/resource content as untrusted | ❓ VERIFY | injection-surface review pending |
| 22 | Plain tool-calling backend for DeepSeek (no MCP) | ✅ PASS by transport | DeepSeek consumes as backend, not via /mcp |
| 23 | Don't assume Gemini-3 reachability | ⚠️ NOTE | external constraint, not a code fix |
| 24 | Tolerate OpenAI approval flow + `defer_loading` | ❓ VERIFY | approval yes; defer_loading untested |
| 25 | Progressive-disclosure discovery for large catalogs | ❌ GAP | flat 26-tool list |

**Score: 4 PASS (+2 by transport/client), 11 GAP, 4 PARTIAL, 6 VERIFY.** The surface satisfies transport,
naming, and auth scaffolding; it fails nearly every *output-shape* and *token-discipline* obligation.

---

## §5 — Per-client readiness

| Client | Reachable? | Blockers |
|---|---|---|
| **Claude MCP connector** | Auth + transport OK | no outputSchema/structuredContent; no response cap; consolidation; F-4 contamination |
| **ChatGPT connector** | OAuth wired | needs strict structured outputs; approval flow OK; arg-decode (JSON string) — verify; defer_loading untested |
| **Gemini Remote-MCP** | Transport OK (Streamable HTTP, no `-`) | **Gemini-3 reachability unknown (external)**; thought_signature round-trip — verify; schema-strictness for ANY-mode |
| **DeepSeek (backend, no MCP)** | n/a via /mcp | consumes tools as plain function-calling backend; validate-and-repair mandatory; `reasoning_content` passback (V4); deepseek-v4-flash pinned (ISSUE-6 ✅) |

No client is production-ready today. All are blocked on the same core gaps (F-1, F-3) plus client-specific
verification.

---

## §6 — Per-area rebuild / update / fix decision

Mirrors the retrieval D0 disposition pattern. **R**=rebuild, **U**=update, **F**=fix-in-place, **V**=verify.

| Area | Decision | Rationale |
|---|---|---|
| Wired tool → registry consumption (F-1) | **R (rebuild the projection layer)** | The 26 hand-wired tools should become a thin projection of `lib/retrieval`, not 26 parallel query paths. Rebuild the wiring so MCP tools call the registry; retire direct-sidecar/direct-PG paths under the reverse-citation gate. This restores the single-source invariant. Biggest item. |
| Output shape (F-3): outputSchema + structuredContent + text | **U (uniform envelope)** | Add a shared MCP response envelope (outputSchema + structuredContent + text fallback) once, applied to all tools — ideally in the projection layer so it's free per tool. |
| Native contamination (F-4) | **F (surgical, urgent-ish)** | Retire/parameterize `ephemeris_cache_native_lifetime` (make it `ephemeris_cache_range(chart birth window)` or drop); strip the native FORENSIC fallback from `kala_temporal_bundle` (fail honestly instead of serving native data); scrub native specifics from descriptions. **Extend the CI gate to catch native-data fallbacks + native-hardcoded tools, not just UUIDs.** Reverse-citation before any deletion. |
| Tool count / health literal (F-2) | **F (trivial)** | Compute `tools` dynamically; reconcile the "12 consolidated" framing with the real number after consolidation. |
| Consolidation + progressive disclosure (#15, #25) | **R (topology decision)** | Decide the consolidated topology per principle #13 (astrological traversal) — likely an `action`-param umbrella per layer. This is a design task before the build. |
| Pagination / response cap / response_format (#11,12,13,17) | **U** | Add to the shared envelope + list ops once the projection layer exists. |
| Declared-profile / MARO on MCP (F-6) | **R (mechanism + wiring)** | Resolve Decision Point #10 (config/OAuth-scope/per-key/client-hint) then wire declared→profiled / undeclared→universal-best. Depends on the projection layer existing. |
| Rate limiting (#19) | **U** | Add at the Express layer or Cloud Run; not present today. |
| `audience_tier` residue (F-7) | **F** | Re-verify post-seal; strip variants + test. |
| Annotations, titles, error shape, untrusted-content (#5,9,10,21) | **V then F** | Verify per-tool, then fix in the envelope. |
| Deployment / revision drift | **V (live, native-run)** | §7. amjis-mcp redeploys only when `changes.outputs.mcp==true` — confirm the running revision == main HEAD. |

**Sequencing implication:** the projection-layer rebuild (F-1) is the keystone — output shape, pagination,
response_format, MARO, and consolidation all become cheap once tools project the registry through one
envelope. F-4 (contamination) is independent and should go first as a surgical safety fix. The handoff's
§6 agenda still holds, but step 2 ("production-harden") now has a concrete, ordered backlog.

---

## §7 — LIVE-PROD verification (native-run; could not run from sandbox)

The sandbox has no gcloud/GCP creds and amjis-mcp is `--no-allow-unauthenticated`. Run these on your
machine (or hand to Claude Code) to close the deployment-state question before the verify-revision rule
([[feedback-verify-cloud-run-revision-before-chrome-probe]]):

```bash
# 1) Which revision is live, and does it match main HEAD (13c141a9)?
gcloud run services describe amjis-mcp --region asia-south1 \
  --format='value(status.traffic[0].revisionName, status.latestReadyRevisionName)'
gcloud run revisions describe <revisionName> --region asia-south1 \
  --format='value(spec.containers[0].image)'   # image tag == github.sha of main?

# 2) Authenticated health probe (IAM-gated service)
TOKEN=$(gcloud auth print-identity-token)
curl -s -H "Authorization: Bearer $TOKEN" \
  https://amjis-mcp-938361928218.asia-south1.run.app/health
#   → expect {status:ok, ... tools:13}  ← NOTE the 13 is the stale literal (F-2), not real count

# 3) Real MCP handshake: list tools with a valid app key (confirm 26, names, schemas)
curl -s -X POST https://amjis-mcp-938361928218.asia-south1.run.app/mcp \
  -H "Authorization: Bearer <app_mcp_key>" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq '.result.tools | length, [.[].name]'
```

Record the results back into this artifact (§7 results block) before the hardening plan is briefed.

---

## §8 — What this audit does NOT cover (correctly out of scope)

- **ISSUE-4 (L2 Bodha MSR rebuild)** — data-layer, owned by the L2 Bodha campaign. Low fact-resolution is
  NOT an MCP bug; do not chase it here.
- **Retrieval logic gaps** — any retrieval-capability gap found while hardening routes BACK to the registry
  (§7 of the handoff: the MCP channel is a thin adapter, never a place to reimplement retrieval).
- **Product-surface (discovery/onboarding/docs/multi-tenant UX)** — the larger arc; design after hardening.

---

*End of MCP_CHANNEL_AUDIT_D0 v1.0. Next: native runs §7 live-prod verification; then Cowork authors the
production-hardening plan + CLAUDECODE briefs in the §6 order (F-4 contamination fix first, then the F-1
projection-layer rebuild as the keystone).*
