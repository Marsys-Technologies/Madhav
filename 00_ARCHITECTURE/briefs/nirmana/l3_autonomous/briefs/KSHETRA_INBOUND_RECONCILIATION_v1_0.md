---
artifact: KSHETRA_INBOUND_RECONCILIATION
canonical_id: KSHETRA_INBOUND_RECONCILIATION
version: "1.0"
status: RECONCILED_FOR_STAGE_3
date: 2026-09-24
purpose: >
  The native asked, before stage 3 starts, that every instruction, feedback, review and pointer
  sent to Kshetra from every side — L0, the L3 Claude Code handoff, the strategic session, Gochara,
  Sangam, the two independent reviews and the synergy audit — be verified as captured, once and for
  all. This is that record: every source swept, every item matched to where the packet holds it,
  every gap folded into the packet in the same PR, and every inbound claim that measurement
  refuted named as refuted so no session inherits it.
method: >
  Three read-only sweeps (strategic branch l3/kala-elevation-readiness; main-branch governance;
  the Gochara and Sangam worktrees) enumerated 200+ Kshetra-directed items with file:line. The
  author then verified at source every item that would change the executor's work — by grep, by
  reading the L0 repair's diff and PR record, and by SELECT-only queries against production through
  the project's read-only proxy — before folding it. Presence alone was never treated as capture.
sweeps: 2026-09-24, main @ 0dcf28d6d; readiness @ 5c05a0e2f+; gochara wp0-7 @ e93112eb0; sangam/stage3 @ 8ad8e0b52
---

# Kshetra — inbound reconciliation before stage 3

## §1 — Verdict

**Captured before this pass:** the ten rulings and their cross-stream locks (M-2 AV source; N-4a node
frame; F-23/G-8 re-citation; D-2/D-3 censoring and eligibility; D-S6 four-value enum; B8-6 unruled
episodes; B8-10 re-rank), the t-axis defect, the vedha row repair, the ablation pre-registration, the
L3 handoff's contract on Kshetra (mutation-free planner, `lel_derived=false` ownership, resume v10,
W7 hold, P0 accepted), the depends-on audit's edge findings, the environment audit's F4, Lane C's
K-2/K-3/K-5/K-6/K-8 and B-1/B-3/B-5/B-7, the W0 field-contract register's two QX gates, DP-SD-019,
FOUNDATION_SAFETY §4.1/§6/§8 — see §3, columns "captured".

**Folded in this pass (PR of this artifact):** the L0 repair's actual dispositions (ruling 7's L0 side
is discharged as declaration + degree anchor, *no* mean derivation; the sarvatobhadra population was
attempted and blocked; the malefic scale is pinned as PG353); the binding's B1/B2/B4/B5 rows that
were carried in spirit but not as named columns (`time_basis`, `epistemic_class`, six-state
`completeness_state`, `operator_role`, `tier_basis`, coverage's seven-field shape, empty-result row,
`independence_group` union); K-1's provenance pinning by `(generation, id)`; D-S5's `window_ref`
handle; M-8's consumer semantics; the stale-consumer state of `kala_vedha_gochara` (C3); stages 0–3
registering no substeps; the resume fingerprint's blindness to upstream content (PRATIJNA B5); the
registry's null volume metadata and the tiling invariant (F-KSHETRA-11); CG-1's two halves; the
ephemeris-backend assert (checklist B4); the `kala_timeline` / `kala_timeline_spec` non-conflation;
F-78 as already executed on the writer; the binding's rule of adoption (brief §1 citation, §6 proof
matrix with tests 5/6/7/9). Native questions that no session may answer are listed in §4.

