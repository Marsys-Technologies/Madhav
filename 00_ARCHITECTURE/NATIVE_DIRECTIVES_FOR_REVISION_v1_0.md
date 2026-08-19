---
artifact: NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md
version: 1.0
status: LIVING
role: >
  Authoritative log of native-issued directives that shape the governance
  rebuild (Step 0 → Step 15). Each directive is issued by the native during
  the rebuild, captures intent that goes beyond what the grounding audit and
  Step-1 critique already surface, and names the specific downstream step(s)
  responsible for implementing it. A directive is "open" until every step
  named in its consumption matrix has closed with the directive verified
  as addressed.
schema: >
  §1 Directive Log has one entry per directive. Each entry carries: stable
  ID (ND.N), issued_on date, status (open | addressed | partially_addressed
  | withdrawn), native statement (verbatim or near-verbatim), interpretation
  (editorial paraphrase for implementation clarity), scope (what surfaces
  it governs), and consumption matrix (step → obligation → verification).
  §2 Step-Consumption Matrix is the inverse view — each step lists the
  directive IDs it must close.
updated_at: 2026-08-19 (ND.2 appended — NCD-10 formalization route; directive governs native-self health-crisis/mental-health readings; folds into next MP revision per §3.10.A(d); session PARIPRASHNA-G0-CLOSE-2026-08-19). Prior: 2026-04-24 (ND.1 global status flipped `open` → `addressed` at STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION close per its consumption-matrix close condition; all six per-step verifications Steps 2/3/4/5A/6/7 confirmed; pointer to DRIFT_REPORT_STEP_7_v1_0.md + SESSION_LOG STEP_7 entry recorded below). Prior: 2026-04-23 (issued during STEP_1_MACRO_PLAN_CRITIQUE_AMENDMENT).
consumers:
  - Step 2 (revision spec)
  - Step 3 (rewrite)
  - Step 4 (red-team)
  - Step 5A (architecture refresh)
  - Step 6 (governance integrity protocol design)
  - Step 7 (governance integrity implementation)
close_rule: >
  No step named in a directive's consumption matrix may be marked `completed`
  in STEP_LEDGER until its obligation for that directive is verifiably
  addressed. Step close-criteria have been amended to include each applicable
  directive as a discrete checklist item.
---

# NATIVE DIRECTIVES FOR REVISION v1.0

## §0 — Purpose

The grounding audit (GROUNDING_AUDIT_v1_0) and the Step 1 critique (MACRO_PLAN_CRITIQUE_v1_0) capture **structural defects** — things the documents fail to say or say inconsistently. They do not capture **native intent** — specific convictions the native holds about how the project should be governed that may or may not be visible in existing artifacts.

This artifact is the native-intent channel. Its entries are issued during the rebuild, indexed by stable IDs, bound to the specific steps that implement them, and close-criteria-enforced so no step can silently drop one.

This artifact is LIVING: additional directives may be appended between rebuild steps. Each new directive adds a row to the consumption matrix and may amend affected step briefs. Directives are never deleted once issued — if withdrawn, they are marked `withdrawn` with rationale.

---

## §1 — Directive Log

### ND.1 — Mirror Discipline as a First-Class Governance Principle

