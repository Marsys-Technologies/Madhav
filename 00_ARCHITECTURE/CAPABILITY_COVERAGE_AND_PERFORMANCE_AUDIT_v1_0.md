---
artifact: CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md
canonical_id: CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT
version: 1.2
status: SUPERSEDED-AS-COMPLETE
closed_by: M5_COVERAGE_CAMPAIGN_CLOSE_2026-05-21
closed_on: "2026-05-21"
final_defect_disposition:
  shipped: 55
  carry_forward: 3
  total: 58
  carry_forward_items:
    - "MSR signal-grounding gap: 419/573 signals lack explicit FORENSIC/LEL citations (surfaced ICR-S2)"
    - "Bootstrap build_manifests auto-registration audit (open follow-up Phase 4C close)"
    - "PLANNER_PROMPT R-rule: warn when cited signal has pending PROPOSED patch"
  carry_forward_queue: "00_ARCHITECTURE/V1_3_AUDIT_QUEUE_v1_0.md"
authored_on: 2026-05-21
authored_by: Cowork session — Capability-Coverage-and-Performance-Audit
role: >
  Forensic audit of (a) the asset → retrieval-tool → manifest → planner
  coverage chain and (b) the super-admin Performance tab, plus a phased
  remediation plan that closes every defect under M5 governance discipline.
  Diagnostic + plan; not a code-edit session. Read-only authorship.
produced_during: M5-A (concurrent with Phase 4C Wave 1 close)
authoritative_side: claude
mirror_obligations:
  claude_side: 00_ARCHITECTURE/CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  rationale: >
    This is a Claude-side execution-planning artifact. Gemini's L4 Discovery
    Layer role does not bind to retrieval-tool or planner internals. No
    Gemini-side counterpart needed; mirror_enforcer.py emits
    PASS_DECLARED_CLAUDE_ONLY.
consumers:
  - native (decision authority on remediation prioritization)
  - subsequent CLAUDECODE_BRIEF authoring (one brief per remediation session in §G–§I)
  - PLANNER_PROMPT_v2_0 amendment cycle (R-rule + few-shot updates downstream of §G)
  - OBSERVATORY_REDESIGN_PLAN_v1_0 (this audit identifies gaps that plan does not cover)
related:
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - 00_ARCHITECTURE/manifest_overrides.yaml
  - 00_ARCHITECTURE/MANIFEST_AUDIT_v1_0.md
  - 00_ARCHITECTURE/ASSET_INVENTORY_REPORT_v1_0.md
  - 00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json
  - 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md
  - 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md
  - 00_ARCHITECTURE/OBSERVATORY_REDESIGN_PLAN_v1_0.md
  - 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md
  - platform/src/lib/retrieve/index.ts
  - platform/src/lib/pipeline/manifest_compressor.ts
  - platform/src/lib/pipeline/manifest_planner.ts
  - platform/src/lib/performance/compliance.ts
  - platform/src/lib/performance/ingestion.ts
  - platform/src/components/performance/PerformanceClient.tsx
changelog:
  - v1.2 (2026-05-21): added §G.8–G.10 (COV-S8–S10), §C.8–C.10, §N (ICR
    stream, six sessions ICR-S1 through ICR-S6), §H.5 (PERF-S5 conflict
    panel). Promoted from v1.0 to v1.2 to match campaign queue spec_version.
    Total sessions: COV 1–10, PERF 1–5, ICR 1–6 = 21 sessions across three
    parallel streams.
  - v1.0 (2026-05-21): initial audit + plan. Diagnostic of supply side
    (manifest + retrieval-tool registry), demand side (planner +
    manifest_compressor + PLANNER_PROMPT), and the /performance dashboard
    surface. Forty-one defects identified; six P0, twelve P1, twenty-three
    P2. Remediation organized into two parallel session streams: §G
    (Capability) seven sessions, §H (Performance) four sessions. Native
    decisions pending on three items in §I.
---

# Capability Coverage and Performance Audit v1.2

## §A — Mission

This artifact answers two questions the native asked together:

1. Are all data assets that add astrological value fully reachable through retrieval tools, registered on the capability manifest, schema-documented, and selectable by the LLM-first planner — or are there silent gaps along that four-stage chain?

2. Is the `/performance` super-admin dashboard a meaningful instrument for diagnosing where the asset → retrieval-tool → planner → synthesis pipeline is failing, or is it an outdated outcome-shaped scoreboard that hides the actual operating state?

The audit is forensic and read-only. No code was changed. Every defect cited carries a file path, a line number, and a verification command. Remediation lands across two parallel session streams in §G and §H; the native approves a brief before each session begins.

## §B — Method and scope

Three independent investigations were run in parallel against `main` at 2026-05-21:

1. **Supply side** — Enumerate every asset folder, every entry in `CAPABILITY_MANIFEST.json`, every wired retrieval tool under `platform/src/lib/retrieve/` and `platform/python-sidecar/`, and the curated overlays in `manifest_overrides.yaml`. Cross-check folder ↔ manifest ↔ tool.

2. **Demand side** — Read `PLANNER_PROMPT_v2_0.md` v2.3 and `manifest_compressor.ts` line-by-line. Trace what the planner actually sees at runtime versus what is wired in the retrieval registry. Compare against `tests/eval/planner_golden_set.json` and `regression_baseline.json`.

3. **Performance surface** — Locate the Performance tab, read `PerformanceClient.tsx` plus every aggregator under `platform/src/lib/performance/`, audit the wiring to its backing tables, and identify stale references (post-Phase-11B rename, removed flags, deleted code paths).

Findings from the three streams were reconciled and load-bearing claims were re-verified by direct read of the cited code. Manifest counts cite the May 21 2026 audit at `MANIFEST_AUDIT_v1_0.md` (163 entries, 12 expected fingerprint drifts on living files, zero missing files). Phase-O cost telemetry, Observatory redesign sessions OBS-S1/S2/S3, and Phase-4C panchang chat-side wiring are treated as already-shipped context and not re-audited.

Reachability is judged against the native's stated rule: *if an asset adds astrological value, the planner must be able to reach it*. Governance, schema, and ledger files are exempt from the rule when they carry `expose_to_chat: false` and are not consumed at synthesis time.

## §C — Capability coverage findings

The coverage chain has four gates. An asset is fully reachable only if it passes all four:

```
gate 1: asset exists at the file or row level
gate 2: a retrieval tool reads it
gate 3: that tool is registered on CAPABILITY_MANIFEST.json with a tool_name binding
gate 4: that tool is emitted by manifest_compressor.ts into the planner's <manifest> block
```

The audit found that gates 1 and 2 are largely healthy, gate 3 is severely under-populated, and gate 4 is the load-bearing chokepoint that quietly excludes most of the registry.

### §C.1 — Asset inventory (gate 1)

Every asset folder enumerated in Phase 14 (`ASSET_INVENTORY_REPORT_v1_0.md`) is still on disk. Eleven previously-flagged archive candidates were archived and the manifest reflects 163 current entries with no missing files (`MANIFEST_AUDIT_v1_0.md`, 2026-05-21). The ephemeris CSVs that Phase 14 flagged as "DEAD_DATA, inert today" are no longer inert — `python-sidecar/pipeline/bootstrap_ephemeris.py` and `pipeline/ingest_eclipses_retrogrades.py` ingest them into `ephemeris_daily` (≈657k rows), `eclipses_staging`, and `retrogrades_staging`, all surfaced by `query_ephemeris.ts` and `temporal.ts`.

Two folder-level gaps remain at gate 1, both of which contain assets the native has invested in but which the manifest does not list:

- `00_NAK/` carries 26 nakshatra design files; zero appear in `CAPABILITY_MANIFEST.json`. If these are pure design specs (not consumed at synthesis time) they are correctly absent; if any carry interpretive content the planner should reach, that content is silently unavailable.
- `05_TEMPORAL_ENGINES/` carries 19 files describing dasha, transit, KP, and varshaphala computation surfaces. The retrieval tools that consume these surfaces are wired (`query_dasha_periods`, `query_transit_event`, `kp_query`, `query_varshaphala`), but the underlying source assets themselves have no manifest entries — meaning planner-discoverable asset binding via `linked_data_asset_id` is impossible for any temporal tool.

### §C.2 — Retrieval-tool registry (gate 2)

`platform/src/lib/retrieve/index.ts` lines 86–116 export a `RETRIEVAL_TOOLS[]` array containing **30 tools** (not 21, not 24, not 26; the trace-side constant `ALL_21_RETRIEVAL_TOOLS` in `platform/src/lib/trace/types.ts` lines 251–281 is misnamed and the `RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md` doc is stale on this point — M9 tools 27 + 28 are in fact wired). The 30 tools are:

```
msr_sql, pattern_register, resonance_register, cluster_atlas,
contradiction_register, temporal, query_msr_aggregate,
cgm_graph_walk, manifest_query, vector_search, kp_query,
saham_query, divisional_query, chart_facts_query,
cross_varga_dignity_query, domain_report_query,
remedial_codex_query, timeline_query, query_signal_state,
query_kp_ruling_planets, query_varshaphala, lel_query,
classical_text_search, classical_attribution_lookup,
multi_school_signal_lookup, convergence_score_lookup,
query_ephemeris, query_panchanga, query_transit_event,
query_dasha_periods
```

Description quality in code is bimodal. Five tools carry rich, planner-grade docstrings (`lel_query`, `query_ephemeris`, `query_panchanga`, `query_transit_event`, `multi_school_signal_lookup`, `convergence_score_lookup`). Six more carry one-paragraph descriptions with a routing hint (`kp_query`, `saham_query`, `divisional_query`, `cross_varga_dignity_query`, `query_kp_ruling_planets`, `query_varshaphala`). The remaining **14 tools carry no inline description at all** — they are pure functions with a `name` and a `retrieve()` implementation, nothing else. The 14 are: `msr_sql`, `pattern_register`, `resonance_register`, `cluster_atlas`, `contradiction_register`, `temporal`, `query_msr_aggregate`, `cgm_graph_walk`, `manifest_query`, `vector_search`, `chart_facts_query`, `domain_report_query`, `remedial_codex_query`, `timeline_query`, `query_signal_state`. The `RetrievalTool` type at `platform/src/lib/retrieve/types.ts` line 92 declares `description?` as optional, which is how this passed review.

Three Python-sidecar endpoints have **no TypeScript retrieval-tool wrapper**, meaning they are sidecar-only and the planner cannot reach them at all: `/api/compute/muhurat`, `/jaimini_drishti`, `/v7_additions`. The first one — Muhurat — was shipped in Phase 4C as a user-facing computation but is reachable only through the `/panchang` UI surface, not through the chat planner.

### §C.3 — Manifest tool bindings (gate 3)

