---
artifact: KALA_LAYER_PLAN_RECONCILIATION
canonical_id: KALA_LAYER_PLAN_RECONCILIATION
version: "1.0"
status: RECORD — the author's finding-by-finding reconciliation of ASTRA_REVIEW_KALA_LAYER_PLAN_v1_0 against the three reviewed documents; produces v1.1 of each. Authorises nothing. §7 updated 2026-10-06 with the native's three rulings (decisions/KALA_LAYER_NATIVE_RULINGS_v1_0.md).
produced_on: 2026-10-06
produced_in: 'Claude Code (Fable 5.1); same session as the three v1.0 documents and the Astra run (codex exec, gpt-6-astra, reasoning xhigh, read-only, 14:20–15:00 IST)'
reviewed_artifact: 'reviews/ASTRA_REVIEW_KALA_LAYER_PLAN_v1_0.md (verdict_overall REWORK; D1 PROCEED_WITH_AMENDMENTS, D2 REWORK, D3 REWORK)'
reconciles:
  D1: 'KALA_LAYER_VALUE_REVIEW_v1_0.md  sha256 ff74f7bb2638aaaaa9bb2662b332ec9025cae9f8d148a6115857244b57b5eec0 → v1.1'
  D2: 'KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_0.md  sha256 08784d5095df1d42b581c99aae0d2452151e04166eae23b56839551f061221b0 → v1.1'
  D3: 'KALA_ASSET_ALGORITHM_ELEVATIONS_v1_0.md  sha256 8128e5ff0583ae1d8ac2c55932817aa7ad72eea290302ad499a5bd3f509994e7 → v1.1'
v1_0_retention: 'the three v1.0 files are retained byte-identical as the artifacts the review hashed; v1.1 files supersede them in content and say so in their own frontmatter. No v1.0 frontmatter was edited, so the review hashes still verify.'
disposition_vocabulary: 'ACCEPTED (the finding is right; the change is made) · AMENDED (right in substance; the wording or scope is corrected, and the change made is narrower or different from the one proposed) · HELD (the finding routes to an owner who is not this session; the plan records the recommendation and waits) · REFUTED (the finding is wrong, with evidence). "Verified by" names who re-checked the evidence behind each disposition.'
---

# Kāla layer plan — reconciliation of Astra's review

**Written for:** the native (decision owner); then the sessions that will write the K-packet briefs.

## §0 · Outcome in one paragraph

Astra's direction stands and is adopted: judge → jury → forecaster is right; the implementation as written in v1.0 was not ready to build. Of its 25 findings, 24 are ACCEPTED or AMENDED and 1 is AMENDED-with-a-scope-split (KL25); none is REFUTED. Of its 18 confirmation-register corrections to my own findings, all 18 hold once the narrower scope is applied; four of my findings (F-A3, F-A4, F-A7, F-A12) were overstated and are reworded. Eleven doctrine locators Astra found in the local BPHS and KP OCR were independently confirmed line by line and are adopted into the corpus register with a new label `[D-local]`, distinct from the served corpus. The five Muhūrta Cintāmaṇi passages Astra could not see were re-pulled from the served corpus this session; their exact predicates now replace my prose summaries, and one of my attributions (a Venus rule on PG82 v.46) is withdrawn because the verse names Jupiter only. Eight items are HELD for the native (§7). The first packet to code changes from "K0 importable skeleton" to "K0a: a working vertical slice".

## §1 · Verification ledger — who re-checked what

Nothing in this record rests on Astra's word alone. Each class of claim was re-verified before disposition:

| Claim class | Re-verified by | Result |
|---|---|---|
| Kṣetra / Saṅgam / clock code (F-A1–F-A6, legacy aspects, muhūrta finder) | read-only sub-agent, 49 file reads at `cooperative-racer @ c751f3bd8` | 8/8 confirmed; two small location corrections (grammar file lives in `gochara_grammar/`, graha short codes are Title-case `Ju`) |
| Certification detectors (`asset_census.py`, `nikasha_certify.py`) | read-only sub-agent; checkout A (`cooperative-racer`) matches all line numbers; the suvarna-plan worktree has neither file | 6/9 confirmed, 3/9 partly (Null gate's second leg is the graders' `clean` flags, not a writer scan; Idem files parameterised table names as `{?}` → PARTIAL; registry has a fourth `NONE`, `Completeness.depth.dasha_link`) |
| BPHS / Jaimini / KP OCR locators | read-only sub-agent, 14 ranges | 9 exact, 5 partly (52.11–14 is the Sun-daśā / Moon-antardaśā instance, not a general rule; Jaimini 3473–3583 is Abhyankar's introduction, the Cara rule is 3537–3546; BPHS2 7078–7168 is Cara only, kendrādi/kāraka daśā sit at 7717–7877; Sudarśana's lowest level is 12½ ghaṭikā, not "day"; Yoginī's total 36 is implied, not stated) |
| Judge, serving plane, L4 consumers, orchestrator runner, null engine, ruling documents | the author, direct reads (two sub-agents were cut off by a usage limit; their items were done by hand) | all confirmed: `vedha_derive.py` states; `result_policy.py` manifest selection; judge loads pinned Vimśottarī (`load_pinned_vimshottari`, `make_period_rows_for`); R9-6.1 builder self-check vs separate verification job; `date_resolver.py:497–499` primary survives cap; Jivana "Deliberately NOT lowering"; `ga_strength_writer.py:1218–1226` legacy HOUSE label is sign-indexed; `asset_runner.py` delta-skip + `output_changed`; `staleness.py` BFS; `dhara_null.py` 1023 shifts; `hazard.py` `log1p(−ρu)` term; W2 §5.2 refinement τ = 0.02 nats; B8-6, B8-7, ruling 10, AM-21 part 4, `NR-VIPAREETA-20261002` verbatim; Vidhi bridge `unmapped = 29`; `query_activation_waveform.ts` reads `kala_taranga`; Bhavishya reads `phala_anchors` to protect referenced ids |
| Muhūrta Cintāmaṇi predicates (`UNVERIFIABLE_HERE` for Astra) | the author, served-corpus search this session (`classical_text_search`, 5 queries) | PG110 v.68, PG115–116 v.88, PG116 vv.89–91, PG26 v.34 ṭīkā, PG67 v.13, PG82 v.46 retrieved with chapter headings; exact predicates quoted in D3 v1.1 §3.17; **PG82 v.46 names Jupiter only** (boy's upanayana, girl's marriage) — my "Śukra-bala from PG82" is withdrawn |

## §2 · Findings KL01–KL25

| ID | Disposition | Verified by | What changes (document · section) |
|---|---|---|---|
| KL01 replacement field model unspecified | **ACCEPTED** | author (D3:423–429 re-read; `hazard.py:269–374`) | D3 §3.20 rewritten as two generations: G1 = the existing model with its five defects repaired and nothing else changed (so the ablation measures the model that was designed); G2 = a replacement admitted only after K5's brief specifies event process, risk set, baseline units, graph features, coefficients, suppression operator and unavailable-input behaviour. D2 §6.2 item 4, §9 K5 |
| KL02 publication cycle | **ACCEPTED** | author (D2:224–229, 275) | D2 new §4.4: candidate generation pinned at run start; every stage and read model reads the candidate by `build_id`; completeness + verification precede one publication operation; `manifest.current_generation` in the template becomes `manifest.candidate_generation(ctx)`. §2.2 manifest row, §6.4 |
| KL03 daśā conflation | **ACCEPTED** | OCR sub-agent (Cara at BPHS2 7078–7168; kendrādi/kāraka at 7717–7877; Abhyankar 3537–3546); author (D3:89–95; my own §2 said PG198 is the kāraka daśā) | D3 §3.1 rewritten: Cara, kāraka-kendrādi and Mūla are three named methods; Sārāvalī PG155 is Mūla daśā, not a Vimśottarī start variant; the Cara fixture uses Mars in Capricorn (exalted) and Mars in Cancer (debilitated) with the counting convention pinned; competence classes become descriptive tags; Kālacakra covers wealth, education, family (46.131–134) |
| KL04 cancellation ≠ sign − | **ACCEPTED** | author (D3:131, 141, 155) | D3 §3.3: typed `defeats(rule_conclusion)` and `excepts` edges; candidate and effective states stored separately; §3.4 effective state exposed |
| KL05 negative space reads downstream rate; F1 edge missing | **ACCEPTED** | author (D3:154–155; D2:191) | `measured_lower_rate` leaves the producer and becomes a post-forecaster read model; D2 §4.1 row 4 Reads gains F1 |
| KL06 Kalasutra universal daśā gate | **ACCEPTED** | author (AM-21 part 4 verbatim: PD = testimony, never scored-path member) | D3 §3.5: intervals keep the judge's own period anchor; "lord's period concurrent" is an annotation, never a filter; recurrence ladder from the complete contact inventory with ordinals and coverage |
| KL07 Taranga domain transform undefined | **ACCEPTED** | author (W2 §5.1 is per event class) | D3 §3.9: class integrals served; a declared class→domain table with overlap rule is the only route to a domain figure; counts separate |
| KL08 knot set insufficient; sampled byte-equality is not proof | **ACCEPTED** | author (`hazard.py:364–374` `log1p(−ρu)`; W2 §5.2 adaptive refinement τ = 0.02 nats, depth 6; `stage4_field.py:880–896`) | D2 §6.2 item 4 and §10: operator-complete knot set (envelope rise/plateau/fall, max-envelope switching roots, `min(Moon, Lagna)` crossings, clock and scenario boundaries, mask edges, horizon seams, refinement); acceptance = structural equality of partitions + per-segment bound + one-sided evaluation at discontinuities + adversarial fixtures + null-statistic reproduction |
| KL09 one null ≠ one estimand | **ACCEPTED** | author (W2 §5.5; `dhara_null.py:166–175`) | D2 §6.2 items 5/7a: shared preparation and shift schedule; separate estimands and conditioning for jury `D(W)`, whole-pipeline selection, class field maxima; denominator stated as shifts + observation (1,023 + 1) |
| KL10 universal `replace_partition` | **ACCEPTED** | detector sub-agent (Idem: append-only INSERT = FAIL; dynamic name = PARTIAL) | D2 §3.2 `idempotency/` split into `replace_candidate_partition`, `insert_immutable_checked`, `publish_head`; §7 Idem row says the registrar needs a reviewed detector rule, not a delete |
| KL11 "verification substep, the judge's pattern" | **ACCEPTED** | author (`ka_gochara_v5.py:774–776`, R9-6.1) | D2 §1 principle 8 and §7 Earn: builder self-check (reported) + separately dispatched verification job under the verifier principal |
| KL12 three-lineage invalidation not automatic | **AMENDED** | author (`asset_runner.py:1138–1154` delta-skip; `:1390–1416` `output_changed`; `staleness.py:21–45, 93–101`) | D2 §6.2 item 3: the runner gives whole-asset skip on receipt-visible inputs and transitive propagation on `output_changed`; grain reuse is the writer's own decision from its recorded input vector; no finer scheduling is claimed; §13 Q1 answered |
| KL13 "retire own geometry" overstates F-2 vs B8-6 | **ACCEPTED** | author (B8-6 verbatim) | D2 §8.1 Kṣetra fold and the "what the fold changes" paragraph; D3 §3.20: internal continuous knots kept; transit cited as evidence consumes the judge by `window_ref` only |
| KL14 vedha cards disagree | **ACCEPTED** | author (`vedha_derive.py` docstring; `NR-VIPAREETA-20261002`) | D3 §3.4 inputs = judge states {active, inactive, unqualified} + coverage; §3.12 contract: `unqualified` reasons `node_obstruction_undecided` / `obstructor_residence_unknown`; Moon scope `excluding_on_demand_moon_obstruction`; node + cited obstructor → `active`; viparīta not emitted at all (ruled), disclosure retained; Sarvatobhadra = `information_unavailable` |
| KL15 "uncancelled" vs unassessed; marriage scope | **ACCEPTED** | author (served corpus: vv.88–91 sit under "in marriage" headings; PG109 v.65 ṭīkā says the vivāha chapter's doṣa reckoning is chapter-specific) | D3 §3.17: `cancellation_unassessed` until the applicable rules are evaluated; parihāra scoped to marriage (and upanayana where the verse says so) until a general-scope clause is found |
| KL16 Śukra-bala from a Guru passage; combustion replaced | **ACCEPTED** | author (PG82 v.46 retrieved: Jupiter only) | D3 §3.17 item 5: Guru-bala only; combustion kept as its own factor; sign-phase rules (PG70 vv.17, 19) added as separate factors; §2 register row corrected |
| KL17 event identity ≠ issue identity | **ACCEPTED** | author (D3:219–221) | D3 §3.8: episode key + immutable issue/version key + delivery linkage; a generated candidate is not an issued forecast; original statements preserved |
| KL18 certification mechanisms ≠ detectors | **ACCEPTED** | detector sub-agent (all nine rows) | D2 §7 rewritten against the inspected detectors at registry revision 25: expected verdict per gate stated as PASS / measured N/A / PARTIAL / NO_DETECTOR; `single_derivation` removed; Narr fidelity capped at PARTIAL; Dens revision 6; Carr D2/D3 and Earn.service_state NO_DETECTOR; Null is AND |
| KL19 two oracles encode false conclusions | **ACCEPTED** | author (D3:207, 247) | D3 §3.7 condition-aware diff; §3.10 unavailable evidence → incomparability |
| KL20 Sudarśana still tautology-prone | **ACCEPTED** | OCR sub-agent (BPHS2 43255–43381, 43867–43946) | D3 §3.16: full method — three frames, benefic/malefic occupancy and aspect, strength tie-break, coincident-frame rule (two or three of Lagna/Moon/Sun in one rāśi → judge from the birth chart only), nested year / month / 2½ days / 12½ ghaṭikā, commencement conditions; conclusions compared, never offsets |
| KL21 duplication counts mixed units | **ACCEPTED** | code sub-agent (`legacy_semantics.py:9–17` is a DB-free reference implementation) | D2 §3.1 re-headed as an operation inventory; counts labelled as buckets; legitimate variants listed (independent verifiers, continuous knots vs served verdicts, point roots vs interior extrema, Parāśari / Jaimini / Tājika configurations, legacy comparison arms, method-specific conventions) |
| KL22 four "Today" source errors | **ACCEPTED** | author (`date_resolver.py:474–499`; Jivana `:385–387`; `ga_strength_writer.py:1218–1226`; judge `:472, 694–704`) | D3 §3.5 Today, §3.7 Defects, §3.19 Today, §3.21 bullet 5 corrected |
| KL23 B8-7 misfiled; E0 not discharged | **ACCEPTED** | author (B8-7 verbatim: activity / applicability / availability / valence alias map; valence NULL `class_polarity_not_declared_upstream`) | D2 §8.1 rows for B8-7 and ruling 6; E0 = with/without-obstruction model contrast, non-causal |
| KL24 vacuous K0, K5 before ablation, timeout unmeasured | **ACCEPTED** | author (ruling 10 verbatim: three arms before S1 ingestion) | D2 §9 re-sequenced: K0a vertical slice → K1 ∥ K2 → K7 narrow → K3 → K4 → value checkpoint → K5 → K6 → K8 incremental → K9 |
| KL25 F-L19–F-L22 overstated | **AMENDED** | author (bridge `unmapped = 29`; `query_activation_waveform.ts` reads `kala_taranga`; Bhavishya `:271` protects referenced ids) | D1 §0 and F-L19–F-L22 reworded by reach (registry / MCP facade / web floor); F-L22's "one-line correction" withdrawn for Bhavishya; the registered-capability reach of Taranga recorded |

## §3 · Confirmation register — my findings as corrected

| Mine | Astra | Disposition | Correction made |
|---|---|---|---|
| F-A1 clock term zero | [C] static; [U] every stored generation | ACCEPTED | wording: "in this implementation"; graha short codes are Title-case `Ju`; sign-period lords (Cara stores sign names) need typed handling, planet normalisation alone is not the repair |
| F-A2 no obstructive primitive built | [C]; builders exist, uncalled | ACCEPTED | wording: "never called from the production assembly" |
| F-A3 weights never match | [R] as worded | **AMENDED** | Vimśottarī, Yoginī, Kālacakra, Mudda keys match; `w_s:chara` ≠ `chara_karaka`; Aṣṭottarī and `vimshottari_kp` unseeded. A missing KP weight is not authority to give KP independent weight |
| F-A4 every contact at 0° Aries | [C] A/B/TRIGGER; [R] "every" | AMENDED | scope: Modes A, B and TRIGGER default `target_longitude_deg = 0.0`; Mode C sign-based with Aries-lagna constants; Mode D's first-predicate guard defeated by per-predicate lifetime substeps |
| F-A5 agreement = identical dates | [C] formula; [U] live distribution | ACCEPTED | the all-one distribution stays my measurement, labelled [L] |
| F-A6 severe unreachable; no veto | [C] | ACCEPTED | — |
| F-A7 two vedha definitions | [C] divergence; [R] "judge ignores nodes" shorthand; viparīta exclusion is a ruling | **AMENDED** | the judge's node-only state is `unqualified`; a cited obstructor alongside a node is `active`; viparīta is excluded by `NR-VIPAREETA-20261002`, not by omission |
| F-A8 MC cancellation verses present, never extracted | [U] for Astra | **ACCEPTED as scoped**: the verses are in the served corpus (re-retrieved this session with headings); "60 rows all natal" is my [L] count; Astra's inability to see the served corpus is recorded, not a refutation | exact predicates now in D3 §3.17 |
| F-A9 resonance frame join | [C] | ACCEPTED | fix is to resolve frame before rule matching, not to relabel |
| F-A10 epoch mismatch | [C]; one label does not close it | ACCEPTED | sky contract carries instant, backend, flags, node model |
| F-A11 today() defaults | [C] defaults; [U] historical invocations | ACCEPTED | requirement restated as "pinned `as_of` required", not "every build used wall-clock" |
| F-A12 judge stores no numbers; literals pinned | [C] default policy; [R] literals | **AMENDED** | result policy is manifest-selected (`all_null_candidate/1` default); the registered writer loads pinned L1 Vimśottarī; "pinned as literals" was true of a reference module, not the writer |
| F-A13 Tulana unused | [C] | ACCEPTED | "top-750 is 100 % Mode C" stays an attributed observation |
| F-A14 Sudarśana constant | [C] | ACCEPTED | — |
| F-L19 unreachable from both doors | [C] named gaps; [R] universal | AMENDED | reach stated in three layers |
| F-L20 Tulana never called | [C] | ACCEPTED | bounded to the searched callers |
| F-L21 Taranga unreachable | [C] gap; [R] blanket | AMENDED | registry capability reads the table; no MCP facade; Vidhi primitive misrouted |
| F-L22 dead inputs; one-line fixes | [C] defects; [R] ease | AMENDED | Bhavishya's L4 read protects referenced outcomes; replace with a reference-protection contract, never delete bare |

## §4 · Card judgments (B1) — dispositions

| Card | Astra | Disposition | Where |
|---|---|---|---|
| 3.1 Daśā Kāla | Rework | ACCEPTED | §3.1 rewritten (methods separated; tags; fixtures; perturbation tests) |
| 3.2 Avadhi | Proceed with amendments | ACCEPTED | depends on F1 and F2; lord-condition oracle |
| 3.3 Yojaka | Rework cancellation; retain source architecture | ACCEPTED | typed defeat edges; two routes (admitted / proposed interpretive) |
| 3.4 Vighnakara | Rework | ACCEPTED | effective-state algebra; six-value vocabulary derived; release may be unknown; no downstream input |
| 3.5 Kalasutra | Rework | ACCEPTED | path-specific; annotation not gate |
| 3.6 Darshana | Proceed with amendments | ACCEPTED | contextual rows; unknown intervals visible |
| 3.7 Jivana Parva | Proceed with amendments | ACCEPTED | condition-aware diff; Today corrected |
| 3.8 Bhavishya | Rework identity and issuance | ACCEPTED | identity split; issuance ≠ generation; L4 read → protection contract; table location routed (R-11) |
| 3.9 Taranga | Rework domain transform | ACCEPTED | class integrals; declared mapping |
| 3.10 Tulana | Proceed with amendments | ACCEPTED | incomparability; policy vs evidence |
| 3.11 Resonance | Proceed with amendments | ACCEPTED | frame before rule |
| 3.12 Vedha | Proceed after reconciliation | ACCEPTED | contract reconciled to the judge + later rulings |
| 3.13 Mūrti | Amend | ACCEPTED | legacy preserved and qualified; second convention only with a source |
| 3.14 Koṭa | Amend | ACCEPTED | direction null until path geometry sourced |
| 3.15 Tithi Praveśa | Amend substantially | ACCEPTED | legacy named; variant needs a cited definition before computation |
| 3.16 Sudarśana | Proceed with fuller method | ACCEPTED | BPHS 74 method; anchor convention declared [U] |
| 3.17 Muhūrta | Proceed after scoped extraction and interval redesign | ACCEPTED | exact predicates; scope; boundaries; factors separated |
| 3.18 Graha Sañcāra | Proceed | ACCEPTED | contract elements added |
| 3.19 Saṅgam | Proceed after contracts preserved | ACCEPTED | SAV correction; ancestry; no independence claim |
| 3.20 Kṣetra | Rework before implementation | ACCEPTED | G1/G2 staging; knots kept; null experiment stated; ablation amended first |
| 3.21 Judge | Observations to Pravāha | ACCEPTED | corrections: pinned periods, manifest policy, verifier separation, later rulings |

## §5 · Routed decisions and question sets

**D2 §12 R-1…R-10** — Astra's technical recommendations are adopted into v1.1 as the plan's position; the reserved decisions stay with their owners (§7 below). R-1 adopt (import pure kernel APIs; verifiers stay independent; no reverse imports). R-2 **first slice needs no new id** — judge-owned substrate tables; a shared row only on measured need. R-3 field-by-field parity + steward amendment. R-4 adopt. R-5 additive versioned storage, not semantic replacement under old columns. R-6 recommendation: wire the amended comparator; native rules. R-7 one owner per logical producer. R-8 do not serve two computations as coequal traditions. R-9 retain the hold. R-10 no new approval layer.

**D2 §13 Q1–Q9** answered in D2 v1.1 §13 with Astra's recommendation and the author's adoption. **D3 §6 Q1–Q7** answered in D3 v1.1 §6.

## §6 · Doctrine adopted from the local OCR (`[D-local]`)

Each confirmed by the OCR sub-agent at the stated lines of `00_ARCHITECTURE/SOURCE_DATA/classical_texts/{BPHS,KP,Jaimini_Sutram}`; these files are **not** the served `classical_text_chunks` corpus (15–16 texts), so the label is distinct from `[D]`:

Aṣṭottarī conditions (46.17–20, 23; BPHS2 3256–3272, 3595–3598) · Yoginī construction (46.195–199; 8600–8619) · Kālacakra results breadth (46.131–134; 6850–6881) · antardaśā lord relative to daśā lord, shown by the Sun-daśā/Moon-AD instance (52.11–14; 12013–12034) · commencement and fruition phase (47.3–6; 8939–8977) · Sudarśana method (74.5–26; 43255–43381, 43867–43946) · Argalā and virodha (31.2–9; BPHS1 24310–24335) · bādhaka for movable signs (ch.50 vv.20–21; 10412–10454) · transit exception by running daśā (70.12–14; 40952–40970) · piṇḍa timing (70.24–27, 30–33; 41248–41260, 41537–41558) · KP star-lord / sub-lord rule (KP Reader V; `kp_reader_vol5_djvu.txt` 2215–2249) · viparīta vedha as Santhanam's note, not a verse (BPHS1 24418–24442; ruled not used).

**Correction to my own non-claim:** KP text does exist locally (KP Reader V and VI OCR); it is not in the served corpus. KP admission stays corpus-gated (D-T2) until ingestion; the local text makes the ingestion a bounded L0 task.

## §7 · HELD for the native — status after the native's rulings of 2026-10-06

The native ruled on items 1, 2 and 8 in-session ("I approve both."); the rulings are recorded with ids in `decisions/KALA_LAYER_NATIVE_RULINGS_v1_0.md`. Items 3–7 remain held.

1. **RULED `NR-KALA-R13-20261006`** — the four semantic corrections (distinct daśā constructions; effective cancellation states; path-specific period gating; separate field and null estimands) are doctrine for every K-packet.
2. **RULED `NR-KALA-R2-20261006`** — no new registry id in the first slice; a shared sky row only later, on measured need, through Suvarṇa and Pravāha.
3. **R-5** — asset ids kept; storage additive and versioned (lifecycle disposition is Suvarṇa's + native's).
4. **R-6** — wire the amended Tulana comparator into PRIORITY, or retire the service (product ruling).
5. **R-8** — mūrti and tithi-praveśa: preserve the legacy computation with qualified status; admit a sourced variant only separately (doctrinal admission).
6. **R-9** — retain the century hold until the successor proves coverage and refinement semantics.
7. **R-11 (new)** — the issued-forecast table lives in L5 beside Samīkṣā with L3 as registrar interface (cross-layer).
8. **RULED `NR-KALA-R12-20261006`** — the amended ablation runs on the minimally repaired G1 field before any forecaster G2 spend; a park outcome parks G2, not the G1 repair.

## §8 · What changed per document (summary; details in each v1.1 changelog)

- **D1 → v1.1:** §0 reach sentence; F-L19, F-L21, F-L22 reworded; F-L22 Bhavishya correction; companion pointers; no disposition changed.
- **D2 → v1.1:** §0 rulings list; §1 principles 3, 5, 7, 8; §2.2 negative space / manifest rows; §3.1 re-headed; §3.2 `assertion`, `idempotency`, `manifest`, `verify`, `measure` rows; §4.1 rows 0, 4, 8; §4.3 template; new §4.4 candidate→publication; §5 reach layers; §6.2 items 3, 4, 5, 6, 7, 7a; §6.3 measures; §7 rewritten; §8 Kṣetra and Bhavishya rows; §8.1 B8-6, B8-7, ruling 6, AM-21 rows and the closing paragraph; §9 re-sequenced; §10 oracles; §11 two risks added; §12 R-1…R-12 with recommendations; §13 answered.
- **D3 → v1.1:** §0 labels; §2 register (12 rows upgraded or corrected, `[D-local]` introduced, KP non-claim corrected); cards 3.1, 3.3, 3.4, 3.5, 3.7, 3.8, 3.9, 3.10, 3.12, 3.13, 3.14, 3.15, 3.16, 3.17, 3.19, 3.20, 3.21 rewritten in part or whole; 3.2, 3.6, 3.11, 3.18 amended; §4 F-A3, F-A4, F-A7, F-A8, F-A12 reworded; §5 packet map re-keyed to the new order; §6 answered; §7 non-claims corrected.

## §9 · Hashes

v1.0 (unchanged, as hashed by the review): see frontmatter; re-verified byte-identical after this session's writes. Each v1.1 file names its predecessor's hash in its own `supersedes` field. The v1.1 files as produced by this session:

```text
57d528320b5ee1b514d442a129f699b3fae0a166bb4e4651cbb6325ccde483bc  KALA_LAYER_VALUE_REVIEW_v1_1.md
85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef  KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md
ec382daa61eed5fde19bc4d9e8bca45719ab5b82de878c4c1e8893bd52524569  KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md
3f659b9bf9c7b4a7e4d26e2dfc786e7047b7272fe9342c1a16942dc419f888d6  reviews/ASTRA_REVIEW_KALA_LAYER_PLAN_v1_0.md
```

`SESSION_LOG` carries the canonical copy at close; a later edit to any v1.1 file is a new version, not a silent mutation (B.8).
