---
artifact: CLAUDE_CODE_PROMPTS_L0_L4_AUDIT.md
canonical_id: CLAUDE_CODE_PROMPTS_L0_L4_AUDIT
version: 1.0
status: READY — five per-layer paste-prompts for the L0→L4 soundness audit. Run bottom-up. ASSESS ONLY, NO FIX, NO SEAL.
authored_by: Cowork 2026-06-22
spec: L0_L4_SOUNDNESS_AUDIT_SPEC_v1_0.md
---

# L0→L4 Soundness Audit — Per-Layer Claude Code Prompts

> Run BOTTOM-UP: L0 → L1 → L2 → L3 → L4, one session each. Each completes its layer, reports, then you
> decide before the next. ASSESS ONLY — never fix, never seal. After each, send the report back to Cowork.
> The shared method is in §A; the per-layer specifics in §B (paste the layer's block + the §A preamble).

---

## §A — SHARED PREAMBLE (prepend to every layer prompt)

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Run a SOUNDNESS AUDIT of one
layer's assets. **READ FIRST:** `00_ARCHITECTURE/CONDUCTOR/audit/L0_L4_SOUNDNESS_AUDIT_SPEC_v1_0.md` (the
governing framework — §3 lenses, §4 detection patterns, §5 audit unit). **ASSESS ONLY — do NOT fix any
bug, do NOT change any code/data, do NOT seal.** Report findings + traced evidence; fixes are the native's
separate decision.

You hunt the "plausible-but-wrong" bug class: code that produces a sensible-LOOKING answer that passed
tests + lit the cockpit green while being WRONG (silent-`'Jupiter'`, Capricorn ascendant, empty-catch
0-rows, vocabulary drift, stubs). Tests can't catch these — look at ACTUAL VALUES + the CODE LOGIC.

**Method per asset (the §5 unit — STRATIFIED SAMPLE, not 2 cherry-picked rows):**
> Two hand-picked rows mislead: they might be the two that WORK, and 2 rows can't show a DISTRIBUTION bug
> (all-Jupiter is invisible in any 2 rows). Sample must be REPRESENTATIVE + REVEALING. The LOGIC is the
> subject; the sample is the probe — but it must be a probe that can't be fooled by a lucky pair.
1. **DISTRIBUTION CENSUS FIRST (whole column, all rows — not a sample):** for each meaningful column,
   `SELECT col, count(*) FROM <table> WHERE chart_id='482012f1-...' GROUP BY col ORDER BY 2 DESC`. Highest-
   value check — catches the degenerate-value class instantly (~1 distinct where many expected = the
   silent-Jupiter signature) AND auto-detects the categories (low-cardinality columns) for step 2.
2. **STRATIFIED ROW SAMPLE (~8-12 rows, cutting across the axes the census exposed):**
   - **Random 3-4** (`ORDER BY random() LIMIT 4` — rows nobody designed to work);
   - **Extremes 2** (strongest + weakest score; + the empty/null case if any — bugs live at boundaries);
   - **One per AUTO-DETECTED category** (from step 1's low-cardinality column(s) — one row of EACH
     signature_class / domain / lord / varga). THIS catches per-category bugs a random sample misses (the
     ka_sangam per-signature bug only emerged when DOSHA/DIGNITY/YOGA were separated). Self-scaling.
   - **Anchor 1-2** (rows tied to a known-correct answer — FORENSIC Lagna, a known life event).
3. **Read the writer** (`pipeline/orchestrator/writers/<asset>.py` + `services/<asset>/`) — trace the logic.
4. **Independently re-derive** what the sampled rows SHOULD be from `depends_on` upstream — compute from
   inputs, don't trust the asset's own output.
5. **Three lenses across the whole stratified sample** (so you see PER-CATEGORY, not just per-row):
   (a) data-engineering (shape, nulls, cited upstream ids RESOLVE, count, key unique); (b) astrological —
   summary + YOU judge classical coherence ACROSS categories (Lagna/dignity/dāśā-seq/yoga/remedy-fit);
   (c) faithfulness — does each row inherit its upstream value or restate/mutate it?