- **Stable ID:** `ND.1`
- **Issued on:** 2026-04-23
- **Issued during:** STEP_1_MACRO_PLAN_CRITIQUE_AMENDMENT (closed after Step 1, before Step 2 opens)
- **Status:** **`RETIRED`** (flipped from `addressed` → `RETIRED` on 2026-05-27 per native directive — Gemini collaboration declared inactive; mirror discipline retired across 5 surfaces in atomic PR `0b.3 retire Gemini mirror-discipline governance`. Historical `addressed` close evidence preserved below for audit trail.) Previously: `addressed` 2026-04-24 at STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION close; all six per-step verifications — Steps 2, 3, 4, 5A, 6, 7 — confirmed; Step 7 implementation evidence: `mirror_enforcer.py` exit 0 against full MP.1–MP.8 inventory per `00_ARCHITECTURE/mirror_reports/MIRROR_REPORT_STEP_7_POST_REAUTHOR.md`; `CANONICAL_ARTIFACTS_v1_0.md §2` carries MP.1–MP.8 with per-pair `mirror_obligations` populated; `.geminirules` and `.gemini/project_state.md` re-authored to adapted parity + Asymmetries sections; `DISAGREEMENT_REGISTER_v1_0.md` class `DIS.class.mirror_desync` registered; `00_ARCHITECTURE/drift_reports/DRIFT_REPORT_STEP_7_v1_0.md` and SESSION_LOG STEP_7 entry record the flip.
- **Severity:** equivalent to a CRITICAL finding in the critique; addressed in Step 2 spec, enacted in Step 3 rewrite, verified in Step 4 red-team, inventoried in Step 5A, designed in Step 6, implemented in Step 7.

**Native statement (verbatim):**

> "It would be appropriate to update or rebuild the corresponding Gemini files every time we do the Claude files. Is that a good point — and I'll go further to say that whatever CLAUDE.md has which is as per the configuration of Claude, the mirrored adapted version should be in Gemini's respective file as per Gemini construct — and not limited to just CLAUDE.md but similarly other files which have corresponding Gemini references."

**Interpretation (for implementation clarity):**

Mirror discipline is a first-class governance principle, not an operational afterthought. Its three load-bearing claims are:

1. **Bidirectional obligation.** Every Claude-side governance file that has a Gemini-side counterpart MUST be kept in continuous semantic parity with its counterpart. Any change on the Claude side triggers a mirror update on the Gemini side in the same session. Symmetrically, any change on the Gemini side triggers a mirror update on the Claude side in the same session.
2. **Adapted parity, not byte-identity.** The mirror is *semantically* equivalent, not *textually* identical. CLAUDE.md speaks in Claude's conventions (`<system-reminder>`-style phrasing, Claude-Code-anchored norms, Claude-tool expectations). `.geminirules` and `.gemini/project_state.md` speak in Gemini's conventions (Gemini-rules idiom, Gemini-tool expectations). Each mirror is adapted to its target agent's construct while preserving the meaning.
3. **Scope is not limited to CLAUDE.md.** The principle extends to every governance surface that has a Gemini-side reference or counterpart. This includes (non-exhaustively): CLAUDE.md ↔ `.geminirules` / `.gemini/project_state.md`; MACRO_PLAN ↔ any Gemini-side macro-plan reference; PHASE_B_PLAN ↔ any Gemini-side phase reference; FILE_REGISTRY ↔ any Gemini-side canonical-path block; GOVERNANCE_STACK ↔ any Gemini-side governance reference; SESSION_LOG ↔ any Gemini-side session pointer. The precise inventory is the subject of Step 5A (high-level acknowledgment) and Step 7 (CANONICAL_ARTIFACTS as the authoritative list with explicit mirror-obligation columns).

**Scope (what surfaces this governs):**

- Every file in `00_ARCHITECTURE/` that is referenced by, or referenced from, any Gemini-side file under `.gemini/` or at root level starting with `.gemini`.
- The two root-level Gemini files: `.geminirules` and `.gemini/project_state.md`.
- Any future Gemini-side artifact introduced during the rebuild.
- Forward-looking: if a third agent is admitted (per MPC.13.4 fix direction), the mirror discipline extends to that agent's governance-surface counterparts.

**Asymmetries to preserve (not defects):**

