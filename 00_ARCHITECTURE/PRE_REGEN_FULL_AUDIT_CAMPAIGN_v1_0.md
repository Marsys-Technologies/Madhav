---
artifact: PRE_REGEN_FULL_AUDIT_CAMPAIGN_v1_0.md
canonical_id: PRE_REGEN_FULL_AUDIT_CAMPAIGN
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
severity: HIGH — the comprehensive correctness gate before regenerating all layers for all charts
purpose: >
  Exhaustive, layer-by-layer audit of EVERY built asset across L0–L4 (~70 assets) on THREE axes —
  code correctness, data correctness (data-engineering), and astrological/classical validity — folding
  in the full NATIVE_BIRTH contamination sweep as one mandatory dimension. Produces a per-asset findings
  register and a derived fix plan, so the subsequent full regeneration runs on code+data proven correct,
  with no fear of contamination of any type. Modeled on the 16-asset L1 audit that worked, scaled to all
  layers.
audience: Claude Code (Antigravity) — executed as a multi-wave campaign
related: NATIVE_BIRTH_CONTAMINATION_SWEEP_ALL_LAYERS_v1_0, feedback-sync-freeze-before-data-generation,
  project-ak-divergence-and-positions-contamination
---

# Pre-Regeneration Full Audit Campaign — L0→L4, code + data + astrology

## §0 — Mission + non-negotiables
Before regenerating all layers for all charts, audit every built asset so we KNOW the code is correct
and the current data's defects are catalogued. This is the gate that earns "regenerate once." It is a
CAMPAIGN (multiple sessions), not a single run — pacing is per-layer wave with a native review gate
between waves.

