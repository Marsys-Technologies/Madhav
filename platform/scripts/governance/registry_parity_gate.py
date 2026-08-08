#!/usr/bin/env python3
"""registry_parity_gate.py — ADHIṢṬHĀNA Lane A6(i) permanent registry-parity guard.

MASTER_PLAN_v1_0.md §3 Lane A6: makes the identity-contract convergence Lanes
A1-A5 just did PERMANENT and self-enforcing, so future code can't silently
re-fragment it. Structured after `msr_referential_integrity.py`'s
`--self-test` (DB-free, hermetic, CI hard gate) / `--live` (real DB + real
Python/TS SSoT modules, deploy-gate mode) split — see that script's header
for the pattern this one replicates.

Scope: the four identity domains ADHIṢṬHĀNA touched — graha, varga, house,
event_class. For each domain, up to three independently-sufficient checks run
(a domain runs only the checks whose required inputs are supplied):

  (a) unregistered_alias — every alias/canonical token the PYTHON SSoT
      recognizes for this domain (`brahmagyan/graha_vocabulary.py`'s
      `_GRAHA_ALIASES` keys for graha; `brahmagyan/l0_ontology.py`'s
      per-entity_class `canonical_id` + `synonyms` for varga/house;
      `brahmagyan/l0_ghatana.py`'s `EVENT_CLASSES` ids for event_class) must
      be discoverable in the live `brahma_ontology` / `brahma_event_ontology`
      registry (as a canonical_id, canonical_name, or a synonym). Catches:
      "a new graha alias added to the Python SSoT but never registered in
      brahma_ontology's synonyms."

  (b) ssot_drift — the Python SSoT's canonical value set for a domain must
      equal the TypeScript SSoT's canonical value set for the same domain
      (only runs where both exist: graha —
      `graha_vocabulary._GRAHA_ALIASES` values vs
      `address_resolver.GRAHA_CODE_TO_NAME` keys; event_class —
      `l0_ghatana.EVENT_CLASSES` ids vs `event_classes.EVENT_CLASS_IDS`).
      varga/house have no independent TS canonical-value SSoT today (TS reads
      them live from `brahma_ontology` via `resolve_entity.ts`, it does not
      declare its own parallel set) so this check is skipped for them, not
      fabricated as a false pass. Catches: "TS and Python SSoT drifting apart
      on canonical values."

  (c) unresolved_producer_value — every DISTINCT value a producer actually
      wrote into chart data for this domain (`chart_facts.fact_subject` for
      graha/house-shaped subjects, `chart_divisionals.varga`/`.graha` for
      varga, `gochara_resonance_map.event_class` for event_class) must
      resolve into the live registry. Catches: "a producer emitting a
      graha/varga/house code that resolves to nothing in the registry."

Modes
-----
  --self-test   DB-free, hermetic. Runs bundled synthetic fixtures (one clean
                scenario per domain + one independent mutation per check
                kind). Exit 0 iff the clean fixtures produce zero violations
                AND every mutation is independently caught. This is the CI
                hard gate (CI has no database, no `npx`/node dependency).

  --live        Real-DB, real-SSoT mode (requires DBURL or DATABASE_URL).
                Imports the live Python SSoT modules directly, shells `npx
                tsx` to read the live TS SSoT modules (mirrors
                `platform/scripts/probes/probe_p1_identity.py`'s technique
                for the same reason: `address_resolver.ts` transitively
                imports the `server-only` marker package), and queries
                `brahma_ontology` / `brahma_event_ontology` / `chart_facts` /
                `chart_divisionals` / `gochara_resonance_map` read-only.
                Deploy-gate mode — never run against production from an
                untrusted context; R19 (this is governance tooling: it never
                writes to `chart_facts` or any chart table).

  --domain X    (--live only) scope to one domain (graha|varga|house|event_class).

Exit codes
----------
  0  clean (no violations / self-test pass)
  1  violations found (or self-test fail)
  2  invocation / environment error
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # platform/scripts/governance -> repo root
SIDECAR = REPO_ROOT / "platform" / "python-sidecar"
PLATFORM_DIR = REPO_ROOT / "platform"

DOMAINS = ("graha", "varga", "house", "event_class")


# ---------------------------------------------------------------------------
# Core (pure, DB-free, unit-testable, mutation-provable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    domain: str
    kind: str  # "unregistered_alias" | "ssot_drift" | "unresolved_producer_value"
    value: str
    detail: str


def _norm(s: str) -> str:
    return str(s).strip().upper()


def find_unregistered_aliases(
    domain: str, python_aliases: Iterable[str], registry_tokens: Iterable[str]
) -> list[Violation]:
    """Every alias/canonical token the Python SSoT recognizes for `domain`
    must resolve (case-insensitively) against the live registry's token set
    (canonical_id ∪ canonical_name_en ∪ canonical_name_sa ∪ synonyms)."""
    reg_norm = {_norm(t) for t in registry_tokens}
    violations = []
    for alias in sorted(set(python_aliases)):
        if _norm(alias) not in reg_norm:
            violations.append(
                Violation(
                    domain,
                    "unregistered_alias",
                    alias,
                    f"Python SSoT alias {alias!r} (domain={domain}) has no matching "
                    f"canonical_id/name/synonym in the live registry — a new alias "
                    f"was added to code but never registered.",
                )
            )
    return violations


def find_ssot_drift(
    domain: str, python_canonical: Iterable[str], ts_canonical: Iterable[str]
) -> list[Violation]:
    """The Python SSoT's canonical output set must equal the TS SSoT's
    canonical output set for `domain`, exactly (not a subset either way)."""
    py = {_norm(x) for x in python_canonical}
    ts = {_norm(x) for x in ts_canonical}
    violations = []
    for v in sorted(py - ts):
        violations.append(
            Violation(
                domain,
                "ssot_drift",
                v,
                f"{v!r} is in the Python SSoT canonical set (domain={domain}) but "
                f"absent from the TS SSoT canonical set — the two languages' "
                f"identity contracts have drifted apart.",
            )
        )
    for v in sorted(ts - py):
        violations.append(
            Violation(
                domain,
                "ssot_drift",
                v,
                f"{v!r} is in the TS SSoT canonical set (domain={domain}) but "
                f"absent from the Python SSoT canonical set — the two languages' "
                f"identity contracts have drifted apart.",
            )
        )
    return violations


def find_unresolved_producer_values(
    domain: str, producer_values: Iterable[str], registry_tokens: Iterable[str]
) -> list[Violation]:
    """Every DISTINCT value a producer actually emitted for `domain` must
    resolve (case-insensitively) into the live registry's token set."""
    reg_norm = {_norm(t) for t in registry_tokens}
    violations = []
    for v in sorted(set(producer_values)):
        if _norm(v) not in reg_norm:
            violations.append(
                Violation(
                    domain,
                    "unresolved_producer_value",
                    v,
                    f"Producer emitted {v!r} (domain={domain}) into chart data; it "
                    f"resolves to nothing in the live registry — an orphaned "
                    f"identity code with no registry entry.",
                )
            )
    return violations


