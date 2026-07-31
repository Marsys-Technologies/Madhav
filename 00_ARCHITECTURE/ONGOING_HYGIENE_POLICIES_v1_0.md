---
artifact: ONGOING_HYGIENE_POLICIES_v1_0.md
version: 1.0
status: CURRENT
produced_during: STEP_12_ONGOING_HYGIENE_POLICIES (Step 0 → Step 15 governance rebuild)
produced_on: 2026-04-24
authoritative_side: claude
role: >
  Institutionalized hygiene-rule set governing the MARSYS-JIS project's living governance
  surfaces. Prevents the kind of drift the grounding audit found (version disagreement,
  unarchived predecessors, scope leak, session-log gaps, stale canonical pointers) from
  re-accumulating between macro-phases. Each policy names the mechanism that enforces
  it: a validator check, a template field, a registry rule, or a documented human
  cadence. Referenced by every session-close checklist from Step 12 forward.
implements: >
  Step 12 brief §3 (§A–§J policy structure). Closes GA.12 (LEL v1.1 predecessor),
  GA.20 (scope-boundary enforcement at close-checklist layer; Step 7 closed at
  handshake layer), GA.21 (SESSION_LOG completeness). Extends Step 7 governance-
  integrity implementation by adding three schema_validator checks (scope_boundary,
  files_touched_completeness, learning_layer_stub) and closing Step 8 red-team
  findings F.1, F.2, F.3. Commits the per-mechanism Learning Layer N-override
  default (N=3, no override) per LEARNING_LAYER_SCAFFOLD_DECISION_v1_0 §5.4.
  References — does NOT duplicate — LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md
  (CLOSED; corpus-refresh cadence) and MAINTENANCE_SCHEDULE_v1_0.md (CLOSED;
  concrete 36-month calendar). Those artifacts govern the corpus-subject layer
  (varshphal, LEL bump, HEATMAP); this artifact governs the governance-artifact
  layer.
supersedes: >
  (None — first version.) Previously, hygiene rules were scattered across
  GOVERNANCE_STACK amendment logs, LIVING_PROJECT_MAINTENANCE_GUIDE, the
  Step 7 governance-integrity protocol §C axes, and ad-hoc SESSION_LOG notes.
  This artifact consolidates the governance-layer rules into a single surface
  with explicit enforcement-mechanism mapping.
mirror_obligations:
  claude_side: 00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md
  gemini_side: null
  mirror_mode: claude_only
  authoritative_side: claude
  asymmetries: >
    Claude-only policy artifact. Gemini-side sessions (if any produce governance
    surfaces) cite this file by reference from .geminirules collaboration section.
    No Gemini-side counterpart is required because the enforcing mechanisms
    (schema_validator.py extensions, CANONICAL_ARTIFACTS schema, SESSION_LOG_SCHEMA
    entry structure) are themselves Claude-side Claude-only infrastructure per
    CANONICAL_ARTIFACTS §2 MP.6 (GOVERNANCE_STACK) + MP.7 (SESSION_LOG) declarations.
consumers:
  - platform/scripts/governance/schema_validator.py — implements §C scope-boundary
    check, §D files-touched-completeness check, §G learning_layer_stub class
  - 00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md — declared_scope field validates
    against §C
  - 00_ARCHITECTURE/SESSION_CLOSE_TEMPLATE_v1_0.md — files_touched + known_residuals
    fields validate against §C, §D, and the §F exit-code-3 whitelist rule
  - 00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md — §A archival discipline binds
    supersession-path-declaration rule; §B binds the GA.12 closure
  - Every session-close checklist from Step 12 onward
changelog:
  - v1.0 amended in-place (2026-04-26, Madhav_BUILD_TRACKER_GCS_PERMISSIONS_FIX):
      Added §O "Operational setup (one-time per bucket)" sub-block — canonizes
      IAM + CORS bootstrap pattern after discovering the predecessor session's
      public-read + CORS steps did not take effect. Source: session
      Madhav_BUILD_TRACKER_GCS_PERMISSIONS_FIX.
  - v1.0 amended in-place (2026-04-26, Madhav_BUILD_TRACKER_INTEGRATION_v0_1):
      Added §O (Build-state serialization at session close) — integrates
      serialize_build_state.py into session-close discipline. Added §O row to §J
      implementation-actions index. See BUILD_TRACKER_DEPLOYMENT_NOTES.md §4.2.
  - v1.0 (2026-04-24, Step 12 of the Step 0 → Step 15 governance rebuild):
      Initial policy set. §A retain-in-place archival; §B LEL v1.1 one-time
      cleanup + standing predecessor-cleanup rule; §C scope-boundary close-check
      (GA.20 full-surface closure); §D SESSION_LOG completeness check (GA.21
      closure); §E Staleness Register (30-day + fingerprint-delta); §F CI/cron
      cadence with manual-fallback documentation; §G red-team cadence + learning
      layer stub validator class; §H quarterly governance pass; §I Macro Plan
      review triggers (absorbs WARN.2/5/7 explicit re-defer with PHASE_B_PLAN
      v1.0.3 amendment-cycle rationale); §J implementation-actions index; §K
      residual-disposition record (GA.12/20/21 + F.1/F.2/F.3 + Step 7/8/9/10/11
      carried items); §L finding-coverage table.
date: 2026-04-24
---

# ONGOING HYGIENE POLICIES v1.0
## MARSYS-JIS Project — Governance-Layer Hygiene Rule Set

*Produced in Step 12 of the Step 0 → Step 15 governance rebuild. Closes GA.12 + GA.20 + GA.21 and Step 8 red-team findings F.1 + F.2 + F.3. Reference point for every session-close checklist from this session forward.*

---

## §0 — How to read this artifact

Each policy section (§A–§J) carries four parts: **Policy** (the rule in prose), **Rationale** (what drift it prevents, citing GA.N / F.N / WARN.N where applicable), **Enforcement mechanism** (the script / template field / registry rule / documented human cadence that backs it), and **Failure mode** (what a violation looks like + what the enforcer does about it). §K records residual-finding disposition — every open finding at Step 12 open either closes here or is explicitly re-deferred with rationale, per brief §4's "no 'will revisit'" rule. §L is the finding-coverage audit table.

This file is governance-layer. Subject-layer corpus-refresh cadence (varshphal, LEL bump, HEATMAP refresh, dasha-transition deep-dives) is governed by `LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md` (CLOSED 2026-04-18) and `MAINTENANCE_SCHEDULE_v1_0.md` (CLOSED 2026-04-18). Those artifacts are referenced, not duplicated. When a conflict arises between a governance-layer rule here and a corpus-layer rule there, the governance rule takes precedence for the governance surface and the corpus rule takes precedence for the corpus surface — they operate on disjoint sets.

The `MACRO_PLAN_v2_0.md §IS.8` red-team cadence and `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §C.1–§C.6` six axes are the upstream substrate this artifact operationalizes. This artifact is not an alternative to them — it is the session-level operating layer that makes their axioms enforceable per-session.

---

## §A — Archival policy (SUPERSEDED artifacts)

### Policy

When a canonical artifact is version-bumped and its prior version becomes SUPERSEDED, the prior version **retains in place** at its original path with two surface changes:

1. A SUPERSEDED banner prepended as the first content line (above frontmatter body but not above the YAML fence): `> **SUPERSEDED <YYYY-MM-DD>** by `<successor-path>` at <session_id>. Content retained for audit trail; do not consume as CURRENT.`
2. Frontmatter `status` field flipped to `SUPERSEDED`; `superseded_by` field added pointing at the successor path; `superseded_on` date populated.

No move to an `archive/` subfolder. No deletion. The file remains grep-findable at its historical path so pointer-follow from old artifacts resolves cleanly in one hop (the banner routes the reader to the successor).

