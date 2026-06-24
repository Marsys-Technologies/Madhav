---
artifact: CLAUDE_CODE_PROMPT_L0_CONSISTENCY_SWEEP.md
canonical_id: CLAUDE_CODE_PROMPT_L0_CONSISTENCY_SWEEP
version: 1.0
status: READY — final L0 closure: (A) live-data confirmation of the 2 fixes, (B) intra-L0 constant-consistency sweep across all 22 assets. ASSESS + GUARD only.
authored_by: Cowork 2026-06-23
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md — the last step before L0 is truly sealed
context: Rahu/Ketu + Mercury fixes verified IN CODE by Cowork. This closes the 2 remaining loops the native raised.
---

# L0 — Final Closure: Live-Data Confirm + Intra-L0 Consistency Sweep

> Two loops to truly close L0: (A) CONFIRM the 2 fixes are live in the DATA (not just code — the table is
> writer-seeded, so it depends on a re-run); (B) SWEEP all 22 L0 assets for OTHER cross-asset constant
> divergences (the Rahu/Ketu conflict proved L0 can disagree with itself — find any others). ASSESS +
> extend the GUARD only; no data fix unless a new divergence is found (then report for native decision).

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Two final L0-closure tasks.
READ-ONLY except for extending the integrity-guard test (B). No data changes unless a NEW divergence is
found — and then STOP + report, don't auto-pick. Verify against the live DB.

### PART A — Confirm the 2 sealed fixes are LIVE IN THE DATA (eyes-on-data)
The bg_dignity_reference + bg_motion_state_thresholds tables are SEEDED BY THE WRITER (250_*.sql is
schema-only, 0 INSERTs) — so the fix is only "in the data" if the writer was re-run. The guard tests pass
(they read live), but run an explicit confirmation:
```
SELECT graha, exaltation_sign, debilitation_sign FROM bg_dignity_reference WHERE graha IN ('Rahu','Ketu');
  -- expect Rahu: Taurus/Scorpio ; Ketu: Scorpio/Taurus
SELECT exaltation_sign FROM reference_planets WHERE planet_id IN ('rahu','ketu');
  -- expect Taurus(2)/Scorpio(8) — must AGREE with bg_dignity_reference
SELECT graha, motion_state, speed_threshold_low FROM bg_motion_state_thresholds
  WHERE graha='Mercury' AND motion_state='atichara';   -- expect 2.0
```
Report the actual returned values. If any does NOT match (e.g. the writer wasn't re-run and the DB still
shows Gemini or 2.5), FLAG it — the fix is in code but not data → re-run the writer. (Data is disposable, so
re-running is fine; but we must KNOW the data state, not assume it.)

### PART B — Intra-L0 constant-consistency sweep (the substantive task)
The Rahu/Ketu bug was an intra-L0 divergence: two L0 tables held the same classical fact with different
values. We fixed THAT pair + guarded it. Now find any OTHER such divergence across ALL 22 L0 assets — this
was never swept.
1. **Enumerate the classical constants that appear in MORE THAN ONE L0 table/writer.** Candidates: planet
   exaltation/debilitation/moolatrikona/own-signs (reference_planets vs bg_dignity_reference — already
   guarded for exaltation; CHECK debilitation/moolatrikona/own-signs too), sign lords, nakshatra lords +
   spans, planetary friendships (multiple friendship schemas?), motion thresholds, dosha definitions,
   dignity degrees, ayanamsha values. For EACH constant that lives in 2+ places: do the values AGREE?
2. **Find hardcoded bypasses WITHIN L0:** does any L0 writer hardcode a value that ANOTHER L0 table is the
   declared source-of-truth for (instead of reading it)? (e.g. a writer with its own inline sign-lord map
   when reference_planets/bg_reference already defines lords.)
3. For every duplicated constant found: report AGREE / DIVERGE. For each DIVERGENCE → a new finding
   (like Rahu/Ketu): present the two values + which is classically correct (SOURCE-verified, not
   self-label) + which table is wrong → STOP for native decision, do NOT auto-fix.
4. **EXTEND THE INTEGRITY GUARD:** generalize the cross-table agreement test (currently Rahu/Ketu
   exaltation only) to assert agreement on EVERY duplicated constant you found that SHOULD be single-valued
   — so no L0 constant can silently diverge again. This is the durable outcome of the sweep (adding guard
   tests is allowed; it's test code, not data).

### OUTPUT
Update `L0_SEAL_v1_0.md` (or a `L0_CONSISTENCY_SWEEP.md` appendix): Part A's live-data confirmation (actual
values); Part B's full list of duplicated L0 constants with AGREE/DIVERGE per each; any NEW divergence as a
native-decision finding (source-verified); the extended guard test (what it now covers). State explicitly:
"L0 intra-consistency = CLEAN" (if no new divergence) or "N new divergences found → native decision needed."
Only when Part A confirms live data + Part B is CLEAN (or its divergences are decided+fixed) is L0 TRULY
sealed. NO data auto-fix; STOP + report any new divergence. NO build, NO L1.

---
*End. Close L0 for real: confirm the 2 fixes are live in the DATA (writer-seeded, must verify not assume),
and sweep all 22 L0 assets for OTHER cross-asset constant divergences (the Rahu/Ketu conflict proved L0 can
contradict itself) — extend the guard to cover every duplicated constant. New divergences → native decision,
not auto-fix. Then L0 is genuinely done → L1.*