6. **TWO aggregate checks no row sample replaces (whole column):** null-rate per column (100% null = gap;
   0% where nulls expected = a fallback filling them); FK/inheritance resolution RATE (do ALL cited
   upstream ids resolve — the %, not just sampled ones?). + row-count sanity from the census.
7. **Silent-default code scan:** grep the writer for `.get(key, <constant>)` fallbacks + bare
   `except: return [default]/None` — the mechanism behind degenerate data. Flag every one.
8. **Verdict per asset:** `SOUND` / `SUSPECT` / `BROKEN` + the census + traced stratified evidence + the
   re-derivation. **Where a finding is AMBIGUOUS (a value is uniform/null — could be computed-WRONG or
   not-yet-COMPUTED), the re-derivation MUST settle which of THREE it is:**
   - **WRONG** — the logic computes a value, and it's incorrect (a real bug). → see fix-drafting below.
   - **DEFERRED** — the column is a deliberately-unpopulated stub (a scoring/graph stage built later, by
     design). NOT a bug — confirm it's intentionally deferred (check the writer + any TODO/phase marker),
     classify as DEFERRED, do NOT draft a fix.
   - **SOUND** — the uniformity/null is actually correct (e.g. all rows genuinely share the value).
   The CGM #3 (all strength=0.506) + resonance #4 (all 0.28) are the archetypal ambiguous cases — the
   re-derivation (does the writer ATTEMPT to differentiate and fail, or never attempt?) is what classifies them.

**FIX-DRAFTING (only for WRONG; keep it SEPARATE from assessment):** for any asset classified WRONG, ALSO
draft the fix SCOPE inline — root cause + the change-points + which lens it failed — but **do NOT apply it**
(assess-only stands). DEFERRED + SOUND get the classification only, no fix draft. Keep the draft clearly in
a "PROPOSED FIX (not applied)" subsection so assessment ≠ fix is never blurred — the re-derivation EVIDENCE
must precede any fix draft (no "looks wrong → here's a fix" without the proof in between).

**DOWNSTREAM-IMPACT CHAIN (for every asset classified WRONG — native-mandated; this makes the report an
executable fix plan, not just a bug list):** record the COMPLETE TRANSITIVE set of assets that depend on
the broken one (directly + indirectly, all layers up) → everything that must REBUILD once it's fixed.
- Compute the transitive downstream closure from the registry `depends_on` (reuse `src/lib/build/plan.ts`
  transitiveDownstream / `asset_runner.py` compute_downstream_closure — do NOT hand-roll graph code).
- **VERIFY EACH declared edge against what the writer ACTUALLY READS** (grep the writer's FROM/joins/reads).
  depends_on has been WRONG before (bo_laksana declared bg_rules/ga_structural but reads only chart_facts).
  Flag: OVER-DECLARED edges (declared, not read — harmless but note) and UNDER-DECLARED edges (READ but NOT
  declared — DANGEROUS: a hidden dependency the cascade would MISS, leaving stale data). The under-declared
  ones are findings in their own right.
- Output per WRONG asset: "fixing <asset> requires rebuilding (in dependency order): [the verified
  transitive downstream list]" + any edge corrections found.

**Rails:** read-only (no writes, no fixes APPLIED — drafts are text only); verify against live prod data via
the Cloud SQL proxy; Gemini/DeepSeek + Claude-in-Code for the astrological judgment (dev-time review,
allowed — NOT a runtime instrument call); FORENSIC anchors = Sun Capricorn · Moon Purva Bhadrapada · Lagna
Aries (×5 ayanamshas) · Tithi Shukla Tritiya · Vara Ravivara · Yoga Shiva · Karana Garaja.

**Complete the WHOLE layer, then write `L<n>_SOUNDNESS_REPORT.md`** (per-asset verdict
SOUND/SUSPECT/BROKEN/+WRONG/DEFERRED classification for ambiguous ones + evidence + re-derivation + any
PROPOSED-FIX drafts + the single most important finding + the layer tally). A BROKEN asset does NOT block
its siblings. **STRICT GATE: do NOT proceed to the next layer — STOP and report. The native + Cowork review
this layer's report and decide before the next layer runs** (a foundational finding may change how the
layer above is read).

