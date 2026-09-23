---
artifact: KIMI_K3_CLOSE_REVIEW_KSHETRA
canonical_id: KIMI_K3_CLOSE_REVIEW_KSHETRA
version: "1.0"
status: COMPLETED_EXTERNAL_REVIEWER_OUTPUT
date: 2026-09-23
reviews: the CLOSED Kshetra packet (KSHETRA_RULING_SHEET_v1_0.md v1.3, KSHETRA_INDEPENDENT_REVIEW_7_8_9_v1_0.md v1.0,
  KSHETRA_ECOSYSTEM_ELEVATION_PLAN_v1_0.md v1.8, KSHETRA_ELEVATION_BRIEF_v1_0.md v4.7) — a second,
  independent pass after the first fresh-agent review, requested by the native and run via the Kimi
  Code desktop app in an isolated detached-HEAD worktree (`/Users/Dev/madhav-l3/kshetra-kimi-review`,
  no branch, no write access, no shared checkout with any other active worktree).
prompt: KIMI_REVIEW_PACKET_KSHETRA_CLOSE_v1_0.md (not committed; held in the author's scratchpad)
disposition: three corrections adopted into the packet (v1.4/v1.9/v1.1), each independently
  re-verified by the author at the served corpus or in the code before adoption, per this
  campaign's standing rule never to adopt a reviewer's claim on trust. No ruling re-opened.
---

# Kimi K3 desktop review — the closed Kshetra packet

Reproduced below as returned by Kimi K3 (interior `---` rules rendered as `***` so they don't
collide with this file's frontmatter fence; otherwise verbatim). This is Kimi's own report — data,
not verified fact — until the "Independently re-verified" section below it says otherwise. §N.7
discipline requires the claim trail to be inspectable, not summarized away.

***

All verification is complete, the proxy is stopped (0 listeners), and `git status` is clean — the
workspace is untouched. What follows is my own re-derivation; I trusted nothing from the packet
that I could re-run.

**Method note.** DB access was refused at session start (`ECONNREFUSED 127.0.0.1:5433`), so I
brought up the project's documented Cloud SQL Auth Proxy path (the same read-only route the 7/8/9
reviewer used), ran SELECT-only queries against `classical_text_chunks`, `bg_transit_rules`,
`ephemeris_daily`, `chart_facts`, and the L0 tables, then stopped the proxy. Swiss computations used
pyswisseph against `/tmp/se1`, whose three file checksums I verified **byte-equal to the sha256
pins in migration 624**. No file was written; no git state changed.

***

## (A) Verdict on the ruling-8 correction — re-derived: **CONFIRMED, with one false sentence inside it and two refinements**

I pulled PG322:C1 (Phaladīpikā Adh. XXVI śl. 3-5) and PG323:C1 (śl. 6-8) from the served corpus and
the 41 rows via the producer's own predicate (`rule_type='favourable' AND vedha_house IS NOT NULL`,
exactly the SQL at `services/ka_vedha_gochara/writer.py:98-102`). The text gives these
transit→vedha pairs (Iyer translation, verbatim from the chunks):

- **Śl. 3 Sun:** 11→5, 3→9, 10→4, 6→12 (Saturn excepted)
- **Śl. 4 Moon:** 7→2, 1→5, 6→12, 11→8, 10→4, 3→9 (Mercury excepted)
- **Śl. 5 Mars / Saturn:** 3→12, 11→5, 6→9 (Sun excepted for Saturn)
- **Śl. 6 Mercury:** 2→5, 4→3, 6→9, **8→1**, 10→8, 11→12 (Moon excepted) — six pairs
- **Śl. 7 Jupiter:** 2→12, 11→8, 9→10, 5→4, 7→3
- **Śl. 8 Venus:** 1→8, 2→7, 3→1, 4→10, 5→9, 8→5, 9→11, 12→6, 11→3 — nine pairs

Row-by-row against the table:

