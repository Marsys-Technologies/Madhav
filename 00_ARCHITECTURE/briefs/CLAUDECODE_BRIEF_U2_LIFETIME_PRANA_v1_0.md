---
artifact: CLAUDECODE_BRIEF_U2_LIFETIME_PRANA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_U2_LIFETIME_PRANA
brief_for: U2 — Lifetime convergence + jivana_parva null-score fix (reopens & re-seals L3). [Prāṇa DROPPED — see §4.]
status: FINALIZED — built on prod-verified state (GATE A); CLOSED 2026-06-21; ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D20d, D26 single-wave, D27 L3-reseal, D29 Prāṇa-dropped)
classification: UPSTREAM-ENABLER (L3 reopen) — sequenced SECOND in the wave; enriches the temporal substrate all ph_* consume
swarm_coordination:
  wave: W2 (after U1; parallel-safe with U1)
  blocked_by: []          # parallel-safe with U1; both feed U4 + L4
  blocks: [m9_activation, ph_nimitta, ph_phaladesa]   # lifetime windows + scored parvas feed prediction
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py        # horizon parameterization (lifetime tier)
    - platform/python-sidecar/services/ka_sangam/engine.py                      # lifetime-horizon convergence
    - platform/python-sidecar/pipeline/orchestrator/writers/ka_jivana_parva.py  # re-run scoring over lifetime data
    - platform/supabase/migrations/<33N>_kala_convergence_horizon_tier.sql      # horizon_tier column (see §3.1)
    - 00_ARCHITECTURE/L3_KALA_CLOSE_v1_0.md                                      # version bump + re-seal (D27)
  parallel_safe_with: [u1_dasha_consensus]
  hard_internal_gate: none   # Prāṇa dropped; the lifetime run + the re-score are the whole job (sequential within U2)
---

# CLAUDECODE BRIEF — U2 Lifetime convergence + jivana_parva fix (L3 reopen + re-seal)

> **PRĀṆA (level-5) DROPPED (D29, native-ruled 2026-06-21).** Rationale: the birth time is itself
> being rectified (`ph_sodhana`), so daśā-boundary-derived sub-week precision would exceed the input
> certainty (false precision); and `ka_sangam`'s transit `peak_date` already provides fine timing on
> CERTAIN (ephemeris) ground, not birth-time-sensitive daśā boundaries. The sealed L1 `max_level ≤ 4`
> invariant is PRESERVED — no `chart_dashas_prana` table, no level-5 persistence. U2 is now just
> **lifetime convergence + the null-score fix** — simpler, bounded, seal-clean. (If post-rectification
> electional/muhūrta-grade Prāṇa is ever wanted, it becomes its own enabler on a VERIFIED birth time.)

> **GATE-A VERIFIED (D20d) + code-verified causal insight:** the reconciliation found
> `kala_jivana_parva` (739 rows) has `avg_effective_score = NULL` throughout. Code inspection shows
> the SCORING LOGIC IS CORRECT (`ka_jivana_parva.py` joins `kala_convergence` + `kala_darshana` and
> computes `avg_effective_score`). **The nulls are not a missing formula — they are a HORIZON
> MISMATCH:** `ka_jivana_parva` spans the whole LIFETIME (739 parvas across all 7 dāśā systems), but
> `ka_sangam` only scores a forward **5-year** window (`_HORIZON_YEARS = 5`). The lifetime parvas have
> no convergence windows to average → null. **The null scores and the lifetime gap are ONE problem.**
> U2 fixes the root (lifetime convergence); the scoring then populates naturally.

## §0 — What this enabler IS (lifetime context)
One reach an acharya cannot make, structurally supported by the existing engine: **lifetime
convergence** — run `ka_sangam` across the full life (birth → ~100y), so every dāśā parva sits in a
scored temporal context (not just a rolling 5-year window). This SIMULTANEOUSLY resolves the null
`kala_jivana_parva` scores. (Sub-month precision is handled separately by the transit `peak_date`,
which `ka_sangam` already computes on certain ephemeris ground — see the Prāṇa note above.)

## §1 — Strategic role
- **It places every prediction in a lifetime arc.** Without it, ph_nimitta anchors float in a 5-year
  window with no sense of where they sit in the life. With it, "this is the most significant career
  window of your life" becomes a computable statement.
