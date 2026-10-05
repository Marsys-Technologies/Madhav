"""C47 — the ephemeris directory under the REAL orchestrator (steward EPHE-RULING; conditions 1, 2, 3, 5, 6).

THE DEFECT: the real runner builds the writer context as `config = {chart_id, birth_params}` (asset_runner.py) — never `ephe_path` — while
the v5 writer read `ctx.config.get("ephe_path")` everywhere, so a real run did the whole body phase and then failed at the manifest
substep ('ephemeris: no ephe_path configured'). Every earlier test injected `ephe_path` by hand, so none could see it.

THE FIX (writer only; the orchestrator is frozen): `_ephe_path(ctx)` = `ctx.config['ephe_path']` when present, else the process environment
`SE_EPHE_PATH` (the variable the Swiss C library honours; the pipeline image sets it), refused BY NAME at the first substep when neither is
set, or the directory is missing, or lacks a pinned file. No default.

HERE, no shim: the real entry point `python -m pipeline.orchestrator.main --run-id <id>` runs as a SUBPROCESS over a database with the real
orchestrator tables (migrations 167..1201) and an INACTIVE registry row in the 1304 shape, with the variable set and unset.
"""
from __future__ import annotations

import json
import os
import types
from pathlib import Path

import psycopg
import pytest

from pipeline.orchestrator import runner as runner_mod  # noqa: F401  (the real runner module must import)
from pipeline.orchestrator.asset_runner import get_writer_source_hash
from pipeline.orchestrator.writers import ContextSpec, SubStep, WRITER_REGISTRY, discover_all
from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod

from . import _runner_world as rw
from .conftest import EPHE_PATH
from .test_a55_replace_chain import CHART_ID, _World, template  # noqa: F401

ONE_CLASS = "marriage"
MARKER = {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": "one_class_full",
          "horizon": [writer_mod.DEFAULT_HORIZON[0].isoformat(), writer_mod.DEFAULT_HORIZON[1].isoformat()],
          "classes": [ONE_CLASS]}


# ── the resolver, in process ───────────────────────────────────────────────────────────────────────────────────────────────────

def _ctx(**config):
    return types.SimpleNamespace(config=config)


def test_a_config_supplied_path_is_used_and_the_same_directory_in_the_environment_is_accepted(monkeypatch, tmp_path):
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)
    assert writer_mod._ephe_path(_ctx(ephe_path=EPHE_PATH)) == EPHE_PATH
    link = tmp_path / "corpus"
    link.symlink_to(EPHE_PATH)                                  # the same REAL directory under another spelling
    monkeypatch.setenv("SE_EPHE_PATH", str(link))
    assert writer_mod._ephe_path(_ctx(ephe_path=EPHE_PATH)) == EPHE_PATH


def test_with_no_config_the_environment_variable_is_used(monkeypatch):
    monkeypatch.setenv("SE_EPHE_PATH", EPHE_PATH)
    assert writer_mod._ephe_path(_ctx()) == EPHE_PATH
    assert writer_mod._ephe_path(_ctx(ephe_path=None)) == EPHE_PATH         # None is 'absent': it falls back


def test_neither_configured_is_refused_by_name_there_is_no_default(monkeypatch):
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)
    monkeypatch.setenv("SWE_EPHE_PATH", EPHE_PATH)          # the older variable is NOT a fallback; neither is /app/ephe
    with pytest.raises(writer_mod.EphemerisConfigRefusal, match=r"no Swiss Ephemeris directory is configured.*SE_EPHE_PATH"):
        writer_mod._ephe_path(_ctx())
    monkeypatch.setenv("SE_EPHE_PATH", "")
    with pytest.raises(writer_mod.EphemerisConfigRefusal, match="no Swiss Ephemeris directory is configured"):
        writer_mod._ephe_path(_ctx(ephe_path=None))


@pytest.mark.parametrize("value", ["", "   ", 0, 5, [], {}])
def test_an_explicitly_supplied_unusable_config_value_is_refused_and_never_read_as_absent(monkeypatch, value):
    """Codex P3: only a missing key or None falls back to the environment; anything else that is supplied must be a usable path."""
    monkeypatch.setenv("SE_EPHE_PATH", EPHE_PATH)
    with pytest.raises(writer_mod.EphemerisConfigRefusal, match="was supplied as .* not a usable path"):
        writer_mod._ephe_path(_ctx(ephe_path=value))


