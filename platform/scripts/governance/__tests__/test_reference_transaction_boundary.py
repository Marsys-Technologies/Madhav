"""Enforce the borrowed transaction contract for the registered Reference writer."""

import ast
import json
from pathlib import Path
import re

import pytest


SIDECAR = Path(__file__).resolve().parents[3] / "python-sidecar"
WRITER = "pipeline/orchestrator/writers/bg_reference.py"
SEEDER = "brahmagyan/l0_reference.py"
COUNT_HELPER = "pipeline/orchestrator/writers/_rows_present.py"

REFERENCE_TABLES = (
    "reference_planets", "reference_signs", "reference_aspects", "reference_vargas",
    "reference_houses", "reference_strength_systems", "reference_karakas",
    "reference_upagrahas", "reference_constants", "reference_topic_tags", "reference_glossary",
)
READ_COUNT = "SELECT " + " + ".join(f"(SELECT count(*) FROM {table})" for table in REFERENCE_TABLES) + " AS n"
IDENTIFIER = r"[a-z_][a-z_0-9]*"
COLUMNS = rf"{IDENTIFIER}(?:\s*,\s*{IDENTIFIER})*"
PARAMETERS = r"%s(?:::\w+)?(?:\s*,\s*%s(?:::\w+)?)*"
INSERT = re.compile(
    rf"INSERT INTO (?P<table>{IDENTIFIER}) \({COLUMNS}\) VALUES \({PARAMETERS}\) "
    rf"ON CONFLICT \({COLUMNS}\) DO NOTHING"
)

WRITER_CALLS = {
    "WriterResult", "conn.cursor", "counts.values", "cur.execute", "cur.fetchone", "getattr",
    "int", "isinstance", "present_count", "seed_reference_borrowed", "sum", "time.time",
}
SEED_CALLS = {
    "ValueError", "_json.dumps", "a.get", "c.get", "conn.cursor", "cur.execute", "cur.fetchall",
    "datetime.now", "len", "logger.info", "logger.warning", "p.get", "ss.get",
}
COUNT_CALLS = {"RuntimeError", "int", "isinstance", "iter", "next", "row.values"}


def _definition(module, name, kind=ast.FunctionDef):
    definitions = [node for node in module.body if isinstance(node, kind) and node.name == name]
    assert len(definitions) == 1, f"expected one definition of {name}"
    _require_no_assignment(module, name)
    return definitions[0]


def _require_no_assignment(module, name):
    assert not any(
        isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.id == name
        for node in ast.walk(module)
    ), f"rebound callable {name}"


def _require_import(module, target, name):
    bindings = [
        (node.level, node.module, alias.name)
        for node in ast.walk(module)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if (alias.asname or alias.name) == name
    ]
    assert bindings == [(0, target, name)], f"unexpected import binding for {name}"
    assert not any(
        (alias.asname or alias.name.split(".", 1)[0]) == name
        for node in ast.walk(module) if isinstance(node, ast.Import)
        for alias in node.names
    ), f"unexpected import binding for {name}"
    _require_no_assignment(module, name)
    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name
        for node in ast.walk(module)
    ), f"rebound callable {name}"


def _inside_disabled_branch(node, parents):
    while node in parents:
        parent = parents[node]
        if isinstance(parent, ast.If) and node in parent.body and isinstance(parent.test, ast.Constant):
            if parent.test.value is False:
                return True
        node = parent
    return False


def _check_sql(call, parents, count_sql):
    assert call.args, "missing SQL statement"
    sql = call.args[0]
    if count_sql is not None:
        assert isinstance(sql, ast.Name) and sql.id == "ROWS_PRESENT_SQL", "unexpected writer read"
        assert count_sql == READ_COUNT, "rows-present statement exceeds Reference scope"
        return
    assert isinstance(sql, ast.Constant) and isinstance(sql.value, str), "dynamic seed SQL"
    statement = " ".join(sql.value.split())
    if statement == "SELECT canonical_id FROM brahma_ontology":
        return
    insert = INSERT.fullmatch(statement)
    assert insert is not None, "unexpected seed SQL shape"
    table = insert["table"]
    inactive = table == "reference_nakshatras" and _inside_disabled_branch(call, parents)
    assert table in REFERENCE_TABLES or inactive, f"seed SQL exceeds Reference scope: {table}"


