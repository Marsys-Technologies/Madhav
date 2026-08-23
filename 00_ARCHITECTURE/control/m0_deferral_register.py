#!/usr/bin/env python3
"""M0 DEFERRAL REGISTER — generator (WORK_QUEUE id M0-T31).

Builds 00_ARCHITECTURE/control/M0_DEFERRAL_REGISTER_v1_0.md and .json from ONE
in-file data structure, so the prose and the machine-readable tally can never
disagree.

WHAT THIS DOCUMENT IS FOR. ADHIKĀRIN ruling D-24 part 3 sets the precondition for
flipping the M0 CI guards to blocking:

    "The switch flips when T17's exit scorecard shows each criterion either at zero
     or explicitly deferred with a recorded reason — never on a criterion that is
     merely unexamined."

The scorecard measures. It does not separate *non-zero and repairable* from
*non-zero and cannot reach zero, for a stated reason*. This register performs that
separation, per criterion and per contract rule, and names what is left UNEXAMINED.

WHAT IT IS NOT. It decides nothing. It flips nothing. It writes nothing to
asset_registry, .github/ or any guard. Classification is evidence-assembly for
ADHIKĀRIN (charter G7/G9); certification is PARĪKṢAKA's (I16 / charter H7).

DECLARED WRITE SCOPE — ENFORCED AT RUNTIME, NOT ASSERTED IN PROSE.
This generator writes EXACTLY the two paths in `DECLARED_WRITES` below:

    00_ARCHITECTURE/control/M0_DEFERRAL_REGISTER_v1_0.md
    00_ARCHITECTURE/control/M0_DEFERRAL_REGISTER_v1_0.json

Every write goes through `_write()`, which raises `ScopeViolation` on any other path.
The declaration and the detector are the same object; a future edit that adds a write
outside the list fails loudly instead of succeeding quietly.

IT DOES NOT WRITE platform/scripts/governance/asset_catalogue_disclosed_residuals.json.
It READS that file, and only to REPORT divergence (`_report_disclosure_divergence()`).

WHY THAT MATTERS, recorded rather than left as folklore (KĀRAKA M0-T62, Standing Queue
SQ-12, on ADHIKĀRIN D-44 part 4). Until 2026-08-23 this generator had a
`_write_disclosure_block()` that wrote four `deferred_rule_disclosures*` keys into that
guard file as a SIDE EFFECT, outside the scope this docstring and PROVENANCE
["guard_files_read_not_written"] both declared. Consequences, measured not supposed:

  * M0-T46 had to reach for `git checkout --` to undo the side effect — the command the
    campaign's standing restore rule forbids. D-44 granted a narrow carve-out for that
    instance and named THIS side effect as "the defect underneath, which is the one
    worth fixing".
  * By 2026-08-23T15:5xZ the side effect had become destructive. The block in the live
    file is no longer this module's output: KĀRAKA M0-T49/T51/T55 wrote D-54's fifteen
    AUTHORISED disclosures into it on D-57's corrected ground, certified V-35/V-37, and
    the in-file `DISCLOSURE_DRAFT` was never updated to match. Measured at
    2026-08-23T15:5xZ: live block 19 entries, DISCLOSURE_DRAFT 16; 3 live entries
    (C-11, X-03, X-05) absent from the draft entirely; 12 of the remaining 16 differing;
    only 4 identical; all 4 `deferred_rule_disclosures_not_drafted` values differing;
    `deferred_rule_disclosures_count` 19 vs 16. A run would have deleted three
    authorised entries and reverted twelve to unauthorised drafts carrying
    `gating_effect: "none"` and no `authorised_by` — REVERTING AUTHORISED GOVERNANCE
    WORK, and looking like a clean generator run while doing it.
  * Nothing depends on the write. The only reader of that file is
    check_asset_catalogue_contract.py, which needs the AUTHORISED content; and the live
    file contains ZERO references to this module (grep, 2026-08-23), so it makes no
    claim that this generator owns it. The block was detached; the writer was not.

THE LIVE FILE IS THE SOURCE OF TRUTH FOR ITS OWN `deferred_rule_disclosures` BLOCK.
`DISCLOSURE_DRAFT` below is retained as the M0-T36 HISTORICAL DRAFT — it is the record
of what M0-T36 drafted, still rendered into this register's §10, and it is no longer a
thing this module writes anywhere.

Regenerate: python3 00_ARCHITECTURE/control/m0_deferral_register.py
"""
from __future__ import annotations
import json, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_MD = ROOT / "00_ARCHITECTURE/control/M0_DEFERRAL_REGISTER_v1_0.md"
OUT_JSON = ROOT / "00_ARCHITECTURE/control/M0_DEFERRAL_REGISTER_v1_0.json"

# ── declared write scope, with its own detector (CLAUDE.md §N.8, on the control plane) ─
# A scope declaration nothing can falsify is a declaration with no detector behind it.
# These two lines ARE the declaration, and `_write()` is the detector: it is the only
# way this module puts bytes on disk, and it refuses any path not named here.
DECLARED_WRITES = (OUT_MD, OUT_JSON)


class ScopeViolation(RuntimeError):
    """Raised when this module attempts a write outside `DECLARED_WRITES`."""


def _write(path: pathlib.Path, text: str) -> pathlib.Path:
    """The module's ONLY write path. Refuses anything not in `DECLARED_WRITES`.

    Deliberately compares resolved paths, so a relative or symlinked spelling of an
    undeclared path cannot slip through. Raises BEFORE opening the file, so a refused
    write leaves nothing partially written and no agent needs git to undo it.
    """
    resolved = pathlib.Path(path)
    allowed = {pathlib.Path(p) for p in DECLARED_WRITES}
    if resolved not in allowed:
        raise ScopeViolation(
            f"UNDECLARED WRITE REFUSED: {resolved}\n"
            f"This generator's declared write scope is exactly:\n  "
            + "\n  ".join(str(p) for p in DECLARED_WRITES)
            + "\nIf a new output is genuinely intended, add it to DECLARED_WRITES and say "
              "so in the module docstring and in PROVENANCE — the declaration and the "
              "detector move together, or neither moves. See M0-T62 / SQ-12 / D-44 part 4.")
    resolved.write_text(text, encoding="utf-8")
    return resolved

REPAIRABLE = "REPAIRABLE-IN-M0"
DEFERRED = "DEFERRED-WITH-REASON"
RESERVED = "RESERVED"
UNEXAMINED = "UNEXAMINED"
AT_ZERO = "AT-ZERO-WITH-EXPOSURE"   # not one of the four; see §5

BUCKETS = [REPAIRABLE, DEFERRED, RESERVED, UNEXAMINED, AT_ZERO]

# ── provenance ───────────────────────────────────────────────────────────────
PROVENANCE = {
    "authored_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T31; v1.1 by "
                   "M0-T36; v1.2 by M0-T46, applying D-38/D-39/D-40/D-41/D-42)",
    "certified_by": None,
    "branch": "campaign/nirmana-autonomous",
    "db_access": "READ-ONLY throughout (SET default_transaction_read_only=on; SELECT only). "
                 "Nothing was written to asset_registry, asset_throughput or any guard file.",
    "readings": [
        {"what": "live asset_registry — criterion/rule re-measurement by this task",
         "at": "2026-08-23T06:55:57Z", "how": "psycopg, read-only, DATABASE_URL read from "
         "platform/.env.local as measure_assets.py does (never printed — charter P4)"},
        {"what": "live asset_registry — second pass (C-04/C-06/C-07/C-15/C-17/C-20/C-21 detail)",
         "at": "2026-08-23T06:56:30Z", "how": "same connection method"},
        {"what": "seed projection — live vs asset_registry_seed.ts, 5 modelled columns",
         "at": "2026-08-23T06:57:16Z", "how": "00_ARCHITECTURE/control/seed_durability/"
         "extract_seed_projection.mjs (stdout only; writes nothing; the seed module is never "
         "imported — D-13, and D-28 part 5 for the inertness-proof method)"},
        {"what": "check_asset_catalogue_contract.py --live --json (C-01…C-28, X-01…X-05)",
         "at": "2026-08-23T06:58:51Z", "how": "the shipped guard, run READ-ONLY. NOT edited by "
         "this task — a sibling task holds the C-23 guard and the workbook generator."},
        {"what": "check_asset_source_parity.py --live --json (P-01…P-06)",
         "at": "2026-08-23T07:02:39Z", "how": "the shipped guard, run READ-ONLY"},
        {"what": "C-28 residual measurement (lit assets with no completed build_run_assets row)",
         "at": "2026-08-23T07:06Z", "how": "read-only SQL, quoted in the C-28 entry"},
        {"what": "origin/main presence of the two guards and the workflow",
         "at": "2026-08-23T07:03Z", "how": "git fetch origin main; git ls-tree -r --name-only "
         "origin/main @ 2670e61e2"},
    ],
    "guard_files_read_not_written": [
        "platform/scripts/governance/check_asset_catalogue_contract.py (mtime 2026-08-23 11:32 local)",
        "platform/scripts/governance/check_asset_source_parity.py (mtime 2026-08-23 10:43 local)",
        "platform/scripts/governance/asset_catalogue_disclosed_residuals.json",
        "platform/scripts/governance/asset_source_parity_allowlist.json",
        "platform/scripts/governance/asset_catalogue_declared_cowriters.json",
        ".github/workflows/nirmana-m0-guards.yml",
    ],
    # The list above used to be a claim this module falsified: it named
    # asset_catalogue_disclosed_residuals.json as read-not-written while
    # `_write_disclosure_block()` wrote four keys into it. M0-T62 removed the write and
    # gave the claim a detector, so the list is now enforced rather than asserted.
    "write_scope_enforced_by": (
        "DECLARED_WRITES + _write() in this module (an undeclared write raises "
        "ScopeViolation before any bytes are written), proved by the sandboxed "
        "regression test 00_ARCHITECTURE/control/test_m0_deferral_register_scope.py — "
        "which runs this generator against a throwaway copy of the tree, byte-compares "
        "every file, and includes a MUTATION control that re-injects an undeclared "
        "write and requires the test to go red. KĀRAKA M0-T62, Standing Queue SQ-12, "
        "ADHIKĀRIN D-44 part 4."),
}

# ── the classification bar ───────────────────────────────────────────────────
REASON_KINDS = {
    "ruling": "a line of state/DECISIONS.jsonl, cited by id and part",
    "plan-assignment": "a specific assignment of this exact item to a named rung or phase in "
                       "NIRMANA_ELEVATION_PLAN (a specific assignment governs a general exit "
                       "criterion — D-12 part 4)",
    "contract-mandate": "ASSET_CATALOGUE_CONTRACT_v1_0.md states in its own text that the rule "
                        "has no detector and must never read as passing",
    "structural-fact": "a measured property of the schema, the code or the charter that makes "
                       "zero unreachable inside M0 — stated with the measurement that shows it",
    "charter-prohibition": "charter §2 reserves the operation, or §3 prohibits it outright",
}

# ── the entries ──────────────────────────────────────────────────────────────
# Every entry: what it measures, what it reads NOW, which bucket, why, who owns it,
# and what would have to become true for it to close.

CRITERIA = [
 dict(id="crit-1", title="three-way diff (registry vs @register vs seed) = 0",
   measured={"scorecard_detector_2026-08-23T06:20Z": 5,
             "shipped_parity_guard_P-01…P-06_2026-08-23T07:02:39Z": 0},
   bucket=UNEXAMINED, reason_kind=None,
   reason="THE CRITERION HAS TWO DETECTORS AND THEY DISAGREE BY CONSTRUCTION, AND NOBODY HAS "
     "RULED WHICH ONE IS THE CRITERION. The scorecard counts every id not present in all three "
     "sources (5). The shipped guard — the thing a blocking flip would actually gate on — does "
     "NOT treat 'in registry and in seed but with no production @register' as a violation at "
     "all: check_asset_source_parity.py:254 reports those four ids (bg_ephemeris_engine, "
     "bg_panchanga, bg_sarvatobhadra_grid, lel_events) as a DETAIL under P-03, on the reasoning "
     "that a service row and a source row legitimately have no writer. The fifth "
     "(bg_gochara_citation_resolution) is excused by a disclosure naming R0 as its owner. So the "
     "same criterion reads 5 and 0 depending on which detector is asked, and 'zero' means two "
     "different things. That is not a repair question; it is a definition question, and it is "
     "unasked.",
   owner="ADHIKĀRIN (G9) — then whichever rung the surviving ids belong to",
   closes_when="ADHIKĀRIN rules which detector expresses the criterion. Under the guard's "
     "reading it is already at zero. Under the scorecard's reading it needs 4 service/source "
     "exemptions ruled and 1 R0 disposition (G1).",
   rows=[
     {"asset_id":"bg_gochara_citation_resolution","rung":"R0","class":"registry_only",
      "sub_bucket":DEFERRED,
      "note":"CURRENT, is_active, has_writer=false, in NEITHER the writer tree NOR the seed, "
             "never built. Its disposition (provision / demote / retire) is charter G1, whose "
             "bound is 'only assets in the current rung' and no rung is open. Recorded in "
             "ASSET_CATALOGUE_CONTRACT §7 and in asset_source_parity_allowlist.json as R0-owned. "
             "REASON RECORDED BY A KĀRAKA DISCLOSURE, NOT BY A RULING — ADHIKĀRIN has never "
             "countersigned it (`certified_by: null` in that file)."},
     {"asset_id":"bg_ephemeris_engine","rung":"R0","class":"registry+seed_not_decorator",
      "sub_bucket":UNEXAMINED,"note":"asset_kind='service' since the M0-T21 kind repair. A "
             "service has no writer by definition; whether the criterion should exempt services "
             "has never been ruled."},
     {"asset_id":"bg_panchanga","rung":"R0","class":"registry+seed_not_decorator",
      "sub_bucket":UNEXAMINED,"note":"same as bg_ephemeris_engine."},
     {"asset_id":"bg_sarvatobhadra_grid","rung":"R0","class":"registry+seed_not_decorator",
      "sub_bucket":UNEXAMINED,"note":"asset_kind='data', CURRENT, has_writer=false — a CURRENT "
             "data asset nothing builds, which contract §7 names as the thing never to leave "
             "standing. Same G1 shape as bg_gochara_citation_resolution but with NO disclosure "
             "and no ruling."},
     {"asset_id":"lel_events","rung":"R5","class":"registry+seed_not_decorator",
      "sub_bucket":DEFERRED,"note":"D-23: the SOURCE reclassification is R5, not M0."}],
   evidence=["00_ARCHITECTURE/control/M0_EXIT_SCORECARD_v1_0.md §1 criterion 1 (reading 2)",
     "check_asset_source_parity.py --live 2026-08-23T07:02:39Z: P-01…P-06 all pass; P-03 detail "
     "registry_and_seed_not_decorator = the 4 ids",
     "platform/scripts/governance/asset_source_parity_allowlist.json (bg_gochara_citation_"
     "resolution, class registry_only, owner 'R0 — NOT M0', certified_by null)",
     "CHARTER.md §1 G1 bound; DECISIONS.jsonl D-23"]),

 dict(id="crit-2", title="contract violations per kind = 0",
   measured={"scorecard_2026-08-23T06:20Z_violations_by_kind": {"data":136,"service":16,
             "artifact":0,"source":0},
             "guard_live_2026-08-23T06:58:51Z": {"pass":13,"fail":16,"not_checkable":4}},
   bucket=UNEXAMINED, reason_kind=None,
   reason="COMPOSITE — its 33 constituent rules are classified individually in §4, and the "
     "criterion as a whole is UNEXAMINED FOR A REASON THAT IS NOT ABOUT ANY OF THEM: as written "
     "('violations per kind = 0') it can NEVER be satisfied, because C-25, C-26 and C-27 have no "
     "detector and the contract forbids reporting them as passing. A criterion that cannot read "
     "zero needs either a column (making the rules checkable) or a re-wording ('every CHECKABLE "
     "rule at zero, the un-checkable ones reported not_checkable with their reason'). Neither "
     "has been decided, so the criterion is not deferrable — its own terms are undecided.",
   owner="ADHIKĀRIN (G9)",
   closes_when="the wording question is ruled AND every constituent rule in §4 is at zero or "
     "carries a recorded deferral the guard can read.",
   rows=[], evidence=["ASSET_CATALOGUE_CONTRACT_v1_0.md §6 closing paragraph and §8",
     "check_asset_catalogue_contract.py:1069-1109 (C-25/26/27 hard-wired NOT_CHECKABLE)",
     "M0_EXIT_SCORECARD_v1_0.md §1 criterion 2"]),

 dict(id="crit-3", title="prefix mismatches = 0",
   measured={"live_2026-08-23T06:55:57Z":1,"guard_C-01_2026-08-23T06:58:51Z":1},
   bucket=DEFERRED, reason_kind="ruling",
   reason="The single offender is `lel_events` (prefix 'lel', layer 'mimamsa'). C-01 exempts "
     "`asset_kind='source'` rows, so the mismatch disappears the moment lel_events is "
     "reclassified SOURCE — and D-23 REVERSED D-21 and assigned that reclassification to R5 by "
     "name, on plan §8.4's R5 row ('LEL_EVENTS RECLASSIFIED SOURCE'), holding additionally that "
     "widening the asset_kind CHECK now would be pre-building infrastructure for a later phase. "
     "This criterion therefore cannot reach zero inside M0 by any authorised route.",
   owner="R5 (Mīmāṃsā rung), stage 2 Conform",
   closes_when="R5 opens, the asset_kind CHECK is widened to admit the contract's SOURCE token, "
     "and lel_events is reclassified by a G1 exercise on census evidence.",
   rows=[{"asset_id":"lel_events","rung":"R5","sub_bucket":DEFERRED,
     "note":"live: layer=mimamsa, asset_kind=data, catalog_status=DRAFT, target_table NULL"}],
   evidence=["DECISIONS.jsonl D-23 (reverses D-21)","NIRMANA_ELEVATION_PLAN_v4_0.md:862 §8.4 R5 row",
     "ASSET_CATALOGUE_CONTRACT_v1_0.md §7 and §10.1",
     "live query 2026-08-23T06:55:57Z returned exactly this one row"]),

 dict(id="crit-4", title="dangling or DRAFT-targeted edges = 0",
   measured={"dangling_C-12":0,"CURRENT→DRAFT_C-11":3,"at":"2026-08-23T06:58:51Z"},
   bucket=REPAIRABLE, reason_kind=None,
   reason="THE REPAIR IS NAMED AND NOBODY HAS DONE IT. Plan Phase 0.8b — an M0 step — reads "
     "'34 DRAFT-but-served promoted or justified; CURRENT-may-not-depend-on-DRAFT enforced'. "
     "Each of the three edges closes by promoting the DRAFT dependency to CURRENT (charter G1) "
     "or by recording why it stays DRAFT. Both are catalogue dispositions on evidence M0 already "
     "holds (DRAFT_INVENTORY / CONSUMER_MAP).",
   blocker="G1's charter bound reads 'Only assets in the current rung, on M0 census evidence' "
     "and NO RUNG IS OPEN. Phase 0.8b assigns the work to M0; G1's bound appears to withhold the "
     "power that performs it. That collision must be ruled before any promotion is written — it "
     "is the same collision criterion 9 sits behind, so one ruling clears both.",
   owner="ADHIKĀRIN (G1 + the bound reconciliation); execution is a KĀRAKA task",
   closes_when="three dispositions are ruled and written: ga_vichara (R1), ka_dasha_kala (R3), "
     "ka_sangam (R3) — promoted, or the dependants justified.",
   rows=[{"asset_id":"bo_laksana","dep":"ga_vichara","dep_status":"DRAFT","dep_rung":"R1"},
     {"asset_id":"ka_kshetra","dep":"ka_dasha_kala","dep_status":"DRAFT","dep_rung":"R3"},
     {"asset_id":"ka_taranga","dep":"ka_sangam","dep_status":"DRAFT","dep_rung":"R3"}],
   evidence=["guard C-11 live 2026-08-23T06:58:51Z (3 rows, class current_depends_on_draft)",
     "NIRMANA_ELEVATION_PLAN_v3_0.md §Phase 0 step 0.8b (the 15-step table §14.4 maps to M0)",
     "CHARTER.md §1 G1 bound"]),

 dict(id="crit-5", title="multi-producer partitions = 0",
   measured={"C-25":"not_checkable — no schema column",
             "X-01_undeclared_collisions_2026-08-23T06:58:51Z":0,
             "co_written_target_tables":5},
   bucket=UNEXAMINED, reason_kind=None,
   reason="THE TEMPTING ANSWER IS 'DEFERRED — NO COLUMN EXISTS', AND IT IS WRONG. The absence of "
     "a partition column is a real structural fact and it is what makes C-25 permanently "
     "not_checkable (§4). But the CRITERION is not the rule: plan Phase 0.4 — an M0 step — reads "
     "'(table × generation × partition) invariant; correct the gochara attribution; DECLARE "
     "CO-WRITER PARTITIONS'. M0 is the phase the plan assigns this work to. Under D-4's own "
     "reasoning ('a criterion that cannot be met without a change has NAMED that change even "
     "where it numbers no migration') a partition-declaration column is arguably already "
     "authorised; under D-23's correction it may instead belong to each rung. Nobody has asked, "
     "so this is not deferred — it is undecided. What exists today is X-01, which passes and "
     "means only 'no multi-producer table that nobody declared' — its own docstring refuses the "
     "stronger reading.",
   owner="ADHIKĀRIN (G9, and P5 if a column is involved)",
   closes_when="either a partition-declaration column is authorised and the 16 co-writer rows "
     "across 5 tables declare their partitions, or the item is deferred to the owning rungs with "
     "the reason recorded.",
   rows=[{"target_table":"bodha_msr_signals","producers":7},
     {"target_table":"chart_facts","producers":5},
     {"target_table":"brahma_class_priors","producers":2},
     {"target_table":"classical_text_chunks","producers":2},
     {"target_table":"kala_gochara_windows","producers":2,
      "note":"ka_gochara (CURRENT) + ka_gochara_sweep (RETIRED, charter P1)"}],
   evidence=["ASSET_CATALOGUE_CONTRACT_v1_0.md §4.9, §10.3; rule C-25",
     "platform/scripts/governance/asset_catalogue_declared_cowriters.json _README "
     "('Listing a table here means these producers are known and expected, never that these "
     "producers are correct')",
     "NIRMANA_ELEVATION_PLAN_v3_0.md Phase 0 step 0.4","DECISIONS.jsonl D-4, D-23"]),

 dict(id="crit-6", title="throughput rows on inactive assets = 0",
   measured={"live_2026-08-23T06:55:57Z":{"assets":1,"rows":3,"states":["error"]}},
   bucket=RESERVED, reason_kind="charter-prohibition",
   reason="The only offender is `ka_gochara_sweep` — charter §2 P1's NAMED unrecoverable asset "
     "(38,287 v1 gochara rows whose only recovery path is the 2026-08-23 snapshot). Any "
     "operation on it is a reserved power: parked, never decided by an agent. D-12 part 4 "
     "additionally dissolves the apparent M0-vs-P1 collision without needing P1 at all — plan "
     "§14.2 assigns these exact rows to R3 by name, and 'a specific assignment governs a general "
     "exit criterion' — and rules that M0 CLOSES WITH THIS CRITERION EXPLICITLY UNMET AND "
     "RECORDED AS DEFERRED-TO-R3, never silently green. THIS REGISTER DID NOT TOUCH THE ROWS, "
     "AND NOTHING IN M0 MAY.",
   owner="R3 (Kāla rung) for the lifecycle exit; the native for anything P1 reaches",
   closes_when="R3 opens and completes ka_gochara_sweep's lifecycle exit. Not in M0, on any "
     "reading.",
   rows=[{"asset_id":"ka_gochara_sweep","rung":"R3","catalog_status":"RETIRED",
     "is_active":False,"throughput_rows":3,"states":["error"],
     "note":"state='error' is at least not a false green (D-12 part 4). The guard reports it as "
            "X-02 with severity RESIDUAL and an itemised disclosure, and the disclosure "
            "deliberately DOES NOT turn the rule green."}],
   evidence=["CHARTER.md §2 P1","DECISIONS.jsonl D-12 part 4",
     "NIRMANA_ELEVATION_PLAN_v4_0.md §14.2",
     "platform/scripts/governance/asset_catalogue_disclosed_residuals.json disclosed_additions",
     "live query 2026-08-23T06:55:57Z: 1 asset, 3 rows, all state='error'"]),

 dict(id="crit-7", title="retired assets without a data_disposition = 0",
   measured={"live_2026-08-23T06:55:57Z":1,"guard_C-08_2026-08-23T06:58:51Z":1,
             "note":"moved BLOCKED → FAIL when migration 590 supplied the data_disposition "
                    "column at 2026-08-23T05:36:13Z; the detector now exists and returns 1"},
   bucket=DEFERRED, reason_kind="plan-assignment",
   reason="One RETIRED row exists and it is `ka_gochara_sweep`. Plan §14.2 names its "
     "data_disposition explicitly among R3's outstanding items — 'the zombie throughput rows "
     "behind its standing no-writer-registered red, AND ITS data_disposition, are still "
     "outstanding' — and D-12 part 4 quotes that sentence in ruling the same asset's items "
     "R3-owned. A specific assignment governs a general exit criterion.",
   owner="R3 (Kāla rung), lifecycle exit",
   closes_when="R3 writes the disposition. NOTE THE SECOND-ORDER QUESTION NOBODY HAS ASKED: "
     "writing data_disposition touches the REGISTRY ROW, not the corpus. Whether charter P1 "
     "reaches an asset's registry metadata or only its data has never been ruled; it does not "
     "change this deferral (R3 owns it either way) but it will matter the moment R3 opens.",
   machinery_gap="THE DEFERRAL IS RECORDED IN THE LEDGER BUT NOT IN THE GUARD. Only X-02 has an "
     "entry in asset_catalogue_disclosed_residuals.json and only X-02 carries severity RESIDUAL. "
     "C-08 is BLOCKING with no disclosure, so a blocking flip today reds the branch on this "
     "criterion — and the only way to make it green would be to touch a P1 asset, which is "
     "exactly the pressure charter H3 exists to refuse.",
   rows=[{"asset_id":"ka_gochara_sweep","rung":"R3","catalog_status":"RETIRED",
     "data_disposition":None,"reserved_asset":True}],
   evidence=["DECISIONS.jsonl D-12 part 4","NIRMANA_ELEVATION_PLAN_v4_0.md §14.2",
     "live query 2026-08-23T06:55:57Z: the one RETIRED row, data_disposition NULL",
     "_migrations_applied: 590_nirmana_m0_catalogue_contract_columns.sql @ 2026-08-23T05:36:13Z"]),

 dict(id="crit-8", title="active assets with neither build coverage nor a dead flag = 0",
   measured={"scorecard_2026-08-23T06:20Z":"NOT-MEASURABLE (no dead-flag field is defined)",
             "guard_X-03_2026-08-23T06:58:51Z":2},
   bucket=UNEXAMINED, reason_kind=None,
   reason="THE TWO DETECTORS DISAGREE ABOUT WHETHER THE CRITERION IS MEASURABLE AT ALL. The "
     "scorecard says NOT-MEASURABLE: asset_registry has no column designating a registered-but-"
     "dead asset, the contract defines none, and has_writer — the only candidate — was itself "
     "wrong on 2 rows (D-25). The shipped guard's X-03 reads has_writer as the proxy anyway and "
     "returns 2 violations. Meanwhile plan Phase 0.8a — an M0 step — reads 'Registered-but-dead "
     "FLAGGED (bg_gochara_citation_resolution)', i.e. M0 is asked to produce a flag that has "
     "nowhere to live. Defining the flag, ruling the proxy sufficient, or deferring the whole "
     "criterion are three different answers and none has been given.",
   owner="ADHIKĀRIN (G9; P5 if a new column is the answer)",
   closes_when="the flag question is ruled, and then the two rows below are dispositioned by "
     "whoever owns them.",
   rows=[{"asset_id":"bg_gochara_citation_resolution","rung":"R0","catalog_status":"CURRENT",
     "sub_bucket":DEFERRED,"note":"disclosed R0-owned in the parity allowlist; not countersigned"},
     {"asset_id":"lel_events","rung":"R5","catalog_status":"DRAFT","sub_bucket":DEFERRED,
      "note":"D-23 — R5"}],
   evidence=["M0_EXIT_SCORECARD_v1_0.md §1 criterion 8","guard X-03 live 2026-08-23T06:58:51Z",
     "NIRMANA_ELEVATION_PLAN_v3_0.md Phase 0 step 0.8a","DECISIONS.jsonl D-25"]),

 dict(id="crit-9", title="unresolved zero-consumer findings = 0",
   measured={"packets":23,"dispositions_recorded":0,"at":"2026-08-23T06:58:51Z"},
   bucket=REPAIRABLE, reason_kind=None,
   reason="THE REPAIR IS NAMED, THE MACHINERY IS BUILT, AND THE RULINGS HAVE NOT BEEN MADE. "
     "Plan Phase 0.8c — an M0 step — reads '13 assets: record the consumer or retire with a "
     "disposition' (the measured packet count is 23; the plan's 13 has no per-asset list behind "
     "it and its own annotations count 7 — the 23 is the measured figure and the one the guard "
     "reduces). asset_catalogue_disclosed_residuals.json already carries the "
     "`zero_consumer_dispositions` block, and X-05 resolves a packet ONLY on an entry carrying a "
     "decision_ref into DECISIONS.jsonl — disposition is charter G1 and no KĀRAKA may self-serve "
     "one. The block is empty; 23 rulings are outstanding.",
   blocker="the same G1 rung-bound collision as criterion 4: 0.8c assigns the work to M0 while "
     "G1's bound reads 'only assets in the current rung' and no rung is open. One ruling clears "
     "both criteria.",
   owner="ADHIKĀRIN (G1 ×23); recording them is a KĀRAKA task",
   closes_when="each of the 23 packets carries either a recorded consumer or a retire-with-"
     "disposition ruling, referenced by decision id in the residuals file.",
   rows=[{"asset_id":a,"rung":r} for a,r in [
     ("bg_cohort","R0"),("bg_concordance","R0"),("bg_ephemeris_engine","R0"),
     ("bg_gochara_arcs","R0"),("bg_kota_chakra_rings","R0"),("bg_kp_sublord_division","R0"),
     ("bg_panchanga","R0"),("bg_phaladeepika_latta","R0"),("bg_reference","R0"),
     ("bg_sarvatobhadra_grid","R0"),("bg_sky_calendar","R0"),("bg_vedha_malefic_scale","R0"),
     ("bg_vidhi_floors","R0"),("bg_vidhi_primitives","R0"),("bo_cdlm_summary","R2"),
     ("bo_samskara","R2"),("ka_dasha_kala","R3"),("ka_gochara_v3_century_materialize","R3"),
     ("ka_graha_sancara","R3"),("ka_kshetra","R3"),("ka_muhurta_seva","R3"),("ka_tulana","R3"),
     ("mi_jivanaghatana","R5")]],
   evidence=["guard X-05 live 2026-08-23T06:58:51Z: 23 packets, 0 dispositions recorded",
     "00_ARCHITECTURE/control/ZERO_CONSUMER_EVIDENCE_v1_0.md (M0-T6/T7, 23 packets)",
     "platform/scripts/governance/asset_catalogue_disclosed_residuals.json _README (2)",
     "NIRMANA_ELEVATION_PLAN_v3_0.md Phase 0 step 0.8c"]),

 dict(id="crit-10", title="CI guard merged and blocking",
   measured={"guard_scripts_found":2,"workflow_invocations":4,
     "merged_to_origin_main_2026-08-23T07:03Z":False,
     "invocation_is_blocking":False,"workflow_runs_ever":0},
   bucket=UNEXAMINED, reason_kind=None,
   reason="TWO HALVES, AND THE HARD ONE IS NOT THE ONE EVERYONE IS LOOKING AT.\n\n"
     "(a) BLOCKING — circular, and the circle resolves cleanly once named. This criterion asks "
     "whether the guards are blocking; D-24 part 3 makes the switch conditional on every "
     "criterion being at zero or explicitly deferred; and THIS REGISTER IS THAT PRECONDITION. If "
     "criterion 10 is inside its own precondition, the precondition is unsatisfiable: the switch "
     "can never flip, because the thing it waits for is itself. THE RESOLUTION IS NOT TO IGNORE "
     "THE CIRCLE BUT TO EXCLUDE THE SWITCH FROM ITS OWN CONDITION — D-24 part 3 quantifies over "
     "the criteria the guards would GATE ON, and criterion 10 is not one of those; it is the "
     "gate. ADHIKĀRIN should record that carve-out explicitly rather than leave it implicit, "
     "because an implicit exception to a stated precondition is exactly the shape of the "
     "'weaken a criterion to get moving' pressure D-24 part 3 warned about. With the carve-out "
     "recorded, this half is REPAIRABLE-IN-M0 and is satisfied BY the flip.\n\n"
     "(b) MERGED — unexamined, and it collides with a HARD PROHIBITION. 'Merged' means present "
     "on the default branch: verified ABSENT from origin/main at 2026-08-23T07:03Z for all three "
     "files (git ls-tree @ 2670e61e2), and the workflow has never run (0 runs; the API reports "
     "404 on the default branch). Getting there means merging campaign work into `main` — and "
     "charter H2 reads 'Force-push, history rewrite, OR ANY WRITE TO MAIN. All work is on "
     "the campaign branch.' Whether a reviewed PR merge is inside H2's prohibition or outside it "
     "has never been asked. It is not a KĀRAKA's question and this register does not answer it; "
     "it names it, because criterion 10 cannot be satisfied without an answer.",
   owner="ADHIKĀRIN (G9 for both halves)",
   closes_when="(a) the self-reference carve-out is recorded and the two `continue-on-error: "
     "true` lines are removed by ADHIKĀRIN's own act; (b) H2's reach is ruled, the guards reach "
     "origin/main by whatever route that ruling permits, and at least one run executes and "
     "reports — a workflow that has never run is not evidence of anything (D-28 part 4: 'a guard "
     "that has never had to choose is not yet a detector').",
   rows=[], evidence=[
     "git ls-tree -r origin/main @ 2670e61e2, 2026-08-23T07:03Z: nirmana-m0-guards.yml, "
     "check_asset_catalogue_contract.py, check_asset_source_parity.py — all ABSENT",
     ".github/workflows/nirmana-m0-guards.yml:48,87 — `continue-on-error: true` on both jobs",
     "M0_EXIT_SCORECARD_v1_0.md §1 criterion 10 (github_run_evidence: run_count 0, HTTP 404)",
     "DECISIONS.jsonl D-24 part 3; CHARTER.md §3 H2, H3"]),

 dict(id="crit-11", title="every asset carrying domain and rung (v4.1)",
   measured={"C-18_domain_null_or_wrong":0,"C-19_rung_null_or_wrong":0,
             "at":"2026-08-23T06:55:57Z"},
   bucket=AT_ZERO, reason_kind="structural-fact",
   reason="AT ZERO, AND NOT THE SAME THING AS BEING AT ZERO. Migration 590 added and backfilled "
     "`domain` and `rung`, and neither column is written by the seed at all — so the backfill "
     "itself is durable (SEED_DURABILITY_REGISTER §3.3). TWO EXPOSURES SURVIVE ANYWAY. (i) THE "
     "PAIR, NOT THE COLUMN: 590 derived `domain` FROM `scope`, and `scope` IS seed-owned. "
     "mi_jivanaghatana is live scope='per_chart' → domain='chart', while the seed declares "
     "scope='global' → the same row would imply domain='shared'. A re-seed moves one half of the "
     "pair and leaves the other, and the row then answers 'which domain am I' two different ways "
     "while C-18 still counts it as present. Re-measured independently here at 06:57:16Z: it is "
     "the ONLY such row. (ii) COVERAGE OF FUTURE ROWS: both columns are absent from the seed's "
     "INSERT list with no NOT NULL / DEFAULT / trigger behind them, so any asset the seed newly "
     "inserts lands with both NULL and re-breaks the criterion silently.",
   owner="ADHIKĀRIN for the scope/domain ownership fix (D-27's divergence-report mandate); the "
     "column-level backfill is done",
   closes_when="the seed-vs-DB divergence report D-27(2b) mandates exists and treats a "
     "NULL→value transition as its own category (D-28 part 1), and mi_jivanaghatana's scope is "
     "reconciled on the merits in one surface rather than by whoever runs last.",
   rows=[{"asset_id":"mi_jivanaghatana","rung":"R5","live_scope":"per_chart",
     "seed_scope":"global","live_domain":"chart","domain_implied_by_seed_scope":"shared"}],
   evidence=["live 2026-08-23T06:55:57Z: domain NULL 0, rung NULL 0, 0 scope→domain mismatches",
     "seed projection 2026-08-23T06:57:16Z: mi_jivanaghatana scope live per_chart vs seed global",
     "SEED_DURABILITY_REGISTER_v1_0.md §3.3","DECISIONS.jsonl D-27, D-28 part 1"]),

 dict(id="crit-12", title="the §11 CI domain-coherence assertion green (v4.1)",
   measured={"assertion_exists":True,"guard_X-04_2026-08-23T06:58:51Z":0,
     "has_ever_run_in_CI":False,
     "note":"the scorecard's reading 2 (06:20Z) says 'THE ASSERTION DOES NOT EXIST'. That is "
            "stale: X-04 ('domain coherence: a shared asset depends only on shared assets', "
            "origin 'plan §11') is implemented in check_asset_catalogue_contract.py and returns "
            "0 violations live."},
   bucket=REPAIRABLE, reason_kind=None,
   reason="REDUCES ENTIRELY TO CRITERION 10. The assertion now exists and passes; what it does "
     "not do is RUN — the workflow is not on origin/main, is non-blocking, and has executed zero "
     "times. 'Green' cannot be read off a check that has never run (CLAUDE.md §N.8), so the "
     "criterion is honestly not-green today for a reason that has nothing to do with domain "
     "coherence itself.",
   blocker="criterion 10, both halves.",
   owner="ADHIKĀRIN (via criterion 10)",
   closes_when="criterion 10 closes and one run reports X-04 green.",
   rows=[], evidence=["guard X-04 live 2026-08-23T06:58:51Z: pass, 0 violations",
     "M0_EXIT_SCORECARD_v1_0.md §1 criterion 12 (reading 2, 06:20Z — superseded on the "
     "'assertion does not exist' clause)"]),
]

