"""SR-NDH-INPLACE / SR-DOCTRINE-H (TRIAL_READY T11) — ND-H applied IN PLACE on rule_version 1.2.0: the changelog and the retained-row census.

The rulings (decisions ledger; quoted, not paraphrased):
  SR-SOLVER-PLAN-1  in-place re-derivation only for decision-pending rules, conditioned on a measured check that no sealed generation references them.
  SR-DOCTRINE-H     node mūlatrikoṇa/own signs and the five node-friendship pairs are L0 content (migration 1401, BPHS 47.34-39 and the 3.55 translator note).
  SR-NDH-INPLACE    apply the eight ND-H classes in place on 1.2.0 (no 1.4.0), with (a) the measured check covering sealed generations AND retained rows on
                    main, lane and trial databases — any retained row derived from pre-change 1.2.0 content is deleted or re-derived in the same job;
                    (b) the 1.2.0 rule-version row carries a changelog entry: ruling ids, date, the eight classes changed, content digest before and after.
                    Content follows SR-DOCTRINE-H and L0 migration 1401, which must be applied before the derivation runs.

What "the 1.2.0 content" is here. The 1.2.0 rows (P1/P3/P4 of the eight classes, `registry.ND_H_ROWS`) hold no node-dignity value of their own: they CONSUME it. Two
inputs moved, and both are in the digest:
  * the registry side — the three 1.2.0 path rows' soft factors, re-derived in place by SR-OD1 V1 (commit 5ecd70e7e) from the 1.0.0 factor set onto the owner-confirmed
    1.3.0 doctrine factors (+ karaka_agent@1.2.0); the H table (`registry.h_table_sha256('1.2.0')`) did not move;
  * the L0 side — `bg_dignity_reference` (Rāhu/Ketu mūlatrikoṇa + own signs) and `bg_graha_naisargika_friendship` (five pairs), corrected by migration 1401.
`content_bundle` states both, `content_digest` hashes the bundle, `changelog_entry` computes the before/after pair BY CODE from (a) the live registry, (b) the committed
L0 seeds the writer rebuilds from, and (c) the pre-change basis reconstructed from the 1.0.0 row and the migration-250 values (`PRE_1401_PAIRS`, cross-checked against the
migration's own guard by the test). Nothing is typed as a digest. The changelog is a committed record (`od1_ndh_changelog_1_2_0.json`) that the test recomputes: a later
edit of the 1.2.0 content moves the digest and fails that test until the entry is regenerated (`changelog --write`).

Why the changelog does not live in a persisted column. The three persisted columns of `ka_gochara_rule_path` that carry free text are digest-covered and the table is
INSERT-ONLY by migration 1154 (§2.1 amendment 1: "a path change is a new rule_version row"); appending text to `score_rule` would move every registry digest and every pin,
and pins are re-derived once at I1-FINAL (SR-GEOMETRY-PIN-ONCE), not here. Hence no edit of `registry.py` or any IMPLEMENTATION_MODULES file.

The retained-row census (`census`): per database, read-only. It reports, for every table that can hold a 1.2.0 row, the count and the ids, and classifies:
  * REGISTRY  the stored 1.2.0 path / prerequisite / soft-factor / seal rows against the declared catalogue (final profile): any divergence is STALE — the table is
              insert-only, so a stale registry row can only be removed by rebuilding the database, never edited;
  * GENERATION every generation holding a 1.2.0 row (records, windows, pins, obligations, verifications) against the L0 digests its stored input vector recorded
              (`input_generation_vector.l0`): a digest other than the post-1401 content means the generation was derived from pre-change content (STALE); a generation with
              no stored vector or no recorded L0 digest cannot be classified (UNDETERMINED — an honest null, never green).
  Verdict: STALE if either is stale; UNDETERMINED if nothing is stale but something cannot be classified; CLEAN otherwise (including no 1.2.0 row at all — nothing
  retained, nothing to delete). The L0 state of the database (post_1401 / pre_1401 / other / unreadable) is reported beside it; T10 is the claim that 1401 is applied.
`stale_generations_sql` is the ONE detector: the census runs it, and `t11_parts` renders it as the `db_sql` part the registry binds (`NOT EXISTS` its rows).

Deleting. A sealed generation, its records and its windows are immutable by design, and the rule-path tables are insert-only: this module therefore never deletes. A
database the census reads STALE is rebuilt (dropped and re-created by the job that owns it); the census output is the record of what was found.

CLI (read-only; `census` refuses a non-loopback database — a job never connects to main):
  python3 -I od1_ndh_in_place.py changelog [--write]       print (or rewrite) the changelog record
  python3 -I od1_ndh_in_place.py census --dsn <loopback dsn> [--ids]   exit 0 CLEAN, 1 STALE, 2 UNDETERMINED
  python3 -I od1_ndh_in_place.py sql                       print the read-only queries behind the census, for the cockpit to run on main with its own read-only access
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

_SIDECAR = Path(__file__).resolve().parents[2]
if str(_SIDECAR) not in sys.path:
    sys.path.insert(0, str(_SIDECAR))

from brahmagyan.l0_dignity_reference import DIGNITY_REFERENCE            # noqa: E402  the committed seed the writer rebuilds L0 from
from pipeline.orchestrator.writers import bg_dignity_reference as _l0_writer   # noqa: E402
from services.gochara_kernel import p1_operands as p1o                   # noqa: E402
from services.gochara_kernel import rule_registry as rr                  # noqa: E402
from services.gochara_rules import registry as reg                       # noqa: E402

VERSION = reg.ND_H_VERSION                                              # "1.2.0"
RULING_IDS = ("SR-DOCTRINE-H", "SR-NDH-INPLACE")
CHANGELOG_DATE = "2026-10-22"
CHANGELOG_PATH = Path(__file__).with_name("od1_ndh_changelog_1_2_0.json")
NODES = ("Rahu", "Ketu")
PATHS = ("P1", "P3", "P4")

#: migration 1401's five corrected node-friendship pairs and the relation migration 250 held (the 1401 guard names both); the test parses the migration and equals this.
PRE_1401_PAIRS = {("Rahu", "Mercury"): "friend", ("Rahu", "Mars"): "neutral", ("Rahu", "Jupiter"): "neutral",
                  ("Ketu", "Sun"): "neutral", ("Ketu", "Moon"): "neutral"}

#: the tables that can hold a row at rule_version 1.2.0, and the SQL that names a row (a table without a single id column is named by its key)
RETAINED_TABLES = (
    ("ka_gochara_relationship_record", "record_id::text"),
    ("ka_gochara_eval_window", "window_id::text"),
    ("ka_gochara_eval_window_verification", "chart_id::text || '/' || generation || '/' || path_id"),
    ("ka_gochara_search_path_pin", "chart_id::text || '/' || generation || '/' || event_class || '/' || path_id"),
    ("ka_gochara_search_obligation", "chart_id::text || '/' || generation || '/' || path_id"),
)
REGISTRY_TABLES = ("ka_gochara_rule_path", "ka_gochara_rule_path_prerequisite", "ka_gochara_rule_path_soft_factor", "ka_gochara_rule_path_seal")


# ── the content ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def content_digest(bundle: dict) -> str:
    return hashlib.sha256(_canon(bundle).encode("utf-8")).hexdigest()


def seed_friendship_rows() -> list[tuple[str, str, str]]:
    """The 72 (graha, other_graha, relation) rows the L0 writer rebuilds `bg_graha_naisargika_friendship` from (post-1401)."""
    return [(a, b, c) for a, b, c, _cite in _l0_writer._NAISARGIKA_FRIENDSHIP]


def seed_dignity_rows() -> list[dict]:
    return [dict(r) for r in DIGNITY_REFERENCE]


def pre_1401_friendship_rows() -> list[tuple[str, str, str]]:
    return [(a, b, PRE_1401_PAIRS.get((a, b), c)) for a, b, c in seed_friendship_rows()]


def pre_1401_dignity_rows() -> list[dict]:
    """Migration 250's node rows: exaltation/debilitation only — no mūlatrikoṇa sign, no own sign (migration 1401 header: 'L0 held none')."""
    out = seed_dignity_rows()
    for r in out:
        if r["graha"] in NODES:
            r.update(moolatrikona_sign=None, moolatrikona_from=None, moolatrikona_to=None, own_signs=[])
    return out


