"""kyschema (relaunch plan v2.7 §14 B-0c): the stdlib-only JSON-Schema subset validator, and the six fleet
schemas it admits (§8 packet front matter, §10 release receipt, §4a.3 awaiting / surrogate decision, §6 job
result, §7 bootstrap launch input). Every rule is shown both passing and failing; a failing case must fail for
its own reason (the instance path and the schema location are asserted, not only the verdict)."""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
SCHEMAS = FLEET / "schemas"
FIX = HERE / "fixtures" / "b0c"
sys.path.insert(0, str(FLEET))

import kyschema  # noqa: E402

SCHEMA_NAMES = ["awaiting", "bootstrap_launch_input", "job_result", "packet", "release_receipt",
                "surrogate_decision"]
H40 = "a" * 40
H64 = "b" * 64


def schema(name):
    return json.loads((SCHEMAS / f"{name}.json").read_text(encoding="utf-8"))


def fixture(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def errors(sch, doc):
    return kyschema.validate(sch, doc)


def assert_valid(sch, doc):
    found = errors(sch, doc)
    assert found == [], "\n".join(found)


def assert_refused(sch, doc, *needles):
    """the document is refused and ONE error line carries every needle (path, reason, schema location)"""
    found = errors(sch, doc)
    assert found, "accepted, but a refusal was expected"
    assert any(all(n in line for n in needles) for line in found), \
        f"no error line carries all of {needles!r}:\n" + "\n".join(found)


def edit(doc, **changes):
    out = copy.deepcopy(doc)
    for dotted, value in changes.items():
        *parents, leaf = dotted.split("__")
        node = out
        for key in parents:
            node = node[int(key)] if isinstance(node, list) else node[key]
        if value is DROP:
            del node[int(leaf) if isinstance(node, list) else leaf]
        elif isinstance(node, list):
            node[int(leaf)] = value
        else:
            node[leaf] = value
    return out


DROP = object()


# --------------------------------------------------------------------------------------------------------------
# the validator: one positive and one negative per supported keyword
# --------------------------------------------------------------------------------------------------------------
KEYWORD_CASES = [
    ("type", {"type": "string"}, "x", 1, "expected type string, found integer"),
    ("type-list", {"type": ["string", "null"]}, None, 1.5, "expected type string or null, found number"),
    ("type-integer-is-not-boolean", {"type": "integer"}, 3, True, "found boolean"),
    ("type-integer-is-not-a-float", {"type": "integer"}, 3, 3.0, "found number"),
    ("type-number", {"type": "number"}, 3.5, "3.5", "expected type number, found string"),
    ("type-number-is-not-boolean", {"type": "number"}, 0, False, "found boolean"),
    ("type-object", {"type": "object"}, {}, [], "expected type object, found array"),
    ("type-array", {"type": "array"}, [], {}, "expected type array, found object"),
    ("type-boolean", {"type": "boolean"}, False, 0, "expected type boolean, found integer"),
    ("type-null", {"type": "null"}, None, "", "expected type null, found string"),
    ("required", {"required": ["a"]}, {"a": None}, {"b": 1}, "required property 'a' is missing"),
    ("properties", {"properties": {"a": {"type": "string"}}}, {"a": "x"}, {"a": 1}, "$.a: expected type string"),
    ("additionalProperties", {"properties": {"a": {}}, "additionalProperties": False}, {"a": 1}, {"a": 1, "z": 2},
     "$.z: additional property is not allowed"),
    ("items", {"items": {"type": "integer"}}, [1, 2], [1, "2"], "$[1]: expected type integer"),
    ("enum", {"enum": ["a", 1, None]}, 1, "b", "is not one of"),
    ("enum-true-is-not-1", {"enum": [1]}, 1, True, "is not one of"),
    ("enum-1.0-is-1", {"enum": [1]}, 1.0, 2, "is not one of"),
    ("enum-is-case-sensitive", {"enum": ["x"]}, "x", "X", "is not one of"),
    ("const", {"const": "2.3"}, "2.3", "2.4", "must equal \"2.3\""),
    ("const-false-is-not-0", {"const": False}, False, 0, "must equal false"),
    ("const-object", {"const": {"mcpServers": {}}}, {"mcpServers": {}}, {"mcpServers": {"x": {}}}, "must equal"),
    ("pattern", {"pattern": "^[0-9a-f]{4}$"}, "0af9", "0AF9", "does not match pattern"),
    ("pattern-dollar-is-the-true-end", {"pattern": "^[a-z]+$"}, "abc", "abc\n", "does not match pattern"),
    ("pattern-is-a-search", {"pattern": "b"}, "abc", "xyz", "does not match pattern"),
    ("pattern-digits-are-ascii", {"pattern": "^\\d+$"}, "123", "１２３", "does not match pattern"),
    ("pattern-word-characters-are-ascii", {"pattern": "^\\w+$"}, "a_1", "é", "does not match pattern"),
    # finding N-13: \\s is the ECMA-262 white-space set, so a negated class refuses what the standard refuses
    ("pattern-not-space-refuses-a-no-break-space", {"pattern": "^[^\\s]+$"}, "a-b", "a\u00a0b", "does not match pattern"),
    ("pattern-not-space-refuses-a-line-separator", {"pattern": "^[^\\s]+$"}, "a-b", "a\u2028b", "does not match pattern"),
    ("pattern-not-space-refuses-a-byte-order-mark", {"pattern": "^[^\\s]+$"}, "a-b", "a\ufeffb", "does not match pattern"),
    ("pattern-not-space-refuses-an-ideographic-space", {"pattern": "^[^\\s]+$"}, "a-b", "a\u3000b", "does not match pattern"),
    ("pattern-space-matches-a-no-break-space", {"pattern": "^a\\sb$"}, "a\u00a0b", "a\u200bb", "does not match pattern"),
    ("pattern-space-in-a-class-with-others", {"pattern": "^[\\s,]+$"}, " ,\u2029\t", " ;", "does not match pattern"),
    ("pattern-non-space", {"pattern": "^\\S+$"}, "a\u200bb", "a\u00a0b", "does not match pattern"),
    ("pattern-dot-stops-at-a-carriage-return", {"pattern": "^a.b$"}, "a\u00a0b", "a\rb", "does not match pattern"),
    ("pattern-dot-stops-at-a-line-separator", {"pattern": "^a.b$"}, "a b", "a\u2028b", "does not match pattern"),
    ("pattern-dot-stops-at-a-paragraph-separator", {"pattern": "^.*$"}, "", "a\u2029b", "does not match pattern"),
    ("pattern-escaped-dot-is-a-dot", {"pattern": "^a\\.b$"}, "a.b", "axb", "does not match pattern"),
    ("pattern-dot-in-a-class-is-a-dot", {"pattern": "^[.]+$"}, "..", "\r", "does not match pattern"),
    ("minLength", {"minLength": 2}, "ab", "a", "shorter than minLength 2"),
    ("maxLength", {"maxLength": 2}, "ab", "abc", "longer than maxLength 2"),
    ("minimum", {"minimum": 1}, 1, 0, "less than the minimum 1"),
    ("maximum", {"maximum": 5}, 5, 6, "greater than the maximum 5"),
    ("minItems", {"minItems": 1}, [0], [], "fewer than minItems 1"),
    ("maxItems", {"maxItems": 1}, [0], [0, 1], "more than maxItems 1"),
    ("uniqueItems", {"uniqueItems": True}, [1, "1", True], [{"a": 1}, {"a": 1.0}], "items [0] and [1] are equal"),
    ("allOf", {"allOf": [{"minimum": 1}, {"maximum": 3}]}, 2, 4, "greater than the maximum 3"),
    ("anyOf", {"anyOf": [{"type": "string"}, {"type": "null"}]}, None, 1, "matches none of the 2 anyOf alternatives"),
    ("oneOf-none", {"oneOf": [{"type": "string"}, {"type": "null"}]}, "x", 1, "matches 0 of the 2 oneOf alternatives"),
    ("oneOf-two", {"oneOf": [{"type": "integer"}, {"minimum": 0}]}, -1, 1, "matches 2 of the 2 oneOf alternatives"),
    ("not", {"not": {"required": ["a"]}}, {"b": 1}, {"a": 1}, "must not match the 'not' schema"),
    ("if-then", {"if": {"properties": {"k": {"const": 1}}, "required": ["k"]}, "then": {"required": ["x"]}},
     {"k": 2}, {"k": 1}, "required property 'x' is missing"),
    ("if-else", {"if": {"properties": {"k": {"const": 1}}, "required": ["k"]}, "then": {},
                 "else": {"not": {"required": ["x"]}}}, {"k": 1, "x": 0}, {"k": 2, "x": 0}, "must not match"),
    ("$ref", {"$defs": {"h": {"type": "string", "pattern": "^[0-9a-f]{40}$"}}, "properties": {"a": {"$ref": "#/$defs/h"}}},
     {"a": H40}, {"a": "zz"}, "does not match pattern '^[0-9a-f]{40}$' (schema #/properties/a/$ref(h)/pattern)"),
]


@pytest.mark.parametrize("name,sch,good,bad,reason", KEYWORD_CASES, ids=[c[0] for c in KEYWORD_CASES])
def test_each_supported_keyword_accepts_and_refuses(name, sch, good, bad, reason):
    assert_valid(sch, good)
    assert_refused(sch, bad, reason)


def test_patterns_are_read_as_ecma_262_reads_them_and_the_docstring_says_what_is_not_reconciled():
    """finding N-13: with ASCII classes `[^\\s]` accepted a no-break space and U+2028, which the standard's
    pattern language refuses — 'refuses more, never less' was untrue for negated classes"""
    ecma_space = "\t\n\x0b\x0c\r \xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a" \
                 "\u2028\u2029\u202f\u205f\u3000\ufeff"
    assert len(ecma_space) == 25
    space, not_space, in_class = (kyschema.compile_pattern(p) for p in ("^\\s$", "^\\S$", "^[^\\s]$"))
    for character in ecma_space:
        assert space.search(character) and not not_space.search(character) and not in_class.search(character), hex(ord(character))
    for character in "a0_-\x00\x1f\x85\u200b\u2060\u180e":          # not white space in ECMA-262 (U+0085, U+200B, …)
        assert not space.search(character) and not_space.search(character) and in_class.search(character), hex(ord(character))
    dot = kyschema.compile_pattern("^.$")
    assert [c for c in "\n\r\u2028\u2029" if dot.search(c)] == [] and all(dot.search(c) for c in "a \t\x0b\x0c\x85\xa0")
    # the three places that use a negated white-space class (packet.json): path, revision, schema_receipt_id
    packet = (SCHEMAS / "packet.json").read_text(encoding="utf-8")
    assert packet.count('"^[^\\\\s]+$"') == 3
    for bad in ("a\u00a0b", "a\u2028b", "a b", "a\tb", "a\ufeffb", ""):
        assert kyschema.validate({"pattern": "^[^\\s]+$"}, bad), repr(bad)
    doc = kyschema.__doc__
    assert "plan v2.7" in doc and "v2.3" not in doc
    for phrase in ("`\\s` is the ECMA-262 white space and line terminator set", "inside a character class too",
                   "`\\S` is its complement outside a", "refused at lint time inside one", "What is NOT reconciled",
                   "an unescaped `.` outside a class", "A pattern Python cannot compile is refused at lint time"):
        assert phrase in doc, phrase


def test_the_supported_keyword_list_is_exactly_the_documented_one():
    assert sorted(kyschema.SUPPORTED) == sorted([
        "type", "required", "properties", "additionalProperties", "items", "enum", "const", "pattern",
        "minLength", "maxLength", "minimum", "maximum", "minItems", "maxItems", "uniqueItems", "allOf", "anyOf",
        "oneOf", "not", "if", "then", "else", "$ref"])
    covered = {c[0].split("-")[0] for c in KEYWORD_CASES} | {"if", "then", "else"}
    assert set(kyschema.SUPPORTED) <= covered, sorted(set(kyschema.SUPPORTED) - covered)


def test_type_specific_keywords_do_not_apply_to_other_types():
    assert_valid({"minLength": 3, "minimum": 9, "minItems": 2, "required": ["a"], "pattern": "^z"}, None)
    assert_valid({"type": ["string", "null"], "pattern": "^[0-9a-f]{40}$"}, None)
    assert_refused({"type": ["string", "null"], "pattern": "^[0-9a-f]{40}$"}, "nope", "does not match pattern")


def test_errors_name_the_instance_path_the_reason_and_the_schema_location():
    sch = {"properties": {"list": {"items": {"properties": {"odd key": {"maximum": 1}}}}}}
    found = errors(sch, {"list": [{}, {"odd key": 2}]})
    assert found == ['$.list[1]["odd key"]: 2 is greater than the maximum 1 '
                     '(schema #/properties/list/items/properties/odd key/maximum)']


def test_every_error_is_reported_not_only_the_first():
    found = errors({"required": ["a", "b"], "properties": {"c": {"type": "string"}}}, {"c": 1})
    assert len(found) == 3


UNSUPPORTED = [
    ("format", {"type": "string", "format": "date-time"}, "unsupported keyword 'format'"),
    ("patternProperties", {"patternProperties": {"^x": {}}}, "unsupported keyword 'patternProperties'"),
    ("minProperties", {"minProperties": 1}, "unsupported keyword 'minProperties'"),
    ("exclusiveMinimum", {"exclusiveMinimum": 0}, "unsupported keyword 'exclusiveMinimum'"),
    ("default", {"default": 3}, "unsupported keyword 'default'"),
    ("definitions", {"definitions": {}}, "unsupported keyword 'definitions'"),
    ("dependentRequired", {"dependentRequired": {"a": ["b"]}}, "unsupported keyword 'dependentRequired'"),
    ("prefixItems", {"prefixItems": [{}]}, "unsupported keyword 'prefixItems'"),
    ("typo", {"requried": ["a"]}, "unsupported keyword 'requried'"),
    ("nested-in-properties", {"properties": {"a": {"items": {"format": "uri"}}}},
     "#/properties/a/items: unsupported keyword 'format'"),
    ("nested-in-defs", {"$defs": {"d": {"multipleOf": 2}}}, "#/$defs/d: unsupported keyword 'multipleOf'"),
    ("nested-in-allOf", {"allOf": [{"if": {"contains": {}}}]}, "#/allOf/0/if: unsupported keyword 'contains'"),
    ("additionalProperties-as-schema", {"additionalProperties": {"type": "string"}},
     "additionalProperties must be a boolean"),
    ("items-as-list", {"items": [{"type": "string"}]}, "#/items: a schema must be an object"),
    ("boolean-subschema", {"properties": {"a": True}}, "#/properties/a: a schema must be an object"),
    ("unknown-type", {"type": "str"}, "unknown type 'str'"),
    ("external-ref", {"$ref": "other.json#/$defs/x"}, "only '#/$defs/<name>' references are supported"),
    ("deep-ref", {"$defs": {"a": {"properties": {"b": {}}}}, "$ref": "#/$defs/a/properties/b"},
     "only '#/$defs/<name>' references are supported"),
    ("dangling-ref", {"$defs": {"a": {}}, "$ref": "#/$defs/b"}, "$ref target '#/$defs/b' does not exist"),
    ("nested-defs", {"properties": {"a": {"$defs": {"x": {}}}}}, "'$defs' is supported only at the schema root"),
    ("then-without-if", {"then": {"required": ["a"]}}, "'then' without 'if'"),
    ("else-without-if", {"else": {"required": ["a"]}}, "'else' without 'if'"),
    ("bad-pattern", {"pattern": "("}, "pattern does not compile"),
    ("non-space-inside-a-class", {"pattern": "^[\\S,]+$"}, "\\S inside a character class is not supported"),
    ("empty-enum", {"enum": []}, "enum must be a non-empty array"),
    ("required-not-strings", {"required": [1]}, "required must be an array of distinct strings"),
    ("required-duplicate", {"required": ["a", "a"]}, "required must be an array of distinct strings"),
    ("negative-minLength", {"minLength": -1}, "minLength must be a non-negative integer"),
    ("boolean-maximum", {"maximum": True}, "maximum must be a number"),
    ("empty-allOf", {"allOf": []}, "allOf must be a non-empty array of schemas"),
    ("uniqueItems-not-boolean", {"uniqueItems": 1}, "uniqueItems must be a boolean"),
    ("required-forbidden-by-additionalProperties",
     {"required": ["a"], "properties": {"b": {}}, "additionalProperties": False},
     "required property 'a' is not declared in properties although additionalProperties is false"),
    ("self-reference", {"$defs": {"a": {"$ref": "#/$defs/a"}}, "$ref": "#/$defs/a"}, "reference cycle"),
    ("cycle-through-allOf", {"$defs": {"a": {"allOf": [{"$ref": "#/$defs/b"}]}, "b": {"not": {"$ref": "#/$defs/a"}}}},
     "reference cycle"),
    ("root-not-an-object", [], "#: a schema must be an object"),
    ("annotation-not-a-string", {"description": 3}, "'description' must be a string"),
]


@pytest.mark.parametrize("name,sch,finding", UNSUPPORTED, ids=[c[0] for c in UNSUPPORTED])
def test_an_unsupported_or_malformed_schema_is_a_hard_error_never_ignored(name, sch, finding):
    found = kyschema.lint(sch)
    assert any(finding in line for line in found), found
    with pytest.raises(kyschema.SchemaError) as refused:
        kyschema.validate(sch, {})
    assert finding in str(refused.value)


def test_a_recursive_reference_through_a_property_is_not_a_cycle():
    tree = {"$defs": {"node": {"type": "object", "properties": {"kids": {"type": "array",
                                                                         "items": {"$ref": "#/$defs/node"}}}}},
            "$ref": "#/$defs/node"}
    assert kyschema.lint(tree) == []
    assert_valid(tree, {"kids": [{"kids": []}]})
    assert_refused(tree, {"kids": [{"kids": [3]}]}, "$.kids[0].kids[0]: expected type object")


def test_annotations_are_accepted_and_change_nothing():
    sch = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "x", "title": "t", "description": "d",
           "$comment": "c", "type": "integer"}
    assert kyschema.lint(sch) == []
    assert_valid(sch, 1)
    assert_refused(sch, "1", "expected type integer")


