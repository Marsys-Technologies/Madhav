---
artifact: KALA_SIX_VIEWS_DESIGN (The Temporal Views — Deep Design, Round 2)
canonical_id: KALA_SIX_VIEWS_v2_0
version: 2.0
status: DESIGN — v1.0 RATIFIED by the native (all build tiers A/B/C approved); this round
  deepens it per the native's six directives before the implementation plan is cut
created: 2026-07-27
supersedes: KALA_SIX_VIEWS_DESIGN_v1_0.md (v1.0 remains valid; this EXTENDS — nothing retracted)
native_directives_addressed:
  1. Reconciliation beyond schools — daśā systems, ayanāṁśas, Sūkṣma depth, disagreeing
     surfaces; principled, astro-logical; astronomy/physics when in doubt; statistics for clarity
  2. Salience — rebuilt with explicit factor logic (the native's stated suspicion is confirmed
     by measurement: CR-65 93% noise, CR-81 inert prior, CR-82 tier-ceiling, MC-030 rare-event
     inversion)
  3. Law 3 amended — unpromised events happen; capacity for daiva; the intervention asset
  4. Presentation capability for Pariprashna (internal chat) + MCP channel
  5. Per-view deepening across astrology, astronomy, physics, statistics + the register of
     concepts CONSCIOUSLY EXCLUDED, so coverage is provably exhaustive
  6. Architecture ruling — replace assets vs. a better way
---

# The Six Views, Round 2 — Reconciliation, Salience, Grace, and the Master Algorithm

## §A — The full reconciliation stack: five axes of disagreement, one uncertainty budget

v1.0's five laws reconciled *schools*. The native is right that disagreement lives on more axes.
The complete set, each with its own principled resolution — and one unifying instrument at the
end (the uncertainty budget) that makes them composable.

### A.1 Ayanāṁśa reconciliation — treat it as physics, because it is
The ayanāṁśa is an empirical estimate of a physical quantity: accumulated precession from a
fiducial epoch. Different ayanāṁśas are **systematic offsets, not opinions** — so the resolution
is measurement methodology, not debate:

- **Pinned operational default** (Lahiri, already the case) for all serving; others are
  **sensitivity analyses**, never parallel truths.