def check_domain(
    domain: str,
    *,
    registry_tokens: Iterable[str],
    python_aliases: Iterable[str] | None = None,
    python_canonical: Iterable[str] | None = None,
    ts_canonical: Iterable[str] | None = None,
    producer_values: Iterable[str] | None = None,
) -> list[Violation]:
    """Run every check whose required inputs are supplied for `domain`. A
    check with a missing input is SKIPPED, never fabricated as a pass — e.g.
    varga/house supply no `ts_canonical` (no independent TS SSoT exists for
    them), so `find_ssot_drift` simply does not run for those domains."""
    violations: list[Violation] = []
    registry_tokens = list(registry_tokens)
    if python_aliases is not None:
        violations += find_unregistered_aliases(domain, python_aliases, registry_tokens)
    if python_canonical is not None and ts_canonical is not None:
        violations += find_ssot_drift(domain, python_canonical, ts_canonical)
    if producer_values is not None:
        violations += find_unresolved_producer_values(domain, producer_values, registry_tokens)
    return violations


# ---------------------------------------------------------------------------
# Self-test fixtures (DB-free hard gate + mutation proof)
# ---------------------------------------------------------------------------


def _clean_fixture() -> dict[str, dict]:
    """One internally-consistent synthetic scenario per domain. Deliberately
    small/synthetic (not the real ~9/30/12/27-entry SSoTs) — this proves the
    CORE comparison logic, exactly as msr_referential_integrity.py's fixture
    proves its core logic with 4 fake fact_ids, not a real chart. The real
    SSoT/registry/producer data is only exercised in --live mode."""
    return {
        "graha": dict(
            python_aliases={"SUN", "SURYA", "SU", "MAR", "MARS", "MANGALA", "KUJA"},
            python_canonical={"SUN", "MAR"},
            ts_canonical={"SUN", "MAR"},
            registry_tokens={"sun", "surya", "su", "mar", "mars", "mangala", "kuja"},
            producer_values={"SUN", "MAR"},
        ),
        "varga": dict(
            python_aliases={"D1", "D9", "rashi_chart", "navamsha_chart"},
            python_canonical=None,
            ts_canonical=None,
            registry_tokens={"d1", "d9", "rashi_chart", "navamsha_chart"},
            producer_values={"D1", "D9"},
        ),
        "house": dict(
            python_aliases={"HOUSE_07", "HOUSE_7", "H7", "seventh_house"},
            python_canonical=None,
            ts_canonical=None,
            registry_tokens={"house_07", "house_7", "h7", "seventh_house"},
            producer_values={"HOUSE_07", "H7"},
        ),
        "event_class": dict(
            python_aliases=None,
            python_canonical={"marriage", "separation", "childbirth"},
            ts_canonical={"marriage", "separation", "childbirth"},
            registry_tokens={"marriage", "separation", "childbirth"},
            producer_values={"marriage"},
        ),
    }


