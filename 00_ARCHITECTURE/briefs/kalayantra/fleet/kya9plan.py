#!/usr/bin/env python3
"""kya9plan.py — apply Amendment A9 (D-51, D-52, D-54, D-53 not_applicable set) to the plan model.

Owner Amendment A9 (KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A9_SCOPE.md §2–§5). Idempotent and deterministic:
it edits only the fields named below, writes ACCEPTANCE_ROOTS_v3.json from the model, and computes the closure with
kyclosure.compute (twice; the two renders must be byte-identical). CLOSURE_v3.json is machine-owned (SR-CHURN-CUT 3: CI
regenerates it from main, a PR never carries it), so this script prints its digest and writes the file only with --write-closure
(the cockpit's refresh of the main checkout).

Edits to plan_model.json (nothing else is touched):
  C-1.depends_on          JOIN-ALL removed (D-51.1); C-1 gates on the acceptance roots, K-AVADHI-C and the post-flip
                          phase (D-52) so the guarded close can never open early
  K9-4a.depends_on        the five retired packet-exit reviews dropped (D-54)
  K6-N1..N3.depends_on    V-K6 (retired by D-54) replaced by the K6 items it reviewed, so the retirement does not
                          propagate not_applicable into three live follow-ups
  V-K9.depends_on         K9-5, KR-1, KR-2 (deferred by D-53) removed, so a deferred item never gates the final review
  J-7, J-7-a63, J-7-b61, J-7-n-t2, J-7b, J-7b-b62
                          depends_on J-6l where missing (D-52.1); triage class a (was b: deferred) — not deferred
  D-T2, L0-K              (SR-W34-PREP-RULINGS 5b, applied by the close-prep PR, not by this script) deferred with re-entry
                          'post-flip'; not C-1 dependencies; the J-7 family no longer depends on D-T2
  JOIN-ALL, K-CERT-2, W4-SAFETY-N01/N02, KA3B-N1/N2, OPS-NB-03, V-K3b/V-K5/V-K6/V-KA/V-VC
                          not_applicable, the way the tracker records it (CONTROL_PLANE.md: a final decision outcome
                          that contradicts requires_outcome): one retirement decision per reason, requires_outcome
                          {decision: approved}; the cockpit records each decision `refused` after the merge
  D-53 deferred set       triage class b with the re-entry condition (never counted as closed)
  A9-NB-04 triage-b       (SR-A9-INTERP) J-4a-a25 / J-4a-a26: no phase brief reads their output (J-4a reads the single
                          settled build only) → J-4a's depends_on edges cut, deferred with re-entry; J-3a-b44: the '4.1'
                          scored baseline is named by J-5q-b54's brief → class a, stays in the closure
  SR-DT2-CANDIDATE (2026-10-22) D-T2          decided (a): its gates J-6l and L0-K are cut so the tracker reads the recorded decision as done
  SR-PARKED-OUT-OF-CAMPAIGN (2026-10-22) KR-1, KR-2, J-7a, J-7a-pr3099, J-7a-a62, J-8, J-8a, J-8-b63, J-8-j3, J-4a-a25, J-4a-a26,
                          J-3a-b44, L0-K: deferred out of the campaign (class b, ruling named in the reason, re-entry carried to
                          POST_CAMPAIGN_v1_0.md); applied last, so it supersedes the A9_NB04_KEPT class a for J-3a-b44
  SR-AUDIT-NA-TIMEOUT (2026-10-22) D-GOCHARA-TIMEOUT, J-GOCHARA-TIMEOUT: not_applicable, the same way (retirement decision
                          D-GOCHARA-TIMEOUT-NA, requires_outcome approved; the cockpit records it `refused`)
  SR-AUDIT-BOOKKEEPING (2026-10-22) plan-model text: J-5q-b54 (4.1 is no longer a comparator, SR-F5-41-DEFER), J-4c-a55m (the 1303
                          clause dropped; D-J4B-1303-NA declared)
  SR-A55J-GAPS C8 / SR-A55M-TESTSLICE (2026-10-22, bookkeeping round 2) plan-model text: J-4b-a55j says "verification job configured;
                          executes only on an executor dispatch; no schedule" (C8 option a), not "configured but disabled"; J-4c-a55m
                          records the FB-19 publication-row CHECK (1307) as superseded by the 1379 authority-head guard and acts 12-14
                          as evidenced by the iam_readback receipts (cited by operation id). Text only: no step, edge or status changes.
  FOLD-OUT (owner via madhav-44, 2026-10-22 ~23:30Z: "do not add anything to the tracker")  D-GOCHARA-TIMEOUT-NA and D-J4B-1303-NA are no
                          longer plan ITEMS (the item total returns to 274). J-GOCHARA-TIMEOUT reads not_applicable through the plan's own
                          requires_outcome on the EXISTING decision item D-GOCHARA-TIMEOUT once the cockpit records it `refused`; that item
                          reads decided (class retired). D-J4B-1303-NA stays a declared decision (it retires a clause, not an item) so
                          J-4c-a55m's 1303 clause stays dropped.
  control_plane.triage    roots/closure point at the v3 files

Usage:  kya9plan.py [--repo-root DIR]      (default: the repository containing this file)
"""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kyclosure  # noqa: E402

