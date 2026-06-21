---
artifact: CLAUDECODE_BRIEF_BO_PRAMANA_MAPA_v1_0.md
canonical_id: BO_PRAMANA_MAPA_BRIEF
version: 1.0
status: FOR_NATIVE_REVIEW (Batch 3 — the scorecard; the instrument's CONSCIENCE; the layer finale)
authored_by: Cowork (grounded in live scorecard schema + the judgment substrate) 2026-06-19
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
scope: bo_pramana_mapa ONLY — Pramāṇa-māpā ("the measure/proof map"): the GLOBAL synthesis-quality scorecard that AUDITS the whole layer's integrity + judgment soundness + calibration-readiness. Depends on ALL other bo_* assets (it audits them). Global (no chart_id filter on the asset; per-chart rows).
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY_v1_0.md (v1.1 FROZEN — the scorecard audits THESE guarantees)
  - L2_BODHA_OVERALL_APPROACH_v1_0.md (the two pillars — the scorecard proves they MEET) + L2_BODHA_STORAGE_ARCHITECTURE_v1_0.md
  - MSR_COMPUTED_VALUE_DRIFT_HANDOFF (Trap 1) + MSR_UCN_CONTAMINATION_AUDIT (Trap 2)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase) ; the B6 eval harness (this scorecard is its DATA BACKBONE)
target_files:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_pramana_mapa.py (the audit writer; runs LAST in the DAG)
  - migration: ENRICH synthesis_quality_scorecard (build-health → judgment + calibration + reachability) — empty, redefine freely
  - platform/src/lib/retrieval/registry/layers/L2_bodha/ (the self-assessment retrieval surface)
must_not_touch: FROZEN orchestrator contract; ga_* writers; the other bo_* writers (it READS + audits them).
---

# bo_pramana_mapa — the instrument's CONSCIENCE (audit + calibration substrate)

## §0 — What this is + the gap it closes
Pramāṇa-māpā = "the measure/proof map." Every other asset PRODUCES; this one JUDGES WHETHER THE PRODUCTION IS
TRUSTWORTHY. The current schema is a BUILD-HEALTH checker (counts, percentages, trap-flags) — it audits the
MECHANICS. But we elevated Bodha to a JUDGMENT substrate (weight-of-evidence, confidence, the pivot, the
no-tunnel-vision lens, the pillars-meet reachability) — and the build-health scorecard audits NONE of it. **The
supreme scorecard audits the JUDGMENT substrate, proves the two pillars MEET, lays the CALIBRATION frame, and
lets the LLM honestly VOICE the limits of its own knowledge.** It asks not "did the build run?" but "can we
TRUST the judgment, WHERE, and HOW MUCH — and is the instrument honest about its limits?" DETERMINISTIC: every
metric a deterministic audit query; no LLM, no narrative.

## §1 — Non-negotiables
Deterministic-first; no audience tier; no silent drops (a failed audit is REPORTED, never hidden); **Trap 1 + 2
are what it AUDITS**; FROZEN orchestrator contract (`@register('bo_pramana_mapa')` WriterBase on ctx.db_conn,
never commits, no asset_throughput; depends_on all other bo_* so it runs LAST); global asset. **A failed
load-bearing audit (anti-drift, pillars-meet, no-pre-answer) is a SEAL BLOCKER, not a warning.**

## §2 — Preconditions
1. Proxy up; main == prod; max migration verified.
2. **ALL other bo_* assets built** (it audits them — it must run last; the DAG enforces this via depends_on).
3. Apply the ENRICHED synthesis_quality_scorecard migration (build-health columns KEPT + the judgment/calibration/
   reachability columns ADDED). Empty — redefine freely.

## §3 — KEEP the build-health audit (necessary floor)
Per-asset counts (msr/cdlm/cgm-node/cgm-edge/rm/embedding/convergence/contradiction); two_pass_verified_pct;
citation coverage; formula versions in use; `msr_no_threshold_drop_flag` (weak tail present). This stays — it's
the floor. But it is NOT sufficient.

