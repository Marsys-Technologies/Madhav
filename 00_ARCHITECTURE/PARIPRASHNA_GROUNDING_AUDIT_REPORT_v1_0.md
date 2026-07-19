---
artifact: PARIPRASHNA_GROUNDING_AUDIT_REPORT
canonical_id: PARIPRASHNA_GROUNDING_AUDIT_REPORT
version: 1.0
status: CURRENT — PG-1 wave synthesis report
verified_against_tree: 2026-07-19 (pg1/wave; 87 findings all ACCEPT by the Opus verification floor, 12/12 lanes)
authored_by: Lane Z-1 (SYNTHESIS), PG-1 Paripraśna Grounding Audit — Claude Code (Opus 4.8, 1M)
supersedes: none (new artifact)
purpose: >
  The consolidated verdict of the PG-1 grounding audit against
  PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.5). Delivers: the assumption
  verdict table for A1–A32; the new-defect register (F-25h…) continuing §16's
  F-number sequence; a findings-by-severity roll-up; the prioritized
  immediate-fixes list; and — verbatim and unsoftened — the three gate-critical
  verdicts (C-2 shim feasibility, Q-1 reading quality, R-3 falsification).
governing_inputs:
  - 00_ARCHITECTURE/pg1_audit/deliverables/pg1_findings.jsonl (87 findings)
  - 00_ARCHITECTURE/pg1_audit/state/PG1_LANE_*.md (12 lanes)
  - 00_ARCHITECTURE/pg1_audit/state/VERIFICATION_RECEIPTS.md
---

# Paripraśna Grounding Audit — Report (PG-1)

The PG-1 wave ran 12 read-only lanes against `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`
(v0.5) and the live tree/DB/infra. **87 findings, all verified ACCEPT** by the
Opus verification floor (two lanes — R-3, Q-1 — required an attempt-2 correction,
recorded in §Provenance below). This report synthesizes them; the sibling artifact
`RETRIEVAL_SYSTEM_TRUTH_v1_0.md` holds the current-state system description.

---

## §1 — Assumption verdict table (A1–A32)

Verdicts pulled from every finding carrying an `assumption` field, cross-referenced
against the `affects` field where a lane rendered a verdict indirectly. Where **no
lane's findings address an assumption**, it is marked **NOT AUDITED THIS WAVE** —
honestly, without fabricated coverage.

