"""Content-digest specs must be deterministic, bounded, and fail closed."""
from __future__ import annotations

import pathlib
import json
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from pipeline.orchestrator.output_digest import (
    _component_key_preflight,
    _component_statement,
    compute_output_digest,
    _validate_spec,
    load_output_digest_spec,
)
from pipeline.orchestrator.provenance import canonical_digest


class _Cursor:
    def __init__(self, row=None, batches=(), null_key=False):
        self.row = row
        self.batches = list(batches)
        self.null_key = null_key
        self.executed = []
        self._next_row = row

    def execute(self, statement, params=None):
        self.executed.append((statement, params))
        self._next_row = ({"invalid_key": 1} if self.null_key else None) \
            if "SELECT 1 AS invalid_key" in statement else self.row

    def fetchone(self):
        return self._next_row

    def fetchmany(self, size):
        return self.batches.pop(0) if self.batches else []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _Connection:
    def __init__(self, stream_cursor):
        self.stream_cursor = stream_cursor
        self.cursor_calls = []

    def cursor(self, **kwargs):
        self.cursor_calls.append(kwargs)
        return self.stream_cursor


SPEC = {
    "version": "nirmana-output-digest-spec-v1",
    "components": [{
        "name": "rules",
        "relation": "bg_rules",
        "key_columns": ["rule_id"],
        "value_columns": ["rule_id", "rule_text"],
    }],
}


def test_missing_spec_is_explicitly_unproven_without_querying_output_rows():
    cursor = _Cursor(row=None)
    assert compute_output_digest(cursor, asset_id="bg_unknown") == (None, None)
    assert len(cursor.executed) == 1


def test_digest_streams_ordered_canonical_rows_and_never_fetches_all():
    cursor = _Cursor(
        row={"spec": SPEC, "spec_sha256": load_output_digest_spec.__module__ and ""},
        batches=[[{"row_json": '{"rule_id":"a","rule_text":"first"}'}], [{"row_json": '{"rule_id":"b","rule_text":"second"}'}]],
    )
    # The persisted SHA is checked against canonical spec content, rather than trusted.
    from pipeline.orchestrator.provenance import canonical_digest
    cursor.row["spec_sha256"] = canonical_digest(SPEC)

    first = compute_output_digest(cursor, asset_id="bg_rules")
    assert first[0] is not None
    assert first[1] == canonical_digest(SPEC)
    assert "ORDER BY" in cursor.executed[-1][0]
    assert "public" in cursor.executed[-1][0]


def test_component_statement_orders_by_reviewed_natural_keys_without_a_json_sort():
    statement = _component_statement(SPEC["components"][0])
    assert 'ORDER BY source."rule_id"' in statement
    assert 'to_jsonb(source."rule_id")' not in statement
    assert "row_json COLLATE" not in statement


def test_component_where_equals_is_parameterized_and_scopes_preflight_and_stream():
    filtered = {
        "version": "nirmana-output-digest-spec-v1",
        "components": [{
            "name": "ontology_doshas",
            "relation": "brahma_ontology",
            "key_columns": ["entity_class", "canonical_id"],
            "value_columns": ["entity_class", "canonical_id", "canonical_name_en"],
            "where_equals": {"entity_class": "dosha' OR TRUE --"},
        }],
    }
    cursor = _Cursor(
        row={"spec": filtered, "spec_sha256": canonical_digest(filtered)},
        batches=[[{"row_json": '{"entity_class":"dosha","canonical_id":"kala_sarpa"}'}]],
    )

    digest, _ = compute_output_digest(cursor, asset_id="bg_doshas")

    assert digest is not None
    preflight_sql, preflight_params = cursor.executed[-2]
    stream_sql, stream_params = cursor.executed[-1]
    assert 'source."entity_class" = %s' in preflight_sql
    assert 'source."entity_class" = %s' in stream_sql
    assert "OR TRUE" not in preflight_sql
    assert "OR TRUE" not in stream_sql
    assert preflight_params == ("dosha' OR TRUE --",)
    assert stream_params == ("dosha' OR TRUE --",)


