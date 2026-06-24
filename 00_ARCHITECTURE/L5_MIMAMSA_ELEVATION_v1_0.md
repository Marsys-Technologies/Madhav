---
artifact: L5_MIMAMSA_ELEVATION_v1_0.md
canonical_id: L5_MIMAMSA_ELEVATION
version: 1.0
status: DRAFT — the ambitious-vision elevation: lifecycle/determinism/no-LEL design + tiered external-knowledge candidate catalog + the segregated controllable signal-family matrix
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The "take stock of what we will elevate" deliverable. Three parts: (A) the settled design facts from
  the native's 2026-06-22 directive — L5 as a purely deterministic overlay, its build-time + LEL-update
  lifecycle, and how it operates with NO LEL; (B) the curated, evidence-tiered catalog of external-
  knowledge candidate signal-families (astrophysics / chronobiology / statistical-astrology /
  esoteric), distilled from deep research, INCLUDING the negative-control battery; (C) the segregated,
  controllable signal-family matrix that lets each domain influence the deterministic reading while
  staying independently switchable, tier-labeled, and calibration-scored. Feeds the decision-closure
  re-walk of the 15 open decisions.
research_provenance:
  - deep-research pass 2026-06-22 (astrophysics/space-weather catalog + chronobiology/statistical-astrology/esoteric catalog); real peer-reviewed citations inline
native_decisions_2026_06_22:
  - "L5 is PURELY DETERMINISTIC — no judgment in the layer; all judgment is the LLM's at synthesis/serve time via the retrieval tools"
  - "L5 is an OVERLAY — never built into the upper layers; deterministic upper-layer values stay segregated"
  - "Overlay is chart-specific (L1–L5); never L0 (global)"
  - "Lifecycle: compute at end of the build DAG; re-compute on LEL update (ongoing)"
  - "Must define no-LEL operation"
  - "Elevate beyond the corpus: incorporate astrophysics/modern-science + esoteric knowledge with HIGH-CONFIDENCE correlation, tier-labeled"
  - "Each external domain = an independently controllable channel in a segregated matrix; full influence over deterministic data but fully switchable; admitted only if astrologically OR scientifically sound"
depends_on_artifacts:
  - L5_MIMAMSA_VISION_v1_0.md · L5_LEARNING_PROPAGATION_v1_0.md · L5_CONTRIBUTION_CONTROL_v1_0.md · L5_MIMAMSA_INDEX_v1_0.md
---

# L5 Mīmāṃsā — The Elevation (lifecycle · external-knowledge catalog · controllable matrix)

> The differentiator. This is where L5 stops being "a calibration table" and becomes the layer that
> (a) recomputes itself honestly as life unfolds, (b) reaches beyond the classical corpus into
> high-confidence external correlations — held to a strict evidence bar — and (c) keeps the native in
> total control of which of those influences touch the reading.

---

## PART A — The settled design (deterministic overlay · lifecycle · no-LEL)

### A.1 — L5 is a purely deterministic overlay; judgment lives with the LLM
**Ruling:** L5 contains **no judgment**. Every `mi_*` asset is deterministic computation (scoring math,
multipliers, overlays) — reproducible, auditable, Python. The *interpretive* judgment happens **only at
synthesis/serve time**, where the LLM pulls deterministic facts + signals + the L5 overlay **through the
retrieval tools** and narrates. The LLM is never inside L5; L5 produces the controllable ingredients the
LLM reasons over.

Consequences (consistent with the prior artifacts):
- L5 writes its own `mimamsa_*` tables; **the upper-layer deterministic values are never mutated**
  (`L5_LEARNING_PROPAGATION_v1_0.md` §3 — overlay, strict base/effective segregation).
- The overlay is **chart-specific** (L1→L5); **L0 is never touched** (global, classical, priors locked).
- No generative LLM computes any L5 number; embeddings (deterministic transforms) are allowed.

### A.2 — Lifecycle: when L5 computes (the trigger model)
L5 sits at the **end of the build DAG** and recomputes on **LEL change**. Concretely:

**Trigger 1 — Build (end of DAG).** When a guest/super-admin creates a client profile and clicks Build,
L0 pre-exists (global) and L1→L5 build in DAG order (mostly sequential). L5 runs **last**, after the
deterministic layers it depends on (L1, L3, L4, partly L2) are present, and populates the overlay from
*whatever deterministic information + LEL is available at that moment*.

**Trigger 2 — LEL update (the ongoing path).** LEL is not static — events arrive over time: the native
logs them directly, or logs them **in response to the prediction journal** L4 produced, or via other
channels. Each new admissible event is new ground truth, so L5's calibration must re-sync. **Recommended
re-sync policy (the "right time"):**

| event | re-sync behavior | rationale |
|---|---|---|
| New LEL event(s) recorded | Mark L5 **stale** for that chart; recompute L5 **incrementally** (only the `mi_*` assets that consume LEL: `mi_jivanaghatana` → `mi_pramana` → `mi_gunanaka` → overlays). Upper layers L1–L4 are NOT rebuilt (they don't depend on LEL). | LEL only flows UP into L5; nothing below consumes it, so a full chart rebuild is wasteful + wrong |
| Batch of events / journal-response session | **Debounce**: coalesce a burst into one recompute (e.g. on session-close or a short timer) rather than recomputing per event | avoids thrash when a user logs ten events in a sitting |
| Prediction comes **due** (eval_date passes) with candidate evidence | Flag for recompute on next sync; the verdict is computed when admissible evidence exists | respects the falsifiability lifecycle (ph_pramana PR3 staging) |
| Manual "recalibrate" action (portal/MCP) | Force a full L5 recompute for the chart | operator escape hatch |

**Key invariant:** because L5 is an overlay and LEL flows only upward, **an LEL update triggers an
L5-only recompute, never an L1–L4 rebuild.** This is cheap, fast, and keeps the deterministic base
stable. (The `learning_influence` toggle still governs whether the refreshed overlay is *applied* at
serve time.)

**Cockpit/state:** L5 carries a freshness marker (`lel_version` / `last_calibrated_at`) so the build
tracker can show "L5 in sync with LEL vN" vs "L5 stale — N new events pending."

### A.3 — The no-LEL case (how L5 operates with zero life events)
A native may have **no LEL at all** (new client, or chose not to log events). L5 must still be valuable
and must never fabricate calibration. Design:

- **L5 still builds and is fully available** — but in **structural-only mode**. With no outcomes to
  score, the calibration pillar produces **no empirical multipliers** (no fabricated numbers, B.10).
- **What L5 still contributes with no LEL:**
  1. **The falsifiability + prediction registry** (`mi_bhavisya` from `phala_pramana`) — the chart's
     predictions are still staged, time-indexed, and *ready to be scored* the moment events arrive.
  2. **The external-knowledge signal-families** (Part B) that are **chart/time-anchored, not
     LEL-dependent** — e.g. the photoperiod-at-birth feature, the lunar-phase-at-event feature. These
     are deterministic from the chart + ephemeris and can enrich the reading as **prior-tier** signals
     (their *classical/scientific prior weight*, since no empirical weight has been earned yet).
  3. **Self-examination + export integrity** (`mi_pariksha`/`mi_vistara`) — unaffected by LEL.
- **What is honestly withheld:** any *empirical* calibration claim ("we are right 70% of the time"),
  any *learned* multiplier. With no LEL, `learning_influence` ON yields only **prior-tier** modulation
  (the classical/scientific priors of admitted signal-families), never empirically-earned modulation.
- **The contribution metadata says so:** `contribution_state` reports `lel_status: absent` and
  `calibration_mode: structural_prior_only`, so the user knows the enhancement is prior-based, not
  track-record-based.

> Net: no-LEL L5 = "the instrument primed to learn" — predictions staged, priors available and
> controllable, zero fabricated calibration. The first logged event begins the empirical loop.

---

## PART B — The external-knowledge candidate catalog (tiered; the elevation)

The native's bar: **high-confidence correlation only, tier-labeled; included only if astrologically OR
scientifically sound; esoteric allowed but never dressed as science.** From the deep-research pass, the
candidates below are organized by **evidence tier** and by **how they bind** (natal vs event-date). Real
peer-reviewed citations are carried so each candidate is auditable.

### B.1 — TIER-1 SCIENCE (established, peer-reviewed) — admit as real, low-but-nonzero prior
These are genuine science. Crucial honesty: most are **seasonal/photoperiod/space-weather**, mechanistic
(vitamin-D, infection, geomagnetic), **not "planetary"** — but they are astronomically *legible* (they
bind to solar declination / lunar phase / geomagnetic index at a date) and so can ride the same
time-index the chart uses.

| id | signal-family | correlation (1-line) | binding | anchor citation |
|---|---|---|---|---|
| X-PHOTO | Birth-season / photoperiod | Season-of-birth shifts risk for schizophrenia, MS, lifespan; photoperiod at birth imprints physiology | **natal** (solar declination + photoperiod at birth date/latitude) | Davies *Schizophr Bull* 2003; Willer *BMJ* 2005; Doblhammer & Vaupel *PNAS* 2001 |
| X-SOLARYR | Solar-cycle phase at birth | High-sunspot birth/gestation years → lower survival/lifespan/fertility (folate pathway) | **natal** (sunspot number in birth year) | Skjærvø et al. *Proc R Soc B* 2015 |
| X-GEOMAG | Geomagnetic activity on event day | Higher Kp/Ap → more acute-MI, lower HRV, small mortality uptick | **event-date** (Ap/Kp ±1–3d) | Normative Aging Study *Sci Total Environ* 2022; *Environ Health* 2019 |
| X-SEASON | Circannual physiology | ~25% of transcriptome seasonal; vitamin-D, TSH, testosterone circannual | **event-date** (season + latitude) | Dopico *Nat Commun* 2015; Hyppönen *AJCN* 2007 |

**Guardrail baked in:** every Tier-1 family must be scored against a **seasonality/weekday/temperature
null model** (seasonality is the universal confound) and, for collinear pairs (geomagnetic ↔ cosmic-ray
↔ season), encoded **together**, never as independent terms.

### B.2 — TIER-2 PLAUSIBLE (mixed but real signal) — admit as testable low-weight prior
| id | signal-family | correlation | binding | note |
|---|---|---|---|---|
| X-LUNARSLEEP | Lunar phase → sleep/mood | Sleep later/shorter pre-full-moon (moonlight-driven) | event-date (tithi) | Cajochen 2013 / Casiraghi 2021 vs Cordi 2014 — contested; maps naturally onto the Vedic tithi frame |
| X-TIDALBIP | Tidal cycle → rapid-cycling bipolar | Mood switches entrain to ~14-day tidal-amplitude cycle | event-date (tidal day) | Wehr 2018 — tiny-n; a *different* lunar quantity than X-LUNARSLEEP |
| X-PHOTOIMP | Perinatal photoperiod imprinting (clock/monoamine) | Day-length at birth biases chronotype/mood-seasonality | natal | strong in rodents, weak/age-dependent in humans |

### B.3 — TIER-3 / ESOTERIC + CLASSICAL-CONVERGENCE (tradition-grade) — admit under classical-citation discipline ONLY
Never claimed as physical causation. Computable + textually-cited; weak but structured.

| id | signal-family | basis | binding | provenance note |
|---|---|---|---|---|
| T-NAKPADA | Nakṣatra-pada akṣara | fixed syllable per 108 padas; nāmakaraṇa rite | natal (Moon pada) | cleanest in corpus — Vedāṅga Jyotiṣa / BPHS / Gṛhya-sūtras |
| T-DASHA | Vimśottarī (and declared alt) daśā | 120-yr nested planetary time-index from Moon nakṣatra | **lifetime time-index** | BPHS; the single most important classical time-index — *versioned declared choice* |
| T-CONVERGE | Cross-tradition convergence | independent traditions agreeing = weak corroboration | meta-tag | **HARD RULE: Vedic↔Western = common descent (ONE datum). Only Chinese (gānzhī/BaZi) + pre-Hellenistic indigenous nakṣatra/daśā count as independent corroboration** (Pingree; Needham) |

### B.4 — THE NEGATIVE-CONTROL BATTERY (the surprise differentiator) — admit as TRAPS that MUST score null
The most valuable research output. These are **known-false** or **physically-negligible** claims with
the *surface form* of a real signal. L5 loads them as **negative controls**: if the calibration harness
assigns any of them non-trivial empirical weight against the LEL, **the harness is detecting its own
leakage/over-fitting**, not a real effect. This is how L5 *proves its own discriminative validity* — a
capability no astrologer and no astrology product offers.

| id | false signal | status | source |
|---|---|---|---|
| NC-BIORHYTHM | 23/28/33-day biorhythms | FALSIFIED (134-study review) | Hines *Psychol Reports* 1998 |
| NC-FLIESS | Fliess 23/28-day cycles | same thing in costume | Fliess 1906; RS *Notes & Records* 2024 |
| NC-LUNARED | Lunar phase → ER/birth/crime | DEBUNKED (≤1% variance; null at 70M births) | Rotton & Kelly *Psychol Bull* 1985 |
| NC-CARLSON | Astrologer chart-matching | ROBUST NULL (double-blind, chance) | Carlson *Nature* 1985 |
| NC-CFEPP | Mars-effect neutral replication | ROBUST NULL | Benski et al. 1996 |
| NC-TWINS | Time-twins trait convergence | ROBUST NULL (NCDS n=2,101) | Dean & Kelly 2003 |
| NC-SUNSIGN | Sun-sign extraversion | self-attribution artifact (vanishes in naïve subjects) | Mayo/White/Eysenck 1978 |
| NC-BODYTIDE | Human gravitational "biological tides" | PHYSICALLY FALSE (~7×10¹² too weak) | Tyson 1995 |

> **Why this matters:** the Mars-effect history (sTARBABY, Dean's birth-time-tampering hypothesis)
> teaches that a credible harness grades **method** (pre-registration, blinding, independent
> replication, pre-specified scoring), not side. The negative-control battery operationalizes exactly
> that — it's the instrument's self-skepticism, made mechanical.

---

## PART C — The segregated, controllable signal-family matrix

The native's requirement: each external domain must be able to **influence the deterministic data** yet
be **independently controllable** — a segregated matrix where we govern what impacts what. This **extends
the existing contribution-control framework** (`L5_CONTRIBUTION_CONTROL_v1_0.md`): each signal-family is
a **channel** in the same registry, with the same toggle/parity/metadata machinery.

### C.1 — Every candidate is a registered signal-family channel
```
signal_family_registry row:
{
  family_id,                 -- e.g. X-GEOMAG, T-NAKPADA, NC-BIORHYTHM
  display_name, layman_name,
  evidence_tier,             -- TIER1_SCIENCE | TIER2_PLAUSIBLE | TRADITION | NEGATIVE_CONTROL
  soundness_basis,           -- "scientific" | "astrological" | "both"
  binding_kind,              -- natal | event_date | lifetime_index | meta
  default_state,             -- ON | OFF | CONTROL_ONLY (see C.3)
  prior_weight,              -- classical/scientific prior (pre-calibration)
  calibration_status,        -- prior_only | earning | promoted | suspended
  citation_refs[],           -- audit (real sources)
  apply_point                -- which overlay surface it modulates
}
```

### C.2 — How a family influences the deterministic data (still overlay, still bounded, still dedup'd)
A family does **not** mutate L1–L4. It contributes a **bounded, evidence-scaled overlay** at a defined
apply-point (per `L5_LEARNING_PROPAGATION_v1_0.md`): e.g. X-PHOTO adjusts the salience of birth-season-
linked health signals; X-GEOMAG adjusts an event-window's confidence on the event date. **Single-origin
attribution still holds** — a family's adjustment attaches to its origin and propagates read-side,
applied once. Families are just *additional, labeled origins* of overlay adjustments, governed by the
same bounds, the same `learning_influence` master switch, and (newly) their **own per-family switch**.

### C.3 — The control surface (the segregated matrix)
- **Per-family toggle** — every family is independently switchable (ON/OFF), inheriting the
  per-request-over-saved-default scope and portal/MCP parity from the contribution framework.
- **Tier-grouped master controls** — convenience switches: "all Tier-1 science ON," "all tradition-grade
  ON," "all OFF" — without losing per-family control.
- **Negative controls are `CONTROL_ONLY`** — never applied to a reading; they run only inside the
  calibration harness as validity traps. They cannot be toggled "on" into a response (a safety rail).
- **`soundness_basis` filter** — the user can say "only scientifically-sound families" or "only
  astrologically-sound" or "both," matching the native's "astrologically OR scientifically sound" bar.
- **Everything is metadata-transparent** — `contribution_state` lists which families were active and
  how each was resolved; the provenance endpoint can explain any family's contribution + its tier +
  its citations.

### C.4 — The calibration spine keeps them honest
Each non-control family enters the **same calibration loop**: it starts at `prior_only` weight; as
admissible LEL accrues, it moves to `earning`, and only `promoted` (past the min-n + held-out gate)
after it demonstrably tracks outcomes; it is `suspended` if it degrades. So "more signals" never means
"more noise applied blindly" — a speculative family must **earn its empirical weight** exactly like a
classical signal, and the negative controls continuously verify the scorer isn't fooling itself.

### C.5 — The matrix, at a glance
```
                         soundness   default        applied to reading?     in harness?
 TIER1_SCIENCE  X-PHOTO   scientific  ON (prior)     yes (bounded overlay)   scored
 TIER1_SCIENCE  X-GEOMAG  scientific  ON (prior)     yes                     scored vs season-null
 TIER2_PLAUSIBLE X-LUNAR  both        ON (low prior) yes (low weight)        scored
 TRADITION      T-NAKPADA astrological ON            yes                     scored (weak)
 TRADITION      T-DASHA   astrological ON            yes (time-index)        scored
 TRADITION      T-CONVERGE astrological ON           meta-weight only        independent-only
 NEGATIVE_CTRL  NC-*      —           CONTROL_ONLY   NEVER                   trap (must score null)
```

---

## PART D — How this reshapes the open decisions (preview of the closure re-walk)

The native's directive answers or reframes several open decisions. Captured here; to be confirmed in the
decision re-walk:

- **N17 sharpened** → L5 fully deterministic; judgment only at LLM synthesis via retrieval. (settled)
- **New: lifecycle** → build-end trigger + LEL-update incremental recompute (L5-only, debounced); freshness marker. (A.2)
- **New: no-LEL mode** → structural-prior-only; predictions staged; external families at prior weight; no fabricated calibration. (A.3)
- **New: external-knowledge matrix** → tiered candidate catalog + per-family controllable channels + negative-control battery. (B, C)
- **V1 (build scope)** → now must include (i) the calibration spine, (ii) the signal-family registry +
  the Tier-1/tradition families that bind cleanly, (iii) the negative-control battery. Lean: core +
  the cleanest-binding families (X-PHOTO, X-GEOMAG, T-NAKPADA, T-DASHA) + all negative controls.
- **V7 (metrics)** → add a **discriminative-validity metric**: the harness must score the negative-control
  battery ≈ null; report that as a headline trust indicator.
- **C1 (per-domain toggles)** → upgraded: the matrix already implies **per-family** control; v1 can ship
  per-family ON/OFF + tier-group masters (richer than the original "global only" lean).
- **P-series (bounds/caps)** → external families inherit the same bounded + evidence-scaled overlay;
  Tier-1 science families may merit a slightly higher prior_weight than Tier-2/tradition (native sets).

---

## PART E — Value-vs-divergence ruling (the n=1 honesty gate)

**The assessment (native asked "do these add value to the learning system or divergence?"):** With n=1
(~57 LEL events, ~9/domain), admitting many external families as *learning inputs* is a multiple-
comparisons hazard — the most likely outcome is that 2–3 spuriously correlate and falsely promote
(exactly the failure mode behind the field's famous false positives). As **priors/enrichment**, the
well-evidenced natal families (X-PHOTO, X-SOLARYR) are genuinely additive. The **negative-control
battery is value-add of a higher order** — it doesn't compete for evidence, it *protects* it, by
detecting whether the divergence risk has fired. Net: the families are a differentiator as a controllable
enrichment matrix, and a divergence risk only if allowed to learn freely — so the discipline below is
what converts the risk into a managed one. (Note: **Vimśottarī/T-DASHA is core L3/L4 spine, not an
external elevation** — categorization corrected.)

**Native rulings 2026-06-22 (these interlock):**

| id | ruling | consequence |
|---|---|---|
| **E1** | **External families are learning-eligible NOW, behind a HARD promotion gate.** They contribute as controllable priors immediately AND may earn empirical weight — but only past the strict gate (E2). | ambition kept; divergence contained by the gate, not by exclusion |
| **E2** | **Promotion is VERY STRICT, n=1-aware** — high per-stratum min-n + held-out validation + negative-controls-pass required before ANY signal (classical OR external) moves prior→empirical. **"Almost nothing promotes at n=1" is the CORRECT behavior, not a failure.** | the SNR of the learning spine is protected; honest under-claiming |
| **E3** | **The negative-control battery is a BLOCKING SEAL GATE.** L5 cannot seal, and no learned weight may promote, if any negative control (NC-*) scores non-null. | self-skepticism is structural; it is what makes E1 safe — the gate that admits families is trustworthy only because the bullshit-detector is blocking |

> **The keystone insight:** E1 (admit families to learning) is only responsible because E3 (blocking
> negative-control gate) exists. The instrument doesn't bet the external families are right — it refuses
> to believe them until they prove it against held-out outcomes, and refuses to seal if its own
> validity check is broken. This is the honest form of the ambitious vision.

---

## PART F — Final decision closure (2026-06-22, plain-language walk-through)

The native asked for every term in plain language, then ruled. All open decisions are now closed.

**Plain-language glossary (for the corpus):**
- **Signal-family** = a source of hunches about the chart (a classical rule; "birth-season affects health"; "geomagnetic storms stress the heart").
- **Prior stage** = a family's opinion counts at textbook/book value; allowed in the room, no special trust.
- **Promotion** = graduating a family from "textbook opinion" to "checked against THIS person's real life and proven to track it → now trusted to move the dial more." 
- **The hard gate** = the tough exam a family must pass to graduate (right across enough events + holds up on sealed events + doesn't trip the lie-detector).
- **n=1-aware** = the system knows it learns from ONE life (~57 events, ~9/domain), so it stays humble; "almost nothing promotes yet" is CORRECT behavior, not failure (the 9-coin-flips lesson).
- **Negative-control battery** = a panel of KNOWN-FAKE signals (biorhythms, full-moon-lunacy, the debunked astrology tests) fed in deliberately as tripwires; they MUST score ~null; if any lights up, the instrument is fooling itself and must not certify. The built-in self-pointed lie-detector.
- **Reverse channel** = the one feedback wire that flows DOWN — learning telling lower layers "this signal oversold itself; ease off next time." A forecaster reviewing yesterday's misses.
- **Held-out** = sealed life events the prediction-builder never saw, used as the honest grade (don't grade yourself on questions you wrote).
- **Multi-chart rails** = designing the tables now to HOLD many charts later (lay the plumbing while pouring the foundation), even though only the native's chart exists today.

**Closed decisions:**

| id | decision | RULING |
|---|---|---|
| **V1** | First build scope | **CORE FIRST** — the essential loop (predict → check vs life → score → gently adjust → lie-detector) + the cleanest-binding external families (X-PHOTO, X-GEOMAG, T-NAKPADA) + the FULL negative-control battery. LL.1–LL.10 (the ten learning machines) are designed-in but switched on later as evidence grows. Walk before run. |
| **V3** | Held-out strategy | **Both, headline the clean one** — grade honestly on sealed/clean events as the headline; report the looser grade too for transparency, but always lead with the honest grade. |
| **V4** | Reverse channel in v1 | **TWO-KEY LOCK (native-sharpened):** a real reading is impacted ONLY when BOTH (a) the hard gate is passed AND (b) confidence is high. Gate-passed-but-low-confidence stays in suggestion mode (logged, not applied). Suggestion mode is the default state; live impact is the earned exception, requiring both keys. Stricter than "promote after gate" — it's "promote after gate AND only where confidence is high." |
| **V5** | Multi-chart rails | **Lay the rails now** — design tables multi-chart-ready (chart-keyed); leave the cohort unpopulated. Cheap now, painful to retrofit. |
| **V6** | mi_pariksha scope | **Predictions-only at v1** — first prove the forecasts are right; grading the written-reading quality + prompt wording comes later. |
| **C2** | MCP shape + **conversational defaults** | **NATIVE-RULED (new):** when a conversation starts (esp. MCP) and it's not yet known whether to use the LEL or apply Mīmāṃsā learning influence, **the assistant ASKS the user** ("Shall I draw on your life events? Shall I apply the learning adjustments?"); once answered, those become the **working session defaults** until changed. The LLM handles this intelligently/conversationally — no silent assumption. (Per-tool args still exist for explicit overrides; the conversational ask is the default UX.) |
| **C3** | LEL-OFF depth | **Suppress the literal injection** — when life-events are OFF, do not quote the native's actual events into the reading. (Paraphrase handling per Cowork rec.) |
| **P1** | Per-layer caps | **Principle locked (tight L1 → wide L4); exact numbers set at build-planning** once ground-truth audit + LEL count confirmed. |
| **P3** | Effective values | **Cached `effective` views**, refreshed per calibration session (the bodha_msr_signals 10-reader fan-out makes live joins expensive). |
| **P4** | FORENSIC exclusion | **Exclude** — the 7 FORENSIC anchors + canonical computed facts are NEVER modulated. |
| **EL1** | Tier prior-weights | **Modest gradient** — Tier-1 science families may start at a slightly higher prior weight than Tier-2/tradition; exact values at build-planning. |
| **EL2** | Debounce trigger | **Session-close + manual force** — coalesce a burst of LEL logging into one recompute at session close; plus an explicit "recalibrate now" action. |
| **EL3** | soundness_basis default | **All admitted-tier families ON by default** (default-ON per the contribution framework); negative controls are CONTROL_ONLY (never applied). User can filter to scientific-only / astrological-only. |

**Also reaffirmed:** V2 (re-point mi_bhavisya at phala_*); V7 (add discriminative-validity headline metric = neg-controls score null); C1 (per-family + tier-group control); E1/E2/E3 (learning-eligible behind hard gate / very-strict n-aware promotion / blocking negative-control seal gate). P2 collapsed into E2.

**THE GOVERNING PRINCIPLE (native, verbatim intent):** *"Strict promotion unless we have high confidence —
anything impacting the reasoning can introduce errors."* This is not just a setting; it is the soul of L5.
Every promotion, every overlay application, every external-family admission resolves in favor of NOT
moving the reading unless the evidence is strong and the confidence is high. The default is restraint;
impact is earned. When in doubt, the instrument leaves the classical reading untouched. (This is why the
V4 two-key lock, E2 very-strict promotion, and E3 blocking lie-detector all point the same direction.)

**Net:** all decisions closed. Remaining "exact numbers" (P1 caps, EL1 weights) are deliberately deferred to the build-planning session that follows the ground-truth audit — principle locked, arithmetic later.

---

*End of L5_MIMAMSA_ELEVATION v1.0. L5 = a deterministic, chart-specific overlay that recomputes at build-end
and incrementally on LEL update (never rebuilding the base), operates honestly in structural-prior-only
mode with no LEL, and reaches beyond the classical corpus into a tiered, cited catalog of external
correlations — each a per-family controllable channel in a segregated matrix, each earning its empirical
weight on the calibration spine, with a negative-control battery that lets the instrument prove its own
discriminative validity. The differentiator: not more assertions, but more controllable, honestly-graded
evidence — and a layer that can show it isn't fooling itself.*
