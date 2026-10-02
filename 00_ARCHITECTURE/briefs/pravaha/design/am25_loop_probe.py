"""Read-only probe for design/AM25_RETROGRADE_LOOP_ROOT_IDENTITY_CANDIDATE_v1_0.md: the kernel's own solve_episodes on the real ephemeris.
Run from platform/python-sidecar:  python3 <this file> Saturn 2023 2026   (prints every (target, level) that holds >= 3 episodes). No database access."""
import sys; sys.path.insert(0,'.')
from datetime import datetime, timedelta, timezone
from services.gochara_kernel.knots import calc_sidereal_lon
from services.gochara_kernel.arcs import build_arc_index
from services.gochara_kernel.episodes import solve_episodes
EPHE="/Users/Dev/madhav-l3/gochara-wp0-7/.run/se1"
UTC=timezone.utc
nat={"JUP":249.7875,"KET":229.0330,"LAGNA":12.4311,"MAR":198.5192,"MER":270.8388,"MOON":327.0552,"RAH":49.0330,"SAT":202.4320,"SUN":291.9626,"VEN":259.1727}
def jd(dt): return dt.timestamp()/86400+2440587.5
def iso(j): return datetime.fromtimestamp((j-2440587.5)*86400,tz=UTC).strftime('%Y-%m-%d %H:%M:%S')
body=sys.argv[1]; y0=int(sys.argv[2]); y1=int(sys.argv[3])
lo=datetime(y0,1,1,tzinfo=UTC); hi=datetime(y1,1,1,tzinfo=UTC)
knots=[jd(lo)+i for i in range(int((jd(hi)-jd(lo))))]
lons=[calc_sidereal_lon(body,k,EPHE)[0] for k in knots]
idx=build_arc_index(body,knots,lons)
for name,t in nat.items():
    for rel,src in (("conjunction","orb_conj_slow"),("drishti_contact","orb_drishti_slow")):
        try: eps=solve_episodes(idx,body,rel,t,(knots[0],knots[-1]),src,ephe_path=EPHE)
        except Exception as e: continue
        by={}
        for e in eps: by.setdefault(round(e.level_deg,3),[]).append(e)
        for lvl,es in by.items():
            if len(es)>=3:
                print(f"== {body} {rel} natal {name} {t} level {lvl} orb {es[0].orb_max_deg}")
                for e in es:
                    print(f"   t_in {iso(e.t_in)}  exact {iso(e.t_exact) if e.t_exact else None}  t_out {iso(e.t_out)}  branch {e.branch}  dwell {e.dwell_days:.4f}  station_flag {e.station_flag}  near_station_unres {e.near_station_unresolved}")
