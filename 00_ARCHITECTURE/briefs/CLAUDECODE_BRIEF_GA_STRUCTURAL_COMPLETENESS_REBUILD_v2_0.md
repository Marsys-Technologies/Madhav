# ga_structural — Completeness Rebuild (LOCKED LOGIC, v2.0) — paste into Claude Code / Antigravity

**Read CLAUDE.md §C first + memory `feedback-ga-structural-rebuild-locked-logic` (the GOVERNING spec — all native
decisions, build to THIS), `feedback-three-tier-relational-boundary`, `feedback-ga-structural-pure-relational-
generator`, `feedback-canonical-or-floor-rule`.**

ga_structural is the relational hub the ENTIRE L2 Bodha layer reads. A deep audit found 77,821 is BOTH too low
(threshold-drops, ingest gaps, ~half the depth layer D1-only) AND partly spurious (contradiction_pair inflation).
The native ruled: **get the LOGIC correct first → then rebuild the code → then rebuild the data (data rebuild is
fine; COMPLETENESS is the priority).** This supersedes the "ga_structural COMPLETE" claim and
`CLAUDECODE_BRIEF_GA_STRUCTURAL_COMPLETENESS_REMEDIATION_v1_0.md`.

**SEQUENCING IS MANDATORY: STEP 0 (logic, cited) is a GATE — no code changes until STEP 0 is approved.**

## STANDING RAILS
no-threshold-drop (weak/wide CAPTURED with salience, never filtered); L1-is-authority §N.5 (reference source
fact_id, never proxy a computed value); three-tier boundary (2+ entities + fixed rule + NO life-meaning =
ga_structural; meaning = L2); canonical-or-floor; FROZEN orchestrator contract (HALT if change seems needed —
this is writer-internal, not orchestrator); per-chart delete-then-insert idempotency; floors = ACHIEVED
(recalibrate after, NEVER fabricate to a target); verify by PER-CATEGORY breakdown + ACHARYA hand-checks, NOT raw
count; only 482012f1; FORENSIC 7/7.

---

## STEP 0 — LOGIC FIRST (CITED) — GATE: produce `GA_STRUCTURAL_REBUILD_LOGIC_v1_0.md`, native approves BEFORE any code

No writer edits until this doc is approved. It must contain:

### 0.1 — Aspect re-derivation (cited, all 5 graha sets) — the native's #1 concern
Re-derive from **BPHS Ch.7** (cite verses), graha by graha, the special aspects (beyond the universal 7th):
- Mars: 4th + 8th · Jupiter: 5th + 9th · Saturn: 3rd + 10th · Rahu/Ketu: 5th + 7th + 9th · all grahas: 7th.
Prove the writer's canonical `PARASHARI_ASPECTS` (L414-428) MATCHES the cited rule graha-by-graha (it appears
correct: Mars{4,7,8}, Jup{5,7,9}, Sat{3,7,10}, nodes{5,7,9}). Then DOCUMENT that `_build_sambandha_rows`
(~L4347) and `_build_bhava_web_rows` (~L4579) use WRONG private tables (Jup{4,6,8}/Sat{2,6,9}) and the fix is to
collapse BOTH onto the single canonical helper — NOT to redefine aspects. Confirm there is exactly ONE
aspect-offset source in the file after the fix (grep for any other private offset literals). **Do not write code
in Step 0 — just prove the table + locate every divergence.**

### 0.2 — Per-varga applicability table (ALL 30 VARGAS, NO EXCEPTIONS — native ruling)
List EVERY relationship type the writer computes (~30 `_build_*` outputs). The native ruling is **ALL 30 vargas,
no exceptions** — every type recomputed from EACH varga's OWN computed positions (chart_divisionals has real
per-varga longitudes; recompute, do NOT project D1). For each type, state the varga-space computation basis.
- graha-yuddha + combustion: RECOMPUTE in varga space from divisional longitudes (native chose recompute, not
  project — divisional longitudes are real computed values, so this is deterministic, not fabrication).
- **combustion orbs:** apply the SAME classical per-planet orbs (Moon 12°, Mars 17°, Mercury 14°/12°R,
  Venus 10°/8°R, Jupiter 11°, Saturn 15°) measured against the Sun's VARGA longitude. **DOCUMENT this as an
  explicit modeling assumption** — classical texts define combustion orbs in D1; applying them in varga space is
  a consistent-but-assumed extension, not directly blessed by a cited verse. State it as an assumption, not
  settled tradition.