MODEL_VERSION_TAG = "a9-plan-20261018"
CONTROL = Path("00_ARCHITECTURE/control/kalayantra")
BRIEF = "00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_V3_OWNER_DECISIONS_AMENDMENT_A9_SCOPE.md"

# A9 D-51.1, exactly as listed
ROOTS = {
    "i": ["K9-4b", "K9-6"],
    "ii": ["J-6l", "J-5s", "V-J6"],
    "iii": ["K8-REG", "K-CERT"],
    "iv": ["V-K9", "C-1", "C-2", "C-3", "C-4"],
}
STATEMENTS = {
    "i": "Kāla serves chart 482012f1 end-to-end from a rebuilt, published layer (production rebuild read back and published; live acceptance)",
    "ii": "The Gochara 5.0 flip is sealed and served (ledger sealed, flip reviewed)",
    "iii": "Certification mappings exist for every served Kāla asset (registry and the certification item)",
    "iv": "A guarded close: the final whole-layer review, then C-1 → C-2 → C-3 → C-4 (A9 D-51: the close chain is rooted, JOIN-ALL is superseded)",
}
ROLES = {
    "K9-4b": "the rebuild is read back per writer, verified, and the new head published and read back",
    "K9-6": "live acceptance: the seven views resolve through the registry and the Vidhi bridge against the published head",
    "J-6l": "the 5.0 flip is served and soaked",
    "J-5s": "the Gochara ledger is sealed",
    "V-J6": "the flip packet is accepted by the normal reviewer under criterion v2",
    "K8-REG": "the registry carries a certification mapping for every served Kāla asset",
    "K-CERT": "certification mappings exist for every served Kāla asset",
    "V-K9": "final whole-layer review of the rebuilt layer against the exit criteria",
    "C-1": "guarded close step 1", "C-2": "guarded close step 2", "C-3": "guarded close step 3",
    "C-4": "guarded close step 4",
}

DEFERRED = {  # D-53 (parked, re-entry stated)
    "J-7a": "after V-J6 is accepted and the served layer has run one week on 5.0",
    "J-7a-a62": "after V-J6 is accepted and the served layer has run one week on 5.0",
    "J-7a-pr3099": "after V-J6 is accepted and the served layer has run one week on 5.0",
    "KR-1": "after V-J6 is accepted and the served layer has run one week on 5.0",
    "KR-2": "after V-J6 is accepted and the served layer has run one week on 5.0",
    "J-8": "at campaign close, as documentation",
    "J-8-b63": "at campaign close, as documentation",
    "J-8-j3": "at campaign close, as documentation",
    "J-8a": "at campaign close, as documentation",
    "K9-5": "when Suvarṇa schedules its certification census",
    "K9-5-NB-01": "when Suvarṇa schedules its certification census",
}

# A9-NB-04 (SR-A9-INTERP): J-4a reads the single settled Vimśottarī build (its brief/tests name no A2.5/A2.6 output),
# so the edges J-4a → A2.5/A2.6 are cut and both items are deferred with a re-entry condition.
A9_NB04_CUT_EDGES = {"J-4a": ["J-4a-a25", "J-4a-a26"]}
A9_NB04_REASON = ("deferred by A9 (SR-A9-INTERP, A9-NB-04): no consuming phase brief reads its output "
                  "(FINAL_BUILD_SCOPE_v1_0 and the J-4a brief are silent on A2.5/A2.6)")
A9_NB04_DEFERRED = {
    "J-4a-a25": "when the owner/surrogate records the approved Q6 disposition of the historical 4.1 build, or a phase brief "
                "names the 4.1 build as a measured input",
    "J-4a-a26": "when J-4a-a25 re-enters and the 4.1 evidence (Link-2, gates, PRAMĀṆIN, benchmark) is wanted by a phase brief",
}
# A9-NB-04 class (a): J-5q-b54 (retrodiction '5.0' vs '3.0' vs '4.1') lists B4.4 as an inherited prerequisite it must prove
# (J-5q-b54 brief.tests), so the '4.1' scored baseline is a baseline a contract names: it stays, no longer class b.
A9_NB04_KEPT = {
    "J-3a-b44": "the '4.1' geometric baseline is a scored baseline named by J-5q-b54 (title '5.0 vs 3.0 vs 4.1'; brief.tests "
                "'independently prove inherited prerequisite: B4.4'); stays in the closure (A9-NB-04 class a)",
}

