---
artifact: DISCOVERY_ENGINE_ACCURACY_TEST_v1_0
version: 1.0
status: CLOSED (point-in-time test; repeat after R6 Wave C lands)
date: 2026-07-10
author: Cowork (Fable-5)
method: >
  Blinded retrodiction. Lane 1 (blind extractor, no LEL access) probed every live
  discovery/convergence MCP surface for chart 482012f1 and normalized all time-indexed claims.
  Lane 2 (scorer) held LIFE_EVENT_LOG_v1_2.md (v1.7, 57 events, 1984–2026) as answer key and
  scored hit/miss/false-alarm. Read-only; no outcomes recorded to mimamsa.
chart: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek; born 1984-02-05)
caveats: n=1 chart; wide windows inflate hit rates; scorer judgment on theme-matching is
  qualitative; several engine surfaces were dead/empty at test time (see §4), so this grades
  what the engine SERVES today, not its design ceiling.
---

# DISCOVERY ENGINE — RETRODICTIVE ACCURACY TEST (2026-07-10)

## §1 — What the engine actually claimed (dated, scoreable)

The entire dated retrodictive claim set for 2000–2026 reduces, after dedup, to ~10 claims from
two sources (the L4 anchor surface and the L3 life-arc), all positive/"elevated" valence:

- **A. Two overlapping career windows** (posterior 0.4629, the only above-floor score in the estate):
  career_entry 2022-04-29→2024-10-11 and 2023-01-17→2025-07-02. Basis: Saturn@Aquarius transit cycle.
- **B. Transition + spiritual_turn claims in the same two windows** (0.322 / 0.266, ~25 duplicate rows each).
- **C. Three overlapping "transition" windows 1993–1998** (0.322), same Saturn-cycle basis.
- **D. Life-arc "peak" flags:** Mercury MD 2010–2027 (whole period); sub-peaks Mars 2019-20,
  Rahu 2020-22, Saturn 2024-27; pre-2000 peaks 1989-97.
- **E. Pre-birth claims:** anchors 1964-01-27→1966-07-12 and 1966-11-03→1969-04-17 tagged
  "near"; life-arc parvas from 1950. (Auto-scored false; register T-5/T-9.)

**Coverage: 2000-01-01 → 2022-04-28 contains ZERO dated anchor claims at any confidence.**
The L3 convergence layer proper (kala_activation, temporal bundle, convergence/obstruction)
served 0 rows; bodha_discoveries_get is dead (500); projections are one duplicated window
(2027-10-20→2030-04-03 ×50).

## §2 — Scoring against the LEL

Answer key: 15 major/life-altering dated events in 2000–2026 (grandfather 2009 · MBA 2011 ·
R#3 2012 · MBA grad + Mahindra + father's illness onset + marriage 2013 · employer crash 2016 ·
Tech Mahindra 2017 · father's death 2018 · US move 2019 · twins 2022 · US return/job loss +
Tepper + Marsys founding 2023 · mining launch 2024 · scam + first big contract 2025).

