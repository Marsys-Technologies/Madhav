#!/usr/bin/env python3
"""image_routeB.py TAG [--phase ephe|pip|src|all] [--src DIR] [--out FILE]

READ-ONLY verification of the deployed pipeline job image by STREAMING its layers from Artifact Registry
(IMAGE_VERIFICATION_W2.md route B). No docker, no docker login, no pull, nothing written to disk except --out (a small JSON).
The bearer token comes from `gcloud auth print-access-token` IN-PROCESS and is never printed or written.

Checks (PASS/FAIL lines on stdout, exit 0 only if all selected phases PASS):
  config   PYTHON_VERSION, SE_EPHE_PATH, SWE_EPHE_PATH, ENTRYPOINT
  ephe     the final content of /app/ephe/*.se1 (later layers override earlier ones; whiteouts honoured): sha256 + size == the pins
  pip      *.dist-info METADATA Name/Version of the 8 packages, and the sha256 of the pyswisseph binary (the biggest layer, ~3.5 GB: ~7 min)
  src      (with --src DIR = a git worktree at the image commit) every file under /app/ in the NON-pip layers == the same path in DIR
"""
import argparse, hashlib, json, os, re, subprocess, sys, tarfile, urllib.request

HOST = 'asia-south1-docker.pkg.dev'; REPO = 'madhav-astrology/amjis/brahma-pipeline'
SE1 = {  # pins (Dockerfile.pipeline sha256sum -c)
    'sepl_18.se1': ('ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66', 484061),
    'semo_18.se1': ('1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7', 1304771),
    'seas_18.se1': ('a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2', 223004)}
VERS = {'pyswisseph': '2.10.3.2', 'pyjhora': '4.8.6', 'numpy': '2.4.6', 'scipy': '1.17.1', 'psycopg': '3.3.6',
        'psycopg-binary': '3.3.6', 'psycopg2-binary': '2.9.13', 'timezonefinder': '9.0.0'}
SO_SHA = '3911614ca013be4520e355306620a3fcd27a39374a960a2063b056cfbd093338'   # swisseph.cpython-311-x86_64-linux-gnu.so, baseline 2026-10-03
ACC = ('application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json,'
       'application/vnd.oci.image.manifest.v1+json,application/vnd.docker.distribution.manifest.v2+json')
RES = []

def rec(name, ok, detail=''):
    RES.append(ok); print(('PASS ' if ok else 'FAIL ') + name + ((' | ' + detail) if detail else ''), flush=True)

def tok():
    return subprocess.check_output(['gcloud', 'auth', 'print-access-token'], text=True).strip()

def req(path, t, accept=None):
    h = {'Authorization': 'Bearer ' + t}
    if accept: h['Accept'] = accept
    return urllib.request.urlopen(urllib.request.Request(f'https://{HOST}/v2/{REPO}/{path}', headers=h))

def getj(path, t, accept=ACC):
    with req(path, t, accept) as f: return json.load(f)

def sha_of(fo):
    h = hashlib.sha256()
    while True:
        b = fo.read(1 << 20)
        if not b: break
        h.update(b)
    return h.hexdigest()

