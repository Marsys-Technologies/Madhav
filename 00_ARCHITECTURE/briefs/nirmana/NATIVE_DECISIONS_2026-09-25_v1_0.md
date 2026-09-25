---
artifact: NATIVE_DECISIONS_2026-09-25
canonical_id: NATIVE_DECISIONS_2026_09_25
version: "1.5"
status: RULED
date: 2026-09-25
decision_owner: Native
recorded_by: L3 strategy session (madhav-e3)
role: "Decisions put to the native on 2026-09-25 with a recommendation each; the native's rulings, verbatim in effect, and what each unblocks. Eight at v1.0; six further native-initiated authorizations added at v1.1-v1.5 (#9 signature authority, #10 mortality-exclusion removal, #11 domain correctness is not a data-plane obligation, #12 Sarvatobhadra school named, #13 tiers 1-3 sealed, #14 the A3 materialized-view expectation, decided under delegation), plus the resolution of decision 5 and the chart_facts verification-status investigation, both GOVERNING FACTS rather than answers to a question this session asked."
---

# Native decisions, 2026-09-25

Eight decisions were put with a recommendation each. **Seven accepted as recommended; one changed.**

| # | decision | ruling | status |
|---|---|---|---|
| 1 | `bg_sarvatobhadra_grid` — which school's grid | "rule it" accepted **as a task, not as an answer** — the school itself is still unnamed | **OPEN in substance** |
| 2 | `bg_prashna_rules` — open the horary facility? | **Keep closed.** Nothing in L0 requires it; it deserves its own product decision | RULED |
| 3 | D-K merge gate — does one instrument satisfy it? | **Yes. One review discharges D-K.** The native extended this generally: where a review has been done once, the instrument is accepted | RULED |
| 4 | Who owns the `ka_sangam → ka_vedha_gochara` edge | **Gochara's migration 1084 owns it; Saṅgam withdraws its seed claim.** Two migrations for one edge is worse than the current state | RULED |
| 5 | Production changed outside the migration ledger | **Treat as urgent.** See the finding below — it is materially larger than the single migration this decision was framed around | RULED |
| 6 | Merge queue squashes Saṅgam's 119 commits | **Let it squash.** The evidence lives in the review artifacts, not the commit log. A one-way door, knowingly taken | RULED |
| 7 | Begin the consolidation onto one surface | **Yes, once 3–5 are settled** | RULED |
| 8 | Start L1 now, or finish L0 first | **CHANGED from the recommendation: finish L0 completely first.** L1 does not begin until L0 is wrapped | RULED |

## What each unblocks

- **3 + 4 + 6** release Saṅgam PR #2735: D-K is discharged, the edge has an owner, the history question is closed. The remaining CI failures are the two mechanical ones plus the RRV-01 defect, which is the Saṅgam author's.
- **5** is now the gate on **7**: the consolidation cannot merge onto a surface whose deployed state is unknown.
- **8** re-aims the campaign. The L0 packets W-L0-1 … W-L0-9 and the six corrections in the L0 instance's §7 are the work. **No L1 instance is written until they close.**
- **1** still needs a school named before `bg_sarvatobhadra_grid` can hold a row.

## Finding raised under decision 5 — larger than the decision assumed

Decision 5 was put as "migration 1084's body is in production but 1084 is not in the ledger." Measured
2026-09-25 against production, the gap is **not one migration**:

| migration | its effect in production | recorded in `_migrations_applied` |
|---|---|---|
| 1080 gochara_resonance_target_resolution_state | `gochara_resonance_map.target_resolution_state` **exists** | **no** |
| 1081 gochara_ledger_coverage_publication | `kala_gochara_coverage`, `kala_gochara_publication` **exist** | **no** |
| 1082 vedha_moorti_stamp_columns | `kala_vedha_gochara` 17 → **20** cols, `kala_moorti_nirnaya` 22 → **26**, both with `source_qualification`, `precision_regime`, `corpus_verifiable` | **no** |
| 1084 wp7_k1_v1_registry_edges | `ka_sangam` and `ka_kshetra` both carry `ka_vedha_gochara` in `depends_on` | **no** |
| 1087 contacts inclusivity/completeness/tier_basis | `kala_gochara_contacts` carries `comparable_with` | **no** |

