import re, sys, os, subprocess
from pathlib import Path
OUT = Path(sys.argv[1]); REPO = Path('/Users/Dev/suvarna-al5')
W = 'platform/python-sidecar/pipeline/orchestrator/writers/'
def find(path):
    p = REPO / path
    if p.exists(): return p
    # basename search for short names
    base = os.path.basename(path)
    out = subprocess.run(['git', '-C', str(REPO), 'ls-files', '*' + path], capture_output=True, text=True).stdout.split('\n')
    out = [o for o in out if o]
    return (REPO / out[0]) if len(out) >= 1 else None
cache = {}
def nlines(p):
    if p not in cache: cache[p] = len(open(p, errors='ignore').read().split('\n'))
    return cache[p]
bad = []; total = 0; unresolved = set()
for f in sorted(OUT.glob('*_ELEVATION_BRIEF_v1_0.md')):
    a = f.name.replace('_ELEVATION_BRIEF_v1_0.md', '')
    txt = f.read_text()
    wp = REPO / (W + a + '.py') if (REPO / (W + a + '.py')).exists() else None
    for m in re.finditer(r'`?([A-Za-z0-9_./\[\]-]*[A-Za-z0-9_\]]\.(?:py|ts|tsx|json|sql|md)):(\d+)(?:-(\d+))?', txt):
        path, n1, n2 = m.group(1), int(m.group(2)), m.group(3)
        p = find(path) if '/' in path or path.endswith(('.py', '.ts', '.tsx')) else None
        if p is None: unresolved.add(path); continue
        total += 1
        hi = int(n2) if n2 else n1
        if hi > nlines(p): bad.append((a, path, n1, n2, nlines(p)))
    if wp:
        for m in re.finditer(r'(?<![A-Za-z0-9_.\]/])(?::)(\d+)(?:-(\d+))?', txt):
            n1 = int(m.group(1)); n2 = m.group(2); hi = int(n2) if n2 else n1
            total += 1
            if hi > nlines(wp): bad.append((a, 'bare(writer)', n1, n2, nlines(wp)))
print('citations checked', total, 'out of range', len(bad), 'unresolved paths', len(unresolved))
for b in bad: print(' OUT', b)
print(sorted(unresolved)[:30])
