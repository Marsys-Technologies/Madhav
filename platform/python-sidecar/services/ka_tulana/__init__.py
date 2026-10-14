"""K7-4 comparison service and version-specific certification evidence.

The mapping is audited from the repository, never required by sidecar runtime
(which does not ship web sources). It awards no unmeasured certification PASS.
"""
import ast
import hashlib
import json
from pathlib import Path

from .ranker import KaTulanaService, WindowInput, KNOWN_DOMAINS

__all__ = ["KaTulanaService", "WindowInput", "KNOWN_DOMAINS", "CERTIFICATION_MAPPING", "validate_certification_mapping"]

CERTIFICATION_MAPPING = json.loads(r'''
{
  "schema": "k7-4:certification_mapping:v1",
  "asset_id": "ka_tulana",
  "kind": "service",
  "carriage": {
    "nature": "computation",
    "served_call": "platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts:700",
    "served_surface": null,
    "read_table": null
  },
  "ldgr_source": null,
  "vocab_alias": null,
  "prose_fields": null,
  "null_convention": {
    "unbound_dw": "information_unavailable(stage_to_reader_mapping_unadmitted)",
    "null_dw": "information_unavailable(null_reason)",
    "null_tier": "information_unavailable(robustness_not_computed)",
    "obstruction": "annotation_only; unavailable distinct from evaluated_silent"
  },
  "produced_tables": [],
  "writer_digest_entry": "platform/src/generated/nirmana-writer-digests.json#/writers/ka_tulana",
  "semantic_fingerprint": {
    "contract_version": "k7-4:pareto:v1",
    "axes": [
      "nearest",
      "strongest",
      "most_robust",
      "best_suited_if_frame"
    ],
    "dominance": "all active axes available; tie-or-better everywhere; one strict win",
    "ordering": "declared caller lexicographic preference, remaining defaults appended",
    "live_jury_binding": "unadmitted",
    "fixed_weights": false
  },
  "disposition": "Service wired beside legacy scalar aliases; live jury mapping explicitly unavailable. Certification and production publication remain unmeasured.",
  "registry_revision": 30,
  "registry_path": "platform/scripts/governance/asset_census.py",
  "detectors": {
    "Build.contract": {
      "detector": "asset_census.py:measure()",
      "revision": 2,
      "verdict": "UNMEASURED"
    },
    "Idem.pattern": {
      "detector": "asset_census.py:measure()",
      "revision": 5,
      "verdict": "UNMEASURED"
    },
    "Dens.served": {
      "detector": "asset_census.py:measure()",
      "revision": 14,
      "verdict": "UNMEASURED"
    },
    "Narr.agree": {
      "detector": "asset_census.py:measure()",
      "revision": 8,
      "verdict": "UNMEASURED"
    },
    "Narr.checkable": {
      "detector": "asset_census.py:measure()",
      "revision": 8,
      "verdict": "UNMEASURED"
    },
    "Narr.fidelity_test": {
      "detector": "asset_census.py:measure()",
      "revision": 7,
      "verdict": "UNMEASURED"
    },
    "Narr.lint": {
      "detector": "asset_census.py:measure()",
      "revision": 7,
      "verdict": "UNMEASURED"
    },
    "Null.schema_default": {
      "detector": "asset_census.py:measure()",
      "revision": 11,
      "verdict": "UNMEASURED"
    },
    "Null.blank_rows": {
      "detector": "asset_census.py:measure()",
      "revision": 11,
      "verdict": "UNMEASURED"
    },
    "Carr.D1": {
      "detector": "asset_census.py:measure()",
      "revision": 5,
      "verdict": "UNMEASURED"
    },
    "Carr.D2": {
      "detector": "NONE",
      "revision": 3,
      "verdict": "NO_DETECTOR"
    },
    "Carr.D3": {
      "detector": "asset_census.py:measure()",
      "revision": 4,
      "verdict": "UNMEASURED"
    },
    "Earn.service_state": {
      "detector": "asset_census.py:measure()",
      "revision": 2,
      "verdict": "UNMEASURED"
    }
  },
  "views": {
    "now": {
      "public_name": "kala_now_get",
      "public_uri": "marsys://tool/L3/kala_now_get",
      "stage_uri": "marsys://tool/L3/now_read",
      "module": "platform/src/lib/retrieval/registry/layers/L3_kala/view_now.ts",
      "sources": [
        "kala_darshana",
        "kala_obstruction"
      ],
      "tier_select": "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts:266",
      "density_contract": {
        "paginated": true,
        "facets": [
          "event_class",
          "source_table"
        ],
        "empty_reason": true,
        "stored_tier_columns": [
          "kala_darshana.verification_pass_status",
          "kala_obstruction.verification_pass_status"
        ]
      },
      "fidelity_tests": [
        "platform/src/lib/retrieval/registry/layers/L3_kala/views_registry.integration.test.ts",
        "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.test.ts"
      ],
      "narration": "Stored stage data and roots carried verbatim; no verified prose or chart computation inferred.",
      "known_gaps": [
        "Missing stored tier stays unknown; public web adapter remains deliberately dark until cutover equivalence."
      ]
    },
    "ahead": {
      "public_name": "kala_ahead_get",
      "public_uri": "marsys://tool/L3/kala_ahead_get",
      "stage_uri": "marsys://tool/L3/ahead_read",
      "module": "platform/src/lib/retrieval/registry/layers/L3_kala/view_ahead.ts",
      "sources": [
        "kala_darshana",
        "kala_bhavishya",
        "kala_gochara_contacts"
      ],
      "tier_select": "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts:266",
      "density_contract": {
        "paginated": true,
        "facets": [
          "event_class",
          "source_table"
        ],
        "empty_reason": true,
        "stored_tier_columns": [
          "kala_darshana.verification_pass_status",
          "kala_bhavishya.verification_pass_status",
          "kala_gochara_contacts.verification_pass_status"
        ]
      },
      "fidelity_tests": [
        "platform/src/lib/retrieval/registry/layers/L3_kala/views_registry.integration.test.ts",
        "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.test.ts"
      ],
      "narration": "Stored stage data and roots carried verbatim; no verified prose or chart computation inferred.",
      "known_gaps": [
        "Missing stored tier stays unknown; public web adapter remains deliberately dark until cutover equivalence."
      ]
    },
    "priority": {
      "public_name": "kala_priority_get",
      "public_uri": "marsys://tool/L3/kala_priority_get",
      "stage_uri": "marsys://tool/L3/priority_read",
      "module": "platform/src/lib/retrieval/registry/layers/L3_kala/view_priority.ts",
      "sources": [
        "kala_darshana",
        "kala_convergence"
      ],
      "tier_select": "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts:266",
      "density_contract": {
        "paginated": true,
        "facets": [
          "event_class",
          "source_table"
        ],
        "empty_reason": true,
        "stored_tier_columns": [
          "kala_darshana.verification_pass_status",
          "kala_convergence.verification_pass_status"
        ]
      },
      "fidelity_tests": [
        "platform/src/lib/retrieval/registry/layers/L3_kala/views_registry.integration.test.ts",
        "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.test.ts",
        "platform/src/lib/retrieval/registry/layers/L3_kala/__tests__/f131_priority_ranking_glossary.test.ts",
        "platform-mcp/src/tools/kala_views/f171_disclosure_receipt_regression.test.ts"
      ],
      "narration": "Stored stage data and roots carried verbatim; no verified prose or chart computation inferred.",
      "known_gaps": [
        "Missing stored tier stays unknown; public web adapter remains deliberately dark until cutover equivalence."
      ]
    },
    "elect": {
      "public_name": "kala_elect_get",
      "public_uri": "marsys://tool/L3/kala_elect_get",
      "stage_uri": "marsys://tool/L3/elect_read",
      "module": "platform/src/lib/retrieval/registry/layers/L3_kala/view_elect.ts",
      "sources": [
        "kala_darshana",
        "kala_obstruction",
        "kala_gochara_contacts"
      ],
      "tier_select": "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts:266",
      "density_contract": {
        "paginated": true,
        "facets": [
          "event_class",
          "source_table"
        ],
        "empty_reason": true,
        "stored_tier_columns": [
          "kala_darshana.verification_pass_status",
          "kala_obstruction.verification_pass_status",
          "kala_gochara_contacts.verification_pass_status"
        ]
      },
      "fidelity_tests": [
        "platform/src/lib/retrieval/registry/layers/L3_kala/views_registry.integration.test.ts",
        "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.test.ts"
      ],
      "narration": "Stored stage data and roots carried verbatim; no verified prose or chart computation inferred.",
      "known_gaps": [
        "Missing stored tier stays unknown; public web adapter remains deliberately dark until cutover equivalence."
      ]
    },
    "story": {
      "public_name": "kala_story_get",
      "public_uri": "marsys://tool/L3/kala_story_get",
      "stage_uri": "marsys://tool/L3/story_read",
      "module": "platform/src/lib/retrieval/registry/layers/L3_kala/view_story.ts",
      "sources": [
        "kala_darshana",
        "kala_jivana_parva"
      ],
      "tier_select": "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts:266",
      "density_contract": {
        "paginated": true,
        "facets": [
          "event_class",
          "source_table"
        ],
        "empty_reason": true,
        "stored_tier_columns": [
          "kala_darshana.verification_pass_status",
          "kala_jivana_parva.verification_pass_status"
        ]
      },
      "fidelity_tests": [
        "platform/src/lib/retrieval/registry/layers/L3_kala/views_registry.integration.test.ts",
        "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.test.ts"
      ],
      "narration": "Stored stage data and roots carried verbatim; no verified prose or chart computation inferred.",
      "known_gaps": [
        "Missing stored tier stays unknown; public web adapter remains deliberately dark until cutover equivalence."
      ]
    },
    "ritual": {
      "public_name": "kala_ritual_get",
      "public_uri": "marsys://tool/L3/kala_ritual_get",
      "stage_uri": "marsys://tool/L3/ritual_read",
      "module": "platform/src/lib/retrieval/registry/layers/L3_kala/view_ritual.ts",
      "sources": [
        "kala_darshana",
        "kala_obstruction"
      ],
      "tier_select": "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts:266",
      "density_contract": {
        "paginated": true,
        "facets": [
          "event_class",
          "source_table"
        ],
        "empty_reason": true,
        "stored_tier_columns": [
          "kala_darshana.verification_pass_status",
          "kala_obstruction.verification_pass_status"
        ]
      },
      "fidelity_tests": [
        "platform/src/lib/retrieval/registry/layers/L3_kala/views_registry.integration.test.ts",
        "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.test.ts"
      ],
      "narration": "Stored stage data and roots carried verbatim; no verified prose or chart computation inferred.",
      "known_gaps": [
        "Missing stored tier stays unknown; public web adapter remains deliberately dark until cutover equivalence."
      ]
    },
    "explain": {
      "public_name": "kala_explain_get",
      "public_uri": "marsys://tool/L3/kala_explain_get",
      "stage_uri": "marsys://tool/L3/explain_read",
      "module": "platform/src/lib/retrieval/registry/layers/L3_kala/view_explain.ts",
      "sources": [
        "kala_darshana",
        "kala_obstruction",
        "kala_gochara_contacts",
        "kala_bhavishya",
        "kala_convergence",
        "kala_jivana_parva"
      ],
      "tier_select": "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts:266",
      "density_contract": {
        "paginated": true,
        "facets": [
          "event_class",
          "source_table"
        ],
        "empty_reason": true,
        "stored_tier_columns": [
          "kala_darshana.verification_pass_status",
          "kala_obstruction.verification_pass_status",
          "kala_gochara_contacts.verification_pass_status",
          "kala_bhavishya.verification_pass_status",
          "kala_convergence.verification_pass_status",
          "kala_jivana_parva.verification_pass_status"
        ]
      },
      "fidelity_tests": [
        "platform/src/lib/retrieval/registry/layers/L3_kala/views_registry.integration.test.ts",
        "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.test.ts"
      ],
      "narration": "Stored stage data and roots carried verbatim; no verified prose or chart computation inferred.",
      "known_gaps": [
        "Missing stored tier stays unknown; public web adapter remains deliberately dark until cutover equivalence."
      ]
    }
  },
  "hashes": {
    "platform-mcp/src/tools/kala_views/f171_disclosure_receipt_regression.test.ts": "a8d0c071042d0ebc3e2f7ecd19e86a3d60415f163962042120faa35c6f92a0c6",
    "platform-mcp/src/tools/kala_views/priority.ts": "d4c61e746aeddf4f05552b0812d8a753cdc44b0da6b013f80db909eb3b3095cc",
    "platform-mcp/src/tools/register_p1_aliases.ts": "9d2c038d3a5ef27343b7fb322e827a509abc41cc6360ecffbba25e3d37079128",
    "platform/migrations/1377_k7_4_tulana_pareto_health_probe.sql": "b978e1b088631aadad198cc8080576575d06f706d3a8ffb50e36979dbfa39e76",
    "platform/python-sidecar/services/ka_tulana/ranker.py": "b1335f803b18a29e99fd763a851e59a10c579c9d030c86df1541f1a37198f853",
    "platform/python-sidecar/services/ka_tulana/writer.py": "06688590c72dcac9000545f02ba7b49bb85b01c3fd032208a07320e973b1a620",
    "platform/src/lib/retrieval/registry/layers/L3_kala/__tests__/f131_priority_ranking_glossary.test.ts": "75805a1b3c77cde0cf5ff9ab634d8a1befe9d92159d2e3ad9a537f52af917d62",
    "platform/src/lib/retrieval/registry/layers/L3_kala/call_service_wrappers.ts": "73b4ea74e3b3e57ea3a6a1992df6cfa6842301087472f797f147d448e73c8635",
    "platform/src/lib/retrieval/registry/layers/L3_kala/view_ahead.ts": "8b86d0fea6b3a802dab0dbbd40313e660fae360841c34b0561b7718aac515938",
    "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.test.ts": "af171fd981ca01a3f4f6322968499da6a3cf419abff67307db3eed2afcbcf2e3",
    "platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts": "89f21cf3247c95bb1d0dcafcbf2cd8585ce764b545d4d3936fb349b47a8f101e",
    "platform/src/lib/retrieval/registry/layers/L3_kala/view_elect.ts": "33a4c14a7a66b27c6757188bd886d9a114a4c7711e2e085ad90061afc4a95589",
    "platform/src/lib/retrieval/registry/layers/L3_kala/view_explain.ts": "f561265b6c922fac0084f5317ebd3af1851c4b58926563bf948bb4a9c25a3c33",
    "platform/src/lib/retrieval/registry/layers/L3_kala/view_now.ts": "4c8266893b1cd10b5b687b8cfe1344460b23d841ad6bcbf77954c2e63af75bcd",
    "platform/src/lib/retrieval/registry/layers/L3_kala/view_priority.ts": "e593c623cdd70ff65e09f1283264354c7b527d82f743d53b522fa76cd11bb66a",
    "platform/src/lib/retrieval/registry/layers/L3_kala/view_ritual.ts": "602628753eae5b79a8969e507965f8252a6cd4b4d814bae87e6fef83a503096b",
    "platform/src/lib/retrieval/registry/layers/L3_kala/view_story.ts": "c1d75b5a097bc4b315bbad19c2c1059aeba20a65ce8b653736382b4e25fc2c23",
    "platform/src/lib/retrieval/registry/layers/L3_kala/views_registry.integration.test.ts": "e5d4b6992f2bf60035ae75fea5e3fc34b9bb2c8a2ac36dec13fb6b7acb8a03eb"
  },
  "declaration_sha256": "45538005b9d0c2074744f80c1924f64edbf4fb8719f70503332d7c36494ba340",
  "interpretations": [
    "(I) INTERPRETATION I1: POST /api/compute/tulana_compare; validated fixture bindings only, no live jury bridge.",
    "(I) INTERPRETATION I2: DATE window_end is inclusive for relevance; date_to is the half-open horizon end; default H=90 days.",
    "(I) INTERPRETATION I3: This packet-local mapping pins seven view declarations, stored tier SELECT, narration goldens, detector revisions and file hashes; it does not award census PASS.",
    "(I) INTERPRETATION I4: existing field_snapshot_id scopes legacy forecaster windows; mixed snapshots refuse. Future-start windows beyond date_to are excluded; elapsed candidates inside the fetched set are explicitly rejected.",
    "(I) INTERPRETATION I5: the probe freshness declaration uses the conservative 24-hour limit of the current registry rule; Tulana remains a registered writer service, with no cockpit no-writer-probe admission claimed."
  ]
}
''')