def test_a_missing_directory_or_a_missing_pinned_file_is_refused_by_name(monkeypatch, tmp_path):
    monkeypatch.setenv("SE_EPHE_PATH", str(tmp_path / "nowhere"))
    with pytest.raises(writer_mod.EphemerisConfigRefusal, match="is not a directory"):
        writer_mod._ephe_path(_ctx())
    for name in writer_mod.PINNED_EPHE_FILES[:2]:
        (tmp_path / name).write_bytes(b"x")
    monkeypatch.setenv("SE_EPHE_PATH", str(tmp_path))
    with pytest.raises(writer_mod.EphemerisConfigRefusal, match=r"lacks the pinned file\(s\) \['seas_18.se1'\]"):
        writer_mod._ephe_path(_ctx())


def test_a_bad_config_path_is_refused_and_is_never_replaced_by_the_environment(monkeypatch, tmp_path):
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)
    with pytest.raises(writer_mod.EphemerisConfigRefusal, match=r"ctx\.config\['ephe_path'\].*is not a directory"):
        writer_mod._ephe_path(_ctx(ephe_path=str(tmp_path / "nowhere")))
    monkeypatch.setenv("SE_EPHE_PATH", EPHE_PATH)
    with pytest.raises(writer_mod.EphemerisConfigRefusal, match="name different directories"):    # and a valid environment does not rescue it
        writer_mod._ephe_path(_ctx(ephe_path=str(tmp_path / "nowhere")))


def test_a_config_path_and_an_environment_path_that_differ_are_refused_on_real_calculations_too(monkeypatch, tmp_path):
    """Codex P2: the string precedence alone is not enough. The Swiss library honours SE_EPHE_PATH itself after set_ephe_path(<config>),
    so a valid config path with an environment variable naming ANOTHER directory would let calculations use the other corpus. The
    resolver refuses before any calculation, in the real substep path; and with both naming the same directory a real calculation runs."""
    monkeypatch.setenv("SE_EPHE_PATH", str(tmp_path / "nonexistent"))

    class Untouched:
        row_factory = None

        def __getattr__(self, name):
            raise AssertionError(f"connection used: {name}")
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="x", db_conn=Untouched(), dry_run=False,
                      config={"chart_id": CHART_ID, "ephe_path": EPHE_PATH})
    for key in (writer_mod.RULES_SUBSTEP, f"{writer_mod.BODY_SUBSTEP_PREFIX}Sun", writer_mod.MANIFEST_SUBSTEP):
        with pytest.raises(writer_mod.EphemerisConfigRefusal, match="name different directories"):
            writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=key, label=key))
    monkeypatch.setenv("SE_EPHE_PATH", EPHE_PATH)
    from services.gochara_kernel.knots import calc_sidereal_lon
    lon, retflag = calc_sidereal_lon("Sun", 2451545.0, writer_mod._ephe_path(_ctx(ephe_path=EPHE_PATH)))
    assert retflag & 2 and 0.0 <= lon < 360.0                    # a real Swiss-file calculation through the resolved path


def _corpus_copy(tmp_path):
    import shutil
    for name in writer_mod.PINNED_EPHE_FILES:
        shutil.copy(os.path.join(EPHE_PATH, name), tmp_path / name)
    return tmp_path


def test_a_file_that_is_not_the_pinned_bytes_is_refused_before_any_computation(monkeypatch, tmp_path):
    """Codex P2: one corpus across the build. Same names and sizes, one byte changed: refused by name (every substep, so the bodies and the
    manifest cannot run over different bytes)."""
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)
    corpus = _corpus_copy(tmp_path)
    assert writer_mod._ephe_path(_ctx(ephe_path=str(corpus))) == str(corpus)                       # an exact copy passes
    target = corpus / "semo_18.se1"
    data = bytearray(target.read_bytes())
    data[len(data) // 2] ^= 0x01
    target.write_bytes(bytes(data))
    with pytest.raises(writer_mod.EphemerisConfigRefusal, match=r"semo_18\.se1 .* is not the pinned corpus: sha256 [0-9a-f]{64} != pinned "):
        writer_mod._ephe_path(_ctx(ephe_path=str(corpus)))


def test_the_pin_check_is_cached_per_path_size_and_mtime_so_the_cost_is_paid_once(monkeypatch, tmp_path):
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)
    corpus = _corpus_copy(tmp_path)
    reads = []
    original = Path.read_bytes

    def counting(self):
        reads.append(self.name)
        return original(self)
    monkeypatch.setattr(Path, "read_bytes", counting)
    writer_mod._PIN_VERIFIED.clear()
    for _ in range(5):
        writer_mod._ephe_path(_ctx(ephe_path=str(corpus)))
    assert sorted(reads) == sorted(writer_mod.PINNED_EPHE_FILES), reads                         # each file hashed ONCE for five substeps
    os.utime(corpus / "sepl_18.se1", (1, 1))                                                    # a touched file is hashed again
    writer_mod._ephe_path(_ctx(ephe_path=str(corpus)))
    assert reads.count("sepl_18.se1") == 2 and reads.count("semo_18.se1") == 1


