---
artifact: L4_PHALA_UPSTREAM_COMPLETENESS_FIX_BRIEF_v1_0.md
canonical_id: L4_PHALA_UPSTREAM_COMPLETENESS_FIX_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
purpose: >
  Fix the L4 Phala upstream-completeness bugs found in the L4 coverage audit (Parts A–D). Key
  finding folded in: 3 of 4 fixes DEPEND ON L2 being fixed first — the L4 thinness is largely L2
  damage propagating downstream. So this brief does the L2-INDEPENDENT work NOW and stages the
  L2-DEPENDENT fixes ready-to-apply-after-L2 (specified exactly, not applied against broken upstream).
audience: Claude Code executor
constraints: prod plane :5433; native 482012f1 read-only; FROZEN orchestrator contract; main only.
---

# L4 Phala — Upstream Completeness Fixes

## §0 — The audit verdict (6 of 9 assets SOUND; 2 NO + 1 borderline)
SOUND (no fix): ph_pratikara, ph_phaladesa, ph_sodhana, ph_pramana*, ph_suddha_sodhana, ph_rectification.
BUGS (ranked by upstream signal loss):
1. **ph_sankrama** (line 77–80) — domain-label equality join (`c.domain_row == domain`) silently
   empties matching_cells for any anchor whose L3-derived label (e.g. `career_advancement`) ≠ the L2
   CDLM label (e.g. `career`). ROOT of the 96.5% career skew. ~20–50 spillovers/chart lost.
2. **ph_nimitta** (line 267) — bodha_cgm_paths loaded then DISCARDED (`return {}`). Axis 3
   (causal_chain_jsonb) NULL on EVERY anchor. ~50–200 CGM paths/chart lost.
3. **ph_nimitta** (line 332) — bodha_signal_embeddings LIMIT 50 no-ORDER-BY, loader returns only
   self-reference. Axis 5 (precedent_refs_jsonb) trivial on every anchor. ~500–2,000 neighbors lost.
4. **ph_muhurta** (line 175) — LIMIT 100 ordered-by-confidence; defensible at current size but silent
   if chart outgrows 100 influenceable anchors. Latent, not active.
*ph_pramana soft issue: LEL `domain_primary` vocab vs anchor domain vocab not confirmed normalized —
RESOLVE this (same failure class as ph_sankrama).

## §0.1 — NATIVE DECISIONS (2026-06-25) that set the sequencing
- **ph_sankrama fix → at the L2 SOURCE (canonicalize CDLM vocab), not an L4 normalization map.**
  Avoids double-correction; one vocabulary shared. ⇒ ph_sankrama's real fix is the L2 Phase-1 CDLM
  vocab fix; the L4 join then matches naturally. **L4 ph_sankrama WAITS on L2.**
- **ph_nimitta Axes 3 & 5 → COMPLETE the loaders (wire real CGM paths + nearest-neighbor embeddings),
  not defer.** BUT the L2 audit flagged bodha_cgm_nodes DEGENERATE (all strength 0.506, zero edges)
  and embeddings in the msr_signals cluster. Wiring the loader NOW reads GARBAGE. ⇒ complete-the-loader
  is correct but only DELIVERS value after L2's CGM + embeddings are rebuilt sound. **WAITS on L2.**

## §0.2 — DEPENDENCY REALITY (the reframe)
3 of 4 L4 fixes depend on L2 being fixed first (L2_BODHA_REMEDIATION_PHASE_PLAN_v1_0.md Phases 1–3).
The L4 thinness the native noticed is, in large part, L2 damage propagating downstream — this audit
and the L2 plan are the same problem from two ends. Correct global order:
  L2 Phase 1–3 (canonical CDLM vocab + fix degenerate CGM/embeddings) → THEN L4 §B fixes apply clean.

---

## §A — DO NOW (L2-INDEPENDENT). Safe to fix + commit immediately.
1. **ph_muhurta line 175 — instrument, don't change behavior.** Add a comment stating LIMIT 100 is the
   M3 fusion design decision (1 anchor : 1 action_class, top-confidence selection). Add a WARN log:
   if the influenceable-anchor upstream count > 100, log `[ph_muhurta] influenceable anchors=<N> exceeds
   LIMIT 100 — <N-100> dropped (M3 top-confidence design; revisit if persistent)`. No behavior change —
   makes the latent cliff visible in build logs.