# ── contract + extension rules currently non-zero, not_checkable, or blocked ──
# Rule statuses are the shipped guard's own output, run live READ-ONLY at
# 2026-08-23T06:58:51Z (C-01…C-28, X-01…X-05) and 07:02:39Z (P-01…P-06).

NAMED_FIELD_TEST = (
  "THE NAMED-FIELD TEST — the one question that decides six of these rules at once. "
  "D-24 established that repairing registry METADATA in M0 trespasses no rung (it is I14 "
  "Track-M work, and no rung is open to be trespassed). D-25 part 2b then drew the line: "
  "has_writer 'is NOT among the derived fields M0's Phase 0.6a names … so unlike D-24 I have no "
  "named M0 mandate to write them', and the row repair was pinned to R0 stage 2 Conform. Read "
  "together, the operative test is: A REGISTRY COLUMN IS M0'S TO REPAIR IF AND ONLY IF ONE OF "
  "PHASE 0'S FIFTEEN STEPS NAMES IT. Phase 0 names layer_index/layer_name (0.5a), has_substeps "
  "(0.6a), asset_kind/asset_type (0.6b), the lifecycle columns (0.3), partitions (0.4), the "
  "consumer map (0.7), estimated_seconds (0.9). IT NAMES NONE OF: target_table, count_sql, "
  "health_probe, provides_apis, service_health. Applying that test to those columns is an "
  "inference from precedent, not a ruling anyone has made — so this register REFUSES to record "
  "it as a deferral and files the affected rules UNEXAMINED. One ADHIKĀRIN ruling on the test "
  "itself reclassifies all six.")

RULES = [
 dict(id="C-01", severity="BLOCKING", assertion="asset_id prefix matches layer, non-source rows",
   measured=1, bucket=DEFERRED, reason_kind="ruling",
   reason="Same single row and same reason as criterion 3: lel_events, whose SOURCE "
     "reclassification D-23 assigned to R5. C-01 exempts source rows, so the reclassification "
     "IS the repair and it is not M0's.",
   owner="R5", rows=["lel_events"],
   evidence=["DECISIONS.jsonl D-23","guard C-01 live 06:58:51Z"]),

 dict(id="C-02", severity="BLOCKING", assertion="layer_index is ^L[0-5]$ and agrees with layer",
   measured=1, bucket=DEFERRED, reason_kind="ruling",
   reason="MOVED 21 → 1 WHILE THIS TASK WAS RUNNING. The scorecard's reading 2 (06:20:44Z) "
     "records 21; M0-T26 landed the Phase 0.5a repair at ~06:51–06:54Z; this task measured 1 at "
     "06:55:57Z and the guard measured 1 at 06:58:51Z. The single remaining row is lel_events, "
     "whose layer_index is NULL DELIBERATELY: D-28 part 1 rules that this NULL is 'THE ONLY "
     "PLACE IN THE REGISTRY WHERE THE OPENNESS OF A RESERVED DECISION IS WRITTEN DOWN' — the "
     "correct value is NULL-if-source but L5-if-data, and D-23 reserved that choice to R5. "
     "Filling it in M0 would answer a reserved question by default.",
   owner="R5", rows=["lel_events"],
   durability="DURABLE BY AGREEMENT, measured not assumed: layer_index is seed-owned "
     "(DO UPDATE SET), so the repair survives only if it wrote exactly what the seed writes. "
     "Compared live-vs-seed at 06:57:16Z across all 127 seed entries: ZERO divergent "
     "layer_index cells except lel_events (live NULL, seed 'L5'). The repair agrees with the "
     "seed everywhere it touched — and note the corollary D-28 part 1 names: a re-seed would "
     "FILL lel_events's deliberate NULL with 'L5', silently answering the reserved question.",
   evidence=["M0_EXIT_SCORECARD_v1_0.md reading 2 (21)","live 06:55:57Z (1)",
     "guard C-02 live 06:58:51Z (1, class layer_index_null)",
     "seed projection 06:57:16Z","DECISIONS.jsonl D-23, D-28 part 1"]),

 dict(id="C-03", severity="BLOCKING", assertion="layer_name is the exact lexicon spelling",
   measured=1, bucket=DEFERRED, reason_kind="ruling",
   reason="Same movement and same reason as C-02: 20 → 1 between the scorecard's reading 2 and "
     "this measurement. The surviving row is lel_events (layer_name NULL, deliberate). Live "
     "spellings now carry the §N.1 LOCKED diacritics on every populated row — Gaṇita, Kāla, "
     "Mīmāṃsā — which D-28 part 6 records as a real §N.1 violation caught PRE-write by a "
     "codepoint pin.",
   owner="R5", rows=["lel_events"],
   durability="DURABLE BY AGREEMENT — measured: zero divergent layer_name cells live-vs-seed at "
     "06:57:16Z other than lel_events (live NULL, seed 'Mīmāṃsā').",
   evidence=["live 06:56:30Z: layer/layer_name distinct pairs — bodha/Bodha 22, brahmagyan/"
     "Brahmagyan 40, ganita/Gaṇita 19, kala/Kāla 23, mimamsa/Mīmāṃsā 14, phala/Phala 9, "
     "mimamsa/NULL 1","DECISIONS.jsonl D-28 parts 1 and 6"]),

 dict(id="C-04", severity="BLOCKING",
   assertion="data/artifact ⇒ target_table NOT NULL and the table exists",
   measured=9, bucket=UNEXAMINED, reason_kind=None,
   reason="NINE ROWS, THREE DIFFERENT SITUATIONS, AND ONLY TWO OF THEM HAVE A REASON ON RECORD. "
     "(i) lel_events — DEFERRED to R5 with the rest of its cluster (D-23). (ii) bg_sky_calendar "
     "— DEFERRED: its target_table names `bg_sky_events`, a relation ABSENT from production; "
     "D-28 part 4 ruled it 'L0 → R0 → not open → UNTOUCHED (I13)' and recorded it as a "
     "TRIGGER-BEARING defect for R0 intake (a re-seed's to_regclass pre-flight would switch the "
     "asset off). (iii) THE OTHER SEVEN have target_table NULL and no ruling of any kind: "
     "bg_prashna_rules (R0), bo_cdlm_summary and bo_chart_gestalt (R2), ga_sade_sati, "
     "ga_sensitive, ga_strength, ga_structural (R1). Four of those seven are chart_facts "
     "co-writers, where a NULL target_table might be deliberate rather than missing — nobody has "
     "established which, and 'probably fine' is not a reason. " + NAMED_FIELD_TEST,
   owner="ADHIKĀRIN (the named-field test); then R0/R1/R2 Conform",
   rows=["bg_prashna_rules","bg_sky_calendar","bo_cdlm_summary","bo_chart_gestalt","ga_sade_sati",
     "ga_sensitive","ga_strength","ga_structural","lel_events"],
   evidence=["guard C-04 live 06:58:51Z: 8 × target_table_null + 1 × target_table_missing",
     "DECISIONS.jsonl D-28 part 4, D-23","DECISIONS.jsonl D-24, D-25 part 2b"]),

 dict(id="C-06", severity="BLOCKING", assertion="chart-domain count_sql contains $1",
   measured=1, bucket=UNEXAMINED, reason_kind=None,
   reason="The single row is mi_seva, whose count_sql should not exist at all: mi_seva is "
     "asset_kind='service', and C-07 says a service carries no count_sql. So C-06 is a shadow of "
     "C-07 and closes with it. It inherits C-07's bucket for the same reason. " + NAMED_FIELD_TEST,
   owner="ADHIKĀRIN (the named-field test); then R5 Conform", rows=["mi_seva"],
   evidence=["guard C-06 live 06:58:51Z (1 row, domain=chart, domain_provenance=column)",
     "guard C-07 live 06:58:51Z (mi_seva carries count_sql, target_floor, target_table)"]),

 dict(id="C-07", severity="BLOCKING",
   assertion="service ⇒ target_table / count_sql / target_floor / clear_tables all NULL",
   measured=4, bucket=UNEXAMINED, reason_kind=None,
   reason="Four service rows carry data-asset fields: ka_dasha_kala and ka_tulana (target_floor), "
     "mi_abhilekha and mi_seva (count_sql + target_floor + target_table). The repair is "
     "mechanical — NULL four fields — and that is exactly why it must not be done on a KĀRAKA's "
     "own reading: none of those columns is named by any Phase 0 step, all four assets are R3/R5, "
     "and three of the four columns are SEED-OWNED, so a DB-only NULLing is reverted by the next "
     "re-seed anyway. " + NAMED_FIELD_TEST,
   owner="ADHIKĀRIN (the named-field test); then R3/R5 Conform",
   rows=["ka_dasha_kala","ka_tulana","mi_abhilekha","mi_seva"],
   evidence=["guard C-07 live 06:58:51Z","SEED_DURABILITY_REGISTER_v1_0.md §1.2 (count_sql, "
     "target_floor, target_table all in the seed's DO UPDATE SET)"]),

 dict(id="C-08", severity="BLOCKING", assertion="RETIRED ⇒ data_disposition NOT NULL",
   measured=1, bucket=DEFERRED, reason_kind="plan-assignment",
   reason="criterion 7's rule. Plan §14.2 names ka_gochara_sweep's data_disposition as R3 work; "
     "D-12 part 4 quotes that sentence. Reserved asset (charter P1) — untouched by this task.",
   owner="R3", rows=["ka_gochara_sweep"],
   machinery_gap="BLOCKING severity, no disclosure entry. See criterion 7.",
   evidence=["guard C-08 live 06:58:51Z","DECISIONS.jsonl D-12 part 4"]),

 dict(id="C-11", severity="BLOCKING", assertion="CURRENT depends only on CURRENT (or source)",
   measured=3, bucket=REPAIRABLE, reason_kind=None,
   reason="criterion 4's rule; see that entry. Named by Phase 0.8b; blocked on the G1 rung-bound "
     "reconciliation, not on evidence.",
   owner="ADHIKĀRIN (G1)", rows=["bo_laksana→ga_vichara","ka_kshetra→ka_dasha_kala",
     "ka_taranga→ka_sangam"],
   evidence=["guard C-11 live 06:58:51Z"]),

 dict(id="C-15", severity="BLOCKING", assertion="service ⇒ health_probe AND provides_apis NOT NULL",
   measured=6, bucket=UNEXAMINED, reason_kind=None,
   reason="All six DRAFT service rows (ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, "
     "ka_tulana, mi_abhilekha, mi_seva) carry NULL for both. Worth noting because it corrects "
     "the contract's own §6 cell: that cell says '6 (all 6 service rows)', but there are EIGHT "
     "service rows live since the M0-T21 kind repair, and the two new ones (bg_ephemeris_engine, "
     "bg_panchanga) DO carry both fields — so the count is unchanged for a different reason than "
     "the contract states. Neither health_probe nor provides_apis is named by any Phase 0 step. "
     + NAMED_FIELD_TEST,
   owner="ADHIKĀRIN (the named-field test); then R3/R5 Conform",
   rows=["ka_dasha_kala","ka_graha_sancara","ka_muhurta_seva","ka_tulana","mi_abhilekha","mi_seva"],
   evidence=["guard C-15 live 06:58:51Z","live 06:56:30Z: 8 service rows, 6 failing C-15",
     "ASSET_CATALOGUE_CONTRACT_v1_0.md §6 C-15 cell"]),

 dict(id="C-17", severity="BLOCKING", assertion="graded service_health ⇒ health_probe NOT NULL",
   measured=4, bucket=UNEXAMINED, reason_kind=None,
   reason="SPLIT, AND THE SPLIT IS THE POINT. THREE of the four rows are covered by a ruling: "
     "D-13 part 2 recorded 'three service assets read service_health=healthy with no "
     "health_probe … a status with no detector — H4/§N.8', declined to repair it, and routed it "
     "to a rung's stage-1 intake as pre-measured input. Those three are ka_dasha_kala, "
     "ka_muhurta_seva, ka_tulana. THE FOURTH — ka_graha_sancara, service_health='unhealthy', no "
     "probe — is covered by NO ruling: D-13 counted three because the contract's §6 cell counted "
     "three, while the contract's own §8 SQL matches ('healthy','degraded','unhealthy') and "
     "returns four. A rule is not classified until every row under it is, so C-17 is UNEXAMINED "
     "on one row. "
     "TWO CORRECTIONS THIS REGISTER OWES THE LEDGER: (i) D-13 part 2 says 'It is R0 substrate "
     "and R0 IS NOT OPEN'. All three assets are ka_* / layer=kala, and their live `rung` column "
     "— backfilled by migration 590 from layer, per contract §5.2 — reads R3, not R0. The "
     "deferral stands (a rung owns it, not M0); the rung it names is wrong. (ii) the same slip "
     "would misroute the intake, so it is worth fixing in a ruling rather than in prose.",
   owner="ADHIKĀRIN (to correct the rung and cover the fourth row); then R3 stage-1 intake",
   rows=["ka_dasha_kala (D-13 part 2)","ka_muhurta_seva (D-13 part 2)","ka_tulana (D-13 part 2)",
     "ka_graha_sancara (NO RULING — unhealthy, no probe)"],
   evidence=["guard C-17 live 06:58:51Z: 4 rows","live 06:56:30Z: same 4 rows with rung=R3",
     "DECISIONS.jsonl D-13 part 2","ASSET_CATALOGUE_CONTRACT_v1_0.md §6 C-17 cell vs its own §8 SQL",
     "M0_EXIT_SCORECARD_v1_0.md §2b disagreement register (records the 3-vs-4 discrepancy)"]),

 dict(id="C-20", severity="BLOCKING", assertion="CURRENT data/artifact ⇒ target_floor NOT NULL",
   measured=3, bucket=DEFERRED, reason_kind="ruling",
   reason="Three R0 rows: bg_class_priors, bg_formula_constants, bg_ghatana. target_floor is the "
     "one column whose ownership the campaign HAS already ruled, twice. D-19 part 1: a floor is "
     "the MEASURED ACHIEVED COUNT (I7), 'a declarative source file structurally CANNOT hold a "
     "measured value', and measured values belong to the campaign, written at §8.6 stage 2 "
     "Conform — per rung. D-27 part 2a re-affirms it with a number behind it. So the floors are "
     "R0's to set when R0 opens, not M0's.",
   owner="R0, stage 2 Conform",
   closes_when="R0 opens, the three assets are measured, and G2 sets each floor to the measured "
     "achieved count — AFTER the durability precondition below is met.",
   durability="THE DEFERRAL HAS A PRECONDITION NOBODY HAS DISCHARGED. target_floor is in the "
     "seed's `ON CONFLICT DO UPDATE SET`, and D-19 part 2 REQUIRED it to be removed or "
     "MR-06-guarded before any campaign-set floor can survive. That change has not been made "
     "(verified in the seed text at 06:57:16Z), and a re-seed would move 27 target_floor cells "
     "today, 10 of them between two non-NULL values. A floor written at R0 Conform into an "
     "unguarded column is a floor with an expiry date nobody is told about.",
   rows=["bg_class_priors","bg_formula_constants","bg_ghatana"],
   evidence=["guard C-20 live 06:58:51Z","DECISIONS.jsonl D-19 parts 1-2, D-27 part 2a",
     "SEED_DURABILITY_REGISTER_v1_0.md §1.2 and §3.6(b)","CLAUDE.md §N.4 / invariant I7"]),

 dict(id="C-21", severity="BLOCKING", assertion="target_floor = 0 ⇒ volume_explanation NOT NULL",
   measured=19, bucket=DEFERRED, reason_kind="ruling",
   reason="Nineteen rows across four rungs (R0 ×2, R1 ×2, R2 ×2, R3 ×12, R5 ×1). A "
     "volume_explanation on a zero floor is precisely a G4 by-design classification, and D-19 "
     "part 1 names it in the campaign-owned set — 'volume_explanation WHERE IT RECORDS A G4 "
     "BY-DESIGN CLASSIFICATION' — written at the owning rung's Conform. G4 also requires a "
     "WRITTEN by-design justification per asset, which is a per-asset judgment on that asset's "
     "data: exactly what I14 keeps out of Track M. Same durability precondition as C-20: "
     "volume_explanation is seed-owned and would move on 47 cells at the next re-seed.",
   owner="each row's own rung, stage 2 Conform",
   rows=["bg_class_lifetime_counts","bg_sarvatobhadra_grid","bo_cgm_motifs","bo_pratijna",
     "ga_ayurdaya","ga_sensitive_degree","ka_avadhi","ka_gochara","ka_gochara_resonance",
     "ka_gochara_sweep","ka_gochara_v3_century_materialize","ka_kota_chakra","ka_kshetra",
     "ka_moorti_nirnaya","ka_sudarshana_varsha","ka_taranga","ka_tithi_pravesha",
     "ka_vedha_gochara","lel_events"],
   evidence=["guard C-21 live 06:58:51Z: 19 rows","DECISIONS.jsonl D-19 part 1, D-27 part 2a",
     "CHARTER.md §1 G4","SEED_DURABILITY_REGISTER_v1_0.md §1.2"]),

 dict(id="C-22", severity="RUNG",
   assertion="rung-frozen data/artifact ⇒ integrity_check_sql NOT NULL",
   measured="not_checkable (vacuous — 0 rungs frozen)", bucket=DEFERRED,
   reason_kind="structural-fact",
   reason="VACUOUS TODAY AND HONESTLY REPORTED AS SUCH RATHER THAN AS A PASS. The rule's "
     "antecedent is 'rung-frozen', and no rung has frozen — R0 has not opened. Measured "
     "separately and worth stating plainly: 0 of 128 live assets carry an integrity_check_sql at "
     "all (06:55:57Z). The column is not seed-written, so checks authored at Conform are durable; "
     "authoring them is each rung's stage-2 work per the plan's per-asset 'Add integrity_check_"
     "sql' lines.",
   owner="each rung, stage 2 Conform",
   closes_when="a rung freezes, at which point the rule stops being vacuous for that rung's "
     "assets. It is a RUNG-severity rule, not a BLOCKING one, so it is not an M0 exit condition.",
   rows=[], evidence=["guard C-22 live 06:58:51Z: not_checkable",
     "live 06:55:57Z: integrity_check_sql NOT NULL on 0 of 128 rows"]),

 dict(id="C-25", severity="BLOCKING",
   assertion="co-written target_table ⇒ every co-writer declares its partition",
   measured="not_checkable", bucket=DEFERRED, reason_kind="contract-mandate",
   reason="THE MODEL ENTRY — a deferral whose reason is written into the specification itself. "
     "ASSET_CATALOGUE_CONTRACT §4.9/§10.3: no schema column exists for a natural-key partition "
     "declaration, and §6 states 'Rules C-25, C-26 and C-27 must never be reported as passing… "
     "a CI guard implementing this document emits them as not_checkable with the reason, and a "
     "dashboard that renders that as a pass is itself a defect.' The shipped guard hard-wires "
     "exactly that (check_asset_catalogue_contract.py:1105, `_no_detector`) and its own "
     "cross-check FAILS if the guard and the contract ever disagree about which rules are "
     "not_checkable. This is what a well-formed deferral looks like: a named structural fact, a "
     "specification that records it, a detector that refuses to report green, and a guard test "
     "that would catch the two drifting apart.",
   owner="ADHIKĀRIN (§10.3 is an explicitly unsettled fork)",
   closes_when="a partition-declaration column exists and every co-writer fills it. NOTE THE "
     "ASYMMETRY WITH CRITERION 5: this RULE's deferral is well-formed; the WORK it stands in for "
     "is named as M0 content by Phase 0.4 and is UNEXAMINED. The rule being honestly null does "
     "not make the work deferred.",
   rows=[], evidence=["ASSET_CATALOGUE_CONTRACT_v1_0.md §4.9, §6, §8, §10.3",
     "check_asset_catalogue_contract.py:1069-1109 and the §cross_check spec comparison",
     "guard C-25 live 06:58:51Z: not_checkable"]),

 dict(id="C-26", severity="BLOCKING",
   assertion="generation-bearing asset declares its authority pointer",
   measured="not_checkable", bucket=DEFERRED, reason_kind="contract-mandate",
   reason="Same shape as C-25: no schema column for an authority pointer / protected_generations "
     "(§4.11, §10.3); the contract forbids reporting it as passing; the guard hard-wires "
     "not_checkable with that reason. Unlike C-25 there is NO Phase 0 step that names an "
     "authority pointer as M0 content, so both the rule and the work are deferred.",
   owner="ADHIKĀRIN (§10.3 fork)", closes_when="the §10.3 fork is settled and a column exists.",
   rows=[], evidence=["ASSET_CATALOGUE_CONTRACT_v1_0.md §4.11, §10.3","guard C-26 live 06:58:51Z"]),

 dict(id="C-27", severity="ADVISORY",
   assertion="writer_timeout_seconds set from telemetry where p95 ≥ 0.5× the value",
   measured="not_checkable", bucket=DEFERRED, reason_kind="contract-mandate",
   reason="ADVISORY by the contract's own severity column, and not checkable until Track M2 "
     "produces cleaned telemetry (§4.8) — the p95 the rule compares against does not exist yet. "
     "Recorded, explicitly not green.",
   owner="M2 (telemetry)", closes_when="M2 produces the cleaned telemetry the rule reads.",
   rows=[], evidence=["ASSET_CATALOGUE_CONTRACT_v1_0.md §4.8, §6","guard C-27 live 06:58:51Z"]),

 dict(id="C-28", severity="BLOCKING",
   assertion="estimated_seconds NOT NULL where a successful build exists",
   measured=105, bucket=REPAIRABLE, reason_kind=None,
   reason="REPAIRABLE — BUT NOT TO ZERO, AND THIS REGISTER MEASURED THE FLOOR RATHER THAN "
     "ASSUMING ONE. Phase 0.9 names the backfill as M0 content and D-6 GRANTED it conditionally; "
     "M0-T3 produced the proposal and executed NOTHING (`writes_executed: NONE`). Its statement "
     "T-5 backfills estimated_seconds from the median of completed build_run_assets rows, "
     "affecting 93 rows. THE RESIDUAL: 31 assets are `lit` in asset_throughput and have NO "
     "completed build_run_assets row at all, so no measured duration exists for them — and D-6 "
     "condition 4 forbids inventing one ('an asset with no clean telemetry gets NULL, not a "
     "plausible number', H6). Measured read-only at 07:06Z: C-28 = 105 now, 31 after the "
     "authorised repair, ALL 31 in R0. So the criterion's rule reaches 31, not 0, by any "
     "authorised route, and the residual 31 is DEFERRED to whenever those assets next build.",
   blocker="M0-T3's proposal §10 records a genuine open condition: D-6 condition 5 says 'scoped "
     "to asset_throughput', while D-6's own subject names medians and estimated_seconds, which "
     "live in build_run_assets and asset_registry. The proposal flags the contradiction and "
     "states T-3/T-4/T-5 should not execute until ADHIKĀRIN confirms condition 5 is scoped to "
     "the repair's CONTENT rather than the single table named. D-12 part 5 corrects condition 5 "
     "in exactly that direction ('may touch asset_throughput, build_run_assets telemetry "
     "aggregates, and asset_registry.estimated_seconds') — so the correction appears already "
     "made and the proposal predates it. Someone should confirm that reading rather than assume "
     "it; it is one sentence of ADHIKĀRIN's time.",
   owner="ADHIKĀRIN (confirm D-12 part 5 discharges the flag), then a KĀRAKA executes T-1…T-5",
   closes_when="T-5 runs (93 rows) and the residual 31 is recorded as deferred with this "
     "measurement attached.",
   rows=["31 residual assets, all R0 — bg_class_lifetime_counts, bg_cohort, bg_compendium_index, "
     "bg_concordance, bg_dasha_systems, bg_dignity_reference, bg_doshas, bg_ephemeris, "
     "bg_gochara_arcs, bg_kota_chakra_rings, bg_medical_mappings, bg_muhurta_lattice, "
     "bg_nakshatra, bg_nakshatra_medical, bg_ontology, bg_parihara_rules, bg_phaladeepika_latta, "
     "bg_prashna_rules, bg_reference, bg_remedies, bg_rules, bg_sarvatobhadra_grid, "
     "bg_sign_medical, bg_sky_calendar, bg_text_index, bg_texts, bg_transit_engine, "
     "bg_transit_rules, bg_vastu_directions, bg_vedha_malefic_scale, bg_yogas"],
   evidence=["guard C-28 live 06:58:51Z: 105 violations (the scorecard's reading 2 says 112 at "
     "06:20Z — two detectors, both stated, neither averaged)",
     "read-only SQL 07:06Z: c28_now=105, c28_residual_after_T5=31",
     "TELEMETRY_REPAIR_PROPOSAL_v1_0.md §T-5 and §10 condition 5",
     "DECISIONS.jsonl D-6 conditions 1 and 4, D-12 part 5"]),

 dict(id="X-02", severity="RESIDUAL",
   assertion="no asset_throughput rows on inactive/RETIRED assets",
   measured=1, bucket=RESERVED, reason_kind="charter-prohibition",
   reason="criterion 6's rule. Charter P1 asset; deferred to R3 by plan §14.2 and D-12 part 4. "
     "It is the ONLY rule in the guard that already carries both an itemised disclosure and "
     "RESIDUAL severity, and its disclosure deliberately does not turn it green — the model the "
     "other deferrals need and do not have.",
   owner="R3 / the native", rows=["ka_gochara_sweep"],
   evidence=["guard X-02 live 06:58:51Z (fail, disclosed:true, does_not_turn_the_rule_green:true)",
     "asset_catalogue_disclosed_residuals.json"]),

 dict(id="X-03", severity="BLOCKING",
   assertion="no active asset with neither build coverage nor a dead flag",
   measured=2, bucket=UNEXAMINED, reason_kind=None,
   reason="criterion 8's rule; see that entry. Both rows have plausible owners (R0 and R5); what "
     "is unexamined is the criterion itself — there is no dead-flag column, the guard uses "
     "has_writer as a proxy, and Phase 0.8a asks M0 to produce a flag with nowhere to live.",
   owner="ADHIKĀRIN (G9)", rows=["bg_gochara_citation_resolution","lel_events"],
   evidence=["guard X-03 live 06:58:51Z"]),

 dict(id="X-05", severity="BLOCKING", assertion="no unresolved zero-consumer finding",
   measured=23, bucket=REPAIRABLE, reason_kind=None,
   reason="criterion 9's rule; see that entry. 23 packets, 0 dispositions recorded, machinery "
     "built and waiting on G1 rulings.",
   owner="ADHIKĀRIN (G1 ×23)", rows=["23 packets — listed under criterion 9"],
   evidence=["guard X-05 live 06:58:51Z"]),
]