def test_component_where_in_is_parameterized_and_scopes_preflight_and_stream():
    filtered = {
        "version": "nirmana-output-digest-spec-v1",
        "components": [{
            "name": "canonical_texts",
            "relation": "classical_texts",
            "key_columns": ["text_id"],
            "value_columns": ["text_id", "title_en"],
            "where_in": {"text_id": ["bphs", "bphs_jaimini"]},
        }],
    }
    cursor = _Cursor(
        row={"spec": filtered, "spec_sha256": canonical_digest(filtered)},
        batches=[[{"row_json": '{"text_id":"bphs","title_en":"BPHS"}'}]],
    )

    digest, _ = compute_output_digest(cursor, asset_id="bg_texts")

    assert digest is not None
    preflight_sql, preflight_params = cursor.executed[-2]
    stream_sql, stream_params = cursor.executed[-1]
    assert 'source."text_id" = ANY(%s)' in preflight_sql
    assert 'source."text_id" = ANY(%s)' in stream_sql
    assert preflight_params == (["bphs", "bphs_jaimini"],)
    assert stream_params == (["bphs", "bphs_jaimini"],)


def test_component_where_in_rejects_empty_unsorted_duplicate_and_mixed_sets():
    invalid_sets = [[], ["bphs_jaimini", "bphs"], ["bphs", "bphs"], [1, "bphs"]]
    for values in invalid_sets:
        invalid = {
            "version": "nirmana-output-digest-spec-v1",
            "components": [{
                "name": "canonical_texts",
                "relation": "classical_texts",
                "key_columns": ["text_id"],
                "value_columns": ["text_id"],
                "where_in": {"text_id": values},
            }],
        }
        cursor = _Cursor(row={"spec": invalid, "spec_sha256": canonical_digest(invalid)})
        try:
            load_output_digest_spec(cursor, "bg_texts")
        except ValueError as exc:
            assert "where_in" in str(exc)
        else:
            raise AssertionError(f"invalid where_in set was accepted: {values!r}")


def test_one_relation_can_be_split_into_disjoint_reviewed_null_scopes():
    split = {
        "version": "nirmana-output-digest-spec-v1",
        "components": [
            {
                "name": "compendium_by_chapter",
                "relation": "brahma_compendium_index",
                "key_columns": ["text_id", "chapter_num"],
                "value_columns": ["text_id", "chapter_num", "summary_text"],
                "where_is_null": ["topic_id"],
            },
            {
                "name": "compendium_by_topic",
                "relation": "brahma_compendium_index",
                "key_columns": ["text_id", "topic_id"],
                "value_columns": ["text_id", "topic_id", "summary_text"],
                "where_is_null": ["chapter_num"],
            },
        ],
    }
    cursor = _Cursor(row={"spec": split, "spec_sha256": canonical_digest(split)})

    loaded = load_output_digest_spec(cursor, "bg_compendium_index")

    assert loaded is not None
    chapter_sql = _component_statement(split["components"][0])
    topic_sql = _component_statement(split["components"][1])
    assert 'source."topic_id" IS NULL' in chapter_sql
    assert 'source."chapter_num" IS NULL' in topic_sql


def _not_null_spec(**extra):
    component = {
        "name": "candidates",
        "relation": "kala_activation_predicates",
        "key_columns": ["chart_id", "mechanism_id"],
        "value_columns": ["chart_id", "mechanism_id", "signal_id"],
        "where_not_null": ["mechanism_id"],
    }
    component.update(extra)
    return {"version": "nirmana-output-digest-spec-v1", "components": [component]}


def test_where_not_null_scopes_both_the_row_scan_and_the_null_key_preflight():
    """K9 D10/D6: legacy rows (NULL mechanism_id) must be scoped out of the scan AND of the NULL-key preflight."""
    spec = _not_null_spec(where_equals={"chart_id": "c"})
    component = spec["components"][0]
    cursor = _Cursor(row={"spec": spec, "spec_sha256": canonical_digest(spec)})
    assert load_output_digest_spec(cursor, "ka_yojaka") is not None
    assert 'source."mechanism_id" IS NOT NULL' in _component_statement(component)
    preflight = _component_key_preflight(component)
    assert '(source."chart_id" = %s AND source."mechanism_id" IS NOT NULL) AND (' in preflight


