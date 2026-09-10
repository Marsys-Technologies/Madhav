---
artifact: SAFETY_PRIVACY_TENANCY_v0_1_PROPOSAL
canonical_id: PARIPRASHNA_SAFETY_PRIVACY_TENANCY
version: 0.1
status: PROPOSAL — Phase-1 output, awaiting native ratification (not canonical; authorizes no code)
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18)
date: 2026-08-18
authoritative_side: claude
relates_to:
  - MACRO_PLAN_v2_0.md §3.5 (Ethical Framework — the AUTHORITY this file translates, never overrides)
  - PROJECT_ARCHITECTURE_v2_2.md §K protection clauses, §D.6, §J.3–J.5
  - 00_ARCHITECTURE/briefs/pariprashna_v012/PARIPRASHNA_V012_PHASE1_REVIEW_v0_1.md §8
changelog:
  - "0.1 (2026-08-18): initial proposal."
---

# Safety, Privacy, Consent, and Tenancy — Ethical Framework as Runtime Architecture

## §0 — The finding that motivates this file

MP §3.5 is binding governance. **None of it is enforced at the serving layer
today.** Verified 2026-08-18 (STATIC_VERIFIED against HEAD dfbdfe620): the
`/api/pariprashna` route contains no safety classifier, no mortality/self-harm
output gate, no consent check beyond chart entitlement, no minor exclusion;
`ganita_ayurdaya_get` (longevity computation) is live on the 125-tool MCP
surface with no disclosure-class gate. While the only user is the native this
is a latent gap; the moment mission item 6 (research beyond the native)
admits a second subject, it is a violation of §3.5.D/§3.5.F. This file makes
the framework runtime-enforceable BEFORE that moment, per the mission's own
sequencing.

## §1 — The two axes, disentangled (resolves the D-15 conflation)

- **Register axis (D-15, ruled 2026-07-19):** one prose register, acharya-grade
  and reader-legible, for everyone. No quality tiers. UNCHANGED.
- **Disclosure-class axis (MP §3.5.B, binding):** `native_self` /
  `cohort_subject` / `acharya_reviewer` / `public` — who may receive which
  OUTPUT CLASSES, under which consent, with which redaction rights. This is an
  access-control and consent axis, not a prose-quality axis. Per-class
  enforcement notes: `acharya_reviewer` requires native consent before
  identifying data is shown, with identifier redaction honoring the subject's
  `anonymization_choice` enforced at serve time, not by convention;
  **`public` is FAIL-CLOSED — the class exists in the enum but serves nothing
  until the §3.9.B publication protocol is built** (declaring it now prevents
  the enum from inviting accidental use). One honest wrinkle recorded: the
  public class's mandated redaction/aggregation DOES change what is produced —
  that is §3.5.B's own requirement and is a consent/publication transformation,
  not the quality tier D-15 abolished; the two-axis naming rule below keeps
  this distinction speakable.

The TA's §13.4 "Open check" (an unverified paraphrase of "stated disclosure
tiers") is hereby closed with the source read: the Ethical Framework's tiers
are REAL and orthogonal to D-15. Naming rule to prevent re-conflation:
**"register" is never plural; "disclosure class" is never called a tier of
quality.** Both words appear in every future spec that touches either.

## §2 — Hard stops (MP §3.5.C → runtime controls)