def l0_digests(dignity_rows, friendship_rows) -> dict:
    """The two L0 content digests exactly as the input vector stores them (`p1_operands` loaders' `content_digest`)."""
    return {"bg_dignity_reference": p1o.dignity_reference_from_rows(dignity_rows).content_digest,
            "bg_graha_naisargika_friendship": p1o.naisargika_from_rows(friendship_rows).content_digest}


def expected_l0_after() -> dict:
    return l0_digests(seed_dignity_rows(), seed_friendship_rows())


def expected_l0_before() -> dict:
    return l0_digests(pre_1401_dignity_rows(), pre_1401_friendship_rows())


def _node_dignity(rows) -> dict:
    keep = ("exaltation_sign", "debilitation_sign", "moolatrikona_sign", "moolatrikona_from", "moolatrikona_to", "own_signs")
    return {r["graha"]: {k: r[k] for k in keep} for r in rows if r["graha"] in NODES}


def _node_friendship(rows) -> dict:
    return {g: {o: rel for a, o, rel in sorted(rows) if a == g} for g in NODES}


def after_soft_factors() -> dict:
    """The live 1.2.0 path rows' soft-factor references (the registry the build seeds)."""
    return {pid: [list(ref) for ref in reg.RULE_PATHS[reg.composite_ref(pid, VERSION)]["soft_factors"]] for pid in PATHS}


