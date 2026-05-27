---
artifact: PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md
canonical_id: PLATFORM_MODERNIZATION_MASTER_PLAN
document: MARSYS-JIS Platform Modernization & Refactoring — The Total Plan
version: 2.1
status: DRAFT (umbrella program plan — reconciled against Claude Code audit MODERNIZATION_AUDIT_REPORT_v1_0 + Gemini v1; pending native approval; modifies nothing canonical)
reconciliation: see §15 — Audit Reconciliation Ledger
date: 2026-05-27
authored_by: Claude (Cowork session) — extends v1.0 with verified code recon (3 sub-agents) + the four dimensions the native requested
supersedes: PLATFORM_MODERNIZATION_MASTER_PLAN_v1_0.md (absorbs its five-track reconciliation spine; adds taxonomy, GCP maximization, gap-to-build, elimination, verified findings)
constituent_plans:
  spine:            00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v1_0.md
  data_engine:      [00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md, 00_ARCHITECTURE/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md, 00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md]
  tooling:          [00_ARCHITECTURE/BRIEFS/TOOL_PORTFOLIO_PLAN_v1_4.md, 00_ARCHITECTURE/INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md, 00_ARCHITECTURE/PANEL_MODE_TOOL_SPEC_v1_0.md]
  platform_portal:  [00_ARCHITECTURE/PLATFORM_REBUILD_ARCHITECTURE_v1_0.md, 00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.md]
  hygiene:          00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md
  governing_findings: [00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md, 00_ARCHITECTURE/PROVENANCE_TIERING_DECISION_v1_0.md]
companion_diagrams: [00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.svg]
approval_gate: native sign-off; run as a declared macro-phase with version bumps + mirror discipline + red-team at close (CLAUDE.md §L, §M)
expose_to_chat: false
---

# Platform Modernization & Refactoring — The Total Plan (v2.0)

## §0 — Thesis

One governed macro-phase modernizes the whole instrument along five tracks at once: a **deterministic,
JH-equivalent compute engine** builds every per-chart asset narrative-free; **multi-tenancy** (one
`chart_id` key, owner≠subject, one authorization brain) and **multi-guest RBAC** become foundational;
the **dual-channel tooling** is unified behind one contract and *de-judged* (query-time scoring removed);
the **portal** gains role-gated nav, a Command Center runtime control plane, and two isolated query
pipelines; and **interpretation moves to serve time** where a model panel + judge reason over the
deterministic substrate. v2.0 adds the four cross-cutting disciplines v1.0 did not: a **standardized
naming taxonomy**, **GCP maximization**, a **gap-to-build list**, and a **clean-system elimination list**
— all grounded in verified code recon. The store schema is *extended additively*, builds run *strangler /
parallel*, and nothing is a big-bang.

## §1 — What v2.0 adds over v1.0 (the delta)

v1.0 is the reconciliation spine (five tracks, sequencing waves, gates, cutover, risk register, open
decisions) — **kept and referenced, not restated**. v2.0 adds:

1. **§3 Naming & Nomenclature Standardization** — a single cross-platform taxonomy + rename map.
2. **§4 GCP Maximization** — current service map + prioritized improvement program.
3. **§5 Gaps to Build** — work no constituent plan owns.
4. **§6 Elimination List** — the clean-system deletions, code-verified.
5. **Verified corrections** folded throughout (see §2.1).

## §2 — Unifying architecture (carried from v1.0)

The five-track model and the single coherent picture stand as in v1.0 §2–§3 (INPUT → `chart_id` →
engine → JSONL source-of-truth → additively-extended chart-keyed stores → unified de-judged retrieval →
serve-time panel+judge; Command Center governs source + query availability). The layered module view +
colour-coded current→target diagram is `PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.svg`. **Determinism seam:**
everything through the L2.5 skeleton + computed coefficients is deterministic; only meaning/valence/
narrative/pick at serve time is non-deterministic.

### §2.1 — Verified corrections to the plan family (from this session's recon)
- **`TOOL_PORTFOLIO_PLAN_v1_4` lives at `00_ARCHITECTURE/BRIEFS/`**, not `00_ARCHITECTURE/` — v1.0's
  `constituent_plans` path is wrong; fixed here. (Path-governance item, §3.7.)
- **L2 is already archived** (`99_ARCHIVE/02_ANALYTICAL_LAYER/`, Phase 14F) — "drop L2" is *done*; only
  the L1+L1.5 fold + layer-vocabulary canonicalization remain (§3.6).
- **The "Deep / Study / Brief" depth selector IS the tier picker** — `platform/src/components/consume/
  TierPicker.tsx` maps those labels onto `super_admin`/`acharya_reviewer`/`client`. Removing the depth
  selector and excising tiers are the **same act** (§6-C/E).
- **De-judgment is confirmed in code** — `platform/src/lib/retrieve/msr_sql.ts` lines 20/24/33/44
  (`DEFAULT_CONFIDENCE_FLOOR`, `FINANCE_WEALTH_CONFIDENCE_FLOOR`, `PANCHA_MP_CLIQUE`,
  `LL1_PRODUCTION_WEIGHTS`). Track 2's de-judgment phase is real and load-bearing.