Scope: **all registered assets L0(bg_) · L1(ga_) · L2(bo_) · L3(ka_) · L4(ph_)** — ~70 assets. (L5
Mīmāṃsā is excluded — it's a calibration/learning layer, audited separately when it closes.)

Rules: read-only audit first per asset (no fixes mid-audit); destructive checks only on non-native
1c826d5a; native 482012f1 read-only + FORENSIC-gated; data plane = prod :5433; FROZEN orchestrator
contract; never fabricate a value, a citation, or a classical rule. Output a findings register that
becomes the fix plan.

## §1 — The per-asset audit rubric (apply to EVERY asset; this is the heart of the campaign)
For each asset, produce a findings row scored on THREE axes. An asset PASSES only if all three pass.

### Axis A — CODE CORRECTNESS
A1. **Contamination sweep (MANDATORY — the NATIVE_BIRTH class).** Does the writer/compute path ever
    fall back to NATIVE_BIRTH / hardcoded 1984-02-05 / `chart_id = CANONICAL_CHART_ID` default for a
    non-native chart? Classify CHART-INDEPENDENT / NATIVE-ONLY-BY-DESIGN / CORRECTLY-GUARDED /
    VULNERABLE per NATIVE_BIRTH_CONTAMINATION_SWEEP_ALL_LAYERS. VULNERABLE = halt-worthy fix.
A2. **Idempotency** — per-chart delete-then-insert scoped to (chart_id × natural key)? A rebuild must
    REPLACE, not accrete (the ga_dashas N==N concern). Confirm against the §N.3 standard.
A3. **Orchestrator-contract conformance** — @register, run(ctx)/substeps, runs on ctx.db_conn, never
    commits, never writes asset_throughput itself, reads chart_id+birth_params from ctx.config.
A4. **L1-authority / no value-restating** (L2+ only) — does the asset RESTATE an upstream computed
    value as its own, or correctly REFERENCE the source fact_id? A restated value that can drift is a
    bug (the MSR drift trap).
A5. **Derivation ledger / source citation** (L2+ interpretive assets) — every claim cites the specific
    upstream fact_ids / classical source it consumes; no "as is known classically" without a source.
A6. **Determinism** — build-time construction is deterministic (Python over LLM; embeddings OK,
    generative curation not). No hidden randomness / wall-clock dependence in the computed value.
A7. **Error handling** — failure is a loud halt or a recorded error, never silent garbage or a
    plausible-but-wrong constant (the degenerate-distribution / `dict.get(k, default)` trap).

### Axis B — DATA CORRECTNESS (data-engineering) — POST-REGEN ONLY (native amendment 2026-06-26)
**SCOPE CHANGE:** the existing/stale data is being fully WIPED and regenerated on the fixed code, so
auditing the about-to-be-discarded data pre-regeneration is wasted effort. Therefore Axis B is NOT run
per-asset pre-regen. Instead it becomes the **post-regeneration acceptance checklist** — the same B1–B7
checks run ONCE against the freshly-regenerated data to confirm the clean build is actually clean.
CONSEQUENCE: with no pre-regen data backstop, Axis A (code) is now the SOLE guarantee against
re-contamination — so the Axis A contamination guard MUST be exhaustive (full bug-class, not one
literal string). A missed vulnerable writer = silently re-contaminated data at regen with nothing to
catch it. The B7 isolation check is additionally kept as a mandatory POST-REGEN spot-check (see §4).

B1. **Cockpit-count truth** — asset_registry.count_sql is chart-scoped and correct; the displayed
    count == a live COUNT of the asset's actual rows.
B2. **Row-count sanity** — actual rows vs target_floor / expected order of magnitude; not silently
    zero, not implausibly low/high.
B3. **Distribution check** — no degenerate collapse (a column that should vary pinned to one value —
    the all-Jupiter kala_convergence bug). Spot the attribution columns and verify diversity.
B4. **Null / completeness** — required fields populated; null rates sane; no truncated builds.
B5. **Duplicates / natural-key integrity** — no dup rows on the natural key; fact_id/citation_ref
    resolve.
B6. **Cross-asset referential integrity** — constituent_facts_array / depends_on references resolve to
    real upstream rows (no dangling fact_ids).
B7. **Per-chart isolation** — a chart's rows contain THAT chart's data (the contamination data-check:
    e.g. non-native Sun ≠ native's Sun). Run for every chart that has data.

### Axis C — ASTROLOGICAL / CLASSICAL VALIDITY
C1. **Rule fidelity** — the computed value matches the classical rule the asset claims to implement
    (e.g. AK = highest degree-in-sign with the CORRECT school reckoning — the KN Rao Rāhu-reverse bug).
    Re-derive a sample by hand / from the cited source.
C2. **Canonical-value discipline** — stores the canonical cited value OR floors NULL+reason; never a
    non-canonical computable substitute (the graha-yuddha-by-longitude trap).
C3. **FORENSIC consistency** (native) — values trace consistently to the 7 birth anchors; nothing
    contradicts Sun=Capricorn / Moon=PuBha / Lagna=Aries etc.
C4. **Cross-system coherence** — where multiple schools/ayanāṁśas are emitted, the divergences are
    real doctrine, not computation artifacts (the AK-divergence lesson). Both-school emission where
    required (esoteric-AK).
C5. **Spot re-derivation** — for each asset, hand-verify at least 1–2 representative rows end-to-end
    against the source. Acharya-grade: would a senior Jyotiṣa reviewer accept this value?

## §2 — Wave structure (layer by layer; gated)
Each wave = one layer, audited asset-by-asset on **Axis A (code) + Axis C (astrology) only** — Axis B
data checks are POST-REGEN (see Axis B banner + §4), since the stale data is being discarded. The
per-wave focus notes below that say "heavy on B" now mean: that B-dimension is a POST-REGEN acceptance
priority for that layer, NOT pre-regen work. Native reviews each wave's register before the next.

- **Wave 0 — Shared compute + harness (do FIRST).** Audit the cross-cutting compute every layer
  depends on: `pyjhora_adapter/compute.py`, `panchanga_writer.py`, `birth_params.py`,
  `routers/pyhora.py`. A bug here contaminates ALL layers, so it gates everything. Also stand up the
  audit harness: the per-asset query templates (count, distribution, null, dup, isolation) + the
  findings-register schema.
- **Wave 1 — L0 Brahmagyan (~22 bg_ assets).** Mostly chart-independent reference data — but that's a
  hypothesis to verify per A1, not an assumption. Heavy on B (data integrity of reference corpora) +
  C (classical-source fidelity of rules/texts/dignity/medical mappings).
- **Wave 2 — L1 Gaṇita (~16 ga_ assets).** The computational core. Re-audit even the already-fixed
  ones (ga_positions, ga_sensitive) on all 3 axes + the 14 others. Heavy on C (rule fidelity per
  asset) + A2 (idempotency, esp. ga_dashas).
- **Wave 3 — L2 Bodha (~11 bo_ assets).** Synthesis layer — heavy on A4 (no value-restating),
  A5 (derivation ledger), B6 (referential integrity into L1), C4 (cross-system coherence).
- **Wave 4 — L3 Kāla (~11 ka_ assets).** Temporal — heavy on C1 (dasha/transit rule fidelity),
  A1 (the ka_ writers take birth-time inputs — prime contamination suspects), B3 (the degenerate-
  distribution bug lived here).
- **Wave 5 — L4 Phala (~11 ph_ assets).** Applied/prediction — heavy on A1 (l4_anchors native-hardcoded
  confirmed; audit all ph_ for the same), A5 (citation discipline; the LEL-leak class), C5.

Per wave DELIVER: the layer findings register (one row per asset × 3 axes × pass/fail + evidence +
severity) + the per-asset VERDICT (PASS / FIX-REQUIRED) + a fix-list extract. STOP for native review.

## §3 — Findings register schema (the durable artifact)
One row per asset:
`asset_id | layer | A1 contamination class | A2..A7 (pass/fail+note) | B1..B7 (pass/fail+metric) |
C1..C5 (pass/fail+evidence) | OVERALL VERDICT | severity (blocker/major/minor) | fix summary | fix
owner-phase`.
Maintain it as a single living doc (e.g. PRE_REGEN_AUDIT_FINDINGS_REGISTER_v1_0.md) appended per wave.
This register IS the deliverable that becomes the fix plan (mirrors how the 16-asset L1 audit produced
its fix plan).

## §4 — From findings → fixes → regeneration (the gate)
1. After all waves: consolidate the register. Group fixes by severity (blocker / major / minor) and by
   code-fix vs data-only (data-only defects are mooted by regeneration; code-fixes are not).
2. Author a FIX PLAN from the register (separate brief) — every blocker + major CODE defect fixed,
   tested, committed; contamination guards (A1) + the structural guard from the contamination sweep in
   place; CI green; Cloud Run job image rebuilt to carry all fixes.
3. RE-PROVE main==prod (web + job image == main HEAD, all fix commits ancestors).
4. ONLY THEN regenerate all layers for all charts on the proven image. Data-only defects need no
   pre-fix — they vanish in the clean rebuild.
5. POST-REGEN acceptance (Axis B runs HERE, once, on the fresh data): run the B1–B7 checks against the
   regenerated data. MANDATORY among these is the **B7 per-chart isolation spot-check** — confirm a
   non-native chart's regenerated rows carry ITS OWN values, not the native's (e.g. Abhinandan's Sun =
   his ~318° Aquarius, NOT the native's 292° Capricorn), on at least one asset per layer. This is the
   end-to-end proof that "fix code → regenerate → clean data" actually held. A B7 failure here means a
   vulnerable writer was MISSED by Axis A → halt, find it, fix, regenerate the affected asset.
GATE: regeneration does not start until every blocker/major CODE finding is fixed + verified live and
the contamination structural guard is in place AND EXHAUSTIVE (full bug-class, not one literal pattern).
RATIONALE: with the pre-regen data audit dropped (native amendment — stale data is discarded), Axis A
is the SOLE pre-regen guarantee against re-contamination; the post-regen B7 spot-check (step 5) is the
only backstop, so it is mandatory, not optional.

## §5 — Pacing + governance
- This is a multi-session campaign. Each session = one wave (or a sub-wave for the big layers). Open a
  campaign tracker (PRE_REGEN_AUDIT_CAMPAIGN_TRACKER) listing waves, status, and the per-wave register
  link, updated at each session close.
- Re-use the orchestrator's own dependency graph (asset_registry.depends_on) to order intra-layer
  audit (audit an asset after its upstreams, so referential checks have a verified base).
- The contamination sweep (NATIVE_BIRTH_CONTAMINATION_SWEEP_ALL_LAYERS) is SUBSUMED here as Axis A1 —
  run it as part of Wave 0 (shared) + each layer wave, not as a separate effort; its structural guard
  (single resolve_birth_params helper + CI grep test) is a Wave-0 deliverable.
- Parked (not in this campaign): the "remove runtime native concept" architecture refactor. A1 tags
  NATIVE-ONLY-BY-DESIGN assets as de-native candidates; the refactor itself is deferred per native.

## §6 — Deliverables summary
- Wave 0: shared-compute audit + harness + findings-register schema + the contamination structural
  guard.
- Waves 1–5: per-layer findings register (every asset × 3 axes).
- Consolidated register → FIX PLAN → fixes → job-image rebuild → main==prod re-proof.
- Post-regen acceptance checklist (the B/C rows) to confirm the clean data passes what the stale data
  failed.
GUARDRAILS: read-only audit before any fix; destructive checks on 1c826d5a only; native 482012f1
read-only+FORENSIC; no fabricated values/citations/rules; acharya-grade bar on Axis C; regeneration
gated on all blocker/major CODE fixes live + contamination guard in place.