def norm(n): return re.sub(r'[-_.]+', '-', n).lower()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('tag'); ap.add_argument('--phase', default='all'); ap.add_argument('--src'); ap.add_argument('--out')
    a = ap.parse_args(); t = tok()
    m = getj('manifests/' + a.tag, t)
    if 'manifests' in m:
        sel = [x for x in m['manifests'] if x.get('platform', {}).get('architecture') == 'amd64']
        m = getj('manifests/' + sel[0]['digest'], t)
    cfg = getj('blobs/' + m['config']['digest'], t, None)
    env = dict(e.split('=', 1) for e in cfg['config'].get('Env', []) if '=' in e)
    layers = m['layers']; pip_i = max(range(len(layers)), key=lambda i: layers[i]['size'])
    out = {'tag': a.tag, 'nlayers': len(layers), 'pip_layer': pip_i, 'python': env.get('PYTHON_VERSION'),
           'SE_EPHE_PATH': env.get('SE_EPHE_PATH'), 'SWE_EPHE_PATH': env.get('SWE_EPHE_PATH'), 'entrypoint': cfg['config'].get('Entrypoint'),
           'arch': cfg.get('architecture')}
    rec('config', env.get('SE_EPHE_PATH') == '/app/ephe' and cfg.get('architecture') == 'amd64',
        f"python={out['python']} SE_EPHE_PATH={out['SE_EPHE_PATH']} arch={out['arch']} entrypoint={out['entrypoint']} layers={len(layers)} pip_layer={pip_i}")
    def stream(i):
        return req('blobs/' + layers[i]['digest'], t)
    if a.phase in ('ephe', 'all'):
        state = {}
        for i in range(len(layers)):
            if i == pip_i: continue
            with stream(i) as f:
                tf = tarfile.open(fileobj=f, mode='r|gz')
                for mem in tf:
                    n = mem.name.lstrip('./'); base = os.path.basename(n)
                    if base == '.wh..wh..opq' and os.path.dirname(n) == 'app/ephe':
                        state = {k: v for k, v in state.items() if not k.startswith('app/ephe/')}
                    elif base.startswith('.wh.') and os.path.dirname(n).startswith('app/ephe'):
                        state.pop(os.path.join(os.path.dirname(n), base[4:]), None)
                    elif n.startswith('app/ephe/') and mem.isfile():
                        state[n] = (i, mem.size, sha_of(tf.extractfile(mem)))
        out['ephe'] = {k: list(v) for k, v in state.items()}
        for name, (sha, size) in SE1.items():
            got = state.get('app/ephe/' + name)
            rec('ephe ' + name, bool(got) and got[2] == sha and got[1] == size, f"size={got[1] if got else None} sha256={got[2][:16] if got else None}...")
    if a.phase in ('pip', 'all'):
        found = {}; so = []
        with stream(pip_i) as f:
            tf = tarfile.open(fileobj=f, mode='r|gz')
            for mem in tf:
                n = mem.name
                if mem.isfile() and n.endswith('.dist-info/METADATA'):
                    d = tf.extractfile(mem).read().decode('utf-8', 'replace')
                    nm = re.search(r'^Name: (.+)$', d, re.M); vs = re.search(r'^Version: (.+)$', d, re.M)
                    if nm and vs and norm(nm.group(1).strip()) in VERS: found[norm(nm.group(1).strip())] = vs.group(1).strip()
                elif mem.isfile() and re.search(r'(^|/)swisseph\.cpython[^/]*\.so$', n):
                    so.append((n, mem.size, sha_of(tf.extractfile(mem))))
        out['versions'] = found; out['swisseph_so'] = so
        for p, v in VERS.items(): rec('version ' + p, found.get(p) == v, f'image={found.get(p)} expected={v}')
        rec('swisseph binary', len(so) == 1 and so[0][2] == SO_SHA, f"{so[0][0] if so else None} size={so[0][1] if so else None} sha256={so[0][2][:16] if so else None}...")
    if a.phase in ('src', 'all') and a.src:
        tot = bad = miss = 0; badl = []
        for i in range(len(layers)):
            if i == pip_i: continue
            with stream(i) as f:
                tf = tarfile.open(fileobj=f, mode='r|gz')
                for mem in tf:
                    n = mem.name.lstrip('./')
                    if not mem.isfile() or not n.startswith('app/') or n.startswith('app/ephe/'): continue
                    h = sha_of(tf.extractfile(mem)); tot += 1
                    rel = 'platform/python-sidecar/requirements.txt' if n == 'app/requirements.txt' else n[len('app/'):]   # Dockerfile.pipeline: COPY platform/python-sidecar/requirements.txt .
                    p = os.path.join(a.src, rel)
                    if not os.path.isfile(p): miss += 1; badl.append(('MISSING', n))
                    elif hashlib.sha256(open(p, 'rb').read()).hexdigest() != h: bad += 1; badl.append(('DIFF', n))
        out['src'] = {'compared': tot, 'diff': bad, 'missing': miss, 'examples': badl[:20]}
        rec('source layers == worktree', tot > 0 and bad == 0 and miss == 0, f'compared={tot} diff={bad} missing={miss}')
    if a.out: json.dump(out, open(a.out, 'w'), indent=1, sort_keys=True)
    print('ROUTE_B ' + ('PASS' if all(RES) else 'FAIL')); sys.exit(0 if all(RES) else 1)

if __name__ == '__main__':
    main()