def test_ref_siblings_are_applied_together_with_the_target():
    sch = {"$defs": {"s": {"type": "string"}}, "$ref": "#/$defs/s", "minLength": 2}
    assert_valid(sch, "ab")
    assert_refused(sch, "a", "shorter than minLength 2")
    assert_refused(sch, 12, "expected type string")


# --------------------------------------------------------------------------------------------------------------
# strict loading and the command line
# --------------------------------------------------------------------------------------------------------------
def test_strict_loader_refuses_duplicate_keys_and_non_json_numbers(tmp_path):
    dup = tmp_path / "dup.json"
    dup.write_text('{"env": {"A": "1"}, "env": {}}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate key 'env'"):
        kyschema.load_json(dup)
    nan = tmp_path / "nan.json"
    nan.write_text('{"a": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="NaN"):
        kyschema.load_json(nan)
    ok = tmp_path / "ok.json"
    ok.write_text('{"a": [1, 2.5, null]}', encoding="utf-8")
    assert kyschema.load_json(ok) == {"a": [1, 2.5, None]}


def run_cli(*args):
    return subprocess.run([sys.executable, str(FLEET / "kyschema.py"), *map(str, args)],
                          capture_output=True, text=True, timeout=30)


def test_cli_exit_codes_valid_invalid_unsupported(tmp_path):
    good_schema = tmp_path / "s.json"
    good_schema.write_text(json.dumps({"type": "object", "required": ["a"]}), encoding="utf-8")
    bad_schema = tmp_path / "bad.json"
    bad_schema.write_text(json.dumps({"type": "object", "format": "x"}), encoding="utf-8")
    good = tmp_path / "good.json"
    good.write_text('{"a": 1}', encoding="utf-8")
    bad = tmp_path / "doc_bad.json"
    bad.write_text('{"b": 1}', encoding="utf-8")
    dup = tmp_path / "dup.json"
    dup.write_text('{"a": 1, "a": 2}', encoding="utf-8")

    ok = run_cli("validate", good_schema, good)
    assert ok.returncode == 0 and "SCHEMA-VALID" in ok.stdout
    invalid = run_cli("validate", good_schema, bad)
    assert invalid.returncode == 1 and "required property 'a' is missing" in invalid.stderr
    duplicated = run_cli("validate", good_schema, dup)
    assert duplicated.returncode == 1 and "duplicate key 'a'" in duplicated.stderr
    unsupported = run_cli("validate", bad_schema, good)
    assert unsupported.returncode == 2 and "unsupported keyword 'format'" in unsupported.stderr
    assert run_cli("lint", good_schema).returncode == 0
    linted = run_cli("lint", bad_schema)
    assert linted.returncode == 2 and "unsupported keyword 'format'" in linted.stderr
    missing = run_cli("validate", tmp_path / "absent.json", good)
    assert missing.returncode == 2
    assert run_cli("validate", good_schema, tmp_path / "absent.json").returncode == 1
    assert run_cli("frobnicate").returncode == 2


# --------------------------------------------------------------------------------------------------------------
# the fleet schemas
# --------------------------------------------------------------------------------------------------------------
def test_the_schema_directory_holds_the_six_schemas_of_this_work():
    """other B-0c work adds its own schemas beside these (qualification, launch configuration); those are tested
    where they are written — here only that none of the six is missing"""
    present = sorted(p.stem for p in SCHEMAS.glob("*.json"))
    assert [name for name in SCHEMA_NAMES if name in present] == SCHEMA_NAMES


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_every_schema_file_passes_lint_in_process_and_by_cli(name):
    assert kyschema.lint(kyschema.load_json(SCHEMAS / f"{name}.json")) == []
    cli = run_cli("lint", SCHEMAS / f"{name}.json")
    assert cli.returncode == 0, cli.stderr


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_every_schema_is_closed_at_the_top_level_and_describes_itself(name):
    sch = schema(name)
    assert sch["type"] == "object" and sch["additionalProperties"] is False
    assert sch["description"].strip() and sch["$id"].startswith("ky.")
    assert_refused(sch, {**fixture(VALID[name][0]), "surprise": 1}, "$.surprise: additional property is not allowed")
    assert_refused(sch, [], "$: expected type object")


VALID = {
    "packet": ["packet_bootstrap.json", "packet_feature.json", "packet_artifact.json", "packet_operation.json",
               "packet_schema_prerequisite.json"],
    "release_receipt": ["release_receipt_wait.json", "release_receipt_satisfied.json"],
    "awaiting": ["awaiting.json"],
    "surrogate_decision": ["surrogate_decision_routine.json", "surrogate_decision_veto.json",
                           "surrogate_decision_veto_effective.json", "surrogate_decision_hard_stop.json"],
    "job_result": ["job_result_done.json", "job_result_blocked.json", "job_result_failed.json",
                   "job_result_done_reviewer.json"],
    "bootstrap_launch_input": ["launch_input.json"],
}


@pytest.mark.parametrize("name,doc", [(n, d) for n, docs in VALID.items() for d in docs])
def test_valid_fixtures_are_accepted(name, doc):
    assert_valid(schema(name), fixture(doc))


def test_every_fixture_document_is_claimed_by_a_schema():
    claimed = {d for docs in VALID.values() for d in docs}
    on_disk = {p.name for p in FIX.glob("*.json")}
    assert on_disk == claimed, sorted(on_disk ^ claimed)


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_every_required_field_is_individually_required(name):
    sch = schema(name)
    doc = fixture(VALID[name][0])
    assert sch["required"], "a schema with no required field proves nothing"
    for field in sch["required"]:
        assert_refused(sch, edit(doc, **{field: DROP}), f"required property '{field}' is missing")


# ---- packet (plan §8) -----------------------------------------------------------------------------------------
PACKET_NEG = [
    # (id, fixture, edits, needles)
    ("kind-unknown", "packet_feature.json", {"kind": "chore"}, ("$.kind", "is not one of")),
    ("plan-version-pinned", "packet_feature.json", {"plan_version": "2.2"}, ("$.plan_version", 'must equal "2.7"')),
    ("plan-version-of-the-retired-plan", "packet_feature.json", {"plan_version": "2.3"},
     ("$.plan_version", 'must equal "2.7"')),
    ("max-loops-zero", "packet_feature.json", {"max_loops": 0}, ("$.max_loops", "less than the minimum 1")),
    ("max-loops-six", "packet_feature.json", {"max_loops": 6}, ("$.max_loops", "greater than the maximum 5")),
    ("max-loops-not-integer", "packet_feature.json", {"max_loops": "3"}, ("$.max_loops", "expected type integer")),
    ("needs-chart-data-not-boolean", "packet_feature.json", {"needs_chart_data": "false"},
     ("$.needs_chart_data", "expected type boolean")),
    ("build-tier-unknown", "packet_feature.json", {"build_tier": "haiku"}, ("$.build_tier", "is not one of")),
    ("routing-reason-empty", "packet_feature.json", {"routing_reason": ""}, ("$.routing_reason", "minLength 1")),
    ("wave-unknown", "packet_feature.json", {"wave": 4}, ("$.wave", "is not one of")),
    ("id-with-slash", "packet_feature.json", {"id": "K4/2a"}, ("$.id", "does not match pattern")),
    ("packet-sha-uppercase", "packet_feature.json", {"packet_sha256": "B" * 64},
     ("$.packet_sha256", "does not match pattern")),
    ("packet-sha-short", "packet_feature.json", {"packet_sha256": "b" * 63},
     ("$.packet_sha256", "does not match pattern")),
    ("spec-sources-empty", "packet_feature.json", {"spec_sources": []}, ("$.spec_sources", "fewer than minItems 1")),
    ("spec-source-sha-not-hex", "packet_feature.json", {"spec_sources__0__sha256": "z" * 64},
     ("$.spec_sources[0].sha256", "does not match pattern")),
    ("spec-source-missing-section-range", "packet_feature.json", {"spec_sources__0__section_range": DROP},
     ("$.spec_sources[0]", "required property 'section_range' is missing")),
    ("spec-source-missing-revision", "packet_feature.json", {"spec_sources__0__revision": DROP},
     ("$.spec_sources[0]", "required property 'revision' is missing")),
    ("spec-source-missing-path", "packet_feature.json", {"spec_sources__0__path": DROP},
     ("$.spec_sources[0]", "required property 'path' is missing")),
    ("spec-source-path-climbs", "packet_feature.json", {"spec_sources__0__path": "00_ARCHITECTURE/../x.md"},
     ("$.spec_sources[0].path", "must not match")),
    ("spec-source-path-not-a-string", "packet_feature.json", {"spec_sources__0__path": 7},
     ("$.spec_sources[0].path", "expected type string")),
    ("release-pins-negative-build", "packet_feature.json", {"release_pins__dash_build": -1},
     ("$.release_pins.dash_build", "less than the minimum 0")),
    ("release-pins-negative-revision", "packet_feature.json", {"release_pins__registry_revision": -1},
     ("$.release_pins.registry_revision", "less than the minimum 0")),
    ("spec-source-extra-key", "packet_feature.json", {"spec_sources__0__note": "x"},
     ("$.spec_sources[0].note", "additional property is not allowed")),
    # kind = feature
    ("feature-needs-original-failing-base", "packet_feature.json", {"original_failing_base": DROP},
     ("required property 'original_failing_base' is missing",)),
    ("feature-original-failing-base-null", "packet_feature.json", {"original_failing_base": None},
     ("$.original_failing_base", "expected type string")),
    ("feature-original-failing-base-short", "packet_feature.json", {"original_failing_base": "abc123"},
     ("$.original_failing_base", "does not match pattern")),
    ("feature-needs-test-commits", "packet_feature.json", {"test_commits": DROP},
     ("required property 'test_commits' is missing",)),
    ("feature-test-commits-empty", "packet_feature.json", {"test_commits": []},
     ("$.test_commits", "fewer than minItems 1")),
    ("feature-needs-expected-failing-assertion", "packet_feature.json", {"expected_failing_assertion": DROP},
     ("required property 'expected_failing_assertion' is missing",)),
    ("feature-expected-failing-assertion-null", "packet_feature.json", {"expected_failing_assertion": None},
     ("$.expected_failing_assertion", "expected type string")),
    ("test-commit-sha-not-40-hex", "packet_feature.json", {"test_commits__0__sha": "a" * 39},
     ("$.test_commits[0].sha", "does not match pattern")),
    ("test-commit-digest-not-sha256", "packet_feature.json", {"test_commits__0__digest": "a" * 40},
     ("$.test_commits[0].digest", "does not match pattern")),
    ("test-commit-path-absolute", "packet_feature.json", {"test_commits__0__path": "/abs/test_x.py"},
     ("$.test_commits[0].path", "does not match pattern")),
    ("test-commit-missing-digest", "packet_feature.json", {"test_commits__0__digest": DROP},
     ("$.test_commits[0]", "required property 'digest' is missing")),
    ("feature-intended-schema-forbidden", "packet_feature.json", {"intended_schema": {"t": ["c"]}},
     ("must not match the 'not' schema", "intended_schema")),
    ("feature-d1-paths-forbidden", "packet_feature.json", {"d1_paths": ["a/b.py"]},
     ("must not match the 'not' schema", "d1_paths")),
    ("feature-release-pins-bootstrap-string", "packet_feature.json", {"release_pins": "not_applicable: bootstrap"},
     ("$.release_pins", "expected type object")),
    ("feature-release-pins-missing-registry-revision", "packet_feature.json",
     {"release_pins__registry_revision": DROP}, ("$.release_pins", "'registry_revision' is missing")),
    ("feature-release-pins-main-sha", "packet_feature.json", {"release_pins__main_sha": H40},
     ("$.release_pins.main_sha", "additional property is not allowed")),
    ("feature-wave-B", "packet_feature.json", {"wave": "B"}, ("$.wave", "is not one of")),
    ("feature-wave-is-a-string", "packet_feature.json", {"wave": "0"}, ("$.wave", "is not one of")),
    ("feature-release-pins-a-list", "packet_feature.json", {"release_pins": ["dash", "r1"]},
     ("$.release_pins", "expected type object")),
    ("feature-schema-receipt-null", "packet_feature.json", {"schema_receipt_id": None},
     ("$.schema_receipt_id", "expected type string")),
    ("feature-pw-mechanism-version-null", "packet_feature.json", {"pw_mechanism_version": None},
     ("$.pw_mechanism_version", "expected type string")),
    # kind = bootstrap
    ("bootstrap-release-pins-must-be-not-applicable", "packet_bootstrap.json",
     {"release_pins": {"dash_build": "d", "registry_revision": "r"}},
     ("$.release_pins", 'must equal "not_applicable: bootstrap"')),
    ("bootstrap-release-pins-other-string", "packet_bootstrap.json", {"release_pins": "not_applicable"},
     ("$.release_pins", 'must equal "not_applicable: bootstrap"')),
    ("bootstrap-needs-d1-paths", "packet_bootstrap.json", {"d1_paths": DROP},
     ("required property 'd1_paths' is missing",)),
    ("bootstrap-d1-paths-empty", "packet_bootstrap.json", {"d1_paths": []}, ("$.d1_paths", "fewer than minItems 1")),
    ("bootstrap-d1-path-absolute", "packet_bootstrap.json", {"d1_paths__0": "/Users/Dev/x.py"},
     ("$.d1_paths[0]", "does not match pattern")),
    ("bootstrap-d1-path-dotdot", "packet_bootstrap.json", {"d1_paths__0": "fleet/../../etc/passwd"},
     ("$.d1_paths[0]", "must not match")),
    ("bootstrap-d1-path-leading-dotdot", "packet_bootstrap.json", {"d1_paths__0": "../x"},
     ("$.d1_paths[0]", "must not match")),
    ("bootstrap-d1-path-glob", "packet_bootstrap.json", {"d1_paths__0": "fleet/**"},
     ("$.d1_paths[0]", "does not match pattern")),
    ("bootstrap-d1-path-empty", "packet_bootstrap.json", {"d1_paths__0": ""},
     ("$.d1_paths[0]", "does not match pattern")),
    ("bootstrap-d1-path-not-a-string", "packet_bootstrap.json", {"d1_paths__0": 7},
     ("$.d1_paths[0]", "expected type string")),
    ("bootstrap-red-test-base-wrong-type", "packet_bootstrap.json", {"original_failing_base": 7},
     ("$.original_failing_base", "expected type string or null")),
    ("bootstrap-red-test-base-not-a-commit", "packet_bootstrap.json", {"original_failing_base": "HEAD"},
     ("$.original_failing_base", "does not match pattern")),
    ("bootstrap-red-test-assertion-wrong-type", "packet_bootstrap.json", {"expected_failing_assertion": 7},
     ("$.expected_failing_assertion", "expected type string or null")),
    ("bootstrap-red-test-assertion-empty", "packet_bootstrap.json", {"expected_failing_assertion": ""},
     ("$.expected_failing_assertion", "minLength 1")),
    ("bootstrap-test-commits-not-a-list", "packet_bootstrap.json", {"test_commits": "none"},
     ("$.test_commits", "expected type array")),
    ("bootstrap-wave-is-a-string-zero", "packet_bootstrap.json", {"wave": "0"}, ("$.wave", 'must equal "B"')),
    ("bootstrap-d1-path-duplicate", "packet_bootstrap.json",
     {"d1_paths": ["fleet/kylock.sh", "fleet/kylock.sh"]}, ("$.d1_paths", "are equal")),
    ("bootstrap-needs-acceptance", "packet_bootstrap.json", {"acceptance": DROP},
     ("required property 'acceptance' is missing",)),
    ("bootstrap-acceptance-needs-command", "packet_bootstrap.json", {"acceptance__command": DROP},
     ("$.acceptance", "required property 'command' is missing")),
    ("bootstrap-acceptance-needs-expected-result", "packet_bootstrap.json", {"acceptance__expected_result": DROP},
     ("$.acceptance", "required property 'expected_result' is missing")),
    ("bootstrap-acceptance-needs-negative-cases", "packet_bootstrap.json", {"acceptance__negative_cases": DROP},
     ("$.acceptance", "required property 'negative_cases' is missing")),
    ("bootstrap-acceptance-negative-cases-empty", "packet_bootstrap.json", {"acceptance__negative_cases": []},
     ("$.acceptance.negative_cases", "fewer than minItems 1")),
    ("bootstrap-needs-chart-data-true", "packet_bootstrap.json", {"needs_chart_data": True},
     ("$.needs_chart_data", "must equal false")),
    ("bootstrap-wave-not-B", "packet_bootstrap.json", {"wave": 0}, ("$.wave", 'must equal "B"')),
    ("bootstrap-tier-not-opus", "packet_bootstrap.json", {"build_tier": "sonnet"},
     ("$.build_tier", 'must equal "opus"')),
    ("bootstrap-id-not-namespaced", "packet_bootstrap.json", {"id": "K4-2a"}, ("$.id", "^KV3-B-")),
    ("bootstrap-intended-schema-forbidden", "packet_bootstrap.json", {"intended_schema": "x"},
     ("must not match the 'not' schema", "intended_schema")),
    # kind = schema-prerequisite
    ("schema-prerequisite-needs-intended-schema", "packet_schema_prerequisite.json", {"intended_schema": DROP},
     ("required property 'intended_schema' is missing",)),
    ("schema-prerequisite-intended-schema-empty-object", "packet_schema_prerequisite.json",
     {"intended_schema": {}}, ("$.intended_schema", "must not match the 'not' schema")),
    ("schema-prerequisite-intended-schema-empty-string", "packet_schema_prerequisite.json",
     {"intended_schema": ""}, ("$.intended_schema", "minLength 1")),
    ("schema-prerequisite-intended-schema-null", "packet_schema_prerequisite.json",
     {"intended_schema": None}, ("$.intended_schema", "expected type object or string")),
    ("schema-prerequisite-id-not-namespaced", "packet_schema_prerequisite.json", {"id": "K-CERT"},
     ("$.id", "^KV3-SCHEMA-")),
    # kinds artifact / operation
    ("artifact-needs-semantic-acceptance", "packet_artifact.json", {"semantic_acceptance": DROP},
     ("required property 'semantic_acceptance' is missing",)),
    ("artifact-semantic-acceptance-empty", "packet_artifact.json", {"semantic_acceptance": ""},
     ("$.semantic_acceptance", "minLength 1")),
    ("artifact-needs-negative-fixtures", "packet_artifact.json", {"negative_fixtures": DROP},
     ("required property 'negative_fixtures' is missing",)),
    ("artifact-negative-fixtures-empty", "packet_artifact.json", {"negative_fixtures": []},
     ("$.negative_fixtures", "fewer than minItems 1")),
    ("artifact-invented-red-test-base", "packet_artifact.json", {"original_failing_base": H40},
     ("$.original_failing_base", "must equal null")),
    ("artifact-invented-red-test-assertion", "packet_artifact.json", {"expected_failing_assertion": "assert x"},
     ("$.expected_failing_assertion", "must equal null")),
    ("artifact-intended-schema-forbidden", "packet_artifact.json", {"intended_schema": "x"},
     ("must not match the 'not' schema", "intended_schema")),
    ("operation-needs-semantic-acceptance", "packet_operation.json", {"semantic_acceptance": DROP},
     ("required property 'semantic_acceptance' is missing",)),
    ("operation-needs-negative-fixtures", "packet_operation.json", {"negative_fixtures": DROP},
     ("required property 'negative_fixtures' is missing",)),
    ("operation-invented-red-test-base", "packet_operation.json", {"original_failing_base": H40},
     ("$.original_failing_base", "must equal null")),
    ("operation-d1-paths-forbidden", "packet_operation.json", {"d1_paths": ["fleet/executor.py"]},
     ("must not match the 'not' schema", "d1_paths")),
]


@pytest.mark.parametrize("case,doc,edits,needles", PACKET_NEG, ids=[c[0] for c in PACKET_NEG])
def test_packet_refusals(case, doc, edits, needles):
    base = fixture(doc)
    assert_valid(schema("packet"), base)
    assert_refused(schema("packet"), edit(base, **edits), *needles)


def test_packet_optional_red_test_fields_may_be_null_or_absent_outside_feature_packets():
    sch = schema("packet")
    art = fixture("packet_artifact.json")
    assert_valid(sch, edit(art, original_failing_base=None, expected_failing_assertion=None, test_commits=[]))
    boot = fixture("packet_bootstrap.json")
    assert_valid(sch, edit(boot, schema_receipt_id="SR-20261009T200542Z-a9d843652016", pw_mechanism_version="1.0"))
    assert_valid(sch, edit(boot, original_failing_base=H40, expected_failing_assertion="AssertionError: x",
                           test_commits=[{"sha": H40, "digest": H64, "path": "fleet/tests/test_x.py"}]))
    for wave in (0, 1, 2, 3):
        assert_valid(sch, edit(fixture("packet_feature.json"), wave=wave))
    for loops in (1, 3, 5):
        assert_valid(sch, edit(fixture("packet_feature.json"), max_loops=loops))


# ---- release receipt (plan §10) -------------------------------------------------------------------------------
CONDITIONS = {
    "certification": ["coordination_commit", "record_id"],
    "pins": ["rebuild_producer", "rebuild_run"],
    "regeneration": ["main_commit", "generator_version", "output_digest"],
    "pr_dispositions": ["traversal_exhausted", "prs"],
    "coordinator_closure": ["handoff_records"],
}


def test_release_receipt_has_exactly_the_five_conditions_and_states_the_deferred_equality_check():
    sch = schema("release_receipt")
    assert sorted(sch["properties"]["conditions"]["required"]) == sorted(CONDITIONS)
    assert sorted(sch["properties"]["conditions"]["properties"]) == sorted(CONDITIONS)
    text = json.dumps(sch)
    assert "equal" in sch["description"] and "release_id" in sch["description"] and "code" in sch["description"]
    assert text.count("not checked by this schema") >= 1


@pytest.mark.parametrize("condition,field", [(c, f) for c, fs in CONDITIONS.items() for f in fs])
def test_a_satisfied_condition_requires_each_evidence_field_and_wait_does_not(condition, field):
    sch = schema("release_receipt")
    sat = fixture("release_receipt_satisfied.json")
    broken = edit(sat, **{f"conditions__{condition}__evidence__{field}": DROP})
    assert_refused(sch, broken, f"$.conditions.{condition}.evidence", f"required property '{field}' is missing")
    waiting = edit(broken, **{f"conditions__{condition}__status": "WAIT"})
    assert_valid(sch, waiting)


RECEIPT_NEG = [
    ("status-unknown", "release_receipt_wait.json", {"conditions__pins__status": "DONE"},
     ("$.conditions.pins.status", "is not one of")),
    ("condition-release-id-missing", "release_receipt_wait.json", {"conditions__pins__release_id": DROP},
     ("$.conditions.pins", "required property 'release_id' is missing")),
    ("condition-evidence-missing", "release_receipt_wait.json", {"conditions__pins__evidence": DROP},
     ("$.conditions.pins", "required property 'evidence' is missing")),
    ("condition-missing", "release_receipt_wait.json", {"conditions__coordinator_closure": DROP},
     ("$.conditions", "required property 'coordinator_closure' is missing")),
    ("sixth-condition", "release_receipt_wait.json",
     {"conditions__extra": {"status": "WAIT", "release_id": "R-1", "evidence": {}}},
     ("$.conditions.extra", "additional property is not allowed")),
    ("release-id-empty", "release_receipt_wait.json", {"release_id": ""}, ("$.release_id", "does not match pattern")),
    ("schema-version-other", "release_receipt_wait.json", {"schema_version": "ky.release_receipt/2"},
     ("$.schema_version", "must equal")),
    ("digest-not-sha256", "release_receipt_wait.json", {"digest": "abc"}, ("$.digest", "does not match pattern")),
    ("unknown-evidence-key", "release_receipt_wait.json", {"conditions__pins__evidence__note": "x"},
     ("$.conditions.pins.evidence.note", "additional property is not allowed")),
    ("certification-commit-not-40-hex", "release_receipt_satisfied.json",
     {"conditions__certification__evidence__coordination_commit": "abc"},
     ("$.conditions.certification.evidence.coordination_commit", "does not match pattern")),
    ("certification-record-id-empty", "release_receipt_satisfied.json",
     {"conditions__certification__evidence__record_id": ""},
     ("$.conditions.certification.evidence.record_id", "minLength 1")),
    ("regeneration-main-commit-not-40-hex", "release_receipt_satisfied.json",
     {"conditions__regeneration__evidence__main_commit": "main"},
     ("$.conditions.regeneration.evidence.main_commit", "does not match pattern")),
    ("regeneration-output-digest-not-sha256", "release_receipt_satisfied.json",
     {"conditions__regeneration__evidence__output_digest": H40},
     ("$.conditions.regeneration.evidence.output_digest", "does not match pattern")),
    ("satisfied-needs-exhausted-traversal", "release_receipt_satisfied.json",
     {"conditions__pr_dispositions__evidence__traversal_exhausted": False},
     ("$.conditions.pr_dispositions.evidence.traversal_exhausted", "must equal true")),
    ("pr-disposition-unknown", "release_receipt_satisfied.json",
     {"conditions__pr_dispositions__evidence__prs__0__disposition": "open"},
     ("$.conditions.pr_dispositions.evidence.prs[0].disposition", "is not one of")),
    ("pr-number-zero", "release_receipt_satisfied.json",
     {"conditions__pr_dispositions__evidence__prs__0__pr": 0},
     ("$.conditions.pr_dispositions.evidence.prs[0].pr", "less than the minimum 1")),
    ("waiting-traversal-flag-not-boolean", "release_receipt_wait.json",
     {"conditions__pr_dispositions__evidence": {"traversal_exhausted": "yes"}},
     ("$.conditions.pr_dispositions.evidence.traversal_exhausted", "expected type boolean")),
    ("pr-number-not-integer", "release_receipt_satisfied.json",
     {"conditions__pr_dispositions__evidence__prs__0__pr": "3379"},
     ("$.conditions.pr_dispositions.evidence.prs[0].pr", "expected type integer")),
    ("pr-owner-missing", "release_receipt_satisfied.json",
     {"conditions__pr_dispositions__evidence__prs__0__owner": DROP},
     ("$.conditions.pr_dispositions.evidence.prs[0]", "required property 'owner' is missing")),
    ("pr-re-entry-missing", "release_receipt_satisfied.json",
     {"conditions__pr_dispositions__evidence__prs__0__re_entry": DROP},
     ("$.conditions.pr_dispositions.evidence.prs[0]", "required property 're_entry' is missing")),
    ("parked-pr-needs-a-re-entry", "release_receipt_satisfied.json",
     {"conditions__pr_dispositions__evidence__prs__1__re_entry": None},
     ("$.conditions.pr_dispositions.evidence.prs[1].re_entry", "expected type string")),
    ("satisfied-closure-needs-a-hand-off-record", "release_receipt_satisfied.json",
     {"conditions__coordinator_closure__evidence__handoff_records": []},
     ("$.conditions.coordinator_closure.evidence.handoff_records", "fewer than minItems 1")),
]


@pytest.mark.parametrize("case,doc,edits,needles", RECEIPT_NEG, ids=[c[0] for c in RECEIPT_NEG])
def test_release_receipt_refusals(case, doc, edits, needles):
    base = fixture(doc)
    assert_valid(schema("release_receipt"), base)
    assert_refused(schema("release_receipt"), edit(base, **edits), *needles)


def test_release_receipt_wait_tolerates_partial_evidence_but_still_types_it():
    sch = schema("release_receipt")
    wait = fixture("release_receipt_wait.json")
    assert_valid(sch, edit(wait, conditions__pr_dispositions__evidence={"traversal_exhausted": False, "prs": []}))
    assert_refused(sch, edit(wait, conditions__regeneration__evidence={"main_commit": "main"}),
                   "$.conditions.regeneration.evidence.main_commit", "does not match pattern")


def test_release_receipt_schema_cannot_see_mixed_release_ids_and_says_so():
    """the schema's limit, stated rather than hidden: equality of the release ids is the gate's check (§10)"""
    sat = fixture("release_receipt_satisfied.json")
    mixed = edit(sat, conditions__pins__release_id="R-OTHER")
    assert_valid(schema("release_receipt"), mixed)
    assert "not checked by this schema" in schema("release_receipt")["$defs"]["condition_release_id"]["description"]


# ---- awaiting / surrogate decision / job result ----------------------------------------------------------------
SMALL_NEG = [
    ("awaiting", "awaiting.json", {"schema": "ky.awaiting/2"}, ("$.schema", 'must equal "ky.awaiting/1"')),
    ("awaiting", "awaiting.json", {"id": "AW-20261011T2200Z-x"}, ("$.id", "does not match pattern")),
    ("awaiting", "awaiting.json", {"id": "AW-20261011T220000Z-Bad_Slug"}, ("$.id", "does not match pattern")),
    ("awaiting", "awaiting.json", {"id": "AW-20261011T220000Z-"}, ("$.id", "does not match pattern")),
    ("awaiting", "awaiting.json", {"created_at": "2026-10-11 22:00"}, ("$.created_at", "does not match pattern")),
    ("awaiting", "awaiting.json", {"created_at": "2026-10-11T22:00:00+05:30"},
     ("$.created_at", "does not match pattern")),
    ("awaiting", "awaiting.json", {"raised_by__role": DROP}, ("$.raised_by", "required property 'role' is missing")),
    ("awaiting", "awaiting.json", {"raised_by__session_id": DROP},
     ("$.raised_by", "required property 'session_id' is missing")),
    ("awaiting", "awaiting.json", {"raised_by__job_id": 7}, ("$.raised_by.job_id", "expected type string or null")),
    ("awaiting", "awaiting.json", {"item": 3}, ("$.item", "expected type string or null")),
    ("awaiting", "awaiting.json", {"question": ""}, ("$.question", "minLength 1")),
    ("awaiting", "awaiting.json", {"options__0__text": DROP}, ("$.options[0]", "required property 'text' is missing")),
    ("awaiting", "awaiting.json", {"options": "a or b"}, ("$.options", "expected type array")),
    ("awaiting", "awaiting.json", {"recommendation": 1}, ("$.recommendation", "expected type string or null")),
    ("awaiting", "awaiting.json", {"evidence": ["ok", 3]}, ("$.evidence[1]", "expected type string")),
    ("awaiting", "awaiting.json", {"deadline": "tomorrow"}, ("$.deadline", "does not match pattern")),
    ("awaiting", "awaiting.json", {"class_hint": "urgent"}, ("$.class_hint", "is not one of")),
    ("awaiting", "awaiting.json", {"blocks": "everything"}, ("$.blocks", "is not one of")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"id": "SD-20261011T220000Z-x"},
     ("$.id", "does not match pattern")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"awaiting": "the capacity question"},
     ("$.awaiting", "does not match pattern")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"class": "unknown"}, ("$.class", "is not one of")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"by": "claude"}, ("$.by", "is not one of")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"state": "DONE"}, ("$.state", "is not one of")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"state": "PENDING_VETO"},
     ("$.state", "is not one of", "allOf/2/then")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"state": "VETOED"},
     ("$.state", "is not one of", "allOf/2/then")),
    ("surrogate_decision", "surrogate_decision_hard_stop.json", {"state": "EFFECTIVE"},
     ("$.state", 'must equal "PROPOSED"')),
    ("surrogate_decision", "surrogate_decision_hard_stop.json", {"state": "EXECUTED"},
     ("$.state", 'must equal "PROPOSED"')),
    ("surrogate_decision", "surrogate_decision_hard_stop.json", {"state": "PENDING_VETO"},
     ("$.state", 'must equal "PROPOSED"')),
    ("surrogate_decision", "surrogate_decision_veto.json", {"state": "EFFECTIVE"},
     ("$.effective_at", "expected type string", "allOf/1/then")),
    ("surrogate_decision", "surrogate_decision_veto_effective.json", {"effective_at": None},
     ("$.effective_at", "expected type string", "allOf/1/then")),
    ("surrogate_decision", "surrogate_decision_veto_effective.json", {"veto_deadline": None},
     ("$.veto_deadline", "expected type string")),
    ("surrogate_decision", "surrogate_decision_veto_effective.json", {"state": "EXECUTED", "effective_at": None},
     ("$.effective_at", "expected type string", "allOf/5/then")),
    ("surrogate_decision", "surrogate_decision_veto.json", {"state": "EXECUTED"},
     ("$.effective_at", "expected type string", "allOf/5/then")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"target": "KY_BUILDERS_MAX"},
     ("$.target", "expected type object")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"authority__source_commit": "e709f60d7"},
     ("$.authority.source_commit", "does not match pattern")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"authority__entrypoints_digest": "5" * 40},
     ("$.authority.entrypoints_digest", "does not match pattern")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"authority__entrypoints_digest": DROP},
     ("$.authority", "required property 'entrypoints_digest' is missing")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"authority__plan": "2.7"},
     ("$.authority.plan", "additional property is not allowed")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"notification__submitted": "yes"},
     ("$.notification.submitted", "expected type boolean")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"notification__ts": 1760220301},
     ("$.notification.ts", "expected type string or null")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"notification__ts": DROP},
     ("$.notification", "required property 'ts' is missing")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"reason": 7}, ("$.reason", "expected type string")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"effective_at": 0},
     ("$.effective_at", "expected type string or null")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"decision": ""}, ("$.decision", "minLength 1")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"rationale": ""}, ("$.rationale", "minLength 1")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"session": ""}, ("$.session", "minLength 1")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"effective_at": "now"},
     ("$.effective_at", "does not match pattern")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"evidence": "x"}, ("$.evidence", "expected type array")),
    ("surrogate_decision", "surrogate_decision_routine.json", {"veto_deadline": "2026-10-11T22:30:00Z"},
     ("$.veto_deadline", "expected type null")),
    ("surrogate_decision", "surrogate_decision_veto.json", {"veto_deadline": None},
     ("$.veto_deadline", "expected type string")),
    ("surrogate_decision", "surrogate_decision_veto.json", {"veto_deadline": "in 30 minutes"},
     ("$.veto_deadline", "does not match pattern")),
    ("job_result", "job_result_done.json", {"schema": "ky.job_result/0"}, ("$.schema", "must equal")),
    ("job_result", "job_result_done.json", {"status": "ok"}, ("$.status", "is not one of")),
    ("job_result", "job_result_done.json", {"head_sha": None}, ("$.head_sha", "expected type string", "allOf/1/then")),
    ("job_result", "job_result_done_reviewer.json", {"pr_number": 3501},
     ("$.head_sha", "expected type string", "allOf/1/then")),
    ("job_result", "job_result_blocked.json", {"pr_number": 3501}, ("$.head_sha", "expected type string")),
    ("job_result", "job_result_done_reviewer.json", {"proposed_verdict": "ACCEPTED"},
     ("$.proposed_verdict", "expected type object")),
    ("job_result", "job_result_done_reviewer.json", {"verdict": {"verdict": "ACCEPTED"}},
     ("$.verdict", "additional property is not allowed")),
    ("job_result", "job_result_done.json", {"head_sha": "abc"}, ("$.head_sha", "does not match pattern")),
    ("job_result", "job_result_done.json", {"pr_number": "12"}, ("$.pr_number", "expected type integer or null")),
    ("job_result", "job_result_done.json", {"pr_number": 0}, ("$.pr_number", "less than the minimum 1")),
    ("job_result", "job_result_done.json", {"tests__0__exit": "0"}, ("$.tests[0].exit", "expected type integer")),
    ("job_result", "job_result_done.json", {"tests__0__cmd": DROP},
     ("$.tests[0]", "required property 'cmd' is missing")),
    ("job_result", "job_result_done.json", {"tests__0__summary": DROP},
     ("$.tests[0]", "required property 'summary' is missing")),
    ("job_result", "job_result_done.json", {"notes": None}, ("$.notes", "expected type string")),
    ("job_result", "job_result_done.json", {"job_id": "../escape"}, ("$.job_id", "does not match pattern")),
    ("job_result", "job_result_done.json", {"branch": 4}, ("$.branch", "expected type string or null")),
    ("job_result", "job_result_blocked.json", {"blocked_reason": None}, ("$.blocked_reason", "expected type string")),
    ("job_result", "job_result_blocked.json", {"blocked_reason": ""}, ("$.blocked_reason", "minLength 1")),
]