def before_soft_factors() -> dict:
    """The pre-V1 1.2.0 rows took the BOUND 1.0.0 row's soft factors and added karaka_agent@1.2.0 (registry.py at 5ecd70e7e^, `[*_old["soft_factors"], …]`)."""
    return {pid: [list(ref) for ref in reg.RULE_PATHS[reg.composite_ref(pid, reg.RULE_VERSION)]["soft_factors"]]
            + [list(reg.composite_ref("karaka_agent", VERSION))] for pid in PATHS}


def content_bundle(*, soft_factors: dict, dignity_rows, friendship_rows) -> dict:
    """Everything the eight classes' 1.2.0 rows are derived from that moved under SR-DOCTRINE-H / SR-NDH-INPLACE, plus what did not (the H table's digest, the
    class roster), so a digest that moves says WHICH part moved."""
    return {
        "rule_version": VERSION,
        "classes": sorted(reg.ND_H_CLASSES),
        "h_table_sha256": reg.h_table_sha256(VERSION),
        "path_soft_factors": {pid: soft_factors[pid] for pid in PATHS},
        "l0_node_inputs": {"dignity": _node_dignity(dignity_rows), "friendship": _node_friendship(friendship_rows),
                           "digests": l0_digests(dignity_rows, friendship_rows)},
    }


def before_bundle() -> dict:
    return content_bundle(soft_factors=before_soft_factors(), dignity_rows=pre_1401_dignity_rows(), friendship_rows=pre_1401_friendship_rows())


def after_bundle() -> dict:
    return content_bundle(soft_factors=after_soft_factors(), dignity_rows=seed_dignity_rows(), friendship_rows=seed_friendship_rows())


def changelog_entry() -> dict:
    """The 1.2.0 rule-version changelog entry (SR-NDH-INPLACE (b)); every digest is computed here."""
    before, after = before_bundle(), after_bundle()
    return {
        "rule_version": VERSION,
        "date": CHANGELOG_DATE,
        "rulings": list(RULING_IDS),
        "classes_changed": sorted(reg.ND_H_CLASSES),
        "also_reads_1_2_0": sorted(reg.ND_P2_KB_TARGETS),        # bereavement runs P3/P4 at 1.2.0 (ND-P2 rule 3); its P1 stays at 1.0.0
        "paths": list(PATHS),
        "migration": "1401_l0_node_dignity_friendship.sql",
        "changed": {"soft_factors": before["path_soft_factors"] != after["path_soft_factors"],
                    "l0_node_inputs": before["l0_node_inputs"] != after["l0_node_inputs"],
                    "h_table": before["h_table_sha256"] != after["h_table_sha256"]},
        "content_digest_before": content_digest(before),
        "content_digest_after": content_digest(after),
        "l0_digests_before": before["l0_node_inputs"]["digests"],
        "l0_digests_after": after["l0_node_inputs"]["digests"],
    }