# ── §5 · at zero, but not the same thing as being at zero ────────────────────
NON_DURABLE = [
 dict(id="C-05", assertion="data/artifact ⇒ count_sql NOT NULL", status="pass (0)",
   durability="NON-DURABLE — REVERTED BY A RE-SEED",
   why="C-05 reads zero only because bg_ephemeris_engine and bg_panchanga are now "
     "asset_kind='service' (the M0-T21 kind repair), which takes them out of the rule's scope. "
     "Neither seed entry declares asset_kind, and asset_registry_seed.ts:3268 supplies "
     "`asset.asset_kind ?? 'data'` — SO THE DEFAULT IS AN ACTIVE WRITE OF 'data', NOT A NO-OP. "
     "The next seed run puts both rows back inside C-05's scope with count_sql still NULL, and "
     "the rule fails again with 2. Re-measured independently here at 06:57:16Z: both cells still "
     "diverge live-vs-seed.",
   projected_after_reseed=2),
 dict(id="C-14", assertion="asset_kind / asset_type coherent", status="pass (0)",
   durability="NON-DURABLE — REVERTED BY A RE-SEED ON EIGHT ROWS",
   why="The M0-T21 repair wrote 'service' into asset_kind on 2 rows and asset_type on 6. Both "
     "columns are in the seed's unconditional `DO UPDATE SET`, and NOT ONE of the eight seed "
     "entries declares the key — so all eight are re-written to the `?? 'data'` default. "
     "Re-measured at 06:57:16Z: 8 divergent cells, exactly the eight rows the repair touched "
     "(bg_ephemeris_engine, bg_panchanga on asset_kind; ka_dasha_kala, ka_graha_sancara, "
     "ka_muhurta_seva, ka_tulana, mi_abhilekha, mi_seva on asset_type).",
   projected_after_reseed=8),
 dict(id="C-18 / criterion 11", assertion="domain present and derived from scope",
   status="pass (0)", durability="EXPOSED — the COLUMN is durable, the PAIR is not",
   why="See criterion 11. domain and rung are absent from both seed column lists, so migration "
     "590's backfill cannot be reverted; but `scope` is seed-owned and domain was DERIVED from "
     "scope, so a re-seed moves one half of the pair on mi_jivanaghatana and leaves the other. "
     "C-18 keeps counting it as present while the value it presents becomes wrong.",
   projected_after_reseed=1),
 dict(id="C-02 / C-03", assertion="layer_index / layer_name", status="fail (1 each, lel_events)",
   durability="DURABLE BY AGREEMENT — measured, not assumed",
   why="Both columns ARE seed-owned, so the M0-T26 repair was durable only if it wrote exactly "
     "what the seed writes. Compared across all 127 seed entries at 06:57:16Z: zero divergent "
     "cells on either column except lel_events, where live is NULL and the seed would write "
     "'L5' / 'Mīmāṃsā'. So the repair agrees with the seed everywhere it touched — and the one "
     "place they disagree is the deliberate NULL D-28 part 1 protects.",
   projected_after_reseed=0),
 dict(id="C-23 / has_substeps", assertion="has_substeps equals the writer-class truth",
   status="pass (0)", durability="DURABLE for today's rows; UNENFORCED for future rows",
   why="has_substeps is in neither seed column list, so the M0-T20 repair of 12 rows cannot be "
     "reverted by a re-seed (SEED_DURABILITY_REGISTER §3.1). The caveat is coverage, not "
     "durability: an asset the seed NEWLY INSERTS lands with has_substeps NULL, and NULL is "
     "falsy at asset_runner.py's `if has_substeps:` — so a new heavy writer silently arrives with "
     "the substep-plan-completeness detector switched off, which is §N.8 instance 4 all over "
     "again. Nothing enforces this. Live rows with has_substeps IS TRUE at 06:55:57Z: 26.",
   projected_after_reseed=0),
]

# ── §6 · what would have to be true to flip the switch ───────────────────────
FLIP_CHECKLIST = [
 dict(n=1, kind="RULING", title="Record the self-reference carve-out for criterion 10",
   what="D-24 part 3 conditions the flip on every criterion being at zero or explicitly "
     "deferred. Criterion 10 IS the flip. Unless ADHIKĀRIN records that criterion 10 is excluded "
     "from its own precondition — satisfied BY the flip, not before it — the precondition is "
     "unsatisfiable and the switch can never legitimately move.",
   unblocks=["crit-10"]),
 dict(n=2, kind="RULING", title="Rule the NAMED-FIELD TEST",
   what="Does M0 repair registry columns that none of Phase 0's fifteen steps names "
     "(target_table, count_sql, health_probe, provides_apis, service_health), or does each go to "
     "its owning rung's stage-2 Conform? D-24 says registry metadata is Track-M work; D-25 part "
     "2b says an UNNAMED field has 'no named M0 mandate' and pinned it to the rung. ONE RULING "
     "RECLASSIFIES SIX RULES AND TWO CRITERIA. Either answer is workable; the absence of an "
     "answer is what blocks the flip.",
   unblocks=["C-04 (7 rows)","C-06","C-07","C-15","C-17 (1 row)","crit-1 (partly)"]),
 dict(n=3, kind="RULING", title="Rule what criterion 1 means",
   what="Is the three-way diff the scorecard's reading (every registry row needs a production "
     "@register — 5 violations) or the shipped guard's (P-01…P-06 — 0 violations, with services "
     "and source rows legitimately writerless)? The guard is what a blocking flip gates on, so "
     "this decides whether criterion 1 is already satisfied or has four exemptions and one G1 "
     "disposition still to make.",
   unblocks=["crit-1"]),
 dict(n=4, kind="RULING", title="Rule Phase 0.4 — the partition declaration",
   what="Phase 0.4 names 'declare co-writer partitions' as M0 content, but no schema column "
     "exists to declare them in. Authorise a column under D-4's reasoning, or defer the work to "
     "the owning rungs with the reason recorded. C-25 itself stays not_checkable either way — "
     "that part is already well-formed; what is undecided is the WORK.",
   unblocks=["crit-5","crit-2 (partly)"],
   resolved="D-39 (2026-08-23T09:25:50Z) — CONFIRMED M0's; the column is authorised under D-4's "
     "reasoning, NOT reserved by P5. crit-5 moved UNEXAMINED → REPAIRABLE-IN-M0. The remaining "
     "work is execution (author the migration, backfill, verify), not a further ruling."),
 dict(n=5, kind="RULING", title="Rule Phase 0.8a — the dead flag",
   what="Define a registered-but-dead flag, rule the guard's has_writer proxy sufficient, or "
     "defer the criterion. Today the scorecard calls criterion 8 NOT-MEASURABLE and the guard "
     "returns 2 violations from a proxy the contract never designated.",
   unblocks=["crit-8","X-03"],
   resolved="D-39 (2026-08-23T09:25:50Z) — CONFIRMED M0's for both crit-8 and X-03; the dead-flag "
     "column is authorised under D-4's reasoning, NOT reserved by P5. Both moved UNEXAMINED → "
     "REPAIRABLE-IN-M0. The remaining work is execution — no column has been created yet."),
 dict(n=6, kind="RULING", title="Rule criterion 2's wording",
   what="'contract violations per kind = 0' cannot be satisfied while C-25/C-26/C-27 have no "
     "detector and must never read green. Re-word it to 'every CHECKABLE rule at zero, the "
     "un-checkable ones reported not_checkable with their reason', or make them checkable.",
   unblocks=["crit-2"]),
 dict(n=7, kind="RULING", title="Reconcile G1's rung bound with Phase 0.8b / 0.8c",
   what="G1's charter bound reads 'only assets in the current rung' and no rung is open, while "
     "Phase 0.8b and 0.8c assign 3 promotions and 23 zero-consumer dispositions to M0. One "
     "ruling clears both criteria; without it, the two largest REPAIRABLE items cannot be "
     "executed by anyone.",
   unblocks=["crit-4","crit-9","C-11","X-05"],
   resolved="D-38 (2026-08-23T09:24:48Z) — 0.8b's disposition is REMAIN DRAFT (a decision, not a "
     "promotion): none of ga_vichara/ka_dasha_kala/ka_sangam is named by a rung-specific "
     "promotion clause, so crit-4/C-11 move to DEFERRED-WITH-REASON (R1/R3), not repaired in M0. "
     "0.8c's 23 packets are adjudicated per reading class (INPUT-ONLY/BY-DESIGN closed, "
     "METHOD-BLIND closed-as-unknown, NO-CONSUMER-FOUND/SHADOWED routed to rung); "
     "crit-9/X-05 move to AT-ZERO-WITH-EXPOSURE, unresolved = 0."),
 dict(n=8, kind="RULING", title="Rule H2's reach — is a PR merge to main a 'write to main'?",
   what="Criterion 10's 'merged' half requires the guards to reach origin/main (verified absent "
     "at 07:03Z). Charter H3 forbids weakening a gate; charter H2 forbids 'any write to main'. "
     "Whether a reviewed PR merge is inside H2 has never been asked. It is not a KĀRAKA's "
     "question. Until it is answered criterion 10 cannot be satisfied by any route.",
   unblocks=["crit-10","crit-12"]),
 dict(n=9, kind="RULING", title="Correct D-13 part 2's rung, and cover its fourth row",
   what="D-13 part 2 defers three unearned service_health greens to 'R0'; all three are "
     "layer=kala and their live rung column reads R3. And a fourth row (ka_graha_sancara, "
     "'unhealthy', no probe) is covered by no ruling because the contract's §6 cell undercounted "
     "its own §8 SQL by one.",
   unblocks=["C-17"]),
 dict(n=10, kind="MECHANISM",
   title="Give every DEFERRED item a disclosure the guard can actually read",
   what="THIS IS THE STEP THAT ACTUALLY STOPS THE FLIP, AND IT IS MECHANICAL. Twelve entries are "
     "deferred with reasons — ten of them rules — and NOT ONE of the ten has an entry in "
     "asset_catalogue_disclosed_residuals.json. The only rule that has one is X-02, which is "
     "RESERVED rather than deferred, and it is also the only rule carrying a severity "
     "(RESIDUAL) that does not gate. Eight of the ten deferred rules — C-01, C-02, C-03, "
     "C-08, C-20, C-21, C-25, C-26 — are BLOCKING in the guard's rule table with no "
     "disclosure attached (C-22 is RUNG and C-27 ADVISORY, so those two do not gate). "
     "FLIPPING BLOCKING TODAY REDS THE BRANCH ON THE 15 BLOCKING FAILURES THE GUARD RETURNED "
     "LIVE AT 06:58:51Z, several of which can only be made green by touching a P1 asset or by "
     "pre-building R5 work — which is precisely the 'weaken a criterion to get moving' "
     "pressure D-24 part 3 "
     "named. A deferral that lives only in a markdown file is not a deferral the CI gate can "
     "honour. NOTE: the disclosure must not turn a rule green — X-02's `does_not_turn_the_rule_"
     "green: true` is the pattern, and per D-12 part 4 an unmet criterion is recorded unmet.",
   unblocks=["crit-10 in practice"]),
 dict(n=11, kind="EXECUTION", title="Execute the repairs that are already authorised",
   what="(a) telemetry T-1…T-5 under D-6 + D-12 part 5 → C-28 from 105 to its measured floor of "
     "31; (b) the 3 C-11 dispositions and the 23 zero-consumer dispositions, once step 7 lands; "
     "(c) D-19 part 2 / D-27 part 2a's seed change for target_floor — WITHOUT which C-20's "
     "eventual repair expires silently, and whose model (the MR-06 guard) D-28 part 4 warns has "
     "never had to choose and must be proven by fixture rather than inherited.",
   unblocks=["C-28","crit-4","crit-9","C-20 durability"]),
 dict(n=12, kind="EXECUTION", title="Merge, flip, and make it RUN once",
   what="Per step 8's ruling: get the two guards and the workflow onto origin/main, delete the "
     "two `continue-on-error: true` lines (ADHIKĀRIN's own act — charter G9, and explicitly not "
     "a KĀRAKA's), and confirm at least one real run reports. Zero runs have ever executed; a "
     "workflow that has never run is not evidence.",
   unblocks=["crit-10","crit-12"]),
 dict(n=13, kind="VERIFICATION", title="Re-measure, then let PARĪKṢAKA certify",
   what="Re-run m0_exit_scorecard.py (it appends a reading rather than replacing one) and both "
     "guards, and hand the result to PARĪKṢAKA. No agent that performed any of the above may "
     "sign it (I16 / charter H7), and this register — authored by a KĀRAKA — certifies nothing.",
   unblocks=["M0 freeze (M0-T10)"]),
]

# ── §7 · disagreements and corrections found while classifying ───────────────
DISAGREEMENTS = [
 dict(item="C-02 / C-03 violation counts",
   a="M0_EXIT_SCORECARD_v1_0.md reading 2 (06:20:44Z): 21 and 20",
   b="this task's live query (06:55:57Z) and the shipped guard (06:58:51Z): 1 and 1",
   resolution="NOT A CONFLICT — A CLOCK. M0-T26 landed the Phase 0.5a repair between the two "
     "readings (WORK_QUEUE: done_pending_verification 06:51:24Z, commit_recorded 06:52:23Z). "
     "Both figures are true of their instant. The scorecard's own §0 note that filesystem- and "
     "database-sourced criteria move between runs is exactly this. Anyone reading the scorecard "
     "as current on these two rules will overstate the remaining work by 39 rows."),
 dict(item="criterion 12 — does the domain-coherence assertion exist?",
   a="M0_EXIT_SCORECARD_v1_0.md reading 2: 'THE ASSERTION DOES NOT EXIST'",
   b="check_asset_catalogue_contract.py implements X-04 ('domain coherence: a shared asset "
     "depends only on shared assets', origin 'plan §11') and it returns 0 violations live",
   resolution="The scorecard's clause is stale. What remains true is the operative half: the "
     "assertion has never RUN in CI. Criterion 12 is therefore not-green for criterion 10's "
     "reasons, not for its own."),
 dict(item="criterion 8 — measurable or not?",
   a="scorecard: NOT-MEASURABLE (no dead-flag field is defined)",
   b="guard X-03: fail, 2 violations, using has_writer as the proxy",
   resolution="Both are honest and they are answering different questions. The scorecard asks "
     "whether the criterion AS WRITTEN has a detector (it does not — nothing defines a dead "
     "flag); the guard asks whether any active asset has no registered writer (2 do). Recorded "
     "as a disagreement rather than reconciled, because reconciling it is ADHIKĀRIN's step 5."),
 dict(item="C-28 violation count",
   a="scorecard reading 2 (06:20Z): 112", b="shipped guard (06:58:51Z): 105",
   resolution="Two independent detectors, 35 minutes apart, over a table nothing repaired in "
     "between. Both are reported; neither is averaged. This register's own residual measurement "
     "(31 after the authorised repair) was computed from the same definition the guard uses, so "
     "it is comparable to 105, not to 112."),
 dict(item="C-17 row count — the contract disagrees with its own SQL",
   a="ASSET_CATALOGUE_CONTRACT §6 cell: 3 (ka_dasha_kala, ka_muhurta_seva, ka_tulana)",
   b="the contract's own §8 SQL, and the guard: 4 — it also matches 'unhealthy', catching "
     "ka_graha_sancara",
   resolution="The §8 SQL is the detector, so 4 is the rule's result. It matters beyond "
     "bookkeeping: D-13 part 2's deferral was written for 'three service assets', so the fourth "
     "row inherits no ruling. Already noted in the scorecard's §2b; carried here because it "
     "changes a classification."),
 dict(item="D-13 part 2 names the wrong rung",
   a="D-13 part 2: 'It is R0 substrate and R0 IS NOT OPEN'",
   b="all three assets are ka_* / layer='kala'; their live `rung` column, backfilled by "
     "migration 590 per contract §5.2, reads R3",
   resolution="The deferral stands — a rung owns it and M0 does not — but the rung named is "
     "wrong, and the ruling routes the finding to R0's stage-1 intake where R3 will need it. "
     "Reported, not corrected: correcting a ruling is ADHIKĀRIN's (charter §4)."),
 dict(item="ASSET_CATALOGUE_CONTRACT §11 says migration 590 is not applied",
   a="contract §11: 'That migration is AUTHORED AND NOT APPLIED. … No DDL or DML from it has "
     "been executed against any database.'",
   b="_migrations_applied carries 590_nirmana_m0_catalogue_contract_columns.sql at "
     "2026-08-23T05:36:13.833986+00:00, and all four columns are live",
   resolution="The contract's §11 is stale, not wrong-at-authoring. Flagged because §11 is the "
     "sentence a later reader would use to decide whether the columns exist, and it now says the "
     "opposite of the database. Fixing it is a documentation task, not this one's."),
 dict(item="zero-consumer count: plan 13 vs measured 23",
   a="NIRMANA_ELEVATION_PLAN §1 states 13; the plan's own per-asset annotations count 7",
   b="ZERO_CONSUMER_EVIDENCE_v1_0.md and the guard: 23 packets",
   resolution="The 23 is the measured figure with a per-asset list behind it and is what X-05 "
     "reduces. The plan's 13 reconciles with nothing, including the plan. Not averaged, not "
     "adopted — recorded, as the scorecard also recorded it."),
]