@pytest.mark.parametrize("name,doc,edits,needles", SMALL_NEG,
                         ids=[f"{c[0]}:{'+'.join(c[2])}={i}" for i, c in enumerate(SMALL_NEG)])
def test_awaiting_surrogate_decision_and_job_result_refusals(name, doc, edits, needles):
    base = fixture(doc)
    assert_valid(schema(name), base)
    assert_refused(schema(name), edit(base, **edits), *needles)


def test_the_nullable_fields_accept_null_where_the_pinned_shape_says_so():
    aw = fixture("awaiting.json")
    assert_valid(schema("awaiting"), edit(aw, item=None, recommendation=None, deadline=None, options=[], evidence=[],
                                          raised_by__session_id=None, raised_by__job_id=None))
    assert_valid(schema("awaiting"), edit(aw, created_at="2026-10-11T22:00:00.123456+00:00"))
    for hint in ("routine", "veto", "hard_stop", "unknown"):
        assert_valid(schema("awaiting"), edit(aw, class_hint=hint))
    for blocks in ("item", "loop", "none"):
        assert_valid(schema("awaiting"), edit(aw, blocks=blocks))
    failed = fixture("job_result_failed.json")
    assert failed["head_sha"] is None and failed["branch"] is None and failed["pr_number"] is None
    assert failed["blocked_reason"] is None
    hard = fixture("surrogate_decision_hard_stop.json")
    assert_valid(schema("surrogate_decision"), edit(hard, veto_deadline=None))
    assert_valid(schema("surrogate_decision"), edit(hard, veto_deadline="2026-10-11T22:30:00Z"))


