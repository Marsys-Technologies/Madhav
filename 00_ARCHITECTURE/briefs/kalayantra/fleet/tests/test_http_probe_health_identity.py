"""D-FLIP F-12: the `http_probe mcp_health` record can state the deployed image and migration set, because the MCP /health now states them.

One oracle per distinct claim; no network is touched.

  H1  a /health body in the shape the service emits is read through: `image` is its image_digest, `migration_set` its {count, sha256, algorithm} digest
  H2  a body whose identity fields are null (the service's honest "unavailable" answer, with a *_reason) reads null in the record, never a placeholder
  H3  a malformed migration digest (count < 1 or not an int, non-hex or upper-case sha256, extra or missing key) reads null; the older list form still reads through
  H4  the field names the probe reads are the ones the service emits (platform-mcp/src/lib/deploy_identity.ts), so neither can drift without this failing
  H5  the deploy states the image digest from the image build step's `digest` output — never from the mutable tag — and the candidate attestation checks it
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]

spec = importlib.util.spec_from_file_location("http_probe_identity_under_test", FLEET / "http_probe.py")
HP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HP)

NOW = lambda: __import__("datetime").datetime(2026, 10, 22, 9, 0, 0, tzinfo=__import__("datetime").timezone.utc)   # noqa: E731
IMAGE = "sha256:" + "a1" * 32
LEDGER = {"count": 1400, "sha256": "c3" * 32, "algorithm": "sha256 of the applied filenames sorted by code point, each followed by LF"}
HEALTH = {"status": "ok", "service": "marsys-mcp", "version": "1.0.0", "deployed_sha": "0123456789abcdef0123456789abcdef01234567",
          "revision": "amjis-mcp-00042-abc", "image_digest": IMAGE, "image_digest_reason": None, "migration_set": LEDGER, "migration_set_reason": None,
          "tools": 88, "stream_g_capabilities": ["compute_natal_positions"]}


def measure(body):
    return HP.measure("mcp_health", lambda url: (200, json.dumps(body).encode()), NOW)


def test_h1_the_service_shaped_body_states_image_and_migration_set():
    record = measure(HEALTH)
    assert record["image"] == IMAGE and record["migration_set"] == LEDGER
    assert record["deployed_sha"] == HEALTH["deployed_sha"] and record["revision"] == HEALTH["revision"]


def test_h2_an_unavailable_identity_reads_null_not_a_placeholder():
    body = dict(HEALTH, image_digest=None, image_digest_reason="NIRMANA_IMAGE_DIGEST is not set", migration_set=None,
                migration_set_reason="platform ledger route unreachable (TypeError)")
    record = measure(body)
    assert record["image"] is None and record["migration_set"] is None


@pytest.mark.parametrize("digest", [
    dict(LEDGER, count=0), dict(LEDGER, count=-3), dict(LEDGER, count=True), dict(LEDGER, count=1.5), dict(LEDGER, count="1400"),
    dict(LEDGER, sha256="C3" * 32), dict(LEDGER, sha256="c3" * 31), dict(LEDGER, algorithm=""), dict(LEDGER, algorithm=None),
    dict(LEDGER, extra=1), {k: v for k, v in LEDGER.items() if k != "algorithm"}, {},
])
def test_h3_a_malformed_migration_digest_reads_null(digest):
    assert measure(dict(HEALTH, migration_set=digest))["migration_set"] is None


def test_h3_the_per_file_list_form_still_reads_through():
    listed = [{"filename": "1379_x.sql", "sha256": "a" * 64}]
    assert measure(dict(HEALTH, migration_set=listed))["migration_set"] == listed


def test_h4_the_probe_reads_the_field_names_the_service_emits():
    source = (REPO / "platform-mcp/src/lib/deploy_identity.ts").read_text()
    emitted = set(re.findall(r"^\s+(\w+): ", source[source.index("res.json({"):], re.M))
    assert {"image_digest", "image_digest_reason", "migration_set", "migration_set_reason", "deployed_sha", "revision"} <= emitted
    probe = (FLEET / "http_probe.py").read_text()
    assert 'doc.get("image_digest")' in probe and 'doc.get("migration_set")' in probe


def mcp_deploy_steps():
    text = (REPO / ".github/workflows/deploy.yml").read_text()
    start = text.index("- name: Build and push MCP image")
    end = text.index("- name: Wait for matching web revision")
    return {m.group(1): m.group(0) for m in re.finditer(r"- name: ([^\n]+)\n(?:(?!\n      - name:).)*", text[start:end], re.S)}


def test_h5_the_deploy_env_takes_the_digest_from_the_build_step_output():
    steps = mcp_deploy_steps()
    build = steps["Build and push MCP image (Artifact Registry, not gcr.io)"]
    assert "uses: docker/build-push-action@" in build
    step_id = re.search(r"^\s+id: (\S+)$", build, re.M).group(1)
    deploy = steps["Deploy MCP to Cloud Run (IAM-gated, least-priv SA)"]
    lines = [ln.strip() for ln in deploy.splitlines() if ln.strip().startswith("NIRMANA_IMAGE_DIGEST=")]
    assert lines == ["NIRMANA_IMAGE_DIGEST=${{ steps.%s.outputs.digest }}" % step_id]      # not DEPLOY_SHA, not a tag, not :latest


def test_h5_the_candidate_attestation_requires_the_stated_digest_to_equal_the_built_one():
    attest = mcp_deploy_steps()["Attest exact MCP candidate identity"]
    assert "EXPECTED_IMAGE_DIGEST: ${{ steps.mcp-image.outputs.digest }}" in attest
    assert ".image_digest == $digest" in attest and 'test("^sha256:[0-9a-f]{64}$")' in attest
