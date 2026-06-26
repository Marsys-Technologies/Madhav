---
artifact: L3_KALA_COMPLETENESS_AUDIT_v1_0.md
canonical_id: L3_KALA_COMPLETENESS_AUDIT
version: 1.0
status: AUDIT COMPLETE — answers "is Kāla fully leveraging upstream / why are counts modest"
audited_by: Cowork 2026-06-21 (2 parallel subagents + direct line-level verification)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
scope: >
  Code-logic completeness review of all 12 L3 Kāla assets (counts ignored as stale). Two
  questions: (1) does anything artificially CAP output below what upstream supports? (2) is each
  writer LEVERAGING the full breadth of its declared upstream? Both answered YES there are gaps.
verdict: >
  The modest Kāla counts are NOT architectural sparsity. They are the product of (A) a cascade of
  hardcoded output CAPS and (B) large UNCONSUMED upstream — ~40% of the ratified convergence
  weight is pinned to 0.0, an entire signal class is filtered out, and a key service is wired to
  None. Kāla is currently running on roughly half its intended evidence and a fraction of its
  intended breadth. This is fixable; the fixes are real scope decisions, not one-liners.
---

# L3 KĀLA — COMPLETENESS AUDIT

## TL;DR (the answer to your question)

**You were right — the modest counts are a bug-class, not the nature of the layer.** There are TWO
compounding problems, both verified at the line level:

1. **A cascade of hardcoded CAPS** that truncate output at every stage (the master one throttles
   66,738 signals → 60 before any temporal search even begins).
2. **Large unconsumed upstream** — ~40% of the ratified convergence weight runs at `0.0`, the
   whole SUBSYSTEM signal class is filtered out of convergence, and the panchanga/muhūrta service
   is passed as `None`. So even the windows that ARE produced rest on ~half their intended evidence.

The deterministic spine that IS wired (dāśā + transit + ashtakavarga/vedha/tājika) is real and
correct. The gap is breadth and evidence-density, not correctness of what's there.

---

## PART A — The cap cascade (artificial output limits)

Every cap verified at file:line. ka_yojaka is the only writer at full breadth; everything
downstream truncates.

| Stage | Cap | Location | Effect |
|---|---|---|---|
| ka_yojaka | **none** ✅ | — | Full: 1 predicate per MSR signal (~66,738). The one complete writer. |
| ka_kalasutra | none on count, but **hollow rows** | — | Full row count, BUT activation dates are NULL for every signal ka_sangam skipped (inherits the 60-cap). |
| **ka_sangam (MASTER CHOKE)** | **`_MAX_PREDICATES = 60`** | ka_sangam.py:45,89-91 | Of 66,738 predicates, only **top-60 by eligibility** ever enter the convergence engine. 99.9% get zero windows. |
| ka_sangam | `_LIFETIME_MAX_PREDICATES = 24` | ka_sangam.py:54,152 | Lifetime tier runs for only 24 signals. |
| ka_sangam | `_HORIZON_YEARS = 5` (near tier) | ka_sangam.py:44,189 | "Near" convergence searches only today→+5y, never the lifespan. |
| ka_sangam | `_LIFETIME_MAX_ROWS = 13_000` | ka_sangam.py:55 | Hard row ceiling (sized FOR the 60/24 budget). |
| ka_vighnakara | **`LIMIT 200`** | ka_vighnakara.py:24 | Only top-200 convergence windows checked for obstruction. |
| ka_kala_darshana | **`LIMIT 300`** | ka_kala_darshana.py:25 | Display catalog capped at top-300 windows. |
| ka_jivana_parva | **`level_n = 1` (MD only)** | ka_jivana_parva.py:24-26 | One chapter per mahādaśā → ~6-9 rows. AD/PD levels (chart_dashas level-4) unused. |
| ka_bhavishya_lekha | **`LIMIT 50` + next-3-years only** | ka_bhavishya_lekha.py:31-33 | The literal answer to "why exactly 50." Also drops `obstructed_severe`. |

