#!/usr/bin/env python3
"""Generate the Nirmāṇa per-layer analysis-receipt pin record.

Why this script exists
----------------------
`nirmana-l0-analysis-receipts.ts` was hand-maintained committed output with no
generator.  That is the defect behind the convergence-pin drift recorded in
CAMPAIGN_STATE: a pin nobody can regenerate is a pin nobody can verify.
Generalising the receipt spine to six layers without a generator would multiply
that hazard by six (adjudication #1715, Conductor ruling, requirement 4).

What a "pin" is
---------------
One record per layer, holding:

  asset_prefix            the writer-id prefix that identifies the layer
  convergence_commit      the reviewed commit whose writer inventory this pins
  writer_inventory_sha256 sha256 over the layer's slice of the writer inventory
  receipt_count           how many receipt bases the layer must produce
  non_writer_assets       manifest assets with no sidecar writer (probe/static/
                          empty obligations), which still need a receipt base

`writer_inventory_sha256` is what makes the spine **fail closed PER LAYER**: a
writer edit in one layer changes only that layer's aggregate, so only that
layer's receipts become unavailable.  A single global pin would let any layer's
writer fix silently invalidate every other layer's accepted analyses — the
cross-layer failure the original L0-only design could not even express.

L0's three pinned values are INPUTS here, never recomputed: re-deriving them
would invalidate 29 already-frozen L0 capsules.  `--check` proves they survive.

Usage
-----
  python -m scripts.generate.nirmana_analysis_layer_pins            # regenerate (needs DB)
  python -m scripts.generate.nirmana_analysis_layer_pins --check    # verify (no DB needed)
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

GENERATED = Path(__file__).resolve().parents[2] / "src" / "generated"
REPO_ROOT = Path(__file__).resolve().parents[3]
WRITER_DIGESTS_PATH = GENERATED / "nirmana-writer-digests.json"
PINS_PATH = GENERATED / "nirmana-analysis-layer-pins.json"

PINS_VERSION = "nirmana-analysis-layer-pins/v2"
LEGACY_PINS_VERSION = "nirmana-analysis-layer-pins/v1"
SUCCESSOR_SCHEMA_VERSION = "nirmana-analysis-layer-successor/v2"
DEFINITION_SCHEMA_VERSION = "nirmana-analysis-layer-definition/v1"
SOURCE_ACCEPTANCE_SCHEMA_VERSION = "nirmana-analysis-source-acceptance/v1"
ALLOWED_DELTA_CLASSIFICATIONS = frozenset(
    {
        "approved_intentional_change",
        "approved_intentional_and_derived_import_change",
        "derived_import_change",
        "generator_defect",
        "stale_receipt",
        "unapproved_foreign_source",
    }
)

# D-NATIVE-11 (#2258, native-ruled 2026-09-07): supporting infrastructure
# writers are registered in the orchestrator DAG (so they run and their
# dependents see them) but are NOT elevation-denominator assets -- they never
# join the frozen manifest, produce no terminal capsule, and are verified as
# part of the grounding of the assets they serve. They therefore stay OUT of
# receipt_count arithmetic, while remaining IN writer_inventory_sha256: a
# supporting writer's code change must still fail the spine closed and force
# a reviewed re-pin, exactly like any other writer in the layer.
# D-NATIVE-11 (#2258, native-ruled 2026-09-07): supporting infrastructure
# writers register in the DAG (seed row + digest inventory) but are NOT
# elevation-denominator assets — receipt membership excludes them so the
# 128-identity denominator is undisturbed. Adding a name here requires its
# own native ruling. Pravāha A2.5 (steward-directed, PR #2799;
# M20260930T195042-a4a0 Option A; SUPPORTING_WRITER_IDS addition flagged for
# native ruling in REVIEW_REQUEST_A2_5_V41_CANDIDATE_WRITER_v1_1 §3):
# ka_gochara_v4_41_candidate is a candidate-only writer, is_active=false in
# the seed (inert to all planners), never an elevation-denominator identity.
SUPPORTING_WRITERS = frozenset({"bo_grounding", "ka_gochara_v4_41_candidate"})
NON_WRITER_PREFIX_EXCEPTIONS = {"L5": frozenset({"lel_events"})}

LAYER_PREFIX = {
    "L0": "bg_",
    "L1": "ga_",
    "L2": "bo_",
    "L3": "ka_",
    "L4": "ph_",
    "L5": "mi_",
}

AUTHORITY_BINDINGS = {
    "CCD-018": {
        # The native-authorized controlled Jataka production rollout includes
        # fresh source review and release-blocker correction before protected
        # integration.  The decision register binds that narrow authority to
        # this exact session; it does not grant a general L5 re-pin capability.
        "authority_commit": "463c1dd66796356380fe2cab3103ad68b0d08d21",
        "evidence_commit": "463c1dd66796356380fe2cab3103ad68b0d08d21",
        "path": "00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md",
        "sha256": "dbe44c43c8df047d8e0de560aa5584217b4c0ffbaa963efed8c282dbcbf672a5",
        "decision_binding": "## CCD-018 — Jātaka controlled production rollout authority",
        "authority_identity_binding": "`JATAKA-CONTROLLED-PROD-ROLLOUT-20260927`",
    },
    "DP-SD-018": {
        # The approval identity remains immutable metadata.  Validation reads
        # the later integrated unblock record, which quotes that exact identity
        # and is reachable from every supported checkout of this branch.
        "authority_commit": "7f21f27b14a7909424591a530096dc2f5d6e2b13",
        "evidence_commit": "8c80cd46159d8cce7ce3450f20061d7e0db466e2",
        "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_RI02_AUTHORIZED_UNBLOCK_v1_0.md",
        "sha256": "b1bc568532980e787389d86f4d44ddc3ed4e3709f7133e68713899e13f4ddb26",
        "decision_binding": "strategy_decision: DP-SD-018",
        "authority_identity_binding": "`7f21f27b14a7909424591a530096dc2f5d6e2b13`",
    },
    "DP-SD-019": {
        # The strategy-side content identity remains immutable metadata.  The
        # permanent execution branch carries a reachable ledger snapshot that
        # binds the exact identity and decision without depending on a side ref.
        "authority_commit": "16590cc49f720e4200a8d9b6cad3f52b68e21792",
        "evidence_commit": "ec93db981193627c80cc71f583772717318f9d14",
        "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_STRATEGIC_LEDGER_v1_0.md",
        "sha256": "2e5c8bd0815f2be318eaa288d99fdb12313b93e133b2350237c13cb086dd802a",
        "decision_binding": "DP-SD-019",
        "authority_identity_binding": "`16590cc49f720e4200a8d9b6cad3f52b68e21792`",
    },
    "NATIVE-2026-09-24-L0-REPAIR-REPIN": {
        # L0 repair (PR #2727). The approval is the native's, recorded verbatim in
        # the evidence document with its provenance. The authority identity is the
        # tip of the PR at the moment of approval, which is also the successors'
        # source commit, so what was approved and what is pinned cannot diverge.
        "authority_commit": "101171f76517fa3c6b0b44fa9d1cc46358612eee",
        "evidence_commit": "a9701272d08388997b79b7203d20e207e165ca30",
        "path": "00_ARCHITECTURE/briefs/nirmana/L0_REPAIR_ANALYSIS_REPIN_DECISION_v1_0.md",
        "sha256": "6ade3fe137d777a8a7a1bf53527da540a398cfef03f93b70a1b493f02cddc3b9",
        "decision_binding": "status: L0_REPAIR_REPIN_APPROVED",
        "authority_identity_binding": "`101171f76517fa3c6b0b44fa9d1cc46358612eee`",
    },
    "D-E022": {
        # Pins re-admission at the PR #2731 merge (Pravaha A0.3). The native's
        # approval ("Accept all recommendations.", 2026-09-29) is recorded verbatim
        # in the evidence document; the authority identity is the commit that first
        # introduced that document. Scope: exactly one L1 and one L3 successor
        # admission, per MERGE_HYGIENE_12_10c_RUNBOOK step 2 / ESCALATIONS E-022.
        "authority_commit": "442f1ed955a701008b2a975c7df80d543fbbc67a",
        "evidence_commit": "f4cba9d606abffd6c73bee42307ea8cbfd733ae6",
        "path": "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/D_E022_PINS_READMISSION_AUTHORITY_v1_0.md",
        "sha256": "14f98475c61de92759e78021267a7c2b9dae936fb63d78de61c1beaa60658c7e",
        "decision_binding": "status: PINS_READMISSION_AUTHORIZED",
        "authority_identity_binding": "`442f1ed955a701008b2a975c7df80d543fbbc67a`",
    },
    "D-PINS-A2": {
        # Pins re-admission for the pravaha/a2-kernel-geometry merge (Pravaha
        # A2.3). The steward's decision (on the native's 2026-09-30 standing
        # authority, EVENTS.jsonl 2026-09-30T03:22:56Z) is recorded verbatim in
        # the evidence document; the authority identity is the commit that first
        # introduced that document. Scope: exactly one L3 successor admission
        # over the A2.1 kernel-geometry changeset (A2.2-accepted, Codex closure
        # round 3 ACCEPT on ee0dd335f). No other layer; no membership change.
        "authority_commit": "fa0b0a9a003624b8f39e30600e98460a60170bb2",
        # Evidence re-pointed 2026-09-30 (pravaha/pins-admit-2793): the lane
        # commit 1e5ce331fbb2833d2a2f3bd20448293b36def276 is not an ancestor of
        # main (the doc reached main through the #2764 squash); the squash
        # delivery commit 95e96d63c carries the byte-identical document
        # (sha256 verified unchanged), so main-side admissions can dereference
        # the authority evidence.
        "evidence_commit": "95e96d63cb8f5b58689d19f728266107f39df346",
        "path": "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/D_PINS_A2_PINS_READMISSION_AUTHORITY_v1_0.md",
        "sha256": "78814bbfa4fcf076cf70aebe8cc05855287151318d81e86018d4ceaf0868ca6c",
        "decision_binding": "status: PINS_READMISSION_AUTHORIZED",
        "authority_identity_binding": "`fa0b0a9a003624b8f39e30600e98460a60170bb2`",
    },
    "D-PINS-A5.4": {
        # Pins re-admission for the pravaha/a5-tier0s-repairs merge (PR #2769,
        # Pravaha A5.4 Tier 0-S repairs). The steward's decision (on the
        # native's 2026-09-30 standing authority, EVENTS.jsonl
        # 2026-09-30T13:02:03Z, message M20260930T130203-0531) is recorded
        # verbatim in the evidence document; the authority identity is the
        # commit that first introduced that document. Scope: exactly one L3
        # successor admission over the A5.4 repairs changeset, on top of main's
        # protected baseline l3:f4c69a6d0cd4:829354703812 (the D-PINS-A2
        # successor, never rewritten). No other layer; no membership change.
        "authority_commit": "e47d0b274ebf234ada8be7cfe82a34d5446384eb",
        "evidence_commit": "69382f6860f79c36ddb70b677ed42e234b4fb099",
        "path": "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/D_PINS_A5_4_PINS_READMISSION_AUTHORITY_v1_0.md",
        "sha256": "d50a9d8e19fe2ddec33ce55f9c61f2c2770eb0d7cbe88ae6732d28e7c9bf0765",
        "decision_binding": "status: PINS_READMISSION_AUTHORIZED",
        "authority_identity_binding": "`e47d0b274ebf234ada8be7cfe82a34d5446384eb`",
    },
    "D-PINS-A2.5": {
        # Pins re-admission for the pravaha/a25-v41-candidate-writer merge (PR
        # #2799, Pravāha A2.5). The steward's decision (on the native's
        # 2026-09-30 standing authority, EVENTS.jsonl 2026-10-01T06:46:16Z,
        # message M20261001T064616-8eed) is recorded verbatim in the evidence
        # document; the authority identity is the commit that first introduced
        # that document. Scope: exactly one L3 successor admission over the
        # A2.5 changeset — the ONE membership change the PR carries (the new
        # candidate writer ka_gochara_v4_41_candidate) — on top of main's
        # protected baseline l3:4f4a1993c6ad:1ddd6f117934 (the D-PINS-A5.4 r7
        # successor, never rewritten). No other layer.
        "authority_commit": "2292ee6b0cebceedc6fdaa80f0fd428e04231c65",
        "evidence_commit": "8f1844cd2255eae2d2bda650c1ef73db9e9a7b33",
        "path": "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/D_PINS_A2_5_PINS_READMISSION_AUTHORITY_v1_0.md",
        "sha256": "e1a2c79c18967b5a21f7b391a76e4db3ffe69e6c8f008e3041c295d57e216a17",
        "decision_binding": "status: PINS_READMISSION_AUTHORIZED",
        "authority_identity_binding": "`2292ee6b0cebceedc6fdaa80f0fd428e04231c65`",
    },
    "D-PINS-A2.5-CONTINUATION": {
        # Continuation of D-PINS-A2.5 (PR #2799, ASTRA v1.0 rework): the
        # rework (PUSH 1-3) moved the admitted L3 writer digests, so the
        # l3:639eece63be3:df2b966b1d97 successor no longer matches source
        # (ASTRA amendment rank 3: regenerate + re-admit). The steward's
        # grant (native's 2026-09-30 standing authority, EVENTS.jsonl
        # 2026-10-01T12:14:51Z, message M20261001T121451-1a8d) is recorded
        # verbatim in the evidence document. Scope: exactly ONE append-only
        # L3 successor over l3:639eece63be3:df2b966b1d97 (archived whole,
        # never rewritten) with exactly the four-writer delta the evidence
        # doc tabulates. No other layer.
        # v1.1 (2026-10-01): the ASTRA v1.1 closure rework moved the same
        # four digests again; the steward's v1.1 verdict (EVENTS.jsonl
        # 2026-10-01T14:04:14Z, message M20261001T140414-f44d — "refresh
        # digests/pins/census (continuation authority stands)") authorizes
        # ONE further successor over l3:f6cb3914e7f1:bf1dba54ee01 with the
        # identical four-writer delta (evidence doc, v1.1 addendum).
        "authority_commit": "53a3d1f85abaa581ff5c1441eb7e29584a82d120",
        "evidence_commit": "954014d8213b63840bc6e4a76cf232bd189a9ee3",
        "path": "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/gochara_wp0_7/D_PINS_A2_5_CONTINUATION_PINS_READMISSION_AUTHORITY_v1_0.md",
        "sha256": "63f243f93a69acfee614fb5cd9b89d2af243dcfef6b70876d351135f697187cc",
        "decision_binding": "status: PINS_READMISSION_AUTHORIZED",
        "authority_identity_binding": "`53a3d1f85abaa581ff5c1441eb7e29584a82d120`",
    },
}

# These source identities were accepted on an earlier lane branch.  They stay
# byte-for-byte in historical admissions, but the executable inventory proof is
# read from an integrated ancestor carrying the exact same inventory blob.
SOURCE_INVENTORY_BINDINGS = {
    "d2369b888e760e5b8d693328f00683877cbd5f28": {
        "integrated_equivalent_commit": "7b1576d59f8300a608fce3acc1d1ec26e8bb3bda",
        "blob_oid": "56766cefc8b30423a59c815ae8eaa85fcf6ec05d",
        "sha256": "baa1d59e56c87601cc8b2f9ab4aa7d8c46c76679f458cb386fddabd713084aa1",
    }
}

EXPECTED_REVIEW_ARTIFACTS = {
    "L5": [{
        "commit": "a97fc8ffb0268954fb4bf8c7fb7e838c4bf6e558",
        "path": "00_ARCHITECTURE/SESSION_LOG.md",
        "sha256": "78273beef6032e0216916167f52b943e49605d6e11a7248f626d2b3205bf779f",
        "decision_binding": "**Reviewed technical head:** `ed5ad601c5e568f5d6c5d8ec72bc7c8f9ff2bd2b`.",
    }],
    "L0": [{
        "commit": "f6fed12c794224329f6b3b436f8b1b814499d06d",
        "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_PRODUCER_READY_ACCEPTANCE_v1_0.md",
        "sha256": "abeb3ffa67d646bdbf4777145ba43e97318e04da9226c78a3fb2e0876b7e76f4",
        "decision_binding": "status: PRODUCER_READY_ACCEPTED",
    }],
    "L1": [{
        "commit": "18503e9c2dbb140f5d17b4bc34a5f6d087f97c38",
        "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_PRODUCER_READY_ACCEPTANCE_v1_0.md",
        "sha256": "265ed113e94915ee3dcaa55c842bf3fd61f6a71320ffe33f3dbd22e87a82c267",
        "decision_binding": "status: PRODUCER_READY_ACCEPTED",
    }],
    "L2": [{
        "commit": "5142109f7f219ea860f859e322646f79d875bee8",
        "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_PRODUCER_READY_ACCEPTANCE_v1_0.md",
        "sha256": "adc2b3c9eceee0e51018c068f5a9e1a6554fa3d1421d5c4e16c5d1b744768b9e",
        "decision_binding": "status: PRODUCER_READY_ACCEPTED",
    }, {
        "commit": "5142109f7f219ea860f859e322646f79d875bee8",
        "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_W2_FIRST_FRONTIER_SOURCE_v1_0.md",
        "sha256": "27ba58e10997ae9c35053d75d11d044c66220053c7a0dc4bdc8727bc09bcf781",
        "decision_binding": "status: SOURCE_PACKET_ACCEPTED_PROVENANCE_LOCAL",
    }],
    "L3": [{
        "commit": "5142109f7f219ea860f859e322646f79d875bee8",
        "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_W2_FIRST_FRONTIER_SOURCE_v1_0.md",
        "sha256": "27ba58e10997ae9c35053d75d11d044c66220053c7a0dc4bdc8727bc09bcf781",
        "decision_binding": "status: SOURCE_PACKET_ACCEPTED_PROVENANCE_LOCAL",
    }],
    "L4": [{
        "commit": "f6fed12c794224329f6b3b436f8b1b814499d06d",
        "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_SWISS_STATE_BOUNDARY_VALIDATION_v1_0.md",
        "sha256": "0f87dc072590179cc9a5e8b928bf30a0436de5d13b3d1e9ed4c20ce31aceee79",
        "decision_binding": "status: VALIDATED_INDEPENDENT_CHALLENGE_PASS",
    }],
}

AUTHORIZED_SOURCE_COMMITS = {
    "CCD-018": {
        "L5": frozenset({"ed5ad601c5e568f5d6c5d8ec72bc7c8f9ff2bd2b"}),
    },
    "DP-SD-018": {
        "L0": frozenset({"d2369b888e760e5b8d693328f00683877cbd5f28"}),
        "L1": frozenset({
            "d2369b888e760e5b8d693328f00683877cbd5f28",
            "149f8479ac4e22874aabe9a5e5b340fb86bc16fb",
        }),
        "L2": frozenset({
            "d2369b888e760e5b8d693328f00683877cbd5f28",
            "149f8479ac4e22874aabe9a5e5b340fb86bc16fb",
        }),
        "L3": frozenset({"d2369b888e760e5b8d693328f00683877cbd5f28"}),
        "L4": frozenset({"d2369b888e760e5b8d693328f00683877cbd5f28"}),
    },
    "DP-SD-019": {
        "L3": frozenset({
            "64facb9763d13eece7098b5b24cc03dfb8e3ba81",
            "87cc8c9baf894c615e167672c6c7af57a15cf71c",
        }),
    },
    # L0 repair (PR #2727): exactly one source commit, for exactly the three layers
    # whose writer digests moved. L1, L4 and L5 are deliberately absent.
    #
    # The source commit (7d40f8c70...) is NOT the approved-state identity in
    # AUTHORITY_BINDINGS (101171f76...), and that is deliberate and disclosed:
    # the inventory committed at 101171f76 was stale (a comment-only edit after its
    # regeneration moved 25 writer digests), so no commit at or before it can be a
    # source whose inventory is true. 7d40f8c70 regenerates it and changes nothing
    # else under platform/python-sidecar - `git diff 101171f76 7d40f8c70 --
    # platform/python-sidecar` is empty - so the writer SOURCES are exactly the ones
    # approved. See L0_REPAIR_ANALYSIS_REPIN_DECISION_ADDENDUM_v1_0.md.
    "NATIVE-2026-09-24-L0-REPAIR-REPIN": {
        "L0": frozenset({"7d40f8c706406ee8187eadb5c3930553800a1a4a"}),
        "L2": frozenset({"7d40f8c706406ee8187eadb5c3930553800a1a4a"}),
        "L3": frozenset({"7d40f8c706406ee8187eadb5c3930553800a1a4a"}),
    },
    # D-E022 (Pravaha A0.3/A0.6): exactly one source commit, for exactly the two
    # layers whose writer digests moved at the PR #2731 merge.
    #
    # A0.6 delivery re-base: the merge queue delivers this PR as a one-parent
    # squash onto main, so lane-only commits are never ancestors of the delivery
    # HEAD and a lane-admitted-then-archived generation (the first A0.3 L3
    # successor) can never name a deliverable historical snapshot. The two
    # lane-local admissions per the A0.3 shape were therefore rewound to the
    # protected baseline (byte-for-byte) and re-admitted ONCE per layer directly
    # on top of the origin/main merge, each archived predecessor naming the
    # protected baseline as its historical snapshot. The lane-local source
    # commits f4cba9d606ab (L1, L3) and ad22bef06784 (L3) authorized for the A0.3
    # shape are WITHDRAWN here before first delivery: they never reached main and
    # their committed inventories predate the origin/main merge, so no admission
    # can cite them against the merged tree.
    #
    # The source commit below IS the origin/main merge commit on the #2731 lane:
    # its committed writer inventory is byte-identical to the merged tree's
    # derived inventory (provenance_inventory --check green). L0, L2, L4, L5 are
    # deliberately absent.
    "D-E022": {
        "L1": frozenset({"333eb7abcac33deefa4f89dc417e73d4f28d74bd"}),
        "L3": frozenset({"333eb7abcac33deefa4f89dc417e73d4f28d74bd"}),
    },
    # D-PINS-A2 (Pravaha A2.3): exactly one source commit, for exactly the one
    # layer (L3) whose writer digests moved on pravaha/a2-kernel-geometry after
    # the origin/main merge (469009b6a8, merge commit eccd32d14). The source
    # commit is the branch's writer-digest regeneration commit: its committed
    # writer inventory is byte-identical to the merged tree's derived inventory
    # (provenance_inventory --check green). L0, L1, L2, L4, L5 verify clean in
    # delivery topology on this branch and are deliberately absent.
    "D-PINS-A2": {
        "L3": frozenset({
            "f4c69a6d0cd40c05ea6dc64eba789b7c4efdea24",
            # D-PINS-A2 continuation (2026-09-30, steward M20260930T220447-289d):
            # #2793 (A5.5 kernel F10-F12, the A2.1 changeset's own continuation)
            # moved ka_sangam, ka_moorti_nirnaya and
            # ka_gochara_v3_century_materialize through their gochara_kernel
            # import closures; no own-module edits. Same decision, same
            # authority identity; ONE successor over the D-PINS-A2 baseline,
            # never a rewrite. Source = the #2793 merge commit (its committed
            # writer inventory is byte-identical to this tree).
            "61e1aa60b5084a144101f4f1a233a6da0edee81c",
        }),
    },
    # D-PINS-A5.4 (Pravaha A5.4, PR #2769): exactly one source commit, for
    # exactly the one layer (L3) whose writer digests moved on
    # pravaha/a5-tier0s-repairs after the origin/main merge (16e3725cee36).
    # The source commit is the branch's writer-digest regeneration commit: its
    # committed writer inventory is byte-identical to the branch tree's
    # derived inventory (provenance_inventory --check green). L0, L1, L2, L4,
    # L5 verify clean in delivery topology on this branch and are deliberately
    # absent.
    "D-PINS-A5.4": {
        "L3": frozenset({
            "454dab04134d81ae420676210c9700e2d4496c6b",
            # A5.4 rework (ASTRA_REVIEW_A5_4 closure, 2026-09-30): the
            # reviewer's eight P1 amendments moved three of the same five
            # writers' import closures again (ka_gochara,
            # ka_gochara_v3_century_materialize, ka_vedha_gochara — all via
            # gochara_grammar/primitives.py and gochara_v3/*; no own-module
            # edit). Same decision, same authority identity, same five-writer
            # scope; a SECOND append-only successor over the branch's own
            # A5.4 successor, never a rewrite of it or of the baseline. Source
            # = the rework's writer-digest regeneration commit.
            "92c07a9051abad73815933e3a5b98ffde37fa848",
            # A5.4 rework r2 (ASTRA_REVIEW_A5_4 v1.1 closure, 2026-09-30): the
            # seven round-2 P1 amendments moved the same three writers'
            # import closures again (gochara_grammar/{dasha_data,primitives}.py,
            # gochara_v3/{context,engine}.py, the new ka_vedha_gochara/gate.py);
            # no own-module writer edit. Same decision, same authority, same
            # five-writer scope; ONE successor over the then-current protected
            # baseline. Source = the r2 writer-digest regeneration commit.
            "aa6a67fb715248fa2b2eccffaf5327692319194a",
            # A5.4 rework r3 (ASTRA_REVIEW_A5_4 v1.2 closure, 2026-09-30): the
            # round-3 P1-2 amendment (vedha state and identity through the
            # persisted output) moved the same three writers' import closures
            # again (ka_vedha_gochara/gate.py, gochara_v3/engine.py, the
            # materializer's _build_suppression_state); no writer outside the
            # five. Same decision, same authority, same five-writer scope; ONE
            # successor over the then-current protected baseline (d4feada9b).
            # Source = the r3 writer-digest regeneration commit.
            "de07494333a770192dd8d8a47cc2aae91f31be79",
            # A5.4 rework r5 (ASTRA_REVIEW_A5_4 v1.3 closure, 2026-10-01): the
            # round-4 amendment 2 (truthful primary-contact identity; testimony
            # evidence through serialisation — ka_vedha_gochara/gate.py) moved
            # ka_gochara_v3_century_materialize's import closure; no writer
            # outside the five. Same decision, same authority, same five-writer
            # scope; ONE successor over the then-current protected baseline.
            # Source = the r5 writer-digest regeneration commit.
            "a7fa8c25e1db78f01c2d33036b1a020501555704",
            # A5.4 rework r7 (D-PINS-A5.4, 2026-10-01): origin/main advanced
            # under the r6 successor — #2793 (61e1aa60b, gochara_kernel
            # F10-F12 geometry) moved ka_moorti_nirnaya and
            # ka_gochara_v3_century_materialize through their gochara_kernel
            # import closures and ka_sangam on main itself (admitted on main
            # by #2800, the D-PINS-A2 continuation), and #2765 (A5.1
            # migrations) and #2801 followed; main's own movement, admitted
            # into the branch by the origin/main merge. The A5.4 delta is
            # unchanged (same decision, same authority, same five-writer
            # scope); ONE successor over main's new protected baseline
            # (l3:61e1aa60b508:9844e89ddd17, the #2800 successor). Source =
            # the origin/main merge commit carrying the regenerated writer
            # inventory (provenance_inventory --check green on the merged
            # tree).
            "4f4a1993c6ada24bf8576206b39742497e3099e3",
        }),
    },
    # D-PINS-A2.5 (Pravāha A2.5, PR #2799): exactly one source commit, for
    # exactly the one layer (L3) whose writer inventory changes on
    # pravaha/a25-v41-candidate-writer — the ONE membership change the PR
    # carries (the new candidate writer ka_gochara_v4_41_candidate; every
    # other writer's digest is unchanged, verified from content-hashed
    # closures of HEAD vs origin/main). The source commit is the origin/main
    # merge commit: its committed writer inventory is byte-identical to the
    # merged tree's derived inventory (provenance_inventory --check green).
    # L0, L1, L2, L4, L5 verify clean in delivery topology on this branch and
    # are deliberately absent.
    "D-PINS-A2.5": {
        "L3": frozenset({
            "639eece63be38a27fb9840ee778beb4c6c1459fd",
        }),
    },
    # D-PINS-A2.5-CONTINUATION (Pravāha A2.5, PR #2799, ASTRA v1.0 rework):
    # exactly one source commit — the PUSH 3 head f6cb3914e, whose committed
    # writer inventory is byte-identical to the reworked tree's derived
    # inventory (provenance_inventory --check green). The delta against the
    # l3:639eece63be3:df2b966b1d97 predecessor inventory (at 348c8e7fc) is
    # exactly four writers: ka_gochara_v4_41_candidate
    # (approved_intentional_change, declared source closure), and
    # ka_gochara_v3_century_materialize / ka_moorti_nirnaya / ka_sangam
    # (derived_import_change via services/gochara_kernel/episodes.py only).
    # L0, L1, L2, L4, L5 are deliberately absent.
    "D-PINS-A2.5-CONTINUATION": {
        "L3": frozenset({
            "f6cb3914e7f1fd5c6170f874dd0cf094eaa35c98",
            # v1.1 (ASTRA v1.1 closure rework; steward M20261001T140414-f44d,
            # continuation authority stands): the v1.1 rework's digest
            # re-derivation head, whose committed writer inventory is
            # byte-identical to the derived inventory. Same four-writer
            # delta over l3:f6cb3914e7f1:bf1dba54ee01.
            "89f788c67827db3a5dc762f47ae4624f0efdb8f6",
        }),
    },
}

# A later compatibility/security source admission must not overwrite the
# original per-layer acceptance bindings above.  It gets its own immutable,
# source-specific binding: exact reviewed branch tree, exact integration tree,
# independently recorded verdict blob and a reproducible proof that every path
# in the reviewed Lane-S surface has the same Git object in the integration.
SOURCE_ACCEPTANCE_BINDINGS = {
    "149f8479ac4e22874aabe9a5e5b340fb86bc16fb": {
        "schema_version": SOURCE_ACCEPTANCE_SCHEMA_VERSION,
        "reviewed_source_commit": "da498ebd980cac87796eceb889c7f1c42cfb952b",
        "integrated_equivalent_commit": "d22533825613c3d428bd844a5dfdc2c0c283b088",
        "common_base_commit": "5142109f7f219ea860f859e322646f79d875bee8",
        "source_surface_sha256": "59a1845b74fb0777274f18b876de0ddae3ac873cea95e405f959d1163ad4d876",
        "reviewed_surface": [
            {"path": ".github/workflows/deploy.yml", "blob_oid": "e6a42c8035c47920d745c35da2e10f3036bd6324"},
            {"path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_RI02_SECURITY_CUTOVER_v1_0.md", "blob_oid": "b97ba202377a68de1d6c181b50ab30207be6b189"},
            {"path": "platform/package-lock.json", "blob_oid": "26f2f718d8066fe8df50591b1ff50a774ab44b89"},
            {"path": "platform/package.json", "blob_oid": "1c05bf84e8077433194424f8c1860e1cda776517"},
            {"path": "platform/pnpm-lock.yaml", "blob_oid": "abba1b47b3981ef7e998b7cb322116aa72247f28"},
            {"path": "platform/python-sidecar/bodha_writers/_idempotency.py", "blob_oid": "46d5e70c0af44989afe22db8b94aa78dd807a00b"},
            {"path": "platform/python-sidecar/ga_writers/_idempotency.py", "blob_oid": "6ea79a86d6654dfab8805ac63ff102fb5a8891d4"},
            {"path": "platform/python-sidecar/ga_writers/ga_condition_writer.py", "blob_oid": "e787b242a1d7c673d9ca62baa908315be3e83855"},
            {"path": "platform/python-sidecar/ga_writers/ga_dashas_writer.py", "blob_oid": "7bc444068023de3502f9056c6799a08b54e09a4a"},
            {"path": "platform/python-sidecar/pipeline/dispatcher.py", "blob_oid": "e72aea9012013f7c0bdfc3a3b2d2c2c072aa9dff"},
            {"path": "platform/python-sidecar/tests/test_bodha_idempotency.py", "blob_oid": "56242b0b4043a5254f1a4e85bc52720a0c2f697b"},
            {"path": "platform/python-sidecar/tests/test_ga_idempotency.py", "blob_oid": "3b6ed86f0572e1c69e6d913552d98e157ab857fd"},
            {"path": "platform/scripts/data-plane-cutover-preflight.ts", "blob_oid": "0e171ae470b931e7328f1437e51f0ab579b74051"},
            {"path": "platform/scripts/data-plane-migration-attestation.ts", "blob_oid": "5972102d5894476bd8ed0cfec7bb76c24d5c4a16"},
            {"path": "platform/scripts/data-plane-ownership-preflight.ts", "blob_oid": "85a760356640d943264f3c67c7b6c759c56eefac"},
            {"path": "platform/scripts/data-plane-ownership-status.ts", "blob_oid": "8e9b980ce6e2bef5d7b122c34f185e83bba99328"},
            {"path": "platform/scripts/data-plane-protected-cutover.ts", "blob_oid": "57fb5a613646f25d0f3cbe465f57bd54e05cf2b0"},
            {"path": "platform/scripts/data-plane-secret-isolation-preflight.ts", "blob_oid": "112a3592848d51c462b14269061948fd7f548c15"},
            {"path": "platform/scripts/migrate.ts", "blob_oid": "1807347da2dbf470b589b3aad6e835768b5504e2"},
            {"path": "platform/supabase/migrations/1035_data_plane_l1_producer_history.sql", "blob_oid": "aa878d964dbdbc5d35d352eec7cbacb62c1bdb0d"},
            {"path": "platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql", "blob_oid": "d00b7cda7f00b1243c8a9e8dfcf5a2903f502e69"},
            {"path": "platform/tests/integration/data_plane_protected_roles.db.test.ts", "blob_oid": "43dfa413d26f39a42c3a7ac2d2336b462884ae94"},
            {"path": "platform/tests/unit/data_plane_security_contract.test.ts", "blob_oid": "d0c8059efe1487b1f5bc389ed6f094be26586e8f"},
        ],
        "review_artifacts": {
            layer: [{
                "commit": "149f8479ac4e22874aabe9a5e5b340fb86bc16fb",
                "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_RI02_SECURITY_SOURCE_ACCEPTANCE_v1_0.md",
                "sha256": "94cbe76aff7d1a15d5efd1d3f355a6f49a6af49fafc14edf7b708bb8f454c084",
                "decision_binding": "status: SECURITY_CLEAR_SOURCE_ACCEPTED",
            }]
            for layer in ("L1", "L2")
        },
    },
    "64facb9763d13eece7098b5b24cc03dfb8e3ba81": {
        "schema_version": SOURCE_ACCEPTANCE_SCHEMA_VERSION,
        "reviewed_source_commit": "7697c43b31da3655c2add7cda128a57ca4afd44e",
        "integrated_equivalent_commit": "64facb9763d13eece7098b5b24cc03dfb8e3ba81",
        "common_base_commit": "d07ea4f3f3b6b0bcb5d66cbd7c1d5f67784d658f",
        "source_surface_sha256": "c7335980706c9815362f3fc39dca349b42aa94e7f0bddcc6b0e85c56d19d366a",
        "reviewed_surface": [
            {
                "path": "platform/python-sidecar/pipeline/orchestrator/writers/ka_yojaka.py",
                "blob_oid": "8939b234c20794eb59edc559bb6f8e3a44865cc5",
            },
            {
                "path": "platform/python-sidecar/tests/l3/test_ka_yojaka_multidomain.py",
                "blob_oid": "52e7ba3d5ba97024f1327ca2f97d25e98e01e589",
            },
        ],
        "review_artifacts": {
            "L3": [{
                "commit": "64facb9763d13eece7098b5b24cc03dfb8e3ba81",
                "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_DP019_SOURCE_ACCEPTANCE_v1_0.md",
                "sha256": "a24f4ad257d755359dd82d3ad52af928f74d625aaf183f2638c5ec08f07858c5",
                "decision_binding": "status: SOURCE_PACKET_ACCEPTED",
            }],
        },
    },
    "87cc8c9baf894c615e167672c6c7af57a15cf71c": {
        "schema_version": SOURCE_ACCEPTANCE_SCHEMA_VERSION,
        "reviewed_source_commit": "87cc8c9baf894c615e167672c6c7af57a15cf71c",
        "integrated_equivalent_commit": "87cc8c9baf894c615e167672c6c7af57a15cf71c",
        "common_base_commit": "6c1a65e23be6176322d7a9ab78e0c291feeec700",
        "source_surface_sha256": "8eb4cce85bdc32434cad92d649837a1fcb80e63e941efedc9838c6e5e8c62cbe",
        "reviewed_surface": [
            {
                "path": "platform/python-sidecar/services/ka_kshetra/dhara_null.py",
                "blob_oid": "786fa0644d733005a6c9cbfd016915232822563b",
            },
            {
                "path": "platform/python-sidecar/services/ka_kshetra/dhara_null_vec.py",
                "blob_oid": "ebaa7014a49f035770495b72eb1a6701c4f25520",
            },
            {
                "path": "platform/python-sidecar/services/ka_kshetra/layer1.py",
                "blob_oid": "b4affc3ea1bb74c44fbb0edbbc31ef483e12a95a",
            },
            {
                "path": "platform/python-sidecar/services/ka_kshetra/tests/test_dhara_null.py",
                "blob_oid": "ea1dd0d6b230f18954b10a824fbc18846fcec712",
            },
            {
                "path": "platform/python-sidecar/services/ka_kshetra/tests/test_dhara_null_vectorized.py",
                "blob_oid": "ce70ca1253c3ef2addb146db5b968be07c3a7616",
            },
            {
                "path": "platform/python-sidecar/services/ka_kshetra/tests/test_stage1_symbolization.py",
                "blob_oid": "1b0277fe9ddb4259a575df80c9dcabfd1e5bc6cf",
            },
        ],
        "review_artifacts": {
            "L3": [{
                "commit": "58b7d455d803c54238bdae050c1770f9f514d21e",
                "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_DP019_KSHETRA_GATE_ACCEPTANCE_v1_0.md",
                "sha256": "687eed0309e906730364a394fb674ebac17ce58220309308bfcf071ac972175d",
                "decision_binding": "status: SOURCE_PACKET_ACCEPTED",
            }],
        },
    },
}

# Post-integration acceptance records cover privileged route corrections that
# intentionally do not move a writer generation. Keeping them distinct from
# per-layer successor admissions prevents a no-writer-delta repair from
# rewriting L1/L2 receipt history merely to preserve review provenance.
POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS = {
    "ea9b27bfeba607c5332c51e10b037e100e97b717": {
        "schema_version": SOURCE_ACCEPTANCE_SCHEMA_VERSION,
        "reviewed_source_commit": "ea9b27bfeba607c5332c51e10b037e100e97b717",
        "integrated_equivalent_commit": "ea9b27bfeba607c5332c51e10b037e100e97b717",
        "common_base_commit": "7982524fde1b210dea72eb38e1704aa2b0514eb2",
        "source_surface_sha256": "89fdc9c7ef43031faffcf7e9d633114bed4892e7b401703d7d9bb951bcb2dde1",
        "reviewed_surface": [
            {"path": "platform/scripts/data-plane-migration-attestation.ts", "blob_oid": "ae225a2d5c3ac1eb03938c8338191e21a8a56fd7"},
            {"path": "platform/scripts/data-plane-ownership-preflight.ts", "blob_oid": "3fc5f7d7f296fd6c79c0e8650154fa51df66b342"},
            {"path": "platform/scripts/data-plane-protected-cutover.ts", "blob_oid": "bad228594eb620d68e6ddbd79267af94499315f0"},
            {"path": "platform/tests/unit/data_plane_security_contract.test.ts", "blob_oid": "f3ea6d49d191dad280390edd6aed76391a37a64f"},
        ],
        "record_artifact": {
            "commit": "3fcf972e1f2e3b3d9994b361902048276c1aff3b",
            "path": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_RI02_SECURITY_SOURCE_ACCEPTANCE_v1_1.md",
            "sha256": "fc2ac7c157d4222337ccaff5b4ea5425c1d297bbd96d8220ca83a4251c27d3fb",
            "decision_binding": "status: SECURITY_CLEAR_SOURCE_ACCEPTED",
        },
    },
}

# L0's reviewed convergence, carried forward verbatim from the pre-generalisation
# nirmana-l0-analysis-receipts.ts.  Changing either value re-computes every L0
# analysis digest and invalidates the frozen L0 capsules — see --check.
#
# `writer_inventory_sha256` re-pinned 2026-09-06 (D-NATIVE-06, native-ratified
# transparent re-derivation): the previous value (8650e7a7...) was superseded
# because bg_yogas's writer was fixed (a dict-row-as-tuple bug in
# extract_yogas_from_corpus silently yielded 0 corpus-extracted yogas on every
# real dispatch). This aggregate is NOT part of any per-asset
# NirmanaAnalysisReceiptBase (see nirmana-analysis-receipts.ts's
# buildLayerReceipts — only writer_digest_sha256, layer, convergence_commit,
# and the two static grounding constants feed the hashed base); it only gates
# whether NEW analysis-acceptance calls resolve for the layer at all. Verified
# before re-pinning: regenerating platform/src/generated/nirmana-writer-digests.json
# changed exactly one entry (bg_yogas); the other 35 frozen L0 writers' digests
# are byte-identical to before, so no other asset's already-accepted
# analysis_digest is affected by this re-pin.
#
# Re-pinned again 2026-09-07 (issue #2122, F-D21/F-D23): bg_vidhi_primitives.py's
# from_moon_view entry was corrected (re-pointed from the inert reference_point
# arg on ganita_chart_facts_get to the real ganita_transit_anchors_get consumer).
# Same verification discipline: regenerating the writer inventory changed
# exactly one entry (bg_vidhi_primitives); the other 35 frozen L0 writers'
# digests (bg_yogas included) are byte-identical to the prior re-pin.
L0_FROZEN_PINS = {
    "convergence_commit": "49bb5c98b864a2cb2fee037cdb7f14f6892a8263",
    "writer_inventory_sha256": "5125cccb68715ebc6054c3ce47bc4c047684445249503a4c4dabd85e0d036178",
    "receipt_count": 40,
}


def layer_inventory_sha256(writer_digests: dict[str, str], prefix: str) -> str:
    """Aggregate over one layer's slice, matching the TS assert byte for byte.

    Mirrors assertNirmanaL0WriterInventoryMatchesConvergence: filter by prefix,
    sort by key, JSON.stringify (no spaces, no ASCII escaping), sha256.
    """
    layer_inventory = {
        asset_id: digest
        for asset_id, digest in sorted(writer_digests.items())
        if asset_id.startswith(prefix)
    }
    if not layer_inventory:
        raise SystemExit(f"writer inventory has no entries for prefix {prefix!r}")
    encoded = json.dumps(
        layer_inventory, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_frozen_manifest_assets() -> list[dict[str, Any]]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit(
            "DATABASE_URL is required to regenerate pins (the frozen manifest is the "
            "authority for receipt_count and non_writer_assets). Use --check offline."
        )
    import psycopg2  # imported lazily so --check needs no driver

    connection = psycopg2.connect(database_url)
    connection.set_session(readonly=True)
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT manifest FROM nirmana_evidence.nirmana_elevation_campaign_definitions "
            "WHERE definition_status='frozen' AND superseded_at IS NULL"
        )
        rows = cursor.fetchall()
    finally:
        connection.close()
    if len(rows) != 1:
        raise SystemExit(f"expected exactly one frozen campaign definition; found {len(rows)}")
    return list(rows[0][0]["assets"])


def build_pins(
    writer_digests: dict[str, str],
    manifest_assets: list[dict[str, Any]],
    convergence_commit: str,
    definition_snapshot_commit: str,
    *,
    layers: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Derive each requested layer's pin, validated against its OWN authority only.

    `layers` scopes both which layers get a freshly-derived pin AND which
    layers' frozen/definition-binding invariants are checked. Omitting it (the
    whole-file regeneration path) preserves the original behaviour: every
    layer, including L0, is derived and validated.

    This scoping is the fix for the cross-layer coupling NIRMANA issue #1930
    found: a caller asking only for L5's pin (`--layer L5`) was forced through
    L0's frozen-pin comparison too, because the loop below used to run over
    every layer unconditionally regardless of which one the caller actually
    wanted. A legitimate, reviewed L5-only successor must never require,
    rewrite, or re-accept L0 — see NIRMANA_L0_L5_RECEIPT_COUPLING_FIX_ADDENDUM_v1_0.md.
    Requesting L0 itself (whole-file regeneration, or an explicit `layers={"L0"}`)
    still runs L0's frozen-pin check and still fails closed on genuine L0 drift.
    """
    requested = list(LAYER_PREFIX) if layers is None else list(layers)
    unknown = [layer for layer in requested if layer not in LAYER_PREFIX]
    if unknown:
        raise SystemExit(f"unknown layer(s) requested: {unknown}")
    layer_pins: dict[str, Any] = {}
    for layer in requested:
        prefix = LAYER_PREFIX[layer]
        manifest_ids = sorted(
            asset["asset_id"] for asset in manifest_assets if asset["layer"] == layer
        )
        if not manifest_ids:
            raise SystemExit(f"frozen manifest carries no assets for {layer}")
        non_writer = [a for a in manifest_ids if a not in writer_digests]
        pin = {
            "asset_prefix": prefix,
            "convergence_commit": convergence_commit,
            "writer_inventory_sha256": layer_inventory_sha256(writer_digests, prefix),
            "receipt_count": len(manifest_ids),
            "non_writer_assets": non_writer,
        }
        if layer == "L0":
            # convergence_commit is a RECORDED INPUT, not a derived value: it
            # names the commit whose inventory was reviewed, which no later
            # regeneration can rediscover.  Carry L0's forward verbatim.
            pin["convergence_commit"] = L0_FROZEN_PINS["convergence_commit"]
            # The other two ARE derived, so they must still agree with the frozen
            # record.  Drift here means the L0 writer inventory or manifest cohort
            # has moved under 29 already-frozen capsules — a real finding.  Stop
            # rather than silently re-pin it.  This branch is unreachable unless
            # L0 was actually requested (see `requested` above) — an L5-only
            # caller never reaches it and never compares against L0_FROZEN_PINS.
            for key in ("writer_inventory_sha256", "receipt_count"):
                if pin[key] != L0_FROZEN_PINS[key]:
                    raise SystemExit(
                        f"L0 {key} derives to {pin[key]!r} but is frozen at "
                        f"{L0_FROZEN_PINS[key]!r}; re-pinning L0 would invalidate "
                        "its accepted analyses. Investigate before regenerating."
                    )
        layer_pins[layer] = pin
    definition_bindings = build_definition_bindings(definition_snapshot_commit, layers=requested)
    for layer, pin in layer_pins.items():
        membership = receipt_membership(layer, pin, writer_digests)
        if membership_sha256(membership) != definition_bindings[layer]["membership_sha256"]:
            raise SystemExit(
                f"{layer} database manifest differs from immutable definition snapshot"
            )
    return {
        "version": PINS_VERSION,
        "layers": layer_pins,
        "history": {layer: [] for layer in requested},
        "definition_bindings": definition_bindings,
    }


