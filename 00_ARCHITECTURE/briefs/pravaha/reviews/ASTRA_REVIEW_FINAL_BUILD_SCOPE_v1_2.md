VERDICT: NOT_READY

**As a final sealed-build specification, v1.2 remains internally inconsistent and contains requirements that cannot pass against `origin/main`. It is also not yet precise enough to authorize the measuring build after the small test.** Several outside findings are genuinely repaired, but naming an unresolved dependency—or putting a decision in the “open” table—does not resolve contradictory operative clauses.

I reviewed document HEAD `f1f2657627cd131d068a4eac031de86d3c0c7371` against local `origin/main` at `091362f315a2d2f7e9c44cc205aac54440c8f6a9`. No files, database, or network were touched.

References below:

- **F** = [FINAL_BUILD_SCOPE_v1_0.md, version 1.2](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-fbs/00_ARCHITECTURE/briefs/pravaha/decisions/FINAL_BUILD_SCOPE_v1_0.md).
- **Review** = [FABLE_REVIEW_FINAL_BUILD_SCOPE_v1_1.md](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-fbs/00_ARCHITECTURE/briefs/pravaha/reviews/FABLE_REVIEW_FINAL_BUILD_SCOPE_v1_1.md).
- Other document paths are relative to `00_ARCHITECTURE/briefs/pravaha/`.
- Code references are **at `origin/main`**. **K/** means `platform/python-sidecar/services/gochara_kernel/`; **R/** means `platform/python-sidecar/services/gochara_rules/`; **W** means `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py`; **M/** means `platform/migrations/`.

**P1 findings**

**P1-1 — Open owner decisions remain executable instructions.**  
FB-1/3/5, FB-41/48, FB-53/54 and FB-66 contain operative choices while §12b labels those same choices open. Examples include the general horizon narrowings, future-window serving, the scored-horizon density denominator, a mandatory final-rules candidate unless waived, and a named refusal for pre-1998 questions. §11.6 additionally permits an all-null seal before the result-policy decision.

This does not make either conditional branch implementable as *the final build*. An implementer must choose which conflicting instruction controls. The complete inventory appears below. **Evidence:** F:63–78,160,170,204–205,242–252,256–258,282.

**P1-2 — FB-2’s pinned horizon evidence cannot support its promised independent replay.**  
The detector consumes interval starts, parent links, birth classification and the competing dated events. The stored basis contains one event plus a digest of `(id,date,date_confidence,shape)` for the consumed rows. A digest cannot reconstruct those rows or prove that the chosen event was the earliest eligible event. Parent links and interval starts are not explicitly preserved.

FB-55 then describes a different input vocabulary—`date`, `precision`, `is_birth`—and leaves its mapping to the real schema unconfirmed. The schema has `event_date`, `category`, `shape`, `date_confidence`, interval fields and parent links; it does not provide the stated birth “type” or `is_birth` field. Chain-root confidence and interval-root handling also remain unspecified.

**Consequence:** a verifier can confirm the author’s selected answer, but cannot independently re-derive the selection after the live log changes. A malformed interval or differently classified birth row can change the build horizon.

**Evidence:** FB-1/2/55, F:64–69,260; M/`001_baseline.sql`:463–474; M/`457_lel_schema_v2_event_shapes.sql`:19–45.

**P1-3 — FB-57’s generation mechanism does not work through the production caller.**  
The clause assumes the frozen orchestrator will pass `ctx.config["generation"]`. It does not:

`platform/python-sidecar/pipeline/orchestrator/asset_runner.py:1119–1122` constructs config containing only `chart_id` and `birth_params`.

The same config participates in the pre-execution skip check at `asset_runner.py:1144–1155`. W:141 still hardcodes `GENERATION = "5.0"`.

**Consequence:** the proposed mechanism cannot create the required later generations through the documented production route. “Stream A confirms” is already answered negatively by the nominated baseline; the specification needs a concrete compatible transport and receipt/skip behavior.

**Evidence:** FB-57, F:264; FB-8/41/66, F:84,160,282; code above.

**P1-4 — The version-selection and census rules are inconsistent.**  
FB-30 leaves 1.1.0 unbound and selects 1.2.0 only for nine classes. FB-32 nevertheless demands accounting for every “bound-or-registered” version, including 1.1.0, and describes a universal `1.0.0 → 1.1.0 → 1.2.0` chain despite no P1@1.1.0.

The database requires accounting for **sealed** versions, not every Python registry declaration. `RuleRegistryStore.seed()` seals only bound versions. More seriously, after 1.2.0 becomes globally bound, the other classes still selecting 1.0.0 also need a legitimate disposition for their unselected 1.2.0 grains. Merely extending the older-to-newer supersession chain does not provide that disposition: the current verifier refuses an otherwise includable, unselected newer version.

**Consequence:** unchanged classes can become unverifiable after the registry expansion. The nine-class path census also demands dispositions for versions the specification says remain unbound.

**Evidence:** FB-18/30/32/33, F:103,131–134; K/`rule_registry.py`:82–110,458–494; K/`inventory_verifier.py`:399–440; M/`1206_gochara_search_inventory_completeness.sql`:799–807.

**P1-5 — The golden and digest acceptance requirements are impossible as written.**  
Three independent problems remain:

- §11.2/FB-69 require identical relationship-record IDs between measuring and final generations. Generation is part of the record’s hashed natural key, so a new generation changes those IDs.
- FB-33 speaks of changing only “that class’s registry digest.” The registry digest covers the whole bound catalogue and sealed census; it is not a per-class digest.
- FB-69 calls all 18 existing H classes unchanged. Bereavement is explicitly changed by FB-45; FB-46 may change additional existing classes.

G12 also explicitly changes the digest inputs from the old representation to copied content. Preserving the *recipe* does not preserve its value.

**Consequence:** a correct implementation fails the stated acceptance gate. Capturing the golden before teardown fixes availability, not comparability.

**Evidence:** F:92,131–134,167–168,201,288; K/`evaluator.py`:133–166; K/`input_vector.py`:97–112,152–172; `decisions/G12_ROUTE1_SNAPSHOT_DESIGN_v1_0.md`:22.

The replacement must identify invariant contact identities and compare generation-normalized record semantics separately from deliberately changed manifest, registry, snapshot and state digests.

**P1-6 — FB-56/67 do not yet define trustworthy unresolved counts or certified near-miss accuracy.**  
FB-56 calls its three reasons “the three cases where `classify_graze` returns None.” The function also returns `None` for:

- unsupported target/relation;
- a detected real crossing;
- failure to find a relevant sampled minimum.

Those cases cannot all be counted as unresolved near-misses. In particular, an omitted genuine contact must retain its distinct failure identity.

FB-67 pins a “classification step” without choosing it, uses a measured angular error as a solver tolerance without defining the guarantee, and omits the reconstruction’s 60-second minimum excursion and one-second boundary tolerance. Its oracle tests manifest sensitivity and a speed-table bound, not the claimed global closest approach or uncertainty.

**Consequence:** the measuring report can misclassify defects, while the final near-miss set and ordinals remain dependent on unspecified numerical choices.

**Evidence:** F:119–127,262,284; K/`contact_certify.py`:108–165; K/`contact_reconstruct.py`:25–33. Current `classify_graze` selects a sampled minimum at lines158–165; it does not implement FB-24’s refined global minimum.

**P1-7 — Adding the near-miss arm to the combined gate does not automatically add it to SQL sealing.**  
FB-20/28 correctly identify `ka_gochara_candidate_gate_violations` as the function to extend. But the database seal triggers currently invoke its components directly:

- search seal guard → `ka_gochara_search_completeness_violations`;
- window seal guard → `ka_gochara_window_verification_violations`.

They do not call the combined wrapper. The Python approval path does use the combined candidate gate, which is useful but different from specifying the database enforcement promised by “refused … at seal.”

**Consequence:** the proposed two-function 1308 change leaves an unspecified SQL enforcement path. The migration contract must name how first seal and replay enforce near-miss completeness and verification.

**Evidence:** F:108–111,123; M/`1206_gochara_search_inventory_completeness.sql`:953–985; M/`1240_gochara_window_verification_gate.sql`:1147–1168; K/`seal_flow.py`:36–72.

**P2 findings**

**P2-1 — All-null acceptance is incorrectly weakened, and the extractor contract remains missing.**  
FB-53/60 call the endpoints and budgets “vacuous” under all-null policy. Coverage, admitted-day burden and computation honesty remain meaningful without a score or peak. The existing scorer calculates adverse burden from admitted days, the gain band from coverage, and T-honesty from coverage completeness.

Conversely, the current loader cannot simply ingest all-null windows: it calls `float(si)` and parses a required peak date. A read-only SQL query alone does not supply the missing policy-aware adapter.

FB-5’s fallback also fails logically: when the extractor cannot read the measuring candidate because it is `test_slice`, moving the oracle to FB-66 moves it to another `test_slice` candidate.

**Consequence:** required checks can be silently dropped, or the promised acceptance report cannot run. The adapter also needs explicit conversion from UTC half-open intervals to the scorer’s date-based representation and a straddling-cutoff test.

**Evidence:** F:77–78,256,270,282; `platform/python-sidecar/services/gochara_eval/extract.py`:106,128–139; `…/gochara_eval/metrics.py`:207–253.

**P2-2 — Density decisions still use conflicting populations and policies.**  
FB-7 says the measuring build supplies fast-planet and ND-H density decisions. FB-41/66 require the final-rules candidate. FB-48 reserves that later evidence expressly for the eight new classes, overlooking changed bereavement and potentially wider P1 karakatva effects.

FB-41/50 apply the 40% gain-band guard while OD-10 leaves its application to adverse `financial_deception` and its denominator open. The existing scorer explicitly separates adverse budgets from the gain band.

**Consequence:** a final rule can be selected using measurements of different rules, or an adverse class can be assessed against the wrong criterion.

**Evidence:** F:82,160,170,175–180,232,245,251,282; R/`registry.py`:173–205; `…/gochara_eval/metrics.py`:207–234; `decisions/ND-P2-20261005_DECISION_BY_DELEGATE_RECONCILED.md`:12.

**P2-3 — Migration and cross-document contracts remain divergent.**

| Conflict | Evidence and consequence |
|---|---|
| **1307 CHECK versus transition guard** | F:104 explicitly chooses CHECK-only; `runbooks/SECOND_WINDOW_PLAN_v1_0.md`:25,42,46 still specifies replacing a guard and treats all three migrations as protected. V1.2 acknowledges the disagreement but does not amend the operating plan. |
| **1307 lacks the exact status-qualified predicate** | FB-19 describes refusing a sliced vector on the publication row without expressing the `published` condition. A literal vector-only CHECK would reject the candidate manifests needed by the measuring build. Acceptance must cover candidate insertion, publication refusal, malformed/NULL scope and both scope representations. |
| **1309 reservation collision** | FB-22 reserves 1309 for any newly discovered registry constraint change. That conflicts with the serving migration reservation described in the user’s brief. The serving design file is absent, so I could not verify its proposed SQL or W1–W12. |
| **G12 fact identity differs** | F:92 uses natural fact keys with `fact_id` as metadata; G12 design:19 uses `fact_id` as key. The natural-key change may be appropriate, but the two contracts must be reconciled explicitly. |
| **G12 live-read boundary is ambiguous** | F:96 permits post-capture live reads only for a report whose result never feeds stored output. G12 design:26 requires live identity drift to block first seal. The allowlist must explicitly preserve that seal-time comparison. |
| **Daśā re-pin is incomplete** | FB-9 names changing `_C_BUILD`; sequencing:74 requires changing **both** `_C_BUILD` and `DASHA_READ_CONTRACT["build_id"]`, plus the lock. Both code constants currently equal `75524b3e…`. Changing only one fails verification. |
| **Brief/seal order is reversed** | F:236 says “seal, brief with the report.” K/`seal_flow.py`:36–72 requires the current approved brief before publication and seal. |

The corrected **1305 → 1306 → 1307 → 1308** order and per-function stacking table are genuine improvements.

**P2-4 — Timeout and failed-candidate handling remain insufficient for dispatch.**  
FB-58 carries the correct 28,800/86,400-second values and recognizes non-cancellation. It omits the measuring-build writer state guard required by the checklist’s timeout ruling, and describes resumption through substeps although the production retry procedure starts again from substep 1.

FB-59 declares that final candidates use the small-test teardown mechanism without specifying the removal of its test-slice eligibility restriction. “Zero rows in every table of the layer” must also be scoped to the candidate, preserving shared registry/substrate state and other generations.

**Consequence:** a timed-out writer may continue committing or overwrite its failure state; teardown can race that writer or reject the final candidate it is supposed to remove.

**Evidence:** F:223–225,266–268; `runbooks/SMALL_TEST_SITTING_CHECKLIST_v1_0.md`:10,166,221–222.

**P2-5 — Report freshness and the independent fixture are only partly repaired.**  
FB-52 binds a report’s label and self-hash, but does not name the candidate input/state identity against which freshness is checked. FB-57 permits replacement under an unsealed label; an old report can retain that same label and a valid self-hash.

The FB-70 fixture exists and its SHA-256 matches the document. It covers the eight FB-35 rows. It does not provide the full independent data promised by FB-38b: bereavement, mother handling, the full affected-person P1 mapping, K-B agent/relation/band rules, and testimony/exclusion behavior.

**Consequence:** a stale report or an incomplete three-way equality test can satisfy the newly stated checks.

**Evidence:** F:156–158,192,264,290; `decisions/fixtures/FB35_TABLE_v1_2.json`.

**P3 findings**

**P3-1 — Editorial leftovers obscure which contract controls.**  
FB-29 refers to a nonexistent §15; FB-50 repeats its seven-item list; FB-37 still names P4’s `infl()` after FB-34 corrects the implementation locus. OD-6 says `_CLASS_KARAKAS` covers “20+” classes; the current mapping contains 17. **Evidence:** F:124,155,175–190,247; R/`registry.py`:173–205.

**P3-2 — One ERRATA instruction is softened instead of carried.**  
ERRATA item 7 is now present. However, both delegate ERRATA say the unfound BPHS Sun-month passage is **not to be cited**; F:40 permits carrying it as “unverified” in rationale. No actual scored use was established, but the instructions differ. **Evidence:** `decisions/ND-H-20261005_DECISION_BY_DELEGATE.md`:62; `decisions/ND-P2-20261005_DECISION_BY_DELEGATE_RECONCILED.md`:37.

**Places where v1.2 still settles or operationalizes owner matters**

An “OPEN” label does not qualify an unconditional instruction elsewhere. Some entries below are inherited delegate rulings, rather than new author decisions; that distinction matters.

| Matter | Operative locations in v1.2 | Assessment |
|---|---|---|
| Numbers on/off and decision timing | §11.6, FB-53/60; F:205,256,270 | Does not explicitly choose numbers-on, but authorizes sealing all-null before OD-1 is decided and removes acceptance checks on that basis. |
| Serving scope and switch | §0, FB-54, §14 step7; F:20,236,258 | Chooses to exclude serving from the final-build scope, while keeping unconditional serving obligations elsewhere. Reader versus projection remains genuinely open. |
| General horizon narrowings | FB-1/2/55, measuring prerequisites; F:63–69,223,260 | Fully dated only, excluding birth, year-start rounding and raw-row rules are operative despite OD-3. |
| Refusal instead of domain extension | FB-1/3, OD-11; F:64,71–72,252 | Chooses second-chart refusal and named domain/future/birth/leap-day refusals; general-chart consequences remain owner matters. |
| January 1 versus February 16 | FB-1/2/7/56, §12; F:63,67,82,217,262 | January 1 is baked into build inputs, tests and measurement before the put-back is resolved. |
| Future windows served but unscored | FB-5/54; F:77–78,258 | An operative protocol sentence despite OD-3 acknowledging that the range approval did not approve this sentence. |
| Pre-1998 reader behavior | FB-54(d); F:258 | Chooses a named refusal while OD-2 says the behavior is undecided. |
| Measuring versus final-rules density decisions | FB-41/48/66, §11.5, §14; F:160,170,204,232–235,282 | Makes the final-rules candidate the default requirement and owner waiver the alternative. FB-7 retains the earlier choice. |
| DVI guard and denominator | FB-41/50; F:160,175–180 | Chooses scored-horizon comparison and literal gain-band application while OD-10 remains open. The next-generation guard itself originated in ND-H. |
| P1 karakatva breadth | FB-46, §12, OD-6; F:168,213,247 | Generic extension is treated as ruled; OD-6 instead says implementation is limited to eight. These are incompatible scopes. |
| Bereavement K-B | FB-45, §12, OD-7; F:167,209,213,248 | Unconditionally implemented. **Already expressly delegated by ND-P2 rule3**; the new inconsistency is presenting the same matter as still open. |
| Mother refusal | FB-39, OD-8; F:158,249 | Unconditional refusal beside an open-decision entry. **Already prescribed by ND-H item5**, not invented by v1.2. |
| R2 near-miss semantics and junction kinds | FB-24/27/29, OD-9; F:119,122–124,250 | Operative beside an open entry. **R2 and the junction list already appear in ND-P2 rule1.** The exact proximity normalization is an additional specification choice. |
| Unresolved residual | FB-56, OD-5; F:246,262 | Chooses refusal pending a ruling; refinement versus an accepted residual remains open. This is a conservative default, but must not be described as closure of the owner decision. |

**Outside-review disposition, finding by finding**

“Resolved” means the specific defect is repaired in clause text, **not** that implementation or production acceptance has been proved. “Partly” includes dependencies acknowledged but not made implementable. The response document contains **no actual rejected finding**; therefore none merits the status “wrongly rejected.” Several accepted premises nevertheless need correction, as noted afterward.

| Finding | Status | Clause-text assessment |
|---|---|---|
| **1.1 Result policy** | Partly | FB-53 exposes alternatives, but §11.6 defers selection beyond seal and all-null acceptance is wrong. F:205,256. |
| **1.2 Serving mechanism** | Not | FB-54 lists a separate workstream and prerequisites; no implementation contract is supplied. F:258. |
| **1.3 Horizon/log changes** | Partly | Shapes, refusals and soft drift added; persisted evidence cannot replay the detector. F:64–72,260. |
| **1.4 Unresolved stretches** | Partly | FB-56 adds reporting/default refusal; reason classification and accuracy remain incomplete. F:262,284. |
| **1.5 Generation bump** | Not | FB-57 relies on config the production caller does not provide. F:264. |
| **1.6 Timeout/run length** | Partly | Caps and lower-bound warning added; state guard, retry semantics and final timeout relation remain incomplete. F:266. |
| **1.7 Failed final candidate** | Partly | FB-59 states intent and one oracle; eligibility, shutdown and exact deletion boundary are unspecified. F:268. |
| **1.8 Owner-facing tests/extractor** | Partly | FB-60 names outputs; loader, policy handling and cutoff acceptance remain missing. F:78,270. |
| **1.9 Rollback/legacy/pre-1998** | Partly | Listed in FB-54; rollback state transitions and reader behavior are not designed. F:258. |
| **1.10 G1/G2/G3** | Partly | FB-61 names dependencies, but supplies neither enforcement nor a report schedule. F:272. |
| **1.11 P4 role/factor shape** | Resolved | FB-22/36 explicitly require the role and factor mapping/null behavior. F:114,154. Adapter implementation remains work. |
| **1.12 Parental P2 exclusion** | Partly | FB-39 names no edges and an excluded pin, but leaves the exact exclusion reason unresolved. F:158. |
| **1.13 Version coexistence** | Not | New chain wording conflicts with unbound 1.1.0 and omits newer-version disposition for other classes. F:131–134. |
| **1.14 Mother resolver** | Partly | Invalid inventory state withdrawn; actual resolver/input contract still unnamed. F:158. |
| **1.15 Path census** | Partly | P2-only negative control added, but version accounting and mandatory `included` semantics need correction. F:103. |
| **1.16 ERRATA item7** | Resolved | Explicitly carried. F:38. |
| **2.1 Wrong stacked function** | Resolved | Per-function chains distinguish completeness, candidate gate and state digest. F:105–112. SQL-seal enforcement is a separate new gap. |
| **2.2 `occurrence_kind` changes digest** | Resolved | Field addition withdrawn; absent-layer before/after-1308 digest oracle added. F:121,123. Broader golden remains invalid. |
| **2.3 1307 mechanism/class** | Partly | CHECK chosen and privilege measurement required; operating plan and exact behavior remain inconsistent. F:104,113. |
| **2.4 General horizon versus ruling** | Not | Acknowledged as open, then stated normatively. F:63–72,244. |
| **2.5 Showing near-misses versus scope** | Not | Showing remains required; serving excluded; §15 reference is broken. F:20,124,258. |
| **2.6 P4 implementation locus** | Partly | FB-34 corrected; FB-37 retains `infl()` wording. F:140,155. |
| **2.7 Daśā pin disagreement** | Partly | Correct code pin identified; required two-constant re-pin not fully specified. F:86. |
| **3.1 Wrong generation for density** | Partly | FB-66 helps; FB-7/48 retain conflicting scope and evidence timing. F:82,170,282. |
| **3.2 Near-miss determinism** | Partly | Accuracy object added without a complete numerical contract. F:284. |
| **3.3 Suvarṇa re-pin sequencing** | Partly | Added to final builder step, but only one of two constants named for update. F:86,234. |
| **3.4 Small-test timing versus 86 years** | Resolved | Measuring timing expressly required; final timing identified as longer/lower-bound issue. F:221,266. |
| **3.5 Lock once versus each PR** | Resolved | Explicit every-merge rule. F:202. |
| **3.6 PostgreSQL formatting version** | Resolved | Same major version and recorded server version required. F:112,203. |
| **4.1 Vacuous noninterference** | Resolved | Four concrete mutation cases must make the check fail. F:124. |
| **4.2 Live-read allowlist** | Resolved | Capture/report exceptions and positive populated controls supplied. F:96. G12 seal-time comparison still needs reconciliation. |
| **4.3 DVI guard oracle/build** | Partly | Correct candidate and denominator named; owner-policy and generation mechanism remain unresolved. F:160,282. |
| **4.4 Which horizon gates budgets** | Partly | Scored horizon specified, but simultaneously left open and conflated with adverse criteria. F:170,175,251. |
| **4.5 Declared accuracy** | Partly | Manifest-sensitivity oracle is not an accuracy oracle. F:119,284. |
| **4.6 START-edge oracle** | Resolved | Explicit lower-edge and birth tests added. F:71–72. |
| **4.7 Test-slice extractor** | Not | Fallback candidate is also `test_slice`; adapter contract remains absent. F:78,282. |
| **4.8 Golden before teardown** | Partly | Capture gate added, but demanded comparison is impossible. F:201,288. |
| **4.9 Junction verification** | Resolved | Explicit independent junction-field recomputation. F:126. |
| **4.10 Independent specification fixture** | Partly | Real fixture/hash exists for eight rows, not all FB-38b contracts. F:157,290. |
| **4.11 Correspondence/stale report** | Partly | Correspondence defined; report lacks explicit candidate-state binding. F:98,192. |
| **5.1 Unreachable switch** | Not | Serving remains outside the delivered scope. F:258. |
| **5.2 Mutable horizon input** | Partly | Soft drift specified; replay evidence incomplete. F:69. |
| **5.3 Unresolved geometry** | Partly | Sink/default refusal specified; classification and accuracy insufficient. F:262,284. |
| **5.4 Non-representative density build** | Partly | Final-rules candidate added but not consistently applied. F:170,282. |
| **5.5 Migration acceptance** | Partly | Function mapping fixed; 1307 and SQL near-miss seal coverage remain. F:104–123. |
| **6.1 General horizon narrowings** | Not | Open in OD-3, operative in FB-1/3. F:63–72,244. |
| **6.2 Numbers on/off** | Partly | Decision exposed; final-seal timing and conditional acceptance still decide consequential behavior. F:205,256. |
| **6.3 Future served/not scored** | Not | Still an unconditional protocol sentence. F:77. |
| **6.4 Near-miss semantics/proximity** | Partly | OD-9 conflicts with operative clauses; R2 itself was already delegated. F:119,122,250. |
| **6.5 P1 extension breadth** | Not | Generic FB-46 conflicts with eight-only OD-6. F:168,247. |
| **6.6 Bereavement K-B** | Partly | Flagged open while applied; outside review understates ND-P2’s explicit approval. F:167,248. |
| **6.7 DVI next-generation effect** | Partly | Candidate avoids first-served over-density if required, but the owner choice is replaced by a default/waiver structure. F:160,282. |
| **6.8 Pre-1998 behavior** | Not | FB-54 selects named refusal despite OD-2. F:243,258. |
| **6.9 Mother failure** | Partly | Open/operative contradiction persists; refusal already appears in ND-H. F:158,249. |
| **6.10 Junction kinds** | Partly | Same contradiction; exact kinds already appear in ND-P2 rule1. F:122,250. |
| **6.11 January versus February** | Not | January remains hardwired despite the unresolved put-back. F:63,67,217,244. |

**Acceptance-test audit of every new or changed FB clause**

I compared v1.2 with document revision `eaed03250`. The table covers all changed FB clauses and all new FB-53–70. “Yes” means a meaningful oracle is specified somewhere in the cited contract; it does not mean it exists or passed in `origin/main`.

| New/changed clauses | Falsifiable acceptance specified? | Missing or defective coverage |
|---|---|---|
| FB-1,2,55 | Partial — F:67,260 | No complete raw-schema, interval/chain, root-confidence, birth-classification or replay-from-copy suite. |
| FB-3 | Partial — F:72 | Edge/birth tests exist; future-start, empty and leap-anniversary refusals lack corresponding cases. |
| FB-5 | Partial — F:78 | Tests windows ending before cutoff, not straddling windows, policy/NULL adaptation or date conversion. Stage fallback is invalid. |
| FB-8 | Partial — F:84,284 | Accuracy mutation covered; not every newly pinned field and its generation-change obligation. |
| FB-9 | Partial — F:86 | No two-constant re-pin acceptance or explicit old-seal replay after the re-pin. |
| FB-14 | Yes — F:96 | Populated positive cases plus denied reads and exercised exceptions. |
| FB-16 | Partial — F:98; G12 design:35 | Positive moved-boundary case exists; ambiguous and competing one-to-one matches need negative cases. |
| FB-18,65 | Partial — F:103,280 | P2-only refusal exists; invalid/unbound versions and legitimately computed-empty grains are not covered. |
| FB-19 | Partial — F:104 | Privilege/deploy-order checks exist; exact candidate-versus-published behavior and malformed scope cases are missing. |
| FB-20,21 | Yes — F:105–113,203 | Real-chain/readback acceptance specified; incomplete SQL enforcement remains a substantive defect. |
| FB-22,36,62 | Partial — F:114,154,274 | Row validation specified; rank-only behavior must prove that non-karaka zero never zeroes/admit/excludes a record. |
| FB-24,25 | Partial — F:119–120,127 | Identity/edge cases listed; no numerical oracle establishes the promised global minimum and uncertainty. |
| FB-26 | Yes — F:121 | Concrete absent-layer before/after migration equality. |
| FB-28,29,68 | Partial — F:123–127,286 | Strong mutation/set tests; direct SQL first-seal/replay and verification-digest integration need explicit tests. |
| FB-30,32,33,64 | Invalid as written — F:131–134,278 | Oracle assumes a per-class registry digest and inconsistent version universe. |
| FB-34,35,70 | Partial — F:140–152,290 | Eight-row fixture equality is meaningful; house-lord behavior and full semantic contracts exceed that fixture. |
| FB-39,63 | Partial — F:158,276 | P2/mother oracle names supplied; real resolver and exact exclusion reason remain undefined. |
| FB-41,48 | Partial — F:160,170 | Share calculation specified; threshold boundary, adverse-policy separation and selected-generation behavior need explicit tests. |
| FB-50,52 | Partial — F:175–192 | Report contents/self-hash are testable; source-state freshness and full counterfactual calculations are not adequately bound. |
| FB-53 | **No policy-specific acceptance suite** — F:256 | Gate list is not a test of all-null versus numerical output and applicable endpoints. |
| FB-54 | Partial — F:258 | One happy-path query; no refusal, rollback, scope, legacy preservation or standalone near-miss acceptance matrix. |
| FB-56 | **No measuring-sink oracle** — F:262 | Final unresolved refusal is covered elsewhere; complete, correctly classified and recountable sink output is not. |
| FB-57 | **No generation-transport/reuse oracle** — F:264 | Needs actual production dispatch, invalid labels, sealed reuse, unsealed replacement and skip/receipt tests. |
| FB-58 | **No fired-cap acceptance test** — F:266 | Needs proof of writer termination/state guarding and safe teardown/re-dispatch. |
| FB-59 | Partial — F:268 | Positive deletion case only; sealed, other-generation, shared-state and still-running-writer protections need cases. |
| FB-60 | **No executable acceptance contract** — F:270 | Lists owner-visible material but not validation of its generation, policy, completeness and comparison basis. |
| FB-61 | **No dependency/scheduling oracle** — F:272 | No proof that omitted G1–G3 duties actually gate or run. |
| FB-66 | **No acceptance test for using the correct candidate** — F:282 | Needs rejection of density decisions/report/cap taken from old rules or another candidate state. |
| FB-67 | Partial — F:284 | Identity and speed-table tests do not establish numerical certification accuracy. |
| FB-69 | Invalid as written — F:288 | Capture-before-teardown is specified; the cross-generation byte-equality oracle is impossible. |

**The six prerequisites for the measuring build**

| Outside-review prerequisite | Sufficient now? | Required correction before dispatch |
|---|---|---|
| Exact horizon detector, shapes, START refusal, pinned basis and drift rule | **No** | Resolve the real-row mapping and retain enough immutable input evidence for independent derivation. Existing START tests are useful. |
| Structured unresolved sink | **No** | Separate genuine crossings/omissions from unresolved geometry; define stable identifiers, recounting and reason-specific fixtures. |
| Golden before teardown | **No** | Replace impossible cross-generation ID/digest equality; enumerate the genuinely unchanged rules/classes. Then retain the capture gate. |
| Cap, Cloud Run timeout and fired-cap procedure | **Partly** | Carry the measuring-build state guard; require actual writer exit before teardown; specify restart-from-zero behavior. |
| Test-slice extractor or relocated oracle | **No** | Supply the policy-aware extractor or move the oracle to a genuinely usable stage. FB-66 is also test-sliced. |
| Reconcile 1307 mechanism/class before scheduling the window | **Partly** | Reconcile the operating plan and specify/test the status-qualified CHECK. Privilege classification appropriately remains measured. |

These corrections do **not** require pretending that all final serving decisions must be closed before measurement. They require a reliable measurement contract and an explicit boundary around what that build can establish.

**Additional implementability checks against `origin/main`**

Besides the mismatches identified above:

- `derive_chart_horizon`, the cited `measuring_report` and `nd_h_tables` implementations, near-miss storage tables, and migrations1305–1309 are not present at the nominated baseline. They are proposed work, not verified delivery merely because F cites an in-flight PR.
- `karaka_agent` requires more than inserting the described factor: K/`rule_registry.py`:301–327 uses fixed factor-direction and selector handling and currently persists a category mapping only for the existing dignity factor.
- `P1_RELATION_KINDS` is not presently the generic mechanism that `period_lord_relation` consumes. FB-46 correctly demands a real consumer; that consumer must be implemented explicitly. R/`permission.py`:104 onward contains the actual relationship logic.
- Adding `parental_event → father` does not itself make P2’s existing native rows fail the relative-frame constraint. P2 explicitly emits `affected_person="native"`; the required exclusion must operate independently. K/`evaluator.py`:326–392.
- FB-54’s projection alternative needs a resolution of migration1240’s legacy-row refusal, not just relaxation of1236.
- Rollback needs an actual lifecycle design. The governed boundary guard permits `published → superseded/rolled_back`, but not republishing a superseded governed row. Retaining old data and moving a pointer alone do not prove a working rollback. M/`1240_gochara_window_verification_gate.sql`:975–985.

**What the outside review got right—and what it got wrong**

| Claim | Independent check |
|---|---|
| No non-test product reader of `ka_gochara_eval_window` outside the kernel | **Confirmed within the searched repository scope.** Kernel readers exist; production MCP retrieval still reads legacy tables. See `platform-mcp/src/tools/retrieval/register_gochara_contact_ledger.ts`:287,416,456 and `register_gochara_windows.ts`:708,1809,2114. |
| Migration1236 refuses v5 authority | **Confirmed.** Its CHECK rejects governed major versions ≥5. M/`1236_gochara_authority_refuses_governed_generation.sql`:46–51. |
| Sealer requires all-null | **Correct for the default/current milestone path, overstated as a universal SQL restriction.** K/`seal_flow.py`:209,238–241 accepts a required-policy parameter; migration1240 recognizes both policies and applies its no-number rule conditionally. |
| Migration1240 forbids legacy projection rows | **Confirmed.** The violation arm is unconditional for the governed check; it is not limited by the preceding all-null condition. M/`1240_gochara_window_verification_gate.sql`:448–460. |
| Eval-window chart lock | **Already present.** Statement lock on UPDATE/DELETE, row guard on INSERT/UPDATE/DELETE and no-truncate trigger exist. M/`1156_gochara_eval_window.sql`:558–577. A claim that this table lacks chart locking would be wrong. |
| All five endpoints and budgets become vacuous with all-null scores | **Wrong.** Numerical peak/rank metrics need qualification or adaptation; coverage, burden and computation honesty remain meaningful. Existing loader incompatibility is a separate problem. |
| One-hour versus six-hour steps prove builder/verifier disagreement | **Overstated.** The cited values belong to cooperating certification/reconstruction routines: `classify_graze` calls reconstruction. They demonstrate different numerical stages, not two independent implementations disagreeing by construction. |
| Every registered 1.1.0 declaration must be inventoried | **Wrong unless actually sealed/bound.** Migration1206 accounts for `ka_gochara_rule_path_seal`; seeding seals only bound versions. V1.2 amplified this misunderstanding. |
| R2, junction kinds, mother refusal and bereavement K-B were newly settled by the scope author | **Overstated.** ND-P2:7–10 and ND-H:33 already prescribe them under the recorded delegation. Their simultaneous classification as open in v1.2 is the real documentary conflict. |
| “No invented numeric weight” forbids any geometric proximity number | **Not established.** ND-P2:8 explicitly permits geometric proximity while prohibiting invented scoring weight. The exact formula still needs a defined contract, but those concepts are distinct. |
| All 18 existing H classes form an unchanged golden | **Wrong.** Bereavement changes explicitly; wider P1 karakatva may change more. The review’s proposed remedy needed correction before adoption. |

**What I did not verify**

- No database state, applied migration ledger, privileges, production readers, image contents, small-test outcome, timings or numerical counts.
- No network refresh: `origin/main` means the local ref identified above.
- No in-flight PR implementations or claims of their delivery, including3185/3187.
- No serving brief W1–W12: `V5_SERVING_PATH_DESIGN_BRIEF_v0_1_FABLE.md` was absent from the inspected checkout/ref. The proposed1309 reservation could therefore only be checked against the user’s description and FB-22.
- No ephemeris execution, full-horizon root enumeration, scoring run, database migration rehearsal or runtime tests.
- No independent verification of Sanskrit/verse sources or empirical predictive validity. I checked the specification against the recorded rulings and ERRATA.
- I did verify the committed FB-35 fixture’s contents and SHA-256; that establishes the fixture artifact, not implementation equality.