- **It fixes a real prod defect** (null lifetime scores) as a by-product of the right architecture.
- **Fine timing is already covered** — `ka_sangam`'s transit `peak_date` (I-17 orb-strength peak)
  pins the moment on ephemeris-certain ground, so U2 needs no daśā-grain precision layer.
- **D26 single-wave + bounded** — coarse lifetime tier keeps the row budget low; no dedicated infra.

## §2 — VERIFIED ground truth (code + prod, 2026-06-21)
- **`ka_sangam` horizon is a parameter:** `engine.py` mode_a/mode_b take `horizon_start_jd`,
  `horizon_end_jd`; the WRITER (`ka_sangam.py` line 30, 79-83) hardcodes `_HORIZON_YEARS = 5`,
  `today → today+5y`. Lifetime = change the writer's horizon derivation; the engine already supports it.
- **`ka_jivana_parva` scoring is correct + complete:** `ka_jivana_parva.py` (run, lines 34-37) joins
  `kala_convergence kc LEFT JOIN kala_darshana kd ON kc.convergence_id = kd.convergence_id`, computes
  `avg_effective_score` (line 154) + `high_convergence_count` + `parva_quality`
  (peak/building/consolidating/receding/transitional classifier, lines 103-116). It needs lifetime
  convergence data to produce non-null scores.
- **`ka_sangam` provides fine timing already:** each window carries `peak_date` (the I-17 orb-strength
  maximum), computed from the ephemeris — so the "when does this peak" question is answered without
  daśā-grain Prāṇa (which would inherit birth-time uncertainty).
- **`kala_convergence` row budget:** 660 windows at 5-year horizon. Lifetime at the SAME grain would
  be ~100/5 × 660 ≈ 13,000 — large; **coarser lifetime grain keeps it bounded** (§3.1).

## §3 — The build (two steps, in causal order)

### Step 1 — LIFETIME convergence (the root fix) — `ka_sangam`
- Parameterize the writer's horizon: instead of `today → today+5y`, ALSO produce a **lifetime horizon**
  (birth_date → birth_date + ~100y) while keeping the fine 5-year forward tier. **Two coexisting tiers:**
  - **Coarse lifetime tier** (`horizon_tier='lifetime'`) — the full life at a coarser cadence
    (LOCKED default: **daśā-boundary-anchored windows** — one convergence evaluation per significant
    daśā-period boundary across the 7 systems, rather than a fixed calendar sampling) so the row
    budget stays bounded (target: lifetime adds low thousands of rows).
  - **Fine 5-year tier** (`horizon_tier='near'`) — the existing precise forward window, unchanged.
- LOCKED default (R2): add a **`horizon_tier` column** to `kala_convergence` (`'near'|'lifetime'`)
  so the two tiers coexist queryably and ph_nimitta can request the right tier. Keep
  `convergence_score ∈ [0,1]`; the I-16/I-17 math is grain-agnostic and unchanged.

### Step 2 — RE-SCORE jivana_parva (the null fix, now automatic) — `ka_jivana_parva`
- Re-run `ka_jivana_parva` AFTER Step 1. With lifetime convergence present, the existing join
  populates `avg_effective_score` + `high_convergence_count` + a real `parva_quality` per parva (no
  code change to the scoring — it was always correct; it lacked data). (R4 LOCKED: in-scope for U2.)
- **Verify the nulls are gone:** `parva_quality` should now vary (not 'transitional' throughout);
  `avg_effective_score` non-null for parvas overlapping convergence windows.

## §4 — Prāṇa: DROPPED (D29) — the simplification
Prāṇa (level-5) is NOT built. The sealed L1 `chart_dashas` `max_level ≤ 4` invariant is preserved;
no `chart_dashas_prana` table; no level-5 persistence; no relaxing of the `ValueError` guard. The R1
storage decision is therefore moot. Fine timing is delivered by `ka_sangam`'s existing transit
`peak_date`. This keeps U2 minimal, bounded, and seal-clean, and avoids claiming sub-week precision
on a birth time we are actively rectifying.