def test_where_not_null_rejects_empty_duplicate_non_identifier_and_contradictory_scopes():
    for bad in ([], ["mechanism_id", "mechanism_id"], ["Mechanism-Id"], "mechanism_id"):
        spec = _not_null_spec(where_not_null=bad)
        cursor = _Cursor(row={"spec": spec, "spec_sha256": canonical_digest(spec)})
        try:
            load_output_digest_spec(cursor, "ka_yojaka")
        except ValueError:
            continue
        raise AssertionError(f"invalid where_not_null was accepted: {bad!r}")
    both = _not_null_spec(where_is_null=["mechanism_id"])
    cursor = _Cursor(row={"spec": both, "spec_sha256": canonical_digest(both)})
    try:
        load_output_digest_spec(cursor, "ka_yojaka")
    except ValueError as exc:
        assert "NULL and NOT NULL" in str(exc)
    else:
        raise AssertionError("a column scoped both NULL and NOT NULL was accepted")


def test_components_differing_only_in_where_not_null_are_distinct_scopes():
    """The classed/classless split of the ka_yojaka v2 spec relies on NULL / NOT NULL being different scopes."""
    spec = _not_null_spec()
    twin = dict(spec["components"][0], name="twin", where_not_null=["chart_id"])
    spec["components"].append(twin)
    cursor = _Cursor(row={"spec": spec, "spec_sha256": canonical_digest(spec)})
    assert load_output_digest_spec(cursor, "ka_yojaka") is not None
    spec["components"][1]["where_not_null"] = ["mechanism_id"]
    cursor = _Cursor(row={"spec": spec, "spec_sha256": canonical_digest(spec)})
    try:
        load_output_digest_spec(cursor, "ka_yojaka")
    except ValueError as exc:
        assert "repeats a component" in str(exc)
    else:
        raise AssertionError("two components with the identical scope were accepted")


def test_unknown_component_key_is_refused_by_name_so_a_spec_never_means_less_than_it_says():
    """K9 D10 (N.8): a misspelt or unsupported filter key would otherwise be silently ignored."""
    for key in ("where_not_nul", "where_ne", "where_like", "limit"):
        spec = _not_null_spec(**{key: ["mechanism_id"]})
        cursor = _Cursor(row={"spec": spec, "spec_sha256": canonical_digest(spec)})
        try:
            load_output_digest_spec(cursor, "ka_yojaka")
        except ValueError as exc:
            assert "unknown key" in str(exc) and key in str(exc)
        else:
            raise AssertionError(f"unknown component key {key!r} was accepted")


def test_every_registered_migration_spec_still_validates_under_the_closed_key_set():
    """The closed key set must not retire any spec already registered by a migration."""
    migrations = pathlib.Path(__file__).resolve().parents[4] / "migrations"
    decoder = json.JSONDecoder()
    checked = 0
    for path in sorted(migrations.glob("*.sql")):
        text = path.read_text(errors="ignore")
        for match in re.finditer(r'\{"version":"nirmana-output-digest-spec-v1"', text):
            spec, _ = decoder.raw_decode(text[match.start():])
            _validate_spec("asset", spec, canonical_digest(spec))
            checked += 1
    assert checked >= 50, f"expected the registered specs to be found, saw {checked}"


def test_digest_uses_a_named_server_cursor_instead_of_client_buffering():
    stream = _Cursor(
        batches=[[{"row_json": '{"rule_id":"a","rule_text":"first"}'}]],
    )
    spec_cursor = _Cursor(row={"spec": SPEC, "spec_sha256": canonical_digest(SPEC)})
    spec_cursor.connection = _Connection(stream)

    digest, spec_sha = compute_output_digest(spec_cursor, asset_id="bg_rules")

    assert digest is not None
    assert spec_sha == canonical_digest(SPEC)
    assert len(spec_cursor.executed) == 2  # spec lookup + key-null preflight
    assert len(stream.executed) == 1
    assert spec_cursor.connection.cursor_calls[0]["name"].startswith("nirmana_digest_")
    assert spec_cursor.connection.cursor_calls[0]["row_factory"] is not None