- **32 exact matches — confirmed.** Sun 4/4 (ids 1-4), Moon 6/6 (8-13), Mars 3/3 (15-17), Saturn
  3/3 (36-38), Mercury 5/5 (21-25), Jupiter 5/5 (26-30), Venus 6/9 (33, 34, 42, 43, 179, 180). The
  text's Mercury 8→1 pair has **no row at all** — the table holds 35 of the text's 36 graha pairs.
- **3 Venus contradictions — confirmed.** id 35 stores (3,11), text says 3→1; id 44 stores (8,1),
  text says 8→5; id 45 stores (9,2), text says 9→11. **Refinement:** ids 35 and 44 are exact
  *transpositions* of correct rows already in the table (179 = (11,3), 33 = (1,8)) — two of the
  three look like column-swap duplicates, not geometry errors; only id 45 is a content typo
  (nearest text pair 9→11). The repair spec "L0 geometry correction" is imprecise: it is house-pair
  data repair, and for two rows *dedup*, since the correct pairs already exist. What I am NOT
  deciding: whether the mis-entry originated in the L0 ingest or a later edit — no history was
  examined.
- **6 Rāhu/Ketu rows unsourced — confirmed for disposition.** ids 187/188/189 (Rāhu) and 196/197/198
  (Ketu) store (3,9), (6,12), (11,5) — Sun's set minus (10,4). Citation census: 39 rows carry "BPHS
  Ch.29", 2 (ids 189, 198) carry "Phaladeepika Ch.26" — matching the packet's "39 of 41". Ślokas
  3-8 name only the seven classical grahas. I also searched the *rest* of the served corpus
  (Sārāvalī, Jātaka Pārijāta, Horā Sāra, Uttara Kālāmṛta): no alternative vedha-table source for
  these pairs exists — "deferred/unqualified" is right, and there is no re-citation path.
