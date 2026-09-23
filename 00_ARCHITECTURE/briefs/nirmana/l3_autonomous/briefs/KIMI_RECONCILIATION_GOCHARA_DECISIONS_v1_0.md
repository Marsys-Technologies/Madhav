---
artifact: KIMI_RECONCILIATION_GOCHARA_DECISIONS
version: "1.0"
status: CLOSED
date: 2026-09-23
reviews: KIMI_K3_REVIEW_GOCHARA_DECISIONS_v1_0.md (Kimi K3, effort=max, 39,725 bytes; verdict — no BLOCKING, 3 MAJOR, 12 MINOR, 11 gaps in §E)
reviewed_document: GOCHARA_DECISION_RECOMMENDATIONS_v1_0.md
produces: GOCHARA_RULING_SHEET_v2_0.md (proposed rulings for the native's authorization)
method: "Every finding asserting a code or corpus fact was re-verified at source (engine.py, w44_weight_fitting.py, resolution_hierarchy.py, peaks.py, the BPHS OCR) or by count against classical_text_chunks before disposition. Labels: VERIFIED · ACCEPT · ACCEPT-AMENDED · REJECT."
---

# Reconciliation — Kimi K3 review of the pending-decision recommendations

## 1. Disposition of the review's findings

| # | Finding | Verification | Disposition | Effect on the ruling sheet |
|---|---|---|---|---|
| **A-1 MAJOR** | N-15 mislocates Sade-Sati: it enters PERMISSION (`SYSTEM_WEIGHTS`, normalized), not `quality_gates` | **VERIFIED** `engine.py:1367-1374, :1411-1413`; `quality_gates` is the vedha suppression product `:468` | **ACCEPT** — my error | N-15 restated: drop `sade_sati` from `SYSTEM_WEIGHTS` and renormalize, with the global permission lift disclosed in the manifest and measured in both walkthroughs |
| **A-2 MAJOR** | M-1's "delta is entirely box removal" is false: served bound is 5.0°, WP4's kernel used 1.0° | **VERIFIED** `engine.py:222` (=5.0), `:939`, `:1039`; `legacy_semantics.py:67`; arithmetic: no-box×5.0° → 0.7888, no-box×1.0° → 0.7441 | **ACCEPT** — my error | M-1: six-arm battery incl. `no-box × 5.0°`; re-pin/remove the constant and mirrors at ratification; fallback candidate = box-removed at 5.0° |
| **A-3 MAJOR** | M-7's re-OCR remedy aims at the wrong text; the kakṣyā source in the served corpus is likely Phaladīpikā; read the 1 UK + 6 nāḍī rows | **VERIFIED in part.** BPHS: no `kaks*` at any fuzz in either volume (edition-absence plausible). **Corrected by count:** served Phaladīpikā has **0** kakṣyā rows under six phrasings `[L]`; the UK row is Kakṣyā-Hrāsa (unrelated); the **6 nāḍī rows are the aṣṭakavarga kakṣyā doctrine** — `PG1615` *"Kakshyas (30° ÷ 8 = 3°45′) of those planets which have donated bindus"*, `PG1616` transit through a kakṣyā with/without a bindu `[L]` | **ACCEPT-AMENDED** | M-7 remedy reordered: (1) nāḍī rows graded as MEDIUM-provenance testimony for exactly G-10's per-contributor model; (2) Phaladīpikā recorded absent by count; (3) BPHS re-OCR third, as the F-27 settler only |
| **A-4 MINOR** | N-16 understated: absent keys default to wired=True; w30 absent from dict and register | **VERIFIED** `w44_weight_fitting.py:150-169` (`.get(key, True)` rule in the comment block) | **ACCEPT** | N-16 becomes a three-way detector (dict ↔ register ↔ `engine.py` imports/product) and must land before any w44 re-fit |
| **A-5 MINOR** | my `engine.py:154` citation is stale | VERIFIED (real sites `:222/:939/:1039`) | ACCEPT | citation-drift sweep folded into N-16 |
| **A-6 MINOR** | exceptions = general mutual exclusion (Sun↔Saturn, Moon↔Mercury), not three instances | consistent with PG322/323 and `bphs_vol1:24418-24424` | ACCEPT | M-8 rule restated |
| **A-7 MINOR** | vipareeta cancellation is an interval | **VERIFIED** `bphs_vol1:24439-24442` *"…proves auspicious till he has a companion"* | ACCEPT | M-8: `cancelled_from`/`cancelled_until` |
| **A-8 MINOR** | say whether the nāḍī rows state the composite doctrine | **VERIFIED**: `nadi_navamsa_patel` PG1334 *"The transit of Saturn through the 12th, 1st and 2nd houses from the Moon is known as sade-sati"*; PG786, PG1333 `[L]` | ACCEPT | N-15 cites the nāḍī rows as its testimony source, graded MEDIUM |
| **A-9 MINOR** | M-6 order flip must be re-ruled on one count of PG214–220 | **count satisfied**: `phaladeepika` PG214–PG220 rows exist and were read `[L]` | ACCEPT | M-6 order re-ruled explicitly in the sheet |
| **A-10 MINOR** | N-17 must address the 90-day separation filter and re-pin the golden test | **VERIFIED** `resolution_hierarchy.py:104-105`; `peaks.py:26-44` has no separation filter | ACCEPT | N-17: separation moves to serve-time trim policy; golden test re-pinned as legacy baseline |
| **A-11 MINOR** | A-3 gate omits WP8 M-1 ratified + WP9 M-8 landed; align §1/§4 candidate lists | — | ACCEPT | sheet A-3 |
| **A-12 MINOR** | pre-declare retrograde-saturated windows for M-2(c) | — | ACCEPT | M-2 |
| **A-13 MINOR** | KP5 byte-duplicate in SOURCE_DATA | **VERIFIED** `cmp` identical | ACCEPT | housekeeping to the corpus owner |
| **A-14 MINOR** | a standing nāḍī-tier grading ruling is missing | — | ACCEPT | **N-21** (new) |
| **A-15 MINOR** | N-13 ruled but unscheduled | — | ACCEPT | **N-22** (new) |
| B/M-1 | six-arm discrimination battery; translator Rule-6 30° note | — | ACCEPT | M-1 |
| B/M-8 | evaluation order exceptions→vipareeta; instant-grain needs `precision_regime` | — | ACCEPT | M-8 |
| B/M-3 n.1 | Moon-from-Moon list should be verse-cited in the channel if served Phaladīpikā holds it | **count: not found** under `moon ∧ transit ∧ (1st…11th) ∧ auspicious` in `phaladeepika` `[L]`; KP-only corroboration | ACCEPT-AMENDED | channel content marked `[U]` pending a page-grain read; Sade-Sati testimony kept out of the channel |
| B/M-6 | Prāṇapada may be a spelling miss | **re-counted** with `pranapad|prana pada|prāṇapada` ∧ transit: **0 rows** `[L]` | corrected | deferral stands |
| C/N-15 | no Parāśari primary source exists for the composite; grade nāḍī as citation; re-admission only on a primary attestation | consistent with all counts | ACCEPT | N-15 |
| D | one candidate with recorded flags + factor-level delta report; fallback = no-box×5.0° | — | ACCEPT | A-3 |
| E-1..E-11 | eleven gaps | — | ACCEPT all | folded into N-15, N-22, A-3 (G-9 landing state, benchmark owner/inputs), N-16, M-3, M-8, M-1, N-21, M-2, housekeeping |

**Rejected:** nothing. **Two of the reviewer's premises corrected by count:** Phaladīpikā is not the kakṣyā source in the served corpus (0 rows); the Moon-from-Moon list is not found in served Phaladīpikā by predicate. Both were marked `[U]` by the reviewer, who could not query the table.

## 2. New since the review (from the Saṅgam session, verified here)
Migration numbers **1071/1072 are claimed on three other branches** (`sangam/stage3` and `l3/kala-elevation-readiness` in `platform/supabase/migrations`; `l3/kala-p1-1-b1-clear-guard` in `platform/migrations` — the Phase 1.1 Clear guard and registry-truth migrations themselves), and **1073/1074 on `l3/kala-p1-2-builder-grants-timeout`** `[R]`. This branch's two migrations were renumbered **1075/1076** (lowest free across every remote branch) with every reference rewritten and the suite re-run. Consequence for A-2: runbook steps 0 and 3 are already partly in flight on `l3/kala-p1-1-b1-clear-guard` — tranche 1 must consume that branch, not duplicate it.
