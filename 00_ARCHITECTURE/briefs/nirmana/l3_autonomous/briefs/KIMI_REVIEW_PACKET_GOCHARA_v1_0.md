# Review packet — Gochara family (ka_gochara · ka_gochara_resonance · century · Vedha · Moorti): the final elevation plan v2.0

You are Kimi K3, asked for a **thorough independent review** of the final elevation plan for the
Gochara (transit) asset family of this Jyotiṣa instrument, and for **recommendations**. The native
(Abhisek Mohanty — the chart owner and the ruling authority) will read your answer before ruling on
the eleven decisions the plan puts to him, and the plan will then be used for the L3 (Kāla) elevation.
You are not the authority — you advise. Standard: **acharya-grade.** A senior Jyotiṣa ācārya reading
your answer should find it at or above their own level, and a senior engineer should find nothing
hand-waved. Generic astrology is a failure; so is generic engineering.

## Ground rules
- Do NOT write any file. Print your answer only.
- Read the document under review IN FULL before answering:
  `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_FAMILY_ELEVATION_PLAN_v2_0.md`
  (the plan; ~420 lines; §1 decision ledger, §3 findings F-01..F-22, §4 design, §5 upstream
  contracts incl. the target-resolution contract §5.3, §6 downstream contracts, §7 work packets,
  §9 cutover runbook, §10 proof matrix, Appendix C kernel spike).
- Read these for the measurements the plan cites (same directory):
  `GOCHARA_FAMILY_ELEVATION_BRIEF_v1_2.md` (Appendices B–E: live measurement record; the four-way
  node split; ephemeris backend and epoch; directed aspects) and `GOCHARA_FAMILY_ELEVATION_PLAN_v1_0.md`
  (the ratified decisions D-1..D-3 and R1–R10 — these are CLOSED by the native; do not re-open them,
  but do say if v2.0 contradicts them anywhere). `ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md` is the earlier
  independent review; `evidence_gochara/OUTPUT_2026-09-20.txt` holds the E1–E8 outputs.
- Read the code for depth (paths relative to the working directory):
  `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara.py` (the W2-eligible writer;
  `TABLE` at 120, `date.today()` at 268, generation at 336/362, build-state upsert 438-458);
  `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py`
  (the held century writer; generation constants 354/360, tables 482/487);
  `platform/python-sidecar/services/gochara_v3/engine.py` (λ_v3; activity at ~821; sentences
  gathered and discarded at 1063-1137), `interval_solver.py`, `threshold.py` (~393),
  `resolution_hierarchy.py`, `context.py` (reads at 289/355/405/449/510/553);
  `platform/python-sidecar/services/gochara_grammar/primitives.py` (dṛṣṭi table 189-196; kakṣyā
  fixture 664-719); `platform/python-sidecar/services/gochara_intensity/enrichment.py` (target
  resolution coverage, docstring 41-79); `platform/python-sidecar/services/ka_gochara_resonance/writer.py`
  (target builders 293-314; fetch SQL 380-414; 27-class gate 518-549);
  `platform/python-sidecar/services/w2g/{arcs,crossings,solver,db_source}.py` (the arc/solver
  functions the kernel re-homes; `db_source.py` is tropical at 35/80/178);
  `platform/python-sidecar/pipeline/transit_search.py` (TRUE node at 10/64; ephemeris path resolver
  187-200; directional aspect search 320);
  `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` (serving: provenance 573-598,
  authority filter 641-643, coverage attestation 926-1000);
  `platform/src/app/api/cockpit/clear/route.ts` (93, 95-96, 114-117) and
  `platform/src/app/api/cockpit/clear/execute/route.ts` (160-182); `platform/src/lib/cockpit/assetClearSpec.ts`.
- Governing texts you may consult: `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md`
  (§2 L3-Q01–Q13; §3 Contact / Search coverage / Temporal testimony objects; §5 P3 equivalence);
  `MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md` (F04 epistemic classes, F06 completeness
  states, F12 operator roles); `00_ARCHITECTURE/briefs/nirmana/MADHAV_PRODUCT_DEFINITION_v3_0.md`
  (§1.3, §3.10, §7.1, §9); `CLAUDE.md` §N.3–§N.8 (idempotency, cockpit truth, L1 authority, density,
  narration fidelity, earned signal); classical corpus at `00_ARCHITECTURE/SOURCE_DATA/classical_texts/`.
