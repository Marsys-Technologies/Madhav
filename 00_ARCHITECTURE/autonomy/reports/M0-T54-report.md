# M0-T54 — independent re-derivation of D-57's 99/10 ownership split

**Agent:** KĀRAKA-M0-T54 · **Mode:** READ-ONLY · **Task:** WORK_QUEUE.jsonl:141
**Method constraint honoured:** I did not open, run, or read the output of M0-T51's script. My
starting points were D-57's `corrected_grounds` (the claim under test), D-30 part 1 (the test),
and `NIRMANA_ELEVATION_PLAN_v4_0.md` itself. I read `check_asset_catalogue_contract.py` only to
learn what each rule id *asserts*, because prong (b) of D-30's test is column-level and cannot be
applied without knowing which column each rule is about.

## 0 — Headline

**I do not reproduce 99/10.** Applying D-30's test as D-30 actually words it, I derive
**97 M0-BLOCKED / 12 NAMED-LATER-RUNG**, with a further 6 pairs I flag as genuinely uncertain
and did not move. The arithmetic of the split is sound; its *application* is not uniform.

Six firm disagreements, in both directions:

| pair | D-57 says | I derive | why |
|---|---|---|---|
| C-15 / `ka_graha_sancara` | M0-BLOCKED | **NAMED → R3** | §8.4 R3 row names the asset and assigns the probe |
| C-15 / `ka_muhurta_seva` | M0-BLOCKED | **NAMED → R3** | same clause |
| C-17 / `ka_graha_sancara` | M0-BLOCKED | **NAMED → R3** | same clause |
| C-17 / `ka_muhurta_seva` | M0-BLOCKED | **NAMED → R3** | same clause |
| X-05 / `bg_ephemeris_engine` | NAMED → R0 | **M0-BLOCKED** | the §14.2 clause assigns the *image fix*, not the zero-consumer disposition |
| C-04 / `ga_sade_sati` | NAMED → R1 | **M0-BLOCKED** | the §14.2/§8.4 clauses assign the *57 % below-floor repair*, not `target_table` |

99 − 4 + 2 = **97**; 10 + 4 − 2 = **12**; 97 + 12 = 109. The 109 itself I do not dispute.

## 1 — The test I applied, verbatim

D-30 part 1 (`DECISIONS.jsonl`, D-30):