def test_digest_fails_closed_before_scanning_rows_when_a_reviewed_key_is_null():
    cursor = _Cursor(
        row={"spec": SPEC, "spec_sha256": canonical_digest(SPEC)},
        null_key=True,
    )
    try:
        compute_output_digest(cursor, asset_id="bg_rules")
    except ValueError as exc:
        assert "NULL" in str(exc)
    else:
        raise AssertionError("NULL digest key was accepted")
    assert len(cursor.executed) == 2


def test_component_statement_batches_wide_tables_under_jsonb_build_object_arity_ceiling():
    # PostgreSQL's jsonb_build_object is variadic subject to FUNC_MAX_ARGS=100
    # (50 column/value pairs). A relation wider than that must never emit a
    # single call with >100 args, or every wide-table spec authored after
    # ga_positions' original 23-column precedent fails hard at compute time.
    wide = {
        "version": "nirmana-output-digest-spec-v1",
        "components": [{
            "name": "wide",
            "relation": "bo_wide_relation",
            "key_columns": ["signal_id"],
            "value_columns": [f"col_{i:03d}" for i in range(82)],
        }],
    }
    statement = _component_statement(wide["components"][0])
    for call in re.findall(r"jsonb_build_object\(([^)]*)\)", statement):
        arg_count = len([part for part in call.split(",") if part.strip()])
        assert arg_count <= 100, f"jsonb_build_object call exceeds FUNC_MAX_ARGS: {arg_count} args"
    assert statement.count("jsonb_build_object(") == 2  # 82 columns -> 2 batches of <=45
    assert " || " in statement
    assert all(f'"col_{i:03d}"' in statement for i in range(82))


def test_component_statement_single_batch_is_unchanged_for_narrow_tables():
    # Narrow tables (<=45 value_columns, the common case) must produce the
    # exact same SQL shape as before batching existed -- no wrapping
    # parentheses, no `||`, so every already-shipped digest spec's stored
    # content stays byte-identical.
    statement = _component_statement(SPEC["components"][0])
    assert statement.count("jsonb_build_object(") == 1
    assert " || " not in statement
    assert statement.startswith("SELECT jsonb_build_object(")


def test_invalid_spec_identifier_fails_closed_before_querying_a_relation():
    from pipeline.orchestrator.provenance import canonical_digest
    invalid = {"version": "nirmana-output-digest-spec-v1", "components": [{
        "name": "rules", "relation": "bg_rules; DROP TABLE asset_registry", "key_columns": ["rule_id"], "value_columns": ["rule_id"],
    }]}
    cursor = _Cursor(row={"spec": invalid, "spec_sha256": canonical_digest(invalid)})
    try:
        load_output_digest_spec(cursor, "bg_rules")
    except ValueError as exc:
        assert "identifier" in str(exc)
    else:  # pragma: no cover - assertion reads more clearly than pytest.raises here
        raise AssertionError("invalid digest spec was accepted")
    assert len(cursor.executed) == 1


def _ghatana_spec():
    migration = pathlib.Path(__file__).resolve().parents[4] / "supabase/migrations/598_nirmana_output_digest_specs.sql"
    match = re.search(r"'bg_ghatana',\s*'([a-f0-9]{64})',\s*'({.+?})'::jsonb", migration.read_text(), re.DOTALL)
    assert match, "migration 598 must seed a reviewed bg_ghatana digest spec"
    spec = json.loads(match.group(2))
    assert canonical_digest(spec) == match.group(1)
    return spec


def test_ghatana_spec_hashes_every_serving_semantic_event_shape_column():
    spec = _ghatana_spec()
    event_component = next(component for component in spec["components"] if component["name"] == "event_ontology")
    required = {
        "temporal_shape", "duration_prior", "milestone_template", "irreversibility_milestone",
        "evidence_requirements", "self_report_non_discriminating", "kill_switch_criteria",
    }
    assert required <= set(event_component["value_columns"])
    statement = _component_statement(event_component)
    assert all(f'"{column}"' in statement for column in required)


