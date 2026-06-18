# ga_structural — REMEDIATION (collapse to one path + finish Phase 1 + fix parivartana, rebuild, re-verify)

**Context:** `GA_STRUCTURAL_DEPTH_VERIFICATION_v1_0.md` → REMEDIATE-FIRST. The Phase-2 depth code exists + passes
unit tests but produces ZERO prod rows because of a DUAL-BUILD-PATH bug: the orchestrator runs
`build_ga_structural` (old) while all 11 depth builders live only in `build_ga_structural_substep` (lines
5287-5329, never called). Also: Phase 1 only partially ran (2 proxy builders + 5 unwired sensitive categories),
and `parivartana_per_varga` has 227 wrong self-parivartana rows in prod. The native ruled: (1) COLLAPSE to ONE
build path (root-cause fix, not a merge), (2) FINISH Phase 1 in the same rebuild, (3) fix the parivartana bug —
then rebuild ONCE + re-run the full verification. Standing rails: FROZEN orchestrator contract (HALT if a change
is needed); L1-is-authority; endpoint-verify (`?chart_id=`); FORENSIC 7/7; the three-tier boundary; floors =
achieved; only 482012f1.

---

## STEP 1 — COLLAPSE TO ONE BUILD PATH (root cause; stay within the FROZEN contract)

ga_structural has TWO paths: `build_ga_structural` (old; what the orchestrator calls) and
`build_ga_structural_substep` (new; where the 11 depth builders live). This dual-path IS the bug. Make the
substep path the SINGLE path:
1. **Confirm the substep path is the FROZEN-contract-correct one.** The frozen contract says HEAVY writers use
   `plan_substeps(ctx)` + `run_substep(ctx, step)`. Read `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2` + the
   ga_structural orchestrator adapter. Confirm `build_ga_structural_substep` is the intended heavy-writer entry
   and the orchestrator SHOULD call it. **If making the orchestrator call the substep path requires ANY change to
   the frozen orchestrator contract → HALT and raise with the native** (the freeze is deliberate). It should NOT
   — this is writer-internal + adapter wiring, not a contract change.
2. **Point the orchestrator at the substep path** (the ga_structural `@register` adapter uses plan_substeps +
   run_substep), and **RETIRE / converge `build_ga_structural`** so only ONE path exists. Move any logic that
   lives only in the old path into the substep path so nothing is lost. After: there is exactly ONE way
   ga_structural builds, and it includes all 11 depth builders.
3. Verify by reading: a single build path, all 22 Phase-1 builders + all 11 Phase-2 depth builders invoked in the
   per-ayanamsha loop of that one path. No orphaned second path.

---

## STEP 2 — FINISH PHASE 1 (reference-not-proxy + all 6 sensitive cats) — so depth computes over the FULL graph

The graph-theoretic depth must compute over the FULLY-REFERENCED graph, not the partial-proxy one. Complete the
2 Phase-1 gaps the verification found:
1. **`_build_shadbala_extension_rows` + `_build_anubindu_rows`:** STOP the inline proxy computation; REFERENCE
   ga_strength's authoritative per-varga Shadbala / ashtakavarga_bindu_per_varga via fact_id (the edge-weights
   come from ga_strength, not a recompute). The relationship row's constituent_facts (in fact_value_jsonb) must
   resolve to real ga_strength fact_ids.
2. **`_load_special_points`:** extend from ONLY `upagraha_position` to ALL 6 enriched ga_sensitive categories.
   (Verification named: gandanta, bhava_sandhi, yoga_karana, nakshatra_boundary as the 4-5 unwired — CONFIRM the
   exact enriched category names on prod by querying ga_sensitive's distinct fact_categories, then wire all of
   them.) `_build_special_point_relationship_rows` then generates the relationships over the complete set.
This matters because Jupiter-final-dispositor happened to verify correct, but centrality/sambandha/net-argala
edge-WEIGHTS depend on the referenced strength values — proxy weights = subtly wrong graph properties.

---

## STEP 3 — FIX the self-parivartana false positives (227 wrong rows in prod)

`_build_varga_relationship_rows` (parivartana_per_varga) flags a planet in its OWN sign as exchanging with itself
(e.g. `D1_JUP_JUP` — Jupiter in Sagittarius own-sign fires a false parivartana). Add the guard `if g1 != lord1:`
(a planet cannot be in parivartana with itself — exchange requires TWO distinct planets each in the other's
sign). The standalone `parivartana_pairs` category is already correct — do NOT touch it. After the fix, the 227
wrong rows are replaced on rebuild (delete-then-insert).

---

## STEP 4 — REBUILD ONCE + RE-RUN THE FULL VERIFICATION

Rebuild ga_structural for 482012f1 via the orchestrator (now the single substep path). Then re-run the 4-part
verification (`GA_STRUCTURAL_DEPTH_VERIFICATION_v1_0.md`), this time expecting PASS:
- **Part 2 (the fix's whole point):** all 14 depth categories now have NON-ZERO rows on prod (sambandha ~36,
  nak-dispositor-chain ~9, dispositor-tree ~10, bhava-web ~36, karaka-concordance ~30, net-argala ~12,
  graph-theoretic ~20, n-way-config, varga-provenance-meta, convergence-count ~21, contradiction-pair). Report
  prod counts. floor recalibrated to achieved.
- **Part 1:** Phase 1 now FULLY ran — the 2 builders reference ga_strength; all 6 sensitive cats wired; one build path.
- **Part 3 (acharya correctness — now the depth rows EXIST to check):** hand-verify against 482012f1 — Jupiter
  final-dispositor still holds; ONE sambandha grade correct (4 components); ONE net-argala house correct; ONE
  cycle is a real loop; NO self-parivartana rows remain (query for any `<X>_<X>` parivartana → expect zero).
- **Part 4:** boundary still CLEAN (the runtime linter still passes; no life-meaning in any new depth row).
- FORENSIC 7/7; endpoint lit/no-error/not-stale; zero duplicate fact_ids on the full prod build.

---

## STEP 5 — CLOSE
Update `GA_STRUCTURAL_DEPTH_VERIFICATION` to PASS (or a v2 with the post-remediation verdicts + prod counts);
update CURRENT_STATE + OPEN_ITEMS; note the dual-path collapse as a permanent fix (so depth can't silently
miss the build path again). FLAG (style, native-decides-later): `karaka_bhava_concordance` uses CAREER/SPOUSE as
SUBJECT-IDS — clean but a smell; rename-or-keep is a native call, not blocking.

**Then ga_structural is genuinely complete to maximal Tier-2 depth, ON PROD, verified — and L2 Bodha can consume
it.** Report back: the single-path confirmation, Phase-1-finished confirmation, the prod depth-category counts,
and the re-run Part-3 acharya spot-checks (especially: zero self-parivartana, sambandha/net-argala correct).