### Rationale

Moving SUPERSEDED files to `archive/` was considered but rejected. Every cross-reference in the corpus (from MACRO_PLAN_v1_0 → MP v2.0, MSR_v2_0 → v3.0, PROJECT_ARCHITECTURE_v2_1 → v2.2, FILE_REGISTRY_v1_0..v1_3 → v1.4, GOVERNANCE_INTEGRITY_PROTOCOL DRAFT → CURRENT, etc.) was authored with the historical path. Moving the file breaks the pointer; rewriting every pointer breaks B.12 (no retroactive edits to closed artifacts). Retain-in-place with a banner preserves both the audit trail and the pointer graph. The current behavior — observed throughout Steps 1–11 — is hereby canonized as policy.

### Enforcement mechanism

- **Detective (automatic).** `drift_detector.py` already flags a file whose frontmatter reads `status: SUPERSEDED` but whose body lacks the `> **SUPERSEDED` banner, and vice versa. This existing check (introduced at Step 7) is the §A enforcement.
- **Preventive (human).** The session that performs a version bump writes both surface changes (banner + frontmatter flip) in the same tool call as the successor creation. The session's `files_touched` must include both the new CURRENT path AND the SUPERSEDED predecessor path.

### Failure mode

An orphan SUPERSEDED file (frontmatter SUPERSEDED, no banner, OR banner without frontmatter SUPERSEDED) fires `drift_detector.py` finding `supersession_banner_mismatch` at MEDIUM severity. The next session that touches the file resolves it; if none does, the quarterly governance pass (§H) catches it.

---

## §B — Predecessor cleanup (GA.12 closure)

### Policy

One-time cleanup action performed at Step 12 close: `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_1.md` receives §A treatment (SUPERSEDED banner + frontmatter flip pointing at `LIFE_EVENT_LOG_v1_2.md`). This is the only predecessor in the corpus that lacks the banner at Step 12 open.

Standing rule: from Step 12 forward, every L1 / L2.5 / L3 / governance predecessor that has been version-bumped receives §A treatment in the same session as the bump. The quarterly governance pass (§H) scans for orphans.

### Rationale

GROUNDING_AUDIT_v1_0 §GA.12 (LOW, HYGIENE, owning_step=Step 11) named this file specifically. Step 11 deferred the cleanup to Step 12 per LL scaffold decision close notes. Resolving here closes GA.12 at the full-surface layer.

### Enforcement mechanism

- **One-time (this session).** The Step 12 close includes a SUPERSEDED banner + frontmatter flip on `LIFE_EVENT_LOG_v1_1.md` (pointing at `LIFE_EVENT_LOG_v1_2.md`).
- **Standing (forward).** §A enforcement applies. `drift_detector.py` scans for orphan-predecessor patterns at every session close.

### Failure mode

If the Step 12 close-checklist does not report `LIFE_EVENT_LOG_v1_1.md` in its `files_touched` list, Step 12 does not pass close. Forward: any L1/L2.5/L3/governance successor created without corresponding predecessor §A treatment fires `supersession_banner_mismatch` MEDIUM.

---

## §C — Scope-boundary enforcement (GA.20 full-surface closure)

### Policy

Every session's `session_close.files_touched` paths MUST each resolve to a `session_open.declared_scope.may_touch` glob, AND no path may resolve to `session_open.declared_scope.must_not_touch`. This is enforced at close — session cannot close if violated.

Scope declaration at open (already required per `SESSION_OPEN_TEMPLATE_v1_0.md §2`) is insufficient alone: a session could declare scope and then edit outside it. The close-checklist check is the complement that GA.20 requires.

### Rationale

Step 7 (governance integrity implementation) closed GA.20 at the handshake layer: sessions must declare scope at open, including a non-empty `must_not_touch`. GROUNDING_AUDIT_v1_0 §GA.20 explicitly names Step 7 AND Step 12 as owning steps — Step 7 addresses the declaration, Step 12 addresses the compliance check. This policy closes GA.20 at the compliance layer.

### Enforcement mechanism

- `platform/scripts/governance/schema_validator.py` gains a new check function `validate_scope_boundary(session_close, session_open)`:
  - For each path in `files_touched`:
    - Check membership in `declared_scope.may_touch` (glob match against each entry).
    - Check non-membership in `declared_scope.must_not_touch`.
  - Emit finding `scope_boundary_violation` at HIGH severity for each path that fails either check.
- Registered in `schemas/artifact_schemas.yaml` under the existing `session_close` class.
- Fires at every `schema_validator.py --session-close` invocation from Step 12 forward.

### Failure mode

A session that edits outside its declared scope fires `scope_boundary_violation` HIGH. The session cannot close. Remediation options: (a) amend `declared_scope` in a same-session directive-documented expansion and re-run the validator; (b) revert the out-of-scope edit; (c) halt and report to the native per GOVERNANCE_INTEGRITY_PROTOCOL §K disagreement protocol if the out-of-scope edit is load-bearing.

---

## §D — SESSION_LOG completeness (GA.21 closure)

### Policy

The `session_close.files_touched` list MUST equal the set of files whose fingerprints changed during the session window. Specifically: for every canonical artifact in `CANONICAL_ARTIFACTS_v1_0.md §1`, the observed fingerprint at session close is compared to the declared fingerprint at session open. Any artifact whose fingerprint rotated must appear in `files_touched`; any `files_touched` entry must have a rotated fingerprint or a documented why-no-rotation reason (e.g., file created this session has no prior fingerprint).

### Rationale

GROUNDING_AUDIT_v1_0 §GA.21 (LOW, SCOPE-CREEP, owning_step=Step 12): "No automated check that every artifact touched in a session has a corresponding SESSION_LOG entry. An artifact can be edited without its session being logged." Closes here.

### Enforcement mechanism

- `schema_validator.py` gains `validate_files_touched_completeness(session_close, canonical_artifacts)`:
  - Compute the fingerprint-delta set: `{canonical_id : declared_fp != observed_fp}`.
  - Compute the files_touched set: `{path : path in session_close.files_touched}`.
  - For each entry in the fingerprint-delta set, resolve its canonical_id's path and check membership in files_touched. Missing → finding `files_touched_incomplete` HIGH.
  - For each entry in files_touched, either (a) the path's fingerprint rotated this session, or (b) the path's `files_touched[i].reason` field reads `created_this_session` / `reviewed_not_modified` / `status_flag_only`. Neither → finding `files_touched_unjustified` MEDIUM.
- Registered in `schemas/artifact_schemas.yaml`.

### Failure mode

A session that modifies a canonical artifact without declaring it in files_touched fires `files_touched_incomplete` HIGH. Session cannot close. Remediation: amend files_touched to include the missing path + rerun the validator.

---

## §E — Staleness Register (30-day + fingerprint-delta)

### Policy

A CURRENT canonical artifact is **STALE-SUSPECT** when BOTH:
1. Its `last_verified_on` (per CANONICAL_ARTIFACTS §1) is more than 30 days ago, AND
2. At least one of its cited canonical artifacts (transitively) has a rotated fingerprint since that `last_verified_on` date.

The 30-day threshold aligns with MACRO_PLAN_v2_0 §IS.8 red-team cadence's "every 12 months for MP itself" lower bound — a governance artifact untouched for more than 30 days in a daily-cadence project is suspect. Fingerprint-delta is the binary flip condition: stale-by-calendar alone is only a warning; stale-by-calendar + transitive-dependency-rotated is the finding.

### Rationale

Axis C.5 of the governance integrity protocol (Living-Document Hygiene) requires staleness detection. This policy gives the detection its concrete thresholds.

### Enforcement mechanism

