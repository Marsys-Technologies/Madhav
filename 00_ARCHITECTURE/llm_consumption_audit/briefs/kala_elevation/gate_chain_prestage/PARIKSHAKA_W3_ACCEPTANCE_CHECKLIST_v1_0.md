---
artifact: PARIKSHAKA_W3_ACCEPTANCE_CHECKLIST (Track T2 gate-chain pre-staging)
canonical_id: PARIKSHAKA_W3_ACCEPTANCE_CHECKLIST
version: 1.0
status: PRE-STAGED — not yet walked; walk this checklist ONLY after real production
  data exists for both charts and Gate W2 has been evaluated (W3 computations run
  over the field W2 establishes).
created: 2026-08-05
author: Track T2 builder (ṢAḌ-DARŚANA overnight campaign, gate-chain pre-staging lane)
governing: SHAD_DARSHANA_BRIEF_v2_0.md §3 "Gate W3" (verbatim source of every item below)
  + SHAD_DARSHANA_NIGHT_RUN_v1_0.md §A (PARĪKṢAKA role charter, four-disposition vocabulary)
chart_ids:
  - 482012f1-710e-4a25-994a-93821f5871aa   # Abhisek Mohanty (native, primary canonical)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a   # Abhinandan Mohanty (secondary canonical)
---

# PARĪKṢAKA — Gate W3 live acceptance checklist

**How to use this file.** Same discipline as the W2 checklist in this directory: PARĪKṢAKA
(Opus, never writes code) walks each item below against LIVE production, on **BOTH** canonical
charts, after the gate-close deploy. Four dispositions only —
`VERIFIED-FIXED` / `VERIFIED-NO-DEFECT` / `PARKED-HONEST` / `FAILED-REOPENED` — no "passed
with caveats". Every clause below is copied **verbatim** from `SHAD_DARSHANA_BRIEF_v2_0.md`
§3 "Gate W3" (lines 422–426 as of brief v2.0); this checklist only adds structure.

---

## W3.0 — Item 9 / S4-05 re-test (run FIRST — separate staged artifact)

**Brief text:** *"health class passes the S4-05 re-test."*

This is the highest-stakes single clause in Gate W3 — it closes the campaign's one
TRUST-BREAKING veto (`UAT_DARPANA_REGISTER_v1_0.md` §S4-05). It is pre-staged as its own
executable script, not just a checklist row:
`platform/python-sidecar/scripts/s4_05_data_real_retest.py` (this repo, sibling directory).

| # | Check | 482012f1 evidence | 1c826d5a evidence | Disposition |
|---|---|---|---|---|
| W3.0.a | `python3 scripts/s4_05_data_real_retest.py` run against production `DATABASE_URL`, exit code `0` (both charts PASS the two-axis covered predicate: every item-9 health class targeted AND swept; `'health'` absent from `domains_not_covered`). | | | |
| W3.0.b | The script's `evidence` block (health/legacy window row counts) is inspected directly — an honest-empty health-window count is legitimate (no window in this chart's horizon is a real possible answer) but the COVERAGE flags must be correct regardless of count. | | | |
| W3.0.c | The `kala_windows_crosscheck` block is inspected for any reintroduction of the ORIGINAL incoherence (a "clean" gochara answer contradicted by real `kala_windows` health-domain/DOSHA activations) — best-effort, not gating on its own, but a real finding here is escalated, not ignored. | | | |
| W3.0.d | The two existing CODE-level S4-05 regression suites are re-confirmed still green on the gate-close branch: `pytest tests/l3/test_s4_05_health_adverse_class.py` and `vitest src/__tests__/s4_05_health_coverage.test.ts` (platform-mcp). | | | |

## W3.1 — Every computation two-pass verified on BOTH charts, served through its view(s), citation-carrying

**Brief text:** *"every computation two-pass verified on BOTH charts, served through its
view(s), citation-carrying"*

The W3 item list (brief §3 W3): 1-full (sandhi calendar) · 3 (sky calendar) · 4 (moorti) ·
5 (vedha + Sarvatobhadra) · 6 (activity rule tables) · 7 (muhūrta-lagna) · 9 (health/adverse,
see W3.0 above) · 13 (Tithi-Praveśa) · 14 (janma-anchored rules) · 16 (Kota) · 17 (Sudarśana) ·
31 (period-echo) · 33 (absence-of-expected) · 34 (contrastive EXPLAIN) · 36 (contender lattice)
· 41 (Muhūrta Factor Census) · 37-part (paddhati schema) · 38-full (ELECT depth) · E6-full.