**Why the caps exist (important):** ka_sangam runs a HEAVY per-predicate ephemeris sweep (Mode A +
Mode B). The comments show the 60/24/13k budget was deliberately sized to keep runtime under the
15-min orphan watchdog. So the master cap is a **conscious cost/runtime tradeoff set
conservatively** — not an accidental bug. Lifting it is a real performance decision (more
predicates × full horizon = much longer builds), which is why this needs your sign-off, not a
silent patch.

---

## PART B — Unconsumed upstream (the evidence/breadth gap)

This is the more consequential half. Declared-but-unread upstream + stubbed scoring inputs.

### B1. ~40% of the convergence weight runs at 0.0 (verified engine.py:724-730, 867-873)
The I-7 ratified weight TABLE declares 12 currents (engine.py:39-52). At RUNTIME, 5 are hardcoded
`0.0` in BOTH Mode A and Mode B, with "wire later" comments:

| Current | Ratified weight | Runtime | Why dead |
|---|---|---|---|
| cross_dasha_agreement | 0.12 | **0.0** | "wire later from U1 at ph_nimitta level" |
| benefic_dristi | 0.10 | **0.0** | no aspect/dṛṣṭi read |
| panchanga_quality | 0.07 | **0.0** | muhūrta service = None |
| tara_bala | 0.06 | **0.0** | muhūrta service = None |
| nakshatra_subsystem | 0.05 | **0.0** | no ga_nakshatra/bg_nakshatra read |

That's **0.40 of the supporting weight permanently zero** (plus C13 school_consensus ~0.0 pre-U4).
Only **6 of 12 currents carry live signal**. Because convergence is a saturating sum, dead currents
don't just lower scores — they suppress evidence DIVERSITY, which also deflates
`independent_current_count` (the I-22 anti-echo-chamber metric) and the confidence labels. So the
windows that survive the caps are also under-scored.

### B2. The muhūrta/panchāṅga service is passed as None (verified ka_sangam.py:281)
`muhurta_service=None` — the entire panchāṅga + tāra-bala evidence stream (a DECLARED upstream of
both ka_sangam and ka_vighnakara) is a no-op. The service EXISTS and has tāra-bala wired; it's
simply never called. **Highest-leverage single fix** — wiring it lights up 2 currents (0.13) + real
tithi for obstruction.

### B3. The entire SUBSYSTEM signal class is filtered out of convergence (verified ka_sangam.py:87)
`AND signature_class != 'SUBSYSTEM'` excludes every subsystem-class signal — nakshatra, sade-sati,
panchāṅga, varga-pattern, composite-state, annual — from EVER getting temporal activation. The
ratified design (`L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS §T7`) specifies a full SUBSYSTEM template
(Sade-Sati→Saturn-gochara, medical→malefic-to-āyur, Vāstu→directional), but the binder has no
`_build_subsystem` and the engine `_resolve_transit_planet` returns None for SUBSYSTEM. These signals
are classified, stored as predicates, then dropped. `varga_pattern` + `composite_state` alone are
high-volume classes — this is the single biggest BREADTH gap.

