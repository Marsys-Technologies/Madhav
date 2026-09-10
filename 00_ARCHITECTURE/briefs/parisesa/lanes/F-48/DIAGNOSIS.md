---
lane: F-48
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE
author: SATYA-LEAD (sonnet)
cross_reference: F-47 (same file, same function — `_transit_quality_for_window` is both
  F-48's entire subject and one of the two action_type-blind sub-scores F-47 names. Diagnosed
  together in one read pass and filed as two documents per plan §3 because they carry
  separate finding IDs and separate claim texts; they will very likely converge into ONE SPEC
  at Stage S, or F-48's remediation choice for `_transit_quality_for_window` will directly
  gate what F-47's fix can do with the same function — see F-47 DIAGNOSIS.md §5/§6.)
---

# F-48 — `transit_quality` (20% of composite score) has no real transit computation behind it
(class CL-09, earned signal)

## 1. Live reproduction (today, 2026-08-16, re-verified)

Read `platform/python-sidecar/brahmagyan/phala/muhurta.py:420-465` directly (not summarized —
full function body quoted in §3). Cross-checked against the same three
`kala_muhurta_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, start_date=2026-08-15,
end_date=2026-09-14)` calls used for F-47 (business / marriage / medical, this turn's tool
output): for the identical calendar window (2026-08-19T00:00→2026-08-21T00:00),
`factors.transit_quality = 0.65` in ALL THREE calls regardless of `action_type` — consistent
with a function that takes no `action_type` parameter and performs no planet-specific
computation at all, only a function of the window's start date.

CONFIRMED REPRODUCES exactly as claimed. Not ALREADY-FIXED.

## 2. Claim decomposition

- **C1** — the `transit_quality` field served by `kala_elect_get`/`kala_muhurta_get` (20% of
  the composite score) contains no actual planetary transit computation. Verified in §3 — the
  function body contains zero ephemeris/planet-position logic; only a lunar-phase formula and
  a static day-of-week lookup table.
- **C2** — it is a lunar-phase approximation plus a static day-of-week lookup table. Verified
  verbatim in §3 (both pieces quoted directly from the function body).
- **C3** — a §N.8 earned-signal violation: a signal named "transit quality" with no transit
  detector behind it. This is a direct instance of CLAUDE.md §N.8's own defined defect class
  ("a status, grade, or PASS must be computed by a detector that measures the specific claim
  it asserts") — `transit_quality` asserts "planetary transit strength for this window" but no
  code path in the function ever reads a planet's position, sign, or aspect; nothing exists
  that could make the signal read differently based on any actual transiting planet.
- **C4** — the docstring's own admission: "Full transit computation requires Swiss
  Ephemeris... simplified seasonal approximation... All values are approximations only."
  Verified verbatim in §3 — quoted directly, character-for-character, from the live file.

## 3. Mechanism (file:line, read directly, quoted verbatim)

`platform/python-sidecar/brahmagyan/phala/muhurta.py:420-465`:

```python
def _transit_quality_for_window(window_start: datetime) -> float:
    """
    Approximate transit quality based on known planetary cycles.

    Full transit computation requires Swiss Ephemeris (B.10: no fabricated computation).
    This function uses a simplified seasonal approximation:
      - Jupiter transits ~1 year per sign; currently (2026) in Gemini/Cancer.
      - Saturn transits ~2.5 years per sign; currently (2026) in Aquarius/Pisces.
      - Monthly lunar cycle: full moon weeks generally more auspicious.

    All values are approximations only. For production use, integrate with
    the sidecar's ephemeris engine (/ephemeris endpoint).

    Returns a score in [0.0, 1.0].
    """
    # Simple approximation based on day of lunar cycle (28-day cycle)
    # Using Julian Day approximation:
    #   JD 2451550.1 = 2000-01-06 18:14 UTC (known new moon)
    #   Lunar period = 29.53059 days
    jd_ref = 2451550.1
    jd_window = (
        (window_start - datetime(2000, 1, 1, tzinfo=timezone.utc)).total_seconds()
        / 86400.0
        + 2451545.0
    )
    lunar_phase = ((jd_window - jd_ref) % 29.53059) / 29.53059  # 0.0–1.0

    # Waxing moon (0.0–0.5): generally more auspicious for initiations
    # Full moon peak (0.45–0.55): auspicious
    # Waning moon dark (0.85–1.0): less auspicious
    if 0.45 <= lunar_phase <= 0.55:
        phase_quality = 0.80  # full moon
    elif 0.05 <= lunar_phase <= 0.45:
        phase_quality = 0.65  # waxing
    elif 0.55 <= lunar_phase <= 0.80:
        phase_quality = 0.55  # waning
    else:
        phase_quality = 0.30  # dark moon (near new moon)

    # Day-of-week overlay (some days have inherently stronger transits)
    weekday = window_start.weekday()  # 0=Mon, 6=Sun
    # Thursday (3, Guruvara) and Friday (4, Shukravara) = Jupiter and Venus days
    day_boost = {0: 0.60, 1: 0.55, 2: 0.65, 3: 0.75, 4: 0.70, 5: 0.50, 6: 0.50}
    day_quality = day_boost.get(weekday, 0.55)

    return float(max(0.0, min(1.0, 0.60 * phase_quality + 0.40 * day_quality)))
```

The docstring's admission (C4) is quoted exactly above, character-for-character, from the
live file — no paraphrase. The function body confirms it precisely:
1. **Lunar-phase approximation** — `lunar_phase` computed from a Julian Day offset against a
   fixed reference new moon (`jd_ref = 2451550.1`) and the mean synodic month
   (`29.53059` days); classified into four buckets (`phase_quality` 0.80/0.65/0.55/0.30). This
   is Moon-only; the docstring's own mention of "Jupiter... Saturn... currently (2026) in
   [sign]" appears **only in the docstring's prose**, not in the code — Jupiter and Saturn are
   named as context but never read, computed, or referenced by any variable in the function
   body. The docstring is more honest than the field name, but the code doesn't even fully
   implement what the docstring describes as its "seasonal approximation."
2. **Static day-of-week lookup table** — `day_boost = {0: 0.60, 1: 0.55, 2: 0.65, 3: 0.75,
   4: 0.70, 5: 0.50, 6: 0.50}`, keyed purely by `window_start.weekday()`. A hardcoded constant
   table with no chart-specific or ephemeris-derived input whatsoever.
3. No import of an ephemeris library, no call to `/ephemeris`, no query against any
   `chart_facts`/`chart_dashas`/transit table anywhere in the function — confirmed by reading
   the full function body above; there is no elided code between the `def` line and the
   `return`.

Line-number verification: audit's pin was `muhurta.py:420-465`. Confirmed exact — the function
`def` starts at 420, its closing `return` is at 465 in the current file (verified via direct
read, no drift from the audit corpus).

## 4. Sibling census

Grepped `platform/python-sidecar/brahmagyan/phala/muhurta.py` for every scoring `def` (see
F-47 DIAGNOSIS.md §4 for the full table — reproduced here for this lane's own completeness):

| Function | Line | Real domain computation behind its name? |
|---|---|---|
| `_panchanga_quality_for_action` | 231 | yes — reads real `panchanga_daily` row fields (tithi/vara/nakshatra/yoga) |
| `_dasha_quality_for_chart` | 372 | partial — native branch is a hardcoded FORENSIC-citation constant (0.72), not a live per-window `chart_dashas` re-derivation (see F-47 DIAGNOSIS.md §5 note); non-native branch does query `chart_facts` |
| `_transit_quality_for_window` | 420 | **no — this finding's defect. No transit computation of any kind.** |
| `_signal_activation_for_action` | 468 | native branch is a hardcoded MSR-citation constant per action_type; non-native branch queries `chart_facts` |

`_transit_quality_for_window` is the only one of the four whose docstring itself explicitly
concedes the gap ("Full transit computation requires Swiss Ephemeris... All values are
approximations only") — the other three at least cite a real table or a real per-chart lookup
path, even where (as with `_dasha_quality_for_chart`'s native branch) that path is bypassed by
a shortcut. `_transit_quality_for_window` has no live-data branch at all, native or otherwise
— it is a pure function of the window's calendar date.

**No other file in the S3 lease** (`L4_phala/**`, `L5_mimamsa/**`, `ph_nimitta/**`) implements
a second "transit_quality"-named function — grepped for `transit_quality` and
`_transit_quality` across the sidecar; the only definition is this one, consumed by both
`kala_elect_get` and `kala_muhurta_get` via the shared engine trace in F-47 DIAGNOSIS.md §4.

## 5. Blast radius

- **CL-00 controls:** none of the known CL-00 controls assert on `transit_quality`'s
  computation method — no control regression risk.
- **F-47 (this same stream, this same file, this same function):** `_transit_quality_for_window`
  is simultaneously this finding's entire subject and 20 of the 50 domain-blind composite
  points F-47 names. **These two lanes must not be specced independently** — whichever
  remediation F-48 chooses for `transit_quality` (real computation vs. disclosure) directly
  determines what F-47's fix can do with the same function. See F-47 DIAGNOSIS.md §5/§6 for
  the shared fork.
- **Downstream consumers:** `elect.ts`'s argument-shaped reading (E3, per its own comment at
  `elect.ts:174`: "the data genuinely IS computed by muhurta_finder.ts's enrichWindowsLaneF")
  and any narration layer that reads `factors.transit_quality` and states it as if it reflects
  real planetary transit strength would inherit this gap — out of S3's file lease to fix
  (narration layers are S4's `VĀCA` lease), but worth flagging to SPEC as a downstream
  narration-fidelity (§N.7) consideration if any S3/S4-adjacent copy currently asserts
  "transit quality" without qualification.

## 6. Note for SPEC stage

Per the plan's PRATINIDHI standing rule ("when two remediations are defensible, choose the
one that discloses more"), two remediations are defensible here and are flagged, not resolved:
1. **Compute a real transit signal** — wire `_transit_quality_for_window` (or a
   replacement) to the sidecar's actual ephemeris engine (the docstring's own suggested path:
   "/ephemeris endpoint") to derive real planet-position-based transit strength for the
   window, gated by `action_type` (which would also help close F-47's transit-half gap).
2. **Disclose the approximation** — rename the field (e.g. `lunar_phase_seasonal_proxy`) or
   keep `transit_quality` but attach a structured `computation_method: "lunar_phase_approx"`
   / `is_approximation: true` flag so a caller can distinguish it from a genuinely
   ephemeris-derived score, without necessarily replacing the underlying computation yet.
Given F-47's identical fork over the same function, Stage S should treat these as one
decision, not two.
