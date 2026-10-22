"""AMD64-DOCKER (ruling SR-T24-AMD64-DOCKER, owner surrogate madhav-44; TR blocker T24/B8): the one linux/amd64 slice of a TR head runs in a linux/amd64 Docker container on this Mac
(Docker Desktop emulation) against a PG 15 / locale C sibling container on a private network.  One oracle per distinct claim, each failing on its single planted reversion
(`mutants_amd64.py`, ids AD-*).  Docker itself is a stand-in (a recording fake CLI); the real container run is the job's smoke, not a test.

AD-1  the architecture of the run is READ inside the container: no probe, a probe from outside, another run's nonce, or a machine that is not x86_64 on linux is refused
AD-2  G-5 is NOT_EVALUATED for a run executed under emulation, whatever the class count and load (its wall time is not used; SR-G5-LOAD); an ordinary run is computed as before
AD-3  the emulation is DETECTED (engine architecture + the container's CPU) and recorded as rosetta|qemu|undetermined; an unreadable engine is refused, never assumed native
AD-4  the containers are linux/amd64, the sibling PG is PG 15 locale C on an INTERNAL network with no published port, the slice shares its namespace, code and chart data are read-only
AD-5  the 4-class slice only
AD-6  the Dockerfile is the deploy one with ONLY the network fetch of the ephemeris replaced (pinned corpus + the Dockerfile's own sha256 checks); a moved Dockerfile or a corpus that
      does not match its checks is refused
AD-7  everything the run created is removed at the end — also when the slice fails — and an image asked for by digest is used by digest or not at all
AD-8  the finished run attaches the `platform` block (wall_comparable false under emulation) to its report only from a valid in-container probe
AD-9  run_trial.sh TRIAL_AMD64_DOCKER=1 asks for the container slice (bound to TRIAL_CODE_HEAD)
AD-10 a run whose driver was killed after the container ran to its end is finished from its out directory — never while the container still runs — and torn down
[doctrine: SR-T24-AMD64-DOCKER and SR-G5-LOAD (owner surrogate rulings, ~20:36Z 2026-10-22); R-2026-10-15-02 (the pinned ephemeris, never a network fetch); root CLAUDE.md §N.8 —
a signal is read from the machine it describes, never asserted]"""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import amd64_docker as ad
import fixtures as fx
import gates
import trial_eval as te
import trial_slice as ts

HARNESS = Path(__file__).resolve().parents[1]
NONCE = "feedfacecafe0001"
DIGEST = "sha256:" + "ab" * 32
LOCK = "cd" * 32


def probe(**over):
    p = {"schema": ad.PROBE_SCHEMA, "source": "in_container", "nonce": NONCE, "uname_machine": "x86_64", "uname_sysname": "Linux", "uname_release": "7.0.14-linuxkit",
         "platform_machine": "x86_64", "sys_platform": "linux", "python": "3.11.15", "python_implementation": "CPython", "pointer_bits": 64,
         "cpu": {"vendor_id": "VirtualApple", "model_name": "VirtualApple @ 2.50GHz"}, "dependency_lock_digest": LOCK, "distributions": 200, "swiss": {"swe_version": "2.10.03"},
         "dockerenv": True}
    p.update(over)
    return p


ROSETTA = {"emulated": True, "layer": "rosetta", "engine": {"arch": "aarch64"}}
NATIVE = {"emulated": False, "layer": None, "engine": {"arch": "x86_64"}}


def block(p=None, emulation=ROSETTA, nonce=NONCE, image=DIGEST):
    return ad.runtime_block(probe() if p is None else p, nonce=nonce, emulation=emulation, image_digest=image)


