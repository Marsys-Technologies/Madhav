---
artifact: PRASHNA_SUBSYSTEM_MASTER_PLAN_v1_0.md
canonical_id: PRASHNA_SUBSYSTEM_MASTER_PLAN
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10 — maximal scope; chart-TYPE + horary rule layer
authored_for: the Prashna/Horary subsystem build (subsystem #7 of 7, Wave 4)
purpose: >
  Build the Prashna (Horary) subsystem to full classical depth: a NEW CHART-TYPE (the question-moment chart)
  that reuses the ENTIRE existing pipeline + all 6 other subsystems, plus a maximal Prashna-specific rule
  layer (all Prashna-Lagna methods + the full horary judgment ruleset + significator derivation +
  fructification timing). A complete second MODE of the instrument (event/question astrology). Pattern-embedded.
read_in_combination_with:
  - SUBSYSTEM_PROGRAM_ROADMAP_v1_0.md (§7 the chart-type reframe; §0.5 + hard gate)
  - the Tajak/A7 (Ithasala/Eesarpha already computed in ga_dashas/A8 aspect_tajik) + ALL other subsystems
hard_gate: Prashna RULES + the question-chart computations are deterministic+cited; the "answer" synthesis is the ONE place pre-answering is appropriate (a prashna chart exists to answer ONE question) but the JUDGMENT inputs are computed+cited, the narration is serve-time.
namespace: prashna outputs live in their OWN namespace, NEVER mixed with the natal chart's facts (a prashna chart is time-bound to the question-moment, not natal).
---

# Prashna / Horary Subsystem — Master Plan (maximal) v1.0

## §0 — Reframe: a chart-TYPE that reuses everything

Prashna = horary = the astrology of the MOMENT A QUESTION IS ASKED. It is NOT a new L0–L5 stack — it is a
**new chart-TYPE** (cast a chart for the question-instant) that then runs through the ENTIRE existing pipeline
(positions, vargas, dashas, nakshatra, yoga, dignity, transit — every subsystem) PLUS a thin-but-maximal
Prashna-specific rule layer (the horary judgment methods). The value is REUSE; the build is mostly an
entry-point + the horary rules. A prashna chart IS a chart — so 90% of the computation already exists.

## §1 — The architectural work: a question-chart entry point
The real plumbing — a SECOND chart-creation path:
- **`prashna_charts`** table (alongside `charts`) — each row = a question: the question text, the EXACT
  question-instant (when asked), the querent's location (lat/lon), the prashna-method used, optional the
  querent's natal chart_id (for cross-reference).
- Casting a prashna chart REUSES the entire chart-build pipeline (the orchestrator builds its positions,
  vargas, dashas, nakshatra, condition, etc. exactly as for a natal chart — a prashna chart is just a chart
  with a question attached).
- **Namespace isolation:** prashna outputs NEVER mix with natal facts. A prashna chart's data is time-bound
  to its question-moment.

## §2 — L0 `bg_prashna_rules` (MAXIMAL horary rule reference, cited)
Every classical horary method + rule, static + cited:
- **Prashna-Lagna derivation methods (ALL):** Tajik (the moment-Lagna), **KP number (1–249 → cuspal
  sub-lord)**, Brihat Prashna / Prashna Marga methods, **Aarudha-based** (the querent's seat/number),
  **Swara/breath-based**, **Chandra-Lagna prashna** (Moon as the significator of the question). Each method's
  exact derivation rule.
- **The horary JUDGMENT ruleset (the full Tajik + classical set):** Ithasala (applying aspect = yes, it will
  happen), Eesarpha/Isarpha (separating = no/past), Nakta, Yamaya, Manaau, Kambula, Gairi-kambula, Dutthottha,
  Rudda (prevention), Khallasara, Duhphali-kuttha, Manau — the complete Tajik prashna-yoga set applied to the
  question-chart. (Reuses the A8 aspect_tajik computation, applied to the prashna chart.)
- **Significator derivation:** the rules for QUERENT (Lagna + its lord + Moon) vs QUESITED (the house of the
  matter + its lord) per question-type — the house-significator map for every question class (marriage=7th,
  career=10th, litigation=6th, lost-object=2nd/4th, health=1st/6th/8th, etc.).
- **Fructification timing rules:** when the matter resolves (the degree-gap in the Ithasala → time-units;
  the dasha/transit of the significators).
- **Special prashna techniques:** Nashta-jataka (lost-horoscope reconstruction), Tithi/Nakshatra/Yoga-of-
  the-question prashna, the Arudha-of-the-query, omen (nimitta) integration where deterministic.
All cited (Prashna Marga, Tajik Neelakanthi, Krishnamurti KP prashna, Shatpanchasika → into bg_texts).

## §3 — L1 `ga_prashna` (per prashna-chart, computed)
For each prashna chart, per ayanamsha:
- **Prashna-Lagna** by each method (store all methods' Lagnas; the primary per the chosen method).
- **Querent + Quesited significators** for the question (which houses/planets/Moon represent each side).
- **The Tajik yoga between them** — Ithasala/Eesarpha/etc. (will it happen? — computed via the existing
  aspect_tajik logic on the prashna chart) + the strength/applying-degree.
- **Fructification window** (when — from the degree-gap + the significators' dasha/transit, reuses the
  transit service + ga_dashas).
- **Full reuse:** the prashna chart's yogas (Yoga subsystem), planetary conditions (Dignity), nakshatra
  picture (Nakshatra), transit overlay (Transit service) — ALL computed on the prashna chart, in the prashna
  namespace.
- Two-pass; cited.

## §4 — L2 — the ONE place pre-answering is appropriate
A prashna chart exists to answer ONE question — so a focused "answer synthesis" IS appropriate here (unlike
the natal chart's open-ended retrieval). The deterministic JUDGMENT inputs (Ithasala=yes/no, fructification=
when, significator strength) are computed+cited; the LLM narrates the answer from them. Store the judgment
ingredients; the narration is serve-time. (This is consistent with the L2 philosophy — store ingredients,
LLM synthesizes — just focused on one question.)

## §5 — L3/L4/L5
L3: the fructification timing (reuses the transit service). L4: prashna-indicated remedies. L5: did the
prashna answers verify (a prashna chart has a CLEAN test — the question had a real outcome — making prashna
arguably the BEST-calibrated part of the whole instrument for the research layer; held-out).

## §6 — Standards + the hard gate + namespace
Computed-and-cited (the horary rules + the question-chart judgment computed+cited; the answer-narration
serve-time); **prashna namespace ISOLATED from natal facts**; reuse-don't-recompute every other subsystem on
the prashna chart; orchestrator-native (a prashna chart builds via the orchestrator like any chart, +
ga_prashna as its own writer); L0 ON-CONFLICT / L1 delete-then-insert; two-pass; no-JH-parity; no tier;
surgical migrations.

## §7 — Decisions upfront
1. Primary Prashna-Lagna method (Tajik vs KP-249 vs Chandra — recommend KP-249 primary, others stored).
2. The question→house-significator map (lock the classical map per question class). 3. prashna_charts entry
UX (how a question + moment + location is captured). 4. Fructification time-unit conversion (degree-gap →
time — the classical rule). 5. Source editions (Prashna Marga / Tajik / KP prashna → bg_texts).

---

*End. Prashna maximal: a new chart-TYPE (the question-moment chart) reusing the entire pipeline + all 6 other
subsystems, + a complete horary rule layer (all Prashna-Lagna methods, the full Tajik judgment ruleset,
significators, fructification). A second MODE of the instrument; the cleanest test case for the research
layer (questions have real outcomes); namespace-isolated from natal facts.*