- Claude-side files may contain Claude-specific constructs (e.g., Claude Code hooks, MCP references, skills) that have no Gemini equivalent. The mirror does not synthesize fake Gemini equivalents. Instead, the mirror declares the asymmetry explicitly (e.g., `.geminirules` contains a "Claude-only surfaces" section documenting what exists on the Claude side without a Gemini mirror, and why).
- Gemini-side files may contain Gemini-specific constructs (e.g., Gemini-specific rules idiom) that have no Claude equivalent. Same treatment in reverse.
- The mirror principle is *semantic parity of governance content*, not *feature parity of agent capabilities*.

**Consumption matrix:**

| Step | Obligation | Verification (new close-criterion) |
|------|-----------|------------------------------------|
| 2 — Revision Spec | Revision spec must direct Step 3 to add mirror discipline as a first-class axis of the new Macro Plan's System Integrity Substrate section, with the three load-bearing claims above stated explicitly. Spec also directs Step 5 cross-surface impact list to name every mirror pair. | Spec §3 (new sections) and §5 (cross-surface impact) both contain the mirror-discipline entry. Spec §7 Finding Coverage binds ND.1 to the MPC.14.2 and MPC.13.1 critique findings. |
| 3 — Rewrite | MP rewrite must contain a subsection in the System Integrity Substrate section titled "Mirror Discipline" stating the three claims. MP changelog entry names ND.1. | Subsection present with verbatim "semantic parity of governance content, not feature parity of agent capabilities" phrasing or equivalent. |
| 4 — Red-team | T.2 test extended to verify ND.1 is addressed as the spec committed. T.6 ambiguity test verifies the "adapted, not byte-identical" claim admits only one good-faith reading. | §1 Verdict explicitly reports ND.1 addressed status; §3 Findings include at least one ND.1-linked entry (FIX / WARN / OK). |
| 5A — Architecture refresh | v2.2 §D.11 (Multi-Agent Collaboration workstream) must enumerate the mirror-pair inventory at a summary level — names every mirror pair and flags which are authoritative. Step 5A's eyeball mirror check in §5 discipline rules is upgraded from "all five surfaces name v2.2" to "all five surfaces name v2.2 AND Gemini-side counterparts reflect the same semantic content adapted to Gemini's construct." | v2.2 §D.11 contains the mirror-pair inventory and explicit statement of the adapted-parity principle. |
| 6 — Governance Integrity Protocol Design | §J Mirror enforcer spec must specify enforcement over the full mirror-pair inventory, not just CLAUDE.md ↔ `.geminirules`. §K multi-agent disagreement protocol must account for mirror-desync as a disagreement class. §N finding coverage adds ND.1 as an explicit input alongside GA.N findings. | §J enumerates the full inventory with per-pair enforcement rules; §K mirror-desync is a listed disagreement class; §N has an ND.1 row. |
| 7 — Governance Integrity Implementation | `mirror_enforcer.py` implementation runs against the full mirror-pair inventory declared in CANONICAL_ARTIFACTS. CANONICAL_ARTIFACTS_v1_0.md carries a `mirror_obligations` column declaring the Gemini counterpart (if any) for every canonical artifact. `.geminirules` and `.gemini/project_state.md` are re-authored in this step to semantic parity with their Claude counterparts. Any asymmetry is documented in an "Asymmetries" section in each Gemini-side file. | `mirror_enforcer.py` exits 0 against the inventory; CANONICAL_ARTIFACTS has the `mirror_obligations` column populated; Gemini-side files each have an "Asymmetries" section or an explicit declaration of no asymmetries. |

**Relationship to Step 1 critique findings:**

- Implements **MPC.14.2** (HIGH) — "No mention of mirror discipline (CLAUDE.md, `.geminirules`, `.gemini/project_state.md`)."
- Implements **MPC.13.1** (HIGH) — "MP contains zero mentions of Gemini."
- Extends beyond both findings by promoting the principle to substrate-level parity with the Learning Layer, per the native directive's strong form.
- Does not conflict with any other finding; compounds favorably with MPC.14.1 (drift-prevention as a first-class axis) and MPC.14.7 (substrate parity).

**Close condition for ND.1:**