# ── AD-1 ────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_ad1_the_arch_is_read_inside_the_container_and_builds_the_qualifying_runtime():
    """SR-T24-AMD64-DOCKER: 'arch must still read linux/amd64 from inside the container - uname -m == x86_64'.  A valid probe yields runtime.kind qualifying_run / linux/amd64, the
    probe's own python and lock digest, `arch_probe` as evidence, the emulation note for E6 and a `platform` block with wall_comparable false."""
    b = block()
    assert b["runtime"]["kind"] == "qualifying_run" and b["runtime"]["arch"] == "linux/amd64" and b["runtime"]["python"] == "3.11.15"
    assert b["runtime"]["dependency_lock_digest"] == LOCK and b["runtime"]["emulated"] is True
    assert b["runtime"]["arch_probe"]["source"] == "in_container" and b["runtime"]["arch_probe"]["uname_machine"] == "x86_64"
    assert b["platform_notes"]["emulation"]["layer"] == "rosetta" and b["platform_notes"]["emulation"]["emulated"] is True
    assert b["platform"]["wall_comparable"] is False and b["platform"]["arch_read_from"] == "in_container_probe"
    assert block(emulation=NATIVE)["platform"]["wall_comparable"] is True and block(emulation=NATIVE)["platform_notes"] == {}


@pytest.mark.parametrize("bad", [{"source": "host_assertion"}, {"schema": "something/else"}])
def test_ad1_a_probe_that_was_not_taken_inside_the_container_is_refused(bad):
    with pytest.raises(ad.Amd64Refused, match="no in-container runtime probe"):
        block(probe(**bad))


def test_ad1_no_probe_at_all_is_refused_an_arch_is_never_asserted_from_outside():
    with pytest.raises(ad.Amd64Refused, match="asserted from outside"):
        block(p={"arch": "linux/amd64"})          # a host-side assertion has no probe shape
    with pytest.raises(ad.Amd64Refused, match="asserted from outside"):
        ad.runtime_block(None, nonce=NONCE, emulation=ROSETTA, image_digest=DIGEST)


def test_ad1_another_runs_probe_is_refused():
    with pytest.raises(ad.Amd64Refused, match="another run's nonce"):
        block(probe(nonce="0000000000000000"))


@pytest.mark.parametrize("bad", [{"uname_machine": "aarch64"}, {"platform_machine": "arm64"}, {"sys_platform": "darwin"}])
def test_ad1_a_container_that_does_not_read_linux_x86_64_is_not_an_amd64_run(bad):
    with pytest.raises(ad.Amd64Refused, match="not linux/x86_64"):
        block(probe(**bad))


# ── AD-2 ────────────────────────────────────────────────────────────────────────────────────────────────────────

FAST = {"body": 330.0, "record": 800.0, "window": 50.0}
EFFECTIVE = "projected effective wall (compute + lock wait) ≤ limit"
PROJECTION = "projected century writer time ≤ limit"


def g5_with(platform=None):
    r = fx.a10_report()
    r["config"]["classes"] = list(gates.TRIAL_CLASSES_12)
    r["runtime_s"]["by_step_kind"] = dict(FAST)
    r["effective_wall"]["stages"] = {f"build:{k}": {"wall_s": v, "lock_wait_s": 0.0, "compute_s": v, "max_load_per_core": fx.QUIET_LOAD} for k, v in FAST.items()}
    if platform is not None:
        r["platform"] = platform
    v = gates.evaluate(r, fx.a10_baseline(), fx.profile(), decision_table=fx.decision_table(), dispatch_digests=fx.dispatch_digests(), verification=r["verification"])
    return v["gates"]["G-5"], r


def test_ad2_g5_is_not_evaluated_for_an_emulated_run_and_computed_as_before_for_any_other():
    """SR-T24-AMD64-DOCKER ('its wall time is NOT used for G-5; SR-G5-LOAD applies'): a 12-class, quiet, otherwise passing measurement reads PASS without a platform block and
    NOT_EVALUATED — on EVERY runtime check, the verifier's included — with the block of an emulated run."""
    ok, _ = g5_with()
    assert ok["status"] == gates.PASS
    emulated, rep = g5_with(block()["platform"])
    assert emulated["status"] == gates.NOT_EVALUATED, emulated["status"]
    wall_claims = {PROJECTION, EFFECTIVE, "verifier solver check ≤ per-class budget (projected to the century horizon)"}
    by_claim = {c["claim"]: c for c in emulated["checks"]}
    assert wall_claims <= set(by_claim)
    for claim in wall_claims:
        assert by_claim[claim]["status"] == gates.NOT_EVALUATED and "emulation" in by_claim[claim]["note"], by_claim[claim]
    assert gates.g5_runtime(rep, fx.profile(), rep["verification"])["status"] == gates.NOT_EVALUATED
    native, _ = g5_with(block(emulation=NATIVE)["platform"])
    assert native["status"] == gates.PASS                  # a non-emulated amd64 run's wall time is comparable