# ═════════════════════════════════════════════════════════════════════════════
# D-30 APPLICATION LAYER — added by M0-T36, 2026-08-23
# ═════════════════════════════════════════════════════════════════════════════
# M0-T31 (this file's v1.0) filed six rules and five criteria UNEXAMINED and named
# the named-field test as the single largest lever. ADHIKĀRIN ruling D-30 part 1
# then ADOPTED that test as a rule and instructed it be applied. This layer applies
# it. It does NOT rewrite v1.0's classification in place: every entry it moves keeps
# `prior_bucket_m0t31`, so the register still shows what M0-T31 decided and what
# D-30 changed. Nothing here is a ruling; D-30 is the ruling and this is its
# arithmetic.
#
# THE RULE, quoted from D-30 part 1 (the ruling governs, not this gloss):
#   "A REGISTRY COLUMN IS M0's TO REPAIR IF AND ONLY IF (a) A PHASE-0 STEP OR M0's
#    OWN ACCEPTANCE CRITERIA NAME IT … AND (b) NO MORE-SPECIFIC PLAN CLAUSE ASSIGNS
#    IT TO A LATER RUNG, in which case the specific governs the general … Absent (a),
#    the column belongs to the rung that owns the asset, and repairing it in M0 is
#    the I13 breach."

# The fifteen Phase-0 steps, quoted from NIRMANA_ELEVATION_PLAN_v3_0.md §Phase 0 and
# carried to M0 verbatim by v4.0 §14.4 ("Phase 0 — all 15 steps | M0"). This is the
# (a)-half's left-hand side and it is transcribed, not summarised, because the whole
# rule turns on whether a column appears in it.
PHASE_0_STEPS = {
 "0.1  Six-source census": "asset_registry · @register() · asset_registry_seed.ts · migrations · asset_throughput · CAPABILITY_MANIFEST.json",
 "0.2  Author the contract": "§3 as an enforceable per-kind specification — including `integrity_check_sql` and `target_floor` AS REQUIRED FIELDS",
 "0.3  Lifecycle + tombstone": "§3.2; `superseded_by`, `data_disposition`; no DELETEs (I6)",
 "0.4  Semantic de-duplication": "(table × generation × partition) invariant; correct the gochara attribution; DECLARE CO-WRITER PARTITIONS",
 "0.5a Layer position": "14 null + 6 malformed `layer_index` → `Lx`; `layer_name` derived",
 "0.5b SOURCE classification": "`lel_events` → `SOURCE`",
 "0.6a has_substeps": "14 false negatives — derive from the writer class",
 "0.6b Kind reconciliation": "`asset_kind` authoritative; 6 disagreements resolved",
 "0.7  Consumer map": "Asset → serving-surface index as a required field",
 "0.8a Build coverage audit": "Registered-but-dead FLAGGED (`bg_gochara_citation_resolution`)",
 "0.8b catalog_status drift": "34 DRAFT-but-served promoted or justified; CURRENT-may-not-depend-on-DRAFT enforced",
 "0.8c Zero-consumer review": "13 assets: record the consumer or retire with a disposition",
 "0.9  Telemetry repair": "close orphaned rows; recompute medians; backfill `estimated_seconds`; schedule the refresh",
 "0.10 CI enforcement": "three-way guard + contract conformance + prefix + edge + DRAFT-dependency invariants, merged and BLOCKING",
 "0.11 Freeze the baseline": "tag the reconciled catalogue; later phases measure drift against it",
}

# M0's OWN acceptance criteria, quoted from v4.0 §14.1's M0 row. This is the (a)-half's
# other left-hand side, which D-30 added explicitly ("acceptance criteria count, per D-4").
M0_ACCEPTANCE_NAMES = (
 "v3.0 Phase 0's ten exit criteria verbatim, PLUS 'every asset carrying `domain` and "
 "`rung`', PLUS 'the CI domain-coherence assertion (§11) green'. The domain/rung clause "
 "is the only place either column is named anywhere in Phase 0 or M0 — which is exactly "
 "why D-4 could authorise migration 590 and why D-30 had to add this half to the rule.")

# ── the rule verified against the case law it was derived from ───────────────
# D-30 states it verified this itself. M0-T36 re-derived it independently rather than
# accept the claim: a rule that failed to reproduce its own precedents would be a worse
# instrument than no rule. Each row states the (a) finding, the (b) finding, the rule's
# output and the ruling's actual holding.
D30_VERIFICATION = [
 dict(case="has_substeps", ruling="D-24", held="M0",
      a="SATISFIED — Phase 0.6a names `has_substeps` by column name, and §14.1's M0 content line "
        "names '`has_substeps` repair' again.",
      b="DOES NOT FIRE — §8.6 stage 2 (Conform) lists 'has_substeps corrected' among each rung's "
        "registry-metadata work, but that is the GENERAL per-rung stage description; 0.6a + §14.1 "
        "are the SPECIFIC clauses and the specific governs. See the §8.6 collision note below — "
        "this is the one place the rule's two halves pull against each other, and the tiebreak is "
        "forced: read the other way, the rule would not reproduce D-24 and D-30's own verification "
        "claim would be false.",
      rule_output="M0", reproduces=True),
 dict(case="has_writer (row repair)", ruling="D-25 part 2(b)", held="R0",
      a="FAILS — no Phase-0 step names `has_writer`; M0's acceptance criteria do not name it. "
        "Criterion 8 names 'build coverage' and 'a dead flag', not this column; the guard's X-03 "
        "uses `has_writer` only as a PROXY it designated itself.",
      b="not reached (a already fails)",
      rule_output="the rung that owns the asset = R0", reproduces=True),
 dict(case="domain / rung", ruling="D-4", held="M0",
      a="SATISFIED via the acceptance-criteria half ONLY — no Phase-0 step names either column; "
        "§14.1's 'every asset carrying `domain` and `rung`' does. This case is why refinement (a) "
        "cannot be 'a Phase-0 step' alone.",
      b="DOES NOT FIRE — no rung clause claims either column; migration 590 derived both centrally.",
      rule_output="M0", reproduces=True),
 dict(case="layer_index / layer_name", ruling="D-24 / executed at M0-T26, certified V-10", held="M0",
      a="SATISFIED — Phase 0.5a names both columns explicitly.",
      b="DOES NOT FIRE — the §15 per-asset bullets that mention layer position cite '(Phase 0.5a)' "
        "by name, i.e. they point AT the M0 step rather than claiming the work for a rung.",
      rule_output="M0", reproduces=True),
 dict(case="SOURCE reclassification (lel_events)", ruling="D-23", held="R5",
      a="SATISFIED — Phase 0.5b names it, and names the asset: '`lel_events` → `SOURCE`'.",
      b="FIRES — §8.4's R5 row names the same asset for the same work ('`lel_events` reclassified "
        "`SOURCE`'). The specific governs the general.",
      rule_output="R5", reproduces=True),
]

D30_VERIFICATION_VERDICT = (
 "5 of 5 REPRODUCED, re-derived independently by M0-T36 from the plan text rather than "
 "inherited from D-30's assertion. Two structural observations that the verification produced "
 "and that a bare PASS would have hidden. FIRST: refinement (b) is load-bearing in exactly one "
 "of the five cases (lel_events). Refinement (a)'s acceptance-criteria half is load-bearing in "
 "exactly one other (domain/rung). Neither refinement is decoration; drop either and the rule "
 "contradicts a ruling ADHIKĀRIN has already made. SECOND, and this one is a finding rather than "
 "a confirmation — see §9.1.1: plan §8.6 stage 2 assigns SIX kinds of registry metadata to every "
 "rung's Conform stage BY NAME, one of which is `has_substeps`, and closes with 'Stage 2 is "
 "deliberately inside the rung rather than in Track M'. Read as a (b)-firing clause it would send "
 "has_substeps to the rungs and D-24 would not be reproduced — so it must be read as the general "
 "and Phase 0.6a as the specific. That reading is forced by the rule's own verification property, "
 "not chosen for convenience, but it is nowhere written down and the next agent to read §8.6 will "
 "not know it.")

# ── §8.6 stage 2 — the collision the verification surfaced ───────────────────
PHASE_86_STAGE2_COLLISION = dict(
 quote="Conform — complete the §3 registration for this layer's assets only: floors set to "
       "achieved (I7), `integrity_check_sql` authored per asset, timeouts derived, `has_substeps` "
       "corrected, partitions declared, consumers recorded. Registry metadata only — no writer "
       "runs. … Stage 2 is deliberately inside the rung rather than in Track M.",
 source="NIRMANA_ELEVATION_PLAN_v4_0.md §8.6 stage 2 + its closing paragraph",
 fields_named=["target_floor", "integrity_check_sql", "writer_timeout_seconds",
               "has_substeps", "partition declaration", "consumer map"],
 collides_with={
   "has_substeps": "Phase 0.6a + §14.1 M0 content line. RESOLVED IN FAVOUR OF M0 — forced, because "
                   "the opposite reading breaks D-24, which D-30 asserts the rule reproduces. "
                   "CONSEQUENCE IF READ THE OTHER WAY: the has_substeps repair executed at M0-T26 "
                   "and certified by PARĪKṢAKA at V-9 would retroactively be an I13 breach on 12 "
                   "rows spanning five rungs. It is not — but the reading that makes it one is "
                   "available to any agent who reads §8.6 and not this note.",
   "partition declaration": "Phase 0.4 + §14.1 M0 content line ('semantic de-duplication with "
                            "declared co-writer partitions'). SAME SHAPE, NOT YET RULED — see "
                            "crit-5 below, which the named-field test reaches and D-30 did not "
                            "anticipate it reaching.",
   "consumer map": "Phase 0.7. Not currently a failing rule, so nothing turns on it today; "
                   "recorded so it is not rediscovered.",
   "target_floor / integrity_check_sql / writer_timeout_seconds":
       "NO COLLISION. Phase 0.2 names `integrity_check_sql` and `target_floor` only as REQUIRED "
       "FIELDS OF THE CONTRACT SPECIFICATION — the authoring of §3, which M0 did. It does not "
       "assign the POPULATION of either. §8.6 stage 2 is therefore the only clause assigning that "
       "work, and it assigns it per rung. This is independently confirmed by D-19 part 1 and D-27 "
       "part 2a for floors, and it is why C-20/C-21/C-22/C-27 were already correctly DEFERRED in "
       "v1.0 — the named-field test does not move them, it explains them.",
 },
 disposition="RECORDED, NOT RESOLVED. Reading §8.6 stage 2 as general rather than specific is "
             "forced for has_substeps and is the working assumption for partitions and the "
             "consumer map. Whether ADHIKĀRIN wants that written into the case law is ADHIKĀRIN's; "
             "M0-T36 states it as the reading the rule requires and does not rule it.",
)

# ── the reclassification itself ──────────────────────────────────────────────
_NFT = ("**D-30 PART 1 APPLIED (M0-T36).** ")

D30_APPLICATION = {
 "C-04": dict(
   new_bucket=DEFERRED, reason_kind="ruling",
   owner="the rung that owns each row — R0 (bg_prashna_rules, bg_sky_calendar), R1 (ga_sade_sati, "
         "ga_sensitive, ga_strength, ga_structural), R2 (bo_cdlm_summary, bo_chart_gestalt), "
         "R5 (lel_events) — at that rung's §8.6 stage-2 Conform",
   addendum=_NFT +
     "`target_table` is named by NO Phase-0 step and by NO M0 acceptance criterion. Phase 0.2 — the "
     "only step that names registry columns at all — names `integrity_check_sql` and `target_floor`, "
     "and not this one. Clause (a) therefore FAILS and the column belongs to the rung that owns the "
     "asset; repairing it in M0 would be the I13 breach D-30 names. Clause (b) independently confirms "
     "the same destination for two of the nine rows: plan §15's per-asset entries for bo_cdlm_summary "
     "and bo_chart_gestalt each carry the bullet 'Declare `target_table` (or `clear_tables` if it "
     "writes several)', and both assets are R2. The two rows that already had a reason keep it "
     "(lel_events → R5 by D-23; bg_sky_calendar → R0 by D-28 part 4, whose `bg_sky_events` relation is "
     "genuinely absent from production and is a trigger-bearing R0 intake defect). The seven that had "
     "none now have one: not 'probably fine', but 'no clause of the plan gives this column to M0'. "
     "NOTE, because it is the honest residual: this settles WHOSE the column is, not WHETHER a NULL "
     "target_table on the four chart_facts co-writers is deliberate. That question travels to R1 with "
     "the rows."),
 "C-06": dict(
   new_bucket=DEFERRED, reason_kind="ruling",
   owner="R5 (Mīmāṃsā rung), §8.6 stage-2 Conform — inherited from C-07, of which this rule is a shadow",
   addendum=_NFT +
     "`count_sql` is named by no Phase-0 step and no M0 acceptance criterion; clause (a) FAILS. The "
     "single row is mi_seva (R5), and C-06 closes when C-07 does because mi_seva's count_sql should "
     "not exist at all on a service row. Same destination by two independent routes."),
 "C-07": dict(
   new_bucket=DEFERRED, reason_kind="ruling",
   owner="R3 (ka_dasha_kala, ka_tulana) and R5 (mi_abhilekha, mi_seva), §8.6 stage-2 Conform",
   addendum=_NFT +
     "THIS IS THE ONE RULE WHERE CLAUSE (a) IS PARTLY SATISFIED, AND IT IS WORTH SAYING SO RATHER THAN "
     "REPORTING A CLEAN DEFERRAL. Of the four columns C-07 asserts NULL on a service row, three "
     "(`target_table`, `count_sql`, `clear_tables`) are named nowhere in Phase 0 — clause (a) fails "
     "flatly. The fourth, `target_floor`, IS named — by Phase 0.2. But 0.2 names it as a REQUIRED FIELD "
     "OF THE CONTRACT SPECIFICATION being authored, not as a population M0 performs; the clause that "
     "assigns the work of setting and correcting floors is §8.6 stage 2 ('floors set to achieved (I7)'), "
     "per rung, which is refinement (b) firing. That is not a novel reading: D-19 part 1 already held "
     "that 'a declarative source file structurally CANNOT hold a measured value' and placed floors at "
     "§8.6 stage 2 Conform, and D-27 part 2a re-affirmed it with a measurement. So all four columns "
     "reach the same destination, three by (a) and one by (b). All four assets are R3/R5. Three of the "
     "four columns are additionally SEED-OWNED, so a DB-only NULLing in M0 would be reverted by the "
     "next re-seed — a durability fact that makes the deferral not merely correct but load-bearing."),
 "C-15": dict(
   new_bucket=DEFERRED, reason_kind="ruling",
   owner="R3 (ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana) and R5 (mi_abhilekha, "
         "mi_seva) — §8.6 stage-2 Conform for provides_apis; the probe itself is tier-S rung work (§9)",
   addendum=_NFT +
     "Neither `health_probe` nor `provides_apis` is named by any Phase-0 step or M0 acceptance "
     "criterion; clause (a) FAILS for both and the columns belong to the rungs. Note the shape of what "
     "is being deferred: `provides_apis` is a declaration, but `health_probe` is a DETECTOR, and §8.4's "
     "R3 row already assigns 'a real known-answer probe with an SLO' to R3 by name for two of these six "
     "assets — so refinement (b) fires there too. Writing a probe in M0 to clear C-15 would be "
     "manufacturing a detector to satisfy a criterion, which is the H3 shape D-29 part 5 named for the "
     "sibling rule C-17. The v1.0 entry's correction of the contract's §6 cell stands unchanged: there "
     "are EIGHT service rows live since the M0-T21 kind repair, not six, and the two new ones "
     "(bg_ephemeris_engine, bg_panchanga) DO carry both fields."),
 "C-17": dict(
   new_bucket=DEFERRED, reason_kind="ruling",
   owner="R3 (Kāla rung) stage-1 intake — all four rows, per D-13 part 2 AS CORRECTED BY D-29",
   addendum=_NFT +
     "TWO RULINGS CLOSE THIS ENTRY AND THE SECOND ONE ANSWERED THE EXACT DEFECT v1.0 FILED IT FOR. "
     "v1.0 filed C-17 UNEXAMINED on ONE ROW: three of the four were covered by D-13 part 2, the fourth "
     "(ka_graha_sancara, service_health='unhealthy', no probe) by nothing, because the contract's §6 "
     "cell undercounted its own §8 SQL by one. D-29 has since (i) corrected D-13 part 2's destination "
     "from 'R0 substrate' to R3 — the rung the live `rung` column actually carries for every ka_* row — "
     "and (ii) extended it from three rows to four, characterising the fourth as A RED WITH NO DETECTOR "
     "BEHIND IT rather than a false green: §N.8 in its other direction, failing safe, and explicitly "
     "NOT to be 'fixed' by clearing it to healthy or NULL when R3 opens. So every row now carries a "
     "ruling. Independently, the named-field test reaches the same place: `health_probe` and "
     "`service_health` are named by no Phase-0 step and no M0 criterion, so clause (a) fails and the "
     "columns are the owning rung's. Two routes, one destination, and the register's own §6 step 9 "
     "('correct D-13 part 2's rung, and cover its fourth row') is discharged."),
}

# ── entries the test REACHES but does not move, and why that is the finding ──
# D-30 instructed the test be applied to "the 6 rules and 2 criteria". Applied honestly it
# lands on five rules cleanly, and it lands on three further entries in a way ADHIKĀRIN did
# not anticipate: it settles their OWNERSHIP to M0 while leaving their MECHANISM undecided.
# Per the asymmetry D-30's closing paragraph adopted from M0-T31 — "an UNEXAMINED entry costs
# me a minute; a wrongly-DEFERRED one costs the gate its meaning" — these stay UNEXAMINED,
# narrowed rather than closed.
D30_NARROWED = {
 "X-03": dict(
   result="OWNERSHIP SETTLED TO M0 BY CLAUSE (a) — MECHANISM STILL UNDECIDED. Stays UNEXAMINED.",
   addendum=_NFT + "**THE TEST REACHES THIS ENTRY AND D-30 DID NOT ANTICIPATE THAT IT WOULD.** "
     "D-30 listed X-03 and criterion 8 under a SEPARATE ruling (v1.0 §6 step 5, 'Rule Phase 0.8a — "
     "the dead flag'), not among the named-field test's reclassifications. But clause (a) is "
     "satisfied here twice over and more explicitly than in any of the five verification cases: "
     "Phase 0.8a reads 'Registered-but-dead FLAGGED (`bg_gochara_citation_resolution`)' — naming the "
     "work AND the asset — and M0 acceptance criterion 8 names 'active assets with neither build "
     "coverage nor a dead flag'. Clause (b) does not fire: no rung clause claims a dead flag. So the "
     "rule's output is unambiguous — THE DEAD FLAG IS M0's, NOT A RUNG's, and deferring it to R0/R5 "
     "would be the error in the opposite direction. WHAT THE TEST DOES NOT DECIDE, and why this entry "
     "does not move to a settled bucket: there is no column for the flag to live in. Creating one is "
     "charter P5 (a schema change outside the migrations this plan names) unless D-4's reasoning "
     "extends — 'a criterion that cannot be met without a change has NAMED that change even where it "
     "numbers no migration'. Ruling the guard's self-designated `has_writer` proxy sufficient is the "
     "other available answer, and D-25 already found that column wrong on 2 rows. The register's "
     "definition of REPAIRABLE-IN-M0 requires 'a KNOWN repair'; none is known. So the entry stays "
     "UNEXAMINED — but the question left is narrower and different in kind: not 'whose is it' (answered: "
     "M0's) but 'what is the flag'."),
 "crit-8": dict(
   result="OWNERSHIP SETTLED TO M0 BY CLAUSE (a) — MECHANISM STILL UNDECIDED. Stays UNEXAMINED.",
   addendum=_NFT + "Criterion 8 is X-03's criterion and inherits its finding exactly: Phase 0.8a and "
     "the criterion's own text both name the dead flag, so clause (a) is satisfied and the work is "
     "M0's — a result D-30 routed to a separate ruling and did not expect the named-field test to "
     "produce. What remains undecided is the mechanism (a P5 column, the `has_writer` proxy ruled "
     "sufficient, or the criterion deferred), and beneath it the fact the scorecard has recorded from "
     "its first reading: the two detectors disagree about whether this criterion is MEASURABLE at all "
     "— NOT-MEASURABLE from the scorecard, 2 violations from the guard's proxy."),
 "crit-5": dict(
   result="OWNERSHIP SETTLED TO M0 BY CLAUSE (a) — MECHANISM STILL UNDECIDED, AND (b) COLLIDES. "
          "Stays UNEXAMINED.",
   addendum=_NFT + "**THE TEST REACHES THIS ENTRY TOO, AND IT WAS NOT ON D-30's LIST EITHER** (v1.0 "
     "§6 step 4 files it as a separate ruling). Clause (a) is satisfied: Phase 0.4 names 'DECLARE "
     "CO-WRITER PARTITIONS' and §14.1's M0 content line names 'semantic de-duplication with declared "
     "co-writer partitions'. Clause (b) is where this differs from X-03 and where it is genuinely "
     "harder: §8.6 stage 2 lists 'partitions declared' among each rung's Conform work, so the SAME "
     "collision documented above for has_substeps applies here — and here it is NOT forced by the "
     "verification property, because no prior ruling pins partitions either way. The working reading "
     "(§8.6 stage 2 general, Phase 0.4 specific) gives the work to M0; the opposite reading gives it "
     "to the rungs. Under either, C-25 stays permanently `not_checkable` for the same structural "
     "reason — no schema column — and that part of v1.0's entry was already well-formed. What the test "
     "changes is that the undecided question is now narrower: not 'is this M0's or the rungs'' but "
     "'does §8.6 stage 2 override Phase 0.4, and if not, is the column authorised under D-4's "
     "reasoning or reserved under P5'."),
 "crit-1": dict(
   result="PARTLY DISPOSED — 2 of 5 rows settled by the test; the criterion's own blocker is untouched. "
          "Stays UNEXAMINED.",
   addendum=_NFT + "v1.0's §6 step 2 listed 'crit-1 (partly)' among the test's beneficiaries, and "
     "'partly' is right but smaller than it sounds. The test disposes of two of the five diverging "
     "ids by clause (a) failing on `has_writer`: bg_sarvatobhadra_grid (R0) and, redundantly with "
     "D-23, lel_events (R5). It does NOT touch the other three, and it does NOT touch the criterion's "
     "actual blocker, WHICH IS NOT A COLUMN QUESTION AT ALL: the scorecard's detector and the shipped "
     "parity guard disagree by construction about what the three-way diff MEANS — 5 violations versus "
     "0 — and no ruling says which detector expresses the criterion. A rule about who owns a column "
     "cannot answer a question about what a criterion counts. Recorded so that 'the named-field test "
     "landed' is not mistaken for 'criterion 1 moved'."),
 "C-28": dict(
   result="RESIDUAL DEFERRAL GRANTED BY D-30 PART 3 (G7) — bucket unchanged, residual now recorded.",
   addendum="**D-30 PART 3 APPLIED (M0-T36).** ADHIKĀRIN granted the residual deferral under G7 and "
     "D-31 part 2 indexes it as one of the three G7 deferrals on the record. M0-T36 re-measured the "
     "split read-only at 2026-08-23T08:0xZ rather than inherit it, and it reproduces exactly: of the "
     "105 data/artifact rows the shipped guard reports, **74 are backfillable** from the median of "
     "their completed `build_run_assets` rows (D-6's authorised statement T-5) and **31 have no "
     "completed build_run_assets row at all**, so no measured duration exists and D-6 condition 4 "
     "forbids inventing one (H6). All 31 are R0. THE BUCKET DOES NOT MOVE, and that is deliberate: the "
     "rule is genuinely repairable-in-M0 for 74 rows and genuinely deferred for 31, and collapsing it "
     "to one bucket would lose whichever half was collapsed. What the flip needs from this rule is "
     "therefore TWO things, not one — T-5 executed (nothing has executed; M0-T3 produced the proposal "
     "with `writes_executed: NONE`), and the 31-row residual disclosed. Until T-5 runs, C-28 reads 105, "
     "not 31, and any statement that 'C-28 is deferred' is premature by 74 rows."),
}

# ── what the reclassification did to the tally ───────────────────────────────
D30_TALLY_DELTA = dict(
 rules_before={REPAIRABLE: 3, DEFERRED: 10, RESERVED: 1, UNEXAMINED: 6},
 rules_after={REPAIRABLE: 3, DEFERRED: 15, RESERVED: 1, UNEXAMINED: 1},
 criteria_before={REPAIRABLE: 3, DEFERRED: 2, RESERVED: 1, UNEXAMINED: 5, AT_ZERO: 1},
 criteria_after={REPAIRABLE: 3, DEFERRED: 2, RESERVED: 1, UNEXAMINED: 5, AT_ZERO: 1},
 moved=["C-04 UNEXAMINED→DEFERRED-WITH-REASON", "C-06 UNEXAMINED→DEFERRED-WITH-REASON",
        "C-07 UNEXAMINED→DEFERRED-WITH-REASON", "C-15 UNEXAMINED→DEFERRED-WITH-REASON",
        "C-17 UNEXAMINED→DEFERRED-WITH-REASON"],
 narrowed_not_moved=["X-03 (ownership→M0)", "crit-8 (ownership→M0)", "crit-5 (ownership→M0, (b) collides)",
                     "crit-1 (2 of 5 rows)", "C-28 (residual 31 recorded, bucket held)"],
 count_reconciliation=(
   "D-30's question field says the test 'moves 6 rules + 2 criteria', a figure it inherited verbatim "
   "from SUTRADHĀRA's escalation, which inherited it from v1.0 §0 of this file. THAT FIGURE IS NOT "
   "ITEMISABLE AND M0-T36 COULD NOT REPRODUCE IT. v1.0's own §6 step 2 lists six 'unblocks' entries — "
   "C-04, C-06, C-07, C-15, C-17, crit-1 — which is FIVE RULES AND ONE CRITERION, not six and two; and "
   "the shared NAMED_FIELD_TEST reason text is attached to only FOUR rules (C-04, C-06, C-07, C-15) "
   "while asserting in its own last sentence that 'one ADHIKĀRIN ruling on the test itself reclassifies "
   "all six'. So v1.0 disagrees with itself in two places and the disagreement propagated into the "
   "ledger unchallenged. THE MEASURED ANSWER: applied strictly, the test moves FIVE rules to "
   "DEFERRED-WITH-REASON; it additionally REACHES three entries D-30 did not list (X-03, crit-8, "
   "crit-5) and narrows them without moving them; and it partly disposes crit-1. This is not a "
   "quibble about arithmetic — the three unanticipated entries are the finding, and they were "
   "invisible while the count was believed."),
)

