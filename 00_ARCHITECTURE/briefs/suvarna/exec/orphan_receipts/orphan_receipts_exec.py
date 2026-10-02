#!/usr/bin/env python3
"""D6 owner-path executor: retire the ORPHANED legacy `__whole_asset__` receipt row (and its asset_freshness twin)
of ONE asset on ONE chart. One-shot operator tool (not product code); parameterised so the same executor serves
ga_positions at S-L1 and bo_laksana / bo_sangati / bo_cgm_motifs / bo_upaya at S-L2.

  python3 orphan_receipts_exec.py --asset <asset_id> --chart <chart_id> --dry-run [--min-build-after <ISO ts>]
  python3 orphan_receipts_exec.py --asset <asset_id> --chart <chart_id> --apply --expect-plan <sha256>
                                  --min-build-after <ISO ts, tz-aware> [--expect-evidence <sha256>]

  exit codes: 0 ok / committed; 1 apply refused or aborted; 2 dry-run refused; 3 dry-run counterfactual (no --min-build-after)

  --dry-run   runs EVERY check and the real DELETEs inside one transaction, then ALWAYS ROLLS BACK, and prints the
              full diff JSON plus the plan hash it computes.
  --apply     requires --expect-plan == the plan hash and --min-build-after; re-checks every condition inside the
              same transaction; COMMITs only if all pass (otherwise ROLLBACK and exit 1).

Every condition is a CHECK that REFUSES (P1-P5 pre-checks, D/V/A post-checks, E evidence digest: see run_txn); nothing is committed unless all hold. Before-images of
both rows (all columns, JSON) and a reversal SQL file are written to the evidence directory BEFORE any DELETE; if they
cannot be written the run aborts (rollback) in both modes.

Admin credential: fetched from Secret Manager in-process (same mechanism as ChartGrants/cg_exec.py), never printed,
logged or saved. Proxy 127.0.0.1:5433. `main()` is the only place that reaches the real database; tests call
`execute()` with an injected connection factory against a disposable local Postgres.

plan hash = sha256(plan_text + "\\n" + json.dumps(DIFF)); the plan text embeds this file's own sha256 and that of
resolver_verdicts.sql (so the hash binds the executor and the verdict definition). The hash is computed WITHOUT the
database. The DB-dependent part (before-images, verdict diff, row counts, ACL/RLS/policy/membership snapshots) is
computed at dry-run/apply time and bound by the optional `evidence_digest` (see PLAN.md).
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import uuid

import psycopg

PROJECT = "madhav-astrology"
OWNER = "amjis_app"
WHOLE = "__whole_asset__"
RECEIPTS = "asset_provenance_receipts"
FRESH = "asset_freshness"
EVIDENCE_ROOT = "/Users/Dev/suvarna-evidence/OrphanReceipts"
HERE = pathlib.Path(__file__).resolve().parent
VERDICT_SQL_FILE = HERE / "resolver_verdicts.sql"
INFLIGHT_STATES = ("planned", "running", "paused")
EXPECTED_VERDICT = ("receipt_not_proven", "RESOLVED")
ASSET_RE = re.compile(r"^[a-z][a-z0-9_]{1,62}$")

# The two DELETEs. Shared by the executor and the rendered plan text so they cannot drift apart.
# The state guards mean the executor can never delete a proven/fresh row (it only ever removes an `unknown`/non-fresh
# orphan; it never creates or edits a receipt, so no freshness is fabricated).
DELETE_FRESH = ("DELETE FROM public.asset_freshness WHERE asset_id = %(a)s AND chart_id = %(c)s::uuid "
                "AND partition_key = '__whole_asset__' AND freshness_state IN ('stale','unknown')")
DELETE_RECEIPT = ("DELETE FROM public.asset_provenance_receipts WHERE asset_id = %(a)s AND chart_id = %(c)s::uuid "
                  "AND partition_key = '__whole_asset__' AND receipt_state = 'unknown'")
LOCK_SQL = ("LOCK TABLE public.asset_provenance_receipts, public.asset_freshness, public.build_runs "
            "IN SHARE ROW EXCLUSIVE MODE")

ACL_SQL = """
SELECT c.relname, COALESCE(r.rolname,'PUBLIC'), a.privilege_type, a.is_grantable::text
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault('r', c.relowner))) a
LEFT JOIN pg_roles r ON r.oid=a.grantee
WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')
"""
OWN_SQL = ("SELECT c.relname, pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
           "WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f')")
MEMBER_SQL = ("SELECT r.rolname, m.rolname, (to_jsonb(am) - 'oid')::text FROM pg_auth_members am "  # all option columns, any PG major
              "JOIN pg_roles r ON r.oid=am.roleid JOIN pg_roles m ON m.oid=am.member")
RLS_SQL = ("SELECT c.relname, c.relrowsecurity::text, c.relforcerowsecurity::text FROM pg_class c "
           "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p')")
POLICY_SQL = ("SELECT c.relname, p.polname, p.polcmd::text, p.polroles::text, pg_get_expr(p.polqual,p.polrelid), "
              "coalesce(pg_get_expr(p.polwithcheck,p.polrelid),'') FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid")


class EvidenceError(Exception):
    """before-images / reversal SQL could not be written: the run aborts (rollback)."""


# --------------------------------------------------------------------------------------------- plan text + hash
def exec_sha(path=None):
    return hashlib.sha256(pathlib.Path(path or __file__).read_bytes()).hexdigest()


def expected_diff(asset, chart):
    """The static, DB-independent expectation bound into the plan hash."""
    return sorted([
        "%s|%s|%s|%s|present->absent" % (FRESH, asset, chart, WHOLE),
        "%s|%s|%s|%s|present->absent" % (RECEIPTS, asset, chart, WHOLE),
        "resolver_verdict|%s|%s->%s" % ((asset,) + EXPECTED_VERDICT),
    ])


def render_plan(asset, chart, sha, vsha=None):
    vsha = vsha or sha_file(VERDICT_SQL_FILE)
    d = {"a": asset, "c": chart}
    fresh = DELETE_FRESH.replace("%(a)s", "'%s'" % asset).replace("%(c)s", "'%s'" % chart)
    rec = DELETE_RECEIPT.replace("%(a)s", "'%s'" % asset).replace("%(c)s", "'%s'" % chart)
    return "\n".join([
        "-- plan: retire the ORPHANED legacy __whole_asset__ receipt row and its asset_freshness twin for asset %s on chart %s (data rows only: no grant, no schema, no code, no other row of any table)" % (asset, chart),
        "SET LOCAL search_path = pg_catalog, pg_temp",
        "SET LOCAL lock_timeout = '5s'",
        "SET LOCAL statement_timeout = '5s'",
        "SET LOCAL TimeZone = 'UTC'",
        "-- snapshot A (session user): relacl + owner of every public relation, relrowsecurity/relforcerowsecurity, pg_policy, pg_auth_members",
        "-- membership: GRANT %s TO <session user> only if missing; REVOKE before snapshot B only if granted here" % OWNER,
        "SET LOCAL ROLE %s" % OWNER,
        LOCK_SQL,
        "-- before-images (all columns, JSON) of both rows + reversal INSERT SQL written to the evidence directory BEFORE any DELETE; if unwritable: abort + ROLLBACK",
        "-- resolver port (resolver_verdicts.sql, chart-parameterised) run for ALL assets: verdicts A; row-key+md5 map of both tables A",
        "-- pre-checks (any failure: no DELETE is issued, ROLLBACK):",
        "--   P1 registry declares a non-empty natural_key_partition for the asset, != '__whole_asset__'",
        "--   P2 the __whole_asset__ receipt is receipt_state='unknown' and its twin freshness_state in ('stale','unknown') (never a proven/fresh row)",
        "--   P3 a PROVEN declared-partition receipt exists with freshness 'fresh', from a COMPLETED build that is newer than the __whole_asset__ row's build",
        "--      AND its receipt observed_at and its build created_at are > --min-build-after (required at --apply; a runtime parameter, tz-aware, bound by the evidence digest; a --dry-run without it is a counterfactual only, exit 3)",
        "--   P4 exactly 1 receipt row and exactly 1 freshness twin for (asset, chart, '__whole_asset__')",
        "--   P5 zero build_runs in state planned/running/paused on ANY chart",
        fresh + "   -- rowcount must be 1",
        rec + "   -- rowcount must be 1",
        "-- resolver port again: verdicts B; row-key+md5 map B",
        "RESET ROLE",
        "-- REVOKE %s FROM <session user> only if granted here; snapshot B" % OWNER,
        "-- commit only if: both DELETE rowcounts == 1; the row-key+md5 diff of BOTH tables is exactly the two removed keys (no other row of any table changed); the per-asset verdict diff over ALL assets is exactly {%s: %s -> %s}; relacl, owner, relrowsecurity, relforcerowsecurity, pg_policy and pg_auth_members diffs between snapshot A and B are all empty; chart-scoped receipt<->freshness twin integrity unchanged" % ((asset,) + EXPECTED_VERDICT),
        "-- --dry-run: the same statements, then ROLLBACK, always. --apply: COMMIT only if every check above holds and --expect-plan equals this plan hash.",
        "-- resolver port: resolver_verdicts.sql sha256 %s" % vsha,
        "-- executor: orphan_receipts_exec.py sha256 %s" % sha,
    ])


def plan_hash(asset, chart, sha=None):
    text = render_plan(asset, chart, sha or exec_sha())
    return hashlib.sha256((text + "\n" + json.dumps(expected_diff(asset, chart))).encode()).hexdigest()


# --------------------------------------------------------------------------------------------- db plumbing
def secret(name):
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest", "--secret", name, "--project", PROJECT],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("secret access failed")
    return r.stdout.rstrip("\r\n")


def connect_admin():
    return psycopg.connect(host="127.0.0.1", port=5433, dbname="amjis", user="postgres",
                           password=secret("cloudsql-postgres-admin-password"), sslmode="disable",
                           connect_timeout=15)


def load_verdict_sql():
    lines = [ln for ln in VERDICT_SQL_FILE.read_text().splitlines() if not ln.lstrip().startswith("--")]
    return "\n".join(lines).replace(":'chart'", "%(chart)s")


def verdicts(cur, chart, sql):
    cur.execute(sql, {"chart": chart})
    return {r[0]: r[1] for r in cur.fetchall()}


def snap(cur):
    out = {}
    for k, sql in (("acl", ACL_SQL), ("own", OWN_SQL), ("mem", MEMBER_SQL), ("rls", RLS_SQL), ("pol", POLICY_SQL)):
        cur.execute(sql)
        out[k] = {tuple(map(str, row)) for row in cur.fetchall()}
    return out


def key_map(cur, table):
    cur.execute("SELECT asset_id, scope_key, partition_key, md5(t::text) FROM public.%s t" % table)
    return sorted(tuple(r) for r in cur.fetchall())


def twin_integrity(cur, chart):
    cur.execute("SELECT (SELECT count(*) FROM public.asset_freshness f WHERE f.chart_id = %(c)s::uuid AND NOT EXISTS "
                "(SELECT 1 FROM public.asset_provenance_receipts r WHERE r.asset_id=f.asset_id AND r.scope_key=f.scope_key "
                "AND r.partition_key=f.partition_key)), "
                "(SELECT count(*) FROM public.asset_provenance_receipts r WHERE r.chart_id = %(c)s::uuid AND NOT EXISTS "
                "(SELECT 1 FROM public.asset_freshness f WHERE r.asset_id=f.asset_id AND r.scope_key=f.scope_key "
                "AND r.partition_key=f.partition_key))", {"c": chart})
    return list(cur.fetchone())


def chart_counts(cur, chart):
    cur.execute("SELECT (SELECT count(*) FROM public.asset_provenance_receipts WHERE chart_id=%(c)s::uuid), "
                "(SELECT count(*) FROM public.asset_freshness WHERE chart_id=%(c)s::uuid)", {"c": chart})
    r = cur.fetchone()
    return {RECEIPTS: r[0], FRESH: r[1]}


def table_columns(cur, table):
    cur.execute("SELECT quote_ident(a.attname), format_type(a.atttypid, a.atttypmod), a.attname, (a.attgenerated <> '') "
                "FROM pg_attribute a WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped "
                "ORDER BY a.attnum", ("public." + table,))
    return [{"ident": r[0], "type": r[1], "name": r[2], "generated": r[3]} for r in cur.fetchall()]


def fetch_images(cur, table, asset, chart):
    """Full before-image (to_jsonb of every column) plus the quoted-literal values for the reversal INSERT."""
    cols = table_columns(cur, table)
    ins = [c for c in cols if not c["generated"]]
    sel = ", ".join("quote_nullable(t.%s::text)" % c["ident"] for c in ins)
    cur.execute("SELECT to_jsonb(t)::text, ARRAY[%s] FROM public.%s t WHERE t.asset_id = %%(a)s AND "
                "t.chart_id = %%(c)s::uuid AND t.partition_key = %%(p)s ORDER BY 1" % (sel, table),
                {"a": asset, "c": chart, "p": WHOLE})
    rows = cur.fetchall()
    images = [json.loads(r[0]) for r in rows]
    inserts = ["INSERT INTO public.%s (%s) VALUES (%s);" % (
        table, ", ".join(c["ident"] for c in ins),
        ", ".join("%s::%s" % (v, c["type"]) for v, c in zip(r[1], ins))) for r in rows]
    return {"columns": [{"name": c["name"], "type": c["type"], "generated": c["generated"]} for c in cols],
            "rows": images}, inserts


def sha_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def write_evidence(root, asset, chart, ts, images, inserts, sha):
    """Create <root>/<asset>_<chart8>_<UTC ts>/ (0700) with before_images.json + reversal.sql (0600) and SHA256SUMS."""
    try:
        rootp = pathlib.Path(root)
        rootp.mkdir(mode=0o700, parents=True, exist_ok=True)
        d = rootp / ("%s_%s_%s" % (asset, chart[:8], ts))
        d.mkdir(mode=0o700)
        os.chmod(d, 0o700)
        bi = json.dumps({"asset_id": asset, "chart_id": chart, "partition_key": WHOLE, "tables": images},
                        indent=2, sort_keys=True) + "\n"
        rev = "\n".join([
            "-- REVERSAL for the retirement of the orphaned %s receipt + freshness twin of %s on chart %s." % (WHOLE, asset, chart),
            "-- Re-inserts exactly the rows captured in before_images.json (scope_key is GENERATED and is not inserted).",
            "-- Run in ONE transaction through the same D6 owner path (transient membership of %s + SET LOCAL ROLE %s)." % (OWNER, OWNER),
            "-- executor sha256 %s" % sha,
            "BEGIN;",
            "SET LOCAL TimeZone = 'UTC';",
            "SET LOCAL ROLE %s;" % OWNER,
        ] + inserts[RECEIPTS] + inserts[FRESH] + ["COMMIT;", ""])
        files = {"before_images.json": bi, "reversal.sql": rev}
        for name, text in files.items():
            fd = os.open(str(d / name), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as fh:
                fh.write(text)
        sums = {n: sha_file(d / n) for n in files}
        (d / "SHA256SUMS").write_text("".join("%s  %s\n" % (h, n) for n, h in sorted(sums.items())))
        os.chmod(d / "SHA256SUMS", 0o600)
    except OSError as exc:
        raise EvidenceError("cannot write evidence under %s (%s)" % (root, type(exc).__name__))
    return {"dir": str(d), "before_images.json": {"path": str(d / "before_images.json"), "sha256": sums["before_images.json"]},
            "reversal.sql": {"path": str(d / "reversal.sql"), "sha256": sums["reversal.sql"]}}


# --------------------------------------------------------------------------------------------- the transaction
def parse_min(value):
    if value is None:
        return None
    t = dt.datetime.fromisoformat(value)
    if t.tzinfo is None:
        raise SystemExit("REFUSED: --min-build-after must carry a timezone (e.g. 2026-10-05T09:00:00Z)")
    return t


def run_txn(conn, args, sha, phash, evidence_root, now):
    asset, chart = args.asset, args.chart
    min_after = parse_min(args.min_build_after)
    apply_mode = bool(args.apply)
    cur = conn.cursor()
    checks = collections.OrderedDict()

    def chk(name, ok, detail=None):
        checks[name] = {"ok": bool(ok), "detail": detail}
        return bool(ok)

    def skip(name, why):  # a check that could not run because a pre-check already refused (ok=None, not a pass)
        checks[name] = {"ok": None, "detail": "not run: " + why}

    cur.execute("SET LOCAL search_path = pg_catalog, pg_temp")
    cur.execute("SET LOCAL lock_timeout = '5s'")
    cur.execute("SET LOCAL statement_timeout = '5s'")
    cur.execute("SET LOCAL TimeZone = 'UTC'")
    snap_a = snap(cur)
    cur.execute("SELECT pg_has_role(session_user, %s, 'MEMBER'), quote_ident(session_user)", (OWNER,))
    is_member, who = cur.fetchone()
    granted = False
    if not is_member:
        cur.execute("GRANT %s TO %s" % (OWNER, who))
        granted = True
    cur.execute("SET LOCAL ROLE %s" % OWNER)
    cur.execute(LOCK_SQL)

    # ---- before-images: written to disk BEFORE any DELETE; failure aborts the run
    images, inserts = {}, {}
    for t in (RECEIPTS, FRESH):
        images[t], inserts[t] = fetch_images(cur, t, asset, chart)
    ts = now.strftime("%Y%m%dT%H%M%S%fZ")  # microseconds: a dry run and an apply never collide
    evidence = write_evidence(evidence_root, asset, chart, ts, images, inserts, sha)
    n_rec, n_fr = len(images[RECEIPTS]["rows"]), len(images[FRESH]["rows"])

    sql_v = load_verdict_sql()
    v_before = verdicts(cur, chart, sql_v)
    km_before = {t: key_map(cur, t) for t in (RECEIPTS, FRESH)}
    counts_before = chart_counts(cur, chart)
    twin_before = twin_integrity(cur, chart)

    # ---- P1 registry declares a partition (orphan by definition, part 1)
    cur.execute("SELECT natural_key_partition FROM public.asset_registry WHERE asset_id = %s", (asset,))
    reg = cur.fetchall()
    declared = reg[0][0] if len(reg) == 1 else None
    declares = declared is not None and declared.strip() != "" and declared != WHOLE
    chk("P1_registry_declares_partition", declares,
        {"asset_in_registry": len(reg) == 1, "declared_partition_length": len(declared) if declared else 0})

    # ---- P2 the __whole_asset__ rows are the unproven artefact, never a proven/fresh row
    orphan = None
    if n_rec == 1:
        orphan = images[RECEIPTS]["rows"][0]
    ofr = images[FRESH]["rows"][0] if n_fr == 1 else None
    chk("P2_orphan_is_unproven",
        orphan is not None and orphan["receipt_state"] == "unknown" and ofr is not None
        and ofr["freshness_state"] in ("stale", "unknown"),
        {"receipt_state": orphan and orphan["receipt_state"], "freshness_state": ofr and ofr["freshness_state"]})

    # ---- P3 a PROVEN declared-partition receipt from a LATER, completed build exists (and is newer than --min-build-after)
    later = {"found": False}
    p3 = False
    if declares and orphan is not None:
        cur.execute(
            "SELECT d.receipt_state, f.freshness_state, d.observed_at, d.build_id::text, br.state, br.created_at, "
            "       (ba.run_id IS NOT NULL), ba.disposition, o.observed_at, obr.created_at "
            "FROM public.asset_provenance_receipts d "
            "LEFT JOIN public.asset_freshness f ON f.asset_id=d.asset_id AND f.scope_key=d.scope_key "
            "     AND f.partition_key=d.partition_key AND f.receipt_version=d.receipt_version "
            "LEFT JOIN public.build_runs br ON br.id=d.build_id AND br.chart_id=d.chart_id "
            "LEFT JOIN public.build_run_assets ba ON ba.run_id=d.build_id AND ba.asset_id=d.asset_id "
            "JOIN public.asset_provenance_receipts o ON o.asset_id=d.asset_id AND o.scope_key=d.scope_key AND o.partition_key=%(w)s "
            "LEFT JOIN public.build_runs obr ON obr.id=o.build_id AND obr.chart_id=o.chart_id "
            "WHERE d.asset_id=%(a)s AND d.chart_id=%(c)s::uuid AND d.partition_key=%(p)s",
            {"a": asset, "c": chart, "p": declared, "w": WHOLE})
        r = cur.fetchall()
        if len(r) == 1:
            (rs, fs, d_obs, d_build, run_state, run_created, asset_row, disp, o_obs, o_run_created) = r[0]
            d_ts = run_created or d_obs
            o_ts = o_run_created or o_obs
            newer_than_orphan = (d_ts is not None and o_ts is not None and d_ts > o_ts and d_obs > o_obs)
            after_min = (min_after is None) or (d_obs > min_after and run_created is not None and run_created > min_after)
            p3 = (rs == "proven" and fs == "fresh" and run_state == "completed" and asset_row
                  and newer_than_orphan and after_min)
            later = {"found": True, "receipt_state": rs, "freshness_state": fs, "run_state": run_state,
                     "build_disposition": disp, "newer_than_orphan_build": bool(newer_than_orphan),
                     "after_min_build_after": bool(after_min), "min_build_after_given": min_after is not None,
                     "declared_observed_at": d_obs.isoformat(), "declared_build_created_at": run_created and run_created.isoformat(),
                     "orphan_build_created_at": o_run_created and o_run_created.isoformat(),
                     "orphan_observed_at": o_obs.isoformat()}
    chk("P3_later_proven_declared_receipt", p3, later)

    # ---- P4 exactly one receipt row and exactly one freshness twin
    chk("P4_rowcount_receipt_is_1", n_rec == 1, {"found": n_rec})
    chk("P4_rowcount_freshness_is_1", n_fr == 1, {"found": n_fr})

    # ---- P5 no build in flight on ANY chart (real column: build_runs.state)
    cur.execute("SELECT left(chart_id::text, 8), state FROM public.build_runs WHERE state = ANY(%s) ORDER BY 1, 2",
                (list(INFLIGHT_STATES),))
    inflight = [list(r) for r in cur.fetchall()]
    chk("P5_no_build_in_flight", len(inflight) == 0, {"in_flight": len(inflight), "chart_prefix_state": inflight})

    pre_ok = all(c["ok"] is True for c in checks.values())
    d_fresh = d_rec = None
    v_after, km_after, counts_after, twin_after = v_before, km_before, counts_before, twin_before
    if pre_ok:
        cur.execute(DELETE_FRESH, {"a": asset, "c": chart})
        d_fresh = cur.rowcount
        cur.execute(DELETE_RECEIPT, {"a": asset, "c": chart})
        d_rec = cur.rowcount
        chk("D_delete_rowcounts_are_1_and_1", d_fresh == 1 and d_rec == 1, {"freshness": d_fresh, "receipt": d_rec})
        v_after = verdicts(cur, chart, sql_v)
        km_after = {t: key_map(cur, t) for t in (RECEIPTS, FRESH)}
        counts_after = chart_counts(cur, chart)
        twin_after = twin_integrity(cur, chart)
    else:
        skip("D_delete_rowcounts_are_1_and_1", "a pre-check refused; no DELETE was issued")

    # ---- other rows untouched (row-key + md5 of the whole row, both tables)
    removed = lambda r: r[0] == asset and r[1] == chart and r[2] == WHOLE
    exp_after = {t: sorted(r for r in km_before[t] if not removed(r)) for t in (RECEIPTS, FRESH)}
    if pre_ok:
        chk("D_no_other_row_touched", all(km_after[t] == exp_after[t] for t in (RECEIPTS, FRESH)),
            {"receipts_before": len(km_before[RECEIPTS]), "receipts_after": len(km_after[RECEIPTS]),
             "freshness_before": len(km_before[FRESH]), "freshness_after": len(km_after[FRESH])})
        chk("D_twin_integrity_unchanged", twin_before == twin_after,
            {"freshness_without_receipt_and_receipt_without_freshness_before": twin_before, "after": twin_after})
    else:
        skip("D_no_other_row_touched", "a pre-check refused")
        skip("D_twin_integrity_unchanged", "a pre-check refused")

    # ---- resolver verdict diff over ALL assets
    vdiff = {a: [v_before.get(a), v_after.get(a)] for a in sorted(set(v_before) | set(v_after))
             if v_before.get(a) != v_after.get(a)}
    if pre_ok:
        chk("V_verdict_diff_is_exactly_the_asset", vdiff == {asset: list(EXPECTED_VERDICT)},
            {"diff": vdiff, "expected": {asset: list(EXPECTED_VERDICT)}})
    else:
        skip("V_verdict_diff_is_exactly_the_asset", "a pre-check refused")

    # ---- ACL / owner / RLS / policy / membership diffs: all must be empty (transient membership revoked first)
    cur.execute("RESET ROLE")
    if granted:
        cur.execute("REVOKE %s FROM %s" % (OWNER, who))
    snap_b = snap(cur)
    acl_diff = sorted("%s|%s|%s|grantable=%s|absent->present" % t for t in (snap_b["acl"] - snap_a["acl"])) + \
        sorted("%s|%s|%s|grantable=%s|present->absent" % t for t in (snap_a["acl"] - snap_b["acl"]))
    diffs = {k: len(snap_a[k] ^ snap_b[k]) for k in ("own", "rls", "pol", "mem")}
    chk("A_acl_diff_empty", acl_diff == [], {"acl_diff": acl_diff})
    chk("A_owner_diff_empty", diffs["own"] == 0, {"count": diffs["own"]})
    chk("A_rls_diff_empty", diffs["rls"] == 0, {"count": diffs["rls"]})
    chk("A_policy_diff_empty", diffs["pol"] == 0, {"count": diffs["pol"]})
    chk("A_membership_diff_empty", diffs["mem"] == 0, {"count": diffs["mem"], "transient_membership_granted": granted})

    n_res = lambda v: {"resolved": sum(1 for x in v.values() if x == "RESOLVED"),
                       "unresolved": sum(1 for x in v.values() if x != "RESOLVED")}
    rowcounts = {"orphan_rows_found": {RECEIPTS: n_rec, FRESH: n_fr}, "delete_rowcounts": {RECEIPTS: d_rec, FRESH: d_fresh},
                 "chart_scoped_before": counts_before, "chart_scoped_after": counts_after,
                 "table_totals_before": {t: len(km_before[t]) for t in km_before},
                 "table_totals_after": {t: len(km_after[t]) for t in km_after}}
    evidence_digest = hashlib.sha256(json.dumps({
        "asset": asset, "chart": chart, "min_build_after": min_after.isoformat() if min_after else None,
        "plan_hash": phash, "executor_sha256": sha,
        "before_images_sha256": evidence["before_images.json"]["sha256"], "reversal_sha256": evidence["reversal.sql"]["sha256"],
        "verdict_diff": vdiff, "chart_scoped_before": counts_before, "chart_scoped_after": counts_after,
        "checks": {k: v["ok"] for k, v in checks.items()}}, sort_keys=True).encode()).hexdigest()
    if apply_mode and args.expect_evidence is not None:
        chk("E_evidence_digest_matches_expected", args.expect_evidence == evidence_digest,
            {"computed": evidence_digest, "expected": args.expect_evidence})

    failed = [k for k, v in checks.items() if v["ok"] is False]
    skipped = [k for k, v in checks.items() if v["ok"] is None]
    result = {
        "asset": asset, "chart": chart, "mode": "apply" if apply_mode else "dry-run",
        "executor_sha256": sha, "plan_hash": phash, "min_build_after": min_after.isoformat() if min_after else None,
        "checks": checks, "failed_checks": failed, "skipped_checks": skipped,
        "rowcounts": rowcounts, "verdict_diff": vdiff,
        "verdict_counts": {"before": n_res(v_before), "after": n_res(v_after)},
        "acl_diff": acl_diff, "rls_diff": diffs["rls"], "policy_diff": diffs["pol"], "membership_diff": diffs["mem"],
        "owner_diff": diffs["own"],
        "before_images": evidence, "evidence_digest": evidence_digest,
    }
    return result, (not failed and not skipped)


def save_result(result):
    """Best effort: keep the printed diff JSON next to the before-images (not part of any hash)."""
    try:
        d = result["before_images"]["dir"]
        fd = os.open(os.path.join(d, "result.json"), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    except (OSError, KeyError):
        result.setdefault("warnings", []).append("result.json could not be saved next to the before-images")


def execute(args, connect, evidence_root=EVIDENCE_ROOT, now=None):
    """Returns (exit_code, result dict). `connect` is the only door to a database."""
    now = now or dt.datetime.now(dt.timezone.utc)
    sha = exec_sha()
    phash = plan_hash(args.asset, args.chart, sha)
    if args.apply:
        if args.expect_plan != phash:
            raise SystemExit("REFUSED: --expect-plan does not equal the plan hash")
        if args.min_build_after is None:
            raise SystemExit("REFUSED: --apply requires --min-build-after")
    parse_min(args.min_build_after)
    conn = connect()
    try:
        try:
            result, good = run_txn(conn, args, sha, phash, evidence_root, now)
        except EvidenceError as exc:
            conn.rollback()
            return 1, {"status": "ABORTED_ROLLED_BACK", "reason": "before-images not writable: %s" % exc,
                       "plan_hash": phash, "executor_sha256": sha}
        except Exception:
            conn.rollback()
            raise
        if args.apply and good:
            result["status"] = "COMMITTED"
            conn.commit()
            save_result(result)
            return 0, result
        conn.rollback()  # --dry-run ALWAYS ends here
        if args.apply:
            result["status"] = "REFUSED_ROLLED_BACK"
            save_result(result)
            return 1, result
        if good and args.min_build_after is None:
            # P3 was evaluated WITHOUT the rebuild gate, so this is a counterfactual, not a rehearsal of --apply
            result["status"] = "DRY_RUN_ROLLED_BACK_COUNTERFACTUAL_NO_MIN_BUILD_AFTER"
            result["warnings"] = ["--min-build-after not supplied: the 'declared receipt is from the S-L1 rebuild' gate was not "
                                  "applied. --apply requires it and would refuse unless the declared receipt is newer than it."]
            save_result(result)
            return 3, result
        result["status"] = "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD" if good else "DRY_RUN_ROLLED_BACK_REFUSED"
        save_result(result)
        return (0 if good else 2), result
    finally:
        conn.close()


def build_parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--asset", required=True)
    p.add_argument("--chart", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", dest="dry_run")
    g.add_argument("--apply", action="store_true")
    p.add_argument("--expect-plan")
    p.add_argument("--expect-evidence")
    p.add_argument("--min-build-after")
    p.add_argument("--evidence-root", default=EVIDENCE_ROOT)
    return p


def parse_args(argv):
    p = build_parser()
    a = p.parse_args(argv)
    if not ASSET_RE.match(a.asset):
        p.error("--asset must match %s" % ASSET_RE.pattern)
    try:
        a.chart = str(uuid.UUID(a.chart))
    except ValueError:
        p.error("--chart must be a uuid")
    if a.apply and not a.expect_plan:
        p.error("--apply requires --expect-plan <sha256>")
    return a


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        code, result = execute(args, connect_admin, evidence_root=args.evidence_root)
    except SystemExit:
        raise
    except Exception as exc:
        print("failed: %s %s" % (type(exc).__name__, str(exc)[:200].replace("\n", " ")))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return code


if __name__ == "__main__":
    sys.exit(main())