# not_applicable by decision: (decision id, reason, items). Reasons are A9's wording.
NOT_APPLICABLE = [
    ("D-A9-NA-JOIN-ALL", "superseded by ACCEPTANCE_ROOTS_v3 (A9 D-51)", ["JOIN-ALL"]),
    ("D-A9-NA-K-CERT-2", "superseded as complete by Suvarṇa PR #3435 (A9 D-53)", ["K-CERT-2"]),
    ("D-A9-NA-W4-SAFETY", "superseded by the scoped backup and the executed small test (A9 D-53)",
     ["W4-SAFETY-N01", "W4-SAFETY-N02"]),
    ("D-A9-NA-PROCESS-NOTES", "process notes (A9 D-53)", ["KA3B-N1", "KA3B-N2"]),
    ("D-A9-NA-OPS-NB-03", "fleet tooling (A9 D-53)", ["OPS-NB-03"]),
    ("D-A9-NA-PACKET-EXITS",
     "satisfied by the per-change independent reviews under D-OWNER-TESTS-20261016 (A8 §4, A9 D-54)",
     ["V-K3b", "V-K5", "V-K6", "V-KA", "V-VC"]),
]
RETIRED_PACKET_EXITS = ["V-K3b", "V-K5", "V-K6", "V-KA", "V-VC"]
POST_FLIP = ["J-7", "J-7-a63", "J-7-b61", "J-7-n-t2", "J-7b", "J-7b-b62"]
# SR-W34-PREP-RULINGS item 5b (2026-10-19) overrides A9 D-52 for these two: deferred with re-entry, outside C-1's dependencies.
# The J-7 family no longer waits on D-T2 (a closure member must not wait on a deferred item).
PREP_DEFERRED = {
    "D-T2": "post-flip: after V-J6 is accepted and the served layer has run one week on 5.0 (as the J-7a family)",
    "L0-K": "post-flip: after V-J6 is accepted and the served layer has run one week on 5.0 (as the J-7a family)",
}
PREP_CUT_EDGES = {iid: ["D-T2"] for iid in ("J-7", "J-7-a63", "J-7-b61", "J-7-n-t2")}

# SR-PARKED-OUT-OF-CAMPAIGN (owner surrogate madhav-44, 2026-10-22 ~20:06Z; owner direction OWNER-WRAP-NOW-20261022): these thirteen
# are deferred OUT OF THIS CAMPAIGN, with their re-entry conditions carried to POST_CAMPAIGN_v1_0.md. Same mechanism as every
# deferral above (triage class b + re_entry; outside the closure; shown by the tracker as deferred, never as open or done).
# Applied last, so the reason names this ruling; the re-entry text is the item's own condition, carried unchanged except the J-8
# family, whose "at campaign close" is now post-campaign. Nothing here adds or deletes a plan item.
PARKED_REASON = ("deferred out of this campaign by SR-PARKED-OUT-OF-CAMPAIGN (owner surrogate madhav-44, 2026-10-22, owner direction "
                 "OWNER-WRAP-NOW-20261022); carried to 00_ARCHITECTURE/briefs/kalayantra/POST_CAMPAIGN_v1_0.md")
_POST_FLIP_WEEK = DEFERRED["J-7a"]
_Q6_4_1 = A9_NB04_DEFERRED["J-4a-a25"]
PARKED_OUT_OF_CAMPAIGN = {
    "KR-1": _POST_FLIP_WEEK,
    "KR-2": _POST_FLIP_WEEK,
    "J-7a": _POST_FLIP_WEEK,
    "J-7a-pr3099": _POST_FLIP_WEEK,
    "J-7a-a62": _POST_FLIP_WEEK,
    "J-8": "post-campaign, as documentation (was: at campaign close)",
    "J-8a": "post-campaign, as documentation (was: at campaign close)",
    "J-8-b63": "post-campaign, as documentation (was: at campaign close)",
    "J-8-j3": "post-campaign, as documentation (was: at campaign close)",
    "J-4a-a25": _Q6_4_1,
    "J-4a-a26": A9_NB04_DEFERRED["J-4a-a26"],
    "J-3a-b44": _Q6_4_1,
    "L0-K": PREP_DEFERRED["L0-K"],
}

# SR-AUDIT-NA-TIMEOUT (owner surrogate madhav-44, 2026-10-22 ~20:25Z; tracker audit X-20261022T200203Z-tracker-audit, section 5 R1):
# D-GOCHARA-TIMEOUT and J-GOCHARA-TIMEOUT are not_applicable. Same mechanism as the NOT_APPLICABLE set above: one retirement
# decision, requires_outcome {decision: approved} on both items, the cockpit records it `refused`. J-GOCHARA-TIMEOUT keeps its
# own requires_outcome on D-GOCHARA-TIMEOUT (a second, additive condition).
TIMEOUT_NA_DECISION = "D-GOCHARA-TIMEOUT-NA"
TIMEOUT_NA_TARGETS = ["D-GOCHARA-TIMEOUT", "J-GOCHARA-TIMEOUT"]
TIMEOUT_NA_REASON = (
    "Not applicable. The only target of J-GOCHARA-TIMEOUT is the legacy v3 century materializer row (writer timeout 3600 s). "
    "No retained item consumes it (plan-model triage text for D-GOCHARA-TIMEOUT); the century is built by ka_gochara_v5, whose "
    "writer timeout migration 1395 set to 72,000 s and read back (EXEC-1395-READBACK; receipts "
    "J-3c.1395-migration-readback-20261018T101656Z, J-3c.1395-registry-readback-20261018T101656Z); the v3 writer is retired by "
    "J-7a. KYD-108 deferral stands; the receipts it asked for were never produced. Re-entry: if J-4f shows a timeout binding. "
    "(SR-AUDIT-NA-TIMEOUT, owner surrogate madhav-44, 2026-10-22)")