| # | Rule (authority) | Runtime control (proposed) |
|---|---|---|
| HS-1 | **No date-of-death output — unqualified — for any subject under any disclosure class** (§3.5.C, carried verbatim; the "individualized" qualifier belongs only to the separate mortality-WINDOW clause, HS-4) | SafetyPolicyGate blocks at three points: (a) plan-time — mortality-window capabilities are excluded from plans for `query_class: sensitive/mortality` unless the aggregate-framing path is chosen; (b) synthesis-time — prompt policy forbids date-of-death composition; (c) pre-wire output scan — date-adjacent mortality phrasing detector on remedial/predictive/sensitive blocks. Violation = withhold block + honest gap ribbon + audit row. NEVER silent. |
| HS-2 | **No suicide-adjacent analysis/output, any class** (§3.5.C) | Query classifier routes to a fixed, calm, non-analytic response with support-resource framing; NO retrieval plan is built (nothing to leak); audit row; native notified for cohort subjects — **and that notification pathway is itself disclosed in the §3.5.D consent document** (a subject's crisis query reaching the researcher is a disclosure the subject must have accepted in advance). |
| HS-3 | **Health-crisis + mental-health output require double red-team AND native sign-off — two distinct controls, never collapsed — before leaving a session** (§3.5.C, §3.5.A.3, PA §D.6; red-team = adversarial critique passes per §IS.8, not an approval click) | Three-step serving path for these classes: (1) the reading is composed and SEALED-PENDING (persisted, not streamed beyond an acknowledgment); (2) **two independent adversarial review passes run against the sealed reading** (distinct models/contexts, prompted to refute grounding, calibration language, and framing), verdicts recorded on the receipt; (3) the sign-off affordance (native) releases it — a separate act, informed by the two passes. For the native's own chart: NCD-4 ruled the interstitial (deliberation pause) in place of steps 1–3; that relaxation's formalization route is NCD-10. |
| HS-4 | **Mortality-window output: double red-team AND aggregate-statistical framing only; individualized mortality windows disallowed** (§3.5.C + §3.5.A.3 — the double-red-team requirement applies to the mortality domain itself, not only to health-crisis/mental-health) | Two controls: (a) the permitted output shape for longevity-domain questions is period-quality and aggregate-statistical framing — `ganita_ayurdaya_get` results enter synthesis context only under this frame, tagged so the planner cannot select them for individualized windows; (b) any mortality-window output additionally rides the full HS-3 three-step path — seal-pending, two independent adversarial passes, then sign-off as a separate act — all recorded on the receipt. |

The `safety_decision` field of the AcharyaReadingReceipt records every
classification and action — a hard stop is auditable, never invisible (§N.8:
the gate is a detector; its firing is the earned signal).

**HS-5 — Reversibility (§3.5.A.6, previously untranslated).** Every output is
rescindable if calibration or grounding data reveals it was unfounded.
Runtime shape: a receipt-linked **retraction record** (what was retracted,
why, evidence ref, when) appended — never edited into — the sealed reading
(its append-only correction mechanism is the vehicle); recipient notification
for cohort/acharya disclosure classes; a retraction note on any prediction
ledger row the reading fed. Retraction is a governance act (native-initiated
or red-team-initiated), not an automated one.

**HS-6 — Predictive-output red-team cadence (§3.5.A.5, previously
untranslated).** Served readings whose receipts carry `prediction_candidates`
are sampled into the standing red-team cadence (§IS.8 — every third session /
phase close): the sample's receipts + prose are reviewed adversarially, and
findings enter the normal fix-log. This is the runtime hook that makes "every
predictive output is subject to the red-team cadence" a detector-backed
claim rather than prose.

## §3 — SafetyPolicyGate — placement and shape

```
NormalizedQuery → EntitlementDecision → **SafetyPolicyDecision** → ScopeTuple → plan …
                                              │
   {classes_detected[], disclosure_class, consent_state, subject_age_check,
    action: proceed | reframe | hard_stop | seal_pending_signoff}
```

- Runs BEFORE planning (a blocked class must never build a retrieval plan).
- Deterministic-first (§N.4): keyword/domain classifier + capability-class
  rules; an LLM assist may RAISE severity, never lower it.
- Output-side twin: the pre-wire scan extends the existing register-leak lint
  pass (same infrastructure, new pattern classes) — HS-1 phrasing, entitlement
  scan (chart_ids/facts not belonging to the caller), per TA v0.11 §14A.1.
- Applies to ALL THREE doors. On raw MCP tools, where no prose crosses our
  boundary, enforcement is capability-level: sensitive-class tools carry
  disclosure-class requirements in the registry and are excluded from
  `consult`-profile projections entirely.

## §4 — Consent, subjects, and exclusions (§3.5.D/§3.5.F → schema)

- **`chart_subject_consent`** (new table, proposed — adoption is NCD-9):
  chart_id · subject_kind (native_self | cohort | test) · consent_document_ref
  · granted_at · withdrawn_at · redaction_requests · anonymization_choice
  (DEFAULT anonymous, per §3.5.D.3 — attribution only by active election) ·
  vulnerable_exclusion_flag · verified_deletion_at. **`native_self` is defined
  strictly: a chart whose SUBJECT is the native** (plus the §3.5.F
  minor-guardian carve-out). Any other chart — spouse, colleague, friend —
  is a non-native subject and serves NO L2+ output without a consent row
  (§3.5.A.4): the entitlement layer refuses, and the refusal is a designed
  state, not an error. Withdrawal triggers the §3.5.D verified-deletion
  workflow (L2+ corpus destruction — compatible with §N.3 delete-then-insert;
  receipt snapshots resolved by subject-scoped snapshot deletion with a
  tombstone hash so audit integrity survives content deletion). Deletion-scope
  disputes open a DISAGREEMENT_REGISTER entry (§3.5.D.2, carried verbatim).
  Subject access/export ships as a machine-readable JSON manifest + the
  sealed-reading renderings.
- **Excluded-subject register (§3.5.F, carried):** exclusions (minors,
  consent-incapacity) are LOGGED — no corpus produced, no analysis performed —
  in their own register, so the exclusion discipline is itself auditable.
- **Minors (§3.5.F):** trivially computable — `birth_date` is the chart's own
  primary datum. A chart whose subject is <18 is servable ONLY to the native
  in a parent/guardian capacity and NEVER enters the cohort; enforced at
  entitlement resolution, not convention.
- **Vulnerable-subject exclusion:** a consent-table flag set at intake; no
  automated detection pretense (§N.8 — we do not claim a detector we lack).

## §5 — Data classification and handling

| Class | Data | At rest | Leaves to LLM providers? | Retention |
|---|---|---|---|---|
| C1 sacred-personal | birth data, LEL life events, health/relationship content, conversation prose | Postgres, encrypted at rest (Cloud SQL default) — verify and STATE | YES, necessarily (synthesis context) → §6 controls | native-controlled; cohort: per consent doc |
| C2 derived | L1–L5 layer tables, envelopes, receipts | same | YES (evidence context) | rebuildable; snapshots per subject consent |
| C3 predictive | prediction ledger, outcomes, Brier, calibration | same | **NO — NO-LEAKAGE forbids serving-path access; provider exposure = leakage by proxy** | permanent (research record) unless subject withdrawal |
| C4 operational | traces, model calls, costs, audit rows | same | no | bounded (state a number, Gate 1) |
| C5 credentials | keys, tokens | Secret Manager | no | rotation policy (CCD-004 already flags one rotation owed) |

**Rules:** C3 never enters a synthesis prompt (this is the NO-LEAKAGE
invariant restated as data classification — the four arms enforce it); audit
logs reference content by hash/id, never duplicate C1 bodies (safe-logging
rule); subject access/export = the sealed-reading export plus a per-subject
machine-readable data manifest (cheap: everything is chart_id-scoped).
**LEL post-hoc-edit discipline (§3.5.E, carried):** LEL entries are
timestamped at first entry; post-hoc edits are flagged in the audit trail —
who, when, what changed, rationale — the exact fields, verbatim from source.
**Incident response (ED.9 names "breach" as a failure mode):** Gate 1 ships a
one-page breach-response note — detection sources, containment steps
(credential rotation, session revocation), assessment, and the
subject-notification duty, which the §3.5.D consent document discloses up
front. Session revocation covers BOTH doors: Firebase session invalidation
and MCP key revocation, exercisable same-day.
**Audit-trail integrity:** `safety_decision` records, retraction records, and
consent-state transitions are written under an INSERT-only grant (part of the
§7 role migration) or hash-chained — a safety gate whose firing record is
editable under the serving credential is not "never invisible."

## §6 — Model-provider privacy posture (currently UNSTATED anywhere)

What leaves today (STATIC_VERIFIED): chart facts, signal text, conversation
history, summaries — C1/C2 — to Gemini (default), OpenAI-class, DeepSeek,
NVIDIA-hosted endpoints per the stack routing. Required before any cohort
subject (Gate 1 deliverable, mostly a documentation + configuration act):
per-provider rows stating retention, training-use posture, region; a
provider-allowlist per disclosure class (a cohort subject's C1 may be
restricted to providers with contractual no-training terms); redaction option
for direct identifiers (name; birth data is analytically load-bearing and
cannot be redacted — say so honestly in the consent document, §3.5.D item 1).

## §7 — Tenancy and DB enforcement

- Object-level authorization exists (`authorizeChartAccess`, per-capability
  chart entitlement) — STATIC_VERIFIED, and fail-closed per PG2-X4-0002.
- **Missing beneath it:** the single `amjis_app` credential (F-25q, arm-1) and
  no RLS. Proposal: the five TA v0.11 §7.4 roles as Gate-1 work —
  **`role_web_serve`** (SELECT layer tables, conv-store R/W, NO ledger
  INSERT/UPDATE, NO calibration write), **`role_orchestrator`** (build-path
  layer-table writes only), **`role_ledger_write`** (ledger + outcome +
  calibration writes; held ONLY by the out-of-process writer, arm-3),
  **`role_jobs`** (model_health, summaries, digests), **`role_sidecar`**
  (minimal compute-support read) — PLUS chart-scoped RLS
  policies on the C1/C3 tables keyed to a session-set `app.chart_context` —
  RLS is the depth layer that survives an application bug, exactly the class
  of defense the mission's consent obligations warrant. Rotation of `amjis_app`
  after role migration (pairs with CCD-004's flagged rotation).
- Cache isolation: SHA-256 chart-scoped keys + echo-back guard exist (F-20
  fix) — carried forward as a stated invariant with its regression test.

## §8 — Abuse cases (threat model, condensed)

| # | Abuse case | Path | Existing defense | Gap → control |
|---|---|---|---|---|
| A1 | Prompt injection via question or prior turns → plan manipulation | all doors | Zod-validated plan; chart_id never from text | prompt-structure containment (data-not-instruction delimiting); tool-sequence anomaly flag (TA §14A.1) |
| A2 | Injection via retrieved content (LEL text, classical corpus) → output manipulation | synthesis | none stated | retrieved-content provenance tagging; instruct-following scan on evidence blocks; register/entitlement output scan is the backstop |
| A3 | Cross-chart exfiltration ("compare me to chart X") | all doors | per-capability entitlement, fail-closed CHART_REQUIRED | answer-side entitlement scan (chart_ids/facts in output vs caller's grants) |
| A4 | Runaway spend via prashna_ask or deep-dive loops | MCP, portal | budget arbitration per tool; maxDuration | **NONE blocks a request** — per-user rate limit + per-turn/daily spend ceilings (Gate 1; F-25d) |
| A5 | Outcome leakage into generation (the mission-killing one) | serving | arm-2 runtime filter, arm-4 canary, leak guard on emitter | arm-1 DB roles + RLS (Gate 1); provider-exposure rule §5/C3 |
| A6 | Sensitive-class extraction from raw MCP tools (ayurdaya etc.) | raw MCP | profile gating only | capability disclosure-class requirements; sensitive tools off `consult`; §2 HS-4 framing rule |
| A7 | Stolen/replayed resume token or MCP key | transport | resume auth re-check per chart (built); Bearer keys | key rotation cadence; revocation list; abuse-rate alerting |
| A8 | A cohort subject's kin extracting the subject's data via a shared chart | portal | entitlement grants | consent-table redaction rights; disclosure-class enforcement per §1 |
| A9 | **The native (or any entitled user) creates a chart for a non-consenting adult** — spouse, colleague, public figure — and reads them without their knowledge. The highest-likelihood real-world abuse of any astrology instrument. | portal chart creation → L1 build → serving | none today (chart creation is ungated; §3.5.A.4 is unenforced) | the §4 consent rule: no L2+ serving without a `chart_subject_consent` row; `native_self` strictly defined (subject IS the native, or minor-guardian carve-out); build itself may proceed (L1 facts are computation) but INTERPRETIVE serving refuses in a designed, explained state |

Trust-boundary diagram: master review §6.3.

## §9 — Ratification asks

NCD-4 (hard-stop UX for the native's own chart — RULED: interstitial;
formalization route is NCD-10), NCD-5 (RLS — RULED: adopt), NCD-6
(provider-allowlist posture — RULED: document now, strict on first cohort
subject), NCD-9 (consent-schema adoption — RULED: adopt at G1), NCD-10 (NCD-4's
formalization route — RULED: ND directive). All in the master review's decision packet §13.

*End SAFETY_PRIVACY_TENANCY v0.1 PROPOSAL.*