- `drift_detector.py` already computes fingerprint-delta across CANONICAL_ARTIFACTS (Step 7 implementation). This policy adds the 30-day + transitive-dependency-rotated composite rule as a new finding class `stale_suspect_canonical` at MEDIUM severity.
- Registered as a documented detector behavior — no new code path if `drift_detector.py --full` already walks the canonical graph. If not, the code addition is one predicate in the existing canonical-walk loop. (Step 13 drift-detection baseline run will confirm the extension shape.)
- Quarterly governance pass (§H) materializes the Staleness Register as a dated report.

### Failure mode

`stale_suspect_canonical` MEDIUM fires. The next session that opens the project is prompted at handshake to acknowledge the stale artifact and schedule a refresh. No session close-blocker — staleness is a watch, not a stop.

---

## §F — CI / cron cadence

### Policy

The three governance scripts (`drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py`) MUST run on every session close. This is already mandated by `SESSION_CLOSE_TEMPLATE_v1_0.md §2` (`drift_detector_run`, `schema_validator_run`, `mirror_enforcer_run` fields). This policy confirms the per-session cadence is the operational floor.

**Nightly automation is out of scope** for this environment. The MARSYS-JIS project runs as a daily-cadence human-in-the-loop workflow; there is no CI runner, no cron service, no persistent automation host at the time of this policy commit. The per-session cadence is sufficient because closed-artifact-per-session discipline (§M CLAUDE.md) ensures there is no between-session edit activity to detect.

If a persistent automation host is introduced in a future phase, the nightly cadence becomes: `drift_detector.py --full` + `schema_validator.py --full-repo` + `mirror_enforcer.py --all-pairs` at 02:00 local, with reports persisted under `00_ARCHITECTURE/drift_reports/nightly/`. Introduction of the nightly cadence is a Macro-Plan review trigger (§I) per "non-trivial mechanism addition" category.

**Phase 14G Lockdown Whitelisted Residuals (2026-04-29).** The following known residuals are added to the §F exit-code-3 whitelist at Phase 14G close. Each item carries a booking reference and rationale. Sessions that cite these items by ID in their `known_residuals` block are permitted exit-code-2/3 pass for the named finding categories.

| WL ID | Validator | Finding | Booking Reference | Rationale |
|---|---|---|---|---|
| WL.14G.01 | schema_validator | +6 violations: Phase 14 reports use `report_id:` frontmatter instead of `artifact:` | Phase_14G_Lockdown_Verification / PHASE_14_FINDINGS_DISCHARGE_v1_0 D.1 | Naming inconsistency in reports only; no artifact integrity impact. Batch-correct in next governance pass. |
| WL.14G.02 | drift_detector | 222 total findings (11 HIGH, 211 MEDIUM): 5 Learning Layer schema fingerprint mismatches + 5 Phase 14E register JSON fingerprint mismatches (CANONICAL_ARTIFACTS stale) + ~76 MEDIUM registry_disagreement from TRANSITIONAL→LOCKED entries in CAPABILITY_MANIFEST | Phase_14G_Lockdown_Verification / PHASE_14_FINDINGS_DISCHARGE_v1_0 D.2 | Pre-existing stale fingerprints in CANONICAL_ARTIFACTS (SUPERSEDED surface); registry_disagreement expected while CANONICAL_ARTIFACTS and CAPABILITY_MANIFEST are not byte-identical. Resolve at CANONICAL_ARTIFACTS retirement pass. |
| WL.14G.03 | drift_detector | A.1: l25_cgm_edges lacks FK constraints for source_node_id→l25_cgm_nodes and target_node_id→l25_cgm_nodes | Phase_14G_Lockdown_Verification / PHASE_14_FINDINGS_DISCHARGE_v1_0 A.1 | App-level integrity confirmed (0 broken refs). FK constraints would complicate batch loads. Defer to Phase 14H maintenance. |
| WL.14G.04 | drift_detector | B.1: build_manifests has 7 live rows (6 are FK-anchor seed entries with chunk_count=0) | Phase_14G_Lockdown_Verification / PHASE_14_FINDINGS_DISCHARGE_v1_0 B.1 | Seed pattern is intentional; not a swap-discipline violation. |

**Exit-code policy (close-checklist extension).** Step 8 red-team finding F.2 noted that the current close-checklist fails on any nonzero exit code from the three scripts, but exit code 3 (MEDIUM/LOW findings only) is the normal baseline when `drift_detector.py` reports pre-existing whitelisted MEDIUM/LOW drift. This policy amends the close-checklist validation: exit code 3 passes close IF AND ONLY IF accompanied by a `known_residuals` block in the close YAML that enumerates every MEDIUM/LOW finding with a booking reference (step/date/rationale). Exit codes 1, 2, and 4+ always fail close.

### Rationale

Axis C.5 of the protocol mandates script execution at every session close. F.2 from Step 8 red-team documents the exit-code-3 policy gap. Both close here.

### Enforcement mechanism

- `SESSION_CLOSE_TEMPLATE_v1_0.md` (already active): three `*_run` fields are mandatory close-checklist items.
- `schema_validator.py` close-checklist validation: exit-code-3 whitelist rule added — pass IF `known_residuals` block present AND every listed finding is MEDIUM or LOW AND each carries a booking reference (step_id + rationale).
- Documented human cadence: no nightly automation; per-session cadence is the operational floor.

### Failure mode

Exit code 1/2/4+ in any script run → close fails, session halts. Exit code 3 without `known_residuals` block → close fails with `close_checklist_known_residuals_missing` HIGH. Exit code 3 with `known_residuals` block containing a HIGH/CRITICAL entry → close fails with `close_checklist_residual_severity_violation` HIGH.

**GH-DRIFT-DETECTOR-FIX (2026-05-21) — drift_detector directory-entry hardening.** `drift_detector.py` crashed with `IsADirectoryError` when `CAPABILITY_MANIFEST.json` contained entries whose `path` resolved to a directory (e.g., `08_CLASSICAL_CROSS_REFERENCE/` registered with `representations: ["folder"]`). Fix applied in session GH-DRIFT-DETECTOR-FIX: `check_ca_filesystem_fingerprints` now guards `path_abs.is_dir()` before calling `compute_sha256`, emitting a LOW `directory_entry_skipped` finding and continuing. This is fix shape (b) per the brief. The exit-code-3 known_residuals discipline is NOT relaxed — the threshold remains exit ≤ 3 for findings-only; exit 4 (script error) still fails close. Directory entries that are intentional folder registrations will appear as LOW `directory_entry_skipped` findings; these may be added to the known_residuals whitelist at any session that encounters them.

**GitHub Actions pre-merge CI gap (2026-05-24, surfaced at R11.F audit).** The project's GitHub Actions workflows (`ci.yml`, `deploy.yml`, `chat-v2-ci.yml`) are configured to trigger on push/PR to `main` or specific named branches (`feature/**`), but NOT on the `chat-v2/**` branch family used by Chat V2 rounds (R7–R11+). As a result, PRs from `chat-v2/*` branches (including R11.F PR #156) land on main without any automated pre-merge test run. The only pre-merge verification is the per-session local test run discipline and the manually-invoked audit protocol. **Structural gap:** every future `chat-v2/*` PR merges without CI gate. Remediation options: (a) add `chat-v2/**` to `ci.yml` and `chat-v2-ci.yml` trigger branches; (b) require a `pre-merge` label on Chat V2 PRs which `chat-v2-ci.yml` already uses for its conditional jobs (see `if: contains(github.event.pull_request.labels.*.name, 'pre-merge')`). Option (b) is lower-risk (no branch-glob expansion); option (a) provides full coverage. Neither is a MARSYS data-integrity gap — it is a platform engineering quality gap. Resolution requires a targeted `.github/workflows/` edit (1-session scope); book as a maintenance item for the next Chat V2 arc setup session.

