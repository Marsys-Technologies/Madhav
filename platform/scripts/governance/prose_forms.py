"""prose_forms.py: the pure helpers of the FORM-GAP declaration forms (SS rulings N-191 and N-192, 2026-10-07).

Fourteen assets could not be declared TRUE because the census engine had no CHECKED form for what they hold. Every form added here is verified against the data, the schema or the committed
source; none trusts a declaration (earned-signal rule: a signal without a detector is null, never green). This module holds only the PURE parts (no database, no census state); the
validators, the live reads and the graders live in `asset_census.py` (one contiguous FORM-GAP block) and call into this file.

  1. run-stamp text column   : a TEXT column holding the orchestrator run id (`build_id TEXT`): every value must have the canonical run-id shape (a lower-case uuid, what `str(build_runs.id)`
                               yields) AND be a run id of THIS asset (build_run_assets / asset_provenance_receipts). `RUN_STAMP_RE`.
  2. scaled value cap        : a closed vocabulary may hold up to VALUES_HARD_CAP values; the live read of its DISTINCT values is bounded by `values_cap(declared count)`. `values_from` names the
                               committed constant that holds the vocabulary (resolved by AST, no code is run). `resolve_values_from`.
  3. scaled leaf-pattern cap : a json(b) closure may declare up to LEAF_PATTERNS_HARD_CAP leaf patterns. `leaf_pattern_cap`.
  5. templated closure       : a pointer text (`ga_dashas:{chart_id}:{system}`) built from a fixed template whose chart-id placeholder is bound at MEASURE time to the measured chart id and whose
                               other placeholders are closed sets or named classes. `compile_templates`.
  6. curated corpus          : a hand-curated sentence corpus pinned by count and sha256 digest. `corpus_digest`, `normalise_sentence`.

The regular expressions this module builds are valid, and mean the same, in Python `re` and in PostgreSQL ARE (no backslash, no lookaround, no named group): the census reads the data with the
PostgreSQL form and the tests compare the two.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path

# ───────────────────────────── 2 / 3: caps that scale with the real count ─────────────────────────────
VALUES_BASE_CAP = 300           # the old fixed cap: the floor of the scaled cap
VALUES_HARD_CAP = 5000          # the bound: past it a list is a corpus, not a vocabulary (declare it by reference to its committed source, or it is not a closed set)
VALUES_HEADROOM = 1.25          # the live DISTINCT read may exceed the declared count by this factor before it is "more than the declaration can hold"
LEAF_PATTERNS_BASE_CAP = 8      # the old fixed cap
LEAF_PATTERNS_HARD_CAP = 64     # the bound: a record with more distinct string-leaf paths is a document, not a closed record
LEAF_PATTERNS_HEADROOM = 1.25


def scaled_cap(n: int, base: int, hard: int, headroom: float) -> int:
    """min(max(ceil(n * headroom), base), hard): the cap that grows with the real count `n`, never below `base`, never above `hard`."""
    return min(max(int(math.ceil(n * headroom)), base), hard)


def values_cap(n_declared: int) -> int:
    """The cap on the DISTINCT values one closed column may be READ with (declared count x 1.25, at least 300, at most 5000): the live read is `SELECT DISTINCT ... LIMIT cap + 1`."""
    return scaled_cap(n_declared, VALUES_BASE_CAP, VALUES_HARD_CAP, VALUES_HEADROOM)


def leaf_pattern_cap(n_declared: int) -> int:
    """The cap on the leaf patterns of one json(b) column (declared count x 1.25, at least 8, at most 64)."""
    return scaled_cap(n_declared, LEAF_PATTERNS_BASE_CAP, LEAF_PATTERNS_HARD_CAP, LEAF_PATTERNS_HEADROOM)


# ───────────────────────────── shapes shared by the forms ─────────────────────────────
RUN_STAMP_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"      # str(uuid): what the orchestrator stamps (build_runs.id is a UUID; ctx.build_id = str(run id))
UUID_ANY_RE = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
_UUID_ANY = re.compile(UUID_ANY_RE)
_CANON_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

# the characters a template literal / a placeholder value may hold: each non-alphanumeric one is rendered as a one-character bracket expression ([:]), so the regex needs no backslash
_TEMPLATE_SAFE_PUNCT = " _:@=,.;/#%&+~|-()$*?!<>'\u2192"      # includes the quote (the census doubles it in a SQL literal) and the right arrow of the nakshatra matrix pointers
_PLACEHOLDER_NAME = re.compile(r"[a-z][a-z0-9_]{0,31}")
_PH_TOKEN = re.compile(r"\{([^{}]*)\}")
CHART_PLACEHOLDER = "chart_id"
TEMPLATE_CLASSES = {
    "int": "[0-9]+",
    "ident": "[a-z][a-z0-9]{0,23}(?:_[0-9]{1,6})?",                      # re-review fix: ONE lower-case word with an optional numeric suffix: any multi-word token (Sun_is_strong, a sentence joined by underscores) must be declared as a values list
    "name": "[A-Za-z][A-Za-z0-9]{0,23}",                                  # ONE word: a multi-word name is a declared closed set, never a pattern
    "decimal": "-?[0-9]+(?:[.][0-9]+)?",
    "iso_date": "[0-9]{4}-[0-9]{2}-[0-9]{2}",
    "hex64": "[0-9a-f]{64}",                                               # N-233: a lower-case sha256 hex digest (bg_texts content_sha256 = hashlib.sha256(...).hexdigest())
}
MAX_TEMPLATES = 32
MAX_TEMPLATE_CHARS = 240
MAX_PLACEHOLDER_VALUES = 200
MAX_REGEX_CHARS = 60_000


SENTENCE_WORDS = 6


def sentence_vocabulary_problem(values) -> str | None:
    """None unless MORE THAN HALF of the distinct values of a closed vocabulary are sentences of SENTENCE_WORDS or more words (re-review fix: such a column holds hand-typed prose, which is pinned as a curated
    corpus by count and digest, not declared as a closed word list)."""
    vals = [v for v in (values or []) if isinstance(v, str)]
    if len(vals) < 2:
        return None
    n = sum(1 for v in vals if len(v.split()) >= SENTENCE_WORDS)
    if n * 2 > len(vals):
        return f"{n} of its {len(vals)} values are sentences of {SENTENCE_WORDS} or more words"
    return None


def _lit_ok(s: str) -> bool:
    return bool(s) and all((ch.isascii() and ch.isalnum()) or ch in _TEMPLATE_SAFE_PUNCT for ch in s)


def _lit_regex(s: str) -> str:
    """A literal as a regex fragment valid in Python re and PostgreSQL ARE: alphanumerics and `_` stay, every other (whitelisted) character becomes `[c]`."""
    out = []
    for ch in s:
        out.append(ch if (ch.isalnum() or ch == "_") else "[" + ch + "]")
    return "".join(out)


def parse_template(template: str):
    """A template as parts: [("lit", text) | ("ph", name)]. Raises ValueError with the reason when it is not a sound template (an unknown character, an unbalanced brace, an empty
    placeholder, a uuid-shaped literal: the chart id must never be written into the declaration)."""
    if not isinstance(template, str) or not template or len(template) > MAX_TEMPLATE_CHARS:
        raise ValueError(f"a template is a non-empty string of at most {MAX_TEMPLATE_CHARS} characters")
    if _UUID_ANY.search(template):
        raise ValueError("a template holds a uuid-shaped literal: write the chart id as the placeholder {chart_id}, never as a value")
    parts, pos = [], 0
    for m in _PH_TOKEN.finditer(template):
        lit = template[pos:m.start()]
        if lit:
            parts.append(("lit", lit))
        name = m.group(1)
        if not _PLACEHOLDER_NAME.fullmatch(name):
            raise ValueError(f"placeholder {{{name}}} is not a lower-case identifier of at most 32 characters")
        parts.append(("ph", name))
        pos = m.end()
    tail = template[pos:]
    if tail:
        parts.append(("lit", tail))
    for kind, text in parts:                       # a brace left in a literal part is not a complete {placeholder}: it is outside the whitelist below
        if kind == "lit" and not _lit_ok(text):
            bad = sorted({ch for ch in text if not ((ch.isascii() and ch.isalnum()) or ch in _TEMPLATE_SAFE_PUNCT)})
            raise ValueError(f"a template literal may hold only ASCII letters, digits and {_TEMPLATE_SAFE_PUNCT!r} (found {bad})")
    return parts


SEQUENCE_FIELDS = ("values", "join", "min", "max")
MAX_SEQUENCE_ITEMS = 8


def placeholder_value_problem(spec) -> str | None:
    """None when `spec` is a sound placeholder spec: exactly one of {values: [1..MAX_PLACEHOLDER_VALUES distinct whitelisted strings, none uuid-shaped]}, {class: one of TEMPLATE_CLASSES} or a
    SEQUENCE {values, join, min, max}: min..max (1..MAX_SEQUENCE_ITEMS) of those values joined by one separator character (a dash-joined lord chain such as `Jupiter-Saturn`)."""
    if isinstance(spec, dict) and "join" in spec:
        if set(spec) != set(SEQUENCE_FIELDS):
            return f"a sequence spec is exactly {list(SEQUENCE_FIELDS)}"
        j, lo, hi = spec["join"], spec["min"], spec["max"]
        if not (isinstance(j, str) and len(j) == 1 and j in _TEMPLATE_SAFE_PUNCT.replace(" ", "")):
            return "join must be one separator character"
        if not (all(isinstance(x, int) and not isinstance(x, bool) for x in (lo, hi)) and 1 <= lo <= hi <= MAX_SEQUENCE_ITEMS):
            return f"min and max must be integers with 1 <= min <= max <= {MAX_SEQUENCE_ITEMS}"
        bad = placeholder_value_problem({"values": spec["values"]})
        if bad:
            return bad
        if any(j in v for v in spec["values"]):
            return "a sequence value may not contain its own separator"
        return None
    if not isinstance(spec, dict) or len(spec) != 1:
        return "a placeholder spec is exactly one of {values: [...]}, {class: <name>} or a sequence {values, join, min, max}"
    if "class" in spec:
        if spec["class"] not in TEMPLATE_CLASSES:
            return f"class must be one of {sorted(TEMPLATE_CLASSES)}"
        return None
    vals = spec.get("values")
    if not (isinstance(vals, list) and 1 <= len(vals) <= MAX_PLACEHOLDER_VALUES and len(set(vals)) == len(vals)):
        return f"values must be 1 to {MAX_PLACEHOLDER_VALUES} distinct strings"
    for v in vals:
        if not (isinstance(v, str) and _lit_ok(v) and len(v) <= 80):
            return f"value {v!r} is not a short string of ASCII letters, digits and {_TEMPLATE_SAFE_PUNCT!r}"
        if _UUID_ANY.search(v):
            return f"value {v!r} is uuid-shaped: a placeholder value may never carry a chart id"
    return None


def templates_problem(templates, placeholders) -> str | None:
    """None when `templates` (a list of template strings) and `placeholders` ({name: spec}) agree: every non-chart placeholder named in a template has a sound spec, no spec is unused, the chart
    placeholder has no spec (it is bound at measure time), and the compiled regex is bounded. Pure; the census validator calls it."""
    if not (isinstance(templates, list) and 1 <= len(templates) <= MAX_TEMPLATES and len(set(templates)) == len(templates)):
        return f"templates must be 1 to {MAX_TEMPLATES} distinct strings"
    if not isinstance(placeholders, dict):
        return "placeholders must be an object {name: {values: [...]} | {class: name}} ({} when the templates name only {chart_id})"
    used = set()
    for t in templates:
        try:
            parts = parse_template(t)
        except ValueError as exc:
            return f"template {t!r}: {exc}"
        used |= {n for k, n in parts if k == "ph"}
    if CHART_PLACEHOLDER in placeholders:
        return f"{{{CHART_PLACEHOLDER}}} is bound to the measured chart at measure time: it takes no spec"
    need = used - {CHART_PLACEHOLDER}
    if need != set(placeholders):
        return f"placeholders must describe exactly the placeholders the templates use ({sorted(need)}), got {sorted(placeholders)}"
    for name, spec in placeholders.items():
        bad = placeholder_value_problem(spec)
        if bad:
            return f"placeholder {{{name}}}: {bad}"
    try:
        compile_templates(templates, placeholders, "00000000-0000-0000-0000-000000000000")
    except ValueError as exc:
        return str(exc)
    return None


def compile_templates(templates, placeholders, chart_id: str) -> str:
    """The ONE regex (anchored, alternation of the templates) a value must match. `chart_id` replaces {chart_id}: it must be a canonical uuid. Raises ValueError otherwise or when too long."""
    if not (isinstance(chart_id, str) and _CANON_UUID.fullmatch(chart_id)):
        raise ValueError("the measured chart id is not a canonical lower-case uuid")
    alts = []
    for t in templates:
        buf = []
        for kind, text in parse_template(t):
            if kind == "lit":
                buf.append(_lit_regex(text))
            elif text == CHART_PLACEHOLDER:
                buf.append(_lit_regex(chart_id))
            else:
                spec = placeholders[text]
                if "class" in spec:
                    buf.append("(?:" + TEMPLATE_CLASSES[spec["class"]] + ")")
                elif "join" in spec:
                    one = "(?:" + "|".join(_lit_regex(v) for v in spec["values"]) + ")"
                    buf.append(one + "(?:" + _lit_regex(spec["join"]) + one + "){" + str(spec["min"] - 1) + "," + str(spec["max"] - 1) + "}")
                else:
                    buf.append("(?:" + "|".join(_lit_regex(v) for v in spec["values"]) + ")")
        alts.append("".join(buf))
    rx = "^(?:" + "|".join(alts) + ")$"
    if len(rx) > MAX_REGEX_CHARS:
        raise ValueError(f"the compiled template pattern is {len(rx)} characters (cap {MAX_REGEX_CHARS}): declare fewer or smaller closed sets")
    return rx


def compile_each(templates, placeholders, chart_id: str) -> list:
    """[(prefix, regex)] for every template: `prefix` is the template's leading LITERAL (up to its first placeholder, up to the first placeholder or the whole string) and `regex` the anchored pattern of that ONE
    template. The census reads a column as `(starts_with(v, prefix) AND v ~ regex) OR ...`: the cheap prefix test keeps the regex engine off every template but the right one (an alternation of all of them
    costs several times as much per row). A value matches the set iff it matches any one of them: exactly what the union pattern of `compile_templates` says."""
    out = []
    for t in templates:
        parts = parse_template(t)
        prefix = parts[0][1] if parts and parts[0][0] == "lit" else ""
        out.append((prefix, compile_templates([t], placeholders, chart_id)))
    return out


def template_matches(rx: str, value: str) -> bool:
    """The Python side of the pattern (the census reads with PostgreSQL's `~`; the tests compare the two)."""
    return re.fullmatch(rx[1:-1], value) is not None


def carries_other_chart_id(value: str, chart_id: str) -> bool:
    """True when `value` holds a uuid-shaped token other than `chart_id` (a value must never name another chart)."""
    return any(m.group(0).lower() != chart_id.lower() for m in _UUID_ANY.finditer(value))


# ───────────────────────────── 6: the curated corpus ─────────────────────────────
CORPUS_MAX_COUNT = 5000
CORPUS_COVERS = ("constant_write", "literal_fallback")


def normalise_sentence(s: str) -> str:
    """Unicode NFC, every run of whitespace collapsed to one space, trimmed: the form a corpus sentence is digested in (so a re-flowed or re-encoded line is not drift, an edited word is)."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


def corpus_digest(sentences) -> str:
    """sha256 over the JSON array (ensure_ascii False, compact separators) of the normalised sentences in code-point order, duplicates kept. The digest of the empty corpus is defined (zero sentences)."""
    norm = sorted(normalise_sentence(s) for s in sentences)
    return hashlib.sha256(json.dumps(norm, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


# ───────────────────────────── 2: values_from (a vocabulary by reference to its committed source) ─────────────────────────────
VALUES_FROM_FIELDS = ("file", "constant", "field")
_SOURCE_PREFIX = "platform/python-sidecar/"
_CONST_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}")
_SRC_CACHE: dict = {}


def values_from_shape_problem(spec) -> str | None:
    """Shape only: exactly {file: 'platform/python-sidecar/....py', constant: <identifier>, field?: <key | index>}."""
    if not isinstance(spec, dict) or not {"file", "constant"} <= set(spec) or set(spec) - set(VALUES_FROM_FIELDS):
        return f"a source reference is an object with file, constant and an optional field (got {sorted(spec) if isinstance(spec, dict) else spec!r})"
    bad = _file_problem(spec["file"])
    if bad:
        return bad
    if not (isinstance(spec["constant"], str) and _CONST_NAME.fullmatch(spec["constant"])):
        return "constant must be a module-level name"
    fld = spec.get("field")
    if fld is not None and not ((isinstance(fld, str) and _CONST_NAME.fullmatch(fld)) or (isinstance(fld, int) and not isinstance(fld, bool) and 0 <= fld < 32)):
        return "field must be null, a key name or a small index"
    return None


def _file_problem(f) -> str | None:
    if not (isinstance(f, str) and f.startswith(_SOURCE_PREFIX) and f.endswith(".py") and ".." not in f.split("/") and "\\" not in f and len(f) <= 200):
        return f"file must be a repo-relative path under {_SOURCE_PREFIX} ending in .py"
    return None


SEED_FIELDS = ("file", "constant", "field", "constants", "key", "overlay")
OVERLAY_FIELDS = ("file", "removed", "edits", "id_key", "apply_function", "apply_sha256")


def seed_shape_problem(spec) -> str | None:
    """Shape of a curated-corpus `seed`: either a literal constant ({file, constant, field?}: `values_from_shape_problem`) or the per-key plain literals of several module-level constants
    ({file, constants: [names], key: <dict key>}: every string literal that is the value of `key` in a dict display / dict(...) call inside those constants; composed values are not read)."""
    if isinstance(spec, dict) and "constants" in spec:
        if set(spec) not in ({"file", "constants", "key"}, {"file", "constants", "key", "overlay"}):
            return "a per-key seed is exactly {file, constants, key} (plus an optional overlay)"
        if "overlay" in spec:
            ov = spec["overlay"]
            if not (isinstance(ov, dict) and set(ov) == set(OVERLAY_FIELDS)):
                return f"an overlay is exactly {list(OVERLAY_FIELDS)}"
            bad = _file_problem(ov["file"])
            if bad:
                return f"overlay.{bad}"
            if not all(isinstance(ov[k], str) and _CONST_NAME.fullmatch(ov[k]) for k in ("removed", "edits", "id_key", "apply_function")):
                return "overlay.removed, overlay.edits, overlay.apply_function and overlay.id_key must be a module-level name / a dict key name"
            if not (isinstance(ov["apply_sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", ov["apply_sha256"])):
                return "overlay.apply_sha256 must be the 64-hex sha256 of the normalised source of the overlay's apply function"
        bad = _file_problem(spec["file"])
        if bad:
            return bad
        cs = spec["constants"]
        if not (isinstance(cs, list) and 1 <= len(cs) <= 16 and len(set(cs)) == len(cs) and all(isinstance(c, str) and _CONST_NAME.fullmatch(c) for c in cs)):
            return "constants must be 1 to 16 distinct module-level names"
        if not (isinstance(spec["key"], str) and _CONST_NAME.fullmatch(spec["key"])):
            return "key must be a dict key name"
        return None
    return values_from_shape_problem(spec)


def _literal_of(node):
    """`ast.literal_eval` of a node, also through one `frozenset(...)` / `set(...)` / `tuple(...)` / `list(...)` / `sorted(...)` wrapper of a literal; ValueError when it is not a literal."""
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        pass
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("frozenset", "set", "tuple", "list", "sorted")
            and len(node.args) == 1 and not node.keywords):
        try:
            return list(ast.literal_eval(node.args[0]))
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError) as exc:
            raise ValueError(f"the constant is not a plain literal (a wrapped value is not): {exc}") from exc
    raise ValueError("the constant is not a plain literal (a comprehension, a call, an f-string or a name cannot be read without running code)")


def resolve_source_items(root: Path, spec) -> list:
    """The list of items (strings, or dict / tuple elements reduced by `field`) a committed module-level literal holds, in source order. Reads the file's AST: NO code is imported or run. Raises ValueError
    with the reason when the file is missing, the constant is absent or assigned more than once, or is not a plain literal."""
    bad = values_from_shape_problem(spec)
    if bad:
        raise ValueError(bad)
    p = (Path(root) / spec["file"]).resolve()
    try:
        p.relative_to(Path(root).resolve())
    except ValueError as exc:
        raise ValueError("the source file resolves outside the repository") from exc
    if not p.is_file():
        raise ValueError(f"source file {spec['file']} does not exist")
    st = p.stat()
    key = (str(p), st.st_mtime_ns, st.st_size, spec["constant"], spec.get("field"))
    if key in _SRC_CACHE:
        return list(_SRC_CACHE[key])
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    except (SyntaxError, UnicodeDecodeError, OSError) as exc:
        raise ValueError(f"source file {spec['file']} cannot be parsed: {exc}") from exc
    found = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == spec["constant"] for t in node.targets):
            found.append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == spec["constant"] and node.value is not None:
            found.append(node.value)
    if len(found) != 1:
        raise ValueError(f"{spec['constant']} is assigned {len(found)} time(s) at the top level of {spec['file']} (exactly one literal assignment is required)")
    obj = _literal_of(found[0])
    fld = spec.get("field")
    if isinstance(obj, dict) and fld is None:
        items = list(obj.keys())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        items = list(obj)
    else:
        raise ValueError(f"{spec['constant']} is a {type(obj).__name__}: expected a list / tuple / set of items, or a dict (its keys are read)")
    out = []
    for it in items:
        if fld is None and isinstance(it, (list, tuple)) and it and all(isinstance(x, str) for x in it):
            out.extend(it)                                        # a row of strings (one level): its elements are values
            continue
        if fld is None:
            val = it
        elif isinstance(it, dict) and isinstance(fld, str):
            if fld not in it:
                raise ValueError(f"an item of {spec['constant']} has no key {fld!r}")
            val = it[fld]
        elif isinstance(it, (list, tuple)) and isinstance(fld, int):
            if fld >= len(it):
                raise ValueError(f"an item of {spec['constant']} has no index {fld}")
            val = it[fld]
        else:
            raise ValueError(f"field {fld!r} does not apply to an item of type {type(it).__name__}")
        if not isinstance(val, str):
            raise ValueError(f"an item of {spec['constant']} is {type(val).__name__}, not a string")
        out.append(val)
    _SRC_CACHE[key] = list(out)
    return out


def resolve_values_from(root: Path, spec) -> list[str]:
    """The closed vocabulary a `values_from` reference names: the DISTINCT non-blank strings of the committed source, sorted. Two forms: a literal constant ({file, constant, field?}: a list / tuple / set of
    strings, of dicts or tuples read by `field`, or a dict whose keys are read; an item that is itself a list / tuple of strings is flattened one level when no `field` is given), or the per-key literals of
    several constants ({file, constants, key}, `resolve_seed_sentences`: every string literal assigned to `key` in a dict display / dict(...) call, a list / tuple value contributing its string elements).
    Raises ValueError (the reason) when it cannot be resolved, is empty, holds a blank / control-bearing / over-long / backslash value, or has more than VALUES_HARD_CAP distinct values."""
    vals = resolve_seed_sentences(root, spec)
    distinct = sorted(set(vals))
    if not distinct:
        raise ValueError(f"{spec.get('constant') or spec.get('constants')} holds no value")
    if len(distinct) > VALUES_HARD_CAP:
        raise ValueError(f"{spec.get('constant') or spec.get('constants')} holds {len(distinct)} distinct values (the bound is {VALUES_HARD_CAP})")
    for v in distinct:
        if not (v.strip() and len(v) <= 200 and "\\" not in v and not any(unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") for ch in v)):
            raise ValueError(f"{spec.get('constant') or spec.get('constants')} holds a value that cannot be a closed-vocabulary value (blank, over 200 characters, a backslash or a control character): {v[:40]!r}")
    return distinct


def _top_level_value(tree, name: str, where: str):
    found = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            found.append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name and node.value is not None:
            found.append(node.value)
    if len(found) != 1:
        raise ValueError(f"{name} is assigned {len(found)} time(s) at the top level of {where} (exactly one assignment is required)")
    return found[0]


def _literal_strings(v) -> list[str]:
    """The string literals a value expression is made of: one string Constant, or the string Constant elements of a list / tuple / set display (a composed or named element is not a literal and is skipped)."""
    if isinstance(v, ast.Constant) and isinstance(v.value, str):
        return [v.value]
    if isinstance(v, (ast.List, ast.Tuple, ast.Set)):
        return [e.value for e in v.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return []


def resolve_seed_sentences(root: Path, spec) -> list[str]:
    """The sentences a curated-corpus `seed` names, in source order, duplicates kept (the corpus is a multiset). Literal form: `resolve_source_items`. Per-key form ({file, constants, key}): every
    string literal that is the value of `key` in a dict display or a dict(...) call anywhere inside the named constants' assigned expressions; a value that is not a plain string literal (an f-string, a
    name, a concatenation) is NOT part of the corpus (it is composed, never curated). No code is imported or run. Raises ValueError with the reason."""
    bad = seed_shape_problem(spec)
    if bad:
        raise ValueError(bad)
    if "constants" not in spec:
        return resolve_source_items(root, spec)
    if "overlay" in spec:
        return _resolve_overlay_sentences(root, spec)
    p = (Path(root) / spec["file"]).resolve()
    try:
        p.relative_to(Path(root).resolve())
    except ValueError as exc:
        raise ValueError("the source file resolves outside the repository") from exc
    if not p.is_file():
        raise ValueError(f"source file {spec['file']} does not exist")
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    except (SyntaxError, UnicodeDecodeError, OSError) as exc:
        raise ValueError(f"source file {spec['file']} cannot be parsed: {exc}") from exc
    bad = constant_mutations(tree, spec["constants"])
    if bad:
        raise ValueError(f"a seed constant is changed after its assignment in {spec['file']} ({'; '.join(bad[:3])}): the literal is not what the module holds")
    out = []
    for name in spec["constants"]:
        for node in ast.walk(_top_level_value(tree, name, spec["file"])):
            if isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if isinstance(k, ast.Constant) and k.value == spec["key"]:
                        out.extend(_literal_strings(v))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
                for kw in node.keywords:
                    if kw.arg == spec["key"]:
                        out.extend(_literal_strings(kw.value))
    return out


_MUTATORS = frozenset({"append", "extend", "insert", "update", "add", "remove", "pop", "popitem", "clear", "discard", "setdefault", "sort", "reverse", "difference_update", "intersection_update",
                       "symmetric_difference_update", "__setitem__", "__delitem__", "__iadd__", "__ior__"})


def constant_mutations(tree, names) -> list[str]:
    """The module-level statements (outside any def / class body) that change one of the named constants after its assignment: an augmented assignment (`C |= {...}`, `C += [...]`), an item or attribute store
    (`C[k] = v`), a delete, or a call of a mutating method (`C.update(...)`, `C.append(...)`, `C.extend(...)`). A seed read from the assignment alone would not be what the module holds once it is imported, so
    the reader refuses such a module. Descends into module-level if / for / while / with / try blocks."""
    names = set(names)
    out = []

    def root(n):
        while isinstance(n, (ast.Subscript, ast.Attribute)):
            n = n.value
        return n.id if isinstance(n, ast.Name) else None

    def walk(stmts):
        for st in stmts:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(st, ast.AugAssign) and root(st.target) in names:
                out.append(f"line {st.lineno}: augmented assignment to {root(st.target)}")
            elif isinstance(st, (ast.Assign, ast.AnnAssign)):
                tg = st.targets if isinstance(st, ast.Assign) else [st.target]
                for t in tg:
                    if isinstance(t, (ast.Subscript, ast.Attribute)) and root(t) in names:
                        out.append(f"line {st.lineno}: item or attribute store into {root(t)}")
            elif isinstance(st, ast.Delete):
                for t in st.targets:
                    if root(t) in names:
                        out.append(f"line {st.lineno}: delete from {root(t)}")
            for sub in ast.walk(st) if not isinstance(st, (ast.If, ast.For, ast.While, ast.With, ast.Try)) else []:
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr in _MUTATORS and root(sub.func.value) in names:
                    out.append(f"line {sub.lineno}: {root(sub.func.value)}.{sub.func.attr}(...)")
            for fld in ("body", "orelse", "finalbody"):
                if isinstance(st, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    walk(getattr(st, fld, []))
            if isinstance(st, ast.Try):
                for h in st.handlers:
                    walk(h.body)
    walk(tree.body)
    return out


def function_source_sha256(tree, name: str, where: str) -> str:
    """sha256 of `ast.unparse` of the top-level function `name` (comments and layout do not move it; any code change does). ValueError when it is not defined exactly once."""
    defs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    if len(defs) != 1:
        raise ValueError(f"{name} is defined {len(defs)} time(s) at the top level of {where} (exactly one definition is required)")
    return hashlib.sha256(ast.unparse(defs[0]).encode("utf-8")).hexdigest()


def _parse_source(root: Path, rel: str):
    p = (Path(root) / rel).resolve()
    try:
        p.relative_to(Path(root).resolve())
    except ValueError as exc:
        raise ValueError("the source file resolves outside the repository") from exc
    if not p.is_file():
        raise ValueError(f"source file {rel} does not exist")
    try:
        return ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    except (SyntaxError, UnicodeDecodeError, OSError) as exc:
        raise ValueError(f"source file {rel} cannot be parsed: {exc}") from exc


def _resolve_overlay_sentences(root: Path, spec) -> list[str]:
    """The sentences a per-key seed WITH an overlay names: what the committed rows say after the committed overlay module is applied, by AST (no code is run). Rows are the dict displays inside the named
    constants that carry `overlay.id_key` as a string literal; the overlay module holds `overlay.removed` (a set / frozenset literal of row ids that are dropped) and `overlay.edits` (a dict display
    {row id: {field: value}}). A row that is removed contributes nothing; a row with an edit of `key` contributes the edit's string literal (an edit that is not a plain literal contributes nothing: it is
    composed); any other row contributes its own literal. An edit of `key` for an id that no named row carries (a row built elsewhere) contributes its literal too: whether it really reaches the table
    is what the live presence check decides. Raises ValueError with the reason."""
    key, ov = spec["key"], spec["overlay"]
    tree = _parse_source(root, spec["file"])
    otree = _parse_source(root, ov["file"])
    bad = constant_mutations(tree, spec["constants"])
    if bad:
        raise ValueError(f"a seed constant is changed after its assignment in {spec['file']} ({'; '.join(bad[:3])}): the literal is not what the module holds")
    bad = constant_mutations(otree, [ov["removed"], ov["edits"]])
    if bad:
        raise ValueError(f"an overlay constant is changed after its assignment in {ov['file']} ({'; '.join(bad[:3])}): the literal is not what the module holds")
    got = function_source_sha256(otree, ov["apply_function"], ov["file"])
    if got != ov["apply_sha256"]:
        raise ValueError(f"{ov['apply_function']} in {ov['file']} is not the function the overlay was pinned to (sha256 {got[:12]}... is not {ov['apply_sha256'][:12]}...): the overlay reading must be re-reviewed")
    removed = set(_literal_of(_top_level_value(otree, ov["removed"], ov["file"])))
    ed_node = _top_level_value(otree, ov["edits"], ov["file"])
    if not isinstance(ed_node, ast.Dict):
        raise ValueError(f"{ov['edits']} in {ov['file']} is not a dict display")
    edits = {}
    for k, v in zip(ed_node.keys, ed_node.values):
        if isinstance(k, ast.Constant) and isinstance(k.value, str) and isinstance(v, ast.Dict):
            edits[k.value] = {kk.value: vv for kk, vv in zip(v.keys, v.values) if isinstance(kk, ast.Constant) and isinstance(kk.value, str)}
    out, seen = [], set()
    for name in spec["constants"]:
        for node in ast.walk(_top_level_value(tree, name, spec["file"])):
            if isinstance(node, ast.Dict):
                fields = {k.value: v for k, v in zip(node.keys, node.values) if isinstance(k, ast.Constant) and isinstance(k.value, str)}
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
                fields = {kw.arg: kw.value for kw in node.keywords if kw.arg}
            else:
                continue
            rid = fields.get(ov["id_key"])
            if not (isinstance(rid, ast.Constant) and isinstance(rid.value, str)):
                continue
            seen.add(rid.value)
            if rid.value in removed:
                continue
            val = edits.get(rid.value, {}).get(key, fields.get(key))
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                out.append(val.value)
    for rid, fields in edits.items():
        if rid not in seen and rid not in removed and isinstance(fields.get(key), ast.Constant) and isinstance(fields[key].value, str):
            out.append(fields[key].value)
    return out