- **B.11 citation-gate asymmetry** — the legacy single-pass path has `validateCitationsForStream`
  (`consume/route.ts:1374`); the live adapter/agentic path does **not**. Hard gate: port the gate to the
  adapter path **before** deleting the legacy path (§6-G, §7).

## §3 — Naming & Nomenclature Standardization

The platform carries three product names and several keyed-concept spellings. The goal is **one name per
concept**, enforced by CI, with expensive renames (GCP project) explicitly excluded.

### §3.1 — Three product names → three defined scopes (don't collapse, *define*)
| Name | Canonical scope | Action |
|---|---|---|
| **MARSYS-JIS** | the *system / codebase / architecture* identity (docs, governance) | keep as the doc/system name |
| **Madhav** | the *user-facing brand* + the *GCP project* (`madhav-astrology`) | keep; do NOT rename the GCP project (cost) |
| **amjis-** | the *deployable-service* namespace (`amjis-web/sidecar/mcp`) | **standardize**: rename `marsys-pipeline` → **`amjis-builder`** |
Rule: infra = `amjis-`, brand/project = Madhav, system docs = MARSYS-JIS. No fourth name introduced.

### §3.2 — Tenant + identity keys (the highest-value normalization)
| Concept | Canonical | Deprecate |
|---|---|---|
| Chart / subject tenant key | **`chart_id uuid`** (FK → `charts.id`) everywhere | `chart_id text` (`'abhisek_mohanty_primary'`), `native_id varchar/text`, `chart_id` literals |
| Chart owner (the guest) | **`owner_id text`** (Firebase UID → `profiles.id`) | `client_id`-as-owner overload |
| Logged-in user | **`principal_id`** (= Firebase UID); table concept = *principal* | — |
| Chart subject label | **`subject_name`** on `charts` (data, not an account) | per-chart Firebase user (§6-H) |
Migration normalizes migrations 008/009/022/023/024/025/031/033/058/071/110 onto `chart_id uuid`.
> **Audit correction (v2.1, §15.1-C4):** there are **two** live native defaults — `'abhisek_mohanty_primary'`
> (text, 4 files) and `'362f9f17-…'` (uuid, 2 files) — plus a `DEFAULT_CHART_ID` constant. This is a
> **strangler** migration (add a `chart_text_alias` ↔ `chart_id uuid` mapping; reads→writes→drop), **not** a
> column-type alter, and it must map both values.

### §3.3 — Tool names (one canonical name per engine, both channels)
Collapse the portal↔MCP splits to the unified-contract `canonical_name` (TOOL_PORTFOLIO Phase 7). Confirmed splits to retire:
`chart_facts_query`↔`query_chart_facts`, `query_varshaphala`↔`query_varshphal`,
`divisional_query`↔`query_divisional_chart`, `cgm_graph_walk`↔`get_cgm_subgraph`,
`classical_text_search_tool`↔`read_classical_text`, `multi_school_signal_lookup_tool`↔`multi_school_bundle_tool`;
duplicate surfaces `msr_sql`+`query_signals` and the `*_balam`+`*_for_native` pairs. **Rule:** the MCP
external name is the canonical name; the portal imports it; aliases deleted (no permanent aliases).

### §3.4 — Feature flags
Convention: **`MARSYS_FLAG_<DOMAIN>_<FEATURE>`**, boolean flags suffixed `_ENABLED`. Retire release-round
prefixes (`R9_/R10_/R11_`) into domain names once a round ships. **One flag source:** `configService`
reads `runtime_config` (Command Center) with the env var as bootstrap default — eliminate the second
`getFlag` key set that has no `MARSYS_FLAG_` mirror (e.g. `PANEL_MODE_ENABLED`, `CITATION_GATE_OVERRIDE`,
`VALIDATOR_FAILURE_HALT`). Client flags stay `NEXT_PUBLIC_MARSYS_FLAG_*` (build-baked — known constraint).

### §3.5 — Env vars
One Google prefix: **`GOOGLE_CLOUD_*`** for GCP resource/config; collapse the `GCP_*` / `GOOGLE_*` /
`GOOGLE_CLOUD_*` trio. DB on **`DB_*`** (retire the `DATABASE_URL` dual). Provider keys `<PROVIDER>_API_KEY`.
Consolidate the triplicated chart-id test vars (`INTEGRATION_CHART_ID`/`MARSYS_MCP_CHART_ID`/`SMOKE_CHART_ID`)
to `MARSYS_CHART_ID_<CONTEXT>`. GCS buckets `marsys-<purpose>` (one scheme).

### §3.6 — Canonical layer model (reconcile docs ↔ dirs ↔ manifest)
Today the layer vocabulary differs across CLAUDE.md (L1–L4 + halves), the dir tree (00/00/01/025/03/03/035/
…/99/99 — duplicate + half-numbered + missing 02/07), and `CAPABILITY_MANIFEST.json` (L1–L9). Canonical set:

| Layer | Meaning | Status |
|---|---|---|
| **L0** | Classical corpus (T0, shared, build-once) | rename/cluster scattered classical dirs |
| **L1** | Deterministic facts (engine-direct + derivations folded; T1) | L1+L1.5 **fold** |
| **L2** | — | **retired** (archived Phase 14F) |
| **L2.5** | Holistic synthesis skeleton + computed coefficients (MSR/CDLM/CGM/RM/UCN-digest) | rebuild deterministic |
| **L3** | Registers (pattern/resonance/cluster/contradiction) | keep |
| **L4** | Discovery layer | keep |
| **L5** | Timeline | keep |
| **L6** | Learning / calibration | keep |
Action: make the manifest `L#` the single source for layer labels; re-number the dir tree to match (fix
duplicate `00_/03_/99_`, half-numbers `025/035`); update CLAUDE.md §I to the canonical set.

### §3.7 — Routes, paths & governance
- `consume` → **`consult`** (UI/route/code, alias during cutover).
- Merge the duplicate **`/api/panchang` + `/api/panchanga`** trees into one (`/api/panchang`).
- Fix the doc-path drift (`TOOL_PORTFOLIO_PLAN` under `BRIEFS/`).
- **Naming-governance CI gate (NEW):** a lint that fails on (a) a new tenant key other than `chart_id uuid`,
  (b) a tool name not in the unified contract, (c) a flag off-convention, (d) a Google env prefix outside
  `GOOGLE_CLOUD_*`. The `CAPABILITY_MANIFEST` + unified contract are the name SSOT; this gate stops drift
  from re-accreting. (Builds on the existing `drift_detector.py`/`schema_validator.py`.)

## §4 — GCP Maximization (project `madhav-astrology`, `asia-south1`)