`SELECT filename FROM _migrations_applied WHERE filename ~ '^(108[0-9]|109[0-5])_'` returns **nothing**.

**This happened during the session, not historically.** An earlier measurement the same day recorded
`kala_vedha_gochara` at 17 columns with none of the three stamps; it now has 20 with all three.

**Why it matters beyond tidiness.** Every instrument that answers "what is deployed?" reads
`_migrations_applied`. This session's own tracker did, and consequently reported 1080–1091 as
*pending* when their effects are live — so the tracker's deployed-vs-code figure was wrong in the
direction that matters: it understated what production already carries. Any consolidation, any
rollback plan and any "is this safe to merge" answer built on that ledger is unreliable until the
ledger and production agree.

This is the mirror of the hazard CLAUDE.md §N.4 names. That rule warns of migrations silently doing
nothing while a deploy reports success. Here migrations did something while the ledger reported
nothing. The same detector closes both: **compare the ledger against production structure, not
against the deploy's own report.**

**Not established:** who applied them, by what path, and whether the bodies applied match the
committed files. Those are execution-session questions; this session measured the divergence and
stopped.

---

# v1.1 — two native-initiated authorizations, 2026-09-25

These two were not put by a session. The native raised them and authorized them directly, and both are
recorded as **governing facts**: they bind every later document, layer plan, asset brief and review in
this chain until the native changes them.

## 9 — Signature authority on a reviewed governing document

**Ruling, native, verbatim in effect:** "The reviewer doesn't have to be the one who signs this
document. It can be the reviewer. Or the native, that is me, or you — it just needs to have been
reviewed, that's it."

**The rule.** A governing document's verdict may be signed by **any** of: the reviewer, the native, or
the Claude session. Who signs is not constrained. The one hard requirement is that **a review actually
happened** before the signature.

**What stays closed.** The defect that produced the older, stricter rule remains a defect: a verdict
stamped with **no review behind it at all**, or with its acceptance tests still pending, is void. The
original K3 finding was about a document carrying a verdict nobody had reviewed — not about which of the
three signs it. Review is mandatory; reviewer-identity for the signature is not.

**What this amends.** `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` §5.4 and its changelog carry
"THE REVIEWER ASSIGNS THE VERDICT, NOT THE AUTHOR" as an absolute. Under this ruling that line becomes:
"A verdict requires a completed review. The reviewer, the native or the session may sign it; a verdict
with no review behind it, or with acceptance tests pending, is void." The template must be brought into
line; until it is, this ruling governs and the template's stricter sentence is superseded in place.

**What it unblocks.** Nothing waits on a third party to countersign. A document that has been reviewed
can be signed and moved forward in the same session as its review, which is the normal case in this
campaign.

## 10 — The medical and mortality exclusions stay removed (governing fact)

**Ruling, native:** the medical/mortality exclusions are to be removed and to stay removed.

**The rule.** Āyurdāya (lifespan), constitution, vitality and vulnerability are **in scope** for this
product and for every layer of the data plane. They are served as the tradition serves them: the
applicable method and school, its required inputs, the cancellations each school applies, the
disagreement between authorities and the genuine uncertainty at every step — and **never as a bare
date**. No document, layer plan, asset brief, writer, serving surface or intermediary may re-impose an
exclusion on these subjects, and none may gate them behind an extra permission an ordinary domain
question does not need.

**Current state of the corpus under this ruling — already correct:**

| artefact | state |
|---|---|
| `MADHAV_PRODUCT_DEFINITION_FINAL` P23 (L165) | lifespan in scope as the classical discipline — correct |
| its changelog 3.1 | "REMOVED: the death, illness and fertility exclusions" — correct |
| `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL` V12 (L106) | serves āyurdāya with method, cancellations, disagreement, uncertainty — correct |
| same, §5 Ayurdaya row (L277) | the L0→L1→L2→L3→L4 hop chain with the tradition's caveats preserved — correct |
| same, §12.1 (L510) | "answered as V12 requires … never a bare date" — correct |

