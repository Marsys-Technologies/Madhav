#!/usr/bin/env python3
"""Executor standards inherited by every executor (stdlib only). Import it or copy it BYTE-IDENTICALLY next to the executor.

(1) LAUNCH MARKER. run_gated.sh sets the environment variable GATE_V2_LAUNCH only after prerun_gate.py exited 0:
        GATE_V2_LAUNCH = v1.<gate_sha256>.<run_gated_sha256>.<epoch_seconds>.<nonce_hex32>.<check>
        check          = sha256("|".join(["GATE_V2_LAUNCH", "v1", gate_sha256, run_gated_sha256, epoch_seconds, nonce]))
    The executor calls require_gate_launch(...) first thing and REFUSES (SystemExit, exit 93) unless: the marker exists and
    parses; its check recomputes; its gate/launcher shas equal the sha256 of the LIVE prerun_gate.py / run_gated.sh next
    to this file (and equal the shas pinned in the executor's plan, when given); it is not from the future (> 120 s skew)
    and not older than 6 hours. This is a convention-grade guard against accidents in a single-operator setting (running
    the executor directly, running a stale or edited gate): it is NOT a security boundary (anyone who can run python can
    forge a marker). The gate and launcher shas are PART OF THE PLAN HASH: see bind_gate_into_plan_hash().

(2) OUTCOME FILE. In EVERY mode (dry_run, applied, failed) the executor writes <evidence_dir>/outcome.json (file 0600,
    dir 0700), also on failure, so a lost stdout never hides what happened:
        schema, status (dry_run|applied|failed), utc (ISO-8601 Z), executor_sha256, plan_hash, gate_sha256,
        run_gated_sha256, evidence_digest (hex or null), failed_checks (list of check names; empty unless failed)
    Use the outcome_guard() context manager: whatever happens inside (a refusal, an exception, a SystemExit, a return with
    no outcome declared) an outcome.json with status failed is written; success is declared with .dry_run() / .applied().

CLI (used by run_gated.sh):  executor_standards.py make-marker <prerun_gate.py> <run_gated.sh>   -> marker on stdout
                             executor_standards.py fingerprint [dir]                              -> sha256 JSON on stdout
"""
import hashlib
import json
import os
import re
import secrets
import sys
import tempfile
import time

MARKER_ENV = "GATE_V2_LAUNCH"
MARKER_VERSION = "v1"
MAX_AGE_S = 6 * 3600
MAX_FUTURE_SKEW_S = 120
EXIT_NO_LAUNCH = 93
OUTCOME_FILE = "outcome.json"
OUTCOME_SCHEMA = "executor_outcome_v1"
STATUSES = ("dry_run", "applied", "failed")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_CHECK_NAME = re.compile(r"[A-Za-z0-9_.:\-]{1,80}")
HERE = os.path.dirname(os.path.abspath(__file__))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(gate_dir=None):
    d = gate_dir or HERE
    return {"gate_sha256": sha256_file(os.path.join(d, "prerun_gate.py")),
            "run_gated_sha256": sha256_file(os.path.join(d, "run_gated.sh"))}


def bind_gate_into_plan_hash(plan_hash_hex, fp):
    """The gate and launcher shas are part of the plan hash: changing either gate file changes the plan the operator approved."""
    return hashlib.sha256("|".join([plan_hash_hex, fp["gate_sha256"], fp["run_gated_sha256"]]).encode()).hexdigest()


# ---------------------------------------------------------------- (1) launch marker
def _check(gate_sha, launcher_sha, epoch, nonce):
    return hashlib.sha256("|".join(["GATE_V2_LAUNCH", MARKER_VERSION, gate_sha, launcher_sha, str(epoch), nonce]).encode()).hexdigest()


def make_marker(gate_file, launcher_file, now=None, nonce=None):
    gate_sha, launcher_sha = sha256_file(gate_file), sha256_file(launcher_file)
    epoch = int(time.time() if now is None else now)
    nonce = nonce or secrets.token_hex(16)
    return ".".join([MARKER_VERSION, gate_sha, launcher_sha, str(epoch), nonce, _check(gate_sha, launcher_sha, epoch, nonce)])


def verify_marker(marker, gate_dir=None, expected_gate_sha=None, expected_launcher_sha=None, now=None, max_age_s=MAX_AGE_S):
    """Returns (ok, reason). reason is a short class, never the marker content."""
    if not marker:
        return False, "no_marker"
    parts = marker.split(".")
    if len(parts) != 6 or parts[0] != MARKER_VERSION:
        return False, "malformed_marker"
    _, gate_sha, launcher_sha, epoch_s, nonce, check = parts
    if not (_HEX64.fullmatch(gate_sha) and _HEX64.fullmatch(launcher_sha) and _HEX64.fullmatch(check)
            and epoch_s.isdigit() and re.fullmatch(r"[0-9a-f]{32}", nonce)):
        return False, "malformed_marker"
    if _check(gate_sha, launcher_sha, int(epoch_s), nonce) != check:
        return False, "marker_check_mismatch"
    try:
        live = fingerprint(gate_dir)
    except OSError:
        return False, "gate_files_unreadable"
    if gate_sha != live["gate_sha256"]:
        return False, "gate_sha_differs_from_live_gate_file"
    if launcher_sha != live["run_gated_sha256"]:
        return False, "launcher_sha_differs_from_live_run_gated"
    if expected_gate_sha is not None and expected_gate_sha != gate_sha:
        return False, "gate_sha_differs_from_plan"
    if expected_launcher_sha is not None and expected_launcher_sha != launcher_sha:
        return False, "launcher_sha_differs_from_plan"
    age = (time.time() if now is None else now) - int(epoch_s)
    if age < -MAX_FUTURE_SKEW_S:
        return False, "marker_from_the_future"
    if age > max_age_s:
        return False, "marker_stale"
    return True, "ok"