- For every recommendation: the option you recommend · why (classical basis with text/chapter where
  you can; engineering basis where relevant) · what it costs · what would falsify it · what you are
  NOT deciding. Mark each claim **[D]** doctrine (name the text), **[P]** practice, **[J]** your
  judgment, **[U]** you could not verify. Never present a number as fact — thresholds and weights
  are proposals for the native to ratify.
- The native's priority order: (1) quality of what the asset delivers, (2) build efficiency,
  (3) the surrounding ecosystem matters as much as the asset — an asset is not elevated if only its
  algorithm is; its upstream inputs and downstream readers must be confirmed and tested too.
- Binding constraints you must respect: no invented computed values (B.10); L1 facts are the
  authority, never restated (§N.5); no scalar "confidence"/"salience" field may be invented; a
  reduced cap, coarser grid or narrower horizon can never pass as an equivalent optimisation
  (Strategy §5); "another representation of the same origin adds no independent support" (L3-U02);
  a signal with no detector behind it is null, not green (§N.8); the protected `v1` rows and the
  century's `'3.0'` rows are untouchable; nothing is retired; no guard is weakened; the FROZEN
  orchestrator `WriterBase` contract (`@register`, `run(ctx)`/`plan_substeps`+`run_substep`,
  never commit `ctx.db_conn`) is not extended.

## What the Gochara family is
The L3 (Kāla) transit layer. `ka_gochara_resonance` derives per-chart natal *targets* (8 types, 27
event classes) from L0 rules and L1 facts. A scoring engine (λ_v3 = PROMISE × PERMISSION × activity
× tārā × w30 × quality_gates, in `services/gochara_v3`) turns transit contacts with those targets
into dated *windows* (`kala_gochara_windows`) served to three MCP tools, the reading checklist,
D8/D9 judgment and Kṣetra. Vedha and Moorti are overlay writers (obstruction, ingress quality);
Kota is proposed-use; `GocharaTransitService` is a live compute service Saṅgam calls. The retired
sweep's `v1` rows (38,287) are protected history.

## Verified facts about the current state (checked at source and live; do not re-litigate)
1. The product reads generation `'3.0'` — the **held** century writer's output. The active,
   W2-eligible `ka_gochara` writes `'2.0'` into `kala_gochara_windows_v2`, which **nothing serves**.
2. Served rows carry **no qualified contact**: `active_sentences='[]'` on 914/914 rows; partial
   records (planet, target, instant, orb decay) exist in `term_breakdown` on 380/914 rows; no orb in
   degrees, applying/separating, station branch, bracket, tolerance or coverage anywhere; all
   window columns are `DATE` grain. Contacts are computed and discarded before persistence.
3. **13 of 27 event classes have no timing window anywhere in the served century** (marriage,
   career_advancement, illness_acute, surgery, childbirth among them). Marriage 2013: one
   2004→2014 envelope where `v1` served 52 daily rows with contact sentences.
4. The century build takes hours (270 substeps; longest completed run 58.2 min; the native reports
   20–25 h end to end); 64 ms per evaluation, ~92 % of it repeated per-instant search; the kakṣyā
   primitive runs on an **uncited equal-eighths fixture** on the served path (59 % of cost; served
   activity ∈ [0.99964844, 1.0]).
5. The `ka_gochara` arc index is built on **tropical** longitudes and joined to sidereal natal
   targets (Saturn contact error up to 763 d). Its horizon moves with `date.today()`.
6. **No protection trigger exists** on the protected table (migration 588 dropped them 2026-08-23);
   the cockpit Clear route can reach the 38,287 `v1` rows through the retired sweep's own
   `count_sql`; the restore identity lacks SELECT on its own archive.
7. **Node convention is a four-way split**: served L1 natal = MEAN node (`RAH_MEAN`, pāda 3 of
   Rohiṇī); L0 daily knots = TRUE node (stored equals Swiss TRUE to 0.000″); `transit_search.py`
   and `l1_positions.py` + importers = TRUE; at the birth instant TRUE lands in pāda 4. Blast
   radius measured (40/765 targets; 232/914 served rows; 6,225/16,297 `v1` rows).