**The one residue that must go.** Data plane §5 L278 still reads "Horizon qualification cannot bypass
exclusions." The exclusions that sentence refers to no longer exist, which makes it the only remaining
hook by which the removed exclusion could re-enter a later document by reference. Delete it; the row's
surviving sentence ("Attributed guidance only; source testimony is not demonstrated remedial efficacy")
is the whole of what that row needs to say. This was raised as finding 12 of `REVIEW_DATA_PLANE_v3_0`
and again as finding 13 of `REVIEW_DATA_PLANE_FINAL_v1_0`; under this ruling it is no longer a tidiness
MINOR but the closing act of a governing fact.

**What it does not change.** The product still makes no medical diagnosis, prescribes no treatment and
gives no fertility guarantee — those were never exclusions of the *subject*, they are limits on the
*kind of claim* any domain may make, and they stand under the parent's §13 boundaries.

## 11 — "Is the astrology right" is not a data-plane obligation (governing fact)

**Ruling, native:** "I was the one who introduced that idea, but later I realized it is not the
responsibility of the data plane. Regarding astrology, the data plane basically is data engineering,
mathematical calculations, which is going to feed the layers above, and the last thing is astrology with
the LLM."

**The rule.** The data plane's job is faithful computation and faithful carriage: compute correctly,
hold the tradition's own testimony without corrupting it, and hand everything upward with its
conventions, prerequisites, exceptions and uncertainty intact. **The astrological verdict — whether a
reading is astrologically right — is formed above the data plane, in the reasoning layer.** The data
plane is therefore scored on **ten** of the product definition's eleven §14 obligations. Domain
correctness is the one it is not scored on, and that is a deliberate exclusion, not an omission.

**Raised and placed by the same person.** The native introduced Domain correctness into the product
definition on 2026-09-25 and, on review the same day, placed it at the correct altitude. The idea is
kept; its owner changes.

**What the data plane still owes, so nothing is lost by the move.** These are data checks, not
astrological verdicts, and they stay:

| check | where it lives now | why it is not "astrological judgment" |
|---|---|---|
| the stored rule is authentic, sourced, correctly identified and inside its method boundary | L0's existing **Source and domain fidelity** obligation (product §11) | it compares a record against its own cited source — a provenance check |
| a computed classical quantity reproduces when derived a second way | L1's existing **Computational correctness** obligation; the two-pass verification tiers already do this | it is arithmetic agreement, not interpretation |
| where two admitted sources disagree, the disagreement is **carried**, never silently resolved | DP02 "unresolved alternatives"; §4.3; §5's method-before-comparison rule | carrying a disagreement is transmission; settling it is judgment |

**What leaves the data plane:** the verdict itself, the seeded-counterexample suite, and any adjudication
between schools. Those belong to the reasoning layer and, when that layer is elevated to a governing
artefact of its own, they are its obligations to name.

**Consequences, in order:**

1. `MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL` §13.3's "**ten** proof obligations" is **correct** and
   must not be "fixed" to eleven. It must, however, state *why* it is ten — one sentence naming this
   ruling — or a future session will read the parent's eleven rows and correct it back.
2. §12.2's **Domain correctness test row** comes out of the data plane's test table. If anything replaces
   it, it is a carriage test: the cited passage, the witness set and its recorded disagreement, and the
   second derivation are all *present and handed onward*, unjudged.
3. `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` §2.7 and the `Dom` gate in its §5.2 instrument stop
   asking about doctrinal correctness. **Executed as a rescope rather than a deletion**, which is the
   faithful reading of this ruling as it was put: the native agreed in the same exchange that the
   *mechanical* checks stay inside the data plane, and two of the four were mechanical. §2.7 is now
   "Source carriage and reproduction — did we transmit it faithfully?", keeping source correspondence,
   witness carriage (the disagreement is carried, never averaged or silently settled) and independent
   re-derivation; the gate is renamed `Dom` → `Carr`; the verdict framing and the fourth check — seeding a
   case the tradition says must NOT fire, which is a doctrinal act — are removed and recorded as belonging
   to the reasoning layer's own artefact when that plane is elevated. `NO DETECTOR` is kept as an honest
   null. If the native prefers outright deletion of the section, say so and it goes.
