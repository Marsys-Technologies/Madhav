# T5 · VOCABULARY — cross-component consistency check

Task: Nikaṣa Phase 5, VOCABULARY. Date run: 2026-09-26. Branch `campaign/nikasha-test` (no commits made).
Scope surfaces (paths verified; Tier 1 was **not** at the stated path — located by Glob at `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md`, one level up from `briefs/nirmana/`):

- T1: `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md`
- T2: `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md`
- T3: `00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`
- T4: `00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md`
- L0: `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md`
- Pilots: `00_ARCHITECTURE/briefs/nirmana/l0_assets/*.md` (5 files)
- Inspector: `platform/scripts/governance/asset_census.py`
- Tracker: `00_ARCHITECTURE/control/asset_elevation_tracker.py`
- Ledgers: `00_ARCHITECTURE/control/asset_gaps.jsonl` (263 lines), `asset_certs.jsonl` (1 line, `_schema` only)
- Manifest: `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (found via `manifest_fingerprint.py:40`)

---

## FINDINGS (disagreements)

### V1 — T4 §4 says "the eight gates"; its own table and T3/tracker have nine
- T4 `ASSET_ELEVATION_TEMPLATE_v2_0.md:210`: `## §4 · Asset conformance — the eight gates`; `:213` `inherits: layer §5.2 (a) — the eight gates`; also `:13` (`§5.2 the eight gates`) and `:498` (`the eight gates or the`).
- Same file's §4 table lists **nine** rows: Ldgr, Idem, Earn, Null, Vocab, Carr, Narr, Dens, **Build** (lines 221–233).
- T3 `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md:518-519`: "**Seven always, plus at most two that apply conditionally — nine in total** (eight at v1.1; `Build` added 2026-09-26 by native ruling, decision 17)."
- Tracker `asset_elevation_tracker.py:52-72`: `GATES` has 9 entries; `asset_elevation_tracker.json` (generated 2026-09-26T17:03:13+05:30) carries 9 gates.

`| Rnnn | T4 §4 heading/inherits/§13-ref/§Adapting: replace "the eight gates" with "the nine gates" (4 occurrences: lines 13, 210, 213, 498) | T5 | OPEN |`

### V2 — T4 §4.2 heading says "the six checks"; its table lists nine
- T4 `:240`: `### 4.2 · Buildability — the six checks, and what is NOT a gap`
- T4 `:268` (same section): "All nine checks run read-only, and all nine can return false:" followed by a table numbered 1–9 (`:269–279`).

`| Rnnn | T4 §4.2 heading: "the six checks" → "the nine checks" (the section body already counts nine) | T5 | OPEN |`

### V3 — Build check-count disagrees across T3 (sealed), T4, and the tracker comment
- T3 `:37` (changelog, decision 17): "the property is decidable: six read-only static checks plus a runtime state that `ctx.dry_run` establishes"; §5.2 Build row (`:535`): "six static checks (registered · contract · dispatchable target · DAG resolvable · count/integrity · completion honesty) plus a runtime state proved by `ctx.dry_run`".
- T4 §4.2 (`:269–279`): nine checks — the same six plus **7 exercised**, **8 history**, **9 dependency liveness**.
- Tracker `:61-71` (comment on the Build gate): "six static checks plus a dry-run proof".

`| Rnnn | Decide the canonical Build check count (T4's nine) and align T3 §5.2 Build row + the 2026-09-26 changelog wording and the tracker GATES comment, or explicitly record "T3 names the six static checks; T4 §4.2 adds three run-record checks" | T5 | OPEN |`

### V4 — Tracker header comment stale: "Eight, not thirty-three"
- `asset_elevation_tracker.py:43-44`: "# The certified gates. Eight, not thirty-three." — directly above a 9-entry `GATES` list (`:52-72`, Build at `:71`).