## §5 — Acceptance criteria [tagged; prod-verified]
1. `[pytest]` `ka_sangam` runs a lifetime horizon producing windows across the full life arc (coarse
   `horizon_tier='lifetime'` tier), tagged distinctly from the 5-year `'near'` tier; row budget within
   the documented bound (low thousands).
2. `[pytest]` `convergence_score` stays ∈ [0,1] for lifetime-tier rows; the I-16/I-17 math is unchanged
   (grain-agnostic); existing 660 near-tier rows are not altered.
3. `[verify: prod]` after re-run, `kala_jivana_parva.avg_effective_score` is **non-null** for parvas
   overlapping convergence; `parva_quality` VARIES (not 'transitional' throughout) — the null defect resolved.
4. `[schema]` `horizon_tier` column added to `kala_convergence`; the sealed L1 `chart_dashas` tree is
   UNCHANGED (max_level ≤ 4 invariant preserved; no level-5 anything).
5. `[anti-drift]` U2 never restates L1/L2 computed values; lifetime windows cite their constituent
   `signal_id`/`fact_id`s; writes only L3 tables (`kala_convergence`, `kala_jivana_parva`).
6. `[contract]` writers never commit/rollback `ctx.db_conn`; `WriterResult(asset_id=, rows_inserted=)`.
7. `[re-seal]` `L3_KALA_CLOSE` version-bumped (D27); lifetime tier + the jivana_parva score-fix recorded;
   the Prāṇa-dropped decision (D29) noted in the seal.
8. `[FORENSIC]` 7/7 holds; only chart `482012f1`. `[cockpit]` L3 assets stay lit; new counts correct.

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/u2-lifetime
# the horizon to parameterize
sed -n '25,90p' platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py
# the scoring that will auto-populate once lifetime data exists
sed -n '30,40p;100,155p' platform/python-sidecar/pipeline/orchestrator/writers/ka_jivana_parva.py
cd platform/python-sidecar && pytest -q services/ka_sangam -k "horizon or lifetime or tier or jivana"
```

## §7 — Definition of done
- [ ] Lifetime convergence tier in `ka_sangam` (coexists with 5-year near tier via `horizon_tier`; bounded row budget).
- [ ] `ka_jivana_parva` re-run → `avg_effective_score` non-null, `parva_quality` varies (null defect fixed).
- [ ] NO Prāṇa / level-5 (D29); sealed L1 `chart_dashas` tree untouched.
- [ ] Anti-drift clean; frozen contract; `L3_KALA_CLOSE` re-sealed; FORENSIC 7/7; cockpit verified.

## §8 — VALUE ADDED BY THIS BRIEF
1. **Diagnoses the null-score defect as a horizon mismatch, not a missing formula** — so U2 fixes the
   ROOT (lifetime convergence) and the scores populate for free, rather than inventing a scoring rule
   the writer already has.
2. **Places every prediction in a lifetime arc** — "the most significant career window of your life"
   becomes computable; ph_nimitta gains lifetime context an acharya cannot hold.
3. **Honest precision** — drops Prāṇa (D29) so the instrument never claims sub-week precision on an
   unrectified birth time; fine timing comes from the ephemeris-certain transit `peak_date`.
4. **Bounded + seal-clean** — coarse daśā-boundary-anchored lifetime tier keeps the row budget low;
   the sealed L1 tree is untouched; clean L3 re-seal.

## §9 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [DISSOLVED]:** Prāṇa storage — N/A; Prāṇa dropped (D29). No `chart_dashas_prana`, no level-5.
- **R2 [RESOLVED — Cowork default locked]:** lifetime tier = **daśā-boundary-anchored** windows; the two
  tiers coexist via a **`horizon_tier`** column on `kala_convergence`.
- **R3 [DISSOLVED]:** Prāṇa top-N — N/A (Prāṇa dropped).
- **R4 [RESOLVED — Cowork default locked]:** the jivana_parva null-defect fix IS in-scope for U2
  (resolves automatically from Step 1's lifetime convergence).

---
*End of CLAUDECODE_BRIEF_U2_LIFETIME v1.0 — CLOSED. Lifetime convergence + the null-score fix; Prāṇa
dropped (D29) for honest precision; reopens + re-seals L3. R1–R4 resolved.*
