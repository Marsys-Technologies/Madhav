---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.7"
author: "Stream B (Śāstra) — Exec B (Claude Sonnet)"
date: "2026-10-02"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.6. THIS VERSION = fixes for Codex round-6 R1–R9 (§A) + the items v1.6 introduced that round 6 has not seen (§B). §C standing limits; §D judge-list."
---

# A5.5 gate — round-7 request (2026-10-02)

Round 6 returned REJECT with nine ranked items. Each is answered below with the exhibit and what to judge. R1 is a separate, small PR (as ordered). Frozen specs/oracles v1.4 are untouched; spec text lives in the amendments draft **v0.13** (`campaign/pravaha`, `design/GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md`).

## §A. Round-6 items → fixes

| R | Codex finding (short) | Fix | Exhibit | Judge |
|---|---|---|---|---|
| **R1** | Qualification not propagated; a NULL operand could still yield a number | `score.py`: `factor_product` skips only a **declared** `not_applicable`; any unqualified scored record makes the affected channel NULL with `unqualified_reasons`, `unqualified_record_ids`, **known partial subtotals kept as lower bounds only**; testimony skipped; an unevaluated record qualifies neither channel. `valence.py`: NULL evidence takes the unresolved branch `evidence_channel_unqualified`; severity untouched (Stream C C8). | **PR #2905**, head `c083cbd6d` — all checks green, mergeable CLEAN; 9 tests, 8/8 mutations caught | Is NULL-until-qualified honest at every reduction? Is the lower-bound disclosure never readable as a value? |
| **R2** | AM-14: literal Moon exclusion does not settle `period_lord:*` intervals resolving to Moon | AM-14 rewritten (v0.13). Resolved agent incl. `period_lord:*`; **per-obligation snapshot-bound domain**; Moon-resolved portions are accounted as **excluded — neither missing nor searched** (new interval state `excluded_moon_tier`); machine-readable stored scope `stored_non_moon` bound to the manifest vector and required by the coverage constructor. **Additive migration 1232** (HOLD), `missing_inputs_present` / `obligation_uncovered` not weakened — the completeness function is 1206's plus **exactly two edits** (static test proves it). | **PR #2909**, head `358c33211`, DRAFT, stacked on #2867; live suite 10/10 with a real Moon-resolved daśā interval (Mercury [2024-06-01, 2025-02-01) + Moon [2025-02-01, 2026-01-01)); static 4/4; mutation check 5/6 caught (6th blocked by the migration's own presence check) | Does the domain derivation match the daśā levels (md/ad/pd) and the horizon clip? Is a hidden Moon gap still impossible (`moon_domain_missing`/`_extra`)? The sealer needs EXECUTE on the two new functions (stated, not granted) |
| **R3** | AM-17: component cardinality, prerequisite-restricted support, peak objective undefined | Rewritten per Codex's closing text; window = connected component of prerequisite-satisfying admitted support within one (path-version × class); peak objective stated; component→row mapping and cardinality defined | Draft v0.13 §AM-17 | Is a window ever ≠ one component? Is the peak objective total (tie rule `1e-9`, earliest)? |
| **R4** | Kernel geometry not validated | `kernel_factor.activity_kernel(object_kind, canonical_target, *, factor_ref, body_longitude_deg=None, aspect_angle_deg=None)`: refuses a target whose kind ≠ object kind (`TargetKindMismatch`); seam-safe angular distance; invalid / unratified-with-orb row config fails closed (`KernelFactorConfigError`); 1.0.0 row → `applicability_undeclared`, never 1 | **PR #2897**, head `d70d76cb0`; 27 tests, 11 mutations caught | Is every kind→geometry pairing validated? |
| **R5** | operand_selector lossy; drishti returns its own ref; supersession text; O-CF-DRISHTI attribution | Flat **lossless** `operand_selector` (1154-conformant keys/values; `flat_selector.py` mirrors 1154's regexes, encode/decode round-trip); **version-exact dispatch** — the caller's factor ref is returned by the evaluator; per-class supersession text (`SUPERSEDED_FACTORS`, `SUPERSEDED_PATHS`); drishti attribution to O-CF-DRISHTI corrected | #2897 (above); **PR #2907** head `b598ee302` (drishti `factor_ref`, `normalize_agent`; stand-in 1.1.0 row exercises version binding; mutations caught) | Does the flat form survive 1154 as written? Is unbound-version use impossible? **Note: A's version-aware `BOUND_PATHS`/`factor_rows` is still required.** |
| **R6** | AM-16 fingerprint incomplete | Versioned key schema + canonical serialization; registry digest over selected path/predicate/factor payloads, **ordered** prerequisites, soft-factor memberships, applicability declarations and the sealed-version census (excluding only `created_at`); node-series and arc-series content digests; admission and scale orb policies; rulings; implementation identities (geometry/evaluation/window). Writer **and** independent derivation recompute and refuse on mismatch; historical replay checks its original bound inputs. | Draft v0.13 §AM-16; **`design/am16_vectors_model.py`** — reference model + frozen identity table (membership-only, node-series-only, window-algorithm-only, prerequisite-order-only, census-only, orb-policy-only each change the identity; the audit field alone does not) | Is the preimage free of any result-bearing field it omits? Are the frozen vectors sufficient? (They are a model, not production; Stream A's implementation must reproduce them.) |
| **R7** | SI addendum NULL policy missing | v1.1: admission, computation coverage and score qualification distinguished; NULL handled **before** merge / representative selection / candidate counting / ranking / timing / plateau detection; conservative policy adopted (unknown → no invented si or peak; affected result **unqualified and ineligible to establish a passing endpoint**; events retained and reported; known zero stays numeric; unknown necessary-predicate admission not admitted); freeze list extended; "clipped" → "constrained by the schema CHECK" | `measurement/EVALUATION_PROTOCOL_v2_3_ADDENDUM_SI_MAPPING_v1_1.md` | Does the policy leave T-FP burden and event denominators intact? Is the freeze list complete? |
| **R8** | ND-ORB packet conflated admission and ranking orbs; options A/D/E misstated; corpus claim | v1.1: two decisions (admission/contact angle; ranking scale), explicit if one ruling binds both; options re-stated (A closed singleton range, not division by zero; B/E durations are constant-speed illustrations; D is a different strength model, "plainly monotone" withdrawn); versioning "new factor version and new consuming path versions once bound"; leads added incl. the Devanagari-only Tājaka corpus (`दीप्तांश` + OCR variants) and the derived-summary orb table, reported as "not found in the stated searches" | `decisions/ND_ORB_DECISION_PACKET_v1_1.md` (v1.0 marked superseded) | Are the options now each correct, and is non-exhaustion stated? |
| **R9** | PC ordering | Restructured: PC-1 (before sealer activation: seal + both replays under the restricted role, PUBLIC EXECUTE revoked, full helper closure, effective privileges, builder cannot seal); PC-2 (identity/registry/manifest prerequisites before the first candidate build; Moon receipt tied to on-demand use); PC-3 (protected 1204+1206 window: exact heads, supported PostgreSQL, faithful ownership/default privileges, complete grants, realistic 26-class volume, contention/seal timing, per-file recovery, advisory DB job evidence at the reviewed head); PC-4 (verifier read/helper privileges, effective-role separation); **new gate PC-5** before the first 5.0 candidate build | Draft v0.13 §PC | Is each precondition placed before the action it protects? |

## §B. NEW since v1.6 (not seen by round 6)

| # | Exhibit | Ref | What to judge |
|---|---|---|---|
| N1 | **AM-18 — vedha** (RULED), amends frozen text "zeroes ⇒ excludes" | Draft v0.13; `design/P2_VEDHA_ANSWER_v1_0.md` v1.1 | unchanged since v1.6 N1/N2 — now with round-6 lessons applied (below) |
| N2 | **PR #2901** vedha derivation, `vedha_attenuation@1.1.0`, `P2@1.1.0`, pairs accessor, O-VI-6 | head `37de1bb2c`, stacked on #2897 (merged in, not rebased) | round-6 lessons applied before round 7: flat lossless `operand_selector`; version-exact `vedha_factor_value(segment, *, factor_ref)`; declared `vedha_not_applicable`; qualification propagation (its integration test skips until #2905 merges); refuses uncited and node rows |
| N3 | Stream A window-sweep semantics (P3/P4) | per v1.6 N5, branch `pravaha/a53-am5-inventory` (A's current head per the steward) | unchanged since v1.6 N5 |
| N4 | `decisions/NATIVE_OPEN_DECISIONS_v1_0.md` v1.1 | `campaign/pravaha` | ND-ORB (now two decisions), ND-VIPAREETA, ND-NODE-VEDHA, BPHS human re-read |
| N5 | P1/P2/P5 answers: `P1_INPUTS_ANSWER_v1_0.md` v1.1 (+Q4), `P5_P1_SWEEP_ANSWER_v1_0.md` | `campaign/pravaha` | cited, no code |
| N6 | PR #2894 drishti evaluator **MERGED**; PR #2884 migration 1220 merged; #2817 (1204) head `b9d5d2718` and #2867 (1206 v1.2) head `fc10a91fe` unchanged, HOLD | — | — |
| N7 | AM-10 repin tool, PR #2903 | DRAFT — stays draft until Suvarṇa confirms the L1 rebuild | not for judgment yet |

Digest/census: #2897 and #2901 regenerate the writer-digest inventory and census (steward rule M20261002T010935-e09d); #2905 and #2907 are outside the writer import closure and need no regeneration (checked).

## §C. Standing limits (unchanged)
Database cannot judge the *right* inventory; sealer and verifier principals not provisioned; DB-Integration CI job advisory (`postgres:16`); mutation harness counts "any test fails"; seal cost measured only on synthetic volume; **ND-ORB open** (point targets stay `unqualified`, never a made-up number); `'5.0'`/`'4.1'` scorer not run; SI mapping pre-registered after seeing '3.0' knowledge (disclosed, not blind). Open list: BPHS human re-read; L1 Sun-rūpa finding; L0/L1 Mercury/Moon mūlatrikoṇa off-by-one and three combustion copies (referred to Suvarṇa); AM-12 candidate; YAMAKANTAKA L1 gap; `varga_position` unclassified; combustion Jupiter/Saturn lines; ND-VIPAREETA; ND-NODE-VEDHA.

## §D. Judge-list
1. R1–R9 per §A, in Codex's own ranking order.
2. #2909 as the only schema-touching delta; confirm "additive, no weakening".
3. The AM-16 frozen vectors as sufficient evidence.
4. #2901 under the round-6 lessons.
5. Anything in v1.5/v1.6 the fixes contradict.

Verdict shape requested: ACCEPT / ACCEPT_WITH_AMENDMENTS / REJECT per R-item and per N-item, with numbered findings.