4. The L0 instance (v2.1) never absorbed §2.7 — checked, no occurrence — so nothing is unwound there.
5. `MADHAV_PRODUCT_DEFINITION_FINAL` §14 keeps the Domain correctness row: the *product* must not be
   astrologically wrong, and deleting the row would lose a correct idea. It gains one line naming its
   owner — discharged above the data plane, in the reasoning layer. **Recorded as the recommendation and
   the default action unless the native rules otherwise.**

**Review bookkeeping.** This ruling supersedes finding 1 of `REVIEW_DATA_PLANE_FINAL_v1_0` (which
prescribed the opposite fix — adding the eleventh obligation) and withdraws its finding 12 (the
reference-layer fidelity list is correct as written, because fidelity is exactly the data plane's half of
the question). Both are re-stated in place there, with this ruling as the reason. The two remaining
blockers of that review — the unmarked cross-plane obligations and the unassigned synergy term — are
untouched by this ruling and still stand.

---

# v1.3 — decision 5 resolved, and decision 12

## Resolution of decision 5 — the ledger gap needs no production write

**Native ruling:** "I will go with your recommendation" — reconcile the ledger, then add the
automatic check. Both discharged below, and the reconciliation turned out to need no hand-written
write at all.

**Step 1 — every one of the seven re-verified live, read-only, 2026-09-25 by this session.** Not
inherited from the earlier measurement; re-run against production:

| migration | effect asserted | verified in production |
|---|---|---|
| 1080 | `gochara_resonance_map.target_resolution_state` + `target_qualifier` | 2/2 columns LIVE |
| 1081 | `kala_gochara_convention` / `_publication` / `_contacts` / `_coverage` | 4/4 tables LIVE |
| 1082 | `kala_vedha_gochara` + `kala_moorti_nirnaya` stamp columns | 6/6 columns LIVE |
| 1083 | `contact_id` on `brahma_prospective_ledger` + `mimamsa_predictions` | 2/2 columns LIVE |
| 1084 | `ka_kshetra` + `ka_sangam` carry `ka_vedha_gochara` in `depends_on` | 2/2 rows LIVE |
| 1087 | `kala_gochara_contacts` inclusivity / completeness_state / tier_basis / comparable_with | 4/4 columns LIVE |
| 1091 | `ka_gochara` `count_sql` pinned to generation 4.0 with 8 `depends_on` edges | 1/1 row LIVE |

`SELECT count(*) FROM _migrations_applied WHERE filename ~ '^(108[0-9]|109[0-5])_'` = **0**. The
ledger's highest numbered row is **1079** (applied 2026-09-22); 869 rows total.

**Step 2 — the boundary that changes the plan: all seven are re-runnable.** Read at
`l3/gochara-autonomous-wp0-7:platform/migrations/`: 1080, 1081, 1082, 1083 and 1087 are
`IF NOT EXISTS` DDL throughout; 1084's two `UPDATE`s are guarded by
`AND NOT (depends_on @> ARRAY[...])` and the file documents itself as idempotent; 1091 is
`CREATE TABLE IF NOT EXISTS` + `INSERT ... ON CONFLICT (asset_id) DO NOTHING` + absolute `SET`
assignments.

**Therefore no row should be hand-inserted into production.** The deploy runner will apply each one
(no-op, or convergent to the state already there) and **write the ledger row itself**, with the
sha256 and `sql_identity` it computes from the committed file — which is the identity the runner will
later re-verify. A hand-written row would assert a hash for a body nobody watched execute; letting
the runner do it is the same reconciliation through the sanctioned path, and it is strictly better
evidence. This supersedes the earlier session's prepared-but-unexecuted INSERT of seven rows: that
statement should be discarded, not run.

Two caveats, stated rather than buried:
- **1091 re-applied would overwrite later edits** to `ka_gochara`'s `count_sql` / `clear_tables` /
  `depends_on`, because its `SET` is absolute. Verified 2026-09-25: production already holds exactly
  what 1091 sets, so re-running is a literal no-op **today**. If anything edits those three fields
  before the deploy, re-check before merging.