- AMBIGUOUS varga-applicability → DEFAULT to compute + LOG the assumption in this doc (don't halt).
This table is the per-varga build plan; it must show the expected category × varga matrix so the post-rebuild
per-category breakdown can be checked against intent.

### 0.3 — The drop/inflation ledger
Enumerate every `continue`/`return None`/orb-gate/dedup in the writer (the audit found these; re-confirm against
live code with line numbers): classify each KEEP (true non-relationship: self-loop, definitional) vs REMOVE
(silent drop). Specifically: per-varga conjunction >10° drop (~L3388) → REMOVE, emit to 30° graded + salience;
Tajik >30° drop (~L1043) → REMOVE, emit low-salience. And the contradiction_pair definition (~L5159) → redefine
to genuine same-ENTITY + same-VARGA + opposing-valence-on-SAME-relationship-type (count will DROP — correct).

### 0.4 — Ingest-gap closure plan (GAP 1-4) + WHY they happened
Document the closure for each, citing the exact chart_facts categories to read + where to reference:
- GAP-1: extend `_load_special_points` (~L2967/L2985, currently 3 cats) to the full sensitive-point family:
  special_lagna, arudha_pada(~285), saham_position(~2,800), esoteric_point_*, saturn_derived_point,
  aprakasha_position — each a relationship participant.
- GAP-2/3: replace inline proxies (`dignity_to_strength` L2136, `shadbala_proxy` L2148, `bhava_bala_proxy`
  L2130) with REFERENCES to per-varga ga_strength (ashtakavarga_bindu_per_varga, graha_*_bala_per_varga) +
  per-varga ga_condition fact_ids. Add `ga_condition` to seed `depends_on` (currently missing).
- GAP-4: reference ga_nakshatra's canonical dispositor chain (not recompute; L4419 diverges).
- ROOT-CAUSE note (native asked): GAP 1-4 were known + deferred in FOUNDATION_COMPLETION_HANDOFF §3, but the
  "ga_structural COMPLETE" seal was applied to the maximal-DEPTH half while the maximal-INGEST half stayed open.
  Document the sealing-discipline lesson (don't seal an asset on half its scope).

### 0.5 — Phase-3 blind-spot designs (ALL across 30 vargas, same rule)
Design (logic + chart_facts sources + varga treatment) for: virupa-graded drishti (continuous BPHS Ch.7 graded
aspect, not boolean); bhinnashtakavarga inter-graha contribution edges; nakshatra co-tenancy + tara +
nakshatra-lord relationships (read `graha_nakshatra_join`, currently unread); bhava-chalit-vs-rasi divergence
flag; significator path-analysis (shortest/all-paths — in spec §2.5/§6, currently UNimplemented).

**GATE: native reviews `GA_STRUCTURAL_REBUILD_LOGIC_v1_0.md` and approves before STEP 1.**

---

## STEP 1 — CODE (only after Step 0 approved) — implement the locked logic

1. **Aspects:** collapse `_build_sambandha_rows` + `_build_bhava_web_rows` (and any other private offset table found
   in 0.1) to call the single canonical aspect helper. ONE aspect source in the file. Fix combustion var bug
   (~L2531 `360-sun_long`→`360-sun_dist`); unify the two divergent combustion computations on the correct one.
   Resolve dead Jaimini sign-type branching (~L943) per 0.2.
2. **All-30-varga expansion:** extend EVERY relationship builder to recompute per-varga from divisional positions
   (the per-varga loop exists at `_build_varga_aspect_rows` L3713 — bring the D1-only builders into it: sambandha,
   bhava-web, net-argala, graph-theoretic centrality/COG, dispositor-tree, n-way, graha-yuddha, combustion, AND
   the Phase-3 additions). Each varga row recomputed from that varga's own positions per the 0.2 table.
3. **No-threshold-drop:** remove the conjunction >10° and Tajik >30° drops; emit graded + a `salience` column.
4. **contradiction_pair:** redefine per 0.3 (same entity + same varga + opposing valence on same type).
5. **GAP 1-4:** implement the 0.4 closures — full sensitive-point ingest; proxies → per-varga ga_strength/
   ga_condition fact_id references (L1-authority — constituent_facts_array must RESOLVE to real fact_ids);
   ga_nakshatra canonical chain reference; add ga_condition to depends_on.
6. **Phase-3 blind spots:** implement the 0.5 designs across 30 vargas.
7. Idempotency: per-chart delete-then-insert (rebuild REPLACES). FROZEN orchestrator contract untouched (HALT if
   a writer-contract change seems needed). Recalibrate target_floor to ACHIEVED after rebuild.

---

## STEP 2 — DATA REBUILD + VERIFY (per-category + acharya, NOT raw count)

Rebuild ga_structural for 482012f1. Produce `GA_STRUCTURAL_REBUILD_VERIFY_v2_0.md`:
- **PER-CATEGORY row breakdown** (GROUP BY fact_category) vs the 0.2 expected category × varga matrix — every
  type appears for every applicable varga; flag any category that DIDN'T expand to 30 (a missed varga = a bug).
- **contradiction_pair DROPPED** to a genuine count (de-inflated) — show before/after.
- **No-threshold-drop audit:** grep remaining `continue`/`return None`/orb-gates; each is a true non-relationship.
- **L1-authority:** sample proxy-replaced rows — constituent_facts_array resolves to REAL ga_strength/ga_condition
  fact_ids (zero proxies remain).
- **GAP-1:** a saham + an arudha now participate in ≥1 relationship each (show the rows).
- **ACHARYA hand-checks (correctness):** a 5th/7th/9th sambandha aspect fires at the correct house in BOTH
  sambandha + bhava-web (the fixed builders); Jupiter final-dispositor still holds; a combust planet >180° from
  Sun is now correct; one per-varga sambandha (e.g. D9) computed from D9 positions verified by hand.
- FORENSIC 7/7; floor = ACHIEVED; FROZEN contract untouched. PR with the per-category before/after table + the
  acharya checks + the Step-0 logic doc linked in the body.

**L2 Bodha opens ONLY after this lands (native: all phases 0-3 before L2).** The expected count is well north of
77,821 (the all-30-varga expansion + GAP-1 entities), MINUS the de-inflated contradiction_pairs — but the NUMBER
IS NOT THE GOAL. Per-category correctness + acharya-verified relationships are. A higher number with spurious
rows is worse than a correct lower one.
