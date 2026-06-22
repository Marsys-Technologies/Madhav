---
artifact: L5_MIMAMSA_ONBOARDING_HANDOFF_v1_0.md
canonical_id: L5_MIMAMSA_ONBOARDING_HANDOFF
version: 1.0
status: CURRENT — the L5 Mīmāṃsā campaign onboarding handoff (start the next Cowork conversation from this)
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The single rich-context entry point for the L5 Mīmāṃsā campaign. Everything the next Cowork session
  needs: what L5 IS, the platform/assets/services it leverages, the FROZEN contract it must obey, the
  structural reality (incl. the legacy-code trap), the ph_pramana→L5 contract it consumes, and the exact
  repo-grounding steps to take BEFORE any work. Read this first; then read the repo (it will be live on
  localhost + main once L4's deploy lands).
---

# L5 Mīmāṃsā — Campaign Onboarding Handoff

## §0 — HOW TO START THE NEXT CONVERSATION (do this first, in order)
1. **Read this whole document.**
2. **Ground in the live repo — do NOT work from memory.** The L4 merge is on `main` and (once the
   PROD_DATABASE_URL deploy lands) live on localhost:3000 + prod. Before any L5 work:
   - Read `CLAUDE.md §C` (mandatory per-session reading list) + `00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2`
     (the authoritative "you are here" — confirm L4 is CLOSED before opening L5).
   - Read `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2` (the FROZEN WriterBase contract) +
     `00_ARCHITECTURE/L1_GANITA_CLOSURE_v1_0.md` (the layer-onboarding template).
   - Read the L4 close artifacts when they exist: `L4_PHALA_CLOSE_v1_0.md` + the `ph_pramana` writer
     (`platform/python-sidecar/pipeline/orchestrator/writers/ph_pramana.py`) — this is the asset that
     wrote L5's input contract (see §5).
   - Grep the live registry: `curl -s localhost:3000/api/cockpit/registry | jq '[.data.assets[]|select(.layer=="mimamsa")]'`
     to see the 6 mi_* rows as they actually exist in the DB.
3. **Verify state from CURRENT_STATE + git, NOT from CLAUDE.md §F** (it's intentionally stale) — and NOT
   from this handoff's "as of" facts alone; re-confirm against the repo (the L4 cockpit incident proved
   docs drift from deployed reality).
4. Emit the SESSION_OPEN handshake (`SESSION_OPEN_TEMPLATE_v1_0.md`); declare may_touch/must_not_touch.

## §1 — WHAT L5 MĪMĀṂSĀ IS (the mission)
L5 Mīmāṃsā (external name; internal "L5") is the **learning / calibration / self-correction layer** — the
top of the L0→L5 arc. Its job: take L4 Phala's **falsifiable predictions**, compare them against **lived
reality** (the Life Event Log), **score** them (calibration: were the probabilistic, time-indexed
predictions actually right?), and feed **correction signals** back so the instrument improves over time.
This is the layer that fulfills CLAUDE.md §A: *"time-indexed, probabilistic, calibrated predictions
testable against lived reality and correctable from outcomes."*

**The L4/L5 boundary (D5, hard):** L4 makes predictions falsifiable (scaffolding — structured falsifier,
eval_date, empty outcome hook) and ships confidence HONESTLY LABELED as structural-not-yet-empirical.
**L5 owns ALL scoring/calibration.** L4's `ph_pramana` writes a falsifiability registry and explicitly
RAISES a build-halt if anyone tries to put a calibration_score in L4. L5 is where those scores live.

**External lexicon (LOCKED):** Brahmagyan · Gaṇita · Bodha · Kāla · Phala · **Mīmāṃsā** = L0–L5.
Never show "L5" externally. Asset prefix: **`mi_*`**. Tables: **`mimamsa_*`** (+ shared `life_events`).

## §2 — STRUCTURAL REALITY (the most important section — read twice)
**L5 is NOT greenfield, and it is NOT plug-and-play. It is the same trap L3 and L4 were:**
substantial engine/script code EXISTS but does NOT conform to the frozen orchestrator contract.

- **6 `mi_*` assets are ALREADY REGISTERED** in `platform/scripts/seed/asset_registry_seed.ts`:
  | asset_id | name | target_table | depends_on |
  |---|---|---|---|
  | mi_bhavisya | Predictions | mimamsa_predictions | bo_laksana, ka_kalasutra |
  | mi_gunanaka | Multipliers | mimamsa_multipliers | mi_pramana |
  | mi_jivanaghatana | Life event log (held-out) | life_events | — |
  | mi_pariksha | QA evaluation | mimamsa_qa_eval | — |
  | mi_pramana | Calibration | mimamsa_calibration | mi_bhavisya |
  | mi_vistara | Export log | mimamsa_export_log | — |
  (CONFIRM these against the live registry + re-examine the depends_on — `mi_bhavisya` depending on
  `bo_laksana`/`ka_kalasutra` but NOT on L4's `ph_*` looks WRONG for a layer that scores L4 predictions.
  The dependency wiring almost certainly needs correction to point L5 at the `phala_*` outputs. Treat the
  seed depends_on as DRAFT, not authoritative.)

- **Legacy code EXISTS in `platform/python-sidecar/brahmagyan/mimamsa/`** — real, non-trivial:
  `prediction_ledger.py, outcome.py, multiplier.py, answer_quality.py, lel_intake.py, l5_calibration_substrate.py,
  l5_learning_multiplier.py, l5_event_chart_state_index.py, l5_bigquery_export.py, export_to_bigquery.py`.
  Plus real migrations (`brahma_mimamsa_*.sql` — prediction_ledger 177 lines, outcome 205, multiplier 190,
  answer_quality 288, lel_intake 292) and L5 test files (`tests/l5/`, `tests/test_mimamsa_*`).
- **CRITICAL: NONE of it uses `@register('mi_*')` / WriterBase.** `grep -rln "@register('mi_" ` returns
  ZERO. This is PRE-ORCHESTRATOR legacy code. So the L5 build is **audit → wire to the frozen contract →
  reconcile the existing tables/migrations → fill gaps**, exactly like L3 Kāla was (where "engines exist,
  just wire" turned out FALSE — transit_search was never built; see [[project-l3-kala-engine-audit]]).
  **Do NOT trust "L5 is mostly done."** Audit the actual code against the contract FIRST.
- **Apply the rebuild-skepticism rule** ([[feedback-rebuild-skepticism-of-existing-code]]): the legacy
  mimamsa code is reference for INTENT, not authoritative implementation. Multiple revisions may have
  corrupted it. Clean-architecture review before reuse; rewrite where cruft is present.

## §3 — THE FROZEN ORCHESTRATOR CONTRACT (L5 inherits it without exception)
Every `mi_*` writer is a `@register('mi_<asset>')` subclass of `WriterBase` in
`platform/python-sidecar/pipeline/orchestrator/writers/`. It:
- implements `run(ctx) -> WriterResult` (light) OR `plan_substeps(ctx)` + `run_substep(ctx, step)` (heavy);
- uses `conn = ctx.db_conn` and **NEVER commits or closes it** (orchestrator owns the txn + per-substep savepoint);
- **never writes `asset_throughput`** (orchestrator is the sole build-state writer);
- returns `WriterResult(asset_id=..., rows_inserted=...)` — the kwarg is **`rows_inserted`**, NOT `rows_written` (L3 BUG-3);
- gets `chart_id` + `birth_params` from `ctx.config`;
- **idempotency:** per-chart delete-then-insert scoped to `(chart_id × natural key)` (mirror `ga_writers/_idempotency.py`);
- **count_sql uses `$1`** (never `$$CHART_ID$$` — L3 BUG-1); the stats route reads `count_sql`;
- **service dir MUST be COPY'd in `platform/python-sidecar/Dockerfile.pipeline`** (the silent-hang gotcha
  that bit bo_pramana_mapa + every ka_*/ph_* — `services/` IS now COPY'd, line 44; add any new top-level dir).
**If a writer seems to need a contract change → STOP and raise with the native. The freeze is deliberate.**
The orchestrator click-Build path drives the build; never a reconcile script (CF.L3.8). Auto-discovery is
pkgutil-based and HARD-FAILS on any import error in the writers package — every mi_* writer must import clean.

## §4 — WHAT L5 LEVERAGES (the existing platform — reuse, do not duplicate)
**Upstream layers (all SEALED, read-only to L5):**
- **L4 Phala** `phala_*` — the predictions L5 scores. Key: `phala_anchors` (the spine, 8 axes + 5
  elevations, ~350 rows for native), `phala_pramana` (the **falsifiability registry** — L5's primary
  input; see §5), `phala_phaladesa` (the delivered outlook), `phala_muhurta/mitigation/sankrama`, and the
  `phala_rectification`/`_best` (birth-time rectification, staged not adopted).
- **L3 Kāla** `kala_*` — `kala_convergence` (with horizon_tier near/lifetime from U2), `kala_jivana_parva`
  (lifetime parvas, now scored), `kala_activation`, `kala_obstruction`, the dāśā timeline. Services:
  `ka_dasha_kala, ka_gochara, ka_graha_sancara, ka_muhurta_seva, ka_tulana` (callable, not re-derive).
- **L2 Bodha** `bodha_*` — `bodha_msr_signals` (66,738), `bodha_signal_embeddings` (66,738 — real
  embeddings), `bodha_discoveries` (1,505), `bodha_cdlm_cells` (the Cross-Domain Linkage Matrix),
  `bodha_rm_remedy_prescriptions`. The CGM graph + CDLM asymmetry are L5's richest latent substrate.
- **L1 Gaṇita** `chart_facts` (the 7 FORENSIC anchors + all computed values; 27,554 rows), `chart_dashas`
  (536,471 — all 7 systems, N1–N4), `chart_divisionals` (21,635), plus the per-subsystem assets
  (ga_medical, ga_vastu, ga_yoga_firings, ga_condition_composite, l1_tajik_varsha_year_lords).
- **L0 Brahmagyan** `bg_*` — classical rule base, ontology, texts, ephemeris (825,084 rows, 1900–2150),
  remedy corpus, nakshatra. The citation substrate (`brahma_yoga_catalog`, `bg_rules`, `bg_texts`).
- **The Life Event Log** (`life_events` / `LIFE_EVENT_LOG_v1_2.md`, canonical_id LEL, v1.7) — the GROUND
  TRUTH L5 scores predictions against. ~57 events. **This is small** — see §6 calibration caution.
- **Parallel subsystems** (all built + readable per-chart): Nakshatra, Astrovastu, Medical, Yoga, Dignity,
  Sade-Sati, Tājika, Prashna. Reuse via READ-asset → CALL-service → recompute-PyJHora-only-if-absent.
- **Retrieval layer:** `src/lib/retrieval/registry/layers/L5_mimamsa` already scaffolds L5 retrieval.
- **PyJHora is THE engine** (no JH-parity oracle anywhere; verify by internal consistency only).

## §5 — THE ph_pramana → L5 CONTRACT (L5's primary input, written by L4)
L4's `ph_pramana` writer (`writers/ph_pramana.py`) built `phala_pramana` as a **falsifiability evidence
registry** — one record per `phala_anchors` entry — with: the structured falsifier, `window_status`,
`evidence_type`, `outcome_valence`, `eval_date`, and an EMPTY outcome hook. It explicitly does NOT score
(the D5 gate RAISES a build-halt if `calibration_score`/`posterior_probability`/`accuracy_rate` appear in
L4). **L5 consumes `phala_pramana` + `life_events`, fills the outcome, and computes the calibration.**
Read `ph_pramana.py` lines ~120–190 for the exact column contract L5 must honor. The L5 onboarding contract
ph_pramana drafted is the authoritative spec for `mi_pramana` (Calibration).

## §6 — HARD CONSTRAINTS + RATIFIED DECISIONS L5 MUST OBEY
- **B.10 — canonical chart immutable.** Never auto-mutate `482012f1`. (Rectification adoption is native-gated.)
- **Calibration-data caution (the reason L4 deferred scoring to L5):** the LEL is THIN (~57 events,
  ~9/domain). Per-domain calibration on this alone is statistically fragile. **Leakage/circularity risk:**
  the same LEL events ground L2 signals + L4 rectification AND would score L5 predictions — L5 likely needs
  a HELD-OUT event set and/or NON-NATIVE charts (the multi-chart apparatus is an L5 concern, not L4's).
  `mi_jivanaghatana` is named "Life event log (HELD-OUT)" — honor that. Design the calibration to be honest
  about n and leakage; a LEAKAGE-FIREWALL like ph_sodhana's is mandatory.
- **No fabricated computation (B.10/B.11):** if a value needs a specialist tool and isn't in L1–L4, mark
  `[EXTERNAL_COMPUTATION_REQUIRED]`; never invent calibration numbers.
- **Deterministic-first** ([[feedback-deterministic-first-for-data-build]]): Python for computation;
  embeddings are fine; generative LLM for curation is NOT. Scoring math must be deterministic + auditable.
- **Floors aspirational, not gates** ([[feedback-floors-are-aspirational-not-gates]]); **no audience tier**
  ([[feedback-no-audience-tier]]); **L-is-authority** (L5 references L4 ids, never restates a value).
- **Model policy:** Gemini/DeepSeek; **Anthropic BANNED** for the instrument's own LLM calls.
- **Surgical migrations only** (next free number after L4's 341 — confirm against prod max at open).
- **Whole-Chart-Read (B.11):** every query routes through L2 synthesis first; L5 adds the calibration view.

## §7 — INFRA + DEPLOY REALITIES (so L5 doesn't re-hit L4's blockers)
- **Localhost = code plane only; data plane is ALWAYS prod** via the Cloud SQL proxy (port 5433). No local
  Postgres. Applying a migration on localhost IS a prod schema change ([[feedback-localhost-codeplane-prod-dataplane]]).
- **Push to main AUTO-MIGRATES + DEPLOYS prod** (`deploy.yml` runs `migrate.ts` against PROD_DATABASE_URL
  before deploying — [[push-to-main-auto-migrates-prod]]). The push IS the prod-migrate trigger.
- **PROD_DATABASE_URL GitHub secret** must stay set (it was the L4 P6 blocker — [[prod-database-url-secret-missing]]).
- **Verify against the LIVE deployed cockpit, never the branch** (SESSION_CLOSE_TEMPLATE §7.9 live-deployment
  guard — the seal must assert `mimamsa == N lit` against the running prod API). This is the #1 lesson from L3+L4.
- **Next.js 16.2.4 Turbopack CPU-thrash** → use `next dev --webpack` locally ([[feedback-turbopack-1624-cpu-thrash]]).
- **Cowork plans/authors; Claude Code in Antigravity implements** ([[feedback-cowork-vs-antigravity-split]]).
  Every Cowork output = a pasteable prompt or a committed .md brief, never chat bullets to hand-translate.

## §8 — SUGGESTED L5 CAMPAIGN ARC (Cowork plans this in the next session; not prescriptive)
Mirror the L3/L4 pattern that worked: **audit (what mi_* code really exists vs the contract) → holistic
design (the calibration method, the held-out/leakage strategy, the feedback loop) → per-asset specs (the 6
mi_*, fixing the depends_on to point at phala_*) → wire to the frozen contract → retrieval → clean seal
with the live-deployment guard.** Open with a prod-truth reconciliation (which mimamsa_* tables exist in
prod, which are empty, what the legacy code actually does) exactly as L4 opened with one.

## §9 — POINTERS (canonical artifacts to cite, not duplicate)
- `CLAUDE.md` (mission §A, do-not §L, build standards §N) · `PROJECT_ARCHITECTURE_v2_2.md` (principles B.1–B.12)
- `MACRO_PLAN_v2_0.md` (M1–M10, Ethical Framework, the Learning Layer substrate = L5's charter)
- `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` (frozen contract) · `L1_GANITA_CLOSURE_v1_0.md` (onboarding template)
- `L4_PHALA_CLOSE_v1_0.md` (when sealed — the immediate upstream) · `L4_PHALA_DECISIONS_LEDGER_v1_0.md` (D5 boundary)
- `LIFE_EVENT_LOG_v1_2.md` (LEL ground truth) · `MSR_v5_0.md` / `CDLM_v1_1.md` / `CGM_v9_0.md` (L2 substrate)
- The memory index `MEMORY.md` (all the feedback/[[...]] lessons referenced above)

---
*End of L5_MIMAMSA_ONBOARDING_HANDOFF v1.0. L5 is the calibration/learning layer that scores L4's
falsifiable predictions against the LEL. NOT greenfield (6 mi_* registered + real legacy code) and NOT
plug-and-play (zero frozen-contract conformance — same wire-it trap as L3/L4). Ground in the live repo
first, audit the legacy code against the contract, fix the depends_on to point at phala_*, honor the
held-out/leakage discipline, and seal against the LIVE cockpit. Open the next Cowork conversation by
reading this, then the repo.*
