---
artifact: CLAUDECODE_BRIEF_BODHA_B1_v1_0.md
canonical_id: BODHA_B1_BRIEF
version: 1.0
status: READY_TO_EXECUTE (after L1-E completes — see §1 dependency)
authored_by: Cowork (planning) 2026-06-16
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
scope: B1 ONLY — bo_laksana (MSR) full projection + the anti-drift spine. NOT the fan-out (B2+).
execution_mode: CONTINUOUS within B1's sub-steps; STOP on a real dependency miss or a Tier-3 event
  (destructive op / genuine ambiguity / needed architecture change → raise to native).
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (platform/scripts/start_db_proxy.sh, 127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_MASTER_PLAN_v3_0.md (the dual-capture model — B1 is §3 of it)
  - L2_BODHA_L1E_SCOPE_AND_DEDUP_v1_0.md (ownership/dedup rules B1 must honor)
  - L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md (intrinsic L1 vs population-level L2)
  - A10_MSR_SPEC_v1_0.md (§3 schema, §4 salience_formula_v1, §11 MVs)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase contract) + §5 (conformance)
  - MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md (Trap 1) + MSR_UCN_CONTAMINATION_AUDIT_v1_0.md (Trap 2)
target_files:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py (rewrite the projection)
  - bodha_writers/formulas.py (salience_formula_v1 — already present; do NOT change the formula)
  - a new surgical migration (signal_summary_text column + dedup unique index, if not already present)
must_not_touch:
  - the FROZEN orchestrator contract (WriterBase / registry / asset_throughput)
  - any ga_* writer (L1-E is a SEPARATE brief; B1 consumes its output, does not produce it)
  - the fan-out writers (bo_sangati/bo_karanajala/bo_bimba/bo_samskara/bo_upaya/bo_pramana_mapa/bo_samvada)
---

# Bodha B1 — bo_laksana (MSR) Full Projection + Anti-Drift Spine

## §0 — What B1 is, in one paragraph
`bo_laksana` projects the WHOLE of L1 into `bodha_msr_signals` — one signal per meaningful L1 fact,
across ALL L1 assets (the enriched `ga_structural` for relationship facts, and `ga_strength` /
`ga_sensitive` / `ga_sade_sati` / `ga_panchanga` / `ga_positions` for their native-grained facts). It does
NOT re-fire predicates, does NOT re-derive values, does NOT curate. It INHERITS each L1 `fact_id` by
reference and ADDS population-level enrichment: `computed_salience` (salience_formula_v1),
`top_k_salience_rank`, domain + tradition tags, `fact_kind` typing, the L0 classical bridge, and a
lossless summary text. **The whole point of B1 is the anti-drift spine: every signal's
`constituent_facts_array` resolves to a real `chart_facts.fact_id`. Prove that before B2 ever runs.**

## §1 — DEPENDENCY GATE (read before starting)
B1 consumes the OUTPUT of L1-E (the ga_structural enrichment per `L2_BODHA_MASTER_PLAN_v3_0 §2` +
`L2_BODHA_L1E_SCOPE_AND_DEDUP`). **If L1-E has not run and re-sealed (ga_structural grown past 74,644 with
FORENSIC 7/7 re-passed), STOP** — B1 would project an incomplete relational layer. Confirm on prod that
the enriched ga_structural facts exist before coding B1's build. (B1's CODE can be written in parallel; the
BUILD must wait for L1-E.)

**Inherited non-negotiables:** deterministic-first (no generative LLM in the build); no audience tier;
no silent drops (skips logged + must be zero in a clean run); per-chart isolation by chart_id; **real
fact_ids, never mock**; FROZEN orchestrator contract (`@register('bo_laksana')` WriterBase, runs on
`ctx.db_conn`, NEVER commits/closes it, NEVER writes asset_throughput, gets chart_id+birth_params from
`ctx.config`); count_sql is data-truth; floors aspirational (target_floor = achieved). **If the writer
seems to need an orchestrator-contract change → STOP, raise with the native.**

## §2 — Preconditions (verify on prod; fix-forward if any fail)
1. Cloud SQL proxy up (127.0.0.1:5433).
2. Migrations 226 (`bodha_*` spec tables) + 230 (registry reconcile) applied to prod — verify
   `bodha_msr_signals` exists at full ~50-col spec schema; do not infer from file presence. Apply
   surgically if missing; readback after.