**Refuted by measurement, recorded so they are not re-inherited (§5):** "the hazard field is flat over
time" (PRATIJNA B6); "stamp columns exist with writers populating them" (true on Gochara's branch,
false in production); "vedha-pair partitions of the sarvatobhadra grid are transcribable from prose
today" (this packet's own claim, refuted by the L0 attempt); "the kinematics roots are *merged* into
the axis" (the clip is the mechanism; the roots are excluded by design); two code defects the sweeps
cited as open that current code already fixes (`fact_category='lagna'`; the class-lifetime tiebreaker).

## §2 — Sources swept

| # | Source | Where | Items |
|---|---|---|---|
| S1 | KALA_SYNERGY_BINDING v2.2 · AUDIT v1.5 · AMENDMENTS v2.1 (Kshetra section) | readiness branch | 28 rows |
| S2 | KALA_ELEVATION_BLUEPRINT v4.7 · CHRONICLE §11.x · DELEGATED_DECISIONS D-A…D-F · PRE_ELEVATION_CHECKLIST v1.7 · NATIVE_RULING_SHEET · L0_REPAIR_EXECUTION_PROMPT · EVENTS.jsonl · INTEGRATOR_VERIFICATION_LOG | readiness branch | 89 items |
| S3 | MADHAV_L3_CLAUDE_CODE_HANDOFF_2026-09-19 · L3_DEPENDS_ON_AUDIT · L3_STATE · KALA_STRATEGY_TRACEABILITY_MATRIX · KALA_ENVIRONMENT_READINESS_AUDIT · LANE_C_HARD_ASSETS · T1/F4/DOMAIN_H · KALA_W2_FIELD_DESIGN · SHAD_DARSHANA · W2_DETERMINISM_PRECHECK · CAMPAIGN_COORDINATION · L3_W1_ANALYSIS D/E · DATA_PLANE disposition/execution brief/DP019/W0 FOUNDATION_SAFETY/FIELD_CONTRACT_REGISTER · F-78 SPEC · PRATIJNA_V4_STATE · CURRENT_STATE · DISAGREEMENT_REGISTER · EXECUTION_LEDGER | main | 121 items |
| S4 | GOCHARA_RULING_SHEET v1/v2 · GOCHARA_SYNERGY_RESPONSE · GOCHARA_FAMILY_ELEVATION_PLAN v2.1 · PACKET_K1 · KALA_BASELINE · STATE · GOCHARA_NATIVE_RULINGS_2026-09-24 · KSHETRA_INSTRUCTIONS_FROM_GOCHARA_2026-09-24 | gochara wp0-7 (origin @ e93112eb0) | 20 + 5 |
| S5 | SANGAM_RULING_SHEET §RULINGS/§CLOSE/§Corrections · SANGAM_STAGE3_STATE · SANGAM_ELEVATION_FINAL · EVENTS.jsonl | sangam/stage3 | 17 |
| S6 | L0 repair PR #2727 (diff + per-item record) · migrations 1075–1079 · production reads | l0/vedha-and-frame-repair; production | 8 items |
| S7 | KIMI_K3_CLOSE_REVIEW C-1…C-6, D-1…D-5 · KSHETRA_INDEPENDENT_REVIEW_7_8_9 "not in the packet" list | packet | 15 |

## §3 — Disposition of every item that changes the executor's work

Legend: **C** captured before this pass · **F** folded now (this PR) · **N** native question (§4) ·
**R** refuted by measurement (§5) · **X** not Kshetra's, correctly absent.