def test_ghatana_digest_changes_when_a_serving_semantic_event_shape_value_changes():
    spec = _ghatana_spec()
    sha = canonical_digest(spec)
    point = '{"event_class_id":"career_entry","temporal_shape":"point","duration_prior":null}'
    interval = '{"event_class_id":"career_entry","temporal_shape":"interval","duration_prior":{"min_days":1}}'
    left = _Cursor(row={"spec": spec, "spec_sha256": sha}, batches=[[{"row_json": point}], [], [], []])
    right = _Cursor(row={"spec": spec, "spec_sha256": sha}, batches=[[{"row_json": interval}], [], [], []])
    assert compute_output_digest(left, asset_id="bg_ghatana")[0] != compute_output_digest(right, asset_id="bg_ghatana")[0]


def _migration_specs(path: pathlib.Path):
    matches = re.findall(
        r"\(\s*'([^']+)',\s*'([a-f0-9]{64})',\s*'({.+?})'::jsonb\s*\)",
        path.read_text(),
        re.DOTALL,
    )
    return {asset_id: (spec_sha, json.loads(raw_spec)) for asset_id, spec_sha, raw_spec in matches}


def _migration_609_specs(path: pathlib.Path):
    text = path.read_text()
    result = {}
    for suffix, asset_id in (("reference", "bg_reference"), ("texts", "bg_texts")):
        sha_match = re.search(
            rf"new_{suffix}_sha constant text :=\s*'([a-f0-9]{{64}})'", text
        )
        spec_match = re.search(
            rf"new_{suffix}_spec constant jsonb :=\s*'({{.+?}})'::jsonb;",
            text,
            re.DOTALL,
        )
        assert sha_match and spec_match, f"migration 609 exact spec missing for {asset_id}"
        result[asset_id] = (sha_match.group(1), json.loads(spec_match.group(1)))
    return result


def test_every_frozen_l0_wave0_build_has_a_reviewed_canonical_digest_spec():
    platform_root = pathlib.Path(__file__).resolve().parents[4]
    repo_root = platform_root.parent
    seeded = {}
    for filename in (
        "598_nirmana_output_digest_specs.sql",
        "600_nirmana_l0_wave0_output_digest_specs.sql",
    ):
        seeded.update(_migration_specs(platform_root / "supabase/migrations" / filename))
    seeded.update(_migration_609_specs(
        platform_root / "supabase/migrations/609_nirmana_l0_digest_spec_revision.sql"
    ))

    manifest = json.loads(
        (repo_root / "00_ARCHITECTURE/control/NIRMANA_T0_MANIFEST_v1_1.json").read_text()
    )
    wave0_builds = {
        asset["asset_id"]
        for asset in manifest["assets"]
        if asset["layer"] == "L0"
        and asset["wave_index"] == 0
        and asset["execution_obligation"] == "build"
    }
    assert wave0_builds <= set(seeded)

    execution_only = {"build_id", "created_at", "computed_at", "ingested_at", "updated_at"}
    for asset_id in wave0_builds:
        spec_sha, spec = seeded[asset_id]
        assert canonical_digest(spec) == spec_sha
        assert spec["components"]
        for component in spec["components"]:
            assert set(component["key_columns"]) <= set(component["value_columns"])
            assert execution_only.isdisjoint(component["value_columns"])
            _component_statement(component)


def test_migration_600_remains_the_immutable_previously_unspecced_wave0_gap():
    platform_root = pathlib.Path(__file__).resolve().parents[4]
    specs_598 = _migration_specs(
        platform_root / "supabase/migrations/598_nirmana_output_digest_specs.sql"
    )
    specs_600 = _migration_specs(
        platform_root / "supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql"
    )
    assert len(specs_600) == 20
    assert not (set(specs_598) & set(specs_600))
    assert {"bg_reference", "bg_transit_rules", "bg_medical_mappings"} <= set(specs_600)

    legacy_reference_relations = {
        component["relation"] for component in specs_600["bg_reference"][1]["components"]
    }
    assert "reference_nakshatras" in legacy_reference_relations

    transit_relations = {
        component["relation"]
        for component in specs_600["bg_transit_rules"][1]["components"]
    }
    assert transit_relations == {"bg_transit_rules", "bg_transit_engine", "bg_transit_moorti"}