| # | Assumption (abbrev, §) | Verdict this wave | Driving finding(s) |
|---|---|---|---|
| **A-01** | Monorepo demoted; extend shim generator, wire `codegen:check` | **CONFIRMED accurate** — shim generator exists ("LANDED ALONGSIDE, NOT WIRED IN"); `codegen:check` npm script exists but is in **none** of the 8 CI workflows (drift undetected). | `PG1-R1-0004` |
| **A-02** | Delete 45 aliases; `layer_noun_verb` canon | **BASELINE CORRECTED** — 55 aliases (not 45); the alias layer is 139 tool names over 119 registry URIs. Deletion sizing must use 139/119. | `PG1-R1-0002/0003` |
| **A-03** | Three projections (MCP-full/compact/chat) | **UNBUILT (target-state)** — server registers all 139 tools unconditionally; no full/compact/chat split; `marsys_drill` in doc prose only. Compact-umbrella count must derive from 119, not 113. | `PG1-R1-0005` |
| **A-04** | `mutation: true` class; pull sidecar tools into registry | **UNBUILT** — no `mutation` field in `CapabilityDescriptor`; 3 KEYSTONE sidecar tools named in `server.ts` comments are the concrete pull-in inventory (independently confirmed by their double-encoded wire shape). | `PG1-R1-0006`, `PG1-R2-0010` |
| **A-05** | `density_contract` becomes mandatory | **CONFIRMED still optional** (`density_contract?:` at `types.ts:207`) — matches §N.6's own wording; promotion to mandatory has not happened. | `PG1-R1-0007` |
| **A-06** | One planner pipeline → vidhi validator → `PlanReceipt` | **UNBUILT, reality worse than doc** — 4 planner surfaces, 2 live-divergent (`PipelinePlan` web vs `VidhiPlan` MCP), 2 dead islands. `PlanReceipt` **absent from code entirely** (docs-only). | `PG1-R3-0001/0005/0006`, `PG1-R1-0008` |
| **A-07** | One agentic loop, two doors; MCP gets `prashna_ask` | **PARTIAL / "two doors" is one door** — loop extracted as a module, but its sole live caller is the web dispatch; `prashna_ask` has **ZERO source hits** (the apparent hits were the substring of horary `prashna_undertaking_get`). | `PG1-R3-0002` |
| **A-08** | Canonical store `conversation_messages` + `message_parts` child rows | **PARTIAL & mis-specified** — `conversation_messages` exists but parts are a `parts_json` **blob column**, not child rows; `UIMessage` still live across ~10 surfaces. Store is **empty (0 rows)** — the migration is green-field schema-hardening, not a salvage op. | `PG1-R3-0003`, `PG1-D1-0002/0003` |
| **A-09** | Model plane + OpenRouter + CachePlanner + reasoning-token accounting | **FULLY UNBUILT** — no `model_plane` file; "OpenRouter" appears only in the arch doc itself. A full build, not a refactor. | `PG1-R1-0009` |
| **A-10** | Per-turn provenance stamp in both channels, copied into ledger | **UNVERIFIABLE this wave** — R-1 lacked schema-read budget; partially informed by A-08 findings (metadata_json exists, no provenance column confirmed). | `PG1-R1-0010` |
| **A-11** | AI SDK transport replaced by typed SSE + reducer | **CONFIRMED (current-state premise)** — client runs `DefaultChatTransport`; nuance: an extra `@assistant-ui/react-ai-sdk` `useChatRuntime` wrapper sits between app and `ai` package, widening the replacement blast radius. | `PG1-C1-0004` |
| **A-12** | Block-level stream semantics (today is token-level) | **CONFIRMED** — `text-delta` written per provider token at `run_adapter_dispatch.ts:329`, no block buffering. | `PG1-C1-0005` |
| **A-13** | No virtualization; frozen-block memoization + `content-visibility` | **NOT AUDITED THIS WAVE** (the ruling itself; the dead virtualizer substrate is confirmed present via A-14). | — |
| **A-14** | Dead virtualizer present (substrate for the no-virtualization ruling) | **CONFIRMED present** — `VirtualizedMessageList.tsx` + `AdaptiveMessageList.tsx` exist, transitively dead. | `PG1-C1-0006`, `PG1-C3-0003/0005` |
| **A-15** | Citation sentinels; server rewrites before the wire | **UNBUILT / not prompt-alone** — `citation_check.ts` is entirely post-stream (regex count + cross-ref); the sentinel rewriter + hold-back buffer must be new code in the delta loop. | `PG1-C2-0005`, `PG1-C1-0007` |
| **A-16** | ~~Three disclosure tiers~~ | **STRUCK by D-15** — n/a; not audited (correctly, it no longer exists as an assumption). | — |
| **A-17** | Pre-commit server-side register gate | **CONFIRMED accurate (net-new)** — `citation_check.ts` validates provenance (one id family, `SIG.MSR.NNN`), not vocabulary; A-17's gate is additive, not a fix to existing logic. | `PG1-C1-0007` |
| **A-18** | Reader vocabulary in registry `register` block; missing labels fail CI | **CONFIRMED premise** — `bodha_msr_signals` text is 20/20 raw `key=value` internal register (debug-log-grade); editorial work is real and unowned. Sizing unit = distinct `signal_type_id`, not row count. | `PG1-S1-0001/0002`, `PG1-C1-0007` |
| **A-19** | NO-LEAKAGE four ways (DB roles, registry flag, out-of-proc writer, canary) | **ARM-1 0% BUILT (critical)** — none of the 5 designed DB roles exist; single `amjis_app` credential has full CRUD on the ledger + calibration it is designed to be walled from. Canary substrate exists but scope unconfirmed. | `PG1-D3-0004`, `PG1-C1-0011` |
| **A-20** | Streaming replay harness | **CONFIRMED net-new** — only a single hardcoded Playwright mock exists (`round6-mock-route.ts`); the multi-fixture adversarial-cadence replay server is genuinely unbuilt. | `PG1-C1-0010` |
| **A-21** | Client-side block segmentation; one markdown engine | **CONFIRMED cheap/mostly-done** — Streamdown v2.5.0 already does progressive block rendering + memoization; caveat: both `streamdown` and `react-markdown` ship (a consolidation, not a build). | `PG1-C2-0006` |
| **A-22** | Register lint defanged; never fail-the-turn | **CONFIRMED already true on adapter path** — `run_adapter_dispatch.ts` already logs-only/never-throws post-stream; A-22 codifies an existing pattern + extends it to the vocabulary class. | `PG1-C1-0009` |
| **A-23** | Sentinel failure handling (64B/400ms hold-back, tolerant grammar) | **UNBUILT** — no hold-back buffer exists; deltas written raw to the wire; required by A-15's rewriter. | `PG1-C2-0005` |
| **A-24** | Transport resilience (`Last-Event-ID` replay, ring buffer) | **CURRENT-STATE GAP CONFIRMED** (no forward-design verdict) — F-25f: resume is snapshot-based; `last_event_seq` stored, never consumed; no mid-session reconnect. | `PG1-C2-0008` (gate row), §16.6 |
| **A-25** | Failure UX adopts dead `classify-error.ts` | **SUBSTRATE CONFIRMED dead-but-present** — `classifyChatError` has zero importers; the file A-25 wants to adopt is exactly the confirmed dead code. | `PG1-C3-0001` |
| **A-26** | Mobile first-class | **LABEL CORRECTED + PARTIAL** — D-1 corrected the dispatch mislabel (A-26 is mobile, not conversation-migration); mobile itself verified PARTIAL in §16.6 (`md:` only), not freshly behaviourally audited. | `PG1-D1-0001` |
| **A-27** | Accessibility preserved + extended | **CONFIRMED live** — `aria-live={streaming?'polite':'off'}` present + behaviorally tested; axe-core harness is the outstanding forward ask. | `PG1-O1-0005` |
| **A-28** | Cross-conversation per-chart memory; `prior_reading` citation kind | **UNBUILT (honest forward conclusion)** — zero `prior_reading` hits; consistent with A-28's own not-yet-built framing. | `PG1-O1-0006` |
| **A-29** | The instrument can ask (clarification = 3rd planner outcome) | **CONFIRMED net-new** — planner has exactly two outcomes today (`PipelinePlan` or `PlannerFault`→422); no clarification state exists. | `PG1-C1-0001` |
| **A-30** | Calibration min-n gated, pooled, intervals, collect-only | **UNVERIFIABLE (out of S-1 charge)** — correctly self-scoped; route to a calibration-path lane. | `PG1-S1-0004` |
| **A-31** | Compliance decay designed for | **NOT AUDITED THIS WAVE.** | — |
| **A-32** | Disagreement captured as first-class rows | **UNVERIFIABLE (out of S-1 charge)** — doc's own §16.6 already marks it ABSENT/stubbed (F-25c); no dispute column in `conversation_messages`'s 7-col schema. | `PG1-S1-0005` |