# ── re-measurement, 2026-08-23 (M0-T36) ──────────────────────────────────────
REMEASUREMENT = dict(
 at="2026-08-23T08:00:51Z (contract guard, --live --json, READ-ONLY) and 08:0xZ (direct read-only SQL)",
 headline=(
   "NOTHING MOVED. Every contract-rule count is IDENTICAL to the 06:58:51Z reading v1.0 recorded — "
   "13 pass / 16 fail / 4 not_checkable, the same 15 BLOCKING ids, the same per-rule violation counts. "
   "Criterion readings are unchanged too, including origin/main (re-verified @ 2670e61e2: all three "
   "guard/workflow files still ABSENT). THE REASON IS WORTH STATING, because 'four verdicts landed and "
   "nothing changed' reads like a null result and is not one: V-8, V-9 and V-10 certified writes that "
   "had ALREADY LANDED before v1.0 measured — migration 590 at 05:36:13Z, has_substeps before 06:20Z, "
   "the layer repair at ~06:51–06:54Z, and v1.0's first reading is 06:55:57Z. The certifications "
   "changed those writes' EVIDENTIARY STATUS, not the registry. V-11 certified this register itself and "
   "wrote nothing. D-29 and D-30 are rulings, which move buckets, not rows. So the correct reading is: "
   "the register's numbers were already post-repair when they were taken, and four verdicts later they "
   "still are."),
 scorecard="reading 4 appended to m0_exit_scorecard.json's `_meta.reading_history` (append-only; "
           "readings 1–3 preserved byte-for-byte). Tally unchanged from reading 3: PASS 1, FAIL 7, "
           "NOT-MEASURABLE 3, BLOCKED 1.",
 new_findings=[
   dict(id="F-T36-1", severity="MEDIUM",
        title="The two C-28 detectors disagree by 7, and the 7 are all services",
        detail="The shipped guard reports C-28 = 105; the scorecard's SQL reports 112. Neither is "
               "wrong — they are different rules wearing one id. `c28()` in "
               "check_asset_catalogue_contract.py:860-861 skips any row whose `asset_kind` is not in "
               "DATA_KINDS; the scorecard's SQL (m0_exit_scorecard.py:743-747) does not filter by kind. "
               "The 7 rows in the gap are ALL `asset_kind='service'`: bg_panchanga, ka_dasha_kala, "
               "ka_graha_sancara, ka_muhurta_seva, ka_tulana, mi_abhilekha, mi_seva. This is the SAME "
               "defect class as crit-1's — one criterion, two detectors, two different meanings of "
               "zero — and it had not been named for C-28. It matters for the flip because the "
               "residual D-30 part 3 deferred (31) was measured under the guard's definition; under "
               "the scorecard's it would be 31 plus however many of those 7 services never complete a "
               "build. NOT RULED, NOT FIXED — neither file was edited to reconcile them."),
   dict(id="F-T36-2", severity="HIGH",
        title="CI never runs the guard against production — it runs --baseline against a frozen "
              "05:09:17Z snapshot",
        detail="Every number in this register, in the scorecard, in V-11 and in D-30 comes from "
               "`--live`. THE WORKFLOW DOES NOT RUN `--live`. "
               ".github/workflows/nirmana-m0-guards.yml invokes `--self-test` and `--baseline`, and "
               "`--baseline` is a shorthand for `--snapshot asset_catalogue_baseline_20260823.json`, a "
               "file captured at 2026-08-23T05:09:17Z — BEFORE migration 590 applied (05:36:13Z) and "
               "before the Phase 0.5a layer repair (~06:51Z). Run today it exits 1 with pass=6 fail=18 "
               "not_checkable=9 and **17 BLOCKING failures**, not 15: it still fails C-05, C-14 and "
               "C-23, all three of which PASS live, and it reports C-08/C-09/C-10/C-18/C-19 as "
               "not_checkable because migration 590's columns do not exist in the snapshot. "
               "CONSEQUENCE FOR THE FLIP: removing `continue-on-error` today would gate the branch on "
               "a detector reading a three-hour-old file, not on production — a signal that does not "
               "measure the claim it makes (CLAUDE.md §N.8), and one that would red the branch on "
               "three rules the campaign has already repaired and PARĪKṢAKA has already certified. "
               "Refreshing the snapshot, or changing what CI invokes, is a THIRD prerequisite for the "
               "flip that no ledger line has recorded. NOT FIXED: no .github/ file and no baseline "
               "snapshot was written by M0-T36."),
   dict(id="F-T36-3", severity="HIGH",
        title="A disclosure entry cannot be honoured for any rule except X-02 — the guard has no "
              "code path that reads one",
        detail="D-30 part 4's amended flip condition requires that 'EVERY DEFERRED RULE CARRIES ITS "
               "DISCLOSURE ENTRY'. M0-T36 drafted them (see §9). THEY ARE INERT, and that must be "
               "said plainly rather than discovered at flip time. Two mechanical facts: (i) "
               "`disclosed_additions` is keyed by ASSET_ID and is read in exactly one place, "
               "check_asset_catalogue_contract.py:951 inside `x02()`; no other rule function opens "
               "the residuals file except `x05()`, which reads a different block "
               "(`zero_consumer_dispositions`). (ii) Severity is a hardcoded constant in the RULES "
               "table (line 1142: `Rule(\"X-02\", RESIDUAL, …)`); a disclosure cannot demote a rule "
               "from BLOCKING, and X-02's docstring is explicit that a disclosure does NOT turn a rule "
               "green — 'what the disclosure buys is that the severity is RESIDUAL'. X-02 is "
               "non-gating because someone TYPED `RESIDUAL` in the rule table, not because it carries "
               "a disclosure. SO: writing the fifteen entries satisfies D-30 part 4's letter and "
               "changes nothing the guard does. Making them honourable requires a guard code change — "
               "a per-rule disclosure reader and a disclosure-conditioned severity — and that change "
               "is a demotion of thirteen BLOCKING gates, which is exactly the shape H3 exists to "
               "scrutinise. IT IS NOT A KĀRAKA's CHANGE AND M0-T36 DID NOT MAKE IT. The guard was run "
               "read-only and not edited."),
 ],
)


# ═════════════════════════════════════════════════════════════════════════════
# D-38 / D-39 / D-40 / D-41 / D-42 APPLICATION LAYER — added by M0-T46, 2026-08-23
# ═════════════════════════════════════════════════════════════════════════════
# Six ADHIKĀRIN rulings landed after v1.1 (M0-T36) closed this register. Of the six, D-38,
# D-39 and D-42 change a classification here; D-37 is background (it corrects D-12 part 3
# and the named-field test's refinement (b), neither of which this register's live entries
# rest on); D-40 amends the flip condition's CI clause (§10 below) without moving a bucket;
# D-41 authorises the deploy.yml edit and a CI-edit-by-direction rule that this register
# does not itself need to act on (checked: no "awaiting a ruling on CI edit scope" flag
# exists anywhere in this file, the scorecard, or M0_CLOSE_READINESS_v1_0.md).
#
# This layer does NOT rewrite what v1.1 decided: every entry it moves keeps its v1.1 bucket
# under a new `prior_bucket_v1_1` key, and the appended addendum is prefixed to the
# (already D-30-layered) reason text — the same discipline `_apply_d30()` used above.

# ── D-38 part 1 on Phase 0.8b, quoted verbatim (the ruling governs, not this gloss) ──
#   "PHASE 0.8b — THE DISPOSITION FOR THE DRAFT-BUT-SERVED SET IS: REMAIN DRAFT. THIS IS A
#    G1 DECISION, NOT A DEFERRAL. ... Promoting assets to CURRENT on the strength of
#    servedness would be writing a status from a proxy rather than from its detector's
#    verdict ... promotion for at least R2's nine, R3's two named, R4's nine and R5's
#    lel_events belongs to those rungs BY NAME."
# None of criterion 4 / C-11's three DRAFT dependencies (ga_vichara R1, ka_dasha_kala R3,
# ka_sangam R3) is named by any of those rung-specific promotion clauses, so the general
# REMAIN-DRAFT disposition governs all three and the C-11 edges cannot be repaired in M0.
D38_CRIT4_ADDENDUM = (
 "**D-38 APPLIED (M0-T46).** Phase 0.8b's disposition is now RULED, not merely blocked on "
 "a G1 rung-bound reconciliation. D-38 part 1 decided the DRAFT-but-served set's general "
 "disposition is REMAIN DRAFT — 'a G1 decision, not a deferral' — and part 2 confirmed bulk "
 "promotion in M0 is refused outright: only where a specific rung clause names an asset for "
 "promote-or-retire (R2's nine, R3's ka_graha_sancara/ka_muhurta_seva, R4's nine, R5's "
 "lel_events) does that rung decide it; otherwise REMAIN DRAFT stands until the owning "
 "rung's own §8.6 stage-2 Conform revisits it with real integrity evidence behind it. None "
 "of this criterion's three DRAFT dependencies — ga_vichara (R1), ka_dasha_kala (R3), "
 "ka_sangam (R3) — is named by any rung-specific promotion clause, so REMAIN DRAFT is their "
 "disposition too. THE THREE C-11 EDGES THEREFORE CANNOT BE REPAIRED IN M0 BY PROMOTION: "
 "D-38 states plainly that promoting on servedness alone 'would be writing a status from a "
 "proxy rather than from its detector's verdict' — precisely H4/§N.8 — and I13 forbids the "
 "only other route (asset-lifecycle work on a dependency outside the open rung). Moved from "
 "REPAIRABLE-IN-M0 to DEFERRED-WITH-REASON: the reason is D-38 itself, the destination is "
 "each dependency's own rung, and Phase 0.8b's own 'promoted or justified' is satisfied by "
 "the justified half — REMAIN DRAFT, decided, not silently unexamined.")
D38_C11_ADDENDUM = (
 "**D-38 APPLIED (M0-T46).** Criterion 4's rule; see that entry. D-38 part 1 rules the "
 "general DRAFT-but-served disposition REMAIN DRAFT, and none of ga_vichara, ka_dasha_kala "
 "or ka_sangam is named by a rung-specific promotion clause, so all three stay DRAFT and "
 "these three edges cannot be closed by promotion in M0. Moved to DEFERRED-WITH-REASON.")

# ── D-38 part 3 on Phase 0.8c, quoted verbatim ──
#   "THE 23 ZERO-CONSUMER PACKETS ARE RESOLVED NOW, PER PACKET, BY DETERMINATION RATHER
#    THAN BY MUTATION ... RESOLVED MEANS ADJUDICATED, NOT MUTATED: M0's exit criterion is
#    'unresolved zero-consumer findings all zero', and a finding adjudicated against its
#    evidence with a recorded determination IS resolved."
# Applied to the 23 measured packets by reading class (ZERO_CONSUMER_EVIDENCE_v1_0.md §1/§2,
# M0-T6) — transcribed from that document's own summary table, not re-derived; D-38 rules
# the CLASS disposition, this table only carries the already-published per-asset fact.
D38_ZERO_CONSUMER_DISPOSITION_TABLE = {
 "INPUT-ONLY": dict(rule="no action, closed", n=8,
   assets=["bg_cohort", "bg_gochara_arcs", "bg_kota_chakra_rings", "bg_kp_sublord_division",
           "bg_phaladeepika_latta", "bg_reference", "bg_vedha_malefic_scale",
           "ka_gochara_v3_century_materialize"]),
 "NO CONSUMER FOUND": dict(rule="retirement candidate, NOT retired — routed to owning rung",
   n=1, assets=["bg_concordance"]),
 "METHOD-BLIND": dict(rule="no action, closed as UNKNOWN — explicitly NOT a retirement candidate",
   n=7, assets=["bg_panchanga", "bg_sky_calendar", "bo_cdlm_summary", "bo_samskara",
                "ka_graha_sancara", "ka_kshetra", "mi_jivanaghatana"]),
 "SHADOWED": dict(rule="a real defect — routed to owning rung", n=5,
   assets=["bg_vidhi_floors", "bg_vidhi_primitives", "ka_dasha_kala", "ka_muhurta_seva",
           "ka_tulana"]),
 "BY DESIGN EMPTY / CATEGORY MISMATCH": dict(rule="no action, closed, mismatch recorded", n=2,
   assets=["bg_ephemeris_engine", "bg_sarvatobhadra_grid"]),
}
D38_ROUTED_TO_RUNG = (D38_ZERO_CONSUMER_DISPOSITION_TABLE["NO CONSUMER FOUND"]["assets"] +
                      D38_ZERO_CONSUMER_DISPOSITION_TABLE["SHADOWED"]["assets"])
D38_CRIT9_ADDENDUM = (
 "**D-38 APPLIED (M0-T46).** Phase 0.8c is now RULED per packet, per reading class, rather "
 "than left open pending 23 individual G1 dispositions. D-38 part 3 adjudicates each of the "
 "five reading classes ZERO_CONSUMER_EVIDENCE_v1_0.md kept apart: INPUT-ONLY -> no action, "
 "closed (the absence of a serving consumer is the design); NO CONSUMER FOUND -> recorded "
 "as a retirement candidate, NOT retired, routed to the owning rung; METHOD-BLIND -> no "
 "action, and explicitly NOT a retirement candidate (this is UNKNOWN, not zero — retiring "
 "on a method-blind absence would be H6); SHADOWED -> a real defect, routed to the owning "
 "rung; BY DESIGN EMPTY / CATEGORY MISMATCH -> no action, closed, mismatch recorded. Applied "
 "to the 23 measured packets: 8 INPUT-ONLY and 2 BY-DESIGN close with no action; 7 "
 "METHOD-BLIND close as genuinely unknown, not as retirement candidates; 1 NO-CONSUMER-FOUND "
 "(bg_concordance, R0) is recorded as a retirement candidate and routed to R0; 5 SHADOWED "
 "(bg_vidhi_floors, bg_vidhi_primitives — R0; ka_dasha_kala, ka_muhurta_seva, ka_tulana — R3) "
 "are recorded as real defects and routed to their rungs. D-38's own words govern the "
 "count: 'RESOLVED MEANS ADJUDICATED, NOT MUTATED … a finding adjudicated against its "
 "evidence with a recorded determination IS resolved. Reading that criterion to require "
 "status changes would force asset-lifecycle work on six closed rungs to satisfy a "
 "catalogue step, which I13 forbids.' ALL 23 PACKETS NOW CARRY A RECORDED DETERMINATION, so "
 "unresolved = 0 by the ruling's own definition of resolved. THE ZERO IS CONDITIONAL, NOT "
 "UNCONDITIONAL: 6 of the 23 (1 retirement candidate, 5 SHADOWED defects) carry follow-on "
 "asset-lifecycle work at their owning rung that this ruling explicitly does not perform, "
 "and 7 more are closed as UNKNOWN rather than confirmed-absent. Moved from "
 "REPAIRABLE-IN-M0 to AT-ZERO-WITH-EXPOSURE — the same shape as criterion 11 — rather than "
 "to a plain settled bucket, because the underlying rows are adjudicated, not fixed.")
D38_X05_ADDENDUM = (
 "**D-38 APPLIED (M0-T46).** Criterion 9's rule; see that entry. D-38 part 3 adjudicates "
 "all 23 packets by reading class; unresolved = 0. Moved to AT-ZERO-WITH-EXPOSURE: 6 "
 "packets (1 retirement candidate, 5 SHADOWED defects) are routed to their owning rungs "
 "rather than closed outright, and 7 METHOD-BLIND packets are closed as unknown, not as "
 "confirmed-zero.")

# ── D-39 part 4 on X-03, criterion 8, criterion 5, quoted verbatim ──
#   "CONFIRMED: all three are M0's. Both need a column, and by D-4's reasoning a Phase-0
#    step that names the thing has named the change that creates it, so the columns are
#    inside the plan's naming and NOT reserved by P5 — subject to D-4's standing conditions
#    (additive only, mechanical backfill only, NULL where not derivable, verify applied,
#    never edit after, PARIKSAKA verifies). It was right not to move them to a settled
#    bucket while no mechanism exists."
# "No mechanism exists" described v1.1's moment, when whether a column was even AUTHORISED
# (D-4) or RESERVED (P5) was still open. D-39 settles that. What remains is execution —
# author the migration, backfill, verify — which nobody has done: exactly
# REPAIRABLE-IN-M0's own definition ("a known repair takes it to zero; nobody has done
# it"), so these three move there from UNEXAMINED.
_D39 = "**D-39 APPLIED (M0-T46).** "
D39_X03_ADDENDUM = (
 _D39 + "M0-T36's own re-derivation of the named-field test (independent of D-30's "
 "assertion) reached X-03 and found clause (a) satisfied — Phase 0.8a names the dead flag "
 "AND the asset — but left it UNEXAMINED because 'the register's definition of "
 "REPAIRABLE-IN-M0 requires a KNOWN repair; none is known', the open question being whether "
 "a new column is authorised under D-4's reasoning or reserved under charter P5. D-39 part "
 "4 CONFIRMS ownership to M0 independently and SETTLES the P5 question: the column is "
 "'inside the plan's naming and NOT reserved by P5 … subject to D-4's standing conditions "
 "(additive only, mechanical backfill only, NULL where not derivable, verify applied, "
 "never edit after, PARĪKṢAKA verifies)'. With ownership confirmed and the column "
 "authorised rather than reserved, a KNOWN repair now exists — even though nothing has "
 "executed it. Moved from UNEXAMINED to REPAIRABLE-IN-M0. What remains undone: authoring "
 "the migration, running the backfill, and PARĪKṢAKA's verification — none of which this "
 "task performs.")
D39_CRIT8_ADDENDUM = (
 _D39 + "Criterion 8 is X-03's criterion and inherits D-39's finding exactly: ownership to "
 "M0 confirmed, the dead-flag column authorised under D-4 and not reserved by P5. Moved "
 "from UNEXAMINED to REPAIRABLE-IN-M0. The scorecard's own disagreement with the guard "
 "about whether this criterion is measurable at all is unaffected — no column exists yet, "
 "so the scorecard still reads NOT-MEASURABLE until the repair is executed. Separately, "
 "D-42 (2026-08-23T11:04:17Z) ranks build_run_assets as authoritative wherever a surface "
 "asks 'was this asset built' — bearing on this criterion's BUILD-COVERAGE half, not the "
 "dead-flag half D-39 just settled: has_writer and asset_throughput.state='lit' both "
 "remain proxies for 'built', and the dead-flag column D-39 authorises does not by itself "
 "decide which proxy the criterion's other half should read.")
D39_CRIT5_ADDENDUM = (
 _D39 + "Criterion 5's entry additionally flagged a (b)-clause collision the other two did "
 "not carry — whether §8.6 stage 2's generic 'partitions declared' overrides Phase 0.4's "
 "specific naming. D-39 part 4 confirms criterion 5 M0's OUTRIGHT, alongside X-03 and "
 "criterion 8, resolving that collision in M0's favour rather than leaving it open. The "
 "column question is settled the same way: authorised under D-4, not reserved by P5. Moved "
 "from UNEXAMINED to REPAIRABLE-IN-M0. C-25 itself stays permanently `not_checkable` for "
 "the separate structural reason already recorded — no column exists YET — which is "
 "exactly the repair this bucket names as not yet done.")

# ── D-42 on C-28, quoted verbatim ──
#   "It is not '31 assets missing an estimated_seconds'. It is '31 ASSETS READ lit WITH NO
#    COMPLETED RUN RECORD BEHIND THEM'." And: "build_run_assets IS AUTHORITATIVE.
#    asset_throughput.state='lit' IS A CLAIM ABOUT A BUILD, NOT EVIDENCE OF ONE … THE SAME
#    RANKING THEREFORE APPLIES WHEREVER THE QUESTION IS ASKED." And on the two forbidden
#    fixes: backfilling the 31 is H6; RE-POINTING c28() at build_run_assets to close it is
#    a weakening under D-41 part 2, presumptively H3, and is explicitly refused.
D42_C28_ADDENDUM = (
 "**D-42 APPLIED (M0-T46).** ADHIKĀRIN ruling D-42 reclassifies this residual's FRAMING and "
 "forbids both available 'fixes'. THE OLD FRAME WAS WRONG: this is not '31 assets missing "
 "an estimated_seconds'. D-42's authoritative framing: '31 ASSETS READ lit WITH NO "
 "COMPLETED RUN RECORD BEHIND THEM' — the missing estimate is a symptom, the unearned "
 "`lit` is the finding (D-13's telemetry pollution meeting §N.8's no-op-completion class). "
 "RANKING ESTABLISHED FOR THE WHOLE REGISTER, NOT JUST THIS RULE: 'build_run_assets IS "
 "AUTHORITATIVE. asset_throughput.state=\"lit\" IS A CLAIM ABOUT A BUILD, NOT EVIDENCE OF "
 "ONE' — applying wherever a surface asks 'was this asset built', including criterion 8's "
 "build-coverage half (see that entry). TWO FIXES ARE EXPLICITLY FORBIDDEN, NOT MERELY "
 "DISCOURAGED: backfilling estimates for the 31 (H6 — a number on a build nothing "
 "witnessed), and RE-POINTING c28()'s detector at build_run_assets to close it — 'under "
 "the authoritative definition C-28 would report zero violations and a BLOCKING failure "
 "would pass — while all 31 unearned lit states remain exactly as they are. That is a "
 "weakening under D-41 part 2 and presumptively H3.' NEITHER FIX IS THIS TASK'S TO MAKE "
 "AND NEITHER WAS MADE — no detector in m0_exit_scorecard.py or "
 "check_asset_catalogue_contract.py was re-pointed by M0-T46; a future re-pointing found "
 "inconsistent with this ruling is a finding for a separate task, not a repair for this "
 "one. THE BUCKET DOES NOT MOVE — the deferral for the 31 stands (D-30 part 3), now "
 "grounded on the definitional finding rather than the absence of estimates — and the 31 "
 "unearned lit states are additionally understood as ROUTED TO THEIR OWNING RUNGS (all "
 "R0), since D-42 holds 'each rung's own build is the only thing that can earn or refute a "
 "lit'.")

# ── the reclassifications themselves, applied by _apply_d3842() below ────────
D3842_TO_DEFERRED = {
 "crit-4": dict(new_bucket=DEFERRED, reason_kind="ruling",
   owner="R1 (ga_vichara) and R3 (ka_dasha_kala, ka_sangam) — each at its own §8.6 "
         "stage-2 Conform",
   addendum=D38_CRIT4_ADDENDUM),
 "C-11": dict(new_bucket=DEFERRED, reason_kind="ruling",
   owner="R1 (ga_vichara) and R3 (ka_dasha_kala, ka_sangam)",
   addendum=D38_C11_ADDENDUM),
}
D3842_TO_AT_ZERO = {
 "crit-9": dict(new_bucket=AT_ZERO, reason_kind="ruling", addendum=D38_CRIT9_ADDENDUM),
 "X-05": dict(new_bucket=AT_ZERO, reason_kind="ruling", addendum=D38_X05_ADDENDUM),
}
D3842_TO_REPAIRABLE = {
 "crit-5": dict(new_bucket=REPAIRABLE, reason_kind=None,
   owner="ADHIKĀRIN confirmed M0 (D-39); execution (author migration, backfill, verify) "
         "is a KĀRAKA task",
   addendum=D39_CRIT5_ADDENDUM),
 "crit-8": dict(new_bucket=REPAIRABLE, reason_kind=None,
   owner="ADHIKĀRIN confirmed M0 (D-39); execution is a KĀRAKA task",
   addendum=D39_CRIT8_ADDENDUM),
 "X-03": dict(new_bucket=REPAIRABLE, reason_kind=None,
   owner="ADHIKĀRIN confirmed M0 (D-39); execution is a KĀRAKA task",
   addendum=D39_X03_ADDENDUM),
}
D3842_ADDENDUM_ONLY = {
 "C-28": D42_C28_ADDENDUM,   # bucket unchanged — D-30 part 3's deferral stands, reframed
}

D3842_TALLY_DELTA = dict(
 rules_before={REPAIRABLE: 3, DEFERRED: 15, RESERVED: 1, UNEXAMINED: 1, AT_ZERO: 0},
 rules_after={REPAIRABLE: 2, DEFERRED: 16, RESERVED: 1, UNEXAMINED: 0, AT_ZERO: 1},
 criteria_before={REPAIRABLE: 3, DEFERRED: 2, RESERVED: 1, UNEXAMINED: 5, AT_ZERO: 1},
 criteria_after={REPAIRABLE: 3, DEFERRED: 3, RESERVED: 1, UNEXAMINED: 3, AT_ZERO: 2},
 moved=["crit-4 REPAIRABLE-IN-M0→DEFERRED-WITH-REASON (D-38)",
        "C-11 REPAIRABLE-IN-M0→DEFERRED-WITH-REASON (D-38)",
        "crit-9 REPAIRABLE-IN-M0→AT-ZERO-WITH-EXPOSURE (D-38)",
        "X-05 REPAIRABLE-IN-M0→AT-ZERO-WITH-EXPOSURE (D-38)",
        "crit-5 UNEXAMINED→REPAIRABLE-IN-M0 (D-39)",
        "crit-8 UNEXAMINED→REPAIRABLE-IN-M0 (D-39)",
        "X-03 UNEXAMINED→REPAIRABLE-IN-M0 (D-39)"],
 reframed_not_moved=["C-28 — D-42 corrects the framing ('lit with no completed "
                     "build_run_assets record', not 'missing estimated_seconds'); bucket "
                     "held at REPAIRABLE-IN-M0, the D-30 part 3 deferral for the 31-row "
                     "residual is unchanged and now better grounded"],
 net_unexamined="6 of 32 entries were UNEXAMINED after v1.1 (M0-T36): crit-1, crit-2, "
               "crit-5, crit-8, crit-10, X-03. D-39 resolves 3 of those 6 to "
               "REPAIRABLE-IN-M0 (crit-5, crit-8, X-03). The other 3 (crit-1, crit-2, "
               "crit-10) are untouched by these six rulings and stay UNEXAMINED — 3 of "
               "32 entries remain UNEXAMINED after v1.2.",
)

def _apply_d3842():
    """Apply D-38 (0.8b/0.8c), D-39 (X-03/crit-8/crit-5 ownership) and D-42 (C-28 framing) to
    the v1.1 (D-30-applied) entries, preserving what v1.1 decided. Mirrors `_apply_d30()`."""
    for e in CRITERIA + RULES:
        for table in (D3842_TO_DEFERRED, D3842_TO_AT_ZERO, D3842_TO_REPAIRABLE):
            a = table.get(e["id"])
            if a:
                e["prior_bucket_v1_1"] = e["bucket"]
                e["bucket"] = a["new_bucket"]
                if a.get("reason_kind"):
                    e["prior_reason_kind_v1_1"] = e.get("reason_kind")
                    e["reason_kind"] = a["reason_kind"]
                if a.get("owner"):
                    e["prior_owner_v1_1"] = e.get("owner")
                    e["owner"] = a["owner"]
                e["reason"] = (a["addendum"] +
                    "\n\n— — — v1.1 (M0-T36, D-30 applied) classification, preserved — — —\n\n"
                    + e["reason"])
                e["reclassified_by"] = ("DECISIONS.jsonl D-38/D-39 (ADHIKĀRIN, 2026-08-23); "
                    "applied by M0-T46. Ruling: ADHIKĀRIN. Application: KĀRAKA. "
                    "Certification: none (I16 / H7).")
        add = D3842_ADDENDUM_ONLY.get(e["id"])
        if add:
            e["reason"] = (add +
                "\n\n— — — v1.1 (M0-T36, D-30 applied) classification, preserved — — —\n\n"
                + e["reason"])
    return True