- **Boundary-distance robustness on every derived claim.** Every position-derived fact carries
  its distance to the nearest boundary that would change it (nakṣatra/pada edge, varga edge,
  sign edge). A claim that survives all pinned ayanāṁśas = `ayanamsha_robust`; one that flips =
  served with the flip-point ("Moon is Aquarius 27°04′ — P.Bhadrapada under all five ayanāṁśas;
  its D60 position flips at +14′"). The discovery engine's cross-ayanāṁśa duplication becomes a
  **robustness score** — the same computation, inverted from noise into signal.
- **The Sūkṣma consequence (this is the critical one):** Vimśottarī balance-at-birth depends on
  the Moon's fractional nakṣatra arc → ayanāṁśa shift + birth-time uncertainty propagate into
  daśā-boundary shifts. At MD level the induced error is weeks against periods of years —
  negligible. At Sūkṣma level the error **exceeds the period length**. Therefore: **error
  propagation is mandatory below PD.** Every Sūkṣma boundary serves as an interval, not an
  instant, with the dominant uncertainty source named (birth-time vs ayanāṁśa). The 185-candidate
  rectification posterior (unresolved, WL-6) plugs in directly: until rectification closes,
  boundary intervals are honest; after it closes, they tighten. **No claim is ever served at a
  precision the input uncertainty cannot support** — this single rule is what makes Sūkṣma-depth
  serving defensible at all, and no astrology software on earth does it.

### A.2 Daśā-system reconciliation — jurisdiction, then competence, then concurrence
Law 1 (applicability) gains a second gate: **competence class**. Systems answer different
questions and should only be compared within a class:
- Vimśottarī — the general fruition clock (agents: which graha delivers). Universal spine.
- Jaimini Chara — arenas (which sign/house domain comes into focus). Complementary, not rival:
  Vimśottarī names the actor, Chara names the stage. **Compose, never reconcile.**
- Yogini — flavor/quality overlay; Kalachakra — health/life-force jurisdiction; Mudda — intra-
  annual (Tājika's own clock, joined to the varsha plane); Naisargika — the life-stage underlay
  (childhood Moon → old-age Saturn), a slow context band, not a predictor.
- Conditional daśās — apply only where their entry condition holds (evaluated per chart, served
  as excluded-with-reason otherwise).
True disagreement (two same-class, both-applicable systems, opposite verdicts) is served as
dissent per Law 2, tie-broken by: classical seniority for that question class → applicability
strength → (eventually) per-chart L5 calibration. Never averaged.

### A.3 Internal-surface reconciliation — one authority per fact class
When our own artifacts disagree (the measured CR-55/MC-025 class: digest vs remedy on
weakest-graha), the resolution is structural: every fact class has ONE authority row (§N.5: L1),
every derived surface must cite it (`authority_basis` on every field row), and a CI check
diffs stored-vs-derived on the authority set (the GA.1 kill rule, made permanent). Disagreement
between surfaces becomes a build error, not a consumer's puzzle.

### A.4 Statistics — three honest instruments, no p-hacking theatre
1. **The synthetic reference cohort (NEW BUILD, foundational).** Rarity and base rates are
   currently uncomputable honestly (n=4 charts). Build a reference population: ~10⁴–10⁵ synthetic
   charts sampled uniformly over birth-moments across a century × a location distribution — the
   sampling measure is given by astronomy for free. Every configuration then has an honest base
   rate: "Śaśa + exalted 11th-lord in 7th + Moon-11th occurs in 0.4% of the cohort." This single
   asset powers PRIORITIZE's rarity axis, EXPLAIN's "how unusual," the discovery engine's
   informativeness, and STORY's "what is genuinely distinctive about your chart."
2. **Null-calibrated notability (NEW, the anti-pareidolia instrument).** With ~12k concepts per
   domain, impressive-looking convergences arise by chance. Fix: per-chart **circular-shift
   null** — recompute convergence scores under random time-shifts of the transit stream against
   the fixed natal structure; a window is "notable" only if its score exceeds the chart's own
   null quantile (matched-filter detection with background estimation — the LIGO discipline
   applied to Jyotiṣa). Serves as `null_exceedance` on every window. This is the statistical
   spine that makes "convergence" mean something.
3. **Hierarchical shrinkage on outcomes** (already designed, ARC §7) — when L5 accrues events,
   per-chart × per-event-class × per-tradition weights shrink toward global priors, honest at
   small n. Cited, not redesigned.

### A.5 Physics/astronomy assists — the kinematic layer earns its keep
The division of labor, stated once: **astronomy answers where/when exactly; astrology answers
what it means; statistics answers how unusual and how reliable; physics-shaped reasoning answers
how to weight kinematic features.** Concrete assists adopted:
- **Dwell-time weighting**: a transit's influence weight ∝ time spent in orb (bounded). This is
  simultaneously the physical formalization of the classical rule "stationary planets act with
  full force" — stations are simply maximal dwell. One formula replaces a special case.
- **True lunar velocity** (perigee/apogee variation, ±20%) for tārā/chandra window durations —
  never mean motion.
- **Eclipse geometry**: magnitude, gamma, and local visibility computed, because the classical
  weighting (visible > invisible, total > partial) maps directly onto them.
- **Uncertainty propagation** (A.1) — the deepest physics contribution is epistemic honesty.

### A.6 The uncertainty budget — the unifying instrument
Every served temporal claim carries a **robustness vector**:
`{ayanamsha_robust, birth_time_robust, system_concurrent, null_exceeding, authority_clean}`.
The claim's confidence tier (Law 5) = **the minimum across dimensions** (weakest link), with the
weakest dimension named. This composes all five axes into one honest, explainable statement —
and it is what an acharya cannot do: hold five uncertainty sources simultaneously and report the
binding one.

## §B — Salience, rebuilt from first principles

The native's suspicion is measurement-confirmed. Root cause of every measured salience defect:
**salience is a single opaque scalar composed from unexamined factors.** Rebuild as a served,
decomposed vector — five factors, each with its logic, plus a selection principle:

| Factor | Definition | What it fixes |
|---|---|---|
| **Informativeness** | −log P(observation \| reference cohort) — surprise under A.4's cohort measure | "dignity: neutral" has ≈0 surprise and can never again outrank a fired puṣkara (MC-030 dies mathematically, not by special-case boost) |
| **Consequence** | Magnitude of domain impact if real — from the event grammar (domains touched × severity band × classical significance class) | Descriptor rows vs event-bearing rows separated by nature, fixing the CR-81 inert prior with a *real* prior |
| **Relevance** | Match to the question's scope (domain/entity/horizon), as a score not a binary filter | MC-022's character-rows-in-wealth-queries; leakage is visible and priced, not silently included |
| **Reliability** | The §A.6 robustness vector's tier | Fragile claims sink; concurrent claims rise; the consumer sees why |
| **Actionability** | Existence of an ELECT lever or intervention join (§C) | A window one can act on outranks one that can only be awaited — triage aligned with human use |

**Selection principle — submodular top-K, not top-K-by-score.** The served set maximizes
*coverage of independent information*: each additional row is scored by its marginal
information given rows already chosen (family-membership discounting). This is the
principled generalization of `window_families` dedup, and it is the mathematical fix for
"14 of 15 rows are the same signal type" (CR-65): the second row of a family earns almost
nothing, so the 15-row budget spends itself across 15 *different* things.
The composition into an ordering scalar is versioned and **served with the vector** — salience
becomes auditable, which is the property the native asked for.

## §C — Law 3 amended: the graded gate, the Adṛṣṭa channel, and UPĀYA-SETU

### C.1 The amendment
Law 3 stands as the *ordering* of evidence, but the gate becomes **graded, with an explicit
residual**. Promise strength is a continuous prior, not a binary permit. Windows over weak or
absent promise are **served, not suppressed**, labeled honestly: *"temporal pressure without
strong natal promise — events of this class are not indicated by the birth chart; if pursued,
this is the window where the attempt is least opposed."* Classical warrant is native to the
tradition: BPHS's own remedial chapters, the entire Praśna literature (the asking-moment carries
fresh information precisely because the natal chart is not the whole story), and the doctrine of
daiva. The residual channel is named **Adṛṣṭa** ("the unseen") and is formally identical to the
model-humility term the doctrine waves already designed (DR-17's `unmodeled_variance`) — theology
and statistics agreeing on the same reserved probability mass is a feature, not a coincidence.

### C.2 UPĀYA-SETU — the intervention-leverage engine (the standout asset)
**Question it answers:** *"This outcome is unlikely for me. What would raise its likelihood, and
when?"* No computed instrument anywhere does this honestly. Design:

1. **Diagnose the failing link** in the PACT chain for the desired event class: promise absent
   at L2? · promised but no daśā eligibility inside the horizon? · eligible but suppressed
   (vighna)? · triggered but never elected/acted on? Each failure mode has a different remedy
   class — the diagnosis IS the product.
2. **Map interventions to links:**
   - *Promise-side:* remedial strengthening of the weak significator (the existing remedy engine,
     targeted by the diagnosis rather than generic weakest-graha) + **alternate-routing search**:
     path-search over the chart's own promise graph (dispositor chains, argala, yoga membership,
     karaka webs) for a *different mechanism* that reaches a similar outcome — "your 2nd-house
     channel is weak, but an 11th-lord channel exists via X" — computed from machinery we already
     have (the CGM/mechanism layer finally load-bearing).
   - *Eligibility-side:* the least-opposed windows (ELECT integration over the weak chain —
     argmax of the weak promise's λ, honestly labeled "best available, still weak").
   - *Suppression-side:* vighna-specific counters (classical obstruction remedies, timing around
     the obstruction's own window).
   - *Decision-side:* a Praśna cast at the moment of intent (the engine exists) as the final
     fresh-information gate.
3. **Honesty contract:** every intervention carries an efficacy tier — `classically_attested
   (citation)` / `traditional` / `speculative_extension` — and the framing is receptivity, never
   guarantee: *"upāya prepares the vessel; it does not command the rain."* Each adopted
   intervention **auto-files a falsifiable prospective entry** (window X becomes the test), so
   UPĀYA-SETU is self-calibrating from birth — over time the system learns, per chart, whether
   intervention-accompanied windows outperform their priors. **That study design does not exist
   anywhere in this field.**
4. **Placement:** UPĀYA-SETU is a seventh *capability* but not a seventh view — it serves
   THROUGH the views (AHEAD windows carry `intervention_leverage` pointers; ELECT accepts
   `for_intervention`; EXPLAIN drills the diagnosis). One new tool: `kala_upaya_get`
   (diagnosis + ledger), keeping the six-name surface clean while adding the capability.

## §D — The presentation contract (Pariprashna + MCP)

Temporal truth is intrinsically visual — bands, phases, horizons — and the consuming LLM is only
one of two audiences. The engine therefore emits **one payload, three renderings**:

1. **`reading`** — composed prose, hardFloored (the LLM's voice; exists per v1.0).
2. **`compact`** — table/card rows for chat surfaces (Pariprashna inline).
3. **`presentation`** — a renderer-agnostic declarative **`kala_timeline_spec v1`** (opt-in flag,
   so MCP token budgets don't pay for it by default): tracks (clocks/domains), intervals
   ({start, end, peak, valence, tier, shape, label, id}), points (punctuation events), bands
   (sandhi/eclipse/sāde-satī phases), a now-marker, and drill ids that map 1:1 to EXPLAIN.
Per-view canonical renderings: NOW = layered state-stack ("weather dial") · AHEAD = horizon
gantt · ELECT = slate cards with why/why-not ledgers · STORY = chapter river with LEL pins ·
PRIORITIZE = ranked cards showing the five salience axes · EXPLAIN = chain graph.
Pariprashna renders the spec as an interactive widget; MCP clients that can't render simply
ignore the block; the id-mapping means **a user can click any bar and the chat can answer "why?"
by calling `kala_explain_get(id)`** — presentation and provenance become one loop. This contract
is part of the engine (computed once, serialization-cheap), not a UI afterthought.

## §E — Per-view deepening (beyond v1.0) + what each addition buys

**NOW —** add: **transit condition of the running daśā-lords** (the period lord currently
exalted/retrograde/combust/in-war *by transit* colors the whole period — classical, cheap, and
currently unserved anywhere); **Chandrāṣṭama** flag (Moon transiting 8th from natal Moon — the
most-used practical daily rule in living tradition); current **horā lord + day-part**;
**janma-tithi/vara/nakṣatra resonance** ("today is your janma-nakṣatra day"); transit contacts
to natal **sensitive-degree firings** (64th navāṁśa, 22nd drekkāṇa, mṛtyu-bhāga — natal points
exist; the transit-contact join is part of the sky calendar).

**AHEAD —** add: **forward transit-condition of upcoming daśā-lords** (the Ketu MD beginning
2027 reads differently if Ketu's dispositor is then exalted in transit); **Mudda daśā** inside
each varsha (the Tājika micro-clock, already computed as one of the 8 systems, never joined);
**Naisargika life-stage band** as the slowest underlay; **period-echo mining** — "the last time
a Saturn sub-period ran (2001–2004), the log shows X" — LEL-verified resonance of same-lord
sub-periods, served as *narrative hypothesis with falsifier*, never as law (statistically tiny
n, honestly labeled — but it is exactly how a great jyotiṣī actually reasons).

**ELECT —** add: **Gulika/Māndi kālam** day-part avoidance (computed daily, unjoined);
**Diśā-śūla** directional rules for travel undertakings (computed! `panchanga_disha_shul` —
never served); **remedial-initiation** as a first-class activity type (UPĀYA-SETU's "when to
begin the upāya" — classically mandatory and a natural product loop); Sarvatobhadra day-vedha
once the real grid lands (R-19, now forced by Tier A).

**STORY —** add: **Naisargika stage overlay** (chapters read differently in the Moon-childhood
vs Saturn-elder stage — same daśā, different register); **echo-chapter annotations** (period-echo
above, as biography: "your third Saturn sub-cycle; the first built, the second tested");
**Chara-daśā arena track** formally as the second voice (v1.0 named it; this confirms it as a
track in the timeline spec).

**PRIORITIZE —** the §B rebuild IS the deepening. One addition: a **`surprise_of_absence`**
row type — when something classically expected for this chart is NOT firing ("Śaśa is running
its own daśā yet no career window scores — that silence is itself notable"), the absence enters
triage. Absence-as-signal is the mark of a master reader and no software serves it.

**EXPLAIN —** add: **contrastive explanation** ("why this window and not last month" — computed
from field diffs, answers the question users actually ask); **pedagogy expansion** (each chain
link can expand into its classical source passage via the ingested corpus — the instrument
becomes a teacher); the **weakest-link named** (v1.0) now uses §A.6's budget formally.

## §F — The consciously-excluded register (so exhaustiveness is provable)

Considered fully, excluded deliberately, each with its reason and re-entry condition:

| Concept | Why excluded now | Re-entry condition |
|---|---|---|
| **Pañcapakṣī** (Tamil bird-rhythm intraday) | Regional school; birth-pakṣī tables absent from corpus; overlaps ELECT's intraday layer | Corpus ingestion of pakṣī tables + native interest |
| **Śiva-svarodaya / breath timing** | No data substrate possible (requires live somatic input) | Out of instrument scope permanently |
| **Aṣṭamaṅgala / Deva-praśna** | Temple divination ritual, not a computable service | Out of scope |
| **Western progressions / solar arcs / transiting outers (Uranus/Neptune/Pluto)** | Different zodiacal paradigm; mixing would corrupt corpus coherence (Law 4's tradition tags exist precisely to prevent silent paradigm blending) | Only ever as a separately-tagged tradition, native-commissioned |
| **Nadi-style varga-transit triggers** (transits read directly in divisional charts) | Classically contested; our corpus support is thin; risk of false precision at varga granularity below the A.1 uncertainty budget | If corpus support + an ayanāṁśa-robustness proof at varga scale |
| **Lal Kitab varṣphal cycles** | School present in corpus only as isolated points; no coherent rule base | Corpus expansion |
| **Numerology/name cycles** | Out of śāstric scope for this instrument | — |
| **Pre-natal eclipse/syzygy sensitive points** | Classical warrant in OUR ingested corpus is thin (one-line mentions); the sky-calendar makes them cheap later | One corpus citation pass; then a 2-line add to the sky calendar |
| **Heliocentric positions** | No jyotiṣa warrant | — |
| **Aṣṭakavarga kakṣyā-lord sub-timing beyond current** | Already served at kakṣyā level; deeper subdivision exceeds the uncertainty budget | GOCHARA-2.0 sub-day substrate + demonstrated need |
| **Praśna-at-every-query** (auto-cast a horary chart for each user question) | POWERFUL but deliberately reserved: folded into the Adṛṣṭa/UPĀYA-SETU channel as a *decision-time* gate rather than ambient (ambient use would double every reading's surface area and dilute the natal instrument's identity) | Product decision after UPĀYA-SETU ships |

Everything else surveyed in the corpus (all 8 daśā systems, all pañcāṅga limbs, moorti, vedha,
tārā 9-fold with vadha classes, AV including sodhita, sāde-satī 15-category family, Tājika
including Mudda, Jaimini chara/karakas/arudhas, KP as designed slot, sensitive degrees, kota,
sudarśana, tithi-praveśa) is **IN**, per v1.0 + §E.

## §G — The master algorithm (the ten-stage pipeline, complete)

```
STAGE 0  KINEMATICS      splines over ephemeris; events (ingress/station/eclipse/return);
                         dwell-time weights; true velocities; local visibility
STAGE 1  SYMBOLIZATION   kinematics → classical primitives: contacts (dual-reference), moorti
                         at ingress, vedha/latta, AV+kakṣyā gates, pañcāṅga limbs, sandhi bands
STAGE 2  PROMISE GRAPH   L2 judgment digested per event-class: promise strength (continuous),
                         significator sets, ALTERNATE ROUTINGS (path-search over dispositor/
                         argala/yoga graph), suppressors — the chart's delivery network
STAGE 3  CLOCKS          multi-system daśā with applicability + competence gates; boundaries
                         as intervals below PD (uncertainty propagation per §A.1); varsha +
                         mudda annual plane; naisargika stage band
STAGE 4  FIELD           λ(chart, domain, event_class, t) = Σ currents×(promise prior)
                         ×(AV gate)×(moorti/vedha modifiers) − Σ suppression, integrated
                         analytically between events; every term carries provenance edges
STAGE 5  CALIBRATED      circular-shift null per chart → null_exceedance per window;
         NOTABILITY      robustness vector per claim (§A.6); Adṛṣṭa residual reserved
STAGE 6  SALIENCE        five-factor vector (§B); submodular top-K selection; absence-of-
                         expected as first-class rows
STAGE 7  VIEWS           NOW/AHEAD/ELECT/STORY/PRIORITIZE/EXPLAIN projections + UPĀYA-SETU
                         diagnosis; window ids stable; family-collapse everywhere
STAGE 8  PRESENTATION    reading (prose) + compact (chat) + kala_timeline_spec (UI), one
                         payload; EXPLAIN ids threaded through all three
STAGE 9  LEARNING LOOP   every AHEAD window + every adopted upāya auto-files a falsifiable
                         prospective entry; L5 outcomes → hierarchical shrinkage → per-chart
                         per-tradition weights (Law 4) → tiers migrate structural_prior →
                         concurrent → calibrated
```
Determinism contract: stages 0–8 are pure functions of (chart, corpus, pinned config) — same
inputs, identical field, hash-verified. Stage 9 is the only state that grows.

## §H — Architecture ruling: strangler-fig, not replacement-in-place

The native asked whether to replace current assets with view-shaped ones. **Recommendation: no
in-place replacement — strangler-fig migration**, because the measured failure mode of this
codebase is *two surfaces answering one question while documents drift* (§0 of the ledger), and
a half-migrated hybrid is that failure mode at maximum intensity:

1. **Facades first** (v1.0 §10 stands): the six tools ship over EXISTING substrate. The consuming
   LLM's world becomes six names immediately; imperfection hides behind a stable contract.
2. **The field is built BESIDE, not inside**: new `kala_field` tables per §G, populated by the
   consolidated pipeline, while sangam/yojaka/kalasutra/taranga keep running untouched.
3. **Per-view cutover with equivalence verification** — the GOCHARA-2.0 §3 discipline applied to
   ourselves: the old surface is the ground-truth corpus; every divergence is classified
   (old-artifact / new-capability / new-bug) with evidence; **no divergence ships unclassified.**
4. **Retirement only at zero consumers**, proven by the catalog census, one writer at a time;
   the two clock substrates (daśā tables, sweep corpus) are keepers — replacement applies to the
   middle layer (4 writers → field pipeline) and the serving layer (14 tools → 6 + `kala_upaya_get`
   + one deprecation cycle of aliases).
5. **The sealed harness + the sweep corpus are the regression floor throughout** — untouched,
   re-run at every cutover.
This is slower than big-bang by weeks and safer by a category. Given this program's history —
where every incident came from surfaces disagreeing about what is true — the choice makes itself.

## §I — Build-registry deltas from this round (append to v1.0 §7; all tiers pre-approved)

22. [N] **Synthetic reference cohort** (~10⁴⁺ charts, birth-moment measure) — powers §A.4/§B/§E. **Tier A** (salience depends on it).
23. [N] **Circular-shift null calibration** in the field pipeline — §A.4.2. **Tier A**.
24. [N] **Uncertainty-budget propagation** (birth-time × ayanāṁśa → boundary intervals below PD; robustness vector on every claim) — §A.1/§A.6. **Tier A**.
25. [N] **Salience vector rebuild + submodular selection** (replaces the CR-65/81/82 complex at the root) — §B. **Tier A**.
26. [N] **UPĀYA-SETU** (`kala_upaya_get`): PACT-link diagnosis, alternate-routing search, intervention ledger with efficacy tiers, auto-filed falsifiers — §C. **Tier B, flagship**.
27. [N] **`kala_timeline_spec v1`** presentation contract + Pariprashna widget contract — §D. **Tier A** (cheap, multiplies every view's value).
28. [J] **Daśā-lord transit-condition** (current + forward) — §E. **Tier A**.
29. [J] **Chandrāṣṭama + horā + janma-resonance day flags** — §E. **Tier B** (trivial).
30. [J] **Mudda daśā joined to the varsha plane** — §E. **Tier B**.
31. [N] **Period-echo mining** (LEL-verified same-lord sub-period resonance, hypothesis-framed) — §E. **Tier B**.
32. [J] **Diśā-śūla + Gulika-kālam election joins** — §E. **Tier B** (computed, unserved).
33. [N] **Absence-of-expected detector** (PRIORITIZE row type) — §E. **Tier B**.
34. [N] **Contrastive EXPLAIN** (field diffs) — §E. **Tier B**.
35. [—] **Planner wiring verified LIVE**: per the native's directive, every view primitive +
    intent route is verified by real MARSYS-JIS MCP calls from the implementing Claude Code
    session at wire-up time (call → response shape → floor presence), not by unit tests alone.
    **Gate condition on the implementation campaign.**

---
*Round-2 in one line: disagreement is resolved by jurisdiction, physics, and honest uncertainty
rather than averages; salience becomes five auditable reasons instead of one opaque number;
grace gets a channel and intervention gets an engine; every view learns to draw itself; and the
migration strangles the old surfaces instead of gambling the product on a cutover.*
