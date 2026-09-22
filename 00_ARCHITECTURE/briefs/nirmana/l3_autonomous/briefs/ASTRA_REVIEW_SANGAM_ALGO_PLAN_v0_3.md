---
artifact: ASTRA_REVIEW_SANGAM_ALGO_PLAN
version: "0.3"
status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
reviewer: "Codex gpt-6-astra — independent adversarial review"
date: 2026-09-22
verdict: REWORK
reviewed_plan_sha256: 7f1fe9ff5b09260fe5bfc0e5ff7043a9be5773f59a344176d5697ce028ce0e3e
authority: "Review only; authorizes nothing."
---

## A. Claims

### A.1 Every row of the §0.1 disposition ledger

`APPLIED` means the revision actually incorporates the stated disposition as a plan requirement. It does **not** mean implemented, tested, protected, deployed, or accepted. `LISTED_NOT_APPLIED` means the cited section repeats an obligation without supplying the promised substance. `MISAPPLIED` means the application contradicts the disposition or the evidence. Original finding IDs are retained; new re-review findings use `RR-01` onward.

Citation shorthand: **P** is `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ALGORITHM_ELEVATION_PLAN_v0_3.md`; **R** is the sibling `ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_1.md`; **B** is the sibling `SANGAM_ELEVATION_BRIEF_v1_0.md`. Other keys are expanded in A.2. Sections below distinguish an applied correction from a remaining defect instead of treating all unfinished implementation as a failed disposition.

| §0.1 row | Disposition | Section actually checked and result |
|---|---|---|
| F-01 | APPLIED | §3 R-1 and §1b.1 require sourced targets and unavailable state. The separate “never 0°” falsifier is wrong for a legitimately sourced Aries origin; correct it under RR-03. P:163,197,287. |
| F-02 | APPLIED | §3 E1 explicitly requires directed source/target semantics and reverse-branch tests; S2 supports the arithmetic. This is a specification, not proof of an adapter. P:205–218,292; S2:5–17. |
| F-03 | MISAPPLIED | §3 E2 correctly chooses sign facts, but §0.1/S3/§3b invent a lagna rotation absent from the real producer. Legacy HOUSE_N and SIGN_N have the same absolute-sign values. RR-02. P:87,220–229,293; GS:970–979,1026–1036. |
| F-04 | APPLIED | §3 E2 removes the SAV-and-BAV conjunction and proposes a signed BAV verdict. Its integration with the retained nonnegative score remains unspecified, addressed in RR-05. P:220–229,293. |
| F-05 | APPLIED | §3 E2 explicitly defers contributor-specific kakṣyā to a bounded L1 amendment; it no longer claims boundaries alone provide the contributor matrix. P:226–227; AS:216. |
| F-06 | APPLIED | §3 E3 withdraws the count cap and specifies complete enumeration within declared scope, with incomplete/resumable state. §3b's universal-looking count of five still needs a dated fixture. P:231–240,294. |
| F-07 | APPLIED | §1b.9/.16 and E4 distinguish short-period flag, boundary annotation, and serving-layer capability aggregation. P:171,178,242–254. |
| F-08 | APPLIED | E4 expressly withdraws applicability gates and multipliers for weak/adverse natal evidence. Existing dignity suppression remains a separate unclosed interface defect. P:242–254; E:1221–1223. |
| F-09 | APPLIED | E5 withdraws the ICC repair claim and directs testing toward downstream aggregation. Testing only active months is insufficient to detect duplicated weights; see B/E5. P:256–264,296. |
| F-10 | APPLIED | E5 specifies child contact intervals and labels the hull an envelope. S8 supplies candidate crossing points, not proof of interval occupancy or gap handling. P:256–264; S8:19–36. |
| F-11 | APPLIED | E6 separates geometric frequency from predictive rarity and demands exposure/coverage. The denominator and counting strata are still incomplete. P:266–274; B/E6 below. |
| F-12 | MISAPPLIED | R-5 adopts stable identity and immutability, but E6 still puts `model-invalidated` in the same mutually exclusive outcome enum as hit/miss. Model validity and observed outcome require separate fields. §4 also omits an explicit R-5 implementation gate. P:201,270–273,309–316. |
| F-13 | APPLIED | R-2 replaces exact endpoint grouping with simultaneous intersection and hierarchy. Its empty/zero/unavailable semantics and falsifier need amendment; the core repair is present. P:198,288; DS:76–78,194–212. |
| F-14 | MISAPPLIED | R-3 adds frame context but proposes a dedup key dropping signal, mode, method and node convention. A reusable geometry key cannot be the testimony identity. Other current readers remain hardcoded or unqualified. P:199; W:760–765,1059–1071,1149–1162. |
| F-15 | APPLIED | R-4 explicitly requires actual egress, measured shoulders, tangencies and horizon-edge occupancy. S7 does not test those requirements. P:200,290. |
| F-16 | LISTED_NOT_APPLIED | R-4 addresses C8, C11 and domain lord selection, but omits the accepted correction of generic benefic-dṛṣṭi weights. Neither a governing contract nor a falsifier covers E:442–482; C9 and post-engine TRIGGER composition also require the same audit. P:60,200; W:49–114. |
| F-17 | LISTED_NOT_APPLIED | §6 says each E states applicable, selected and served sets; no E actually enumerates all three or reconciles existing caps across the consumer paths. Calling the old superset test a regression check is useful but insufficient. P:359–367,369–375,385–386. |
| F-18 | APPLIED | §6 explicitly requires an L3-U04/U11 packet and served sentinel rather than assuming JSONB is consumed. Concrete paths and sentinels remain to be supplied; section E supplies the missing review. P:372–375. |
| F-19 | APPLIED | R-5 and §6 require a dependent map before rebuild. The proposed preservation detector is too weak and partly non-executable; RR-08 is an acceptance-specification defect, not denial that the requirement was added. P:201,350–357. |
| A-01 | MISAPPLIED | R-4 requalifies I-17/C11, but §1 still preserves the quota selector and self-scoped delete “unconditionally.” A capped selector is not a complete universe, and delete safety depends on the admitted generation/cascade design. Preserve transaction ownership and resumability, not those policies unconditionally. P:149–151,200; B:337–371. |
| A-02 | APPLIED | E2 records edition-to-stored-value mapping and leaves equality to an explicit decision. It does not invert the adapter's benefic counts based on vocabulary alone. P:223–228; AS:187–228; BP2:35666–35684. |
| A.3 doctrine | MISAPPLIED | E1 correctly restores fractional Parāśari aspects and Tājika legitimacy, but §3b(c)'s “never under Parāśari” square fixture contradicts those very fractional/full fourth aspects if interpreted geometrically. The doctrinal exclusion and method-label exclusion must be separated. P:207–215,292. |
| C.1 F-13…F-16 | APPLIED | Stage R includes the four repair areas; the F-14/F-16 application defects above remain open. Inclusion is not closure. P:197–200. |
| C.2 techniques | APPLIED | §5 rules each candidate in/out, with bhāva-madhya placed in R-1/M-1a. Qualification and source contracts, especially actual annual Tājika inputs, still need substance. P:197,326–334,395. |
| D.1 sequence | LISTED_NOT_APPLIED | §4 step 1 amends identity documents; step 2 executes only R-1…R-4. It does not explicitly implement and qualify R-5 before E1 changes contacts. E4 is before E3, but annual judgment has no scheduled delivery gate despite “ahead of E3.” P:309–315,238–239. |
| D.2 P4 | LISTED_NOT_APPLIED | §6 names benchmark dimensions but supplies no per-E complete-universe contract; its supposed executable acceptance machinery permits false success. Withholding speed claims is applied; the promised qualification machinery is not. P:340–367; RUN:5–7; RR-01. |
| D.3 lineage | LISTED_NOT_APPLIED | §4 gives sound prohibitions but says “each declares roots” without enumerating source fact/generation/rule roots for each route and consumer. E4's capability/varga correlation and existing TRIGGER composition are not mapped. P:317–321; W:49–114. |
| E.1 consumers | LISTED_NOT_APPLIED | §6 names three consumers and assigns all seven a future “decision per E.” There is no seven-by-six disposition or check for the actual SQL break when confidence/rarity columns disappear. P:369–375; CW/ka_kala_darshana:24–31. |
| E.2 served | APPLIED | §6 correctly says EXPLAIN has no automatic edge and requires managed changes. It does not justify a direct PRIORITY effect; my previous review overstated that effect, corrected in E.2 below. P:372–375; R:273. |
| E.3 rebuild | APPLIED | The dependent preservation requirement is explicit. Its count/hash detector and identity-to-content binding must be replaced before it can demonstrate safety. P:350–357; RR-08. |
| F verdict — three changes | LISTED_NOT_APPLIED | Repairs are substantially specified, but the claimed executable evidence, first identity gate, and ecosystem dispositions are incomplete. The high-value direction is incorporated; the three changes are not all closed. P:115,197–201,309–321,340–388. |