Of the 163 entries in `CAPABILITY_MANIFEST.json`, **five carry a `tool_name` field**: `lel_query`, `classical_text_search`, `classical_attribution_lookup`, `multi_school_signal_lookup`, `convergence_score_lookup`. **Three carry a `query_schema`**: `lel_query`, `multi_school_signal_lookup`, `convergence_score_lookup`. **One carries a `retrieval_tool` field**: only `PANCHANG_DAILY_v1_0 → query_panchanga`, and this uses a different field name (`retrieval_tool`) than the rest of the registry (`tool_name`), meaning the field is read by nothing — see §C.4.

Per-entry field histogram across the 163 entries:

```
path                  160    near-universal
status                160    near-universal
canonical_id          141
layer                 141
expose_to_chat        120    28 true / 92 false / 43 missing
representations       120    always ["file"]
interface_version     114
fingerprint           112
description            33    free-text, mostly ingestion-script blurbs
preferred_for          11    only the 7 L2.5/L1 hot-path assets + 4 domain reports
cost_weight            11    same 11
tool_name               5    lel_query + classical_* + M9 pair
tool_description        5    same five
query_schema            3    lel_query + M9 pair
token_cost_hint         3
linked_data_asset_id    3
retrieval_tool          1    PANCHANG_DAILY only — orphan field
expose_to_planner       0    flag does not exist in the schema
```

The schema effectively carries no canonical asset → tool binding. 162 of 163 entries do not declare which retrieval tool reads them. Per-tool JSON Schema input declarations exist for 3 of the 30 wired tools. There is no machine-readable way to ask the manifest "what tool exposes asset X" or "what asset does tool Y read."

`manifest_overrides.yaml` curates 11 entries with `preferred_for` routing hints (`factual`, `interpretive`, `holistic`, etc.) and `cost_weight` for token budgeting. These 11 are the hot-path assets (FORENSIC, CGM, UCN, CDLM, RM, MSR, LEL, plus four domain reports). 152 of 163 manifest entries get no curated metadata. The override file also declares an `additional_entries:` section containing five L6 learning-substrate schemas and five L3.5 discovery registers — but their build-time merge into the manifest is fragile and warrants verification (none of these IDs appeared in the manifest sample we read).

### §C.4 — Planner visibility (gate 4)

`platform/src/lib/pipeline/manifest_compressor.ts` is the single chokepoint between the registry and the planner. The algorithm is:

1. Iterate `manifest.entries[]`. Keep only entries that carry `tool_name`. (162 of 163 entries are dropped here.)
2. Iterate a hardcoded list of 11 names called `PRIMARY_TOOL_NAMES` (lines 55–68). Look each name up in the map from step 1. Entries not present are silently skipped (line 104: `if (!entry) continue`).
3. Project each survivor into a 5-field compressed shape `{t, d, p, c, a}`: tool name, description (capped at 15 words, lines 78–83), parameter names (extracted from `query_schema.properties`), cost hint, and `linked_data_asset_id`.
4. Sort by `t` and serialize to a deterministic JSON string for inclusion in the planner prompt.

The composition of steps 1 and 2 produces an intersection. A tool is planner-visible only if **both** (a) it has `tool_name` in the manifest, AND (b) its name is hardcoded in `PRIMARY_TOOL_NAMES`. The current intersection contains **three tools**:

```
lel_query                       (in PRIMARY, in manifest with tool_name)
multi_school_signal_lookup      (in PRIMARY, in manifest with tool_name)
convergence_score_lookup        (in PRIMARY, in manifest with tool_name)
```

The other two manifest entries with `tool_name` (`classical_text_search`, `classical_attribution_lookup`) are not in `PRIMARY_TOOL_NAMES` and are silently filtered out. Eight names in `PRIMARY_TOOL_NAMES` are silently dropped because they have no `tool_name` manifest entry: `msr_sql`, `pattern_register`, `resonance_register`, `cluster_atlas`, `contradiction_register`, `cgm_graph_walk`, `vector_search`, `remedial_codex_query`. The header comment at line 50 still says "8 primary tools the LLM-first planner is allowed to call" — stale by three; the list contains 11.

The planner therefore receives a `<manifest>` block containing three tools at runtime. The other 27 wired tools are planner-blind through the manifest path. They are reachable only because `PLANNER_PROMPT_v2_0.md` v2.3 carries 32 numbered R-rules plus 11 named rules that mention specific tool names in routing instructions and 31 worked examples, and the planner LLM has memorized the names. Tools that R-rules do not name remain entirely orphaned: `timeline_query`, `saham_query`, `query_msr_aggregate`, `manifest_query`, `domain_report_query`, `divisional_query`, `cross_varga_dignity_query`, `classical_text_search`, `classical_attribution_lookup` — nine of the 30 wired tools have neither a manifest binding the planner can see nor an R-rule the model can recall.

The downstream failure mode is silent. `platform/src/app/api/chat/consume/route.ts` line 665 looks up the planner-selected tool name via `getTool(toolName)`; if no match, the line returns `null` without emitting a trace event, a warning, or an error. Selection of an unwired or misspelled tool produces no diagnostic signal anywhere.

### §C.5 — Sidecar tool gap

The Python sidecar at `platform/python-sidecar/main.py` exposes computation endpoints that have no TypeScript retrieval-tool wrapper, so they cannot be reached by the planner:

- `/api/compute/muhurat` — the Muhurat Finder shipped in Phase 4C is reachable only from the `/panchang` UI surface. A user asking "what's an auspicious muhurta for starting my business next week?" through chat will not get a tool-grounded answer.
- `/jaimini_drishti` — Jaimini aspect computation. Wired in the sidecar; the planner cannot select it.
- `/v7_additions` — Forensic v7.0 additions endpoint. Wired in the sidecar; not exposed.

### §C.6 — Schema and documentation thinness

Even for the three tools the planner can see, schema fidelity is uneven. `lel_query` carries the only rich `query_schema` with full JSON Schema parameters; the M9 pair carry minimal schemas (`signal_id`, `domain`); zero tools document their output shape in the manifest. Examples are documented only in `PLANNER_PROMPT_v2_0.md` few-shots (§4, 31 examples covering ≈10 of the 30 tools), never in the tool's own description or schema. Gating constraints ("use only when X is true," "do not call alongside Y") live only in PLANNER_PROMPT R-rules — they are not machine-readable and they are not surfaced through the manifest path at all.

### §C.7 — Asset → tool coverage matrix

Coverage verdict per major asset folder:

```
folder                       files  manifest  tool exposure                           verdict
01_FACTS_LAYER                  16      7    FORENSIC,LEL,SADE_SATI well-covered      OK
00_NAK                          26      0    none                                     GAP (intent unclear)
025_HOLISTIC_SYNTHESIS           9      6    CGM,MSR strong; UCN/CDLM/RM thin         AMBER
035_DISCOVERY_LAYER             93     18    4 register tools surface key data        OK (intentional expose_to_chat:false)
03_DERIVATIONS                   1      1    query_panchanga                          OK
03_DOMAIN_REPORTS               29     20    domain_report_query                      OK
04_REMEDIAL_CODEX                4      —    remedial_codex_query                     OK
05_TEMPORAL_ENGINES             19      0    4 tools but no asset bindings            AMBER (gap 3)
06_LEARNING_LAYER               77     29    none                                     GAP
08_CLASSICAL_CROSS_REFERENCE    12     29    classical_text_search + attribution      OK
09_MULTI_SCHOOL_TRIANGULATION   25     25    M9 pair                                  OK
```

The two GAPs at the asset-folder level are `00_NAK/` (intent unclear; native decision needed in §I) and `06_LEARNING_LAYER/` (no retrieval tool exposes learning-layer assets; this is structurally correct for an active substrate but should be revisited when LL.7+ outputs are stable and may add interpretive value to user queries).

UCN, CDLM, and RM at L2.5 are AMBER because they have only `vector_search` (a generic secondary tool) reaching them; no dedicated tool surfaces the structural content of the Union of Confluences Network, the Cross-Domain Linkage Matrix, or the Resonance Map. The asset metadata in `manifest_overrides.yaml` lists them as `preferred_for: [interpretive, cross_domain, holistic]` — but the planner has no tool through which to act on that preference.

### §C.8 — Intra-signal conflict inventory

At the time of this audit, **one confirmed Class A (intra-signal) conflict** exists in the signal corpus: MSR.377 (Varshaphala Muntha, 2026 solar year), where the signal's `claim` text disagrees with the FORENSIC citation it cites. This conflict is tracked as **DIS.013** in `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md`. The ICR stream (§N) is the systematic workflow for detecting, classifying, and resolving this class of defect.

Based on Class A prevalence patterns in comparable signal corpora (≈1–2% of signals), an estimated **3–5 additional Class A conflicts** are expected to surface when the automated detector (ICR-S3) performs a full scan of all 514 MSR signals. These are speculative until ICR-S3 completes; only the MSR.377 / DIS.013 conflict is confirmed.

### §C.9 — Inter-signal conflict inventory

**Two confirmed Class B (inter-signal) conflicts** are known at the time of this audit, both surfaced via the `contradiction_register` retrieval tool. Neither has been promoted to a DISAGREEMENT_REGISTER entry yet; ICR-S3's Class B extension will formalize them.

Based on Class B prevalence patterns (independent signal pairs making incompatible claims about the same chart entity), an estimated **8–12 additional Class B conflicts** are expected across the full 514-signal corpus once systematic pairwise cross-checking is implemented. These are advisory estimates; ICR-S3 will produce the authoritative count.

Class C conflicts (MSR signal claim contradicts a FORENSIC field directly) have not been systematically checked. That check is within ICR-S3's scope.

### §C.10 — Propagation chain model

When an MSR signal is corrected via a propose-patch artifact (§N.3), downstream artifacts that reference that signal must also be reviewed and potentially updated. The canonical propagation chain is:

```
Tier 1 (mandatory): the MSR signal itself — corrected claim text + updated fingerprint
Tier 2 (mandatory): UCN edges that reference the signal_id — any Confluence node whose
          `signal_refs[]` includes the corrected signal; the edge weight or confluence
          assessment may change
Tier 3 (advisory):  CDLM links that reference affected UCN edge IDs — cross-domain
          linkages built on the now-corrected confluence
Tier 4 (advisory):  RM resonance paths that reference affected CDLM link IDs — resonance
          amplification factors that may shift
Tier 5 (advisory):  synthesis cache entries and prediction_ledger rows grounded on the
          corrected signal — any prediction whose evidence chain included the signal
```

The `propose_patch` YAML artifact emitted by ICR-S4 must include a `propagation_chain` list enumerating every affected node at Tier 1 and Tier 2 (mandatory), and may enumerate Tiers 3–5 as advisory items. A patch whose `propagation_chain` omits Tier 2 UCN references fails the `munta_propose_patch_emitted` gate. Tiers 3–5 are surfaced in the Conflict panel (PERF-S5) for native review but do not block atomic apply. The ICR-S4 acceptance gate verifies that the MSR.377 patch lists all UCN edges whose `signal_refs` includes `MSR.377`.