3. L1-E complete + re-sealed (see §1).
4. **Pin the projection count NOW (the "load-bearing number" is knowable today, not at build time):**
   run against prod `SELECT count(*) FROM chart_facts WHERE chart_id = '<native>' AND fact_category = ANY(<the
   full projectable signal-category set>)`. Record it. This is B1's parity target.

## §3 — B1.1 — DELETE the curation; project the whole L1 population
The merged `bo_laksana` fetches `WHERE fact_category = ANY(ALL_SIGNAL_CATEGORIES)` — a legacy ~31-item
allow-list. **Remove it as a filter.**
- Enumerate projectable categories FROM LIVE `chart_facts` (data-derived, never hardcoded). The simplest
  correct rule: project every row whose `source_asset_id` is in the L1 set, EXCEPT a tiny documented
  EXCLUDE set of pure-helper rows used only as salience inputs — and per the native, even those are ALSO
  projected as their own magnitude-signals (§B1.2). Net: nothing is curated away.
- Keep `CATEGORY_DOMAIN_MAP` / `CATEGORY_TRADITION_MAP` as ENRICHMENT lookups (not filters). For a category
  with no mapping: default `domains_affected = ['general']`, `tradition = 'parashari'`, and FLAG it in run
  notes so the native can extend the maps — never drop a row for lacking a mapping.
- Salience computed per signal; **NEVER used as a filter** (no `WHERE salience > x`, no `LIMIT N` drop).
  Weak tail kept.

## §4 — B1.2 — ga_strength facts as SIGNALS *and* INPUTS
Project every shadbala / ashtakavarga / bhava-bala / ishta-kashta / vimsopaka fact as a retrievable
magnitude-signal (`fact_kind = magnitude`) AND keep the salience lookup dicts (a fact can be both an input
and a stored signal). Closes the ~2,184-row gap where strength was invisible to retrieval.

## §5 — B1.3 — fact_kind typing on every signal
Derive and store `fact_kind` ∈ {relationship, magnitude, position, time_window, birth_moment} from
`source_asset_id` + category:
- enriched ga_structural → `relationship`
- ga_strength → `magnitude`
- ga_sensitive / ga_positions → `position`
- ga_sade_sati → `time_window`
- ga_panchanga → `birth_moment`
This typing flows through to retrieval so the synthesis LLM knows WHAT KIND of fact each signal is. (Add the
column via a surgical migration if `bodha_msr_signals` lacks it; otherwise reuse the existing column.)

## §6 — B1.4 — DEDUP by ownership (honor L2_BODHA_L1E_SCOPE_AND_DEDUP)
- Each signal references its owning L1 fact_id(s) in `constituent_facts_array`. A magnitude-signal (from
  ga_strength) and a relationship-signal (from enriched ga_structural that USED that magnitude) are NOT
  duplicates — different fact_kind, both kept.
- **Two signals are duplicates iff same `fact_kind` AND same `constituent_facts_array` AND same
  `configuration`.** Enforce with a dedup check at insert (or a unique index on that natural key). Collapse
  those only; keep everything else. A weak-but-real relationship is never a duplicate → always kept.

## §7 — B1.5 — THE ANTI-DRIFT SPINE (the gate — prove on bo_laksana ALONE before any B2 work)
Run ONLY bo_laksana for the native chart (single-asset run). Verify, against PROD, in order — HALT on any
failure:
1. **Spine resolves:** every `bodha_msr_signals.constituent_facts_array` element resolves to a real
   `chart_facts.fact_id` for this chart → MUST be zero unresolved. `[verify-against: prod]`
2. **Count parity:** `count(bodha_msr_signals WHERE chart_id=native)` == the §2.4 pinned count (parity over
   the WHOLE L1 population — not ga_structural alone, not a subset, not a predicate catalog). Skips logged
   = zero in a clean run. `[verify-against: prod]`
3. **No re-derivation (Trap 1):** spot-check ≥10 signals incl. the FORENSIC anchors (Sun=Capricorn, Moon=
   Purva Bhadrapada, Lagna=Aries, Muntha) — each inherits the L1 value, not a recomputed one. `[verify-against: prod]`
4. **Weak tail present:** the bottom decile of `computed_salience` is non-empty (a curated build would lack
   it). `[verify-against: prod]`