# ── AD-3 ────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_ad3_the_emulation_layer_is_detected_from_the_engine_and_the_containers_cpu():
    """Docker Desktop on Apple silicon: engine aarch64 + a linux/amd64 container = emulation; the CPU the container sees names the layer (Rosetta: VirtualApple, QEMU: a QEMU model)."""
    eng = {"Architecture": "aarch64", "OperatingSystem": "Docker Desktop", "ServerVersion": "29.8.2", "KernelVersion": "7.0.14-linuxkit"}
    r = ad.detect_emulation(eng, {"vendor_id": "VirtualApple", "model_name": "VirtualApple @ 2.50GHz"})
    assert r["emulated"] is True and r["layer"] == "rosetta" and r["engine"]["arch"] == "aarch64"
    assert ad.detect_emulation(eng, {"vendor_id": "GenuineIntel", "model_name": "QEMU Virtual CPU version 2.5+"})["layer"] == "qemu"
    assert ad.detect_emulation(eng, {})["layer"] == "undetermined"
    native = ad.detect_emulation({**eng, "Architecture": "x86_64"}, {"vendor_id": "GenuineIntel"})
    assert native["emulated"] is False and native["layer"] is None
    with pytest.raises(ad.Amd64Refused, match="engine architecture"):
        ad.detect_emulation({"OperatingSystem": "x"}, {"vendor_id": "VirtualApple"})


# ── AD-4 ────────────────────────────────────────────────────────────────────────────────────────────────────────

def arg_after(argv, flag):
    return argv[argv.index(flag) + 1]


def test_ad4_the_containers_are_linux_amd64_and_the_sibling_pg_is_15_locale_c_on_an_internal_network():
    """SR-T24-AMD64-DOCKER: 'linux/amd64 Docker container ... PG 15, locale C, in a SIBLING container on a private docker network ... chart data never leaves this Mac (no image push, no
    artifact upload)': internal network, no published port, locale C, the slice platform amd64 and in the PG's namespace, chart-data mounts read-only, nothing pushed."""
    net, pg = ad.network_argv("n1", "r1"), ad.pg_argv("pg1", "n1", "r1")
    assert "--internal" in net
    assert arg_after(pg, "-e") == "POSTGRES_HOST_AUTH_METHOD=trust" and "POSTGRES_INITDB_ARGS=--locale=C --encoding=UTF8" in pg and "postgres:15" in pg
    assert arg_after(pg, "--network") == "n1" and f"port={ad.PG_PORT}" in pg
    assert not {"-p", "--publish", "-P"} & set(pg)
    sl = ad.slice_argv(name="s1", pg="pg1", run_id="r1", image="img", harness=Path("/h"), code=Path("/c"), out=Path("/o"), ephe=Path("/e"), l1_export=Path("/l1"), head="a" * 40,
                       classes=["major_loss"], nonce=NONCE)
    assert arg_after(sl, "--platform") == "linux/amd64" and arg_after(sl, "--network") == "container:pg1"
    assert not {"-p", "--publish", "-P", "push"} & set(sl)
    mounts = [sl[i + 1] for i, a in enumerate(sl) if a == "-v"]
    assert "/c:/work/code:ro" in mounts and "/e:/e:ro" in mounts and "/l1:/l1:ro" in mounts and "/o:/work/out" in mounts
    assert all(m.endswith(":ro") for m in mounts if not m.startswith("/o:"))
    assert "TRIAL_CLASSES=major_loss" in sl and "TRIAL_CODE_HEAD=" + "a" * 40 in sl
    assert "amd64_probe.py --nonce " + NONCE in sl[-1] and sl[-1].index("amd64_probe.py") < sl[-1].index("run_trial.sh")      # the probe runs inside, BEFORE the slice
    assert ad.build_argv("t", Path("/x"))[:3] == ["build", "--platform", "linux/amd64"]


