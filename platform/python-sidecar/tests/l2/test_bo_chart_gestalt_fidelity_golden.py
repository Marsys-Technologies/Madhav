"""Golden-value narration fidelity test for bo_chart_gestalt.

bo_chart_gestalt stores pointers plus a handful of strings it composes or fixes in code:
constant `note` sentences in nine jsonb columns, a per-domain constant `verdict_note`, and
two graded labels (`linking_mechanism`, computed from the domain overlap of the two poles,
and `fragility_class`, computed from a cross-ayanamsha comparison). The DB boundary
(`_fetch_dict`) is replaced with an in-memory router so the REAL `_write_aya`,
`_assess_fragility` and `_patch_fragility` run on FIXED rows; every expected sentence and
label below is stated by hand from the writer's own templates and rules (module docstring
and the `note` strings in bo_chart_gestalt.py), never read back from the builder.
"""
from __future__ import annotations

import json

from pipeline.orchestrator.writers import bo_chart_gestalt as W


class _Cursor:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if isinstance(params, dict) and "gestalt_id" in params:
            self._conn.inserted.append(params)
        elif isinstance(params, list) and params and "headline_epistemic_jsonb" in sql:
            self._conn.updated.append(params)
        else:
            self._conn.other.append((sql, params))


class _FakeConn:
    def __init__(self):
        self.inserted = []
        self.updated = []
        self.other = []

    def cursor(self):
        return _Cursor(self)


_TOP = [
    {"signal_id": "sig-a", "signal_type_id": "yoga_alpha", "signal_type_class": "yoga",
     "computed_salience": 8.0, "signature_tier": "chart_defining", "valence": "benefic",
     "source_l1_asset": "ga_yoga", "domains_affected_array": ["career"], "constituent_facts_array": []},
    {"signal_id": "sig-b", "signal_type_id": "dosha_beta", "signal_type_class": "dosha",
     "computed_salience": 6.0, "signature_tier": "major", "valence": "malefic",
     "source_l1_asset": "ga_dosha", "domains_affected_array": ["health"], "constituent_facts_array": []},
]
_DOMAIN_SIGNALS = [
    {"unnested_domain": "career", "signal_id": "sig-a", "computed_salience": 8.0,
     "valence": "benefic", "signature_tier": "chart_defining"},
    {"unnested_domain": "wealth", "signal_id": "sig-w", "computed_salience": 2.0,
     "valence": "malefic", "signature_tier": "minor"},
]
_EVIDENCE = [
    {"domain": "career", "signal_count": 10, "benefic_count": 6, "malefic_count": 4,
     "mixed_count": 0, "neutral_count": 0, "major_tier_count": 3},
    {"domain": "wealth", "signal_count": 3, "benefic_count": 0, "malefic_count": 3,
     "mixed_count": 0, "neutral_count": 0, "major_tier_count": 0},
]
_MALEFIC = [
    {"signal_id": "sig-m", "signal_type_id": "dosha_gamma", "computed_salience": 5.0,
     "domains_affected_array": ["career"]},
]
_BENEFIC = [
    {"signal_id": "sig-a", "signal_type_id": "yoga_alpha", "domains_affected_array": ["career", "health"]},
]
_CONTESTED = [{"domain": "career", "benefic_count": 6, "malefic_count": 4}]


def _router(conn, sql, params):
    if "FROM bodha_cdlm_cells" in sql:
        return [{"cell_id": "cell-1", "domain_row": "career", "domain_col": "wealth",
                 "computed_linkage_strength": 0.9}]
    if "FROM bodha_cgm_nodes" in sql:
        return [{"node_id": "node-1", "node_subject": "Jupiter", "pagerank_score": 0.3, "hub_flag": True}]
    if "FROM bodha_cgm_paths" in sql:
        return [{"to_node_id": "node-2"}]
    if "FROM bodha_discoveries" in sql:
        return [{"discovery_id": "disc-1", "discovery_class": "embedding_outlier",
                 "non_obviousness_score": 0.7, "constituent_refs_jsonb": {}}]
    if "signature_tier IN ('chart_defining', 'major')" in sql:
        return list(_TOP)
    if "DISTINCT ON (unnested_domain)" in sql:
        return list(_DOMAIN_SIGNALS)
    if "HAVING" in sql:
        return list(_CONTESTED)
    if "AS signal_count" in sql:
        return list(_EVIDENCE)
    if "AND valence = 'malefic'" in sql:
        return list(_MALEFIC)
    if "AND valence = 'benefic'" in sql:
        return list(_BENEFIC)
    raise AssertionError("unexpected query: " + sql[:80])


