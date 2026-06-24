---
artifact: CLAUDE_CODE_PROMPT_KA_SANGAM_PER_SIGNATURE_FIX.md
canonical_id: CLAUDE_CODE_PROMPT_KA_SANGAM_PER_SIGNATURE_FIX
version: 1.0
status: READY — per-signature transit-planet fix + inline confidence gate (no cap). Direct to main. NO SEAL.
authored_by: Cowork 2026-06-22
design: L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN_v1_0.md §4.6 (per-signature model + native rulings)
gates: L4 seal (ph_pratikara rebuilds from corrected kala_convergence)
---

# Claude Code Prompt — ka_sangam Per-Signature Transit Fix

> Paste §PROMPT to Claude Code in Antigravity. Implement on MAIN directly (native instruction; discard the
> agent worktree). **DO NOT SEAL.** OBJECTIVE: maximal genuine value, NOTHING speculative — reuse existing
> machinery, add no cap, no new table, no abstraction beyond the per-signature planet source.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Fix `services/ka_sangam/engine.py`
so `kala_convergence` carries the CORRECT transit planet per predicate signature, and the Moon/Mercury
performance explosion is eliminated — by an INLINE CONFIDENCE GATE, not a cap. Apply directly on `main`
(discard the prior agent worktree). **DO NOT seal anything.**

**READ FIRST:** `00_ARCHITECTURE/CONDUCTOR/cleanup/L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md` §4.6 (the
per-signature model + native rulings) + §4.5 (no speculative infra).

**GOVERNING OBJECTIVE (native, explicit):** maximal genuine value from the asset; do NOT do anything that
doesn't add value. No event cap, no new persisted table, no generic abstraction. Reuse the engine's
EXISTING confidence machinery. If you'd build something not specified here — STOP and ask.

**Rails:** Frozen contract (ka_sangam writes only its kala_* tables; never commit/close ctx.db_conn;
WriterResult(rows_inserted=)); anti-drift; L-is-authority; canonical chart 482012f1 never mutated;
Gemini/DeepSeek only; verify against live data.

### THE MODEL — transit planet is PER SIGNATURE (not one global planet)
The bug: ka_sangam read `transit_trigger->>'planet'` (never exists) → fell back to constant 'Jupiter' →
full ephemeris scan. The MD-lord "fix" scanned fast planets → 11h/1.2GB. The CORRECT planet source differs
by the predicate's signature_class:

| signature | trigger | transit planet source | how |
|---|---|---|---|
| DOSHA (270) | malefic_transit_over_afflicted_point | **Saturn** | hardcode Saturn (slow, safe, matches saturn_over_afflicted) |
| DIGNITY (397) | graha_activation | **the signal's OWN graha** | `signal_id → bodha_msr_signals/chart_facts` to get the graha whose dignity activates. This is a NATAL-POSITION activation — if it does NOT require a sky-transit scan, do a LOOKUP not a scan (confirm; prefer the cheaper correct path). |
| DISPOSITOR_RELATIONAL (5,145) | relational_link_transit | the relevant lord, **confidence-gated** | see the GATE below — NOT MD-lord-full-scan, NOT a cap |
| YOGA (481) | benefic_transit_to_kendra_trikona | **Jupiter** | keep Jupiter (correct benefic activator) |
| SUBSYSTEM (60,445) | subsystem_trigger | none | NO transit search — leave the subsystem path untouched |

### THE CONFIDENCE GATE (the core of the DISPOSITOR fix — native ruling)
- **DO NOT add a max_events cap.** A count cap truncates to an arbitrary slice = silent-plausible-wrong.
- The engine ALREADY HAS the machinery: `orb_strength_score` (I-17, cos² decay) + the `confidence_label`
  threshold classifier (I-21), and the scan already computes `Score = max orb-strength across events`
  (engine.py ~126-145) — it only ever uses the STRONGEST event per window.