def render_changelog() -> str:
    return json.dumps({"schema": "ky.ndh_changelog/1", "entries": [changelog_entry()]}, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


# ── the census ───────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _is_hex64(s: str) -> bool:
    return len(s) == 64 and all(c in "0123456789abcdef" for c in s)


def stale_generations_sql(tables: tuple[str, ...], dignity_digest: str, friendship_digest: str) -> str:
    """Rows (chart_id, generation, reason) of every generation that holds a 1.2.0 row in one of `tables` and whose stored input vector does not record the post-1401 L0.

    reason: 'no_input_vector' | 'no_l0_digest_recorded' (both UNDETERMINED) | 'l0_differs_from_post_1401' (STALE). The digests are rendered as literals so the same text
    runs under a read-only psql (the registry's `db_sql` part)."""
    if not (_is_hex64(dignity_digest) and _is_hex64(friendship_digest)):
        raise ValueError("an L0 digest is 64 lowercase hex characters")
    if not tables:
        return "SELECT NULL::text, NULL::text, NULL::text WHERE false"
    held = " UNION ".join(f"SELECT chart_id, generation FROM public.{t} WHERE rule_version = '{VERSION}'" for t in tables)
    vec = "s.input_generation_vector -> 'l0'"
    return (f"SELECT h.chart_id::text, h.generation, CASE"
            f" WHEN s.chart_id IS NULL THEN 'no_input_vector'"
            f" WHEN {vec} ->> 'bg_dignity_reference' IS NULL OR {vec} ->> 'bg_graha_naisargika_friendship' IS NULL THEN 'no_l0_digest_recorded'"
            f" WHEN {vec} ->> 'bg_dignity_reference' <> '{dignity_digest}' OR {vec} ->> 'bg_graha_naisargika_friendship' <> '{friendship_digest}'"
            f" THEN 'l0_differs_from_post_1401' END AS reason"
            f" FROM ({held}) h LEFT JOIN public.ka_gochara_search_input_snapshot s ON s.chart_id = h.chart_id AND s.generation = h.generation")


ALL_RETAINED = tuple(t for t, _ in RETAINED_TABLES)


def t11_parts() -> list[dict]:
    """The registry parts that bind T11 (`trial_ready_checks.json`, arrives with the main merge-up): the oracle file, and the census SQL on the lane database.
    `NOT EXISTS` of the detector's rows — a generation that cannot be classified also reads false (null would be a green by omission)."""
    after = expected_l0_after()
    sql = ("SELECT NOT EXISTS (SELECT 1 FROM (" + stale_generations_sql(ALL_RETAINED, after["bg_dignity_reference"], after["bg_graha_naisargika_friendship"])
           + ") g WHERE g.reason IS NOT NULL) AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_rule_path_soft_factor"
           f" WHERE rule_version = '{VERSION}' AND factor_rule_version = '{reg.RULE_VERSION}')")
    return [
        # the oracle's database tests default to port 55434 and skip (the part would read null); the lane cluster's admin DSN, like the other DB-backed parts of the registry
        {"kind": "pytest", "cwd": "platform/python-sidecar", "tests": ["tests/l3/gochara/test_od1_ndh_in_place.py"],
         "env": {"GOCHARA_A53_ADMIN_DSN": "postgresql://postgres@127.0.0.1:55433/postgres", "KALA_ADMIN_DSN": "postgresql://postgres@127.0.0.1:55433/postgres",
                 "SE_EPHE_PATH": "/Users/Dev/kalayantra/ephe"}},
        {"kind": "db_sql", "dsn_env": "TRIAL_READY_LANE_DSN", "expect": "t", "sql": sql},
    ]


def _rows(conn, sql: str, params=()) -> list[tuple]:
    out = []
    for r in conn.execute(sql, params).fetchall():
        out.append(tuple(r.values()) if isinstance(r, dict) else tuple(r))
    return out


def _existing(conn, names) -> tuple[str, ...]:
    have = {r[0] for r in _rows(conn, "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = ANY(%s)", (list(names),))}
    return tuple(n for n in names if n in have)


def _declared_registry() -> dict:
    """The 1.2.0 rows the build would seed, from the SAME functions `RuleRegistryStore.seed` binds (final profile: the only one that binds 1.2.0)."""
    with rr.rule_profile(final_rules=True):
        paths = {(r["path_id"], r["rule_version"]): r for r in rr.path_rows() if r["rule_version"] == VERSION}
        pre = {(r["path_id"], r["rule_version"], r["ordinal"]): r for r in rr.prerequisite_rows() if r["rule_version"] == VERSION}
        soft = {(r["path_id"], r["rule_version"], r["factor_id"], r["factor_rule_version"]): r for r in rr.soft_factor_rows() if r["rule_version"] == VERSION}
    return {"ka_gochara_rule_path": paths, "ka_gochara_rule_path_prerequisite": pre, "ka_gochara_rule_path_soft_factor": soft,
            "ka_gochara_rule_path_seal": {(p, VERSION): {"path_id": p, "rule_version": VERSION} for p, _v in paths}}


def _registry_census(conn) -> dict:
    declared = _declared_registry()
    out, stale = {}, []
    for table in REGISTRY_TABLES:
        if not _existing(conn, [table]):
            out[table] = {"present": False}
            continue
        cols = {"ka_gochara_rule_path": ("path_id", "rule_version", "frame_kind", "frame_arg", "agent_set", "relation_set", "object_selector",
                                         "provenance", "operator_role", "ruling_ref", "score_rule"),
                "ka_gochara_rule_path_prerequisite": ("path_id", "rule_version", "ordinal", "predicate_id", "predicate_rule_version"),
                "ka_gochara_rule_path_soft_factor": ("path_id", "rule_version", "factor_id", "factor_rule_version"),
                "ka_gochara_rule_path_seal": ("path_id", "rule_version")}[table]
        keylen = {"ka_gochara_rule_path": 2, "ka_gochara_rule_path_prerequisite": 3, "ka_gochara_rule_path_soft_factor": 4, "ka_gochara_rule_path_seal": 2}[table]
        rows = _rows(conn, f"SELECT {', '.join(cols)} FROM public.{table} WHERE rule_version = %s ORDER BY {', '.join(str(i + 1) for i in range(keylen))}", (VERSION,))
        stored = {r[:keylen]: dict(zip(cols, r)) for r in rows}
        want = declared[table]
        extra = sorted(set(stored) - set(want))
        missing = sorted(set(want) - set(stored))
        differs = sorted(k for k in set(stored) & set(want)
                         if {c: rr._normalise(v) for c, v in stored[k].items()} != {c: rr._normalise(rr._adapt(v)) for c, v in want[k].items()})
        # an absent row is not stale (nothing retained); a stored row that is not the declared one is
        out[table] = {"present": True, "count": len(stored), "ids": [list(k) for k in sorted(stored)], "not_declared": [list(k) for k in extra],
                      "differs_from_declared": [list(k) for k in differs], "declared_but_absent": [list(k) for k in missing]}
        stale += [(table, k) for k in extra + differs]
    return {"tables": out, "stale": [[t, list(k)] for t, k in stale]}


def _l0_state(conn) -> dict:
    after, before = expected_l0_after(), expected_l0_before()
    try:
        cur = conn.cursor()
        d, f = p1o.load_dignity_reference(cur), p1o.load_naisargika(cur)
    except Exception as exc:                                                   # noqa: BLE001 — unreadable L0 is a reported state, not a crash
        try:
            conn.rollback()
        except Exception:                                                      # noqa: BLE001
            pass
        return {"state": "unreadable", "why": f"{type(exc).__name__}: {str(exc)[:160]}", "digests": None}
    digests = {"bg_dignity_reference": d.content_digest, "bg_graha_naisargika_friendship": f.content_digest}
    state = "post_1401" if digests == after else "pre_1401" if digests == before else "other"
    return {"state": state, "digests": digests}


def census(conn, *, ids: bool = False) -> dict:
    """The retained-row census of one database (read-only). `ids=False` prints the first/last ids and a digest of the id list instead of every id."""
    after = expected_l0_after()
    l0 = _l0_state(conn)
    reg_c = _registry_census(conn)
    tables = _existing(conn, ALL_RETAINED)
    retained = {}
    for t, idexpr in RETAINED_TABLES:
        if t not in tables:
            retained[t] = {"present": False}
            continue
        found = [r[0] for r in _rows(conn, f"SELECT {idexpr} FROM public.{t} WHERE rule_version = %s ORDER BY 1", (VERSION,))]
        item = {"present": True, "count": len(found), "ids_sha256": hashlib.sha256(_canon(found).encode()).hexdigest() if found else None}
        item["ids"] = found if ids else found[:3] + (["…"] if len(found) > 6 else []) + (found[-3:] if len(found) > 3 else [])
        retained[t] = item
    snapshot_present = bool(_existing(conn, ["ka_gochara_search_input_snapshot"]))
    gens = []
    if tables:
        if not snapshot_present:
            held = _rows(conn, " UNION ".join(f"SELECT chart_id::text, generation, 'no_input_vector' FROM public.{t} WHERE rule_version = '{VERSION}'" for t in tables))
            gens = [list(r) for r in held]
        else:
            gens = [list(r) for r in _rows(conn, "SELECT * FROM (" + stale_generations_sql(tables, after["bg_dignity_reference"], after["bg_graha_naisargika_friendship"])
                                            + ") g WHERE g.reason IS NOT NULL ORDER BY 1, 2")]
    stale_gen = [g for g in gens if g[2] == "l0_differs_from_post_1401"]
    undet_gen = [g for g in gens if g[2] != "l0_differs_from_post_1401"]
    holds_rows = any(v.get("count") for v in retained.values() if v.get("present")) or bool(reg_c["stale"])
    l0_blocks = holds_rows and l0["state"] == "pre_1401"
    l0_unknown = holds_rows and l0["state"] in ("other", "unreadable")
    nothing_to_read = not tables and not any(t.get("present") for t in reg_c["tables"].values())
    if reg_c["stale"] or stale_gen or l0_blocks:
        verdict = "STALE"
    elif undet_gen or l0_unknown or nothing_to_read:             # a database with no gochara table at all is not "clean": the detector had nothing to run on
        verdict = "UNDETERMINED"
    else:
        verdict = "CLEAN"
    return {"rule_version": VERSION, "l0": l0, "expected_post_1401_l0": after, "registry": reg_c, "retained": retained,
            "stale_generations": stale_gen, "undetermined_generations": undet_gen, "no_gochara_tables": nothing_to_read, "verdict": verdict,
            "remedy": None if verdict == "CLEAN" else
            "rebuild the database: the rule-path tables are insert-only (migration 1154) and a sealed generation's rows are immutable — a stale or unclassifiable 1.2.0 row "
            "is replaced by building the database again on the post-1401 chain, not edited"}


# ── CLI ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def census_queries() -> list[tuple[str, str]]:
    """(label, SQL) — every query the census runs, as plain read-only SQL (no parameters), so the cockpit can run the SAME census on a database a job may not open."""
    after = expected_l0_after()
    out = [(f"retained ids: {t}", f"SELECT {idexpr} FROM public.{t} WHERE rule_version = '{VERSION}' ORDER BY 1") for t, idexpr in RETAINED_TABLES]
    out += [(f"registry rows: {t}", f"SELECT * FROM public.{t} WHERE rule_version = '{VERSION}' ORDER BY 1, 2") for t in REGISTRY_TABLES]
    out.append(("pre-V1 membership (a 1.2.0 path naming a 1.0.0 factor)",
                f"SELECT path_id, factor_id, factor_rule_version FROM public.ka_gochara_rule_path_soft_factor WHERE rule_version = '{VERSION}' AND factor_rule_version = '{reg.RULE_VERSION}'"))
    out.append(("generations holding 1.2.0 rows that are not provably post-1401 (empty = none)",
                "SELECT * FROM (" + stale_generations_sql(ALL_RETAINED, after["bg_dignity_reference"], after["bg_graha_naisargika_friendship"])
                + ") g WHERE g.reason IS NOT NULL ORDER BY 1, 2"))
    out.append(("L0 node rows (compare with the post-1401 values; the tool's digest is over all 9 / 72 rows)",
                "SELECT graha, exaltation_sign, debilitation_sign, moolatrikona_sign, moolatrikona_from, moolatrikona_to, own_signs FROM public.bg_dignity_reference ORDER BY graha"))
    out.append(("ledger: when 1401 was applied", "SELECT filename, applied_at FROM public._migrations_applied WHERE filename LIKE '1401\\_%'"))
    return out


def _loopback_connect(dsn: str):
    import psycopg
    u = urlsplit(dsn)
    if u.hostname not in ("127.0.0.1", "localhost", "::1") or "," in (u.netloc or ""):
        raise SystemExit("refused: the census reads a loopback database only")
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=5, options="-c default_transaction_read_only=on")
    return conn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("changelog")
    c.add_argument("--write", action="store_true")
    k = sub.add_parser("census")
    k.add_argument("--dsn", required=True)
    k.add_argument("--ids", action="store_true")
    sub.add_parser("sql")
    a = ap.parse_args(argv)
    if a.cmd == "sql":
        for label, q in census_queries():
            print(f"-- {label}\n{q};\n")
        return 0
    if a.cmd == "changelog":
        text = render_changelog()
        if a.write:
            CHANGELOG_PATH.write_text(text, encoding="utf-8")
        sys.stdout.write(text)
        return 0
    conn = _loopback_connect(a.dsn)
    try:
        result = census(conn, ids=a.ids)
    finally:
        conn.close()
    print(json.dumps(result, indent=1, sort_keys=True, default=str))
    return {"CLEAN": 0, "STALE": 1, "UNDETERMINED": 2}[result["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