**Coverage count:** of **A-1 … A-32 (32 assumptions)**, **29 received a verdict this
wave** (full, partial, or unverifiable-with-reason). **3 were NOT audited this
wave:** **A-13** (the no-virtualization ruling itself — only its dead substrate was
confirmed), **A-16** (struck by D-15, effectively n/a), and **A-31** (compliance
decay). A-24 received a current-state-gap confirmation but no forward-design
verdict; it is counted among the 29 as a partial. Beyond the A-1..A-32 range,
**A-34** (security/cost/durability) and **A-35** (`audience_tier` excision) also
received verdicts (O-1, C-1) and **A-36** (emotional register) was touched via
Q-1's remedy-register finding.

---

## §2 — New-defect register (continuing §16's F-number sequence)

The highest existing forensic number in `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md`
§16.1 is **F-25g**. The PG-1 wave surfaces the following genuinely-new
current-state defects, numbered **F-25h … F-25v** (added to the architecture doc
as append-only §16.7). Each is a NEW defect, not already carried in §16.1–§16.6.

| # | Defect | Severity | Driving finding |
|---|---|---|---|
| **F-25h** | Stale self-referential parity comment: `run_adapter_dispatch.ts:357` claims the adapter citation gate "mirrors the legacy gate at `route.ts:1373-1475`", but `consult/route.ts` is only 1030 lines — the range does not exist. Misleads a future editor into believing adapter/legacy citation gating is verified-equivalent. | low | `PG1-C1-0012` |
| **F-25i** | Hand-maintained tool census wrong: `server.ts:522 REGISTERED_TOOL_COUNT = 120` (self-labelled "authoritative") undercounts 4 files; live surface is **139** tool names over **119** registry URIs; the health endpoint reports the stale 120. GA.1/B.8 drift class. | high | `PG1-R1-0002` |
| **F-25j** | `drill_pointers`/`recover_via` degrade to the literal string `"unknown_tool"` on sidecar/alias-backed tools (`kala_windows_get` ×3, `phala_outlook_get` ×2), making the recovery pointer unusable; registry-backed L1 tools resolve correctly. Tool-name-threading bug in the trim-report constructor for the alias path. | medium | `PG1-R2-0001` |
| **F-25k** | `phala_anchors_get` schema over-promises: `date_range` is `.optional()` in the tool JSON/Zod schema but **mandatory** at the sidecar (`/api/compute/phala/event_anchors` 422s "Field required"); the alias wrapper synthesizes no default. First-day hard error on documented usage. | medium | `PG1-R2-0002` |
| **F-25l** | `ref_dignity_reference_get` 400 `internal_error` ("platform DB query failed: 400") on its flagship documented filter `planet=Saturn` — a broken code path on a non-exotic parameter, surfaced as a 500-class error instead of an honest empty. | high | `PG1-R2-0003` |
| **F-25m** | Default legacy envelope leaves `pagination.total` null even when `content.total` is known one level down (520/340/39 observed), giving a caller a false "total unknown"; populated only on the v3 path. | medium | `PG1-R2-0008` |
| **F-25n** | Three KEYSTONE sidecar tools (`mimamsa_calibration_get`, `mimamsa_insight_get`, `phala_mitigation_get`) double-encode their payload as a JSON **string** one level deeper than every other tool; `phala_mitigation_get`'s is additionally truncated mid-JSON by the budget. Breaks uniform envelope parsing. | medium | `PG1-R2-0010` |
| **F-25o** | Dead cost-accounting schema: `llm_usage_events`, `llm_provider_cost_reports`, `llm_cost_reconciliation` exist with the exact cost-attribution column set §14A.2 says is needed — and hold **0 rows each**, never wired into the request path. Remediation is "wire the existing schema," not "design it." | medium | `PG1-D2-0002` |
| **F-25p** | Two disjoint, unreconciled prediction ledgers with no shared id space: `mcp_predictions` (chat-side detector path, **0 rows**, id `PPL.CAL.*`) and `mimamsa_predictions` (L5 orchestrator build-time, **384 rows**, the one `mimamsa_calibration`/`phala_anchors` actually reference). §7's diagram presents one ledger; the codebase built two. | medium | `PG1-D3-0003` |
| **F-25q** | **NO-LEAKAGE role separation 0% built (critical).** None of §7.4's five designed roles exist; a single `amjis_app` credential — the same one the web app serves every request with — holds full CRUD (SELECT/INSERT/UPDATE/DELETE/TRUNCATE) on `mimamsa_predictions` (384-row ledger with outcomes) and `mimamsa_calibration`, the exact two surfaces `role_web_serve` is designed to be denied. Repo-wide grep for the five role names: zero hits. | critical | `PG1-D3-0004` |
| **F-25r** | §7 pipeline-diagram table names do not exist in the live DB: `brahma_mimamsa_prediction_ledger`, `brahma_mimamsa_answer_quality`, `brahma_phala_anchors` return zero rows in `information_schema`. The real tables are `mimamsa_predictions`, `mimamsa_qa_eval`, `phala_anchors` (no `brahma_` prefix). Diagram is target-state mislabelled as current. | medium | `PG1-D3-0001` |
| **F-25s** | Build-side interpretive-data integrity defects in `bodha_discoveries` / `mimamsa_insight_units`: (a) hypothesis rows carry an internal-varga citation mismatch (`aggregate_D108` row with `meaningfulness_basis: aggregate_d10`); (b) verdict strings render grade→word incoherence — `denied` at a neutral grade 5.0/10 with band `[0.35,0.65)` and prose "Conditional". A build-time consistency assertion is missing before persistence. | medium | `PG1-Q1-0005`, `PG1-Q1-0009` |
| **F-25t** | Cloud SQL PITR **disabled** on prod `amjis-postgres` (`pointInTimeRecoveryEnabled=False`); daily backups exist (7 retained, 02:00) but no PITR and **no restore drill ever executed** against a scratch instance — worst-case RPO ~24h on the irreplaceable ledger/conversation tables, not the near-zero §14A.3 calls for. Resolves §16.6's "nobody knows" to verified-and-insufficient. | high | `PG1-O1-0001/0002` |
| **F-25u** | `chart_facts` live row count diverges **+402%** from the sealed L1_GANITA_CLOSURE canonical (27,554 canonical vs **138,519** at BIND probe; 276,206 in later lane probes) — outside the §8.7 ±1% health tolerance, and the number is itself unstable across probes. Either legitimate post-closure enrichment or an idempotency/duplication defect; **undiagnosed** (PG-1 read-only). A sealed closure figure and the live table disagree by 5×. | high | BIND B-5, corroborated `PG1-D1-0003`/`PG1-D3-0002` (276,206) |
| **F-25v** | The Bearer-key MCP auth face returns **401** (`POST /mcp`, `Authorization: Bearer $MARSYS_MCP_KEY` → "Invalid or missing Bearer API key"), while the `?api_key=` seat is live. Either a stale/rotated prod key or an auth regression — unverifiable root cause, confirmed symptom; blocked R-2's ability to sweep the Bearer face and the verifier's ability to replay `mcp:` evidence. | medium | BIND B-3, VERIFICATION_RECEIPTS (R-2 note) |