def require_gate_launch(environ=None, gate_dir=None, expected_gate_sha=None, expected_launcher_sha=None, now=None,
                        max_age_s=MAX_AGE_S):
    """Executors call this first. Refuses (SystemExit 93) unless launched by run_gated.sh. Returns the live fingerprint."""
    environ = os.environ if environ is None else environ
    ok, reason = verify_marker(environ.get(MARKER_ENV), gate_dir, expected_gate_sha, expected_launcher_sha, now, max_age_s)
    if not ok:
        sys.stderr.write("REFUSED: not launched by run_gated.sh after a passing GATE_V2 (%s). Start it as: run_gated.sh <executor> <args>\n"
                         % reason)
        raise SystemExit(EXIT_NO_LAUNCH)
    return fingerprint(gate_dir)


# ---------------------------------------------------------------- (2) outcome file
def _utc(now=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() if now is None else now))


def write_outcome(evidence_dir, status, executor_path, plan_hash, gate_fp, evidence_digest=None, failed_checks=(), now=None):
    """Atomically writes <evidence_dir>/outcome.json (0600; directory made/forced 0700). Returns the path."""
    if status not in STATUSES:
        raise ValueError("status must be one of %s" % (STATUSES,))
    checks = list(failed_checks)
    if not all(isinstance(c, str) and _CHECK_NAME.fullmatch(c) for c in checks):
        raise ValueError("failed_checks must be a list of short check names")
    if status == "failed" and not checks:
        raise ValueError("a failed outcome must name at least one failed check")
    if status != "failed" and checks:
        raise ValueError("only a failed outcome carries failed checks")
    if evidence_digest is not None and not _HEX64.fullmatch(evidence_digest):
        raise ValueError("evidence_digest must be 64 lowercase hex chars or None")
    os.makedirs(evidence_dir, mode=0o700, exist_ok=True)
    os.chmod(evidence_dir, 0o700)
    body = {"schema": OUTCOME_SCHEMA, "status": status, "utc": _utc(now), "executor_sha256": sha256_file(executor_path),
            "plan_hash": plan_hash, "gate_sha256": gate_fp["gate_sha256"], "run_gated_sha256": gate_fp["run_gated_sha256"],
            "evidence_digest": evidence_digest, "failed_checks": checks}
    path = os.path.join(evidence_dir, OUTCOME_FILE)
    fd, tmp = tempfile.mkstemp(prefix=".outcome.", dir=evidence_dir)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(body, indent=2, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


class outcome_guard:
    """with outcome_guard(evidence_dir, executor_path, plan_hash, gate_fp) as o: ... o.dry_run(digest) | o.applied(digest) | o.fail([names])"""

    def __init__(self, evidence_dir, executor_path, plan_hash, gate_fp, now=None):
        self.args = (evidence_dir, executor_path, plan_hash, gate_fp)
        self.now = now
        self.done = False
        self.path = None

    def _write(self, status, digest=None, checks=()):
        self.path = write_outcome(*self.args[:1], status, *self.args[1:], evidence_digest=digest, failed_checks=checks, now=self.now)
        self.done = True

    def dry_run(self, evidence_digest):
        self._write("dry_run", evidence_digest)

    def applied(self, evidence_digest):
        self._write("applied", evidence_digest)

    def fail(self, failed_checks, evidence_digest=None):
        self._write("failed", evidence_digest, list(failed_checks))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None and not self.done:
            name = "exit_%s" % (exc.code,) if isinstance(exc, SystemExit) else exc_type.__name__
            self._write("failed", None, [re.sub(r"[^A-Za-z0-9_.:\-]", "_", name)[:80] or "unknown"])
        elif not self.done:
            self._write("failed", None, ["no_outcome_recorded"])
        return False


def main(argv):
    if len(argv) == 4 and argv[1] == "make-marker":
        sys.stdout.write(make_marker(argv[2], argv[3]))
        return 0
    if len(argv) in (2, 3) and argv[1] == "fingerprint":
        sys.stdout.write(json.dumps(fingerprint(argv[2] if len(argv) == 3 else None), sort_keys=True) + "\n")
        return 0
    sys.stderr.write("usage: executor_standards.py make-marker <prerun_gate.py> <run_gated.sh> | fingerprint [dir]\n")
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv))