def test_the_pins_agree_across_the_constant_the_dockerfile_ci_swiss_backend_and_the_conftest():
    import re
    from panchang_engine import swiss_backend
    from services.gochara_kernel.ephemeris_pins import PINNED_SE1_SHA256 as pins
    from .conftest import SE1_CHECKSUMS
    assert dict(SE1_CHECKSUMS) == pins and dict(swiss_backend._PINNED_SHA256) == pins
    docker = (rw.REPO / "platform/python-sidecar/Dockerfile.pipeline").read_text(encoding="utf-8")
    ci = (rw.REPO / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for name, digest in pins.items():
        assert re.search(rf"{digest}\s+/app/ephe/{re.escape(name)}", docker), f"Dockerfile.pipeline does not pin {name} to {digest}"
        assert re.search(rf"{digest}\s+{re.escape(name)}", ci), f"ci.yml does not pin {name} to {digest}"
    # every sha256sum line CI writes for a corpus file carries one of the pins (a stale digest anywhere fails here)
    for digest, name in re.findall(r"'([0-9a-f]{64})\s+((?:sepl|semo|seas)_18\.se1)'", ci):
        assert pins[name] == digest, f"ci.yml pins {name} to a different digest {digest}"


def test_the_first_substep_refuses_before_anything_is_written(monkeypatch):
    """'rules' is the first substep: refusal happens before the rule registry is touched, so a mis-provisioned job fails in seconds."""
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)

    class Boom:
        row_factory = None                                 # the writer only inspects this to adapt row shape

        def __getattr__(self, name):                      # any USE of the connection (execute, cursor, transaction...) fails the test
            raise AssertionError(f"connection used: {name}")
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="x", db_conn=Boom(), dry_run=False, config={"chart_id": CHART_ID})
    with pytest.raises(writer_mod.EphemerisConfigRefusal):
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.RULES_SUBSTEP, label="rules"))


def test_no_substep_reads_ephe_path_straight_from_the_config():
    """The seven bare reads are gone: every use goes through the resolver (mutation guard for a half-applied fix)."""
    source = open(writer_mod.__file__, encoding="utf-8").read()
    assert 'config.get("ephe_path")' not in source
    assert source.count("_ephe_path(ctx)") >= 8


def test_the_other_config_keys_the_writer_reads_are_defaulted_not_required():
    """EPHE-RULING condition 6: the keys the v5 writer reads from ctx.config that the real runner never supplies."""
    source = open(writer_mod.__file__, encoding="utf-8").read()
    keys = sorted(set(__import__("re").findall(r'ctx\.config(?:\.get)?[\[(]\s*"([a-z_]+)"', source)))
    assert keys == ["chart_id", "ephe_path", "horizon", "result_policy"], keys      # chart_id supplied; ephe_path: this fix; the rest default
    assert "DEFAULT_HORIZON" in source and "DEFAULT_RESULT_POLICY" in source


# ── the REAL entry point ───────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def rworld(template):
    w = _World(template)
    try:
        rw.apply_orchestrator_schema(w.conn)
        discover_all()
        rw.seed_registry(w.conn, set(WRITER_REGISTRY) - {"bg_nakshatra_medical", "bg_transit_engine"})
        w.run_id = rw.stage_run(w.conn, MARKER, get_writer_source_hash(writer_mod.ASSET_ID))
        yield w
    finally:
        w.close()


def _row(w, sql, *args):
    return w.conn.execute(sql, args).fetchone()


