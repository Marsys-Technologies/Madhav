---
artifact: RETRIEVAL_SYSTEM_TRUTH
canonical_id: RETRIEVAL_SYSTEM_TRUTH
version: 2.0
status: CURRENT — supersedes v1.0 (retained as historical record)
verified_against_tree: 2026-07-19 (pg2/wave, base origin/main @ 4b69df8c; PG-1 findings + PG-2 X-2/X-3 additions)
authored_by: Lane Z-2 (SYNTHESIS), PG-2 Diagnostic Wave — Claude Code (Opus 4.8, 1M); consolidating Lane Z-1 (PG-1) + Lanes X-2/X-3 (PG-2)
supersedes: RETRIEVAL_SYSTEM_TRUTH_v1_0.md (NOT deleted — v1.0 remains in place as the PG-1-era historical record; this v2.0 is the current ground-truth surface)
purpose: >
  The single ground-truth statement of what the MARSYS-JIS retrieval + serving
  system ACTUALLY IS, as of 2026-07-19. v1.0 (PG-1 Lane Z-1) drew this entirely
  from the PG-1 audit's static/behavioural findings and R-2's 35-tool sample, and
  X-3 later appended a §2b coverage extension to it in place. v2.0 consolidates
  v1.0 + X-3's ~96% coverage sweep + the single most important new datum this
  project has ever had: X-2's live, authenticated invocation of the chat engine,
  which is the FIRST real serving-path observation — and it is a deterministic
  failure. Where PARIPRASHNA_TARGET_ARCHITECTURE describes what should exist, this
  document describes what is observed to exist — declared and behavioural, live and
  dead, working and broken — and where the two disagree.
governing_inputs:
  - 00_ARCHITECTURE/RETRIEVAL_SYSTEM_TRUTH_v1_0.md (PG-1 Z-1 base + X-3 §2b append)
  - 00_ARCHITECTURE/pg1_audit/deliverables/pg1_findings.jsonl (98 findings, all ACCEPT)
  - 00_ARCHITECTURE/pg2_diagnostic/deliverables/pg2_findings.jsonl (44 findings, all ACCEPT)
  - 00_ARCHITECTURE/pg2_diagnostic/state/PG2_LANE_{X-2,X-3}.md
---

# Retrieval System Truth v2.0 — What Paripraśna Gets Designed Against

> **Reading contract.** Every number and behaviour is sourced to a PG-1 finding
> (`PG1-R1-0003`), a PG-2 finding (`PG2-X2-0001`), or a BIND observation. Nothing is
> asserted from memory or from the target-architecture document. Where a claim is the
> author's own synthesis judgment it says so (§6, §7). This document is descriptive of
> CURRENT STATE; it authorizes no code change.
>
> **Supersession note.** This v2.0 supersedes `RETRIEVAL_SYSTEM_TRUTH_v1_0.md`, which
> remains in place as the PG-1-era historical record (its §2b was X-3's in-place PG-2
> append). Read v1.0 only for audit trail; read v2.0 for current state.

---

## 0 — The one-paragraph truth (v2.0)

There is one platform capability registry (`platform/src/lib/retrieval/registry/`,
**119** distinct `marsys://tool/*` URIs) served through the MCP edge as **139** tool
aliases (many-to-one), documented internally by a hand-maintained census that says
**120** (stale, undercounts by 19), and mis-audited at PG-1 BIND against
`CAPABILITY_MANIFEST.json`'s **113** — which is a governance-artifact catalog, not an MCP
registry at all. Of those 139 tool names, **133 (~96%) have now been mechanically
exercised at least once** (PG-1 R-2's 35 + PG-2 X-3's 98); the surface mostly works and
is honest about its density on the `v3` envelope, but carries a handful of live defects a
first-day caller hits, a judgment-flags vocabulary far richer than documented but gated
behind `response_format=v3`, a planning plane split into two live-but-incompatible
planners plus two dead islands, and a cost/latency observability plane that is
schema-present but 100% unpopulated — so what the acharya floor costs in tools, bytes,
and milliseconds is still genuinely unmeasurable. **And now the decisive new fact: the
web chat engine — the actual Paripraśna serving path — has been invoked live for the
first time, and it fails deterministically with HTTP 500 before it streams a single
byte.** No served conversational reading has ever been produced or persisted, and now we
know precisely why. This is the substrate Paripraśna sits on.