def _check_function(function, calls, *, count_sql=None):
    assert not function.decorator_list, f"unreviewed decorator on {function.name}"
    parents = {child: parent for parent in ast.walk(function) for child in ast.iter_child_nodes(parent)}
    for node, parent in parents.items():
        assert not isinstance(node, (ast.Lambda, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Global, ast.Nonlocal)), (
            "unexpected executable binding in the borrowed closure"
        )
        if isinstance(node, ast.withitem):
            assert ast.unparse(node.context_expr) == "conn.cursor()" and isinstance(node.optional_vars, ast.Name), (
                "unexpected context manager in the borrowed closure"
            )
            assert node.optional_vars.id == "cur", "unexpected cursor binding"
        if isinstance(node, ast.Call):
            target = ast.unparse(node.func)
            assert target in calls, f"unexpected call in {function.name}: {target}"
            if target == "cur.execute":
                _check_sql(node, parents, count_sql)
            if target == "conn.cursor":
                assert isinstance(parent, ast.withitem) and parent.context_expr is node
        if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
            continue
        if node.id == "conn":
            member = isinstance(parent, ast.Attribute) and parent.attr in {"cursor", "row_factory"}
            arguments = ast.unparse(parent) if isinstance(parent, ast.Call) else ""
            delegation = arguments in {
                "getattr(conn, 'row_factory', None)",
                "seed_reference_borrowed(conn, ctx.build_id, dry_run=ctx.dry_run)",
            }
            assert member or delegation, "borrowed connection escaped its interface"
            if member and parent.attr == "cursor":
                caller = parents.get(parent)
                assert isinstance(caller, ast.Call) and caller.func is parent, "cursor factory escaped"
            if member and parent.attr == "row_factory":
                binding = parents.get(parent)
                assert isinstance(binding, ast.Assign) and ast.unparse(binding) in {
                    "conn.row_factory = psycopg.rows.tuple_row",
                    "conn.row_factory = prior_row_factory",
                }, "unexpected row factory binding"
        if node.id == "cur":
            assert isinstance(parent, ast.Attribute), "borrowed cursor escaped its interface"
            if parent.attr != "rowcount":
                caller = parents.get(parent)
                assert isinstance(caller, ast.Call) and caller.func is parent, "cursor method escaped"
        if node.id == "ctx":
            assert isinstance(parent, ast.Attribute) and parent.attr in {"db_conn", "dry_run", "build_id"}
            if parent.attr == "db_conn":
                binding = parents.get(parent)
                assert isinstance(binding, ast.Assign) and ast.unparse(binding) == "conn = ctx.db_conn"


@pytest.fixture(scope="module")
def reference_sources():
    return {name: (SIDECAR / name).read_text(encoding="utf-8") for name in (WRITER, SEEDER, COUNT_HELPER)}


def _check_reference(sources):
    writer, seed, counts = (ast.parse(sources[name]) for name in (WRITER, SEEDER, COUNT_HELPER))
    _require_import(writer, "brahmagyan.l0_reference", "seed_reference_borrowed")
    _require_import(writer, "pipeline.orchestrator.writers._rows_present", "present_count")
    count_literals = [
        ast.literal_eval(node.value) for node in writer.body
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ROWS_PRESENT_SQL" for t in node.targets)
    ]
    assert len(count_literals) == 1 and isinstance(count_literals[0], str)
    writer_class = _definition(writer, "ReferenceWriter", ast.ClassDef)
    assert [ast.unparse(node) for node in writer_class.decorator_list] == ["register('bg_reference')"]
    _check_function(_definition(writer_class, "run"), WRITER_CALLS, count_sql=count_literals[0])
    _check_function(_definition(seed, "seed_reference_borrowed"), SEED_CALLS)
    _check_function(_definition(counts, "present_count"), COUNT_CALLS)


def test_reference_writer_borrows_and_legacy_entry_can_commit(reference_sources):
    _check_reference(reference_sources)
    _check_legacy_wrapper(reference_sources[SEEDER])


def _check_legacy_wrapper(source):
    wrapper = _definition(ast.parse(source), "seed_reference")
    parents = {child: parent for parent in ast.walk(wrapper) for child in ast.iter_child_nodes(parent)}
    calls = [node for node in parents if isinstance(node, ast.Call)]
    assert {ast.unparse(node.func) for node in calls} == {"seed_reference_borrowed", "conn.commit"}
    commit_calls = [node for node in calls if ast.unparse(node.func) == "conn.commit"]
    assert len(commit_calls) == 1
    statement = parents[commit_calls[0]]
    branch = parents[statement]
    assert isinstance(branch, ast.If) and ast.unparse(branch.test) == "autocommit" and statement in branch.body, (
        "legacy commit must remain conditional on autocommit"
    )