---

## §G — Red-team cadence + learning_layer_stub validator class

### Policy (red-team cadence)

Per `MACRO_PLAN_v2_0.md §IS.8`, red-team passes fire at three cadences:

1. **Every 3rd session by default** (counter resets at each step-bound red-team AND at each macro-phase close).
2. **Every macro-phase close** before the SESSION_LOG seal (the red-team is a close-blocker, not a post-close cleanup).
3. **Every 12 months for MP itself** regardless of phase state.

Red-team sessions are a first-class session class per `SESSION_LOG_SCHEMA_v1_0.md §1`. Their SESSION_LOG entries carry a `red_team_verdict` field (one of: `PASS | PASS_WITH_FIXES | FAIL`) and a `findings_log_path` field pointing at the red-team artifact (e.g., `GOVERNANCE_INTEGRITY_REDTEAM_v1_0.md`).

The session-open handshake's `red_team_due` field makes the cadence machine-checkable: when `true`, the session either is a red-team session OR the handshake fails. The counter is maintained in `CURRENT_STATE_v1_0.md` (added as a field at Step 12 close) and incremented at every session close.

### Policy (learning_layer_stub validator class per LL scaffold §5.7)

Per `LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md §5.7`, Step 12 commits a `learning_layer_stub` validator class to `schemas/artifact_schemas.yaml`. The class governs the four LL.1–LL.4 mechanism stub READMEs under `06_LEARNING_LAYER/`. Its rules:

1. **STATUS-banner regex.** The first non-frontmatter line of each stub README must match `^STATUS:\s*(STUB|ACTIVE)\s*(—|-)\s*.*$`. Exact form: `STATUS: STUB — activates at M4` (or equivalent for the mechanism).
2. **Population gate.** If the STATUS banner reads `ACTIVE`, the frontmatter must contain a non-null `activation_session_id` field pointing at a SESSION_LOG entry AND either a non-null `activation_lel_entry` (pointing at a LEL v1.X event ID) OR a non-null `activation_ppl_entry` (pointing at a PPL prediction ID). This enforces the two-pass population-gate rule from LL scaffold §5.2 (a mechanism cannot be marked ACTIVE without a matching LEL or PPL record).
3. **Classical-priors-locked guard.** The frontmatter's `writes_to` field, if present, must be a subset of `06_LEARNING_LAYER/**` globs. Any write-target outside `06_LEARNING_LAYER/` fails the check — this enforces LL scaffold §5.5 (learning modulates; never overwrites the classical-prior corpus).

### Policy (per-mechanism LL N-override default)

Per `LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md §5.4` explicit deferral to Step 12: the per-mechanism N-override value is **N=3 per mechanism, no override**. Binding from Step 12 close forward. A mechanism's activation session (at M4 for LL.1–LL.4; at M5–M10 for LL.5–LL.10) MAY propose a different N via a §LL-Appendix.B amendment to MACRO_PLAN, which is itself a Macro-Plan review trigger (§I).

### Rationale

`MACRO_PLAN_v2_0.md §"Learning discipline rule #3"` deferred per-mechanism N-override to "Step 11 scaffold or the mechanism's activation phase, whichever comes first." LL_SCAFFOLD §5.4 exercised the "whichever comes first" clause by deferring to Step 12. Committing N=3 default now gives the mechanism stubs a concrete baseline without pre-building M4+ operational parameters.

### Enforcement mechanism

- **Red-team cadence.** Session-open handshake `red_team_due` field + CURRENT_STATE `red_team_counter` field (added at Step 12). Counter increment at every close.
- **learning_layer_stub class.** Registered in `schemas/artifact_schemas.yaml`. Validated by `schema_validator.py` at every session that touches a file under `06_LEARNING_LAYER/`.
- **LL N=3 default.** Documented in this policy; LL mechanism stubs at `06_LEARNING_LAYER/{LL.1,LL.2,LL.3,LL.4}/README.md` cite this policy + the N=3 value in their frontmatter (existing stubs carry N=3 already per LL scaffold §5.4).

### Failure mode

- Red-team due but session is not a red-team session → handshake fails with `red_team_cadence_violation` HIGH.
- Stub README missing STATUS banner → `learning_layer_stub_banner_missing` HIGH.
- STATUS ACTIVE without `activation_lel_entry` or `activation_ppl_entry` → `learning_layer_population_gate_violation` HIGH. Session cannot close until one is populated.
- `writes_to` points outside `06_LEARNING_LAYER/**` → `classical_priors_locked_violation` CRITICAL. Session cannot close.

---

## §H — Quarterly governance pass

### Policy

Every calendar quarter (first week of January, April, July, October), the project runs a **governance delta audit**: a fresh read of every canonical artifact + a diff against the prior quarter's grounding-audit baseline. Deliverable: `GROUNDING_AUDIT_v1_<next-minor>.md` (delta-only; does not re-audit unchanged artifacts). The baseline for Q2 2026 is the current `GROUNDING_AUDIT_v1_0.md` (dated 2026-04-23).

First quarterly pass scheduled: **2026-07-01** (Q3 2026 audit). Subsequent passes: 2026-10-01, 2027-01-01, 2027-04-01, etc.

The quarterly pass is distinct from the §G red-team cadence. Red-team is adversarial (tests injections); governance pass is confirmatory (scans for drift). Both run at macro-phase close (§G rule 2 + §H quarterly).

### Rationale

Prevents slow creep: the per-session drift_detector catches single-session deltas, but a cumulative drift pattern across 20 sessions may slip below per-session thresholds. Quarterly full-surface audit catches the cumulative pattern.

### Enforcement mechanism

- Documented human cadence entered into `MAINTENANCE_SCHEDULE_v1_0.md`'s calendar — NOT here. Cross-reference only: this policy binds the cadence; MAINTENANCE_SCHEDULE carries the date list. (MAINTENANCE_SCHEDULE is CLOSED; the cross-reference entry lives in a new §N.1 appendix to be added during post-Step-15 ongoing operations — booked in §K residuals as non-blocking.)
- `drift_detector.py --full` + `schema_validator.py --full-repo` + `mirror_enforcer.py --all-pairs` are the tool-level invocations.
- The pass produces `GROUNDING_AUDIT_v1_<N>.md` as a minor-version bump successor to v1.0. Fingerprint-delta report attached as appendix.

### Failure mode

Missed quarterly pass → `quarterly_governance_pass_missed` LOW at the next session's handshake. Not a close-blocker — the pass is caught up at the next session. Persistent skip (2+ quarters) escalates to MEDIUM via §I Macro-Plan review trigger.

---

## §I — Macro Plan review triggers

### Policy

`MACRO_PLAN_v2_0.md` is version-bumped when any of the following triggers fires:

1. **Non-trivial mechanism addition** — a new L2.5 synthesis mechanism, a new L3 domain report class, a new L4 discovery pattern, a new Learning Layer mechanism (LL.11+), a new System Integrity Substrate axis (IS.10+), or a new Ethical Framework tier.
2. **Macro-phase redefinition** — scope change to any of M1–M10, addition of an M11+, or merger/split of existing macro-phases.
3. **External constraint change** — new classical text corpus acquired (e.g., a new Nadi branch); new agent class integrated (per MP §3.4.E third-agent admission protocol); ethical-framework policy change from the native.
4. **Finding cluster** — ≥3 cumulative HIGH findings against MP v2.0 from quarterly governance passes (§H) without resolution.
5. **Red-team FAIL verdict** — any red-team session whose verdict is FAIL against MP content.

Each trigger forces a minor-version bump (v2.0 → v2.1) at minimum. Multi-trigger events or architectural-level changes force a major bump (v2.0 → v3.0) with native approval.

### Explicit re-defer of WARN.2 / WARN.5 / WARN.7 (from Step 5 / Step 5A)