def test_the_surrogate_decision_states_each_class_may_take():
    """plan v2.7 §4a.3: routine PROPOSED → EFFECTIVE → EXECUTED; veto PROPOSED → PENDING_VETO → EFFECTIVE →
    EXECUTED | VETOED | FAILED, EFFECTIVE only with an effective_at; hard_stop is recorded, never published"""
    sch = schema("surrogate_decision")
    states = sch["properties"]["state"]["enum"]
    assert states == ["PROPOSED", "PENDING_VETO", "EFFECTIVE", "EXECUTED", "VETOED", "FAILED"]
    assert sch["properties"]["by"]["enum"] == ["kalayantra-owner-surrogate", "kyveto"]
    routine, veto, hard = (fixture(f"surrogate_decision_{name}.json") for name in ("routine", "veto", "hard_stop"))
    allowed = {"routine": {"PROPOSED", "EFFECTIVE", "EXECUTED", "FAILED"},
               "veto": {"PROPOSED", "PENDING_VETO", "VETOED", "FAILED"},      # EFFECTIVE, EXECUTED: see below
               "hard_stop": {"PROPOSED"}}
    for doc, name in ((routine, "routine"), (veto, "veto"), (hard, "hard_stop")):
        for state in states:
            for effective_at in (None, "2026-10-11T22:35:02Z"):
                found = kyschema.validate(sch, edit(doc, state=state, effective_at=effective_at))
                # finding N-14: a veto decision that was executed became effective first — at a recorded time
                expected = state in allowed[name] or (name == "veto" and state in ("EFFECTIVE", "EXECUTED")
                                                      and effective_at)
                assert (not found) == bool(expected), (name, state, effective_at, found[:1])
    executed = edit(fixture("surrogate_decision_veto_effective.json"), state="EXECUTED")
    assert_valid(sch, executed)
    assert_refused(sch, edit(executed, effective_at=None), "$.effective_at: expected type string, found null")
    assert_valid(sch, edit(routine, state="EXECUTED", effective_at=None))        # a routine record needs none
    assert len(sch["allOf"]) == 6 and "EXECUTED only with the effective_at" in sch["allOf"][5]["$comment"]
    assert fixture("surrogate_decision_veto_effective.json")["by"] == "kyveto"
    assert_valid(sch, edit(routine, by="kyveto"))
    assert_valid(sch, edit(routine, reason="superseded"))
    assert "reason" not in sch["required"] and "reason" not in routine
    assert_valid(sch, edit(routine, notification={"submitted": False, "ts": None}))