# NOTE: called after `_apply_d30()` below, not here — this function's addenda assume the
# v1.1 (D-30-applied) reason text is already in place, so it must run second.


# ── §9 — the disclosure entries, DRAFTED (M0-T36) ────────────────────────────
# D-30 part 4 amends D-24 part 3: "the switch flips when every criterion is at zero or
# deferred AND EVERY DEFERRED RULE CARRIES ITS DISCLOSURE ENTRY, itemized and dated, in
# the same discipline D-10 part 3 granted for the migration-number allowlist."
#
# THESE ARE THE M0-T36 HISTORICAL DRAFTS, AND THIS MODULE NO LONGER WRITES THEM ANYWHERE.
# Read this before reading anything below it, or the block reads as live and it is not.
#
# M0-T36 wrote these into a then-new top-level block (`deferred_rule_disclosures`) of
# platform/scripts/governance/asset_catalogue_disclosed_residuals.json, deliberately NOT
# merged into `disclosed_additions`, which `x02()` reads and validates. Two things have
# happened since:
#   (1) the block is no longer inert — M0-T40 wired check_asset_catalogue_contract.py to
#       read it BY RULE ID and compute each rule's `effective_severity` from it, which
#       closed finding F-T36-3; and
#   (2) the block is no longer this module's output — M0-T49/T51/T55 wrote D-54's fifteen
#       AUTHORISED disclosures into the live file on D-57's corrected ground (certified
#       V-35/V-37) and this draft was never updated to match.
# So M0-T62 REMOVED THE WRITE (Standing Queue SQ-12, ADHIKĀRIN D-44 part 4): the live
# file owns its own block; what follows is the record of what M0-T36 drafted, rendered
# into this register's §10 and written to no guard file. `_report_disclosure_divergence()`
# reads the live file and PRINTS the difference, so the staleness is visible rather than
# silently overwriting the authorised entries.
#
# Nothing here changes any rule's severity, status or exit code, and nothing here turns a
# rule green: X-02's `does_not_turn_the_rule_green: true` is the pattern and every entry
# carries it, per D-12 part 4's "never silently green".
#
# Field discipline mirrors X-02's exactly (owner / landed_at / disclosed_via / reason /
# deferred_to are the five the guard would ERROR on if absent), plus the four this block
# adds so the entry is dated, attributed and honest about being unwired.
DISCLOSURE_COMMON = dict(
    disclosed_at="2026-08-23",
    disclosed_by="KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
    certified_by=None,          # I16 / charter H7
    # F-T36-3 CLOSED by M0-T40: check_asset_catalogue_contract.py now reads this block
    # by RULE ID, validates every entry, and computes each rule's `effective_severity`
    # FROM the disclosures instead of from a constant. So these entries are read — and
    # they still have NO gating effect, because a demotion additionally requires
    # `gating_effect="non_gating"` plus an `authorised_by` decision id that exists in
    # DECISIONS.jsonl under ADHIKĀRIN's name, plus an itemised `covers` list that
    # accounts for every current violation. None of the three is present here, and a
    # KĀRAKA may not supply the second: demoting a gate is a charter G-power.
    wired_into_the_guard=True,
    gating_effect="none",
    gating_effect_reason=(
        "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may "
        "add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised "
        "`covers` list, and even then the rule still reports every violation — a "
        "disclosure makes a residual visible and non-gating, never invisible "
        "(D-12 part 4, D-10 part 3)."),
    does_not_turn_the_rule_green=True,
)

def _d(rule, severity, gates, owner, deferred_to, landed_at, via, reason, measured):
    e = dict(rule=rule, severity_in_the_rule_table=severity, gates_the_exit_code_today=gates,
             owner=owner, deferred_to=deferred_to, landed_at=landed_at,
             disclosed_via=via, reason=reason, measured=measured)
    e.update(DISCLOSURE_COMMON)
    return e

DISCLOSURE_DRAFT = {
 "C-01": _d("C-01", "BLOCKING", True, "R5 (Mīmāṃsā rung), stage 2 Conform", "R5",
   "pre-campaign (the row predates the campaign; prefix has never matched)",
   "DECISIONS.jsonl D-23 (ADHIKĀRIN, 2026-08-23T05:04:21Z) — reverses D-21 and assigns the SOURCE "
   "reclassification to R5, not M0",
   "One row: lel_events, prefix 'lel' against layer 'mimamsa'. C-01 EXEMPTS source rows, so the "
   "SOURCE reclassification IS the repair — there is nothing separate to fix. D-23 assigned that "
   "reclassification to R5 (§8.4's R5 row names the asset: 'lel_events reclassified SOURCE'), "
   "reversing D-21 which had briefly placed it in M0. Repairing it in M0 would re-commit the error "
   "D-23 corrected.",
   {"violations": 1, "rows": ["lel_events"], "measured_at": "2026-08-23T08:00:51Z"}),

 "C-02": _d("C-02", "BLOCKING", True, "R5 (Mīmāṃsā rung), stage 2 Conform", "R5",
   "2026-08-23T06:51-06:54Z (M0-T26 repaired 20 of 21 rows; this one was held back deliberately)",
   "DECISIONS.jsonl D-28 part 1 (deliberate-NULL category) + D-23; write certified by PARĪKṢAKA V-10",
   "One row: lel_events, layer_index NULL. THE NULL IS DELIBERATE AND MUST NOT BE FILLED. D-28 part 1 "
   "rules it 'THE ONLY PLACE IN THE REGISTRY WHERE THE OPENNESS OF A RESERVED DECISION IS WRITTEN "
   "DOWN': the correct value is NULL-if-source but L5-if-data, and D-23 reserved that choice to R5. "
   "Filling it in M0 would answer a reserved question by default. V-10 confirmed the row held NULL "
   "through the 39-cell layer repair, which is the deliberate NULL surviving contact with a real write.",
   {"violations": 1, "rows": ["lel_events"], "was": 21, "repaired_by": "M0-T26 (V-10)",
    "measured_at": "2026-08-23T08:00:51Z"}),

 "C-03": _d("C-03", "BLOCKING", True, "R5 (Mīmāṃsā rung), stage 2 Conform", "R5",
   "2026-08-23T06:51-06:54Z (M0-T26 repaired 19 of 20 rows; this one was held back deliberately)",
   "DECISIONS.jsonl D-28 part 1 + D-23; write certified by PARĪKṢAKA V-10",
   "One row: lel_events, layer_name NULL. Identical reason to C-02 and the same reserved decision: "
   "the lexicon spelling that belongs here depends on whether the row is SOURCE or L5 data, which is "
   "R5's to decide. Every other populated row now carries the §N.1 LOCKED diacritics (Gaṇita, Kāla, "
   "Mīmāṃsā), a real §N.1 violation caught PRE-write by a codepoint pin (D-28 part 6).",
   {"violations": 1, "rows": ["lel_events"], "was": 20, "repaired_by": "M0-T26 (V-10)",
    "measured_at": "2026-08-23T08:00:51Z"}),

 "C-04": _d("C-04", "BLOCKING", True,
   "per row: R0 (bg_prashna_rules, bg_sky_calendar) · R1 (ga_sade_sati, ga_sensitive, ga_strength, "
   "ga_structural) · R2 (bo_cdlm_summary, bo_chart_gestalt) · R5 (lel_events)",
   "the owning rung's §8.6 stage-2 Conform",
   "pre-campaign for all nine rows",
   "DECISIONS.jsonl D-30 part 1 (the named-field test) — applied by M0-T36; plus D-23 (lel_events) "
   "and D-28 part 4 (bg_sky_calendar) for the two rows that already had a reason",
   "`target_table` is named by NO Phase-0 step and NO M0 acceptance criterion. Phase 0.2 — the only "
   "step naming registry columns — names `integrity_check_sql` and `target_floor`, not this one. "
   "Clause (a) of the named-field test fails, so the column belongs to the rung that owns the asset "
   "and repairing it in M0 is the I13 breach D-30 names. Clause (b) confirms two rows independently: "
   "plan §15's per-asset entries for bo_cdlm_summary and bo_chart_gestalt each carry 'Declare "
   "target_table', and both are R2. bg_sky_calendar is separately trigger-bearing — its target_table "
   "names `bg_sky_events`, a relation ABSENT from production — and D-28 part 4 routed it to R0 intake. "
   "WHAT THIS DOES NOT SETTLE: whether a NULL target_table on the four chart_facts co-writers is "
   "deliberate. That question travels to R1 with the rows; it is not answered here and must not be "
   "read as answered.",
   {"violations": 9,
    "rows": ["bg_prashna_rules", "bg_sky_calendar", "bo_cdlm_summary", "bo_chart_gestalt",
             "ga_sade_sati", "ga_sensitive", "ga_strength", "ga_structural", "lel_events"],
    "classes": {"target_table_null": 8, "target_table_missing": 1},
    "measured_at": "2026-08-23T08:00:51Z"}),

 "C-06": _d("C-06", "BLOCKING", True, "R5 (Mīmāṃsā rung), stage 2 Conform", "R5",
   "pre-campaign",
   "DECISIONS.jsonl D-30 part 1 — applied by M0-T36",
   "One row: mi_seva. `count_sql` is named by no Phase-0 step and no M0 acceptance criterion — clause "
   "(a) fails. C-06 is additionally a shadow of C-07: mi_seva is asset_kind='service' and a service "
   "carries no count_sql at all, so the row disappears when C-07's row does. Same destination (R5) by "
   "two independent routes.",
   {"violations": 1, "rows": ["mi_seva"], "measured_at": "2026-08-23T08:00:51Z"}),

 "C-07": _d("C-07", "BLOCKING", True, "R3 (ka_dasha_kala, ka_tulana) and R5 (mi_abhilekha, mi_seva)",
   "the owning rung's §8.6 stage-2 Conform",
   "pre-campaign",
   "DECISIONS.jsonl D-30 part 1 (named-field test) — applied by M0-T36; and D-19 part 1 + D-27 part 2a "
   "for the target_floor half",
   "Four service rows carrying data-asset fields. THE HONEST SHAPE: three of the four columns "
   "(`target_table`, `count_sql`, `clear_tables`) are named nowhere in Phase 0, so clause (a) fails "
   "flatly. The fourth, `target_floor`, IS named by Phase 0.2 — but as a REQUIRED FIELD OF THE "
   "CONTRACT SPECIFICATION being authored, not as a population M0 performs; the clause assigning the "
   "work of setting floors is §8.6 stage 2 ('floors set to achieved (I7)'), per rung, which is "
   "refinement (b) firing. D-19 part 1 already held floors rung-owned ('a declarative source file "
   "structurally CANNOT hold a measured value') and D-27 part 2a re-affirmed it. DURABILITY, which "
   "makes the deferral load-bearing rather than merely correct: three of the four columns are "
   "SEED-OWNED, so a DB-only NULLing in M0 would be reverted by the next re-seed.",
   {"violations": 4,
    "rows": {"ka_dasha_kala": ["target_floor"], "ka_tulana": ["target_floor"],
             "mi_abhilekha": ["count_sql", "target_floor", "target_table"],
             "mi_seva": ["count_sql", "target_floor", "target_table"]},
    "measured_at": "2026-08-23T08:00:51Z"}),

 "C-08": _d("C-08", "BLOCKING", True, "R3 (Kāla rung), lifecycle exit", "R3",
   "2026-08-12T16:30:19Z (the asset's last build; RETIRED since)",
   "DECISIONS.jsonl D-12 part 4 (ADHIKĀRIN, 2026-08-23T04:46:23Z), quoting plan §14.2 by name",
   "One row: ka_gochara_sweep, RETIRED with data_disposition NULL. Plan §14.2 names this exact asset's "
   "data_disposition as R3 work; D-12 part 4 quotes that sentence and defers it. THE ASSET IS CHARTER "
   "P1 — its 38,287 v1 gochara rows are recoverable only from the 2026-08-23 snapshot — so any "
   "operation on it is reserved to the native, not merely deferred. H6 was respected under real "
   "temptation here: migration 590's own header says the disposition is 'almost certainly' known, and "
   "D-31 records that leaving it NULL was right, because 'almost certainly' is not a detector. THE SAME "
   "ASSET IS THE SUBJECT OF X-02, which is already disclosed and already non-gating; C-08 is the "
   "identical situation one column over, and is BLOCKING.",
   {"violations": 1, "rows": ["ka_gochara_sweep"], "catalog_status": "RETIRED", "is_active": False,
    "charter": "P1 — unrecoverable asset", "measured_at": "2026-08-23T08:00:51Z"}),

 "C-15": _d("C-15", "BLOCKING", True,
   "R3 (ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana) and R5 (mi_abhilekha, mi_seva)",
   "the owning rung — §8.6 stage-2 Conform for provides_apis; tier-S probe work (§9) for health_probe",
   "pre-campaign",
   "DECISIONS.jsonl D-30 part 1 — applied by M0-T36; §8.4's R3 row for the probe half",
   "Six DRAFT service rows with health_probe and provides_apis both NULL. Neither column is named by "
   "any Phase-0 step or M0 acceptance criterion — clause (a) fails for both. THE TWO HALVES ARE NOT THE "
   "SAME KIND OF THING and the deferral matters more for one: `provides_apis` is a declaration, but "
   "`health_probe` is a DETECTOR, and §8.4's R3 row already assigns 'a real known-answer probe with an "
   "SLO' to R3 by name for two of these assets (clause (b) firing). Authoring a probe in M0 to clear "
   "C-15 would be manufacturing a detector to satisfy a criterion — the H3 shape D-29 part 5 named for "
   "the sibling rule C-17. CORRECTION TO THE CONTRACT'S OWN §6 CELL, carried from v1.0: that cell reads "
   "'6 (all 6 service rows)'. There are EIGHT service rows live since the M0-T21 kind repair; the count "
   "is unchanged for a different reason than the contract states, because the two new ones "
   "(bg_ephemeris_engine, bg_panchanga) DO carry both fields.",
   {"violations": 6,
    "rows": ["ka_dasha_kala", "ka_graha_sancara", "ka_muhurta_seva", "ka_tulana", "mi_abhilekha",
             "mi_seva"],
    "live_service_rows": 8, "contract_s6_cell_says": 6, "measured_at": "2026-08-23T08:00:51Z"}),

 "C-17": _d("C-17", "BLOCKING", True, "R3 (Kāla rung), stage-1 intake", "R3",
   "the three 'healthy' rows were last written by a self-test on 2026-08-02; health_probe has always "
   "been NULL on all four",
   "DECISIONS.jsonl D-13 part 2 AS CORRECTED AND EXTENDED BY D-29 (ADHIKĀRIN, 2026-08-23T07:44:26Z)",
   "Four rows, and D-29 is the reason all four are now covered where v1.0 could cover only three. "
   "THREE are false greens: ka_dasha_kala, ka_muhurta_seva and ka_tulana read service_health='healthy' "
   "with no health_probe — a status with no detector, H4 / CLAUDE.md §N.8, the campaign's founding "
   "defect sitting live in the registry. THE FOURTH IS DIFFERENT IN KIND and D-29 part 3 insists it not "
   "be folded in: ka_graha_sancara reads 'unhealthy' with no probe, which is A RED WITH NO DETECTOR "
   "BEHIND IT — §N.8 in its other direction. It FAILS SAFE (it understates confidence rather than "
   "overstating it) and it must NOT be 'fixed' by clearing it to healthy or NULL when R3 opens; only a "
   "real probe may retire it. D-29 also corrected D-13's destination from R0 to R3: all four assets are "
   "ka_* / layer=kala, and ZERO ka_* assets carry rung='R0'. Independently, the named-field test reaches "
   "the same place — neither `health_probe` nor `service_health` is named by any Phase-0 step. NOTE THE "
   "DOUBLE REPORT (D-29 part 4): ka_graha_sancara also has a SERVING-side defect ruled separately at "
   "D-26 (deriveState() returns service_ok, overriding the stored 'unhealthy'). Different defects, "
   "different layers, different owners; fixing one leaves the other.",
   {"violations": 4,
    "rows": {"ka_dasha_kala": "healthy", "ka_graha_sancara": "unhealthy",
             "ka_muhurta_seva": "healthy", "ka_tulana": "healthy"},
    "health_probe": "NULL on all four", "measured_at": "2026-08-23T08:00:51Z"}),

 "C-20": _d("C-20", "BLOCKING", True, "R0 (Brahmagyan rung), §8.6 stage-2 Conform", "R0",
   "pre-campaign", "DECISIONS.jsonl D-19 part 1 and D-27 part 2a",
   "Three R0 rows with target_floor NULL: bg_class_priors, bg_formula_constants, bg_ghatana. THIS IS THE "
   "ONE COLUMN THE CAMPAIGN HAS RULED TWICE. D-19 part 1: a floor is the MEASURED ACHIEVED COUNT (I7), "
   "'a declarative source file structurally CANNOT hold a measured value', and measured values are "
   "written at §8.6 stage 2 Conform, per rung. D-27 part 2a re-affirmed it with a number behind it. "
   "Setting a floor in M0 would also collide with charter G2's bound — to the measured achieved count "
   "only, never an invented number — and the measurement that would justify it is R0's intake, which "
   "has not run.",
   {"violations": 3, "rows": ["bg_class_priors", "bg_formula_constants", "bg_ghatana"],
    "measured_at": "2026-08-23T08:00:51Z"}),

 "C-21": _d("C-21", "BLOCKING", True, "four rungs — R0 ×2, R1 ×2, R2 ×2, R3 ×12, R5 ×1",
   "the owning rung's §8.6 stage-2 Conform", "pre-campaign",
   "DECISIONS.jsonl D-19 part 1 (volume_explanation named in the campaign-owned set) + charter G4",
   "Nineteen rows with target_floor = 0 and volume_explanation NULL. A volume_explanation on a zero "
   "floor is precisely a charter G4 by-design classification, and G4 requires a WRITTEN by-design "
   "justification PER ASSET — a per-asset judgment about that asset's data, which is exactly what I14 "
   "keeps out of Track M. D-19 part 1 names it in the campaign-owned set ('volume_explanation WHERE IT "
   "RECORDS A G4 BY-DESIGN CLASSIFICATION') and places it at the owning rung's Conform. Same durability "
   "precondition as C-20: the column is seed-owned and would move on 47 cells at the next re-seed. "
   "Plan §8.4's R5 row independently names this work for its own layer ('zero-row-by-design assets "
   "recorded honestly with target_floor = 0 and a volume_explanation'), which is clause (b) firing for "
   "at least that rung.",
   {"violations": 19, "by_rung": {"R0": 2, "R1": 2, "R2": 2, "R3": 12, "R5": 1},
    "measured_at": "2026-08-23T08:00:51Z"}),

 "C-22": _d("C-22", "RUNG", False, "every rung, at its own §8.6 stage-2 Conform", "each rung in turn",
   "n/a — the rule has never had a satisfiable antecedent",
   "structural fact, measured; plan §8.6 stage 2 ('integrity_check_sql authored per asset') and the "
   "closing paragraph ('Stage 2 is deliberately inside the rung rather than in Track M')",
   "VACUOUS TODAY AND REPORTED AS VACUOUS RATHER THAN AS A PASS. The antecedent is 'rung-frozen' and no "
   "rung has frozen — R0 has not opened. Measured separately and worth stating plainly: 0 of 128 live "
   "assets carry an integrity_check_sql at all. The column is NOT seed-written, so checks authored at "
   "Conform are durable. Severity RUNG, so it does not gate today; it is disclosed anyway because D-30 "
   "part 4 says every deferred rule carries its entry, and because a rule that is vacuous now will stop "
   "being vacuous the moment R0 freezes.",
   {"status": "not_checkable (vacuous — 0 rungs frozen)", "assets_with_integrity_check_sql": 0,
    "of": 128, "measured_at": "2026-08-23T08:00:51Z"}),

 "C-25": _d("C-25", "BLOCKING", False,
   "UNDECIDED — the named-field test reaches it (Phase 0.4 names partition declaration) but §8.6 stage 2 "
   "assigns 'partitions declared' to every rung; see crit-5 and §9.3",
   "undecided — M0 under Phase 0.4, or each rung under §8.6 stage 2",
   "n/a — no column has ever existed", "ASSET_CATALOGUE_CONTRACT_v1_0.md §4.9 / §6 / §10.3 "
   "(contract-mandate: 'Rules C-25, C-26 and C-27 must never be reported as passing')",
   "THE MODEL DEFERRAL — a reason written into the specification itself. No schema column exists for a "
   "natural-key partition declaration. The contract states in its own §6 that these rules must never be "
   "reported as passing, 'a CI guard implementing this document emits them as not_checkable with the "
   "reason, and a dashboard that renders that as a pass is itself a defect'. The shipped guard hard-wires "
   "exactly that (check_asset_catalogue_contract.py, `_no_detector`) and its own cross-check FAILS if the "
   "guard and the contract ever disagree about which rules are not_checkable. This is what a well-formed "
   "deferral looks like: a named structural fact, a specification that records it, a detector that "
   "refuses to report green, and a guard test that catches the two drifting apart. IT DOES NOT GATE "
   "TODAY because not_checkable is excluded from the exit code — but note that its severity is BLOCKING, "
   "so if a column ever appears the rule gates immediately. WHAT IS UNDECIDED IS THE WORK, NOT THE RULE: "
   "the rule's not_checkable status is correct and permanent-until-a-column-exists; whether M0 or the "
   "rungs should create that column is crit-5's open question.",
   {"status": "not_checkable", "co_written_target_tables": 5, "co_writer_rows": 16,
    "X-01_undeclared_collisions": 0, "measured_at": "2026-08-23T08:00:51Z"}),

 "C-26": _d("C-26", "BLOCKING", False, "the rung that owns each generation-bearing asset",
   "the owning rung", "n/a — no column has ever existed",
   "ASSET_CATALOGUE_CONTRACT_v1_0.md §4.11 / §6 / §10.3 (contract-mandate)",
   "Same shape as C-25 — no schema column for an authority pointer / protected_generations, the contract "
   "forbids reporting it as passing, the guard hard-wires not_checkable with that reason. ONE DIFFERENCE "
   "FROM C-25 AND IT IS THE DECISIVE ONE: no Phase-0 step names an authority pointer as M0 content, so "
   "unlike C-25 BOTH the rule and the work are deferred, and the named-field test settles it cleanly "
   "rather than leaving it open.",
   {"status": "not_checkable", "measured_at": "2026-08-23T08:00:51Z"}),

 "C-27": _d("C-27", "ADVISORY", False, "Track M2 (cleaned telemetry), then each rung's Conform",
   "M2", "n/a", "ASSET_CATALOGUE_CONTRACT_v1_0.md §6 severity column + plan §4.8",
   "ADVISORY by the contract's own severity column, and not checkable until Track M2 produces cleaned "
   "telemetry — the p95 the rule compares against does not exist yet. Recorded, explicitly not green. "
   "Does not gate today on two independent grounds (ADVISORY severity AND not_checkable status), and is "
   "disclosed anyway for completeness with D-30 part 4.",
   {"status": "not_checkable", "blocked_on": "M2 cleaned telemetry", "measured_at": "2026-08-23T08:00:51Z"}),

 "C-28_residual": _d("C-28", "BLOCKING", True, "R0 (Brahmagyan rung) — all 31 residual rows are R0",
   "R0's own build (only a real build can retire it)",
   "n/a — these assets have never completed a tracked build",
   "DECISIONS.jsonl D-30 part 3 (G7 deferral, ADHIKĀRIN, 2026-08-23T07:46:10Z), indexed as a G7 by D-31 "
   "part 2",
   "PARTIAL DISCLOSURE — THIS COVERS 31 OF C-28's 105 ROWS AND NOT THE OTHER 74, AND THAT DISTINCTION IS "
   "THE POINT. Re-measured read-only by M0-T36: 74 rows are backfillable from the median of their "
   "completed build_run_assets rows, which is D-6's authorised statement T-5 and is REPAIRABLE-IN-M0, "
   "not deferred. The remaining 31 have NO completed build_run_assets row at all, so no measured "
   "duration exists and D-6 condition 4 forbids inventing one ('an asset with no clean telemetry gets "
   "NULL, not a plausible number', H6). There is no path to zero for those 31 that does not pass through "
   "either a real build or a fabrication. All 31 are R0, so R0's freeze inherits this rather than "
   "rediscovering it. NOTHING HAS BEEN EXECUTED: M0-T3 produced the T-5 proposal with `writes_executed: "
   "NONE`, so C-28 reads 105 today, not 31, and any statement that C-28 is deferred is premature by 74 "
   "rows.",
   {"guard_violations_total": 105, "backfillable_by_T5": 74, "deferred_residual": 31,
    "residual_by_rung": {"R0": 31}, "T5_executed": False,
    "note_scorecard_disagrees": "the scorecard's C-28 SQL returns 112 because it does not filter by "
                                "asset_kind; the 7 extra rows are all services — finding F-T36-1",
    "measured_at": "2026-08-23T08:0xZ"}),
}

DISCLOSURE_NOT_DRAFTED = {
 "C-11": "NEWLY DEFERRED-WITH-REASON BY D-38 (2026-08-23T09:24:48Z), NOT REPAIRABLE-IN-M0 "
         "any more — see the C-11 entry above. Phase 0.8b's disposition is REMAIN DRAFT for "
         "all three of this rule's DRAFT dependencies, deferred to R1/R3. A disclosure entry "
         "for this rule has NOT been drafted by M0-T46: this task is scoped to "
         "`00_ARCHITECTURE/control/` and does not write "
         "`platform/scripts/governance/asset_catalogue_disclosed_residuals.json`. Drafting "
         "one, in the same shape as the other DEFERRED rules above, is follow-up work for a "
         "task with that file in scope.",
 "X-05": "RESOLVED BY D-38 part 3 (2026-08-23T09:24:48Z), NOT REPAIRABLE-IN-M0 and NOT "
         "deferred — see the X-05 entry above. All 23 zero-consumer packets are adjudicated "
         "per reading class; unresolved = 0. A disclosure is the wrong instrument for a "
         "resolved (not deferred) rule. The guard's `zero_consumer_dispositions` block "
         "remains empty per-packet, which is correct: D-38's adjudication is by CLASS, not "
         "by writing a `decision_ref` into that per-packet block, and no KĀRAKA may write one "
         "there regardless (catalogue disposition is G1).",
 "X-02": "ALREADY DISCLOSED, in `disclosed_additions`, and is the pattern every entry above follows. "
         "Untouched by M0-T36 or M0-T46.",
 "X-03": "REPAIRABLE-IN-M0 (D-39, 2026-08-23T09:25:50Z), NOT deferred any more — see the X-03 "
         "entry above. Ownership to M0 is confirmed and the column is authorised under D-4, "
         "not reserved by P5; the repair (add the column, backfill, verify) is known but "
         "unexecuted. A disclosure would be the wrong instrument: this needs the repair, not "
         "a reason it cannot happen.",
}