> A REGISTRY COLUMN IS M0's TO REPAIR IF AND ONLY IF (a) A PHASE-0 STEP OR M0's OWN ACCEPTANCE
> CRITERIA NAME IT — acceptance criteria count, per D-4 … — AND (b) NO MORE-SPECIFIC PLAN CLAUSE
> ASSIGNS IT TO A LATER RUNG, in which case the specific governs the general, per D-12 (the
> gochara zombie rows) and D-23 (lel_events -> SOURCE at §8.4's R5 row).

Two things follow that govern everything below.

**(i) "IT" is the COLUMN, not the asset.** Prong (b) asks whether a clause assigns *this repair*
to a later rung. A clause that names the asset while assigning some *other* work to a rung does
not satisfy it. This is the reading D-30 itself uses — D-25 part 2(b) pinned the `has_writer`
ROW repair to R0 while `has_substeps` on the same assets stayed M0's.

**(ii) §8.4's rung rows are an accepted source of prong-(b) clauses.** D-30 cites
"D-23 (lel_events -> SOURCE at **§8.4's R5 row**)" as one of its two exemplars, and D-23 says so
in terms: "NIRMANA_ELEVATION_PLAN_v4_0.md:862, the §8.4 R5 row … The plan assigns this
reclassification to R5, by name."

## 2 — FINDING 1 (the root cause): D-57's evidence line is wrong about where the by-name clauses live

D-57's evidence array, item 2, reads:

> "NIRMANA_ELEVATION_PLAN_v4_0.md §14.2 (lines 1065-1071) — **the only** per-asset later-rung
> assignments by name: bg_ephemeris_engine -> R0; ga_prashna, ga_sade_sati -> R1;
> ka_gochara_sweep lifecycle exit + data_disposition -> R3"

**That claim is false, and D-57's own ruling depends on it being false.** §14.2 is not the only
such place; §8.4's rung table is another, and D-57 itself uses §8.4 (for `lel_events`, via D-23)
in the same breath. The complete inventory of per-asset later-rung assignments by name in the
plan's narrative text — every one found by boundary-exact grep over lines 1–1137 and 3476–3899:

**§8.4 R0 row (line 857), verbatim:**
> "The 6 P0s first — `bg_ephemeris_engine` (66-day red) at the very front, since every L1
> computation stands on it … Note that `rung` follows *layer*, not domain: four shared-domain
> assets live in higher layers — `ka_graha_sancara` and `ka_muhurta_seva` (**R3**), `mi_kula` and
> `mi_vistara` (**R5**) — and are not touched here, even though they are substrate."

**§8.4 R1 row (line 858), verbatim:**
> "`ga_prashna`'s zero-row unearned `lit` and `ga_sade_sati`'s 57 % are the two headline repairs;
> `ga_dashas`' stale 536,471 floor is reset to measured; … heavy resume is proven on `ga_dashas` /
> `ga_vichara` / `ga_strength`."

**§8.4 R2 row (line 859), verbatim:**
> "`bo_laksana` / `bo_samskara` 60,000 floors re-measured."

**§8.4 R3 row (line 860), verbatim:**
> "**A mixed-domain rung** (§6.2): 21 chart-domain assets plus the two shared service probes
> `ka_graha_sancara` and `ka_muhurta_seva`, both DRAFT — **promote or retire them, and give each a
> real known-answer probe with an SLO** (tier S treatment, §9). The gochara transition executed per
> §5 (v2 reclassified, F-52 rematerialization decided and recorded either way); `ka_kshetra` and
> `ka_sangam` under the shared `ResumableWriter` …"

**§8.4 R4 row (line 861):** names `ph_phaladesa` (narration-fidelity goldens).

**§8.4 R5 row (line 862), verbatim:**
> "zero-row-by-design assets recorded honestly with `target_floor = 0` and a `volume_explanation`
> rather than left reading dormant; **`lel_events` reclassified `SOURCE`**; the layer's two
> shared-domain members (`mi_kula`, `mi_vistara`) built as a shared run within this rung."

**§14.2 (lines 1066–1071), verbatim:**
> "Standing debris from v3.0's Phase 1 lands in its proper rung rather than as a bulk pass:
> `bg_ephemeris_engine`'s **image fix** and the substrate's other P0s in **R0**; `ga_prashna` and
> `ga_sade_sati` in **R1**; completion of `ka_gochara_sweep`'s lifecycle exit in **R3** — its
> registry row already reads RETIRED, but the zombie throughput rows behind its standing 'no
> writer registered' red, and its **`data_disposition`**, are still outstanding — together with the
> F-52 decision."

**§6.2 rule 2 (line 518), verbatim:**
> "**Two rungs are genuinely mixed and dispatch as run groups**: **R3** (21 chart-domain assets
> plus the shared probes `ka_graha_sancara` and `ka_muhurta_seva`) and **R5** (13 chart-domain
> assets plus `mi_kula` and `mi_vistara`)."

**§9 (lines 921–923), verbatim:**
> "Tier H's ten assets are spread across three layers, so tier-H work happens three times — five
> assets in **R1** (`ga_dashas`, `ga_vichara`, `ga_sensitive`, `ga_strength`, `ga_vargas`), three
> in **R2** (`bo_laksana`, `bo_laksana_rerank`, `bo_samskara`), two in **R3** (`ka_kshetra`,
> `ka_sangam`) — each time using the one shared `ResumableWriter` built in Track M."

**§11 (lines 978–983), verbatim:**
> "It is *not* yet verified for the **four** shared assets that live above L0 — `ka_graha_sancara`
> and `ka_muhurta_seva` (L3), `mi_kula` and `mi_vistara` (L5) … a failure there is **a
> registration defect resolved in the owning rung (R3 or R5)** — either the declared domain is
> wrong or an edge is."

**§19.6 (lines 3865–3867):** repeats §9's R1/R2/R3 tier-H rosters by name.

D-57 consulted exactly one of these nine clauses for nine of its ten decisions, and a second one
(§8.4 R5) for the tenth. That asymmetry is where the split goes wrong.

## 3 — The four flips TO named-later-rung: `ka_graha_sancara` and `ka_muhurta_seva`

- **C-15** asserts *"service ⇒ `health_probe` and `provides_apis` NOT NULL"*
  (`check_asset_catalogue_contract.py:1446`).
- **C-17** asserts *"graded `service_health` ⇒ `health_probe` NOT NULL"* (`:1448`).

