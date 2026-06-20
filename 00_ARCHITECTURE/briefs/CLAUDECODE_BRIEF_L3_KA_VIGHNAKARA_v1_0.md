---
artifact: CLAUDECODE_BRIEF_L3_KA_VIGHNAKARA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_VIGHNAKARA
brief_for: ka_vighnakara — Vighnakāra / THE DANGER ENGINE (L3 Kāla; co-equal danger/avoidance windows) [ELEVATE]
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.11.3 Gap-B + §5.11.4-D (danger windows CO-EQUAL with opportune; prophecy includes WARNING), QT-3 (danger/avoidance), §5.7.4 (knockout/affliction stage), §5.13.C2 + I-23 (temporal DISSONANCE — opportune×danger overlap), §14.5.1 (extend kala_obstruction), §14.1 (L3 windows → L4 ph_pratikara applies the remedy)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K5
  blocked_by: [ka_sangam, ka_yojaka, ka_gochara, ka_dasha_kala, ka_muhurta_seva]  # the inverse search reuses the engine spine
  blocks: [ka_tulana, ka_bhavishya_lekha]  # prioritization + prediction-records consume danger windows; dissonance needs both
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_vighnakara.py   # NEW writer = the danger engine
    - platform/python-sidecar/services/ka_vighnakara/**                        # NEW (inverse-search reuse of ka_sangam spine)
    - platform/supabase/migrations/<next>_kala_obstruction_rigor.sql           # EXTEND kala_obstruction (windows + rigor)
    - platform/scripts/seed/asset_registry_seed.ts                             # re-point ka_vighnakara deps; rewrite description
  parallel_safe_with: [ka_kala_darshana]   # both are K5 products reading ka_sangam; disjoint tables
---

# CLAUDECODE BRIEF — ka_vighnakara (The Danger Engine) [ELEVATE]

## §0 — What this asset IS
`ka_vighnakara` (Vighnakāra, "the maker of obstacles") is **the danger engine** — the first-class INVERSE
of `ka_sangam`. It finds and ranks **danger / avoidance windows**: when NOT to act, the exposure /
affliction periods, the caution windows. Today it is a thin "inauspicious/obstructed windows" placeholder;
this ELEVATES it to a co-equal product (plan §5.11.4-D): **prophecy includes WARNING, not just
opportunity.** It runs the SAME engine spine as `ka_sangam` (plan §5.11.7 — same machine) but with
MALEFIC / affliction predicates, emitting ranked danger windows with severity + rigor scores. It extends —
not replaces — the existing `kala_obstruction` table (plan §14.5.1).

## §1 — Why it matters / strategic role
- **It doubles the instrument's value + honesty (plan §5.11.4-D).** An oracle that only says "act here"
  but never "avoid here" is half-blind. Danger windows are at least as actionable as opportune ones.
- **It is the source of TEMPORAL DISSONANCE (plan §5.13.C2 / I-23).** A strong OPPORTUNE window (from
  `ka_sangam`) coinciding with a DANGER window here = a dissonance the instrument must SURFACE (e.g.
  "great time to marry, terrible time financially"), never average into a bland "medium."
- **It feeds the L4 mitigation product (plan §14.1).** `ph_pratikara` (mitigation, registered
  `depends_on: bo_upaya + ka_vighnakara`) consumes these windows to time remedies. L3 finds the danger;
  L4 applies the fix.
- **It is the DOSHA-class destination (plan §5.12.3).** `ka_yojaka` classifies affliction signals as
  DOSHA → their templates "fire" as danger windows HERE.

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **The table EXISTS and anticipates the design (`kala_obstruction`):** `id, chart_id, date,
  obstruction_type text CHECK ∈ {malefic_transit, adverse_dasha, double_affliction}, severity double
  precision CHECK [0,1], factors jsonb, source_citation NOT NULL`. **EXTEND this; keep `severity ∈ [0,1]`
  + the obstruction_type vocabulary (widen it as needed).**
- **The registered seed row** (`ka_vighnakara`, Vighnakāra/Obstruction) currently `depends_on:
  ['ka_kalasutra','ga_sensitive']`. **Re-point** to `ka_sangam` (the spine) + the affliction sources.
- **Note the date-grained schema.** `kala_obstruction.date` is a single DATE (not a window). L3 danger
  is a WINDOW (start/end/peak), like `ka_sangam`. **Extend to windowed rows (§3.3).**
- **`ga_sensitive`** (sensitive points: gulika/mandi, upagrahas, etc.) + `ga_sade_sati` are the affliction
  inputs the malefic-transit predicates key on.

## §3 — The build (inverse-search reuse of the ka_sangam spine)
**3.1 — Reuse the ka_sangam engine spine with MALEFIC predicates (plan §5.11.7).** Do NOT build a second
engine. The danger search = the convergence spine where the trigger vocabulary is affliction-shaped:
- **malefic_transit:** Saturn/Mars/Rahu/Ketu transiting OVER a sensitive point (`ga_sensitive`) or the
  lord of a vulnerable house; the §5.9.2 station/eclipse triggers are high-magnitude danger.
- **adverse_dasha:** the daśā-eligibility prior (`ka_dasha_kala`) for an AFFLICTING lord (the DOSHA-class
  daśā rule from `ka_yojaka`).
- **double_affliction:** the existing type — two afflictions converging (the danger analog of confluence).
- **Sade Sati phases** (`ga_sade_sati`) as a standing danger overlay.
- knockout interplay: the `ka_muhurta_seva` inauspicious-knockout is a danger signal here, not just a veto.

**3.2 — The RIGOR STRATUM applies symmetrically (plan §5.13).** Each danger window carries: `severity`
(the danger analog of convergence_score — same multiplicative-necessary × additive-supporting form,
I-16), continuous orb-strength (I-17), window profile (peak danger date + shoulder, I-18), rarity (a rare
severe affliction matters more, I-19), confidence + independence discount (I-21/I-22). **Weights are
native-ratified (I-7) — PROPOSE, `[NATIVE-RATIFY]`, HALT.**

**3.3 — Extend `kala_obstruction` to WINDOWED rigor rows (the migration).** ADD (idempotent): rename/augment
to a window: `window_start date`, `window_end date`, `peak_date date` (keep `date` or migrate it);
`signal_id uuid` (the DOSHA L2 signal — anti-drift), `confidence_score double precision CHECK [0,1]`,
`confidence_label text`, `rarity_years double precision`, `independent_current_count smallint`. Widen the
`obstruction_type` CHECK if new types are needed (e.g. `eclipse_hit`, `sade_sati`, `transit_over_sensitive`).
Keep `severity ∈ [0,1]`.

**3.4 — TEMPORAL DISSONANCE detection (plan §5.13.C2 / I-23).** Provide the overlap query: for any
`ka_sangam` opportune window that OVERLAPS a `ka_vighnakara` danger window (same/adjacent dates, possibly
different life-domains), emit a DISSONANCE record (the pair + both magnitudes + the domains). This is NOT
averaged into one score — it is surfaced as a named tension. Store in a dissonance view/table or as a
flag both engines can join on. (The serve layer / `ka_tulana` consumes it.)

**3.5 — Anti-drift (plan §6, N.5).** Each danger window references the L2 DOSHA `signal_id` + the L1
affliction facts (`ga_sensitive`/`ga_sade_sati` fact_ids) in `factors`/`source_citation`; never restates
an L1 value. No writes to L2.

## §4 — Asset registration (ELEVATE)
Update `ka_vighnakara`: keep id + `Vighnakāra` + `kala_obstruction`; rewrite english_description to
"Ranked danger/avoidance windows (malefic transit / adverse daśā / affliction) with severity + rigor +
dissonance vs. opportune windows"; `depends_on: ['ka_sangam','ka_yojaka','ga_sensitive','ga_sade_sati']`;
`asset_kind='artifact'`; chart-scoped count_sql; per-chart delete-then-insert (plan §N.3).

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: pytest]** the danger search reuses the `ka_sangam` spine (no duplicate engine — assert
   shared module), producing ranked danger windows for known afflictions (e.g. a Sade Sati peak, a
   Saturn-over-sensitive-point).
2. **[verify: pytest]** severity uses the same multiplicative-necessary × additive-supporting form;
   a double_affliction scores higher than a single malefic transit.
3. **[verify: pytest]** windowed rows: peak_date = max-severity instant; rarity_years computed for a rare
   severe configuration.
4. **[verify: pytest]** TEMPORAL DISSONANCE: a constructed opportune window overlapping a danger window
   emits a dissonance record with BOTH magnitudes + domains — NOT a single averaged score.
5. **[verify: anti-drift]** every danger window references a resolving L2 DOSHA `signal_id` + L1
   affliction fact_ids; no L2 writes (grep → 0).
6. **[verify: NATIVE-RATIFY]** the I-7 danger weights HALT for native sign-off.
7. **[verify: psql_prod + curl_prod]** `kala_obstruction` extended to windowed rows; `ka_vighnakara`
   elevated; cockpit count correct; idempotent rebuild; FORENSIC chart unaffected.
8. **[verify: L4-handoff]** the danger windows are shaped so `ph_pratikara` (L4 mitigation) can consume
   them (the §14.1 / R-4 hand-up contract — document the interface).
9. **[contract]** the writer never commits/rolls back `ctx.db_conn` (plan §9 / Vimarśaka-RED).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-vighnakara
# the table to EXTEND
sed -n '/CREATE TABLE IF NOT EXISTS public.kala_obstruction/,/);/p' platform/supabase/migrations/0001_brahma_baseline.sql
# affliction inputs
grep -rn "gulika\|mandi\|upagraha\|sade_sati" platform/python-sidecar/pipeline/orchestrator/writers/ga_sensitive.py platform/python-sidecar/pipeline/orchestrator/writers/ga_sade_sati.py 2>/dev/null | head
# tests
cd platform/python-sidecar && pytest -q services/ka_vighnakara -k "vighnakara or danger or obstruction or dissonance"
```
> Branch/merge: Madhav human-gated PR. NATIVE-RATIFY gate (I-7 danger weights) — Conductor HALTS.

## §7 — Definition of done
- [ ] Danger engine = inverse-search reuse of the ka_sangam spine (malefic/affliction predicates).
- [ ] Rigor stratum on each danger window (severity, orb-strength, profile, rarity, confidence, independence).
- [ ] kala_obstruction extended to windowed rigor rows; obstruction_type widened.
- [ ] Temporal dissonance detection (opportune×danger overlap) — surfaced, not averaged.
- [ ] Anti-drift clean; L4 ph_pratikara hand-up interface documented; weight gate honored.
- [ ] ka_vighnakara elevated + re-pointed; idempotent; FORENSIC-clean; PR opened.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Makes the instrument honest and protective, not just optimistic** — elevating obstruction from a
   knockout-veto afterthought into a co-equal, ranked danger product means the layer can say "avoid here"
   with the same rigor it says "act here," roughly doubling its real-world usefulness.
2. **Delivers temporal dissonance — a genuinely deep insight** — surfacing the tension when an opportune
   window for one domain collides with a danger window for another (instead of averaging it into a
   misleading "medium") is the temporal twin of L2's contradiction handling and exactly what separates a
   nuanced instrument from a naive one.
3. **Reuses the convergence spine instead of forking it** — building danger as the inverse search over the
   same engine (not a second engine) keeps the layer DRY, ensures the rigor scoring is identical, and
   honors the §5.11.7 "same machine" discipline that keeps the layer from bloating.
4. **Extends an anticipatory schema** — `kala_obstruction` already had severity∈[0,1] + a malefic/dasha/
   double-affliction vocabulary; the brief widens it to windows + rigor without a destructive rebuild.
5. **Wires the prophecy→agency loop's danger half** — by shaping danger windows for `ph_pratikara` (L4
   mitigation) consumption, it sets up "here is the danger window AND when to do the remedy," the
   protective counterpart to the opportune-intervention loop.
6. **Grounds danger in the embedded subsystems** — pulling `ga_sensitive` + `ga_sade_sati` as first-class
   affliction inputs means danger is computed from the chart's actual vulnerable points, not a generic
   malefic heuristic.

---
*End of CLAUDECODE_BRIEF_L3_KA_VIGHNAKARA v1.0. The danger engine — prophecy's warning half. NATIVE-RATIFY gate (I-7) inside.*
