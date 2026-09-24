---
artifact: GOCHARA_NATIVE_RULINGS_2026_09_24
canonical_id: GOCHARA_NATIVE_RULINGS_2026_09_24
version: "1.0"
status: NATIVE_AUTHORIZED
date: 2026-09-24
authority: >
  Issued by the native (Abhisek Mohanty) through the L3 Gochara execution session under an explicit
  delegation of 2026-09-24: "I'm good with all the points that you have mentioned, left in the run no
  authorization needed / waiting on you — I would like you to respond to all of this on my behalf. I
  don't want to put guards, so I think we should be ready with tranche two. … Just assign somebody and
  get the review done. … once the complete thing is ready, you can get it reviewed by Kimi."
  Every ruling below is the native's. Any item the native later names as excepted reverts to PROPOSED
  for that item only.
rules: "D-S1..D-S6 (GOCHARA_SYNERGY_RESPONSE_v1_0.md) · M-1 value ratification (WP8_M1_ORB_BATTERY_v1_0.md) · A-2 tranche 1 · A-3 tranche 2 · O-1/O-2/O-3 owners · binding B8 items that are this family's"
supersedes_in_scope: "the 'awaiting the native' status of the items named; GOCHARA_RULING_SHEET_v2_0.md is otherwise unchanged and still governs"
---

# Native rulings, 2026-09-24 — the Gochara family's open decisions, closed

## 0. Scope

This sheet closes every Gochara item that was waiting on the native as of 2026-09-24 03:00 IST. It
rules the six synergy decisions, ratifies the M-1 activity shape and its value, authorizes both WP10
tranches, and names the O-class owners. It does not change any ruling on
`GOCHARA_RULING_SHEET_v2_0.md`; where it touches one (M-1's value, A-2, A-3) it supplies the decision
that sheet left to the native.

## 1. Synergy decisions D-S1..D-S6 — all RULED

| id | ruling | note |
|---|---|---|
| **D-S1** | **APPROVED.** Fold the conformance fixes into the brief as §4.13: (a) `find_episodes` returns a `coverage` object on **every** branch, not only `moon=True`; (b) an `inclusivity` column on `kala_gochara_contacts`, CHECK ∈ {`closed_closed`,`closed_open`}, value **`closed_closed`**, because both `t_in` and `t_out` are in-orb threshold-crossing instants; (c) the `primitives.py:193-194` comment corrected to record that its BPHS Ch.26 citation is refuted by F-29 and the entry is retained **only** for the legacy arm of flag `nodal_drishti`; (d) a per-call node-mode assertion in this family's own readers — every node longitude read asserts `RAH_MEAN`/`KET_MEAN`, never `TRUE_NODE`, and raises rather than degrades | additive migration, next free number by scan; disposable DB only |
| **D-S2** | **APPROVED with the F06 rename.** `completeness_state` CHECK-constrained to the six F06 states `{applied, inapplicable, unavailable, unqualified, contradictory_unresolved, unexplored}`; the live `qualified` migrates to **`applied`**; the λ-decomposition key `removed_by_ruling_N14` becomes `completeness_state: 'inapplicable'` plus a sibling `removed_by_ruling: 'N-14'`. CHECK-constrain `time_basis` and add `tier_basis TEXT` CHECK ∈ {`relative_uncalibrated`, `calibrated:<gate_id>`}. `inapplicable` stays **out** of `target_resolution_state` (N-12 / WP3c R-1 stands) | one migration with D-S1; `ledger.py`, `episodes.py`, `interval_solver.py`, `resolution_hierarchy.py` and the tests follow |
| **D-S3** | **APPROVED.** `KALA_SYNERGY_BINDING_v1_0` §B1–B7 adopted by reference in the brief §1, each OFFER/DEMAND proved in the packet proof matrix with the binding's tests 5, 6, 7 and 9, each with a negative fixture that makes the detector fire. B6 is adopted as written: this family is the **sole contact-episode producer**; Kṣetra's episodes are Kṣetra's to reconcile | a green run that could not go red does not count |
| **D-S4** | **APPROVED as the producer's recommendation: one name, `precision_regime`.** Three rulings already name it (Kṣetra 8, this family's G-9, Saṅgam M-3). `kala_gochara_contacts.claim_grain` is **renamed `precision_regime`** in the migration, `ledger.py`, the kernel dataclasses and the tests **before that migration is ever applied outside a disposable DB** — so no alias generation is needed and nothing served ever carried the old name. Values `{instant_grain, date_grain}`, pinned in `WP1_CONTRACTS.md` §3.1. `day_grade` is aliased to `date_grain` **until the successor condition of Saṅgam D-7 is met — every dependent claim has an authorized successor — not for a count of generations** (binding 2.2 §B1, verified at `8211c2dc6`) for Kṣetra's benefit | this is binding B8-9, answered |
| **D-S5** | **APPROVED.** No new `target_type`. The cross-asset handle is `window_ref = {asset_id: 'ka_gochara', generation, id: contact_id}`, resolving against the existing PK `(chart_id, generation, contact_id)`. Documented in `WP1_CONTRACTS.md` §5 and in packet C-1's contract, with one test that resolves a `window_ref` against the PK. **Plan R2 stands**: this family imports nothing from Kṣetra or Saṅgam | this is binding B8-3, answered |
| **D-S6** | **DECLINED, as recommended.** `unstable_key` is **not** admitted to `comparable_with`; the enum stays at the four values pinned at WP1 §6. It names a property of one row's identity, not a relation between two rows, and admitting it would let a row assert a comparability class while being unfindable across rebuilds. Kṣetra's interim belongs in two places the contract already has: `NOT_RUN` with reason `unstable_key` on the comparison record, and F06 `unqualified` on the row's identity claim until its content-addressed key lands. If Kṣetra wants it machine-visible on its own rows, an additive `id_basis ∈ {content_addressed, surrogate_unstable}` column on its own table touches no Gochara contract | relayed to Kṣetra |