- **These files carry their own `BEGIN`/`COMMIT`,** so under the runner's outer transaction the inner
  `COMMIT` ends it early and the ledger INSERT lands in its own statement. The two are therefore not
  atomic with each other. That is a pre-existing property of every migration in this repository that
  wraps itself, not something these seven introduce, and it does not change the outcome.

**What still blocks the deploy** — unchanged by this resolution and still decision 4/7 territory:
`migration_number_guard` hard-fails on **1071/1072 existing twice** (Saṅgam and B1). Note for
completeness: 1071/1072's effects are **not** live (`kala_convergence_episodes` absent,
`kala_convergence.target_provenance` absent), so those two are genuinely unapplied — "unrecorded" and
"unapplied" are different states, and conflating them is what made the original report misleading.

**Step 3 — the detector, written and proven:**
`platform/scripts/governance/check_migration_ledger_vs_production.py`. For every migration file with
no ledger row it extracts the objects the file asserts (tables, added columns, indexes, functions —
comments stripped first, so a rollback recipe in a comment block is never read as an assertion) and
asks the catalog whether they already exist. All present → `applied_but_unrecorded` (HIGH). Some
present → `partially_applied_unrecorded` (HIGH, worse). None → genuinely pending, clean. No
introspectable object → `indeterminate` (LOW), never clean. **Unreachable database exits 4 UNKNOWN
and reports nothing clean** — §N.8 applied to the check itself.

Proven, not asserted: run against the seven files it reports six as `applied_but_unrecorded` (2/2,
11/11, 7/7, 2/2, 2/2, 1/1 objects live) and 1084 as `indeterminate` — correct, since 1084 is a pure
`UPDATE` with no object to introspect. Run against this branch's own migration set it reports 1071
and 1072 as genuinely pending, which matches the live check above. Unreachable-DB path tested: exit 4.

## 12 — `bg_sarvatobhadra_grid`: the school is named (delegated pick)

**Native ruling:** "I will let you make the pick. Think through this, do some research and go with the
most popular among the options."

**Pick: `muhurta_chintamani`** (Rāma Daivajña's Muhūrta Cintāmaṇi) as the first `school_tag`.

**Why, on the evidence rather than on taste:**

1. **Most current of the three recorded candidates.** `bg_gochara_citation_resolution` (migration 565)
   names three, all `status='unresolved'`: Muhūrta Cintāmaṇi and Jyotiṣa Sāra Saṅgraha for the
   28-nakshatra 9×9 grid, and Praśna Mārga for the rekha/kona/vīthi vedha geometry. Muhūrta Cintāmaṇi
   is the standard muhūrta authority in practice — the one routinely cited for Sarvatobhadra vedha in
   muhūrta work; Jyotiṣa Sāra Saṅgraha is a compilation with far less currency; Praśna Mārga is a
   praśna classic whose vedha construction is a *different* geometry, not a variant of the same grid.
2. **It is the only one we hold any of.** `classical_text_chunks` carries 15 texts;
   `muhurta_chintamani` is one of them (274 chunks). Jyotiṣa Sāra Saṅgraha and Praśna Mārga are absent
   entirely — Praśna Mārga is not even present as a `text_id`. So this pick extends an existing
   ingestion and its rights position rather than opening a new one.
3. **It forecloses nothing.** `school_tag` is designed to hold competing variants side by side; Praśna
   Mārga's geometry can be seated later under its own tag without disturbing this one.

**What the pick does NOT do, measured before claiming it:** it does not populate the table. The 274
chunks we hold contain **zero** occurrences of "sarvatobhadra" and one of "vedha" — the chapter
carrying the chakra is not in the portion ingested. (Checked the obvious alternative too: Brihat
Samhita's four "sarvatobhadra" hits are OCR noise from an index of scents and from temple-architecture
verses, not the nakshatra chakra.) So the pick converts an open ruling into **one bounded task**:
ingest and verify the Muhūrta Cintāmaṇi chapter that carries the grid, then seat the rows under
`school_tag='muhurta_chintamani'` with real citations.

**Until then, nothing changes and nothing lies:** the table stays deliberately empty, and
`ka_vedha_gochara` keeps serving its `algorithmic_approximation` with `uncited_extension=true` on every
row. One populated `school_tag` row switches its DB-grid path on with no code change — the consumer is
already wired and waiting.

---

# v1.4 — decision 13, and the chart_facts investigation

## 13 — Tiers 1 to 3 of the elevation chain are SEALED

**Ruling, native:** "Set the template to final. Seal the product definition strategy, data plane
definition strategy and layer template. The three things open are layer instance, asset template,
asset instance."

**Done.** The layer template's version is now `FINAL` (it was 1.2; numbered versions stop there, and the
filename keeps `_v1_0` so the instances and reviews citing it do not break). All three documents carry
`status: SEALED` and a `seal:` block naming the seal date, the authority, the review it rests on and the
reopen rule. The seal record, with each document's exact sha256 at seal and the review behind each, is
`00_ARCHITECTURE/briefs/nirmana/ELEVATION_CHAIN_SEAL_2026-09-25_v1_0.md`.

