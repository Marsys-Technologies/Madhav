---
artifact: GA_SENSITIVE_AK_RECKONING_FIX_BRIEF_v1_0.md
canonical_id: GA_SENSITIVE_AK_RECKONING_FIX_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: GA_SENSITIVE_AK_DIVERGENCE_INVESTIGATION_v1_0.md
purpose: >
  Fix the KN Rao Ātmakāraka reckoning in ga_sensitive (Rāhu sorted on raw degree instead of the
  reverse 30−deg), plus bundled cleanups (stale halt docstring; esoteric Parāśarī-only inconsistency).
  Gated behind a one-source citation per the canonical-or-floor rule.
audience: Claude Code (Antigravity)
---

# ga_sensitive AK reckoning fix (+ bundled cleanups)

## §0 — The verified finding (from the investigation)
The AK divergence on 1c826d5a is a RECKONING BUG, not doctrine. `_build_karaka_rows`
(`ga_writers/ga_sensitive_writer.py` ~L991-999) sorts the KN Rao 8-graha set with Rāhu at raw
`rahu_long % 30`. KN Rao reckons Rāhu retrograde → its degree-in-sign should be `30 − (rahu_long % 30)`.
Rāhu sits in late Aries (~28-30° raw) at this birth, so raw reckoning makes it spuriously outrank
Mercury (27-29°) by ~0.92° in 4 of 5 ayanāṁśas. Under correct reversal Rāhu collapses to 0.2-1.7°
(last place) and Mercury is the unambiguous AK in those 4; Surya-Siddhanta has Mars and no divergence
either way. So the fix removes a false divergence and yields the correct stored AK.

## §1 — CITATION GATE (do this BEFORE the code change — canonical-or-floor rule)
We must not encode one author's convention as canonical without a citable source. The fix asserts
"KN Rao's chara-kāraka scheme reckons Rāhu's degree in reverse (30 − deg)."
PASTE TO CLAUDE CODE:
```
Read-only. Confirm + cite the rule before any code change: in the KN Rao 8-chara-karaka system, is
Rāhu's degree-within-sign reckoned in REVERSE (effective = 30 − (longitude mod 30)) for the purpose of
ranking the Ātmakāraka? Find the project's own classical source layer first — search bg_texts /
brahma_yoga_catalog / bg_rules and the 08_CLASSICAL_CROSS_REFERENCE corpus for the chara-karaka /
Rāhu-reverse rule and quote the exact reference. If the corpus has it, cite the bg_text/rule id. If it
does NOT, say so plainly — then the fix needs a native-supplied citation before it lands (do not invent
one). Deliver the citation (or its absence) and the exact wording. STOP and report.
```
If the corpus lacks it, surface to the native for a source; do NOT proceed to §2 on an uncited rule.

## §2 — THE FIX (after §1 yields a citation)
PASTE TO CLAUDE CODE:
```
Apply the KN Rao Rāhu reverse-reckoning fix in ga_writers/ga_sensitive_writer.py _build_karaka_rows.

1. Compute the KN Rao sort key for Rāhu ONLY as 30 − (rahu_long % 30); all 7 classical grahas keep
   their normal (long % 30) key. Do NOT alter the Parāśarī 7-graha set at all. Concretely: build the
   KN Rao ranking with a key function that special-cases the Rāhu entry's effective degree. Keep the
   stored longitude/degree_in_sign facts truthful (the REVERSAL affects RANKING, not the reported raw
   degree — store raw degree, rank by reversed). Add a short comment citing the §1 source.
2. The `ak_divergent` flag (parashari top != knrao top) then naturally stops firing for this chart.
   Keep the warning code path (it is correct when a REAL divergence exists, e.g. Rāhu genuinely highest
   under reversed reckoning) — we are fixing the input to the comparison, not removing the guard.
3. Regression test: for a fixture matching 1c826d5a's degrees (Rāhu ~28° raw late Aries, Mercury ~27.5°),
   assert the KN Rao AK == Mercury (NOT Rāhu) and ak_divergent == False. Add a second fixture where
   Rāhu IS genuinely highest under reversed reckoning and assert the warning still fires (guard intact).
4. CLEANUP a — docstring: line ~976 still says "AK divergence → halt build". Update to reflect
   warning-not-halt + the reverse-reckoning.
5. CLEANUP b — esoteric inconsistency: _build_esoteric_rows (~L1073) computes AK Parāśarī-only (Rāhu
   excluded) while _build_karaka_rows runs both schools. DECISION REQUIRED FROM NATIVE: should the
   esoteric points (Brahma/Vishnu/Shiva) also carry both schools, or stay Parāśarī-only? Do NOT change
   it unilaterally — implement only the choice the native makes; until then, leave as-is and add a
   `# NOTE: Parāśarī-only by current design; see AK reckoning brief §2.5` marker.
6. Run the ga_sensitive tests green. COMMIT:
   fix(ga_sensitive): KN Rao Ātmakāraka reckons Rāhu reverse-degree (removes false AK divergence)
7. REBUILD ga_sensitive for 1c826d5a via execute_run (cloud job image must carry this commit — check
   job_image_tag, rebuild the job image if stale per BUILD_TRACKER_WRITER_FIXES_PERSIST_BRIEF).
   Confirm the [GA5] AK-divergence warning no longer logs for this chart and the stored KN Rao AK =
   Mercury in the 4 affected ayanāṁśas, Mars in Surya-Siddhanta.

CONSTRAINTS: 1c826d5a only; never native 482012f1. NOTE: this rebuild should happen AFTER the
ga_positions contamination fix (GA_POSITIONS_CONTAMINATION_BRIEF) lands, since ga_sensitive consumes
positions — rebuilding it on contaminated positions would just re-bake bad data. Sequence: positions
fix → positions+downstream rebuild → THEN this AK rebuild. Deliver: the diff, test results, commit SHA,
and the BEFORE/AFTER stored AK per ayanāṁśa. STOP and report.
```

## §3 — Sequencing note (important)
ga_sensitive depends on ga_positions. The contamination fix (GA_POSITIONS_CONTAMINATION_BRIEF) MUST
land and 1c826d5a's positions be corrected BEFORE re-running ga_sensitive — otherwise the AK rebuild
runs on the native's contaminated positions and proves nothing. Order:
1. ga_positions contamination fix + rebuild (positions + downstream) on 1c826d5a.
2. THEN this AK reckoning fix + ga_sensitive rebuild.
The CODE change here can be written/committed/tested anytime; only the REBUILD step is order-dependent.

## §4 — Done when
KN Rao AK ranks Rāhu by reversed degree (cited), the false divergence is gone for 1c826d5a, the guard
still fires on genuine divergence (test-proven), the stale docstring is fixed, and the esoteric
inconsistency is resolved per the native's explicit choice.