Three drift warnings remain open from earlier rebuild steps that are **explicitly out of scope for Step 12 and are not silent deferrals**:

- **WARN.2** — `PHASE_B_PLAN_v1_0.md §5` header + `§N.10` live MP v1.0 pointers.
- **WARN.5** — `B0_KICKOFF_PROMPT_FOR_CLAUDE_CODE.md` line 20 live MP v1.0 pointer.
- **WARN.7** — `025_HOLISTIC_SYNTHESIS/CLAUDE.md` line 3 live `PROJECT_ARCHITECTURE_v2_1 §C.3 / §H.4` pointer.

**Disposition.** All three are scheduled for resolution at the `PHASE_B_PLAN_v1_0.md v1.0.3` amendment cycle that fires naturally when M2 execution resumes post-Step-15 close. Rationale for non-inclusion at Step 12:
- PHASE_B_PLAN is a separately-authored artifact (canonical_id `PHASE_B_PLAN`, path `00_ARCHITECTURE/PHASE_B_PLAN_v1_0.md`, authoritative_side claude); its amendment cycle is governed by the B-plan itself, not by a governance-hygiene step.
- The 025_HOLISTIC_SYNTHESIS/CLAUDE.md subfolder helper is a B-plan-phase-specific reading surface activated at M2 B-phase resume; touching it at Step 12 would pre-build for a later phase (forbidden by MACRO_PLAN §Scope Boundary).
- The v1.0 SUPERSEDED banners on `MACRO_PLAN_v1_0.md` and `PROJECT_ARCHITECTURE_v2_1.md` already route any reader of these three live pointers to the CURRENT version in one hop, per §A archival policy. No functional hazard persists between Step 12 close and PHASE_B_PLAN v1.0.3 amendment-cycle fire.

This re-defer is not "will revisit" language — it is a scheduled amendment with a named owner (the PHASE_B_PLAN v1.0.3 cycle) and a named trigger (M2 resume post-Step-15). It meets brief §4's "explicitly out of scope with rationale" standard.

### Rationale

§2 of MACRO_PLAN_v2_0 defines the ten-macro-phase arc; §IS-level additions are architectural, not incremental. Explicit trigger enumeration prevents silent MP mutation.

### Enforcement mechanism

- Human trigger recognition + version bump per `PROJECT_ARCHITECTURE_v2_2.md §B.8` versioning discipline.
- `drift_detector.py` scans MACRO_PLAN_v2_0 frontmatter `changelog` against CANONICAL_ARTIFACTS §1 version; mismatch fires `macro_plan_version_mismatch` HIGH.

### Failure mode

Silent MP mutation (content change without version bump) fires `macro_plan_version_mismatch` HIGH at the next session's handshake. Unrecognized trigger (e.g., a new mechanism landed without MP bump) catches at the next quarterly governance pass via §H.

---

## §J — Implementation actions (index)

Every policy §A–§I has a backing action. This section is the cross-index.

| Policy | Action type | Implementation site |
|---|---|---|
| §A Archival retain-in-place | Documented human cadence + existing detector | GOVERNANCE_STACK §13 STEP_12 amendment log; drift_detector.py `supersession_banner_mismatch` check (Step 7 origin) |
| §B LEL v1.1 cleanup | One-time session action + standing §A rule | Step 12 close: `files_touched` includes `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_1.md` with §A treatment |
| §C Scope-boundary close-check | New validator function | `schema_validator.py::validate_scope_boundary` + `schemas/artifact_schemas.yaml::session_close.scope_boundary` |
| §D SESSION_LOG completeness | New validator function | `schema_validator.py::validate_files_touched_completeness` + schema entry |
| §E Staleness Register | Existing detector + new finding class | `drift_detector.py` canonical-walk + `stale_suspect_canonical` finding |
| §F CI cadence + exit-3 whitelist | Template field (existing) + new validator rule | `SESSION_CLOSE_TEMPLATE §2` + `schema_validator.py` close-checklist exit-code rule |
| §G Red-team cadence | Handshake field (existing) + CURRENT_STATE counter | `SESSION_OPEN_TEMPLATE §2.red_team_due` + new `CURRENT_STATE.red_team_counter` field |
| §G learning_layer_stub class | New validator class | `schemas/artifact_schemas.yaml::learning_layer_stub` + `schema_validator.py::validate_learning_layer_stub` |
| §G LL N=3 default | Policy commit (this file) | Binding from Step 12 close; cited by LL mechanism stub frontmatter |
| §H Quarterly pass | Documented cadence | Cross-reference entry into `MAINTENANCE_SCHEDULE` §N.1 appendix (post-Step-15 action) |
| §I MP review triggers + WARN re-defer | Documented trigger list + existing detector | MACRO_PLAN §Scope Boundary + `macro_plan_version_mismatch` check |
| §O Build-state serialization at close | New script + close-checklist field | `platform/scripts/governance/serialize_build_state.py`; `SESSION_CLOSE_TEMPLATE §2::build_state_serialized`; `schema_validator.py` presence/value check |