Both are the `health_probe` column on two service probes. §8.4's R3 row names both assets and
assigns, in the same sentence, *"give each a real known-answer probe with an SLO (tier S
treatment, §9)"*. That is the `health_probe` work, assigned to R3, by name. §8.4's R0 row
independently forbids touching them in R0 (*"and are not touched here"*), and §6.2 and §11 both
re-state R3 ownership by name.

This clause is at least as specific as the one D-23/D-30 accepted for `lel_events` — arguably
more so, since it names the *deliverable* (a real known-answer probe with an SLO) and not only a
lifecycle state. If §8.4's R5 row satisfies prong (b), §8.4's R3 row does too. **4 pairs move.**

I did **not** move C-15/`ka_dasha_kala`, C-15/`ka_tulana`, C-15/`mi_abhilekha`, C-15/`mi_seva`,
C-17/`ka_dasha_kala`, C-17/`ka_tulana` — those four assets are never named in any rung clause
(`ka_dasha_kala`, `ka_tulana`: zero narrative mentions at all; `mi_abhilekha`, `mi_seva`: one
mention each, both in §1.5's zero-rows diagnosis table at line 311, which assigns nothing). The
R3 row's probe clause is explicitly scoped to *"the two shared service probes"*, so it does not
reach the chart-domain L3 probes. D-57 is right about all six.

## 4 — The two flips TO M0-BLOCKED

### X-05 / `bg_ephemeris_engine`

X-05 asserts *"no unresolved zero-consumer finding"*, and its own docstring defines the repair:

> "A packet is RESOLVED only when an explicit, dated disposition for that asset exists in
> `asset_catalogue_disclosed_residuals.json`'s `zero_consumer_dispositions` block, naming the
> DECISIONS.jsonl ruling that made it (disposition is charter G1 — ADHIKĀRIN's …)."

The repair is a recorded G1 disposition. §14.1's M0 acceptance criteria name that work in terms:
*"… retired-without-disposition, active-without-coverage, **unresolved zero-consumer findings** all
zero"*. The only clause naming `bg_ephemeris_engine` with a rung assigns *"`bg_ephemeris_engine`'s
**image fix**"* to R0 — a different repair on a different surface. The specific governs the general
only when the specific is about the same thing; here it is not. **Moves to M0-BLOCKED.**

### C-04 / `ga_sade_sati`

C-04 asserts *"data/artifact ⇒ `target_table` NOT NULL and the table exists"* (`:1435`). The two
clauses naming `ga_sade_sati` with a rung assign its **57 % below-floor repair** to R1 (§8.4 R1:
*"`ga_sade_sati`'s 57 % [is one of] the two headline repairs"*; §14.2: *"`ga_prashna` and
`ga_sade_sati` in R1"*, in a sentence about *"standing debris from v3.0's Phase 1"*). Neither
names `target_table` or any registry column. Meanwhile §14.1 gives M0 *"the §3 contract authored
as an enforceable per-kind specification"* and an exit criterion of *"contract violations … all
zero"*. **Moves to M0-BLOCKED.**

Note the symmetry that makes this diagnosis, not nitpicking: D-57 keeps C-08/`ka_gochara_sweep`
as NAMED-R3 and it is **right** to, because §14.2 names *"its `data_disposition`"* explicitly —
the column itself. C-04/`ga_sade_sati` and X-05/`bg_ephemeris_engine` were classified as though
they had the same kind of support, and they do not.

## 5 — Method for the 99, stated so it is falsifiable

I did not attempt to prove a negative 99 times. Instead:

**Step 1 — isolate the narrative plan.** The plan is 3,899 lines. Lines 1138–3475 are the
generated `<!-- ASSET_PLANS:BEGIN/END -->` block (§15), handled separately in §6 below. I built
`narrative.txt` = lines 1–1137 ∪ 3476–3899 (1,561 lines) with:

```
awk 'NR<1138 || NR>3475 {printf "%d\t%s\n", NR, $0}' NIRMANA_ELEVATION_PLAN_v4_0.md
```

**Step 2 — boundary-exact grep, per identity.** For each of the 72 distinct assets in D-57's
`corrected_grounds` (the 109 are 109 *(rule × asset)* pairs over 72 distinct assets — see §7):

```
grep -nE '(^|[^a-z0-9_])<asset_id>([^a-z0-9_]|$)' narrative.txt
```

The boundary class `[^a-z0-9_]` matters: a plain `grep bg_ephemeris` returns 6 hits that are all
`bg_ephemeris_engine`, and a plain `grep bo_laksana` cannot tell `bo_laksana` from
`bo_laksana_rerank`. With boundaries, `bg_ephemeris` has **zero** mentions.

**Step 3 — result.** Of the 68 distinct assets D-57 classes M0-BLOCKED, **48 are never mentioned
anywhere in the plan's narrative text**, carrying **62 of the 99 pairs**. For those, prong (b) is
not merely unsatisfied, it is unsatisfiable: no clause names the asset at all, so no clause can
assign anything about it to a rung. The 48:

`bg_class_lifetime_counts, bg_class_priors, bg_cohort, bg_compendium_index, bg_dasha_systems,
bg_dignity_reference, bg_doshas, bg_ephemeris, bg_formula_constants, bg_ghatana,
bg_kota_chakra_rings, bg_kp_sublord_division, bg_medical_mappings, bg_muhurta_lattice,
bg_nakshatra, bg_nakshatra_medical, bg_ontology, bg_parihara_rules, bg_phaladeepika_latta,
bg_prashna_rules, bg_remedies, bg_rules, bg_sign_medical, bg_transit_engine, bg_transit_rules,
bg_vastu_directions, bg_vedha_malefic_scale, bg_vidhi_floors, bg_vidhi_primitives, bg_yogas,
bo_cdlm_summary, bo_cgm_motifs, bo_chart_gestalt, bo_pratijna, ga_ayurdaya, ga_sensitive_degree,
ga_structural, ka_avadhi, ka_dasha_kala, ka_gochara_resonance, ka_kota_chakra, ka_moorti_nirnaya,
ka_sudarshana_varsha, ka_taranga, ka_tithi_pravesha, ka_tulana, ka_vedha_gochara, mi_jivanaghatana`

**Step 4 — hand-adjudicate the remaining 20 assets / 37 pairs.** Every mention of each was read in
context. Disposition:

| asset | pairs | mentions | verdict |
|---|---|---|---|
| `bg_concordance` | 1 | §1.5:309 below-floor table | no rung → M0 ✔ |
| `bg_gochara_arcs` | 2 | §9:939 tier-G exemplar; §19.6:3841 | no rung → M0 ✔ |
| `bg_gochara_citation_resolution` | 1 | §0:179, §1.2:291, :295 diagnosis | no rung → M0 ✔ (matches D-57 §6) |
| `bg_panchanga` | 1 | §9:928 tier-S roster | no rung → M0 ✔ |
| `bg_reference` | 2 | §1.5:309, §6.8:571, §9:913 | no rung → M0 ✔ |
| `bg_sarvatobhadra_grid` | 3 | §1.5:311 zero-rows "(by design)" | no rung → M0 ✔ |
| `bg_sky_calendar` | 3 | §1.5:309 | no rung → M0 ✔ |
| `bg_text_index` | 1 | §1.5:309 | no rung → M0 ✔ |
| `bg_texts` | 1 | §1.5:314 genai audit | no rung → M0 ✔ |
| `bo_laksana` | 1 (C-11) | §8.4 R2:859 floors; §9:922 tier H | rung named, **wrong column** → M0 ✔ |
| `bo_samskara` | 1 (X-05) | §8.4 R2:859; §9:922; §1.5:314 | rung named, wrong column → M0 ✔ |
| `ga_sensitive` | 1 (C-04) | §9:921 R1 tier-H roster | rung named, wrong column → M0 ✔ |
| `ga_strength` | 1 (C-04) | §8.4 R1:858; §9:921 | rung named, wrong column → M0 ✔ |
| `ka_gochara` | 1 (C-21) | §5:456, :473 (as "v2") | **uncertain — see §8** |
| `ka_gochara_v3_century_materialize` | 2 | §5:458 (as "v3") | **uncertain — see §8** |
| `ka_graha_sancara` | 3 | §8.4 R0/R3, §6.2, §9, §11 | **C-15, C-17 → R3 (FLIP)**; X-05 uncertain |
| `ka_kshetra` | 3 | §8.4 R3:860; §9:923; §19.6 | rung named, wrong column → M0 ✔ |
| `ka_muhurta_seva` | 3 | §8.4 R0/R3, §6.2, §9, §11 | **C-15, C-17 → R3 (FLIP)**; X-05 uncertain |
| `mi_abhilekha` | 2 | §1.5:311 zero-rows | no rung → M0 ✔ |
| `mi_seva` | 3 | §1.5:311 zero-rows | no rung → M0 ✔ |

`bo_laksana`, `bo_samskara`, `ga_sensitive`, `ga_strength`, `ka_kshetra` are the interesting
"agree, but only under the strict reading" cases: each **is** named in a rung clause, just not for
the column its failing rule is about. Under a loose asset-level reading of prong (b) all five would
flip. They stay M0-BLOCKED here only because D-30 says "IT", meaning the column.

## 6 — The §15 reading, considered and rejected (but it is a real ambiguity nobody has recorded)

The generated §15 block gives **every asset a `**rung:**` field, by name**. I extracted them
mechanically: **128 assets, 128 rung fields, and all 72 of D-57's identities have one.** e.g.
line 1147 `#### `bg_reference` …` / line 1152 `**domain:** shared · **rung:** R0 · **within-rung wave:** 0 …`.
§8.4 closes with: *"The regenerated workbook (§15) gives each asset its rung and within-rung
wave."*

On the most literal reading of "a plan clause that names THAT ASSET and assigns it to a later
rung", §15 satisfies prong (b) for all 109 pairs and the split is **0/109**. I reject that
reading for two reasons, and I want both on the record because D-57 never addresses §15 at all:

1. **The §15 rung is mechanically the layer.** I checked all 128: `rung` equals the layer→rung map
   for 127 of them, and the single exception (`lel_events`, L5 → R5) is still its layer's rung.
   Distribution R0=40, R1=19, R2=22, R3=23, R4=9, R5=15 — exactly §8.4's asset counts. It is a
   *layer* assignment wearing each asset's name, which is precisely the thing the task brief says
   is not the same as naming the asset.
2. **It assigns no column.** The §15 field says when the asset's *elevation* happens. It does not
   assign any registry-column repair anywhere, so it cannot satisfy a column-level prong (b) —
   and if it did, it would swallow §14.1's entire M0 scope row, which the plan plainly intends to
   be real work.

**This is nonetheless an unrecorded ambiguity in D-30's test**, and it is load-bearing: the test's
phrase "a more-specific plan clause" is doing all the work, and the plan contains a generated
per-asset surface that names every asset with a rung. I flag it rather than decide it.

## 7 — Two smaller findings

**FINDING 2 — "109 identities" is 109 *(rule × asset)* pairs over 72 distinct assets.** D-57's
prose says "the 109 identities" throughout, which reads as 109 assets. Summing `covers` across the
15 rules gives 109 pairs; `len(set(covers))` = 72. The partition is internally consistent
(`named ∪ blocked == covers` and `named ∩ blocked == ∅` for all 15 rules; `n == len(covers)` for
all 15 — I checked). No numbers change; the word does.

**FINDING 3 — `ga_prashna` is named in D-57 part 4 as one of the NAMED-LATER-RUNG identities but
contributes zero pairs.** D-57's ruling lists five assets — "`lel_events` (R5), `ka_gochara_sweep`
(R3), `ga_sade_sati` and `ga_prashna` (R1), `bg_ephemeris_engine` (R0)" — and the task brief
inherits that list. `ga_prashna` appears in **no** `covers` array in `corrected_grounds`. The 10
named pairs are carried by four assets only: `lel_events` ×6 (C-01, C-02, C-03, C-04, C-21, X-03),
`ka_gochara_sweep` ×2 (C-08, C-21), `ga_sade_sati` ×1 (C-04), `bg_ephemeris_engine` ×1 (X-05).
Harmless to the arithmetic; it does mean any reader auditing the 10 against that five-asset list
will not be able to make them reconcile.

## 8 — What I am unsure about — stated plainly

1. **Which reading of prong (b) is correct is not mine to settle.** Everything above turns on
   "IT" = the column. I read D-30's own text and its own worked examples (D-25 part 2(b)) as
   settling it, but D-57 applied a looser reading in at least two places
   (X-05/`bg_ephemeris_engine`, C-04/`ga_sade_sati`), so the ledger is not self-consistent on the
   point. If ADHIKĀRIN rules the loose reading correct, my two "flips to M0" reverse — and five
   more pairs (`bo_laksana`/C-11, `bo_samskara`/X-05, `ga_sensitive`/C-04, `ga_strength`/C-04,
   `ka_kshetra`/C-11, `ka_kshetra`/C-21, `ka_kshetra`/X-05) flip the other way. **Under no reading
   I can construct does the answer come out 99/10.**
2. **X-05 / `ka_graha_sancara` and X-05 / `ka_muhurta_seva` (2 pairs) — left as M0-BLOCKED, low
   confidence.** §11 says a domain-coherence failure on exactly these assets "is a registration
   defect resolved in the owning rung (R3 or R5)". A zero-consumer finding is arguably that kind
   of registration defect. Against: X-05's repair is a G1 disposition entry, which §14.1 names as
   M0's. I left them where D-57 put them, but I would not defend it hard.
3. **C-21 / `ka_gochara_sweep` — left as NAMED-R3, low confidence.** C-21 is
   `target_floor = 0 ⇒ volume_explanation NOT NULL`. §14.2 names the asset's "lifecycle exit",
   "zombie throughput rows" and "`data_disposition`" for R3 — it does not name
   `volume_explanation`. Whether "lifecycle exit" is broad enough is a judgment call. D-12 part 4
   may already settle it; I did not read D-12 in full.
4. **C-21 / `ka_gochara` and C-21, X-05 / `ka_gochara_v3_century_materialize` (3 pairs) — left as
   M0-BLOCKED, low confidence.** §8.4's R3 row assigns "the gochara transition executed per §5
   (v2 reclassified, F-52 rematerialization decided …)", and §5 identifies v2 as `ka_gochara`
   (line 456) and v3 as `ka_gochara_v3_century_materialize` (line 458). That is a two-hop
   name — the R3 row names a *role*, §5 binds the role to the asset. If two-hop counts, these
   move.
5. **C-02 / `lel_events` and C-03 / `lel_events` — I raised a doubt and then withdrew it.**
   `c02`/`c03` do not exempt `asset_kind='source'` (unlike `c01`, `c04`, `x03`, which do), so the
   R5 SOURCE reclassification does not mechanically clear them. But D-23 explains why they are
   still R5's: *"it held `lel_events`'s `layer_index` and `layer_name` NULL rather than guess,
   because the correct value is NULL-if-source but L5/Mīmāṃsā-if-data and is therefore not
   mechanically derivable."* The values are downstream of the R5 decision. D-57 is right; I record
   the doubt because the *rule implementations* do not show it and a future reader may re-raise it.
6. **I did not re-measure the 109.** D-57 says they were measured from the guard's own JSON and
   PARĪKṢAKA verified the covers content four ways (V-35). I took the 109 as given and tested only
   the split, which is what was asked. If the covers lists are wrong, so is everything above.
7. **I did not check whether `bg_gochara_citation_resolution` is named by "Phase 0.8a".** D-57 §6
   cites it; I confirmed only that no *later-rung* clause names the asset, which is the half prong
   (b) needs. Prong (a) for it is unverified by me.

## 9 — What I did not do

- Did not read, run, or reference `M0-T51`'s script or its output, at any point.
- Did not edit `asset_catalogue_disclosed_residuals.json` (M0-T55 is editing it concurrently).
  I read `check_asset_catalogue_contract.py` only, and only to learn each rule's assertion.
- Did not touch `main`, any asset, any registry row, any migration, or any `state/*.json*` other
  than appending my own completion line to `WORK_QUEUE.jsonl`.
- Did not certify anything. Everything above is an observation and a derivation. Whether the
  split should be amended, and whether the flip is affected, is ADHIKĀRIN's (G7/G9) — I note only
  that D-57 part 5 already reasons the practical outcome is identical either way, since every
  affected criterion is DEFERRED under D-24 part 3 as amended by D-39 regardless of *which* honest
  reason the `deferred_to` field carries. What changes is the truth of the record, which D-57
  itself calls "the only thing this campaign is for."

## 10 — Reproduction

```
# the narrative plan (excludes the generated §15 block)
awk 'NR<1138 || NR>3475 {printf "%d\t%s\n", NR, $0}' 00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md > narrative.txt
# per-identity, boundary-exact
grep -nE '(^|[^a-z0-9_])ka_graha_sancara([^a-z0-9_]|$)' narrative.txt
# the §15 rung fields
grep -nE '^\*\*domain:\*\*|\*\*rung:\*\* R[0-5]' 00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md | sed -n '1,5p'
# the rule assertions
sed -n '1432,1475p' platform/scripts/governance/check_asset_catalogue_contract.py
```

— KĀRAKA-M0-T54