### Rulings, locks and rulings' L0 side
| Item | Source | Disp. | Where |
|---|---|---|---|
| Ruling 7 L0 side: degree anchor (migration 1075, `service_probes.py` enforces `49.033044° ± 10″`) — **done, applied** | S6 | F | sheet row 7; plan §7.7; prompt §2 |
| Ruling 7 L0 side: `ephemeris_daily.node_mode='true'` / `epoch_convention='noon_ut'` on all 183,352 node rows, `noon_ut` on all 641,732 others (migration 1076) — **done, applied**; **no mean-node column derived**; mean consumers compute live (`routers/ephemeris.py`) | S6, verified live | F | same |
| Consequence: Kshetra S0 node contacts are TRUE-transit vs MEAN-natal — a mixed frame; the packet's "derive mean in the L0 service" wording superseded by N-4a as implemented | S6, S4 N-4a | F | prompt Phase 2 pins + S0 decision; sheet row 7; plan §7.7 |
| Ruling 8 L0 side: 35 rows re-cited; Venus 35/44/45 → 1/5/11; Mercury 8→1 = id 569; 6 node rows `UNSOURCED`; exceptions in `rule_notes` — **applied** | S6, verified live | C | sheet row 8; L0 spec 1.3 |
| Sarvatobhadra population: **attempted and BLOCKED** on primary-source grounds (3/28 asterisms; letter glyphs garbled; traversal direction unstated; schema cannot hold the 9-point vedha set); this packet's "vedha-pair partitions transcribable today" claim **withdrawn** | S6 PR #2727 item 4; D-E item 4 | F + R | sheet row 8; plan §2/§7.8; L0 spec §7; independent review §Ruling 8 |
| Malefic scale pinned as the **PG353 battle-context** scale, distinct from PG349's general-transit scale; which one Kshetra's transit covariate should read is a doctrinal choice for the S1 packet | S6 item 5, migration 1077 | F | prompt Phase 4 S1; plan §7.8 |
| `ka_vedha_gochara/logic.py` corpus docstring corrected (item 8) — packet's citation of `logic.py:13,105` as mis-cited is now historical | S6 | F | brief §2.4 note |
| Consumer rows stale: canonical `kala_vedha_gochara` house_vedha 132 rows still cite "BPHS Ch.29" (built 2026-09-07, before the repair); 24 sarvatobhadra rows cite Prasna Marga (not in corpus); neither writer fingerprints `bg_transit_rules` (checklist C3) | S2 C3, verified live | F | prompt Phase 4 S1: consume only rows rebuilt after re-citation, or treat citation-stale rows as `unqualified` |
| Stamp columns `source_qualification`/`corpus_verifiable`/`precision_regime` on `kala_vedha_gochara`/`kala_moorti_nirnaya`: **on Gochara's branch (migration 1082), NOT in production** (verified: NONE) | S4 instructions; verified live | F + R | prompt Phase 4 S1 "check, do not assume" strengthened with the live state |
| Mūrti graded at the true sign-ingress instant, `precision_regime='instant_grain'` on mūrti rows (Gochara WP9) | S4 | F | prompt Phase 4 S1 |
| D-S5 `window_ref = {asset_id:'ka_gochara', generation, id: contact_id}` against PK `(chart_id, generation, contact_id)` — the consume option's exact handle | S4 native rulings | F | prompt Phase 2/4 |
| M-8: exceptions emit **no vedha row**, coverage records `searched, exception_applied`; vipareeta kept with `cancelled=true`; retrograde malefic → `intensity_qualifier` — Kshetra as consumer must read the coverage token, never infer absence | S4 M-8 | F | prompt Phase 4 S1 |
| K-1: pin provenance edges by `(generation, id)` at `writer.py:948-953` / `:1059-1064` (`source_pk=str(row['id'])` is bare); declare the `→ka_gochara` edge (the CURRENT producer — not the retired sweep) as an F12 `evaluation` edge; keep the `'v1'` removal | S4 PACKET_K1; verified at source | F | prompt Phase 2 |
| B8-7 (R-6 four-way separation for Kshetra), B8-4 (`independence_group` jsonb shape), B-2 (staged acceptance), B-4 (shared vs per-class knot grid) | S1, S3 | N | §4 |