2. **ph_pramana — CONFIRM the LEL vocab question (resolve the soft issue).** Compare
   life_event_log.domain_primary distinct values vs phala_anchors domain distinct values for a built
   chart (read-only). If they share vocabulary → document "verified aligned, no fix". If they DIVERGE
   (same class as ph_sankrama) → this is a 5th bug; fix it the SAME way the ph_sankrama fix will be
   done (canonical mapping), and note it joins the L2-dependent set. Report the distinct-value lists.
- GATE A: ph_muhurta instrumented; ph_pramana vocab verified aligned OR newly-flagged. Commit §A.

## §B — STAGE FOR AFTER L2 (specify exactly; do NOT apply against broken upstream yet).
These are authored ready-to-apply the moment L2 Phase 1–3 lands. Write them as a precise change spec
(and tests), but DO NOT commit them live until L2's CDLM vocab + CGM + embeddings are proven sound,
because applying now wires correct code to broken data.
1. **ph_sankrama line 77–80 — after L2 CDLM vocab is canonical:** the equality join should then match
   naturally (both sides canonical). VERIFY post-L2: do phala_anchors domain labels and bodha_cdlm
   domain_row labels now share one vocabulary? If yes → the join needs NO code change (the L2 fix
   resolved it) — confirm with a spillover-by-domain distribution (career should drop from 96.5% to a
   realistic spread). If a residual mismatch remains (L3-derived suffixes like `_advancement`) →
   add a thin canonical normalization at the join, reading the SAME canonical map the L2 CDLM writer
   uses (never a separate L4-only map — that's the double-correction the native rejected).
2. **ph_nimitta line 267 (CGM paths) — after L2 CGM rebuilt sound:** complete the loader to return a
   real `signal_id → [path_ids]` dict from bodha_cgm_paths (remove the `return {}`), so
   causal_chain_jsonb populates. Order by path relevance; keep a sane LIMIT but DOCUMENT it as
   intentional. VERIFY: causal_chain_jsonb non-NULL on a representative anchor sample post-build.
3. **ph_nimitta line 332 (embeddings) — after L2 embeddings sound:** complete the loader to return
   real nearest-neighbor ids (add ORDER BY similarity, read the neighbors, not self-reference), so
   precedent_refs_jsonb populates with real precedents. VERIFY: precedent_refs_jsonb has >1 (non-self)
   ref on a representative sample.
- GATE B: these are SPEC'd + tested-in-isolation but NOT committed live until L2 is sound. They move
  to "apply" only inside the post-L2 L4 re-fix pass.

## §C — VERIFY (after each phase; live data is the arbiter)
- §A: ph_muhurta WARN fires on a synthetic >100-anchor fixture; ph_pramana vocab verdict recorded.
- §B (post-L2 only): on non-native 1c826d5a, after L2 is sound + L4 rebuilt — ph_sankrama spillover
  distribution is realistic (career ≪ 96.5%); ph_nimitta Axis 3 + Axis 5 non-trivial on a sample.
- Native 482012f1 read-only throughout.

## §D — REPORT
- §A: what was committed (ph_muhurta instrumentation), ph_pramana vocab verdict (aligned / new-bug).
- §B: the exact staged change specs + isolation tests, marked BLOCKED-ON-L2.
- The global sequencing statement: L4 completeness is gated on L2 Phase 1–3; this brief unblocks the
  independent slice now and arms the rest.

## §HARD CONSTRAINTS
- Do NOT apply the L2-dependent fixes (§B) against current (broken) L2 upstream — they'd wire correct
  code to garbage data. Stage, don't commit-live, until L2 is proven sound.
- ph_sankrama: NO separate L4-only normalization map — read the L2 canonical vocab (native decision).
- Native 482012f1 read-only; destructive verification on 1c826d5a only.
- FROZEN orchestrator contract; assess/instrument/spec now, full data rebuild is operator-driven later.
- Distinguish intentional curation (LIMIT 200 convergence, LIMIT 100 discoveries — both documented +
  ordered, leave alone) from the accidental discards (§B) — do not "fix" the legitimate caps.
