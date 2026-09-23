---
artifact: KALA_PRE_ELEVATION_CHECKLIST
canonical_id: KALA_PRE_ELEVATION_CHECKLIST
version: "1.0"
status: CURRENT
date: 2026-09-24
author: "L3 Kāla strategic session (madhav-fc)"
purpose: >
  Everything that must happen before Kāla elevation (W1 takeoff) begins, in one list, with each
  item's owner and blocking strength. Assembled from the blueprint gap register, the three stream
  packets, the native's rulings, and this session's delegated decisions.
provenance_rule: >
  Items marked [V] were verified by this session at source. Items marked [A] are attributed to
  another stream and NOT independently verified here. Nothing is listed as done on a report alone.
---

# Kāla — everything outstanding before elevation begins

Grouped by what each item blocks, not by who owns it. **Nothing below is elevation work itself** —
this is the ground the elevation stands on.

---

## A — Waiting on the native (2 items, both one word)

| # | item | why only the native |
|---|---|---|
| A1 | **Authorize the L0 repair scope** — section C below, 8 items, one session, reviewer from outside the three Kāla streams | No L0 owner exists anywhere in the repository; this appoints the job, not a standing office |
| A2 | **Release the hold on L3 generation infrastructure** (G1) | Designed and frozen, never built; zero L1/L2 generations have ever been opened. Nothing can reach `DATA_ACCEPTED` until it exists |

*Closed since the last list: the E6 gate numbers (the native instructed 20/50 directly), the node
dṛṣṭi scope (N-14), and the reviewer for the three rulings this session declined.*

---

## B — Hard blockers on W1 takeoff (environment, not doctrine)

| # | item | blocks | owner |
|---|---|---|---|
| B1 | **Production cutover** — backup and isolated restore proven, cutover not executed | W1 entirely | administrator authority, outside the campaign [A] |
| B2 | **Disaster recovery** — PITR disabled, no restore drill ever run against any `kala_*` table | any unattended mutation | native ruling + one drill [V] |
| B3 | **Determinism gate** — `date.today()` in build paths, naive-timezone persistence | "wipe and rebuild freely" | temporal contract + a CI build-twice-diff [V] |
| B4 | **Both DB endpoints are refusing** (`127.0.0.1:5433` and `:5434`) | two staged SQL actions, and any measurement at all | infrastructure [V] |
| B5 | **Ephemeris backend is process-global and unowned** (G4, revised) — the 0.314″ figure's origin is decorated for locking but never configures a path; `panchang_engine` forces Moshier four times | the 0.314″ precision gate | every entry point must resolve-and-assert, or take an explicit backend [V] |

---

## C — The L0 repair job (one session, 8 items, blocked on A1)

All eight have their target values already located. None reinterprets the chart.

| # | item | source located |
|---|---|---|
| C1 | Re-cite 39 `bg_transit_rules` rows from the refuted "BPHS Ch.29" to Phaladīpikā Adh. XXVI, page-anchored | `PG322:C1`–`PG323:C1` [V] |
| C2 | Repair Venus rows 35/44/45 → 1/5/11 by UPDATE, never DELETE; INSERT the missing Mercury 8→1 | Kṣetra L0 spec [A] |
| C3 | Six Rāhu/Ketu vedha rows → disposition under N-14 | ruled [V] |
| C4 | Populate `bg_sarvatobhadra_grid` by transcription, under migration 526's own partition invariant | `PG346:C1`–`PG352:C1` [V] |
| C5 | Pin which of Adh. XXVI's **two** 1–5 malefic scales `bg_vedha_malefic_scale` cites | `PG349` vs `PG353` [V] |
| C6 | Replace migration 624's **sign-level** node anchor with a **degree-level** one — expected mean node 49.033° ± arcsec at JD 2445735.717361 | both frames give the same sign, so the existing anchor provably cannot fail [V] |
| C7 | Declare `ephemeris_daily`'s node frame **and** epoch (noon UT) — it stores TRUE under a contract asserting mean | [V] |
| C8 | Correct `ka_vedha_gochara/logic.py`'s docstring, which asserts a four-text corpus "confirmed by direct search, not assumed" and is false in every load-bearing part | [V] |

---

## D — Ruled, execution pending (no further decision needed)

| # | item | ruling |
|---|---|---|
| D1 | Century writer `is_active=false` at runbook step 3, reversible at WP10, nothing deleted | N-6a [V] |
| D2 | Registry declares the century writer's production write — add `kala_gochara_windows` to `clear_tables` | F-30, runbook step 5 [V] |
| D3 | Remove node dṛṣṭi from the served λ and regenerate as generation `'4.0'`, keeping the term one generation as a labelled non-scoring annotation | N-14 + N-5 + N-10 [V] |
| D4 | Sade-Sati → `source_qualification = 'unsourced'`, served flagged, no confident narration | D-D, this session [V] |
| D5 | Run the Sade-Sati predicate query — **by predicate, not by term** — against the primaries | staged, blocked on B4 [V] |

---

## E — Gates that must fire before any code is written

| # | item | why |
|---|---|---|
| E1 | **Third independent review of the Saṅgam plan** — the text v1.0 is built from has never been reviewed by anyone; v0.1 returned rework on 19 findings, v0.3 on 10 | D-8 stage-3 **entry** gate, not a close condition [A] |
| E2 | **Kṣetra stage-3 authorization** — prompt prepared, status `AWAITING_NATIVE_AUTHORIZATION` | [A] |
| E3 | **Gochara N-18** — WP0-7 branch deliberately unpushed pending it | [A] |
| E4 | **Independent-verifier capacity** (G13) — one reviewer per wave who is not the author; the three streams are mutually conflicted on the cross-cutting findings | [V] |

---

## F — Known-broken infrastructure that will bite during elevation

| # | item | effect |
|---|---|---|
| F1 | **Governance frontmatter gate is blind to this campaign** (G18) — no governed glob reaches the briefs tree, and a YAML parse failure raises no violation even in scope | every artifact we produce passes CI without being checked [V] |
| F2 | **Migration numbers 1071–1074 claimed by four unmerged branches** | collision on merge [A] |
| F3 | **Branch divergence** — `l3/kala-elevation-readiness` and `sangam/stage3` have both moved; readiness still shows the stale D-1 heading | a reader on the wrong branch acts on stale values [V] |
| F4 | **No cost budget** (G5) — registry claims 24 min/chart, ≥7.5 h measured | cannot promise a build time [V] |
| F5 | **No cancel / pause / resume, no substep progress, unearned `rows_written`** (G6) | the person's first touch of the build UI [V] |
| F6 | **No retrieval capability over `kala_field`** (G8) | the largest asset is unreadable by the product [V] |
| F7 | **No admissible receipts** for `CONSUMER_INTEGRATED` / `VALUE_EVALUATED` (G7) | the headline cannot move past `DATA_ACCEPTED` [V] |
| F8 | **Ordinary-period fixtures absent** (G17) | the product's own §9 is untestable [V] |

---

## G — Standing discipline, carried into every lane

1. **Absence is established by `count(*)` against the object** — never a directory, never a search
   tool, never another artifact's assurance that it checked.
2. **Check the ruling set, not a ruling.**
3. **Convergence between sessions is not verification when they share a premise.** Four sessions
   agreed for a day; one direct query dissolved it in two hours.
4. **A commit succeeding is not the edit applying.** Assert the post-condition, not the exit code.
5. **A signal with no code path that could make it read false is null, not green.**