**F-number range added this wave: F-25h through F-25v (15 entries).**

Note: `PG1-C2-0007` (writer path saturated with `as any`, reasoning has no
open/close lifecycle) is **not** assigned a new F-number — it corroborates the
existing **F-02/F-03** and the §19.7 gate row, and is recorded as a corroboration
in §16.1, not a new defect.

---

## §3 — Findings by severity

Across all 87 findings (all ACCEPT):

| Severity | Count | Notable examples |
|---|---|---|
| **critical** | 5 | NO-LEAKAGE roles 0% built (`D3-0004`); P0' shim cannot pass §19.7 without route reorder (`C2-0001`, `C2-0008`); no served reading has ever existed / §J unproven (`Q1-0001`); the systemic machinery-instead-of-synthesis diagnosis (`Q1-0012`); top-ranked discovery is a self-referential z-score (`Q1-0007`). |
| **high** | ~24 | census stale/wrong (`R1-0002`); `ref_dignity` 400 (`R2-0003`); cost/latency unmeasurable (`D2-0001`); PITR off + no restore drill (`O1-0001/0002`); 4-planner divergence (`R3-0001`); falsification week-scale (`R3-0007`); most Q-1 reading verdicts; signal text unreadable (`S1-0001`); green-field migration reframing (`D1-0003`). |
| **medium** | ~28 | drill `unknown_tool` (`R2-0001`); `phala_anchors` 422 (`R2-0002`); double-encoded sidecars (`R2-0010`); two ledgers (`D3-0003`); dead cost schema (`D2-0002`); A-08/A-07 partials; A-11 wrapper depth. |
| **low** | ~9 | stale parity comment (`C1-0012`); single_pass scaffold precision (`R3-0004`); dead-code clusters (`C3-*`). |
| **informational** | ~21 | confirmations that a target-state assumption is accurately scoped as unbuilt; deploy/rollback in sync (`O1-0003`); feature-flag infra ready (`O1-0004`); A2 gate holds (`R2-0004`). |