---

## 1 — Real capability inventory: declared vs observed

### 1.1 The four numbers, and why only two of them are registries

PG-1 Lane R-1 (`PG1-R1-0001..0003`) established that BIND's "113 vs ~200" was **two
errors stacked**, not one drift:

| Number | Source | What it actually is | Use it as… |
|---|---|---|---|
| **113** | `CAPABILITY_MANIFEST.json` `entry_count` | A **governance-artifact catalog** (canonical_id, path, version, status, layer, expose_to_chat), first entry `CGP_AUDIT_v1_0.md`; no `input_schema`/`tool_role`. | **Never** as an MCP-capability count — a category error. (`PG1-R1-0001`) |
| **119** | `registry/layers/**` | The **real "one registry"** — distinct `marsys://tool/*` URIs across 104 files, `CapabilityDescriptor`-typed. | The **authoritative baseline** for "how many capabilities exist." (`PG1-R1-0003`) |
| **120** | `server.ts:522` `REGISTERED_TOOL_COUNT` | A **hand-maintained census comment** that undercounts four of its own cited files; the health endpoint reports it. | Nothing — GA.1/B.8 drift. (`PG1-R1-0002`, F-25i) |
| **139** | live `mcp__marsys-jis-direct__*` listing | The **actual served MCP tool-name surface** — a many-to-one **alias layer** over the 119 URIs. Reconciles: 120 + 5 (`registry_bridge`) + 3 (`register_p1_synthesis`) + 10 (`register_p1_aliases`) + 1 (`register_p2_dasha_lord`) = 139. | Sizing the MCP-compact projection (A-03) + alias deletion (A-02). |

**Corrected inventory sentence:** *119 distinct registry capabilities, served as 139 MCP
tool names via an alias layer, documented internally as 120 (stale undercount), audited
at BIND against 113 (wrong artifact entirely).*

### 1.2 Observed coverage: 133/139 (~96%) now exercised

PG-1 R-2 exercised 35/139 tools against chart `482012f1` (Abhisek) via the `?api_key=`
seat (mostly `response_format=legacy`). PG-2 Lane X-3 then exercised **98 additional
distinct tool names**, bringing combined coverage to **133/139 ≈ 96%** (`PG2-X3-0010`),
closing most of the G.4 coverage gap PG-1 disclosed.

**[CORRECTED PG-2 gate-runner review, 2026-07-19]** — the arithmetic as first written
did not reconcile: 35 (R-2) + 98 (X-3, "additional distinct") = 133, and 139 − 133 = 6,
not the "two tools remain unexercised" originally stated here (which implied 137
touched). The gate runner's independent anti-gaming pass caught this and it is recorded
honestly rather than resolved past the evidence (PC-1): either X-3's 98-count includes
some overlap with R-2's original 35 (meaning the true untouched set is larger than 2
but the 133 "combined distinct" figure is still correct), or the "two remaining" list is
incomplete. **X-3 named only two by identity** — `prashna_undertaking_get` (needs a
horary/prashna-cast chart, none of the 4 charts qualify) and `mimamsa_outcome_record`
(alias twin of `record_outcome`, not re-probed once the shared handler's 500 was
confirmed) — without reconciling the count against 139−133. This wave does not have
the evidence to name the remaining 0–4 tools with certainty; a follow-up pass should
produce the exact set-difference (full 139-name list minus R-2's 35 minus X-3's 98,
computed programmatically) rather than trusting either lane's manual tally.