def _run_domain_fixtures(fixtures: dict[str, dict]) -> list[Violation]:
    out: list[Violation] = []
    for domain, kwargs in fixtures.items():
        out += check_domain(domain, **kwargs)
    return out


def _run_self_test() -> int:
    clean = _clean_fixture()
    clean_v = _run_domain_fixtures(clean)
    if clean_v:
        print("[registry-parity] SELF-TEST FAIL: clean fixture produced violations:", file=sys.stderr)
        for v in clean_v:
            print(f"  [{v.domain}][{v.kind}] {v.value!r}: {v.detail}", file=sys.stderr)
        return 1

    failures: list[str] = []

    # Mutation 1: unregistered_alias — a new Python alias never registered.
    mut1 = _clean_fixture()
    mut1["graha"]["python_aliases"] = set(mut1["graha"]["python_aliases"]) | {"PLUTO_XYZ"}
    v1 = check_domain("graha", **mut1["graha"])
    if not any(v.kind == "unregistered_alias" and v.value == "PLUTO_XYZ" for v in v1):
        failures.append("unregistered_alias mutation (graha, 'PLUTO_XYZ') was NOT caught.")

    # Mutation 2: ssot_drift — TS SSoT silently drops a Python-side event class.
    mut2 = _clean_fixture()
    mut2["event_class"]["ts_canonical"] = set(mut2["event_class"]["ts_canonical"]) - {"separation"}
    v2 = check_domain("event_class", **mut2["event_class"])
    if not any(v.kind == "ssot_drift" and v.value == "SEPARATION" for v in v2):
        failures.append("ssot_drift mutation (event_class, dropped 'separation' from TS) was NOT caught.")

    # Mutation 3: unresolved_producer_value — a producer emits an orphan house code.
    mut3 = _clean_fixture()
    mut3["house"]["producer_values"] = set(mut3["house"]["producer_values"]) | {"HOUSE_99"}
    v3 = check_domain("house", **mut3["house"])
    if not any(v.kind == "unresolved_producer_value" and v.value == "HOUSE_99" for v in v3):
        failures.append("unresolved_producer_value mutation (house, 'HOUSE_99') was NOT caught.")

    # Negative control: re-running the ORIGINAL clean fixture after building
    # three independent mutated copies must still be silent (mutations are
    # copies, not in-place edits — proves fixtures don't leak state).
    still_clean = _run_domain_fixtures(_clean_fixture())
    if still_clean:
        failures.append("clean fixture is no longer clean after mutation runs (fixture state leak).")

    if failures:
        print("[registry-parity] SELF-TEST FAIL:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1

    print(
        "[registry-parity] SELF-TEST PASS: 4 clean domain fixtures clean; "
        "3/3 independent mutations (unregistered_alias, ssot_drift, "
        "unresolved_producer_value) caught."
    )
    return 0


# ---------------------------------------------------------------------------
# Live mode — real Python SSoT + real TS SSoT (via npx tsx) + real DB
# ---------------------------------------------------------------------------


def _get_dburl() -> str:
    dsn = os.environ.get("DBURL") or os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit(
            "[registry-parity] Neither DBURL nor DATABASE_URL is set. --live "
            "mode needs a real connection (see the campaign kickoff for the "
            "cloud-sql-proxy one-liner). Use --self-test for the DB-free CI gate."
        )
    return dsn


def _load_python_ssot() -> dict:
    sys.path.insert(0, str(SIDECAR))
    from brahmagyan.graha_vocabulary import _GRAHA_ALIASES  # noqa: E402
    from brahmagyan import l0_ontology  # noqa: E402
    from brahmagyan.l0_ghatana import EVENT_CLASSES as PY_EVENT_CLASSES  # noqa: E402

    varga_aliases: set[str] = set()
    house_aliases: set[str] = set()
    for e in l0_ontology.ENTITIES:
        if e["entity_class"] == "varga":
            varga_aliases.add(e["canonical_id"])
            varga_aliases.update(e["synonyms"])
        elif e["entity_class"] == "house":
            house_aliases.add(e["canonical_id"])
            house_aliases.update(e["synonyms"])

    return {
        "graha_aliases": set(_GRAHA_ALIASES.keys()),
        "graha_canonical": set(_GRAHA_ALIASES.values()),
        "varga_aliases": varga_aliases,
        "house_aliases": house_aliases,
        "event_class_canonical": {e["event_class_id"] for e in PY_EVENT_CLASSES},
    }


def _run_ts_snippet(js: str) -> dict:
    """Mirrors probe_p1_identity.py's run_ts_check: --conditions=react-server
    reproduces Next's build-time export-condition routing of the `server-only`
    marker package (which address_resolver.ts transitively imports via
    `@/lib/db/client`) to a no-op, without touching any source file."""
    proc = subprocess.run(
        ["npx", "tsx", "--conditions=react-server", "-e", js],
        cwd=str(PLATFORM_DIR),
        capture_output=True,
        text=True,
        timeout=90,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"TS SSoT read failed: {proc.stderr.strip()[-2000:]}")
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError(
            f"TS SSoT read produced unparseable stdout: {proc.stdout!r} stderr: {proc.stderr!r}"
        ) from exc


def _load_ts_ssot() -> dict:
    graha_js = (
        "import {GRAHA_CODE_TO_NAME} from './src/lib/retrieval/address_resolver';"
        "console.log(JSON.stringify({graha: Object.keys(GRAHA_CODE_TO_NAME)}));"
    )
    event_js = (
        "import {EVENT_CLASS_IDS} from './src/lib/event_classes';"
        "console.log(JSON.stringify({event_class: EVENT_CLASS_IDS}));"
    )
    graha_out = _run_ts_snippet(graha_js)
    event_out = _run_ts_snippet(event_js)
    return {
        "graha_canonical": set(graha_out["graha"]),
        "event_class_canonical": set(event_out["event_class"]),
    }


def _load_registry_and_producers(conn, domains: Sequence[str]) -> dict:
    import psycopg  # psycopg3, matches msr_referential_integrity.py's import convention

    out: dict = {}
    with conn.cursor() as cur:
        if "graha" in domains:
            cur.execute(
                "SELECT canonical_id, canonical_name_en, canonical_name_sa, synonyms "
                "FROM brahma_ontology WHERE entity_class = 'planet'"
            )
            tokens: set[str] = set()
            for canonical_id, name_en, name_sa, synonyms in cur.fetchall():
                tokens.update(t for t in (canonical_id, name_en, name_sa) if t)
                tokens.update(synonyms or [])
            out["graha_registry_tokens"] = tokens

            # NOTE: 'karaka_chara_position' is deliberately EXCLUDED here — its
            # fact_subject values are Jaimini karaka ROLE names (ATMAKARAKA,
            # AMATYAKARAKA, ...), a different identity domain entirely
            # (address_resolver.ts's own KARAKA_CODE_TO_SUBJECT), not a graha
            # identity code. Including it produced false "unresolved" hits
            # against the planet registry during --live calibration
            # (2026-08-08) — confirmed by direct query, not assumed.
            cur.execute(
                "SELECT DISTINCT fact_subject FROM chart_facts "
                "WHERE fact_category IN ('graha_position', 'graha_sign_attributes')"
            )
            out["graha_producer_values"] = {r[0] for r in cur.fetchall() if r[0]}

            # chart_divisionals.graha carries four confirmed non-graha internal
            # bookkeeping sentinels (2026-08-08 live calibration, direct query):
            # 'ALL' (an all-grahas-apply row shape), 'SARVA'/'SCOPE_CAP'/'karya'
            # (ashtakavarga/scope-cap internal markers). These are a real,
            # pre-existing, out-of-Lane-A6-scope use of the column (chart_divisionals
            # is a base GA6 table — see ADHISTHANA_STATE.md backlog AB2/AB4), not a
            # graha identity that failed to register; excluded here by name so
            # this gate measures graha identity parity, not chart_divisionals'
            # internal sentinel convention.
            _NON_GRAHA_DIVISIONAL_SENTINELS = {"ALL", "SARVA", "SCOPE_CAP", "karya"}
            cur.execute("SELECT DISTINCT graha FROM chart_divisionals")
            out["graha_producer_values"] |= {
                r[0] for r in cur.fetchall() if r[0] and r[0] not in _NON_GRAHA_DIVISIONAL_SENTINELS
            }

        if "varga" in domains:
            cur.execute(
                "SELECT canonical_id, canonical_name_en, canonical_name_sa, synonyms "
                "FROM brahma_ontology WHERE entity_class = 'varga'"
            )
            tokens = set()
            for canonical_id, name_en, name_sa, synonyms in cur.fetchall():
                tokens.update(t for t in (canonical_id, name_en, name_sa) if t)
                tokens.update(synonyms or [])
            out["varga_registry_tokens"] = tokens

            # Same sentinel-exclusion discipline as the graha domain above.
            # chart_divisionals.varga carries three confirmed non-varga
            # bookkeeping labels (2026-08-08 live calibration, direct query):
            # 'D81'/'ALL_VARGAS' are rows whose graha column is itself the
            # 'SCOPE_CAP' sentinel (house/sign NULL — a scope-cap marker
            # reusing the varga column as a free-form label, not a divisional
            # chart id), and 'CROSS' rows carry degree_in_sign=0 / house=NULL
            # for every graha (a cross-check placeholder shape, not a
            # divisional position). None of the three is a real varga.
            _NON_VARGA_DIVISIONAL_SENTINELS = {"D81", "ALL_VARGAS", "CROSS"}
            cur.execute("SELECT DISTINCT varga FROM chart_divisionals")
            out["varga_producer_values"] = {
                r[0] for r in cur.fetchall() if r[0] and r[0] not in _NON_VARGA_DIVISIONAL_SENTINELS
            }

        if "house" in domains:
            cur.execute(
                "SELECT canonical_id, canonical_name_en, canonical_name_sa, synonyms "
                "FROM brahma_ontology WHERE entity_class = 'house'"
            )
            tokens = set()
            for canonical_id, name_en, name_sa, synonyms in cur.fetchall():
                tokens.update(t for t in (canonical_id, name_en, name_sa) if t)
                tokens.update(synonyms or [])
            out["house_registry_tokens"] = tokens

            cur.execute(
                r"SELECT DISTINCT fact_subject FROM chart_facts "
                r"WHERE fact_subject ~ '^(HOUSE_[0-9]+|H[0-9]+)$'"
            )
            out["house_producer_values"] = {r[0] for r in cur.fetchall() if r[0]}

        if "event_class" in domains:
            cur.execute("SELECT event_class_id FROM brahma_event_ontology")
            out["event_class_registry_tokens"] = {r[0] for r in cur.fetchall() if r[0]}

            cur.execute("SELECT DISTINCT event_class FROM gochara_resonance_map")
            out["event_class_producer_values"] = {r[0] for r in cur.fetchall() if r[0]}

    return out


def _run_live(domains: Sequence[str]) -> int:
    dsn = _get_dburl()
    try:
        import psycopg  # psycopg3
    except ImportError:
        try:
            import psycopg2 as psycopg  # type: ignore
        except ImportError:
            print("[registry-parity] neither psycopg nor psycopg2 available.", file=sys.stderr)
            return 2

    py = _load_python_ssot()
    ts = _load_ts_ssot()

    conn = psycopg.connect(dsn)
    try:
        live = _load_registry_and_producers(conn, domains)
    finally:
        conn.close()

    all_violations: list[Violation] = []

    if "graha" in domains:
        all_violations += check_domain(
            "graha",
            registry_tokens=live["graha_registry_tokens"],
            python_aliases=py["graha_aliases"],
            python_canonical=py["graha_canonical"],
            ts_canonical=ts["graha_canonical"],
            producer_values=live["graha_producer_values"],
        )
    if "varga" in domains:
        all_violations += check_domain(
            "varga",
            registry_tokens=live["varga_registry_tokens"],
            python_aliases=py["varga_aliases"],
            producer_values=live["varga_producer_values"],
        )
    if "house" in domains:
        all_violations += check_domain(
            "house",
            registry_tokens=live["house_registry_tokens"],
            python_aliases=py["house_aliases"],
            producer_values=live["house_producer_values"],
        )
    if "event_class" in domains:
        all_violations += check_domain(
            "event_class",
            registry_tokens=live["event_class_registry_tokens"],
            python_canonical=py["event_class_canonical"],
            ts_canonical=ts["event_class_canonical"],
            producer_values=live["event_class_producer_values"],
        )

    if all_violations:
        print(
            f"[registry-parity] FAIL: {len(all_violations)} violation(s) across "
            f"domains {list(domains)}:",
            file=sys.stderr,
        )
        for v in all_violations:
            print(f"  [{v.domain}][{v.kind}] {v.value!r}: {v.detail}", file=sys.stderr)
        return 1

    print(
        f"[registry-parity] PASS: 0 violations across domains {list(domains)} — "
        f"Python SSoT, TS SSoT (where applicable), the live registry, and every "
        f"producer-emitted DISTINCT value all agree."
    )
    return 0


# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true", help="Run DB-free fixture self-test (the CI hard gate).")
    ap.add_argument(
        "--live",
        action="store_true",
        help="Explicit spelling of the (also-default) live-DB mode. Requires DBURL/DATABASE_URL.",
    )
    ap.add_argument(
        "--domain",
        choices=DOMAINS,
        action="append",
        help="Scope --live to one domain (repeatable). Default: all four.",
    )
    args = ap.parse_args(argv)

    if args.self_test and args.live:
        ap.error("--self-test and --live are mutually exclusive.")

    if args.self_test:
        return _run_self_test()

    domains = tuple(args.domain) if args.domain else DOMAINS
    return _run_live(domains)


if __name__ == "__main__":
    sys.exit(main())
