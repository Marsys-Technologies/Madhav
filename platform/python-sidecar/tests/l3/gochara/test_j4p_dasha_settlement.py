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
BUILD = "7377833e-5d3b-4e70-8bef-1318904f470e"
UNKNOWN = "22222222-2222-4222-8222-222222222222"  # negative fixture only
COLLISION = "7377833e-2222-4222-8222-222222222222"  # negative prefix collision
LO, HI = (datetime(2026, 1, day, tzinfo=timezone.utc) for day in (1, 9))
# Suvarṇa's attestation, copied byte-exactly from origin/campaign-coordination at POSTED_COMMIT
# (00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md, "2026-10-17T05:41:43Z — SUVARṆA (Exec) → KĀLA-YANTRA: L1_SETTLED v1").
POSTED_COMMIT = "5a8a80ebfc0fc6135020f24d82ff9ed43ab14d73"
POSTED_LINE = ("L1_SETTLED v1 utc=2026-10-17T05:41:43Z pos_build=7377833e dash_build=7377833e "
               "natal_fp=3c034bdf vim13_fp=ee2e8bc7 vim13_rows=1040 dash_all_fp=ea7611f7")
RECEIPT = {
    "schema": "gochara_dasha_settlement/1",
    "header_comment": "Governed settlement record. Changes require a reviewed PR.",
    "line": POSTED_LINE,
    "utc": "2026-10-17T05:41:43Z", "pos_build": "7377833e", "dash_build": "7377833e",
    "natal_fp": "3c034bdf", "vim13_fp": "ee2e8bc7", "vim13_rows": 1040,
    "dash_all_fp": "ea7611f7", "run_id": BUILD, "chart_id": CHART,
    "provenance": {
        "source": "origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md",
        "commit": POSTED_COMMIT, "heading": "L1_SETTLED v1",
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
            self.result = [(0,)]                    # a snapshot with no copy columns: the verifier's legacy (ids-only) path
        elif "search_input_snapshot" in sql:
            ids = [row(BUILD)["dasha_row_id"]]
            self.result = [([], ids)] if "consumed_fact_ids" in sql else [(ids,)]
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
    ("utc", "2026-02-30T05:41:43Z"),
    ("dash_build", "22222222"), ("run_id", UNKNOWN), ("run_id", "7377833e-bad"),
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


def test_governed_record_is_exactly_suvarnas_posted_line():
    """The committed record binds the posted L1_SETTLED v1 line and nothing else (copied, never synthesised)."""
    record = json.loads(reader.SETTLEMENT_PATH.read_text(encoding="utf-8"))
    assert record["line"] == POSTED_LINE
    assert record["provenance"]["commit"] == POSTED_COMMIT
    assert (record["run_id"], record["provenance"]["rebuild_run"], record["chart_id"]) == (
        "7377833e-5d3b-4e70-8bef-1318904f470e", "7377833e-5d3b-4e70-8bef-1318904f470e", CHART)
    assert (record["utc"], record["pos_build"], record["dash_build"], record["natal_fp"], record["vim13_fp"],
            record["vim13_rows"], record["dash_all_fp"]) == (
        "2026-10-17T05:41:43Z", "7377833e", "7377833e", "3c034bdf", "ee2e8bc7", 1040, "ea7611f7")
    assert reader.load_dasha_settlement(CHART) == record


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
    record["line"] = record["line"].replace("2026-10-17", "2026-02-30")
    record["utc"] = "2026-02-30T05:41:43Z"
    settlement.write_text(json.dumps(record))
    refused(invoke, "settlement_malformed")


def test_reviewed_successor_requires_only_a_consistent_receipt(settlement, invoke):
    # Synthetic reviewed-repin fixture; this asserts no future L1 computation.
    record = copy.deepcopy(RECEIPT)
    record["line"] = record["line"].replace("dash_build=7377833e", "dash_build=22222222")
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


# P01-B1: exercise the lazy P1 operand and the actual writer snapshot branch.
# Replacing the governed selector with builds[0] must fail both regressions.
@pytest.mark.parametrize("build", [UNKNOWN, COLLISION])
def test_p01_lazy_p1_operand_refuses_ungoverned_sole_build(settlement, monkeypatch, build):
    conn = Conn([build])
    calls = []
    def fetch(c, chart_id, **kw):
        calls.append(kw)
        return [row(build)]
    monkeypatch.setattr(reader, "_fetch_dasha_periods_multilevel", fetch)
    rows_for, contract = reader.make_period_rows_for(conn, CHART)
    with pytest.raises(reader.DashaBuildRefused, match="settled_build_absent"):
        rows_for("Saturn", "md")
    assert contract["read"] is False and contract["build_id"] is None
    assert len(calls) == 1 and calls[0]["canonicalize"] is False


def test_p01_lazy_p1_operand_uses_full_settled_build_once(settlement, monkeypatch):
    conn = Conn([BUILD])
    pins = []
    def fetch(c, chart_id, **kw):
        pins.append(kw.get("build_id"))
        return [row(BUILD)]
    monkeypatch.setattr(reader, "_fetch_dasha_periods_multilevel", fetch)
    rows_for, contract = reader.make_period_rows_for(conn, CHART)
    assert rows_for("Saturn", "md") == [{"start_iso": LO, "end_iso": HI}]
    assert rows_for("Saturn", "ad") == []
    assert contract["build_id"] == BUILD and contract["read"] is True
    assert pins == [None, BUILD]


def test_p01_snapshot_refuses_unknown_build_before_generation_delete(settlement, monkeypatch):
    from types import SimpleNamespace
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer
    from pipeline.orchestrator.writers import SubStep
    conn = Conn([UNKNOWN])
    monkeypatch.setattr(reader, "_fetch_dasha_periods_multilevel", lambda *a, **kw: [row(UNKNOWN)])
    monkeypatch.setattr(writer, "fetch_chart_context", lambda *a: {})
    monkeypatch.setattr(writer, "require_complete", lambda *a: None)
    monkeypatch.setattr(writer.SkyEventStore, "register_convention", lambda self: "synthetic-convention")
    def forbidden(*a, **kw):
        pytest.fail("ungoverned daśā build reached generation deletion")
    monkeypatch.setattr(writer.RecordStore, "delete_generation_chain", forbidden)
    ctx = SimpleNamespace(db_conn=conn, config={})
    with pytest.raises(reader.DashaBuildRefused, match="settled_build_absent"):
        writer.GocharaV5Writer()._run_inventory_phase(ctx, SubStep(key=writer.SNAPSHOT_SUBSTEP), CHART)
