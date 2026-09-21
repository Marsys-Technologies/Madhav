# READ-ONLY. Re-runs the independent reviewer's counterexamples (ASTRA_REVIEW_GOCHARA_PLAN_v0_2.md App. C/D, F4.3, F4.6).
import sys, pathlib
from dataclasses import replace
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[6] / "platform" / "python-sidecar"))
import swisseph as swe
from scipy.interpolate import CubicSpline
from services.w2g.arcs import build_arcs, _station_times
from services.w2g.crossings import find_contacts
from services.ka_kshetra.stage0_kinematics import build_spline, find_contact_episodes
from services.gochara_v3.tests.test_speedup import _build_context_for_benchmark
from services.gochara_v3 import engine as E
from services.gochara_grammar import primitives as P
T=[0.0,1.0,2.0,3.0]; f=lambda t:100.0+(t-1.5)**3/3.0-0.01*(t-1.5); L=[f(t) for t in T]; sp=CubicSpline(T,L)
print("close stations: actual", sorted(float(r) for r in sp.derivative().roots(extrapolate=False)), "| w2g retains", _station_times(sp,T))
print("roots of target 100: expected 3 | w2g finds", [round(e.exact_jd,6) for e in find_contacts(build_arcs('Mercury',T,L),100.0,1.0,tolerance_arcsec=1e-7)])
print("wrap tangency at 360/0, orb 1: w2g contacts =", len(find_contacts(build_arcs('X',T,[357.75,359.75,359.75,357.75]),0.0,1.0)), "(expected >=1)")
print("S0 body already inside orb for whole horizon: episodes =", find_contact_episodes(build_spline(T,[100.0,100.1,100.2,100.3],[0.1]*4),natal_lon=100.0,body='Saturn',target_ref='t',t_grid=T,orb_deg=1.0,orb_source='t'), "(expected 1)")
ctx=_build_context_for_benchmark('marriage')[0]; tg=replace(ctx.resonance_targets[0],target_longitude_deg=None,target_sign='Libra')
a=swe.julday(2026,1,1,12.0); t=a+30
allev=P.drishti_contact(swe,ctx.chart_id,tg,a-5,a+185,planets=['Jupiter']); loc=P.drishti_contact(swe,ctx.chart_id,tg,t-5,t+5,planets=['Jupiter'])
print("sign-only drishti residence: engine-window activity", E._compute_activity_v3(loc,ctx.weight_by_target_ref)[0], "| filtered global list", E._compute_activity_v3([e for e in allev if t-5<=e.event_jd<=t+5],ctx.weight_by_target_ref)[0])
swe.set_sid_mode(swe.SIDM_LAHIRI)
for y,m,d in ((2026,1,1),(2020,1,1),(1984,2,5)):
    jd=swe.julday(y,m,d,12.0); a1=swe.calc_ut(jd,swe.MOON,swe.FLG_SWIEPH|swe.FLG_SIDEREAL)[0][0]; a2=(swe.calc_ut(jd,swe.MOON,swe.FLG_SWIEPH)[0][0]-swe.get_ayanamsa_ut(jd))%360
    print(f"two sidereal conventions in this repo disagree (Moon, {y}): {(a1-a2)*3600:+.3f} arcsec")
