---
artifact: L5_CALIBRATION_COMPARISON_MODEL_v1_0.md
canonical_id: L5_CALIBRATION_COMPARISON_MODEL
version: 1.0
status: DRAFT — the core specification of HOW L5 compares predictions to lived events (context-aware, scorecard, many-to-many)
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The heart of L5's honesty: the exact model by which a logged prediction is compared to LEL events.
  Native-ruled 2026-06-22: the comparison is CONTEXT-AWARE (the full frozen prediction bundle, not bare
  outcome-vs-outcome), produces a MULTI-DIMENSIONAL SCORECARD (timing / magnitude / domain / falsifier →
  composite), and matches via DETERMINISTIC MANY-TO-MANY candidate-matching. This scorecard is what makes
  per-signal attribution (Pillar 2 / LL.9) possible. Everything here is deterministic Python.
native_decisions_2026_06_22:
  - "Comparison is context-aware: full prediction bundle (outcome + window + confidence + magnitude + domain + driving signals + falsifier + manifestation_set), NOT outcome-vs-outcome"
  - "Verdict is a multi-dimensional scorecard (timing / magnitude / domain-specificity / falsifier-satisfaction / manifestation → composite), not a single hit/miss"
  - "Matching is deterministic many-to-many (one event → several predictions; one prediction → several events), via the frozen falsifier criteria; not LLM-judged"
  - "Alternate manifestations COUNT (a signal expresses a karmic theme through multiple legitimate channels): domain-bounded matching; GRADED credit (literal=full, alternate-cited=partial, non-falsifier-meeting echo=thematic-resonance-only); HYBRID set generation (classical-cited deterministic spine + flagged citation-gated LLM additions), frozen at emission, NEVER widened post-hoc"
depends_on_artifacts:
  - L5_MIMAMSA_VISION_v1_0.md (Pillar 1 SCORE, Pillar 2 ATTRIBUTE)
  - L5_MIMAMSA_ELEVATION_v1_0.md (pre-registration, the two-key lock, the governing principle)
  - L5_MIMAMSA_GAP_ANALYSIS_v1_0.md (HC-5 pre-registration, R-1 base rates, R-2 null models)
  - ph_pramana falsifier schema {metric, comparison, threshold, observation_window, data_source}
---

# L5 Calibration Comparison Model — How a Prediction Meets Reality

> The native's question: *when an LEL event is compared to the prediction log, is it just the prediction,
> or the CONTEXT of the prediction too?* The answer, ruled: **the full context.** Comparing bare outcomes
> would make the learning shallow, reward vagueness, and make attribution impossible. This document
> specifies the context-aware model.

---

## §1 — Why context-aware (the failure of outcome-only)

A bare comparison ("career change predicted" vs "changed jobs in March" → hit) **throws away everything
that made it a prediction**: the timing, the confidence, the intensity, the domain, the driving signals,
the falsifier. Consequences of outcome-only scoring:
- It **rewards vagueness** — "something career-ish, sometime" scores the same as a precise, in-window,
  right-magnitude call. The instrument would learn to be vaguer.
- It **blocks attribution** — you can't ask "which signal oversold itself" if you didn't keep the
  signals that drove the prediction.
- It **invites rationalization** — without a pre-stated falsifier, any near-miss can be talked into a hit.

A prediction is a **bundle**, and the comparison scores the event against the whole bundle.

---

## §2 — The frozen prediction bundle (what is compared)

When a prediction is emitted (pre-registered per HC-5 / §3.5.E), its full context is **frozen** — locked
before the event so the comparison is honest. The bundle (sourced from `phala_pramana` + `phala_anchors`):

```
prediction_bundle {
  prediction_id,
  outcome_claim,            -- what is claimed to happen
  domain,                   -- career / health / relationship / ...
  observation_window,       -- {start, end} — the predicted time range
  confidence_band,          -- the instrument's stated confidence (the two-key input)
  magnitude_expected,       -- intensity: minor / moderate / major / rupture
  falsifier,                -- the frozen {metric, comparison, threshold, observation_window, data_source}
  manifestation_set[],      -- frozen legitimate manifestations (§5A): classical-cited spine + flagged LLM additions (citation-gated); each {channel, domain, citation_ref, source: classical|llm_flagged}
  driving_signals[],        -- the specific signal_ids + chart logic that produced it (lineage)
  emitted_at,               -- the pre-registration timestamp (admissibility key)
  base_rate                 -- how often this outcome happens anyway (R-1) — the realism anchor
}
```

The `emitted_at` timestamp is the **pre-registration seal**: only predictions frozen *before* an event's
window are admissible as clean calibration evidence (HC-5). The `driving_signals[]` is what makes
attribution possible. The `base_rate` is what makes a "hit" meaningful (a hit on a common event is weak
evidence; a hit on a rare one is strong).

---

## §3 — The multi-dimensional scorecard (the verdict)

A verdict is **not** a single hit/miss. When an LEL event is compared to a bundle, L5 computes a score on
each dimension, then composites. All deterministic.