**Binding B8 items that are this family's:** B8-1 (sha256 identity) and B8-2 (`generation` in the PK)
are **ratified** — already this family's practice in migration 1081. B8-5 (the seven-field coverage
shape) is **ratified**. B8-3 = D-S5. B8-8 = D-S2. B8-9 = D-S4. B8-6 is ratified in this family's
favour per D-S3. B8-4, B8-7 and B8-10 are Saṅgam's and Kṣetra's and are not ruled here.

## 2. M-1 — the activity shape and its value, RATIFIED with the value split across two candidates

**Evidence read before ruling:** `WP8_M1_ORB_BATTERY_v1_0.md` v1.0, eight passing tests, six arms plus
three plateau neighbours, two synthetic workloads. The report's own §7 declares two things that this
ruling takes at face value: recall **ties 3/3 on every arm** because the synthetic anchors are
saturated by construction, and the sheet's literal exit gate ("a narrower orb only if it beats
5.0°-no-box on recall AND range") is therefore **not met**.

**Ruling:**

1. **Shape — RATIFIED.** The activity term becomes **linear in separation with no time box**:
   `activity = 1 − |Δ| / orb_max_deg`. This was already M-1's ruled direction; the battery supports it
   on every λ-margin (anchor A 0.040 → 0.106 at 5.0°) and on peak/median dynamic range (1.32 → 1.61)
   at equal recall and equal-or-fewer active days. The legacy ±5-day box is retired as a *shape*.
2. **Value, first `'4.0'` candidate — `orb_max_deg = 5.0`**, the declared fallback. Reason: the first
   candidate's whole purpose is a factor-level delta report against `'3.0'`. At 5.0° the battery shows
   the window structure essentially unchanged (195 vs 196 active days, 14 vs 14 windows) while the
   margins and dynamic range improve — so candidate 1 **isolates the shape change** and the delta
   report is interpretable. Narrowing the orb fivefold *at the same time* would change two variables
   at once and make the report unreadable, which is the opposite of what A-3 asks for.
3. **Value, second candidate — `orb_max_deg = 1.0`, carried, not yet ratified.** The battery's own
   recommendation, and the ruling accepts its reasoning as far as synthetic evidence can carry it:
   1.0° has the best peak/median ratio of the non-knife-edge arms (1.6294), holds plateau stability
   across its 0.5×/2× neighbours, resolves the Δ=8 envelope clusters into distinct windows without
   fragmenting Δ=3 single events, and does not inflate the ordinary quarter (56 ≤ 85). **0.5° is
   rejected outright** for failing plateau stability (0.25° halves its window count 22 → 16). 2.0° is
   the recorded runner-up. The 1.0° candidate is ratified **only** on the factor-level delta report of
   candidate 1 against `'3.0'` on the real canonical chart, where recall can actually discriminate. A
   synthetic battery whose recall metric cannot go red is evidence about shape, not about width.
4. This satisfies A-3's "WP8 M-1 ratified by the native in the sheet OR the declared fallback used" —
   both, in sequence, and stated as such.

## 3. WP10 — both tranches AUTHORIZED

**A-2 / tranche 1 (runbook steps 0–5): AUTHORIZED.**
**A-3 / tranche 2 (runbook steps 6–10): AUTHORIZED.**

Both frontmatter flags in `GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md` are set `true` by this ruling.
This is the fresh production authorization that plan §12, sheet A-2/A-3 and the 2026-08-21 standing
order require, given in advance for both tranches so the run does not stop between them.

**What this authorization does NOT do — read this before step 0.**

