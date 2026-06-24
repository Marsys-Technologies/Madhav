---
artifact: CLAUDE_CODE_PROMPT_KA_SANGAM_TRANSIT_REDESIGN.md
canonical_id: CLAUDE_CODE_PROMPT_KA_SANGAM_TRANSIT_REDESIGN
version: 1.0
status: READY — implement the ratified ka_sangam transit-model redesign (slow-transit rule evaluation, NO ephemeris scan). NO SEAL.
authored_by: Cowork 2026-06-22
design: L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN_v1_0.md (§4.5 ratified decisions)
gates: L4 seal (ph_pratikara rebuilds from corrected kala_convergence)
---

# Claude Code Prompt — ka_sangam Transit Model Redesign

> Paste §PROMPT to Claude Code in Antigravity. Implements the ratified design. **DO NOT SEAL.**
> GOVERNING OBJECTIVE: maximal genuine value from the asset, NOTHING speculative. Reuse what exists;
> build nothing that isn't required. Do not add infrastructure, tables, abstractions, or "future-proofing"
> beyond what §4.5 ratifies.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Implement the ratified redesign of
`ka_sangam`'s transit-factor logic. **READ FIRST:** `00_ARCHITECTURE/CONDUCTOR/cleanup/L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md`
(§4.5 = the ratified decisions — they GOVERN). **DO NOT seal anything.**

