---
artifact: PG2_LANE_M-1
lane: M-1 — ADVERSARIAL META-AUDIT of PG-1
wave: PG-2 Diagnostic
role: the party that does NOT want the wave to be green (ADJUDICATOR_CHARGE governing principle)
run_by: Claude Code (Opus 4.8, 1M) — pg2/M-1 isolated worktree
date: 2026-07-19
audited_versions (sha256, per BIND_PG-2 B-6):
  - REPORT_PG-1.md = e7a4c2d6...
  - PARIPRASHNA_GROUNDING_AUDIT_REPORT_v1_0.md = 0d33df3f...
  - RETRIEVAL_SYSTEM_TRUTH_v1_0.md = 5b9ba1a8...
---

# PG-2 Lane M-1 — Adversarial Meta-Audit of PG-1

## ⬛ TOP-LINE VERDICT

**PG-1's gate result is VALID.**

The GATE GREEN stands. I attacked it as hard as the charge demands — the single
most consequential check (item 2, the G.1 addendum) was probed for backward
causality and content fabrication and came back **fully clean**. Every integrity
assertion survives independent re-derivation from primary DB/git/file evidence, not
from re-reading PG-1's prose. I found six correction-worthy defects (below), but
**none of them voids the gate**: they are versioning/hygiene/citation defects in the
sealed synthesis report, correctable in place, not integrity failures in the audit
itself.

I never left `/Users/Dev/Vibe-Coding/Apps/Madhav-pg2-M-1`.

---

## Per-item verdicts

### Item 1 — the 87/98 discrepancy — RESOLVED (defect confirmed, non-voiding)
- `pg1_findings.jsonl` has **98 lines**. The 12 primary lanes sum to **exactly 87**
  (C1=12,C2=8,C3=6,D1=4,D2=2,D3=4,O1=6,Q1=12,R1=11,R2=10,R3=7,S1=5); the +11 Z-1
  reconciliation addendum brings it to 98.
- The report's "87" is a **pre-addendum synthesis snapshot**. It is asserted in ≥4
  places (frontmatter L6 + L17, body L25, L122, L424) while the file it cites now
  has 98 lines. The **raw jsonl (98) is authoritative** for the artifact set; the
  report's 87 is stale-but-explained.
- **Critical count:** report §3 (L126) states "critical | 5", but **6** critical
  findings exist (D3-0004, Q1-0001, Q1-0007, Q1-0012, C2-0001, C2-0008) — two
  serialization styles (spaced vs unspaced JSON) masked the true count. Note the
  brief's specific hypothesis ("Q1-0007 omitted from the count") is slightly off:
  Q1-0007 IS named in §3's examples — the §3 example list actually enumerates all
  **six** IDs while the prose count says five. It is an **internal contradiction**
  (5 stated vs 6 listed), not an omission.
- **Correction needed:** yes — a dated note fixing the count to 98 and critical to 6.

### Item 2 — THE G.1 ADDENDUM (most important) — RESOLVED, ADDENDUM GENUINE
- **Causality provably forward.** Report = one immutable commit `6336c218`
  @06:56:25 (435 insertions, single file), **never modified after**. Addendum =
  commit `75b42b5a` @07:04:58 touching **only** the two jsonl files (+11 each), the
  report untouched. The report therefore **could not** have been retro-edited to
  justify the gate. Backward-causality hypothesis **REFUTED**.
- **All 11 rows verified.** The 8 evidence-bearing rows (A15,A18,A21,A23,A24,A25,
  A30,A32) each cite a specific report §1 table line (55,58,61,63,64,70,72) and
  quote it **verbatim** modulo stripped markdown. The 3 empty-evidence rows
  (A13,A16,A31) are honest `unverifiable`/"NOT AUDITED"/"STRUCK" and map exactly to
  the report table entries at L53/L56/L71.
