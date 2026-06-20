# ga_structural — Completeness Remediation (the L2-critical relational hub) — paste into Claude Code

**Read CLAUDE.md §C first + memory `feedback-three-tier-relational-boundary`, `feedback-ga-structural-pure-relational-generator`, `feedback-canonical-or-floor-rule`.**
A deep audit of the live 5,349-line `ga_structural_writer.py` (against the ingest map + maximal-depth spec) found
the 77,821-row count is **NOT complete**: genuine threshold-drops, the GAP-1..4 ingest gaps still mostly open,
~half the Phase-2 depth layer running D1-only, AND a likely-spurious `contradiction_pair` inflation masking the
undercount. ga_structural is the relational substrate the ENTIRE L2 Bodha layer reads — fix before L2 opens.
This brief is PHASED: correctness fixes first (some of the 77,821 rows are WRONG), then completeness expansion,
then the integrity (proxy→fact_id) fix. **VERIFY each phase via the per-category row breakdown + acharya
hand-checks — NOT "tests pass" and NOT a raw count delta (a higher number with spurious rows is worse).**

## STANDING RAILS
no-threshold-drop (weak/wide relationships are CAPTURED with a salience/strength column, NEVER filtered);
L1-is-authority §N.5 (reference the source fact_id, never restate/proxy a computed value); three-tier boundary
(2+ entities + fixed rule + no life-meaning = ga_structural; meaning = L2); canonical-or-floor; FROZEN
orchestrator contract (HALT if a change seems needed); per-chart delete-then-insert idempotency; floors =
ACHIEVED (recalibrate after, never fabricate); endpoint + per-category verify; only 482012f1; FORENSIC 7/7.

---

## PHASE 0 — CORRECTNESS FIXES (some existing rows are WRONG — fix before adding more)

These don't change the count much but mean current rows carry wrong values. Fix + rebuild + acharya-verify each.

1. **Aspect off-by-one in sambandha + bhava-web (regression of the PR#300 fix).** `_build_sambandha_rows`
   (~L4347-4355) and `_build_bhava_web_rows` (~L4579-4587) use a PRIVATE aspect-offset table
   (Jup/Rah/Ketu `{4,6,8}`, Saturn `{2,6,9}`) that DISAGREES with the canonical `PARASHARI_ASPECTS` (L414-428)
   and the graph-theoretic builder (L4869). PR #300 fixed `_has_aspect`/`_lord_aspects_house` but MISSED these
   two private copies. **Refactor BOTH to call the single canonical aspect helper** — no private offset tables
   anywhere. Acharya-verify a 5th/7th/9th-aspect pair fires at the correct house in sambandha + bhava-web.
2. **Combustion variable bug** `_build_special_state_rows` (~L2530-2531): `if sun_dist > 180: sun_dist =
   360 - sun_long` must be `360 - sun_dist`. Corrupts `is_combust` for any graha >180° from Sun. (The correct
   form exists at L2468-2469 — combust is computed two divergent ways; unify on the correct one.)
3. **Lossy per-varga D1 conjunction orb-drop** `_build_varga_relationship_rows` (~L3387-3388): `if orb > 10.0:
   continue` drops pairs beyond 10°, while the natal path (L972) correctly emits to 30° with graded strength.
   **Remove the drop; emit to 30° with graded strength + a salience column** (no-threshold-drop). Make the two
   conjunction paths use ONE orb policy.
4. **Tajik aspect 30°+ drop** `_build_aspect_rows` (~L1042-1043): `else: continue` drops Tajik pairs wider than
   30°. Emit at low salience instead (spec §2.1). 
5. **Dead-code Jaimini sign-type branching** `_build_aspect_rows` (~L943-948): all three fixed/movable/common
   branches compute the same `offset not in [1,11]`. Either implement the type-dependent Jaimini rasi-drishti
   correctly OR collapse to one branch with a comment that it's the simplified rule — don't leave dead branches
   implying a fidelity that isn't there. (Native decides: faithful Jaimini vs documented-simplified.)
6. **`contradiction_pair` likely-spurious inflation** `_build_contradiction_pair_rows` (~L5159, 1,810 rows —
   largest Phase-2 category). It keys on `fact_subject` across ALL 30 vargas; argala/virodha share `SIGN_N`
   subjects so nearly every sign trivially gets a benefic+malefic source. INVESTIGATE: are these genuine
   contradictions or trivial co-presence? If spurious, tighten the contradiction definition (same entity, same
   varga, genuinely opposing valence on the SAME relationship type) so it reflects real contradictions. A
   smaller-but-true count here is CORRECT even though the number drops. (This is the one place the count should
   go DOWN.)

---

## PHASE 1 — CLOSE THE INGEST GAPS (GAP 1-4: the entity set is truncated + proxies contaminate)

7. **GAP 1 — full sensitive-point entity set.** `_load_special_points` (~L2967/L2985) reads only
   `upagraha_position`, `sensitive_point_gulika_mandi`, `sun_derived_upagraha`. EXTEND to read the rest of the
   spatial sensitive-point family that exists in chart_facts: `special_lagna`, `arudha_pada` (~285 rows),
   `saham_position` (~2,800 rows!), `esoteric_point_*`, `saturn_derived_point`, `aprakasha_position`. Each
   becomes an entity that participates in aspect/conjunction/house relationships. **This alone unlocks edges for
   ~3,000+ currently-orphaned entity rows** (highest ROI per the handoff). VERIFY: query distinct fact_subject
   in the sensitive-point family, confirm each now appears as a relationship participant.
8. **GAP 2/3 — replace proxies with authoritative fact_id refs (L1-authority, §N.5).** The composite-strength +
   edge-weight builders use INLINE proxies — `dignity_to_strength` (~L2136), `shadbala_proxy` (~L2148),
   `bhava_bala_proxy` (~L2130). These now have authoritative sources: per-varga ga_strength
   (`ashtakavarga_bindu_per_varga`, `graha_*_bala_per_varga`) and per-varga ga_condition
   (`graha_avastha_*_per_varga`). **Reference the real fact_id + inherit its value; stop computing the proxy.**
   Add `ga_condition` to ga_structural's seed `depends_on` (currently missing). This is an INTEGRITY fix (proxy
   rows currently carry non-authoritative values), not just completeness.
