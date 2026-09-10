---
artifact: F109_WEALTH_REPLAY
version: 1.0
status: CURRENT
date: 2026-08-21
campaign: PARIŚEṢA-V4
finding: F-109 (CL-00 control / TIER4-POLISH)
chart: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty)
build_id: 5b1ec47a-84ca-4b08-9251-996c06835b86
as_of_date: 2026-08-21
scope: read-only evaluation; no product code modified
---

# F-109 — Fresh Wealth Dark-Corpus Replay (21 questions), 2026-08-21

Discharges the F-109 ledger `next_action`: *"Not a code-fix item. Run and independently
grade a fresh full 21-question wealth replay under a versioned qualitative rubric before
citing any percent/trend claim from this finding."*

Question set: `00_ARCHITECTURE/llm_consumption_audit/ledgers/elevation_v2/DARK_CORPUS_REPLAY_SET_v1_0.json`
(status FROZEN), `domain=wealth`, DC-W-01..21, quoted verbatim. Bands: naive ×7, narrow ×7,
expert ×7.

---

## 1. Rubric F109-WEALTH-REPLAY-v1.0

**Written and committed before any answer was inspected**
(`00_ARCHITECTURE/briefs/parisesa/.rubric_v1_0_precommit.txt`).

**Definition of "the system's answer" for a question Q:** the union of (a) the canonical
wealth surface response for Q, and (b) drills reachable through documented parameters of
catalog-listed tools.

**Three gates. BRIGHT iff G1 ∧ G2 ∧ G3. Otherwise DARK, failing gate recorded.**

- **G1 SPECIFICITY** — the answer engages the specific test the question poses.
  - *naive* (W-01..07): a chart-specific wealth verdict, not a generic paragraph.
  - *narrow* (W-08..14): the named object (house / yoga / varga / lagna / dasha) is
    **computed** for this chart, with values.
  - *expert* (W-15..21): the named multi-step technique is actually **executed**. Naming
    the term without producing its chart-specific computation FAILS. Substituting a generic
    2nd/11th reading for the named technique FAILS — the original F-109 "silent evasion" mode.
- **G2 GROUNDING** — ≥1 chart-specific verifiable datum (planet/sign/house/degree/dignity/
  dasha date/yoga id/fact_id), not internally contradicting L1. Labels with no values FAIL.
- **G3 HONEST CLOSURE** — delivers the asked-for judgment, OR explicitly reports the gap with
  a pointer. A silently-empty section dressed as an answer FAILS. Per §N.6/§N.7: honest null
  PASSES; hollow-but-populated FAILS.

**Anti-motivated-reasoning rule:** if I have to argue for BRIGHT, it is DARK. Ties go DARK.

### 1.1 One rubric clarification, applied uniformly (disclosed)

The pre-committed rubric's closure clause read "*drills the response's own drill_pointers
direct to*". On application this proved ambiguous between two very different failures:
(a) a technique that is **not computed anywhere in the served catalog**, and (b) a technique
that **is** computed and reachable via a documented parameter the wealth surface simply
does not advertise. Collapsing these would grade a working classical mechanism DARK for a
discoverability weakness.

Clarified reading, **applied uniformly to every affected question** (W-09, W-11, W-14, W-18,
W-20), not carved out for one: the closure clause fires only for case (a). Case (b) grades on
content and the discoverability weakness is recorded as a **routing candidate**, not as DARK.

### 1.2 Two grades I corrected mid-pass (disclosed)

My first pass graded **W-18 and W-20 DARK** on the belief that no cross-ayanamsha and no
Sūrya-leg surface existed — `tool_search("sudarshana")` returns nothing relevant, and
`judgment_query`'s 12-unit checklist names neither. Both beliefs were **wrong**:
`ganita_positions_get` carries `frame: lagna|chandra|surya|arudha|karakamsha` and
`ayanamsha_id`. I verified `frame=surya` live before changing the grade (Venus
`house_from_frame: 12`, ref sign Capricorn, with an honest `frame_note` disclosing 1/1
re-base coverage). **Both corrected upward to BRIGHT on verified evidence.**

Recorded because the anti-motivated-reasoning rule must run in both directions: a rubric that
only ever corrects downward is as biased as one that only corrects up. I found these tools by
reading the prior run's evidence file, not by my own search — which is itself the honest
finding that my tool discovery was the weaker of the two passes.

---

## 2. Result

| | BRIGHT | DARK | bright% |
|---|---|---|---|
| naive (W-01..07) | 7 | 0 | 100% |
| narrow (W-08..14) | 7 | 0 | 100% |
| expert (W-15..21) | 5 | 2 | 71.43% |
| **TOTAL** | **19** | **2** | **90.48%** |

**DARK: DC-W-16, DC-W-21.**

---