def test_a_job_result_names_a_head_only_when_it_names_a_pull_request():
    sch = schema("job_result")
    done = fixture("job_result_done.json")
    assert done["pr_number"] == 3501 and done["head_sha"]
    assert_valid(sch, edit(done, pr_number=None, head_sha=None))            # done, nothing pushed
    assert_valid(sch, edit(done, pr_number=None))                            # a head without a pull request
    for status in ("done", "failed", "blocked"):
        changed = edit(done, status=status, blocked_reason="why" if status == "blocked" else None)
        assert_refused(sch, edit(changed, head_sha=None), "$.head_sha", "expected type string")
        assert_valid(sch, edit(changed, head_sha=None, pr_number=None))
    reviewer = fixture("job_result_done_reviewer.json")
    assert reviewer["status"] == "done" and reviewer["head_sha"] is None and reviewer["proposed_verdict"]
    assert_valid(sch, edit(reviewer, proposed_verdict=DROP))
    assert "proposed_verdict" not in sch["required"]


# ---- bootstrap launch input (shape only; the launch rules are kyboot's, tested in test_kyboot.py) ---------------
LAUNCH_NEG = [
    ({"schema": "ky.bootstrap_launch_input/2"}, ("$.schema", "must equal")),
    ({"item": "K4-2a"}, ("$.item", "does not match pattern")),
    ({"job_id": "a/b"}, ("$.job_id", "does not match pattern")),
    ({"job_id": ".."}, ("$.job_id", "does not match pattern")),
    ({"kind": "POST-READBACK"}, ("$.kind", "is not one of")),
    ({"kind": "ruling"}, ("$.kind", "is not one of")),
    ({"base_sha": "HEAD"}, ("$.base_sha", "does not match pattern")),
    ({"claude_min_version": "2.1.239"}, ("$.claude_min_version", 'must equal "2.1.296"')),
    ({"model": "claude-haiku-5"}, ("$.model", "is not one of")),
    ({"effort": "max"}, ("$.effort", "is not one of")),
    ({"permission_mode": "dontAsk"}, ("$.permission_mode", "is not one of")),
    ({"permission_mode": DROP}, ("required property 'permission_mode' is missing",)),
    ({"max_turns": 0}, ("$.max_turns", "less than the minimum 1")),
    ({"max_turns": "150"}, ("$.max_turns", "expected type integer")),
    ({"max_turns": 150.0}, ("$.max_turns", "expected type integer")),
    ({"mcp_config_sha256": "x"}, ("$.mcp_config_sha256", "does not match pattern")),
    ({"prompt_sha256": H40}, ("$.prompt_sha256", "does not match pattern")),
    ({"env": []}, ("$.env", "expected type object")),
    ({"extra_lean_flags": ["positional prompt text"]}, ("$.extra_lean_flags[0]", "does not match pattern")),
    ({"extra_lean_flags": ["-p"]}, ("$.extra_lean_flags[0]", "does not match pattern")),
    ({"extra_lean_flags": "--disable-slash-commands"}, ("$.extra_lean_flags", "expected type array")),
    ({"disallowed_tools": ["--model"]}, ("$.disallowed_tools[0]", "does not match pattern")),
    ({"disallowed_tools": [""]}, ("$.disallowed_tools[0]", "does not match pattern")),
    ({"disallowed_tools": [7]}, ("$.disallowed_tools[0]", "expected type string")),
    ({"extra_lean_flags": [7]}, ("$.extra_lean_flags[0]", "expected type string")),
    ({"deadline": ""}, ("$.deadline", "minLength 1")),
    ({"plan_version": "2.3"}, ("$.plan_version", 'must equal "2.7"')),
    ({"role": "builder"}, ("$.role", "is not one of")),
    ({"role": "SURROGATE"}, ("$.role", "is not one of")),
    ({"role": None}, ("$.role", "is not one of")),
    ({"approved_source_commit": "a5c0bef2a"}, ("$.approved_source_commit", "does not match pattern")),
]