### A.2 Provenance, citation key, and limits

Reviewed disk plan, prior review, evidence, companion, cited producer/consumer sources, governed strategy/context, June ruling and classical corpus. Branch observed: `l3/kala-elevation-readiness`; HEAD `feec1354588ca3ca9a60e091c9f43919b85f635e`; local `origin/main` `b997ee0bd42efb9c7cd4ca2799d2732727a3482c`. A byte comparison against `git show origin/main:<path>` confirmed equality for engine, Saṅgam writer and transit scanner. No fetch occurred; this is not verification of the current remote tip.

Only this new review is an authorized write. No plan/source/evidence edit, build, migration, DB query/write, PR, or v0.1 overwrite was performed. Generic session logging requirements were bounded by the explicit one-file instruction; no session-close or acceptance claim is made. The request calls RUN_ALL read-only, but RUN:5 truncates a sibling output file. I replayed its script loop with output captured in memory; the exception and exact replay recipe are in A.5.

| Key | File, relative to this worktree unless a URL is given |
|---|---|
| E | `platform/python-sidecar/services/ka_sangam/engine.py` |
| W / CW/name | `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` / `platform/python-sidecar/pipeline/orchestrator/writers/name.py` |
| T | `platform/python-sidecar/pipeline/transit_search.py` |
| YB / YW | `platform/python-sidecar/services/ka_yojaka/binder.py` / `platform/python-sidecar/pipeline/orchestrator/writers/ka_yojaka.py` |
| DS | `platform/python-sidecar/services/ka_dasha_kala/service.py` |
| GS / GD / GV | `platform/python-sidecar/ga_writers/ga_strength_writer.py`, `ga_dashas_writer.py`, `ga_vargas_writer.py` respectively |
| AS | `platform/python-sidecar/pyjhora_adapter/strength.py` |
| CAP | `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dasha_lord_capability.ts` |
| Q / WRAP | `platform/src/lib/retrieval/registry/layers/L3_kala/query_convergence_windows.ts` / `call_service_wrappers.ts` |
| TR | `platform/python-sidecar/services/ka_tulana/ranker.py` |
| TG | `platform/python-sidecar/services/kala_trigger/trigger.py` |
| KV/name | `platform-mcp/src/tools/kala_views/name.ts` |
| S | `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` |
| K | `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ASSET_BRIEF_CONTEXT_v1_0.md` |
| JUNE | `00_ARCHITECTURE/CONDUCTOR/cleanup/L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md` |
| BP1 / BP2 | `00_ARCHITECTURE/SOURCE_DATA/classical_texts/BPHS/bphs_vol1_rsanthanam_djvu.txt` / `bphs_vol2_rsanthanam_djvu.txt` |
| RUN / OUTPUT | `P`'s sibling `evidence_sangam/RUN_ALL.sh` / `evidence_sangam/OUTPUT_2026-09-22.txt` |
| S1…S10 | Sibling evidence scripts: `S1_target_default_zero.py`, `S2_directed_aspect_arithmetic.py`, `S3_frame_confusion_nonaries.py`, `S4_moon_contact_count.py`, `S5_rarity_angle_fraction.py`, `S6_overlap_key_exact_pair.py`, `S7_gate_not_streaming.py`, `S8_saturn_loop_oracle.py`, `S9_sandhi_flag_meaning.py`, `S10_mode_a_necessary_terms.py` |

Source reachability is established; live incidence, current protected generations, both production charts' asserted Aries lagnas, runtime service health, predictive superiority and production compatibility are **UNVERIFIABLE in this review**. No code comment, saved report, chart identity, or native ruling substitutes for those observations. Classical verification below is edition-specific; OCR uncertainty is identified rather than silently normalized.

### A.3 Every [C] baseline row in §1

| P row | Verdict | Verified evidence and qualification |
|---|---|---|
| Mode A, P:129 | CONFIRMED | E:1113–1142 uses queried lord eligibility when available, otherwise a static prior; E:1221–1223 makes dignity/orb/vedha necessary and daśā supporting. This describes the kernel, not final persisted score after W:682's TRIGGER composition. |
| Mode B, P:130 | CONFIRMED | E:1363–1404 searches, then gates orb and magnitude; no daśā prerequisite. W:702 supplies the magnitude threshold. |
| Mode C, P:131 | CONFIRMED | E:1621–1635 uses real ingress plus period/12 for the end. It does not prove occupancy until an observed egress. |
| Mode D, P:132 | CONFIRMED | E:1673–1683,1723–1727,1739–1758; W:721–737. Current sign/SAV scan takes a first predicate's identity/context and estimated end. |
| Target, P:133 | CONFIRMED | No semantic binder target; W:277–298 passes trigger JSON through. Defaults at E:1148,1377 and W:662. YW:417–418 persists the trigger; source evidence does not count live unbound predicates. |
| Contact model, P:134 | PARTLY | T:320,331–351 does target-plus-angle, one unsigned branch and zero-crossing search. The angles/orb are engine defaults, E:1148–1150; YB's YOGA trigger can specify a narrower orb. “Orb 5°” is not universal, and T does not itself enforce a full occupancy interval. |
| Planet, P:135 | CONFIRMED | E:992–1015 maps DIGNITY to its graha and DISPOSITOR to its lord, without a slow-only allowlist. Reachable fast search does not establish compliance with June authority. |
| Gate, P:136 | CONFIRMED | T:351–371 accumulates before returning; E:1154 precedes E:1171's gate. No demonstrated streaming-memory saving. |
| C11, P:137 | CONFIRMED | E:251–298 returns 0.3 for matching obstruction and 1.0 when rules are missing. It consumes precomputed time ranges; “house-from-Moon frame” is a producer contract, not a local house recomputation. |
| C7, P:138 | CONFIRMED | E:103–138 leaves C7 unavailable; W:991–1024 reads legacy category with fixed Lahiri and loses fact IDs. Legacy naming does not establish numerically rotated data; RR-02. |
| C8, P:139 | CONFIRMED | E:141–186 does not use the supplied target longitude for the proposed relevance distinction. |
| C12, P:140 | CONFIRMED | E:648–691 compares the selected lord with annual/Munthā lords at the window start, using inclusive boundaries. This is a limited lord-match feature, not a complete annual chart judgment. |
| C13, P:141 | CONFIRMED | W:989 documents unpopulated convergence scores; E's school-consensus current therefore lacks its intended input. TG's separate informational school feature is also not an automatic populated input. |
| Cross-daśā, P:142 | CONFIRMED | DS:76–78,194–212 uses exact start/end keys. S6 directly reproduced unequal keys for overlapping intervals. |
| Daśā depth/interval, P:143 | CONFIRMED | E:1124 requests depth 3; DS:102 defaults to 4; E:1140 performs an inclusive endpoint test. A precision/boundary amendment is required before claiming exact simultaneity. |
| Frame, P:144 | CONFIRMED | T:242–272 fixes sidereal context/node behavior; W:276 carries predicate ayanāṃśa; W:879–886 dedups on mode/date/signal and omits geometry/context components. Output lacks the proposed explicit context identity. |
| Shoulders, P:145 | CONFIRMED | E:1186–1187,1412–1413 uses fixed ±15-day shoulders. |
| Rarity, P:146 | CONFIRMED | E:971–989 implements angle-scaled period; direct S5 call gives Saturn opposition 14.73 years. A fixed angular target does not acquire twice the recurrence rate merely by being an opposition. Exact geocentric episode spacing is not necessarily one constant sidereal period either. |
| L1 unread, P:147 | CONFIRMED | GS:1028–1036,1071–1083 emits the named sign facts/boundaries; GD:1042–1062 emits precise clock fields; GV:973–1002 emits natal varga positions. Current Saṅgam readers do not consume the proposed material. Existence in writer source is not a live-data completeness receipt. |

The extra “preserved unconditionally” line is **PARTLY**, not an established engineering baseline: transaction ownership, resumability and scoped SAVEPOINT handling are reusable mechanisms, whereas capped selection, deletion policy and current-state semantics remain subject to coverage and generation contracts. E:731–756 represents computed/honest-empty availability, not the proposed signed route calculus. P:149–151; W:274–305,572–579; K:28–53.

