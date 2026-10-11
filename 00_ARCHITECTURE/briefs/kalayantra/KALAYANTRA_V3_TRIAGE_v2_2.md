---
artifact: KALAYANTRA_V3_TRIAGE_v2_2.md
content_version: 2.2
status: DRAFT — B-0b in progress. Classes (a) and the deferral candidates follow mechanically from the committed closure; the items marked NEEDS REVIEW and §5 (schema prerequisites) await the admitted schema receipt and the reviewed expected delta. No reduced count is claimed as accepted before that review.
authored_by: Claude Code (Opus 5.5, xhigh) — KĀLA-YANTRA v3 Planner, session local_ec1c912e-e039-4666-abc3-a815f9c4a2d1
plan: KALAYANTRA_RELAUNCH_PLAN_v2_2.md §0 steps 3–4
inputs:
  model: 00_ARCHITECTURE/control/kalayantra/plan_model.json (148 items; canonical sha256 fba94b41cc26c257c1cadd742e08812fa99b116675a82adb7d401c67cd6a1017)
  roots: 00_ARCHITECTURE/control/kalayantra/ACCEPTANCE_ROOTS_v2_1.json (canonical sha256 841eee4b3a192d4d99b5c8ed1266af2bde0b59fa9c5299462155dd63e695a844)
  closure: 00_ARCHITECTURE/control/kalayantra/CLOSURE_v2_1.json (file sha256 c98db3a06e5e38b107a6766d81be2833aae034c4c8585c1c134960b18bc5ce52; content hash 5d86f2bba1c848edba9f16c7638991ea87bab9d6aca718ce5825f49153989c21)
  live_status: tracker GET /api/state, version 60704, 2026-10-11T13:58Z; EVENTS.jsonl 12192 lines, sha256 0bc219bc10403e1b8bf0592149d60e1c3932e2626cb4f30f019c5950bc2e41c1
generator: scratch make_triage.py over the three inputs (deterministic; the table is not hand-edited)
---

# KĀLA-YANTRA v3 — triage of the 148 plan-model items

## 1. Result

| class | meaning | items | of which already done |
|---|---|--:|--:|
| (a) critical path | in the closure of acceptances (i)–(iii) | 125 | 40 |
| (a·close) | the mechanical close chain for acceptance (iv); regenerated from the retained set, not a scope root | 5 | 0 |
| (b) deferred | parked with a re-entry condition; never counted as closed | 8 | 0 |
| (c) dispositioned | inherited Pravāha material under the accepted J0_DISPOSITION | 2 | 0 |
| retired by decision | unfinished control-plane items, D-RETIRE-* (refusal staged, published only by B-2) | 2 | 0 |
| done, outside the closure | earned guarded completions and decisions; preserved, no action | 6 | 6 |
| **total** | | **148** | |

Open work on the critical path: **85 items** (62 waiting, 14 review, 5 parked, 4 ready), plus the 5-item close chain.
Source: `CLOSURE_v2_1.json` (`closure_count` 125, `outside_count` 23) joined to the live status named above.

Per acceptance (members overlap): (i) 122 · (ii) 49 · (iii) 123.

## 2. The plan's deferral candidates, examined

| candidate | in the closure? | conclusion |
|---|---|---|
| J-7 | no — consumed only by J-8a, JOIN-ALL | deferrable (b): the plan's first deferral candidate: optional Tier-2 Sudarśana, a candidate method outside the sealed '5.0' |
| J-7b | no — consumed only by J-8a, JOIN-ALL | deferrable (b): documentation-only L5 hand-off contract; no retained item consumes it |
| D-T2 | no — consumed only by J-7, JOIN-ALL | deferrable (b): decides only J-7's admission |
| L0-K | no — consumed only by D-T2, JOIN-ALL | deferrable (b): KP corpus ingestion feeds only D-T2's corpus count; blocked today on a missing ingestion path |

## 3. Skips can never satisfy an acceptance

The closure lists, per acceptance, every place where an item that accepts skipped inputs could absorb one.
If any of these inputs ends `not_applicable`, the acceptance above it is reported with that gap and the
campaign closes `CLOSED-PARTIAL`.

| acceptance | absorbing item ← skippable input (reason) |
|---|---|
| (i) | K9-5 ← K9-4b (input:K9-4a); K9-5 ← KR-1 (input:K9-6); K9-5 ← KR-2 (decision:D-KR=approved, input:K9-6); V-J6 ← J-6l (input:J-6); V-K3b ← K3-2 (input:J-5s); V-K5 ← D-G2 (decision:D-VC=approved, optional); V-K5 ← K5-2b (decision:D-COMPACT=approved, optional); V-K5 ← K5-3 (decision:D-G2=approved, input:D-G2, optional); V-K7 ← K7-4 (decision:D-R6=approved); V-K9 ← K9-6 (input:K9-4b); V-K9 ← KR-1 (input:K9-6); V-K9 ← KR-2 (decision:D-KR=approved, input:K9-6) |
| (ii) | V-J6 ← J-6l (input:J-6) |
| (iii) | K9-5 ← K9-4b (input:K9-4a); K9-5 ← KR-1 (input:K9-6); K9-5 ← KR-2 (decision:D-KR=approved, input:K9-6); V-J6 ← J-6l (input:J-6); V-K3b ← K3-2 (input:J-5s); V-K5 ← D-G2 (decision:D-VC=approved, optional); V-K5 ← K5-2b (decision:D-COMPACT=approved, optional); V-K5 ← K5-3 (decision:D-G2=approved, input:D-G2, optional); V-K7 ← K7-4 (decision:D-R6=approved) |

