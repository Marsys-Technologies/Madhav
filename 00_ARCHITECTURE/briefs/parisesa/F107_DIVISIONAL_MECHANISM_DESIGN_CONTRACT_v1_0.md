---
canonical_id: F107_DIVISIONAL_MECHANISM_DESIGN_CONTRACT
version: 1.0
status: DRAFT — AWAITING NATIVE RULING
campaign: PARIŚEṢA-V4
finding: F-107 (CL-20 Classical-derivation defects)
authored: 2026-08-21
author: GA-2 design authority (PARIŚEṢA-V4 repair lane)
scope: design contract only — NO convergence algorithm is implemented by this document or its PR
supersedes: none
---

# F-107 — Divisional (Cross-Varga) Mechanism Design Contract

## §0 — What this document is, and is not

This is a **design contract awaiting a native ruling**, not a specification to build from. It
records what was verified live, distinguishes the parts of F-107 that were mechanically
fixable from the part that is genuinely from-scratch design, and lays out the classical
methodology options for the latter **with their sources and their disagreements stated**.

It deliberately stops short of choosing one. Wealth is a consequential domain; per CLAUDE.md
§B.10 and §N.7 item 6, an invented convergence weighting that reads plausibly is worse than a
stated gap. The PR that carries this document ships **disclosure only**.

---

## §1 — The finding, reproduced live

**Claim (corpus_ledger F-107):** `judgment_query(domain='wealth')` and `bodha_mechanisms_get`,
asked DC-W-16 — *"What convergent mechanisms across my D1, D2, D11 and Indu Lagna support or
contradict wealth accumulation?"* — silently substitute a D1-natal-graph-only mechanism list
for the cross-varga convergence the question named; no field, filter, or row anywhere in the
response references D2, D11, or Indu Lagna.

**Reproduced 2026-08-21** against production, chart `482012f1-710e-4a25-994a-93821f5871aa`:

| surface | result |
|---|---|
| `bodha_mechanisms_get` | 123 rows, **every one** `snapshot_type='static_natal'`. Facets: `mutual_aspect_triangle` 84, `mutual_aspect` 36, `graha_bhava_affliction` 2, `convergent_dispositor_chain` 1. `empty_reason: null`. **No varga field, facet, filter or note anywhere in the envelope.** Claim CONFIRMED. |
| `judgment_query(domain='wealth')` | `operative_varga: "D2"`, `varga_term: 0`, `receipt.varga_confirmed: false`. Discloses `varga_confirmed_forced_false` and `special_lagnas: not_joined`. **Never mentions D11 at all.** Claim CONFIRMED in part — the tool was partially honest already, but silent on the D11 leg. |

---

## §2 — What the investigation found that the ledger did not know

The ledger graded F-107 as needing *"a divisional-mechanism precode contract authored and
independently reviewed… design work, not an existing fix to rebase."* That is **correct for
the mechanism half and wrong for the data half.** Three material discoveries:

### §2.1 — The data all exists, and is two_pass_verified

| leg | status | location |
|---|---|---|
| **D2 (Horā)** | EXISTS, richly | `chart_divisionals` varga='D2'; `chart_facts.graha_dignity_per_varga` subject `D2_<CODE>`; plus D2-specific `varga_hora_class` (`surya_hora`/`chandra_hora`, `hora_d2_house`) from `ga_vargas_writer.py` |
| **D11 (Rudrāṃśa / Ekādaśāṃśa)** | EXISTS | 147 divisional facts on the canonical chart — `varga_position`, `varga_dignity`, `varga_house_lord`, `varga_house_occupant`, `varga_ashtakavarga`, `varga_rollup`, and `varga_karya_bhava_per_varga` = `{karya_bhava: 11, "gains_karya2"}`. Built via `SUPPLEMENTARY_11` in `ga_vargas_writer.py`. |
| **Indu Lagna** | EXISTS, `two_pass_verified` | `chart_facts` `fact_category='special_lagna'`, `fact_subject='INDU_LAGNA'` — sign Scorpio, sign_lord Mars, house_d1 8, nakshatra Jyeshtha. Provenance: `PyJHora drik.indu_lagna (BV Raman method)`. Also emitted as an MSR signal (`special_lagna_emitter.py`, class_prior 0.90, domain `wealth`). |

**Known honest data gap:** per-varga Ashtakavarga (`ashtakavarga_pinda_sarva_per_varga`) has no
D11 rows. This is already disclosed per-call by `assess_wealth`'s `empty_reason`, not stubbed.

### §2.2 — A ratified cross-varga convergence primitive ALREADY EXISTS

This is the discovery that most changes the scope picture. `chart_vichara`'s
`varga_ratification` family — served by `ganita_vichara_get` — is a real agree/oppose
convergence vote across a domain's operative-varga set. Verified live:

```
family=varga_ratification, domain=wealth, subject=SAT
  d1_dignity: "exalted", d1_direction: "positive"
  operative_vargas: ["D1","D2","D9","D11"]
  domain_provisional: false
  per_varga: { D2: {Cancer, neutral, abstain},
               D9: {Aries, debilitated, OPPOSE},
               D11:{Gemini, neutral, abstain} }
  n_agree: 0, n_oppose: 1  →  value_num (ratification_factor): 0.8
  formula_version: varga_ratification_v1
  source_citation: DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §11
  constituent_fact_ids: [4 real chart_facts ids]
```

Algorithm (`ga_vichara_writer.py::build_varga_ratification_rows`): D1 is the **reference and
never votes**; each other operative varga votes agree / oppose / abstain against the D1 dignity
direction; `factor = clamp(1.0 + 0.2·(n_agree − n_oppose), 0.6, 1.4)`. Each opposing varga also
emits a standalone `varga_ratification_divergence` row.

Crucially, the seed config `brahma_vichara_constants.operative_vargas` gives:

```json
"wealth": {"vargas": ["D1","D2","D9","D11"], "provisional": false, "houses": [2,11], "karaka": "Jupiter"}
```

**Wealth is the only `provisional: false` — i.e. design-RATIFIED — domain set in the table.**
The other four (career, marriage, health, general) are all `provisional: true`.

So the instrument already has a ratified opinion about which vargas bear on wealth, and it
already computes a convergence vote over them. **`judgment_query` does not read
`chart_vichara` at all** (zero references), and `bodha_mechanisms_get` cannot — the CGM graph
has no varga dimension.

### §2.3 — The mechanism table structurally cannot carry a varga

`bodha_mechanisms` (migration 445) has **no** `varga_id` / `varga` / `divisional_chart` column.
`snapshot_type` is a module-level constant `"static_natal"` in `bo_yantra_mechanism.py` — a
natal-vs-transit axis, not a varga axis, with no code path assigning any other value.

Its upstream is D1 throughout: `bodha_cgm_nodes` / `bodha_cgm_edges` (migration 325) carry no
varga dimension either; `bo_bimba.py` filters `fact_value_jsonb->>'varga' = 'D1'`;
`bo_karanajala.py` reads `chart_vichara ... AND varga = 'D1'` and house lords as `D1_H<n>`;
`bo_yantra_mechanism.py` reads `house_d1`.

Two traps for any future implementer:

1. `bodha_cgm_edges.weight_varga_source TEXT` exists in migration 325 with the comment *"which
   varga/evidence this weight comes from"* — and is **dead**: zero writers, zero readers. It
   looks like a ready-made hook and is not one.
2. The unique key is `(chart_id, ayanamsha_id, build_id, mechanism_class, fingerprint_hash)`
   and `_fingerprint()` hashes only `mechanism_class + sorted(node_ids)`. Adding a varga
   dimension **without** folding varga into the fingerprint would collide same-class mechanisms
   across vargas and silently drop rows.

Note also `bo_karanajala.py` DOES consume `varga_consistency` / `varga_ratification` — but only
as a scalar multiplier on a D1 edge (`0.75 + 0.25 × varga_consistency`). Varga evidence tunes
edge strength; it never creates a varga-scoped node, edge, or mechanism.

---

## §3 — Scope verdict

| part of F-107 | verdict | disposition |
|---|---|---|
| No disclosure that `bodha_mechanisms_get` is D1-only | **Mechanical.** Pure honesty fix. | **FIXED in this PR.** |
| No disclosure that `judgment_query` weights one varga of the domain's two, and skips Indu Lagna | **Mechanical.** Registry already existed in `register_d8`. | **FIXED in this PR.** |
| Neither surface points at `ganita_vichara_get`, the built cross-varga primitive | **Mechanical.** | **FIXED in this PR.** |
| Folding D11 + Indu Lagna into `judgment_query`'s **verdict score** | **DESIGN.** Requires a weighting no source ratifies. | **DEFERRED — §4.** |
| Cross-varga **mechanism detection** (named multi-node structures spanning vargas) | **DESIGN + schema migration.** Does not exist in any form. | **DEFERRED — §5.** |

The ledger's framing was right about the mechanism half. It could not have known that the
*evidence* half was already built and merely unrouted.

---

## §4 — Deferred: folding D11 + Indu Lagna into a wealth verdict

### §4.1 — The classical basis for D2 and D11 as wealth vargas

**Bṛhat Parāśara Horā Śāstra, Ch. 6 (Ṣoḍaśavarga-adhyāya)** assigns each varga a *kārya* — the
matter it ripens. Horā (D2) is assigned **dhana** (wealth/substance); the classical ṣoḍaśavarga
scheme (BPHS 6.6–6.11) lists Horā second after Rāśi. The instrument's own
`varga_karya_bhava_per_varga` fact for D11 stores `gains_karya2`, matching **lābha** (gains).

