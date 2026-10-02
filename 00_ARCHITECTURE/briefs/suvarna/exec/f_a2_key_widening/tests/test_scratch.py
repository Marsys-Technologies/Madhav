import time, pytest, conftest as cf, real_writers as rw

@pytest.fixture()
def runner(cluster, mod, db, tmp_path):
    return cf.Runner(cluster, mod, db, tmp_path)

def test_flow(runner, cluster, db):
    cluster.su(db, "GRANT SELECT ON public.bg_shashtiamsha_deities TO data_plane_builder")
    code, r = runner.run("apply"); assert code == 0, r["details"]
    t=time.time(); print(rw.load_upstream(cluster, db, ("ga_positions","ga_vargas","ga_strength","ga_nakshatra","ga_panchanga","ga_sensitive")), time.time()-t)
    import ga_writers.ga_structural_writer as gsw; rw.shim_ascendant_longitude(gsw)
    W = rw.load_writer("ga_structural")
    for label in ("patched", "rolledback"):
        if label == "rolledback":
            code, r = runner.run("rollback"); assert code == 0, r["details"]
        run = rw.new_run(cluster, db, "ga_structural"); conn = rw.connect(cluster, db)
        ctx = rw.context(cluster, db, "ga_structural", run, conn)
        t=time.time()
        try:
            print(label, rw.drive(W, ctx, only={"ayanamsha_lahiri_chitrapaksha"}), time.time()-t)
            rw.finish_run(cluster, db, run, "ga_structural")
        except Exception as e:
            print(label, "FAILED", type(e).__name__, str(e)[:200]); conn.rollback(); rw.fail_run(cluster, db, run, "ga_structural")
        conn.close()