# SR-AUDIT-BOOKKEEPING (same ruling batch; audit section 3 rows J-5q-b54 and J-4c-a55m, section 5 R3): plan-model text that lagged a
# recorded ruling. Exact-text edits, applied once (each is skipped when the old text is already gone).
B54_TITLE_OLD = "Retrodiction report: '5.0' vs '3.0' vs '4.1' on held-out events, per-mechanism attribution"
B54_TITLE_NEW = ("Retrodiction report: '5.0' vs '3.0' on held-out events, per-mechanism attribution "
                 "(4.1 was not built for this campaign: SR-F5-41-DEFER)")
B54_TEST_OLD = "Before landing, independently prove inherited prerequisite: B4.4"
B54_TEST_NEW = ("4.1 is not a comparator (SR-F5-41-DEFER, owner surrogate madhav-44, 2026-10-21): the report states in its header "
                "that 4.1 was not built for this campaign (deferred by this ruling), compares 5.0 vs 3.0 only and never "
                "substitutes another baseline; the B4.4 prerequisite (the 4.1 baseline) is post-campaign EVAL-41-ON-SEALED, "
                "not proven here")

A55M_NA_DECISION = "D-J4B-1303-NA"
A55M_TITLE_OLD = "G8 seal-time census, 1303 and the dormant-role revokes, runner set"
A55M_TITLE_NEW = "G8 seal-time census, runner set"
A55M_TEST_PREFIX = "1303 and the dormant-role revokes: OPEN."
A55M_TEST_NEW = (
    "1303 and the dormant-role revokes: NOT APPLICABLE by D-J4B-1303-NA (DECISIONS_SURROGATE.jsonl, 2026-10-21T03:17Z; SR-AUDIT-BOOKKEEPING "
    "declares it here). MEASURED: 1303 is not in the production ledger (never merged) and 1378 revokes nothing; the window2 readback "
    "J-4c-a55m.window2-20261021T0315Z shows 13 dormant-writer rows (NOLOGIN, memberless roles holding INSERT/UPDATE/DELETE/TRUNCATE "
    "on Gochara tables) - a security-posture item with no effect on any result, not done in this campaign (OWNER-MINIMAL-PROTECTION-20261018, "
    "SR-GRANTS-MINIMAL); finding F-DORMANT-ROLES is on the native's post-campaign list. This step no longer requires the revokes.")
A55M_NOTES_OLD = "1303 / the dormant-role revokes stay OPEN (1378 revokes nothing) until the window2 readback is run."
A55M_NOTES_NEW = ("1303 / the dormant-role revokes are not_applicable by D-J4B-1303-NA (the window2 readback was run; 1378 revokes "
                  "nothing; F-DORMANT-ROLES is post-campaign).")
A55M_NA_DECISION_TITLE = "Not applicable (J-4c-a55m, the 1303 clause): 1303 and the dormant-role revokes"
A55M_NA_DECISION_DEFAULT = (
    "refused — the 1303 and dormant-role revokes clause of J-4c-a55m is not applicable: 13 dormant-writer rows (receipt "
    "J-4c-a55m.window2-20261021T0315Z) are a security-posture item with no effect on any result, not done in this campaign "
    "(OWNER-MINIMAL-PROTECTION-20261018, SR-GRANTS-MINIMAL); finding F-DORMANT-ROLES is recorded for the native's post-campaign list "
    "(DECISIONS_SURROGATE.jsonl D-J4B-1303-NA, madhav-88, 2026-10-21T03:17Z)")


# FOLD-OUT: the two retirement-decision ITEMS #3896 added are removed; their DECISIONS stay (decision ledger entries, not plan items).
FOLDED_OUT_DECISION_ITEMS = (TIMEOUT_NA_DECISION, A55M_NA_DECISION)
TIMEOUT_RULED_DECISION = "D-GOCHARA-TIMEOUT"     # the existing decision item the timeout pair's n/a now reads