def splice_layer_pin(
    committed: dict[str, Any],
    layer: str,
    fresh: dict[str, Any],
    *,
    accepted_definition_binding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge one freshly-derived layer's pin into an already-committed record.

    `fresh` is `build_pins()`'s output scoped to exactly `layer` (via its
    `layers=[layer]` argument) -- never the whole-file result, so no other
    layer's derivation or L0 validation ever ran to produce it. Every other
    layer's committed data, and the WHOLE `history` block for every layer
    including `layer` itself, is carried through byte-for-byte: a per-layer
    splice regenerates a layer's live PIN, never its successor history (that
    is `admit_successor()`'s job, gated on its own authority-binding registry).
    """
    updated = copy.deepcopy(committed)
    updated["layers"][layer] = fresh["layers"][layer]
    definitions = updated.setdefault("definition_bindings", {})
    fresh_definition = fresh["definition_bindings"][layer]
    accepted_definition = (
        accepted_definition_binding
        if accepted_definition_binding is not None
        else definitions.get(layer)
    )
    if accepted_definition is None:
        definitions[layer] = fresh_definition
    elif (
        accepted_definition.get("schema_version")
        != fresh_definition.get("schema_version")
        or accepted_definition.get("membership_sha256")
        != fresh_definition.get("membership_sha256")
    ):
        raise SystemExit(
            f"{layer} scoped re-pin membership differs from its accepted definition binding"
        )
    else:
        definitions[layer] = copy.deepcopy(accepted_definition)
    return updated


def render(pins: dict[str, Any]) -> str:
    return json.dumps(pins, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def layer_writer_slice(writer_digests: dict[str, str], prefix: str) -> dict[str, str]:
    return {
        asset_id: digest
        for asset_id, digest in sorted(writer_digests.items())
        if asset_id.startswith(prefix)
    }


def generation_id(layer: str, pin: dict[str, Any]) -> str:
    return (
        f"{layer.lower()}:{pin['convergence_commit'][:12]}:"
        f"{pin['writer_inventory_sha256'][:12]}"
    )


def _validate_sha(value: str, label: str) -> None:
    if not re.fullmatch(r"[a-f0-9]{40}", value):
        raise SystemExit(f"{label} must be an exact 40-hex commit, got {value!r}")


def _commit_is_ancestor_of_head(commit: str) -> bool:
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        return False
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
    ).returncode == 0


def _commit_is_ancestor_of_commit(ancestor: str, descendant: str) -> bool:
    if not re.fullmatch(r"[a-f0-9]{40}", ancestor) or not re.fullmatch(
        r"[a-f0-9]{40}", descendant
    ):
        return False
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=REPO_ROOT,
        capture_output=True,
    ).returncode == 0


def _require_reachable_commit(commit: str, label: str) -> None:
    _validate_sha(commit, label)
    if not _commit_is_ancestor_of_head(commit):
        raise SystemExit(f"{label} commit {commit} must be an ancestor of HEAD")


def _direct_parent(commit: str, label: str) -> str:
    _require_reachable_commit(commit, label)
    parents = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", commit],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip().split()[1:]
    if len(parents) != 1 or not re.fullmatch(r"[a-f0-9]{40}", parents[0]):
        raise SystemExit(f"{label} commit {commit} must have exactly one direct parent")
    return parents[0]


def _blob_at_commit(commit: str, path: str) -> bytes:
    _require_reachable_commit(commit, "artifact")
    return _blob_at_revision(commit, path, "commit")


def _blob_at_revision(revision: str, path: str, label: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "show", f"{revision}:{path}"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"{label} {revision} does not carry {path}") from exc


def _blob_oid_at_commit(commit: str, path: str) -> str:
    _require_reachable_commit(commit, "blob source")
    try:
        oid = subprocess.run(
            ["git", "rev-parse", f"{commit}:{path}"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"commit {commit} does not carry {path}") from exc
    if not re.fullmatch(r"[a-f0-9]{40}", oid):
        raise SystemExit(f"commit {commit} carries an invalid blob identity at {path}")
    return oid


def _commit_exists(commit: str) -> bool:
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        return False
    return subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
    ).returncode == 0


def _json_at_commit(commit: str, path: str) -> dict[str, Any]:
    try:
        value = json.loads(_blob_at_commit(commit, path))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"commit {commit} carries invalid JSON at {path}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"commit {commit} does not carry an object at {path}")
    return value


def _inventory_at_commit(commit: str) -> dict[str, str]:
    inventory_commit = commit
    binding = SOURCE_INVENTORY_BINDINGS.get(commit)
    if binding is not None:
        inventory_commit = binding["integrated_equivalent_commit"]
        path = "platform/src/generated/nirmana-writer-digests.json"
        if _blob_oid_at_commit(inventory_commit, path) != binding["blob_oid"]:
            raise SystemExit(
                f"integrated inventory for source {commit} has the wrong blob identity"
            )
        if hashlib.sha256(_blob_at_commit(inventory_commit, path)).hexdigest() != binding["sha256"]:
            raise SystemExit(
                f"integrated inventory for source {commit} has the wrong content digest"
            )
    try:
        writers = _json_at_commit(
            inventory_commit, "platform/src/generated/nirmana-writer-digests.json"
        )["writers"]
    except KeyError as exc:
        raise SystemExit(
            f"source commit {commit} does not carry a readable writer inventory"
        ) from exc
    if not isinstance(writers, dict):
        raise SystemExit(f"source commit {commit} carries an invalid writer inventory")
    return writers


def _pins_at_commit(commit: str) -> dict[str, Any]:
    return _json_at_commit(
        commit, "platform/src/generated/nirmana-analysis-layer-pins.json"
    )


def receipt_membership(
    layer: str, pin: dict[str, Any], writer_digests: dict[str, str]
) -> dict[str, Any]:
    prefix = LAYER_PREFIX[layer]
    non_writers = pin.get("non_writer_assets")
    if not isinstance(non_writers, list):
        raise SystemExit(f"{layer} non_writer_assets must be a list")
    if (
        any(not isinstance(asset_id, str) for asset_id in non_writers)
        or non_writers != sorted(set(non_writers))
        or any(
            (
                not asset_id.startswith(prefix)
                and asset_id not in NON_WRITER_PREFIX_EXCEPTIONS.get(layer, frozenset())
            )
            for asset_id in non_writers
        )
        or any(asset_id in writer_digests for asset_id in non_writers)
    ):
        raise SystemExit(
            f"{layer} non_writer_assets must be sorted, unique, layer-scoped and writer-disjoint"
        )
    asset_ids = sorted(
        asset_id
        for asset_id in writer_digests
        if asset_id.startswith(prefix) and asset_id not in SUPPORTING_WRITERS
    ) + non_writers
    asset_ids = sorted(asset_ids)
    if len(asset_ids) != len(set(asset_ids)):
        raise SystemExit(f"{layer} receipt membership contains duplicate identities")
    return {
        "asset_ids": asset_ids,
        "layer": layer,
        "non_writer_assets": non_writers,
    }


def membership_sha256(membership: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            membership, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
    ).hexdigest()


def build_definition_bindings(
    snapshot_commit: str, *, layers: Iterable[str] | None = None
) -> dict[str, Any]:
    _validate_sha(snapshot_commit, "definition snapshot commit")
    snapshot_pins = _pins_at_commit(snapshot_commit).get("layers", {})
    snapshot_inventory = _inventory_at_commit(snapshot_commit)
    bindings: dict[str, Any] = {}
    for layer in (LAYER_PREFIX if layers is None else layers):
        snapshot_pin = snapshot_pins.get(layer)
        if not isinstance(snapshot_pin, dict):
            raise SystemExit(
                f"definition snapshot {snapshot_commit} has no {layer} pin"
            )
        membership = receipt_membership(layer, snapshot_pin, snapshot_inventory)
        bindings[layer] = {
            "schema_version": DEFINITION_SCHEMA_VERSION,
            "snapshot_commit": snapshot_commit,
            "membership_sha256": membership_sha256(membership),
        }
    return bindings


def _artifact_metadata(
    artifact: dict[str, Any], label: str
) -> tuple[str, str, str, str]:
    try:
        commit = artifact["commit"]
        path = artifact["path"]
        digest = artifact["sha256"]
        decision_binding = artifact["decision_binding"]
    except KeyError as exc:
        raise SystemExit(f"{label} is missing {exc.args[0]}") from exc
    _validate_sha(commit, f"{label} commit")
    if not path or not decision_binding or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise SystemExit(f"{label} metadata is invalid")
    return commit, path, digest, decision_binding


def _validate_artifact_content(
    artifact: dict[str, Any], label: str, content: bytes
) -> None:
    commit, path, digest, decision_binding = _artifact_metadata(artifact, label)
    if hashlib.sha256(content).hexdigest() != digest:
        raise SystemExit(f"{label} content digest does not match {commit}:{path}")
    if decision_binding.encode("utf-8") not in content:
        raise SystemExit(f"{label} does not contain its expected decision binding")


def validate_artifact_binding(artifact: dict[str, Any], label: str) -> None:
    commit, path, _, _ = _artifact_metadata(artifact, label)
    content = _blob_at_commit(commit, path)
    _validate_artifact_content(artifact, label, content)


def validate_delivered_artifact_binding(
    artifact: dict[str, Any],
    label: str,
    *,
    required_content_bindings: tuple[str, ...] = (),
) -> None:
    """Validate exact evidence packaged by a squash-style delivery commit.

    GitHub's merge queue carries the source PR tree in a synthetic single-parent
    commit, so source-only commits are not ancestors of delivery HEAD. The
    source-topology check must still dereference those commits. Delivery instead
    re-hashes the exact path packaged at HEAD and binds it to the reviewed source
    identities recorded inside the artifact.
    """
    _, path, _, _ = _artifact_metadata(artifact, label)
    content = _blob_at_revision("HEAD", path, "delivery")
    _validate_artifact_content(artifact, label, content)
    for binding in required_content_bindings:
        if binding.encode("utf-8") not in content:
            raise SystemExit(
                f"{label} delivered content does not contain {binding!r}"
            )


def validate_protected_squash_artifact_binding(
    artifact: dict[str, Any],
    label: str,
    protected_baseline_commit: str,
    *,
    required_content_bindings: tuple[str, ...] = (),
) -> None:
    """Validate evidence already squash-delivered on the protected baseline.

    Source PRs still require reachable source artifacts unless the trusted base
    already carries the exact record. In that case, find the first-parent commit
    that introduced those bytes, require GitHub's one-parent delivery shape, and
    revalidate the digest plus every immutable decision/source binding there.
    """
    _require_reachable_commit(protected_baseline_commit, "protected baseline")
    _, path, digest, _ = _artifact_metadata(artifact, label)
    try:
        candidates = subprocess.run(
            [
                "git",
                "rev-list",
                "--first-parent",
                protected_baseline_commit,
                "--",
                path,
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            f"{label} protected baseline history cannot be inspected"
        ) from exc

    for delivery_commit in candidates:
        try:
            parent = _direct_parent(delivery_commit, f"{label} delivery")
            content = _blob_at_revision(delivery_commit, path, "delivery")
        except SystemExit:
            continue
        if hashlib.sha256(content).hexdigest() != digest:
            continue
        try:
            parent_content = _blob_at_revision(parent, path, "delivery parent")
        except SystemExit:
            parent_content = None
        if parent_content == content:
            continue
        _validate_artifact_content(artifact, label, content)
        for binding in required_content_bindings:
            if binding.encode("utf-8") not in content:
                raise SystemExit(
                    f"{label} delivered content does not contain {binding!r}"
                )
        return

    raise SystemExit(
        f"{label} is not an exact protected one-parent delivery at or before "
        f"{protected_baseline_commit}"
    )


def validate_authority_binding(decision: str, commit: str) -> None:
    expected = AUTHORITY_BINDINGS.get(decision)
    if expected is None or expected["authority_commit"] != commit:
        raise SystemExit(f"authority decision {decision!r} is not bound to {commit}")
    artifact = {
        "commit": expected["evidence_commit"],
        "path": expected["path"],
        "sha256": expected["sha256"],
        "decision_binding": expected["decision_binding"],
    }
    validate_artifact_binding(artifact, f"authority {decision}")
    content = _blob_at_commit(expected["evidence_commit"], expected["path"])
    if expected["authority_identity_binding"].encode("utf-8") not in content:
        raise SystemExit(
            f"authority {decision} record does not contain the immutable approval identity"
        )


def _source_acceptance_public(binding: dict[str, Any]) -> dict[str, Any]:
    public = {
        key: binding[key]
        for key in (
            "schema_version",
            "reviewed_source_commit",
            "integrated_equivalent_commit",
            "common_base_commit",
            "source_surface_sha256",
        )
    }
    public["reviewed_surface"] = json.loads(json.dumps(binding["reviewed_surface"]))
    return public


def _source_surface_mapping(
    reviewed_surface: list[dict[str, str]],
    integrated_equivalent_commit: str,
) -> tuple[list[str], str]:
    _require_reachable_commit(integrated_equivalent_commit, "integrated equivalent")
    if not isinstance(reviewed_surface, list) or not reviewed_surface:
        raise SystemExit("reviewed source surface is missing or empty")
    if any(
        not isinstance(item, dict)
        or set(item) != {"path", "blob_oid"}
        or not isinstance(item["path"], str)
        or not item["path"]
        or not isinstance(item["blob_oid"], str)
        or not re.fullmatch(r"[a-f0-9]{40}", item["blob_oid"])
        for item in reviewed_surface
    ):
        raise SystemExit("reviewed source surface contains invalid path/blob metadata")
    paths = [item["path"] for item in reviewed_surface]
    if paths != sorted(set(paths)):
        raise SystemExit("reviewed source surface paths must be sorted and unique")
    material = bytearray()
    for item in reviewed_surface:
        path = item["path"]
        reviewed_oid = item["blob_oid"]
        integrated_oid = _blob_oid_at_commit(integrated_equivalent_commit, path)
        if integrated_oid != reviewed_oid:
            raise SystemExit(
                f"integrated source differs from reviewed source at {path}"
            )
        material.extend(path.encode("utf-8"))
        material.extend(b"\0")
        material.extend(reviewed_oid.encode("ascii"))
        material.extend(b"\n")
    return paths, hashlib.sha256(material).hexdigest()


def validate_source_acceptance(
    source_commit: str, source_acceptance: dict[str, Any] | None
) -> None:
    configured = SOURCE_ACCEPTANCE_BINDINGS.get(source_commit)
    if configured is None:
        if source_acceptance is not None:
            raise SystemExit(
                f"source commit {source_commit} has an unexpected source-acceptance binding"
            )
        return
    expected = _source_acceptance_public(configured)
    if source_acceptance != expected:
        raise SystemExit(
            f"source commit {source_commit} is missing or has the wrong source-acceptance binding"
        )
    _, derived_digest = _source_surface_mapping(
        expected["reviewed_surface"],
        expected["integrated_equivalent_commit"],
    )
    if derived_digest != expected["source_surface_sha256"]:
        raise SystemExit(
            "reviewed/integrated source-surface digest does not match its immutable binding"
        )


def validate_post_integration_source_acceptance_bindings(
    *,
    delivery_topology: bool = False,
    protected_baseline_commit: str | None = None,
) -> None:
    """Re-derive privileged no-writer-delta acceptance records offline."""
    for source_commit, binding in POST_INTEGRATION_SOURCE_ACCEPTANCE_BINDINGS.items():
        expected_keys = {
            "schema_version", "reviewed_source_commit", "integrated_equivalent_commit",
            "common_base_commit", "source_surface_sha256", "reviewed_surface", "record_artifact",
        }
        if set(binding) != expected_keys or binding["schema_version"] != SOURCE_ACCEPTANCE_SCHEMA_VERSION:
            raise SystemExit(f"post-integration source acceptance {source_commit} is malformed")
        if binding["reviewed_source_commit"] != source_commit:
            raise SystemExit(f"post-integration source acceptance {source_commit} has the wrong reviewed tip")
        _require_reachable_commit(source_commit, "post-integration reviewed source")
        common_base = binding["common_base_commit"]
        _require_reachable_commit(common_base, "post-integration common base")
        if _direct_parent(source_commit, "post-integration reviewed source") != common_base:
            raise SystemExit(
                f"post-integration source acceptance {source_commit} common base is not its direct parent"
            )
        _, derived_digest = _source_surface_mapping(
            binding["reviewed_surface"], binding["integrated_equivalent_commit"]
        )
        if derived_digest != binding["source_surface_sha256"]:
            raise SystemExit(
                f"post-integration source acceptance {source_commit} has the wrong source-surface digest"
            )
        artifact = binding["record_artifact"]
        artifact_label = f"post-integration source acceptance {source_commit}"
        required_content_bindings = (
            f"reviewed_branch_tip: {source_commit}",
            "integrated_equivalent_tip: "
            f"{binding['integrated_equivalent_commit']}",
        )
        if delivery_topology:
            validate_delivered_artifact_binding(
                artifact,
                artifact_label,
                required_content_bindings=required_content_bindings,
            )
        elif (
            not _commit_is_ancestor_of_head(artifact["commit"])
            and protected_baseline_commit is not None
        ):
            validate_protected_squash_artifact_binding(
                artifact,
                artifact_label,
                protected_baseline_commit,
                required_content_bindings=required_content_bindings,
            )
        else:
            validate_artifact_binding(artifact, artifact_label)
            if not _commit_is_ancestor_of_commit(
                source_commit, artifact["commit"]
            ):
                raise SystemExit(
                    f"{artifact_label} record does not descend from its reviewed source"
                )


def validate_review_artifacts(
    layer: str,
    artifacts: list[dict[str, str]],
    source_commit: str,
    protected_baseline_commit: str | None = None,
) -> None:
    """Validate the review artifacts a successor cites.

    `protected_baseline_commit` (optional) admits ONE narrow fallback, and only
    for an artifact whose commit is not an ancestor of HEAD: the trusted base
    must already carry those exact bytes as a one-parent squash delivery, which
    `validate_protected_squash_artifact_binding` re-derives (digest plus decision
    binding). Without a baseline, or for an artifact that is neither reachable
    nor squash-delivered on the baseline, behaviour is unchanged and strict.

    Why this exists (L0 repair, 2026-09): the L0-L3 data-plane evidence was
    delivered to main by squash (fa9857f00), which severs the source branch's
    ancestry. A branch cut from that main can never reach 5142109f7f2..., so a
    successor citing the standing acceptance artifacts could be *verified* on
    the protected baseline (check()) but could not be *admitted* here.
    """
    source_binding = SOURCE_ACCEPTANCE_BINDINGS.get(source_commit)
    expected = (
        source_binding.get("review_artifacts", {}).get(layer)
        if source_binding is not None
        else EXPECTED_REVIEW_ARTIFACTS.get(layer)
    )
    if expected is None or artifacts != expected:
        raise SystemExit(
            f"{layer} review artifacts do not match the required acceptance artifacts "
            f"for source {source_commit}"
        )
    for index, artifact in enumerate(artifacts):
        label = f"{layer} review artifact {index}"
        commit, _, _, _ = _artifact_metadata(artifact, label)
        if protected_baseline_commit is not None and not _commit_is_ancestor_of_head(commit):
            validate_protected_squash_artifact_binding(
                artifact, label, protected_baseline_commit
            )
        else:
            validate_artifact_binding(artifact, label)


def validate_authorized_source(decision: str, layer: str, source_commit: str) -> None:
    authorized = AUTHORIZED_SOURCE_COMMITS.get(decision, {}).get(layer, frozenset())
    if source_commit not in authorized:
        raise SystemExit(
            f"{layer} source commit {source_commit} is not authorized by {decision}"
        )


def parse_classifications(values: list[str]) -> dict[str, str]:
    classifications: dict[str, str] = {}
    for value in values:
        asset_id, separator, classification = value.partition("=")
        if not separator or not asset_id:
            raise SystemExit(
                f"classification must be asset_id=category, got {value!r}"
            )
        if classification not in ALLOWED_DELTA_CLASSIFICATIONS:
            raise SystemExit(
                f"unsupported classification {classification!r}; expected one of "
                f"{sorted(ALLOWED_DELTA_CLASSIFICATIONS)}"
            )
        if asset_id in classifications:
            raise SystemExit(f"duplicate classification for {asset_id}")
        classifications[asset_id] = classification
    return classifications


def parse_review_artifacts(values: list[str]) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    for value in values:
        try:
            artifact = json.loads(value)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"review artifact must be a JSON object: {exc}") from exc
        if not isinstance(artifact, dict) or any(
            not isinstance(key, str) or not isinstance(item, str)
            for key, item in artifact.items()
        ):
            raise SystemExit("review artifact must be a string-to-string JSON object")
        artifacts.append(artifact)
    return artifacts


def _resolve_definition_bindings(
    existing: dict[str, Any] | None,
    definition_snapshot_commit: str,
    protected_baseline_commit: str | None,
) -> dict[str, Any]:
    """Return the definition bindings a successor admission must carry.

    Normal path: re-derive them from the (reachable) definition snapshot commit.

    Squash-delivery path: when `protected_baseline_commit` is given AND the
    bindings already committed are byte-identical to the ones the protected
    baseline carries AND every layer names `definition_snapshot_commit`, the
    snapshot commit cannot be re-dereferenced from this branch (squash delivery
    severed its ancestry) but is already accepted history on the trusted base.
    Carry those bindings verbatim. This mirrors check(), which already compares
    a candidate's definition to the baseline's rather than re-dereferencing.

    It weakens nothing that carries the evidence: the caller still verifies the
    candidate membership against each layer's carried `membership_sha256`
    (admit_successor, "candidate membership does not match the immutable
    definition snapshot"), so a wrong membership is still refused.
    """
    if existing is not None and protected_baseline_commit is not None:
        _require_reachable_commit(protected_baseline_commit, "protected baseline")
        baseline_definitions = _pins_at_commit(protected_baseline_commit).get(
            "definition_bindings"
        )
        if (
            existing == baseline_definitions
            and isinstance(existing, dict)
            and set(existing) == set(LAYER_PREFIX)
            and all(
                isinstance(binding, dict)
                and binding.get("snapshot_commit") == definition_snapshot_commit
                for binding in existing.values()
            )
        ):
            return json.loads(json.dumps(existing))
    return build_definition_bindings(definition_snapshot_commit)


def recover_direct_splice_predecessor(
    committed: dict[str, Any],
    *,
    layer: str,
    historical_snapshot_commit: str,
    candidate_writer_digests: dict[str, str],
    source_commit: str,
) -> dict[str, Any]:
    """Recover the predecessor of one exact unversioned direct splice.

    This is deliberately narrower than a generic rewind.  It is only for a
    layer whose candidate pin was already spliced into the live slot without
    a successor admission.  The layer history and immutable definition must
    still be byte-identical to the historical snapshot, and the live pin must
    be exactly the candidate core derived from ``source_commit``.  Only then
    is the historical predecessor restored in memory so ``admit_successor``
    can archive it and append the governed candidate generation.
    """
    if layer not in LAYER_PREFIX:
        raise SystemExit(f"unknown layer {layer!r}; expected one of {sorted(LAYER_PREFIX)}")
    historical = _pins_at_commit(historical_snapshot_commit)
    historical_pin = historical.get("layers", {}).get(layer)
    active_pin = committed.get("layers", {}).get(layer)
    if not isinstance(historical_pin, dict) or not isinstance(active_pin, dict):
        raise SystemExit(f"{layer} direct-splice recovery needs both active and historical pins")

    historical_history = historical.get("history", {}).get(layer, [])
    active_history = committed.get("history", {}).get(layer, [])
    if active_history != historical_history:
        raise SystemExit(f"{layer} history differs from historical snapshot; refusing recovery")
    historical_definition = historical.get("definition_bindings", {}).get(layer)
    active_definition = committed.get("definition_bindings", {}).get(layer)
    if active_definition != historical_definition:
        raise SystemExit(
            f"{layer} definition binding differs from historical snapshot; refusing recovery"
        )

    lineage_keys = {"generation_id", "supersedes_generation_id", "admission"}
    if lineage_keys & set(active_pin) or lineage_keys & set(historical_pin):
        raise SystemExit(f"{layer} direct-splice recovery only accepts unversioned pins")
    expected_candidate = copy.deepcopy(historical_pin)
    expected_candidate["convergence_commit"] = source_commit
    expected_candidate["writer_inventory_sha256"] = layer_inventory_sha256(
        candidate_writer_digests, LAYER_PREFIX[layer]
    )
    if active_pin != expected_candidate:
        raise SystemExit(
            f"{layer} active pin is not the exact candidate direct splice; refusing recovery"
        )

    recovered = copy.deepcopy(committed)
    recovered["layers"][layer] = copy.deepcopy(historical_pin)
    return recovered


def admit_successor(
    committed: dict[str, Any],
    *,
    layer: str,
    previous_writer_digests: dict[str, str],
    candidate_writer_digests: dict[str, str],
    source_commit: str,
    review_artifacts: list[dict[str, str]],
    authority_decision: str,
    authority_commit: str,
    reason: str,
    classifications: dict[str, str],
    historical_snapshot_commit: str,
    definition_snapshot_commit: str,
    protected_baseline_commit: str | None = None,
) -> dict[str, Any]:
    """Append one fail-closed provenance successor without rewriting history.

    The implementation predecessor carries the candidate inventory.  This
    receipt commit therefore references an already-immutable tree and never
    tries to name its own future SHA.  The superseded pin plus its complete
    layer writer snapshot remain embedded so historical receipt bases can be
    reconstructed byte-for-byte without consulting mutable current files.
    """
    if layer not in LAYER_PREFIX:
        raise SystemExit(f"unknown layer {layer!r}; expected one of {sorted(LAYER_PREFIX)}")
    _validate_sha(source_commit, "source commit")
    _validate_sha(authority_commit, "authority commit")
    _validate_sha(historical_snapshot_commit, "historical snapshot commit")
    _validate_sha(definition_snapshot_commit, "definition snapshot commit")
    if not authority_decision.strip() or not reason.strip():
        raise SystemExit("authority decision and reason must be non-empty")
    validate_authority_binding(authority_decision, authority_commit)
    validate_review_artifacts(
        layer, review_artifacts, source_commit, protected_baseline_commit
    )
    validate_authorized_source(authority_decision, layer, source_commit)
    if _inventory_at_commit(source_commit) != candidate_writer_digests:
        raise SystemExit(
            "candidate writer inventory is not byte-equivalent to its immutable source commit"
        )

    document = json.loads(json.dumps(committed))
    if document.get("version") == LEGACY_PINS_VERSION:
        document["version"] = PINS_VERSION
        document["history"] = {known_layer: [] for known_layer in LAYER_PREFIX}
    elif document.get("version") != PINS_VERSION:
        raise SystemExit(
            f"cannot admit successor from pins version {document.get('version')!r}"
        )
    document.setdefault("history", {known_layer: [] for known_layer in LAYER_PREFIX})
    existing_definitions = document.get("definition_bindings")
    definition_bindings = _resolve_definition_bindings(
        existing_definitions, definition_snapshot_commit, protected_baseline_commit
    )
    if existing_definitions is not None and existing_definitions != definition_bindings:
        raise SystemExit("definition bindings cannot be silently replaced")
    document["definition_bindings"] = definition_bindings

    prefix = LAYER_PREFIX[layer]
    old_pin = document["layers"][layer]
    historical_pin = _pins_at_commit(historical_snapshot_commit).get("layers", {}).get(layer)
    if old_pin != historical_pin:
        raise SystemExit(
            f"{layer} active predecessor pin is not present at its historical snapshot commit"
        )
    old_slice = layer_writer_slice(previous_writer_digests, prefix)
    new_slice = layer_writer_slice(candidate_writer_digests, prefix)
    old_aggregate = layer_inventory_sha256(previous_writer_digests, prefix)
    new_aggregate = layer_inventory_sha256(candidate_writer_digests, prefix)
    if old_aggregate != old_pin.get("writer_inventory_sha256"):
        raise SystemExit(
            f"{layer} historical inventory derives {old_aggregate}, but the active "
            f"predecessor pin says {old_pin.get('writer_inventory_sha256')}"
        )
    definition_membership = receipt_membership(
        layer, old_pin, candidate_writer_digests
    )
    if (
        membership_sha256(definition_membership)
        != definition_bindings[layer]["membership_sha256"]
    ):
        raise SystemExit(
            f"{layer} candidate membership does not match the immutable definition snapshot"
        )
    changed_assets = sorted(
        asset_id
        for asset_id in set(old_slice) | set(new_slice)
        if old_slice.get(asset_id) != new_slice.get(asset_id)
    )
    if not changed_assets:
        raise SystemExit(f"{layer} has no source delta to admit")
    if sorted(classifications) != changed_assets:
        missing = sorted(set(changed_assets) - set(classifications))
        excess = sorted(set(classifications) - set(changed_assets))
        raise SystemExit(
            f"{layer} classifications must cover exactly the changed assets; "
            f"missing={missing}, excess={excess}"
        )
    unsupported = sorted(
        set(classifications.values()) - ALLOWED_DELTA_CLASSIFICATIONS
    )
    if unsupported:
        raise SystemExit(f"unsupported delta classifications: {unsupported}")
    if "unapproved_foreign_source" in classifications.values():
        raise SystemExit(
            "unapproved/foreign source cannot be admitted; exclude it from the candidate"
        )

    predecessor_generation = old_pin.get("generation_id") or generation_id(layer, old_pin)
    successor_pin = {
        "asset_prefix": prefix,
        "convergence_commit": source_commit,
        "non_writer_assets": list(old_pin.get("non_writer_assets") or []),
        "receipt_count": old_pin["receipt_count"],
        "writer_inventory_sha256": new_aggregate,
    }
    successor_generation = generation_id(layer, successor_pin)
    admission = {
        "generation_id": successor_generation,
        "supersedes_generation_id": predecessor_generation,
        "admission": {
            "schema_version": SUCCESSOR_SCHEMA_VERSION,
            "authority_decision": authority_decision,
            "authority_commit": authority_commit,
            "source_commit": source_commit,
            "review_artifacts": review_artifacts,
            "reason": reason,
            "changed_assets": changed_assets,
            "delta_classifications": {
                asset_id: classifications[asset_id] for asset_id in changed_assets
            },
        },
    }
    source_acceptance_binding = SOURCE_ACCEPTANCE_BINDINGS.get(source_commit)
    if source_acceptance_binding is not None:
        admission["admission"]["source_acceptance"] = _source_acceptance_public(
            source_acceptance_binding
        )
    validate_source_acceptance(
        source_commit, admission["admission"].get("source_acceptance")
    )
    successor_pin.update(admission)
    history_entry = {
        "generation_id": predecessor_generation,
        "historical_snapshot_commit": historical_snapshot_commit,
        "superseded_by_generation_id": successor_generation,
        "pin": old_pin,
        "writer_digests": old_slice,
    }
    existing_ids = {
        entry.get("generation_id") for entry in document["history"].setdefault(layer, [])
    }
    if predecessor_generation in existing_ids:
        raise SystemExit(f"{layer} predecessor generation is already archived")
    document["history"][layer].append(history_entry)
    document["layers"][layer] = successor_pin
    return document


def check(
    pins: dict[str, Any],
    writer_digests: dict[str, str],
    *,
    protected_baseline_commit: str | None = None,
    delivery_topology: bool = False,
) -> list[str]:
    """Offline verification: every claim in the committed pins must re-derive.

    Deliberately re-derives rather than re-reads, so this fails on a hand-edited
    pin file — the exact failure mode the missing generator allowed.
    """
    failures: list[str] = []
    try:
        validate_post_integration_source_acceptance_bindings(
            delivery_topology=delivery_topology,
            protected_baseline_commit=protected_baseline_commit,
        )
    except SystemExit as exc:
        failures.append(str(exc))
    baseline_pins: dict[str, Any] | None = None
    baseline_inventory: dict[str, str] | None = None
    baseline_nodes_by_layer: dict[
        str, dict[str, tuple[dict[str, Any], dict[str, str]]]
    ] = {}
    baseline_history_entries_by_layer: dict[str, dict[str, dict[str, Any]]] = {}
    if delivery_topology and protected_baseline_commit is None:
        failures.append("delivery topology requires a protected baseline commit")
    if protected_baseline_commit is not None:
        try:
            _require_reachable_commit(protected_baseline_commit, "protected baseline")
            baseline_pins = _pins_at_commit(protected_baseline_commit)
            baseline_inventory = _inventory_at_commit(protected_baseline_commit)
        except SystemExit as exc:
            failures.append(f"protected baseline: {exc}")
        if baseline_pins is not None and baseline_inventory is not None:
            baseline_history = baseline_pins.get("history", {})
            baseline_layers = baseline_pins.get("layers", {})
            if not isinstance(baseline_history, dict) or not isinstance(
                baseline_layers, dict
            ):
                failures.append("protected baseline pin document is malformed")
            else:
                for layer, prefix in LAYER_PREFIX.items():
                    layer_nodes: dict[
                        str, tuple[dict[str, Any], dict[str, str]]
                    ] = {}
                    layer_history_entries: dict[str, dict[str, Any]] = {}
                    for entry in baseline_history.get(layer, []):
                        if not isinstance(entry, dict):
                            continue
                        generation = entry.get("generation_id")
                        pin = entry.get("pin")
                        writers = entry.get("writer_digests")
                        if (
                            isinstance(generation, str)
                            and isinstance(pin, dict)
                            and isinstance(writers, dict)
                        ):
                            layer_nodes[generation] = (pin, writers)
                            layer_history_entries[generation] = entry
                    active_pin = baseline_layers.get(layer)
                    if isinstance(active_pin, dict):
                        active_generation = active_pin.get("generation_id")
                        if isinstance(active_generation, str):
                            layer_nodes[active_generation] = (
                                active_pin,
                                layer_writer_slice(baseline_inventory, prefix),
                            )
                    baseline_nodes_by_layer[layer] = layer_nodes
                    baseline_history_entries_by_layer[layer] = layer_history_entries
    if pins.get("version") != PINS_VERSION:
        failures.append(f"pins version is {pins.get('version')!r}, expected {PINS_VERSION!r}")
    history = pins.get("history")
    if not isinstance(history, dict):
        failures.append("successor history is missing or is not an object")
        history = {}
    definitions = pins.get("definition_bindings")
    if not isinstance(definitions, dict) or set(definitions) != set(LAYER_PREFIX):
        failures.append("definition bindings must cover every and only L0-L5")
        definitions = {}

    inventory_cache: dict[str, dict[str, str] | None] = {}
    pin_cache: dict[str, dict[str, Any] | None] = {}

    def inventory_at_commit(commit: str, label: str) -> dict[str, str] | None:
        if commit not in inventory_cache:
            try:
                inventory_cache[commit] = _inventory_at_commit(commit)
            except SystemExit as exc:
                failures.append(f"{label}: {exc}")
                inventory_cache[commit] = None
        return inventory_cache[commit]

    def pins_at_commit(commit: str, label: str) -> dict[str, Any] | None:
        if commit not in pin_cache:
            try:
                pin_cache[commit] = _pins_at_commit(commit)
            except SystemExit as exc:
                failures.append(f"{label}: {exc}")
                pin_cache[commit] = None
        return pin_cache[commit]

    def pin_common(
        layer: str,
        pin: dict[str, Any],
        inventory: dict[str, str],
        label: str,
    ) -> None:
        prefix = LAYER_PREFIX[layer]
        if pin.get("asset_prefix") != prefix:
            failures.append(f"{label}: wrong asset prefix")
        if not re.fullmatch(r"[a-f0-9]{40}", str(pin.get("convergence_commit", ""))):
            failures.append(f"{label}: convergence commit is invalid")
        # Historical convergence identities are immutable receipt metadata.
        # The checker validates their embedded inventories and reachable
        # snapshot/source-equivalence proofs without requiring old lane refs.
        layer_writers = layer_writer_slice(inventory, prefix)
        invalid_digests = sorted(
            asset_id
            for asset_id, digest in layer_writers.items()
            if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest)
        )
        if invalid_digests:
            failures.append(f"{label}: invalid writer digests for {invalid_digests}")
        try:
            derived = layer_inventory_sha256(inventory, prefix)
        except SystemExit as exc:
            failures.append(f"{label}: {exc}")
            return
        if pin.get("writer_inventory_sha256") != derived:
            failures.append(
                f"{label}: writer_inventory_sha256 is stale — committed "
                f"{pin.get('writer_inventory_sha256')}, inventory derives {derived}"
            )
        try:
            membership = receipt_membership(layer, pin, inventory)
        except SystemExit as exc:
            failures.append(f"{label}: {exc}")
            return
        if pin.get("receipt_count") != len(membership["asset_ids"]):
            failures.append(f"{label}: receipt_count does not match exact membership")

    def admission_common(
        layer: str,
        pin: dict[str, Any],
        inventory: dict[str, str],
        label: str,
        *,
        validate_references: bool = True,
    ) -> None:
        admission = pin.get("admission")
        if not isinstance(admission, dict):
            failures.append(f"{label}: successor pin has no admission record")
            return
        if admission.get("schema_version") != SUCCESSOR_SCHEMA_VERSION:
            failures.append(f"{label}: successor admission schema is invalid")
        if admission.get("source_commit") != pin.get("convergence_commit"):
            failures.append(f"{label}: source commit does not match convergence pin")
        source_commit = str(admission.get("source_commit", ""))
        if not re.fullmatch(r"[a-f0-9]{40}", source_commit):
            failures.append(f"{label}: source commit is invalid")
        elif validate_references:
            source_inventory = inventory_at_commit(source_commit, f"{label} source")
            if (
                source_inventory is not None
                and layer_writer_slice(source_inventory, LAYER_PREFIX[layer])
                != layer_writer_slice(inventory, LAYER_PREFIX[layer])
            ):
                failures.append(f"{label}: inventory does not match immutable source commit")
        decision = str(admission.get("authority_decision", ""))
        authority_commit = str(admission.get("authority_commit", ""))
        if validate_references:
            try:
                validate_authority_binding(decision, authority_commit)
            except SystemExit as exc:
                failures.append(f"{label}: {exc}")
        else:
            expected_authority = AUTHORITY_BINDINGS.get(decision)
            if (
                expected_authority is None
                or expected_authority["authority_commit"] != authority_commit
            ):
                failures.append(
                    f"{label}: authority decision {decision!r} is not bound to "
                    f"{authority_commit}"
                )
        try:
            validate_authorized_source(decision, layer, source_commit)
        except SystemExit as exc:
            failures.append(f"{label}: {exc}")
        artifacts = admission.get("review_artifacts")
        if not isinstance(artifacts, list):
            failures.append(f"{label}: review artifacts are missing")
        elif validate_references:
            try:
                validate_review_artifacts(
                    layer, artifacts, source_commit, protected_baseline_commit
                )
            except SystemExit as exc:
                failures.append(f"{label}: {exc}")
        else:
            source_binding = SOURCE_ACCEPTANCE_BINDINGS.get(source_commit)
            expected_artifacts = (
                source_binding.get("review_artifacts", {}).get(layer)
                if source_binding is not None
                else EXPECTED_REVIEW_ARTIFACTS.get(layer)
            )
            if expected_artifacts is None or artifacts != expected_artifacts:
                failures.append(
                    f"{label}: review artifacts do not match the required acceptance "
                    f"artifacts for source {source_commit}"
                )
        source_acceptance = admission.get("source_acceptance")
        if source_acceptance is not None and not isinstance(source_acceptance, dict):
            failures.append(f"{label}: source acceptance binding is malformed")
        elif validate_references:
            try:
                validate_source_acceptance(source_commit, source_acceptance)
            except SystemExit as exc:
                failures.append(f"{label}: {exc}")
        else:
            configured_source = SOURCE_ACCEPTANCE_BINDINGS.get(source_commit)
            expected_source = (
                _source_acceptance_public(configured_source)
                if configured_source is not None
                else None
            )
            if source_acceptance != expected_source:
                failures.append(
                    f"{label}: source commit {source_commit} is missing or has the "
                    "wrong source-acceptance binding"
                )
        if not str(admission.get("reason", "")).strip():
            failures.append(f"{label}: successor reason is missing")
        changed_assets = admission.get("changed_assets")
        classifications = admission.get("delta_classifications")
        if not isinstance(changed_assets, list) or changed_assets != sorted(set(changed_assets)):
            failures.append(f"{label}: changed_assets must be sorted and unique")
        if not isinstance(classifications, dict) or sorted(classifications) != changed_assets:
            failures.append(f"{label}: classifications do not exactly cover changed_assets")
        elif any(value not in ALLOWED_DELTA_CLASSIFICATIONS for value in classifications.values()):
            failures.append(f"{label}: delta classification vocabulary is invalid")
        elif "unapproved_foreign_source" in classifications.values():
            failures.append(f"{label}: an unapproved/foreign delta was admitted")

    for layer, prefix in LAYER_PREFIX.items():
        active_pin = pins.get("layers", {}).get(layer)
        if not isinstance(active_pin, dict):
            failures.append(f"{layer}: missing from the pin record")
            continue
        pin_common(layer, active_pin, writer_digests, f"{layer} active")

        definition = definitions.get(layer)
        if not isinstance(definition, dict):
            failures.append(f"{layer}: immutable definition binding is missing")
        else:
            snapshot_commit = str(definition.get("snapshot_commit", ""))
            if definition.get("schema_version") != DEFINITION_SCHEMA_VERSION:
                failures.append(f"{layer}: definition schema is invalid")
            if baseline_pins is not None and baseline_inventory is not None:
                baseline_definition = baseline_pins.get("definition_bindings", {}).get(
                    layer
                )
                if definition != baseline_definition:
                    failures.append(
                        f"{layer}: definition binding differs from protected baseline"
                    )
                snapshot_inventory = baseline_inventory
                snapshot_pin = baseline_pins.get("layers", {}).get(layer)
            else:
                snapshot_inventory = inventory_at_commit(
                    snapshot_commit, f"{layer} definition"
                )
                snapshot_pins = pins_at_commit(
                    snapshot_commit, f"{layer} definition"
                )
                snapshot_pin = (
                    snapshot_pins.get("layers", {}).get(layer)
                    if isinstance(snapshot_pins, dict)
                    else None
                )
            if snapshot_inventory is not None and isinstance(snapshot_pin, dict):
                try:
                    expected_membership = receipt_membership(
                        layer, snapshot_pin, snapshot_inventory
                    )
                    active_membership = receipt_membership(
                        layer, active_pin, writer_digests
                    )
                    expected_digest = membership_sha256(expected_membership)
                    if definition.get("membership_sha256") != expected_digest:
                        failures.append(f"{layer}: definition membership digest is invalid")
                    if active_membership != expected_membership:
                        failures.append(
                            f"{layer}: active membership differs from immutable definition"
                        )
                    if not active_pin.get("generation_id") and active_pin != snapshot_pin:
                        failures.append(
                            f"{layer}: unversioned active pin differs from immutable definition snapshot"
                        )
                except SystemExit as exc:
                    failures.append(f"{layer}: invalid definition membership: {exc}")
            elif snapshot_pin is None:
                failures.append(f"{layer}: definition snapshot has no layer pin")

        layer_history = history.get(layer, [])
        if not isinstance(layer_history, list):
            failures.append(f"{layer}: history is not a list")
            continue
        nodes: dict[str, tuple[dict[str, Any], dict[str, str]]] = {}
        outgoing: dict[str, str] = {}
        for entry in layer_history:
            if not isinstance(entry, dict):
                failures.append(f"{layer}: malformed history entry")
                continue
            archived_pin = entry.get("pin")
            archived_writers = entry.get("writer_digests")
            archived_generation = entry.get("generation_id")
            if not isinstance(archived_pin, dict) or not isinstance(archived_writers, dict):
                failures.append(f"{layer}: historical pin or writer snapshot is missing")
                continue
            if not isinstance(archived_generation, str):
                failures.append(f"{layer}: historical generation id is invalid")
                continue
            pin_common(layer, archived_pin, archived_writers, f"{layer} history {archived_generation}")
            if archived_generation != generation_id(layer, archived_pin):
                failures.append(f"{layer}: historical generation id does not match its pin")
            if archived_generation in nodes:
                failures.append(f"{layer}: duplicate historical generation {archived_generation}")
                continue
            nodes[archived_generation] = (archived_pin, archived_writers)
            successor_generation = entry.get("superseded_by_generation_id")
            if not isinstance(successor_generation, str):
                failures.append(f"{layer}: historical successor generation is invalid")
                continue
            outgoing[archived_generation] = successor_generation
            baseline_node = baseline_nodes_by_layer.get(layer, {}).get(
                archived_generation
            )
            if baseline_node is not None:
                if baseline_node != (archived_pin, archived_writers):
                    failures.append(
                        f"{layer}: archived generation differs from protected baseline"
                    )
                baseline_entry = baseline_history_entries_by_layer.get(layer, {}).get(
                    archived_generation
                )
                if baseline_entry is not None and entry != baseline_entry:
                    failures.append(
                        f"{layer}: protected baseline history entry "
                        f"{archived_generation} was rewritten"
                    )
                elif (
                    baseline_entry is None
                    and protected_baseline_commit is not None
                    and entry.get("historical_snapshot_commit")
                    != protected_baseline_commit
                ):
                    failures.append(
                        f"{layer}: newly archived protected generation "
                        f"{archived_generation} must name protected baseline "
                        f"{protected_baseline_commit} as its historical snapshot"
                    )
            else:
                snapshot_commit = str(entry.get("historical_snapshot_commit", ""))
                snapshot_inventory = inventory_at_commit(
                    snapshot_commit, f"{layer} history snapshot"
                )
                snapshot_pins = pins_at_commit(
                    snapshot_commit, f"{layer} history snapshot"
                )
                snapshot_pin = (
                    snapshot_pins.get("layers", {}).get(layer)
                    if isinstance(snapshot_pins, dict)
                    else None
                )
                if snapshot_inventory is not None and layer_writer_slice(
                    snapshot_inventory, prefix
                ) != archived_writers:
                    failures.append(
                        f"{layer}: archived writers differ from immutable historical snapshot"
                    )
                if snapshot_pin != archived_pin:
                    failures.append(
                        f"{layer}: archived pin differs from immutable historical snapshot"
                    )

        current_generation = active_pin.get("generation_id")
        if current_generation:
            if not isinstance(current_generation, str):
                failures.append(f"{layer}: active generation id is invalid")
                continue
            if current_generation != generation_id(layer, active_pin):
                failures.append(f"{layer}: active generation id does not match its pin")
            if current_generation in nodes:
                failures.append(f"{layer}: active generation is duplicated in history")
            nodes[current_generation] = (active_pin, layer_writer_slice(writer_digests, prefix))
            for baseline_generation, baseline_node in baseline_nodes_by_layer.get(
                layer, {}
            ).items():
                current_node = nodes.get(baseline_generation)
                if current_node is None:
                    failures.append(
                        f"{layer}: protected baseline generation {baseline_generation} "
                        "is absent"
                    )
                elif current_node != baseline_node:
                    failures.append(
                        f"{layer}: protected baseline generation {baseline_generation} "
                        "was rewritten"
                    )
            targets = list(outgoing.values())
            unknown_targets = sorted(set(targets) - set(nodes), key=str)
            if unknown_targets:
                failures.append(f"{layer}: history points to unknown successors {unknown_targets}")
            roots = sorted(set(nodes) - set(targets), key=str)
            if len(roots) != 1:
                failures.append(f"{layer}: successor history must have exactly one root")
            else:
                visited: list[str] = []
                cursor = roots[0]
                while cursor not in visited:
                    visited.append(cursor)
                    if cursor == current_generation:
                        break
                    next_generation = outgoing.get(cursor)
                    if next_generation is None:
                        break
                    cursor = next_generation
                if cursor != current_generation or set(visited) != set(nodes):
                    failures.append(f"{layer}: successor history is not one complete linear chain")
                root_pin = nodes[roots[0]][0]
                if root_pin.get("admission") or root_pin.get("supersedes_generation_id"):
                    failures.append(f"{layer}: successor history root is not the legacy predecessor")

            predecessor_by_successor: dict[str, list[str]] = {}
            for predecessor, successor in outgoing.items():
                predecessor_by_successor.setdefault(successor, []).append(predecessor)
            for successor, predecessors in predecessor_by_successor.items():
                if len(predecessors) != 1 or successor not in nodes:
                    continue
                predecessor = predecessors[0]
                successor_pin, successor_writers = nodes[successor]
                predecessor_writers = nodes[predecessor][1]
                if successor_pin.get("supersedes_generation_id") != predecessor:
                    failures.append(f"{layer}: successor does not name its actual predecessor")
                admission_common(
                    layer,
                    successor_pin,
                    successor_writers,
                    f"{layer} successor {successor}",
                    validate_references=(
                        successor not in baseline_nodes_by_layer.get(layer, {})
                        and not delivery_topology
                    ),
                )
                exact_delta = sorted(
                    asset_id
                    for asset_id in set(predecessor_writers) | set(successor_writers)
                    if predecessor_writers.get(asset_id) != successor_writers.get(asset_id)
                )
                admission = successor_pin.get("admission")
                if isinstance(admission, dict) and admission.get("changed_assets") != exact_delta:
                    failures.append(
                        f"{layer}: successor {successor} changed_assets do not match exact delta"
                    )
        elif layer_history:
            failures.append(f"{layer}: history exists but active pin is not versioned")

    l0_history = history.get("L0", []) if isinstance(history, dict) else []
    active_l0 = pins.get("layers", {}).get("L0", {})
    if not all(active_l0.get(key) == value for key, value in L0_FROZEN_PINS.items()) and not any(
        isinstance(entry, dict)
        and all(entry.get("pin", {}).get(key) == frozen_value for key, frozen_value in L0_FROZEN_PINS.items())
        for entry in l0_history
    ):
        failures.append("L0 immutable frozen baseline is absent from successor history")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the committed pins (no DB)")
    parser.add_argument(
        "--protected-baseline-commit",
        help=(
            "protected base commit whose accepted pin history is packaged into the "
            "candidate; permits squash-delivered history to be verified without "
            "dereferencing side-ref-only commits"
        ),
    )
    parser.add_argument(
        "--delivery-topology",
        action="store_true",
        help=(
            "verify a merge-group or protected-main delivery tree after the strict "
            "source-head check has already passed"
        ),
    )
    parser.add_argument(
        "--convergence-commit",
        help="reviewed commit to pin for layers other than L0 (required to regenerate)",
    )
    parser.add_argument(
        "--admit-successor",
        action="store_true",
        help="append one reviewed layer successor while retaining the complete predecessor",
    )
    parser.add_argument(
        "--recover-direct-splice",
        action="store_true",
        help=(
            "before successor admission, recover the exact unversioned predecessor from "
            "--historical-snapshot-commit; fails unless history, definition and candidate "
            "pin are otherwise byte-identical"
        ),
    )
    parser.add_argument("--source-commit", help="immutable implementation predecessor")
    parser.add_argument(
        "--historical-snapshot-commit",
        help="immutable commit whose writer inventory reconstructs the active predecessor",
    )
    parser.add_argument("--authority-decision", help="decision authorizing this successor")
    parser.add_argument("--authority-commit", help="immutable approval commit")
    parser.add_argument(
        "--review-artifact",
        action="append",
        default=[],
        help="immutable acceptance-artifact JSON; repeat when multiple reviews apply",
    )
    parser.add_argument(
        "--definition-snapshot-commit",
        help="immutable pin/inventory snapshot defining exact receipt membership",
    )
    parser.add_argument("--reason", help="bounded evidence-backed successor reason")
    parser.add_argument(
        "--classification",
        action="append",
        default=[],
        help="asset_id=classification; must cover every and only changed layer identity",
    )
    parser.add_argument(
        "--layer",
        help=(
            "regenerate ONLY this layer's record (e.g. L3), preserving every other "
            "layer's committed pin verbatim. Use this when your own writers changed: "
            "the whole-file regeneration restates every non-L0 layer's "
            "convergence_commit, which is a false claim about other sessions' review "
            "state. See NIRMANA issue #1814."
        ),
    )
    parser.add_argument("--output", type=Path, default=PINS_PATH)
    args = parser.parse_args()

    writer_digests = json.loads(WRITER_DIGESTS_PATH.read_text(encoding="utf-8"))["writers"]

    if args.check:
        if not args.output.is_file():
            print(f"ERROR: {args.output} does not exist", file=sys.stderr)
            return 1
        failures = check(
            json.loads(args.output.read_text(encoding="utf-8")),
            writer_digests,
            protected_baseline_commit=args.protected_baseline_commit,
            delivery_topology=args.delivery_topology,
        )
        if failures:
            print("Nirmana analysis layer pins are STALE or INVALID:", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            print(
                "\nRegenerate with: python -m scripts.generate.nirmana_analysis_layer_pins "
                "--convergence-commit <reviewed sha>",
                file=sys.stderr,
            )
            return 1
        print(f"Nirmana analysis layer pins are current ({args.output.name}).")
        return 0

    if args.admit_successor:
        required = {
            "--layer": args.layer,
            "--source-commit": args.source_commit,
            "--historical-snapshot-commit": args.historical_snapshot_commit,
            "--definition-snapshot-commit": args.definition_snapshot_commit,
            "--authority-decision": args.authority_decision,
            "--authority-commit": args.authority_commit,
            "--reason": args.reason,
        }
        missing = [flag for flag, value in required.items() if not value]
        if missing:
            print(f"ERROR: successor admission requires {', '.join(missing)}", file=sys.stderr)
            return 1
        previous_inventory = _inventory_at_commit(args.historical_snapshot_commit)
        committed = json.loads(args.output.read_text(encoding="utf-8"))
        if args.recover_direct_splice:
            committed = recover_direct_splice_predecessor(
                committed,
                layer=args.layer,
                historical_snapshot_commit=args.historical_snapshot_commit,
                candidate_writer_digests=writer_digests,
                source_commit=args.source_commit,
            )
        successor = admit_successor(
            committed,
            layer=args.layer,
            previous_writer_digests=previous_inventory,
            candidate_writer_digests=writer_digests,
            source_commit=args.source_commit,
            review_artifacts=parse_review_artifacts(args.review_artifact),
            authority_decision=args.authority_decision,
            authority_commit=args.authority_commit,
            reason=args.reason,
            classifications=parse_classifications(args.classification),
            historical_snapshot_commit=args.historical_snapshot_commit,
            definition_snapshot_commit=args.definition_snapshot_commit,
            protected_baseline_commit=args.protected_baseline_commit,
        )
        args.output.write_text(render(successor), encoding="utf-8")
        print(
            f"Wrote {args.output} -- admitted {args.layer} successor "
            f"{successor['layers'][args.layer]['generation_id']}."
        )
        return 0

    if not args.convergence_commit or len(args.convergence_commit) != 40:
        print(
            "ERROR: --convergence-commit <40-hex sha> is required to regenerate.",
            file=sys.stderr,
        )
        return 1
    if not args.definition_snapshot_commit:
        print(
            "ERROR: --definition-snapshot-commit <40-hex sha> is required to regenerate.",
            file=sys.stderr,
        )
        return 1

    if args.layer:
        # Per-layer regeneration (NIRMANA issue #1814, Conductor ruling option A).
        #
        # Whole-file regeneration rewrites every non-L0 layer's convergence_commit
        # from the single --convergence-commit argument. For a layer that did not
        # change, that restates "the reviewed commit whose writer inventory this
        # pins" as a value nobody reviewed it at -- a false claim about four other
        # sessions' review state, and the D-CND-16 defect committed by a tool
        # rather than by a comment. It also makes two lanes re-pinning in parallel
        # fight over one file.
        #
        # So: splice in ONLY the named layer's freshly-derived record and carry
        # every other layer's committed record through byte-for-byte. These
        # checks -- and which layers build_pins() below actually computes and
        # validates -- happen BEFORE any L0 work, so an L5-only (or any non-L0)
        # request never reaches L0's frozen-pin comparison at all (NIRMANA issue
        # #1930; see NIRMANA_L0_L5_RECEIPT_COUPLING_FIX_ADDENDUM_v1_0.md).
        if not args.output.is_file():
            print(f"ERROR: --layer needs an existing {args.output}", file=sys.stderr)
            return 1
        committed = json.loads(args.output.read_text(encoding="utf-8"))
        if args.layer not in committed.get("layers", {}):
            print(
                f"ERROR: unknown layer {args.layer!r}; "
                f"known: {sorted(committed.get('layers', {}))}",
                file=sys.stderr,
            )
            return 1
        if args.layer == "L0":
            # L0's three pins are frozen against 29 accepted capsules. Re-deriving
            # them would invalidate every one of them, and no L0 writer change is
            # in scope for this campaign.
            print(
                "ERROR: refusing to re-pin L0 -- its pins are frozen against "
                "accepted capsules (#1715 requirement 3).",
                file=sys.stderr,
            )
            return 1
        pins = build_pins(
            writer_digests,
            load_frozen_manifest_assets(),
            args.convergence_commit,
            args.definition_snapshot_commit,
            layers=[args.layer],
        )
        before = committed["layers"][args.layer]
        accepted_definition_binding = None
        if args.protected_baseline_commit:
            _require_reachable_commit(
                args.protected_baseline_commit, "protected baseline"
            )
            accepted_definition_binding = _pins_at_commit(
                args.protected_baseline_commit
            ).get("definition_bindings", {}).get(args.layer)
            if not isinstance(accepted_definition_binding, dict):
                print(
                    f"ERROR: protected baseline has no {args.layer} definition binding",
                    file=sys.stderr,
                )
                return 1
        updated = splice_layer_pin(
            committed,
            args.layer,
            pins,
            accepted_definition_binding=accepted_definition_binding,
        )
        fresh = updated["layers"][args.layer]
        args.output.write_text(render(updated), encoding="utf-8")
        moved = [k for k in fresh if before.get(k) != fresh.get(k)]
        print(f"Wrote {args.output} -- {args.layer} only.")
        print(f"  fields changed: {', '.join(moved) if moved else '(none)'}")
        print(f"  layers untouched: {', '.join(k for k in updated['layers'] if k != args.layer)}")
        return 0

    # Whole-file regeneration: every layer, L0 included, is derived and validated.
    pins = build_pins(
        writer_digests,
        load_frozen_manifest_assets(),
        args.convergence_commit,
        args.definition_snapshot_commit,
    )
    args.output.write_text(render(pins), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