---

## §B — PER-LAYER BLOCKS

### LAYER 0 — Brahmagyan (22 assets) — THE FOUNDATION
Audit all 22 bg_* assets. Most are ROOTS (no upstream) → check against the CLASSICAL SOURCE + internal
consistency, not an upstream asset. Priorities: `bg_ephemeris` (the planetary positions everything rests
on — spot-check a few dates against an independent ephemeris; this is the deepest foundation), `bg_rules`/
`bg_texts`/`bg_text_index` (classical rule corpus — do citations resolve to real texts?), `bg_yogas`/
`bg_doshas`/`bg_dasha_systems`←ontology (do the definitions match classical sources?), `bg_transit_rules`
(feeds ka_yojaka — the rules ka_sangam evaluates), `bg_nakshatra`/`bg_dignity_reference`/`bg_medical_*`/
`bg_vastu_directions` (reference tables — sample for correctness vs classical). Degenerate-distribution +
silent-default scan on each. The foundation MUST be confirmed sound — everything above inherits it.

### LAYER 1 — Gaṇita (16 assets) — THE COMPUTED CHART (re-derive vs chart_facts + FORENSIC)
`ga_positions` (root) FIRST — re-derive the native's planet+Lagna positions; MUST match the 7 FORENSIC
anchors (this is where a Capricorn-class bug would live). Then the position-derived: ga_vargas, ga_dashas
(the dāśā sequence — confirm lords are in correct Vimśottarī order, not collapsed), ga_strength, ga_sensitive,
ga_panchanga (vs FORENSIC Tithi/Vara/Yoga/Karana). Then ga_structural (the big relational asset — many
depends_on; check its inherited values resolve). Then ga_condition/yoga/vastu/medical/tajaka/sade_sati.
Re-derive each against chart_facts; degenerate-distribution scan (a dignity or sign column collapsed to one
value = smell); silent-default scan.

### LAYER 2 — Bodha (10 assets) — SYNTHESIS (faithfulness to L1 + the known CDLM drift)
`bo_laksana`←(ga_structural+bg_rules) FIRST — it's L2's root; confirm it faithfully projects L1 (the
L-is-authority check — does it reference ga_structural fact_ids or restate values?). Then the laksana-
derived. **`bo_sangati` — AUDIT THE CDLM VOCABULARY EXPLICITLY** (known drift: `spirituality` vs `spiritual`,
`character` vs `psychological`, `wealth` vs `financial` — confirm whether the fix landed or it's still
divergent; check `KNOWN_DOMAINS` line ~42 + the stored bodha_cdlm_cells domain labels). bo_upaya (remedies),
bo_drishti, bo_anveshana, bo_pramana_mapa. Faithfulness lens is primary here — L2 must inherit L1 truthfully.