**The Bearer-key MCP face is NOT broken** (revising v1.0/PG-1's open `F-25v`). PG-1 could
not authenticate the `Authorization: Bearer` face (401) and left root cause
`unverifiable`. X-3 resolved it (`PG2-X3-0001`): a raw `curl -X POST /mcp` with the
**correct** key returned **HTTP 200 with the full 139-tool `tools/list`** (both header
casings, both hosts); a **garbage** key reproduced PG-1's exact 401 byte-for-byte. Root
cause: a **stale/wrong key value** at PG-1's audit time — not a request-shape, host, or
server-side auth regression. (The exact stale value is unrecoverable;
`scripts/setup_mcp_env.sh` is gitignored and absent from the isolated worktree.)

---

## 2 — The serving path, observed live for the first time (PG-2 X-2)

> **This is the single most important addition in v2.0.** Every prior audit of the
> serving path was of an **unexercised** path (T-9): `conversation_messages = 0`, so no
> one had ever driven the deployed chat engine and observed what happens. X-2 did.

**The web chat engine (`/api/chat/consult`) fails deterministically with HTTP 500 before
it streams a single byte** (`PG2-X2-0001`). Two authenticated invocations (native login
flow, chart `482012f1`, real questions) 3.5 minutes apart both returned an identical body:

```
{"error":{"code":"SYSTEM_INTERNAL","message":"An unexpected server error occurred.",
"retry":false,"detail":"bundle_hydrator: floor asset 'FORENSIC' not found in manifest"}}
```

- **Root cause:** `platform/src/lib/bundle/bundle_hydrator.ts:25` hard-codes
  `FLOOR_ASSET_IDS = ['FORENSIC','CGM']` and throws at line 96 when a floor asset is
  absent from `CAPABILITY_MANIFEST.json`. `FORENSIC` was deleted from the manifest in PR
  #187 Legacy Teardown (CLAUDE.md §B); `grep -c FORENSIC CAPABILITY_MANIFEST.json` = 0.
  `route.ts:689` calls `hydrateBundle`; the throw is caught at `route.ts:1023-1027` and
  returns `res.internal()` → 500.
- **Same class as LCA-2, one stage downstream.** LCA-2 (the retired `reports` table,
  `route.ts:306-316`) was fixed; that unblocked the request far enough to hit the **next**
  retired-legacy relic. A NEW, distinct regression — same class, different asset.
- **Steady-state, not cold-start:** byte-identical across two calls + byte-identical
  Cloud Run logs (`[consume:v2] pre-stream error: … 'FORENSIC' not found in manifest`).
- **Partial write, not clean:** the eager `conversations` insert (`route.ts:375`) fires
  before the failing try block, so each failed call left an **orphaned `conversations`
  row** (2 total, both KEPT as first serving-path evidence:
  `14d96091-4038-461e-9a21-1e822bbe7555`, `3829624c-ff9f-4e19-96ba-4f10d87c03a0`). The
  planner ran and succeeded (`llm_call_log +2`, `query_plan_log +2`), but
  `conversation_messages` and `mcp_predictions` stayed 0 — both are written in
  `onFinish`, **structurally unreachable** past the `hydrateBundle` throw.
- **Why the prediction detector never fires (resolves `PG1-D3-0002`):** the detector is
  wired correctly but every request dies upstream of `onFinish`. It is not "no traffic"
  and not "silently swallowed write" — it is a specific, named-line 500.
- **Fix candidate (one line):** drop `'FORENSIC'` from `FLOOR_ASSET_IDS` (leaving `CGM`,
  which resolves), the direct analogue of the LCA-2 fix — plus a
  manifest-vs-`FLOOR_ASSET_IDS` CI assertion. After the fix, whether the engine produces
  a clean end-to-end reading or hits a THIRD retired relic cannot be known read-only.

**Consequence for §J and everything downstream.** CLAUDE.md §J acharya-grade quality
remains **unproven** — no reading has ever been produced. C-2's streaming-protocol
analysis (§3 / the ~6–9-week P0' estimate) is unaffected by X-2 (X-2 never reached the
stream), but the `bundle_hydrator` fix is now a hard prerequisite before any
streaming/shim work can be observed end-to-end.

---

## 3 — Behavioural profile per capability (including the dead and broken ones)

### 3.1 The surface mostly works and is honest about density (on v3)

Every whole-chart / signal-heavy tool triggered the R5 §N.6 response-budget trimmer
(`PG1-R2-0009`): `ganita_strength_get` 520→65, `ganita_sade_sati_get` 1259→78,
`bodha_domain_reading_get` 3107 signal_id_refs→200, etc. Drill pointers, tested
end-to-end on a **registry-backed** pair, resolve to richer data (`ganita_yogas_get` 7
catalog rows → `ganita_yoga_firings_get` 12 fired yogas with bhaṅga ledgers,
`PG1-R2-0006`). The chart-agnostic gate held (`PG1-R2-0004`), and PG-2 X-3 corroborated
**no cross-chart leakage** on a broader 12-tool second-chart (Abhinandan) sweep run
immediately after ~90 Abhisek calls (`PG2-X3-0008`).

### 3.2 Density signalling is `v3`-gated

The `judgment_flags` vocabulary is far richer than the "3" BIND documented — R-2 alone
surfaced ≥9 values (`PG1-R2-0007`) — but flags appear **only** under
`response_format=v3`. Every default-legacy call returned `judgment_flags: []` **even where
the underlying condition was present in `content`**. X-3 reconfirmed this on a second
chart (Abhinandan): the `catalog_only_rows_present` flag is present under v3 and absent
under legacy on `ganita_yogas_get` — **systemic envelope behavior, not a data artifact**
(`PG2-X3-0007`). Envelope `total` disclosure is v3-gated the same way (`PG1-R2-0008`,
F-25m). **For Paripraśna:** the chat projection must request v3 (or the default must flip)
or it inherits the legacy blindness §N.6 exists to prevent.

### 3.3 Live defects a first-day caller hits

| Tool | Defect | Finding |
|---|---|---|
| `phala_anchors_get` | **422** on its own documented-optional `date_range` (mandatory at the sidecar; alias synthesizes no default). Reconfirmed unchanged by X-3. | `PG1-R2-0002` / `PG2-X3-0002` |
| `ref_dignity_reference_get` | **400 `internal_error`** on its flagship `planet=Saturn`. X-3 confirmed chart-independent (fails on both Abhisek and Abhinandan) → pure code-path defect. | `PG1-R2-0003` / `PG2-X3-0003` |
| `record_outcome` | **500** on a syntactically valid but non-existent `prediction_id` (unguarded sidecar lookup) instead of a graceful 404. Its alias `mimamsa_outcome_record` almost certainly shares it. | `PG2-X3-0005` |
| `holistic_bundle_chart_facts` | Returns `type: bundle.completed` while only **3/8** sub-tools fire (UCN/RM/CDLM); 5 silently error (MSR/CGM/LEL/PANCHANG/DASHA). A caller trusting it for B.11 whole-chart-read is silently missing 5/8 subsystems. | `PG2-X3-0006` |

### 3.4 Drill pointers degrade to `"unknown_tool"` — now known systemic

The `drill_pointers`/`recover_via` self-reference resolves correctly on registry-backed
L1 tools but falls back to the literal `"unknown_tool"` on sidecar/alias-backed tools
(`kala_windows_get`, `phala_outlook_get`, `PG1-R2-0001`). X-3 found the **catalog family**
(`catalog_assets_all`/`catalog_assets_list`) also hits it (`PG2-X3-0004`) — so the defect
is **systemic to a broader class of Phase-1 alias-registered tools**, not the 2–3 R-2
sampled. Fix at the alias-registration self-reference helper.

### 3.5 Three KEYSTONE sidecar tools break the uniform envelope

`mimamsa_calibration_get`, `mimamsa_insight_get`, `phala_mitigation_get` double-encode
their payload as a JSON **string** one level deeper than every other tool;
`phala_mitigation_get`'s is additionally truncated mid-JSON by the budget (`PG1-R2-0010`,
F-25n). The concrete A-04 sidecar pull-in inventory, confirmed from the wire shape.