## §D — Performance tab findings

### §D.1 — Current surface

The Performance tab lives at `/performance` (super-admin only) and renders `platform/src/components/performance/PerformanceClient.tsx`. Layout guard: `platform/src/app/(super-admin)/performance/layout.tsx` lines 15–18. Sub-route: `/performance/eval-runs` for golden-set eval-run listings. It is reachable from the portal rail (`platform/src/components/shared/AppShellRail.tsx` lines 56–64) with the `ChartColumn` icon.

The page shows four KPI tiles, each with a 24-bucket sparkline, plus a Query Log table:

```
Pipeline correctness  → plan accuracy (recall) | precision | citation rate | n | unjudged
Answer quality        → B.10 compliance | B.11 compliance | Brier | calibration n
Performance health    → p95 latency | p50 latency | synthesis pass rate | n
Retrieval health      → hit rate | n
Query Log             → timestamp | source | class | plan_type | plan_accuracy |
                        validator_verdict | B.10 | B.11 | citations | latency | status
```

Two modals attach to the log: `JudgeRunModal` (LLM-judge backfill for `unjudged` rows) and `TracePanelLauncher` (opens the per-query trace at `/admin/trace/[query_id]`). The header carries a refresh button, a time-window picker (preset/custom), and a source filter (`all | consume | eval`).

### §D.2 — Wiring (current vs. stale)

Every metric is read from a single denormalized table, `performance_queries`, populated by `platform/src/lib/performance/ingestion.ts` on each consume/eval run. Cross-references touch only `audit_log` and `prediction_ledger` (for Brier).

The Performance tab has **zero overlap with the Observatory schema**. Observatory reads `llm_usage_events`; Performance reads `performance_queries`. The two surfaces share no metrics, no time index, and no join keys at the API layer. This is a defensible separation (cost vs. correctness), but it means an operator must mentally stitch the two views together to diagnose any cross-cutting issue.

Stale signals in the current wiring:

1. **`compliance.ts` lines 26–35** hardcodes the L2.5 tool set used to compute B.11 (Whole-Chart-Read) compliance: `msr_sql, query_msr_aggregate, pattern_register, resonance_register, cluster_atlas, contradiction_register, temporal, cgm_graph_walk`. This is 8 of the 30 wired tools. Every L2.5-relevant tool added after this set — `query_signal_state` (R28), `query_kp_ruling_planets` (R29), `query_varshaphala` (R30), `cross_varga_dignity_query`, `convergence_score_lookup` — does not count toward B.11 satisfaction. The result: queries that correctly route through newer L2.5 tools are silently flagged as B.11 violations, artificially inflating the violation rate on the dashboard.

2. **`ingestion.ts` line 24**: `RETRIEVAL_TOP_SCORE_TOOLS = new Set(['vector_search'])`. Only `vector_search`'s top-1 score is captured into `performance_queries.retrieval_score_top1`. The other 29 tools' confidence/significance signals are dropped. Retrieval health is effectively measured against one tool out of thirty.

3. **No `compose_bundle` stage telemetry**. Phase 11B (2026-05-11) renamed the legacy CONTEXT_ASSEMBLY stage to `compose_bundle` and preserved it in production `query_trace_steps` (per CLAUDE.md §F). `ingestion.ts` lines 58–63 compute total latency as `planner + Σ(tool.latency_ms) + synthesis` — bundle composition is invisible. Any latency regression in `compose_bundle` is masked.

4. **`citation_rate` is regex-derived from synthesis text** (`compliance.ts` lines 108–119). It scans for `(→ ...)` markers with prefix matching against layer labels. This is not driven by actual citation records (which exist as enriched `enrichCitations` data after R7/R8 work). Any synthesis-style change in `markdownContent` or footnote handling silently changes the rate.

5. **Silent latency fallback to zero**. `ingestion.ts` line 63 wraps the synthesis latency in `Number.isFinite(synthesisLatencyMs) ? synthesisLatencyMs : 0`. Missing synthesis timestamps fall back to zero rather than null, understating total latency without any diagnostic flag.

6. **"Live" indicator is dishonest**. The header says "live"; the client polls every 45 s (`PerformanceClient.tsx` line 65). A super-admin watching an ongoing query will not see it appear.

7. **Source filter is binary** (`consume | eval | all`). No filter by query class, by user, by tool, by client (post-M5 multi-native scope).

### §D.3 — What the Performance tab does not show

The page is outcome-shaped: it answers "are queries correct? are they fast? are they compliant?" It does not answer the operator's questions about the operating system itself. Specifically, it does not show:

- **Asset inventory and health**. No list of L1/L1.5/L2.5/L3 assets, no per-asset row count, no per-asset last-rebuilt timestamp, no detection of empty/stale tables. A super-admin cannot answer "is `multi_school_signal_coverage` populated for the current native?" or "when was `ephemeris_daily` last regenerated?" from this page.

- **Per-retrieval-tool utilization**. No calls-per-day, no error rate, no p95 latency per tool, no zero-call detection. The page collapses all 30 tools into a single `retrieval_hit` boolean. A tool that has not fired in seven days (e.g., `query_varshaphala` rarely selected) appears identical to one that fires on every query.

- **Planner routing audit**. `plan_tools_selected` is stored as JSON in `ingestion.ts` line 133 but is shown only as a comma-joined blob in the trace panel. No view exposes "planner asked for tool X but the registry returned null" (the silent-drop failure mode at `route.ts:665`). The mismatch is unobservable.

- **Coverage scoreboard**. No surface reports "% of registered assets reached by at least one tool," "% of wired tools registered on the manifest," "% of wired tools the planner can actually select." The four-gate chain documented in §C is invisible to operators.

- **Freshness/staleness signals**. No per-asset or per-tool last-touched indicator, no manifest-fingerprint drift warning (the `MANIFEST_AUDIT_v1_0.md` scheduled audit ran today and found 12 mismatches; the dashboard does not surface them).

- **Cache hit-rate per retrieval tool**. The Observatory tracks LLM prompt-cache effectiveness; retrieval-tool result caches (where they exist) are not surfaced anywhere.

- **Schema-mismatch and empty-result diagnostics**. Tools that return empty result sets, schema errors, or partial responses are folded into "no hit." The pipeline likely emits these as trace events but no aggregator picks them up.

- **Per-conversation drill-down**. Source filter is `consume | eval`; there is no breakdown by conversation, user, client, or session.

### §D.4 — Adjacent surfaces

The Observatory at `/observatory` (super-admin) carries cost/usage telemetry across nine sub-pages: Overview, Events, Reconciliation, Budgets, Cost Arc, Cache, Pricing Diff, Anomalies, Cost-per-Quality, Replay. None of these covers asset inventory, retrieval-tool utilization, or planner-registry coverage. The Cockpit at `/cockpit/*` covers operator-ops control (plan/health/sessions/registry/interventions) but is action-oriented, not diagnostic. The Audit view at `/admin/trace/[query_id]` shows per-query traces and is the right drill-down target for any aggregate the new Performance tab would surface.

The OBSERVATORY_REDESIGN_PLAN_v1_0 (CURRENT) covers OBS-S1 (data wiring), OBS-S2 (design system), OBS-S3 (UX) — all focused on the Observatory and on LLM cost/usage. None of those three sessions covers the Performance tab or asset-side metrics. The redesign and this audit are complementary, not overlapping.

## §E — Defects classified

Forty-one defects, classified by impact on the audit goal (every asset planner-reachable; every metric meaningful). P0 means the gap directly hides the operating system from either the planner or the operator; P1 means the gap distorts a real measurement or limits routing; P2 means hygiene, naming, or staleness without immediate decision impact.

### §E.1 — P0 (six)

**P0.1 — Planner sees three tools out of thirty.** `manifest_compressor.ts` lines 95–113 produce a `<manifest>` block containing `lel_query`, `multi_school_signal_lookup`, `convergence_score_lookup` only. The other 27 wired tools are invisible through the manifest path. Routing rests entirely on PLANNER_PROMPT R-rule memorization plus few-shot mimicry. New tools added to `RETRIEVAL_TOOLS[]` are planner-blind until either an R-rule is added (a prompt-engineering change) or a manifest entry is added. The Phase-2 campaign documents this as "planner-blind RCS fix" but solves it at the prompt level, not at the manifest level.

**P0.2 — No manifest schema for asset → tool binding.** 162 of 163 `CAPABILITY_MANIFEST.json` entries declare no retrieval tool, no JSON Schema for tool input, no expected output shape, no `expose_to_planner` flag. The native's stated invariant ("every astrologically-valuable asset must be planner-reachable") has no machine-checkable representation in the manifest. There is no way to detect coverage drift, no CI gate that fails when a new asset lands without a tool, no equivalent of the fingerprint mismatch check (`MANIFEST_AUDIT_v1_0.md`) for the coverage chain.

**P0.3 — Silent unknown-tool drop at runtime.** `consume/route.ts` line 665 looks up the planner-selected tool by name; if no match, returns `null`. No trace event, no warning, no metric. Misspelled tool names, hallucinated tool names, and tools deprecated without R-rule cleanup all fail identically and invisibly.

**P0.4 — B.11 violation calculation uses stale L2.5 tool list.** `compliance.ts` lines 26–35 hardcodes 8 tool names; the dashboard's B.11 compliance metric does not credit the seven post-2026-05-04 L2.5 tools (`query_signal_state`, `query_kp_ruling_planets`, `query_varshaphala`, `cross_varga_dignity_query`, `convergence_score_lookup`, plus older `query_msr_aggregate` if used in L2.5 context, plus `temporal` for sade_sati-style scoring). The B.11 metric on the dashboard is wrong.

**P0.5 — Performance tab has no asset/tool/planner inventory.** The current four KPI tiles describe outcomes (recall, B.10, latency). They do not describe the system that produced those outcomes. An operator cannot answer "which assets exist," "which tools fire," "which routings the planner used" from this surface. The user's stated objective for the Performance tab is unmet at the structural level.

**P0.6 — Three sidecar computations are planner-unreachable.** `/api/compute/muhurat`, `/jaimini_drishti`, and `/v7_additions` are sidecar endpoints with no TypeScript retrieval-tool wrapper. The user-facing Muhurat Finder shipped in Phase 4C is unreachable from chat. The Jaimini drishti computation, which carries unique astrological signal not duplicated in Vedic graha drishti, is also unreachable.

### §E.2 — P1 (twelve)

**P1.1 — 14 of 30 retrieval tools carry no inline description.** They are pure functions. Even if `manifest_compressor.ts` were fixed to emit them, there would be no documentation for the planner to read.

**P1.2 — `PRIMARY_TOOL_NAMES` is a hardcoded 11-name allowlist.** Every new tool requires a code edit to this constant. The header comment at line 50 says "8 primary tools" — stale.