### LAYER 3 — Kāla (12 assets) — TEMPORAL (ka_sangam known-BROKEN; audit siblings + seams)
**`ka_sangam` is KNOWN BROKEN (silent-Jupiter; per-signature fix in flight) — note it as BROKEN-in-fix, do
NOT re-litigate, but DO audit whether its sibling/downstream assets inherited the bad data.** Audit
`ka_yojaka` (builds the predicates — confirm transit_trigger rule specs are well-formed + the signature
classes are correct), ka_gochara/graha_sancara (the transit events — do they carry real varied planets, or
another degenerate set?), ka_dasha_kala, ka_muhurta_seva, ka_vighnakara (←sangam — inherited the Jupiter
collapse? confirm), ka_kalasutra/kala_darshana/jivana_parva (the null-score history — are scores now
populated + sensible?)/bhavishya_lekha/tulana. Degenerate-distribution scan is HIGH-yield in this layer
(it's where the planet/window collapse lives).

### LAYER 4 — Phala (9 assets) — PREDICTION (re-audit after the ka_sangam fix lands)
**Re-audit ph_pratikara + ph_sankrama AFTER the ka_sangam per-signature fix + rebuild (they're downstream
of the broken convergence — their current data is suspect).** Audit ph_nimitta (the spine — 8 axes + 5
elevations; does it faithfully consume ka_sangam + bo_*? the all-Jupiter would surface here too),
ph_muhurta, ph_sodhana (anomaly registry — sound?), ph_suddha_sodhana, ph_rectification (the JD-fix landed
— confirm Aries-stable candidates, auto_action='stage_for_review', chart unmutated), ph_pramana
(falsifiability, NO calibration column — confirm the D5 boundary holds), ph_phaladesa (composer — does it
faithfully compose its 6 upstream assets?). Faithfulness lens primary; confirm the L4/L5 boundary (no
scoring in L4).

### GATE A — CONSOLIDATION + MASTER REBUILD SCHEDULE (after all 5 layer reports; the Phase-B spine)
> Paste this as its own session AFTER L0–L4 reports exist. It builds the executable fix sequence.

You are Claude Code in Antigravity on MARSYS-JIS. All five L<n>_SOUNDNESS_REPORT.md exist. Consolidate them
into `00_ARCHITECTURE/FOUNDATION_ROOT_CAUSE_MAP.md` — the complete, certain picture that Phase B executes.
READ-ONLY; assess + plan only; fix nothing; seal nothing.

1. **Collate every confirmed-WRONG asset** across all 5 reports (+ the 3 already-diagnosed convergence
   bugs: eligibility-NULL, fact_value_num overload, YOGA crowd-out). For each: the data-proven root cause,
   its root-cause FAMILY (F1–F8 per FOUNDATION_INTEGRITY_CAMPAIGN §4), and its VERIFIED downstream-impact
   chain (the transitive rebuild set, with the edge-corrections each layer flagged).
2. **Build the dependency graph of WRONG assets + their downstreams**, using the VERIFIED edges (apply the
   under-/over-declared corrections the layer audits found — NOT the raw registry depends_on if it was
   wrong). Reuse plan.ts transitiveDownstream + topoSort; do not hand-roll.
3. **Compute the MASTER REBUILD SCHEDULE** — the wave plan Phase B runs:
   - Each WRONG asset + each transitive-downstream gets a "READY-TO-REBUILD WHEN: [all these upstream fixes
     complete]" condition. A downstream depending on 2+ broken upstreams waits for the LAST.
   - Topologically order into WAVES: Wave N only contains assets whose every broken-upstream was fixed+
     rebuilt in waves < N. Independent broken assets (no shared dependency) go in the SAME wave (parallel-safe).
   - Flag: (a) single fixes that trigger LARGE downstream rebuilds (cost/time); (b) parallel-safe groups;
     (c) any cycle or contradiction in the graph (should be none — flag if found).
4. **Group WRONG findings by root-cause FAMILY** so Phase B can fix a pattern once across assets (e.g. all
   F1 degenerate-uniform fixes together) where the family fix is shared.
5. **Output FOUNDATION_ROOT_CAUSE_MAP.md:** the family-grouped root-cause list (data evidence per finding),
   the interconnection diagram (which upstream bug causes which downstream symptom), and the MASTER REBUILD
   SCHEDULE as an ordered "Wave 1: fix [..] → rebuild closure [..]; Wave 2: fix [..] (was waiting on Wave 1) …"
   that the Phase B session executes top-to-bottom with zero sequencing guesswork. Plus an explicit list of
   the depends_on EDGE CORRECTIONS to apply (the under-declared hidden deps especially). NO fix, NO seal. STOP.

---
*End. Five layer audits, bottom-up, shared method (§A) + per-layer focus (§B). Logic-vs-data on the
stratified sample/asset, three lenses, degenerate + silent-default scans, PER-WRONG-ASSET downstream-impact
chains (edge-verified), assess-only, full-layer-then-report → Gate-A consolidation builds the
FOUNDATION_ROOT_CAUSE_MAP + MASTER REBUILD SCHEDULE (the Phase-B execution spine). Produces
five L<n>_SOUNDNESS_REPORTs → the pre-L5 confidence gate.*