`| Rnnn | asset_elevation_tracker.py:43 comment: "Eight, not thirty-three" → "Nine, not thirty-three" (Build added by native ruling 17) | T5 | OPEN |`

### V5 — T3 §5.4 test 5 demands "§5.2's eight-row map"; the map has nine rows
- T3 `:629`: "5. **The gate map exists.** §5.2's eight-row map from gate to feeding section is written out in the instance."
- T3 §5.2 gate map (`:573-583`) has **9 rows** (Ldgr, Idem, Earn, Null, Vocab, Carr, Narr, Dens, Build).

`| Rnnn | T3 §5.4 test 5: "§5.2's eight-row map" → "§5.2's nine-row map" | T5 | OPEN |`

### V6 — Verdict spelling drift inside T3 and T4 against the closed set
Closed set (agrees everywhere it is *defined*): `PASS | FAIL | PARTIAL | NO_DETECTOR | N/A` — T3 `:611`, T4 `:236-238`, tracker `:109`, census `:84`, `asset_certs.jsonl` `_schema`.
- T3 `:359`: "result — `PASS` / `FAIL` / `PARTIAL` / **`NO DETECTOR`**. `NO DETECTOR` is never a pass; it is a gap." (space spelling, §2.7)
- T3 `:520`: "a gate without one is `NO DETECTOR`, which is an honest null, never a pass." (space spelling)
- T4 `:278` (§4.2 check 8): "PARTIAL if it has errored before and the latest run completed; NA if never run" — bare `NA`, not `N/A`.
- The tracker comment (`:105-108`) itself records this exact failure class: "Three surfaces previously spelled these three different ways (NO DETECTOR / NO_DETECTOR, N-A / N/A / NA)". The doc surfaces still carry the space/bare spellings.

`| Rnnn | T3 lines 359 and 520: "NO DETECTOR" → "NO_DETECTOR"; T4 §4.2 check 8: "NA if never run" → "N/A if never run" — the closed-set spellings already rule the ledgers | T5 | OPEN |`

### V7 — L0 instance contradicts itself on the gate denominator: 320 vs 360
- L0 `:612`: "**Nine gates × 40 assets = 360. Certified: 0.** (Eight until 2026-09-26; `Build` added by native ruling 17 …)"
- Same document: `:146` "**NO_BRIEF = 40/40, ELEVATED 0/40, gates certified 0/320.**"; `:522` "5. **Briefs and gates** — 40 briefs, 320 gates"; `:613` "which agrees with the tracker's `gates certified 0/320`"; `:730` "0/320 gates certified".
- Current tracker state (`asset_elevation_tracker.json`, 9 gates): a fresh run's denominator is 9 × 40 = **360**, so `0/320` can no longer be printed.

`| Rnnn | L0 v3.0: replace the four "0/320"/"320 gates" figures (lines 146, 522, 613, 730) with 0/360, keeping the parenthetical history at line 612 | T5 | OPEN |`

