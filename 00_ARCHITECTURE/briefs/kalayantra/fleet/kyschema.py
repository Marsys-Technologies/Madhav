#!/usr/bin/env python3
r"""kyschema.py — a minimal, stdlib-only JSON-Schema validator for the KĀLA-YANTRA v3 fleet schemas.

Relaunch plan v2.7 §14 B-0c (schemas for §8 packets, §10 release receipt, §4a.3 awaiting / surrogate decision,
§6 job result, §7 bootstrap launch input). `jsonschema` is not installed on the campaign host and is not assumed
in CI, so the fleet carries exactly the subset its schemas use. Python >= 3.9, no third-party imports.

Supported keywords — exactly these; any other keyword is a hard error, never silently ignored:
  type (one name or a list) · required · properties · additionalProperties (boolean only) · items (one schema)
  enum · const · pattern · minLength · maxLength · minimum · maximum · minItems · maxItems · uniqueItems
  allOf · anyOf · oneOf · not · if / then / else · $ref (to '#/$defs/<name>' only)
Annotations accepted and ignored: $schema · $id · title · description · $comment; `$defs` only at the root.

Deliberate narrowings (each one refuses more, never less, than the standard):
  * a schema is always an object: the boolean schemas `true` / `false` are refused;
  * "integer" is a JSON number written as an integer: 3 is one, 3.0 is not; booleans are never numbers;
  * enum / const compare JSON values (true is not 1; 1 equals 1.0; objects by key set, arrays by position);
  * `then` / `else` without `if`, a `$ref` cycle that consumes no input, and a `required` name that the same
    schema's `additionalProperties: false` forbids are refused at lint time;
  * documents are loaded strictly: a duplicate object key, NaN or Infinity refuses the document.

pattern is a Python `re` search, made to read a pattern the way ECMA-262 (which the standard names) reads it
without its `u` flag — neither stricter nor laxer where the two languages can be made to agree:
  * `$` matches only at the true end of the string, never before a trailing newline;
  * `\d`, `\w`, `\b` and their negations are the ASCII classes;
  * `\s` is the ECMA-262 white space and line terminator set (tab, LF, VT, FF, CR, space, U+00A0, U+1680,
    U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, U+3000, U+FEFF), inside a character class too, so `[^\s]`
    refuses a no-break space or a line separator exactly as ECMA-262 does; `\S` is its complement outside a
    class and is refused at lint time inside one (it cannot be written there faithfully);
  * an unescaped `.` outside a class matches any character except the four ECMA-262 line terminators (LF, CR,
    U+2028, U+2029).
What is NOT reconciled, and is therefore the pattern author's to avoid: syntax only one of the two languages
has (for example Python's `(?P<name>…)`, `\A` and `\Z`; ECMA-262's `\cX` and `\p{…}`), characters outside the
Basic Multilingual Plane (ECMA-262 without `u` sees two surrogates, Python one character) and case-insensitive
matching (never requested here). A pattern Python cannot compile is refused at lint time, never ignored.

Usage:
  kyschema.py validate <schema.json> <doc.json>
  kyschema.py lint <schema.json>
Exit: 0 valid · 1 the document is refused (one reason per line on stderr: JSON path, reason, schema location)
      2 the schema is refused (unsupported keyword, malformed or unreadable schema) or the command is malformed
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SUPPORTED = ("type", "required", "properties", "additionalProperties", "items", "enum", "const", "pattern",
             "minLength", "maxLength", "minimum", "maximum", "minItems", "maxItems", "uniqueItems",
             "allOf", "anyOf", "oneOf", "not", "if", "then", "else", "$ref")
ANNOTATIONS = ("$schema", "$id", "title", "description", "$comment")
TYPES = ("null", "boolean", "object", "array", "number", "integer", "string")
REF_PREFIX = "#/$defs/"
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\Z")


class SchemaError(ValueError):
    """the schema itself is refused; .findings lists every reason"""

    def __init__(self, findings):
        self.findings = list(findings)
        super().__init__("\n".join(self.findings))


# --------------------------------------------------------------------------------------------------------------
# JSON values
# --------------------------------------------------------------------------------------------------------------
def load_json_text(text: str):
    """strict JSON: duplicate keys, NaN and Infinity are refused (ValueError names the reason)"""
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate key {key!r}")
            out[key] = value
        return out

    def constant(name):
        raise ValueError(f"{name} is not JSON")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def load_json(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as unreadable:
        raise ValueError(f"cannot read {path}: {unreadable}") from None
    try:
        return load_json_text(text)
    except ValueError as bad:
        raise ValueError(f"{path} is not acceptable JSON: {bad}") from None


def type_of(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise TypeError(f"not a JSON value: {type(value).__name__}")


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def json_equal(a, b) -> bool:
    """JSON equality: 1 equals 1.0; true is not 1 (booleans are not numbers here, and the types then differ)"""
    if _is_number(a) and _is_number(b):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(json_equal(a[k], b[k]) for k in a)
    return a == b


def _show(value) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= 120 else text[:117] + "..."


def _child(path: str, key) -> str:
    if isinstance(key, int):
        return f"{path}[{key}]"
    return f"{path}.{key}" if _IDENT.match(key) else f"{path}[{json.dumps(key, ensure_ascii=False)}]"


# ECMA-262 WhiteSpace + LineTerminator, as the body of a Python character class (what `\s` means there)
ECMA_SPACE = "\\t\\n\\x0b\\x0c\\r \\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000\\ufeff"
ECMA_LINE_TERMINATORS = "\\n\\r\\u2028\\u2029"


def compile_pattern(pattern: str):
    r"""Python `re` reading the pattern as ECMA-262 does (see the module docstring): ASCII `\d \w \b`, the
    ECMA-262 set for `\s` / `\S`, `.` stopping at every ECMA-262 line terminator, and every unescaped `$`
    outside a character class anchored at the true end. re.error when it cannot be written faithfully."""
    out, i, in_class = [], 0, False
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\":
            escaped = pattern[i + 1:i + 2]
            if escaped == "s":
                out.append(ECMA_SPACE if in_class else "[" + ECMA_SPACE + "]")
            elif escaped == "S":
                if in_class:
                    raise re.error("\\S inside a character class is not supported (write the class without it)")
                out.append("[^" + ECMA_SPACE + "]")
            else:
                out.append(pattern[i:i + 2])
            i += 2
            continue
        if in_class:
            if ch == "]":
                in_class = False
        elif ch == "[":
            in_class = True
            out.append(ch)
            i += 1
            if pattern[i:i + 1] == "^":
                out.append("^")
                i += 1
            if pattern[i:i + 1] == "]":
                out.append("]")
                i += 1
            continue
        elif ch == "$":
            out.append("\\Z")
            i += 1
            continue
        elif ch == ".":
            out.append("[^" + ECMA_LINE_TERMINATORS + "]")
            i += 1
            continue
        out.append(ch)
        i += 1
    return re.compile("".join(out), re.ASCII)


# --------------------------------------------------------------------------------------------------------------
# lint: the schema itself
# --------------------------------------------------------------------------------------------------------------
def _resolve(ref, root):
    if not isinstance(ref, str) or not ref.startswith(REF_PREFIX) or "/" in ref[len(REF_PREFIX):] \
            or not ref[len(REF_PREFIX):]:
        return None, f"only '#/$defs/<name>' references are supported, found {ref!r}"
    defs = root.get("$defs") if isinstance(root, dict) else None
    name = ref[len(REF_PREFIX):]
    if not isinstance(defs, dict) or name not in defs:
        return None, f"$ref target {ref!r} does not exist"
    return defs[name], None


def _lint_schema(schema, spath, root, out, is_root=False):
    if not isinstance(schema, dict):
        out.append(f"{spath}: a schema must be an object (boolean and array schemas are not supported), "
                   f"found {type_of(schema) if _json_like(schema) else type(schema).__name__}")
        return
    for keyword, value in schema.items():
        here = f"{spath}/{keyword}"
        if keyword in ANNOTATIONS:
            if not isinstance(value, str):
                out.append(f"{spath}: '{keyword}' must be a string")
        elif keyword == "$defs":
            if not is_root:
                out.append(f"{spath}: '$defs' is supported only at the schema root")
            elif not isinstance(value, dict):
                out.append(f"{spath}: '$defs' must be an object of schemas")
            else:
                for name, sub in value.items():
                    _lint_schema(sub, f"{here}/{name}", root, out)
        elif keyword not in SUPPORTED:
            out.append(f"{spath}: unsupported keyword {keyword!r}")
        elif keyword == "type":
            names = value if isinstance(value, list) else [value]
            if not names or len(set(map(str, names))) != len(names):
                out.append(f"{spath}: type must be one type name or a non-empty list of distinct names")
            for name in names:
                if name not in TYPES:
                    out.append(f"{spath}: unknown type {name!r}")
        elif keyword == "required":
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value) \
                    or len(set(value)) != len(value):
                out.append(f"{spath}: required must be an array of distinct strings")
        elif keyword == "properties":
            if not isinstance(value, dict):
                out.append(f"{spath}: properties must be an object of schemas")
            else:
                for name, sub in value.items():
                    _lint_schema(sub, f"{here}/{name}", root, out)
        elif keyword == "additionalProperties":
            if not isinstance(value, bool):
                out.append(f"{spath}: additionalProperties must be a boolean (the schema form is not supported)")
        elif keyword in ("items", "not", "if", "then", "else"):
            _lint_schema(value, here, root, out)
        elif keyword == "enum":
            if not isinstance(value, list) or not value:
                out.append(f"{spath}: enum must be a non-empty array")
        elif keyword == "const":
            pass
        elif keyword == "pattern":
            if not isinstance(value, str):
                out.append(f"{spath}: pattern must be a string")
            else:
                try:
                    compile_pattern(value)
                except re.error as bad:
                    out.append(f"{spath}: pattern does not compile ({bad}): {value!r}")
        elif keyword in ("minLength", "maxLength", "minItems", "maxItems"):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                out.append(f"{spath}: {keyword} must be a non-negative integer")
        elif keyword in ("minimum", "maximum"):
            if not _is_number(value):
                out.append(f"{spath}: {keyword} must be a number")
        elif keyword == "uniqueItems":
            if not isinstance(value, bool):
                out.append(f"{spath}: uniqueItems must be a boolean")
        elif keyword in ("allOf", "anyOf", "oneOf"):
            if not isinstance(value, list) or not value:
                out.append(f"{spath}: {keyword} must be a non-empty array of schemas")
            else:
                for index, sub in enumerate(value):
                    _lint_schema(sub, f"{here}/{index}", root, out)
        elif keyword == "$ref":
            _, problem = _resolve(value, root)
            if problem:
                out.append(f"{spath}: {problem}")
    for branch in ("then", "else"):
        if branch in schema and "if" not in schema:
            out.append(f"{spath}: '{branch}' without 'if' would never be applied")
    if schema.get("additionalProperties") is False and isinstance(schema.get("required"), list):
        declared = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        for name in schema["required"]:
            if isinstance(name, str) and name not in declared:
                out.append(f"{spath}: required property {name!r} is not declared in properties although "
                           f"additionalProperties is false (no document could satisfy both)")


def _json_like(value) -> bool:
    return value is None or isinstance(value, (bool, int, float, str, list, dict))


def _in_place_targets(schema, root):
    """schemas applied to the SAME instance as `schema` (the edges along which a $ref cycle never terminates)"""
    if not isinstance(schema, dict):
        return
    if "$ref" in schema:
        target, problem = _resolve(schema["$ref"], root)
        if not problem:
            yield schema["$ref"], target
    for keyword in ("allOf", "anyOf", "oneOf"):
        if isinstance(schema.get(keyword), list):
            for sub in schema[keyword]:
                yield None, sub
    for keyword in ("not", "if", "then", "else"):
        if keyword in schema:
            yield None, schema[keyword]


def _lint_cycles(root, out):
    if not isinstance(root, dict) or not isinstance(root.get("$defs"), dict):
        return
    reported = set()

    def walk(schema, trail):
        for ref, target in _in_place_targets(schema, root):
            if ref is not None:
                if ref in trail:
                    cycle = " -> ".join(trail[trail.index(ref):] + [ref])
                    key = frozenset(trail[trail.index(ref):])
                    if key not in reported:
                        reported.add(key)
                        out.append(f"#: reference cycle that consumes no input: {cycle}")
                    continue
                walk(target, trail + [ref])
            else:
                walk(target, trail)

    for name, sub in root["$defs"].items():
        walk(sub, [REF_PREFIX + name])


def lint(schema) -> list:
    """every reason this schema is refused; [] when it uses only the supported subset correctly"""
    out: list = []
    _lint_schema(schema, "#", schema, out, is_root=True)
    if not out:
        _lint_cycles(schema, out)
    return out


# --------------------------------------------------------------------------------------------------------------
# validate: a document against a linted schema
# --------------------------------------------------------------------------------------------------------------
def _type_matches(value, name) -> bool:
    actual = type_of(value)
    return actual == name or (name == "number" and actual == "integer")


def _check(schema, value, ipath, spath, root, out):
    def fail(keyword, reason):
        out.append(f"{ipath}: {reason} (schema {spath}/{keyword})")

    if "$ref" in schema:
        target, _ = _resolve(schema["$ref"], root)
        _check(target, value, ipath, f"{spath}/$ref({schema['$ref'][len(REF_PREFIX):]})", root, out)
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_matches(value, name) for name in names):
            fail("type", f"expected type {' or '.join(names)}, found {type_of(value)}")
    if "enum" in schema and not any(json_equal(value, option) for option in schema["enum"]):
        fail("enum", f"{_show(value)} is not one of {_show(schema['enum'])}")
    if "const" in schema and not json_equal(value, schema["const"]):
        fail("const", f"must equal {_show(schema['const'])}, found {_show(value)}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            fail("minLength", f"{_show(value)} is shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            fail("maxLength", f"{_show(value)} is longer than maxLength {schema['maxLength']}")
        if "pattern" in schema and not compile_pattern(schema["pattern"]).search(value):
            fail("pattern", f"{_show(value)} does not match pattern {schema['pattern']!r}")
    if _is_number(value):
        if "minimum" in schema and value < schema["minimum"]:
            fail("minimum", f"{_show(value)} is less than the minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            fail("maximum", f"{_show(value)} is greater than the maximum {schema['maximum']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            fail("minItems", f"{len(value)} item(s), fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            fail("maxItems", f"{len(value)} item(s), more than maxItems {schema['maxItems']}")
        if schema.get("uniqueItems"):
            for i in range(len(value)):
                for j in range(i + 1, len(value)):
                    if json_equal(value[i], value[j]):
                        fail("uniqueItems", f"items [{i}] and [{j}] are equal")
        if "items" in schema:
            for index, element in enumerate(value):
                _check(schema["items"], element, _child(ipath, index), f"{spath}/items", root, out)
    if isinstance(value, dict):
        for name in schema.get("required", ()):
            if name not in value:
                fail("required", f"required property {name!r} is missing")
        declared = schema.get("properties", {})
        for name, sub in declared.items():
            if name in value:
                _check(sub, value[name], _child(ipath, name), f"{spath}/properties/{name}", root, out)
        if schema.get("additionalProperties") is False:
            for name in value:
                if name not in declared:
                    out.append(f"{_child(ipath, name)}: additional property is not allowed "
                               f"(schema {spath}/additionalProperties)")

    for index, sub in enumerate(schema.get("allOf", ())):
        _check(sub, value, ipath, f"{spath}/allOf/{index}", root, out)
    if "anyOf" in schema:
        attempts = []
        for index, sub in enumerate(schema["anyOf"]):
            found: list = []
            _check(sub, value, ipath, f"{spath}/anyOf/{index}", root, found)
            attempts.append(found)
        if all(attempts):
            detail = " | ".join(f"[{i}] {found[0]}" for i, found in enumerate(attempts))
            fail("anyOf", f"matches none of the {len(attempts)} anyOf alternatives: {detail}")
    if "oneOf" in schema:
        attempts = []
        for index, sub in enumerate(schema["oneOf"]):
            found = []
            _check(sub, value, ipath, f"{spath}/oneOf/{index}", root, found)
            attempts.append(found)
        matched = sum(1 for found in attempts if not found)
        if matched != 1:
            fail("oneOf", f"matches {matched} of the {len(attempts)} oneOf alternatives (exactly one is required)")
    if "not" in schema:
        found = []
        _check(schema["not"], value, ipath, f"{spath}/not", root, found)
        if not found:
            fail("not", f"must not match the 'not' schema {_show(schema['not'])}")
    if "if" in schema:
        found = []
        _check(schema["if"], value, ipath, f"{spath}/if", root, found)
        branch = "else" if found else "then"
        if branch in schema:
            _check(schema[branch], value, ipath, f"{spath}/{branch}", root, out)


def validate(schema, document) -> list:
    """every reason `document` is refused by `schema` ([] = valid); SchemaError when the schema is refused"""
    findings = lint(schema)
    if findings:
        raise SchemaError(findings)
    out: list = []
    _check(schema, document, "$", "#", schema, out)
    return out


# --------------------------------------------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------------------------------------------
USAGE = "usage: kyschema.py validate <schema.json> <doc.json> | kyschema.py lint <schema.json>"


def _load_schema(path):
    try:
        schema = load_json(path)
    except ValueError as bad:
        return None, [str(bad)]
    return schema, lint(schema)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) == 2 and argv[0] == "lint":
        _, findings = _load_schema(argv[1])
        if findings:
            print(f"SCHEMA REFUSED {argv[1]}\n" + "\n".join(findings), file=sys.stderr)
            return 2
        print(f"SCHEMA-OK {argv[1]}")
        return 0
    if len(argv) == 3 and argv[0] == "validate":
        schema, findings = _load_schema(argv[1])
        if findings:
            print(f"SCHEMA REFUSED {argv[1]}\n" + "\n".join(findings), file=sys.stderr)
            return 2
        try:
            document = load_json(argv[2])
        except ValueError as bad:
            print(f"REFUSED {argv[2]}\n{bad}", file=sys.stderr)
            return 1
        errors = validate(schema, document)
        if errors:
            print(f"REFUSED {argv[2]} against {argv[1]}\n" + "\n".join(errors), file=sys.stderr)
            return 1
        print(f"SCHEMA-VALID {argv[2]} against {argv[1]} "
              f"(shape only; cross-field rules named in the schema's descriptions are not checked here)")
        return 0
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