### Binding rows (KALA_SYNERGY_BINDING v2.2) not yet named as columns
| Row | Disp. | Where |
|---|---|---|
| B1 `time_basis ∈ {event_instant, noon_ut_knot, date_grain_midpoint}` — MUST ADD | F | prompt Phase 2 |
| B1 `inclusivity` literal `closed_open` per row | F | prompt Phase 2 |
| B1 `t_exact`/`t_peak` as `timestamptz` or NULL, never a sentinel | F | prompt Phase 2 |
| B2 `epistemic_class` (F04), six-state `completeness_state` (F06), `operator_role` (F12), `tier_basis ∈ {relative_uncalibrated, calibrated:<gate_id>}` — MUST EMIT | F | prompt Phase 4 S5 |
| B4 `independence_group` = union of witnesses' groups; any scored projection carries it with `comparable_with` | F | prompt Phase 4 S5 |
| B5 `coverage` seven-field shape; empty result = a row **and** coverage, never "no row" | F | prompt Phase 4 S5 |
| Rule of adoption: cite the binding in brief §1; prove OFFER/MUST rows in §6 with tests 5/6/7/9 + negative fixtures (D-S3 approved this form for Gochara) | F | brief §1, §6; prompt Phase 5 exit |

### Build-integrity findings from the main-branch sweep
| Item | Source | Disp. | Where |
|---|---|---|---|
| Stages 0–3 register **no** substeps (`plan_substeps` starts at `prepare:replace` then stage4…); the §N.8 substep-completeness detector cannot see them | F-KSHETRA-9; verified `writer.py:277-405` | F | prompt Phase 2 |
| Resume `_fingerprint()` blind to upstream content (`bodha_pratijna` rescoring resumed as done; 123-row manual clear on the canonical chart) | PRATIJNA_V4 B5 | F | prompt Phase 2 pins |
| Registry: `count_sql` present; `size_sql`/`expected_volume_*`/`integrity_check_sql` null, `target_floor` 0; proposed invariant: stage-4 segments tile `(chart_id, event_class)` with no gaps/overlaps; every window's `field_snapshot_id` = the chart's newest snapshot | F-KSHETRA-11; verified seed | F | prompt Phase 5 exit |
| CG-1 Circularity Guard needs both halves (dynamic hash invariance ∧ static import/SQL scan) | W2 design §8.3 | F | prompt Phase 2 |
| Ephemeris backend is process-global: every swisseph entry point resolves and asserts the backend per call from `retflag` (`stage3_clocks.py:885` computes Moon velocity at birth directly) | checklist B4 | F | prompt Phase 2 |
| `kala_timeline` is DARK; `kala_timeline_spec` is Kshetra's live table — never conflate | traceability §11 | F | prompt §3 |
| F-78 (`built_event_classes`, disclosure test) is **already on the writer** (`writer.py:227`, `tests/l3/ka_kshetra/test_event_classes_disclosure.py`); its spec still reads "awaiting REVIEW" — do not duplicate; the S4 migration must not collide | F-78 SPEC; verified | F | prompt Phase 2 S4 |
| Stage-8 per-view substep (1,210 s) exceeds `_WRITER_TIMEOUT_SECONDS` (env, default at `runner.py:111`) — W7 scope, recorded for the W7 packet | F-KSHETRA-6 | F | plan §8 |
| `bg_synthetic_cohort*` / `phala_rectification` grants (F4): σ_T replaced, not granted (ruling 3); cohort SAVEPOINT | env audit F4 | C | brief §4.3; prompt Phase 2 |
| L3 ↔ Gochara hub coupling: `ka_dasha_kala` and `transit_search` (MEAN_MOTIONS only); no automated staleness bridge from hub digest to sibling rows | DOMAIN_H | F | plan §3.1 note |

### Items correctly absent (not Kshetra's)
D-C century writer; D-D Sade-Sati; N-14's λ-product conditions (Gochara-internal); D-6/DIS.031 nodal dṛṣṭi —
**verified not applicable**: `find_contact_episodes` is conjunction-only (`stage0_kinematics.py:401-408`),
Kshetra casts no aspect from any body; Sangam D-1's 20/50 binomial gate — the pre-registration is
pair-scored, not a binomial test (recorded in KIMI/Sangam exchange); Sangam's `-k 'not ka_kshetra'` test
exclusion — Kshetra's own suite is its proof, not Sangam's.