**P1.3 — `retrieval_tool` is an orphan field.** `PANCHANG_DAILY_v1_0` carries `retrieval_tool: query_panchanga` in the manifest. No reader code consumes that field; the rest of the registry uses `tool_name`. The Phase-4C wire-up added a field nothing reads.

**P1.4 — Description capped at 15 words.** `manifest_compressor.ts` lines 78–83 silently truncate `tool_description`/`description` to 15 words. Even the three planner-visible tools get heavily compressed docstrings.

**P1.5 — Only `vector_search` top-1 score captured.** `ingestion.ts` line 24 means retrieval-health metrics on the dashboard reflect one tool, not thirty.

**P1.6 — No `compose_bundle` stage telemetry.** Latency is invisible for the Phase-11B-renamed stage. The dashboard's `latency_total_ms` is structurally incomplete.

**P1.7 — Silent latency fallback to zero.** `ingestion.ts` line 63: `Number.isFinite(synthesisLatencyMs) ? synthesisLatencyMs : 0` masks dropped timestamps.

**P1.8 — Citation rate is a regex heuristic over synthesis text.** Not driven by enriched-citation records.

**P1.9 — Golden set is stale on every count.** `planner_golden_set.json` description says 82 entries; file has 86. `regression_baseline.json` description says 29 entries; file has 86. `available_tools` in the golden set lists 19 (yet a third inconsistent count). The eval surface measures against a moving target.

**P1.10 — No expose_to_planner flag in the manifest schema.** Several entries declare `expose_to_chat: false` (e.g., the four discovery-layer registers) but the four register-backing tools are nonetheless planner-callable. The two concepts — file-asset surfacing vs. tool surfacing — are conflated.

**P1.11 — UCN/CDLM/RM lack dedicated tools.** Only `vector_search` (a generic secondary tool, lines 1 of registry) reaches them. The L2.5 graph structure of UCN, the cross-domain linkages of CDLM, and the resonance map of RM are accessible only via embedding similarity, not via structural query.

**P1.12 — `ALL_21_RETRIEVAL_TOOLS` constant is misnamed.** Lists 30; name says 21. Load-bearing for callsite compatibility per its docstring; the rename is gated on a coordinated callsite sweep.

### §E.3 — P2 (twenty-three)

A list of hygiene findings: stale doc claims (the Phase-2 campaign doc says M9 27+28 are not wired; they are), inconsistent comments, `PRIMARY_TOOL_NAMES` header comment ("8 primary tools" vs. 11 listed), several manifest entries without `canonical_id` (22 of 163), 43 entries without `expose_to_chat`, the 12 fingerprint mismatches surfaced today by the scheduled audit (mostly expected drift on living files but one — `LL1_TWO_PASS_APPROVAL_v1_0` — warrants a targeted review per `MANIFEST_AUDIT_v1_0.md`), no description hierarchy in `manifest_overrides.yaml` for the 152 unannotated entries, no surface for `manifest_overrides.additional_entries` merge verification, no "live" indicator that reflects actual polling cadence, source filter is binary, no per-client breakdown, etc. None of these blocks the audit objective alone but each compounds the diagnostic blindness.

## §F — Architectural recommendations (long-term)

Three structural recommendations underpin the remediation in §G–§H. The native should accept or amend these before any session below opens, because they shape every brief.

### §F.1 — Make `CAPABILITY_MANIFEST.json` the single load-bearing source of truth for both supply and demand

Today the manifest carries 163 file-asset entries and 5 tool entries. The natural evolution is for every wired retrieval tool to have a first-class manifest entry alongside the assets it reads. The schema should grow these per-tool fields, all of which are missing today:

- `tool_name` (string, identifier)
- `tool_description` (string, planner-grade, no length cap at this layer)
- `query_schema` (JSON Schema for input)
- `output_schema` (JSON Schema for output — currently absent for every tool)
- `linked_data_asset_ids` (array — current field is singular; tools often touch multiple assets)
- `expose_to_planner` (boolean, explicit)
- `examples` (array of `{query, expected_plan_fragment}` — promotes few-shots from prompt to manifest)
- `gating_constraints` (array of structured "use when…" / "avoid when…" predicates — promotes R-rules where they apply to a single tool)
- `cost_weight`, `token_cost_hint`, `cache_class`

The 15-word description cap in `manifest_compressor.ts` would be lifted; the compressor would emit the full structured tool description but the *system prompt* would carry a compressed view for token budgeting. The planner would receive: full tool list with schemas (machine-readable, for plan validation) plus a token-budgeted summary (for routing).

### §F.2 — Replace `PRIMARY_TOOL_NAMES` with `expose_to_planner: true` declarative wiring

The hardcoded 11-name allowlist must die. Replace it with `manifest_compressor.ts` filtering on `entry.expose_to_planner === true` for every entry that has `tool_name`. Every wired retrieval tool gets a manifest entry; every entry with `expose_to_planner: true` reaches the planner. The hardcoded constant becomes a CI assertion ("at least N planner-visible tools, no fewer") rather than the gate itself.

### §F.3 — Promote routing rules from prompt to manifest

`PLANNER_PROMPT_v2_0.md` carries 32 numbered R-rules. Many of them are single-tool gating constraints ("when query class is X and query contains Y, include tool Z") that belong on the tool. Migrating these into `manifest_overrides.yaml` (or back into `CAPABILITY_MANIFEST.json` as `gating_constraints`) lets the planner reason about routing from data, not from prompt prose. The prompt remains authoritative for cross-tool composition rules (R-DISC, R-CDOM, R-FACT) and for the floor/asset_bundle logic (R16, R21–R26). This is a multi-session migration and is not P0; it is a long-term architectural goal that §G.6 begins.

## §G — Remediation plan: Capability coverage (seven sessions)

Each session is a single closed brief targeting Anti-Gravity (Claude Code) per the project's `CLAUDECODE_BRIEF` discipline. Each ships its own PR on the `analysis/backend-data-pipeline-perf-audit` branch (or a successor branch the native approves), per the Phase-2 campaign's branch policy. Sessions are loosely sequential: COV-S1 and COV-S2 can run in parallel; COV-S3 depends on both; COV-S4 onward is sequential.

### §G.1 — COV-S1: Manifest schema extension

**Goal:** Extend `CapabilityManifestEntry` and the build pipeline so every wired retrieval tool can carry a first-class entry with `tool_name`, `tool_description`, `query_schema`, `output_schema`, `linked_data_asset_ids[]`, `expose_to_planner`, `examples`, `gating_constraints`, `cost_weight`. Backwards-compatible (every new field optional); existing entries pass through unchanged.