Additional implementation actions required by Step 12 close (not in §A–§I but in the brief's close-criteria list):

| Action | Target | Rationale |
|---|---|---|
| F.1 mirror-structural-block check | `schema_validator.py::validate_mirror_structural_block` | Closes Step 8 red-team F.1 (coarse mirror substring match) |
| F.2 close-checklist exit-3 policy | §F policy | Closes F.2 |
| F.3 `--dr-entry` validator subcommand | `schema_validator.py` CLI | Closes F.3 (no single-entry DR validator mode) |

---

## §K — Residual-finding disposition (Step 12 close record)

Per brief §4 "do not defer with 'will revisit'" — every residual as of Step 12 open either closes here or re-defers with explicit rationale + named owner + named trigger.

| ID | Description | Severity | Disposition | Rationale |
|---|---|---|---|---|
| **GA.12** | LEL v1.1 predecessor unarchived | LOW | **CLOSED** | §B action |
| **GA.20** | Scope-boundary enforcement | MEDIUM | **CLOSED at full-surface layer** | §C validator (Step 7 closed handshake layer; Step 12 closes close-checklist layer) |
| **GA.21** | SESSION_LOG completeness | LOW | **CLOSED** | §D validator |
| **F.1** | Mirror substring-presence gap | WARN | **CLOSED** | `validate_mirror_structural_block` extension |
| **F.2** | Close-checklist exit-3 policy gap | WARN | **CLOSED** | §F exit-code whitelist rule |
| **F.3** | No `--dr-entry` validator mode | WARN | **CLOSED** | New CLI subcommand |
| **WARN.2** | PHASE_B_PLAN §5 + §N.10 live MP v1.0 pointers | WARN | **RE-DEFERRED** to PHASE_B_PLAN v1.0.3 amendment cycle | §I rationale; trigger: M2 resume post-Step-15 |
| **WARN.5** | B0_KICKOFF_PROMPT MP v1.0 pointer | WARN | **RE-DEFERRED** to PHASE_B_PLAN v1.0.3 amendment cycle | §I rationale; same trigger as WARN.2 |
| **WARN.7** | 025_HOLISTIC_SYNTHESIS/CLAUDE.md v2.1 pointer | WARN | **RE-DEFERRED** to PHASE_B_PLAN v1.0.3 amendment cycle | §I rationale; subfolder helper activated at M2 B-phase resume |
| **WARN.3** | MP CW.PPL scaffold-anchor language harmonization | WARN | **RE-DEFERRED** to next MP minor-version bump | Low-priority phrasing nit; no functional hazard |
| **WARN.4** | BOOTSTRAP v2.1 pointer | WARN | **CLOSED** | Step 12 retires BOOTSTRAP with SUPERSEDED banner per native decision 2026-04-24 |
| **WARN.6** | subfolder 00_ARCHITECTURE/CLAUDE.md v2.1 pointer | WARN | **CLOSED** | Same retirement action as WARN.4 (subfolder CLAUDE.md stops being referenced from master CLAUDE.md §C #11; becomes orphan and is SUPERSEDED-bannered in the same pass) |
| **FILE_REGISTRY v1.3→v1.4 bump** | Step 10-deferred minor bump | — | **PERFORMED this session** | §K of FILE_REGISTRY_v1_4 changelog |
| **GOVERNANCE_STACK cumulative-log consolidation** | Step 9/10/11-deferred consolidation | — | **PERFORMED this session** | §13 STEP_12 amendment + cumulative-log index |
| **CANONICAL_ARTIFACTS self-row fingerprint** | Step 7 "populated-at-step-7-close" placeholder | — | **RESOLVED this session** | Self-row fingerprint computed + written at Step 12 close |
| **LL N-override default** | LL scaffold §5.4 deferral to Step 12 | — | **COMMITTED** | §G: N=3 per mechanism, no override |
| **GA.6, GA.17, GA.18, GA.19** | Learning Layer / SESSION_LOG naming / menu / you-are-here | — | **already closed at Steps 10/11** | Reference only; no Step 12 action |

---

## §L — Finding-coverage audit table

Comprehensive audit of every finding class relevant to Step 12's scope. Each row either closes at Step 12 or is explicitly re-deferred.

| Class | Count at Step 12 open | Closed at Step 12 | Re-deferred | Remaining |
|---|---|---|---|---|
| GA.N (GROUNDING_AUDIT) | 3 named for Step 12 (GA.12/20/21) | 3 | 0 | 0 |
| F.N (Step 8 red-team) | 3 (F.1/F.2/F.3) | 3 | 0 | 0 |
| WARN.N (pre-existing) | 7 (WARN.1–7; WARN.1 closed Step 11; WARN.3 low-priority re-defer) | 2 (WARN.4, WARN.6) | 4 (WARN.2, WARN.3, WARN.5, WARN.7) | 0 (all have named owner+trigger) |
| Deferred items (Step 7/8/9/10/11 carried) | 4 (FILE_REGISTRY bump, GOVERNANCE_STACK consolidation, CANONICAL_ARTIFACTS self-row, LL N=3) | 4 | 0 | 0 |

Total findings closed at Step 12: **12**. Total findings re-deferred with explicit rationale + owner + trigger: **4**. No silent deferrals. No "will revisit" language.

---

## §O — Build-state serialization at session close

### Policy

Every session-close checklist MUST run `platform/scripts/governance/serialize_build_state.py` and include a populated `build_state_serialized` block in the `session_close` YAML. The field `build_state_serialized.serialized: true` is required for close.

The serializer reads four canonical files (CURRENT_STATE, CANONICAL_ARTIFACTS, SESSION_LOG, ONGOING_HYGIENE_POLICIES) and emits `build_state.json`, which is then uploaded to the GCS object `gs://marsys-jis-build-state/build-state.json`. The AIMJISBuildTracker artifact fetches this object on its refresh-button click and renders current project state without requiring direct repo access.

**Graceful-degradation rule:** If the GCS upload fails due to network or credential issues but the local serialize succeeded, close passes with `uploaded: false` and `gcs_uri` set to the intended target. The uploader retries on the next session. If local serialization itself fails, close is blocked.

### Rationale

The AIMJISBuildTracker artifact's refresh button had no data source — it displayed stale static state and could not self-update. This policy closes that gap: every session close is also a build-state publication event, so the artifact always reflects the most recent closed session without requiring manual intervention. Cowork session 2026-04-26 designed and verified the serializer end-to-end; this session (Madhav_BUILD_TRACKER_INTEGRATION_v0_1) integrates it into the governance discipline.

### Enforcement mechanism

- **Script.** `platform/scripts/governance/serialize_build_state.py` (installed at Madhav_BUILD_TRACKER_INTEGRATION_v0_1, version 0.1.0). Reads canonical files; emits conformant JSON per `platform/scripts/governance/schemas/build_state.schema.json`.
- **Close-checklist field.** `session_close.build_state_serialized` block (added to SESSION_CLOSE_TEMPLATE_v1_0.md §2 at Madhav_BUILD_TRACKER_INTEGRATION_v0_1). `schema_validator.py` validates the block is present and `serialized: true`. Absence or `serialized: false` blocks close.
  Required sub-fields (as of serializer v0.2.0, Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1):
  - `serializer_version`: "0.2.0"
  - `shards_emitted`: integer count of session + phase shard files written (0 if `--emit-shards` was not passed)
  - `cowork_ledger_referenced`: true if `00_ARCHITECTURE/COWORK_LEDGER.md` was read and its entries included in the serialized output; false if file absent (non-blocking)
- **Invocation.** Run after all canonical-file mutations are complete (so the serialized snapshot reflects the final closed state):

  ```bash
  python3 platform/scripts/governance/serialize_build_state.py \
      --repo-root . \
      --session-id <SESSION_ID> \
      --output /tmp/build_state.json \
      --validate-against-schema platform/scripts/governance/schemas/build_state.schema.json \
      --upload-to-gcs gs://marsys-jis-build-state/build-state.json
  ```

  Requires: `pip install pyyaml jsonschema google-cloud-storage` and ADC (`gcloud auth application-default login`) for GCS upload. Local write works without GCS credentials.

- **Canonical endpoint.** `gs://marsys-jis-build-state/build-state.json` (public-read on the single object; bucket-level access remains private). Public URL: `https://storage.googleapis.com/marsys-jis-build-state/build-state.json`. Future session-close serializer invocations pass this URI to `--upload-to-gcs`. Bootstrap performed at `Madhav_BUILD_TRACKER_GCS_BOOTSTRAP` (2026-04-26).

### Failure mode

- Serialization fails (exit 1 or 4) → `build_state_serialized.serialized: false` → close blocked with `build_state_serialization_failed` HIGH. Diagnose via `--validate-only` to isolate the source-parse error.
- Schema validation fails (exit 2) → `build_state_serialized.schema_validated: false` → close blocked. Schema and serializer are out of sync; amend whichever diverged.
- GCS upload fails (exit 3) but local serialize succeeded → `uploaded: false` — **close passes** (LOW warning `build_state_upload_deferred`). Upload manually with `gsutil cp /tmp/build_state.json gs://marsys-jis-build-state/build-state.json` before the next session if freshness matters.
- `build_state_serialized` block absent from close checklist → `schema_validator.py` fires `build_state_serialized_missing` HIGH → close blocked.

### Operational setup (one-time per bucket)

Performed at `Madhav_BUILD_TRACKER_GCS_PERMISSIONS_FIX` (2026-04-26) after the predecessor session's public-read configuration silently failed. Canonized here as the required bootstrap pattern for any future `marsys-jis-*` GCS bucket.

**Step 1 — Grant bucket-level public-read IAM.**

Object-level ACLs (`gsutil acl ch -u AllUsers:R`) are unreliable: when Uniform Bucket-Level Access (UBLA) is enabled — the default for buckets created with `gsutil mb -b on` — UBLA disables object-level ACLs entirely, so the command silently does nothing. Even when UBLA is disabled, the bucket-level IAM binding is the preferred pattern (works in both UBLA-on and UBLA-off states, is idempotent, and survives future UBLA toggles):

```bash
gcloud storage buckets add-iam-policy-binding gs://<BUCKET_NAME> \
    --member=allUsers --role=roles/storage.objectViewer
```

Verify with a bare curl before proceeding:

```bash
curl -sI https://storage.googleapis.com/<BUCKET_NAME>/<OBJECT> | head -3
# Expected: HTTP/2 200
```

**Step 2 — Set CORS configuration.**

GCS sends no `Access-Control-Allow-Origin` header by default. Browsers fetching from `claude.ai` (or any cross-origin context) will see `TypeError: Failed to fetch` even when the object is publicly readable. Apply CORS before testing in any browser context:

```bash
cat > /tmp/cors.json <<'EOF'
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type", "Last-Modified"],
    "maxAgeSeconds": 3600
  }
]
EOF
gsutil cors set /tmp/cors.json gs://<BUCKET_NAME>
gsutil cors get gs://<BUCKET_NAME>   # verify it stuck
```

`origin: ["*"]` is acceptable for the `marsys-jis-build-state` bucket because the object (`build-state.json`) contains only governance metadata (session IDs, version strings, phase pointers) — no birth data, no chart data, no PII. Future build-state buckets that expose sensitive data MUST narrow the origin to `["https://claude.ai"]` or the specific authorized host.

**Step 3 — Verify CORS preflight end-to-end.**

```bash
curl -sI -H "Origin: https://claude.ai" \
     https://storage.googleapis.com/<BUCKET_NAME>/<OBJECT> \
     | grep -i -E "^(HTTP|access-control|content-type)"
# Expected (all three lines must appear):
# HTTP/2 200
# access-control-allow-origin: *
# content-type: application/json
```

If `access-control-allow-origin` is missing, CORS did not propagate — wait 60 s and retry before diagnosing further.

---

## §M — Interactions with other governance surfaces

- **`GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md`** — §C axes remain the upstream definition; this artifact is the operating-level realization of §C.4 (scope) + §C.5 (hygiene) + §C.6 (multi-agent via §G red-team cadence).
- **`LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md`** (CLOSED, 2026-04-18) — corpus-layer maintenance. Referenced, not duplicated. Disjoint scope: this artifact governs `00_ARCHITECTURE/**` + `platform/scripts/governance/**`; LPMG governs `01_FACTS_LAYER/**` + `025_HOLISTIC_SYNTHESIS/**` + `03_DOMAIN_REPORTS/**` refresh.
- **`MAINTENANCE_SCHEDULE_v1_0.md`** (CLOSED, 2026-04-18) — concrete calendar. Referenced by §H for quarterly-pass dates (cross-reference entry to be added at post-Step-15 hygiene pass).
- **`SESSION_LOG_SCHEMA_v1_0.md`** (Step 10) — entry-structure schema. §G red-team cadence consumes `session_class` values from SLS §1.
- **`LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md`** (Step 11) — §5.4 (N-override deferral) and §5.7 (learning_layer_stub validator class) are the source of §G's Learning Layer commitments.

---

## §N — Appendix: fingerprint-rotation audit for Step 12 close

(Populated by the Step 12 close artifact batch; recorded here for §L audit.)

| canonical_id | Pre-Step-12 fingerprint | Post-Step-12 fingerprint | Reason |
|---|---|---|---|
| CANONICAL_ARTIFACTS | (self-row placeholder from Step 7) | `<rotated-at-close>` | +1 row ONGOING_HYGIENE_POLICIES + FILE_REGISTRY path swap v1.3→v1.4 + fingerprint updates + self-row fingerprint resolved |
| FILE_REGISTRY | b23b399de5…b3f833e | `<rotated>` (v1.4 fingerprint) | v1.3 → v1.4 bump |
| GOVERNANCE_STACK | f2a1b1149a…5ca80faa | `<rotated>` | §13 STEP_12 + cumulative-log consolidation |
| CLAUDE | 16002b6b9f…9773a54d | `<rotated>` | §F + §C #11 (BOOTSTRAP drop) + §C #12 (ONGOING_HYGIENE add) edits |
| GEMINIRULES | 5967a56c3e…ff34ae8de | `<rotated>` | MP.1 mirror of CLAUDE.md edits |
| PROJECT_STATE | d6d3757b94…9626e043 | `<rotated>` | MP.2 composite state-block update |
| STEP_LEDGER | 6973a30b30…d0bb853d956 | `<rotated>` | Row 12 → completed; row 13 → ready; History append |
| CURRENT_STATE | 68e2aca859…efc530530e8 | `<rotated>` | State-block update (Step 12 → completed, Step 13 → ready) |
| SESSION_LOG | `<Step-10-placeholder>` | `<rotated>` | Step 12 entry appended |
| LEL | a8e5148a7b…f05014057b4b6 | unchanged | Not touched; LEL v1.1 (predecessor) receives §A banner — not a canonical artifact |
| ONGOING_HYGIENE_POLICIES | (new) | `<computed-at-close>` | NEW artifact |

---

## §P — Cowork ledger discipline

### Policy

Every time a Cowork platform thread that produced governance artifacts, implementation plans, or substantive decisions for MARSYS-JIS is closed, one YAML entry MUST be appended to `00_ARCHITECTURE/COWORK_LEDGER.md` (canonical_id `COWORK_LEDGER`). The entry must be appended in the same session that executes the work spawned by the Cowork thread, or at the latest in the immediately following session.

**Cadence:** append-on-thread-close. One entry per thread. No batching of multiple threads into one entry.

**Length cap:** ≤5 lines of free-form prose per entry (YAML fields not counted toward the cap). This is an intentional low-effort rule: if writing the entry feels burdensome, it is too detailed.

### Entry format

```yaml
thread_name: "<Cowork thread title>"
opened_on: "YYYY-MM-DD"
closed_on: "YYYY-MM-DD"   # or null if ongoing
purpose: "<1-sentence summary>"
outcomes:
  - "<artifact or decision produced>"
spawned_sessions:
  - "<Claude Code session_id>"
```

### Rationale

Cowork conversations are ephemeral from the repo's perspective — they happen outside the repo and are otherwise unreachable by governance scripts. `COWORK_LEDGER.md` is the project-side record. `serialize_build_state.py` reads this file at every session close and surfaces entries in the portal's `/build/parallel` view ("Cowork Ledger" panel). If the file is absent the serializer returns an empty array gracefully; absence does not block close but triggers a LOW finding `cowork_ledger_absent`.

### Enforcement mechanism

- `serialize_build_state.py` reads `COWORK_LEDGER.md` and sets `cowork_ledger_referenced: true/false` in `build_state_serialized`.
- `schema_validator.py` fires `cowork_ledger_absent` LOW if the file does not exist.
- Missing entries for threads whose spawned sessions are already in SESSION_LOG are surfaced as `cowork_ledger_gap` LOW at quarterly governance pass (§H).

---

## §Q — AIOps Routing Override Policy (Phase 3C, 2026-05-18)

### Policy

1. **TTL on temporary overrides.** All writes to `llm_stack_routing_override` MUST set `expires_at` when the override is temporary. AIOps automation: default `NOW() + INTERVAL '72 hours'`; critical emergencies: `NOW() + INTERVAL '4 hours'`. Permanent policy overrides (e.g., nim stack synthesis → gemini-2.5-flash) may use `expires_at = NULL`.

2. **Prefer the Control Panel API.** All writes SHOULD use `PUT /api/admin/aiops/routing/[stack]/[call_type]` so that `actor_user_id` is captured from the authenticated Firebase session. Direct DB writes are captured by the trigger (migration 057) but will log `actor_user_id = updated_by` which may be `'system'` or `'db_direct'`.

3. **Active-override review at session open.** The `00_ARCHITECTURE/aiops_overrides_active.sql` query MUST be reviewed at the start of any session evaluating production state. Add as step 0 of session-open checklist §G.

### Rationale

The 2026-05-15 3-day silent demote (root cause per `PHASE_3C_AIOPS_OBSERVABILITY_BRIEF_v1_0.md`): a direct DB insert on `llm_stack_routing_override` produced no audit entry and persisted indefinitely. Three countermeasures close all three failure modes: DB trigger (migration 057) for audit coverage, `expires_at` column (migration 058) + resolver enforcement (`runtime_config.ts`) for TTL, and `aiops_overrides_active.sql` for review cadence.

### Enforcement mechanism

- Migration 057 trigger: automatic; fires on ALL INSERT/UPDATE/DELETE regardless of source.
- Migration 058 column: `expires_at` resolver filter in `runtime_config.ts` line 43 (`expires_at IS NULL OR expires_at > NOW()`).
- Body schema (`_parse.ts` `routingOverrideBodySchema`): accepts optional `expires_at` ISO string; defaults to NULL if omitted.
- UPSERT in `routing/[stack]/[call_type]/route.ts`: persists `expires_at` to DB; echoes it in the JSON response.

---

## §R — Migration-directory ruling: single directory only (doctrine-waves D-1.5a, 2026-07-15)

### Policy

**All SQL migrations live in `platform/migrations/` and ONLY that directory, from this point
forward.** `platform/supabase/migrations/` is a known failure mode, not a second valid location.

### Rationale

`DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md` §1 (Fable 5's D-1 spec-by-spec audit, 2026-07-14) found
migrations split across two directories on `main`: `platform/migrations/` (367, 435, 436) and
`platform/supabase/migrations/` (434) — "the collision class Lane 2 itself flagged," logged there
as governance close-out item #20, **NOT DONE**. A split migration surface risks numbering
collisions, silent no-ops (a migration applied against the wrong tracked directory never runs),
and an auditor who checks only one directory missing state entirely — exactly the class of drift
`CLAUDE.md §N.4` ("Surgical migrations, verified:") exists to prevent. `CONDUCTOR_PROTOCOL.md` §1 (the
Migration guard role) and §8.5 (the surgical-migration procedure) both already codify
`platform/migrations/` as the single directory for the doctrine-waves campaign; this entry is the
project-wide governance record of that ruling, per BRIEF_D1_5A.md Lane A-0's A6 process item
("migration-directory ruling (all future migrations in `platform/migrations/` only), recorded in
ONGOING_HYGIENE").

### Ruling

1. Every new migration is scaffolded via the `create-migration` skill, which targets
   `platform/migrations/` — never hand-created, never targeted at `platform/supabase/migrations/`.
2. `platform/supabase/migrations/` is not deleted or backfilled by this ruling (that is a
   separate, deliberate consolidation task, out of scope for a D-1.5a A6 process item) — it is
   simply closed to new writes. A session that finds a new file appearing there treats it as a
   defect (misdirected migration), not a valid alternate location.
3. Every migration requires a migration-guard receipt before apply (`CONDUCTOR_PROTOCOL.md` §1 +
   §8.5): destructive-ops review, idempotency (`IF NOT EXISTS` / `ON CONFLICT` discipline per
   `CLAUDE.md` §N.3), and numbering-collision check against `platform/migrations/` as the sole
   source of truth for "what number is next."
4. Apply procedure unchanged from `CONDUCTOR_PROTOCOL.md` §8.5: Cloud SQL Auth Proxy →
   `--dry-run` confirms exactly the expected pending files → apply one file at a time. The deploy
   workflow's auto-run of `migrate.ts` is safe only because the guard receipt already verified
   idempotency pre-merge.

### Enforcement mechanism

- `create-migration` skill hardcodes the target directory — the scaffolding path itself makes
  the wrong directory the harder option, not merely the discouraged one.
- Migration-guard review (`CONDUCTOR_PROTOCOL.md` §1, §3.1 Phase-1 verification) is a required
  receipt before any migration merges in the doctrine-waves campaign; a project-wide CI check
  (`platform/scripts/governance/drift_detector.py` or an equivalent migration-directory linter)
  is a natural follow-up but is NOT introduced by this entry — recorded here as a residual for a
  future hygiene pass, not fabricated as already-built per `CLAUDE.md` §N.4 ("never fabricate").
- Cross-reference: `CONDUCTOR_PROTOCOL.md` §1 (Migration guard role), §8.5 (apply procedure).

## §S — Density-contract hygiene check (doctrine-waves D-1.5b Lane B-7, 2026-07-15)

### Policy

**A capability declaring `density_contract` on its `CapabilityDescriptor` (CLAUDE.md §N.6) must
have that contract mechanically verifiable, not merely self-asserted.** Any capability whose
response layers confirmed findings against catalog-only/requires_pass rows, or whose response is
subject to the response-budget trimmer's byte cap, is a hygiene-check candidate.

### Rationale

CLAUDE.md §N.6 (Serving Density Principle) codifies a discipline the code already practices
(`judgment_query`'s verdict/grounding/drill_pointers/judgment_flags layering; `ganita_yogas_get`'s
`catalog_only_rows_in_page` separation from confirmed `yogas_fired`). A principle written into
governance text with no executable check attached is exactly the drift class this artifact exists
to prevent (§0's own framing: "a validator check, a template field, a registry rule, or a
documented human cadence" — prose alone is none of these). D-1.5b Lane B-7 wires the first
executable check; see `platform/scripts/audit/density_harness/` for the harness itself.

### Ruling

1. Every new or modified capability that declares `density_contract` and layers confirmed vs.
   catalog-only/requires_pass rows (or any other verification-density split) MUST have at least
   one assertion in the density/census harness (`platform/scripts/audit/density_harness/`)
   covering: (a) the confirmed-layer is never silently merged into the catalog-only count, and
   (b) a `TrimmableSection` with `hardFloor: true` on that capability's confirmed layer actually
   survives a forced hard-cap trim (regression guard for the class of bug the D-1.5a wave gate
   caught in `judgment_query`'s `bearing_yogas`).
2. The harness runs in CI (`.github/workflows/` — the Ganga Quality Gate or an equivalent
   governance-gates job) on every PR touching a file under `platform/src/lib/retrieval/registry/`
   or `platform-mcp/src/lib/response_budget.ts` / `platform-mcp/src/tools/`.
3. A capability that declares `density_contract` but has zero harness coverage is a residual to
   flag at the next quarterly governance pass (§H) — not a blocking condition for THIS wave (the
   harness ships covering the two surfaces D-1.5b Lane B-7 verified: `judgment_query` and
   `ganita_yogas_get`), but future waves extending density-layered surfaces inherit the obligation
   in Ruling item 1.

### Enforcement mechanism

- `platform/scripts/audit/density_harness/` — executable assertions against the MCP/serving
  layer (never prose), following the doctrine-waves convention set by the D-1.5a doctrine harness.
- CI wiring per Ruling item 2 — a red result blocks merge like any other Ganga Quality Gate check.
- Cross-reference: `CLAUDE.md` §N.6 (the principle text this check verifies); `CONDUCTOR_PROTOCOL.md`
  §3 (Phase-1 verification's "executable assertion harness" requirement, the same discipline this
  entry extends to density/layering rather than doctrine correctness).

---

*End of ONGOING_HYGIENE_POLICIES_v1_0.md — amended at Madhav_PORTAL_BUILD_TRACKER_IMPL_v0_1 (2026-04-26): §O extended (shards_emitted, cowork_ledger_referenced fields); §P Cowork ledger discipline added. Amended 2026-05-18 Phase 3C: §Q AIOps Routing Override Policy added. Amended 2026-07-15 (doctrine-waves D-1.5a Lane A-0, A6 process item): §R migration-directory ruling added (single directory `platform/migrations/`, per DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §1 finding + CONDUCTOR_PROTOCOL.md §1/§8.5). Amended 2026-07-15 (doctrine-waves D-1.5b Lane B-7): §S density-contract hygiene check added (CLAUDE.md §N.6 companion enforcement mechanism).*
