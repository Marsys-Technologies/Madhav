---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.9"
author: "Stream B (Śāstra) — Exec B (Claude Sonnet)"
date: "2026-10-02"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.8. ROUND-8 DELTA. FILL BEFORE DISPATCH: <<WRITER_HEAD>> (Stream A, branch pravaha/a53-am5-inventory) and <<BRIEF_VERSION>>; everything else is final."
---

# A5.5 gate — round-8 request (2026-10-02)

Round 7 returned REJECT (R9 CLOSED; 1232 ACCEPT_WITH_AMENDMENTS at source; AM-18 doctrine defensible; ND-ORB packet v1.1 acceptable); the steward adopted every closing text. This packet answers it in two parts: **Stream B's items** (§A, unchanged in substance from v1.8 plus the new rulings) and **Stream A's writer head** (§B, to be filled). Specs/oracles v1.4 are frozen and untouched; spec text lives in the amendments draft **v0.17** (`campaign/pravaha`).

## §A. Stream B — code and text (heads as of this packet)

| Exhibit | Ref | State |
|---|---|---|
| **#2913** — `aggregate_paths`: unknown competing path ⇒ unqualified unless proved independent (known max = 1.0); lower bound labelled | `8d4463d47` | **MERGED** |
| **#2897** — activity_kernel/graduated_drishti 1.1.0 registry (P3/P4/P5 @1.1.0), **ONE flat codec** (closed key schema; numeric orb only with `ratified` + `orb_decision_ref`), **exact nakṣatra/sign membership** in integer arcseconds | `55fec69a1` | OPEN, mergeable |
| **#2901** — vedha: residence **coverage**, validated complete 36+6 pairs load with content digest, structured results, independent pointwise oracle; also contains #2897, #2907 and main | `ed03d3c6c` — **kept stable, fast-forward only** | OPEN, CLEAN |
| **#2907** — drishti `factor_ref` binding (explicit calls return the requested ref) | `b598ee302` | OPEN (also inside #2901) |
| **#2909** — migration 1232 (AM-14 Moon-scope accounting; additive over 1206; source ACCEPT_WITH_AMENDMENTS) | `358c33211` | DRAFT / HOLD |
| **#2914** — P1 strict input wrappers over L1's pure rules (no silent defaults; dignity-boundary authority checked) | `f5f921c03` | OPEN |
| #2867 (1206), #2817 (1204), #2884 (1220), #2905, #2894 | unchanged | HOLD / merged as before |
| #2903 (AM-10 repin tool) | — | DRAFT; not for judgment |

**Text (all on `campaign/pravaha`):** amendments draft **v0.17**; `measurement/EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING_v1_2.md` (unknown-competitor rule, worked 2/1/0/NULL/NULL case, freeze record with actual hashes); `decisions/NATIVE_OPEN_DECISIONS_v1_0.md` v1.3 (ND-ORB-ADMISSION / ND-ORB-SCALE split; ND-P1-FRAME added); `decisions/ND_ORB_DECISION_PACKET_v1_1.md`; `design/am16_vectors_model.py` v3 + `design/am16_vectors_frozen_v1.json` (literal preimages, 12 cases) + `design/am16_series_equivalence_probe.py`; `design/P1_INPUTS_ANSWER_v1_0.md` v1.2 §(5); `design/P1_FRAME_ANSWER_v1_0.md`.

### New since v1.8 (not seen by round 7/8)
| # | Item | Content | Judge |
|---|---|---|---|
| **AM-20** | **RULED** — reference sign of the `dasha_lord` frame for P1 transit records | S §0 never defines it; S §2.2 P1 says only "natal sign positions"; no oracle exercises it; `frames.py` already reads it as the period lord's natal sign. Phaladīpikā XX.37–38 (`phaladeepika:PG250:C1`, read verbatim) judges the transit by the **quality of the sign**, so no P1 factor reads the house number: `house_from_frame` is a stored descriptor required by 1155's CHECK. Ruled text: inclusive count from the natal sign of the period lord anchoring the record (`dasha_lord:<graha>`; the bhukti lord for the Sun/Jupiter-in-the-lord's-exaltation-sign relation); AM-15's lagna count for the natal relation unchanged. Brihat Jātaka VIII.10 (`brihat_jataka:PG215:C1`) is the classical precedent for counting *from the daśā lord* (natal relations). ND-P1-FRAME records the native's confirmation; the frame label is a convention only. Open: XX.37's "or be retrograde, the effects will be good" has no factor in the P1 inventory | whether option (c) is acceptable as a stored descriptor; the retrograde gap |
| **Tie ruling** (AM-17) | steward, round 8 | **1e-9 applies between distinct maxima or plateaus**; **a smooth piece's own argmax is taken otherwise** (no tolerance blurs one smooth maximum); the separate storage-comparison tolerance is never used to choose a peak | consistent with the frozen measurement contract's `1e-9`? |
| **Verifier status model** | steward + Stream A | `VERIFIED` / `UNVERIFIED_DYNAMIC` (the window verifier cannot reproduce a function-valued window numerically); **an UNVERIFIED_DYNAMIC result cannot satisfy the gate** (PC-5) and is never reported as semantic success | is the status honest where a numeric reproduction is skipped? |
| **Mandatory scope constructor** | Stream A | `scope_response.coverage_response` is the mandatory positive **and no-window** response constructor reading `stored_scope` from the bound manifest | **PRE-CONDITION, NOT YET MET:** the **serving call site is not yet wired** — the constructor exists; no served response uses it. Listed under PC-5. |

## §B. Stream A — writer head (to be filled at dispatch)
* Writer: `pravaha/a53-am5-inventory` @ **<<WRITER_HEAD>>**, brief **<<BRIEF_VERSION>>**. Stream A's round-7 items [1], [7], [3], [2], [5], [8], [9] were at `f886b0ac6` (brief v1.18) when this packet was prepared; **[4] (the ONE codec and version references through the writer, against #2901 `ed03d3c6c`) was in progress**.
* The inventory verifier still refuses included P2 until an independent derivation exists — `vedha_oracle.py` (#2901) is that oracle's candidate.

## §C. Standing limits (unchanged)
Database cannot judge the *right* inventory; sealer and verifier principals not provisioned; DB-Integration CI advisory (`postgres:16`); mutation harness counts "any test fails"; seal cost measured only on synthetic volume; **ND-ORB-ADMISSION and ND-ORB-SCALE open** (point targets `unqualified`); ND-P1-FRAME, ND-COMBUSTION, ND-VIPAREETA, ND-NODE-VEDHA open; `'5.0'`/`'4.1'` scorer not run; SI mapping pre-registered after seeing '3.0' (disclosed, not blind); the AM-16 model is a model — the writer's `assemble_vector` must reproduce the frozen literals. **PC-5 pre-conditions still open:** serving call site for `coverage_response`; actual-role sealer/verifier receipts; protected 1204 → 1206 → 1232 window rehearsal (ledger precondition stated in PC-3). Open list: BPHS human re-read; L1 Sun-rūpa; Mercury/Moon mūlatrikoṇa one-degree and three combustion copies; L1 silent defaults (relayed to Suvarṇa); AM-12 and AM-19 candidates; `varga_position` unclassified; **P5 remains held.**

## §D. Judge-list
1. §A new items (AM-20, tie ruling, verifier status model, scope constructor pre-condition).
2. #2913 (merged), #2897, #2901, #2914 and the v1.8 §A fixes, if the delta contradicts them.
3. §B against the writer head named at dispatch.

Verdict shape requested: ACCEPT / ACCEPT_WITH_AMENDMENTS / REJECT per item, with numbered findings.