@pytest.mark.parametrize("edits,needles", LAUNCH_NEG, ids=[f"{'+'.join(c[0])}={i}" for i, c in enumerate(LAUNCH_NEG)])
def test_bootstrap_launch_input_shape_refusals(edits, needles):
    base = fixture("launch_input.json")
    assert_valid(schema("bootstrap_launch_input"), base)
    assert_refused(schema("bootstrap_launch_input"), edit(base, **edits), *needles)


def test_bootstrap_launch_input_requires_exactly_the_pinned_fields():
    pinned = ["schema", "job_id", "item", "kind", "role", "worktree", "branch", "base_sha", "claude_bin",
              "claude_min_version", "model", "effort", "permission_mode", "max_turns", "mcp_config",
              "mcp_config_sha256", "prompt_path", "prompt_sha256", "card_path", "card_sha256", "packet_path",
              "packet_sha256", "job_scratch", "stdout_path", "stderr_path", "tmp_path", "state_path", "env",
              "extra_lean_flags", "disallowed_tools", "deadline", "plan_version", "approved_source_commit"]
    sch = schema("bootstrap_launch_input")
    assert sorted(sch["required"]) == sorted(pinned)
    assert sorted(sch["properties"]) == sorted(pinned)
    assert sch["properties"]["role"]["enum"] == ["bootstrap-builder", "bootstrap-reviewer", "surrogate", "planner"]
    assert sch["properties"]["plan_version"] == {"const": "2.7"} == schema("packet")["properties"]["plan_version"]
    for role in sch["properties"]["role"]["enum"]:
        assert_valid(sch, edit(fixture("launch_input.json"), role=role))
    # finding N-15: a ruling, a pre-acceptance and an owner-surrogate job have kinds (and turn caps) of their own
    assert sch["properties"]["kind"]["enum"] == ["BUILD", "REWORK", "ARTIFACT", "VERIFY", "PRE-ACCEPT", "RULING",
                                                 "SURROGATE", "PLAN"]
    for kind in sch["properties"]["kind"]["enum"]:
        assert_valid(sch, edit(fixture("launch_input.json"), kind=kind))
        assert f"{kind} " in sch["properties"]["kind"]["description"], kind


