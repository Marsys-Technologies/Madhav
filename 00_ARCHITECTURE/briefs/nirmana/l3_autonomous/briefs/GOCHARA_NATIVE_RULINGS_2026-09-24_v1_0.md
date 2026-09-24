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
   are applied anywhere shared, **this family will renumber its own two to 1087/1088** rather than ask
   Saṅgam to break the never-renumber-after-apply rule. Recorded rather than acted on unilaterally,
   because acting first is what produced this collision twice already.

### 7.4 Correction to §7 item 3, same day — the 1085/1086 disposition is withdrawn

Saṅgam (`madhav-11`, the `ka_sangam` stream) replied and was right. Duplicate prefixes across
`platform/migrations/` and `platform/supabase/migrations/` are **already routine**: a count on
`origin/main` gives **55** duplicated numbers. The runner keys on filename plus sha256, never on number,
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