### A.4 Every §1b source-contract row

| # | Verdict | Evidence, and what is still missing |
|---|---|---|
| 1 | CONFIRMED | YB:39–131,231–238 and W:277–298 support the unbound trigger claim. R-1 must specify detector selection per trigger type; natal-point binding is not a universal interpretation of relational/house rules. |
| 2 | PARTLY | E:1113–1142 uses the full supplied lord set and can fall back to a prior. But the producer contract is not merely “binder”: YW:244–310,392–418 enriches eligibility and records resolution reasons. Preserve that source/reason lineage. Successful empty or zero eligibility must not be merged with service failure. |
| 3 | CONFIRMED | W:276; E:1099; T:242–272. Default is implemented but is not authority to silently change a context. The plan's nearby E:1097 citation is imprecise. |
| 4 | CONFIRMED | W:337–360 selects the first domain and substitutes 0.5 in ranking. The required multi-domain contract is valid, but each domain must retain its own role/lord rather than duplicate one score across an array. |
| 5 | PARTLY | W:758–765,1143–1166 confirms the queries, but P's null/default “—” omits default Aries at W:1149 and the fallback retained at W:1162. Moon reads fix Lahiri; the lagna query does not qualify ayanāṃśa. ORDER BY alone fixes neither defect. |
| 6 | PARTLY | All named categories and current null/default behavior exist, GS:970–1036 and W:991–1024. The proposed reader-only distinction of missing-planet zero versus measured zero is impossible after GS:1026 has emitted identical rows. Requires a bounded producer completeness/validity amendment. RR-02. |
| 7 | CONFIRMED | W:832–861 resolves coordinates and timezone, but calculates an offset at run time. Birth-instant zone resolution and explicit UTC/offset provenance are required. Fail-loud missing location does not prove correct historical offset. |
| 8 | PARTLY | W:866–876 does derive a year from minimum level-1 period start. Calling this birth-year derivation is not proof that the earliest stored period begins at birth; no contract establishes that invariant here. Leave actual birth-year equivalence **UNVERIFIABLE** until compared with authoritative birth input. |
| 9 | CONFIRMED | GD:1042–1062 proves ISO fields and `duration_days < 20`. ISO output can itself be reconstructed at midnight where source precision is unavailable; boundary annotation must carry actual precision. |
| 10 | CONFIRMED | E:1113–1140; DS:38–54,76–78,194–212. Date grain and exact keys are real. Implement atomic simultaneous intersections with parent hierarchy, not transitive merging of any overlapping supporters. |
| 11 | PARTLY | Scanner constraints are confirmed by T:242–272,301–371. P combines KaGocharaService and the scanner as one source contract although each consuming current needs its own context audit. The existing scanner signature does not accept the proposed context arguments; P's bounded-amendment escape is an unresolved prerequisite, not proof an adapter can supply them. |
| 12 | CONFIRMED | W:1055–1073 reads precomputed vedha windows, using a fixed context and losing full source identity; E:251–298 supplies optimistic missing behavior. Declare the edge, generation/context and completeness before absence can mean no obstruction. |
| 13 | PARTLY | W:1098–1120 and E:675–690 confirm limited annual lord consumption and inclusive start-only matching. Fixed Lahiri and missing/failed-read state also belong in the contract. A full annual Tājika method needs more than this table. |
| 14 | CONFIRMED | W:989 and E's unpopulated C13 input support the absence; remove an uncomputed term from claimed evidence/coverage denominators rather than recording agreement zero. |
| 15 | CONFIRMED | GV:819–828,973–1002 establishes natal varga computation/positions. “Natal” and the selected varga/ayanāṃśa must survive consumption. A position row alone does not provide a complete rule for promise, cancellation, strength and domain. |
| 16 | CONFIRMED | CAP:6–33,174–204 computes a serving aggregation for Vimśottarī MD lords, with averaged varga evidence. It is neither a stored universal L1 floor nor an all-clock lord authority. Citing it also requires identifying the contributing underlying facts. |

**RR-04 — High: the source contract remains incomplete in consequential ways.** R-3's proposed tuple is acceptable only as the beginning of a geometry cache key. Testimony identity must additionally retain chart, signal/predicate, route, mode, method/version, node convention, target identity, relevant source generations and precise interval/contact identity. Share geometry without coalescing distinct claims. Reject missing lagna/Moon context honestly instead of silently using Aries; qualify all current readers, not just the scanner. Preserve a successful clock query with zero support as evaluated evidence; reserve unavailable for missing/failed inputs and inapplicable for a genuine method-scope decision. Sources: P:198–199; W:760–765,879–886,1143–1166; DS:184–212; S:285,442.

### A.5 Replay and adversarial evidence audit

**RR-01 — Blocking: the evidence suite is predominantly demonstration output, not a falsifier.** RUN:5 overwrites `OUTPUT_<date>.txt`; RUN:6 catches script failures and continues; RUN:7 counts lines rather than validating their result or the expected suite. Most scripts print CONFIRMED unconditionally. The plan's “if any script's verdict flips” acceptance mechanism therefore does not work. P:340–347.

To satisfy the one-file restriction I did not execute the mutating runner literally. I used the same interpreter, working-directory selection, `S*.py` expansion and script bodies, removing only output-file setup/redirection and the final file-summary command. Replay completed with exit 0, ten VERDICT lines, **nine** CONFIRMED lines and S8's non-CONFIRMED oracle statement. This refutes P:342's “all CONFIRMED”; it does not refute the independently checked source defects. An initial attempt to redirect to `/dev/stdout` failed before scripts ran; the pipe-capture replay below succeeded. No saved evidence output changed.

Command actually used, with the replay portion shown independently of the subsequent mutation checks:

```python
# Executed using:
# /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/venv/bin/python -B -
from pathlib import Path
import subprocess
p = Path('00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/evidence_sangam').resolve()
s = (p / 'RUN_ALL.sh').read_text().splitlines()
s = [x for x in s if not x.startswith('OUT=') and not x.startswith('echo "wrote')]
s = '\n'.join(s).replace(' >> "$OUT"', '')
r = subprocess.run(['bash', '-c', s, str(p / 'RUN_ALL.sh')],
                   text=True, capture_output=True)
```

| Script | What replay establishes | Attack / limitation |
|---|---|---|
| S1:5–11 | Binder has no matching target field; current fallback exists. | Only conditional verdict in this set; REFUTED still does not cause a nonzero exit. String absence/presence does not validate actual target binding or all runtime producers. |
| S2:5–17 | Arithmetic exposes Mars/Saturn direction reversal; Jupiter's symmetric pair conceals it. | Does not call the adapter/scanner under a method contract. Its final verdict is unconditional. Test both directions, exact target and actual emitted provenance after implementation. |
| S3:10–20 | An invented house-rotated dictionary differs from a sign dictionary. | This is not GS's producer behavior. Its assertion can pass while the claimed real defect is false. RR-02. |
| S4:5–10 | Uniform-motion conjunction/opposition arithmetic provides a counterexample to the old count bound. | It is not a Swiss ephemeris count for a named real 60-day parent. No count assertion guards the verdict. |
| S5:5–9 | Calls the real rarity function and prints 29.46/14.73/7.37. | In memory, replacing `_rarity_years` with a constant 29.46 still printed CONFIRMED. This attack tests the verdict's dependence on evidence, not a proposed correct physical recurrence model. |
| S6:7–14 | Calls real exact-pair key function; fixture has 305 days by endpoint subtraction and unequal keys. | In memory, returning identical keys printed `keys equal=True` and still “keys differ → no agreement” CONFIRMED. Boundary convention also determines whether one calls this 305 elapsed days or 306 included dates. |
| S7:5–9 | Finds append/return/gate text; full control-flow inspection independently confirms accumulation. | Emptying all grep results in memory still printed CONFIRMED. It tests neither R-4 shoulders nor edge occupancy despite its placement beside that SPEC. |
| S8:9–36 | Produces useful candidate Saturn loop/control points. | Replacing crossing count with zero printed six CHECKs and a successful oracle statement. Emptying `loops` printed no cases and the same statement. No expected case count or assert guards completion. RR-09. |
| S9:4–5 | Prints the real short-duration assignment. | Supplying `sandhi_flag = False` instead still printed CONFIRMED. |
| S10:4–5 | Prints the present necessary/supporting assignment. | Supplying `necessary = [dasha_score]; supporting = {}` still printed the opposite CONFIRMED claim. |

