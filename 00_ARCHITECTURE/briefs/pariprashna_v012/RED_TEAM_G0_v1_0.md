---
artifact: RED_TEAM_G0_v1_0
canonical_id: PARIPRASHNA_V012_RED_TEAM_G0
version: 1.0
status: CLOSED — panel complete, all accepted findings fixed in place 2026-08-18
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18)
date: 2026-08-18
authoritative_side: claude
role: >
  The B.5/GIP §L.7 red-team record for the v0.12 Phase-1 package — the pass that
  qualifies the package as input to PARIPRASHNA_ARCHITECTURE v1.0-RC. Four
  independent adversarial reviewers, distinct lenses, full findings + adjudications
  + fix log. Native ruling NCD-1..8 preceded this panel; CURRENT status remained
  correctly gated on this record (ordering rationale: the rulings are value
  decisions the panel could not have made; the panel's job was the package's
  soundness, which it attacked post-ruling).
changelog:
  - "1.0 (2026-08-18): panel run (4 lenses), findings adjudicated, fixes applied in place."
---

# Red-Team Record — v0.12 Package, Gate-0 Pass

## §1 — Panel and verdicts

| Lens | Charge | Verdict |
|---|---|---|
| A | Over-claim / traceability / evidence-class integrity | **PASS-WITH-FIXES** (1 HIGH-as-stated → rejected on evidence, 1 MED, 4 LOW) |
| B | Safety/privacy/consent completeness vs MP §3.5 clause-by-clause | **PASS-WITH-FIXES** (3 HIGH, 4 MED, 4 LOW) |
| C | Mission drift / doctrine conflict / scope smuggling | **PASS-WITH-FIXES** (0 HIGH, 4 MED, 3 LOW) |
| D | Fresh-agent readability / executability (cold read; 11-question scorecard 8/11 → fixes) | **PASS-WITH-FIXES** (2 HIGH, 3 MED, 3 LOW) |

Aggregate: **PASS-WITH-FIXES.** Zero CRITICAL. All ACCEPTED findings fixed in
place in the package the same day; adjudications below. Everything the panel
attacked and could not break is listed in each lens's "held" record (kept in
the panel outputs; headline: every number, migration id, MP §3.5 subsection,
PB-4 lane/ruling citation, and contradiction-matrix adjudication survived).

## §2 — Adjudications and fixes