The three most consequential clusters are: **(1)** the NO-LEAKAGE / durability /
role-separation gap (`D3-0004`+`O1-0001/0002`+`F-25q`/`F-25t`) — the security spine
of the calibration mission is unbuilt at the DB level; **(2)** the P0' sequencing
reality (C-2) — the headline "3–4 week shim" bet is false as scoped; and **(3)**
the reading-quality verdict (Q-1) — the mission's central §J promise is, today,
entirely unproven by any live output.

---

## §4 — Prioritized recommended immediate fixes

Per §F2.1 of the audit brief, `codegen:check` CI-wiring is item 1. Ordering below
is by (blast-radius × cheapness × how-many-other-findings-it-unblocks). **This
report authorizes no code change; it recommends a fix sequence for the native's
ruling.**

1. **Wire `codegen:check` into CI (`§F2.1` mandate).** The npm script exists
   (`platform-mcp/package.json`) but appears in none of the 8 workflows; contract
   drift between the registry and the generated envelope/shims is currently
   undetected. One-line CI addition; directly closes the A-01 residual gap and is
   the mechanism that prevents the F-25i census-drift class from recurring.
   (`PG1-R1-0004`, `PG1-R1-0002`)
2. **Replace the hand-maintained `REGISTERED_TOOL_COUNT` with a runtime count**
   (`server.registrationCount`) and stop citing `CAPABILITY_MANIFEST.json`'s 113
   as an MCP figure. Kills F-25i and F-25v-adjacent confusion; makes 119/139
   authoritative. (`PG1-R1-0001/0002/0003`)
3. **Fix the two first-day hard errors:** `phala_anchors_get` (synthesize a
   default `date_range` or mark it required — F-25k) and `ref_dignity_reference_get`
   (repair or honestly-empty the `planet=Saturn` 400 — F-25l). Both hit a normal
   caller on day one. (`PG1-R2-0002/0003`)
4. **Fix the `unknown_tool` drill-pointer fallback** on sidecar/alias tools
   (F-25j) — the reference-don't-repeat contract the chat projection will inherit
   is broken on this class. (`PG1-R2-0001`)
5. **Decide the NO-LEAKAGE posture before any production reliance** (F-25q,
   critical): either build the 5 DB roles and migrate the web app off `amjis_app`
   for read paths, or explicitly downgrade §7.4 from an enforced invariant to an
   application-level convention with no DB backstop. Today the serving credential
   can leak outcome data into new predictions. (`PG1-D3-0004`)
6. **Enable Cloud SQL PITR + run one restore drill** (F-25t) — the doc's own
   "first action, costs an hour," still outstanding; the ledger and (future)
   conversation store are the only irreplaceable data. (`PG1-O1-0001/0002`)
7. **Diagnose the `chart_facts` +402% divergence** (F-25u) — a sealed closure
   figure (27,554) and the live table (138,519 / 276,206) disagree by 5×, and the
   live number is unstable across probes. Enrichment or duplication must be
   established before it silently poisons downstream sizing.
8. **Add the green-field `parts_json` schema-version discriminator now**
   (`D1-0003`, F-25e) — the store is empty (0 rows), so this is a zero-row
   migration that eliminates the "unverifiable migration" risk at near-zero cost,
   rather than a future salvage op.
9. **Wire the existing `llm_usage_events` cost schema + populate
   `query_trace_steps.latency_ms` + phase-tag `step_type`** (F-25o, `D2-0001`) —
   until then every cost/latency figure in the planning docs is a guess.
10. **Insert the missing build-time consistency assertion** on verdict
    grade→word→band coherence and varga citations before persistence (F-25s) —
    cheap, and it removes the most embarrassing intra-chart incoherence Q-1 found.

---

## §5 — Shim feasibility: NO

*(Gate item G.5. Reproduced faithfully from `PG1_LANE_C-2.md`, the load-bearing
judgment lane; not compressed.)*

**Shim feasibility: NO.** A translation shim CANNOT re-emit
`run_adapter_dispatch`'s existing event stream as the §12.3 typed SSE protocol
without touching the engine and the route. D-17's core premise — *"a disposable
shim over the existing engine, no planner work, old route untouched, 3–4 weeks"* —
is **FALSE as scoped.** (`PG1-C2-0001`, critical; `PG1-C2-0008`, critical)

**The single load-bearing fact.** §12.3 (arch doc:1545): *"The stream opens
immediately on POST. `turn.open` and `phase{plan, start}` go out before the planner
runs."* §19.7 (arch doc:3173) makes this a GATE PASS CONDITION: *"Work is visible
immediately | POST → `turn.open` < 300 ms; first activity < 1 s."* Today, in the
current tree:

1. The planner runs at `consult/route.ts:436-454`.
2. On `PlannerFault` the route returns a **non-streaming** `NextResponse.json(…,
   {status:422})` at `route.ts:447-450`; bundle validation returns a second 422 at
   `route.ts:803-806`.
3. The SSE stream does not exist until `runAdapterDispatch` is called at
   `route.ts:988` — **after** planning **and** after tool fetch (`route.ts:752-798`).
4. The first wire byte is written at `run_adapter_dispatch.ts:294`.

A pure translation shim wraps the stream `runAdapterDispatch` produces. It cannot
invent a `turn.open` that must occur *before that stream exists*, and the two 422
bail-outs are structurally mutually exclusive with an already-open stream (once
streaming headers are flushed you cannot set a 422 status). To emit `turn.open`
early you MUST (a) hoist `createUIMessageStream` to the top of the route, (b) move
the planner + tool-fetch inside the stream `execute` body, and (c) convert both 422
paths into in-stream `error` events. **That is a restructuring of the OLD ROUTE —
the exact thing D-17 says stays untouched.**

**Four §12.3 events have no source and require NEW emission, not translation**
(`PG1-C2-0003`): `citation.define` (no sentinel-rewrite pipeline exists — 
`citation_check.ts` counts ids post-hoc, `PG1-C2-0005`), `block.commit{final_md,
anchors}` (the assistant text is one flat `text-0` part, no server-side
segmentation, no anchors), `reasoning.open/close` (only a single flat
`{type:'reasoning'}` delta exists, no lifecycle), and true keyed `activity.upsert`
(today `data-tool` is append-per-event, dumped in one loop at synthesis-start
*after* retrieval, so "first activity < 1s" fails, `PG1-C2-0004`).

**The §19.7 gate row "no `as any` anywhere in the writer path" is violated at the
source** (`PG1-C2-0007`): six `as any` casts at `run_adapter_dispatch.ts:294,325,
329,334,354,573`, and reasoning has no open/close lifecycle. Passing this row needs
a fully typed writer protocol — not a wrapper that re-emits the existing `as any`
stream.

**Honest time estimate.** The full §19.7 gate as written is **~6–9 weeks with a
bounded route reorder**, not 3–4 weeks with an untouched route:

| Work item | Estimate | Touches "untouched" files? |
|---|---|---|
| A. Event re-label shim (shape only) | 3–5 days | no |
| B. Client render bet (freeze/caret) — mostly DONE via Streamdown | 3–5 days | no |
| C. Early `turn.open` <300ms + first activity <1s | ~1 wk | **YES — `consult/route.ts` reorder** |
| D. `citation.define` sentinel rewriter (§12.9.1) | 1–1.5 wk | **YES — dispatch delta loop** |
| E. `activity.upsert` live-emission + reader-label projection | ~1 wk | **YES — route tool loop + registry** |
| F. Typed writer protocol (kill 6 `as any`) + reasoning lifecycle | 3–5 days | **YES — dispatch writer** |
| G. Network resilience / reconnect-replay + mobile + a11y gate | 2–3 wk | net-new (§16.6 says absent) |
| **Total (full §19.7 gate)** | **~6–9 wk** | **route + dispatch, not untouched** |

**The one cleanly-green sub-answer** (`PG1-C2-0006`): client stable-prefix
segmentation already works — the client renders through Streamdown v2.5.0
(memoized), purpose-built for progressive block rendering; A-21/§12.4's "one engine,
freeze all but the last, memoize" is largely already implemented. The render HALF
of the bet is cheap; the problem is the render bet is **not where the risk lives** —
the SSE-protocol/route-reorder half is, and that half cannot be shimmed.