Directive status flips from `open` to `addressed` only after Step 7 closes with all six per-step verifications above confirmed. Partial closure (e.g., Steps 2–5A done but Steps 6–7 pending) is recorded as `partially_addressed`. A partial-close state does not unblock the next step; the next step still must verify its own obligation.

**Status flipped at Step 7 close (2026-04-24):** all six per-step obligations verified addressed. ND.1 global status: **`addressed`**. Evidence:
- Step 2 (spec): `MACRO_PLAN_REVISION_SPEC_v1_0.md §3.3 §IS.2 + §5.2 + §7.16`.
- Step 3 (rewrite): `MACRO_PLAN_v2_0.md §IS.2 Mirror Discipline` + changelog entry.
- Step 4 (red-team): `MACRO_PLAN_REDTEAM_v1_0.md §1 + §3` — T.7 PASS.
- Step 5A (architecture): `PROJECT_ARCHITECTURE_v2_2.md §D.11.1 + §D.11.2` (MP.1–MP.8 inventory).
- Step 6 (design): `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §J + §K.2 + §E + §N.2 + §J.7` (ND.1 verbatim citation).
- Step 7 (implementation): `CANONICAL_ARTIFACTS_v1_0.md §2` (machine-readable MP.1–MP.8); `platform/scripts/governance/mirror_enforcer.py` exit 0 against full inventory (`mirror_reports/MIRROR_REPORT_STEP_7_POST_REAUTHOR.md`); `.geminirules` + `.gemini/project_state.md` re-authored to adapted parity with explicit Asymmetries sections; `DISAGREEMENT_REGISTER_v1_0.md` carries class `DIS.class.mirror_desync` with forbidden-silent-overwrite rule.

Pointer to the closing SESSION_LOG entry + DRIFT_REPORT: see `SESSION_LOG.md` STEP_7_GOVERNANCE_INTEGRITY_IMPLEMENTATION entry dated 2026-04-24 and `00_ARCHITECTURE/drift_reports/DRIFT_REPORT_STEP_7_v1_0.md`.

---

### ND.2 — Native-Self Interstitial for Health-Crisis / Mental-Health Readings

- **Stable ID:** `ND.2`
- **Issued on:** 2026-08-18
- **Issued during:** PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5) — NCD-4 + NCD-10 rulings
- **Logged by:** PARIPRASHNA-G0-CLOSE-2026-08-19 (session PB-3-Bot, per NCD-10 binding)
- **Status:** **`OPEN`** — folds into the next natural MP revision per §3.10.A(d)
- **Severity:** Policy relaxation for the native's own chart only; no safety impact on any cohort subject

**Native statement (verbatim, NCD-4 ruling 2026-08-18):**

> "For the NATIVE'S OWN chart only: health-crisis and mental-health readings use a self-acknowledged interstitial in place of MP §3.5.C's seal + double-red-team + sign-off ceremony. Cohort subjects always receive the full HS-3 path. Folds into the next natural MP revision per §3.10.A(d)."

**Background (NCD-4):** MP §3.5.C requires a seal + double-red-team + sign-off ceremony before any health-crisis or mental-health reading is served. The native ruled (NCD-4, 2026-08-18) that for their own chart — where the native is both subject and informed operator — a self-acknowledged interstitial (pop-up/gate acknowledging sensitivity before proceeding) satisfies the protective intent of §3.5.C without the full ceremony overhead. This relaxation does NOT extend to any cohort subject; cohort subjects always receive the complete HS-3 path.

**NCD-10 formalization route:** The native chose ND directive (over §3.10.B MP amendment) so the relaxation is machine-readable, version-tracked, and folds cleanly into the next MP revision (§3.10.A(d)) rather than patch-amending the current MP in place.

**Interpretation (for implementation clarity):**