8. Swiss Ephemeris silently falls back to Moshier unless `set_ephe_path` is called (`retflag 260`
   vs `258`); the `.se1` files exist locally and in the deployed image; Moshier's true-node error
   is bounded at 65.3″ over 55,152 noon knots. Stored knots are noon UT.
9. Target resolution today: only karaka / dasha_lord_portfolio get a degree; bhava gets a sign;
   lord / arudha / sensitive_degree / mechanism_node / yoga_constituent get nothing — 609 of 765
   targets (79.6 %) reach the engine without a degree. Measured referents: 154 of 176
   `sensitive_degree` targets cite a NEGATIVE check (`not_gandanta`, `not_pushkara`, `mrityu_bhaga
   not_fired`, `kartari none`); every `arudha_pada.longitude_sidereal` is an exact sign-cusp
   multiple of 30°; 2 of 13 `yoga_constituent` ids (`ardhachandra`, `chatra`, 54 rows) have no
   `ga_yoga_firings` row for the chart today. L1 does carry real degrees for special lagnas (7),
   nakṣatra pādas (4), Gulika/Māndi (2), Prāṇapada (1), bhāva-ārūḍhas (14) that resonance never targets.
10. Directed special dṛṣṭi (Mars 4/7/8, Jupiter 5/7/9, Saturn 3/7/10, nodes as Jupiter; BPHS
    Ch.26) is correct and exercised on this family's path; Saṅgam's own call site uses a symmetric
    generic set — that is Saṅgam's defect, not this family's.
11. Hidden edges: Saṅgam reads `kala_vedha_gochara` undeclared; Kṣetra reads the served windows
    table undeclared and pins provenance edges by row id.
12. A kernel spike on real Swiss files (retflag 258) reproduced stored knots to 0.002″ and matched
    direct Swiss root-solves for Mars, Saturn (incl. a retrograde triple pass at the 270° dṛṣṭi)
    and the Moon within ≤0.96″ / seconds, with a clean negative control.

## What the plan proposes (so you can aim your critique)
`ka_gochara` becomes the served owner under a new immutable publication generation `'4.0'` in
`kala_gochara_windows` beside `v1` and `'3.0'` (N-5, N-10); a new deterministic kernel solves each
(body × target × relation) once per chart on Swiss-sidereal arcs and persists **episodes** as a
Contact ledger `kala_gochara_contacts` with orb, branch, bracket, tolerance, `contact_id`,
`independence_group`, F04/F06/F12 qualification and a Search-coverage manifest (N-7); the century's
λ_v3 becomes a projection over that ledger (N-6; honesty fixes H-1..H-6; method calls M-1..M-6
deferred to evidence); the resonance target set is corrected per the target-resolution contract
(§5.3; N-12); the node convention is ruled mean with analytic derivation from the true-node knots
(N-4/N-4a); guards and the Clear route are fixed first (N-1); serving gets explicit `'4.0'`
branches (P-1), the reading checklist carries ids (P-2), L5 gets `contact_id` (P-3), a ledger read
capability is added (P-4); Saṅgam and Kṣetra declare their edges (V-1, K-1); the registry is
re-pinned by migration (§6.3); cutover follows a ten-step runbook with rollback by head re-point (§9).

## What I need from you — in this order

### A. Verdict and blocking gaps
Is the plan complete enough to execute the L3 elevation of this family as written? Name every gap
that would block a competent implementer, in severity order (BLOCKING / MAJOR / MINOR), each with
the section it belongs to and what would close it. Say explicitly if any part is internally
inconsistent, contradicts a ratified decision (D-1..D-3, R1–R10), or violates a binding constraint.

### B. Astrological review — is the geometry and the target set right?
1. **Contact object and episodes (§4.2–4.3):** are `t_in / t_exact / t_out`, orb, applying/separating,
   station branch and dwell the right classical primitives for gochara contact? Which orbs and which
   relations (conjunction, dṛṣṭi, sign/nakṣatra ingress, kakṣyā crossing, return) have textual basis
   and which are practice? Cite texts [D] where you can (BPHS, Phaladīpikā, Sārāvalī, Bṛhat Saṃhitā,
   Jātaka Pārijāta, Praśna Mārga, Uttara Kālāmṛta — whichever actually speaks).