# --------------------------------------------------------------------------------------------------------------
# sweeps: every node of every valid fixture, so that no type, emptiness, closure or requirement rule is untested
# --------------------------------------------------------------------------------------------------------------
SAMPLES = {"null": None, "true": True, "false": False, "int": 7, "float": 1.5, "empty-str": "", "str": "x",
           "empty-arr": [], "arr": ["x"], "empty-obj": {}, "obj": {"x": 1}}
CONDITION_NAMES = ["certification", "pins", "regeneration", "pr_dispositions", "coordinator_closure"]

# What ELSE a position accepts besides its fixture value, by sample label ("[]" = any index). A (position,
# sample) pair that is not listed here must be refused: this table is the whole of each schema's leniency.
ACCEPTS = {
    "awaiting": {
        "$.raised_by.role": {"str"}, "$.raised_by.session_id": {"null", "str"}, "$.raised_by.job_id": {"null", "str"},
        "$.item": {"null", "str"}, "$.question": {"str"}, "$.options": {"empty-arr"}, "$.options[].id": {"str"},
        "$.options[].text": {"str"}, "$.recommendation": {"null", "str", "empty-str"},
        "$.evidence": {"empty-arr", "arr"}, "$.evidence[]": {"str", "empty-str"}, "$.deadline": {"null"},
    },
    "surrogate_decision": {
        "$.decision": {"str"}, "$.rationale": {"str"}, "$.evidence": {"empty-arr", "arr"},
        "$.evidence[]": {"str", "empty-str"}, "$.session": {"str"}, "$.target": {"empty-obj", "obj"},
        "$.notification.submitted": {"true", "false"}, "$.notification.ts": {"null", "str", "empty-str"},
        "$.effective_at": {"null"}, "$.reason": {"str", "empty-str"},
    },
    "job_result": {
        "$.job_id": {"str"}, "$.item": {"str"}, "$.branch": {"null", "str"}, "$.head_sha": {"null"},
        "$.pr_number": {"null", "int"}, "$.tests": {"empty-arr"}, "$.tests[].cmd": {"str"}, "$.tests[].exit": {"int"},
        "$.tests[].summary": {"str", "empty-str"}, "$.blocked_reason": {"null", "str", "empty-str"},
        "$.notes": {"str", "empty-str"}, "$.proposed_verdict": {"empty-obj", "obj"},
    },
    "packet": {
        "$.id": {"str"}, "$.routing_reason": {"str"}, "$.needs_chart_data": {"true", "false"},
        "$.spec_sources[].path": {"str"}, "$.spec_sources[].revision": {"str"},
        "$.spec_sources[].section_range": {"str"}, "$.schema_receipt_id": {"str"}, "$.pw_mechanism_version": {"str"},
        "$.release_pins.dash_build": {"str", "int"}, "$.release_pins.registry_revision": {"str", "int"},
        "$.d1_paths": {"arr"}, "$.d1_paths[]": {"str"}, "$.acceptance.command": {"str"},
        "$.acceptance.expected_result": {"str"}, "$.acceptance.negative_cases": {"arr"},
        "$.acceptance.negative_cases[]": {"str"}, "$.test_commits[].path": {"str"},
        "$.expected_failing_assertion": {"str"}, "$.semantic_acceptance": {"str"}, "$.negative_fixtures": {"arr"},
        "$.negative_fixtures[]": {"str"}, "$.intended_schema": {"str", "obj"},
    },
    "release_receipt": dict(
        [("$.release_id", {"str"})] + [(f"$.conditions.{c}.release_id", {"str"}) for c in CONDITION_NAMES] + [
            ("$.conditions.certification.evidence.record_id", {"str"}),
            ("$.conditions.pins.evidence.rebuild_producer", {"str"}),
            ("$.conditions.pins.evidence.rebuild_run", {"str"}),
            ("$.conditions.regeneration.evidence.generator_version", {"str"}),
            ("$.conditions.pr_dispositions.evidence.prs", {"empty-arr"}),
            ("$.conditions.pr_dispositions.evidence.prs[].pr", {"int"}),
            ("$.conditions.pr_dispositions.evidence.prs[].owner", {"str"}),
            ("$.conditions.pr_dispositions.evidence.prs[].re_entry", {"null", "str"}),
            ("$.conditions.coordinator_closure.evidence.handoff_records", {"arr"}),
            ("$.conditions.coordinator_closure.evidence.handoff_records[]", {"str"})]),
    "bootstrap_launch_input": {
        "$.job_id": {"str"}, "$.worktree": {"str"}, "$.branch": {"str"}, "$.claude_bin": {"str"},
        "$.max_turns": {"int"}, "$.mcp_config": {"str"}, "$.prompt_path": {"str"}, "$.card_path": {"str"},
        "$.packet_path": {"str"}, "$.job_scratch": {"str"}, "$.stdout_path": {"str"}, "$.stderr_path": {"str"},
        "$.tmp_path": {"str"}, "$.state_path": {"str"}, "$.env": {"empty-obj", "obj"},
        "$.extra_lean_flags": {"empty-arr"}, "$.disallowed_tools": {"arr"}, "$.deadline": {"str"},
    },
}
# Where one fixture's kind / class / status narrows (or widens) a position: exact path, real indexes.
ACCEPTS_HERE = {
    ("packet_bootstrap.json", "$.id"): set(),                          # must stay KV3-B-*
    ("packet_schema_prerequisite.json", "$.id"): set(),                # must stay KV3-SCHEMA-<n>
    ("packet_bootstrap.json", "$.needs_chart_data"): set(),            # false only
    ("packet_bootstrap.json", "$.schema_receipt_id"): {"null", "str"},
    ("packet_bootstrap.json", "$.pw_mechanism_version"): {"null", "str"},
    ("packet_operation.json", "$.expected_failing_assertion"): set(),  # no invented red test
    ("job_result_done.json", "$.head_sha"): set(),                     # it names a PR ⇒ it names the head
    ("job_result_blocked.json", "$.pr_number"): set(),                 # no head ⇒ no PR number may be added
    ("job_result_failed.json", "$.pr_number"): set(),
    ("job_result_done_reviewer.json", "$.pr_number"): set(),
    ("surrogate_decision_veto_effective.json", "$.effective_at"): set(),   # veto + EFFECTIVE ⇒ an effective time
    ("surrogate_decision_veto.json", "$.target"): set(),                   # veto ⇒ a bound target (kind + fingerprint)
    ("surrogate_decision_veto_effective.json", "$.target"): set(),
    ("job_result_blocked.json", "$.blocked_reason"): {"str"},          # blocked ⇒ a reason
    ("release_receipt_satisfied.json", "$.conditions.pr_dispositions.evidence.prs[1].re_entry"): {"str"},  # parked
}
OPEN = {("bootstrap_launch_input", "$.env"), ("packet", "$.intended_schema"), ("surrogate_decision", "$.target"),
        ("job_result", "$.proposed_verdict")}                                        # contents are not typed here
