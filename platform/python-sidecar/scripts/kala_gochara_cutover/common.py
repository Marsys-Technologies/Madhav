"""Shared plumbing for the kala_gochara WP10 cutover scripts (remainder brief §7.A).

Every step script in this directory:

  * takes the target database as an EXPLICIT `--dsn` argument (never a default
    pointing at a shared database);
  * REFUSES the production instance unless the matching authorization flag is
    set: steps 0-5 (tranche 1) require env `PRODUCTION_TRANCHE_1_AUTHORIZED=true`,
    steps 6-10 (tranche 2) require `PRODUCTION_TRANCHE_2_AUTHORIZED=true`.
    Both flags are `false` in GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md
    frontmatter at preparation time, so any production-pointed invocation
    exits 4 with a refusal line.

Production instance identification: production PostgreSQL is reached through
the Cloud SQL proxy on 127.0.0.1:5433 (the `DATABASE_URL` convention every
integration test in tests/ documents), or any non-loopback host. A DSN whose
port is 5433, or whose host is not a loopback address, is treated as the
production instance. The disposable rehearsal databases (55433/55434 on
loopback) never trip the guard.

`write_evidence(step, body)` appends a dated section to
`evidence/stepNN_evidence.md` next to this file; the evidence file is created
from `evidence/stepNN_evidence.template.md` on first use when the template
exists.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", ""}
PRODUCTION_PROXY_PORT = 5433  # Cloud SQL proxy convention (tests/ DATABASE_URL)


def tranche_for_step(step: int) -> int:
    return 1 if step <= 5 else 2


# ── DSN redaction (Pravāha A2.5 / ASTRA A2.5 review amendments 3 + r2-3) ─────
#
# Connection strings carry credentials; none may ever reach a log line or a
# failure diagnostic. Every chain script logs subprocess argv and error text
# ONLY through these helpers. Two layers, both always applied by redact_text:
#
#   1. PATTERN redaction — every credential-carrying form libpq accepts:
#        postgresql://user:PASS@host          (URI user-info)
#        postgresql://host/db?password=PASS   (URI query parameter)
#        host=h user=u password=PASS          (libpq keyword=value form,
#        password='PA SS' / password="PA SS"   quoted variants included)
#        PGPASSWORD=PASS                      (environment form)
#   2. LITERAL redaction — once a script has parsed its --dsn it registers the
#      credential value(s) it carries (register_dsn_secrets); every later
#      redact_text call also scrubs those literal strings wherever they occur
#      (a traceback repr, a child's stderr, an argparse message), so a form the
#      patterns do not anticipate still cannot leak the secret itself.

_DSN_URI_USERINFO_RE = re.compile(
    r"((?:postgresql|postgres)(?:\+[a-z0-9]+)?://[^:/@\s]+):[^@\s]+@",
    re.IGNORECASE)
_DSN_URI_QUERY_RE = re.compile(r"([?&]password=)[^&\s'\"]+", re.IGNORECASE)
_DSN_KEYWORD_QUOTED_RE = re.compile(
    r"(\bpassword\s*=\s*)(?:'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")",
    re.IGNORECASE)
_DSN_KEYWORD_BARE_RE = re.compile(r"(\bpassword\s*=\s*)[^\s'\"&]+",
                                  re.IGNORECASE)
_PGPASSWORD_RE = re.compile(r"(\bPGPASSWORD=)\S+")

REDACTED = "***REDACTED***"

_REGISTERED_SECRETS: list[str] = []


def dsn_secrets(dsn: str) -> list[str]:
    """The credential literal(s) a DSN carries, in any libpq form (URI
    user-info, URI ?password=, keyword password=..., quoted keyword). Empty
    when the DSN carries none. Percent-decoded values are included too, so a
    URI-encoded password is scrubbed whether it is later printed encoded or
    decoded."""
    if not dsn:
        return []
    found: list[str] = []
    text = str(dsn)
    if "://" in text:
        try:
            parsed = urlparse(text)
            if parsed.password:
                found.append(parsed.password)
                found.append(unquote(parsed.password))
            for value in parse_qs(parsed.query).get("password", []):
                found.append(value)
        except ValueError:
            pass
    for m in _DSN_KEYWORD_QUOTED_RE.finditer(text):
        quoted = m.group(0)[len(m.group(1)):]
        found.append(quoted[1:-1].replace("\\'", "'").replace('\\"', '"'))
    for m in _DSN_KEYWORD_BARE_RE.finditer(text):
        found.append(m.group(0)[len(m.group(1)):])
    # longest first so a secret that contains another is scrubbed whole
    return sorted({s for s in found if s}, key=len, reverse=True)


def register_dsn_secrets(dsn: str) -> int:
    """Register the credential literal(s) of `dsn` for literal redaction by
    every subsequent redact_text call in this process. Returns the number of
    secrets now registered. Idempotent."""
    for secret in dsn_secrets(dsn):
        if secret not in _REGISTERED_SECRETS:
            _REGISTERED_SECRETS.append(secret)
    _REGISTERED_SECRETS.sort(key=len, reverse=True)
    return len(_REGISTERED_SECRETS)


def clear_registered_secrets() -> None:
    """Test seam: forget registered secrets (never called by the scripts)."""
    _REGISTERED_SECRETS.clear()


def redact_text(text: str) -> str:
    """Redact every credential form in arbitrary text (log lines, exception
    messages, diagnostics, child output) — pattern layer, then the literal
    layer for any secret registered via register_dsn_secrets."""
    out = str(text)
    out = _DSN_URI_USERINFO_RE.sub(r"\1:" + REDACTED + "@", out)
    out = _DSN_URI_QUERY_RE.sub(r"\1" + REDACTED, out)
    out = _DSN_KEYWORD_QUOTED_RE.sub(r"\1'" + REDACTED + "'", out)
    out = _DSN_KEYWORD_BARE_RE.sub(r"\1" + REDACTED, out)
    out = _PGPASSWORD_RE.sub(r"\1" + REDACTED, out)
    for secret in _REGISTERED_SECRETS:
        if secret in out:
            out = out.replace(secret, REDACTED)
    return out


def redact_argv(argv: list[str]) -> list[str]:
    """A copy of a command vector safe to log: the value of every --dsn (both
    '--dsn X' and '--dsn=X' forms) is replaced, and any residual credential
    form in the remaining tokens is scrubbed by redact_text."""
    out: list[str] = []
    skip = False
    for i, token in enumerate(argv):
        if skip:
            skip = False
            continue
        if token == "--dsn" and i + 1 < len(argv):
            out.extend(["--dsn", REDACTED])
            skip = True
        elif token.startswith("--dsn="):
            out.append("--dsn=" + REDACTED)
        else:
            out.append(redact_text(token))
    return out


class RedactingArgumentParser(argparse.ArgumentParser):
    """argparse whose usage/validation errors and exit messages pass through
    redact_text, and whose parse_args registers the parsed --dsn's secrets
    for literal redaction before returning — an early validation failure
    ('invalid float value', 'unrecognized arguments: ...') can echo a
    neighbouring token, so it is redacted like every other diagnostic."""

    def parse_known_args(self, args=None, namespace=None):
        # Register the DSN literal BEFORE argparse can complain about a later
        # token (parse_known_args raises through error() on the first bad
        # argument; the --dsn value may already be in the message).
        raw = list(sys.argv[1:] if args is None else args)
        for i, token in enumerate(raw):
            if token == "--dsn" and i + 1 < len(raw):
                register_dsn_secrets(raw[i + 1])
            elif token.startswith("--dsn="):
                register_dsn_secrets(token[len("--dsn="):])
        ns, extras = super().parse_known_args(args, namespace)
        if getattr(ns, "dsn", None):
            register_dsn_secrets(ns.dsn)
        if getattr(ns, "memory_guard_bytes", None):
            # the guard applies at the earliest point every step script
            # shares: right after its arguments parse (disclosed on ns)
            ns.memory_guard = apply_memory_guard(ns.memory_guard_bytes)
        return ns, extras

    def error(self, message):  # noqa: D401 — argparse contract
        super().error(redact_text(message))

    def exit(self, status=0, message=None):
        super().exit(status, redact_text(message) if message else None)

    def print_usage(self, file=None):
        (file or sys.stderr).write(redact_text(self.format_usage()))


def run_main_guarded(main_fn, argv: list[str] | None = None) -> int:
    """Run a step script's main() as the process entry point with every
    failure path redacted (amendment r2-3) and the memory guard's failure
    made LOUD (amendment r2-1):

      * SystemExit propagates unchanged (the scripts' own exit codes);
      * MemoryError (the RLIMIT_AS guard applied by apply_memory_guard, or a
        genuine allocation failure) prints a MEMORY GUARD diagnostic and
        exits 3 — a process that cannot hold its working set must fail
        visibly here, never as an opaque container OOM-kill;
      * any other uncaught exception prints its traceback through
        redact_text and exits 1 (the interpreter's default exit for an
        uncaught exception, now with the credential scrubbed).
    """
    try:
        return main_fn(argv) if argv is not None else main_fn()
    except SystemExit:
        raise
    except MemoryError:
        print("MEMORY GUARD: the process exceeded its memory guard (RLIMIT_AS)"
              " or the allocator refused — aborting LOUDLY rather than "
              "letting the container be OOM-killed. Reduce the workload "
              "(per-body chunking) or raise --memory-guard-bytes if the "
              "container genuinely has headroom.", file=sys.stderr,
              flush=True)
        return 3
    except BaseException:  # noqa: BLE001 — the redacting last line of defence
        print(redact_text(traceback.format_exc()), file=sys.stderr, flush=True)
        return 1


# ── memory guard (ASTRA A2.5 round-2 amendment 1) ────────────────────────────
#
# The per-body enumeration is inherently input-sized (the ADK-0020 dedupe and
# the canonical sort need the whole body's payload — CENTURY_CLOUD_RUN_JOB_SPEC
# §2.2 sizes it at 2–4 GiB per body); the projection is bounded per overlap
# cluster, whose worst case (one class continuously in orb) is likewise
# input-sized. Where a bound cannot be proven, the process carries a HARD,
# MEASURED guard: RLIMIT_AS set below the container's 16 GiB so an overrun
# fails as a Python MemoryError (run_main_guarded → exit 3 with a diagnostic)
# instead of an opaque OOM-kill; the driver additionally measures each
# child's peak RSS (RUSAGE_CHILDREN) and refuses to continue past a step
# whose peak exceeded the guard.

DEFAULT_MEMORY_GUARD_BYTES = 14 * (1 << 30)  # 14 GiB, under the job's 16 GiB


def apply_memory_guard(limit_bytes: int | None) -> dict:
    """Best-effort RLIMIT_AS at `limit_bytes` (None/0 = no guard). Returns a
    disclosure dict {applied, limit_bytes, reason}; a platform that refuses
    the rlimit is reported honestly, never claimed guarded."""
    if not limit_bytes:
        return {"applied": False, "limit_bytes": None, "reason": "no guard requested"}
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        new_hard = hard if hard != resource.RLIM_INFINITY and hard < limit_bytes else limit_bytes
        resource.setrlimit(resource.RLIMIT_AS, (min(limit_bytes, new_hard), new_hard))
        return {"applied": True, "limit_bytes": int(limit_bytes), "reason": None}
    except (ImportError, ValueError, OSError) as exc:
        return {"applied": False, "limit_bytes": int(limit_bytes),
                "reason": f"RLIMIT_AS not applied on this platform: {exc}"}


def peak_rss_bytes(children: bool = False) -> int | None:
    """Peak resident set size (bytes) of this process, or of its terminated
    children (RUSAGE_CHILDREN — the max over them). ru_maxrss is KiB on Linux
    and bytes on macOS; normalized here. None when unavailable."""
    try:
        import resource
        who = resource.RUSAGE_CHILDREN if children else resource.RUSAGE_SELF
        raw = resource.getrusage(who).ru_maxrss
    except (ImportError, OSError, AttributeError):
        return None
    return int(raw) if sys.platform == "darwin" else int(raw) * 1024


def is_production_dsn(dsn: str) -> bool:
    parsed = urlparse(dsn)
    host = parsed.hostname or ""
    port = parsed.port
    if port == PRODUCTION_PROXY_PORT:
        return True
    return host not in LOOPBACK_HOSTS


def refuse_production(dsn: str, step: int) -> None:
    """Exit 4 with a refusal when the DSN names production and the matching
    tranche flag is not exactly 'true'."""
    if not is_production_dsn(dsn):
        return
    tranche = tranche_for_step(step)
    flag = f"PRODUCTION_TRANCHE_{tranche}_AUTHORIZED"
    if os.environ.get(flag) != "true":
        print(
            f"REFUSED: step {step} targets the production instance "
            f"(host={urlparse(dsn).hostname!r} port={urlparse(dsn).port!r}) "
            f"but {flag} is not 'true'. WP10 tranches run only under the "
            "brief's flags; see GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md §7.",
            file=sys.stderr,
        )
        sys.exit(4)


def step_parser(step: int, description: str) -> argparse.ArgumentParser:
    parser = RedactingArgumentParser(description=description)
    parser.add_argument("--dsn", required=True,
                        help="explicit target connection string (no default)")
    parser.add_argument("--evidence", action="store_true",
                        help="append this run's outcome to evidence/step%02d_evidence.md" % step)
    parser.add_argument("--memory-guard-bytes", type=int, default=None,
                        help="RLIMIT_AS guard for this process (0/absent = "
                             "none); the century driver forwards its guard so "
                             "an overrun fails LOUDLY (exit 3) below the "
                             "container limit instead of an OOM-kill")
    return parser


def file_stats(path) -> dict:
    """Streamed {lines, bytes, sha256} of one local file — the binding the
    enumeration receipt, the finalized input manifest, and the candidate
    build all compute the same way (one detector, three call sites)."""
    import hashlib
    hasher = hashlib.sha256()
    nbytes = 0
    lines = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            hasher.update(chunk)
            nbytes += len(chunk)
            lines += chunk.count(b"\n")
    return {"lines": lines, "bytes": nbytes,
            "sha256": "sha256:" + hasher.hexdigest()}


def write_evidence(step: int, outcome: str, details: str = "") -> Path:
    EVIDENCE_DIR.mkdir(exist_ok=True)
    path = EVIDENCE_DIR / f"step{step:02d}_evidence.md"
    template = EVIDENCE_DIR / f"step{step:02d}_evidence.template.md"
    if not path.exists() and template.exists():
        path.write_text(template.read_text())
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with path.open("a") as fh:
        fh.write(f"\n## {stamp} — {outcome}\n\n{details}\n")
    return path


def connect(dsn: str, step: int, autocommit: bool = True):
    """Refuse production, then connect. psycopg3, autocommit on by default."""
    refuse_production(dsn, step)
    import psycopg  # noqa: F401 -- deferred so --help works without the driver
    return psycopg.connect(dsn, autocommit=autocommit, connect_timeout=5)