**What makes the seal real rather than a word:** the same three hashes sit in `CAPABILITY_MANIFEST.json`
per entry, and `drift_detector.py` recomputes and compares them every run. A silent edit to a sealed
document becomes a HIGH finding on the next pass. There is no other mechanism and none is needed.

**Open beneath the seal, exactly as the native named them:** the layer instance (L0 is
`REVISED_PENDING_REVIEW`; L1–L5 unwritten and held by decision 8), the asset template
(`ASSET_ELEVATION_TEMPLATE_v1_0.md`, v1.1, unsealed), and the asset instance (per-asset briefs).

**Consequence worth stating once:** the numbers above the line are now settled — ten obligations for the
data plane, ten layer-plan elements, eight dispositions, six evidence states, five edge types. A session
that "corrects" one of those has broken a seal, not fixed a document.

## Resolution of the chart_facts verification-status finding

**Native instruction:** "Please go ahead and look at it."

**It is a false positive, and the gate was the defect.** Measured against production 2026-09-25:

| verification_pass_status | rows | in the settled vocabulary? |
|---|---|---|
| `single` | 356,286 | yes |
| `two_pass_verified` | 32,650 | yes (the only member meaning a detector ran that could have said otherwise) |
| `computed_extension` | 11,385 | yes |
| `single_pass` | 10,937 | yes |
| `floored` | 7,095 | yes |
| `documented_approximation` | 2,410 | yes |
| `pending_w3_verification` | 150 | yes |
| `not_defined_for_nodes` | 96 | yes |
| `divergent_flagged` | 45 | yes |
| `classical_match` | 42 | yes |

Ten distinct values live, every one a member of `brahmagyan/verification_vocab.py`'s thirteen. The
drift gate was comparing against its own **four-value copy**, so the six legal members it did not know
about summed to exactly the 32,073 rows it reported as violations — 11,385 + 10,937 + 7,095 + 2,410 +
150 + 96 = 32,073. The arithmetic matches the complaint exactly, which is the proof.

**The real defect in that class is already closed:** `pass` / `PASS` are prohibited by `assert_legal()`,
and production carries **zero** of them today. The vocabulary's own docstring had named this situation
and routed it as a residual — "a seventh copy … raises a HARD violation for 56,028 live rows, of which
only the 5,428 `PASS` rows are the real defect." Those 5,428 are gone. What was left was a permanently
red gate that could no longer tell a legal value from a violation, which is the one thing a gate is for.

**Fixed, not whitelisted.** `drift_detector.py` now reads the vocabulary from its single source of truth
(three hardcoded copies removed — two sets and one inline query list, all in the same file), fails
**closed** if that module cannot be imported (an unreadable authority is not a clean result), and adds a
separate **CRITICAL** check for the prohibited spellings, which the old four-value set could not
distinguish from an unknown value. Same doctrine the day has been about: §4.1 rule 6, one map per class;
§N.7 item 3, no wrapper-local constant may shadow a source value. Result: the HIGH finding is gone, the
A3 unit tests pass (5/5), and 0 CRITICAL confirms no prohibited spellings exist.

## Left for the native — the twelve missing materialized views

