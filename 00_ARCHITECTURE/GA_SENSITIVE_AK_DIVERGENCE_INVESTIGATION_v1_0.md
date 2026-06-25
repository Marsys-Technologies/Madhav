---
artifact: GA_SENSITIVE_AK_DIVERGENCE_INVESTIGATION_v1_0.md
canonical_id: GA_SENSITIVE_AK_DIVERGENCE_INVESTIGATION
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
purpose: >
  Determine WHY the ga_sensitive Ātmakāraka (AK) divergence fires for Abhinandan Mohanty (1c826d5a) —
  separating a legitimate doctrinal split (Parāśarī 7-graha vs KN Rao 8-graha) from a possible
  reckoning bug (KN Rao reverse-degree not applied to Rāhu). Read-only diagnosis; no writer changes
  until the native rules on the finding.
audience: Claude Code (Antigravity)
---

# ga_sensitive AK-divergence — root-cause investigation

## §0 — The question
The build logs `[GA5] AK divergence (non-fatal)` for 1c826d5a: Parāśarī and KN Rao disagree on the
Ātmakāraka. We want the ASTROLOGICAL why (which planet vs Rāhu, by how much, in which ayanāṁśas) AND
a CODE-CORRECTNESS check (is KN Rao's reverse-degree reckoning applied to Rāhu?).

## §1 — What the code does today (Cowork audit, file
`platform/python-sidecar/ga_writers/ga_sensitive_writer.py`)
- `_build_karaka_rows` (~line 968): AK = highest `degree-in-sign` (`long % 30`).
  - Parāśarī set = 7 grahas, Rāhu EXCLUDED (`grahas_7`, ~line 982).
  - KN Rao set = 8 grahas, Rāhu INCLUDED at **raw** longitude (`grahas_8 = {**grahas_7, "Rahu": rahu_long}`, ~line 992).
  - Both sorted by the SAME `_deg_in_sign(long) = long % 30` (~line 995-999). **No `30 − deg`
    reversal is applied to Rāhu.**
  - Divergence flag = `parashari_sorted[0][0] != knrao_sorted[0][0]` (~line 1009) → now `logger.warning`
    (was a fatal raise; docstring line ~976 still wrongly says "→ halt build").
- SEPARATE inconsistency: `_build_esoteric_rows` (~line 874) computes AK as "highest degree among 7,
  EXCLUDING Rahu" (Parāśarī-only) — so the esoteric points (Brahma/Vishnu/Shiva) use Parāśarī AK while
  `_build_karaka_rows` emits both schools. Worth confirming this is intentional.

## §2 — The doctrinal background (so the finding can be judged)
The chara-kāraka AK = the graha at the highest degree within its sign (the "soul significator").
Two schools differ on whether Rāhu counts:
- **Parāśarī**: 7 planets only; Rāhu/Ketu are chāyā grahas, excluded.
- **KN Rao**: 8 planets; Rāhu included, and because Rāhu is perpetually retrograde its degree is
  reckoned in REVERSE — i.e. effective degree-in-sign = `30 − (rahu_long % 30)`, NOT `rahu_long % 30`.
The schools can only diverge when Rāhu out-ranks all 7 classical planets on degree-in-sign. WHETHER
Rāhu out-ranks depends entirely on which reckoning is used — so the reverse-degree question is not
academic: it can flip the divergence on or off.

## §3 — PASTE TO CLAUDE CODE (read-only diagnosis on prod :5433; 1c826d5a only)
```
Read-only investigation. Data plane = prod via Cloud SQL proxy :5433. Chart = Abhinandan Mohanty
1c826d5a-41cb-4450-b4dc-59d440e5f75a. Do NOT modify any writer or run any build. Goal: explain WHY the
ga_sensitive AK divergence fires, and whether it is doctrinal or a reckoning bug.

PART A — the degrees (per ayanamsha). From chart_facts (and/or ga_positions) for 1c826d5a, pull the D1
sidereal longitude of all 8 grahas (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu-mean) for
EACH of the 5 canonical ayanamshas. For each graha compute degree-in-sign = longitude % 30. Produce,
per ayanamsha, a table sorted by degree-in-sign descending, with Rahu shown TWICE:
  - rahu_raw   = rahu_long % 30        (what the current code uses)
  - rahu_knrao = 30 - (rahu_long % 30) (proper KN Rao reverse reckoning)
Identify, per ayanamsha:
  - the Parashari AK (highest of the 7, Rahu excluded);
  - the KN-Rao-as-coded AK (highest of 8 using rahu_raw);
  - the KN-Rao-correct AK (highest of 8 using rahu_knrao).

PART B — classify the divergence per ayanamsha:
  - If Parashari AK == KN-Rao-correct AK but != KN-Rao-as-coded AK → the divergence is a RECKONING BUG
    (raw Rahu degree wrongly outranks; reverse reckoning would remove it).
  - If Parashari AK != KN-Rao-correct AK → the divergence is DOCTRINAL (real; Rahu genuinely highest
    even under correct reckoning). Report by how many degrees Rahu beats the runner-up.
  - Report whether the divergence holds in ALL 5 ayanamshas or only some (borderline-degree case if it
    flips near a boundary).

PART C — code cross-check (read only, no edits):
  In platform/python-sidecar/ga_writers/ga_sensitive_writer.py confirm:
  1. _build_karaka_rows sorts Rahu on raw `long % 30` with NO 30-deg reversal (quote the lines).
  2. Whether any upstream step already reverses RAH_MEAN before it reaches all_longs (grep the writer +
     its context builder + the pyjhora_adapter for any 30 - / reverse / retrograde handling of Rahu).
     If Rahu is already reversed upstream, the raw-degree sort is correct and there is NO bug — say so.
  3. Note the intra-file inconsistency: _build_esoteric_rows computes AK Parashari-only (excludes Rahu)
     while _build_karaka_rows runs both schools — confirm and flag (do not fix).

DELIVER: the per-ayanamsha degree tables (with rahu_raw vs rahu_knrao), the per-ayanamsha
classification (doctrinal vs reckoning-bug vs borderline), the exact code lines for the Rahu reckoning,
the answer to whether Rahu is reversed upstream, and a one-paragraph verdict: "the AK divergence for
this chart is [doctrinal / a reckoning bug / borderline] because …". STOP and report. Recommend NO code
change yet — the native rules on the verdict.
```

## §4 — How to read the result (decision tree for the native)
- **Verdict = doctrinal** → the divergence is real Jyotiṣa; the warning-not-halt fix is correct, and
  both AK rows belong in chart_facts as a genuine cross-school contradiction for L2 to weigh. Only
  cleanup left: fix the stale "→ halt build" docstring; decide if esoteric-points should also carry
  both schools.
- **Verdict = reckoning bug** → KN Rao's Rāhu reverse-degree is missing; the "divergence" is partly an
  artifact. Then a follow-up writer fix applies `30 − (rahu_long % 30)` for the KN Rao set ONLY (never
  touch Parāśarī), re-runs ga_sensitive for 1c826d5a, and confirms whether the warning clears. This is
  a real correctness finding (B.10 / canonical-value discipline), authored as its own brief.
- **Verdict = borderline** → flags near an ayanāṁśa boundary; document as a known sensitivity, keep
  both rows, no code change.

## §5 — Guardrails
Read-only; no writer edits, no builds, in this pass. 1c826d5a only; never native 482012f1. The fix that
already landed (halt→warning) is NOT in question here — this investigates the underlying divergence, not
the error-handling. Any code change is a SEPARATE, native-approved follow-up.