def test_real_runner_with_the_variable_unset_refuses_at_the_first_substep_in_seconds(rworld):
    w = rworld
    out = rw.run_real_entry_point(w.dsn, w.run_id, ephe_env=None)
    events = rw.substep_events(out["stdout"])
    run = _row(w, "SELECT state FROM public.build_runs WHERE id = %s", w.run_id)[0]
    asset = _row(w, "SELECT state, error FROM public.build_run_assets WHERE run_id = %s", w.run_id)
    print("UNSET:", {"code": out["code"], "seconds": round(out["seconds"], 1), "run": run, "asset": asset, "events": len(events)})
    assert run == "failed" and asset[0] != "completed", (run, asset, out["stderr"][-2000:])
    assert "no Swiss Ephemeris directory is configured" in (asset[1] or "")
    assert events == [], "no substep completed: the FIRST one refused"
    assert _row(w, "SELECT count(*) FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", CHART_ID)[0] == 0
    assert out["seconds"] < 120, out["seconds"]


def test_real_runner_with_the_variable_set_runs_the_slice(rworld, template):
    """Through the real runner, SE_EPHE_PATH set, no config path, class `marriage`. What this shows and what it does not:

    SHOWN: the writer runs under the real orchestrator past the point where it used to die: rules, convention, the 8 body substeps, the
    manifest (stamped test_slice, vector binds the sha256 of the .se1 files actually opened), the snapshot, the class's inventory and
    coverage and its FIRST record grain (P1, whose anchor verification passes for this class) all COMPLETE, and the ephemeris identity equals
    the one a config-supplied path produces. The registry row stayed INACTIVE.
    NOT ASSERTED (observed, and deliberately not pinned here so a fix does not need this test changed): the run does not complete. On this
    database it goes on through record P2 to P4 and window P1 and P2, then stops at window P3 on 'member geometry verification' of
    zero-length (grazing) contacts (window_verifier.py:668); that is a separate defect awaiting its own ruling. The class is `marriage`, not
    the first scored class: achievement_recognition (and 7 other classes whose signature houses are unknown) fail at P1 for a structural
    reason that does not depend on the ephemeris path (ruling P1-EMPTY-CLASS). So NO completed slice through the real runner is shown."""
    w = rworld
    out = rw.run_real_entry_point(w.dsn, w.run_id, ephe_env=EPHE_PATH)
    events = rw.substep_events(out["stdout"])
    keys = [e["substep_key"] for e in events]
    run = _row(w, "SELECT state FROM public.build_runs WHERE id = %s", w.run_id)[0]
    asset = _row(w, "SELECT state, error FROM public.build_run_assets WHERE run_id = %s", w.run_id)
    manifest = _row(w, "SELECT input_generation_vector FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'",
                    CHART_ID)
    print("SET:", {"code": out["code"], "seconds": round(out["seconds"], 1), "run": run, "asset_state": asset[0], "substeps": keys,
                   "error_head": (asset[1] or "")[:160]})
    expected_head = ["rules", "convention"] + [f"body:{b}" for b in writer_mod.SUBSTRATE_BODIES] + \
        [writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP, f"inventory:{ONE_CLASS}", f"coverage:{ONE_CLASS}",
         f"record:{ONE_CLASS}:P1"]
    assert keys[:len(expected_head)] == expected_head, (keys, out["stderr"][-2000:])
    assert manifest is not None and manifest[0]["stored_scope"] == "test_slice"
    assert manifest[0]["ephemeris"]["files"], "the vector binds the sha256 of the files actually opened"
    assert _row(w, "SELECT is_active FROM public.asset_registry WHERE asset_id = 'ka_gochara_v5'")[0] is False
    assert "no Swiss Ephemeris directory" not in (asset[1] or "")
    assert "P1 anchor verification failed" not in (asset[1] or ""), (asset[1] or "")[:400]
    # the env fallback must give the SAME ephemeris identity as a config-supplied path (content digests, not the path string)
    clone = _World(template)
    try:
        ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="cfg", db_conn=clone.conn, dry_run=False,
                          config={"chart_id": CHART_ID, "ephe_path": EPHE_PATH, "horizon": writer_mod.DEFAULT_HORIZON})
        with clone.conn.transaction():
            writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label="manifest"))
        cfg_vector = clone.conn.execute("SELECT input_generation_vector FROM public.kala_gochara_publication WHERE chart_id = %s"
                                        " AND generation = '5.0'", (CHART_ID,)).fetchone()[0]
    finally:
        clone.close()
    assert manifest[0]["ephemeris"] == cfg_vector["ephemeris"]