**Two honest problems the sources create, which the native must rule on:**

1. **D11 is not in the Parāśarī ṣoḍaśavarga.** The sixteen are D1, D2, D3, D4, D7, D9, D10,
   D12, D16, D20, D24, D27, D30, D40, D45, D60. D11 (Rudrāṃśa / Ekādaśāṃśa / Labhāṃśa) belongs
   to a **supplementary** tradition — the codebase itself files it under `SUPPLEMENTARY_11`
   alongside D5/D6/D8/D14/D15/D21/D32/D33/D50/D54. Its use for gains is real in modern practice
   (and in the Rudrāṃśa material some Śaiva-tradition texts carry), but it does **not** have
   the same Parāśarī footing D2 has. Weighting it *equally* with D2 would give a supplementary
   varga the authority of a ṣoḍaśavarga member.
2. **Horā's classical use is contested.** BPHS Ch.6's Horā is the *sun/moon half-sign*
   (Leo/Cancer only — which is exactly what `varga_hora_class` stores as `surya_hora`/
   `chandra_hora`). A Horā "dignity" in the ordinary exalted/own/friend/enemy sense — which is
   what `graha_dignity_per_varga` subject `D2_<CODE>` holds, and what `judgment_query`'s varga
   term currently reads — is a **later, Parāśarī-D-chart-generalized** reading, not the BPHS
   Ch.6 Horā. Both objects exist in L1. **Which one the verdict should weight is an open
   question this contract does not answer.** (Observed live: `judgment_query` reported D2
   bhāveśa dignity `neutral` with weight 0 while `varga_confirmation.rows` was empty — the
   generalized-D2 reading contributing nothing while the hora-class facts sat unread.)

### §4.2 — Indu Lagna: real, and a different KIND of object

Indu Lagna (BV Raman's rendering of the Jaimini/BPHS *dhana* lagna — computed from the kalās
of the 9th lords from Lagna and from Moon, summed, mod 12, counted from the Moon) is stored
`two_pass_verified` with an explicit BV Raman provenance string. It is a genuine, distinct
wealth-strength indicator.

But it is **a lagna, not a varga.** It cannot join a `varga_ratification` vote — there is no
"Indu Lagna dignity of Venus" to agree or oppose with. Its classical use is: *benefics
occupying or aspecting Indu Lagna, and the strength of its sign-lord, indicate wealth.* That is
a **different predicate shape** from per-graha varga dignity, and folding it into a single
scalar term alongside varga votes would be a category error.