2. **Target-resolution contract (§5.3):** for each target type, is the resolution rule classically
   defensible? In particular: (a) treating ārūḍha as a rāśi (sign-level) target rather than a degree —
   right or wrong, and under which school (Jaimini vs later)? (b) treating negative sensitive-degree
   checks as non-targets; (c) resolving `lord` targets through whole-sign house lordship; (d) yoga
   constituents as an `independence_group`; (e) mechanism nodes as residence spans. Where should
   bhāva-madhya (cusp) contact matter (M-5)? Is there doctrine for transit over the natal Gulika/Māndi,
   Prāṇapada, special lagnas, nakṣatra pādas, bhāva-ārūḍhas (E-1 / M-6)? Which of E-1 would you admit
   first, and on what text?
3. **Node convention (N-4/N-4a):** mean vs true node for gochara — what do the texts and the
   dominant living traditions actually use, and is deriving mean at read time from true-node knots
   an acceptable engineering answer, or does it hide a doctrinal choice?
4. **Scoring projection (§4.5, §8):** does keeping λ_v3's factor algebra as a projection over the
   ledger preserve or distort the astrology? Which of H-1..H-6 is not purely an honesty fix? Which of
   M-1..M-6 would you rule first, and how? Is anything classically load-bearing missing from the
   factor list (e.g. vedha specifics, aṣṭakavarga kakṣyā weighting, Sade-Sati phases, retrograde
   weighting, latta, tārā-bala)?
5. **Overlays (§5.4):** Moorti at true ingress vs day-grade; Vedha `independence_group`; Kota's
   proposed-use gate — right?

### C. Engineering review — will it work, end to end?
1. **Kernel (§4.2, App. C):** is the arc-index + Swiss-bisection design sound for stations,
   retrograde loops, seams, horizon edges and the Moon? What is missing from the feasibility spike
   before WP3a can be trusted? Is the ε/tolerance contract sufficient?
2. **Ledger and publication (§4.3, 4.7):** schema gaps; `contact_id` derivation stability; the
   `'4.0'` label choice vs the serving code's `'3.0'`/`g3_*` routing; the immutability rule; the
   size estimate.
3. **Upstream (§5):** anything the kernel needs that the plan has not sourced from L0/L1? Is the
   input generation vector (§5.5) enough to catch drift like F-21?
4. **Downstream (§6):** is the reader inventory complete? Are P-1..P-4, S-1, V-1, K-1 correctly
   scoped and owned? Are the registry re-pins (§6.3) complete and safe (count_sql, clear_tables,
   integrity conjuncts, depends_on, digest spec 1018)? Does the Clear route become safe?
5. **Cutover and rollback (§9):** is the ten-step runbook ordered correctly? What fails if steps
   are reordered? Is rollback genuinely provable through the real serving adapters?
6. **Tests (§10):** which proof rows are vacuous as written, and what would make them real detectors?
7. **Efficiency (§4.5):** does the design credibly remove the per-instant search without any of the
   forbidden shortcuts? What should the cost profile measure so a speedup claim is honest?

### D. Elevation, enrichment, improvement
Beyond gaps: what would make this family *better than a senior ācārya's own transit reading*? Name
concrete enrichments with classical basis and their cost, ranked; say which belong in this elevation
and which should wait.

### E. Per-decision recommendations
For N-1, N-4, N-4a, N-5, N-6, N-7, N-8, N-9, N-10, N-11, N-12 and for M-1..M-6: your recommended
option, why, cost, falsifier, and what you are not deciding. Where you disagree with the plan's
recommendation, say so plainly and give the better option.

## Deliverable
A single structured answer with headings A–E above. Severity-ordered findings in A. Every claim
labelled [D]/[P]/[J]/[U]. Quote file:line for every code claim you make and section numbers for
every plan claim. Be specific and complete; length is not a constraint, hand-waving is.
