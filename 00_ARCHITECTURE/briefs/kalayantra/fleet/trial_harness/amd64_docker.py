"""AMD64-DOCKER (ruling SR-T24-AMD64-DOCKER, owner surrogate madhav-44; TR blocker T24/B8).  The one linux/amd64 slice of a TR head, run in a linux/amd64 Docker container on this Mac
(Docker Desktop emulation), against a PG 15 / locale C SIBLING container on a private (internal) docker network.  Stdlib only; nothing here imports the sidecar.

  derive_dockerfile / context_sources   the brahma-pipeline Dockerfile with ONE change: the ephemeris is COPYed from the pinned local corpus (R-2026-10-15-02: never a network fetch),
                                        under the Dockerfile's own three sha256 checks (which must equal the pinned files'); every other line is the deploy Dockerfile's
  check_classes                         the 4-class slice only (a subset of it for a smoke)
  detect_emulation                      docker info (the host side of the emulation) + the container's own CPU identity -> {emulated, layer: rosetta|qemu|undetermined, ...}
  runtime_block                         the EQUIVALENCE_RECORD runtime block + provenance platform note + report platform block, built ONLY from an in-container probe
                                        (`amd64_probe.py`: uname -m == x86_64, this run's nonce).  The architecture is read there, never asserted from outside.
  run                                   build/locate the image, start PG, run probe + slice in the container, tear down

What the run is, in the record: runtime.kind = qualifying_run, arch = linux/amd64 (from inside), the emulation named in provenance.platform_notes (E6, never compared) and in the report's
`platform` block, whose `wall_comparable: false` makes G-5 read NOT_EVALUATED (SR-G5-LOAD: the emulated wall time is not used).  No paid cloud, no hosted runner; the chart data
(the canonical L1 export) is mounted read-only into containers on internal networks and goes nowhere: no image push, no artifact upload, containers and volumes removed at the end.
Containers are joined by SHARING THE PG CONTAINER'S NETWORK NAMESPACE (`--network container:<pg>`): the harness's disposable-database guard then sees the server at 127.0.0.1:55433
like any local cluster — the guard is not relaxed, no GITHUB_ACTIONS shortcut."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import time
from pathlib import Path

SCHEMA = "ky.amd64_docker_run/1"
PROBE_SCHEMA = "ky.amd64_runtime_probe/1"
SLICE_CLASSES = ("bereavement", "chronic_onset", "illness_acute", "major_loss")      # == trial_eval.FOUR_CLASS_SLICE (pinned by a test)
PG_IMAGE = "postgres:15"
PG_PORT = 55433                                                                        # the harness's fixed ADMIN_DSN port; the container shares PG's loopback
LAYERS = ("rosetta", "qemu", "undetermined")
EPHE_FILES = ("sepl_18.se1", "semo_18.se1", "seas_18.se1")
PINNED_EPHE_DIR = ".pinned_ephe"
DOCKERFILE_REL = "platform/python-sidecar/Dockerfile.pipeline"
LABEL = "ky.amd64_run"
EX_RESUME = 75
SHA256 = re.compile(r"sha256:[0-9a-f]{64}")


class Amd64Refused(RuntimeError):
    """The run (or the record built from it) is refused: nothing is asserted, nothing is guessed (B.10)."""


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ── the Dockerfile ──────────────────────────────────────────────────────────────────────────────────────────────

def derive_dockerfile(text: str, pinned_sha256: dict[str, str]) -> str:
    """The deploy Dockerfile with the network-fetching ephemeris step replaced by a COPY of the pinned corpus plus the Dockerfile's OWN sha256 checks.  `pinned_sha256` = {file: sha of the
    local pinned file}; every check the Dockerfile declares must equal it (the pinned corpus IS the corpus the deploy image verifies), else the derivation is refused."""
    lines = text.split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.rstrip() == "RUN set -eu; \\" and i + 1 < len(lines) and "mkdir -p /app/ephe" in lines[i + 1]]
    if len(starts) != 1:
        raise Amd64Refused(f"{DOCKERFILE_REL}: expected exactly one ephemeris RUN block, found {len(starts)} — the Dockerfile moved, the derivation is not guessed")
    i = starts[0]
    j = i
    while lines[j].rstrip().endswith("\\"):
        j += 1
    block = "\n".join(lines[i:j + 1])
    declared = dict((Path(p).name, h) for h, p in re.findall(r"echo '([0-9a-f]{64})  (/app/ephe/[^']+)' \| sha256sum -c -", block))
    if sorted(declared) != sorted(EPHE_FILES):
        raise Amd64Refused(f"the Dockerfile's ephemeris checks cover {sorted(declared)}, not {sorted(EPHE_FILES)}")
    wrong = {f: (h, pinned_sha256.get(f)) for f, h in declared.items() if pinned_sha256.get(f) != h}
    if wrong:
        raise Amd64Refused(f"the pinned ephemeris files do not match the Dockerfile's sha256 checks: {sorted(wrong)}")
    new = ["# AMD64-DOCKER (SR-T24-AMD64-DOCKER): the pinned local corpus replaces the network fetch (R-2026-10-15-02); the Dockerfile's own sha256 checks are kept",
           "COPY " + " ".join(f"{PINNED_EPHE_DIR}/{f}" for f in EPHE_FILES) + " /app/ephe/",
           "RUN set -eu; \\"]
    checks = [f"    echo '{h}  /app/ephe/{f}' | sha256sum -c -" for f, h in sorted(declared.items())]
    new += [c + (" ; \\" if k < len(checks) - 1 else "") for k, c in enumerate(checks)]
    out = "\n".join(lines[:i] + new + lines[j + 1:])
    if "storage.googleapis.com" in out or re.search(r"\bcurl\b[^\n]*-o /app/ephe", out):
        raise Amd64Refused("the derived Dockerfile still fetches the ephemeris over the network")
    return out


def context_sources(dockerfile: str) -> list[str]:
    """Every source path the Dockerfile COPYs from the build context (no `--from`)."""
    srcs: list[str] = []
    for ln in dockerfile.split("\n"):
        t = ln.split()
        if len(t) >= 3 and t[0] == "COPY" and not t[1].startswith("--"):
            srcs += t[1:-1]
    return srcs


def assemble_context(dockerfile: str, export: Path, ephe: Path, ctx: Path) -> dict:
    """Build the (small) docker context: only what the Dockerfile COPYs, from the git-archive export of the head and the pinned corpus; the derived Dockerfile as `Dockerfile`."""
    if ctx.exists():
        shutil.rmtree(ctx)
    ctx.mkdir(parents=True)
    copied = []
    for s in context_sources(dockerfile):
        src = (ephe / Path(s).name) if s.startswith(PINNED_EPHE_DIR + "/") else (export / s)
        dst = ctx / s
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not src.exists():
            raise Amd64Refused(f"the Dockerfile COPYs {s}, which the head's export does not carry")
        shutil.copytree(src, dst) if src.is_dir() else shutil.copy2(src, dst)
        copied.append(s)
    (ctx / "Dockerfile").write_text(dockerfile)
    return {"copied": copied, "dockerfile_sha256": sha_bytes(dockerfile.encode())}


# ── the slice ───────────────────────────────────────────────────────────────────────────────────────────────────

def check_classes(classes) -> list[str]:
    """The 4-class slice only (SR-T24-AMD64-DOCKER): a non-empty subset of the four ruled classes."""
    classes = list(classes or [])
    if not classes or len(set(classes)) != len(classes) or any(c not in SLICE_CLASSES for c in classes):
        raise Amd64Refused(f"the amd64 slice runs the 4-class slice only ({', '.join(SLICE_CLASSES)}); asked for {classes}")
    return classes


def _norm_arch(a: str | None) -> str | None:
    return {"aarch64": "arm64", "arm64": "arm64", "x86_64": "amd64", "amd64": "amd64"}.get((a or "").lower())


def detect_emulation(info: dict, cpu: dict | None) -> dict:
    """Is this docker engine running linux/amd64 containers by emulation, and by which layer?  `info` = `docker info` (the engine's own architecture); `cpu` = the CPU identity the container
    saw (/proc/cpuinfo: Rosetta reports vendor VirtualApple, QEMU a QEMU model).  An engine whose architecture cannot be read is refused — never assumed native."""
    server = _norm_arch(info.get("Architecture"))
    if server is None:
        raise Amd64Refused(f"docker info reports no readable engine architecture ({info.get('Architecture')!r}): emulation cannot be told")
    cpu = cpu or {}
    emulated = server != "amd64"
    layer = None
    if emulated:
        ident = f"{cpu.get('vendor_id') or ''} {cpu.get('model_name') or ''}".lower()
        layer = "rosetta" if "virtualapple" in ident else "qemu" if "qemu" in ident else "undetermined"
    return {"emulated": emulated, "layer": layer, "engine": {"os": info.get("OperatingSystem"), "arch": info.get("Architecture"), "version": info.get("ServerVersion"),
                                                              "kernel": info.get("KernelVersion")},
            "cpu_seen_in_container": {"vendor_id": cpu.get("vendor_id"), "model_name": cpu.get("model_name")},
            "detected_by": "docker info (engine architecture) + the container's /proc/cpuinfo"}


def runtime_block(probe: dict | None, *, nonce: str, emulation: dict, image_digest: str) -> dict:
    """The runtime facts of the run, from the IN-CONTAINER probe only.  Refused (nothing built) unless the probe is this run's (schema, source `in_container`, nonce), the machine it
    reports is x86_64 on linux, and the image digest is a sha256.  Returns {runtime (pinned-inputs runtime block), platform_notes (E6), platform (report block)}."""
    if not isinstance(probe, dict) or probe.get("schema") != PROBE_SCHEMA or probe.get("source") != "in_container":
        raise Amd64Refused("no in-container runtime probe: the architecture of a qualifying run is read inside the container, never asserted from outside")
    if probe.get("nonce") != nonce:
        raise Amd64Refused("the runtime probe carries another run's nonce")
    if probe.get("uname_machine") != "x86_64" or probe.get("platform_machine") not in ("x86_64", "AMD64") or probe.get("sys_platform") != "linux":
        raise Amd64Refused(f"the container reports {probe.get('sys_platform')}/{probe.get('uname_machine')}, not linux/x86_64: this is not a linux/amd64 run")
    if not re.fullmatch(r"[0-9a-f]{64}", str(probe.get("dependency_lock_digest"))) or not probe.get("python"):
        raise Amd64Refused("the probe carries no python version or dependency-lock digest")
    if not SHA256.fullmatch(str(image_digest)):
        raise Amd64Refused(f"image digest {image_digest!r} is not sha256:<64 hex>")
    if not isinstance(emulation, dict) or not isinstance(emulation.get("emulated"), bool) or (emulation["emulated"] and emulation.get("layer") not in LAYERS):
        raise Amd64Refused("the emulation record must say emulated true/false and, when true, the layer (rosetta|qemu|undetermined)")
    arch = "linux/amd64"                                      # = sys_platform / the normalised machine the PROBE read
    rt = {"kind": "qualifying_run", "arch": arch, "python": probe["python"], "dependency_lock_digest": probe["dependency_lock_digest"], "emulated": emulation["emulated"],
          "arch_probe": {"source": "in_container", "uname_machine": probe["uname_machine"], "platform_machine": probe["platform_machine"], "sys_platform": probe["sys_platform"],
                         "nonce_sha256": sha_bytes(nonce.encode())}}
    notes = {"emulation": {**emulation, "wall_time": "not comparable; not used for G-5 (SR-G5-LOAD)", "ruling": "SR-T24-AMD64-DOCKER"}} if emulation["emulated"] else {}
    plat = {"kind": "qualifying_run", "arch": arch, "emulated": emulation["emulated"], "emulation_layer": emulation.get("layer"), "image_digest": image_digest,
            "wall_comparable": not emulation["emulated"], "arch_read_from": "in_container_probe", "python": probe["python"],
            "ruling": "SR-T24-AMD64-DOCKER"}
    return {"runtime": rt, "platform_notes": notes, "platform": plat}


# ── docker ──────────────────────────────────────────────────────────────────────────────────────────────────────

class Docker:
    """The docker CLI, with a scrubbed environment (no credential, no GIT_*, no DOCKER_HOST override) and an explicit timeout on every call."""

    def __init__(self, binary: str | None = None):
        self.binary = binary or shutil.which("docker", path="/usr/local/bin:/opt/homebrew/bin:/usr/bin") or "docker"
        self.env = {"PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin", "HOME": os.environ.get("HOME", "/tmp")}

    def __call__(self, *argv: str, timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess:
        r = subprocess.run([self.binary, *argv], capture_output=True, text=True, timeout=timeout, env=self.env)
        if check and r.returncode != 0:
            raise Amd64Refused(f"docker {' '.join(argv[:3])} failed (exit {r.returncode}): {(r.stderr or r.stdout).strip()[-300:]}")
        return r


def build_argv(image_tag: str, ctx: Path) -> list[str]:
    return ["build", "--platform", "linux/amd64", "--pull=false", "--label", f"{LABEL}=build", "-t", image_tag, str(ctx)]


def network_argv(name: str, run_id: str) -> list[str]:
    return ["network", "create", "--internal", "--label", f"{LABEL}={run_id}", name]


def pg_argv(name: str, net: str, run_id: str, image: str = PG_IMAGE) -> list[str]:
    """PG 15, locale C, on the private network: no published port, data on tmpfs (nothing to clean), trust auth reachable only inside the namespace."""
    return ["run", "-d", "--name", name, "--network", net, "--label", f"{LABEL}={run_id}", "--tmpfs", "/var/lib/postgresql/data:rw,size=16g", "--shm-size", "1g",
            "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "-e", "POSTGRES_INITDB_ARGS=--locale=C --encoding=UTF8", image, "-c", f"port={PG_PORT}", "-c", "listen_addresses=*"]


def slice_argv(*, name: str, pg: str, run_id: str, image: str, harness: Path, code: Path, out: Path, ephe: Path, l1_export: Path, head: str, classes: list[str],
               nonce: str, label: str = "amd64_slice", budget_s: int | None = None, extra_env: dict | None = None) -> list[str]:
    """`docker run` of the slice: linux/amd64, joined to the PG container's network namespace, code/harness/ephemeris/L1 export read-only, only the out dir writable."""
    env = {"TRIAL_PYTHON": "python", "TRIAL_CODE_HEAD": head, "TRIAL_CLASSES": ",".join(check_classes(classes)), "TRIAL_LABEL": label, "TRIAL_VERIFY": "1",
           "TRIAL_BASELINE": "/work/harness/baseline_12.json", "TRIAL_PROFILE": "/work/harness/gate_profile.plan_defaults.json", "HOME": "/tmp", "PYTHONDONTWRITEBYTECODE": "1"}
    if budget_s:
        env["TRIAL_BUDGET_S"] = str(budget_s)
    env.update(extra_env or {})
    script = f"set -e; python -I /work/harness/amd64_probe.py --nonce {nonce} --out /work/out/runtime_probe.json; exec bash /work/harness/run_trial.sh /work/code /work/out"
    argv = ["run", "--rm", "--name", name, "--platform", "linux/amd64", "--network", f"container:{pg}", "--label", f"{LABEL}={run_id}", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--entrypoint", "bash",
            "-v", f"{harness}:/work/harness:ro", "-v", f"{code}:/work/code:ro", "-v", f"{out}:/work/out", "-v", f"{ephe}:{ephe}:ro", "-v", f"{l1_export}:{l1_export}:ro"]
    for k, v in sorted(env.items()):
        argv += ["-e", f"{k}={v}"]
    return argv + [image, "-c", script]


def teardown(docker: Docker, run_id: str) -> dict:
    """Remove everything this run created, found by label: containers (with their volumes), then the network.  Reports what was removed and what is still there."""
    rep = {"containers_removed": [], "network_removed": [], "left": []}
    for cid in docker("ps", "-aq", "--filter", f"label={LABEL}={run_id}", check=False).stdout.split():
        docker("rm", "-f", "-v", cid, check=False)
        rep["containers_removed"].append(cid)
    for nid in docker("network", "ls", "-q", "--filter", f"label={LABEL}={run_id}", check=False).stdout.split():
        docker("network", "rm", nid, check=False)
        rep["network_removed"].append(nid)
    rep["left"] = (docker("ps", "-aq", "--filter", f"label={LABEL}={run_id}", check=False).stdout.split()
                   + docker("network", "ls", "-q", "--filter", f"label={LABEL}={run_id}", check=False).stdout.split())
    return rep


def _json(p: Path):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def run(*, head: str, export: Path, harness: Path, out: Path, classes, ephe: Path, l1_export: Path, docker: Docker | None = None, image_digest: str | None = None,
        budget_s: int | None = None, build_timeout_s: int = 590, slice_timeout_s: int = 590, keep_image: bool = False, extra_env: dict | None = None) -> dict:
    """Image -> PG -> probe + slice -> (teardown).  Writes <out>/amd64_run.json after every stage and returns it.  Exit protocol: `status` is `complete`, `resume` (the same command resumes;
    the PG container and network are KEPT for it) or `failed`.  Everything is torn down on complete/failed."""
    if not re.fullmatch(r"[0-9a-f]{40}", head or ""):
        raise Amd64Refused("the amd64 slice is bound to a TR head: a 40-hex commit is required")
    classes = check_classes(classes)
    docker = docker or Docker()
    out.mkdir(parents=True, exist_ok=True)
    rec_path = out / "amd64_run.json"
    rec = _json(rec_path) or {"schema": SCHEMA, "run_id": secrets.token_hex(4), "nonce": secrets.token_hex(8), "head": head, "classes": classes, "stages": {}}
    if rec["head"] != head:
        raise Amd64Refused("the out directory belongs to another head: one amd64 slice per head (SR-AMD64-PER-HEAD)")
    rid, nonce = rec["run_id"], rec["nonce"]
    net, pg, sl = f"ky-amd64-{rid}", f"ky-amd64-{rid}-pg", f"ky-amd64-{rid}-slice"
    rec.update({"names": {"network": net, "pg": pg, "slice": sl}, "ephemeral": True})

    def save(status: str | None = None):
        if status:
            rec["status"] = status
        rec_path.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")

    def stage(name, **kv):
        rec["stages"][name] = {**rec["stages"].get(name, {}), **kv}
        save()

    try:
        info = json.loads(docker("info", "--format", "{{json .}}", timeout=60).stdout)
        rec["engine"] = {k: info.get(k) for k in ("Architecture", "OperatingSystem", "ServerVersion", "KernelVersion", "NCPU", "MemTotal")}
        # ── image: by digest if given (never silently built instead), else built from the head's Dockerfile ──
        if image_digest:
            if not SHA256.fullmatch(image_digest) or docker("image", "inspect", image_digest, check=False).returncode != 0:
                raise Amd64Refused(f"the image {image_digest} is not present locally: it is used by digest or not at all (no silent rebuild)")
            tag, rec["image"] = image_digest, {"digest": image_digest, "digest_kind": "given", "built": False}
        else:
            tag = f"ky-amd64-pipeline:{head[:12]}"
            if rec["stages"].get("build", {}).get("status") != "done":
                df = (export / DOCKERFILE_REL).read_text()
                pinned = {f: sha_bytes((ephe / f).read_bytes()) for f in EPHE_FILES}
                ctx_info = assemble_context(derive_dockerfile(df, pinned), export, ephe, out.parent / f"{out.name}.ctx")
                stage("build", status="running", dockerfile_source_sha256=sha_bytes(df.encode()), **ctx_info)
                t0 = time.monotonic()
                try:
                    docker(*build_argv(tag, out.parent / f"{out.name}.ctx"), timeout=build_timeout_s)
                except subprocess.TimeoutExpired:
                    stage("build", status="timeout", wall_s=round(time.monotonic() - t0, 1))
                    save("resume")
                    return rec
                stage("build", status="done", wall_s=round(time.monotonic() - t0, 1), wall_note="this invocation only; layers of an earlier invocation are cached")
            iid = docker("image", "inspect", "--format", "{{.Id}}|{{.Architecture}}|{{.Os}}", tag).stdout.strip().split("|")
            if iid[1:] != ["amd64", "linux"]:
                raise Amd64Refused(f"the built image is {iid[2:]}/{iid[1:2]}, not linux/amd64")
            rec["image"] = {"digest": iid[0], "digest_kind": "local_image_id (a locally built image has no registry digest)", "built": True, "tag": tag}
        # ── PG 15 locale C sibling on an internal network ──
        if docker("inspect", "-f", "{{.State.Running}}", pg, check=False).stdout.strip() != "true":
            docker("image", "inspect", PG_IMAGE, check=False).returncode == 0 or docker("pull", PG_IMAGE, timeout=300)
            teardown(docker, rid)
            docker(*network_argv(net, rid))
            docker(*pg_argv(pg, net, rid))
        ver = ""
        for _ in range(90):
            r = docker("exec", pg, "psql", "-h", "127.0.0.1", "-p", str(PG_PORT), "-U", "postgres", "-tAc",
                       "select current_setting('server_version')||'|'||current_setting('lc_collate')||'|'||current_setting('lc_ctype')||'|'||current_setting('server_encoding')", check=False)
            if r.returncode == 0 and r.stdout.strip():
                ver = r.stdout.strip()
                break
            time.sleep(1)
        v = ver.split("|")
        if not ver or not v[0].startswith("15.") or v[1:3] != ["C", "C"]:
            raise Amd64Refused(f"the sibling PG is not PG 15 with locale C: {ver!r}")
        pgimg = docker("image", "inspect", "--format", "{{.Id}}|{{index .RepoDigests 0}}|{{.Architecture}}", PG_IMAGE).stdout.strip().split("|")
        rec["pg"] = {"server_version": v[0], "lc_collate": v[1], "lc_ctype": v[2], "encoding": v[3], "image": PG_IMAGE, "image_id": pgimg[0], "repo_digest": pgimg[1],
                     "image_arch": pgimg[2], "network": "internal (no external route)", "port": PG_PORT, "published_ports": "none"}
        save()
        # ── the slice, in the container ──
        probe_path = out / "runtime_probe.json"
        probe_path.unlink(missing_ok=True) if rec["stages"].get("slice", {}).get("status") != "resume" else None
        argv = slice_argv(name=sl, pg=pg, run_id=rid, image=tag, harness=harness, code=export, out=out, ephe=ephe, l1_export=l1_export, head=head, classes=classes, nonce=nonce,
                          budget_s=budget_s, extra_env={"TRIAL_IMAGE_DIGEST": rec["image"]["digest"], **(extra_env or {})})
        docker("rm", "-f", sl, check=False)
        t0 = time.monotonic()
        prev_total = rec["stages"].get("slice", {}).get("wall_total_s", 0.0)
        stage("slice", status="running")
        try:
            r = docker(*argv, timeout=slice_timeout_s, check=False)
        except subprocess.TimeoutExpired:
            docker("rm", "-f", sl, check=False)
            stage("slice", status="resume", exit="timeout", wall_s=round(time.monotonic() - t0, 1), wall_total_s=round(prev_total + time.monotonic() - t0, 1))
            save("resume")
            return rec
        wall = round(time.monotonic() - t0, 1)
        (out / "slice_container.log").write_text((r.stdout or "")[-20000:] + "\n--stderr--\n" + (r.stderr or "")[-20000:])
        done = r.returncode == 0
        stage("slice", status="resume" if r.returncode == EX_RESUME else "done" if done else "failed", exit=r.returncode, wall_s=wall, wall_total_s=round(prev_total + wall, 1),
              wall_use="recorded for sizing only (wall_total_s = all invocations of this out dir); never used for G-5 (SR-G5-LOAD)")
        probe = _json(probe_path)
        cpu = (probe or {}).get("cpu")
        rec["emulation"] = detect_emulation(info, cpu)
        if r.returncode == EX_RESUME:
            save("resume")
            return rec
        save("complete" if done else "failed")
        return rec
    except BaseException:
        rec["status"] = "failed"
        save()
        raise
    finally:
        if rec.get("status") != "resume":
            rec["teardown"] = teardown(docker, rid)
            if not keep_image and rec.get("image", {}).get("built"):
                rec["teardown"]["image_removed"] = docker("rmi", rec["image"]["tag"], check=False).returncode == 0
            save()