The other HIGH finding is also stale, but fixing it is a design call, not a transcription, so it is
recorded here rather than changed. `drift_detector.py` demands twelve `mv_*_facts` materialized views and
tells the reader to "apply migration `138_mvs.sql`". That migration is **archived**
(`platform/migrations/_archive/138_mvs.sql`), it is not in the ledger, and **none** of the twelve views
exists — while 25 other materialized views do exist and serve. So the gate is asserting an A3 design the
system no longer has.

Two honest options, native's call: **build them** (if the A3 fact-view design is still wanted), or
**retire the expectation** from the check and name whatever replaced it. What should not continue is a
gate demanding views from an archived migration — that is the same defect as the vocabulary copy, one
layer over.

---

# v1.5 — decision 14, delegated

## 14 — The twelve A3 materialized views: expectation corrected, three not built

**Native instruction:** "I want you to decide for myself and do the needful and wrap this out."
Decided and executed; the reasoning is recorded here so the decision can be overturned on its merits
rather than re-litigated from scratch.

**Decision: do not build the absent views. Correct the gate to assert the eight that exist and are
read.** Done in `platform/scripts/governance/drift_detector.py`.

**What was actually true, measured before deciding:**

| claim the gate made | what the evidence says |
|---|---|
| twelve `mv_*_facts` views are missing | those twelve names exist in **no** database, **no** code, and **not even in the migration the gate names** — they came from `A3_CHART_FACTS_SPEC_v1_0.md`'s prose while the implementation used `mv_chart_*_summary` |
| "apply migration `138_mvs.sql`" | that migration is **archived** (`platform/migrations/_archive/`) and absent from the ledger |
| nothing of that design exists | **eight of the twelve views the archived migration really declares are live, populated and consumed** |

The eight, each referenced by 4–8 files and all holding rows today: `mv_chart_planet_summary` (50),
`mv_chart_shadbala_summary` (42), `mv_chart_vargas_summary` (1,550), `mv_chart_ashtakavarga_summary`
(520), `mv_chart_bhava_bala_summary` (60), `mv_chart_sensitive_points_summary` (1,515),
`mv_chart_panchanga_birth_summary` (386), `mv_cross_ayanamsha_consensus` (20,043).

**Why the four absent ones are not built** — `mv_chart_arudhas`, `mv_chart_house_summary`,
`mv_chart_sahams`, `mv_chart_yogas_active_at_birth`:

1. **Nothing reads them.** They appear only in planning documents — the A3 spec, the old conductor
   implementation plan and its session queue. Not one line of application code refers to any of them.
2. **The fourth already has a successor.** `mv_chart_yogas_fired_summary` exists, is populated and is
   read; it does that view's job under a truer name (fired, not merely "active at birth").
3. **Product doctrine says not to.** A materialized view is a stored snapshot that must be refreshed on
   every build. Building one with no consumer buys a recurring refresh cost for no earned distinction —
   precisely what §14.1's ablation rule exists to prevent ("an asset that cannot be ablated because
   nothing reads it has already answered the question"). The underlying facts remain fully queryable
   from `chart_facts`; what would be added is speed no caller has asked for.
4. **Reversible in an afternoon.** If a consumer appears — an arudha surface, a house-summary panel, a
   Tājaka saham reader — the view is one small migration and one row in the gate's list. The note at
   `MV_NAMES` says exactly this, so the next session does not have to rediscover it.

**Two detectors came out of it, both able to fail:**

- The gate now asserts the **eight consumed views**. If one disappears or is dropped, that is a real
  HIGH finding with real consequences (live readers break) rather than noise about names nobody used.
- New: **`a3_materialized_view_never_refreshed`** (MEDIUM). A view that exists and holds zero rows while
  `chart_facts` is populated is a snapshot nobody refreshed — an answer-shaped object with no answer in
  it, which is the §N.8 class one layer over, and worse than an error because the reader is served a
  confident empty result. All eight pass today; the check would catch the day one stops being refreshed.

**Result:** the drift detector reports **0 CRITICAL, 0 HIGH, 0 MEDIUM** against production. The single
remaining LOW is the soft, by-design one (73 schema categories whose writers are added incrementally).