**Files:** `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (schema fields added at next regeneration); `platform/src/lib/types/capability_manifest.ts` (TS types); the manifest builder script (likely `platform/scripts/governance/build_manifest.ts` — verify path at brief authoring); `00_ARCHITECTURE/manifest_overrides.yaml` (new field stubs).

**Acceptance:** TS types compile clean; manifest regenerates with new optional fields populated as null/empty for existing entries; `MANIFEST_AUDIT_v1_0.md` scheduled job continues to pass; no runtime behavior change yet (compressor still uses old gates).

### §G.2 — COV-S2: Per-tool manifest entries for all 30 wired retrieval tools

**Goal:** Author a manifest entry for each of the 30 tools in `RETRIEVAL_TOOLS[]`, including the 14 tools that currently lack any inline description. Each entry carries `tool_name`, `tool_description` (planner-grade prose, 50–150 words), `query_schema` (JSON Schema for input), `linked_data_asset_ids[]` (every asset the tool reads), `expose_to_planner: true`, and the existing `cost_weight`/`token_cost_hint`. `output_schema`, `examples`, `gating_constraints` may be deferred to COV-S6 (promotion from prompt).

**Files:** `00_ARCHITECTURE/manifest_overrides.yaml` (the right place — the manifest is generated, the overrides file is hand-edited). The override file's `additional_entries:` pattern already exists; this session adds 30 (or as many as are missing — six already exist) tool-shaped entries.

**Acceptance:** All 30 tools have a manifest entry. `MANIFEST_AUDIT_v1_0.md` regenerates with 30 `tool_name` entries (up from 5). `tsc` clean. Schema validator passes.

### §G.3 — COV-S3: Compressor cutover from PRIMARY_TOOL_NAMES to expose_to_planner

**Goal:** Replace `PRIMARY_TOOL_NAMES` filtering in `manifest_compressor.ts` with declarative `expose_to_planner === true` filtering. Drop the 15-word description cap and replace it with a configurable budget (default 60 words; cap enforced at total `<manifest>` block token budget level, not per-tool). The compressor becomes data-driven.

**Files:** `platform/src/lib/pipeline/manifest_compressor.ts` (algorithm), unit tests, and any planner integration tests under `platform/tests/eval/`.

**Acceptance:** Planner sees all 30 tools (or whatever subset is marked `expose_to_planner: true`); planner prompt token count stays within budget (currently the manifest block is tiny because it has 3 entries — adding 27 will require measurement). Existing golden-set planner runs still produce equivalent plans (regression test against `regression_baseline.json` after refreshing it). Unit tests for `compressManifest` updated.

### §G.4 — COV-S4: Sidecar tool wrappers for muhurat, jaimini_drishti, v7_additions

**Goal:** Author TypeScript retrieval-tool wrappers for the three orphaned sidecar endpoints. Pattern: mirror `query_panchanga.ts` (the closest precedent — also a sidecar-backed tool with rich docs). Each wrapper: thin fetch + parse + format + return `RetrievalToolResult`. Register in `RETRIEVAL_TOOLS[]`. Add corresponding manifest entry via COV-S2 pattern. Add `toolStepType` + `inferLayer` mappings in `consume/route.ts` per the Phase-2 campaign's hard rule §F.5.

**Files:** `platform/src/lib/retrieve/query_muhurat.ts`, `query_jaimini_drishti.ts`, `query_v7_additions.ts` (new); `retrieve/index.ts` registry; `trace/types.ts` (the misnamed `ALL_21_RETRIEVAL_TOOLS`); `consume/route.ts`; `manifest_overrides.yaml` (3 new entries); unit tests mirroring `lel_query.test.ts`.

**Acceptance:** 33 tools wired total. All planner-visible. Chat-side query "what's an auspicious muhurta for X" returns tool-grounded answer. Unit tests pass. SLA probe extended.

### §G.5 — COV-S5: Dedicated tools for UCN, CDLM, RM (structural query)

**Goal:** Author three dedicated retrieval tools that surface the structural content of the three L2.5 graphs (Union of Confluences Network, Cross-Domain Linkage Matrix, Resonance Map) — beyond what `vector_search` currently provides. Pattern: mirror `cgm_graph_walk.ts` (the closest precedent for graph-shaped L2.5 retrieval). Inputs: a structural seed (signal id, domain id, confluence id) plus a walk depth. Outputs: a structured slice of the graph.

**Files:** `query_ucn_walk.ts`, `query_cdlm_lookup.ts`, `query_rm_walk.ts` (new); registry; manifest entries; unit tests; PLANNER_PROMPT R-rule patch for routing (R-CDOM extension at minimum).

**Acceptance:** 36 tools wired total. Planner correctly routes interpretive cross-domain queries to the new tools when appropriate. Smoke test in `planner_golden_set.json` extended with 3+ entries that require UCN/CDLM/RM structural access.

### §G.6 — COV-S6: Promote planner R-rules to manifest gating constraints

**Goal:** Migrate single-tool R-rules from `PLANNER_PROMPT_v2_0.md` into `gating_constraints` on the corresponding manifest entries. The migration is incremental: each session pick a coherent rule cluster (e.g., R28/R29/R30 — the L1 substrate trio) and migrate. The R-rule remains in the prompt as documentation but is now also machine-readable.

**Files:** `manifest_overrides.yaml` (gating constraints added per tool); `PLANNER_PROMPT_v2_0.md` (R-rules amended to cite the manifest); `manifest_compressor.ts` (extended to emit gating constraints into the prompt's tool descriptions).

**Acceptance:** First migration cluster ships; planner behavior on golden set unchanged or improved; per-rule unit tests added. This is the entry point to a multi-session migration that may run for a quarter.

### §G.7 — COV-S7: CI coverage gate

**Goal:** Add a CI check that fails any PR landing a new `RETRIEVAL_TOOLS[]` entry without a corresponding manifest entry, and fails any PR adding a new asset folder without at least one tool binding declared. The check runs as part of `MANIFEST_AUDIT_v1_0.md`'s scheduled job and as a pre-merge gate. This is the long-term enforcement layer that prevents the gaps documented in §C from re-accreting.

**Files:** `platform/scripts/governance/` (new check); GitHub Actions workflow update; CI documentation.

**Acceptance:** Synthetic PR adding a tool without a manifest entry fails CI. Synthetic PR adding an asset folder with no reachability fails CI. The scheduled audit's verdict adds two new categories: `COVERAGE_GATE_MANIFEST` and `COVERAGE_GATE_ASSETS`.

### §G.8 — COV-S8: Discovery register version audit and smoke gate

**Goal:** Verify that the planner's tool discovery register reads the correct `interface_version` from `CAPABILITY_MANIFEST.json` after COV-S1's schema extension, and that adding new optional fields in COV-S1 does not accidentally trigger an `interface_version` bump. COV-S1 extends the manifest schema with new optional fields; by the project's versioning discipline, an additive backward-compatible change does not change `interface_version`. This session adds an explicit smoke test that reads the manifest through the same code path that `manifest_compressor.ts` uses at runtime (`manifest_reader.py` → `compressManifest()`) and asserts the returned `interface_version` matches the value declared in the manifest JSON. The test must catch any mismatch introduced by build-pipeline changes.

**Files:** `platform/scripts/governance/schema_validator.py` (add version-read assertion alongside the existing fingerprint checks); `platform/tests/governance/smoke_planner_register_tools.ts` (new — imports `compressManifest`, calls it with the live manifest file, and asserts `interface_version` matches the manifest-level field; also asserts the compressed block contains at least the three baseline tools from v1.0 — `lel_query`, `multi_school_signal_lookup`, `convergence_score_lookup`).

**Acceptance:** `smoke_planner_register_tools.ts` passes under `vitest run` without modification on any branch that does not explicitly bump `interface_version`. `manifest_reader.py` exits 0 after COV-S1's schema changes. No regression in the `schema_validator.py` exit code on the existing suite. The smoke test is added to the `vitest_changed` gate set so that any future manifest schema change must re-pass it.

### §G.9 — COV-S9: Tool-coverage metadata migration (Postgres tables)

**Goal:** Reflect the manifest tool-binding fields added in COV-S1 (`expose_to_planner`, `tool_name`, `query_schema`, `output_schema`, `linked_data_asset_ids`, `cost_weight`) in two new Postgres tables so the Performance tab (PERF-S2 / PERF-S3) can query coverage metrics live from the database rather than reading the JSON file at request time. The two tables are:

- **`capability_tool_registry`** — one row per wired retrieval tool. Columns: `tool_name` (PK, text), `expose_to_planner` (boolean), `description` (text), `query_schema` (jsonb), `output_schema` (jsonb), `cost_weight` (numeric), `linked_data_asset_ids` (text[]), `created_at` (timestamptz), `updated_at` (timestamptz).
- **`capability_asset_tool_bindings`** — many-to-many join between asset canonical_ids and tool_names. Columns: `asset_canonical_id` (text), `tool_name` (text), `binding_source` (text — `manifest | override | inferred`), `created_at` (timestamptz). Composite PK on `(asset_canonical_id, tool_name)`.

A seed script populates both tables from `CAPABILITY_MANIFEST.json` and `manifest_overrides.yaml` at migration time. The seed script is re-runnable (upsert semantics) and is the canonical way to update the tables when the manifest changes.

**Files:** `platform/supabase/migrations/<next_number>_capability_tool_registry.sql` (new migration; use the next available migration number after verifying the latest in `platform/supabase/migrations/`); `platform/scripts/governance/seed_tool_registry.ts` (new seed script that reads the manifest + overrides and upserts into both tables); `platform/src/lib/types/capability_tool_registry.ts` (new — TypeScript types matching the two tables, generated from the migration); unit tests for the seed script.

**Acceptance:** Migration dry-run (`supabase db diff --use-migra` or equivalent) exits 0. After apply, `capability_tool_registry` has ≥ 30 rows (one per wired tool after COV-S2). `capability_asset_tool_bindings` has ≥ 5 rows covering the five manifest entries that carry `tool_name` as of v1.0. No row-count regression on any existing table (`panchanga_daily`, `ephemeris_daily`, `performance_queries`, etc.). Seed script idempotent: running it twice produces the same table state.

### §G.10 — COV-S10: Sade Sati cycle table: migration and population

**Goal:** Create the `sade_sati_cycles` table and populate it for the native (Abhisek Mohanty). Sade Sati is the 7.5-year period when Saturn transits the natal Moon sign and the two adjacent signs (preceding and following), each transit approximately 2.5 years. The native's natal Moon sign must be confirmed from `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` at session open before any computation proceeds (do not assume; read the file). Computation draws from `ephemeris_daily` (Saturn longitude column), which is already populated with 657k+ rows from 1900–2100 by `bootstrap_ephemeris.py`.

The table schema: `id` (uuid PK), `native_id` (text, FK-style reference — use the canonical native identifier from FORENSIC), `start_date` (date), `end_date` (date), `phase` (text — `rising | peak | setting`), `moon_sign` (text — the natal Moon sign, constant for all rows for a given native), `saturn_sign` (text — the sign Saturn occupies during this phase), `severity_weight` (numeric — see note below), `computation_source` (text — `ephemeris_daily`), `created_at` (timestamptz).

Severity weight convention: `rising` = 0.7, `peak` = 1.0 (Saturn directly over natal Moon sign), `setting` = 0.7. These are conventional Jyotish weightings; the session must not invent alternative values without FORENSIC support.

The population script reads Saturn longitude from `ephemeris_daily`, groups consecutive days where Saturn occupies the same sign, and identifies runs that cover the natal Moon sign ± one sign. Each such run becomes a row with the appropriate `phase`. Rows must span at least 1984-01-01 to 2100-12-31 for the native.

**Files:** `platform/supabase/migrations/<next_number>_sade_sati_cycles.sql` (new migration, after COV-S9's migration number); a population script at `platform/scripts/data/populate_sade_sati.py` or `populate_sade_sati.ts`; unit/integration tests; `platform/src/lib/types/sade_sati_cycles.ts` (TypeScript types).

**Acceptance:** Migration dry-run exits 0. After apply and population, `sade_sati_cycles` has ≥ 3 rows for the native covering the 1984–2100 period (there should be approximately 8–9 complete Sade Sati cycles in a 116-year window). Each row carries all required columns with non-null values. The native's natal Moon sign in the rows matches the FORENSIC record read at session open. No row-count regression on any existing table. Population script is idempotent.

## §H — Remediation plan: Performance tab (four sessions)

The Performance tab is transformed in-place at `/performance` per the native's stated preference (existing surface, not a new one). The four sessions ship sequentially: PERF-S1 is the data-wiring prerequisite; PERF-S2 and PERF-S3 are UI; PERF-S4 is the final polish.

### §H.1 — PERF-S1: Wiring fixes and metric correctness

**Goal:** Resolve the six wiring defects in §D.2. Specifically: (a) replace the hardcoded 8-tool list in `compliance.ts` with a runtime query against `RETRIEVAL_TOOLS[]` filtered by `inferLayer === 'L2.5'`; (b) replace `RETRIEVAL_TOP_SCORE_TOOLS = new Set(['vector_search'])` with per-tool top-score capture (extending `performance_queries.retrieval_score_top1` to a JSON map of `tool_name → top_score`); (c) add `compose_bundle` stage latency to the ingestion path (`performance_queries.compose_bundle_latency_ms` new column + migration); (d) replace silent `null → 0` latency fallback with explicit null preservation and a `latency_complete` boolean; (e) replace the citation regex heuristic with a count of enriched-citation records from `query_trace_steps` post-R7 work; (f) honest "live" indicator that shows last-fetch timestamp.

**Files:** `platform/src/lib/performance/compliance.ts`, `ingestion.ts`, `kpi_aggregator.ts`; new migration for the column additions; `PerformanceClient.tsx` for the "live" indicator.

**Acceptance:** B.11 metric counts all 30 wired L2.5 tools (with `inferLayer === 'L2.5'`). Per-tool top-1 score captured. `compose_bundle` latency on the dashboard. Null latency surfaces a yellow badge instead of zero. Citation rate is record-driven. "Live" badge shows actual last-fetch time. All existing tests pass.

### §H.2 — PERF-S2: New section — Asset Catalog (with health badges)

**Goal:** Add a top-level page section that renders the full asset inventory grouped by layer, with per-asset health badges. This is the answer to "show me what assets are available in an interactive way."

**Sections:**
- **Asset list grouped by layer** (L1 / L1.5 / L2.5 / L3 / L5 / L6 / L8 / L9). Each row: canonical_id, path, version, status, fingerprint (truncated), last-touched timestamp, expose_to_chat flag, expose_to_planner flag, row count if backed by a Postgres table, bound retrieval tools (list).
- **Health badges**: green (CURRENT, fingerprint matches, table populated), yellow (LIVING, expected drift), red (SUPERSEDED, missing file, empty table, fingerprint mismatch unexpectedly), gray (DEAD_DATA or expose_to_chat:false).
- **Drilldown**: click an asset → side panel with full manifest entry, derivation ledger (if L2.5+), schema (if backed by table), and a "Show me the queries that touched this" link to a filtered Query Log.
- **Filter bar**: by layer, by status, by health, by reachability (reachable / unreachable / no tool).

**Data source:** `CAPABILITY_MANIFEST.json` (cached server-side; revalidated on `MANIFEST_AUDIT_v1_0.md` scheduled-job cadence) joined with `bundle_*` table row counts (via a thin server-side aggregator).

**Files:** `platform/src/components/performance/AssetCatalogSection.tsx` (new); aggregator `platform/src/lib/performance/asset_health.ts` (new); page composition in `PerformanceClient.tsx`.

**Acceptance:** Asset Catalog renders all manifest entries. Health badges accurate against `MANIFEST_AUDIT_v1_0.md` output. Drilldown panel functional. Filter bar responsive. Loads in under 500 ms.

### §H.3 — PERF-S3: New section — Retrieval Utilization & Planner Routing

**Goal:** Add two paired sections that answer "how well are these assets being leveraged" and "is the planner routing correctly?"

**Retrieval Utilization section:**
- A heatmap: rows = retrieval tools (all 30+, alphabetically), columns = time buckets (24 hourly, or 7 daily — user-toggleable). Cell color encodes call volume; cell label shows count. Zero-call tools are visually distinct (gray with a small "0").
- A side panel per tool: 30-day call count, error rate, p95 latency, average result size, top-1 score distribution histogram, "queries that selected me" link to filtered Query Log.
- A "Zero-call tools (7d)" callout listing every tool the planner has not selected in the last week. This is the diagnostic for orphaned tools.

**Planner Routing section:**
- A flow diagram per query class (factual, interpretive, predictive, holistic, remedial, planetary, discovery, cross_domain, cross_native): each shows the top-5 tool sets the planner emitted for that class in the last 7 days, with frequency. Visual: Sankey from class → tool combinations.
- A "Routing mismatches" panel: any case where the planner emitted a tool name not in `RETRIEVAL_TOOLS[]` (caught by extending `route.ts:665` to emit a trace event rather than silently returning null — this is a small PERF-S1 extension; native should approve at brief authoring time).
- A "Coverage scoreboard" at the top: four big numbers — total assets, % with retrieval tool, % tools with manifest entry, % tools the planner can select (P0.1's count, computed live).

**Data source:** `performance_queries.plan_tools_selected` JSON column (already populated by ingestion) aggregated by tool name + time bucket; `RETRIEVAL_TOOLS[]` for the registry side; `CAPABILITY_MANIFEST.json` compressed via `compressManifest()` for the planner-visible count.

**Files:** `RetrievalUtilizationSection.tsx` (new), `PlannerRoutingSection.tsx` (new), aggregators under `platform/src/lib/performance/`; small extension to `route.ts` if the native approves the unknown-tool trace event.

**Acceptance:** Heatmap renders 30+ tools by 24 hourly buckets. Zero-call callout populated correctly. Routing Sankey renders per class. Coverage scoreboard reads live from `compressManifest()`. Mismatch panel surfaces P0.3's silent-drop incidents (if the native approves the route.ts extension).

### §H.4 — PERF-S4: New section — Freshness, Diagnostics, Drilldowns

**Goal:** Close the remaining diagnostic gaps in §D.3: per-asset freshness, schema-mismatch and empty-result diagnostics, per-conversation drilldown.

**Sections:**
- **Freshness panel**: list of assets sorted by last-touched timestamp ascending. Flag any asset whose last-touched is older than its declared rebuild cadence (panchang: daily; ephemeris: yearly; MSR/CGM: per-session; LEL: per-event).
- **Diagnostics panel**: per-tool error rates and empty-result rates (from `query_trace_steps`), schema-mismatch counts (caught by Zod on tool outputs — requires a small instrumentation extension at the retrieval layer), and a "recent failures" list with stack trace links.
- **Per-conversation drilldown**: extend the Query Log source filter from `consume | eval | all` to `consume | eval | per-conversation | per-user | per-client` (post-M5 multi-native scope). Group toggle: by-query (current) or by-conversation.
- **Manifest fingerprint drift surface**: render the output of the latest `MANIFEST_AUDIT_v1_0.md` scheduled run directly on the page. Today this is invisible to operators.

**Data source:** `query_trace_steps` for diagnostics; manifest builder output for freshness/drift; conversation tables (added in R7/R8) for per-conversation grouping.

**Files:** `FreshnessSection.tsx`, `DiagnosticsSection.tsx`, extended Query Log component; aggregators for trace-step diagnostics.

**Acceptance:** Freshness panel surfaces stale assets. Per-tool error/empty rates visible. Manifest fingerprint drift surfaces on page load. Per-conversation drilldown navigable. All sections lazy-loaded for sub-second page load.

### §H.5 — PERF-S5: Performance tab Conflict panel (full)

**Goal:** Ship the full Conflict panel in the Performance tab. The panel exposes the ICR stream's propose-patch artifacts to the native for review and action. It is the primary interface through which the native confirms, rejects, or escalates every intra-signal conflict patch produced by ICR-S4. The stub section wired in ICR-S5 is expanded here into a complete, production-ready panel.

**Panel layout:**

- **Pending patches table** — one row per YAML file present in `00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/`. Columns: `conflict_id` (text), `class` (A / B / C badge), `signals_affected` (comma-joined signal IDs), `proposed_change` (expandable diff preview — collapsed by default, expand on row click), `propagation_chain_depth` (integer — count of tiers listed in the artifact's `propagation_chain`), `authored_by` (text), `authored_on` (date). Row actions: **Confirm**, **Reject**, **Escalate to L1 Review**. Empty state: "No pending conflicts" with a green checkmark badge.

- **History table** — one row per YAML in `RESOLVED/` and `REJECTED/` directories. Columns: `conflict_id`, `class`, `resolution` (`resolved | rejected`), `resolved_by` (operator identifier), `resolved_at` (timestamp). Paginated at 25 rows; oldest first.

- **Confirm action** — calls `POST /api/icr/confirm` (route authored in ICR-S5) with the patch file path and `action: confirm`. The API moves the YAML atomically from `PROPOSED/` to `RESOLVED/` (the atomic-apply logic is tested for rollback correctness in ICR-S5). On success: row disappears from Pending, appears in History with `resolved`.

- **Reject action** — a confirm dialog ("Reject this patch? Add a reason (optional):") then calls `POST /api/icr/confirm` with `action: reject`. API writes the YAML to `REJECTED/` with a `rejected_at` and optional `reject_reason` appended to the file. On success: row moves to History with `rejected`.

- **Escalate to L1 Review action** — moves the YAML to `L1_REVIEW/` and creates a new `DISAGREEMENT_REGISTER_v1_0.md` entry in the same atomic operation (DIS.N+1). A modal prompts for a short escalation note; the note is written into the DISAGREEMENT_REGISTER entry as `escalation_note`. On success: row disappears from Pending.

**Files:** `platform/src/components/performance/ConflictPanel.tsx` (new — full implementation, replacing the ICR-S5 stub); `platform/src/app/api/icr/confirm/route.ts` (extended from ICR-S5 to handle `action: reject` and `action: escalate`); integration into `PerformanceClient.tsx` as a new top-level section below the existing four KPI tiles; unit tests for the route; a `conflict_panel_smoke` test that mounts the panel with a synthetic PROPOSED/ artifact and verifies all three action paths render correctly.

**Data source:** `PROPOSED/`, `RESOLVED/`, `REJECTED/` directories read server-side via the `/api/icr/confirm` route's companion `GET /api/icr/patches` endpoint (new in this session). The endpoint returns the list of artifacts grouped by directory. All file I/O is server-side; the client receives JSON, not raw YAML.

**Acceptance:** ConflictPanel renders all YAML files in `PROPOSED/` with correct columns. Empty-state "No pending conflicts" renders when `PROPOSED/` is empty. Confirm action moves artifact atomically (rollback tested via ICR-S5's dry-run harness). Reject action writes to `REJECTED/` with optional reason. Escalate writes to `L1_REVIEW/` and creates a `DISAGREEMENT_REGISTER` entry. History table renders `RESOLVED/` + `REJECTED/` files. `conflict_panel_smoke` gate passes. Panel does not crash on an empty `PROPOSED/` directory.

## §I — Open native decisions

Three items require the native's call before any session below opens.

### §I.1 — `00_NAK/` exposure intent

The 26 nakshatra files in `00_NAK/` have zero manifest entries. The folder appears to carry design specs and prompt scaffolding (NAK = nakshatra) rather than queryable interpretive content. The native should confirm: (a) these are design assets and correctly not planner-reachable, or (b) some subset is interpretive content the planner should reach and needs manifest entries via COV-S2's pattern. If (b), the native flags which files.

### §I.2 — `06_LEARNING_LAYER/` exposure cadence

The Learning Layer is the live substrate for prediction ledgers, two-pass events, calibration, and pattern register. None of it is currently planner-reachable. As LL.7+ outputs stabilize, some learning-layer outputs may add interpretive value to user queries (e.g., calibrated confidence on a predicted dasha period). The native should specify a cadence: keep planner-blind until M6 close, or selectively expose specific learning-layer outputs starting at M5-C.

### §I.3 — Unknown-tool trace event vs. error

P0.3 (the silent unknown-tool drop at `route.ts:665`) can be fixed in three ways: (a) emit a trace event but keep returning null (low-risk, observable), (b) throw and 422 the request (high-discipline, immediately surfaces hallucinated tools), (c) attempt fuzzy match against `RETRIEVAL_TOOLS[]` and emit a corrective trace event with the mapped name (UX-friendly, hides the underlying problem). The native picks; PERF-S3's mismatch panel is most useful under (a).

## §J — Acceptance criteria summary

Every session in §G and §H ships its own brief with explicit acceptance criteria. The cross-cutting invariants every session must satisfy:

- `tsc --noEmit` clean.
- Existing tests pass; new tests added for the changed surface.
- Golden-set / regression-baseline run shows no regression (or, if expected to show change, the change is documented in the brief).
- `MANIFEST_AUDIT_v1_0.md` scheduled job continues to pass.
- The session's PR carries a one-paragraph "what this changes for the operator/planner" note.
- The session's close-checklist updates `SESSION_LOG.md` and (if a manifest or PLANNER_PROMPT change) propagates to the Gemini-side mirror per MP.1/MP.3 discipline.

## §K — Mirror obligations

This artifact is declared Claude-only per MP.6/MP.7 precedent — Gemini's L4 Discovery Layer scope does not bind to retrieval-tool or planner internals. `mirror_enforcer.py` emits `PASS_DECLARED_CLAUDE_ONLY` for this file. Downstream PLANNER_PROMPT amendments under §G.6 will require Gemini-side mirroring per MP.1; downstream `CAPABILITY_MANIFEST.json` extensions under §G.1 are within the L2.5-path subset mirrored by MP.5 and will be propagated at the next mirror cycle.

## §L — References

Source files cited in this audit, by section:

```
§A,§B,§C  00_ARCHITECTURE/CAPABILITY_MANIFEST.json
          00_ARCHITECTURE/manifest_overrides.yaml
          00_ARCHITECTURE/MANIFEST_AUDIT_v1_0.md
          00_ARCHITECTURE/ASSET_INVENTORY_REPORT_v1_0.md
          00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json
          00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md
          00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md
          platform/src/lib/retrieve/index.ts                    lines 86–116
          platform/src/lib/retrieve/types.ts                    line 92
          platform/src/lib/trace/types.ts                       lines 246–285
          platform/python-sidecar/main.py                       lines 37–54