# SR-A55J-GAPS C8 option a (owner surrogate madhav-44, 2026-10-22T20:34:34Z): the verification job is configured and enabled:true is the
# intended state since J-4b (step 9 used it); the job executes only on an executor dispatch and nothing schedules it. The step ids
# `principals_grants_disabled_config` and `protected_apply_and_disabled_provision_readback` are receipt/detector identifiers and keep
# their historical names (renaming would orphan the filed receipts and their patterns).
A55J_WORDING = "verification job configured; executes only on an executor dispatch; no schedule"
A55J_TITLE_OLD = "and the verification job configured but disabled"
A55J_TITLE_NEW = f"and the {A55J_WORDING} (SR-A55J-GAPS C8, option a)"
A55J_NOTES_OLD = "principals, grants and the disabled job config are measured by readbacks"
A55J_NOTES_NEW = (f"principals, grants and the job config ({A55J_WORDING}: SR-A55J-GAPS C8 option a; enabled:true is the intended state "
                  "since J-4b and step 9 used it) are measured by readbacks")
STEP_ID_NOTE = (" The step id %s keeps its historical name: it identifies the filed receipts and detector patterns and is not a claim "
                "about the job's state (SR-A55J-GAPS C8).")
A55J_TEST_OLD = "the entry's enabled state is measured, never assumed)."
A55J_TEST_NEW = (f"the entry's enabled state is measured, never assumed). The claim is \"{A55J_WORDING}\" (SR-A55J-GAPS C8, option a), "
                 "not \"disabled\": cloudrun_job_readback reads the job definition and executor_ops.json the dispatch entry, and neither "
                 "reads Cloud Scheduler, so the no-schedule clause is the ruling's wording and no step receipt claims to have measured it.")
A55M_JOB_OLD = "Verification job definition and sealer credential in disabled state: as J-4b-a55j"
A55M_JOB_NEW = f"Verification job definition and sealer credential: as J-4b-a55j ({A55J_WORDING}; SR-A55J-GAPS C8, option a)"

# SR-A55M-TESTSLICE (the kyd of the readback below): the FB-19 publication-row CHECK was never a migration (the plan-doc number 1307
# collided with an unrelated migration); the migration-1379 authority-head guard refuses a test-slice vector instead.
A55M_PUBLICATION_PREFIX = "Publication refusal for a test-slice vector:"
A55M_PUBLICATION_NEW = (
    "Publication refusal for a test-slice vector: the FB-19 publication-row CHECK (plan-doc number 1307, never a migration) is SUPERSEDED "
    "by the migration-1379 authority-head guard (SR-A55M-TESTSLICE): platform/migrations/1379_gochara_sealed_authority.sql adds CHECK "
    "kga_sealed_authority_ck on kala_gochara_authority (ka_gochara_authority_admissible(chart_id, authoritative_generation)), so a governed "
    "authority head requires a published non-test-slice manifest and a matching seal. MEASURED in production by operation "
    "J-4c-a55m.testslice-refusal-20261022T2054Z (readback_sql, COMPLETED, exit 0, mechanically accepted): kga_sealed_authority_ck present "
    "and validated (convalidated true), both authority heads unchanged at 3.0, 0 published test-slice rows in kala_gochara_publication, "
    "and no test-slice CHECK on the publication table (the readback's publication_row_check section returned no row). The 1307 "
    "publication-row CHECK is therefore not a claim of this step.")
A55M_ACT_OLD = {
    12: "NO existing readback kind measures it (cloudrun_job_readback describes the pipeline job only).",
    13: "NO existing readback kind measures it (cloudrun_job_readback reads a job definition, not its IAM policy).",
    14: "indirectly, a successful one-shot provisioning run through the same proxy identity (github_run_readback, currently enabled:false).",
}
A55M_ACT_NEW = {
    12: ("EVIDENCED by the iam_readback receipt J-4c-a55m.act12-logging-view-20261022T2306Zb (kind iam_readback, read-only; COMPLETED, exit 0; "
         "probe logging_view, MEASURED 2026-10-22T23:06:08Z): view gochara_verification_job (bucket _Default, filter "
         "resource.type=cloud_run_job AND job_name=gochara-verification-job) carries exactly one binding, roles/logging.viewAccessor for "
         "serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com. The negative read with the workflow identity is not part of "
         "this receipt. The earlier request J-4c-a55m.act12-logging-view-20261022T2304Z was REFUSED (missing field kind) and is superseded "
         "by the Zb request (SR-A55J-GAPS)."),
    13: ("EVIDENCED by the iam_readback receipt J-4c-a55m.act13-run-job-iam-20261022T2306Zb (kind iam_readback, read-only; COMPLETED, exit 0; "
         "probe run_job_iam, MEASURED 2026-10-22T23:06:08Z): job gochara-verification-job (asia-south1) carries exactly one binding, "
         "roles/run.jobsExecutorWithOverrides for serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com. The probe reads "
         "that job's policy only; the absence of a project-level roles/run.* binding is not part of this receipt. The earlier request "
         "J-4c-a55m.act13-run-job-iam-20261022T2304Z was REFUSED (missing field kind) and is superseded (SR-A55J-GAPS)."),
    14: ("EVIDENCED by the iam_readback receipt J-4c-a55m.act14-project-cloudsql-client-20261022T2306Zb (kind iam_readback, read-only; "
         "COMPLETED, exit 0; probe project_iam_member_role, MEASURED 2026-10-22T23:06:08Z): held:true for member "
         "serviceAccount:gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com on roles/cloudsql.client. OPEN POINT: the "
         "runbook's Act 14 names github-actions@ as the proxy identity, and this receipt measured the verifier runtime service account, so "
         "the github-actions@ binding is NOT evidenced by it; the reviewer decides which identity the proxy uses. The earlier request "
         "J-4c-a55m.act14-project-cloudsql-client-20261022T2304Z was REFUSED (missing field kind) and is superseded (SR-A55J-GAPS)."),
}
A55M_NOTES_ACTS_OLD = "No new executor kind is assumed; acts 12 and 13 (and 14 directly) have no existing readback."
A55M_NOTES_ACTS_NEW = ("Acts 12-14 are evidenced by the iam_readback executor kind (#3894): receipts J-4c-a55m.act12-logging-view-20261022T2306Zb, "
                       "J-4c-a55m.act13-run-job-iam-20261022T2306Zb, J-4c-a55m.act14-project-cloudsql-client-20261022T2306Zb (act 14: see the open "
                       "point in its step text). The FB-19 publication-row CHECK (1307, never a migration) is superseded by the migration-1379 "
                       "authority-head guard, read back by J-4c-a55m.testslice-refusal-20261022T2054Z (SR-A55M-TESTSLICE). No completion is "
                       "asserted by this text: the item completes only on its own receipt, steps and acceptance.")


