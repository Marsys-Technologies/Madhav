"""A10.1 trial-evaluator helpers (task T1B): the digests record, the natural-key noninterference snapshot, the per-stage effective-wall clock, the TRIAL_READY/1 and
EQUIVALENCE_RECORD/1 stages, the DIAGNOSTIC label, and the amd64 readiness record.  Job-local; not repository code.

Everything here is DATABASE-FREE except `capture_noninterference` (it only runs the SQL it is given on a connection it is handed) and `LockProbe`.  The two merged
repository tools are CALLED as programs (`platform/scripts/governance/trial_ready.py`, `00_ARCHITECTURE/briefs/kalayantra/fleet/equivalence_record.py`), never
re-implemented: a stage whose tool, repo or input is absent records `NOT_RUN` with the reason — null, never green (§N.7.6).  Output is counts, ids, digests, seconds."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Iterable

import gates

sys.dont_write_bytecode = True

TRIAL_READY_REL = "platform/scripts/governance/trial_ready.py"
EQ_RECORD_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/equivalence_record.py"
PINNED_SCHEMA = "ky.eq_pinned_inputs/1"
SNAPSHOT_SCHEMA = "ky.noninterference_snapshot/1"
DIGESTS_SCHEMA = "ky.trial_digests/1"
READINESS_SCHEMA = "ky.amd64_slice_readiness/1"
#: the manifest-vector keys that are CONFIG (how the build is asked for), as distinct from the trial's own scope keys (test_slice, scored_classes, horizon_basis, stored_scope)
CONFIG_VECTOR_KEYS = ("result_policy", "in_build_verify", "qualification_table", "near_miss_layer_version")


def sha(obj: Any) -> str:
    return gates.sha256_of(obj)


def sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ── the digests record (PLAN v2 G-8) ────────────────────────────────────────────────────────────────────────────

def ephemeris_identity(eph) -> dict | None:
    """What identifies the ephemeris for G-8: the pinned corpus FILES (name → sha256) and the swisseph library VERSION.  The platform and the library binary's hash
    differ between an arm64 trial and an amd64 dispatch by construction, so they are provenance (`digests_record.provenance`), never part of the equality digest (N2).
    None when the stored vector lacks either (an absent identity reads NOT_EVALUATED in G-8, never equal)."""
    if not isinstance(eph, dict) or not isinstance(eph.get("files"), dict) or not eph["files"] or not eph.get("swe_version"):
        return None
    return {"swe_version": eph["swe_version"], "files": dict(eph["files"])}


def digests_record(vector: dict | None) -> dict | None:
    """The trial's registry / L0 / ephemeris / convention / orb-policy / rulings / config digests, read from the generation's STORED manifest vector
    (`ka_gochara_input_vector/3`).  None when the vector is unreadable — an absent record reads NOT_EVALUATED in G-8, never equal."""
    if not isinstance(vector, dict):
        return None
    need = ("registry", "l0", "ephemeris", "sky_convention", "node", "orb_policy", "rulings_digest")
    if any(k not in vector for k in need):
        return None
    eph = ephemeris_identity(vector["ephemeris"])
    if eph is None:
        return None
    comps = {"registry": vector["registry"], "l0": vector["l0"], "ephemeris": eph,
             "convention": {"sky_convention": vector["sky_convention"], "node": vector["node"]}, "orb_policy": vector["orb_policy"], "rulings": vector["rulings_digest"],
             "config": {k: vector.get(k, "absent") for k in CONFIG_VECTOR_KEYS}}
    raw = vector["ephemeris"]
    return {"schema": DIGESTS_SCHEMA, "components": {name: {"sha256": sha(v)} for name, v in comps.items()}, "vector_sha256": sha(vector),
            # PROVENANCE only: where this trial ran.  Never compared (g8_digest_checks reads `components`), never inside a component digest.
            "provenance": {"ephemeris": {k: raw.get(k) for k in ("platform", "library_sha256", "probe_digest")}},
            "note": "sha256 over the canonical JSON of each stored-vector component; trial-scope keys (test_slice, scored_classes, horizon_basis, stored_scope) are not config; "
                    "the ephemeris component is the pinned FILES + the swisseph library VERSION (platform / library binary hash are provenance, not equality); "
                    "vector_sha256 covers the whole stored vector INCLUDING the platform and is informational only"}


def geometry_config(vector: dict | None, horizon: dict | None, classes: Iterable[str]) -> str | None:
    """What the natural keys depend on: the sky convention and node model, the ephemeris corpus, the ADMISSION orb (it fixes the supports), the horizon and the
    class list.  None when any is unknown (the comparison then reads NOT_EVALUATED)."""
    if not isinstance(vector, dict) or not isinstance(horizon, dict):
        return None
    try:
        eph = vector["ephemeris"]
        return sha({"sky_convention": vector["sky_convention"], "node": vector["node"], "ephemeris": {k: eph[k] for k in ("backend", "swe_version", "files")},
                    "admission_orb": vector["orb_policy"]["admission_digest"], "horizon": [horizon.get("start"), horizon.get("end")], "classes": sorted(classes)})
    except (KeyError, TypeError):
        return None


# ── the natural-key noninterference snapshot (GPT N3) ───────────────────────────────────────────────────────────

_TS = "to_char({c} AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US')"
_REC_KEY = ("r.event_class, r.affected_person, r.frame_kind, r.frame_arg, r.agent, r.relation, r.object_id::text, r.object_role, r.contact_id::text, r.path_id,"
            " r.source_text")
_WIN_KEY = "w.event_class, w.path_id, " + _TS.format(c="lower(w.interval)") + ", " + _TS.format(c="upper(w.interval)")
#: each query returns (group = 'class|path', rule_version, key text).  Keys are the STORED natural-key columns minus chart_id/generation (MEASURING_BUILD_CONTRACT
#: MB-3.2); the RULE VERSION is not in a key (it is the one identity a declared change may move) and is reported per path beside them.
SNAPSHOT_SQL = {
    "windows": f"SELECT w.event_class || '|' || w.path_id, w.rule_version, jsonb_build_array({_WIN_KEY})::text FROM public.ka_gochara_eval_window w"
               " WHERE w.chart_id = %s AND w.generation = %s AND w.event_class = ANY(%s)",
    "supports": f"SELECT r.event_class || '|' || r.path_id, r.rule_version, jsonb_build_array({_REC_KEY}, r.admission_state, r.operator_role,"
                " r.temporal_support_intervals::text)::text FROM public.ka_gochara_relationship_record r"
                " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = ANY(%s)",
    "membership": f"SELECT w.event_class || '|' || w.path_id, w.rule_version, jsonb_build_array(jsonb_build_array({_WIN_KEY}), jsonb_build_array({_REC_KEY}))::text"
                  " FROM public.ka_gochara_eval_window_record m"
                  " JOIN public.ka_gochara_eval_window w ON w.window_id = m.window_id AND w.chart_id = m.chart_id AND w.generation = m.generation"
                  " JOIN public.ka_gochara_relationship_record r ON r.record_id = m.record_id AND r.chart_id = m.chart_id AND r.generation = m.generation"
                  " WHERE m.chart_id = %s AND m.generation = %s AND m.event_class = ANY(%s)",
}
CONTACTS_SQL = ("SELECT 'contacts|-', '-', jsonb_build_array(c.contact_id::text, " + _TS.format(c="c.t_in") + ", " + _TS.format(c="c.t_out") + ", " + _TS.format(c="c.t_exact")
                + ", c.delta_lambda::text)::text FROM public.ka_gochara_contact c WHERE c.chart_id = %s AND c.generation = %s")


def snapshot_from_rows(rows: dict, geometry: str | None) -> dict:
    """rows = {kind: iterable of (group, rule_version, key_text)} → the snapshot.  Keys are SORTED here (never trusting the database's order); a group digest is the
    sha256 of its sorted key lines, the kind digest the sha256 over the sorted (group, digest, count) triples."""
    kinds, versions = {}, {}
    for kind in gates.NONINTERFERENCE_KINDS:
        groups: dict = {}
        for group, rv, key in rows.get(kind) or ():
            groups.setdefault(group, []).append(key)
            if kind == "windows" and rv is not None:
                versions.setdefault(group.split("|", 1)[1], set()).add(rv)
        out = {g: {"count": len(ks), "sha256": hashlib.sha256(("\n".join(sorted(ks)) + "\n").encode("utf-8")).hexdigest()} for g, ks in sorted(groups.items())}
        kinds[kind] = {"count": sum(v["count"] for v in out.values()), "sha256": sha([[g, v["sha256"], v["count"]] for g, v in out.items()]), "groups": out}
    return {"schema": SNAPSHOT_SCHEMA, "geometry_config": geometry, "kinds": kinds, "rule_versions": {p: sorted(v) for p, v in sorted(versions.items())},
            "note": "sorted natural keys per class|path; window rule_version is not part of a key"}


def capture_noninterference(conn, chart: str, generation: str, classes: list, geometry: str | None) -> dict:
    """Read the four natural-key sets from the trial database (session time zone pinned to UTC so range text is stable)."""
    conn.execute("SET TIME ZONE 'UTC'")
    args = (chart, generation, classes)
    rows = {kind: conn.execute(sql, args).fetchall() for kind, sql in SNAPSHOT_SQL.items()}
    rows["contacts"] = conn.execute(CONTACTS_SQL, (chart, generation)).fetchall()
    return snapshot_from_rows(rows, geometry)


# ── the effective-wall clock (T17): per stage, compute and lock wait SEPARATELY ───────────────────────────────

class StageClock:
    """Accumulates, per named stage, `wall_s`, `lock_wait_s` (the time at least one database session of the trial was waiting on a lock, sampled every
    `interval_s`) and `compute_s = wall_s − lock_wait_s`.  `probe()` returns True/False for 'someone is waiting on a lock now', or None when it cannot be asked —
    a stage with an unanswerable probe has `lock_wait_s = None` (unknown, never zero).

    HARNESS-3.2 (D-10): each stage also records `max_load_per_core`, the highest 1-minute load average per core sampled during the stage (at its start, at every probe tick and at
    its end) — the validity detector of G-5: a runtime measured on a machine that was busier than the profile's bound is not a measurement of the build.  No answered sample = null."""

    def __init__(self, probe: Callable[[], bool | None], interval_s: float = 0.25, load_probe: Callable[[], float | None] | None = None):
        self.probe, self.interval_s = probe, interval_s
        self.load_probe = load_probe if load_probe is not None else load_per_core
        self.stages: dict = {}

    def add(self, stage: str, wall_s: float, waiting_samples: int, samples: int, unanswered: int = 0, max_load: float | None = None, load_samples: int = 0) -> None:
        s = self.stages.setdefault(stage, {"wall_s": 0.0, "lock_wait_s": 0.0, "samples": 0, "waiting_samples": 0, "unanswered_samples": 0,
                                           "max_load_per_core": None, "load_samples": 0})
        s["wall_s"] += wall_s
        s["samples"] += samples
        s["waiting_samples"] += waiting_samples
        s["unanswered_samples"] += unanswered
        s["lock_wait_s"] += min(wall_s, waiting_samples * self.interval_s)
        s["load_samples"] += load_samples
        if max_load is not None:
            s["max_load_per_core"] = max_load if s["max_load_per_core"] is None else max(s["max_load_per_core"], max_load)

    @contextlib.contextmanager
    def measure(self, stage: str | Callable[[], str]):
        """Time a block.  `stage` may be a callable resolved AFTER the block (the build learns a step's kind only when the call returns)."""
        stop, tally = threading.Event(), {"samples": 0, "waiting": 0, "unanswered": 0, "load_max": None, "load_n": 0}

        def sample_load():
            ld = self.load_probe()
            if ld is not None:
                tally["load_n"] += 1
                tally["load_max"] = ld if tally["load_max"] is None else max(tally["load_max"], ld)

        def loop():
            while not stop.wait(self.interval_s):
                sample_load()
                v = self.probe()
                tally["samples"] += 1
                if v is None:
                    tally["unanswered"] += 1
                elif v:
                    tally["waiting"] += 1
        t = threading.Thread(target=loop, daemon=True)
        t0 = time.time()
        sample_load()
        t.start()
        try:
            yield
        finally:
            stop.set()
            t.join(timeout=5)
            sample_load()
            self.add(stage() if callable(stage) else stage, time.time() - t0, tally["waiting"], tally["samples"], tally["unanswered"], tally["load_max"], tally["load_n"])

    def close(self) -> None:
        """Release the probe's admin connection (N4); a probe without one is left alone."""
        closer = getattr(self.probe, "close", None)
        if callable(closer):
            closer()

    def record(self) -> dict:
        stages = {}
        for name, s in sorted(self.stages.items()):
            unknown = s["unanswered_samples"] > 0       # ANY sample the probe could not answer: those intervals might have been waiting, so the stage's lock wait is unknown (N3)
            lock = None if unknown else round(s["lock_wait_s"], 3)
            wall = round(s["wall_s"], 3)
            stages[name] = {"wall_s": wall, "lock_wait_s": lock, "compute_s": None if lock is None else round(wall - lock, 3), "samples": s["samples"],
                            "waiting_samples": s["waiting_samples"], "unanswered_samples": s["unanswered_samples"],
                            # what WAS observed, reported beside the unknown: a lower bound (answered waiting samples only)
                            "lock_wait_observed_s": round(s["lock_wait_s"], 3),
                            # HARNESS-3.2 (D-10): the busiest the machine was during the stage, per core (null = no answered sample)
                            "max_load_per_core": None if s["max_load_per_core"] is None else round(s["max_load_per_core"], 3), "load_samples": s["load_samples"]}
        return {"schema": "ky.effective_wall/1", "method": "pg_stat_activity wait_event_type = 'Lock' on the trial database, sampled",
                "load_method": "os.getloadavg()[0] / os.cpu_count(), sampled at stage start, every interval and stage end (the kernel's 1-minute average: a stage shorter than a minute "
                               "also reads the minute before it)", "cpu_count": os.cpu_count(),
                "interval_s": self.interval_s, "stages": stages,
                "note": "lock_wait_s is a SAMPLED lower-resolution estimate (± one interval); wall = compute + lock wait by construction; a stage with ANY unanswered probe sample is null "
                        "(unknown, never zero) and reports what was observed in lock_wait_observed_s / unanswered_samples"}

    def load(self, rec: dict | None) -> None:
        """Resume: restore the accumulators from a previously saved `record()` (resumable runs keep one clock)."""
        for name, s in ((rec or {}).get("stages") or {}).items():
            load = {"max_load_per_core": s.get("max_load_per_core"), "load_samples": s.get("load_samples") or 0}
            if s.get("lock_wait_s") is None:                                   # it was unknown, it stays unknown
                n = max(s.get("samples") or 0, 1)
                self.stages[name] = {"wall_s": s["wall_s"], "lock_wait_s": s.get("lock_wait_observed_s") or 0.0, "samples": n, "waiting_samples": s.get("waiting_samples") or 0,
                                     "unanswered_samples": max(s.get("unanswered_samples") or 0, 1), **load}
            else:
                self.stages[name] = {"wall_s": s["wall_s"], "lock_wait_s": s["lock_wait_s"], "samples": s["samples"], "waiting_samples": s["waiting_samples"],
                                     "unanswered_samples": s["unanswered_samples"], **load}


def load_per_core() -> float | None:
    """The kernel's 1-minute load average divided by the core count; None when the platform cannot answer (an unanswerable sample is unknown, never zero)."""
    try:
        return os.getloadavg()[0] / max(os.cpu_count() or 1, 1)
    except (OSError, AttributeError):
        return None


def lock_probe(admin_dsn: str, database: str) -> Callable[[], bool | None]:
    """A probe over a SEPARATE admin connection: is any other session of `database` waiting on a lock right now?  None when the admin connection fails."""
    holder: dict = {}

    def probe():
        try:
            import psycopg
            if "conn" not in holder:
                holder["conn"] = psycopg.connect(admin_dsn, autocommit=True, connect_timeout=3)
            row = holder["conn"].execute("SELECT count(*) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid() AND wait_event_type = 'Lock'",
                                         (database,)).fetchone()
            return bool(row[0])
        except Exception:                                                        # noqa: BLE001 — an unanswerable probe is unknown, not zero
            _close_quietly(holder.pop("conn", None))
            return None

    def close():
        _close_quietly(holder.pop("conn", None))
    probe.close = close          # type: ignore[attr-defined]
    return probe


def _close_quietly(conn) -> None:
    try:
        if conn is not None:
            conn.close()
    except Exception:                                                            # noqa: BLE001 — closing a dead connection must not mask the run
        pass


# ── the DIAGNOSTIC label (A10.1 §2.1) ───────────────────────────────────────────────────────────────────────────

def qualification_block(report: dict, image: str | None = None) -> dict:
    """Every run before TRIAL_READY/1 reads true writes {qualifying: false, label: DIAGNOSTIC, head, image, scope, status}; the TR report refuses to cite it."""
    g0 = gates.g0_trial_ready(report)
    qualifying = g0["status"] == gates.PASS
    build = report.get("build") or {}
    return {"qualifying": qualifying, "label": "QUALIFYING_CANDIDATE" if qualifying else "DIAGNOSTIC", "head": _head(report), "image": image,
            "scope": {"classes": len(_get_classes(report)), "policy": (report.get("config") or {}).get("requested_result_policy"), "horizon": report.get("horizon")},
            "status": "BUILD_DEFECTS" if (build.get("defects") or build.get("aborted")) else "BUILD_COMPLETE",
            "g0": g0["status"],
            "rule": "a rolling result is discarded on the next integration advance and is not evidence for G-1..G-8 nor for the amd64 run (A10.1 N3, SR-AMD64-PER-HEAD)"}


def _head(report: dict) -> str | None:
    return (report.get("code") or {}).get("head")


def _get_classes(report: dict) -> list:
    return (report.get("config") or {}).get("classes") or []


# ── TRIAL_READY/1 (the merged evaluator, called as a program) ───────────────────────────────────────────────────

def run_trial_ready(repo: Path | None, head: str | None, out_json: Path, *, python: str = sys.executable, tool: Path | None = None, timeout_s: int = 3600) -> dict:
    """Run `trial_ready.py --repo <work tree at head> --ref <head>` and return its JSON (the whole document: predicate, head_sha, evaluated_at, checks, ready).
    A run that cannot start (no repo, no tool, no head) returns a document with `ready: false`, no checks and a `not_run_reason` — never a pass."""
    def not_run(why: str) -> dict:
        return {"predicate": gates.TRIAL_READY_PREDICATE, "head_sha": head, "evaluated_at": None, "checks": [], "ready": False, "not_run_reason": why}
    if repo is None or not head:
        return not_run("no --trial-ready-repo (a clean work tree at the head) or no head to evaluate")
    tool = tool or (Path(repo) / TRIAL_READY_REL)
    if not Path(tool).is_file():
        return not_run(f"the evaluator is not in the repo: {tool}")
    out_json = Path(out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    cmd = [python, "-I", str(tool), "--repo", str(repo), "--ref", head, "--out", str(out_json), "--workdir", str(out_json.with_suffix(".work")), "--python", python]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
    except (OSError, subprocess.SubprocessError) as exc:
        return not_run(f"trial_ready.py could not run: {type(exc).__name__}")
    if r.returncode == 2 or not out_json.is_file():
        return not_run(f"trial_ready.py refused (exit {r.returncode}): {(r.stderr or r.stdout).strip()[:200]}")
    try:
        doc = json.loads(out_json.read_text(encoding="utf-8"))
    except ValueError:
        return not_run("trial_ready.json is not readable")
    doc["evaluator_exit"] = r.returncode
    doc["evaluator_sha256"] = sha_file(Path(tool))
    return doc


# ── EQUIVALENCE_RECORD/1 emission (the merged tool, called as a program) ────────────────────────────────────────

def runtime_identity() -> dict:
    machine = {"x86_64": "amd64", "AMD64": "amd64", "aarch64": "arm64"}.get(platform.machine(), platform.machine())
    return {"arch": f"{sys.platform}/{machine}", "python": platform.python_version()}


def pinned_inputs(vector: dict, *, trial_horizon: Any, provenance: dict, extra: dict | None = None) -> dict:
    """The `ky.eq_pinned_inputs/1` document the harness can honestly write: the stored vector, the trial's own horizon, the runtime it ran on (a ROLLING
    DIAGNOSTIC unless `extra` says otherwise) and provenance.  Everything the repository and the trial cannot say (rules.selection, E3a rows, the century config, the
    dependency-lock digest) comes ONLY from `extra` — absent, the tool writes the record INCOMPLETE with those categories null (B.10, N.7.6)."""
    doc = {"schema": PINNED_SCHEMA, "input_vector": vector, "trial_scope": {"horizon": trial_horizon},
           "runtime": {"kind": "rolling_diagnostic", **runtime_identity()}, "provenance": dict(provenance)}
    for k, v in (extra or {}).items():
        if k in ("schema", "input_vector"):
            continue
        doc[k] = {**doc.get(k, {}), **v} if isinstance(v, dict) and isinstance(doc.get(k), dict) else v
    return doc


def emit_equivalence_record(repo: Path | None, head: str | None, pinned: dict | None, out_dir: Path, *, python: str = sys.executable, tool: Path | None = None,
                            timeout_s: int = 600) -> dict:
    """Call `equivalence_record.py record` for the trial head.  Returns a summary: status COMPLETE (exit 0) / INCOMPLETE (exit 2: written, a category null) /
    REFUSED (exit 1: nothing written) / NOT_RUN (no repo, tool, head or pinned inputs), the record digest and the unreadable reasons."""
    def not_run(why: str) -> dict:
        return {"status": "NOT_RUN", "reason": why, "head": head}
    if repo is None or not head:
        return not_run("no --eq-repo (a git repository containing the head) or no head")
    if pinned is None:
        return not_run("no manifest vector was readable: the pinned inputs cannot be written")
    tool = tool or (Path(repo) / EQ_RECORD_REL)
    if not Path(tool).is_file():
        return not_run(f"the equivalence_record tool is not in the repo: {tool}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pin_path, rec_path = out_dir / "eq_pinned_inputs.json", out_dir / "equivalence_record.json"
    pin_path.write_text(json.dumps(pinned, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    cmd = [python, "-I", str(tool), "record", "--repo", str(repo), "--commit", head, "--pinned-inputs", str(pin_path), "--out", str(rec_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
    except (OSError, subprocess.SubprocessError) as exc:
        return not_run(f"equivalence_record.py could not run: {type(exc).__name__}")
    out = {"head": head, "exit": r.returncode, "tool_sha256": sha_file(Path(tool)), "pinned_inputs_sha256": sha_file(pin_path),
           "projection": "trial (rolling_diagnostic runtime unless the pinned inputs say qualifying_run)"}
    if r.returncode == 1 or not rec_path.is_file():
        return {**out, "status": "REFUSED", "reason": (r.stderr or r.stdout).strip()[:300]}
    try:
        summary = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        summary = {}
    return {**out, "status": "COMPLETE" if r.returncode == 0 else "INCOMPLETE", "complete": summary.get("complete"), "record_digest": summary.get("record_digest"),
            "unreadable": summary.get("unreadable"), "record_file": str(rec_path), "record_file_sha256": sha_file(rec_path)}


# ── amd64 readiness (T24 prep; SR-AMD64-PER-HEAD: ONE amd64 slice per TR head) — NOT RUN ────────────────────────────

FOUR_CLASS_SLICE = ("bereavement", "chronic_onset", "illness_acute", "major_loss")


def amd64_readiness(head: str | None, image_digest: str | None, *, checkout_in_image: str = "/work/code", harness_in_image: str = "/work/harness",
                    out_in_image: str = "/work/out/amd64_slice", baseline: str = "baseline_12.json", profile: str = "gate_profile.plan_defaults.json") -> dict:
    """The command and inputs for the one linux/amd64 slice of a TR head.  NOT RUN here.  `ready` is true only when every required input is present: a missing image
    digest or head means the slice cannot start (the T24 detector)."""
    import re
    inputs = {
        "head": {"value": head, "present": bool(head and re.fullmatch(r"[0-9a-f]{40}", head)), "what": "the TR head (40 hex) the slice is bound to; once per head"},
        "image_digest": {"value": image_digest, "present": bool(image_digest and re.fullmatch(r"sha256:[0-9a-f]{64}", image_digest)),
                         "what": "the immutable linux/amd64 image digest (sha256:...) holding the python sidecar, the pinned ephemeris corpus and the lock-pinned dependencies"},
        "slice_classes": {"value": list(FOUR_CLASS_SLICE), "present": True, "what": "the 4 ruled classes (mine N-4: one amd64 run of the 4-class slice)"},
    }
    env = {"TRIAL_CODE_HEAD": head or "<40-hex head>", "TRIAL_CLASSES": ",".join(FOUR_CLASS_SLICE), "TRIAL_LABEL": "amd64_slice", "TRIAL_VERIFY": "1",
           "TRIAL_BASELINE": f"{harness_in_image}/{baseline}", "TRIAL_PROFILE": f"{harness_in_image}/{profile}"}
    in_image = [f"{k}={v}" for k, v in sorted(env.items())] + ["bash", f"{harness_in_image}/run_trial.sh", checkout_in_image, out_in_image]
    return {
        "schema": READINESS_SCHEMA, "rule": "SR-AMD64-PER-HEAD: once per TR head; arm64 runs are corroboration, never the qualifying E4", "not_run": True,
        "ready": all(v["present"] for v in inputs.values()), "inputs": inputs,
        "in_image_command": in_image,
        "example_runner": {"interpretation": "(I) INTERPRETATION: how the image is entered is the ops decision (T24 owner); a container runtime form is shown",
                           "argv": ["<container-runtime>", "run", "--rm", "--platform", "linux/amd64", "--network", "host", "-v", "<job dir>:/work", image_digest or "<image digest>",
                                    "env", *in_image]},
        "requirements": [
            "the process sees the lane cluster at 127.0.0.1:55433 (the harness's fixed ADMIN_DSN): host networking, or a cluster inside the image",
            "SE_EPHE_PATH points at the PINNED ephemeris corpus (never a stand-in, never a network fetch)",
            "the checkout in the image is the head's tree (`git archive` export: pass TRIAL_CODE_HEAD)",
            "afterwards, `trial_slice.py eq-record` with a pinned-inputs file whose runtime.kind = qualifying_run and arch = linux/amd64 turns this run into the E4 of the record"],
        "after": "the slice's trial_report.json (label amd64_slice) is the qualifying E4 evidence for this head only; any integration advance voids it",
    }
