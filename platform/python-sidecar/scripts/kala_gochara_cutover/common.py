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
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", ""}
PRODUCTION_PROXY_PORT = 5433  # Cloud SQL proxy convention (tests/ DATABASE_URL)


def tranche_for_step(step: int) -> int:
    return 1 if step <= 5 else 2


# ── DSN redaction (Pravāha A2.5 / ASTRA A2.5 review amendment 3) ─────────────
#
# Connection strings carry credentials; none may ever reach a log line or a
# failure diagnostic. Every chain script logs subprocess argv and error text
# ONLY through these helpers.

_DSN_PASSWORD_RE = re.compile(
    r"((?:postgresql|postgres)(?:\+[a-z0-9]+)?://[^:/@\s]+):[^@\s]+@",
    re.IGNORECASE)

REDACTED = "***REDACTED***"


def redact_text(text: str) -> str:
    """Redact the password component of any postgres connection URI appearing
    in arbitrary text (log lines, exception messages, diagnostics)."""
    return _DSN_PASSWORD_RE.sub(r"\1:" + REDACTED + "@", str(text))


def redact_argv(argv: list[str]) -> list[str]:
    """A copy of a command vector safe to log: the value of every --dsn (both
    '--dsn X' and '--dsn=X' forms) is replaced, and any residual URI password
    in the remaining tokens is scrubbed by redact_text."""
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
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--dsn", required=True,
                        help="explicit target connection string (no default)")
    parser.add_argument("--evidence", action="store_true",
                        help="append this run's outcome to evidence/step%02d_evidence.md" % step)
    return parser


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