def test_migration_609_append_only_revisions_install_exact_owned_scopes():
    platform_root = pathlib.Path(__file__).resolve().parents[4]
    specs_609 = _migration_609_specs(
        platform_root / "supabase/migrations/609_nirmana_l0_digest_spec_revision.sql"
    )
    assert set(specs_609) == {"bg_reference", "bg_texts"}
    for spec_sha, spec in specs_609.values():
        assert canonical_digest(spec) == spec_sha

    reference_relations = {
        component["relation"]
        for component in specs_609["bg_reference"][1]["components"]
    }
    assert reference_relations == {
        "reference_planets",
        "reference_signs",
        "reference_aspects",
        "reference_vargas",
        "reference_houses",
        "reference_strength_systems",
        "reference_karakas",
        "reference_upagrahas",
        "reference_constants",
        "reference_topic_tags",
        "reference_glossary",
    }
    assert len(reference_relations) == 11

    text_components = specs_609["bg_texts"][1]["components"]
    canonical_text_ids = {
        "bhrigu_nandi_nadi", "bphs", "bphs_jaimini", "brihat_jataka",
        "brihat_samhita", "hora_sara", "jataka_parijata",
        "muhurta_chintamani", "nadi_navamsa_patel", "phaladeepika",
        "saravali", "sarvartha_chintamani", "tajaka_neelakanthi",
        "uttara_kalamrita", "yavana_jataka",
    }
    assert len(text_components) == 2
    assert all(
        set(component["where_in"]["text_id"]) == canonical_text_ids
        for component in text_components
    )
    chunk_component = next(
        component for component in text_components
        if component["relation"] == "classical_text_chunks"
    )
    co_written_columns = {
        "content_summary", "topics", "topic_tag", "ocr_confidence_score",
        "cleaned_translation_text", "cleaned_devanagari_text",
        "low_confidence_flag", "ocr_review_note", "ocr_cleanup_pass_version",
        "translation_status", "translation_provenance",
    }
    assert co_written_columns.isdisjoint(chunk_component["value_columns"])

def test_migration_601_completes_every_frozen_l0_build_digest_spec():
    platform_root = pathlib.Path(__file__).resolve().parents[4]
    repo_root = platform_root.parent
    seeded = {}
    for filename in (
        "598_nirmana_output_digest_specs.sql",
        "600_nirmana_l0_wave0_output_digest_specs.sql",
        "601_nirmana_l0_wave1_wave2_output_digest_specs.sql",
    ):
        seeded.update(_migration_specs(platform_root / "supabase/migrations" / filename))

    manifest = json.loads(
        (repo_root / "00_ARCHITECTURE/control/NIRMANA_T0_MANIFEST_v1_1.json").read_text()
    )
    l0_builds = {
        asset["asset_id"]
        for asset in manifest["assets"]
        if asset["layer"] == "L0" and asset["execution_obligation"] == "build"
    }
    assert l0_builds == set(seeded)

    specs_601 = _migration_specs(
        platform_root / "supabase/migrations/601_nirmana_l0_wave1_wave2_output_digest_specs.sql"
    )
    assert len(specs_601) == 10
    compendium = specs_601["bg_compendium_index"][1]["components"]
    assert {component["where_is_null"][0] for component in compendium} == {
        "chapter_num", "topic_id",
    }
    for asset_id, entity_class in (
        ("bg_dasha_systems", "dasha_system"),
        ("bg_doshas", "dosha"),
        ("bg_yogas", "yoga"),
    ):
        ontology = next(
            component
            for component in specs_601[asset_id][1]["components"]
            if component["relation"] == "brahma_ontology"
        )
        assert ontology["where_equals"] == {"entity_class": entity_class}


def test_compendium_digest_scopes_have_a_durable_exclusive_exhaustive_guard():
    migration = (
        pathlib.Path(__file__).resolve().parents[4]
        / "supabase/migrations/601_nirmana_l0_wave1_wave2_output_digest_specs.sql"
    ).read_text()
    assert "CHECK ((chapter_num IS NULL) <> (topic_id IS NULL))" in migration
    assert "Invalid brahma_compendium_index digest scope" in migration