OPTIONAL_HERE = {("packet_operation.json", "$.original_failing_base"),
                 ("packet_operation.json", "$.expected_failing_assertion"),
                 ("surrogate_decision_hard_stop.json", "$.reason"),
                 ("job_result_done_reviewer.json", "$.proposed_verdict")}
ALL_FIXTURES = [(n, d) for n, docs in VALID.items() for d in docs]


def show(steps, wildcard=False) -> str:
    out = "$"
    for step in steps:
        out += ("[]" if wildcard else f"[{step}]") if isinstance(step, int) else f".{step}"
    return out


def positions(name, value, steps=()):
    yield steps, value
    if (name, show(steps, wildcard=True)) in OPEN:
        return
    children = value.items() if isinstance(value, dict) else enumerate(value) if isinstance(value, list) else ()
    for key, child in children:
        yield from positions(name, child, steps + (key,))


def put(doc, steps, value):
    out = copy.deepcopy(doc)
    if not steps:
        return copy.deepcopy(value)
    node = out
    for step in steps[:-1]:
        node = node[step]
    if value is DROP:
        del node[steps[-1]]
    else:
        node[steps[-1]] = copy.deepcopy(value)
    return out


@pytest.mark.parametrize("name,doc", ALL_FIXTURES)
def test_sweep_every_position_refuses_every_other_type_and_emptiness_it_does_not_declare(name, doc):
    sch, base = schema(name), fixture(doc)
    tried = accepted = 0
    for steps, current in positions(name, base):
        allowed = ACCEPTS_HERE.get((doc, show(steps)), ACCEPTS[name].get(show(steps, wildcard=True), set()))
        for label, sample in SAMPLES.items():
            if kyschema.json_equal(sample, current):
                continue
            found = kyschema.validate(sch, put(base, steps, sample))
            tried += 1
            accepted += not found
            assert (not found) == (label in allowed), \
                f"{doc} {show(steps)} := {label}: expected {'accepted' if label in allowed else 'REFUSED'}; {found[:2]}"
    assert tried >= 100 and accepted >= 1


def test_the_leniency_tables_name_only_positions_that_exist():
    seen = {name: set() for name in ACCEPTS}
    exact = set()
    for name, doc in ALL_FIXTURES:
        for steps, _ in positions(name, fixture(doc)):
            seen[name].add(show(steps, wildcard=True))
            exact.add((doc, show(steps)))
    for name, table in ACCEPTS.items():
        assert set(table) <= seen[name], sorted(set(table) - seen[name])
    assert set(ACCEPTS_HERE) <= exact and OPTIONAL_HERE <= exact
    assert all(labels <= set(SAMPLES) for table in ACCEPTS.values() for labels in table.values())


@pytest.mark.parametrize("name,doc", ALL_FIXTURES)
def test_sweep_every_object_is_closed_and_every_present_key_is_required(name, doc):
    sch, base = schema(name), fixture(doc)
    objects = keys = 0
    for steps, current in positions(name, base):
        if not isinstance(current, dict) or (name, show(steps, wildcard=True)) in OPEN:
            continue
        objects += 1
        where = show(steps + ("zz_unknown",))
        assert_refused(sch, put(base, steps + ("zz_unknown",), 1), f"{where}: additional property is not allowed")
        for key in current:
            found = kyschema.validate(sch, put(base, steps + (key,), DROP))
            optional = (doc, show(steps + (key,))) in OPTIONAL_HERE
            assert (not found) == optional, f"{doc}: dropping {show(steps + (key,))}: {found[:2]}"
            keys += 1
    assert objects >= 1 and keys >= 5


DUPLICATES = [
    ("packet", "packet_feature.json", ("spec_sources",)),
    ("packet", "packet_feature.json", ("test_commits",)),
    ("packet", "packet_bootstrap.json", ("d1_paths",)),
    ("release_receipt", "release_receipt_satisfied.json", ("conditions", "coordinator_closure", "evidence",
                                                           "handoff_records")),
    ("bootstrap_launch_input", "launch_input.json", ("extra_lean_flags",)),
]


@pytest.mark.parametrize("name,doc,steps", DUPLICATES, ids=[f"{d[0]}:{d[2][-1]}" for d in DUPLICATES])
def test_lists_that_enumerate_refuse_a_repeated_entry(name, doc, steps):
    base = fixture(doc)
    node = base
    for step in steps:
        node = node[step]
    assert node, "the fixture list must not be empty"
    assert_refused(schema(name), put(base, steps, node + [node[0]]), show(steps), "are equal")


def test_disallowed_tools_refuse_a_repeated_entry():
    base = fixture("launch_input.json")
    assert_valid(schema("bootstrap_launch_input"), put(base, ("disallowed_tools",), ["Edit", "WebFetch"]))
    assert_refused(schema("bootstrap_launch_input"), put(base, ("disallowed_tools",), ["Edit", "Edit"]),
                   "$.disallowed_tools", "are equal")


DISCRIMINATORS = [
    # (schema, fixture, steps of the discriminating field): dropping it is refused ONCE, for being missing —
    # a conditional must not fire (and complain about another field) when its discriminator is absent
    ("packet", "packet_feature.json", ("kind",)),
    ("packet", "packet_artifact.json", ("kind",)),
    ("surrogate_decision", "surrogate_decision_routine.json", ("class",)),
    ("surrogate_decision", "surrogate_decision_veto.json", ("class",)),
    ("surrogate_decision", "surrogate_decision_veto_effective.json", ("class",)),
    ("surrogate_decision", "surrogate_decision_veto_effective.json", ("state",)),
    ("surrogate_decision", "surrogate_decision_veto.json", ("state",)),
    ("surrogate_decision", "surrogate_decision_hard_stop.json", ("class",)),
    ("job_result", "job_result_blocked.json", ("pr_number",)),
    ("job_result", "job_result_done.json", ("status",)),
    ("job_result", "job_result_blocked.json", ("status",)),
    ("release_receipt", "release_receipt_wait.json", ("conditions", "pins", "status")),
    ("release_receipt", "release_receipt_satisfied.json",
     ("conditions", "pr_dispositions", "evidence", "prs", 0, "disposition")),
]


@pytest.mark.parametrize("name,doc,steps", DISCRIMINATORS, ids=[f"{d[1]}:{d[2][-1]}" for d in DISCRIMINATORS])
def test_a_missing_discriminator_is_one_refusal_and_fires_no_conditional(name, doc, steps):
    found = kyschema.validate(schema(name), put(fixture(doc), steps, DROP))
    assert len(found) == 1 and f"required property '{steps[-1]}' is missing" in found[0], found