| # | Lens/finding | Adjudication | Fix applied |
|---|---|---|---|
| 1 | A-HIGH: §15 claims writes at `briefs/pariprashna_v012/` — path absent in reviewer's corpus | **REJECTED-AS-STATED**: the writes ARE landed on the real repo (device commit confirmed 2026-08-18); the reviewer's corpus was a container snapshot lacking them. No package error. Recorded here so the evidence trail explains the discrepancy. | none needed |
| 2 | A-MED: "zero runtime enforcement" of §3.5 overstates — §3.5.E seal/freeze/transitions + arm-2 are live | **ACCEPTED** | master §1 verdict-2 and V12-F1 rescoped to "§3.5.B/C/D/F unenforced; §3.5.E partially enforced" |
| 3 | A-LOW ×4: limitation(a) vs LIVE census; STATIC_VERIFIED definition too narrow; F-lane→gate mapping overstated; §0 scope quote truncated | **ACCEPTED** (all) | limitation carve-out; NFR §1 definition widened; §11 intro rewritten with the true lane split; §0 quoted in full |
| 4 | B-F1 HIGH: §3.5.A.6 Reversibility untranslated | **ACCEPTED** | new HS-5 (receipt-linked retraction record, recipient notification, ledger note) |
| 5 | B-F2 HIGH: double red-team collapsed into sign-off | **ACCEPTED** | HS-3 rewritten as three distinct steps (seal → two independent adversarial passes → separate sign-off); HS-4(b) follows |
| 6 | B-F3 HIGH: missing abuse case — non-consenting adult third-party charts | **ACCEPTED** | A9 added; `native_self` strictly defined (subject IS the native + minor-guardian carve-out) |
| 7 | B-F4/F5/F6/F7 MED: breach response; audit-trail integrity; LEL edit-flag; predictive red-team cadence | **ACCEPTED** (all) | §5 rules block: incident-response note + notification duty; INSERT-only/hash-chained audit rows; LEL §3.5.E fields carried verbatim; new HS-6 sampling receipts into §IS.8 cadence |
| 8 | B-F8/F9/F10/F11 LOW: acharya redaction enforcement; public fail-closed; consent drops (disputes→DISAGREEMENT_REGISTER, default-anonymous, excluded-subject register); NCD-4 letter-deviation; session revocation + export format | **ACCEPTED** (all) | §1 per-class enforcement notes (public FAIL-CLOSED until §3.9.B); §4 consent additions; HS-2 consent-doc disclosure; §5 revocation both doors + JSON manifest; NCD-4 routing → NCD-10 |
| 9 | C-F1 MED: artifact-1 subordination list omitted GIP + CAPABILITY_MANIFEST | **ACCEPTED** | §12 row restored to the full §21-rule-5 five-authority set |
| 10 | C-F2 MED: `calibration_method_version` silently amends Ruling-79's fixed schema | **ACCEPTED** | calibration §8 now discloses it as a PROPOSED Ruling-79 amendment for the G9 native point |
| 11 | C-F3 MED: consent schema had no NCD | **ACCEPTED** | **NCD-9 added (OPEN)** with the Scope-Boundary rationale |
| 12 | C-F4 MED / B-F10: NCD-4 relaxation needs a formalization route (§3.10.B vs ND directive) | **ACCEPTED** | **NCD-10 added (OPEN)**; recommendation: ND directive now, folded into next natural MP revision |
| 13 | C-F5 LOW: early acharya-reviewer application is M10-gated | **ACCEPTED** | NFR §5 dimension relabeled aspirational-for-external; native §J + model panel until §3.7 opens |
| 14 | C-F6 LOW: novel status string | **ACCEPTED** | `SUPERSEDED` (enumerated vocab) + mechanism in banner body |
| 15 | C-F7 LOW: byte-equality apparatus left without disposition | **ACCEPTED** | master §7.4: repurposed as the semantic-hash comparator's capture feed; FD-9 closes against the new invariant |
| 16 | D-1 HIGH: gate table columns vs intro promise | **ACCEPTED-modified** | intro rewritten: sequence IS the precondition graph; live-evidence column named as the test column |
| 17 | D-2 HIGH: "five §7.4 roles" dangling; names absent from package | **ACCEPTED** | safety §7 now names all five roles + grant intent, cited to TA v0.11 §7.4 |
| 18 | D-3/D-4/D-5 MED: PB-4 brief unlocated; NO-LEAKAGE arms unenumerated; stale self-check bullet 11 + NCD unexpanded | **ACCEPTED** (all) | §11 intro carries the brief path + lane/ruling glosses + vocabulary legend; TB-3 arms 1–4 labeled; bullet 11 updated; NCD expanded |
| 19 | D-6/D-7/D-8 LOW: unglossed corpus IDs; C-classes used before pointer; authority-today wrinkle | **ACCEPTED** (all) | §11 legend covers FD/NCD/HS/ANTHROPIC-key; TB-2 carries the §5 pointer; self-check bullet 1 states the authority chain today explicitly |

## §3 — What this record qualifies

Per GIP §L.7, this pass qualifies the v0.12 package (as fixed) to serve as
the source material for `PARIPRASHNA_ARCHITECTURE_v1_0` at DRAFT_PENDING_REDTEAM
→ v1.0-RC. Two decisions remain OPEN for the native (NCD-9, NCD-10); neither
blocks authoring — both are Gate-1-adjacent and are carried in the decision
register as open rows.

*End RED_TEAM_G0 v1.0.*