- **The false sentence [P].** Both the ruling sheet (row 8) and the independent review repeat:
  *"no vedha-bearing Phaladīpikā chunk anywhere in the corpus mentions Rāhu or Ketu transit vedha."*
  My count: **7 chunks** match `vedha` ∧ (`rahu`∨`ketu`) — including **PG339:C1** (laṭṭā: "the 9th
  from that of Rahu and the 22nd from that of the Moon are called Latta"), **PG347:C1**, and
  **PG348:C1** ("In the case of Rahu and Ketu, which are always retrograde, the Vedha will be on
  the right"). The *operative* claim — the six house-vedha rows have no counterpart in ślokas 3-8 —
  stands, and Rāhu/Ketu vedha is indeed not "doctrinally absent" (the SBC explicitly handles their
  retrograde vedha direction). But the sentence as written is checkable-and-false, in a packet
  whose own theme is citation discipline; it will be quoted. Cost if unfixed: a future session
  "discovers" PG339/PG348 and re-opens a settled ruling. Falsifier: the count query, already run.
  Not deciding: nothing about the 6 rows' status.
- **Sarvatobhadra narrowing — confirmed, and slightly too narrow in the favorable direction.**
  PG345:C1 = 592 chars of diagram tokens ("NORTH/SOUTH" labels only); PG346:C1-PG352:C1 = 1,349-1,499
  chars of clean prose per page. The partitions the `vedha_pair` cells need are all procedural: 28
  asterisms from Kṛttikā at the NE outermost square, 7 per side; 12 rāśis from Vṛṣabha in the East;
  the five tithi groups (Nanda/Bhadra/Jaya/Rikta/Pūrṇa) and weekday assignments named in full.
  **What the review called untranscribable "vowel/consonant letter cells" is only half right**: the
  16 vowels *are* procedurally specified ("Write in the regular order the 16 vowels... commencing
  from the outmost corner in the North-east, thus filling up in rotation the 4 corners of each of
  the 4 sets of squares"); only the consonant (varga) cells are OCR fragments ("a*, q\, |r..."). 
  Verifiable at PG346:C1. bg_sarvatobhadra_grid = 0 rows, laṭṭā = 8, malefic scale = 5 — all as
  stated.
- **Ruling 4's PG299:C1 backing — verified verbatim**: "If there should be one, two, three, four,
  five, six, seven or eight benefic dots, the effects will be (1) destruction or loss (2)
  expenditure (3) fear (4) fear (5) accomplishment of the desired object (6) acquisition of a
  damsel (7) gain of wealth or property and (8) gaining a Kingdom..." The "3 and 4 share a word"
  observation is exact; citation correct. [D — Phaladīpikā Adh. XXIII, PG299:C1]
- **Corpus roster — confirmed**: 15 texts; phaladeepika = 564 chunks; no KP text. "BPHS Ch.29"
  remains a miscitation (corpus-wide, "gochara" occurs twice in bphs; no transit-vedha chapter
  exists).

## (B) Verdict on the rulings 7/9 corrections — **CONFIRMED, with one load-bearing sharpening on ruling 7**

**Ruling 7.** My own Swiss/Lahiri run at JD 2445735.717361 (`swe.revjul` → **1984-02-05 05:13 UT**,
the same instant migration 624:27 pins as its forensic anchor): TRUE node = **50.049248°**, MEAN =
**49.033044°**, retflag 65858, no Moshier bit. The reviewer's figures reproduce to the last digit;
the margin past the 50.000° Rohiṇī pāda-4 boundary is **0.049248° (177.3″)** — **0.049° confirmed,
0.045° refuted**. L1's served `RAH_MEAN` fact (49.0330441) matches my MEAN to 7 s.f., while the
plan's 49.028927 disagrees at exactly the same 0.0041° as its TRUE figure — and my 2-minute
differential test shows a time shift moves the two nodes *differentially* (−0.92″ vs −0.26″), so
the plan's offset is an ayanamsha-value difference, not a different birth instant: the reviewer's
diagnosis is right. Separately, at 1984-02-05 12:00 UT I reproduce the stored daily knot to 6 dp
(73.629058, diff −0.000000°) — store is true-node at noon-UT knots, Swiss-exact. `chart_facts` has
**0 RAH_TRUE rows** (RAH_MEAN-referencing rows: 13,375 — the review's "793" is a narrower
natal-subset count; substance confirmed). `l0_ephemeris.py:77` (`swe_id 11`, comment "Mean North
Node") and `:286-295` (Ketu = body 11 + 180°) are as cited; migration 624:30 asserts `"node_mode":
"mean"`.

All three "not L0-invisible" sites exist exactly as the correction says: `service_probes.py:339-340`
raises unless the probe spec reads `"mean"`; `routers/ephemeris.py:49` and `routers/panchang.py:572`
broadcast `"node_mode": "mean"` to MCP callers.

**The sharpening [P]**: I read the engines behind the two served declarations before accepting the
correction's framing, and it changes the reconciliation's *direction*. `routers/ephemeris.py:82`
computes `('Rahu', swe.MEAN_NODE)` directly via `swe.calc_ut` (:154), explicitly "distinct from
the ... ephemeris_daily table" (:248); `panchang_engine/planets.py:6-8,27,36` mandates MEAN_NODE
with TRUE_NODE "explicitly forbidden per Phase 4B." **Both served declarations are true today** —
the Phase 4B house standard *is* mean, and both live endpoints already comply. The §N.8 violation
is confined to `ephemeris_daily` (the store), migration 624, and the `l0_ephemeris.py:77` comment.
So disposition (b)'s reconciliation is one-sided: the declarations stay exactly as they are; the
*store* must gain the derived mean column to match its own declarations. An executor reading
"reconcile the two served declarations" could needlessly touch verified-correct serving code — the
correction should say "reconcile the store to the declarations," not the reverse. Consequence
worth stating plainly: live MCP consumers already receive mean node; the wrong-frame data reaches
**only builders that read `ephemeris_daily`** — Kshetra's S0, and (if the 6 node rows are ever
sourced) `ka_vedha_gochara`'s transit positions, which are computed from the same true knots — a
latent mixed-frame hazard (true transit vs mean natal) contained today only by the uniform
admission rule. Falsifier: the engine lines above. Not deciding: L0 owner or sequencing (explicitly
not Kshetra's per the packet).

Minor [P] slips found in the same neighbourhood: plan §6a says mean is "0.954° away" from true at
the noon instant — my computation gives **0.980180°** (conclusion "absolute discrimination"
unaffected); §6a.1's "margins 149-176 arcsec" doesn't match its own figures (162.5″-177.3″).

**Ruling 9.** All confirmed at this revision: `dhara_build_segments` at `dhara_sweep.py:163`;
`terms_at` call sites at **:212, :227, :243, :248** (the packet's older :43,:55 citations are
indeed wrong here); `stage4_field.py:561-565`'s "structurally impossible" docstring is **polarity
separation** (obstruction cannot leak into the additive modifier term M_e — it thins via S_e), not
route-scoping. The route-scoping contract lives at `layer1.py:15-21,29-30`, `hazard.py:347-350`,
`layer0.py:57-60` ("SM-R-7's per-class filter is applied in Layer 1, NOT here"). G3's substance
re-verified end-to-end: `terms_at` passes `obstructions=self.envelopes.obstructions_at(t)`
unfiltered (`stage4_field.py:855-873`); the null replicates through the same evaluator
(`dhara_null.py:86-163`, clock-only `EnvelopeIndex([])` C/E decomposition); `project_layer1` has no
production caller (only `services/ka_kshetra/tests/test_layer0_projection.py`, whose :436 comment
"project_layer1 > terms_at" and :455 assert the divergence as correct — the seed of the
byte-equality test, exactly as the review said). Ruling 10's measured claims also check out:
`mi_bhara.py:122-130` declares ka_kshetra, `mi_adhilepa.py:305` references ka_sangam, and
`mi_bhara` never reads `baseline_is_synthetic`.

## (C) New findings — tagged, with cost and falsifier

1. **[P] Sign-level probe anchor cannot detect the defect it guards.** Migration 624's anchor
   expects `expected_mean_node_rahu_sign: 2` — but *both* frames give sign 2 at the forensic JD
   (mean 49.033°, true 50.049°, both Vṛṣabha; only the pāda differs). The fail-closed validator
   enforces the spec's *text*; nothing compares data against a degree-level expectation. So even
   after declarations are repaired, §N.8's "signal with no detector behind it is null" persists for
   the node frame. Cost: one migration line + tolerance (e.g., expected mean-node longitude ≈
   49.033° ± arcseconds) — trivial next to the L0 derivation itself. Falsifier: run today's probe
   against the true-node store and observe it pass. Not deciding: who owns it (L0, outside this
   packet).
2. **[J]/[U] Pin-identity does not name the node frame.** `FieldPins`/`config_pin`
   (`stage4_field.py:186-212`, populated at `writer.py:318-336`) already pins `segment_engine`,
   `dhara_sweep_semantic_version`, `null_replicates`, etc. — but not the ephemeris node frame or
   noon-UT epoch that S0 consumes, and `ephemeris_daily` is a read-never-declared edge until the
   S1 register fix. If disposition (b) lands between builds, two fields computed under different
   node frames could carry the same `field_snapshot_id`. Recommend `node_mode`/`epoch_convention`
   enter `config_pin` at W7, matching the pattern the ruling already establishes for the row.
   Falsifier: the FieldPins payload vs the ephemeris derivation inputs. The [U] half: I did not
   exhaustively trace `corpus_pin`'s input set — if it already covers the L0 ephemeris generation,
   this collapses to a no-op; verify first.
3. **[P] Unowned completeness gap: the text's 36th pair.** Re-citation qualifies 32 rows, but no
   one owns *adding* the missing Mercury 8→1 row — the producer stays one row short of Phaladīpikā
   śl. 6 forever, and S1 ingestion inherits the gap silently. Cost: one L0 row; falsifier: `SELECT
   count(*) ... WHERE graha='mercury'` = 5 vs the text's 6.
4. **[J] Cross-class rank comparability is implied-safe nowhere.** A1 covers *within-class* rank
   invariance; Q08 across classes is deferred to calibration. But Q07's "cross-class simultaneity
   is exact and free" can be misread as licensing cross-class λ ranking while 19/25 classes carry
   synthetic baselines — a synthetic class and a calibrated class are not level-comparable at all.
   The U11 comparability flag should say this in words. Cost: prose. Falsifier: any consumer path
   that ranks event classes by absolute λ across the synthetic boundary (none exists today — this
   is pre-emptive).
5. **[P] Governance concentration (observation, not a defect).** One native sentence ("Go ahead and
   do it.") carried all ten rulings; the sheet complies with contract §8 (native record, conflicts
   declared, fresh 7/8/9 reviewer, author's corroboration) — and my re-derivation is a third layer
   on the load-bearing items. But the execution brief should carry one line: the delegation is
   overridable, and any native second thought re-opens by a single line in the sheet. Not deciding:
   whether any ruling deserves re-litigation — I found nothing that warrants it.
6. **[P] On "self-certification" and uncited classical appeals (question 4).** I grepped the packet
   for "as is known classically"-type appeals: **none exist**. Every load-bearing classical claim I
   tested held at page grain — PG299:C1 (ruling 4), PG322-323 (ruling 8), PG338-353
   (SBC/laṭṭā/malefic), PG345-346 (SBC construction). The packet's self-review statements
   ("verified here," "corroborated by the author") are layered verification, not self-approval; the
   approval record correctly terminates at native delegation. The one self-certifying-adjacent item
   is finding (C1)'s false absence sentence — an uncounted absence claim inside a document that
   elsewhere adopts the count rule.

## (D) What should have been caught earlier, and the method that would have caught it

1. **The "no vedha-bearing chunk mentions Rāhu/Ketu" sentence** — in the ruling sheet row 8, the
   independent review §Ruling 8, and echoed in plan §2 item 6. Method: the packet's *own adopted
   method rule* ("absence only by `count(*)` against `classical_text_chunks` naming the predicate")
   applied one more time. It was applied to retract the directory-read corpus claims but not to
   this sentence; my single count (7 hits, PG339/347/348) falsifies it. This is the third instance
   of the same failure class in one packet — absence asserted from a read that wasn't a count.
2. **The reconciliation direction on ruling 7** — the correction enumerated the two served
   declarations as sites to reconcile without reading the 10 lines of engine code behind each.
   Method: *follow the computation, not the declaration string* — the same discipline the packet
   praises in G3 ("read the writer's call chain end to end"). Had it done so, the correction would
   have stated the one-sided reconciliation and flagged the `ka_vedha_gochara` mixed-frame
   consumer.
3. **The 0.045° margin surviving three documents** — it was catchable without any recomputation:
   the plan's own §6a.1 prints L1's `RAH_MEAN` 49.0330441 *and* its own mean 49.028927, a visible
   0.0041° internal disagreement that no session flagged until the fresh reviewer recomputed.
   Method: *two stated figures for the same quantity must be reconciled before either is quoted* —
   the discrepancy was in the text, not hidden in code.
4. **The Venus transposition pattern (ids 35/44 duplicating 179/33 swapped)** — method: a
   set-symmetry check of the table against itself (any row that is the transposition of another
   row), a five-minute query once the corpus is the comparison target. The review compared
   row-to-text but not row-to-row; the disposition is unchanged but the repair spec ("geometry
   correction") misdescribes two of the three rows.
5. **The sign-level forensic anchor** — method: §N.8 applied reflexively to the detector itself:
   "can this anchor detect the defect class it guards?" A mean-vs-true frame slip at the anchor's
   own epoch sits entirely inside one sign, so the answer is no, and no session asked the question.
   Both reviews applied §N.8 to the *declarations*; the anchor is also a declaration.

**Closing verdict.** The ruling-8 correction is sound and I affirm it — 32/3/6 reproduces exactly at
the served corpus, and the disposition (ratify shared producers; uniform mechanical admission;
laṭṭā and the malefic scale `applied`; sarvatobhadra `unqualified` pending grid population from
PG346-352 prose) is correct on my independent read. The rulings 7/9 corrections are sound and
affirmed, with the one-sided-reconciliation sharpening recorded above. Nothing I found re-opens any
ruling; findings C1-C6 are execution-phase amendments the Data Plane task can absorb as written
notes. The packet's central discipline — L1 facts as authority, no invented values, a signal
without a detector is null — survived my attempt to break it everywhere except the one false
absence sentence, which costs one line to fix and nothing to fix it on.

***

## Independently re-verified by the author before adoption

Per this campaign's rule (never adopt a reviewer's claim without re-running it), three of Kimi's
findings were checked at source before any packet text changed. All three held.

**1. The false-absence sentence (ruling 8).** The packet's independent-review file and ruling sheet
both said "no vedha-bearing Phaladīpikā chunk anywhere in the corpus mentions Rāhu or Ketu transit
vedha." Kimi flagged this as checkable-and-false. The author pulled PG339, PG347, and PG348
directly via `read_chapter`:

- PG339:C1 (laṭṭā, śl. 46-48): "Misery will result during the Latta of Rahu and Ketu," transitioning
  into "Sloka 48 — The Vedhas pronounced as auspicious in the (Sarvatobhadrachakra)..."
- PG347:C1: "Saturn, the Sun, Rahu, Ketu and Mars are malefic" — inside the passage on how "three
  Vedhas arise" by aspect.
- **PG348:C1 (śl. 48, direct hit): "In the case of Rahu and Ketu, which are always retrograde, the
  Vedha will be on the right, and in the case of the Sun and the Moon which move direct... the
  Vedha will be on the left."**

PG348 is an explicit, substantive Rāhu/Ketu vedha rule. The sentence as written was false. It is
**not** a rule for the same mechanism the six unqualified rows need, though: PG348 governs the
Sarvatobhadra chakra's asterism-direction vedha, not the house-from-Moon transit vedha pairs at
ślokas 3-8 that `bg_transit_rules`' 41 rows encode. The disposition (6 rows unqualified for *that*
mechanism) survives; the universal absence claim does not, and is corrected in place across the
sheet, plan, and independent-review file, quoted as false and replaced rather than silently edited.

**2. The Venus transposition finding.** Kimi's claim — that ids 35 and 44 are exact transpositions
of already-correct rows 179 and 33 — was checked directly against the served rules
(`ref_transit_rules_get`): id 35 = (primary_house 3, vedha_house 11); id 179 = (11, 3) — an exact
reversal. id 44 = (8, 1); id 33 = (1, 8) — an exact reversal. Confirmed. Only id 45 = (9, 2), with
no matching row anywhere in the table to reverse against, is a genuine content error (text gives
9→11). This refines "L0 geometry correction" into "dedup for two rows, geometry fix for one,"
folded into the sheet and plan.

**3. Ruling 7's reconciliation direction.** Kimi's claim — that `routers/ephemeris.py` and
`panchang_engine/planets.py` already comply with MEAN_NODE and should not be touched by a
disposition-(b) fix — was checked by reading both files. `routers/ephemeris.py:82` computes Rahu
via `swe.MEAN_NODE` directly (not from `ephemeris_daily`), documented at the same file as "distinct
from the bounded 1900-2150 daily-grain ephemeris_daily table." `panchang_engine/planets.py` carries
an explicit, assertion-guarded "Phase 4B" mandate — `assert planet_id != swe.TRUE_NODE` — with five
separate comments naming TRUE_NODE "explicitly forbidden." Both are correctly MEAN-compliant today
and load-bearing on that guard. The defect is confined to the store (`ephemeris_daily`, migration
624, `l0_ephemeris.py:77`'s "Mean North Node" comment on a body that is in fact TRUE) and its own
fail-closed probe validator. The correction's direction — reconcile the store to the declarations,
not the declarations to each other — is now stated that way in all three files.

## Not independently re-derived; recorded as Kimi's own report

The remaining content of Kimi's review above — the six new tagged findings (sign-level probe
anchor insensitivity; `config_pin` not naming the node frame; the missing Mercury 8→1 row;
cross-class rank comparability; the governance-concentration observation; the self-certification
sweep finding none) and the five method-failure notes in its closing section — were not
independently re-run by the author beyond the spot-checks above. They read as consistent with
everything independently verified elsewhere in this packet and are recorded here as
execution-phase notes for whoever implements the corrected ruling 7/8/9 scope, not as verified
findings, and they re-open nothing.