| # | Item | Two-pass verified? | Served through its view(s)? | Citation-carrying? | 482012f1 | 1c826d5a | Disposition |
|---|---|---|---|---|---|---|---|
| W3.1.1 | (1-full) Daśā-sandhi calendar | | | | | | |
| W3.1.3 | (3) Sky-event calendar | | | | | | |
| W3.1.4 | (4) Moorti-nirṇaya per ingress | | | | | | |
| W3.1.5 | (5) Vedha + REAL Sarvatobhadra grid (closes R-19) | | | | | | |
| W3.1.6 | (6) Activity-specific muhūrta rule tables | | | | | | |
| W3.1.7 | (7) Muhūrta-lagna + strength check | | | | | | |
| W3.1.9 | (9) Health/adverse class — see W3.0 above (do not re-litigate here, cross-reference only) | | | | | | |
| W3.1.13 | (13) Tithi-Praveśa | | | | | | |
| W3.1.14 | (14) Janma-anchored election micro-rules | | | | | | |
| W3.1.16 | (16) Kota-Chakra transit fortress | | | | | | |
| W3.1.17 | (17) Sudarśana-Chakra year-wheel (post collision-audit; writer named `ka_sudarshana_varsha`) | | | | | | |
| W3.1.31 | (31) Period-echo mining (hypothesis-framed) | | | | | | |
| W3.1.33 | (33) Absence-of-expected detector | | | | | | |
| W3.1.34 | (34) Contrastive EXPLAIN | | | | | | |
| W3.1.36 | (36) Contender lattice + adjudication engine (ELECT+YAJÑA shared) | | | | | | |
| W3.1.41 | (41) Muhūrta Factor Census + corpus extraction | | | | | | |
| W3.1.37p | (37-part) Paddhati profile schema | | | | | | |
| W3.1.38f | (38-full) ELECT depth: lattice-backed slates, frontier, gap report | | | | | | |
| W3.1.E6 | (E6-full) NOW state_delta · AHEAD decision_value · STORY developmental thesis · PRIORITIZE attention ledger · EXPLAIN pedagogy+counterfactual | | | | | | |

## W3.2 — ELECT candidates carry judgment ledgers

**Brief text:** *"ELECT candidates carry judgment ledgers (doṣas → parihāras → residual)"*

| # | Check | 482012f1 evidence | 1c826d5a evidence | Disposition |
|---|---|---|---|---|
| W3.2.a | At least one real `kala_elect_get` response carries, per candidate, a judgment ledger with the full chain: `doṣas_present → parihāras_applied (with citations) → residual_doṣas → net standing`. | | | |
| W3.2.b | Citations in the ledger are real (resolve to actual corpus rows), not placeholder/fabricated strings. | | | |

## W3.3 — Abhijit-override case demonstrably rescues a candidate

**Brief text:** *"the Abhijit-override case demonstrably rescues a candidate"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W3.3.a | Construct or locate a real query where a candidate would otherwise be eliminated by a doṣa that Abhijit muhūrta classically overrides, and confirm the served ELECT response actually rescues it (not merely that the rule exists in the corpus — the SERVED behavior is what's checked). | | |

## W3.4 — Gap report present when the horizon lacks the ideal

**Brief text:** *"gap report present when the horizon lacks the ideal"*

| # | Check | 482012f1 evidence | 1c826d5a evidence | Disposition |
|---|---|---|---|---|
| W3.4.a | Construct or locate a real query whose constraint conjunction has NO ideal candidate in the searched horizon, and confirm the response returns a gap report (naming the eliminating constraint and when the pattern next occurs) rather than a silent/unexplained empty. | | | |

## W3.5 — Factor census served in coverage

**Brief text:** *"factor census served in coverage"*

| # | Check | Evidence | Disposition |
|---|---|---|---|
| W3.5.a | The Muhūrta Factor Census (item 41, 50-row census per the ledger's own build evidence) is visible in a real served coverage block, distinguishing `computed` / `not_computed` / `not_in_corpus` rows honestly (not flattened into one undifferentiated list — §N.6 Serving Density Principle). | | |

## W3.6 — Health class passes the S4-05 re-test (cross-reference)

Already covered fully at **W3.0** above — this row exists only so the checklist's item-by-item
structure visibly maps 1:1 onto the brief's own Gate W3 sentence, per this checklist's own
"add structure, not content" discipline. Disposition here MUST equal W3.0's overall disposition,
never a separate judgment.

| # | Check | Disposition (must equal W3.0) |
|---|---|---|
| W3.6.a | Cross-reference: item 9 / S4-05 disposition == W3.0's recorded disposition | |

---

## Overall Gate W3 disposition

| Chart | All W3.0–W3.5 items VERIFIED-FIXED or VERIFIED-NO-DEFECT? | Any FAILED-REOPENED? | Gate W3 disposition for this chart |
|---|---|---|---|
| 482012f1 | | | |
| 1c826d5a | | | |

**Gate W3 closes only when BOTH charts show no `FAILED-REOPENED` row above, every item carries
a real disposition (no blanks), and item 14 (janma-anchored election micro-rules) — confirmed
NOT-STARTED as of this pre-staging pass (2026-08-05) — has actually been built and dispositioned
before Gate W3 can honestly close.** A parked item is legal only as `PARKED-HONEST` with a named
reason and release condition.