# ── AD-5 ────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_ad5_only_the_4_class_slice_is_accepted():
    assert ad.check_classes(["major_loss"]) == ["major_loss"] and ad.check_classes(list(te.FOUR_CLASS_SLICE)) == list(te.FOUR_CLASS_SLICE)
    assert ad.SLICE_CLASSES == te.FOUR_CLASS_SLICE
    for bad in ([], ["parental_event"], ["major_loss", "parental_event"], list(gates.TRIAL_CLASSES_12), ["major_loss", "major_loss"]):
        with pytest.raises(ad.Amd64Refused, match="4-class slice only"):
            ad.check_classes(bad)


# ── AD-6 ────────────────────────────────────────────────────────────────────────────────────────────────────────

HA, HB, HC = "11" * 32, "22" * 32, "33" * 32
DOCKERFILE = f"""FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc
# Swiss Ephemeris data files
RUN set -eu; \\
    mkdir -p /app/ephe; \\
    GCS_BASE="https://storage.googleapis.com/madhav-ephemeris/se1"; \\
    curl -fsSL -o /app/ephe/sepl_18.se1 "$GCS_BASE/sepl_18.se1"; \\
    curl -fsSL -o /app/ephe/sefstars.txt "$GCS_BASE/sefstars.txt"; \\
    echo '{HA}  /app/ephe/sepl_18.se1' | sha256sum -c -; \\
    echo '{HB}  /app/ephe/semo_18.se1' | sha256sum -c -; \\
    echo '{HC}  /app/ephe/seas_18.se1' | sha256sum -c -
ENV SE_EPHE_PATH=/app/ephe
COPY platform/python-sidecar/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY platform/python-sidecar/pipeline/ ./platform/python-sidecar/pipeline/
"""
PINNED = {"sepl_18.se1": HA, "semo_18.se1": HB, "seas_18.se1": HC}


def test_ad6_only_the_ephemeris_network_fetch_is_replaced_and_its_sha256_checks_are_kept():
    """R-2026-10-15-02 (the pinned ephemeris corpus, never a network fetch) with 'built from the dispatch head with the brahma-pipeline Dockerfile': every other line is the Dockerfile's;
    the three sha256 checks stay and are satisfied by the pinned files."""
    out = ad.derive_dockerfile(DOCKERFILE, PINNED)
    assert "storage.googleapis.com" not in out and "curl" not in out
    assert "COPY .pinned_ephe/sepl_18.se1 .pinned_ephe/semo_18.se1 .pinned_ephe/seas_18.se1 /app/ephe/" in out
    for f, h in PINNED.items():
        assert f"echo '{h}  /app/ephe/{f}' | sha256sum -c -" in out
    kept = [ln for ln in DOCKERFILE.split("\n") if not ln.startswith(("RUN set -eu", "    "))]
    assert all(ln in out.split("\n") for ln in kept), "a line outside the ephemeris block changed"
    assert ad.context_sources(out) == [".pinned_ephe/sepl_18.se1", ".pinned_ephe/semo_18.se1", ".pinned_ephe/seas_18.se1", "platform/python-sidecar/requirements.txt",
                                       "platform/python-sidecar/pipeline/"]