### V8 — L0 status figures no longer reproduce against the live tracker/ledger
- L0 `:146`: "NO_BRIEF = 40/40" and `:730`: "**Ledger after five pilots:** 30 gap rows, 18 opportunity rows, 5 assets at `GAPS_REGISTERED`, 35 at `NO_BRIEF`".
- Measured 2026-09-26: `asset_elevation_tracker.json` (generated 17:03:13+05:30) shows all 40 L0 assets at **GAPS_REGISTERED**, 0 at NO_BRIEF; `asset_gaps.jsonl` contains **243 kind=gap** and **19 kind=opportunity** rows (census-emitted rows landed after the doc's measurement). Command: `python3 -c` Counter over the ledger + tracker JSON (see Agreements A6).

`| Rnnn | L0 v3.0 §1.1/§9: re-run the tracker and ledger counts and restate (40 GAPS_REGISTERED, 243 gap + 19 opportunity rows as of 2026-09-26), or date-stamp the figures as pre-census-emission | T5 | OPEN |`

### V9 — [TRANSFERS] contradiction between T2 §1/§12.2 and T3 §5.4 test 4
- T2 `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md:83-85` (§1): "Every obligation in this document that belongs to one of them is marked **[TRANSFERS]** — it moves to that plane's artefact, unchanged in substance, when that plane is elevated. A [TRANSFERS] obligation is not a data-plane layer's to build alone, and a layer plan does not inherit it as its own work."
- T2 `:614` (§12.2): "| Presentation parity **[TRANSFERS]** | …" and `:621` "| Delivery sentinel **[TRANSFERS]** |".
- T3 `:628` (§5.4, acceptance of the instance): "4. **Presentation parity** holds for the layer's served surface." — a layer-instance acceptance test requires the very obligation T2 marks [TRANSFERS] and forbids a layer plan to inherit.
- (T4 is consistent with T2: `:166,173,474` mark the reachability requirement [TRANSFERS] to the retrieval plane.)

`| Rnnn | Resolve: either T3 §5.4 test 4 is reworded ("Presentation parity is carried as a [TRANSFERS] row, named and not claimed as this layer's own work"), or T2 §12.2 un-marks Presentation parity; the two documents currently impose opposite obligations on a layer instance | T5 | OPEN |`

### V10 — T1's review_record points to a file that does not exist; its counts are unverifiable
- T1 `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md:24`: `review_record: briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md  # verdict ACCEPT, 11 MAJOR + 14 MINOR, all folded` (also `:22` review_backing).
- `find . -name "REVIEW_PRODUCT_DEFINITION*"` returns nothing; `00_ARCHITECTURE/briefs/reviews/` contains only KIMI_K3_*, REVIEW_DATA_PLANE_*, REVIEW_L0_STRATEGY_v2_0.md. "11 MAJOR + 14 MINOR" is NOT_MEASURED — needs the missing review file.

`| Rnnn | T1 frontmatter: locate or restore briefs/reviews/REVIEW_PRODUCT_DEFINITION_v3_1.md, or correct the pointer; until then the "11 MAJOR + 14 MINOR, all folded" claim is unverifiable | T5 | OPEN |`

### V11 — T2's summary of the v3.0 review's finding counts does not match the review file
- T2 frontmatter (`:36-38` area, `document_reviews`): "reviews/REVIEW_DATA_PLANE_v3_0.md      # REJECT, 2 BLOCKER + 10 MAJOR + 11 MINOR; 10 folded at FINAL, 6 partly, 5 outstanding".
- Measured (`grep -oE '^\*\*[0-9]+\. [A-Z]+' 00_ARCHITECTURE/briefs/reviews/REVIEW_DATA_PLANE_v3_0.md | sort | uniq -c`): findings 1–21 = **2 BLOCKER (1,2) + 9 MAJOR (3–11) + 10 MINOR (12–21)** = 21 findings.
- Corroborated by the FINAL review itself: `REVIEW_DATA_PLANE_FINAL_v1_0.md:8`: "every one of the 21 findings of REVIEW_DATA_PLANE_v3_0 checked against the file". T2's "10 MAJOR + 11 MINOR" sums to 23, not 21.

`| Rnnn | T2 frontmatter document_reviews: "2 BLOCKER + 10 MAJOR + 11 MINOR" → "2 BLOCKER + 9 MAJOR + 10 MINOR (21 findings)" to match the review file | T5 | OPEN |`

### V12 — "Ten obligations": T3 lists ten as "the product's"; T1's §14 table has eleven rows
- T3 `:503-505`: "The ten obligations are the product's, not the layer's: source and domain fidelity · computational correctness · concept and relationship completeness · interpretive fidelity · distinctive understanding · consumer understanding · temporal integrity · predictive performance · delivery fidelity · operational honesty." (10 items; Domain correctness omitted, no reason given at this surface.)
- T1 §14 (`00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md:570-588`): the table has **11 rows** — the same ten **plus `Domain correctness`** (marked "Discharged above the data plane, in the reasoning layer (native ruling, 2026-09-25)").
- T2 §13.3 (`:660-668`) carries the reconciliation T3 lacks: "**Ten, not eleven, and deliberately so:** `Domain correctness` … is **not** a data-plane obligation (native ruling, 2026-09-25)."

`| Rnnn | T3 §5.1: after "The ten obligations are the product's", add the ruling-11 clause ("the product's §14 table carries eleven rows; Domain correctness is discharged above the data plane and is scored on no data-plane layer") so the omission of Domain correctness reads as deliberate, not as drift | T5 | OPEN |`

### V13 — T2's own changelog says "§13.3 is nine elements"; §13.3 says "Ten elements"
- T2 `:42` (FINAL changelog, item f): "(f) §13.3 is nine elements and says so (1a kept rather than renumbered…)".
- T2 §13.3 (`:658`): "**Ten elements.** Item 1a is the vocabulary element … and item 1b the value-terms element …" — items 1, 1a, 1b, 2–8 = 10 (verified by reading the list, `:660-684`).

`| Rnnn | T2 changelog item (f): "nine elements" → "ten elements" (1, 1a, 1b, 2–8), or annotate that 1b was added after that entry was written | T5 | OPEN |`

### V14 — Manifest fingerprint mismatch on T4 (declared ≠ on-disk)
- Manifest `CAPABILITY_MANIFEST.json` entry ASSET_ELEVATION_TEMPLATE: `fingerprint_sha256: bb341cc1a696…` (full `bb341cc1a696db7b5541af8792237aff12ac18985b1491979a73ed8ed98fa4dc`), version 2.0, doc_status DRAFT_PENDING_REVIEW.
- On disk: `shasum -a 256 ASSET_ELEVATION_TEMPLATE_v2_0.md | cut -c1-12` → **244e87dff30a**. The v1.1→v2.0 edit was never restamped. (Other four documents match — see A6.)
- Manifest note on the L0 entry is also stale in prose: "doc_status mirrors the document's own frontmatter (REVISED_PENDING_REVIEW as of 2026-09-25)" while the document reads `status: DRAFT_PENDING_ACCEPTANCE` (L0 `:7`); the structured `doc_status` field is correct.

`| Rnnn | Run manifest_fingerprint.py --write (or the entry-level restamp) for ASSET_ELEVATION_TEMPLATE v2.0 in the session that next touches the manifest; fix the L0 entry's stale "REVISED_PENDING_REVIEW" prose note | T5 | OPEN |`

### V15 — Same check, two criterion strings/ids: hand vs census `Earn.build_record` rows
- Hand rows: `asset_gaps.jsonl` `bg_ontology-G02` — `"criterion": "Earn.count_sql_scope"`… and `bg_ontology-G02`→`Earn.build_record`: "measured: asset_throughput.rows_written = 0 against 741 live rows, rows_per_second NULL, last_built_at 2026-09-04 / required: a build record carrying a real figure"; `bg_ephemeris-G03` — "measured: asset_throughput.rows_written = 0 for the layer's largest table (825,084 rows), rows_per_second NULL / required: a build record carrying a real figure".
- Census rows for the same check on the same assets: `bg_ontology-Earn.build_record` and `bg_ephemeris-Earn.build_record` — "measured: rows_per_second=NULL, last_built=2026-09-04 / required: the Earn gate's claim" (emitted per `asset_census.py:599`, `what=f"measured: {res['measured']} / required: the {crit.split('.')[0]} gate's claim"`).
- Same check name (`Earn.build_record`), same asset, different `gap_id` namespace and different `what` strings → duplicate-in-substance ledger rows. (Namespace reconciliation is the LEDGER_DRIFT task's R28 scope; the vocabulary defect — two strings for one criterion — is recorded here.)

`| Rnnn | Pick one criterion-string authority for Earn.build_record (the census-generated string with the richer hand-written measured clause merged in) and withdraw the duplicate row under the other id | T5 | OPEN |`

### V16 — "Review record" names three different artefacts across tiers (item 10 answer: they are NOT the same artefact)
- T1 `:24`: field name `review_record:` → a **document review** (and its target is missing, V10).
- T2 `:35`: `source_review_record: MADHAV_DATA_PLANE_V2_REVIEW_RECORD_v1_0.md` → the **source research record** ("inspected files, [S0x] findings").
- T2 `:37-39`: `document_reviews:` → reviews **of** the document (REJECT verdicts); plus `seal.review_backing` (`:22`).
- T2's own changelog (`:42` item g) records the fix: "`the review record` split into the source record and the document reviews". The split landed in T2 only; T1 still uses the ambiguous bare name `review_record` for a document review.
- Separately, layer-level instances use a fourth pattern: `MADHAV_DATA_PLANE_L0_VALIDATION_AND_REVIEW_RECORD_v1_0.md` (and L1, L2, `L3_ASTRA_REVIEW_RECORD`).

`| Rnnn | Rename T1's frontmatter field review_record → document_reviews (mirroring T2's disambiguated convention), and record the four naming patterns (source_review_record / document_reviews / review_backing / *_VALIDATION_AND_REVIEW_RECORD) in one glossary line so "review record" is never again a bare referent | T5 | OPEN |`

### V17 — All five L0 pilot briefs carry eight gates, no Build row; the tracker already requires nine
- Every file in `l0_assets/` has `## §4 · The eight gates` (EPHEMERIS:99, ONTOLOGY:178, PANCHANGA:91, RULES:116, SARVATOBHADRA_GRID:90) and exactly 8 gate rows (Ldgr…Dens, no Build — verified: `grep -oE '\*\*(Ldgr|Idem|Earn|Null|Vocab|Carr|Narr|Dens|Build)\*\*'` per file).
- Tracker `REQUIRED_GATES` (`:112`) includes `Build`, so no pilot asset can reach ELEVATED without a Build record; the tracker comment at `:29` already flags these briefs as pilots under a DRAFT_PENDING_ACCEPTANCE instance.
- BG_PANCHANGA `:20`: "six of eight gates are N/A" — under the nine-gate set the count changes.

`| Rnnn | On pilot refresh against the accepted L0 instance, add the Build gate row to each pilot §4 and recompute the N/A counts ("six of nine"); note in each pilot that the eight-gate shape predates native ruling 17 | T5 | OPEN |`

---

## AGREEMENTS (one line each, with evidence)

- **A1 · SHAPE markers (item 5):** tracker `SHAPE` (`asset_elevation_tracker.py:92-103`, 10 markers) == T4 §2 list (`:186-187`: "identity · inputs/DAG · correctness · data sufficiency · consumers · value/target · synergy · knowledge-time · change packet · evidence"), and T4 `:181` declares them "the ten markers below, verbatim". Evidence: `sed -n '88,103p' tracker` vs `sed -n '179,190p' T4`.
- **A2 · Verdict closed set (item 2):** identical five spellings `PASS FAIL PARTIAL NO_DETECTOR N/A` at census `:84` (`NO_DET`/`NA` are variable names holding the full strings), tracker `:109`, T3 `:611`, T4 `:236-238`, `asset_certs.jsonl:1` `_schema`. Evidence: `grep -n "VERDICTS = " tracker`; `head -1 asset_certs.jsonl`. (Census's sixth value `NOT_GENERIC`, `:84`, is print-only by design — "never a pass", `:36-37` — and never enters the certification ledger; recorded as consistent-with-note.)
- **A3 · Ledger states (item 3):** `OPEN | IN_PROGRESS | CLOSED | WITHDRAWN` identical in T4 §5 (`:359-362`), gaps `_schema` (`asset_gaps.jsonl:1`), tracker filter (`:200`, `:235-238`). Ledger rows actually contain only OPEN (261) and IN_PROGRESS (1) plus the `_schema` line. Evidence: `python3 -c "collections.Counter(r.get('state'))"` → `{'OPEN': 261, None: 1, 'IN_PROGRESS': 1}`.
- **A4 · kind vocabulary (item 4):** `gap | opportunity` identical in T4 §5 (`:347-350`), gaps `_schema` line, tracker (`:200-201` default gap, `:236-238` separate counts), census emit (`asset_census.py:599`, always `kind="gap"`). Ledger: 243 gap, 19 opportunity. Evidence: Counter over `kind` field.
- **A5 · Gate keys (item 1, names):** the nine keys Ldgr/Idem/Earn/Null/Vocab/Carr/Narr/Dens/Build are identical in tracker `GATES` (`:52-72`), T3 §5.2 table (`:523-533`), T4 §4 table (`:221-233`). Dom→Carr rename recorded consistently in T3 changelog `:41`, tracker `:77-86` (incl. `DOMAIN_MENU = CARRIAGE_MENU` alias), T4 `:516`. Carriage menu D1–D3 (D4 removed) identical in tracker `:81-85`, T3 `:545-551`, T4 `:318-322`.
- **A6 · Cross-document counts verified (item 11):** L0 40 assets — L0 `:144` == census JSON `n_assets: 40`; "registry says 34 writer-backed … code registers 36" (L0 `:144`) == census JSON `registered_ids: 36, registry_has_writer: 34`; "68 global runs, zero included bg_*" (T4 `:250-255`) == census JSON `global_runs: 68, global_runs_touching_layer: 0`; T4's "one of them (`bg_sign_medical`) with a writer" == census JSON `never_exercised_with_writer: ['bg_sign_medical']`. Manifest fingerprints match for T1 `b9c098cd390d`, T2 `a7eaf821bf65`, T3 `137ba6b9a415`, L0 `2233d00ad48d` (`shasum -a 256 … | cut -c1-12` vs `fingerprint_sha256`). T2's FINAL-review summary "2 BLOCKER + 9 MAJOR + 10 MINOR … 1 restated and 1 withdrawn" matches `REVIEW_DATA_PLANE_FINAL_v1_0.md` (measured: findings 1–22 = 2 BLOCKER + 9 MAJOR + 10 MINOR + 1 WITHDRAWN, #1 restated MAJOR per its own header `:10`). Tier-2 §13.3's "Ten elements" matches its own list (1, 1a, 1b, 2–8). Tier-1/T2/T3/L0 version-status fields match their manifest entries (`version`/`doc_status`) — only the T4 fingerprint and one L0 prose note drift (V14).
- **A7 · Cert record shape:** T3 §5.3 (`:605-611`), T4 §7 (`:407-409`) and `asset_certs.jsonl` `_schema` all name `asset · criterion · criterion_version · detector · evidence · verdict · verified_by · verified_on`; the ledger holds only its schema line (1 line total), so no row-level drift is possible yet.

## NOT_MEASURED (needs production DB — `DATABASE_URL` was not available this session)

- "9 × 129 assets across L0–L5" (T3 `:521`, L0 `:612`): the 129 total needs `asset_registry` reads for L1–L5; census JSON covers L0 only (40 ✓).
- T4 §4.2 figures: "776 recorded runs" (`:246`), "5 of 40 L0 assets have never appeared in any run" (`:275`), "13 of 40 … errored or aborted" (`:278`), "21 of L0's records carry skip_no_delta" (`:281`) — need `build_runs` / `build_run_assets` tables.
- L0 `:145` "1 is catalog_status = DRAFT (bg_vidhi_floors); the other 39 are CURRENT" — needs registry read.
- T1's "11 MAJOR + 14 MINOR" review counts — blocked on the missing file (V10), not the DB.