## §4 — ANTI-DRIFT SPINE AS ITEMIZED PRIMARY GATE (the load-bearing audit)
Not "trap1_count = 0" (one integer) — a full ITEMIZED audit, the spine made provable EVERY build:
- `constituent_refs_checked` / `constituent_refs_unresolved` (+ `unresolved_refs_jsonb` listing the offenders).
- Audited across MSR (constituent_facts_array → chart_facts), CGM (edge underlying_msr_signal_ids → MSR), CDLM
  (ledger support/oppose ids → MSR), RM (prescriptions → brahma_remedy_corpus), digest/lens (pointers → upstream).
- **A SINGLE unresolved reference FAILS the seal** (`anti_drift_seal_pass` BOOLEAN). This is the layer's
  load-bearing guarantee, now a standing every-build proof.

## §5 — JUDGMENT-INTEGRITY AUDIT (the core elevation — audits what we actually built)
Verify each judgment-substrate guarantee as a deterministic check:
- **Ledger independence (no double-counting):** flag any evidence ledger where independent_count == raw_count
  despite shared constituent_fact_ids → `ledger_double_count_violations`. A master never double-counts.
- **No pre-answering:** scan lens + digest + ledgers for stored verdict/conclusion TEXT (vs pointers) →
  `pre_answer_violations` (must be 0).
- **Pillars-meet reachability:** from the digest (bo_samvada §5), count stored items reachable in bounded hops vs
  orphaned → `items_stored` / `items_reachable` / `items_orphaned` (+ list). Orphaned = invisible to the LLM =
  a completeness AND retrievability FAILURE. `pillars_meet_pass` BOOLEAN.
- **Anti-tunnel-vision:** flag any bo_drishti lens WITHOUT its mandatory wildcard sweep → `tunnel_vision_violations` (must be 0).
- **Epistemic coverage:** pct of signals/ledgers carrying structured uncertainty (vs bare) → `epistemic_coverage_pct`.
- **L0 grounding completeness:** pct of remedies + named-yoga signals carrying a resolvable classical citation → `l0_grounding_pct`.
- **Embedding consistency:** the cross-layer CI check result (L0 + L2 same model/version/dim) → `embedding_consistency_pass`.

## §6 — CALIBRATION-READINESS FRAME (the research-instrument north star)
Can't measure calibration yet (no outcomes observed) — but lay the MEASURABLE FRAME so the instrument is
calibration-READY, not calibration-blind:
- `confidence_distribution_jsonb` — the distribution of confidence scores across signals/ledgers (is the
  instrument over- or under-confident as a population?).
- `prediction_hook_count` / `falsifier_hook_count` — count the calibration_hook fields (the empty slots L4/L5
  populate with OBSERVED accuracy — the correctable loop).
- `calibration_frame_version` — the versioned structure L4 Phala / L5 Mīmāṃsā will read + fill.
This makes the instrument's path to "calibrated/testable/correctable" CONCRETE — the frame exists, awaiting outcomes.

## §7 — RETRIEVABLE SELF-ASSESSMENT SURFACE (the instrument voicing its own limits)
The most aligned-with-the-goal move: the instrument should SAY how much it trusts itself, per area:
- `per_domain_trust_jsonb` — per life-domain: data depth + confidence + ayanamsha-fragility + grounding coverage
  ("high-confidence well-grounded on career; health thinner + more ayanamsha-fragile").
- `per_asset_trust_jsonb` — per bo_* asset: its audit health.
- These are RETRIEVABLE (§9) so the LLM can VOICE them: "I have strong data on X; my data on Y is thinner —
  treat with caution." The research-instrument ethic (knowing + admitting the limits of its own knowledge) made
  retrievable. Honest, calibrated, the opposite of fortune-telling.