§C.4      platform/src/lib/pipeline/manifest_compressor.ts      lines 50–125
          platform/src/lib/pipeline/manifest_planner.ts
          platform/src/lib/pipeline/pipeline_planner.ts         lines 146–268
          00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md                v2.3 §§3,4
          platform/src/app/api/chat/consume/route.ts            lines 456–464,665–666
          platform/tests/eval/planner_golden_set.json
          platform/tests/eval/fixtures/regression_baseline.json

§D        platform/src/app/(super-admin)/performance/page.tsx
          platform/src/app/(super-admin)/performance/layout.tsx lines 15–18
          platform/src/components/performance/PerformanceClient.tsx
          platform/src/components/shared/AppShellRail.tsx       lines 56–64
          platform/src/lib/performance/compliance.ts            lines 26–35,108–119
          platform/src/lib/performance/ingestion.ts             lines 24,58–63,70–81,126,133
          platform/src/lib/performance/kpi_aggregator.ts        lines 83–234

§E        all of the above, classified.

§G,§H     additionally: 00_ARCHITECTURE/OBSERVATORY_REDESIGN_PLAN_v1_0.md
                        (complementary, non-overlapping)
```

## §M — Changelog

- **v1.2 (2026-05-21)** — Promoted to v1.2 to match campaign queue `spec_version`. Added §G.8 (COV-S8: discovery register version smoke gate), §G.9 (COV-S9: tool-coverage metadata Postgres migration), §G.10 (COV-S10: Sade Sati cycle table migration and population). Added §C.8 (intra-signal conflict inventory), §C.9 (inter-signal conflict inventory), §C.10 (propagation chain model). Added §N (ICR: Intra-Signal Conflict Resolution stream) — §N.1 mission, §N.2 conflict taxonomy (Class A/B/C), §N.3 propose-patch protocol, §N.4 L1 truth index, §N.5 Muntha conflict DIS.013 narrative, §N.6 six-session ICR plan (ICR-S1 through ICR-S6). Added §H.5 (PERF-S5: Performance tab Conflict panel, full implementation). Total remediation sessions across all streams: 21 (COV-S1–S10, PERF-S1–S5, ICR-S1–S6).

- **v1.0 (2026-05-21)** — Initial audit + plan. Three parallel research streams executed against `main`. Forty-one defects identified (6 P0, 12 P1, 23 P2). Two parallel session streams proposed in §G (Capability, seven sessions) and §H (Performance, four sessions). Three open native decisions surfaced in §I.

## §N — ICR: Intra-Signal Conflict Resolution stream

### §N.1 — ICR mission

The M5 audit revealed that signal-layer artifacts (MSR, FORENSIC, UCN, CDLM) sometimes carry conflicting claims about the same astrological entity. The canonical example is **DIS.013**: MSR.377 (Muntha signal for Varshaphala 2026) contradicts the FORENSIC ground truth for the native's Varshaphala Muntha position — the signal's claim text and its cited FORENSIC source point to different Muntha placements.

Without a principled conflict-detection and resolution workflow, these contradictions silently produce inconsistent synthesis outputs: two signals that disagree can both be surfaced to the planner, both carry non-zero resonance weights, and the native receives a response that is internally incoherent without any diagnostic signal. This failure mode is invisible to the operator because neither the Performance tab nor the planner routing layer surfaces it.

The ICR stream builds the end-to-end workflow: **detect** conflicts via automated cross-checking against L1 facts → **classify** by severity → **propose a patch** artifact for native review → **native confirms or rejects** via the Performance tab Conflict panel (PERF-S5) → **atomic apply** moves the patch to RESOLVED/ → **CI gate** prevents future PRs from introducing new ungrounded signals. Six sessions (ICR-S1 through ICR-S6) close this workflow from schema scaffolding through production CI enforcement.

### §N.2 — Conflict taxonomy

Three conflict classes, ordered by detection difficulty and remediation impact:

**Class A — Intra-signal conflict.** A single MSR signal's `claim` text contradicts the specific FORENSIC or LEL fact it cites in its own `sources` block. Example: MSR.377 claims Muntha is in sign X; its `sources` entry cites `FORENSIC §7.4` which states Muntha is in sign Y. Detectable by automated cross-reference of `claim` text against the cited source field. Severity: high when the `claim` is load-bearing for synthesis; medium otherwise. **MSR.377 / DIS.013 is a confirmed Class A conflict.**

**Class B — Inter-signal conflict.** Two separate MSR signals make mutually incompatible claims about the same planet, house, nakshatra, or astrological construct in the same chart layer. Example: Signal A says Jupiter is exalted in Karka; Signal B says Jupiter is debilitated in Makara — these cannot both be true for the same native in the same chart context. Detectable by pairwise contradiction analysis across the `claim` corpus, seeded by `contradiction_register` entries. Severity: high when both signals appear in a synthesis bundle for the same query; medium when they appear in separate contexts.

**Class C — L1 conflict.** An MSR signal's claim directly contradicts a field in the FORENSIC ground truth without the FORENSIC citation appearing in the signal's own `sources` block — meaning the signal simply got it wrong independently of its cited sources. Example: MSR says Sun is in Capricorn; FORENSIC says Sun is in Aquarius. This is the highest severity class: the signal is not merely self-inconsistent but contradicts the canonical L1 record. **Always native-review-required** regardless of synthesis context. Every Class C conflict produces a DISAGREEMENT_REGISTER entry at detection time, not at propose-patch time.

### §N.3 — Propose-patch protocol

The propose-patch protocol is the interface between automated conflict detection and human decision. It ensures no automated process modifies the signal corpus without the native's explicit confirmation.

**Step 1 — Emit:** When ICR-S3 or ICR-S4 detects and classifies a conflict, the emitter writes a YAML artifact to `00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/` with the following structure:

```yaml
conflict_id: DIS.013           # matching DISAGREEMENT_REGISTER entry
class: A                       # A | B | C
signal_ids_affected:
  - MSR.377