Roots that can themselves end `not_applicable` (the acceptance is then NOT MET, never silently met):
(i) K9-4a: decision:D-FLIP=approved, input:D-FLIP, input:J-6l, input:K9-23; (i) K9-4b: input:K9-4a; (i) K9-6: input:K9-4b; (ii) J-5q: input:J-4f; (ii) J-5s: input:J-5q; (ii) J-6: decision:D-FLIP=approved, input:D-FLIP; (ii) J-6l: input:J-6; (iii) K3-2: input:J-5s; (iii) K7-4: decision:D-R6=approved; (iii) K8-REG: input:K3-2, input:K7-4.

## 4. Outside the closure — each item's disposition

| item | live status | class | reason | re-entry / decision |
|---|---|---|---|---|
| L0-K | blocked | (b) | KP corpus ingestion feeds only D-T2's corpus count; blocked today on a missing ingestion path | re-entry: with D-T2 |
| J-7a | waiting | (b) | legacy ka_gochara writer retirement after the flip; charter §0 line 2 names it, the retained set (ii) names only the sealed flip — NEEDS REVIEW | re-entry: after J-6l's soak, before Suvarṇa certifies the ka_gochara lifecycle |
| D-T2 | waiting | (b) | decides only J-7's admission | re-entry: with J-7 |
| J-7 | waiting | (b) | the plan's first deferral candidate: optional Tier-2 Sudarśana, a candidate method outside the sealed '5.0' | re-entry: after the flip (J-6l) if D-T2 admits it |
| J-7b | waiting | (b) | documentation-only L5 hand-off contract; no retained item consumes it | re-entry: before L5 reads '5.0' |
| B-DB-BASELINE | parked | (b) | its content (registry-inclusive seed, the 1320 failure detected) moves into the Wave B slot-database packet (plan §5) | re-entry: if that packet's acceptance does not cover its four steps; PR #3284 then refreshed or closed |
| D-GOCHARA-TIMEOUT | waiting | (b) | rules one legacy materializer timeout; no retained item consumes it | re-entry: if J-4e/J-4f show that timeout binding |
| J-GOCHARA-TIMEOUT | waiting | (b) | applies D-GOCHARA-TIMEOUT; no retained item consumes it | re-entry: with D-GOCHARA-TIMEOUT |
| J-8a | waiting | (c) | records the disposition of every remaining Pravāha item under the accepted J0_DISPOSITION (J-0c → J-0); its dependencies J-7/J-7a/J-7b must be re-cut to J-0 + V-J6 when joins are regenerated — NEEDS REVIEW | per J0_DISPOSITION once J-0c is accepted |
| J-8 | waiting | (c) | Pravāha close report; follows J-8a | per J0_DISPOSITION once J-0c is accepted |
| B-CLAIM-RECOVERY | parked | retired | relaunch plan §0 step 4: its function is replaced by the v3 dispatcher and its terminal claim release | `D-RETIRE-B-CLAIM-RECOVERY` registered; `requires_outcome` approved; `refused` staged for B-2 |
| B-K-INBOX | running | retired | relaunch plan §0 step 4: its function is replaced by the v3 dispatcher and its terminal claim release | `D-RETIRE-B-K-INBOX` registered; `requires_outcome` approved; `refused` staged for B-2 |
| JOIN-ALL | waiting | (a·close) | acceptance (iv); regenerated from the retained set | — |
| C-1 | waiting | (a·close) | acceptance (iv); regenerated from the retained set | — |
| C-2 | waiting | (a·close) | acceptance (iv); regenerated from the retained set | — |
| C-3 | waiting | (a·close) | acceptance (iv); regenerated from the retained set | — |
| C-4 | waiting | (a·close) | acceptance (iv); regenerated from the retained set | — |
| B-8 | done | done·outside | earned; evidence preserved | — |
| D-R5 | done | done·outside | earned; evidence preserved | — |
| D-R9 | done | done·outside | earned; evidence preserved | — |
| B-6r | done | done·outside | earned; evidence preserved | — |
| B-DEPLOY-DIAG | done | done·outside | earned; evidence preserved | — |
| L0-K-RUNNER | done | done·outside | earned; evidence preserved | — |

## 5. Schema prerequisites (`KV3-SCHEMA-<n>`) — PENDING the admitted schema receipt

