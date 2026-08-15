# LEDGER_B — Stream B (ŚĀSTRA) — SOLE WRITER: ŚĀSTRA-LEAD

campaign: EKAVĀKYATĀ
stream: B (ŚĀSTRA — classical engines, Python)
lead_worktree: ekv-lead-shastra
owns: platform/python-sidecar/**
model: sonnet-high (lead) · sonnet-medium (builders)

---

## STANDING POSITIONS (from PRATINIDHI ledger, absorbed at session open)

- B.10 absolute: no fabricated numerical values; oracle READS bg_dignity_reference data.
- Contested doctrine → PRATINIDHI (who picks the more disclosing option).
- One file per writer. Lease violations fail the lane.
- Python tests run in worktree venv (.venv at repo root — reuse, don't reinstall).
- TDD: failing golden test FIRST, then implementation.
- Heartbeats ≤20min; blocked → marker + move on.

---

## SESSION OPEN — 2026-08-16T00:06Z

ŚĀSTRA-LEAD online. Source audit complete. Five W1 lanes dispatched in parallel.

### Pre-dispatch source facts (verified reads, not memory):

**B-01 dignity oracle:**
- `bg_dignity_reference._DIGNITY_REFERENCE` has full data: moolatrikona_sign/from/to per graha (:149-155 Jupiter → Sag, 0°–10°; :116 Sun → Leo, 0°–20°; :167 Saturn → Aquarius, 0°–20°; etc.)
- `ga_structural_writer.py:4853-4857` already defines `get_degree(g_name)` in the varga loop — oracle can use it directly
- `ga_structural_writer.py:4872-4879` has 4-value if/elif (exalted/debilitated/own/neutral) — **no moolatrikona** — the bug
- `ga_vargas_writer._compute_dignity:464-485` has local DIGNITY_TABLE with sign-level MT only (no degree gate), returns "Moolatrikona" or "Own" (Title case, not lowercase)
- `bo_pratijna_v4_engine.py:271-274` already has degree-gated MT check reading `r["mooltrikona_sign"]` (NOTE: "mooltrikona" vs "moolatrikona" — check actual key name)
- Oracle golden: Jup 9.79° Sag → moolatrikona (within 0°–10°); Jup 15° Sag → own (outside 0°–10°); Rahu/Ketu → neutral-default (§2.1)

**B-02 nodal aspects:**
- `ga_structural_writer.py:564` has correct `NODE_PARASHARI_ASPECTS={5:1.0,7:1.0,9:1.0}` — this is the canonical constant
- `services/gochara_grammar/primitives.py:189-193` SPECIAL_DRISHTI_DEG has Mars/Jup/Sat only; default `_DEFAULT_DRISHTI_DEG=[180.0]` — nodes get 7th only — **bug**
- `ga_yoga_writer.py:1499-1504` NB_GRAHA_DRISHTI has Mars/Jup/Sat only; NB_DEFAULT_DRISHTI=frozenset({7}) — nodes get 7th only — **bug**
- BPHS graha-drishti: Rahu/Ketu same as Jupiter (5th/7th/9th) per parashari mainstream
- Degree mapping: 5th aspect = 120°, 7th = 180°, 9th = 240° (matching Jupiter's [120.0, 180.0, 240.0])
- House-offset mapping: 5th/7th/9th (matching NB_GRAHA_DRISHTI frozenset({5,7,9}))
- Golden: Ketu in Leo (sign 5, 0-indexed=4) casts 5th aspect (120°) onto Venus in Sagittarius (sign 9, 0-indexed=8); Leo+4sign_offset=Sag ✓

**B-03 yoga predicate:**
- `ga_yoga_writer.py:644`: `if len(placed) >= 5 and all(p in ps_in_houses for p in placed)` — fires at ≥5, should be EXACTLY 7 in 7 DISTINCT houses (one per house)
- `placed` = [p for p in classical_seven if p in state.planet_sign] — up to 7 planets
- `ps_in_houses` = planets IN the 7 consecutive houses
- `constituent_houses` is set to `houses` (the 7 consecutive) regardless — correct only if all 7 are there
- Sibling correct pattern at :548-555 uses `actual_count == target_count` (exact match)
- Fix: `len(placed) == 7 and all(p in ps_in_houses for p in placed)` — verify no two planets share a house (need per-house uniqueness check)

**B-04 mi honesty pair:**
- `mi_darshana.py` lines 136, 183, 214, 246, 365, 508 have bare string `"clean"` — must be `"not_assessed"` (mi_adhilepa's honest tier precedent)
- `mi_bhara.py` falsifier-resolution: open_predictions from brahma_prospective_ledger may have empty/null observation_window; float(None) TypeError when score is processed — need isempty/None guard on open_predictions before passing to score_predictions_against_event
- C-01 repairs the data; B-04 guards the code

**B-05 spec pack (early priority — unblocks A-16/A-14/B-08):**
- Locate reading_checklist emitter (likely bo_laksana) — need file path
- Write 7th-house join spec for A-16's assess_marriage
- Write register glossary entries for F-114/131 leaked token families
- Add not_built checklist units for bhavat-bhavam (F-107) and cross-varga (F-108) in checklist source

---

## HEARTBEAT LOG

| Time (Z) | Lane | Status | Note |
|---|---|---|---|
| 00:06 | ALL | LEAD-ONLINE | Source audit complete; dispatching B-01..B-05 parallel |
| ~00:20 | B-02 | **EKV-B-02-BUILT** | 14/14 goldens pass; sha=692563430; pushed; lead review PASS |

---

## LANE STATES

| Lane | Branch | Status | Exit Test | Verifier |
|---|---|---|---|---|
| B-01 | ekv/b-01-dignity-oracle | DISPATCHED | golden: Jup 9.79°→MT, 15°→own, nodes→neutral | pending |
| B-02 | ekv/b-02-nodal-aspects | **BUILT** ✓ sha=692563430 | 14/14 pass incl. Ketu-Leo→Sag 5th ✓ | pending verifier |
| B-03 | ekv/b-03-yoga-predicate | DISPATCHED | golden: 4-house non-fire; Kedara fires | pending |
| B-04 | ekv/b-04-mi-honesty | DISPATCHED | 6× not_assessed in DB; mi_bhara no TypeError | pending |
| B-05 | ekv/b-05-spec-pack | DISPATCHED | A-16 spec delivered; checklist units present | pending |
| B-06 | — | W2 — waiting | muhurta honesty | — |
| B-07 | — | W2 — waiting | ph_nimitta tag | — |
| B-08 | — | W3 — waiting on A EKV-KERNEL-API-FROZEN + B-05 | ranker | — |
| B-09 | — | W2 — waiting | rebuild runbook for E | — |

---

## DEPENDENCY NOTES

- B-08 waits on BOTH: A's EKV-KERNEL-API-FROZEN marker AND B-05 glossary delivery
- E-03 gochara rebuild waits on B-01/B-02/B-03 merged + deployed
- B-05 specs must reach A-16 and A-14 BEFORE those lanes start; ŚĀSTRA-LEAD posts EKV-B-05-DELIVERED marker to CAMPAIGN_COORDINATION when builder returns

---

*ŚĀSTRA-LEAD — LEDGER_B — last updated 2026-08-16T00:20Z*
