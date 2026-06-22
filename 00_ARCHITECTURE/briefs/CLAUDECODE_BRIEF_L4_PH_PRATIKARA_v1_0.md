---
artifact: CLAUDECODE_BRIEF_L4_PH_PRATIKARA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L4_PH_PRATIKARA
brief_for: ph_pratikara — Mitigation (a managed, sequenced, affordable, auspiciously-timed remedy PROGRAM) [maximal capacity]
status: FINALIZED — built on prod-verified state (GATE A) + D40 elevations; ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: CLAUDECODE_BRIEF_L4_PH_PRATIKARA_v1_0.md (the 6-asset draft)
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D10 reuse, D40 elevations, D5 outcome-to-L5, B.3 citation)
swarm_coordination:
  wave: W3 (parallel-safe with ph_muhurta; after ph_nimitta spine)
  blocked_by: [ph_nimitta]      # proportionality keys on anchor severity; influenceable anchors route here
  blocks: [ph_phaladesa]
  soft_depends: [ph_muhurta]    # P3 hands remedy-start to ph_muhurta for the auspicious begin moment
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_pratikara.py
    - platform/python-sidecar/services/ph_pratikara/**
    - platform/supabase/migrations/332_phala_mitigation.sql
    - platform/scripts/seed/asset_registry_seed.ts
    - platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  parallel_safe_with: [ph_muhurta]
  hard_internal_gate: none
---

# CLAUDECODE BRIEF — ph_pratikara (Mitigation) — a managed remedy PROGRAM [maximal capacity]

> **What it is, in one line:** for each adverse window in the native's life, ph_pratikara produces not
> "a remedy" but a **managed program** — affordable + sustainable options across traditions, ordered so
> nothing conflicts, timed to an auspicious start, proportioned to the severity, and tied to a
> re-evaluation point. This is what a family astrologer runs over years — at machine scale across a
> lifetime of windows.

## §0 — REUSE the rich remedy store (D10 / D40)
**Code-verified (2026-06-21):** `bodha_rm_remedy_prescriptions` (bo_upaya) ALREADY carries everything
needed — `tradition` + `sub_tradition` + `remedy_category`, `classical_strength_rating`,
`resonance_match_score`, `counter_indications_array`, `incompatible_with_prescription_ids_array`,
`prerequisite_prescription_ids_array`, `feasibility_score`, `estimated_cost_inr_range_jsonb`,
estimated-time, phase-sequence, substitute-options, `pranapratishtha`, `recommended_hora`/
`recommended_choghadiya`, `requires_acharya_review`, cross-tradition corroboration, and an
`outcome_tracking_placeholder_jsonb` hook. **ph_pratikara CONSUMES this; it does NOT author remedies.**
The draft used only the basic obstruction→remedy join; this asset uses the full richness.

## §1 — The 5 ELEVATIONS (D40)

### P1 — Economics + feasibility optimization
Rank candidate remedies by `resonance_match_score` × `classical_strength_rating` × `feasibility_score`,
and present **tiers** scoped to the native's constraints: a free/low-time option (e.g. 10-min daily
mantra), a low-cost option (charity, ₹ range), and a high-investment option (gemstone, ₹ range), each
with `estimated_cost_inr_range_jsonb` + estimated daily time + `requires_acharya_review` flagged. A
remedy the native can't afford or sustain is useless — surface the trade-off, don't just pick the "strongest."

### P2 — Coherent program (sequencing + no conflicts)
Use `prerequisite_prescription_ids_array` (X must precede Y) + `incompatible_with_prescription_ids_array`
(can't do both — e.g. two clashing gemstones) to assemble an ORDERED, non-conflicting remedy SCHEDULE
across the active windows — a small graph-ordering (topological sort over prerequisites; conflict-exclusion).
Output a program, not a flat list. No astrologer does this by hand across a lifetime of windows.

### P3 — Muhūrta-timed initiation (fuse to ph_muhurta)
For each remedy with `recommended_hora`/`recommended_choghadiya`/`pranapratishtha`, hand the
remedy-start to `ph_muhurta` (action_class = the remedy's initiation) to find the auspicious BEGIN
moment BEFORE the obstruction peaks. Store `initiation_muhurta_ref` (the ph_muhurta window). "Start the
Saturn mantra on [date] in [hora]" — remedy + timing fused.

### P4 — Proportionality + the outcome loop
- **Proportionality:** match remedy INTENSITY to the obstruction `severity` (ka_vighnakara) +the linked
  anchor `magnitude` (ph_nimitta) — a mild affliction → a mantra/charity, not a ₹50,000 gemstone. Store
  `intensity_tier` + the proportionality basis.
- **The loop:** tie the remedy to the obstruction window with a `re_evaluation_date` (= window_end) and
  carry the falsifiable `outcome_hook_jsonb` (from the store's `outcome_tracking_placeholder`) → L5
  scores whether the affliction eased (mirrors ph_pramana / D5). Mitigation is a managed loop, not fire-and-forget.

### P5 — Cross-tradition choice (with corroboration)
Present remedy options ACROSS the 6 traditions (Vedic / Tantra / Ayurvedic / Vastu / Lal-Kitab /
Modern) with the cross-tradition corroboration count ("4 of 6 traditions converge on strengthening
Saturn"). The native chooses per comfort (some won't do tantric ritual; some want only mantra). Store
`tradition_options_jsonb` + `cross_tradition_corroboration`. Respect preference; show convergence strength.

## §2 — Schema (migration 332)
`phala_mitigation`:
```
mitigation_id           uuid PK
chart_id                uuid NOT NULL
obstruction_id          bigint REFERENCES kala_obstruction(id)      -- the adverse window (anti-drift FK)
linked_anchor_id        uuid REFERENCES phala_anchors(anchor_id)    -- the prediction it mitigates (nullable)
afflicting_graha        text
obstruction_severity    text                                        -- from ka_vighnakara
program_jsonb           jsonb NOT NULL    -- P2: the ordered, conflict-free remedy schedule (prescription_ids + order)
tradition_options_jsonb jsonb NOT NULL    -- P5: per-tradition options + corroboration
recommended_tier_jsonb  jsonb             -- P1: free/low-cost/high-investment tiers w/ cost+time
intensity_tier          text              -- P4: matched to severity × anchor magnitude
proportionality_basis   text              -- P4
initiation_muhurta_ref  uuid REFERENCES phala_muhurta(muhurta_id)   -- P3 (auspicious begin moment, nullable)
window_start            date
window_end              date
re_evaluation_date      date NOT NULL     -- P4 (= window_end; L5 re-checks)
outcome_hook_jsonb      jsonb NOT NULL    -- P4 (falsifiable did-it-help, for L5)
classical_citation      text NOT NULL     -- B.3 (the remedy's MC/BPHS source)
cross_tradition_corroboration smallint    -- P5 (N of 6)
derivation_ledger_jsonb jsonb NOT NULL
source_citation         text NOT NULL
computed_at             timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, obstruction_id, intensity_tier)
```

## §3 — Engine spec (`services/ph_pratikara/engine.py`)
1. For each `ka_vighnakara` obstruction window (60) + each influenceable `ph_nimitta` anchor (V4): find
   the matching `bodha_rm_remedy_prescriptions` for the afflicting graha/signal.
2. P1: rank + tier by resonance × strength × feasibility, scoped to cost/time.
3. P2: topo-sort over prerequisites + exclude incompatibles → the ordered program.
4. P5: group options by tradition + the corroboration count.
5. P4: set intensity_tier from severity × anchor magnitude; set re_evaluation_date + the outcome hook.
6. P3: for the chosen/primary remedy, call `ph_muhurta` for the initiation window.
7. Anti-drift: cite obstruction_id + prescription_ids + anchor_id; write ONLY `phala_mitigation`.

## §4 — Acceptance criteria [tagged; prod-verified]
1. `[pytest]` every mitigation references a real `ka_vighnakara` obstruction + real `bodha_rm` prescription ids; remedies are CONSUMED not authored (grep → no remedy text invented).
2. `[pytest — P1]` remedies are tiered by cost/time/feasibility; each tier carries the real cost range + estimated time + acharya-review flag.
3. `[pytest — P2]` the program is a topologically-ordered schedule respecting prerequisites with ZERO incompatible pairs co-scheduled.
4. `[pytest — P3]` a remedy with hora/choghadiya gets an `initiation_muhurta_ref` from ph_muhurta.
5. `[pytest — P4]` intensity_tier scales with obstruction severity × anchor magnitude (a mild obstruction does NOT yield a high-investment remedy); re_evaluation_date + outcome_hook set.
6. `[pytest — P5]` options span the traditions present with the corroboration count; every remedy carries its classical citation (B.3).
7. `[anti-drift]` writes only phala_mitigation; zero `.commit()/.rollback()`; ledgers resolve; `WriterResult(asset_id='ph_pratikara', rows_inserted=N)`.
8. `[psql_prod + curl_prod]` phala_mitigation lit; cockpit shows ph_pratikara; idempotent; FORENSIC 7/7.

## §5 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l4-ph-pratikara
# the rich remedy store to consume (do NOT author remedies)
sed -n '700,780p' platform/migrations/325_l2_bodha_enriched_schema.sql
psql "$DATABASE_URL" -c "\d kala_obstruction"; psql "$DATABASE_URL" -c "SELECT count(*) FROM kala_obstruction WHERE chart_id=:'NATIVE';"  # 60
cd platform/python-sidecar && pytest -q services/ph_pratikara -k "pratikara or program or feasibility or proportion or tradition"
```

## §6 — Definition of done
- [ ] Migration 332: phala_mitigation created.
- [ ] Consumes bodha_rm store (no remedy authoring); P1 economics, P2 program, P3 muhūrta-init, P4 proportionality+loop, P5 cross-tradition all implemented + tested.
- [ ] Anti-drift clean; registered/idempotent/FORENSIC-clean; cockpit lit; PR opened.

## §7 — VALUE ADDED BY THIS BRIEF
1. **Turns remedy-lookup into a managed remedy PROGRAM** — affordable, sequenced, conflict-free,
   auspiciously-timed, proportional, re-evaluated — exactly what a family astrologer runs over years,
   at machine scale across a lifetime of windows.
2. **Uses the rich remedy store the draft ignored** — cost/feasibility/incompatibility/prerequisite/
   tradition/hora data was DESIGNED for this and sat unused (D10 reuse).
3. **Fuses three layers** — obstruction (L3) + prediction (ph_nimitta) + remedy (L2) + auspicious timing
   (ph_muhurta) into one coherent intervention.
4. **Honest + accountable** — proportional to severity, choice across traditions, and a falsifiable
   outcome hook so L5 can score whether remedies actually helped.

## §8 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [RESOLVED — Cowork default locked]:** proportionality (severity × magnitude → `intensity_tier`):
  mild/minor → mantra/charity only; moderate → + vrata/behavioral; severe/major → gemstone/puja
  eligible (always still feasibility-tiered within the band).
- **R2 [RESOLVED — Cowork default locked]:** `requires_acharya_review` remedies (tantric initiation,
  high-cost) are **SURFACED with the flag + a "consult a qualified acharya before undertaking" note —
  NEVER auto-prescribed** as the primary program step. The autonomous program may recommend them as an
  *optional high-investment tier*, always flagged; the native (with an acharya) decides. Safety-respecting.
- **R3 [RESOLVED — Cowork default locked]:** show ALL cost tiers (free → high-investment); the native
  chooses; no hard budget cap baked in (the tiers expose the trade-off rather than pre-deciding it).

---
*End of CLAUDECODE_BRIEF_L4_PH_PRATIKARA v1.0 — CLOSED. Mitigation at maximal capacity: a managed remedy
program — economics, sequencing, muhūrta-timed initiation, proportionality + outcome loop, cross-tradition
choice. R1–R3 resolved.*