def test_ad6_a_corpus_that_does_not_match_the_dockerfiles_checks_or_a_moved_dockerfile_is_refused():
    with pytest.raises(ad.Amd64Refused, match="do not match"):
        ad.derive_dockerfile(DOCKERFILE, {**PINNED, "semo_18.se1": "00" * 32})
    with pytest.raises(ad.Amd64Refused, match="exactly one ephemeris RUN block"):
        ad.derive_dockerfile(DOCKERFILE.replace("mkdir -p /app/ephe", "mkdir -p /app/other"), PINNED)
    with pytest.raises(ad.Amd64Refused, match="cover"):
        ad.derive_dockerfile(DOCKERFILE.replace(f"    echo '{HC}  /app/ephe/seas_18.se1' | sha256sum -c -", f"    echo '{HC}  /app/ephe/other.se1' | sha256sum -c -"), PINNED)


def test_ad6_the_real_pipeline_dockerfile_derives_and_the_pinned_corpus_matches_its_checks():
    """Against the head's real Dockerfile.pipeline (skipped where the checkout has none): the derivation is accepted with the pinned corpus."""
    sidecar = Path(os.environ.get("KY_TEST_CHECKOUT", HARNESS.parents[4])) / "platform" / "python-sidecar" / "Dockerfile.pipeline"
    ephe = Path(ts.EPHE)
    if not sidecar.is_file() or not all((ephe / f).is_file() for f in ad.EPHE_FILES):
        pytest.skip("no Dockerfile.pipeline or no pinned corpus on this machine")
    pinned = {f: ad.sha_bytes((ephe / f).read_bytes()) for f in ad.EPHE_FILES}
    out = ad.derive_dockerfile(sidecar.read_text(), pinned)
    assert "storage.googleapis.com" not in out and "FROM python:3.11-slim" in out and "pip install --no-cache-dir -r requirements.txt" in out


# ── AD-7 ────────────────────────────────────────────────────────────────────────────────────────────────────────

class FakeDocker:
    """A recording docker CLI: containers/networks are kept in a dict; `run` of the slice returns the exit code the test sets."""

    def __init__(self, slice_exit=0, have_image=True, slice_writes=None):
        self.calls, self.containers, self.networks, self.slice_exit, self.have_image, self.slice_writes = [], {}, {}, slice_exit, have_image, slice_writes

    def __call__(self, *argv, timeout=120, check=True):
        self.calls.append(argv)
        cp = lambda out="", rc=0: subprocess.CompletedProcess(argv, rc, out, "")      # noqa: E731
        a = list(argv)
        if a[0] == "info":
            return cp(json.dumps({"Architecture": "aarch64", "OperatingSystem": "Docker Desktop", "ServerVersion": "29", "KernelVersion": "k", "NCPU": 14, "MemTotal": 1}))
        if a[:2] == ["image", "inspect"]:
            if len(a) > 3 and a[2] == "--format":
                return cp("sha256:" + "ef" * 32 + "|amd64|linux" if "{{.Architecture}}|{{.Os}}" in a[3] else "sha256:" + "12" * 32 + "|postgres@sha256:" + "34" * 32 + "|arm64")
            return cp(rc=0 if self.have_image else 1)
        if a[0] == "inspect":
            return cp("true" if a[-1] in self.containers else "", rc=0 if a[-1] in self.containers else 1)
        if a[0] == "network" and a[1] == "create":
            self.networks[a[-1]] = a[a.index("--label") + 1]
            return cp()
        if a[0] == "run" and "-d" in a:
            name = a[a.index("--name") + 1]
            self.containers[name] = a[a.index("--label") + 1]
            return cp(name)
        if a[0] == "exec":
            return cp("15.17|C|C|UTF8")
        if a[0] == "run":
            name = a[a.index("--name") + 1]
            out = Path(a[[i + 1 for i, x in enumerate(a) if x == "-v" and a[i + 1].endswith(":/work/out")][0]].split(":")[0])
            if self.slice_writes:
                (out / "runtime_probe.json").write_text(json.dumps(self.slice_writes))
            return cp("slice output", rc=self.slice_exit)
        if a[0] == "ps":
            lab = a[a.index("--filter") + 1].split("=", 1)[1] if "--filter" in a else ""
            return cp("\n".join(n for n, l in self.containers.items() if l == "ky.amd64_run=" + lab.split("=")[-1] or l.endswith(lab.split("=")[-1])))
        if a[0] == "rm":
            self.containers.pop(a[-1], None)
            return cp()
        if a[0] == "network" and a[1] == "ls":
            lab = a[a.index("--filter") + 1].split("=", 2)[-1]
            return cp("\n".join(n for n, l in self.networks.items() if l.endswith(lab)))
        if a[0] == "network" and a[1] == "rm":
            self.networks.pop(a[-1], None)
            return cp()
        return cp()