- **Verdict:** the addendum is a legitimate machine-readability back-fill of
  analysis the report already contained — **not fabricated coverage**. The gate is
  **NOT void** on G.1 grounds. (Soft point: G.1 greens partly on 3 honestly-
  not-audited assumptions being tagged — mechanical, but transparently disclosed in
  §1's "29 of 32 received a verdict; 3 NOT audited". Honest under-coverage, not gaming.)

### Item 3 — protocol deviations, per-finding impact — RESOLVED (none compromise a finding)
- (a) **Shared checkout** → one commit race (`9216bc84` = R-1+D-3), scope-warden
  false-positive on R-1, resolved by fresh-context Adjudicator + conductor
  reconciliation. My independent view: genuinely a **commit-hygiene** issue, not a
  content-reliability one; no cross-lane authorship, and every finding I spot-checked
  re-derives cleanly from primary source.
- (b) **D-3 rode inside R-1's commit** → does NOT weaken NO-LEAKAGE: I re-derived
  D3-0004 directly from the live DB, independent of any commit boundary.
- (c) **Branch cut from local main:** `9c358819` (unrelated, touches CLAUDE.md) IS
  in `pg1/wave` ancestry and NOT in `origin/main` → PR #613 **genuinely carries
  contamination**. But it is disclosed (REPORT deviation #2) and is **outside PG-1's
  own commit range** (predates fork `e58e19ce`). Real hygiene problem, adequately
  disclosed, non-voiding.
- (d) **Mid-wave G.9 change** (diff from fork point, not origin/main): **legitimate
  bug fix**, not goalpost-moving. `9c358819` is provably outside PG-1's authored
  commits, so an origin/main diff would falsely attribute it to PG-1. I independently
  ran `git diff e58e19ce^..pg1/wave` = **42 files, ALL under 00_ARCHITECTURE, ZERO
  forbidden paths** — the underlying G.9 property is genuinely TRUE regardless of base.

### Item 4 — 10 independent spot-verifications — 10/10 HOLD (8 exact, 2 temporal drift, 1 imprecision)
| # | Finding | Method | Result |
|---|---|---|---|
| 1 | D3-0004 NO-LEAKAGE (critical) | DB roles+grants | HOLDS, understated (only amjis_app; full CRUD+TRUNCATE on both ledger+calibration) |
| 2 | Q1-0001 conv store empty | DB | conversation_messages=0 HOLDS; conversations=**1** (report said 0) — drift |
| 3 | D3-0003/F-25p two ledgers | DB | mimamsa_predictions=384, mcp_predictions=0 — EXACT |
| 4 | D2-0002/F-25o dead cost schema | DB | cost_reports=0, reconciliation=0 HOLD; llm_usage_events=**1** (said 0) — drift |
| 5 | A-08/D1 parts_json blob schema | DB | 7-col schema + no message_parts table — EXACT |
| 6 | F-25u chart_facts divergence | DB | core divergence HOLDS; "unstable across probes" IMPRECISE (see item 6) |
| 7 | R1-0002/F-25i census=120 | file | server.ts:522 `REGISTERED_TOOL_COUNT = 120` — EXACT |
| 8 | C1-0012/F-25h stale parity comment | file | route.ts=1030 lines, comment cites 1373-1475 — EXACT |
| 9 | C2-0001 planner/shim NO | file | runPlanner@436, PlannerFault→422@446 — EXACT |
| 10 | C3-0001 classifyChatError dead | grep | only its own def file, zero importers — EXACT |

No exaggeration found in any of the 10. The two `=0`→`=1` drifts and F-25u's framing
are the only imprecisions; none is load-bearing.

### Item 5 — G.4's qualified-GREEN, re-assessed — RESOLVED (sound, honestly disclosed)
R-2 executed **35 of 139** tools (~25%, single chart, mostly legacy). The assertion's
literal "EVERY capability" is unmet (104 never executed). But the integrity property
("no silent omissions") **is** met — the 35/139 bound is disclosed repeatedly and
never presented as exhaustive — and the gate runner did the **opposite of
laundering**: it recorded the literal shortfall, named it the closest call, and
routed it to native override (§3). **I concur with the qualified-GREEN.** My only
critique: a literally-unmet-but-honestly-disclosed integrity assertion would be more
precisely a "YELLOW/native-decision" than "GREEN"; within the binary vocabulary and
given full disclosure it is within bounds. Not gate-voiding.

### Item 6 — uncited prior work — PARTIALLY RESOLVED (pattern extends, not universal)
- **chart_facts (F-25u): confirmed uncited prior art.** `ABHINANDAN_POST_REGEN_DATA_AUDIT_v1_0.md`
  (2026-06-28, three weeks prior) already reported chart_facts at 130,212 vs canonical
  27,554, **diagnosed** it as stale multi-build residue / idempotency violation with
  build_id evidence, and specifically flagged native chart `482012f1` as carrying "5
  distinct build_ids... stale multi-build residue." PG-1's F-25u called the divergence
  "undiagnosed." PG-1 cited none of it. This **extends the §0.2 pattern.**
- **NO-LEAKAGE and PITR: clean.** The repo "leakage" hits are a different concept
  (interpretive/layer leakage, chart contamination); the DB-role NO-LEAKAGE design is
  in the PARIPRASHNA target arch D-3 correctly audited; PITR hits were incidental. No
  genuine uncited prior art on these two.
- So the failure is real and recurs on a high-consequence topic, but is **not a
  universal lane-wide pattern**.

### Item 7 — governance exit codes — RESOLVED (reproduced exactly)
Independently re-ran both from my worktree:
- `drift_detector.py` → **exit 3, 219 findings**; zero PG-1-path hits in output.
- `schema_validator.py` → **exit 3, 35 violations**; zero PG-1-path hits.
Both match REPORT_PG-1 L175/L178 exactly. PG-1's "pre-existing, zero touch PG-1
paths" claim is **VERIFIED**. (drift_detector wrote an adhoc report into
`00_ARCHITECTURE/drift_reports/`; I removed only the session-generated file and
restored all tracked reports — worktree left clean.)

### Item 8 — was a MEMO_PG-1 needed? — RESOLVED (no; correctly)
No ESCALATION_POLICY §2 halt-class event occurred. The initial G.1 RED was a
**non-integrity** mechanical assertion (integrity set = G.2/G.4/G.5/G.8/G.9), fixed
same-session by the legitimate reconciliation verified in item 2. G.4 was ruled
GREEN (qualified) → §3 async native-disposition, not §2 halt. No doctrine question,
no PARK, no circuit-breaker trip. The item-8 hint's contingency ("if the addendum is
questionable, that is a circuit-breaker-class event") **does not fire, because item
2 came back clean.** Absence of a MEMO is correct.

---

## The six defects I found (all correction-worthy, none gate-voiding)
1. Sealed report says "87 findings" in ≥4 places; file has 98 (stale post-addendum count).
2. Report §3 says "critical | 5"; 6 exist and its own §3 examples list all six (internal contradiction).
3. F-25u's "unstable across probes" is a chart-scoped-vs-whole-table artifact (138,519 = Abhisek alone; 276,206 = both charts; 138,519+137,687=276,206). The real divergence (138,519 vs canonical 27,554 = 5.03x) is stable.
4. F-25u fails to cite `ABHINANDAN_POST_REGEN_DATA_AUDIT_v1_0.md`, which had already diagnosed the divergence.
5. PR #613 carries the `9c358819` contamination (disclosed, outside PG-1's range; reconcile at merge).
6. Minor temporal DB drift: report's `conversations = 0` and `llm_usage_events = 0` are now `= 1` each (immaterial to any verdict).

These are **Z-2's corrective scope** (report-in-place fixes), not a basis to reopen
the gate.

## Confidence
High on all 8 items. Every claim above was independently re-derived from the live DB,
git history, or the working-tree files — not read-and-repeated from PG-1's artifacts.

*End of PG2_LANE_M-1 — adversarial meta-audit, 2026-07-19.*