### 3.6 Whole-chart tools can exceed the client token ceiling

X-3 found `assess_career/health/marriage/wealth`, `get_temporal_windows` (289KB),
`kala_temporal_bundle`, `get_domain_reading`, `ref_nakshatra_get` produce 92–289KB
payloads too large for the calling MCP client even after server-side trimming, even with
narrow params (`PG2-X3-0009`). Either these tools are exempt from the `response_budget.ts`
trimmer that protects other whole-chart tools, or the trim ceiling is miscalibrated
against realistic client token limits.

### 3.7 Dead capability islands (C-3 census, 6 clusters)

Zero-importer code the plane carries but never runs: `classify-error.ts`'s
`classifyChatError` (the very classifier A-25 wants to adopt, `PG1-C3-0001`);
`retrieval/adapters/agentic_loop/` (7-file island distinct from the LIVE
`synthesis/agentic_loop`, `PG1-C3-0002`); `AdaptiveMessageList.tsx` +
`VirtualizedMessageList.tsx` — **but note A-14's inversion below**; `useChatSession.ts`;
the `consume/lifecycle/` folder (5 shells over the LIVE `useChatLifecycle` hook).

> **A-14 correction (PG-2 X-4, `PG2-X4-0006`).** PG-1 called the virtualizer
> "transitively dead." X-4 found the render picture is the **inverse of A-14's target**:
> `VirtualizedMessageList.tsx` IS imported live by `AdaptiveMessageList.tsx`, while **both**
> techniques A-14 mandates to replace it are **absent** (`content-visibility` = 0 hits,
> frozen-block memoization = 0 hits). So the virtualizer A-14 says to *remove* is running,
> and neither replacement is built — a real target-vs-actual gap. (PG-1 also mislabelled
> this ruling A-13; the memoization ruling is A-14, §12.7.)

