"""Rebuild GA8 with per-ayanamsha retry on connection failure."""
import uuid, sys, time

sys.path.insert(0, ".")
from ga_writers.ga_positions_writer import CANONICAL_AYANAMSHAS, CANONICAL_CHART_ID, _conn
from ga_writers.ga_structural_writer import (
    build_ga_structural_substep,
    _load_yoga_catalog,
    _load_dosha_catalog,
)
from pipeline.orchestrator.birth_params import fetch_birth_params

CHART_ID = CANONICAL_CHART_ID
BUILD_ID = str(uuid.uuid4())
print(f"chart_id = {CHART_ID}")
print(f"build_id = {BUILD_ID}")

with _conn() as conn:
    BIRTH_PARAMS = fetch_birth_params(conn, CHART_ID)
    yoga_catalog = _load_yoga_catalog(conn)
    dosha_catalog = _load_dosha_catalog(conn)
    conn.commit()
print(f"Catalogs: yoga={len(yoga_catalog)} dosha={len(dosha_catalog)}")

total_rows = 0
for ayanamsha_id in CANONICAL_AYANAMSHAS:
    for attempt in range(3):
        try:
            print(f"Building {ayanamsha_id} (attempt {attempt+1}) ...")
            with _conn() as conn:
                count = build_ga_structural_substep(
                    chart_id=CHART_ID,
                    build_id=BUILD_ID,
                    ayanamsha_id=ayanamsha_id,
                    conn=conn,
                    birth_params=BIRTH_PARAMS,
                    yoga_catalog=yoga_catalog,
                    dosha_catalog=dosha_catalog,
                )
                conn.commit()
            print(f"  -> {count} rows")
            total_rows += count
            break
        except Exception as exc:
            print(f"  ATTEMPT {attempt+1} FAILED: {exc}")
            if attempt < 2:
                time.sleep(5)
    else:
        print(f"  ALL RETRIES FAILED for {ayanamsha_id}")

print(f"\nTOTAL ROWS: {total_rows}")

print("\n=== PER-CATEGORY (lahiri_chitrapaksha) ===")
with _conn() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT fact_category, COUNT(*) as cnt
            FROM chart_facts
            WHERE chart_id=%s AND build_id=%s AND ayanamsha_id='lahiri_chitrapaksha'
            GROUP BY fact_category ORDER BY cnt DESC
        """, (CHART_ID, BUILD_ID))
        for fc, cnt in cur.fetchall():
            print(f"  {fc}: {cnt}")

print("\n=== GRAPH-THEORETIC CHECK ===")
graph_cats = [
    "graha_centrality", "dispositor_tree", "chart_cluster",
    "chart_center_of_gravity", "convergence_count",
    "karaka_bhava_concordance", "nakshatra_dispositor_chain"
]
with _conn() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT fact_category, COUNT(*) as cnt FROM chart_facts
            WHERE chart_id=%s AND build_id=%s AND ayanamsha_id='lahiri_chitrapaksha'
              AND fact_category=ANY(%s) GROUP BY fact_category
        """, (CHART_ID, BUILD_ID, graph_cats))
        found = {r[0]: r[1] for r in cur.fetchall()}
        for cat in graph_cats:
            status = "OK" if found.get(cat, 0) > 0 else "MISSING"
            print(f"  {cat}: {found.get(cat, 0)} [{status}]")

print(f"\nBUILD_ID={BUILD_ID}")