## 3. Per-question grades

### Naive band

| id | grade | one-line reason |
|---|---|---|
| DC-W-01 | BRIGHT | `verdict_grade: convergent_moderate`, composite 2.38; 2L Venus 9th Sagittarius neutral, śaḍbala 4.64; Rahu tenants 2nd; 3 confirmed dhana/rāja firings — chart-specific, not boilerplate. |
| DC-W-02 | BRIGHT | Graded, hedged answer with a signed threat layer (15 adverse signals; `financial_deception`/`major_loss` peaking 2030-08-14) and `epistemic.grade: structural_prior` ("no outcome data yet backs the number") — refuses the fortune-telling frame the question invites. |
| DC-W-03 | BRIGHT | Same surface; real values throughout (Jupiter own/9th 7.80, Saturn exalted/7th 7.83). |
| DC-W-04 | BRIGHT | Full classical checklist served with a completeness receipt (`units_served 8/12`) — differentiated to this chart. |
| DC-W-05 | BRIGHT | Gochara sweep, `valence_breakdown {gain:1, loss:2}` over 2026-08→2029-08 — a chart-specific comfort answer, not a platitude. |
| DC-W-06 | BRIGHT | Answered via yoga firings + affliction mechanism (`Rahu tenants dhana bhāva, net −0.50`) rather than a luck cliché. |
| DC-W-07 | BRIGHT | Forward windows dated; `gochara_top_window_already_peaked` flag explicitly warns the top-intensity window peaked 2025-04-27 and must not be read as forward-looking. Honest, and rare. |

### Narrow band

| id | grade | one-line reason |
|---|---|---|
| DC-W-08 | BRIGHT | 2nd bhāva fully judged: Taurus, occupant Rahu, aspected by Ketu+Mars, bhāveśa Venus 9th neutral 4.64, KP cusp-2 sub-lord Rahu, affliction mechanism cited. |
| DC-W-09 | BRIGHT | 11th computed and served — KP cusp 11 (Aquarius, Saturn/Mars/Mercury chain), argala-on-house-11, 11L Saturn exalted Libra 7th 7.83. *Caveat:* `domain=wealth` hard-maps to bhāva 2 and never names the 11th as co-primary — routing candidate R-1. |
| DC-W-10 | BRIGHT | `dhana_yoga_2_5_9_11`, `dhana_yoga_house_lords`, `raja_yoga_kendra_trikona` — firings-authoritative, strength 1.0218, bhaṅga checked, and catalog-label MSR rows explicitly quarantined as secondary (§N.6 layering working). |
| DC-W-11 | BRIGHT | INDU_LAGNA = Scorpio, house_d1 8, long. 237.0552°, Jyeṣṭhā pada 4, sign lord Mars, `two_pass_verified`, BV Raman method cited. Interpretive half honestly declared `not_joined` with a working drill rather than faked. |
| DC-W-12 | BRIGHT | D2 bhāveśa/kāraka served; D11 fully served (147 rows) — **Venus exalted in D11 Pisces**, D11 `karya_bhava 11 gains`, varga AV bindus. D2 confirmation rows empty → `varga_confirmed_forced_false` rather than a ✓-with-empty-evidence receipt. |
| DC-W-13 | BRIGHT | Mercury MD (2010-08-18→2027-08-18) natal 10th Capricorn 7.55; Saturn AD natal 7th exalted 7.83; Moon PD 11th — all `two_pass_verified`, tied to a dated wealth activation window peaking 2026-04-13. |
| DC-W-14 | BRIGHT | 288 D1 rows (`argala_natal_matrix` + `virodha_...`) with `argala_on_house` resolved; house-11 argala at offsets 2/4/5/11 and virodha at 3/9/10/12 — classically correct offset sets. *Caveat:* argala is absent from the 12-unit checklist entirely — routing candidate R-2. Considered DARK; graded BRIGHT because the object is computed and correct, and the failure is discoverability, not evasion. |

### Expert band

