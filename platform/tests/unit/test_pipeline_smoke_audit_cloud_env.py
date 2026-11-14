"""Pure cloud project resolution checks without invoking the smoke audit."""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import types
import unittest


AUDIT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "pipeline_smoke_audit.py"
SPEC = importlib.util.spec_from_file_location("pipeline_smoke_audit_cloud_env_test", AUDIT_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)

CASES = [
    ("absent", {}, "madhav-astrology"),
    ("canonical only", {"GOOGLE_CLOUD_PROJECT": "canonical"}, "canonical"),
    ("legacy only", {"GCP_PROJECT": "legacy"}, "legacy"),
    ("equal", {"GCP_PROJECT": "same", "GOOGLE_CLOUD_PROJECT": "same"}, "same"),
    ("conflict", {"GCP_PROJECT": "legacy", "GOOGLE_CLOUD_PROJECT": "canonical"}, "legacy"),
    ("empty legacy", {"GCP_PROJECT": "", "GOOGLE_CLOUD_PROJECT": "canonical"}, ""),
    ("empty canonical", {"GCP_PROJECT": "legacy", "GOOGLE_CLOUD_PROJECT": ""}, "legacy"),
    ("both empty", {"GCP_PROJECT": "", "GOOGLE_CLOUD_PROJECT": ""}, ""),
    ("canonical empty only", {"GOOGLE_CLOUD_PROJECT": ""}, ""),
    ("legacy empty only", {"GCP_PROJECT": ""}, ""),
    ("null legacy", {"GCP_PROJECT": None, "GOOGLE_CLOUD_PROJECT": "canonical"}, "canonical"),
    ("both null", {"GCP_PROJECT": None, "GOOGLE_CLOUD_PROJECT": None}, "madhav-astrology"),
]


class CloudProjectResolutionTests(unittest.TestCase):
    def test_pure_resolution_matrix(self):
        for name, env, expected in CASES:
            with self.subTest(name=name):
                before = dict(env)
                self.assertEqual(AUDIT.read_google_cloud_project(env), "madhav-astrology" if env.get("GOOGLE_CLOUD_PROJECT") is None else env["GOOGLE_CLOUD_PROJECT"])
                self.assertEqual(env, before)

    def test_both_audit_project_reads_use_pure_resolution(self):
        functions = {
            node.name: node for node in ast.parse(AUDIT_PATH.read_text()).body
            if isinstance(node, ast.FunctionDef)
        }
        for name in ("audit_gcs", "audit_vertex_ai"):
            assignments = [
                node for node in ast.walk(functions[name])
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "project" for target in node.targets)
            ]
            self.assertEqual(len(assignments), 1)
            expression = assignments[0].value
            self.assertEqual(ast.unparse(expression), "read_google_cloud_project(os.environ)")
            for case, env, expected in CASES:
                with self.subTest(function=name, case=case):
                    namespace = {
                        "os": types.SimpleNamespace(environ=env),
                        "read_google_cloud_project": AUDIT.read_google_cloud_project,
                    }
                    self.assertEqual(eval(compile(ast.Expression(expression), str(AUDIT_PATH), "eval"), namespace), "madhav-astrology" if env.get("GOOGLE_CLOUD_PROJECT") is None else env["GOOGLE_CLOUD_PROJECT"])

    def test_import_does_not_run_audit(self):
        self.assertEqual(AUDIT.results, [])

    def test_explicit_translation_preserves_the_old_effective_binding(self):
        for name, env, expected in CASES:
            with self.subTest(name=name):
                translated = dict(env)
                translated.pop("GCP_PROJECT", None)
                translated["GOOGLE_CLOUD_PROJECT"] = expected
                self.assertEqual(AUDIT.read_google_cloud_project(translated), expected)


if __name__ == "__main__":
    unittest.main()
