---
artifact: SUDDHA_VACA_FIX_LEDGER
canonical_id: SUDDHA_VACA_FIX_LEDGER
version: 1.1
status: PARTIAL — P0-5,6,7,8,10,11 + the P2 allowlist one-liner + C.7 VERIFIED-FIXED and merged to
  main (PRs #835-840); P0-1..4 (lane:serve-shadbala) and P0-9 (lane:ga-tajaka) remain PARKED on
  PARISHODHANA PRs #827/#828 (confirmed open at this update). See SUDDHA_VACA_REPORT_v1_0.md's
  Phase C/D/E/F section for full evidence.
created: 2026-07-28
chart_under_test: 482012f1-710e-4a25-994a-93821f5871aa
source: NARRATION_SURFACE_CENSUS_v1_0.md (Wave 1) + seed-reconciliation pass over
  NARRATION_DETERMINISM_AUDIT_v1_0.md's 29 findings, both from workflow run wf_a58675cc-700.
---

# ŚUDDHA-VĀCA — Fix Ledger v1.0

**Headline escalation vs. the brief's own framing:** the brief anticipated the honest rebuild
blast radius as "L2 → L5" (from the `bo_laksana` P0 defect). Wave 1 census surfaced P0-severity
(verdict-inverting) defects **originating in L1 (`ga_tajaka_writer.py`), L2 (`bo_laksana.py`,
`sudarshana_emitter.py`), L3 (`l3_convergence.py`), L4 (`services/ph_nimitta/engine.py`), L5
(`mi_darshana.py`), and serve-side (`registry_bridge.ts`)** — i.e. **every layer of the stack has
at least one verdict-inverting narration defect**, not only L2. Plan Phase D rebuild scope
accordingly: this is not a single-writer rebuild, it is a full L1→L5 re-derivation for the charts
under rebuild, gated on the QUEUE-BEHIND wait (see report §Phase 0.2).

Both residuals the seed audit named as "unaudited, highest-value next sweep" produced
VERDICT_INVERTING findings on first read: `bodha_writers/sudarshana_emitter.py` (residual #1) and
`services/ph_nimitta/engine.py` (residual #2). The seed audit's prediction was correct.

**Seed reconciliation result:** 28 of 29 seed findings reconfirmed **STILL-OPEN** (F18 alone
CANNOT-REPRODUCE — its register text couldn't be independently re-derived this pass; F18 is
COSMETIC/lowest priority, not touched by any fix in the interim). **Nothing has been fixed by any
other campaign in the time since the seed audit.** PARISHODHANA's in-flight PRs (#827/#828) touch
`registry_bridge.ts` but not the Ṣaḍbala block itself (confirmed by hunk-line inspection in Phase
0.2) — hence QUEUE-BEHIND rather than an assumption that PARISHODHANA already fixed anything here.

---

## P0 — Verdict-inverting (fix before anything else)

| # | File:line | Defect | Origin layer | Fix layer | Rebuild blast radius | Lane |
|---|---|---|---|---|---|---|
| P0-1 | `registry_bridge.ts:3498` (=seed F2) | D1_MISSELECT — Ṣaḍbala total row selected by `fact_category` alone, no `fact_key` pin | serve | serve | none (redeploy amjis-mcp only) | lane:serve-shadbala |
| P0-2 | `registry_bridge.ts:3502` (=seed F10) | D3_HARDCODED_DRIFT — `SHADBALA_REQUIRED_RUPAS` wrapper constant shadows L1 `required_rupa` fact | serve | serve | none | lane:serve-shadbala |
| P0-3 | `registry_bridge.ts:3506` (new, same chain as P0-1) | D4_GRADE_INVERSION — `surplus = rupas − required` computed off the mis-selected ratio row | serve | serve | none | lane:serve-shadbala |
| P0-4 | `registry_bridge.ts:3508` (=seed F9) | D2_MISLABEL — unitless ratio printed with hardcoded literal `"rupas"` | serve | serve | none | lane:serve-shadbala |
| P0-5 | `bo_laksana.py:831` (=seed F1) | D1_MISSELECT — `_build_strength_lookup` selects `graha_shadbala_total` with no `fact_key` filter **and no ORDER BY** — non-deterministic, worse than P0-1 | L2 (Bodha) | writer | **L2 → L5** (bo_laksana is L2 root; cascades bo_bimba/karanajala/sangati/samvada/samskara → bo_upaya → bo_pramana_mapa, and L3 Kāla/L4 Phala/L5 Mīmāṃsā all consume Bodha) | lane:bo-laksana |
| P0-6 | `bo_laksana.py:848` (=seed F3) | D3_HARDCODED_DRIFT — normalizes every graha's rupa by a flat `/1.0` instead of the per-planet `required_rupa` fact, clamps at 2.0, erasing inter-planet strength discrimination | L2 (Bodha) | writer | same as P0-5 (same file, same rebuild) | lane:bo-laksana |
| P0-7 | `bodha_writers/sudarshana_emitter.py:167` (**new — the named residual #1**) | D4_GRADE_INVERSION — `_VALENCE_BY_AGREEMENT` grades valence purely by 3-frame AGREEMENT TIER (confirmed/partial/contradicted), never by the actual classical quadrant (`matching_class` — trikona/kendra/dusthana); a dusthana agreement can still be labeled "benefic" | L2 (Bodha emitter) | writer (emitter) | L2 cascade (feeds `bo_sudarshana` → same L2→L5 chain as above) | lane:bo-sudarshana |
| P0-8 | `brahmagyan/kala/l3_convergence.py:279` (new) | D4_GRADE_INVERSION — `health_attention` convergence-type's own domain classifier set omits `"health_attention"` itself (unlike the other two named types, which self-include), so a chart's own health-attention signal can fail to classify as health-attention | L3 (Kāla) | writer | **L3 → L5** (Kāla feeds Phala/Mīmāṃsā) | lane:ka-convergence |
| P0-9 | `ga_writers/ga_tajaka_writer.py:530` (new) | D3_HARDCODED_DRIFT — Varshesha (year-lord) candidate-scoring aspect test uses a hardcoded 7° orb constant instead of the graha's own L1-computed aspect orb, potentially mis-selecting the year lord that grades the whole annual chart | **L1 (Gaṇita)** | writer | **L1 → L5** (Tajaka/Varshaphal feeds downstream annual-chart consumers; this is the widest blast radius in the ledger — an L1 writer defect) | lane:ga-tajaka |
| P0-10 | `pipeline/orchestrator/writers/mi_darshana.py:316` (new) | D4_GRADE_INVERSION — `grade = pr.get("grade") or 5.0`: Python truthiness treats a real, computed `0.0` grade (the most-refuted possible score) as missing and silently substitutes the neutral default `5.0` | L5 (Mīmāṃsā) | writer | L5 only (terminal layer — no downstream Bodha/Kāla/Phala consumer, but re-verify) | lane:mi-darshana |
| P0-11 | `services/ph_nimitta/engine.py:437` (**new — the named residual #2**) | D4_GRADE_INVERSION — `derive_anchor_from_convergence()`'s directional-valence read falls back to `'elevated'` (a positive-sounding default) whenever the stored direction value is anything outside a fixed allow-list, silently flipping a suppressed/mixed signal to read as elevated | L4 (Phala service engine) | service engine | **L4 → L5** (feeds `phala_predictive_anchors_get` and Mīmāṃsā retrodiction) | lane:ph-nimitta-engine |

**P0 fix-attempt note:** P0-1/2/3/4 (serve-side) are independent of P0-5..11 (writer/engine) and can
be fixed and merged in parallel once PARISHODHANA's `registry_bridge.ts`-touching PRs land. P0-5/6
(same file) are one lane. P0-7 through P0-11 are five separate writers/engines across four layers —
five separate lanes, each triggering its own downstream rebuild.

---

## P1 — Misleading verifications & silently-dropped warnings (reads "clean" when it is not)

| File:line | Defect | Note |
|---|---|---|
| `bo_pramana_mapa.py:224/228/262/278` (=seed F6/F7/F15 + new line 262 in same cluster) | D5/D6 — `lel_zero_leak_pass`, `pillars_meet_reachability_pass` (tautological, can only ever be True), `divergent_flagged_count`, `trap2_narration_leak_count` are proxies/tautologies/literal-0-no-detector | Four fields in one writer; one PR |
| `ph_phaladesa.py:121` (=seed F5) | D6 — contradiction-caution sentence is dead code; `contradiction_jsonb` fetched, never consumed | |
| `ka_bhavishya_lekha.py:232` (=seed F16) + `:226` (new, PLAUSIBLE, same family) | D6 — `obstruction_summary`/`net_label` fetched but never narrated; obstructed windows read identically to clear ones | Same root cause, two symptoms |
| `kala_temporal.ts:377` (=seed F13) / `:380` (=seed F12) | D6 — "active today" fields are date-range-scoped, not today-scoped; empty-array truthiness bug | |
| `services/ph_phaladesa/engine.py:39` (=seed F14) | D5 — `PERMITTED_NARRATION_MODELS` permits `gpt-4o`/`gpt-4-turbo` while docstring says Gemini/DeepSeek only. **One-line fix, do in the P0 wave** per brief §4. | |
| `ga_writers/gates.py:144` (new) | D6 — `run_g7_only_facts_gate_db`'s Check 3 hardcodes a `valid_statuses` allowlist that is stale against the vocabulary this very audit's writers now use, so a legitimately-verified row can fail the gate (or a real gap pass it) | |

---

## P2 — Mislabel / drift / paraphrase

Seed: F4, F8, F11, F17, F19, F20 (plausible), F21 (plausible), F24 (plausible).
New CONFIRMED: `capabilities.ts:72`, `envelope.ts:1416`, `vidhi_registry_resource.ts:71`,
`server.ts:687`, `register_p1_synthesis.ts:893`, `l3_snapshot.py:519`, `l3_timeline.py:270`,
`answer_quality.py:180`, `muhurta.py:355`, `l4_anchors.py:211`, `ga_sade_sati_writer.py:974`,
`bo_bimba.py:253`, `bo_chart_gestalt.py:210`, `bo_karanajala.py:1387`, `bo_upaya.py:1251`,
`ga_nakshatra.py:87`, `ga_nakshatra.py:289`, `bo_pratijna.py:102`, `mi_sambandha.py:81`,
`mi_darshana.py:159`, `mi_pramana.py:382`, `gochara_grammar/primitives.py:788`,
`ph_sodhana/engine.py:38`, `ph_sodhana/engine.py:136`.
New PLAUSIBLE: `register_p1_ganita.ts:374`, `ga_sensitive_writer.py:2677`,
`bo_cdlm_summary.py:348`, `ka_kala_darshana.py:180` (=seed F27, still plausible),
`mi_darshana.py:360`, `mi_bhavisya.py:103` (=seed F28 family), `mi_bhavisya.py:161` (=seed F25).

Each needs its own one-line-to-one-function fix; none is verdict-inverting on its own, but several
(`ga_nakshatra.py:87` hardcoding `verification_pass_status='PASS'` for every row with zero actual
verification logic; `bo_chart_gestalt.py:210` storing a verdict in a writer whose own docstring
bans storing verdicts) are architecturally significant even at MISLEADING severity and should not
be deprioritized just because they don't flip a grade today.

## P3 — Cosmetic / lowest priority

Seed: F18 (CANNOT-REPRODUCE this pass — register text unconfirmable), F19 already listed above.
New: `ph_rectification/engine.py:253` (hardcoded dasha-lord natal sign index, justified as
"sourced from chart_facts, embedded as constant" — verify the justification holds, low urgency).

---

## Lane assignment summary (for Phase C worktree planning, once unblocked)

- `lane:serve-shadbala` — `registry_bridge.ts` (P0-1..4). **Blocked on PARISHODHANA PR #827/#828
  merging to main** (both touch this file; #828's hunk lands adjacent to this exact block).
- `lane:bo-laksana` — `bo_laksana.py` (P0-5/6) + full L2→L5 rebuild.
- `lane:bo-sudarshana` — `sudarshana_emitter.py` (P0-7) + L2 cascade rebuild.
- `lane:ka-convergence` — `l3_convergence.py` (P0-8) + L3→L5 rebuild.
- `lane:ga-tajaka` — `ga_tajaka_writer.py` (P0-9) + **L1→L5 rebuild** (widest radius; also **blocked
  on PARISHODHANA** per Phase 0.2 — `ph_nimitta.py`, a sibling L4 writer, is mid-fix under
  PARISHODHANA B1, and while `ga_tajaka_writer.py` itself is not directly touched, an L1 rebuild
  this wide should not run concurrently with any other campaign's active rebuild-adjacent work;
  confirm no additional overlap before opening this lane).
- `lane:mi-darshana` — `mi_darshana.py` (P0-10, P2 items on same file) + L5-only rebuild.
- `lane:ph-nimitta-engine` — `services/ph_nimitta/engine.py` (P0-11) + L4→L5 rebuild. **Direct
  file-adjacency risk with PARISHODHANA's `ph_nimitta.py` writer fix (different file, same
  subsystem) — coordinate merge order even after QUEUE-BEHIND clears.**
- `lane:p1-batch` — the six P1 items, mostly independent files, batchable into 1-2 PRs.
- `lane:p2-batch` — the ~24 P2 items, batchable by subsystem (bo_*, ga_*, mi_*, ph_*, serve)
  into several PRs once a builder is assigned.

**All lanes are QUEUE-BEHIND per SUDDHA_VACA_REPORT_v1_0.md Phase 0.2 until PARISHODHANA's open
PRs land on main.** This ledger is the Phase B deliverable; no Phase C code has been written.

---

## P0-NEW — Newly discovered during Phase C execution (2026-07-28), NOT authorized/fixed this wave

| # | File:line | Defect | Origin layer | Note |
|---|---|---|---|---|
| P0-N1 | `ga_writers/ga_structural_writer.py:3369` (`graha_shadbala_total`) and `:3378` (`house_bhava_bala_total`), both in `_load_shadbala_and_bhava_fact_ids` | D1_MISSELECT — identical shape to P0-5: unpinned fact_category selection, dict-overwrite, no fact_key, no ORDER BY, against the SAME `graha_shadbala_total` category confirmed to carry dual `rupa`/`ratio` fact_key variants | **L1 (Gaṇita)** | Surfaced independently by the `lane:bo-laksana` builder's investigation and the C.7 lint's live scan; confirmed real by the Opus Verifier. Wider blast radius than P0-5 (L1, upstream of everything). Recommend a dedicated future wave, own L1→L5 rebuild. |
| P0-N2 | `platform/supabase/migrations/339_phala_phaladesa.sql` `narration_model` CHECK constraint | D5_CONTAMINATION — same OpenAI-in-Gemini/DeepSeek-only-allowlist pattern as the P2 one-liner, but baked into a landed DB migration | DB schema | Confirmed real. Out of scope for a one-line Python fix; needs its own surgical ALTER-CONSTRAINT migration per §N.4. |

## P3-NEW — Newly discovered, lower severity

| File:line | Defect | Note |
|---|---|---|
| `mi_darshana.py` `verdict_note` (~line 377, post-fix line numbers) | D6_COVERAGE-GAP-adjacent — "Strong evidence across traditions" phrased purely from `grade >= 6.0`, ignoring whether `tradition_concordance` has any data | Investigated during the P0-10 fix; correctly judged not a clean one-line fix (would need restructuring across two axes). PLAUSIBLE. |
| `mi_gunanaka.py:337` | Non-fatal `'UUID' object is not subscriptable` in an optional "snapshot publish" step, caught and logged, doesn't fail the build | Pre-existing, unrelated to any of this wave's fixed writers. |
| `pipeline/orchestrator/writers/bo_laksana_rerank`'s `asset_registry.writer_timeout_seconds=600` | Operational, not narration — the operator E2E chart's rebuild exceeded this timeout; the writer's own daemon thread completed correctly 9 min later and the orchestrator's `RR-fix` reconciliation self-healed the state. Config-tuning recommendation, not a defect. | |

*End of SUDDHA_VACA_FIX_LEDGER_v1_0.md (v1.1 — Phase C/D/E closure appendix added 2026-07-28).*