## §8 — THE B6 EVAL-HARNESS DATA BACKBONE (native decision)
The scorecard does NOT run the eval — it produces the structured AUDIT DATA the B6 semantic-completeness eval
harness READS to make its seal pass/fail: the reachability map (§5), the anti-drift result (§4), the judgment-
integrity checks (§5), the per-domain trust (§7). Scorecard = the measurable substrate; eval = the judgment-
quality test on top. Expose these as queryable so the eval consumes them. Clean separation; both reinforce the seal.

## §STORAGE COMPLIANCE (storage §4B)
- May AUDIT embedding-consistency (§5) + ledger integrity as scorecard metrics. S5: pass/fail booleans + pcts =
  real columns; the itemized violation lists are jsonb. S2: chart_id present. No vector column.

## §9 — Retrieval (the conscience, made queryable)
Extend `L2_bodha/`: `query_scorecard(chart)` → the full audit (build-health + anti-drift + judgment-integrity +
calibration frame + self-assessment); `query_self_assessment(chart, domain?)` → the per-domain/per-asset trust
the LLM VOICES. Coverage gate: the scorecard reachable; the self-assessment surface exercised.

## §10 — Acceptance
- [ ] Build-health audit KEPT (counts, pcts, formula versions, weak-tail flag).
- [ ] **Anti-drift itemized gate:** refs checked/unresolved listed; a single unresolved ⇒ anti_drift_seal_pass=false (SEAL BLOCKER).
- [ ] **Judgment integrity:** ledger-double-count + pre-answer + tunnel-vision violations (all must be 0); pillars_meet_pass (orphaned items listed); epistemic + l0-grounding coverage pcts; embedding_consistency_pass.
- [ ] **Calibration frame:** confidence distribution + prediction/falsifier hook counts + frame version (the L4/L5-fillable structure).
- [ ] **Self-assessment:** per_domain_trust + per_asset_trust populated + RETRIEVABLE (the LLM can voice its limits).
- [ ] **Eval backbone:** the audit data is queryable for the B6 harness.
- [ ] query_scorecard + query_self_assessment tools; coverage gate; runs LAST in the DAG; FROZEN contract; migration fresh.
- [ ] A failed load-bearing audit BLOCKS the L2 seal (not a warning).

---

# §ELEVATION (toward supreme)
- **P-1 [research] Build-over-build TREND** — score each build's health/judgment metrics over time, so improving
  a formula (version bump) shows a measurable before/after (the research-instrument's self-improvement loop made visible).
- **P-2 [honesty] The "known gaps" register** — a first-class list of what the instrument KNOWS it doesn't know
  for this chart (un-groundable signals, ayanamsha-fragile verdicts, thin domains) — retrievable so the LLM leads with honesty.
- **P-3 [research] Red-team hooks** — fields a periodic red-team pass fills (per the project's IS.8 cadence) so
  adversarial findings are tracked in the conscience, not just in session logs.
- **P-4 [calibration] Per-confidence-band reliability slots** — the frame to later answer "when Bodha says 0.8,
  how often is it right?" bucketed by confidence band (the actual calibration curve, awaiting L5 outcomes).

---
*End of BO_PRAMANA_MAPA v1.0. The instrument's CONSCIENCE: elevated from a build-health checker to the audit +
calibration substrate. It makes the anti-drift spine an itemized SEAL-BLOCKING gate; audits the JUDGMENT substrate
(ledger independence, no-pre-answer, pillars-meet reachability, anti-tunnel-vision, epistemic + L0-grounding
coverage); lays the CALIBRATION-READINESS frame (confidence distribution + the L4/L5-fillable hooks); exposes a
RETRIEVABLE SELF-ASSESSMENT so the LLM voices the limits of its own knowledge; and serves as the B6 eval harness's
DATA BACKBONE. It validates everything the layer built. Runs last; a failed load-bearing audit blocks the seal.*