## §4 — Questions only the native can answer (none block stage 3's first four phases)

1. **B8-7** — does Kshetra adopt the R-6 four-way separation (`activity · valence · applicability ·
   availability`) as emitted columns, as Sangam did, or declare its λ decomposition (promise, clock,
   modifier, suppression) as the equivalent with a mapping? Needed before the S5 projection ships.
2. **B-2** — does "Accepted N/22" count a partially-elevated Kshetra (stage-family acceptance with the
   snapshot as a separate terminal gate), or one terminal asset? Needed at PRODUCER_READY.
3. **B-4** — shared knot grid (342,803 segments per class regardless of structure) vs per-class grids;
   cost against cross-class comparability. Needed before P1 is funded.
4. **B8-4** — the jsonb shape of `independence_group`. Needed at S5.
5. **B8-6** — one contact producer: consume `kala_gochara_contacts` by `window_ref` or keep
   evaluation-only episodes. Kshetra's interim is declared; the ruling is the native's.
6. **PG349 vs PG353** — which of Adh. XXVI's two 1–5 malefic scales Kshetra's transit covariate reads.
   The L0 pin says the served table is PG353's battle-context scale; the transit scale is PG349's.

## §5 — Inbound claims refuted by measurement (do not re-inherit)

| Claim | Source | Measurement | Standing |
|---|---|---|---|
| "The hazard field is flat over time for every class (γ=0, identical α per segment)" | PRATIJNA_V4_STATE B6; CURRENT_STATE v6.58 | canonical `kala_field`: 342,803 segments per class, **~129k distinct γ and ~318k distinct α per class; 8,417,290 rows with γ ≠ 0** | Refuted for the current substrate; the clock term does vary. A2 (zero the clock term) stays the test of whether it *matters*. |
| "The three stamp columns now exist with writers populating them" | KSHETRA_INSTRUCTIONS_FROM_GOCHARA §1 | production `information_schema`: **NONE** on `kala_vedha_gochara` (17 columns) and `kala_moorti_nirnaya` | True of Gochara's unmerged branch (migration 1082); false in production until merged and applied. |
| "Vedha-pair partitions of the SBC grid are transcribable from prose today" | this packet (sheet 1.4–1.10; independent review 1.1+; Kimi C) | L0 repair read PG345–354 verbatim: 3/28 asterisms, direction unstated, glyphs garbled, schema cannot hold the 9-point set | Withdrawn. Sarvatobhadra stays `unqualified` with **no prose-only remedy**. |
| "`load_kinematics_breakpoints` merges the roots into the birth-relative axis" | synergy audit 1.1; Gochara instructions §4 | `dhara_sweep.py:66` excludes the roots by design; the `[0, H]` clip on J2000 knots is the mechanism; all knot sources are J2000 | Scoped up; audit 1.5 adopted the correction. |
| "`fact_category='lagna'` read-dead" (open) | L3_STATE M1; depends-on audit §4.5 | `writer.py:1794-1796`: measured and corrected to `lagna_position` in current code | Already fixed. |
| "`load_class_lifetime_count` has no tiebreaker" (open) | W2_DETERMINISM_PRECHECK §5 | `stage4_field.py:1141-1164`: all four predicates pinned, total `ORDER BY` | Already fixed; PK-P4's second prior set is safe on this read. |
| "F-78 awaiting review, unexecuted" | F-78 SPEC frontmatter | `writer.py:227 built_event_classes`; disclosure test present | Executed on the writer; spec status stale. |

## §6 — What this pass did not do
No code, migration, build, grant or deployment. No ruling re-opened. The stage-3 prompt remains
`AUTHORIZED_STAGE_3_ONLY`, executor not started; stage 4 remains closed by the native's word.