---

## 4 — The planning path as it actually runs

Unchanged from v1.0 (`PG1-R3-0001`): **four planner surfaces, two live-but-incompatible,
two dead islands.**

| # | Surface | Wired? | Emits | Floor/dark/CR/version? |
|---|---|---|---|---|
| 1 | `pipeline_planner.ts` (web consult, `route.ts:436`) | **LIVE** | `PipelinePlan` | **NO — none** |
| 2 | `plan_builder.ts` (MCP `plan_retrieval`, `server.ts:388`) | **LIVE** | `VidhiPlan` (+ `completeness_receipt` served/empty/dark + `capability_version`) | **YES — all** |
| 3 | `retrieval/router/router.ts` | **DEAD ISLAND** | `RouteResult` | partial, unused |
| 4 | `lib/vidhi/compiler.ts` | **DEAD ISLAND** | `CompiledContract` | yes, unused |

The identical career question yields a `PipelinePlan` on web and a `VidhiPlan` on MCP —
**two non-interoperating plan objects**. `single_pass` is a **test scaffold not on the
runtime path** (`PG1-R3-0004`); the live single-vs-agentic choice is inline at
`run_adapter_dispatch.ts:314`. `PlanReceipt` is **absent from code entirely**
(`PG1-R3-0005`; PG-2 X-4 reconfirmed `PG2-X4-0008`) — its de-facto analogue is the MCP
`VidhiPlan` + `CompletenessReceipt`.

---

## 5 — What the acharya floor costs; and known-dark territory

**Cost/latency is genuinely unmeasurable today** (`PG1-D2-0001/0002`, F-25o): the
cost-accounting tables (`llm_usage_events`, `llm_provider_cost_reports`,
`llm_cost_reconciliation`) exist with the exact right columns and hold **0 rows each**;
`query_trace_steps.latency_ms` is NULL on all rows and `step_type` is `'sql'` only. Cost-
per-turn-by-model and p50/p95 TTFT are not computable even in principle. Remediation is
"wire the existing schema," not "design one."

**Known-dark territory is real and shipped, MCP-only** (`PG1-R3-0006`): the
`completeness_receipt.ts` `dark[]` bucket emits `{floor_item_id, cr_row}` with `cr_row`
matching `/^CR-\d+$/`, guaranteed OPEN/LOGGED. The traced `career_deepdive` (12 floor
items) carries 5 dark at issuance (CR-56/64/24/66/69). **The channel asymmetry Paripraśna
must close:** the live web `PipelinePlan` carries **no dark concept at all** — no floor,
no receipt, no CR pointers, no `capability_version` — so a native asking on the portal
gets no machine-readable account of what was structurally unavailable, while an MCP caller
gets the full dark ledger. This is the single sharpest current-state gap between channels.

---

## 6 — Prediction-ledger landscape (PG-2 X-5 refinement of §16/OT-11)