1. **Native-self scope only.** The interstitial substitution applies exclusively to readings for `chart_id = 482012f1-710e-4a25-994a-93821f5871aa` (Abhisek Mohanty, the native). Any other chart_id — including any future cohort subject — triggers the full §3.5.C ceremony path, no exception.
2. **Interstitial content.** The interstitial must: (a) name the reading's sensitivity category (health-crisis / mental-health); (b) surface the disclosure tier that applies; (c) require explicit acknowledgment (not auto-dismissed) before the reading is served; (d) be logged (timestamp + acknowledgment token) in the same audit trail that would otherwise hold the ceremony record.
3. **No ceremony-component omission for cohort.** The ceremony overhead NCD-4 relaxes (double-red-team + sign-off) is waived ONLY for the native's own chart. Any implementation that routes cohort-chart readings through the interstitial path instead of the ceremony path is a defect.
4. **MP revision trigger.** When the MP next opens for a revision pass (§3.10.A(d) trigger), this directive's scope — specifically §3.5.C — is to be amended in place to carry the native-self / cohort-subject bifurcation as a named clause, at which point this ND.2 flips to `addressed`.

**Scope (what surfaces this governs):**

- `MACRO_PLAN_v2_0.md §3.5.C` (next revision: bifurcation clause)
- Any Paripraśna gate-spec or implementation that serves health-crisis / mental-health readings (G2+)
- `chart_subject_consent` schema (NCD-9, G1): the native's consent record must distinguish the interstitial path from the ceremony path so the audit trail is unambiguous

**Consumption matrix:**

| Surface / trigger | Obligation | Verification (close criterion) |
|---|---|---|
| Next MP revision (§3.10.A(d)) | §3.5.C amended to bifurcate native-self (interstitial) vs. cohort (full ceremony) | §3.5.C carries both clauses; cohort-path ceremony requirement unchanged and explicit |
| G2+ health/mental-health serving (Paripraśna) | Interstitial gate wired for native chart; ceremony gate wired for all other chart_ids | Fixture: native chart → interstitial, cohort chart → ceremony |
| Audit trail | Interstitial log record carries acknowledgment token + timestamp | Verification matrix row PPR-35 updated at relevant gate close |

---

## §2 — Step-Consumption Matrix (inverse view)

This is the rapid-lookup view for a session that opens a given step and needs to know which directives it is bound to.

| Step | Directive IDs to address | Close-criterion count added |
|------|-------------------------|----------------------------|
| 2 — Revision Spec | ND.1 | 1 (§6 list amended) |
| 3 — Rewrite | ND.1 | 1 |
| 4 — Red-team | ND.1 | 1 |
| 5A — Architecture refresh | ND.1 | 1 |
| 6 — Governance Integrity Design | ND.1 | 1 |
| 7 — Governance Integrity Implementation | ND.1 | 1 |
| 0, 1, 5, 8, 9, 10, 11, 12, 13, 14, 15 | (none currently) | — |
| Next MP revision (§3.10.A(d)) | ND.2 | 1 (§3.5.C bifurcation clause) |

When a new directive (ND.3, ...) is issued, it appends to §1 and amends this matrix.

---

## §3 — Issuance protocol (forward-looking)

Future directives are issued the same way ND.1 was:

1. Native issues the directive in session.
2. In-session, a new `ND.N` entry is appended to §1 with verbatim statement, interpretation, scope, consumption matrix, and close condition.
3. §2 matrix is updated.
4. Every affected step brief gets: (a) this artifact added to its §2 MUST-read inputs (if not already), (b) a new checklist item in §6 close criteria naming the specific ND.N obligation, (c) if the step's scope is materially expanded, a scope-boundary edit.
5. STEP_LEDGER is amended with a directive-tracking note.
6. SESSION_LOG appends an amendment entry.
7. If any step affected is already closed, the directive triggers a workflow amendment rather than a silent revision of a closed step — via a fresh session modeled on the Step 5A insertion pattern.

---

*End of NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md.*