# SR-DT2-CANDIDATE (owner surrogate madhav-44, 2026-10-22 20:05Z): D-T2 decided (a) — Sudarśana admitted as a CANDIDATE judge method.
DT2_CLOSED_CUT_EDGES = {"D-T2": ["J-6l", "L0-K"]}


def _dedupe(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


def apply_model_edits(model: dict) -> dict:
    model = copy.deepcopy(model)
    items = {i["id"]: i for i in model["items"]}
    decisions = {d["id"] for d in model["decisions"]}

    # D-51.1 / D-52 — the guarded close follows the acceptance, K-AVADHI-C and the post-flip phase
    root_items = [r for k in ("i", "ii", "iii") for r in ROOTS[k]] + ["V-K9"]
    items["C-1"]["depends_on"] = _dedupe(
        [d for d in items["C-1"]["depends_on"] if d != "JOIN-ALL"] + root_items + ["K-AVADHI-C"] + POST_FLIP)

    # D-52.1 — the post-flip phase depends on J-6l and is not deferred (it was triage b before A9)
    for iid in POST_FLIP:
        if "J-6l" not in items[iid]["depends_on"]:
            items[iid]["depends_on"] = items[iid]["depends_on"] + ["J-6l"]
        items[iid]["triage"] = {"class": "a", "reason": f"post-flip phase of the campaign, not deferred (A9 D-52; {BRIEF})"}

    # D-54 — K9-4a drops the retired packet exits; V-K9 stays out of it (V-K9 → K9-6 → K9-4b → K9-4a would be a cycle)
    items["K9-4a"]["depends_on"] = [d for d in items["K9-4a"]["depends_on"] if d not in RETIRED_PACKET_EXITS]
    for iid in ("K6-N1", "K6-N2", "K6-N3"):
        items[iid]["depends_on"] = _dedupe(
            [x for d in items[iid]["depends_on"] for x in (items["V-K6"]["depends_on"] if d == "V-K6" else [d])])

    # D-53 — a deferred item never gates the final whole-layer review
    items["V-K9"]["depends_on"] = [d for d in items["V-K9"]["depends_on"] if d not in DEFERRED]

    # D-53 — deferred with re-entry (triage class b: never counted as closed)
    for iid, re_entry in DEFERRED.items():
        items[iid]["triage"] = {"class": "b", "reason": f"deferred by A9 D-53 ({BRIEF})", "re_entry": re_entry}

    # A9-NB-04 — cut the edges nothing reads, defer the items; keep the baseline B5.4 names
    for consumer, cut in A9_NB04_CUT_EDGES.items():
        items[consumer]["depends_on"] = [d for d in items[consumer]["depends_on"] if d not in cut]
    for iid, re_entry in A9_NB04_DEFERRED.items():
        items[iid]["triage"] = {"class": "b", "reason": A9_NB04_REASON, "re_entry": re_entry}
    for iid, reason in A9_NB04_KEPT.items():
        items[iid]["triage"] = {"class": "a", "reason": reason}

    # not_applicable, recorded by decision (the tracker's own mechanism)
    anchor = items["D-KCERT-EXISTING-STATUS-20261015"]
    for did, reason, targets in NOT_APPLICABLE:
        if did not in items:
            model["items"].append({
                "id": did, "track": anchor["track"], "lane": anchor["lane"],
                "title": f"Not applicable: {', '.join(targets)} — {reason}",
                "owner": anchor["owner"], "depends_on": ["B-7"], "mandatory": True,
                "done_by": "decision", "decision": did,
                "triage": {"class": "retire_decision", "retires": targets[0] if len(targets) == 1 else targets},
            })
            items[did] = model["items"][-1]
        if did not in decisions:
            model["decisions"].append({
                "id": did,
                "title": f"Not applicable ({', '.join(targets)}): {reason}",
                "owner": "native — owner-authorised by Amendment A9 (D-51, D-53, D-54)",
                "default": f"refused — {reason}",
            })
        for t in targets:
            items[t]["requires_outcome"] = {did: "approved"}
            if did not in items[t]["depends_on"]:
                items[t]["depends_on"] = items[t]["depends_on"] + [did]
            items[t]["triage"] = {"class": "retired", "decision": did, "reason": reason}

    # SR-DT2-CANDIDATE — the decision is recorded (approved, 2026-10-22): D-T2 closes. The tracker reads a decision item done only
    # while every dependency is done, and L0-K now leaves the campaign, so D-T2's gates J-6l and L0-K are cut; the admission work
    # is post-campaign (POST_CAMPAIGN_v1_0.md). Nothing in the closure depends on D-T2 (PREP_CUT_EDGES).
    for consumer, cut in DT2_CLOSED_CUT_EDGES.items():
        items[consumer]["depends_on"] = [d for d in items[consumer]["depends_on"] if d not in cut]

    # SR-PARKED-OUT-OF-CAMPAIGN — the thirteen leave the campaign; class b, re-entry carried, never closed
    for iid, re_entry in PARKED_OUT_OF_CAMPAIGN.items():
        items[iid]["triage"] = {"class": "b", "reason": PARKED_REASON, "re_entry": re_entry}

    # FOLD-OUT (owner via madhav-44, 2026-10-22 ~23:30Z): the retirement-decision ITEMS #3896 added leave the plan; the item total is 274
    # again. The decisions below stay declared (the ledger refuses an outcome for an undeclared decision) and carry `retires`.
    model["items"] = [i for i in model["items"] if i["id"] not in FOLDED_OUT_DECISION_ITEMS]
    for k in FOLDED_OUT_DECISION_ITEMS:
        items.pop(k, None)
    for i in model["items"]:
        if any(d in FOLDED_OUT_DECISION_ITEMS for d in i.get("depends_on", [])):
            i["depends_on"] = [d for d in i["depends_on"] if d not in FOLDED_OUT_DECISION_ITEMS]

    # SR-AUDIT-NA-TIMEOUT — J-GOCHARA-TIMEOUT is not_applicable by the plan's own requires_outcome on the EXISTING decision item
    # D-GOCHARA-TIMEOUT (kyclosure demands a decision item, and the fold-out added none): a recorded `refused` reads it so. The decision
    # item itself reads done once decided, like D-VC after its refusal (the plan's no-cycle invariant forbids a self-requirement); its
    # triage class `retired` keeps it in the cancelled bucket, never in the work. (I) INTERPRETATION; the alternative is a second decision
    # item, which the owner ruled out. The cockpit records `ky decide D-GOCHARA-TIMEOUT --outcome refused` (SR-AUDIT-NA-TIMEOUT).
    model["decisions"] = [d for d in model["decisions"] if d["id"] != TIMEOUT_NA_DECISION]
    items["D-GOCHARA-TIMEOUT"].pop("requires_outcome", None)
    items["J-GOCHARA-TIMEOUT"]["requires_outcome"] = {TIMEOUT_RULED_DECISION: "approved"}
    for t in TIMEOUT_NA_TARGETS:
        items[t]["triage"] = {"class": "retired", "decision": TIMEOUT_RULED_DECISION, "reason": TIMEOUT_NA_REASON}

    # SR-AUDIT-BOOKKEEPING — J-5q-b54: 4.1 is no longer a comparator (SR-F5-41-DEFER)
    b54 = items["J-5q-b54"]
    b54["title"] = b54["title"].replace(B54_TITLE_OLD, B54_TITLE_NEW)
    b54["brief"]["tests"] = [B54_TEST_NEW if t == B54_TEST_OLD else t for t in b54["brief"]["tests"]]

    # SR-AUDIT-BOOKKEEPING — J-4c-a55m: D-J4B-1303-NA declared; the 1303 clause leaves the step
    a55m = items["J-4c-a55m"]
    a55m["title"] = a55m["title"].replace(A55M_TITLE_OLD, A55M_TITLE_NEW)
    a55m["brief"]["tests"] = [A55M_TEST_NEW if t.startswith(A55M_TEST_PREFIX) else t for t in a55m["brief"]["tests"]]
    a55m["brief"]["notes"] = a55m["brief"]["notes"].replace(A55M_NOTES_OLD, A55M_NOTES_NEW)
    if A55M_NA_DECISION not in decisions:
        model["decisions"].append({
            "id": A55M_NA_DECISION, "title": A55M_NA_DECISION_TITLE,
            "owner": ("ADHIKĀRIN (N); surrogate madhav-88, 2026-10-21T03:17Z (DECISIONS_SURROGATE.jsonl D-J4B-1303-NA); declared by "
                      "SR-AUDIT-BOOKKEEPING; the cockpit records the outcome (`ky decide D-J4B-1303-NA --outcome refused`)"),
            "default": A55M_NA_DECISION_DEFAULT,
        })
    # retiring a clause never retires the item: J-4c-a55m carries no requires_outcome on it
    next(d for d in model["decisions"] if d["id"] == A55M_NA_DECISION)["retires"] = ["J-4c-a55m (the 1303 clause only)"]

    # SR-A55M-TESTSLICE / SR-A55J-GAPS (bookkeeping round 2): text only
    a55m["brief"]["tests"] = [
        A55M_PUBLICATION_NEW if t.startswith(A55M_PUBLICATION_PREFIX) else
        t.replace(A55M_JOB_OLD, A55M_JOB_NEW).replace(A55M_ACT_OLD[14], A55M_ACT_NEW[14]) if t.startswith("Act 14 (") else
        t.replace(A55M_ACT_OLD[12], A55M_ACT_NEW[12]).replace(A55M_ACT_OLD[13], A55M_ACT_NEW[13]).replace(A55M_JOB_OLD, A55M_JOB_NEW)
        for t in a55m["brief"]["tests"]]
    a55m["brief"]["notes"] = a55m["brief"]["notes"].replace(A55M_NOTES_ACTS_OLD, A55M_NOTES_ACTS_NEW)
    a55j = items["J-4b-a55j"]
    a55j["title"] = a55j["title"].replace(A55J_TITLE_OLD, A55J_TITLE_NEW)
    a55j["brief"]["tests"] = [t if A55J_TEST_NEW in t else t.replace(A55J_TEST_OLD, A55J_TEST_NEW) for t in a55j["brief"]["tests"]]
    a55j["brief"]["notes"] = a55j["brief"]["notes"].replace(A55J_NOTES_OLD, A55J_NOTES_NEW)
    for item in (a55j, a55m):
        if "keeps its historical name" not in item["brief"]["notes"]:
            item["brief"]["notes"] += STEP_ID_NOTE % item["steps"][0]

    cp = model["control_plane"]["triage"]
    cp["roots"] = str(CONTROL / "ACCEPTANCE_ROOTS_v3.json")
    cp["closure"] = str(CONTROL / "CLOSURE_v3.json")
    if MODEL_VERSION_TAG not in model["model_version"]:
        model["model_version"] += "+" + MODEL_VERSION_TAG
    return model


def build_roots(model: dict, template: dict) -> dict:
    items = {i["id"]: i for i in model["items"]}
    old = {r["item"]: r for a in template["acceptances"] for r in a["roots"]}
    acceptances = []
    for aid in ("i", "ii", "iii", "iv"):
        roots = []
        for iid in ROOTS[aid]:
            it = items[iid]
            roots.append({
                "item": iid,
                "role": ROLES.get(iid) or old[iid]["role"],
                "step": None,
                "title": it["title"],
                "brief_spec": it.get("brief", {}).get("spec"),
                "detector": it.get("detector"),
            })
        acceptances.append({"id": aid, "statement": STATEMENTS[aid], "charter": BRIEF + " §2.1", "roots": roots})
    return {
        "artifact": "ACCEPTANCE_ROOTS",
        "content_version": "3.0",
        "plan_version": "2.7+A9",
        "plan": BRIEF + " §2 (D-51); plan v2.7 §0 closure procedure step 1",
        "canonical_path": str(CONTROL / "ACCEPTANCE_ROOTS_v3.json"),
        "model": "00_ARCHITECTURE/control/kalayantra/plan_model.json (every brief_spec and detector below is copied "
                 "from it and re-checked by fleet/kyclosure.py)",
        "supersedes": "ACCEPTANCE_ROOTS_v2_2.json (JOIN-ALL superseded by this file, A9 D-51)",
        "acceptances": acceptances,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[4]))
    ap.add_argument("--write-closure", action="store_true", help="also write CLOSURE_v3.json (main-checkout refresh only)")
    ns = ap.parse_args(argv)
    root = Path(ns.repo_root)
    model_path = root / CONTROL / "plan_model.json"
    model = apply_model_edits(json.loads(model_path.read_text(encoding="utf-8")))
    template = json.loads((root / CONTROL / "ACCEPTANCE_ROOTS_v2_2.json").read_text(encoding="utf-8"))
    roots = build_roots(model, template)
    first, second = (kyclosure.render(kyclosure.compute(model, roots)) for _ in range(2))
    if first != second:
        print("closure is not deterministic", file=sys.stderr)
        return 1
    model_path.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (root / CONTROL / "ACCEPTANCE_ROOTS_v3.json").write_bytes(kyclosure.render(roots))
    if ns.write_closure:
        (root / CONTROL / "CLOSURE_v3.json").write_bytes(first)
    closure = json.loads(first)
    print(f"closure_count={closure['closure_count']} closure_sha256={closure['closure_sha256']} "
          f"file_sha256={hashlib.sha256(first).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