@pytest.mark.parametrize(
    ("path", "original", "replacement", "diagnostic"),
    [
        (WRITER, "import seed_reference_borrowed", "import seed_reference as seed_reference_borrowed", "import binding"),
        (WRITER, "conn = ctx.db_conn", "conn = ctx.db_conn\n        finish = conn.commit", "connection escaped"),
        (WRITER, "conn = ctx.db_conn", "conn = ctx.db_conn\n        with conn:\n            pass", "unexpected context manager"),
        (WRITER, "conn = ctx.db_conn", "conn = ctx.db_conn\n        with external_manager:\n            pass", "unexpected context manager"),
        (WRITER, "conn = ctx.db_conn", "conn = ctx.db_conn\n        conn.autocommit = True", "connection escaped"),
        (WRITER, "import seed_reference_borrowed", "import seed_reference_borrowed\nimport external as seed_reference_borrowed", "import binding"),
        (WRITER, "    def run(", "    @external\n    def run(", "unreviewed decorator"),
        (SEEDER, "def seed_reference_borrowed", "@external\ndef seed_reference_borrowed", "unreviewed decorator"),
        (SEEDER, "def seed_reference_borrowed", "seed_reference_borrowed = seed_reference\n\ndef seed_reference_borrowed", "rebound callable"),
        (SEEDER, "SELECT canonical_id FROM brahma_ontology", "SELECT canonical_id FROM brahma_ontology; COMMIT", "SQL shape"),
        (SEEDER, "INSERT INTO reference_planets", "INSERT INTO asset_throughput", "exceeds Reference scope"),
        (COUNT_HELPER, "value = None", "driver_write(row)\n    value = None", "unexpected call"),
    ],
)
def test_reference_boundary_rejects_bypasses(reference_sources, path, original, replacement, diagnostic):
    assert original in reference_sources[path]
    candidate = {**reference_sources, path: reference_sources[path].replace(original, replacement, 1)}
    with pytest.raises(AssertionError, match=diagnostic):
        _check_reference(candidate)


def test_legacy_wrapper_cannot_commit_unconditionally(reference_sources):
    candidate = reference_sources[SEEDER].replace("    if autocommit:\n        conn.commit()", "    conn.commit()", 1)
    with pytest.raises(AssertionError, match="commit must remain conditional"):
        _check_legacy_wrapper(candidate)

def test_reference_declaration_cites_borrowed_inserts_and_registered_delegate(reference_sources):
    declaration_path = SIDECAR.parent / "scripts/governance/asset_declarations.json"
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))["assets"]["bg_reference"]
    seed = _definition(ast.parse(reference_sources[SEEDER]), "seed_reference_borrowed")
    writer = _definition(ast.parse(reference_sources[WRITER]), "ReferenceWriter", ast.ClassDef)
    run = _definition(writer, "run")
    delegates = [
        node.lineno for node in ast.walk(run)
        if isinstance(node, ast.Call) and ast.unparse(node.func) == seed.name
    ]
    assert len(delegates) == 1

    insert_lines = {}
    for node in ast.walk(seed):
        if not (isinstance(node, ast.Call) and ast.unparse(node.func) == "cur.execute"):
            continue
        sql = node.args[0]
        assert isinstance(sql, ast.Constant) and isinstance(sql.value, str)
        for offset, line in enumerate(sql.value.splitlines()):
            match = re.fullmatch(r"\s*INSERT INTO (\w+)\s*", line)
            if match and match[1] in REFERENCE_TABLES:
                table = match[1]
                assert table not in insert_lines
                insert_lines[table] = sql.lineno + offset
    assert set(insert_lines) == set(REFERENCE_TABLES)

    seeder_path = f"platform/python-sidecar/{SEEDER}"
    writer_path = f"platform/python-sidecar/{WRITER}"
    locator = re.compile(re.escape(seeder_path) + r":(\d+)(?:[-–](\d+))?")

    def citations(text):
        return [(int(start), int(end) if end else None) for start, end in locator.findall(text)]

    evidence = declaration["evidence"]["prose_fields"]
    expected_range = (min(insert_lines.values()), max(insert_lines.values()))
    assert [pair for pair in citations(evidence) if pair[1] is not None] == [expected_range]
    delegate = f"{seed.name} ({seeder_path}:{seed.lineno}, called by the writer {writer_path}:{delegates[0]})"
    if delegate not in evidence:
        raise AssertionError("Reference evidence must identify the borrowed seeder and registered call site")

    prose_none = declaration["prose_none"]
    for row in prose_none["closed_columns"]:
        if row.get("table") == "reference_glossary" and row["column"] == "related_concepts":
            # This declaration cites the literal rather than the INSERT.
            continue
        table = row.get("table", "reference_planets")
        assert citations(row["why"])[-1] == (insert_lines[table], None), (table, row["column"])
    for row in prose_none["identifier_columns"]:
        table = row.get("table", "reference_planets")
        assert citations(row["why"])[-1] == (insert_lines[table], None), (table, row["column"])
        assert citations(row["evidence"]) == [(insert_lines[table] + 1, None)], (table, row["column"])
    for row in declaration["vocab_embedded_text"]:
        table = row["table"]
        assert citations(row["evidence"]) == [(insert_lines[table] + 1, None)], (table, row["column"])