- **It does not weaken a single guard.** The native's instruction "I don't want to put guards" removes
  the *authorization* gates, not the *database* guards. The `(table, generation)` guard, the Phase 1.1
  Clear `is_active` filter, `EXPLICIT_CLEAR_OPS`, the writer's refusal to delete-then-insert against a
  `published` generation, and the four flip gates all **remain in force and are built, not bypassed**.
  They are the deliverables of steps 0 and 5 and the reason the tranche is safe to run at all.
  Weakening a guard remains forbidden.
- **It does not remove the evidence preconditions**, which are gates on *truth*, not on permission:
  each step writes its evidence file before the next begins; tranche 2 still requires tranche 1's
  evidence green, P-1 merged, WP9 §5.2 merged, N-19's artifacts on `main`, and M-1 ratified (now
  satisfied by §2). A failed gate stops the tranche, writes the evidence and escalates. **A failed flip
  gate yields a new candidate, never a patch.**
- **It does not authorize touching protected data.** `kala_gochara_windows` where
  `generation IN ('v1','3.0')` and `_v2 g3_*` stay untouched; `'3.0'` remains the rollback surface and
  is never regenerated.
- **It does not extend scope.** The brief §3 hard list, including `pipeline/transit_search.py`,
  `platform-mcp/src/tools/kala_views/**`, `brahmagyan/l0_ephemeris.py`, `services/ka_dasha_kala/**` and
  `services/ka_kota_chakra/**`, is unchanged.
- **Step 0 consumes, not duplicates,** `origin/l3/kala-p1-1-b1-clear-guard`.
- The authority flip is the last act of step 8 and is logged with `evidence_ref = manifest_id`.

## 4. O-1 / O-2 / O-3 — owners NAMED

Why this mattered rather than being a formality: every one of these three roles exists to keep a
*claim* separate from the *party that made it*. O-1 is who is accountable for the evidence; O-2 exists
because the brief §9 forbids the implementer from grading its own work, which is the single defect
class this whole campaign was built to end; O-3 exists because Kṣetra's rulings 7, 8 and 9 rest partly
on corpus counts **this family supplied and twice had to correct**, so the re-count must come from
someone who did not make the original error. Leaving them unnamed was not a paperwork gap; it meant
three claims had no one standing behind them.

| id | role | owner named |
|---|---|---|
| **O-1** | implementation owner per packet | **the Gochara remainder run** (`l3/gochara-autonomous-wp0-7`), already the implementation owner by the brief's own scope extension. Discharged for P-1..P-4, S-1/S-2, T-1, C-1, V-1, K-1 — all landed with a `REVIEW_REQUEST_*.md` each. No further naming needed |
| **O-2** | independent reviewer per packet, not the author | **Kimi K3 at max effort**, run by the L3 Gochara session as the review + reconciliation loop, on the **whole** remainder campaign once the run reports complete — the same loop that reviewed the plan and the decisions. Per the native's instruction of 2026-09-24. Nothing is marked `REVIEWED` by the implementer |
| **O-3** | a fresh session for Kṣetra rulings 7/8/9, instructed to re-run the corpus counts | **a fresh independent session, dispatched 2026-09-24 by this session**, instructed to re-derive every count from the served table `classical_text_chunks` by `count(*)` with a stated predicate, never from `SOURCE_DATA/classical_texts/` and never from a search tool, and to report `NOT_RUN` honestly where it cannot reach the corpus rather than infer a number. Its report is `KSHETRA_RULINGS_789_INDEPENDENT_RECOUNT_v1_0.md` |

## 5. What each stream is told, and by whom

- **Kṣetra** receives `KSHETRA_INSTRUCTIONS_FROM_GOCHARA_2026-09-24_v1_0.md` — three items: retire the
  duplicate vedha and mūrti producers per its own ratified rulings 8 and 4; reconcile its contact
  producer against this family's kernel; take the D-S6 answer on `unstable_key`. Plus one item that is
  not this family's to rule but is the layer's most serious open correctness defect, flagged as such.
- **Saṅgam** receives `SANGAM_INSTRUCTIONS_FROM_GOCHARA_2026-09-24_v1_0.md` — one item: consume the new
  `find_episodes` so the node convention unifies on mean, with the interim stamp until it lands.

## 6. Recorded honestly

Nothing in this sheet was measured by this session against real production data. The M-1 evidence is
synthetic and says so; §2 rules accordingly and refuses to let a synthetic metric that cannot go red
decide a fivefold narrowing of the served activity window. The tranche authorization is a permission,
not a claim that any step has passed — every step still earns its own evidence file.

## 7. Addendum, 2026-09-24 afternoon — three corrections received from the L3 strategic session, each verified here