5. **No-loss:** count of DISTINCT L1 fact_ids referenced across all signals == count of projectable L1
   fact_ids (every L1 fact → ≥1 signal; relationships add MORE, never fewer). `[verify-against: prod]`
6. **Idempotency:** re-run one ayanamsha; row count stable (delete-then-insert, not accrete). `[verify-against: prod]`
**If 1, 2, or 5 fail, the projection is wrong — fix it; do NOT let B2 build on a broken root.**

## §8 — B1.6 — THE L0 CLASSICAL BRIDGE
Populate every matchable signal's `classical_sources_array` (schema column exists, currently `None`) by a
DETERMINISTIC join — NO LLM:
- named yogas/doshas → `brahma_yoga_catalog` / `brahma_dosha_catalog` (id + citation).
- rule-traceable configs → `bg_rules` (verse ref) where a deterministic structural match exists.
- classical chunks → `bg_texts` via the existing L0 id-linkage (NOT semantic similarity here — that's a
  retrieval-time op).
- unmatched raw signals → empty array (NOT faked). Report the matched-vs-unmatched ratio in run notes.
**Acceptance [verify-against: prod]:** every named-yoga/dosha signal carries ≥1 resolvable classical source;
deterministic (re-run → identical); raw signals empty not fabricated. This is what makes retrieval return
the FACT + its connected classical citation(s) together.

## §9 — B1.7 — Lossless signal_summary_text (E2)
Add a deterministic, template-generated `signal_summary_text` (new column via surgical migration, or a 1:1
side table). **EXHAUSTIVE BY CONSTRUCTION:** render ALL typed columns, THEN iterate EVERY key in
`configuration_jsonb` (the current `_build_input_summary` pulls only 5 keys — that is lossy; fix it). No LLM
(pure template). Example: "Jupiter–Venus conjunction in D1 Sagittarius (Lahiri), orb 2°, salience 0.81,
rank 12, supports career+spirituality, two-pass verified, cites Phaladeepika 6.12." **Acceptance:** every
signal has a non-empty summary; a fuzz test confirms NO `configuration_jsonb` key is omitted (losslessness).
This is the dense citable surface the synthesis LLM reasons over AND the input text for the B2 embeddings.

## §10 — B1.8 — Materialized views (A10 §11)
Build/refresh the 3 MVs after the insert: `mv_msr_top_signals_per_chart` (top-100 by salience per
ayanamsha), `mv_msr_recurring_patterns_per_chart`, `mv_msr_domain_summary`.

## §11 — B1 acceptance (the whole gate)
- [ ] Curation deleted — projection enumerated from live chart_facts, no hardcoded allow-list.
- [ ] Whole-L1 projection — relationship + magnitude + position + time_window + birth_moment signals all present.
- [ ] **Anti-drift spine (§7): zero unresolved constituent fact_ids; count == pinned parity; FORENSIC anchors inherit L1; weak tail present; no-loss; idempotent.**
- [ ] Dedup: zero same-kind+same-constituents+same-config duplicates; weak-but-real relationships kept.
- [ ] fact_kind on every signal.
- [ ] L0 bridge: named yoga/dosha signals carry resolvable classical_sources_array; raw signals empty (not faked); ratio reported.
- [ ] signal_summary_text present + lossless (fuzz test passes).
- [ ] 3 MVs built/refreshed.
- [ ] FROZEN contract honored; migration numbers fresh; surgical apply + readback held.
- [ ] **Proven on bo_laksana ALONE — no fan-out asset touched.**

## §OUT OF SCOPE for B1
The fan-out (B2: CDLM/CGM/embeddings/UCD), bo_upaya (B3), scorecard (B4), orchestrate+seal (B5), the eval
harness (B6). The L1-E enrichment itself (separate brief — B1 consumes it). Real embeddings live in B2
(bo_samskara), though B1.7's summary text is their input. Do NOT reintroduce the predicate-firing model or
G52. Do NOT change the FROZEN orchestrator contract or any ga_* writer.

---
*End of BODHA_B1 v1.0 — bo_laksana projects the WHOLE of L1 (no curation; relationship + magnitude +
position + time_window + birth_moment, fact_kind-typed; dedup by ownership; L0-bridged; lossless summary),
and the anti-drift spine (every constituent_facts_array resolves; count parity; no loss) is PROVEN on
bo_laksana alone before any fan-out. Depends on L1-E (enriched ga_structural) having run + re-sealed.*
