"""Exercise reconciliation exit status with public synthetic inputs."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "platform/scripts/governance/check_reconciliation_cadence.py"
WORKFLOW = ROOT / ".github/workflows/reconciliation-cadence.yml"


@pytest.fixture
def gate(monkeypatch):
    spec = importlib.util.spec_from_file_location("reconciliation_cadence_fixture", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)

    def reject_network(*args, **kwargs):
        pytest.fail("unexpected network call")

    monkeypatch.setattr(module.urllib.request, "urlopen", reject_network)
    monkeypatch.delenv("MCP_CANARY_KEY", raising=False)
    return module


@pytest.fixture
def static_inputs(gate, tmp_path):
    required = [
        *gate.CR_STATUS_PATHS, *gate.REGISTRY_DATA_PATHS,
        *gate.DEFAULT_TABLE_REGISTERS, gate.ELEVATION_REGISTER_PATH,
    ]
    for name in required:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("// inert fixture\n", encoding="utf-8")
    for name in gate.CR_STATUS_PATHS:
        (tmp_path / name).write_text(
            "export const OPEN_CRS = [] as const;\nexport const LOGGED_CRS = [] as const;\n"
            "export const CLOSED_CRS = [] as const;\n", encoding="utf-8",
        )
    for name in gate.REGISTRY_DATA_PATHS:
        (tmp_path / name).write_text("{ primitive_id: 'fixture_primitive' }\n", encoding="utf-8")
    for i, name in enumerate(gate.DEFAULT_TABLE_REGISTERS):
        (tmp_path / name).write_text(
            f"| ID | Status |\n| --- | --- |\n| CR-{123 + i} | CLOSED |\n", encoding="utf-8",
        )
    (tmp_path / gate.ELEVATION_REGISTER_PATH).write_text(
        "**EL-001. Synthetic fixture**\nCLOSED\n", encoding="utf-8",
    )
    return tmp_path


def test_bundled_self_test(gate):
    assert gate.main(["--self-test"]) == 0


@pytest.mark.parametrize("mode", ["missing", "empty", "invalid_utf8", "unparseable_status", "no_register_rows", "missing_extra"])
def test_static_operational_failure_keeps_json_report(gate, static_inputs, mode):
    table = static_inputs / gate.DEFAULT_TABLE_REGISTERS[0]
    extra = []
    if mode == "missing":
        (static_inputs / gate.REGISTRY_DATA_PATHS[0]).unlink()
    elif mode == "empty":
        table.write_text(" \n", encoding="utf-8")
    elif mode == "invalid_utf8":
        table.write_bytes(b"\xff")
    elif mode == "unparseable_status":
        (static_inputs / gate.CR_STATUS_PATHS[0]).write_text("// no status blocks\n", encoding="utf-8")
    elif mode == "no_register_rows":
        table.write_text("# no parsed rows\n", encoding="utf-8")
    else:
        extra = ["--register", "missing-extra.md"]
    out = static_inputs / "report.json"
    assert gate.main(["--root", str(static_inputs), "--advisory", "--json", "--out", str(out), *extra]) == 2
    result = json.loads(out.read_bytes())
    assert result["execution_error"] == "static_inputs_unavailable_or_unparseable"
    assert result["pass"] is False
    assert result["live_results"] is None


@pytest.mark.parametrize("role", ["status_array", "registry", "first_table", "second_table", "elevation", "extra"])
def test_single_unparseable_required_role_fails_even_with_valid_rows(gate, static_inputs, role):
    required = {
        "status_array": gate.CR_STATUS_PATHS[0],
        "registry": gate.REGISTRY_DATA_PATHS[0],
        "first_table": gate.DEFAULT_TABLE_REGISTERS[0],
        "second_table": gate.DEFAULT_TABLE_REGISTERS[1],
        "elevation": gate.ELEVATION_REGISTER_PATH,
        "extra": "synthetic-extra.md",
    }
    # A recognized status array on its own does not prove all three status roles.
    wrong = "export const OPEN_CRS = [] as const;\n" if role == "status_array" else "# nonempty but not parseable\n"
    (static_inputs / required[role]).write_text(wrong, encoding="utf-8")
    out = static_inputs / "report.json"
    extra = ["--register", required[role]] if role == "extra" else []
    assert gate.main(["--root", str(static_inputs), "--advisory", "--json", "--out", str(out), *extra]) == 2
    assert json.loads(out.read_bytes())["execution_error"] == "static_inputs_unavailable_or_unparseable"


def test_real_empty_status_and_gap_sets_are_not_missing_inputs(gate, static_inputs):
    _, rows, statuses, citations = gate.run_static_pass(static_inputs, [])
    assert len(rows) == 3 and len(statuses) == 2
    assert all(not s.open_crs and not s.closed_crs and not s.logged_crs for s in statuses)
    assert not citations


def test_static_real_parser_and_completed_divergence_remains_advisory(gate, static_inputs, monkeypatch):
    rows = gate.run_static_pass(static_inputs, [])[1]
    assert len(rows) == 3
    monkeypatch.setattr(gate, "cross_reference", lambda *_: [gate.Divergence(
        kind="synthetic_difference", item_id=rows[0].item_id, severity="warning", detail="synthetic", sources=[],
    )])
    out = static_inputs / "report.json"
    opts = ["--root", str(static_inputs), "--json", "--out", str(out)]
    assert gate.main(opts) == 1
    assert gate.main([*opts, "--advisory"]) == 0
    result = json.loads(out.read_bytes())
    assert result["register_rows_scanned"] == 3 and len(result["divergences"]) == 1
    assert not result["pass"] and "execution_error" not in result


@pytest.mark.parametrize("mode", ["missing_key", "no_candidate", "unavailable_definition", "probe_failed", "completed"])
def test_requested_live_preserves_status_and_controls(gate, static_inputs, monkeypatch, mode):
    if mode != "missing_key":
        monkeypatch.setenv("MCP_CANARY_KEY", "synthetic-placeholder")
    rows_expected = 3
    execution = []
    opts = []
    if mode not in {"missing_key", "no_candidate"}:
        opts = ["--live-all-open"]
        row = "| CR-123 | OPEN |\n"
        if mode != "unavailable_definition":
            row = "| CR-123 | OPEN `fixture_get()` |\n"
        if mode == "probe_failed":
            row += "| CR-125 | OPEN `fixture_get()` |\n"
            rows_expected = 4
        (static_inputs / gate.DEFAULT_TABLE_REGISTERS[0]).write_text(
            "| ID | Status |\n| --- | --- |\n" + row, encoding="utf-8",
        )

        def fake_probe(_url, _key, tool, _args):
            execution.append(tool)
            failed = mode == "probe_failed" and len(execution) == 2
            return {"ok": not failed, "status": 503 if failed else 200, "content": []}

        monkeypatch.setattr(gate, "mcp_call", fake_probe)
    out = static_inputs / "report.json"
    rc = gate.main(["--root", str(static_inputs), "--advisory", "--live", "--json", "--out", str(out), *opts])
    result = json.loads(out.read_bytes())
    assert result["register_rows_scanned"] == rows_expected
    assert len(execution) == {"completed": 1, "probe_failed": 2}.get(mode, 0)
    if mode == "completed":
        assert rc == 0 and result["pass"] is True and "execution_error" not in result
        return
    assert rc == 2 and result["pass"] is False
    assert result["execution_error"] == {
        "missing_key": "live_key_missing",
        "no_candidate": "no_eligible_live_probe",
        "unavailable_definition": "live_probe_incomplete",
        "probe_failed": "live_probe_incomplete",
    }[mode]
    if mode == "probe_failed":
        assert len(result["live_results"]) == 2


class InertResponse:
    status = 200

    def __init__(self, body):
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


@pytest.mark.parametrize(("payload", "ok"), [
    (b"not JSON", False),
    (b'{"jsonrpc":"2.0","id":1}', False),
    (b'{"jsonrpc":"2.0","id":1,"result":{}}', False),
    (b'{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"[]"}]}}', False),
    (b'{"result":{"content":[{"type":"text","text":"[]"}]}}', False),
    (b'data: {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"[]"}]}}\n', True),
    (b'{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"[]"}],"isError":true}}', False),
    (b'{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"[]"}]}}', True),
    (b'{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"   "}]}}', False),
    (b'{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"image","text":"[]"}]}}', False),
    (b'{"jsonrpc":"2.0","id":1,"result":{"content":[{"text":"[]"}]}}', False),
    (b'{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"ordinary prose"}]}}', False),
    (b'{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"123"}]}}', False),
])
def test_transport_response_only_accepts_valid_result(gate, monkeypatch, payload, ok):
    monkeypatch.setattr(gate.urllib.request, "urlopen", lambda *_a, **_kw: InertResponse(payload))
    response = gate.mcp_call("https://fixture.invalid", "synthetic-placeholder", "fixture_tool", {})
    assert response["ok"] is ok
    if ok:
        assert response["content"] == []


def test_workflow_default_and_failure_propagation(tmp_path, monkeypatch):
    doc = yaml.load(WORKFLOW.read_bytes(), Loader=yaml.BaseLoader)
    assert set(doc["on"]) == {"workflow_dispatch"}
    assert doc["on"]["workflow_dispatch"]["inputs"]["run_live"]["default"] == "false"
    steps = next(iter(doc["jobs"].values()))["steps"]
    static = next(step for step in steps if step.get("id") == "static_pass")
    live = next(step for step in steps if "MCP_CANARY_KEY" in step.get("env", {}))
    upload = next(step for step in steps if step.get("uses", "").startswith("actions/upload-artifact@"))
    assert "continue-on-error" not in static
    assert live["if"] == "${{ inputs.run_live == true }}"
    assert upload["if"] == "${{ always() }}"
    fake = tmp_path / "python3"
    fake.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$*\" >> \"$INERT_TRACE\"\n"
        "case \"$*\" in *--self-test*) exit \"$INERT_SELFTEST\" ;; esac\n"
        "exit \"$INERT_RESULT\"\n", encoding="utf-8",
    )
    fake.chmod(0o700)
    monkeypatch.setenv("PATH", f"{tmp_path}:/usr/bin:/bin")
    trace = tmp_path / "trace"
    monkeypatch.setenv("INERT_TRACE", str(trace))
    monkeypatch.setenv("INERT_RESULT", "2")
    monkeypatch.setenv("INERT_SELFTEST", "1")
    assert subprocess.run(["/bin/bash", "-e", "-c", static["run"]], cwd=tmp_path).returncode == 1
    assert trace.read_text().count("\n") == 1
    trace.unlink()
    monkeypatch.setenv("INERT_SELFTEST", "0")
    assert subprocess.run(["/bin/bash", "-e", "-c", static["run"]], cwd=tmp_path).returncode == 2
    assert "--advisory" in trace.read_text()
    trace.unlink()
    monkeypatch.delenv("MCP_CANARY_KEY", raising=False)
    assert subprocess.run(["/bin/bash", "-e", "-c", live["run"]], cwd=tmp_path).returncode == 2
    assert "--advisory" in trace.read_text() and "--live" in trace.read_text()



@pytest.mark.parametrize("role", ["status", "registry"])
def test_multiline_commented_roles_do_not_satisfy_required_inputs(gate, static_inputs, role):
    if role == "status":
        path = static_inputs / gate.CR_STATUS_PATHS[0]
        active = "export const OPEN_CRS = [] as const;\nexport const LOGGED_CRS = [] as const;\n"
        commented = "export const CLOSED_CRS = [] as const;"
    else:
        path = static_inputs / gate.REGISTRY_DATA_PATHS[0]
        active = "// a registry with no active primitives\n"
        commented = "{ primitive_id: 'commented_fixture' }"
    path.write_text(active + "/*\n" + commented + "\n*/\n", encoding="utf-8")
    report = static_inputs / "report.json"
    assert gate.main(["--root", str(static_inputs), "--advisory", "--json", "--out", str(report)]) == 2
    assert json.loads(report.read_bytes())["execution_error"] == "static_inputs_unavailable_or_unparseable"


def test_active_empty_arrays_ignore_commented_rows_and_keep_strings(gate, static_inputs):
    status = static_inputs / gate.CR_STATUS_PATHS[0]
    status.write_text(
        'export const OPEN_CRS = [/* "CR-404" */] as const;\n'
        'export const LOGGED_CRS = [] as const;\n'
        'export const CLOSED_CRS = [] as const;\n'
        '/*\nexport const CLOSED_CRS = ["CR-405"] as const;\n*/\n',
        encoding="utf-8",
    )
    registry = static_inputs / gate.REGISTRY_DATA_PATHS[0]
    registry.write_text(
        "{ primitive_id: 'fixture_primitive' }\n"
        "/*\n{ primitive_id: 'commented_fixture' }\n*/\n",
        encoding="utf-8",
    )
    _, rows, statuses, citations = gate.run_static_pass(static_inputs, [])
    assert len(rows) == 3 and len(statuses) == 2
    assert all(not s.open_crs and not s.closed_crs and not s.logged_crs for s in statuses)
    assert not citations


def test_comment_scanner_preserves_quoted_markers_and_line_offsets(gate):
    value = repr("https://fixture.invalid/a") + " /* a\nb */ " + repr("/* literal */") + " // tail\n"
    masked = gate._strip_ts_comments_but_keep_strings(value)
    assert len(masked) == len(value)
    assert [i for i, char in enumerate(masked) if char == "\n"] == [
        i for i, char in enumerate(value) if char == "\n"
    ]
    assert repr("https://fixture.invalid/a") in masked and repr("/* literal */") in masked
    assert "tail" not in masked and "b */" not in masked


def test_registry_parser_does_not_read_multiline_commented_primitives(gate, tmp_path):
    # Use the existing public fixture as the source of a known parsed citation.
    original = gate.FIXTURE_DIR / "registry_data_a.ts"
    assert gate.parse_known_gap_citations(original, "synthetic.ts")
    path = tmp_path / "commented.ts"
    public_body = original.read_text(encoding="utf-8").split("*/", 1)[1]
    path.write_text("/*\n" + public_body + "\n*/\n", encoding="utf-8")
    assert gate.parse_known_gap_citations(path, "synthetic.ts") == []



@pytest.mark.parametrize("role", ["status", "registry"])
@pytest.mark.parametrize("encoding", ["double", "template", "interpolation_string"])
def test_documentation_literal_cannot_supply_required_role(gate, static_inputs, role, encoding):
    marker = ("export const CLOSED_CRS = [] as const;" if role == "status"
              else "{ primitive_id: 'fixture_primitive' }")
    if encoding == "double":
        value = json.dumps(marker)
    elif encoding == "template":
        value = chr(96) + marker + chr(96)
    else:
        value = chr(96) + "$" + "{" + json.dumps(marker) + "}" + chr(96)
    active = ("export const OPEN_CRS = [] as const;\nexport const LOGGED_CRS = [] as const;\n"
              if role == "status" else "")
    path = static_inputs / (gate.CR_STATUS_PATHS[0] if role == "status" else gate.REGISTRY_DATA_PATHS[0])
    path.write_text(active + "const docs = " + value + ";\n", encoding="utf-8")
    out = static_inputs / "literal-report.json"
    assert gate.main(["--root", str(static_inputs), "--advisory", "--json", "--out", str(out)]) == 2
    assert json.loads(out.read_bytes())["execution_error"] == "static_inputs_unavailable_or_unparseable"


@pytest.mark.parametrize("quote", ["'", '"'])
def test_real_quoted_property_keys_values_and_comments_are_read(gate, static_inputs, quote):
    primitive = quote + "primitive_id" + quote
    gap = quote + "known_gap" + quote
    row = ("{ " + primitive + " /* code comment */ : " + quote + "fixture_primitive" + quote +
           ", " + gap + ": " + quote + "CR-123" + quote + " }\n")
    path = static_inputs / gate.REGISTRY_DATA_PATHS[0]
    path.write_text(row, encoding="utf-8")
    citations = gate.parse_known_gap_citations(path, "synthetic.ts")
    assert len(citations) == 1
    assert citations[0].primitive_id == "fixture_primitive"
    assert citations[0].cr_id == "CR-123"
    assert citations[0].line == 1
    assert len(gate.run_static_pass(static_inputs, [])[1]) == 3


@pytest.mark.parametrize("quote", ["'", '"'])
def test_status_ids_are_real_quoted_values_not_string_contents(gate, tmp_path, quote):
    path = tmp_path / "status.ts"
    path.write_text(
        "export const OPEN_CRS = [" + quote + "CR-123" + quote + "] as const;\n"
        "export const LOGGED_CRS = [] as const;\n"
        "export const CLOSED_CRS = [] as const;\n"
        "const docs = " + json.dumps("export const CLOSED_CRS = ['CR-999'] as const;") + ";\n",
        encoding="utf-8",
    )
    result = gate.parse_cr_status_ts(path, "synthetic.ts")
    assert result.open_crs == {"CR-123"}
    assert result.closed_crs == set()
    assert result.logged_crs == set()


@pytest.mark.parametrize("nested", [False, True])
def test_real_property_code_inside_template_interpolation_remains_visible(gate, static_inputs, nested):
    expression = "({ primitive_id: 'fixture_primitive', known_gap: 'CR-123' }).primitive_id"
    rendered = chr(96) + "text " + "$" + "{" + expression + "}" + chr(96)
    if nested:
        rendered = chr(96) + "outer " + "$" + "{" + rendered + "}" + chr(96)
    path = static_inputs / gate.REGISTRY_DATA_PATHS[0]
    path.write_text("const rendered = " + rendered + ";\n", encoding="utf-8")
    rows = gate.parse_known_gap_citations(path, "synthetic.ts")
    assert len(rows) == 1 and rows[0].cr_id == "CR-123"
    assert len(gate.run_static_pass(static_inputs, [])[1]) == 3


def test_quoted_known_gap_documentation_does_not_create_citation(gate, tmp_path):
    path = tmp_path / "registry.ts"
    path.write_text(
        "{ primitive_id: 'fixture_primitive', docs: " + json.dumps("known_gap: 'CR-999'") + " }\n",
        encoding="utf-8",
    )
    assert gate.parse_known_gap_citations(path, "synthetic.ts") == []


def test_escaped_template_interpolation_is_only_literal_text(gate, static_inputs):
    text = chr(96) + "\\" + "$" + "{ { primitive_id: 'fixture_primitive' } }" + chr(96)
    path = static_inputs / gate.REGISTRY_DATA_PATHS[0]
    path.write_text("const docs = " + text + ";\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no parsed reconciliation registry primitives"):
        gate.run_static_pass(static_inputs, [])


def test_regex_literal_does_not_supply_required_status_declaration(gate, static_inputs):
    prefix = "export const OPEN_CRS = [] as const;\nexport const LOGGED_CRS = [] as const;\n"
    path = static_inputs / gate.CR_STATUS_PATHS[0]
    path.write_text(prefix + "const docs = /export const CLOSED_CRS = [] as const;/;\n", encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete reconciliation status blocks"):
        gate.run_static_pass(static_inputs, [])


def test_code_and_comment_views_preserve_offsets_and_literal_markers(gate):
    body = ("const x = " + json.dumps("/* literal */") + "; /*\nmasked*/\n" +
            "const out = " + chr(96) + "known_gap:'CR-999' " + "$" + "{ ({ primitive_id: 'p' }) }" + chr(96))
    comments, code, active = gate._ts_lexical_views(body)
    assert len(comments) == len(code) == len(body)
    assert [i for i, char in enumerate(code) if char == "\n"] == [i for i, char in enumerate(body) if char == "\n"]
    assert "/* literal */" in comments
    assert "masked" not in comments
    assert "known_gap" not in code
    assert "primitive_id" in code
    assert body.index("primitive_id") in active


def test_string_array_closing_marker_cannot_truncate_real_array(gate, tmp_path):
    path = tmp_path / "status.ts"
    path.write_text(
        "export const OPEN_CRS = [" + json.dumps("] as const; 'CR-999'") + ", 'CR-123'] as const;\n"
        "export const LOGGED_CRS = [] as const;\nexport const CLOSED_CRS = [] as const;\n",
        encoding="utf-8",
    )
    row = gate.parse_cr_status_ts(path, "synthetic.ts")
    assert row.open_crs == {"CR-123"}


@pytest.mark.parametrize('suffix', [
    "left / ({ primitive_id: 'hidden_primitive', known_gap: 'CR-999', value: 1 }).value / right",
    "left / right",
    "'literal' / ({ primitive_id: 'hidden', known_gap: 'CR-999', value: 1 }).value / right",
    '"literal" / right',
    '`literal` / right',
    '(left) / right',
    '[left][0] / right',
    'left++ / right',
    'left /* comment */ / right',
])
def test_operand_or_ambiguous_slash_context_refuses_instead_of_hiding_code(gate, static_inputs, suffix):
    path = static_inputs / gate.REGISTRY_DATA_PATHS[0]
    path.write_text("const left = 12, right = 3;\nconst registry = [{ primitive_id: 'fixture_primitive' }];\n"
                    + 'const ratio = ' + suffix + ';\n', encoding='utf-8')
    with pytest.raises(ValueError, match='unsupported reconciliation source slash'):
        gate.run_static_pass(static_inputs, [])


@pytest.mark.parametrize('terminator', ['\n', '\r', '\u2028', '\u2029'])
def test_every_js_line_comment_terminator_exposes_following_real_citation(gate, static_inputs, terminator):
    path = static_inputs / gate.REGISTRY_DATA_PATHS[0]
    path.write_text("const registry = [{ primitive_id: 'fixture_primitive' }];\n// documentation" + terminator
                    + "const active = ({ primitive_id: 'hidden_primitive', known_gap: 'CR-999', value: 1 }).value;\n",
                    encoding='utf-8')
    report = gate.run_static_pass(static_inputs, [])
    assert len(report[3]) == 1 and report[3][0].cr_id == 'CR-999'
    assert len(report[0]) == 1


def test_multiplication_keeps_same_active_property_visible(gate, static_inputs):
    path = static_inputs / gate.REGISTRY_DATA_PATHS[0]
    path.write_text("const left = 12, right = 3;\nconst registry = [{ primitive_id: 'fixture_primitive' }];\n"
                    "const ratio = left * ({ primitive_id: 'hidden_primitive', known_gap: 'CR-999', value: 1 }).value * right;\n",
                    encoding='utf-8')
    report = gate.run_static_pass(static_inputs, [])
    assert len(report[3]) == len(report[0]) == 1


@pytest.mark.parametrize('source', [
    "/primitive_id: 'hidden', known_gap: 'CR-999'/;",
    "const pattern = /primitive_id: 'hidden', known_gap: 'CR-999'/;",
    "f(/primitive_id: 'hidden', known_gap: 'CR-999'/);",
    "const patterns = [/primitive_id: 'hidden', known_gap: 'CR-999'/];",
    "const patterns = {a: /primitive_id: 'hidden', known_gap: 'CR-999'/};",
    "const patterns = [0, /primitive_id: 'hidden', known_gap: 'CR-999'/];",
    "const pattern = /* comment */ /primitive_id: 'hidden', known_gap: 'CR-999'/;",
])
def test_supported_regex_expression_prefixes_remain_opaque(gate, static_inputs, source):
    path = static_inputs / gate.REGISTRY_DATA_PATHS[0]
    path.write_text("const registry = [{ primitive_id: 'fixture_primitive' }];\n" + source + '\n', encoding='utf-8')
    assert gate.run_static_pass(static_inputs, [])[3] == []


@pytest.mark.parametrize('terminator', ['\u2028', '\u2029'])
def test_line_separator_in_quoted_or_template_literal_does_not_activate_fake_property(gate, static_inputs, terminator):
    path = static_inputs / gate.REGISTRY_DATA_PATHS[0]
    docs = "primitive_id: 'hidden', known_gap: 'CR-999'" + terminator + 'literal'
    path.write_text("const registry = [{ primitive_id: 'fixture_primitive' }];\nconst docs = "
                    + json.dumps(docs, ensure_ascii=False) + ';\nconst rendered = ' + chr(96) + docs + chr(96) + ';\n', encoding='utf-8')
    assert gate.run_static_pass(static_inputs, [])[3] == []