Mutation method actually executed: `unittest.mock.patch.object` on imported E/DS/_common, `runpy.run_path` with stdout captured in `io.StringIO`, and `exec(compile(modified_S8_text, '<in-memory-S8>', 'exec'), {})`. Only in-memory functions/text changed. Production and evidence files were not patched. The observed results above are repeatable without a database.

Required acceptance design: each script asserts a named proposition, exits nonzero on contradiction/missing evidence, and states whether it expects a pre-fix defect or a post-fix behavior. The runner propagates any failure, checks the expected case manifest, and does not overwrite its source evidence. Include negative controls that must fail. A source regex may support reachability; it cannot claim behavioral qualification. P:340–347; RUN:5–7; S1–S10 as cited.

**RR-02 — High: the non-Aries falsifier misrepresents the real producer, and zero provenance is already lost.** GS:970–979 explicitly describes absolute-rāśi indexing. GS:1028–1036 writes both `HOUSE_N` and `SIGN_N` from the **same** value without a lagna transformation. S3:12 instead rotates the values by Capricorn lagna. It tests a hypothetical producer, not this producer; C7 is disabled in E:103–138 anyway. Consequently “Aries charts conceal the present numeric rotation bug” is not demonstrated. Migrating to the correctly named sign category remains good interface design.

I additionally executed an in-memory AST extraction of the real `GS._build_ashtakavarga_rows` body, stubbing metadata/citation helpers but retaining its numeric/category construction. Saturn vector `[4,2,6,1,7,3,5,0,8,2,5,6]` emitted HOUSE_1 = SIGN_1 = 4 and HOUSE_10 = SIGN_10 = 2. Missing Saturn and explicitly all-zero Saturn produced identical Saturn rows. Thus downstream code cannot recover which zeros were fabricated by `bav.get(planet_name, [0] * 12)`. Add a producer completeness/validity receipt or reject unqualified generations; do not pretend a new reader can infer lost information. This is a bounded L1 amendment beyond the separately deferred contributor-matrix work. GS:1026; P:168,227–229,293.

**RR-03 — High: several proposed post-change falsifiers would accept the wrong thing or reject the right thing.**

| SPEC | Defect | Replace with |
|---|---|---|
| R-1, P:197,287 | A ban on all 0° targets rejects a legitimate sourced point at exactly 0° Aries. | Assert explicit source-backed binding, including a valid zero fixture and an absent target fixture. Missing is not numeric zero. |
| R-2, P:288 | Equality of `_build_overlap_key` is the old implementation, not the desired intersection oracle. | Expected intersection segments with supporter/parent sets; include unequal endpoints, disjoint intervals, nested levels, zero score, valid empty, failure and sub-day boundary precision. |
| R-4, P:290 | S7 only addresses full-list filtering. | Separate occupancy/tangent/egress tests and unavailable-vedha tests; keep S7 as a performance-path observation. |
| E1, P:292 | “90° never under Parāśari” is false as an angular exclusion; Mars has a full fourth and Jupiter a fractional fourth. | Same geometry may carry separately tagged Parāśari and Tājika evaluations. A Tājika inference must not be relabelled Parāśari; two labels do not create two independent roots. |
| E2, P:293 | Capricorn rotation fixture does not exercise GS; fabricated zero distinction is impossible at reader level. | Feed real GS output to the reader; independently test sign selection, vocabulary mapping, real zero, absent/null state and an incomplete-producer receipt. |
| E3, P:294 | Five contacts is pinned without a target, dates, ephemeris context or boundary rule. S4 supplies uniform arithmetic, not that ephemeris oracle. | Declare full fixture inputs and independently enumerated expected contacts; include varying phase, overlapping parents, no-contact parents and resource-interrupted resume. |
| E4, P:295 | Two whole charts with different D10 dignities need not have identical health rankings, nor must a disclosed career condition force a rank change when conditions are not multipliers. | Hold every other consumed fact fixed. Assert only the authorized domain-route condition changes, adverse remains applicable, and no unauthorized cross-domain leakage or boundary multiplier occurs. |
| E5, P:296 | Triple exact crossings do not demonstrate three disjoint orb intervals. Default 5° orbs can span a loop continuously. | Specify orb/threshold and exact child entry/exit intervals; include a genuinely disjoint occupancy case and a continuous-occupancy case. Test aggregate weights as well as active months. |
| E6, P:297 | A fully scanned declared 30-year horizon is complete for that horizon; it is incomplete only for a larger claimed exposure. | Bind coverage to the declared estimand/horizon. Test truncated lifetime coverage separately from complete restricted-horizon frequency. |

**RR-09 — Medium: S8 is useful exploratory geometry, not a pinned complete oracle.** Its daily speed sign detection brackets stations rather than solving them; crossing logic misses exact sampled zeros/tangencies; printed targets are rounded, station/contact dates and numerical tolerance are omitted, and expected loop count is unchecked. Replay yielded completed loops for 2026/2027/2028 with inside/outside 3/1 counts, including the wraparound loop. It did not establish a complete four-year station/episode manifest. S8:9–36.

A direct `swe.calc_ut(swe.julday(2026,1,1), swe.SATURN, FL)` check reported Swiss Ephemeris library 2.10.03, requested flags **65794**, returned **65860**: the calculation used **Moshier fallback**, not the requested SWIEPH data files. This does not by itself falsify the crossing geometry; it refutes a claim of pinned Swiss-file provenance. Record actual engine/data/flags, context, timestamps, precision, horizon clipping and a root-refined independent reference before this becomes an acceptance oracle. P:300–303's “Swiss independent referee” also requires an algorithm independent of the detector being tested, not merely the same library label. P:413's “no ephemeris test” conflicts with the shipped S8 run and should be corrected.

### A.6 Doctrine: every substantive [D]/[P] claim and retained [U]

The corpus was reachable in `00_ARCHITECTURE/SOURCE_DATA/classical_texts`, rather than the request's suggested `platform/` location. The following distinguishes a recognizable classical method from proof of predictive advantage. No traditional source establishes empirical superiority of this implementation.

