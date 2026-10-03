"""test_e5_7_fingerprint_declarations.py -- E5.7: `00_ARCHITECTURE/control/FINGERPRINT_DECLARATIONS.json` and its loader/validator
(`fingerprint_declarations.py`), tests-first and mutation-checked.

No production database, credential or network is touched. The mirror dump (`prod_schema.sql`, schema only) is read as TEXT when it is
present on the machine; the committed schema extract (derived from it) makes the same checks run in CI. PostgreSQL appears ONLY through the
repo's disposable fixture.

Layout
  1. the committed file          valid against the registry snapshot, the schema extract and the writer files; 40 assets, every one
                                 declared or listed undeclared with a reason; ONE fingerprint definition
  2. the mirror dump             every declared table is `CREATE TABLE public.<name>` in the dump; every excluded column is in that
                                 table's body; the committed extract equals one regenerated from the dump
  3. refusals                    one mutation per refusal (the validator must name it)
  4. conversion + composition    each declared table is a valid E5.5 declaration; the asset fingerprint composition
  5. real SQL                    on the disposable cluster: the asset fingerprint equals E5.5's `table_fingerprint`, ignores exactly the
                                 declared volatile columns, moves on a semantic change; undeclared assets are refused
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys
import types

import pytest

HERE = pathlib.Path(__file__).resolve().parent
GOV = HERE.parent
REPO = GOV.parents[2]
sys.path.insert(0, str(GOV))
sys.path.insert(0, str(HERE))

import fingerprint_declarations as fd  # noqa: E402
import nikasha_stale_certs as nsc  # noqa: E402
import suvarna_rehearsal as sr  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401

MIRROR_DUMP = pathlib.Path("/Users/Dev/suvarna-evidence/S_L1/rehearsal_final/seed/prod_schema.sql")
needs_dump = pytest.mark.skipif(not MIRROR_DUMP.is_file(), reason="the mirror recipe dump is not on this machine (the committed extract covers CI)")

DOC = json.loads(fd.DEFAULT_DECLARATIONS.read_text(encoding="utf-8"))
REG = fd.load_registry()
EXT = fd.load_schema_extract()


def problems(doc, *, registry=REG, schema=EXT, repo_root=REPO):
    return fd.validate(doc, registry=registry, schema=schema, repo_root=repo_root)


def codes(doc, **kw):
    return sorted({c for c, _p, _m in problems(doc, **kw)})


def mut(fn, doc=None):
    d = copy.deepcopy(DOC if doc is None else doc)
    fn(d)
    return d


def first_declared(pred=lambda a, d: True):
    for a, d in DOC["assets"].items():
        if d["status"] == "declared" and pred(a, d):
            return a
    raise AssertionError("no declared asset matches")


# ═════════════════════════ 1. the committed file ═════════════════════════

def test_the_committed_declarations_are_valid():
    assert problems(DOC) == []
    d = fd.load_declarations()
    assert d.sha256 == fd.sha256_file(fd.DEFAULT_DECLARATIONS) and len(d.sha256) == 64


def test_every_active_l0_asset_is_declared_or_listed_undeclared_exactly_once():
    assert len(REG) == 40 and set(DOC["assets"]) == set(REG)
    d = fd.load_declarations()
    assert sorted(d.declared_assets() + list(d.undeclared_assets())) == sorted(REG)
    assert d.expected_assets() == d.declared_assets()
    assert not set(d.expected_assets()) & set(d.undeclared_assets())
    assert 20 <= len(d.declared_assets()) <= 36                # an honest split, neither "everything" nor "nothing"
    for a, u in d.undeclared_assets().items():
        assert u["reason_code"] in fd.UNDECLARED_CODES and len(u["reason"]) >= fd.MIN_UNDECLARED_REASON_CHARS, a


def test_the_known_undeclared_assets_and_their_reasons():
    un = fd.load_declarations().undeclared_assets()
    assert {a: u["reason_code"] for a, u in un.items()} == {
        "bg_class_lifetime_counts": "shared_table", "bg_class_priors": "shared_table", "bg_ontology": "shared_table",
        "bg_texts": "shared_table", "bg_text_index": "shared_table", "bg_compendium_index": "no_plain_natural_key",
        "bg_ephemeris_engine": "no_table", "bg_panchanga": "no_table", "bg_gochara_citation_resolution": "migration_owned_rows",
        "bg_sarvatobhadra_grid": "migration_owned_rows", "bg_transit_rules": "migration_owned_rows", "bg_rules": "second_writer_unprobed"}


def test_partial_assets_name_the_tables_they_do_not_cover():
    p = fd.load_declarations().partial_assets()
    assert sorted(p) == ["bg_dasha_systems", "bg_doshas", "bg_remedies", "bg_yogas"]
    assert {n["name"] for a in ("bg_dasha_systems", "bg_doshas", "bg_yogas") for n in p[a]} == {"brahma_ontology"}
    assert [n["name"] for n in p["bg_remedies"]] == ["remedy_review_queue"]


def test_one_fingerprint_definition_everywhere():
    assert fd.FINGERPRINT_DEFINITION == sr.FINGERPRINT_DEFINITION == "nikasha_stale_certs.table_fingerprint/1"
    assert DOC["fingerprint_definition"] == fd.FINGERPRINT_DEFINITION
    assert all(d["fingerprint_definition"] == fd.FINGERPRINT_DEFINITION for d in DOC["assets"].values() if d["status"] == "declared")
    src = (GOV / "fingerprint_declarations.py").read_text(encoding="utf-8")
    assert "def fingerprint_rows" not in src and "def table_fingerprint" not in src       # the module defines no fingerprint of its own


def test_reproducibility_flags_are_the_known_ones():
    d = fd.load_declarations()
    assert d.coverage_report()["reproducibility"] == {"bg_cohort": ["platform_bound"], "bg_muhurta_lattice": ["rolling_horizon"],
                                                       "bg_sky_calendar": ["rolling_horizon", "platform_bound"]}


def test_the_declarations_file_is_stable_json_with_no_duplicate_keys():
    text = fd.DEFAULT_DECLARATIONS.read_text(encoding="utf-8")
    assert fd.strict_loads(text) == DOC and text.endswith("\n")


# ═════════════════════════ 2. the mirror dump ═════════════════════════

def _declared_tables():
    out = []
    for a, d in DOC["assets"].items():
        if d["status"] == "declared":
            out += [(a, t) for t in d["tables"]]
    return out


def test_every_declared_table_and_excluded_column_exists_in_the_committed_extract():
    for a, t in _declared_tables():
        tab = EXT["tables"].get(t["name"])
        assert tab is not None, (a, t["name"])
        for e in t["exclude"]:
            assert e["column"] in tab["columns"], (a, t["name"], e["column"])
        for c in t["key"]:
            assert c in tab["columns"]


@needs_dump
def test_every_declared_table_exists_in_the_mirror_dump_and_every_excluded_column_is_in_its_body():
    text = MIRROR_DUMP.read_text(encoding="utf-8")
    for a, t in _declared_tables():
        assert re.search(rf"^CREATE TABLE public\.{re.escape(t['name'])} \(", text, re.M), (a, t["name"])
        body = fd.dump_table_body(text, t["name"])
        assert body is not None
        for e in t["exclude"]:
            assert re.search(rf'^\s+"?{re.escape(e["column"])}"? ', body, re.M), (a, t["name"], e["column"])
        for c in t["key"] + t["naive_utc_columns"]:
            assert re.search(rf'^\s+"?{re.escape(c)}"? ', body, re.M), (a, t["name"], c)
    for a, d in DOC["assets"].items():
        for n in d.get("not_covered_tables", []):
            assert fd.dump_table_body(text, n["name"]) is not None
        for n in d.get("tables_written", []):
            assert fd.dump_table_body(text, n) is not None


@needs_dump
def test_the_committed_schema_extract_is_exactly_what_the_dump_yields():
    text = MIRROR_DUMP.read_text(encoding="utf-8")
    again = fd.extract_schema(text, sorted(fd.tables_named(DOC)), dump_name="prod_schema.sql")
    assert again == EXT
    assert DOC["source"]["schema_dump_sha256"] == EXT["source"]["sha256"] == fd.sha256_bytes(text.encode("utf-8"))


@needs_dump
def test_the_mirror_dump_is_schema_only():
    """Schema only: no COPY data block and no column-0 INSERT (the INSERT text in it sits inside function bodies)."""
    lines = MIRROR_DUMP.read_text(encoding="utf-8").split("\n")
    assert not [i for i, ln in enumerate(lines, 1) if ln.startswith("COPY ") or ln.startswith("INSERT INTO ")]


def test_registry_snapshot_hash_in_the_declarations_is_the_snapshots():
    assert DOC["source"]["registry_snapshot_sha256"] == fd.sha256_file(fd.DEFAULT_REGISTRY)
    assert (REPO / DOC["source"]["registry_snapshot"]).is_file()


def test_extract_schema_parses_columns_keys_and_identity_on_a_synthetic_dump():
    dump = (
        "CREATE TABLE public.t_a (\n    id integer NOT NULL,\n    k text NOT NULL,\n    v numeric(9,6) NOT NULL,\n"
        "    ts timestamp without time zone,\n    created_at timestamp with time zone DEFAULT now() NOT NULL,\n"
        "    u uuid DEFAULT gen_random_uuid() NOT NULL,\n    g text GENERATED ALWAYS AS (COALESCE(k, ''::text)) STORED,\n"
        "    CONSTRAINT t_a_chk CHECK ((v > 0))\n);\n\n"
        "ALTER TABLE public.t_a ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (\n    SEQUENCE NAME public.t_a_id_seq\n);\n"
        "ALTER TABLE ONLY public.t_a\n    ADD CONSTRAINT t_a_pkey PRIMARY KEY (id);\n"
        "ALTER TABLE ONLY public.t_a\n    ADD CONSTRAINT t_a_k_key UNIQUE (k);\n"
        "CREATE UNIQUE INDEX t_a_part ON public.t_a USING btree (v) WHERE (v > 1);\n"
        "CREATE UNIQUE INDEX t_a_plain ON public.t_a USING btree (k, v);\n")
    e = fd.extract_schema(dump, ["t_a"])
    t = e["tables"]["t_a"]
    assert t["primary_key"] == ["id"] and t["primary_key_name"] == "t_a_pkey"
    assert t["columns"]["id"]["identity"] and t["columns"]["u"]["identity"] and not t["columns"]["k"]["identity"]
    assert t["columns"]["ts"] == {"type": "timestamp without time zone", "not_null": False, "default": None, "generated": False, "identity": False}
    assert t["columns"]["v"]["type"] == "numeric(9,6)" and t["columns"]["g"]["generated"] is True
    assert t["columns"]["created_at"]["default"] == "now()"
    assert [u["name"] for u in t["unique"]] == ["t_a_k_key", "t_a_plain"] and t["unique"][1]["columns"] == ["k", "v"]
    assert [u["name"] for u in t["unique_other"]] == ["t_a_part"]
    with pytest.raises(fd.DeclarationError):
        fd.extract_schema(dump, ["t_missing"])


# ═════════════════════════ 3. refusals (one mutation each, table-driven) ═════════════════════════

def _t(doc, asset, name=None):
    tabs = doc["assets"][asset]["tables"]
    return tabs[0] if name is None else next(t for t in tabs if t["name"] == name)


def _ex_append(code, col, asset="bg_medical_mappings"):
    return lambda x: _t(x, asset)["exclude"].append({"column": col, "reason_code": code, "reason": "r" * 30})


def _del_reason(x):
    del _t(x, "bg_medical_mappings")["exclude"][0]["reason"]


def _nullable_schema(sch):
    sch["tables"]["bg_medical_mappings"]["columns"]["graha"]["not_null"] = False


MP = "platform/python-sidecar/brahmagyan/l0_medical.py"
# (id, expected problem code, mutator of the DOC | None, mutator of the schema extract | None)
REFUSALS = [
    ("unknown_asset", "unknown_asset", lambda x: x["assets"].update({"bg_not_an_asset": copy.deepcopy(x["assets"]["bg_sign_medical"])}), None),
    ("missing_asset", "missing_asset", lambda x: x["assets"].pop("bg_sign_medical"), None),
    ("unknown_top_key", "unknown_key", lambda x: x.update({"extra": 1}), None),
    ("missing_top_key", "missing_key", lambda x: x.pop("source"), None),
    ("unknown_asset_key", "unknown_key", lambda x: x["assets"]["bg_sign_medical"].update({"x": 1}), None),
    ("unknown_table_key", "unknown_key", lambda x: _t(x, "bg_sign_medical").update({"x": 1}), None),
    ("unknown_exclude_key", "unknown_key", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"x": 1}), None),
    ("undeclared_with_tables_key", "unknown_key", lambda x: x["assets"]["bg_panchanga"].update({"tables": []}), None),
    ("unknown_table", "unknown_table", lambda x: _t(x, "bg_sign_medical").update({"name": "no_such_table"}), None),
    ("unknown_table_written", "unknown_table", lambda x: x["assets"]["bg_class_priors"]["tables_written"].append("no_such_table"), None),
    ("unknown_table_not_covered", "unknown_table", lambda x: x["assets"]["bg_dasha_systems"]["not_covered_tables"][0].update({"name": "no_such_table"}), None),
    ("unknown_key_column", "unknown_column", lambda x: _t(x, "bg_medical_mappings").update({"key": ["no_such_col"]}), None),
    ("unknown_exclude_column", "unknown_column", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"column": "no_such_col"}), None),
    ("unknown_naive_column", "unknown_column", lambda x: _t(x, "bg_medical_mappings").update({"naive_utc_columns": ["no_such_col"]}), None),
    ("duplicate_key_column", "key_duplicate_column", lambda x: _t(x, "bg_dignity_reference", "bg_avastha_schemes").update({"key": ["scheme_name", "scheme_name"]}), None),
    ("key_not_a_constraint", "key_not_unique_in_schema", lambda x: _t(x, "bg_medical_mappings").update({"key": ["classical_citation"]}), None),
    ("key_proper_subset", "key_not_unique_in_schema", lambda x: _t(x, "bg_dignity_reference", "bg_avastha_schemes").update({"key": ["scheme_name"]}), None),
    ("key_evidence_unknown_constraint", "key_not_unique_in_schema", lambda x: _t(x, "bg_dignity_reference", "bg_avastha_schemes").update({"key_evidence": "unique:no_such_constraint"}), None),
    ("key_evidence_other_columns", "key_not_unique_in_schema", lambda x: _t(x, "bg_dignity_reference", "bg_avastha_schemes").update({"key_evidence": "primary_key:bg_avastha_schemes_pkey"}), None),
    ("key_evidence_malformed", "bad_key_evidence", lambda x: _t(x, "bg_dignity_reference", "bg_avastha_schemes").update({"key_evidence": "somewhere"}), None),
    ("nullable_key", "key_nullable", None, _nullable_schema),
    ("excluded_key_column", "exclude_key", _ex_append("surrogate_identity", "graha"), None),
    ("exclude_reason_deleted", "exclude_no_reason", _del_reason, None),
    ("exclude_reason_blank", "exclude_no_reason", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"reason": "   "}), None),
    ("exclude_reason_null", "exclude_no_reason", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"reason": None}), None),
    ("exclude_reason_short", "exclude_reason_short", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"reason": "volatile"}), None),
    ("exclude_unknown_code", "exclude_bad_reason_code", lambda x: _t(x, "bg_medical_mappings")["exclude"][0].update({"reason_code": "because"}), None),
    ("exclude_identity_unfit", "exclude_reason_unfit", _ex_append("surrogate_identity", "classical_citation"), None),
    ("exclude_timestamp_unfit", "exclude_reason_unfit", _ex_append("wall_clock_timestamp", "classical_citation"), None),
    ("exclude_build_unfit", "exclude_reason_unfit", _ex_append("build_identity", "classical_citation"), None),
    ("exclude_twice", "exclude_duplicate", lambda x: _t(x, "bg_medical_mappings")["exclude"].append(copy.deepcopy(_t(x, "bg_medical_mappings")["exclude"][0])), None),
    ("table_claimed_by_two_assets", "duplicate_table_claim", lambda x: x["assets"]["bg_nakshatra_medical"]["tables"].append(copy.deepcopy(_t(x, "bg_sign_medical"))), None),
    ("declared_table_also_written_elsewhere", "duplicate_table_claim", lambda x: x["assets"]["bg_class_priors"]["tables_written"].append("bg_sign_medical"), None),
    ("declared_and_not_covered", "duplicate_table_claim", lambda x: x["assets"]["bg_remedies"]["not_covered_tables"][0].update({"name": "brahma_remedy_corpus"}), None),
    ("naive_not_declared", "naive_utc_missing", lambda x: _t(x, "bg_muhurta_lattice").update({"naive_utc_columns": ["start_utc"]}), None),
    ("naive_not_declared_sky", "naive_utc_missing", lambda x: _t(x, "bg_sky_calendar").update({"naive_utc_columns": []}), None),
    ("naive_on_a_non_naive_column", "bad_naive_utc", lambda x: _t(x, "bg_medical_mappings").update({"naive_utc_columns": ["graha"]}), None),
    ("write_evidence_empty", "evidence_missing", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": []}), None),
    ("write_evidence_no_file", "evidence_missing", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": ["platform/python-sidecar/brahmagyan/no_such.py:3"]}), None),
    ("write_evidence_no_line", "evidence_missing", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": [f"{MP}:99999999"]}), None),
    ("write_evidence_other_table", "evidence_missing", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": ["platform/python-sidecar/brahmagyan/l0_kota_chakra_rings.py:5"]}), None),
    ("write_evidence_no_line_number", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": ["l0_medical.py"]}), None),
    ("write_evidence_absolute", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": ["/etc/passwd:1"]}), None),
    ("write_evidence_dotdot", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": ["../x.py:1"]}), None),
    ("write_evidence_line_zero", "evidence_bad", lambda x: _t(x, "bg_medical_mappings").update({"write_evidence": [f"{MP}:0"]}), None),
    ("undeclared_reason_short", "undeclared_reason", lambda x: x["assets"]["bg_panchanga"].update({"reason": "service"}), None),
    ("undeclared_reason_code", "undeclared_reason", lambda x: x["assets"]["bg_panchanga"].update({"reason_code": "whatever"}), None),
    ("undeclared_reason_code_missing", "missing_key", lambda x: x["assets"]["bg_panchanga"].pop("reason_code"), None),
    ("undeclared_no_evidence", "evidence_missing", lambda x: x["assets"]["bg_class_priors"].update({"evidence": []}), None),
    ("undeclared_reason_empty", "undeclared_reason", lambda x: x["assets"]["bg_class_priors"].update({"reason": ""}), None),
    ("partial_without_not_covered", "partial_mismatch", lambda x: x["assets"]["bg_remedies"].update({"coverage": "full"}), None),
    ("full_with_not_covered", "partial_mismatch", lambda x: x["assets"]["bg_sign_medical"].update({"coverage": "partial"}), None),
    ("not_covered_reason_short", "undeclared_reason", lambda x: x["assets"]["bg_remedies"]["not_covered_tables"][0].update({"reason": "queue"}), None),
    ("top_definition", "bad_definition", lambda x: x.update({"fingerprint_definition": "other/1"}), None),
    ("asset_definition", "bad_definition", lambda x: x["assets"]["bg_sign_medical"].update({"fingerprint_definition": "other/1"}), None),
    ("schema_id", "bad_schema_id", lambda x: x.update({"schema": "other/v1"}), None),
    ("asset_scope", "bad_scope", lambda x: x["assets"]["bg_sign_medical"].update({"scope": "chart"}), None),
    ("table_scope", "bad_scope", lambda x: _t(x, "bg_sign_medical").update({"scope": "chart"}), None),
    ("status", "bad_status", lambda x: x["assets"]["bg_sign_medical"].update({"status": "maybe"}), None),
    ("reproducibility_value", "bad_reproducibility", lambda x: x["assets"]["bg_sign_medical"].update({"reproducibility": ["sometimes"]}), None),
    ("reproducibility_mixed", "bad_reproducibility", lambda x: x["assets"]["bg_sign_medical"].update({"reproducibility": ["deterministic", "rolling_horizon"]}), None),
    ("coverage_value", "bad_coverage", lambda x: x["assets"]["bg_sign_medical"].update({"coverage": "most"}), None),
    ("empty_tables", "empty_tables", lambda x: x["assets"]["bg_sign_medical"].update({"tables": []}), None),
    ("registry_table_unaccounted", "registry_table_unaccounted",
     lambda x: _t(x, "bg_sign_medical").update({"name": "bg_nakshatra_medical", "key": ["nakshatra_name"], "key_evidence": "unique:bg_nakshatra_medical_nakshatra_name_key",
                                                "write_evidence": [f"{MP}:454"]}), None),
    ("undeclared_registry_table_unaccounted", "registry_table_unaccounted", lambda x: x["assets"]["bg_compendium_index"].update({"tables_written": []}), None),
    ("source_commit", "bad_source", lambda x: x["source"].update({"code_commit": "abc"}), None),
    ("source_sha", "bad_source", lambda x: x["source"].update({"schema_dump_sha256": "zz"}), None),
    ("no_assets", "bad_shape", lambda x: x.update({"assets": {}}), None),
]


def refusal_results(validate_fn) -> dict[str, bool]:
    """For every refusal: True when `validate_fn` (the validator under test) reports the expected problem code on the mutated document."""
    out = {}
    for rid, code, mdoc, msch in REFUSALS:
        doc, sch = copy.deepcopy(DOC), copy.deepcopy(EXT)
        if mdoc:
            mdoc(doc)
        if msch:
            msch(sch)
        try:
            out[rid] = code in {c for c, _p, _m in validate_fn(doc, registry=REG, schema=sch, repo_root=REPO)}
        except Exception:                                         # noqa: BLE001 - the validator never raises: a crash is a failed refusal
            out[rid] = False
    return out


def test_unmutated_baseline_has_no_problem():
    assert problems(copy.deepcopy(DOC)) == []


@pytest.mark.parametrize("rid,code,mdoc,msch", REFUSALS, ids=[r[0] for r in REFUSALS])
def test_refusal(rid, code, mdoc, msch):
    doc, sch = copy.deepcopy(DOC), copy.deepcopy(EXT)
    if mdoc:
        mdoc(doc)
    if msch:
        msch(sch)
    got = {c for c, _p, _m in problems(doc, schema=sch)}
    assert code in got, f"{rid}: expected {code}, got {sorted(got)}"


def test_every_refusal_code_the_validator_can_emit_is_covered_by_a_mutation():
    emitted = set(re.findall(r'probs\.append\(\("([a-z_]+)"', SRC_FD))
    covered = {r[1] for r in REFUSALS}
    # codes that guard the caller's own inputs rather than the document (registry/extract/file unreadable, bad fingerprint, bad table name)
    exempt = {"registry_unreadable", "schema_extract_unreadable", "declarations_unreadable", "bad_fingerprint", "bad_json", "duplicate_json_key",
              "bad_table_name", "bad_asset_id", "bad_key", "bad_exclude", "bad_naive_utc", "bad_shape", "unknown_key", "missing_key"}
    missing = sorted(emitted - covered - exempt)
    assert not missing, f"validator codes with no refusal test: {missing}"


def test_refuses_a_duplicate_json_key():
    text = json.dumps(DOC).replace('"bg_sign_medical": {', '"bg_sign_medical": {"status": "declared", "status": "declared", ', 1)
    with pytest.raises(fd.DeclarationError) as ei:
        fd.strict_loads(text)
    assert "duplicate_json_key" in ei.value.codes
    with pytest.raises(fd.DeclarationError) as e2:
        fd.strict_loads("{not json")
    assert "bad_json" in e2.value.codes
    with pytest.raises(fd.DeclarationError):
        fd.strict_loads('{"a": NaN}')


def test_load_declarations_raises_with_every_problem(tmp_path):
    bad = copy.deepcopy(DOC)
    _t(bad, "bg_medical_mappings")["exclude"][0]["reason"] = ""
    bad["assets"].pop("bg_sign_medical")
    p = tmp_path / "d.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(fd.DeclarationError) as ei:
        fd.load_declarations(p)
    assert {"exclude_no_reason", "missing_asset"} <= set(ei.value.codes)
    with pytest.raises(fd.DeclarationError):
        fd.load_declarations(tmp_path / "absent.json")
    assert fd.main(["validate", "--declarations", str(p)]) == 2


def test_cli_validate_and_summary_on_the_committed_file(capsys):
    assert fd.main(["validate"]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True
    assert fd.main(["summary"]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["assets_total"] == 40 and len(rep["declared"]) + len(rep["undeclared"]) == 40


# ═════════════════════════ 4. conversion to E5.5 and composition ═════════════════════════

def test_every_declared_table_is_a_valid_e55_declaration_in_volatile_mode():
    d = fd.load_declarations()
    n = 0
    for a in d.declared_assets():
        for t in d.tables(a):
            decl = d.table_declaration(a, t)
            norm = nsc.validate_declaration(decl, a)
            assert norm["scope"] == "global" and norm["semantic_columns"] is None and norm["volatile_columns"] == decl["volatile_columns"]
            assert nsc.build_select(decl) == f'SELECT * FROM "{t}"'
            n += 1
    assert n == sum(len(x["tables"]) for x in DOC["assets"].values() if x["status"] == "declared") == 59


def test_table_declaration_refuses_an_undeclared_asset_and_an_unknown_table():
    d = fd.load_declarations()
    for bad in (("bg_panchanga", "x"), ("bg_class_priors", "brahma_class_priors"), ("bg_nope", "x"), ("bg_sign_medical", "no_such")):
        with pytest.raises(fd.DeclarationError):
            d.table_declaration(*bad)
    with pytest.raises(fd.DeclarationError):
        d.tables("bg_text_index")


def test_a_declaration_that_e55_refuses_is_refused_at_conversion():
    d = fd.load_declarations()
    bad = copy.deepcopy(d.doc)
    _t(bad, "bg_medical_mappings")["key"] = ["Graha"]                       # not a lower-case identifier: E5.5's own refusal
    dd = fd.Declarations(doc=bad, sha256="0" * 64)
    with pytest.raises(nsc.BadDeclaration):
        dd.table_declaration("bg_medical_mappings", "bg_medical_mappings")


def test_composite_fingerprint_single_table_is_passthrough_and_multi_is_order_independent():
    a, b, c = "a" * 64, "b" * 64, "c" * 64
    assert fd.composite_fingerprint({"t1": a}) == a
    m1 = fd.composite_fingerprint({"t1": a, "t2": b})
    assert m1 == fd.composite_fingerprint({"t2": b, "t1": a}) and m1 not in (a, b)
    assert fd.composite_fingerprint({"t1": a, "t2": c}) != m1                  # a changed table moves the asset fingerprint
    assert fd.composite_fingerprint({"t1": a, "t3": b}) != m1                  # a renamed table moves it too
    for bad in ({}, {"t": "short"}, {"t": 5}, {1: a}):
        with pytest.raises(fd.DeclarationError):
            fd.composite_fingerprint(bad)


def test_reader_selects_are_exactly_the_build_select_of_each_declared_table():
    d = fd.load_declarations()
    sel = fd.reader_selects(d)
    assert len(sel) == 59 and all(re.fullmatch(r'SELECT \* FROM "[a-z0-9_]+"', s["sql"]) for s in sel)
    assert [s for s in sel if s["asset"] == "bg_sign_medical"] == [{"asset": "bg_sign_medical", "table": "bg_sign_medical", "sql": 'SELECT * FROM "bg_sign_medical"'}]
    assert not [s for s in sel if s["asset"] in d.undeclared_assets()]
    assert fd.reader_selects(d, ["bg_sign_medical"]) == [s for s in sel if s["asset"] == "bg_sign_medical"]
    with pytest.raises(fd.DeclarationError):
        fd.reader_selects(d, ["bg_panchanga"])


# ═════════════════════════ 5. real SQL on the disposable cluster ═════════════════════════

@pytest.fixture
def needs_psycopg():
    return pytest.importorskip("psycopg")


SYN_REG = {"a_one": {"target_table": "syn_one"}, "a_two": {"target_table": "syn_two_a"}}
SYN_DOC = {
    "schema": fd.SCHEMA_ID, "fingerprint_definition": fd.FINGERPRINT_DEFINITION, "layer": "L0", "scope": "global",
    "source": {"registry_snapshot": "x", "registry_snapshot_sha256": "0" * 64, "schema_dump": "x", "schema_dump_sha256": "0" * 64, "code_commit": "1" * 40},
    "assets": {
        "a_one": {"status": "declared", "fingerprint_definition": fd.FINGERPRINT_DEFINITION, "scope": "global", "coverage": "full",
                  "reproducibility": ["deterministic"], "not_covered_tables": [], "tables": [
                      {"name": "syn_one", "scope": "global", "key": ["k"], "key_evidence": "primary_key:syn_one_k", "naive_utc_columns": ["at_utc"],
                       "exclude": [{"column": "id", "reason_code": "surrogate_identity", "reason": "serial surrogate assigned at insert"},
                                   {"column": "created_at", "reason_code": "wall_clock_timestamp", "reason": "DEFAULT now() at insert time"}],
                       "write_evidence": ["x.py:1"]}]},
        "a_two": {"status": "declared", "fingerprint_definition": fd.FINGERPRINT_DEFINITION, "scope": "global", "coverage": "full",
                  "reproducibility": ["deterministic"], "not_covered_tables": [], "tables": [
                      {"name": "syn_two_a", "scope": "global", "key": ["k"], "key_evidence": "primary_key:p", "naive_utc_columns": [],
                       "exclude": [], "write_evidence": ["x.py:1"]},
                      {"name": "syn_two_b", "scope": "global", "key": ["k", "n"], "key_evidence": "unique:u", "naive_utc_columns": [],
                       "exclude": [{"column": "id", "reason_code": "surrogate_identity", "reason": "identity column assigned at insert"}],
                       "write_evidence": ["x.py:1"]}]},
        "a_three": {"status": "undeclared", "reason_code": "no_table", "tables_written": [], "evidence": [],
                    "reason": "a service asset: it owns no stored rows so there is nothing to fingerprint at all"}}}


def _syn_decls():
    reg = {**SYN_REG, "a_three": {"target_table": None}}
    assert fd.validate(SYN_DOC, registry=reg, schema=None, repo_root=None) == []
    return fd.Declarations(doc=copy.deepcopy(SYN_DOC), sha256="9" * 64)


def _connect(cl):
    log = sr.ConnectionLog()
    return sr.connect_checked(cl.url, "disposable", log, expect={"data_directory": str(cl.data_dir), "port": cl.port})


def _make_synthetic(conn, build: int, bump: str | None = None):
    cur = conn.cursor()
    for t in ("syn_one", "syn_two_a", "syn_two_b"):
        cur.execute(f"DROP TABLE IF EXISTS {t}")
    cur.execute("CREATE TABLE syn_one (id bigserial, k text PRIMARY KEY, v numeric(9,4) NOT NULL, at_utc timestamp NOT NULL, created_at timestamptz NOT NULL DEFAULT now())")
    cur.execute("CREATE TABLE syn_two_a (k text PRIMARY KEY, j jsonb NOT NULL)")
    cur.execute("CREATE TABLE syn_two_b (id bigserial, k text NOT NULL, n int NOT NULL, w text, UNIQUE (k, n))")
    for i in range(30):
        v = f"{i * 1.5:.4f}" if bump != f"k{i:02d}" else f"{i * 1.5 + 1:.4f}"
        cur.execute("INSERT INTO syn_one (k, v, at_utc) VALUES (%s, %s, %s)", (f"k{i:02d}", v, f"2020-01-{i % 28 + 1:02d} 00:00:00"))
        cur.execute("INSERT INTO syn_two_a (k, j) VALUES (%s, %s::jsonb)", (f"k{i:02d}", json.dumps({"i": i})))
        cur.execute("INSERT INTO syn_two_b (k, n, w) VALUES (%s, %s, %s)", (f"k{i:02d}", i, f"w{i}"))
    conn.commit()


def test_asset_fingerprint_equals_e55_table_fingerprint_and_ignores_exactly_the_declared_volatile_columns(needs_psycopg, disposable_pg):
    d = _syn_decls()
    conn = _connect(disposable_pg)
    try:
        _make_synthetic(conn, 1)
        one = fd.asset_fingerprint(conn, d, "a_one")
        decl = d.table_declaration("a_one", "syn_one")
        assert one["composite"] == one["tables"]["syn_one"]["sha256"] == nsc.table_fingerprint(conn, decl)
        assert one["tables"]["syn_one"]["rows"] == 30
        two = fd.asset_fingerprint(conn, d, "a_two")
        assert two["composite"] == fd.composite_fingerprint({t: v["sha256"] for t, v in two["tables"].items()}) != two["tables"]["syn_two_a"]["sha256"]
        # a delete-then-insert rebuild changes only id and created_at: the fingerprint must not move
        cur = conn.cursor()
        cur.execute("DELETE FROM syn_one")
        for i in range(30):
            cur.execute("INSERT INTO syn_one (k, v, at_utc) VALUES (%s, %s, %s)", (f"k{i:02d}", f"{i * 1.5:.4f}", f"2020-01-{i % 28 + 1:02d} 00:00:00"))
        conn.commit()
        assert fd.asset_fingerprint(conn, d, "a_one")["composite"] == one["composite"]
        # one semantic column changes in one table of a two-table asset: only that table and the composite move
        cur.execute("UPDATE syn_two_b SET w = 'changed' WHERE k = 'k07'")
        conn.commit()
        two2 = fd.asset_fingerprint(conn, d, "a_two")
        assert two2["tables"]["syn_two_a"] == two["tables"]["syn_two_a"] and two2["tables"]["syn_two_b"]["sha256"] != two["tables"]["syn_two_b"]["sha256"]
        assert two2["composite"] != two["composite"]
        # a semantic change in syn_one moves it
        cur.execute("UPDATE syn_one SET v = v + 1 WHERE k = 'k03'")
        conn.commit()
        assert fd.asset_fingerprint(conn, d, "a_one")["composite"] != one["composite"]
    finally:
        for t in ("syn_one", "syn_two_a", "syn_two_b"):
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
        conn.close()


def test_asset_fingerprints_covers_declared_assets_only_and_refuses_an_undeclared_one(needs_psycopg, disposable_pg):
    d = _syn_decls()
    conn = _connect(disposable_pg)
    try:
        _make_synthetic(conn, 1)
        out = fd.asset_fingerprints(conn, d, cursor_prefix="t")                 # server-side named cursors
        assert sorted(out["fingerprints"]) == ["a_one", "a_two"] and out["definition"] == fd.FINGERPRINT_DEFINITION
        assert out["declarations_sha256"] == "9" * 64 and out["tables"]["a_one"]["syn_one"]["rows"] == 30
        assert out["fingerprints"]["a_one"] == fd.asset_fingerprint(conn, d, "a_one")["composite"]
        with pytest.raises(fd.DeclarationError):
            fd.asset_fingerprints(conn, d, ["a_three"])
    finally:
        for t in ("syn_one", "syn_two_a", "syn_two_b"):
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
        conn.close()


def test_a_missing_declared_table_raises_it_never_reads_as_unchanged(needs_psycopg, disposable_pg):
    d = _syn_decls()
    conn = _connect(disposable_pg)
    try:
        conn.execute("DROP TABLE IF EXISTS syn_one")
        conn.commit()
        with pytest.raises(nsc.UnreadableInput):
            fd.asset_fingerprint(conn, d, "a_one")
        conn.rollback()
    finally:
        conn.close()


def test_a_naive_timestamp_not_declared_naive_utc_is_refused_by_e55_at_fingerprint_time(needs_psycopg, disposable_pg):
    d = _syn_decls()
    bad = copy.deepcopy(d.doc)
    bad["assets"]["a_one"]["tables"][0]["naive_utc_columns"] = []
    conn = _connect(disposable_pg)
    try:
        _make_synthetic(conn, 1)
        with pytest.raises(nsc.UnreadableInput):
            fd.asset_fingerprint(conn, fd.Declarations(doc=bad, sha256="9" * 64), "a_one")
        conn.rollback()
    finally:
        for t in ("syn_one", "syn_two_a", "syn_two_b"):
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
        conn.close()


# ═════════════════════════ 6. source mutants of the validator ═════════════════════════

SRC_FD = (GOV / "fingerprint_declarations.py").read_text(encoding="utf-8")


def load_module(src: str, name: str):
    mod = types.ModuleType(name)
    mod.__file__ = str(GOV / "fingerprint_declarations.py")
    sys.modules[name] = mod
    exec(compile(src, f"<{name}>", "exec"), mod.__dict__)         # noqa: S102 - the repo's own source, one mutation applied
    return mod


MUTANTS = [
    ('probs.append(("exclude_no_reason"', 'probs.append(("exclude_no_reason_x"'),
    ('        if col in key:\n            probs.append(("exclude_key"', '        if False:\n            probs.append(("exclude_key"'),
    ('        if code not in EXCLUDE_REASON_CODES:', '        if False:'),
    ('    if len(set(key)) != len(key):', '    if False:'),
    ('and not cols[c]["generated"]:', 'and False:'),
    ('        elif sorted(named[ke]) != sorted(key):', '        elif False:'),
    ('        if ke not in named:', '        if False:'),
    ('        for a in sorted(set(assets) - set(registry)):', '        for a in []:'),
    ('        for a in sorted(set(registry) - set(assets)):', '        for a in []:'),
    ('if code == "surrogate_identity" and not meta["identity"]:', 'if False:'),
    ('if code == "wall_clock_timestamp" and not meta["type"].startswith("timestamp"):', 'if False:'),
    ('if code == "build_identity" and col != "build_id":', 'if False:'),
    ('        if meta["type"] == TIMESTAMP_NAIVE and c not in ex_cols and c not in naive:', '        if False:'),
    ('        if c in cols and cols[c]["type"] != TIMESTAMP_NAIVE:', '        if False:'),
    ('        if (d["coverage"] == "partial") != bool(notcov):', '        if False:'),
    ('    if doc["fingerprint_definition"] != FINGERPRINT_DEFINITION:', '    if False:'),
    ('        if d["fingerprint_definition"] != FINGERPRINT_DEFINITION:', '        if False:'),
    ('    if int(line) > text.count("\\n") + 1:', '    if False:'),
    ('    elif table is not None and not re.search(rf"\\b{re.escape(table)}\\b", text):', '    elif False:'),
    ('                if n in claimed and claimed[n] != asset:', '                if False:'),
    ('        if others:', '        if False:'),
    ('            if d["reason_code"] not in UNDECLARED_CODES:', '            if False:'),
    ('        if d["coverage"] not in COVERAGE:', '        if False:'),
    ('    if doc["schema"] != SCHEMA_ID:', '    if False:'),
    ('    if t["scope"] != SCOPE:', '    if False:'),
    ('        if d["scope"] != SCOPE:', '        if False:'),
    ('        if status != "declared":', '        if False:'),
    ('    if tab is None:', '    if False:'),
    ('        if not (isinstance(tables, list) and tables):', '        if False:'),
    ('elif len(reason.strip()) < MIN_REASON_CHARS:', 'elif False:'),
    ('            if registry is not None and asset in registry and registry[asset].get("target_table") not in (None, *(tw if isinstance(tw, list) else [])):', '            if False:'),
    ('        if registry is not None and asset in registry and registry[asset].get("target_table") not in (None, *names):', '        if False:'),
    ('        for k in ("registry_snapshot_sha256", "schema_dump_sha256"):', '        for k in ():'),
    ('        if not (isinstance(src["code_commit"], str) and _HEX40.fullmatch(src["code_commit"])):', '        if False:'),
    ('    if len(table_shas) == 1:\n        return next(iter(table_shas.values()))', '    if len(table_shas) == 0:\n        return next(iter(table_shas.values()))'),
    ('"tables": dict(sorted(table_shas.items()))', '"tables": {k: "0" * 64 for k in table_shas}'),
    ('            raise DeclarationError([("duplicate_json_key"', '            pass\n            DeclarationError([("duplicate_json_key"'),
]


@pytest.mark.parametrize("old,new", MUTANTS, ids=[f"m{i:02d}" for i in range(len(MUTANTS))])
def test_validator_source_mutants_are_caught(old, new):
    """Each mutant removes one refusal from the validator; the refusal matrix (and the composition checks) must notice."""
    assert SRC_FD.count(old) >= 1, f"the mutant target no longer exists in the source: {old!r}"
    mutated = SRC_FD.replace(old, new, 1)
    assert mutated != SRC_FD
    try:
        m = load_module(mutated, "fd_mut_" + str(abs(hash(old + new)) % 10**8))
    except Exception:
        return                                                    # a mutant that does not even load is trivially dead
    base = {rid: ok for rid, ok in refusal_results(m.validate).items()}
    failed = [rid for rid, ok in base.items() if not ok]
    ok_clean = m.validate(copy.deepcopy(DOC), registry=REG, schema=EXT, repo_root=REPO) == []
    comp = False
    try:
        comp = (m.composite_fingerprint({"t1": "a" * 64}) == "a" * 64
                and m.composite_fingerprint({"t1": "a" * 64, "t2": "b" * 64}) == fd.composite_fingerprint({"t1": "a" * 64, "t2": "b" * 64}))
    except Exception:                                             # noqa: BLE001
        comp = False
    try:
        strict = m.strict_loads('{"a": 1, "a": 2}')
        dup_refused = False
    except Exception:                                             # noqa: BLE001 - DeclarationError from the mutant's own class
        dup_refused = True
        strict = None
    assert failed or not ok_clean or not comp or not dup_refused, f"SURVIVING MUTANT: replacing {old!r} with {new!r} changed no check"
