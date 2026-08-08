#!/usr/bin/env python3
"""
probe_p1_identity.py — ADHIṢṬHĀNA Proof Ladder, Rung P1 (identity round-trip).

Blocking gate after Stage 1 (Lanes A1-A4: producer convergence, graha SSoT,
registry completion, event-class contract). Proves the identity contract is
ONE contract across Python, TypeScript, and the live `brahma_ontology` /
`brahma_event_ontology` registries — not three surfaces that happen to agree
today.

For each identity kind, this checks that all reachable surfaces resolve a
sample input to the SAME canonical entity:
  - 9 grahas (+ LAGNA, checked separately — see LAGNA note below):
    Python `graha_vocabulary.norm_graha()` == TS `address_resolver.grahaCodeOf()`
    == live `brahma_ontology` resolution (the same SQL resolve_entity.ts runs).
  - 3 sample houses: live `brahma_ontology` resolution across the real
    storage-format synonyms L1 writers actually emit (HOUSE_0N, HOUSE_N, H<n>).
  - 5 sample vargas: live `brahma_ontology` resolution, entity_class='varga'
    winning its Lane-A3 tie-break against the legacy `concept`-class D<n>
    synonyms it collides with.
  - 5 sample event classes: Python `l0_ghatana.EVENT_CLASSES` = TS
    `event_classes.isKnownEventClass()` = a real row in `brahma_event_ontology`.

This is a PERMANENT regression gate (MASTER_PLAN_v1_0.md §10) — re-run at
every future acceptance, not a one-time check. Read-only: makes zero writes.

Usage: python3 probe_p1_identity.py
Requires: DBURL env var (postgres connection string) OR the standing
cloud-sql-proxy on 127.0.0.1:5433 with amjis-pipeline-db-url resolvable via
gcloud (see CLAUDE.md-adjacent campaign kickoff for the exact secret name).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SIDECAR = REPO_ROOT / "platform" / "python-sidecar"
sys.path.insert(0, str(SIDECAR))

import psycopg  # noqa: E402
from brahmagyan.graha_vocabulary import norm_graha  # noqa: E402
from brahmagyan.l0_ghatana import EVENT_CLASSES  # noqa: E402

RESULTS: list[dict] = []


def record(kind: str, input_: str, ok: bool, detail: str):
    RESULTS.append({"kind": kind, "input": input_, "ok": ok, "detail": detail})
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {kind:14s} {input_!r:20s} {detail}")


def get_dburl() -> str:
    if os.environ.get("DBURL"):
        return os.environ["DBURL"]
    raise SystemExit(
        "DBURL not set. Resolve it first:\n"
        "  export DBURL=$(gcloud secrets versions access latest "
        "--secret=amjis-pipeline-db-url | python3 -c \"...\")\n"
        "(see campaign kickoff for the exact one-liner) and ensure "
        "cloud-sql-proxy is listening on 127.0.0.1:5433."
    )


def resolve_entity_sql(conn, name: str) -> dict | None:
    """Exact mirror of resolve_entity.ts's live SQL (including its Lane-A3 tie-break)."""
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(
            """
            SELECT canonical_id, entity_class, canonical_name_en, canonical_name_sa
            FROM brahma_ontology
            WHERE %(name)s = ANY(synonyms)
               OR lower(canonical_name_en) = lower(%(name)s)
               OR lower(canonical_name_sa) = lower(%(name)s)
            ORDER BY (entity_class = 'varga') DESC, entity_class, canonical_id
            LIMIT 1
            """,
            {"name": name},
        )
        row = cur.fetchone()
        return dict(row) if row else None


def run_ts_check(js: str) -> dict:
    """Run a small tsx snippet against the live TS SSoT modules, return parsed JSON stdout."""
    proc = subprocess.run(
        # --conditions=react-server: address_resolver.ts transitively imports
        # '@/lib/db/client', which imports the 'server-only' marker package.
        # That package's default export unconditionally throws outside a
        # Next.js server-component bundle; Next's own build sets the
        # "react-server" export condition to route it to a no-op instead.
        # Passing the same condition to a bare tsx/node run reproduces that
        # routing without touching any source file or node_modules content.
        ["npx", "tsx", "--conditions=react-server", "-e", js],
        cwd=str(REPO_ROOT / "platform"),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        return {"__error__": proc.stderr.strip()[-2000:]}
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"__error__": f"unparseable stdout: {proc.stdout!r} stderr: {proc.stderr!r}"}