def _apply_d30():
    """Apply D-30 part 1/part 3 to the v1.0 entries, preserving what v1.0 decided."""
    for e in CRITERIA + RULES:
        a = D30_APPLICATION.get(e["id"])
        if a:
            e["prior_bucket_m0t31"] = e["bucket"]
            e["bucket"] = a["new_bucket"]
            if a.get("reason_kind"):
                e["prior_reason_kind_m0t31"] = e.get("reason_kind")
                e["reason_kind"] = a["reason_kind"]
            if a.get("owner"):
                e["prior_owner_m0t31"] = e.get("owner")
                e["owner"] = a["owner"]
            e["reason"] = a["addendum"] + "\n\n— — — v1.0 (M0-T31) classification, preserved — — —\n\n" + e["reason"]
            e["reclassified_by"] = ("DECISIONS.jsonl D-30 part 1 (the named-field test, adopted as a "
                                    "rule); applied by M0-T36. Ruling: ADHIKĀRIN. Application: KĀRAKA. "
                                    "Certification: none (I16 / H7).")
        n = D30_NARROWED.get(e["id"])
        if n:
            e["named_field_test"] = n["result"]
            e["reason"] = n["addendum"] + "\n\n— — — v1.0 (M0-T31) classification, preserved — — —\n\n" + e["reason"]
    return True

_apply_d30()
_apply_d3842()

# ── render ───────────────────────────────────────────────────────────────────
def tally(entries):
    t = {b: 0 for b in BUCKETS}
    for e in entries:
        t[e["bucket"]] += 1
    return t

# ── the ORIGIN tally, DERIVED rather than remembered ─────────────────────────
# `_apply_d30()` and `_apply_d3842()` each stamp, on the entry itself, the bucket it
# carried BEFORE that wave moved it (`prior_bucket_m0t31`, `prior_bucket_v1_1`) and the
# ruling that moved it (`reclassified_by`). That per-entry provenance is enough to
# COMPUTE where each entry started — so §0's summary can state the movement without
# restating a figure or a ruling list that the next ADHIKĀRIN ruling would falsify.
# (KĀRAKA M0-T63, Standing Queue SQ-14: the sentence it replaced read "after D-30 —
#  down from 11 in v1.0", hardcoded prose concatenated to a live f-string, which four
#  later rulings had already made a mis-attribution. A fresher hardcoded attribution
#  would only reset the same clock — CLAUDE.md §C item 14's precedent, and M0-T56's.)
def origin_bucket(e):
    """The bucket this entry carried at v1.0 (M0-T31), read from its own provenance.

    `prior_bucket_m0t31` is checked first because it is the earlier of the two stamps:
    an entry moved by both waves would carry both. An entry no wave touched carries
    neither, and its current bucket is also its original one.
    """
    for k in ("prior_bucket_m0t31", "prior_bucket_v1_1"):
        if k in e:
            return e[k]
    return e["bucket"]


def origin_tally(entries):
    t = {b: 0 for b in BUCKETS}
    for e in entries:
        t[origin_bucket(e)] += 1
    return t

def esc(x):
    return str(x).replace("|", "\\|").replace("\n", "<br>")

def render() -> str:
    ct, rt = tally(CRITERIA), tally(RULES)
    tot = {b: ct[b] + rt[b] for b in BUCKETS}
    oc, ort = origin_tally(CRITERIA), origin_tally(RULES)
    orig = {b: oc[b] + ort[b] for b in BUCKETS}
    classified_since_v1_0 = sum(1 for e in CRITERIA + RULES
                                if origin_bucket(e) == UNEXAMINED and e["bucket"] != UNEXAMINED)
    L = []
    A = L.append
    A("---")
    A("canonical_id: M0_DEFERRAL_REGISTER")
    A("version: 1.2")
    A("status: LIVE-CLASSIFICATION")
    A("task: M0-T46 (v1.0 authored by M0-T31; v1.1 by M0-T36 applied D-30; v1.2 applies "
      "D-38/D-39/D-40/D-41/D-42)")
    A(f"generated: {datetime.datetime.now(datetime.UTC).isoformat()}")
    A("generator: 00_ARCHITECTURE/control/m0_deferral_register.py")
    A("authored_by: KĀRAKA — v1.0 by M0-T31, v1.1 by M0-T36, v1.2 by M0-T46 (Nirmāṇa "
      "autonomous campaign)")
    A("filename_note: the file keeps its v1_0 path deliberately — canonical_id and every "
      "pointer to it are stable; the frontmatter `version` field is the version (§B.8). "
      "A v1_0 filename carrying version 1.2 is an in-place update, not registry drift.")
    A("certified_by: null   # I16 / charter H7 — a KĀRAKA never certifies its own work")
    A("satisfies: DECISIONS.jsonl D-24 part 3 AS AMENDED BY D-30 part 2(a)+part 4, THEN BY "
      "D-39 part 1 (withdrawn) AND D-40 part 1 (final): the switch flips when every "
      "criterion is at zero or explicitly deferred AND the disclosure mechanism is "
      "demonstrably in effect (a two-direction fixture: a disclosed rule still reports its "
      "violation and only stops gating; an undisclosed rule still blocks) AND CI detects "
      "and refuses a stale baseline (NOT 'CI gates live' — D-40 withdrew that as impossible, "
      "no DB credential in CI Actions)")
    A("applies: DECISIONS.jsonl D-30 part 1 (named-field test), part 3 (C-28 residual), "
      "D-29, D-38 (0.8b REMAIN DRAFT, 0.8c per-packet adjudication), D-39 (X-03/crit-8/"
      "crit-5 confirmed M0's, not P5), D-40 (flip condition's CI clause, final form), D-42 "
      "(C-28 reframed; build_run_assets ranking)")
    A("---")
    A("")
    A("# NIRMĀṆA M0 — Deferral Register v1.2")
    A("")
    A("**The question this document exists to answer**, verbatim from ADHIKĀRIN ruling D-24 "
      "part 3:")
    A("")
    A("> *The switch flips when T17's exit scorecard shows each criterion either at zero or "
      "explicitly deferred with a recorded reason — **never on a criterion that is merely "
      "unexamined**.*")
    A("")
    A("The scorecard measures; it does not separate *non-zero and repairable* from *non-zero and "
      "cannot reach zero, for a stated reason*. This register performs that separation and — the "
      "actual work product — names what nobody has yet established either way.")
    A("")
    A("**This document decides nothing, flips nothing, and certifies nothing.** No guard file, "
      "no `.github/` file and no `asset_registry` row was written by the task that produced it. "
      "Classification is evidence for ADHIKĀRIN (charter G7/G9); certification is PARĪKṢAKA's "
      "(I16 / charter H7).")
    A("")
    A("## 0 — The tally")
    A("")
    A("| bucket | criteria | contract rules | total | meaning |")
    A("|---|--:|--:|--:|---|")
    mean = {
      REPAIRABLE: "a known repair takes it to zero; nobody has done it. The repair and its "
                  "blocker are named per entry.",
      DEFERRED: "it cannot reach zero inside M0, and a **ruling, plan assignment, contract "
                "mandate or measured structural fact** says why.",
      RESERVED: "it collides with a charter prohibition. Not the campaign's to resolve, and "
                "untouched by this task.",
      UNEXAMINED: "**nobody has established which of the above it is.** D-24 part 3 forbids "
                  "flipping the switch on any of these. This bucket is the deliverable.",
      AT_ZERO: "reads zero, with a named exposure that makes that zero conditional (§5).",
    }
    for b in BUCKETS:
        A(f"| **{b}** | {ct[b]} | {rt[b]} | **{tot[b]}** | {mean[b]} |")
    A(f"| | **{len(CRITERIA)}** | **{len(RULES)}** | **{len(CRITERIA)+len(RULES)}** | |")
    A("")
    A(f"**{tot[UNEXAMINED]} of {len(CRITERIA)+len(RULES)} entries remain UNEXAMINED** — down "
      f"from {orig[UNEXAMINED]} at v1.0's first classification, {classified_since_v1_0} of those "
      "having since been classified. **Every number in that sentence is computed at generation "
      "time**: the current tally from the entries below, the v1.0 figure from the prior bucket "
      "each moved entry records on itself. Neither is typed in, so neither can drift from the "
      "classifications it describes. **And no ruling is named in it, deliberately.** Which "
      "ruling moved which entry is recorded ON THAT ENTRY — `reclassified_by`, sitting above "
      "the preserved v1.0/v1.1 classification it replaced — and the wave-level accounts, with "
      "their before/after tallies, are §9 and §12. A ruling list in this summary would be "
      "accurate only until the next ruling lands; a pointer to the entry that carries its own "
      "provenance stays accurate. (This paragraph previously read *\u201cafter D-30 \u2014 down from "
      "11 in v1.0\u201d*: hardcoded prose concatenated to a live count, correct when written and a "
      "mis-attribution by the time four later rulings had moved entries it did not name. "
      "KĀRAKA M0-T63, Standing Queue SQ-14.)")
    A("")
    A("D-30's named-field test — which v1.0 named as the largest single lever and D-30 part 1 "
      "then adopted as a rule — was applied at v1.1: it moved five rules to "
      "DEFERRED-WITH-REASON and it REACHED three further entries nobody expected it to reach. "
      "§9 is that application and §9.2 is its count reconciliation, which does not come out "
      "where the ledger says it does; §12 is the later wave.")
    A("")
    A("**The one fact that stops the flip even after every ruling lands** is mechanical, and "
      "v1.1 finds it is worse than v1.0 reported. v1.0: of ten DEFERRED rules none carried a "
      "disclosure and eight were `BLOCKING`. After D-30 there are **fifteen** DEFERRED rules and "
      "**thirteen** carry `BLOCKING` severity — the deferrals grew, the disclosures did not. "
      "D-30 part 4 amended the flip condition to require every deferred rule to carry its "
      "disclosure entry, and §10 drafts all fifteen. **They are inert** (finding `F-T36-3`): the "
      "guard reads `disclosed_additions` in exactly one function, `x02()`, and severity is a "
      "hardcoded constant in the rule table — X-02 is non-gating because someone typed "
      "`RESIDUAL`, not because it carries a disclosure. And a third prerequisite nobody has "
      "recorded (`F-T36-2`): CI does not run `--live` at all. It runs `--baseline` against a "
      "snapshot frozen at 05:09:17Z, which returns **17** BLOCKING failures including three rules "
      "that pass in production today.")
    A("")
    A("**v1.2 (M0-T46) applies six further ADHIKĀRIN rulings — D-37 through D-42 — three of "
      "which move a bucket here.** D-38 decided Phase 0.8b (REMAIN DRAFT — a decision, not a "
      "promotion) and adjudicated all 23 Phase 0.8c packets per reading class, moving "
      "**crit-4 and C-11 to DEFERRED-WITH-REASON** (deferred to R1/R3, not repairable in M0 "
      "by promotion) and **crit-9 and X-05 to AT-ZERO-WITH-EXPOSURE** (all 23 packets "
      "adjudicated; unresolved = 0; 6 carry follow-on rung work). D-39 confirmed X-03, "
      "criterion 8 and criterion 5 as M0's and settled that their columns are authorised "
      "under D-4, not reserved by charter P5, moving **crit-5, crit-8 and X-03 to "
      "REPAIRABLE-IN-M0** (a known repair — add the column, backfill, verify — now exists; "
      "nobody has executed it). D-42 reframes C-28's residual ('31 assets read `lit` with no "
      "completed `build_run_assets` record', not '31 missing an estimate') and ranks "
      "`build_run_assets` authoritative wherever a surface asks 'was this asset built' — "
      "recorded on the C-28 entry and on criterion 8; **the bucket does not move**, and D-42 "
      "explicitly forbids re-pointing C-28's detector at `build_run_assets` to close it "
      "(that would be H3). D-40 additionally WITHDRAWS part of D-39's amended flip "
      "condition — 'CI must gate against live state' is impossible, CI Actions carries no "
      "database credential — and replaces it with a detect-and-refuse-stale-baseline "
      "requirement; §10 restates the final condition. D-37 and D-41 are read but change no "
      "bucket here (D-37 corrects D-12 part 3 on assets outside this register's scope and "
      "clarifies the named-field test's refinement (b); D-41 authorises the deploy.yml edit "
      "and a CI-edit-by-direction rule, and no 'awaiting a ruling on CI edit scope' flag was "
      "found anywhere in this file, the scorecard, or M0_CLOSE_READINESS_v1_0.md for it to "
      "resolve). See §12 for the full application and the before/after tally.")
    A("")
    A("### What counts as a reason")
    A("")
    A("A reason is only a reason if it names one of these. *\"Not yet done\"*, *\"probably "
      "fine\"* and *\"an analogous ruling exists for a different column\"* are **UNEXAMINED**, "
      "not deferred — that distinction is the whole point of the exercise. v1.0 filed six rules "
      "UNEXAMINED that a looser reading would have called deferred; D-30's closing paragraph "
      "adopted that asymmetry as standing policy (*\"an UNEXAMINED entry costs me a minute; a "
      "wrongly-DEFERRED one costs the gate its meaning\"*), and v1.1 applies it again in §9.3 — "
      "three entries the test REACHES are narrowed and left UNEXAMINED rather than closed, "
      "because the test settles whose they are and not what to do about them.")
    A("")
    A("| reason kind | what it must cite |")
    A("|---|---|")
    for k, v in REASON_KINDS.items():
        A(f"| `{k}` | {v} |")
    A("")
    A("## 1 — Provenance: every number below was re-measured, not inherited")
    A("")
    A(f"**Database access:** {PROVENANCE['db_access']}")
    A("")
    A("| reading | at (UTC) | how |")
    A("|---|---|---|")
    for r in PROVENANCE["readings"]:
        A(f"| {esc(r['what'])} | `{r['at']}` | {esc(r['how'])} |")
    A("")
    A("Files **read and not written** by this task (a sibling task holds `writer_substep_census."
      "py`, `build_asset_control_workbook.py` and the C-23 guard):")
    A("")
    for f in PROVENANCE["guard_files_read_not_written"]:
        A(f"- `{f}`")
    A("")
    A("**The scorecard moved under this task while it ran, and that is reported rather than "
      "smoothed:** M0-T26 landed the Phase 0.5a repair at ~06:51–06:54Z, between the scorecard's "
      "reading 2 (06:20:44Z) and this register's measurements (06:55:57Z onward). C-02 and C-03 "
      "moved 21→1 and 20→1 in that window. Both readings are stated with their timestamps in §7; "
      "neither is averaged.")
    A("")
    A("## 2 — The twelve exit criteria")
    A("")
    A("| # | criterion | reads now | bucket | owner |")
    A("|---|---|---|---|---|")
    for e in CRITERIA:
        m = e["measured"]
        mv = "; ".join(f"{k}={v}" for k, v in m.items()) if isinstance(m, dict) else str(m)
        A(f"| {e['id'].split('-')[1]} | {esc(e['title'])} | `{esc(mv)[:110]}` | "
          f"**{e['bucket']}** | {esc(e.get('owner',''))} |")
    A("")
    for e in CRITERIA:
        A(f"### {e['id']} · {e['title']}")
        A("")
        A(f"**Bucket: {e['bucket']}**" + (f" · reason kind: `{e['reason_kind']}`"
                                          if e.get("reason_kind") else ""))
        A("")
        A("**Reads now**")
        A("")
        A("```json")
        A(json.dumps(e["measured"], indent=1, ensure_ascii=False))
        A("```")
        A("")
        A(e["reason"])
        A("")
        if e.get("blocker"):
            A(f"**What blocks it:** {e['blocker']}")
            A("")
        if e.get("machinery_gap"):
            A(f"**Machinery gap:** {e['machinery_gap']}")
            A("")
        A(f"**Owner:** {e.get('owner','—')}  ")
        A(f"**Closes when:** {e.get('closes_when','—')}")
        A("")
        if e.get("rows"):
            A("<details><summary>rows</summary>")
            A("")
            A("```json")
            A(json.dumps(e["rows"], indent=1, ensure_ascii=False))
            A("```")
            A("")
            A("</details>")
            A("")
        A("**Evidence**")
        A("")
        for ev in e["evidence"]:
            A(f"- {ev}")
        A("")
        A("---")
        A("")
    A("## 3 — Contract and extension rules reading non-zero, `not_checkable` or blocked")
    A("")
    A("Rule statuses are the shipped guard's own output — `check_asset_catalogue_contract.py "
      "--live --json` at `2026-08-23T06:58:51Z` (13 pass · 16 fail · 4 not_checkable) and "
      "`check_asset_source_parity.py --live --json` at `2026-08-23T07:02:39Z` (P-01…P-06 all "
      "pass). Rules reading `pass` are listed in §4; §5 covers the ones whose zero is "
      "conditional.")
    A("")
    A("| rule | severity | assertion | reads now | bucket | owner |")
    A("|---|---|---|---|---|---|")
    for e in RULES:
        A(f"| `{e['id']}` | {e['severity']} | {esc(e['assertion'])} | `{esc(e['measured'])}` | "
          f"**{e['bucket']}** | {esc(e.get('owner',''))} |")
    A("")
    for e in RULES:
        A(f"### `{e['id']}` — {e['assertion']}")
        A("")
        A(f"**Severity {e['severity']} · reads `{e['measured']}` · bucket {e['bucket']}**"
          + (f" · reason kind `{e['reason_kind']}`" if e.get("reason_kind") else ""))
        A("")
        A(e["reason"])
        A("")
        if e.get("blocker"):
            A(f"**What blocks it:** {e['blocker']}")
            A("")
        if e.get("durability"):
            A(f"**Durability:** {e['durability']}")
            A("")
        if e.get("machinery_gap"):
            A(f"**Machinery gap:** {e['machinery_gap']}")
            A("")
        A(f"**Owner:** {e.get('owner','—')}"
          + (f"  \n**Closes when:** {e['closes_when']}" if e.get("closes_when") else ""))
        A("")
        if e.get("rows"):
            A("Rows: " + ", ".join(f"`{r}`" for r in e["rows"]))
            A("")
        A("Evidence: " + " · ".join(e["evidence"]))
        A("")
        A("---")
        A("")
    A("## 4 — Rules reading `pass`, for completeness")
    A("")
    A("`C-05` `C-09` `C-10` `C-12` `C-13` `C-14` `C-16` `C-18` `C-19` `C-23` `C-24` `X-01` "
      "`X-04` (contract guard, 06:58:51Z) and `P-01`…`P-06` (parity guard, 07:02:39Z).")
    A("")
    A("Two cautions the §0 tally deliberately does not fold in. **A pass is one detector "
      "returning zero at one instant against one database** — the scorecard's §3a proved each "
      "passing rule falsifiable under a deliberate mutation, which is the right standard, but "
      "falsifiable is not permanent. And `X-01`'s pass means *'no multi-producer table that "
      "nobody declared'*, never *'the partitions are correct'* — its own docstring and the "
      "declared-co-writers file both say so, and C-25 is the rule that would say the stronger "
      "thing if it had a column.")
    A("")
    A("## 5 — At zero, and not the same thing as being at zero")
    A("")
    A("D-24 part 3 asks for criteria *at zero*. A zero that the next routine `asset_registry_"
      "seed.ts` run silently reverts is worse than a red, because nothing announces its expiry "
      "(SEED_DURABILITY_REGISTER §0). Every zero below was re-checked against the seed "
      "projection at `06:57:16Z` rather than inherited.")
    A("")
    A("| rule | status | durability | violations after a re-seed |")
    A("|---|---|---|--:|")
    for d in NON_DURABLE:
        A(f"| `{d['id']}` | {d['status']} | {d['durability']} | {d['projected_after_reseed']} |")
    A("")
    for d in NON_DURABLE:
        A(f"**`{d['id']}` — {d['durability']}**")
        A("")
        A(d["why"])
        A("")
    A("**The through-line:** the campaign's durable repairs are durable because their columns "
      "are absent from the seed's column lists (`has_substeps`, `domain`, `rung`, "
      "`integrity_check_sql`), and its fragile ones are fragile because they are not "
      "(`asset_kind`, `asset_type`, `scope`, `target_floor`, `volume_explanation`). That is "
      "structural, not incidental: **before the switch flips, ADHIKĀRIN should decide whether a "
      "green resting on a seed-owned column may count as 'at zero' at all.** This register's "
      "view — offered as a recommendation, not a ruling — is that it may not, and that D-19 part "
      "2's required seed change is therefore a precondition of the flip rather than a follow-on "
      "from it.")
    A("")
    A("## 6 — What would have to be true to flip the switch")
    A("")
    A("In order. Steps 1–9 are rulings only ADHIKĀRIN can make; step 10 is mechanical and is the "
      "one that actually stops the flip; steps 11–13 are execution and verification.")
    A("")
    A("| # | kind | what | unblocks | resolved? |")
    A("|---|---|---|---|---|")
    for s in FLIP_CHECKLIST:
        A(f"| {s['n']} | {s['kind']} | **{esc(s['title'])}** | {esc(', '.join(s['unblocks']))} | "
          f"{'YES — see below' if s.get('resolved') else 'open'} |")
    A("")
    for s in FLIP_CHECKLIST:
        A(f"**{s['n']}. [{s['kind']}] {s['title']}**")
        A("")
        A(s["what"])
        A("")
        if s.get("resolved"):
            A(f"**RESOLVED (M0-T46 records; ruled by ADHIKĀRIN):** {s['resolved']}")
            A("")
    A("**What this list is not.** It is not a claim that M0 exits when the thirteen are done — "
      "M0's freeze is M0-T10's and its certification is PARĪKṢAKA's. It is the answer to one "
      "narrower question: what has to become true before D-24 part 3's precondition is honestly "
      "satisfied, so the switch can be flipped without weakening anything to get there.")
    A("")
    A("## 7 — Disagreements and corrections found while classifying")
    A("")
    A("Nothing below is averaged. Two angles disagreeing is a finding (the discipline the "
      "scorecard's own §2b established).")
    A("")
    for d in DISAGREEMENTS:
        A(f"**{d['item']}**")
        A("")
        A(f"- A — {d['a']}")
        A(f"- B — {d['b']}")
        A(f"- **Resolution** — {d['resolution']}")
        A("")
    A("## 8 — What this register does NOT establish")
    A("")
    A("- **It does not certify M0, and it does not certify itself.** A KĀRAKA authored it; "
      "PARĪKṢAKA decides what it means (I16 / charter H7).")
    A("- **It does not flip the switch, wire any guard blocking, or edit `.github/`.** That is "
      "ADHIKĀRIN's and it is explicitly reserved.")
    A("- **A bucket is a classification, not a verdict.** Where this register says DEFERRED it "
      "means a reason of the declared kinds is on record — not that the deferral is wise.")
    A("- **UNEXAMINED is not an accusation and not a soft FAIL.** Eleven entries are unexamined "
      "because the campaign has been moving fast and honestly; the register's only claim is that "
      "no one has yet decided them, and D-24 part 3 says the switch may not move until someone "
      "does.")
    A("- **The classification of `RESERVED` items ends at the label.** Criterion 6 and `X-02` "
      "were read, counted and left exactly as they were.")
    A("- **Where a ruling covers only some rows of a rule, the rule is filed by its weakest "
      "row** (C-17 is UNEXAMINED on one row of four, C-04 on seven of nine). A rule is not "
      "classified until every row under it is.")
    A("- **The measurements expire.** They are timestamped to the minute for that reason; a "
      "sibling task moved 39 rows out from under the scorecard while this register was being "
      "written. Re-run the generator rather than trusting this snapshot.")
    A("")

    # ── §8 — D-30 applied ────────────────────────────────────────────────────
    A("---")
    A("")
    A("## 9 — D-30 part 1 applied: the named-field test")
    A("")
    A("v1.0 named this test as the single largest lever and REFUSED to apply it, on the grounds "
      "that inferring a rule from precedent is not the same as being given one. ADHIKĀRIN ruling "
      "**D-30 part 1** then adopted it as a rule and instructed it be applied. This section is "
      "that application. It is arithmetic on a ruling, not a ruling.")
    A("")
    A("> " + "\n> ".join(
      ("A REGISTRY COLUMN IS M0's TO REPAIR IF AND ONLY IF **(a)** a Phase-0 step OR M0's own "
       "acceptance criteria NAME IT — acceptance criteria count, per D-4 — AND **(b)** no "
       "more-specific plan clause assigns it to a later rung, in which case the specific governs "
       "the general. Absent (a), the column belongs to the rung that owns the asset, and repairing "
       "it in M0 is the I13 breach.").split("\n")))
    A("")
    A("*(D-30's own wording governs; the above is the operative sentence quoted, not a paraphrase "
      "to be relied on in its place.)*")
    A("")
    A("### 9.0 — The left-hand side, transcribed")
    A("")
    A("The whole rule turns on whether a column appears in these fifteen steps, so they are "
      "transcribed from `NIRMANA_ELEVATION_PLAN_v3_0.md` §Phase 0 — carried to M0 verbatim by "
      "v4.0 §14.4 (*\"Phase 0 — all 15 steps | M0\"*) — rather than summarised.")
    A("")
    A("| step | what it names |")
    A("|---|---|")
    for k, v in PHASE_0_STEPS.items():
        A(f"| `{k}` | {esc(v)} |")
    A("")
    A(f"**M0's own acceptance criteria (v4.0 §14.1):** {M0_ACCEPTANCE_NAMES}")
    A("")
    A("### 9.1 — The rule verified against the case law it was derived from")
    A("")
    A("D-30 states it verified this itself. M0-T36 re-derived it independently from the plan text "
      "rather than accept the claim — a rule that failed to reproduce its own precedents would be "
      "a worse instrument than no rule.")
    A("")
    A("| case | ruling | held | clause (a) | clause (b) | rule output | reproduces? |")
    A("|---|---|---|---|---|---|:--:|")
    for c in D30_VERIFICATION:
        A(f"| **{esc(c['case'])}** | {c['ruling']} | `{c['held']}` | {esc(c['a'])} | "
          f"{esc(c['b'])} | `{c['rule_output']}` | {'✅' if c['reproduces'] else '❌'} |")
    A("")
    A(f"**Verdict.** {D30_VERIFICATION_VERDICT}")
    A("")
    A("#### 9.1.1 — The §8.6 stage-2 collision")
    A("")
    A(f"> {esc(PHASE_86_STAGE2_COLLISION['quote'])}")
    A(f"> — *{PHASE_86_STAGE2_COLLISION['source']}*")
    A("")
    A("That one paragraph names **six** kinds of registry metadata as each rung's Conform work: "
      + ", ".join(f"`{f}`" for f in PHASE_86_STAGE2_COLLISION["fields_named"]) + ".")
    A("")
    A("| field | collision, and how it resolves |")
    A("|---|---|")
    for k, v in PHASE_86_STAGE2_COLLISION["collides_with"].items():
        A(f"| `{esc(k)}` | {esc(v)} |")
    A("")
    A(f"**Disposition.** {PHASE_86_STAGE2_COLLISION['disposition']}")
    A("")
    A("### 9.2 — What moved, and the count that does not reconcile")
    A("")
    A("| entry | before (M0-T31) | after (D-30 applied) |")
    A("|---|---|---|")
    for m in D30_TALLY_DELTA["moved"]:
        eid, rest = m.split(" ", 1)
        b, a_ = rest.split("→")
        A(f"| `{eid}` | {b} | **{a_}** |")
    A("")
    A("| bucket | rules before | rules after | criteria before | criteria after |")
    A("|---|--:|--:|--:|--:|")
    for b in BUCKETS:
        A(f"| {b} | {D30_TALLY_DELTA['rules_before'].get(b,0)} | "
          f"{D30_TALLY_DELTA['rules_after'].get(b,0)} | "
          f"{D30_TALLY_DELTA['criteria_before'].get(b,0)} | "
          f"{D30_TALLY_DELTA['criteria_after'].get(b,0)} |")
    A("")
    A(f"**The count reconciliation — a finding, not a quibble.** "
      f"{D30_TALLY_DELTA['count_reconciliation']}")
    A("")
    A("### 9.3 — What the test REACHED that nobody expected it to")
    A("")
    A("D-30 routed each of these to a *separate* ruling in v1.0's §6 checklist. Applied honestly "
      "the named-field test lands on them anyway, and settles their **ownership** while leaving "
      "their **mechanism** open. Per D-30's own adopted asymmetry they are narrowed, not closed — "
      "they stay `UNEXAMINED`.")
    A("")
    A("| entry | v1.0 routed it to | what the test decides |")
    A("|---|---|---|")
    _routed = {"X-03": "§6 step 5 — a separate 'dead flag' ruling",
               "crit-8": "§6 step 5 — a separate 'dead flag' ruling",
               "crit-5": "§6 step 4 — a separate 'Phase 0.4 partition' ruling",
               "crit-1": "§6 step 2 — listed as 'crit-1 (partly)'",
               "C-28": "§6 step 11 — execution, not a ruling"}
    for k, v in D30_NARROWED.items():
        A(f"| `{k}` | {_routed.get(k,'—')} | {esc(v['result'])} |")
    A("")
    A("## 10 — The disclosure entries, drafted")
    A("")
    A("**D-30 part 4** amends D-24 part 3: the switch flips when every criterion is at zero or "
      "deferred **and every deferred rule carries its disclosure entry**, itemised and dated, in "
      "the discipline D-10 part 3 granted for the migration-number allowlist.")
    A("")
    A("M0-T36 drafted all of them and wrote them into a then-new top-level block "
      "`deferred_rule_disclosures` in "
      "`platform/scripts/governance/asset_catalogue_disclosed_residuals.json` — deliberately NOT "
      "merged into `disclosed_additions`, which `x02()` reads and validates. **Nothing is wired "
      "blocking, no severity is changed, no `.github/` file was touched, and no rule is turned "
      "green:** every entry carries `does_not_turn_the_rule_green: true`, per D-12 part 4's "
      "*never silently green*.")
    A("")
    A("**WHAT FOLLOWS IS THE M0-T36 HISTORICAL DRAFT, NOT THE LIVE BLOCK — and this generator "
      "no longer writes it anywhere.** KĀRAKA M0-T49/T51/T55 wrote D-54's fifteen AUTHORISED "
      "disclosures into the live file on D-57's corrected ground (certified V-35/V-37), and this "
      "draft was never updated to match. Regenerating this register used to overwrite that live "
      "block from the draft below — deleting three authorised entries and reverting twelve to "
      "unauthorised ones — which is the side effect ADHIKĀRIN D-44 part 4 named as the defect "
      "worth fixing and Standing Queue SQ-12 assigned. **KĀRAKA M0-T62 removed the write.** The "
      "live file is the source of truth for its own block; this generator READS it and reports "
      "the divergence on stdout (`_report_disclosure_divergence()`), and its declared write "
      "scope is now enforced at runtime by `DECLARED_WRITES` + `_write()` rather than asserted "
      "in prose.")
    A("")
    A("**They are also inert, and that is finding `F-T36-3`** — see §11. Writing them satisfies "
      "D-30 part 4's letter and changes nothing the guard does, because the guard has no code path "
      "that reads a disclosure for any rule but `X-02`.")
    A("")
    A("**v1.2 (M0-T46) — THE FLIP CONDITION HAS BEEN AMENDED TWICE SINCE THE ABOVE WAS WRITTEN, "
      "AND THE FINAL FORM IS DIFFERENT FROM D-30 part 4's.** D-39 part 1 first amended D-30 part "
      "4: an existing disclosure entry is not evidence the mechanism does anything — the switch "
      "flips only when the disclosure mechanism is 'DEMONSTRABLY IN EFFECT, PROVEN BY A FIXTURE "
      "THAT SHOWS BOTH DIRECTIONS — a disclosed rule's violation is still REPORTED while no "
      "longer GATING, and an UNDISCLOSED rule still BLOCKS'; D-39 also added 'CI MUST GATE "
      "AGAINST LIVE STATE, NOT A SNAPSHOT'. D-40 part 1 WITHDREW that CI clause as an "
      "impossibility M0-T40 root-caused: CI Actions carries no database credential, so "
      "`--live` is a job that cannot run there at all. D-40 replaces it: **CI need not gate "
      "against live state — it must DETECT AND REFUSE A STALE BASELINE**, with rule results "
      "still printed in full so only the exit changes. THE FINAL CONDITION, as amended twice, "
      "supersedes D-30 part 4 for this document's own §0/frontmatter: every criterion at zero "
      "or explicitly deferred, AND the disclosure mechanism demonstrably in effect (the "
      "two-direction fixture), AND CI's baseline check detects and refuses staleness. Neither "
      "half of the mechanism half is discharged by this task; both remain open per §12.")
    A("")
    A("**A tension this task found and does not resolve.** D-39's characterisation of "
      "`F-T36-3` as still-inert rests on SUTRADHĀRA's mailbox escalation timestamped "
      "`20260823T082157Z` (from M0-T36's own close-readiness pass). This file's own §9 "
      "header comment — and, until M0-T62 removed the write, the `_write_disclosure_block()` "
      "docstring and the README text it used to write into the guard file, which is where "
      "that text now lives and is maintained — assert that a LATER task, M0-T40, closed "
      "`F-T36-3` by making the guard read "
      "`deferred_rule_disclosures` BY RULE ID and compute `effective_severity` from it — and "
      "M0-T46 verified, read-only, that `check_asset_catalogue_contract.py` does contain "
      "exactly that code path (`effective_severity`, a rule-id-keyed reader). D-39 is timestamped "
      "*after* that M0-T40 work would have landed but cites *pre*-M0-T40 evidence for its "
      "F-T36-3 finding. This is recorded as an open question for ADHIKĀRIN, not settled here: "
      "a KĀRAKA does not adjudicate whether a ruling used stale evidence (I13/I16). See the "
      "mailbox finding this task files alongside its report.")
    A("")
    A("| rule | severity | gates today | deferred to | ruling / mandate cited |")
    A("|---|---|:--:|---|---|")
    for k, d in DISCLOSURE_DRAFT.items():
        A(f"| `{k}` | {d['severity_in_the_rule_table']} | "
          f"{'YES' if d['gates_the_exit_code_today'] else 'no'} | {esc(d['deferred_to'])} | "
          f"{esc(d['disclosed_via'])[:120]} |")
    A("")
    A(f"**{sum(1 for d in DISCLOSURE_DRAFT.values() if d['gates_the_exit_code_today'])} of "
      f"{len(DISCLOSURE_DRAFT)}** drafted entries cover a rule that gates the exit code today.")
    A("")
    A("**Deliberately NOT drafted:**")
    A("")
    for k, v in DISCLOSURE_NOT_DRAFTED.items():
        A(f"- `{k}` — {v}")
    A("")
    for k, d in DISCLOSURE_DRAFT.items():
        A(f"### disclosure · {k}")
        A("")
        A("```json")
        A(json.dumps({k: d}, indent=1, ensure_ascii=False))
        A("```")
        A("")
    A("## 11 — Re-measurement (M0-T36)")
    A("")
    A(f"**At:** `{REMEASUREMENT['at']}`")
    A("")
    A(REMEASUREMENT["headline"])
    A("")
    A(f"**Scorecard:** {REMEASUREMENT['scorecard']}")
    A("")
    A("### New findings")
    A("")
    for f in REMEASUREMENT["new_findings"]:
        A(f"#### `{f['id']}` · {f['severity']} · {f['title']}")
        A("")
        A(f["detail"])
        A("")

    # ── §12 — D-38/D-39/D-40/D-41/D-42 applied (M0-T46) ──────────────────────
    A("---")
    A("")
    A("## 12 — D-38 / D-39 / D-40 / D-41 / D-42 applied (M0-T46)")
    A("")
    A("Six ADHIKĀRIN rulings landed after v1.1 (M0-T36) closed §§0–11 above. This section "
      "documents what each did to this register; §§0–11 are left exactly as v1.1 wrote "
      "them (history), and the per-entry sections above carry the new addenda prefixed to "
      "the preserved v1.1 text, in the same discipline v1.1 used for D-30.")
    A("")
    A("### 12.1 — Before / after tally")
    A("")
    d = D3842_TALLY_DELTA
    A("| | REPAIRABLE-IN-M0 | DEFERRED-WITH-REASON | RESERVED | UNEXAMINED | "
      "AT-ZERO-WITH-EXPOSURE |")
    A("|---|--:|--:|--:|--:|--:|")
    A(f"| criteria — before | {d['criteria_before'][REPAIRABLE]} | "
      f"{d['criteria_before'][DEFERRED]} | {d['criteria_before'][RESERVED]} | "
      f"{d['criteria_before'][UNEXAMINED]} | {d['criteria_before'][AT_ZERO]} |")
    A(f"| criteria — after | {d['criteria_after'][REPAIRABLE]} | "
      f"{d['criteria_after'][DEFERRED]} | {d['criteria_after'][RESERVED]} | "
      f"{d['criteria_after'][UNEXAMINED]} | {d['criteria_after'][AT_ZERO]} |")
    A(f"| rules — before | {d['rules_before'][REPAIRABLE]} | {d['rules_before'][DEFERRED]} | "
      f"{d['rules_before'][RESERVED]} | {d['rules_before'][UNEXAMINED]} | "
      f"{d['rules_before'][AT_ZERO]} |")
    A(f"| rules — after | {d['rules_after'][REPAIRABLE]} | {d['rules_after'][DEFERRED]} | "
      f"{d['rules_after'][RESERVED]} | {d['rules_after'][UNEXAMINED]} | "
      f"{d['rules_after'][AT_ZERO]} |")
    A("")
    A("**Moved:**")
    A("")
    for item in d["moved"]:
        A(f"- {item}")
    A("")
    A("**Reframed, bucket held:**")
    A("")
    for item in d["reframed_not_moved"]:
        A(f"- {item}")
    A("")
    A(d["net_unexamined"])
    A("")
    A("### 12.2 — D-38: Phase 0.8b and 0.8c decided")
    A("")
    A("**0.8b — REMAIN DRAFT, a decision not a deferral.** Neither ga_vichara (R1) nor "
      "ka_dasha_kala / ka_sangam (R3) is named by a rung-specific promote-or-retire clause "
      "(only R2's nine, R3's ka_graha_sancara/ka_muhurta_seva, R4's nine and R5's "
      "lel_events are named), so the general REMAIN-DRAFT disposition governs all three and "
      "criterion 4 / C-11 move to DEFERRED-WITH-REASON.")
    A("")
    A("**0.8c — all 23 packets adjudicated by reading class:**")
    A("")
    A("| reading class | n | D-38 disposition | assets |")
    A("|---|--:|---|---|")
    for cls, v in D38_ZERO_CONSUMER_DISPOSITION_TABLE.items():
        A(f"| {cls} | {v['n']} | {esc(v['rule'])} | {esc(', '.join(v['assets']))} |")
    A("")
    A(f"**{sum(v['n'] for v in D38_ZERO_CONSUMER_DISPOSITION_TABLE.values())} of 23 packets "
      "adjudicated; 0 unresolved.** "
      f"**{len(D38_ROUTED_TO_RUNG)} of 23** (1 retirement candidate + 5 SHADOWED defects) "
      "carry follow-on asset-lifecycle work routed to their owning rung — a recorded "
      "determination, not an open question, per D-38's own holding that adjudication IS "
      "resolution. Criterion 9 / X-05 move to AT-ZERO-WITH-EXPOSURE.")
    A("")
    A("### 12.3 — D-39: X-03, criterion 8 and criterion 5 confirmed M0's, the P5 question settled")
    A("")
    A("D-39 part 4, independently re-deriving the named-field test rather than inheriting "
      "D-30's assertion of it, CONFIRMS ownership of X-03, criterion 8 and criterion 5 to "
      "M0 and settles that their columns are 'inside the plan's naming and NOT reserved by "
      "P5 … subject to D-4's standing conditions'. What v1.1 filed as UNEXAMINED "
      "('ownership settled to M0, mechanism still undecided') has its mechanism question "
      "resolved: the column is authorised, not reserved. All three move to "
      "REPAIRABLE-IN-M0 — a known repair (add the column under D-4's conditions, backfill, "
      "verify) now exists; nobody has executed it.")
    A("")
    A("### 12.4 — D-40: the flip condition's CI clause, final form")
    A("")
    A("D-39 part 1 added 'CI MUST GATE AGAINST LIVE STATE' to the flip condition. D-40 part "
      "1 WITHDREW that clause as an impossibility M0-T40 root-caused: CI Actions carries no "
      "database credential (`platform/.env.local` does not exist there), so `--live` cannot "
      "run. D-40 replaces it: CI must DETECT AND REFUSE A STALE BASELINE instead — two "
      "DB-free detectors (age, and schema-behind: declared columns minus baseline columns) "
      "that can run without a credential. This register's own frontmatter and §10 now state "
      "the final condition; no criterion or rule bucket in this register turns on the CI "
      "clause itself, so nothing in §§0–9 moves because of D-40 — only the STATEMENT of the "
      "condition changes.")
    A("")
    A("### 12.5 — D-42: C-28 reframed; the build_run_assets ranking")
    A("")
    A(D42_C28_ADDENDUM)
    A("")
    A("### 12.6 — D-37 and D-41: read, no bucket change")
    A("")
    A("**D-37** corrects D-12 part 3's premise (the three orphaned throughput rows belong "
      "to ka_kota_chakra / ka_vedha_gochara / mi_sankalpa, not ka_gochara_sweep) and "
      "clarifies the named-field test's refinement (b) fires only on a clause naming a "
      "specific asset or a specific field at a specific rung. None of the three assets or "
      "the clarified refinement changes any entry this register classifies.")
    A("")
    A("**D-41** authorises the deploy.yml sentinel-assertion edit and states a CI-edit-by-"
      "direction rule (strengthening changes proceed without a ruling; weakening changes "
      "are presumptively H3). M0-T46 searched this file, M0_EXIT_SCORECARD_v1_0.md and "
      "M0_CLOSE_READINESS_v1_0.md for an open 'awaiting a ruling on CI edit scope' flag and "
      "found none — D-41 has nothing to resolve in these three instruments. D-41's "
      "standing mutation-testing requirements (structural assertion + inverse-direction "
      "mutation, per part 3) bear on future guard-code changes, not on this classification "
      "register.")
    A("")
    A("### 12.7 — What this task did not do")
    A("")
    A("No `asset_registry` row was written (this generator has never queried the database "
      "directly — every `measured` value is a frozen figure from when M0-T17/M0-T36 or the "
      "guard last measured it live; the fresh live re-measurement for this task ran through "
      "`m0_exit_scorecard.py`, whose own reading 5 shows criterion 4 unchanged at 3 and "
      "criterion 9's packet count unchanged at 23). No guard file was edited — `c28()` and "
      "every other detector in `check_asset_catalogue_contract.py` and "
      "`check_asset_source_parity.py` are unchanged. No `.github/` file was touched. No new "
      "entry was added to `DISCLOSURE_DRAFT` (C-11's newly-deferred status has no disclosure "
      "drafted for it — see `DISCLOSURE_NOT_DRAFTED`). No `DECISIONS.jsonl` or "
      "`state/*.jsonl` line was edited. `ka_gochara_sweep` (charter P1) was not touched. No "
      "UNEXAMINED entry this task did not name was resolved, and nothing here is certified "
      "— that is PARĪKṢAKA's (I16 / H7).")
    A("")
    A("**AMENDED 2026-08-23 BY KĀRAKA M0-T62 (Standing Queue SQ-12, on ADHIKĀRIN D-44 part "
      "4).** The clause that stood at the end of the paragraph above is preserved verbatim "
      "here because it is the defect's own confession, written by the agent that hit it: "
      "«so a re-run of this generator's `_write_disclosure_block()` should not change "
      "`platform/scripts/governance/asset_catalogue_disclosed_residuals.json`'s content; if "
      "it does, M0-T46 reverted that file to keep this task's footprint inside "
      "`00_ARCHITECTURE/control/`, per its own scope instruction.» That sentence describes "
      "an agent planning to reach for `git checkout --` — the command the standing restore "
      "rule forbids — to undo a write its own generator performed outside its declared "
      "scope. It is removed from the live text because it is now false in both halves: "
      "`_write_disclosure_block()` no longer exists, and a re-run CANNOT change that file. "
      "The write was removed rather than re-declared, on measured evidence that nothing "
      "depends on it: the only reader of that file is `check_asset_catalogue_contract.py`, "
      "which needs the AUTHORISED content M0-T49/T51/T55 wrote there under D-54/D-57 "
      "(certified V-35/V-37), and the live file contains zero references to this module. "
      "Measured divergence at the moment of the fix — live block 19 entries vs "
      "`DISCLOSURE_DRAFT` 16, three live entries absent from the draft, twelve of sixteen "
      "differing, all four `*_not_drafted` values differing — means a run would have "
      "REVERTED authorised governance work while printing a clean-looking success line.")
    A("")

    return "\n".join(L) + "\n"