def run_with(tmp_path, docker, **kw):
    export = tmp_path / "export"
    (export / "platform").mkdir(parents=True, exist_ok=True)
    return ad.run(head="a" * 40, export=export, harness=HARNESS, out=tmp_path / "out", classes=["major_loss"], ephe=tmp_path / "ephe", l1_export=tmp_path / "l1",
                  docker=docker, image_digest=DIGEST, **kw)


def test_ad7_everything_the_run_created_is_removed_at_the_end_also_when_the_slice_fails(tmp_path):
    """SR-T24-AMD64-DOCKER ('containers and volumes removed at the end'; user policy 'remove that session's finished ... folders'): the PG container (with `rm -v`) and the network are
    gone after a complete run AND after a failing one; the record says what was removed and that nothing is left."""
    for exit_code, status in ((0, "complete"), (1, "failed")):
        d = FakeDocker(slice_exit=exit_code, slice_writes=probe())
        out = tmp_path / f"o{exit_code}"
        out.mkdir()
        rec = ad.run(head="a" * 40, export=tmp_path, harness=HARNESS, out=out, classes=["major_loss"], ephe=tmp_path, l1_export=tmp_path, docker=d, image_digest=DIGEST)
        assert rec["status"] == status and rec["stages"]["slice"]["exit"] == exit_code
        assert d.containers == {} and d.networks == {}, (d.containers, d.networks)
        assert rec["teardown"]["left"] == [] and rec["teardown"]["containers_removed"] and rec["teardown"]["network_removed"]
        assert ("rm", "-f", "-v", rec["teardown"]["containers_removed"][0]) in d.calls
        assert rec["pg"]["server_version"].startswith("15.") and rec["pg"]["lc_collate"] == "C" and rec["emulation"]["layer"] == "rosetta"


def test_ad7_the_run_is_torn_down_when_an_exception_ends_it_and_an_image_given_by_digest_is_never_silently_rebuilt(tmp_path):
    d = FakeDocker(have_image=False)
    with pytest.raises(ad.Amd64Refused, match="no silent rebuild"):
        run_with(tmp_path, d)
    assert not any(c[0] == "build" for c in d.calls) and not any(c[0] == "run" for c in d.calls)

    class Boom(FakeDocker):
        def __call__(self, *argv, **kw):
            if argv[0] == "run" and "-d" not in argv:
                raise RuntimeError("the slice command blew up")
            return super().__call__(*argv, **kw)
    b = Boom()
    with pytest.raises(RuntimeError):
        run_with(tmp_path / "b", b) if (tmp_path / "b").mkdir() is None else None
    assert b.containers == {} and b.networks == {}


def test_ad7_one_amd64_slice_per_head_and_a_head_is_required(tmp_path):
    with pytest.raises(ad.Amd64Refused, match="40-hex"):
        ad.run(head="main", export=tmp_path, harness=HARNESS, out=tmp_path / "o", classes=["major_loss"], ephe=tmp_path, l1_export=tmp_path, docker=FakeDocker())
    d = FakeDocker(slice_writes=probe())
    (tmp_path / "o").mkdir()
    ad.run(head="a" * 40, export=tmp_path, harness=HARNESS, out=tmp_path / "o", classes=["major_loss"], ephe=tmp_path, l1_export=tmp_path, docker=d, image_digest=DIGEST)
    with pytest.raises(ad.Amd64Refused, match="another head"):
        ad.run(head="b" * 40, export=tmp_path, harness=HARNESS, out=tmp_path / "o", classes=["major_loss"], ephe=tmp_path, l1_export=tmp_path, docker=d, image_digest=DIGEST)