| dimension | question | how scored (deterministic) |
|---|---|---|
| **Timing accuracy** | Did it happen in the predicted window? | distance of event_date from `observation_window`; in-window = full, near = partial, far = none |
| **Magnitude accuracy** | Was the intensity right? | `magnitude_expected` vs the event's assessed magnitude (minor↔rupture scale) |
| **Domain specificity** | Was it the right kind of event? | `domain` + outcome character match vs the event's domain/character |
| **Falsifier satisfaction** | Does it meet the pre-stated test? | the frozen `{metric, comparison, threshold}` evaluated against the event's `data_source` value — the binding, non-negotiable check |
| **(derived) Base-rate-adjusted skill** | Is this better than chance? | the composite, discounted by `base_rate` (R-1) — credit scales with how surprising the correct call was |

**Composite verdict** = a deterministic function over the dimensions, yielding both:
- a **graded label** (`confirmed / partial / denied / pending`) for the lifecycle, AND
- the **full dimension vector** retained (so "right event, wrong timing" is distinguishable from "right
  timing, wrong magnitude").

> The falsifier dimension is the **judge of record**: a verdict cannot be `confirmed` if the frozen
> falsifier is not satisfied, regardless of how good the other dimensions look. This is the anti-
> rationalization lock — the pre-stated test, not post-hoc narrative, decides.

**Why the scorecard matters (the payoff):** the dimension vector is what makes attribution *precise*. If
timing is consistently off but domain is consistently right across many predictions, the instrument
learns the *what*-signals are sound but the *when*-signals (timing/dāśā logic) are oversold — and damps
the right thing. A single hit/miss could never reveal that. **The scorecard turns a scoreboard into a
diagnostic.**

---

## §4 — Deterministic many-to-many matching

One event can bear on several predictions; one prediction can be touched by several events. Matching is
**computed, not LLM-judged**, from the frozen criteria:

```
for each new admissible LEL event E:
    candidates = all predictions P where
        E.date ∈ (P.observation_window ± tolerance)        -- timing gate
        AND domain_compatible(E.domain, P.domain)          -- domain gate
        AND falsifier_addressable(E, P.falsifier)          -- can E even speak to P's test?
    for each candidate P:
        score E against P's full bundle → scorecard (§3)    -- many-to-many: E may score several P
```

- **Deterministic:** the gates (window, domain, falsifier-addressability) are computed predicates; the
  same event + same predictions always yield the same candidate set and the same scorecards.
- **Many-to-many:** an event isn't forced to a single "nearest" prediction — it scores every prediction
  it legitimately bears on, and a prediction accumulates evidence from every event that addresses it.
- **No LLM in the matching or scoring** (D-1): the judgment of "what this reading MEANS" is the LLM's at
  serve time; the judgment of "did the prediction's frozen test pass" is deterministic math here.

---

## §5 — From scorecard to learning (the attribution link)

The scorecard feeds the two downstream pillars, keeping the whole loop context-aware:

1. **Attribution (Pillar 2 / LL.9 / `mi_pariksha`).** For each scored prediction, credit/blame flows to
   its `driving_signals[]` *per dimension*: signals tied to timing logic get the timing score; signals
   tied to the outcome character get the domain score. A miss is traced to *which* signal on *which*
   dimension failed. This is only possible because the bundle kept the signal lineage.
2. **Calibration (Pillar 1 / `mi_pramana`).** Scorecards aggregate into reliability curves per signal-
   family, per domain, per confidence-tier — base-rate-adjusted (R-1), seasonality-null-checked (R-2),
   held-out-gated (V3). A family earns empirical weight only if its predictions score well *on the
   dimensions it claims to drive*.
3. **The two-key lock (V4).** A family's learned weight moves a real reading only when it has both passed
   the hard gate (good scorecards across enough held-out events) AND the resulting confidence is high.

> The chain is: frozen bundle → deterministic many-to-many match → multi-dimensional scorecard →
> per-dimension signal attribution → calibrated family weights → two-key-locked overlay. Context is
> preserved at every link; drop it anywhere and the learning goes shallow.

---

## §5A — Alternate manifestations (the karmic-theme problem) — NATIVE-RULED 2026-06-22

**The insight (native):** a classical signal does not promise one fixed outcome — it promises a *karmic
theme* that can legitimately express through several channels. A 4th-house/4th-lord affliction may
manifest as a property dispute, a mother's illness, a residential upheaval, domestic unrest, or a vehicle
loss. These are **alternate manifestations of the same underlying significance**, not different
predictions. A comparison that demands literal string-match would score "mother fell ill" as a MISS when
the chart's signal actually **fired correctly through a sibling channel** — a false negative that would
wrongly teach the instrument to distrust a signal that was right.

**The danger (stated honestly):** "alternate manifestation" is also the exact mechanism by which
astrology fools itself. If *anything in the domain counts*, every prediction hits something and the
instrument becomes unfalsifiable — destroying the honesty the whole design protects. So the model must
honor genuine alternates **without** opening the door to "everything counts."

**The ruling (three interlocking controls):**

1. **Domain-bounded matching (the outer boundary).** An event in the **same life-domain** as the
   prediction is eligible to count as a manifestation — we do not require pre-enumerating every specific
   channel. The domain is the *room* within which a manifestation can be recognized.

2. **Graded credit (the brake that keeps it honest).** Matches are NOT equal:
   - **Literal-outcome match** (the predicted channel happened) → **full credit**.
   - **Alternate-channel match** (a different but same-domain manifestation, meeting the falsifier) →
     **high-but-partial credit** — it confirms the signal fired, but the instrument was less specific
     about the channel. **The scorecard records WHICH channel actually fired.**
   - **Same-domain echo that does NOT meet the falsifier** → **graded partial (thematic resonance), never
     a clean `confirmed`**. This is the line that stops "everything counts": a vague domain echo is
     visibly a partial, not a hit.

3. **Hybrid, citation-gated set generation (deterministic spine + flagged additions).** The legitimate
   manifestation set is generated as:
   - **Classical spine (deterministic, L0):** looked up from the classical rule base
     (`bg_rules` / house-significations / karaka-significations) — e.g. 4th house → its canonical
     significations. Computed, cited, reproducible, **no LLM**. This is the authoritative core.
   - **LLM-suggested additions (flagged, citation-required):** an LLM may *propose* additional
     manifestations, but each is **clearly flagged as non-canonical and counts ONLY if it carries a
     classical citation**. Un-cited LLM suggestions are recorded for review but **cannot score**.
   - The whole set is **frozen at emission** (pre-registration) and **can never be widened after the
     event to rescue a miss** — that post-hoc widening is the cardinal sin this guards against.

**Why this is safe:** the domain is the room (control 1); grading means a loose match never scores like a
clean hit (control 2); and the citation-gate means any expansion beyond the deterministic classical core
must earn its place with a source (control 3). **The falsifier remains the judge** — domain-bounded
matching widens what *manifestation* can satisfy a prediction, but the pre-stated falsifier must still be
met for a full `confirmed`.

**The bonus (this deepens the model):** *which* alternate channel fires is itself rich learning. If a
4th-house signal repeatedly manifests as mother's-health rather than property across many events, the
instrument learns something true and specific about how THIS native's chart expresses — a per-channel
manifestation profile. The scorecard's recorded-channel field is what makes that learnable.

**Scorecard impact:** the §3 scorecard gains a **manifestation dimension** — `literal / alternate-cited /
thematic-resonance / none` — and the composite credit is graded accordingly. The `driving_signals[]`
attribution (§5) now also learns *channel-specificity* per signal, not just hit/miss.

---

## §6 — What this guarantees (tie to the five qualities)

- **Realistic** — base-rate-adjusted, seasonality-checked scoring; a hit on a common event isn't
  oversold.
- **Reliable** — deterministic matching + scoring; same inputs → same scorecards, every run.
- **High-confidence** — the falsifier is the judge (no rationalized hits); pre-registration gates
  admissibility; confidence is earned per-dimension.
- **Deterministic** — no LLM anywhere in the comparison; frozen bundles + computed predicates.
- **Current** — driven by the prediction-due sweep (C-3) as windows close and events arrive.

---

## §7 — Build implications (folds into the campaign)

- `mi_bhavisya` stores the **full frozen bundle** (incl. `manifestation_set[]`, `driving_signals[]`,
  `base_rate`, `emitted_at`), not just an outcome row. The `manifestation_set[]` is generated by the
  hybrid spine (§5A.3): classical-cited lookup from `bg_rules`/significations + citation-gated LLM
  additions, frozen at emission.
- `mi_pramana` implements the **deterministic matcher** (§4) + the **scorecard** (§3 + §5A manifestation
  dimension), retaining the dimension vector + the recorded-channel field, not collapsing to a single
  verdict.
- `mi_pariksha` implements **per-dimension attribution** (§5.1) including **per-channel manifestation
  profiling** (which channel a signal tends to fire through).
- Seal gate addition: **no post-hoc manifestation-set widening** — the set is frozen at emission and any
  attempt to expand it after an event is a halt-worthy integrity violation.
- Seal gates: scorecard reproducibility (RL-1); falsifier-as-judge enforced (no confirmed-without-
  falsifier); pre-registration admissibility enforced (HC-5); base-rate + null-model applied (R-1/R-2).
- The **Prediction Journal** (S-1) is where the native confirms events against staged predictions —
  feeding exactly the admissible, context-rich evidence this model consumes.

---

*End of L5_CALIBRATION_COMPARISON_MODEL v1.0. The comparison is context-aware: the full frozen prediction
bundle (outcome + window + confidence + magnitude + domain + driving signals + falsifier), scored on a
multi-dimensional scorecard (timing / magnitude / domain / falsifier → composite, falsifier as judge),
matched deterministically many-to-many. The scorecard is what makes precise per-signal attribution
possible — turning a scoreboard into a diagnostic — and it is deterministic end to end, with the LLM's
judgment reserved for serve-time synthesis, never the scoring.*