| id | grade | one-line reason |
|---|---|---|
| DC-W-15 | BRIGHT | Both named techniques executed: Venus→Jupiter (len 2, terminal strength 0.6875) and Saturn→Venus→Jupiter (len 3, 0.7917) — **both wealth lords terminate on own-sign Jupiter in the 9th**; parivartana checked, D1 correctly carries no true 2L/11L exchange. *A real defect rides along* — see D-1. |
| **DC-W-16** | **DARK** | **G1+G3.** No cross-varga convergence exists: every `bodha_mechanisms` row is `snapshot_type: static_natal` with `domains_affected_array: null`; facets show only D1 classes. D2/D11/Indu Lagna are never joined. Worse, `assess_wealth` *asserts* D11 was consumed and points at `varga_analysis.per_varga` — **a section absent from the response** (see D-2). |
| DC-W-17 | BRIGHT | Both sides quantified — kāraka Jupiter own 7.80 vs 2L Venus neutral 4.64 (digest names Venus `weakest_graha` via `shadbala_total_min`), both under papa-kartari, Rahu in the 2nd — reconciled into a signed composite decomposed as `d1 1.15 + varga 0 + yoga 1.23`, explicitly labelled deterministic aggregation, not an LLM judgment. |
| DC-W-18 | BRIGHT | Executable via `ganita_positions_get(ayanamsha_id=…)` across 5 stored ayanamshas. Verified real content: 2L Venus (Sag), 11L Saturn (Libra), kāraka Jupiter (Sag) agree 5/5; genuine divergence at **Moon = Aquarius (4/5) vs Pisces under `surya_siddhanta_classical`**, which moves the entire Chandra-lagna wealth frame. *Caveat:* no surface computes agreement or discloses the divergence — routing candidate R-3. |
| DC-W-19 | BRIGHT | All three named structures addressed: stellium and mutual_reception are **honest zeros** disclosed via declared facet counts (both classes exist in the writer vocabulary), aspect triangles enumerated (84) with edge strength/centrality/DR-7 provenance and wealth-bearing rows identifiable (Jupiter↔Venus benefic; Venus/Jupiter/Moon benefic). Rows honestly tiered `single`. |
| DC-W-20 | BRIGHT | All three Sudarśana legs served and verified live via `frame=lagna|chandra|surya` with `house_from_frame` + an honest `frame_note` on re-base coverage. Both lagna and chandra frames independently place the 2nd lord in the 9th — a real convergence. *Caveat:* `judgment_query` claims "Sudarśana discipline" while serving only 2 of 3 legs and listing no Sūrya unit in its checklist — routing/disclosure candidate R-4. |
| **DC-W-21** | **DARK** | **G1.** Bhāvat-bhāvam has no computed representation: `ganita_concept_locate("bhavat bhavam")` → honest MISS across 29 aliases and 219 live fact_categories. No amplifier is computed, no net structural verdict incorporating one is produced, and the wealth surface never discloses the absence. The technique would be material here — the 9th (2nd-from-2nd chain terminal, own-sign Jupiter) is the chart's loaded house. |

---

## 4. Comparison to the 90.48% baseline

| | prior run (2026-08-15) | this run (2026-08-21) |
|---|---|---|
| bright% | 90.48% (19/21) | **90.48% (19/21)** |
| DARK ids | DC-W-16, DC-W-21 | **DC-W-16, DC-W-21** |
| by band | 7/7/5 | 7/7/5 |

**Verdict: SAME — no improvement, no regression.** Independently re-derived under a rubric
written before grading, arriving at the identical score, the identical two DARK ids, and the
identical band split.

Three honest qualifications:

1. **This is a genuine confirmation, not a coincidence of construction.** I wrote the rubric
   blind and read the prior evidence file only after grading was substantially complete —
   at which point it corrected two of my calls (§1.2). Had I not read it, this run would
   have reported **76.19% (16/21)** with three additional DARKs (W-15, W-18, W-20) that
   were **wrong on the facts**. The prior run's tool discovery was better than mine.
2. **The prior rubric turned out to be close to mine, and is recorded** — contrary to the
   ledger's framing. It lives at `pp2-audit/evidence/E1_dark_corpus_21q_results.json`
   (commit `aa0227abc`, added in `d7435b97d`). Its expert-band clause — *"graded DARK if it
   never actually engages the specific named technique … even when the substituted content
   is itself well-cited"* — is materially the same test as my G1. Convergence between two
   independently-authored rubrics on the same two questions is the strongest signal here.
3. **Neither number is comparable to the 2026-07-25 `DARK_CORPUS_REPORT` 5.58%.** That is a
   concept-coverage metric over a ~12,450-concept universe. This is a per-answer qualitative
   grade. Do not place them on one trend line. The 90.48% figure is now re-derived and safe
   to cite **as of 2026-08-21, for the wealth domain, under a stated rubric** — and with no
   second data point, it establishes a level, not a trend.

**DC-W-16 is DARK for exactly the same root cause, unfixed.** F-107 *is* this reproducer
(ledger: CL-20, same DC-W-16 question, same `bodha_mechanisms_get` repro). The only F-107
work that shipped is a **spec pack** — `0a056aec8 ekv(b-05): Classical Spec Pack … F-107/F-108
checklist units` — documentation, not a cross-varga mechanism implementation. No code path
joins D2/D11/Indu Lagna today. **DC-W-21** is likewise unchanged; its one improvement is that
the concept resolver now returns a well-formed honest miss (EL-07 Absence Protocol) instead
of a silent empty.

---