A missing required column is never a reason to defer its consumer (plan §0 step 3). One candidate is known
from the decision ledger; the full list is produced when the schema receipt is admitted (next B-0b step).

| id | consumer | missing column | evidence | state |
|---|---|---|---|---|
| KV3-SCHEMA-1 (candidate) | K-CERT | the stored verification-tier column that the citation-resolution density contract names | `run/DECISIONS.jsonl` KYD-150: "do not synthesize a verification tier … or select a column not evidenced in the table" | to confirm against the schema receipt; the live detector reports K-CERT's branch merged, which does not prove the column exists |

## 6. Every item

`class · id · owner · live status · brief citation (first pinned sections) — title`

- a · **B-0** · S · done · CHARTER frontmatter plan_documents; SUTRADHARA B-0 — Specifications present and hash-verified: the five plan documents in wt/campaign match the
- a · **B-4** · S · done · CHARTER §8 rule 6; SUTRADHARA B-4 — Campaign SESSION_OPEN (YAML session_open mapping, validator-clean) + CCD entry + coordinat
- a · **B-1a** · S · done · CHARTER §2.3, §4.1 — Tracker package and the Gochara campaign's unsaved material are on campaign/kalayantra: pr
- a · **B-1b** · S · done · CHARTER §4.1 (every row of the capability table), §4.2, §4.4; ASTRA charter review KY-02… — Control-plane generalisation, behind model declarations so the Pravāha model behaves ident
- a · **B-1c** · V · done · CHARTER §4.1 acceptance column; PARIKSAKA — Control-plane acceptance by PARĪKṢAKA: the acceptance cases run against both models on tem
- a · **B-5** · N · done · CHARTER §2.3 (a)–(f); ADHIKARIN bootstrap — Pravāha hand-over made real: no absorbed writer active (recorded); KY lanes registered in 
- a · **B-6** · S · done · CHARTER §7; fleet/README.md — Executor live (operator-started) and reading its operations table from main: capabilities 
- a · **B-1p** · S · done · CHARTER §6; SUTRADHARA B-1p — Bootstrap PR open and reviewable: ADHIKĀRIN's hand-over branch merged in, the branch curre
- a · **B-1v** · V · done · CHARTER §4.1 pre-B-2 bootstrap protocol, §10 item verdicts; PARIKSAKA — PARĪKṢAKA's verdict on the bootstrap PR at its exact head
- a · **B-1** · S · done · CHARTER §6; SUTRADHARA B-1 — Bootstrap PR campaign/kalayantra → main merged through the merge queue after PARĪKṢAKA's v
- a · **B-2** · S · done · CHARTER §4.1, §6; SUTRADHARA B-2 — Control plane reinstalled from the merged package: wt/campaign follows origin/main from he
- a · **B-3b** · S · done · CHARTER §6 CI/CD (1), §7 local databases; SUTRADHARA B-3b — Local rehearsal databases for every lane pass their assertions; precheck compared with the
- a · **B-3** · S · done · CHARTER §7; fleet/preflight.sh — Lane environments accepted: preflight in launch mode green; launch receipt carries the has
- a · **B-7** · S · done · CHARTER §3.3, §4.1 last paragraph; SUTRADHARA B-7 — Launch acceptance (join): every bootstrap item done, audit clean, PARĪKṢAKA's launch verdi
- done·outside · **B-8** · S · done · CHARTER §3.3; ASTRA charter review §4.12 step 10 — First earned progress observed (one exclusive claim → review → accepted verdict → merge); 
- done·outside · **D-R5** · N · done · SURROGATE §5 KYD-1; PLAN §12 R-5 — R-5: keep asset ids; additive versioned storage (KYD-1)
- a · **D-R6** · N · done · SURROGATE §5 KYD-2; PLAN §12 R-6 — R-6: wire the amended Tulana comparator into PRIORITY, or retire it (KYD-2)
- a · **D-R8** · N · done · SURROGATE §5 KYD-3; PLAN §12 R-8 — R-8: contested adapters — legacy computations preserved and qualified; a sourced variant a
- done·outside · **D-R9** · N · done · SURROGATE §5 KYD-4; PLAN §12 R-9 — R-9: century materializer hold retained until the successor proves coverage and refinement
- a · **D-R11** · N · done · SURROGATE §5 KYD-5; PLAN §12 R-11 — R-11: issued-forecast lifecycle in L5 beside Samīkṣā; L3 owns the registrar interface; the
- a · **D-KR** · N · done · PLAN §8 last row (brahmagyan/kala/*); CHARTER §2.2 — Legacy second writers: re-point the one importer of brahmagyan/kala (a read-only change in
- a · **K0a-0** · K · done · CHARTER §6 CI/CD (1), (7); .github/workflows/ci.yml jobs governance-gates (py-sidecar di… — The campaign's tests are really run by CI: a canary proves the required Governance Gates j
- a · **K0a-1a** · K · done · PLAN §3.2 rows vocab, ayanamsha, idempotency, ontology, resume; PLAN §7 Idem row — kala_core.vocab (canonical graha and system ids; typed lord and frame ids; null reasons; m
- a · **K0a-1b** · K · done · PLAN §3.2 rows vocab, ayanamsha, idempotency, ontology, resume; PLAN §7 Idem row — kala_core.idempotency — the three operation-specific helpers, each naming its table static
- a · **K0a-1c** · K · done · PLAN §3.2 rows vocab, ayanamsha, idempotency, ontology, resume; PLAN §7 Idem row — kala_core.ontology (one loader, one 27-class roster) and kala_core.resume (progress bound 
- a · **K0a-1** · K · done · PLAN §3.2 rows vocab, ayanamsha, idempotency, ontology, resume; PLAN §7 Idem row — JOIN — kala_core with real code: vocab (canonical graha and system ids; typed lord and fra
- a · **K0a-2** · K · done · ALGO 3.20 G1 (a)–(b) and defects (1)–(2); PLAN §9 K0a — G1 clock reference repair in Kṣetra: hazard lookup through kala_core.vocab, clock weights 
- a · **K0a-4** · K · done · PLAN §4.2 envelope; PLAN §4.3 read-model template — Assertion envelope (shared fields + the negative-space payload) and ONE assertion carried 
- a · **V-K0a** · V · ready · CHARTER §10 packet-exit reviews; PARIKSAKA — Packet exit K0a: Astra review run, structured verdict ACCEPTED with every BLOCKING finding
- a · **K0-SV** · K · done · CHARTER §1 native direction NR-KALA-DIRECTION-20261007, §15 item 8; PLAN §3.2 row clocks… — Suvarṇa alignment before Kāla code: (a) Suvarṇa's per-asset elevation template and certifi
- a · **K1-1a** · K · done · PLAN §3.2 row clocks; PLAN §3.1 daśā row — kala_core.clocks core: period_context, boundaries, hierarchy walk L1–L4, sandhi bands, the
- a · **K1-1b** · K · done · ALGO 3.1 (methods, applicability, σ); RULINGS NR-KALA-R13 (a) — Named daśā methods with applicability (Vimśottarī, Aṣṭottarī with its conditions, Yoginī, 
- a · **K2-1a** · K · done · PLAN §3.2 row promise; ALGO 3.3 — kala_core.promise graph: nodes, typed signed edges, frames, the event-class map from the s
- a · **K2-1b** · K · done · ALGO 3.3 (defeat/exception, effective state); RULINGS NR-KALA-R13 (b) — Cancellation as typed defeats/excepts edges with candidate vs effective conclusion state; 
- a · **K2-2** · K · done · ALGO 3.11; PLAN §8 row ka_gochara_resonance — Typed relationship resolver (ka_gochara_resonance folded into F1): frame resolved before r
- a · **K1-2** · K · done · ALGO 3.2; PLAN §4.1 row ka_avadhi — ka_avadhi as a read model over F2 and F1: period rows with σ, applicability, lord conditio
- a · **V-K12** · V · ready · CHARTER §10 — Packet exit K1+K2: Astra review, structured verdict ACCEPTED
- a · **K7-1b** · K · review · PLAN §5 change paragraph; REVIEW F-L19 — MCP facades become thin aliases of the registry capabilities; Vidhi bridge regenerated; th
- a · **K7-2** · K · review · REVIEW F-L2, F-L3; PLAN §5 rules — The two serving defects: STORY stale counts nulled with reason (F-L2); NOW era rows labell
- a · **K7-3** · K · review · PLAN §7 Dens row; PLAN §10 Serving — density_contract declared on the same capability entry that selects the tier column, for a
- a · **K7-4** · K · waiting · ALGO 3.10; PLAN §8 row ka_tulana — Tulana comparator (Pareto front, declared incomparability) wired into PRIORITY over jury D
- a · **V-K7** · V · waiting · CHARTER §10 — Packet exit K7 (serving): Astra review, structured verdict ACCEPTED
- a · **KA-2** · K · done · PLAN §3.2 row rules; PLAN §3.1 AV row — kala_core.rules: the rule-registry read model (paths, prerequisites in evaluation order, s
- a · **KA-3a** · K · waiting · ALGO 3.12; PLAN §3.2 row overlays — kala_core.overlays and the vedha adapter: ka_vedha_gochara serves vedha as intervals with 
- a · **KA-3b** · K · waiting · ALGO 3.13, 3.14, 3.15, 3.16 (adapter side); PLAN §8 rows for the four — The contested adapters carried honestly: ka_moorti_nirnaya (method_contested), ka_kota_cha
- a · **KA-4** · K · done · ALGO 3.17 (primitives); PLAN §3.2 row calendar — kala_core.calendar: pañcāṅga primitives with mandatory location, muhūrta scoring, one Tāra
- a · **KA-4b** · K · parked · ALGO 3.17 step 3; PLAN §9 row L0-M exit — Election view on scoped parihāra: reads `cancelled` with citation for in-scope undertaking
- a · **V-KA** · V · waiting · CHARTER §10 — Packet exit KA (adapters and services): Astra review, structured verdict ACCEPTED
- a · **K3-1** · K · parked · ALGO 3.4; RULINGS NR-KALA-R13 (b) — ka_vighnakara rewritten on fixtures: five axes stored separately, effective_state, release
- a · **V-K3** · V · ready · CHARTER §10 — Packet exit K3 (fixtures): Astra review, structured verdict ACCEPTED
- a · **K3-2** · K · waiting · PLAN §9 row K3 (fixtures until '5.0'); ALGO 3.4, 3.21 — Negative space wired to the real judge records of the sealed '5.0' generation (vedha state
- a · **V-K3b** · V · waiting · ASTRA charter review §4.11 — Packet exit K3 on real records: independent review before final K3 acceptance
- a · **K4-1** · K · done · PLAN §3.2 row measure; PLAN §6.2 item 5 — kala_core.measure: shared segment preparation and shift schedule; the jury's incremental-a
- a · **K4-2b** · K · review · PLAN §8 row ka_sangam; PLAN §8.1 concept-note dispositions — The jury's deletions, behind a compatibility shim: Modes A–D as row producers, the own eph
- a · **K4-3** · K · review · ALGO 3.19 (attachment); PLAN §3.2 row assertion (attach) — Canonical claim attachment (reading claims → jury assertions); no double credit
- a · **V-K4** · V · ready · CHARTER §10 — Packet exit K4: Astra review, structured verdict ACCEPTED
- a · **K5-G1a** · K · waiting · ALGO 3.20 G1 (c), (d), (e), (g) and defect (5); PLAN §8 row ka_kshetra — G1 (c)–(e), (g): suppression inputs wired from the adapters and negative space's effective
- a · **K5-G1b** · K · waiting · ALGO 3.20 G1 (f), null and uncertainty; PLAN §6.2 items 5, 8 — G1 (f) and the measurement side: insight detectors given working thresholds or removed; th
- a · **VC-1** · K · waiting · RULINGS NR-KALA-R12; PLAN §8.1 ruling 10 — Ablation pre-registration amended and FROZEN against the frozen G1 baseline before any res
- a · **VC-2** · K · waiting · RULINGS NR-KALA-R12; PLAN §9 row 7 — The three arms run on the lane database with the frozen G1 baseline; outputs committed ver
- a · **D-VC** · N · waiting · SURROGATE G3; RULINGS NR-KALA-R12 — Value checkpoint verdict per the frozen rubric (G3): approved = pass; refused = fail or a 
- a · **V-VC** · V · waiting · CHARTER §10 — Checkpoint review (Astra): the rubric was applied as frozen and the verdict follows from t
- a · **K5-2** · K · waiting · PLAN §6.2 item 4; ALGO 3.20 numerical contract — Compact evaluator trial under the numerical contract, including null-statistic reproductio
- a · **D-COMPACT** · N · waiting · SURROGATE G4; PLAN §6.2 item 4 — Admit the compact field as the stage's representation: approved only when every clause of 
- a · **K5-2b** · K · waiting · PLAN §4.1 row 6; PLAN §8.1 Kṣetra ruling 2 — Stage switched to the compact field (segments with coefficients, masks, ∫λ); dense rows re
- a · **D-G2** · N · waiting · SURROGATE G4; ALGO 3.20 G2 (event process, risk set, baseline units, graph features, coe… — Open a G2 (replacement model) brief or refuse (G4): approved only when D-VC supports it AN
- a · **K5-3** · K · waiting · ALGO 3.20 G2; PLAN §9 row 8 — The specified replacement model (G2): brief with every element present, then the implement
- a · **V-K5** · V · waiting · CHARTER §10; ASTRA charter review §4.11 — Packet exit K5: Astra review covering every applicable K5 child (a not_applicable child is
- a · **K6-4** · K · waiting · ALGO 3.9; PLAN §4.1 row ka_taranga — ka_taranga read model: per-event-class monthly integrals with units and risk set; a domain
- a · **K6-5a** · K · review · ALGO 3.8; PLAN §12 R-11 — The L5 issued-forecast lifecycle contract (the one permitted cross-layer item): table loca
- a · **K6-5** · K · review · ALGO 3.8; PLAN §4.1 row 8 — ka_bhavishya_lekha as the registrar: episode key + immutable issue key + delivery linkage;
- a · **V-K6** · V · waiting · CHARTER §10 — Packet exit K6: Astra review, structured verdict ACCEPTED
- a · **K8-R26** · K · review · PLAN §7; platform/scripts/governance/asset_census.py CRITERION_REGISTRY — Plan §7's gate table reconciled with the criterion registry revision live on main (26 sinc
- a · **K8-REG** · K · waiting · PLAN §9 row K8; PLAN §7 Build row — Registry-truth migration: depends_on equal to the tables actually read; has_substeps, coun
- a · **L0-M** · K · parked · ALGO 3.17 step 3 (the exact predicates and PG locators); PLAN §9 row L0-M — Scoped Muhūrta Cintāmaṇi parihāra extraction into bg_parihara_rules: scope ∈ {marriage, up
- b · **L0-K** · K · blocked · PLAN §9 row L0-K; ALGO 3.19 (G-K) — KP Reader V/VI local OCR ingested into the served corpus (classical_text_chunks) with the 
- a · **J-0** · K · waiting · CHARTER §2.3 (the twelve phases); /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pr… — JOIN — independently accepted inherited PR inventory, residual-state inventory, dispositio
- a · **J-0m** · S · waiting · CHARTER §4.2 (split before claim), §2.3; SUTRADHARA standing duty 3 — Plan model extended with the J children from J-0: one PR-sized child per inherited PR or r
- a · **J-1a** · K · waiting · /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/runbooks/SMALL_TEST_SITTING_… — Phase 1 — small-test prerequisites landed (and only those); the executor's small-test, tea
- a · **D-TEARDOWN** · N · waiting · SURROGATE G7, KYD-7; ASTRA charter review §4.10 — Small-test teardown capability (G7): approved only when the owner capability is present an
- a · **J-2a** · N · waiting · /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/runbooks/SMALL_TEST_SITTING_… — Phase 2 — small test run 1 dispatched (dry run first) on the canonical chart
- a · **J-2b** · N · waiting · SMALL_TEST_SITTING_CHECKLIST run 1 readback and teardown; V5_SMALLTEST_TEARDOWN_RUNBOOK — Phase 2 — run 1 read back, torn down, and its absence proven
- a · **J-2c** · N · waiting · SMALL_TEST_SITTING_CHECKLIST run 2 — Phase 3 — small test run 2 dispatched
- a · **J-2d** · N · waiting · SMALL_TEST_SITTING_CHECKLIST run 2 readback and final teardown — Phase 3 — run 2 read back, torn down, and its absence proven
- a · **J-3a** · K · waiting · /Users/Dev/kalayantra/wt/campaign/00_ARCHITECTURE/briefs/pravaha/decisions/MEASURING_BUI… — Phase 4 — measuring build, builder side landed on the measuring rules (PR 3194 lineage); m
- a · **J-3b** · K · waiting · MEASURING_BUILD_CONTRACT_v1_0; /Users/Dev/kalayantra/wt/campaign/00_ARCHITECTURE/briefs/… — Phase 4 — measuring build, verifier side landed (PR 3185 lineage)
- a · **J-3c** · N · waiting · MEASURING_BUILD_CONTRACT_v1_0 — Phase 5 — measuring build dispatched per the contract
- a · **J-3d** · N · waiting · MEASURING_BUILD_CONTRACT_v1_0 (readback, golden capture, report, teardown) — Phase 5 — measuring build read back, golden capture taken, report written, torn down
- a · **D-G9** · N · waiting · SURROGATE G5; MEASURING_BUILD_CONTRACT_v1_0 (horizon_basis) — What '5.0' answers after 2026-04-17: the derived horizon per the measuring-build contract,
- a · **J-4a** · K · waiting · /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/decisions/FINAL_BUILD_SCOPE_… — Phase 6 — final-build decisions resolved and the upstream release prerequisite met (the si
- a · **J-4p** · K · waiting · GOCHARA_DESIGN_SPECS_v1_4 §4.0 (the pin — amended here by the native's direction NR-KALA… — The hard daśā build pin (DASHA_READ_CONTRACT build 75524b3e in services/gochara_rules/perm
- a · **J-4b** · K · waiting · /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/runbooks/PROTECTED_WINDOW_RE… — Phase 7 — protected-window changes landed inside the window with independent readbacks (gr
- a · **J-4c** · K · waiting · FINAL_BUILD_SCOPE_v1_0; Gochara spec v1.4 + the delegated rulings of 2026-10-02 (frozen) — Phase 8 — final-rule builder and verifier changes landed with their equality and non-inter
- a · **J-4d** · K · waiting · FINAL_BUILD_SCOPE_v1_0 (density, residual, cap) — Phase 9 — final-rules candidate built on the lane database; density and residual decisions
- a · **D-CLOUD** · N · waiting · SURROGATE G5; PLAN §8.1 F-5 full century — Authorise the full century build of ka_gochara_v5 for the canonical chart on Cloud Run, ca
- a · **J-4e** · N · waiting · FINAL_BUILD_SCOPE_v1_0 — Phase 10 — full century build dispatched
- a · **J-4f** · N · waiting · CHARTER §5 long jobs; CHARTER §10 production gates — Phase 10 — full build observed to completion and read back (one inspection per cycle; nobo
- a · **J-5q** · K · waiting · /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/measurement/EVALUATION_PROTO… — Phase 10 — qualification: the A5.7 engineering gates and every co-primary endpoint of the 
- a · **J-5s** · N · waiting · ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0; PLAN §4.4 steps 3–4 — Phase 10 — independent verification job dispatched under the verifier principal; generatio
- a · **J-6a** · K · waiting · /Users/Dev/kalayantra/wt/campaign/00_ARCHITECTURE/briefs/pravaha/reviews/ASTRA_REVIEW_PR… — Phase 11 — serving reader for sealed generations live with the test-slice refusal (PR 3192
- a · **J-6m** · K · waiting · migration 1236 (kga_governed_generation_refused_ck); CLAUDE §N.4 (never edit an applied … — Phase 11 — the authority CHECK replacement migration (migration 1236 refuses a 5.x authori
- a · **J-6r** · K · waiting · PLAN §4.4 step 6; SURROGATE G6 (rollback rehearsal, previous-head retention) — Phase 11 — end-to-end reader, legacy-reader cutover and rollback acceptance rehearsed on t
- a · **D-FLIP** · N · waiting · SURROGATE G6; ASTRA charter review §4.10 — Flip the canonical chart to '5.0' (G6): approved for the exact sealed and independently ve
- a · **J-6** · N · waiting · SURROGATE G6, G8 — Phase 12 — the flip executed on the governed path (authority switch, previous head retaine
- a · **J-6l** · N · waiting · SURROGATE G6; CHARTER §10 production gates — Phase 12 — live readback (a served response answers from '5.0', identifying the deployed i
- a · **V-J6** · V · waiting · CHARTER §10 — Flip packet review (Astra): seal evidence, protocol run, reader behaviour, authority switc
- b · **J-7a** · K · waiting · /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/PRAVAHA_CAMPAIGN_PLAN_v1_0.m… — Phase 12 — legacy retirement (A6.2): ka_gochara's writer retired after the flip, lifecycle
- b · **D-T2** · N · waiting · SURROGATE G5; ALGO 3.16 — Tier-2 admissions in the enrichment order: Sudarśana as a judge method first; Tājaka and K
- b · **J-7** · K · waiting · ALGO 3.16; PLAN §8 row ka_sudarshana_varsha — Tier-2 — Sudarśana as a judge method: the full BPHS 74 method, the coincident-frame rule, 
- b · **J-7b** · K · waiting · /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/PRAVAHA_CAMPAIGN_PLAN_v1_0.m… — Phase 12 — the L5 hand-off (B6.2): what L5 reads from '5.0' and how, recorded as the contr
- c · **J-8a** · K · waiting · CHARTER §2.3, §14 — Every remaining Pravāha item dispositioned in its own tracker; the on-disk run material ar
- c · **J-8** · S · waiting · /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/PRAVAHA_CAMPAIGN_PLAN_v1_0.m… — Pravāha close report written (B6.3 lineage) and merged
- a · **K9-1** · K · waiting · PLAN §6.4; PLAN §4.1 — Rehearsal full-layer candidate build on the lane database in level order: candidate → stag
- a · **K9-4a** · N · waiting · PLAN §6.4; SURROGATE G8 — Production Kāla rebuild for the canonical chart dispatched through the orchestrator: lease
- a · **K9-4b** · N · waiting · PLAN §4.4 steps 3–5; CHARTER §10 production gates — Production rebuild read back per writer, verification job run, the new head published by c
- a · **K9-5** · K · waiting · PLAN §7; PLAN §9 row K8 exit — Rehearsal Suvarṇa census over the Kāla assets: the expected verdict per gate recorded, hon
- a · **K9-6** · K · waiting · CHARTER §0 line 3; PLAN §5 — Live acceptance: the seven views resolve through the registry and the Vidhi bridge against
- a · **KR-1** · K · waiting · PLAN §8 lower rows (gochara_grammar, gochara_intensity, kala_trigger, kala_permission, w… — Contract phase: code whose replacement is published is deleted — the Saṅgam compatibility 
- a · **KR-2** · K · waiting · PLAN §8 last row; D-KR — The legacy second writers retired: brahmagyan/kala modules that write the same tables as k
- a · **V-K9** · V · waiting · CHARTER §10 — Final packet review (Astra): the rebuilt layer against the plan's exit criteria
- a·close · **JOIN-ALL** · S · waiting · CHARTER §0, §14; ASTRA charter review KY-09 — Mandatory-results join: every item of the campaign is terminal (done, or not_applicable wi
- a·close · **C-1** · S · waiting · CHARTER §0, §14 — Close report: the five definition-of-done lines, each MET or NOT MET with its detector evi
- a·close · **C-2** · S · waiting · CHARTER §8 rule 6, §14; 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md — SESSION_CLOSE validated; SESSION_LOG entry; CURRENT_STATE §2; CCD closure row; one PR merg
- a·close · **C-3** · S · waiting · CHARTER §12; fleet/finalize.sh — Drain: every lane except v1 stopped, locks released, only clean worktrees removed — an acc
- a·close · **C-4** · V · waiting · CHARTER §0, §12, §14; PARIKSAKA final acceptance — Final acceptance and physical shutdown: v1's independent review of the five lines, then al
- done·outside · **B-6r** · K · done · NR-KALA-THROUGHPUT-20261007; run/DECISIONS.jsonl KYD-14; CHARTER §7, §8, §12; fleet/exec… — Executor automatically refreshes safely from merged main through its credential-bearing co
- retired · **B-CLAIM-RECOVERY** · K · parked · CHARTER §4.2 atomic claims and §8 rule 10; KYD-30; k1 NEW ITEM M20261007T111649-2f5b — Preserve original-owner checkpoint identity across released and expired claim recovery, in
- retired · **B-K-INBOX** · K · running · Existing NEW ITEM M20261007T142014-df98; logs/k3.26.log and unacked KYD33 messages M2026… — Worker role consumes current K directions before resume/claim work and persists with canon
- done·outside · **B-DEPLOY-DIAG** · S · done · KYD-41 and existing report M20261007T152037-00ff; run/adhikarin.cycle17.inspection.20261… — Establish K0a-1a deployment failure cause and owner; verify actual deployment contains its
- a · **J-0a** · K · done · CHARTER §2.3 (the twelve phases); /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pr… — Inventory every currently open pravaha/* PR exactly once
- a · **J-0b** · K · done · CHARTER §2.3 (the twelve phases); /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pr… — Inventory remaining Pravāha items, decisions and holds with their evidence
- a · **J-0c** · K · review · CHARTER §2.3 (the twelve phases); /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pr… — Assign evidence-backed dispositions and landing phases to the inherited inventories
- a · **J-0d** · K · waiting · CHARTER §2.3 (the twelve phases); /Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pr… — Map inherited changed files to current Kāla writer ownership and proposed shared-file wait
- done·outside · **L0-K-RUNNER** · K · done · KYD-46 and the one existing report M20261007T153231-1f7f; follow-up M20261007T154221-5ca… — Repair the existing KP V/VI ingestion runner so it imports, dry-runs and targets the serve
- b · **B-DB-BASELINE** · K · parked · KYD-47 existing report M20261007T153231-d330; follow-up M20261007T154221-65a8 is the sam… — Prepare the caller lane disposable DB from the governed current-main baseline and require 
- b · **D-GOCHARA-TIMEOUT** · N · waiting · KYD-68; original single report M20261007T183855-4b15; G5/G12 literal evidence and retain… — Rule the single materializer timeout from independently measured registry and completed-ru
- b · **J-GOCHARA-TIMEOUT** · K · waiting · KYD-68; existing single M20261007T183855-4b15; Actual asset_registry row ka_gochara_v3_c… — Update only the measured materializer writer timeout through an additive migration and ind
- a · **K0a-3** · K · done · PLAN §4.4 steps 1–6; PLAN §3.2 rows manifest, verify — Layer manifest: candidate and publication tables, open_candidate, candidate_generation, co
- a · **K7-1a** · K · review · PLAN §5; CLAUDE §N.6 — Seven retrieval-registry view composites, their shared response contract and registration
- a · **KA-1e** · K · done · PLAN §3.2 row sky; PLAN §3.1 ephemeris row — Gochara engine: ephemeris, events, geometry, contacts, coverage, api
- a · **KA-1w** · K · done · PLAN §3.2 row sky; PLAN §3.1 ephemeris row — Gochara facade and writer
- a · **K4-2aw** · K · review · ALGO 3.19; PLAN §3.2 rows assertion and measure — Convergence writer and qualification
- a · **K4-2a** · K · review · ALGO 3.19; PLAN §3.2 rows assertion and measure — Convergence core: schema, algebra, Jaimini, groups, agreement, contests
- a · **K6-123** · K · review · ALGO 3.5; RULINGS NR-KALA-R13 (c) — Kalasutra, kala_darshana and jivana_parva writers (three additive migrations, one PR)
- a · **K9-23** · K · waiting · PLAN §6.3; PLAN §6.1 (today's costs) — Publication tooling and the layer_verify/publish/rollback executor scripts
- a · **K-CERT** · K · parked · Suvarṇa FINAL/strict FIX_LIST: bg_gochara_citation_resolution Dens.served PARTIAL; CLAUD… — bg_gochara_citation_resolution Dens.served: the served select in platform-mcp/src/tools/re
- a · **K-CERT-2** · K · review · Suvarṇa SS N-443; PR #3055 (branch suvarna/land/TI-l0data-20-001, head 0dd4b6e59): the b… — bg_gochara_citation_resolution gets a registered, dispatchable WriterBase writer (ported f
- a · **K-AVADHI-C** · K · parked · Suvarṇa SS N-450 item (3); production asset_throughput ka_avadhi: state=error since 2026… — ka_avadhi builds clean on 482012f1: the post-write integrity check's conjunct (c) lord_con