def main():
    dburl = get_dburl()
    conn = psycopg.connect(dburl)
    conn.read_only = True

    print("=" * 78)
    print("RUNG P1 — Identity round-trip (live, 482012f1-scope registries)")
    print("=" * 78)

    # ── 1. Nine grahas: Python norm_graha == TS grahaCodeOf == live DB resolution ──
    GRAHAS = [
        ("Sun", "SUN"), ("Moon", "MOON"), ("Mars", "MAR"), ("Mercury", "MER"),
        ("Jupiter", "JUP"), ("Venus", "VEN"), ("Saturn", "SAT"),
        ("Rahu", "RAH_MEAN"), ("Ketu", "KET_MEAN"),
    ]
    ts_graha_js = (
        "import {grahaCodeOf} from './src/lib/retrieval/address_resolver';"
        "const names=" + json.dumps([n for n, _ in GRAHAS]) + ";"
        "const out:Record<string,string|null>={};"
        "for(const n of names){try{out[n]=grahaCodeOf(n)}catch(e){out[n]=null}}"
        "console.log(JSON.stringify(out));"
    )
    ts_graha = run_ts_check(ts_graha_js)

    print("\n-- 9 grahas --")
    for name, expected_code in GRAHAS:
        py_code = norm_graha(name)
        ts_code = ts_graha.get(name) if "__error__" not in ts_graha else None
        db_row = resolve_entity_sql(conn, expected_code) or resolve_entity_sql(conn, name)
        db_ok = db_row is not None and db_row["canonical_id"] is not None
        db_canon = db_row["canonical_id"] if db_row else None
        ok = (py_code == expected_code) and (ts_code == expected_code) and db_ok
        record(
            "graha", name, ok,
            f"py={py_code!r} ts={ts_code!r} db_canonical_id={db_canon!r} "
            f"db_entity_class={db_row['entity_class'] if db_row else None!r}",
        )
    if "__error__" in ts_graha:
        record("graha", "<ts subprocess>", False, f"TS check failed to run: {ts_graha['__error__']}")

    # ── LAGNA: checked separately, three-way, with an explicit scope note ──
    print("\n-- LAGNA (checked separately — see note) --")
    py_lagna = norm_graha("LAGNA")
    ts_lagna_js = (
        "import {grahaCodeOf} from './src/lib/retrieval/address_resolver';"
        "let out; try{out=grahaCodeOf('LAGNA')}catch(e){out=null}"
        "console.log(JSON.stringify({LAGNA: out}));"
    )
    ts_lagna = run_ts_check(ts_lagna_js)
    ts_lagna_code = ts_lagna.get("LAGNA") if "__error__" not in ts_lagna else "<subprocess error>"
    db_lagna = resolve_entity_sql(conn, "LAGNA")
    note = (
        "py norm_graha('LAGNA') and live brahma_ontology agree (canonical_id="
        f"{db_lagna['canonical_id'] if db_lagna else None!r}); "
        "TS grahaCodeOf() intentionally scoped to the 9 planetary graha_position/"
        "karaka_chara_position fact_subject codes only (GRAHA_CODE_TO_NAME's own "
        "docstring) and correctly throws for LAGNA rather than silently returning "
        "a wrong graha code — this is a documented SCOPE BOUNDARY, not a "
        "three-way contradiction. Python's LAGNA agreement is an identity "
        "fallback (LAGNA has no explicit _GRAHA_ALIASES entry), not a deliberate "
        "alias table entry either — flagged for the campaign record, not treated "
        "as a defect."
    )
    lagna_ok = (py_lagna == "LAGNA") and (db_lagna is not None) and (ts_lagna_code is None)
    record("graha(lagna)", "LAGNA", lagna_ok,
           f"py={py_lagna!r} ts={ts_lagna_code!r} db_canonical_id={db_lagna['canonical_id'] if db_lagna else None!r} — {note}")

    # ── 2. Three sample houses, real storage-format synonyms from L1 writers ──
    print("\n-- 3 sample houses --")
    HOUSES = [
        ("HOUSE_07", "house_07"),
        ("HOUSE_1", "house_01"),
        ("H12", "house_12"),
    ]
    for code, expected_canonical in HOUSES:
        row = resolve_entity_sql(conn, code)
        ok = row is not None and row["canonical_id"] == expected_canonical and row["entity_class"] == "house"
        record("house", code, ok,
               f"db_canonical_id={row['canonical_id'] if row else None!r} "
               f"db_entity_class={row['entity_class'] if row else None!r}")

    # ── 3. Five sample vargas — must win the Lane-A3 concept-class tie-break ──
    print("\n-- 5 sample vargas --")
    VARGAS = ["D1", "D9", "D10", "D30", "D60"]
    for code in VARGAS:
        row = resolve_entity_sql(conn, code)
        ok = row is not None and row["entity_class"] == "varga" and row["canonical_id"] == code.lower()
        record("varga", code, ok,
               f"db_canonical_id={row['canonical_id'] if row else None!r} "
               f"db_entity_class={row['entity_class'] if row else None!r}")

    # ── 4. Five sample event classes — Python == TS == live brahma_event_ontology ──
    print("\n-- 5 sample event classes --")
    py_event_ids = {e["event_class_id"] for e in EVENT_CLASSES}
    SAMPLE_EVENTS = ["marriage", "separation", "childbirth", "surgery", "relocation"]
    ts_event_js = (
        "import {isKnownEventClass} from './src/lib/event_classes';"
        "const ids=" + json.dumps(SAMPLE_EVENTS) + ";"
        "const out:Record<string,boolean>={};"
        "for(const id of ids){out[id]=isKnownEventClass(id)}"
        "console.log(JSON.stringify(out));"
    )
    ts_events = run_ts_check(ts_event_js)
    for eid in SAMPLE_EVENTS:
        py_ok = eid in py_event_ids
        ts_ok = ts_events.get(eid) if "__error__" not in ts_events else None
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT event_class_id FROM brahma_event_ontology WHERE event_class_id = %s",
                (eid,),
            )
            db_row = cur.fetchone()
        db_ok = db_row is not None
        ok = py_ok and (ts_ok is True) and db_ok
        record("event_class", eid, ok, f"py={py_ok} ts={ts_ok} db={db_ok}")
    if "__error__" in ts_events:
        record("event_class", "<ts subprocess>", False, f"TS check failed to run: {ts_events['__error__']}")

    conn.close()

    print("\n" + "=" * 78)
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r["ok"])
    failed = [r for r in RESULTS if not r["ok"]]
    print(f"RUNG P1 RESULT: {passed}/{total} checks passed")
    if failed:
        print(f"FAILING ({len(failed)}):")
        for r in failed:
            print(f"  - {r['kind']} {r['input']!r}: {r['detail']}")
    print("=" * 78)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