def test_gestalt_notes_and_labels_golden(monkeypatch):
    monkeypatch.setattr(W, "_fetch_dict", _router)
    conn = _FakeConn()

    written = W._write_aya(conn, "chart-1", "lahiri_chitrapaksha", "build-1", "2026-10-05T00:00:00+00:00")
    assert written == 1

    row = conn.inserted[0]
    defining_threads = json.loads(row["defining_threads_jsonb"])
    domain_verdict_map = json.loads(row["domain_verdict_map_jsonb"])
    headline = json.loads(row["headline_jsonb"])
    watch_list = json.loads(row["watch_list_jsonb"])
    central_question = json.loads(row["central_question_jsonb"])
    outliers = json.loads(row["outliers_jsonb"])
    contested_areas = json.loads(row["contested_areas_jsonb"])
    zoom_spine = json.loads(row["zoom_spine_jsonb"])
    headline_epistemic = json.loads(row["headline_epistemic_jsonb"])

    assert defining_threads == {
        "signal_ids": ["sig-a", "sig-b"],
        "tiers": ["chart_defining", "major"],
        "note": "pointer-only — follow signal_id to bodha_msr_signals for content",
    }

    assert domain_verdict_map["career"] == {
        "signal_id": "sig-a",
        "evidence": {
            "signal_count": 10, "benefic_count": 6, "malefic_count": 4, "mixed_count": 0,
            "neutral_count": 0, "major_tier_count": 3, "top_signal_valence": "benefic",
            "top_signal_signature_tier": "chart_defining", "top_signal_salience": 8.0,
        },
        "verdict_note": (
            "no verdict stored — this writer carries pointers and deterministic evidence only "
            "(docstring ANTI-DRIFT ABSOLUTE; migration 325 col comment). A verdict must be "
            "computed by the consuming layer from `evidence`, which is whole-domain, not the "
            "top signal alone."
        ),
    }
    assert domain_verdict_map["wealth"]["verdict_note"] == (
        "no verdict stored — this writer carries pointers and deterministic evidence only "
        "(docstring ANTI-DRIFT ABSOLUTE; migration 325 col comment). A verdict must be "
        "computed by the consuming layer from `evidence`, which is whole-domain, not the "
        "top signal alone."
    )

    assert headline == {
        "top_signal_id": "sig-a",
        "top_signal_type": "yoga_alpha",
        "strongest_domain": "career",
        "note": (
            "pointer-only — no verdict text stored here. strongest_domain is ranked by "
            "evidence.top_signal_salience (descending), not by insertion/alphabetical order."
        ),
    }

    assert watch_list == {
        "malefic_signal_ids": ["sig-m"],
        "weakest_domain": "wealth",
        "weakest_domain_signal_id": "sig-w",
        "note": (
            "pointer-only — follow signal_ids for content. weakest_domain is ranked by "
            "evidence.top_signal_salience (ascending), not by insertion/alphabetical order."
        ),
    }

    assert central_question == {
        "positive_pole_signal_id": "sig-a",
        "negative_pole_signal_id": "sig-m",
        "linking_mechanism": "domain_tension",
        "linking_mechanism_terms": {"shared_domains": ["career"]},
        "note": "pointer-only — antagonistic axis; follow signal_ids for content",
    }
    # the poles share the domain "career", so the graded label names a same-domain tension
    assert central_question["linking_mechanism"] == "domain_tension"

    assert outliers == {
        "discovery_ids": ["disc-1"],
        "note": "pointer-only — non-template-significant outliers from bo_anveshana",
    }

    assert contested_areas == {
        "contested_domains": [
            {"domain": "career", "benefic_count": 6, "malefic_count": 4,
             "balance_ratio": 0.6667, "genuinely_balanced": False},
        ],
        "balance_ratio_threshold": 0.67,
        "note": (
            "domains where BOTH benefic and malefic evidence exist (contested). Contested is "
            "NOT the same as balanced — see per-domain balance_ratio / genuinely_balanced "
            "(ratio >= 0.67 required); a lopsided domain (e.g. 136 vs 632, ratio 0.215) is "
            "contested but not genuinely balanced."
        ),
    }

    assert zoom_spine == {
        "gestalt_signal_ids": ["sig-a", "sig-b"],
        "domain_entry_points": {"career": "sig-a", "wealth": "sig-w"},
        "cgm_hub_node_ids": ["node-1", "node-2"],
        "note": "zoom spine: gestalt → domain signal ids → CGM hubs → L1 facts via constituent_facts_array",
    }

    assert headline_epistemic == {
        "ayanamsha_count": 5,
        "fragility_class": None,
        "note": (
            "fragility_class is None here by construction — a single ayanamsha's write cannot "
            "compare across ayanamshas. It is patched to a real value once all ayanamsha rows "
            "for this build exist; see run()'s post-loop _assess_fragility() pass."
        ),
    }


def _frag_router(rows_by_aya):
    def route(conn, sql, params):
        if "SELECT ayanamsha_id, domain_verdict_map_jsonb" in sql:
            return [
                {"ayanamsha_id": aya,
                 "domain_verdict_map_jsonb": {"career": {"evidence": {"benefic_count": b, "malefic_count": m}}}}
                for aya, (b, m) in rows_by_aya.items()
            ]
        if "SELECT gestalt_id, headline_epistemic_jsonb" in sql:
            return [{"gestalt_id": "g-1", "headline_epistemic_jsonb": json.dumps(
                {"ayanamsha_count": 5, "fragility_class": None, "note": "placeholder from write"})}]
        raise AssertionError("unexpected query: " + sql[:80])
    return route


def test_gestalt_fragility_class_golden(monkeypatch):
    # lahiri leans benefic (6 > 4) while raman leans malefic (2 < 5): the one comparable
    # domain disagrees, so the cross-ayanamsha reading is ayanamsha-sensitive.
    monkeypatch.setattr(W, "_fetch_dict", _frag_router({"lahiri_chitrapaksha": (6, 4), "raman": (2, 5)}))
    conn = _FakeConn()

    result = W._assess_fragility(conn, "chart-1", "build-1")
    assert result["fragility_class"] == "ayanamsha_sensitive"
    assert result["terms"] == {
        "ayanamsha_rows_compared": 2,
        "domains_compared": ["career"],
        "domains_disagreeing": ["career"],
    }

    W._patch_fragility(conn, "chart-1", "build-1", result)
    patched = json.loads(conn.updated[0][0])
    assert patched["fragility_class"] == "ayanamsha_sensitive"

    # both rows lean benefic: every comparable domain agrees
    monkeypatch.setattr(W, "_fetch_dict", _frag_router({"lahiri_chitrapaksha": (6, 4), "raman": (7, 3)}))
    stable = W._assess_fragility(conn, "chart-1", "build-1")
    assert stable["fragility_class"] == "stable_across_ayanamsha"