- **The explosion is RAM accumulation:** the scan generates + holds ALL weak crossings before taking the
  max. **Fix: apply a HIGH-confidence orb/strength threshold INLINE during the scan** — discard any event
  below the bar AS IT IS FOUND, never accumulate it. Only events clearing the high-confidence orb bar are
  kept. A fast lord (Moon/Mercury, only in their own MD periods) then yields FEW qualifying events
  naturally — no explosion, no cap, self-regulating by merit. This is LESS code than a cap.
- Reuse the existing `orb_strength_score` + `confidence_label` thresholds — do not invent a new scoring
  scheme. Pick the high-confidence cutoff from the existing classifier's bands (e.g. only 'decisive'/
  'probable' equivalent), documented + a single named constant, not a magic number.

### IMPLEMENTATION (only this — §4.5 scope discipline)
1. In `mode_a_search` / `mode_b_sweep` (engine.py): replace the `transit_trigger->>'planet'` read + the
   Jupiter fallback + the MD-lord helpers (`_get_active_md_lord`/`fetch_md_periods`) with a per-signature
   planet resolver driven by the predicate's `signature_class`/trigger type per the table above.
2. Apply the inline confidence gate in the scan loop (discard sub-threshold events as found).
3. DIGNITY: resolve the signal's own graha via `signal_id`; use the cheapest correct path (lookup if no
   sky-transit is semantically required).
4. `constituent_factors['planet']` = the resolved transiting graha for that window (per the model). It may
   legitimately differ per signature; absent if no qualifying event clears the gate (a window may still
   score on dāśā + signal factors — do NOT invent a planet).
5. NO new table, NO cap, NO subsystem-path change, NO fast-planet ephemeris accumulation.

### DOWNSTREAM
`ph_pratikara` bridges `constituent_factors->>'planet'` → afflicting_graha. Confirm it handles the now-
correct per-signature planet (single value per window is fine here). Verify ph_nimitta / any other reader.

### REBUILD via the ORCHESTRATOR (direct runners retired)
Rebuild through the orchestrator click-Build / runs route; let the DAG cascade carry ka_sangam →
ka_vighnakara → ph_pratikara. This is the slow build that lets you WATCH the new stage progress bar —
confirm it animates (reload to refresh SSE first to avoid a dev-mode false negative).

### VERIFY
- `kala_convergence` planet distribution is now CORRECT per signature: DOSHA→Saturn, YOGA→Jupiter,
  DIGNITY→the signal's graha, DISPOSITOR→the gated lord. NOT 660 Jupiter. Run completes fast (no 11h / no
  1.2GB — the inline gate prevents accumulation).
- `ph_pratikara` mitigation spans multiple afflicting grahas matching the obstruction signatures.
- Add tests: (a) per-signature planet resolution (DOSHA→Saturn, YOGA→Jupiter, DIGNITY→own-graha,
  DISPOSITOR→gated); (b) NO event cap exists; (c) the inline confidence gate discards sub-threshold events
  (assert a fast-lord window yields few high-confidence events, not 65); (d) no planet fallback constant;
  (e) memory stays bounded on a lifetime rebuild. These guard against re-collapse, re-scan, and re-cap.
- Version-bump L3_KALA_CLOSE (surgical). CI green; commit + push to main (auto-deploys); verify prod.

### REPORT — NO SEAL
Report: the per-signature resolver; the inline confidence gate (cutoff used, from the existing classifier);
DIGNITY lookup-vs-scan decision; before/after planet distribution by signature; ph_pratikara graha spread;
the rebuild runtime + peak memory (proving the gate fixed the explosion); the progress bar animation
observed (screenshot/GIF — discharge the debt); L3 version-bump; CI + prod revision. Anything flagged
out-of-scope. Do NOT seal. STOP.

---
*End. Per-signature transit planet (DOSHA→Saturn, DIGNITY→own-graha, YOGA→Jupiter, DISPOSITOR→confidence-
gated lord, SUBSYSTEM→none). NO cap — an INLINE high-confidence orb gate (reusing the existing I-17/I-21
machinery) discards weak events as found, killing the Moon/Mercury RAM explosion by merit not truncation.
No new table, no speculative infra. Direct to main, rebuild via orchestrator. L4 seal then unblocks. NO SEAL.*
