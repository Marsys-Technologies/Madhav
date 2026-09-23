---
artifact: KALA_PRE_ELEVATION_CHECKLIST
canonical_id: KALA_PRE_ELEVATION_CHECKLIST
version: "1.5"
status: CURRENT
date: 2026-09-24
revision_note: "v1.2 — after the L0 repair (PR #2727): §A shrinks to three native items; §C becomes the PR close-out; §D gains the Sade-Sati query result; §E records that the Saṅgam entry gate did not gate; §B4 downgraded (production reachable via proxy on 5432)."
author: "L3 Kāla strategic session (madhav-fc)"
purpose: >
  Everything that must happen before Kāla elevation (W1 takeoff) begins, in one list, with each
  item's owner and blocking strength. Assembled from the blueprint gap register, the three stream
  packets, the native's rulings, and this session's delegated decisions.
provenance_rule: >
  Items marked [V] were verified by this session at source. Items marked [A] are attributed to
  another stream and NOT independently verified here. Nothing is listed as done on a report alone.
---

# Kāla — the remainder, after the L0 repair

Grouped by what each item blocks. **[V]** verified by this session at source; **[A]** attributed.

---

## A — The native's, three items

| # | item | why only the native |
|---|---|---|
| ~~A1~~ | ~~Release the W1 hold~~ **RULED — RELEASED 2026-09-24** (native, verbatim: "Yes, release the hold. On the generation infrastructure.") | build the §6 design physically; the cutover (B1) still gates W1 [V] |
| ~~A2~~ | ~~Authorize Kṣetra stage 3~~ **RULED — AUTHORIZED 2026-09-24** (native, verbatim: "I want to authorize Kshetra … I have just authorized stage three now"). **Stage 3 only; stage 4 explicitly not opened** ("I don't want to start the stage four") | the Kṣetra stream flips its prompt from `AWAITING_NATIVE_AUTHORIZATION` and executes in its own worktree [V] |
| A3 | ~~Rule Gochara N-18~~ **CORRECTED: N-18 is already `NATIVE_RATIFIED`** on the Gochara v2.0 sheet (read from that session's worktree, read-only). N-18 is a *delivery* item — push the 13-commit WP0-7 branch and open a code-only PR, no build — not a doctrinal question. **The remaining action is the Gochara session's push, not a native ruling.** One new blocker on it: the ratified plan assigned that branch migrations **1075/1076**, which the L0 repair applied to production last night under the same numbers (my prompt said "1075 or higher" without knowing). Renumber to 1077/1078 before push — sent to that session | [V] |

*Closed: the L0 scope authorization (executed), the E6 gate numbers, the node scope, the reviewer for the three conflicted rulings.*

---

## B — Hard blockers on takeoff

| # | item | owner |
|---|---|---|
| B1 | **Production cutover** not executed | administrator authority [A] |
| B2 | **Restore drill** — PITR disabled, none ever run on a `kala_*` table | native ruling + one drill [V] |
| B3 | **Determinism gate** — none in CI (the only "determinism" hit is a Pariprashna test) | temporal contract + build-twice-diff [V] |
| B4 | **Ephemeris backend process-global and unowned** — the L0 repair declared frame and epoch (items 6–7) but did *not* touch this; `v3_spline_accuracy.py` still never sets a path and `panchang_engine` still forces Moshier | every entry point resolves-and-asserts [V] |
| B5 | *(downgraded)* Local DB endpoints `5433`/`5434` refuse; **production is reachable** via `cloud-sql-proxy --port 5432` with the existing `.pgpass` — a dev-environment item, no longer a blocker [V] | — |

---

## C — Close out the L0 repair (PR #2727, OPEN, BLOCKED)

Seven of eight items applied to production and **verified live by this session with the PR's own falsifiers** [V]. What remains:

| # | item | note |
|---|---|---|
| ~~C1~~ | **DONE — an independent review ran** (agent outside the three streams; six findings, three real defects fixed in `2d3b25fb2`, dispositions posted in the PR thread under the author's account). No GitHub review object exists, which is why my earlier "none requested" was true and misleading | [V] |
| C2 | **PR is RED on two required checks** (`Unit Tests`, `Governance Gates`) for one shared cause: `nirmana-analysis-layer-pins.json` pins a per-layer `writer_inventory_sha256`, and the repair legitimately moves 38 writer digests (a digest hashes the transitive source closure, not the file). Re-pin under the governed procedure, then merge | [V — author's diagnosis read; not reproduced by me] |
| C2b | **All FIVE migrations are applied to production, not two:** 1075, 1076 (21:07–21:08 UTC), 1077, 1078 (21:17), 1079 (22:03). I reported two because my query only named two. 1077/1078 reseal the frozen integrity contracts items 1/2/3/5 correctly broke (the old seal went red as designed; the reseal records the prior hash as its precondition). 1079 fixes 1078's own false description | [V — live query] |
| C2c | **Nineteen `bg_transit_rules` rows still carry the refuted "BPHS Ch.29" citation** — 18 unfavourable + 1 favourable-without-vedha — outside item 1's row-verified predicate, correctly left un-recited rather than re-cited unverified. A residual for a later, separately-verified re-citation | [V — reviewer finding, confirmed in 1079] |
| C2d | Migration 1075's header arithmetic ("640× tighter") is wrong; correct is ~366×. 1075 is applied so it is not edited; recorded in 1079 | trivial [A] |
| C3 | **Two consumers are now silently stale.** `kala_vedha_gochara` (355 rows) and `kala_moorti_nirnaya` (143 rows) were built from the *old* citations and **neither writer fingerprints its `bg_transit_rules` input**; `ka_sangam` does. Rebuild both, or add the fingerprint first so the staleness is detectable | the repair's own §N.8 consequence, unflagged by the PR [V] |
| C4 | **Sarvatobhadra grid — blocked correctly, against my claim.** Partially recoverable (outer ring, rāśis, tithi groups, weekdays, 3 worked asterisms), not buildable in full: letter cells OCR-destroyed, 3/28 networks, traversal direction unstated. If a partial build is wanted: native ruling on the direction convention + source images or another edition. Otherwise stays empty with its docstring saying why | [V] |
| C5 | PR body calls migration 1042 "unapplied"; it was applied 2026-09-19. Skipping it was right, the reason was wrong | trivial [V] |

---

## D — Ruled, execution pending

| # | item | status |
|---|---|---|
| D1 | Century writer `is_active=false` at runbook step 3 | N-6a; Gochara runbook [A] |
| D2 | Add `kala_gochara_windows` to that asset's `clear_tables` | F-30, step 5; SQL staged [V] |
| D3 | Remove node dṛṣṭi from the served λ; regenerate as `'4.0'` | N-14/N-5/N-10; Gochara execution [A] |
| D4 | **Sade-Sati demotion — decided, NOT executed.** `source_qualification='unsourced'`, served flagged, no confident narration. Surfaces: `routers/sade_sati.py`, `routers/permission_curve.py`. Needs a serve-side owner | [V] |
| D5 | **Sade-Sati predicate query — RUN.** Substrate (Saturn's house-by-house results from the janma-rāśi) is in Phaladīpikā Adh. XXVI, 26 rows; the named 7½-year **composite** is not found. Demotion targets the composite. Count-level only; rows not read in full | [V] |

---

## E — Gates that must fire before code — and one that did not

| # | item | status |
|---|---|---|
| E1 | **Saṅgam D-8 entry gate did not gate.** The third independent review of plan v1.0 has **no artifact** (only the v0.1 and v0.3 review requests exist) — and the stage-3 executor has already landed Phases 0–5 on `sangam/stage3`. The gate was written after the code. It must become a **merge gate** on that branch, run by a reviewer who is not the author, before anything from it reaches `main` | [V] |
| E2 | Kṣetra stage-3 authorization | = A2 |
| E3 | Gochara WP0-7 push (N-18, ratified) after renumbering 1075/1076 → 1077/1078 | = A3 [V] |
| E4 | Independent-verifier capacity per wave (G13) | structural [V] |

---

## F — Known broken, will bite during elevation

| # | item |
|---|---|
| F1 | Governance frontmatter gate blind to the briefs tree; parse failure raises nothing (G18) [V] |
| F2 | Migration numbers 1070–1074 claimed by four unmerged branches; 1075–1076 now consumed by the L0 repair [V] |
| F3 | `l3/kala-elevation-readiness` and `sangam/stage3` diverged — a merge plan is owed [V] |
| F4 | No cost budget; registry claims 24 min/chart, ≥7.5 h measured (G5) [V] |
| F5 | No cancel/pause/resume, no substep progress, unearned `rows_written` (G6) [V] |
| F6 | No retrieval capability over `kala_field` (G8) [V] |
| F7 | `CONSUMER_INTEGRATED` / `VALUE_EVALUATED` exist in no enum; headline stuck at 0 (D2, unruled) [V] |
| F8 | Ordinary-period fixtures absent (G17) [V] |

---

## G — Before elevation can be *shown* (from the review, the true prerequisite)

| # | item |
|---|---|
| G1 | **Freeze `KALA_BASELINE_v1_0.md`** — 13 questions, 3 proving cases, 1 ordinary period, run against current serving. Without it every wave closes on *changed*, not *elevated* [V — it does not exist] |
| G2 | The five synergy contracts as five packets with lanes — the layer-level elevation [V — unowned] |
| G3 | The receipts enum (= F7) |

---

## H — Standing discipline

1. Absence by `count(*)` against the object. 2. The ruling set, not a ruling. 3. Convergence is not
verification under a shared premise. 4. Assert the post-condition, not the exit code. 5. No signal
without a detector. 6. **A preview is not a page.**
