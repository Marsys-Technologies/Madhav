#!/usr/bin/env python3
"""Login-only probe of the D6 administrator credential path (SS RELEASE probe). No transaction work, no grant, nothing written.
Uses the executor's OWN connect_admin() (Secret Manager -> 127.0.0.1:5433 as postgres). Prints PASS/FAIL + error CLASS only."""
import importlib.util, sys, os
D = "/Users/Dev/suvarna-d6rf/00_ARCHITECTURE/briefs/suvarna/exec/f_a2_key_widening"
sys.path.insert(0, D)
try:
    spec = importlib.util.spec_from_file_location("d6exec", os.path.join(D, "d6_dataplane_capture_fa2_exec.py"))
    m = importlib.util.module_from_spec(spec); sys.modules["d6exec"] = m; spec.loader.exec_module(m)
    conn = m.connect_admin()
except SystemExit as e:
    print("PROBE FAIL class=secret_access_failed(SystemExit)"); sys.exit(2)
except Exception as e:
    sq = getattr(e, "sqlstate", None) or getattr(getattr(e, "diag", None), "sqlstate", None)
    print(f"PROBE FAIL class={type(e).__name__} sqlstate={sq}"); sys.exit(2)
try:
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("select current_user, rolsuper, rolcreaterole, pg_has_role(current_user,'pg_read_all_stats','MEMBER'), pg_has_role(current_user,'pg_monitor','MEMBER'), current_setting('server_version_num')::int/10000, current_database() from pg_roles where rolname = current_user")
    r = cur.fetchone()
    print(f"PROBE PASS current_user={r[0]} rolsuper={r[1]} rolcreaterole={r[2]} pg_read_all_stats_member={r[3]} pg_monitor_member={r[4]} server_major={r[5]} database={r[6]}")
finally:
    conn.close()
