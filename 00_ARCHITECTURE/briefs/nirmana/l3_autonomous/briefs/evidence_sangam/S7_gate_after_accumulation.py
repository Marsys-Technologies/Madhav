"""P:48 (performance-path observation, NOT R-4's occupancy/tangency test — those are SPEC). Proposition:
find_aspect_events appends every event and returns the full list; the engine's 0.45 gate runs afterwards.
Source structure via AST: the append is inside the search loop; a single 'return events' follows it."""
import ast
from _common import *
head("S7 — orb gate runs after full accumulation (AST)")
tree = ast.parse("\n".join(src('pipeline/transit_search.py')))
fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'find_aspect_events')
appends = [n.lineno for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(getattr(n.func,'value',None),'id',None)=='events' and n.func.attr=='append']
rets = [n.lineno for n in ast.walk(fn) if isinstance(n, ast.Return)]
in_loop = any(isinstance(p, (ast.For, ast.While)) for p in ast.walk(fn) for c in ast.walk(p) if isinstance(c, ast.Call) and c.lineno in appends and p.lineno < c.lineno)
if NEG: appends, rets = [], [1]
prop("append occurs inside the search loop", bool(appends) and in_loop, f"append lines={appends}")
prop("single return of the full list after the loop", len(rets) >= 1 and (not appends or max(appends) < max(rets)), f"return lines={rets}")
g = grep('services/ka_sangam/engine.py', r'orb_s < HIGH_CONFIDENCE_ORB_THRESHOLD'); call = grep('services/ka_sangam/engine.py', r'find_aspect_events\(')
prop("engine gate line follows the scan call", bool(g) and bool(call) and min(i for i,_ in g) > min(i for i,_ in call if i > 1000), f"gate={[i for i,_ in g]} call={[i for i,_ in call]}")
done()
