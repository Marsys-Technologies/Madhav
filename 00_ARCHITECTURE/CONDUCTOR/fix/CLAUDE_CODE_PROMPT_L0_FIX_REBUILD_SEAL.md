---
artifact: CLAUDE_CODE_PROMPT_L0_FIX_REBUILD_SEAL.md
canonical_id: CLAUDE_CODE_PROMPT_L0_FIX_REBUILD_SEAL
version: 1.0
status: READY — L0 Stage 2-3-4: fix code (native-decided) → rebuild L0 data → seal. Then L1.
authored_by: Cowork 2026-06-23
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md — layer-by-layer full-close; this is L0 fix→rebuild→seal.
audit: L0_SOUNDNESS_REPORT.md v2.0 (the reconciled findings)
native_decisions: "Rahu/Ketu → Taurus/Scorpio (Gemini is the bug). Mercury atichara → lower to ~2.0°/day. brahma_ontology 657→652 → explain before seal. 3 DEFERRED → leave, don't block seal."
---

# L0 — Fix → Rebuild → Seal (Stages 2-4 of L0 full-close)

> The L0 audit (v2) is reconciled with the native. This implements the DECIDED fixes, rebuilds L0's data,
> and seals L0. Full latitude (fix RIGHT). DATA-FIRST verification. Then STOP — L1 is the next layer.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Execute L0 fix → rebuild → seal.
**READ FIRST:** `L0_SOUNDNESS_REPORT.md` v2.0 (the audited findings) + `FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md`.
Full latitude to fix RIGHT (fix the WRITER/seed so any future build is correct, not just patch rows).
DATA-FIRST: prove every fix against the live DB. Gemini/DeepSeek + Claude-in-Code (dev-time). Frozen
contract for any writer touched. Canonical chart 482012f1 not the subject (L0 is global reference).

### NATIVE-DECIDED FIXES (implement exactly these)

**FIX 1 — Rahu/Ketu exaltation → Taurus/Scorpio (Gemini/Sagittarius is the BUG).**
Native canonical decision (textually-backed: Santanam BPHS Ch.3, Phaladeepika, Saravali, JH/PL consensus):
- `bg_dignity_reference` (`bg_dignity_reference.py` + its seed): change Rahu exaltation Gemini(3)→**Taurus(2)**,
  Ketu exaltation Sagittarius(9)→**Scorpio(8)**. Replace the unsourced "Gemini per Parashara majority" note
  with the correct citation (BPHS Ch.3 Santanam / Phaladeepika / Saravali).
- `reference_planets` (`l0_reference.py`): already Taurus/Scorpio — confirm it stays, keep its correct
  "Taurus per Parasara" comment.
- **ADD A CROSS-TABLE INTEGRITY GUARD** (the durable fix): a CI/test assertion that
  `reference_planets` and `bg_dignity_reference` AGREE on every planet's exaltation sign (Rahu/Ketu
  especially) — so they can never silently diverge again. This guard is as important as the value fix.
- PROVE: post-fix, both tables return Rahu=Taurus/Ketu=Scorpio; the guard passes; a dignity read for
  Rahu/Ketu now returns ONE consistent answer regardless of source table.

**FIX 2 — Mercury atichara threshold → ~2.0°/day (reachable).**
Native decision: LOWER, not remove (classically Mercury HAS an atichara state; the 2.5 was a too-high
number, not a deliberate "never"). In `bg_dignity_reference.py` + the `bg_motion_state_thresholds` seed:
Mercury atichara threshold 2.5 → **2.0°/day** (~P90 of Mercury's real speed range; max observed 2.2027°/day).
On the way, briefly confirm the classical intent that Mercury does carry an atichara state (source note);
if a source explicitly excludes Mercury from atichara, STOP and report instead of lowering. PROVE: the
atichara state is now reachable — show a date in the ephemeris where Mercury's speed ≥ 2.0°/day so the
state CAN fire.

**FIX 3 — Explain brahma_ontology row drift (657→652) BEFORE seal.**
The v2 audit flagged brahma_ontology current=652 vs v1=657 (−5). Determine WHY: is it a real deletion (5
rows genuinely removed — by what? when? correct or accidental?) or a v1 miscount? Check the writer + any
migration touching brahma_ontology + git history of the seed. Do NOT guess — find the cause. If it's a real
accidental loss, restore/fix it; if it's a correct removal or a v1 miscount, document the explanation. L0
does NOT seal until this −5 is explained. (Internal cross-checks reportedly hold at 652 — so likely benign,
but "a count dropped and we don't know why" is not allowed past seal.)

### LEAVE AS-IS (the 3 DEFERRED — not errors, not blocking L0 seal)
bg_texts OCR garble (D1), bg_rules null yoga_canonical_id/dasha_system_id (D2), bg_yogas/bg_dasha_systems
empty source_chunk_ids (D3). These are genuinely not-yet-built features, not computation errors. Record
them in the L0 seal as KNOWN-DEFERRED (a future-work list), do NOT fix in this L0 pass, do NOT let them
block the seal.

### REBUILD L0 DATA
After the fixes, rebuild the affected L0 reference data (re-run the seeds/migrations for reference_planets,
bg_dignity_reference, bg_motion_state_thresholds, + brahma_ontology if Fix 3 required a change) so the live
DB reflects the corrected code. Apply via the proxy; push (auto-deploys). L0 is global reference — confirm
no chart-specific rebuild needed beyond what reads these tables.

### SEAL L0 (the gate — data-verified, then STOP)
Verify on live data BEFORE declaring L0 sealed:
- Rahu=Taurus/Ketu=Scorpio in BOTH tables; the cross-table agreement guard passes.
- Mercury atichara reachable (a real date hits the new threshold).
- brahma_ontology −5 EXPLAINED (cause documented; restored if it was an accidental loss).
- FORENSIC 7/7 still passes (these L0 fixes must not perturb the confirmed chart base — Rahu/Ketu
  exaltation change affects DIGNITY reads, which is intended, but the 7 anchors are positions, unaffected —
  confirm).
- The 15 prior-SOUND assets unchanged; the 3 DEFERRED recorded as known-future-work.
Write `L0_SEAL_v1_0.md`: the fixes applied + data-proof for each + the ontology explanation + the deferred
list + FORENSIC intact. Flip the L0 findings in FOUNDATION_ROOT_CAUSE_MAP.md to FIXED-VERIFIED-SEALED.

**STOP — do NOT start L1.** Report the L0 seal evidence for native+Cowork review. L1 (its own
audit→reconcile→fix→rebuild→seal cycle) is the next layer, authorized separately after L0 seal is confirmed.

---
*End. L0 fix (Rahu/Ketu→Taurus/Scorpio + cross-table guard; Mercury atichara→2.0; explain ontology −5),
rebuild L0 data, seal with data-proof + FORENSIC intact. 3 DEFERRED recorded not fixed. STOP before L1.
Layer-by-layer full-close: L0 done-done, then L1.*