The strategic session (now `madhav-a6`, formerly signing as `madhav-fc`) reported three items after
this sheet was issued. Each was checked at source before being accepted.

1. **Current layer-artifact versions.** Binding **2.2**, amendments **2.1**, audit **1.5**, blueprint
   **4.8**, at `8211c2dc6` on `origin/l3/kala-elevation-readiness` — verified by reading the files at
   that commit. §1's D-S3 adoption is unchanged in substance; the brief's §12.4 pointer is updated from
   `5c05a0e2f` (2.0) to `8211c2dc6` (2.2), with the standing instruction to read the live file rather
   than any quoted version. Binding 2.1 recorded this family's `find_episodes` precision; 2.2 recorded
   D-S6's decline of `unstable_key`.

2. **The `day_grade` alias wording was wrong here, and is corrected.** This sheet's D-S4, the brief's
   §12.3 4.13e, and both stream instruction files said the alias holds "for one generation, then
   retired". Binding 2.2 §B1 says something different and says it deliberately: `day_grade` is aliased
   to `date_grain` **until the successor condition of Saṅgam D-7 is met — every dependent claim has an
   authorized successor — and explicitly not for a count of generations.** The original wording came
   from binding **1.0**, which did say "one generation"; it was superseded and this sheet carried the
   stale form forward. Restating a ruled condition as a generation count is itself a ruling change,
   which is the defect class the layer's governance verifier exists to catch. All four files are
   corrected to the ruled condition. `[S]` verified at `8211c2dc6`.