# ── AD-8 ────────────────────────────────────────────────────────────────────────────────────────────────────────

def finished_run(tmp_path, probe_doc):
    out = tmp_path / "run"
    out.mkdir()
    (out / "state.json").write_text(json.dumps({"label": "amd64_slice", "code": {"head": "a" * 40, "branch": None}, "horizon": {}}))
    (out / "amd64_slice_report.json").write_text(json.dumps({"schema": "ky.trial_report/2", "config": {"classes": ["major_loss"]}, "code": {"head": "a" * 40}}))
    if probe_doc is not None:
        (out / "runtime_probe.json").write_text(json.dumps(probe_doc))
    rec = {"nonce": NONCE, "emulation": ROSETTA, "image": {"digest": DIGEST, "built": False}, "pg": {"server_version": "15.17"}, "engine": {"Architecture": "aarch64"},
           "stages": {"slice": {"status": "done", "exit": 0, "wall_s": 12.5}}, "teardown": {"left": []}}
    return out, rec


def test_ad8_the_report_carries_the_platform_block_only_from_a_valid_in_container_probe(tmp_path):
    """A finished container run: the report gets `platform` {qualifying_run, linux/amd64, emulated, wall_comparable false, arch read from the in-container probe} and the run record; the
    probe's python/lock reach the pinned runtime (the equivalence stage is NOT_RUN here: no repo).  A missing or forged probe is refused and the report is left untouched."""
    out, rec = finished_run(tmp_path, probe())
    fin = ts.amd64_finish(out, rec, eq_repo=None, eq_tool=None, pinned_extra=None)
    rep = json.loads((out / "amd64_slice_report.json").read_text())
    assert rep["platform"]["wall_comparable"] is False and rep["platform"]["arch"] == "linux/amd64" and rep["platform"]["arch_read_from"] == "in_container_probe"
    assert rep["amd64_docker"]["probe"]["uname_machine"] == "x86_64" and rep["amd64_docker"]["emulation"]["layer"] == "rosetta"
    assert fin["equivalence_record"]["status"] == "NOT_RUN" and rep["qualification"]["head"] == "a" * 40
    for name, doc in (("none", None), ("forged", probe(source="host_assertion")), ("arm", probe(uname_machine="aarch64"))):
        out2, rec2 = finished_run(tmp_path / name, doc) if (tmp_path / name).mkdir() is None else (None, None)
        with pytest.raises(ad.Amd64Refused):
            ts.amd64_finish(out2, rec2, eq_repo=None, eq_tool=None, pinned_extra=None)
        assert "platform" not in json.loads((out2 / "amd64_slice_report.json").read_text())


def test_ad8_the_runtime_and_the_emulation_note_reach_the_equivalence_stage(tmp_path, monkeypatch):
    """The equivalence stage is given runtime (kind qualifying_run, arch linux/amd64, the probe's python and lock digest, arch_probe) and provenance.platform_notes.emulation."""
    seen = {}

    def fake_emit(repo, head, pinned, out_dir, **kw):
        seen["pinned"] = pinned
        return {"status": "NOT_RUN", "reason": "test"}
    monkeypatch.setattr(te, "emit_equivalence_record", fake_emit)
    out, rec = finished_run(tmp_path, probe())
    (out / "input_vector.json").write_text(json.dumps({"schema": "v"}))
    ts.amd64_finish(out, rec, eq_repo=str(tmp_path), eq_tool=None, pinned_extra=None)
    rt = seen["pinned"]["runtime"]
    assert (rt["kind"], rt["arch"], rt["python"], rt["dependency_lock_digest"], rt["emulated"]) == ("qualifying_run", "linux/amd64", "3.11.15", LOCK, True)
    assert rt["arch_probe"]["source"] == "in_container" and seen["pinned"]["provenance"]["platform_notes"]["emulation"]["layer"] == "rosetta"
    assert seen["pinned"]["provenance"]["image_digest"] == DIGEST