### B4. ka_yojaka reads only 1 of 6 bo_* assets (verified ka_yojaka.py:33)
Reads only `bodha_msr_signals`. The 5 other L2 assets (bo_sangati domain-links, bo_drishti aspects,
bo_upaya remediation, bo_karanajala, bo_samskara) are never consumed, so activation predicates are
built blind to L2 relational context. Declared `bg_transit_rules` + `ga_dashas` are also unread (the
ledger's rule IDs are hardcoded literals `[1,2,3,4]`, not queried).

### B5. ka_vighnakara reads neither of its 2 declared services + runs on hardcoded proxies
Reads only `kala_convergence`; ignores declared `ka_gochara` + `ka_muhurta_seva`. Its detectors are
placeholders: malefic-transit gated on a **literal Saturn-in-Gemini 2030-04-01→2032-06-30 date
window** (ka_vighnakara.py:139), panchāṅga obstruction is `day % 15 ∈ {4,9,14}` arithmetic (not real
tithi), and gandanta + papakartari + combustion return `not_implemented` stub rows. So danger
detection is largely synthetic.

---

## PART C — Per-asset verdict (count = design vs cap vs unconsumed-upstream)

| Asset | Count cause | Verdict |
|---|---|---|
| ka_yojaka | full MSR projection | ✅ COMPLETE — the reference |
| ka_kalasutra | full count, hollow content | ⚠️ count OK, activation-dates NULL for 99.9% (ka_sangam cap symptom) |
| ka_sangam | 60-predicate cap + 5y horizon + 0.0 weights | ❌ MASTER CHOKE — caps + ~40% dead evidence |
| ka_vighnakara | LIMIT 200 + proxy detectors + ignores 2 upstreams | ❌ capped + synthetic detection |
| ka_kala_darshana | LIMIT 300 + doesn't read ka_kalasutra | ❌ capped |
| ka_jivana_parva | MD-only (level_n=1) | ⚠️ defensible design, but AD/PD unused + dominant_signal_class stubbed |
| ka_bhavishya_lekha | LIMIT 50 + 3y window | ❌ the literal "50" cap |
| 5 services | 0 rows by design | ✅ correct (health-probed) |

---

## PART D — Fix priority (highest leverage first; each is a native scope decision)

1. **Wire the muhūrta service into ka_sangam** (remove `muhurta_service=None`) → lights panchanga
   (0.07) + tara_bala (0.06) + real tithi for ka_vighnakara. Service already exists. Biggest
   evidence gain per unit effort.
2. **Wire the 3 other dead currents**: benefic_dristi (0.10, from bo_drishti/aspect data),
   nakshatra_subsystem (0.05, from ga_nakshatra), cross_dasha_agreement (0.12, the U1 multi-dāśā
   wiring). Restores ~0.33 more weight + evidence diversity.
3. **Build the SUBSYSTEM template (§T7)** — the `_build_subsystem` binder + per-subsystem timing
   rule + remove the `!= 'SUBSYSTEM'` filter. Unlocks the whole subsystem signal class for temporal
   activation (biggest breadth gain).
4. **Raise/parameterize the caps** consciously: `_MAX_PREDICATES` (60→?), `_HORIZON_YEARS` (5→full
   life?), `LIMIT 50/200/300`, `_LIFETIME_MAX_ROWS`. THIS IS A RUNTIME-COST TRADEOFF — needs a
   performance plan (heavier builds) + native sign-off on the budget. Don't lift blindly.
5. **Replace ka_vighnakara's proxy detectors** with real gochara-driven malefic-transit /
   gandanta / papakartari / combustion (the not_implemented stubs).
6. **ka_yojaka: read the other bo_* assets** for richer L2 context in predicates.
7. **(Optional) ka_jivana_parva: add AD-level chapters**; populate dominant_signal_class.

---

## IMPORTANT FRAMING

- **None of this is a correctness bug** — what Kāla computes is right; it just computes on a
  deliberately narrow slice. The caps were sized for runtime safety; the dead weights/SUBSYSTEM
  filter are "wire later" debt from the autonomous build, not errors.
- **This is a SCOPE + PERFORMANCE decision, not a silent patch.** Lifting caps multiplies build
  time; wiring currents changes every convergence score (re-tuning territory); the SUBSYSTEM
  template is genuine new build. Each should be a deliberate, native-ratified enhancement — ideally
  a sequenced "Kāla completeness" workstream, possibly folded into the L4 upstream-first work since
  some currents (cross_dasha from U1 multi-dāśā) were explicitly deferred to that phase.
- **Recommendation:** treat this as a **Kāla v2 completeness pass**, prioritized as Part D, decided
  item-by-item. Do NOT bulk-lift caps before wiring the evidence (you'd get more, but equally
  under-scored, windows). Wire evidence (1-3) FIRST, then raise caps (4) with a perf budget.

---

*End of L3_KALA_COMPLETENESS_AUDIT v1.0. The counts are modest because Kāla runs on a 60-of-66,738
predicate slice, a 5-year near horizon, hardcoded LIMITs, ~40% dead convergence weight, a None'd
panchāṅga service, and a whole signal class filtered out — all fixable, all needing your scope call.*