3. **Migration numbers: 1082 is taken by this family, and 1085/1086 are now double-claimed.** A full
   re-scan of every `origin/*` head plus this local head, 2026-09-24, gives:

   | number | this family | another stream |
   |---|---|---|
   | 1080, 1081 | resonance target state; ledger/coverage/publication | — |
   | 1082 | WP9 vedha/mūrti stamp columns | — (the strategic session's relay had told Kṣetra 1082 was free; it is not) |
   | 1083, 1084 | L5 ledger contact_id; WP7 K-1/V-1 registry edges | — |
   | **1085** | `1085_nirmana_l0_bg_transit_rules_vedha_repair.sql`, first committed **08:54 IST** | `origin/sangam/stage3` `1085_kala_convergence_kernel_fields.sql`, **11:25 IST** |
   | **1086** | `1086_nirmana_l0_gochara_g10_ga_strength_contributor_digest_spec.sql`, **11:21 IST** | `origin/sangam/stage3` `1086_kala_convergence_r5_identity.sql`, **11:42 IST** |

   **Highest prefix anywhere: 1086. The next free number is 1087**, by scan, and it must be re-scanned
   again before any file claims it.

   **Disposition offered to Saṅgam, not imposed.** This family claimed both numbers first, by two and a
   half hours and by twenty-one minutes respectively, and **neither of this family's files has been
   applied outside a disposable database**, so either side *can* still move. The rule this family
   proposes, and will abide by in reverse: **whichever side has already applied its file to a shared
   database keeps the number**, because a migration is never renumbered after it is applied; if neither
   has applied, first claim holds. Saṅgam is asked to state its applied-state. If Saṅgam's 1085/1086
   are applied anywhere shared, **this family will renumber its own two** to the lowest free numbers at that time ~~to 1087/1088~~ **[STALE — DO NOT USE 1087/1088: Saṅgam now holds 1088; see §7.10]** rather than ask
   Saṅgam to break the never-renumber-after-apply rule. Recorded rather than acted on unilaterally,
   because acting first is what produced this collision twice already.

### 7.4 Correction to §7 item 3, same day — the 1085/1086 disposition is withdrawn

Saṅgam (`madhav-11`, the `ka_sangam` stream) replied and was right. Duplicate prefixes across
`platform/migrations/` and `platform/supabase/migrations/` are **already routine**: a count on
`origin/main` gives **30** numbers claimed in BOTH live directories (see §7.7 — an earlier figure of 55 stated here was this session's own measurement error). The runner keys on filename plus sha256, never on number,
and orders duplicates numerically then lexically. Two files sharing 1085 in different directories, with
different names and no dependency, are benign. **Nobody renumbers; both sides keep their numbers**, and
the applied-state question put to Saṅgam is moot and withdrawn.

The distinction worth keeping: the earlier 1075/1076 renumber was right for a reason that does not apply
here. There, the colliding L0 files were applied to production *and* a ruled step in this family's sheet
read "migrations 1075/1076 applied and verified", so the duplicate would have let a routing be read as an
outcome. No ruling text names 1085 or 1086, and neither side's file is applied. **Renumber for a specific
misreading, never for the mere fact of a shared number.** This session over-applied the earlier lesson and
records it.

Saṅgam has since taken **1087**; the next free number is **1088** by scan, re-scanned before claiming.

### 7.5 Second addendum, 2026-09-24 — scope authority for three migrations, the settled number map, and two corrections received

**A. Scope authority for the L5- and L0-prefixed migrations on this branch** (asked by the strategic
session, answered here so no later reader has to infer it). All three are authorized by the
**2026-09-23 brief**, not by the 2026-09-24 delegation, and **none is applied to any database**:

| file | authority | applied? |
|---|---|---|
| `1083_l5_ledger_contact_id.sql` | brief §6 packet **P-3**, under the brief's own `scope_extension` naming this run the implementation owner of the eight WP7 packets. Its header says so: "L5 ledger contact_id — frozen-claim identity chain (WP7 P-3)" | no |
| `1085_nirmana_l0_bg_transit_rules_vedha_repair.sql` | brief §8.4, whose wording is explicit: "**G-9 repair as a migration file (L0 data; file only)**". Writing the file is in scope; **applying it is not, and has not happened** — the file's own header states "Applied to a disposable docker Postgres only; unapplied to any shared DB" | no |
| `1086_nirmana_l0_gochara_g10_ga_strength_contributor_digest_spec.sql` | brief §8.5, "G-10 (**L1**) — design + migration + writer change, carefully" | no |

**Filename defect, recorded:** 1086's basename says `nirmana_l0_` but its content is an **L1** change —
`ga_strength_writer`'s `chart_facts` category `ashtakavarga_bindu_contributor` and its output-digest
contract. The brief calls G-10 L1 and the file agrees in substance. The `l0_` in the name is wrong and
could route this to the wrong owner. It is unapplied, so **rename the file to an `l1_` basename** as part
of §12.3; a filename is not a number, so no numbering rule is engaged.

**B. The migration map, settled.** Saṅgam renumbered its three files rather than keep contested numbers,
and this session verified the result at source rather than take it on report:

| range | owner | note |
|---|---|---|
| 1080–1086 | this family | 1085/1086 retained; Saṅgam moved instead |
| **1087** | **free** | released by Saṅgam's renumber; it was double-pointed for about twenty minutes today, so anyone taking it must re-scan first |
| 1088–1090 | Saṅgam | `kala_convergence_kernel_fields`, `_r5_identity`, `_comparable_with` |
| 1091+ | free | max prefix anywhere is 1090 |

Saṅgam accepted the first-claim rule in the direction that cost it, having independently re-verified this
family's commit times, and its own applied-state answer ("both endpoints refused all session") is
consistent with its session-close record written before the question was asked. §7.4's withdrawal of the
*question* stands; the *outcome* is Saṅgam's choice, not this family's demand, and this family does not
ask anyone to renumber again.

**C. Correction received from Kṣetra, accepted: the t-axis defect is not unmentioned.** This family's
instruction file said Kṣetra's packet does not mention it. Wrong: it is Kṣetra plan §2 item 00 and
stage-3 Phase 1 item zero, measured live on 2026-09-23, ahead of ruling 9's G3. It is also **larger**
than this family described — the knot sources are not merged with a missing offset; `dhara_sweep.py:66`
**excludes the roots by design**, and every knot source (stage-0 roots, stage-1 primitives, stage-3
boundaries) is J2000 while the sweep, evaluator and writer clip and partition as birth-relative `[0, H]`.
The Kṣetra instruction file is corrected.

**D. Correction received from Kṣetra, accepted, and it lands on this family's own plan.** Plan §5.4
asserts that Phaladīpikā Adhyāya XXVI śl. 48 at PG345–PG348 is "a full primary construction of the
Sarvatobhadra-cakra", and concluded that SBC is therefore "an L0 population task with page anchors, not
a doctrine gap". **The L0 repair attempted exactly that construction from PG345–354 verbatim and was
blocked** (PR #2727 item 4); Kṣetra's matching "buildable from prose" claim is withdrawn on its record.
The honest status is now: the passages exist and are cited correctly, **and the grid is not reconstructible
from that prose as it stands**. Plan §5.4's conclusion is downgraded to `[U]` pending whoever attempts it
next with more than the prose. Recorded here rather than quietly left standing, because this family
supplied the claim.

**E. New work for this family, from Kṣetra's C3 finding — verified at source.** `ka_vedha_gochara`'s
writer reads `bg_transit_rules` (`writer.py:106`) and copies each rule's citation **verbatim**
(`writer.py:236`), but **fingerprints no upstream input**. So the canonical chart's 132 `house_vedha`
rows are still the 2026-09-07 build and still cite "BPHS Ch.29" after the L0 re-citation, the 24
sarvatobhadra rows cite Prasna Marga, and **nothing in the system detects that the rows disagree with
their own source**. That is §N.8 exactly: the citation is asserted and no detector could ever find it
stale. It also threatens tranche 2 directly — a `'4.0'` candidate built on those rows would publish
refuted citations. Added to the brief as §12.9. Kṣetra is right to consume only rows rebuilt after the
re-citation.

### 7.6 O-3's independent re-count has returned, and it corrects this family's own citations

Report: `KSHETRA_RULINGS_789_INDEPENDENT_RECOUNT_v1_0.md`, commit `030896ced`, status
`INDEPENDENT_RECOUNT_COMPLETE`. The session reached the served corpus read-only through the proxy,
aggregates and verse references only, and stopped the proxy after. It also did the one thing this family
asked for and could not do itself: it re-derived the numbers **this family supplied** rather than
re-reading this family's summary of them. Several of those numbers were wrong. They are corrected here,
at the source of the error.

**The finding that changes the picture.** `bg_transit_rules` is **already re-cited in production**:
`count(*) where vedha_house is not null` → **42** (not 41), of which **36 are verse-cited** to PG322/PG323
and **6 are `UNSOURCED` Rāhu/Ketu rows**, and **0 cite BPHS Ch.29 as a source** — the six BPHS mentions
are those same node rows, whose `UNSOURCED` stamp names Ch.29 *only to record its absence*.
**Corrected 2026-09-24 (see §7.8):** this sheet first wrote "42 cite Phaladīpikā". That was an `ILIKE
'%phalad%'` string match, not a citation count: the L0 session wrote each row's full *reason text* into
`classical_citation`, so the six node rows merely mention the text they are not cited to. The honest form
is **36 + 6**, which is what the geometry line already said. The geometry split is **36 matching / 0 deferred / 6 nodal**, not 32/3/6:
the three Venus rows (ids 35, 44, 45) now read vedha 1/5/11 and all match. So:

- **Plan §5.4's "39 rules citing BPHS Ch.29 alone and exactly 2 citing Phaladīpikā" is stale.** It was
  true when measured and is not true now. It must be restated as a re-runnable query with its predicate,
  never as a copied figure — the same lesson DVA Ruling 16 already taught this project for the L1 row
  counts, and this is the **third** correction to this particular number.
- **Migration 1085 (the G-9 re-citation repair) may now be redundant or actively wrong**, because the
  repair it performs appears already applied upstream. **Nobody applies it** until someone diffs it
  against the live `bg_transit_rules` state. It is file-only by brief §8.4 and unapplied, so nothing has
  broken; it must not be treated as pending work that is safe to run.
- **This makes §12.9 more urgent, not less.** Upstream L0 is repaired and this family's 132
  `house_vedha` output rows still carry the old citations from the 2026-09-07 build. The divergence is
  live right now, and no detector exists for it. Both facts are true because they are different tables.

**Corrections to this family's own cited page anchors** — each with its predicate in the report:

| this family said | measured | where it lands |
|---|---|---|
| Sade-Sati testimony at `PG1334 / PG786 / PG1333` | **`PG786` returns 0 rows.** The five hits are `PG1333, PG1334, PG1339, PG1340, PG1342`, all `nadi_navamsa_patel` | **N-15's citation list is wrong** and is corrected to the five real pages |
| kakṣyā doctrine in "6 nāḍī rows, PG1615/PG1616" | six **pages**: `PG80, PG1615, PG1616, PG1618, PG1623, PG1624`; bindu semantics verbatim at PG1615/1616 | **M-7's evidence base widens**; the two pages quoted are right, the set was incomplete |
| SBC construction at `PG345:C1`–`PG346:C1` | **`PG345` is 592 characters of garbled diagram page** carrying only an announcement and a legend; the construction is at **`PG346:C1`** onward | plan §5.4's anchor corrected; reinforces §7.5 D — the prose was not buildable |
| "two scales: PG349 general, PG353 battle" | **`PG349`'s own count-keyed scale opens "fear in battle"** too, so the clean general-versus-battle split does not hold | the honesty item stands but its framing was too tidy; `bg_vedha_malefic_scale`'s rows already declare the battle scoping in `effect_description`, so the data-layer defect is remediated |
| — | **new: Mercury's 2→5 row is page-grain only** — the served śloka-6 chunk gives that vedha house as the OCR token `Bill`, not a number | under a mechanical `applied iff corpus_verifiable` rule that row **must not** be stamped beside the 35 clean matches. Added to §12.3's stamp work |
| — | **new: a bare `'%kaksh%'` count returns 14**, of which 6 are Jaimini's unrelated *Kakṣyā-Hrāsa* longevity doctrine | recorded so no later session "corrects" a right number |

**Confirmed unchanged:** 15 texts / 10,651 chunks; `phaladeepika` 564 chunks with exactly 17 carrying
vedha; KP **0**; `muhurta_chintamani` **0 of 274** `sarvato*`; `bg_sarvatobhadra_grid` **0**; ślokas 3–8
name only the seven classical grahas; `PG348:C1`'s Rāhu/Ketu rule is the Sarvatobhadra mechanism, not
house-transit; laṭṭā at PG338/339.

**What O-3 refused to certify, and this sheet records as uncertified:** rulings **7** and **9** have
**zero corpus-count dependency** — 7 rests on ephemeris arithmetic and code reconciliation, 9 on code
semantics — so a re-count can neither confirm nor disturb them, and **no later session may read that
report as having reviewed them.** They were bundled with 8 for a shared *reviewer-conflict* reason, not a
shared evidence base. O-3 also declined to restate two node longitudes it did not itself compute (B.10),
and did not attempt the Sarvatobhadra transcription. Four `NOT_RUN` items, each with its reason. That is
the correct output of an honest reviewer, and the bundling assumption is itself a finding.

### 7.7 Correction against this session, 2026-09-24 — the duplicate-prefix count was wrong, and wrong in this session's own favour

This session published **55** as the number of duplicated migration prefixes on `origin/main`, and told
both the Saṅgam and the strategic session that Saṅgam's figure of 41 had *understated* it. **The 55 is
wrong.** Saṅgam questioned it, this session re-measured, and the command behind 55 counted two things it
should not have: **155 `_archive/` files**, and numbers repeated *within* a single directory.

Measured properly, excluding `_archive/`, on `origin/main`:

| measure | value |
|---|---|
| numbers claimed in **both** live directories (the figure that matters to the runner) | **30** |
| repeats within `platform/migrations` alone | 1 |
| repeats within `platform/supabase/migrations` alone | 4 |

The conclusion is unchanged and if anything is cleanest at 30: cross-directory duplicate numbers are
routine on `main`, so a shared number is not by itself a defect, and nobody needed to renumber. But the
error ran in the direction that made this session's own correction look better founded than it was, and
it was published to two other streams as a correction *of* one of them. That is the same defect class this
campaign has been closing all day — a number restated with more confidence than its derivation supported
— committed here by the session policing it. Recorded at full strength rather than quietly fixed. The
reproducible form, which is what should have been published in the first place:

```
a=$(git ls-tree -r --name-only origin/main -- platform/migrations \
      | grep -v '_archive/' | grep -oE '/[0-9]{3,4}_' | grep -oE '[0-9]{3,4}' | sort -u)
b=$(git ls-tree -r --name-only origin/main -- platform/supabase/migrations \
      | grep -v '_archive/' | grep -oE '/[0-9]{3,4}_' | grep -oE '[0-9]{3,4}' | sort -u)
comm -12 <(echo "$a") <(echo "$b") | wc -l     # => 30
```

Saṅgam's 41 and this session's 55 are both artifacts of undeclared method. The lesson is the one O-3 drew
about ruling 8's figure and DVA Ruling 16 drew about the L1 row counts, arriving for the third time today:
**publish the predicate, not the number.**

### 7.8 Third correction against this session, same day — "42 cite Phaladīpikā" conflated a string match with a citation

Both the strategic session and Kṣetra independently caught the same thing, and they are right. O-3's report
gave two distinct numbers — `ILIKE '%phalad%'` → **42**, and geometry-matching verse-cited rows → **36** —
and this session's headline collapsed them into "42 cite Phaladīpikā". The six extra rows are the Rāhu/Ketu
rows, stamped `UNSOURCED`, which contain the string only because the L0 session wrote each row's full reason
text into the `classical_citation` column. O-3's own report carried the mechanism for this in its next
sentence; this session read past it while writing the summary.

Kṣetra's fuller decomposition, reproduced from the served table on its side and consistent with O-3's:
**36 = 32 originally matching + Venus ids 35/44/45 repaired to 1/5/11 + Mercury 8→1 as id 569**, with **6**
node rows `UNSOURCED`. And the strict `corpus_verifiable` cover is **35**, not 36, because Mercury id 21
remains page-grain only — its śloka-6 vedha house is the OCR token `Bill`.

**The pattern, stated plainly, because this is the third time today.** §7.4 withdrew an over-applied renumber
rule. §7.7 corrected a duplicate-prefix count that this session had published as a correction *of* another
stream. §7.8 corrects a count that conflated a match with a claim. Every one of the three ran in the
direction that made this session's own position look better supported than it was, and every one was caught
by a peer re-deriving rather than reading. That is the layer's review mechanism working, and it is also the
standing evidence for why **the figure belongs in a predicate, not in prose** — the conclusion O-3 reached
about ruling 8, DVA Ruling 16 reached about the L1 row counts, and this session has now demonstrated three
times by violating it.

### 7.9 Blast radius of the §7.7 error, traced and closed

A wrong number's real cost is where it propagates, so the correction is not complete until that is traced.
The 55 figure reached three places; two are clean and one is another stream's record:

| where | state |
|---|---|
| this family's own artifacts | **corrected** — the rulings sheet §7.4, the Kṣetra instruction file and the Saṅgam instruction file all now read 30, with the reproducible command in §7.7 rather than a bare figure |
| the strategic session's artifacts | **never entered them.** That session confirmed, on checking, that 55 appears in no artifact and no commit message on its side. It had the figure only in a message |
| **the Saṅgam stream's record** | **contaminated by this family, then informed.** Saṅgam had recorded, on this family's assertion, that its own 41 was "understated". That framing was inherited from the wrong 55. Saṅgam has been told the correct figure is 30 and that its 41 was closer than this family claimed; whether its record is updated is Saṅgam's to do, and this entry stands as the trace if it is not |

Recorded because it is the honest completion: this session did not merely publish a wrong number, it
pushed a wrong number into a peer's record *as a correction of that peer*, which is worse than being
wrong alone. The strategic session notes that the same mechanism caught two of its own errors today
against three of this family's; the count is not the point, the mutual re-derivation is.

### 7.10 Dead-offer hazard closed, 2026-09-24 — never write a bare number into a conditional offer

The L3 layer-briefs session flagged that §7.5's conditional offer — "this family will renumber its own two
to **1087/1088**" — would, if anyone acted on it, put this family's second migration **on top of Saṅgam's
`1088_kala_convergence_kernel_fields.sql`**. It is right, and the offer is struck here and in the Saṅgam
instruction file.

The offer was already dead: it was conditional on Saṅgam's files being applied, Saṅgam answered that
nothing it wrote touched a database, and §7.4 withdrew the question. But a dead conditional that still
contains a live-looking pair of numbers is a loaded gun in a document, and a later reader has no way to
know the condition lapsed. **The defect is naming numbers inside a conditional at all.** Corrected form:
an offer names *the lowest free numbers at the time the condition fires*, never a literal pair — the same
"publish the predicate, not the number" rule as §7.7 and §7.8, in its forward-looking form. Fourth
instance today of one rule.

**Current state, re-verified at 13:05 across every remote head and the local head, both migration
directories:** this family 1080–1086 (`platform/migrations/`); Saṅgam 1088–1090
(`platform/supabase/migrations/`); **1087 free and holding exactly one slot** between the two; **1091+
free**. Anyone renumbering into that gap must take 1091+, not 1087/1088.

### 7.11 MIG-1 run for real, 2026-09-24 — PASS, and the renumber question was never a courtesy

Saṅgam withdrew its own "hygiene, not a defect" framing of the 1085/1086 collision, and the withdrawal
is correct and material. This session had accepted that framing and reasoned from it too.

**The gate Saṅgam found, and this session had not looked for either.** `.github/workflows/ci.yml:201`
runs **`MIG-1 — migration number guard (cross-directory duplicate)`**
(`npm run guard:migration-numbers` → `platform/scripts/ci/migration_number_guard.ts`), deliberately
before `npm test`. A duplicate leading integer across **or within** the two migration directories that is
**not in the frozen baseline** is a hard PR failure. The ~30 duplicates both sessions cited as proof of
harmlessness survive only because `migration_number_legacy_duplicates.json` freezes them by exact file
list, and the guard carries a rule whose stated purpose is that a legacy collision cannot be cover for a
new one. **So the collision would have failed CI the moment the two branches met.** The renumber was
load-bearing, not cosmetic, and both sessions had the mechanism right and the gate unchecked.

**This session ran the guard, which Saṅgam could not** (`tsx` absent on its host; its clean read was a
rules-against-census inference, correctly caveated):

```
cd platform && npm run guard:migration-numbers
=> PASS — no new migration-number collision.   (exit 0)
```

Also verified directly: each of this family's 1080–1086 exists in `platform/migrations/` and in **none**
of them in `platform/supabase/migrations/`, so there is no cross-directory duplicate waiting at merge for
PR #2731.

**One real defect the run surfaced, this session's own, now fixed.** The guard's advisory
`header-mismatch` check flagged that `1080_*` and `1081_*` still carried inner title lines reading
"Migration 1071" and "Migration 1072" — the original numbers, which survived **both** renumbers
(1071→1075→1080) because only the filename and the prose references were rewritten, not the body's own
title. Non-fatal, and precisely the defect class this sheet has been recording all day: a stale number
left inside a document while the document's surface was corrected. Both title lines now state the current
number and name the original in place. Guard re-run: PASS.

**Standing instruction for this family's numbering, replacing "scan every head":** scan every head **and
then run MIG-1**. The scan tells you what is claimed; only the guard tells you what will merge.