### §4.1 — Current map (verified)
Cloud Run: `amjis-web` (Next.js), `amjis-sidecar` (Python/Swiss-Ephemeris, cpu2/1Gi/min1), `amjis-mcp`
(512Mi/min1/**--allow-unauthenticated**), + Cloud Run **Job** `marsys-build-pipeline-job` (the build DAG —
**no in-app trigger**, run manually). CI: GitHub Actions via **Workload Identity Federation** (no JSON key)
— **plus** Cloud Build configs (dual path → drift risk). Cloud SQL: `amjis-postgres`, **`db-g1-small`**
(dev tier). GCS: chat-attachments, chart-documents, `madhav-marsys-sources`, `madhav-marsys-build-artifacts`,
`marsys-jis-build-state`. Vertex AI: `text-multilingual-embedding-002` (per-text REST). Secret Manager
(mixed naming). Firebase Auth (login). BigQuery (narrow — observatory reconciliation). **Absent:** Cloud
Tasks, Pub/Sub, Memorystore, CDN, Cloud Armor, Eventarc, Workflows; Cloud Scheduler only in comments.

### §4.2 — Improvement program (prioritized; ties to the tracks)
1. **Build orchestration (Track 3):** `amjis-web` enqueues a **Cloud Task / Pub-Sub** on Build → executes
   the Cloud Run **Job** → progress rows the cockpit already polls. Optionally **Workflows + Eventarc** for
   per-stage gated DAG (staging→live swaps as explicit steps). Removes manual `gcloud`, enables concurrent
   multi-tenant builds.
2. **Cloud SQL upgrade:** off `db-g1-small` → dedicated-core + **HA/read-replica**; **partition** high-volume
   tables (`chart_facts`, `l25_*`, `query_trace_steps`, messages) by `chart_id`/time; verify PITR. (Track 1/3.)
3. **Memorystore (Redis):** replace process-local 60s caches + survive `min-instances` recycles; cache
   retrieval bundles / planner results / embeddings → cut DB load + LLM spend.
4. **Edge:** external HTTPS LB + **Cloud CDN** for `_next/static` + chart docs; **Cloud Armor** WAF/rate-limit;
   put `amjis-mcp` behind IAM/LB (currently public).
5. **Least-privilege SAs:** per-service runtime SAs (web/sidecar/mcp/builder) scoped to only their SQL/bucket/
   Vertex/secret needs.
6. **Secret + registry hygiene:** normalize secret names, pin/rotate versions (not `:latest`); **remove
   hardcoded DB passwords** from dev scripts (security); migrate MCP off **legacy GCR** → Artifact Registry;
   add image cleanup policies.
7. **Consolidate the deploy path:** one of GitHub Actions *or* Cloud Build as authoritative (recommend GH
   Actions WIF) to kill drift.
8. **Cloud Scheduler as IaC:** codify the MV-refresh + stream-reaper jobs (today comment-only) so cadence is
   auditable; verify they run.
9. **Observability:** Cloud Trace across web→sidecar→mcp; Monitoring dashboards + budget alerts + SLOs;
   batch Vertex embeddings; confirm `VERTEX_AI_LOCATION` is set in prod.
10. **Cost review:** `min-instances=1 × 3` and live `ANTHROPIC_*` despite the documented cost-ban — deliberate decisions, not defaults.

## §5 — Gaps to Build (no constituent plan fully owns these)
1. **Tenant-context propagation library** — a single `QueryContext{principal, chart_id}` threaded through
   pipelines, retrieval, gateway, MCP (avoids re-deriving auth/tenant per call).
2. **Command Center control plane** — North-Star §8 specs it; no constituent *builds* it. `gate_registry` +
   `runtime_config` + `configService` extension + the five gate classes incl. **data-source controls + LEL
   build-exclusion/serve-time boundary**.
3. **B.11 citation gate on the adapter path** — the asymmetry (§2.1); TOOL_PORTFOLIO Phase 1 hotfix.
4. **Build trigger wiring** — web → Cloud Task → Job (§4.2-1); the Job exists but is unreachable from the app.
5. **Intake determinism** — geocoding + historical-timezone resolution pinned at intake + recorded in
   provenance (multi-tenant birth places/eras; today trivially IST-only).
6. **Naming-governance CI** (§3.7) — enforce the taxonomy so it can't re-fragment.
7. **Observability/SLOs** (§4.2-9) — currently only LLM-cost reconciliation exists.
8. **Learning loop wiring** — instrument prediction-logging now (uncalibrated at n=1) so the computed-salience
   formula can later calibrate (v1.0 Track 5; build the seam early).

## §6 — Elimination List (the clean system; all code-verified)
| # | Category | What | Evidence |
|---|---|---|---|
| A | Query-time judgment | `DEFAULT_CONFIDENCE_FLOOR`, `FINANCE_WEALTH_CONFIDENCE_FLOOR`, `PANCHA_MP_CLIQUE`, `LL1_PRODUCTION_WEIGHTS` (4 lines) **× 2 channels** — portal `msr_sql.ts` + MCP `platform-mcp/src/tools/query_signals.ts:72,73`. (`query_varshphal.ts:87` is a hard-403 **tier gate** → handled under §6-C / G2, not here.) | `msr_sql.ts:20/24/33/44` |
| B | Dead/orphaned | legacy synthesis trio (`orchestrator.ts`/`single_model_strategy.ts`/`panel_strategy.ts`), `/api/mcp/execute/route.ts`, `callPlatform()/callPlatformPlan()` (`client.ts:145/165`) | TARGET_ARCH DEL-004/5/6; verified |
| C | Tier / disclosure subsystem | `lib/disclosure/`, `X-MCP-Audience-Tier` (`client.ts:109/142/248/326`), `mcp_api_keys.audience_tier` (mig 070/117), `tier_catalog.ts`, hard-403 health gates, `DisclosureTierBadge.tsx`, `public_redacted.md` | REALITY_REPORT §9 |
| D | Dual-channel dup | `MCP_TO_RETRIEVAL_TOOL` aliases + pass-throughs (`primitives_registry.ts:96`), `SURGICAL_TOOLS` 32 dups (`:46`), inline name-bridge objects (`retrieve/index.ts:151-212`), duplicated budget tables (`route.ts` `tokensFor`/`tokensForAdapter`) | REALITY_REPORT §3D/4/6/7 |
| E | Deprecated UI | **`TierPicker.tsx`** (= the Deep/Study/Brief selector — goes with tier excision), `CONSUME_UI_V2_ENABLED` dead branch (`consume/page.tsx:123`) | verified |
| F | Layer model | L2 already archived — only the L1+L1.5 fold + dir-renumber remain | `99_ARCHIVE/02_ANALYTICAL_LAYER/` |
| G | Legacy pipeline | Classic single-pass path (`consume/route.ts` else @ ~1201, `synthesisRequest` 863-907, import :82) — **delete only after porting B.11 gate to adapter path** | verified; §2.1 |
| H | Per-chart Firebase user | `adminAuth.createUser` (`api/clients/route.ts:51`) + `client_id=firebaseUser.uid` (:57) — remove on owner/subject split | verified |
| I | Stale tests / symbols | `tool_descriptions.test.ts:91` (asserts 22 vs 57), `PRIMARY_TOOL_NAMES`, `@deprecated resolver.ts:68`, `assembleTraceLegacy`/`fetchTraceLegacy` | TARGET_ARCH DEL-007/8/9 |
Note: `retrieval_capability_spec.ts` claimed dead but **does not exist** as a source file (only a test) — drop from the delete list.

## §7 — Sequencing spine & hard gates (extends v1.0 §4)

**Hard gates (ordered):** (1) **JH parity gate** — nothing above L1 builds until the engine reproduces the
**pinned Jagannatha Hora oracle** (a specific JH version + ayanamsha, captured once as the golden fixture;
JH is the sole formula authority and not a runtime dependency). FORENSIC v8.0 remains a reconciliation, not
the oracle, resolving the circularity where FORENSIC defers to JH. *(Native decision 2026-05-27, §15.4-1.)*; (2) **multi-tenant authz live before tier excision**; (3) **contract unification before
de-judgment**; (4) **data plane `chart_id`-keyed before `NATIVE_CHART_ID` fallback removed**; (5) **NEW —
B.11 gate ported to adapter path before legacy pipeline deletion**; (6) **NEW G5b (audit) — adapter
`onFinish` parity (persistence + predictions + observatory), proven by golden-transcript test, before
deleting the legacy pipeline** (else telemetry/persistence silently drop).

**Waves (parallel-safe unless a gate intervenes):**
- **Wave 0 — Foundations (immediate, parallel-safe):** tooling hygiene (ghosts, dups, stale tests, null
  `query_schema`) + **B.11 adapter-path hotfix** + **naming-taxonomy refactor pass** (pure renames behind the
  new CI gate — tenant key, services, flags, env, routes; §3) + GCP deploy-path consolidation + secret/DB-password
  remediation. **Split (audit, v2.1):** Wave **0a** = pure renames behind the CI gate; Wave **0b** = B.11
  adapter hotfix + secret/DB-password remediation + the single atomic mirror-discipline-retirement PR —
  behaviour-altering work kept out of the rename batch. No dependency on the engine.
- **Wave 1 — The engine gate:** PyJHora engine + adapter + JH parity gate (Track 1).
- **Wave 2 — Parallel:** (a) deterministic L1→L2.5 build into the additively-extended schema; (b) contract
  unification + `chart_id` in the contract (Track 2); (c) charts registry + owner/subject + `authorizeChartAccess`
  + role rename (Track 3); (d) Command Center + data-source/LEL controls scaffold (gap §5.2).
- **Wave 3 — Sequenced:** de-judgment (after contract unification); gateway + control-model-B + pipeline
  isolation; per-chart cutover (after build validates, behind a Command Center gate); portal Consult/nav;
  tier excision (after authz live); legacy-pipeline delete (after B.11 ported).
- **Wave 4 — GCP scale + close:** build-trigger wiring + Cloud SQL upgrade/partition + Memorystore + CDN/Armor
  + observability; eval re-baseline (multi-chart aware, once); learning-loop wiring; red-team + macro-phase seal.

## §8 — Risk register (extends v1.0 §7)
v1.0 R1–R8 stand. Added:
- **R9 — Naming-migration blast radius:** the tenant-key + tool-name renames touch many surfaces; mitigate
  with the CI gate + one atomic rename batch per surface-class + worktrees.
- **R10 — Security debt:** hardcoded DB passwords in dev scripts; `amjis-mcp` public; live Anthropic vs cost-ban.
  Mitigate in Wave 0 (secret hygiene, IAM/LB on MCP, explicit Anthropic decision).
- **R11 — Deploy-path drift:** GitHub Actions + Cloud Build both present. Mitigate by consolidating (Wave 0).
- **R12 — GCP cost step-up:** SQL upgrade + Memorystore + CDN + min-instances raise spend; budget-gate per item.

## §9 — Consolidated open decisions (v1.0 §8 + new)
v1.0's 8 stand (ayanamsha parity, coefficient child-table shape, hybrid-tool chart_id rule, write/ops authz,
pipeline-isolation timing, per-asset deterministic add-ons, cutover granularity, macro-phase number). Added:
9. **Product-prefix policy** — confirm §3.1 (amjis-=infra, Madhav=brand/project, MARSYS-JIS=system).
10. **Layer-vocabulary canonicalization** — adopt the §3.6 set + dir renumber, or keep current irregular dirs?
11. **GCP investment level** — how far in Wave 4 (SQL tier, HA, Memorystore, CDN, Armor) given current scale.
12. **Build trigger mechanism** — Cloud Tasks vs Pub/Sub vs Workflows for the Job.
13. **Deploy path** — GitHub Actions WIF as the sole authoritative path?
14. ~~Data cleanse mechanism~~ — **RESOLVED 2026-05-27: parallel-build + validated cutover + freeze-old-as-archive.** (§12)
15. ~~Existing-governance posture~~ — **RESOLVED 2026-05-27: LEAN TRANSFORM.** (§11)
16. ~~Gemini / multi-agent mirror discipline~~ — **RESOLVED 2026-05-27: RETIRE** (Gemini inactive). (§11.1)
17. **MCP client-expectations source** — locate the prior conversation's requirements + reconcile against §14's first-principles design. (OPEN)

## §10 — How to iterate this plan (the native's process)
This is v1 of the total plan, built for the **Cowork ⇄ Claude Code ⇄ other-LLM** iteration loop:
- **Claude Code pass:** validate every cited path/line against HEAD; cost each rename + elimination; confirm
  the gaps; return a findings report. (The §2.1 corrections + §6 citations are the seed checklist.)
- **Other-LLM pass:** stress the architecture (determinism seam, salience-as-computed-column, strangler
  cutover, GCP choices) for blind spots.
- **Cowork finalize:** fold both into v2.1, declare the macro-phase, then emit per-track/per-wave
  CLAUDECODE_BRIEF units. No implementation until the native approves + affected canonical artifacts are
  version-bumped (CLAUDE.md §L).

## §11 — Governance Transformation (Track 0 — governs the whole program)

The program runs under **one** governance that absorbs and transforms the accreted governance, tuned to
guarantee a **reproducible** (deterministic) outcome. "Deterministic outcome" = the end state is
objectively verifiable and re-derivable from inputs + versions; every wave is gated by automated,
reproducible checks, not subjective sign-off; no silent changes. **Posture (confirmed 2026-05-27):
LEAN TRANSFORM** — keep the load-bearing gates, streamline the heavy session-open reads, prune accreted
ceremony; bias toward "don't let governance complicate things."

### §11.1 — Existing-governance review (KEEP / TRANSFORM / RETIRE)
| Surface | Disposition | Why |
|---|---|---|
| Versioning + changelog (B.8); drift/schema/mirror enforcers; CAPABILITY_MANIFEST | **KEEP + extend** | the determinism backbone; extend manifest to the unified tool contract + naming SSOT (§3.7) |
| Derivation-ledger (B.3); no-fabricated-computation (B.10); B.11 holistic-read | **KEEP** | load-bearing correctness invariants; B.10 is *why* the deterministic engine exists |
| Session-close checklist; CURRENT_STATE pointer | **KEEP (lightened)** | progress integrity; trim ceremony |
| Macro-phase model (M1–M10); red-team cadence | **TRANSFORM** | the modernization runs as ONE declared macro-phase with per-wave red-team |
| Mandatory §C session-open reads (12 items) | **TRANSFORM / streamline** | too heavy; replace with a single program-state pointer + this plan |
| Mirror discipline (Claude/Gemini, MP.1–MP.8, `.geminirules`, `project_state.md`, `mirror_enforcer`) | **RETIRE (confirmed 2026-05-27)** | Gemini collaboration no longer active; remove mirror enforcers + `.geminirules` + `project_state.md` so they stop complicating every change. Drop `DIS.class.mirror_desync` from the disagreement protocol. |
| STEP_LEDGER | **already RETIRED** | historical only |
| ONGOING_HYGIENE_POLICIES; DISAGREEMENT_REGISTER; NATIVE_DIRECTIVES | **PRUNE to essentials** | keep the rules that gate; drop ceremony |
| Conductor (autonomous session orchestrator) | **KEEP, scoped** | useful for executing per-wave briefs; distinct from the build DAG (no LLM in the build path) |

### §11.2 — Determinism guarantee model (how the program stays reproducible)
Each wave closes only on **objective, re-runnable gates**: (a) JH parity gate; (b) schema + unified-contract
validation; (c) **golden-transcript tests** for every behaviour-preserving refactor (pipeline isolation,
de-judgment, renames — output identical pre/post); (d) **content-addressed provenance** (engine_version +
ayanamsha + inputs hash) so any chart asset is re-derivable; (e) per-asset build verification; (f)
**naming-governance CI** (§3.7); (g) drift/schema/mirror clean. SSOT = manifest + unified contract,
CI-enforced. Nothing merges without its gate; no manual gate where an automated one is possible.

### §11.3 — Program wrapper
Declare a macro-phase (open decision §9 item 8); version-bump every touched canonical artifact at each wave
close; red-team at each wave close + at program close; this plan + a single PROGRAM_STATE pointer replace
the heavy session-open read list for the duration.

## §12 — Data architecture: asset taxonomy & cleanse-and-rebuild

**Reconciliation of the native's model:** feeding essentials (datetime · lat · lon · location) assigns a
`chart_id` and regenerates the deterministic profile; the outcome is that the old contaminated data is gone
from the live system. **Refinement:** achieve this by *parallel-build + validated cutover + freeze-old-as-
archive*, never an in-place destructive wipe (§6 R1). For a new client there is no existing data — clean
build. For the native — parallel build, validate (JH parity + diff-vs-old), cut over, freeze old as rollback.

**Four asset classes (the build DAG must respect the distinction):**
| Class | Examples | Build behaviour |
|---|---|---|
| **A — Shared / chart-independent** | L0 classical corpus, ephemeris, eclipses, retrogrades | built once; never per-chart; never cleansed per build |
| **B — Per-chart natal** | L1 facts; L2.5 MSR/CDLM/CGM/RM/UCN-digest; structural facts (shadbala, ashtakavarga, KP sublords, aspects, dispositors) | regenerated deterministically from birth inputs — **this is "the rebuild"** |
| **C — Per-chart date-parameterized derivations** | transits/gochara, varshphal/annual, dashas, personalized panchang, muhurta, sade sati | derive from the B natal base + a date; **the "other derived assets" to investigate** — DAG must enumerate + include them |
| **D — Empirical / held-out** | **LEL (Life Event Log)** | **never engine-built, never in build/churn, serve-time-only; persists independently of the rebuild** |

**Rebuild flow:** essentials → `chart_id` → engine builds **B** (parallel, validated) → **C** derives from
B → cut over (native: replace live, freeze old) → **A** untouched → **D** untouched. The investigation
deliverable for Track 1: a complete enumeration of class **C** so nothing downstream is missed by the DAG.

## §13 — MCP from the LLM-client perspective

**Design principle:** structure the surface around the *client's reasoning workflow + token/latency
economics*, not our internal engine layout. Client-centric acceptance criteria (sharpens Track 2 / Tool
Portfolio):
- **Small, prompt-cache-stable resident core + gateway** (`search_tools`/`invoke_tool`) for the long tail —
  never load 55 tool schemas into context.
- **Real input schemas** on every tool (fix null `query_schema`) so the client forms valid calls first try.
- **LLM-tuned names + descriptions + annotations** (read-only / idempotent / destructive) so the client
  selects correctly and can cache/retry safely.
- **De-judged, structured results** — facts + coefficients; the client/model does meaning + the pick; the
  server never pre-filters (ties to de-judgment, §6-A).
- **Bundles + a `prompts` primitive** for common workflows (a career read = one rich call, not ten
  round-trips); **auto-loaded resources** for standing context (house-rules, chart-snapshot).
- **Forced B.11-first** guarantee in the gateway the client cannot skip.
- **Explicit required `chart_id`** + clear, actionable authz/error contracts ("chart not built", "no access",
  "invalid chart_id").
- **Determinism + idempotency** end-to-end so results are cacheable and reproducible.
- **Operator observability** (traces, health, coverage) that is invisible to the client.

**Open:** reconcile this against the native's prior conversation on client expectations (§9 item 17) —
locate that session's requirements and fold any deltas in before finalizing the MCP brief.

## §14 — Panchang component carve-out (post-wave build-out)

Panchang has the basic ingredients today (`python-sidecar` panchang, `/panchang` surface, `query_panchanga`
tool, `panchanga_daily` table). **Now:** carve a clear bounded **Panchang component** with defined seams —
it is an **asset-class-C** (per-chart date-parameterized) module dependent on the L1 natal base + ephemeris,
personalized via the multi-tenant chart dropdown, exposed as one UI surface + one retrieval tool. Reserve its
namespace and consolidate the duplicate `/api/panchang` + `/api/panchanga` trees (§3.7). **Later:** its full
build-out runs as its own phase **after** the modernization wave — not inside it. This plan only fixes the
boundary so the build-out is clean.

## §15 — Audit Reconciliation Ledger (v2.1)

Reconciles v2.0 against the Claude Code code-grounded audit (`00_ARCHITECTURE/INVESTIGATION/
MODERNIZATION_AUDIT_REPORT_v1_0.md`, verdict **APPROVE WITH CONDITIONS**, main HEAD `367ee47c`) + the Gemini
independent audit (v1). **Where this ledger conflicts with the v2.0 body, the ledger is authoritative for
v2.1.** Per-wave CLAUDECODE_BRIEF units draw from here.

### §15.1 — Corrections applied (factual; audit-verified)
| # | v2.0 said | Correct state (cited) | Disposition |
|---|---|---|---|
| C1 | constituent path `BRIEFS/FACT_ENGINE_PYJHORA_BRIEF` | actual `00_ARCHITECTURE/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md` (no BRIEFS/) | frontmatter fixed |
| C2 | §6-A peers under `platform/src/lib/retrieve/` | they live in `platform-mcp/src/tools/`; portal counterpart is `query_varshaphala.ts` | §6-A fixed; de-judgment = 4 lines × 2 channels |
| C3 | `query_varshphal.ts:87` = "redaction" | it is a **hard-403 tier gate** (`audience_tier==='client'`→Forbidden) — a G2 item, not redaction | reclassified to §6-C / G2 |
| C4 | §3.2 one native default | **TWO** live: `'abhisek_mohanty_primary'` (text, 4 files) + `'362f9f17-…'` (uuid, 2 files) + `DEFAULT_CHART_ID` const | §3.2 amended; strangler join-table |
| C5 | §6-D `MCP_TO_RETRIEVAL_TOOL` at line 96 | line **92** | noted |
| C6 | §6-D "all 79 manifest query_schema null" | 9 have it; 70+ have **no field at all** | rephrase "populate the 70+ missing"; action unchanged |
| C7 | §6-F "L2 fully archived" | archived as **artifacts** only; `api/clients/route.ts:82–83` still creates `L2.analysis_mode_a/b` rows | add live-code cleanup task |
| C8 | §3.3 classical = 2-way; multi_school = 1:1 | classical is **3-way**; multi_school is **2:1** (`multi_school_bundle` composite + `cross_school_lookup` primitive) — do NOT collapse | §3.3 amended |
| C9 | §6-B `panel_strategy.ts` legacy | distinct from the **active** `synthesis/panel/` dir — disambiguate before delete | flagged |

### §15.2 — Structural additions (accepted from audit)
- **New hard gate G5b** (now §7): adapter `onFinish` parity (persistence + predictions + observatory),
  golden-transcript proven, before legacy-pipeline delete.
- **Wave 0 split** into **0a** (pure renames) and **0b** (B.11 hotfix + secrets + atomic mirror-retirement PR).
- **§3.7 CI rules (c)+(d)** move Wave 0 → **Wave 3** (the unified contract/gateway does not exist yet).
- **Tenant-key migration = strangler** with a `chart_text_alias ↔ chart_id uuid` mapping, reads→writes→drop, mapping BOTH live values (C4) — not a column-alter.
- **Cutover atomicity:** reuse the Phase 4C `bootstrap_panchanga.py` staging→live swap + `build_id` rollback.
- **Class-C enumeration is a Wave-1-BLOCKING deliverable**, not "an investigation" — the build DAG can't be authored without it.
- **Mirror-discipline retirement = ONE atomic Wave-0a PR** touching all five surfaces: CLAUDE.md §C-11 + §K, `GOVERNANCE_INTEGRITY_PROTOCOL §K.3`, `CANONICAL_ARTIFACTS §2`, `NATIVE_DIRECTIVES ND.1`, + delete `.geminirules`/`project_state.md`/`mirror_enforcer.py`. Half-state fails `drift_detector.py`.
- **Determinism model made operational (§11.2):** pin the golden-transcript test schema + the content-addressed provenance row `{chart_id, asset_id, engine_version, ayanamsha, input_hash, salience_formula_version, computed_at}`.
- **python-sidecar reality:** Wave 1 is a **BUILD** (new `python-sidecar/natal_engine/`), not a refactor; existing routers become adapters.
- **`marsys-build-pipeline-job` unverified in IaC** — confirm/provision before §4.2-1.
- **L2 live-code cleanup** task added (delete L2 sublayer creation in `api/clients` POST).
- **Tool↔Asset Reconciliation (NEW — native-raised 2026-05-27; gate G6):** after the data assets are rebuilt
  (2a) and the unified contract lands (2b), explicitly re-map EVERY retrieval/MCP tool to the NEW data
  asset(s) it serves, and audit: (a) **coverage** — every live asset (incl. the new T1 structural-fact
  layer, the UCN computed-digest that replaces narrative UCN, and the deterministic CDLM/CGM graphs) has ≥1
  appropriate tool; (b) **no redundancy** — no two tools serve the same asset+intent (collapse per §3.3);
  (c) **no orphans** — no tool still reads a retired/changed asset shape; (d) **LLM-client fit** — the
  surfaced set matches §13 (gateway + bundles + real schemas). Driven by the manifest `data_dependency` graph
  + the `data_coverage`/`tool_health` tools. Gate **G6_tool_coverage** = `data_coverage` reports 100% asset
  coverage + 0 orphaned tools + 0 redundant duplicates. First-class Wave-3 unit `3.tool_asset_recon`, gated
  after 2a+2b — tools cannot be finally mapped until the assets they read have settled. Closes the
  "tools still point at the old data sources" risk.

### §15.3 — Gemini independent-perspective keepers (folded in)
- **Postgres Row-Level Security keyed on `owner_id`** as defense-in-depth behind `authorizeChartAccess` (Track 3).
- **Connection pooling** (PgBouncer / connector pool) — multi-chart builds exhaust `db-g1-small` connections (Track 0/Wave 4).
- **Content-hash recalculation storm:** an `engine_version` bump invalidates EVERY chart's hash at once → lazy/scheduled, version-scoped rebuild, not eager global recompute (Track 1).
- **Single-chart JH validation is insufficient** → add a **multi-chart edge-case validation set** (extreme latitudes, retrograde stations, leap seconds) alongside the FORENSIC oracle (Track 1 / G1).
- **Decompose the MSR coefficient into separate DB columns** (`deterministic_strength`, `verification_certainty`, `computed_salience`) — structural, not LLM-instructed (Track 1 §12; complements de-judgment).
- **Progressive-disclosure UX:** facts by default; explicit "Interpret" runs the serve-time panel — saves cost, segregates facts from opinion (Track 4 / §7).
- **Parallel panel development** against mock T1 data — both audits agree it shortens the critical path; relax the panel's Wave-3-after-Wave-2 coupling (Track 5).
- *Rejected:* Gemini's "move new data to Firestore/BigQuery" — keep Postgres as system-of-record (additive extension protects working tooling). Recorded for completeness.

### §15.4 — Forks still needing the NATIVE's decision (elevated from audit MUST-RESOLVE)
1. ~~JH-oracle policy~~ — **RESOLVED 2026-05-27: JH-as-oracle.** Pin a specific Jagannatha Hora version + ayanamsha, capture its outputs once as the golden fixture (JH not a runtime dependency); FORENSIC v8.0 stays a reconciliation. G1 amended in §7. Consistent with the standing "JH is sole formula authority, validate-once at build time" constraint. Deliverable: which JH version/build + which ayanamsha to pin.
2. **Macro-phase number** (M6 vs a parallel M5-X modernization track).
3. **GCP investment level** (recommend incremental: Memorystore + observability first; SQL upgrade + HA when the first external tenant signs up).
4. **TierPicker depth replacement:** planner auto-picks depth by query class, or a new explicit user setting?
5. **MCP client-expectations source** (§9 item 17, still open).
6. **Anthropic-cost decision** — `ANTHROPIC_*` live in deploy.yml despite the documented cost-ban; make it explicit.

### §15.5 — Provenance of the reconciliation
Authored by Claude (Cowork), 2026-05-27, against the Claude Code audit (HEAD `367ee47c`) + Gemini v1. A
deeper Gemini re-run (prompt v2) may feed a future v2.2. No implementation begins until the native resolves
§15.4 and approves; affected canonical artifacts version-bump at that point.

---

## §16 — Provenance
Model-authored (Claude, Cowork), DRAFT, **v2.1** (reconciled — see §15). v2.0 extended v1.0 with verified code
recon (3 sub-agents) + four native-requested dimensions; v2.1 reconciles the Claude Code + Gemini audits.
Modifies nothing canonical. Run as a declared macro-phase.