Sources disagree on the kalā values themselves (Raman's table vs. other renderings), which is a
second reason to require an explicit ruling rather than a default.

### §4.3 — Options for the native

| option | what it does | cost | honesty risk |
|---|---|---|---|
| **A. Route, don't re-weight** (recommended) | `judgment_query` reads the existing `varga_ratification` factor for the domain and serves it as a named, cited evidence layer beside the verdict — **without** multiplying it into `composite_score`. | Low. Reuses a built, cited, `provisional:false` primitive. | Lowest. Nothing new is invented; the factor carries its own formula_version and constituent_fact_ids. |
| **B. Multiply the ratification factor into the verdict** | `composite_score × ratification_factor` (already clamped [0.6, 1.4]). | Low code, HIGH semantics. | The factor was designed as signal-level evidence, not a verdict multiplier. Requires a ruling that its clamp and its 0.2/vote step are correct at verdict scale. |
| **C. Extend SHASTRA_MAP to `vargas: string[]` and weight each** | D2 ×0.75, D11 ×(new weight). | Medium. | Requires inventing D11's weight relative to D2 — precisely the unratified number §4.1 problem 1 warns about. |
| **D. Add an Indu Lagna term** | Benefic-occupancy/aspect + sign-lord strength on Indu Lagna as a verdict term. | Medium. | Needs a ruling on the predicate AND on the kalā table variant. Independent of A–C. |

**GA-2 recommendation: A, plus resolving the §4.1-problem-2 hora question separately.** Option
A converts F-107's wealth half from "undisclosed gap" to "served, cited cross-varga evidence"
without inventing a single number. B, C and D should each be separate, separately-ruled work.

---

## §5 — Deferred: cross-varga MECHANISM detection

This is the part the ledger correctly called from-scratch design. It is a genuinely open
research question, not an unimplemented spec, because **classical Jyotiṣa does not describe
mechanisms spanning divisional charts.**

A mechanism here means a named multi-node structure — a convergent dispositor chain, a closed
dispositor cycle, a house-lordship circuit. The classical treatment of vargas is
**confirmatory**: the rāśi promises, the amsha ripens or withholds (the Parāśarī
"D9-is-the-fruit" dictum, BPHS Ch.6–7). A dispositor chain *within* D9 is a defensible object;
a chain whose edges *span* D1 and D9 is not something any source this investigation can cite
describes. Building one would be **new method presented as classical derivation** — the exact
CL-20 defect class F-107 is filed under.

Three candidate framings, in decreasing classical defensibility:

1. **Per-varga mechanism sets + a cross-varga agreement report** (defensible). Run the existing
   `bo_yantra_mechanism` detector independently per varga; report where the *same named
   mechanism* recurs across vargas. This is "does the structure repeat in the amsha?" — a
   confirmatory question, classically shaped. Requires: a varga dimension on
   `bodha_cgm_nodes` / `bodha_cgm_edges` / `bodha_mechanisms` **and folding varga into
   `_fingerprint()`** (§2.3 trap 2). Substantial build; sound premise.
2. **Vimśopaka-weighted mechanism strength** (partly defensible). Keep D1 mechanisms; weight
   member-graha contributions by the already-computed `graha_vimsopaka_shodasavarga`. Cheap,
   and BPHS Ch.6's Vimśopaka IS a ratified cross-varga strength scheme — but it produces a
   *strength annotation on a D1 mechanism*, not a cross-varga mechanism, and must be labelled
   as such.
3. **Cross-varga edges in one graph** (NOT recommended). A single graph whose edges span
   vargas. No classical warrant found. Would also break the fingerprint uniqueness contract.

**No option here should be built without a native ruling.** Framing 1 is the only one that
could honestly be called a cross-varga mechanism, and it is a schema migration plus a writer
change plus a serving change.

---

## §6 — What the accompanying PR actually ships

Disclosure only. No convergence algorithm, no new scoring term, no schema change, no writer
change.

1. **`query_mechanisms.ts`** — a `varga_scope` block on every response (populated AND empty):
   `computed_over: ['D1']`, `frame: 'rasi_d1_natal_graph_only'`,
   `cross_varga_mechanisms_computed: false`, the not-covered vargas and special lagnas named
   explicitly, and four drill pointers led by `ganita_vichara_get`. Plus `scope_flags`, a
   scope sentence in `provenance.source`, and the D1-only scope stated in the tool
   **description** so a caller sees it before calling.
2. **`register_d9_judgment.ts`** — a `cross_varga_convergence_not_computed` judgment flag and a
   `corroborating_vargas` reading-checklist unit when the domain has classical vargas beyond
   its operative one; the `special_lagnas` unit now names Indu Lagna specifically for wealth
   rather than saying "Indu/Ārūḍha/Hora lagnas not folded here". All carry live drill handles.
3. **`reading_checklist.ts`** — `DOMAIN_DIRECT_VARGAS` / `DOMAIN_INDU_LAGNA` relocated here
   (leaf module) so `judgment_query` and `assess_*` read ONE registry; `register_d8` re-exports
   them so every existing import path and the Lane-E CI rule keep working. A second local copy
   would have been a GA.1-class registry disagreement (§B.8).
4. **`envelope.ts`** — the new flag code registered in the closed vocabulary.
5. **Tests** — 15 new, locking the disclosure. They assert the NEGATIVE claim is stated
   (`cross_varga_mechanisms_computed: false`), never that a cross-varga finding exists.

**Deliberately NOT shipped:** any weighting of D11 or Indu Lagna into a wealth verdict, and any
cross-varga mechanism detection. Both await the rulings in §4.3 and §5.

---

## §7 — Ruling requested

1. **§4.3 — Option A, B, C, or D** for routing/weighting cross-varga wealth evidence into
   `judgment_query`. GA-2 recommends **A**.
2. **§4.1 problem 2** — should the wealth varga term read BPHS Ch.6 hora-class
   (`surya_hora`/`chandra_hora`, already stored) or generalized D2 dignity (currently read)?
3. **§5** — is framing 1 (per-varga mechanism sets + agreement report) authorized as a build,
   deferred, or rejected?
4. **Adjacent, out of F-107 scope but surfaced by it:** `varga_confirmed` in `judgment_query`'s
   receipt is a bare `rows.length > 0` existence check on `chart_divisionals`, not a
   confirmation test — it cannot report "the amsha contradicts the rāśi". Since
   `chart_divisionals` is populated for every built chart, it is a near-always-green signal
   with no detector behind the claim it makes (CLAUDE.md §N.8). Recommend filing separately.

---

*End of F107_DIVISIONAL_MECHANISM_DESIGN_CONTRACT v1.0. Status DRAFT — no ruling recorded. All
live evidence in §1–§2 verified against production on 2026-08-21, chart
`482012f1-710e-4a25-994a-93821f5871aa`.*