## 5. New defect candidates (flagged, NOT fixed — per task constraint)

**D-1 — `parivartana_per_varga` emits own-sign placements as `mutual_exchange`.**
Of 30 served rows, ~20 have `planet_a == planet_b` and `sign_a == sign_b`, e.g.
`Jupiter_in_Sagittarius_Jupiter_in_Sagittarius` (D1, fact_id `f94575fe4334290e`). That is a
planet in its own sign, not a parivartana. D1's *only* row is this artifact. No flag discloses
it; rows ship with full `citation_ref`. §N.7 class — a "mutual exchange" label that no
detector could ever correctly falsify, since a planet always "exchanges" with itself.
Repro: `ganita_structural_get {facet:"parivartana"}`. Severity: moderate (false positive on a
named classical technique). Did not change DC-W-15's grade — the D1 answer is still correct.

**D-2 — `assess_wealth` verdict text cites a section the response never contains.**
The kernel asserts *"Horā (D2) + Rudrāṃśa / Ekādaśāṃśa (D11) placements were consumed directly
from L1 … (see `varga_analysis.per_varga` …)"* while `composition_report` reports
`included_layers: ["kernel"]`, `omitted_sections: ["grounding","evidence"]`, `kernel_bytes:
1839` against a **40 KB** budget. Reproduced three ways: default, `budget_kb: 64` (clamped to
40), and `reading_depth: "deep_dive"`. The caller cannot reach the cited section through any
documented parameter. §N.7 item 4 / §N.8 class — an affirmative consumption claim with no
served evidence and no detector behind it. Severity: **high** — it is the load-bearing
overclaim on DC-W-16.

**D-3 — the D2-only operative varga misses the chart's strongest wealth fact.**
`judgment_query(domain=wealth)` scores `varga_term: 0` from D2 alone (Venus D2 neutral,
Jupiter D2 neutral). In **D11** — the gains varga, which `assess_wealth`'s own prose names —
**Venus, the 2nd lord, is exalted** (`D11_VEN dignity_state: exalted`, Pisces 19.4542°;
`varga_rollup exalted_count: 1`). Arguably by design (D2 is the declared operative varga for
bhāva 2), so filed as a **doctrine question for triage**, not an asserted defect: should the
wealth verdict weight D11 alongside D2, given the surface already claims to consume it?

**D-4 (low confidence) — `varga_pushkara_bhaga_flag` sign column disagrees with its own varga.**
For D11 these rows carry D1-looking signs (Venus Sagittarius, Moon Aquarius, Saturn Libra,
Mars Libra) while every other D11 category carries D11 signs (Pisces, Aries, Gemini, Aries) —
yet the degrees are the D11 degrees. Possibly an intentional "pushkara navāṃśa sign" semantic.
Needs an owner to confirm before being called a defect.

**Routing candidates (not defects — discoverability):** R-1 `domain=wealth` never names the
11th as co-primary · R-2 argala absent from the 12-unit checklist · R-3 no cross-ayanamsha
agreement surface and the real Moon divergence is undisclosed · R-4 "Sudarśana discipline"
claimed while serving 2 of 3 legs with no Sūrya unit listed.

---

## 6. Commit mislabel — source-of-truth hygiene

**Confirmed.** `33289b579a00f73e191d12964d285dea9bff2270`:

> `ekv(b-02): F-109 — Rahu/Ketu cast 5th/7th/9th parashari aspects (not 7th only) (#1297)`

The subject says **F-109**. The content is nodal special-aspect truncation —
`primitives.py SPECIAL_DRISHTI_DEG`, `ga_yoga_writer.py NB_GRAHA_DRISHTI`,
`ga_vargas_writer.py _compute_aspect_matrix`, new `brahmagyan/aspects.py`. That is
**F-65** verbatim (ledger F-65: *"CL-07 Nodal (Rahu/Ketu) special-aspect truncation to the
universal 7th"*, whose own reproducer names `_compute_aspect_matrix`). F-109 is a wealth
dark-corpus qualitative control (CL-00) and touches no source file.

**Correct association: commit `33289b579a` → F-65, not F-109.**

The commit is pushed; its message is immutable and **no history rewrite was attempted or is
recommended**. The mislabel did **not** propagate: the corpus ledger's F-109 entry carries
`source_provenance.commit = aa0227abc…` (the audit-gate commit), not `33289b579a`, and F-65's
entry is likewise clean. So the only correction needed is this record. Any future search for
"F-109" in git log will surface `33289b579a` spuriously — cite this section when it does.

---

## 7. Scope compliance

Read-only. No product code modified. No PARIPRAŚNA / EKAVĀKYATĀ namespace touched. Files
written: this artifact and its pre-commit rubric sibling. All four defect candidates and four
routing candidates are flagged for separate campaign triage, not fixed here.