proposed_change:               # diff-format string showing exact text change
  before: "<current claim text>"
  after: "<corrected claim text>"
propagation_chain:             # per §C.10 model
  tier_1:
    - MSR.377
  tier_2:
    - UCN_EDGE_<id>            # all UCN edges whose signal_refs include MSR.377
  tier_3_advisory:
    - CDLM_LINK_<id>
  tier_4_advisory: []
  tier_5_advisory: []
confidence: 0.92               # detector confidence that this patch is correct
authored_by: ICR-S4-detector
authored_on: 2026-05-21
status: PROPOSED
```

**Step 2 — Await:** The artifact is NOT applied automatically. It waits in `PROPOSED/` until the native acts via the Conflict panel (PERF-S5). The session log records a `propose_patch_pending` halt, which is not a failure — it is the designed checkpoint.

**Step 3 — Confirm:** The native clicks Confirm in the Conflict panel. The `/api/icr/confirm` route moves the YAML from `PROPOSED/` to `RESOLVED/` in a filesystem transaction. A `resolved_at` timestamp and `resolved_by` field are appended. The corrected claim is applied to the MSR signal in a second atomic step within the same transaction; if either step fails, the entire transaction rolls back.

**Step 4 — Reject:** The native clicks Reject. The YAML moves from `PROPOSED/` to `REJECTED/` with an optional `reject_reason`. The MSR signal is untouched.

**Step 5 — Escalate:** The native clicks Escalate to L1 Review. The YAML moves from `PROPOSED/` to `L1_REVIEW/`. A new DISAGREEMENT_REGISTER entry is created (if one does not already exist for this conflict_id) with the escalation note. The signal remains untouched. L1 review means the conflict requires manual inspection of the underlying FORENSIC data before a resolution can be proposed.

### §N.4 — L1 truth index

The **L1 truth index** is the fraction of MSR signals that carry at least one grounding fact from the FORENSIC ground truth or the Life Event Log (LEL):

```
L1_truth_index = (signals with ≥1 FORENSIC or LEL citation in sources[]) / (total signals)
```

At 514 total signals (MSR v3.1), the **target is ≥ 95%** — meaning at most 25 signals may lack any grounding fact. Signals that are purely interpretive (e.g., classical yoga assessments grounded in FORENSIC planetary positions transitively) count toward the numerator only if their `sources` block explicitly lists the FORENSIC field or LEL entry that anchors the interpretation.

The L1 truth index score is computed by ICR-S2 and emitted as a report at `06_LEARNING_LAYER/L1_TRUTH_INDEX_REPORT_v1_0.md`. If the score is below 95%, the `l1_truth_index_coverage_gte_95pct` gate fails and the ICR stream halts; the native must approve a remediation plan for the below-threshold signals before ICR-S3 opens.

The index is also re-computed by the ICR-S6 CI gate on every PR that touches `MSR_v3_0.md`, and by the scheduled weekly scan (ICR-S6's job).

### §N.5 — Muntha conflict (DIS.013)

MSR.377 is the Varshaphala Muntha signal for the native's 2026 solar year. The Muntha (sometimes called the annual progressed ascendant) advances one sign per year from the natal ascendant in Varshaphala practice; the exact sign depends on the native's birth details and the computation method (mean vs. true Muntha). MSR.377's `claim` block states a specific sign and house; its `sources` block cites `FORENSIC §7.4` (Varshaphala subsection). An automated cross-check at audit time revealed that the claim text and the cited FORENSIC field disagree on the Muntha's sign placement.

This conflict is recorded as **DIS.013** in `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md`. At the time of the audit, DIS.013 was opened as a Class A conflict. It is the smoke-test case for the ICR stream: ICR-S3 must detect it, ICR-S4 must emit a patch for it, and native confirmation is required before ICR-S5 can proceed. If the detector fails to surface DIS.013, the `intra_signal_munta_detected` gate fails and the stream halts.

The patch ICR-S4 proposes for MSR.377 must carry a full propagation chain per §C.10: Tier 1 (MSR.377 claim correction), Tier 2 (all UCN edges whose `signal_refs` list includes `MSR.377`), and advisory Tiers 3–5. The `munta_propose_patch_emitted` gate verifies the propagation chain structure before halting for native review.

### §N.6 — ICR session plan (six sessions)

The ICR stream is a third parallel remediation stream running alongside the Capability (§G) and Performance (§H) streams. ICR-S1 and COV-S1 can open simultaneously; ICR-S2 through ICR-S5 run sequentially; ICR-S6 is the final CI-hardening session.

#### §N.6 ICR-S1 — Schema + detector scaffolding

**Goal:** Author the conflict-detection data model, directory structure, and detector scaffolding. Establish the TypeScript types for conflict records and propose-patch artifacts. Implement the YAML schema validator for artifacts in `PROPOSED/`. Verify that the `00_ARCHITECTURE/CONFLICT_PATCHES/` directory structure (PROPOSED/, RESOLVED/, REJECTED/, L1_REVIEW/) is already on disk (scaffolded in an earlier session); if any subdirectory is missing, create it. No detector logic ships in this session — only types, interfaces, and the schema validator.

**Files:** `platform/src/lib/icr/types.ts` (new — `ConflictRecord`, `ProposePathArtifact`, `ConflictClass`, `PatchStatus` types); `platform/src/lib/icr/detector.ts` (new — `ConflictDetector` class with interface defined but `detect()` method returning an empty array; placeholder for ICR-S3 implementation); `platform/scripts/governance/schema_validator_icr.py` (new — reads every YAML in `PROPOSED/` and validates against the propose-patch JSON Schema defined in §N.3; exits 0 on empty directory, exits non-zero on schema violation, exits 0 on all-valid artifacts).

**Acceptance:** `tsc --noEmit` clean with new types in place. `schema_validate` (`schema_validator_icr.py`) exits 0 on an empty `PROPOSED/` directory. `schema_validate` exits non-zero on a synthetically malformed YAML (test in unit test; do not leave malformed YAML in PROPOSED/ after test). `CONFLICT_PATCHES/` subdirectory structure confirmed present on disk.

#### §N.6 ICR-S2 — L1 truth index computation

**Goal:** Implement the L1 truth index scorer. For each of the 514 MSR signals in `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`, determine whether the signal's `sources` block contains at least one citation to a FORENSIC field or LEL entry. A citation counts if it references any of: `FORENSIC §<section>`, `FORENSIC_ASTROLOGICAL_DATA_v8_0`, `LIFE_EVENT_LOG`, `LEL`, or a canonical LEL event ID. Emit a coverage report listing: total signals, grounded signals, ungrounded signals (with signal IDs and claim text), and the index score as a fraction and percentage.

**Files:** `platform/scripts/governance/l1_truth_index.ts` (new — reads `MSR_v3_0.md` via a markdown parser, extracts each signal's `sources` block, scores against the grounding criteria, outputs JSON + human-readable summary); a vitest unit test with a synthetic 10-signal fixture (5 grounded, 5 not) that verifies the scorer produces 50% on the fixture; output report written to `06_LEARNING_LAYER/L1_TRUTH_INDEX_REPORT_v1_0.md` (new artifact, frontmatter-bearing, version 1.0).

**Acceptance:** Scorer runs without error on the full MSR v3.1 corpus. Coverage report written to `06_LEARNING_LAYER/L1_TRUTH_INDEX_REPORT_v1_0.md`. If score ≥ 95%: `l1_truth_index_coverage_gte_95pct` gate passes; ICR-S3 may open. If score < 95%: gate fails; the report lists all below-threshold signal IDs; ICR stream halts for native remediation decision before ICR-S3 opens.

#### §N.6 ICR-S3 — Intra-signal conflict detector (Muntha smoke test)

**Goal:** Implement the Class A conflict detector in `platform/src/lib/icr/detector.ts`. The detector reads every MSR signal, extracts the `claim` and `sources` fields, fetches the cited FORENSIC or LEL fields (via the manifest or direct file read), and checks for textual contradictions using a structured comparison (not LLM-based — deterministic field lookup). At minimum, the detector must recognize when a signal's claim text asserts a sign placement that differs from the cited FORENSIC field's value. The primary smoke test is MSR.377 (DIS.013, Muntha conflict): the detector must emit a `ConflictRecord` for this signal with `class: A` and `signal_ids_affected: [MSR.377]`.

**Files:** `platform/src/lib/icr/detector.ts` (implement `detect()` method); `platform/src/lib/icr/forensic_reader.ts` (new — thin reader that extracts specific FORENSIC field values by section reference, used by the detector); a vitest unit test with a synthetic MSR fragment that contains a known mismatch (verifies the detector emits a conflict); a governance script `platform/scripts/governance/run_icr_detector.ts` that runs the detector against the live corpus and writes output JSON to `06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json`.

**Acceptance:** Detector exits with ≥ 1 conflict detected. `intra_signal_munta_detected` gate: the output JSON contains a `ConflictRecord` where `signal_ids_affected` includes `MSR.377` and `class === 'A'`. Detector output serialized to `06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json` for ICR-S4 consumption. Unit test passes on synthetic fixture. `tsc --noEmit` clean.

#### §N.6 ICR-S4 — Propose-patch emitter (Muntha)

**Goal:** For each `ConflictRecord` in the ICR-S3 detector output, compute the full propose-patch artifact and write it to `PROPOSED/`. For MSR.377 specifically: the patch proposes a specific text correction to the Muntha claim, with `before` and `after` strings derived from the discrepancy the detector found. The patch must carry a complete `propagation_chain` per §C.10: Tier 1 (MSR.377), Tier 2 (all UCN edges whose `signal_refs` includes `MSR.377`). Tiers 3–5 advisory. The patch file is named `DIS.013_MSR.377_proposed.yaml`. This session ends with a **NATIVE_REVIEW_REQUIRED** halt — no auto-apply.

**Files:** `platform/src/lib/icr/propose_patch.ts` (new — reads detector output JSON, queries UCN edges for each affected signal, constructs the `ProposePathArtifact`, validates against the schema from ICR-S1, writes YAML to `PROPOSED/`); `platform/src/lib/icr/ucn_edge_reader.ts` (new — reads `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` to extract edges referencing a given signal_id); YAML artifact written to `00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/DIS.013_MSR.377_proposed.yaml`.

**Acceptance:** At least one YAML file present in `PROPOSED/` after the session runs. `munta_propose_patch_emitted` gate: `DIS.013_MSR.377_proposed.yaml` exists in `PROPOSED/`, passes `schema_validator_icr.py`, and contains a `propagation_chain.tier_2` list that is non-empty (at least one UCN edge referenced). The propagation chain matches the §C.10 model (all tiers present in the YAML, advisory tiers may be empty lists). Session halt recorded as `propose_patch_pending` in `CONDUCTOR_HALT_LOG.md` — this is a designed checkpoint, not a failure. `NATIVE_REVIEW_REQUIRED_ON_PROPOSE_PATCH` halt flag set. `tsc --noEmit` clean.

#### §N.6 ICR-S5 — Confirmation UI + atomic apply

**Goal:** Build the native confirmation workflow. Two surfaces: (a) API route that handles confirm/reject/escalate actions; (b) a stub UI section in PerformanceClient that will be expanded to the full Conflict panel in PERF-S5. The session's primary deliverable is the API layer and its atomic-apply guarantees.

**API:** `platform/src/app/api/icr/confirm/route.ts` — a `POST` handler accepting `{ patch_file: string, action: 'confirm' | 'reject' | 'escalate', reason?: string }`. For `confirm`: read YAML from `PROPOSED/`, apply the text correction to the MSR signal file (a filesystem write), then move the YAML to `RESOLVED/`, all in a transaction with rollback if any step fails. For `reject`: move YAML to `REJECTED/` with appended `reject_reason`. For `escalate`: move to `L1_REVIEW/`, create a DISAGREEMENT_REGISTER stub entry. Companion `GET /api/icr/patches` handler returning `{ proposed: [...], resolved: [...], rejected: [...] }` for the UI.

**UI stub:** `platform/src/components/performance/ConflictPanel.tsx` — a minimal stub rendering a "Conflict (N pending)" heading and a placeholder "Full panel coming in PERF-S5" note. Mounted in `PerformanceClient.tsx` as a new section below the existing KPIs.

**Atomic-apply dry-run test:** A vitest integration test that calls the `confirm` handler with a synthetic PROPOSED/ artifact, simulates a filesystem failure mid-way through the two-step transaction (write MSR correction → move YAML), and verifies the YAML has not moved to RESOLVED/ and the MSR file is unchanged after the simulated failure.

**Files:** `platform/src/app/api/icr/confirm/route.ts`; `platform/src/components/performance/ConflictPanel.tsx` (stub); `PerformanceClient.tsx` (mount new section); `platform/tests/icr/atomic_apply.test.ts` (new).

**Acceptance:** `atomic_apply_dry_run` gate: simulated mid-apply failure leaves both PROPOSED/ and MSR signal unchanged (full rollback). `confirmation_ui_smoke`: ConflictPanel stub renders without error in a mounted component test. API route validates the patch file path is within `PROPOSED/` (path traversal prevention). `tsc --noEmit` clean.

#### §N.6 ICR-S6 — CI gate + scheduled scan

**Goal:** Add enforcement infrastructure that prevents future conflicts from accumulating silently. Two mechanisms:

1. **Pre-merge CI gate:** A GitHub Actions check that fires on any PR touching `MSR_v3_0.md`. The check runs `l1_truth_index.ts` on the PR's version of the file and fails if the score drops below 95%. It also runs a structural validator that checks every new signal added in the PR has a non-empty `sources` block with at least one FORENSIC or LEL citation (not necessarily a fully resolved cross-check — just structural completeness). A synthetic test PR that adds a citation-free signal must fail this check.

2. **Scheduled weekly scan:** A GitHub Actions workflow that runs on Sunday 02:00 UTC. It executes `run_icr_detector.ts` against main and, if any new ConflictRecords appear beyond what is already in `PROPOSED/`, `RESOLVED/`, or `REJECTED/`, writes new YAML artifacts to `PROPOSED/` and sends a `CONDUCTOR_HALT_LOG.md` notification. The scan is idempotent: running it twice on the same corpus produces the same set of artifacts with no duplicates.

**Files:** `platform/scripts/governance/icr_pr_gate.ts` (new — CI check script); `.github/workflows/icr_weekly_scan.yml` (new — scheduled workflow); `.github/workflows/ci.yml` or equivalent (updated to call `icr_pr_gate.ts` on MSR-touching PRs); unit tests for the gate script using a synthetic MSR fragment.

**Acceptance:** `synthetic_pr_conflict_gate_fails` gate: a test invocation of `icr_pr_gate.ts` with a synthetic MSR fragment containing a citation-free signal exits non-zero. `scheduled_job_smoke` gate: a dry-run invocation of the weekly scan script (with `--dry-run` flag, no actual PROPOSED/ writes) exits 0 and prints the list of conflicts it would emit. `tsc --noEmit` clean. All existing CI checks remain green after workflow update.

---

*End of CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md. CURRENT; living document until §G.1 ships and the audit can re-baseline against post-COV-S1 schema state. Successor v1.1 will land at first remediation-session close to mark progress and amend any decisions the native made under §I.*