def validate_certification_mapping(root: Path, mapping=None) -> list[str]:
    """Offline step verifier: missing/mutated bindings refuse, never invent PASS."""
    mapping = CERTIFICATION_MAPPING if mapping is None else mapping
    errors = []
    required_views = {"now", "ahead", "priority", "elect", "story", "ritual", "explain"}
    view_root = "platform/src/lib/retrieval/registry/layers/L3_kala/"
    required_hashes = {view_root + f"view_{name}.ts" for name in required_views} | {
        view_root + "view_common.ts", view_root + "call_service_wrappers.ts",
        view_root + "view_common.test.ts", view_root + "views_registry.integration.test.ts",
        view_root + "__tests__/f131_priority_ranking_glossary.test.ts",
        "platform-mcp/src/tools/kala_views/priority.ts",
        "platform-mcp/src/tools/kala_views/f171_disclosure_receipt_regression.test.ts",
        "platform-mcp/src/tools/register_p1_aliases.ts",
        "platform/python-sidecar/services/ka_tulana/ranker.py",
        "platform/python-sidecar/services/ka_tulana/writer.py",
        "platform/migrations/1377_k7_4_tulana_pareto_health_probe.sql",
    }
    if not required_hashes <= set(mapping.get("hashes", {})):
        errors.append("missing hash binding for required source/golden evidence")
    if set(mapping.get("views", {})) != required_views:
        errors.append("seven view identities required")
    for name, view in mapping.get("views", {}).items():
        if not view.get("tier_select") or not view.get("fidelity_tests") or not view.get("sources"):
            errors.append(f"missing tier/golden/source binding: {name}")
        if view.get("public_uri") != f"marsys://tool/L3/kala_{name}_get" or view.get("stage_uri") != f"marsys://tool/L3/{name}_read":
            errors.append(f"wrong view URI: {name}")
        density = view.get("density_contract", {})
        if density.get("paginated") is not True or density.get("empty_reason") is not True or density.get("facets") != ["event_class", "source_table"]:
            errors.append(f"density declaration missing/invalid: {name}")
        if view.get("density_contract", {}).get("stored_tier_columns") != [t + ".verification_pass_status" for t in view.get("sources", [])]:
            errors.append(f"tier declaration mismatch: {name}")
        for file in [view.get("module"), *view.get("fidelity_tests", [])]:
            if file not in mapping.get("hashes", {}):
                errors.append(f"unpinned view evidence: {file}")
    for file, expected in mapping.get("hashes", {}).items():
        path = root / file
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"stale/missing evidence: {file}")
    if not mapping.get("hashes"):
        errors.append("hash bindings required")
    try:
        declarations = json.loads((root / "platform/scripts/governance/asset_declarations.json").read_text())
        entry = declarations["assets"]["ka_tulana"]
        digest = hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if digest != mapping.get("declaration_sha256"):
            errors.append("stale ka_tulana declaration")
        tree = ast.parse((root / mapping["registry_path"]).read_text())
        revision = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "REGISTRY_REVISION" for t in n.targets))
        if revision != mapping.get("registry_revision"):
            errors.append("stale detector registry revision")
        registry = next(n.value for n in tree.body if isinstance(n, ast.AnnAssign)
                        and isinstance(n.target, ast.Name) and n.target.id == "CRITERION_REGISTRY")
        criteria = {ast.literal_eval(k): {x.arg: ast.literal_eval(x.value) for x in v.keywords
                    if x.arg in {"revision", "detector"}} for k, v in zip(registry.keys, registry.values)}
        if set(mapping.get("detectors", {})) != set(CERTIFICATION_MAPPING["detectors"]):
            errors.append("missing detector binding")
        for key, evidence in mapping.get("detectors", {}).items():
            criterion = criteria.get(key, {})
            if any(evidence.get(field) != criterion.get(field) for field in ("revision", "detector")):
                errors.append(f"stale detector: {key}")
            expected = "NO_DETECTOR" if criterion.get("detector") == "NONE" else "UNMEASURED"
            if evidence.get("verdict") != expected:
                errors.append(f"unearned verdict: {key}")
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        errors.append(f"mapping source unavailable: {exc}")
    return errors