v1.0 (via PG-1 F-25p) described **two** disjoint prediction ledgers. PG-2 X-5 established
the live landscape is **three** tables plus the anchor set `record_outcome` actually
resolves against (`PG2-X5-0006`):

- `mimamsa_predictions` — 384 rows, build-time L5 (`mi_bhavisya`), referenced by
  `mimamsa_calibration`; the only populated + referenced ledger.
- `mcp_predictions` — 0 rows, chat-detector interim relay (migration 071, explicitly
  TODO-migrate); written by `ppl_writer.ts`/`calibration_producer.ts`.
- `brahma_prospective_ledger` — 5 rows, D-4a §11 explicit-filing ledger.

`record_outcome` writes to **neither prediction ledger**, and there are **two
same-sounding tools** hitting different tables: `record_outcome` → `phala_anchors` +
`mimamsa_calibration` (sidecar); `mimamsa_outcome_record` → `mcp_predictions`
(`PG2-X5-0005`). **Neither table satisfies §14.3 without a schema change** — none carries
`message_part_id` FK / `created_from_channel` / the 8-state lifecycle
(`PG2-X5-0004`). OT-11 (which ledger is canonical) is now **fully costed** but
deliberately left as an open native fork (PC-8) — see
`PG2_DIAGNOSTIC_REPORT_v1_0.md §7` and the architecture doc's OT-11 row.

**Also surfaced:** the sidecar `outcome.py` references `phala_anchors` columns absent from
the live schema — a runtime-breaking drift the `record_outcome` sidecar would hit
(`PG2-X5-0005`).

---

## 7 — Recommended chat projection (synthesis judgment, carried from v1.0)

> **Author's own synthesis recommendation for architecture §8.3, not an observed fact.**

Unchanged from v1.0 §6, now with X-2's hard prerequisite prepended:

0. **Fix `bundle_hydrator`'s stale `FORENSIC` floor asset first** (`PG2-X2-0001`) — the
   engine cannot produce any reading until this one-line unblock lands.
1. **Request `response_format=v3` unconditionally** — the entire density/total disclosure
   apparatus is v3-gated (§3.2); legacy silently inherits the blindness §N.6 prevents.
2. **Route the chat plan through the MCP `VidhiPlan` compiler, not web `PipelinePlan`** —
   the floor/dark/CR/`capability_version` machinery exists only MCP-side (§5); R-3's
   falsification shows unifying is week-scale, not a contradiction.
3. **Exclude sidecar/alias tools with broken recovery pointers / hard errors from the
   drill surface** until F-25j/k/l/n + the catalog-family `unknown_tool` (`PG2-X3-0004`)
   are fixed.
4. **Size against 119 registry URIs**, not 113/120/139.

The chat projection is *"fix bundle_hydrator → v3 envelope + VidhiPlan floor + drill
surface minus the broken sidecar tools, filtered per turn from the 119-URI registry."*

---

## Appendix — finding-id index

**PG-1 (v1.0 base):** R-1 `PG1-R1-0001/0002/0003`; R-2 `PG1-R2-0001..0010`; R-3
`PG1-R3-0001/0004/0005/0006/0007`; D-2 `PG1-D2-0001/0002`; D-3 `PG1-D3-0003/0004`; C-3
`PG1-C3-0001..0006`.
**PG-2 (v2.0 additions):** X-2 `PG2-X2-0001` (chat engine 500); X-3 `PG2-X3-0001` (Bearer),
`-0002/0003` (known-broken reconfirm), `-0004` (catalog unknown_tool), `-0005`
(record_outcome 500), `-0006` (holistic bundle partial), `-0007` (v3 gating 2nd chart),
`-0008` (no leakage 2nd chart), `-0009` (client token ceiling), `-0010` (coverage 96%);
X-4 `PG2-X4-0006` (A-14 inversion), `-0008` (planner/PlanReceipt not-built); X-5
`PG2-X5-0004/0005/0006` (ledger landscape).

*End of RETRIEVAL_SYSTEM_TRUTH v2.0 — PG-2 Lane Z-2, 2026-07-19. v1.0 retained as
historical record.*