# ── AD-9 ────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_ad9_run_trial_sh_asks_for_the_container_slice_bound_to_the_head():
    env = {**os.environ, "TRIAL_DRY_RUN": "1", "TRIAL_AMD64_DOCKER": "1", "TRIAL_CODE_HEAD": "b" * 40, "TRIAL_CLASSES": "major_loss", "TRIAL_PYTHON": sys.executable}
    r = subprocess.run(["bash", str(HARNESS / "run_trial.sh"), "/some/repo", "/some/out"], capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 0, r.stderr
    argv = r.stdout.split("\n")
    assert "amd64-run" in argv and argv[argv.index("--head") + 1] == "b" * 40 and argv[argv.index("--classes") + 1] == "major_loss" and "--repo" in argv
    no_head = subprocess.run(["bash", str(HARNESS / "run_trial.sh"), "/some/repo", "/some/out"], capture_output=True, text=True, timeout=30,
                             env={k: v for k, v in env.items() if k != "TRIAL_CODE_HEAD"})
    assert no_head.returncode != 0 and "TRIAL_CODE_HEAD" in no_head.stderr
    plain = subprocess.run(["bash", str(HARNESS / "run_trial.sh"), "/some/repo", "/some/out"], capture_output=True, text=True, timeout=30,
                           env={k: v for k, v in env.items() if k != "TRIAL_AMD64_DOCKER"})
    assert "amd64-run" not in plain.stdout.split("\n") and "run" in plain.stdout.split("\n")


# ── AD-10 ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_ad10_a_killed_driver_run_is_finished_from_its_out_dir_never_while_the_container_runs(tmp_path, monkeypatch, capsys):
    """The foreground session limit can kill the driver while the slice container runs on.  `amd64-finish` refuses while that container is up (a half-written report must not be
    attached), and after it ends attaches the platform block and tears the sibling PG and the network down."""
    out, rec = finished_run(tmp_path, probe())
    rec.update({"run_id": "r1", "names": {"network": "ky-amd64-r1", "pg": "ky-amd64-r1-pg", "slice": "ky-amd64-r1-slice"}, "engine": {"Architecture": "aarch64"}, "status": "resume"})
    rec["stages"] = {"slice": {"status": "running"}}
    (out / "amd64_run.json").write_text(json.dumps(rec))
    d = FakeDocker()
    d.containers.update({"ky-amd64-r1-pg": "ky.amd64_run=r1", "ky-amd64-r1-slice": "ky.amd64_run=r1"})
    d.networks["ky-amd64-r1"] = "ky.amd64_run=r1"
    real_ps = d.__call__

    def with_names(*argv, **kw):                  # `docker ps --format {{.Names}}` lists the running containers
        if argv[:1] == ("ps",) and "--format" in argv:
            return subprocess.CompletedProcess(argv, 0, "\n".join(d.containers), "")
        return real_ps(*argv, **kw)
    monkeypatch.setattr(ad, "Docker", lambda *a, **k: with_names)
    args = types_ns(out=str(out))
    assert ts.cmd_amd64_finish(args) == 2 and "still running" in capsys.readouterr().err
    assert "platform" not in json.loads((out / "amd64_slice_report.json").read_text())
    d.containers.pop("ky-amd64-r1-slice")
    assert ts.cmd_amd64_finish(args) == 0
    assert json.loads((out / "amd64_slice_report.json").read_text())["platform"]["wall_comparable"] is False
    assert d.containers == {} and d.networks == {}
    done = json.loads((out / "amd64_run.json").read_text())
    assert done["status"] == "complete" and done["stages"]["slice"]["exit"] is None and done["emulation"]["layer"] == "rosetta"


def types_ns(**kw):
    import types
    return types.SimpleNamespace(keep_image=False, eq_repo=None, eq_tool=None, pinned_extra=None, **kw)
