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
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

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
SUPPORTING_WRITERS = frozenset({"bo_grounding"})
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
) -> dict[str, Any]:
    layers: dict[str, Any] = {}
    for layer, prefix in LAYER_PREFIX.items():
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
            # rather than silently re-pin it.
            for key in ("writer_inventory_sha256", "receipt_count"):
                if pin[key] != L0_FROZEN_PINS[key]:
                    raise SystemExit(
                        f"L0 {key} derives to {pin[key]!r} but is frozen at "
                        f"{L0_FROZEN_PINS[key]!r}; re-pinning L0 would invalidate "
                        "its accepted analyses. Investigate before regenerating."
                    )
        layers[layer] = pin
    definition_bindings = build_definition_bindings(definition_snapshot_commit)
    for layer, pin in layers.items():
        membership = receipt_membership(layer, pin, writer_digests)
        if membership_sha256(membership) != definition_bindings[layer]["membership_sha256"]:
            raise SystemExit(
                f"{layer} database manifest differs from immutable definition snapshot"
            )
    return {
        "version": PINS_VERSION,
        "layers": layers,
        "history": {layer: [] for layer in LAYER_PREFIX},
        "definition_bindings": definition_bindings,
    }


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


def build_definition_bindings(snapshot_commit: str) -> dict[str, Any]:
    _validate_sha(snapshot_commit, "definition snapshot commit")
    snapshot_pins = _pins_at_commit(snapshot_commit).get("layers", {})
    snapshot_inventory = _inventory_at_commit(snapshot_commit)
    bindings: dict[str, Any] = {}
    for layer in LAYER_PREFIX:
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
    pins = build_pins(
        writer_digests,
        load_frozen_manifest_assets(),
        args.convergence_commit,
        args.definition_snapshot_commit,
    )

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
        # every other layer's committed record through byte-for-byte.
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
        fresh = pins["layers"][args.layer]
        before = committed["layers"][args.layer]
        committed["layers"][args.layer] = fresh
        committed.setdefault("definition_bindings", {})[args.layer] = pins[
            "definition_bindings"
        ][args.layer]
        args.output.write_text(render(committed), encoding="utf-8")
        moved = [k for k in fresh if before.get(k) != fresh.get(k)]
        print(f"Wrote {args.output} -- {args.layer} only.")
        print(f"  fields changed: {', '.join(moved) if moved else '(none)'}")
        print(f"  layers untouched: {', '.join(k for k in committed['layers'] if k != args.layer)}")
        return 0

    args.output.write_text(render(pins), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
