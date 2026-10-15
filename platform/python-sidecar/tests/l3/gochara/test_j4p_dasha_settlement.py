"""J4P-B1: row presence cannot authorize a daśā build. Only SQL is faked.

Skipping the settlement load/reparse or selecting builds[0] must break these tests.
The verifier executes its own SQL and loader; the reader loader is forbidden there.
"""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from services.gochara_grammar import dasha_data as DD
from services.gochara_kernel import dasha_read as reader, inventory_verifier as verifier

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
BUILD = "ca17639b-f3cf-42c7-9866-0a61f3855802"
UNKNOWN = "22222222-2222-4222-8222-222222222222"  # negative fixture only
COLLISION = "ca17639b-2222-4222-8222-222222222222"  # negative prefix collision
LO, HI = (datetime(2026, 1, day, tzinfo=timezone.utc) for day in (1, 9))
RECEIPT = {
    "schema": "gochara_dasha_settlement/1",
    "header_comment": "Governed settlement record. Changes require a reviewed PR.",
    "line": "L1_SETTLED v1 utc=2026-10-07T22:18:24Z pos_build=ca17639b dash_build=ca17639b natal_fp=7e4278be vim13_fp=ee2e8bc7 vim13_rows=1040 dash_all_fp=ea7611f7",
    "utc": "2026-10-07T22:18:24Z", "pos_build": "ca17639b", "dash_build": "ca17639b",
    "natal_fp": "7e4278be", "vim13_fp": "ee2e8bc7", "vim13_rows": 1040,
    "dash_all_fp": "ea7611f7", "run_id": BUILD, "chart_id": CHART,
    "provenance": {
        "source": "origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md",
        "commit": "2051951aaa3f4e1b6a55d728f703bc074daf11ef", "heading": "L1_SETTLED v1",
        "release_receipt": "SUVARNA-L0L2-CLOSE-REV30-20261013", "rebuild_run": BUILD,
    },
}


def row(build):
    return {"dasha_row_id": "11111111-1111-4111-8111-111111111111", "level_n": 1,
            "parent_row_id": None, "lord_graha": "Saturn", "start_iso": LO, "end_iso": HI,
            "build_id": build, "system_id": "vimshottari", "ayanamsha_id": "lahiri_chitrapaksha",
            "verification_pass_status": "two_pass_verified"}


class Conn:
    def __init__(self, builds, tier="two_pass_verified"):
        self.builds, self.tier, self.pins = builds, tier, []

    def execute(self, sql, params=()):
        if "information_schema.columns" in sql:
            self.result = [(0,)]  # This settlement fixture models a legacy (ids-only) snapshot.
        elif "SELECT consumed_fact_ids, consumed_dasha_row_ids" in sql:
            self.result = [([], [row(BUILD)["dasha_row_id"]])]
        elif "search_input_snapshot" in sql:
            self.result = [([row(BUILD)["dasha_row_id"]],)]
        elif "search_inventory" in sql:
            self.result = [(LO, HI)]
        elif "SELECT DISTINCT" in sql:
            eligible = "verification_pass_status" in sql
            self.result = [(b,) for b in self.builds
                           if not eligible or self.tier == "two_pass_verified"]
        else:
            assert "chart_dashas" in sql
            if "dasha_row_id = ANY" in sql:
                selected = self.builds
            else:
                self.pins.append(params[-1])
                selected = [b for b in self.builds if b == params[-1] and self.tier == "two_pass_verified"]
            names = ("dasha_row_id", "level_n", "parent_row_id", "lord_graha", "start_iso", "end_iso",
                     "build_id", "system_id", "ayanamsha_id", "verification_pass_status")
            self.result = [tuple(row(b)[key] for key in names) for b in selected]
        return self

    def fetchall(self):
        return self.result

    def fetchone(self):
        return self.result[0] if self.result else None


@pytest.fixture
def settlement(tmp_path, monkeypatch):
    path = tmp_path / "settlement.json"
    path.write_text(json.dumps(RECEIPT))
    monkeypatch.setattr(reader, "SETTLEMENT_PATH", path, raising=False)
    monkeypatch.setattr(verifier, "_SETTLEMENT_PATH", path, raising=False)
    return path


@pytest.fixture(params=["reader", "verifier"])
def invoke(request, monkeypatch):
    def run(builds=(BUILD,), chart=CHART, tier="two_pass_verified"):
        conn = Conn(list(builds), tier)
        if request.param == "reader":
            def fetch(c, chart_id, systems=None, canonicalize=True, build_id=None, **kw):
                if build_id is not None:
                    conn.pins.append(build_id)
                return [row(b) for b in builds if tier == "two_pass_verified"
                        and (build_id is None or b == build_id)]
            monkeypatch.setattr(reader, "_fetch_dasha_periods_multilevel", fetch)
            rows, contract = reader.load_pinned_vimshottari(conn, chart)
            return contract["build_id"], conn.pins
        def forbidden(*args, **kwargs):
            raise AssertionError("verifier called the reader settlement loader")
        monkeypatch.setattr(reader, "load_dasha_settlement", forbidden, raising=False)
        monkeypatch.setattr(reader, "select_dasha_read_contract", forbidden)
        verifier.validate_consumed_dasha_population(conn, chart_id=chart, generation="5.0")
        return conn.pins[-1], conn.pins
    run.error = reader.DashaBuildRefused if request.param == "reader" else verifier.Unverifiable
    return run