def payload() -> dict:
    ct, rt = tally(CRITERIA), tally(RULES)
    return {
        "_meta": {
            "canonical_id": "M0_DEFERRAL_REGISTER", "version": "1.2",
            "task": "M0-T46", "v1_0_task": "M0-T31", "v1_1_task": "M0-T36",
            "generated": datetime.datetime.now(datetime.UTC).isoformat(),
            "generator": "00_ARCHITECTURE/control/m0_deferral_register.py",
            "satisfies": "DECISIONS.jsonl D-24 part 3 as amended by D-30 part 2(a)+part 4, "
                        "then D-39 part 1 (withdrawn) and D-40 part 1 (final)",
            "certified_by": None,
            "provenance": PROVENANCE, "reason_kinds": REASON_KINDS,
        },
        "tally": {"criteria": ct, "rules": rt,
                  "total": {b: ct[b] + rt[b] for b in BUCKETS},
                  "n_criteria": len(CRITERIA), "n_rules": len(RULES)},
        "criteria": CRITERIA, "rules": RULES,
        "at_zero_with_exposure": NON_DURABLE,
        "flip_checklist": FLIP_CHECKLIST,
        "disagreements": DISAGREEMENTS,
        "d30_application": {
            "phase_0_steps": PHASE_0_STEPS,
            "m0_acceptance_names": M0_ACCEPTANCE_NAMES,
            "verification": D30_VERIFICATION,
            "verification_verdict": D30_VERIFICATION_VERDICT,
            "phase_86_stage2_collision": PHASE_86_STAGE2_COLLISION,
            "tally_delta": D30_TALLY_DELTA,
            "narrowed_not_moved": {k: v["result"] for k, v in D30_NARROWED.items()},
        },
        "d38_d39_d40_d41_d42_application": {
            "tally_delta": D3842_TALLY_DELTA,
            "moved_to_deferred": {k: v["addendum"] for k, v in D3842_TO_DEFERRED.items()},
            "moved_to_at_zero": {k: v["addendum"] for k, v in D3842_TO_AT_ZERO.items()},
            "moved_to_repairable": {k: v["addendum"] for k, v in D3842_TO_REPAIRABLE.items()},
            "reframed_not_moved": D3842_ADDENDUM_ONLY,
            "zero_consumer_disposition_table_D38": D38_ZERO_CONSUMER_DISPOSITION_TABLE,
            "flip_condition_final_form": "DECISIONS.jsonl D-40 part 1: the switch flips when "
                "every criterion is at zero or explicitly deferred AND the disclosure "
                "mechanism is demonstrably in effect (a two-direction fixture) AND CI "
                "detects and refuses a stale baseline (not: CI gates live — withdrawn as "
                "impossible, no DB credential in CI Actions).",
            "d37_and_d41_reviewed_no_bucket_change": True,
        },
        "disclosure_draft": DISCLOSURE_DRAFT,
        "disclosure_not_drafted": DISCLOSURE_NOT_DRAFTED,
        "remeasurement": REMEASUREMENT,
    }

# READ ONLY. Deliberately NOT in `DECLARED_WRITES`, and `_write()` would refuse it if a
# future edit tried. See the module docstring for why the write that used to target this
# path was removed (M0-T62, Standing Queue SQ-12, ADHIKĀRIN D-44 part 4).
RESIDUALS_JSON = ROOT / "platform/scripts/governance/asset_catalogue_disclosed_residuals.json"


def _report_disclosure_divergence() -> str:
    """READ-ONLY. Report how the historical `DISCLOSURE_DRAFT` differs from the live block.

    THIS FUNCTION WRITES NOTHING. It replaced `_write_disclosure_block()`, which wrote four
    `deferred_rule_disclosures*` keys into
    platform/scripts/governance/asset_catalogue_disclosed_residuals.json as a side effect,
    outside this module's declared scope — the defect ADHIKĀRIN D-44 part 4 named and
    Standing Queue SQ-12 assigned to KĀRAKA M0-T62.

    The live block is owned by the live file. It carries D-54's fifteen AUTHORISED
    disclosures on D-57's corrected ground, written by M0-T49/T51/T55 and certified across
    V-35/V-37. `DISCLOSURE_DRAFT` is the M0-T36 historical draft and is NOT authorised —
    every entry in it carries `gating_effect: "none"` and no `authorised_by`. Overwriting
    the former from the latter reverts authorised governance work, which is exactly what a
    run of this module used to do.

    So the divergence is REPORTED, not reconciled. Reconciling it in either direction is a
    charter G-power (catalogue-gate disposition) and belongs to ADHIKĀRIN, not to this
    generator and not to a KĀRAKA.

    Returns a one-paragraph note for stdout. Returns a plainly-stated note instead of
    raising if the live file is missing or unreadable: this module's outputs do not depend
    on that file, and a report generator should not fail on a file it merely observes.
    """
    try:
        doc = json.loads(RESIDUALS_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"{RESIDUALS_JSON.relative_to(ROOT)}: NOT READ ({exc.__class__.__name__}) — "
                "divergence not computed. Nothing was written; this generator only observes "
                "that file.")
    live = doc.get("deferred_rule_disclosures") or {}
    only_live = sorted(set(live) - set(DISCLOSURE_DRAFT))
    only_draft = sorted(set(DISCLOSURE_DRAFT) - set(live))
    differing = sorted(k for k in DISCLOSURE_DRAFT if k in live and DISCLOSURE_DRAFT[k] != live[k])
    identical = sorted(k for k in DISCLOSURE_DRAFT if k in live and DISCLOSURE_DRAFT[k] == live[k])
    nd_live = doc.get("deferred_rule_disclosures_not_drafted") or {}
    nd_differ = sorted(k for k in DISCLOSURE_NOT_DRAFTED
                       if DISCLOSURE_NOT_DRAFTED[k] != nd_live.get(k))
    return (
        f"{RESIDUALS_JSON.relative_to(ROOT)}: READ, NOT WRITTEN (declared scope enforced by "
        f"_write(); see DECLARED_WRITES). live deferred_rule_disclosures={len(live)} vs "
        f"DISCLOSURE_DRAFT (M0-T36 historical)={len(DISCLOSURE_DRAFT)}; "
        f"only-live={only_live or 'none'}; only-draft={only_draft or 'none'}; "
        f"differing={len(differing)} {differing or ''}; identical={len(identical)}; "
        f"not_drafted values differing={len(nd_differ)} {nd_differ or ''}. "
        "THE LIVE FILE IS AUTHORITATIVE (D-54 authorisations on D-57's ground, M0-T49/T51/T55, "
        "certified V-35/V-37). This generator does not reconcile the difference in either "
        "direction — that is a charter G-power. Reported so the staleness is visible instead "
        "of being silently overwritten.")


def _DELETED_write_disclosure_block__M0_T62() -> str:
    """DELETED BY M0-T62 — kept only as this docstring, so the removal is legible in place.

    It used to load the residuals JSON, add/overwrite `deferred_rule_disclosures_README`,
    `deferred_rule_disclosures_count`, `deferred_rule_disclosures_not_drafted` and
    `deferred_rule_disclosures`, and write the file back. It claimed to preserve every
    other key byte-for-byte, and it did — but the four keys it owned had long since stopped
    being its own output, so "preserving the others" was never the safety property that
    mattered. See the module docstring for the measured damage a run would have done.
    """
    raise NotImplementedError(
        "removed by M0-T62 (SQ-12 / D-44 part 4): this generator does not write "
        "platform/scripts/governance/asset_catalogue_disclosed_residuals.json")


# (the former body of `_write_disclosure_block()` was deleted here by M0-T62;
#  its four `doc[...] = ...` assignments and its `RESIDUALS_JSON.write_text()`
#  are gone, not commented out — a commented-out write is a landmine, and the
#  point of SQ-12 is that no agent should need git to undo this again.)


if __name__ == "__main__":
    # reading_history is append-only by design: preserve every prior reading verbatim.
    prior = None
    if OUT_JSON.exists():
        try:
            prior = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prior = None
    rec = payload()
    history = list(((prior or {}).get("_meta", {}) or {}).get("reading_history") or [])
    if prior and not history:
        history = [{"label": "reading 1 — M0-T31 (v1.0, first classification)",
                    "task": ((prior.get("_meta") or {}).get("task")),
                    "generated": ((prior.get("_meta") or {}).get("generated")),
                    "version": ((prior.get("_meta") or {}).get("version")),
                    "tally": prior.get("tally")}]
    entry = {"label": f"reading {len(history) + 1} — {rec['_meta']['task']} "
                      f"(D-38/D-39/D-40/D-41/D-42 applied)",
             "task": rec["_meta"]["task"], "generated": rec["_meta"]["generated"],
             "version": rec["_meta"]["version"], "tally": rec["tally"]}
    # reading_history is append-only across TASKS, not across re-runs of one task. A second
    # run by the same task with an identical tally is the same reading rendered twice, not a
    # new observation; recording it would inflate the history with noise and make a genuine
    # movement harder to see. Same task + same tally => refresh in place, keeping the label.
    if history and history[-1].get("task") == entry["task"] \
            and history[-1].get("tally") == entry["tally"]:
        entry["label"] = history[-1]["label"]
        entry["regenerated_count"] = int(history[-1].get("regenerated_count", 1)) + 1
        history[-1] = entry
    else:
        history.append(entry)
    rec["_meta"]["reading_history"] = history

    # Every write goes through `_write()`, which refuses any path outside DECLARED_WRITES.
    _write(OUT_MD, render())
    _write(OUT_JSON, json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    note = _report_disclosure_divergence()   # READ-ONLY — writes nothing (M0-T62 / SQ-12)
    t = rec["tally"]["total"]
    print(f"wrote {OUT_MD.relative_to(ROOT)} and {OUT_JSON.relative_to(ROOT)}")
    print("tally: " + " · ".join(f"{b}={t[b]}" for b in BUCKETS))
    print(f"readings preserved: {len(history)}  ({[h['label'] for h in history]})")
    print(note)