### Hits
| Engine claim | LEL match | Quality |
|---|---|---|
| Career windows 2022-04→2025-07 (A) | US return + job loss (2023-05), Tepper completion (2023-06), **Marsys founding (2023-07)**, mining launch (2024-02) | **GENUINE HIT** — "career_entry" for a man entering entrepreneurship in that window is semantically apt; the union window brackets the largest career transformation of the native's life |
| Transition claims same windows (B) | Salaried→entrepreneur pivot, India return | HIT (same window, adds no independent information) |
| spiritual_turn 2022-04→2024-10 (B) | Practice intensification 2024 (major, spiritual) | MARGINAL HIT (year-approx event at window edge) |
| Mars sub-peak 2019-20 (D) | US move 2019-05 (life-altering, positive) | HIT, coarse |
| Saturn sub-peak 2024-27 (D) | Mining launch 2024-02, contract 2025-07, hearing clear 2026-04 | HIT on positives — but the window also contains the May-2025 scam (major, negative), which "peak/positive" mislabels |
| 1993–98 transitions (C) | Headache onset ~1995 (significant, NEGATIVE) inside window; R#1 start 1998-02-16 missed by 25 days (window ends 01-22) | THEME/VALENCE MISMATCH — window right, claim content wrong |
| Mercury MD 2010–2027 "peak: intellect/commerce" (D) | MBA, corporate rise, US, founding — directionally right | UNFALSIFIABLE (17-year window; also contains father's death, separation, scam) |

### Misses (major events with no dated claim of any kind)
Marriage 2013-12-11 (life-altering) · father's kidney onset 2013 · employer crash 2016 ·
Tech Mahindra switch 2017 · **father's death 2018-11-28 (life-altering)** · grandfather 2009 ·
XIMB MBA 2011 · panic episode 2021-01 · **scam 2025-05 (major, negative)** ·
twins 2022-01-03 (inside window A, but claimed as career_entry, not childbirth).

### The starkest single finding
The synthesis brief's judgment block marks **childbirth: DENIED (grade 5.0/10)** for a native
whose twin daughters were born 2022-01-03 — inside the engine's own strongest window. Whatever
that denied-block is computing, it is contradicted by the ground truth the system itself stores
(the LEL intake will make this visible to L5; today LEL serves 0 events via MCP, register T-11).

## §3 — Metrics (honest, n=1)

| Metric | Value | Note |
|---|---|---|
| Temporal coverage of 2000–2026 by dated claims | **~12%** (one ~3.2y window union) | Everything else is empty or unfalsifiably wide |
| Recall on 15 major events | **~4–6/15 (27–40%)**, all inside the one window | 0 hits outside 2022–2025 |
| Recall on NEGATIVE major events (5) | **0/5 (0%)** | Engine emitted zero adverse-valence dated claims anywhere, ever |
| Skill vs base rate | LOW | Native averages a major career event every ~2.4 years; a random 2.5y window hits one with p≈0.7 — the career hit clears this bar only modestly |
| Discrimination | Near-zero | All confidences at the 0.322 uniform floor except one 0.4629; duplicates ×25-31 |
| Calibration (engine's own L5 strata) | Broken | Predictions scored [0.5,0.6) → 0% observed (n=55); [0.6,0.7) → 3.6% (n=28) |
| Absurdity check | FAIL | Pre-birth anchors (1964/1966) served as "near" predictions; parvas from 1950 |

## §4 — Diagnosis: why the engine behaves this way

The engine's living signal today is effectively ONE thing: the **Saturn-in-Aquarius transit
cycle** — which for this chart is Sade Sati (Saturn over natal Aquarius Moon). That single
signal is genuinely informative (the 2022–25 window it flags IS the native's Sade Sati peak,
and it did coincide with job loss, return, separation-era upheaval, and the founding of Marsys —
correct in substance, mislabeled in valence). Everything else is dark:

1. **kala_activation empty** (register T-4) — the dasha×transit convergence layer contributes zero claims.
2. **Ephemeris sidecar dark** (T-1) — no transit gating beyond the one baked-in Saturn cycle.
3. **bodha_discoveries_get dead** (R-9) — the discovery surface itself is unreachable.
4. **No lifetime clipping** (T-5/T-9) and **no dedup** (T-6) on what remains.
5. **No adverse-event model** — every claim is "elevated/positive"; dosha/bhanga signals never
   reach anchors (Section 1 of the register: the honest yoga engine is unwired, cancellations
   unimplemented).
6. **LEL not served** (T-11) — the calibration loop that would have caught the childbirth-denied
   contradiction is open-circuited.

## §5 — Verdict + what would move the needle

**Verdict: the discovery engine, as served today, is not yet an instrument — it is one correct
Sade Sati signal wrapped in duplication, positive-only bias, and dead infrastructure.** It found
the right 3-year window for the biggest transformation of the native's life and correctly typed
it as career — that is a real, non-trivial success and worth preserving as the baseline. It
missed everything else, cannot see adverse events at all, and its own calibration table already
knows its confidence scores don't mean anything.

Needle-movers, in order (all already in DEFECT_GAP_REGISTER v2.0):
1. **T-4 + T-1** — populate kala_activation and revive the transit sidecar: multi-signal
   convergence is the engine's entire design premise and is currently absent.
2. **T-11** — LEL intake, so L5 can score anchors against events and the childbirth-class
   contradictions surface automatically.
3. **Section 1 (Y-rows)** — wire honest yogas/doshas with cancellations into anchor generation
   so adverse-event claims become possible (0% negative recall is a design hole, not a tuning issue).
4. **T-5/T-6/T-9** — lifetime clipping + dedup (mechanical trust repairs).
5. Re-run THIS test (blinded, same protocol) after Wave C — the metrics table in §3 is the baseline.

*Repeat protocol: blind extractor probes → normalized claims table → LEL scoring → same 7 metrics.*