| Claim / location | Judgment and primary anchor |
|---|---|
| Moon-relative gochara and vedha, E1 | Correct as a distinct contract; include stated exceptions and results by planet rather than converting all obstruction to one universal scalar. Phaladīpikā 26.1–8, [chapter translation](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621598.html). |
| Full/special/fractional graha-dṛṣṭi, E1 | Correct in the cited Santhanam edition: BPHS 26.2–5, BP1:16485–16505. A quarter third/tenth, half fifth/ninth and three-quarter fourth/eighth are not erased by the special full aspects. Generic Western angular weights are not a substitute. |
| Degree strength, E1 / I-17 in R-4 | BPHS 26.6–8 supplies a piecewise treatment, BP1:16514–16529; translator elaboration at BP1:16605–16652. Freeze directional normalization and special-planet additions against worked fixtures. A universal cos² curve and separating multiplier 0.7 remain **UNVERIFIABLE as classical rules**; label them a proposed model if retained. |
| Jaimini rāśi-dṛṣṭi, E1 | Recognizable and correctly separated. Movable/fixed exclusions and dual-to-dual rules appear in BPHS 8.1–3, BP1:8686–8692; degree irrelevance is discussed at BP1:8722–8723. Do not require an exact degree pass for sign applicability. |
| Tājika 60°/90°, orbs and itthaśāla, E1 | Legitimate within Tājika, not a reason to admit the current unsigned list as a universal Jyotiṣa method. [Hāyanaratna 2.1](https://www.wisdomlib.org/hinduism/book/hayanaratna-the-jewel-of-annual-astrology/d/doc1500892.html) describes aspects with variant strength schemes; choose the school. [Hāyanaratna 3.3](https://www.wisdomlib.org/hinduism/book/hayanaratna-the-jewel-of-annual-astrology/d/doc1500905.html) treats configuration and relative motion/orbs, including retrograde qualifications. A moving transit approaching a fixed natal target is not automatically an itthaśāla of annual-chart significators. |
| BAV own-planet values and ≥4/≤3 practice, E2 | Own-planet BAV reading is recognizable; the universal equality rule is not established by this plan. Phaladīpikā 23.10–11 should be retained with its dignity/placement conditions; exact equality at four remains an edition/translation adjudication, **UNVERIFIABLE here as a universal cutoff**. [Chapter 23 translation](https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621595.html). |
| SAV alternatives, E2 | BPHS 72.3–5 gives >30 / 25–30 / <25, BP2:42332–42354. Phaladīpikā 23.20 gives the >28/<28 distinction; equality at 28 is not supplied by that wording. Preserve alternatives with explicit school identity and no extra witness count. Same Chapter 23 source above. |
| Bindu/rekhā mapping, A-02/E2 | Correct caution. Santhanam BPHS 66.13–15 uses the adverse/benefic terminology noted in BP2:35666–35684; AS:187–228 stores benefic contribution counts. The storage label cannot determine polarity without the mapped convention. |
| Kakṣyā, E2 | Eight contributor-specific divisions have textual standing, Phaladīpikā 23.16–19. Boundaries alone do not reveal which contributor supplies a benefic indication; AS:216 discards the needed matrix. Reuse/expose L1 output with lineage; do not rederive it in Saṅgam. Same Chapter 23 source above. |
| Fast Sun/Moon and tāra, E3 | Phaladīpikā 26.2 and the Moon results in 26.12 support giving these planets their own temporal consideration; they do not prove that their contact peak dates a life event or provide the disputed count bound. Tāra 3/5/7 is explicitly a practice proposal here; its exact claimed textual anchor remains **UNVERIFIABLE**. Chapter 26 source above. |
| Universal sandhi gating / last-part amplification, E4 | Withdrawn correctly. BPHS 47.2–4 treats results by lord strength/condition and beginning/middle/end by drekkāṇa, with reversed ordering under retrogression; BP2:8926–8950. This does not establish a uniform junction penalty or “last part strongest.” Boundary distance is an engineering annotation, not yet a doctrine-derived signed result. |
| Weak lord remains operative, E4 | Supported in that same BPHS 47.2–4 discussion. Weakness/adverse delivery is not method inapplicability. The exact mapping to a domain's promise/denial remains a rule proposal requiring cancellation/context. |
| Domain vargas, E4 | D7 progeny, D9 spouse, D10 position and D4 fortunes are grounded in BPHS 7.1–8, BP1:7569–7593. This supports natal contextual use, not a universal veto or the full health-invariance assertion in §3b. |
| Retrogression/ceṣṭā and peak, E5 | BPHS 27.21–25, BP1:22725–22764, treats motion states and strength. It does not make the retrograde contact the default life-event date. No default phase is the defensible correction. |
| Hybrid sign interval with degree annotation, E1 | A declared synthesis/model choice, not a demonstrated single classical doctrine. It is acceptable only if the sign route remains valid without exact perfection and degree interpretation retains its own method/context. BPHS ch.8 versus ch.26; P:215–218. |
| Frequency and outcome model, E6 | These are statistical/software proposals, not classical doctrine. Geometric exposure does not supply an event base rate or calibration. P:266–274; S:447,450. |
| Node fifth/ninth aspects, Muhūrta Cintāmaṇi tāra verse, Narapati-jaya-caryā/Sarvatobhadra attribution | **UNVERIFIABLE** in this review at the requested exact source level. Existing served vedha functionality proves an available producer, not those particular textual attributions. Preserve P:409–410's uncertainty; do not promote it through M-1/M-3 by implication. |

## B. The six elevations

### E1 — AMEND: separate rule contracts and geometry sharing from testimony

The split into Moon-gochara, Parāśari graha-dṛṣṭi, Jaimini rāśi-dṛṣṭi and Tājika is a substantial improvement. A competent practitioner would recognize those methods separately. The strongest defensible design implements each selected method's actual rule and relevance conditions; it does not treat a Western-looking angle list as the common definition of all four. Sign applicability plus a degree annotation can be an explicitly declared hybrid; requiring exact degree perfection would still destroy legitimate sign-based testimony. P:205–218; BPHS ch.8/ch.26; A.6.

Jaimini belongs only on a qualified Jaimini route with its clock/karaka/argalā context. Dropping all 60°/90° signals loses legitimate Tājika material and can discard fractional Parāśari aspects; retaining their current undirected weights is not the remedy. For a directed aspect offset `a` from source to target, a fixed target `t` requires source longitude `(t-a) mod 360`, not generally `(t+a) mod 360`. S2 demonstrates why Jupiter alone is a poor regression fixture. Require source/target reversal and both legitimate contexts at the same angular separation. T:320; S2:5–17; P:292.

**RR-05 — Blocking: the method/state contracts have no coherent numerical or legacy coexistence boundary.** P retains `legacy_unsigned_angles` for a generation, while B:191–192 and B:325 preserve I-16/I-17/I-18/rarity semantics. Merely adding signed labels around a nonnegative combiner cannot meet the new contract: E:696–728 clamps/combines positive terms and E:1221 multiplies dignity into necessity. Direct in-memory execution of `E.convergence_score([0,1,1], {'constituent_lord_transit':1,'benefic_dristi':1})` returned **0.0**. This can erase intense adverse activity while E4 says weak/adverse remains applicable. Define activity, valence, applicability, evidence availability and any calibrated probability separately, with consumer-specific projections. Old and new method generations must have explicit compatibility selection; do not pool or rank legacy and new scores as interchangeable. S:447; K:28–53; P:213–218,242–254.

Acceptance alternative: validate a complete method-specific event manifest before reuse optimization; retain old rows as historical/versioned output with disclosed semantics; demonstrate one signed adverse, low-ranked condition surviving persistence and a real served query. The shared scanner remains frozen; an incapable signature raises a bounded dependency amendment before implementation. P:199; T:301–309; S:211–214,451.

### E2 — AMEND: use qualified sign facts and preserve adverse meaning

Consume existing sign-keyed raw BAV/SAV with fact IDs, generation, context and benefic-count convention. The frame is already settled by L1 producer code; it is not a new empirical question for the native or a reason to rotate a fixed vector by lagna. A different natal lagna can itself change a contribution, so “change lagna while holding the real BAV computation constant” is not a general physical chart experiment. GS:970–1036; BP2:35666–35684; RR-02.

Keep ≥4/≤3 explicitly provisional until the equality rule and contextual conditions are resolved. Do not combine SAV and BAV as independent confirmations; SAV contains the component BAVs. Do not feed `BAV/8` into the positive score and call the result signed. Require a structured verdict with source/rule/availability and separate route relevance; an adverse indication can accompany high activity. P:220–229; BPHS 72.3–5; Phaladīpikā 23.10–20; RR-05.

Kakṣyā is potentially useful for a specifically selected finer gochara method, but the first useful amendment is exposure of the existing contributor matrix, not new L0 geometry. Accept its cost only with contributor lineage, context qualification and a consumer that can express the change. Defer it otherwise. Also fix missing-planet validity at the producer boundary now; that is a separate dependency from kakṣyā and cannot be deferred while claiming null/zero distinction complete. AS:216; GS:1026; P:227–229.

### E3 — AMEND: conditional refinement, subject to an integrated June ruling

A bounded parent window still involves fast-planet search and does not automatically satisfy June's slow-only/no-scan direction. Conversely, the June document also contains the qualified fast-planet direction. M-3 must reconcile both E1's new geometry and E3's search, explicitly selecting the controlling rule and allowed scope. Existing fast scans establish reachability, not authorization. JUNE:62–105,123; E:992–1015; P:182–189,397.

The old `ceil(days/27.3)+1` bound is false for the stated conjunction-plus-opposition scope even under uniform motion; additional targets/aspects increase counts. S4's five in 60/seven in 90 is a counterexample, not a universal real-ephemeris count. Retain scope and resource budgets, never a correctness cap. The coverage receipt must identify how parents were selected; “complete inside selected parents” must not become “complete chart refinement.” Parent overlap must not duplicate the same child evidence. P:231–240,294; S4:5–10; S:226,451.

Tāra bala and Sarvatobhadra are different conditioning methods, not interchangeable generic confirmations. Reuse qualified served vedha/laṭṭā evidence where relevant; do not create a second producer or count correlated chart-derived views as independent proof. A real annual Tājika question should receive its annual-chart analysis before adding generic fast precision. But annual C12 reform needs its own scheduled source contract and acceptance gate; the present year/Munthā lord table cannot supply all annual significators and motion relations. W:1098–1120; KV/now:556–607; A.6.

### E4 — AMEND: the replacement is sound, but it must govern the actual score

I **AGREE with rejecting the former applicability gates**. The replacement should retain operative but adverse/weak lords, separate natal from transit varga evidence, and preserve cancellation and domain specificity. Sandhi boundary distance has no textual basis here for automatic suppression or amplification. BPHS 47.2–4 and 7.1–8; P:242–254.

Return boundary information per clock, level, parent and relevant lord, with signed time-to/from and source precision. A minimum over “any level” destroys which clock/level caused the proximity and can let a fine level dominate a broad period description. As an annotation this is not a reason to halt the concept, but it must not acquire an implicit universal salience meaning. P:244–246; DS:38–54; GD:1042–1062.

Replace the E4 SPEC as in RR-03 and reconcile the unchanged dignity-product kernel under RR-05. The capability aggregate is a derived view of some of the same natal evidence; its varga average cannot be a fresh vote, an all-clock strength floor, or a substitute for the actual domain/lord/source chain. CAP:174–204; E:1221–1223; S:447.

### E5 — AMEND: episodes must preserve occupancy, identity and aggregation semantics

No default retrograde peak. A station loop can organize repeated contacts into an episode, but phase strength is not an event-date oracle. Preserve every child, exact temporal precision, source geometry, applied method/orb and truncation. A singleton is a valid contact even when no episode is formed; a >3-contact or horizon-truncated episode must not be forced into a three-pass template. P:256–264; BPHS 27.21–25; S8:19–36.

Separately define the event's geometric identity and its claim attachment. A shared geometric episode may be relevant to several signals/domains without those testimonies disappearing into one row. Establish explicit split/merge/supersession relations before any key change. The hull is a search envelope; occupied time is a union of actual child intervals. R-5 and the dependent preservation harness precede this change, not just its production rebuild. P:201,256–264; S:450; B:337–379.

Taranga needs more than “months equal union.” Its current mean includes one contribution for each intersecting row, so duplicate or overlapping contacts can change weights even if the set of active months is unchanged. Specify whether weighting is by occupied duration, episode, route or another admitted unit, keeping activity and polarity distinct. Test duplicate insertion invariance, partial-month occupancy, continuous loop occupancy, disjoint gaps, overlapping near/lifetime representations and Jīvana-parva chapter boundaries. CW/ka_taranga:110–114,161–169; CW/ka_jivana_parva:165–180.

### E6 — AMEND: define an estimand, and separate model validity from outcomes

Qualified episodes divided by complete exposure can be a **modelled episode frequency**. It is not a life-event base rate and does not establish a prediction probability. The denominator must specify target/predicate/route/domain population, context, method version, horizon, eligible exposure, censoring, duplicate policy and unit (for example episodes per target-year). “Full applicable universe” without those strata can change the rate merely by adding duplicated predicates. Call a contact count a contact count and an episode count an episode count. P:266–274; S:450; RR-04.

The angle-based rarity formula must retire, but replacing it with a constant orbital period is not qualification. Geocentric reversals and horizon censoring affect recurrence. A zero numerator over complete positive exposure is a measured zero; zero/missing exposure is unavailable; a partial horizon cannot support a lifetime claim. P:297; E:971–989; S5:5–9.

**RR-07 — High: the outcome loop still conflates two axes.** Preserve an issued claim's original content/version/exposure and separately record (a) observation/adjudication status and result and (b) derivation/model validity or supersession. A claim can have a recorded hit or miss and later be found to have used an invalid model. The latter must neither erase the observation nor convert it to a miss. P:270–273's single enum does not represent that. Bind split/merge successors without rewriting historical forecasts or multiplying one success. S:450; CW/ka_bhavishya_lekha:16–32,365–383.

M-6 is authority for a separately qualified consumption/evaluation boundary; it is not permission to label the method empirically evaluated because outcome infrastructure exists. Held-out/predeclared evaluation, issuance chronology, eligibility and censoring remain prerequisites. P:273–274,400; K:84–99.

## C. What the author missed

### C.1 Existing behavior still bypasses the proposed audit

**RR-06 — High: §1b omits post-engine TRIGGER inputs/composition and leaves the accepted generic-aspect defect untouched.** W:49–114 applies two suppressive TRIGGER components to A/B results, at admitted weights 0.2/0.2, then persists the modified score and selected provenance. Missing service is a no-op; exceptions log and continue. Calls occur after engine searches at W:682 and W:708. Thus a source contract ending at the engine's necessary/supporting lists is incomplete. Record component source facts/context/availability, the precise admitted version, and how suppression relates to favorable or adverse propositions. Do not infer that a no-op proves “no obstruction.” This review does not reopen or replace the separate admission authority based on a code comment. W:41–114; TG:390–440; S:443,447.

There is **no demonstrated current double application of the removed vedha filter**: TG:314–329 explicitly describes its removal. The requirement is to prove and expose lineage among remaining C11, TRIGGER and Vighnakara conditions, not manufacture a duplicate-vedha bug. Meanwhile E:442–482 still scores benefic generic conjunction/trine/sextile/opposition/square weights, and E:210–224 has another generic angular current. Name both in R-4, assign a method/role or withdraw them, and test relevance/polarity. P:60,200; R:179.

### C.2 Candidate techniques, ruled individually

“Higher predictive leverage” is **UNVERIFIABLE empirically** without qualified outcomes. The ordering below is my method/engineering judgment: restore a complete relevant judgment before multiplying fine timestamps. Existing producer availability alone does not demonstrate classical correctness or incremental predictive value.

| Candidate | Ruling and missing condition |
|---|---|
| Chara/Jaimini daśā | **IN for a qualified route after R-2.** Pair its declared school, karakas, sign aspects and argalā; do not add a naked clock-agreement point to a Parāśari score. DS:1–12 already lists `chara_karaka`; BPHS ch.46.155–157, BP2:7078–7097, gives sign-period/co-lord rules whose exact chosen variant must be declared. |
| Yoginī | **IN as a qualified existing clock**, preserving Moon-derived lineage and source precision. It is not independent simply because its name differs from Vimśottarī. DS:1–12; BPHS ch.46.195–199, BP2:8572–8619. |
| Kālacakra | **IN conditionally**, after school/birth-input and savya/apasavya/deha/jīva qualification; avoid asserting equal applicability to every chart. DS:1–12; BPHS ch.46.52 onward, BP2:5442–5462, with its further rules, and results in ch.49. Exact implementation fidelity remains **UNVERIFIABLE** without that focused qualification. |
| Tājika varṣa-praveśa | **IN before generic E3 precision for annual questions.** C12's 1/0.5/0 lord match is not a complete annual judgment. Require annual chart context, relevant significators, Munthā/year-lord rules, strength, actual aspect/orb/configuration and annual-boundary splitting. W:1098–1120; E:648–691; Hāyanaratna 2.1/3.3, A.6. |
| Sudarśana cakra | **IN as audited reuse**, not three independent natal origins. BPHS 74.4–6, BP2:43236–43260, gives ascendant/Moon/Sun perspectives; 74.19–23, BP2:43867–43915, includes same-sign qualification and temporal rotation. Verify those conditions before assuming the served producer realizes the full method. KV/now:475. |
| Praśna | **OUT of an unattended lifetime sweep.** It needs a separately authorized inquiry and its own question/time/place/context contract; a natal batch must not invent a question chart. This is a scope judgment, not a claim that a particular cited Praśna passage was verified. P:332; K:133–139. |
| Argalā/virodhārgalā | **IN through its authoritative producer for relevant routes**, with obstruction/counter-obstruction and period relevance, not a universally positive current. BPHS 31.2–9, BP1:24310–24334. The fact that an obstruction exists cannot be collapsed into inapplicability. |
| Bhāva-madhya versus whole sign | **MANDATORY decision at binding.** A sign target, natal longitude, house cusp and house-lord relation are different objects. Record house system/location/birth precision as applicable; do not globally substitute one for the other. BPHS ch.26 commentary discusses bhāva-madhya, BP1:16632–16633; P:197,395. |
| Rāhu/Ketu transits | **IN only under named rules and node convention.** Their absence from `_AV_SCAN_PLANETS` is not itself a defect: a seven-planet BAV mechanism must not invent node BAV. Give authorized node transit/eclipsing/other methods separate scope and lineage. E:1683; T:242–272; Phaladīpikā 26.2, A.6. Node fifth/ninth aspects remain **UNVERIFIABLE** as a universal choice. |

No additional technique should precede correct target/clock/context, signed adverse testimony, identity and a real caller test. Those corrections improve the meaning of every existing output; more named currents do not compensate for timing the wrong point. E:1148,1221–1223; W:879–886; S:285,442,447,451.

## D. Sequencing, P4 and lineage

### D.1 Amend §4's order and its companion contract

The revised direction is sound, but documents alone do not implement R-5, and an unscheduled “annual first” promise is not a dependency. Replace the ambiguous gates with:

1. Correct the evidence/fixture defects and prepare concrete method/source decision packets. Reconcile June scope, target kinds and school-specific meaning. These decisions can precede code repairs; production acceptance cannot. P:182–201,292–300,395–397.
2. Amend the companion's full contract, then implement and qualify **R-5 identity/history/generation behavior in a disposable harness before any contact-changing implementation is admitted**. Preserve existing history while new identities are introduced; do not run a destructive rebuild to discover attachment policy. P:201,309; B:337–379; RR-08.
3. R-1…R-4: establish truthful inputs, interval intersections, context, actual detectors, current polarity/availability and complete baseline manifests. A measured baseline may expose more required source amendments. P:197–200; A.4; RR-06.
4. E1/E2 method-specific and signed contracts; qualify complete route/predicate coverage before reusing geometry. E5 follows the defined events, with child aggregation and every consumer mapping. P:311–312; S:226,285.
5. E4 typed natal/clock conditions and an explicitly scheduled annual-Tājika contract where selected; source lineage and consumer meaning precede E3. P:238–254,313–315.
6. E3 after the integrated ruling and fixed-context full-scope cost experiment; then E6 frequency on the qualified versioned exposure. Historical claim preservation begins in step 2, not at the last evaluation step. P:315–316; S:450.

The companion amendment list must extend beyond P §7's four bullets. Correct B:98,114,229's streaming/memory claims; replace B:191–192/B:325's unchanged kernel-method/rarity promises; amend the actual key section **§5.3**, not P:381's mistaken “§4.2 keys”; replace peak-based regression equivalence with a mapped semantic comparison that permits explicitly invalid old rows to be withdrawn; and publish generation/served compatibility for all consumers. Merely preserving every old `(class, signal, peak)` row conflicts with changing incorrect geometry. B:218–230,375–379; P:381–388.

### D.2 P4: complete evaluated scope before optimization claims

No runtime saving is established. Withdrawing the former streaming claim is correct. Existing per-class selection caps (W:274–305,388–389), downstream top-500/750/100 reads and served pagination do not define the applicable universe. The native's small canonical set is a useful seed, not a coverage oracle. S:196–209,226,238–253; P:359–367.

| E | Required applicable/selected/served accounting and P4 test |
|---|---|
| E1 | Manifest every applicable predicate × qualified method × target/context; separate display selection. Geometry reuse must preserve every route, mode, signed result and source root, including sign-valid/no-exact-pass cases. |
| E2 | Qualify every authorized ingress and usable planet/sign fact, including adverse/zero/equality/unavailable cases. Removing a prefilter broadens scope; later top-K must disclose what it excludes. Missing L1 validity is incomplete coverage, not zero evidence. |
| E3 | Report both parent selection coverage and complete child enumeration inside selected parents. A resource limit yields resumable incomplete state; no fast cap can masquerade as equivalent complete refinement. |
| E4 | Cover every relevant domain × clock/lord × available natal condition. Missing varga/capability is an explicit state. Equivalent geometry does not permit dropping adverse or conflicting domain testimony. |
| E5 | Every qualified old contact has an explicit retained child/supersession disposition. Fewer parent rows is not reduced event coverage if all children, occupied intervals and consumer meanings survive; prove those facts. |
| E6 | Compute frequency from its declared complete exposure manifest, not ranked/served rows. Demonstrate invariance to page size, top-K and duplicate representations. |

These are acceptance requirements, not measurements performed here. Benchmark cold/warm/resume on pinned chart/source generations, horizon, context, rule versions and accepted semantic output; report wall/CPU, peak RSS, ephemeris calls, DB/WAL and coverage receipts. Compare quality-equivalent results only after accounting for intentionally corrected outputs. Shared geometry cannot erase mode identity or witness roots. S:226,238–253,285; K:143–162.

### D.3 Roots that must be declared

| Elevation | Required lineage and non-independence rule |
|---|---|
| E1 | Target facts/derivation, transit geometry, time/context, route/method version and binding predicate. Same contact evaluated through two methods remains shared geometry; method disagreement is preserved. |
| E2 | Raw sign BAV contributor roots and source generation; SAV is an aggregate of BAV; future kakṣyā is a contributor view. Never count all three as separate origins. |
| E3 | Parent-selection derivation plus independently computed child geometry and source precision. Child placement is conditional on parent selection; it does not increment the parent's independent-evidence count. |
| E4 | Actual clock intervals/parents, natal lordship/dignity/varga facts and cancellation rule. Capability aggregates must expose their reused varga/strength roots, not hide them behind a service name. |
| E5 | Every contact and station-loop geometry with episode membership and occupancy union. Grouping neither creates corroboration nor repairs within-row ICC automatically. |
| E6 | Full exposure/episode manifest for frequency, separate immutable issued claim and observation/adjudication provenance for outcomes. Frequency never returns as evidence for its own generating contacts. |

Also declare C11/TRIGGER/Vighnakara roots and their proposition-specific roles before composing them. These are bookkeeping/correlation statements, not empirical statistical-independence claims. P:317–321; S:442–443,450; RR-06.

## E. Ecosystem

### E.1 Seven consumers × six elevations

Each cell describes current compatibility and the required change; none claims a deployed improvement. The row evidence identifies the real read/aggregation seam. `Unconsumed` means the proposed new structure has no demonstrated current read path, not that it is irrelevant.

| Consumer and source seam | E1 | E2 | E3 | E4 | E5 | E6 |
|---|---|---|---|---|---|---|
| **ka_kalasutra** — CW/ka_kalasutra:70–89,104–116; picks best convergence per signal and uses peak | New method/context rows cannot compete blindly for one best scalar; preserve route/context choice. | Signed AV cannot be inferred from old score ranking. | Child timing is unconsumed; choose whether timeline exposes children or declares no refinement. | Domain conditions need per-domain attribution rather than one global best date. | One peak loses repeated contacts; timeline must represent child intervals/episode membership. | No direct frequency read shown; test selection invariance when old score/ranking changes. |
| **ka_vighnakara** — CW/ka_vighnakara:177–183,214–226; top 500 non-null peaks, detects obstruction at peak | New target/method/geometry changes obstruction applicability; retain source linkage. | Adverse BAV is not automatically an obstruction of an adverse proposition. | Existing peak-only detection does not evaluate each fast child. | Distinguish unavailable from no obstruction and qualify proposition polarity. | Peak-only evaluation misses variable obstruction among children and occupied intervals. | No direct frequency input; top-500 coverage must never supply E6's population. |
| **ka_kala_darshana** — CW/ka_kala_darshana:24–31,38–74,89–97; top 750, scalar labels, obstruction join | Version/context and new row IDs must survive joins and ranking. | Structured signed verdict needs an explicit interpretation path; scalar net label cannot stand in. | Children unconsumed; disclose or add an authorized temporal interpretation. | Null-score 0.5 and unsigned effective score conflict with unavailable/adverse semantics. | Join and ranking must distinguish episode parent from child; a hull is not continuously active. | Reads `confidence_label` and `rarity_years`: removal can break SQL; compatibility shim cannot silently equate frequency to rarity. |
| **ka_taranga** — CW/ka_taranga:110–114,161–169; monthly means of intersecting row scores | New/legacy duplicate method views can overweight a month; define aggregation unit. | Keep activity and polarity separately; no silent positive conversion of obstruct. | Avoid counting parent plus sub-peaks as additional independent activity; expose refinement coverage. | Conditions need route/domain treatment, not a generic weight pasted into all months. | Aggregate actual child occupancy with duplicate/weight rules; month-set union alone is insufficient. | No direct frequency read; aggregation output is not an unbiased recurrence sample. |
| **ka_jivana_parva** — CW/ka_jivana_parva:116–126,165–180; peak-to-MD membership and class counts/means | New method/route copies change counts unless counting units are explicit; current class lookup's LIMIT 1 needs deterministic meaning. | Adverse and favorable counts must not collapse into high/low score activity. | Child periods/precision unconsumed by a parent-peak chapter assignment. | Clock hierarchy/domain conditioning must be retained; a low score is not no manifestation. | An episode spanning chapters needs child/interval allocation; do not move all activity to one chosen peak. | No direct frequency input; class counts cannot become outcome or recurrence denominators. |
| **ka_bhavishya_lekha** — CW/ka_bhavishya_lekha:163–195,230–241,320–377,562–586; top 100, signal/peak identities, confidence/rarity narrative | Geometry/peak changes break natural-key attachment and may rewrite a claim unless R-5 is in place. | Signed conditions must alter claim polarity/eligibility explicitly; existing obstruction exclusion can hide adverse claims. | A child must not retroactively narrow an issued forecast; new precision requires separate issuance/version/exposure. | Preserve natal-condition meaning in claim content; no unsupported probability/strength language. | Split/merge and every historical attachment require mapping; fail-closed checks are not a migration algorithm. | Reads/narrates confidence and rarity; redesign issuance/outcome/model-validity axes and remove cycle-as-prediction prose. |
| **ka_tulana (Python window ranker)** — TR:38–49,123–138,191–195,220–229 | New method scores/proximity are incomparable without a declared ranking contract. | Signed AV cannot fit a favorable scalar ranking by default. | WindowInput has no demonstrated sub-peak/coverage semantics. | Applicability, valence and missingness need explicit ranking behavior. | Parent/child ranking must avoid duplicate prominence and arbitrary peak proximity. | 40/25/20/15 composite consumes convergence/rarity/confidence/proximity; its rarity/30 and missing defaults cannot consume a frequency rename. Redesign, do not relabel. |

**RR-08 — Blocking before any rebuild qualification: §6's preservation test cannot prove historical integrity.** Equal table counts permit different rows; a hash of unbound outcome content permits swapping observations between claims. `string_agg` needs an explicit input/delimiter/order, null handling and canonical framing; concatenated unframed content can collide even before hashing. More fundamentally, the current writer's actual fields are `outcome_recorded` and `outcome_notes`, not a demonstrated `outcome_content` column. The proposed expression is not an executable current schema contract. P:350–357; CW/ka_bhavishya_lekha:98–142.

The cascade includes CASCADE, SET NULL and an FK-free top-anchor reference, so no single orphan count proves preservation. B:337–371 maps convergence→obstruction/Darśana, Bhaviṣya, anchors and their children; it also documents nullable and unenforced references. Require a pre/post manifest keyed by each original stable claim/outcome/entity ID: canonical full issued content, original source/version/exposure, observation bytes, all original dependent bindings and authorized successor mappings. Compare original identities and content exactly; validate every FK-free and nullable attachment semantically. Test empty rebuild, moved date, one-to-many split, many-to-one merge, ambiguous match, interrupted/resumed rebuild and an unchanged-count/content-swap attack. Candidate additions have an explicit expected delta; original history is immutable. P:201,350–357; B:337–379; S:450; K:84–99.

This does not authorize an L4 rebuild. A candidate Saṅgam generation can be prepared while original claims remain intact; switching dependent generations or rebinding claims needs its own concrete admitted contract. The review performed no DB preservation experiment and claims no production safety receipt.

### E.2 Served capabilities and an explicit correction to my v0.1 review

**I retract R:273's claim that E6 directly changes the ranker underlying `kala_views/priority.ts`.** The actual route is KV/priority:225,373 → `marsys://tool/L3/call_priority_ranking` → WRAP:516 onward. WRAP:673–711 directly joins MSR to `kala_activation`, ranks salience × available orb factor × neutral-dignity adjustment, and does **not** read `kala_convergence` or call TR's window ranker. Its description mentions convergence but its SQL is authoritative. KV/priority:99–110 separately averages `kala_field_salience`; a future upstream effect requires tracing that producer, not assuming it. This correction belongs here rather than an edit to the immutable v0.1 review.

| Served surface | What a user can actually see, and required disposition |
|---|---|
| **Q:90–129** `query_convergence_windows` | Current query selects old scalar fields and `constituent_factors`, overlaps by dates, defaults to 30/max 200 rows and lacks explicit method/ayanāṃśa selection. E1/E2/E4 alter content/selection; E5 requires child-occupancy overlap rather than hull-only relevance; E6 column removal is a direct compatibility change. A total matching row count does not establish upstream applicable coverage. Publish material method states, children, context, lineage and coverage through the accepted schema and test a decisive low-ranked sentinel. |
| **KV/now:1645–1654;475;556–607** | Calls activation/temporal-view capabilities, with separate Sudarśana and vedha paths. New Saṅgam child fields do not automatically join those paths. E1/E2/E4 need explicit interpretation linkage; E3/E5 need occupancy/refinement semantics; E6 must not reappear as an unexplained confidence claim. |
| **KV/ahead:1837–1859** | Activation and projection paths make Bhaviṣya compatibility decisive. Expose E3 refinements without rewriting issued claims; E5 must retain child dates and envelope distinction; E6 changes prediction language and lineage, not merely a field name. |
| **KV/story:226–246,539–609** | Counts/means and chapter narratives depend on consumer aggregation. E1/E2/E4 alter interpreted activity/polarity; E5 changes counting units; E3 is unconsumed until chapter integration is explicit. E6 cannot infer calibration from activity summaries. |
| **KV/priority:225,373–392; WRAP:673–711** | No demonstrated direct E1–E6 Saṅgam window input in its principal ranking query. The Python Tulana redesign alone will not change this facade. Declare either unchanged behavior/non-consumption or an explicitly authorized new route; test it independently from TR. |
| **KV/explain:433–447,464–592** | Existing school/KP/gochara voices do not automatically consume `method_states`. Link the new E1/E2/E4 signed reasoning and E3/E5/E6 coverage/identity material, or disclose non-consumption. Do not claim explanation parity from JSONB persistence. |

**RR-10 — High: the serving proof is still a future obligation.** P:369–375 says “each consumer gets” a decision but contains neither the matrix above nor a route-specific material-field sentinel. Require an actual authorized producer→persistence→consumer→capability traversal for each changed meaning, with exact context and generation. A low-ranked adverse condition must survive where material; a capped display must report incompleteness/selection truthfully. The present review supplies the missing analysis, not those execution receipts. S:451; K:133–139,143–162.

## F. Verdict

**REWORK.** v0.3 makes substantial corrections: it withdraws false sandhi/capability gates, removes the Moon count cap, recognizes distinct aspect methods, restores adverse BAV meaning, and models child contacts instead of treating a hull as continuous activity. These improvements do not close the re-review. The evidence suite can claim success when its own observations contradict it; the non-Aries producer fixture is false; several SPECs are invalid; and the signed-score, identity/history and consumer contracts remain internally incomplete. A.1, RR-01–RR-10.

**Fit for native rulings M-1…M-6 now: not as one ready decision package.** M-1/M-1a, M-2 and M-3 are legitimate decisions before implementation, but first correct the zero-target/square/AV fixture facts and provide bounded alternatives with real input dependencies. Presenting those corrected choices need not wait for all repairs to land. M-4 should follow the repaired domain/lord/context contract; M-5 needs the actual contact/episode/occupancy/identity alternatives; M-6 needs a separate issuance/outcome/model-validity and consumption gate. A ruling selects method/authority; it does not validate arithmetic, producer availability, safety or empirical accuracy. P:395–400; S:442,447,450–451.

The three changes with the greatest value, in the native's priority order, are:

1. **Quality:** make every claim refer to a real target, qualified clock/context and a named method, then reconcile signed adverse testimony with the actual score and repair the falsifiers. Correct S3 and the zero/square/fast-count/domain fixtures before seeking ratification. This prevents precise-looking output about the wrong point or suppression of the adverse event being examined. RR-01–RR-07; E:1148,1221–1223; S:447.
2. **Build efficiency:** establish complete applicable manifests and failure-sensitive evidence first, then benchmark reuse on pinned equivalent semantics. Share geometry while retaining every predicate/mode/route; measure cold/warm/resume and actual ephemeris provenance. Do not preserve caps or full-list “streaming” assertions as optimization baselines. A.5; D.2; S:226,238–253,285.
3. **Ecosystem:** implement and qualify R-5 before changed contacts are admitted, rewrite the companion's conflicting invariants, and decide every consumer/served path explicitly. Preserve original claim/outcome content and attachment through splits/merges; prove material signed fields survive to a real caller. The separate PRIORITY SQL route must be tested separately from the Python ranker. RR-08, RR-10; E.1–E.2; S:450–451.

Closure evidence for this review: plan SHA-256 is recorded in frontmatter; unchanged v0.1 review SHA-256 was `36c2d7aa56e5dbe1b3d53e482a812eb13f1b4c49b56129a3a3369a25521f26fd`; unchanged saved evidence output SHA-256 was `8ea7666031f58302e57f1b6454b63c14993de544ea20da0e6403d36f61586534`. No implementation, production incidence, build-performance, deployment, predictive-accuracy or acceptance conclusion is implied.