9. **GAP 4 — nakshatra-dispositor: reference ga_nakshatra's canonical chain** instead of recomputing from
   longitude (`_build_nakshatra_dispositor_chain_rows` L4419 currently diverges). Reference ga_nakshatra's
   canonical rows so there's ONE chain, not two.

---

## PHASE 2 — PER-VARGA EXPANSION (the largest genuine completeness gain, ~+15-20k rows)

~Half the Phase-2 depth layer runs D1-ONLY. Extend the VARGA-MEANINGFUL builders across the vargas where the
underlying data exists (the per-varga loop already exists at `_build_varga_aspect_rows` L3713 — extend it):
10. **Per-varga sambandha** (`_build_sambandha_rows`) — D9/D10 sambandha is classically central. ~+5,200 rows.
11. **Per-varga bhava-web** (`_build_bhava_web_rows`). ~+5,200 rows.
12. **Per-varga net-argala** (`_build_net_argala_rows`) — the RAW per-varga argala ALREADY exists (L3759); only
    the NET roll-up is D1-only. Asymmetric gap, cheap to close.
13. **Per-varga graph-theoretic** (`_build_graph_theoretic_rows`) — per-varga centrality/COG ("which graha
    dominates the D10 career-graph") is exactly spec §2.5. ~+4,000 rows.
14. **Per-varga dispositor-tree + n-way configs** where varga-meaningful.
**Guard:** only extend builders where the relationship is genuinely varga-meaningful (graha-yuddha is a longitude
phenomenon → stays D1; don't fabricate varga rows for D1-only-meaningful facts). Floor = ACHIEVED after rebuild.

---

## PHASE 3 — BLIND-SPOT ADDITIONS (in-scope deterministic types currently absent — native prioritizes)

Design + (native-approved) build the standard structural types not computed at all:
15. **Virupa-graded drishti** (continuous BPHS Ch.7 graded-orb aspect strength, not boolean house-offset).
16. **Bhinnashtakavarga inter-graha contribution edges** (contributor-graha → sign bindu).
17. **Nakshatra-level relationships** — co-tenancy (two grahas same nakshatra = tighter than same sign), tara,
    nakshatra-lord aspects. (`graha_nakshatra_join` is currently unread.)
18. **Bhava-chalit vs rasi divergence flag** (cusp-based vs whole-sign house assignment difference — a
    deterministic structural fact, currently entirely whole-sign).
19. **Significator path-analysis** (shortest/all-paths between two significators) — in spec §2.5/§6 acceptance
    but NOT implemented; completes Phase-2.
(Phase 3 is the largest design surface — native picks which land now vs post-L2. Each must stay meaning-free:
the NUMBER/relationship is ga_structural; any life-meaning is L2.)

---

## VERIFY (per phase — paste the per-category breakdown, NOT just a total)
- **Per-category row distribution** before/after each phase (GROUP BY fact_category) — show which categories grew,
  which shrank (contradiction_pair SHOULD shrink in Phase 0), which are new.
- **Acharya hand-checks** (correctness, not count): a 5th/7th/9th sambandha aspect fires at the right house; a
  combust planet >180° from Sun is now correct; Jupiter final-dispositor still holds; a saham now participates in
  ≥1 relationship; a proxy-replaced edge now cites a real ga_strength fact_id that RESOLVES.
- **No-threshold-drop audit:** grep the writer for remaining `continue`/`return None`/orb-gates after Phase 0;
  confirm each is a true non-relationship (self-loop, definitional), not a silent drop.
- **L1-authority:** sample Phase-1 rows — `constituent_facts_array` resolves to real chart_facts fact_ids (no
  proxies). 
- floor recalibrated to ACHIEVED; FORENSIC 7/7; FROZEN contract untouched; per-chart idempotency (rebuild
  REPLACES). Then PR with the per-category before/after table in the body.

**Sequence:** Phase 0 (correctness — fix wrong rows + de-inflate contradiction_pair) → Phase 1 (ingest gaps +
proxy→fact_id) → Phase 2 (per-varga expansion) → Phase 3 (blind spots, native-prioritized). Phases 0-2 are the
"is it complete + correct" answer the native asked for; Phase 3 is the "what else could it catch" answer. L2
Bodha should open on the post-Phase-2 (at minimum post-Phase-0/1) hub, not the current one.