def refused(invoke, code, **kw):
    with pytest.raises(invoke.error, match=code) as caught:
        invoke(**kw)
    assert caught.value.code == code


def test_named_settlement_pins_exact_build(settlement, invoke):
    build, pins = invoke()
    assert build == BUILD and pins == [BUILD]


def test_missing_settlement_refuses_populated_build(settlement, invoke):
    settlement.unlink()
    refused(invoke, "settlement_missing")


def test_unreadable_settlement_refuses_populated_build(settlement, invoke, monkeypatch):
    real = Path.read_text
    def read(path, *a, **kw):
        if path == settlement:
            raise PermissionError("test unreadable receipt")
        return real(path, *a, **kw)
    monkeypatch.setattr(Path, "read_text", read)
    refused(invoke, "settlement_missing")


@pytest.mark.parametrize("payload", ["{", "[]", "null"])
def test_invalid_json_shape_refuses(settlement, invoke, payload):
    settlement.write_text(payload)
    refused(invoke, "settlement_malformed")


@pytest.mark.parametrize("field, value", [
    ("line", RECEIPT["line"].replace("vim13_fp=ee2e8bc7", "vim13_fp=ffffffff")),
    ("line", RECEIPT["line"] + " unknown=1"),
    ("utc", "2026-02-30T22:18:24Z"),
    ("dash_build", "22222222"), ("run_id", UNKNOWN), ("run_id", "ca17639b-bad"),
    ("chart_id", "bad"), ("vim13_rows", "1040"), ("vim13_rows", True),
    ("schema", "unknown"), ("provenance", {}), ("header_comment", ""),
])
def test_tampered_record_refuses(settlement, invoke, field, value):
    record = copy.deepcopy(RECEIPT)
    record[field] = value
    settlement.write_text(json.dumps(record))
    refused(invoke, "settlement_malformed")


@pytest.mark.parametrize("field", ["line", "dash_build", "run_id", "chart_id", "provenance"])
def test_missing_required_field_refuses(settlement, invoke, field):
    record = copy.deepcopy(RECEIPT)
    del record[field]
    settlement.write_text(json.dumps(record))
    refused(invoke, "settlement_malformed")


@pytest.mark.parametrize("builds, tier", [([], "two_pass_verified"), ([UNKNOWN], "two_pass_verified"),
                                         ([COLLISION], "two_pass_verified"), ([BUILD], "single")])
def test_settled_build_absent_refuses_without_fallback(settlement, invoke, builds, tier):
    refused(invoke, "settled_build_absent", builds=builds, tier=tier)


@pytest.mark.parametrize("builds", [[BUILD, UNKNOWN], [UNKNOWN, BUILD], [BUILD, COLLISION]])
def test_more_than_one_candidate_refuses(settlement, invoke, builds):
    refused(invoke, "settled_build_ambiguous", builds=builds)


def test_unnamed_chart_refuses_even_with_named_build(settlement, invoke):
    refused(invoke, "chart_not_settled", chart="11111111-1111-4111-8111-111111111111")


def test_reviewed_record_loads_through_both_independent_paths():
    assert reader.load_dasha_settlement(CHART)["run_id"] == BUILD
    assert verifier._load_dasha_settlement(CHART)["run_id"] == BUILD


@pytest.mark.parametrize("field", ["pos_build", "natal_fp", "vim13_fp", "dash_all_fp"])
def test_each_fingerprint_field_must_match_the_line(settlement, invoke, field):
    record = copy.deepcopy(RECEIPT)
    record[field] = "ffffffff"
    settlement.write_text(json.dumps(record))
    refused(invoke, "settlement_malformed")


def test_invalid_encoding_is_a_typed_refusal(settlement, invoke):
    settlement.write_bytes(b"\xff")
    refused(invoke, "settlement_malformed")


def test_coherent_but_invalid_date_is_a_typed_refusal(settlement, invoke):
    record = copy.deepcopy(RECEIPT)
    record["line"] = record["line"].replace("2026-10-07", "2026-02-30")
    record["utc"] = "2026-02-30T22:18:24Z"
    settlement.write_text(json.dumps(record))
    refused(invoke, "settlement_malformed")


def test_reviewed_successor_requires_only_a_consistent_receipt(settlement, invoke):
    # Synthetic reviewed-repin fixture; this asserts no future L1 computation.
    record = copy.deepcopy(RECEIPT)
    record["line"] = record["line"].replace("dash_build=ca17639b", "dash_build=22222222")
    record["dash_build"] = "22222222"
    record["run_id"] = UNKNOWN
    record["provenance"]["rebuild_run"] = UNKNOWN
    settlement.write_text(json.dumps(record))
    build, pins = invoke(builds=[UNKNOWN])
    assert build == UNKNOWN and pins == [UNKNOWN]


@pytest.mark.parametrize("path", ["reader", "verifier"])
def test_settlement_bytes_are_bound_to_the_implementation_digest(monkeypatch, path):
    from services.gochara_kernel import input_vector as iv, input_vector_verifier as ivv
    digest = iv.implementation_digests if path == "reader" else ivv.module_digests
    modules = {"evaluation": ("services.gochara_kernel.dasha_read",)}
    before = digest(modules)
    read = Path.read_text
    def altered(p, *a, **kw):
        content = read(p, *a, **kw)
        return content + " " if p.name == "dasha_settlement.json" else content
    monkeypatch.setattr(Path, "read_text", altered)
    assert digest(modules) != before, "unreviewed settlement edit escaped implementation identity"