**What this means for D-17 (report, do not redesign — PC-2, the native's call):**
two honest options. **(1)** Keep 3–4 weeks, **descope** P0' to the render bet only,
accepting that `turn.open` ships *after* planning and the dead-air row is deferred —
but that does not prove the "feels like Claude Code / no dead air" bet D-17 says P0'
exists to prove. **(2)** Keep the full §19.7 gate, **budget ~6–9 weeks** with a
bounded reorder of `consult/route.ts` and the dispatch delta loop, dropping the "old
route untouched" constraint. **What is not honest is claiming the full gate in 3–4
weeks with an untouched route.**

---

## §6 — Reading-quality verdict (Q-1, full and unsoftened)

*(Gate item G.8. Reproduced from `PG1_LANE_Q-1.md`, corrected per the attempt-2
chart-scoping fix, without softening.)*

**The instrument does not, today, produce a single acharya-grade reading — because
it does not, today, produce a served reading at all, and every persisted
interpretive artifact that stands in for one describes the instrument's own
machinery instead of reading the chart.** (`PG1-Q1-0001`, critical; `PG1-Q1-0012`,
critical)

Q-1 was charged to sample 10 real past assistant readings and judge each against
the §J bar. **They do not exist.** The entire conversation store is empty:
`conversation_messages = 0`, `conversations = 0`, `conversation_branches = 0`,
`conversation_message_embeddings = 0`, `project_conversations = 0`, `llm_call_log =
0`, `tool_execution_log = 0`, `context_assembly_item_log = 0`, `query_plan_log = 0`.
**No user-facing reading has ever left this instrument and been persisted.** The
claim that this instrument reads at or above an acharya's level is, as of this
audit, **entirely unvalidated by any live output.** The Pariprashna conversational
surface is target-architecture (v0.5), not a running, reading-producing system.

Faithful to the charge, Q-1 judged the ten best available **proxies** — the
deterministic interpretive artifacts the build pipeline does persist: L5
`mimamsa_insight_units` verdicts, `mimamsa_predictions`, L2 `bodha_discoveries`
(whose columns `surface_reading`/`depth_reading`/`why_an_acharya_misses_it` are
built to embody the §J "reveals things I wouldn't have seen" clause), and
`bodha_rm_remedy_prescriptions`. **All ten fall short of §J.**

1. **Career** — falls short (generic slot-filled template; names no
   graha/bhava/dasha/yoga). One row per chart; no intra-chart contradiction.
2. **Health** — `"denied (grade 1.2/10). Mixed or insufficient evidence."` repeated
   across surgery/acute/chronic; `denied` and `insufficient evidence` are
   contradictory; no disease karaka or maraka window.
3. **Marriage** — `"denied (1.6/10). Mixed or insufficient evidence."` on the most
   anxiously-asked question; internally incoherent; no 7th house/Venus/Darakaraka/
   dasha; a bare frightening negative that **inverts §13.9's emotional-register
   obligation.**
4. **Grade/label/prose incoherence** — `"Education Milestone: denied (grade 5.0/10).
   Conditional — context-dependent."` The verdict word (maximally negative), the
   number (neutral), and the prose (conditional) contradict inside one string.
5. **Wealth** — `Major Financial Gain` and `Major Financial Loss` carry the
   IDENTICAL grade (2.3/10) and IDENTICAL band `[0.23,0.43)` — a tell the grade is a
   shared subsystem constant, not a lens-specific dhana/vyaya derivation.
6. **Top-ranked discovery** — `"Stands -5.9σ from ga_sade_sati baseline"`; circular
   (an acharya "misses it" because the instrument's own z-score is extreme); stored
   5+ times verbatim; no graha/bhava/dasha/meaning.
7. **Latent insight** — names an internal DB key `graha_kp_lords:prana_lord` and
   three of its own scores, declares "structurally consequential" with no jyotish
   content.
8. **Distributional hypothesis** — leaks raw column names (`aspects_VEN`,
   `constituent_facts_jsonb_atomic`) and predicts "distinctly unusual outcomes"
   without saying what; one row mismatches its own varga (D108 vs d10).
9. **Career-timing prediction** — `"elevated career career_discovery_event"`, an
   untranslated machine slug, repeated across 40+ rows, one identical window, null
   base_rate — not a sentence, not calibrated, not discriminatingly time-indexed.
10. **Remedy register** — every remedy is a second-person command (`"Recite…"`,
    `"Donate… Feed crows"`, `"Chant…"`) — the "you should do X" register **§13.8
    explicitly names as the exploitative line**, not the attributive "the tradition
    prescribes X." Citation is a synthetic slug (`"G27 remedy…"`) yet stamped
    `classical_strength_rating 0.90`. Mantra content is correct — the only favorable
    note — but correct content does not rescue a forbidden register.

**Attempt-2 correction (honest, per PC-7/PC-8 symmetry).** Three findings
(career/marriage/wealth) originally asserted the instrument emits SELF-CONTRADICTORY
verdicts for one chart. **That was wrong**: those rows came from two different
charts (Abhisek `482012f1` vs Abhinandan `1c826d5a`) compared without a `chart_id`
filter. Scoped correctly, **each chart carries exactly one verdict row per lens** —
delete-then-insert idempotency (§N.3) is functioning; the instrument does NOT
contradict itself within a chart. The "has not judged, it has enumerated" drama is
retracted. The corrected picture is **less lurid (no self-contradiction) but not
materially less damning for §J**: the surviving, chart-scoped, independently
re-confirmed defects — generic slot-filled verdict templates with zero graha/bhava/
dasha grounding, `denied` co-occurring with `Mixed or insufficient evidence`, gain
and loss sharing one grade — are enough on their own to place every one of the ten
proxies below the acharya bar.

**The systemic diagnosis (`PG1-Q1-0012`, unaffected by the correction):** across
every persisted interpretive layer, the instrument describes its own machinery —
grades, z-scores, salience, consequence scores, embedding distance ("Semantic
meaning-vector far from chart centroid" is the *entire* reasoning chain of a top
discovery), internal signal keys — in place of reading the chart. **The pipeline
computes structure impeccably and stops exactly one layer short of the reading.**

**The one fair mitigation:** L5 is sealed in explicit STRUCTURAL mode (CLAUDE.md
§E) — the missing empirical *calibration* numbers are by design. That is true and
honestly disclosed. **But it does not touch this verdict, because the failure here
is not missing calibration — it is missing astrological PROSE.** A verdict can be
uncalibrated and still read like an acharya wrote it; none of these do. The gap is
in the synthesis layer, not the calibration loop.

**Bottom line:** §J must be treated as **ASPIRATIONAL and UNPROVEN** until the
serve-time synthesis path runs end-to-end, persists real readings, and those
readings are put in front of the acharya bar. Nothing short of that can
substantiate the mission's central promise.

---

## §7 — Falsification exercise result (R-3, reproduced)

*(Gate corroboration. Reproduced from `PG1_LANE_R-3.md` / `PG1-R3-0007`.)*

**VERDICT: WEEK-SCALE INTEGRATION, NOT A CONTRADICTION.** The exercise (PC-3)
attempted to sketch the unified plan type A-06 calls for — floor+machine-band as
one addressable set, per-item served/empty/dark with CR refs, tool+args resolved
against `capability_version`, a decidable subsumption relation — and report
honestly whether it is a day, a week, or a genuine contradiction. **No type-theoretic
impossibility was found, and ~80% of the type already exists, unrecognized, as the
MCP `VidhiPlan`.**

The MCP path already realizes almost all of the unified type U:
`completeness_receipt.ts`'s `uniqueFloorItems()` already collapses
`[...floor, ...machine_band]` into one deduped addressable set keyed by
`primitive_id` (the "one addressable set" requirement — **DONE**); served/empty/dark
with `cr_row` + OPEN/LOGGED CR guarantee is **DONE**; tool+args resolve per
`CompiledFloorItem.live_tool` + `compileContract(chart_id)`, versioned by
`VIDHI_CAPABILITY_VERSION` (**DONE**); a `subsumes` relation over `primitive_id`
set-containment is trivially decidable (finite sets of string ids).

**Where the real cost lives — the honest week, three gaps, none fatal:**
1. **Namespace unification (load-bearing).** The web `PipelinePlan.tool_calls` are
   keyed by `tool_name` ("one of the tool_names in CAPABILITY_MANIFEST.json") and
   its few-shots emit R-alias names, whereas `VidhiPrimitive` keys on `live_tool` =
   bare MCP tool names. These are overlapping-but-distinct namespaces; subsumption
   is decidable only given a TOTAL `tool_name → primitive_id` map, which does not
   exist today (only a replay-oriented `tool_name_bridge.ts`). Building + CI-proving
   that map is the bulk of the week.
2. **LLM band-3 is not addressable** — today a free-text `llm_extension_note`, not
   typed items; must be promoted to `PlanItem`s with minted ids. Modest.
3. **Two runtimes** — deterministic vidhi is MCP-only; the live web route runs
   `PipelinePlan` with no floor/receipt/dark/`capability_version`. Unifying = wire
   the web consult route through the already-built vidhi compiler and emit U — which
   **couples this to the same `consult/route.ts` reorder C-2 priced** (§5 above).

**Why NOT a contradiction:** the only candidate — "a deterministic floor cannot
contain a non-deterministic LLM plan in one addressable set" — resolves cleanly:
floor/band items are deterministic, LLM items are additive-only
(`band === 'llm_extension'`), and `subsumes` is DEFINED to ignore `llm_extension`
items, so floor determinism is preserved while the LLM layer stays per-item
accountable. A-06 only requires the LLM plan be VALIDATED-as-covering the
deterministic floor, which set-containment provides.

**Honest verdict: a WEEK (5–8 working days)**, dominated by gap #1 (the total
`tool_name↔primitive_id` map + its CI proof) and gap #3 (route reorder to emit U).
Not a day (the namespace map + route reorder are real); not a contradiction (the
type closes; MCP already runs ~80% of it). **The negative-for-contradiction result
is the high-value finding: the architecture's unified plan type is INTEGRATION DEBT
(two live divergent planners + two dead islands), not a design impossibility.**
A-06 must not be treated as blocked.

---

## §Provenance — wave verification standing

12/12 lanes ACCEPT under the Opus verification floor; validator clean (87/87
findings, all shards valid). Two lanes were REJECTED on attempt 1 and corrected:
**R-3** (PG1-R3-0001 evidence[0] cited `consult/route.ts:758` for the `runPlanner`
call; the real call site is `:436` — a stale line number, substantive claim
unchanged; fixed, re-verified ACCEPT) and **Q-1** (three findings conflated two
charts' verdict rows as intra-chart self-contradictions; re-queried chart-scoped,
corrected down, re-verified ACCEPT — the systemic §J diagnosis was independent of
the conflation and stood). R-1 was REJECTED on a commit-boundary scope-warden
false-positive and reinstated ACCEPT by the Adjudicator (zero cross-lane authorship).
Full record: `VERIFICATION_RECEIPTS.md`.

*End of PARIPRASHNA_GROUNDING_AUDIT_REPORT v1.0 — PG-1 Lane Z-1, 2026-07-19.*
