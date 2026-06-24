---
artifact: CLAUDE_CODE_PROMPT_L0_REAUDIT.md
canonical_id: CLAUDE_CODE_PROMPT_L0_REAUDIT
version: 1.0
status: READY — L0 thorough re-audit (all 22, fresh, incl. 'SOUND', with SOURCE verification). Stage 1 of L0's full cycle. ASSESS ONLY.
authored_by: Cowork 2026-06-23
campaign: FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md — but native shifted to LAYER-BY-LAYER full-close (audit→reconcile→fix→rebuild→seal→next). This is L0 Stage 1 (audit).
note: The prior L0_SOUNDNESS_REPORT (15 SOUND/2 WRONG/3 DEFERRED) is SUSPECT — it carried a likely-INVERTED fix (align-to-Gemini) + repeated a dubious 'Parashara majority/Gemini' source label without verifying it. Re-audit fresh.
---

# L0 Brahmagyan — Thorough Re-Audit (Stage 1 of the L0 full-close cycle)

> Native shifted to LAYER-BY-LAYER: fully close L0 (audit → reconcile → fix code → rebuild data → seal)
> before L1. This is L0's AUDIT stage only. Re-audit ALL 22 assets FRESH — including the 15 prior-"SOUND" —
> because the Rahu/Ketu bug proves a prior "SOUND" can hide a fundamental issue, and the prior audit's own
> proposed FIX was probably backwards. ASSESS ONLY — no fix, no build, no seal.

---

## §PROMPT

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav). Re-audit ALL of LAYER 0
(Brahmagyan — the 22 bg_* / reference assets) THOROUGHLY and FRESH for chart
`482012f1-710e-4a25-994a-93821f5871aa`. **READ FIRST:** `00_ARCHITECTURE/FOUNDATION_ROOT_CAUSE_MAP.md §2`
(the prior L0 findings — treat as LEADS to re-verify, NOT settled) + the prior `L0_SOUNDNESS_REPORT.md` +
`L0_L4_SOUNDNESS_AUDIT_SPEC_v1_0.md` (method). **ASSESS ONLY — apply no fix, change no data, run no build,
seal nothing. Verify against the live DB AND the cited classical sources — not the tables' self-labels.**

**WHY FRESH (do not trust the prior pass):** the prior L0 audit marked 15 assets SOUND, but (a) it carried
a likely-INVERTED fix for Rahu/Ketu (it proposed aligning everything TO Gemini — the native states the
standard convention is Rahu=Taurus / Ketu=Scorpio, so the Gemini value is likely the BUG, not the target),
and (b) it repeated a "Parashara majority / Gemini" source attribution WITHOUT verifying it against an
actual text. So: re-audit ALL 22 including the SOUND ones; take NO prior verdict on faith.

**NEW CAPABILITY this audit must have (the prior one lacked it) — SOURCE VERIFICATION:** for any finding
that is a CLASSICAL FACT (an exaltation sign, a dignity, a yoga condition, a dāśā rule, a threshold), do
NOT accept the table's stored value OR its self-documented rationale as evidence. VERIFY against the actual
classical source the table claims to cite (BPHS chapter/verse, or the standard convention). Treat a
confident-sounding unsourced self-label (e.g. "Parashara majority") with SUSPICION — it is exactly how a
wrong value hides behind a plausible justification. Report the SOURCE EVIDENCE, not just the value.

**Per-asset DEEP method (SPEC §5):** distribution census (all rows) → stratified sample → read the
writer/seed → INDEPENDENTLY re-derive (for L0 roots: against the CLASSICAL SOURCE + cross-table consistency,
since most L0 assets have no upstream) → 3 lenses (data-engineering / astrological-coherence-vs-SOURCE /
internal+cross-table consistency) → null-rate + FK-resolution → silent-default code scan → verdict
SOUND / SUSPECT / WRONG (+ WRONG/DEFERRED/SOUND for ambiguous). For each WRONG, the downstream-impact chain
(which L1+ writers read this table — edge-verified against actual reads).

**EXECUTION:** sequential / ≤2-3 parallel where file-disjoint, RESUMABLE, write findings incrementally
(an API-529 costs one asset, not the run). All 22 assets — none skipped.

### SPECIFIC L0 FOCUS POINTS (verify these hard, with sources)
1. **Rahu/Ketu exaltation (L0-W1) — THE priority.** `reference_planets` says Rahu=Taurus(2)/Ketu=Scorpio(8);
   `bg_dignity_reference` says Rahu=Gemini(3)/Ketu=Sagittarius(9). VERIFY: what does each table actually
   CITE as its source? Is there ANY real classical text supporting Rahu-exalts-Gemini, or is it an error
   (e.g. confusion with mooltrikona/own-sign, a transcription slip, an unsourced assertion)? The native's
   strong prior: Taurus/Scorpio is the standard, well-established convention; Gemini/Sagittarius is likely
   the BUG. **Report the source evidence for BOTH values + your assessment of which is the classical
   standard + which table is wrong. DO NOT pick/fix — this is the native's canonical decision; surface the
   evidence so they decide.** (The prior map's "align to Gemini" proposal is probably inverted — flag that.)
2. **Mercury atichara threshold (L0-W2).** Confirm: threshold 2.5°/day vs Mercury's real max ~2.2°/day (from
   ephemeris_daily). Confirm the classical INTENT — is Mercury meant to have an atichara state at all, and
   if so at what speed? (Decides fix = lower threshold vs remove row.) Source the classical definition.
3. **bg_ephemeris** — re-confirm SOUND: spot-check positions vs an independent ephemeris; FORENSIC anchors.
   The deepest foundation — re-verify even though prior=SOUND.
4. **bg_rules / bg_yogas / bg_dasha_systems** (the prior DEFERRED items D2/D3) — re-confirm: are the
   null FK columns / empty source_chunk_ids genuinely DEFERRED (planned-unbuilt) or do they break a live
   consumer? Check what actually reads them.
5. **bg_texts OCR (D1)** — re-confirm DEFERRED: does the OCR garble inject FALSE astrological facts, or only
   degrade retrieval precision? Scope the live-impact (do garbled chunks reach interpretation?).
6. **The 15 prior-SOUND** — re-audit each with the deep method + source-check; a "SOUND" that doesn't
   survive source-verification gets reclassified.

### OUTPUT — rewrite `L0_SOUNDNESS_REPORT.md` (v2, fresh)
Per-asset verdict + the DATA + SOURCE evidence + re-derivation + impact chain + family tag (F1–F8) +
PROPOSED-FIX scope for WRONG (with the CORRECT direction per source, explicitly noting where it differs
from the prior map's proposal — esp. Rahu/Ketu). The Rahu/Ketu finding presented as a NATIVE-DECISION with
full source evidence, not a pre-picked fix. The tally + the single most important finding. NO fix, NO
build, NO seal. STOP and report for native+Cowork reconciliation (then we decide fixes → fix → rebuild → seal).

---
*End. L0 Stage 1 = thorough fresh re-audit of all 22, source-verified (not table-self-labels), prior
verdicts not trusted, Rahu/Ketu surfaced as a source-evidenced native decision (the prior fix direction is
likely inverted). → reconcile with native → then fix → rebuild → seal → L1. ASSESS ONLY.*