**GOVERNING OBJECTIVE (the native's explicit instruction):** maximal genuine value from the asset, do
NOT do anything that does not add value. No speculative tables, no "for future reuse" infra, no abstractions
beyond what's needed. Reuse existing code. If you find yourself building something not required by §4.5 —
STOP, it's out of scope.

**Rails:** Frozen orchestrator contract (ka_sangam writes ONLY kala_* tables it owns; never commits/closes
ctx.db_conn; WriterResult(rows_inserted=)); anti-drift; L-is-authority; canonical chart 482012f1 never
mutated; Gemini/DeepSeek only; localhost code-plane / prod data-plane; verify against live data.

### THE BUG (three layers — fix the root, not the symptom)
`kala_convergence` is 660/660 planet='jupiter'. Cause: ka_sangam read `transit_trigger->>'planet'` (a key
that NEVER exists — `transit_trigger` from `ka_yojaka/binder.py::build_predicate` is a RULE SPEC:
`type`, `trigger_events`, `bg_transit_rules_ids`, `scale_by:'transiting_graha_nature'` — no planet field),
fell back to constant 'Jupiter', and ran a full ephemeris scan. The MD-lord "fix" kept the scan + fed a
wrong planet → 11h/1.2GB explosion (fast planets the model excludes). **ROOT: ka_sangam must NOT scan
ephemerides. It is a SCORER, not an ephemeris engine.**

### THE FIX (per §4.5 — implement exactly this, no more)
1. **Remove ALL ephemeris-scanning from ka_sangam's transit-factor path.** Delete the planet-fallback +
   the per-window Swiss-Ephemeris transit scan. Delete `_get_active_md_lord` / `fetch_md_periods` (the
   wrong MD-lord fix). ka_sangam does NOT call swisseph for transits.
2. **Consume the existing SLOW-transit overlap logic.** Use `l3_timeline._active_transits_for_period`
   (Saturn/Jupiter/Rahu/Ketu overlap loop — cheap, in-memory, no scan) OR the `ka_gochara` service to get,
   per window, the slow transits overlapping it (each carries a real `transit_planet` + sign/house/dates).
   DO NOT create a new persisted transit table (Q1 ratified: speculative — only ka_sangam consumes it,
   in-memory is cheap).
3. **Evaluate which transit rules FIRE per window.** For each predicate's `transit_trigger` rule, check
   whether any overlapping slow-transit event SATISFIES it (use `bg_transit_rules_ids` → the L0 classical
   transit rules, the `trigger_events`, `veto_if`/`mitigate_if`, `scale_by:'transiting_graha_nature'`).
   Reuse existing rule-eval helpers if present; do not build a new rule engine if one exists.
4. **`constituent_factors['planet']` becomes a LIST** (Q2) of the slow-transiting graha(s) that fired the
   rule for that window — possibly Saturn AND Jupiter, etc. Never a constant; ABSENT (empty/omitted) if no
   rule fires — a window can still score on its dāśā + signal factors without a transit factor. Do NOT
   invent a planet to fill a gap.
5. **Preserve the convergence scoring model** — only the transit-factor derivation changes; the
   ≥3-factor convergence logic, weights, dedup, horizon tiers stay. The transit factor's contribution
   scales by `transiting_graha_nature` per the existing model.

### DOWNSTREAM CONTRACT (keep consumers working)
- `ph_pratikara` bridges `constituent_factors->>'planet'` → afflicting_graha. Now that planet is a LIST,
  update the bridge to take the STRONGEST by graha-nature weight (or handle the array). Verify ph_nimitta /
  any other `constituent_factors.planet` reader handles the list shape. Update them minimally.

### REBUILD (via the ORCHESTRATOR — direct runners are retired)
Drive the rebuild through the orchestrator click-Build / runs route (NOT a script). Let the DAG cascade
(Q3) carry ka_sangam → ka_vighnakara → ph_pratikara (+ any other convergence consumer per registry
depends_on). This is the SLOW build that finally lets you WATCH the new stage progress bar — confirm it
animates queued→running→substeps→committing→lit (discharge the verification debt; reload to refresh SSE
first so dev-mode exhaustion doesn't give a false negative).

### VERIFY
- `kala_convergence` planet distribution is DIVERSE and matches the real slow-transit events (Saturn/
  Jupiter/Rahu/Ketu, as lists) — NOT 660 Jupiter, NOT a fast-planet explosion. Run completes in reasonable
  time (no 11h hang — the in-memory overlap is cheap).
- `ph_pratikara` mitigation now spans multiple afflicting grahas (not 60× Jupiter).
- Add a test asserting: (a) no ephemeris scan in ka_sangam's transit path; (b) planet is a list of slow
  grahas; (c) windows with no firing rule have no transit planet (not a fallback constant); (d) the native's
  convergence shows ≥2 distinct grahas. This guards against re-collapse AND re-introduction of a scan.
- Version-bump L3_KALA_CLOSE (Q4 — surgical, engine-logic correction, NOT a re-seal).
- CI green; commit + push (auto-deploys); verify on live prod cockpit.

### SCOPE DISCIPLINE (the native's objective — enforce it)
Do ONLY items 1-5 + the downstream contract + rebuild + verify. Do NOT: add a persisted transit table,
build a generic transit-event abstraction, add fast-planet transits, add new config surfaces, or
"improve" adjacent code. If something seems needed but isn't in this list, STOP and report it as a
question rather than building it. Maximal value from the asset = the convergence transit factor is
CORRECT and rich (real slow-graha lists), with zero speculative scaffolding.

### REPORT — NO SEAL
Report: the ephemeris-scan removal; the slow-transit consumption + rule-eval approach; the before/after
planet distribution (660-Jupiter → diverse slow-graha lists); the ph_pratikara graha spread; the progress
bar animation observed during the rebuild (screenshot/GIF — finally discharge that debt); the L3
version-bump; CI + prod revision. Note anything you flagged as out-of-scope. Do NOT seal. STOP.

---
*End. ka_sangam = scorer not ephemeris engine: evaluate which slow-transit (Saturn/Jupiter/Rahu/Ketu)
rules fire per window using existing in-memory overlap logic; planet = LIST of firing grahas, absent if
none. No new table, no scan, no speculative infra. Rebuild via orchestrator + DAG cascade (watch the
progress bar). Surgical L3 version-bump. L4 seal then unblocks on corrected ph_pratikara. NO SEAL.*
